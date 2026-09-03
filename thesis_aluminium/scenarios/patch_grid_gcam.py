"""Rescale MPP scope-2 grid emissions to a GCAM scenario's grid intensity (from the cache).

Same mechanism as patch_grid_iam.py, but the grid intensity comes from pipeline/gcam_extract's
cached GCAM runs (pipeline/gcam_cache/) instead of the AR6 IAM database. Scope 1 (anode, captive
power) is untouched, so the grid acts on the grid-vs-captive margin only.

Importable: apply_gcam_grid(model_dir, scen). Also runnable: python patch_grid_gcam.py <model> <scen>
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
import gcam_extract  # noqa: E402

REFERENCE_TECHNOLOGY = "Inert Anode + Grid"   # plain grid supply, to read MPP's implied intensity


def _patch_folder(model, folder, grid):
    """grid: DataFrame [year x MPP region], t CO2/MWh."""
    path = model / "aluminium" / "data" / "lc" / folder / "intermediate" / "emissions.csv"
    emissions = pd.read_csv(path)
    inputs = pd.read_csv(path.parent / "inputs_outputs.csv")
    electricity = inputs[inputs["parameter"] == "Electricity Consumption"]

    reference = emissions[emissions["technology"] == REFERENCE_TECHNOLOGY]
    if reference.empty:
        print(f"  {folder}: no grid technology, scope 2 left unchanged")
        return

    scale = {}
    for (region, year), rows in reference.groupby(["region", "year"]):
        if region not in grid.columns or year not in grid.index:
            continue
        mwh = electricity[
            (electricity["region"] == region)
            & (electricity["year"] == year)
            & (electricity["technology"] == REFERENCE_TECHNOLOGY)
        ]["value"]
        if mwh.empty or mwh.iloc[0] == 0:
            continue
        mpp_intensity = rows["co2_scope2"].iloc[0] / mwh.iloc[0]
        target = grid.loc[year, region]
        scale[(region, year)] = target / mpp_intensity if mpp_intensity > 0 else 0

    before = emissions["co2_scope2"].sum()
    emissions["co2_scope2"] = emissions.apply(
        lambda row: row["co2_scope2"] * scale.get((row["region"], row["year"]), 1), axis=1)
    after = emissions["co2_scope2"].sum()
    emissions.to_csv(path, index=False)
    print(f"  {folder}: scope 2 total {before:.1f} -> {after:.1f}")


def apply_gcam_grid(model_dir, scen):
    model = Path("models") / model_dir if not str(model_dir).startswith("/") else Path(model_dir)
    grid = gcam_extract.load_grid(scen)          # [year x MPP region], t CO2/MWh, from cache
    grid.index = grid.index.astype(int)
    print(f"Applying GCAM {scen} grid intensity to {model.name}")
    for folder in ["def", "def_refineries"]:
        _patch_folder(model, folder, grid)


if __name__ == "__main__":
    apply_gcam_grid(sys.argv[1], sys.argv[2])
