# Formalism

Mathematical statement of the DualBalance districting algorithm. See [../README.md](../README.md) for motivation and the narrative algorithm.

## 1. Objects

Let the state be divided into atomic units (census blocks, block groups, or VTDs):

```
U = {u_1, u_2, ..., u_m}
```

Each unit `u` has:

```
population p_u
area       a_u
centroid   x_u = (x, y)  in an equal-area projection
geometry   polygon g_u
```

Let:

```
N    = number of representatives apportioned to the state
P    = total state population
A    = total state land area
P*   = P / N      target population per district
A*   = A / N      target area per district
norm = bounding-box diagonal of the units (used to normalize distances)
```

## 2. Seed placement (radial)

Let `c = (c_x, c_y)` be the population-weighted centroid of the units:

```
c_x = (Σ p_u · x_u) / Σ p_u
c_y = (Σ p_u · y_u) / Σ p_u
```

Choose seed radius `r = 0.001 · norm` (0.1 % of the bounding-box diagonal — small enough that the Voronoi cells degenerate to near-perfect radial slices through `c`, large enough that the seeds are numerically distinct).

For `d = 0, 1, ..., N-1`, place seed `s_d` at

```
θ_d = 2π · d / N
s_d = (c_x + r · cos(θ_d), c_y + r · sin(θ_d))
```

Seed 0 sits due east of `c`; seeds advance counter-clockwise. With this placement the assignment in §3 produces districts that look like pie slices through `c`, each slice naturally spanning both dense (near-center) and sparse (boundary-side) territory.

## 3. Capacitated first-fit assignment

Let `d(u, i) = ||x_u - s_i||` be the Euclidean distance from unit `u` to seed `i`, and normalize by `norm` so the cost is unitless. Sort the full set of `(u, i)` pairs by ascending normalized distance, then walk that list in order:

```
remaining_capacity[i] = P*    for all i
for each (u, i) in ascending d(u, i) / norm:
    if u is already assigned:        continue
    if remaining_capacity[i] >= p_u: assign u to i; remaining_capacity[i] -= p_u
    else:                             skip
```

Any unit not placed by the end of the walk (a rare integer-rounding edge case) is assigned to the district with the largest remaining capacity (`argmax` resolves ties to the smallest district id).

Population balance is enforced as a hard cap. There is no soft-penalty form, no Lloyd recentering, no iteration: a single pass suffices because the seed positions are fixed by the radial rule and do not drift.

## 4. Contiguity repair

After §3, every unit belongs to exactly one district, but a district may consist of more than one connected component (rare on convex states, more common on those with peninsulas or islands). For each such district, keep the component with the largest total population and dissolve the rest into adjacent districts.

For each unit `u` in a smaller component, the destination district is the lowest-cost adjacent district whose neighbors of `u` already lie in it. Cost is

```
cost(u, j) = d(x_u, s_j) / norm
           + |Pop(D_j) + p_u - P*| / P*
           + |Area(D_j) + a_u - A*| / A*
```

with ties broken in cascade `(cost, pop_pen, area_pen, distance, district_id)` ascending. Repair iterates until every district is contiguous (capped at 10 sweeps; in practice it converges in 0–1 sweeps).

## 5. Score

The scoring harness reports a single primary metric. Define the per-district relative deviations

```
pop_dev_i  = |Pop(D_i)  − P*| / P*
area_dev_i = |Area(D_i) − A*| / A*
```

and their state-wide means `pop_dev_mean`, `area_dev_mean`. Then

```
DualBalance Score = 1 / (1 + 0.5 · pop_dev_mean + 0.5 · area_dev_mean)
```

The 0.5/0.5 coefficients weight population and area equally so each district is judged on representing roughly 1/N of the people *and* roughly 1/N of the state's geography (the House and Senate principles combined within a single chamber). The score reaches 1.0 for a perfectly balanced plan and approaches 0 as deviations grow without bound.

Secondary metrics — Polsby-Popper compactness and Reock — are reported but not optimized against. Pizza-slice districts have lower compactness than blob-Voronoi or hand-drawn districts by construction; this is a deliberate trade for area-balance, not a bug.

## 6. Constraints

Always:

1. Every unit belongs to exactly one district.
2. Every district is contiguous (guaranteed by §4).
3. No district is empty (guaranteed by §3 plus capacity arithmetic, unless `N > number of spatially separable subregions`).
4. Boundaries follow unit boundaries.
5. Tie-breaking is deterministic at every step (see §7).

## 7. Deterministic tie-breaking

Every comparison that could otherwise be ambiguous resolves to a fixed cascade:

1. In §3 assignment, ties in normalized distance `d(u, i) / norm` resolve to ascending `(unit_id, district_id)`.
2. In §3 fallback (unassigned units), ties on remaining capacity resolve to the smallest district id (`np.argmax` convention).
3. In §4 repair, candidate selection for a transferred unit resolves to ascending `(cost, pop_pen, area_pen, distance, district_id)`.
4. There is no other source of nondeterminism: no RNG, no wall-clock, no hash-order dependence, no parallel reduce.
