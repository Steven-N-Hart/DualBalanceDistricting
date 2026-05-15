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
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

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


# Census PL 94-171 variables. P1 is total population; P3 is voting-age
# population by race (alone); P4 is VAP by Hispanic/Latino origin and race.
# Documented at https://api.census.gov/data/2020/dec/pl/variables.html.
_PL_VARIABLES: dict[str, str] = {
    "population": "P1_001N",  # Total population
    "vap_total": "P3_001N",  # Total VAP
    "vap_nhwhite": "P4_005N",  # Not Hispanic, White alone VAP
    "vap_black": "P3_004N",  # Black or African American alone VAP
    "vap_aian": "P3_005N",  # American Indian / Alaska Native alone VAP
    "vap_asian": "P3_006N",  # Asian alone VAP
    "vap_hispanic": "P4_002N",  # Hispanic or Latino VAP
}


def _fetch_pl_via_api(geography: Geography, state_fips: str, api_key: str) -> pd.DataFrame:
    """Query the 2020 PL 94-171 dataset for total pop + race VAP per unit.

    Returns a DataFrame with columns ``GEOID`` plus one column per
    canonical name in :data:`_PL_VARIABLES`. GEOID is the full census
    GEOID string (state + county + unit subcode), matching TIGER's
    GEOID20 field.
    """
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
    with urllib.request.urlopen(url, timeout=120) as resp:
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


# Source: dra2020/vtd_data — 2020 precinct/VTD election results joined to
# TIGER 2020 GEOID20 by the maintainers of Dave's Redistricting App.
# https://github.com/dra2020/vtd_data
DRA_ELECTION_URL = (
    "https://github.com/dra2020/vtd_data/raw/master/2020_VTD/MN/Election_Data_MN.v07.zip"
)


def _fetch_dra_elections(url: str) -> pd.DataFrame:
    """Download the dra2020 MN election ZIP and return 2020 presidential.

    Output columns: ``GEOID20``, ``votes_R``, ``votes_D`` (renamed from
    ``E_20_PRES_Rep`` / ``E_20_PRES_Dem``). Other races in the file are
    ignored — pick a different one by post-processing the CSV manually.
    """
    print(f"  downloading election data from {url}")
    with urllib.request.urlopen(url, timeout=120) as resp:
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
    id_column: str,
    csv_path: Path | None,
    api_key: str | None,
) -> gpd.GeoDataFrame:
    """Join total population + race VAP onto ``gdf``.

    Precedence: ``csv_path`` > Census API > synthesized uniform fallback.
    The CSV path is population-only (race VAP only loads via the API).
    """
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
            pl_df = _fetch_pl_via_api(geography, MN_FIPS, api_key)
        except RuntimeError as exc:
            print(
                f"  WARNING: Census API call failed ({exc}); "
                "falling back to synthetic uniform population=1000 (no race data)."
            )
            print("  If you just signed up, check your email for the activation link.")
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
            f"  joined real demographics for {len(merged):,} units "
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
    url: str | None,
) -> gpd.GeoDataFrame:
    """Join 2020 presidential vote totals onto ``gdf``.

    Either reads a local CSV (must have ``GEOID20``, ``votes_R``,
    ``votes_D``) or fetches the dra2020/vtd_data MN zip from ``url``.
    On any failure prints a warning and returns ``gdf`` unchanged — the
    scoring harness will then simply omit partisan metrics.
    """
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
    elif url is not None:
        try:
            edf = _fetch_dra_elections(url)
            edf = edf.rename(columns={"GEOID20": id_column})
        except (urllib.error.URLError, RuntimeError) as exc:
            print(
                f"  WARNING: failed to fetch partisan data ({exc}); "
                "skipping partisan join. Use --election-csv to provide locally."
            )
            return gdf
    else:
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
    parser.add_argument(
        "--election-csv",
        type=Path,
        dest="election_csv",
        help="Optional path to a CSV with GEOID20,votes_R,votes_D. "
        "Overrides the dra2020/vtd_data auto-fetch.",
    )
    parser.add_argument(
        "--election-url",
        dest="election_url",
        default=DRA_ELECTION_URL,
        help=f"URL to fetch partisan data from (default: {DRA_ELECTION_URL}).",
    )
    parser.add_argument(
        "--no-elections",
        dest="no_elections",
        action="store_true",
        help="Skip partisan join entirely (no votes_R / votes_D columns).",
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

    gdf = _attach_demographics(
        gdf,
        geography=geography,
        id_column=expected_id,
        csv_path=args.population_csv,
        api_key=api_key,
    )

    if not args.no_elections:
        gdf = _attach_elections(
            gdf,
            id_column=expected_id,
            csv_path=args.election_csv,
            url=args.election_url,
        )

    # County FIPS = first 5 chars of any Census GEOID (state[2] + county[3]).
    # Preserved as a diagnostic column for the scoring harness; the core
    # generator must not read it.
    gdf["county"] = gdf[expected_id].astype(str).str[:5]

    out_cols = [expected_id, "population", "county"]
    for c in [*list(_PL_VARIABLES), "votes_R", "votes_D"]:
        if c in gdf.columns and c not in out_cols:
            out_cols.append(c)
    out_cols.append("geometry")

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    gdf[out_cols].to_file(out, driver="GeoJSON")
    print(f"wrote {len(gdf):,} {geography.cli_name} units to {out}")
    shutil.rmtree(out.with_suffix(""), ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
