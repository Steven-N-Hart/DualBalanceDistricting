"""Deterministic local search that maximizes the DualBalance Score.

Two-phase greedy local search over boundary-unit moves, with an
augmenting-chain escape for the Phase 1 local optimum:

**Phase 1 (pop tightening).** Each step picks the boundary move that
either (a) reduces the L^1 sum of |pop_dev_d|, or (b) strictly
reduces pop_dev_max. When single-move greedy stalls but
pop_dev_max > tolerance, we invoke a *chain escape* (length 2, then
length 3) that searches for an augmenting transport on the
district-adjacency graph: a sequence of boundary moves
``u_0: D_0 -> D_1, u_1: D_1 -> D_2, ...`` chosen so the chain as a
whole strictly reduces pop_dev_max even though no single step does.
This is the deterministic analogue of an ejection chain. Phase 1
terminates only when neither 1-opt nor bounded-chain escape finds an
improving sequence.

**Phase 2 (DBS hill-climb).** Each step picks the boundary move that
maximally improves DBS, subject to pop_dev_max not exceeding the
running maximum (which equals tolerance once Phase 1 has converged
there). Runs until no improving move exists.

Engineering: per-district articulation-point caching (see
:class:`dualbalance.contiguity.ContiguityTracker`) reduces the
contiguity check from ``O(V + E)`` to ``O(1)`` per candidate. A
boundary-unit set tracked incrementally restricts the inner scan to
units that actually have a different-district neighbor, instead of
all units. The chain-escape builds the district arc lists
just-in-time when 1-opt is stuck, so it adds work only when needed.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
from gerrychain import Graph as DualGraph

from dualbalance.contiguity import ContiguityTracker
from dualbalance.types import Plan


def _build_dual_graph(units: gpd.GeoDataFrame) -> DualGraph:
    return DualGraph.from_geodataframe(units.set_index("unit_id"), adjacency="rook")


class _BoundarySet:
    """Tracks units with at least one neighbor in a different district.

    Updated incrementally on each move so the optimizer doesn't have
    to scan every unit every pass.
    """

    def __init__(self, graph: DualGraph, assignment: dict[str, int]):
        self.graph = graph
        self.assignment = assignment
        self.members: set[str] = set()
        for uid in graph.nodes:
            d = assignment[uid]
            for nbr in graph.neighbors(uid):
                if assignment[nbr] != d:
                    self.members.add(uid)
                    break

    def update_after_move(self, uid: str, d_dest: int) -> None:
        """Recompute boundary status for ``uid`` and each of its neighbors."""
        # uid's old district is now d_src (already updated externally); we
        # only need uid's own status plus its neighbors' status.
        self._refresh(uid)
        for nbr in self.graph.neighbors(uid):
            self._refresh(nbr)

    def _refresh(self, uid: str) -> None:
        d = self.assignment[uid]
        is_boundary = any(self.assignment[n] != d for n in self.graph.neighbors(uid))
        if is_boundary:
            self.members.add(uid)
        else:
            self.members.discard(uid)


def optimize_dbs(
    plan: Plan,
    units: gpd.GeoDataFrame,
    *,
    pop_dev_max_tolerance: float | None = None,
    max_passes: int = 100000,
    progress_every: int | None = None,
) -> Plan:
    """Hill-climb the DualBalance Score with optional Reynolds/Karcher constraint.

    If ``progress_every`` is set to a positive integer, the optimizer
    prints a one-line status update every ``progress_every`` accepted
    moves (pop_dev_max, DBS, elapsed wall time, recent moves/sec).
    """
    import time as _time

    n = plan.n_districts
    graph = _build_dual_graph(units)

    indexed = units.set_index("unit_id")
    pop = indexed["population"].astype(float).to_dict()
    area = indexed["area"].astype(float).to_dict()

    p_total = float(units["population"].sum())
    a_total = float(units["area"].sum())
    p_target = p_total / n
    a_target = a_total / n

    assignment = dict(plan.assignment)
    pop_totals = np.zeros(n)
    area_totals = np.zeros(n)
    for uid, d in assignment.items():
        pop_totals[d] += pop[uid]
        area_totals[d] += area[uid]

    contig = ContiguityTracker(graph, assignment)
    boundary = _BoundarySet(graph, assignment)

    def dbs_now() -> float:
        pop_dev_mean = float(np.mean(np.abs(pop_totals - p_target) / p_target))
        area_dev_mean = float(np.mean(np.abs(area_totals - a_target) / a_target))
        return 1.0 / (1.0 + 0.5 * pop_dev_mean + 0.5 * area_dev_mean)

    def pop_dev_max_now() -> float:
        return float(np.max(np.abs(pop_totals - p_target)) / p_target)

    initial_dbs = dbs_now()
    initial_pop_dev_max = pop_dev_max_now()

    _t0 = _time.time()
    _last_progress_t = _t0
    _last_progress_moves = 0

    def _maybe_progress(phase: str, moves: int) -> None:
        nonlocal _last_progress_t, _last_progress_moves
        if not progress_every or moves == 0 or moves % progress_every != 0:
            return
        now = _time.time()
        dt = max(now - _last_progress_t, 1e-9)
        recent = (moves - _last_progress_moves) / dt
        elapsed = now - _t0
        print(
            f"  [{phase} moves={moves} elapsed={elapsed:.1f}s "
            f"recent={recent:.1f}/s pop_dev_max={pop_dev_max_now() * 100:.4f}% "
            f"DBS={dbs_now():.4f}]",
            flush=True,
        )
        _last_progress_t = now
        _last_progress_moves = moves

    def apply_move(uid: str, d_dest: int) -> None:
        d_src = assignment[uid]
        pop_totals[d_src] -= pop[uid]
        pop_totals[d_dest] += pop[uid]
        area_totals[d_src] -= area[uid]
        area_totals[d_dest] += area[uid]
        assignment[uid] = d_dest
        contig.apply_move(uid, d_dest)
        boundary.update_after_move(uid, d_dest)

    def best_contiguous(ranked: list[tuple]) -> tuple | None:
        for entry in ranked:
            if contig.can_remove(entry[1]):
                return entry
        return None

    # --- Chain escape: bounded augmenting paths -----------------------
    def _build_arcs() -> dict[tuple[int, int], list[tuple[float, str]]]:
        """Just-in-time arc lists. arcs[(i, j)] = sorted [(p_u, uid), ...]
        of safe removable units in V_i that have at least one neighbor
        in V_j. Sorted by (p_u, uid) ascending for deterministic
        binary-search matching.
        """
        arcs: dict[tuple[int, int], list[tuple[float, str]]] = {}
        for uid in boundary.members:
            if not contig.can_remove(uid):
                continue
            d_src = assignment[uid]
            seen_dest: set[int] = set()
            for nbr in graph.neighbors(uid):
                d_dest = assignment[nbr]
                if d_dest == d_src or d_dest in seen_dest:
                    continue
                seen_dest.add(d_dest)
                arcs.setdefault((d_src, d_dest), []).append((pop[uid], uid))
        for key in arcs:
            arcs[key].sort()
        return arcs

    def _chain_score(new_devs: np.ndarray, chain: list[tuple[str, int]]) -> tuple:
        """Lex objective for ranking chains. Lower is better.
        Tuple: (max |dev|, sum |dev|, chain length, sorted-uid signature).
        """
        new_max_abs = float(np.max(np.abs(new_devs)))
        new_l1 = float(np.sum(np.abs(new_devs)))
        sig = tuple(sorted(uid for uid, _ in chain))
        return (new_max_abs, new_l1, len(chain), sig)

    def _chain_improves(new_max_abs: float, new_l1: float,
                        cur_max_abs: float, cur_l1: float) -> bool:
        """Accept chains that either strictly cut max-norm, or hold
        max-norm flat while strictly cutting L^1. The L^1 clause is
        what lets us drain one of several max-tied districts: a single
        chain pulls one district below the tie, leaving the others at
        max (so max-norm is unchanged), but the L^1 sum drops by the
        amount drained. The next chain can then target a different
        max-tied district.
        """
        if new_max_abs < cur_max_abs - 1e-9:
            return True
        if new_max_abs <= cur_max_abs + 1e-9 and new_l1 < cur_l1 - 1e-6:
            return True
        return False

    def _length2_chain_for_path(
        d_0: int, d_1: int, d_2: int,
        arcs: dict[tuple[int, int], list[tuple[float, str]]],
        cur_devs: np.ndarray, cur_max_abs: float, cur_l1: float,
    ) -> tuple | None:
        """Length-2: u: d_0 -> d_1, v: d_1 -> d_2. Find lex-best
        improving (u, v).

        For each u in B_{01}, we want v in B_{12} with p_v close to
        p_u (so d_1 stays near unchanged). With the relaxed L^1
        criterion any chain draining d_0 into d_2 typically improves
        L^1, so we two-pointer-walk both sorted-by-pop arrays and
        evaluate pairs whose populations are within a sensible
        neighbourhood. We cap the per-u inner scan to keep the worst
        case bounded; the cap is generous enough that an improving
        chain is essentially never missed in practice.
        """
        import bisect

        B_01 = arcs.get((d_0, d_1))
        B_12 = arcs.get((d_1, d_2))
        if not B_01 or not B_12:
            return None
        B_12_keys = [p for p, _ in B_12]
        # Cap how many v's we evaluate per u so a pathologically large
        # arc list doesn't blow up the worst case. 64 is enough in
        # practice to find an improving chain at block scale.
        WINDOW = 64
        best_score: tuple | None = None
        best_chain: list[tuple[str, int]] | None = None
        for p_u, u in B_01:
            idx = bisect.bisect_left(B_12_keys, p_u)
            # Collect WINDOW indices closest to idx (symmetric outward walk).
            candidates: list[int] = []
            lo = idx - 1
            hi = idx
            while len(candidates) < WINDOW and (lo >= 0 or hi < len(B_12)):
                if hi < len(B_12):
                    candidates.append(hi)
                    hi += 1
                if len(candidates) >= WINDOW:
                    break
                if lo >= 0:
                    candidates.append(lo)
                    lo -= 1
            for j in candidates:
                p_v, v = B_12[j]
                if v == u:
                    continue
                if graph.has_edge(u, v):
                    continue
                new_devs = cur_devs.copy()
                new_devs[d_0] -= p_u
                new_devs[d_1] += p_u - p_v
                new_devs[d_2] += p_v
                new_max_abs = float(np.max(np.abs(new_devs)))
                new_l1 = float(np.sum(np.abs(new_devs)))
                if not _chain_improves(new_max_abs, new_l1, cur_max_abs, cur_l1):
                    continue
                chain = [(u, d_1), (v, d_2)]
                score = _chain_score(new_devs, chain)
                if best_score is None or score < best_score:
                    best_score = score
                    best_chain = chain
        if best_chain is None:
            return None
        return (best_score, best_chain)

    def _length3_chain_for_path(
        d_0: int, d_1: int, d_2: int, d_3: int,
        arcs: dict[tuple[int, int], list[tuple[float, str]]],
        cur_devs: np.ndarray, cur_max_abs: float, cur_l1: float,
    ) -> tuple | None:
        """Length-3: u_0: d_0 -> d_1, u_1: d_1 -> d_2, u_2: d_2 -> d_3.
        Heuristic: enumerate u_0, then for the resulting target on d_1
        do the length-2 sub-problem on (d_1, d_2, d_3).
        """
        import bisect

        B_01 = arcs.get((d_0, d_1))
        B_12 = arcs.get((d_1, d_2))
        B_23 = arcs.get((d_2, d_3))
        if not B_01 or not B_12 or not B_23:
            return None
        B_12_keys = [p for p, _ in B_12]
        B_23_keys = [p for p, _ in B_23]
        best_score: tuple | None = None
        best_chain: list[tuple[str, int]] | None = None
        for p_u0, u0 in B_01:
            target_pv1 = cur_devs[d_1] + p_u0  # want new s_{d_1} ~= 0
            idx = bisect.bisect_left(B_12_keys, target_pv1)
            for j in range(max(0, idx - 2), min(len(B_12), idx + 3)):
                p_u1, u1 = B_12[j]
                if u1 == u0 or graph.has_edge(u0, u1):
                    continue
                # After u0, u1: d_1 receives p_u0, loses p_u1; d_2 gains p_u1.
                # Now want u2: d_2 -> d_3 with p_u2 ~= s_{d_2} + p_u1
                target_pv2 = cur_devs[d_2] + p_u1
                idx2 = bisect.bisect_left(B_23_keys, target_pv2)
                for k in range(max(0, idx2 - 2), min(len(B_23), idx2 + 3)):
                    p_u2, u2 = B_23[k]
                    if u2 in (u0, u1):
                        continue
                    if graph.has_edge(u1, u2) or graph.has_edge(u0, u2):
                        continue
                    new_devs = cur_devs.copy()
                    new_devs[d_0] -= p_u0
                    new_devs[d_1] += p_u0 - p_u1
                    new_devs[d_2] += p_u1 - p_u2
                    new_devs[d_3] += p_u2
                    new_max_abs = float(np.max(np.abs(new_devs)))
                    if new_max_abs >= cur_max_abs - 1e-9:
                        continue
                    chain = [(u0, d_1), (u1, d_2), (u2, d_3)]
                    score = _chain_score(new_devs, chain)
                    if best_score is None or score < best_score:
                        best_score = score
                        best_chain = chain
        if best_chain is None:
            return None
        return (best_score, best_chain)

    def _chain_escape() -> list[tuple[str, int]] | None:
        """Search for a bounded-length chain that reduces pop_dev_max
        (strictly) or holds it flat while reducing the L^1 sum. The
        latter is the case that matters when several districts are
        tied at the max: draining one of them keeps max-norm pinned
        but lowers L^1, opening room for the next chain to attack a
        different tied district.

        Returns the chain as ``[(uid, d_dest), ...]`` in apply order
        (we apply LAST move first, so the caller should reverse).
        """
        cur_devs = pop_totals - p_target
        cur_max_abs = float(np.max(np.abs(cur_devs)))
        cur_l1 = float(np.sum(np.abs(cur_devs)))
        if cur_max_abs <= 1e-9:
            return None
        arcs = _build_arcs()
        if not arcs:
            return None

        # Candidate sources (districts whose |dev| equals current max) and
        # candidate sinks (districts whose dev sign is opposite).
        sources_over = [d for d in range(n) if cur_devs[d] >= cur_max_abs - 1e-9]
        sources_under = [d for d in range(n) if -cur_devs[d] >= cur_max_abs - 1e-9]
        sinks_under = [d for d in range(n) if cur_devs[d] < -1e-9]
        sinks_over = [d for d in range(n) if cur_devs[d] > 1e-9]

        best_score: tuple | None = None
        best_chain: list[tuple[str, int]] | None = None

        # Length-2 chains: D_0 -> D_1 -> D_2 with D_0 source, D_2 sink.
        for d_0 in sources_over:
            for d_1 in range(n):
                if d_1 == d_0 or (d_0, d_1) not in arcs:
                    continue
                for d_2 in sinks_under:
                    if d_2 == d_0 or d_2 == d_1 or (d_1, d_2) not in arcs:
                        continue
                    res = _length2_chain_for_path(d_0, d_1, d_2, arcs, cur_devs, cur_max_abs, cur_l1)
                    if res is None:
                        continue
                    score, chain = res
                    if best_score is None or score < best_score:
                        best_score = score
                        best_chain = chain
        # Symmetric: under-max source, over sink (e.g. fill an under-pop max).
        for d_0 in sources_under:
            for d_1 in range(n):
                if d_1 == d_0 or (d_1, d_0) not in arcs:
                    continue
                for d_2 in sinks_over:
                    if d_2 == d_0 or d_2 == d_1 or (d_2, d_1) not in arcs:
                        continue
                    # Equivalent to reversed chain D_2 -> D_1 -> D_0.
                    res = _length2_chain_for_path(d_2, d_1, d_0, arcs, cur_devs, cur_max_abs, cur_l1)
                    if res is None:
                        continue
                    score, chain = res
                    if best_score is None or score < best_score:
                        best_score = score
                        best_chain = chain

        if best_chain is not None:
            return best_chain

        # Length-3 chains: try if length-2 found nothing.
        for d_0 in sources_over:
            for d_1 in range(n):
                if d_1 == d_0 or (d_0, d_1) not in arcs:
                    continue
                for d_2 in range(n):
                    if d_2 in (d_0, d_1) or (d_1, d_2) not in arcs:
                        continue
                    for d_3 in sinks_under:
                        if d_3 in (d_0, d_1, d_2) or (d_2, d_3) not in arcs:
                            continue
                        res = _length3_chain_for_path(
                            d_0, d_1, d_2, d_3, arcs, cur_devs, cur_max_abs, cur_l1
                        )
                        if res is None:
                            continue
                        score, chain = res
                        if best_score is None or score < best_score:
                            best_score = score
                            best_chain = chain
        return best_chain

    def apply_chain(chain: list[tuple[str, int]]) -> bool:
        """Apply chain moves in REVERSE order with per-step contiguity recheck.
        Returns True if the full chain applied; False if any step was infeasible
        in its updated state (in which case no moves are applied).
        """
        # Verify all steps first by simulating in a snapshot, then commit.
        # Simulation: deep-copy of assignment + pop/area totals + a *fresh*
        # ContiguityTracker would be too slow. Instead we apply forward,
        # check each step's contiguity, and if any fails we roll back.
        applied: list[tuple[str, int, int]] = []  # (uid, d_src, d_dest)
        for uid, d_dest in reversed(chain):
            if not contig.can_remove(uid):
                # Roll back applied moves in reverse.
                for u, d_src_old, d_dest_old in reversed(applied):
                    apply_move(u, d_src_old)  # move back
                return False
            d_src = assignment[uid]
            apply_move(uid, d_dest)
            applied.append((uid, d_src, d_dest))
        return True

    # --- Phase 1: L^1 + max-norm pop tightening, with chain escape ----
    # We accept any move that EITHER reduces the L^1 sum of |pop_dev|
    # OR reduces pop_dev_max (the worst single district's deviation).
    # When single-move greedy stalls but pop_dev_max > tolerance, we
    # invoke a bounded-chain augmenting-path search to escape.
    tighten_moves = 0
    chain_moves_total = 0
    chain_invocations = 0
    if pop_dev_max_tolerance is not None:
        tol_abs = pop_dev_max_tolerance * p_target
        for _ in range(max_passes):
            cur_max = float(np.max(np.abs(pop_totals - p_target)))
            if cur_max <= tol_abs + 1e-9:
                break

            ranked: list[tuple[int, float, str, int]] = []
            for uid in sorted(boundary.members):
                d_src = assignment[uid]
                p_u = pop[uid]
                cur_dev_src = abs(pop_totals[d_src] - p_target)
                new_dev_src = abs(pop_totals[d_src] - p_u - p_target)
                delta_src = new_dev_src - cur_dev_src
                seen: set[int] = set()
                for nbr in graph.neighbors(uid):
                    d_dest = assignment[nbr]
                    if d_dest == d_src or d_dest in seen:
                        continue
                    seen.add(d_dest)
                    cur_dev_dest = abs(pop_totals[d_dest] - p_target)
                    new_dev_dest = abs(pop_totals[d_dest] + p_u - p_target)
                    delta_l1 = delta_src + (new_dev_dest - cur_dev_dest)
                    reduces_max = (
                        new_dev_src < cur_max - 1e-9
                        and new_dev_dest < cur_max - 1e-9
                        and (cur_dev_src >= cur_max - 1e-9 or cur_dev_dest >= cur_max - 1e-9)
                    )
                    if reduces_max:
                        ranked.append((0, delta_l1, uid, d_dest))
                    elif delta_l1 < -1e-9:
                        ranked.append((1, delta_l1, uid, d_dest))

            chosen = None
            if ranked:
                ranked.sort()
                for priority, dl1, uid, d_dest in ranked:
                    if contig.can_remove(uid):
                        chosen = (uid, d_dest)
                        break

            if chosen is not None:
                apply_move(*chosen)
                tighten_moves += 1
                _maybe_progress("tighten", tighten_moves)
                continue

            # 1-opt stalled. Try a bounded-chain escape.
            chain_invocations += 1
            chain = _chain_escape()
            if chain is None:
                break
            if not apply_chain(chain):
                break
            chain_moves_total += len(chain)
            _maybe_progress("tighten", tighten_moves + chain_moves_total)

    # --- Phase 2: DBS hill-climb with running-max constraint -----------
    dbs_moves = 0
    for _ in range(max_passes):
        cur_pop_max_abs = float(np.max(np.abs(pop_totals - p_target)))
        if pop_dev_max_tolerance is not None:
            tol_abs = max(pop_dev_max_tolerance * p_target, cur_pop_max_abs)
        else:
            tol_abs = float("inf")

        ranked = []
        for uid in sorted(boundary.members):
            d_src = assignment[uid]
            p_u = pop[uid]
            a_u = area[uid]

            cur_pop_src = abs(pop_totals[d_src] - p_target)
            new_pop_src = abs(pop_totals[d_src] - p_u - p_target)
            cur_area_src = abs(area_totals[d_src] - a_target)
            new_area_src = abs(area_totals[d_src] - a_u - a_target)

            seen = set()
            for nbr in graph.neighbors(uid):
                d_dest = assignment[nbr]
                if d_dest == d_src or d_dest in seen:
                    continue
                seen.add(d_dest)

                cur_pop_dest = abs(pop_totals[d_dest] - p_target)
                new_pop_dest = abs(pop_totals[d_dest] + p_u - p_target)
                cur_area_dest = abs(area_totals[d_dest] - a_target)
                new_area_dest = abs(area_totals[d_dest] + a_u - a_target)

                if new_pop_src > tol_abs or new_pop_dest > tol_abs:
                    continue

                delta_pop_sum = (new_pop_src + new_pop_dest) - (cur_pop_src + cur_pop_dest)
                delta_area_sum = (new_area_src + new_area_dest) - (cur_area_src + cur_area_dest)
                delta_weighted = (
                    0.5 * delta_pop_sum / p_target + 0.5 * delta_area_sum / a_target
                ) / n

                if delta_weighted < -1e-12:
                    ranked.append((delta_weighted, uid, d_dest))

        if not ranked:
            break
        ranked.sort()
        chosen = best_contiguous(ranked)
        if chosen is None:
            break
        _, uid, d_dest = chosen
        apply_move(uid, d_dest)
        dbs_moves += 1
        _maybe_progress("dbs", dbs_moves)

    final_dbs = dbs_now()
    final_pop_dev_max = pop_dev_max_now()

    new_meta = dict(plan.metadata)
    new_meta["optimize_dbs_moves"] = tighten_moves + chain_moves_total + dbs_moves
    new_meta["optimize_dbs_tighten_moves"] = tighten_moves
    new_meta["optimize_dbs_chain_moves"] = chain_moves_total
    new_meta["optimize_dbs_chain_invocations"] = chain_invocations
    new_meta["optimize_dbs_dbs_moves"] = dbs_moves
    new_meta["optimize_dbs_initial_dbs"] = initial_dbs
    new_meta["optimize_dbs_final_dbs"] = final_dbs
    new_meta["optimize_dbs_initial_pop_dev_max"] = initial_pop_dev_max
    new_meta["optimize_dbs_final_pop_dev_max"] = final_pop_dev_max
    if pop_dev_max_tolerance is not None:
        new_meta["optimize_dbs_pop_max_tolerance"] = pop_dev_max_tolerance

    return Plan(
        assignment=assignment,
        n_districts=plan.n_districts,
        geography=plan.geography,
        metadata=new_meta,
    )
