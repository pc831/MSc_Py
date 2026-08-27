"""Limit capture on captive fossil power generation to the world rate in IEA WEO 2024 NZE.

Without this the model builds 72 GW of capture-equipped captive coal and gas for aluminium
alone, capturing 368 Mt CO2 in 2050 and 7.2 Gt cumulatively. That is 31% of the entire world
fossil power CCS fleet in NZE, for one industry.

The rule: aluminium's captive coal and gas plants get capture at the same rate as the world
fossil power fleet of the same fuel. No uplift and no discount. Coal and gas are handled
separately because their penetration diverges sharply, reaching 40.7% and 11.9% by 2050.

Scope is power generation only. Anode capture is left unlimited, so `co2_scope1_captured` is
populated with the power component alone.

Six things are patched, because a limit file on its own does nothing:
  1. `co2_scope1_captured` in emissions.csv, empty as shipped, so the constraint reads zero
     captured and passes every year no matter what limit is set
  2. `co2_storage_constraint.csv`, in the same format MPP ships for ammonia
  3. the config and the pathway constructor, neither of which wires the constraint up
  4. brownfield's failure handling, copied verbatim from ammonia. MPP wrote this handler for
     ammonia and never connected it for aluminium, so without it the constraint blocks a
     switch but leaves it at the top of the ranking table and the solver re-picks it forever

  5. the `deepcopy` on the tentative asset that ammonia and cement both have and aluminium
     does not. Without it the switch is applied to the live stack before any constraint is
     checked, so rejecting it does nothing. This is the change that makes the limit bind.
  6. `CO2_STORAGE_CONSTRAINT_TYPE = "annual_addition"`, the setting ammonia uses. The
     alternative, `annual_cumulative`, caps the running total, so once the fleet reaches the
     cap every capture switch is rejected for the rest of the run and plants strand on
     unabated fossil. `annual_addition` caps the year-on-year increase instead, giving a fresh
     allowance each year, which is what limiting rather than banning requires.

The failure handler uses `remove_transition`, MPP's own function, the one the emissions
constraint uses a few lines above. Ammonia removes the whole destination technology instead,
but their constraint never binds so that path was never exercised; with a binding limit it
wipes every capture route for the year and strands plants on unabated fossil.

Greenfield stays unconstrained, which is MPP's design in every sector: neither ammonia nor
cement calls check_constraints there either.

Usage: python patch_ccs_limit.py <model_dir_name>   (relative to models/)
"""

import sys
from pathlib import Path

import pandas as pd

MODEL = Path("models") / sys.argv[1]
WORLD = Path("../inputs/WEO2024_AnnexA_Free_Dataset_World.csv")
# The unconstrained run, used only to size aluminium's captive fossil fleet
REFERENCE = Path("runs/LC_MPPgrid_CCS_AnodeLocked/smelter/final")

YEARS = range(2020, 2051)


def capture_penetration():
    """Share of world fossil power capacity that is capture-equipped, per fuel and year.

    IEA WEO 2024 Net Zero scenario. Only the World file carries this; the regional file has
    Advanced economies alone for NZE. Published at 2023, 2030, 2035, 2040 and 2050, so the
    intervening years are interpolated.
    """
    weo = pd.read_csv(WORLD)
    nze = weo[(weo["SCENARIO"].str.contains("Net Zero"))
              & (weo["FLOW"] == "Electrical capacity")]
    capacity = nze.pivot_table(index="PRODUCT", columns="YEAR", values="VALUE")

    rates = {}
    for fuel in ["Coal", "Natural gas"]:
        with_ccus = capacity.loc[f"{fuel}: with CCUS"]
        total = capacity.loc[f"{fuel}: unabated"] + with_ccus
        rates[fuel] = with_ccus / total
    return pd.DataFrame(rates).reindex(YEARS).interpolate(limit_direction="both")


def emission_factors(folder):
    path = MODEL / "aluminium" / "data" / "lc" / folder / "intermediate" / "emissions.csv"
    return path, pd.read_csv(path)


def power_capture_rate(technology, region, year, factors):
    """CO2 captured by the power plant alone, tonnes per tonne of aluminium."""
    anode, power = technology.split(" + ", 1)
    if not power.endswith("+CCS"):
        return 0.0
    uncaptured = f"{anode} + {power[:-4]}"
    try:
        return factors.loc[(uncaptured, region, year)] - factors.loc[(technology, region, year)]
    except KeyError:
        return 0.0


