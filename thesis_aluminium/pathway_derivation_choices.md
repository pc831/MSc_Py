# Aluminium pathway — methodological choices

Running record of every normative choice that affects the pathway numbers.
Source material for the pathway derivation technical report.

**Maintenance rule:** add an entry whenever a choice is made that could have been
made differently and would change a published number. Record the alternative that
was rejected. Do not record mechanical implementation detail that has only one
defensible answer.

Last updated: 2026-08-26

---

## CURRENT BASIS — read this first

**We are not reproducing MPP's 1.5°C scenario. We are using their model to build SBTi's own.**
Runs live in `scenarios/runs/`, the model copies in `scenarios/models/`, and
`MODEL_REFERENCE.md` is the verified account of how the model behaves.

Three things vary across the twelve 1.5°C runs: the grid emissions assumption (MPP's or the
SBTi power pathway), whether an inert-anode plant on captive fossil power may change its power
source (our six added switches), and how much carbon capture is available.

Regions are **China and Rest of the World** for the published pathway, because that is all MPP
publishes. The model itself runs on 16 regions and the outputs support that granularity, with
country level available for the 74% of 2050 capacity that exists in 2020. What blocks finer
reporting is not data but solver determinism: see choice 31.

**Live choices:** 1 (scenario), 10 (anode constants), 11 (refinery all process), 13 (alumina
ratio), 14 (denominators), 15 (deliverable metric), 20 to 28 (the milestone pathway), 30 and 31
(local modifications; solver stochasticity), and 32 to 34 (switch table, grid reversals, the
capture limit).

**Inactive choices** are in `_archive/pathway_derivation_choices_inactive.md`: 2 to 9 and 12
belong to the abandoned asset-level derivation, and 16 to 19 to model re-run questions since
answered.

**Not yet logged:** the key-assumptions table (`build_assumption_table.py`) makes normative
calls that need a choice 29 — the six indicator definitions, the 2020–2030 and 2030–2050
period windows, dropping the secondary aluminium row, and rounding to the nearest 1%.

**Workbooks:** `build_pathway_workbook.py` and `build_milestone_workbook.py` rebuild
`Aluminium Emissions Pathway.xlsx` and `Aluminium Milestone Pathway.xlsx` in
`~/Desktop/Aluminium Pathway Derivation/`. Both are formula-driven; only raw source tables are
values.

---

## 1. Scenario source

**Choice.** MPP 1.5DS, taken from the open-source MPP model rather than the published
summary workbook.

`lc` is MPP's internal name for the scenario published externally as 1.5DS.
Full sector coverage requires **two independent model runs**:

- `def` — smelters, `PRODUCTS=["Aluminium"]`
- `def_refineries` — alumina refineries, `PRODUCTS=["Alumina"]`

Alumina refining is modelled separately; its output feeds smelter operation as an
exogenous input.

**Why not the published workbook.** `mpp_aluminium_net_zero_outputs.xlsx` is global
only. Any regional split requires running the model.

**Status.** Settled.

---

## 10. Splitting scope 1 into process and captive power

**Choice.** Captive power emissions are separated from process emissions using the
anode archetype constants, with captive power taken as the residual:

```
captive power factor = max(0, co2_scope1 − archetype constant)
```

Archetype constants, MPP Aluminium Technical Appendix Exhibit TA3.3 (p. 11):

| Anode archetype | tCO₂e/tAl |
|---|---|
| Carbon Anode (Hall-Héroult) | 2.13 |
| Carbon Anode + CCS | 1.17 |
| Inert Anode | 0.10 |

**Why a residual is needed.** MPP places captive fossil power generation inside
Scope 1, so `co2_scope1` for e.g. `Carbon Anode + Coal` is 16–19 tCO₂/t — mostly
power, not process. There is no separate captive-power column to read.

**Note on units.** MPP's `co2_scope1` is **CO₂e**, not CO₂: it bundles anode process
CO₂, PFCs, and anode thermal emissions. Verified against Exhibit TA3.3.

**Status.** Settled. The residual approach is an inference, not a reported quantity —
flag in the technical report.

---

## 11. Refinery emissions are all process

**Choice.** No archetype split is applied to refineries. All refinery Scope 1 counts
as process emissions.

**Why.** Refinery technologies are boiler + calciner combinations
(`Coal-Boiler + Oil-Calciner`, `MVR-Fossil-Boiler + Gas-Calciner`, …). There is no
anode, and the emissions are thermal fuel for digestion and calcination — process
heat, not power generation.

**Status.** Settled.

---

## 13. Alumina-to-aluminium ratio

**Value.** 1.935 t alumina per t aluminium.

**Not a choice.** Taken from `inputs_outputs.csv`, parameter `Alumina Consumption`,
unit t/t. Verified as a single global constant — zero variation across all 12,400
region × technology × year rows. Recorded here only so the technical report can cite
its provenance rather than presenting it as an assumption.

---

## 14. Intensity denominators

**Choice.**

- Smelter process and electricity intensities divide by **smelter production (Mt Al)**.
- Refinery intensity is computed per tonne **alumina**, then converted to a per-tonne-
  aluminium basis by multiplying by 1.935.

```
process intensity = smelter process / Mt Al  +  (refinery process / Mt alumina) × 1.935
total intensity   = process intensity  +  (captive power + grid power) / Mt Al
```

**Status.** Settled.

---

## 15. Deliverable metric

**Choice.** Intensity, tCO₂e per tonne aluminium, is the pathway. Absolute emissions
are an intermediate step, not the published output.

**The pathway is process emissions ONLY. All electricity is excluded — both Scope 2
imported power and captive fossil combustion.** Confirmed by Parker, 2026-07-28.

In scope: smelter anode process CO₂ + PFCs + anode thermal (the archetype constants of
choice 10), plus refinery digestion and calcination fuel.

Out of scope: Scope 2 imported electricity, and captive fossil power generation — even
though MPP reports captive power inside `co2_scope1`, which is why the residual split in
choice 10 is required to remove it.

