"""Command-line interface for DualBalance.

Subcommands:

- ``generate`` — produce a DualBalance plan for a state.
- ``apportion`` — apportion seats across states via Method of Equal Proportions.
- ``score`` — score an existing plan (DualBalance or other) against the same metrics.
- ``compare`` — placeholder, not in PoC scope.

Every subcommand accepts ``--config <path.yaml>`` for YAML-based defaults;
explicit CLI flags override matching YAML keys (see
:mod:`dualbalance.config`).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from dualbalance.apportionment import apportion_seats
from dualbalance.cascade import generate_cascade_plan
from dualbalance.config import load_config, merge_config
from dualbalance.districting import generate_plan
from dualbalance.geography import Geography
from dualbalance.io import (
    load_plan,
    load_state_populations,
    load_units,
    write_metrics,
    write_plan,
)
from dualbalance.scoring import score_plan
from dualbalance.tighten import tighten_population


def _apply_config(args: argparse.Namespace, defaults: dict[str, Any]) -> argparse.Namespace:
    if getattr(args, "config", None):
        yaml_dict = load_config(args.config)
        args = merge_config(yaml_dict, args, defaults)
    return args


def _require(args: argparse.Namespace, *names: str) -> None:
    missing = [n for n in names if getattr(args, n, None) in (None, "")]
    if missing:
        flags = ", ".join(f"--{n.replace('_', '-')}" for n in missing)
        raise SystemExit(f"missing required argument(s): {flags}")


def _cmd_generate(args: argparse.Namespace, defaults: dict[str, Any]) -> int:
    args = _apply_config(args, defaults)
    _require(args, "units", "districts", "out")

    geography = Geography.from_cli_name(args.geography)
    id_column = args.id_column or geography.default_id_column
    pop_column = args.pop_column or "population"

    units = load_units(
        args.units,
        id_column=id_column,
        pop_column=pop_column,
        county_column=args.county_column,
        extra_columns=args.extra_columns,
    )
    plan = generate_plan(units, args.districts, geography=geography.cli_name)
    if args.tighten_pop:
        plan = tighten_population(plan, units, pop_tolerance=args.pop_tolerance)
    metrics = score_plan(plan, units)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_plan(plan, units, out_dir / "map.geojson")
    write_metrics(metrics, out_dir / "metrics.json")
    print(
        f"generated {plan.n_districts} districts over {len(units)} "
        f"{geography.cli_name} unit(s); DualBalance Score = "
        f"{metrics['dualbalance_score']:.4f}; wrote map.geojson + "
        f"metrics.json to {out_dir}"
    )
    return 0


def _cmd_generate_cascade(args: argparse.Namespace, defaults: dict[str, Any]) -> int:
    args = _apply_config(args, defaults)
    _require(args, "units", "districts", "out")

    geography = Geography.from_cli_name(args.geography)
    id_column = args.id_column or geography.default_id_column
    pop_column = args.pop_column or "population"

    units = load_units(
        args.units,
        id_column=id_column,
        pop_column=pop_column,
        county_column=args.county_column,
        extra_columns=args.extra_columns,
    )
    if "county" not in units.columns:
        raise SystemExit(
            "generate-cascade requires a county column on the units. "
            "Pass --county-column COL or set county_column in the YAML config."
        )
    plan = generate_cascade_plan(units, args.districts, geography=geography.cli_name)
    metrics = score_plan(plan, units)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_plan(plan, units, out_dir / "map.geojson")
    write_metrics(metrics, out_dir / "metrics.json")
    print(
        f"cascade: {plan.n_districts} districts over {len(units)} "
        f"{geography.cli_name} unit(s); DualBalance Score = "
        f"{metrics['dualbalance_score']:.4f}; wrote map.geojson + "
        f"metrics.json to {out_dir}"
    )
    return 0


def _cmd_apportion(args: argparse.Namespace, defaults: dict[str, Any]) -> int:
    args = _apply_config(args, defaults)
    _require(args, "populations", "seats")

    pops = load_state_populations(args.populations)
    seats = apportion_seats(pops, args.seats)

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(seats, indent=2, sort_keys=True), encoding="utf-8")
        print(f"wrote {len(seats)} state allocations totaling {sum(seats.values())} seats to {out}")
    else:
        for state in sorted(seats):
            print(f"{state}\t{seats[state]}")
    return 0


def _cmd_score(args: argparse.Namespace, defaults: dict[str, Any]) -> int:
    args = _apply_config(args, defaults)
    _require(args, "plan", "units")

    geography = Geography.from_cli_name(args.geography) if args.geography else None
    id_column = args.id_column or (
        geography.default_id_column if geography is not None else "GEOID"
    )
    pop_column = args.pop_column or "population"

    units = load_units(
        args.units,
        id_column=id_column,
        pop_column=pop_column,
        county_column=args.county_column,
        extra_columns=args.extra_columns,
    )
    plan = load_plan(
        args.plan,
        geography=geography.cli_name if geography is not None else "unknown",
    )
    metrics = score_plan(plan, units)
    if args.out:
        write_metrics(metrics, args.out)
        print(
            f"scored {plan.n_districts} districts over {len(units)} unit(s); "
            f"DualBalance Score = {metrics['dualbalance_score']:.4f}; wrote {args.out}"
        )
    else:
        print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


def _cmd_compare(args: argparse.Namespace, defaults: dict[str, Any]) -> int:
    raise SystemExit("`dualbalance compare` is not in the PoC scope yet")


_DISPATCH: dict[str, Callable[[argparse.Namespace, dict[str, Any]], int]] = {
    "generate": _cmd_generate,
    "generate-cascade": _cmd_generate_cascade,
    "apportion": _cmd_apportion,
    "score": _cmd_score,
    "compare": _cmd_compare,
}


def _add_config_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to a YAML config file with subcommand defaults.",
    )


def _defaults_for(parser: argparse.ArgumentParser) -> dict[str, Any]:
    """Map ``{dest: default}`` for every flag of a (sub)parser, excluding help."""
    out: dict[str, Any] = {}
    for action in parser._actions:
        if action.dest in ("help", argparse.SUPPRESS):
            continue
        out[action.dest] = action.default
    return out


def build_parser() -> tuple[argparse.ArgumentParser, dict[str, dict[str, Any]]]:
    """Build the top-level parser. Returns (parser, per-subcommand-defaults)."""
    parser = argparse.ArgumentParser(
        prog="dualbalance",
        description="Deterministic district-map generation and scoring.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    geography_choices = [g.cli_name for g in Geography]

    generate = subparsers.add_parser("generate", help="Generate a DualBalance plan for a state.")
    _add_config_flag(generate)
    generate.add_argument("--districts", type=int, help="Number of districts N.")
    generate.add_argument(
        "--units",
        type=Path,
        help="Path to atomic-unit data (GeoJSON / Shapefile / GeoPackage / ...).",
    )
    generate.add_argument(
        "--geography",
        default="vtd",
        choices=geography_choices,
        help="Base unit type (default: vtd).",
    )
    generate.add_argument(
        "--id-column",
        dest="id_column",
        help="Column to read as the unit ID (default: per --geography).",
    )
    generate.add_argument(
        "--pop-column",
        dest="pop_column",
        help="Column with population (default: population).",
    )
    generate.add_argument(
        "--county-column",
        dest="county_column",
        help="Optional column with county FIPS / name. Preserved through "
        "load_units and used by the scoring harness to report county splits. "
        "The core generator never reads it.",
    )
    generate.add_argument(
        "--extra-columns",
        dest="extra_columns",
        default=None,
        # YAML-only: argparse can't ergonomically express a dict. Set via
        # --config <yaml> with an ``extra_columns:`` mapping or list.
        help=argparse.SUPPRESS,
    )
    generate.add_argument("--out", type=Path, help="Output directory.")
    generate.add_argument(
        "--tighten-pop",
        dest="tighten_pop",
        action="store_true",
        help="Opt-in post-assignment pass: greedy boundary-unit swaps "
        "to close the per-district pop_deviation gap to --pop-tolerance. "
        "Off by default; turning it on weakens the pure-radial guarantee.",
    )
    generate.add_argument(
        "--pop-tolerance",
        dest="pop_tolerance",
        type=float,
        default=0.005,
        help="Target |pop - P*|/P* for --tighten-pop (default 0.005 = 0.5%%, "
        "the typical Reynolds v. Sims threshold).",
    )

    cascade = subparsers.add_parser(
        "generate-cascade",
        help="Iowa-LSA-flavored baseline: county-aggregated, county-integrity-first.",
    )
    _add_config_flag(cascade)
    cascade.add_argument("--districts", type=int, help="Number of districts N.")
    cascade.add_argument("--units", type=Path, help="Path to atomic-unit data.")
    cascade.add_argument(
        "--geography",
        default="vtd",
        choices=geography_choices,
        help="Base unit type (default: vtd).",
    )
    cascade.add_argument("--id-column", dest="id_column")
    cascade.add_argument("--pop-column", dest="pop_column")
    cascade.add_argument(
        "--county-column",
        dest="county_column",
        help="Column with county FIPS / name. Required for cascade.",
    )
    cascade.add_argument(
        "--extra-columns",
        dest="extra_columns",
        default=None,
        help=argparse.SUPPRESS,
    )
    cascade.add_argument("--out", type=Path, help="Output directory.")

    apportion = subparsers.add_parser(
        "apportion",
        help="Apportion seats across states using the Method of Equal Proportions.",
    )
    _add_config_flag(apportion)
    apportion.add_argument(
        "--populations",
        type=Path,
        help="Path to a state-populations file (CSV or JSON).",
    )
    apportion.add_argument("--seats", type=int, help="Total seats to allocate.")
    apportion.add_argument(
        "--out",
        type=Path,
        help="Optional output JSON path; prints to stdout otherwise.",
    )

    score = subparsers.add_parser("score", help="Score an existing district plan.")
    _add_config_flag(score)
    score.add_argument("--plan", type=Path, help="Path to a plan GeoJSON.")
    score.add_argument(
        "--units",
        type=Path,
        help="Path to the same unit data the plan was generated against.",
    )
    score.add_argument(
        "--geography",
        default=None,
        choices=geography_choices,
        help="Base unit type (metadata only for scoring).",
    )
    score.add_argument("--id-column", dest="id_column")
    score.add_argument("--pop-column", dest="pop_column")
    score.add_argument(
        "--out",
        type=Path,
        help="Optional path to write metrics JSON; prints to stdout if omitted.",
    )
    score.add_argument(
        "--county-column",
        dest="county_column",
        help="Optional column with county FIPS / name; enables county-split "
        "reporting in the metrics.",
    )
    score.add_argument(
        "--extra-columns",
        dest="extra_columns",
        default=None,
        help=argparse.SUPPRESS,
    )

    compare = subparsers.add_parser(
        "compare",
        help="Compare plans against the DualBalance baseline (not in PoC).",
    )
    _add_config_flag(compare)
    compare.add_argument("--state")
    compare.add_argument("--plans", type=Path)

    defaults: dict[str, dict[str, Any]] = {
        "generate": _defaults_for(generate),
        "generate-cascade": _defaults_for(cascade),
        "apportion": _defaults_for(apportion),
        "score": _defaults_for(score),
        "compare": _defaults_for(compare),
    }
    return parser, defaults


def main(argv: list[str] | None = None) -> int:
    parser, defaults = build_parser()
    args = parser.parse_args(argv)
    return _DISPATCH[args.command](args, defaults[args.command])


if __name__ == "__main__":
    sys.exit(main())
