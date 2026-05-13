# Data

This directory holds prepared input files for the `dualbalance` CLI. Raw
downloads and processed outputs are gitignored; only this README and any
small fixtures live in version control.

## Minnesota PoC

The Phase 8 end-to-end run targets Minnesota's 8 U.S. House districts using
2020 TIGER/Line Voting Tabulation District (VTD) geometry. The companion
helper script is at [`scripts/prep_mn_units.py`](../scripts/prep_mn_units.py).

### One-time prep

```powershell
python scripts/prep_mn_units.py --geography vtd
```

This writes `data/mn_vtds.geojson` with the canonical columns the CLI loader
expects: `GEOID20`, `population`, `geometry`. By default the script
**synthesizes a uniform population (1000 per VTD)** because the canonical
2020 population source — the Census Bureau's PL 94-171 redistricting summary
file or its Data API — either requires fixed-width parsing or an API key.
The downstream algorithm and CLI work the same way; only the per-district
population deviation metric reflects the synthetic input.

### Other geographies

`prep_mn_units.py` also supports `--geography block` and
`--geography block_group`; they download the corresponding TIGER files from

| Geography     | URL                                                                                                       |
|---------------|-----------------------------------------------------------------------------------------------------------|
| `vtd`         | `https://www2.census.gov/geo/tiger/TIGER2020PL/STATE/27_MINNESOTA/27/tl_2020_27_vtd20.zip`                |
| `block`       | `https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_27_tabblock20.zip`                        |
| `block_group` | `https://www2.census.gov/geo/tiger/TIGER2020/BG/tl_2020_27_bg20.zip`                                      |

### Joining real population data

To replace the synthetic population with the actual 2020 count:

1. Register for a free Census Data API key at
   <https://api.census.gov/data/key_signup.html>.
2. Request the variable `P1_001N` from the 2020 PL 94-171 dataset
   (`/data/2020/dec/pl`) at the matching geography level, scoped to
   `state:27`.
3. Join the API response onto the GeoDataFrame on `GEOID20` (VTDs / blocks)
   or `GEOID` (block groups) and write the result back to
   `data/mn_<geography>.geojson`.

Patches to `prep_mn_units.py` that wire this through (gated on the
`CENSUS_API_KEY` env var) are welcome.
