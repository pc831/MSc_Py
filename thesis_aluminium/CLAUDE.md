# Aluminium sector pathways — project state

Last updated 2026-08-24.

Read `MODEL_REFERENCE.md` first. It is the verified account of how the MPP model works and
what the scenario runs show, checked line by line against source and against run output.
`pathway_derivation_choices.md` holds the 28 choices behind the earlier published-data work.

## What we are doing

**We are not reproducing MPP's 1.5°C scenario. We are using their model to build SBTi's own.**
Following the method Humphrey used on steel with Steel-IQ.

The method: run the model under progressively more ambitious scenarios using best-guess
assumptions, which exposes which inputs actually move the sector and which are flat,
placeholder or missing. **Those exposed gaps become the data request to IIASA.** The runs are
not waiting on IIASA — they are how we work out what to ask for. We work with IIASA directly,
so the ask is not limited to published data.

Two end products: a slide deck mirroring Humphrey's, and an aluminium data request in the same
format as the steel one (`~/Downloads/IIASA data variable list.docx`).

## Where things stand

| Piece | State |
|---|---|
| Model mapping | **Done** — `MODEL_REFERENCE.md`, 25 sections |
| Model deep dive deck | **Done to slide 7** — `~/Downloads/Aluminium Model Deep Dive and IIASA Data Request (1).pptx` |
| Twelve scenario runs, both plant types | **Done** — `scenarios/runs/`, rebuilt 2026-08-26. Three capture regimes; the superseded `noCCS` set is in `_archive/` |
| Carbon capture limit | **Done** — IEA-derived, enforced through MPP's own constraint. Needed six changes, two of them defects in their aluminium module |
| Scenario results deck | **Stale** — `~/Desktop/Aluminium Scenario Results.pptx`, 14 slides, still quotes the superseded 92-pair numbers |
| Questions for MPP | **Seven**, see below |
| IIASA data request | Not started |
| Earlier published-data pathway | Complete, now a benchmark. See the bottom of this file |

**Never rendered the decks.** LibreOffice is not installed on this machine, so table widths
and text fitting in `Aluminium Scenario Results.pptx` are estimates.

## The twelve scenarios

Three things vary. Naming is `LC_<grid>grid_<capture>_Anode<Locked|Unlocked>`.

