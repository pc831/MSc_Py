# MPP aluminium model — verified reference

Every statement here was checked against source code or against output from the runs in
`scenarios/`. Line references are to `scenarios/models/model_clean/`, which is MPP commit `b09472f`
with three changes only: sector set to aluminium, a pandas 2 fix, and the smelter demand file
swapped for the 1.5C series.

Anything I have not verified is marked **UNVERIFIED**. Nothing else in this document is
inference.

---

## 1. Two runs, not one

Aluminium is two separate executions that never communicate.

| | Smelters | Refineries |
|---|---|---|
| Product | Aluminium | Alumina |
| Data folder | `aluminium/data/<pathway>/def/` | `.../def_refineries/` |
| Plants | 181 | 94 |
| Technology naming | `<anode> + <power source>` | `<boiler> + <calciner>` |
| Technologies | 25 | 31 |

They share one `config_aluminium.py`, so every config setting applies identically to both.
Only the input spreadsheets differ.

Alumina enters the smelter run as a fixed conversion factor of 1.935 tonnes of alumina per
tonne of aluminium (`inputs_outputs.csv`, parameter `Alumina Consumption`). One number, all
regions, all years, never changes. Nothing checks that the refinery run actually produced
that much alumina.

---

## 2. The four stages

`aluminium/main_aluminium.py:21` maps stage names to functions. `run_config` in
`config_aluminium.py:22` selects which run.

1. **`APPLY_IMPLICIT_FORCING`** (`aluminium/solver/implicit_forcing.py:32`) — deletes
   disallowed switches from the switch list, computes emission differences, writes
   `technologies_to_rank.csv`. **Overwrites MPP's committed copy of that file.**
2. **`MAKE_RANKINGS`** (`aluminium/solver/ranking.py:16`) — scores every surviving switch,
   writes `decommission_rank.csv`, `brownfield_rank.csv`, `greenfield_rank.csv`.
3. **`SIMULATE_PATHWAY`** (`aluminium/solver/simulate.py:94`) — the solve, 2020 to 2050.
4. **`CALCULATE_OUTPUTS`** (`aluminium/solver/output_processing.py:531`) — post-processing.

Stages 1 and 2 run once for all 31 years before the solve begins. A switch's rank in 2045 was
computed before the model knew anything about the 2045 fleet.

---

## 3. The yearly loop

`aluminium/solver/simulate.py:55-89`. Fixed order, every year:

```python
pathway = adjust_capacity_utilisation(pathway=pathway, year=year)
pathway = pathway.copy_stack(year=year)      # next year starts as a copy of this year
pathway.export_stack_to_csv(year)            # writes stack_<year>.csv
pathway = decommission(pathway=pathway, year=year)
pathway = brownfield(pathway=pathway, year=year)
pathway = greenfield(pathway=pathway, year=year)
```

Decommission, brownfield and greenfield all modify the **year+1** stack, not the current one.
`stack_<year>.csv` is written before they run, so it holds the stack as finalised by the
previous year's three agents.

---

## 4. Adjust capacity utilisation

`mppshared/agent_logic/agent_logic_functions.py:186`.

- Demand exceeds production → raise utilisation to 0.95, cheapest plant first
  (`increase_cuf_of_assets`, line 246)
- Production exceeds demand → cut utilisation to 0.60, most expensive plant first
  (`decrease_cuf_of_assets`, line 285)

Ordering uses `lcox` for aluminium (`mppshared/config.py`, `COST_METRIC_CUF_ADJUSTMENT`).
Both loops set utilisation to the threshold value directly, not incrementally, and stop as
soon as demand is met or the candidate list is empty.

The starting stack ships utilisation values from 0.039 to 1.064, including twelve refineries
above 1.0. The first call to this function overwrites most of them.

---

## 5. Decommission

`aluminium/solver/decommission.py:11`.

```python
surplus = production - demand
while surplus > 0:
    asset_to_remove = get_best_asset_to_decommission(...)
    new_stack.remove(asset_to_remove)
    surplus -= asset_to_remove.get_annual_production_volume()
```

That is the entire trigger. Oversupply, nothing else.

**Eligibility** (`mppshared/models/asset.py:542`) — two tests only:
- utilisation at or below 0.60
- age at least 10 years (`INVESTMENT_CYCLE`)

**Asset lifetime is never used.** `asset_lifetime` is stored on every plant and written to
outputs, but the only eligibility checks that read it are `asset.py:582` and `asset.py:640`,
both cement-only. No aluminium plant ever retires because of age.

**Selection** (`mppshared/agent_logic/decommission.py:18`) — take the top row of the
decommission ranking, find plants matching its origin technology and region, choose one at
random (`random.choice`, line 73). If no plant matches, that row is deleted and the next is
tried.

