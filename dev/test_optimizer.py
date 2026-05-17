"""Reynolds-constrained DBS optimizer test (two-phase optimizer).

Init: DualBalance raw (no separate tighten step needed).
Optimize: two-phase greedy with Reynolds constraint.
  Phase 1 (max-norm): drive pop_dev_max down to <= 0.005.
  Phase 2 (DBS): hill-climb DBS subject to pop_dev_max <= 0.005.
Compare optimized DBS vs enacted DBS on each state.
"""

from __future__ import annotations

import json
import time

from dualbalance.districting import generate_plan
from dualbalance.io import load_plan, load_units
from dualbalance.optimize import optimize_dbs
from dualbalance.scoring import score_plan

EXTRA = [
    "vap_total",
    "vap_nhwhite",
    "vap_black",
    "vap_hispanic",
    "vap_aian",
    "vap_asian",
    "votes_R",
    "votes_D",
]

STATES = [
    ("MN", 8),
    ("IA", 4),
    ("MA", 9),
    ("WI", 8),
    ("NC", 14),
    ("TX", 38),  # last; biggest
]

POP_TOLERANCE = 0.0005  # Karcher (0.05% target for congressional)


def run_state(postal: str, n: int) -> dict:
    state = postal.lower()
    units = load_units(
        f"data/{state}_vtd.geojson",
        id_column="GEOID20",
        pop_column="population",
        county_column="county",
        extra_columns=EXTRA,
    )

    t0 = time.time()
    prism = generate_plan(units, n, geography="vtd")
    prism_metrics = score_plan(prism, units)
    prism_time = time.time() - t0

    t1 = time.time()
    opt = optimize_dbs(prism, units, pop_dev_max_tolerance=POP_TOLERANCE, max_passes=10000)
    opt_metrics = score_plan(opt, units)
    optimize_time = time.time() - t1

    enacted = load_plan(f"data/{state}_enacted.geojson", geography="vtd")
    enacted_metrics = score_plan(enacted, units)

    return {
        "state": postal,
        "n_districts": n,
        "n_units": len(units),
        # DualBalance raw
        "prism_dbs": prism_metrics["dualbalance_score"],
        "prism_pop_dev_max": prism_metrics["pop_deviation_max"],
        "prism_time_s": round(prism_time, 1),
        # Optimized
        "opt_dbs": opt_metrics["dualbalance_score"],
        "opt_pop_dev_max": opt_metrics["pop_deviation_max"],
        "opt_area_dev_mean": opt_metrics["area_deviation_mean"],
        "opt_counties_split": opt_metrics["counties_split"],
        "opt_moves_total": opt.metadata.get("optimize_dbs_moves"),
        "opt_moves_tighten": opt.metadata.get("optimize_dbs_tighten_moves"),
        "opt_moves_chain": opt.metadata.get("optimize_dbs_chain_moves", 0),
        "opt_chain_invocations": opt.metadata.get("optimize_dbs_chain_invocations", 0),
        "opt_moves_dbs": opt.metadata.get("optimize_dbs_dbs_moves"),
        "optimize_time_s": round(optimize_time, 1),
        # Enacted
        "enacted_dbs": enacted_metrics["dualbalance_score"],
        "enacted_pop_dev_max": enacted_metrics["pop_deviation_max"],
        "enacted_area_dev_mean": enacted_metrics["area_deviation_mean"],
        "enacted_counties_split": enacted_metrics["counties_split"],
        "winner": "OPT"
        if opt_metrics["dualbalance_score"] >= enacted_metrics["dualbalance_score"]
        else "ENACTED",
        "reynolds_ok": opt_metrics["pop_deviation_max"] <= POP_TOLERANCE + 1e-6,
    }


def main() -> int:
    results = []
    for postal, n in STATES:
        print(f"\n========== {postal} ==========")
        try:
            r = run_state(postal, n)
            results.append(r)
            print(json.dumps(r, indent=2))
        except Exception as exc:
            print(f"FAILED: {exc}")
            import traceback

            traceback.print_exc()
            results.append({"state": postal, "error": str(exc)})

    print("\n========== SUMMARY ==========")
    print(
        f"{'State':<5} {'N':>3} "
        f"{'DualBalance':>7} {'Opt':>7} {'Enacted':>8} "
        f"{'Winner':>7} {'Reyn':>5} "
        f"{'TightMv':>7} {'Chain':>11} {'DbsMv':>6} "
        f"{'TotalTime':>9} {'OptPopMax%':>10}"
    )
    for r in results:
        if "error" in r:
            print(f"{r['state']:<5} ERROR: {r['error']}")
            continue
        total_time = r["prism_time_s"] + r["optimize_time_s"]
        reyn = "Y" if r["reynolds_ok"] else "N"
        print(
            f"{r['state']:<5} {r['n_districts']:>3} "
            f"{r['prism_dbs']:>7.4f} {r['opt_dbs']:>7.4f} "
            f"{r['enacted_dbs']:>8.4f} "
            f"{r['winner']:>7} {reyn:>5} "
            f"{r['opt_moves_tighten']:>7} "
            f"{r['opt_chain_invocations']:>5}/{r['opt_moves_chain']:<5} "
            f"{r['opt_moves_dbs']:>6} "
            f"{total_time:>8.0f}s {r['opt_pop_dev_max'] * 100:>9.2f}%"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
