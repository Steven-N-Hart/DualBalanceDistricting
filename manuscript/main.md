---
abstract: |
  Partisan gerrymandering is structurally entrenched. Federal courts
  cannot review it after *Rucho v. Common Cause*, and forensic metrics
  can document manipulation only after it has occurred. What if
  congressional districts were drawn not by legislators, but by a fully
  specified mathematical rule with no human discretion at any stage?

  We propose and test *DualBalance Districting*: a deterministic
  algorithm that computes districts as a pure function of state
  geometry, census population, and seat count $`N`$, with no
  discretionary parameters and no political inputs. Every design choice
  is pre-committed before any state’s data are examined. Each district
  carries roughly $`1/N`$ of the state’s people *and* $`1/N`$ of its
  land, weighted equally in the DualBalance Score.

  Applied to all 41 multi-seat states with available VTD data, the
  algorithm achieves *Karcher*-compliant population balance on 26
  states; both deterministic baselines achieve it on zero. Districts are
  substantially less compact than enacted plans (median Polsby-Popper
  0.115 vs. 0.281), a structural cost of spanning the full urban-rural
  gradient. A rotation sensitivity analysis finds the DualBalance Score
  stable across anchor angles (cross-state median $`\sigma = 0.010`$)
  while projected seat counts shift by 1–3 seats in 26 of 41 states,
  identifying seed rotation as a consequential pre-committed design
  choice requiring a legislatively specified rule.

  This paper demonstrates feasibility and documents the properties of an
  apolitical deterministic design. Whether such a rule constitutes fair
  representation is a normative question the algorithm cannot answer;
  that judgment belongs to legislatures, courts, and voters.
author:
- Steven Hart
bibliography: references.bib
date: 2026-05-17
title: |
  DualBalance Districting:\
  From Detection to Generation
---

# Introduction

In most U.S. states, congressional district boundaries are drawn by the
same legislators whose electoral prospects depend on where those
boundaries fall. This structural conflict of interest is not resolved by
the Constitution, which mandates only that House districts achieve
population balance (Art. I, §2) while leaving every other line-drawing
decision to political actors. The consequences are well-documented:
gerrymandered boundaries reduce electoral competition, dilute minority
voting power, and produce seat allocations that diverge substantially
from statewide vote totals (Stephanopoulos and McGhee 2015; Chen and
Rodden 2013). Federal judicial oversight of these practices has
progressively narrowed, as detailed in
§<a href="#sec:intro-legal" data-reference-type="ref"
data-reference="sec:intro-legal">1.1</a> below. This paper proposes and
validates *DualBalance Districting*: a deterministic algorithm that
computes congressional district maps as a pure function of state
geometry, census populations, and district count $`N`$, with no
discretionary parameters, no randomness, and no human intervention at
any stage. Each district is designed to carry approximately $`1/N`$ of
the state’s population and approximately $`1/N`$ of its land area,
weighted equally in a single objective we call the DualBalance Score. A
deterministic algorithm with pre-committed, publicly documented rules
provides, by construction, a mathematical barrier against ad hoc map
manipulation: every design choice is fixed before any specific state’s
data are examined, so no choice can be made after the fact to favor a
party or candidate.

## Redistricting Without a Neutral Standard

The federal courts have largely withdrawn from gerrymandering review. In
*Rucho v. Common Cause* (Supreme Court of the United States 2019), the
Supreme Court held 5–4 that partisan-gerrymandering claims present
nonjusticiable political questions; the Court conceded the practice is
“incompatible with democratic principles” but found no manageable
judicial standard. After *Rucho*, the only federal channel for
gerrymandering review is racial. That channel has since narrowed.
Section 2 of the Voting Rights Act, as construed in *Thornburg
v. Gingles* (Supreme Court of the United States 1986), requires
majority-minority districts where the three Gingles preconditions are
met. The Court reaffirmed this in *Allen v. Milligan* (Supreme Court of
the United States 2023a). One year later, *Alexander v. South Carolina
Conf. of the NAACP* (Supreme Court of the United States 2024) raised
plaintiffs’ evidentiary burden; *Louisiana v. Callais* (Supreme Court of
the United States 2026) held in April 2026 that even a plan drawn to
comply with a prior Section 2 order may violate the Equal Protection
Clause if Section 2 did not in fact compel a race-based remedy.
Together, *Alexander* and *Callais* leave race-conscious line-drawing in
a narrower window of constitutional safety than at any point since the
VRA’s adoption.

State constitutional review under *Moore v. Harper* (Supreme Court of
the United States 2023b) remains available but is uneven and politically
contingent: roughly ten state supreme courts have recognized
state-constitutional partisan-gerrymandering claims (Pluta, Robbie
2025); the rest have not. Several states have already redrawn maps
mid-decade in response to electoral results rather than census revision,
shifting redistricting from a once-per-decade event into a recurring
one. Reducing this discretionary intervention requires a procedure whose
output is determined entirely by census data, with no human choices at
the line-drawing stage.

## Population and Geography as Dual Representational Axes

The Constitution already encodes two theories of representation: the
House apportions seats by population (Art. I, §2), the Senate by
sovereign state regardless of population (Art. I, §3). Madison’s defense
in *Federalist* Nos. 54–58 (Madison 1788) frames the bicameral structure
as a principled refusal to collapse representation onto a single
dimension. Within the House, the existing framework uses only one
extensive quantity, population, to define what a district should be.
Geographic area is a second extensive quantity: it is well-defined,
measurable from the same census geometry, and orthogonal to population
density. Balancing area alongside population discourages concentration
of districts exclusively within either dense metropolitan cores or
sparse rural regions.

The Electoral College illustrates how the founders embedded both
principles within a single institution. Each state’s electoral vote
total equals its House seats plus its two Senate seats (Art. II, §1),
blending a population-proportional component with a geographic floor.
The analogy operates at the level of constitutional design philosophy,
not mechanical equivalence: the Electoral College combines the two
principles *across* states, allocating a fixed geographic bonus between
them, while DualBalance applies them *within* a single state’s
districts. The design logic is the same regardless, a constitutional
order that declines to collapse representation onto a single extensive
quantity.

This is a mathematical challenge, not a free choice. A typical
U.S. state varies by two to three orders of magnitude between its
densest census tract and its sparsest rural block. Equal population,
equal area, contiguity, and shape compactness cannot all be satisfied
simultaneously in general; some trade-off is unavoidable. The question
is which trade-off to make, how transparently to make it, and whether
the resulting procedure can be defended as impartial.

## Existing Metrics Are Forensic, Not Generative

Quantitative tests for gerrymandering include shape-compactness measures
(Polsby-Popper (Polsby and Popper 1991); Reock (Reock 1961)),
partisan-asymmetry statistics (Wang 2016; Warrington 2018), the
Efficiency Gap (Stephanopoulos and McGhee 2015), and ensemble outlier
methods (Herschlag et al. 2020; DeFord et al. 2021). We report
Polsby-Popper, Reock, and the Efficiency Gap (EG) as comparative
benchmarks in §<a href="#sec:results" data-reference-type="ref"
data-reference="sec:results">3</a>. EG, defined formally in
§<a href="#sec:methods" data-reference-type="ref"
data-reference="sec:methods">2</a>, measures the difference between the
two parties’ wasted-vote totals as a fraction of statewide turnout; it
has received the widest adoption in federal redistricting litigation,
serving as the central metric in *Whitford v. Gill*, with
$`|\mathrm{EG}| > 0.07`$ proposed as a threshold for a plausible
partisan-gerrymandering challenge (Stephanopoulos and McGhee 2015). All
of these metrics are *forensic* instruments: they take an enacted map as
input and ask whether its observed properties (shape, vote efficiency,
partisan asymmetry, the location of its seat–vote curve) are consistent
with maps that some reference process (random redistricting, ensemble
sampling under legal constraints) would have produced absent partisan
intent. They compare the enacted plan against a counterfactual
distribution to infer the line-drawer’s motive, and were built for an
adversarial context in which the question is “did somebody do something
here that they should not have done?”

A generative metric is a different object. It states, directly, what a
district *should* look like, and is used as the objective of the
line-drawing procedure rather than as evidence about the procedure.
Population balance is the only generative metric U.S. redistricting law
currently uses: *Wesberry v. Sanders* (Supreme Court of the United
States 1964b) and *Reynolds v. Sims* (Supreme Court of the United States
1964a) require that each district hold roughly $`1/N`$ of the relevant
population. Every other criterion (compactness, communities of interest,
partisan fairness) enters the law as a forensic instrument or a
discretionary guideline.

The DualBalance Score (DBS;
equation <a href="#eq:dbs" data-reference-type="ref"
data-reference="eq:dbs">[eq:dbs]</a> in
§<a href="#sec:methods" data-reference-type="ref"
data-reference="sec:methods">2</a>) is a *generative* criterion: it
states what a district should be, one that carries roughly $`1/N`$ of
the people and roughly $`1/N`$ of the land, and serves as the objective
the algorithm pursues rather than a test applied after the fact.

## The Iowa Model as a Reference Point

Iowa’s Legislative Services Agency (Iowa Legislative Services Agency
2021) has operated under a written, publicly documented redistricting
procedure since 1980 – one of the few U.S. examples of a formalized,
procedural approach that has functioned without major legal challenge
across multiple redistricting cycles. Its longevity and transparency
make it a natural reference point for proposals to replace discretionary
redistricting with an explicit algorithm. The open question is whether a
procedure designed for Iowa’s geographic and demographic conditions
constitutes a legally defensible, impartial template for states with
substantially different population distributions and geographic
structure. We re-implement it as a structured baseline (referred to here
as *Cascade* to avoid confusion with the agency) and use it as a point
of comparison throughout. Cascade captures the geographic-prioritization
logic of the Iowa formula (county integrity first, then population
balance, then compactness) but omits the institutional framework (the
bipartisan advisory commission, multiple plan submissions, and
legislative up-or-down vote) that is integral to Iowa’s actual
redistricting process. The comparison therefore isolates the algorithmic
contribution of county-preservation, not the process surrounding it.

## Contribution

We propose *DualBalance Districting*: a deterministic multi-resolution
pipeline whose output is a pure function of
$`(\text{state geometry}, \text{census populations}, N)`$, formalized in
§<a href="#sec:methods" data-reference-type="ref"
data-reference="sec:methods">2</a>.

#### Pipeline.

The algorithm runs in three stages: radial seed placement around the
population-weighted centroid, followed by a two-phase greedy local
search at VTD scale that closes per-district population deviation toward
the *Karcher* threshold (Supreme Court of the United States 1983),
followed by the same search re-run at census-block scale where finer
granularity allows the DualBalance Score to make its largest gains. The
full formalization is in
§<a href="#sec:methods" data-reference-type="ref"
data-reference="sec:methods">2</a>.

#### Empirical validation.

We evaluate the full pipeline on all 41 multi-seat states for which
TIGER 2020PL VTD boundaries are available (California, Hawaii, and
Oregon are excluded for lack of VTD data). DualBalance achieves
*Karcher*-compliant population balance
($`\mathrm{pop\_dev\_max} \leq 0.05\,\%`$) on 26 of 41 states and
exceeds the enacted 119th-Congress plan on the DualBalance Score on 26
of 41 states. On partisan fairness, DualBalance reduces
$`|\mathrm{EG}|`$ relative to the enacted plan on 14 of the 20 states
with composite or congressional election data (median $`|\mathrm{EG}|`$
0.085 vs. enacted 0.133). On minority-majority district counts,
DualBalance produces at least as many as the enacted plan on most states
and more on several high-minority states, including TX (22 vs. 19
enacted) and NC (2 vs. 1 enacted).

#### Claims.

The procedure contains no explicit partisan, racial, or incumbent-aware
optimization criteria: its inputs are census geometry and population
totals, and its output is a pure function of those inputs. Every design
choice, including seed geometry, objective weighting, tolerance, and
tie-breaking, is pre-committed and fixed before any specific state is
examined. There are no in-session discretionary parameters that a
line-drawer could adjust to affect electoral or demographic outcomes.
Adopting a generative criterion as the design objective, rather than a
forensic instrument, is a natural response to a setting in which no
line-drawer is present to investigate. Scope limits and further
qualifications appear in
§<a href="#sec:discussion" data-reference-type="ref"
data-reference="sec:discussion">4</a>.

#### Roadmap.

Section <a href="#sec:methods" data-reference-type="ref"
data-reference="sec:methods">2</a> formalizes the algorithm.
Section <a href="#sec:results" data-reference-type="ref"
data-reference="sec:results">3</a> reports the 41-state empirical
validation. Section <a href="#sec:discussion" data-reference-type="ref"
data-reference="sec:discussion">4</a> discusses limits, trade-offs, and
legal exposure.

# Methods

## Data and inputs