No constraint check is performed on decommissioning.

---

## 6. Brownfield — switching technology

`aluminium/solver/brownfield.py:21`. Covers both `brownfield_renovation` (convert in place)
and `brownfield_newbuild` (rebuild on the same site). One ranking table holds both.

**Eligibility** (`asset.py:596`) — the union of two lists, concatenated:
```python
candidates_renovation = [a for a in assets if not a.retrofit]
candidates_rebuild    = [a for a in assets if a.cuf > 0.60 and a.get_age(year) >= 10]
return list(candidates_renovation) + list(candidates_rebuild)
```
A plant meeting both appears twice. Renovation is available once per plant, ever — the flag
is set at `asset.py:174`.

**Annual cap** (`brownfield.py:51`): `floor(0.2 * number_of_assets)`. 36 smelters, 18
refineries. A switch where origin equals destination does not count toward it
(`brownfield.py:175`).

**The loop** (`brownfield.py:59`):
```python
while (candidates != []) & (n_assets_transitioned <= maximum_n_assets_transitioned):
```
There is no trigger. The model switches every year until one of three exits:

| Exit | Line | Meaning |
|---|---|---|
| Ranking table empty | 66-67 | No switches left to try |
| Emissions under budget | 82-86 | Stops early |
| Loop condition fails | 59 | Hit the 20% cap or ran out of plants |

Only the third exit reaches the summary log line at 190, which is how the three can be told
apart in the logs.

**Constraint handling** (`brownfield.py:137-188`): the switch is applied to a deep copy of the
stack, constraints are checked, and then either committed or rejected. Rejection differs by
constraint — a failed emissions check deletes **that one switch**, a failed build rate check
deletes **every switch into that destination technology**.

**PPA gate** (`brownfield.py:91`): if the destination name contains `PPA`, only plants with
`ppa_allowed` are eligible. No refinery technology contains `PPA`, so this never fires in the
refinery run. All 94 refineries have the flag set true anyway.

---

## 7. Greenfield — building new plants

`aluminium/solver/greenfield.py:34`. Two passes.

**Pass one, regional floors** (lines 64-106). For each region producing less than its required
share of its own demand, build until the shortfall is covered. Shares are hardcoded at
`config_aluminium.py:43`: 0.30 for the six Chinese sub-regions, 0.75 for the other ten. No
source is given for either figure.

**Pass two, global gap** (lines 108-141): `while demand > production:` build the top-ranked
plant.

Every new plant is 1 Mt of annual capacity at 0.95 utilisation
(`ASSUMED_ANNUAL_PRODUCTION_CAPACITY`, `config_aluminium.py:99`), regardless of what real
plants look like. The refinery fleet averages 1.7 Mt per plant.

**Hydro** is stripped from the greenfield ranking at `greenfield.py:53`, so no new hydro-powered
plant is ever built.

---

## 8. The ranking

`mppshared/solver/ranking.py:37`, called from `aluminium/solver/ranking.py:29`.

Cost metric is `tco` (`RANKING_COST_METRIC`, `config_aluminium.py:114`).

**Two different formulas, selected by pathway name.**

Non-`lc` pathways (line 116):
```python
score = emissions_delta_normalized * ranking_config["emissions"] + cost_normalized * ranking_config["cost"]
rank  = score.rank(ascending=False)     # rank 1 = highest score
```

The `lc` pathway (line 94):
```python
tco_adjusted_by_emissions = tco / sum_emissions_delta
score = normalized(tco_adjusted_by_emissions)
rank  = score.rank(ascending=True)      # rank 1 = lowest score
```

**`RANKING_CONFIG` is not used at all in the 1.5C pathway.** `lc_weight_cost` and
`lc_weight_emissions` at `config_aluminium.py:144-145` are dead values.

**The substitution at line 81** is the most consequential line in the ranking:
```python
df["sum_emissions_delta"].apply(lambda x: x if x > 0 else (0.01 if x == 0 else 0.000001))
```
Greenfield switches have origin `New-build`, which has no emissions record, so the origin is
filled with zero and every greenfield emission difference is zero or negative. Zero becomes
0.01, negative becomes 0.000001. The result: **every zero-emission technology scores about
10,000 times better than anything that emits, and among emitting technologies only cost
decides the order.**

Verified in the refinery data for 2030: gas refining is the cheapest option on the table at
$210 per tonne and ranks 65th, while a mechanical vapour recompression route at 0.016 tonnes
of CO2 per tonne ranks 197th, below coal at 0.784, purely because coal is cheaper.

