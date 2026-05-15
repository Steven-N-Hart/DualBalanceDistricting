"""Prepare per-state census-geography input for `dualbalance generate`.

Generalizes the earlier ``prep_mn_units.py`` to any U.S. state. For a
given state (two-letter postal code) the script:

1. Downloads the TIGER/Line 2020 shapefile for the requested geography.
2. Joins Census PL 94-171 (population + race VAP) via the Census Data API.
3. Joins 2020 presidential two-party votes from dra2020/vtd_data.
4. Joins enacted 119th-Congress district assignments via TIGER cd119 +
   a representative-point spatial join.
5. Writes two GeoJSON files:
   - ``data/<state>_vtd.geojson``       (units, with all diagnostic columns)
   - ``data/<state>_enacted.geojson``  (plan: unit_id + district_id +
                                         geometry, scorable directly by
                                         ``dualbalance score``)

The core algorithm reads only the first file's geometry + population.
The remaining columns are diagnostic and used only by the scoring harness.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

from dualbalance.geography import Geography
from dualbalance.io import EQUAL_AREA_CRS

# Per-state metadata: FIPS code, TIGER state name (used in VTD URL path),
# and apportioned 119th-Congress seat count.
STATE_INFO: dict[str, dict[str, Any]] = {
    "MN": {"fips": "27", "tiger_name": "MINNESOTA", "n_seats": 8},
    "IA": {"fips": "19", "tiger_name": "IOWA", "n_seats": 4},
    "MA": {"fips": "25", "tiger_name": "MASSACHUSETTS", "n_seats": 9},
    "TX": {"fips": "48", "tiger_name": "TEXAS", "n_seats": 38},
}


def _load_dotenv(path: Path) -> None:
    """Read ``KEY=value`` pairs from ``path`` into ``os.environ``."""
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


def _download_and_extract(url: str, dest_dir: Path) -> Path:
    """Download a TIGER zip and extract it. Returns the .shp path inside it."""
    print(f"  downloading {url}")
    with urllib.request.urlopen(url, timeout=180) as resp:
        zip_bytes = resp.read()
    print(f"  extracted {len(zip_bytes):,} bytes")
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        zf.extractall(dest_dir)
    shp_files = list(dest_dir.glob("*.shp"))
    if not shp_files:
        raise RuntimeError(f"no .shp found inside {url}")
    return shp_files[0]


def _tiger_vtd_url(fips: str, tiger_name: str) -> str:
    return (
        f"https://www2.census.gov/geo/tiger/TIGER2020PL/STATE/"
        f"{fips}_{tiger_name}/{fips}/tl_2020_{fips}_vtd20.zip"
    )


def _tiger_block_url(fips: str) -> str:
    return f"https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_{fips}_tabblock20.zip"


def _tiger_bg_url(fips: str) -> str:
    return f"https://www2.census.gov/geo/tiger/TIGER2020/BG/tl_2020_{fips}_bg20.zip"


def _tiger_url_for(geography: Geography, fips: str, tiger_name: str) -> str:
    if geography == Geography.VTD:
        return _tiger_vtd_url(fips, tiger_name)
    if geography == Geography.BLOCK:
        return _tiger_block_url(fips)
    if geography == Geography.BLOCK_GROUP:
        return _tiger_bg_url(fips)
    raise ValueError(f"unsupported geography {geography}")


_API_GEO_LEVEL: dict[Geography, str] = {
    Geography.VTD: "voting district",
    Geography.BLOCK: "block",
    Geography.BLOCK_GROUP: "block group",
}


_PL_VARIABLES: dict[str, str] = {
    "population": "P1_001N",
    "vap_total": "P3_001N",
    "vap_nhwhite": "P4_005N",
    "vap_black": "P3_004N",
    "vap_aian": "P3_005N",
    "vap_asian": "P3_006N",
    "vap_hispanic": "P4_002N",
}


def _fetch_pl_via_api(geography: Geography, state_fips: str, api_key: str) -> pd.DataFrame:
    """Query the 2020 PL 94-171 dataset for total pop + race VAP per unit."""
    level = _API_GEO_LEVEL[geography]
    params = {
        "get": ",".join(_PL_VARIABLES.values()),
        "for": f"{level}:*",
        "in": f"state:{state_fips} county:*",
        "key": api_key,
    }
    query = urllib.parse.urlencode(params).replace("+", "%20")
    url = f"https://api.census.gov/data/2020/dec/pl?{query}"
    print(f"  fetching {len(_PL_VARIABLES)} PL 94-171 variables from Census Data API")
    with urllib.request.urlopen(url, timeout=180) as resp:
        body = resp.read()
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        snippet = body.decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"Census API returned non-JSON: {snippet}") from exc

    header = data[0]
    state_idx = header.index("state")
    county_idx = header.index("county")
    unit_idx = header.index(level)
    var_idx = {canonical: header.index(code) for canonical, code in _PL_VARIABLES.items()}

    rows = []
    for row in data[1:]:
        geoid = row[state_idx] + row[county_idx] + row[unit_idx]
        record: dict[str, Any] = {"GEOID": geoid}
        for canonical, idx in var_idx.items():
            record[canonical] = int(row[idx])
        rows.append(record)
    return pd.DataFrame(rows)


def _resolve_dra_election_url(state_postal: str) -> str:
    """Find the highest-version Election_Data zip for this state in dra2020/vtd_data."""
    api_url = f"https://api.github.com/repos/dra2020/vtd_data/contents/2020_VTD/{state_postal}"
    print(f"  resolving dra2020 election version for {state_postal}")
    with urllib.request.urlopen(api_url, timeout=60) as resp:
        files = json.load(resp)
    prefix = f"Election_Data_{state_postal}.v"
    candidates = [f for f in files if f["name"].startswith(prefix) and f["name"].endswith(".zip")]
    if not candidates:
        raise RuntimeError(f"no Election_Data files in dra2020/vtd_data for {state_postal}")
    latest = sorted(candidates, key=lambda f: f["name"])[-1]
    return latest["download_url"]


def _fetch_dra_elections(url: str) -> pd.DataFrame:
    """Download a dra2020 state election ZIP and return 2020 presidential."""
    print(f"  downloading election data from {url}")
    with urllib.request.urlopen(url, timeout=180) as resp:
        zip_bytes = resp.read()
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise RuntimeError(f"no CSV inside {url}")
        with zf.open(csv_names[0]) as f:
            df = pd.read_csv(f, dtype={"GEOID20": str})
    need = {"GEOID20", "E_20_PRES_Rep", "E_20_PRES_Dem"}
    missing = need - set(df.columns)
    if missing:
        raise RuntimeError(f"dra2020 CSV missing expected columns: {sorted(missing)}")
    return (
        df[["GEOID20", "E_20_PRES_Rep", "E_20_PRES_Dem"]]
        .rename(columns={"E_20_PRES_Rep": "votes_R", "E_20_PRES_Dem": "votes_D"})
        .astype({"votes_R": int, "votes_D": int})
    )


def _attach_demographics(
    gdf: gpd.GeoDataFrame,
    *,
    geography: Geography,
    state_fips: str,
    id_column: str,
    csv_path: Path | None,
    api_key: str | None,
) -> gpd.GeoDataFrame:
    """Join total population + race VAP onto ``gdf``."""
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
            pl_df = _fetch_pl_via_api(geography, state_fips, api_key)
        except RuntimeError as exc:
            print(
                f"  WARNING: Census API call failed ({exc}); "
                "falling back to synthetic uniform population=1000 (no race data)."
            )
            gdf = gdf.copy()
            gdf["population"] = 1000
            return gdf
        merged = gdf.merge(pl_df, left_on=id_column, right_on="GEOID", how="left").drop(
            columns=["GEOID"]
        )
        missing = int(merged["population"].isna().sum())
        if missing:
            sample = merged.loc[merged["population"].isna(), id_column].head(5).tolist()
            raise RuntimeError(
                f"Census API returned no data for {missing} unit(s); example IDs: {sample}"
            )
        for col in _PL_VARIABLES:
            merged[col] = merged[col].astype(int)
        print(
            f"  joined demographics for {len(merged):,} units "
            f"(pop {int(merged['population'].sum()):,}; "
            f"VAP {int(merged['vap_total'].sum()):,})"
        )
        return merged

    print("  no --population-csv or CENSUS_API_KEY -- synthesizing uniform pop=1000")
    gdf = gdf.copy()
    gdf["population"] = 1000
    return gdf


def _attach_elections(
    gdf: gpd.GeoDataFrame,
    *,
    id_column: str,
    csv_path: Path | None,
    state_postal: str,
) -> gpd.GeoDataFrame:
    """Join 2020 presidential vote totals onto ``gdf``."""
    if csv_path is not None:
        try:
            edf = pd.read_csv(csv_path, dtype={id_column: str})
        except OSError as exc:
            print(f"  WARNING: failed to read --election-csv ({exc}); skipping partisan join")
            return gdf
        need = {id_column, "votes_R", "votes_D"}
        missing = need - set(edf.columns)
        if missing:
            print(
                f"  WARNING: --election-csv missing columns {sorted(missing)}; "
                "skipping partisan join"
            )
            return gdf
        edf = edf[[id_column, "votes_R", "votes_D"]]
    else:
        try:
            url = _resolve_dra_election_url(state_postal)
            edf = _fetch_dra_elections(url)
            edf = edf.rename(columns={"GEOID20": id_column})
        except (urllib.error.URLError, RuntimeError) as exc:
            print(f"  WARNING: failed to fetch partisan data ({exc}); skipping partisan join.")
            return gdf

    merged = gdf.merge(edf, on=id_column, how="left")
    n_missing = int(merged["votes_R"].isna().sum())
    if n_missing:
        print(f"  NOTE: {n_missing} units missing election data; filled with 0 votes")
        merged[["votes_R", "votes_D"]] = merged[["votes_R", "votes_D"]].fillna(0)
    merged["votes_R"] = merged["votes_R"].astype(int)
    merged["votes_D"] = merged["votes_D"].astype(int)
    print(
        f"  joined 2020 presidential votes for {len(merged):,} units "
        f"(R {int(merged['votes_R'].sum()):,}; D {int(merged['votes_D'].sum()):,})"
    )
    return merged


def _join_enacted_cd(
    gdf: gpd.GeoDataFrame,
    *,
    state_fips: str,
    id_column: str,
    tmp_dir: Path,
) -> gpd.GeoDataFrame:
    """Spatial-join the enacted 119th-Congress districts onto each VTD.

    Uses representative points (guaranteed inside the polygon) for the
    point-in-polygon join, which is deterministic and avoids the
    straddling-VTD problem. Any unmatched units (rare, only when a
    point lands exactly on a CD boundary) fall back to the
    smallest-CD-number tiebreaker.

    Returns ``gdf`` with a new integer column ``cd119_district`` (1-indexed
    to match TIGER) or, if the spatial join fails entirely, ``gdf`` unchanged.
    """
    cd_url = f"https://www2.census.gov/geo/tiger/TIGER2024/CD/tl_2024_{state_fips}_cd119.zip"
    try:
        cd_shp = _download_and_extract(cd_url, tmp_dir / "cd119")
    except urllib.error.URLError as exc:
        print(f"  WARNING: failed to fetch enacted CD geometry ({exc}); skipping enacted-plan join")
        return gdf

    cd_gdf = gpd.read_file(cd_shp)
    cd_col_candidates = ["CD119FP", "CDFP", "CD118FP", "CD117FP"]
    cd_col = next((c for c in cd_col_candidates if c in cd_gdf.columns), None)
    if cd_col is None:
        raise RuntimeError(
            f"unexpected CD shapefile columns: {list(cd_gdf.columns)} "
            f"(looked for one of {cd_col_candidates})"
        )
    cd_gdf = cd_gdf[[cd_col, "geometry"]].rename(columns={cd_col: "cd119_district"})
    cd_gdf["cd119_district"] = cd_gdf["cd119_district"].astype(int)
    cd_gdf = cd_gdf.to_crs(EQUAL_AREA_CRS)

    # Project units to the same CRS, then use representative points for the join.
    units_proj = gdf.to_crs(EQUAL_AREA_CRS)
    units_pts = units_proj[[id_column]].copy()
    units_pts["geometry"] = units_proj.geometry.representative_point()
    units_pts = gpd.GeoDataFrame(units_pts, geometry="geometry", crs=EQUAL_AREA_CRS)

    joined = gpd.sjoin(units_pts, cd_gdf, how="left", predicate="within")
    # On the rare exact-boundary case sjoin can return duplicate rows; keep
    # the lowest CD number for deterministic resolution.
    joined = joined.sort_values(["cd119_district", id_column]).drop_duplicates(
        id_column, keep="first"
    )[[id_column, "cd119_district"]]

    n_missing = int(joined["cd119_district"].isna().sum())
    if n_missing:
        # Fallback: nearest-CD-by-centroid for any missed units.
        print(f"  NOTE: {n_missing} VTDs not matched via point-in-polygon; using nearest CD")
        missing_ids = set(joined.loc[joined["cd119_district"].isna(), id_column])
        missing_units = units_proj[units_proj[id_column].isin(missing_ids)].copy()
        missing_units["geometry"] = missing_units.geometry.centroid
        nearest = gpd.sjoin_nearest(missing_units[[id_column, "geometry"]], cd_gdf, how="left")
        fallback = nearest[[id_column, "cd119_district"]].drop_duplicates(id_column)
        joined = pd.concat(
            [
                joined[~joined["cd119_district"].isna()],
                fallback,
            ],
            ignore_index=True,
        )

    joined["cd119_district"] = joined["cd119_district"].astype(int)
    out = gdf.merge(joined, on=id_column, how="left")
    n_districts = int(out["cd119_district"].nunique())
    print(f"  joined enacted 119th-Congress CDs for {len(out):,} units ({n_districts} districts)")
    return out


def _write_enacted_plan(
    gdf: gpd.GeoDataFrame,
    *,
    id_column: str,
    out_path: Path,
) -> None:
    """Write the enacted plan as a Plan-format GeoJSON (unit_id + district_id)."""
    plan_gdf = gdf[[id_column, "cd119_district", "geometry"]].copy()
    plan_gdf = plan_gdf.rename(columns={id_column: "unit_id"})
    # PRISM districts are 0-indexed; TIGER CDs are 1-indexed. Match PRISM.
    plan_gdf["district_id"] = (plan_gdf["cd119_district"].astype(int) - 1).astype(int)
    plan_gdf = plan_gdf[["unit_id", "district_id", "geometry"]].sort_values("unit_id")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    plan_gdf.to_file(out_path, driver="GeoJSON")
    print(f"  wrote enacted plan to {out_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download per-state TIGER/Line geometry, demographics, partisan returns, "
            "and the enacted 119th-Congress plan. Emits both a units geojson and an "
            "enacted-plan geojson."
        )
    )
    parser.add_argument(
        "--state",
        required=True,
        choices=sorted(STATE_INFO.keys()),
        help="Two-letter postal code for a supported state.",
    )
    parser.add_argument(
        "--geography",
        default="vtd",
        choices=[g.cli_name for g in Geography],
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Units output path (default: data/<state-lower>_<geography>.geojson).",
    )
    parser.add_argument(
        "--enacted-out",
        type=Path,
        dest="enacted_out",
        help="Enacted-plan output path (default: data/<state-lower>_enacted.geojson).",
    )
    parser.add_argument(
        "--population-csv",
        type=Path,
        dest="population_csv",
        help="Optional path to a CSV with <id_column>,population.",
    )
    parser.add_argument(
        "--election-csv",
        type=Path,
        dest="election_csv",
        help="Optional CSV with <id_column>,votes_R,votes_D. "
        "Overrides the dra2020/vtd_data auto-fetch.",
    )
    parser.add_argument(
        "--no-elections",
        dest="no_elections",
        action="store_true",
        help="Skip partisan join (no votes_R / votes_D columns).",
    )
    parser.add_argument(
        "--no-enacted",
        dest="no_enacted",
        action="store_true",
        help="Skip enacted-plan join (no cd119_district column, no enacted-plan geojson).",
    )
    args = parser.parse_args(argv)

    state = args.state.upper()
    info = STATE_INFO[state]
    state_fips: str = info["fips"]
    tiger_name: str = info["tiger_name"]

    geography = Geography.from_cli_name(args.geography)
    url = _tiger_url_for(geography, state_fips, tiger_name)

    repo_root = Path(__file__).resolve().parent.parent
    out = args.out or (repo_root / "data" / f"{state.lower()}_{geography.cli_name}.geojson")
    enacted_out = args.enacted_out or (repo_root / "data" / f"{state.lower()}_enacted.geojson")

    _load_dotenv(repo_root / ".env")
    api_key = os.environ.get("CENSUS_API_KEY")

    print(f"preparing {state} {geography.label}")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        shp = _download_and_extract(url, tmp_dir)
        gdf = gpd.read_file(shp)

        expected_id = geography.default_id_column
        if expected_id not in gdf.columns:
            raise RuntimeError(
                f"shapefile missing expected ID column {expected_id!r}; have: {list(gdf.columns)}"
            )
        gdf = gdf[[expected_id, "geometry"]].copy()

        gdf = _attach_demographics(
            gdf,
            geography=geography,
            state_fips=state_fips,
            id_column=expected_id,
            csv_path=args.population_csv,
            api_key=api_key,
        )

        if not args.no_elections:
            gdf = _attach_elections(
                gdf,
                id_column=expected_id,
                csv_path=args.election_csv,
                state_postal=state,
            )

        if not args.no_enacted:
            gdf = _join_enacted_cd(
                gdf,
                state_fips=state_fips,
                id_column=expected_id,
                tmp_dir=tmp_dir,
            )

    # County FIPS = first 5 chars of any Census GEOID (state[2] + county[3]).
    gdf["county"] = gdf[expected_id].astype(str).str[:5]

    out_cols = [expected_id, "population", "county"]
    for c in [*list(_PL_VARIABLES), "votes_R", "votes_D", "cd119_district"]:
        if c in gdf.columns and c not in out_cols:
            out_cols.append(c)
    out_cols.append("geometry")

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    gdf[out_cols].to_file(out, driver="GeoJSON")
    print(f"wrote {len(gdf):,} {geography.cli_name} units to {out}")
    shutil.rmtree(out.with_suffix(""), ignore_errors=True)

    if not args.no_enacted and "cd119_district" in gdf.columns:
        _write_enacted_plan(gdf, id_column=expected_id, out_path=enacted_out)
        shutil.rmtree(enacted_out.with_suffix(""), ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