Atomic units are U.S. Census Bureau *voting tabulation districts* (VTDs)
and *census tabulation blocks* from the 2020 decennial release (U.S.
Census Bureau 2021), obtained via TIGER/Line shapefiles (U.S. Census
Bureau 2020). Boundaries are used as-is; no simplification or smoothing
is applied. Population counts are the total-population figures from
PL 94-171. The enacted congressional plan used for comparison is the
119th-Congress plan (effective January 2025), joined to VTDs and blocks
via a spatial representative-point join against the TIGER 2024 `cd119`
layer (U.S. Census Bureau 2024).

#### Note on enacted-plan population deviations.

Enacted U.S. congressional plans are litigated to *Karcher* compliance
at the census-block level. The enacted-plan deviations reported in this
paper reflect the VTD-layer spatial join: a VTD that straddles a
district boundary is assigned in full to one district, introducing
apparent deviation where the legislative record shows none.
DualBalance’s reported deviations come from its own block-refined output
and are directly comparable to the *Karcher* threshold. Counts of
enacted-plan Karcher compliance
(Tables <a href="#tab:multistate-dbs" data-reference-type="ref"
data-reference="tab:multistate-dbs">1</a>–<a href="#tab:aggregate-comparison" data-reference-type="ref"
data-reference="tab:aggregate-comparison">2</a>) should be read as a
conservative lower bound on enacted compliance, not as legally
cognizable deviations: the true enacted deviations are near zero on
block-accurate data.

#### Reproducibility.

The `dualbalance` Python package, per-state configuration files
(`configs/`), and the data pipeline (`scripts/prep_state_units.py`)
reproduce all tables and figures from publicly available TIGER and
Census source files. Algorithm outputs are byte-identical across
repeated runs on the same input data; the `votes_source` field in each
state’s units file records which election data source was used.

## Problem statement

Given a state $`S`$ partitioned into atomic units
$`U = \{u_1, \ldots, u_M\}`$ (census tabulation blocks, block groups, or
voting tabulation districts (VTDs), in increasing order of size) and a
target district count $`N`$, DualBalance Districting produces a
deterministic assignment $`\pi : U \to \{1, \ldots, N\}`$ such that each
district $`D_i = \pi^{-1}(i)`$ is contiguous, non-empty, and as close as
the geometry allows to representing both $`1/N`$ of the state’s people
and $`1/N`$ of its geography. Let $`P = \sum_u \mathrm{pop}(u)`$ and
$`A = \sum_u \mathrm{area}(u)`$ with per-district targets $`P^* = P/N`$
and $`A^* = A/N`$.

The full pipeline runs in three stages: a radial-seed stage,
*DualBalance* (§§<a href="#sec:methods-seeds" data-reference-type="ref"
data-reference="sec:methods-seeds">2.3</a>–<a href="#sec:methods-repair" data-reference-type="ref"
data-reference="sec:methods-repair">2.5</a>), which provides the
deterministic starting configuration; a VTD-scale tightening stage
(§<a href="#sec:methods-optimize" data-reference-type="ref"
data-reference="sec:methods-optimize">[sec:methods-optimize]</a>) which
drives $`\max_i |\delta_i|/P^{*}`$ toward the user-supplied tolerance
$`\tau`$ via a hybrid greedy local search with bounded-chain escape; and
a block-scale refinement stage
(§<a href="#sec:methods-block" data-reference-type="ref"
data-reference="sec:methods-block">2.8</a>) which re-initializes at
finer granularity to recover area balance within the achieved
pop-deviation envelope. Each stage is a pure function of its inputs.

## Radial seed placement

Compute the population-weighted centroid
``` math
c = (c_x, c_y) =
  \left(
    \frac{\sum_u p_u\,x_u}{\sum_u p_u},\;
    \frac{\sum_u p_u\,y_u}{\sum_u p_u}
  \right),
```
where $`x_u, y_u`$ are the centroid coordinates of unit $`u`$ in an
equal-area projection and $`p_u`$ its population. Let $`\mathrm{diag}`$
denote the bounding-box diagonal of the units and set the seed radius
$`r = 0.001 \cdot \mathrm{diag}`$. For $`d = 0, 1, \ldots, N-1`$ place
seed $`s_d`$ at
``` math
s_d = \bigl(c_x + r\cos(2\pi d/N),\, c_y + r\sin(2\pi d/N)\bigr).
```
Seed 0 sits due east of the centroid; seeds advance counter-clockwise by
equal angular steps. The choice $`r = 0.001 \cdot \mathrm{diag}`$ is
small enough that the Voronoi cells generated by the seeds degenerate to
near-perfect radial slices through $`c`$, but large enough to keep the
seed positions numerically distinct.

These angular parameters, seed 0 due east and counter-clockwise advance,
are pre-committed design choices fixed before any state-specific data
are examined. Different anchor angles $`\theta \in [0,\,2\pi/N)`$
produce different partitions with different partisan and demographic
properties, because the resulting radial slices land differently on the
state’s population geography. Rotation sensitivity, i.e., the
distribution of DBS, $`|\mathrm{EG}|`$, and seat outcomes across the
full rotation range, is therefore an important robustness check; results
are reported in
§<a href="#sec:results-rotation" data-reference-type="ref"
data-reference="sec:results-rotation">3.1</a>. The due-east anchor was
selected as the natural zero of the standard angular convention; an
adopting body would need to pre-specify a rotation rule (or adopt this
one) as part of any legislative implementation.

The radial configuration is what carries the dual-balance property: each
slice spans both the dense (near-$`c`$) and sparse (boundary-side)
territory of the state, so the population it inherits is bounded by the
cap (§<a href="#sec:methods-assign" data-reference-type="ref"
data-reference="sec:methods-assign">2.4</a>) while the area it inherits
is driven toward $`A^*`$ by the slicing geometry.

## Capacitated first-fit assignment

Let $`d(u, i) = \|x_u - s_i\|`$ be the Euclidean distance from unit
$`u`$ to seed $`i`$. Initialize remaining capacities $`\rho_i = P^*`$
for $`i = 1, \ldots, N`$. Sort all $`(u, i)`$ pairs by ascending
normalized distance $`d(u, i) / \mathrm{diag}`$ and walk the sorted list
in order:
``` math
\begin{array}{l}
    \text{for each } (u, i)\text{ in ascending } d(u,i)/\mathrm{diag}: \\
    \quad \text{if $u$ already assigned: continue} \\
    \quad \text{if $\rho_i \geq p_u$: assign $u$ to $i$;\;\; }\rho_i \leftarrow \rho_i - p_u \\
    \quad \text{else: skip}
  \end{array}
```
Population balance is enforced as a hard cap: no district receives more
than $`P^*`$. Any unit not placed by the end of the walk (a rare
integer-rounding edge case) is assigned to the district with the largest
remaining capacity; `argmax` resolves ties to the smallest district id.

Ties in normalized distance break by ascending
$`(\mathrm{unit\_id},\,\mathrm{district\_id})`$. There is no Lloyd
recentering, no iteration count, no convergence test: the radial seeds
do not drift, so a single assignment pass suffices.

## Contiguity repair

After §<a href="#sec:methods-assign" data-reference-type="ref"
data-reference="sec:methods-assign">2.4</a> every unit belongs to
exactly one district, but a district may consist of more than one
connected component (rare on convex states; more common on those with
peninsulas, islands, or rural enclaves). For each such district, the
largest connected component by total population is retained; units in
the smaller components are reassigned to neighboring districts one at a
time, in the lowest-cost direction. Cost is
``` math
c(u, j) = \frac{d(x_u, s_j)}{\mathrm{diag}}
          + \frac{|P(D_j) + p_u - P^*|}{P^*}
          + \frac{|A(D_j) + a_u - A^*|}{A^*},
```
combining a normalized distance term with normalized population and area
deviation penalties for the receiving district. Ties break in cascade
$`(c, \mathrm{pop\_pen}, \mathrm{area\_pen}, \mathrm{dist},
\mathrm{district\_id})`$ ascending. The repair sweep iterates until no
district has more than one connected component, capped at ten sweeps; in
practice it converges in zero or one sweep on real census geometries.

Algorithm <a href="#alg:dualbalance" data-reference-type="ref"
data-reference="alg:dualbalance">[alg:dualbalance]</a> summarizes the
full core pipeline.

<div class="algorithm">

<div class="algorithmic">

Atomic units $`\mathcal{U}=\{u_1,\dots,u_M\}`$ with populations
$`\{p_u\}`$, centroids $`\{x_u\}`$, and areas $`\{a_u\}`$; district
count $`N`$ Assignment $`\pi:\mathcal{U}\to\{1,\dots,N\}`$; every
district contiguous and non-empty
$`c \leftarrow \bigl(\sum_u p_u\,x_u\bigr)\big/\bigl(\sum_u p_u\bigr)`$
$`P^* \leftarrow \bigl(\sum_u p_u\bigr)/N`$;
$`A^* \leftarrow \bigl(\sum_u a_u\bigr)/N`$
$`\Delta \leftarrow \mathrm{diag}\bigl(\mathrm{bbox}(\mathcal{U})\bigr)`$;
$`r \leftarrow 0.001\,\Delta`$ **Phase 1Radial seed placement**
$`s_d \leftarrow c + r\,\bigl(\cos(2\pi d/N),\;\sin(2\pi d/N)\bigr)`$
**Phase 2Capacitated first-fit assignment** $`\rho_i \leftarrow P^*`$
for all $`i`$; $`\pi(u) \leftarrow \varnothing`$ for all $`u`$ Sort
pairs $`(u,\,i)`$ by $`\|x_u - s_i\|/\Delta`$ ascending
$`\pi(u) \leftarrow i`$;$`\rho_i \leftarrow \rho_i - p_u`$ Assign each
unassigned $`u`$ to $`\arg\max_i\,\rho_i`$ **Phase 3Contiguity repair**
Let $`C`$ be the smallest component of district $`i`$
$`\mathrm{cost}(u,\,j) \leftarrow
               \dfrac{\|x_u - s_j\|}{\Delta}
               + \dfrac{|P(D_j)+p_u-P^*|}{P^*}
               + \dfrac{|A(D_j)+a_u-A^*|}{A^*}`$
$`\pi(u) \leftarrow \arg\min_j\;\mathrm{cost}(u,j)`$ for each
$`u \in C`$

</div>

</div>

## Scoring

Define per-district relative deviations
$`\mathrm{pop\_dev}_i = |P(D_i) - P^*|/P^*`$ and
$`\mathrm{area\_dev}_i = |A(D_i) - A^*|/A^*`$ and let
$`\overline{\mathrm{pop\_dev}}`$, $`\overline{\mathrm{area\_dev}}`$
denote their means over $`i = 1, \ldots, N`$. The DualBalance Score is
``` math
\begin{equation}
  \mathrm{DBS}
    = \frac{1}{1
       + \tfrac{1}{2}\,\overline{\mathrm{pop\_dev}}
       + \tfrac{1}{2}\,\overline{\mathrm{area\_dev}}}.
  \label{eq:dbs}
\end{equation}
```
The $`0.5/0.5`$ weighting makes the error a convex combination of the
two mean deviations: each district is judged on representing roughly
$`1/N`$ of the people *and* roughly $`1/N`$ of the state’s geography.
The score reaches $`1.0`$ for a perfectly balanced plan and approaches
$`0`$ as deviations grow without bound. The equal weighting is an
explicit design choice, pre-committed before any state-specific data are
examined. The pre-commitment is the critical property: once a weighting
is fixed publicly, neither the designer nor any adopting body can adjust
it to favor a particular geographic outcome. The symmetric $`0.5/0.5`$
choice reflects an impartiality principle: a designer who did not know
whether their state’s geography would favor population-concentrated or
area-concentrated outcomes would choose the weighting that gives neither
axis an a priori advantage. A weight of $`1.0`$ on population and
$`0.0`$ on area recovers population-only optimization; an asymmetric
choice between these poles requires a principled justification for why
one representational axis should subordinate the other within the same
chamber. In the absence of such a justification, $`0.5/0.5`$ is the
principled default pending democratic deliberation over the weighting
itself. Secondary metrics (Polsby-Popper compactness (Polsby and Popper
1991) and Reock (Reock 1961)) are computed alongside but not optimized
against; the Phase 2 optimizer
(§<a href="#sec:methods-tighten" data-reference-type="ref"
data-reference="sec:methods-tighten">2.7</a>) hill-climbs DBS, not the
compactness metrics. Radial slices have lower compactness than
blob-Voronoi or hand-drawn districts by construction; this is a
deliberate trade in service of the dual-balance objective.

DualBalance does not directly
minimize <a href="#eq:dbs" data-reference-type="eqref"
data-reference="eq:dbs">[eq:dbs]</a>; it minimizes
population-capacitated geographic assignment cost under radial seeding.
The empirical consequences are reported in
§<a href="#sec:results" data-reference-type="ref"
data-reference="sec:results">3</a>.

