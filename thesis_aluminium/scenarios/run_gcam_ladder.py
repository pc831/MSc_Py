"""Run the GCAM ambition-ladder x CCS matrix on MPP, in parallel across cores.

Each cell = one GCAM SSP-RCP scenario (its demand + grid + budget, from pipeline/gcam_cache/)
crossed with one CCS regime, on the fixed MPP asset model. MPP is single-threaded, so the way to
use the machine is to run many independent cells at once — this launches up to --workers model
processes concurrently (default: cores - 1).

Two stages, because capped-CCS cells need each scenario's `unlimited` run as their capture
reference:
  stage 1  4 `unlimited` cells      (parallel)
  stage 2  none/low/high x 4 = 12   (parallel, each keyed to its scenario's unlimited output)

Usage (run from scenarios/, model env active):
  python run_gcam_ladder.py                 # all 16
  python run_gcam_ladder.py --ccs unlimited none   # subset of CCS regimes
  python run_gcam_ladder.py --dry SSP1_1p9 unlimited   # build inputs for one cell, don't solve
  python run_gcam_ladder.py --workers 8
"""

import argparse
import concurrent.futures as cf
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

SCEN = Path(__file__).resolve().parent
sys.path.insert(0, str(SCEN.parent / "pipeline"))
import gcam_extract  # noqa: E402
sys.path.insert(0, str(SCEN))
import patch_grid_gcam  # noqa: E402

SCENARIOS = list(gcam_extract.SCENARIOS)          # SSP1_1p9, SSP1_2p6, SSP2_3p7, SSP2_4p5
CCS_ALL = ["unlimited", "none", "low", "high"]    # unlimited first: reference for the rest
PY = sys.executable


def sh(*args):
    subprocess.run([PY, *args], cwd=SCEN, check=True, capture_output=True, text=True)


def clone(name):
    d = SCEN / "models" / name
    if d.exists():
        subprocess.run(["rm", "-rf", str(d)], check=True)
    subprocess.run(["cp", "-cR", "models/model_clean", f"models/{name}"], cwd=SCEN, check=True)
    return d


def write_demand(model, scen):
    """Scale the GCAM global production onto MPP's regional distribution (D5 shortcut).

    The model reads demand from `demand.csv` (mppshared.import_data.get_demand); `demand_lc.csv`
    is a sibling that is NOT read for the solve, so we write both to keep them consistent. Both are
    regional (per-MPP-region rows summing to a Global row). We keep MPP's own regional shares each
    year and rescale so the total matches GCAM's global series:
        new(region, y) = GCAM_global(y) * MPP(region, y) / MPP_global(y);  Global row = GCAM_global.
    """
    dem = gcam_extract.load_demand(scen)                        # index=year, Mt, global
    for fname in ("demand.csv", "demand_lc.csv"):
        p = model / "aluminium/data/lc/def/intermediate" / fname
        if not p.exists():
            continue
        df = pd.read_csv(p)
        mpp_global = df[df["region"] == "Global"].set_index("year")["value"]

        def new_value(row):
            y = int(row["year"])
            if y not in dem.index:
                return row["value"]
            g = dem[y]
            if row["region"] == "Global":
                return g
            mg = mpp_global.get(y)
            return g * row["value"] / mg if mg and mg > 0 else row["value"]

        df["value"] = df.apply(new_value, axis=1)
        df.to_csv(p, index=False)


def write_budget(model, scen):
    """Overwrite the smelter carbon budget with the cached GCAM budget (Gt/yr) from the 2025 anchor
    onward; 2020-2024 (spin-up) and pre-2020 left as MPP's shipped, non-binding budget."""
    p = model / "aluminium/data/lc/def/intermediate/carbon_budget.csv"
    b = pd.read_csv(p)
    bud = gcam_extract.load_budget(scen)["annual_limit"]       # index=year, Gt CO2/yr
    b["annual_limit"] = b.apply(
        lambda r: bud.get(int(r["year"]), r["annual_limit"])
        if int(r["year"]) >= gcam_extract.ANCHOR_YEAR else r["annual_limit"], axis=1)
    b.to_csv(p, index=False)


def build_inputs(name, scen):
    """Clone + apply the full switch table + write GCAM demand/grid/budget. Returns model path."""
    model = clone(name)
    sh("patch_fulltt.py", name)                                   # full table + 6 unlock switches
    write_demand(model, scen)
    patch_grid_gcam.apply_gcam_grid(str(model), scen)             # GCAM grid (from cache)
    write_budget(model, scen)
    return model


def run_cell(scen, ccs, dry=False):
    name = f"g_{scen}_{ccs}"
    scenario = f"{scen}_{ccs}"
    try:
        build_inputs(name, scen)
        if ccs != "unlimited":
            reference = f"runs/{scen}_unlimited/smelter/final"
            sh("patch_ccs_limit.py", name, ccs, reference)
        if dry:
            return (scenario, True, "inputs built (dry)")
        r = subprocess.run([PY, "run.py", scenario, "lc", "smelter", name],
                           cwd=SCEN, capture_output=True, text=True)
        ok = r.returncode == 0
        return (scenario, ok, "" if ok else (r.stderr or r.stdout)[-400:])
    except subprocess.CalledProcessError as e:
        return (scenario, False, (e.stderr or e.stdout or str(e))[-400:])
    except Exception as e:  # noqa: BLE001
        return (scenario, False, repr(e)[-400:])


def parallel(cells, workers):
    results = []
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(run_cell, s, c): (s, c) for s, c in cells}
        for fut in cf.as_completed(futs):
            scenario, ok, msg = fut.result()
            print(f"  {'OK  ' if ok else 'FAIL'} {scenario}" + (f"   {msg}" if msg and not ok else ""),
                  flush=True)
            results.append((scenario, ok))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ccs", nargs="+", default=CCS_ALL)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--dry", nargs=2, metavar=("SCEN", "CCS"), default=None)
    args = ap.parse_args()

    if args.dry:
        scenario, ok, msg = run_cell(args.dry[0], args.dry[1], dry=True)
        print(f"{'OK  ' if ok else 'FAIL'} {scenario}   {msg}")
        return

    ccs = [c for c in CCS_ALL if c in args.ccs]
    print(f"GCAM ladder: {len(SCENARIOS)} scenarios x {len(ccs)} CCS = {len(SCENARIOS)*len(ccs)} "
          f"cells, {args.workers} workers", flush=True)

    results = []
    if "unlimited" in ccs:
        print("Stage 1: unlimited (reference fleets)", flush=True)
        results += parallel([(s, "unlimited") for s in SCENARIOS], args.workers)
    rest = [(s, c) for s in SCENARIOS for c in ccs if c != "unlimited"]
    if rest:
        print("Stage 2: capped CCS", flush=True)
        results += parallel(rest, args.workers)

    print("\n################ GCAM LADDER SUMMARY ################")
    for s, ok in sorted(results):
        print(f"  {'OK  ' if ok else 'FAIL'} {s}")


if __name__ == "__main__":
    main()
