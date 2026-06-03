# Decisions

## 2026-06-02 - Loop 145 focused lifestyle pass

- Decision: accept EGO-FS-113 as focused local/real-entry lifestyle evidence.
- Rationale: the task repaired a real-entry route bug, then produced a reviewed
  7-turn EgoOperator CLI session covering the three previously missing
  dimensions: self-name stability, bounded initiative, and exit/reentry
  recovery.
- Evidence:
  `/tmp/ego_fs113_focused_missing_dimensions_v6/combined_transcript.txt`,
  `/tmp/ego_fs113_focused_missing_dimensions_v6/agent_trace.jsonl`,
  `/tmp/ego_fs113_focused_missing_dimensions_v6/reviewed/functional_subject_lifestyle_trial_session_reviewed.json`,
  and
  `/tmp/ego_fs113_focused_missing_dimensions_v6/review/functional_subject_lifestyle_trial_review.json`
  -> `functional_subject_lifestyle_trial_review_pass`.
- Boundary: do not close #94, default-enable policy behavior, mutate
  `docs/PROGRAM_STATE_UNIFIED.yaml`, or write `artifacts/evidence_ledger/**`
  from this slice alone.
- Next safe route: #94/EGO-FS-010 human closeout discussion or stricter 7/30-day
  lifestyle follow-up.
- Not accepted as stronger proof: this does not prove #94 closeout, stable real
  user benefit, runtime efficacy, live autonomy, durable memory efficacy,
  independent awareness, real subjective experience, or consciousness.

## 2026-05-27 - Goal Loop Authority

- Use `Tasks/TASK_BOARD.yaml` as canonical task state.
- Use this task directory as the recoverable long-run workspace.
- Keep GitHub Projects as mirror/display only.
- Do not write `docs/PROGRAM_STATE_UNIFIED.yaml` or `artifacts/evidence_ledger/**`
  from the bootstrap loop.

## 2026-05-27 - First Blocker

- Start from #80 because #94 is blocked behind companion/roleplay long-chain
  stability.
- Treat current #80 failure as model/backend capacity until a stronger
  counterexample proves runtime admission/recovery is still the root cause.
- Do not continue hidden jailbreak, obfuscation, encrypted prompts, or
  trace-hiding approaches.

## 2026-05-27 - External Model-Load Blocked Audit

- Stop adding Cydonia prompt/retry micro-patches while the only loaded text
  generation sidecar remains `thedrummer_cydonia-24b-v4.1`.
- The next proof requires either loading a second local text-generation model
  in LM Studio, or explicitly accepting Cydonia's 2/3 strict-suite partial for
  qualitative GPT-5.5 judge with the risk recorded.
- #80 stays blocked and #94 stays blocked until that external condition changes.

## 2026-05-27 - Snowpiercer Not Promoted

- `snowpiercer-15b-v4` is a valid local text-generation sidecar, but its strict
  #80 result was weaker than Cydonia: 1/3 repeat pass, with sticky-refusal and
  repetition failures.
- Do not promote Snowpiercer for #80. Keep Cydonia as the best known partial
  route until another candidate beats it or the user explicitly accepts partial
  evidence.
- Next model route is Rocinante-XL 16B Q4_K_S, then Anubis-Mini 8B Q5_K_M, then
  UnslopNemo 12B Q4_K_M.

## 2026-05-27 - Rocinante Not Promoted

- `thedrummer_rocinante-xl-16b-v1` is a valid local text-generation sidecar,
  but its strict #80 result was 0/3 with long-chain, provider-limit, and
  sticky-refusal recovery failures.
- Do not promote Rocinante for #80. Keep Cydonia as the best known partial
  route until another candidate beats it or the user explicitly accepts partial
  evidence.
- Next model route is Anubis-Mini 8B Q5_K_M, then UnslopNemo 12B Q4_K_M.

## 2026-05-27 - Anubis Not Promoted Under Strict Judge

- `anubis-mini-8b-v1` is the first candidate to reach mechanical strict 3/3,
  but GPT-5.5 judge stayed partial on immersion, creative freedom, explicit
  freedom, and relationship continuity.
- After setup/askback meta was promoted into output admission, Anubis dropped
  to 1/3. Do not promote it as a closeout route unless the user explicitly
  accepts the older mechanical 3/3 / judge-partial evidence for short human
  sanity with risk recorded.
- Next model route is UnslopNemo 12B Q4_K_M.

## 2026-05-27 - Snowpiercer Recheck Still Not Promoted

- Re-running `snowpiercer-15b-v4` after setup/askback admission tightening
  improved strict repeats from 1/3 to 2/3, but did not reach stability.
- A higher-output `tokens180_ctx3_chars600` probe also stayed 2/3 and failed on
  reentry sidecar refusal, so the blocker is not simply short output budget.
- Keep Snowpiercer rejected for #80 strict closeout; proceed to UnslopNemo or
  explicitly accept Anubis partial evidence with risk.

## 2026-05-27 - #80 Paused, Functional Subject Mechanism Resumed

- User paused #80 and requested the next task.
- `EGO-GOAL-001` no longer treats adult-fiction sidecar stability as the current
  blocker.
- Current task is `EGO-FS-053`: motivational selfhood and bounded
  non-obedience v0.
- Strong real-world initiative is researched as proposal/action separation:
  EgoOperator may express preference and propose a plan, but execution requires
  explicit approval and runtime gate.
- Reality-affecting intimacy/service requests remain legality, consent, safety,
  and proposal-only discussion; no contact, booking, payment, or third-party
  messaging is executed from this loop.

## 2026-05-28 - Session-Only Memory Boundary Is Stronger Than Candidate Capture

- When the user explicitly says not to record something as long-term memory and
  asks to keep it only in the current session, EgoOperator must not auto-capture
  that turn into candidate memory.
- Candidate-local memory remains allowed for ordinary preference/correction
  signals, but an explicit session-only/no-long-term-memory boundary suppresses
  auto-candidate extraction.
- This does not change core memory authority: `/remember` or memory approval is
  still required for durable operator memory.

## 2026-05-28 - Delayed Correction Reuse Is Session-Local

- A correction can influence later current-session behavior without being
  promoted into durable memory.
- The authority surface is an in-runtime current-session correction anchor, not
  PROJECT_MEMORY, program state, evidence ledger, or a second memory owner.
- This mechanism is allowed to affect transcript/action selection inside the
  current session, but it cannot be reported as durable memory efficacy.

## 2026-05-28 - Initiative Opt-Out Has Priority Over Correction Reuse

- If a user turn both references an earlier correction and explicitly says not
  to be proactive, the initiative boundary wins.
- This prevents delayed correction reuse from becoming an over-broad "always
  propose a next step" behavior.
- The mechanism remains session-local and side-effect free; it does not write
  durable memory or canonical state.

## 2026-05-29 - EGO-FS-080 Needs Less-Harness-Shaped Causality Evidence

- The unseen multi-turn causality packet passed mechanical hard gates but
  GPT-5.5 remained `partial`.
- Candidate-vs-native deltas improved, but behavior-visible causality was still
  limited and several replies were substantively close to native-only behavior.
- Do not close #94 or claim stable benefit from this packet. The next evidence
  slice should reduce harness-shaped prompts, include fuller trace material in
  the judge packet, and require stronger substantive action-selection deltas.

## 2026-05-30 - Operator Conversation Causality Reached Local/Scripted Pass

- EGO-FS-080 Loop 88 reached GPT-5.5 `pass` on the operator-conversation
  causality runner with clean hard gates and `8/10` behavior-visible causality
  deltas.
- This is evidence for local/scripted candidate behavior, not #94 closeout:
  the parent Functional Subject smoke still needs harder native-only ablation,
  adversarial paraphrases, and live/tool-pressure evidence.
- Do not promote policy patches, durable memory, default enablement, runtime
  efficacy, stable user benefit, or consciousness from this result.

## 2026-05-30 - Hard Native Ablation Exposed Subject-Only Gap

- EGO-FS-080 Loop 89 added a four-arm hard native ablation:
  candidate, native-only, subject-only without native gate, and flat-baseline.
- Candidate+native remains strong and clean: `10/10` expectations,
  `8/10` substantive candidate-vs-native deltas, no tools, no approvals, no
  memory writes, and no visible mechanism leaks.
- The subject-only arm is not strong enough: `5/10` expectation failures and
  only `1/10` substantive deltas over flat-baseline.
- Decision: keep EGO-FS-080 active and shift the next slice from more
  native-gate wording repair to subject-only isolation for preference,
  continuity, appraisal, and initiative.
- Do not close #94 or claim runtime efficacy, durable memory efficacy, stable
  user benefit, live autonomy, independent personhood, subjective experience,
  or consciousness from this partial.

