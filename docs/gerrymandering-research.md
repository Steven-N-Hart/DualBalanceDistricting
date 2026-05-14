# Deep Research: Gerrymandering Doctrine, Detection, and Deterministic Districting

*Compiled May 12, 2026, as background for the DualBalance Districting manuscript.*

This document is a literature review covering three things: the current state
of U.S. Supreme Court doctrine on race vs. partisanship in districting, the
mathematical tests used to detect gerrymandering (and the paradox that
"fair" maps still impose a normative choice), and deterministic algorithms —
especially those closest to what DualBalance proposes.

A framing correction up front: it is not that the Court "recently struck
down" race-based gerrymandering and approved partisanship. The asymmetry is
older and more interlocking than that, and it sharpened on April 29, 2026
in *Louisiana v. Callais*.

---

## 1. The Current Doctrinal Asymmetry: Race-Restricted, Partisan-Untouchable

### 1.1 Rucho v. Common Cause (2019) — the federal door slammed on partisan claims

The pivotal case is [*Rucho v. Common Cause*, 588 U.S. 684 (2019)](https://www.supremecourt.gov/opinions/18pdf/18-422_9ol1.pdf). In a 5-4 opinion by Chief Justice Roberts, the Court held that **partisan gerrymandering claims present nonjusticiable political questions** beyond the reach of federal courts. Roberts conceded the practice was "incompatible with democratic principles" but said no "judicially discoverable and manageable standard" existed.

Justice Kagan, joined by Ginsburg, Breyer, and Sotomayor, dissented with rare force: *"Of all times to abandon the Court's duty to declare the law, this was not the one. The practices challenged in these cases imperil our system of government."* She specifically rejected the manageability rationale, pointing out that lower courts had already coalesced around tests — the efficiency gap, mean-median difference, partisan symmetry, MCMC outlier analysis — that produced consistent answers. ([Wikipedia: Rucho v. Common Cause](https://en.wikipedia.org/wiki/Rucho_v._Common_Cause); [Harvard L. Rev. Comment](https://harvardlawreview.org/wp-content/uploads/2019/11/252-261_Online.pdf))

The doctrinal effect: **federal courts cannot review partisan gerrymandering.** This is not a holding that partisanship is *permitted*; it is a holding that the federal judiciary won't intervene. State constitutions and state courts remain free to act, as does Congress (which has not).

### 1.2 Race: still constrained, but the bar keeps moving

Race-conscious districting operates under two overlapping legal regimes: the Fourteenth and Fifteenth Amendments (forbidding intentional racial discrimination, with strict scrutiny applied to maps where race "predominates" — *Shaw v. Reno*, 1993) and Section 2 of the Voting Rights Act (forbidding maps that dilute minority voting strength under the *Thornburg v. Gingles* three-factor framework). These regimes can conflict: a map drawn to remedy §2 vote dilution may be challenged under *Shaw* as a racial gerrymander.

Three cases since 2023 have reshaped this terrain:

**[*Allen v. Milligan*, 599 U.S. 1 (2023)](https://www.supremecourt.gov/opinions/22pdf/21-1086_1co6.pdf)** — surprisingly, Roberts and Kavanaugh joined the liberals to *uphold* §2 of the VRA and require Alabama to draw a second majority-Black congressional district. The Court reaffirmed the *Gingles* preconditions and rejected Alabama's "race-neutral benchmark" argument that would have used MCMC ensembles as a defense (Alabama argued its map looked typical of computer-generated neutral plans, so it couldn't be discriminatory). Plaintiffs' computational evidence — that a second majority-Black district was readily achievable through neutral redistricting — was central. ([CRS analysis](https://www.congress.gov/crs-product/LSB11002))

**[*Alexander v. South Carolina State Conference of the NAACP*, 602 U.S. 1 (2024)](https://www.supremecourt.gov/opinions/23pdf/22-807_3e04.pdf)** — went the other way. The Court 6-3 reversed a district-court finding that South Carolina's CD-1 was a racial gerrymander. Justice Alito's majority opinion erected a steep new evidentiary wall: a plaintiff alleging racial gerrymandering must **"disentangle race from politics"** and **must produce an alternative map showing a less race-driven plan that performs the State's legitimate goals**. The presumption of legislative good faith was emphasized. ([Harvard L. Rev.](https://harvardlawreview.org/print/vol-138/alexander-v-south-carolina-state-conference-of-the-naacp/); [LWV explainer](https://www.lwv.org/blog/how-supreme-court-made-racial-gerrymandering-easier-alexander-v-south-carolina-naacp))

**[*Louisiana v. Callais*, 608 U.S. ___ (April 29, 2026)](https://www.supremecourt.gov/opinions/25pdf/24-109_21o3.pdf)** — decided two weeks ago. In a 6-3 opinion by Alito (joined by Roberts, Thomas, Gorsuch, Kavanaugh, Barrett), the Court held Louisiana's SB8 congressional map — drawn explicitly to comply with a prior order to create a second majority-Black district — was itself an *unconstitutional racial gerrymander*. The majority found that the VRA did not actually compel a second majority-minority district under the *Gingles* facts and so there was no compelling interest to justify race-predominant line-drawing. The Court also held that **a plaintiff's illustrative maps must satisfy all of the state's legitimate districting goals without using race as a predominant factor**, and that **evidence of racially polarized voting must be disentangled from partisan affiliation**. ([SCOTUSblog coverage](https://www.scotusblog.com/2026/04/in-major-voting-rights-act-case-supreme-court-strikes-down-redistricting-map-challenged-as-racia/); [Brennan Center](https://www.brennancenter.org/our-work/research-reports/louisiana-v-callais))

The combined effect of *Alexander* + *Callais* is a **race-conscious-districting trap**: a state that draws a majority-minority district to comply with §2 is now likely to face a *Shaw* counter-suit, and the burden of justifying race as predominant has been ratcheted up. Section 2 was not formally struck down, but, as SCOTUSblog put it, "the ruling significantly limits how Section 2 can be used in practice."

### 1.3 The race/party entanglement

This is the doctrinal crack at the heart of the asymmetry. Because Black voters in the U.S. vote roughly 90% Democratic, and because residential segregation correlates race with geography, **race and party are statistically entangled**. After *Rucho*, partisan gerrymandering is unreviewable federally; after *Alexander*/*Callais*, racial gerrymandering requires plaintiffs to *disentangle* race from party — to prove race rather than partisanship was the predominant motive. As Richard Hasen put it in his foundational [*William & Mary Law Review* article](https://wmlawreview.org/sites/default/files/Hasen.pdf): "Race or Party, Race as Party, or Party All the Time?" — a mapmaker can openly say "we packed Democrats" and immunize themselves; a mapmaker who packs Black voters under that same theory and produces the same map gets the same protection. The [Columbia Law Review](https://columbialawreview.org/content/racial-gerrymandering-after-rucho-v-common-cause-untangling-race-and-party/) and [Southern California Law Review](https://southerncalifornialawreview.com/2023/04/24/race-and-politics-the-problem-of-entanglement-in-gerrymandering-cases/) have run lengthy treatments of this problem.

This is the structural reason DualBalance's design choice — *don't read race, don't read party* — is doctrinally tidy: it sidesteps the entanglement entirely by refusing to consider either input.

### 1.4 Moore v. Harper and the state-law channel

[*Moore v. Harper*, 600 U.S. 1 (2023)](https://www.supremecourt.gov/opinions/22pdf/21-1271_3f14.pdf) (6-3, Roberts) rejected the "independent state legislature" theory and confirmed that state courts may review congressional maps under state constitutions. After *Rucho*, this is the only judicial channel for partisan gerrymandering claims. ([Brennan Center explainer](https://www.brennancenter.org/our-work/research-reports/moore-v-harper-explained))

State supreme courts have used it actively. The Pennsylvania Supreme Court in [*League of Women Voters v. Commonwealth*, 178 A.3d 737 (Pa. 2018)](https://www.lwv.org/legal-center/moore-v-harper) struck down PA's congressional map under the state Free and Equal Elections Clause. New York's Court of Appeals struck down its 2022 maps; in January 2026 a state judge ordered the commission to redraw CD-11 for diluting Black/Latino voting power. Ohio's Supreme Court repeatedly struck down state legislative and congressional maps; as of February 2026 a new map is in place. North Carolina swung the opposite way — its supreme court struck down maps under the state constitution, then reversed itself in *Harper v. Hall II* after a partisan composition change, and a federal three-judge panel in late 2025 allowed a redrawn map intended to flip a seat. ([Stateline summary](https://stateline.org/2025/12/22/as-supreme-court-pulls-back-on-gerrymandering-state-courts-may-decide-fate-of-maps/); [State Court Report](https://statecourtreport.org/our-work/analysis-opinion/status-partisan-gerrymandering-litigation-state-courts-mid-year-roundup))

The current snapshot ([Democracy Docket live tracker](https://www.democracydocket.com/analysis/live-redistricting-tracker/), [Ballotpedia NY](https://ballotpedia.org/Redistricting_in_New_York_ahead_of_the_2026_elections)): a mid-decade re-gerrymandering arms race is underway, with state-level partisan gerrymandering reviewable in roughly ten state supreme courts that have so held, and unreviewable in the rest.

---

## 2. Tests for Gerrymandering — and the Bias of "Bias Detection"

Every gerrymandering test embeds a normative claim about what the right baseline looks like. This is the central paradox: maps that try to *eliminate* bias necessarily *impose* bias by adopting one fairness theory over its competitors. Below are the principal tests, what each encodes, and where each fails.

### 2.1 Efficiency Gap (Stephanopoulos & McGhee, 2014)

A "wasted vote" is any vote cast for a loser, or any vote for a winner above the 50%+1 threshold. The Efficiency Gap is the difference in wasted votes between parties, divided by total votes. Under uniform turnout it reduces to **EG ≈ (Seat margin − 50%) − 2(Vote margin − 50%)**. ([Brennan Center primer](https://www.brennancenter.org/sites/default/files/legal-work/How_the_Efficiency_Gap_Standard_Works.pdf); [U. Chi. L. Rev. 82:831 (2015)](https://chicagounbound.uchicago.edu/cgi/viewcontent.cgi?article=1946&context=public_law_and_legal_theory))

Stephanopoulos and McGhee proposed 8% (legislative) and 2 seats (congressional) as presumptive unconstitutionality thresholds. The metric was central to [*Whitford v. Gill*](https://en.wikipedia.org/wiki/Efficiency_gap) (W.D. Wis. 2016), where Wisconsin's Assembly map showed EG of 11.7-13% against Democrats. SCOTUS vacated on standing grounds (2018) and effectively rejected the test in *Rucho*.

**Embedded normative claim:** that the right benchmark is roughly 2:1 seats-to-votes responsiveness around 50%. EG = 0 only under specific seats-votes relationships that are mathematically close to proportional representation. Yale Law's [Veasey et al. critique](https://law.yale.edu/sites/default/files/area/center/liman/document/ssrn-id3019540.pdf) shows EG can label as "fair" maps that are extremely uncompetitive, and label as "unfair" maps that comply with the VRA (because the VRA *requires* packing minority voters into majority-minority districts — exactly what EG penalizes).

### 2.2 Mean-Median Difference (Wang, McDonald, Best)

For one party's vote share across districts, **MM = median − mean**. If the typical district is systematically more Republican than the statewide average, that's a fingerprint of a tilt at the seat-determining margin. ([Wang, 68 Stan. L. Rev. 1263 (2016)](https://www.stanfordlawreview.org/print/article/three-tests-for-practical-evaluation-of-partisan-gerrymandering/); McDonald & Best, *Election Law J.* 14, 2015.)

**Embedded normative claim:** symmetric district-share distributions are the neutral case. The metric loses meaning when the statewide vote is far from 50% and is confounded by political geography (see §2.7).

### 2.3 Partisan Symmetry / Seats-Votes Curve (Gelman, King, Grofman)

A map is symmetric if **S(V) + S(1−V) = 1** — if the parties swapped vote shares, they would swap seat shares. Summary statistics include partisan bias β = S(0.5) − 0.5 and responsiveness ρ = dS/dV at V = 0.5. (Gelman & King, [JASA 85 (1990)](https://gking.harvard.edu/publications) and AJPS 38 (1994).)

Justice Stevens endorsed symmetry in his *LULAC v. Perry* (2006) concurrence. Justice Kennedy declined to adopt it as the standard. **Embedded normative claim:** procedural fairness = identical treatment under counterfactual vote-swapping. Requires a swing model (typically uniform partisan swing, which is empirically suspect).

### 2.4 Declination (Warrington, 2018)

Order districts by one party's vote share, plot them, find the centroid of won districts and lost districts, and measure the angle of the kink as the curve crosses 50%. Symmetric maps produce a smooth crossing; gerrymanders produce a sharp asymmetric kink (many narrow wins for the gerrymanderer, few overwhelming wins; the opposite for the victim). ([Warrington, *ELJ* 17:1 (2018)](https://www.liebertpub.com/doi/10.1089/elj.2019.0562); [arXiv:1803.04799](https://ar5iv.labs.arxiv.org/html/1803.04799); [PlanScore](https://planscore.org/metrics/declination/))

**Strength:** doesn't depend on district shape, easy to compute, "provably related to packing and cracking" per Warrington. **Weakness:** undefined when one party wins all or none of the districts, less developed normatively than EG.

### 2.5 MCMC Ensemble / Outlier Analysis (Duke, MGGG, Princeton)

The modern dominant approach. Generate thousands of districting plans satisfying the state's legal constraints (equal population, contiguity, compactness, VRA compliance), score the enacted plan on a metric of interest, and ask: is the enacted plan an outlier? An enacted map producing, say, 10R-3D when 95% of neutral plans on the same geography produce 8R-5D or 7R-6D is statistical evidence of intent. ([MGGG samplers](https://mggg.org/samplers); [GerryChain](https://github.com/mggg/GerryChain); [Duke report](https://mggg.org/uploads/md-report.pdf))

The two major research groups:

- **Duke Quantifying Gerrymandering Group** (Mattingly, Herschlag, Bangia, Ravier). Metropolis-Hastings on precinct graphs. Their NC analysis showed the 2016 10R-3D outcome was beyond the 99th percentile of neutral plans — central in *Common Cause v. Lewis* (NC state, 2019) and *Harper v. Hall*.
- **MGGG Redistricting Lab** (Duchin, DeFord, Solomon, Tufts → now a broader consortium). Developed **ReCom (Recombination)**: merge two adjacent districts, draw a spanning tree on the merged region, cut a balanced edge to re-split. ReCom mixes far faster than flip-step chains and produces more compact plans by construction. Released as the open-source **GerryChain** Python library. [DeFord-Duchin-Solomon, "Recombination," *Harvard Data Science Review* (2021)](https://hdsr.mitpress.mit.edu/pub/1ds8ptxu).

Used or cited in *LWV v. Commonwealth* (PA 2018), *Common Cause v. Lewis* (NC 2019), *Harper v. Hall* (NC 2022), *Ohio LWV* (2022), and as plaintiff evidence in *Allen v. Milligan* (2023).

**Embedded normative claim:** the right baseline is "this state's actual political geography filtered through legally codified neutral constraints." But *which* constraints? Compactness weights, county-split tolerances, and VRA encodings each select a different neutral. The constraint-choice problem is the soft underbelly of ensemble methods. The mixing-time critique — Chikina, Frieze & Pegden, *PNAS* 114 (2017) — argues that ensembles may not represent the full target distribution; Pegden, Procaccia & Yu (2017) developed a local-search alternative that tests a slightly different hypothesis.

### 2.6 Compactness Metrics

District-level shape measures:

- **Polsby-Popper:** PP = 4πA / P² (1 for a circle). [Polsby & Popper, *Yale L. & Pol'y Rev.* 9:301 (1991)](https://cran.r-project.org/web/packages/redistmetrics/vignettes/compactness.html)
- **Reock:** A / A_MBC (area / minimum bounding circle area). Reock, *MJPS* (1961).
- **Schwartzberg:** P / (2√(πA)) — the inverse-square-root variant.
- **Convex Hull:** A_D / A_hull(D).
- **Population polygon (Hofeller):** population inside district / population inside convex hull.

[King's "How to Measure Compactness If You Only Have a Computer"](https://gking.harvard.edu/files/gking/files/compact.pdf) and the [AMS Feature Column](https://www.ams.org/publicoutreach/feature-column/fc-2014-08) discuss the proliferation. **The metrics correlate weakly with each other** (Reock-Polsby-Popper correlation around 0.70 — [compactness vignette](https://cran.r-project.org/web/packages/redistmetrics/vignettes/compactness.html)). None penalizes pack-and-crack done with compact districts (you can gerrymander demographically without ugly shapes — Barnes & Solomon, *Pol. Analysis* 2021). All penalize states with irregular coastlines for reasons unrelated to intent. None is adversarial-robust.

### 2.7 The political-geography confound (Chen & Rodden 2013)

Worth its own subsection because it complicates every test above. [Chen & Rodden, "Unintentional Gerrymandering," *QJPS* 8:239 (2013)](https://web.stanford.edu/~jrodden/wp/florida.pdf) showed via automated simulations that in many states, Democrats are so densely clustered in cities that **even neutral, automated maps produce systematic seat bias against Democrats**. A non-zero EG, MM, or declination may reflect geography, not intent. This is why ensemble methods — which condition on the actual geography — became dominant: they answer "is this map's bias greater than the bias of a neutral map *on this geography*?" rather than "is this map biased relative to an abstract baseline?"

### 2.8 The normative paradox summarized

Every test embeds a fairness theory:

| Test | Implicit baseline |
|------|-------------------|
| Efficiency Gap | Proportional-adjacent (2:1 responsiveness) |
| Partisan symmetry | Procedural mirror-symmetry under vote swap |
| Mean-median | Symmetric district-share distribution |
| Declination | Symmetric kink at 50% |
| MCMC outlier | Distribution of constraint-satisfying plans |
| Compactness | Geometric regularity is itself a virtue |
| Gingles / BVAP | Minority representation is a constitutional good |

Richard Pildes ("[The Constitutionalization of Democratic Politics](https://harvardlawreview.org/print/vol-137/moore-v-harper/)," *Harv. L. Rev.* 2004) has long argued there is no neutral baseline. Bruce Cain (*Democracy More or Less*, 2014) argues districting trades off incommensurable goods — representation, competitiveness, minority protection, communities of interest, geographic coherence — and any scalar metric collapses the tradeoff. Moon Duchin has put it bluntly in public talks: "compactness is not a metric, it's a family of metrics, and the choice is political."

Kagan's *Rucho* dissent answered this paradox with an outlier-of-outliers argument: even if no single fairness number is neutral, *extreme* asymmetry shows up under *all* reasonable baselines, and that's enough for courts to act. Roberts' majority disagreed.

**What this means for DualBalance.** A scoring harness that reports population error, area error, compactness, *and* (optionally) efficiency gap or partisan metrics is not "neutral" — it is operationalizing the claim that population balance + geographic-area parity + shape regularity are the legitimate criteria. That is itself a normative choice. The honest move (which the README already makes, ll. 207-213, 229-238) is to label the baseline explicitly rather than claim universal fairness.

---

## 3. Deterministic Districting Algorithms — From Founders to Present

### 3.1 The founders on apportionment and representation

Article I, § 2 fixed population as the basis for House apportionment ("the actual Enumeration"). Madison defended this in [*Federalist No. 54*](https://guides.loc.gov/federalist-papers/text-51-60) and No. 55-57: "the right of choosing this allotted number in each State is to be exercised by such part of the inhabitants as the State itself may designate." The structural balance in the Constitution — proportional House, equal-state-vote Senate — was the design compromise. **DualBalance's README explicitly invokes this balance** (lines 27-33) and extends it within a single chamber by requiring equal population *and* equal area per district.

The mechanics of *apportionment* (seats per state, before any line-drawing) became the first political-arithmetic crisis. Washington's first veto in 1792 rejected Hamilton's largest-remainder method in favor of Jefferson's greatest-divisor method. The current **Method of Equal Proportions / Huntington-Hill** — priority(s,n) = pop(s) / √(n(n+1)) — was adopted in 1941 and is DualBalance's default. ([U.S. Census methods](https://www.census.gov/about/history/historical-censuses-and-surveys/census-programs-surveys/decennial-census/methods.html); [AMS feature column on apportionment history](https://www.ams.org/publicoutreach/feature-column/fcarc-apportion2)) Huntington-Hill minimizes the relative difference in constituents-per-representative between any two states.

### 3.2 Vickrey (1961) — the founding paper for algorithmic redistricting

[William Vickrey, "On the Prevention of Gerrymandering," *Pol. Sci. Q.* 76:105 (March 1961)](https://www.psqonline.org/article.cfm?IDArticle=7310) — Nobel laureate in economics, here writing on redistricting — proposed that line-drawing be done by "an automated and impersonal procedure." His sketch: rules for contiguity, compactness, and population equality, mechanically applied. The paper is short, six pages, and is the intellectual ancestor of every algorithmic-redistricting proposal since.

### 3.3 Hess et al. (1965) — operations research enters

[Hess, Weaver, Siegfeldt, Whelan, Zitlau, "Nonpartisan Political Redistricting by Computer," *Operations Research* 13:998 (1965)](https://pubsonline.informs.org/doi/abs/10.1287/opre.13.6.998) — the canonical OR formulation. They cast districting as a **transportation problem**: minimize the population moment of inertia (sum of squared distances from each person to their district center) subject to equal population at each center, then iterate by recomputing centroids. The four-step algorithm — guess centers, solve transportation LP, repair to whole-unit assignment, recompute centroids — is structurally identical to Lloyd's algorithm with capacity constraints. **Federal courts received Hess-style computer plans for use in Delaware and were offered them for Connecticut.** This is the direct ancestor of DualBalance's iteration.

### 3.4 Shortest Splitline (Warren Smith, c. 2005-2007)

[rangevoting.org/GerryExamples.html](https://rangevoting.org/GerryExamples.html), [rangevoting.org/Splitlining.html](https://rangevoting.org/Splitlining.html). Recursively divide the state into A:B equipopulous halves with the **shortest straight line** that achieves the population ratio, where N = A + B, A = ⌊N/2⌋, B = ⌈N/2⌉. Use spherical distance; tie-break with closeness to north-south orientation. Pure-deterministic, unique output for a given state and N. Produces straight-edged, geometrically regular districts.

**Strengths:** Provably unique, fully deterministic, content-blind. **Weaknesses:** ignores natural boundaries (rivers, mountain ridges), county lines, communities of interest; produces districts that cut through cities and ignore the actual urban-rural fabric. Has never been formally adopted.

### 3.5 Brian Olson / BDistricting (c. 2006-present)

[bdistricting.com](https://bdistricting.com/about.html) — a one-man operation that is arguably the closest publicly-available precedent for DualBalance. Olson minimizes **sum of person-to-district-center distances** using a k-means-style iterative solver that respects census-block atomicity. He has published computer-generated maps for **all 50 states** at his site, updated each census cycle, and the project has been profiled by the [Washington Post](https://www.washingtonpost.com/news/wonk/wp/2014/06/03/this-computer-programmer-solved-gerrymandering-in-his-spare-time/), [Priceonomics](https://priceonomics.com/algorithm-the-unfairness-of-gerrymandering/), and [FiveThirtyEight's Atlas of Redistricting](https://fivethirtyeight.com/features/we-drew-2568-congressional-districts-by-hand-heres-how/). Olson's objective: "If there were exactly one voting-place in each district, and if each one were optimally located, and if each inhabitant traveled there by personal helicopter to vote, and if all helicopters had identical performance, then the best district map would be the one minimizing the total travel expense."

**This is the prior art closest to DualBalance** — but with one critical difference. Olson optimizes population balance + compactness (via distance-to-center). He does **not** optimize equal land area.

### 3.6 Capacitated Voronoi / Balanced Power Diagrams (Cohen-Addad et al., 2017-2018)

[Cohen-Addad, Klein, Young, "Balanced Power Diagrams for Redistricting," ACM SIGSPATIAL 2018 (arXiv:1710.03358)](https://arxiv.org/pdf/1710.03358); [Cohen-Addad et al., "Balanced Centroidal Power Diagrams for Redistricting," ACM (2018)](https://dl.acm.org/doi/10.1145/3274895.3274979). A **power diagram** is a generalization of a Voronoi diagram where each seed gets an additive weight (Aurenhammer, "Power diagrams: properties, algorithms and applications," *SIAM J. Comput.* 16:78, 1987). By solving for the weights, you can produce a **capacitated** power diagram where every cell has equal population — districts whose populations differ by at most one person. The algorithm uses a capacitated variant of Lloyd's method.

**Strengths:** mathematically clean, population-balanced by construction, compact by construction (power-diagram cells are convex). **Weakness for our purposes:** it balances *one* quantity (population). It does not simultaneously balance area.

Related work: [Levin & Friedler, "Automated Congressional Redistricting" (2019)](https://scholarship.tricolib.brynmawr.edu/handle/10066/14074) on capacitated k-center variants; [Bourne & Roper on centroidal power diagrams](https://arxiv.org/pdf/1409.2786); [DROPS-LIPIcs on FORC 2021 paper on tractability](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.FORC.2021.3) of the geographic clustering problem.

### 3.7 Lloyd's algorithm / Centroidal Voronoi Tessellations

[Du, Faber, Gunzburger, "Centroidal Voronoi Tessellations: Applications and Algorithms," *SIAM Review* 41:637 (1999)](https://epubs.siam.org/doi/10.1137/040617364) is the canonical theoretical reference. A CVT is a Voronoi tessellation where each generator coincides with its cell's centroid. Lloyd's algorithm (1957/1982) converges to a CVT. Population-weighted CVTs (weighted by demographic density) balance the *integral of density* over each cell — i.e., they balance population, not area.

This is DualBalance's iteration step (README ll. 60-69, Formalism §3): "Recalculate each seed: move it to the population-weighted centroid of its assigned blocks. Repeat until stable." This is a population-weighted Lloyd iteration.

### 3.8 Other named approaches

- **Iowa LSA criteria-based** — not an algorithm; a rules-based process where the Legislative Services Agency draws maps using strict lexicographic priority: population equality (±1% congressional, ±5% legislative) → contiguity → preservation of political subdivisions (counties, then cities) → compactness (length-width ratio + perimeter sum) → no consideration of incumbents, party, or election results. Iowa's been the gold standard for criteria-driven (vs. algorithm-driven) reform since 1980. The legislature has accepted the first or second LSA proposal each cycle.
- **Garfinkel & Nemhauser (1970)** — set partitioning formulation; enumerate feasible districts, choose N that partition the state.
- **Mehrotra, Johnson, Nemhauser (1998)** — column-generation IP for districting; exact at moderate scales but doesn't reach census-block resolution.
- **Fryer & Holden (2011)** — relative-proximity index with existence proofs.
- **Chen & Rodden** simulations — stochastic, not deterministic; ancestor of MCMC ensembles.
- **Genetic algorithms** (e.g., Bação et al.) — stochastic.
- **Autoredistrict.org** (Kevin Baas), **DistrictBuilder** (Azavea/PPL), **Districtr** (MGGG), **Maptitude for Redistricting** (Caliper) — interactive tools, not autonomous algorithms.

A 2019 survey, [Becker & Solomon, "Redistricting Algorithms" in *Political Geometry* (Birkhäuser/Springer)](https://link.springer.com/article/10.1007/s42001-019-00053-9), is a good overview.

---

## 4. How DualBalance Sits in This Landscape

DualBalance, distilled:

1. Apportion seats by Method of Equal Proportions (1941 standard).
2. Within each state, pick N seeds deterministically (population-weighted cluster centroids or farthest-point sampling).
3. Assign each census block by minimizing α·distance + β·|running pop − P*|/P* + γ·|running area − A*|/A*, with **β = γ**.
4. Iterate Lloyd-style with population-weighted centroid updates.
5. Repair contiguity.
6. Deterministic tie-break cascade.

The DualBalance Score = 1 / (1 + 0.5·pop_err + 0.5·area_err) is symmetric in population and area errors (β = γ = ½).

### 4.1 What is *not* novel

The Lloyd-iteration core (steps 2-4 without the area term) is essentially **Hess et al. (1965)** with modern compute. Olson's BDistricting does this with population-only balancing. Cohen-Addad's balanced power diagrams do this with exact population balance. The Method of Equal Proportions is the law of the land since 1941. Deterministic tie-breaking with a fixed cascade is standard in the OR literature.

### 4.2 What may be novel — the dual pop/area objective

The most distinctive feature is the **equal-weighting of population error and land-area error (β = γ)**. The motivating analogy in the README — "the House → population-based; the Senate → geography-based; DualBalance applies that philosophy within a single districting system" (ll. 27-33) — appears in this exact form in no algorithmic-redistricting paper located in this review.

Searches for the conjunction of "equal area" and "equal population" as co-objectives in districting turn up:

- **Compactness-as-area** uses: Polsby-Popper and Reock contain area in the denominator/numerator of *shape* metrics, but no one balances area *across* districts as a constraint.
- **Rural representation** proposals: there are political-theory pieces ([CRS](https://www.congress.gov/crs-product/IN11618), [Wikipedia Gerrymandering](https://en.wikipedia.org/wiki/Gerrymandering)) about whether rural areas are under-represented, but no algorithmic operationalization as area-balance constraint.
- **Geographic apportionment** ideas: there's a fringe literature (rangevoting.org, occasional law review notes) arguing for geographic-weighted apportionment *between states*, but not as an intra-state districting objective.

A caveat: an obscure law-review note or a non-English political science paper may have proposed exactly this objective and not surfaced in this search. But it's not in the mainstream computational-redistricting or districting-law canon. **The dual objective is the contribution to claim** — the Lloyd iteration is engineering, the apportionment is policy, but β = γ is the new normative move.

### 4.3 What this commits the design to (the normative claim)

By weighting area equal to population, the algorithm produces districts where a citizen of a rural, low-density block has roughly the same *district-population fraction* as a citizen of a dense urban block, but the rural citizen's district covers a much larger area — because the algorithm is penalized for letting the rural district grow too large. The practical effect: **rural districts shrink (in area) relative to a population-only baseline, and urban districts grow (in area)**. Counterintuitive on first read, but follows directly from forcing area equality: if each district has A* = A/N, then rural areas (low density) cannot stretch to absorb population without exceeding A*, so the algorithm has to add more districts to rural areas than population alone would justify — *over-representing* low-density geography in seat counts.

This is the opposite of Chen & Rodden's "unintentional gerrymandering": where pure population-balance under residential clustering systematically disadvantages urban-clustered Democrats, equal-area pulls in the opposite direction by giving more representational density to the geographically dispersed. Whether that's a feature or a bug depends entirely on whether one accepts the founders'-balance framing.

It also has constitutional friction. *Reynolds v. Sims*, 377 U.S. 533 (1964) and *Wesberry v. Sanders*, 376 U.S. 1 (1964) established **one-person-one-vote** for state and federal legislative districts, requiring near-perfect population equality between districts. Area equality plus strict population equality may be in tension: if rural blocks are sparse, the algorithm may have to choose between exceeding A* and exceeding the 0.5%-2% population tolerance courts apply. The Formalism (§3) treats them as a soft trade-off via the α/β coefficients, which is mathematically clean but may produce maps that fail strict-scrutiny population equality if β = γ is enforced too strongly. Worth thinking through which constraint hard-binds.

### 4.4 The closest algorithmic comparators, in rank order

| Rank | Method | Match on (a) determinism, (b) Lloyd-style iteration, (c) population balance, (d) area balance |
|------|--------|----|
| 1 | **Olson / BDistricting** | ✓, ✓, ✓ (soft), ✗ |
| 2 | **Hess et al. 1965** | ✓, ✓ (transport-LP), ✓, ✗ |
| 3 | **Cohen-Addad balanced power diagrams** | ✓ (modulo tie-break), ✓, ✓ (hard), ✗ |
| 4 | **Centroidal Voronoi Tessellation (Du-Faber-Gunzburger)** | ✓, ✓, depends on weighting, ✗ |
| 5 | **Shortest Splitline (Smith)** | ✓, ✗, ✓, ✗ |
| 6 | **Vickrey 1961** | ✓ (sketch), —, ✓, ✗ |
| 7 | **Iowa LSA criteria** | semi (humans interpret rules), ✗, ✓ (strict), ✗ |

None of the top six prior-art methods carries the dual area+population objective.

The honest description of DualBalance: **"Olson's BDistricting with a co-equal land-area term, Hess's transportation-problem heritage in the iteration, Method-of-Equal-Proportions at the apportionment layer, Federalist-Papers framing for the dual objective."** That sentence is unflattering as a marketing pitch but accurate as a positioning statement, and it makes the contribution defensible.

### 4.5 Recommendations for the implementation (and the manuscript)

Three things worth surfacing into the manuscript and the code, given the literature:

1. **State the normative claim explicitly.** The README does this on lines 229-238 (the fairness-philosophy section). The manuscript should foreground the Senate-analog framing as the *defining* normative move, cite *Federalist 54-58* for the precedent, and engage Chen & Rodden directly: their "political geography produces unintentional bias" finding is the empirical setup that the dual objective responds to.

2. **In the scoring harness, report against an ensemble.** Pure point estimates (DualBalance Score, EG, MM) are weak evidence in litigation. An MCMC ensemble (built via GerryChain on the same state, same constraints) gives a distribution against which DualBalance maps and enacted maps can both be located. This is the modern litigation standard ([MGGG samplers](https://mggg.org/samplers); used in *Allen v. Milligan*). The current scoring section (README ll. 132-218) is benchmark-and-rank against named plans; adding ensemble percentiles would strengthen the comparison.

3. **One-person-one-vote vs. equal-area tension.** Either declare population equality a hard constraint (and area equality a soft objective subject to that), or be explicit that maps may exceed *Reynolds*-style tolerances. The current formalism (§3-4) treats both as soft via β = γ; the README (§"Limitations," ll. 246-250) acknowledges the tension. A hierarchical formulation — hard pop equality within tolerance ε, then minimize area error — would be more defensible legally without giving up the philosophical content. Worth deciding before the code matures.

### 4.6 What the doctrine says about the design

Returning to §1: the algorithm reads no race data and no party data. After *Alexander* (2024) and *Callais* (April 2026), this is no longer just a philosophical position — it is the safest defensive posture available to a mapmaker. A map drawn without race or partisanship as inputs (a) cannot be a racial gerrymander under *Shaw*/*Alexander*/*Callais* because race did not predominate; (b) cannot be a partisan gerrymander under federal law because *Rucho* makes that nonjusticiable; (c) is reviewable under state constitutions, but most state-court partisan-gerrymandering tests rely on outcome metrics (EG, MM, ensemble outliers) that a geography-only algorithm should pass routinely unless the state's underlying political geography is already lopsided (Chen & Rodden territory).

The one residual risk: the *Allen v. Milligan* §2 obligation. A state using DualBalance still has an affirmative duty under §2 of the VRA to draw majority-minority districts where the *Gingles* preconditions are met. A purely geography-driven map will not automatically satisfy §2 in states like Alabama, Louisiana, South Carolina, or Texas; the post-*Callais* terrain makes this harder, but the obligation has not been eliminated. The clean architectural answer: keep the generator race-blind, but allow the scoring harness to flag §2 risk (Gingles-style compactness of minority population, BVAP per district) so that operators can know whether a §2 challenge would require manual adjustment or a constrained re-run. The scoring section already separates generator from harness (README ll. 207-218); this is the right place to put it.

---

## Summary

The doctrinal situation as of May 12, 2026: *Rucho* (2019) makes partisan gerrymandering federally unreviewable; *Allen v. Milligan* (2023) preserved §2 of the VRA; *Alexander* (2024) and *Louisiana v. Callais* (April 29, 2026) make racial-gerrymandering plaintiffs prove race-not-party predominance through illustrative maps that satisfy all other state goals, which significantly limits §2 in practice. State constitutional review under *Moore v. Harper* (2023) is the only judicial channel for partisan claims and is active in PA, NY, OH, NC, and elsewhere.

The mathematical tests — efficiency gap, mean-median, partisan symmetry, declination, MCMC ensembles, compactness measures, Gingles — each embed a contested normative baseline; "bias detection" is unavoidably "bias-with-respect-to-a-chosen-baseline." Ensembles are the current state of the art because they use this-state's-geography-under-neutral-constraints as the baseline rather than an abstract ideal, but the constraint choice is itself political.

The deterministic-algorithm lineage runs Vickrey (1961) → Hess et al. (1965) → Olson's BDistricting → Cohen-Addad's balanced power diagrams, with shortest-splitline as a parallel branch. DualBalance fits squarely in this tradition. The Lloyd iteration and population balancing are inherited; the **dual area-plus-population objective with β = γ, motivated by the Federalist House/Senate balance, is the apparently-novel contribution** — though it commits the design to a specific (and contestable) normative claim about geographic representation that may have constitutional friction with strict *Reynolds v. Sims* population-equality jurisprudence. The race-and-party blindness is doctrinally well-placed in the post-*Callais* environment, with the residual concern being §2 of the VRA, which the scoring harness can flag without compromising the generator's content-neutrality.

## Sources

### SCOTUS and case law
- [Rucho v. Common Cause, 588 U.S. 684 (2019) — full opinion](https://www.supremecourt.gov/opinions/18pdf/18-422_9ol1.pdf)
- [Rucho v. Common Cause — Wikipedia](https://en.wikipedia.org/wiki/Rucho_v._Common_Cause)
- [Rucho — Harvard Law Review comment](https://harvardlawreview.org/wp-content/uploads/2019/11/252-261_Online.pdf)
- [Allen v. Milligan, 599 U.S. 1 (2023) — full opinion](https://www.supremecourt.gov/opinions/22pdf/21-1086_1co6.pdf)
- [Allen v. Milligan — Wikipedia](https://en.wikipedia.org/wiki/Allen_v._Milligan)
- [Allen v. Milligan — CRS analysis](https://www.congress.gov/crs-product/LSB11002)
- [Alexander v. South Carolina NAACP, 602 U.S. 1 (2024) — full opinion](https://www.supremecourt.gov/opinions/23pdf/22-807_3e04.pdf)
- [Alexander — Harvard Law Review](https://harvardlawreview.org/print/vol-138/alexander-v-south-carolina-state-conference-of-the-naacp/)
- [Alexander — League of Women Voters explainer](https://www.lwv.org/blog/how-supreme-court-made-racial-gerrymandering-easier-alexander-v-south-carolina-naacp)
- [Louisiana v. Callais, 608 U.S. ___ (April 29, 2026) — full opinion](https://www.supremecourt.gov/opinions/25pdf/24-109_21o3.pdf)
- [Louisiana v. Callais — SCOTUSblog coverage](https://www.scotusblog.com/2026/04/in-major-voting-rights-act-case-supreme-court-strikes-down-redistricting-map-challenged-as-racia/)
- [Louisiana v. Callais — Brennan Center](https://www.brennancenter.org/our-work/research-reports/louisiana-v-callais)
- [Moore v. Harper, 600 U.S. 1 (2023) — full opinion](https://www.supremecourt.gov/opinions/22pdf/21-1271_3f14.pdf)
- [Moore v. Harper — Brennan Center explainer](https://www.brennancenter.org/our-work/research-reports/moore-v-harper-explained)

### State-level partisan gerrymandering
- [Stateline: State courts may decide fate of maps (Dec 2025)](https://stateline.org/2025/12/22/as-supreme-court-pulls-back-on-gerrymandering-state-courts-may-decide-fate-of-maps/)
- [2025–2026 U.S. redistricting — Wikipedia](https://en.wikipedia.org/wiki/2025%E2%80%932026_United_States_redistricting)
- [Democracy Docket live redistricting tracker](https://www.democracydocket.com/analysis/live-redistricting-tracker/)
- [State Court Report: Partisan gerrymandering litigation roundup](https://statecourtreport.org/our-work/analysis-opinion/status-partisan-gerrymandering-litigation-state-courts-mid-year-roundup)
- [Ballotpedia: Redistricting in New York ahead of 2026](https://ballotpedia.org/Redistricting_in_New_York_ahead_of_the_2026_elections)

### Race-party entanglement
- [Hasen, "Race or Party, Race as Party, or Party All the Time?" — William & Mary L. Rev.](https://wmlawreview.org/sites/default/files/Hasen.pdf)
- [Hasen, "The Supreme Court's Pro-Partisanship Turn" — Georgetown L.J.](https://www.law.georgetown.edu/georgetown-law-journal/wp-content/uploads/sites/26/2020/07/Hasen-The-Supreme-Court%E2%80%99s-Pro-Partisanship-Turn.pdf)
- [Racial gerrymandering after Rucho — Columbia Law Review](https://columbialawreview.org/content/racial-gerrymandering-after-rucho-v-common-cause-untangling-race-and-party/)
- [Race and politics: Entanglement — Southern California Law Review](https://southerncalifornialawreview.com/2023/04/24/race-and-politics-the-problem-of-entanglement-in-gerrymandering-cases/)
- [Racial vote dilution vs. racial gerrymandering — Democracy Docket](https://www.democracydocket.com/analysis/racial-gerrymandering-vs-racial-vote-dilution-explained/)

### Detection tests
- [Stephanopoulos & McGhee, "Partisan Gerrymandering and the Efficiency Gap," 82 U. Chi. L. Rev. 831 (2015)](https://chicagounbound.uchicago.edu/cgi/viewcontent.cgi?article=1946&context=public_law_and_legal_theory)
- [Brennan Center: How the Efficiency Gap Works (Petry)](https://www.brennancenter.org/sites/default/files/legal-work/How_the_Efficiency_Gap_Standard_Works.pdf)
- [Yale Liman: Evaluation of the Efficiency Gap Proposal](https://law.yale.edu/sites/default/files/area/center/liman/document/ssrn-id3019540.pdf)
- [Efficiency gap — Wikipedia](https://en.wikipedia.org/wiki/Efficiency_gap)
- [Wang, "Three Tests for Practical Evaluation of Partisan Gerrymandering," 68 Stan. L. Rev. 1263 (2016)](https://www.law.uchicago.edu/news/proving-partisan-gerrymandering-efficiency-gap)
- [Warrington, "Quantifying Gerrymandering Using the Vote Distribution," Election Law J. (2018)](https://www.liebertpub.com/doi/10.1089/elj.2019.0562)
- [Declination — arXiv:1803.04799](https://ar5iv.labs.arxiv.org/html/1803.04799)
- [Declination — PlanScore methodology](https://planscore.org/metrics/declination/)
- [DeFord, Duchin, Solomon, "Recombination" — Harvard Data Science Review](https://mggg.org/uploads/ReCom.pdf)
- [MGGG samplers and ReCom](https://mggg.org/samplers)
- [GerryChain — GitHub](https://github.com/mggg/GerryChain)
- [Duke Quantifying Gerrymandering report](https://mggg.org/uploads/md-report.pdf)
- [MGGG: Computational Redistricting and the VRA](https://mggg.org/publications/VRA-Ensembles.pdf)
- [Compactness measures vignette — redistmetrics R package](https://cran.r-project.org/web/packages/redistmetrics/vignettes/compactness.html)
- [King, "How to Measure Legislative District Compactness"](https://gking.harvard.edu/files/gking/files/compact.pdf)
- [AMS Feature Column: Congressional Redistricting and Gerrymandering](https://www.ams.org/publicoutreach/feature-column/fc-2014-08)
- [Tapp, "Measuring Political Gerrymandering" — arXiv:1801.02541](https://arxiv.org/pdf/1801.02541)
- [Gerrymandering and Compactness — arXiv:1803.02857](https://arxiv.org/pdf/1803.02857)
- [Chen & Rodden, "Unintentional Gerrymandering" — QJPS 2013](https://web.stanford.edu/~jrodden/wp/florida.pdf)
- [Chen & Rodden, "Cutting Through the Thicket" — 2015](https://www.brennancenter.org/sites/default/files/legal-work/Chen_Rodden_Through_the_Thicket_2015.pdf)

### Deterministic and algorithmic districting
- [Vickrey, "On the Prevention of Gerrymandering," Pol. Sci. Q. 76:105 (1961)](https://www.psqonline.org/article.cfm?IDArticle=7310)
- [Hess et al., "Nonpartisan Political Redistricting by Computer," OR 13:998 (1965)](https://pubsonline.informs.org/doi/abs/10.1287/opre.13.6.998)
- [Brian Olson — BDistricting, About](https://bdistricting.com/about.html)
- [BDistricting maps (2000 cycle)](https://bdistricting.com/2000/)
- [Washington Post profile of Brian Olson](https://www.washingtonpost.com/news/wonk/wp/2014/06/03/this-computer-programmer-solved-gerrymandering-in-his-spare-time/)
- [FiveThirtyEight: We Drew 2,568 Congressional Districts](https://fivethirtyeight.com/features/we-drew-2568-congressional-districts-by-hand-heres-how/)
- [Warren Smith — Shortest Splitline overview](https://rangevoting.org/GerryExamples.html)
- [Shortest Splitline — algorithm details](https://rangevoting.org/Splitlining.html)
- [Shortest Splitline — all 50 states maps](https://www.rangevoting.org/SplitLR.html)
- [Cohen-Addad, Klein, Young, "Balanced Power Diagrams for Redistricting" — arXiv:1710.03358](https://arxiv.org/pdf/1710.03358)
- [Cohen-Addad et al., "Balanced Centroidal Power Diagrams for Redistricting" — ACM 2018](https://dl.acm.org/doi/10.1145/3274895.3274979)
- [Bourne & Roper, "Centroidal Power Diagrams, Lloyd's Algorithm" — arXiv:1409.2786](https://arxiv.org/pdf/1409.2786)
- [Lloyd's algorithm — Wikipedia](https://en.wikipedia.org/wiki/Lloyd's_algorithm)
- [Centroidal Voronoi tessellation — Wikipedia](https://en.wikipedia.org/wiki/Centroidal_Voronoi_tessellation)
- [Convergence of Lloyd's Algorithm for CVT — SIAM J. Numer. Anal.](https://epubs.siam.org/doi/10.1137/040617364)
- [Brown University: Algorithm to combat gerrymandering (Cohen-Addad coverage)](https://www.brown.edu/news/2017-11-07/redistricting)
- [Gerrymandering and computational redistricting — J. Comp. Soc. Sci.](https://link.springer.com/article/10.1007/s42001-019-00053-9)
- [Mathematical models of political districting — ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S036083521930734X)
- [Imposing Contiguity Constraints in Political Districting — OR 2021](https://pubsonline.informs.org/doi/10.1287/opre.2021.2141)
- [On the Computational Tractability of Geographic Clustering for Redistricting — FORC 2021](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.FORC.2021.3)

### Apportionment and founders
- [Federalist No. 54 — full text, Library of Congress](https://guides.loc.gov/federalist-papers/text-51-60)
- [Federalist No. 54 — Wikipedia](https://en.wikipedia.org/wiki/Federalist_No._54)
- [U.S. Census: Methods of Apportionment](https://www.census.gov/about/history/historical-censuses-and-surveys/census-programs-surveys/decennial-census/methods.html)
- [Huntington-Hill method — Wikipedia](https://en.wikipedia.org/wiki/Huntington%E2%80%93Hill_method)
- [AMS: History of Apportionment in America](https://www.ams.org/publicoutreach/feature-column/fcarc-apportion2)
- [Hill's Method of Apportionment — MAA](https://old.maa.org/press/periodicals/convergence/apportioning-representatives-in-the-united-states-congress-hills-method-of-apportionment)

### Tools and projects
- [Princeton Gerrymandering Project — Redistricting Report Card Methodology](https://gerrymander.princeton.edu/redistricting-report-card-methodology/)
- [Rose Institute — Algorithmic Redistricting](https://roseinstitute.org/262-2/)
- [Priceonomics: Can an Algorithm Eliminate Gerrymandering?](https://priceonomics.com/algorithm-the-unfairness-of-gerrymandering/)
