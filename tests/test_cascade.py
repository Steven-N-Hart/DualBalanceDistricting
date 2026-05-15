from __future__ import annotations

import geopandas as gpd
import pytest

from dualbalance.cascade import generate_cascade_plan
from dualbalance.scoring import score_plan


def test_cascade_requires_county_column(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    with pytest.raises(ValueError, match="county"):
        generate_cascade_plan(synthetic_grid_4x4, n_districts=4)


def test_cascade_preserves_counties(
    synthetic_grid_4x4_with_counties: gpd.GeoDataFrame,
) -> None:
    plan = generate_cascade_plan(synthetic_grid_4x4_with_counties, n_districts=4)
    # 4 counties, 4 districts: every county should be entirely within one district.
    # All four units of a county should share the same district id.
    indexed = synthetic_grid_4x4_with_counties.set_index("unit_id")
    by_county: dict[str, set[int]] = {}
    for uid, did in plan.assignment.items():
        c = str(indexed.loc[uid, "county"])
        by_county.setdefault(c, set()).add(did)
    for c, dids in by_county.items():
        assert len(dids) == 1, f"county {c} split across districts {dids}"


def test_cascade_is_deterministic(
    synthetic_grid_4x4_with_counties: gpd.GeoDataFrame,
) -> None:
    p1 = generate_cascade_plan(synthetic_grid_4x4_with_counties, n_districts=4)
    p2 = generate_cascade_plan(synthetic_grid_4x4_with_counties, n_districts=4)
    assert p1.assignment == p2.assignment


def test_cascade_splits_oversize_county(
    synthetic_grid_4x4_with_counties: gpd.GeoDataFrame,
) -> None:
    # One mega-county = whole state. Cascade auto-splits it via PRISM into
    # 4 pseudo-counties and records the split in metadata.
    gdf = synthetic_grid_4x4_with_counties.copy()
    gdf["county"] = "ONE"
    plan = generate_cascade_plan(gdf, n_districts=4)
    assert set(plan.assignment.values()) <= {0, 1, 2, 3}
    assert plan.metadata["counties_split_by_cap"] == {"ONE": 4}


def test_cascade_metadata_records_seeds(
    synthetic_grid_4x4_with_counties: gpd.GeoDataFrame,
) -> None:
    plan = generate_cascade_plan(synthetic_grid_4x4_with_counties, n_districts=4)
    assert plan.metadata["algorithm"] == "cascade"
    assert len(plan.metadata["seed_counties"]) == 4
    assert plan.metadata["n_counties"] == 4


def test_cascade_plan_scores(
    synthetic_grid_4x4_with_counties: gpd.GeoDataFrame,
) -> None:
    plan = generate_cascade_plan(synthetic_grid_4x4_with_counties, n_districts=4)
    metrics = score_plan(plan, synthetic_grid_4x4_with_counties)
    # 4 counties of equal size and equal pop, perfectly assigned 1:1 to districts
    # means zero pop_dev, zero area_dev, zero county splits.
    assert metrics["pop_deviation_mean"] == 0.0
    assert metrics["area_deviation_mean"] == 0.0
    assert metrics["counties_split"] == 0
