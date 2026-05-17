"""Story plots: one ranked bar chart (the headline) + boxplots for everything else.

Reads out/compare_all_summary.json. Works on whatever states are in
the JSON, so it's a no-op preview at 6 states and the final figure
once the 50-state loop has populated more.

Output: out/story_headline_eg.png and out/story_box_<metric>.png.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]

with open(REPO / "out" / "compare_all_summary.json") as f:
    data = json.load(f)

states = sorted(data.keys())
plans = ["dualbalance", "cascade", "bdistricting", "enacted"]
plan_labels = {
    "dualbalance":  "DualBalance",
    "cascade":      "Cascade",
    "bdistricting": "BDistricting",
    "enacted":      "Enacted",
}
plan_colors = {
    "dualbalance":  "#1f77b4",
    "cascade":      "#ff7f0e",
    "bdistricting": "#2ca02c",
    "enacted":      "#888888",
}

# Two-tier: EG plots use only composite/CONG states; all other metrics use all states.
eg_states = sorted(
    s for s in states
    if data[s].get("votes_source", "pres_20") in ("comp_16_22", "cong_22")
)
print(f"EG tier: {len(eg_states)} states with composite/CONG data: {eg_states}")
print(f"Full tier: {len(states)} states for non-partisan metrics")


def collect(metric: str, plan: str, state_set: list[str] | None = None) -> dict[str, float]:
    ss = state_set if state_set is not None else states
    out: dict[str, float] = {}
    for s in ss:
        v = data.get(s, {}).get(plan, {}).get(metric)
        if v is not None:
            out[s] = float(v)
    return out


# --- HEADLINE: ranked |EG| comparison — EG tier only --------------------
enacted_eg_abs = {s: abs(v) for s, v in collect("efficiency_gap", "enacted", eg_states).items()}
db_eg_abs = {s: abs(v) for s, v in collect("efficiency_gap", "dualbalance", eg_states).items()}
both = sorted(enacted_eg_abs.keys() & db_eg_abs.keys(),
              key=lambda s: -enacted_eg_abs[s])
fig, ax = plt.subplots(figsize=(max(11, 0.45 * len(both)), 5.5))
x = np.arange(len(both))
w = 0.4
ax.bar(x - w / 2, [enacted_eg_abs[s] for s in both], w,
       color=plan_colors["enacted"], label="Enacted (119th Congress)")
ax.bar(x + w / 2, [db_eg_abs[s] for s in both], w,
       color=plan_colors["dualbalance"], label="DualBalance (this work)")
ax.axhline(0.07, color="red", linestyle="--", linewidth=1, alpha=0.6,
           label="|EG| = 0.07 (gerrymander threshold)")
ax.set_xticks(x)
ax.set_xticklabels(both, rotation=0 if len(both) <= 12 else 90, fontsize=8)
ax.set_ylabel("|efficiency gap|  (lower is fairer)")
ax.set_title(
    f"Partisan fairness across {len(both)} states with composite/congressional election data\n"
    "(sorted by enacted |EG|, worst-gerrymandered on left; "
    "21 states using presidential proxy excluded)"
)
ax.legend(loc="upper right", fontsize=9)
fig.tight_layout()
out = REPO / "out" / "story_headline_eg.png"
fig.savefig(out, dpi=130, bbox_inches="tight")
plt.close(fig)
print(f"wrote {out}")


# --- BOXPLOTS: one box per plan, one dot per state ---------------------
def box(metric: str, title: str, ylabel: str, fmt: str = "{:.3f}",
        yscale: str = "linear",
        hline: tuple[float, str] | None = None,
        absolute: bool = False,
        state_set: list[str] | None = None) -> None:
    ss = state_set if state_set is not None else states
    series = {}
    for plan in plans:
        vals = list(collect(metric, plan, ss).values())
        if absolute:
            vals = [abs(v) for v in vals]
        series[plan] = vals
    fig, ax = plt.subplots(figsize=(8.5, 5))
    box_data = [series[p] for p in plans]
    box_labels = [f"{plan_labels[p]}\n(n={len(series[p])})" for p in plans]
    bp = ax.boxplot(box_data, labels=box_labels, widths=0.55,
                    patch_artist=True, showmeans=True,
                    meanprops={"marker": "D", "markerfacecolor": "white",
                               "markeredgecolor": "black", "markersize": 6})
    for patch, plan in zip(bp["boxes"], plans):
        patch.set_facecolor(plan_colors[plan])
        patch.set_alpha(0.6)
    # Jittered scatter of individual state points on top.
    rng = np.random.default_rng(0)
    for i, plan in enumerate(plans, start=1):
        xs = i + rng.uniform(-0.12, 0.12, size=len(series[plan]))
        ax.scatter(xs, series[plan], s=18, color=plan_colors[plan],
                   edgecolor="black", linewidth=0.4, zorder=3)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if yscale == "log":
        ax.set_yscale("log")
    if hline is not None:
        y, lbl = hline
        ax.axhline(y, color="red", linestyle="--", linewidth=1, alpha=0.6, label=lbl)
        ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    out = REPO / "out" / f"story_box_{metric}.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


box("dualbalance_score",
    title=f"DualBalance Score across {len(states)} states (higher = better)",
    ylabel="DBS")
box("pop_deviation_max",
    title=f"Max population deviation across {len(states)} states (Karcher ~0.05%)",
    ylabel="pop_dev_max (log)", yscale="log",
    hline=(0.0005, "Karcher 0.05%"))
box("area_deviation_mean",
    title=f"Mean area deviation across {len(states)} states (lower = better)",
    ylabel="area_dev_mean")
box("polsby_popper_mean",
    title=f"Polsby-Popper compactness across {len(states)} states (higher = more compact)",
    ylabel="PP_mean")
box("reock_mean",
    title=f"Reock compactness across {len(states)} states (higher = more compact)",
    ylabel="Reock_mean")
box("efficiency_gap",
    title=f"|Efficiency gap| across {len(eg_states)} states (composite/CONG data; lower = fairer)",
    ylabel="|EG|", absolute=True,
    hline=(0.07, "Gerrymander threshold 0.07"),
    state_set=eg_states)
box("mean_median_R",
    title=f"|mean-median R asymmetry| across {len(eg_states)} states (composite/CONG data)",
    ylabel="|mean_median_R|", absolute=True,
    state_set=eg_states)
box("minority_majority_districts",
    title=f"Minority-majority district count across {len(states)} states",
    ylabel="count")
box("counties_split",
    title=f"Counties split across {len(states)} states (lower preserves admin units)",
    ylabel="counties_split")

print("done")
