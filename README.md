# DualBalance Districting

A deterministic alternative to gerrymandering.

## Why this exists

Modern redistricting is fundamentally unstable.

Maps are routinely drawn to favor one group over another — whether political, geographic, or demographic. Even when done "fairly," the process depends on human judgment, negotiated criteria, and iterative adjustment. The result is predictable: bias enters the system.

DualBalance Districting starts from a different premise:

> If humans draw the lines, bias is inevitable.

So this project removes that step entirely.

## Core idea

DualBalance is a deterministic algorithm that generates district maps from first principles:

- Equal population representation
- Equal geographic representation
- No randomness
- No manual adjustment
- No subjective criteria

It is inspired by the structural balance already present in U.S. governance:

- The House → population-based representation
- The Senate → geography-based representation

DualBalance applies that same philosophy *within a single districting system*.

## What it does

Given:

- A state boundary
- Census-level population data
- A fixed number of districts

DualBalance produces:

- A complete district map
- With equal weighting of population and land area
- Using a fully deterministic process

Same input → same output. Every time.

## What it does NOT do

- Does not consider political parties
- Does not consider race or demographics
- Does not preserve "communities of interest"
- Does not optimize for competitiveness

Those are all sources of human interpretation — and therefore bias.

## Algorithm (high level)

Formally, this is a population-center Voronoi districting algorithm. See [Formalism.md](Formalism.md) for the precise mathematical statement.

1. **Identify population centers:** major cities, census-defined urban areas, or population-weighted centroids.
2. **Choose seed points:** place `N` seeds so they are spaced equidistantly from one another or from major population centers.
3. **Assign every census block:** each block goes to the nearest seed by geographic distance.
4. **Recalculate each seed:** move it to the population-weighted centroid of its assigned blocks.
5. **Repeat until stable.**
6. **Repair boundaries:** enforce contiguity and adjust for population/area targets.

Population and area are weighted equally in the objective.

## Representation allocation (apportionment)

DualBalance extends beyond district drawing. It can also incorporate a deterministic method for assigning the total number of districts per state based on census population.

This mirrors how representation in the U.S. House is apportioned every 10 years.

### Method

Given:

- Total U.S. population (from census)
- Fixed number of seats (e.g., 435)
- State populations

Seats are assigned using a deterministic apportionment algorithm.

By default, DualBalance uses the **Method of Equal Proportions** (the current U.S. standard):

1. Each state receives one seat.
2. Remaining seats are assigned iteratively.
3. At each step, assign the next seat to the state with the highest priority value:

```
priority(s, n) = population(s) / sqrt(n(n+1))
```

where `s` is a state and `n` is the current number of seats assigned to that state.

This produces a fully deterministic distribution of representatives across states.

### Integration with districting

Once seats are assigned:

1. Each state receives `N_s` districts.
2. DualBalance is applied independently within each state.
3. Each state's districts are generated using equal population (within state) and equal geographic area (within state).

This creates a two-level system:

- National level → population-based apportionment across states
- State level → balanced population + geography districting

### Resulting structure

The system mirrors existing U.S. representation but removes discretionary boundary drawing:

- Apportionment remains population-driven
- Districting becomes deterministic and bias-minimized

### Optional extensions

DualBalance can also explore alternative apportionment rules:

- Pure population proportionality (fractional or continuous models)
- Geography-weighted apportionment (experimental)
- Hybrid models combining population and land area at the national level

These are not enabled by default but provide a research framework for exploring different representation systems.

## Output and evaluation

DualBalance produces both district maps and a full evaluation report.

The goal is not only to generate a map, but to measure how that map performs relative to existing plans and alternative algorithms.

### Outputs

For each run, DualBalance generates:

- `map.geojson` — district boundaries
- `metrics.json` — raw scoring data
- `report.html` — visual summary
- `comparison.json` — benchmark comparison across plans
- `national_map.geojson` — optional combined multi-state output

### Scoring harness

DualBalance includes a built-in scoring system to evaluate any districting plan, including:

- Enacted maps
- Court-drawn maps
- Public submissions
- Maps generated by other algorithms

### Primary metrics

Population balance:

- Mean population deviation
- Maximum population deviation

Geographic balance:

- Mean area deviation
- Maximum area deviation

**DualBalance Score:**

```
DualBalance Score = 1 / (1 + population_error + area_error)
```

This is the defining metric of the system, treating population and land area equally.

### Secondary metrics

Reported but not optimized directly:

- Compactness (Polsby-Popper, Reock)
- Contiguity validation
- County and municipal splits
- Boundary length / fragmentation

Optional:

- Partisan metrics (efficiency gap, bias, seats-votes curve)

### Benchmarking

DualBalance can compare its output against multiple plans:

```
dualbalance compare --state MN --plans ./plans/
```

This produces:

- Rank ordering across metrics
- Pairwise comparisons
- Distance from DualBalance baseline
- Sensitivity to population vs. geography trade-offs

### Interpretation

The scoring harness is intentionally separate from the generator.

DualBalance does not claim to define fairness universally. Instead, it provides:

> A measurable, reproducible baseline for evaluating district maps.

This allows users to answer:

- How does an enacted map compare to a deterministic baseline?
- Where does it deviate (population, geography, compactness)?
- What trade-offs were made, and how large are they?

### Evaluation criteria

Any districting system should be judged by:

- What it optimizes
- What it ignores
- How reproducible its results are

DualBalance makes all three explicit.

## Fairness philosophy

DualBalance does not attempt to define fairness in political terms.

Instead, it enforces a structural constraint:

> Representation should reflect both people and place.

Pure population-based systems concentrate influence in dense regions. Pure geography-based systems over-weight sparsely populated land. DualBalance sits between these extremes.

## Design principles

- Deterministic over stochastic
- Transparent over heuristic
- Reproducible over negotiable
- Structural balance over subjective fairness

## Limitations

- Equal population and equal land area are inherently in tension
- Results may not align with legal requirements in all jurisdictions
- Does not encode social or political considerations
