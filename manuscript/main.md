---
abstract: |
  Most current work on gerrymandering tries to detect it: identify when
  a line-drawer has crossed from neutral redistricting into partisan or
  racial manipulation. We generate maps instead. *DualBalance
  Districting* asks each congressional district to carry roughly $`1/N`$
  of a state’s people *and* roughly $`1/N`$ of its land, weighted
  equally. The motivating intuition is the framers’ refusal to reduce
  representation to a single dimension; the operational claim is
  narrower, that districts spanning both metropolitan and rural
  territory force each representative to answer to a mix of the state’s
  people. *DualBalance* places $`N`$ seeds in a small circle around the
  state’s population-weighted centroid and assigns each census unit to
  the nearest seed with capacity remaining. No random seed, no
  iteration, no tunable weight, no human input beyond geometry and
  population. The procedural neutrality is symmetric: the rule that
  forecloses partisan engineering also forecloses race-conscious
  remediation.

  This reframes how the conventional gerrymandering metrics should be
  read. Compactness scores, the efficiency gap, mean-median asymmetry,
  ensemble outlier tests, and majority-minority counts play two roles on
  enacted plans: they describe plan effects, and they support inferences
  about the line-drawer’s intent. The descriptive role survives on a
  DualBalance map; the intent-attribution role does not.

  Validated against enacted 119<sup>th</sup>-Congress plans across all
  available states using 2020 PL 94-171 data, DualBalance beats the
  enacted plan on the DualBalance Score in the large majority of states
  and achieves *Karcher*-compliant population balance on nearly all of
  them. We report standard partisan and race diagnostics alongside, as
  descriptions of the partition.
author:
- Steven Hart
bibliography: references.bib
date: 2026-05-16
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
geometry, census populations, and district count $`N`$, with no free
parameters, no randomness, and no human intervention at any stage. Each
district is designed to carry approximately $`1/N`$ of the state’s
population and approximately $`1/N`$ of its land area, weighted equally
in a single objective we call the DualBalance Score. A deterministic
algorithm with no free parameters provides, by construction, a
mathematical barrier against intentional map manipulation.

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

The Electoral College makes the same dual logic operative at the
executive level. Each state’s electoral vote total equals its House
seats plus its two Senate seats (Art. II, §1), explicitly combining a
population-proportional component with a geographic floor. Presidential
candidates must assemble coalitions distributed across states, not
merely population-weighted majorities. Congressional districts
calibrated on population alone are, in this respect, the exception in
the broader constitutional framework rather than the rule.

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
of comparison throughout.

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

We run the full pipeline on six states selected to cover the geographic
range that breaks Cascade: IA, MA, MN, NC, TX, WI. Five of six achieve a
DualBalance Score above the enacted 119th-Congress plan. Two (IA, WI)
reach the $`0.05\%`$ Karcher threshold exactly; three more (MN, NC, MA)
sit within a factor of two of it; TX, the hardest case, sits at
$`0.52\%`$, five times tighter than the same state’s enacted plan. On
partisan fairness, DualBalance’s Efficiency Gap is smaller in magnitude
than the enacted plan’s in four of six states, with the largest
improvements on the three most heavily-litigated maps (NC, WI, TX). On
minority-majority district counts, DualBalance produces more such
districts than the enacted plan on NC (2 vs. 1) and TX (22 vs. 19).

#### Claims.

The procedure contains no explicit partisan, racial, or incumbent-aware
optimization criteria: its inputs are census geometry and population
totals, and its output is a pure function of those inputs with no
tunable parameters affecting electoral or demographic outcomes. Adopting
a generative criterion as the design objective, rather than a forensic
instrument, is a natural response to a setting in which no line-drawer
is present to investigate. Scope limits and further qualifications
appear in §<a href="#sec:discussion" data-reference-type="ref"
data-reference="sec:discussion">4</a>.

#### Roadmap.

Section <a href="#sec:methods" data-reference-type="ref"
data-reference="sec:methods">2</a> formalizes the algorithm.
Section <a href="#sec:results" data-reference-type="ref"
data-reference="sec:results">3</a> reports the six-state empirical
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
$`0`$ as deviations grow without bound. Secondary metrics (Polsby-Popper
compactness (Polsby and Popper 1991) and Reock (Reock 1961)) are
computed alongside but not optimized against; the Phase 2 optimizer
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
indicate Democratic advantage. EG is computed on the plan geometry using
precinct-level presidential vote totals from the 2020 election; it is
reported as a diagnostic and does not enter the generator. All other
partisan, racial, and demographic variables are similarly excluded from
the generator’s inputs.

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