Non-`lc` scores are binned into 50 histogram buckets first, so near-equal switches tie
deliberately and are then broken at random. The `lc` branch is not binned.

**Ties** are broken by `.sample(n=1)` at `agent_logic_functions.py:35`, unseeded.

**The ranking is sliced by year and rebuilt fresh each year** (`simulation_pathway.py:135`,
`get_ranking` at line 375). Deletions made during one year do not carry into the next.

---

## 9. What is filtered out before ranking

`aluminium/solver/implicit_forcing.py:32`, in order.

1. **Availability** (`mppshared/solver/implicit_forcing.py:246`) — removes switches that
   downgrade classification (transition to initial, end-state to initial, end-state to
   transition), and removes any switch in a year before the destination's `expected_maturity`.
   Only 5 of 25 smelting technologies and 8 of 31 refining technologies exist in 2020.
2. **Hydro** (line 51) — switching into hydro is only allowed from hydro.
3. **Moratorium** (line 367), applied to `lc` and `cc` only — from `TECHNOLOGY_MORATORIUM`
   (2030) no new build or renovation into an `initial` technology; from 2030 plus
   `TRANSITIONAL_PERIOD_YEARS` (10), so 2040, none into a `transition` technology either.
   Decommission is exempt.
4. **Emission differences** computed (line 459).
5. **Classification, lifetime and cost of capital** attached (line 520).

---

## 10. Constraints

Seven exist in `mppshared/models/constraints.py:50`. Aluminium uses two
(`config_aluminium.py:207`):

```python
"bau": [],
"cc":  ["rampup_constraint"],
"lc":  ["emissions_constraint", "rampup_constraint"],
"fa":  ["emissions_constraint", "rampup_constraint"],
```

**Business as usual runs with no constraints at all.**

| Constraint | Implemented | Used |
|---|---|---|
| emissions | `constraints.py:210` | yes, `lc` and `fa` |
| build rate | `constraints.py:99` | yes, `lc`, `fa`, `cc` |
| regional production | `constraints.py:157` | no, and explicitly excluded from the pass test at `brownfield.py:153` and `greenfield.py:151` |
| CO2 storage | `constraints.py:453` | no |
| biomass | `constraints.py:612` | no |
| demand share | `constraints.py:284` | no |
| electrolysis capacity | `constraints.py:331` | no, ammonia only |

**The CO2 storage limit cannot work even if switched on.** It reads
`co2_scope1_captured` (`asset.py:calculate_co2_captured_stack`), and that column is empty in
all 11,835 smelter rows and all 12,524 refinery rows. Capture is instead netted into scope 1:
coal smelting in northern China in 2030 is 16.5 tonnes per tonne, the same plant with capture
is 3.5. The 13 tonnes captured are removed from the number and recorded nowhere.

**The biomass limit cannot work either.** Biomass is not among the tracked energy carriers —
`inputs_outputs.csv` holds only coal, gas, oil, hydrogen and electricity. `Bio-Boiler +
Oil-Calciner` exists as a buildable end-state refinery technology with nothing limiting it.

---

## 11. Build rate limit

`mppshared/models/technology_rampup.py`, checked at `constraints.py:99`.

Parameters (`config_aluminium.py:217`): 10 plants in the first year, growing 25% a year, over
a 5-year window. MPP's own commented alternative is 6 plants, 50%, 8 years.

Built at `agent_logic_functions.py:338`. Two facts that matter:

**It only applies to `transition` and `end-state` technologies** (line 372). Coal and gas have
no build limit at all.

**It only exists inside the ramp-up window.** The curve runs from the technology's
`expected_maturity` to maturity plus 5 years. Outside that window `maximum_asset_additions` is
`NaN` (`technology_rampup.py:98`), and `constraints.py:146` treats `NaN` as passing:
```python
df_rampup["check"] = (proposed <= maximum) | (maximum.isna())
```
So from six years after maturity onward, a technology has **no build limit whatsoever**.

---

## 12. The carbon budget — how it actually behaves

`mppshared/models/carbon_budget.py`. `CARBON_BUDGET_SECTOR_CSV = True`
(`config_aluminium.py:133`), so `create_emissions_pathway` reads `carbon_budget.csv` and the
`SECTORAL_CARBON_PATHWAY` block in config is **never used**.

The file is two columns, year and annual limit in gigatonnes, 2018 to 2050. Global, no region.

| | 2020 | 2050 | Cumulative 2020-2050 |
|---|---|---|---|
| Smelting | 0.784 | 0.018 | 10.2 Gt |
| Refining | 0.103 | 0.008 | 1.8 Gt |

