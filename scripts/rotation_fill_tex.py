"""Parse rotation_sweep.json and fill \DROT{} placeholders in results.tex.

Usage:
    python scripts/rotation_fill_tex.py
"""

from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SWEEP = ROOT / "results" / "rotation_sweep.json"
TEX   = ROOT / "manuscript" / "sections" / "results.tex"


def main() -> None:
    with open(SWEEP) as f:
        data = json.load(f)

    dbs_stds  = [s["summary"]["dbs_std"]  for s in data if s["summary"]["dbs_std"]  is not None]
    eg_stds   = [s["summary"]["eg_std"]   for s in data if s["summary"]["eg_std"]   is not None]
    seat_swings = []
    seat_variable = 0
    for s in data:
        mn = s["summary"]["seats_r_min"]
        mx = s["summary"]["seats_r_max"]
        if mn is not None and mx is not None:
            swing = mx - mn
            seat_swings.append(swing)
            if swing >= 1:
                seat_variable += 1

    import numpy as np
    vals = {
        "dbs_std_median": f"{float(np.median(dbs_stds)):.4f}",
        "dbs_std_min":    f"{float(np.min(dbs_stds)):.4f}",
        "dbs_std_max":    f"{float(np.max(dbs_stds)):.4f}",
        "eg_std_median":  f"{float(np.median(eg_stds)):.4f}",
        "eg_std_min":     f"{float(np.min(eg_stds)):.4f}",
        "eg_std_max":     f"{float(np.max(eg_stds)):.4f}",
        "seat_variable_count": str(seat_variable),
        "seat_swing_min": str(min(seat_swings)) if seat_swings else "0",
        "seat_swing_max": str(max(seat_swings)) if seat_swings else "0",
    }
    print("Summary stats:")
    for k, v in vals.items():
        print(f"  {k}: {v}")

    tex = TEX.read_text(encoding="utf-8")
    for key, value in vals.items():
        # LaTeX escapes underscores in text mode as \_
        tex_key = key.replace("_", r"\_")
        tex = tex.replace(f"\\DROT{{{tex_key}}}", value)

    # Verify no placeholders remain
    remaining = re.findall(r"\\DROT\{[^}]+\}", tex)
    if remaining:
        print(f"WARNING: unfilled placeholders: {remaining}")

    TEX.write_text(tex, encoding="utf-8")
    print(f"Updated {TEX}")


if __name__ == "__main__":
    main()
