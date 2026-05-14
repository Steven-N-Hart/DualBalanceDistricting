from __future__ import annotations

import json

import geopandas as gpd

from dualbalance.districting import generate_plan
from dualbalance.scoring import score_plan
from dualbalance.types import Plan


def test_uniform_grid_scores_near_one(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    # Radial seeds on the 4x4 uniform grid produce a 5-4-4-3 split (diagonal
    # tie-breaks favor lower district ids). Score is high but not 1.0; the
    # algorithm hits 1.0 only when the geometry has no diagonal ambiguity.
    plan = generate_plan(synthetic_grid_4x4, n_districts=4, geography="test")
    metrics = score_plan(plan, synthetic_grid_4x4)
    assert metrics["dualbalance_score"] > 0.85
    assert metrics["pop_deviation_max"] <= 0.25
    assert metrics["area_deviation_max"] <= 0.25


def test_compactness_metrics_are_computed(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    metrics = score_plan(plan, synthetic_grid_4x4)
    assert 0.0 <= metrics["polsby_popper_min"] <= 1.0
    assert metrics["polsby_popper_mean"] >= metrics["polsby_popper_min"]
    assert 0.0 <= metrics["reock_min"] <= 1.0
    assert metrics["reock_mean"] >= metrics["reock_min"]


def test_per_district_block_present(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    metrics = score_plan(plan, synthetic_grid_4x4)
    districts = metrics["districts"]
    assert len(districts) == 4
    assert {d["district_id"] for d in districts} == {0, 1, 2, 3}
    for d in districts:
        for k in (
            "population",
            "area",
            "n_units",
            "pop_deviation",
            "area_deviation",
            "polsby_popper",
            "reock",
        ):
            assert k in d, f"missing key {k}"


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
    # Three districts empty -> max pop deviation = 1.0.
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
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    metrics = score_plan(plan, synthetic_grid_4x4)
    json.dumps(metrics)  # raises if any value is non-serializable
