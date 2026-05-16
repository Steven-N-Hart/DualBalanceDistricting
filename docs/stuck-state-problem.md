# Deterministic Districting: Local-Optimum Problem

## Setting

Let $G = (V, E)$ be a planar **dual graph** whose nodes are atomic census units (Voting Tabulation Districts or Census Blocks) of a single U.S. state, and whose edges connect units that share a non-trivial boundary (rook adjacency). Each unit $u \in V$ has a population $p_u \in \mathbb{Z}_{\geq 0}$ and an area $a_u > 0$.

A **districting plan** is a partition $\pi: V \to \{1, 2, \dots, N\}$ assigning each unit to exactly one of $N$ districts (with $N$ given by the U.S. Method of Equal Proportions). Let $V_d = \pi^{-1}(d)$ be the units in district $d$, and let

$$
P_d = \sum_{u \in V_d} p_u, \qquad A_d = \sum_{u \in V_d} a_u, \qquad P^* = \frac{1}{N}\sum_{u \in V} p_u, \qquad A^* = \frac{1}{N}\sum_{u \in V} a_u .
$$

A valid plan satisfies three hard constraints:

1. **Coverage**: every unit is assigned to exactly one district.
2. **Contiguity**: for every $d$, the subgraph $G[V_d]$ is connected.
3. **Non-empty**: $V_d \neq \emptyset$ for all $d$.

## Objective

We define population and area deviations per district as

$$
\delta^P_d = \frac{|P_d - P^*|}{P^*}, \qquad \delta^A_d = \frac{|A_d - A^*|}{A^*} ,
$$

and the **DualBalance Score**

$$
\mathrm{DBS}(\pi) \;=\; \frac{1}{1 + \tfrac{1}{2}\bar{\delta}^P + \tfrac{1}{2}\bar{\delta}^A}, \qquad \bar{\delta}^P = \frac{1}{N}\sum_d \delta^P_d, \quad \bar{\delta}^A = \frac{1}{N}\sum_d \delta^A_d.
$$

DBS lies in $(0, 1]$ and equals $1$ for a perfectly balanced plan. We seek $\pi^*$ maximizing $\mathrm{DBS}$.

## Legal constraint (the binding one)

U.S. congressional case law (*Wesberry v. Sanders* 1964; *Karcher v. Daggett* 1983) holds that congressional districts must be "as nearly equal in population as practicable" with **no de minimis threshold**. Practical interpretation: real enacted congressional plans achieve

$$
\delta^P_{\max} := \max_d \delta^P_d \;\lesssim\; 5 \times 10^{-4} \quad (0.05\%).
$$

(State-legislative districts get a 10% safe harbor under *Reynolds v. Sims*, which is much easier; we are targeting congressional.)

So the practical optimization problem is

$$
\max_\pi\; \mathrm{DBS}(\pi) \qquad \text{subject to constraints 1-3 and}\quad \delta^P_{\max}(\pi) \;\leq\; \tau , \tau \approx 5 \times 10^{-4}.
$$

The algorithm must be **deterministic** (no RNG, same input always produces the same output) and **driven only by $(G, \{p_u\}, \{a_u\}, N)$** — no politics, race, or hand-tuning.

## Local search

We initialize $\pi^{(0)}$ by a radial-Voronoi seeding heuristic followed by capacitated first-fit assignment, then run local search over **boundary moves**:

