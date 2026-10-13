# Idea A — running strategic context

Strategic layer above the detailed logs (`thesis_design_choices.md` D1–D11/O1–O10,
`MODEL_REFERENCE.md`, `CLAUDE.md`). Read to restore context after a `/clear`; append dated
decisions here as they are made. Started 2026-08-30.

## Working question
At fixed VL ambition, how do the grid decarbonisation pathway (varied across IAMs) and the
captive-power CCS constraint shape the least-cost electricity sourcing of primary aluminium
smelting — and where do those choices make the sector budget infeasible or force an outsized
claim on shared CCS. Two-model division of labour: **MPP** asset-level stock + emission factors;
**GCAM/IAM** demand + grid electricity intensity. (Full framing: `thesis_design_choices.md`.)

## State as of 2026-09-02
Design pivoted to the **GCAM ambition-ladder** (decision 11 below). The earlier **multi-IAM
grid × CCS at fixed VL** design — its working question, choices, and the 16-cell PoC matrix with
its 2026-08-30 findings — is **parked and moved to `_archive/IDEA_A_multi_IAM.md`** (still a good
idea; survives as the robustness axis on the central ambition rung). The "CCS paradox" from that
PoC is **retracted** (stochastic noise, decision 7). Read the 2026-09-02 block below for the
active direction and critical path.

---

## Session decisions & findings — 2026-09-02 (supersedes parts of 08-30)

### 7. Finding #1 ("CCS paradox") RETRACTED — stochastic noise, not signal
`none < unlimited` rests on ~0.16 Gt / ~1.3% cross-cell differences; MPP's agent ranking has
stochastic tie-breaking and each PoC cell ran **once**. A single run can't distinguish a real
ordering from seed variance. The whole −0.0% to −3.9% "feasibility gradient" likely sits near or
inside the noise floor. To make any cross-cell claim: run one cell N times across seeds,
characterise the spread, trust only orderings that clear it. Not a headline finding.

### 8. Finding #2 REVERSED — GCAM aluminium IS primary demand (verified)
Earlier claim ("GCAM primary is really *total*") was wrong. GCAM `aluminum` is calibrated/
downscaled on **USGS *electrolytic* (= primary) production**; base-year quantity is primary. The
56.5→121 Mt growth is consistent with a primary series (primary itself ran ~24→65 Mt 2000-2020).
- **MPP and GCAM are both primary-only → GCAM demand drops straight into MPP** (same quantity
  concept, no scrap-loop reasoning). The MFA/ODYM coupling is **no longer on the critical path**;
  reserve as optional refinement (GCAM's primary trajectory embeds an implicit, invisible
  circularity assumption, but it is usable as-is).
- Base offset: GCAM 2021 = 56.5 vs MPP/observed 2020 ≈ 65.3 (~13% low). Resolved by the 2025
  anchor (below), not by rebasing.

### 9. GCAM aluminium structure verified against `aluminum.xml` + official doc diagram
- `aluminum` (smelting) stub-tech inputs = **`alumina` feedstock + `elect_td_ind` (grid
  electricity ~0.054 GJ/kg ≈ 15 MWh/t). No CO2 coefficient, no F-gas.** Only emitting input =
  electricity; **all** smelting electricity (captive incl.) is in scope. Earlier "GCAM misses
  captive power" was WRONG. `alumina` (refining) carries the 8 fuel techs (coal/RL/gas/biomass
  ± CCS) — refining direct CO2 lives here.
- **Spine (locked):** MPP is the **zoom INTO GCAM's single Electricity smelting technology** —
  resolving anode type, captive-vs-grid, vintage, PFC, CCS that the logit can't see. GCAM says
  "aluminium ~solved by 2050 because the grid is clean" (SSP1-1.9: smelting elec 4.85 EJ ×
  near-zero grid → ~0; refining stays ~27 MTC; anode/PFC = 0, unmodelled). The thesis measures
  the **asset-resolution gap** between GCAM's smooth pathway and MPP's asset reality.

### 10. Budget taken FROM GCAM (scales with production)
`budget(t) = GCAM_smelting_elec_emis(t) + GCAM_refining_direct_CO2(t) + (anode_CO2/t + PFC/t) ×
GCAM_production(t)`. All from GCAM except the two per-tonne factors (MPP/IAI-calibrated), which
GCAM lacks. Two calls:
- Electricity term uses **GCAM's own (scenario) grid, fixed** — NOT the treatment grid (would be
  circular). **Rejected:** IAM/treatment grid in the budget.
