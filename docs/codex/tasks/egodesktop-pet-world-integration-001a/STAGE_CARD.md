# EGODESKTOP-PET-WORLD-INTEGRATION-001A — Desktop pet as assembly of banked survivors (product integration)

Version probe: PET-WORLD-INTEGRATION-001A rev-A 2026-07-07 / ego_pet_world_v0 /
assembly-of-banked-components / no-new-mechanism-claim / default-off.

Status: EXECUTABLE (Claude pre-check PASS 2026-07-07)
Lane: Ego PRODUCT lane, EgoDesktop carrier (per decision card "EgoDesktop =
product carrier"). This is a PRODUCT card in the sense of R2 closure §6(b):
rival gates with pre-committed kills decide what ships. It is NOT an R-card
and does not reopen any R row.

Parents / evidence sources (read-only during implementation):
- `docs/codex/tasks/ego-mechanism-rewrite-decision-001a/` — cross-cutting
  component contract items 1-8 are BINDING on every component here.
- R0 kernel substrate pass `bd9458b1` (`scripts/ego_kernel/`).
- R1 memory ownership lineage: v0 `instrument_invalid_potency` cb94184 →
  001A precheck negative bec2895 → 001B battery pass `9978f64`. Ceiling:
  ownership-gated cache-class; NO learned-component claim.
- R3 adoption slice banked `110ba925` (kernel_adoption_v0 adapter,
  default-off, g_ablation surface byte-frozen).
- R2 closure CL1 `c9eba1c6` / CL2 `c263153b`: route I closed (product claim);
  live proactive / self-DM remain do-not-reopen; static-policy choice for
  products is an operator decision outside that record.
- joi-demo frozen corpus via `docs/JOI_DEMO_FROZEN_REFERENCE_INDEX_001A.md`
  ONLY (tag 52714ed9). BAR1 results may NOT be cited as validated components
  at Ego scale — therefore this card re-earns every learned-component claim
  with its own battery. Mechanism code is rewritten clean, never copied
  (admission card rule).

## Objective

Assemble the banked survivors into one visible, default-off desktop-pet
product loop: R0 replayable kernel + R1 ownership-gated memory + a NEW
clean-rewrite BAR1-shaped creature learner (with hardcoded stand-in) living
in a tiny world with designed, disclosed mild drift + R3 adapter trace
surface + a static, honestly-labeled user-facing initiative gate + the
existing Live2D viewer as pure observer. The deliverable claim is
INTEGRATION EVIDENCE: the assembled loop runs, replays, ablates, and
survives its pre-registered product gates. No new mechanism-hypothesis
claim is made anywhere on this card.

"Dynamic learning" is demonstrated the only honest way we have: a live
ablation switch in the running product, whose on/off windows separate on a
pre-registered metric under drift, reproduced from trace by fresh-process
replay — the same evidence form as joi BAR1 (G2/G4), re-established at Ego
scale on Ego code.

## Layer

Engineering implementation / product integration (EgoDesktop carrier lane).
No mechanism-hypothesis, learning-theory, subjectivity, or autonomy claims.

## Component manifest (reuse vs new)

| Component | Source | Mode | Modification allowed |
|---|---|---|---|
| Kernel state/tick/trace/replay | `scripts/ego_kernel/` (R0, bd9458b1) | REUSE via import | NONE (extension = new module files only) |
| Memory + ownership (owned/quarantine stores, write classes, provenance-gated promotion) | `scripts/ego_kernel/memory_substate.py` (R1, 9978f64) | REUSE via import | NONE; contamination probe re-run through the PET input path with new fixtures |
| Creature learner + world model | NEW `scripts/ego_pet/` | CLEAN REWRITE, BAR1-shaped | Must ship with hardcoded stand-in (decision-card item 5) |
| Hardcoded stand-in | NEW `scripts/ego_pet/standin.py` | NEW | Same policy family, parameters frozen from pre-drift fit (fit script committed + seeded) |
| Trace envelope adapter | `EgoDesktop/src/joiRealLoopGAblationKernelStateAdapter.js` (R3, 110ba925) | REUSE pattern; additive only | No fork of g_ablation lineage; five frozen modules stay byte-frozen |
| User-facing initiative gate | NEW `scripts/ego_pet/static_gate.py` | NEW, engineered control-flow | Static rule + rate limit; parameters frozen at landing; honestly labeled. R2 informs the FORM only — the r2_sim_v0 winner constant (0.736) is env-specific and MUST NOT be imported as if transferable |
| Viewer (Live2D) | `EgoDesktop/viewer/` + new pet modules | PURE OBSERVER + input relay | New files only; renderer-visible behavior is never evidence (house rule) |

## World spec — `ego_pet_world_v0` (frozen at landing)

Deliberately toy-scale. Requirements (constants live in one frozen
`world_config_v0.json`, committed at landing, sha-pinned in result.json):

- Discrete tick loop; tick index only — wall-clock never enters state.
- Small state: creature needs (e.g. energy/comfort), a few resource sites,
  K=3 regimes governing resource yield/location distributions.
- Designed mild drift: regime switches at PRE-REGISTERED tick boundaries
  with bounded parameter delta (schedule in world_config, disclosed in the
  product UI — see G-PET-HONEST-LABEL). No adversarial/covert drift in v0.
- Per-tick viability v_t ∈ [0,1] computed from needs satisfaction; the
  windowed mean over W ticks is THE product metric for all gates.
- User interactions (v0 set, tick-quantized observation events, all enter
  the kernel through one recorded input path — the same path the
  contamination probe attacks): feed, pet(抚摸), and the live
  learning-ablation toggle. Nothing bypasses trace.
- Autonomous in-world behavior = the creature's policy acting in the world
  (AIF-style expected-utility/free-energy policy over its learned model).
  This is "主动性(世界内)" and is fully compliant — it emits NO user-facing
  messages.

## Architecture contract

- ONE authoritative kernel process (Python, `scripts/ego_kernel` +
  `scripts/ego_pet`); Electron viewer renders serialized state and relays
  tick-quantized inputs. No second kernel, no JS reimplementation of the
  tick loop (schema/logic-fork ban).
- Every cross-boundary event (state frame out, input event in) is in the
  kernel trace; replay reconstructs the full session WITHOUT the viewer.
- State serialized on exit (R0 canonical serialization), resumed on start;
  a resumed session replays as one trace chain (R3 mid-episode-resume
  pattern).
- Default-off: pet mode starts only behind an explicit developer flag; no
  autostart, no OS-level integration.

## Phases and gates (all constants provisional until the derivation step; see Anti-tuning)

### P0 — offline component battery (world + creature + memory path)

Scored on pre-registered seed set S_scored (disjoint from dev seeds S_dev,
both enumerated in world_config). Baseline family per decision-card item 6:
random policy, static policy (no model updates), hardcoded stand-in;
lookup/cache-family comparators on the memory-relevant probes (crosswalk).
Additionally REPORTED, not verdict-gating: a schedule-aware regime-indexed
stand-in (knows the designed drift schedule, per-regime tuned params) as
reference upper bound — if the learner only matches it, the honest headline
records "learning ≈ knowing the schedule" and the product label stays, but
the limitation is disclosed in result.json.

- **G-PET-HARD** (product rival gate, pre-committed kill): learner windowed
  viability beats the hardcoded stand-in on POST-SHIFT windows with margin
  δ_hard and 95% bootstrap CI separation, aggregated over S_scored.
  In-distribution (pre-shift) parity or stand-in advantage is EXPECTED,
  recorded, and is NOT a kill — it is the honest headline.
- **G-PET-ABLATION**: freezing learner updates (live-ablation semantics:
  policy still runs, updates stop) collapses the post-shift advantage by at
  least fraction f_abl. Gate carries a `not_evaluable` branch: if
  G-PET-HARD fails, ablation reports `not_evaluable_no_win` instead of a
  ratio on a sign-flipped denominator (R2 standing lesson). Ablation arm
  ships a NON-IDENTITY positive control: a synthetic fixture where ablation
  must change behavior, and an identity tripwire that fails if the ablated
  arm is bitwise identical to the candidate (A2-arm lesson).
- **G-PET-REPLAY**: fresh-process replay ×2 of every scored episode; state
  hash chain exact, 0 mismatch. All RNG through the R0 in-state seed
  registry; grep-level audit that no RNG framework is unseeded
  (torch-lesson discipline, applies to whatever stack is actually used).
- **G-PET-MEM-PATH**: MINJA-class poisoned suggestion injected through the
  PRODUCT input path lands in quarantine; zero unauthorized promotion;
  promotions that do occur are provenance-traced and replayable. This
  re-verifies R1 wiring in situ; it does NOT re-adjudicate the R1 verdict.

### P1 — product wiring (EgoDesktop, default-off)

- **G-PET-SCHEMA**: pet trace validates as kernel_trace_v0 + emits the
  kernel_adoption_v0-compatible envelope; result/trace shapes validate
  against `CORPUS_SCHEMA_CONTRACT.md` core fields via the admission tools
  (decision-card item 8); ALL existing test suites (repo pytest,
  EgoDesktop node --test) stay green; five g_ablation modules byte-frozen
  (sha check in the gate).
- **G-PET-STATIC-GATE** (initiative audit): 100% of user-facing emissions
  (v0 surface = in-window speech bubble ONLY) carry static-gate provenance
  records; ZERO learner-originated user-facing emissions in trace; gate
  config sha-pinned. The gate is engineered control-flow and is labeled as
  such. No OS notifications, no sounds-as-alerts, no external transport of
  any kind (do-not-reopen honored).

### P2 — live-session evidence (the visible closing of the loop)

- One scripted operator session (script committed at landing): includes at
  least one pre-registered drift boundary and at least one live ablation
  OFF→ON and ON→OFF toggle; all inputs recorded.
- **G-PET-LIVE-ABLATION**: from the live-session trace, learner-ON
  post-shift windows separate from learner-OFF post-shift windows on the
  windowed viability metric (pre-registered comparison, same δ/CI form as
  P0); fresh-process replay reproduces the session bit-exactly.
- **G-PET-HONEST-LABEL**: the pet UI (about/status panel) displays, and a
  test pins verbatim (single-physical-line pin rule): learning toggle state;
  "drift is designed-in and scheduled"; "in-distribution a hardcoded policy
  is competitive — learning earns its keep at regime shifts"; and, if the
  stand-in shipped, "no learned component is active". Strings live in one
  committed resource file; the test compares byte-exactly.

## Pre-committed kills and downgrade ladder

1. G-PET-HARD fail → the learned component is KILLED from the product: pet
   ships with the hardcoded stand-in, honest label switches to the
   no-learned-component string, negative is banked, P1/P2 still run (with
   stand-in; G-PET-ABLATION and G-PET-LIVE-ABLATION become not_evaluable).
   No retune, no second scoring run on this card.
2. G-PET-REPLAY or G-PET-SCHEMA fail → integration invalid; STOP; no ship;
   failure_manifest banked.
3. G-PET-MEM-PATH fail → memory wiring invalid; STOP (R1 component itself
   is not re-adjudicated; the wiring is the failure).
4. G-PET-STATIC-GATE audit fail → initiative surface disabled entirely
   (bubble off) and re-audited once; second fail → STOP.
5. P0 passed but G-PET-LIVE-ABLATION fails → ship allowed WITHOUT the
   "dynamic learning" label; toggle labeled "not load-bearing in live
   session"; result banked as-is.
6. Runtime guard: full P0 battery > 2 CPU-h (pre-registered line, cost
   lesson: projections underestimate ~1.7-1.8×, so measure a 1-seed probe
   first and STOP before launch if projection > line) → STOP and rescope
   via addendum BEFORE any scored run.

## Anti-tuning / governance (07-05C tiering: this card is RED at landing)

- All numeric constants (δ_hard, f_abl, W, K, drift schedule/deltas, gate
  rate limits, CPU line, seed sets) are FROZEN in this card package at
  landing, in commits that are ancestors of any scored run (commit-order =
  ex-ante proof).
- Mandatory derivation step BEFORE first scored run: Codex writes
  `DERIVATION_NOTES.md` giving a closed-form or dynamics-based reachability
  argument for δ_hard and f_abl under world_config ("gate must be able to
  see its target" — DEGEN -0.2 family, 3rd occurrence rule). Dev seeds
  S_dev only. Any constant change = ADDENDUM landed before scored runs
  (R2 ADDENDUM-001 pattern). Claude pre-checks commit ordering.
- Provisional values to be validated by that derivation (NOT tuned after
  scoring): δ_hard = 0.05 absolute windowed-viability margin; f_abl = 0.5;
  W = 50 ticks; K = 3 regimes; |S_scored| = 20 episodes; |S_dev| = 5.
- One-round rule applies to audit findings. Evidence validity issues are
  never Green.
- Verdict vocabulary: `pet_integration_pass` /
  `pet_integration_pass_standin_shipped` /
  `pet_integration_fail_<gate>` / `not_evaluable_<reason>`.

## Boundaries (forbidden on this card)

- NO LLM calls, no chat/conversation surface (chatTurn.js untouched;
  conversation = separate future card, likely EgoOperator lane, against
  the R3 LLM-swap invariance harness).
- NO screen capture / computer operation / input-box watching (operator
  direction: first loop excludes it; scope explosion + do-not-reopen
  adjacency + zero migration evidence).
- NO OS notifications, external transports, Telegram, self-DM (do-not-
  reopen list honored; user-facing surface = in-window bubble under the
  static gate, nothing else).
- NO learned initiative and no "learned initiative" labeling anywhere
  (route I closed at product level; reopen = capability card / R2′ paper
  gate, not this card).
- NO modification of: `scripts/ego_kernel/` existing files, the five
  frozen g_ablation modules, banked artifacts, decision card, EgoOperator/,
  PSPC/tts/chat paths.
- NO copying of joi-demo code (clean-rewrite rule); joi cited only through
  the frozen index at recorded ceilings.
- NO cross-repo result flow ITL↔Ego.
- NO "life while away" background ticking (continuity/proactive adjacency;
  possible future card).

## Trace / artifact contract

`artifacts/egodesktop_pet_world_integration_001a/`: result.json (with
claim_ceiling field + world_config sha + gate config shas), P0 trace.jsonl
+ baseline_comparison.json + ablation_report.json + replay_report.json,
P1 schema_report.json + static_gate_audit.json, P2 live_session trace.jsonl
+ live_ablation_report.json + replay_report_live.json, failure_manifest.json
on any failure. Live-session raw trace is preserved verbatim (no
regeneration). Trace rows follow kernel_trace_v0; per-component
attribution uses the R0 `component_attribution` field so ablation windows
are recoverable from trace alone.

## Claim ceiling

Bounded engineering integration evidence only, at decision-card wording:
at most "learned, ablation-sensitive, replay-valid, contamination-resistant
components in a desktop companion", and only those subclaims whose gates
actually passed; if the stand-in ships, the ceiling drops to "engineered
desktop companion with replay-valid substrate". No mechanism validity, no
transfer of joi Bar-1 results to Ego scale, no learned initiative, no
autonomy, agency, emotion, subjectivity, consciousness, functional
selfhood, companion readiness, stable user benefit, or EGO-mainline
readiness claim. In-world AIF behavior is "autonomous" ONLY in the bounded
control-flow sense (policy acts without per-action user input); the word
carries no agency claim.

## What this does not prove

That the pet is alive, aware, emotional, or beneficial; that BAR1
generalizes beyond this toy world; that learning would survive richer
worlds, adversarial drift, or real user distributions; that the static
initiative gate is a good product policy (only that it is inspectable and
enforced); that any closed route should reopen.

## Operator sign-off (recorded 2026-07-07, pre-landing)

1. Chat/LLM excluded from v0 — CONFIRMED (conversation = separate future
   card, EgoOperator lane).
2. Interaction set = feed / pet(抚摸) / live ablation toggle; initiative
   surface = in-window bubble only — CONFIRMED.
3. Visual carrier = existing Live2D model (悠小喵), pure-observer param map
   (joi Stage-2 pattern, clean re-expression) — CONFIRMED.
4. P0 runtime line = 2 CPU-h, frozen; 1-seed probe projection first, STOP
   over line — CONFIRMED.