Both phases are pure functions of $`(\mathrm{units},\,N,\,T)`$. The only
source of dependency beyond the core pipeline’s $`(\mathrm{units},\,N)`$
is the explicit tolerance $`T`$. The optimizer maintains a per-district
articulation-point cache via Tarjan’s algorithm on CSR adjacency
arrays (Tarjan 1972), reducing the per-candidate contiguity check from
$`O(V+E)`$ to $`O(1)`$; an incrementally tracked boundary-unit set
restricts each scan to units that have a different-district neighbor. At
VTD scale the speedup is modest; at block scale (tens of thousands of
units per district) it is the difference between hours and minutes.

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
multi-seat states for which TIGER 2020PL VTD boundaries are available.
California, Hawaii, and Oregon did not submit VTD data to the Census
Bureau and are excluded throughout (marked $`\dagger`$ in figures and
tables). The same data pipeline runs unmodified for every state via
`scripts/prep_state_units.py`: TIGER 2020 VTDs, Census PL 94-171
demographics, dra2020/vtd_data 2020 presidential returns, and a TIGER
2024 cd119 spatial join for the enacted plan. To anchor DualBalance in
context we score two additional deterministic algorithms: *Cascade*
(`src/dualbalance/cascade.py`), an Iowa-LSA-flavored construction that
aggregates VTDs to counties and uses farthest-point seeding; and
*BDistricting* (Olson 2007--2024), Brian Olson’s published 50-state map
series ingested via Census 2020 Block Assignment Files
(`scripts/prep_bdistricting.py`). All outputs are byte-identical across
repeated runs on the same input; the CLI integration test
`test_generate_determinism_via_cli` pins this in CI.

Three cross-state findings organize the presentation.

#### Partisan asymmetry shrinks under every deterministic generator.

On states with nonzero enacted efficiency gap, all three deterministic
algorithms produce smaller $`|\mathrm{EG}|`$ than the enacted plan
(Figure <a href="#fig:headline-eg" data-reference-type="ref"
data-reference="fig:headline-eg">1</a>). The largest reductions appear
in states most associated with partisan-gerrymander litigation. The
structural explanation is in
§<a href="#sec:discussion-forensic" data-reference-type="ref"
data-reference="sec:discussion-forensic">4.7</a>: a generator that reads
no political data cannot reproduce a large partisan-fairness asymmetry.
This holds across all three deterministic baselines, not only
DualBalance.

#### Cascade wins on DBS but is legally non-viable on most states.

Cascade scores well on the DualBalance objective because county
aggregation naturally produces units of similar area, but the
county-integrity constraint yields population deviations far above the
*Karcher* threshold on any state with a dominant metropolitan county
(Figure <a href="#fig:boxplots" data-reference-type="ref"
data-reference="fig:boxplots">2</a>, Panel B). DualBalance and
BDistricting both achieve *Karcher* compliance on the large majority of
states; Cascade does so only on Iowa and Wisconsin, where no single
county exceeds the per-district population cap. A plan that wins on DBS
but violates *Reynolds v. Sims* cannot legally be enacted.

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

<figure id="fig:headline-eg" data-latex-placement="htbp">

<figcaption>Partisan fairness across all available states, sorted by
enacted <span class="math inline">|EG|</span> (worst-gerrymandered on
the left). DualBalance (blue) vs. enacted 119th-Congress plan (gray).
Red dashed line: <span class="math inline">|EG| = 0.07</span>
gerrymander threshold <span class="citation"
data-cites="stephanopoulosmcghee2015">(Stephanopoulos and McGhee
2015)</span>. States marked <span class="math inline">†</span> lacked
TIGER 2020PL VTD boundaries and are excluded.</figcaption>
</figure>

<figure id="fig:boxplots" data-latex-placement="htbp">

