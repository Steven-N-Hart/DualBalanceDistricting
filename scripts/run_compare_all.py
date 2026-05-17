"""Run the complete scoring harness on the six PoC states.

For each state in {IA, MA, MN, NC, WI, TX}:
  1. Generate the DualBalance Districting plan (DualBalance + Phase 1 +
     Phase 2 at VTD scale with Karcher tolerance) and persist it to
     out/<state>_dualbalance/map.geojson. The harness is a VTD-level
     tool, so DualBalance is scored here at VTD scale -- the
     block-scale refinement results are reported separately
     (see the README headline table).
  2. Invoke scripts/compare_state.py to score every available plan
     against the same units with the same metric set.

Writes per-state comparison.json files under out/<state>_compare/ and
prints the consolidated multi-state table at the end.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

from dualbalance.cascade import generate_cascade_plan
from dualbalance.districting import generate_plan
from dualbalance.io import load_units, write_plan
from dualbalance.optimize import optimize_dbs
from dualbalance.states import STATE_INFO


def _discover_states() -> list[tuple[str, int]]:
    """Every state with VTD data on disk and >1 seat."""
    out: list[tuple[str, int]] = []
    for postal, info in sorted(STATE_INFO.items()):
        if info["n_seats"] <= 1:
            continue
        if (REPO / "data" / f"{postal.lower()}_vtd.geojson").exists():
            out.append((postal, info["n_seats"]))
    return out


STATES = _discover_states()
EXTRA = [
    "vap_total", "vap_nhwhite", "vap_black", "vap_hispanic",
    "vap_aian", "vap_asian", "votes_R", "votes_D",
]
KARCHER = 0.0005


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _load_vtd_units(state: str):
    return load_units(
        REPO / "data" / f"{state.lower()}_vtd.geojson",
        id_column="GEOID20", pop_column="population",
        county_column="county", extra_columns=EXTRA,
    )


def ensure_dualbalance_plan(state: str, n: int) -> Path:
    """Generate (if missing) and persist the DualBalance plan at VTD scale."""
    out_dir = REPO / "out" / f"{state.lower()}_dualbalance"
    map_path = out_dir / "map.geojson"
    if map_path.exists():
        log(f"{state}: DualBalance plan already exists, skipping regen")
        return map_path
    log(f"{state}: generating DualBalance plan (DualBalance + Phase 1 + Phase 2)...")
    units = _load_vtd_units(state)
    raw = generate_plan(units, n, geography="vtd")
    opt = optimize_dbs(
        raw, units,
        pop_dev_max_tolerance=KARCHER, max_passes=100000,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    write_plan(opt, units, map_path)
    log(f"  wrote {map_path}")
    return map_path


def ensure_cascade_plan(state: str, n: int) -> Path | None:
    """Generate (if missing) the Iowa-LSA-flavored Cascade plan."""
    out_dir = REPO / "out" / f"{state.lower()}_cascade"
    map_path = out_dir / "map.geojson"
    if map_path.exists():
        log(f"{state}: Cascade plan already exists, skipping regen")
        return map_path
    log(f"{state}: generating Cascade plan...")
    try:
        units = _load_vtd_units(state)
        plan = generate_cascade_plan(units, n, geography="vtd")
    except Exception as exc:  # NotImplementedError when a county is too small to split, etc.
        log(f"  cascade failed: {exc}")
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    write_plan(plan, units, map_path)
    log(f"  wrote {map_path}")
    return map_path


def ensure_bdistricting_plan(state: str) -> Path | None:
    """Ingest Brian Olson's published plan via scripts/prep_bdistricting.py."""
    path = REPO / "data" / f"{state.lower()}_bdistricting.geojson"
    if path.exists():
        log(f"{state}: BDistricting plan already exists, skipping fetch")
        return path
    log(f"{state}: fetching BDistricting plan from Olson...")
    rc = subprocess.call(
        [sys.executable, "scripts/prep_bdistricting.py", "--state", state],
        cwd=REPO,
    )
    if rc != 0 or not path.exists():
        log(f"  BDistricting prep failed (rc={rc})")
        return None
    return path


def main() -> int:
    for state, n in STATES:
        ensure_dualbalance_plan(state, n)
        ensure_cascade_plan(state, n)
        ensure_bdistricting_plan(state)
        log(f"{state}: scripts/compare_state.py")
        subprocess.call(
            [sys.executable, "scripts/compare_state.py", "--state", state],
            cwd=REPO,
        )

    print()
    log("=== consolidated summary (VTD-scale harness) ===")
    rows = {}
    for state, _ in STATES:
        p = REPO / "out" / f"{state.lower()}_compare" / "comparison.json"
        if p.exists():
            rows[state] = json.loads(p.read_text())
    plans = ["dualbalance", "cascade", "bdistricting", "enacted"]
    # Each section prints one metric across all states + plans.
    sections = [
        ("DualBalance Score (higher = better)",      "dualbalance_score",     lambda x: f"{x:.4f}"),
        ("pop_dev_max (lower = more legal)",         "pop_deviation_max",     lambda x: f"{x*100:.2f}%"),
        ("area_dev_mean (lower = more area-equal)",  "area_deviation_mean",   lambda x: f"{x:.3f}"),
        ("Polsby-Popper mean (higher = more compact)", "polsby_popper_mean", lambda x: f"{x:.3f}"),
        ("Reock mean (higher = more compact)",       "reock_mean",            lambda x: f"{x:.3f}"),
        ("Efficiency gap (|x| lower = fairer; >0 = R-favored)",
                                                     "efficiency_gap",        lambda x: f"{x:+.3f}"),
        ("mean_median_R (closer to 0 = fairer)",     "mean_median_R",         lambda x: f"{x:+.3f}"),
        ("Minority-majority districts",              "minority_majority_districts", lambda x: f"{x}"),
        ("Counties split",                           "counties_split",        lambda x: f"{x}"),
    ]
    if rows:
        for title, key, fmt in sections:
            print()
            print(title)
            hdr = f"{'State':<5}" + "".join(f"{p[:13]:>15}" for p in plans)
            print(hdr)
            print("-" * len(hdr))
            for st, data in rows.items():
                vals = []
                for plan in plans:
                    v = data.get(plan, {}).get(key)
                    vals.append("---" if v is None else fmt(v))
                print(f"{st:<5}" + "".join(f"{v:>15}" for v in vals))
    out_summary = REPO / "out" / "compare_all_summary.json"
    out_summary.write_text(json.dumps(rows, indent=2))
    log(f"wrote {out_summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
