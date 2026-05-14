"""Optional post-assignment population-tightening pass.

Pure radial assignment produces districts balanced on the DualBalance
score but with per-district population deviation typically in the
5-15 % range on real census geometry — well above the ~0.5-1 %
*Reynolds v. Sims* target. This module provides an opt-in greedy
swap procedure that moves boundary units between districts to reduce
the sum of absolute population deviations (L¹), until either every
district is within ``pop_tolerance`` of P* or no contiguity-preserving
move can further reduce the L¹ objective.

The pass is intentionally a separate module gated by an explicit CLI
flag (``--tighten-pop``). It is the only piece of the pipeline that
is not a pure function of (units, n_districts) — running it weakens
the visual radial structure (units near slice boundaries may end up
in non-obvious districts) and adds a non-trivial knob
(``--pop-tolerance``). Whether to ship a plan with or without
tightening is a project-level decision; this module just makes the
choice available.

The L¹ objective is used (not the L∞ ``max_i |Pop(D_i) - P*|``)
because radial geometries place the over-target and under-target
districts on opposite sides of the population centroid: no single
adjacent-slice swap reduces the max, but many such swaps reduce the
sum.
"""

from __future__ import annotations

import geopandas as gpd
import networkx as nx
import numpy as np
from gerrychain import Graph as DualGraph

from dualbalance.types import Plan


def _build_dual_graph(units: gpd.GeoDataFrame) -> DualGraph:
    return DualGraph.from_geodataframe(units.set_index("unit_id"), adjacency="rook")


def _removable_without_disconnect(graph: DualGraph, assignment: dict[str, int], uid: str) -> bool:
    """True iff removing ``uid`` from its district keeps that district
    connected (and non-empty)."""
    d = assignment[uid]
    same_district = [n for n, dd in assignment.items() if dd == d and n != uid]
    if not same_district:
        return False
    return nx.is_connected(graph.subgraph(same_district))


def tighten_population(
    plan: Plan,
    units: gpd.GeoDataFrame,
    *,
    pop_tolerance: float = 0.01,
    max_passes: int = 50000,
) -> Plan:
    """Tighten population balance via greedy boundary-unit swaps.

    Each pass: enumerate every boundary unit and every (uid, d_dest)
    transfer that strictly reduces the L¹ deviation
    ``Σ_i |Pop(D_i) - P*|``. Sort those candidates by improvement,
    and accept the most-improving one whose source remains contiguous
    after the move. Stops when every district is within
    ``pop_tolerance`` of P* OR no contiguity-preserving improving move
    exists OR ``max_passes`` is reached.

    Returns a new ``Plan``; does not mutate the input. The metadata
    of the returned plan records:

    - ``tighten_pop_moves`` — number of swaps performed
    - ``tighten_pop_tolerance`` — the tolerance argument
    - ``tighten_pop_final_dev_max`` — the post-tighten max deviation
    """
    if pop_tolerance < 0:
        raise ValueError(f"pop_tolerance must be >= 0, got {pop_tolerance}")
    n = plan.n_districts
    graph = _build_dual_graph(units)

    indexed = units.set_index("unit_id")
    pop = indexed["population"].astype(float).to_dict()

    assignment = dict(plan.assignment)
    p_target = float(units["population"].sum()) / n
    pop_totals = np.zeros(n)
    for uid, d in assignment.items():
        pop_totals[d] += pop[uid]

    sorted_nodes = sorted(graph.nodes)
    tol_abs = p_target * pop_tolerance

    moves = 0
    for _ in range(max_passes):
        dev = pop_totals - p_target
        if dev.max() <= tol_abs and dev.min() >= -tol_abs:
            break

        ranked: list[tuple[float, str, int]] = []
        for uid in sorted_nodes:
            d_src = assignment[uid]
            p_u = pop[uid]
            delta_src = abs(dev[d_src] - p_u) - abs(dev[d_src])
            seen: set[int] = set()
            for nbr in graph.neighbors(uid):
                d_dest = assignment[nbr]
                if d_dest == d_src or d_dest in seen:
                    continue
                seen.add(d_dest)
                delta = delta_src + abs(dev[d_dest] + p_u) - abs(dev[d_dest])
                if delta < -1e-9:
                    ranked.append((delta, uid, d_dest))

        if not ranked:
            break
        ranked.sort()  # most-improving first; ties break (uid, d_dest) asc

        chosen: tuple[str, int] | None = None
        for _, uid, d_dest in ranked:
            if _removable_without_disconnect(graph, assignment, uid):
                chosen = (uid, d_dest)
                break

        if chosen is None:
            break
        uid, d_dest = chosen
        d_src = assignment[uid]
        assignment[uid] = d_dest
        pop_totals[d_src] -= pop[uid]
        pop_totals[d_dest] += pop[uid]
        moves += 1

    final_dev_max = float(np.max(np.abs(pop_totals - p_target)) / p_target)

    new_meta = dict(plan.metadata)
    new_meta["tighten_pop_moves"] = moves
    new_meta["tighten_pop_tolerance"] = pop_tolerance
    new_meta["tighten_pop_final_dev_max"] = final_dev_max

    return Plan(
        assignment=assignment,
        n_districts=plan.n_districts,
        geography=plan.geography,
        metadata=new_meta,
    )
