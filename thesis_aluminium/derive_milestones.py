"""Derive asset-transition milestone years for aluminium, China vs Rest of the World.

Seven milestones for the 2PC specification sheet, following the Power pattern of one
"no new" year and one "phase out" year per unabated technology group:

    1. No new unabated fossil digester        refinery boiler raising digestion steam
    2. Phase out unabated fossil digester
    3. No new unabated fossil calciner        refinery calciner
    4. Phase out unabated fossil calciner
    5. Phase out unabated carbon anode        smelter anode
    6. No new unabated fossil auxiliary       remelting, scrap refining, casting
    7. Phase out unabated fossil auxiliary


WHAT COUNTS AS UNABATED
A technology is abated if either limb holds:
    (a) it is fitted with CCS at >= 90% capture rate, or
    (b) its scope 1 intensity is roughly <= 10% of BAU performance for the same
        process step.
Everything else is unabated. Both limbs are evaluated against data rather than
technology names, because MPP's names are misleading in both directions - the
"-Fossil-" boilers are mostly decarbonised, and "Carbon Anode+CCS" still emits half of
BAU. Classifications and the ratios behind them are set out at each group below.


CAPTIVE POWER GENERATION IS OUT OF SCOPE
MPP smelter technology strings are "<anode> + <power source>", where the power source is
the smelter's captive or contracted electricity. Under SBTi guidance that generation takes
its milestone from the power sector, so the power-source component is never tested here.
Anode milestones are computed on production summed across all power sources.


THE TWO TESTS
  no_new_year     the year after the last year the series exceeded its own prior running
                  maximum by more than the materiality threshold. For MPP this is applied
                  to production, which works because MPP caps utilisation at
                  CUF_UPPER_THRESHOLD = 0.95, so production above a technology's previous
                  peak cannot come from utilisation alone and requires added capacity. For
                  the auxiliary group it is applied to capacity directly.

                  Applied per technology and the latest year across the group taken, so
                  that building a new gas boiler while retiring a coal boiler still counts
                  as a new unabated fossil digester. The group-total test is reported
                  alongside as the weaker net-capacity reading.

  phase_out_year  the first year the series is at or below the materiality threshold and
                  stays there.

  materiality     1% of the group's 2020 production or capacity, applied to both tests.
                  Without it, single stranded assets and rounding-scale increments drive
                  the milestone: China's unabated carbon anode falls 99.7% by 2042 and then
                  one 0.13 Mt smelter holds flat to 2050, which would otherwise read as no
                  phase-out at all.

  2050 backstop   net zero by 2050 is a hard requirement of the standard, so any milestone
                  with no year in the source scenario is set to 2050. Flagged in the output
                  wherever it binds, because it means the source scenario does not deliver
                  the milestone on its own.

Limitation: the capacity test detects NET growth within a technology, so it is a lower
bound on gross new build. Capacity added in a year while more capacity retired would be
invisible.

Sources: MPP published workbooks for digester, calciner and anode - the China and Rest of
the World files, which are an exact partition of the global one. No local model run.
IAI 1.5DS for auxiliary, which is the source MPP itself defers to for the value chain steps
outside its asset-level model. IAI is GLOBAL ONLY, so the auxiliary milestone carries the
same year in both regions.

Writes milestones_aluminium.csv.
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(".")
MPP_BOOKS = {"China": "mpp_aluminium_net_zero_outputs (1).xlsx",
             "RoW": "mpp_aluminium_net_zero_outputs (2).xlsx"}
SCENARIO = "1.5DS"
SHEET = "Annual_production_volume_Mt_df"
MATERIALITY = 0.01
BACKSTOP = 2050
EPS = 1e-9

# --- Digester -------------------------------------------------------------------------
# The boiler raises digestion steam, 69% of refinery thermal energy. Classified on gas
# consumption per tonne alumina from inputs_outputs.csv, against the Gas-Boiler, which is
# the lowest-intensity pure fossil option and so the strictest available benchmark. Ratios
# are identical in all 16 MPP regions.
#   Coal-Boiler 181%   Oil-Boiler 129%   Gas-Boiler 100%   -> unabated
#   MVR-Fossil-Boiler 5%    -> ABATED under limb (b). Mechanical vapour recompression at
#                              300% efficiency, 0.363 GJ/t alumina of residual gas. No CCS,
#                              so it qualifies on intensity, not capture.
#   CST-Fossil-Boiler 26%   -> ABATED BY OVERRIDE. Fails limb (b) on the rule, but its
#                              residual is a solar backup rather than a primary fuel and is
#                              treated as switchable to biogas or hydrogen. Parker's call.
#                              Reverting it moves the RoW digester milestone to 2046 / 2050
#                              (backstop) instead of 2022 / 2045, because MPP builds 3.78 Mt
#                              of CST capacity in RoW in 2045.
#   Elec-Boiler, H2-Boiler, Bio-Boiler 0%   -> abated
DIGESTER_UNABATED = ["Coal-Boiler", "Oil-Boiler", "Gas-Boiler"]

# --- Calciner -------------------------------------------------------------------------
# MPP considered CCS retrofits to calciners and rejected them - no known industrial
# example, and the capture scale is too small to be viable (Technical Appendix p.10). So no
# abated fossil calciner exists in the technology set and every fossil calciner is unabated
# by construction. Elec-Calciner and H2-Calciner carry zero direct emissions.
CALCINER_UNABATED = ["Gas-Calciner", "Oil-Calciner"]

# --- Anode ----------------------------------------------------------------------------
# Direct emissions per tonne aluminium, region- and year-invariant in emissions.csv, read
# on "+ Grid" technologies so captive generation is zero:
#   Carbon Anode       2.093 tCO2e/t  = 100% of BAU  -> unabated
#   Carbon Anode+CCS   1.135 tCO2e/t  =  54% of BAU  -> ABATED under limb (a). MPP specifies
#       "90% capture of smelter process CO2, not PFCs or anode production emissions"
#       (Technical Appendix p.11), so it meets the 90% capture test on the stream it
#       addresses. It fails limb (b) badly: the 1.029 tCO2e/t of PFCs plus anode production
#       emissions sits outside the captured stream and survives. Counting it as abated is
#       therefore a decision about the capture rate, not about residual intensity, and it
#       means the anode milestone does NOT imply zero smelter process emissions.
#   Inert Anode        0.063 tCO2e/t  =   3% of BAU  -> abated on both limbs
ANODES = ["Carbon Anode+CCS", "Carbon Anode", "Inert Anode"]
ANODE_UNABATED = ["Carbon Anode"]

# --- Auxiliary ------------------------------------------------------------------------
# Not in MPP. Its aluminium model has two plant types, Refinery and Smelter; casting,
# remelting, recycling and semis are taken from the IAI 1.5DS instead (Appendix pp.3-4, 20),
# so IAI is the consistent source for the auxiliary milestones.
#
# IAI gives emissions and production by value chain step, GLOBAL ONLY, at 2018 and then
# 5-year intervals - no technology mix and no regional split. That changes how the two
# tests have to be applied, because there is no technology series to detect capacity
# additions in:
#
#   Phase out  is read off intensity against limb (b) of the abatement rule directly: the
#              first year auxiliary intensity falls to <= 10% of its 2018 level, at which
#              point the remaining fleet is abated by definition.
#   No new     is the phase-out year less the equipment lifetime, since a fossil furnace
#              built in year Y is still operating in Y + lifetime. This is the same logic
#              that underpins the Power spec's "no new" milestones.
#
# Auxiliary is the three post-primary value chain steps. Primary casting is NOT separable -
# IAI folds it into "Primary Aluminium" as an unlabelled residual (2018: 1036.6 total less
# 823.3 electrolysis less 171.5 refining = 41.8 Mt, which also carries bauxite mining and
# anode production).
AUXILIARY_STEPS = ["Recycled Aluminium",          # collection, decoating, scrap remelting
                   "Internal Scrap/Fabrication Scrap",   # internal scrap remelting
                   "Semis Process"]               # rolling, extrusion, casting furnaces
AUXILIARY_DENOMINATOR = "Semis Shipments"   # all auxiliary throughput passes through semis
AUXILIARY_FILE = "IAI_1.5 Scenario Dataset.xlsx"
AUXILIARY_SHEET = "1.5"
AUXILIARY_BASE_YEAR = 2018

# Lifetime of fossil-fired thermal equipment, used only for the auxiliary "no new" year.
# 25 years is MPP's own assumption for every boiler type (Technical Appendix Exhibit TA3.1).
# IAI publishes no lifetime, so this is an imported assumption - confirm before publishing.
EQUIPMENT_LIFETIME = 25


# ======================================================================================
# The two tests
# ======================================================================================

def no_new_year(series, threshold):
    """Year after the last year the series grew beyond its prior running maximum.

    2020 is the initial asset stack, so it is not treated as a capacity addition.
    """
    prior_max = series.cummax().shift(1).fillna(-1)
    grew = series[(series > prior_max + threshold) & (series.index > 2020)]
    return int(grew.index.max()) + 1 if len(grew) else 2021


def phase_out_year(series, threshold):
    """First year at or below the threshold that stays there. None if it never does."""
    below = [y for y in series.index
             if series.loc[y] <= threshold and (series.loc[series.index >= y] <= threshold).all()]
    return int(min(below)) if below else None


def apply_tests(group, region, label, unit):
    """Run both tests on one technology group. group is technologies x years."""
    total = group.sum()
    threshold = max(MATERIALITY * total.loc[2020], EPS)

    # Per-technology test: switching between two unabated technologies is a new asset.
    per_tech = {}
    for tech, series in group.iterrows():
        if series.max() <= threshold:
            continue
        per_tech[tech] = no_new_year(series, threshold)

    phase_out = phase_out_year(total, threshold)
    return {"Group": label, "Region": region, "Unit": unit,
            "2020": round(total.loc[2020], 2),
            "2035": round(total.loc[2035], 2),
            "2050": round(total.loc[2050], 2),
            "Materiality threshold": round(threshold, 3),
            "No New Year": max(per_tech.values()) if per_tech else 2021,
            "No New Year (group net)": no_new_year(total, threshold),
            "Phase Out Year": phase_out if phase_out else BACKSTOP,
            "Phase Out From Backstop": phase_out is None,
            "Detail": "; ".join(f"{k} {v}" for k, v in sorted(per_tech.items()))}


# ======================================================================================
# MPP published production - digester, calciner, anode
# ======================================================================================

def load_mpp(plant_type):
    """Published 1.5DS annual production, Mt, technologies x years, per region."""
    out = {}
    for region, filename in MPP_BOOKS.items():
        df = pd.read_excel(DATA_DIR / filename, sheet_name=SHEET)
        df = df[(df["scenario"] == SCENARIO) & (df["plant_type"] == plant_type)]
        out[region] = df.pivot_table(index="technology", columns="year", values="value",
                                     aggfunc="sum").fillna(0).sort_index(axis=1)
    return out


def component_of(tech, plant_type, part):
    """Boiler or calciner for a refinery technology, anode for a smelter technology."""
    if plant_type == "Smelter":
        for anode in ANODES:          # "Carbon Anode+CCS" also starts with "Carbon Anode"
            if tech.startswith(anode):
                return anode
        raise ValueError(tech)
    return tech.split(" + ")[0 if part == "boiler" else 1]


def mpp_milestone(production, plant_type, part, unabated, label, unit):
    """Milestones for one MPP technology group, per region.

    Group production is summed over every full technology string whose component is
    unabated, then re-indexed on the component so the per-technology test sees one series
    per unabated technology rather than one per anode-power or boiler-calciner pair.
    """
    rows = []
    for region, pivot in production.items():
        keep = [t for t in pivot.index if component_of(t, plant_type, part) in unabated]
        group = pivot.loc[keep].copy()
        group.index = [component_of(t, plant_type, part) for t in keep]
        group = group.groupby(level=0).sum()
        if not len(group) or group.to_numpy().max() <= EPS:
            continue
        rows.append(apply_tests(group, region, label, unit))
    return rows


# ======================================================================================
# IAI 1.5DS - auxiliary
# ======================================================================================

def read_iai_table(marker):
    """One IAI table, indexed by row label with years as columns.

    Tables are laid out as a "Table N: ..." marker in column 0, then the year header three
    rows below and the data from four rows below until the first blank label.
    """
    raw = pd.read_excel(DATA_DIR / AUXILIARY_FILE, sheet_name=AUXILIARY_SHEET, header=None)
    start = raw.index[raw[0].astype(str).str.startswith(marker)][0]
    years = raw.iloc[start + 3, 1:7].astype(int).tolist()

    table = {}
    for i in range(start + 4, len(raw)):
        label = raw.iloc[i, 0]
        if pd.isna(label):
            break
        table[label] = pd.Series(raw.iloc[i, 1:7].astype(float).values, index=years)
    return pd.DataFrame(table).T


def auxiliary_intensity():
    """Global auxiliary emissions intensity, tCO2e per tonne semis shipped.

    Emissions from the three post-primary steps over semis shipments. Intensity rather than
    absolute emissions, because semis shipments grow 57% to 2050 and an intensity test is
    what the abatement rule is written against.
    """
    emissions = read_iai_table("Table 2")
    production = read_iai_table("Table 3")
    return (emissions.loc[AUXILIARY_STEPS].sum()
            / production.loc[AUXILIARY_DENOMINATOR])


def auxiliary_milestones():
    """Phase-out and no-new years for unabated fossil auxiliary, from the intensity curve."""
    intensity = auxiliary_intensity()
    share_of_base = intensity / intensity.loc[AUXILIARY_BASE_YEAR]

    abated = share_of_base[share_of_base <= 0.10]
    phase_out = int(abated.index.min()) if len(abated) else None
    from_backstop = phase_out is None
    if from_backstop:
        phase_out = BACKSTOP

    return {"intensity": intensity, "share_of_base": share_of_base,
            "phase_out": phase_out, "from_backstop": from_backstop,
            "no_new": phase_out - EQUIPMENT_LIFETIME}


# ======================================================================================
# Run
# ======================================================================================

pd.set_option("display.width", 250)

refinery = load_mpp("Refinery")
smelter = load_mpp("Smelter")

rows = []
rows += mpp_milestone(refinery, "Refinery", "boiler", DIGESTER_UNABATED,
                      "Unabated fossil digester", "Mt alumina")
rows += mpp_milestone(refinery, "Refinery", "calciner", CALCINER_UNABATED,
                      "Unabated fossil calciner", "Mt alumina")
rows += mpp_milestone(smelter, "Smelter", "anode", ANODE_UNABATED,
                      "Unabated carbon anode", "Mt aluminium")

# Auxiliary. IAI is global, so the same year is reported for both regions rather than
# leaving the rows empty - the milestone is real, it just carries no regional detail.
auxiliary = auxiliary_milestones()
for region in MPP_BOOKS:
    rows.append({"Group": "Unabated fossil auxiliary", "Region": region,
                 "Unit": "tCO2e/t semis",
                 "2020": round(auxiliary["intensity"].loc[AUXILIARY_BASE_YEAR], 3),
                 "2035": round(auxiliary["intensity"].loc[2035], 3),
                 "2050": round(auxiliary["intensity"].loc[2050], 3),
                 "Materiality threshold": "10% of 2018 intensity",
                 "No New Year": auxiliary["no_new"],
                 "No New Year (group net)": auxiliary["no_new"],
                 "Phase Out Year": auxiliary["phase_out"],
                 "Phase Out From Backstop": auxiliary["from_backstop"],
                 "Detail": "global, from IAI 1.5DS intensity; no regional split"})

milestones = pd.DataFrame(rows)
milestones.to_csv(DATA_DIR / "milestones_aluminium.csv", index=False)

print("=" * 118)
print("ALUMINIUM ASSET TRANSITION MILESTONES")
print("MPP 1.5DS published production; IAI 1.5DS for auxiliary (global only)")
print("=" * 118)
cols = ["Group", "Region", "Unit", "2020", "2035", "2050",
        "No New Year", "Phase Out Year", "Phase Out From Backstop"]
print(milestones[cols].to_string(index=False))

print("\n" + "-" * 118)
print("Last capacity addition by technology, and the group-net reading of the same test")
print("-" * 118)
for _, row in milestones.iterrows():
    print(f"{row['Group']:<44} {row['Region']:<7} group net {row['No New Year (group net)']}"
          f"   |  {row['Detail']}")

print("\n" + "=" * 118)
print("SPECIFICATION SHEET TABLE")
print("=" * 118)
spec = [("No new unabated fossil digester", "Unabated fossil digester", "No New Year"),
        ("Phase out unabated fossil digester", "Unabated fossil digester", "Phase Out Year"),
        ("No new unabated fossil calciner", "Unabated fossil calciner", "No New Year"),
        ("Phase out unabated fossil calciner", "Unabated fossil calciner", "Phase Out Year"),
        ("Phase out unabated carbon anode", "Unabated carbon anode", "Phase Out Year"),
        ("No new unabated fossil auxiliary", "Unabated fossil auxiliary", "No New Year"),
        ("Phase out unabated fossil auxiliary", "Unabated fossil auxiliary", "Phase Out Year")]


def cell(group, region, column):
    row = milestones[(milestones["Group"] == group) & (milestones["Region"] == region)]
    if not len(row):
        return "-"
    year = int(row.iloc[0][column])
    return f"{year}*" if column == "Phase Out Year" and row.iloc[0][
        "Phase Out From Backstop"] else str(year)


print(f"{'Milestone':<40}{'China':>10}{'RoW':>10}")
for label, group, column in spec:
    print(f"{label:<40}{cell(group, 'China', column):>10}{cell(group, 'RoW', column):>10}")

print("\n* set by the 2050 net-zero backstop: the source scenario does not reach the")
print("  abatement threshold by 2050 on its own.")
print("Auxiliary carries the same year in both regions - IAI 1.5DS is global, with no")
print("regional disaggregation, and its no-new year assumes a 25-year equipment lifetime.")

print("\n" + "-" * 118)
print("Auxiliary intensity, tCO2e per tonne semis shipped, and % of 2018")
print("-" * 118)
aux = pd.DataFrame({"Intensity": auxiliary["intensity"].round(4),
                    "% of 2018": (auxiliary["share_of_base"] * 100).round(1)})
print(aux.T.to_string())