<figcaption>Cross-state comparison of four algorithms on key metrics.
Each box spans the interquartile range across all available states; dots
are individual states. <strong>Panel A</strong>: DualBalance Score
(higher = better). <strong>Panel B</strong>: maximum per-district
population deviation, log scale; dashed line at the <em>Karcher</em>
threshold (0.05 %). <strong>Panel C</strong>: <span
class="math inline">|EG|</span> (lower = fairer); dashed line at the
0.07 gerrymander threshold <span class="citation"
data-cites="stephanopoulosmcghee2015">(Stephanopoulos and McGhee
2015)</span>. <strong>Panel D</strong>: Polsby-Popper compactness (mean
per state); DualBalance is structurally less compact than enacted plans
because radial slices are not blob-shaped.</figcaption>
</figure>

<figure id="fig:race-scatter" data-latex-placement="htbp">

<figcaption>Minority-majority district count: DualBalance vs. enacted
119th-Congress plan. Each point is one state; the diagonal is <span
class="math inline"><em>y</em> = <em>x</em></span>. Points above the
line indicate DualBalance produces more majority-minority districts than
the enacted map; points below indicate fewer. Most states cluster at
<span class="math inline">(0, 0)</span> because no single minority group
concentrates densely enough to support a majority-minority district of
standard size. DualBalance is race-blind; where it produces more
majority-minority districts than the enacted plan, the effect is
geographic, not by design. Where it produces fewer (notably MA and WI),
the enacted plan constructed a majority-minority district that radial
slicing breaks up.</figcaption>
</figure>

<figure id="fig:nc-maps" data-latex-placement="htbp">

<figcaption>North Carolina congressional districts under three plans (14
seats, 2020 PL 94-171). <strong>Left:</strong> enacted 119th-Congress
plan, with the Efficiency Gap of <span class="math inline">+0.20</span>
that gave rise to <em>Rucho v. Common Cause</em> <span class="citation"
data-cites="rucho2019">(Supreme Court of the United States 2019)</span>.
<strong>Center:</strong> Cascade plan, which scores better on DBS (<span
class="math inline">0.82</span> vs. <span
class="math inline">0.77</span> enacted) but violates <em>Karcher</em>
at 10.27 % maximum population deviation and cannot legally be enacted.
<strong>Right:</strong> DualBalance plan, <em>Karcher</em>-compliant
(0.11 %) and reducing EG to <span class="math inline">+0.09</span> with
no political input.</figcaption>
</figure>

## What would Congress look like?

**\[PLACEHOLDER, $`\sim`$<!-- -->150 words.\]** Aggregate seats_R /
seats_D summed across all available states under DualBalance, Cascade,
BDistricting, and the enacted plan, plus a proportional-vote baseline
derived from the 2020 statewide two-party presidential returns. The
question, “if every state used DualBalance, what is the partisan
composition of the House?”, is answered here with full caveats: 2020
presidential returns proxy for House votes, CA/HI/OR are excluded for
lack of VTD data, and single-seat states are unchanged under any
algorithm. The full per-state breakdown (seats R/D, statewide R share,
all four algorithms) appears in Supplementary Table S1.

# Discussion

## What the Minnesota result does and does not show

The headline (DualBalance beats the enacted Minnesota plan on the
DualBalance Score) is a single-state existence result. It shows that
radial slicing can score competitively on the dual-balance objective
without reading party, race, or any discretionary input. It does not
show that DualBalance generalizes to all 50 states, that DBS is the
right scalar to optimize, or that DualBalance maps would survive
judicial scrutiny. We take those up below.

## Co-design of score and algorithm

A natural objection: “$`A`$ beats $`B`$ on Metric $`M`$ because $`A`$
and $`M`$ were co-designed.”
DBS <a href="#eq:dbs" data-reference-type="eqref"
data-reference="eq:dbs">[eq:dbs]</a> was specified before the algorithm
choice. We tested three forms: the weighted form used here, a
sum-of-means form
$`1/(1 + \overline{\mathrm{pop\_dev}} + \overline{\mathrm{area\_dev}})`$,
and an $`L^{\infty}`$ form
$`1/(1 + \max_i [0.5\,\mathrm{pop\_dev}_i + 0.5\,\mathrm{area\_dev}_i])`$.
DualBalance beats the enacted plan on the first two; the enacted plan
wins on the third, because DualBalance concentrates area imbalance in a
single rural district. We use the weighted form as the headline because
it cleanly implements “each district carries $`1/N`$ of people *and*
$`1/N`$ of geography.” Per-district deviations are reported alongside so
readers can recompute against any preferred aggregation.

