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

  On Minnesota (4,110 voting tabulation districts (VTDs), 8 seats, 2020
  PL 94-171), DualBalance beats the enacted 119<sup>th</sup>-Congress
  plan on the DualBalance Score ($`0.6472`$ vs. $`0.6390`$). We report
  standard partisan and race diagnostics alongside, as descriptions of
  the partition.
author:
- Steven Hart
bibliography: references.bib
date: 2026-05-16
title: |
  DualBalance Districting:\
  From Detection to Generation
---

# Introduction

## The Problem Is Getting Worse

U.S. legislative districts are drawn by human beings under nominal
constraints, and the structure invites gerrymandering. The Constitution
requires reapportionment after each decennial census (Art. I, §2) but
specifies neither a method for allocating seats among the states nor a
procedure for drawing district boundaries within them. Both decisions
have, by default, been delegated to political actors. The result is what
the design predicts: maps drawn to advantage whichever party controls
the pen at the moment of redistricting.

The federal courts have largely stepped back from the problem. In *Rucho
v. Common Cause* (Supreme Court of the United States 2019), the Supreme
Court held 5–4 that partisan-gerrymandering claims present
nonjusticiable political questions; the Court conceded the practice is
“incompatible with democratic principles” but found no manageable
judicial standard. After *Rucho*, the only federal channel for
gerrymandering review is racial. That channel has now narrowed as well.
Section 2 of the Voting Rights Act, as construed in *Thornburg
v. Gingles* (Supreme Court of the United States 1986), requires
majority-minority districts where the three Gingles preconditions are
met. The Court reaffirmed this in *Allen v. Milligan* (Supreme Court of
the United States 2023a). One year later, *Alexander v. South Carolina
Conf. of the NAACP* (Supreme Court of the United States 2024) raised
plaintiffs’ evidentiary burden; *Louisiana v. Callais* (Supreme Court of
the United States 2026) held in April 2026 that even a plan drawn to
comply with a prior Section 2 order may violate the Equal Protection
Clause if Section 2 did not in fact compel a race-based remedy. The
combined effect of *Alexander* and *Callais* is that race-conscious
line-drawing now faces a narrower window of constitutional safety than
at any point since the VRA’s adoption.

Federal partisan review is foreclosed. Section 2 has been narrowed.
State review under *Moore v. Harper* (Supreme Court of the United States
2023b) remains, but is uneven and politically contingent: roughly ten
state supreme courts have so far recognized state-constitutional
partisan-gerrymandering claims (Pluta, Robbie 2025); the rest have not.
Several states have already redrawn maps mid-decade in response to
electoral results rather than census revision. Redistricting is shifting
from a once-per-decade event into a continuous partisan exercise. The
trend line is bad and accelerating.

## The Founders’ Refusal to Reduce Representation to a Single Axis

The U.S. Constitution divides representation along two axes: the House
apportions seats by population (Art. I, §2), the Senate by sovereign
state regardless of population (Art. I, §3). Madison’s defense in
*Federalist* Nos. 54–58 (Madison 1788) treats this as a principled
refusal to collapse representation onto a single dimension. We do not
claim the Senate represents land area; it represents states. What we
take from the bicameral compromise is a weaker but still useful
intuition: *within a chamber*, the choice to make districts equal in
only one extensive quantity – population – is a choice, not a necessity.
A second extensive quantity, geographic area, is available,
well-defined, and computable from the same census data. A district that
spans both metropolitan and rural territory forces each elected
representative to answer to constituents across the state’s density
range, rather than to a single dense metro or a single rural hinterland.

This is a mathematical challenge, not a free choice. Real states are not
uniform in population density: a typical state varies by two to three
orders of magnitude between its densest urban tract and its sparsest
rural one. Equal population, equal area, contiguity, and shape
compactness are not simultaneously achievable in general. Some trade-off
is unavoidable. The question, then, is which trade-off to make, how
transparently to make it, and whether the resulting procedure can be
defended as impartial.

## Existing Metrics Are Forensic, Not Generative

A substantial mathematical literature has developed quantitative tests
for gerrymandering: Polsby-Popper (Polsby and Popper 1991) and
Reock (Reock 1961) compactness; the Efficiency Gap (Stephanopoulos and
McGhee 2015); mean–median, lopsided wins, and partisan-asymmetry
$`t`$-tests (Wang 2016); declination (Warrington 2018); ensemble outlier
methods from Duke (Herschlag et al. 2020) and the MGGG Redistricting
Lab (DeFord et al. 2021). All of these are *forensic* instruments: they
take an enacted map as input and ask whether its observed properties
(shape, vote efficiency, partisan asymmetry, the location of its
seat–vote curve) are consistent with maps that some reference process –
random redistricting, ensemble sampling under legal constraints – would
have produced absent partisan intent. They are differential, comparing
the enacted plan against a counterfactual distribution to infer the
line-drawer’s motive. They were built for an adversarial context in
which the question is “did somebody do something here that they should
not have done?”

A generative metric is a different object. It states, directly, what a
district *should* look like, and is used as the objective of the
line-drawing procedure rather than as evidence about the procedure.
Population balance is the only generative metric U.S. redistricting law
currently uses: *Wesberry v. Sanders* (**wesberry1964?**) and *Reynolds
v. Sims* (Supreme Court of the United States 1964) require that each
district hold roughly $`1/N`$ of the relevant population. Every other
criterion (compactness, communities of interest, partisan fairness)
enters the law as a forensic instrument or a discretionary guideline.

