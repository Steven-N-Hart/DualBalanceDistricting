"""Block-scale optimizer initialized from VTD-Karcher plan.

Pipeline (for any state):
1. Load <state> VTD units; run full optimizer (DualBalance + Phase 1 + Phase 2)
   with Karcher tolerance.
2. Load <state> block units and reproject to the same CRS.
3. Spatial join: each block's representative point -> containing VTD ->
   inherit that VTD's district_id.
4. Run the block-scale optimizer from this initial state with Karcher
   tolerance.

Usage: python _test_block_from_vtd.py <STATE> <N_DISTRICTS>
e.g.   python _test_block_from_vtd.py IA 4
"""

from __future__ import annotations

import sys
import time

import geopandas as gpd
import pandas as pd

from dualbalance.io import EQUAL_AREA_CRS, load_units
from dualbalance.districting import generate_plan
from dualbalance.optimize import optimize_dbs
from dualbalance.scoring import score_plan
from dualbalance.types import Plan


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


KARCHER_TOL = 0.0005


def main(state: str, n_districts: int) -> int:
    state_lc = state.lower()
    T0 = time.time()
    log(f"=== STATE {state} N={n_districts} ===")

    log("LOAD: vtd…")
    t = time.time()
    vtd_units = load_units(
        f"data/{state_lc}_vtd.geojson",
        id_column="GEOID20",
        pop_column="population",
        county_column="county",
    )
    log(f"LOAD: {len(vtd_units):,} VTDs in {time.time() - t:.1f}s")

    t = time.time()
    log("DualBalance(vtd): generate seed plan…")
    vtd_prism = generate_plan(vtd_units, n_districts, geography="vtd")
    log(f"DualBalance(vtd): in {time.time() - t:.1f}s")

    t = time.time()
    log("OPT(vtd) with Karcher tolerance…")
    vtd_opt = optimize_dbs(
        vtd_prism, vtd_units,
        pop_dev_max_tolerance=KARCHER_TOL, max_passes=100000,
        progress_every=100,
    )
    log(f"OPT(vtd): in {time.time() - t:.1f}s")
    vtd_metrics = score_plan(vtd_opt, vtd_units)
    log(f"VTD result: DBS={vtd_metrics['dualbalance_score']:.4f} "
        f"pop_dev_max={vtd_metrics['pop_deviation_max']:.6f}")

    t = time.time()
    log("LOAD: blocks (raw geojson)…")
    blocks_raw = gpd.read_file(f"data/{state_lc}_block.geojson")
    log(f"LOAD: {len(blocks_raw):,} blocks in {time.time() - t:.1f}s")

    t = time.time()
    log("PROJECT: blocks + vtds to equal-area CRS…")
    blocks_proj = blocks_raw.to_crs(EQUAL_AREA_CRS)
    vtd_raw = gpd.read_file(f"data/{state_lc}_vtd.geojson").to_crs(EQUAL_AREA_CRS)
    log(f"PROJECT: done ({time.time() - t:.1f}s)")

    vtd_district_df = pd.DataFrame(
        {"GEOID20": list(vtd_opt.assignment.keys()),
         "district_id": list(vtd_opt.assignment.values())}
    )
    vtd_raw = vtd_raw.merge(vtd_district_df, on="GEOID20", how="left")
    missing_vtd = int(vtd_raw["district_id"].isna().sum())
    if missing_vtd:
        raise RuntimeError(f"{missing_vtd} VTDs missing district_id after merge")

    t = time.time()
    log("JOIN: block reps -> VTD polygons…")
    block_reps = blocks_proj[["GEOID20"]].copy()
    block_reps["geometry"] = blocks_proj.geometry.representative_point()
    block_reps = gpd.GeoDataFrame(block_reps, geometry="geometry", crs=EQUAL_AREA_CRS)
    join = gpd.sjoin(
        block_reps,
        vtd_raw[["district_id", "geometry"]],
        how="left",
        predicate="within",
    )
    join = (
        join.sort_values(["GEOID20", "district_id"])
            .drop_duplicates("GEOID20", keep="first")
            [["GEOID20", "district_id"]]
    )
    n_missing = int(join["district_id"].isna().sum())
    if n_missing:
        log(f"  NOTE: {n_missing} blocks did not land inside any VTD; "
            "filling via nearest-VTD")
        miss_ids = set(join.loc[join["district_id"].isna(), "GEOID20"])
        miss = block_reps[block_reps["GEOID20"].isin(miss_ids)]
        near = gpd.sjoin_nearest(
            miss, vtd_raw[["district_id", "geometry"]], how="left"
        )[["GEOID20", "district_id"]].drop_duplicates("GEOID20")
        join = pd.concat(
            [join[~join["district_id"].isna()], near], ignore_index=True
        )
    join["district_id"] = join["district_id"].astype(int)
    log(f"JOIN: in {time.time() - t:.1f}s")

    t = time.time()
    log("LOAD: block units via load_units…")
    block_units = load_units(
        f"data/{state_lc}_block.geojson",
        id_column="GEOID20",
        pop_column="population",
        county_column="county",
    )
    log(f"LOAD: {len(block_units):,} block units in {time.time() - t:.1f}s")

    block_assignment = dict(zip(join["GEOID20"], join["district_id"]))
    missing_blk = [u for u in block_units["unit_id"] if u not in block_assignment]
    if missing_blk:
        raise RuntimeError(
            f"{len(missing_blk)} blocks unassigned, first: {missing_blk[:5]}"
        )

    init_plan = Plan(
        assignment=block_assignment,
        n_districts=n_districts,
        geography="block",
        metadata={"init": "vtd_karcher_inherited"},
    )
    init_metrics = score_plan(init_plan, block_units)
    log(f"INIT (block, from VTD-Karcher): "
        f"DBS={init_metrics['dualbalance_score']:.4f} "
        f"pop_dev_max={init_metrics['pop_deviation_max']:.6f}")

    t = time.time()
    log("OPT(block) with Karcher tolerance, from VTD-Karcher init…")
    block_opt = optimize_dbs(
        init_plan, block_units,
        pop_dev_max_tolerance=KARCHER_TOL, max_passes=100000,
        progress_every=100,
    )
    log(f"OPT(block): in {time.time() - t:.1f}s")

    # Persist the final block plan so we can re-score later (e.g. against
    # units with race + partisan columns) without re-running the optimizer.
    from dualbalance.io import write_plan
    import os as _os

    out_dir = f"out/{state_lc}_block_refined"
    _os.makedirs(out_dir, exist_ok=True)
    write_plan(block_opt, block_units, f"{out_dir}/map.geojson")
    log(f"saved block plan to {out_dir}/map.geojson")

    block_metrics = score_plan(block_opt, block_units)
    mt = block_opt.metadata.get("optimize_dbs_tighten_moves", 0)
    mc = block_opt.metadata.get("optimize_dbs_chain_moves", 0)
    ci = block_opt.metadata.get("optimize_dbs_chain_invocations", 0)
    md = block_opt.metadata.get("optimize_dbs_dbs_moves", 0)
    log(f"BLOCK result: DBS={block_metrics['dualbalance_score']:.4f} "
        f"pop_dev_max={block_metrics['pop_deviation_max']:.6f} "
        f"tight={mt} chain={ci}/{mc} dbs={md}")
    log(f"TOTAL: {(time.time() - T0) / 60:.1f}min")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python _test_block_from_vtd.py <STATE> <N>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], int(sys.argv[2])))
