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


def test_uniform_grid_perfectly_balanced_population(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    pop_by_district: dict[int, int] = {}
    for uid, d in plan.assignment.items():
        pop = int(
            synthetic_grid_4x4.loc[synthetic_grid_4x4["unit_id"] == uid, "population"].iloc[0]
        )
        pop_by_district[d] = pop_by_district.get(d, 0) + pop
    # Uniform 100 across 16 units, 4 districts -> exactly 400 each.
    assert pop_by_district == {0: 400, 1: 400, 2: 400, 3: 400}


def test_uniform_grid_produces_quadrant_layout(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    # Locks in the expected geometry: the four districts split the grid into
    # the four 2x2 quadrants. District labels are an implementation detail
    # of seed-placement order; we assert the partition by groups instead.
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    groups: dict[int, set[str]] = {}
    for uid, d in plan.assignment.items():
        groups.setdefault(d, set()).add(uid)
    expected_quadrants = {
        frozenset({"R0C0", "R0C1", "R1C0", "R1C1"}),  # NW
        frozenset({"R0C2", "R0C3", "R1C2", "R1C3"}),  # NE
        frozenset({"R2C0", "R2C1", "R3C0", "R3C1"}),  # SW
        frozenset({"R2C2", "R2C3", "R3C2", "R3C3"}),  # SE
    }
    assert {frozenset(g) for g in groups.values()} == expected_quadrants


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
    assert plan.metadata["converged"] is True
    assert plan.metadata["n_iterations"] >= 1
    assert plan.metadata["targets"]["population"] == 400.0
    assert plan.metadata["alpha"] == 1.0
    assert plan.metadata["beta"] == 1.0


def test_converges_quickly_on_uniform_grid(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    assert plan.metadata["converged"]
    assert plan.metadata["n_iterations"] <= 5


def test_n_districts_zero_raises(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    with pytest.raises(ValueError, match="positive"):
        generate_plan(synthetic_grid_4x4, n_districts=0)


def test_n_districts_exceeds_units_raises(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    with pytest.raises(ValueError, match="exceeds"):
        generate_plan(synthetic_grid_4x4, n_districts=100)


def test_max_iter_zero_raises(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    with pytest.raises(ValueError, match="max_iter"):
        generate_plan(synthetic_grid_4x4, n_districts=4, max_iter=0)


def test_eight_districts_on_grid_still_all_assigned(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    # Asking for more districts than the natural geometry supports cleanly is
    # a useful stress test of basic invariants (no crash, all units assigned).
    plan = generate_plan(synthetic_grid_4x4, n_districts=8)
    assert set(plan.assignment.keys()) == set(synthetic_grid_4x4["unit_id"])
    assert min(plan.assignment.values()) >= 0
    assert max(plan.assignment.values()) < 8


def test_generate_plan_marks_contiguous_in_metadata(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    assert plan.metadata["contiguous"] is True
    # Quadrant result was already contiguous, so no repair work needed.
    assert plan.metadata["repair_iterations"] == 0


def test_repair_dissolves_discontiguous_component(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    # Importing the private helper to exercise the repair branch directly.
    from dualbalance.districting import _repair_contiguity
    from dualbalance.types import Seed, Targets

    units_sorted = synthetic_grid_4x4.sort_values("unit_id", kind="mergesort").reset_index(
        drop=True
    )
    # Hand-built discontiguity: district 0 owns two disconnected corners,
    # district 1 owns the rest.
    assignment = {uid: 1 for uid in units_sorted["unit_id"]}
    assignment["R0C0"] = 0
    assignment["R0C3"] = 0

    seeds = [Seed(0, 0.5, 0.5), Seed(1, 2.0, 2.0)]
    targets = Targets(population=800.0, area=8.0)

    new_assignment, n_iters, contiguous = _repair_contiguity(
        assignment,
        units_sorted,
        seeds,
        targets,
        alpha=1.0,
        beta=1.0,
        norm=10.0,
        n_districts=2,
        max_repair_iter=5,
    )

    assert contiguous is True
    assert n_iters >= 1
    # Tie on per-component population; tie-break on ascending min unit_id keeps
    # the {R0C0} component as district 0.
    assert new_assignment["R0C0"] == 0
    assert new_assignment["R0C3"] == 1
    # No unit was lost.
    assert set(new_assignment.keys()) == set(assignment.keys())


def test_repair_no_op_when_already_contiguous(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    plan_repaired = generate_plan(synthetic_grid_4x4, n_districts=4, repair=True)
    plan_raw = generate_plan(synthetic_grid_4x4, n_districts=4, repair=False)
    assert plan_repaired.assignment == plan_raw.assignment
    assert plan_repaired.metadata["repair_iterations"] == 0
