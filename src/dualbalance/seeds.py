"""Deterministic radial seed placement.

Seeds are placed on a small circle around the population-weighted centroid
of the state, equally spaced by angle. With seeds arranged on a small
circle relative to the state's extent, the resulting Voronoi cells are
near-perfect radial slices (``pizza slices``) through the population
center, so each district naturally mixes dense (near the center) and
sparse (out to the boundary) territory.

Two strategies are available:

``place_seeds`` (radial)
    Seeds at equally-spaced angles ``2π·d/N``.  Works well for states
    whose population is roughly uniform in angle from the centroid.

``place_seeds_angular_quantile``
    Seeds at angles that divide the *cumulative angular population* into N
    equal slices.  Angular spacing compresses in densely-populated sectors
    and expands in sparse ones, adapting to polycentric or coastal
    geographies without any state-specific switching.  Seeds remain on the
    same small circle; only the angular positions change.

Both are pure functions of ``(units, n)`` — deterministic, no tuning knobs.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np

from dualbalance.types import Seed


def place_seeds(
    units: gpd.GeoDataFrame,
    n: int,
    *,
    rotation_offset: float = 0.0,
) -> list[Seed]:
    """Place ``n`` seeds radially around the population-weighted centroid.

    Seed 0 starts at ``rotation_offset`` radians east of the centroid and
    seeds advance counter-clockwise in equal angular steps of ``2π/n``.
    The default ``rotation_offset=0.0`` places seed 0 due east. Radius is
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
            x=center_x + radius * float(np.cos(2.0 * np.pi * d / n + rotation_offset)),
            y=center_y + radius * float(np.sin(2.0 * np.pi * d / n + rotation_offset)),
        )
        for d in range(n)
    ]


_HILBERT_ORDER = 16  # 2^16 × 2^16 grid — sufficient precision for any state VTD set


def _xy_to_hilbert(ix: int, iy: int) -> int:
    """Hilbert curve index for integer grid point (ix, iy) at fixed order."""
    n = 1 << _HILBERT_ORDER
    d = 0
    s = n >> 1
    x, y = ix, iy
    while s > 0:
        rx = 1 if (x & s) > 0 else 0
        ry = 1 if (y & s) > 0 else 0
        d += s * s * ((3 * rx) ^ ry)
        if ry == 0:
            if rx == 1:
                x = s - 1 - x
                y = s - 1 - y
            x, y = y, x
        s >>= 1
    return d


