"""Fix 1 — the stranded fossil-boiler tail in MPP's refinery switch table.

MPP's refinery switch table wires every unabated fossil boiler to a clean end-state only through
a transition-class intermediate (e.g. Gas-Boiler+Gas-Calciner -> H2-Boiler+Gas-Calciner ->
H2-Boiler+H2-Calciner). The technology moratorium bans renovation INTO transition tech from 2040,
so after 2040 a plant still on an initial fossil boiler cannot take that first hop, and its only
moratorium-proof exits are the two concentrated-solar-thermal (CST) end-states, which cannot carry
the load. The plant strands and refining breaks above budget. This is the refinery twin of the
frozen inert-anode power source on the smelter side (MODEL_REFERENCE Section 20 / decision 15).

Fix: add a DIRECT brownfield_renovation row from each unabated (initial-class) fossil boiler to
each real clean end-state, so a stranded plant jumps to a clean end-state in one hop. End-state
destinations are never blocked by the moratorium. Economics/year/region are copied from the
destination's own existing renovation rows (reassigning technology_origin), so nothing is invented.

Grid-agnostic: apply identically to every refinery model copy.

Importable: apply_switch_fix(model_dir). Also runnable: python patch_refining_switches.py <model>
"""

import sys
from pathlib import Path

import pandas as pd

# The 6 unabated (initial-class) fossil-boiler technologies that can strand.
ORIGINS = [f"{b}-Boiler + {c}-Calciner"
           for b in ("Coal", "Gas", "Oil")
           for c in ("Gas", "Oil")]

# The 6 real clean end-states a stranded plant must be able to reach in one hop.
DESTINATIONS = [f"{b}-Boiler + {c}-Calciner"
                for b in ("Elec", "H2", "MVR-Fossil")
                for c in ("Elec", "H2")]

KEY = ["product", "region", "year", "switch_type",
       "technology_origin", "technology_destination"]


def apply_switch_fix(model_dir):
    model = Path("models") / model_dir if not str(model_dir).startswith("/") else Path(model_dir)
    live = (model / "aluminium" / "data" / "lc" / "def_refineries"
            / "intermediate" / "technology_transitions.csv")
    df = pd.read_csv(live)
    before = len(df)

    new_rows = []
    for destination in DESTINATIONS:
        template = df[
            (df["technology_destination"] == destination)
            & (df["switch_type"] == "brownfield_renovation")
        ]
        if template.empty:
            raise SystemExit(f"No brownfield_renovation template rows for {destination}")
        # One representative economics per (product, region, year) for this destination.
        template = template.drop_duplicates(
            subset=["product", "region", "year", "switch_type", "technology_destination"])
        for origin in ORIGINS:
            if origin == destination:
                continue
            rows = template.copy()
            rows["technology_origin"] = origin
            new_rows.append(rows)

    added = pd.concat(new_rows, ignore_index=True)

    # Drop any origin->destination pair (by full key) that already exists, so nothing duplicates.
    added = added.merge(df[KEY].drop_duplicates(), on=KEY, how="left", indicator=True)
    added = added[added["_merge"] == "left_only"].drop(columns="_merge")

    df = pd.concat([df, added], ignore_index=True)
    df.to_csv(live, index=False)

    print(f"{model.name}: refinery switch rows {before} -> {len(df)} ({len(added)} added)")
    for origin in ORIGINS:
        got = sorted(set(df[(df["technology_origin"] == origin)
                           & (df["technology_destination"].isin(DESTINATIONS))]
                         ["technology_destination"].unique()))
        print(f"  {origin:30s} -> {len(got)}/{len(DESTINATIONS)} clean end-states")
    return added


if __name__ == "__main__":
    apply_switch_fix(sys.argv[1])
