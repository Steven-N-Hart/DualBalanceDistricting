from __future__ import annotations

import geopandas as gpd
import numpy as np
import pytest

from dualbalance.districting import generate_plan
from dualbalance.scoring import score_plan
from dualbalance.trades import tighten_to_reynolds


def _pop_totals(plan, units):
    totals = np.zeros(plan.n_districts)
    pop = units.set_index("unit_id")["population"]
    for uid, d in plan.assignment.items():
        totals[d] += pop[uid]
    return totals


def test_tighten_is_noop_on_perfectly_balanced_plan(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    # Synthetic 4x4 already produces perfect balance; tighten should not move.
    tight = tighten_to_reynolds(plan, synthetic_grid_4x4, pop_tolerance=0.005)
    assert tight.assignment == plan.assignment
    assert tight.metadata["reynolds_pop_moves"] == 0
    assert tight.metadata["reynolds_area_swaps"] == 0


def test_tighten_records_metadata(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    tight = tighten_to_reynolds(plan, synthetic_grid_4x4, pop_tolerance=0.005)
    md = tight.metadata
    for k in (
        "reynolds_pop_moves",
        "reynolds_area_swaps",
        "reynolds_pop_tolerance",
        "reynolds_final_pop_dev_max",
        "reynolds_final_area_dev_max",
    ):
        assert k in md, f"missing key {k}"


def test_tighten_preserves_unit_count(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    tight = tighten_to_reynolds(plan, synthetic_grid_4x4, pop_tolerance=0.005)
    assert set(tight.assignment.keys()) == set(plan.assignment.keys())
    assert sum(_pop_totals(tight, synthetic_grid_4x4)) == sum(_pop_totals(plan, synthetic_grid_4x4))


def test_tighten_is_deterministic(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    a = tighten_to_reynolds(plan, synthetic_grid_4x4, pop_tolerance=0.005)
    b = tighten_to_reynolds(plan, synthetic_grid_4x4, pop_tolerance=0.005)
    assert a.assignment == b.assignment


def _imbalanced_grid() -> gpd.GeoDataFrame:
    """4x4 grid with bottom-right cluster carrying 10x population."""
    from shapely.geometry import Polygon

    rows = []
    for r in range(4):
        for c in range(4):
            poly = Polygon([(c, r), (c + 1, r), (c + 1, r + 1), (c, r + 1)])
            pop = 10_000 if (r >= 2 and c >= 2) else 100
            rows.append({"unit_id": f"R{r}C{c}", "population": pop, "geometry": poly})
    gdf = gpd.GeoDataFrame(rows, crs="EPSG:5070")
    gdf["area"] = gdf.geometry.area
    return gdf


def test_tighten_runs_on_imbalanced_grid() -> None:
    # Generate with farthest-point seeding (which under-seeds the dense region),
    # then tighten; check that pop deviation does not get worse.
    gdf = _imbalanced_grid()

    plan = generate_plan(gdf, n_districts=4)
    tight = tighten_to_reynolds(plan, gdf, pop_tolerance=0.05, max_pop_passes=200)
    totals_before = _pop_totals(plan, gdf)
    totals_after = _pop_totals(tight, gdf)
    p_target = gdf["population"].sum() / 4
    before_max = float(np.abs(totals_before - p_target).max())
    after_max = float(np.abs(totals_after - p_target).max())
    assert after_max <= before_max + 1e-6  # never gets worse


def test_tighten_classic_variant_runs() -> None:
    """Classic variant: classic score never decreases, metadata records variant."""
    gdf = _imbalanced_grid()
    plan = generate_plan(gdf, n_districts=4)
    tight = tighten_to_reynolds(
        plan,
        gdf,
        pop_tolerance=0.05,
        max_pop_passes=200,
        score_variant="classic",
    )

    before = score_plan(plan, gdf)["dualbalance_score_classic"]
    after = score_plan(tight, gdf)["dualbalance_score_classic"]
    assert after >= before - 1e-9  # classic score never strictly worsens

    assert tight.metadata["reynolds_score_variant"] == "classic"
    assert "reynolds_pop_moves" in tight.metadata


def test_tighten_rejects_unknown_score_variant(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    with pytest.raises(ValueError, match="score_variant"):
        tighten_to_reynolds(
            plan,
            synthetic_grid_4x4,
            pop_tolerance=0.005,
            score_variant="bogus",
        )
