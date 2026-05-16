# Legal Standards for Population Equality in U.S. Redistricting

Internal reference: what the case law actually requires, what real
enacted plans achieve, and what it means for the DualBalance algorithm.

## Two distinct standards

U.S. redistricting law applies two different population-equality standards
depending on the body being districted:

- **Congressional districts** (U.S. House of Representatives) →
  *Wesberry v. Sanders* (1964) line, rooted in Article I, § 2.
  Standard: "as nearly equal as practicable." Effectively zero tolerance.
- **State and local legislative districts** →
  *Reynolds v. Sims* (1964) line, rooted in the Fourteenth Amendment's
  Equal Protection Clause. Standard: "substantially equal." A 10% total
  deviation safe harbor applies.

These are not interchangeable. A plan with 5% total deviation is
legally fine for a state legislative chamber and immediately struck
down for a U.S. House plan.

## Total deviation: the canonical formula

Total deviation is measured across the *spread* between extremes, not
the deviation of the worst single district:

$$
\text{total deviation} = \frac{\text{largest district pop} - \text{smallest district pop}}{\text{ideal pop}} \times 100\%
$$

Equivalently:

$$
\text{total deviation} = \text{(\% over ideal in the most-populous district)} + \text{(\% under ideal in the least-populous district)}
$$

Example: ideal = 100,000 people per district. Largest district has 105,000
(+5%); smallest has 96,000 (−4%). Total deviation = 9%.

This formula is what courts use to evaluate plans under both Reynolds
and Wesberry. The two extreme districts can be any pair; total deviation
is not (max district − ideal) alone.

## Congressional: Wesberry → Karcher

**Wesberry v. Sanders, 376 U.S. 1 (1964).** Held that Article I, § 2's
requirement that Representatives be chosen "by the People of the several
States" requires that "one man's vote in a congressional election is to
be worth as much as another's." Congressional districts within a state
must be drawn "as nearly as is practicable" to equal population.

**Kirkpatrick v. Preisler, 394 U.S. 526 (1969).** Invalidated a Missouri
congressional plan with **5.97%** total deviation. The Court rejected any
"fixed numerical or percentage population variance" as an acceptable
deviation. Required a "good faith effort to achieve precise mathematical
equality."

**Karcher v. Daggett, 462 U.S. 725 (1983).** The decisive modern
authority. Invalidated a New Jersey congressional plan with **0.6984%**
total deviation (largest district 527,472 people; smallest 523,798;
spread 3,674 people on an ideal of 526,059). The Supreme Court held:

1. There is **no de minimis threshold** for congressional districts.
   Any measurable deviation requires justification.
2. The state bears the burden of showing each deviation is necessary to
   achieve some legitimate state interest (geographic compactness,
   respect for political subdivisions, preserving communities of
   interest, etc.).
3. Plaintiffs need only show some deviation; they need not show it was
   intentional.

**Practical interpretation.** Modern congressional plans aim for total
deviations in the **0.001%–0.05%** range. Plans at or above ~1% require
substantial documented justification and remain vulnerable to challenge.
The 0.7% Karcher plan was struck down; subsequent plans rarely exceed
0.5% even with justifications.

## State legislative: Reynolds → the 10% safe harbor

**Reynolds v. Sims, 377 U.S. 533 (1964).** Held that the Equal
Protection Clause requires state legislative districts to be
"substantially equal" in population. Anticipated that some deviation
"based on legitimate considerations incident to the effectuation of a
rational state policy" would be acceptable.

**Mahan v. Howell, 410 U.S. 315 (1973).** Upheld a Virginia state plan
with **16.4%** total deviation, justified by the state's interest in
preserving political subdivision boundaries.

**White v. Regester, 412 U.S. 755 (1973).** Upheld a Texas state plan
with **9.9%** total deviation. The Court held that overall deviations
under 10% are "minor" and do not constitute a *prima facie* equal
protection violation. Established the 10% safe harbor in practice.

**Brown v. Thomson, 462 U.S. 835 (1983).** Reaffirmed the 10% safe
harbor for state legislative plans. Plans under 10% are presumptively
constitutional; the burden is on the challenger to demonstrate
unconstitutional intent or effect.

**Practical interpretation.** Under 10% total deviation is
presumptively safe for state legislative districts. Over 10% triggers
*Mahan*-style review where the state must justify the deviation with a
rational state policy (typically political-subdivision preservation).

## What does and doesn't count as "deviation"

- Population is measured against the **ideal** = total state population
  ÷ number of districts in that chamber.
- Only census population is counted (Voting Age Population, Citizen
  VAP, and similar are not part of the *Wesberry/Reynolds* test).
- The 10% safe harbor for state legislative is the *total deviation*
  metric, not the max single-district deviation. Many sources conflate
  these.

## Implications for DualBalance

DualBalance is currently evaluated on six states' **congressional**
plans (MN, IA, MA, NC, TX, WI). The legal target is therefore the
Karcher standard, not the 10% rule.

Real enacted congressional plans achieve total deviations on the order
of **0.001%–0.05%**. The DualBalance optimizer's current best is
**~0.04%** (WI) with most states in the **0.3%–35%** range. This means
the algorithm is currently producing plans that would not survive
Karcher scrutiny on most states, even though they score higher on the
DualBalance Score than the enacted plans.

Two paths forward depending on intended deployment:

1. **State legislative districting** (10% rule applies). Most of our
   current results fit comfortably under 10% total deviation. The
   algorithm needs only modest refinement to be a legally credible
   state-legislative-redistricting proposal.

2. **Congressional districting** (Karcher applies). Reaching the
   0.01%–0.1% range that real enacted plans achieve requires either
   (a) much finer input data — Census blocks rather than VTDs —
   so single-block moves can make sub-1000-person adjustments to
   district totals, or (b) MILP-based exact optimization, which is
   tractable on small N but does not scale to large-N states with
   the open-source solvers available.

Both options preserve the conceptual contribution of DualBalance
(deterministic generation breaks the forensic-metric inference chain).
The empirical claims about competitive DBS scores hold under either
deployment.

## Sources

- *Karcher v. Daggett*, 462 U.S. 725 (1983). Justia:
  <https://supreme.justia.com/cases/federal/us/462/725/>.
- *Karcher v. Daggett*. Wikipedia:
  <https://en.wikipedia.org/wiki/Karcher_v._Daggett>.
- *Reynolds v. Sims*, 377 U.S. 533 (1964). Justia:
  <https://supreme.justia.com/cases/federal/us/377/533/>.
- *Kirkpatrick v. Preisler*, 394 U.S. 526 (1969).
- *Mahan v. Howell*, 410 U.S. 315 (1973).
- *White v. Regester*, 412 U.S. 755 (1973). FindLaw:
  <https://caselaw.findlaw.com/court/us-supreme-court/412/755.html>.
- *Brown v. Thomson*, 462 U.S. 835 (1983).
- *Wesberry v. Sanders*, 376 U.S. 1 (1964).
- Ballotpedia, "Deviation": <https://ballotpedia.org/Deviation>.
- Loyola Law School (All About Redistricting), "Where are the lines
  drawn?": <https://redistricting.lls.edu/redistricting-101/where-are-the-lines-drawn/>.
- Congressional Research Service, "Apportionment and Redistricting
  Process for the U.S. House of Representatives":
  <https://www.congress.gov/crs-product/R45951>.
