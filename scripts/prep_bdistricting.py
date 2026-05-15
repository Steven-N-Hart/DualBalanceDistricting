"""Ingest Brian Olson's BDistricting maps as a per-state plan baseline.

Olson publishes block-level CSVs at https://bdistricting.com/2020/<ST>_Congress/
(BLOCKID,district). The Census 2020 Block Assignment File (BAF) maps
BLOCKID -> VTDID. Joining these gives a VTD-level assignment: each VTD is
assigned to the BDistricting district that owns the plurality of its
constituent blocks. Tiebreaker: lowest district id.

Output: data/<state-lower>_bdistricting.geojson (Plan-format, scorable by
``dualbalance score``).

Usage:
  python scripts/prep_bdistricting.py --state MN
"""

from __future__ import annotations

import argparse
import io
import sys
import tempfile
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

import geopandas as gpd
import pandas as pd

from dualbalance.states import STATE_INFO

REPO_ROOT = Path(__file__).resolve().parent.parent


def _download_zip(url: str, dest_dir: Path) -> None:
    print(f"  downloading {url}")
    with urllib.request.urlopen(url, timeout=180) as resp:
        zip_bytes = resp.read()
    print(f"  extracted {len(zip_bytes):,} bytes")
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        zf.extractall(dest_dir)


def _fetch_bdistricting_blocks(state_postal: str, tmp_dir: Path) -> pd.DataFrame:
    """Return DataFrame with columns BLOCKID (str) and bd_district (int)."""
    url = f"https://bdistricting.com/2020/{state_postal}_Congress/solution.zip"
    _download_zip(url, tmp_dir / "bdistricting")
    csv_paths = list((tmp_dir / "bdistricting").glob("*.csv"))
    if not csv_paths:
        raise RuntimeError(f"no CSV inside BDistricting zip for {state_postal}")
    df = pd.read_csv(
        csv_paths[0], header=None, names=["BLOCKID", "bd_district"], dtype={"BLOCKID": str}
    )
    df["bd_district"] = df["bd_district"].astype(int)
    return df


def _fetch_block_to_vtd(state_postal: str, state_fips: str, tmp_dir: Path) -> pd.DataFrame:
    """Return DataFrame with columns BLOCKID (str) and GEOID20 (str: VTD)."""
    url = (
        f"https://www2.census.gov/geo/docs/maps-data/data/baf2020/"
        f"BlockAssign_ST{state_fips}_{state_postal}.zip"
    )
    _download_zip(url, tmp_dir / "baf")
    vtd_file = tmp_dir / "baf" / f"BlockAssign_ST{state_fips}_{state_postal}_VTD.txt"
    df = pd.read_csv(
        vtd_file,
        sep="|",
        dtype={"BLOCKID": str, "COUNTYFP": str, "DISTRICT": str},
    )
    # Build VTD GEOID20 = state + county + district-code (matches TIGER GEOID20).
    df["GEOID20"] = state_fips + df["COUNTYFP"].str.zfill(3) + df["DISTRICT"].str.zfill(6)
    return df[["BLOCKID", "GEOID20"]]


def _assign_vtds_to_bdistricting(
    bd_blocks: pd.DataFrame, block_to_vtd: pd.DataFrame
) -> pd.DataFrame:
    """For each VTD, assign the BDistricting district with most blocks.

    Tiebreaker: lowest district id.
    """
    merged = bd_blocks.merge(block_to_vtd, on="BLOCKID", how="inner")
    if len(merged) == 0:
        raise RuntimeError("no overlap between BDistricting blocks and Census BAF blocks")
    print(f"  matched {len(merged):,} blocks across BDistricting and Census BAF")

    rows = []
    for vtd_id, group in merged.groupby("GEOID20"):
        counts = Counter(group["bd_district"])
        # Plurality with lowest-district-id tiebreaker.
        best_district = min(counts.keys(), key=lambda d: (-counts[d], d))
        rows.append({"GEOID20": vtd_id, "bd_district": int(best_district)})
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state",
        required=True,
        choices=sorted(STATE_INFO.keys()),
    )
    parser.add_argument(
        "--units",
        type=Path,
        help="Override path to the units geojson (default: data/<state-lower>_vtd.geojson).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output plan path (default: data/<state-lower>_bdistricting.geojson).",
    )
    args = parser.parse_args(argv)

    state = args.state.upper()
    info = STATE_INFO[state]
    state_fips = info["fips"]

    units_path = args.units or (REPO_ROOT / "data" / f"{state.lower()}_vtd.geojson")
    out_path = args.out or (REPO_ROOT / "data" / f"{state.lower()}_bdistricting.geojson")

    print(f"preparing {state} BDistricting plan")
    if not units_path.is_file():
        raise SystemExit(
            f"units file not found: {units_path}\n"
            f"Run `python scripts/prep_state_units.py --state {state}` first."
        )

    print(f"  loading units: {units_path}")
    units = gpd.read_file(units_path)
    if "GEOID20" not in units.columns:
        raise SystemExit("units geojson missing GEOID20 column")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        bd_blocks = _fetch_bdistricting_blocks(state, tmp_dir)
        block_to_vtd = _fetch_block_to_vtd(state, state_fips, tmp_dir)

    vtd_assign = _assign_vtds_to_bdistricting(bd_blocks, block_to_vtd)
    print(f"  assigned {len(vtd_assign):,} VTDs to BDistricting districts")

    # Merge to inherit VTD geometry.
    merged = units[["GEOID20", "geometry"]].merge(vtd_assign, on="GEOID20", how="left")
    missing = int(merged["bd_district"].isna().sum())
    if missing:
        print(f"  WARNING: {missing} VTDs had no blocks in BDistricting CSV; dropping")
        merged = merged.dropna(subset=["bd_district"])
    merged["bd_district"] = merged["bd_district"].astype(int)

    # Write as Plan-format geojson (unit_id + district_id 0-indexed + geometry).
    # BDistricting districts are 0-indexed per the sample (0..N-1).
    plan_gdf = merged.rename(columns={"GEOID20": "unit_id", "bd_district": "district_id"})
    plan_gdf = plan_gdf[["unit_id", "district_id", "geometry"]].sort_values("unit_id")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    plan_gdf.to_file(out_path, driver="GeoJSON")
    print(
        f"wrote BDistricting plan for {len(plan_gdf):,} VTDs "
        f"({plan_gdf['district_id'].nunique()} districts) to {out_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