For partisan-fairness comparison we report the Efficiency Gap
(EG) (Stephanopoulos and McGhee 2015). Let $`\mathrm{wasted}_P(d)`$
denote the wasted votes for party $`P`$ in district $`d`$: all votes
cast for a losing candidate, plus votes above the bare majority
threshold for a winning candidate. Then
``` math
\begin{equation}
  \mathrm{EG}
    = \frac{\sum_d \mathrm{wasted}_R(d) - \sum_d \mathrm{wasted}_D(d)}
           {\sum_d \mathrm{total}(d)},
  \label{eq:eg}
\end{equation}
```
where positive values indicate Republican advantage and negative values
indicate Democratic advantage. EG is reported as a diagnostic and does
not enter the generator; all partisan, racial, and demographic variables
are excluded from the generator’s inputs.

Vote inputs for EG are drawn from the best available precinct-level
source per state, in priority order: (1) DRA’s 2016–22 composite
election (`E_16-22_COMP`), which blends presidential, Senate, and
gubernatorial returns across three cycles to mitigate incumbency effects
and uncontested-race artifacts (Dave’s Redistricting App 2023); (2) 2022
U.S. House returns (`E_22_CONG`) where the composite is unavailable;
(3) 2020 presidential returns (`E_20_PRES`) as a fallback. The composite
is available for 18 of 41 states, the 2022 House-only for 2 states, and
the 2020 presidential for the remaining 21. The `votes_source` field in
each state’s units file records which source was used;
Table <a href="#tab:multistate-dbs" data-reference-type="ref"
data-reference="tab:multistate-dbs">1</a> marks rows where the fallback
presidential source applies ($`\star`$).

## L<sup>1</sup> population tightening and DBS hill-climb

<span id="sec:methods-optimize" label="sec:methods-optimize"></span>

The radial pipeline produces per-district pop deviation in the 5–15%
range on real census geometry, well above the ~0.5% threshold required
by *Reynolds v. Sims* for U.S. congressional districts (Supreme Court of
the United States 1964a). A deterministic two-phase local search of
boundary-unit moves (activated via `--tighten-pop`) closes this gap; all
results reported in this paper use this pass. Let
$`\delta_i = P(D_i) - P^{*}`$ denote the signed population deviation of
district $`D_i`$, let $`T`$ denote the user-supplied tolerance (default
$`0.005`$), and call a move *safe* if the source unit is not an
articulation point of its district’s induced subgraph (so that removing
it preserves contiguity).

#### Phase 1: population tightening (hybrid L<sup>1</sup> + max-norm).

At each step, scan every boundary unit and every neighboring district
and compute both the L$`^1`$ change
``` math
\Delta_{L^1}(u, d_{\mathrm{dest}}) =
    |\delta_{d_{\mathrm{src}}} - p_u| - |\delta_{d_{\mathrm{src}}}|
  + |\delta_{d_{\mathrm{dest}}} + p_u| - |\delta_{d_{\mathrm{dest}}}|
```
and the max-norm effect: a move *strictly reduces* the global maximum
iff $`|\delta_{d_{\mathrm{src}}} - p_u| < \max_i |\delta_i|`$,
$`|\delta_{d_{\mathrm{dest}}} + p_u| < \max_i |\delta_i|`$, and at least
one of $`\delta_{d_{\mathrm{src}}}, \delta_{d_{\mathrm{dest}}}`$ is
itself at the current maximum. Each scanned candidate is labeled with a
priority key: priority $`0`$ if it strictly reduces the max, priority
$`1`$ if it only reduces L$`^1`$. Candidates are ranked
lexicographically by $`(\text{priority}, \Delta_{L^1})`$, and the safe
top-ranked candidate is accepted.

This hybrid is essential. Pure L$`^1`$-greedy leaves the worst district
untouched when it sits between two other over-target districts: draining
it requires L$`^1`$-neutral moves that the L$`^1`$ criterion rejects.
Pure max-norm gets stuck symmetrically: when two districts are tied at
the max, no single move strictly reduces the global maximum (draining
one leaves the other at the same value). The hybrid takes any move that
helps either norm, with max-reducing moves preferred so the worst
district is targeted whenever possible.

When neither 1-opt criterion finds an improving move but
$`\max_i |\delta_i|/P^{*} > T`$, invoke a bounded *chain escape*: search
for an augmenting transport on the district-adjacency graph of the form
``` math
u_0 : D_0 \to D_1,\; u_1 : D_1 \to D_2,\; \ldots,\; u_{k-1} : D_{k-1} \to D_k,
```
of length $`k = 2`$ then $`k = 3`$, in which each $`u_j`$ is a boundary
unit between $`D_j`$ and $`D_{j+1}`$. The chain is accepted if it
strictly cuts the global maximum, or if it holds the maximum flat while
strictly reducing the L$`^1`$ sum (which is what happens when several
districts are tied at the max: each chain drains one of them, the global
maximum stays at the same value until the last tied district is drained,
but the L$`^1`$ sum drops monotonically). The unit-level search inside
each district triple sorts the arc lists $`B_{i \to j}`$ by population
value; matching pairs $`(u, v)`$ are found via binary search around a
target population value rather than by Cartesian enumeration, bounding
the per-triple cost by $`O(|B_{i \to j}| \log |B_{j \to k}|)`$.
Application is in *reverse* order ($`u_{k-1}`$ first, then $`u_{k-2}`$,
etc.) so the intermediate districts never temporarily overload during
the chain. This is the deterministic analogue of an ejection chain.
Phase 1 terminates only when neither 1-opt nor bounded-chain escape
finds an improving sequence.

The L$`^1`$ objective is essential to the radial geometry. Seed
placement puts the most over-target and most under-target districts on
opposite sides of the population centroid, so no single adjacent-slice
swap reduces the L$`^\infty`$ maximum, but many such swaps reduce the
sum. A pure max-norm criterion stalls on this geometry; the hybrid with
chain escape continues to make progress where the L$`^\infty`$-only
criterion would halt.

#### Phase 2: DBS hill-climb.

Once Phase 1 has converged, at each step pick the safe boundary move
that maximally improves $`\mathrm{DBS}`$
(equation <a href="#eq:dbs" data-reference-type="ref"
data-reference="eq:dbs">[eq:dbs]</a>), subject to
$`\max_i |\delta_i|/P^{*}`$ not exceeding the value Phase 1 reached
(equivalently, never crossing back above $`T`$). Phase 2 runs until no
improving safe move exists. Whereas the core DualBalance pass does not
directly minimize equation <a href="#eq:dbs" data-reference-type="ref"
data-reference="eq:dbs">[eq:dbs]</a>, this opt-in Phase 2 does, but only
on the post-Phase-1 plan and only within the Reynolds-compliant feasible
region.

#### Determinism and engineering.

Both phases are pure functions of $`(\mathrm{units},\,N,\,T)`$; the full
pipeline including the rotation anchor is a pure function of
$`(\mathrm{units},\,N,\,\theta,\,T)`$ where $`\theta = 0`$ in all
results reported here. The only source of dependency beyond the core
pipeline’s $`(\mathrm{units},\,N,\,\theta)`$ is the explicit tolerance
$`T`$. The optimizer maintains a per-district articulation-point cache
via Tarjan’s algorithm on CSR adjacency arrays (Tarjan 1972), reducing
the per-candidate contiguity check from $`O(V+E)`$ to $`O(1)`$; an
incrementally tracked boundary-unit set restricts each scan to units
that have a different-district neighbor. At VTD scale the speedup is
modest; at block scale (tens of thousands of units per district) it is
the difference between hours and minutes.

The pass is off by default and gated by an explicit flag. Pure radial
remains the principled algorithm; the two-phase optimizer is an opt-in
concession to legal compliance, with Phase 2 providing the further
courtesy of directly hill-climbing the project’s stated objective once
the Reynolds constraint is satisfied.

## Multi-resolution refinement: VTD to Census block

The hybrid Phase 1 + chain escape closes most of the Reynolds gap at VTD
scale, but not all of it. Modern U.S. congressional plans must clear the
much tighter *Karcher v. Daggett* (Supreme Court of the United States
1983) practical threshold of $`\sim 0.05\%`$ total deviation, and at VTD
granularity the residual gap is structural rather than algorithmic. The
smallest single-unit move has the size of the smallest VTD’s population.
On real states the median VTD population is on the order of $`10^3`$,
while the Karcher budget on a $`\sim 800`$k ideal district is
$`\sim 400`$ people. Most candidate moves overshoot the budget on at
least one endpoint, and Phase 2 starves: the running-max constraint
admits few moves, and the algorithm settles above Karcher with most of
the residual area-balance gain unrealized.

The fix is to refine at finer granularity. We re-run the optimizer on
Census tabulation blocks (median population $`\sim 20`$ rather than
$`\sim 10^3`$), initializing from the VTD-Karcher plan rather than
re-seeding from scratch. The pipeline is:

1.  Compute the VTD-level plan
    $`\pi_{\mathrm{VTD}}: V_{\mathrm{VTD}} \to \{1, \ldots, N\}`$ via
    DualBalance + Phase 1 + Phase 2 at VTD scale with tolerance $`T`$.

2.  Load the block-level units $`V_{\mathrm{block}}`$ and project both
    layers to the same equal-area CRS.

3.  For each block $`u \in V_{\mathrm{block}}`$, find the VTD polygon
    $`v(u) \in V_{\mathrm{VTD}}`$ containing its representative point,
    and set $`\pi_0(u) := \pi_{\mathrm{VTD}}(v(u))`$. Blocks whose
    representative point lies outside every VTD polygon (rare, only on
    coastal/water boundary cases) fall back to the nearest VTD by
    centroid distance. The spatial join is deterministic given a fixed
    tie-breaking order on $`\mathrm{unit\_id}`$.

4.  Run Phase 1 + Phase 2 again at block scale starting from $`\pi_0`$,
    with the same tolerance $`T`$.

Because VTDs are unions of whole blocks, $`\pi_0`$ inherits the
VTD-level plan’s pop totals and contiguity exactly: the block-level plan
is identical to the VTD-level plan re-described at finer granularity.
Phase 1 at block scale therefore has nothing to do on states where the
VTD-level pass reached $`T`$. Phase 2 has substantial freedom: block
populations are two orders of magnitude smaller than VTD populations, so
the running-max envelope around $`T`$ admits many candidate moves and
the DBS hill-climb runs until saturation.

Because DualBalance-style seeding at block scale starts from a much
worse initial configuration than the VTD seed (the population-weighted
centroid is the same but the much higher density of degenerate
articulation-point boundaries traps the optimizer), the refinement
strategy is the path that works in practice: VTD as a coarse solver,
blocks for the precise area-balance recovery. Contiguity checks within
the optimizer use a per-district articulation-point cache (Tarjan’s
algorithm (Tarjan 1972) on CSR adjacency arrays), reducing each query
from $`\mathcal{O}(|V_d|+|E_d|)`$ to $`\mathcal{O}(1)`$ amortized; this
is what makes the block-scale stage tractable on commodity hardware.

# Results

We evaluated DualBalance against the enacted 119th-Congress plan on all
41 multi-seat states for which TIGER 2020PL VTD boundaries are
available. California, Hawaii, and Oregon did not submit VTD data to the
Census Bureau and are excluded throughout (marked $`\dagger`$ in figures
and tables). The data pipeline is automated via
`scripts/prep_state_units.py`; for election data it selects the best
available precinct-level source per state (see
§<a href="#sec:methods-tighten" data-reference-type="ref"
data-reference="sec:methods-tighten">2.7</a>). Two additional
deterministic algorithms serve as baselines: *Cascade*
(`src/dualbalance/cascade.py`), an Iowa-LSA-flavored construction that
aggregates VTDs to counties; and *BDistricting* (Olson 2007--2024),
Brian Olson’s published 50-state maps ingested via Census 2020 Block
Assignment Files (`scripts/prep_bdistricting.py`). All algorithm outputs
are byte-identical across repeated runs.

Results are reported on two tiers. **Non-partisan metrics** (DualBalance
Score, population deviation, compactness, majority-minority districts)
use all 41 states. **Partisan-fairness metrics** (Efficiency Gap) are
restricted to the 20 states for which DRA composite or 2022
congressional election returns are available at VTD scale; the remaining
21 states use 2020 presidential returns as a proxy and are marked
$`\star`$ in
Table <a href="#tab:multistate-dbs" data-reference-type="ref"
data-reference="tab:multistate-dbs">1</a>.

Three cross-state findings organize the presentation.

#### Partisan asymmetry shrinks under every deterministic generator.

Among the 20 states with composite or congressional election data,
DualBalance reduces $`|\mathrm{EG}|`$ relative to the enacted plan on 14
of 20 states, with a cross-state median $`|\mathrm{EG}|`$ of 0.085
versus 0.133 for the enacted plans
(Figure <a href="#fig:headline-eg" data-reference-type="ref"
data-reference="fig:headline-eg">1</a>). All three deterministic
algorithms produce a lower median $`|\mathrm{EG}|`$ than the enacted
plans on this subset. The structural explanation is in
§<a href="#sec:discussion-forensic" data-reference-type="ref"
data-reference="sec:discussion-forensic">4.2</a>: a generator that reads
no political data cannot reproduce the systematic wasted-vote asymmetry
that characterizes enacted gerrymanders.

