# Idea B — running strategic context

Second candidate MSc thesis project, **selected as the thesis direction** (2026-08-30).
Durable memory of strategic conclusions — read to restore context after a `/clear`; append dated
decisions with the rejected alternative, matching Idea A's design-log style. Load THIS file when
working on Idea B. Sister idea: `thesis_aluminium/IDEA_A_running_context.md` (Idea A is the
aluminium bottom-up work; it is **sector one / method demonstration for B**, not a rival).

## Retrieval note
When working on Idea B, load this file, not Idea A's. Append dated decisions with the rejected
alternative. Ask before running any model.

---

## The idea

- **One-line framing:** Hard-to-abate sectors compete for a shared, regionally limited CO2
  storage budget — limited by both cumulative geological *stock* (Gidden 2025 regional caps) and
  annual injection *flow* (rate cap) — and we resolve, bottom-up and least-cost, who gets it,
  when, and whether CCS cost self-limits deployment below the geophysical limit or a policy cap
  is needed.
- **Working question:** Under an IAM very-low (VL) scenario, given each region's storage stock
  and injection-rate limits, how is scarce CO2 storage allocated across hard-to-abate sectors
  over time on a least-cost basis — and where does cost self-limit CCS below the geophysical
  ceiling versus where must storage be actively rationed by policy?
- **Origin:** Humphrey Adun's framing (Slack, 2026-08-29/30): "a credible allocation of limited
  CCS deployment across hard-to-abate sectors… how should sector-specific deployment rates be
  constrained by IAM outputs, infrastructure availability and competing demand for CO2 storage."
  Humphrey can attach GCAM/IIASA staff as collaborators.
- **Goals:** distinction thesis, definitely publishable; **target One Earth, reach Nature Climate
  Change**. (Idea A = target low-IF, reach One Earth.)

## Why B, relation to A, and the two-clocks decision (2026-08-30)

- **A is a subset of B.** Aluminium MPP work = sector one and the demonstrated method; in A the
  sector sets its own CCS limit and competes with nothing. B's novelty is the **shared** storage
  budget the sectors compete for — what A structurally cannot do.
- **Two clocks (key structural decision):** 12 months to the *thesis*; *publication after*. So
  the thesis is a **scoped B on interim/proxy VL data** (method + ≥2 sectors + Gidden regional
  limits + the allocation), complete and distinction-grade without official GCAM VL runs. The
  **reach paper after** swaps in official GCAM VL, adds sectors, brings IIASA/JGCRI coauthors.
  Aluminium is the bankable floor → even a thin result is a full thesis. The paper's failure mode
  (never gets written) is low here: work is job-aligned, Humphrey championing.
- **Ambition:** user wants to do as much of the full thing as possible, not an artificially small
  version. Aluminium took ~1 week — but that was marginal MPP work on a model already mapped; it
  did **not** include the new build (the LP, MACC extraction, storage-data harmonisation, GCAM
  integration), which is most of the thesis. **Scope multiplier is regions, not sectors** (each
  region needs its own stock cap, flow cap, demand, grid). **Strategy: build the machine once
  with 2 sectors in 1 region (China, where the constraint binds), end-to-end, then scale as far
  as time/data allow.** 2-sector version is a month-3/4 checkpoint, not a ceiling. Protect the
  final ~2–3 months for writing.
- **Rejected:** a single GCAM run or a small ensemble — that is GCAM sensitivity analysis, the
  crowded genre; adding runs doesn't leave it. (User's own point.)

## Target architecture — the coupling