| Axis | Values |
|---|---|
| Grid | `MPPgrid` (MPP's own assumption) or `SBTigrid` (SBTi power pathway V4.0) |
| Capture | `noCCS`, `limitedCCS`, `CCS` |
| Inert anode | `AnodeLocked`, or `AnodeUnlocked` with our six added power-source switches |

`noCCS` is MPP's shipped switch table, where capture-equipped power is unreachable. It is
superseded and lives in `_archive/scenarios_92switches/`, kept only as evidence. `CCS` is
MPP's full table with no cap. `limitedCCS` is the full table with capture held to the IEA WEO
2024 NZE world rate, and **it is the set to use**.

Combined cumulative against the 11.99 Gt budget:

| Grid / inert anode | noCCS | limitedCCS | CCS |
|---|---|---|---|
| MPP, locked | 13.7 Gt, +14.3% | 13.2 Gt, +10.0% | 12.5 Gt, +3.9% |
| MPP, unlocked | 13.2 Gt, +9.9% | 12.3 Gt, +2.4% | 12.5 Gt, +4.0% |
| SBTi, locked | 13.0 Gt, +8.3% | 12.3 Gt, +2.4% | 12.4 Gt, +3.4% |
| SBTi, unlocked | 12.1 Gt, +1.2% | 12.1 Gt, +1.1% | 12.4 Gt, +3.0% |

2050 capture is zero in every `noCCS` run, 25 to 32 Mt across `limitedCCS`, and 290 to 368 Mt
across `CCS`. `BAU` is 31.12 Gt.

Smelting is 10.1 to 10.4 Gt across the limited runs, refining 2.05 to 2.09 Gt everywhere.
Refining has no grid exposure and no capture route, so neither lever touches it.

**`LC_MPPgrid_CCS_AnodeUnlocked` is closest to MPP's published 1.5DS**, 13.1 percentage points
of deviation across the six 2050 power source categories against 21.5 for the next best.
Adding our six switches moves the run toward their published mix, not away from it.

## Making the capture limit work took six changes to MPP's model

All of them are MPP's own code, and two are outright defects in the aluminium module. Section
21b of `MODEL_REFERENCE.md` and choice 34 have the detail. In short: aluminium's brownfield
agent applied every switch to the live stack before checking any constraint, because it passes
the live asset where ammonia and cement pass `deepcopy(asset_to_update)`. Fixing that exposed
a second problem, that the emissions constraint is an absolute "is the stack under budget"
test which rejects even switches that cut emissions, and which ammonia omits entirely.

These two are the strongest questions we have for MPP, and both are narrow and checkable.

## The headline finding

**MPP's switch table lets a plant change its power source only while it still has a carbon
anode.** Once the anode is converted the power source is frozen. `Inert Anode + Natural Gas`
and `Inert Anode + Coal` have themselves as their only destination, in all three shipped
variants of the file. Anode type and electricity supply are physically independent, so this
looks like an omission.

It strands 7.4 Mt on captive gas and 1.5 Mt on captive coal in 2050 with no route out. Adding
six switches — those two origins reaching grid, power purchase agreement and reactor — closes
a third of the gap to the budget on MPP's own grid assumption. Section 20 of
`MODEL_REFERENCE.md` has the full account.

## Questions for MPP

Seven. The last two are new on 2026-08-26 and are the strongest, because both are narrow,
checkable, and differences between aluminium and MPP's own other sectors.

1. **The frozen power source.** A plant may change its power source only while it still has a
   carbon anode. Section 20.
2. **The one-renovation-per-plant rule**, which makes a second change cost a full rebuild.
3. **Which switch table produced the published result.** They ship three; the one the code
   reads has every capture-power route deleted, and their full table reproduces the published
   mix. Carries a second part: what `technology_transitions_noGridtoCCS.csv` is for, given it
   closes the twelve grid-to-captive-capture routes and leaves all twelve grid-to-unabated
   routes open.
4. **Whether the CO₂ storage limit can be applied here.** Now largely answered by us; keep it
   for the storage capacity number itself. Should sit after question 3.
5. **Whether plants reaching end of life should open up switches.**
6. **Why aluminium's brownfield agent omits the `deepcopy`** that ammonia and cement both
   have, so every switch is applied to the live stack before any constraint is checked.
   Section 21b.
7. **Whether `emissions_constraint` is meant to be in aluminium's `CONSTRAINTS_TO_APPLY`.**
   It is an absolute test that rejects switches which reduce emissions, and ammonia omits it
   entirely. Section 21b.

Three dropped after we solved them ourselves: the refinery ranking table columns, the zero
lifetime on grid technologies, and whether the budget is meant to be reached.

## How to run something

```
cd scenarios
python run.py <scenario> <pathway> <plant> [model_dir]
```
`plant` is `smelter` or `refinery`. `model_dir` is a folder name inside `models/` and defaults
to `model_clean`. Results land in `runs/<scenario>/<plant>/`.

Nine model copies, all gitignored and rebuildable:

- `model_clean` — MPP commit `b09472f` with three run fixes only: sector set to aluminium, a
  pandas 2 fix in output processing, and `demand.csv` swapped for `demand_lc.csv` on the
  smelter side. Still carries MPP's shipped 92-pair switch table, so it is the reference for
  what MPP ships, not a scenario base
- `model_{MPP,SBTi}grid_CCS_Anode{Locked,Unlocked}` — clean plus `patch_fulltt.py`, and
  `patch_grid.py` for the SBTi pair
- `model_{MPP,SBTi}grid_limitedCCS_Anode{Locked,Unlocked}` — the above plus `patch_ccs_limit.py`

Patch scripts, each taking a model folder name inside `models/`:

- `patch_fulltt.py` swaps MPP's full 132-pair `technology_transitions_original.csv` in for the
  92-pair file they ship as live, and adds our six power-source switches unless
  `--no-extra-switches` is passed
- `patch_grid.py` rescales scope 2 to the SBTi power pathway
- `patch_ccs_limit.py` applies the six changes the capture limit needs, listed in its docstring

To rebuild: copy `mpp-upstream-reference`, apply the three run fixes, then the patch scripts.
Each run saves the inputs that produced it under `<scenario>/<plant>/inputs_used/`.

Layout inside `scenarios/`: `models/` holds the model copies, `runs/` holds their outputs,
`notebooks/analysis/` holds tables, `notebooks/plots/` holds figures, `figures/` holds the
rendered output as png and svg. Analysis and plotting are separate on purpose, and both import
loaders, the scenario registry and the figure helpers from `common.py`.

| Notebook | What it produces |
|---|---|
| `analysis/01_scenario_summary.ipynb` | cumulative emissions, intensity, 2050 mix, milestone years |
| `analysis/02_switch_table_evidence.ipynb` | the numbers behind the switch table decision |
| `plots/01_smelting_emissions.ipynb` | `smelting_emissions_annual`, `smelting_emissions_cumulative` |
| `plots/02_electricity_generation_mix.ipynb` | `electricity_generation_mix`, the headline figure |
| `plots/03_emissions_intensity.ipynb` | `emissions_intensity_process_vs_electricity` |
| `plots/04_alumina_refining.ipynb` | `refining_emissions_annual`, `refining_digester_technology` |
| `plots/05_carbon_budget_outcome.ipynb` | `budget_cumulative_over_time`, `budget_total_bars`, and the summary table |

Most plot notebooks draw all twelve runs on the same three by four layout, capture regime down
the rows and grid and inert anode across the columns, panels numbered (1) to (12).

Two are deliberately different. **Refining** is one axes rather than a matrix: the capture
regime and the anode rule are both smelter-side and the grid patch skips the refinery folder,
so all twelve solve refining from identical inputs and the 2.8% spread between them is solver
noise. **The budget outcome** notebook compares the twelve against each other rather than over
the matrix, as lines over time and as bars, for smelting alone and for smelting plus refining.
Its table carries business as usual as row 0 and the twelve as rows 1 to 12, matching the panel
numbers in the other figures.

`02_electricity_generation_mix.ipynb` and `05_carbon_budget_outcome.ipynb` are self contained
and import nothing from `common.py`, so every label and position is editable in the cell.

`make_figures.py` writes the five deck figures as `fig1` to `fig5` from the `limitedCCS` runs,
in png and svg. `build_deck.py` builds the results deck on the SBTi template.

`_archive/` holds superseded runs, model copies, patch scripts and notebooks. Never cite it.
The zero CCS in `_archive/scenarios_92switches/` is an artefact of MPP's shipped input file,
not a result.

## Working preferences

- Ask before running anything. Every time.
- Answer the question asked. No adjacent findings, no unsolicited next steps.
- Be concise in chat. Say less, don't move the volume into a file.
- No invented jargon. Plain words.
- Verify before asserting. If it cannot be shown, it is not known.
- Log normative choices to `pathway_derivation_choices.md` with the rejected alternative.

---

# Earlier work — the published-data pathway

Complete, and now a benchmark rather than the product. Built entirely from MPP published
workbooks plus unmodified repo inputs, no local run. It is what we compare our scenarios
against, and the reference for what MPP's published 1.5°C says.

## Process emissions intensity, t CO₂ per tonne aluminium, China and Rest of the World

| Year | China | RoW | Global |
|---|---|---|---|
| 2020 | 3.911 | 3.684 | 3.810 |
| 2030 | 3.843 | 2.734 | 3.373 |
| 2040 | 1.028 | 1.145 | 1.084 |
| 2050 | 0.434 | 0.217 | 0.328 |

Reduction by 2050: China 88.9%, RoW 94.1%, Global 91.4%. Published at five-year intervals
only. The raw shape is published as-is, not reshaped to be monotonic.

## Boundary — process emissions only

All electricity excluded, both purchased power and captive generation. In scope: smelter anode
process CO₂ and fluorocarbons and anode thermal, plus refining digestion and calcination fuel.

MPP reports captive fossil power inside scope 1, so removing it needs the residual split in
choice 10. Captive power would have added roughly 0.2 (advanced), 5.3 (emerging) and 10.0
(China) t CO₂ per tonne in 2020.

This boundary carries over unchanged. Scope 1 and 2 does not work for aluminium, because
captive generation switching to grid supply moves emissions across the boundary and makes the
series discontinuous for reasons unrelated to decarbonisation.

## Milestones

`derive_milestones.py` → `milestones_aluminium.csv`; the workbook agrees cell for cell.

| Milestone | China | RoW |
|---|---|---|
| No new unabated fossil digester | 2021 | 2022 |
| Phase out unabated fossil digester | 2042 | 2045 |
| No new unabated fossil calciner | 2031 | 2022 |
| Phase out unabated fossil calciner | 2050\* | 2050\* |
| Phase out unabated carbon anode | 2042 | 2043 |
| No new unabated fossil auxiliary | 2025 | 2025 |
| Phase out unabated fossil auxiliary | 2050\* | 2050\* |

\* set by the 2050 backstop; the source scenario does not deliver these on its own.

Four things drive every number: captive power is out of scope (choice 24); unabated means
failing both a 90% capture test and a 10%-of-baseline intensity test, judged on data not names
(choice 25); a 1% of 2020 materiality threshold (choice 26); and the 2050 backstop (choice 27).
Three classifications that names would get wrong: `MVR-Fossil-Boiler` is abated on intensity;
`Carbon Anode+CCS` is abated on capture only and still leaves about 1.0 t CO₂ per tonne;
`CST-Fossil-Boiler` is abated by explicit override, which is the most load-bearing judgement in
the table.

Auxiliary comes from IAI, not MPP, because MPP models only refining and smelting (choice 28).

## Files from that work

- `build_pathway_workbook.py`, `validate_against_mpp.py` — intensity pathway
- `derive_milestones.py`, `build_milestone_workbook.py`, `fig_milestones.py` — milestones
- `build_assumption_table.py` → `assumption_table_aluminium.csv`
- Workbooks at `~/Desktop/Aluminium Pathway Derivation/`
- `mpp_aluminium_net_zero_outputs.xlsx` (global), `(1)` China, `(2)` Rest of the World.
  Sheet `Annual_production_volume_Mt_df` carries both 1.5DS and BAU in a scenario column —
  filter it. Do not use the emissions or intensity sheets; they disagree by a factor of 1.7
  and the intensity sheet is still named after MPP's steel model.
