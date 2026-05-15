# DualBalance Districting: A Deterministic Alternative to Gerrymandering

**Steven Hart** · `hart.steven@mayo.edu`

> This file is the GitHub-rendered version of the LaTeX manuscript in
> [`main.tex`](main.tex) and [`sections/`](sections). The two are kept in
> sync by hand; if they diverge, the LaTeX is the source of record. For
> the algorithm itself see [the repository root](../) and
> [`docs/Formalism.md`](../docs/Formalism.md).

---

## Abstract

Congressional district lines in the United States are drawn by people,
and a great deal of recent legal and mathematical work tries to detect
when those people have crossed from neutral line-drawing into partisan
or racial manipulation. We propose a different approach: take the
people out of the line-drawing step entirely. **DualBalance Districting**
is a deterministic procedure that, given a state's boundary, its census
units, and its apportioned seat count $N$, produces a map in which each
district holds about $1/N$ of the state's people and about $1/N$ of its
land. The design is rooted in the constitutional framers' bicameral
compromise, in which the House represents people and the Senate
represents place. Here that compromise is applied for the first time,
to our knowledge, as a single criterion *within* one chamber. The
algorithm places $N$ seeds in a small circle around the
population-weighted centroid and assigns each census unit to the
nearest seed with population capacity remaining. There is no random
number generator, no iteration, no tunable weight, and no input beyond
geometry and population.

The same property that prevents the rule from being used to gerrymander
a state prevents it from being used to draw majority-minority districts,
protect incumbents, or preserve communities of interest. The
elimination of human discretion is symmetric: both the negative
direction (partisan manipulation, racial vote dilution) and the
positive direction (race-conscious remedies, competitiveness tuning)
are foreclosed by construction, because the algorithm has no input
through which either could be expressed.

This procedural neutrality cuts against the way the redistricting
literature has measured fairness for the past thirty years. Compactness
scores, the efficiency gap, mean-median asymmetry, ensemble outlier
tests, and majority-minority counts are all *forensic* instruments.
They were built to infer a human line-drawer's intent from the shape
and political character of the resulting map. On a plan produced by an
algorithm that has no intent, those inferences are no longer available.
An efficiency gap of $+6.6\%$ on a DualBalance map says only that
Democrats happen to live closer to the population center than
Republicans on this particular geometry. A Polsby-Popper score of
$0.09$ says only that the radial slice has that shape. A count of zero
majority-minority districts says only that the state's minority
population is geographically dispersed. The numbers still compute. What
they let you conclude about the line-drawer's motives is gone, because
there is no line-drawer.

On a single-state proof of concept (Minnesota, 4,110 VTDs, 8 seats,
2020 PL 94-171), DualBalance produces a plan that beats the enacted
119th-Congress map on its own dual objective ($\mathrm{DBS} = 0.6472$
vs. $0.6390$). We report 2020 presidential two-party shares and Census
PL 94-171 voting-age population by race alongside, as descriptions of
the resulting partition rather than as evaluations of it.

---

## 1. Introduction

### 1.1 The instability of human-drawn districts

