"""Deterministic seed placement for the DualBalance algorithm.

Two methods are supported, both deterministic:

- ``farthest-point`` (:func:`place_seeds_farthest_point`): farthest-point
  sampling seeded by population rank. Spreads seeds *geographically*. Suited
  to states with roughly uniform population density; on heavily urbanized
  states (e.g. MN with the Twin Cities metro) it under-seeds the dense
  region.
- ``population-slice`` (:func:`place_seeds_population_slice`): projects unit
  centroids onto the principal axis (first PCA direction) of the state,
  sorts along that axis, then drops a seed every time the cumulative
  population crosses an ``i/N`` boundary. Each seed is the
  population-weighted centroid of its 1/N-population slice. Puts more seeds
  inside dense regions by construction.

:func:`place_seeds` dispatches between them by name.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np

from dualbalance.types import Seed

SEED_METHODS = ("farthest-point", "population-slice")


def place_seeds(
    units: gpd.GeoDataFrame,
    n: int,
    method: str = "farthest-point",
) -> list[Seed]:
    """Place ``n`` deterministic seeds over ``units``.

    Dispatches by ``method``:

    - ``"farthest-point"``: see :func:`place_seeds_farthest_point` (default,
      preserves legacy behavior).
    - ``"population-slice"``: see :func:`place_seeds_population_slice`.
    """
    if method == "farthest-point":
        return place_seeds_farthest_point(units, n)
    if method == "population-slice":
        return place_seeds_population_slice(units, n)
    raise ValueError(
        f"unknown seed method {method!r}; valid: {list(SEED_METHODS)}"
    )


def place_seeds_farthest_point(units: gpd.GeoDataFrame, n: int) -> list[Seed]:
    """Farthest-point sampling seeded by population rank."""
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


def place_seeds_population_slice(units: gpd.GeoDataFrame, n: int) -> list[Seed]:
    """Population-balanced slice seeding along the principal axis.

    1. Compute the first principal-axis direction of the unit centroids
       (population-weighted), giving a deterministic 1-D order along the
       state's longest dimension.
    2. Sort units along that axis (ties: ascending ``unit_id``).
    3. Walk the sorted units, accumulating population. The k-th seed gets the
       slice of units whose cumulative-population endpoints straddle the
       interval ``[k / n, (k + 1) / n]`` of total population. Each seed sits
       at the population-weighted centroid of its slice.

    Compared to farthest-point sampling, this places more seeds inside
    densely-populated regions by construction -- which is what you want for
    states like Minnesota where Twin Cities holds ~55 % of the population in
    ~3 % of the area.
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if n > len(units):
        raise ValueError(f"n={n} exceeds number of units ({len(units)})")

    centroids = units.geometry.centroid
    xs = np.asarray(centroids.x, dtype=float)
    ys = np.asarray(centroids.y, dtype=float)
    pops = np.asarray(units["population"], dtype=float)
    ids = units["unit_id"].tolist()

    # Principal axis: SVD on the population-weighted, centered (x, y) matrix.
    # Population weights make the axis align with how the population is
    # actually distributed, not just the bounding-box shape.
    weights = pops / pops.sum() if pops.sum() > 0 else np.full_like(pops, 1 / len(pops))
    mean_x = float((xs * weights).sum())
    mean_y = float((ys * weights).sum())
    centered = np.column_stack([(xs - mean_x), (ys - mean_y)]) * np.sqrt(
        weights[:, None]
    )
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    axis = vh[0]  # first principal direction
    # Sign convention: positive x-component first (deterministic across runs).
    if axis[0] < 0 or (axis[0] == 0 and axis[1] < 0):
        axis = -axis

    projections = (xs - mean_x) * axis[0] + (ys - mean_y) * axis[1]

    # Stable sort along (projection asc, unit_id asc) for deterministic ties.
    order = sorted(range(len(units)), key=lambda i: (projections[i], ids[i]))

    total_pop = float(pops.sum())
    slice_target = total_pop / n
    n_units = len(order)
    seeds: list[Seed] = []
    slice_indices: list[int] = []
    cum = 0.0
    current_slice = 0
    processed = 0

    for idx in order:
        slice_indices.append(idx)
        processed += 1
        cum += pops[idx]
        if current_slice >= n - 1:
            # On the last slice -- absorb everything left.
            continue
        units_left = n_units - processed
        slices_left = n - current_slice - 1
        threshold = (current_slice + 1) * slice_target
        # Close if we've hit the cumulative population threshold, OR if the
        # remaining slices need every remaining unit just to be non-empty.
        if cum >= threshold or units_left <= slices_left:
            seeds.append(
                _weighted_centroid_seed(current_slice, slice_indices, xs, ys, pops)
            )
            slice_indices = []
            current_slice += 1

    if slice_indices:
        seeds.append(
            _weighted_centroid_seed(current_slice, slice_indices, xs, ys, pops)
        )

    return seeds


def _weighted_centroid_seed(
    district_id: int,
    indices: list[int],
    xs: np.ndarray,
    ys: np.ndarray,
    pops: np.ndarray,
) -> Seed:
    idx_arr = np.asarray(indices)
    w = pops[idx_arr]
    tw = float(w.sum())
    if tw > 0:
        cx = float((xs[idx_arr] * w).sum() / tw)
        cy = float((ys[idx_arr] * w).sum() / tw)
    else:
        cx = float(xs[idx_arr].mean())
        cy = float(ys[idx_arr].mean())
    return Seed(district_id=district_id, x=cx, y=cy)