**Captive and grid power columns are retained as diagnostics only.** They are not part
of the published pathway. For reference, captive power would have added 0.18 (AE), 5.34
(EMDE) and 9.96 (China) tCO₂e/tAl in 2020 — i.e. including it would change the pathway
completely and would make the AE series rise 33% to 2030 rather than decline. Do not
reintroduce it without an explicit decision.

**Publication interval.** 5-year intervals only, so small year-on-year upticks in the
annual series do not survive the sampling and need no smoothing. Confirmed by Parker,
2026-07-28.

> ### ⚠️ SUPERSEDED — DO NOT USE THESE NUMBERS
>
> | Year | AE | EMDE | China | Global |
> |---|---|---|---|---|
> | 2020 | 3.604 | 3.760 | 3.911 | 3.810 |
> | 2030 | 3.043 | 3.047 | 3.850 | 3.476 |
> | 2040 | 1.412 | 0.899 | 0.657 | 0.877 |
> | 2050 | 1.315 | 0.638 | 0.345 | 0.657 |
>
> Derived from a misconfigured model run — see choice 16. That run read the BAU demand
> series instead of the 1.5°C series and overproduced aluminium by 31% by 2050, diluting
> the anode mix and distorting every regional intensity. **2020 is approximately correct**
> (it is the initial asset stack, unaffected by the demand bug); every later year is not.
>
> Retained only so the error is documented. Corrected values replace this block once the
> re-run is validated per choice 18.

---

## 20. Collapsing refinery emission factors to China / Rest of the World

**Choice.** Refinery emission factors come from the repo input
`def_refineries/intermediate/emissions.csv`, which is resolved by MPP model region. They are
collapsed to China / RoW as an average weighted by **2020 refinery capacity share** from
`initial_asset_stack.csv`.

**China is exact.** Its sub-regions have identical `co2_scope1` for every technology-year —
verified zero spread across all 775 China technology-years — so weighting is irrelevant
there.

**RoW is an approximation.** Factors vary across the ~10 non-China MPP regions within a
technology-year (mean spread 0.169, max 0.515 tCO₂e/t alumina), and published data does not
resolve production below RoW, so exact weights are unobtainable.

**Sensitivity, expressed per tonne of aluminium:**

| Year | Capacity-weighted | Equal-weighted | Difference |
|---|---|---|---|
| 2020 | 1.555 | 1.657 | 0.102 |
| 2040 | 0.484 | 0.516 | 0.032 |
| 2050 | 0.092 | 0.097 | 0.005 |

Around 2.7% of 2020 process intensity, falling to negligible. Acceptable, but disclose it.

**Alternative rejected.** Weighting by our own refinery run's regional production — rejected
because that run is exactly what choice 19 established cannot be validated.

---

## 21. Definition of the Global row

**Choice.** Global process intensity is computed with the same formula shape as each region:
global smelter process emissions ÷ global Mt Al, plus (global refinery process emissions ÷
global Mt alumina) × 1.935.

**Alternative rejected.** Production-weighting the China and RoW intensities. That gives a
slightly different answer (3.818 vs 3.810 in 2020; 0.319 vs 0.328 in 2050) because global
alumina output is not exactly 1.935 × global aluminium output. The chosen definition is
internally consistent with the regional rows, which matters more than matching a weighted
average of them.

---

## 22. The pathway as derived

Process intensity, tCO₂e per tonne aluminium. **These are the current live numbers.**

| Year | China | RoW | Global |
|---|---|---|---|
| 2020 | 3.911 | 3.684 | 3.810 |
| 2025 | 3.911 | 3.702 | 3.819 |
| 2030 | 3.843 | 2.734 | 3.373 |
| 2035 | 2.226 | 1.423 | 1.835 |
| 2040 | 1.028 | 1.145 | 1.084 |
| 2045 | 0.534 | 0.367 | 0.451 |
| 2050 | 0.434 | 0.217 | 0.328 |

Reduction vs 2020 by 2050: **China 88.9%, RoW 94.1%, Global 91.4%.**

Absolute process emissions 2020: 249.5 Mt CO₂e (China 146.8, RoW 102.7).

**Shape notes, for the technical report:**
- Both regions are flat to 2025. China is still only 1.7% below 2020 at 2030; RoW is 25.8%
  below. The steep decline is 2030–2045 as inert anode deployment lands.
- **China ends above RoW** (0.434 vs 0.217), driven mainly by refining: China finishes at
  0.306 tCO₂e/tAl of refining against RoW's 0.092.
- Per choice 15 the raw MPP shape is published as-is. It is not reshaped to be monotonic or
  smooth.

---

## 23. Deriving milestone years from published production data

**Choice.** Both milestone years are read off MPP's published production series, per
technology per region. No asset-level data is needed.

- **Phase-out year** — the first year production is zero and remains zero thereafter.
- **No new capacity year** — the year after the last year production exceeded its own prior
  running maximum.

**Why the second one is valid.** MPP caps capacity utilisation at `CUF_UPPER_THRESHOLD = 0.95`
in `config_aluminium.py`. Production above a technology's previous peak therefore cannot come
from utilisation alone and requires added capacity.

**Read-off, unabated fossil-powered smelting:**

| Region | Power | Mt 2020 | No new capacity | Phase-out |
|---|---|---|---|---|
| China | Coal | 26.63 | 2021 | 2034 |
| RoW | Coal | 3.63 | 2022 | 2024 |
| RoW | Natural Gas | 5.75 | 2033 | 2035 |
| RoW | Natural Gas (inert anode) | 0.00 | 2034 | 2043 |

Unabated carbon anode, any power source: China last addition 2038, phased out 2042; RoW last
addition 2032, phased out 2043.

**Limitation — disclose in the specification.** The test detects *net* capacity growth, so it
is a **lower bound on gross new build**. If capacity were added in a year while more capacity
retired, production would not exceed the prior peak and the addition would be invisible. The
local model run suggested this does happen for Chinese coal — it showed 8 greenfield
`Carbon Anode + Coal` plants while published China coal production declines monotonically.
The milestone years are therefore derived from net capacity trajectories, which is the
strongest claim published data supports.

