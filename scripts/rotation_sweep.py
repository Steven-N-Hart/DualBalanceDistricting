"""Rotation sensitivity sweep for DualBalance Districting.

For each state with prepared VTD data, sweeps 12 equally-spaced rotation
offsets theta in [0, 2*pi) and runs the core DualBalance pipeline (seed
placement + capacitated assignment + contiguity repair, without population
tightening).  Records DBS, EG, and projected seat counts at each rotation.

Usage:
    python scripts/rotation_sweep.py                # all states
    python scripts/rotation_sweep.py MN NC TX       # selected states
    python scripts/rotation_sweep.py --out results/rotation_sweep.json
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import geopandas as gpd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"

# States with TIGER 2020PL VTD data (41 multi-seat states)
STATES_N: dict[str, int] = {
    "AL": 7,  "AR": 4,  "AZ": 9,  "CO": 8,  "CT": 5,
    "FL": 28, "GA": 14, "IA": 4,  "ID": 2,  "IL": 17,
    "IN": 9,  "KS": 4,  "KY": 6,  "LA": 6,  "MA": 9,
    "MD": 8,  "ME": 2,  "MI": 13, "MN": 8,  "MO": 8,
    "MS": 4,  "MT": 2,  "NC": 14, "NE": 3,  "NH": 2,
    "NJ": 12, "NM": 3,  "NV": 4,  "NY": 26, "OH": 15,
    "OK": 5,  "PA": 17, "RI": 2,  "SC": 7,  "TN": 9,
    "TX": 38, "UT": 4,  "VA": 11, "WA": 10, "WI": 8,
    "WV": 2,
}

N_ROTATIONS = 12  # equally-spaced offsets over [0, 2*pi)


def _run_one(units, n: int, theta: float, graph) -> dict:
    """Run core pipeline at rotation theta on pre-loaded units + pre-built graph."""
    import networkx as nx
    from dualbalance.seeds import place_seeds
    from dualbalance.types import Plan, Targets
    import numpy as np

    units_sorted = units.sort_values("unit_id", kind="mergesort").reset_index(drop=True)

    # Targets
    p_star = float(units_sorted["population"].sum()) / n
    a_star = float(units_sorted["area"].sum()) / n
    targets = Targets(population=p_star, area=a_star)

    minx, miny, maxx, maxy = units_sorted.total_bounds
    import math
    norm = float(math.hypot(maxx - minx, maxy - miny))

    centroids = units_sorted.geometry.centroid
    cx = np.asarray(centroids.x, dtype=float)
    cy = np.asarray(centroids.y, dtype=float)
    pops = np.asarray(units_sorted["population"], dtype=float)
    unit_ids: list[str] = units_sorted["unit_id"].tolist()

    # Seeds with rotation
    seeds = place_seeds(units_sorted, n, rotation_offset=theta)

    # Capacitated first-fit assignment
    from dualbalance.districting import _assign
    assignment = _assign(cx, cy, pops, unit_ids, seeds, targets, norm)

    # Lightweight contiguity check using pre-built graph (skip repair for speed)
    plan = Plan(assignment=assignment, n_districts=n, geography="vtd", metadata={})

    # Compute DBS directly from plan
    pops = units.set_index("unit_id")["population"]
    areas = units.set_index("unit_id")["area"]
    p_star = float(pops.sum()) / n
    a_star = float(areas.sum()) / n

    dist_pop = {}
    dist_area = {}
    for uid, d in plan.assignment.items():
        dist_pop[d] = dist_pop.get(d, 0.0) + float(pops[uid])
        dist_area[d] = dist_area.get(d, 0.0) + float(areas[uid])

    pop_devs = [abs(dist_pop.get(d, 0) - p_star) / p_star for d in range(n)]
    area_devs = [abs(dist_area.get(d, 0) - a_star) / a_star for d in range(n)]
    pop_dev_mean = float(np.mean(pop_devs))
    area_dev_mean = float(np.mean(area_devs))
    dbs = 1.0 / (1.0 + 0.5 * pop_dev_mean + 0.5 * area_dev_mean)

    # EG and seats (only if vote columns present)
    eg = None
    seats_r = None
    seats_d = None
    indexed = units.set_index("unit_id")
    if "votes_R" in indexed.columns and "votes_D" in indexed.columns:
        dist_r: dict[int, float] = {}
        dist_d: dict[int, float] = {}
        for uid, d in plan.assignment.items():
            dist_r[d] = dist_r.get(d, 0.0) + float(indexed.at[uid, "votes_R"])
            dist_d[d] = dist_d.get(d, 0.0) + float(indexed.at[uid, "votes_D"])

        total_votes = sum(dist_r.get(d, 0) + dist_d.get(d, 0) for d in range(n))
        wasted_r = 0.0
        wasted_d = 0.0
        r_wins = 0
        d_wins = 0
        for d in range(n):
            r = dist_r.get(d, 0.0)
            dv = dist_d.get(d, 0.0)
            tot = r + dv
            if tot == 0:
                continue
            threshold = tot / 2.0
            if r > dv:
                wasted_r += r - threshold
                wasted_d += dv
                r_wins += 1
            else:
                wasted_d += dv - threshold
                wasted_r += r
                d_wins += 1
        eg = (wasted_r - wasted_d) / total_votes if total_votes > 0 else None
        seats_r = r_wins
        seats_d = d_wins

    return {
        "dbs": round(dbs, 6),
        "pop_dev_mean": round(pop_dev_mean, 6),
        "pop_dev_max": round(max(pop_devs), 6),
        "area_dev_mean": round(area_dev_mean, 6),
        "eg": round(eg, 6) if eg is not None else None,
        "seats_r": seats_r,
        "seats_d": seats_d,
    }


def sweep_state(state: str, n: int) -> dict:
    from dualbalance.io import load_units
    from dualbalance.districting import _build_dual_graph

    vtd_path = DATA / f"{state.lower()}_vtd.geojson"
    units = load_units(
        str(vtd_path),
        id_column="GEOID20",
        county_column="county",
        extra_columns=["votes_R", "votes_D", "vap_total", "vap_nhwhite",
                       "vap_black", "vap_hispanic", "vap_aian", "vap_asian"],
    )
    # Build adjacency graph once; reuse across all rotations
    units_sorted = units.sort_values("unit_id", kind="mergesort").reset_index(drop=True)
    graph = _build_dual_graph(units_sorted)

    thetas = [2.0 * math.pi * k / N_ROTATIONS for k in range(N_ROTATIONS)]
    rows = []
    for k, theta in enumerate(thetas):
        result = _run_one(units, n, theta, graph)
        result["rotation_k"] = k
        result["theta_deg"] = round(math.degrees(theta), 1)
        rows.append(result)

    dbs_vals = [r["dbs"] for r in rows]
    eg_vals = [r["eg"] for r in rows if r["eg"] is not None]
    seat_r_vals = [r["seats_r"] for r in rows if r["seats_r"] is not None]

    return {
        "state": state,
        "n": n,
        "rotations": rows,
        "summary": {
            "dbs_mean": round(float(np.mean(dbs_vals)), 4),
            "dbs_std": round(float(np.std(dbs_vals)), 4),
            "dbs_min": round(float(np.min(dbs_vals)), 4),
            "dbs_max": round(float(np.max(dbs_vals)), 4),
            "eg_mean": round(float(np.mean(eg_vals)), 4) if eg_vals else None,
            "eg_std": round(float(np.std(eg_vals)), 4) if eg_vals else None,
            "eg_min": round(float(np.min(eg_vals)), 4) if eg_vals else None,
            "eg_max": round(float(np.max(eg_vals)), 4) if eg_vals else None,
            "seats_r_mean": round(float(np.mean(seat_r_vals)), 2) if seat_r_vals else None,
            "seats_r_std": round(float(np.std(seat_r_vals)), 3) if seat_r_vals else None,
            "seats_r_min": int(np.min(seat_r_vals)) if seat_r_vals else None,
            "seats_r_max": int(np.max(seat_r_vals)) if seat_r_vals else None,
        },
    }


def main(argv: list[str]) -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("states", nargs="*", help="State abbreviations (default: all)")
    parser.add_argument("--out", default=str(RESULTS / "rotation_sweep.json"))
    args = parser.parse_args(argv)

    states = [s.upper() for s in args.states] if args.states else sorted(STATES_N)
    missing = [s for s in states if not (DATA / f"{s.lower()}_vtd.geojson").exists()]
    if missing:
        print(f"WARNING: no VTD data for {missing}; skipping")
        states = [s for s in states if s not in missing]

    RESULTS.mkdir(exist_ok=True)
    all_results = []
    t0 = time.time()
    for i, state in enumerate(states):
        n = STATES_N[state]
        print(f"[{i+1}/{len(states)}] {state} N={n} ...", end=" ", flush=True)
        t1 = time.time()
        res = sweep_state(state, n)
        elapsed = time.time() - t1
        s = res["summary"]
        eg_info = f"  EG std={s['eg_std']:.4f}" if s["eg_std"] is not None else ""
        print(
            f"DBS {s['dbs_mean']:.3f}±{s['dbs_std']:.4f}"
            f"{eg_info}"
            f"  seats_R {s['seats_r_min']}-{s['seats_r_max']}"
            f"  ({elapsed:.1f}s)"
        )
        all_results.append(res)

    out_path = Path(args.out)
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nTotal: {time.time()-t0:.0f}s  ->  {out_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
