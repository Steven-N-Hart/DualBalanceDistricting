"""Bench numba Tarjan vs networkx articulation_points at block scale.

Loads IA blocks, builds dual graph, picks one district's subgraph,
and times the articulation-point computation for both implementations.
"""

from __future__ import annotations

import time

import networkx as nx
import numpy as np

from dualbalance.contiguity import ContiguityTracker
from dualbalance.districting import generate_plan
from dualbalance.io import load_units
from dualbalance.optimize import _build_dual_graph

print("loading IA blocks…", flush=True)
t0 = time.time()
units = load_units("data/ia_block.geojson", id_column="GEOID20",
                   pop_column="population", county_column="county")
print(f"  loaded {len(units):,} blocks in {time.time() - t0:.1f}s", flush=True)

print("building DualBalance seed plan + dual graph…", flush=True)
t0 = time.time()
plan = generate_plan(units, 4, geography="block")
graph = _build_dual_graph(units)
print(f"  DualBalance+graph in {time.time() - t0:.1f}s", flush=True)

print("creating ContiguityTracker (first call also JIT-compiles numba)…", flush=True)
t0 = time.time()
tracker = ContiguityTracker(graph, plan.assignment)
print(f"  tracker init in {time.time() - t0:.1f}s", flush=True)

# Pick the largest district for a meaningful microbench.
largest_d = max(tracker._members, key=lambda d: len(tracker._members[d]))
members = list(tracker._members[largest_d])
print(f"\nbenchmarking on district {largest_d} ({len(members):,} blocks)", flush=True)

# Networkx baseline.
sub = graph.subgraph(members)
t0 = time.time()
for _ in range(3):
    nx_art = set(nx.articulation_points(sub))
nx_time = (time.time() - t0) / 3
print(f"  networkx articulation_points (avg of 3): {nx_time * 1000:.0f} ms", flush=True)

# Custom numba.
t0 = time.time()
for _ in range(10):
    custom_art = tracker._compute_articulations(largest_d)
numba_time = (time.time() - t0) / 10
print(f"  custom numba _compute_articulations (avg of 10): {numba_time * 1000:.0f} ms", flush=True)
print(f"  speedup: {nx_time / numba_time:.1f}x", flush=True)

assert nx_art == set(custom_art), "MISMATCH"
print(f"  results identical: {len(custom_art)} articulation points", flush=True)