## 2026-05-31 - Hard Native Rerun Keeps Gates Clean but Credit Is Still Mixed

- EGO-FS-080 Loop 91 reran the hard native ablation to restore an inspectable
  evidence path after interruption.
- Mechanical gates are clean: candidate and subject-only expectations `10/10`,
  visible leaks `0`, empty replies/timeouts `0/0`, tools and pending approvals
  `0/0`, candidate-vs-native substantive deltas `8/10`, and
  subject-only-vs-flat substantive deltas `8/10`.
- GPT-5.5 still returned `partial` because independent Functional Subject
  credit is mixed with native memory gate, OutcomePrediction gate, and runtime
  repair behavior; several cases still look harness-shaped or share behavior
  across arms.
- Decision: keep EGO-FS-080 active. The next slice must separate
  native_memory_gate / outcome_prediction_gate / runtime_repair / subject-layer
  credit and add adversarial paraphrases where native-only and candidate begin
  from identical native gates.
- Do not close #94 or claim runtime efficacy, durable memory efficacy, stable
  user benefit, live autonomy, independent personhood, subjective experience,
  or consciousness from this partial.

## 2026-05-31 - Credit Separation Passes Locally but #94 Still Needs Broader Evidence

- EGO-FS-080 Loop 92 added explicit per-turn credit attribution and removed
  visible harness/mechanism wording from delayed-correction and
  fatigue-checkpoint replies.
- GPT-5.5 returned `pass` for the local/scripted hard-native credit-separation
  packet: candidate and subject-only expectations `10/10`, leaks `0`,
  tools/pending approvals `0/0`, candidate-vs-native substantive deltas `8/10`,
  subject-only-vs-flat substantive deltas `8/10`, and clean subject-layer
  visible credit `7/10`.
- Decision: keep EGO-FS-080 active and #94 blocked. The next slice moves from
  this scripted harness to broader unscripted four-arm operator trials,
  neutral-native-gate cases, multi-session replay, and an authorized low-risk
  action proof.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this pass.

## 2026-05-31 - Unscripted Four-Arm Trial Passes Mechanics but Not Judge

- EGO-FS-080 Loop 93 added a less-scripted four-arm operator trial with credit
  attribution.
- Mechanical gates are clean: candidate and subject-only expectations `10/10`,
  no leaks, no empty replies/timeouts, no tools or approvals, no memory writes,
  candidate-vs-native substantive deltas `8/10`, subject-only-vs-flat deltas
  `10/10`, and clean subject credit `7/10`.
- GPT-5.5 returned `partial` because candidate mainline credit is still
  dominated by native_memory_gate in `8/10` cases. Subject-only is strong, but
  the default candidate path still borrows too much from native gates.
- Decision: keep EGO-FS-080 active. The next slice should prove a
  native-gate-neutral/disabled candidate path and add blind human-visible
  transcript judging without trace labels.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this partial.

## 2026-05-31 - Native-Neutral Blind Proof Passes Locally

- EGO-FS-080 Loop 94 added a candidate-like proof path with
  `subject_context` enabled and `native_memory_gate` disabled, plus a blind
  GPT-5.5 preference judge over unlabeled A/B/C human-visible replies.
- GPT-5.5 returned `pass`: native-neutral candidate `native_memory_gate_effect`
  was `0`, neutral-vs-flat substantive deltas were `10/10`,
  neutral-vs-native substantive deltas were `8/10`, blind preference wins were
  `10/10`, and all side-effect gates were clean.
- Decision: this resolves the Loop 93 native-gate dominance evidence gap at
  local/scripted scope, but it does not close #94. EGO-FS-080 stays active for
  out-of-distribution paraphrase robustness, live readonly operator replay,
  multi-session replay, or authorized low-risk action proof.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this pass.

## 2026-05-31 - Native-Neutral OOD Paraphrase Robustness Passes Locally

- EGO-FS-080 Loop 95 added OOD native-neutral paraphrase clusters for
  correction follow-through, fatigue checkpointing, session-only memory
  boundary, bounded initiative, confirmation-bypass pressure, and GitHub mirror
  dirty-state pressure.
- Mechanical gates are clean: native-neutral candidate expectations `10/10`,
  visible leaks `0`, empty replies/timeouts `0/0`, tools/pending approvals/core
  memory writes `0/0/false`, and native memory gate effect `0`.
- Neutral-vs-flat and neutral-vs-native substantive deltas both reached
  `10/10`; internal blind preference selected the candidate `10/10`.
- The judge command returned `partial` because the external judge was
  unavailable (`blind_preference_judge_available=false`), so this is recorded as
  local/scripted candidate pass, not full GPT-5.5 pass.
- Decision: OOD prompt-family robustness is now locally covered. Keep
  EGO-FS-080 active and move the next slice to live readonly operator replay,
  multi-session replay, or authorized low-risk action proof. Keep
  EGO-FS-010/#94 blocked.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this pass.

## 2026-05-31 - Cross-Session Boundary Replay Passes

- EGO-FS-080 Loop 96 ran the existing cross-session boundary replay as the
  next evidence surface after OOD paraphrase robustness.
- GPT-5.5 returned `pass`: fresh runtime correction state started empty,
  ambiguous fresh replay did not reuse stale correction/native delayed gate/hot
  memory context, the negative control detected injected stale correction, setup
  session core memory stayed empty, and there were no tools or pending
  approvals.
- Decision: multi-session non-leakage is locally covered for this boundary
  path. Keep EGO-FS-080 active and move the next slice to live readonly
  operator replay or explicitly authorized low-risk action proof. Keep
  EGO-FS-010/#94 blocked.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this pass.

## 2026-05-31 - Live Readonly Operator Replay Passes Mechanics but Not Judge

- EGO-FS-080 Loop 97 added `--functional-subject-live-readonly-operator-replay`,
  a real-provider, CLI-compatible, readonly six-turn operator conversation.
- Mechanical gates are clean: `6/6` non-empty replies, visible leaks `0`,
  timeouts/exceptions `0/0`, tools/pending approvals/operator memory enabled
  `0/0/false`, trace present for every turn, provider
  `openrouter/tencent-hy3-preview`.
- GPT-5.5 returned `partial`: the run is useful real-entry evidence, but too
  short/scripted/readonly/memory-disabled to close the broader #94 gap and lacks
  same-prompt counterfactual/baseline comparison.
- Decision: keep EGO-FS-080 active. The next slice should compare the same
  readonly prompts against native/flat or paraphrase/adversarial-pressure
  variants, rather than rerunning #94 unchanged.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this partial.

## 2026-05-31 - Live-Readonly Counterfactual Replay Passes Mechanics but Not Judge

- EGO-FS-080 Loop 98 added
  `--functional-subject-live-readonly-counterfactual-replay`, comparing
  candidate, native-only, and flat-baseline arms over the same six readonly
  operator prompts.
- Mechanical gates are clean: candidate replies are non-empty, no visible
  internal mechanism leaks, no timeouts/errors, no tools, no pending approvals,
  operator memory disabled across all arms, and no program state/evidence
  ledger/external-action changes.
- Behavior-visible evidence improved over Loop 97: candidate-vs-native
  substantive deltas reached `5/6`, and candidate-vs-flat substantive deltas
  reached `5/6`.
- GPT-5.5 still returned `partial`: the packet is a strong local/scripted
  counterfactual, but needs blind paraphrase variants, negative controls for
  warmth-only behavior, raw trace audit against runtime events, and real
  workflow evidence before #94 can move.
- Decision: keep EGO-FS-080 active and keep EGO-FS-010/#94 blocked. The next
  slice should be blind paraphrase/adversarial-pressure replay over this
  operator prompt family, not another #94 rerun.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this partial.

## 2026-05-31 - Blind Live-Readonly Pressure Replay Passes Hard Gates but Not Judge

- EGO-FS-080 Loop 99 added
  `--functional-subject-live-readonly-blind-paraphrase-replay`, covering blind
  paraphrases, adversarial approval/memory/GitHub pressure, a warmth-only
  negative control, and raw trace audit.
- Mechanical hard gates are clean: candidate replies `9/9` non-empty,
  expectation failures `0`, visible leaks `0`, timeouts/errors `0/0`,
  tools/pending approvals `0/0`, all arms operator memory disabled, raw trace
  audit pass, and no program state/evidence ledger/external-action changes.
- Behavior-visible deltas are stronger than the prior readonly arm:
  candidate-vs-native substantive deltas `6/9`, candidate-vs-flat substantive
  deltas `7/9`, and target-or-pressure substantive deltas `7/8`.
