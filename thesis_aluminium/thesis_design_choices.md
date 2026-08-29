# Thesis experimental-design choices

Study-design decisions for the aluminium grid × CCS thesis. Distinct from
`pathway_derivation_choices.md`, which logs the earlier published-data intensity pathway.
Each decision records the rejected alternative and why. Started 2026-08-27.

Working question (current framing): at a fixed very-low (VL) emissions target, how do the
grid decarbonisation pathway (varied across IAMs) and the constraint on captive-power CCS
deployment shape the least-cost electricity sourcing of primary aluminium smelting — and where
do those choices make the sector budget infeasible or force an outsized claim on shared CCS.

**Terminology (from the ScenarioMIP-CMIP7 paper, van Vuuren et al.):** **VL** (Very Low; formerly
VLLO) is the most ambitious CMIP7 scenario. Warming *overshoots* 1.5°C — peaks above it and
returns below by 2100 — with the overshoot "as low as can still be plausibly achieved" and
limited CDR. It is an overshoot pathway; "limited overshoot" is the magnitude, not the absence of
one. **LN** (Low-to-Negative; formerly VLHO) tolerates "more substantial overshoot" with much
higher CDR. The design premise is explicit — "some overshoot of the 1.5°C seems unavoidable" — so
**no-overshoot 1.5°C (AR6 C1-type) is excluded by design; there is no no-overshoot analogue in
CMIP7.** Full set: H, HL, M, ML, L, LN, VL.

Two consequences: (1) the interim **AR6 C1 proxy is broader than VL** — C1 is "no *or* limited
overshoot," so it includes no-overshoot runs VL excludes; fine for the grid, not an exact scenario
match. (2) the **VL budget shape reflects limited overshoot** — less front-loaded than a
no-overshoot pathway, leaning on later reductions/CDR — which f(t) should mirror once official VL
data arrives, not a steep early decline.

**GCAM aluminium structure (verified 2026-08-27):** two sectors — `aluminum` (smelting) takes
alumina feedstock + grid electricity only; `alumina` (refining) takes coal/gas/oil/biomass, each
with a latent CCS technology. Primary only, no secondary. No captive power, no anode process CO2,
no PFCs. In the 1.5C run GCAM deploys no CCS in aluminium at all. So GCAM's usable aluminium
output is production (demand) and smelting electricity intensity; its emissions and CCS are not
usable for the budget.

---

## Decided

### D1. Two-model division of labour: MPP asset-level + factors, GCAM demand + electricity
MPP provides the asset-level anode × power-source resolution, the least-cost switching, and the
emission factors themselves — anode process CO2 (~2 t/t carbon anode, ~0.06 inert), power
intensity, PFCs — all calibrated to real data (IAI, IEA, anode stoichiometry). GCAM provides
regional primary-aluminium production (demand) and the smelting electricity intensity. GCAM's
aluminium emissions and CCS are not used (see the structure note above): smelting is
electricity-only in GCAM, so its aluminium emissions are grid-driven and incomplete.
**Rejected:** single-model. GCAM's logit aluminium sector has no asset stock, no anode/power
pairs, and no aluminium-specific abatement, so it can't produce the sourcing detail that is the
outcome variable; MPP alone has no VL-consistent regional demand.

