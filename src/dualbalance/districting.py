"""DualBalance districting algorithm.

A deterministic, single-pass capacity-constrained assignment:

1. Place ``N`` seeds radially around the population-weighted centroid (see
   :func:`dualbalance.seeds.place_seeds`).
2. Sort all ``(unit, district)`` pairs by normalized Euclidean distance
   ascending; assign each unit to its first district with remaining
   population capacity ``P* = total_population / N``. Ties on distance
   break by ``(unit_id asc, district_id asc)``.
3. Repair contiguity: for each district with more than one connected
   component, dissolve the smaller components into adjacent districts by
   lowest-cost transfer.

No iteration, no tightening pass, no tunable weights. The plan is a pure
function of the inputs. Identical inputs always produce byte-identical
outputs.
"""

from __future__ import annotations

import math

import geopandas as gpd
import networkx as nx
import numpy as np
from gerrychain import Graph as DualGraph

from dualbalance.seeds import (
    place_seeds,
    place_seeds_angular_quantile,
    place_seeds_hilbert,
    place_seeds_recursive_bisection,
)
from dualbalance.types import Plan, Seed, Targets


def _bounding_box_diagonal(units: gpd.GeoDataFrame) -> float:
    minx, miny, maxx, maxy = units.total_bounds
    return float(math.hypot(maxx - minx, maxy - miny))


def _compute_targets(units: gpd.GeoDataFrame, n_districts: int) -> Targets:
    return Targets(
        population=float(units["population"].sum()) / n_districts,
        area=float(units["area"].sum()) / n_districts,
    )


def _assign(
    cx: np.ndarray,
    cy: np.ndarray,
    pops: np.ndarray,
    unit_ids: list[str],
    seeds: list[Seed],
    targets: Targets,
    norm: float,
) -> dict[str, int]:
    """Population-capacity-constrained first-fit assignment by distance."""
    n_districts = len(seeds)
    n_units = len(unit_ids)
    seed_x = np.fromiter((s.x for s in seeds), dtype=float, count=n_districts)
    seed_y = np.fromiter((s.y for s in seeds), dtype=float, count=n_districts)

    dx = cx[:, None] - seed_x[None, :]
    dy = cy[:, None] - seed_y[None, :]
    dist = np.sqrt(dx * dx + dy * dy) / norm

    flat = []
    for u in range(n_units):
        for d in range(n_districts):
            flat.append((float(dist[u, d]), u, d))
    flat.sort()

    capacity = np.full(n_districts, targets.population)
    assignment: dict[str, int] = {}
    assigned = np.zeros(n_units, dtype=bool)

    for _, u, d in flat:
        if assigned[u]:
            continue
        if capacity[d] < pops[u]:
            continue
        assignment[unit_ids[u]] = d
        capacity[d] -= pops[u]
        assigned[u] = True

    # Leftovers (integer-rounding edge case) go to the district with the
    # most remaining capacity; argmax breaks ties to the lowest district id.
    for u in range(n_units):
        if assigned[u]:
            continue
        d = int(np.argmax(capacity))
        assignment[unit_ids[u]] = d
        capacity[d] -= pops[u]
        assigned[u] = True

    return assignment


def generate_plan(
    units: gpd.GeoDataFrame,
    n_districts: int,
    *,
    geography: str = "unknown",
    rotation_offset: float = 0.0,
    seed_method: str = "radial",
) -> Plan:
    """Generate a deterministic DualBalance plan.

    Args:
        units: GeoDataFrame with the canonical ``unit_id``, ``population``,
            ``area``, ``geometry`` columns (as produced by ``io.load_units``).
        n_districts: number of districts to produce.
        geography: ``Geography.cli_name`` of the base unit type (recorded
            in ``Plan.geography``).

    Raises:
        ValueError: for non-positive ``n_districts``, more districts than
            units, or a degenerate units extent.
    """
    if n_districts <= 0:
        raise ValueError(f"n_districts must be positive, got {n_districts}")
    if n_districts > len(units):
        raise ValueError(f"n_districts ({n_districts}) exceeds number of units ({len(units)})")

    units_sorted = units.sort_values("unit_id", kind="mergesort").reset_index(drop=True)

    targets = _compute_targets(units_sorted, n_districts)
    norm = _bounding_box_diagonal(units_sorted)
    if norm == 0.0:
        raise ValueError("units bounding box is degenerate (norm=0)")

    centroids = units_sorted.geometry.centroid
    cx = np.asarray(centroids.x, dtype=float)
    cy = np.asarray(centroids.y, dtype=float)
    pops = np.asarray(units_sorted["population"], dtype=float)
    unit_ids: list[str] = units_sorted["unit_id"].tolist()

    if seed_method == "angular-quantile":
        seeds = place_seeds_angular_quantile(units_sorted, n_districts, rotation_offset=rotation_offset)
    elif seed_method == "hilbert":
        seeds = place_seeds_hilbert(units_sorted, n_districts)
    elif seed_method == "recursive-bisection":
        seeds = place_seeds_recursive_bisection(units_sorted, n_districts)
    elif seed_method == "radial":
        seeds = place_seeds(units_sorted, n_districts, rotation_offset=rotation_offset)
    else:
        raise ValueError(
            f"unknown seed_method {seed_method!r}; "
            "choose 'radial', 'angular-quantile', 'hilbert', or 'recursive-bisection'"
        )
    assignment = _assign(cx, cy, pops, unit_ids, seeds, targets, norm)
    assignment, repair_iters, contiguous = _repair_contiguity(
        assignment,
        units_sorted,
        seeds,
        targets,
        norm,
        n_districts,
    )

    return Plan(
        assignment=assignment,
        n_districts=n_districts,
        geography=geography,
        metadata={
            "seed_method": seed_method,
            "repair_iterations": repair_iters,
            "contiguous": contiguous,
            "targets": {
                "population": targets.population,
                "area": targets.area,
            },
        },
    )


