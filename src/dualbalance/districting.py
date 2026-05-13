"""Core DualBalance districting algorithm.

A deterministic, capacity-constrained variant of the Lloyd / Hess 1965
districting iteration: assign each atomic unit to its lowest-cost district
*subject to a per-district population capacity* ``P*``, then recenter
seeds to the population-weighted centroid of their assigned units. Repeat
until the assignment stops changing.

The assignment step processes all ``(unit, district)`` pairs in ascending
order of normalized geographic distance and gives each unit its first
district that still has remaining population capacity. Distance is
normalized by the units' total bounding-box diagonal so the cost term is
unit-free.

Why capacity-constrained rather than the soft-penalty form once written in
docs/Formalism.md §3: the soft-penalty form (cost = distance + |pop - P*|/P* +
|area - A*|/A*) attracts every unit to whichever district is nearest target
in the previous iteration, producing a 2-cycle that never converges on real
data. A hard capacity is the canonical Hess 1965 / Mehrotra-Johnson-Nemhauser
1998 formulation and avoids the cycle. The DualBalance score still measures
population and area balance equally; area balance is reported but not
enforced as a second capacity (a future extension may turn this into a
true 2D transportation problem).

After iteration, a contiguity-repair pass uses the rook-adjacency dual
graph (built via gerrychain) to dissolve isolated components.

``pop_prev`` and ``area_prev`` are the per-district totals from the previous
iteration's final assignment (zero on iteration 1). Using previous-iteration
totals -- rather than running totals updated mid-pass -- makes a single
assignment pass independent of unit-processing order and avoids the failure
mode where a greedy early fill starves a downstream seed of any units. The
order-independence cascade still matters for tie-breaking: ties on minimum
cost resolve to lower pop penalty -> lower area penalty -> shorter distance
-> smaller district ID.

"""

from __future__ import annotations

import math

import geopandas as gpd
import networkx as nx
import numpy as np
from gerrychain import Graph as DualGraph

from dualbalance.seeds import place_seeds
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
    capacity_slack: float = 0.0,
) -> dict[str, int]:
    """Capacity-constrained assignment.

    Builds the full list of ``(unit, district)`` pairs, sorts by normalized
    geographic distance ascending, and assigns each unit to its first district
    with remaining population capacity ``P* * (1 + capacity_slack)``. Ties on
    distance break by ``(unit_id ascending, district_id ascending)``.

    Any unit that finds no district with capacity (a rare integer-rounding
    edge case) is assigned to the district with the largest remaining
    capacity. This guarantees every unit ends up in some district.
    """
    n_districts = len(seeds)
    n_units = len(unit_ids)
    seed_x = np.fromiter((s.x for s in seeds), dtype=float, count=n_districts)
    seed_y = np.fromiter((s.y for s in seeds), dtype=float, count=n_districts)

    dx = cx[:, None] - seed_x[None, :]
    dy = cy[:, None] - seed_y[None, :]
    dist = np.sqrt(dx * dx + dy * dy) / norm  # shape (n_units, n_districts)

    # Flatten to a list of (cost, unit_idx, district_idx) and sort.
    flat = []
    for u in range(n_units):
        for d in range(n_districts):
            flat.append((float(dist[u, d]), u, d))
    flat.sort()

    capacity = np.full(n_districts, targets.population * (1.0 + capacity_slack))
    assignment: dict[str, int] = {}
    assigned = np.zeros(n_units, dtype=bool)
    pops_arr = pops  # alias

    for _, u, d in flat:
        if assigned[u]:
            continue
        if capacity[d] >= pops_arr[u]:
            assignment[unit_ids[u]] = d
            capacity[d] -= pops_arr[u]
            assigned[u] = True

    # Sweep leftovers (integer-rounding case): give them to the district with
    # most remaining capacity, breaking ties by ascending district id.
    for u in range(n_units):
        if assigned[u]:
            continue
        d = int(np.argmax(capacity))
        assignment[unit_ids[u]] = d
        capacity[d] -= pops_arr[u]
        assigned[u] = True

    return assignment


def _recenter(
    cx: np.ndarray,
    cy: np.ndarray,
    pops: np.ndarray,
    unit_ids: list[str],
    assignment: dict[str, int],
    n_districts: int,
    previous_seeds: list[Seed],
) -> list[Seed]:
    """Recompute seeds as population-weighted centroids of assigned units.

    Empty districts retain their previous seed position so the next assignment
    pass can still consider them.
    """
    members: list[list[int]] = [[] for _ in range(n_districts)]
    for i, uid in enumerate(unit_ids):
        members[assignment[uid]].append(i)

    new_seeds: list[Seed] = []
    for d in range(n_districts):
        idxs = members[d]
        if not idxs:
            new_seeds.append(previous_seeds[d])
            continue
        idx_arr = np.asarray(idxs)
        weights = pops[idx_arr]
        total_w = float(weights.sum())
        if total_w == 0.0:
            new_x = float(cx[idx_arr].mean())
            new_y = float(cy[idx_arr].mean())
        else:
            new_x = float((cx[idx_arr] * weights).sum() / total_w)
            new_y = float((cy[idx_arr] * weights).sum() / total_w)
        new_seeds.append(Seed(district_id=d, x=new_x, y=new_y))
    return new_seeds