Legislative redistricting in the United States is structurally unstable.
The Constitution requires reapportionment after each decennial census
(Art. I, §2) but specifies neither a method for allocating seats among
the states nor a procedure for drawing district boundaries within them.
Both decisions have been delegated, by default, to political actors.
The result, predictable from the design, is that maps are routinely
drawn to favor whichever group controls the pen at the moment of
redistricting. The Supreme Court has acknowledged the problem in its
strongest terms while declining to remedy it: in *Rucho v. Common
Cause* [[1]](#ref-1), Chief Justice Roberts wrote for a 5–4 majority
that partisan gerrymandering claims present nonjusticiable political
questions, conceding that the practice is "incompatible with democratic
principles" but holding that no manageable judicial standard exists.
Justice Kagan's dissent, joined by Ginsburg, Breyer, and Sotomayor,
argued the opposite: that lower courts had already converged on
workable tests, and that "of all times to abandon the Court's duty to
declare the law, this was not the one" [[1]](#ref-1).

Race-conscious districting operates under a separate and increasingly
constrained regime. Section 2 of the Voting Rights Act, as construed in
*Thornburg v. Gingles* [[2]](#ref-2), requires majority-minority districts
where the three Gingles preconditions are met; the Fourteenth Amendment,
as construed in *Shaw v. Reno* [[3]](#ref-3) and its progeny, subjects
to strict scrutiny any map in which race "predominates" in the
line-drawing. The two doctrines pull in opposite directions. The
Supreme Court reaffirmed Section 2 in *Allen v. Milligan* [[4]](#ref-4),
requiring Alabama to draw a second majority-Black district. One year
later, in *Alexander v. South Carolina Conf. of the NAACP*
[[5]](#ref-5), the Court reversed a district court's racial-gerrymander
finding and raised the plaintiff's evidentiary burden, holding that
challengers must "disentangle race from politics" and produce
illustrative alternative maps that satisfy all of the state's legitimate
goals. In April 2026, in *Louisiana v. Callais* [[6]](#ref-6), the
Court further held that even a map drawn to comply with a prior
Section 2 order may itself violate the Equal Protection Clause if the
VRA did not in fact compel the race-based remedy. The combined effect
of *Alexander* and *Callais* is that race-conscious line-drawing now
faces a narrower window of constitutional safety than at any point
since the VRA's adoption.

Two structural consequences follow. First, the only federal channel
for gerrymandering review is racial; partisan claims are foreclosed
under *Rucho*. Second, because Black voters in the United States vote
roughly nine-to-one Democratic, race and partisanship are statistically
entangled [[7]](#ref-7), [[8]](#ref-8). A state legislator can openly
gerrymander on partisan grounds and is shielded from federal review;
the same legislator drawing the same lines on racial grounds faces
strict scrutiny. After *Rucho*, state constitutional review under
*Moore v. Harper* [[9]](#ref-9) remains the only judicial avenue for
partisan claims, but it depends on the politics of each state's
supreme court and the language of its state constitution. Roughly ten
state supreme courts have so far recognized state-constitutional
partisan-gerrymandering claims; the rest have not [[10]](#ref-10).

The practical consequence of this combined doctrine, with federal
partisan review foreclosed by *Rucho*, Section 2 narrowed by
*Alexander* and *Callais*, and state review uneven and politically
contingent, is that redistricting has shifted from a once-per-decade
event into a continuous partisan exercise. Several states have already
redrawn maps mid-decade in response to electoral results rather than
census revision, and analysts expect the practice to expand as
legislative majorities turn over. A redistricting regime that updates
whenever the pen changes hands provides neither stable representation
nor predictable constituencies for the people being represented.

### 1.2 The normative paradox of "bias detection"

In response to *Rucho*'s manageability concern, a substantial
mathematical literature has produced quantitative tests for partisan
gerrymandering. The Efficiency Gap of Stephanopoulos and McGhee
[[11]](#ref-11) measures the disparity in "wasted votes" between
parties and was central to the lower-court ruling in *Whitford v. Gill*.
Wang's three tests [[12]](#ref-12), namely mean-median difference,
lopsided wins, and a $t$-test for partisan asymmetry, played a similar
role in *LWV v. Commonwealth* of Pennsylvania. Warrington's declination
[[13]](#ref-13) measures the asymmetry of the seats-votes kink at 50%.
Most influentially, the Markov Chain Monte Carlo ensemble methods
developed at Duke University [[14]](#ref-14) and the MGGG Redistricting
Lab [[15]](#ref-15) construct large samples of legally compliant
neutral maps and ask whether an enacted plan is an outlier with respect
to that distribution. Ensemble methods have been admitted as evidence
in *Common Cause v. Lewis* (N.C. 2019), *LWV v. Commonwealth* (Pa. 2018),
and as plaintiff support in *Allen v. Milligan*.

Every such test, however, embeds a contested normative claim about
what a "fair" map should look like. The Efficiency Gap is zero only
under seats-votes relationships close to proportional representation;
partisan symmetry presupposes mirror-image counterfactual responsiveness;
ensemble outlier tests use the local political geography filtered
through legally codified constraints as the baseline, but the choice
of which constraints to encode (compactness thresholds, county-split
tolerances, VRA encoding) is itself political. Chen and Rodden
[[16]](#ref-16) demonstrated that in many states even content-neutral
automated maps produce systematic seat bias against Democrats because
of residential clustering, so a nonzero Efficiency Gap or mean-median
value may reflect geography rather than intent. Pildes has long argued
that no neutral baseline exists [[17]](#ref-17), and Cain has framed
districting as a tradeoff among incommensurable goods that no scalar
metric can collapse without bias [[18]](#ref-18).

This is the central paradox of bias detection: any test for
gerrymandering imposes its own definition of fairness on the maps it
judges. The question is not whether the test is neutral (it is not)
but whether the normative commitments it encodes are made explicit
and are defensible on their own terms.

Step back from the technical details and a simpler observation emerges:
every one of these tests was built to catch a human in the act.
Polsby-Popper [[19]](#ref-19) and Reock [[20]](#ref-20) flag districts
that look "wrong," meaning shapes too contorted to have arisen by
ordinary line-drawing, which suggests that someone drew them that way
on purpose. The Efficiency Gap [[11]](#ref-11), mean-median asymmetry
[[12]](#ref-12), declination [[13]](#ref-13), and the ensemble outlier
tests of the Duke and MGGG groups [[14]](#ref-14), [[15]](#ref-15) do
the same job at the level of partisan outcomes: they ask whether the
partisan profile of the enacted plan is what a neutral line-drawer
would plausibly have produced, and call out plans that look engineered.
These are *forensic* instruments. They infer an actor's motives from
the traces the actor leaves. Their value depends on there being an
actor to investigate.

A district-drawing algorithm that admits no human input does not leave
those traces, because there is no actor in the loop to leave them. A
radial slice with $\mathrm{PP} = 0.09$ is not a covert favor to a
party or a community; it is the shape the rule produces on this
geometry. An Efficiency Gap of $+6.6\%$ on a deterministic plan is not
the fingerprint of a partisan operator; it is a description of where
the state's Democratic voters happen to live. The metrics still
compute. What they are designed to point at, a person making choices
in a process that gives them choices, is no longer in the picture.

### 1.3 Deterministic districting: a sixty-year tradition

The alternative to detection is generation: produce a single map from
inputs (state boundary, population, district count) by a fully
specified, reproducible procedure that admits no human discretion.
The intellectual line begins with Vickrey [[21]](#ref-21), who proposed
in 1961 that boundary line-drawing be done by "an automated and
impersonal procedure" to remove the discretion gerrymandering exploits.
Hess et al. [[22]](#ref-22) formalized the idea four years later as a
capacitated transportation problem, alternating between an assignment
step (minimize the population-weighted sum of squared distances from
each unit to a district center subject to equal population) and an
update step (recompute each center as the population-weighted centroid
of its assigned units). This is structurally equivalent to Lloyd's
algorithm with a capacity constraint and remains the canonical
mathematical formulation. Mehrotra, Johnson, and Nemhauser
[[23]](#ref-23) subsequently cast the problem as a column-generation
set partitioning program admitting exact optimization at moderate
scales.

Two contemporary lines extend this work. Brian Olson's BDistricting
[[24]](#ref-24) is a publicly available implementation that minimizes
population-weighted distance to district centers with equal-population
constraints, applied at census-block resolution; maps have been
generated for every state and updated each decennial census.
Cohen-Addad, Klein, and Young [[25]](#ref-25) provide the rigorous
reformulation as balanced *centroidal power diagrams*, generalizing
the Voronoi tessellation by assigning each seed an additive weight
(the Aurenhammer [[26]](#ref-26) construction) and solving for weights
that enforce equal mass per cell. Levin and Friedler [[27]](#ref-27)
independently rediscovered the capacitated $k$-means formulation and
applied it to all fifty states. A parallel branch, Warren Smith's
Shortest Splitline algorithm [[28]](#ref-28), recursively bisects the
state with the shortest population-balancing line; it is fully
deterministic and unique but lacks any global compactness or
boundary-awareness criterion.

Three observations link this tradition to the current work. First, all
extant deterministic algorithms balance *one* extensive quantity
across districts, namely population, and treat geographic area, if at
all, only indirectly through compactness shape metrics such as
Polsby-Popper [[19]](#ref-19) or Reock [[20]](#ref-20). Second, all
are governed by tie-breaking rules that are either implicit (left to
floating-point ordering) or only partially specified. Third, none have
been adopted as the formal map-drawing procedure of any U.S.
jurisdiction, though Iowa's Legislative Services Agency [[29]](#ref-29)
operates under a strict criteria cascade that has produced widely
accepted maps since 1980.

### 1.4 Contribution: dual balance of population and geography

The United States Constitution embeds, at the federal level, an
explicit balance between population-based and geography-based
representation: the House apportions seats by population (Art. I, §2),
the Senate allocates them equally per state (Art. I, §3). The design,
defended by Madison in *Federalist* Nos. 54–58 [[30]](#ref-30),
reflects the framers' judgment that representation should reflect both
*people* and *place*. This balance operates *between* chambers; it
has not, to our knowledge, been operationalized as a districting
objective *within* a single chamber. The proposal that follows is
novel in exactly that sense: the framers' bicameral compromise applied
as a single criterion at the level of one chamber's internal
boundaries, so that each congressional district represents both
roughly $1/N$ of a state's people and roughly $1/N$ of its territory.

The procedural commitment underneath that proposal is equally strong.
The algorithm reads only the state's shape, its census-unit populations,
and the seat count $N$. It cannot be used to harm any group, party, or
incumbent, and, by the same token, cannot be used to help any of them.
The deterministic-districting tradition surveyed above has often
defended procedural neutrality as a guard against gerrymandering. We
make the same commitment from the other side as well: the rule that
forecloses partisan engineering also forecloses majority-minority
remediation, incumbent protection, and community-of-interest
preservation. There is no partisan knob the algorithm refuses to turn;
there is no knob. Whether the symmetry is preferable to the status quo
of partisan and remedial discretion is not a question the algorithm
can answer; we argue only that the symmetry is the design's defining
property, not an accident.

Given a state boundary, census-unit population and area data, and a
target district count $N$, the algorithm produces a partition of the
state into $N$ districts whose score

$$
\mathrm{DBS}
= \frac{1}{1
   + \tfrac{1}{2}\,\overline{\mathrm{pop\_dev}}
   + \tfrac{1}{2}\,\overline{\mathrm{area\_dev}}}
$$

weights mean population deviation and mean area deviation equally,
where $\mathrm{pop\_dev}_i = |P(D_i) - P^{*}|/P^{*}$,
$\mathrm{area\_dev}_i = |A(D_i) - A^{*}|/A^{*}$, $P^{*} = P/N$,
$A^{*} = A/N$, and the overlines denote means over districts. The
generator does not iterate against this score directly; it places $N$
seeds radially around the population-weighted centroid (see Methods)
and performs a single capacitated first-fit assignment. Pop is
enforced as a hard cap of $P^{*}$ per district; area emerges from the
radial geometry. The resulting districts look like pie slices radiating
from the population center, each slice naturally spanning both dense
(near-center) and sparse (boundary-side) territory.

Seats are apportioned among the states by the Method of Equal
Proportions (Huntington-Hill), the standard since 1941 [[31]](#ref-31).
The core pipeline (seed placement, assignment, contiguity repair) is a
pure function of $(\text{units}, N)$. There are no tuning weights, no
iteration count, no stopping threshold, and no random seed; identical
inputs always yield byte-identical outputs. A single optional post-pass
(`--tighten-pop`) is provided to close the residual per-district
population deviation to a user-supplied *Reynolds v. Sims* tolerance
via greedy $L^{1}$ boundary-unit swaps; this is the only piece of the
pipeline that is not a pure function of the inputs and is off by
default. Updates occur only when the underlying census changes, every
ten years.

The algorithm reads neither party registration, vote history, nor
race. After *Alexander* and *Callais*, a generator that does not
consider race cannot, by construction, be a racial gerrymander under
*Shaw*. After *Rucho*, partisan gerrymandering is federally
unreviewable in any case. State constitutional review remains
available, but most state-court partisan-gerrymandering tests rely on
outcome metrics (Efficiency Gap, mean-median, ensemble outliers) that
a geography-only generator should pass routinely except where the
underlying political geography itself produces bias [[16]](#ref-16). A
residual concern is Section 2 of the VRA: a race-blind generator will
not automatically satisfy Section 2 in jurisdictions where the Gingles
preconditions are met, and the scoring harness must therefore flag
this risk without compromising the generator's content-neutrality.

The contributions of this paper are:

1. A deterministic, knob-free districting algorithm that produces
   radially-sliced districts and balances population and area equally
   as scored quantities. The algorithm is a pure function of the unit
   geometry and the district count; it has no iteration, no tunable
   weights, and no source of randomness.
2. A fully specified deterministic tie-breaking cascade sufficient to
   guarantee byte-identical output from a given input, and a proof
   that the cascade resolves every comparison the algorithm makes.
3. A decoupled scoring harness that applies the same metrics to the
   algorithm's output, to enacted maps, and to alternative plans,
   enabling transparent benchmarking against the methods surveyed
   above. Empirical results on Minnesota show DualBalance outperforming
   the enacted 119th-Congress map on the dual objective.
4. A discussion of the legal and normative tradeoffs the radial design
   imposes, including its tension with strict *Reynolds v. Sims*
   [[32]](#ref-32) population-equality jurisprudence, its weaker
   compactness profile relative to hand-drawn or blob-Voronoi designs,
   and its alignment with the post-*Callais* legal regime in which a
   content-neutral race-blind generator faces a narrower constitutional
   risk than any race-conscious remedy.

The remainder of the paper proceeds as follows. Section 2 formalizes
the algorithm in correspondence with [`docs/Formalism.md`](../docs/Formalism.md).
Section 3 reports computational results for Minnesota and benchmarks
against the enacted plan. Section 4 discusses limitations, legal
considerations, and directions for future work.

---

## 2. Methods

### 2.1 Problem statement

Given a state $S$ partitioned into atomic units
$U = \\{u_1, \ldots, u_M\\}$ (census blocks, block groups, or VTDs) and
a target district count $N$ fixed by apportionment, we seek a
deterministic assignment $\pi: U \to \\{1, \ldots, N\\}$ such that
each district $D_i = \pi^{-1}(i)$ is contiguous, non-empty, and as
close as the geometry allows to representing both $1/N$ of the state's
people and $1/N$ of the state's geography. Let
$P = \sum_u \mathrm{pop}(u)$ and $A = \sum_u \mathrm{area}(u)$ denote
state population and area, with per-district targets $P^* = P/N$ and
$A^* = A/N$.

The pipeline has three steps: radial seed placement (§2.2),
capacitated first-fit assignment (§2.3), and contiguity repair (§2.4).
The output of step three is the final plan; there is no iteration and
no post-hoc tightening.

### 2.2 Radial seed placement

Compute the population-weighted centroid

$$
c = (c_x, c_y) =
\left(
  \frac{\sum_u p_u\,x_u}{\sum_u p_u},\;
  \frac{\sum_u p_u\,y_u}{\sum_u p_u}
\right),
$$

where $x_u, y_u$ are the centroid coordinates of unit $u$ in an
equal-area projection and $p_u$ its population. Let $\mathrm{diag}$
denote the bounding-box diagonal of the units and set the seed radius
$r = 0.001 \cdot \mathrm{diag}$. For $d = 0, 1, \ldots, N-1$ place
seed $s_d$ at

$$
s_d = \bigl(c_x + r\cos(2\pi d/N),\, c_y + r\sin(2\pi d/N)\bigr).
$$

Seed 0 sits due east of the centroid; seeds advance counter-clockwise
by equal angular steps. The choice $r = 0.001 \cdot \mathrm{diag}$ is
small enough that the Voronoi cells generated by the seeds degenerate
to near-perfect radial slices through $c$, but large enough to keep
the seed positions numerically distinct.

The radial configuration is what carries the dual-balance property:
each slice spans both the dense (near-$c$) and sparse (boundary-side)
territory of the state, so the population it inherits is bounded by
the cap (§2.3) while the area it inherits is driven toward $A^*$ by
the slicing geometry.

### 2.3 Capacitated first-fit assignment

Let $d(u, i) = \|x_u - s_i\|$ be the Euclidean distance from unit $u$
to seed $i$. Initialize remaining capacities $\rho_i = P^*$ for
$i = 1, \ldots, N$. Sort all $(u, i)$ pairs by ascending normalized
distance $d(u, i) / \mathrm{diag}$ and walk the sorted list in order:

```
for each (u, i) in ascending d(u,i)/diag:
    if u already assigned: continue
    if ρ_i ≥ p_u: assign u to i;  ρ_i ← ρ_i − p_u
    else: skip
```

Population balance is enforced as a hard cap: no district receives
more than $P^*$. Any unit not placed by the end of the walk (a rare
integer-rounding edge case) is assigned to the district with the
largest remaining capacity; `argmax` resolves ties to the smallest
district id.

Ties in normalized distance break by ascending
$(\mathrm{unit\_id}, \mathrm{district\_id})$. There is no Lloyd
recentering, no iteration count, no convergence test: the radial
seeds do not drift, so a single assignment pass suffices.

### 2.4 Contiguity repair

After §2.3 every unit belongs to exactly one district, but a district
may consist of more than one connected component (rare on convex
states; more common on those with peninsulas, islands, or rural
enclaves). For each such district, the largest connected component by
total population is retained; units in the smaller components are
reassigned to neighboring districts one at a time, in the lowest-cost
direction. Cost is

$$
c(u, j) = \frac{d(x_u, s_j)}{\mathrm{diag}}
        + \frac{|P(D_j) + p_u - P^*|}{P^*}
        + \frac{|A(D_j) + a_u - A^*|}{A^*},
$$

combining a normalized distance term with normalized population and
area deviation penalties for the receiving district. Ties break in
cascade $(c, \mathrm{pop\_pen}, \mathrm{area\_pen}, \mathrm{dist},
\mathrm{district\_id})$ ascending. The repair sweep iterates until no
district has more than one connected component, capped at ten sweeps;
in practice it converges in zero or one sweep on real census
geometries.

### 2.5 Scoring

Define per-district relative deviations
$\mathrm{pop\_dev}_i = |P(D_i) - P^*|/P^*$ and
$\mathrm{area\_dev}_i = |A(D_i) - A^*|/A^*$ and let
$\overline{\mathrm{pop\_dev}}$, $\overline{\mathrm{area\_dev}}$ denote
their means over $i = 1, \ldots, N$. The DualBalance Score is

$$
\mathrm{DBS}
= \frac{1}{1
   + \tfrac{1}{2}\,\overline{\mathrm{pop\_dev}}
   + \tfrac{1}{2}\,\overline{\mathrm{area\_dev}}}. \tag{1}
$$

The $0.5/0.5$ weighting makes the error a convex combination of the
two mean deviations: each district is judged on representing roughly
$1/N$ of the people *and* roughly $1/N$ of the state's geography. The
score reaches $1.0$ for a perfectly balanced plan and approaches $0$
as deviations grow without bound. Secondary metrics (Polsby-Popper
compactness [[19]](#ref-19) and Reock [[20]](#ref-20)) are computed
alongside but not optimized against; radial slices have lower
compactness than blob-Voronoi or hand-drawn districts by construction,
and this is a deliberate trade in service of the dual-balance objective.

The generator does not directly minimize (1); it minimizes
population-capacitated geographic assignment cost with radial seeding,
which on the Minnesota PoC produces a higher DBS than the enacted
plan ($0.6472$ vs $0.6390$) despite its weaker compactness profile.

### 2.6 Optional: $L^{1}$ pop-tightening

The radial pipeline produces per-district pop deviation in the 5–15%
range on real census geometry, well above the ~0.5% threshold required
by *Reynolds v. Sims* for U.S. congressional districts [[32]](#ref-32).
An optional post-pass (`--tighten-pop`) closes this gap via greedy
boundary-unit swaps under an $L^{1}$ objective. Each pass:

1. Compute the signed deviations $\delta_i = P(D_i) - P^{*}$.
2. For every boundary unit $u$ in district $d_{\mathrm{src}}$ and
   every neighboring district $d_{\mathrm{dest}}$, compute the $L^{1}$
   change after moving $u$:

$$
\Delta(u, d_{\mathrm{dest}}) =
  |\delta_{d_{\mathrm{src}}} - p_u| - |\delta_{d_{\mathrm{src}}}|
+ |\delta_{d_{\mathrm{dest}}} + p_u| - |\delta_{d_{\mathrm{dest}}}|.
$$

3. Sort candidates by ascending $\Delta$ and accept the most negative
   one whose source district remains contiguous after the move. Stop
   when every district lies within the user-supplied tolerance or no
   contiguity-preserving improving move exists.

The $L^{1}$ objective is essential here. The radial seed placement
puts the most over-target and most under-target districts on opposite
sides of the population centroid, so no single adjacent-slice swap
reduces the $L^{\infty}$ maximum, but many such swaps reduce the sum.
The canonical Reynolds-tightening literature uses $L^{\infty}$ and
bottoms out at ~5% on this geometry; the $L^{1}$ formulation runs to
completion in ~80 swaps on Minnesota, reducing $\mathrm{pop\_dev\_max}$
from $0.1124$ to $0.0021$ (well inside the 0.5% target) while leaving
$\mathrm{area\_dev\_mean}$ essentially unchanged at $1.04$. The radial
structure is preserved visually because the algorithm only moves
units at slice boundaries between adjacent slices.

The pass is off by default and gated by an explicit flag. Pure radial
remains the principled algorithm; pop-tightening is an opt-in
concession to legal compliance.

### 2.7 Determinism and tie-breaking

The pipeline is deterministic at every step. The only sources of
ambiguity (equidistant seed-to-unit pairs in §2.3, equal-capacity
fallbacks for unplaced units, and equal-cost candidates in §2.4) all
resolve to a fixed cascade with no remaining ambiguity:

1. In assignment, ties on normalized distance break by ascending
   $(\mathrm{unit\_id}, \mathrm{district\_id})$.
2. In the fallback for unplaced units, ties on remaining capacity
   break to the smallest district id.
3. In contiguity repair, ties on cost break by ascending
   $(\mathrm{pop\_pen}, \mathrm{area\_pen}, \mathrm{distance},
   \mathrm{district\_id})$.

The implementation uses no random number generator, no wall-clock
input, and no hash-order dependence. Reordering the input rows or
changing the floating-point libraries does not change the output;
identical inputs always yield byte-identical outputs.

### 2.8 Out-of-scope inputs

The generator reads only geography and population. Party registration,
vote history, race, demographics, communities of interest, and
competitiveness are not inputs. The scoring harness may *report*
partisan or demographic diagnostics on the resulting map but does not
feed them back into the generator.

---

## 3. Results

### 3.1 Test bed: Minnesota, 2020 PL 94-171

We evaluate the algorithm on Minnesota's congressional districting
($N = 8$ apportioned seats) using the 2020 PL 94-171 redistricting
data file. The input is the TIGER/Line 2020 VTD (voting tabulation
district) shapefile for Minnesota (4,110 atomic units, total
population $P = 5{,}706{,}494$, total land area
$A = 225{,}187\;\mathrm{km}^2$), joined to the Census Data API's
`P1_001N` total-population field, projected to EPSG:5070 (CONUS
Albers, equal area) at load time. Per-district targets are
$P^{*} = P/8 = 713{,}312$ and $A^{*} = A/8 = 28{,}148\;\mathrm{km}^2$.
All runs are deterministic and reproducible from the script
[`scripts/prep_mn_units.py`](../scripts/prep_mn_units.py) (which
fetches TIGER and joins the Census API output) plus the CLI
invocation. The data pipeline is documented end-to-end in
[`docs/mn-poc-walkthrough.md`](../docs/mn-poc-walkthrough.md).

We compare three plans on the same 4,110-VTD input:

- **Pure radial.** The default algorithm (§2.2–§2.4). No tuning
  knobs.
- **Radial + tighten-pop** ($\tau = 0.005$). The default algorithm
  followed by the optional $L^{1}$ population-tightening pass (§2.6)
  targeting per-district deviation within 0.5% of $P^{*}$.
- **Enacted Minnesota 119th-Congress plan.** The court-drawn,
  legislatively enacted U.S. House districts currently in force,
  joined to the same VTDs and scored with the same harness.

### 3.2 Headline scores

Table 1 reports the DualBalance Score and supporting metrics for the
three plans. $\mathrm{PP}$ is Polsby-Popper; Reock is Reock;
subscripts $\mathrm{min}$, $\mathrm{mean}$ denote per-district min and
mean over the eight districts. Best result per row in **bold**.

**Table 1.** DualBalance metrics on the Minnesota PoC (4,110 VTDs, 8
districts, 2020 PL 94-171 population).

| Metric | Pure radial | Radial + tighten-pop | Enacted (119th) |
|---|---:|---:|---:|
| $\mathrm{DBS}$ | 0.6472 | **0.6574** | 0.6390 |
| $\overline{\mathrm{pop\_dev}}$ | 5.08% | **0.08%** | 0.42% |
| $\mathrm{pop\_dev}_{\max}$ | 11.24% | **0.21%** | 1.32% |
| $\overline{\mathrm{area\_dev}}$ | **103.9%** | 104.2% | 112.6% |
| $\mathrm{area\_dev}_{\max}$ | 271.0% | 275.1% | **241.0%** |
| $\mathrm{PP}_{\mathrm{mean}}$ | 0.200 | 0.162 | **0.320** |
| $\mathrm{PP}_{\min}$ | 0.094 | 0.047 | **0.178** |
| $\mathrm{Reock}_{\mathrm{mean}}$ | 0.361 | 0.342 | **0.419** |

Three findings.

**Pure radial beats the enacted plan on the DualBalance Score.** The
pure-radial pipeline scores 0.6472 against the enacted plan's 0.6390,
a margin of $+1.3\%$ on the project's own metric, without any
iteration, tuning, or post-processing. The advantage comes entirely
from area balance ($\overline{\mathrm{area\_dev}}$ 103.9% vs 112.6%):
radial slicing assigns each district a coherent slice of the state's
geometry that mixes high- and low-density territory, while the
enacted plan carves the Twin Cities metro into four compact urban
seats and leaves four large rural seats. The DualBalance Score
penalizes the latter pattern more heavily because it weights area
deviation equally with population deviation.

**The optional tighten-pop pass closes the legal gap and improves the
DualBalance Score.** The pure-radial plan's $\mathrm{pop\_dev}_{\max}$
of 11.24% is well above the ~0.5% deviation typical of enacted U.S.
House plans [[32]](#ref-32). Running the optional $L^{1}$
pop-tightening pass (§2.6) executed 81 boundary-unit swaps in ~18
seconds of compute, driving $\mathrm{pop\_dev}_{\max}$ from 11.24% to
0.21%, well inside the Reynolds-compliant range and tighter than the
enacted plan's 1.32%. $\overline{\mathrm{area\_dev}}$ rose by only
0.3 percentage points; the DualBalance Score *improved* from 0.6472 to
0.6574, because the pop-balance gain dominates the small area-balance
loss. The tightened plan exceeds the enacted plan on the two
DualBalance inputs (population and mean area deviation) and on the
combined score.

**Compactness is the price.** The enacted plan beats DualBalance on
every compactness measure: $\mathrm{PP}_{\min}$ 0.178 vs 0.094 in the
radial plan and 0.047 after pop-tightening; $\mathrm{PP}_{\mathrm{mean}}$
0.320 vs 0.200 / 0.162; $\mathrm{Reock}_{\mathrm{mean}}$ 0.419 vs
0.361 / 0.342. The radial geometry is structurally less compact than
hand-drawn blob shapes: long thin slices from the population centroid
score lower on circular-shape metrics by construction. Pop-tightening
makes this worse (it moves units across slice boundaries, which
inserts small indentations into otherwise smooth radial cuts),
pushing the smallest-PP slice from 0.094 (already at the "0.10 raises
eyebrows" informal threshold) down to 0.047. Whether the trade is
acceptable is a normative question we return to in §4.3; on the
algorithm's own metric, the trade is favorable.

### 3.3 Map comparison

![Minnesota congressional districts under three plans.](figures/mn_radial_with_tighten.png)

**Figure 1.** Minnesota congressional districts under three plans.
**Left:** the enacted 119th-Congress plan, with four compact Twin
Cities seats and four large rural seats. **Center:** pure-radial
DualBalance (score 0.6472); eight slices radiate from the
population-weighted centroid (near Minneapolis-St. Paul), each
spanning both dense and sparse territory. **Right:** radial +
`--tighten-pop 0.005` (score 0.6574); the radial structure is
preserved (units have moved only at slice boundaries) and per-district
population is now Reynolds-compliant.

### 3.4 Determinism check

We re-ran `dualbalance generate --config configs/mn_vtd.yaml` ten
times in succession, comparing each run's `map.geojson` and
`metrics.json` by byte hash. All ten outputs are identical, including
the order of features in the GeoJSON. We also re-ran the same
configuration after randomly shuffling the input rows; the output
remained byte-identical. The CLI integration test
`test_generate_determinism_via_cli` pins this property in CI.

### 3.5 Per-district breakdown

Table 2 reports the per-district metrics for the radial +
tighten-pop plan, indexed by seed angle (district 0 sits due east of
the population-weighted centroid; subsequent districts advance
counter-clockwise in steps of $2\pi/8$ rad). District IDs are a
deterministic function of seed angle and carry no political meaning.
Areas are in km².

**Table 2.** Per-district breakdown, radial + tighten-pop 0.5%.

| District | Population | Area | $\mathrm{pop\_dev}$ | $\mathrm{area\_dev}$ | $\mathrm{PP}$ | $\mathrm{Reock}$ |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 712,841 | 1,010 | 0.07% | 96.4% | 0.228 | 0.454 |
| 1 | 714,816 | 9,620 | 0.21% | 65.8% | 0.047 | 0.147 |
| 2 | 712,145 | 105,594 | 0.16% | 275.1% | 0.152 | 0.369 |
| 3 | 713,263 | 50,054 | 0.01% | 77.8% | 0.146 | 0.268 |
| 4 | 714,168 | 46,060 | 0.12% | 63.6% | 0.150 | 0.267 |
| 5 | 713,368 | 10,882 | 0.01% | 61.3% | 0.137 | 0.422 |
| 6 | 713,013 | 1,481 | 0.04% | 94.7% | 0.117 | 0.301 |
| 7 | 712,880 | 477 | 0.06% | 98.3% | 0.318 | 0.510 |

District 2 inherits Minnesota's northern panhandle and is the largest
by area (~3.8 × $A^{*}$), while District 7 contains only the Twin
Cities urban core (~0.02 × $A^{*}$). All eight districts are within
0.21% of $P^{*}$. The largest single source of area imbalance,
District 2's 275% over-target area, is geometric: the population
density in the northern panhandle is roughly two orders of magnitude
lower than in the Twin Cities, so any partition that holds each
district to $P^{*}$ must give the rural districts disproportionate
area. This is a property of Minnesota's density profile, not the
algorithm; the enacted plan exhibits the same phenomenon (District 7
of the enacted plan covers 241% over-target area for the same reason).

### 3.6 Descriptive diagnostics: partisan, race, county

We report a second tier of numbers (partisan, racial, and county-split
metrics) not because the algorithm uses them, but because readers will
reasonably ask how a procedurally-neutral plan *looks* on the
diagnostics conventionally applied to enacted maps. These numbers are
reported for the pure-radial plan against 2020 presidential returns
(Dave's Redistricting App / dra2020/vtd_data, joined to TIGER 2020
GEOID20s) and Census PL 94-171 voting-age population by race. The
generator reads none of this data; it is joined onto the units only
at scoring time. We emphasize, in line with §4.7, that these are
descriptive statistics of the resulting partition, not evaluative
scores of it.

**Partisan profile.** Minnesota cast 1,484,065 R and 1,717,077 D
two-party presidential votes in 2020 (46.4% statewide R share, 53.6%
D). On the pure-radial plan the eight districts split 4–4 between
R-winning and D-winning, against a seats-proportional expectation of
$3.7$ R seats. The two D-leaning slices contain the Minneapolis-St.
Paul metro and run at 64–75% D; the two R-leaning slices reaching
into the western and southern parts of the state run at 55–65% R;
the four remaining slices are within $\pm 5$ points of even. The
efficiency gap is $+6.6\%$ (positive = R-favorable) and the
mean-median R difference is $+3.9$ points (positive = D-favorable,
since the typical district leans more D than the average district).
These two "forensic" partisan numbers point in opposite directions
because they measure different things on the same map; both are
entirely artifacts of where Minnesota's Democrats live (packed into
the metro), not of any choice made by the algorithm.

**Race / VAP profile.** Minnesota's voting-age population is 80.0%
non-Hispanic white, 5.9% Black, 5.0% Hispanic, 4.9% Asian, and 1.1%
American Indian / Alaska Native. The pure-radial plan produces zero
majority-minority districts, in the strict sense that no district has
a non-Hispanic-white share below 50%. The district containing the
Minneapolis-St. Paul urban core (District 7) has the lowest
non-Hispanic-white share at 65.3%, the highest Black VAP share at
15.7%, and the highest Hispanic VAP share at 6.7%; the remaining
seven districts run 73–90% non-Hispanic white. The enacted
119th-Congress Minnesota plan also has no majority-minority districts.
Minnesota does not, on the 2020 census, contain a geographic region
in which a single minority group concentrates densely enough to
support a 50%-VAP district of conventional size; this is a property
of the state's demographic geography, not of the algorithm.

**County splits.** The pure-radial plan splits 44 of Minnesota's 87
counties into a total of 143 cross-district pieces. This is a direct
consequence of radial slicing: any line from the population centroid
to the boundary crosses several county lines along the way. The
enacted plan splits fewer counties (it is drawn to follow them more
closely), at the cost of the larger area imbalance that Table 1
reports. Whether one prefers a county-aware or a county-blind
line-drawing rule is a policy question; the DualBalance rule simply
does not encode county membership.

**What to read into these numbers.** The point of reporting them is
to make a single observation precise: every conventional metric that
one might bring to bear on a districting plan continues to compute on
a DualBalance plan, and the values look "ordinary" in the sense that
they sit in the same range as enacted-plan values for the same state.
But the metrics' *interpretation* differs by construction. On an
enacted plan, an efficiency gap of $+6.6\%$ invites the inference
that someone packed and cracked a partisan opponent; on a DualBalance
plan it cannot, because no one packed or cracked anyone. On an
enacted plan, zero majority-minority districts invites the inference
that the line-drawers either declined to honor *Allen v. Milligan*
[[4]](#ref-4) or did honor it on a geography that could not support a
majority-minority seat; on a DualBalance plan only the latter
inference is available, because the algorithm has no way of seeing
race. The numbers are the same; what they license is different. We
return to this point in §4.7.

---

## 4. Discussion

### 4.1 What the Minnesota result does and does not show

The headline finding, that a knob-free deterministic algorithm (with
or without the optional pop-tightening pass) beats the human-drawn
enacted Minnesota plan on the DualBalance Score, is a single-state
existence result. It demonstrates that radial slicing through the
population-weighted centroid can produce a districting that scores
competitively on the project's own dual-balance objective without
reading party, race, or any other discretionary input. It does not by
itself demonstrate that the same approach generalizes across all 50
states, that the DualBalance Score is the right scalar to optimize,
or that the resulting maps would survive judicial or political
scrutiny. We discuss each of these in turn.

### 4.2 The score formula privileges what the algorithm produces

A natural objection to a result of the form "Algorithm $A$ beats Plan
$B$ on Metric $M$" is that $A$ and $M$ may have been co-designed. We
address this directly. The DualBalance Score (1) was specified in
advance of the algorithmic choice. We considered three forms during
development: the published weighted form
$\mathrm{DBS}_{\mathrm{w}} = 1/(1 + 0.5\,\overline{\mathrm{pop\_dev}} + 0.5\,\overline{\mathrm{area\_dev}})$;
a sum-of-means "classic" form
$\mathrm{DBS}_{\mathrm{c}} = 1/(1 + \overline{\mathrm{pop\_dev}} + \overline{\mathrm{area\_dev}})$;
and an $L^{\infty}$ form
$1/(1 + \max_i [0.5\,\mathrm{pop\_dev}_i + 0.5\,\mathrm{area\_dev}_i])$.
The radial algorithm beats the enacted Minnesota plan on the first
two; on the third the enacted plan wins, because the radial design
concentrates area imbalance in a single rural district. We selected
the weighted form for the headline metric because it cleanly
implements the "each district holds roughly $1/N$ of people *and*
$1/N$ of geography" reading, but readers should know that the choice
matters. The per-district deviations and compactness values are
reported alongside the score so consumers can recompute against any
preferred aggregation.

A separate concern is that population density variance fundamentally
bounds the achievable $\overline{\mathrm{area\_dev}}$ on any
pop-balanced plan. Both the enacted plan and our radial pipeline land
in the same neighborhood ($\overline{\mathrm{area\_dev}} \approx 1.0$
to $1.1$), and on Minnesota's geometry, where the Twin Cities
metropolitan area holds roughly 55% of the population in 3% of the
land area, this is essentially a hard floor. Improvements beyond
that floor would require districts that systematically span urban
and rural territory, which is exactly what radial slicing produces.
The 8.7-percentage-point gap (103.9 vs. 112.6) we report is the
operational measurement of how much area balance radial slicing
recovers, given that floor.

### 4.3 Compactness is the trade

The radial design pays its area-balance dividend in compactness. The
smallest-PP slice in the tightened plan is 0.047, against an informal
court-testimony threshold of ~0.10 below which a district is
considered unusually shaped [[19]](#ref-19). The enacted Minnesota
plan's worst PP is 0.178; our worst is roughly a quarter of that
value.

We make three observations about this trade.

**Compactness is a metric, not a constitutional requirement.**
*Polsby-Popper* as a measure was published in 1991 [[19]](#ref-19);
it appears in no federal statute and binds no court. Courts have used
compactness as *evidence* of intent in racial-gerrymandering cases
(*Shaw v. Reno* and progeny), but the constitutional violation in
those cases turns on the use of race in line-drawing, not on the
resulting shape per se. A deterministic, race-blind rule does not
carry the racial intent that triggers *Shaw*; the resulting low
compactness is a property of the rule, not a signal of an attempt to
disadvantage any group.

**Compactness assumes a baseline of comparison.** A district is
"bizarrely shaped" relative to surrounding districts that are not.
If all eight districts in a state are produced by the same geometric
rule and all eight share a similar slice-like character, the
comparative baseline shifts. The aesthetic objection to long thin
shapes is partly historical: it picks out districts that depart from
the surrounding norm of compact blobs. A scheme in which every
district is a slice does not pick anything out.

**The Voting Rights Act trade-off is real.** *Allen v. Milligan*
[[4]](#ref-4) reaffirmed Section 2's vote-dilution doctrine;
*Alexander* [[5]](#ref-5) and *Callais* [[6]](#ref-6) significantly
narrowed its practical reach. The radial design splits the Twin
Cities urban area (and with it, any majority-minority population
concentrated there) across multiple districts. In jurisdictions
where the *Gingles* [[2]](#ref-2) preconditions are met, a race-blind
generator may produce a plan that fails Section 2 review where a
race-conscious plan would not. After *Callais* the constitutional
risk of a race-conscious remedy has grown; the legislative question
of whether to accept slightly diluted minority representation in
exchange for a generator that cannot be partisan-tuned is, properly,
for legislatures and constitutional litigation rather than for an
algorithm.

### 4.4 Relationship to prior deterministic methods

DualBalance fits within the deterministic-districting tradition
surveyed in §1.3 but differs from each prior method on a specific
axis.

**Versus Smith's Shortest Splitline** [[28]](#ref-28). Splitline is
also fully deterministic and unique. It recursively bisects the state
with the shortest population-balancing line, with no global
compactness or balance criterion other than line length. Splitline
produces visually striking but completely arbitrary splits, because
a district can lose half its territory once the shortest cut happens
to fall on that side. DualBalance grounds its geometry in the
population centroid rather than in arbitrary straight cuts and
therefore produces results that reflect the state's underlying
density structure.

**Versus Olson's BDistricting** [[24]](#ref-24). BDistricting also
minimizes population-weighted distance to district centers with
equal-population constraints, applied at block resolution. It uses
farthest-point or random seed initialization with iterative
refinement to convergence. The resulting maps are blob-shaped
(Voronoi cells around dispersed seed centers) and score well on
compactness but exhibit large area imbalance. DualBalance differs in
seed placement (radial around the population centroid versus
dispersed across the state) and in iteration discipline (single pass
versus Lloyd convergence). Our reading of the result table is that
radial seeding gives up compactness to gain area balance, a different
point on the same trade-off curve BDistricting sits on.

**Versus centroidal power diagrams** [[25]](#ref-25). The
Cohen-Addad-Klein-Young construction is the rigorous mathematical
generalization of equal-mass Voronoi cells. It solves for weights
$\\{w_i\\}$ such that the resulting power diagram cells each carry
exactly $1/N$ of the underlying mass. Their algorithm is deterministic
modulo a tie-breaking rule and produces fully equal-population cells
by construction. We do not solve the same problem: their construction
balances a single quantity (population) exactly, while ours balances
two quantities (population and area) approximately. The radial seed
placement is the mechanism by which the second balance approximation
is recovered.

**Versus capacitated $k$-means** [[27]](#ref-27) **and the Hess-style
location-allocation lineage** [[22]](#ref-22), [[23]](#ref-23). These
are the closest mathematical cousins. The capacitated assignment step
(§2.3) is essentially Hess's 1965 transportation step. The novelty in
DualBalance is not the assignment rule but the seed placement: radial
seeds force a slice geometry that no Lloyd-iterated $k$-means
converges to, because Lloyd recentering pulls seeds away from a
tightly clustered radial configuration. Disabling iteration is
therefore not optional in the radial design; it is what preserves the
geometry.

### 4.5 Limitations

**Single-state evidence.** The Minnesota result reports one state with
one apportioned seat count under one census release. We do not yet
have evidence that the radial design beats enacted plans on other
states. States with markedly different density profiles (for example,
a single dominant metropolitan area in a small geography such as
Massachusetts or Connecticut, versus a multi-center state such as
Texas or Florida, versus a near-uniform-density state such as Iowa or
Vermont) should be expected to produce qualitatively different
results. Section 4.6 below identifies cross-state validation as the
most important near-term follow-up.

**Worst-district area outlier.** The radial design concentrates the
area imbalance in a single rural district (here, District 2 at 275%
over-target area). This is geometric (it cannot be avoided on any
partition that imposes a population cap on a state with the density
profile of Minnesota), but our $\mathrm{area\_dev}_{\max}$ of 275% is
worse than the enacted plan's 241%, even though
$\overline{\mathrm{area\_dev}}$ is lower. The radial design therefore
distributes the area imbalance unevenly; whether this is preferable
to the enacted plan's more uniform distribution is a separable
normative question.

**No multi-unit transportation step.** The optional `--tighten-pop`
pass is a greedy single-unit swap procedure. A true two-dimensional
transportation LP (bounding both population and area simultaneously)
would be a stronger candidate for the "directly minimize the
DualBalance objective" role we currently leave to the radial geometric
heuristic. We have not implemented or evaluated such a step; it is
documented as future work.

**Computational cost.** Pure radial assignment runs in a fraction of
a second on Minnesota. The optional pop-tightening pass takes ~18
seconds to drive 80 swaps. We have not profiled larger states
(California, Texas) and do not currently know how the pop-tightening
pass scales with $|U|$ and $N$; in the worst case it is $O(|U|^2 N)$
per swap due to the contiguity check.

**The compactness floor.** The worst slice's $\mathrm{PP}$ of 0.047
(after pop-tightening) is well below the informal court-testimony
threshold of 0.10. We argue in §4.3 that the constitutional doctrine
on compactness turns on intent rather than shape per se, but readers
who reject that argument should regard the 0.047 figure as a hard
ceiling on the maps' legal viability under the *Shaw* [[3]](#ref-3)
line.

### 4.6 Future work

**Multi-state validation.** Reproduce the Minnesota result for the
other 49 states. We expect radial slicing to perform best on states
with one or two dense metropolitan centers and a large rural
hinterland (the Minnesota profile) and worst on states with multiple
dispersed metro centers (e.g., Texas, California, Florida) where the
single-centroid radial assumption may produce slices that don't span
the state's density variation cleanly.

**Multi-center radial seeding.** For states with multiple metropolitan
centers, the population-weighted centroid sits in a low-density region
between them, and radial slicing from that point may produce slices
that miss the actual density structure. A generalization in which
seeds are placed on circles around *each* of $k$ pre-computed
metropolitan centers (with the choice of $k$ deterministic from the
population distribution) is a natural extension. We have not
implemented this.

**Direct 2D transportation step.** Replace the radial-plus-tighten
two-stage pipeline with a single optimization step that minimizes the
DualBalance Score under contiguity constraints. This is
computationally much more expensive than the current pipeline but
would be the mathematically clean answer to "which plan directly
minimizes the DualBalance objective." Whether it produces
qualitatively different maps is an empirical question.

**Comparison against BDistricting and Splitline.** We compare
DualBalance against the enacted plan; we have not yet scored
BDistricting's published maps or computed Splitline maps for the
same states and metrics. A full benchmark across deterministic
methods would situate DualBalance more clearly in the existing
literature.

**Scoring-harness extensions.** The current harness reports
population, area, Polsby-Popper, Reock, convex-hull and length-width
compactness, density, county splits, race VAP, and 2020 presidential
two-party votes. Natural additions include declination, additional
election years, and Citizen Voting Age Population (CVAP) for VRA
diagnostics. These are reporting extensions and would not feed back
into the generator (§2.8).

### 4.7 Forensic metrics applied to a generative procedure

The full menu of gerrymandering diagnostics (Polsby-Popper, Reock,
convex-hull and length-width compactness, the Efficiency Gap,
mean-median asymmetry, declination, majority-minority counts,
county-split counts, ensemble outlier tests) was developed for a
single purpose: to detect when a human drawing district lines has
crossed from neutral line-drawing into deliberate manipulation. Each
is a forensic instrument. Each presupposes the kind of process where
"something happened" is a coherent question and the metric is
supposed to help answer it.

Generation by deterministic algorithm changes the question. There is
no human drawing the lines. There is no party-aware decision, no
race-aware decision, no incumbent-aware decision, and no
community-aware decision, because the algorithm has no input by which
any such consideration could enter. There is no place in the pipeline
at which a decision-maker chose one boundary over another for a reason
a metric might detect. The line-drawing is a function:
$\pi = f(\text{geometry}, \text{population}, N)$.

This matters in two ways. First, the metrics' *measurement* is still
informative. A district with $\mathrm{PP} = 0.09$ is still
geometrically less compact than a district with $\mathrm{PP} = 0.35$;
a plan with an Efficiency Gap of $+6.6\%$ still produces, under that
year's voter distribution, more wasted votes on one side than the
other. Reporting these numbers is reasonable; consumers of the plan
deserve to know them. Second, the metrics' *inference* is no longer
available. A $\mathrm{PP}$ of 0.09 in an enacted plan invites the
question "who drew this oddly-shaped district and what were they
trying to do?". In a DualBalance plan there is no *who* and no
*trying*: the district has $\mathrm{PP} = 0.09$ because radial slices
through a population-weighted centroid have that compactness on the
geometry of Minnesota, period. An Efficiency Gap of $+6.6\%$ in an
enacted plan suggests packed and cracked Democratic voters; in a
DualBalance plan it reports where Democratic voters *actually live*
relative to the radial geometry, with no human packing or cracking
anywhere in the pipeline. Zero majority-minority districts in an
enacted plan invites scrutiny about whether the line-drawers honored
*Allen v. Milligan* [[4]](#ref-4); in a DualBalance plan it reports
the demographic geography of the state, unfiltered by any race-aware
human intervention. The numbers continue to compute. What they license
has changed.

Three implications follow.

**Compactness as a constitutional threshold loses purchase.** *Shaw
v. Reno* [[3]](#ref-3) and its progeny use the bizarre shape of a
district as evidence that race predominated in its drawing. The
evidentiary logic is straightforward: a normal line-drawing process
tends to produce ordinarily-shaped districts; an unusual shape
suggests an unusual process; an unusual process suggests that
something other than ordinary criteria drove the drawing; race,
where alleged, becomes the residual explanation. The chain breaks at
the first link in our case. The unusual shape is a property of the
rule, not of the process applied to this particular district by this
particular line-drawer; every district produced by the rule on every
state has the same shape character. There is no inference from shape
back to motive because there is no motive in the chain.

**Partisan diagnostics measure geography, not intent.** *Rucho v.
Common Cause* [[1]](#ref-1) foreclosed federal partisan-gerrymandering
review on the ground that no judicially manageable standard exists
for distinguishing constitutionally acceptable from unacceptable
partisan motivation in line-drawing. The Court's reasoning supposes a
line-drawer whose motivation is the analytic object. A DualBalance
plan has no such object. State-court tests that rely on the Efficiency
Gap or mean-median asymmetry typically interpret a non-zero value as
*prima facie* evidence of partisan intent; on a DualBalance plan the
same value is evidence only of a particular voter-density distribution.
The plan is in no useful sense "partisan"; it is a function of
geometry and population, evaluated against a layer of vote data the
function never saw.

**Ensemble outlier tests lose their baseline.** The Duke and MGGG
ensembles [[14]](#ref-14), [[15]](#ref-15) compare an enacted plan to
a sample of legally compliant alternatives that a hypothetical neutral
line-drawer might have produced. The ensemble is meaningful because
it stands in for the absent neutral line-drawer; the enacted plan
being an outlier suggests the actual line-drawer differed from the
neutral one. DualBalance *is* the neutral line-drawer, in a much
stronger sense than the ensemble's sample mean. Asking whether the
DualBalance plan is an outlier with respect to its own ensemble is
not an obviously meaningful question; the ensemble has been collapsed
to a single point.

These observations do not amount to a claim that metrics should be
ignored. They are useful as descriptive geometry, as inputs to a
public discussion of what a plan looks like, and as comparison
anchors when the same metrics are applied to several plans together.
What they cannot do, on a deterministic generated plan, is what they
were built to do on an enacted plan: tell us whether a person
manipulated the lines and to what end.

### 4.8 What this paper claims, and what it does not

The paper makes four claims.

First, that a knob-free, race-blind, partisan-blind, deterministic
districting algorithm exists that produces output competitive with,
and on a single empirically tested state superior to, the
corresponding hand-drawn enacted plan on a prespecified
population-and-area objective. The algorithm's output is
byte-reproducible and updates only with the ten-year census.

Second, that the algorithm's procedural neutrality is symmetric. By
construction, the rule cannot be used to harm any group, party, or
incumbent, and cannot be used to help any of them either. The same
property that makes a partisan gerrymander impossible makes a
race-conscious remedy impossible. Whether the symmetry is morally
preferable to the status quo of partisan and remedial discretion is
a question the algorithm itself cannot answer; it is a question for
legislatures, courts, and voters. We claim only that the symmetry is
the algorithm's defining property, not an incidental side-effect.

Third, that the post-*Callais* legal landscape gives a generator of
this kind a narrower constitutional exposure than any race-conscious
or partisan-conscious alternative. Federal partisan review is
foreclosed under *Rucho*; federal racial-gerrymander risk is
contracting under *Alexander* and *Callais*; state-court remedies for
partisan claims depend on the politics of each state's supreme court.
A rule whose inputs do not contain race or party is, in the strict
sense, not subject to either body of doctrine.

Fourth, that the conventional gerrymandering metrics (compactness
scores, Efficiency Gap, mean-median, ensemble outliers,
majority-minority counts) are forensic instruments for inferring
intent in a line-drawing process that has none under this procedure.
They continue to compute and are reported alongside the DualBalance
metrics for transparency; they should not be taken to license, on
this plan, the inferences they license on an enacted plan. This is
the strongest framing claim of the paper, and the one most likely to
draw resistance: it asks the redistricting literature to accept that
an entire toolkit of normative measurement, developed over thirty
years for very good reasons, is the wrong toolkit for the generative
case.

The paper does not claim that the DualBalance Score is universally
the right objective for redistricting, that radial slicing dominates
all enacted plans across all states, that compactness can or should
be ignored, or that Section 2 of the Voting Rights Act can be safely
disregarded after *Callais*. The trade-offs documented above are
real, and a serious adopter of the method would have to weigh them
against the trade-offs the status quo presents.

---

## References

<a id="ref-1"></a>**[1]** *Rucho v. Common Cause*, 588 U.S. 684 (2019).
No. 18-422 (June 27, 2019). Roberts, C.J., for the Court.

<a id="ref-2"></a>**[2]** *Thornburg v. Gingles*, 478 U.S. 30 (1986).

<a id="ref-3"></a>**[3]** *Shaw v. Reno*, 509 U.S. 630 (1993).

<a id="ref-4"></a>**[4]** *Allen v. Milligan*, 599 U.S. 1 (2023).
No. 21-1086 (June 8, 2023). Roberts, C.J., for the Court.

<a id="ref-5"></a>**[5]** *Alexander v. South Carolina State Conference
of the NAACP*, 602 U.S. 1 (2024). No. 22-807. Alito, J., for the Court.

<a id="ref-6"></a>**[6]** *Louisiana v. Callais*, 608 U.S. ___ (2026).
No. 24-109 (April 29, 2026). Alito, J., for the Court.

<a id="ref-7"></a>**[7]** Richard L. Hasen. "Race or Party, Race as
Party, or Party All the Time: Three Uneasy Approaches to Conjoined
Polarization in Redistricting and Voting Cases." *William & Mary Law
Review* 59 (2018): 1837.

<a id="ref-8"></a>**[8]** Nicholas O. Stephanopoulos. "Race, Place,
and Power." *Stanford Law Review* 68 (2016): 1323.

<a id="ref-9"></a>**[9]** *Moore v. Harper*, 600 U.S. 1 (2023).
No. 21-1271 (June 27, 2023). Roberts, C.J., for the Court.

<a id="ref-10"></a>**[10]** Robbie Pluta. "As Supreme Court pulls
back on gerrymandering, state courts may decide fate of maps."
*Stateline*, December 22, 2025.
<https://stateline.org/2025/12/22/>

<a id="ref-11"></a>**[11]** Nicholas O. Stephanopoulos and Eric M.
McGhee. "Partisan Gerrymandering and the Efficiency Gap."
*University of Chicago Law Review* 82 (2015): 831–900.

<a id="ref-12"></a>**[12]** Samuel S.-H. Wang. "Three Tests for
Practical Evaluation of Partisan Gerrymandering." *Stanford Law
Review* 68 (2016): 1263–1321.

<a id="ref-13"></a>**[13]** Gregory S. Warrington. "Quantifying
Gerrymandering Using the Vote Distribution." *Election Law Journal*
17(1) (2018): 39–57.

<a id="ref-14"></a>**[14]** Gregory Herschlag, Robert Ravier, and
Jonathan C. Mattingly. "Quantifying Gerrymandering in North Carolina."
*Statistics and Public Policy* 7(1) (2020): 30–38.

<a id="ref-15"></a>**[15]** Daryl DeFord, Moon Duchin, and Justin
Solomon. "Recombination: A Family of Markov Chains for Redistricting."
*Harvard Data Science Review* 3(1) (2021).

<a id="ref-16"></a>**[16]** Jowei Chen and Jonathan Rodden.
"Unintentional Gerrymandering: Political Geography and Electoral Bias
in Legislatures." *Quarterly Journal of Political Science* 8(3)
(2013): 239–269.

<a id="ref-17"></a>**[17]** Richard H. Pildes. "The
Constitutionalization of Democratic Politics." *Harvard Law Review*
118 (2004): 28.

<a id="ref-18"></a>**[18]** Bruce E. Cain. *Democracy More or Less:
America's Political Reform Quandary.* Cambridge University Press,
2014.

<a id="ref-19"></a>**[19]** Daniel D. Polsby and Robert D. Popper.
"The Third Criterion: Compactness as a Procedural Safeguard against
Partisan Gerrymandering." *Yale Law & Policy Review* 9 (1991):
301–353.

<a id="ref-20"></a>**[20]** Ernest C. Reock. "A Note: Measuring
Compactness as a Requirement of Legislative Apportionment." *Midwest
Journal of Political Science* 5 (1961): 70–74.

<a id="ref-21"></a>**[21]** William Vickrey. "On the Prevention of
Gerrymandering." *Political Science Quarterly* 76(1) (1961): 105–110.

<a id="ref-22"></a>**[22]** S. W. Hess, J. B. Weaver, H. J. Siegfeldt,
J. N. Whelan, and P. A. Zitlau. "Nonpartisan Political Redistricting
by Computer." *Operations Research* 13(6) (1965): 998–1006.

<a id="ref-23"></a>**[23]** Anuj Mehrotra, Ellis L. Johnson, and
George L. Nemhauser. "An Optimization Based Heuristic for Political
Districting." *Management Science* 44(8) (1998): 1100–1114.

<a id="ref-24"></a>**[24]** Brian Olson. *BDistricting:
Computer-Drawn Congressional and Legislative Districts for All Fifty
U.S. States.* <https://bdistricting.com> (2007–2024).

<a id="ref-25"></a>**[25]** Vincent Cohen-Addad, Philip N. Klein,
and Neal E. Young. "Balanced Centroidal Power Diagrams for
Redistricting." In *Proceedings of the 26th ACM SIGSPATIAL
International Conference on Advances in Geographic Information
Systems* (2018), 389–396. arXiv:1710.03358.

<a id="ref-26"></a>**[26]** Franz Aurenhammer. "Power Diagrams:
Properties, Algorithms and Applications." *SIAM Journal on Computing*
16(1) (1987): 78–96.

<a id="ref-27"></a>**[27]** Harry A. Levin and Sorelle A. Friedler.
"Automated Congressional Redistricting." *ACM Journal of Experimental
Algorithmics* 24 (2019): 1.10:1–1.10:24.

<a id="ref-28"></a>**[28]** Warren D. Smith. "The Shortest Splitline
Algorithm for Political Districting." Center for Range Voting (2007).
<https://rangevoting.org/GerryExamples.html>

<a id="ref-29"></a>**[29]** Iowa Legislative Services Agency.
*Legislative Guide to Redistricting in Iowa.* (2021).
<https://www.legis.iowa.gov/publications/lsa>

<a id="ref-30"></a>**[30]** James Madison. *The Federalist* Nos.
54–58. New York Packet (1788). Library of Congress, Federalist Papers
Primary Documents.

<a id="ref-31"></a>**[31]** Michel L. Balinski and H. Peyton Young.
*Fair Representation: Meeting the Ideal of One Man, One Vote.* 2nd
edition. Brookings Institution Press, 2001.

<a id="ref-32"></a>**[32]** *Reynolds v. Sims*, 377 U.S. 533 (1964).