### D2. Fixed ambition at VL — ambition is not an axis
The scenario matrix holds the climate target fixed at VL and varies grid × CCS around it.
**Rejected:** varying ambition (M / L / VL) as a factor. Grid pace, the budget, and CCS demand
all co-move with ambition, so crossing ambition with CCS is near-tautological ("VL leans on CCS
more than M" is not a finding). Fixing ambition is what makes the CCS and grid effects
non-circular.

### D3. Grid pathway is the primary treatment, varied by IAM VL run
Treatment levels are each IAM's VL grid intensity trajectory — {GCAM-VL, REMIND-VL,
MESSAGEix-VL, …}. REMIND is included as the recognised VL marker. Only the regional
power-sector CO2/MWh is taken from each IAM, so IAMs that do not resolve aluminium still
contribute a grid level.
**Justification:** the sector is empirically grid-sensitive — swapping MPP→SBTi grid moved
cumulative emissions ~1 Gt (~9% of budget) and shifted the 2050 tech mix, so even a modest
grid difference produces a visible response. **Rejected:** a single grid, or parametric-only
grid variants — loses the real-pathway credibility and the cross-model spread as a result.
**Data (interim):** AR6 database, ENGAGE `EN_NPi2020_400f` (400 GtCO2, 1.5C low overshoot), R10.
Gross intensity — biomass-CCS added back to the net electricity CO2, since a smelter is not the
beneficiary of economy-wide BECCS removals. Five IAM grids: REMIND, MESSAGEix, AIM, COFFEE,
WITCH (GEM-E3 dropped — no BECCS variable). Loader `pipeline/grid_intensity.py`, parameterised
on (file, scenario) for the AR7 swap. Verified: China 2020 grid ~0.53–0.71 t/MWh (matches
reality), 2030 spread ~14x across models — the model-structural variation the treatment uses.
**Application (generalised patch_grid):** rescale MPP scope-2 (grid electricity) region r, year t:
`scale(r,t) = IAM_intensity(r,t) / MPP_implied_intensity(r,t)`, `co2_scope2 ← co2_scope2 ×
scale`. MPP_implied_intensity is read from the `Inert Anode + Grid` technology (scope-2 ÷
electricity). Scope-1 (anode, captive power) is untouched, so the grid acts on the grid-vs-captive
margin. The source of IAM_intensity swaps from the SBTi workbook to `grid_intensity.py`.

### D4. CCS constraint: four regimes, the two limits from empirical FGD deployment rates
Captive-power CCS is an independent lever crossed with the grid, at fixed VL — a real-world
availability question, not a proxy for ambition. Four regimes:

- **none** — no captive-power CCS.
- **lowLimitCCS** — capture penetration of the captive fossil fleet follows the global FGD
  diffusion pace: 10% → 90% of the fleet over ~26 years (van Ewijk & McDowall 2020, Nat Comms,
  global logistic fit for capacity, R²=0.93). The realistic worldwide rate; it folds in the lag
  as capture spreads country by country rather than everywhere at once.
- **highLimitCCS** — penetration follows the fastest observed national retrofit: Germany, 10% →
  79% of the coal fleet in ~4 years (same paper). The technical ceiling for regulation-driven
  end-of-pipe retrofit when one government forces it. Most permissive empirical bound.
- **unlimited** — least-cost, no cap.

Mechanism: both limits are a logistic penetration curve p(t) on the captive fossil fleet, so the
annual capture allowance = p(t) × (fleet capturable CO2). This replaces the WEO-derived rate in
`patch_ccs_limit.capture_penetration()`; everything downstream (storage constraint, the deepcopy
fix) is unchanged.

    p(t) = logistic from 10% at t0 to {90% over 26 yr (low) | 79% over ~4 yr (high)}

**Why FGD, not IEA-WEO or a within-model ramp:** FGD is the direct historical analogue for
end-of-pipe capture; van Ewijk gives both a national ceiling and a global realistic pace from
peer-reviewed data. It is more defensible than the SBTi WEO ratio (external, power-sector) and it
needs **no new external data** — the parameters are in the paper. Also ties the work to the
active CCS-feasibility literature (see also Kazlou, Cherp & Jewell 2024, NCC).
**Data implications:** need the captive fossil fleet's capturable CO2 (already computed by
`patch_ccs_limit` from the reference CCS run) and one chosen anchor year t0 (the 10% start).
**Open (O4):** van Ewijk finds retrofit diffuses fast but new-build slower — supports restricting
fossil+CCS to retrofit only.
**Rejected:** the SBTi IEA-WEO fossil:fossil-CCS ratio (external, inconsistent with an IAM-grounded
design); an arbitrary within-model ramp rate; GCAM's aluminium CCS (grid-only / not deployed).

### D5. Aluminium demand: fixed, from GCAM-VL, held constant across all cells
One demand trajectory, directly resolved by GCAM, applied to every grid × CCS cell.
**Rejected:** vary demand per-IAM by industry-share downscaling. It confounds the grid signal
with SSP/socioeconomic demand differences (the wrong variable for this RQ), requires
fabrication for IAMs that don't resolve aluminium, and is strictly inferior to GCAM's directly
resolved demand.
**Extraction:** GCAM `aluminum` sector output = primary aluminium production, by region and model
year (5-yr, interpolable). Convert to Mt; map GCAM's 32 regions onto MPP's 16, splitting GCAM's
single China across MPP's six China regions by MPP's existing regional shares.
**PoC shortcut:** use GCAM's *global* production trajectory scaled onto MPP's existing regional
distribution — this uses GCAM demand without the full re-regionalisation, refined to full
regional GCAM later. (Interim GCAM run: SSP1-1.9 stand-in.)