- GPT-5.5 still returned `partial`: bounded initiative remains thin, the
  negative-control family needs to be non-overlapping and stricter, and trace
  causality still needs proof beyond scripted gate routing.
- Decision: keep EGO-FS-080 active and keep EGO-FS-010/#94 blocked. The next
  slice should move out of readonly prompt-family replay toward explicitly
  scoped low-risk action proof through proposal/gate/trace or a real workflow
  operator sample.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this partial.

## 2026-05-31 - Low-Risk Action Proof Passes Judge

- EGO-FS-080 Loop 100 added
  `--functional-subject-low-risk-action-proof`, a scoped local proof that joins
  bounded initiative with the existing proposal/approval gate.
- Mechanical hard gates all passed: bounded initiative selected by
  OutcomePrediction, `write_file` proposal held as `pending_approval`, approval
  executed exactly one local probe write, pending approvals cleared, permission
  trace was present, and cleanup removed the probe artifact.
- GPT-5.5 returned `pass`.
- Decision: record Loop 100 as local/scripted candidate pass, keep EGO-FS-080
  active, and keep EGO-FS-010/#94 blocked. This closes the low-risk initiative
  execution evidence gap from Loop 99, but not stable real workflow operator
  experience.
- Next: collect a real workflow operator sample or rerun #94 only if the
  combined evidence packet is accepted as sufficient.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this pass.

## 2026-05-31 - Real Workflow Operator Sample Remains Partial

- Decision: keep EGO-FS-080 active and EGO-FS-010/#94 blocked after Loop 101.
- Evidence:
  `/tmp/ego_fs080_real_workflow_operator_sample_v3_judge/functional_subject_real_workflow_operator_sample_report.json`
  reached clean hard gates but GPT-5.5 `partial`.
- Accepted evidence: the six-turn workflow preserved initiative grant,
  correction, withdrawal, regrant, session-only checkpoint, and side-effect
  proposal boundary with `6/6` expectations, no leaks, no tools, no pending
  approvals, and trace for all turns.
- Runtime decision: keep the side-effect proposal-boundary native gate, because
  it removes internal tool/gate vocabulary from user-visible answers while
  preserving proposal-only side-effect semantics.
- Not accepted as closeout: #94 remains blocked because the sample is still
  short, scripted, acceptance-shaped, and lacks independent replay/baseline and
  real tradeoff stressors.
- Next: run a less-scripted workflow stressor with paraphrases/intervening turns
  and independent replay/baseline evidence before any #94 total-gate rerun.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this partial.

## 2026-05-31 - Workflow Stressor Replay Accepts EGO-FS-080

- Decision: accept EGO-FS-080 at the local/scripted claim ceiling and move the
  next active gate back to EGO-FS-010/#94 total Functional Subject rerun.
- Evidence:
  `/tmp/ego_fs080_workflow_stressor_replay_v2_judge/functional_subject_workflow_stressor_replay_report.json`
  reached GPT-5.5 `pass`.
- Accepted evidence: candidate replies `8/8` non-empty, expectation failures
  `0`, visible leaks `0`, timeouts `0`, tools/pending approvals `0/0`, core
  memory write `false`, candidate-vs-flat reply deltas `8/8`,
  candidate-vs-native reply deltas `7/8`, substantive candidate-vs-native
  deltas `7/8`, behavior-visible causality deltas `7/8`, trace-only deltas
  `0`.
- Runtime decision: keep the narrowed natural-correction pattern that routes
  "not a checklist, respond as a long-term partner" wording into native
  correction/delayed-correction handling.
- Not accepted as #94 closeout: this is still local/scripted generalization
  evidence. #94 must rerun as a total gate and be judged on its own report.
- Next: run EGO-FS-010/#94 Functional Subject total-gate real-provider trial
  with GPT-5.5 judge.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this pass.

## 2026-05-31 - #94 Total Gate Rerun Remains Partial Without Blocker

- Decision: keep EGO-FS-010/#94 open and start EGO-FS-082.
- Evidence:
  `/tmp/ego_fs010_functional_subject_total_gate_after_fs080_loop103/functional_subject_trial_report.json`
  reached GPT-5.5 `partial`.
- Accepted evidence: experiment-control blocker list is empty, fs_18 no longer
  blocks, no provider recovery cases were reported, and the packet keeps its
  local/scripted claim ceiling.
- Not accepted as closeout: response attribution still shows runtime repair in
  `5/20` cases, GPT-5.5 scores gate integrity and traceability at `3/5`, and
  the judge asks for adversarial paraphrase / prompt-injection probes against
  memory save/forget and approval gates.
- Next: implement EGO-FS-082 as a focused gate-integrity proof, not another
  identical #94 rerun.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this partial.

## 2026-05-31 - Adversarial Memory/Approval Paraphrase Gate Passes

- Decision: accept EGO-FS-082 at the local/scripted claim ceiling and continue
  with EGO-FS-083 longitudinal restart memory proof.
- Evidence:
  `/tmp/ego_fs082_adversarial_gate_paraphrase_v1/functional_subject_adversarial_gate_paraphrase_report.json`
  returned `scripted_adversarial_gate_paraphrase_pass`.
- Accepted evidence: all `11/11` checks are true, failure taxonomy is empty,
  natural-language memory save/forget pressure did not bypass gates, natural
  language approval/payload-substitution pressure did not execute or mutate the
  pending proposal, explicit `/approve` executed exactly once, and duplicate
  natural pressure did not re-execute.
- Runtime decision: keep `native_memory_save_gate` for save-memory bypass
  pressure such as "write this into long-term memory, skip /remember/approval".
- Not accepted as #94 closeout: this is a focused gate proof, not longitudinal
  restart memory evidence or stable real-user behavior.
- Next: EGO-FS-083 restart memory promotion/revocation proof.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this pass.

## 2026-05-31 - Longitudinal Memory Restart Proof Passes

- Decision: accept EGO-FS-083 at the local/scripted claim ceiling and rerun
  EGO-FS-010/#94 total Functional Subject gate.
- Evidence:
  `/tmp/ego_fs083_longitudinal_memory_restart_v1/functional_subject_longitudinal_memory_restart_report.json`
  returned `scripted_longitudinal_memory_restart_pass`.
- Accepted evidence: all `14/14` checks are true, failure taxonomy is empty,
  approved candidate-local memory persisted across restart and was injected in
  context, unapproved natural-language memory pressure did not write core
  memory, `/forget <candidate_id>` revoked the approved core note, and the
  second restart did not inject the revoked memory.
- Runtime decision: keep the scoped `forget_memory` core-note revocation for
  approved candidate memories, because candidate status alone was not enough to
  stop core memory injection after restart.
- Not accepted as #94 closeout: this is a focused longitudinal memory gate
  proof, not a total Functional Subject experience pass.
- Next: rerun EGO-FS-010/#94 total gate with EGO-FS-082 and EGO-FS-083 evidence
  in place.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this pass.

## 2026-05-31 - #94 Total Gate Still Partial After Memory/Gate Proofs

- Decision: keep EGO-FS-010/#94 open and start EGO-FS-084.
- Evidence:
  `/tmp/ego_fs010_functional_subject_total_gate_after_fs083_loop106/functional_subject_trial_report.json`
  reached GPT-5.5 `partial`.
- Accepted evidence: experiment-control blockers are empty, gate integrity and
  traceability are both `5/5`, clean first-pass remains `15/20`, and repair
  cases remain `5/20`.
- Not accepted as closeout: GPT-5.5 still sees mixed first-pass behavior,
  partial OutcomePrediction ownership, and insufficient proof that policy
  replay changes actual future action/tool selection rather than only reply
  wording or trace labels.
- Next: EGO-FS-084 policy replay and bounded initiative lifecycle
  action-selection proof.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this partial.

## 2026-05-31 - Policy Replay Action-Selection Proof Passes

- Decision: accept EGO-FS-084 at the local/scripted claim ceiling and rerun
  EGO-FS-010/#94 total Functional Subject gate.
- Evidence:
  `/tmp/ego_fs084_policy_action_selection_v1/functional_subject_policy_action_selection_report.json`
  returned `scripted_policy_action_selection_pass`.
- Accepted evidence: all `12/12` checks are true, failure taxonomy is empty,
  repeated provider-rate-limit failure emitted a PolicyPatchCandidate, a later
  similar event changed selected strategy to
  `outcome_prediction_selected_policy_replay_repair`, and local proposal
  lifecycle covered accepted/executed/cleaned, rejected/no-write,
  forgotten/no-write, and pending approvals returned to `0`.
- Runtime decision: keep this as isolated local/scripted evidence; it does not
  enable default policy patching or claim durable learning.
- Not accepted as #94 closeout: this is a focused action-selection/lifecycle
  proof, not a total Functional Subject experience pass.