- Anode+PFC/t **declines on a 1.5°C inert-anode shape** (~2 t/t carbon → ~0.06 inert), adding
  only non-electricity/non-refining smelting terms. **Rejected:** constant (never abates hardest
  term) and pulling MPP refining intensity too (double-counts GCAM refining).

### 11. DESIGN PIVOT — ambition axis via GCAM scenario ladder (supersedes D2/D3 cross-IAM)
Vary **climate ambition** by using different **GCAM runs**, each supplying its own internally
consistent **grid + demand + budget**; MPP held fixed; **CCS-regime crossed** as the MPP-side
asset axis. Matrix = GCAM-scenario (ambition) × CCS-regime.
- **Escapes D2's tautology ban:** outcome variable is now the *asset-resolution gap vs GCAM's own
  pathway* (not "does more ambition need more CCS"). Each cell self-consistent; no
  REMIND-grid + GCAM-demand + constructed-budget frankenstein.
- **Demand is ~ambition/SSP-invariant** (114–122 Mt across SSP1/2/4). Ambition acts through
  **grid + budget**, not demand — name this.
- **Rejected:** cross-IAM grid at fixed VL (original D3) → demoted to a robustness axis on the
  central rung.

### 12. SSP2 chosen for the ladder; CMIP7/VL mapping (read van Vuuren 2026, GMD 19:2627)
- **CMIP7 ScenarioMIP scenarios & markers:** VL(SSP1/REMIND,~1.6°C), LN(SSP2/AIM), L(SSP2/
  MESSAGE), ML(SSP2/COFFEE), M(SSP2/IMAGE,≈SSP2-4.5), HL(SSP5/WITCH), **H(SSP3/GCAM)**.
- **SSP2 is the CMIP7 low-to-medium backbone (LN/L/ML/M)** → an SSP2 forcing ladder is
  forward-compatible. Interim ladder = **SSP2 at 1.9/2.6/3.7/4.5**. Need to run **GCAM SSP2-1.9
  and SSP2-2.6** (on disk: SSP2_3p7, SSP2_4p5; also SSP1_1p9, SSP1_2p6, SSP4_6p0).
- **VL wrinkle:** official VL is **SSP1/REMIND, not GCAM** (GCAM = official H). REMIND likely
  won't resolve aluminium → **GCAM stays the aluminium-demand engine** (run at VL-matching
  forcing); grid from REMIND/VL. Build the pipeline this way.