**Correction to an earlier finding.** The claim that MPP 1.5DS builds new coal-powered
smelting through 2035 came from `plant_stack_transition` in the local run and is **not present
in published data**. Published China `Carbon Anode + Coal` never exceeds its prior maximum,
and RoW coal grows only once, to 4.58 Mt by 2022, before reaching zero in 2024. The earlier
open item warning that a "no new unabated capacity" milestone would contradict the underlying
scenario is withdrawn.

**Resolved.** The definition of "unabated" is now settled — see choice 25. The ambiguity over
`Grid` and `PPA+Grid` is resolved by choice 24: the smelter power source is out of scope
entirely, so no power-source technology attracts a milestone.

---

## 24. The milestone set, and captive power generation out of scope

**Choice.** Seven milestones, cut by process step rather than by MPP technology string, at
China / Rest of the World:

1. No new unabated fossil digester
2. Phase out unabated fossil digester
3. No new unabated fossil calciner
4. Phase out unabated fossil calciner
5. Phase out unabated carbon anode
6. No new unabated fossil auxiliary
7. Phase out unabated fossil auxiliary

**All captive and contracted power generation is excluded.** MPP smelter technology strings are
`<anode> + <power source>`, where the power source is the smelter's captive or purchased
electricity. Under SBTi guidance that generation takes its milestone from the power sector,
from a different source, so the power-source component is never tested here. Anode milestones
are computed on production summed across all power sources.

**Why the process-step cut works.** MPP's compound technology strings already carry every cut
the milestone table needs. `<boiler> + <calciner>` splits the refinery into digestion (69% of
refinery thermal energy) and calcination (31%); the anode prefix splits the smelter. Grouping
by component and summing production across every technology sharing that component gives one
series per process step per region.

**Rejected alternative.** Milestones per full technology string. That produces 15 refinery and
21 smelter rows, most immaterial, and it entangles the smelter power source with the anode —
`Carbon Anode + Small Modular Reactor` would read as a new carbon anode in 2038 when it is in
fact an existing carbon-anode plant switching its power supply.

**Consistency note.** Excluding captive power is consistent with choice 15, which excludes all
electricity from the emissions intensity pathway. Captive power inside `co2_scope1` would have
added roughly 10.0 tCO₂e/tAl in China in 2020 — see choice 10.

---

## 25. What counts as unabated

**Choice.** A technology is **abated** if either limb holds:

- **(a)** it is fitted with CCS at ≥90% capture rate, or
- **(b)** its scope 1 intensity is roughly ≤10% of BAU performance for the same process step.

Everything else is unabated. Both limbs are evaluated against data, not technology names,
because MPP's names mislead in both directions.

**Digester — classified on limb (b).** Gas consumption per tonne alumina from
`inputs_outputs.csv`, benchmarked against the `Gas-Boiler`, which is the lowest-intensity pure
fossil option and therefore the strictest available denominator. Ratios are identical across
all 16 MPP regions.

| Boiler | % of Gas-Boiler | Classification |
|---|---|---|
| `Coal-Boiler` | 181% | unabated |
| `Oil-Boiler` | 129% | unabated |
| `Gas-Boiler` | 100% | unabated |
| `CST-Fossil-Boiler` | 26% | **abated by override — see below** |
| `MVR-Fossil-Boiler` | 5% | **abated** |
| `Elec-Boiler`, `H2-Boiler`, `Bio-Boiler` | 0% | abated |

The two `-Fossil-` boilers are hybrids, not the low-carbon technologies the Technical Appendix
implies. Mechanical vapour recompression runs at 300% efficiency and burns 0.363 of the gas
boiler's 7.260 GJ/t alumina — it passes limb (b) despite having no CCS.

**`CST-Fossil-Boiler` is classified abated by explicit override.** It fails limb (b) at 26%,
retaining a 1.888 GJ/t alumina gas backup against the gas boiler's 7.260. It is nonetheless
treated as abated on the grounds that the residual is a *backup* for periods without sun rather
than a primary process fuel, and is switchable to biogas or hydrogen. Parker's call. The
override is implemented as a visible column on the workbook's `Abatement Test` sheet, not
folded into the rule, so the rule-based result and the published result sit side by side.

**What the override changes.** MPP 1.5DS builds 3.78 Mt of `CST-Fossil-Boiler` capacity in RoW
in 2045 and holds it to 2050. Treating CST as unabated would move the RoW digester milestone
from **2022 / 2045** to **2046 / 2050 (backstop)**, because that late build would register as
new unabated fossil digestion and would never be retired. China is unaffected — it has no CST,
oil or gas boilers, only coal.

**Calciner.** MPP considered CCS retrofits to calciners and rejected them — no known industrial
example, and the capture scale is too small to be viable (Technical Appendix p.10). No abated
fossil calciner exists in the technology set, so `Gas-Calciner` and `Oil-Calciner` are unabated
by construction. `Elec-Calciner` and `H2-Calciner` carry zero direct emissions.

**Anode — `Carbon Anode+CCS` classified as abated on limb (a).** Direct emissions per tonne
aluminium from `emissions.csv`, read on `+ Grid` technologies so captive generation is zero.
Region- and year-invariant.

| Anode | tCO₂e/tAl | % of BAU | Classification |
|---|---|---|---|
| `Carbon Anode` | 2.093 | 100% | unabated |
| `Carbon Anode+CCS` | 1.135 | 54% | **abated on limb (a)** |
| `Inert Anode` | 0.063 | 3% | abated on both limbs |

**Why, and the circle this squares.** `Carbon Anode+CCS` fails limb (b) badly at 54% of BAU,
but MPP specifies it as *"90% capture of smelter process CO₂, not PFCs or anode production
emissions"* (Technical Appendix p.11), so it meets limb (a) on the stream it addresses. The
residual is 1.029 tCO₂e/tAl of PFCs plus anode production emissions, which sit outside the
captured stream and survive. Counting HH+CCS as abated is therefore a decision about the
capture rate, not about residual intensity.

