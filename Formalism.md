# Formalism

Mathematical statement of the DualBalance districting algorithm. See [README.md](README.md) for motivation and the narrative algorithm.

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

Assign each block to one district by minimizing a weighted cost:

```
cost(b, i) =
    α · geographic_distance(x_b, s_i)
  + β · population_penalty(i)
  + γ · area_penalty(i)
```

where:

```
population_penalty(i) = |current_population(D_i) + p_b - P*| / P*
area_penalty(i)       = |current_area(D_i)       + a_b - A*| / A*
```

For the concept we set `β = γ`, so population balance and land-area balance are weighted equally.

## 4. Optimization objective

The full objective:

```
minimize Σ_i [
    α · compactness_cost(D_i)
  + β · |Pop(D_i)  - P*| / P*
  + β · |Area(D_i) - A*| / A*
]
```

Subject to:

1. Every block belongs to exactly one district.
2. Every district is contiguous.
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
