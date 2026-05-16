"""Block-scale tractability test on IA — instrumented per-step.

Replicates generate_plan's pipeline with per-phase timing so we can
see where time goes at 175k-block scale.
"""

from __future__ import annotations

import time

import numpy as np


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


T0 = time.time()
log("import dualbalance…")
from dualbalance.io import load_units
from dualbalance.districting import (
    _assign,
    _bounding_box_diagonal,
    _compute_targets,
    _repair_contiguity,
)
from dualbalance.seeds import place_seeds
from dualbalance.types import Plan

log(f"imports done in {time.time() - T0:.1f}s")

t = time.time()
log("LOAD: load_units (reads geojson, reprojects, attaches area, sorts)…")
units = load_units(
    "data/ia_block.geojson",
    id_column="GEOID20",
    pop_column="population",
    county_column="county",
)
log(f"LOAD: {len(units):,} units in {time.time() - t:.1f}s")

t = time.time()
log("SORT: stable sort by unit_id…")
units_sorted = units.sort_values("unit_id", kind="mergesort").reset_index(drop=True)
log(f"SORT: in {time.time() - t:.1f}s")

t = time.time()
log("TARGETS: per-district pop+area targets…")
targets = _compute_targets(units_sorted, 4)
norm = _bounding_box_diagonal(units_sorted)
log(f"TARGETS: pop={targets.population:,.0f} area={targets.area:.3e} norm={norm:.3e} ({time.time() - t:.1f}s)")

t = time.time()
log("CENTROIDS: compute per-unit centroid coords…")
centroids = units_sorted.geometry.centroid
cx = np.asarray(centroids.x, dtype=float)
cy = np.asarray(centroids.y, dtype=float)
pops = np.asarray(units_sorted["population"], dtype=float)
unit_ids: list[str] = units_sorted["unit_id"].tolist()
log(f"CENTROIDS: in {time.time() - t:.1f}s")

t = time.time()
log("SEEDS: radial placement…")
seeds = place_seeds(units_sorted, 4)
seeds_repr = seeds.tolist() if hasattr(seeds, "tolist") else list(seeds)
log(f"SEEDS: {seeds_repr} ({time.time() - t:.1f}s)")

t = time.time()
log("ASSIGN: capacitated first-fit (sort all (unit,seed) pairs by distance, then assign)…")
assignment = _assign(cx, cy, pops, unit_ids, seeds, targets, norm)
log(f"ASSIGN: in {time.time() - t:.1f}s")

t = time.time()
log("REPAIR: building dual graph + contiguity repair pass…")
assignment, repair_iters, contiguous = _repair_contiguity(
    assignment, units_sorted, seeds, targets, norm, 4
)
log(f"REPAIR: contiguous={contiguous} iters={repair_iters} ({time.time() - t:.1f}s)")

prism = Plan(
    assignment=assignment,
    n_districts=4,
    geography="block",
    metadata={"repair_iterations": repair_iters, "contiguous": contiguous},
)

t = time.time()
log("SCORE: PRISM init scoring…")
from dualbalance.scoring import score_plan

prism_metrics = score_plan(prism, units)
log(f"SCORE: DBS={prism_metrics['dualbalance_score']:.4f} "
    f"pop_dev_max={prism_metrics['pop_deviation_max']:.4f} "
    f"({time.time() - t:.1f}s)")

t = time.time()
log("OPT: optimize_dbs with pop_dev_max_tolerance=0.0005…")
from dualbalance.optimize import optimize_dbs

opt = optimize_dbs(prism, units, pop_dev_max_tolerance=0.0005, max_passes=100000, progress_every=25)
opt_time = time.time() - t
opt_metrics = score_plan(opt, units)
mt = opt.metadata.get("optimize_dbs_tighten_moves", 0)
md = opt.metadata.get("optimize_dbs_dbs_moves", 0)
chain_inv = opt.metadata.get("optimize_dbs_chain_invocations", 0)
chain_mv = opt.metadata.get("optimize_dbs_chain_moves", 0)
log(f"OPT: DBS={opt_metrics['dualbalance_score']:.4f} "
    f"pop_dev_max={opt_metrics['pop_deviation_max']:.6f} "
    f"tight={mt} chain_calls={chain_inv} chain_moves={chain_mv} dbs={md} "
    f"({opt_time:.1f}s = {opt_time / 60:.1f}min)")

log(f"TOTAL elapsed: {(time.time() - T0) / 60:.1f}min")
