# RESEARCH_NEGATIVE_RESULTS_CROSSWALK_001A — ITL + joi-demo evidence → Joi-like roadmap routes

Created 2026-07-06. Read-only research input; changes only by importing newly
banked ITL/joi results with anchors. Purpose: upgrade the marked 【推断】 rows
of `docs/Joi-like_bounded_mechanism_proxy_roadmap_v1.md` to 【事实】 where an
actual measurement exists, per that document's own Part 6 contract. Every
entry is a bounded result at its tested scale/access regime — not a universal
theorem. ITL anchors live in `intelligence-theory-lab` artifacts;
joi anchors in the frozen corpus via `JOI_DEMO_FROZEN_REFERENCE_INDEX_001A.md`.

## 1. Cross-cutting facts (both labs)

- **X1 Equal-access identifiability ceiling.** ITL: ~12 closed lineages where
  fair baselines tied/beat single-mechanism candidates (LRGG saturation;
  Route C == discounted-batch-LS; ACOLB/ACP-BV saturation; N2 graph_closure;
  SAME-AGENT kernel tied 1.0=1.0 by drift-aware continual replay). joi: ≥4
  independent confirmations. Design rule: functional non-replaceability must
  be engineered as access asymmetry (owned state gating behavior), not
  expected from cleverer internals at equal access. Not implied: mechanisms
  useless at other scales/regimes; componentized-vs-monolithic SYSTEM question
  (untested; ITL preflight queued).
- **X2 Learning pays where drift/personalization lives.** joi honest
  headline (in-distribution hardcoded crushes learner) + ITL TLGP floor
  (passive M/U absorbed by fair meta-learner; tested-scale bounded negative
  with cross-lineage caveat, banked 3ec8db9).
- **X3 Ops rules.** Cost projections from single samples underestimate
  1.7-1.8× (ITL S3d: 22.3→31.95 CPU-h) — measure full-scale round before
  budget lines. Unseeded framework RNG = process-level replay breakage (ITL
  torch lesson) — seed everything, fresh-process replay gates; joi FUSE
  history — hashes host-native only.

## 2. Route-by-route status (roadmap A-J)

| Route | New status | Evidence |
|---|---|---|
| A memory+reflection | 【推断→部分事实】 raw-store baselines are the real bar | ITL: graph-cache family mandatory (Gate1 collapse; N2). joi: G1 spike thin headroom only after compute-matched control; full G1 on route-economics HOLD |
| B ReAct/tool-use | 【推断】unchanged | no direct test either lab |
| C skill library | 【推断→部分事实】 substrate facts measured | joi: capacity is the competence lever (001C); G0 skill lines same-access saturated at Bar-1 |
| D world-model+PE | 【推断→事实(相邻)】history-conditioned baselines are strong | ITL: RESIDUE window dominance for passive belief; same-agent kernel PE-contrast tied by drift-aware replay. D's held-out-dynamics toy itself still untested |
| E active inference | 【推断→纸面事实】absorption confirmed | ITL C-preflight STOP: stated separators absorbed on paper by structural Bayes/EVI, POMDP planning, drift-aware active replay. joi: S1-P4 homeostatic probe counterproductive; payoff variant == direct optimizer. Roadmap's "易关" rating now evidence-backed |
| F self-model latent | 【推断→事实】collapsed at toy scale | joi S2 CLOSED (not load-bearing; below always-predict). ITL: K1/K2 grounding closed. Roadmap's predicted calibration-collapse confirmed |
| G attention/salience | 【推断】unchanged | no direct test |
| H user modeling | mixed 【事实】 | positive: joi G4B bounded Bar-1 pass (binary latent, beats population floor, below Bayes as expected). trap: ITL Gate4 social self-report tautology — never evaluate on self-generated labels |
| I controlled initiative | **untested — only first-tier route with zero negative evidence** | roadmap T1 card (Part 8) remains the ready-to-execute test with built-in threshold-tuning kill |
| J multi-timescale memory | 【推断→部分事实】 | flat/graph-cache pressure (ITL); contamination is real (ITL MINJA reuse-scan) → write-protection classes + quarantine required in any Ego memory design |
| curiosity (D/E epistemic term) | 【事实】raw PE curiosity harmful at all tested capacities; naive LP degenerate 2× | joi growth/LP lines; capacity does not rescue signal problem |

## 3. What this changes for Ego route selection

1. Roadmap's near-term pick I > B > C stands and is now sharper: I is the
   only first-tier route not yet touched by negative evidence in either lab.
2. Any A/J memory work in Ego must ship graph-cache/raw-RAG challengers and
   MINJA-style contamination defenses from day 1 (not retrofitted).
3. Any E-flavored proposal must state, before code, a separator against
   structural Bayes/EVI + drift-aware active replay (ITL C-preflight showed
   "interventions help" is not one).
4. F/self-model features are engineering (access control, calibration
   plumbing) with zero grounding claims available.
5. System-level open question (not covered by any closure): componentized
   system vs monolithic fair learner under same access/compute/memory — ITL
   design-only preflight queued; either answer informs Ego architecture
   status (science vs convenience).

## 4. Proposal (proposal-only, needs its own card): LLM-swap invariance test

For the LLM-first loops (EgoOperator, EgoDesktop g_ablation lineage), add to
the battery: freeze proxy/creature state + input log; swap LLM
provider/prompt-style; the behavior deltas ATTRIBUTED to owned state by the
existing ablation/replay gates must persist within a predeclared band. If
swapping the renderer erases the attributed differences, the attribution was
renderer-borne (roadmap L1, "renderer = mechanism" cheat vector) and the
result downgrades. Complements off-static replay; default-off; no threshold
chosen here.