**Consequence to disclose in the specification.** "Phase out unabated carbon anode" does **not**
imply zero smelter process emissions. A pathway that meets it entirely via HH+CCS still emits
roughly 1.03 tCO₂e/tAl. This is consistent with the emissions intensity pathway of choice 22,
which ends at 0.434 (China) and 0.217 (RoW) tCO₂e/tAl in 2050 rather than zero.

**Rejected alternative.** Classifying `Carbon Anode+CCS` as unabated, on the grounds that 54%
of BAU intensity is plainly not abated. Rejected because it makes full decarbonisation
unreachable in the milestone framework — MPP's 1.5DS relies on HH+CCS as an end-state
technology alongside inert anodes, so treating it as unabated would mean no phase-out milestone
could ever be met. The residual is disclosed instead.

---

## 26. Materiality threshold of 1% of 2020

**Choice.** Both tests use a threshold of 1% of the group's 2020 production. Phase-out is the
first year the series falls to or below the threshold and stays there; the capacity test
requires growth to exceed the prior running maximum *by more than* the threshold.

**Why.** Without it, single stranded assets and rounding-scale increments set the milestone.
China's unabated carbon anode falls from 38.48 Mt to 0.13 Mt by 2042 — a 99.7% reduction — and
then one 0.13 Mt smelter, `Carbon Anode + Small Modular Reactor`, holds flat to 2050. On a
strict zero test China would have no anode phase-out year at all, which misrepresents a
scenario that has effectively eliminated the technology.

**Rejected alternative.** A strict zero test. Faithful to the data but produces "beyond 2050"
for a 99.7% reduction, and the residual is a model artefact rather than a real fleet.

---

## 27. The 2050 net-zero backstop

**Choice.** Net zero by 2050 is a hard requirement of the standard, so any milestone with no
year in the source scenario is set to **2050**, and flagged as backstop-derived.

**Why.** Two of the seven milestones do not resolve in the source scenarios. Unabated fossil
calcination runs to 2050 in MPP 1.5DS at 48.71 Mt alumina in China and 11.46 Mt in RoW —
roughly 9 MtCO₂/yr in China alone. Auxiliary intensity only reaches 19.7% of its 2018 level.
The standard's requirement binds regardless.

**Disclose which years are backstop-derived,** because they mark where the pathway departs from
its source scenario rather than reading off it: both calciner phase-outs and both auxiliary
phase-outs. Every other milestone is read off the source data.

**Rejected alternative.** Reporting "beyond 2050" for those four. Faithful but incompatible
with a net-zero-2050 standard, and it would leave the calciner — a real, large, unabated source
— without a phase-out milestone.

---

## 28. Auxiliary milestones from IAI 1.5DS

**Choice.** Auxiliary — remelting, scrap refining, decoating and casting — is derived from the
**IAI 1.5°C scenario**, global, with the same year reported for China and RoW.

**Why IAI.** MPP's aluminium model has two plant types, Refinery and Smelter. Casting,
remelting, recycling and semis are explicitly outside its asset-level boundary and MPP takes
them from the IAI 1.5DS itself (Technical Appendix pp.3–4, 20). Using IAI keeps the auxiliary
milestone consistent with the source MPP defers to.

**Scope.** IAI Table 2 steps `Recycled Aluminium` (collection, decoating, scrap remelting),
`Internal Scrap/Fabrication Scrap` and `Semis Process` (rolling, extrusion, casting furnaces).
Intensity is their combined emissions over `Semis Shipments`, the throughput all auxiliary
processing passes through.

| | 2018 | 2030 | 2035 | 2040 | 2045 | 2050 |
|---|---|---|---|---|---|---|
| tCO₂e/t semis | 0.611 | 0.479 | 0.408 | 0.316 | 0.232 | 0.120 |
| % of 2018 | 100% | 78% | 67% | 52% | 38% | **20%** |

**How the two tests are applied.** IAI has no technology mix and no capacity dimension, so the
production-growth test of choice 23 cannot be used.

- **Phase out** is read against limb (b) of choice 25 directly — the first year intensity falls
  to ≤10% of 2018, at which point the remaining fleet is abated by definition. IAI 1.5DS only
  reaches 20%, so this milestone comes from the 2050 backstop of choice 27.
- **No new** is the phase-out year less the equipment lifetime, since a fossil furnace built in
  year Y still operates in Y + lifetime. 2050 − 25 = **2025**. This is the same logic that
  underpins the Power specification's "no new" milestones.

**Assumptions to confirm before publishing.**

- **25-year equipment lifetime.** IAI publishes no lifetime. 25 years is MPP's own assumption
  for every boiler type (Technical Appendix Exhibit TA3.1), imported here for auxiliary
  furnaces. A 20-year lifetime would give 2030 instead of 2025.
- **Primary casting is not separable.** IAI folds it into `Primary Aluminium` as an unlabelled
  residual — 2018: 1036.6 total less 823.3 electrolysis less 171.5 refining = 41.8 Mt, which
  also carries bauxite mining and anode production. The auxiliary milestone therefore covers
  post-primary casting only.
- **No regional split.** IAI is global. The same year is reported for both regions rather than
  leaving the rows empty — the milestone is real, it just carries no regional detail.

**Rejected alternative.** Moritz et al. 2024 (`s41558-024-02193-x`), whose secondary melting
technology stocks give explicit fossil furnace shares by plant type — Remelter, Refiner,
Foundry — falling from 90% in 2020 to 1.2–2.0% by 2050 across its six scenario variants. That
is a better structural fit, since stock shares support the capacity test directly and need no
lifetime assumption. Rejected for source consistency: MPP defers to IAI, not Moritz, so mixing
Moritz in would put the auxiliary milestone on a different demand and scrap basis from the rest
of the pathway. Moritz is also global only, so it does not solve the regional gap either.

---

## 30. Modifications to MPP's own code, and what is left untouched

Choice 29 is reserved for the key-assumptions table (see CURRENT BASIS).

**Choice.** Exactly one line of MPP's model code is modified, and it is a pandas-compatibility
fix, not a methodological change:

`aluminium/solver/output_processing.py`, in `calculate_weighted_average_lcox`:

```python
df_stack = df_stack.rename(columns={0: "lcox"})
```