- **AR6 C1 vs SSP-RCP (user's Q):** SSP1-1.9 = one *scenario* (SSP + forcing + marker IAM).
  **AR6 C1 = an outcome *category*** (~97 scenarios ≤1.5°C no/limited overshoot across many
  models); SSP1-1.9 ∈ C1. **CMIP7 VL = a single scenario** (successor to SSP1-1.9), so
  "VL replaces C1" narrows a category-statistic to one harmonized pathway — flag in write-up.

### 13. Literature precedents (subagent scan 2026-09-02)
- Soft-link GCAM+external sector model: **Zhang 2025 (JIE, doi 10.1111/jiec.13600)**,
  **Rinaldi 2025 (ES&T, doi 10.1021/acs.est.5c15099 — verify authors)**.
- GCAM industry-detailing (JGCRI, the "Speizer" on-disk runs): **Speizer 2023 (One Earth
  6:1494)**, **Durga, Speizer & Edmonds 2024 (Energy & Climate Change 5:100152)**.
- Hard-coupled contrast: **Ünlü 2024, MESSAGEix-Materials (GMD 17:8321)**.
- Bottom-up Al asset study to cite & differentiate: **Tan et al. 2025 (Nat Clim Change 15:51–58,
  s41558-024-02193-x)** — standalone; we couple to GCAM. NB possible mis-attribution: notes call
  `Moritz_2024_Model/` a Pauliuk/ODYM MFA — check the folder vs this paper.
- **Novelty gap (white space):** no published study fixes one SSP and sweeps a forcing ladder for
  one industrial sector's asset-level feasibility. Position as methodological novelty.

### BUG FOUND & FIXED — GCAM demand wasn't reaching the solve (2026-09-02)
First ladder run produced ~65 Mt flat (MPP's own), not GCAM's 80→121: the model's `get_demand()`
reads **`demand.csv`** (`mppshared/import_data/intermediate_data.py:229`), but `write_demand` had
written only `demand_lc.csv`. So GCAM demand never drove production while the budget was GCAM-sized
→ everything sat under budget, non-monotonic fossil. Fix: `write_demand` now writes **both**
`demand.csv` (read) and `demand_lc.csv`. Re-ran: production tracks GCAM (SSP1-1.9: 75.8→120.4 Mt). Lesson: MPP reads `demand.csv`, not
`demand_lc.csv`.
Corrected gaps (cum 2025-50 emis − budget) are **small (±0.15 Gt, ~2%) and NON-MONOTONIC across
CCS** within a scenario (e.g. SSP2-3.7: none +0.12, low +0.04, high +0.16, unlimited −0.03) —
i.e. **consistent with solver noise, NOT a finding** (same over-read as retracted decision 7).

**Noise floor MEASURED (2026-09-02):** ran SSP1_1p9_unlimited 3× with identical inputs → cumulative
2025-50 emissions **6.539 / 6.560 / 6.617 Gt** (spread 0.077 Gt on 3 seeds; annual swings ≤15
Mt/yr). **MPP is stochastic, confirmed.** So:
- **CCS regime + fine budget gaps (~0.15 Gt) are INSIDE the noise → not interpretable from single
  runs.** Need ensembles: N seeds/cell, compare distributions (cheap now cells run parallel).
- **Ambition axis IS robust:** cumulative 6.5 / 9.3 / 14.2 / 15.9 Gt across SSP1-1.9→SSP2-4.5 =
  20-100× the noise floor. The GCAM-scenario axis (demand+grid+budget together) is the real signal.
- TODO: find/set an MPP seed for reproducibility; build an ensemble runner (add a seed loop to
  `run_gcam_ladder.py`). Do NOT report any within-scenario/CCS ordering without an ensemble.
- TODO (re-open O5, 2026-09-02): **rate-limit ALL clean technologies, not just CCS.** SSP1-1.9
  shows unrealistic build rates (e.g. SMR/nuclear jumping to ~7 Mt at 2050, and other clean
  switches ramping implausibly fast). O5 was downgraded on 08-30 (see `_archive/IDEA_A_multi_IAM.md`)
  because a clean-captive cap wouldn't bind under the old design; the GCAM-growth demand changes
  that. Apply empirical max deployment/diffusion rates to nuclear/SMR, hydro, and grid-switching,
  analogous to the FGD-rate CCS limits. **PRIORITY RAISED** — it is the lever that makes
  feasibility real (see finding 14).

### 14. Why every cell ~reaches budget, and what makes feasibility real (2026-09-02)
Investigated the "it solves everywhere" surprise (user expected SSP1-1.9 to fail):
- **Budget co-moves with grid by construction.** The smelter budget is built from the SAME GCAM
  scenario's grid × production + anode/PFC, so the model is asked to hit a target GCAM's own world
  roughly achieves — and it can ride the very same grid the budget assumes. So the ONLY thing that
  can break feasibility is **asset friction** (anode lag, stranded captive fossil, buildout limits).
- **That friction is currently swamped** by two unrealistic things: (1) GCAM's implausibly fast grid
  decarb (China 0.70→0.09 t/MWh in one 5-yr step), and (2) **no cap on clean buildout** — clean
  capacity jumps +46 Mt in the single 2025→2030 step; SMR/nuclear reaches ~30 Mt. So it decarbonises
  effortlessly and CCS is never *needed*.
- **CCS is a substitute, not a necessity:** SSP1-1.9 `none` ~0 CCS vs `unlimited` 45–58 Mt; both
  ~reach budget by riding the grid. SSP1-1.9 `none` is actually marginally OVER budget from 2035
  (~2–5%, within the noise floor) — not cleanly feasible, just close.
- **"solve" = reach the budget** (user's definition); MPP always runs to completion regardless.
- **NEXT STEPS to make feasibility real:** (a) [doing now] close the O4b `none`-CCS leak (finding 15);
  (b) **rate-limit ALL clean techs** (nuclear/SMR, hydro, grid-switching) at empirical rates — THIS is
  what tips SSP1-1.9 `none` back into genuine infeasibility (assets can't follow the grid fast enough);
  (c) swap the stand-in GCAM grids for realistic/better-converged runs.

### 15. BUG — `none` regime leaks CCS via the rebuild route (O4b), fixing now (2026-09-02)
`none` (should be zero captive CCS) shows **1.18 Mt `Carbon Anode + Coal+CCS`** in SSP1-1.9: **5
plants, all via REBUILD (0 greenfield), first at 2028.** `patch_ccs_limit` caps *retrofit
penetration* of the existing fleet at 0% but does NOT cover the **rebuild/greenfield → +CCS power
route**, so a plant rebuilding in place adopts Coal+CCS regardless of `none`. Scenario-dependent
(SSP2-4.5 `none` = 0, doesn't choose it). Fix: block rebuild+greenfield transitions into any `+CCS`
power tech under `none` (and route them through the penetration cap for `low`/`high`). Closes O4/O4b;
makes `none` a true no-CCS counterfactual.
**FIX IMPLEMENTED (simple, no model-code change):** `run_gcam_ladder.strip_power_ccs_switches()`
deletes every switch row whose DESTINATION power source ends in `+CCS` (Coal+CCS / Natural Gas+CCS)
from the live `technology_transitions.csv`, for `none` cells only. So no agent (brownfield/
greenfield/rebuild) can reach captive-power CCS. Anode-only CCS on clean power (e.g. `Carbon
Anode+CCS + Grid`) is kept — `none` bars captive *power* CCS only. Verified: strips the 6 power-CCS
destinations incl. the leaked `Carbon Anode + Coal+CCS`. `low`/`high` unchanged (retrofit-capped;
their greenfield/rebuild leak is a smaller follow-up).
**DONE & VERIFIED (2026-09-03):** re-ran the 4 `none` cells — **captive-power CCS = 0 in all four**
(SSP1-2.6 `none` retains 1.21 Mt `Carbon Anode+CCS + PPA+Grid` = anode CCS on clean power, correctly
kept). Feasibility ~unchanged (SSP1-1.9 `none` gap +0.188 vs +0.18 — leak was tiny, plants switched
to grid). Notebooks/figures regenerated. Also confirmed the `none`-run hook works (blocked a real
run until the "execute" keyword was present).

### 16. SSP socioeconomics drive grid cleanliness — a confound in the mixed ladder (2026-09-02)
User insight, correct: GCAM grid intensity = f(SSP socioeconomics, forcing target). **SSP1**
(sustainability: cheap renewables, high CCS cost, lower demand) decarbonises the grid fast/cheaply;
**SSP2** (core costs) is slower for the SAME forcing. So SSP1-1.9's near-zero grid is partly an
**SSP1 artefact**, giving the smelter an "easy electricity way out"; **SSP2-1.9 (same 1.9 target,
slower grid) would be a stricter 1.5C test** and likely tips toward the infeasibility we expect.
The current interim ladder confounds this — the two most-ambitious rungs (SSP1 1.9/2.6) are ALSO the
cleanest-grid SSP worlds, the two least (SSP2 3.7/4.5) the dirtier. => **strong reason to prioritise
the single-SSP2 ladder** (run GCAM SSP2-1.9/2.6): it removes the SSP-grid confound AND is the more
stringent feasibility test.

### CAVEAT — the interim GCAM runs are stand-ins, not publishable quality (2026-09-02)
The four GCAM SSP-RCP runs (SSP1-1.9/2.6, SSP2-3.7/4.5) were **hard to get to solve** and are
**not publishable quality** — expect solver artefacts (e.g. China grid dropping 0.70→0.09 t/MWh in
one 2025→2030 step under SSP1-1.9). They validate the **pipeline/method only**; do not interpret
specific magnitudes or shapes as findings. Final version swaps in better GCAM scenarios (add to
`SCENARIOS` in `pipeline/gcam_extract.py`, rebuild `gcam_cache/`). Extracted series are cached to
`pipeline/gcam_cache/*.csv` so the runner never re-queries BaseX. NB these are SSP-RCP pairs, NOT
the future CMIP7 VL/L scenarios — keep the two label systems separate.

### GCAM data access (for reuse)
DB: `~/repos/gcam/output/database_basexdb`. Query: `~/repos/gcam/.venv/bin/python` + `gcamreader`
(`LocalDBConn('output','database_basexdb')`, `parse_batch_query('output/queries/Main_queries.xml')`).
Scenarios present: Reference, GCAM_SSP1/2/3/4/5, SSP1_1p9, SSP1_2p6, SSP2_3p7, SSP2_4p5_os,
SSP2_4p5_tol15, SSP4_6p0. Key queries: `aluminum production by region`, `CO2 emissions by sector
(excluding resource production)` (alumina = refining direct), `aluminum inputs by tech`.

## Revised critical path (2026-09-02)
1. **Extraction pipeline:** per GCAM scenario pull demand (production), grid intensity, and build
   the GCAM budget (decision 10). Read-only; do first, show numbers.
2. **[DONE 2026-09-02]** Interim ambition ladder × CCS ran — 16 cells (4 SSP-RCP × 4 CCS), all
   solved, parallel via `scenarios/run_gcam_ladder.py` (<10 min). GCAM demand (regional-share
   preserved), grid (`patch_grid_gcam.py`), budget (2025-anchored, spin-up left MPP-shipped).
   Pipeline: `pipeline/gcam_extract.py` + `gcam_cache/`. Results in `scenarios/runs/<scen>_<ccs>/`.
   NEXT: analysis — each cell's cumulative smelting emissions vs its GCAM budget = the
   asset-resolution gap. Stand-in GCAM runs, so this validates method, not findings.
3. **[DONE 2026-09-02]** Notebooks retrofitted to the ambition×CCS ladder. `common.py` rewired
   (naming convention in its header: ambition=SSP-RCP tag `SSP1_1p9`/display `SSP1-1.9`, CCS
   none/low/high/unlimited, cell id `<amb>_<ccs>`; `GRIDS`→`AMBITION` aliases; `budget()` now
   per-scenario). RUNS OK: analysis/01,03; plots/01,02,03,05 (7 figures in `scenarios/figures/`).
   BLOCKED: plots/04 + full-boundary intensity — refinery not run on GCAM demand (smelter-only
   ladder). SKIPPED: analysis/02 (archival switch-table evidence). Old IAM runs still in `runs/`.
   NEXT options: (a) run a refinery cell on GCAM demand to unblock 04; (b) run GCAM SSP2-1.9/2.6
   for a clean single-SSP axis; (c) read the gap results.
3. **Run GCAM SSP2-1.9 & SSP2-2.6** for a clean single-SSP axis; re-run those rungs.
4. O4 / O4b (unchanged from 08-30).
5. Draft proposal in parallel.

---

## Session decisions & findings — 2026-09-08 (refinery re-run on GCAM demand; plots/04 unblocked)

### 17. RETRACTION — "refining is inert to both levers" (D11/O7) is WRONG; refining is grid-exposed
The refinery was never grid-exposed only because MPP **ships refinery scope-2 electricity as zero**
for every electrified technology bar one placeholder (`CST-Fossil-Boiler + Elec-Calciner`, ~0.887).
Once scope-2 electricity is populated, an electric/MVR boiler's grid emissions become visible and
refining responds to the grid — i.e. to the ambition scenario in this design. So refining is NOT
inert; it just had its grid channel shipped empty. This retracts the D11/O7 inertness claim and the
old plots/04 "one canonical run" framing. (Handoff from a parallel CCS×SSP/RCP agent confirmed the
same two defects; both are MPP's model, grid-agnostic, so they ported unchanged.)

### 18. Two refinery defects fixed (both grid-agnostic; new scripts written to our conventions)
- **Fix 1 — stranded fossil-boiler tail** (`scenarios/patch_refining_switches.py`). MPP's refinery
  switch table routes every unabated fossil boiler to a clean end-state ONLY through a
  transition-class intermediate; the 2040 moratorium bans that first hop, so a plant still on an
  initial fossil boiler at 2040 strands (only the two CST end-states are moratorium-proof and they
  can't carry the load). The refinery twin of the smelter's frozen inert-anode power source
  (decision 15 / Section 20). Fix: add a DIRECT `brownfield_renovation` from each of the 6 unabated
  origins `{Coal,Gas,Oil}-Boiler + {Gas,Oil}-Calciner` to each of the 6 real end-states
  `{Elec,H2,MVR-Fossil}-Boiler + {Elec,H2}-Calciner`, economics templated from the destination's own
  rows. **VERIFIED pre-fix in our model:** unabated fossil freezes ~160.7 Mt 2030→2045 and refining
  breaks budget +6.6 (2045) / +11.4 (2050) Mt CO2/yr. Post-fix roughly doubles post-2040 conversion.
- **Fix 2 — refinery scope-2 electricity** (`scenarios/patch_refining_scope2.py`). (a) reconstruct
  the 10 `inputs_outputs.csv` electricity rows MPP omits (boiler/calciner cross-combos): electricity
  is additive, calciner term = `Gas-Boiler + <calciner>`, boiler term = median over present pairs of
  (value − calciner term), clip ≥0 — verified exact (Coal/Oil-Boiler+Elec = 0.8724, MVR+Gas =
  0.5842). (b) scope-2 = electricity × grid intensity, grid read off the **smelter** `Inert Anode +
  Grid` (co2_scope2/electricity) of the SAME copy, so it inherits that copy's GCAM grid — no grid arg.
  Boundary toggle: counted writes it, free zeroes it. Prereq: `apply_gcam_grid` on the smelter side first.

### 19. Refinery runs: 2×4 (scope-2 boundary × ambition), 8 solves, own GCAM refining budget
`scenarios/run_refinery_ladder.py` clones per ambition → GCAM grid + alumina demand (GCAM aluminium
× 1.935 on MPP alumina regional shares) + **GCAM refining budget** + Fix 1 + reconstructed
electricity, then solves twice (counted / free). Results in `runs/<amb>_refinery_{counted,free}/`.
CCS does NOT touch refining (confirmed: `strip_power_ccs_switches` edits only the smelter `def/`
table), so refining is indexed by ambition only. **New pipeline piece:** `gcam_extract.refining_budget`
= GCAM's own `alumina`-sector direct CO2 (MTC→Gt), cached as `<tag>_refining_budget.csv`.

### 20. FINDING (method-level, on stand-in runs): the scope-2 boundary reshapes TECHNOLOGY, not the TOTAL
Counting refinery scope-2 barely moves cumulative refining emissions (e.g. SSP2-3.7 counted 4.034 vs
free 4.024 Gt) because the model **dodges the electricity cost by going hydrogen-led** rather than
paying for it. So the boundary bites on the digester MIX (counted → H2-led, Electric ≈ 0; free →
grid-exposed Electric + more MVR), not on the emissions total — the honest way to show it is the
technology panels, done in plots/04. NB a large unabated-fossil tail persists (~150 Mt/2050, ~67%)
because GCAM alumina demand (~234 Mt) is ~2× MPP's fleet and the budget pressure is soft — a realism
caveat (same family as the smelter O5 rate-limit TODO), NOT stranding (Fix 1 confirmed working).

### DONE 2026-09-08 (notebooks + common.py)
- `common.py`: retired the single `REFINERY_REF` resolution; added `refinery_run(scenario, boundary)`,
  `REFINERY_BOUNDARIES`/labels, a `boundary=` arg threaded through `interface/emissions/production/
  production_by_technology/budget`, and `intensity_split(scenario, boundary)` now splits refinery into
  process (scope-1) and electricity (scope-2). Default boundary = counted (S1+S2).
- `plots/04_alumina_refining.ipynb`: full rewrite to the 2×4 boundary×ambition matrix (annual
  emissions vs GCAM refining budget + digester technology). Executed; figures regenerated.
- `plots/03_emissions_intensity.ipynb`: added a full-boundary (smelter+refining) section showing
  BOTH boundaries (counted stack vs free total) → `emissions_intensity_full_boundary`. Executed.
- `analysis/01`: corrected the three stale "refining inert / not re-run" notes (smelter tables unchanged).
- OLD `runs/REFINERY_REF` (MPP-flat demand) is superseded and no longer referenced; left on disk.
- STILL PENDING: MODEL_REFERENCE.md Section on refinery inertness (and CLAUDE.md's "Refining has no
  grid exposure" line) not yet edited — retracted here; update when next touching those docs.