This matters for two reasons. First, forensic metrics depend on a
line-drawer to investigate. Removing the line-drawer – replacing it with
a deterministic generator – preserves the descriptive role of these
metrics (the shape is still non-compact; the seat–vote curve is still
asymmetric) but evacuates their inferential content. There is no intent
to infer (Pildes 2004). Second, when forensic metrics are used as design
objectives, the rule that emerges is often unstable: optimizing for
“looks like a fair plan would have looked” is a moving target that
depends on which ensemble distribution one chooses and which legal
constraints one chooses to encode. Chen and Rodden (Chen and Rodden
2013) showed that even fully content-neutral automated maps
systematically disadvantage Democrats in many states because of
residential clustering; a nonzero Efficiency Gap on such a map reflects
geography, not intent. The choice of constraint set is itself
political (Cain 2014).

The DualBalance Score we propose,
``` math
\begin{equation}
  \mathrm{DBS}
    = \frac{1}{1 + \tfrac{1}{2}\overline{\mathrm{pop\_dev}}
                 + \tfrac{1}{2}\overline{\mathrm{area\_dev}}},
\end{equation}
```
is a *generative* criterion: it states what a district should be
(carries roughly $`1/N`$ of the people and roughly $`1/N`$ of the land)
and is the objective the algorithm minimizes against, rather than a test
it must pass.

## Does the Iowa Model Generalize?

Iowa’s Legislative Services Agency (Iowa Legislative Services Agency
2021) operates under a written procedure that has been described to us
as a counterexample to the partisan-redistricting norm: aggregate whole
counties, prioritize county integrity lexicographically, balance
population by capacity, use distance-based assignment for compactness.
The procedure has been in continuous use since 1980. If it works in
Iowa, why not elsewhere?

The answer, which we document quantitatively in
§<a href="#sec:results" data-reference-type="ref"
data-reference="sec:results">3</a>, is that the algorithm’s behavior is
sensitive to the input geography. Iowa is unusually homogeneous: 99
counties, no county exceeding the per-district population cap, no
metropolitan area large enough to dominate state politics. We
re-implemented the procedure (we call it *Cascade* in this paper to
avoid confusion with the agency that designed it) and ran it on six
states. On Iowa, the resulting plan has a per-district population
deviation of $`0.29\%`$; on Wisconsin, $`0.50\%`$. On the remaining four
states the same algorithm produces deviations that are not legally
usable: $`10.27\%`$ on North Carolina, $`24.58\%`$ on Texas, $`41.56\%`$
on Massachusetts, $`76.14\%`$ on Minnesota. The county-integrity
priority that produces clean maps in Iowa – where no county is too large
– produces unconstitutional maps in any state with a county large enough
to swallow a district. The Iowa procedure is exemplary for the
geographic conditions in which it was designed; on these results, it is
not a transplantable template.

A deterministic procedure that hopes to scale to the full set of states
needs a different structural commitment. We propose one below.

## Contribution

We propose *DualBalance Districting*: a deterministic multi-resolution
pipeline whose output is a pure function of
$`(\text{state geometry}, \text{census populations}, N)`$, with no
random seed, no tuning weight, no iteration count, and no
human-in-the-loop adjustments.

#### Pipeline.

DualBalance Districting is a multi-stage deterministic pipeline. Each
stage is a pure function of its inputs; the composition is therefore
also a pure function of
$`(\text{state geometry}, \text{census populations}, N, \text{Karcher tolerance } \tau)`$.

Stage 1 – radial seed.  
DualBalance places $`N`$ seeds in a small circle around the
population-weighted centroid, assigns each census unit to the nearest
seed with capacity remaining, and repairs contiguity
(§<a href="#sec:methods-seeds" data-reference-type="ref"
data-reference="sec:methods-seeds">2.2</a>). The districts come out as
radial slices through the population center; each slice naturally spans
both dense and sparse territory, so the area each slice inherits trends
toward $`A^{*}`$ by geometry rather than by penalty.

Stage 2 – VTD-scale tightening.  
*Voting tabulation districts* (VTDs) are the precinct-scale geographic
units the Census Bureau publishes alongside the decennial PL 94-171
release; a U.S. state typically has a few thousand, each holding on the
order of $`10^3`$ people. A two-phase greedy local search of
boundary-unit moves between adjacent VTDs closes the gap from
several-percent radial pop deviation toward Karcher’s
$`\sim 0.05\%`$ (**karcher1983?**) threshold
(§<a href="#sec:methods-optimize" data-reference-type="ref"
data-reference="sec:methods-optimize">[sec:methods-optimize]</a>).
Phase 1 accepts any move that either reduces the L$`^1`$ pop-deviation
sum or strictly reduces the L$`^\infty`$ maximum (max-reducing
preferred). When 1-opt stalls in a multi-tied-max local optimum, a
length-2 then length-3 augmenting-chain escape – the deterministic
analogue of an ejection chain – searches for a transport sequence on the
district-adjacency graph that the 1-opt neighborhood cannot express.
Phase 2 then hill-climbs DBS subject to the running pop-deviation
envelope.

Stage 3 – block-scale refinement.  
*Census tabulation blocks* are the smallest geographic units the Census
Bureau publishes population for; each VTD is composed of whole blocks,
and block populations are ~50$`\times`$ smaller than VTD populations (a
typical block holds on the order of $`20`$ people). The VTD-level plan
is projected onto blocks via a deterministic spatial join (each block
inherits its containing VTD’s district), and Phases 1 and 2 are re-run
at block granularity
(§<a href="#sec:methods-block" data-reference-type="ref"
data-reference="sec:methods-block">2.7</a>). The finer granularity is
what lets the running-max envelope around $`\tau`$ admit area-improving
moves; this is where DBS makes its biggest gains.