def place_seeds_hilbert(
    units: gpd.GeoDataFrame,
    n: int,
) -> list[Seed]:
    """Place ``n`` seeds by dividing a Hilbert-ordered population into N segments.

    Maps unit centroids onto a Hilbert space-filling curve (fixed order 16),
    sorts units by their curve index (unit_id tie-break), then greedily
    assigns units to N equal-population segments in curve order.  One seed
    is placed at each segment's population-weighted centroid.

    The Hilbert curve preserves spatial locality: nearby units in 2D space
    tend to be nearby in curve order, so each segment corresponds to a
    geographically coherent region.  Unlike radial seeding, the segments
    follow the actual topology of the population distribution — coastal rings,
    elongated lobes, and density cliffs are all represented naturally by the
    curve traversal rather than mapped through a single centroid.

    Deterministic: fixed curve order (16), unit_id ascending tie-break for
    units that map to the same grid cell.
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if n > len(units):
        raise ValueError(f"n={n} exceeds number of units ({len(units)})")

    units_sorted = units.sort_values("unit_id", kind="mergesort").reset_index(drop=True)
    centroids = units_sorted.geometry.centroid
    xs = np.asarray(centroids.x, dtype=float)
    ys = np.asarray(centroids.y, dtype=float)
    pops = np.asarray(units_sorted["population"], dtype=float)

    # Normalize centroids to [0, 2^order - 1] integer grid.
    n_grid = float((1 << _HILBERT_ORDER) - 1)
    x_min, x_max = xs.min(), xs.max()
    y_min, y_max = ys.min(), ys.max()
    x_span = x_max - x_min if x_max > x_min else 1.0
    y_span = y_max - y_min if y_max > y_min else 1.0

    ix = np.round((xs - x_min) / x_span * n_grid).astype(int)
    iy = np.round((ys - y_min) / y_span * n_grid).astype(int)

    # Compute Hilbert index for each unit; stable-sort preserves unit_id tie-break.
    hilbert_idx = np.array([_xy_to_hilbert(int(ix[i]), int(iy[i])) for i in range(len(units_sorted))])
    order = np.argsort(hilbert_idx, kind="stable")

    sorted_xs = xs[order]
    sorted_ys = ys[order]
    sorted_pops = pops[order]

    total = float(sorted_pops.sum())
    target_per_seg = total / n

    # Greedy segment assignment: advance to next segment once target is reached.
    seg_assignments = np.empty(len(order), dtype=int)
    current_seg = 0
    current_pop = 0.0
    for i in range(len(order)):
        seg_assignments[i] = current_seg
        current_pop += float(sorted_pops[i])
        if current_seg < n - 1 and current_pop >= (current_seg + 1) * target_per_seg:
            current_seg += 1

    # Place each seed at its segment's population-weighted centroid.
    seeds = []
    for d in range(n):
        mask = seg_assignments == d
        seg_xs = sorted_xs[mask]
        seg_ys = sorted_ys[mask]
        seg_pops = sorted_pops[mask]
        seg_total = float(seg_pops.sum())
        if seg_total > 0:
            cx = float((seg_xs * seg_pops).sum() / seg_total)
            cy = float((seg_ys * seg_pops).sum() / seg_total)
        else:
            cx = float(seg_xs.mean())
            cy = float(seg_ys.mean())
        seeds.append(Seed(district_id=d, x=cx, y=cy))

    return seeds


def _bisect_centroids(
    xs: np.ndarray,
    ys: np.ndarray,
    pops: np.ndarray,
    n: int,
) -> list[tuple[float, float]]:
    """Recursively bisect a set of units into n equal-population regions.

    Splits along the longer bounding-box axis at the population-weighted
    median.  Ties in coordinate value break by the array order (caller
    ensures this is unit_id ascending).  Returns a list of n (cx, cy)
    population-weighted centroids, one per leaf region.
    """
    total_pop = float(pops.sum())
    if n == 1:
        if total_pop > 0:
            cx = float((xs * pops).sum() / total_pop)
            cy = float((ys * pops).sum() / total_pop)
        else:
            cx = float(xs.mean())
            cy = float(ys.mean())
        return [(cx, cy)]

    # Choose split axis: whichever dimension spans more distance.
    x_range = float(xs.max() - xs.min())
    y_range = float(ys.max() - ys.min())
    split_on_x = x_range >= y_range

    coords = xs if split_on_x else ys

    # Sort along chosen axis; stable sort preserves unit_id tie-break.
    order = np.argsort(coords, kind="stable")
    sorted_pops = pops[order]
    cumsum = np.cumsum(sorted_pops)

    # Split at first unit where cumsum reaches half of total.
    target = total_pop / 2.0
    split = int(np.searchsorted(cumsum, target, side="left"))
    # Guarantee at least one unit on each side.
    split = max(1, min(split, len(order) - 1))

    left_idx = order[:split]
    right_idx = order[split:]

    left_n = n // 2
    right_n = n - left_n

    return (
        _bisect_centroids(xs[left_idx], ys[left_idx], pops[left_idx], left_n)
        + _bisect_centroids(xs[right_idx], ys[right_idx], pops[right_idx], right_n)
    )


def place_seeds_recursive_bisection(
    units: gpd.GeoDataFrame,
    n: int,
) -> list[Seed]:
    """Place ``n`` seeds via population-weighted recursive bisection.

    Recursively splits units into N equal-population regions by bisecting
    along the longer bounding-box axis at the population-weighted median.
    One seed is placed at each leaf region's population-weighted centroid.

    Deterministic: ties in coordinate value break by unit_id ascending;
    split axis chosen by bounding-box extent (x wins ties).  Left subtree
    always receives ``n // 2`` districts; right receives the remainder.
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if n > len(units):
        raise ValueError(f"n={n} exceeds number of units ({len(units)})")

    units_sorted = units.sort_values("unit_id", kind="mergesort").reset_index(drop=True)
    centroids = units_sorted.geometry.centroid
    xs = np.asarray(centroids.x, dtype=float)
    ys = np.asarray(centroids.y, dtype=float)
    pops = np.asarray(units_sorted["population"], dtype=float)

    centroids_list = _bisect_centroids(xs, ys, pops, n)

    return [
        Seed(district_id=d, x=float(cx), y=float(cy))
        for d, (cx, cy) in enumerate(centroids_list)
    ]


