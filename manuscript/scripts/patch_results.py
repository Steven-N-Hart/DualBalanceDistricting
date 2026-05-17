"""Replace all placeholders in results.tex with real content."""

from pathlib import Path
import json
import numpy as np
from dualbalance.states import STATE_INFO

REPO = Path(__file__).resolve().parents[2]
TEX = REPO / "manuscript" / "sections" / "results.tex"
TABLES = (REPO / "out" / "tables_latex.txt").read_text()
TABLE1, TABLE2 = TABLES.split("\n\n", 1)

DATA = json.load(open(REPO / "out" / "compare_all_summary.json"))
states = sorted(DATA.keys())

# ── Congress numbers ────────────────────────────────────────────────────────
total_seats = sum(STATE_INFO[s]["n_seats"] for s in states)
seat_r = {p: sum(DATA[s].get(p, {}).get("seats_R", 0) or 0 for s in states) for p in ["dualbalance","enacted"]}
seat_d = {p: sum(DATA[s].get(p, {}).get("seats_D", 0) or 0 for s in states) for p in ["dualbalance","enacted"]}
prop_r = sum(STATE_INFO[s]["n_seats"] * (DATA[s].get("enacted",{}).get("statewide_share_R") or 0) for s in states)

db_r, db_d = seat_r["dualbalance"], seat_d["dualbalance"]
en_r, en_d = seat_r["enacted"], seat_d["enacted"]
total_counted = db_r + db_d

# ── Build replacement text ──────────────────────────────────────────────────
congress_para = rf"""
Across the {len(states)} states for which TIGER 2020PL VTD data are available,
totalling {total_seats} of the 435 House seats (California, Hawaii, and Oregon
are excluded; see \S\ref{{sec:discussion}}), DualBalance produces
{db_r}~R seats and {db_d}~D seats. The enacted 119\textsuperscript{{th}}-Congress
plan produces {en_r}~R and {en_d}~D across the same states. A proportional
baseline derived from the 2020 statewide two-party presidential returns
implies approximately {prop_r:.0f}~R seats; DualBalance sits
{abs(db_r - prop_r):.0f}~seats {'above' if db_r > prop_r else 'below'} that
baseline, the enacted plan {abs(en_r - prop_r):.0f}~seats above it. The
six-seat difference between DualBalance and enacted (${en_r}-{db_r}={en_r-db_r}$~R)
is a description of the partition, not a design choice: DualBalance reads
no partisan data. The full per-state breakdown (seats R/D, statewide R share,
all four algorithms) appears in Supplementary Table~S1. Caveats: 2020
presidential returns proxy for House votes, state-level ticket-splitting is
ignored, and results for the excluded states would require block-group-level
inputs.
""".strip()

# ── Read the current tex ────────────────────────────────────────────────────
src = TEX.read_text(encoding="utf-8")

# Replacement 1: Table 1 placeholder block
old1 = (
    "% -----------------------------------------------------------------------\n"
    "% TABLE 1: Per-state DualBalance results (50 rows)\n"
    "% -----------------------------------------------------------------------\n"
    r"\begin{table}[htbp]" + "\n"
    r"\centering" + "\n"
)
# Find the full block (from the comment to \end{table})
start1 = src.index("% TABLE 1: Per-state DualBalance results")
end1 = src.index(r"\end{table}", start1) + len(r"\end{table}")
src = src[:start1] + TABLE1 + "\n" + src[end1:]

# Replacement 2: Table 2 placeholder block
start2 = src.index("% TABLE 2: Aggregate algorithm comparison")
end2 = src.index(r"\end{table}", start2) + len(r"\end{table}")
src = src[:start2] + TABLE2 + "\n" + src[end2:]

# Replacement 3: Figure 1 (headline EG)
fig1_new = (
    "% Figure 1: Headline EG\n"
    r"\begin{figure}[htbp]" + "\n"
    r"\centering" + "\n"
    r"\includegraphics[width=\textwidth]{headline_eg.png}" + "\n"
    r"\caption{Partisan fairness across all " + str(len(states)) + r" available states, sorted by enacted" + "\n"
    r"$|\mathrm{EG}|$ (worst-gerrymandered on the left). DualBalance (blue) vs.\\" + "\n"
    r"enacted 119th-Congress plan (gray). Red dashed line: $|\mathrm{EG}|=0.07$" + "\n"
    r"gerrymander threshold~\cite{stephanopoulosmcghee2015}. States CA, HI, OR" + "\n"
    r"lacked TIGER 2020PL VTD boundaries and are excluded ($\dagger$).}" + "\n"
    r"\label{fig:headline-eg}" + "\n"
    r"\end{figure}"
)
start3 = src.index("% FIGURE 1: Headline EG comparison")
end3 = src.index(r"\end{figure}", start3) + len(r"\end{figure}")
src = src[:start3] + fig1_new + "\n" + src[end3:]