A per-district articulation-point cache (Tarjan on CSR adjacency arrays,
JIT-compiled when numba is available) makes each contiguity check
$`\mathcal{O}(1)`$ rather than $`\mathcal{O}(|V_d| + |E_d|)`$, which is
what makes the block-scale stage tractable
(§<a href="#sec:methods-contig" data-reference-type="ref"
data-reference="sec:methods-contig">2.8</a>).

#### Empirical validation.

We run the full pipeline on six states selected to cover the geographic
range that breaks Cascade: IA, MA, MN, NC, TX, WI. Five of six achieve a
DualBalance Score above the enacted 119th-Congress plan. Two (IA, WI)
reach the $`0.05\%`$ Karcher threshold exactly; three more (MN, NC, MA)
sit within a factor of two of it; TX, the hardest case, sits at
$`0.52\%`$ – five times tighter than the same state’s enacted plan. On
partisan fairness, DualBalance’s Efficiency Gap is smaller in magnitude
than the enacted plan’s in four of six states, with the largest
improvements on the three most heavily-litigated maps (NC, WI, TX). On
minority-majority district counts, DualBalance produces more such
districts than the enacted plan on NC (2 vs. 1) and TX (22 vs. 19).

#### What we claim and what we do not.

We claim that DualBalance produces a deterministic alternative whose
structural neutrality is symmetric: it cannot be tuned to advantage any
party, incumbent, racial group, or community of interest, and equally
cannot be tuned to help any of them. We do not claim it is the only
defensible deterministic procedure, or that its specific 0.5/0.5
weighting of population against area is uniquely correct. We do claim
that the choice to use a *generative* criterion as the design objective,
rather than a forensic instrument, is the structurally correct response
to a regime in which line-drawer intent has become both legally
unreviewable (post-*Rucho*) and practically unverifiable (forensic
metrics presuppose the very thing the algorithm removes).

#### Roadmap.

Section <a href="#sec:methods" data-reference-type="ref"
data-reference="sec:methods">2</a> formalizes the algorithm.
Section <a href="#sec:results" data-reference-type="ref"
data-reference="sec:results">3</a> reports the six-state empirical
validation. Section <a href="#sec:discussion" data-reference-type="ref"
data-reference="sec:discussion">4</a> discusses limits, trade-offs, and
legal exposure.

# Methods

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
data-reference="sec:methods-seeds">2.2</a>–<a href="#sec:methods-repair" data-reference-type="ref"
data-reference="sec:methods-repair">2.4</a>), which provides the
deterministic starting configuration; a VTD-scale tightening stage
(§<a href="#sec:methods-optimize" data-reference-type="ref"
data-reference="sec:methods-optimize">[sec:methods-optimize]</a>) which
drives $`\max_i |\delta_i|/P^{*}`$ toward the user-supplied tolerance
$`\tau`$ via a hybrid greedy local search with bounded-chain escape; and
a block-scale refinement stage
(§<a href="#sec:methods-block" data-reference-type="ref"
data-reference="sec:methods-block">2.7</a>) which re-initializes at
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
data-reference="sec:methods-assign">2.3</a>) while the area it inherits
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
data-reference="sec:methods-assign">2.3</a> every unit belongs to
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
computed alongside but not optimized against; radial slices have lower
compactness than blob-Voronoi or hand-drawn districts by construction,
and this is a deliberate trade in service of the dual-balance objective.

DualBalance does not directly
minimize <a href="#eq:dbs" data-reference-type="eqref"
data-reference="eq:dbs">[eq:dbs]</a>; it minimizes
population-capacitated geographic assignment cost under radial seeding.
On the Minnesota PoC this still beats the enacted plan on DBS
($`0.6472`$ vs $`0.6390`$) despite the lower compactness.

## Optional: L<sup>1</sup> pop-tightening with DBS hill-climb

<span id="sec:methods-optimize" label="sec:methods-optimize"></span>

The radial pipeline produces per-district pop deviation in the 5–15%
range on real census geometry, well above the ~0.5% threshold required
by *Reynolds v. Sims* for U.S. congressional districts (Supreme Court of
the United States 1964). An optional post-pass (`--tighten-pop`) closes
this gap via a deterministic two-phase local search of boundary-unit
moves. Let $`\delta_i = P(D_i) - P^{*}`$ denote the signed population
deviation of district $`D_i`$, let $`T`$ denote the user-supplied
tolerance (default $`0.005`$), and call a move *safe* if the source unit
is not an articulation point of its district’s induced subgraph (so that
removing it preserves contiguity).

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
sum. The canonical Reynolds-tightening literature uses L$`^\infty`$ and
bottoms out at ~5% on this geometry; the hybrid pass with chain escape
runs to completion in ~80 swaps on Minnesota, reducing
$`\mathrm{pop\_dev\_max}`$ from $`0.1124`$ to $`0.0021`$ while leaving
$`\mathrm{area\_dev\_mean}`$ essentially unchanged.

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
much tighter *Karcher v. Daggett* (**karcher1983?**) practical threshold
of $`\sim 0.05\%`$ total deviation, and at VTD granularity the residual
gap is structural rather than algorithmic. The smallest single-unit move
has the size of the smallest VTD’s population. On real states the median
VTD population is on the order of $`10^3`$, while the Karcher budget on
a $`\sim 800`$k ideal district is $`\sim 400`$ people. Most candidate
moves overshoot the budget on at least one endpoint, and Phase 2
starves: the running-max constraint admits few moves, and the algorithm
settles above Karcher with most of the residual area-balance gain
unrealized.

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
blocks for the precise area-balance recovery.

## Engineering: per-district articulation-point cache

The hot loop of the optimizer asks repeatedly whether a candidate
boundary unit $`u`$ can be safely removed from its district $`d`$ – in
other words, whether $`u`$ is an articulation point of the subgraph
$`G[V_d]`$. A naive implementation runs $`\mathcal{O}(|V_d| + |E_d|)`$
per query via `networkx.is_connected` on the post-removal subgraph,
which dominates runtime at block scale.