- **The "ideal" (user's vision):** a full bottom-up coupling to GCAM's top-down that resolves CCS
  better at the **regional and asset level** — bottom-up sitting *inside* the top-down for the
  parts GCAM is worst at.
- **The move:** GCAM is the top-down backbone (regional demand + grid intensity + power/removal
  storage use). Bottom-up (MPP-style) refines the heavy-industry sectors GCAM represents crudely.
  **Carve the bottom-up sectors out of the GCAM backbone to avoid double-counting**, then slot in
  the asset-level version.
- **Two versions of the backbone:**
  - **Thesis version:** keep our **own LP** as backbone on proxy VL data; approximate the
    power/BECCS/DAC storage claim from GCAM defaults/literature; our LP allocates the residual
    regional storage across industry. Solo-tractable, proxy-safe, novelty explicit.
  - **Paper version (likely the strongest form):** **run GCAM itself under Gidden stock + flow
    regional caps** as a consistent, published-grade backbone (GCAM handles power/CDR elasticity
    through full equilibrium), then nest bottom-up industry inside. Needs modifying + re-running
    GCAM → depends on official VL run + GCAM-staff time; that is why it is the paper, not the
    thesis critical path.
  - **Middle path:** constrained GCAM supplies only the power/BECCS/DAC storage claim under the
    caps; compute **residual = Gidden cap − power/CDR use**; our LP allocates the residual across
    industry explicitly (keeps the novel industry competition ours, lets GCAM do what it's good
    at). User thinks the GCAM run is gettable → this is plausibly in reach.
- **Pivotal unknown to resolve with GCAM staff:** how hard is imposing the caps in GCAM? If
  tightening cumulative caps = editing the regional storage supply-curve **input files** to
  Gidden numbers (a data change) and a rate-limit mechanism already exists (toolset scan suggests
  it does), it's very feasible. If the flow constraint needs new code, bigger lift. **This single
  fact decides whether the constrained GCAM run is a thesis or a paper component.**

## Method — the allocation crux

Contribution is the **coupling**, not the optimiser (multiperiod source–sink MILPs and GCAM/US
studies already impose cumulative capacity + a separate annual injection-rate limit). Novelty =
fusing that with IAM-driven **bottom-up asset-level** sector demand, **simultaneous stock+flow**
regional caps, **intertemporal** depletion, and the **policy verdict** (self-limit vs cap).

**Decouple (architecture decision):**
1. **MPP as the data engine, not the solver.** Run each sector to produce marginal abatement cost
   curves — CCS quantity wanted and its cost as a function of storage available, per region per
   period, dependent on GCAM grid intensity over time. Aluminium's four CCS regimes
   (none/low/high/unlimited) are already this curve at four points — the template.
2. **A custom intertemporal LP (Pyomo/linopy) does the allocation.** Variables = CO2 stored per
   sector × region × period; objective = discounted total abatement cost; constraints =
   (a) per-region cumulative storage ≤ stock cap, (b) per-region annual injection ≤ rate cap,
   (c) demand/targets from GCAM. A single cumulative constraint captures depletion natively.
   ~50 lines, solver does the math, provably optimal, viva-defensible (more so than MPP's
   agent-based simulation). linopy suits pandas skills.
3. **Iterate for consistency** only if needed (capping a sector shifts its rest-of-pathway/bid).
   For 2 sectors, can start with a plain merit-order allocation (just sorting) and climb to the
   LP for the intertemporal optimum.

**Basis of competition (resolved 2026-08-30): avoided cost, NOT capture cost.**
- A sector's claim on a tonne of storage = (cost of its next-best **non-CCS** abatement) −
  (its own capture + transport cost). Storage goes to whoever saves the system most. "Cheapest
  capture wins" is the trap — a sector may have cheap capture but cheap alternatives (doesn't
  *need* storage). Cement's process CO2 is unavoidable → very high bid; power has cheap
  alternatives → low bid. Least-cost allocation naturally prioritises process emissions.
- **Mechanically = the shadow price on the storage constraint** (the LP dual). Sectors whose
  avoided cost exceeds the clearing price get storage; a merit order priced by the constraint.
  Maps to a carbon price + storage scarcity rent.
- **Intertemporally = a rising scarcity rent** (Hotelling-type): using a tonne now costs its
  future availability. Comes free from the dual on the cumulative constraint.