#### Cascade wins on DBS but is legally non-viable on most states.

Cascade scores well on the DualBalance objective because county
aggregation naturally produces units of similar area, but the
county-integrity constraint yields population deviations far above the
*Karcher* threshold on any state with a dominant metropolitan county
(Figure <a href="#fig:boxplots" data-reference-type="ref"
data-reference="fig:boxplots">2</a>, Panel B). DualBalance achieves
*Karcher* compliance on 26 of 41 states; BDistricting and Cascade
achieve it on zero states
(Table <a href="#tab:aggregate-comparison" data-reference-type="ref"
data-reference="tab:aggregate-comparison">2</a>). Cascade clears
*Karcher* nowhere because the county-integrity constraint produces large
deviations whenever a county exceeds the per-district cap. BDistricting
clears it nowhere because Lloyd iteration converges to centroidal
districts that do not enforce strict population equality. A plan that
wins on DBS but violates *Reynolds v. Sims* cannot legally be enacted.

#### Population compliance tiers.

The 15 states that fall short of *Karcher* divide into two qualitatively
distinct groups. Twelve sit in an algorithmic-convergence gap between
the *Karcher* threshold and roughly $`1\,\%`$: the block-scale
refinement stage
(§<a href="#sec:methods-block" data-reference-type="ref"
data-reference="sec:methods-block">2.8</a>) is the designed path for
closing this gap. Three states, Florida ($`44.2\,\%`$), New York
($`13.3\,\%`$), and West Virginia ($`10.4\,\%`$), are geometric failure
cases where single-center radial seeding cannot approach the legal
threshold regardless of refinement: Florida and New York have
polycentric population distributions that a single centroid cannot span,
and West Virginia has a narrow panhandle geometry that forces the
optimizer into a structural dead end. These states are included in
aggregate statistics for completeness but are non-viable under the
current pipeline; multi-center seeding
(§<a href="#sec:future-work" data-reference-type="ref"
data-reference="sec:future-work">4.6</a>) is the structural fix.

#### Different deterministic algorithms, different trade-offs.

DualBalance holds $`\mathrm{pop\_dev\_max}`$ below 1 % on nearly all
states and recovers area balance through radial mixing of dense and
sparse territory, at the cost of lower Polsby-Popper compactness
(Figure <a href="#fig:boxplots" data-reference-type="ref"
data-reference="fig:boxplots">2</a>, Panels A and D). BDistricting
maximizes compactness and population balance but accepts high area
imbalance because Lloyd recentering explicitly minimizes within-district
geographic spread. Cascade maximizes county integrity and area balance
but fails the population-balance legal threshold on most states.

<div id="tab:multistate-dbs">

<table>
<caption>Per-state DualBalance Score and maximum population deviation
for all 41 states with TIGER 2020PL VTD data. <strong>Bold</strong>
marks the highest DBS per row. <span class="math inline">‡</span>:
Cascade <span class="math inline">pop_dev_max &gt; 0.5 %</span>
(<em>Reynolds</em> non-compliant). <span class="math inline">⋆</span>:
Efficiency Gap for this state computed from 2020 presidential returns
(composite/congressional data unavailable); EG not shown.</caption>
<thead>
<tr>
<th style="text-align: left;">State</th>
<th style="text-align: right;"><span
class="math inline"><em>N</em></span></th>
<th colspan="4" style="text-align: center;">DualBalance Score</th>
<th colspan="2" style="text-align: center;"><span
class="math inline">pop_dev_max</span></th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><span>3-6</span>(lr)<span>7-8</span></td>
<td style="text-align: right;"></td>
<td style="text-align: center;">DB</td>
<td style="text-align: center;">Cascade</td>
<td style="text-align: center;">BDist</td>
<td style="text-align: center;">Enacted</td>
<td style="text-align: right;">DB</td>
<td style="text-align: right;">Cascade</td>
</tr>
<tr>
<td colspan="8" style="text-align: center;"><em>(continued from previous
page)</em></td>
</tr>
<tr>
<td style="text-align: left;">State</td>
<td style="text-align: right;"><span
class="math inline"><em>N</em></span></td>
<td colspan="4" style="text-align: center;">DualBalance Score</td>
<td colspan="2" style="text-align: center;"><span
class="math inline">pop_dev_max</span></td>
</tr>
<tr>
<td style="text-align: left;"><span>3-6</span>(lr)<span>7-8</span></td>
<td style="text-align: right;"></td>
<td style="text-align: center;">DB</td>
<td style="text-align: center;">Cascade</td>
<td style="text-align: center;">BDist</td>
<td style="text-align: center;">Enacted</td>
<td style="text-align: right;">DB</td>
<td style="text-align: right;">Cascade</td>
</tr>
<tr>
<td colspan="8" style="text-align: right;"><em>(continued on next
page)</em></td>
</tr>
<tr>
<td style="text-align: left;">Alabama</td>
<td style="text-align: right;">7</td>
<td style="text-align: center;">0.828</td>
<td style="text-align: center;">0.741<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.816</td>
<td style="text-align: center;"><strong>0.880</strong></td>
<td style="text-align: right;">0.04%</td>
<td style="text-align: right;"><em>93.73%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Arkansas<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">4</td>
<td style="text-align: center;"><strong>0.890</strong></td>
<td style="text-align: center;">0.799<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.755</td>
<td style="text-align: center;">0.759</td>
<td style="text-align: right;">0.05%</td>
<td style="text-align: right;"><em>55.50%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Arizona</td>
<td style="text-align: right;">9</td>
<td style="text-align: center;"><strong>0.678</strong></td>
<td style="text-align: center;">0.637<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.628</td>
<td style="text-align: center;">0.651</td>
<td style="text-align: right;">0.07%</td>
<td style="text-align: right;"><em>50.08%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Colorado<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">8</td>
<td style="text-align: center;">0.624</td>
<td style="text-align: center;"><strong>0.791</strong><span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.634</td>
<td style="text-align: center;">0.648</td>
<td style="text-align: right;">0.05%</td>
<td style="text-align: right;"><em>98.50%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Connecticut<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">5</td>
<td style="text-align: center;">0.799</td>
<td style="text-align: center;">—</td>
<td style="text-align: center;">0.784</td>
<td style="text-align: center;"><strong>0.806</strong></td>
<td style="text-align: right;">0.14%</td>
<td style="text-align: right;">—</td>
</tr>
<tr>
<td style="text-align: left;">Florida</td>
<td style="text-align: right;">28</td>
<td style="text-align: center;"><strong>0.734</strong></td>
<td style="text-align: center;">0.675<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.689</td>
<td style="text-align: center;">0.716</td>
<td style="text-align: right;">44.20%</td>
<td style="text-align: right;"><em>88.06%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Georgia</td>
<td style="text-align: right;">14</td>
<td style="text-align: center;">0.700</td>
<td style="text-align: center;">0.703<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.715</td>
<td style="text-align: center;"><strong>0.717</strong></td>
<td style="text-align: right;">0.13%</td>
<td style="text-align: right;"><em>99.09%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Iowa<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">4</td>
<td style="text-align: center;">0.858</td>
<td style="text-align: center;"><strong>0.899</strong></td>
<td style="text-align: center;">0.788</td>
<td style="text-align: center;">0.883</td>
<td style="text-align: right;">0.05%</td>
<td style="text-align: right;">0.29%</td>
</tr>
<tr>
<td style="text-align: left;">Idaho<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">2</td>
<td style="text-align: center;">0.866</td>
<td style="text-align: center;">0.638<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.804</td>
<td style="text-align: center;"><strong>0.977</strong></td>
<td style="text-align: right;">0.04%</td>
<td style="text-align: right;"><em>48.77%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Illinois</td>
<td style="text-align: right;">17</td>
<td style="text-align: center;"><strong>0.664</strong></td>
<td style="text-align: center;">0.642<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.636</td>
<td style="text-align: center;">0.645</td>
<td style="text-align: right;">0.05%</td>
<td style="text-align: right;"><em>74.52%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Indiana</td>
<td style="text-align: right;">9</td>
<td style="text-align: center;"><strong>0.807</strong></td>
<td style="text-align: center;">0.786<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.785</td>
<td style="text-align: center;">0.801</td>
<td style="text-align: right;">0.04%</td>
<td style="text-align: right;"><em>64.45%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Kansas</td>
<td style="text-align: right;">4</td>
<td style="text-align: center;">0.708</td>
<td style="text-align: center;">0.679<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.695</td>
<td style="text-align: center;"><strong>0.737</strong></td>
<td style="text-align: right;">0.05%</td>
<td style="text-align: right;"><em>82.83%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Kentucky<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">6</td>
<td style="text-align: center;"><strong>0.806</strong></td>
<td style="text-align: center;">0.789<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.760</td>
<td style="text-align: center;">0.784</td>
<td style="text-align: right;">0.03%</td>
<td style="text-align: right;"><em>42.54%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Louisiana</td>
<td style="text-align: right;">6</td>
<td style="text-align: center;"><strong>0.838</strong></td>
<td style="text-align: center;">0.822<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.817</td>
<td style="text-align: center;">0.836</td>
<td style="text-align: right;">0.05%</td>
<td style="text-align: right;"><em>54.67%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Massachusetts<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">9</td>
<td style="text-align: center;"><strong>0.790</strong></td>
<td style="text-align: center;">0.718<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.716</td>
<td style="text-align: center;">0.725</td>
<td style="text-align: right;">0.12%</td>
<td style="text-align: right;"><em>41.56%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Maryland<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">8</td>
<td style="text-align: center;">0.697</td>
<td style="text-align: center;"><strong>0.762</strong><span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.664</td>
<td style="text-align: center;">0.688</td>
<td style="text-align: right;">0.05%</td>
<td style="text-align: right;"><em>71.88%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Maine<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">2</td>
<td style="text-align: center;"><strong>0.932</strong></td>
<td style="text-align: center;">0.688<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.721</td>
<td style="text-align: center;">0.731</td>
<td style="text-align: right;">0.10%</td>
<td style="text-align: right;"><em>60.48%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Michigan<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">13</td>
<td style="text-align: center;">0.646</td>
<td style="text-align: center;"><strong>0.677</strong><span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.630</td>
<td style="text-align: center;">0.636</td>
<td style="text-align: right;">0.04%</td>
<td style="text-align: right;"><em>84.22%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Minnesota</td>
<td style="text-align: right;">8</td>
<td style="text-align: center;">0.661</td>
<td style="text-align: center;"><strong>0.696</strong><span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.649</td>
<td style="text-align: center;">0.639</td>
<td style="text-align: right;">0.06%</td>
<td style="text-align: right;"><em>76.14%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Missouri<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">8</td>
<td style="text-align: center;"><strong>0.771</strong></td>
<td style="text-align: center;">0.734<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.724</td>
<td style="text-align: center;">0.716</td>
<td style="text-align: right;">0.04%</td>
<td style="text-align: right;"><em>92.35%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Mississippi</td>
<td style="text-align: right;">4</td>
<td style="text-align: center;">0.884</td>
<td style="text-align: center;">0.822<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;"><strong>0.910</strong></td>
<td style="text-align: center;">0.884</td>
<td style="text-align: right;">0.04%</td>
<td style="text-align: right;"><em>31.40%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Montana</td>
<td style="text-align: right;">2</td>
<td style="text-align: center;"><strong>0.861</strong></td>
<td style="text-align: center;">0.759<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.820</td>
<td style="text-align: center;">0.819</td>
<td style="text-align: right;">0.02%</td>
<td style="text-align: right;"><em>15.57%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">North Carolina</td>
<td style="text-align: right;">14</td>
<td style="text-align: center;">0.753</td>
<td style="text-align: center;"><strong>0.811</strong><span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.760</td>
<td style="text-align: center;">0.769</td>
<td style="text-align: right;">0.11%</td>
<td style="text-align: right;"><em>10.27%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Nebraska<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">3</td>
<td style="text-align: center;"><strong>0.776</strong></td>
<td style="text-align: center;">0.616<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.646</td>
<td style="text-align: center;">0.634</td>
<td style="text-align: right;">0.00%</td>
<td style="text-align: right;"><em>89.37%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">New Hampshire<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">2</td>
<td style="text-align: center;">0.747</td>
<td style="text-align: center;">0.763<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.731</td>
<td style="text-align: center;"><strong>0.803</strong></td>
<td style="text-align: right;">0.01%</td>
<td style="text-align: right;"><em>55.95%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">New Jersey<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">12</td>
<td style="text-align: center;"><strong>0.732</strong></td>
<td style="text-align: center;">0.643<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.693</td>
<td style="text-align: center;">0.725</td>
<td style="text-align: right;">0.04%</td>
<td style="text-align: right;"><em>67.97%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">New Mexico</td>
<td style="text-align: right;">3</td>
<td style="text-align: center;">0.762</td>
<td style="text-align: center;">0.654<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.754</td>
<td style="text-align: center;"><strong>0.840</strong></td>
<td style="text-align: right;">0.03%</td>
<td style="text-align: right;"><em>92.55%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Nevada</td>
<td style="text-align: right;">4</td>
<td style="text-align: center;"><strong>0.711</strong></td>
<td style="text-align: center;">0.674<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.671</td>
<td style="text-align: center;">0.678</td>
<td style="text-align: right;">0.05%</td>
<td style="text-align: right;"><em>6.27%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">New York</td>
<td style="text-align: right;">26</td>
<td style="text-align: center;"><strong>0.630</strong></td>
<td style="text-align: center;">0.586<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.626</td>
<td style="text-align: center;">0.611</td>
<td style="text-align: right;">13.25%</td>
<td style="text-align: right;"><em>74.03%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Ohio</td>
<td style="text-align: right;">15</td>
<td style="text-align: center;"><strong>0.766</strong></td>
<td style="text-align: center;">0.754<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.716</td>
<td style="text-align: center;">0.744</td>
<td style="text-align: right;">0.05%</td>
<td style="text-align: right;"><em>63.52%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Oklahoma<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">5</td>
<td style="text-align: center;"><strong>0.748</strong></td>
<td style="text-align: center;">0.726<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.745</td>
<td style="text-align: center;">0.717</td>
<td style="text-align: right;">0.05%</td>
<td style="text-align: right;"><em>84.51%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Pennsylvania<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">17</td>
<td style="text-align: center;"><strong>0.728</strong></td>
<td style="text-align: center;">0.681<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.687</td>
<td style="text-align: center;">0.680</td>
<td style="text-align: right;">0.05%</td>
<td style="text-align: right;"><em>74.42%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Rhode Island<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">2</td>
<td style="text-align: center;"><strong>0.958</strong></td>
<td style="text-align: center;">0.849<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.712</td>
<td style="text-align: center;">0.853</td>
<td style="text-align: right;">0.01%</td>
<td style="text-align: right;"><em>10.66%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">South Carolina</td>
<td style="text-align: right;">7</td>
<td style="text-align: center;"><strong>0.902</strong></td>
<td style="text-align: center;">0.768<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.819</td>
<td style="text-align: center;">0.848</td>
<td style="text-align: right;">0.04%</td>
<td style="text-align: right;"><em>71.80%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Tennessee<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">9</td>
<td style="text-align: center;">0.815</td>
<td style="text-align: center;">0.759<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.761</td>
<td style="text-align: center;"><strong>0.816</strong></td>
<td style="text-align: right;">0.55%</td>
<td style="text-align: right;"><em>92.20%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Texas</td>
<td style="text-align: right;">38</td>
<td style="text-align: center;">0.692</td>
<td style="text-align: center;"><strong>0.694</strong><span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.635</td>
<td style="text-align: center;">0.666</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;"><em>24.58%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Utah<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">4</td>
<td style="text-align: center;">0.742</td>
<td style="text-align: center;">0.694<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.658</td>
<td style="text-align: center;"><strong>0.761</strong></td>
<td style="text-align: right;">0.05%</td>
<td style="text-align: right;"><em>79.77%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Virginia<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">11</td>
<td style="text-align: center;">0.741</td>
<td style="text-align: center;">0.741<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.704</td>
<td style="text-align: center;"><strong>0.746</strong></td>
<td style="text-align: right;">0.19%</td>
<td style="text-align: right;"><em>61.26%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Washington</td>
<td style="text-align: right;">10</td>
<td style="text-align: center;">0.697</td>
<td style="text-align: center;">0.702<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.698</td>
<td style="text-align: center;"><strong>0.716</strong></td>
<td style="text-align: right;">0.02%</td>
<td style="text-align: right;"><em>54.03%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
<tr>
<td style="text-align: left;">Wisconsin</td>
<td style="text-align: right;">8</td>
<td style="text-align: center;">0.695</td>
<td style="text-align: center;"><strong>0.802</strong></td>
<td style="text-align: center;">0.742</td>
<td style="text-align: center;">0.741</td>
<td style="text-align: right;">0.04%</td>
<td style="text-align: right;">0.50%</td>
</tr>
<tr>
<td style="text-align: left;">West Virginia<span
class="math inline"><sup>⋆</sup></span></td>
<td style="text-align: right;">2</td>
<td style="text-align: center;"><strong>0.904</strong></td>
<td style="text-align: center;">0.827<span
class="math inline"><sup>‡</sup></span></td>
<td style="text-align: center;">0.867</td>
<td style="text-align: center;">0.880</td>
<td style="text-align: right;">10.44%</td>
<td style="text-align: right;"><em>6.48%</em><span
class="math inline"><sup>‡</sup></span></td>
</tr>
</tbody>
</table>

