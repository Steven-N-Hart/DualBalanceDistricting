from __future__ import annotations

import math

import geopandas as gpd
import pytest

from dualbalance.districting import generate_plan
from dualbalance.scoring import score_plan
from dualbalance.types import Plan


def test_perfectly_balanced_grid_scores_one(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4, geography="test")
    metrics = score_plan(plan, synthetic_grid_4x4)
    assert metrics["pop_deviation_mean"] == 0.0
    assert metrics["pop_deviation_max"] == 0.0
    assert metrics["area_deviation_mean"] == 0.0
    assert metrics["area_deviation_max"] == 0.0
    assert metrics["dualbalance_score"] == 1.0


def test_compactness_of_2x2_blocks(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    # Quadrants are 2x2 blocks; perimeter 8, area 4.
    # Polsby-Popper = 4 * pi * 4 / 64 = pi / 4 ~= 0.7854.
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    metrics = score_plan(plan, synthetic_grid_4x4)
    expected_pp = math.pi / 4
    assert metrics["polsby_popper_mean"] == pytest.approx(expected_pp, rel=1e-6)
    assert metrics["polsby_popper_min"] == pytest.approx(expected_pp, rel=1e-6)
    # Reock: 2x2 block in min bounding circle radius sqrt(2) -> 2*pi area.
    # reock = 4 / (2*pi) = 2/pi ~= 0.6366.
    expected_reock = 2.0 / math.pi
    assert metrics["reock_mean"] == pytest.approx(expected_reock, rel=1e-3)
    assert metrics["reock_min"] == pytest.approx(expected_reock, rel=1e-3)


def test_per_district_block_present(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    metrics = score_plan(plan, synthetic_grid_4x4)
    districts = metrics["districts"]
    assert len(districts) == 4
    assert {d["district_id"] for d in districts} == {0, 1, 2, 3}
    for d in districts:
        assert d["population"] == 400.0
        assert d["area"] == 4.0
        assert d["n_units"] == 4
        assert d["pop_deviation"] == 0.0


def test_unbalanced_plan_has_lower_score(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    # Manually construct a deliberately bad plan: everything in district 0.
    bad = Plan(
        assignment={uid: 0 for uid in synthetic_grid_4x4["unit_id"]},
        n_districts=4,
        geography="test",
    )
    metrics = score_plan(bad, synthetic_grid_4x4)
    # Three districts empty -> max pop deviation = 1.0 (treated as 100% off).
    # District 0 has all 1600 vs target 400 -> deviation 3.0.
    assert metrics["pop_deviation_max"] == 3.0
    assert metrics["dualbalance_score"] < 0.5


def test_geography_tag_round_trips(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4, geography="vtd")
    metrics = score_plan(plan, synthetic_grid_4x4)
    assert metrics["geography"] == "vtd"


def test_metrics_dict_is_json_serializable(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    import json
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    metrics = score_plan(plan, synthetic_grid_4x4)
    # If this raises, our metrics dict has a non-serializable type lurking.
    json.dumps(metrics)