def populate_captured_column():
    """Fill co2_scope1_captured with the power generation component, in every data folder."""
    for folder in ["def", "def_refineries"]:
        path, emissions = emission_factors(folder)
        if folder == "def_refineries":
            # No refinery technology contains CCS, so nothing is ever captured there
            emissions["co2_scope1_captured"] = 0.0
        else:
            factors = emissions.set_index(["technology", "region", "year"])["co2_scope1"]
            emissions["co2_scope1_captured"] = [
                power_capture_rate(t, r, y, factors)
                for t, r, y in zip(emissions["technology"], emissions["region"], emissions["year"])
            ]
        emissions.to_csv(path, index=False)
        nonzero = (emissions["co2_scope1_captured"] > 0).sum()
        print(f"  {folder}: co2_scope1_captured populated, {nonzero} rows nonzero")


def build_limit():
    """Annual capture allowance in Mt CO2, from the world rate times aluminium's own fleet."""
    rates = capture_penetration()

    _, emissions = emission_factors("def")
    factors = emissions.set_index(["technology", "region", "year"])["co2_scope1"]

    reference = pd.read_csv(next(REFERENCE.glob("interface_outputs_*.csv")))
    volume = reference[(reference["technology"] != "All")
                       & (reference["parameter"] == "Annual production volume")]

    def uncaptured_power_emissions(technology, region, year):
        """Power generation emissions of this plant if it had no capture, t per t."""
        anode, power = technology.split(" + ", 1)
        base = power[:-4] if power.endswith("+CCS") else power
        try:
            return (factors.loc[(f"{anode} + {base}", region, year)]
                    - factors.loc[(f"{anode} + Grid", region, year)])
        except KeyError:
            return 0.0

    allowance = {}
    for year in YEARS:
        total = 0.0
        for row in volume[volume["year"] == year].itertuples():
            power = row.technology.split(" + ", 1)[1]
            if power.startswith("Coal"):
                fuel = "Coal"
            elif power.startswith("Natural Gas"):
                fuel = "Natural gas"
            else:
                continue
            total += rates.loc[year, fuel] * row.value * uncaptured_power_emissions(
                row.technology, row.region, year)
        allowance[year] = total
    stock = pd.Series(allowance)
    # annual_addition compares the year-on-year increase in captured CO2, so the limit is the
    # increment of that stock. Kept as increments here; the stock is written alongside for
    # reference.
    return stock


def write_limit_file(allowance):
    """MPP's own format, copied from ammonia/data/lc/def/intermediate/co2_storage_constraint.csv.

    `allowance` is the permitted stock of annual capture. CO2_STORAGE_CONSTRAINT_TYPE is
    annual_addition, which compares the year-on-year increase, so the file carries the
    increment of that stock.
    """
    increment = allowance.diff().fillna(0).clip(lower=0)
    table = pd.DataFrame({
        "product": "All",
        "scenario": "IEA WEO 2024 NZE world fossil CCS addition rate",
        "region": "Global",
        "year": increment.index,
        "unit": "MtCO2",
        "value": increment.values,
    })
    for folder in ["def", "def_refineries"]:
        path = MODEL / "aluminium" / "data" / "lc" / folder / "intermediate" / "co2_storage_constraint.csv"
        table.to_csv(path, index=False)
    print(f"  limit written: {allowance.loc[2030]:.0f} Mt in 2030, "
          f"{allowance.loc[2050]:.0f} Mt in 2050, {allowance.sum():.0f} Mt cumulative")


