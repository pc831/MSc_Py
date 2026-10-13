"""Fix 2 — refinery scope-2 electricity, shipped empty by MPP.

MPP ships refinery co2_scope2 as zero for every electrified technology bar one placeholder, so
the solver never sees the grid emissions an electric or MVR boiler pulls in (the ranking rebuilds
scope 2 from emissions.csv each run). Two sub-problems, both reconstructable, neither a real gap:

1. 10 of the 29 refining technologies are missing from inputs_outputs.csv. They are all
   boiler/calciner cross-combos the model actually builds. Electricity is per-component: a
   technology's electricity = its boiler's term + its calciner's term. The calciner term is read
   off `Gas-Boiler + <calciner>` (a gas boiler draws no electricity). The boiler term is the
   median over that boiler's PRESENT pairs of (value - calciner term); the median is robust to the
   lone additive-breaking placeholder (CST-Fossil-Boiler + Elec-Calciner, shipped ~0.887). Clip at
   zero. Reconstructed rows are appended to inputs_outputs.csv (electricity cost then consistent).

2. Scope 2 = reconstructed electricity x grid intensity, region- and year-specific, written back
   into refinery emissions.csv. Grid intensity (t CO2/MWh) is read off the SMELTER side of the
   same model copy, from the `Inert Anode + Grid` reference (co2_scope2 / Electricity Consumption).
   Because it is read from the same copy, the refinery inherits whatever grid that copy's smelter
   already carries — so on a GCAM-rescaled copy it inherits the GCAM curve, with no grid argument.
   PREREQUISITE: apply the grid rescale to the smelter side (apply_gcam_grid) BEFORE calling this.

Boundary toggle: counted=True writes elec x grid into refinery scope 2 (SBTi S1+S2 boundary);
counted=False zeroes refinery scope 2 (MPP's shipped free boundary). The electricity reconstruction
runs either way, so counted and free differ only on the boundary, not on the input table.

Importable: reconstruct_electricity(model), write_scope2(model, counted).
Also runnable: python patch_refining_scope2.py <model> [free]
"""

import sys
from pathlib import Path

import pandas as pd

REFERENCE_TECHNOLOGY = "Inert Anode + Grid"     # smelter grid supply -> implied grid intensity
CALCINERS = ["Elec", "H2", "Gas", "Oil"]
# The 10 boiler/calciner cross-combos MPP omits from inputs_outputs.csv.
MISSING = [f"{b}-Boiler + {c}-Calciner" for b, c in [
    ("Coal", "Elec"), ("Coal", "H2"), ("Elec", "Gas"), ("Elec", "Oil"),
    ("H2", "Gas"), ("H2", "Oil"), ("MVR-Fossil", "Gas"), ("MVR-Fossil", "Oil"),
    ("Oil", "Elec"), ("Oil", "H2")]]


def _refinery_dir(model):
    return model / "aluminium" / "data" / "lc" / "def_refineries" / "intermediate"


def _grid_intensity(model):
    """t CO2/MWh per (region, year), read off the smelter's Inert Anode + Grid reference of the
    SAME model copy: co2_scope2 / Electricity Consumption. Inherits that copy's grid."""
    smelt = model / "aluminium" / "data" / "lc" / "def" / "intermediate"
    em = pd.read_csv(smelt / "emissions.csv")
    io = pd.read_csv(smelt / "inputs_outputs.csv")
    em = em[em["technology"] == REFERENCE_TECHNOLOGY][["region", "year", "co2_scope2"]]
    el = io[(io["technology"] == REFERENCE_TECHNOLOGY)
            & (io["parameter"] == "Electricity Consumption")][["region", "year", "value"]]
    m = em.merge(el, on=["region", "year"])
    m["intensity"] = m.apply(
        lambda r: r["co2_scope2"] / r["value"] if r["value"] else 0.0, axis=1)
    return m.set_index(["region", "year"])["intensity"]


def _electricity_pivot(io):
    el = io[io["parameter"] == "Electricity Consumption"]
    return el.pivot_table(index=["region", "year"], columns="technology", values="value")


def reconstruct_electricity(model):
    """Append the 10 missing Electricity Consumption rows to the refinery inputs_outputs.csv.
    Idempotent: rows already present are not re-added. Returns the number of rows added."""
    path = _refinery_dir(model) / "inputs_outputs.csv"
    io = pd.read_csv(path)
    present = set(io[io["parameter"] == "Electricity Consumption"]["technology"].unique())
    todo = [t for t in MISSING if t not in present]
    if not todo:
        print(f"  {model.name}: electricity rows already complete")
        return 0

    piv = _electricity_pivot(io)
    calc_term = {c: piv.get(f"Gas-Boiler + {c}-Calciner", pd.Series(0.0, index=piv.index))
                 for c in CALCINERS}

    def boiler_term(boiler):
        cols = [(piv[f"{boiler} + {c}-Calciner"] - calc_term[c])
                for c in CALCINERS if f"{boiler} + {c}-Calciner" in piv.columns]
        return pd.concat(cols, axis=1).median(axis=1)     # robust to the CST placeholder

    template = io[(io["parameter"] == "Electricity Consumption")].iloc[0]
    new_rows = []
    for tech in todo:
        boiler, calciner = tech.split(" + ")
        calc = calciner.replace("-Calciner", "")
        recon = (boiler_term(boiler) + calc_term[calc]).clip(lower=0.0)   # per (region, year)
        for (region, year), value in recon.items():
            row = template.copy()
            row["region"], row["year"], row["technology"] = region, year, tech
            row["value"] = value
            new_rows.append(row)

    io = pd.concat([io, pd.DataFrame(new_rows)], ignore_index=True)
    io.to_csv(path, index=False)
    sample = boiler_term("Elec-Boiler").dropna()
    print(f"  {model.name}: added {len(new_rows)} electricity rows for {len(todo)} techs "
          f"(Elec-Boiler term median {sample.median():.3f} MWh/t)")
    return len(new_rows)


def write_scope2(model, counted):
    """Write refinery co2_scope2. counted=True -> electricity x grid intensity (S1+S2 boundary);
    counted=False -> zero (MPP's shipped free boundary)."""
    rdir = _refinery_dir(model)
    em = pd.read_csv(rdir / "emissions.csv")

    if not counted:
        before = (em["co2_scope2"] != 0).sum()
        em["co2_scope2"] = 0.0
        em.to_csv(rdir / "emissions.csv", index=False)
        print(f"  {model.name}: FREE boundary, scope 2 zeroed ({before} nonzero rows cleared)")
        return

    io = pd.read_csv(rdir / "inputs_outputs.csv")
    el = io[io["parameter"] == "Electricity Consumption"][
        ["technology", "region", "year", "value"]].rename(columns={"value": "mwh"})
    grid = _grid_intensity(model)

    em = em.merge(el, on=["technology", "region", "year"], how="left")
    em["mwh"] = em["mwh"].fillna(0.0)
    em["grid"] = em.apply(lambda r: grid.get((r["region"], r["year"]), 0.0), axis=1)
    em["co2_scope2"] = em["mwh"] * em["grid"]
    total = em["co2_scope2"].sum()
    em = em.drop(columns=["mwh", "grid"])
    em.to_csv(rdir / "emissions.csv", index=False)
    print(f"  {model.name}: COUNTED boundary, scope 2 = elec x grid, "
          f"total {total:.1f} (t/t summed over rows)")


if __name__ == "__main__":
    m = Path("models") / sys.argv[1] if not sys.argv[1].startswith("/") else Path(sys.argv[1])
    reconstruct_electricity(m)
    write_scope2(m, counted=("free" not in sys.argv[2:]))