We maintain a per-district cache. For each district $`d`$, the set
$`A_d \subseteq V_d`$ of articulation points is precomputed by Tarjan’s
algorithm (Tarjan 1972) on CSR (compressed sparse row) integer adjacency
arrays. The per-query `can_remove(u)` reduces to the set membership
$`u \notin A_{\pi(u)}`$, returned in $`\mathcal{O}(1)`$ amortized. After
each accepted move $`u: d_{\mathrm{src}} \to d_{\mathrm{dest}}`$ the two
affected articulation sets $`A_{d_{\mathrm{src}}}`$,
$`A_{d_{\mathrm{dest}}}`$ are recomputed; districts not touched by the
move keep their cached set unchanged.

Each Tarjan recompute is $`\mathcal{O}(|V_d| + |E_d|)`$ rather than the
global $`\mathcal{O}(|V| + |E|)`$ of the naive check
($`|V_d| \approx |V|/N`$ for $`N`$ districts). The recompute itself is
`@njit`-compiled via numba when available, operating on preallocated
workspace buffers (a single integer DFS stack, two boolean masks, and
three integer arrays sized to $`|V|`$). On a typical block-scale
district subgraph of $`\sim 44{,}000`$ nodes the JIT’d recompute
completes in $`\sim 20`$ ms, compared to $`\sim 560`$ ms for the same
query through `networkx.articulation_points`: a $`28\times`$ speedup.
Across a full block-scale optimizer run (thousands of accepted moves and
tens of thousands of candidates per move), this is the difference
between a 20-hour run and a 30-minute run.

A boundary-unit set
$`\partial = \{u : \exists v \in N(u), \pi(v) \neq \pi(u)\}`$ is also
maintained incrementally and updated after each move (only $`u`$ and its
graph neighbors need to be re-checked). The inner scan iterates
$`\partial`$ rather than $`V`$, dropping per-pass work from $`|V|`$ to
$`O(|\partial|)`$, which on real states is roughly the square root of
$`|V|`$.

Neither caching layer changes the algorithm’s output. They preserve
determinism exactly and make the block-scale pipeline tractable on
commodity hardware.

## Determinism and tie-breaking

The pipeline is deterministic at every step. The only sources of
ambiguity (equidistant seed-to-unit pairs in
§<a href="#sec:methods-assign" data-reference-type="ref"
data-reference="sec:methods-assign">2.3</a>, equal-capacity fallbacks
for unplaced units, and equal-cost candidates in
§<a href="#sec:methods-repair" data-reference-type="ref"
data-reference="sec:methods-repair">2.4</a>) all resolve to a fixed
cascade with no remaining ambiguity:

1.  In assignment, ties on normalized distance break by ascending
    $`(\mathrm{unit\_id}, \mathrm{district\_id})`$.

2.  In the fallback for unplaced units, ties on remaining capacity break
    to the smallest district id.

3.  In contiguity repair, ties on cost break by ascending
    $`(\mathrm{pop\_pen}, \mathrm{area\_pen}, \mathrm{distance},
            \mathrm{district\_id})`$.

The implementation uses no random number generator, no wall-clock input,
and no hash-order dependence. Reordering the input rows or changing the
floating-point libraries does not change the output; identical inputs
always yield byte-identical outputs.

## Out-of-scope inputs

The generator reads only geography and population. Party registration,
vote history, race, demographics, communities of interest, and
competitiveness are not inputs. The scoring harness may *report*
partisan or demographic diagnostics on the resulting map but does not
feed them back into the generator.

# Results

## Test bed: Minnesota, 2020 PL 94-171

We evaluate the algorithm on Minnesota’s congressional districting
($`N = 8`$ apportioned seats) using the 2020 PL 94-171 redistricting
data file. The input is the TIGER/Line 2020 VTD (voting tabulation
district) shapefile for Minnesota (4,110 atomic units, total population
$`P = 5{,}706{,}494`$, total land area $`A = 225{,}187`$ km$`^2`$),
joined to the Census Data API’s `P1_001N` total-population field,
projected to EPSG:5070 (CONUS Albers, equal area) at load time.
Per-district targets are $`P^{*} = P/8 = 713{,}312`$ and
$`A^{*} = A/8 = 28{,}148`$ km$`^2`$. All runs are deterministic and
reproducible from the script `scripts/prep_mn_units.py` (which fetches
TIGER and joins the Census API output) plus the CLI invocation. The data
pipeline is documented end-to-end in `docs/mn-poc-walkthrough.md`.

We compare three plans on the same 4,110-VTD input:

- **DualBalance.** The default algorithm
  (§<a href="#sec:methods-seeds" data-reference-type="ref"
  data-reference="sec:methods-seeds">2.2</a>–§<a href="#sec:methods-repair" data-reference-type="ref"
  data-reference="sec:methods-repair">2.4</a>). No tuning knobs.

- **DualBalance + tighten-pop ($`\tau = 0.005`$).** DualBalance followed
  by the optional $`L^{1}`$ pop-tightening pass
  (§<a href="#sec:methods-tighten" data-reference-type="ref"
  data-reference="sec:methods-tighten">2.6</a>) targeting per-district
  deviation within 0.5 % of $`P^{*}`$.

- **Enacted (119th).** The court-drawn, legislatively enacted Minnesota
  U.S. House districts currently in force, scored with the same harness.

## Headline scores

Table <a href="#tab:mn-results" data-reference-type="ref"
data-reference="tab:mn-results">1</a> reports the DualBalance Score and
supporting metrics for the three plans.