def exclude_emissions_constraint_from_pass_test():
    """Stop the emissions constraint vetoing every brownfield switch.

    `check_annual_carbon_budget_constraint` is an absolute test: is the whole stack under
    budget after this switch, not does this switch reduce emissions. While the stack is above
    budget it rejects everything, including switches that cut emissions, and the solver
    deadlocks. It looks harmless in the shipped model only because the switch lands before the
    check, so the rejection never mattered.

    Ammonia, which does enforce its constraints, omits emissions_constraint from
    CONSTRAINTS_TO_APPLY entirely. We exclude it from the brownfield pass test instead, the
    same way regional_constraint already is, so the elif chain below still finds the key. The
    budget still drives the transition through the early exit at brownfield.py:82, which reads
    pathway.carbon_budget directly and does not consult CONSTRAINTS_TO_APPLY.
    """
    path = MODEL / "aluminium" / "solver" / "brownfield.py"
    text = path.read_text()
    if "emissions_constraint excluded" in text:
        print("  brownfield pass test already excludes emissions_constraint")
        return
    old = '                if k in pathway.constraints_to_apply and k != "regional_constraint"'
    new = ('                # emissions_constraint excluded the same way regional_constraint is.\n'
           '                if k in pathway.constraints_to_apply\n'
           '                and k not in ("regional_constraint", "emissions_constraint")')
    assert old in text, "pass test not found, brownfield.py has changed"
    path.write_text(text.replace(old, new))
    print("  emissions_constraint excluded from the brownfield pass test")


def wire_up_constraint():
    """Add the constraint to the config and pass it to the pathway constructor."""
    config = MODEL / "aluminium" / "config_aluminium.py"
    text = config.read_text()
    text = text.replace(
        '"lc": ["emissions_constraint", "rampup_constraint"],',
        '"lc": ["emissions_constraint", "rampup_constraint", "co2_storage_constraint"],')
    if "CO2_STORAGE_CONSTRAINT_TYPE" not in text:
        text = text.replace(
            "YEAR_2050_EMISSIONS_CONSTRAINT = 2051",
            'CO2_STORAGE_CONSTRAINT_TYPE = "annual_addition"\n\n'
            "YEAR_2050_EMISSIONS_CONSTRAINT = 2051")
    config.write_text(text)

    simulate = MODEL / "aluminium" / "solver" / "simulate.py"
    text = simulate.read_text()
    text = text.replace(
        "from aluminium.config_aluminium import (",
        "from aluminium.config_aluminium import (\n    CO2_STORAGE_CONSTRAINT_TYPE,")
    text = text.replace(
        "        year_2050_emissions_constraint=YEAR_2050_EMISSIONS_CONSTRAINT,\n    )",
        "        year_2050_emissions_constraint=YEAR_2050_EMISSIONS_CONSTRAINT,\n"
        "        set_co2_storage_constraint=True,\n"
        "        co2_storage_constraint_type=CO2_STORAGE_CONSTRAINT_TYPE,\n    )")
    simulate.write_text(text)
    print("  constraint wired into config_aluminium.py and simulate.py")


def add_storage_handler():
    """Copy ammonia's CO2 storage failure handler into aluminium's brownfield agent.

    Verbatim from ammonia/solver/brownfield.py:194. Without it a failed storage check leaves
    the rejected switch at the top of the ranking table, so the solver selects it again on the
    next iteration and the constraint never narrows the choice set.
    """
    path = MODEL / "aluminium" / "solver" / "brownfield.py"
    text = path.read_text()
    if "Handle CO2 storage constraint" in text:
        print("  brownfield already carries the storage handler")
        return

    anchor = """        elif dict_constraints["rampup_constraint"] == False:
            df_rank = remove_all_transitions_with_destination_technology(
                df_rank, best_transition["technology_destination"]
            )"""
    handler = anchor + """
        # CO2 STORAGE
        # Copied from ammonia/solver/brownfield.py. MPP wrote this handler and wired it up for
        # ammonia only; aluminium checks the constraint and then ignores the answer.
        elif "co2_storage_constraint" in pathway.constraints_to_apply:
            if not dict_constraints["co2_storage_constraint"]:
                logger.debug(
                    "Handle CO2 storage constraint: removing destination technology"
                )
                df_rank = remove_all_transitions_with_destination_technology(
                    df_rank, best_transition["technology_destination"]
                )"""
    assert anchor in text, "rampup handler not found, brownfield.py has changed"
    path.write_text(text.replace(anchor, handler))
    print("  brownfield storage handler added, copied from ammonia")


print(f"{MODEL}: limiting captive power capture to the IEA NZE world rate")
populate_captured_column()
write_limit_file(build_limit())
wire_up_constraint()
add_storage_handler()
exclude_emissions_constraint_from_pass_test()