`mppshared/config.py` also sets `SECTORAL_CARBON_BUDGETS = {"aluminium": 11}`, but that is
only read when the CSV route is off, which it is not.

**The budget is not a target the model reaches. Neither run stays inside it.**

Measured from the 1.5C run outputs:

| Year | Smelting limit / actual | Refining limit / actual |
|---|---|---|
| 2030 | 586 / 595 Mt | 84 / 89 Mt |
| 2040 | 75 / 186 Mt | 39 / 45 Mt |
| 2050 | 18 / 107 Mt | 8 / 26 Mt |

**Why it is checked and still missed. Three reasons, all verified.**

**First, the two checks use different years.** Brownfield compares against **next** year's
limit (`brownfield.py:36-39`); greenfield compares against **this** year's
(`constraints.py:238`). Both can pass in the same year while the year-end stack fails.

**Second, both round to two decimal places in gigatonnes.**
```python
if np.round(co2_scope1_2, 2) <= np.round(emissions_limit, 2):    # brownfield.py:82
```
That is a tolerance of ±5 MtCO2. Refining's entire 2050 limit is 8.1 Mt, so the tolerance is
62% of the limit. The 2030 log line reads `Emissions lower than budget: 0.5 <= 0.5`.

**Third, greenfield runs last and undoes it.** Brownfield stops switching once the stack is
under the limit, then greenfield builds new plants to meet demand and pushes emissions back
up. Nothing rechecks afterwards. Traced in the 2030 log: decommission removes one plant,
brownfield exits on `0.5 <= 0.5` having switched nothing, greenfield then builds a new gas
smelter in Russia.

---

## 13. What actually stops the transition, per year

Read from the run logs by classifying which brownfield exit was taken.

**Smelting**

| Years | Exit taken |
|---|---|
| 2020-2033 | Under budget, stopped early |
| 2034 | Hit the 20% cap, 37 of 36 |
| 2035-2050 | Ranking table emptied |

**Refining**

| Years | Exit taken |
|---|---|
| 2020-2024 | Zero switches; plants eligible but no ranked switch matched one |
| 2025-2040 | Under budget, stopped early |
| 2041, 2044 | Hit the 20% cap, 18 of 17 |
| 2042, 2045-2050 | Ranking table emptied |

From 2035 smelting has no available switches at all and sits at 107 MtCO2 against a limit of
18. It is not choosing to stop.

**UNVERIFIED:** exactly why the table empties. The inner loop at `brownfield.py:64-118`
deletes a switch whenever no plant matches its origin technology and region, so a fleet that
has already moved to end-state technologies would burn through the table finding no matches.
That is consistent with the counts but I have not instrumented it.

---

## 14. Costs

`technology_transitions.csv` holds four finished cost columns per switch: `tco`, `lcox`,
`switch_capex`, `salvage_value`. **None of them are computed anywhere in this repository.**
They arrive precomputed from MPP's own preprocessing, which is not public.

`tco` is 10.4 to 10.7 times `lcox` on every row. The sum of discount factors over the
technology lifetime at 9% cost of capital is 10.13 for 20 years and 10.82 for 25. So `tco`
behaves as the discounted sum of per-tonne costs over the plant's life, expressed per tonne of
annual capacity. `lcox` is the per-tonne annual figure, $210 to $317 per tonne of alumina in
2030.

Note the consequence: two technologies with different lifetimes are multiplied by different
factors, so a 25-year plant carries a 7% cost penalty against a 20-year plant for reasons
unrelated to its economics.

**Energy prices do not exist in the model.** `inputs_outputs.csv` gives physical consumption
per tonne for five carriers, capital cost and operating cost, but no prices. Verified: the
refinery `inputs_outputs.csv` is byte-identical between the business-as-usual and 1.5C
folders across all 90,768 rows, while the finished costs differ in 57,132 of 57,164 rows. The
entire scenario difference is in prices we cannot see.

`salvage_value` is populated for smelting and empty for refining.

---

## 15. Emissions

`emissions.csv` holds `co2_scope1` and `co2_scope2` per technology, region and year.

**Scope 1 is identical between business-as-usual and 1.5C** in every row. Combustion chemistry
does not change with scenario.

**Scope 2 differs**, because the grid decarbonises at different rates.

**Scope 2 is a smelting input only.** In smelting it reaches 11.5 tonnes per tonne against a
scope 1 average of 4.19, and applies to six grid-connected technologies. In refining it is
nonzero in 26 of 12,524 rows and never exceeds 0.024.

**Three columns are empty in both runs:** `co2_scope1_captured`, `co2_scope3_upstream`,
`co2_scope3_downstream`. Also empty: `current_trl` and `capacity_factor` in
`technology_characteristics.csv`.