def generate_plan(
    units: gpd.GeoDataFrame,
    n_districts: int,
    *,
    alpha: float = 1.0,
    beta: float = 1.0,
    max_iter: int = 100,
    geography: str = "unknown",
    repair: bool = True,
    max_repair_iter: int = 10,
) -> Plan:
    """Generate a deterministic district plan.

    Args:
        units: GeoDataFrame with the canonical ``unit_id``, ``population``,
            ``area``, ``geometry`` columns (as produced by ``io.load_units``).
        n_districts: number of districts to produce.
        alpha: weight on the (normalized) geographic-distance term.
        beta: weight on the population and area penalty terms (shared, so
            population and area are weighted equally).
        max_iter: hard cap on Lloyd iterations.
        geography: ``Geography.cli_name`` of the base unit type (recorded in
            ``Plan.geography``).
        repair: whether to run the contiguity-repair pass after iteration.
        max_repair_iter: hard cap on repair sweeps (each sweep dissolves all
            currently-isolated components).

    Raises:
        ValueError: for non-positive ``n_districts``, ``max_iter``, or a
            degenerate units extent.
    """
    if n_districts <= 0:
        raise ValueError(f"n_districts must be positive, got {n_districts}")
    if n_districts > len(units):
        raise ValueError(
            f"n_districts ({n_districts}) exceeds number of units ({len(units)})"
        )
    if max_iter < 1:
        raise ValueError(f"max_iter must be >= 1, got {max_iter}")

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

    seeds = place_seeds(units_sorted, n_districts)
    previous_assignment: dict[str, int] | None = None
    assignment: dict[str, int] = {}
    converged = False
    n_iters = 0

    for n_iters in range(1, max_iter + 1):  # noqa: B007 — n_iters read after loop
        assignment = _assign(cx, cy, pops, unit_ids, seeds, targets, norm)
        if assignment == previous_assignment:
            converged = True
            break
        previous_assignment = assignment
        seeds = _recenter(cx, cy, pops, unit_ids, assignment, n_districts, seeds)

    repair_iters = 0
    contiguous = None
    if repair:
        assignment, repair_iters, contiguous = _repair_contiguity(
            assignment, units_sorted, seeds, targets,
            alpha, beta, norm, n_districts, max_repair_iter,
        )

    return Plan(
        assignment=assignment,
        n_districts=n_districts,
        geography=geography,
        metadata={
            "n_iterations": n_iters,
            "converged": converged,
            "repair_iterations": repair_iters,
            "contiguous": contiguous,
            "alpha": alpha,
            "beta": beta,
            "targets": {
                "population": targets.population,
                "area": targets.area,
            },
        },
    )


def _build_dual_graph(units: gpd.GeoDataFrame) -> DualGraph:
    """Build the rook-adjacency dual graph keyed by ``unit_id``."""
    indexed = units.set_index("unit_id")
    return DualGraph.from_geodataframe(indexed, adjacency="rook")


def _components_by_district(
    graph: DualGraph, assignment: dict[str, int], n_districts: int
) -> dict[int, list[set[str]]]:
    """Return the connected components of each district's induced subgraph."""
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
    alpha: float,
    beta: float,
    norm: float,
    n_districts: int,
    max_repair_iter: int,
) -> tuple[dict[str, int], int, bool]:
    """Dissolve isolated district components into adjacent districts.

    For each district with more than one connected component, keep the
    largest by total population and reassign units of the smaller components
    to the lowest-cost adjacent district. Iterates because a transfer can
    occasionally introduce a new discontiguity in the receiving district.

    Returns:
        (assignment, n_iterations_performed, contiguous_at_exit)
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
                        assignment[nbr]
                        for nbr in graph.neighbors(uid)
                        if assignment[nbr] != d
                    }
                    if not candidates:
                        continue  # truly isolated; leave in place
                    best_district: int | None = None
                    best_key: tuple[float, float, float, float, int] | None = None
                    for cand in candidates:
                        dist = math.hypot(
                            cx[uid] - seed_x[cand], cy[uid] - seed_y[cand]
                        ) / norm
                        pop_pen = abs(pop_totals[cand] + pop[uid] - p_star) / p_star
                        area_pen = abs(area_totals[cand] + area[uid] - a_star) / a_star
                        cost = alpha * dist + beta * pop_pen + beta * area_pen
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
