# DualBalance Districting

A deterministic alternative to gerrymandering.

## Why this exists

Partisan gerrymandering is entrenched. The Supreme Court's
*Rucho v. Common Cause* (2019) foreclosed federal review of partisan
maps; *Allen v. Milligan* (2023) reaffirmed Section 2 of the Voting
Rights Act, but *Alexander v. NAACP* (2024) and *Louisiana v. Callais*
(April 2026) have significantly narrowed Section 2's reach in practice.
The combined effect is that, in most states, partisan map-drawing is
both federally unreviewable and racially constrained — and several
states have already begun redrawing maps mid-decade in response to
electoral results rather than census revision. Redistricting is moving
from a once-per-decade event into a continuous partisan exercise.

DualBalance Districting starts from a different premise:

> If humans draw the lines, bias is inevitable.

So this project removes that step entirely. The algorithm is a pure
function of two inputs: the state's geometry (from the decennial
census) and the state's apportioned district count. It has no tuning
knobs, no random seed, and no iteration count. Same input → same
output, byte-identical, every time. The map updates only when the
underlying census changes — once every ten years.

## Core idea

DualBalance reframes congressional districts so that each district
carries both representation principles the U.S. Constitution embeds at
the federal level:

- The House → population-based representation (Art. I §2)
- The Senate → geography-based representation (Art. I §3)

Within a single districting system, every district holds roughly 1/N
of the state's people *and* a coherent slice of the state's
geography. Seats are placed radially around the population-weighted
centroid of the state, producing pie-slice districts that each span
both dense and sparse territory. Population balance is enforced as a
hard cap; area balance emerges from the radial geometry.

## What it does

Given:

- A state boundary
- Census-unit population data
- A fixed number of districts (apportioned via Method of Equal Proportions)

DualBalance produces:

- A complete district map (`map.geojson`)
- The DualBalance Score and supporting metrics (`metrics.json`)

Using a fully deterministic, single-pass pipeline.

## What it does NOT do

- Does not consider political parties
- Does not consider race or demographics
- Does not preserve "communities of interest"
- Does not optimize for competitiveness
- Does not iterate, tune, or anneal

These are all sources of human interpretation — and therefore bias.

## Algorithm

A deterministic three-step pipeline. See [docs/Formalism.md](docs/Formalism.md)
for the precise mathematical statement.

1. **Radial seed placement.** Compute the population-weighted
   centroid of the units. Place `N` seeds on a small circle around
   that centroid (radius = 0.1% of the bounding-box diagonal) at
   equally-spaced angles `2π·d/N` for `d = 0, …, N-1`. Seed 0 points
   due east; seeds advance counter-clockwise.
2. **Capacitated first-fit assignment.** Sort all `(unit, district)`
   pairs by normalized Euclidean distance ascending; assign each
   unit to its first district with remaining population capacity
   `P* = total_population / N`. Ties on distance break by
   `(unit_id asc, district_id asc)`. Population balance is enforced
   as a hard cap, not a soft penalty.
3. **Contiguity repair.** Build the rook-adjacency dual graph; for
   any district whose induced subgraph has more than one connected
   component, dissolve the smaller components into adjacent districts
   by lowest-cost transfer.

There is no Lloyd iteration, no recentering loop, no tightening pass
in the core pipeline. The radial seed positions do not drift, so a
single assignment pass suffices. The CLI exposes no algorithmic
tuning flags for the core pipeline — only data-plumbing arguments
(`--units`, `--districts`, `--geography`, `--out`, `--config`).

The MN PoC scores **0.6472** under DualBalance, beating the enacted
119th-Congress plan's **0.6390** by 1.3%. See
[docs/mn-poc-walkthrough.md](docs/mn-poc-walkthrough.md) for the
worked example with reproduction commands.

### Optional: `--tighten-pop` for Reynolds compliance

Pure radial leaves per-district `pop_deviation_max` around 5–15 % —
well above the ~0.5 % *Reynolds v. Sims* threshold required for U.S.
congressional districts. An opt-in `--tighten-pop` flag (with
`--pop-tolerance T`, default 0.5 %) runs a greedy boundary-unit swap
pass that drives `pop_deviation_max` down to the target. On the MN
PoC, this brings the max from 11.24 % to 0.21 %, raises the
DualBalance score from 0.6472 to 0.6574, and preserves the radial
structure (units move only at slice boundaries). The pass is off by
default because it is the only piece of the pipeline that is not a
pure function of `(units, n_districts)`; turning it on is a
project-level choice about whether to trade a small degradation of
the visible radial guarantee for legal compliance.

## Apportionment

DualBalance includes a deterministic apportionment step that assigns
each state its district count using the **Method of Equal Proportions**
(the current U.S. standard since 1941):

```
priority(s, n) = population(s) / sqrt(n(n+1))
```

Given total seats (e.g. 435), each state receives one seat to start,
and remaining seats are assigned iteratively to the state with the
highest priority value. The result is fully deterministic.

The two-level system:

- National level → population-based apportionment across states
- State level → DualBalance districting within each state

## Output and evaluation

For each `dualbalance generate` run:

- `map.geojson` — one feature per atomic unit with `district_id` property
- `metrics.json` — DualBalance Score, per-district populations and areas,
  compactness metrics, deterministic and byte-identical for repeated runs

The scoring harness is intentionally decoupled from the generator: any
plan (enacted, court-drawn, third-party) can be scored against the
same metrics applied to DualBalance's own output:

```
dualbalance score --plan some_plan.geojson --units state_units.geojson --geography vtd
```

### DualBalance Score

```
DualBalance Score = 1 / (1 + 0.5 · pop_deviation_mean + 0.5 · area_deviation_mean)
```

where `pop_deviation_d = |Pop(d) - P*| / P*` and similarly for area,
averaged over districts. The 0.5/0.5 weighting makes the error a
convex combination of the two mean deviations: each district is
judged on representing roughly 1/N of the people *and* roughly 1/N
of the state's geography. The score reaches 1.0 for a perfectly
balanced plan and approaches 0 as deviations grow.

### Secondary metrics

Reported but not optimized:

- Polsby-Popper compactness
- Reock compactness

Radial slices have lower compactness than blob-Voronoi or hand-drawn
districts by construction; this is a deliberate trade for the
dual-balance objective, not a bug.

## Limitations

- Population and area cannot both reach exact balance on real US
  geography. State population densities vary by ~300× between urban
  cores and rural counties, so any contiguous-unit partition has a
  hard floor on `area_dev_mean`.
- Compactness scores will be lower than the hand-drawn norm. Courts
  have used compactness as evidence in race-based gerrymandering
  cases (*Shaw v. Reno* and progeny), but those cases turn on intent,
  not geometry per se. A deterministic, race-blind, content-neutral
  generator does not carry the racial intent that triggers *Shaw*.
- Section 2 of the Voting Rights Act has been substantially narrowed
  by *Alexander* (2024) and *Callais* (2026), but is not formally
  struck down. A race-blind generator may not automatically satisfy
  Section 2 in jurisdictions where the *Gingles* preconditions are
  met; the scoring harness flags this risk without compromising the
  generator's content-neutrality.

## Design principles

- Deterministic over stochastic
- Transparent over heuristic
- Reproducible over negotiable
- Structural balance over subjective fairness
- No tuning knobs over many configurable parameters