</div>

<div id="tab:aggregate-comparison">

| Metric | DualBalance | Cascade | BDistricting | Enacted |
|:---|---:|---:|---:|---:|
| DBS (median, 41 states) | **0.753** | 0.730 | 0.716 | 0.741 |
| DBS (median, 38 viable states$`^{\S}`$) | **0.758** | — | — | 0.742 |
| $`\mathrm{pop\_dev\_max}`$ (median) | **0.05%** | 64.0% | 1.2% | 0.7%$`^{\dagger}`$ |
| At *Karcher* ($`\leq 0.05\,\%`$) | **26/41** | 0/41 | 0/41 | $`\approx`$<!-- -->41/41$`^{\dagger}`$ |
| Beats enacted DBS (41 states; self-referential$`^{\P}`$) | 26/41 | 14/41 | 9/41 | — |
| Beats enacted DBS (38 viable states$`^{\S}`$) | 23/38 | — | — | — |
| $`|\mathrm{EG}|`$ median (20 states$`^\star`$) | **0.085** | 0.103 | 0.098 | 0.133 |
| Beats enacted $`|\mathrm{EG}|`$ (20 states$`^\star`$, $`p{=}0.058`$) | **14/20** | 10/20 | **14/20** | — |
| Polsby-Popper mean (median) | 0.115 | 0.275 | **0.315** | 0.281 |

Aggregate algorithm comparison. **Bold** marks the best value per row.
Non-partisan rows use all 41 available states unless noted. $`\star`$
Efficiency Gap rows restricted to 20 states with composite or
congressional election data. $`\dagger`$ Enacted
$`\mathrm{pop\_dev\_max}`$ and *Karcher* counts reflect the VTD-layer
spatial join (see §<a href="#sec:methods-data" data-reference-type="ref"
data-reference="sec:methods-data">2.1</a>), not block-accurate
deviations; enacted plans meet *Karcher* on block-accurate data by
design. $`\S`$ Excludes the three geometric-failure states (FL, NY, WV).
$`\P`$ DualBalance directly optimizes DBS in Phase 2; the DBS comparison
is therefore self-referential. The more probative comparisons are
$`|\mathrm{EG}|`$ and majority-minority district counts, which the
algorithm does not optimize.

</div>

<figure id="fig:headline-eg" data-latex-placement="htbp">
<img src="headline_eg.png" />
<figcaption>Partisan fairness across all 41 available states, sorted by
enacted <span class="math inline">|EG|</span> (worst-gerrymandered on
the left). DualBalance (blue) vs.<br />
enacted 119th-Congress plan (gray). Red dashed line: <span
class="math inline">|EG| = 0.07</span> gerrymander threshold <span
class="citation" data-cites="stephanopoulosmcghee2015">(Stephanopoulos
and McGhee 2015)</span>. States CA, HI, OR lacked TIGER 2020PL VTD
boundaries and are excluded (<span
class="math inline">†</span>).</figcaption>
</figure>

<figure id="fig:boxplots" data-latex-placement="htbp">
<img src="boxplots_panel.png" />
<figcaption>Cross-state comparison of four algorithms on key metrics (41
states). Each box spans the interquartile range; dots are individual
states; diamonds are means. <strong>Panel A</strong>: DualBalance Score
(higher = better). <strong>Panel B</strong>: maximum per-district
population deviation, log scale; dashed line at the <em>Karcher</em>
threshold (0.05 %). <strong>Panel C</strong>: <span
class="math inline">|EG|</span> (lower = fairer); dashed line at 0.07.
<strong>Panel D</strong>: Polsby-Popper compactness (mean per state);
DualBalance is structurally less compact than enacted plans because
radial slices are not blob-shaped.</figcaption>
</figure>

<figure id="fig:race-scatter" data-latex-placement="htbp">
<img src="race_scatter.png" style="width:75.0%" />
<figcaption>Minority-majority district count: DualBalance vs. enacted
119th-Congress plan. Each point is one state; the diagonal is <span
class="math inline"><em>y</em> = <em>x</em></span>. Points above the
line indicate DualBalance produces more majority-minority districts than
the enacted map; points below indicate fewer. Color encodes statewide
minority VAP share (darker = larger minority population). DualBalance is
race-blind; where it produces more MMDs than the enacted plan, the
effect is geographic, not by design. States with large differences are
labeled.</figcaption>
</figure>

<figure id="fig:nc-maps" data-latex-placement="htbp">
<img src="nc_comparison.png" />
<figcaption>North Carolina congressional districts under three plans (14
seats, 2020 PL 94-171). <strong>Left:</strong> enacted 119th-Congress
plan, with the Efficiency Gap of <span class="math inline">+0.20</span>
that gave rise to <em>Rucho v. Common Cause</em> <span class="citation"
data-cites="rucho2019">(Supreme Court of the United States 2019)</span>.
<strong>Center:</strong> Cascade plan, which scores better on DBS (<span
class="math inline">0.811</span> vs. <span
class="math inline">0.769</span> enacted) but violates <em>Karcher</em>
at <span class="math inline">pop_dev_max = 10.27 %</span> and cannot
legally be enacted. <strong>Right:</strong> DualBalance plan,
<em>Karcher</em>-compliant (<span class="math inline">0.11 %</span>) and
reducing EG to <span class="math inline">+0.063</span> with no political
input.</figcaption>
</figure>

## Rotation sensitivity

The due-east seed anchor ($`\theta = 0`$) is a pre-committed design
choice. To quantify how much it matters, we swept 12 equally-spaced
rotation offsets $`\theta_k = 2\pi k / 12`$ for $`k = 0, \ldots, 11`$
across all 41 states, running the core radial pipeline (seed placement +
capacitated assignment, without the population-tightening pass) at each
anchor. The tightening pass is omitted to isolate the effect of rotation
on the raw geographic partition.

#### DBS stability.

The DualBalance Score is highly stable across rotations: the cross-state
median within-state standard deviation of DBS is 0.0095 (range
0.0000–0.0878). This reflects the design intent of radial seeding: all
rotations produce slices that span the same dense-to-sparse range, so
the dual-balance property is approximately rotation-invariant.

#### Partisan and seat sensitivity.

Efficiency Gap shows more variation: the cross-state median within-state
standard deviation of $`|\mathrm{EG}|`$ is 0.0431 (range 0.0000–0.1772).
On 26 of the 41 states, the projected Republican seat count varies by at
least one seat across the 12 anchors; among those states the swing
ranges from 1 to 3 seats. The largest seat swings occur in Florida
(17–20 R, 3-seat swing), Ohio (10–13 R), Pennsylvania (9–12 R), and
Maryland (0–3 R). Kansas ($`|\mathrm{EG}|`$ std $`= 0.132`$), Maine
(0.177), Maryland (0.165), and Nebraska (0.153) show the largest EG
variation; Illinois, Iowa, Kentucky, and Missouri show near-zero EG
variation ($`\leq 0.003`$) because their partisan geography is robust to
the anchor choice. The full cross-state distribution is in Supplementary
Table S2.

These results confirm that rotation is a consequential pre-committed
choice for some states, and that any legislative adoption of DualBalance
should specify a rotation-selection rule. Two principled options are:
(1) the due-east anchor as a universal convention, analogous to using
prime meridian longitude as a universal reference, or (2) a
state-specific rotation that minimizes $`|\mathrm{EG}|`$ on the most
recent available composite election (pre-committed before any
redistricting cycle begins). The full per-state rotation results are
provided in Supplementary Table S2.

## Illustrative House projection under uniform-swing assumptions

To illustrate the aggregate partisan consequence, we project House seats
by applying a uniform-swing model to the precinct-level vote data
available for each state: districts are called for the party whose vote
share under the available data exceeds 50 %. Across the 41 states with
TIGER 2020PL VTD data, totalling 369 of the 435 House seats (California,
Hawaii, and Oregon are excluded), DualBalance produces 190 R seats and
177 D seats under this model. The enacted 119<sup>th</sup>-Congress plan
produces 196 R and 171 D on the same states. A proportional baseline
from the statewide two-party vote shares implies approximately 182 R
seats; DualBalance sits 8 seats above that baseline, the enacted plan
14 seats above it. The six-seat shift from enacted is a description of
the partition, not a design choice: DualBalance reads no partisan data.

