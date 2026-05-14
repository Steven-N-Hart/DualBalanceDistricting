from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pytest

from dualbalance.config import load_config, merge_config


def test_load_config_reads_yaml(tmp_path: Path) -> None:
    fp = tmp_path / "c.yaml"
    fp.write_text("state: MN\ndistricts: 8\n", encoding="utf-8")
    assert load_config(fp) == {"state": "MN", "districts": 8}


def test_load_config_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nope.yaml")


def test_load_config_empty_returns_empty_dict(tmp_path: Path) -> None:
    fp = tmp_path / "c.yaml"
    fp.write_text("", encoding="utf-8")
    assert load_config(fp) == {}


def test_load_config_non_mapping_raises(tmp_path: Path) -> None:
    fp = tmp_path / "c.yaml"
    fp.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_config(fp)


def test_merge_yaml_fills_in_default_values() -> None:
    args = Namespace(state=None, districts=8)
    defaults = {"state": None, "districts": 8}
    merged = merge_config({"state": "MN"}, args, defaults)
    assert merged.state == "MN"
    assert merged.districts == 8


def test_merge_cli_overrides_yaml() -> None:
    args = Namespace(state="WI", districts=8)
    defaults = {"state": None, "districts": 8}
    merged = merge_config({"state": "MN"}, args, defaults)
    assert merged.state == "WI"


def test_merge_unknown_yaml_key_raises() -> None:
    args = Namespace(state=None)
    defaults = {"state": None}
    with pytest.raises(ValueError, match="unknown YAML key"):
        merge_config({"bogus": 1}, args, defaults)


def test_merge_does_not_mutate_args() -> None:
    args = Namespace(state=None, districts=8)
    defaults = {"state": None, "districts": 8}
    merged = merge_config({"state": "MN"}, args, defaults)
    assert args.state is None
    assert merged.state == "MN"


def test_merge_empty_yaml_is_identity() -> None:
    args = Namespace(state="MN", districts=8)
    defaults = {"state": None, "districts": 8}
    merged = merge_config({}, args, defaults)
    assert vars(merged) == vars(args)