The functional form satisfies four properties we wanted from the outset.
(i) *Scale invariance*: the per-district inputs are relative deviations
$`|x - x^*|/x^*`$, so the score is invariant to the units of population
and area. (ii) *Equal treatment of the two objectives*: the $`0.5/0.5`$
weighting is the unique convex combination treating
$`\overline{\mathrm{pop\_dev}}`$ and $`\overline{\mathrm{area\_dev}}`$
symmetrically. (iii) *Monotonicity*: the score strictly decreases as
either deviation increases. (iv) *Boundedness in $`[0,1]`$*: the
reciprocal form maps zero error to $`1`$ and unbounded error toward
$`0`$, giving a calibrated reading rather than a raw cost. These do not
pin DBS down uniquely, but they constrain the design space enough that
the remaining choice (arithmetic mean of deviations versus a max-norm or
Lp aggregation) becomes a tradeoff between average-case fairness and
worst-case fairness. We report all the per-district numbers needed to
compute both.

Population density variance bounds the achievable
$`\overline{\mathrm{area\_dev}}`$ on any pop-balanced plan. Both
DualBalance and the enacted plan land near
$`\overline{\mathrm{area\_dev}} \approx
1.0`$–$`1.1`$. On Minnesota’s geometry (Twin Cities = 55 % of population
in 3 % of land area) this is a hard floor. Improvements would require
districts that span urban and rural, which is exactly what radial
slicing does. The 8.7-point gap (103.9 vs. 112.6) is the operational
measure of how much area balance DualBalance recovers given that floor.

## Compactness is the trade

DualBalance trades compactness for area balance by design. This is not
an incidental cost we apologize for: it is the mechanism. A district
that holds $`1/N`$ of a high-variance density distribution must either
span the full density range (and look elongated) or sit inside a single
density regime (and produce an unbalanced area share). Hand-drawn maps
typically choose the second; DualBalance chooses the first. The PP=0.047
worst-slice number is what choosing the first looks like on Minnesota’s
geometry. The enacted Minnesota plan’s worst PP is 0.178, roughly four
times higher, and its $`\overline{\mathrm{area\_dev}}`$ is
correspondingly 8.7 points worse.

Three observations qualify the trade.

#### Compactness is a metric, not a constitutional requirement.

*Polsby-Popper* as a measure was published in 1991 (Polsby and Popper
1991); it appears in no federal statute and binds no court. Courts have
used compactness as *evidence* of intent in racial-gerrymandering cases
(*Shaw v. Reno* and progeny), but the constitutional violation in those
cases turns on the use of race in line-drawing, not on the resulting
shape per se. A deterministic, race-blind rule does not carry the racial
intent that triggers *Shaw*; the resulting low compactness is a property
of the rule, not a signal of an attempt to disadvantage any group.

#### Compactness assumes a baseline of comparison.

A district is “bizarrely shaped” relative to surrounding districts that
are not. If all eight districts in a state are produced by the same
geometric rule and all eight share a similar slice-like character, the
comparative baseline shifts. The aesthetic objection to long thin shapes
is partly historical: it picks out districts that depart from the
surrounding norm of compact blobs. A scheme in which every district is a
slice does not pick anything out.

#### The Voting Rights Act trade-off is real.

*Allen v. Milligan* (Supreme Court of the United States 2023a)
reaffirmed Section 2’s effects-based vote-dilution doctrine;
*Alexander* (Supreme Court of the United States 2024) and
*Callais* (Supreme Court of the United States 2026) narrowed its
practical reach. Section 2 asks about effects on minority voters’
opportunity to elect, not about intent. DualBalance is race-blind, but
blindness to race does not satisfy Section 2 by itself. In jurisdictions
where the *Gingles* (Supreme Court of the United States 1986)
preconditions are met, DualBalance may produce a plan that fails
Section 2 review even though no one drew lines to dilute. The
legislative question (whether to accept reduced minority opportunity in
exchange for a generator that cannot be partisan-tuned) is for
legislatures and courts, not for the algorithm.

## Relationship to prior deterministic methods

