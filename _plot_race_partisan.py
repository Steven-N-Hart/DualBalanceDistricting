"""Two more plots: race (minority-majority districts) and partisan (efficiency gap).

DualBalance values are the VTD-Karcher run (block-scale refinement
preserves district demographics to ~1% so VTD-scale numbers are
representative). Cascade and enacted come from out/<state>_cascade /
the score above.
"""

from __future__ import annotations

import json
import os

import matplotlib.pyplot as plt
import numpy as np

# Load DualBalance + Enacted from the script we just ran.
with open("out/race_partisan.json") as f:
    db_data = json.load(f)

# Cascade values from out/<state>_cascade/metrics.json.
cascade: dict[str, dict] = {}
for state in ["IA", "MA", "MN", "NC", "WI", "TX"]:
    path = f"out/{state.lower()}_cascade/metrics.json"
    if os.path.exists(path):
        with open(path) as f:
            cascade[state] = json.load(f)

states = ["IA", "MA", "MN", "NC", "WI", "TX"]

opt_mm = [db_data[s]["dualbalance"]["minority_majority_districts"] for s in states]
cascade_mm = [cascade[s]["minority_majority_districts"] for s in states]
enacted_mm = [db_data[s]["enacted"]["minority_majority_districts"] for s in states]

opt_eg = [db_data[s]["dualbalance"]["efficiency_gap"] for s in states]
cascade_eg = [cascade[s]["efficiency_gap"] for s in states]
enacted_eg = [db_data[s]["enacted"]["efficiency_gap"] for s in states]

x = np.arange(len(states))
width = 0.27

# ----- Race plot -----
fig, ax = plt.subplots(figsize=(11, 5))
ax.bar(x - width, opt_mm, width, label="DualBalance (this work)", color="#1f77b4")
ax.bar(x,         cascade_mm, width, label="Cascade (Iowa-LSA style)", color="#ff7f0e")
ax.bar(x + width, enacted_mm, width, label="Enacted (119th Congress)", color="#888888")
ax.set_xticks(x)
ax.set_xticklabels(states)
ax.set_ylabel("Minority-majority districts (count)")
ax.set_title("Minority-majority districts by state and plan")
ax.legend(loc="upper left", fontsize=9)
for i, (a, b, c) in enumerate(zip(opt_mm, cascade_mm, enacted_mm)):
    ax.text(i - width, a + 0.3, str(a), ha="center", fontsize=8)
    ax.text(i,         b + 0.3, str(b), ha="center", fontsize=8)
    ax.text(i + width, c + 0.3, str(c), ha="center", fontsize=8)
fig.suptitle("Race: minority-majority district count", fontsize=12)
fig.tight_layout()
fig.savefig("out/comparison_race.png", dpi=130, bbox_inches="tight")
print("wrote out/comparison_race.png")

# ----- Partisan plot: efficiency gap (signed; |EG|>0.07 is the rough partisan-gerrymander threshold) -----
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.bar(x - width, opt_eg, width, label="DualBalance (this work)", color="#1f77b4")
ax.bar(x,         cascade_eg, width, label="Cascade (Iowa-LSA style)", color="#ff7f0e")
ax.bar(x + width, enacted_eg, width, label="Enacted (119th Congress)", color="#888888")
ax.axhline(0.07, color="red", linestyle="--", linewidth=1, alpha=0.6,
           label="|EG| = 0.07 (gerrymander threshold)")
ax.axhline(-0.07, color="red", linestyle="--", linewidth=1, alpha=0.6)
ax.axhline(0, color="black", linewidth=0.5)
ax.set_xticks(x)
ax.set_xticklabels(states)
ax.set_ylabel("Efficiency gap (sign: +R / -D bias; closer to 0 is fairer)")
ax.set_title("Efficiency gap by state and plan")
ax.legend(loc="upper left", fontsize=8)
for i, (a, b, c) in enumerate(zip(opt_eg, cascade_eg, enacted_eg)):
    sign_a = 1 if a >= 0 else -1
    sign_b = 1 if b >= 0 else -1
    sign_c = 1 if c >= 0 else -1
    ax.text(i - width, a + 0.012 * sign_a, f"{a:+.3f}", ha="center", fontsize=7)
    ax.text(i,         b + 0.012 * sign_b, f"{b:+.3f}", ha="center", fontsize=7)
    ax.text(i + width, c + 0.012 * sign_c, f"{c:+.3f}", ha="center", fontsize=7)
fig.suptitle("Partisan fairness: efficiency gap", fontsize=12)
fig.tight_layout()
fig.savefig("out/comparison_partisan.png", dpi=130, bbox_inches="tight")
print("wrote out/comparison_partisan.png")