Output emissions (`aluminium/solver/output_processing.py:57`) are the emission factor times
annual production volume, summed by product, region and technology. Same formula as the
in-model check at `asset.py:calculate_emissions_stack`.

---

## 16. Settings that do nothing

**`APPLY_CARBON_COST = False`** (`config_aluminium.py:35`) is defined and read nowhere in the
repository. There is no carbon price input file for aluminium. The shared implementation
exists at `mppshared/solver/implicit_forcing.py:98` and ammonia has its own working copy at
`ammonia/solver/implicit_forcing.py:200`, but the aluminium chain never calls either.

**`SWITCH_TYPES_UPDATE_YEAR_COMMISSIONED = ["brownfield_rebuild"]`**
(`config_aluminium.py:130`) names a switch type the model never produces. It emits
`brownfield_newbuild` and `brownfield_renovation` (`asset.py:176-179`). So build year is never
reset.

**`YEAR_2050_EMISSIONS_CONSTRAINT = 2051`** (`config_aluminium.py:214`). Read at
`constraints.py:224`: from that year, new build is tested against the 2050 limit using an
end-state-only stack. Set to 2051, it never fires inside the model horizon.

**`RANKING_CONFIG`** is bypassed in the 1.5C pathway. See section 8.

**`MAP_LOW_COST_POWER_REGIONS["aluminium"] = None`** (`mppshared/config.py`), so
`get_region_rank_filter` always returns the single region.

---

## 17. Randomness

Four unseeded sites:

| Location | What it decides |
|---|---|
| `agent_logic_functions.py:35` | which of several tied top-ranked switches is taken |
| `brownfield.py:121` | which eligible plant takes the switch |
| `decommission.py:73` | which eligible plant closes |
| `decommission.py:130` | same, cement path |

Plant selection is arbitrary. Once eligibility is passed, a modern low-cost plant and an old
expensive one of the same technology in the same region have identical chances.

Noise floor from repeat runs is about 2 Mt at technology level. Accepted, Parker, 2026-08-24.

---

## 18. Is it a bottom-up model

Bottom-up in its accounting: real plants with real capacities, countries, coordinates and
build years; age and utilisation gate eligibility; outputs are per plant; caps are counted in
plants.

Top-down in its decisions: the decision unit is technology by region by year. Costs and
emissions are regional averages, so every plant of a given technology in a given region is
identical to the model. Plant-level detail enters the starting conditions and the eligibility
filter, then is discarded at the moment of choosing.

---

## 19. Run validation

Business-as-usual smelting against MPP's published business-as-usual:

| Year | Our run | Published | Difference |
|---|---|---|---|
| 2020 | 65.42 | 65.42 | 0.00% |
| 2030 | 65.25 | 65.21 | +0.07% |
| 2040 | 81.36 | 80.80 | +0.70% |
| 2050 | 86.10 | 86.34 | -0.28% |

2020 matching exactly confirms the starting fleet, the region mapping and the harness
independently of anything the solver decides.

The 1.5C mix was long thought unreproducible. It is not: the cause was MPP shipping a switch
table with every capture-power route deleted, and their full table reproduces the published
mix to within 13.1 percentage points across six power source categories. Section 24 has it.

---

## 20. The switch table strands captive generation

**A plant may change its power source only while it still has a carbon anode.** Verified in
all three shipped variants of `technology_transitions.csv`.

| Origin | Power source changes allowed |
|---|---|
| Carbon Anode + Coal | Grid, PPA+Grid, Natural Gas, reactor |
| Carbon Anode + Natural Gas | Grid, PPA+Grid, Coal, reactor |
| Carbon Anode + Grid or PPA+Grid | Coal, Natural Gas, Hydro, reactor, each other |
| Carbon Anode+CCS + Coal or Natural Gas | **none** |
| Inert Anode + Coal or Natural Gas | **none** |

`Inert Anode + Natural Gas` has 496 rows in the shipped file, every one with itself as the
destination. `Inert Anode + Coal` is the same. The other two variants add only
`Inert Anode + Natural Gas+CCS`, so fitting capture to your own gas plant is allowed and
connecting to the grid is not.

**This is a gap, not an assumption.** Anode type and electricity supply are physically
independent. Both technologies are also classified `transition` rather than `end-state`
(`technology_characteristics.csv`), so the model treats them as a stepping stone while no
step onward exists.

**The ranking cannot see it coming.** Switches are compared one step at a time with no view
of what a technology can do next. A gas-powered plant takes the anode conversion because it
ranks best now, and permanently forecloses the power switch.

**Cost:** 7.4 Mt on captive gas and 1.5 Mt on captive coal survive to 2050 with no route out.

