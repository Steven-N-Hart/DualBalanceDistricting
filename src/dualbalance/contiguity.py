"""Incremental contiguity check via cached articulation-point sets.

The hot loop in :mod:`dualbalance.optimize` and
:mod:`dualbalance.tighten` is: "for each candidate boundary move, would
removing this unit disconnect its source district?" The naive
implementation calls ``nx.is_connected`` on the district's subgraph
for every candidate, which is ``O(V + E)`` per check and dominates
runtime at block scale.

A unit ``u`` can be safely removed from district ``d`` iff:

1. ``d`` would not become empty (it has more than one unit), and
2. ``u`` is not an articulation point (cut vertex) of ``d``'s subgraph.

Articulation points for a graph with V nodes and E edges can be found
in ``O(V + E)`` via Tarjan's algorithm, then queried in ``O(1)``.
Maintaining the articulation set per district reduces the per-move
contiguity check to a single set lookup, at the cost of recomputing
the affected districts' articulation sets after each accepted move.

For a district of size V_d, that recompute is ``O(V_d + E_d)``, which
is much smaller than the global ``O(V + E)`` of the naive check
(typically V_d ~ V / N for N districts).

This module implements Tarjan's algorithm directly on CSR adjacency
arrays (rather than calling networkx). At VTD scale (a few thousand
nodes) the speedup is modest; at block scale (tens of thousands per
district) it is the difference between hours and minutes per state.
"""

from __future__ import annotations

import networkx as nx
import numpy as np

try:
    from numba import njit

    _HAS_NUMBA = True
except ImportError:  # pragma: no cover
    _HAS_NUMBA = False

    def njit(*args, **kwargs):
        # Fall back to no-op decorator when numba is missing.
        if len(args) == 1 and callable(args[0]):
            return args[0]

        def _wrap(fn):
            return fn

        return _wrap


def _build_csr(graph: nx.Graph) -> tuple[dict[str, int], list[str], np.ndarray, np.ndarray]:
    """Convert a networkx graph to CSR-style integer adjacency.

    Returns ``(node_to_idx, idx_to_node, indptr, indices)`` where
    ``indices[indptr[i]:indptr[i+1]]`` are the integer-indexed
    neighbors of node ``i``. Neighbor lists are sorted by integer index
    so iteration order is deterministic across runs.
    """
    idx_to_node: list[str] = sorted(graph.nodes)
    node_to_idx: dict[str, int] = {n: i for i, n in enumerate(idx_to_node)}
    indptr = np.zeros(len(idx_to_node) + 1, dtype=np.int64)
    neighbor_lists: list[list[int]] = []
    for n in idx_to_node:
        nbr_idxs = sorted(node_to_idx[nb] for nb in graph.neighbors(n))
        neighbor_lists.append(nbr_idxs)
        indptr[node_to_idx[n] + 1] = len(nbr_idxs)
    indptr = np.cumsum(indptr)
    total = int(indptr[-1])
    indices = np.empty(total, dtype=np.int64)
    for i, nbrs in enumerate(neighbor_lists):
        start = int(indptr[i])
        indices[start : start + len(nbrs)] = nbrs
    return node_to_idx, idx_to_node, indptr, indices


@njit(cache=True)
def _articulations_njit(
    indptr: np.ndarray,
    indices: np.ndarray,
    in_subset: np.ndarray,
    member_idxs: np.ndarray,
    disc: np.ndarray,
    low: np.ndarray,
    parent: np.ndarray,
    children_root: np.ndarray,
    is_root: np.ndarray,
    art_mask: np.ndarray,
    stack_node: np.ndarray,
    stack_cursor: np.ndarray,
) -> None:
    """Iterative Tarjan on a node subset, JIT-compiled.

    Workspace arrays (``disc`` through ``stack_cursor``) are
    pre-allocated by the caller and reset to sentinel values for the
    nodes in ``member_idxs``. The function fills ``art_mask`` in place
    (True at indices that are articulation points within the subset).
    """
    timer = 0
    n_members = member_idxs.shape[0]
    for k in range(n_members):
        start = member_idxs[k]
        if disc[start] != -1:
            continue
        is_root[start] = True
        stack_node[0] = start
        stack_cursor[0] = 0
        stack_size = 1
        disc[start] = timer
        low[start] = timer
        timer += 1
        parent[start] = -1

        while stack_size > 0:
            u = stack_node[stack_size - 1]
            cursor = stack_cursor[stack_size - 1]
            nbr_start = indptr[u]
            nbr_end = indptr[u + 1]
            if cursor + nbr_start >= nbr_end:
                stack_size -= 1
                p = parent[u]
                if p != -1:
                    if low[u] < low[p]:
                        low[p] = low[u]
                    if not is_root[p] and low[u] >= disc[p]:
                        art_mask[p] = True
                continue
            v = indices[nbr_start + cursor]
            stack_cursor[stack_size - 1] = cursor + 1
            if not in_subset[v]:
                continue
            if disc[v] == -1:
                disc[v] = timer
                low[v] = timer
                timer += 1
                parent[v] = u
                if is_root[u]:
                    children_root[u] += 1
                stack_node[stack_size] = v
                stack_cursor[stack_size] = 0
                stack_size += 1
            elif v != parent[u]:
                if disc[v] < low[u]:
                    low[u] = disc[v]

        if children_root[start] > 1:
            art_mask[start] = True


