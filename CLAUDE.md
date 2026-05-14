# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

```
src/dualbalance/   Python package — implementation of the algorithm + CLI
  apportionment.py Method of Equal Proportions (2020 regression-tested)
  geography.py     Geography enum (VTD / BLOCK / BLOCK_GROUP) + TIGER URLs
  io.py            load_units, write_plan, load_plan, write_metrics, etc.
  seeds.py         deterministic farthest-point seed placement
  districting.py   capacitated-greedy assignment + Lloyd recentering + contiguity repair
  scoring.py       pop/area deviation, DualBalance Score, Polsby-Popper, Reock
  config.py        YAML --config support (CLI > YAML > argparse-default)
  cli.py           argparse CLI: generate / apportion / score / compare
tests/             pytest suite (76+ tests, lint-clean)
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
pytest tests/test_cli.py::test_subcommand_help_parses[generate]   # single test
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

DualBalance Districting is a deterministic redistricting algorithm. Given a state boundary, census block data, and a fixed district count `N`, it produces a district map that weights population balance and geographic-area balance equally. There is no randomness and no manual adjustment — same input always yields the same output.

Two-level structure to keep in mind when designing modules:

- **National apportionment** assigns each state its district count `N_s` using the Method of Equal Proportions, where `priority(s, n) = population(s) / sqrt(n(n+1))`.
- **State-level districting** runs the DualBalance algorithm independently inside each state to produce `N_s` districts.

The scoring harness is intentionally decoupled from the generator: it must be able to score any plan (enacted, court-drawn, third-party) using the same metrics applied to DualBalance's own output.

## Core algorithm invariants

These are non-negotiable properties the implementation must preserve. Check every design decision against them:

- **Deterministic.** No RNG, no wall-clock dependence. Capacitated assignment processes `(unit, district)` pairs in ascending normalized distance; ties on min cost break by `(unit_id, district_id)` ascending. Contiguity-repair tie cascade matches [docs/Formalism.md](docs/Formalism.md): lower population error → lower area error → shorter seed distance → smaller district ID → smaller block ID.
- **Block-level atomicity.** Districts are unions of whole atomic units; boundaries follow unit boundaries.
- **Population balance is a hard constraint.** Each district has a capacity `P* = P/N` enforced at the assignment step — a capacitated transportation step in the lineage of Hess-style location-allocation models. Soft penalty forms (absolute or one-sided) destabilize on real census geometry — do not re-introduce them as the primary assignment rule.
- **Area balance is reported, not enforced (v0 baseline).** The current generator is the "Population-Capacitated Voronoi Baseline" (v0): only population is capped. The DualBalance Score weights pop and area deviation equally for *reporting*. The planned "Dual-Capacitated Voronoi Assignment" (v1) extends the assignment step to a two-dimensional capacitated transportation problem that bounds both pop and area — guard tests if you implement it.
- **Contiguity, non-empty, full coverage.** Every unit belongs to exactly one district; the post-iteration repair pass guarantees every district is contiguous. Empty districts can appear only with extreme inputs (more districts than the geometry can spatially separate).
- **Out of scope inputs.** Politics, race/demographics, communities of interest, competitiveness — the generator must not read these. Partisan metrics may be *reported* by the scoring harness but never fed back into the generator.

## Objective function

Two scores are reported side-by-side; the v0 generator does **not** directly minimize either (it minimizes population-capacitated geographic-assignment cost and reports the scores diagnostically):

```
DualBalance Score          = 1 / (1 + 0.5 · pop_deviation_mean + 0.5 · area_deviation_mean)
DualBalance Score, classic = 1 / (1 +       pop_deviation_mean +       area_deviation_mean)
```

where `pop_deviation_d = |Pop(d) - P*| / P*` and similarly for area, averaged over districts. The default (weighted) form's 0.5/0.5 weighting makes the error a convex combination of the two mean deviations (β = γ = ½), enforcing the "each district holds ~1/N of people *and* ~1/N of geography" reading. The classic (sum-of-means) form is strictly more punishing whenever either deviation is nonzero; both reach 1.0 for a perfectly balanced plan. The `--score-variant {weighted,classic}` flag on `dualbalance generate` selects which form Reynolds-tighten Phase A optimizes against (default: `weighted`); both scores still appear in `metrics.json` regardless. Per-district `pop_deviation` and `area_deviation` are exposed so consumers can recompute either form from the breakdown. Secondary metrics: Polsby-Popper compactness (via gerrychain.metrics), Reock (via shapely's minimum bounding radius), per-district population/area breakdown.

## Outputs

A single `dualbalance generate` run emits to its `--out` directory:

- `map.geojson` — one feature per atomic unit with `district_id` property; rows sorted by `unit_id` for byte-identical reproducibility.
- `metrics.json` — DualBalance Score, primary metrics, compactness, per-district breakdown. Keys are sorted; reproducible byte-for-byte.

The `compare` subcommand and `comparison.json`, the HTML report, and the multi-state `national_map.geojson` are explicitly **out of scope** for the current PoC; the `compare` stub raises a clear "not in PoC scope" message.

## Manuscript

The [manuscript/](manuscript/) directory holds a LaTeX write-up of the method, kept under version control alongside the code. Structure: `main.tex` includes `sections/{introduction,methods,results,discussion}.tex` and `references.bib`; figures go in `figures/`. Build with `pdflatex main.tex` (run twice, with `bibtex main` in between, to resolve citations). Methods should mirror [docs/Formalism.md](docs/Formalism.md) — if one changes, update the other.
