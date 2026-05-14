from __future__ import annotations

import json
from pathlib import Path

import pytest

from dualbalance.cli import build_parser, main


@pytest.mark.parametrize("cmd", ["generate", "apportion", "score", "compare"])
def test_subcommand_help_parses(cmd: str) -> None:
    parser, _ = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args([cmd, "--help"])
    assert exc_info.value.code == 0


@pytest.mark.parametrize("geo", ["vtd", "block", "block_group"])
def test_generate_accepts_geography_values(geo: str) -> None:
    parser, _ = build_parser()
    args = parser.parse_args(
        [
            "generate",
            "--geography",
            geo,
            "--districts",
            "8",
            "--units",
            "u.geojson",
            "--out",
            "o/",
        ]
    )
    assert args.geography == geo


def test_generate_rejects_unknown_geography() -> None:
    parser, _ = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["generate", "--geography", "precinct"])


def test_generate_has_no_algorithm_knobs() -> None:
    # The CLI exposes only data-plumbing flags; the algorithm itself takes
    # no tuning knobs (no --max-iter, --seed-method, --alpha, --reynolds-*,
    # --enforce-area, --score-variant, etc).
    _, defaults = build_parser()
    forbidden = {
        "alpha",
        "beta",
        "max_iter",
        "seed_method",
        "capacity_slack",
        "reynolds_tighten",
        "pop_tolerance",
        "no_area_reduction",
        "score_variant",
        "enforce_area",
        "area_tolerance",
        "no_repair",
    }
    assert defaults["generate"].keys().isdisjoint(forbidden)


def test_generate_defaults_dict_has_data_plumbing_keys() -> None:
    _, defaults = build_parser()
    for k in ("districts", "config", "geography", "units", "out", "id_column", "pop_column"):
        assert k in defaults["generate"]
    assert defaults["generate"]["geography"] == "vtd"


def test_apportion_csv_end_to_end(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    csv_path = tmp_path / "pops.csv"
    csv_path.write_text("state,population\nA,1000\nB,500\nC,200\n", encoding="utf-8")
    out_path = tmp_path / "seats.json"
    rc = main(["apportion", "--populations", str(csv_path), "--seats", "7", "--out", str(out_path)])
    assert rc == 0
    assert json.loads(out_path.read_text()) == {"A": 4, "B": 2, "C": 1}


def test_apportion_json_input(tmp_path: Path) -> None:
    src = tmp_path / "pops.json"
    src.write_text(json.dumps({"A": 1000, "B": 500, "C": 200}), encoding="utf-8")
    out = tmp_path / "seats.json"
    rc = main(["apportion", "--populations", str(src), "--seats", "7", "--out", str(out)])
    assert rc == 0
    assert json.loads(out.read_text()) == {"A": 4, "B": 2, "C": 1}


def test_apportion_with_config_file(tmp_path: Path) -> None:
    src = tmp_path / "pops.csv"
    src.write_text("state,population\nA,100\nB,100\n", encoding="utf-8")
    cfg = tmp_path / "c.yaml"
    cfg.write_text(f"populations: {src}\nseats: 4\n", encoding="utf-8")
    out = tmp_path / "seats.json"
    rc = main(["apportion", "--config", str(cfg), "--out", str(out)])
    assert rc == 0
    assert json.loads(out.read_text()) == {"A": 2, "B": 2}


def test_apportion_cli_overrides_yaml(tmp_path: Path) -> None:
    src = tmp_path / "pops.csv"
    src.write_text("state,population\nA,100\nB,100\nC,100\n", encoding="utf-8")
    cfg = tmp_path / "c.yaml"
    cfg.write_text(f"populations: {src}\nseats: 3\n", encoding="utf-8")
    out = tmp_path / "seats.json"
    rc = main(["apportion", "--config", str(cfg), "--seats", "5", "--out", str(out)])
    assert rc == 0
    assert json.loads(out.read_text()) == {"A": 2, "B": 2, "C": 1}


def test_apportion_missing_required_arg() -> None:
    with pytest.raises(SystemExit, match="--populations"):
        main(["apportion", "--seats", "10"])


def test_compare_stub_explains_scope() -> None:
    with pytest.raises(SystemExit, match="not in the PoC scope"):
        main(["compare", "--state", "MN", "--plans", "."])


def test_generate_end_to_end_on_synthetic_grid(tmp_path: Path, synthetic_grid_4x4) -> None:
    units_path = tmp_path / "units.geojson"
    out_dir = tmp_path / "out"
    src = synthetic_grid_4x4.rename(columns={"unit_id": "GEOID20"})[
        ["GEOID20", "population", "geometry"]
    ]
    src.to_file(units_path, driver="GeoJSON")

    rc = main(
        [
            "generate",
            "--districts",
            "4",
            "--units",
            str(units_path),
            "--geography",
            "vtd",
            "--out",
            str(out_dir),
        ]
    )
    assert rc == 0
    assert (out_dir / "map.geojson").is_file()
    assert (out_dir / "metrics.json").is_file()
    metrics = json.loads((out_dir / "metrics.json").read_text())
    assert metrics["dualbalance_score"] > 0.85
    assert metrics["geography"] == "vtd"


def test_generate_determinism_via_cli(tmp_path: Path, synthetic_grid_4x4) -> None:
    units_path = tmp_path / "units.geojson"
    src = synthetic_grid_4x4.rename(columns={"unit_id": "GEOID20"})[
        ["GEOID20", "population", "geometry"]
    ]
    src.to_file(units_path, driver="GeoJSON")

    for out_subdir in ("a", "b"):
        rc = main(
            [
                "generate",
                "--districts",
                "4",
                "--units",
                str(units_path),
                "--geography",
                "vtd",
                "--out",
                str(tmp_path / out_subdir),
            ]
        )
        assert rc == 0
    assert (tmp_path / "a" / "metrics.json").read_text() == (
        tmp_path / "b" / "metrics.json"
    ).read_text()
    assert (tmp_path / "a" / "map.geojson").read_bytes() == (
        tmp_path / "b" / "map.geojson"
    ).read_bytes()


def test_generate_via_yaml_config(tmp_path: Path, synthetic_grid_4x4) -> None:
    units_path = tmp_path / "units.geojson"
    src = synthetic_grid_4x4.rename(columns={"unit_id": "GEOID20"})[
        ["GEOID20", "population", "geometry"]
    ]
    src.to_file(units_path, driver="GeoJSON")
    cfg = tmp_path / "c.yaml"
    cfg.write_text(
        f"districts: 4\nunits: {units_path}\ngeography: vtd\nout: {tmp_path / 'yaml_out'}\n",
        encoding="utf-8",
    )
    rc = main(["generate", "--config", str(cfg)])
    assert rc == 0
    assert (tmp_path / "yaml_out" / "map.geojson").is_file()


def test_score_via_cli(tmp_path: Path, synthetic_grid_4x4) -> None:
    units_path = tmp_path / "units.geojson"
    out_dir = tmp_path / "out"
    src = synthetic_grid_4x4.rename(columns={"unit_id": "GEOID20"})[
        ["GEOID20", "population", "geometry"]
    ]
    src.to_file(units_path, driver="GeoJSON")
    main(
        [
            "generate",
            "--districts",
            "4",
            "--units",
            str(units_path),
            "--geography",
            "vtd",
            "--out",
            str(out_dir),
        ]
    )
    rc = main(
        [
            "score",
            "--plan",
            str(out_dir / "map.geojson"),
            "--units",
            str(units_path),
            "--geography",
            "vtd",
        ]
    )
    assert rc == 0