<div id="tab:mn-results">

| Metric | DualBalance | DualBalance + tighten-pop | Enacted (119th) |
|:---|---:|---:|---:|
| $`\mathrm{DBS}`$ | 0.6472 | **0.6574** | 0.6390 |
| $`\overline{\mathrm{pop\_dev}}`$ | 5.08 % | **0.08 %** | 0.42 % |
| $`\mathrm{pop\_dev}_{\max}`$ | 11.24 % | **0.21 %** | 1.32 % |
| $`\overline{\mathrm{area\_dev}}`$ | **103.9 %** | 104.2 % | 112.6 % |
| $`\mathrm{area\_dev}_{\max}`$ | 271.0 % | 275.1 % | **241.0 %** |
| $`\mathrm{PP}_{\mathrm{mean}}`$ | 0.200 | 0.162 | **0.320** |
| $`\mathrm{PP}_{\min}`$ | 0.094 | 0.047 | **0.178** |
| $`\mathrm{Reock}_{\mathrm{mean}}`$ | 0.361 | 0.342 | **0.419** |

DualBalance metrics on the Minnesota PoC (4,110 VTDs, 8 districts, 2020
PL 94-171 population). $`\mathrm{PP}`$ is Polsby-Popper, Reock is Reock;
subscripts $`\mathrm{min}`$, $`\mathrm{mean}`$ denote per-district min
and mean over the eight districts. $`\mathrm{pop\_dev}`$,
$`\mathrm{area\_dev}`$ are the relative deviations defined in
§<a href="#sec:methods" data-reference-type="ref"
data-reference="sec:methods">2</a>. Best result per row in bold.

</div>

Three findings.

#### DualBalance beats the enacted plan on the DualBalance Score.

DualBalance scores 0.6472 against the enacted 0.6390, a $`+1.3`$ %
margin with no iteration, no tuning, no post-processing. The advantage
comes entirely from area balance ($`\overline{\mathrm{area\_dev}}`$
103.9 % vs 112.6 %). Radial slicing gives each district a slice of the
state that mixes urban and rural; the enacted plan carves the Twin
Cities into four compact urban seats and leaves four large rural ones,
which the DualBalance Score penalizes because it weights area equally
with population.

#### Tightening closes the legal gap and improves DBS.

Pure DualBalance’s $`\mathrm{pop\_dev}_{\max}`$ of 11.24 % exceeds the
~0.5 % *Reynolds v. Sims* threshold for U.S. House plans (Supreme Court
of the United States 1964). The optional pass
(§<a href="#sec:methods-tighten" data-reference-type="ref"
data-reference="sec:methods-tighten">2.6</a>) ran 81 boundary swaps in
~18 s and drove $`\mathrm{pop\_dev}_{\max}`$ to 0.21 %, tighter than the
enacted plan’s 1.32 %. $`\overline{\mathrm{area\_dev}}`$ rose only 0.3
points and the score *improved* to 0.6574.

#### Compactness is the price.

The enacted plan beats DualBalance on every compactness measure:
$`\mathrm{PP}_{\min}`$ 0.178 vs 0.094 (pure DualBalance) and 0.047
(after tightening), $`\mathrm{PP}_{\mathrm{mean}}`$ 0.320 vs 0.200 /
0.162, $`\mathrm{Reock}_{\mathrm{mean}}`$ 0.419 vs 0.361 / 0.342. Radial
slices are structurally less compact than hand-drawn blobs. Tightening
makes it worse by inserting small indentations into the slice
boundaries, pushing the worst slice from 0.094 (at the informal 0.10
threshold) to 0.047. Whether the trade is acceptable is a normative
question taken up in
§<a href="#sec:discussion-compactness" data-reference-type="ref"
data-reference="sec:discussion-compactness">4.3</a>.

## Map comparison

Figure <a href="#fig:mn-comparison" data-reference-type="ref"
data-reference="fig:mn-comparison">1</a> displays the three plans side
by side.

<figure id="fig:mn-comparison" data-latex-placement="h">
<img src="mn_radial_with_tighten.png" />
<figcaption>Minnesota congressional districts under three plans.
<strong>Left:</strong> the enacted 119th-Congress plan, with four
compact Twin Cities seats and four large rural seats.
<strong>Center:</strong> DualBalance (score <span
class="math inline">0.6472</span>); eight slices radiate from the
population-weighted centroid near Minneapolis-St. Paul, each spanning
dense and sparse territory. <strong>Right:</strong> DualBalance <span
class="math inline">+</span> <code>--tighten-pop 0.005</code> (score
<span class="math inline">0.6574</span>); the radial structure is
preserved (units move only at slice boundaries) and per-district
population is Reynolds-compliant.</figcaption>
</figure>

## Determinism check

We re-ran `dualbalance generate --config configs/mn_vtd.yaml` ten times
in succession, comparing each run’s `map.geojson` and `metrics.json` by
byte hash. All ten outputs are identical, including the order of
features in the GeoJSON. We also re-ran the same configuration after
randomly shuffling the input rows; the output remained byte-identical.
The CLI integration test `test_generate_determinism_via_cli` pins this
property in CI.

## Per-district breakdown

Table <a href="#tab:mn-perdistrict" data-reference-type="ref"
data-reference="tab:mn-perdistrict">2</a> reports the per-district
metrics for DualBalance $`+`$ tighten-pop, indexed by seed angle
(district 0 sits due east of the population-weighted centroid;
subsequent districts advance counter-clockwise in steps of $`2\pi/8`$
rad). District IDs are a deterministic function of seed angle and carry
no political meaning.

<div id="tab:mn-perdistrict">