- **Grid coupling enters here:** grid intensity/cost sets the cost of the electricity-exposed
  *alternatives* (power, aluminium). Cleaner grid → their alternatives get cheaper → their
  storage bids fall → they cede storage to cement/chemicals. The grid pathway reorders the
  competition; that's the channel tying the whole grid thread in.
- **Resolved fork:** **positive least-cost as the spine** (one clean defensible rule); **normative
  rules as a contrast layer** (hard-to-abate-first, proportional-to-residual) to show where
  least-cost and "credible/fair" diverge = Humphrey's "credible allocation" question and the
  policy contribution. Positive spine, normative overlay.

**Stock vs flow:** stock = cumulative reservoir (Gidden); flow = annual injection ceiling. Which
binds depends on a region's stock-to-flow ratio → different sectoral winners by region (a finding
axis). Depletion makes competition intertemporal *and* cross-sectoral.

## Sector coverage — bottom-up vs top-down

- **MPP covers (bottom-up candidates):** steel, cement, aluminium, ammonia/chemicals.
- **MPP does NOT cover — often the *biggest* storage users in VL scenarios (must be at the
  table):** power+CCS, BECCS, DACCS, standalone blue hydrogen, refining/liquids, gas processing.
- **Principled hybrid (decision 2026-08-30):** the sectors MPP misses are exactly the ones IAMs
  model *well*; the sectors MPP covers are exactly where IAMs are *weakest*. So **bottom-up the
  industry; take power/BECCS/DAC/blue-H2 from GCAM** at IAM resolution. Coverage gap and
  value-add gap line up — a principled division, not a compromise.
- **Elastic, not fixed:** do **not** reuse GCAM's solved build rates (solved under GCAM's *loose*
  storage → wrong for the constrained world → freezing them assumes the answer). For elastic
  competition, take GCAM's **cost curves** (from its input data), not its quantity outputs, and
  let the model re-solve quantities under the tight caps. Every sector enters as a cost curve;
  the LP solves all quantities. This is *more* consistent than freezing GCAM quantities. Fixed
  service demands + grid + required net removals stay exogenous from GCAM; storage quantities
  flex. Caveat: this is a **partial-equilibrium** re-allocation (doesn't re-ripple through the
  energy system) — state as scope. (The paper-version constrained-GCAM run avoids this by letting
  GCAM re-equilibrate fully.)
- **DAC as the backstop bidder:** include even crudely (a declining cost number) — it sets the
  reservation price for storage and makes the shadow-price structure well-posed.
- **BECCS/DAC are removals, not services:** driver = the scenario's required net-negative;
  BECCS-vs-DAC compete to supply it cheapest, both drawing storage.

## GCAM ↔ MPP crosswalk (verified 2026-08-30)

GCAM: 32 regions; 9 detailed industry sectors — Iron&Steel, Chemicals, Aluminum, Cement,
N-Fertilizer, Other Industry (+ construction/mining/ag energy). CCS across power, hydrogen,
liquid fuels, fertilizer, cement, steel, gas processing, DAC (v5.4+; GCAM-CDR v1.0 GMD 2023 has
DACCS/BECCS/afforestation, CDR market, interregional CDR trade). Recursive-dynamic partial
equilibrium, 5-yr steps to 2100, tech choice by logit + cost. MPP: asset-level, brownfield/
greenfield switching, to 2050, ~16 regions (varies by sector).

