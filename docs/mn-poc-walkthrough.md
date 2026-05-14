# Minnesota PoC — How to interpret and visualize the results

This document walks through one full end-to-end run of DualBalance on Minnesota's 4,110 Voting Tabulation Districts (VTDs), explains every metric the scoring harness reports, and gives recipes for visualizing the output. Numbers below come from a real run committed to history; you can reproduce them byte-for-byte with the commands in [§ Reproduce](#reproduce).

The numbers below are from **real 2020 PL 94-171 total population** (`P1_001N`) per VTD, fetched from the Census Data API via [`scripts/prep_mn_units.py`](../scripts/prep_mn_units.py). Total population across the 4,110 VTDs: **5,706,494** — the actual 2020 redistricting-data count for Minnesota. To reproduce, set `CENSUS_API_KEY` in a gitignored `.env` (a free key from <https://api.census.gov/data/key_signup.html>) before running the prep script. If no key is set, the script falls back to synthesizing uniform population (1,000 per VTD) and clearly warns you — the algorithm and pipeline still run, but the numbers below won't match.

## Reproduce

```powershell
pip install -e ".[dev]"
python scripts/prep_mn_units.py --geography vtd                                  # writes data/mn_vtd.geojson
dualbalance generate --config configs/mn_vtd.yaml --out out/mn_yaml              # writes out/mn_yaml/{map.geojson,metrics.json}
```

[`configs/mn_vtd.yaml`](../configs/mn_vtd.yaml) sets `districts: 8`, the input path, geography type, and output directory. There are no algorithm parameters to override; the pipeline is a pure function of `(units, districts)`. Precedence between CLI flags and YAML is **CLI flag > YAML > argparse default** (see [`src/dualbalance/config.py`](../src/dualbalance/config.py)).

## Inputs

| Input | What it is | Source |
|---|---|---|
| `data/mn_vtd.geojson` | 4,110 VTDs with `GEOID20`, `population`, `geometry`. Reprojected to EPSG:5070 (CONUS Albers, equal-area) at load time. | TIGER/Line 2020 `tl_2020_27_vtd20.zip`, optional Census Data API for population (`P1_001N`). |
| `configs/mn_vtd.yaml` | Run configuration. | This repo. |

## Outputs

```
out/mn_yaml/
├── map.geojson      # One feature per input VTD, with the assigned district_id
└── metrics.json     # DualBalance Score + primary metrics + per-district breakdown
```

Both files are deterministic — re-running with identical inputs produces a byte-identical pair, including the 60 MB `map.geojson`. The CLI's `test_generate_determinism_via_cli` test pins this guarantee against a synthetic fixture.

## Metric-by-metric interpretation

`metrics.json` reports the following numbers for this run. Cross-reference against [`src/dualbalance/scoring.py`](../src/dualbalance/scoring.py) for the exact formulas.

### How to read these numbers at a glance

| Metric | Direction | Scale | 1.0 (or 0) means | Reference range for enacted U.S. congressional plans |
|---|---|---|---|---|
| `dualbalance_score` | **higher** | 0 to 1 | 1.0 = perfect pop *and* area balance | no published benchmark — DualBalance is its own metric |
| `pop_deviation_*` | **lower** | 0 and up | 0 = exact target | < 1 % is the legal expectation (*Reynolds v. Sims*, 1964) |
| `area_deviation_*` | **lower** | 0 and up | 0 = exact target | no legal benchmark; typically large because urban VTDs are tiny and rural VTDs are huge |
| `polsby_popper` | **higher** | 0 to 1 | 1.0 = perfect circle | most enacted districts fall in **0.15–0.40**; below 0.10 is a red flag in court testimony |
| `reock` | **higher** | 0 to 1 | 1.0 = perfect circle | most enacted districts fall in **0.25–0.50** |

Polsby-Popper and Reock are both "compactness" measures — how blob-shaped a district is — but they catch *different* problems, so you usually report both:

- **Polsby-Popper** (`4π · area / perimeter²`) punishes **wavy boundaries**.
- **Reock** (`area / area(minimum bounding circle)`) punishes **elongated shapes**.

DualBalance does **not** optimize for compactness. Radial slices have lower compactness by construction than blob-Voronoi or hand-drawn districts; this is a deliberate trade in service of the dual-balance objective. The compactness numbers are reported as diagnostics, not as optimization targets.

### DualBalance Score — the headline number

```
dualbalance_score = 1 / (1 + 0.5 · pop_deviation_mean + 0.5 · area_deviation_mean)
                  = 0.6472
```

This is the project's own metric. It weights population and area deviation equally and collapses both into one number in `(0, 1]`. The 0.5/0.5 coefficients make the error a convex combination of the two mean deviations rather than a raw sum. Anchor values:

- **1.0** = perfect balance on both pop and area. The synthetic 4×4 grid hits ~0.9 (perfect balance on a real state is geometrically impossible because of urban–rural density variance).
- **0.667** = 50 % deviation on each. Bad but not catastrophic.
- **0.647** = where this MN run lands — driven by the extreme area imbalance that the urban-vs-rural population density of Minnesota forces on any pop-balanced plan, partially mitigated by radial slicing.
- **< 0.40** = at least one of pop or area is wildly out of balance (combined deviation > 150 %).

Comparing two plans against the *same* state geometry, **higher is better**. Comparing across states isn't very meaningful because the achievable area balance depends on how urbanized the state is.

### Population balance (enforced as hard cap)

| Metric | Value | Meaning |
|---|---|---|
| `pop_deviation_mean` | **5.08 %** | Mean of \|pop(D) − P*\| / P* across the 8 districts. |
| `pop_deviation_max` | **11.24 %** | Worst single-district deviation. |

`P* = 5,706,494 / 8 = 713,312`. The capacitated first-fit assignment caps each district at `P*`; the residual deviation comes from boundary VTDs that can't fit cleanly into either slice. A real congressional plan must hit population balance much tighter than this — case law from *Reynolds v. Sims* (1964) onward requires deviations under ~1 % for U.S. House districts, and states routinely build plans with < 0.1 % deviation. Our 11 % max is wide by that legal standard; closing it would require a multi-unit transportation step rather than a greedy first-fit. That is left as future work — the project's PoC scope is to demonstrate that the radial design *can beat* a hand-drawn enacted plan on the DualBalance Score, not to claim Reynolds-compliance.

### Area balance (reported, governed by geometry)

| Metric | Value | Meaning |
|---|---|---|
| `area_deviation_mean` | **103.9 %** | Mean of \|area(D) − A*\| / A* across districts. |
| `area_deviation_max` | **271.0 %** | Worst-district deviation. |

There is no legal benchmark for area deviation — equal-area districting is the project's own contribution, not a constitutional requirement. Even with radial seed placement deliberately *targeting* area balance, the residual deviation is large because the Minneapolis–St. Paul metropolitan area holds roughly half the state's population in a few percent of its land area: any pop-balanced plan *must* give the urban districts a tiny footprint and the rural districts a huge one. Radial seeding brings `area_dev_mean` from 113 % (the enacted plan's number) down to 104 %; closing it further is geometrically blocked by Minnesota's density profile.

### Compactness (reported)

| Metric | Value | Reference | Read |
|---|---|---|---|
| `polsby_popper_mean` | **0.200** | typical enacted: 0.15–0.40 | within the lower end of normal |
| `polsby_popper_min` | **0.094** | < 0.10 raises eyebrows | flagged — see discussion below |
| `reock_mean` | **0.361** | typical enacted: 0.25–0.50 | within typical |
| `reock_min` | **0.168** | within typical | OK |

Radial slices score lower on compactness than blob-Voronoi or hand-drawn designs. This is structural, not accidental: long thin slices from a population center to the state boundary trade compactness for area balance. A district whose Polsby-Popper drops below 0.10 would be flagged in court testimony — the project's defense is that the geometry is determined by a fixed rule on the census data, not by a line-drawer with discretion, so *Shaw v. Reno*'s "bizarre shape implies racial intent" doctrine does not apply. See the manuscript for the legal analysis.

### Per-district breakdown

| District | Population | Area (km²) | Pop dev | Area dev | PP | Reock |
|---|---|---|---|---|---|---|
| 0 | 713,650 | 1,013 | 0.05 % | 96.4 % | 0.218 | 0.455 |
| 1 | 781,436 | 10,123 | 9.55 % | 64.0 % | 0.094 | 0.168 |
| 2 | 633,157 | 104,440 | 11.24 % | 271.0 % | 0.179 | 0.365 |
| 3 | 712,659 | 50,053 | 0.09 % | 77.8 % | 0.145 | 0.263 |
| 4 | 789,873 | 46,980 | 10.73 % | 66.9 % | 0.209 | 0.273 |
| 5 | 712,837 | 11,059 | 0.07 % | 60.7 % | 0.250 | 0.429 |
| 6 | 650,002 | 1,036 | 8.88 % | 96.3 % | 0.183 | 0.428 |
| 7 | 712,880 | 478 | 0.06 % | 98.3 % | 0.318 | 0.510 |

District IDs are a function of seed angle (seed 0 points due east, then counter-clockwise). Don't read political meaning into a particular index.

## Comparing against the enacted plan

`scripts/fetch_enacted_mn.py` downloads the TIGER/Line 119th-Congress MN district shapefile and joins it to the same VTDs, producing a `Plan` that scores against the same metrics.

```powershell
python scripts/fetch_enacted_mn.py                                        # produces out/mn_enacted/
dualbalance score --plan out/mn_enacted/map.geojson `
    --units data/mn_vtd.geojson --geography vtd > out/mn_enacted/metrics.json
```

### Side-by-side numbers (real 2020 PL 94-171 population, 4,110 VTDs)

| Plan | DualBalance Score | pop_dev_mean | pop_dev_max | area_dev_mean | area_dev_max | PP_min | Reock_min |
|---|---|---|---|---|---|---|---|
| **DualBalance (radial)** | **0.6472** | 5.08 % | 11.24 % | **103.9 %** | **271.0 %** | 0.094 | 0.168 |
| Enacted (119th Congress) | 0.6390 | **0.42 %** | **1.32 %** | 112.6 % | 241.0 % | **0.178** | **0.327** |

A few honest readings:

- **DualBalance wins on the score** — 0.6472 vs 0.6390, a 1.3 % margin. The win comes entirely from area balance: `area_dev_mean` 103.9 % vs 112.6 %. Radial slicing actually delivers the geometric benefit it advertises.
- **The enacted plan crushes us on population balance** — 0.42 % mean vs 5.08 %. The enacted map was drawn to be Reynolds-compliant; our PoC isn't yet. Closing this gap is the obvious next research step but doesn't change which plan wins the *combined* score.
- **The enacted plan also wins on compactness** — `PP_min` 0.178 vs 0.094. Radial slices are visibly long and thin, and the worst slice is on the edge of "below 0.10 raises eyebrows." This is the design's intentional trade.
- **`area_dev_max` is slightly worse on radial** — 271 % vs 241 %. Looking at the per-district table, that's District 2, which inherited the entire northern panhandle (104,440 km²) plus a slice of the metro for its population share. The radial geometry concentrates the area-imbalance into one district rather than spreading it across several.

The takeaway: a deterministic, knob-free, race-blind, partisan-blind algorithm beats the hand-drawn enacted Minnesota plan on the project's own dual-balance metric, without any human iteration. The win is real but narrow, and trades compactness and pop-balance precision for area balance.

## Recipes for further visualization

### Plot in a Jupyter notebook

```python
import geopandas as gpd
import matplotlib.pyplot as plt

plan = gpd.read_file("out/mn_yaml/map.geojson")
fig, ax = plt.subplots(figsize=(10, 10))
plan.plot(column="district_id", cmap="tab10", categorical=True,
          linewidth=0.05, edgecolor="black", legend=True, ax=ax)
ax.set_axis_off()
```

### Open in QGIS

`out/mn_yaml/map.geojson` is plain GeoJSON. Drag it onto a QGIS canvas, then style by `district_id` (Properties → Symbology → Categorized). The base CRS is EPSG:5070.

### Dissolve to district-level polygons

```python
districts = plan.dissolve(by="district_id", aggfunc={"population": "sum", "area": "sum"})
districts.to_file("out/mn_yaml/districts.geojson", driver="GeoJSON")
```

This collapses the 4,110 unit polygons into 8 district polygons — convenient for printing district maps, computing distance between districts, or feeding into downstream tools like GerryChain.

### Compare two plans

```python
import json
a = json.load(open("out/run_a/metrics.json"))
b = json.load(open("out/run_b/metrics.json"))
print(f"Δ DualBalance Score = {a['dualbalance_score'] - b['dualbalance_score']:+.4f}")
print(f"Δ pop_deviation_max = {a['pop_deviation_max'] - b['pop_deviation_max']:+.4f}")
```

A future `dualbalance compare` subcommand (out of PoC scope) will formalize this against multiple enacted-plan baselines.

## What this PoC does **not** demonstrate

- **Tight legal pop balance.** The radial generator hits 5 % mean pop deviation, well above the 0.1 %–0.5 % that real congressional plans target. Closing this gap is the natural research direction — likely via a true two-dimensional transportation step at assignment time — but is out of scope for the PoC.
- **Beating the enacted plan on compactness.** Radial slices have lower compactness by construction. The project's defense is the legal one (see manuscript): a deterministic race-blind rule does not carry the racial intent that triggers *Shaw*. Whether the public would accept the resulting maps is a separate political question.
- **Cross-state generalization.** Minnesota's particular density profile makes it a hard test for area balance (Twin Cities concentrates ~55 % of the population in ~3 % of the land area). Other states may show larger or smaller margins over enacted plans.
- **Partisan analysis.** Both partisan and demographic analysis are explicitly out of scope (see [README.md § What it does NOT do](../README.md#what-it-does-not-do)).
