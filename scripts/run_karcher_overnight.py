"""Overnight Karcher-completion run for convergence-gap states.

Fetches block data for states that need it, then calls
dev/test_block_from_vtd.py (which uses KARCHER_TOL=0.0005 and
max_passes=1_000_000) for each state.

Results land in out/<state>_block_refined/map.geojson.

Usage:
    python scripts/run_karcher_overnight.py              # all gap states
    python scripts/run_karcher_overnight.py AZ GA MN     # selected only
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DEV  = ROOT / "dev" / "test_block_from_vtd.py"

GAP_STATES: dict[str, int] = {
    "MN": 8,
    "AZ": 9,
    "MA": 9,
    "CT": 5,
    "VA": 11,
    "GA": 14,
    "NC": 14,
    "TN": 9,
    "TX": 38,
}

NEEDS_BLOCK_PREP = {"CT", "TN", "VA"}


def prep_blocks(state: str) -> bool:
    out = DATA / f"{state.lower()}_block.geojson"
    if out.exists():
        print(f"[{state}] block data present ({out.stat().st_size/1e6:.0f} MB)")
        return True
    print(f"[{state}] fetching block data ...")
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "prep_state_units.py"),
         "--state", state, "--geography", "block"],
        cwd=ROOT,
    )
    ok = r.returncode == 0
    print(f"[{state}] prep {'OK' if ok else 'FAILED'}")
    return ok


def run_state(state: str, n: int) -> bool:
    block_path = DATA / f"{state.lower()}_block.geojson"
    vtd_path   = DATA / f"{state.lower()}_vtd.geojson"
    if not block_path.exists():
        print(f"[{state}] SKIP: missing {block_path.name}")
        return False
    if not vtd_path.exists():
        print(f"[{state}] SKIP: missing {vtd_path.name}")
        return False

    print(f"\n{'='*60}\n[{state}] N={n} starting\n{'='*60}")
    t0 = time.time()
    r = subprocess.run([sys.executable, str(DEV), state, str(n)], cwd=ROOT)
    elapsed = (time.time() - t0) / 60
    ok = r.returncode == 0
    print(f"[{state}] {'OK' if ok else 'FAILED'}  {elapsed:.1f}min")
    return ok


def score(state: str, n: int) -> str:
    p = ROOT / "out" / f"{state.lower()}_block_refined" / "map.geojson"
    if not p.exists():
        return "no output"
    try:
        gdf = gpd.read_file(str(p))
        pop = gdf.groupby("district_id")["population"].sum()
        p_star = pop.sum() / n
        dev = float((pop - p_star).abs().max() / p_star)
        return f"pop_dev_max={dev*100:.4f}%  Karcher={'YES' if dev<=0.0005 else 'NO'}"
    except Exception as e:
        return f"score error: {e}"


def main(argv: list[str]) -> None:
    states = [s.upper() for s in argv] if argv else list(GAP_STATES)
    bad = [s for s in states if s not in GAP_STATES]
    if bad:
        sys.exit(f"Unknown states: {bad}")

    print(f"Overnight run: {states}\n")

    for s in states:
        if s in NEEDS_BLOCK_PREP:
            if not prep_blocks(s):
                states = [x for x in states if x != s]

    results: dict[str, bool] = {}
    t0 = time.time()
    for s in states:
        results[s] = run_state(s, GAP_STATES[s])

    print(f"\n{'='*60}\nSUMMARY  ({(time.time()-t0)/60:.0f}min total)\n{'='*60}")
    for s, ok in results.items():
        print(f"  {s}: {'OK' if ok else 'FAILED'}  {score(s, GAP_STATES[s])}")


if __name__ == "__main__":
    main(sys.argv[1:])
