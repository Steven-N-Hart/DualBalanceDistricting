"""Score multiple plans for a state side by side.

Loads the units geojson once (with the full set of diagnostic columns
that scoring expects), then scores four plans against the same harness:

- **PRISM**       (out/<state>_yaml/map.geojson)
- **Cascade**     (out/<state>_cascade/map.geojson)
- **BDistricting** (data/<state>_bdistricting.geojson)
- **Enacted**     (data/<state>_enacted.geojson)

Missing files are silently skipped. Prints a side-by-side table and
writes per-plan metrics plus comparison.json.

Usage:
  python scripts/compare_state.py --state IA
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dualbalance.io import load_plan, load_units, write_metrics
from dualbalance.scoring import score_plan

REPO_ROOT = Path(__file__).resolve().parent.parent

EXTRA_COLUMNS = [
    "vap_total",
    "vap_nhwhite",
    "vap_black",
    "vap_hispanic",
    "vap_aian",
    "vap_asian",
    "votes_R",
    "votes_D",
]

HEADLINE_KEYS = [
    "dualbalance_score",
    "pop_deviation_mean",
    "pop_deviation_max",
    "area_deviation_mean",
    "area_deviation_max",
    "polsby_popper_mean",
    "polsby_popper_min",
    "reock_mean",
    "counties_split",
    "counties_total",
    "seats_R",
    "seats_D",
    "statewide_share_R",
    "efficiency_gap",
    "mean_median_R",
    "minority_majority_districts",
]


PLAN_SOURCES = [
    ("prism", "out/{state}_yaml/map.geojson"),
    ("cascade", "out/{state}_cascade/map.geojson"),
    ("bdistricting", "data/{state}_bdistricting.geojson"),
    ("enacted", "data/{state}_enacted.geojson"),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True, help="Two-letter postal code (e.g. IA).")
    parser.add_argument(
        "--units",
        type=Path,
        help="Override path to the units geojson (default: data/<state-lower>_vtd.geojson).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="Optional directory to write per-plan metrics + comparison.json "
        "(default: out/<state-lower>_compare).",
    )
    args = parser.parse_args(argv)

    state = args.state.lower()
    units_path = args.units or (REPO_ROOT / "data" / f"{state}_vtd.geojson")
    out_dir = args.out_dir or (REPO_ROOT / "out" / f"{state}_compare")

    print(f"loading units: {units_path}")
    units = load_units(
        units_path,
        id_column="GEOID20",
        pop_column="population",
        county_column="county",
        extra_columns=EXTRA_COLUMNS,
    )

    results: dict[str, dict] = {}
    for name, tmpl in PLAN_SOURCES:
        path = REPO_ROOT / tmpl.format(state=state)
        if not path.is_file():
            print(f"  skipping {name}: {path} not found")
            continue
        print(f"scoring {name}: {path}")
        plan = load_plan(path, geography="vtd")
        results[name] = score_plan(plan, units)

    if not results:
        print("no plans scored")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, metrics in results.items():
        write_metrics(metrics, out_dir / f"{name}_metrics.json")
    comparison = {
        "state": state.upper(),
        "n_units": len(units),
        **{name: {k: m.get(k) for k in HEADLINE_KEYS} for name, m in results.items()},
    }
    write_metrics(comparison, out_dir / "comparison.json")

    print()
    print(f"=== {state.upper()} comparison ===")
    plans_in_order = [n for n, _ in PLAN_SOURCES if n in results]
    header = f"{'Metric':<32}" + "".join(f"{n.upper():>14}" for n in plans_in_order)
    print(header)
    print("-" * len(header))
    for k in HEADLINE_KEYS:
        row_vals = [results[n].get(k) for n in plans_in_order]
        if all(v is None for v in row_vals):
            continue
        row = f"{k:<32}" + "".join(f"{_fmt(v, k):>14}" for v in row_vals)
        print(row)
    print(f"\nWrote {out_dir / 'comparison.json'}")
    return 0


def _fmt(value: object, key: str) -> str:
    if value is None:
        return "-"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if key.endswith(("_mean", "_max", "_min", "_share_R", "_R", "_gap", "_score")):
            return f"{value:.4f}"
        return f"{value:.6f}"
    return str(value)


if __name__ == "__main__":
    sys.exit(main())
