from __future__ import annotations

import geopandas as gpd
import pytest

from dualbalance.districting import generate_plan


def test_all_units_assigned(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    assert set(plan.assignment.keys()) == set(synthetic_grid_4x4["unit_id"])


def test_district_ids_in_range(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    assert min(plan.assignment.values()) >= 0
    assert max(plan.assignment.values()) < 4


def test_all_districts_used_on_uniform_grid(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    assert set(plan.assignment.values()) == {0, 1, 2, 3}


def test_uniform_grid_pop_within_one_unit_of_target(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    # Uniform 100-pop 4x4 grid, 4 radial seeds at 0/90/180/270 degrees. The
    # 8 grid units lying on the 45-degree diagonals are equidistant from
    # two seeds; tie-breaking by ascending district id produces a slight
    # asymmetric drift, so the final split is 5-4-4-3 (in unit counts)
    # rather than 4-4-4-4. Total population is still conserved, every
    # district is non-empty, and per-district pop is within one unit of P*.
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    pop_by_district: dict[int, int] = {}
    for uid, d in plan.assignment.items():
        pop = int(
            synthetic_grid_4x4.loc[synthetic_grid_4x4["unit_id"] == uid, "population"].iloc[0]
        )
        pop_by_district[d] = pop_by_district.get(d, 0) + pop
    assert sum(pop_by_district.values()) == 1600
    assert set(pop_by_district) == {0, 1, 2, 3}
    p_target = 400
    for d, p in pop_by_district.items():
        assert abs(p - p_target) <= 100, f"D{d} pop={p} differs from {p_target} by > one unit"


def test_is_deterministic(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    p1 = generate_plan(synthetic_grid_4x4, n_districts=4)
    p2 = generate_plan(synthetic_grid_4x4, n_districts=4)
    assert p1.assignment == p2.assignment


def test_invariant_to_input_row_order(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    shuffled = synthetic_grid_4x4.sample(frac=1.0, random_state=42).reset_index(drop=True)
    p_original = generate_plan(synthetic_grid_4x4, n_districts=4)
    p_shuffled = generate_plan(shuffled, n_districts=4)
    assert p_original.assignment == p_shuffled.assignment


def test_metadata_recorded(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4, geography="vtd")
    assert plan.n_districts == 4
    assert plan.geography == "vtd"
    assert plan.metadata["targets"]["population"] == 400.0
    assert plan.metadata["targets"]["area"] == 4.0
    assert plan.metadata["contiguous"] is True
    assert plan.metadata["repair_iterations"] >= 0


def test_n_districts_zero_raises(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    with pytest.raises(ValueError, match="positive"):
        generate_plan(synthetic_grid_4x4, n_districts=0)


def test_n_districts_exceeds_units_raises(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    with pytest.raises(ValueError, match="exceeds"):
        generate_plan(synthetic_grid_4x4, n_districts=100)


def test_eight_districts_on_grid_still_all_assigned(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=8)
    assert set(plan.assignment.keys()) == set(synthetic_grid_4x4["unit_id"])
    assert min(plan.assignment.values()) >= 0
    assert max(plan.assignment.values()) < 8


def test_repair_dissolves_discontiguous_component(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    from dualbalance.districting import _repair_contiguity
    from dualbalance.types import Seed, Targets

    units_sorted = synthetic_grid_4x4.sort_values("unit_id", kind="mergesort").reset_index(
        drop=True
    )
    # Hand-built discontiguity: district 0 owns two disconnected corners.
    assignment = {uid: 1 for uid in units_sorted["unit_id"]}
    assignment["R0C0"] = 0
    assignment["R0C3"] = 0

    seeds = [Seed(0, 0.5, 0.5), Seed(1, 2.0, 2.0)]
    targets = Targets(population=800.0, area=8.0)

    new_assignment, n_iters, contiguous = _repair_contiguity(
        assignment, units_sorted, seeds, targets, norm=10.0, n_districts=2
    )

    assert contiguous is True
    assert n_iters >= 1
    assert new_assignment["R0C0"] == 0
    assert new_assignment["R0C3"] == 1
    assert set(new_assignment.keys()) == set(assignment.keys())
