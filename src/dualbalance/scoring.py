"""Scoring harness for evaluating districting plans.

Primary metric:

- ``dualbalance_score = 1 / (1 + 0.5 * pop_deviation_mean + 0.5 * area_deviation_mean)``

  Per-district deviations are
  ``pop_dev_i  = |Pop(D_i)  - P*| / P*`` and
  ``area_dev_i = |Area(D_i) - A*| / A*``,
  averaged over districts. The 0.5/0.5 weighting makes the error a
  convex combination — each district is judged on representing roughly
  1/N of the people *and* roughly 1/N of the state's geography (the
  House and Senate balance, applied within a single chamber).

Secondary metrics:

- ``polsby_popper`` — 4π · area / perimeter² (via gerrychain)
- ``reock`` — area / area(minimum bounding circle) (via shapely 2.x)
- ``convex_hull_ratio`` — area / area(convex hull); 1.0 = convex
- ``length_width_ratio`` — short_side / long_side of the minimum
  rotated bounding rectangle; 1.0 = square, → 0 = thin sliver
- ``density`` — population / area, in people per equal-area unit
- ``density_gini`` — Gini coefficient of the per-district density
  distribution. Low values indicate every district spans a similar mix
  of dense and sparse territory (the radial-slice claim made
  quantitative); high values indicate urban-vs-rural separation.
- ``n_counties`` per district + ``counties_split`` / ``county_pieces_total``
  aggregates, only reported when the units carry a ``county`` column.

Opt-in diagnostic metrics (computed only when the relevant columns are
present on the units; the core generator never reads these):

- **Race / VAP**: per-district counts and shares for ``vap_total``,
  ``vap_nhwhite``, ``vap_black``, ``vap_hispanic``, ``vap_aian``,
  ``vap_asian``. Aggregates include statewide shares and counts of
  districts where each group reaches majority / plurality, plus a
  ``minority_majority_districts`` count (NH-white share < 0.5).
- **Partisan**: per-district ``votes_R`` / ``votes_D`` /
  ``two_party_share_R`` / ``winner``. Aggregates: ``seats_R`` /
  ``seats_D`` under simple plurality, ``efficiency_gap`` (positive =
  pro-R), ``mean_median_R`` (positive = pro-D), ``statewide_share_R``,
  ``seats_proportional_R``, ``seats_bias_R``.

The harness is intentionally decoupled from the generator: ``score_plan``
accepts any ``Plan`` + matching ``units`` and computes the same metrics,
so enacted/court-drawn/third-party plans are directly comparable to a
DualBalance plan.
"""

from __future__ import annotations

import math
from typing import Any

import geopandas as gpd
import numpy as np
from gerrychain.metrics.compactness import compute_polsby_popper
from shapely import minimum_bounding_radius
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from dualbalance.types import Plan

# Canonical column names for opt-in race/partisan diagnostics. Source data
# columns are mapped to these names by ``io.load_units(..., extra_columns=...)``;
# the scoring harness checks for them by canonical name. The generator never
# reads any of these.
RACE_VAP_COLUMNS: tuple[str, ...] = (
    "vap_total",
    "vap_nhwhite",
    "vap_black",
    "vap_hispanic",
    "vap_aian",
    "vap_asian",
)
# Per-group share columns are emitted as ``share_<group>`` where <group> is
# the suffix of the corresponding ``vap_<group>`` column (e.g. ``share_black``).
RACE_GROUPS: tuple[str, ...] = tuple(
    c.removeprefix("vap_") for c in RACE_VAP_COLUMNS if c != "vap_total"
)

PARTISAN_COLUMNS: tuple[str, ...] = ("votes_R", "votes_D")


def _convex_hull_ratio(geom: BaseGeometry) -> float:
    hull_area = float(geom.convex_hull.area)
    return float(geom.area) / hull_area if hull_area > 0 else 0.0


def _length_width_ratio(geom: BaseGeometry) -> float:
    """Short-to-long side ratio of the minimum rotated bounding rectangle.

    Returns a value in [0, 1]: 1.0 for a square-ish district, → 0 for a
    long thin sliver. Distinct signal from Reock (which measures fill of
    the minimum bounding *circle*) — a long thin shape can have a poor
    Reock score and a poor LW score for the same underlying reason, but
    a square district has near-1 LW and middling Reock.
    """
    mrr = geom.minimum_rotated_rectangle
    if mrr.is_empty or not hasattr(mrr, "exterior"):
        return 0.0
    coords = list(mrr.exterior.coords)
    # A rectangle ring has 5 points (closed). First 4 segments are the sides.
    sides = [
        math.hypot(coords[i + 1][0] - coords[i][0], coords[i + 1][1] - coords[i][1])
        for i in range(4)
    ]
    long_side = max(sides)
    if long_side <= 0:
        return 0.0
    return min(sides) / long_side


