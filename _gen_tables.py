"""Generate LaTeX table content for the two placeholder tables in results.tex.

Prints two blocks:
  1. tab:multistate-dbs  -- per-state DBS + pop_dev_max (41 rows)
  2. tab:aggregate-comparison -- summary medians + counts (6 rows)

Run: python _gen_tables.py > /tmp/tables.tex
"""

from __future__ import annotations

import json
import numpy as np
from pathlib import Path

REPO = Path(__file__).resolve().parent
DATA = json.load(open(REPO / "out" / "compare_all_summary.json"))
STATES = sorted(DATA.keys())
PLANS = ["dualbalance", "cascade", "bdistricting", "enacted"]
KARCHER = 0.0005  # 0.05%
REYNOLDS = 0.005  # 0.5% -- legally non-viable threshold

from dualbalance.states import STATE_INFO

STATE_NAMES = {
    "AL": "Alabama", "AR": "Arkansas", "AZ": "Arizona", "CO": "Colorado",
    "CT": "Connecticut", "FL": "Florida", "GA": "Georgia", "IA": "Iowa",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "MA": "Massachusetts", "MD": "Maryland",
    "ME": "Maine", "MI": "Michigan", "MN": "Minnesota", "MO": "Missouri",
    "MS": "Mississippi", "MT": "Montana", "NC": "North Carolina", "NE": "Nebraska",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NV": "Nevada",
    "NY": "New York", "OH": "Ohio", "OK": "Oklahoma", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VA": "Virginia", "WA": "Washington", "WI": "Wisconsin",
    "WV": "West Virginia",
}


def get(state: str, plan: str, metric: str):
    return DATA.get(state, {}).get(plan, {}).get(metric)


# ---------------------------------------------------------------------------
# Table 1: per-state DBS + pop_dev_max
# ---------------------------------------------------------------------------
lines = []
lines.append(r"\begin{longtable}{l r cccc rr}")
lines.append(r"\caption{Per-state DualBalance Score and maximum population")
lines.append(r"deviation for all " + str(len(STATES)) + r" states with TIGER 2020PL VTD data.")
lines.append(r"\textbf{Bold} marks the highest DBS per row.")
lines.append(r"$\ddagger$ marks Cascade plans where $\mathrm{pop\_dev\_max} > 0.5\,\%$")
lines.append(r"(\emph{Reynolds v.~Sims} non-compliant; legally non-viable).}")
lines.append(r"\label{tab:multistate-dbs}\\")
lines.append(r"\toprule")
lines.append(r"State & $N$ & \multicolumn{4}{c}{DualBalance Score} & \multicolumn{2}{c}{$\mathrm{pop\_dev\_max}$} \\")
lines.append(r"\cmidrule(lr){3-6}\cmidrule(lr){7-8}")
lines.append(r" & & DB & Cascade & BDist & Enacted & DB & Cascade \\")
lines.append(r"\midrule")
lines.append(r"\endfirsthead")
lines.append(r"\multicolumn{8}{c}{\small\textit{(continued from previous page)}}\\[2pt]")
lines.append(r"\toprule")
lines.append(r"State & $N$ & \multicolumn{4}{c}{DualBalance Score} & \multicolumn{2}{c}{$\mathrm{pop\_dev\_max}$} \\")
lines.append(r"\cmidrule(lr){3-6}\cmidrule(lr){7-8}")
lines.append(r" & & DB & Cascade & BDist & Enacted & DB & Cascade \\")
lines.append(r"\midrule")
lines.append(r"\endhead")
lines.append(r"\midrule\multicolumn{8}{r}{\small\textit{(continued on next page)}}\\\endfoot")
lines.append(r"\bottomrule\endlastfoot")

for s in STATES:
    n = STATE_INFO[s]["n_seats"]
    dbs = {p: get(s, p, "dualbalance_score") for p in PLANS}
    pop = {p: get(s, p, "pop_deviation_max") for p in PLANS}

    valid = [v for v in dbs.values() if v is not None]
    best = max(valid) if valid else None

    def fmt_dbs(v, plan):
        if v is None:
            return "---"
        txt = f"{v:.3f}"
        if best is not None and abs(v - best) < 1e-9:
            txt = r"\textbf{" + txt + r"}"
        if plan == "cascade" and pop.get("cascade") and pop["cascade"] > REYNOLDS:
            txt += r"$^{\ddagger}$"
        return txt

    def fmt_pop(v, plan):
        if v is None:
            return "---"
        pct = v * 100
        txt = f"{pct:.2f}\\%"
        if plan == "cascade" and v > REYNOLDS:
            txt = r"\textit{" + txt + r"}$^{\ddagger}$"
        return txt

    row = (
        STATE_NAMES.get(s, s),
        str(n),
        fmt_dbs(dbs["dualbalance"], "dualbalance"),
        fmt_dbs(dbs["cascade"], "cascade"),
        fmt_dbs(dbs["bdistricting"], "bdistricting"),
        fmt_dbs(dbs["enacted"], "enacted"),
        fmt_pop(pop["dualbalance"], "dualbalance"),
        fmt_pop(pop["cascade"], "cascade"),
    )
    lines.append(" & ".join(row) + r" \\")

