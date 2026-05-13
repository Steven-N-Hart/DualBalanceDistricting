# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

```
src/dualbalance/   Python package (CLI + algorithm modules; all stubs except CLI plumbing)
tests/             pytest suite
manuscript/        LaTeX manuscript (main.tex + sections/ + references.bib + figures/)
pyproject.toml     hatchling build; ruff + pytest dev extras; `dualbalance` console script
README.md          project motivation, narrative algorithm, scoring harness, design principles
Formalism.md       mathematical specification (objects, seeds, assignment, objective, tie-breaking)
```

Target language is Python (>=3.11), CLI uses stdlib `argparse`, build backend is hatchling. The algorithm modules ([apportionment.py](src/dualbalance/apportionment.py), [districting.py](src/dualbalance/districting.py), [scoring.py](src/dualbalance/scoring.py)) currently raise `NotImplementedError` — they are stubs with docstrings pointing back to the spec. The CLI subcommand wiring in [cli.py](src/dualbalance/cli.py) is real and tested.

## Common commands

```powershell
pip install -e ".[dev]"       # editable install with dev tooling (pytest, ruff)
pytest                         # run the test suite
pytest tests/test_cli.py::test_subcommand_help_parses[generate]   # single test
ruff check .                   # lint
ruff format .                  # format
dualbalance --help             # see subcommands once installed
```

Geospatial dependencies (geopandas, shapely, etc.) are intentionally **not** declared yet — add them to `pyproject.toml` only when code that uses them lands. Same rule for any other runtime dep.

## What the project is

DualBalance Districting is a deterministic redistricting algorithm. Given a state boundary, census block data, and a fixed district count `N`, it produces a district map that weights population balance and geographic-area balance equally. There is no randomness and no manual adjustment — same input always yields the same output.

Two-level structure to keep in mind when designing modules:

- **National apportionment** assigns each state its district count `N_s` using the Method of Equal Proportions, where `priority(s, n) = population(s) / sqrt(n(n+1))`.
- **State-level districting** runs the DualBalance algorithm independently inside each state to produce `N_s` districts.

The scoring harness is intentionally decoupled from the generator: it must be able to score any plan (enacted, court-drawn, third-party) using the same metrics applied to DualBalance's own output.

## Core algorithm invariants

These are non-negotiable properties the implementation must preserve. Check every design decision against them:

- **Deterministic.** No RNG, no wall-clock dependence. Tie-breaking follows the fixed cascade in [Formalism.md](Formalism.md): lower population error → lower area error → shorter seed distance → smaller district ID → smaller block ID.
- **Equal weighting.** Population and area penalties share the same coefficient (`β = γ` in the formalism). Treat any asymmetry as a bug unless the user is explicitly exploring a hybrid.
- **Block-level atomicity.** Districts are unions of whole census blocks; boundaries follow block boundaries.
- **Contiguity, non-empty, full coverage.** Every block belongs to exactly one district; every district is contiguous and non-empty.
- **Out of scope inputs.** Politics, race/demographics, communities of interest, competitiveness — the generator must not read these. Partisan metrics may be *reported* by the scoring harness but never fed back into the generator.

## Objective function

Minimize over districts `D_i`:

```
Σ_i [ α · compactness_cost(D_i)
    + β · |Pop(D_i)  − P*| / P*
    + β · |Area(D_i) − A*| / A* ]
```

with targets `P* = P/N` and `A* = A/N`. The reported **DualBalance Score** is `1 / (1 + population_error + area_error)`.

## Expected outputs

When the generator is built, a single run should emit (per [README.md](README.md)):

- `map.geojson` — district boundaries
- `metrics.json` — raw scoring data
- `report.html` — visual summary
- `comparison.json` — benchmark across plans (when comparing)
- `national_map.geojson` — optional combined multi-state output

## Manuscript

The [manuscript/](manuscript/) directory holds a LaTeX write-up of the method, kept under version control alongside the code. Structure: `main.tex` includes `sections/{introduction,methods,results,discussion}.tex` and `references.bib`; figures go in `figures/`. Build with `pdflatex main.tex` (run twice, with `bibtex main` in between, to resolve citations). Methods should mirror [Formalism.md](Formalism.md) — if one changes, update the other.