| CCS use | GCAM | MPP | Layer | Mapping |
|---|---|---|---|---|
| Electricity + CCS (coal/gas/bio) | Explicit | — | Top-down | Clean by construction |
| Hydrogen + CCS (blue/bio) | Explicit | input only | Top-down | Clean; watch H2-as-feedstock double-count |
| Liquid fuels/refining + CCS (bioliquids) | Explicit | — | Top-down | Clean |
| DACCS | Explicit (v5.4+) | — | Top-down | Clean |
| Gas processing + CCS | Explicit | — | Top-down | Clean |
| **Cement + CCS** (calcination) | Physical, limestone+fuel CO2, CCS | Asset-level | Bottom-up | ✅ Clean — best match |
| **Iron & Steel + CCS** | Explicit | Asset-level | Bottom-up | ✅ Mostly clean; GCAM scrap/EAF is cost-logit not stock-driven (demand mismatch) |
| **Ammonia** | N-Fertilizer + part of Chemicals | Asset-level | Bottom-up | ⚠️ Partial — carve fertilizer cleanly, watch Chemicals boundary |
| **Aluminium** | Distinct sector but **electricity-only, NO process CCS** | Asset-level (built) | Bottom-up | ❗Poor — its CCS is captive power → GCAM *electricity* boundary; double-count risk |
| Other Industry (**32% of industry CO2**) | Aggregate, **excludes** the detailed sectors | — | Top-down | ✅ Clean residual — no overlap, stays top-down untouched |

