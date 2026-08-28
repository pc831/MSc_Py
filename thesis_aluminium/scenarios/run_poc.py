"""First test runs: grid x CCS matrix, MPP demand, budget = present emissions x linear decline.

Each cell: clone model_clean, apply the full switch table + the six unlock switches, apply one
IAM grid, apply one CCS regime, overwrite the smelting carbon budget with a linear decline from
today's emissions to ~zero by 2050 (so anode + power both scale down, forcing the anode switch).
Demand stays MPP's own. Refining is left as shipped.

CCS regimes on the same full table (so only the constraint differs):
  unlimited - no cap (run first per grid; used as the reference fleet for the limited cells)
  none      - FGD curve at 0% (no captive capture)
  low       - global FGD pace, 10->90% over 26 years
  high      - Germany FGD pace, 10->79% in 4 years

Run from scenarios/ with the sbti_alu env active:  python run_poc.py
"""

import shutil
import subprocess
from pathlib import Path

import pandas as pd

SCEN = Path(__file__).resolve().parent
GRIDS = {"REMIND": "REMIND-MAgPIE 2.1-4.2", "MESSAGE": "MESSAGEix-GLOBIOM_1.1",
         "AIM": "AIM/CGE 2.2", "WITCH": "WITCH 5.0"}
CCS = ["unlimited", "none", "low", "high"]   # unlimited first: it is the reference fleet


def sh(*args):
    subprocess.run(list(args), cwd=SCEN, check=True)


def clone(name):
    d = SCEN / "models" / name
    if d.exists():
        shutil.rmtree(d)
    subprocess.run(["cp", "-cR", "models/model_clean", f"models/{name}"], cwd=SCEN, check=True)


def write_linear_budget(model_name):
    """Overwrite the smelting budget: base (2020 emissions) x linear f, 1.0 in 2020 to 0.05 in 2050."""
    p = SCEN / "models" / model_name / "aluminium/data/lc/def/intermediate/carbon_budget.csv"
    b = pd.read_csv(p)
    base = b.loc[b["year"] == 2020, "annual_limit"].iloc[0]

    def f(y):
        if y <= 2020:
            return 1.0
        return max(0.05, 1.0 - (y - 2020) / 30 * 0.95)

    b["annual_limit"] = b["year"].map(lambda y: base * f(y))
    b.to_csv(p, index=False)


results = []
for tag, iam in GRIDS.items():
    for ccs in CCS:
        name = f"m_{tag}_{ccs}"
        scenario = f"{tag}_{ccs}"
        clone(name)
        sh("python", "patch_fulltt.py", name)                 # full switch table + unlock switches
        sh("python", "patch_grid_iam.py", name, iam)          # grid treatment
        if ccs in ("none", "low", "high"):
            reference = f"runs/{tag}_unlimited/smelter/final"
            sh("python", "patch_ccs_limit.py", name, ccs, reference)
        write_linear_budget(name)
        r = subprocess.run(["python", "run.py", scenario, "lc", "smelter", name], cwd=SCEN)
        ok = r.returncode == 0
        results.append((scenario, ok))
        print(f"  {'OK  ' if ok else 'FAIL'} {scenario}", flush=True)

print("\n################ POC MATRIX SUMMARY ################")
for s, ok in results:
    print(f"  {'OK  ' if ok else 'FAIL'} {s}")
