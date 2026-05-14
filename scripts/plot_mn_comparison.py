"""Render a side-by-side comparison of the DualBalance plan and the enacted
Minnesota congressional plan.

Expects each plan to live in its own directory with ``map.geojson`` +
``metrics.json``. Defaults match the directories used in the MN walkthrough.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt

PANELS_DEFAULT = [
    ("out/mn_yaml", "DualBalance (radial)"),
    ("out/mn_enacted", "Enacted MN plan (119th Congress)"),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/figures/mn_poc_comparison.png"),
    )
    args = parser.parse_args(argv)

    fig, axes = plt.subplots(1, 2, figsize=(13, 7))
    fig.suptitle(
        "Minnesota — DualBalance (radial) vs enacted (2020 PL 94-171 pop, 4,110 VTDs)",
        fontsize=13,
        y=0.995,
    )
    for ax, (folder, label) in zip(axes.flat, PANELS_DEFAULT, strict=True):
        path = Path(folder)
        gdf = gpd.read_file(path / "map.geojson")
        metrics = json.loads((path / "metrics.json").read_text())
        gdf.plot(
            column="district_id",
            cmap="tab10",
            categorical=True,
            linewidth=0.05,
            edgecolor="black",
            legend=False,
            ax=ax,
        )
        ax.set_axis_off()
        ax.set_title(
            f"{label}\n"
            f"Score = {metrics['dualbalance_score']:.4f}   "
            f"pop_dev_max = {metrics['pop_deviation_max']:.2%}   "
            f"area_dev_max = {metrics['area_deviation_max']:.0%}",
            fontsize=9.5,
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(args.out, dpi=120, bbox_inches="tight")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