def _gini(values: list[float]) -> float:
    """Gini coefficient of a non-negative distribution.

    0 = perfect equality (all districts identical), → 1 = maximal
    concentration. Used here on per-district *density* to summarize how
    evenly each district spans dense and sparse territory.
    """
    if not values:
        return 0.0
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return 0.0
    mean = float(arr.mean())
    if mean <= 0:
        return 0.0
    n = arr.size
    diff_sum = float(np.abs(arr[:, None] - arr[None, :]).sum())
    return diff_sum / (2.0 * n * n * mean)


def score_plan(plan: Plan, units: gpd.GeoDataFrame) -> dict[str, Any]:
    """Score ``plan`` against the DualBalance primary + compactness metrics."""
    indexed = units.set_index("unit_id")
    has_county = "county" in indexed.columns
    has_race = "vap_total" in indexed.columns
    race_groups_available: tuple[str, ...] = (
        tuple(g for g in RACE_GROUPS if f"vap_{g}" in indexed.columns) if has_race else ()
    )
    has_partisan = all(c in indexed.columns for c in PARTISAN_COLUMNS)

    members: dict[int, list[str]] = {d: [] for d in range(plan.n_districts)}
    for uid, d in plan.assignment.items():
        if d not in members:
            members[d] = []
        members[d].append(uid)

    targets_pop = float(plan.metadata.get("targets", {}).get("population", 0.0))
    targets_area = float(plan.metadata.get("targets", {}).get("area", 0.0))
    if targets_pop <= 0.0:
        targets_pop = float(units["population"].sum()) / plan.n_districts
    if targets_area <= 0.0:
        targets_area = float(units["area"].sum()) / plan.n_districts

    per_district: list[dict[str, Any]] = []
    pop_devs: list[float] = []
    area_devs: list[float] = []
    pp_scores: list[float] = []
    reock_scores: list[float] = []
    hull_scores: list[float] = []
    lw_scores: list[float] = []
    densities: list[float] = []
    # county_id -> set of district ids that touch it
    county_touches: dict[Any, set[int]] = {}
    # Partisan running tallies; only used when has_partisan.
    seats_r = 0
    seats_d = 0
    wasted_r_total = 0.0
    wasted_d_total = 0.0
    district_share_r: list[float] = []
    two_party_total = 0.0

    for d in sorted(members):
        uids = members[d]
        if not uids:
            empty: dict[str, Any] = {
                "district_id": d,
                "population": 0.0,
                "area": 0.0,
                "n_units": 0,
                "pop_deviation": 1.0,
                "area_deviation": 1.0,
                "polsby_popper": 0.0,
                "reock": 0.0,
                "convex_hull_ratio": 0.0,
                "length_width_ratio": 0.0,
                "density": 0.0,
            }
            if has_county:
                empty["n_counties"] = 0
            if has_race:
                empty["vap_total"] = 0.0
                for g in race_groups_available:
                    empty[f"vap_{g}"] = 0.0
                    empty[f"share_{g}"] = 0.0
            if has_partisan:
                empty["votes_R"] = 0.0
                empty["votes_D"] = 0.0
                empty["two_party_share_R"] = 0.0
                empty["winner"] = "none"
            per_district.append(empty)
            pop_devs.append(1.0)
            area_devs.append(1.0)
            pp_scores.append(0.0)
            reock_scores.append(0.0)
            hull_scores.append(0.0)
            lw_scores.append(0.0)
            densities.append(0.0)
            continue

        sub = indexed.loc[uids]
        pop = float(sub["population"].sum())
        area = float(sub["area"].sum())
        merged = unary_union(sub.geometry.values)
        perimeter = float(merged.length)
        pp = compute_polsby_popper(area, perimeter) if perimeter > 0 else 0.0
        mbc_radius = float(minimum_bounding_radius(merged))
        mbc_area = math.pi * mbc_radius * mbc_radius
        reock = area / mbc_area if mbc_area > 0 else 0.0
        hull = _convex_hull_ratio(merged)
        lw = _length_width_ratio(merged)
        density = pop / area if area > 0 else 0.0

        pop_dev = abs(pop - targets_pop) / targets_pop if targets_pop > 0 else 0.0
        area_dev = abs(area - targets_area) / targets_area if targets_area > 0 else 0.0

        pop_devs.append(pop_dev)
        area_devs.append(area_dev)
        pp_scores.append(pp)
        reock_scores.append(reock)
        hull_scores.append(hull)
        lw_scores.append(lw)
        densities.append(density)

        district_row: dict[str, Any] = {
            "district_id": d,
            "population": pop,
            "area": area,
            "n_units": len(uids),
            "pop_deviation": pop_dev,
            "area_deviation": area_dev,
            "polsby_popper": pp,
            "reock": reock,
            "convex_hull_ratio": hull,
            "length_width_ratio": lw,
            "density": density,
        }

        if has_county:
            counties = sub["county"].astype(str).unique().tolist()
            district_row["n_counties"] = len(counties)
            for c in counties:
                county_touches.setdefault(c, set()).add(d)

        if has_race:
            v_total = float(sub["vap_total"].sum())
            district_row["vap_total"] = v_total
            for g in race_groups_available:
                v_g = float(sub[f"vap_{g}"].sum())
                district_row[f"vap_{g}"] = v_g
                district_row[f"share_{g}"] = v_g / v_total if v_total > 0 else 0.0

        if has_partisan:
            vr = float(sub["votes_R"].sum())
            vd = float(sub["votes_D"].sum())
            two_party = vr + vd
            district_row["votes_R"] = vr
            district_row["votes_D"] = vd
            share_r = vr / two_party if two_party > 0 else 0.0
            district_row["two_party_share_R"] = share_r
            district_share_r.append(share_r)
            two_party_total += two_party
            if vr > vd:
                district_row["winner"] = "R"
                seats_r += 1
                wasted_r_total += vr - two_party / 2.0
                wasted_d_total += vd
            elif vd > vr:
                district_row["winner"] = "D"
                seats_d += 1
                wasted_d_total += vd - two_party / 2.0
                wasted_r_total += vr
            else:
                # Exact tie: split wasted votes evenly. Vanishingly rare on
                # real data with 4k+ VTDs aggregating to ~8 districts.
                district_row["winner"] = "tie"
                wasted_r_total += vr / 2.0
                wasted_d_total += vd / 2.0

        per_district.append(district_row)

    pop_dev_mean = float(np.mean(pop_devs))
    pop_dev_max = float(np.max(pop_devs))
    area_dev_mean = float(np.mean(area_devs))
    area_dev_max = float(np.max(area_devs))
    dual_error = 0.5 * pop_dev_mean + 0.5 * area_dev_mean
    dual_score = 1.0 / (1.0 + dual_error)

    metrics: dict[str, Any] = {
        "dualbalance_score": dual_score,
        "pop_deviation_mean": pop_dev_mean,
        "pop_deviation_max": pop_dev_max,
        "area_deviation_mean": area_dev_mean,
        "area_deviation_max": area_dev_max,
        "polsby_popper_mean": float(np.mean(pp_scores)),
        "polsby_popper_min": float(np.min(pp_scores)),
        "reock_mean": float(np.mean(reock_scores)),
        "reock_min": float(np.min(reock_scores)),
        "convex_hull_ratio_mean": float(np.mean(hull_scores)),
        "convex_hull_ratio_min": float(np.min(hull_scores)),
        "length_width_ratio_mean": float(np.mean(lw_scores)),
        "length_width_ratio_min": float(np.min(lw_scores)),
        "density_mean": float(np.mean(densities)),
        "density_min": float(np.min(densities)),
        "density_max": float(np.max(densities)),
        "density_gini": _gini(densities),
        "n_districts": plan.n_districts,
        "geography": plan.geography,
        "targets": {"population": targets_pop, "area": targets_area},
        "districts": per_district,
    }

    if has_county:
        pieces_total = sum(len(ds) for ds in county_touches.values())
        split_counties = sum(1 for ds in county_touches.values() if len(ds) > 1)
        metrics["counties_total"] = len(county_touches)
        metrics["counties_split"] = split_counties
        metrics["county_pieces_total"] = pieces_total

    if has_race:
        statewide_vap = float(indexed["vap_total"].sum())
        metrics["vap_total"] = statewide_vap
        for g in race_groups_available:
            statewide_g = float(indexed[f"vap_{g}"].sum())
            metrics[f"statewide_share_{g}"] = (
                statewide_g / statewide_vap if statewide_vap > 0 else 0.0
            )
            metrics[f"{g}_majority_districts"] = sum(
                1 for r in per_district if r.get(f"share_{g}", 0.0) > 0.5
            )
        if "nhwhite" in race_groups_available:
            metrics["minority_majority_districts"] = sum(
                1 for r in per_district if 0.0 < r.get("share_nhwhite", 1.0) < 0.5
            )

    if has_partisan:
        statewide_r = float(indexed["votes_R"].sum())
        statewide_d = float(indexed["votes_D"].sum())
        statewide_two_party = statewide_r + statewide_d
        statewide_share_r = statewide_r / statewide_two_party if statewide_two_party > 0 else 0.0
        metrics["seats_R"] = seats_r
        metrics["seats_D"] = seats_d
        metrics["statewide_share_R"] = statewide_share_r
        metrics["efficiency_gap"] = (
            (wasted_d_total - wasted_r_total) / two_party_total if two_party_total > 0 else 0.0
        )
        metrics["mean_median_R"] = (
            float(np.median(district_share_r) - np.mean(district_share_r))
            if district_share_r
            else 0.0
        )
        metrics["seats_proportional_R"] = statewide_share_r * plan.n_districts
        metrics["seats_bias_R"] = seats_r - metrics["seats_proportional_R"]

    return metrics