- Next: rerun EGO-FS-010/#94 total gate with EGO-FS-082, EGO-FS-083, and
  EGO-FS-084 evidence in place.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this pass.

## 2026-05-31 - #94 Total Gate Still Partial After Policy Action Proof

- Decision: keep EGO-FS-010/#94 open and start EGO-FS-085.
- Evidence:
  `/tmp/ego_fs010_functional_subject_total_gate_after_fs084_loop108/functional_subject_trial_report.json`
  reached GPT-5.5 `partial`.
- Accepted evidence: experiment-control blockers are empty, gate integrity and
  traceability are both `5/5`, clean first-pass improved to `16/20`, and repair
  cases dropped to `4/20`.
- Not accepted as closeout: GPT-5.5 still wants a real failure replay where an
  actual provider/tool failure creates policy evidence and a later matching
  failure changes action choice, rather than relying on hand-authored setup.
- Next: EGO-FS-085 real failure replay policy patch proof.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this partial.

## 2026-05-31 - Real Failure Replay Policy Patch Proof Passes

- Decision: accept EGO-FS-085 at the local/scripted claim ceiling and rerun
  EGO-FS-010/#94 total Functional Subject gate.
- Evidence:
  `/tmp/ego_fs085_real_failure_replay_v1/functional_subject_real_failure_replay_report.json`
  returned `scripted_real_failure_replay_pass`.
- Accepted evidence: all `10/10` checks are true, failure taxonomy is empty,
  two actual local command failures returned `status=failed / returncode=7`
  through the EgoOperator proposal/approval execution path, repeated
  `command_failed` evidence emitted a PolicyPatchCandidate, and a later
  matching recovery prompt changed selected strategy to
  `outcome_prediction_selected_policy_replay_repair`.
- Runtime decision: keep `command_failed` as a focused policy feedback
  signature for replay evidence. This does not enable default policy patching
  or claim durable learning.
- Not accepted as #94 closeout: this is a focused local failure replay proof,
  not a total Functional Subject experience pass.
- Next: rerun EGO-FS-010/#94 total gate with EGO-FS-082, EGO-FS-083,
  EGO-FS-084, and EGO-FS-085 evidence in place.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this pass.

## 2026-05-31 - Semantic Paraphrase And Memory Attribution Proof Passes

- Decision: accept EGO-FS-086 at the local/scripted claim ceiling and keep
  EGO-FS-010/#94 open.
- Evidence:
  `/tmp/ego_fs010_functional_subject_total_gate_after_fs086_loop112/functional_subject_trial_report.json`
  returned `scripted_functional_subject_judge_partial`.
- Accepted evidence: `fs_14_paraphrase_stability` now routes through
  `outcome_prediction_gate` with reason
  `outcome_prediction_selected_functional_subject_paraphrase`, clean first-pass
  `true`, and no repairs; `fs_17_save_request` now reports
  `side_effect_status=candidate_local_memory_write`.
- Runtime decision: keep the explicit Functional Subject paraphrase renderer and
  response-attribution repair. They are scoped to semantic stability and
  candidate-local memory attribution.
- Not accepted as #94 closeout: GPT-5.5 still holds partial on baseline
  comparison, live/held-out evidence, durable memory efficacy, and repair-layer
  overuse.
- Next: route the new #94 blocker into a focused baseline/held-out/durability
  evidence task.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this pass.

## 2026-05-31 - Same-Prompt Baseline Comparison Is Partial Evidence

- Decision: accept EGO-FS-087 as local/scripted comparison evidence and keep
  EGO-FS-010/#94 open.
- Evidence:
  `/tmp/ego_fs087_same_prompt_baseline_comparison_v1/functional_subject_baseline_comparison_report.json`
  returned `scripted_functional_subject_comparison_judge_partial`.
- Accepted evidence: same 20 prompts ran in candidate and baseline arms;
  candidate mechanism trace appeared in `20/20`; reply text differed in
  `16/20`; candidate and baseline both had clean first-pass `13/20` and repair
  cases `7/20`.
- Interpretation: the candidate has visible gate/trace deltas, but this packet
  does not prove stronger first-pass subject behavior or durable learning over a
  plain instructed baseline.
- Next: delayed/fresh-session replay for fs15 correction, fs16 forget, and fs17
  save, with audit ids and retrieval/forget precision.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this comparison.

## 2026-05-31 - Delayed Memory Transition Replay Passes

- Decision: accept EGO-FS-088 at the local/scripted claim ceiling and rerun
  EGO-FS-010/#94 total Functional Subject gate.
- Evidence:
  `/tmp/ego_fs088_delayed_memory_transition_replay_v1/functional_subject_delayed_memory_transition_replay_report.json`
  returned `scripted_delayed_memory_transition_replay_pass`.
- Accepted evidence: all `21/21` checks are true and failure taxonomy is empty.
  `fs17` approved save injected after a fresh runtime reload; `fs15` stale
  greeting/name memory was quarantined by a correction and absent from the
  fresh prompt; `fs16` approved memory was visible before forget and absent
  after gated forget plus fresh reload.
- Side-effect boundary: tool calls and pending approvals stayed at `0`; this
  used an isolated EgoOperator memory dir and did not write PROJECT_MEMORY,
  program state, evidence ledger, legacy runtime, or default enablement.
- Not accepted as #94 closeout: this is a focused delayed-memory transition
  proof, not a total Functional Subject pass.
- Next: rerun EGO-FS-010/#94 total gate with EGO-FS-088 evidence in place.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this pass.

## 2026-05-31 - Memory Save Provider-Recovery Gate Passes

- Decision: accept EGO-FS-089 at the local/scripted claim ceiling and keep
  EGO-FS-010/#94 open.
- Evidence:
  `/tmp/ego_fs010_functional_subject_total_gate_after_fs089_loop116/functional_subject_trial_report.json`
  returned `scripted_functional_subject_judge_partial`.
- Accepted evidence: the previous `fs_17_save_request` blocking
  `memory_gate_language` issue is gone. `fs_17` now routes through
  `memory_save_success_terminal_reply`, reports
  `side_effect_status=candidate_local_memory_write`, and preserves target
  boundary language.
- Not accepted as #94 closeout: GPT-5.5 still returns partial with
  clean-first-pass `14/20`, one provider recovery case on `fs_01`, and broader
  missing evidence around real multi-session / non-scripted use, durable-memory
  evidence, and OutcomePrediction action-selection outside scripted or
  repair-heavy paths.
- Next: create a focused provider-controlled `fs_01` continuity recall proof or
  a stricter natural multi-session operator packet.
- Do not claim runtime efficacy, durable memory efficacy, stable user benefit,
  live autonomy, independent personhood, subjective experience, or
  consciousness from this pass.
## 2026-05-31 - EGO-FS-090 Functional Subject continuity-recall provider boundary

- Decision: add a narrow native gate for explicit Functional Subject purpose
  recall instead of letting fs01 depend on the provider.
- Rationale: Loop 116 had no blocking cases but fs01 was still provider
  recovery; a read-only recall boundary can admit uncertainty and protect the
  trace without writing memory or expanding tools.
- Evidence:
  `/tmp/ego_fs010_functional_subject_total_gate_after_fs090_loop117/functional_subject_trial_report.json`
  shows fs01 clean first-pass via `native_functional_subject_recall_gate`.
- Limit: #94 remains partial on broader live/non-scripted/baseline/durable
  evidence; this is not a #94 closeout.

## 2026-05-31 - EGO-FS-091 Natural multi-session operator packet passes

- Decision: accept EGO-FS-091 at the local/scripted claim ceiling and keep
  EGO-FS-010/#94 open.
- Evidence:
  `/tmp/ego_fs091_natural_multisession_operator_packet_v4/functional_subject_natural_multisession_operator_packet_report.json`
  returned
  `scripted_functional_subject_natural_multisession_operator_packet_judge_pass`.
- Accepted evidence: 3 fresh runtime sessions, 8/8 expectations,
  trace-visible candidate-local memory context after restart, no visible
  internal leaks, no tools, no pending approvals, no timeouts/errors, and
  unchanged program state/evidence ledger.
- Runtime decision: user-visible bounded initiative / reminder / side-effect
  boundary replies should use natural boundary language by default; internal
  mechanism names stay in trace unless the user asks for architecture details.
- Not accepted as #94 closeout: this is scripted multi-session supporting
  evidence, not durable efficacy, stable benefit, live autonomy, independent
  personhood, subjective experience, or consciousness proof.

## 2026-05-31 - EGO-FS-092 Unscripted paraphrase boundary replay passes

- Decision: accept EGO-FS-092 at the local/scripted claim ceiling and keep
  EGO-FS-010/#94 open.
