# DualBalance Districting

A deterministic alternative to gerrymandering.

## Why this exists

Partisan gerrymandering is structurally entrenched and getting worse.
*Rucho v. Common Cause* (2019) foreclosed federal review of partisan
maps. *Alexander v. NAACP* (2024) and *Louisiana v. Callais* (April
2026) substantially narrowed Section 2 of the Voting Rights Act,
leaving race-conscious districting in a tighter constitutional
window than at any point since the VRA's adoption. With federal
partisan review off the table and federal racial review constrained,
several states have begun redrawing maps mid-decade in response to
electoral results rather than census revision. Redistricting is
shifting from a once-per-decade event into a continuous partisan
exercise.

DualBalance Districting starts from a different premise:

> If a human draws the lines, the lines can be drawn to advantage
> the human's party. The only structurally honest response is to
> remove the human from the line-drawing.

The algorithm is a pure function of the state's geometry, census
populations, and apportioned district count. No tuning knobs, no
random seed, no iteration count. Same input → same output,
byte-identical, every time. The map updates only with the decennial
census.

## The bicameral motivation

The U.S. Constitution divides representation along two axes: the
House apportions seats by population (Art. I §2); the Senate by
sovereign state regardless of population (Art. I §3). Madison's
defense in *Federalist* 54–58 reads this as a principled refusal to
collapse representation onto a single dimension.

We don't claim the Senate represents land area; it represents
states. What we take from the bicameral compromise is a weaker
intuition: *within* a chamber, the choice to make districts equal in
only one extensive quantity — population — is a choice, not a
necessity. A second extensive quantity, geographic area, is
available and computable from the same data. A district that spans
both metropolitan and rural territory forces each representative to
answer to constituents across the state's density range, rather than
to a single dense metro or a single rural hinterland.

Real states are not uniform in population density: a typical state
varies by two to three orders of magnitude between its densest urban
tract and its sparsest rural one. Equal population, equal area,
contiguity, and compact shape are not simultaneously achievable in
general. Some trade-off is unavoidable. The question is which
trade-off to make, how transparently to make it, and whether the
resulting procedure can be defended as impartial.

## Generative metrics, not forensic ones

The mathematical-gerrymandering literature has produced a large
catalog of metrics: Polsby-Popper and Reock compactness, the
Efficiency Gap, mean-median, declination, ensemble outlier methods
from Duke and the MGGG Redistricting Lab. All of these are
**forensic**: they take an enacted plan as input and ask whether its
properties are consistent with maps that some reference process —
random redistricting, ensemble sampling — would have produced
absent partisan intent. They are differential, comparing the enacted
plan against a counterfactual distribution to infer the
line-drawer's motive.

A **generative** metric is a different object. It states, directly,
what a district *should* look like, and is used as the objective the
line-drawing procedure pursues, rather than as evidence about that
procedure. Population balance is the only generative metric U.S.
redistricting law currently uses; *Wesberry* and *Reynolds* require
each district to hold roughly 1/N of the relevant population. Every
other criterion enters the law as a forensic instrument.

This matters because forensic metrics presuppose a line-drawer to
investigate. Removing the line-drawer — replacing it with a
deterministic generator — preserves their descriptive role but
evacuates their inferential content. There is no intent to infer. We
need a generative criterion.

**The DualBalance Score (DBS)** is that criterion:

$$
\mathrm{DBS} = \frac{1}{1 + 0.5\,\overline{\mathrm{pop\_dev}} + 0.5\,\overline{\mathrm{area\_dev}}}
$$

where `pop_dev_d = |Pop(d) − P*| / P*` and `area_dev_d = |Area(d) − A*| / A*`,
averaged over districts. DBS reaches 1.0 for a perfectly balanced plan
and approaches 0 as deviations grow. It is the objective the
algorithm minimizes against, not a test it must pass after the fact.

## Does Iowa's approach generalize?

Iowa's Legislative Services Agency operates under a written
procedure that has been in continuous use since 1980:
county-aggregating, deterministic, no judicial back-and-forth in
recent cycles. A natural question is whether the same procedure
would work elsewhere.

