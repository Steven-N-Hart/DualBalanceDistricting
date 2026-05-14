"""Shared pytest fixtures."""

from __future__ import annotations

import geopandas as gpd
import pytest
from shapely.geometry import Polygon

from dualbalance.io import EQUAL_AREA_CRS


@pytest.fixture
def synthetic_grid_4x4() -> gpd.GeoDataFrame:
    """4x4 grid of unit-square cells, uniform population.

    16 units laid out at integer (col, row) positions in EPSG:5070. Each row
    has columns ``unit_id`` (``R{r}C{c}``), ``population`` (100), ``area``
    (computed from geometry), and ``geometry``. Population is uniform so a
    well-behaved 4-district algorithm should land on exactly 400 people per
    district.
    """
    rows = []
    for r in range(4):
        for c in range(4):
            poly = Polygon([(c, r), (c + 1, r), (c + 1, r + 1), (c, r + 1)])
            rows.append(
                {
                    "unit_id": f"R{r}C{c}",
                    "population": 100,
                    "geometry": poly,
                }
            )
    gdf = gpd.GeoDataFrame(rows, crs=EQUAL_AREA_CRS)
    gdf["area"] = gdf.geometry.area
    return gdf[["unit_id", "population", "area", "geometry"]]
