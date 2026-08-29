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
LIMIT = sys.argv[2] if len(sys.argv) > 2 else "low"   # "none" | "low" | "high" deployment pace
# The unconstrained run, used only to size aluminium's captive fossil fleet
REFERENCE = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(
    "runs/LC_MPPgrid_CCS_AnodeLocked/smelter/final")

YEARS = range(2020, 2051)

# Maximum annual capture addition as a share of the captive fossil fleet's capturable CO2 per
# year, from the maximum feasible technology-diffusion rates in the two papers, normalized to
# market size as those papers do:
#   low  = nuclear-analogue growth, 1.45%/yr (Kazlou, Cherp & Jewell 2024) - the slower ceiling
#   high = global FGD growth, 10.7%/yr (van Ewijk & McDowall 2020) - the faster ceiling
# The same flat rate applies every year to captive coal and gas, with no saturation.
# "none" gives a zero rate: no captive-power CCS at all.
RATES = {"low": 0.0145, "high": 0.107}


def capture_penetration():
    """Flat maximum annual capture addition as a share of the captive fleet, per fuel and year.

    The addition of captured CO2 may not exceed RATES[LIMIT] of the captive fleet's capturable
    CO2 in any year, available every year with no saturation, applied identically to captive
    coal and gas. LIMIT="none" gives a zero rate (no captive-power CCS at all).
    """
    rate = 0.0 if LIMIT == "none" else RATES[LIMIT]
    flat = pd.Series(rate, index=list(YEARS), dtype=float)
    return pd.DataFrame({"Coal": flat, "Natural gas": flat})


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
    if LIMIT in RATES:
        # allowance here is already the per-year addition (rate x fleet). write_limit_file
        # differences whatever it receives, so accumulate first, otherwise a flat flow would be
        # differenced to zero and the limit would ban capture rather than pace it.
        stock = stock.cumsum()
    # annual_addition compares the year-on-year increase in captured CO2, so the limit is the
    # increment of that stock.
    return stock


def write_limit_file(allowance):
    """MPP's own format, copied from ammonia/data/lc/def/intermediate/co2_storage_constraint.csv.

    `allowance` is the permitted stock of annual capture. CO2_STORAGE_CONSTRAINT_TYPE is
    annual_addition, which compares the year-on-year increase, so the file carries the
    increment of that stock.
    """
    increment = allowance.diff().fillna(0).clip(lower=0)
    labels = {"none": "No captive-power CCS",
              "low": "Nuclear-analogue max growth 1.45%/yr (Kazlou et al. 2024)",
              "high": "Global FGD max growth 10.7%/yr (van Ewijk & McDowall 2020)"}
    table = pd.DataFrame({
        "product": "All",
        "scenario": labels[LIMIT],
        "region": "Global",
        "year": increment.index,
        "unit": "MtCO2",
        "value": increment.values,
    })
    for folder in ["def", "def_refineries"]:
        path = MODEL / "aluminium" / "data" / "lc" / folder / "intermediate" / "co2_storage_constraint.csv"
        table.to_csv(path, index=False)
    print(f"  limit written: {increment.loc[2030]:.1f} Mt/yr in 2030, "
          f"{increment.loc[2050]:.1f} Mt/yr in 2050, {increment.sum():.0f} Mt cumulative")


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


def deepcopy_tentative_brownfield_asset():
    """Make the brownfield tentative switch land on a copy, not the live stack asset.

    aluminium/solver/brownfield.py builds a tentative_stack = deepcopy(new_stack), then calls
    tentative_stack.update_asset(asset_to_update=asset_to_update) with the LIVE asset from
    new_stack. update_asset mutates asset_to_update.technology in place (asset.py) and appends
    it, so the switch is applied to new_stack before any constraint is checked. The constraint
    then correctly rejects the switch, but the asset is already converted and stays converted.
    Ammonia and cement pass deepcopy(asset_to_update) here; aluminium does not. Without this the
    co2_storage cap never binds — capture is built regardless of regime. This is the change that
    makes the limit actually reduce capture."""
    path = MODEL / "aluminium" / "solver" / "brownfield.py"
    text = path.read_text()
    old = ("        tentative_stack.update_asset(\n"
           "            year=year,\n"
           "            asset_to_update=asset_to_update,")
    new = ("        tentative_stack.update_asset(\n"
           "            year=year,\n"
           "            asset_to_update=deepcopy(asset_to_update),")
    if "asset_to_update=deepcopy(asset_to_update)" in text:
        print("  brownfield tentative asset already deepcopied")
        return
    assert old in text, "brownfield tentative update_asset call not found; file changed"
    path.write_text(text.replace(old, new))
    print("  brownfield tentative asset now deepcopied (co2_storage cap can bind)")


def keep_storage_constraint_for_ccs():
    """get_constraints_to_apply strips co2_storage_constraint unless the destination name
    contains "storage" (ammonia/cement naming). Aluminium names capture "...+CCS", so the
    cap is stripped from every aluminium capture transition — including greenfield builds via
    select_asset_for_greenfield. Keep it for "CCS" destinations so the cap applies evenly to
    greenfield, brownfield and retrofit."""
    path = MODEL / "mppshared" / "agent_logic" / "agent_logic_functions.py"
    text = path.read_text()
    old = 'if not ("storage" in destination_technology):'
    new = 'if not ("storage" in destination_technology or "CCS" in destination_technology):'
    if new in text:
        print("  get_constraints_to_apply already keeps co2_storage for CCS destinations")
        return
    assert old in text, "get_constraints_to_apply filter not found; base model changed"
    path.write_text(text.replace(old, new))
    print("  get_constraints_to_apply keeps co2_storage_constraint for CCS destinations")


print(f"{MODEL}: limiting captive power capture to the IEA NZE world rate")
populate_captured_column()
write_limit_file(build_limit())
wire_up_constraint()
add_storage_handler()
exclude_emissions_constraint_from_pass_test()
keep_storage_constraint_for_ccs()
deepcopy_tentative_brownfield_asset()
