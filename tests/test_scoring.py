from __future__ import annotations

import json

import geopandas as gpd
import pytest

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
            "convex_hull_ratio",
            "length_width_ratio",
            "density",
        ):
            assert k in d, f"missing key {k}"
    # county keys absent when units have no county column
    assert "n_counties" not in districts[0]
    assert "counties_total" not in metrics


def test_geometry_metrics_in_unit_range(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    metrics = score_plan(plan, synthetic_grid_4x4)
    for k in (
        "convex_hull_ratio_mean",
        "convex_hull_ratio_min",
        "length_width_ratio_mean",
        "length_width_ratio_min",
    ):
        assert 0.0 <= metrics[k] <= 1.0


def test_density_metrics_uniform_grid(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    metrics = score_plan(plan, synthetic_grid_4x4)
    # All units have pop=100 area=1, so per-district density ≈ 100 regardless
    # of the partition. Gini should be ~0.
    assert metrics["density_mean"] == 100.0
    assert metrics["density_gini"] < 1e-9


def test_density_gini_nonzero_when_unbalanced(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    # Construct a deliberately unbalanced plan: one district gets all the
    # population, others are empty. Density distribution is highly skewed.
    uids = list(synthetic_grid_4x4["unit_id"])
    assignment = {u: (0 if i == 0 else 1) for i, u in enumerate(uids)}
    plan = Plan(assignment=assignment, n_districts=4, geography="test")
    metrics = score_plan(plan, synthetic_grid_4x4)
    # Two empty districts (density 0) plus two non-empty - Gini > 0.
    assert metrics["density_gini"] > 0.0


def test_county_metrics_reported_when_column_present(
    synthetic_grid_4x4_with_counties: gpd.GeoDataFrame,
) -> None:
    plan = generate_plan(synthetic_grid_4x4_with_counties, n_districts=4)
    metrics = score_plan(plan, synthetic_grid_4x4_with_counties)
    assert metrics["counties_total"] == 4
    # With 4 districts radially carved out of a 4-county grid, at least some
    # counties get split.
    assert metrics["counties_split"] >= 1
    assert metrics["county_pieces_total"] >= metrics["counties_total"]
    for d in metrics["districts"]:
        assert "n_counties" in d
        assert d["n_counties"] >= 1


def test_county_metrics_no_splits_when_aligned(
    synthetic_grid_4x4_with_counties: gpd.GeoDataFrame,
) -> None:
    # Assign each 2x2 county-block to its own district -> zero splits.
    county_to_district = {"SW": 0, "SE": 1, "NW": 2, "NE": 3}
    assignment = {
        row["unit_id"]: county_to_district[row["county"]]
        for _, row in synthetic_grid_4x4_with_counties.iterrows()
    }
    plan = Plan(assignment=assignment, n_districts=4, geography="test")
    metrics = score_plan(plan, synthetic_grid_4x4_with_counties)
    assert metrics["counties_total"] == 4
    assert metrics["counties_split"] == 0
    assert metrics["county_pieces_total"] == 4


def test_race_metrics_reported_when_vap_columns_present(
    synthetic_grid_4x4_with_demographics: gpd.GeoDataFrame,
) -> None:
    plan = generate_plan(synthetic_grid_4x4_with_demographics, n_districts=4)
    metrics = score_plan(plan, synthetic_grid_4x4_with_demographics)
    # 16 units * 80 VAP = 1280 total.
    assert metrics["vap_total"] == 1280.0
    # Statewide shares match the per-unit ratios (uniform fixture).
    assert metrics["statewide_share_nhwhite"] == pytest.approx(50 / 80)
    assert metrics["statewide_share_black"] == pytest.approx(15 / 80)
    # NH-white is supermajority everywhere - no minority-majority districts.
    assert metrics["nhwhite_majority_districts"] == 4
    assert metrics["minority_majority_districts"] == 0
    for d in metrics["districts"]:
        assert "share_nhwhite" in d
        assert "share_black" in d
        assert d["vap_total"] > 0


def test_partisan_metrics_reported_when_vote_columns_present(
    synthetic_grid_4x4_with_demographics: gpd.GeoDataFrame,
) -> None:
    plan = generate_plan(synthetic_grid_4x4_with_demographics, n_districts=4)
    metrics = score_plan(plan, synthetic_grid_4x4_with_demographics)
    assert metrics["seats_R"] + metrics["seats_D"] <= 4
    # Statewide R share: sum per col c of (10+10c) over (10+10c)+(40-10c) = (10+10c)/50
    # Summed over c=0..3 weighted by row count 4 each:
    #   total R = 4*(10+20+30+40) = 400
    #   total D = 4*(40+30+20+10) = 400
    # So statewide share is exactly 0.5 - perfectly competitive on aggregate.
    assert metrics["statewide_share_R"] == pytest.approx(0.5)
    # Efficiency gap and mean-median are well-defined floats.
    assert isinstance(metrics["efficiency_gap"], float)
    assert isinstance(metrics["mean_median_R"], float)
    for d in metrics["districts"]:
        assert "votes_R" in d
        assert "votes_D" in d
        assert "two_party_share_R" in d
        assert d["winner"] in ("R", "D", "tie", "none")


def test_partisan_efficiency_gap_zero_on_symmetric_plan(
    synthetic_grid_4x4_with_demographics: gpd.GeoDataFrame,
) -> None:
    # Two-district symmetric split (left half vs right half columns).
    assignment = {
        row["unit_id"]: 0 if int(row["unit_id"][3]) < 2 else 1
        for _, row in synthetic_grid_4x4_with_demographics.iterrows()
    }
    plan = Plan(assignment=assignment, n_districts=2, geography="test")
    metrics = score_plan(plan, synthetic_grid_4x4_with_demographics)
    # Two mirror-image districts (D wins one, R wins the other by equal
    # margins) -> wasted votes balance -> EG ~ 0.
    assert abs(metrics["efficiency_gap"]) < 1e-9


def test_metrics_absent_when_columns_absent(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    metrics = score_plan(plan, synthetic_grid_4x4)
    # None of the opt-in keys should leak in.
    for k in (
        "vap_total",
        "statewide_share_nhwhite",
        "nhwhite_majority_districts",
        "minority_majority_districts",
        "seats_R",
        "efficiency_gap",
        "mean_median_R",
    ):
        assert k not in metrics


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
