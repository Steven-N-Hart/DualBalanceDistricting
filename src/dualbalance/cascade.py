"""Cascade: an Iowa-LSA-flavored deterministic baseline.

Where PRISM treats VTDs as the atomic primitive and uses radial seeds
around the population centroid, Cascade treats counties as the atomic
primitive and uses farthest-point seeding to spread coverage. The
algorithm is deterministic (no RNG, no iteration) and lexicographically
prioritizes:

1. **County integrity.** Counties are kept whole wherever possible.
   Counties whose population exceeds the per-district cap are split
   into the minimum number of pseudo-counties via PRISM-style
   capacitated assignment within the county (this matches what Iowa
   LSA does in practice when its own large counties exceed the cap).
2. **Population balance.** A capacitated first-fit assignment caps each
   district at the per-district target ``P*``.
3. **Compactness.** Emerges from distance-based ordering of
   county-to-seed assignments.

The result is a per-VTD plan in which every VTD inherits its
county's district (or sub-county district, where the county was
split). This is the structural opposite of PRISM: instead of spanning
urban-rural by slicing radially, Cascade preserves administrative
units and produces compact county-bundled districts.
"""

from __future__ import annotations

import math
from typing import Any

import geopandas as gpd
import numpy as np

from dualbalance.districting import generate_plan
from dualbalance.types import Plan


def _split_oversize_county(
    units: gpd.GeoDataFrame, county_id: str, n_pieces: int
) -> dict[str, int]:
    """Split a single county into ``n_pieces`` pseudo-counties via PRISM.

    Returns a dict ``unit_id -> sub_index`` for the VTDs in this county.
    Uses the existing radial-seed capacitated assignment on the county's
    VTD subset.
    """
    sub = units[units["county"].astype(str) == county_id].copy()
    if len(sub) < n_pieces:
        raise NotImplementedError(
            f"county {county_id!r} has only {len(sub)} VTDs but needs to be split into "
            f"{n_pieces} pieces; cascade cannot split this county"
        )
    # generate_plan needs the canonical schema (unit_id, population, area, geometry).
    sub_plan = generate_plan(sub, n_pieces, geography="cascade-split")
    return dict(sub_plan.assignment)