**Why.** The preceding aggregation returns a Series whose column is named `0` on current pandas.
The following `.melt(id_vars=agg_vars)` then fails because no `lcox` column exists. Without the
rename the run crashes in output processing. The fix names the column MPP's own downstream code
already expects; it changes no number.

**Alternative rejected.** Pinning an older pandas from `requirements.txt` to match whatever
version MPP developed against. Rejected because the repo pins no exact versions, the required
version is unknown, and a one-line rename is a smaller intervention than an environment
downgrade.

**Full inventory of local modifications**, verified 2026-08-14 by diffing against the pristine
upstream clone at `Aluminium/mpp-upstream-reference` (commit `b09472f`, kept read-only):

| File | Change | Kind |
|---|---|---|
| `main.py` | `SECTOR` cement → aluminium | Required. Upstream ships with `SECTOR = "cement"` |
| `aluminium/config_aluminium.py` | `PRODUCTS`, `SENSITIVITIES`, `TRANSITIONAL_PERIOD_YEARS` | Run selection. No per-run config file exists, so smelter vs refinery can only be chosen by editing this |
| `aluminium/solver/output_processing.py` | the rename above | Compatibility fix |
| `def/intermediate/demand.csv` | replaced with `demand_lc.csv` | Input substitution — choice 16 |
| `def/intermediate/technology_transitions.csv` | replaced with `_original` | Input substitution — choice 17 |
| `def/intermediate/technologies_to_rank.csv` | regenerated | Model *output*, not an input |
| `def_refineries/intermediate/technologies_to_rank.csv` | regenerated | Model *output*, not an input |

**Critically, the three input files the published pathway actually reads are unmodified.**
`emissions.csv`, `inputs_outputs.csv` and `initial_asset_stack.csv`, for both runs, are
byte-identical to upstream. The pathway therefore does not depend on any modified file, and does
not depend on any model run — see CURRENT BASIS.

**The upstream reference clone.** `Aluminium/mpp-upstream-reference` is a pristine clone of the
same commit, held `chmod -R a-w` and guarded by a PreToolUse hook
(`.claude/hooks/block-upstream-reference.sh`) that refuses edits and refuses `chmod`/`rm`
against it while allowing reads. Both directories are gitignored. To re-inventory drift:

```bash
diff -rq mpp-upstream-reference mpp-shared-code | grep -v "^Only in\|\.git"
```

---

## 31. The MPP solver is stochastic and unseeded

**Finding, not a choice.** The solver breaks ties randomly at four unseeded call sites —
`aluminium/solver/brownfield.py:121` and two in `mppshared/agent_logic/decommission.py`
(`random.choice(best_candidates)`), plus `mppshared/agent_logic/agent_logic_functions.py:36`
(`.sample(n=1)`). No seed is set anywhere and no seed parameter exists in the config.

**MPP's own inline comments state the intent** — "If several candidates for best transition,
choose asset for transition randomly" (brownfield), "choose randomly" (decommission), "if same
rank, chosen randomly with sample" (agent logic). It is deliberate tie-breaking, not a bug.
**It is not mentioned in the README, the MPP model documentation PDF, or the Aluminium Technical
Appendix** — all three searched. It is visible only in the source.

**What is deterministic, and what is not.** The distinction matters:

- **Deterministic — the entire preprocessing chain, up to and including the ranking table.**
  Verified by exact reproduction of both of MPP's committed `technologies_to_rank.csv` files
  (refinery 38,630 keys at `TRANSITIONAL_PERIOD_YEARS = 20`; smelter 21,744 keys at the shipped
  10), zero difference either way. Nothing before the simulation loop varies.
- **Stochastic — only tie-breaks inside the simulation loop.** Which of several equally-ranked,
  otherwise-identical assets transitions or is decommissioned, and which of several
  equal-minimum-rank transitions is taken.

**Why the tie-break propagates rather than cancelling.** Assets carry different capacities
(2.19, 4.234, 2.555 Mt among the first three refinery rows), so picking a different tied asset
moves a different volume, changing what capacity remains available in later years.

**Measured by replicate study, 2026-08-14** — 6 runs per config in an isolated copy of the repo
(`scratchpad/replicates.py`, outputs `replicates.csv` and `replicate_mixes_2050.csv`). Refinery
run, 2050:

| Quantity | ty=10 spread | ty=20 spread | Published |
|---|---|---|---|
| Global total, Mt alumina | 130.72 – 132.12 | 129.77 – 131.18 | 131.05 ✅ inside |
| China share of global | 43.0% – 47.8% | 44.4% – 52.1% | 51.3% (**outside** ty=10, inside ty=20) |
| China total | 56.21 – 63.16 | 58.22 – 68.11 | 67.22 ✅ inside ty=20 |
| RoW total | 68.96 – 74.61 | 62.58 – 72.95 | 63.83 ✅ inside ty=20 |
| China `MVR-Fossil-Boiler + Gas-Calciner` | 0.00 – 2.76 | 27.00 – 50.48 | 47.03 ✅ inside ty=20 |
| 2050 mix absolute error | 133.45 – 150.61 | 47.93 – 87.44 | — |

**The demand constraint behaves as expected; the regional split does not.** Global total varies
by only 1.40 Mt across runs — demand pins it. But the China/RoW *split* wanders across roughly
8 percentage points, so **regional totals are not reproducible run-to-run to better than ~±5 Mt
each.** An earlier characterisation of a "±7.7 Mt regional allocation gap" against published was
**noise, not a gap** — published sits inside the ty=20 range for both regions.

**Replicates do permit config comparison, even without a seed.** The ty=10 and ty=20 mix-error
ranges do not overlap at all (worst ty=20 run, 87.44, beats best ty=10 run, 133.45), and ty=10
cannot reach the published China share under any draw. The `TRANSITIONAL_PERIOD_YEARS = 20`
finding is therefore confirmed on output as well as on the ranking table. What is invalid is
comparing configs on *single* runs, not comparing them at all.