lines.append(r"\end{longtable}")

TABLE1 = "\n".join(lines)


# ---------------------------------------------------------------------------
# Table 2: aggregate comparison
# ---------------------------------------------------------------------------
def med(metric, plan, absolute=False):
    vals = []
    for s in STATES:
        v = get(s, plan, metric)
        if v is not None:
            vals.append(abs(v) if absolute else v)
    return np.median(vals) if vals else float("nan")


# Counts
karcher_count = {p: sum(1 for s in STATES if (get(s, p, "pop_deviation_max") or 1) <= KARCHER)
                 for p in PLANS}
beats_enacted = {p: sum(1 for s in STATES
                        if (get(s, p, "dualbalance_score") or 0) >
                           (get(s, "enacted", "dualbalance_score") or 0))
                 for p in PLANS}

N = len(STATES)

rows_agg = [
    ("DBS (median)",            [f"{med('dualbalance_score', p):.3f}" for p in PLANS], None),
    (r"$\mathrm{pop\_dev\_max}$ (median)",
     [f"{med('pop_deviation_max', p)*100:.1f}\\%" for p in PLANS], 1),
    (r"At \emph{Karcher} ($\leq 0.05\,\%$)",
     [f"{karcher_count[p]}/{N}" for p in PLANS], None),
    ("Beats enacted DBS",
     [f"{beats_enacted[p]}/{N}" if p != 'enacted' else '---' for p in PLANS], None),
    (r"$|\mathrm{EG}|$ (median)",
     [f"{med('efficiency_gap', p, absolute=True):.3f}" for p in PLANS], None),
    (r"Polsby-Popper mean (median)",
     [f"{med('polsby_popper_mean', p):.3f}" for p in PLANS], None),
]

# Bold the best value per row
def best_idx(row_vals, row_idx):
    # Rows 0,3,4 (DBS, beats_enacted, -|EG|): higher is better for DB/Casc/BD vs Enacted
    # Row 1 (pop_dev): lower is better
    # Row 2 (Karcher): higher is better
    # Row 5 (PP): higher is better
    # Skip rows with '---'
    try:
        parsed = []
        for v in row_vals:
            if v == "---":
                parsed.append(float("-inf"))
            elif "%" in v:
                parsed.append(float(v.replace("\\%","").strip()))
            elif "/" in v:
                num, den = v.split("/")
                parsed.append(float(num) / float(den))
            else:
                parsed.append(float(v))
        if row_idx == 1:  # pop_dev: lower is better
            parsed = [-x for x in parsed]
        if row_idx == 4:  # |EG|: lower is better
            parsed = [-x for x in parsed]
        best = max(parsed)
        return [i for i, x in enumerate(parsed) if abs(x - best) < 1e-9]
    except Exception:
        return []

agg_lines = []
agg_lines.append(r"\begin{table}[htbp]")
agg_lines.append(r"\centering")
agg_lines.append(r"\caption{Aggregate algorithm comparison across all " + str(N) +
                 r" available states. \textbf{Bold} marks the best value in each row.")
agg_lines.append(r"``At \emph{Karcher}'' counts states where $\mathrm{pop\_dev\_max} \leq 0.05\,\%$.")
agg_lines.append(r"``Beats enacted DBS'' counts states where the algorithm's DualBalance Score")
agg_lines.append(r"exceeds the enacted plan's. Enacted plan cannot beat itself.}")
agg_lines.append(r"\label{tab:aggregate-comparison}")
agg_lines.append(r"\small")
agg_lines.append(r"\begin{tabular}{l rrrr}")
agg_lines.append(r"\toprule")
agg_lines.append(r"Metric & DualBalance & Cascade & BDistricting & Enacted \\")
agg_lines.append(r"\midrule")

for ri, (label, vals, _) in enumerate(rows_agg):
    best_idxs = best_idx(vals, ri)
    formatted = []
    for i, v in enumerate(vals):
        if i in best_idxs and v != "---":
            formatted.append(r"\textbf{" + v + r"}")
        else:
            formatted.append(v)
    agg_lines.append(label + " & " + " & ".join(formatted) + r" \\")

agg_lines.append(r"\bottomrule")
agg_lines.append(r"\end{tabular}")
agg_lines.append(r"\end{table}")

TABLE2 = "\n".join(agg_lines)

# Write both tables to a file for inspection
out = REPO / "out" / "tables_latex.txt"
out.write_text(TABLE1 + "\n\n" + TABLE2)
print(f"wrote {out}")

# Print quick summary
print(f"\n41-state summary:")
print(f"  DualBalance beats enacted DBS: {beats_enacted['dualbalance']}/41")
print(f"  DualBalance at Karcher:        {karcher_count['dualbalance']}/41")
print(f"  Cascade at Karcher:            {karcher_count['cascade']}/41")
print(f"  BDistricting at Karcher:       {karcher_count['bdistricting']}/41")
print(f"  Enacted at Karcher:            {karcher_count['enacted']}/41")