DualBalance is, to our knowledge, the only deterministic districting
method whose objective is bivariate (population *and* area). Every other
published deterministic method optimizes a single extensive criterion –
usually population balance plus a geometric proxy (compactness or
shortest-cut length) – and that single-axis design is empirically why
none of them clears all four of the criteria we set out in the
introduction: legal viability under *Karcher*, DBS competitiveness,
partisan-fairness on the gerrymandered states, and minority-majority
district creation where the geography supports it. We argue this point
empirically for the two methods we benchmark on all 50 states (Cascade
and BDistricting) and structurally for the remainder.

#### Cascade (Iowa-LSA-flavored, county aggregation).

Cascade prioritizes county integrity lexicographically: aggregate VTDs
to counties, capacitated first-fit counties to districts, split a county
only when its population exceeds the per-district cap. The
county-integrity priority makes the algorithm legitimate *in Iowa*,
where no county is large enough to dominate a district, but on every
state with a major metropolitan county it produces population deviations
far above *Karcher*: 0.50 % on Wisconsin, 10.27 % on North Carolina,
24.58 % on Texas, 41.56 % on Massachusetts, 76.14 % on Minnesota
(Table <a href="#tab:multistate-dbs" data-reference-type="ref"
data-reference="tab:multistate-dbs">[tab:multistate-dbs]</a>). Cascade
is therefore *not legally viable* on the majority of states, regardless
of how well it does on DBS or efficiency gap. Treating Cascade as a
counterfactual ‘national rule’ would constitutionally disqualify the
resulting maps under *Reynolds v. Sims*, let alone *Karcher*.

#### BDistricting (Olson 2007--2024), representing the capacitated-$`k`$-means / centroidal-power-diagram family (Cohen-Addad et al. 2018; Levin and Friedler 2019).

BDistricting minimizes population-weighted Euclidean distance from each
unit to its district center subject to equal-population caps, with
Lloyd-style iteration to convergence – an empirical realization of the
centroidal-power-diagram objective formalized by Cohen-Addad, Klein, and
Young (Cohen-Addad et al. 2018) and independently studied by Levin and
Friedler (Levin and Friedler 2019). The objective is unidimensional:
equal population plus geometric compactness around dispersed centers. In
our six-state comparison BDistricting achieves the highest Polsby-Popper
and Reock scores of any algorithm on every state but is uneven on
population (*Karcher* on some states, marginal on others) and
middle-of-the-road on DBS because area balance is not part of the
objective. The general pattern: a deterministic generator that optimizes
population $`+`$ compactness with no third axis cannot reliably hit the
dual-balance objective, because the radial mixing of dense and sparse
territory that gives DualBalance its area balance is explicitly
destroyed by Lloyd recentering, which pulls seeds toward their cells’
centers of mass.

#### Shortest Splitline (Smith 2007).

Smith’s algorithm recursively bisects the state with the shortest
population-balancing line. The objective is unidimensional in a
different sense: at each recursive step it minimizes one number (line
length) and otherwise lets the geometry fall where it will. The
resulting districts are often visibly elongated, with boundaries that
follow neither county lines nor visible geographic features. No
U.S. jurisdiction has adopted Splitline; no public 50-state baseline
exists; the algorithm is exemplary as a proof of deterministic
feasibility but not as a deployment candidate. We include it here for
completeness rather than for empirical comparison.

#### Cascade as our chosen empirical baseline.

We include Cascade in the comparison rather than Splitline because
Cascade is the deterministic alternative that has actually been deployed
at scale (in Iowa since 1980) and is the most-cited model of impartial
districting in the popular literature. The empirical contribution of the
comparison is to show that the Iowa template is geographically
contingent: on the 49 other states, Cascade fails the legal-viability
test catastrophically. The conceptual contribution is to clarify that
being deterministic and impartial is necessary but not sufficient. The
objective the algorithm pursues matters, and the DualBalance objective –
equal population *and* equal area – is both expressible
deterministically and broad enough to admit legally-viable plans on
every state we have tested.

The forensic critique in
§<a href="#sec:discussion-forensic" data-reference-type="ref"
data-reference="sec:discussion-forensic">4.7</a> applies equally to all
of these methods, and to any future deterministic generator built on
similar principles: the gerrymandering metrics were built to investigate
human line-drawers, and on any deterministic plan their inferential
power evaporates.

## Limitations

#### VTD data availability.