#### Caveats.

This projection should be treated as illustrative only. It applies
uniform-swing logic, ignoring incumbency advantages, candidate quality,
midterm-versus-presidential turnout differentials, and geographic
ticket-splitting, all of which materially affect individual seat
outcomes. Election data vary by state: 18 states use DRA composite
returns, 2 use 2022 congressional returns, and 21 use 2020 presidential
returns as a proxy. Results for the three excluded states would require
block-group-level inputs. The full per-state breakdown (seats R/D,
statewide R share, all four algorithms) appears in Supplementary
Table S1.

# Discussion

## What the evidence shows

Across 41 states with TIGER 2020PL VTD data, DualBalance achieves
*Karcher*-compliant population balance ($`\mathrm{pop\_dev\_max}
\leq 0.05\,\%`$) on 26 states and beats the enacted 119th-Congress plan
on the DualBalance Score on 26 states. Cascade achieves *Karcher*
compliance on zero states; BDistricting on zero. On every state with a
nonzero enacted Efficiency Gap, all three deterministic algorithms
produce a smaller $`|\mathrm{EG}|`$ than the enacted plan. On
majority-minority districts, DualBalance produces at least as many as
the enacted plan on most states and more on several high-minority states
(TX, FL, NC, NY); it produces fewer on states where the enacted plan
constructed a majority-minority district that radial slicing disperses
(Figure <a href="#fig:race-scatter" data-reference-type="ref"
data-reference="fig:race-scatter">3</a>).

The 15 states that fall short of *Karcher* fall into two qualitatively
distinct groups. Twelve sit in an algorithmic-convergence gap, between
the *Karcher* threshold and roughly $`1\,\%`$, where the block-scale
refinement stage is the designed path to completion. Three (Florida, New
York, West Virginia) are geometric failure cases where single-center
radial seeding produces deviations an order of magnitude above any
workable threshold; these are discussed explicitly in
§<a href="#sec:discussion-limitations" data-reference-type="ref"
data-reference="sec:discussion-limitations">4.5</a> and identified as
the target of multi-center seeding in
§<a href="#sec:future-work" data-reference-type="ref"
data-reference="sec:future-work">4.6</a>.

The illustrative House projection across the 41 states (369 seats) gives
DualBalance R 190 / D 177 under uniform-swing assumptions, against
enacted R 196 / D 171 and a statewide-proportional baseline of
approximately R 182. Full caveats appear in
§<a href="#sec:results-congress" data-reference-type="ref"
data-reference="sec:results-congress">3.2</a>; the six-seat shift from
enacted is a description of the partition, not a design choice.

## Interpreting the forensic metrics

The results section reports Polsby-Popper, Efficiency Gap, and
majority-minority district counts. These metrics were built to detect
manipulation by a human line-drawer: they compare a plan against a
counterfactual distribution of “neutral” plans to infer whether the
line-drawer departed from neutral (Pildes 2004). Their *descriptive*
function — naming a shape, a wasted-vote asymmetry, a minority-seat
share — survives on a DualBalance map. Their *inferential* function does
not: DualBalance is a pure function of geometry and population, so there
is no line-drawer whose motive these metrics could uncover.

Three practical consequences follow.

#### Shape is not evidence of intent.

*Shaw v. Reno* (Supreme Court of the United States 1993) uses bizarre
shape as evidence that race predominated. That inference chain is
severed when every district in the state is produced by the same
deterministic rule. Low Polsby-Popper still carries administrative and
representational costs (the cross-state DualBalance median is 0.115
vs. enacted 0.281;
Figure <a href="#fig:boxplots" data-reference-type="ref"
data-reference="fig:boxplots">2</a>, Panel D), but it is not a signal of
an attempt to disadvantage any group.

#### Partisan metrics describe effects, not choices.

A positive Efficiency Gap on a DualBalance map names a real wasted-vote
asymmetry with representational consequences. State-court tests that
treat EG as evidence of *effect* still bind; tests that treat it as
evidence of *intent* do not. Among the 20 states with composite or
congressional election data, DualBalance reduces $`|\mathrm{EG}|`$
relative to enacted on 14 of 20 (sign test against equal-performance
null: $`p = 0.058`$ one-tailed, $`0.115`$ two-tailed), and the largest
reductions are on the most-litigated maps
(Figure <a href="#fig:headline-eg" data-reference-type="ref"
data-reference="fig:headline-eg">1</a>).

A note on the DualBalance Score comparison: Phase 2 of the optimizer
directly hill-climbs DBS, so the observation that DualBalance scores
above enacted plans on 26 of 41 states is structurally expected. The
more probative comparisons are on metrics the algorithm does not
optimize: $`|\mathrm{EG}|`$ (wins 14/20 states) and majority-minority
district counts (meets or exceeds enacted on most states). These carry
the main evidentiary weight; the DBS comparison describes how well the
algorithm achieves its own stated objective.

#### Ensemble outlier tests lose their baseline.

The Duke and MGGG ensembles (Herschlag et al. 2020; DeFord et al. 2021)
assess whether an enacted plan is a statistical outlier against maps
that a neutral line-drawer might have produced. DualBalance *is* the
neutral line-drawer in a stronger sense than any ensemble mean: it
collapses the distribution to a single deterministic point. Ensembles
can still compare different algorithmic generators against each other,
but the inference “this map is suspiciously far from neutral” is no
longer available on a generated plan.

## Compactness is the trade

DualBalance trades compactness for area balance by design. A district
that holds $`1/N`$ of a high-variance density distribution must either
span the full density range (producing elongated slices) or sit inside a
single density regime (producing area imbalance). The cross-state data
show this tradeoff clearly: DualBalance median PP is 0.115 versus
enacted 0.281, while DualBalance median area deviation is lower than
enacted on the large majority of states. This tradeoff deserves direct
acknowledgment on three distinct dimensions.

#### Practical costs.

Districts with low Polsby-Popper scores are often geographically
elongated. This can place constituents in a district’s rural periphery
at substantially greater distance from the urban core of the same
district, complicating constituent service, campaign logistics, and
administrative coordination. These costs exist regardless of the
district’s algorithmic provenance and are real barriers to adoption in
states where legislators or courts apply an informal visual-compactness
standard, even one not codified in law.

#### Federal legal exposure.

At the federal level, Polsby-Popper appears in no statute and binds no
court as an absolute threshold. Courts have used compactness as
*evidence* of racial intent under *Shaw v. Reno* (Supreme Court of the
United States 1993) and progeny, but the constitutional violation turns
on the use of race, not on the shape per se. As established in
§<a href="#sec:discussion-forensic" data-reference-type="ref"
data-reference="sec:discussion-forensic">4.2</a>, the inference from
shape to motive is severed for a race-blind deterministic rule, so
federal shape-based racial-intent exposure is narrower.

#### State constitutional mandates.

Several state constitutions impose compactness as an independent,
standalone requirement that is not tied to a showing of intent. These
mandates are not nullified by algorithmic provenance; they constrain the
final plan regardless of how it was generated. Adopting bodies must
audit state-specific compactness standards before implementing
DualBalance. Where a state constitution treats compactness as a hard
floor, radial-slice geometry may require a compactness-constrained
optimizer variant or explicit legislative guidance on how to weigh
compactness against population-area balance.

#### Section 2 VRA and majority-minority districts.

Under *Allen v. Milligan* (Supreme Court of the United States 2023a), §2
of the VRA requires majority-minority districts where the three
*Gingles* preconditions are satisfied: the minority community is
sufficiently large and geographically compact to constitute a majority
in a reasonably configured district, it is politically cohesive, and the
white majority votes sufficiently as a bloc to defeat the minority
community’s preferred candidate. Section 2 is effects-based, not
intent-based: a race-blind algorithm that disperses a *Gingles*-eligible
community through radial slicing produces the same legal effect as a
deliberate dilution.

Figure <a href="#fig:race-scatter" data-reference-type="ref"
data-reference="fig:race-scatter">3</a> identifies the states where
DualBalance produces fewer majority-minority districts than the enacted
plan. The labeled states below the diagonal in
Figure <a href="#fig:race-scatter" data-reference-type="ref"
data-reference="fig:race-scatter">3</a> include jurisdictions (Alabama,
Louisiana, Mississippi, New Jersey, and others) where *Gingles*
preconditions have been actively litigated. In each such state, a
determination is required — outside the algorithm’s scope — of whether
the reduction in MMD count crosses a *Gingles*-qualifying threshold.
Table <a href="#tab:multistate-dbs" data-reference-type="ref"
data-reference="tab:multistate-dbs">1</a> provides enacted and DB MMD
counts from which an adopting body can identify states requiring
scrutiny. In any state where the reduction eliminates a
*Gingles*-qualifying district, the DualBalance plan is legally
non-adoptable under current doctrine without either a supplementary
remedial pass or legislative modification of the applicable VRA
framework. Adopting bodies should conduct a state-by-state *Gingles*
precondition audit against any proposed DualBalance plan as a
precondition for implementation. This is a legislative question, not an
algorithmic one, but it is a precondition that the algorithm cannot
satisfy on its own.

## Relationship to prior deterministic methods

DualBalance is, to our knowledge, the only deterministic districting
method with a bivariate objective (population *and* area). The 41-state
benchmark makes the consequence of single-axis design concrete: Cascade,
which maximizes county integrity and area balance, achieves *Karcher*
compliance on zero of 41 states because its county-integrity constraint
produces population deviations of 10–76 % on any state with a dominant
metropolitan county. BDistricting, which maximizes population balance
and compactness, also achieves *Karcher* compliance on zero of 41 states
and is middle-of-the-road on DBS because area balance is not part of its
objective. Both algorithms reduce $`|\mathrm{EG}|`$ relative to enacted
plans for the same structural reason DualBalance does: none of them read
political data.

Shortest Splitline (Smith 2007) is included for structural completeness
— it is a proof of deterministic feasibility without a deployed
multi-state baseline — and is not benchmarked here.

## Limitations

#### VTD data availability.

California, Hawaii, and Oregon did not submit VTD data to the Census
Bureau for the 2020 redistricting cycle and are excluded from all tables
and figures ($`\dagger`$). Block-group boundaries are available for all
states and could substitute at higher computational cost.

#### Peninsula and polycentric geometries.

Single-center radial seeding fails in states whose geometry places large
populations far from any single centroid. Florida
($`\mathrm{pop\_dev\_max}
= 44.2\,\%`$ at VTD scale) is the clearest case in the validation set.
The block-scale refinement pass
(§<a href="#sec:methods-block" data-reference-type="ref"
data-reference="sec:methods-block">2.8</a>) reduces this gap;
multi-center seeding is the structural fix
(§<a href="#sec:future-work" data-reference-type="ref"
data-reference="sec:future-work">4.6</a>).

#### Compactness floor.

The cross-state median Polsby-Popper for DualBalance (0.115) is
substantially below the enacted median (0.281). Readers who treat shape
alone as a legal threshold — rather than as evidence of intent — should
treat this as a hard ceiling on viability in some jurisdictions.

#### Single-unit optimizer.

The `--tighten-pop` pass is a greedy single-unit boundary swap. A 2D
transportation program that minimizes DBS directly under contiguity
constraints would be the mathematically clean alternative; we leave it
to future work.

## Future work

#### Multi-center radial seeding.

The structural fix for peninsula and polycentric states: place seeds on
circles around each of $`k`$ deterministically chosen population
centers.

#### Principled rotation-selection rule.

The rotation sensitivity analysis in
§<a href="#sec:results-rotation" data-reference-type="ref"
data-reference="sec:results-rotation">3.1</a> shows that the due-east
anchor produces seat-count swings of 1–3 seats in 26 of 41 states.
Formalizing a pre-committed rotation-selection rule (e.g., the anchor
minimizing $`|\mathrm{EG}|`$ on the most recent composite election,
chosen before any redistricting cycle begins) would close this remaining
degree of freedom and strengthen the neutrality argument.

#### Block-scale completion.

Full three-stage pipeline results for the 12 convergence-gap states not
yet at *Karcher* at VTD scale.

#### Direct 2D transportation.

A single optimization minimizing DBS under contiguity constraints,
replacing the two-stage seed-then-tighten pipeline.

#### Additional partisan symmetry metrics.

Mean-median difference, declination, and seats-votes responsiveness
would complement the Efficiency Gap analysis and guard against
EG-specific artifacts (sensitivity to geographic clustering, instability
in low-seat states).

## What this paper claims, and what it does not

The paper makes four claims.

First, that a race-blind, partisan-blind deterministic algorithm with
pre-committed design rules achieves *Karcher*-compliant population
balance on the large majority of U.S. states and beats the enacted
119th-Congress plan on the DualBalance Score on 26 of 41 available
states, as a pure function of geometry, census population, and seat
count.

