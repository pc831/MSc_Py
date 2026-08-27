"""Build the key-assumptions table for the aluminium specification sheet.

Mirrors Tables 3a/3b of the Power pathways spec sheet: one table per region, the
percentage change in each transition indicator over the near term (2020-2030) and the
long term (2030-2050).

Source is MPP 1.5DS published annual production volume, China and Rest of the World
files, plus the process intensity pathway from the derivation workbook. No local model
run - same basis as derive_milestones.py.

Two rows of the requested draft are NOT produced:

  Secondary aluminium production   MPP's aluminium model has only Refinery and Smelter
                                   plant types and defers recycling to IAI, which is
                                   global only with a 2018 base year. There is no
                                   China / RoW secondary series to report.

Writes assumption_table_aluminium.csv.
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(".")
MPP_BOOKS = {"China": "mpp_aluminium_net_zero_outputs (1).xlsx",
             "RoW": "mpp_aluminium_net_zero_outputs (2).xlsx"}
SCENARIO = "1.5DS"
SHEET = "Annual_production_volume_Mt_df"

WORKBOOK = Path.home() / "Desktop" / "Aluminium Pathway Derivation" / "Aluminium Emissions Pathway.xlsx"

# Unabated technology sets, identical to derive_milestones.py choice 25. MVR-Fossil-Boiler
# is abated on the intensity limb, CST-Fossil-Boiler by explicit override.
DIGESTER_UNABATED = ["Coal-Boiler", "Oil-Boiler", "Gas-Boiler"]
CALCINER_UNABATED = ["Gas-Calciner", "Oil-Calciner"]

NEAR_TERM = (2020, 2030)
LONG_TERM = (2030, 2050)


def load_production(region):
    """Published 1.5DS production, Mt, technologies x years, for one region."""
    df = pd.read_excel(DATA_DIR / MPP_BOOKS[region], sheet_name=SHEET)
    df = df[df["scenario"] == SCENARIO]
    return df.pivot_table(index=["plant_type", "technology"], columns="year",
                          values="value", aggfunc="sum").fillna(0)


def load_intensity():
    """Process emissions intensity, tCO2e/t Al, by region, from the derivation workbook."""
    raw = pd.read_excel(WORKBOOK, sheet_name="Pathway Output", header=None)
    start = raw.index[raw[0] == "Year"][0]
    years, china, row = [], [], []
    for i in range(start + 1, len(raw)):
        if pd.isna(raw.iloc[i, 0]):
            break
        years.append(int(raw.iloc[i, 0]))
        china.append(float(raw.iloc[i, 1]))
        row.append(float(raw.iloc[i, 2]))
    return pd.DataFrame({"China": china, "RoW": row}, index=years)


def indicator_series(production, intensity, region):
    """The six transition indicators, each as a series over years."""
    refinery = production.loc["Refinery"]
    smelter = production.loc["Smelter"]

    # Refinery technology strings are "<boiler> + <calciner>"; the boiler raises digestion
    # steam. Smelter strings are "<anode> + <power source>" and captive power is out of
    # scope, so the anode group is summed across every power source.
    digester = refinery.loc[[t for t in refinery.index
                             if t.split(" + ")[0] in DIGESTER_UNABATED]]
    calciner = refinery.loc[[t for t in refinery.index
                             if t.split(" + ")[1] in CALCINER_UNABATED]]
    carbon_anode = smelter.loc[[t for t in smelter.index if t.startswith("Carbon Anode")]]

    return {"Alumina production": refinery.sum(),
            "Primary aluminium production": smelter.sum(),
            "Unabated fossil fuel digestion capacity": digester.sum(),
            "Unabated fossil fuel calcination capacity": calciner.sum(),
            "Carbon anode consuming smelting capacity": carbon_anode.sum(),
            "Direct process emissions intensity": intensity[region]}


def phrase(series, period):
    """'Increases by ~X%' / 'Decreases by ~X%', rounded to the nearest 1%."""
    start, end = period
    change = round((series.loc[end] / series.loc[start] - 1) * 100)
    if change == 0:
        return "Remains broadly flat"
    direction = "Increases" if change > 0 else "Decreases"
    return f"{direction} by ~{abs(change)}%"


intensity = load_intensity()

rows = []
for region in MPP_BOOKS:
    indicators = indicator_series(load_production(region), intensity, region)
    for name, series in indicators.items():
        rows.append({"Region": region,
                     "Assumption category": name,
                     "2020-2030": phrase(series, NEAR_TERM),
                     "2030-2050": phrase(series, LONG_TERM),
                     f"Level {NEAR_TERM[0]}": round(series.loc[2020], 2),
                     "Level 2030": round(series.loc[2030], 2),
                     "Level 2050": round(series.loc[2050], 2),
                     "Unit": "tCO2e/t Al" if "intensity" in name
                             else ("Mt alumina" if "lumina" in name or "digestion" in name
                                   or "calcination" in name else "Mt aluminium")})

table = pd.DataFrame(rows)
table.to_csv(DATA_DIR / "assumption_table_aluminium.csv", index=False)

for region in MPP_BOOKS:
    print("=" * 96)
    print(f"Regional assumptions characterizing sector decarbonization in {region}")
    print("=" * 96)
    block = table[table["Region"] == region]
    print(f"{'Assumption category':<45}{'2020-2030':<26}{'2030-2050'}")
    for _, r in block.iterrows():
        print(f"{r['Assumption category']:<45}{r['2020-2030']:<26}{r['2030-2050']}")
    print()
