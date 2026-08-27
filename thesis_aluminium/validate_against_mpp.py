"""Acceptance test for MPP aluminium model re-runs (choice 18 in pathway_derivation_choices.md).

Compares a local model run's production volumes against MPP's published workbooks at
plant_type x technology x year x {China, Rest of the World}.

MPP publishes three workbooks: global, China, and Rest of the World. The two regional
files are an exact partition of the global one, so China + RoW is the finest regional
split the published data supports. MPP model regions beginning "China" map to China;
everything else maps to RoW.

Production is the right validation target because the pathway consumes only production
volume and technology per asset-year — emission factors come from unmodified repo inputs.
Emissions cannot be used: MPP's own published emissions and intensity sheets disagree with
each other by a factor of ~1.7.

Usage:
    python validate_against_mpp.py                    # validate the live run
    python validate_against_mpp.py RUN_original       # validate a saved run directory
"""

import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(".")
MPP = DATA_DIR / "mpp-shared-code" / "aluminium" / "data" / "lc"

PUBLISHED = {
    "China": DATA_DIR / "mpp_aluminium_net_zero_outputs (1).xlsx",
    "RoW": DATA_DIR / "mpp_aluminium_net_zero_outputs (2).xlsx",
}

RUNS = {
    "Smelter": ("def", "plant_stack_transition_aluminium_lc_def.csv"),
    "Refinery": ("def_refineries", "plant_stack_transition_aluminium_lc_def_refineries.csv"),
}

REPORT_YEARS = [2020, 2025, 2030, 2035, 2040, 2045, 2050]
TOLERANCE = 0.5  # Mt, for counting materially mismatched technology-years


def published_volumes(region, plant_type):
    """Published Mt by (technology, year) for one region and plant type, 1.5DS only."""
    df = pd.read_excel(PUBLISHED[region], sheet_name="Annual_production_volume_Mt_df")
    df = df[(df["scenario"] == "1.5DS") & (df["plant_type"] == plant_type)]
    return df.groupby(["technology", "year"])["value"].sum()


def our_volumes(run_dir, subdir, filename):
    """Our Mt by (region, technology, year), with MPP regions collapsed to China / RoW."""
    path = run_dir / filename if run_dir else MPP / subdir / "final" / filename
    df = pd.read_csv(path)
    df["reg"] = ["China" if str(r).startswith("China") else "RoW" for r in df["region"]]
    return df.groupby(["reg", "technology", "year"])["annual_production_volume"].sum()


def compare(plant_type, region, pub, ours):
    """Align published and ours on the union of technology-years and report the gaps."""
    index = sorted(set(pub.index) | set(ours.index))
    df = pd.DataFrame(
        {"published": pub.reindex(index).fillna(0), "ours": ours.reindex(index).fillna(0)}
    )
    df["diff"] = df["ours"] - df["published"]

    totals = df.groupby(level="year")[["published", "ours"]].sum()
    totals["diff"] = totals["ours"] - totals["published"]

    print(f"\n===== {plant_type} / {region} =====")
    print("Totals by year (Mt):")
    print(totals.loc[[y for y in REPORT_YEARS if y in totals.index]].round(2).to_string())
    print(
        f"  max |diff| on any technology-year : {df['diff'].abs().max():.3f} Mt\n"
        f"  technology-years off by >{TOLERANCE} Mt   : {(df['diff'].abs() > TOLERANCE).sum()} of {len(df)}"
    )

    latest = df[df.index.get_level_values("year") == 2050].droplevel("year")
    latest = latest[(latest["published"] > 0.01) | (latest["ours"] > 0.01)]
    latest = latest.reindex(latest["diff"].abs().sort_values(ascending=False).index)
    print("\n  Largest 2050 technology mismatches:")
    print(latest.head(8).round(3).to_string())
    return df["diff"].abs().max()


run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
print(f"Validating: {run_dir if run_dir else 'live run in mpp-shared-code'}")

worst = {}
for plant_type, (subdir, filename) in RUNS.items():
    ours_all = our_volumes(run_dir, subdir, filename)
    for region in PUBLISHED:
        if region not in ours_all.index.get_level_values(0):
            continue
        worst[(plant_type, region)] = compare(
            plant_type, region, published_volumes(region, plant_type), ours_all.loc[region]
        )

print("\n\n===== SUMMARY: max |diff| in Mt on any technology-year =====")
for (plant_type, region), value in worst.items():
    print(f"  {plant_type:9s} {region:6s} {value:8.3f}")
