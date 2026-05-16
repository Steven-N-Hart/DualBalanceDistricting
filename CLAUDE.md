# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

```
src/dualbalance/   Python package — implementation of the algorithm + CLI
  apportionment.py Method of Equal Proportions (2020 regression-tested)
  geography.py     Geography enum (VTD / BLOCK / BLOCK_GROUP) + TIGER URLs
  states.py        STATE_INFO table (FIPS, TIGER name, apportioned seats)
  types.py         shared dataclasses: Targets, Seed, Plan
  io.py            load_units, write_plan, load_plan, write_metrics, etc.
  seeds.py         deterministic radial seed placement
  districting.py   single-pass capacitated assignment + contiguity repair
  tighten.py       opt-in L¹ pop-balance tightening pass (--tighten-pop)
  optimize.py      two-phase greedy local search with chain-escape (used by
                   cascade and as the engine behind tighten's L¹ pass)
  contiguity.py    Tarjan articulation-point cache for O(1) safe-removal checks
  cascade.py       Iowa-LSA-flavored deterministic baseline (county-aggregated)
  scoring.py       pop/area deviation, DualBalance Score, Polsby-Popper, Reock
  config.py        YAML --config support (CLI > YAML > argparse-default)
  cli.py           argparse CLI: generate / generate-cascade / apportion / score / compare
tests/             pytest suite (106 tests, lint-clean)
configs/           per-state YAML configs (mn_vtd, ia_vtd, ma_vtd, tx_vtd,
                   nc_vtd, wi_vtd, apportion_2020)
data/              prepared input geojson + data/README.md (data files gitignored)
scripts/           prep_state_units.py — per-state TIGER + Census + dra2020 + cd119 join
                   compare_state.py — side-by-side PRISM vs enacted scoring
                   prep_bdistricting.py — ingest BDistricting reference plans for cross-algo comparison
                   fetch_enacted_mn.py, plot_mn_poc.py, plot_mn_comparison.py — PoC helpers
docs/              Formalism.md (mathematical spec), legal-standards.md,
                   mn-poc-walkthrough.md, stuck-state-problem.md,
                   gerrymandering-research.md
manuscript/        LaTeX manuscript (main.tex + sections/ + references.bib + figures/)
pyproject.toml     hatchling build; runtime deps: geopandas, shapely, gerrychain,
                   numpy, pyyaml; dev extras: pytest, ruff; optional: numba (speeds
                   up contiguity.py's articulation-point pass at block scale)
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

# Per-state PoC end-to-end (MN, IA, MA, TX, NC, WI currently supported)
python scripts/prep_state_units.py --state MN            # writes data/mn_vtd.geojson + data/mn_enacted.geojson
dualbalance generate --config configs/mn_vtd.yaml        # writes out/mn_yaml/{map,metrics}.{geojson,json}
dualbalance generate-cascade --config configs/mn_vtd.yaml --out out/mn_cascade   # Cascade baseline
python scripts/compare_state.py --state MN               # PRISM vs Cascade vs BDistricting vs enacted
```

`prep_state_units.py` (generalized from the earlier `prep_mn_units.py`) handles any state in `dualbalance.states.STATE_INFO`: downloads TIGER 2020 VTDs, fetches Census PL 94-171 demographics (using `CENSUS_API_KEY` from `.env` if present, else synthesized uniform 1000), joins dra2020/vtd_data 2020 presidential votes, and joins the enacted 119th-Congress plan via a TIGER 2024 cd119 spatial join (representative-point join with smallest-CD-number tiebreaker). Add a new state by extending `STATE_INFO` (in [src/dualbalance/states.py](src/dualbalance/states.py)) with its FIPS, TIGER state name, and apportioned seat count.

## What the project is

DualBalance Districting is the project framing: each congressional district should carry both ~1/N of a state's people and ~1/N of its land, weighted equally. The objective is captured by the DualBalance Score (DBS); the algorithm that pursues it is **PRISM** (Population-weighted Radial Impartial Slicing Method). Given a state boundary, census-unit data, and a fixed district count `N`, PRISM places `N` seeds radially around the population-weighted centroid and runs a single capacitated first-fit assignment. There is no randomness, no manual adjustment, and no tuning knobs — same input always yields the same output. The CLI, Python package, and repo retain the `dualbalance` umbrella name; algorithm references in the manuscript and docs use `PRISM`.

The motivating context (2026): partisan gerrymandering is entrenched, the Supreme Court's *Rucho* / *Alexander* / *Callais* line has significantly limited Section 2 of the Voting Rights Act in practice, and states are now redrawing maps for partisan advantage on every cycle rather than once per decade. The project proposes a deterministic alternative: a districting rule that updates only with each 10-year census, cannot be tuned to advantage a party, and reframes congressional districts as carrying *both* the House (population) and Senate (geography) representation principles within a single chamber.

Two-level structure:

- **National apportionment** assigns each state its district count `N_s` using the Method of Equal Proportions, where `priority(s, n) = population(s) / sqrt(n(n+1))`.
- **State-level districting** runs PRISM independently inside each state to produce `N_s` districts.

The scoring harness is intentionally decoupled from the generator: it can score any plan (enacted, court-drawn, third-party) using the same metrics applied to PRISM's own output.

## The algorithm

PRISM's core is a deterministic, single-pass pipeline. No iteration, no tuning weights, no post-hoc tightening. An opt-in local-search refinement (`tighten.py` + `optimize.py`) is available separately; it is off by default and never modifies the core pass.

