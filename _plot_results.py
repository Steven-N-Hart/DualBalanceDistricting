"""Comparison barplot: this work (block-scale, refined from VTD) vs Cascade vs Enacted.

Cascade is Iowa-LSA-flavored deterministic baseline (county-aggregating,
farthest-point seeds) with no optimizer post-pass. Values from
out/<state>_cascade/metrics.json. TX is partial (still running).
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np

states = ["IA", "MA", "MN", "NC", "WI", "TX"]

# DualBalance Score (higher is better).
opt_dbs =     [0.9651, 0.8124, 0.6613, 0.7972, 0.6953, 0.7030]  # TX partial
cascade_dbs = [0.8987, 0.7184, 0.6956, 0.8109, 0.8023, 0.6945]
enacted_dbs = [0.8828, 0.7246, 0.6391, 0.7689, 0.7410, 0.6658]

# pop_dev_max as percentage (lower is better; Karcher target = 0.05%).
opt_popdev_pct =     [0.0499, 0.0988, 0.0599, 0.0794, 0.0383, 0.5186]
cascade_popdev_pct = [0.2902, 41.5562, 76.1446, 10.2736, 0.4971, 24.5835]
enacted_popdev_pct = [0.0066, 0.6184, 1.3212, 0.6630, 0.0803, 2.6098]

x = np.arange(len(states))
width = 0.27

fig, (ax_dbs, ax_pop) = plt.subplots(1, 2, figsize=(14, 5.5))

# --- DBS panel ----------------------------------------------------------
ax_dbs.bar(x - width, opt_dbs, width, label="DualBalance (this work)", color="#1f77b4")
ax_dbs.bar(x,       cascade_dbs, width, label="Cascade (Iowa-LSA style)", color="#ff7f0e")
ax_dbs.bar(x + width, enacted_dbs, width, label="Enacted (119th Congress)", color="#888888")
ax_dbs.set_xticks(x)
ax_dbs.set_xticklabels(states)
ax_dbs.set_ylabel("DualBalance Score (higher is better)")
ax_dbs.set_title("DBS")
ax_dbs.set_ylim(0.6, 1.0)
ax_dbs.legend(loc="lower right", fontsize=8)
for i, (a, b, c) in enumerate(zip(opt_dbs, cascade_dbs, enacted_dbs)):
    ax_dbs.text(i - width, a + 0.005, f"{a:.3f}", ha="center", fontsize=7)
    ax_dbs.text(i,         b + 0.005, f"{b:.3f}", ha="center", fontsize=7)
    ax_dbs.text(i + width, c + 0.005, f"{c:.3f}", ha="center", fontsize=7)

# --- pop_dev_max panel (log scale) --------------------------------------
ax_pop.bar(x - width, opt_popdev_pct, width, label="DualBalance (this work)", color="#1f77b4")
ax_pop.bar(x,         cascade_popdev_pct, width, label="Cascade", color="#ff7f0e")
ax_pop.bar(x + width, enacted_popdev_pct, width, label="Enacted", color="#888888")
ax_pop.set_xticks(x)
ax_pop.set_xticklabels(states)
ax_pop.set_ylabel("Max population deviation (%, log scale; lower is better)")
ax_pop.set_title("pop_dev_max (Karcher target ~0.05%)")
ax_pop.set_yscale("log")
ax_pop.axhline(0.05, color="red", linestyle="--", linewidth=1, alpha=0.6,
               label="Karcher ~0.05%")
ax_pop.legend(loc="upper left", fontsize=8)
for i, (a, b, c) in enumerate(zip(opt_popdev_pct, cascade_popdev_pct, enacted_popdev_pct)):
    ax_pop.text(i - width, a * 1.18, f"{a:.2f}", ha="center", fontsize=7)
    ax_pop.text(i,         b * 1.18, f"{b:.2f}", ha="center", fontsize=7)
    ax_pop.text(i + width, c * 1.18, f"{c:.2f}", ha="center", fontsize=7)

fig.suptitle(
    "DualBalance Districting vs Cascade (Iowa-LSA style) vs Enacted (119th Congress)\n"
    "(TX still running, value shown is current Phase 2 progress)",
    fontsize=11,
)
fig.tight_layout()
os.makedirs("out", exist_ok=True)
out = "out/comparison_block.png"
fig.savefig(out, dpi=130, bbox_inches="tight")
print(f"wrote {out}")