### D6. Sector carbon budget: production × present total intensity × external VL decline
The smelting budget is constructed, not lifted:

    budget(t) = GCAM_production(t) × present_total_intensity × f(t)

- **present_total_intensity** is today's smelting intensity on the full boundary — anode + power
  — from MPP's calibrated factors (equivalently, observed IAI emissions per tonne).
- **f(t)** is the reduction fraction (relative decline shape only — the absolute size is set by
  aluminium's own present intensity × production, so f never allocates another sector's budget to
  aluminium). It runs from 1 today toward a near-zero *positive* endpoint (~inert anode + clean
  grid) by 2050. Its reference class is **industry** (or aluminium's own share of a sector/global
  budget) — **not economy-wide**, which reflects power collapsing to zero and BECCS going
  net-negative, neither of which fits a hard-to-abate sector. It is external to GCAM's aluminium
  module, which holds no aluminium-specific ambition (its emissions fall only as fast as the grid,
  the treatment variable).
  **Interim (PoC):** f from the SSP1-1.9 stand-in run's **industry** CO2 reduction fraction (sum
  of industrial sectors), extracted 2026-08-28: f = 1.00 (2021) → 0.85 (2030) → 0.50 (2040) →
  0.18 (2050); flat to 2025 then steep (the limited-overshoot profile). **Use industry, not
  economy-wide** — SSP1-1.9 economy-wide CO2 goes net-negative by 2050 (−0.25 Gt), which is
  impossible for aluminium (its floor is inert anode + clean grid, a small positive). Swap to the
  VL run's industry decline later. **Caveat to test:** industry-average f only reaches 0.18 and
  may be too loose for aluminium (harder to abate than the cement/steel/chemicals that carry the
  industry CCS); if the feasibility signal is weak, escalate to a sector-specific or
  floor-anchored f (O8).
- f multiplies the **total** intensity, not the grid term with the anode held. If only the grid
  term declines, the target forces captive-fossil→grid but never the anode or the last
  grid-carbon-anode plants — a half-target. Multiplying the total pulls the endpoint down to
  inert-anode + clean-grid and forces both switches.
- Functionally a reduction target. Linear f is a defensible default; the VL scenario's decline
  shape is a sensitivity, since the pace interacts with grid pace to set feasibility timing. If
  the ambition is a cumulative VL allocation, scale the path to hit that cumulative.

**Test-run implementation (2026-08-28, in `run_poc.py::write_linear_budget`):** for the first
matrix the budget is `base × linear f`, where `base` = MPP's shipped 2020 smelting emissions
(~0.78 Gt, anode-inclusive) and `f` declines linearly from 1.00 (2020) to 0.05 (2050). Because f
multiplies the total, the anode component scales linearly toward ~zero by 2050, forcing the anode
switch — the construction agreed. Demand is MPP's own flat trajectory for the test runs (see O10).
Swap `base×f` for `GCAM_production × present_total_intensity × industry_f` in the next phase.

**Rejected:** (a) GCAM's aluminium emissions as the budget — grid-only ambition, redundant with
the grid treatment, and missing the anode; (b) MPP's shipped `carbon_budget.csv` — MPP's own
scenario output, so targeting MPP with it is circular; (c) production × (carbon anode + grid)
with the anode held constant — half-target, forces only captive→grid. See D9 and D10.

### D7. Retain the MPP model-correctness fixes as method
Keep the six added power-source switches (so a converted-anode plant can still change power
source) and the deepcopy fix that makes the CCS limit actually bind. **Rejected:** MPP
as-shipped. Its frozen-power-source switch table distorts the electricity-sourcing decision
that is the outcome variable, and without the deepcopy the CCS limit does not bind (the
rate-limited regime silently collapses into unlimited). The shipped model cannot answer the RQ.