def place_seeds_angular_quantile(
    units: gpd.GeoDataFrame,
    n: int,
    *,
    rotation_offset: float = 0.0,
) -> list[Seed]:
    """Place ``n`` seeds at population-quantile angles on the same small circle.

    Computes the angle of each unit's centroid relative to the population-
    weighted centroid, then finds the N angles that divide the *cumulative
    angular population distribution* into N equal slices.  Seed ``d`` is
    placed at the midpoint angle of the ``d``-th slice.

    Seeds are placed on the same small circle as ``place_seeds`` (radius =
    0.1 % of the bounding-box diagonal), so the Voronoi structure is still
    dominated by the angular arrangement.  The difference is that angular
    spacing compresses into densely-populated sectors and expands over
    sparse ones, naturally adapting to polycentric or coastal geographies
    without any state-specific logic.

    ``rotation_offset`` sets the starting angle of the sweep (default 0 =
    due east), consistent with ``place_seeds``.  Tie-break for units at
    identical angles: ``unit_id`` ascending.
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if n > len(units):
        raise ValueError(f"n={n} exceeds number of units ({len(units)})")

    units_sorted = units.sort_values("unit_id", kind="mergesort").reset_index(drop=True)
    centroids = units_sorted.geometry.centroid
    xs = np.asarray(centroids.x, dtype=float)
    ys = np.asarray(centroids.y, dtype=float)
    pops = np.asarray(units_sorted["population"], dtype=float)

    total_pop = float(pops.sum())
    if total_pop > 0:
        center_x = float((xs * pops).sum() / total_pop)
        center_y = float((ys * pops).sum() / total_pop)
    else:
        center_x = float(xs.mean())
        center_y = float(ys.mean())

    minx, miny, maxx, maxy = units_sorted.total_bounds
    diag = float(np.hypot(maxx - minx, maxy - miny))
    radius = diag * 0.001

    # Compute angle of each unit relative to the population-weighted centroid,
    # shifted so that rotation_offset is the start of the sweep, in [0, 2π).
    raw_angles = np.arctan2(ys - center_y, xs - center_x)
    angles = (raw_angles - rotation_offset) % (2.0 * np.pi)

    # Sort by angle, with unit_id (already sorted) as tie-break.
    order = np.argsort(angles, kind="stable")
    sorted_angles = angles[order]
    sorted_pops = pops[order]

    # Cumulative population after each unit in angular order.
    cumulative = np.cumsum(sorted_pops)
    total = float(cumulative[-1]) if total_pop > 0 else float(len(units))

    seeds = []
    for d in range(n):
        # Target cumulative population at the midpoint of the d-th slice.
        target = (d + 0.5) * total / n

        # Find the index where cumulative population first reaches the target.
        idx = int(np.searchsorted(cumulative, target, side="left"))
        idx = min(idx, len(sorted_angles) - 1)

        seed_angle = float(sorted_angles[idx]) + rotation_offset
        seeds.append(Seed(
            district_id=d,
            x=center_x + radius * float(np.cos(seed_angle)),
            y=center_y + radius * float(np.sin(seed_angle)),
        ))

    return seeds
