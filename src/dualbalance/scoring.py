"""Scoring harness for evaluating districting plans.

Primary metrics (the ones the algorithm optimizes against):

- ``pop_deviation_mean`` / ``pop_deviation_max`` -- |pop(D) - P*| / P*
- ``area_deviation_mean`` / ``area_deviation_max`` -- |area(D) - A*| / A*
- ``dualbalance_score = 1 / (1 + 0.5 * (pop_deviation_mean + area_deviation_mean))``

  Equivalently: ``1 / (1 + dualbalance_error)`` where
  ``dualbalance_error = mean_i [0.5 * pop_dev_i + 0.5 * area_dev_i]``.
  The 0.5/0.5 weighting is the explicit "each district should be ~1/N of
  the people *and* ~1/N of the state's geography" statement; it makes the
  score behave as a convex combination of pop- and area-deviation rather
  than a sum, so adding the area term cannot push the score below what an
  area-blind capacitated-Voronoi pass would already report.

Secondary metrics (reported, not optimized):

- ``polsby_popper`` -- 4 * pi * area / perimeter^2  (via gerrychain.metrics)
- ``reock`` -- area / area(minimum bounding circle)  (via shapely 2.x)

The harness is intentionally decoupled from the generator: ``score_plan``
accepts any ``Plan`` + matching ``units`` and computes the same metrics,
making enacted/court-drawn/third-party plans directly comparable to the
DualBalance baseline. See README.md, section "Output and evaluation".
"""

from __future__ import annotations

import math
from typing import Any

import geopandas as gpd
import numpy as np
from gerrychain.metrics.compactness import compute_polsby_popper
from shapely import minimum_bounding_radius
from shapely.ops import unary_union

from dualbalance.types import Plan


def score_plan(plan: Plan, units: gpd.GeoDataFrame) -> dict[str, Any]:
    """Score ``plan`` against the DualBalance primary + compactness metrics."""
    indexed = units.set_index("unit_id")

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

    for d in sorted(members):
        uids = members[d]
        if not uids:
            per_district.append({
                "district_id": d,
                "population": 0.0,
                "area": 0.0,
                "n_units": 0,
                "pop_deviation": 1.0,
                "area_deviation": 1.0,
                "polsby_popper": 0.0,
                "reock": 0.0,
            })
            pop_devs.append(1.0)
            area_devs.append(1.0)
            pp_scores.append(0.0)
            reock_scores.append(0.0)
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

        pop_dev = abs(pop - targets_pop) / targets_pop if targets_pop > 0 else 0.0
        area_dev = abs(area - targets_area) / targets_area if targets_area > 0 else 0.0

        pop_devs.append(pop_dev)
        area_devs.append(area_dev)
        pp_scores.append(pp)
        reock_scores.append(reock)

        per_district.append({
            "district_id": d,
            "population": pop,
            "area": area,
            "n_units": len(uids),
            "pop_deviation": pop_dev,
            "area_deviation": area_dev,
            "polsby_popper": pp,
            "reock": reock,
        })

    pop_dev_mean = float(np.mean(pop_devs))
    pop_dev_max = float(np.max(pop_devs))
    area_dev_mean = float(np.mean(area_devs))
    area_dev_max = float(np.max(area_devs))
    dual_error = 0.5 * pop_dev_mean + 0.5 * area_dev_mean
    dual_score = 1.0 / (1.0 + dual_error)

    return {
        "dualbalance_score": dual_score,
        "pop_deviation_mean": pop_dev_mean,
        "pop_deviation_max": pop_dev_max,
        "area_deviation_mean": area_dev_mean,
        "area_deviation_max": area_dev_max,
        "polsby_popper_mean": float(np.mean(pp_scores)),
        "polsby_popper_min": float(np.min(pp_scores)),
        "reock_mean": float(np.mean(reock_scores)),
        "reock_min": float(np.min(reock_scores)),
        "n_districts": plan.n_districts,
        "geography": plan.geography,
        "targets": {"population": targets_pop, "area": targets_area},
        "districts": per_district,
    }