### D8. Interim data now, official ScenarioMIP as a 1:1 drop-in — no VL config on the critical path
Two parallel data streams, each built on data in hand and swapped for the official
ScenarioMIP/VL version later without touching the pipeline:
- **Grid pathways (treatment):** AR6 database, category **C1** (1.5C, low/no overshoot) as the
  VL proxy, loaded per IAM via `pyam` from the IAMC-format database. The swap to
  AR7/ScenarioMIP VL is loading a new IamDataFrame and changing the scenario filter — so build
  the loader against the IAMC schema, not AR6 quirks.
- **Aluminium rig (demand/budget/CCS baseline):** a GCAM run already on disk (Speizer-1.5C or an
  SSP deep-mitigation run — every GCAM run resolves aluminium) stands in now; swap to the
  official GCAM VL run later.

Consequence: **no new GCAM VL configuration is on the critical path.** The whole MPP<->GCAM
pipeline (boundary reconciliation, region mapping, the adapter) is data-vintage-independent, so
it is built and finished on the interim data before the official runs arrive; the official data
is a drop-in at the end. **Rejected:** configuring a bespoke GCAM VL run up front (a stand-in
either way, and finicky to converge — the 1.5C runs on this machine fail repeatedly before
solving), and waiting on the ScenarioMIP database (which will not report aluminium regardless of
when it lands, so it never unblocks the rig). Caveats: AR6-C1 is a *proxy* for VL — the swap
changes the scenario definition, not just the data vintage; and the AR6-C1 grids need not be
discarded, they can stay as a grid-vintage robustness layer.

### D9. Use MPP's calibrated inputs, never MPP's outputs
MPP's emission factors, switch table, and asset stock are inputs calibrated to real data (IAI,
IEA, anode stoichiometry) — using them is not circular. MPP's shipped budget and its scenario
results are outputs; feeding either back as our target or input would be circular, and is not
done. The budget's base level can be cross-checked against observed IAI emissions; a mismatch
signals a reconciliation error rather than a datum to adopt.

### D10. Smelting budget is on the total, anode-inclusive boundary
Smelting scope-1 is dominated by the carbon-anode process CO2 (~2 t/t, versus ~0.06 for inert),
and anode switching is the solver's largest lever. The budget must count anode emissions, or the
anode switches would cut emissions the target never accounted for. MPP's own emissions accounting
already includes anode, so a total-boundary budget compares like-for-like. Smelting (`def`) and
refining (`def_refineries`) carry separate budgets.

### D11. Refining budget: same construction, minor for the findings
Alumina demand comes from GCAM (its `alumina` sector, or aluminium × 1.935) and the refining
budget is built the same way — alumina production × present refining intensity × the same f(t).
Refining is inert to the grid and CCS levers in MPP (identical across the twelve runs), so this
budget ensures accounting completeness rather than driving results.

---

## Proof-of-concept test runs (set up 2026-08-28, not yet run)

Purpose: confirm the method works before choosing this project for the thesis. Two things to
verify — (1) does swapping the IAM grid clearly move the 2050 technology mix and cumulative
emissions; (2) is there a feasibility gradient (some grid × CCS cells miss the budget, some meet
it), read as gap-to-budget, not pass/fail.

**Feasibility is post-hoc, not a solver failure (verified 2026-08-28).** MPP's LC brownfield loop
switches assets toward the annual emissions limit and stops early once met; if it can't meet the
limit it returns the over-limit stack rather than erroring. Governing limits:
`ANNUAL_RENOVATION_SHARE = 0.2` (≤20% of stock renovated/yr) and `INVESTMENT_CYCLE = 10` yr (one
renovation per plant per cycle); `YEAR_2050_EMISSIONS_CONSTRAINT = 2051` (no separate hard 2050
gate). So an infeasible cell yields a *measured* result: gap to budget per year and cumulative,
the 2050 mix and transition sequence it managed, and what it stranded on carbon anode / captive
fossil that the 20%/yr cap or a missing switch route couldn't move. That renovation-rate inertia
is the MPP-only signal GCAM's smooth logit cannot produce — it carries the contribution.

**Matrix:** 4 IAM grids (REMIND, MESSAGEix, AIM, WITCH — REMIND/WITCH are the fast/slow extremes)
× 4 CCS regimes (unlimited, none, low, high), smelter side. 16 cells. Driver: `run_poc.py`.

