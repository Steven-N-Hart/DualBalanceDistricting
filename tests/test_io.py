from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Polygon

from dualbalance.io import EQUAL_AREA_CRS, load_units, write_metrics


def _toy_gdf(crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "GEOID20": ["A", "B"],
            "P0010001": [100, 200],
            "geometry": [
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
            ],
        },
        crs=crs,
    )


def test_load_units_roundtrip(tmp_path: Path) -> None:
    src = _toy_gdf()
    fp = tmp_path / "units.geojson"
    src.to_file(fp, driver="GeoJSON")

    out = load_units(fp, id_column="GEOID20", pop_column="P0010001")

    assert list(out.columns) == ["unit_id", "population", "area", "geometry"]
    assert list(out["unit_id"]) == ["A", "B"]
    assert list(out["population"]) == [100, 200]
    # Area must be positive after reprojection to an equal-area CRS.
    assert (out["area"] > 0).all()
    assert out.crs is not None and out.crs.to_string().upper() == EQUAL_AREA_CRS


def test_load_units_preserves_county_column(tmp_path: Path) -> None:
    src = gpd.GeoDataFrame(
        {
            "GEOID20": ["27001A", "27003B"],
            "P0010001": [100, 200],
            "COUNTYFP": ["27001", "27003"],
            "geometry": [
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
            ],
        },
        crs="EPSG:4326",
    )
    fp = tmp_path / "units.geojson"
    src.to_file(fp, driver="GeoJSON")

    out = load_units(fp, id_column="GEOID20", pop_column="P0010001", county_column="COUNTYFP")

    assert "county" in out.columns
    assert list(out["county"]) == ["27001", "27003"]


def test_load_units_ignores_county_column_when_absent(tmp_path: Path) -> None:
    fp = tmp_path / "units.geojson"
    _toy_gdf().to_file(fp, driver="GeoJSON")
    out = load_units(fp, id_column="GEOID20", pop_column="P0010001", county_column="NOPE")
    # Missing column is silently dropped — not an error, since county is opt-in
    # diagnostic data and the generator doesn't depend on it.
    assert "county" not in out.columns


def test_load_units_extra_columns_mapping(tmp_path: Path) -> None:
    src = gpd.GeoDataFrame(
        {
            "GEOID20": ["A", "B"],
            "P0010001": [100, 200],
            "P3_004N": [10, 30],
            "PRES20R": [55, 40],
            "PRES20D": [45, 60],
            "geometry": [
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
            ],
        },
        crs="EPSG:4326",
    )
    fp = tmp_path / "units.geojson"
    src.to_file(fp, driver="GeoJSON")

    out = load_units(
        fp,
        id_column="GEOID20",
        pop_column="P0010001",
        extra_columns={"vap_black": "P3_004N", "votes_R": "PRES20R", "votes_D": "PRES20D"},
    )

    assert {"vap_black", "votes_R", "votes_D"}.issubset(out.columns)
    assert list(out["vap_black"]) == [10, 30]
    assert list(out["votes_R"]) == [55, 40]


def test_load_units_extra_columns_list(tmp_path: Path) -> None:
    src = gpd.GeoDataFrame(
        {
            "GEOID20": ["A", "B"],
            "P0010001": [100, 200],
            "vap_black": [10, 30],
            "geometry": [
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
            ],
        },
        crs="EPSG:4326",
    )
    fp = tmp_path / "units.geojson"
    src.to_file(fp, driver="GeoJSON")

    out = load_units(
        fp,
        id_column="GEOID20",
        pop_column="P0010001",
        extra_columns=["vap_black"],  # identity mapping when source uses canonical names
    )
    assert "vap_black" in out.columns
    assert list(out["vap_black"]) == [10, 30]


def test_load_units_extra_columns_missing_silently_dropped(tmp_path: Path) -> None:
    fp = tmp_path / "units.geojson"
    _toy_gdf().to_file(fp, driver="GeoJSON")
    out = load_units(
        fp,
        id_column="GEOID20",
        pop_column="P0010001",
        extra_columns={"votes_R": "DOES_NOT_EXIST"},
    )
    # Opt-in column not in source -> silently absent (not an error).
    assert "votes_R" not in out.columns


def test_load_units_missing_id_column_raises(tmp_path: Path) -> None:
    fp = tmp_path / "units.geojson"
    _toy_gdf().to_file(fp, driver="GeoJSON")
    with pytest.raises(ValueError, match="missing ID column"):
        load_units(fp, id_column="NOPE", pop_column="P0010001")


def test_load_units_missing_pop_column_raises(tmp_path: Path) -> None:
    fp = tmp_path / "units.geojson"
    _toy_gdf().to_file(fp, driver="GeoJSON")
    with pytest.raises(ValueError, match="missing population column"):
        load_units(fp, id_column="GEOID20", pop_column="NOPE")


def test_write_metrics_is_deterministic(tmp_path: Path) -> None:
    metrics = {"b": 2, "a": 1, "nested": {"y": 4, "x": 3}}
    fp = tmp_path / "metrics.json"
    write_metrics(metrics, fp)
    text = fp.read_text(encoding="utf-8")
    # Top-level keys sorted alphabetically.
    parsed = json.loads(text)
    assert list(parsed.keys()) == ["a", "b", "nested"]
    # Writing the same metrics again produces byte-identical output.
    write_metrics(metrics, fp.with_name("metrics2.json"))
    assert text == fp.with_name("metrics2.json").read_text(encoding="utf-8")


def test_synthetic_grid_fixture(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    gdf = synthetic_grid_4x4
    assert len(gdf) == 16
    assert set(gdf.columns) == {"unit_id", "population", "area", "geometry"}
    assert gdf["population"].sum() == 1600
    assert gdf.crs.to_string().upper() == EQUAL_AREA_CRS
