"""Run the VTD->block DualBalance pipeline for all 50 states.

For each state with >1 congressional district:
  1. Skip prep if data/<state>_vtd.geojson and _block.geojson already exist.
  2. Otherwise call scripts/prep_state_units.py to download TIGER +
     Census + cd119 data.
  3. Run _test_block_from_vtd.py and capture metrics.

Results are appended to out/all50_results.json after each state so a
crash mid-loop loses at most one state's run. Re-runs of the script
skip states whose results are already recorded.

Usage:
    python _run_all_states.py            # all states
    python _run_all_states.py CA OR WA   # subset

Background-friendly: run with ``python -u _run_all_states.py``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent
RESULTS = REPO / "out" / "all50_results.json"

# State FIPS, TIGER state-name (used in the prep download URL), 119th-Congress
# apportioned seat count. 1-seat states get skipped (n_districts=1 has no
# districting to do).
ALL_STATES: dict[str, dict] = {
    "AL": {"fips": "01", "tiger_name": "ALABAMA",         "n_seats":  7},
    "AK": {"fips": "02", "tiger_name": "ALASKA",          "n_seats":  1},
    "AZ": {"fips": "04", "tiger_name": "ARIZONA",         "n_seats":  9},
    "AR": {"fips": "05", "tiger_name": "ARKANSAS",        "n_seats":  4},
    "CA": {"fips": "06", "tiger_name": "CALIFORNIA",      "n_seats": 52},
    "CO": {"fips": "08", "tiger_name": "COLORADO",        "n_seats":  8},
    "CT": {"fips": "09", "tiger_name": "CONNECTICUT",     "n_seats":  5},
    "DE": {"fips": "10", "tiger_name": "DELAWARE",        "n_seats":  1},
    "FL": {"fips": "12", "tiger_name": "FLORIDA",         "n_seats": 28},
    "GA": {"fips": "13", "tiger_name": "GEORGIA",         "n_seats": 14},
    "HI": {"fips": "15", "tiger_name": "HAWAII",          "n_seats":  2},
    "ID": {"fips": "16", "tiger_name": "IDAHO",           "n_seats":  2},
    "IL": {"fips": "17", "tiger_name": "ILLINOIS",        "n_seats": 17},
    "IN": {"fips": "18", "tiger_name": "INDIANA",         "n_seats":  9},
    "IA": {"fips": "19", "tiger_name": "IOWA",            "n_seats":  4},
    "KS": {"fips": "20", "tiger_name": "KANSAS",          "n_seats":  4},
    "KY": {"fips": "21", "tiger_name": "KENTUCKY",        "n_seats":  6},
    "LA": {"fips": "22", "tiger_name": "LOUISIANA",       "n_seats":  6},
    "ME": {"fips": "23", "tiger_name": "MAINE",           "n_seats":  2},
    "MD": {"fips": "24", "tiger_name": "MARYLAND",        "n_seats":  8},
    "MA": {"fips": "25", "tiger_name": "MASSACHUSETTS",   "n_seats":  9},
    "MI": {"fips": "26", "tiger_name": "MICHIGAN",        "n_seats": 13},
    "MN": {"fips": "27", "tiger_name": "MINNESOTA",       "n_seats":  8},
    "MS": {"fips": "28", "tiger_name": "MISSISSIPPI",     "n_seats":  4},
    "MO": {"fips": "29", "tiger_name": "MISSOURI",        "n_seats":  8},
    "MT": {"fips": "30", "tiger_name": "MONTANA",         "n_seats":  2},
    "NE": {"fips": "31", "tiger_name": "NEBRASKA",        "n_seats":  3},
    "NV": {"fips": "32", "tiger_name": "NEVADA",          "n_seats":  4},
    "NH": {"fips": "33", "tiger_name": "NEW_HAMPSHIRE",   "n_seats":  2},
    "NJ": {"fips": "34", "tiger_name": "NEW_JERSEY",      "n_seats": 12},
    "NM": {"fips": "35", "tiger_name": "NEW_MEXICO",      "n_seats":  3},
    "NY": {"fips": "36", "tiger_name": "NEW_YORK",        "n_seats": 26},
    "NC": {"fips": "37", "tiger_name": "NORTH_CAROLINA",  "n_seats": 14},
    "ND": {"fips": "38", "tiger_name": "NORTH_DAKOTA",    "n_seats":  1},
    "OH": {"fips": "39", "tiger_name": "OHIO",            "n_seats": 15},
    "OK": {"fips": "40", "tiger_name": "OKLAHOMA",        "n_seats":  5},
    "OR": {"fips": "41", "tiger_name": "OREGON",          "n_seats":  6},
    "PA": {"fips": "42", "tiger_name": "PENNSYLVANIA",    "n_seats": 17},
    "RI": {"fips": "44", "tiger_name": "RHODE_ISLAND",    "n_seats":  2},
    "SC": {"fips": "45", "tiger_name": "SOUTH_CAROLINA",  "n_seats":  7},
    "SD": {"fips": "46", "tiger_name": "SOUTH_DAKOTA",    "n_seats":  1},
    "TN": {"fips": "47", "tiger_name": "TENNESSEE",       "n_seats":  9},
    "TX": {"fips": "48", "tiger_name": "TEXAS",           "n_seats": 38},
    "UT": {"fips": "49", "tiger_name": "UTAH",            "n_seats":  4},
    "VT": {"fips": "50", "tiger_name": "VERMONT",         "n_seats":  1},
    "VA": {"fips": "51", "tiger_name": "VIRGINIA",        "n_seats": 11},
    "WA": {"fips": "53", "tiger_name": "WASHINGTON",      "n_seats": 10},
    "WV": {"fips": "54", "tiger_name": "WEST_VIRGINIA",   "n_seats":  2},
    "WI": {"fips": "55", "tiger_name": "WISCONSIN",       "n_seats":  8},
    "WY": {"fips": "56", "tiger_name": "WYOMING",         "n_seats":  1},
}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def load_results() -> dict:
    if RESULTS.exists():
        return json.loads(RESULTS.read_text())
    return {}


def save_results(d: dict) -> None:
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(d, indent=2))


def patch_state_info_if_needed(postal: str, info: dict) -> None:
    """Make sure src/dualbalance/states.py knows about this state so the
    prep script accepts it. Patch idempotently."""
    from dualbalance.states import STATE_INFO

    if postal in STATE_INFO:
        return
    STATE_INFO[postal] = {
        "fips": info["fips"],
        "tiger_name": info["tiger_name"],
        "n_seats": info["n_seats"],
    }


def run(cmd: list[str], log_to: Path) -> int:
    log(f"$ {' '.join(cmd)}  (-> {log_to.name})")
    log_to.parent.mkdir(parents=True, exist_ok=True)
    with open(log_to, "w") as f:
        proc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=REPO)
    return proc.returncode


def need_prep(state: str) -> tuple[bool, bool]:
    state_lc = state.lower()
    vtd = (REPO / "data" / f"{state_lc}_vtd.geojson").exists()
    blk = (REPO / "data" / f"{state_lc}_block.geojson").exists()
    return (not vtd, not blk)


def parse_block_metrics(log_path: Path) -> dict | None:
    """Parse the final 'BLOCK result' line from _test_block_from_vtd.py output."""
    if not log_path.exists():
        return None
    text = log_path.read_text(errors="replace")
    for line in reversed(text.splitlines()):
        if "BLOCK result:" in line:
            # e.g., "BLOCK result: DBS=0.9651 pop_dev_max=0.000499 tight=0 chain=0/0 dbs=12235"
            parts = {}
            for token in line.split("BLOCK result:")[1].split():
                if "=" in token:
                    k, v = token.split("=", 1)
                    parts[k] = v
            return {
                "dbs": float(parts.get("DBS", "nan")),
                "pop_dev_max": float(parts.get("pop_dev_max", "nan")),
                "tight": int(parts.get("tight", "0")),
                "chain_moves": parts.get("chain", "0/0"),
                "dbs_moves": int(parts.get("dbs", "0")),
            }
    return None


def process_state(postal: str, info: dict, results: dict) -> None:
    n = info["n_seats"]
    if n <= 1:
        log(f"{postal}: 1-seat state, skipping")
        results[postal] = {"skipped": "single_seat", "n_seats": n}
        save_results(results)
        return
    if postal in results and "block" in results[postal]:
        log(f"{postal}: result already recorded, skipping")
        return

    state_lc = postal.lower()
    patch_state_info_if_needed(postal, info)
    log(f"=== {postal} (N={n}) ===")
    t0 = time.time()

    log_dir = REPO / "out" / "all50_logs"
    need_vtd, need_blk = need_prep(postal)

    if need_vtd:
        rc = run(
            [sys.executable, "scripts/prep_state_units.py",
             "--state", postal, "--geography", "vtd"],
            log_dir / f"{state_lc}_prep_vtd.log",
        )
        if rc != 0:
            log(f"  prep VTD FAILED rc={rc}")
            results[postal] = {"error": "prep_vtd_failed", "n_seats": n}
            save_results(results)
            return

    if need_blk:
        rc = run(
            [sys.executable, "scripts/prep_state_units.py",
             "--state", postal, "--geography", "block",
             "--enacted-out", f"data/{state_lc}_block_enacted.geojson"],
            log_dir / f"{state_lc}_prep_block.log",
        )
        if rc != 0:
            log(f"  prep BLOCK FAILED rc={rc}")
            results[postal] = {"error": "prep_block_failed", "n_seats": n}
            save_results(results)
            return

    rc = run(
        [sys.executable, "-u", "_test_block_from_vtd.py", postal, str(n)],
        log_dir / f"{state_lc}_test.log",
    )
    if rc != 0:
        log(f"  test FAILED rc={rc}")
        results[postal] = {"error": "test_failed", "n_seats": n}
        save_results(results)
        return

    metrics = parse_block_metrics(log_dir / f"{state_lc}_test.log")
    if metrics is None:
        log(f"  could not parse metrics from log")
        results[postal] = {"error": "parse_failed", "n_seats": n}
    else:
        results[postal] = {
            "n_seats": n,
            "block": metrics,
            "elapsed_min": round((time.time() - t0) / 60, 1),
        }
        log(f"  DBS={metrics['dbs']:.4f} pop_dev_max={metrics['pop_dev_max']*100:.4f}% "
            f"({results[postal]['elapsed_min']}min)")
    save_results(results)


def main(argv: list[str]) -> int:
    targets = argv[1:] if len(argv) > 1 else sorted(ALL_STATES.keys())
    results = load_results()
    log(f"running {len(targets)} state(s); results -> {RESULTS}")
    for postal in targets:
        if postal not in ALL_STATES:
            log(f"{postal}: unknown state, skipping")
            continue
        try:
            process_state(postal, ALL_STATES[postal], results)
        except Exception as exc:  # noqa: BLE001
            log(f"{postal}: exception {exc}")
            results[postal] = {"error": f"exception: {exc}", "n_seats": ALL_STATES[postal]["n_seats"]}
            save_results(results)
    log("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
