# Formalism

Mathematical statement of the DualBalance districting algorithm. See [../README.md](../README.md) for motivation and the narrative algorithm.

## 1. Objects

Let the state be divided into small atomic units (census blocks):

```
B = {b_1, b_2, ..., b_m}
```

Each block `b` has:

```
population p_b
area       a_b
centroid   x_b = (lat_b, lon_b)
geometry   polygon g_b
```

Let:

```
N = number of representatives
P = total state population
A = total state land area
```

Target per district:

```
P* = P / N
A* = A / N
```

## 2. District seeds

Choose `N` seed points:

```
S = {s_1, s_2, ..., s_N}
```

Seed placement is deterministic. For example:

```
s_i = population-weighted centroid of the i-th largest population cluster
```

or:

```
seeds are initialized by deterministic farthest-point sampling
from ranked population centers
```

## 3. Assignment rule

Each iteration solves a *capacitated* assignment: each district has a hard population capacity `P*`, and units are assigned to their closest district that still has remaining capacity.

Concretely, let `d(b, i) = ||x_b - s_i||` be the geographic distance from block `b` to the centroid of district `i`'s current seed, and let `norm` be the units' total bounding-box diagonal (so the normalized cost `d / norm` lies in `[0, 1]`). Order the full set of `(b, i)` pairs by ascending `d(b, i) / norm`, and walk that list in order:

```
for each (b, i) in ascending d(b, i) / norm:
    if b is already assigned:        continue
    if remaining_capacity[i] >= p_b: assign b to i;  remaining_capacity[i] -= p_b
    else:                             skip
```

Any block not placed by the end of the walk (a rare rounding edge case) is assigned to the district with the largest remaining capacity.

This replaces the earlier soft-penalty form

```
cost(b, i) = α · d(x_b, s_i) + β · |pop(D_i) + p_b - P*| / P*
                              + γ · |area(D_i) + a_b - A*| / A*
```

which resembles the soft-penalty formulations used in early operations-research approaches to political districting, including Hess-style location-allocation models. The soft-penalty form was implemented first, but on real census geometry it converges to a 2-cycle in which units pile into whichever district is nearest target this iteration. The capacity-constrained form (a single transportation step) avoids the cycle and follows the broader lineage of capacitated location-allocation, including Hess et al. (1965) and Mehrotra-Johnson-Nemhauser (1998).

## 4. Iteration and objective

The full procedure is:

1. Place seeds (§2).
2. Run one capacitated assignment pass (§3).
3. Recompute each seed as the population-weighted centroid of its assigned blocks.
4. If the assignment differs from the previous iteration, repeat from step 2.

The current implementation — **v0, "Population-Capacitated Voronoi Baseline"** — minimizes total normalized geographic assignment cost subject to a population capacity `P*`. It then *reports* the DualBalance objective:

```
DualBalance Error = mean_i [ 0.5 · |Pop(D_i)/P  − 1/N| / (1/N)
                           + 0.5 · |Area(D_i)/A − 1/N| / (1/N) ]

DualBalance Score = 1 / (1 + DualBalance Error)
```

Equivalently, writing the per-district deviations as
`pop_dev_i  = |Pop(D_i) − P*| / P*` and
`area_dev_i = |Area(D_i) − A*| / A*`,
the score is `1 / (1 + 0.5·mean(pop_dev) + 0.5·mean(area_dev))`.

The two terms are weighted equally (β = γ = ½) so that each district is judged on representing roughly 1/N of the people *and* roughly 1/N of the state's geography. The 0.5/0.5 coefficients make the error a convex combination of the two mean deviations rather than a raw sum, so adding the area term cannot artificially inflate the error beyond what either component carries on its own.

**v0 vs v1.** In v0 (current), population is enforced as a hard capacity at the assignment step; area is diagnostic only — its deviation appears in the score but never constrains the generator. The intended **v1 ("Dual-Capacitated Voronoi Assignment")** replaces the assignment step with a two-dimensional capacitated transportation problem that bounds both `Pop(D_i)` and `Area(D_i)`. Only v1 *directly minimizes* the DualBalance objective; v0 minimizes a population-capacitated geographic-cost surrogate and reports the DualBalance score diagnostically.

Subject to:

1. Every block belongs to exactly one district.
2. Every district is contiguous (enforced by the post-iteration repair pass).
3. No district is empty.
4. Boundaries follow block boundaries.
5. Tie-breaking is deterministic (see §5).

## 5. Deterministic tie-breaking

When two choices are equal, use this fixed cascade — apply each rule in order until the tie is broken:

1. Lower population error.
2. Lower area error.
3. Shorter distance to seed.
4. Smaller district ID.
5. Smaller census block ID.
