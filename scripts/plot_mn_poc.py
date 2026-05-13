"""Render the Minnesota PoC plan to a static PNG figure.

Produces ``docs/figures/mn_poc_districts.png``, a two-panel image:

- Top: choropleth of all VTDs colored by ``district_id`` (8 colors).
- Bottom: per-district population and area bars vs. the target line.

The figure intentionally uses only ``geopandas`` + ``matplotlib`` (already
runtime dependencies via geopandas) so it can be reproduced with no extra
packages. Inputs default to the canonical run at ``out/mn_a/`` but can be
overridden with ``--plan`` / ``--metrics`` / ``--out``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=Path("out/mn_a/map.geojson"))
    parser.add_argument(
        "--metrics", type=Path, default=Path("out/mn_a/metrics.json")
    )
    parser.add_argument(
        "--out", type=Path, default=Path("docs/figures/mn_poc_districts.png")
    )
    args = parser.parse_args(argv)

    gdf = gpd.read_file(args.plan)
    metrics = json.loads(args.metrics.read_text(encoding="utf-8"))

    fig = plt.figure(figsize=(11, 13))
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 1.2], hspace=0.25)

    # --- choropleth ---
    ax_map = fig.add_subplot(gs[0])
    gdf.plot(
        column="district_id",
        cmap="tab10",
        categorical=True,
        linewidth=0.05,
        edgecolor="black",
        legend=True,
        legend_kwds={"title": "District", "loc": "lower right", "fontsize": 8},
        ax=ax_map,
    )
    ax_map.set_title(
        "Minnesota DualBalance PoC — 8 districts on 4,110 VTDs\n"
        f"(DualBalance Score = {metrics['dualbalance_score']:.4f}; "
        f"synthetic uniform population)",
        fontsize=12,
    )
    ax_map.set_axis_off()

    # --- per-district pop + area bars ---
    ax_bars = fig.add_subplot(gs[1])
    districts = sorted(metrics["districts"], key=lambda d: d["district_id"])
    ids = [d["district_id"] for d in districts]
    pops = [d["population"] for d in districts]
    areas_km2 = [d["area"] / 1e6 for d in districts]  # m² -> km²
    p_target = metrics["targets"]["population"]
    a_target_km2 = metrics["targets"]["area"] / 1e6

    x = np.arange(len(ids))
    width = 0.4
    ax_bars.bar(x - width / 2, pops, width=width, color="#3b82f6", label="population")
    ax_bars.axhline(p_target, color="#3b82f6", linestyle="--", linewidth=1, alpha=0.5)
    ax_bars.set_xlabel("District")
    ax_bars.set_ylabel("Population", color="#3b82f6")
    ax_bars.tick_params(axis="y", labelcolor="#3b82f6")
    ax_bars.set_xticks(x)
    ax_bars.set_xticklabels(ids)

    ax_area = ax_bars.twinx()
    ax_area.bar(x + width / 2, areas_km2, width=width, color="#10b981", label="area (km²)")
    ax_area.axhline(a_target_km2, color="#10b981", linestyle="--", linewidth=1, alpha=0.5)
    ax_area.set_ylabel("Area (km²)", color="#10b981")
    ax_area.tick_params(axis="y", labelcolor="#10b981")

    ax_bars.set_title(
        "Per-district population (left axis) and area (right axis).  "
        f"Targets shown as dashed lines.  P*={int(p_target):,};  A*={int(a_target_km2):,} km²",
        fontsize=10,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=120, bbox_inches="tight")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
