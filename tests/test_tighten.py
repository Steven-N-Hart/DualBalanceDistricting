from __future__ import annotations

import geopandas as gpd
import numpy as np
import pytest

from dualbalance.districting import generate_plan
from dualbalance.scoring import score_plan
from dualbalance.tighten import tighten_population


def _pop_dev_max(plan, units) -> float:
    p_target = float(units["population"].sum()) / plan.n_districts
    indexed = units.set_index("unit_id")
    totals = np.zeros(plan.n_districts)
    for uid, d in plan.assignment.items():
        totals[d] += float(indexed.loc[uid, "population"])
    return float(np.max(np.abs(totals - p_target)) / p_target)


def test_tighten_is_noop_on_already_balanced_plan(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    tight = tighten_population(plan, synthetic_grid_4x4, pop_tolerance=0.5)
    # Tolerance of 50% trivially holds for the 4x4 grid (max dev ~ 25%).
    assert tight.assignment == plan.assignment
    assert tight.metadata["tighten_pop_moves"] == 0


def test_tighten_reduces_max_deviation_on_skewed_grid() -> None:
    from shapely.geometry import Polygon

    rows = []
    for r in range(4):
        for c in range(4):
            poly = Polygon([(c, r), (c + 1, r), (c + 1, r + 1), (c, r + 1)])
            pop = 10_000 if (r >= 2 and c >= 2) else 100
            rows.append({"unit_id": f"R{r}C{c}", "population": pop, "geometry": poly})
    gdf = gpd.GeoDataFrame(rows, crs="EPSG:5070")
    gdf["area"] = gdf.geometry.area

    plan = generate_plan(gdf, n_districts=4)
    before = _pop_dev_max(plan, gdf)
    tight = tighten_population(plan, gdf, pop_tolerance=0.05)
    after = _pop_dev_max(tight, gdf)
    assert after <= before + 1e-9


def test_tighten_records_metadata(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    tight = tighten_population(plan, synthetic_grid_4x4, pop_tolerance=0.01)
    for key in ("tighten_pop_moves", "tighten_pop_tolerance", "tighten_pop_final_dev_max"):
        assert key in tight.metadata


def test_tighten_preserves_unit_count(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    tight = tighten_population(plan, synthetic_grid_4x4, pop_tolerance=0.01)
    assert set(tight.assignment.keys()) == set(plan.assignment.keys())


def test_tighten_is_deterministic(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    a = tighten_population(plan, synthetic_grid_4x4, pop_tolerance=0.01)
    b = tighten_population(plan, synthetic_grid_4x4, pop_tolerance=0.01)
    assert a.assignment == b.assignment


def test_tighten_rejects_negative_tolerance(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    with pytest.raises(ValueError, match="pop_tolerance"):
        tighten_population(plan, synthetic_grid_4x4, pop_tolerance=-0.01)


def test_tighten_does_not_mutate_input(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    plan = generate_plan(synthetic_grid_4x4, n_districts=4)
    original_assignment = dict(plan.assignment)
    original_metadata = dict(plan.metadata)
    _ = tighten_population(plan, synthetic_grid_4x4, pop_tolerance=0.01)
    assert plan.assignment == original_assignment
    assert plan.metadata == original_metadata


def test_tighten_improves_dualbalance_score_on_radial_imbalance() -> None:
    # 8-cell strip with skewed population, 2 districts: radial assignment
    # splits the strip in half by angle, but the pop is uneven; tightening
    # should reduce pop dev and improve the dualbalance score.
    from shapely.geometry import Polygon

    rows = []
    for i in range(8):
        rows.append(
            {
                "unit_id": f"U{i:02d}",
                "population": (200 if i < 4 else 100),
                "geometry": Polygon([(i, 0), (i + 1, 0), (i + 1, 1), (i, 1)]),
            }
        )
    gdf = gpd.GeoDataFrame(rows, crs="EPSG:5070")
    gdf["area"] = gdf.geometry.area

    plan = generate_plan(gdf, n_districts=2)
    tight = tighten_population(plan, gdf, pop_tolerance=0.01)
    score_before = score_plan(plan, gdf)["dualbalance_score"]
    score_after = score_plan(tight, gdf)["dualbalance_score"]
    assert score_after >= score_before - 1e-9