@njit(cache=True)
def _is_connected_njit(
    indptr: np.ndarray,
    indices: np.ndarray,
    in_subset: np.ndarray,
    member_idxs: np.ndarray,
    seen: np.ndarray,
    stack: np.ndarray,
) -> bool:
    """BFS/DFS connectedness check on a node subset, JIT-compiled."""
    n_members = member_idxs.shape[0]
    if n_members == 0:
        return True
    start = member_idxs[0]
    seen[start] = True
    stack[0] = start
    stack_size = 1
    visited = 1
    while stack_size > 0:
        stack_size -= 1
        u = stack[stack_size]
        for k in range(indptr[u], indptr[u + 1]):
            v = indices[k]
            if in_subset[v] and not seen[v]:
                seen[v] = True
                stack[stack_size] = v
                stack_size += 1
                visited += 1
    return visited == n_members


class ContiguityTracker:
    """Per-district subgraph + cached articulation-point sets.

    Construct once from a dual graph + initial assignment. After each
    accepted move, call :meth:`apply_move` so the cached articulation
    sets stay correct. :meth:`can_remove` is the hot-path query.
    """

    def __init__(self, graph: nx.Graph, assignment: dict[str, int]):
        self.graph = graph
        self.assignment: dict[str, int] = dict(assignment)
        self._node_to_idx, self._idx_to_node, self._indptr, self._indices = _build_csr(graph)
        n_nodes = len(self._idx_to_node)
        # Per-district membership stored as a boolean mask over node indices
        # plus the integer-index list for traversal seeding.
        self._members: dict[int, set[str]] = {}
        self._member_mask: dict[int, np.ndarray] = {}
        for uid, d in self.assignment.items():
            self._members.setdefault(d, set()).add(uid)
        for d, mems in self._members.items():
            mask = np.zeros(n_nodes, dtype=bool)
            for uid in mems:
                mask[self._node_to_idx[uid]] = True
            self._member_mask[d] = mask
        # Workspaces reused across Tarjan / BFS calls — sized to the full
        # node count so we never reallocate during the hot loop.
        self._ws_disc = np.full(n_nodes, -1, dtype=np.int64)
        self._ws_low = np.zeros(n_nodes, dtype=np.int64)
        self._ws_parent = np.full(n_nodes, -1, dtype=np.int64)
        self._ws_children_root = np.zeros(n_nodes, dtype=np.int64)
        self._ws_is_root = np.zeros(n_nodes, dtype=np.bool_)
        self._ws_art = np.zeros(n_nodes, dtype=np.bool_)
        self._ws_stack_node = np.empty(n_nodes, dtype=np.int64)
        self._ws_stack_cursor = np.empty(n_nodes, dtype=np.int64)
        self._ws_seen = np.zeros(n_nodes, dtype=np.bool_)
        self._ws_bfs_stack = np.empty(n_nodes, dtype=np.int64)
        self._articulations: dict[int, frozenset[str]] = {}
        for d in self._members:
            self._articulations[d] = self._compute_articulations(d)

    def can_remove(self, uid: str) -> bool:
        """True iff removing ``uid`` keeps its source district contiguous and non-empty."""
        d = self.assignment[uid]
        members = self._members.get(d)
        if not members or len(members) <= 1:
            return False
        return uid not in self._articulations[d]

    def apply_move(self, uid: str, d_dest: int) -> None:
        """Update the cache after a move ``uid: d_src -> d_dest`` is accepted."""
        d_src = self.assignment[uid]
        if d_src == d_dest:
            return
        idx = self._node_to_idx[uid]
        self._members[d_src].discard(uid)
        self._members.setdefault(d_dest, set()).add(uid)
        self._member_mask[d_src][idx] = False
        if d_dest not in self._member_mask:
            self._member_mask[d_dest] = np.zeros(len(self._idx_to_node), dtype=bool)
        self._member_mask[d_dest][idx] = True
        self.assignment[uid] = d_dest
        self._articulations[d_src] = self._compute_articulations(d_src)
        self._articulations[d_dest] = self._compute_articulations(d_dest)

    def _compute_articulations(self, d: int) -> frozenset[str]:
        members = self._members.get(d, set())
        if len(members) <= 2:
            return frozenset()
        mask = self._member_mask[d]
        member_idxs = np.fromiter(
            (self._node_to_idx[uid] for uid in members),
            dtype=np.int64,
            count=len(members),
        )
        member_idxs.sort()

        # Reset workspace entries for this district only.
        self._ws_disc[member_idxs] = -1
        self._ws_low[member_idxs] = 0
        self._ws_parent[member_idxs] = -1
        self._ws_children_root[member_idxs] = 0
        self._ws_is_root[member_idxs] = False
        self._ws_art[member_idxs] = False

        if not self._is_connected_subset(mask, member_idxs):
            return frozenset(members)

        _articulations_njit(
            self._indptr,
            self._indices,
            mask,
            member_idxs,
            self._ws_disc,
            self._ws_low,
            self._ws_parent,
            self._ws_children_root,
            self._ws_is_root,
            self._ws_art,
            self._ws_stack_node,
            self._ws_stack_cursor,
        )
        art_idxs = member_idxs[self._ws_art[member_idxs]]
        return frozenset(self._idx_to_node[int(i)] for i in art_idxs)

    def _is_connected_subset(self, mask: np.ndarray, member_idxs: np.ndarray) -> bool:
        if member_idxs.shape[0] == 0:
            return True
        self._ws_seen[member_idxs] = False
        return bool(
            _is_connected_njit(
                self._indptr,
                self._indices,
                mask,
                member_idxs,
                self._ws_seen,
                self._ws_bfs_stack,
            )
        )
