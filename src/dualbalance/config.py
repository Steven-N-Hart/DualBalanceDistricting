"""YAML configuration support for the CLI.

Subcommands accept ``--config <path.yaml>`` to read default values from a flat
YAML mapping. Precedence: explicitly-set CLI flag > YAML value > argparse
default. A flag is considered "explicitly set" when its value differs from the
parser default; setting a CLI flag to its default value is therefore treated
as unset (acceptable trade-off for v0).

Unknown YAML keys (those that don't match any flag's ``dest``) raise.
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    """Read a flat YAML file into a dict.

    An empty YAML file yields ``{}``. Non-mapping documents raise ``ValueError``.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"config file not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(
            f"config file {p!s} must contain a YAML mapping, got {type(data).__name__}"
        )
    return data


def merge_config(
    yaml_dict: dict[str, Any],
    args: Namespace,
    defaults: dict[str, Any],
) -> Namespace:
    """Layer YAML values onto a parsed argparse Namespace.

    Args:
        yaml_dict: parsed contents of the user's YAML config (may be empty).
        args: the Namespace returned by ``parser.parse_args``.
        defaults: ``{dest: default}`` for every flag of the active subcommand.
            The CLI builds this from each subparser's actions.

    Returns:
        A new Namespace with YAML values substituted wherever the namespace
        attribute equals its argparse default. Does not mutate ``args``.

    Raises:
        ValueError: if ``yaml_dict`` contains keys not in ``defaults``.
    """
    unknown = set(yaml_dict) - set(defaults)
    if unknown:
        raise ValueError(f"unknown YAML key(s): {sorted(unknown)}")

    out = Namespace(**vars(args))
    for key, value in yaml_dict.items():
        if getattr(out, key) == defaults[key]:
            setattr(out, key, value)
    return out