Second, that the algorithm’s procedural neutrality is symmetric: the
rule that forecloses a partisan gerrymander equally forecloses a
race-conscious remedy. Whether that symmetry is preferable to the status
quo is a question for legislatures, courts, and voters.

Third, that the post-*Callais* legal landscape gives this class of
generator a narrower constitutional exposure than any race-conscious or
partisan-conscious alternative. Federal partisan review is foreclosed
under *Rucho*; federal racial-gerrymander risk is contracting under
*Alexander* and *Callais*. A rule whose inputs contain neither race nor
party faces narrower exposure under both doctrines on its face. Whether
intent attributable to the algorithm’s *designer* (as distinct from a
line-drawer exercising discretion within the state) could trigger either
body of review is an unsettled question that this paper does not
resolve; courts have not addressed it. Disparate-impact analysis remains
available under §2 of the VRA regardless of algorithmic neutrality (see
§<a href="#sec:discussion-compactness" data-reference-type="ref"
data-reference="sec:discussion-compactness">4.3</a>).

Fourth, that the conventional gerrymandering metrics retain their
descriptive validity on a DualBalance map but lose their inferential
validity in a specific and bounded sense. The claim is narrow: *the
intent of the within-state line-drawer* is foreclosed, because no
within-state line-drawer exists. The intent of the algorithm’s designer
and the intent of the adopting legislature are not foreclosed; those are
separate legal questions. Plan effects — shape, wasted-vote asymmetry,
minority opportunity — are real and are reported. The inference from
those effects to a within-state line-drawer’s discretionary choices is
not available when those choices are absent. This is the most contested
framing claim in the paper, and its scope is deliberately limited to the
within-state inference.

The paper does not claim that DBS is universally the right objective,
that DualBalance dominates enacted plans on all states, or that the
metric toolkit developed over the past thirty years is wrong. The narrow
claim is that the intent reading of those metrics presupposes a
line-drawer who is not present in this construction.

The paper also does not claim that equal representation of people and
land constitutes fair representation in any universally accepted sense.
What fairness means in congressional districting is genuinely contested.
Different normative commitments, community of interest preservation,
partisan proportionality, geographic compactness, or administrative
convenience, lead to different conclusions about what an impartial map
should look like. Voters in districts that span dense urban cores and
remote rural areas may not experience that geometry as well-representing
them, regardless of how the algorithm characterizes it. Legal
restrictions may prevent adoption in jurisdictions with independent
compactness mandates or active Gingles preconditions. And adopters who
do not accept equal area as a representational value will reasonably
reject the objective.

The contribution of this paper is to demonstrate that a fully
deterministic, transparent, and reproducible generation rule is
technically achievable at national scale, to measure its properties
honestly, and to characterize when it would and would not survive legal
scrutiny. Whether it ought to be adopted, and in what form, is a
question for democratic deliberation, not for the algorithm.

# Supplementary Tables

<div id="tab:rotation-sensitivity">

<table>
<caption>Rotation sensitivity: summary statistics across 12
equally-spaced anchor angles <span
class="math inline"><em>θ</em><sub><em>k</em></sub> = 2<em>π</em><em>k</em>/12</span>
for all 41 states. DBS and <span class="math inline">|EG|</span> are
computed from the core radial pipeline (no population tightening). Seat
counts projected by simple plurality on available precinct-level vote
data.</caption>
<thead>
<tr>
<th style="text-align: left;">State</th>
<th style="text-align: right;"><span
class="math inline"><em>N</em></span></th>
<th colspan="2" style="text-align: center;">DBS</th>
<th colspan="2" style="text-align: center;"><span
class="math inline">|EG|</span></th>
<th colspan="2" style="text-align: center;">Seats R</th>
</tr>
</thead>
<tbody>
<tr>
<td
style="text-align: left;"><span>3-4</span>(lr)<span>5-6</span>(lr)<span>7-8</span></td>
<td style="text-align: right;"></td>
<td style="text-align: center;">mean</td>
<td style="text-align: center;">std</td>
<td style="text-align: center;">mean</td>
<td style="text-align: center;">std</td>
<td style="text-align: center;">min</td>
<td style="text-align: center;">max</td>
</tr>
<tr>
<td colspan="8" style="text-align: center;"><em>(continued)</em></td>
</tr>
<tr>
<td style="text-align: left;">State</td>
<td style="text-align: right;"><span
class="math inline"><em>N</em></span></td>
<td colspan="2" style="text-align: center;">DBS</td>
<td colspan="2" style="text-align: center;"><span
class="math inline">|EG|</span></td>
<td colspan="2" style="text-align: center;">Seats R</td>
</tr>
<tr>
<td
style="text-align: left;"><span>3-4</span>(lr)<span>5-6</span>(lr)<span>7-8</span></td>
<td style="text-align: right;"></td>
<td style="text-align: center;">mean</td>
<td style="text-align: center;">std</td>
<td style="text-align: center;">mean</td>
<td style="text-align: center;">std</td>
<td style="text-align: center;">min</td>
<td style="text-align: center;">max</td>
</tr>
<tr>
<td colspan="8" style="text-align: right;"><em>(continued)</em></td>
</tr>
<tr>
<td style="text-align: left;">AL</td>
<td style="text-align: right;">7</td>
<td style="text-align: center;">0.856</td>
<td style="text-align: center;">0.0119</td>
<td style="text-align: center;">0.113</td>
<td style="text-align: center;">0.0737</td>
<td style="text-align: center;">6</td>
<td style="text-align: center;">7</td>
</tr>
<tr>
<td style="text-align: left;">AR</td>
<td style="text-align: right;">4</td>
<td style="text-align: center;">0.822</td>
<td style="text-align: center;">0.0369</td>
<td style="text-align: center;">0.216</td>
<td style="text-align: center;">0.0000</td>
<td style="text-align: center;">4</td>
<td style="text-align: center;">4</td>
</tr>
<tr>
<td style="text-align: left;">AZ</td>
<td style="text-align: right;">9</td>
<td style="text-align: center;">0.676</td>
<td style="text-align: center;">0.0095</td>
<td style="text-align: center;">0.061</td>
<td style="text-align: center;">0.0558</td>
<td style="text-align: center;">4</td>
<td style="text-align: center;">5</td>
</tr>
<tr>
<td style="text-align: left;">CO</td>
<td style="text-align: right;">8</td>
<td style="text-align: center;">0.610</td>
<td style="text-align: center;">0.0060</td>
<td style="text-align: center;">0.079</td>
<td style="text-align: center;">0.0607</td>
<td style="text-align: center;">2</td>
<td style="text-align: center;">3</td>
</tr>
<tr>
<td style="text-align: left;">CT</td>
<td style="text-align: right;">5</td>
<td style="text-align: center;">0.819</td>
<td style="text-align: center;">0.0240</td>
<td style="text-align: center;">0.296</td>
<td style="text-align: center;">0.0000</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
</tr>
<tr>
<td style="text-align: left;">FL</td>
<td style="text-align: right;">28</td>
<td style="text-align: center;">0.767</td>
<td style="text-align: center;">0.0088</td>
<td style="text-align: center;">0.106</td>
<td style="text-align: center;">0.0422</td>
<td style="text-align: center;">17</td>
<td style="text-align: center;">20</td>
</tr>
<tr>
<td style="text-align: left;">GA</td>
<td style="text-align: right;">14</td>
<td style="text-align: center;">0.700</td>
<td style="text-align: center;">0.0047</td>
<td style="text-align: center;">0.126</td>
<td style="text-align: center;">0.0271</td>
<td style="text-align: center;">9</td>
<td style="text-align: center;">10</td>
</tr>
<tr>
<td style="text-align: left;">IA</td>
<td style="text-align: right;">4</td>
<td style="text-align: center;">0.836</td>
<td style="text-align: center;">0.0276</td>
<td style="text-align: center;">0.091</td>
<td style="text-align: center;">0.0026</td>
<td style="text-align: center;">2</td>
<td style="text-align: center;">2</td>
</tr>
<tr>
<td style="text-align: left;">ID</td>
<td style="text-align: right;">2</td>
<td style="text-align: center;">0.843</td>
<td style="text-align: center;">0.0245</td>
<td style="text-align: center;">0.182</td>
<td style="text-align: center;">0.0000</td>
<td style="text-align: center;">2</td>
<td style="text-align: center;">2</td>
</tr>
<tr>
<td style="text-align: left;">IL</td>
<td style="text-align: right;">17</td>
<td style="text-align: center;">0.667</td>
<td style="text-align: center;">0.0053</td>
<td style="text-align: center;">0.022</td>
<td style="text-align: center;">0.0009</td>
<td style="text-align: center;">5</td>
<td style="text-align: center;">5</td>
</tr>
<tr>
<td style="text-align: left;">IN</td>
<td style="text-align: right;">9</td>
<td style="text-align: center;">0.823</td>
<td style="text-align: center;">0.0147</td>
<td style="text-align: center;">0.165</td>
<td style="text-align: center;">0.0915</td>
<td style="text-align: center;">6</td>
<td style="text-align: center;">8</td>
</tr>
<tr>
<td style="text-align: left;">KS</td>
<td style="text-align: right;">4</td>
<td style="text-align: center;">0.695</td>
<td style="text-align: center;">0.0081</td>
<td style="text-align: center;">0.019</td>
<td style="text-align: center;">0.1323</td>
<td style="text-align: center;">2</td>
<td style="text-align: center;">3</td>
</tr>
<tr>
<td style="text-align: left;">KY</td>
<td style="text-align: right;">6</td>
<td style="text-align: center;">0.794</td>
<td style="text-align: center;">0.0147</td>
<td style="text-align: center;">0.058</td>
<td style="text-align: center;">0.0026</td>
<td style="text-align: center;">5</td>
<td style="text-align: center;">5</td>
</tr>
<tr>
<td style="text-align: left;">LA</td>
<td style="text-align: right;">6</td>
<td style="text-align: center;">0.802</td>
<td style="text-align: center;">0.0257</td>
<td style="text-align: center;">0.198</td>
<td style="text-align: center;">0.0814</td>
<td style="text-align: center;">5</td>
<td style="text-align: center;">6</td>
</tr>
<tr>
<td style="text-align: left;">MA</td>
<td style="text-align: right;">9</td>
<td style="text-align: center;">0.790</td>
<td style="text-align: center;">0.0171</td>
<td style="text-align: center;">0.158</td>
<td style="text-align: center;">0.0000</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
</tr>
<tr>
<td style="text-align: left;">MD</td>
<td style="text-align: right;">8</td>
<td style="text-align: center;">0.717</td>
<td style="text-align: center;">0.0142</td>
<td style="text-align: center;">0.064</td>
<td style="text-align: center;">0.1651</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">3</td>
</tr>
<tr>
<td style="text-align: left;">ME</td>
<td style="text-align: right;">2</td>
<td style="text-align: center;">0.877</td>
<td style="text-align: center;">0.0120</td>
<td style="text-align: center;">0.234</td>
<td style="text-align: center;">0.1772</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">1</td>
</tr>
<tr>
<td style="text-align: left;">MI</td>
<td style="text-align: right;">13</td>
<td style="text-align: center;">0.672</td>
<td style="text-align: center;">0.0034</td>
<td style="text-align: center;">0.108</td>
<td style="text-align: center;">0.0477</td>
<td style="text-align: center;">4</td>
<td style="text-align: center;">6</td>
</tr>
<tr>
<td style="text-align: left;">MN</td>
<td style="text-align: right;">8</td>
<td style="text-align: center;">0.672</td>
<td style="text-align: center;">0.0016</td>
<td style="text-align: center;">0.032</td>
<td style="text-align: center;">0.0601</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">4</td>
</tr>
<tr>
<td style="text-align: left;">MO</td>
<td style="text-align: right;">8</td>
<td style="text-align: center;">0.808</td>
<td style="text-align: center;">0.0048</td>
<td style="text-align: center;">0.104</td>
<td style="text-align: center;">0.0016</td>
<td style="text-align: center;">6</td>
<td style="text-align: center;">6</td>
</tr>
<tr>
<td style="text-align: left;">MS</td>
<td style="text-align: right;">4</td>
<td style="text-align: center;">0.897</td>
<td style="text-align: center;">0.0104</td>
<td style="text-align: center;">0.126</td>
<td style="text-align: center;">0.1213</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">4</td>
</tr>
<tr>
<td style="text-align: left;">MT</td>
<td style="text-align: right;">2</td>
<td style="text-align: center;">0.834</td>
<td style="text-align: center;">0.0365</td>
<td style="text-align: center;">0.286</td>
<td style="text-align: center;">0.0000</td>
<td style="text-align: center;">2</td>
<td style="text-align: center;">2</td>
</tr>
<tr>
<td style="text-align: left;">NC</td>
<td style="text-align: right;">14</td>
<td style="text-align: center;">0.776</td>
<td style="text-align: center;">0.0037</td>
<td style="text-align: center;">0.088</td>
<td style="text-align: center;">0.0541</td>
<td style="text-align: center;">7</td>
<td style="text-align: center;">9</td>
</tr>
<tr>
<td style="text-align: left;">NE</td>
<td style="text-align: right;">3</td>
<td style="text-align: center;">0.680</td>
<td style="text-align: center;">0.0556</td>
<td style="text-align: center;">0.151</td>
<td style="text-align: center;">0.1534</td>
<td style="text-align: center;">2</td>
<td style="text-align: center;">3</td>
</tr>
<tr>
<td style="text-align: left;">NH</td>
<td style="text-align: right;">2</td>
<td style="text-align: center;">0.777</td>
<td style="text-align: center;">0.0372</td>
<td style="text-align: center;">0.425</td>
<td style="text-align: center;">0.0000</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
</tr>
<tr>
<td style="text-align: left;">NJ</td>
<td style="text-align: right;">12</td>
<td style="text-align: center;">0.722</td>
<td style="text-align: center;">0.0000</td>
<td style="text-align: center;">0.146</td>
<td style="text-align: center;">0.0000</td>
<td style="text-align: center;">2</td>
<td style="text-align: center;">2</td>
</tr>
<tr>
<td style="text-align: left;">NM</td>
<td style="text-align: right;">3</td>
<td style="text-align: center;">0.762</td>
<td style="text-align: center;">0.0032</td>
<td style="text-align: center;">0.203</td>
<td style="text-align: center;">0.1236</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">1</td>
</tr>
<tr>
<td style="text-align: left;">NV</td>
<td style="text-align: right;">4</td>
<td style="text-align: center;">0.715</td>
<td style="text-align: center;">0.0125</td>
<td style="text-align: center;">0.082</td>
<td style="text-align: center;">0.1259</td>
<td style="text-align: center;">1</td>
<td style="text-align: center;">2</td>
</tr>
<tr>
<td style="text-align: left;">NY</td>
<td style="text-align: right;">26</td>
<td style="text-align: center;">0.650</td>
<td style="text-align: center;">0.0038</td>
<td style="text-align: center;">0.005</td>
<td style="text-align: center;">0.0384</td>
<td style="text-align: center;">6</td>
<td style="text-align: center;">8</td>
</tr>
<tr>
<td style="text-align: left;">OH</td>
<td style="text-align: right;">15</td>
<td style="text-align: center;">0.846</td>
<td style="text-align: center;">0.0041</td>
<td style="text-align: center;">0.175</td>
<td style="text-align: center;">0.0766</td>
<td style="text-align: center;">10</td>
<td style="text-align: center;">13</td>
</tr>
<tr>
<td style="text-align: left;">OK</td>
<td style="text-align: right;">5</td>
<td style="text-align: center;">0.730</td>
<td style="text-align: center;">0.0236</td>
<td style="text-align: center;">0.161</td>
<td style="text-align: center;">0.0000</td>
<td style="text-align: center;">5</td>
<td style="text-align: center;">5</td>
</tr>
<tr>
<td style="text-align: left;">PA</td>
<td style="text-align: right;">17</td>
<td style="text-align: center;">0.767</td>
<td style="text-align: center;">0.0070</td>
<td style="text-align: center;">0.107</td>
<td style="text-align: center;">0.0390</td>
<td style="text-align: center;">9</td>
<td style="text-align: center;">12</td>
</tr>
<tr>
<td style="text-align: left;">RI</td>
<td style="text-align: right;">2</td>
<td style="text-align: center;">0.805</td>
<td style="text-align: center;">0.0878</td>
<td style="text-align: center;">0.288</td>
<td style="text-align: center;">0.0000</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
</tr>
<tr>
<td style="text-align: left;">SC</td>
<td style="text-align: right;">7</td>
<td style="text-align: center;">0.890</td>
<td style="text-align: center;">0.0048</td>
<td style="text-align: center;">0.169</td>
<td style="text-align: center;">0.0712</td>
<td style="text-align: center;">5</td>
<td style="text-align: center;">6</td>
</tr>
<tr>
<td style="text-align: left;">TN</td>
<td style="text-align: right;">9</td>
<td style="text-align: center;">0.808</td>
<td style="text-align: center;">0.0066</td>
<td style="text-align: center;">0.082</td>
<td style="text-align: center;">0.0440</td>
<td style="text-align: center;">7</td>
<td style="text-align: center;">8</td>
</tr>
<tr>
<td style="text-align: left;">TX</td>
<td style="text-align: right;">38</td>
<td style="text-align: center;">0.672</td>
<td style="text-align: center;">0.0029</td>
<td style="text-align: center;">0.061</td>
<td style="text-align: center;">0.0119</td>
<td style="text-align: center;">23</td>
<td style="text-align: center;">24</td>
</tr>
<tr>
<td style="text-align: left;">UT</td>
<td style="text-align: right;">4</td>
<td style="text-align: center;">0.658</td>
<td style="text-align: center;">0.0346</td>
<td style="text-align: center;">0.025</td>
<td style="text-align: center;">0.0196</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">3</td>
</tr>
<tr>
<td style="text-align: left;">VA</td>
<td style="text-align: right;">11</td>
<td style="text-align: center;">0.777</td>
<td style="text-align: center;">0.0071</td>
<td style="text-align: center;">0.113</td>
<td style="text-align: center;">0.0256</td>
<td style="text-align: center;">3</td>
<td style="text-align: center;">4</td>
</tr>
<tr>
<td style="text-align: left;">WA</td>
<td style="text-align: right;">10</td>
<td style="text-align: center;">0.690</td>
<td style="text-align: center;">0.0060</td>
<td style="text-align: center;">0.037</td>
<td style="text-align: center;">0.0671</td>
<td style="text-align: center;">2</td>
<td style="text-align: center;">4</td>
</tr>
<tr>
<td style="text-align: left;">WI</td>
<td style="text-align: right;">8</td>
<td style="text-align: center;">0.704</td>
<td style="text-align: center;">0.0047</td>
<td style="text-align: center;">0.108</td>
<td style="text-align: center;">0.0539</td>
<td style="text-align: center;">4</td>
<td style="text-align: center;">5</td>
</tr>
<tr>
<td style="text-align: left;">WV</td>
<td style="text-align: right;">2</td>
<td style="text-align: center;">0.906</td>
<td style="text-align: center;">0.0420</td>
<td style="text-align: center;">—</td>
<td style="text-align: center;">—</td>
<td style="text-align: center;">0</td>
<td style="text-align: center;">0</td>
</tr>
</tbody>
</table>

