"""Verify custom Tarjan articulation-point implementation against networkx.

Loads NC VTDs (2666 units, 14 districts after PRISM), builds the dual
graph, computes articulation sets per district using both
implementations, and checks they're equal.
"""

from __future__ import annotations

import networkx as nx

from dualbalance.contiguity import ContiguityTracker
from dualbalance.districting import generate_plan
from dualbalance.io import load_units
from dualbalance.optimize import _build_dual_graph

EXTRA = ["vap_total", "vap_nhwhite", "vap_black", "vap_hispanic", "vap_aian", "vap_asian",
         "votes_R", "votes_D"]

units = load_units("data/nc_vtd.geojson", id_column="GEOID20", pop_column="population",
                   county_column="county", extra_columns=EXTRA)
plan = generate_plan(units, 14, geography="vtd")
graph = _build_dual_graph(units)

tracker = ContiguityTracker(graph, plan.assignment)

for d, members in tracker._members.items():
    sub = graph.subgraph(members)
    if len(members) <= 2:
        nx_art = set()
    elif not nx.is_connected(sub):
        nx_art = set(members)
    else:
        nx_art = set(nx.articulation_points(sub))
    custom_art = set(tracker._articulations[d])
    if nx_art != custom_art:
        only_nx = nx_art - custom_art
        only_custom = custom_art - nx_art
        print(f"MISMATCH on district {d}: nx_only={len(only_nx)} custom_only={len(only_custom)}")
        print(f"  members={len(members)}")
        print(f"  only_nx sample: {list(only_nx)[:5]}")
        print(f"  only_custom sample: {list(only_custom)[:5]}")
    else:
        print(f"district {d}: |members|={len(members):4d}  |art|={len(custom_art):4d}  OK")