| District | Population | Area | $`\mathrm{pop\_dev}`$ | $`\mathrm{area\_dev}`$ | $`\mathrm{PP}`$ | $`\mathrm{Reock}`$ |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 712,841 | 1,010 | 0.07 % | 96.4 % | 0.228 | 0.454 |
| 1 | 714,816 | 9,620 | 0.21 % | 65.8 % | 0.047 | 0.147 |
| 2 | 712,145 | 105,594 | 0.16 % | 275.1 % | 0.152 | 0.369 |
| 3 | 713,263 | 50,054 | 0.01 % | 77.8 % | 0.146 | 0.268 |
| 4 | 714,168 | 46,060 | 0.12 % | 63.6 % | 0.150 | 0.267 |
| 5 | 713,368 | 10,882 | 0.01 % | 61.3 % | 0.137 | 0.422 |
| 6 | 713,013 | 1,481 | 0.04 % | 94.7 % | 0.117 | 0.301 |
| 7 | 712,880 | 477 | 0.06 % | 98.3 % | 0.318 | 0.510 |

Per-district breakdown, DualBalance $`+`$ tighten-pop 0.5 %. Areas are
in km$`^2`$.

</div>

District 2 inherits the northern panhandle
($`\sim`$<!-- -->3.8$`\times A^{*}`$); District 7 is the Twin Cities
urban core ($`\sim`$<!-- -->0.02$`\times A^{*}`$). All eight districts
are within 0.21 % of $`P^{*}`$. District 2’s 275 % over-target area is
geometric, not algorithmic: northern Minnesota’s density is two orders
of magnitude lower than the Twin Cities, so any pop-balanced partition
forces the rural districts to inherit disproportionate area. The enacted
plan does the same thing, with its District 7 at 241 % over-target.

## Descriptive diagnostics: partisan, race, county

