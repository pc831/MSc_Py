# Thesis experimental-design choices

Study-design decisions for the aluminium grid × CCS thesis. Distinct from
`pathway_derivation_choices.md`, which logs the earlier published-data intensity pathway.
Each decision records the rejected alternative and why. Started 2026-08-27.

Working question (current framing): at a fixed very-low (VL) emissions target, how do the
grid decarbonisation pathway (varied across IAMs) and the constraint on captive-power CCS
deployment shape the least-cost electricity sourcing of primary aluminium smelting — and where
do those choices make the sector budget infeasible or force an outsized claim on shared CCS.

---

## Decided

### D1. Two-model division of labour: MPP asset-level, GCAM boundary conditions
MPP Shared Industry Solver provides the asset-level anode × power-source resolution and the
least-cost switching. GCAM provides the consistent boundary conditions MPP lacks: regional
aluminium demand, the sector carbon budget, and the economy-wide + aluminium CCS baseline.
**Rejected:** single-model. GCAM alone is a logit fuel-share model with no asset stock, no
anode/power pairs — it can't produce the sourcing detail that is the outcome variable. MPP
alone can't supply a VL-consistent, aluminium-resolved budget/demand/CCS baseline.

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

### D4. CCS constraint is an independent lever, crossed with grid
Three regimes — none / rate-limited / unlimited captive-power CCS — crossed with the grid
levels at fixed VL. The constraint is an allocation/feasibility lever within a VL world, not a
proxy for ambition. **Rejected:** letting CCS deployment be purely endogenous to the target
(reintroduces the D2 circularity).

### D5. Aluminium demand: fixed, from GCAM-VL, held constant across all cells
One demand trajectory, directly resolved by GCAM, applied to every grid × CCS cell.
**Rejected:** vary demand per-IAM by industry-share downscaling. It confounds the grid signal
with SSP/socioeconomic demand differences (the wrong variable for this RQ), requires
fabrication for IAMs that don't resolve aluminium, and is strictly inferior to GCAM's directly
resolved demand.

### D6. Sector carbon budget: fixed, from GCAM-VL, mutually consistent with demand
The budget and demand come from the same GCAM-VL run so the "task" (make this much aluminium
within this budget) is internally consistent. **Rejected:** the earlier lean, a REMIND-marker
industry trajectory scaled by aluminium's share. Now that GCAM is confirmed to resolve
aluminium directly, the share-downscale is unnecessary and would be inconsistent with a GCAM
demand. **Trade accepted:** the budget is GCAM's, not the marker's — resolved-but-not-marker
beats marker-but-fabricated.

### D7. Retain the MPP model-correctness fixes as method
Keep the six added power-source switches (so a converted-anode plant can still change power
source) and the deepcopy fix that makes the CCS limit actually bind. **Rejected:** MPP
as-shipped. Its frozen-power-source switch table distorts the electricity-sourcing decision
that is the outcome variable, and without the deepcopy the CCS limit does not bind (the
rate-limited regime silently collapses into unlimited). The shipped model cannot answer the RQ.

### D8. Interim data now, official ScenarioMIP as a 1:1 drop-in — no VLLO config on the critical path
Two parallel data streams, each built on data in hand and swapped for the official
ScenarioMIP/VLLO version later without touching the pipeline:
- **Grid pathways (treatment):** AR6 database, category **C1** (1.5C, low/no overshoot) as the
  VLLO proxy, loaded per IAM via `pyam` from the IAMC-format database. The swap to
  AR7/ScenarioMIP VLLO is loading a new IamDataFrame and changing the scenario filter — so build
  the loader against the IAMC schema, not AR6 quirks.
- **Aluminium rig (demand/budget/CCS baseline):** a GCAM run already on disk (Speizer-1.5C or an
  SSP deep-mitigation run — every GCAM run resolves aluminium) stands in now; swap to the
  official GCAM VLLO run later.

Consequence: **no new GCAM VLLO configuration is on the critical path.** The whole MPP<->GCAM
pipeline (boundary reconciliation, region mapping, the adapter) is data-vintage-independent, so
it is built and finished on the interim data before the official runs arrive; the official data
is a drop-in at the end. **Rejected:** configuring a bespoke GCAM VLLO run up front (a stand-in
either way, and finicky to converge — the 1.5C runs on this machine fail repeatedly before
solving), and waiting on the ScenarioMIP database (which will not report aluminium regardless of
when it lands, so it never unblocks the rig). Caveats: AR6-C1 is a *proxy* for VLLO — the swap
changes the scenario definition, not just the data vintage; and the AR6-C1 grids need not be
discarded, they can stay as a grid-vintage robustness layer.

---

## Open, in priority order

### O1. Reconcile GCAM's aluminium emissions boundary with MPP's (existential, hardest task)
Data access is handled (D8); this harmonisation is the remaining existential task. GCAM's
aluminium accounting — what is in scope (captive power? process? anode? which fuels drive
emissions?) — must be matched to MPP's asset-level boundary, or the GCAM budget and the MPP
emissions are apples-to-oranges and every feasibility test is meaningless. It gates the whole
coupling. Solve it now on the interim GCAM run; it is vintage-independent. **If it can't be
reconciled**, fall back to an exogenous demand + a chosen budget, and the design shifts.

### O2. Grid-run selection rule per IAM (define once, reuse for AR7)
The AR6 database holds many C1 runs per model; fix one rule for which run represents each IAM's
grid — e.g. the Illustrative Mitigation Pathways (IMP-LD, IMP-Ren, IMP-SP), or "each model's
SSP-1.9 / headline 1.5C run", or "each model's median-C1". Whatever is chosen must be applied
identically to the AR7/VLLO set so the treatment is defined the same way across vintages. Also
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

### O8. Budget trajectory shape
Once GCAM is fixed as the budget source: use GCAM's aluminium emissions path directly, or
reshape to a smooth annual trajectory / cumulative cap. Implementation detail, decide after O1.
