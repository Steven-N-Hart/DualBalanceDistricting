# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

```
src/dualbalance/   Python package — implementation of the algorithm + CLI
  apportionment.py Method of Equal Proportions (2020 regression-tested)
  geography.py     Geography enum (VTD / BLOCK / BLOCK_GROUP) + TIGER URLs
  io.py            load_units, write_plan, load_plan, write_metrics, etc.
  seeds.py         deterministic radial seed placement
  districting.py   single-pass capacitated assignment + contiguity repair
  tighten.py       opt-in L¹ pop-balance tightening pass (--tighten-pop)
  scoring.py       pop/area deviation, DualBalance Score, Polsby-Popper, Reock
  config.py        YAML --config support (CLI > YAML > argparse-default)
  cli.py           argparse CLI: generate / apportion / score / compare
tests/             pytest suite (75 tests, lint-clean)
configs/           example YAML configs (mn_vtd.yaml, apportion_2020.yaml)
data/              prepared input geojson + data/README.md (data files gitignored)
scripts/           prep_mn_units.py — fetches TIGER + (optional) Census API
docs/              Formalism.md (mathematical spec) + research notes
manuscript/        LaTeX manuscript (main.tex + sections/ + references.bib + figures/)
pyproject.toml     hatchling build; runtime deps: geopandas, shapely, gerrychain,
                   numpy, pyyaml; dev extras: pytest, ruff
.env / .env.example  Census API key (.env gitignored, .env.example committed)
```

Target language is Python (>=3.11), CLI uses stdlib `argparse`, build backend is hatchling. All algorithm modules are implemented and tested; the CLI's `compare` subcommand is the only intentional stub (out of PoC scope).

## Common commands

```powershell
pip install -e ".[dev]"       # editable install with dev tooling (pytest, ruff)
pytest                         # run the test suite
ruff check .                   # lint
ruff format .                  # format
dualbalance --help             # see subcommands

# Minnesota PoC end-to-end
python scripts/prep_mn_units.py --geography vtd          # writes data/mn_vtd.geojson
dualbalance generate --config configs/mn_vtd.yaml        # writes out/mn_yaml/{map,metrics}.{geojson,json}
dualbalance score --plan out/mn_yaml/map.geojson --units data/mn_vtd.geojson --geography vtd
```

`prep_mn_units.py` optionally reads `CENSUS_API_KEY` from a `.env` file (gitignored) to join real 2020 PL 94-171 population; without a key (or if the API rejects the key) it falls back to synthesizing uniform population (1000 per unit) and prints a clear warning.

## What the project is

DualBalance Districting is a deterministic redistricting algorithm. Given a state boundary, census-unit data, and a fixed district count `N`, it produces a district map that weights population balance and geographic-area balance equally. There is no randomness, no manual adjustment, and no tuning knobs — same input always yields the same output.

The motivating context (2026): partisan gerrymandering is entrenched, the Supreme Court's *Rucho* / *Alexander* / *Callais* line has significantly limited Section 2 of the Voting Rights Act in practice, and states are now redrawing maps for partisan advantage on every cycle rather than once per decade. The project proposes a deterministic alternative: a districting rule that updates only with each 10-year census, cannot be tuned to advantage a party, and reframes congressional districts as carrying *both* the House (population) and Senate (geography) representation principles within a single chamber.

Two-level structure:

- **National apportionment** assigns each state its district count `N_s` using the Method of Equal Proportions, where `priority(s, n) = population(s) / sqrt(n(n+1))`.
- **State-level districting** runs the DualBalance algorithm independently inside each state to produce `N_s` districts.

The scoring harness is intentionally decoupled from the generator: it can score any plan (enacted, court-drawn, third-party) using the same metrics applied to DualBalance's own output.

## The algorithm

A deterministic, single-pass pipeline. No iteration, no tuning weights, no post-hoc tightening.

1. **Radial seed placement.** Compute the population-weighted centroid of the state's atomic units. Place `N` seeds on a small circle around that centroid (radius = 0.1 % of the bounding-box diagonal) at equally-spaced angles `2π · d / N` for `d = 0, …, N-1`. Seed 0 points due east; seeds advance counter-clockwise.
2. **Capacitated first-fit assignment.** Sort all `(unit, district)` pairs by normalized Euclidean distance ascending; assign each unit to its first district with remaining population capacity `P* = total_population / N`. Ties on distance break by `(unit_id asc, district_id asc)`. Leftover units from integer-rounding edge cases go to the district with the most remaining capacity (`np.argmax` tie-breaks to the lowest district id).
3. **Contiguity repair.** For each district with more than one connected component, dissolve the smaller components into adjacent districts by lowest-cost transfer, where cost is `dist + pop_pen + area_pen` (normalized distance plus normalized pop and area deviations). Cascade tie-breaks: cost → pop_pen → area_pen → distance → district id.

With seeds arranged on a small circle, the Voronoi cells degenerate to near-perfect radial slices through the population center. Each slice naturally spans both dense (near-center) and sparse (toward-the-boundary) territory, so each district holds roughly 1/N of the population *and* a coherent slice of the state's geography.