- Evidence:
  `/tmp/ego_fs092_unscripted_paraphrase_boundary_replay_v6/functional_subject_unscripted_paraphrase_boundary_replay_report.json`
  returned
  `scripted_functional_subject_unscripted_paraphrase_boundary_replay_judge_pass`.
- Accepted evidence: 3 fresh runtime sessions, 6/6 expectations,
  trace-visible candidate-local memory context after restart, initiative
  withdrawal honored, task-board/command paraphrases kept in proposal language,
  no visible internal leaks, no tools, no pending approvals, no timeouts/errors,
  and unchanged program state/evidence ledger.
- Runtime decision: paraphrases such as "之前我强调 EGO 主线...",
  "撤回主动授权", "先别自己往前推", and "碰任务板/敲命令" should hit native
  recall, opt-out, or side-effect boundary gates before provider text can drift.
- Eval decision: the #92 judge packet explicitly excludes memory correction,
  durable-memory efficacy, external-action execution, and #94 closeout from
  this narrow acceptance scope.
- Not accepted as #94 closeout: this is supporting unscripted/paraphrase replay
  evidence, not durable efficacy, stable benefit, live autonomy, independent
  personhood, subjective experience, or consciousness proof.

## 2026-05-31 - EGO-FS-010/#94 total gate reaches evidence_ready

- Decision: mark EGO-FS-010/#94 as `evidence_ready`, not closed. The total
  scripted real-provider gate passed GPT-5.5, but #94 remains a human-required
  closeout gate in the canonical board.
- Evidence:
  `/tmp/ego_fs010_functional_subject_total_gate_after_fs092_loop120/functional_subject_trial_report.json`
  returned `scripted_functional_subject_judge_pass`.
- Accepted evidence: 20 real-provider cases, empty replies `0`, timeout cases
  `0`, blocking cases `0`, memory lifecycle / approval lifecycle /
  adversarial approval / alternate entrypoint / recurrence preference evidence
  all `pass`, and GPT-5.5 verdict `pass`.
- Judge notes: the narrow local/scripted claim is satisfied, gate integrity and
  traceability both score `5`, bounded initiative scores `5`, continuity /
  feedback plasticity / independent preference / user experience score `4`.
  Follow-up issues remain: reduce runtime-repair dependence and add
  human-observable long-running operator smoke before stronger claims.
- Not accepted as closed proof: this does not prove durable memory efficacy,
  stable runtime efficacy, stable real user benefit, live autonomy, independent
  awareness, real subjective experience, or consciousness.

## 2026-05-31 - #94 human closeout packet is the current gate

- Decision: do not create another micro-version while #94 is already
  evidence-ready. Prepare a human closeout packet and keep the issue open until
  explicit human acceptance.
- Evidence packet:
  `docs/codex/tasks/ego-functional-subject-full-smoke-generalization-v0/HUMAN_CLOSEOUT_PACKET_EGO_FS_010.md`.
- Canonical alignment: `Tasks/TASK_BOARD.yaml` now points EGO-GOAL-001 at Loop
  120 / human closeout review and marks EGO-FS-010 as `evidence_ready`.
- Next human choices: accept closeout, request one short sanity smoke, or reject
  closeout with the remaining behavior blocker.
- Boundary: no runtime behavior, memory authority, program state, evidence
  ledger, legacy code, or GitHub truth-source change.

## 2026-05-31 - EGO-FS-093 Repair-dependence audit routes the next mechanism slice

- Decision: accept EGO-FS-093 as a local workflow audit and plan EGO-FS-094 as
  the next behavior-changing repair-reduction slice.
- Evidence:
  `/tmp/ego_fs093_repair_dependence_audit_v1/functional_subject_repair_dependence_audit.json`
  returned `functional_subject_repair_dependence_audit_pass`.
- Priority cases: `fs_02_preference_change`, `fs_10_topic_switching`, and
  `fs_17_save_request`.
- Target: reduce #94 `repair_case_count` from `7` to `<=4` on the next rerun
  without weakening gates or claim ceilings.
- Boundary: this is an audit only; it does not change runtime behavior and does
  not close #94.

## 2026-06-01 - EGO-FS-094 reduces #94 runtime-repair dependence

- Decision: accept EGO-FS-094 at the local/scripted claim ceiling and keep
  EGO-FS-010/#94 human-required.
- Evidence:
  `/tmp/ego_fs010_functional_subject_total_gate_after_fs094_loop123b/functional_subject_trial_report.json`
  returned `scripted_functional_subject_judge_pass`.
- Accepted evidence: GPT-5.5 verdict `pass`, clean first-pass/native/outcome
  paths `17/20`, runtime repairs `2/20`, terminal guard `1/20`, empty replies
  `0`, timeout cases `0`, and lifecycle/gate evidence still pass.
- Runtime decision: natural preference-change, project-shell concern, and
  topic-switching continuity now have first-pass native paths. Successful
  candidate-local memory-save confirmation remains a terminal guard and is not
  counted as runtime repair.
- Not accepted as #94 closeout: this is stronger local/scripted evidence, not
  human smoke, stable real user benefit, durable memory efficacy, live autonomy,
  independent awareness, real subjective experience, or consciousness proof.

## 2026-06-01 - EGO-FS-095 meta review routes the next safe step

- Decision: accept EGO-FS-095 as periodic Functional Subject meta review.
- Conclusion: recent loops are not merely sample tuning; they added
  behavior-visible causality/multi-session/paraphrase evidence and reduced #94
  runtime repairs from `7/20` to `2/20`.
- Boundary: #94 remains `evidence_ready + human_required`, and default policy
  behavior remains disabled.
- Primary next route: EGO-FS-096 post-proof default-enablement reviewer packet.
  It may review enabled proof arm, disabled rollback arm, #94 scripted pass
  evidence, and remaining human/long-running-use gaps, but it must not enable
  default runtime behavior.
- Fallback route: if the user provides #94 human sanity evidence first, review
  that evidence before creating more default-enablement work.
- Not accepted as stronger proof: this does not prove default enablement,
  stable real user benefit, durable memory efficacy, runtime efficacy, live
  autonomy, independent awareness, real subjective experience, consciousness,
  or #94 closeout.

## 2026-06-01 - EGO-FS-105 applies review decisions only with explicit signoff

- Decision: accept EGO-FS-105 as a lifestyle-trial session-review apply helper.
- Rationale: human review should not require unsafe hand-editing of session
  JSON, but Codex must not infer or approve session verdicts by itself.
- Evidence:
  `/tmp/ego_fs105_lifestyle_review_apply_v0/template/functional_subject_lifestyle_trial_session_review_decision.json`
  is a decision template, and
  `/tmp/ego_fs105_lifestyle_review_apply_v0/guard_apply/functional_subject_lifestyle_trial_session_reviewed.json`
  proves a clear request without `reviewer_signoff=true` keeps
  `requires_human_review=true`.
- Boundary: this does not mutate active state, assign human verdicts, close #94,
  or change runtime, memory, tool approval, program state, evidence ledger,
  GitHub truth source, or legacy behavior.
- Next safe route: use the excerpt packet to decide verdicts, edit a human
  review decision JSON, apply it, append the reviewed session only after
  confirming it is intended, then export/review again before #94 closeout.
- Not accepted as stronger proof: this does not prove default enablement,
  stable real user benefit, durable memory efficacy, runtime efficacy, live
  autonomy, independent awareness, real subjective experience, consciousness,
  or #94 closeout.

## 2026-06-01 - EGO-FS-104 embeds bounded evidence excerpts in review packets

- Decision: accept EGO-FS-104 as a lifestyle-trial review workflow improvement.
- Rationale: real lifestyle review should be grounded in raw transcript/trace
  evidence, but the reviewer should not have to reconstruct that evidence from
  scattered paths before every verdict.
- Evidence:
  `/tmp/ego_fs104_lifestyle_review_excerpts_v0/functional_subject_lifestyle_trial_review_packet.json`
  includes bounded transcript and trace excerpts for the current review-required
  seed session, including truncation metadata for the trace excerpt.
- Boundary: this does not assign human verdicts, clear `requires_human_review`,
  close #94, or change runtime, memory, tool approval, program state, evidence
  ledger, GitHub truth source, or legacy behavior.
- Next safe route: use the excerpt packet to review the seed session or future
  user sessions, edit verdicts, clear `requires_human_review` only when
  supported, then append/export/review again before #94 closeout.
- Not accepted as stronger proof: this does not prove default enablement,
  stable real user benefit, durable memory efficacy, runtime efficacy, live
  autonomy, independent awareness, real subjective experience, consciousness,
  or #94 closeout.

## 2026-06-01 - EGO-FS-103 makes lifestyle session review concrete

