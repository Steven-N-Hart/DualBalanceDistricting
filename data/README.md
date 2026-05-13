# Data

This directory holds prepared input files for the `dualbalance` CLI. Raw
downloads and processed outputs are gitignored; only this README and any
small fixtures live in version control.

## Minnesota PoC

The Phase 8 end-to-end run targets Minnesota's 8 U.S. House districts using
2020 TIGER/Line Voting Tabulation District (VTD) geometry plus 2020 PL
94-171 redistricting-data population. The companion helper script is at
[`scripts/prep_mn_units.py`](../scripts/prep_mn_units.py).

### One-time setup: Census Data API key

The prep script can join real 2020 population from the Census Data API when
a free API key is available. Register at
<https://api.census.gov/data/key_signup.html>, then save the key to a
`.env` file at the repo root (the `.env` filename is gitignored):

```ini
# .env
CENSUS_API_KEY=your_40_char_hex_key_here
```

The script reads `.env` via a tiny built-in loader — no `python-dotenv`
dependency required. Newly issued keys take a few minutes to activate;
until then the API rejects requests with an "Invalid Key" page.

### Running the prep

```powershell
python scripts/prep_mn_units.py --geography vtd
```

This downloads the MN VTD shapefile, joins real population on `GEOID20`
via the API (when `CENSUS_API_KEY` is set and active), and writes
`data/mn_vtd.geojson` with the canonical columns the CLI loader expects:
`GEOID20`, `population`, `geometry`. **Without an active key the script
falls back to synthesizing uniform population (1000 per VTD) and prints a
clear warning** — useful for offline development but not for any number
you'd want to cite.

### Other geographies

`prep_mn_units.py` also supports `--geography block` and
`--geography block_group`; they download the corresponding TIGER files from

| Geography     | URL                                                                                                       |
|---------------|-----------------------------------------------------------------------------------------------------------|
| `vtd`         | `https://www2.census.gov/geo/tiger/TIGER2020PL/STATE/27_MINNESOTA/27/tl_2020_27_vtd20.zip`                |
| `block`       | `https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_27_tabblock20.zip`                        |
| `block_group` | `https://www2.census.gov/geo/tiger/TIGER2020/BG/tl_2020_27_bg20.zip`                                      |

The API population lookup uses the same `P1_001N` (total population) field
for every geography; the script picks the correct `for=` parameter
automatically based on `--geography`.