A boundary move $(u, d')$ takes a unit $u \in V$ with $\pi(u) = d \neq d'$ that has at least one neighbor in $V_{d'}$, and reassigns it to $d'$. The move is **feasible** iff after the move:
- $V_d$ remains connected (i.e., $u$ is not an articulation point of $G[V_d]$, and $|V_d| > 1$);
- $V_{d'}$ remains connected (trivially true since $u$ was adjacent to $V_{d'}$).

The search runs in two phases:

**Phase 1: drive $\delta^P_{\max}$ down to $\tau$.** Each step, accept the feasible boundary move that maximally improves $\delta^P_{\max}$ (or, as a tiebreaker, the $L^1$ sum $\sum_d \delta^P_d$). Stop when $\delta^P_{\max} \leq \tau$ **or** when no improving move exists.

**Phase 2: maximize DBS subject to $\delta^P_{\max} \leq$ (post-Phase-1 value).** Greedy hill-climb.

## The problem

**Phase 1 gets stuck in local optima far above $\tau$.** Concretely, at Census-block granularity on Iowa ($|V| \approx 175{,}000$, $N=4$, $P^* \approx 798{,}000$), Phase 1 settles at $\delta^P_{\max} \approx 0.133$ after $\sim 19{,}000$ moves, then **no feasible single-unit move strictly reduces $\delta^P_{\max}$**.

The stuck configuration appears to have the following structure (this is our working conjecture from algorithm logic; the precise empirical breakdown of which case occurs on the Iowa-block instance has not been fully audited):

- Two or more districts share the same $\delta^P_d$ at or very near the current maximum (say $D^+_1, D^+_2$, both at $\delta^P \approx +M$, i.e., over-populated by approximately the same amount).
- The remaining districts are under-populated ($\delta^P < 0$), call them $D^-_1, \dots, D^-_k$.
- Conjecture: $D^+_1$'s boundary $\partial D^+_1$ (units with a neighbor in another district) consists predominantly of units whose only out-district neighbors lie in $D^+_2$. Symmetrically for $D^+_2$.
- Conjecture: $D^-_j$ are reachable from $D^+_i$ only through $D^+_{3-i}$ in the district-adjacency graph (i.e., the over-pop districts form a separator between the under-pop districts and the over-pop district being targeted).

What is definitely true: the algorithm has exhaustively scanned every boundary unit of every district and found no single move whose $L^1$ delta is negative *and* no single move that strictly reduces the global $\delta^P_{\max}$. The questions above are about *why* that situation arises geometrically.

Any single boundary move $D^+_1 \to D^+_2$ strictly *increases* $\delta^P_{\max}$ (the receiving district overtakes by $p_u / P^*$), so it is rejected. Any single move $D^+_1 \to D^+_1^c$ that would help must cross through $D^+_2$, which a single unit cannot do.

This is a discrete-graph version of "drain one full bucket into another full bucket via an empty bucket reachable only through full buckets." A **chain of length 2**

$$
u: D^+_1 \to D^+_2, \quad v: D^+_2 \to D^-_j
$$

with $p_u \approx p_v$ and $u \neq v$, $v$ not adjacent to $u$, **does** strictly reduce $\delta^P_{\max}$ (drains $D^+_1$ by $p_u$, leaves $D^+_2$ approximately unchanged, fills $D^-_j$ by $p_v$). But enumerating such chains naively is $O(|\partial D^+_1| \cdot |\partial D^+_2| \cdot |V_{D^+_2}|)$ per pass and we lose the determinism + efficiency story.

## What we've ruled out

- **Pure $L^1$-greedy Phase 1**: stops far above $\tau$ because $L^1$-improving moves can avoid the worst district entirely (e.g., shuffling mass between two over-target districts that are not the worst).
- **Pure max-norm-greedy Phase 1**: stops similarly because of the tied-max situation described above.
- **Hybrid (accept move iff $L^1$-improving OR strictly reduces $\delta^P_{\max}$)**: helped a lot — at VTD granularity ($|V| \sim 2{-}10$k) most states reach $\delta^P_{\max} \in [0.0001, 0.005]$. But VTD granularity is too coarse: median $p_u$ is on the order of $10^3$ people, so a single move on a tight plan ($\delta^P_{\max} = \tau P^* \sim 400$ people) almost always overshoots the budget on one endpoint. We need block granularity ($p_u \sim 20$), where the hybrid gets stuck at $\delta^P_{\max} \approx 0.13$.
- **Simulated annealing**: forbidden — breaks the determinism requirement that is core to the algorithm's claim ("partisan-tuning-proof because there is no tuning knob").

## What we'd like

A deterministic procedure that, given the stuck configuration described above, finds a feasible (contiguity-preserving) **chain of boundary moves** of bounded length $k$ (say $k \leq 3$ or $k \leq 5$) that strictly reduces $\delta^P_{\max}$, in time polynomial in $|V|$ and $|E|$ and ideally not much worse than the current $O((|V| + |E|) \cdot \text{(number of accepted moves)})$ per pass.

Equivalently: **a fast deterministic algorithm for finding a minimum-cost augmenting transport on the district-adjacency graph, subject to the constraint that the transport be realizable as a sequence of single-unit contiguity-preserving boundary moves on the underlying dual graph.**

Bonus: any insight on theoretical lower bounds — i.e., is there an instance class where no polynomial-length chain reduces $\delta^P_{\max}$? Anecdotally this hasn't shown up empirically, but we have no proof.
