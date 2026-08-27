"""Use MPP's full switch table instead of the restricted one they ship as live, then add
the six missing power-source switches.

MPP's 1.5C smelter folder holds three switch tables. The live filename the code reads,
technology_transitions.csv, carries 92 switch pairs. Their technology_transitions_original.csv
carries 132, and is a strict superset: the 40 extra pairs are all switches into captive power
with capture. Nothing in the live file is absent from the original. Section 23 of
MODEL_REFERENCE.md has the provenance.

This swaps the original in and then applies the same six switches as patch_unlock.py, so a
plant that has converted its anode can still change its power source.

Usage: python patch_fulltt.py <model_dir_name>   (relative to models/) [--no-extra-switches]

With --no-extra-switches it only swaps the table in, giving MPP's 132 untouched.
"""

import shutil
import sys
from pathlib import Path

import pandas as pd

MODEL = Path("models") / sys.argv[1]
FOLDER = MODEL / "aluminium" / "data" / "lc" / "def" / "intermediate"
LIVE = FOLDER / "technology_transitions.csv"

# Keep MPP's live file under a name that says what it is, then swap the full table in
shutil.copy(LIVE, FOLDER / "technology_transitions_MPP_LIVE_92.csv")
shutil.copy(FOLDER / "technology_transitions_original.csv", LIVE)

ORIGINS = ["Inert Anode + Natural Gas", "Inert Anode + Coal"]
# Each destination keeps the switch type the model already uses for it. A grid
# connection is a renovation; a small modular reactor is only ever a rebuild.
DESTINATIONS = {
    "Inert Anode + Grid": "brownfield_renovation",
    "Inert Anode + PPA+Grid": "brownfield_renovation",
    "Inert Anode + Small Modular Reactor": "brownfield_newbuild",
}

if "--no-extra-switches" in sys.argv:
    df = pd.read_csv(LIVE)
    pairs = df.groupby(["technology_origin", "technology_destination"]).ngroups
    print(f"{MODEL}: MPP's full table in place, {len(df)} rows, {pairs} switch pairs")
    raise SystemExit

df = pd.read_csv(LIVE)
before = len(df)

new_rows = []
for destination, switch_type in DESTINATIONS.items():
    template = df[
        (df["technology_destination"] == destination)
        & (df["switch_type"] == switch_type)
    ]
    if template.empty:
        raise SystemExit(f"No template rows found for {destination}")

    for origin in ORIGINS:
        rows = template.copy()
        rows["technology_origin"] = origin
        new_rows.append(rows)

added = pd.concat(new_rows, ignore_index=True)

# Drop any pair that already exists so nothing is duplicated
key = ["product", "region", "year", "switch_type", "technology_origin", "technology_destination"]
added = added.merge(df[key].drop_duplicates(), on=key, how="left", indicator=True)
added = added[added["_merge"] == "left_only"].drop(columns="_merge")

df = pd.concat([df, added], ignore_index=True)
df.to_csv(LIVE, index=False)

pairs = df.groupby(["technology_origin", "technology_destination"]).ngroups
print(f"{MODEL}: rows {before} -> {len(df)} ({len(added)} added), {pairs} switch pairs")
for origin in ORIGINS:
    got = sorted(df[df["technology_origin"] == origin]["technology_destination"].unique())
    print(f"  {origin} -> {got}")
