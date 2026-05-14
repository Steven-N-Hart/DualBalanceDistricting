"""Command-line interface for DualBalance.

Subcommands map to the four top-level operations described in README.md:
``generate``, ``apportion``, ``score``, ``compare``. Every subcommand accepts
``--config <path.yaml>`` for YAML-based defaults; explicit CLI flags override
matching YAML keys (see :mod:`dualbalance.config`).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from dualbalance.apportionment import apportion_seats
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
from dualbalance.seeds import SEED_METHODS
from dualbalance.trades import tighten_to_reynolds


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

    units = load_units(args.units, id_column=id_column, pop_column=pop_column)
    plan = generate_plan(
        units,
        args.districts,
        alpha=args.alpha,
        beta=args.beta,
        max_iter=args.max_iter,
        geography=geography.cli_name,
        repair=not args.no_repair,
        seed_method=args.seed_method,
        capacity_slack=args.capacity_slack,
    )
    if args.reynolds_tighten:
        plan = tighten_to_reynolds(
            plan,
            units,
            pop_tolerance=args.pop_tolerance,
            reduce_area=not args.no_area_reduction,
            score_variant=args.score_variant,
        )
    metrics = score_plan(plan, units)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_plan(plan, units, out_dir / "map.geojson")
    write_metrics(metrics, out_dir / "metrics.json")
    print(
        f"generated {plan.n_districts} districts over {len(units)} {geography.cli_name} "
        f"unit(s); DualBalance Score = {metrics['dualbalance_score']:.4f}; "
        f"wrote map.geojson + metrics.json to {out_dir}"
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

    units = load_units(args.units, id_column=id_column, pop_column=pop_column)
    plan = load_plan(
        args.plan,
        geography=geography.cli_name if geography is not None else "unknown",
    )
    metrics = score_plan(plan, units)
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


def _cmd_compare(args: argparse.Namespace, defaults: dict[str, Any]) -> int:
    raise SystemExit("`dualbalance compare` is not in the PoC scope yet")


_DISPATCH: dict[str, Callable[[argparse.Namespace, dict[str, Any]], int]] = {
    "generate": _cmd_generate,
    "apportion": _cmd_apportion,
    "score": _cmd_score,
    "compare": _cmd_compare,
}


def _add_config_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config", type=Path, help="Path to a YAML config file with subcommand defaults."
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

    generate = subparsers.add_parser("generate", help="Generate a district plan for a state.")
    _add_config_flag(generate)
    generate.add_argument("--state", help="State identifier (metadata only, e.g. MN).")
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
    generate.add_argument("--out", type=Path, help="Output directory.")
    generate.add_argument(
        "--alpha",
        type=float,
        default=1.0,
        help="Distance weight (default: 1.0).",
    )
    generate.add_argument(
        "--beta",
        type=float,
        default=1.0,
        help="Population/area penalty weight (default: 1.0).",
    )
    generate.add_argument(
        "--max-iter",
        dest="max_iter",
        type=int,
        default=100,
        help="Max Lloyd iterations (default: 100).",
    )
    generate.add_argument(
        "--no-repair",
        dest="no_repair",
        action="store_true",
        help="Skip the contiguity repair pass.",
    )
    generate.add_argument(
        "--seed-method",
        dest="seed_method",
        default="farthest-point",
        choices=list(SEED_METHODS),
        help="Seed placement strategy (default: farthest-point). "
        "population-slice puts more seeds in dense regions.",
    )
    generate.add_argument(
        "--capacity-slack",
        dest="capacity_slack",
        type=float,
        default=0.0,
        help="Extra capacity per district as fraction of P* "
        "(default 0.0; 0.005 absorbs integer-rounding edge cases).",
    )
    generate.add_argument(
        "--reynolds-tighten",
        dest="reynolds_tighten",
        action="store_true",
        help="Run the post-iteration trade pass (Reynolds-compliant pop "
        "tightening + pop-neutral area reduction).",
    )
    generate.add_argument(
        "--pop-tolerance",
        dest="pop_tolerance",
        type=float,
        default=0.005,
        help="Target |pop - P*| / P* tolerance for --reynolds-tighten (default 0.005 = 0.5%%).",
    )
    generate.add_argument(
        "--no-area-reduction",
        dest="no_area_reduction",
        action="store_true",
        help="With --reynolds-tighten, skip Phase B (pop-neutral area swaps).",
    )
    generate.add_argument(
        "--score-variant",
        dest="score_variant",
        choices=["weighted", "classic"],
        default="weighted",
        help="Reynolds-tighten Phase A objective (default: weighted). "
        "'classic' optimizes pop_dev_mean + area_dev_mean "
        "(1/(1+sum) score form); may not always meet --pop-tolerance.",
    )

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
    apportion.add_argument(
        "--seats",
        type=int,
        help="Total seats to allocate.",
    )
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

    compare = subparsers.add_parser(
        "compare",
        help="Compare plans against the DualBalance baseline (not in PoC).",
    )
    _add_config_flag(compare)
    compare.add_argument("--state")
    compare.add_argument("--plans", type=Path)

    defaults: dict[str, dict[str, Any]] = {
        "generate": _defaults_for(generate),
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
