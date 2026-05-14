"""Deterministic radial seed placement.

Seeds are placed on a small circle around the population-weighted centroid
of the state, equally spaced by angle. With seeds arranged on a small
circle relative to the state's extent, the resulting Voronoi cells are
near-perfect radial slices (``pizza slices``) through the population
center, so each district naturally mixes dense (near the center) and
sparse (out to the boundary) territory.

This is the only seed method DualBalance uses. There are no alternatives,
no tuning knobs, and no iterations: the seed positions are a pure
function of the unit geometry and the district count ``N``.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np

from dualbalance.types import Seed


def place_seeds(units: gpd.GeoDataFrame, n: int) -> list[Seed]:
    """Place ``n`` seeds radially around the population-weighted centroid.

    Seed 0 starts at angle 0 (due east of the centroid) and seeds advance
    counter-clockwise in equal angular steps of ``2π/n``. Radius is
    ``0.1 %`` of the bounding-box diagonal — small enough that the
    Voronoi structure is dominated by the radial arrangement, large
    enough to keep seed positions numerically distinct.
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if n > len(units):
        raise ValueError(f"n={n} exceeds number of units ({len(units)})")

    centroids = units.geometry.centroid
    xs = np.asarray(centroids.x, dtype=float)
    ys = np.asarray(centroids.y, dtype=float)
    pops = np.asarray(units["population"], dtype=float)

    total_pop = float(pops.sum())
    if total_pop > 0:
        center_x = float((xs * pops).sum() / total_pop)
        center_y = float((ys * pops).sum() / total_pop)
    else:
        center_x = float(xs.mean())
        center_y = float(ys.mean())

    minx, miny, maxx, maxy = units.total_bounds
    diag = float(np.hypot(maxx - minx, maxy - miny))
    radius = diag * 0.001

    return [
        Seed(
            district_id=d,
            x=center_x + radius * float(np.cos(2.0 * np.pi * d / n)),
            y=center_y + radius * float(np.sin(2.0 * np.pi * d / n)),
        )
        for d in range(n)
    ]
