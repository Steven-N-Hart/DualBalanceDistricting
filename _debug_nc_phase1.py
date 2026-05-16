"""Diagnose why Phase 1 stops on NC with pop_dev_max ~34%.

Runs the optimizer manually one pass at a time and reports for each pass:
- pop_dev per district (sorted desc by |dev|)
- # candidate improving moves (delta < 0)
- # contiguous improving moves (passes contig.can_remove)
- the move taken (or "stuck" reason)

Bypasses optimize_dbs to expose internal state.
"""

from __future__ import annotations

import time

import numpy as np

from dualbalance.contiguity import ContiguityTracker
from dualbalance.districting import generate_plan
from dualbalance.io import load_units
from dualbalance.optimize import _BoundarySet, _build_dual_graph

EXTRA = ["vap_total", "vap_nhwhite", "vap_black", "vap_hispanic", "vap_aian", "vap_asian",
         "votes_R", "votes_D"]


def main() -> int:
    units = load_units(
        "data/nc_vtd.geojson",
        id_column="GEOID20",
        pop_column="population",
        county_column="county",
        extra_columns=EXTRA,
    )
    n = 14
    print(f"loaded {len(units):,} NC VTDs, n={n}")

    print("generating PRISM seed plan…")
    plan = generate_plan(units, n, geography="vtd")

    graph = _build_dual_graph(units)
    indexed = units.set_index("unit_id")
    pop = indexed["population"].astype(float).to_dict()

    p_total = float(units["population"].sum())
    p_target = p_total / n

    assignment = dict(plan.assignment)
    pop_totals = np.zeros(n)
    for uid, d in assignment.items():
        pop_totals[d] += pop[uid]

    contig = ContiguityTracker(graph, assignment)
    boundary = _BoundarySet(graph, assignment)

    print(f"\nideal pop/dist = {p_target:,.0f}")
    print(f"initial pop_dev_max = {np.max(np.abs(pop_totals - p_target)) / p_target * 100:.2f}%")

    # Run Phase 1 manually with diagnostics.
    pop_dev_max_tolerance = 0.005
    tol_abs = pop_dev_max_tolerance * p_target

    for pass_no in range(1, 1000):
        cur_max_abs = float(np.max(np.abs(pop_totals - p_target)))
        if cur_max_abs <= tol_abs + 1e-9:
            print(f"\n[{pass_no:04d}] DONE: pop_dev_max {cur_max_abs/p_target*100:.4f}% within tolerance")
            break

        # Build all candidate improving moves.
        candidates: list[tuple[float, str, int]] = []
        for uid in sorted(boundary.members):
            d_src = assignment[uid]
            p_u = pop[uid]
            delta_src = abs(pop_totals[d_src] - p_u - p_target) - abs(pop_totals[d_src] - p_target)
            seen: set[int] = set()
            for nbr in graph.neighbors(uid):
                d_dest = assignment[nbr]
                if d_dest == d_src or d_dest in seen:
                    continue
                seen.add(d_dest)
                delta = delta_src + abs(pop_totals[d_dest] + p_u - p_target) - abs(pop_totals[d_dest] - p_target)
                if delta < -1e-9:
                    candidates.append((delta, uid, d_dest))

        n_candidates = len(candidates)
        if n_candidates == 0:
            # No improving move. Report the worst district and its neighbors.
            worst_d = int(np.argmax(np.abs(pop_totals - p_target)))
            worst_dev = (pop_totals[worst_d] - p_target) / p_target * 100
            print(f"\n[{pass_no:04d}] STUCK: no improving L1 move")
            print(f"  pop_dev_max = {cur_max_abs/p_target*100:.2f}% on district {worst_d}")
            print(f"  worst district pop = {pop_totals[worst_d]:,.0f} (dev {worst_dev:+.2f}%)")
            # How many boundary units of worst district are not articulation points?
            worst_boundary_units = [u for u in boundary.members if assignment[u] == worst_d]
            movable = [u for u in worst_boundary_units if contig.can_remove(u)]
            print(f"  boundary units in worst district: {len(worst_boundary_units)} total, "
                  f"{len(movable)} movable (not articulation)")
            # What deltas do MOVABLE boundary units in worst district have?
            best_movable_delta = None
            for u in movable:
                p_u = pop[u]
                d_src = assignment[u]
                delta_src = abs(pop_totals[d_src] - p_u - p_target) - abs(pop_totals[d_src] - p_target)
                seen = set()
                for nbr in graph.neighbors(u):
                    d_dest = assignment[nbr]
                    if d_dest == d_src or d_dest in seen:
                        continue
                    seen.add(d_dest)
                    delta = delta_src + abs(pop_totals[d_dest] + p_u - p_target) - abs(pop_totals[d_dest] - p_target)
                    if best_movable_delta is None or delta < best_movable_delta:
                        best_movable_delta = delta
            print(f"  best L1 delta among movable boundary units in worst district: {best_movable_delta}")
            # All districts pop_dev sorted
            devs = sorted(((pop_totals[i] - p_target) / p_target * 100, i) for i in range(n))
            print(f"  all districts (dev%, id): {[(round(d, 2), i) for d, i in devs]}")

            # Look for moves that reduce pop_dev_max (max-norm improvement) even if L1 doesn't improve.
            # Scan all boundary units (not just worst district).
            cur_max_per_dist = np.abs(pop_totals - p_target)
            max_norm_candidates = []
            for u in boundary.members:
                if not contig.can_remove(u):
                    continue
                d_src = assignment[u]
                p_u = pop[u]
                seen = set()
                for nbr in graph.neighbors(u):
                    d_dest = assignment[nbr]
                    if d_dest == d_src or d_dest in seen:
                        continue
                    seen.add(d_dest)
                    new_src = abs(pop_totals[d_src] - p_u - p_target)
                    new_dest = abs(pop_totals[d_dest] + p_u - p_target)
                    new_max = max(
                        new_src, new_dest,
                        np.max(np.delete(cur_max_per_dist, [d_src, d_dest])) if n > 2 else 0.0,
                    )
                    if new_max < cur_max_abs - 1e-9:
                        max_norm_candidates.append((new_max - cur_max_abs, u, d_dest))
            print(f"  max-norm-reducing movable candidates (ignoring L1): {len(max_norm_candidates)}")
            if max_norm_candidates:
                max_norm_candidates.sort()
                top = max_norm_candidates[:5]
                for delta_max, uid, d_dest in top:
                    print(f"    delta_max={delta_max:+.1f}  uid={uid}  D{assignment[uid]}->D{d_dest}")
            break

        # Apply best contiguous move.
        candidates.sort()
        chosen = None
        for entry in candidates:
            if contig.can_remove(entry[1]):
                chosen = entry
                break
        if chosen is None:
            print(f"\n[{pass_no:04d}] STUCK: {n_candidates} improving moves all blocked by contiguity")
            break

        delta, uid, d_dest = chosen
        d_src = assignment[uid]
        pop_totals[d_src] -= pop[uid]
        pop_totals[d_dest] += pop[uid]
        assignment[uid] = d_dest
        contig.apply_move(uid, d_dest)
        boundary.update_after_move(uid, d_dest)

        if pass_no % 25 == 1:
            print(f"[{pass_no:04d}] pop_dev_max={cur_max_abs/p_target*100:5.2f}% "
                  f"candidates={n_candidates:5d} chose delta={delta:+.1f} uid={uid} -> D{d_dest}")

    final_max = float(np.max(np.abs(pop_totals - p_target)))
    print(f"\nfinal pop_dev_max = {final_max/p_target*100:.4f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
