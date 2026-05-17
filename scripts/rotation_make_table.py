"""Generate LaTeX supplementary table S2 from rotation_sweep.json."""

from __future__ import annotations
import json
from pathlib import Path

ROOT  = Path(__file__).resolve().parent.parent
SWEEP = ROOT / "results" / "rotation_sweep.json"
OUT   = ROOT / "manuscript" / "sections" / "rotation_table.tex"


def main() -> None:
    with open(SWEEP) as f:
        data = json.load(f)

    lines = [
        r"\begin{longtable}{l r cccc cc}",
        r"\caption{Rotation sensitivity: summary statistics across 12 equally-spaced",
        r"anchor angles $\theta_k = 2\pi k/12$ for all 41 states. DBS and $|\mathrm{EG}|$",
        r"are computed from the core radial pipeline (no population tightening).",
        r"Seat counts projected by simple plurality on available precinct-level vote data.}",
        r"\label{tab:rotation-sensitivity}\\",
        r"\toprule",
        r"State & $N$ & \multicolumn{2}{c}{DBS} & \multicolumn{2}{c}{$|\mathrm{EG}|$} & \multicolumn{2}{c}{Seats R} \\",
        r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(lr){7-8}",
        r"& & mean & std & mean & std & min & max \\",
        r"\midrule",
        r"\endfirsthead",
        r"\multicolumn{8}{c}{\small\textit{(continued)}}\\",
        r"\toprule",
        r"State & $N$ & \multicolumn{2}{c}{DBS} & \multicolumn{2}{c}{$|\mathrm{EG}|$} & \multicolumn{2}{c}{Seats R} \\",
        r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(lr){7-8}",
        r"& & mean & std & mean & std & min & max \\",
        r"\midrule",
        r"\endhead",
        r"\midrule\multicolumn{8}{r}{\small\textit{(continued)}}\\\endfoot",
        r"\bottomrule\endlastfoot",
    ]

    for row in sorted(data, key=lambda x: x["state"]):
        s = row["summary"]
        state = row["state"]
        n     = row["n"]
        dbs_m = f"{s['dbs_mean']:.3f}" if s['dbs_mean'] is not None else "---"
        dbs_s = f"{s['dbs_std']:.4f}" if s['dbs_std'] is not None else "---"
        eg_m  = f"{abs(s['eg_mean']):.3f}" if s['eg_mean'] is not None else "---"
        eg_s  = f"{s['eg_std']:.4f}" if s['eg_std'] is not None else "---"
        sr_mn = str(s['seats_r_min']) if s['seats_r_min'] is not None else "---"
        sr_mx = str(s['seats_r_max']) if s['seats_r_max'] is not None else "---"
        lines.append(
            f"{state} & {n} & {dbs_m} & {dbs_s} & {eg_m} & {eg_s} & {sr_mn} & {sr_mx} \\\\"
        )

    lines.append(r"\end{longtable}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
