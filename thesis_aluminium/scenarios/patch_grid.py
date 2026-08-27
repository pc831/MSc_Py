"""Replace grid electricity emissions in the model with the SBTi power pathway.

The model stores scope 2 emissions per tonne of product. We rescale them by the ratio
of the SBTi grid intensity to the intensity MPP implied, region by region and year by
year. Rescaling rather than overwriting preserves the structure MPP built in, for
example that a power purchase agreement is partly renewable and so already cleaner
than plain grid supply.
"""

import sys

import pandas as pd
from pathlib import Path

MODEL = Path("models") / sys.argv[1]   # e.g. python patch_grid.py model_SBTigrid_CCS_AnodeLocked
POWER = Path("../inputs/POWER_PATHWAY_FINAL_V4.0_MANUAL.xlsx")

# MPP's 16 regions mapped onto the two SBTi groupings. Judgement call, stated here
# rather than buried: Oceania is Australia and New Zealand, Rest of Europe is treated
# as advanced.
ADVANCED = ["Canada", "Oceania", "Rest of Europe", "Scandinavia", "US"]

# The technology the model uses for plain grid supply, used to read back the grid
# intensity MPP assumed.
REFERENCE_TECHNOLOGY = "Inert Anode + Grid"


def sbti_grid_intensity():
    """SBTi power pathway intensity in tonnes CO2 per MWh, interpolated to every year."""
    df = pd.read_excel(POWER, sheet_name="POWER PATHWAY V4").dropna(subset=["Value"])
    df = df[df["Value"].str.contains("intensity", case=False)]

    years = [c for c in df.columns if isinstance(c, int)]
    series = {}
    for group, label in [("Advanced Economies", "advanced"), ("Emerging economies", "emerging")]:
        row = df[df["Region"] == group].iloc[0]
        # kgCO2/MWh in the workbook, converted to tonnes
        values = pd.Series({y: row[y] / 1000 for y in years})
        full = values.reindex(range(2020, 2051)).interpolate()
        series[label] = full
    return series


def patch_emissions(folder):
    """Rescale scope 2 emissions in one data folder."""
    path = MODEL / "aluminium" / "data" / "lc" / folder / "intermediate" / "emissions.csv"
    emissions = pd.read_csv(path)

    inputs = pd.read_csv(path.parent / "inputs_outputs.csv")
    electricity = inputs[inputs["parameter"] == "Electricity Consumption"]

    sbti = sbti_grid_intensity()

    # Work out the grid intensity MPP assumed, from the plain grid technology
    reference = emissions[emissions["technology"] == REFERENCE_TECHNOLOGY]
    if reference.empty:
        print(f"  {folder}: no grid technology, scope 2 left unchanged")
        return

    scale = {}
    for (region, year), rows in reference.groupby(["region", "year"]):
        mwh = electricity[
            (electricity["region"] == region)
            & (electricity["year"] == year)
            & (electricity["technology"] == REFERENCE_TECHNOLOGY)
        ]["value"]
        if mwh.empty or mwh.iloc[0] == 0:
            continue
        mpp_intensity = rows["co2_scope2"].iloc[0] / mwh.iloc[0]
        group = "advanced" if region in ADVANCED else "emerging"
        target = sbti[group][year]
        scale[(region, year)] = target / mpp_intensity if mpp_intensity > 0 else 0

    before = emissions["co2_scope2"].sum()
    emissions["co2_scope2"] = emissions.apply(
        lambda row: row["co2_scope2"] * scale.get((row["region"], row["year"]), 1),
        axis=1,
    )
    after = emissions["co2_scope2"].sum()

    emissions.to_csv(path, index=False)
    print(f"  {folder}: scope 2 total {before:.1f} -> {after:.1f}")


print("Applying SBTi power pathway grid intensity")
for folder in ["def", "def_refineries"]:
    patch_emissions(folder)
