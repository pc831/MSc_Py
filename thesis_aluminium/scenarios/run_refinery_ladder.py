"""Run the refinery on GCAM demand across the ambition ladder, both scope-2 boundaries.

The refinery is orthogonal to the CCS regime and (there is no) inert-anode lock, so the only axis
that changes refinery outputs is the grid -- which in this design is the ambition scenario (each
SSP-RCP pair carries its own GCAM demand, grid and refining budget). Per ambition scenario the
refinery is solved twice:
  counted  refinery scope-2 = electricity x grid intensity   (SBTi S1+S2 boundary)
  free     refinery scope-2 = 0                               (MPP's shipped free boundary)
So the display axis is the scope-2 boundary (rows) x ambition scenario (columns): a 2x4 matrix,
8 refinery solves. Both rows carry Fix 1 (the switch fix) and the completed electricity table; the
counted/free pair differs only on the boundary.

Each cell is built from a fresh model_clean clone:
  1. apply_gcam_grid          GCAM grid onto the smelter side (sets the grid-intensity reference)
  2. write_alumina_demand     GCAM aluminium x 1.935 onto MPP's alumina regional shares
  3. write_refining_budget    GCAM alumina-sector direct CO2 as the refining allowance
  4. patch_refining_switches  Fix 1: direct unabated->clean-end-state renovation rows
  5. reconstruct_electricity  Fix 2a: the 10 missing inputs_outputs electricity rows
  6. counted then free        Fix 2b: write scope-2, solve, save; zero scope-2, solve, save

Usage (from scenarios/, model env active):
  python run_refinery_ladder.py                 # all 4 scenarios x {counted, free}
  python run_refinery_ladder.py --scen SSP2_3p7 # one scenario
  python run_refinery_ladder.py --dry SSP2_3p7  # build inputs for one scenario, don't solve
  python run_refinery_ladder.py --no-switch-fix SSP2_3p7   # diagnostic: pre-Fix-1 counted run
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
import patch_grid_gcam            # noqa: E402
import patch_refining_switches    # noqa: E402
import patch_refining_scope2      # noqa: E402

SCENARIOS = list(gcam_extract.SCENARIOS)          # SSP1_1p9, SSP1_2p6, SSP2_3p7, SSP2_4p5
ALUMINA_PER_ALUMINIUM = 1.935                     # MPP's fixed conversion (matches common.py)
PY = sys.executable


def clone(name):
    d = SCEN / "models" / name
    if d.exists():
        subprocess.run(["rm", "-rf", str(d)], check=True)
    subprocess.run(["cp", "-cR", "models/model_clean", f"models/{name}"], cwd=SCEN, check=True)
    return d


def write_alumina_demand(model, scen):
    """Scale GCAM global aluminium x 1.935 onto MPP's alumina regional distribution, preserving
    MPP's regional shares each year (the refinery analogue of run_gcam_ladder.write_demand). The
    refinery reads demand.csv; demand_lc.csv is written too to keep them consistent."""
    alu = gcam_extract.load_demand(scen)                        # index=year, Mt aluminium, global
    alumina = alu * ALUMINA_PER_ALUMINIUM                       # Mt alumina, global
    for fname in ("demand.csv", "demand_lc.csv"):
        p = model / "aluminium/data/lc/def_refineries/intermediate" / fname
        if not p.exists():
            continue
        df = pd.read_csv(p)
        mpp_global = df[df["region"] == "Global"].set_index("year")["value"]

        def new_value(row):
            y = int(row["year"])
            if y not in alumina.index:
                return row["value"]
            g = alumina[y]
            if row["region"] == "Global":
                return g
            mg = mpp_global.get(y)
            return g * row["value"] / mg if mg and mg > 0 else row["value"]

        df["value"] = df.apply(new_value, axis=1)
        df.to_csv(p, index=False)


def write_refining_budget(model, scen):
    """Overwrite the refinery carbon budget with the cached GCAM refining budget (Gt/yr) from the
    2025 anchor onward; spin-up (pre-anchor) left as MPP's shipped, non-binding budget."""
    p = model / "aluminium/data/lc/def_refineries/intermediate/carbon_budget.csv"
    b = pd.read_csv(p)
    bud = gcam_extract.load_refining_budget(scen)["annual_limit"]   # index=year, Gt CO2/yr
    b["annual_limit"] = b.apply(
        lambda r: bud.get(int(r["year"]), r["annual_limit"])
        if int(r["year"]) >= gcam_extract.ANCHOR_YEAR else r["annual_limit"], axis=1)
    b.to_csv(p, index=False)


def build_inputs(name, scen, switch_fix=True):
    model = clone(name)
    patch_grid_gcam.apply_gcam_grid(str(model), scen)          # GCAM grid (sets grid reference)
    write_alumina_demand(model, scen)
    write_refining_budget(model, scen)
    if switch_fix:
        patch_refining_switches.apply_switch_fix(str(model))   # Fix 1
    patch_refining_scope2.reconstruct_electricity(model)       # Fix 2a (complete electricity table)
    return model


def solve(scenario_name, model):
    r = subprocess.run([PY, "run.py", scenario_name, "lc", "refinery", model.name],
                       cwd=SCEN, capture_output=True, text=True)
    return r.returncode == 0, (r.stderr or r.stdout)[-400:]


def run_scen(scen, dry=False, switch_fix=True):
    name = f"g_ref_{scen}"
    results = []
    try:
        model = build_inputs(name, scen, switch_fix=switch_fix)
        if dry:
            return [(f"{scen}_refinery (dry)", True, "inputs built")]
        for boundary, counted in (("counted", True), ("free", False)):
            patch_refining_scope2.write_scope2(model, counted=counted)   # Fix 2b
            ok, msg = solve(f"{scen}_refinery_{boundary}", model)
            results.append((f"{scen}_refinery_{boundary}", ok, "" if ok else msg))
    except subprocess.CalledProcessError as e:
        results.append((scen, False, (e.stderr or e.stdout or str(e))[-400:]))
    except Exception as e:  # noqa: BLE001
        results.append((scen, False, repr(e)[-400:]))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scen", nargs="+", default=SCENARIOS)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--dry", metavar="SCEN", default=None)
    ap.add_argument("--no-switch-fix", metavar="SCEN", default=None,
                    help="diagnostic: build+solve one scenario's COUNTED run without Fix 1")
    args = ap.parse_args()

    if args.dry:
        for row in run_scen(args.dry, dry=True):
            print(f"{'OK  ' if row[1] else 'FAIL'} {row[0]}   {row[2]}")
        return
    if args.no_switch_fix:
        scen = args.no_switch_fix
        model = build_inputs(f"g_ref_{scen}_prefix", scen, switch_fix=False)
        patch_refining_scope2.write_scope2(model, counted=True)
        ok, msg = solve(f"{scen}_refinery_prefix", model)
        print(f"{'OK  ' if ok else 'FAIL'} {scen}_refinery_prefix (NO Fix 1)   {msg}")
        return

    scens = [s for s in SCENARIOS if s in args.scen]
    print(f"Refinery ladder: {len(scens)} scenarios x {{counted, free}} = {len(scens)*2} solves, "
          f"{args.workers} workers", flush=True)
    results = []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_scen, s): s for s in scens}
        for fut in cf.as_completed(futs):
            for name, ok, msg in fut.result():
                print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f"   {msg}" if msg else ""),
                      flush=True)
                results.append((name, ok))

    print("\n################ REFINERY LADDER SUMMARY ################")
    for name, ok in sorted(results):
        print(f"  {'OK  ' if ok else 'FAIL'} {name}")


if __name__ == "__main__":
    main()
