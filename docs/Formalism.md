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

which is the canonical Hess 1965 cost function. The soft-penalty form was implemented first, but on real census geometry it converges to a 2-cycle in which units pile into whichever district is nearest target this iteration. The capacity-constrained form (equivalent to a single transportation step) avoids the cycle and matches the lineage from Hess et al. (1965) and Mehrotra-Johnson-Nemhauser (1998).

## 4. Iteration and objective

The full procedure is:

1. Place seeds (§2).
2. Run one capacitated assignment pass (§3).
3. Recompute each seed as the population-weighted centroid of its assigned blocks.
4. If the assignment differs from the previous iteration, repeat from step 2.

Reported objective (used for the DualBalance Score, not directly minimized):

```
Σ_i [ β · |Pop(D_i)  - P*| / P*
    + β · |Area(D_i) - A*| / A* ]
```

with `β` shared between the population and area terms so the two are weighted equally. Population is enforced as a capacity at the assignment step; area is currently reported only. Extending the assignment step to a two-dimensional capacitated transportation problem that bounds area as well is a natural next step.

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
