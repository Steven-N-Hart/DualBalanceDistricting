"""Generate the four manuscript figures from compare_all_summary.json.

Outputs (saved to manuscript/figures/):
  headline_eg.png     -- ranked |EG| bar chart, DualBalance vs Enacted
  boxplots_panel.png  -- 2x2 boxplot panel (DBS, pop_dev, |EG|, PP)
  nc_comparison.png   -- NC 3-panel map (Enacted | Cascade | DualBalance)
  race_scatter.png    -- minority-majority district scatter
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

REPO = Path(__file__).resolve().parent
FIG_DIR = REPO / "manuscript" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

with open(REPO / "out" / "compare_all_summary.json") as f:
    DATA = json.load(f)

STATES = sorted(DATA.keys())
PLANS = ["dualbalance", "cascade", "bdistricting", "enacted"]
COLORS = {
    "dualbalance":  "#1f77b4",
    "cascade":      "#ff7f0e",
    "bdistricting": "#2ca02c",
    "enacted":      "#888888",
}
LABELS = {
    "dualbalance":  "DualBalance",
    "cascade":      "Cascade",
    "bdistricting": "BDistricting",
    "enacted":      "Enacted",
}


def collect(metric: str, plan: str, absolute: bool = False) -> dict[str, float]:
    out: dict[str, float] = {}
    for s in STATES:
        v = DATA.get(s, {}).get(plan, {}).get(metric)
        if v is not None:
            out[s] = abs(float(v)) if absolute else float(v)
    return out


# ---------------------------------------------------------------------------
# Figure 1: Headline EG ranked bar chart
# ---------------------------------------------------------------------------
enacted_eg = {s: abs(v) for s, v in collect("efficiency_gap", "enacted").items()}
db_eg = {s: abs(v) for s, v in collect("efficiency_gap", "dualbalance").items()}
both = sorted(enacted_eg.keys() & db_eg.keys(), key=lambda s: -enacted_eg[s])

fig, ax = plt.subplots(figsize=(max(12, 0.42 * len(both)), 5.5))
x = np.arange(len(both))
w = 0.4
ax.bar(x - w / 2, [enacted_eg[s] for s in both], w,
       color=COLORS["enacted"], label="Enacted (119th Congress)")
ax.bar(x + w / 2, [db_eg[s] for s in both], w,
       color=COLORS["dualbalance"], label="DualBalance (this work)")
ax.axhline(0.07, color="red", linestyle="--", linewidth=1.2, alpha=0.7,
           label="|EG| = 0.07 (gerrymander threshold)")
ax.set_xticks(x)
ax.set_xticklabels(both, rotation=0 if len(both) <= 15 else 90, fontsize=8)
ax.set_ylabel("|Efficiency Gap|  (lower = fairer)", fontsize=11)
ax.set_title(f"Partisan fairness: DualBalance vs enacted plan across {len(both)} states\n"
             "(sorted by enacted |EG|, worst-gerrymandered on left)",
             fontsize=11)
ax.legend(loc="upper right", fontsize=9)
ax.set_ylim(bottom=0)
fig.tight_layout()
out = FIG_DIR / "headline_eg.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"wrote {out}")


# ---------------------------------------------------------------------------
# Figure 2: 2x2 boxplot panel
# ---------------------------------------------------------------------------
PANEL_SPECS = [
    ("dualbalance_score",  "DualBalance Score\n(higher = better)",       False, None),
    ("pop_deviation_max",  "Max pop. deviation (log)\n← Karcher 0.05%", False, 0.0005),
    ("efficiency_gap",     "|Efficiency Gap|\n← gerrymander threshold", True,  0.07),
    ("polsby_popper_mean", "Polsby-Popper mean\n(higher = more compact)", False, None),
]

fig = plt.figure(figsize=(12, 9))
gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.35)
panel_labels = ["A", "B", "C", "D"]

for idx, (metric, ylabel, absolute, hline) in enumerate(PANEL_SPECS):
    ax = fig.add_subplot(gs[idx // 2, idx % 2])
    series = {}
    for plan in PLANS:
        vals = list(collect(metric, plan, absolute=absolute).values())
        series[plan] = vals

    box_data = [series[p] for p in PLANS]
    tick_labels = [f"{LABELS[p]}\n(n={len(series[p])})" for p in PLANS]
    bp = ax.boxplot(box_data, tick_labels=tick_labels, widths=0.5,
                    patch_artist=True, showmeans=True,
                    meanprops={"marker": "D", "markerfacecolor": "white",
                               "markeredgecolor": "black", "markersize": 5})
    for patch, plan in zip(bp["boxes"], PLANS):
        patch.set_facecolor(COLORS[plan])
        patch.set_alpha(0.55)
    rng = np.random.default_rng(42)
    for i, plan in enumerate(PLANS, start=1):
        xs = i + rng.uniform(-0.15, 0.15, size=len(series[plan]))
        ax.scatter(xs, series[plan], s=14, color=COLORS[plan],
                   edgecolor="black", linewidth=0.3, zorder=3)
    if metric == "pop_deviation_max":
        ax.set_yscale("log")
    if hline is not None:
        ax.axhline(hline, color="red", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.text(0.02, 0.97, panel_labels[idx], transform=ax.transAxes,
            fontsize=13, fontweight="bold", va="top")

fig.suptitle(f"Cross-state metric distributions across {len(STATES)} states\n"
             "(boxes = IQR, diamonds = mean, dots = individual states)",
             fontsize=11)
out = FIG_DIR / "boxplots_panel.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"wrote {out}")


# ---------------------------------------------------------------------------
# Figure 3: NC 3-panel map
# ---------------------------------------------------------------------------
def load_plan_gdf(path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    if "district_id" not in gdf.columns:
        for col in ("cd119_district", "DISTRICT", "district"):
            if col in gdf.columns:
                gdf = gdf.rename(columns={col: "district_id"})
                break
    gdf["district_id"] = gdf["district_id"].astype(int)
    return gdf


nc_plans = [
    ("Enacted (119th)\nEG=+0.20, pop_dev=0.66%", REPO / "data" / "nc_enacted.geojson"),
    ("Cascade\nDBS=0.811, pop_dev=10.27%‡", REPO / "out" / "nc_cascade" / "map.geojson"),
    ("DualBalance\nDBS=0.753, pop_dev=0.11%", REPO / "out" / "nc_dualbalance" / "map.geojson"),
]

available = [(lbl, p) for lbl, p in nc_plans if p.exists()]
if available:
    fig, axes = plt.subplots(1, len(available), figsize=(5.5 * len(available), 6))
    if len(available) == 1:
        axes = [axes]
    cmap = plt.get_cmap("tab20")
    n_nc = 14
    for ax, (label, path) in zip(axes, available):
        gdf = load_plan_gdf(path)
        dissolved = gdf.dissolve(by="district_id").sort_index()
        colors = [cmap(i / max(n_nc - 1, 1)) for i in range(len(dissolved))]
        dissolved.plot(ax=ax, color=colors, edgecolor="white", linewidth=0.5)
        ax.set_title(label, fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.suptitle("North Carolina: 14 congressional districts\n"
                 "‡ Cascade violates Karcher (pop_dev_max=10.27%); legally non-viable",
                 fontsize=11)
    fig.tight_layout()
    out = FIG_DIR / "nc_comparison.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")
else:
    print("NC plans not found, skipping map figure")


# ---------------------------------------------------------------------------
# Figure 4: Minority-majority district scatter
# ---------------------------------------------------------------------------
db_mm = collect("minority_majority_districts", "dualbalance")
en_mm = collect("minority_majority_districts", "enacted")
common = sorted(db_mm.keys() & en_mm.keys())

minority_share: dict[str, float] = {}
for s in common:
    total = DATA[s].get("dualbalance", {}).get("vap_total")
    white = DATA[s].get("dualbalance", {}).get("vap_nhwhite")
    if total and white and total > 0:
        minority_share[s] = 1.0 - white / total

db_vals = [db_mm[s] for s in common]
en_vals = [en_mm[s] for s in common]
c_vals = [minority_share.get(s, 0.3) for s in common]

fig, ax = plt.subplots(figsize=(7, 7))
sc = ax.scatter(en_vals, db_vals, c=c_vals, cmap="YlOrRd",
                s=65, edgecolors="black", linewidths=0.5, zorder=3, vmin=0, vmax=0.6)
cb = plt.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
cb.set_label("Statewide minority VAP share", fontsize=9)

lim = max(max(db_vals), max(en_vals)) + 1.5
ax.plot([0, lim], [0, lim], "k--", linewidth=1, alpha=0.5, label="y = x")
ax.set_xlim(-0.5, lim)
ax.set_ylim(-0.5, lim)

for s in common:
    if abs(db_mm[s] - en_mm[s]) >= 1:
        ax.annotate(s, (en_mm[s], db_mm[s]),
                    textcoords="offset points", xytext=(5, 4), fontsize=7.5)

ax.set_xlabel("Enacted plan: majority-minority districts", fontsize=11)
ax.set_ylabel("DualBalance: majority-minority districts", fontsize=11)
ax.set_title(f"Minority-majority districts: DualBalance vs enacted ({len(common)} states)\n"
             "Above diagonal: DualBalance creates more MMDs (race-blind algorithm).",
             fontsize=10)
ax.legend(fontsize=9)
fig.tight_layout()
out = FIG_DIR / "race_scatter.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"wrote {out}")

print("done")