**Eligibility is a separate matter and is not the block.** A renovation is allowed once per
plant for any change at all (`asset.py:602`), so converting the anode spends the plant's only
renovation. But rebuild has no once-only limit — any plant at least ten years old may rebuild
every year, and its commissioning year never resets (see section 16). So a second change is
possible, at rebuild cost rather than renovation cost. In the unlocked run, of the 102 plants
on `Inert Anode + Grid` in 2050, 59 arrived by renovation, 41 by rebuild and 21 were new
builds.

---

## 21. Scenario results

Twelve 1.5°C runs plus business as usual, in `scenarios/runs/`. Three things vary: the grid
emissions assumption, whether an inert-anode plant on captive fossil power may change its
power source (our six added switches), and how much carbon capture is available.

**Capture regimes.** `noCCS` is MPP's switch table as shipped, where capture-equipped power is
unreachable, archived. `limitedCCS` is their full table with capture held to the IEA WEO 2024
NZE world rate, choice 34. `CCS` is the full table with no cap.

Combined cumulative against the 11.99 Gt budget:

| Grid / inert anode | noCCS | limitedCCS | CCS |
|---|---|---|---|
| MPP, locked | 13.7 Gt, +14.3% | 13.2 Gt, +10.0% | 12.5 Gt, +3.9% |
| MPP, unlocked | 13.2 Gt, +9.9% | 12.3 Gt, +2.4% | 12.5 Gt, +4.0% |
| SBTi, locked | 13.0 Gt, +8.3% | 12.3 Gt, +2.4% | 12.4 Gt, +3.4% |
| SBTi, unlocked | 12.1 Gt, +1.2% | 12.1 Gt, +1.1% | 12.4 Gt, +3.0% |

2050 capture: zero in every `noCCS` run, 25 to 32 Mt across `limitedCCS`, 290 to 368 Mt across
`CCS`. So the limit binds and holds capture roughly an order of magnitude below the
unconstrained result.

**The limited runs are the ones to use.** They sit between the other two on emissions in every
pairing, carry 4.9 to 6.1% of 2050 production on capture, and leave 0 to 8.4% on unabated
fossil. Nuclear returns at 11 to 20% except in the SBTi unlocked case, which has always been
the knife-edge one.

**`LC_MPPgrid_CCS_AnodeUnlocked` remains the closest to MPP's published 1.5DS**, 13.1
percentage points of total absolute deviation across the six 2050 power source categories
against 21.5 for the next best. Adding our six switches moves the run toward their published
mix, not away from it.

**Refining barely moves**, 2.05 to 2.09 Gt everywhere. No grid exposure and no capture route.

---

## 21b. Two defects that stop any brownfield constraint working

Found 2026-08-26 while trying to make the CO2 storage limit bind. This is the reason every
brownfield constraint in the aluminium model has been ineffective, including the carbon budget.

`aluminium/solver/brownfield.py:124`:

```python
# Update asset tentatively (needs deepcopy to provide changes to original stack)
tentative_stack = deepcopy(new_stack)
tentative_stack.update_asset(asset_to_update=asset_to_update, ...)
```

`asset_to_update` is an object taken from `new_stack`, the live year+1 stack.
`deepcopy(new_stack)` copies the stack, but `asset_to_update` still references the original
object. `update_asset` then does `asset_to_update.technology = new_technology`
(`asset.py:178`), mutating the asset **inside `new_stack`**.

So the switch is applied before any constraint is evaluated. When a constraint fails the code
simply does not call `new_stack.update_asset(...)`, but the change has already happened. The
rejection branch removes the transition from the ranking table and nothing else.

**Ammonia and cement both pass `deepcopy(asset_to_update)`.** Aluminium is the only sector that
does not. It is a one-expression difference, and MPP got it right in the other two.

**Measured effect.** In a limited-capture run, brownfield logs 14 real switches and greenfield
12 builds, none into a capture technology, while the 2050 stack holds 96 plants on
capture-equipped power. The constraint returned False 625 times and the ranking handler fired
99 times, and capture still reached 355 Mt against a 116 Mt limit. With `deepcopy` added,
matching ammonia, the same run captures 21 Mt.

| | 2030 | 2040 | 2050 |
|---|---|---|---|
| As shipped | 40.7 | 384.9 | 355.5 |
| With ammonia's `deepcopy` | 6.7 | 23.9 | 21.4 |
| The limit | 8.1 | 63.2 | 116.2 |

**A second defect, exposed by fixing the first.** With the `deepcopy` in place the emissions
constraint became real for the first time, and it deadlocks the solver.
`check_annual_carbon_budget_constraint` at `constraints.py:251` is an absolute test:

```python
if np.round(co2_scope1_2, 2) <= np.round(limit, 2):
    return True
return False
```

It asks whether the whole stack is under budget after the switch, not whether the switch
reduces emissions. While the stack is above budget, which it is for most of the run, it
rejects every candidate including the ones that cut emissions. Measured: 8,608 emissions
rejections against 1,187 storage rejections, and zero real brownfield switches in the run.

**Ammonia omits it.** Their `CONSTRAINTS_TO_APPLY["lc"]` is `["co2_storage_constraint",
"electrolysis_capacity_addition_constraint", "demand_share_constraint"]`, with no
`emissions_constraint` at all. So each sector is internally consistent: ammonia enforces its
constraints properly and does not list this one; aluminium lists it and enforces nothing. The
two only conflict once you mix them.

Our four `limitedCCS` copies exclude `emissions_constraint` from the brownfield pass test the
same way `regional_constraint` already is. The budget still drives the transition through the
separate early exit at `brownfield.py:82`, which reads `pathway.carbon_budget` directly and
does not consult `CONSTRAINTS_TO_APPLY`.

**What this changes elsewhere.** Section 12 gives three reasons the carbon budget is missed.
This is a fourth and more fundamental one: the emissions constraint is checked on a stack that
already contains the switch, and rejecting it does not undo it. Any earlier conclusion about a
brownfield constraint not binding should be re-read in this light, including the capture cap
attempted through `demand_share_constraint` and abandoned.

Applied in the four `limitedCCS` model copies only. `model_clean` is left as shipped.

---

## 22. Where the scenario work lives

```
scenarios/
  run.py                  python run.py <scenario> <pathway> <plant> [model_dir]
  common.py               loaders, the twelve-run registry, colours, figure helpers
  patch_fulltt.py         swaps MPP's full 132-pair switch table in, adds our six switches
  patch_grid.py           swaps in the SBTi power pathway grid intensity
  patch_ccs_limit.py      the six changes the capture limit needs
  make_figures.py         the five deck figures, png and svg
  build_deck.py           builds the results deck on the SBTi template
  models/                 one working copy of MPP's model per scenario, gitignored
  runs/                   one folder per scenario: final/, stack_tracker/, ranking/, inputs_used/
  notebooks/
    analysis/             tables only
      01_scenario_summary.ipynb
      02_switch_table_evidence.ipynb
    plots/                figures only, all twelve runs
      01_smelting_emissions.ipynb        3 by 4 matrix, annual and cumulative
      02_electricity_generation_mix.ipynb  3 by 4 matrix, self contained
      03_emissions_intensity.ipynb       3 by 4 matrix, process against electricity
      04_alumina_refining.ipynb          one axes, refining is identical across the twelve
      05_carbon_budget_outcome.ipynb     twelve compared, lines and bars, self contained
  figures/                rendered png and svg
```

Analysis and plotting are deliberately separate. Both import from `common.py`, so neither
carries its own loaders. `RUNS_INDEX` in `common.py` holds all twelve runs with their capture
regime, grid, inert anode setting and folder; `SCENARIOS` is the headline set, business as
usual plus the four `limitedCCS` runs.

Analysis and plotting are deliberately separate. The analysis notebooks produce tables and
nothing else; the plotting notebooks produce figures and nothing else. Both import from
`common.py`, so neither carries its own loaders.

Every run saves the inputs that produced it under `inputs_used/`, so results stay traceable.

---

## 23. File provenance: what is MPP's and what is ours

Written 2026-08-26 to settle a question that kept being re-derived. Checked with
`git ls-files`, `git log` and md5 against `mpp-upstream-reference`, which is a read-only
clone of `missionpossiblepartnership/mpp-shared-code` at `b09472f` on `origin/develop`.

**MPP ships three switch tables in the 1.5C smelter folder.** All three are tracked in MPP's
own repository, committed by Luis Natera of Systemiq on 20 September 2022 in `6593573`
"Upload aluminium data". None of them is ours.

| File in `lc/def/intermediate/` | Switch pairs | Contents |
|---|---|---|
| `technology_transitions_original.csv` | 132 | the full table |
| `technology_transitions_noGridtoCCS.csv` | 120 | full table minus the 12 grid-to-captive-capture routes |
| `technology_transitions.csv` (live) | 92 | full table minus all 40 captive-power-capture routes |

`technology_transitions.csv` is the only name the code reads
(`mppshared/import_data/intermediate_data.py:240`). The other two are inert unless renamed,
so the 92-switch version is what every 1.5C run loads. The BAU folder ships the full 132.

