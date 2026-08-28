"""Replace grid electricity emissions in the model with an IAM's grid pathway.

Generalises patch_grid.py from the single SBTi power pathway to any IAM grid produced by
pipeline/grid_intensity.py. Same mechanism: the model stores scope-2 emissions per tonne of
product; we rescale them, region by region and year by year, by the ratio of the IAM's grid
intensity to the intensity MPP implied. Rescaling rather than overwriting preserves MPP's
structure — e.g. that a power purchase agreement is partly renewable and already cleaner than
plain grid. Scope 1 (anode, captive power) is untouched, so the grid acts on the grid-vs-captive
margin only. Refining has no grid technology, so its scope 2 is left unchanged.

Usage: python patch_grid_iam.py <model_dir> "<IAM model name>"
       e.g. python patch_grid_iam.py model_REMINDgrid_CCS_AnodeUnlocked "REMIND-MAgPIE 2.1-4.2"
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
import grid_intensity  # noqa: E402

MODEL = Path("models") / sys.argv[1]
IAM_MODEL = sys.argv[2]

REFERENCE_TECHNOLOGY = "Inert Anode + Grid"   # plain grid supply, to read back MPP's implied grid


def patch_emissions(folder, iam):
    """Rescale scope 2 emissions in one data folder to the IAM grid intensity.

    iam is a DataFrame [year x MPP region] of grid intensity in t CO2/MWh.
    """
    path = MODEL / "aluminium" / "data" / "lc" / folder / "intermediate" / "emissions.csv"
    emissions = pd.read_csv(path)

    inputs = pd.read_csv(path.parent / "inputs_outputs.csv")
    electricity = inputs[inputs["parameter"] == "Electricity Consumption"]

    reference = emissions[emissions["technology"] == REFERENCE_TECHNOLOGY]
    if reference.empty:
        print(f"  {folder}: no grid technology, scope 2 left unchanged")
        return

    scale = {}
    for (region, year), rows in reference.groupby(["region", "year"]):
        if region not in iam.columns or year not in iam.index:
            continue
        mwh = electricity[
            (electricity["region"] == region)
            & (electricity["year"] == year)
            & (electricity["technology"] == REFERENCE_TECHNOLOGY)
        ]["value"]
        if mwh.empty or mwh.iloc[0] == 0:
            continue
        mpp_intensity = rows["co2_scope2"].iloc[0] / mwh.iloc[0]   # t CO2 / MWh MPP assumed
        target = iam.loc[year, region]                            # t CO2 / MWh the IAM implies
        scale[(region, year)] = target / mpp_intensity if mpp_intensity > 0 else 0

    before = emissions["co2_scope2"].sum()
    emissions["co2_scope2"] = emissions.apply(
        lambda row: row["co2_scope2"] * scale.get((row["region"], row["year"]), 1),
        axis=1,
    )
    after = emissions["co2_scope2"].sum()

    emissions.to_csv(path, index=False)
    print(f"  {folder}: scope 2 total {before:.1f} -> {after:.1f}")


iam = grid_intensity.grid_intensity(IAM_MODEL)
print(f"Applying {IAM_MODEL} grid intensity to {MODEL.name}")
for folder in ["def", "def_refineries"]:
    patch_emissions(folder, iam)