DualBalance reads none of these inputs. We report them anyway, because
readers will ask. They are descriptions of the partition, not
evaluations of it
(§<a href="#sec:discussion-forensic" data-reference-type="ref"
data-reference="sec:discussion-forensic">4.7</a>). Partisan totals come
from 2020 presidential returns
([dra2020/vtd_data](https://github.com/dra2020/vtd_data), keyed on
GEOID20). Race comes from Census PL 94-171 VAP.

#### Partisan.

Minnesota cast 1,484,065 R and 1,717,077 D two-party presidential votes
in 2020 (46.4 % R, 53.6 % D). DualBalance splits the eight seats 4–4
against a seats-proportional expectation of 3.7 R seats. The two
D-leaning slices contain the Twin Cities and run 64–75 % D; two
R-leaning slices reach into western and southern Minnesota and run
55–65 % R; the other four are within $`\pm 5`$ points of even. The
efficiency gap is $`+6.6\,\%`$ (positive = R-favorable); the mean-median
R difference is $`+3.9`$ points (positive = D-favorable). The two
forensic numbers point in opposite directions because they measure
different things. Both are artifacts of where Minnesota’s Democrats live
(packed into the metro), not of any choice by DualBalance.

#### Race / VAP.

Statewide VAP is 80.0 % non-Hispanic white, 5.9 % Black, 5.0 % Hispanic,
4.9 % Asian, 1.1 % AIAN. DualBalance draws zero majority-minority
districts. The Twin Cities slice (District 7) has the lowest
non-Hispanic-white share (65.3 %) and the highest Black VAP share
(15.7 %); the remaining seven run 73–90 % non-Hispanic white. The
enacted 119<sup>th</sup> Congress plan also draws zero majority-minority
districts. Minnesota does not contain a region where a single minority
group concentrates densely enough to support a 50 %-VAP district of
conventional size.

#### County splits.

DualBalance splits 44 of 87 counties into 143 cross-district pieces. Any
line from the population centroid to the boundary crosses county lines;
the enacted plan trades area balance for fewer such crossings.

#### What to make of this.

The descriptive content of these metrics survives on a DualBalance plan;
their intent-attribution role does not.
§<a href="#sec:discussion-forensic" data-reference-type="ref"
data-reference="sec:discussion-forensic">4.7</a> develops the
distinction.

## Cross-state, multi-algorithm validation

We replicated the Minnesota pipeline on five additional states spanning
the density-profile and gerrymandering-history spaces: Iowa (4
districts, near-uniform density, drawn by Iowa’s nonpartisan Legislative
Services Agency (Iowa Legislative Services Agency 2021)), Massachusetts
(9 districts, single-metro Boston), Texas (38 districts, polycentric),
North Carolina (14 districts, the state in which *Rucho* (Supreme Court
of the United States 2019) originated), and Wisconsin (8 districts,
where *Whitford v. Gill* first put the Efficiency Gap (Stephanopoulos
and McGhee 2015) in front of a federal court). The data pipeline (TIGER
2020 VTDs, Census PL 94-171 demographics, dra2020/vtd_data 2020
presidential returns, TIGER 2024 cd119 spatial join for the enacted
plan) is automated in `scripts/prep_state_units.py`.

To put DualBalance in context against other deterministic baselines we
score two additional algorithms on the same six states. *Cascade*
(`src/dualbalance/cascade.py`) is an Iowa-LSA-flavored construction:
aggregate VTDs to counties, pick $`N`$ farthest-spread county seeds, run
capacitated first-fit county-to-district assignment, and split a county
into pseudo-counties (via DualBalance internally) only when its
population exceeds the per-district cap. *BDistricting* (Olson
2007--2024) is Brian Olson’s published 50-state map series, ingested via
Olson’s block-level CSV output joined to our VTDs through the Census
2020 Block Assignment File (`scripts/prep_bdistricting.py`). Cascade
prioritizes county integrity; BDistricting prioritizes compactness;
DualBalance prioritizes area balance. Together with the enacted plan
this gives four points of comparison on each state.

<div id="tab:multistate-dbs">

| State          |   N | DualBalance |    Cascade | BDistricting |    Enacted |
|:---------------|----:|------------:|-----------:|-------------:|-----------:|
| Iowa           |   4 |      0.8132 |     0.8227 |       0.7885 | **0.8828** |
| Massachusetts  |   9 |      0.7591 | **0.7602** |       0.7158 |     0.7246 |
| Minnesota      |   8 |      0.6472 | **0.7709** |       0.6493 |     0.6391 |
| North Carolina |  14 |      0.7252 | **0.8199** |       0.7600 |     0.7689 |
| Texas          |  38 |      0.6230 | **0.7943** |       0.6350 |     0.6658 |
| Wisconsin      |   8 |      0.6556 | **0.8399** |       0.7422 |     0.7410 |

Cross-state DualBalance Score. **Bold** marks the winner on each row.

</div>

<div id="tab:multistate-eg">

| State | Statewide R % | DualBalance | Cascade | BDistricting | Enacted |
|:---|---:|---:|---:|---:|---:|
| Iowa | 54.2 | $`-0.173`$ | $`+0.165`$ | **$`-0.088`$** | $`+0.416`$ |
| Massachusetts | 32.9 | $`-0.158`$ | $`-0.158`$ | $`-0.158`$ | $`-0.158`$ |
| Minnesota | 46.4 | $`+0.066`$ | **$`+0.049`$** | $`+0.067`$ | $`+0.068`$ |
| North Carolina | 50.7 | $`+0.088`$ | **$`+0.026`$** | $`-0.077`$ | $`+0.201`$ |
| Texas | 52.8 | $`+0.029`$ | **$`+0.009`$** | $`+0.058`$ | $`+0.153`$ |
| Wisconsin | 49.7 | $`+0.147`$ | **$`+0.081`$** | $`+0.142`$ | $`+0.267`$ |

Cross-state Efficiency Gap (positive = R-favorable). **Bold** marks the
smallest $`|\mathrm{EG}|`$ on each row.

</div>

<div id="tab:multistate-counties">

| State | Counties | DualBalance (split) | Cascade (split) | BDistricting (split) | Enacted (split) |
|:---|---:|---:|---:|---:|---:|
| Iowa | 99 | 30 | **0** | 21 | **0** |
| Massachusetts | 14 | 12 | **4** | 10 | 9 |
| Minnesota | 87 | 44 | **1** | 25 | 9 |
| North Carolina | 100 | 56 | **2** | 37 | 11 |
| Texas | 254 | 132 | **10** | 82 | 30 |
| Wisconsin | 72 | 46 | **1** | 25 | 12 |

Counties kept intact. Cascade splits a county only when its population
exceeds the per-district cap.

</div>

Three findings stand out.

#### Cascade dominates on DBS.

Cascade wins on five of six states (MN, MA, TX, NC, WI) and runs second
on Iowa. DualBalance wins on no state outright; BDistricting on none.
Cascade’s lead comes from the structural pairing of high county
integrity (1–10 splits vs. the enacted plan’s 9–30) with low area
imbalance (county aggregation produces pseudo-counties of similar size
across each state). The exception is Iowa, where the enacted plan is
itself the result of a closely related cascade process (Iowa Legislative
Services Agency 2021) and the LSA’s manual refinement gives it a small
edge.

#### Different deterministic algorithms, different trade-offs.

The three deterministic generators win on different axes. DualBalance
minimizes $`\overline{\mathrm{area\_dev}}`$ on single-metro states with
a clean radial structure but produces high county splits and low
compactness. BDistricting maximizes compactness and pop-balance but
accepts high area imbalance ($`\overline{\mathrm{area\_dev}}`$ near
$`0.8`$ on MA, $`1.1`$ on TX). Cascade maximizes county integrity and
area balance but tolerates looser population balance (10–20 %
pre-tighten). The “best” algorithm on DBS is whichever happens to weight
the underlying trade-offs in a way the state’s geometry rewards.

#### Partisan asymmetry shrinks across every deterministic generator.

On every state with nonzero statewide partisan asymmetry, all three
deterministic algorithms produce smaller $`|\mathrm{EG}|`$ than the
enacted plan. The largest gaps appear in the two states most associated
with partisan-gerrymander litigation: NC (enacted $`+0.20`$ vs. Cascade
$`+0.03`$) and WI (enacted $`+0.27`$ vs. Cascade $`+0.08`$). Cascade has
the smallest $`|\mathrm{EG}|`$ on five of six states; BDistricting on
one (Iowa). The structural claim in
§<a href="#sec:discussion-forensic" data-reference-type="ref"
data-reference="sec:discussion-forensic">4.7</a> is the empirical core
of this finding: a generator with no political input cannot produce a
$`+0.20`$ partisan-fairness metric. The result holds across all three
deterministic baselines, not just DualBalance. Cascade is the existence
proof of that claim under a different objective hierarchy than
DualBalance’s.

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

DualBalance differs from each prior method on a specific axis.

#### Versus Smith’s Shortest Splitline (Smith 2007).

Splitline recursively bisects the state with the shortest
population-balancing line, with no global compactness or balance
criterion. The cuts are visually striking but arbitrary: a district can
lose half its territory because the shortest cut happens to land there.
DualBalance grounds its geometry in the population centroid, so the
slices reflect the state’s density structure.

#### Versus Olson’s BDistricting (Olson 2007--2024).

BDistricting minimizes population-weighted distance to dispersed seed
centers under equal-population, with Lloyd-style iteration to
convergence. The resulting maps are blob-shaped and score well on
compactness but exhibit large area imbalance. DualBalance differs in two
ways: seeds are radial-clustered around the centroid (not dispersed),
and there is no iteration. On the six-state comparison
(§<a href="#sec:results-multistate" data-reference-type="ref"
data-reference="sec:results-multistate">3.7</a>) BDistricting wins on no
state outright on DBS, but produces the smallest $`|\mathrm{EG}|`$ on
Iowa and the most-compact districts in every state.

#### Versus centroidal power diagrams (Cohen-Addad et al. 2018).

The Cohen-Addad-Klein-Young construction solves for additive weights
$`\{w_i\}`$ so each power-diagram cell carries exactly $`1/N`$ of the
mass. It balances one quantity (population) exactly. DualBalance
balances two (population and area) approximately, with the second
recovered from the radial seed geometry rather than from the
optimization.

#### Versus capacitated $`k`$-means (Levin and Friedler 2019) and Hess-style location-allocation (Hess et al. 1965; Mehrotra et al. 1998).

The capacitated assignment step
(§<a href="#sec:methods-assign" data-reference-type="ref"
data-reference="sec:methods-assign">2.3</a>) is Hess’s 1965
transportation step. DualBalance’s novelty is the seed placement: radial
seeds produce a slice geometry that Lloyd iteration would destroy,
because recentering pulls seeds away from the tight radial cluster.
Disabling iteration is what preserves the geometry.

#### Versus our own Cascade baseline.

Cascade (§<a href="#sec:results-multistate" data-reference-type="ref"
data-reference="sec:results-multistate">3.7</a>,
`src/dualbalance/cascade.py`) is an Iowa-LSA-flavored construction we
include in the empirical comparison: it aggregates VTDs to counties,
picks $`N`$ farthest-spread county seeds, runs capacitated first-fit
assignment at county granularity, and splits a county into
pseudo-counties (via DualBalance internally) only when its population
exceeds the per-district cap. Cascade beats DualBalance on DBS on all
six states tested, sometimes by wide margins (MN $`+0.12`$, TX
$`+0.17`$, NC $`+0.09`$, WI $`+0.18`$); on the six-state set Cascade is
the stronger *deterministic baseline* against the enacted plan. We
include both algorithms because they make the conceptual contribution
sharper: DualBalance and Cascade prioritize different objectives (radial
slicing for density mixing; county integrity for administrative
coherence) and produce different maps on every state, yet both are
race-blind, partisan-blind, and deterministic by construction. The
forensic critique in
§<a href="#sec:discussion-forensic" data-reference-type="ref"
data-reference="sec:discussion-forensic">4.7</a> applies equally to
either, and to BDistricting, and to any future deterministic generator
built on similar principles.

## Limitations

#### Six-state evidence, not fifty-state generality.

Three deterministic algorithms (DualBalance, Cascade, BDistricting) have
been run end-to-end on six states
(§<a href="#sec:results-multistate" data-reference-type="ref"
data-reference="sec:results-multistate">3.7</a>). On DBS, Cascade wins
on MN, MA, TX, NC, and WI; the enacted plan wins only on Iowa. Across
all six states with nonzero partisan asymmetry, every deterministic
algorithm produces a smaller $`|\mathrm{EG}|`$ than the enacted plan,
with the largest gaps in the gerrymander-prone states. The remaining 44
states have not been run, and six states does not establish generality
across the density-profile or litigation-history spaces.

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

#### Full-50-state validation.

Six states (MN, IA, MA, TX, NC, WI) have been run
(§<a href="#sec:results-multistate" data-reference-type="ref"
data-reference="sec:results-multistate">3.7</a>). Extending to the
remaining 44 requires no algorithmic change. California, Florida,
Pennsylvania, and Ohio are the highest-value next targets: California
for its size and many metros, Florida for its peninsula geometry,
Pennsylvania and Ohio for their roles in state-court
partisan-gerrymandering jurisprudence.

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
data-reference="sec:results-multistate">3.7</a>) covers DualBalance,
Cascade, BDistricting, and the enacted plan. Adding Smith’s Shortest
Splitline (Smith 2007) would give a fourth deterministic baseline;
computing it from scratch on each state is straightforward but has not
yet been done.