**Per-cell recipe:** clone `model_clean` → `patch_fulltt.py` (full 132-switch table + the six
unlock switches) → `patch_grid_iam.py <model> "<IAM>"` (grid treatment) → for the three limited
CCS cells, `patch_ccs_limit.py <model> {none|low|high} <reference>` where reference is that grid's
own `unlimited` run (so each grid sizes its own captive fleet; unlimited runs first) →
`write_linear_budget` → `run.py <scenario> lc smelter <model>`.

**New/changed code (all committed-pending):**
- `pipeline/grid_intensity.py` — IAM grid intensity loader (done earlier).
- `scenarios/patch_grid_iam.py` — generalised grid patch; rescales scope-2 by IAM/MPP ratio.
  Tested: REMIND grid moves smelter scope-2 5828.8 → 3759.4.
- `scenarios/patch_ccs_limit.py` — `capture_penetration()` replaced: WEO rate → FGD logistic;
  now takes argv `LIMIT` (none|low|high) and an optional reference-run path (argv 3). FGD_T0=2025,
  FGD_K from van Ewijk (low 10→90% over 26 yr, high 10→79% over 4 yr).
- `scenarios/run_poc.py` — the matrix driver + linear budget writer.

**Interim data used:** MPP flat demand; MPP 2020 emissions as budget base; AR6 `EN_NPi2020_400f`
grids; SSP1-1.9 industry f (recorded, but the test uses a simple linear f for now). Swaps for the
final version: GCAM demand, GCAM/VL industry f, official VL grids.

---

## Open, in priority order

### O1. [RESOLVED 2026-08-27] GCAM boundary reconciliation
Resolved by inspecting the GCAM run. GCAM smelting (`aluminum`) is electricity-only — no captive
power, no anode CO2, no PFCs — so its smelting emissions are recoverable by proxy (electricity ×
grid), and MPP supplies the anode/power factors GCAM lacks. GCAM refining (`alumina`) is fuel
combustion with CCS latent but unused. The reconciliation (now D1, D6, D9, D10): take demand and
electricity intensity from GCAM, emission factors from MPP, and the budget's decline from an
external VL source. No apples-to-oranges budget remains.

### O2. Grid-run selection rule per IAM (define once, reuse for AR7)
The AR6 database holds many C1 runs per model; fix one rule for which run represents each IAM's
grid — e.g. the Illustrative Mitigation Pathways (IMP-LD, IMP-Ren, IMP-SP), or "each model's
SSP-1.9 / headline 1.5C run", or "each model's median-C1". Whatever is chosen must be applied
identically to the AR7/VL set so the treatment is defined the same way across vintages. Also
fix the two grid variables read — power-sector CO2 (`Emissions|CO2|Energy|Supply|Electricity`)
and generation (`Secondary Energy|Electricity`) — and validate them on load.

### O3. Grid → MPP-region mapping, especially the China split (determines the crux)
IAM grid intensity arrives at R5/R10 or native regions; MPP has 16 regions with China split
several ways. China is ~60% of capacity and the dirtiest captive power, so if the IAM grid is
too coarse the China captive-vs-grid signal — the heart of the finding — may wash out. Check
the delivered resolution early.

### O4. Fossil + CCS: retrofit-only or greenfield-allowed?
Whether to structurally forbid new-build captive coal/gas+CCS and allow it only as a retrofit.
Strong prior that greenfield fossil+CCS to smelt aluminium in the 2040s is not credible;
allowing it materially inflates the CCS-claim result. Implementable as a switch-type
restriction. Decide before the CCS regimes are finalised.

### O4b. [OPEN, verified 2026-08-29] Greenfield capture is not fully rate-limited
Two model defects were found and fixed to make the captive-power capture cap bind:
- **The deepcopy fix (the real one).** `aluminium/solver/brownfield.py` built its tentative
  stack as `deepcopy(new_stack)` but passed the *live* `asset_to_update` to `update_asset`,
  which mutates the asset in place — so a capture switch was applied to `new_stack` before any
  constraint check, and the check's later rejection did nothing. Ammonia/cement pass
  `deepcopy(asset_to_update)`; aluminium did not. This was documented as "patched" but no patch
  function did it (a manual edit lost from the reproducible path). Now a tracked step
  (`deepcopy_tentative_brownfield_asset`) in `patch_ccs_limit.py`. This is what makes `none`
  reach zero captive-power capture and gives the clean `none<low<high<unlimited` ordering.
