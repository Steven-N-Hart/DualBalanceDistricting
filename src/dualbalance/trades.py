"""Post-iteration trade passes that tighten a plan to Reynolds tolerance.

Two sequential phases:

1. **Population tightening.** Move boundary units from over-target districts
   to adjacent under-target districts until every district is within
   ``pop_tolerance`` of ``P*``. Each move must preserve the source district's
   contiguity (the destination district necessarily stays contiguous because
   the moved unit is adjacent to it).
2. **Area reduction (pop-neutral).** Swap pairs of boundary units between
   adjacent districts when the swap reduces the sum of their area
   deviations *and* keeps both districts within ``pop_tolerance``. Pop is
   approximately conserved by pairing units of similar population.

Together these turn the capacity-greedy initial plan into one that satisfies
Reynolds v. Sims (population deviation under ~0.5 %) while still pushing
toward area balance as a secondary objective.

The dual graph is built once via gerrychain (rook adjacency, same as in
``districting._repair_contiguity``).
"""

from __future__ import annotations

import geopandas as gpd
import networkx as nx
import numpy as np
from gerrychain import Graph as DualGraph

from dualbalance.types import Plan


def _build_dual_graph(units: gpd.GeoDataFrame) -> DualGraph:
    indexed = units.set_index("unit_id")
    return DualGraph.from_geodataframe(indexed, adjacency="rook")


def _compute_totals(
    assignment: dict[str, int],
    pop: dict[str, float],
    area: dict[str, float],
    n_districts: int,
) -> tuple[np.ndarray, np.ndarray]:
    pop_totals = np.zeros(n_districts)
    area_totals = np.zeros(n_districts)
    for uid, d in assignment.items():
        pop_totals[d] += pop[uid]
        area_totals[d] += area[uid]
    return pop_totals, area_totals


def _removable_without_disconnect(
    graph: DualGraph, assignment: dict[str, int], uid: str
) -> bool:
    """True iff removing ``uid`` from its district keeps that district
    connected (and non-empty)."""
    d = assignment[uid]
    same_district = [n for n, dd in assignment.items() if dd == d and n != uid]
    if not same_district:
        return False  # would leave the district empty
    sub = graph.subgraph(same_district)
    return nx.is_connected(sub)


def tighten_to_reynolds(
    plan: Plan,
    units: gpd.GeoDataFrame,
    *,
    pop_tolerance: float = 0.005,
    reduce_area: bool = True,
    max_pop_passes: int = 5000,
    max_area_passes: int = 5000,
) -> Plan:
    """Run pop-tightening (Phase A) then optionally area-reduction (Phase B).

    Returns a new ``Plan`` whose ``metadata`` records the number of moves in
    each phase and the final ``pop_dev_max`` / ``area_dev_max`` achieved.
    Does not mutate the input plan.
    """
    if pop_tolerance < 0:
        raise ValueError(f"pop_tolerance must be >= 0, got {pop_tolerance}")
    n_districts = plan.n_districts
    graph = _build_dual_graph(units)

    indexed = units.set_index("unit_id")
    pop = indexed["population"].astype(float).to_dict()
    area = indexed["area"].astype(float).to_dict()

    assignment = dict(plan.assignment)
    p_target = float(units["population"].sum()) / n_districts
    a_target = float(units["area"].sum()) / n_districts
    pop_totals, area_totals = _compute_totals(assignment, pop, area, n_districts)

    # --- Phase A: population tightening ---
    pop_moves = _phase_a_pop_tighten(
        graph, assignment, pop, area, pop_totals, area_totals,
        p_target, pop_tolerance, max_pop_passes,
    )

    # --- Phase B: pop-neutral area-reducing swaps ---
    area_swaps = 0
    if reduce_area:
        area_swaps = _phase_b_area_reduce(
            graph, assignment, pop, area, pop_totals, area_totals,
            p_target, a_target, pop_tolerance, max_area_passes,
        )

    final_pop_dev = np.abs(pop_totals - p_target) / p_target
    final_area_dev = np.abs(area_totals - a_target) / a_target

    new_meta = dict(plan.metadata)
    new_meta["reynolds_pop_moves"] = pop_moves
    new_meta["reynolds_area_swaps"] = area_swaps
    new_meta["reynolds_pop_tolerance"] = pop_tolerance
    new_meta["reynolds_final_pop_dev_max"] = float(final_pop_dev.max())
    new_meta["reynolds_final_area_dev_max"] = float(final_area_dev.max())

    return Plan(
        assignment=assignment,
        n_districts=n_districts,
        geography=plan.geography,
        metadata=new_meta,
    )