**Verified corrections (2026-08-30):**
- **"Other Industry" EXCLUDES the detailed sectors** (docs: "the remaining industrial sectors…
  not covered by the nine explicitly detailed sectors"). It is glass/paper/food/ceramics/
  machinery etc. So carving steel/cement/etc. out of GCAM is well-defined and never touches Other
  Industry. Earlier "32% double-count hazard" framing was WRONG — it *de-risks* the coupling.
- **GCAM Aluminum has no process CCS** (electricity-driven only). Aluminium's only capture route
  (captive-power CCS in MPP) has no home in GCAM's aluminium sector — it lives at the electricity
  boundary. This is the one genuine boundary issue; captive power is behind-the-meter so may be
  genuinely additional to GCAM grid-power CCS — **confirm with GCAM staff.**
- **Cross-cutting mismatches:** regions (32 vs ~16, harmonise to a common grid; China/India/US/EU
  identifiable in both); time (MPP 2050 vs GCAM 2100 — bottom-up covers first half, post-2050
  from GCAM/extrapolation; depletion is a to-2100/2200 question); demand basis (GCAM aluminium
  demand wrong — no scrap; steel scrap cost-logit — reconcile, don't inherit blindly); system
  boundary (captive power, scope 1 vs 2 — cement cleanest, aluminium worst).
- **Strategic implication: lead the coupled work with CEMENT and STEEL (cleanest carve).**
  Aluminium — the built sector — is the *worst*-mapping for this architecture; it stays A's
  standalone floor and becomes a special case handled at the power boundary (or deferred to
  paper).

## Toolset decision (2026-08-30)

- **Chosen: custom intertemporal LP (Pyomo/linopy) fed by MPP-derived MACCs + GCAM boundary
  conditions.** Best-matched, defensible, time-realistic; salvages MPP work. The LP is trivial;
  the real work is credible grid-coupled MACCs + storage-data harmonisation.
- **Rejected — MPP as optimiser with external iteration:** manual fixed-point loop, no optimality
  guarantee, hard to defend. (User's own doubt; confirmed.)
- **Stretch only — MESSAGEix-Materials (IIASA):** strongest off-the-shelf, natively steel/cement/
  aluminium/petrochem + CCS, intertemporal LP, IIASA/Gidden's own stack (coauthor alignment) —
  but heavy learning curve (GAMS + MACRO calibration + baseline). Post-thesis extension only if
  IIASA mentorship materialises early. Double edge: the tool the likely-scooper would use.
- **Cite, don't rebuild — TIAM-Grantham** (Grant 2022 precedent; not solo-open).
- **Skip:** GCAM module edits for the *allocation* (C++/XML; simulation-not-optimisation), SimCCS
  (pipeline siting, wrong altitude), PyPSA-Eur-Sec (Europe/power-centric; our constraint = China).
  NB: this "skip GCAM edits" is about the allocation engine; a constrained-GCAM *run* for the
  paper backbone is a separate, plausible thing (see architecture).

## Data sourcing

- **Per-sector tech + cost + alternative costs (the MACCs):** from **MPP** (already have aluminium;
  steel/cement/ammonia native). Extract by differencing runs (the 4-regime sweep pattern).
- **Storage stock caps (regional, cumulative):** Gidden 2025, country-resolved, **Zenodo 15657543**
  (gridded rasters updated Jan 2026). Aggregate to the common region grid. Ready now.
- **Storage flow caps (annual injection rate):** NOT in Gidden — derive separately. Sources:
  Zhang/Jackson/Krevor 2024 *Nat. Commun.* regional rate trajectories (~16 Gt/yr max, 5–6
  feasible), or scale to historical oil & gas throughput (GCAM approach). A real design task.
- **GCAM boundary conditions (regional demand + grid intensity; power/BECCS/DAC cost curves):**
  from GCAM VL (official when available) or proxies now (AR6-C1/SSP, as in A). Grid-intensity
  loader already built in A. Extracting GCAM cost curves = reading its input data system — good
  task for the GCAM staff.
- **Supplementary sector cost data:** JRC 2024 bottom-up EU industrial capture; IEA/IEAGHG.

## Competition / positioning (scan 2026-08-30)

- **Novelty holds:** no published paper puts bottom-up asset-level sectors in intertemporal
  competition for a regional budget limited by *both* stock and flow, IAM-VL-driven, with the
  self-limit-vs-cap verdict. Pieces sit in separate camps (supply caps / IAM realism / engineering
  source–sink).
- **Must read before finalising related work** (novelty tested here):
  - **Zhang (Huizhong) et al. 2026, *Resources, Conservation & Recycling* 228:108785** — DOI
    10.1016/j.resconrec.2026.108785. Nearest neighbour (multi-sectoral source–sink allocation via
    Carbon Storage Composite Curves + Orthogonal Experimental Design); likely engineering, not
    IAM-driven, probably no regional stock cap + intertemporal + policy — **paywalled, confirm.**
  - **Grant et al. 2022, IJGGC 120:103766** — DOI 10.1016/j.ijggc.2022.103766. Standard to beat;
    confirm exactly which constraints (stock, flow, intertemporal, regional) it imposes.
- **Race risk = Gidden / IIASA / CGS-Maryland group** — owns the stock-cap concept, released
  gridded regional caps (Jan 2026), frames storage as needing "explicit priorities," Gidden
  co-develops MESSAGEix. One paper away. **Moat:** bottom-up asset resolution + simultaneous
  stock+flow + intertemporal cross-sector + explicit policy verdict. Lock framing fast.
- **Gap motivation to cite:** REMIND imposes only crude injection limits (~5–20 Gt/yr); MESSAGEix
  has essentially no dedicated storage constraint. Leading IAMs treat storage crudely.

## Open forks (remaining decisions)

- **Positive vs normative allocation** — resolved as positive spine + normative contrast, but
  confirm with Humphrey which normative rules to test.
- **Constrained-GCAM run: thesis or paper?** — decided by how hard imposing caps in GCAM is
  (ask GCAM staff). Default: paper; thesis uses own-LP + residual on proxies.
- **Which 2 starting sectors** — recommend **cement + steel** (cleanest carve). Aluminium special.
- **Flow-cap derivation** — Krevor 2024 vs O&G-throughput scaling.
- **How many sectors/regions in thesis vs paper** — decide ~month 4–5.
- **Aluminium captive-power / GCAM-electricity boundary** — how to avoid double-count.

## Reusable from Idea A

Grid-intensity loader / IAM grid pathways; MPP asset framework + CCS-limit patching experience;
the 4-regime CCS sweep as the MACC-extraction template; budget-construction method;
proxy-VL-then-swap pattern. Aluminium = sector one, already built (but the worst-mapping sector
for the coupling — see crosswalk).

## Key references

- Gidden et al. 2025, *Nature* — prudent planetary limit (~1,460 Gt), regional stock caps. Data:
  Zenodo 15657543 (gridded, Jan 2026).
- Grant et al. 2022, *IJGGC* 120:103766 — regional storage constraints in TIAM (precedent).
  DOI 10.1016/j.ijggc.2022.103766.
- Zahasky & Krevor 2020, *EES*; Zhang, Jackson & Krevor 2024, *Nat. Commun.* 15:6913 — rate/flow
  limits.
- Zhang (Huizhong) et al. 2026, *Resources, Conservation & Recycling* 228:108785 — nearest
  competitor. DOI 10.1016/j.resconrec.2026.108785.
- GCAM-CDR v1.0, *GMD* 16:1105 (2023); GCAM industrial sector docs (IAMC; jgcri.github.io).
- MESSAGEix-Materials v1.1.0, *GMD* 2024 — stretch tool.
- MPP sector models (steel/cement/ammonia/aluminium) — the sector data engine.

## Next steps (priority order)

1. **Pull full texts of Zhang 2026 (10.1016/j.resconrec.2026.108785) and Grant 2022
   (10.1016/j.ijggc.2022.103766)** — confirm exact constraints; lock the novelty wording. Highest
   value before committing framing. (Zhang paywalled — get PDF.)
2. **Prep for the Humphrey meeting (next week).** Bring the crosswalk table. Decide/ask:
   (a) positive-spine + normative-contrast allocation — confirm;
   (b) **how hard is imposing Gidden stock + flow caps in GCAM** (input-data change vs new code) —
       the pivotal fact for thesis-vs-paper backbone; ask the GCAM staff directly;
   (c) how to handle the aluminium captive-power / GCAM-electricity boundary;
   (d) start sectors = cement + steel (cleanest carve) — confirm;
   (e) official GCAM VL run timing (drives proxy-vs-official input decision).
3. **Build the toy LP** (2 sectors, 1 region, 3 periods, shared stock + flow cap) — prove the
   machine is ~50 lines; becomes the skeleton for the real version.
4. **Data starts:** download Gidden regional stock caps (Zenodo 15657543); pick the flow-cap
   source (Krevor 2024) and decide derivation; scope where GCAM power/BECCS/DAC cost curves live
   (with GCAM staff).
5. **Extract steel + cement MACCs from MPP** (mirror the aluminium 4-regime sweep), harmonised to
   the common region grid, China first.
6. **Decide GCAM VL input:** proxy now (AR6/SSP) vs wait for official VL — confirm timing (step 2e).
7. Tangential/admin: get set up on the SBTi GitHub repo (user flagged).

## Decisions log

- **2026-08-30** — B selected as thesis direction (Humphrey's cross-sector allocation variant),
  scoped-on-proxies for the 12-month thesis with aluminium as the bankable floor; reach paper
  after with official GCAM VL + coauthors. Architecture = bottom-up coupled to GCAM top-down;
  thesis uses own-LP + residual on proxies, paper uses constrained-GCAM backbone (feasibility
  hinges on how hard imposing caps in GCAM is — verify with staff). Toolset = custom intertemporal
  LP fed by MPP MACCs; rejected MPP-as-optimiser and (for now) MESSAGEix-Materials. Allocation
  basis = avoided cost (shadow price, rising intertemporal rent, grid-coupled), positive spine +
  normative contrast. Non-MPP sectors (power/BECCS/DAC/blue-H2) enter top-down from GCAM cost
  curves (elastic, not fixed quantities); DAC as backstop. Novelty confirmed open; race risk =
  Gidden/IIASA. Verified GCAM crosswalk: Other Industry is a clean residual (no double-count — my
  earlier framing corrected); GCAM Aluminum has no process CCS (captive-power boundary is the one
  real issue); lead with cement + steel.
