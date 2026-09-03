# Thesis ideas — index and retrieval protocol

Two candidate MSc thesis projects, kept in separate running-context files so work on one
does not consume context budget for the other. **Similar methods** (IAM scenario data +
sector/asset model + material-flow reasoning), so cross-references are expected.

## Retrieval protocol (read this first)
- **Do not load both idea files at once.** When the user names or is clearly working on one
  idea, load only that idea's running-context file. Load the other only when explicitly asked
  to compare or cross-reference.
- Each idea's running-context file is the **durable memory** of strategic conclusions — read it
  to restore context after a `/clear`, and **append** new decisions to it as they are made
  (dated, with the rejected alternative, matching the existing design-log style).
- Detailed model/code state for Idea A lives in its project folder docs; the running-context
  file is the strategic layer above them.

## The two ideas

### Idea A — Aluminium grid × CCS pathway (ACTIVE, PoC done)
Primary aluminium smelting decarbonisation: at fixed VL ambition, how grid pathway (varied by
IAM) × captive-power CCS constraint shape least-cost electricity sourcing, and where that makes
the sector budget infeasible / forces outsized CCS claims. 16-cell PoC matrix has run.
- **Running context:** `thesis_aluminium/IDEA_A_running_context.md` ← today's strategic decisions
- **Detailed design log:** `thesis_aluminium/thesis_design_choices.md` (D1–D11, O1–O10)
- **Model reference / project state:** `thesis_aluminium/MODEL_REFERENCE.md`, `thesis_aluminium/CLAUDE.md`
- **Earlier published-data pathway:** `thesis_aluminium/pathway_derivation_choices.md`

### Idea B — Cross-sector CCS storage allocation (SELECTED as thesis direction 2026-08-30)
Hard-to-abate sectors compete for a shared, regionally stock-and-flow-limited CO2 storage budget
(Gidden 2025 caps); bottom-up asset-level sectors coupled to a GCAM top-down backbone; least-cost
allocation over time; does CCS cost self-limit below the geophysical limit or must policy cap it.
- **Running context:** `thesis_idea_b.md` ← full strategic record + next steps (read this first)
- Origin: Humphrey Adun framing. Thesis on proxy VL data (aluminium = floor); reach paper after
  with official GCAM VL + IIASA/JGCRI coauthors. Idea A (aluminium) is sector one of B.

## Working preferences (both ideas)
Ask before running the model. Answer the question asked. Concise in chat. No invented jargon.
Verify before asserting. Log normative choices with the rejected alternative.