**Caveat on the per-technology verdicts.** Published falls inside the ty=20 range for 6 of 16
technologies. Six replicates give a range, not a confidence interval, so marginal misses are not
evidence of a real gap — `CST-Fossil-Boiler + H2-Calciner` (published 3.78 against runs
3.97–4.24) is 0.19 Mt outside and is almost certainly an unsampled tail.

**Consequences.**

- Exact, to-the-decimal reproduction of MPP's published output is impossible without their seed.
  This is much weaker than choice 19's original "cannot be reproduced from the public repo" — the
  code runs fine, the preprocessing reproduces exactly, and only the draw is unrecoverable.
  **The model is not "unreproducible" in any general sense.**
- **Single-run comparisons cannot be used to tune per-technology outcomes.** A config sweep scored
  on one draw per variant ranks noise on that metric. This invalidated a nine-variant sweep run on
  2026-08-14, which was scored on 2050 mix error.
- Config findings that rest on the *deterministic* part of the chain are unaffected — the
  `TRANSITIONAL_PERIOD_YEARS = 20` result in choice 19's correction is set arithmetic on the
  ranking table and carries no RNG at all.
- The correct test for any future config candidate is whether published output falls inside the
  run-to-run distribution over replicates, not whether one run matches.

**Not fixed by choice.** Adding a fixed seed was proposed on 2026-08-14 and declined by Parker.
Our own runs are therefore not reproducible run-to-run either. This does not affect any published
number, because the pathway uses no model run at all.

**Ask MPP for the seed** alongside the other requests in Open items.

---

## 32. Switch table: MPP's full 132-pair file, not the 92-pair file they ship as live

MPP's 1.5C smelter folder holds three switch tables. The filename the model reads,
`technology_transitions.csv`, carries 92 of the 132 pairs, and the 40 it omits are all and
only the routes into captive power with capture. Every run on it returns exactly zero CCS
because the technology is unreachable, not because it loses on cost.

**Chosen:** `technology_transitions_original.csv`, 132 pairs, swapped in by
`scenarios/patch_fulltt.py`. It is MPP's own file and a strict superset, so the swap adds the
40 capture routes and changes nothing else. It reproduces MPP's published 2050 mix to within
13.1 percentage points across six power source categories, against zero capture from the
shipped file.

**Rejected:** keeping the shipped 92-pair file on the grounds that it is what the repository
loads. Rejected because MPP's published 1.5DS puts 48.3% of 2050 production on captive
capture, 32.6 Mt, which that file cannot produce at all. Reporting zero CCS as a finding would
have been reporting an input file.

**Also rejected:** `technology_transitions_noGridtoCCS.csv`, 120 pairs. It removes the twelve
grid-to-captive-capture routes and leaves the twelve grid-to-unabated-captive routes in place,
which closes the better move and keeps the worse one. See choice 33.

Raised with MPP as a rewrite of question three. See section 24 of `MODEL_REFERENCE.md`.

---

## 33. Grid to captive fossil switches stay open

Twelve routes let a grid-connected plant revert to unabated captive fossil generation, and on
the full table twelve more let it revert to captive fossil with capture. All twelve unabated
routes are present in all three of MPP's files.

**Chosen:** leave all of them in.

The unabated routes fire in none of the four runs on the 132-pair table. Given the choice, the
cost ranking prefers captive fossil with capture over unabated captive fossil, so the unabated
routes stay empty without a prohibition. That is a result, and banning the routes would
replace it with an assumption.

The abated routes do fire, and only where the grid is dirty: 11 plants and 4.68 Mt move from
`Carbon Anode + Grid` to `Inert Anode + Natural Gas+CCS` on MPP's grid assumption and stay
there to 2050, against none at all on the SBTi power pathway. That contrast is the clearest
evidence that the reversal is driven by the grid emissions factor. Deleting the routes would
erase the evidence.

**Rejected:** deleting the twelve unabated routes as a defensive measure. It would have been
free in output terms, since they do not fire, but it would have converted a demonstrated
result into an imposed constraint for no gain.

**Rejected:** deleting the twelve abated routes. It would remove the 4.68 Mt that shows what
MPP's grid assumption costs.

Business as usual keeps all of them and is not touched. A business-as-usual world building
captive coal is the counterfactual, not an artefact. `bau/def/` is a separate file anyway.

---

## Open items

**Advanced Economies vs EMDE is not available.** MPP publishes China and Rest of the World
only. The brief's stated minimum was AE vs EMDE. Options if that split is required:
ask MPP for regional or asset-level outputs, or ask them for the solver version behind the
published refinery run so the asset-level derivation (choices 2–7) can be revived and
validated. The asset-level machinery is preserved and works — it needs trustworthy inputs,
not new code.

**RoW refinery emission factor weighting.** Approximation of ~0.10 tCO₂e/tAl in 2020,
negligible by 2050. See choice 20. Disclose in the technical report.

**Requests to put to MPP.** Consolidated: (a) regional or asset-level outputs, or the solver
version behind their published refinery run — see choice 19; (b) the RNG seed behind their
published runs, without which no run is exactly reproducible — choice 31; (c) which of their two
published emissions/intensity sheets is authoritative — below; (d) whether the
`CST-Fossil-Boiler` gas backup is switchable, given they allocate no biomass to the sector —
choice 25; (e) how their published smelter mix was produced, given four published technologies
are unreachable from both shipped artefacts — choice 17 correction.

**MPP's published emissions and intensity sheets disagree.** Published emissions divided by
published production gives 26.6 tCO₂e/tAl in 2020, while their published intensity sheet says
15.65 — a factor of 1.70 that varies by year. The intensity sheet is even named
`carbon_intensity_primary_steel_production_...`, a leftover from MPP's steel model. Neither
figure is used in this derivation, which computes intensity from production and emission
factors directly, but the discrepancy will be raised if anyone compares our absolutes to
MPP's headline numbers. Worth asking MPP which sheet is authoritative.

**Asset transition / milestone pathway.** Derived — choices 23–28, `derive_milestones.py`,
output in `milestones_aluminium.csv`. Remaining work: write it up in the Power spec format, and
confirm the two open assumptions in choice 28 (25-year auxiliary equipment lifetime, and that
post-primary casting only is acceptable coverage). The earlier concern that MPP builds new coal
smelting is withdrawn — that was a local-run artifact, not in published data.