- **Change #7 (`keep_storage_constraint_for_ccs`)** keeps `co2_storage_constraint` for `+CCS`
  destinations in `get_constraints_to_apply` (it was stripped unless the name contained
  "storage", ammonia naming). On the SBTi machine this is *empirically inert* (greenfield
  capture unchanged, high 12.0→11.4 Mt). On this machine it has a *small* effect: reverting it
  raises `REMIND_none` greenfield capture 0.0→0.6 Mt. So it catches the marginal greenfield
  addition when the allowance is zero, but does **not** rate-limit greenfield under a positive
  allowance — `REMIND_high` still shows 10.35 Mt greenfield capture with #7 applied.
- **Open problem:** total power capture is not held to the nuclear/FGD rate through greenfield.
  The cumulative *totals* still order correctly (none 0 < low < high < unlimited) and `none` is
  clean, so the matrix result stands, but the greenfield path leaks under positive allowances.
  Leading hypothesis (from the SBTi agent): the `annual_addition` check compares captured on the
  tentative stack at `year+1` vs the committed stack at `year`, and a greenfield plant
  commissioned at `year+1` isn't counted in that lookup, so its addition never registers. Also
  the `year+1` read at 2050 hits 2051 (no data → 0), a separate final-year leak. Both untested.
  Ties directly to O4 (retrofit-only would sidestep greenfield capture entirely).

### O5. Symmetric deployment-rate limits on clean captive (hydro / SMR)?
If CCS is rate-limited but hydro and SMR can appear instantly, the "less-ambitious grid → more
hydro/SMR" finding is partly an artefact of unconstrained clean buildout (SMR especially cannot
scale by 2035). A buildout-rate cap on clean captive is needed for a fair comparison. Threat to
validity if skipped.

### O6. Technology cost and learning: MPP-native or updated from VL scenarios?
MPP's shipped cost/learning assumptions are defensible as a baseline but may be dated. Updating
them changes which switches are least-cost and could move results. Baseline = MPP native;
sensitivity = updated. Medium priority.

### O7. Scope: smelting only, or smelting + refining?
Refining is inert to both levers in the model — verified identical across all twelve runs (no
grid exposure, no capture route). Lean: centre the analysis on smelting and carry refining only
as a fixed offset in the sector budget, stated explicitly. Mostly a framing/completeness call.

### O10. Demand: multiple scenarios needed (MPP-flat vs GCAM-growth)
MPP and GCAM disagree fundamentally on primary aluminium demand: MPP "1.5deg" holds primary
roughly flat (~65 Mt 2020 → ~68 Mt 2050, assuming recycling absorbs growth); GCAM SSP1-1.9 has
primary nearly double (56.5 → 121.1 Mt, GDP-driven, no recycling cap). GCAM/MPP = 0.87 (2020) →
1.78 (2050); GCAM also undershoots the observed 2020 base (~65 Mt) by ~13%. This is a first-order
driver — under an absolute budget, MPP-flat needs intensity to ~18% of today, GCAM-doubling to
~8%. So the thesis needs demand as a sensitivity axis (at least MPP-flat and GCAM-growth-rebased
to the observed base), not a single choice. **Test runs (now):** use MPP's own shipped budget and
demand as a self-consistent, known-to-solve baseline, varying only grid × CCS; swap in
GCAM demand + the constructed budget in the next phase.

### O9. [MUST RETURN] Native GCAM region conversion for demand
The PoC uses GCAM's global production trajectory scaled onto MPP's existing regional shares (D5
shortcut). Come back and do the full GCAM 32 → MPP 16 region conversion — including splitting
GCAM's single China region across MPP's six China regions by MPP's regional shares — so demand is
natively regional rather than MPP-shares-scaled. Affects the China captive-vs-grid signal (O3).

### O8. [mostly settled] Budget decline shape — linear vs VL scenario shape
Construction is decided (D6). Remaining choice is the shape of f(t): linear default, or the VL
scenario's own decline curve. Run both as a sensitivity, since the pace interacts with grid pace
to set feasibility timing. If f is anchored to a cumulative VL allocation, scale the path to hit
the cumulative. Also open: whether f comes from the global VL budget or GCAM's industry decline,
and whether aluminium takes the industry-average pace or a sector-specific one (normative).