def _phase_a_pop_tighten(
    graph: DualGraph,
    assignment: dict[str, int],
    pop: dict[str, float],
    area: dict[str, float],
    pop_totals: np.ndarray,
    area_totals: np.ndarray,
    p_target: float,
    pop_tolerance: float,
    max_passes: int,
) -> int:
    """Move boundary units from over-target to adjacent under-target districts.

    Picks the move that maximally reduces ``pop_dev_max`` each step. Ties on
    pop reduction break by smaller area-deviation increase, then by
    ascending (unit_id, target district id) for full determinism.
    """
    n = len(pop_totals)
    p_high = p_target * (1 + pop_tolerance)
    p_low = p_target * (1 - pop_tolerance)

    moves = 0
    for _ in range(max_passes):
        pop_dev = pop_totals - p_target
        max_over_idx = int(np.argmax(pop_dev))
        max_under_idx = int(np.argmin(pop_dev))
        if (
            pop_totals[max_over_idx] <= p_high
            and pop_totals[max_under_idx] >= p_low
        ):
            return moves  # all districts within tolerance

        d_over = max_over_idx
        over_pop = pop_totals[d_over]

        # Find boundary candidates: units in d_over with at least one neighbor
        # in another district that's under-target (or at least less-over).
        # Deterministic order: ascending unit_id.
        candidates: list[tuple[str, int]] = []
        for uid in sorted(graph.nodes):
            if assignment.get(uid) != d_over:
                continue
            neighbor_districts = {
                assignment[nbr]
                for nbr in graph.neighbors(uid)
                if assignment[nbr] != d_over
            }
            for d_dest in neighbor_districts:
                if pop_totals[d_dest] >= pop_totals[d_over]:
                    continue
                candidates.append((uid, d_dest))

        if not candidates:
            return moves  # nothing to do; perhaps non-adjacent over/under

        # Score each candidate. We want to minimize max-deviation across all
        # districts AFTER the move. Compute the deltas.
        current_max = float(np.max(np.abs(pop_dev)))
        best_score: tuple[float, float, str, int] | None = None
        best_move: tuple[str, int] | None = None
        for uid, d_dest in candidates:
            delta_p = pop[uid]
            new_over = over_pop - delta_p
            new_dest = pop_totals[d_dest] + delta_p
            # Worst pop deviation among the untouched districts:
            other_max = 0.0
            for k in range(n):
                if k in (d_over, d_dest):
                    continue
                v = abs(pop_totals[k] - p_target)
                if v > other_max:
                    other_max = v
            new_max = max(
                other_max,
                abs(new_over - p_target),
                abs(new_dest - p_target),
            )
            # Skip moves that wouldn't improve the picture.
            if new_max >= current_max:
                continue
            # Skip moves that would disconnect d_over.
            if not _removable_without_disconnect(graph, assignment, uid):
                continue
            # Secondary preference: small area-deviation increase.
            new_area_over = area_totals[d_over] - area[uid]
            new_area_dest = area_totals[d_dest] + area[uid]
            area_delta = (
                abs(new_area_over - 0) + abs(new_area_dest - 0)
            )  # raw magnitudes; just a tie-breaker
            key = (new_max, area_delta, uid, d_dest)
            if best_score is None or key < best_score:
                best_score = key
                best_move = (uid, d_dest)

        if best_move is None:
            return moves
        uid, d_dest = best_move
        d_src = assignment[uid]
        assignment[uid] = d_dest
        pop_totals[d_src] -= pop[uid]
        pop_totals[d_dest] += pop[uid]
        area_totals[d_src] -= area[uid]
        area_totals[d_dest] += area[uid]
        moves += 1

    return moves


def _phase_b_area_reduce(
    graph: DualGraph,
    assignment: dict[str, int],
    pop: dict[str, float],
    area: dict[str, float],
    pop_totals: np.ndarray,
    area_totals: np.ndarray,
    p_target: float,
    a_target: float,
    pop_tolerance: float,
    max_passes: int,
) -> int:
    """Pop-neutral pairwise swaps that reduce sum of area deviations.

    For each pair of adjacent districts, find unit pairs (one from each)
    whose swap (1) keeps both districts within ``pop_tolerance``, (2)
    preserves contiguity of both, and (3) reduces the sum of their two
    area deviations. Pick the best such swap globally per pass.
    """
    p_high = p_target * (1 + pop_tolerance)
    p_low = p_target * (1 - pop_tolerance)

    swaps = 0
    for _ in range(max_passes):
        best_gain = 0.0
        best_swap: tuple[str, str] | None = None

        # Boundary unit lookup per district pair.
        for uid in sorted(graph.nodes):
            d1 = assignment[uid]
            for nbr in graph.neighbors(uid):
                d2 = assignment[nbr]
                if d2 == d1 or nbr <= uid:
                    continue
                # Tentative swap uid (in d1) <-> nbr (in d2).
                pop_d1_new = pop_totals[d1] - pop[uid] + pop[nbr]
                pop_d2_new = pop_totals[d2] - pop[nbr] + pop[uid]
                if not (p_low <= pop_d1_new <= p_high):
                    continue
                if not (p_low <= pop_d2_new <= p_high):
                    continue
                area_d1_new = area_totals[d1] - area[uid] + area[nbr]
                area_d2_new = area_totals[d2] - area[nbr] + area[uid]
                gain = (
                    abs(area_totals[d1] - a_target) + abs(area_totals[d2] - a_target)
                    - abs(area_d1_new - a_target) - abs(area_d2_new - a_target)
                )
                if gain <= best_gain:
                    continue
                # Contiguity check (the expensive bit, done last).
                if not _removable_without_disconnect(graph, assignment, uid):
                    continue
                if not _removable_without_disconnect(graph, assignment, nbr):
                    continue
                best_gain = gain
                best_swap = (uid, nbr)

        if best_swap is None:
            return swaps
        uid, nbr = best_swap
        d1 = assignment[uid]
        d2 = assignment[nbr]
        assignment[uid] = d2
        assignment[nbr] = d1
        pop_totals[d1] += pop[nbr] - pop[uid]
        pop_totals[d2] += pop[uid] - pop[nbr]
        area_totals[d1] += area[nbr] - area[uid]
        area_totals[d2] += area[uid] - area[nbr]
        swaps += 1

    return swaps
