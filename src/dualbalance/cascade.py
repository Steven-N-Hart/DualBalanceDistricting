"""Cascade: an Iowa-LSA-flavored deterministic baseline.

Where DualBalance treats VTDs as the atomic primitive and uses radial seeds
around the population centroid, Cascade treats counties as the atomic
primitive and uses farthest-point seeding to spread coverage. The
algorithm is deterministic (no RNG, no iteration) and lexicographically
prioritizes:

1. **County integrity.** Counties are kept whole wherever possible.
   Counties whose population exceeds the per-district cap are split
   into the minimum number of pseudo-counties via DualBalance-style
   capacitated assignment within the county (this matches what Iowa
   LSA does in practice when its own large counties exceed the cap).
2. **Population balance.** A capacitated first-fit assignment caps each
   district at the per-district target ``P*``.
3. **Compactness.** Emerges from distance-based ordering of
   county-to-seed assignments.

The result is a per-VTD plan in which every VTD inherits its
county's district (or sub-county district, where the county was
split). This is the structural opposite of DualBalance: instead of spanning
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
    units: gpd.GeoDataFrame,
    county_id: str,
    cap: float,
) -> tuple[dict[str, int], int]:
    """Split a single county into ``ceil(pop/cap)`` pseudo-counties.

    Calls the radial-seed capacitated assignment on the county's VTD
    subset. DualBalance's internal capacitated rule guarantees each piece
    holds at most ``county_pop / n_pieces`` people, which is at most
    ``cap`` since ``n_pieces = ceil(pop/cap)``. Small integer-rounding
    overflow at the splitter's fallback step is possible but bounded
    by the largest single VTD's population.

    Returns ``(assignment, n_pieces)``. ``assignment`` maps
    ``unit_id -> piece_index``.
    """
    sub = units[units["county"].astype(str) == county_id].copy()
    sub_pop = float(sub["population"].sum())
    n_pieces = math.ceil(sub_pop / cap)
    if len(sub) < n_pieces:
        raise NotImplementedError(
            f"county {county_id!r} has only {len(sub)} VTDs but needs to be split "
            f"into {n_pieces} pieces; the county is too coarsely measured to split"
        )
    sub_plan = generate_plan(sub, n_pieces, geography="cascade-split")
    assignment = {str(k): int(v) for k, v in sub_plan.assignment.items()}
    return assignment, n_pieces


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

    # 1. Detect oversize counties. Split each into pseudo-counties via the
    # internal radial sub-routine. Crucially, each pseudo-county piece
    # becomes its own district (no further bundling). This prevents the
    # fallback-overflow problem where multiple pieces of a big county
    # (e.g. Harris in TX) compete for the same neighboring district and
    # the unassigned remainder gets dumped into a single over-cap bucket.
    raw_pop = units.groupby("county")["population"].sum()
    oversize = sorted(raw_pop[raw_pop > cap].index.tolist())
    splits: dict[str, int] = {}
    oversize_piece_names: list[str] = []
    for c in oversize:
        sub_assign, n_used = _split_oversize_county(units, c, cap)
        for uid, sub_idx in sub_assign.items():
            mask = units["unit_id"].astype(str) == str(uid)
            units.loc[mask, "county"] = f"{c}__split{sub_idx}"
        for sub_idx in sorted(set(sub_assign.values())):
            oversize_piece_names.append(f"{c}__split{sub_idx}")
        splits[c] = n_used

    n_oversize_pieces = len(oversize_piece_names)
    if n_oversize_pieces > n_districts:
        raise NotImplementedError(
            f"oversize counties require {n_oversize_pieces} dedicated districts "
            f"but only {n_districts} are available; reduce splitter granularity "
            "or relax the population cap"
        )

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

    # 3. Pre-assign each oversize-county piece to its own district.
    county_to_dist: dict[str, int] = {}
    rho = [cap] * n_districts
    next_did = 0
    # Sort piece names deterministically before assigning district ids.
    for piece in sorted(oversize_piece_names):
        county_to_dist[piece] = next_did
        rho[next_did] -= county_pops[piece]
        next_did += 1

    # 4. Farthest-point seed selection on non-oversize counties for the
    # remaining n_districts - n_oversize_pieces districts. If the oversize
    # pieces already saturated all districts, skip seeding.
    remaining_districts = n_districts - n_oversize_pieces
    non_oversize = sorted(
        (c for c in county_pops if c not in oversize_piece_names),
        key=lambda c: (-county_pops[c], c),
    )
    seeds: list[str] = []
    if remaining_districts > 0 and non_oversize:
        seeds.append(non_oversize[0])
        while len(seeds) < remaining_districts and len(seeds) < len(non_oversize):
            seed_pts = [county_centroids[s] for s in seeds]
            # Also keep oversize-piece centroids in mind so seeds spread
            # away from already-claimed metros.
            seed_pts += [county_centroids[p] for p in oversize_piece_names]
            best: tuple[float, float, str] | None = None
            for c in non_oversize:
                if c in seeds:
                    continue
                min_dist = min(county_centroids[c].distance(p) for p in seed_pts)
                key = (-min_dist, -county_pops[c], c)
                if best is None or key < best:
                    best = key
            assert best is not None
            seeds.append(best[2])
        # Map each seed to a district id (continuing from next_did).
        for i, s in enumerate(seeds):
            county_to_dist[s] = next_did + i

    # 5. Capacitated first-fit assignment of remaining (non-oversize,
    # non-seed) counties to ALL districts, including the oversize-piece
    # districts (which have some residual capacity since each piece is
    # at most cap-sized). Each district has a centroid: for oversize
    # pieces, the piece geometry's centroid; for non-oversize seeds, the
    # seed county's centroid.
    diag = float(
        np.hypot(
            units.total_bounds[2] - units.total_bounds[0],
            units.total_bounds[3] - units.total_bounds[1],
        )
    )
    if diag <= 0:
        diag = 1.0

    district_seed_centroid: dict[int, Any] = {}
    for piece in oversize_piece_names:
        district_seed_centroid[county_to_dist[piece]] = county_centroids[piece]
    for s in seeds:
        district_seed_centroid[county_to_dist[s]] = county_centroids[s]

    pairs: list[tuple[float, str, int]] = []
    for c in non_oversize:
        if c in county_to_dist:
            continue
        cp = county_centroids[c]
        for did, sc in district_seed_centroid.items():
            d = cp.distance(sc) / diag
            pairs.append((d, c, did))
    pairs.sort(key=lambda x: (x[0], x[1], x[2]))

    for _d, c, i in pairs:
        if c in county_to_dist:
            continue
        if rho[i] >= county_pops[c]:
            county_to_dist[c] = i
            rho[i] -= county_pops[c]

    # 6. Fallback: any still-unassigned non-oversize county goes to the
    # district with the most remaining capacity (across all districts).
    # argmax tiebreaks to smallest district id.
    for c in non_oversize:
        if c in county_to_dist:
            continue
        i = max(range(n_districts), key=lambda did: (rho[did], -did))
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
            "n_counties": len(county_pops),
            "n_oversize_pieces": n_oversize_pieces,
            "non_oversize_seed_counties": seeds,
            "counties_split_by_cap": splits,
        },
    )
