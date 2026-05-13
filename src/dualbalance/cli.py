"""Command-line interface for DualBalance.

Subcommands map to the four top-level operations described in README.md:
generate, apportion, score, compare.
"""

from __future__ import annotations

import argparse
import sys


def _cmd_generate(args: argparse.Namespace) -> int:
    raise NotImplementedError("`dualbalance generate` is not yet implemented")


def _cmd_apportion(args: argparse.Namespace) -> int:
    raise NotImplementedError("`dualbalance apportion` is not yet implemented")


def _cmd_score(args: argparse.Namespace) -> int:
    raise NotImplementedError("`dualbalance score` is not yet implemented")


def _cmd_compare(args: argparse.Namespace) -> int:
    raise NotImplementedError("`dualbalance compare` is not yet implemented")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dualbalance",
        description="Deterministic district-map generation and scoring.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser(
        "generate", help="Generate a district plan for a state."
    )
    generate.add_argument("--state", required=True, help="State identifier (e.g. MN).")
    generate.add_argument("--districts", type=int, required=True, help="Number of districts N.")
    generate.add_argument("--blocks", required=True, help="Path to census block data.")
    generate.add_argument("--out", required=True, help="Output directory.")
    generate.set_defaults(func=_cmd_generate)

    apportion = subparsers.add_parser(
        "apportion",
        help="Apportion seats across states using the Method of Equal Proportions.",
    )
    apportion.add_argument(
        "--populations", required=True, help="Path to state populations file."
    )
    apportion.add_argument("--seats", type=int, required=True, help="Total seats to allocate.")
    apportion.set_defaults(func=_cmd_apportion)

    score = subparsers.add_parser("score", help="Score an existing district plan.")
    score.add_argument("--plan", required=True, help="Path to plan (GeoJSON).")
    score.add_argument("--blocks", required=True, help="Path to census block data.")
    score.set_defaults(func=_cmd_score)

    compare = subparsers.add_parser(
        "compare", help="Compare multiple plans against the DualBalance baseline."
    )
    compare.add_argument("--state", required=True)
    compare.add_argument("--plans", required=True, help="Directory containing plans to compare.")
    compare.set_defaults(func=_cmd_compare)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