**The CST override rests on an unverified assumption.** Choice 25 treats `CST-Fossil-Boiler` as
abated because its gas backup is assumed switchable to biogas or hydrogen. MPP's Technical
Appendix does not say whether the backup is a modelling convenience or a real design constraint,
and MPP allocates no biomass to the sector at all (Appendix p.10), so biogas is not available
inside their own scenario. Worth confirming with MPP. If the backup turns out not to be
switchable, the RoW digester milestone moves from 2022 / 2045 to 2046 / 2050 (backstop).

**No "no new unabated carbon anode" milestone.** Choice 24 fixes the set at seven, and the
carbon anode is the only group with a phase-out year but no no-new year — digester, calciner
and auxiliary all have both. `derive_milestones.py` computes the year regardless and
`milestones_aluminium.csv` carries it (China 2021, RoW 2033). Choice 24 does not record
whether the omission was deliberate. Settle before the spec write-up.

**Secondary aluminium.** The pathway covers primary aluminium only — every technology in
MPP's smelter output is an anode-based primary route. Whether the SBTi pathway needs to
address recycled/secondary production is undecided.

---

## 34. Limiting capture on captive power to the IEA rate — built, not yet working

**The rule.** Aluminium's captive coal and gas plants may add carbon capture at the same rate
the world fossil power fleet does in IEA WEO 2024 Net Zero. No uplift, no discount. Coal and
gas separately, because their penetration diverges: 40.7% and 11.9% of capacity by 2050.

Applied to the captive fleet in the unconstrained run, that allows 8 Mt of capture in 2030,
63 Mt in 2040 and 116 Mt in 2050, against 368 Mt unconstrained.

**Rejected: a share of the sector's own emissions.** Rating access to power-generation capture
by aluminium's share of all CO2 is a category error. What is being rationed is capture-equipped
fossil generation, so the denominator has to be fossil generation.

**Rejected: a cumulative cap.** IEA publishes capture-equipped capacity at 2023, 2030, 2035,
2040 and 2050, so an annual series needs only interpolation and cumulative is not forced. A
cumulative cap would also let the model spend the whole allowance by 2035 and then stop, which
is not what a rate means. `total_cumulative` would not run for aluminium anyway: it expects a
region column on a value the code extracts as a scalar, filters on technology names containing
"storage", and treats captured emissions as negative. It is a cement-only path.

**Rejected: IIASA rather than IEA.** The grid intensity already comes from the SBTi power
pathway, which is derived from IEA WEO NZE 2024. An IIASA capture limit against an IEA grid
would be two different futures in one model.

**Implementation, and its current state.** `scenarios/patch_ccs_limit.py` does four things:
populates `co2_scope1_captured`, which ships empty so the constraint would otherwise read zero
captured; writes `co2_storage_constraint.csv` in the format MPP ships for ammonia; wires the
constraint into the config and the pathway constructor, neither of which references it for
aluminium; and copies ammonia's failure handler into aluminium's brownfield agent.

**It works. Six changes were needed, all of them MPP's own code.**

1. Populate `co2_scope1_captured`, which ships empty for aluminium and populated for ammonia.
   Same convention verified against theirs: `co2_scope1` net of capture, `co2_scope1_captured`
   a positive gross amount.
2. Write `co2_storage_constraint.csv` in the format MPP ships for ammonia, read through their
   own `importer.get_co2_storage_constraint()`.
3. Wire the constraint into the config and the pathway constructor, neither of which
   references it for aluminium, exactly as `ammonia/solver/simulate.py` does.
4. Pass `deepcopy(asset_to_update)` to the tentative stack, as ammonia and cement both do.
   Without it the switch lands on the live stack before any constraint is evaluated.
5. Add a failure branch for the storage constraint using `remove_transition`, MPP's own
   function, the one the emissions constraint uses a few lines above. Ammonia's branch removes
   the whole destination technology instead, but their constraint never binds so that path was
   never exercised; with a binding limit it wipes every capture route for the year.
6. Exclude `emissions_constraint` from the brownfield pass test, the way `regional_constraint`
   already is. It is an absolute test, "is the whole stack under budget after this switch",
   so while the stack is above budget it rejects every switch including the ones that reduce
   emissions. Ammonia omits it from `CONSTRAINTS_TO_APPLY` entirely. The budget still drives
   the transition through the separate early exit at `brownfield.py:82`.

**Constraint type: `annual_addition`, not `annual_cumulative`.** The cumulative form caps the
running total, so once the fleet reaches the cap every capture switch is rejected for the rest
of the run and plants strand on unabated fossil. `annual_addition` caps the year-on-year
increase, giving a fresh allowance each year, which is what limiting rather than banning
requires. The file therefore carries the increment of the allowance stock.

**Result.** 2050 capture falls from 290–368 Mt unconstrained to 25–32 Mt across the four runs,
with 0 to 8.4% of production left on unabated fossil and cumulative emissions between the
no-capture and unlimited cases in every pairing. Tested adjustable: quadrupling the series
gives 4.3 times the capture.

**Checked, not assumed: the constraint does not bind in MPP's own ammonia run.** Running their
shipped `lc` pathway unchanged, capture exceeds their own limit in 30 of 31 years, reaching
119.6 Mt against 38.8 Mt. Their file is shaped like a cumulative deployment curve and their
config reads it as a rate, so the annual increments of 0.8 to 16.3 Mt pass against limits of
6.5 to 38.8 Mt while the total runs to three times the cap.

**Cement could not be used as a reference.** No `data/` directory ships, so the sector cannot
be run.

---

## Open items

**Advanced Economies vs EMDE is not available.** MPP publishes China and Rest of the World
only. The brief's stated minimum was AE vs EMDE. Options if that split is required:
ask MPP for regional or asset-level outputs, or ask them for the solver version behind the
published refinery run so the asset-level derivation (choices 2–7) can be revived and
validated. The asset-level machinery is preserved and works — it needs trustworthy inputs,
not new code.

