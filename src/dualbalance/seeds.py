"""Deterministic seed placement for the DualBalance algorithm.

Farthest-point sampling seeded by population rank:

- Seed 0 is the centroid of the highest-population unit.
- Each subsequent seed is the centroid of the unit whose minimum geographic
  distance to any already-placed seed is maximal.
- All ties (on population for seed 0; on min-distance for later seeds) break
  by ascending ``unit_id``.

Seeds are unit centroids, not arbitrary points, so initial placement is fully
discrete and reproducible. Later, the iterative districting loop will move
seeds to population-weighted centroids of their assigned units.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np

from dualbalance.types import Seed


def place_seeds(units: gpd.GeoDataFrame, n: int) -> list[Seed]:
    """Place ``n`` deterministic seeds over ``units``.

    Args:
        units: GeoDataFrame with ``unit_id``, ``population``, ``geometry``
            columns (the canonical schema produced by ``io.load_units``).
        n: number of seeds (districts).

    Returns:
        Seeds with ascending ``district_id`` ``0..n-1``.
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if n > len(units):
        raise ValueError(f"n={n} exceeds number of units ({len(units)})")

    # Stable sort by (population desc, unit_id asc) gives the seed-0 candidate
    # at row 0 and a fully deterministic ordering for subsequent picks.
    sorted_units = units.sort_values(
        ["population", "unit_id"],
        ascending=[False, True],
        kind="mergesort",
    ).reset_index(drop=True)

    centroids = sorted_units.geometry.centroid
    xs = np.asarray(centroids.x, dtype=float)
    ys = np.asarray(centroids.y, dtype=float)
    ids: list[str] = sorted_units["unit_id"].tolist()

    chosen: list[int] = [0]
    # min_dist[i] tracks the minimum distance from unit i to any chosen seed.
    min_dist = np.full(len(sorted_units), np.inf)

    while len(chosen) < n:
        last = chosen[-1]
        dx = xs - xs[last]
        dy = ys - ys[last]
        np.minimum(min_dist, np.sqrt(dx * dx + dy * dy), out=min_dist)

        masked = min_dist.copy()
        masked[chosen] = -np.inf
        max_d = masked.max()
        candidate_indices = np.where(masked == max_d)[0]
        # Tie-break on ascending unit_id (lex). Indices may refer to rows with
        # arbitrary unit_id strings, so compare by the string itself.
        best = min(candidate_indices.tolist(), key=lambda i: ids[i])
        chosen.append(best)

    return [
        Seed(district_id=d_id, x=float(xs[idx]), y=float(ys[idx]))
        for d_id, idx in enumerate(chosen)
    ]