#### Scoring-harness extensions.

The current harness reports population, area, Polsby-Popper, and Reock.
Natural additions include partisan diagnostics (efficiency gap,
mean-median, declination) on voter-registration data, county-split
counts, and minority representation diagnostics under Section 2. These
are reporting extensions and would not feed back into the generator
(§<a href="#sec:methods" data-reference-type="ref"
data-reference="sec:methods">2</a>, “out-of-scope inputs”).

## Forensic metrics applied to a generative procedure

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

<div id="ref-hess1965" class="csl-entry">

Hess, S. W., J. B. Weaver, H. J. Siegfeldt, J. N. Whelan, and P. A.
Zitlau. 1965. “Nonpartisan Political Redistricting by Computer.”
*Operations Research* 13 (6): 998–1006.

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

<div id="ref-mjn1998" class="csl-entry">

Mehrotra, Anuj, Ellis L. Johnson, and George L. Nemhauser. 1998. “An
Optimization Based Heuristic for Political Districting.” *Management
Science* 44 (8): 1100–1114.

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

Supreme Court of the United States. 1964. *Reynolds v. Sims*. 377 U.S.
533.

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

<div id="ref-wang2016" class="csl-entry">

Wang, Samuel S.-H. 2016. “Three Tests for Practical Evaluation of
Partisan Gerrymandering.” *Stanford Law Review* 68: 1263–321.

</div>

<div id="ref-warrington2018" class="csl-entry">

Warrington, Gregory S. 2018. “Quantifying Gerrymandering Using the Vote
Distribution.” *Election Law Journal* 17 (1): 39–57.

</div>

</div>