1. **Radial seed placement.** Compute the population-weighted centroid of the state's atomic units. Place `N` seeds on a small circle around that centroid (radius = 0.1 % of the bounding-box diagonal) at equally-spaced angles `2π · d / N` for `d = 0, …, N-1`. Seed 0 points due east; seeds advance counter-clockwise.
2. **Capacitated first-fit assignment.** Sort all `(unit, district)` pairs by normalized Euclidean distance ascending; assign each unit to its first district with remaining population capacity `P* = total_population / N`. Ties on distance break by `(unit_id asc, district_id asc)`. Leftover units from integer-rounding edge cases go to the district with the most remaining capacity (`np.argmax` tie-breaks to the lowest district id).
3. **Contiguity repair.** For each district with more than one connected component, dissolve the smaller components into adjacent districts by lowest-cost transfer, where cost is `dist + pop_pen + area_pen` (normalized distance plus normalized pop and area deviations). Tie-breaks: cost → pop_pen → area_pen → distance → district id.

With seeds arranged on a small circle, the Voronoi cells degenerate to near-perfect radial slices through the population center. Each slice naturally spans both dense (near-center) and sparse (toward-the-boundary) territory, so each district holds roughly 1/N of the population *and* a coherent slice of the state's geography.

### Optional post-pass: `--tighten-pop`

The radial pipeline's per-district `pop_deviation` typically sits in the 5–15 % range on real census geometry, well above the ~0.5 % *Reynolds v. Sims* threshold. The opt-in `--tighten-pop` flag runs an L¹-greedy boundary-unit swap pass (entry point in [tighten.py](src/dualbalance/tighten.py); the underlying engine lives in [optimize.py](src/dualbalance/optimize.py)) that closes this gap to the user-supplied `--pop-tolerance` (default 0.5 %).

The optimizer is two-phase, both phases deterministic:

- **Phase 1 (pop tightening).** Each step picks the boundary move that either reduces `Σ_d |pop_dev_d|` (L¹) or strictly reduces `max_d |pop_dev_d|` (L∞). The L¹ objective is used rather than L∞ alone because radial geometries place over-target and under-target districts on opposite sides of the population centroid: no single move between adjacent slices reduces the max, but many such moves reduce the sum. When 1-opt stalls but `pop_dev_max` is still above tolerance, a length-2 then length-3 **chain escape** (the deterministic analogue of an ejection chain) searches for an augmenting transport on the district-adjacency graph.
- **Phase 2 (DBS hill-climb).** Once Phase 1 converges, picks the boundary move that maximally improves the DualBalance Score, subject to `pop_dev_max` not exceeding the value Phase 1 reached.

Engineering: [contiguity.py](src/dualbalance/contiguity.py) maintains a per-district articulation-point cache via Tarjan on CSR adjacency arrays (numba-accelerated when available), reducing the per-candidate contiguity check from `O(V + E)` to `O(1)`. An incrementally-tracked boundary-unit set restricts each scan to units that actually have a different-district neighbor. On the MN PoC the full pass takes ~80 swaps and a few seconds to drive `pop_dev_max` from 11.24 % to 0.21 %, with `area_dev_mean` essentially unchanged and the visible radial structure preserved (units move only at slice boundaries). At block scale these caches are the difference between hours and minutes per state.

### Cascade baseline (`dualbalance generate-cascade`)

[cascade.py](src/dualbalance/cascade.py) is a separate, Iowa-LSA-flavored deterministic baseline (not a variant of PRISM). It aggregates VTDs to counties, uses farthest-point seeding for spread, and lexicographically prioritizes (1) county integrity (oversized counties are split via PRISM-style capacitated assignment inside the county), (2) population balance via capacitated first-fit, (3) compactness via distance-based ordering. The L¹ tightening pass from `optimize.py` runs by default after assignment (skip with `--no-tighten`). Cascade is the structural opposite of PRISM: instead of spanning urban-rural by slicing radially, it preserves administrative units and produces compact county-bundled districts. It is exposed primarily for cross-algorithm comparison; the project's primary method is PRISM.

## Core algorithm invariants

Non-negotiable. Check every design decision against them:

- **Deterministic.** No RNG, no wall-clock dependence. Same input always yields byte-identical output. The seed positions, assignment order, tie-breaking, and repair pass are all pure functions of `(units, n_districts)`.
- **Atomic-unit boundaries.** Districts are unions of whole atomic units (VTDs, block groups, or blocks); boundaries follow unit boundaries.
- **Population balance is a hard cap.** Each district receives at most `P* = total_population / N` (a capacitated transportation step in the lineage of Hess-style models). Soft penalty forms destabilize on real census geometry; do not re-introduce them.
- **Area balance is reported, not enforced.** The algorithm draws geometry that naturally trades pop-balance and area-balance equally via radial slicing; the score reports area deviation as a diagnostic.
- **Contiguity, non-empty, full coverage.** Every unit belongs to exactly one district; the repair pass guarantees every district is contiguous.
- **No tuning knobs on the core algorithm.** The `generate` subcommand exposes only data-plumbing flags for the radial generator itself: `--districts`, `--units`, `--geography`, `--id-column`, `--pop-column`, `--county-column`, `--out`, `--config`. There is no `--seed-method`, `--alpha`, `--max-iter`, `--reynolds-tighten`, `--enforce-area`, etc.: the core algorithm has no behavior to tune. One **opt-in** post-pass is available — `--tighten-pop` plus `--pop-tolerance T` — that runs the two-phase deterministic optimizer to close the per-district pop_deviation gap to `T` (default 0.5 %) and then hill-climbs the DualBalance Score. This is the only piece of the PRISM pipeline that is not a pure function of `(units, n_districts)` (it depends additionally on `T`); it is off by default, and turning it on is a project-level decision about whether to trade a small degradation of the visible radial structure for *Reynolds v. Sims* compliance. The separate `generate-cascade` subcommand is a different algorithm exposed as a baseline, not a tuning of PRISM.
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
