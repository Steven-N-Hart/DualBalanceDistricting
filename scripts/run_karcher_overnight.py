"""Overnight Karcher-completion run for convergence-gap states.

Runs the VTD->block DualBalance pipeline (test_block_from_vtd logic)
for states that did not achieve Karcher compliance at VTD scale and
are not geometric failures. Block data for CT, TN, VA is fetched first
if not already present.

Results land in out/<state>_block_refined/map.geojson (overwriting any
existing partial run).

Usage:
    python scripts/run_karcher_overnight.py
    python scripts/run_karcher_overnight.py AZ GA     # selected states only
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# Convergence-gap states: non-Karcher at VTD scale, not geometric failures.
# Ordered roughly small->large to front-load fast wins.
GAP_STATES: dict[str, int] = {
    "MN": 8,
    "AZ": 9,
    "MA": 9,
    "GA": 14,
    "VA": 11,
    "NC": 14,
    "CT": 5,
    "TN": 9,
    "TX": 38,
}

NEEDS_BLOCK_PREP = {"CT", "TN", "VA"}  # no block geojson yet


def prep_blocks(state: str) -> bool:
    """Fetch block data for a state. Returns True on success."""
    out = DATA / f"{state.lower()}_block.geojson"
    if out.exists():
        print(f"  [{state}] block data already present ({out.stat().st_size/1e6:.1f} MB)")
        return True
    print(f"  [{state}] fetching block data via prep_state_units.py ...")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "prep_state_units.py"),
         "--state", state, "--geography", "block"],
        cwd=ROOT,
    )
    if result.returncode != 0:
        print(f"  [{state}] ERROR: data prep failed (exit {result.returncode})")
        return False
    print(f"  [{state}] block data ready")
    return True


def run_block_refinement(state: str, n: int) -> bool:
    """Run VTD->block refinement for one state. Returns True on success."""
    block_path = DATA / f"{state.lower()}_block.geojson"
    if not block_path.exists():
        print(f"  [{state}] SKIP: no block data at {block_path}")
        return False

    vtd_path = DATA / f"{state.lower()}_vtd.geojson"
    if not vtd_path.exists():
        print(f"  [{state}] SKIP: no VTD data at {vtd_path}")
        return False

    print(f"\n{'='*60}")
    print(f"  [{state}] N={n}  starting block refinement ...")
    print(f"{'='*60}")
    t0 = time.time()

    # Run the existing dev script with increased max_passes via env override.
    # We patch MAX_PASSES by wrapping the call in a small inline script so we
    # don't need to modify test_block_from_vtd.py itself.
    inline = f"""
import sys
sys.argv = ['test_block_from_vtd.py', '{state}', '{n}']
# Monkey-patch the module constant before importing main
import importlib.util, types
spec = importlib.util.spec_from_file_location(
    'test_block_from_vtd',
    r'{ROOT / "dev" / "test_block_from_vtd.py"}',
)
mod = importlib.util.module_from_spec(spec)
mod.KARCHER_TOL = 0.0005   # already the default; explicit for clarity
# Increase max_passes for larger states
mod_n = {n}
if mod_n >= 14:
    _max_passes = 500000
elif mod_n >= 9:
    _max_passes = 300000
else:
    _max_passes = 200000

# Override optimize_dbs to pass higher max_passes
import dualbalance.optimize as _opt
_orig_optimize = _opt.optimize_dbs
def _patched_optimize(plan, units, pop_dev_max_tolerance=None,
                      max_passes=100000, **kw):
    return _orig_optimize(plan, units,
                          pop_dev_max_tolerance=pop_dev_max_tolerance,
                          max_passes=_max_passes, **kw)
_opt.optimize_dbs = _patched_optimize

spec.loader.exec_module(mod)
raise SystemExit(mod.main('{state}', {n}))
"""
    result = subprocess.run(
        [sys.executable, "-c", inline],
        cwd=ROOT,
    )
    elapsed = time.time() - t0
    status = "OK" if result.returncode == 0 else f"FAILED (exit {result.returncode})"
    print(f"\n  [{state}] {status}  elapsed={elapsed/60:.1f}min")
    return result.returncode == 0


def main(argv: list[str]) -> None:
    states = [s.upper() for s in argv] if argv else list(GAP_STATES.keys())
    unknown = [s for s in states if s not in GAP_STATES]
    if unknown:
        print(f"ERROR: unknown states {unknown}; valid: {list(GAP_STATES)}")
        sys.exit(1)

    print(f"Karcher overnight run: {states}")
    print(f"Block data prep needed for: {[s for s in states if s in NEEDS_BLOCK_PREP]}\n")

    # Step 1: prep block data for states that need it
    for state in states:
        if state in NEEDS_BLOCK_PREP:
            if not prep_blocks(state):
                print(f"Skipping {state} due to prep failure")
                states = [s for s in states if s != state]

    # Step 2: run block refinement
    results: dict[str, bool] = {}
    t_total = time.time()
    for state in states:
        ok = run_block_refinement(state, GAP_STATES[state])
        results[state] = ok

    print(f"\n{'='*60}")
    print(f"SUMMARY  (total: {(time.time()-t_total)/60:.0f}min)")
    print(f"{'='*60}")
    for state, ok in results.items():
        print(f"  {state}: {'OK' if ok else 'FAILED'}")

    # Report achieved pop_dev_max from saved map files
    print()
    import geopandas as gpd
    import numpy as np
    for state, ok in results.items():
        if not ok:
            continue
        plan_path = ROOT / "out" / f"{state.lower()}_block_refined" / "map.geojson"
        if not plan_path.exists():
            print(f"  {state}: map.geojson not found")
            continue
        try:
            gdf = gpd.read_file(str(plan_path))
            pop = gdf.groupby("district_id")["population"].sum()
            n = GAP_STATES[state]
            p_star = pop.sum() / n
            dev_max = float((pop - p_star).abs().max() / p_star)
            karcher = dev_max <= 0.0005
            print(f"  {state}: pop_dev_max={dev_max*100:.4f}%  "
                  f"Karcher={'YES' if karcher else 'NO'}")
        except Exception as e:
            print(f"  {state}: could not score — {e}")


if __name__ == "__main__":
    main(sys.argv[1:])
