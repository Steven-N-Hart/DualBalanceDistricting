"""Fetch Minnesota's enacted 119th-Congress districts and join them to VTDs.

Downloads the TIGER/Line shapefile for the current MN congressional plan,
performs a centroid-in-polygon spatial join against the prepared VTD file,
and writes the result as a plan-compatible GeoJSON + metrics JSON so it
can be compared against DualBalance output with the same scoring code.

Output:
- ``out/mn_enacted/map.geojson``  -- one feature per VTD with ``district_id``
- ``out/mn_enacted/metrics.json`` -- DualBalance Score + primary metrics

After running this, both `dualbalance score` and the comparison plotter
treat the enacted plan exactly like any DualBalance-generated plan.
"""

from __future__ import annotations

import argparse
import io
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd

from dualbalance.io import EQUAL_AREA_CRS, load_units, write_metrics, write_plan
from dualbalance.scoring import score_plan
from dualbalance.types import Plan

MN_FIPS = "27"
CD_SHAPEFILE_URL = "https://www2.census.gov/geo/tiger/TIGER2024/CD/tl_2024_27_cd119.zip"


def _download_cd_shapefile(dest_dir: Path) -> Path:
    print(f"  downloading {CD_SHAPEFILE_URL}")
    with urllib.request.urlopen(CD_SHAPEFILE_URL, timeout=120) as r:
        zip_bytes = r.read()
    print(f"  extracted {len(zip_bytes):,} bytes")
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        zf.extractall(dest_dir)
    shps = list(dest_dir.glob("*.shp"))
    if not shps:
        raise RuntimeError("no .shp inside CD zip")
    return shps[0]


def _enacted_assignment(vtds: gpd.GeoDataFrame, cds: gpd.GeoDataFrame) -> dict[str, int]:
    """Map each VTD's GEOID20 to its enacted CD's 0-indexed id.

    Strategy: VTD centroid sjoin within CD polygons; fall back to nearest CD
    for any VTD whose centroid doesn't land strictly inside (boundary
    precision artifact).
    """
    cd_col = "CD119FP"
    if cd_col not in cds.columns:
        # Different shapefiles use slightly different column names.
        for candidate in ("CDFP", "GEOID", "NAMELSAD"):
            if candidate in cds.columns:
                cd_col = candidate
                break
    cds = cds.to_crs(EQUAL_AREA_CRS)[[cd_col, "geometry"]].copy()
    cds = cds.rename(columns={cd_col: "cd_code"})
    cds["district_id"] = cds["cd_code"].astype(int) - 1

    centroids = vtds.copy()
    centroids["geometry"] = centroids.geometry.centroid

    joined = gpd.sjoin(centroids, cds, how="left", predicate="within")
    # Handle unmatched (boundary cases) via nearest CD.
    unmatched_mask = joined["district_id"].isna()
    n_unmatched = int(unmatched_mask.sum())
    if n_unmatched:
        print(f"  {n_unmatched} VTD(s) centroid not strictly within any CD; using nearest CD")
        joined = joined.drop(columns=["index_right", "district_id", "cd_code"])
        joined = gpd.sjoin_nearest(centroids, cds, how="left")
    assignment = {
        str(uid): int(d) for uid, d in zip(joined["unit_id"], joined["district_id"], strict=True)
    }
    return assignment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vtds",
        type=Path,
        default=Path("data/mn_vtd.geojson"),
        help="Path to prepared MN VTD GeoJSON (default: data/mn_vtd.geojson).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("out/mn_enacted"),
        help="Output directory (default: out/mn_enacted).",
    )
    args = parser.parse_args(argv)

    units = load_units(args.vtds, id_column="GEOID20", pop_column="population")
    print(f"loaded {len(units)} VTDs from {args.vtds}")

    with tempfile.TemporaryDirectory() as tmp:
        cd_shp = _download_cd_shapefile(Path(tmp))
        cds = gpd.read_file(cd_shp)
    print(f"loaded {len(cds)} congressional district polygons")

    assignment = _enacted_assignment(units, cds)
    plan = Plan(
        assignment=assignment,
        n_districts=len(set(assignment.values())),
        geography="vtd",
        metadata={"source": "TIGER 2024 CD119 (MN 119th Congress, enacted)"},
    )
    metrics = score_plan(plan, units)

    args.out.mkdir(parents=True, exist_ok=True)
    write_plan(plan, units, args.out / "map.geojson")
    write_metrics(metrics, args.out / "metrics.json")
    print(
        f"wrote enacted-plan map.geojson + metrics.json to {args.out}; "
        f"DualBalance Score = {metrics['dualbalance_score']:.4f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