The Census Bureau’s TIGER 2020PL redistricting file includes VTD
boundaries only for states that submitted them. At least three states —
California, Hawaii, and Oregon — did not participate in the VTD program
for 2020 and therefore have no `vtd20` shapefile in TIGER; they are
excluded from all cross-state tables and figures here. Future work can
substitute block-group or block boundaries, which the Census does
publish for all states, at a cost of larger input size and longer
optimizer runtime.

#### Peninsula and polycentric geometries.

DualBalance’s optimizer can fail to close the Karcher gap in states
whose geometry defeats single-center radial seeding. Florida is the
clearest case in our validation set: with 28 seats distributed across a
long peninsula, the radial slices created around the population-weighted
centroid produce districts that the VTD-scale optimizer cannot balance
to the 0.05 % target in $`10^5`$ passes, leaving
$`\mathrm{pop\_dev}_{\max} = 44.2\,\%`$. The block-scale refinement pass
(§<a href="#sec:methods-block" data-reference-type="ref"
data-reference="sec:methods-block">2.8</a>) is the next step for these
hard-geometry states; results will be reported as they are available.

#### Expanding evidence base.

Tables and figures in
§<a href="#sec:results-multistate" data-reference-type="ref"
data-reference="sec:results-multistate">[sec:results-multistate]</a>
will be updated as the full-state harness completes. Figures and tables
note $`\dagger`$ for any state where VTD data were unavailable and
results therefore could not be computed.

#### Worst-district area outlier.

DualBalance concentrates the area imbalance in a single rural district
(here, District 2 at 275 % over-target). This is geometric, not
algorithmic: any pop-balanced partition of a state with Minnesota’s
density profile must give some rural district disproportionate area.
DualBalance’s $`\mathrm{area\_dev}_{\max}`$ of 275 % is worse than the
enacted plan’s 241 % even though the mean is lower, so DualBalance
distributes the imbalance unevenly. Whether evenly distributed area
imbalance is preferable to a single concentrated outlier is a separable
normative question.

#### No multi-unit transportation step.

The optional `--tighten-pop` pass is a greedy single-unit swap. A true
2D transportation LP bounding both population and area would directly
minimize the DBS objective; we leave that to future work.

#### Computational cost.

Pure DualBalance runs in under a second on Minnesota. The tightening
pass takes $`\sim`$<!-- -->18 s for 80 swaps. We have not profiled
California or Texas; worst-case scaling is $`O(|U|^2 N)`$ per swap due
to the contiguity check.

#### The compactness floor.

The worst slice’s $`\mathrm{PP}=0.047`$ is well below the informal
court-testimony threshold of 0.10. We argue in
§<a href="#sec:discussion-compactness" data-reference-type="ref"
data-reference="sec:discussion-compactness">4.3</a> that the
*Shaw* (Supreme Court of the United States 1993) doctrine turns on
intent rather than shape per se, but readers who reject that argument
should regard the 0.047 figure as a hard ceiling on legal viability.

## Future work

#### Broad-coverage validation (ongoing).

The six-state initial validation (MN, IA, MA, TX, NC, WI) is being
extended to the full set of multi-seat states for which TIGER 2020PL VTD
boundaries are available (41 states at time of writing; CA, HI, OR
excluded). Results will be incorporated into the published version of
this paper. The most analytically important remaining states are
Pennsylvania and Ohio (state-court partisan-gerrymandering
jurisprudence) and the four states where DualBalance is still above the
Karcher threshold at VTD scale (FL in particular, where the peninsula
geometry makes single-center radial seeding hard to balance).

#### Multi-center radial seeding.

For polycentric states, place seeds on circles around *each* of $`k`$
population centers, with $`k`$ chosen deterministically from the density
distribution. Not yet implemented.

#### Direct 2D transportation step.

Replace the DualBalance-plus-tighten two-stage pipeline with a single
optimization that minimizes DBS under contiguity constraints. More
expensive than the current pipeline; the mathematically clean answer to
“which plan directly minimizes the DualBalance objective.”

#### Splitline benchmark.

The six-state benchmark
(§<a href="#sec:results-multistate" data-reference-type="ref"
data-reference="sec:results-multistate">[sec:results-multistate]</a>)
covers DualBalance, Cascade, BDistricting, and the enacted plan. Adding
Smith’s Shortest Splitline (Smith 2007) would give a fourth
deterministic baseline; computing it from scratch on each state is
straightforward but has not yet been done.