**RoW refinery emission factor weighting.** Approximation of ~0.10 tCO₂e/tAl in 2020,
negligible by 2050. See choice 20. Disclose in the technical report.

**Requests to put to MPP.** Consolidated: (a) regional or asset-level outputs, or the solver
version behind their published refinery run — see choice 19; (b) the RNG seed behind their
published runs, without which no run is exactly reproducible — choice 31; (c) which of their two
published emissions/intensity sheets is authoritative — below; (d) whether the
`CST-Fossil-Boiler` gas backup is switchable, given they allocate no biomass to the sector —
choice 25; (e) how their published smelter mix was produced, given four published technologies
are unreachable from both shipped artefacts — choice 17 correction.

**MPP's published emissions and intensity sheets disagree.** Published emissions divided by
published production gives 26.6 tCO₂e/tAl in 2020, while their published intensity sheet says
15.65 — a factor of 1.70 that varies by year. The intensity sheet is even named
`carbon_intensity_primary_steel_production_...`, a leftover from MPP's steel model. Neither
figure is used in this derivation, which computes intensity from production and emission
factors directly, but the discrepancy will be raised if anyone compares our absolutes to
MPP's headline numbers. Worth asking MPP which sheet is authoritative.

**Asset transition / milestone pathway.** Derived — choices 23–28, `derive_milestones.py`,
output in `milestones_aluminium.csv`. Remaining work: write it up in the Power spec format, and
confirm the two open assumptions in choice 28 (25-year auxiliary equipment lifetime, and that
post-primary casting only is acceptable coverage). The earlier concern that MPP builds new coal
smelting is withdrawn — that was a local-run artifact, not in published data.

**The CST override rests on an unverified assumption.** Choice 25 treats `CST-Fossil-Boiler` as
abated because its gas backup is assumed switchable to biogas or hydrogen. MPP's Technical
Appendix does not say whether the backup is a modelling convenience or a real design constraint,
and MPP allocates no biomass to the sector at all (Appendix p.10), so biogas is not available
inside their own scenario. Worth confirming with MPP. If the backup turns out not to be
switchable, the RoW digester milestone moves from 2022 / 2045 to 2046 / 2050 (backstop).

**No "no new unabated carbon anode" milestone.** Choice 24 fixes the set at seven, and the
carbon anode is the only group with a phase-out year but no no-new year — digester, calciner
and auxiliary all have both. `derive_milestones.py` computes the year regardless and
`milestones_aluminium.csv` carries it (China 2021, RoW 2033). Choice 24 does not record
whether the omission was deliberate. Settle before the spec write-up.

**Secondary aluminium.** The pathway covers primary aluminium only — every technology in
MPP's smelter output is an anode-based primary route. Whether the SBTi pathway needs to
address recycled/secondary production is undecided.

---

## 34. Limiting capture on captive power to the IEA rate — built, not yet working

**The rule.** Aluminium's captive coal and gas plants may add carbon capture at the same rate
the world fossil power fleet does in IEA WEO 2024 Net Zero. No uplift, no discount. Coal and
gas separately, because their penetration diverges: 40.7% and 11.9% of capacity by 2050.

Applied to the captive fleet in the unconstrained run, that allows 8 Mt of capture in 2030,
63 Mt in 2040 and 116 Mt in 2050, against 368 Mt unconstrained.

**Rejected: a share of the sector's own emissions.** Rating access to power-generation capture
by aluminium's share of all CO2 is a category error. What is being rationed is capture-equipped
fossil generation, so the denominator has to be fossil generation.

**Rejected: a cumulative cap.** IEA publishes capture-equipped capacity at 2023, 2030, 2035,
2040 and 2050, so an annual series needs only interpolation and cumulative is not forced. A
cumulative cap would also let the model spend the whole allowance by 2035 and then stop, which
is not what a rate means. `total_cumulative` would not run for aluminium anyway: it expects a
region column on a value the code extracts as a scalar, filters on technology names containing
"storage", and treats captured emissions as negative. It is a cement-only path.

**Rejected: IIASA rather than IEA.** The grid intensity already comes from the SBTi power
pathway, which is derived from IEA WEO NZE 2024. An IIASA capture limit against an IEA grid
would be two different futures in one model.

**Implementation, and its current state.** `scenarios/patch_ccs_limit.py` does four things:
populates `co2_scope1_captured`, which ships empty so the constraint would otherwise read zero
captured; writes `co2_storage_constraint.csv` in the format MPP ships for ammonia; wires the
constraint into the config and the pathway constructor, neither of which references it for
aluminium; and copies ammonia's failure handler into aluminium's brownfield agent.

**A fifth change was needed, and it is the one that mattered.** The four patches above left
capture at 336 Mt against a 116 Mt limit. The cause is that aluminium's brownfield agent applies
a switch to the live stack before checking any constraint, so rejecting it has no effect.
Ammonia and cement both pass `deepcopy(asset_to_update)`; aluminium passes the live object.
Adding the `deepcopy` to match them takes 2050 capture from 355 Mt to 21 Mt in the same run.
Section 21b of `MODEL_REFERENCE.md` has the full account.

This also explains the earlier abandoned attempt at a capture cap through
`demand_share_constraint`: it was never going to bind either.

**Checked, not assumed: the constraint does not bind in MPP's own ammonia run.** Running
ammonia's shipped `lc` pathway unchanged, capture exceeds their own limit in 30 of 31 years,
reaching 119.6 Mt against 38.8 Mt. The reason is different from aluminium's: ammonia sets
`CO2_STORAGE_CONSTRAINT_TYPE = "annual_addition"`, so the limit is compared against the
year-on-year *increase* in capture rather than the total. Those increases are 0.8 to 16.3 Mt
against limits of 6.5 to 38.8 Mt, so they pass in 27 of 31 years while the total runs to three
times the cap. Their file is shaped like a cumulative deployment curve and read as a rate.

We use `annual_cumulative`, which compares the total captured against the limit. That is the
correct pairing for a series that is itself a total, and it is stricter than MPP's own setting.