Each is a strict subset of the one above it. Nothing appears in the live file that is absent
from `_original`.

**What is ours:**

| Item | Ours or MPP's |
|---|---|
| The six `Inert Anode + <captive fossil>` power-source switches | ours, `scenarios/patch_fulltt.py`. Absent from all three MPP tables |
| Rescaled scope 2 emissions | ours, `scenarios/patch_grid.py` |
| `mpp-bau/lc_final_noGridtoCCS/`, `mpp-bau/lc_final_ORIGINAL_TT/` | ours, run outputs, named after the MPP input file each used |
| `_archive/Aluminium_tt_restricted_backup.csv` | MPP's. A copy of the live 92-switch file under a name that reads like our doing. Archived 2026-08-26 |
| `_archive/OLD_RUN_*`, `_archive/RUN_*` | ours, superseded runs |
| `mpp-shared-code/` | MPP's, with uncommitted local edits. Nothing live depends on it |

Anything in `_archive/` is history. Do not read it as a live input.

---

## 24. Which switch table we use, and why capture stays open

Decided 2026-08-26, after establishing that the shipped 92-pair table made capture-equipped
power arithmetically unreachable. Section 23 has the provenance of the three files.

**We use MPP's full `technology_transitions_original.csv`, 132 switch pairs.** It is MPP's own
file and a strict superset of the shipped one, so nothing is added beyond the 40
captive-power-capture routes. The 92-pair table is superseded. Its four runs and their model
copies are in `_archive/scenarios_92switches/` and `_archive/models_92switches/`. Do not cite
them; the zero CCS in those runs is an artefact of the input file, not a result.

**Capture on captive power is a valid decarbonisation route. It needs a limit, not a
prohibition.** No limit exists for aluminium today. `check_co2_storage_constraint` is
implemented at `constraints.py:453`, is absent from `CONSTRAINTS_TO_APPLY`, and has no
`co2_storage_constraint.csv` in either data folder. Regional CO2 storage capacity is in the
IIASA request for that reason. Until it arrives, capture in these runs is unlimited and the
share should be read as an upper bound.

**Grid to captive fossil stays open, both with and without capture.** Deliberate, and not
because it is realistic.

On the 132-pair table the unabated reversals fire in none of the four runs. That is worth
reporting as a result: given the choice, the cost ranking prefers captive fossil *with*
capture over unabated captive fossil, so the unabated routes need no prohibition to stay
empty. Banning them would replace a finding with an assumption.

The abated reversals do fire, and only where the grid is dirty. On MPP's grid assumption 11
plants and 4.68 Mt of capacity move from `Carbon Anode + Grid` to
`Inert Anode + Natural Gas+CCS` between 2035 and 2037 and remain there in 2050, 6.9% of
production, nine of them in China. On the SBTi power pathway they do not fire at all. That
contrast is the cleanest evidence we have that the reversal tracks the grid emissions factor
rather than anything physical, and deleting the routes would erase it.

Note that MPP's own `technology_transitions_noGridtoCCS.csv` takes the opposite position. It
removes the twelve grid-to-captive-capture routes and leaves all twelve grid-to-unabated
routes in place, so it closes the better move and keeps the worse one. All three of their
files carry the twelve unabated routes unchanged.

**The four live runs, 2050 smelter power source share of production, against MPP published:**

| | Fossil | Fossil + capture | Grid | PPA | Hydro | Nuclear |
|---|---|---|---|---|---|---|
| MPP published 1.5DS | 0.0 | 48.3 | 9.2 | 9.4 | 10.0 | 23.2 |
| MPP grid, plus our six | 0.0 | 53.4 | 9.6 | 7.4 | 11.0 | 18.6 |
| MPP grid | 0.0 | 58.1 | 8.0 | 3.3 | 10.9 | 19.7 |
| SBTi grid, plus our six | 0.0 | 40.5 | 43.2 | 5.1 | 10.2 | 1.0 |
| SBTi grid | 0.0 | 44.6 | 38.7 | 4.2 | 10.8 | 1.7 |

MPP grid plus our six is the closest to published, 13.1 percentage points of total absolute
deviation against 21.5 for the next best. Adding our six switches moves the run toward MPP's
published mix, not away from it.

Cumulative combined emissions against the 11.99 Gt budget, both plants solved on the same
model copy: +4.0% (MPP grid plus our six), +3.9% (MPP grid), +3.0% (SBTi grid plus our six),
+3.4% (SBTi grid). The full table narrows the spread from +1.2% to +14.3% down to under one
point. Refining was first reused from the matching 92-pair runs and later re-solved; the two
agree to within 0.03 Gt, which is solver noise.
