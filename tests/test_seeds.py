from __future__ import annotations

import math

import geopandas as gpd
import pytest
from shapely.geometry import Polygon

from dualbalance.seeds import place_seeds


def test_place_seeds_returns_n_seeds(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    seeds = place_seeds(synthetic_grid_4x4, n=4)
    assert len(seeds) == 4
    assert [s.district_id for s in seeds] == [0, 1, 2, 3]


def test_place_seeds_is_deterministic(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    a = place_seeds(synthetic_grid_4x4, n=4)
    b = place_seeds(synthetic_grid_4x4, n=4)
    assert a == b


def test_place_seeds_invariant_to_row_order(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    shuffled = synthetic_grid_4x4.sample(frac=1.0, random_state=7).reset_index(drop=True)
    a = place_seeds(synthetic_grid_4x4, n=4)
    b = place_seeds(shuffled, n=4)
    assert a == b


def test_place_seeds_centers_on_population_weighted_centroid(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    seeds = place_seeds(synthetic_grid_4x4, n=8)
    mean_x = sum(s.x for s in seeds) / len(seeds)
    mean_y = sum(s.y for s in seeds) / len(seeds)
    assert math.isclose(mean_x, 2.0, abs_tol=1e-6)
    assert math.isclose(mean_y, 2.0, abs_tol=1e-6)


def test_place_seeds_equally_spaced_by_angle(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    n = 8
    seeds = place_seeds(synthetic_grid_4x4, n=n)
    cx = sum(s.x for s in seeds) / n
    cy = sum(s.y for s in seeds) / n
    angles = [math.atan2(s.y - cy, s.x - cx) % (2 * math.pi) for s in seeds]
    expected = [(2 * math.pi * k / n) % (2 * math.pi) for k in range(n)]
    for got, want in zip(angles, expected, strict=True):
        assert math.isclose(got, want, abs_tol=1e-6)


def test_place_seeds_radius_is_small_relative_to_extent(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    seeds = place_seeds(synthetic_grid_4x4, n=4)
    cx = sum(s.x for s in seeds) / len(seeds)
    cy = sum(s.y for s in seeds) / len(seeds)
    bbox_diag = math.hypot(4.0, 4.0)
    for s in seeds:
        r = math.hypot(s.x - cx, s.y - cy)
        assert math.isclose(r, bbox_diag * 0.001, rel_tol=1e-6)


def test_place_seeds_rejects_nonpositive_n(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    with pytest.raises(ValueError, match="positive"):
        place_seeds(synthetic_grid_4x4, n=0)


def test_place_seeds_rejects_n_exceeding_units(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    with pytest.raises(ValueError, match="exceeds"):
        place_seeds(synthetic_grid_4x4, n=100)


def test_place_seeds_falls_back_to_geometric_centroid_when_zero_population() -> None:
    rows = [
        {
            "unit_id": f"U{i}",
            "population": 0,
            "geometry": Polygon([(i, 0), (i + 1, 0), (i + 1, 1), (i, 1)]),
        }
        for i in range(4)
    ]
    gdf = gpd.GeoDataFrame(rows, crs="EPSG:5070")
    gdf["area"] = gdf.geometry.area
    seeds = place_seeds(gdf, n=2)
    mean_x = (seeds[0].x + seeds[1].x) / 2
    assert math.isclose(mean_x, 2.0, abs_tol=1e-6)


def test_seeds_are_numerically_distinct(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    seeds = place_seeds(synthetic_grid_4x4, n=8)
    coords = {(round(s.x, 9), round(s.y, 9)) for s in seeds}
    assert len(coords) == 8


def test_seeds_xy_are_floats(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    seeds = place_seeds(synthetic_grid_4x4, n=4)
    for s in seeds:
        assert isinstance(s.x, float)
        assert isinstance(s.y, float)