Empirically, the algorithm's behavior is sensitive to the input
geography. Iowa is unusually homogeneous: 99 counties, no county
exceeding the per-district population cap, no metropolitan area
large enough to dominate state politics. We re-implemented the
procedure (we call it **Cascade** in this repo to avoid confusion
with the agency) and ran it on six states:

| State | Cascade pop_dev_max |
|---|---|
| IA | 0.29% — clean |
| WI | 0.50% |
| NC | 10.27% |
| TX | 24.58% |
| MA | 41.56% |
| MN | 76.14% |

The county-integrity priority that produces clean maps in Iowa --
where no county is too large -- produces unconstitutional maps in
any state with a county large enough to swallow a district. The
Iowa procedure is exemplary for the geographic conditions in which
it was designed; on these results, it is not a transplantable
template.

A deterministic procedure that hopes to scale to the full set of
states needs a different structural commitment.

## The algorithm

### PRISM: deterministic single-pass core

Three steps, no iteration:

1. **Radial seed placement.** Compute the population-weighted
   centroid of the units. Place `N` seeds on a small circle around
   that centroid (radius = 0.1% of the bounding-box diagonal) at
   equally-spaced angles `2π·d/N`. Seed 0 points due east; seeds
   advance counter-clockwise.
2. **Capacitated first-fit assignment.** Sort all `(unit, district)`
   pairs by normalized Euclidean distance ascending; assign each
   unit to its first district with remaining population capacity
   `P* = total_population / N`. Population balance is enforced as a
   hard cap, not a soft penalty.
3. **Contiguity repair.** For any district whose dual-graph subgraph
   is disconnected, dissolve the smaller components into adjacent
   districts by lowest-cost transfer.

The radial configuration is what carries the dual-balance property:
each slice spans both dense (near-center) and sparse (boundary-side)
territory.

### Multi-resolution refinement (the path to Karcher)

Pure radial typically leaves a few percent per-district population
deviation, well above the ~0.05% practical *Karcher v. Daggett*
threshold for congressional districts. We close that gap
deterministically.

**Phase 1 (pop tightening).** Greedy local search of boundary-unit
moves. Each accepted move either reduces the L¹ sum of |pop_dev| or
strictly reduces `pop_dev_max`. When single-unit moves stall in a
multi-tied-max local optimum, a length-2 then length-3
**augmenting-chain escape** — the deterministic analogue of an
ejection chain — searches for a transport sequence on the
district-adjacency graph that the 1-opt neighborhood cannot express.

**Phase 2 (DBS hill-climb).** Once Phase 1 converges, picks the
boundary move that maximally improves DBS, subject to `pop_dev_max`
not exceeding the value Phase 1 reached.

**Block-scale refinement.** Phase 1 at VTD scale can stall above
Karcher because typical VTDs are too large (avg ~1000–3000 people)
to make sub-Karcher pop adjustments. We re-initialize at Census
block scale by inheriting each block's district from its containing
VTD (a deterministic spatial join), then re-run the optimizer at
block granularity. Block populations average ~20 people, so Phase 2
has the room it needs to refine area balance under the same pop
budget.

To make block-scale tractable, the contiguity check is cached:
[contiguity.py](src/dualbalance/contiguity.py) maintains per-district
articulation points via Tarjan on CSR adjacency arrays
(numba-accelerated when available), reducing each candidate
contiguity check from `O(V + E)` to `O(1)` and giving a 28× speedup
on the per-move cost compared to a networkx baseline.

All phases are deterministic. The full pipeline is a pure function
of `(state geometry, census populations, N, Karcher tolerance)`.

## Results

Six-state validation (MN, IA, MA, NC, WI, TX), block-scale,
refinement from VTD-Karcher init at 0.05% tolerance:

| State | N | DualBalance DBS | Enacted DBS | DualBalance pop_dev_max | Enacted pop_dev_max |
|---|---|---|---|---|---|
| IA | 4 | **0.9651** | 0.8828 | **0.05%** ✓ | 0.007% |
| MA | 9 | **0.8124** | 0.7246 | 0.10% | 0.62% |
| MN | 8 | **0.6613** | 0.6391 | 0.06% | 1.32% |
| NC | 14 | **0.7972** | 0.7689 | 0.08% | 0.66% |
| WI | 8 | 0.6953 | 0.7410 | **0.04%** ✓ | 0.08% |
| TX | 38 | **0.7077** | 0.6658 | 0.52% | 2.61% |

