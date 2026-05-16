"""Collect race + partisan metrics for DualBalance (VTD-Karcher) and Enacted.

For each of the 6 states:
- Load VTD units with race + partisan diagnostic columns.
- Run optimizer at Karcher tolerance to get the VTD DualBalance plan.
- Score the VTD plan to get minority_majority_districts, seats_R/D,
  efficiency_gap, etc.
- Load and score the enacted plan against the same units.

Outputs a single JSON with rows keyed by state.
"""

from __future__ import annotations

import json
import time

from dualbalance.districting import generate_plan
from dualbalance.io import load_plan, load_units
from dualbalance.optimize import optimize_dbs
from dualbalance.scoring import score_plan

EXTRA = [
    "vap_total", "vap_nhwhite", "vap_black", "vap_hispanic",
    "vap_aian", "vap_asian", "votes_R", "votes_D",
]
STATES = [("MN", 8), ("IA", 4), ("MA", 9), ("WI", 8), ("NC", 14), ("TX", 38)]
KARCHER = 0.0005

KEYS = [
    "dualbalance_score",
    "pop_deviation_max",
    "area_deviation_mean",
    "minority_majority_districts",
    "seats_R",
    "seats_D",
    "statewide_share_R",
    "efficiency_gap",
    "mean_median_R",
]


def slim(metrics: dict) -> dict:
    return {k: metrics.get(k) for k in KEYS}


out: dict[str, dict] = {}
for postal, n in STATES:
    print(f"=== {postal} (N={n}) ===", flush=True)
    state = postal.lower()
    t0 = time.time()
    units = load_units(
        f"data/{state}_vtd.geojson",
        id_column="GEOID20", pop_column="population",
        county_column="county", extra_columns=EXTRA,
    )
    print(f"  loaded {len(units):,} VTDs ({time.time() - t0:.1f}s)", flush=True)

    prism = generate_plan(units, n, geography="vtd")
    opt = optimize_dbs(prism, units, pop_dev_max_tolerance=KARCHER, max_passes=100000)
    opt_metrics = slim(score_plan(opt, units))
    print(f"  DualBalance (VTD-Karcher): {opt_metrics}", flush=True)

    enacted = load_plan(f"data/{state}_enacted.geojson", geography="vtd")
    enacted_metrics = slim(score_plan(enacted, units))
    print(f"  Enacted: {enacted_metrics}", flush=True)

    out[postal] = {"dualbalance": opt_metrics, "enacted": enacted_metrics}

with open("out/race_partisan.json", "w") as f:
    json.dump(out, f, indent=2)
print("\nwrote out/race_partisan.json")
