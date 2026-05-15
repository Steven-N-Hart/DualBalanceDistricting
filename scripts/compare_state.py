"""Score PRISM and the enacted 119th-Congress plan for a state, side by side.

Loads the units geojson once (with the full set of diagnostic columns
that scoring expects), scores both ``out/<state>_yaml/map.geojson``
(PRISM output) and ``data/<state>_enacted.geojson`` (TIGER cd119
spatial join from prep_state_units.py), and prints a comparison table.

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True, help="Two-letter postal code (e.g. IA).")
    parser.add_argument(
        "--prism-plan",
        type=Path,
        help="Override path to the PRISM plan geojson "
        "(default: out/<state-lower>_yaml/map.geojson).",
    )
    parser.add_argument(
        "--enacted-plan",
        type=Path,
        help="Override path to the enacted plan geojson "
        "(default: data/<state-lower>_enacted.geojson).",
    )
    parser.add_argument(
        "--units",
        type=Path,
        help="Override path to the units geojson (default: data/<state-lower>_vtd.geojson).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="Optional directory to write prism_metrics.json + enacted_metrics.json "
        "+ comparison.json (default: out/<state-lower>_compare).",
    )
    args = parser.parse_args(argv)

    state = args.state.lower()
    units_path = args.units or (REPO_ROOT / "data" / f"{state}_vtd.geojson")
    prism_path = args.prism_plan or (REPO_ROOT / "out" / f"{state}_yaml" / "map.geojson")
    enacted_path = args.enacted_plan or (REPO_ROOT / "data" / f"{state}_enacted.geojson")
    out_dir = args.out_dir or (REPO_ROOT / "out" / f"{state}_compare")

    print(f"loading units: {units_path}")
    units = load_units(
        units_path,
        id_column="GEOID20",
        pop_column="population",
        county_column="county",
        extra_columns=EXTRA_COLUMNS,
    )

    print(f"scoring PRISM plan: {prism_path}")
    prism_plan = load_plan(prism_path, geography="vtd")
    prism = score_plan(prism_plan, units)

    print(f"scoring enacted plan: {enacted_path}")
    enacted_plan = load_plan(enacted_path, geography="vtd")
    enacted = score_plan(enacted_plan, units)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_metrics(prism, out_dir / "prism_metrics.json")
    write_metrics(enacted, out_dir / "enacted_metrics.json")

    comparison = {
        "state": state.upper(),
        "n_units": len(units),
        "prism": {k: prism.get(k) for k in HEADLINE_KEYS},
        "enacted": {k: enacted.get(k) for k in HEADLINE_KEYS},
    }
    write_metrics(comparison, out_dir / "comparison.json")

    print()
    print(f"=== {state.upper()} comparison ===")
    print(f"{'Metric':<32} {'PRISM':>12} {'Enacted':>12}")
    print("-" * 60)
    for k in HEADLINE_KEYS:
        p = prism.get(k)
        e = enacted.get(k)
        if p is None and e is None:
            continue
        p_str = _fmt(p, k)
        e_str = _fmt(e, k)
        print(f"{k:<32} {p_str:>12} {e_str:>12}")
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
