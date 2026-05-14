"""I/O for census-geography unit data and output artifacts.

The loader is geography-agnostic: it requires only an ID column, a population
column, and a geometry. Area is computed from the geometry after reprojection
to an equal-area CRS so the cost-function area-penalty term is meaningful.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import geopandas as gpd

from dualbalance.types import Plan

# NAD83 / Conus Albers Equal Area. Suitable for the contiguous U.S.; for AK,
# HI, or territories a different equal-area projection would be needed, but
# that is out of scope for the PoC.
EQUAL_AREA_CRS = "EPSG:5070"


def load_units(
    path: str | Path,
    *,
    id_column: str = "GEOID",
    pop_column: str = "population",
) -> gpd.GeoDataFrame:
    """Load atomic units (VTDs, blocks, or block groups) as a GeoDataFrame.

    The input file (anything Fiona/pyogrio can read: GeoJSON, Shapefile,
    GeoPackage, ...) must carry the named ID and population columns plus a
    geometry. The result is reprojected to ``EQUAL_AREA_CRS`` and exposes
    canonical columns ``unit_id``, ``population``, ``area``, ``geometry``.
    """
    gdf = gpd.read_file(path)
    if id_column not in gdf.columns:
        raise ValueError(f"missing ID column {id_column!r}; available: {list(gdf.columns)}")
    if pop_column not in gdf.columns:
        raise ValueError(
            f"missing population column {pop_column!r}; available: {list(gdf.columns)}"
        )
    if gdf.crs is None:
        raise ValueError(f"input {path!s} has no CRS; cannot project to equal-area")

    gdf = gdf.to_crs(EQUAL_AREA_CRS)
    gdf = gdf.rename(columns={id_column: "unit_id", pop_column: "population"})
    gdf["area"] = gdf.geometry.area
    return gdf[["unit_id", "population", "area", "geometry"]]


def write_metrics(metrics: dict[str, Any], path: str | Path) -> None:
    """Write a metrics dict to JSON with sorted keys (deterministic output)."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")


def write_plan(plan: Plan, units: gpd.GeoDataFrame, path: str | Path) -> None:
    """Write a plan as a GeoJSON with one feature per atomic unit.

    Output rows are sorted by ``unit_id`` ascending so the file is
    reproducible byte-for-byte across runs with identical inputs.
    """
    indexed = units.set_index("unit_id")
    rows = sorted(plan.assignment.items())
    sorted_uids = [u for u, _ in rows]
    sorted_dids = [d for _, d in rows]
    sub = indexed.loc[sorted_uids].reset_index()
    sub["district_id"] = sorted_dids
    out_gdf = sub[["unit_id", "district_id", "population", "area", "geometry"]]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()  # GeoJSON driver appends otherwise.
    out_gdf.to_file(out, driver="GeoJSON")


def load_plan(path: str | Path, *, geography: str = "unknown") -> Plan:
    """Read a previously-written plan from a GeoJSON.

    Requires the file's features to carry ``unit_id`` and ``district_id``
    properties (as written by :func:`write_plan`).
    """
    gdf = gpd.read_file(path)
    for col in ("unit_id", "district_id"):
        if col not in gdf.columns:
            raise ValueError(
                f"plan file missing required column {col!r}; available: {list(gdf.columns)}"
            )
    assignment = {
        str(uid): int(did) for uid, did in zip(gdf["unit_id"], gdf["district_id"], strict=True)
    }
    n_districts = max(assignment.values()) + 1 if assignment else 0
    return Plan(
        assignment=assignment,
        n_districts=n_districts,
        geography=geography,
    )


def load_state_populations(path: str | Path) -> dict[str, int]:
    """Read state populations from a CSV (``state,population`` header) or JSON.

    JSON files must be a mapping ``{state: population}``. CSV files must have
    columns named ``state`` and ``population`` (case-sensitive).
    """
    p = Path(path)
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{p!s}: expected JSON object mapping state -> population")
        return {str(k): int(v) for k, v in data.items()}
    with p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if (
            reader.fieldnames is None
            or "state" not in reader.fieldnames
            or "population" not in reader.fieldnames
        ):
            raise ValueError(f"{p!s}: CSV must have header columns 'state' and 'population'")
        return {row["state"]: int(row["population"]) for row in reader}