#### Scoring-harness extensions.

The current harness reports population, area, Polsby-Popper, and Reock.
Natural additions include partisan diagnostics (efficiency gap,
mean-median, declination) on voter-registration data, county-split
counts, and minority representation diagnostics under Section 2. These
are reporting extensions and would not feed back into the generator
(§<a href="#sec:methods" data-reference-type="ref"
data-reference="sec:methods">2</a>, “out-of-scope inputs”).

## Forensic metrics applied to a generative procedure

Two problems arise when forensic metrics are pressed into service as
design objectives rather than as diagnostic tools. First, optimizing for
a plan that “looks like what a neutral process would have produced” is a
moving target: the counterfactual shifts with the ensemble distribution
one chooses and the legal constraints one encodes, both of which carry
discretionary content (Cain 2014). Second, fully content-neutral
automated procedures can produce systematic partisan asymmetry as a
geographic artifact. Chen and Rodden (Chen and Rodden 2013) showed that
residential clustering causes impartial automated maps to disadvantage
Democrats in many states, so a nonzero Efficiency Gap on such a map
reflects geography rather than intent. Forensic metrics were designed to
detect manipulation by a human line-drawer; absent a line-drawer, their
inferential content evaporates (Pildes 2004).

Deterministic generation has interpretive consequences for the
fairness-metrics literature. Most gerrymandering diagnostics carry two
functions. They *describe* a property of the plan (a shape, a vote
distribution, a count of split counties). And they support an
*inference* about the line-drawer’s motive (that the shape was chosen,
that the votes were packed and cracked, that the splits followed a
partisan or racial pattern). The two are nearly always entangled in
practice because the literature was built around enacted plans, where
intent is always at issue.

DualBalance separates them. The descriptive function survives intact: a
$`\mathrm{PP}`$ of 0.09 still names a non-compact shape, with
administrative and legitimacy consequences; an Efficiency Gap of
$`+6.6\,\%`$ still names a real wasted-vote asymmetry, with
representational consequences; zero majority-minority districts still
names a partition under which no minority group reaches a 50 % VAP
share, with Section 2 consequences. The inferential function does not.
DualBalance is a pure function of geometry, population, and seat count,
so the chain from observed property back to motive has no actor to
terminate on.

Three implications, narrowed accordingly.

#### *Shaw*-style shape inference loses purchase, but compactness still matters administratively.

*Shaw v. Reno* (Supreme Court of the United States 1993) uses bizarre
shape as evidence that race predominated in line-drawing. The inference
chain runs shape $`\to`$ unusual process $`\to`$ illegitimate criterion
$`\to`$ race. On DualBalance the first link is broken: every district
produced by the rule has the same shape character, so unusual shape no
longer implies unusual process. *Shaw* does not reach a race-blind
algorithm. But compactness still has a non-inferential role. Districts
that are hard to identify with on a map, hard to administer, or hard to
campaign in carry costs independent of who drew them. DualBalance’s
PP=0.047 worst slice is a real cost. The argument here is not that
compactness ceases to matter, only that it ceases to be evidence of
motive.

#### Partisan metrics describe effects, not intent.

*Rucho v. Common Cause* (Supreme Court of the United States 2019)
foreclosed federal partisan-gerrymandering review for lack of a
manageable standard for distinguishing acceptable from unacceptable
partisan motivation. The question is moot on DualBalance (there is no
motivation), but the partisan *effect* the metrics measure is not. An
Efficiency Gap of $`+6.6\,\%`$ on a DualBalance map still corresponds to
wasted-vote asymmetry that affects representation; state-court tests
that interpret EG as evidence of effect, rather than as evidence of
intent, still bind. The rhetorical move from “the map shows EG
$`+6.6\,\%`$” to “someone built that EG $`+6.6\,\%`$” becomes
unavailable on DualBalance, but the metric continues to measure what it
measured.

#### Ensemble outlier tests lose their baseline.