</div>

<div id="refs" class="references csl-bib-body hanging-indent">

<div id="ref-chenrodden2013" class="csl-entry">

Chen, Jowei, and Jonathan Rodden. 2013. “Unintentional Gerrymandering:
Political Geography and Electoral Bias in Legislatures.” *Quarterly
Journal of Political Science* 8 (3): 239–69.

</div>

<div id="ref-dra2020vtd" class="csl-entry">

Dave’s Redistricting App. 2023. *2020 VTD Election Data*.
<a href="https://github.com/dra2020/vtd_data"
class="uri">Https://github.com/dra2020/vtd_data</a>.

</div>

<div id="ref-recom2021" class="csl-entry">

DeFord, Daryl, Moon Duchin, and Justin Solomon. 2021. “Recombination: A
Family of Markov Chains for Redistricting.” *Harvard Data Science
Review* 3 (1).

</div>

<div id="ref-mattinglyduke" class="csl-entry">

Herschlag, Gregory, Robert Ravier, and Jonathan C. Mattingly. 2020.
“Quantifying Gerrymandering in North Carolina.” *Statistics and Public
Policy* 7 (1): 30–38.

</div>

<div id="ref-iowalsa" class="csl-entry">

Iowa Legislative Services Agency. 2021. *Legislative Guide to
Redistricting in Iowa*.
<a href="https://www.legis.iowa.gov/publications/lsa"
class="uri">Https://www.legis.iowa.gov/publications/lsa</a>.

</div>

<div id="ref-federalist54" class="csl-entry">

Madison, James. 1788. *The Federalist Nos. 54–58*. New York Packet.

</div>

<div id="ref-olsonbd" class="csl-entry">

Olson, Brian. 2007--2024. *BDistricting: Computer-Drawn Congressional
and Legislative Districts for All Fifty U.S. States*.
<a href="https://bdistricting.com"
class="uri">Https://bdistricting.com</a>.

</div>

<div id="ref-pildes2004" class="csl-entry">

Pildes, Richard H. 2004. “The Constitutionalization of Democratic
Politics.” *Harvard Law Review* 118: 28.

</div>

<div id="ref-stateline2025" class="csl-entry">

Pluta, Robbie. 2025. *As Supreme Court Pulls Back on Gerrymandering,
State Courts May Decide Fate of Maps*. Stateline.

</div>

<div id="ref-polsbypopper1991" class="csl-entry">

Polsby, Daniel D., and Robert D. Popper. 1991. “The Third Criterion:
Compactness as a Procedural Safeguard Against Partisan Gerrymandering.”
*Yale Law & Policy Review* 9: 301–53.

</div>

<div id="ref-reock1961" class="csl-entry">

Reock, Ernest C. 1961. “A Note: Measuring Compactness as a Requirement
of Legislative Apportionment.” *Midwest Journal of Political Science* 5:
70–74.

</div>

<div id="ref-smithsplit" class="csl-entry">

Smith, Warren D. 2007. *The Shortest Splitline Algorithm for Political
Districting*. Center for Range Voting,
<https://rangevoting.org/GerryExamples.html>.

</div>

<div id="ref-stephanopoulosmcghee2015" class="csl-entry">

Stephanopoulos, Nicholas O., and Eric M. McGhee. 2015. “Partisan
Gerrymandering and the Efficiency Gap.” *University of Chicago Law
Review* 82: 831–900.

</div>

<div id="ref-reynolds1964" class="csl-entry">

Supreme Court of the United States. 1964a. *Reynolds v. Sims*. 377 U.S.
533.

</div>

<div id="ref-wesberry1964" class="csl-entry">

Supreme Court of the United States. 1964b. *Wesberry v. Sanders*. 376
U.S. 1.

</div>

<div id="ref-karcher1983" class="csl-entry">

Supreme Court of the United States. 1983. *Karcher v. Daggett*. 462 U.S.
725.

</div>

<div id="ref-gingles1986" class="csl-entry">

Supreme Court of the United States. 1986. *Thornburg v. Gingles*. 478
U.S. 30.

</div>

<div id="ref-shaw1993" class="csl-entry">

Supreme Court of the United States. 1993. *Shaw v. Reno*. 509 U.S. 630.

</div>

<div id="ref-rucho2019" class="csl-entry">

Supreme Court of the United States. 2019. *Rucho v. Common Cause*. 588
U.S. 684.

</div>

<div id="ref-milligan2023" class="csl-entry">

Supreme Court of the United States. 2023a. *Allen v. Milligan*. 599 U.S.
1.

</div>

<div id="ref-moore2023" class="csl-entry">

Supreme Court of the United States. 2023b. *Moore v. Harper*. 600 U.S.
1.

</div>

<div id="ref-alexander2024" class="csl-entry">

Supreme Court of the United States. 2024. *Alexander v. South Carolina
State Conference of the NAACP*. 602 U.S. 1.

</div>

<div id="ref-callais2026" class="csl-entry">

Supreme Court of the United States. 2026. *Louisiana v. Callais*. 608
U.S. \_\_\_.

</div>

<div id="ref-tarjan1972" class="csl-entry">

Tarjan, Robert. 1972. “Depth-First Search and Linear Graph Algorithms.”
*SIAM Journal on Computing* 1 (2): 146–60.
<https://doi.org/10.1137/0201010>.

</div>

<div id="ref-tiger2020" class="csl-entry">

U.S. Census Bureau. 2020. *TIGER/Line Shapefiles, 2020*. U.S. Department
of Commerce.
<https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html>.

</div>

<div id="ref-census2020pl" class="csl-entry">

U.S. Census Bureau. 2021. *2020 Census Redistricting Data (P.L. 94-171)
Summary File*. U.S. Department of Commerce.
<https://www.census.gov/programs-surveys/decennial-census/about/rdo/summary-files.html>.

</div>

<div id="ref-tiger2024cd119" class="csl-entry">

U.S. Census Bureau. 2024. *TIGER/Line Shapefiles, 2024: 119th
Congressional Districts*. U.S. Department of Commerce.
<https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html>.

</div>

<div id="ref-wang2016" class="csl-entry">

Wang, Samuel S.-H. 2016. “Three Tests for Practical Evaluation of
Partisan Gerrymandering.” *Stanford Law Review* 68: 1263–321.

</div>

<div id="ref-warrington2018" class="csl-entry">

Warrington, Gregory S. 2018. “Quantifying Gerrymandering Using the Vote
Distribution.” *Election Law Journal* 17 (1): 39–57.

</div>

</div>
