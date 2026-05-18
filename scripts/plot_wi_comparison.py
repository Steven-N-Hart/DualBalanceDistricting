"""Generate three-panel Wisconsin comparison figure for the manuscript.

Left:  enacted 119th-Congress plan (EG=+0.279, Whitford v. Gill context)
Center: Cascade plan (DBS=0.802, pop_dev_max=0.497%, legally non-viable)
Right:  DualBalance plan (DBS=0.695, Karcher-compliant 0.038%, EG=+0.032)
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import numpy as np

ROOT = Path(__file__).resolve().parent.parent

def load_plan(path: Path, id_col: str = "district_id") -> gpd.GeoDataFrame:
    gdf = gpd.read_file(str(path))
    if id_col not in gdf.columns and "cd119_district" in gdf.columns:
        gdf = gdf.rename(columns={"cd119_district": id_col})
    gdf[id_col] = gdf[id_col].astype(int)
    dissolved = gdf.dissolve(by=id_col).reset_index()
    return dissolved


def main() -> None:
    # Load metrics
    def m(name):
        return json.loads((ROOT / "out" / "wi_compare" / f"{name}_metrics.json").read_text())

    en_m  = m("enacted")
    cas_m = m("cascade")
    db_m  = m("dualbalance")

    # Load dissolved district geometries
    enacted  = load_plan(ROOT / "data"  / "wi_enacted.geojson",      id_col="district_id")
    cascade  = load_plan(ROOT / "out"   / "wi_cascade"  / "map.geojson")
    dualbal  = load_plan(ROOT / "out"   / "wi_dualbalance" / "map.geojson")

    # 8-color palette for 8 districts
    cmap = plt.get_cmap("tab10", 8)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5))
    fig.suptitle(
        "Wisconsin: 8 congressional districts  (2020 PL 94-171)",
        fontsize=12, y=1.01
    )

    panels = [
        (axes[0], enacted,  "district_id",
         f"Enacted (119th Congress)\n"
         f"EG = +{en_m['efficiency_gap']:.3f}   "
         f"DBS = {en_m['dualbalance_score']:.3f}   "
         f"pop_dev_max = {en_m['pop_deviation_max']:.2%}"),
        (axes[1], cascade,  "district_id",
         f"Cascade (county-priority)\n"
         f"EG = +{cas_m['efficiency_gap']:.3f}   "
         f"DBS = {cas_m['dualbalance_score']:.3f}   "
         f"pop_dev_max = {cas_m['pop_deviation_max']:.2%}‡"),
        (axes[2], dualbal,  "district_id",
         f"DualBalance (radial)\n"
         f"EG = +{db_m['efficiency_gap']:.3f}   "
         f"DBS = {db_m['dualbalance_score']:.3f}   "
         f"pop_dev_max = {db_m['pop_deviation_max']:.2%}"),
    ]

    for ax, gdf, col, title in panels:
        gdf.plot(
            column=col,
            cmap=cmap,
            categorical=True,
            linewidth=0.4,
            edgecolor="white",
            legend=False,
            ax=ax,
        )
        ax.set_axis_off()
        ax.set_title(title, fontsize=8.5, linespacing=1.5)

    axes[0].annotate(
        "Whitford v. Gill\n(SCOTUS 2018)",
        xy=(0.5, 0.05), xycoords="axes fraction",
        ha="center", fontsize=7.5, style="italic", color="#555555"
    )
    axes[1].annotate(
        "‡ violates Karcher; legally non-viable",
        xy=(0.5, 0.05), xycoords="axes fraction",
        ha="center", fontsize=7.5, color="#aa3333"
    )

    plt.tight_layout()
    out = ROOT / "manuscript" / "figures" / "wi_comparison.png"
    fig.savefig(str(out), dpi=200, bbox_inches="tight")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
