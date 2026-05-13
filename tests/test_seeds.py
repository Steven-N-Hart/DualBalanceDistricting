from __future__ import annotations

import geopandas as gpd
import pytest

from dualbalance.seeds import place_seeds
from dualbalance.types import Seed


def test_place_seeds_returns_n_seeds(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    seeds = place_seeds(synthetic_grid_4x4, n=4)
    assert len(seeds) == 4
    assert [s.district_id for s in seeds] == [0, 1, 2, 3]


def test_place_seeds_is_deterministic(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    s1 = place_seeds(synthetic_grid_4x4, n=4)
    s2 = place_seeds(synthetic_grid_4x4, n=4)
    assert s1 == s2


def test_place_seeds_invariant_to_input_row_order(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    shuffled = synthetic_grid_4x4.sample(frac=1.0, random_state=42).reset_index(drop=True)
    assert place_seeds(synthetic_grid_4x4, n=4) == place_seeds(shuffled, n=4)


def test_place_seeds_n_too_large_raises(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    with pytest.raises(ValueError, match="exceeds"):
        place_seeds(synthetic_grid_4x4, n=100)


def test_place_seeds_n_zero_raises(synthetic_grid_4x4: gpd.GeoDataFrame) -> None:
    with pytest.raises(ValueError, match="positive"):
        place_seeds(synthetic_grid_4x4, n=0)


def test_place_seeds_picks_corners_first_on_uniform_grid(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    # Uniform population -> first seed wins on ascending unit_id (R0C0,
    # centroid 0.5, 0.5). Farthest from that corner is R3C3 at (3.5, 3.5).
    seeds = place_seeds(synthetic_grid_4x4, n=2)
    assert seeds[0] == Seed(district_id=0, x=0.5, y=0.5)
    assert seeds[1] == Seed(district_id=1, x=3.5, y=3.5)


def test_place_seeds_four_corners_on_uniform_grid(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    # After R0C0 + R3C3, the next two seeds tie at distance 3 from each
    # existing seed. Tie-break on ascending unit_id -> R0C3 (3.5, 0.5) before
    # R3C0 (0.5, 3.5).
    seeds = place_seeds(synthetic_grid_4x4, n=4)
    assert seeds[2] == Seed(district_id=2, x=3.5, y=0.5)
    assert seeds[3] == Seed(district_id=3, x=0.5, y=3.5)


def test_place_seeds_highest_pop_wins_first(
    synthetic_grid_4x4: gpd.GeoDataFrame,
) -> None:
    # Bump R2C2's population so it becomes the first seed instead of R0C0.
    units = synthetic_grid_4x4.copy()
    units.loc[units["unit_id"] == "R2C2", "population"] = 1000
    seeds = place_seeds(units, n=1)
    assert seeds[0] == Seed(district_id=0, x=2.5, y=2.5)