def generate_cascade_plan(
    units: gpd.GeoDataFrame,
    n_districts: int,
    *,
    geography: str = "unknown",
) -> Plan:
    """Build a Cascade plan from ``units`` with a per-VTD ``county`` column.

    Returns a :class:`Plan` whose ``assignment`` maps every ``unit_id`` to
    a 0-indexed district id in ``[0, n_districts)``.

    Raises
    ------
    ValueError
        If ``units`` lacks a ``county`` column.
    NotImplementedError
        If any county's population exceeds the per-district cap
        ``P*/N``. v1 does not split oversized counties.
    """
    if "county" not in units.columns:
        raise ValueError("cascade algorithm requires a 'county' column on units")
    if n_districts <= 0:
        raise ValueError(f"n_districts must be positive, got {n_districts}")

    units = units.copy()
    units["county"] = units["county"].astype(str)

    total_pop = float(units["population"].sum())
    cap = total_pop / n_districts

    # 1. Detect oversize counties and split them in-place into pseudo-counties.
    raw_pop = units.groupby("county")["population"].sum()
    oversize = sorted(raw_pop[raw_pop > cap].index.tolist())
    splits: dict[str, int] = {}  # original county_id -> number of pieces
    for c in oversize:
        k = math.ceil(raw_pop[c] / cap)
        sub_assign = _split_oversize_county(units, c, k)
        for uid, sub_idx in sub_assign.items():
            mask = units["unit_id"].astype(str) == str(uid)
            units.loc[mask, "county"] = f"{c}__split{sub_idx}"
        splits[c] = k

    # 2. Aggregate VTDs to (possibly-split) counties.
    county_pops: dict[str, float] = {}
    county_areas: dict[str, float] = {}
    county_centroids: dict[str, Any] = {}
    by_county = units.dissolve(by="county", aggfunc={"population": "sum", "area": "sum"})
    for cname, row in by_county.iterrows():
        c = str(cname)
        county_pops[c] = float(row["population"])
        county_areas[c] = float(row["area"])
        county_centroids[c] = row.geometry.centroid

    n_counties = len(county_pops)
    if n_districts > n_counties:
        raise ValueError(
            f"n_districts ({n_districts}) exceeds number of (possibly-split) counties "
            f"({n_counties})"
        )
    # After splitting, no pseudo-county should exceed cap. If one still
    # does, the radial split inside _split_oversize_county failed to
    # respect the cap (rare; record and continue with best-fit assignment).
    still_oversize = [c for c, p in county_pops.items() if p > cap]
    if still_oversize:
        print(f"  cascade NOTE: pseudo-counties still over cap after split: {still_oversize}")

    # 3. Farthest-point seed selection.
    # Start with the most populous county; subsequent seeds maximize min
    # distance to chosen seeds. Tiebreaks: population (desc), county id (asc).
    counties_sorted = sorted(county_pops.keys(), key=lambda c: (-county_pops[c], c))
    seeds: list[str] = [counties_sorted[0]]
    while len(seeds) < n_districts:
        seed_pts = [county_centroids[s] for s in seeds]
        best: tuple[float, float, str] | None = None  # (-min_dist, -pop, county_id)
        for c in counties_sorted:
            if c in seeds:
                continue
            min_dist = min(county_centroids[c].distance(p) for p in seed_pts)
            # Larger min_dist is better; larger pop is better; smaller id is better.
            key = (-min_dist, -county_pops[c], c)
            if best is None or key < best:
                best = key
        assert best is not None
        seeds.append(best[2])

    seed_to_dist = {s: i for i, s in enumerate(seeds)}

    # 4. Capacitated first-fit assignment of counties to districts.
    # Sort all (county, seed) pairs by distance ascending.
    diag = float(
        np.hypot(
            units.total_bounds[2] - units.total_bounds[0],
            units.total_bounds[3] - units.total_bounds[1],
        )
    )
    if diag <= 0:
        diag = 1.0

    pairs: list[tuple[float, str, int]] = []
    for c in counties_sorted:
        cp = county_centroids[c]
        for s in seeds:
            d = cp.distance(county_centroids[s]) / diag
            pairs.append((d, c, seed_to_dist[s]))
    # Sort by (distance asc, county asc, district asc) for determinism.
    pairs.sort(key=lambda x: (x[0], x[1], x[2]))

    rho = [cap] * n_districts
    county_to_dist: dict[str, int] = {}
    for _d, c, i in pairs:
        if c in county_to_dist:
            continue
        if rho[i] >= county_pops[c]:
            county_to_dist[c] = i
            rho[i] -= county_pops[c]

    # 5. Fallback: any unassigned county goes to the district with largest
    # remaining capacity. argmax tiebreaks to smallest district id.
    for c in counties_sorted:
        if c in county_to_dist:
            continue
        i = int(np.argmax(rho))
        county_to_dist[c] = i
        rho[i] -= county_pops[c]

    # 6. Disaggregate to VTDs.
    assignment: dict[str, int] = {}
    for _, row in units.iterrows():
        c = str(row["county"])
        if c not in county_to_dist:
            raise RuntimeError(f"county {c!r} not in assignment after fallback")
        assignment[str(row["unit_id"])] = county_to_dist[c]

    return Plan(
        assignment=assignment,
        n_districts=n_districts,
        geography=geography,
        metadata={
            "algorithm": "cascade",
            "targets": {
                "population": cap,
                "area": float(units["area"].sum()) / n_districts,
            },
            "n_counties": n_counties,
            "seed_counties": seeds,
            "counties_split_by_cap": splits,
        },
    )