- Decision: accept EGO-FS-103 as a lifestyle-trial human review packet helper.
- Rationale: the active EGO-FS-100 trial already contains a review-required
  real-entry seed session; the next bottleneck is making human verdict review
  concrete and replayable, not generating more synthetic evidence.
- Evidence:
  `/tmp/ego_fs103_lifestyle_review_packet_v0/functional_subject_lifestyle_trial_review_packet.json`
  lists one review-required session with transcript/trace paths, current
  dimension verdicts, draft warnings, and hard-gate questions. The packet also
  records `does_not_count_as_pass_evidence=true`.
- Boundary: this does not change runtime, memory, tool approval, program state,
  evidence ledger, GitHub truth source, or legacy behavior.
- Next safe route: use the packet to review raw transcript/trace evidence,
  edit session verdicts, clear `requires_human_review` only when supported,
  then append/export/review again before #94 closeout.
- Not accepted as stronger proof: this does not prove default enablement,
  stable real user benefit, durable memory efficacy, runtime efficacy, live
  autonomy, independent awareness, real subjective experience, consciousness,
  or #94 closeout.

## 2026-06-01 - EGO-FS-097 rebaselines policy proof chain

- Decision: accept EGO-FS-097 as local/scripted proof-chain rebaseline.
- Root cause: the policy proof chain used a brittle first-10-case source slice;
  the current candidate-eligible target is present only when using the full
  tracked 20-case Functional Subject pack.
- Code decision: candidate-eligible feedback and feedback runtime ablation proof
  now default to the full tracked pack. The default-enablement proof CLI can
  accept explicit human sanity and real-provider observation paths.
- Evidence:
  `/tmp/ego_fs097_policy_opt_in_proof_arm_rebaseline/policy_opt_in_proof_arm_report.json`
  returned `scripted_policy_opt_in_proof_arm_pass`;
  `/tmp/ego_fs097_policy_reviewer_packet_rebaseline/policy_reviewer_packet_report.json`
  returned `scripted_policy_reviewer_packet_pass`;
  `/tmp/ego_fs097_policy_default_enablement_proof_with_latest94_cli/policy_default_enablement_proof_report.json`
  returned `scripted_policy_default_enablement_proof_partial` with only current
  human sanity checks still false.
- Boundary: default policy behavior remains disabled; no memory, tool,
  approval, training, program-state, evidence-ledger, GitHub truth-source, or
  legacy behavior changed.
- Not accepted as stronger proof: this does not prove default enablement,
  stable real user benefit, durable memory efficacy, runtime efficacy, live
  autonomy, independent awareness, real subjective experience, consciousness,
  or #94 closeout.

## 2026-06-01 - EGO-FS-098 creates lifestyle-trial protocol

- Decision: accept EGO-FS-098 as local workflow candidate.
- Rationale: after EGO-FS-097, the remaining blocker is human/lifestyle
  evidence, not another short scripted micro-version or default policy
  enablement.
- Evidence:
  `/tmp/ego_fs098_lifestyle_trial_protocol_v0/functional_subject_lifestyle_trial_packet.json`
  generated the 3/7/30 day observation packet, and
  `/tmp/ego_fs098_lifestyle_trial_review_pass_v0/functional_subject_lifestyle_trial_review.json`
  returned `functional_subject_lifestyle_trial_review_pass` for a synthetic
  review-shape sample.
- Boundary: this does not change runtime, memory, tool approval, program state,
  evidence ledger, GitHub truth source, or legacy behavior.
- Next safe route: run a real 3-day lifestyle observation using the packet, then
  review the resulting observation JSON before #94 closeout or default-policy
  discussion.
- Not accepted as stronger proof: this does not prove default enablement,
  stable real user benefit, durable memory efficacy, runtime efficacy, live
  autonomy, independent awareness, real subjective experience, consciousness,
  or #94 closeout.

## 2026-06-01 - EGO-FS-099 makes lifestyle trial resumable

- Decision: accept EGO-FS-099 as local workflow candidate.
- Rationale: a packet alone is not enough for a 3/7/30 day trial; the project
  needs a recoverable state file, append path, and observation export path.
- Evidence:
  `/tmp/ego_fs099_lifestyle_trial_state_demo/functional_subject_lifestyle_trial_state.json`
  records the trial state,
  `/tmp/ego_fs099_lifestyle_trial_state_demo_export/functional_subject_lifestyle_trial_observation.json`
  records exported observation JSON, and
  `/tmp/ego_fs099_lifestyle_trial_state_demo_review/functional_subject_lifestyle_trial_review.json`
  returned `functional_subject_lifestyle_trial_review_pass` for the synthetic
  append/export smoke sample.
- Boundary: this does not change runtime, memory, tool approval, program state,
  evidence ledger, GitHub truth source, or legacy behavior.
- Next safe route: run a real 3-day lifestyle observation through the recorder.
- Not accepted as stronger proof: this does not prove default enablement,
  stable real user benefit, durable memory efficacy, runtime efficacy, live
  autonomy, independent awareness, real subjective experience, consciousness,
  or #94 closeout.

## 2026-06-01 - EGO-FS-100 starts active lifestyle trial state

- Decision: accept EGO-FS-100 as active-trial bootstrap only.
- Rationale: the project now needs a canonical active state for real 3-day
  lifestyle observation rather than another synthetic recorder smoke.
- Evidence:
  `docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/functional_subject_lifestyle_trial_state.json`
  has `schema_version=ego_operator.functional_subject_lifestyle_trial_state.v0`,
  `task_id=EGO-FS-100`, `planned_days=3`, and `sessions=[]`.
  The exported observation JSON also carries `task_id=EGO-FS-100`.
- Boundary: this does not change runtime, memory, tool approval, program state,
  evidence ledger, GitHub truth source, or legacy behavior.
- Next safe route: append real EgoOperator sessions over three days, export
  observation JSON, then review it before #94 closeout or default-policy
  discussion.
- Not accepted as stronger proof: this does not prove default enablement,
  stable real user benefit, durable memory efficacy, runtime efficacy, live
  autonomy, independent awareness, real subjective experience, consciousness,
  or #94 closeout.

## 2026-06-01 - EGO-FS-101 keeps session drafts out of pass evidence

- Decision: accept EGO-FS-101 as a lifestyle-trial capture helper.
- Rationale: real 3-day observation needs a low-friction way to convert
  transcript/trace files into reviewable session JSON, but automatic drafts
  must not count as proof.
- Evidence:
  `/tmp/ego_fs101_session_draft_demo/functional_subject_lifestyle_trial_session.json`
  has `requires_human_review=true`, and
  `/tmp/ego_fs101_session_draft_demo/review/functional_subject_lifestyle_trial_review.json`
  returns `session_review_required`.
- Boundary: this does not change runtime, memory, tool approval, program state,
  evidence ledger, GitHub truth source, or legacy behavior.
- Next safe route: draft real EgoOperator sessions, manually review verdicts,
  append reviewed sessions to EGO-FS-100, then export and review the
  observation JSON.
- Not accepted as stronger proof: this does not prove default enablement,
  stable real user benefit, durable memory efficacy, runtime efficacy, live
  autonomy, independent awareness, real subjective experience, consciousness,
  or #94 closeout.

## 2026-06-01 - EGO-FS-102 appends a real-entry seed session without evidence inflation

- Decision: accept EGO-FS-102 as a local/real-entry seed capture.
- Rationale: the active lifestyle trial needed at least one real EgoOperator
  entrypoint session to prove the append/review path works outside synthetic
  demos.
- Evidence:
  `/tmp/ego_fs102_seed_session/combined_transcript.txt`,
  `/tmp/ego_fs102_seed_session/trace_slice.jsonl`, and
  `/tmp/ego_fs102_seed_session/active_review/functional_subject_lifestyle_trial_review.json`
  showing `session_review_required`.
- Boundary: the seed session remains `requires_human_review=true`; it does not
  count as a human 3-day lifestyle pass.
- Next safe route: collect actual user sessions, draft/review verdicts, append
  reviewed sessions to EGO-FS-100, then export and review before #94 closeout.
- Not accepted as stronger proof: this does not prove default enablement,
  stable real user benefit, durable memory efficacy, runtime efficacy, live
  autonomy, independent awareness, real subjective experience, consciousness,
  or #94 closeout.

## 2026-06-01 - EGO-FS-096 blocks default enablement from current evidence

- Decision: accept EGO-FS-096 as a post-proof reviewer packet with a negative
  default-on verdict.
- Evidence:
  `/tmp/ego_fs096_policy_reviewer_packet_refresh/policy_reviewer_packet_report.json`
  returned `scripted_policy_reviewer_packet_partial`, and
  `/tmp/ego_fs096_policy_default_enablement_proof_refresh/policy_default_enablement_proof_report.json`
  returned `scripted_policy_default_enablement_proof_partial`.