def _build_dual_graph(units: gpd.GeoDataFrame) -> DualGraph:
    indexed = units.set_index("unit_id")
    return DualGraph.from_geodataframe(indexed, adjacency="rook")


def _components_by_district(
    graph: DualGraph, assignment: dict[str, int], n_districts: int
) -> dict[int, list[set[str]]]:
    nodes_in: dict[int, list[str]] = {d: [] for d in range(n_districts)}
    for node, d in assignment.items():
        nodes_in[d].append(node)
    return {
        d: [set(c) for c in nx.connected_components(graph.subgraph(nodes))]
        for d, nodes in nodes_in.items()
    }


def _repair_contiguity(
    assignment: dict[str, int],
    units_sorted: gpd.GeoDataFrame,
    seeds: list[Seed],
    targets: Targets,
    norm: float,
    n_districts: int,
    max_repair_iter: int = 10,
) -> tuple[dict[str, int], int, bool]:
    """Dissolve isolated district components into adjacent districts.

    For each district with more than one connected component, keep the
    largest by total population and reassign units of the smaller
    components to the lowest-cost adjacent district. Iterates because a
    transfer can occasionally introduce a new discontiguity in the
    receiving district.

    Cost for a candidate transfer is
    ``dist + pop_pen + area_pen``
    where ``pop_pen = |Pop(D)+pop(u) - P*| / P*`` and similarly for area;
    distances are normalized by the bounding-box diagonal.
    """
    graph = _build_dual_graph(units_sorted)

    indexed = units_sorted.set_index("unit_id")
    pop = indexed["population"].astype(float).to_dict()
    area = indexed["area"].astype(float).to_dict()
    centroids = indexed.geometry.centroid
    cx = dict(zip(indexed.index, centroids.x, strict=False))
    cy = dict(zip(indexed.index, centroids.y, strict=False))

    seed_x = [s.x for s in seeds]
    seed_y = [s.y for s in seeds]

    assignment = dict(assignment)
    pop_totals = np.zeros(n_districts)
    area_totals = np.zeros(n_districts)
    for uid, d in assignment.items():
        pop_totals[d] += pop[uid]
        area_totals[d] += area[uid]

    p_star = targets.population
    a_star = targets.area

    for repair_iter in range(1, max_repair_iter + 1):
        comps_by_d = _components_by_district(graph, assignment, n_districts)
        if all(len(c) <= 1 for c in comps_by_d.values()):
            return assignment, repair_iter - 1, True

        for d, comps in comps_by_d.items():
            if len(comps) <= 1:
                continue
            comps_sorted = sorted(
                comps,
                key=lambda c: (-sum(pop[u] for u in c), min(c)),
            )
            for comp in comps_sorted[1:]:
                for uid in sorted(comp):
                    candidates = {
                        assignment[nbr] for nbr in graph.neighbors(uid) if assignment[nbr] != d
                    }
                    if not candidates:
                        continue
                    best_district: int | None = None
                    best_key: tuple[float, float, float, float, int] | None = None
                    for cand in candidates:
                        dist = math.hypot(cx[uid] - seed_x[cand], cy[uid] - seed_y[cand]) / norm
                        pop_pen = abs(pop_totals[cand] + pop[uid] - p_star) / p_star
                        area_pen = abs(area_totals[cand] + area[uid] - a_star) / a_star
                        cost = dist + pop_pen + area_pen
                        key = (cost, pop_pen, area_pen, dist, cand)
                        if best_key is None or key < best_key:
                            best_district = cand
                            best_key = key
                    assert best_district is not None
                    pop_totals[d] -= pop[uid]
                    area_totals[d] -= area[uid]
                    pop_totals[best_district] += pop[uid]
                    area_totals[best_district] += area[uid]
                    assignment[uid] = best_district

    final_comps = _components_by_district(graph, assignment, n_districts)
    contiguous = all(len(c) <= 1 for c in final_comps.values())
    return assignment, max_repair_iter, contiguous
