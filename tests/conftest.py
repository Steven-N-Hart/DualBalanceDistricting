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


@pytest.fixture
def synthetic_grid_4x4_with_counties() -> gpd.GeoDataFrame:
    """Same 4x4 grid, but every 2x2 block carries the same ``county`` value.

    Four counties (NW, NE, SW, SE), each 4 units. Lets tests assert that
    county-split reporting fires when the column is present.
    """
    rows = []
    for r in range(4):
        for c in range(4):
            poly = Polygon([(c, r), (c + 1, r), (c + 1, r + 1), (c, r + 1)])
            county = f"{'S' if r < 2 else 'N'}{'W' if c < 2 else 'E'}"
            rows.append(
                {
                    "unit_id": f"R{r}C{c}",
                    "population": 100,
                    "county": county,
                    "geometry": poly,
                }
            )
    gdf = gpd.GeoDataFrame(rows, crs=EQUAL_AREA_CRS)
    gdf["area"] = gdf.geometry.area
    return gdf[["unit_id", "population", "area", "county", "geometry"]]


@pytest.fixture
def synthetic_grid_4x4_with_demographics() -> gpd.GeoDataFrame:
    """4x4 grid plus race VAP and partisan vote columns.

    Per unit: ``vap_total=80``, ``vap_nhwhite=50``, ``vap_black=15``,
    ``vap_hispanic=10``, ``vap_aian=3``, ``vap_asian=2``. Statewide
    NH-white share is 50/80 = 62.5%; no district should be majority-Black
    on uniform data.

    Per unit: ``votes_R`` increases with column index, ``votes_D``
    decreases with column index, so a partition that respects columns
    will yield distinct R/D winners and a non-trivial efficiency gap.
    """
    rows = []
    for r in range(4):
        for c in range(4):
            poly = Polygon([(c, r), (c + 1, r), (c + 1, r + 1), (c, r + 1)])
            rows.append(
                {
                    "unit_id": f"R{r}C{c}",
                    "population": 100,
                    "vap_total": 80,
                    "vap_nhwhite": 50,
                    "vap_black": 15,
                    "vap_hispanic": 10,
                    "vap_aian": 3,
                    "vap_asian": 2,
                    "votes_R": 10 + 10 * c,
                    "votes_D": 40 - 10 * c,
                    "geometry": poly,
                }
            )
    gdf = gpd.GeoDataFrame(rows, crs=EQUAL_AREA_CRS)
    gdf["area"] = gdf.geometry.area
    return gdf[
        [
            "unit_id",
            "population",
            "area",
            "vap_total",
            "vap_nhwhite",
            "vap_black",
            "vap_hispanic",
            "vap_aian",
            "vap_asian",
            "votes_R",
            "votes_D",
            "geometry",
        ]
    ]
