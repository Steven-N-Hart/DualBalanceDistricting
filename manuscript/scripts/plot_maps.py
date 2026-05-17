"""Side-by-side district maps: Enacted vs Cascade vs DualBalance.

For each PoC state, load the three plans (all VTD-level) and plot
them in a 1x3 panel. Saves to out/maps_<state>.png.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]
STATES = [("IA", 4), ("MA", 9), ("MN", 8), ("NC", 14), ("WI", 8), ("TX", 38)]

# Plan label -> path template + load strategy.
PLANS = [
    ("Enacted (119th Congress)", "data/{s}_enacted.geojson"),
    ("Cascade (Iowa-LSA style)", "out/{s}_cascade/map.geojson"),
    ("DualBalance (this work)",  "out/{s}_dualbalance/map.geojson"),
]


def load_plan_gdf(path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    # Both enacted and the optimizer outputs use 'district_id'.
    if "district_id" not in gdf.columns:
        # Fall back to cd119 column if the enacted file used that.
        for col in ("cd119_district", "DISTRICT", "district"):
            if col in gdf.columns:
                gdf = gdf.rename(columns={col: "district_id"})
                break
    gdf["district_id"] = gdf["district_id"].astype(int)
    return gdf


def plot_state(state: str, n: int) -> None:
    state_lc = state.lower()
    plans_data = []
    for label, tmpl in PLANS:
        path = REPO / tmpl.format(s=state_lc)
        if not path.exists():
            print(f"  skipping {label}: {path} missing")
            continue
        gdf = load_plan_gdf(path)
        plans_data.append((label, gdf))

    if not plans_data:
        return

    fig, axes = plt.subplots(1, len(plans_data),
                             figsize=(5 * len(plans_data), 6))
    if len(plans_data) == 1:
        axes = [axes]

    # Same color palette across all panels (district_id may not align
    # across plans semantically, but a shared palette keeps the
    # visualization legible).
    cmap = plt.get_cmap("tab20" if n <= 20 else "gist_ncar")
    norm = lambda d: d / max(n - 1, 1)

    for ax, (label, gdf) in zip(axes, plans_data):
        # Dissolve units by district to draw cleaner district polygons.
        try:
            dissolved = gdf.dissolve(by="district_id", aggfunc="first")
        except Exception:
            dissolved = gdf
        # Sort by district_id for stable color assignment.
        dissolved = dissolved.sort_index()
        colors = [cmap(norm(int(d))) for d in dissolved.index]
        dissolved.plot(ax=ax, color=colors, edgecolor="black", linewidth=0.4)
        ax.set_title(label, fontsize=11)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    fig.suptitle(f"{state}: {n} congressional districts", fontsize=13)
    fig.tight_layout()
    out = REPO / "out" / f"maps_{state_lc}.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


for state, n in STATES:
    print(f"=== {state} ===")
    plot_state(state, n)
print("done")
