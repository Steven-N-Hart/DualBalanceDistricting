"""Prepare Minnesota census-geography input for `dualbalance generate`.

Downloads the TIGER/Line 2020 shapefile for the requested geography (VTDs by
default), extracts it, and writes ``data/mn_<geography>.geojson`` with the
canonical column schema the CLI loader expects (``GEOID20``, ``population``,
``geometry``).

Population is **synthesized as uniform 1000 per unit** unless a path to a
prepared population CSV is supplied via ``--population-csv``. The CSV must
have columns ``GEOID20,population``. The 2020 PL 94-171 dataset is the
canonical source and either requires fixed-width parsing or a Census Data
API key (see [data/README.md](../data/README.md)).
"""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

from dualbalance.geography import Geography

# State FIPS code for Minnesota.
MN_FIPS = "27"


def _load_dotenv(path: Path) -> None:
    """Read ``KEY=value`` pairs from ``path`` into ``os.environ``.

    Lines starting with ``#`` and blank lines are skipped. Existing env-var
    values win over file values (so explicit shell exports still override).
    Quotes around values are stripped.
    """
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


URL_BY_GEOGRAPHY: dict[Geography, str] = {
    Geography.VTD: (
        "https://www2.census.gov/geo/tiger/TIGER2020PL/STATE/27_MINNESOTA/27/tl_2020_27_vtd20.zip"
    ),
    Geography.BLOCK: (
        "https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_27_tabblock20.zip"
    ),
    Geography.BLOCK_GROUP: ("https://www2.census.gov/geo/tiger/TIGER2020/BG/tl_2020_27_bg20.zip"),
}


def _download_and_extract(url: str, dest_dir: Path) -> Path:
    """Download a TIGER zip and extract it. Returns the .shp path inside it."""
    print(f"  downloading {url}")
    with urllib.request.urlopen(url, timeout=120) as resp:
        zip_bytes = resp.read()
    print(f"  extracted {len(zip_bytes):,} bytes")
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        zf.extractall(dest_dir)
    shp_files = list(dest_dir.glob("*.shp"))
    if not shp_files:
        raise RuntimeError(f"no .shp found inside {url}")
    return shp_files[0]


_API_GEO_LEVEL: dict[Geography, str] = {
    Geography.VTD: "voting district",
    Geography.BLOCK: "block",
    Geography.BLOCK_GROUP: "block group",
}


def _fetch_population_via_api(
    geography: Geography, state_fips: str, api_key: str
) -> dict[str, int]:
    """Query the 2020 PL 94-171 dataset for total population per unit.

    Returns ``{GEOID: population}`` keyed by the full census GEOID string
    (state + county + unit subcode), matching the TIGER GEOID20 field.
    """
    level = _API_GEO_LEVEL[geography]
    params = {
        "get": "P1_001N",
        "for": f"{level}:*",
        "in": f"state:{state_fips} county:*",
        "key": api_key,
    }
    query = urllib.parse.urlencode(params).replace("+", "%20")
    url = f"https://api.census.gov/data/2020/dec/pl?{query}"
    print("  fetching population from Census Data API")
    with urllib.request.urlopen(url, timeout=120) as resp:
        body = resp.read()
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        snippet = body.decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"Census API returned non-JSON: {snippet}") from exc

    header = data[0]
    pop_idx = header.index("P1_001N")
    state_idx = header.index("state")
    county_idx = header.index("county")
    # The unit subcode column name matches `level` with spaces.
    unit_col = level
    unit_idx = header.index(unit_col)

    result: dict[str, int] = {}
    for row in data[1:]:
        geoid = row[state_idx] + row[county_idx] + row[unit_idx]
        result[geoid] = int(row[pop_idx])
    return result


def _attach_population(
    gdf: gpd.GeoDataFrame,
    *,
    geography: Geography,
    id_column: str,
    csv_path: Path | None,
    api_key: str | None,
) -> gpd.GeoDataFrame:
    if csv_path is not None:
        pops = pd.read_csv(csv_path, dtype={id_column: str})
        if id_column not in pops.columns or "population" not in pops.columns:
            raise ValueError(f"{csv_path!s}: must have columns {id_column} and population")
        merged = gdf.merge(pops[[id_column, "population"]], on=id_column, how="left")
        missing = int(merged["population"].isna().sum())
        if missing:
            raise ValueError(f"{csv_path!s}: missing population for {missing} unit(s)")
        merged["population"] = merged["population"].astype(int)
        return merged

    if api_key:
        try:
            pops_by_geoid = _fetch_population_via_api(geography, MN_FIPS, api_key)
        except RuntimeError as exc:
            print(
                f"  WARNING: Census API call failed ({exc}); "
                "falling back to synthetic uniform population=1000."
            )
            print("  If you just signed up, check your email for the activation link.")
            gdf = gdf.copy()
            gdf["population"] = 1000
            return gdf
        merged = gdf.copy()
        merged["population"] = merged[id_column].map(pops_by_geoid)
        missing = int(merged["population"].isna().sum())
        if missing:
            sample = merged.loc[merged["population"].isna(), id_column].head(5).tolist()
            raise RuntimeError(
                f"Census API returned no population for {missing} unit(s); example IDs: {sample}"
            )
        merged["population"] = merged["population"].astype(int)
        print(
            f"  joined real population for {len(merged):,} units "
            f"(total: {int(merged['population'].sum()):,})"
        )
        return merged

    print("  no --population-csv or CENSUS_API_KEY -- synthesizing uniform pop=1000")
    gdf = gdf.copy()
    gdf["population"] = 1000
    return gdf


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=("Download Minnesota TIGER/Line geometry and emit a CLI-ready GeoJSON.")
    )
    parser.add_argument(
        "--geography",
        default="vtd",
        choices=[g.cli_name for g in Geography],
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output path (default: data/mn_<geography>.geojson).",
    )
    parser.add_argument(
        "--population-csv",
        type=Path,
        dest="population_csv",
        help="Optional path to a CSV with GEOID20,population.",
    )
    args = parser.parse_args(argv)

    geography = Geography.from_cli_name(args.geography)
    url = URL_BY_GEOGRAPHY[geography]
    repo_root = Path(__file__).resolve().parent.parent
    out = args.out or (repo_root / "data" / f"mn_{geography.cli_name}.geojson")

    # Load .env (if present) before reading CENSUS_API_KEY so the user can
    # set the key in a gitignored .env file at the repo root.
    _load_dotenv(repo_root / ".env")
    api_key = os.environ.get("CENSUS_API_KEY")

    print(f"preparing MN {geography.label}")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        shp = _download_and_extract(url, tmp_dir)
        gdf = gpd.read_file(shp)

    # Canonicalize the ID column. VTDs and blocks use GEOID20; block groups
    # use GEOID. The CLI default for each is set in geography.py.
    expected_id = geography.default_id_column
    if expected_id not in gdf.columns:
        raise RuntimeError(
            f"shapefile missing expected ID column {expected_id!r}; have: {list(gdf.columns)}"
        )
    gdf = gdf[[expected_id, "geometry"]].copy()

    gdf = _attach_population(
        gdf,
        geography=geography,
        id_column=expected_id,
        csv_path=args.population_csv,
        api_key=api_key,
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    gdf[[expected_id, "population", "geometry"]].to_file(out, driver="GeoJSON")
    print(f"wrote {len(gdf):,} {geography.cli_name} units to {out}")
    shutil.rmtree(out.with_suffix(""), ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