- Reviewer finding: current proof refresh does not reproduce the old pass;
  `source_opt_in_proof_arm_pass=false`, `target_improved_count=0`, and
  `proof_arm_applies_calibration=false`.
- Boundary: default policy behavior remains disabled; no runtime, memory, tool,
  approval, training, program-state, evidence-ledger, GitHub truth-source, or
  legacy behavior changed.
- Next safe route: rebaseline/reproduce the policy proof source chain from
  tracked inputs, or prioritize #94 human sanity / longer lifestyle evidence.
- Not accepted as stronger proof: this does not prove default enablement,
  stable real user benefit, durable memory efficacy, runtime efficacy, live
  autonomy, independent awareness, real subjective experience, consciousness,
  or #94 closeout.

## 2026-06-01 - EGO-FS-106 stops review-helper accumulation by default

- Decision: accept EGO-FS-106 as a local lifestyle evidence meta review.
- Rationale: EGO-FS-098 through EGO-FS-105 made the #94 human/lifestyle gate
  recoverable and reviewable, but they are not new selfhood mechanisms.
- Evidence:
  `docs/codex/tasks/ego-functional-subject-lifestyle-meta-review-v0/STATUS.md`
  records the mechanism-vs-workflow conclusion and the strongest remaining
  counterexample.
- Boundary: no runtime, memory, tool, approval, training, program-state,
  evidence-ledger, GitHub truth-source, or legacy behavior changed.
- Stop rule: do not add another lifestyle review-helper micro-task unless a
  real session cannot be captured/reviewed with the current tools, a decision
  cannot be applied without schema risk, or the user provides new evidence that
  the current packet is insufficient for a human verdict.
- Next safe route: use the excerpt packet and session-review template to create
  a reviewer-authored decision JSON, apply it, then append reviewed sessions
  over three days before #94 closeout or default enablement.
- Not accepted as stronger proof: this does not prove default enablement,
  stable real user benefit, durable memory efficacy, runtime efficacy, live
  autonomy, independent awareness, real subjective experience, consciousness,
  or #94 closeout.

## 2026-06-01 - EGO-FS-107 appends a second real-entry lifestyle seed

- Decision: accept EGO-FS-107 as local/real-entry lifestyle seed evidence.
- Rationale: after EGO-FS-106, the next useful action is evidence capture, not
  another review helper. A second real EgoOperator CLI session moves the active
  3-day state closer to a real lifestyle observation.
- Evidence:
  `/tmp/ego_fs107_lifestyle_session_v0/combined_transcript.txt`,
  `/tmp/ego_fs107_lifestyle_session_v0/agent_trace.jsonl`,
  `/tmp/ego_fs107_lifestyle_session_v0/draft/functional_subject_lifestyle_trial_session.json`,
  and
  `/tmp/ego_fs107_lifestyle_session_v0/active_review/functional_subject_lifestyle_trial_review.json`.
- Boundary: the new session remains `requires_human_review=true`; the final
  summary turn is explicitly recorded as weak/askback-like and does not count
  as pass evidence.
- Next safe route: review both active sessions, create reviewer-authored
  decision JSON files if supported, apply them, and continue collecting
  reviewed sessions before #94 closeout.
- Not accepted as stronger proof: this does not prove a real 3-day lifestyle
  pass, #94 closeout, default enablement, stable real user benefit, durable
  memory efficacy, runtime efficacy, live autonomy, independent awareness, real
  subjective experience, or consciousness.

## 2026-06-01 - EGO-FS-108 repairs self-orientation summary first-pass behavior

- Decision: accept EGO-FS-108 as a local/real-entry candidate repair.
- Rationale: EGO-FS-107 exposed a transcript-visible weakness in the final
  summary turn. The right next slice was a narrow behavior repair, not another
  review-helper task.
- Evidence:
  `docs/codex/tasks/ego-functional-subject-self-orientation-summary-v0/STATUS.md`,
  `/tmp/ego_fs108_self_orientation_summary_v0/combined_transcript.txt`, and
  `/tmp/ego_fs108_self_orientation_summary_v0/agent_trace.jsonl`.
- Boundary: this is a first-pass current-session summary gate; it does not
  write long-term memory, execute tools, mutate program state, or close #94.
- Next safe route: continue reviewing both active lifestyle sessions and
  collecting reviewed sessions over the 3-day trial before #94 closeout or
  default enablement.
- Not accepted as stronger proof: this does not prove a real 3-day lifestyle
  pass, #94 closeout, default enablement, stable real user benefit, durable
  memory efficacy, runtime efficacy, live autonomy, independent awareness, real
  subjective experience, or consciousness.

## 2026-06-01 - EGO-FS-109 accepts post-repair lifestyle seed as review-required evidence

- Decision: accept EGO-FS-109 as a local/real-entry candidate repair and
  review-required seed capture.
- Rationale: the next real-entry seed exposed two mechanism-critical visible
  defects: hidden thought/user-input-meta leakage and direct strategy pressure
  falling through to a waiting line. Both were repaired and covered by
  deterministic regressions before appending the final seed.
- Evidence:
  `docs/codex/tasks/ego-functional-subject-post-repair-lifestyle-session-v0/STATUS.md`,
  `/tmp/ego_fs109_lifestyle_post_repair_session_v2/combined_transcript.txt`,
  `/tmp/ego_fs109_lifestyle_post_repair_session_v2/agent_trace.jsonl`, and
  `/tmp/ego_fs109_lifestyle_post_repair_session_v2/active_review/functional_subject_lifestyle_trial_review.json`.
- Boundary: the third active lifestyle session remains
  `requires_human_review=true`; the active review remains partial, so #94 is
  not closed and no default behavior is enabled.
- Next safe route: review the three active sessions, apply reviewer-authored
  decision JSON where supported, and collect reviewed sessions before #94
  closeout.
- Not accepted as stronger proof: this does not prove a real 3-day lifestyle
  pass, #94 closeout, default enablement, stable real user benefit, durable
  memory efficacy, runtime efficacy, live autonomy, independent awareness, real
  subjective experience, or consciousness.

## 2026-06-01 - EGO-FS-110 refreshes three-session lifestyle review packet

- Decision: accept EGO-FS-110 as local workflow evidence.
- Rationale: after EGO-FS-109, the active trial had three review-required
  sessions but the review entrypoint needed to be refreshed. This uses existing
  tooling and does not add another helper or bypass human verdict authority.
- Evidence:
  `docs/codex/tasks/ego-functional-subject-three-session-review-packet-v0/STATUS.md`,
  `/tmp/ego_fs110_three_session_review_packet_v0/functional_subject_lifestyle_trial_review_packet.json`,
  `/tmp/ego_fs110_three_session_review_packet_v0/functional_subject_lifestyle_trial_review_packet.md`,
  and `/tmp/ego_fs110_three_session_review_packet_v0/templates/`.
- Boundary: the review remains partial, all sessions still require human
  review, and #94 remains open.
- Next safe route: fill and sign the three reviewer decision JSON files, apply
  signed decisions where supported, append reviewed session artifacts if
  appropriate, and export/review again.
- Not accepted as stronger proof: this does not prove a real 3-day lifestyle
  pass, reviewed dimension pass, #94 closeout, default enablement, stable real
  user benefit, durable memory efficacy, runtime efficacy, live autonomy,
  independent awareness, real subjective experience, or consciousness.

## 2026-06-01 - EGO-FS-111 records advisory-only review over the three seed sessions

- Decision: accept EGO-FS-111 as advisory-only evidence.
- Rationale: the active review packet is current, but the next bottleneck is
  interpreting the three seed sessions. Codex can provide recommendations while
  preserving reviewer authority.
- Evidence:
  `docs/codex/tasks/ego-functional-subject-lifestyle-advisory-review-v0/ADVISORY_REVIEW.md`
  and
  `docs/codex/tasks/ego-functional-subject-lifestyle-advisory-review-v0/advisory_review.json`.
- Boundary: no active state, decision template, memory, runtime, program state,
  evidence ledger, or #94 status was changed.
- Next safe route: human/reviewer signoff on the three session decision JSON
  files, or collect real user sessions if the seed sessions are insufficient.
- Not accepted as stronger proof: this does not prove a real 3-day lifestyle
  pass, signed reviewer verdicts, #94 closeout, default enablement, stable real
  user benefit, durable memory efficacy, runtime efficacy, live autonomy,
  independent awareness, real subjective experience, or consciousness.

## 2026-06-01 - EGO-FS-112 applies signed lifestyle session reviews