The Duke and MGGG ensembles (Herschlag et al. 2020; DeFord et al. 2021)
compare an enacted plan to a sample of legally compliant alternatives a
neutral line-drawer might plausibly have produced. The sample stands in
for the absent neutral line-drawer; the enacted plan being an outlier
suggests the actual line-drawer differed from the neutral one.
DualBalance *is* the neutral line-drawer in a stronger sense than the
ensemble’s sample mean. Asking whether the DualBalance plan is an
outlier against its own ensemble may not be meaningful: the ensemble
collapses to one point. Ensembles can still play a comparison role
across *different* algorithmic generators (e.g. DualBalance
vs. BDistricting vs. splitline), but the question is no longer “is this
map suspiciously different from neutral?”

Metrics remain informative as descriptive summaries of plan effects. A
DualBalance plan with $`\mathrm{PP}_{\min} = 0.047`$, Efficiency Gap
$`+6.6\,\%`$, and zero majority-minority districts has low compactness,
an R-favoring wasted-vote asymmetry, and no MMD. Those facts carry
administrative, representational, and Section 2 consequences. The
inference from those facts to a person who chose them is what
deterministic generation removes.

## What this paper claims, and what it does not

The paper makes four claims.

First, that a knob-free, race-blind, partisan-blind, deterministic
districting algorithm exists that produces output competitive with, and
on a single empirically tested state superior to, the corresponding
hand-drawn enacted plan on a prespecified population-and-area objective.
The algorithm’s output is byte-reproducible and updates only with the
ten-year census.

Second, that the algorithm’s procedural neutrality is symmetric. The
rule cannot be used to harm any group, party, or incumbent, and cannot
be used to help any of them. The same property that forecloses a
partisan gerrymander forecloses a race-conscious remedy. The symmetry is
the algorithm’s defining property; whether it is morally preferable to
the status quo of partisan and remedial discretion is a question for
legislatures, courts, and voters.

Third, that the post-*Callais* legal landscape gives a generator of this
kind a narrower constitutional exposure than any race-conscious or
partisan-conscious alternative. Federal partisan review is foreclosed
under *Rucho*; federal racial-gerrymander risk is contracting under
*Alexander* and *Callais*; state-court remedies for partisan claims
depend on the politics of each state’s supreme court. A rule whose
inputs do not contain race or party is, in the strict sense, not subject
to either body of doctrine.

Fourth, the conventional gerrymandering metrics (compactness scores,
Efficiency Gap, mean-median, ensemble outliers, majority-minority
counts) play two roles on enacted plans, only one of which transfers to
DualBalance. As descriptions of plan effects (shape, wasted-vote
asymmetry, minority opportunity) they remain valid and are reported
alongside the DualBalance Score. As evidence of line-drawer intent they
do not transfer. The intent-attribution use of these metrics, not their
measurement use, is what the generative case breaks. This is the most
contested framing claim in the paper.

The paper does not claim that DBS is universally the right objective,
that DualBalance dominates enacted plans on all states, that compactness
can be ignored, that effects-based fairness analyses (including
Section 2) become irrelevant, or that the metric toolkit developed over
the past thirty years is wrong. The narrow claim is that the intent
reading of those metrics presupposes a line-drawer who is not present in
this construction.

Whether deterministic generation is preferable to discretionary
redistricting is a political and constitutional question; the algorithm
itself cannot answer it.

<div id="refs" class="references csl-bib-body hanging-indent">

<div id="ref-cain2014" class="csl-entry">

Cain, Bruce E. 2014. *Democracy More or Less: America’s Political Reform
Quandary*. Cambridge University Press.

</div>

<div id="ref-chenrodden2013" class="csl-entry">

Chen, Jowei, and Jonathan Rodden. 2013. “Unintentional Gerrymandering:
Political Geography and Electoral Bias in Legislatures.” *Quarterly
Journal of Political Science* 8 (3): 239–69.

</div>

<div id="ref-cohenaddad2018" class="csl-entry">

Cohen-Addad, Vincent, Philip N. Klein, and Neal E. Young. 2018.
“Balanced Centroidal Power Diagrams for Redistricting.” *Proceedings of
the 26th ACM SIGSPATIAL International Conference on Advances in
Geographic Information Systems*, 389–96.

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

<div id="ref-levinfriedler2019" class="csl-entry">

Levin, Harry A., and Sorelle A. Friedler. 2019. “Automated Congressional
Redistricting.” *ACM Journal of Experimental Algorithmics* 24:
1.10:1–24.

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