(✓ = below 0.05% Karcher line.)

**Headline reads:**
- **5 of 6 beat enacted on DBS.** WI is the one loss.
- **5 of 6 beat enacted on `pop_dev_max`.** Only IA's enacted plan is
  tighter; we sit exactly at Karcher.
- **More partisan-fair than enacted in 4 of 6** (efficiency gap
  smaller in magnitude on IA, NC, WI, TX; tied on MA, MN).
- **More minority-majority districts than enacted on NC (2 vs 1)
  and TX (22 vs 19).**

See [out/comparison_block.png](out/comparison_block.png),
[out/comparison_race.png](out/comparison_race.png), and
[out/comparison_partisan.png](out/comparison_partisan.png) for the
side-by-side plots vs Cascade and enacted.

## What this does NOT do

By design:

- Does not consider political parties
- Does not consider race or demographics
- Does not preserve "communities of interest"
- Does not optimize for competitiveness
- Does not iterate, tune, or anneal

These are all sources of human interpretation — and therefore bias.
The procedural neutrality is symmetric: the algorithm cannot be
tuned to advantage any group, and equally cannot be tuned to help
any of them.

## Quick start

```powershell
pip install -e ".[dev]"
pytest                                                # 106 tests, ~2s

# Per-state PoC end-to-end (any state in dualbalance.states.STATE_INFO)
python scripts/prep_state_units.py --state MN
dualbalance generate --config configs/mn_vtd.yaml     # PRISM core, raw
python scripts/compare_state.py --state MN            # vs Cascade, BDistricting, enacted

# Full block-scale refinement pipeline (the headline numbers)
python _test_block_from_vtd.py MN 8                   # VTD-Karcher -> block

# All 50 states in one resumable loop
python -u _run_all_states.py
```

## Apportionment

DualBalance includes a deterministic apportionment step that assigns
each state its district count using the **Method of Equal
Proportions** (the U.S. standard since 1941):

```
priority(s, n) = population(s) / sqrt(n(n+1))
```

The two-level system:

- National level → population-based apportionment across states
- State level → DualBalance districting within each state

## Output

For each run:

- `map.geojson` — one feature per atomic unit with `district_id`
- `metrics.json` — DBS, per-district populations and areas,
  compactness, partisan and race diagnostics; deterministic and
  byte-identical for repeated runs

```powershell
dualbalance score --plan some_plan.geojson --units state_units.geojson --geography vtd
```

## Limitations and legal exposure

- **Population × area cannot both reach exact balance on real US
  geography.** Density varies by ~300× between urban cores and rural
  counties, so any contiguous-unit partition has a hard floor on
  `area_dev_mean`. DBS reaches 1.0 only for uniform-density states.
- **Compactness scores will be lower than the hand-drawn norm.**
  Radial slices are deliberately not blob-shaped. Courts have used
  compactness in race-based gerrymandering cases (*Shaw v. Reno*
  and progeny), but those cases turn on intent, not geometry per
  se. A race-blind, content-neutral generator does not carry the
  intent that triggers *Shaw*.
- **Section 2 of the VRA has been substantially narrowed** by
  *Alexander* (2024) and *Callais* (2026), but is not formally
  struck down. A race-blind generator may not automatically satisfy
  Section 2 in jurisdictions where the *Gingles* preconditions are
  met. The scoring harness flags this risk without compromising the
  generator's content-neutrality.

See [docs/legal-standards.md](docs/legal-standards.md) for the case
law overview and [docs/stuck-state-problem.md](docs/stuck-state-problem.md)
for the chain-escape problem statement that motivated the
augmenting-path Phase 1.

## Design principles

- Deterministic over stochastic
- Transparent over heuristic
- Reproducible over negotiable
- Generative criteria over forensic ones
- No tuning knobs over many configurable parameters