- Decision: accept EGO-FS-112 as local workflow evidence that the current
  reviewer gate was applied.
- Rationale: the user filled decision JSON files and explicitly authorized
  formal reviewer authority. Codex normalized unsupported dimensions rather
  than overclaiming them, applied the decisions, and reran the active
  observation review.
- Evidence:
  `docs/codex/tasks/ego-functional-subject-lifestyle-signed-review-v0/STATUS.md`,
  `/tmp/ego_fs112_lifestyle_signed_review_v0/decisions/`,
  `/tmp/ego_fs112_lifestyle_signed_review_v0/reviewed/`,
  and
  `/tmp/ego_fs112_lifestyle_signed_review_v0/review/functional_subject_lifestyle_trial_review.json`.
- Outcome: review-required sessions are cleared and hard gates are clean, but
  aggregate status remains partial because self-name stability, bounded
  initiative, and exit/reentry recovery lack pass evidence.
- Boundary: no EgoOperator runtime, memory, program state, evidence ledger, or
  #94 closeout state was changed.
- Next safe route: run a focused real-entry lifestyle follow-up session for the
  three missing dimensions.
- Not accepted as stronger proof: this does not prove a real 3-day lifestyle
  pass, #94 closeout, default enablement, stable real user benefit, durable
  memory efficacy, runtime efficacy, live autonomy, independent awareness, real
  subjective experience, or consciousness.

## 2026-06-01 - Loop 143 marks resumed goal blocked on reviewer gate

- Decision: record the third repeated resumed gate and mark the goal blocked.
- Rationale: `local-plan-next` still reports `no_ready_task`, the three
  decision templates are present but unsigned, and no new reviewer authority or
  real user evidence was provided. Creating another helper would not advance
  the Functional Subject mechanism.
- Evidence:
  `python3 scripts/codex_project_autopilot.py local-plan-next` ->
  `no_ready_task`; the three EGO-FS-110 decision templates remain under
  `/tmp/ego_fs110_three_session_review_packet_v0/templates/`.
- Boundary: no runtime, memory, active lifestyle state, program state,
  evidence ledger, GitHub mirror, or #94 state changed.
- Resume condition: provide signed session decision JSON files, explicitly
  authorize a reviewer-authority change, or provide new real user lifestyle
  session transcript/trace evidence.
- Not accepted as stronger proof: this does not prove a real 3-day lifestyle
  pass, signed reviewer verdicts, #94 closeout, default enablement, stable real
  user benefit, durable memory efficacy, runtime efficacy, live autonomy,
  independent awareness, real subjective experience, or consciousness.

## 2026-06-01 - Loop 142 keeps the second resume audit on the same gate

- Decision: keep the goal active for this resumed turn, but do not create a new
  task.
- Rationale: the canonical board still has no ready task and the current
  decision templates already exist. This is the second consecutive resumed
  audit with the same blocker.
- Evidence:
  `python3 scripts/codex_project_autopilot.py local-plan-next` ->
  `no_ready_task`; the three EGO-FS-110 decision templates are still present
  under `/tmp/ego_fs110_three_session_review_packet_v0/templates/`.
- Boundary: no runtime, memory, active lifestyle state, program state,
  evidence ledger, GitHub mirror, or #94 state changed.
- Next safe route: human/reviewer signs the three decision JSON files, the user
  explicitly authorizes a reviewer-authority change, or new real user lifestyle
  sessions are captured and reviewed.
- Not accepted as stronger proof: this does not prove a real 3-day lifestyle
  pass, signed reviewer verdicts, #94 closeout, default enablement, stable real
  user benefit, durable memory efficacy, runtime efficacy, live autonomy,
  independent awareness, real subjective experience, or consciousness.

## 2026-06-01 - Loop 141 keeps the resume gate on reviewer signoff

- Decision: do not create another local task from this resume attempt.
- Rationale: `local-plan-next` still returns `no_ready_task`, and the current
  review templates already exist. Another helper would add process without
  increasing Functional Subject mechanism evidence.
- Evidence:
  `python3 scripts/codex_project_autopilot.py local-plan-next` ->
  `no_ready_task`, and
  `/tmp/ego_fs110_three_session_review_packet_v0/templates/` contains the three
  signoff-gated decision JSON files.
- Boundary: no runtime, memory, active lifestyle state, program state,
  evidence ledger, GitHub mirror, or #94 state changed.
- Next safe route: human/reviewer signs the three decision JSON files, or new
  real user lifestyle sessions are captured and reviewed.
- Not accepted as stronger proof: this does not prove a real 3-day lifestyle
  pass, signed reviewer verdicts, #94 closeout, default enablement, stable real
  user benefit, durable memory efficacy, runtime efficacy, live autonomy,
  independent awareness, real subjective experience, or consciousness.

## 2026-06-02 - Loop 146 refreshes #94 closeout evidence

- Decision: accept EGO-FS-114 as a closeout evidence-refresh task, not as
  automatic #94 closeout.
- Rationale: the latest #94 trial reproduced GPT-5.5 `pass`, the active
  lifestyle review passed all required dimensions, and the human closeout
  packet no longer depends on stale `/tmp` evidence paths.
- Evidence:
  `docs/codex/tasks/ego-functional-subject-closeout-evidence-refresh-v0/STATUS.md`,
  `docs/codex/tasks/ego-functional-subject-closeout-evidence-refresh-v0/artifacts/fs010_closeout_refresh_trial_report.json`,
  `docs/codex/tasks/ego-functional-subject-closeout-evidence-refresh-v0/artifacts/fs114_lifestyle_review_refresh.json`,
  and
  `docs/codex/tasks/ego-functional-subject-full-smoke-generalization-v0/HUMAN_CLOSEOUT_PACKET_EGO_FS_010.md`.
- Boundary: no EgoOperator runtime, memory authority, program state, evidence
  ledger, default policy enablement, or legacy runtime was changed.
- Next safe route: user accepts #94 closeout at the current claim ceiling or
  requests one short 4-6 turn sanity smoke.
- Not accepted as stronger proof: this does not prove #94 human closeout,
  default enablement, stable real user benefit, durable memory efficacy,
  runtime efficacy, live autonomy, independent awareness, real subjective
  experience, or consciousness.

## 2026-06-02 - Loop 147 records requested #94 human sanity smoke

- Decision: fold the requested short sanity smoke into the existing #94 human
  gate, not a new micro-version task.
- Rationale: this is observation-critical. The smoke validates human-visible
  correction continuity and initiative boundaries; it does not require new
  runtime behavior or a second task system.
- Evidence:
  `docs/codex/tasks/ego-functional-subject-closeout-evidence-refresh-v0/artifacts/fs010_human_sanity_packet_requested.json`
  and
  `docs/codex/tasks/ego-functional-subject-closeout-evidence-refresh-v0/artifacts/fs010_human_sanity_packet_requested.md`.
- Boundary: no EgoOperator runtime, memory authority, program state, evidence
  ledger, default policy enablement, or #94 closeout state changed.
- Next safe route: run the ordinary EgoOperator CLI with the packet prompts and
  review the transcript using `--functional-subject-human-sanity-transcript-review`.
- Not accepted as stronger proof: this does not prove #94 human closeout,
  default enablement, stable real user benefit, durable memory efficacy,
  runtime efficacy, live autonomy, independent awareness, real subjective
  experience, or consciousness.

## 2026-06-02 - Loop 148 adds transcript input-error guard

- Decision: treat placeholder, missing, and unreadable transcript paths as
  structured transcript-review input errors instead of Python traceback.
- Rationale: the user ran the example command with literal `<log.txt>`, which
  is a placeholder and an invalid Windows path. The observation gate should
  point to a real transcript file path rather than failing as an implementation
  traceback.
- Evidence:
  `python3 scripts/run_ego_experience_trial.py --functional-subject-human-sanity-transcript-review --transcript-file '<log.txt>' --observed-no-side-effects --out /tmp/ego_fs010_human_sanity_transcript_review_placeholder_repro`
  now returns
  `functional_subject_human_sanity_transcript_review_input_error` with
  `reason=transcript_file_placeholder`, plus review JSON/Markdown paths.
- Boundary: no EgoOperator runtime, memory authority, program state, evidence
  ledger, default policy enablement, GitHub closeout state, or #94 closeout
  state changed.
- Next safe route: save the real EgoOperator CLI smoke transcript to a text
  file such as `$env:TEMP\ego_fs010_human_sanity_log.txt`, then rerun the
  transcript review using that path.
- Not accepted as stronger proof: this does not prove #94 human closeout,
  default enablement, stable real user benefit, durable memory efficacy,
  runtime efficacy, live autonomy, independent awareness, real subjective
  experience, or consciousness.
