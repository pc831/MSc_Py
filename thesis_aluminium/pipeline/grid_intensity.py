"""Gross grid CO2 intensity per IAM, mapped to MPP's regions.

Reads an AR6-format IAMC snapshot (the interim grid stream; AR7/ScenarioMIP VLLO drops in by
swapping the file and SCENARIO), computes the gross power-sector CO2 intensity each IAM implies
per region and year, and maps the R10 regions onto MPP's 16 aluminium regions so the result can
drive a scope-2 rescale in the model.

Gross, not net: the electricity emissions variable nets out BECCS as negative removals. A smelter
drawing grid power is not the beneficiary of economy-wide CDR, so we add the biomass-CCS captured
back to get the physical combustion intensity of generation:

    gross intensity = (Emissions|CO2|Energy|Supply|Electricity
                       + Carbon Sequestration|CCS|Biomass|Energy|Supply|Electricity)
                      / Secondary Energy|Electricity

Everything is interpolated to annual over 2020-2050 and returned in t CO2 / MWh.
"""

from pathlib import Path

import numpy as np
import pandas as pd

INPUTS = Path(__file__).resolve().parent.parent / "inputs"
AR6_FILE = INPUTS / "ar6_grid_EN_NPi2020_400f.csv"
SCENARIO = "EN_NPi2020_400f"

EMIS = "Emissions|CO2|Energy|Supply|Electricity"                       # Mt CO2/yr, net of BECCS
BECCS = "Carbon Sequestration|CCS|Biomass|Energy|Supply|Electricity"   # Mt CO2/yr, add back
GEN = "Secondary Energy|Electricity"                                   # EJ/yr

YEARS = list(range(2020, 2051))

# Mt CO2 / EJ  ->  t CO2 / MWh.  1 EJ = 1e18 J = 2.77778e8 MWh; 1 Mt = 1e6 t.
MT_PER_EJ_TO_T_PER_MWH = 1e6 / (1e18 / 3.6e9)   # = 0.0036

# Each MPP region takes the grid of the R10 region it sits in. China splits six ways in MPP but
# is one region at R10, so all six take the same China grid. Judgement calls are flagged; see
# thesis_design_choices.md. R10 cannot resolve, e.g., Scandinavia's hydro grid from the EU28
# average, so those regions inherit a dirtier grid than reality.
R10 = {
    "subsaharan": "Countries of Sub-Saharan Africa",
    "latam": "Countries of Latin America and the Caribbean",
    "south_asia": "Countries of South Asia; primarily India",
    "china": "Countries of centrally-planned Asia; primarily China",
    "middle_east": "Countries of the Middle East; Iran, Iraq, Israel, Saudi Arabia, Qatar, etc.",
    "europe": "Eastern and Western Europe (i.e., the EU28)",
    "north_america": "North America; primarily the United States of America and Canada",
    "other_asia": "Other countries of Asia",
    "pacific_oecd": "Pacific OECD",
    "reforming": "Reforming Economies of Eastern Europe and the Former Soviet Union; primarily Russia",
}

MPP_TO_R10 = {
    "Africa": R10["subsaharan"],          # North Africa unresolved; Sub-Saharan holds the smelting
    "Canada": R10["north_america"],
    "US": R10["north_america"],
    "China - Central": R10["china"],
    "China - East": R10["china"],
    "China - North": R10["china"],
    "China - North East": R10["china"],
    "China - North West": R10["china"],
    "China - South": R10["china"],
    "Middle East": R10["middle_east"],
    "Oceania": R10["pacific_oecd"],        # Pacific OECD also holds Japan/Korea, dirtier than Aus/NZ
    "Rest of Asia": R10["other_asia"],     # India (South Asia) sits in a separate R10 region
    "Rest of Europe": R10["europe"],
    "Scandinavia": R10["europe"],          # loses the clean Nordic hydro grid
    "Russia": R10["reforming"],
    "South America": R10["latam"],
}


def _series(df, model, region, variable):
    """One IAM variable for one model and R10 region, interpolated to annual 2020-2050."""
    rows = df[(df["Model"] == model) & (df["Region"] == region) & (df["Variable"] == variable)]
    if rows.empty:
        return None
    year_cols = [c for c in df.columns if c.strip().isdigit()]
    wide = rows[year_cols].iloc[0]
    x = np.array([int(c) for c in year_cols])
    y = wide.to_numpy(dtype=float)
    keep = ~np.isnan(y)
    return pd.Series(np.interp(YEARS, x[keep], y[keep]), index=YEARS)


def r10_intensity(df, model):
    """Gross grid intensity (t CO2/MWh) per R10 region and year for one model."""
    out = {}
    for region in df["Region"].unique():
        emis = _series(df, model, region, EMIS)
        gen = _series(df, model, region, GEN)
        if emis is None or gen is None:
            continue
        beccs = _series(df, model, region, BECCS)
        if beccs is None:
            beccs = pd.Series(0.0, index=YEARS)   # model didn't report BECCS here -> net is gross
        gross_mt_per_ej = (emis + beccs) / gen
        out[region] = gross_mt_per_ej * MT_PER_EJ_TO_T_PER_MWH
    return pd.DataFrame(out)   # index = year, columns = R10 region


def grid_intensity(model, file=AR6_FILE, scenario=SCENARIO):
    """Gross grid intensity in MPP regions for one IAM. Returns DataFrame [year x MPP region].

    Swap AR6 -> AR7/VLLO by passing a new `file` and `scenario`; nothing else changes.
    """
    df = pd.read_csv(file)
    df = df[df["Model"].notna() & ~df["Model"].astype(str).str.startswith("©")]
    df = df[df["Scenario"] == scenario]

    r10 = r10_intensity(df, model)
    mpp = {}
    for mpp_region, r10_region in MPP_TO_R10.items():
        if r10_region in r10.columns:
            mpp[mpp_region] = r10[r10_region]
    return pd.DataFrame(mpp)


# GEM-E3 dropped: it doesn't report the BECCS variable, so its gross intensity is wrong.
IAM_MODELS = ["REMIND-MAgPIE 2.1-4.2", "MESSAGEix-GLOBIOM_1.1", "AIM/CGE 2.2",
              "COFFEE 1.1", "WITCH 5.0"]


if __name__ == "__main__":
    for model in IAM_MODELS:
        g = grid_intensity(model)
        if g.empty:
            print(f"{model:24s}  no data")
            continue
        china = g["China - Central"]
        print(f"{model:24s}  China grid t/MWh  2020 {china[2020]:.3f}  2030 {china[2030]:.3f}  2050 {china[2050]:.3f}")