### Optional post-pass: `--tighten-pop`

The radial pipeline's per-district `pop_deviation` typically sits in the 5–15 % range on real census geometry, well above the ~0.5 % *Reynolds v. Sims* threshold. The opt-in `--tighten-pop` flag runs an L¹-greedy boundary-unit swap pass (`src/dualbalance/tighten.py`) that closes this gap to the user-supplied `--pop-tolerance` (default 0.5 %). The L¹ objective `Σ_i |Pop(D_i) - P*|` is used rather than the L∞ `max_i |Pop(D_i) - P*|` because radial geometries place over-target and under-target districts on opposite sides of the population centroid: no single move between adjacent slices reduces the max, but many such moves reduce the sum. On the MN PoC the pass takes ~80 swaps and ~18 s to drive `pop_dev_max` from 11.24 % to 0.21 %, with `area_dev_mean` essentially unchanged and the visible radial structure preserved (units move only at slice boundaries).

## Core algorithm invariants

Non-negotiable. Check every design decision against them:

- **Deterministic.** No RNG, no wall-clock dependence. Same input always yields byte-identical output. The seed positions, assignment order, tie-breaking, and repair pass are all pure functions of `(units, n_districts)`.
- **Atomic-unit boundaries.** Districts are unions of whole atomic units (VTDs, block groups, or blocks); boundaries follow unit boundaries.
- **Population balance is a hard cap.** Each district receives at most `P* = total_population / N` (a capacitated transportation step in the lineage of Hess-style models). Soft penalty forms destabilize on real census geometry; do not re-introduce them.
- **Area balance is reported, not enforced.** The algorithm draws geometry that naturally trades pop-balance and area-balance equally via radial slicing; the score reports area deviation as a diagnostic.
- **Contiguity, non-empty, full coverage.** Every unit belongs to exactly one district; the repair pass guarantees every district is contiguous.
- **No tuning knobs on the core algorithm.** The CLI exposes only data-plumbing flags for the radial generator itself: `--districts`, `--units`, `--geography`, `--id-column`, `--pop-column`, `--out`, `--config`. There is no `--seed-method`, `--alpha`, `--max-iter`, `--reynolds-tighten`, `--enforce-area`, etc.: the core algorithm has no behavior to tune. One **opt-in** post-pass is available — `--tighten-pop` plus `--pop-tolerance T` — that performs L¹-greedy boundary-unit swaps to close the per-district pop_deviation gap to `T` (default 0.5 %). This is the only piece of the pipeline that is not a pure function of `(units, n_districts)`; it is off by default, and turning it on is a project-level decision about whether to trade a small degradation of the visible radial structure for *Reynolds v. Sims* compliance.
- **Out-of-scope inputs.** Politics, race/demographics, communities of interest, competitiveness — the generator must not read these. Partisan metrics may be *reported* by the scoring harness but never fed back into the generator.

## Objective function

The scoring harness reports a single primary metric:

```
DualBalance Score = 1 / (1 + 0.5 · pop_deviation_mean + 0.5 · area_deviation_mean)
```

where `pop_deviation_d = |Pop(d) - P*| / P*` and `area_deviation_d = |Area(d) - A*| / A*`, averaged over districts. The 0.5/0.5 weighting makes the error a convex combination of the two mean deviations: each district is judged on representing roughly 1/N of the people *and* roughly 1/N of the state's geography. Both reach 1.0 for a perfectly balanced plan; the score approaches 0 as deviations grow without bound.

The generator does **not** directly minimize this score; it minimizes population-capacitated geographic-assignment cost with radial seeding, which empirically produces a higher score than blob-Voronoi designs and beats enacted plans on the MN PoC (0.6472 vs 0.6390).

Secondary metrics: Polsby-Popper compactness (via gerrychain.metrics), Reock (via shapely's minimum bounding radius), per-district population/area breakdown. Compactness scores will be lower than for blob-Voronoi or hand-drawn plans — radial slices are deliberately not blob-shaped.

## Outputs

A single `dualbalance generate` run emits to its `--out` directory:

- `map.geojson` — one feature per atomic unit with `district_id` property; rows sorted by `unit_id` for byte-identical reproducibility.
- `metrics.json` — DualBalance Score, primary metrics, compactness, per-district breakdown. Keys are sorted; reproducible byte-for-byte.

The `compare` subcommand and `comparison.json`, the HTML report, and the multi-state `national_map.geojson` are explicitly **out of scope** for the current PoC; the `compare` stub raises a clear "not in PoC scope" message.

## Manuscript

The [manuscript/](manuscript/) directory holds a LaTeX write-up of the method, kept under version control alongside the code. Structure: `main.tex` includes `sections/{introduction,methods,results,discussion}.tex` and `references.bib`; figures go in `figures/`. Build with `pdflatex main.tex` (run twice, with `bibtex main` in between, to resolve citations). Methods should mirror [docs/Formalism.md](docs/Formalism.md) — if one changes, update the other.