# Replacement 4: Figure 2 (boxplots)
fig2_new = (
    "% Figure 2: Boxplot panel\n"
    r"\begin{figure}[htbp]" + "\n"
    r"\centering" + "\n"
    r"\includegraphics[width=\textwidth]{boxplots_panel.png}" + "\n"
    r"\caption{Cross-state comparison of four algorithms on key metrics (" + str(len(states)) + r" states)." + "\n"
    r"Each box spans the interquartile range; dots are individual states; diamonds are means." + "\n"
    r"\textbf{Panel A}: DualBalance Score (higher = better)." + "\n"
    r"\textbf{Panel B}: maximum per-district population deviation, log scale;" + "\n"
    r"dashed line at the \emph{Karcher} threshold (0.05\,\%)." + "\n"
    r"\textbf{Panel C}: $|\mathrm{EG}|$ (lower = fairer); dashed line at 0.07." + "\n"
    r"\textbf{Panel D}: Polsby-Popper compactness (mean per state); DualBalance" + "\n"
    r"is structurally less compact than enacted plans because radial slices are" + "\n"
    r"not blob-shaped.}" + "\n"
    r"\label{fig:boxplots}" + "\n"
    r"\end{figure}"
)
start4 = src.index("% FIGURE 2: Four-panel boxplots")
end4 = src.index(r"\end{figure}", start4) + len(r"\end{figure}")
src = src[:start4] + fig2_new + "\n" + src[end4:]

# Replacement 5: Figure 3 (race scatter)
fig3_new = (
    "% Figure 3: Minority-majority district scatter\n"
    r"\begin{figure}[htbp]" + "\n"
    r"\centering" + "\n"
    r"\includegraphics[width=0.75\textwidth]{race_scatter.png}" + "\n"
    r"\caption{Minority-majority district count: DualBalance vs.\ enacted" + "\n"
    r"119th-Congress plan. Each point is one state; the diagonal is $y = x$." + "\n"
    r"Points above the line indicate DualBalance produces more majority-minority" + "\n"
    r"districts than the enacted map; points below indicate fewer. Color encodes" + "\n"
    r"statewide minority VAP share (darker = larger minority population). DualBalance" + "\n"
    r"is race-blind; where it produces more MMDs than the enacted plan, the effect" + "\n"
    r"is geographic, not by design. States with large differences are labeled.}" + "\n"
    r"\label{fig:race-scatter}" + "\n"
    r"\end{figure}"
)
start5 = src.index("% FIGURE 3: Minority-majority district scatter")
end5 = src.index(r"\end{figure}", start5) + len(r"\end{figure}")
src = src[:start5] + fig3_new + "\n" + src[end5:]

# Replacement 6: Figure 4 (NC maps)
fig4_new = (
    "% Figure 4: NC three-panel map\n"
    r"\begin{figure}[htbp]" + "\n"
    r"\centering" + "\n"
    r"\includegraphics[width=\textwidth]{nc_comparison.png}" + "\n"
    r"\caption{North Carolina congressional districts under three plans (14 seats," + "\n"
    r"2020 PL 94-171). \textbf{Left:} enacted 119th-Congress plan, with the" + "\n"
    r"Efficiency Gap of $+0.20$ that gave rise to \textit{Rucho v.~Common Cause}~\cite{rucho2019}." + "\n"
    r"\textbf{Center:} Cascade plan, which scores better on DBS ($0.811$ vs.\ $0.769$ enacted)" + "\n"
    r"but violates \emph{Karcher} at $\mathrm{pop\_dev\_max}=10.27\,\%$ and cannot legally be enacted." + "\n"
    r"\textbf{Right:} DualBalance plan, \emph{Karcher}-compliant ($0.11\,\%$) and" + "\n"
    r"reducing EG to $+0.063$ with no political input.}" + "\n"
    r"\label{fig:nc-maps}" + "\n"
    r"\end{figure}"
)
start6 = src.index("% FIGURE 4: NC three-panel map")
end6 = src.index(r"\end{figure}", start6) + len(r"\end{figure}")
src = src[:start6] + fig4_new + "\n" + src[end6:]

# Replacement 7: Congress placeholder paragraph
old_congress = (
    r"\textbf{[PLACEHOLDER, $\sim$150 words.]} Aggregate seats\_R / seats\_D" + "\n"
    "summed across all available states under DualBalance, Cascade,\n"
    "BDistricting, and the enacted plan, plus a proportional-vote baseline\n"
    "derived from the 2020 statewide two-party presidential returns. The\n"
    "question, ``if every state used DualBalance, what is the partisan\n"
    "composition of the House?'', is answered here with full caveats: 2020\n"
    "presidential returns proxy for House votes, CA/HI/OR are excluded for\n"
    "lack of VTD data, and single-seat states are unchanged under any\n"
    "algorithm. The full per-state breakdown (seats R/D, statewide R share,\n"
    "all four algorithms) appears in Supplementary Table~S1."
)
if old_congress in src:
    src = src.replace(old_congress, congress_para)
else:
    print("WARNING: Congress placeholder not found verbatim; check manually")

TEX.write_text(src, encoding="utf-8")
print(f"Updated {TEX}")
print(f"\nKey numbers in Congress paragraph:")
print(f"  {len(states)} states, {total_seats} seats")
print(f"  DualBalance: R={db_r} D={db_d}")
print(f"  Enacted:     R={en_r} D={en_d}")
print(f"  Proportional baseline: ~{prop_r:.0f} R")
