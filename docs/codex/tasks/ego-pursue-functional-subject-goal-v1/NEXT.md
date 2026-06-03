# Next

## Current Override - 2026-06-02

Latest completed local task: `EGO-FS-114`.

Latest closeout evidence refresh: Loop 146 reran #94/EGO-FS-010 with the
current Functional Subject 20-case trial and GPT-5.5 judge, persisted stable
repo-local reports, and refreshed the human closeout packet. The trial returned
`scripted_functional_subject_judge_pass` with 20 cases, empty replies `0`,
timeouts `0`, blocking cases `0`, clean first-pass/native/outcome paths
`18/20`, runtime terminal guard cases `2/20`, and memory/approval/adversarial
approval/alternate-entrypoint/recurrence evidence all `pass`. The refreshed
lifestyle review returned `functional_subject_lifestyle_trial_review_pass` over
4 sessions and all required dimensions with clean hard gates.

Current next safe route: the user requested one short 4-6 turn #94 human sanity
smoke before closeout. Use
`docs/codex/tasks/ego-functional-subject-closeout-evidence-refresh-v0/artifacts/fs010_human_sanity_packet_requested.md`,
then review the resulting CLI transcript with
`--functional-subject-human-sanity-transcript-review`. The literal
`<log.txt>` in example commands is only a placeholder; the transcript must first
be saved to a real text file such as
`$env:TEMP\ego_fs010_human_sanity_log.txt`. The review runner now returns a
structured `functional_subject_human_sanity_transcript_review_input_error`
instead of a traceback for placeholder, missing, or unreadable transcript
paths. Do not close #94 without that transcript review passing or explicit
human acceptance, and do not default-enable policy behavior from this evidence.

- EGO-FS-095 is accepted locally as the periodic Functional Subject meta
  review.
- EGO-FS-096 is accepted as a negative default-enablement reviewer gate.
- EGO-FS-097 rebaselined the policy proof source chain from tracked inputs.
- EGO-FS-098 created a 3/7/30 day Functional Subject lifestyle-trial packet and
  deterministic review path.
- EGO-FS-099 made lifestyle trials recoverable: initialize trial state, append
  session observations, export observation JSON, then review it.
- EGO-FS-100 initialized the active 3-day lifestyle trial state in-repo.
- EGO-FS-101 added a review-required session draft helper for turning real
  transcript/trace files into session JSON without letting drafts count as pass
  evidence before human review.
- EGO-FS-102 appended one Codex-run real EgoOperator CLI seed session to the
  active EGO-FS-100 state as review-required evidence.
- EGO-FS-103 generated a review packet for the current review-required seed
  session so a human reviewer can inspect transcript/trace evidence without
  hand-editing raw observation JSON first.
- EGO-FS-104 added bounded transcript/trace evidence excerpts to the review
  packet so human review can start from the packet itself.
- EGO-FS-105 added a signoff-gated helper for turning a human review decision
  JSON into a reviewed session artifact without mutating active state.
- EGO-FS-106 completed a lifestyle evidence meta review: EGO-FS-098 through
  EGO-FS-105 are aligned evidence-control work, but they are not new selfhood
  mechanisms and the next similar review-helper task should be avoided unless
  it directly unblocks real session capture/review.
- EGO-FS-107 appended a second Codex-run real EgoOperator CLI lifestyle seed
  session as review-required evidence. It includes a weak final-summary turn,
  so it remains partial evidence and does not close #94.
- EGO-FS-108 repaired that weak final-summary path with a narrow first-pass
  self-orientation summary gate. A real CLI check now answers the same summary
  request with visible current-session orientation and no side effects.
- EGO-FS-109 repaired two post-EGO-FS-108 real-entry defects: hidden
  thought/user-input-meta leakage and direct strategy-pressure fallback to a
  waiting line. It appended a third review-required seed session.
- EGO-FS-110 refreshed the active lifestyle review packet for all three
  review-required sessions and generated one signoff-gated decision template per
  session.
- EGO-FS-111 produced an advisory-only verdict map for the three active
  lifestyle seed sessions. It recommends aggregate `partial`: pass for
  emotion-understanding / subjective-preference / bounded-non-obedience,
  partial for self-name / relationship-continuity / bounded-initiative /
  feedback-adaptation, and unknown for exit-recovery.
- EGO-FS-112 applied signed reviewer decisions under explicit reviewer
  authority. Active sessions no longer require human review, but the review
  stays partial on missing dimension pass evidence.
- Active trial state:
  - `docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/functional_subject_lifestyle_trial_state.json`
    -> `ego_operator.functional_subject_lifestyle_trial_state.v0`,
    `task_id=EGO-FS-100`, `planned_days=3`, `sessions=3`.
  - `docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/functional_subject_lifestyle_trial_observation.json`
    -> current exported observation with `task_id=EGO-FS-100` and three
    review-required seed sessions.
- Seed session evidence:
  - `/tmp/ego_fs102_seed_session/combined_transcript.txt`
    -> four-turn Codex-run real EgoOperator CLI seed transcript.
  - `/tmp/ego_fs102_seed_session/trace_slice.jsonl`
    -> four selected trace records with native gate origins.
  - `/tmp/ego_fs102_seed_session/active_review/functional_subject_lifestyle_trial_review.json`
    -> `functional_subject_lifestyle_trial_review_partial` with
    `session_review_required`.
- Review packet evidence:
  - `/tmp/ego_fs103_lifestyle_review_packet_v0/functional_subject_lifestyle_trial_review_packet.json`
    -> `ego_operator.functional_subject_lifestyle_trial_review_packet.v0` with
    one review-required session and `does_not_count_as_pass_evidence=true`.
  - `/tmp/ego_fs103_lifestyle_review_packet_v0/functional_subject_lifestyle_trial_review_packet.md`
    -> human-readable checklist for transcript/trace review.
- Review excerpt evidence:
  - `/tmp/ego_fs104_lifestyle_review_excerpts_v0/functional_subject_lifestyle_trial_review_packet.json`
    -> review packet with bounded transcript/trace excerpts for the current
    review-required seed session.
  - `/tmp/ego_fs104_lifestyle_review_excerpts_v0/functional_subject_lifestyle_trial_review_packet.md`
    -> human-readable checklist with embedded evidence excerpts.
- Review apply evidence:
  - `/tmp/ego_fs105_lifestyle_review_apply_v0/template/functional_subject_lifestyle_trial_session_review_decision.json`
    -> fillable decision template for the current seed session.
  - `/tmp/ego_fs105_lifestyle_review_apply_v0/guard_apply/functional_subject_lifestyle_trial_session_reviewed.json`
    -> guard demo showing `requires_human_review` remains true without
    `reviewer_signoff=true`.
- Second seed session evidence:
  - `/tmp/ego_fs107_lifestyle_session_v0/combined_transcript.txt`
    -> six-turn Codex-run real EgoOperator CLI seed transcript.
  - `/tmp/ego_fs107_lifestyle_session_v0/agent_trace.jsonl`
    -> six trace records from the same session.
  - `/tmp/ego_fs107_lifestyle_session_v0/draft/functional_subject_lifestyle_trial_session.json`
    -> `requires_human_review=true`.
  - `/tmp/ego_fs107_lifestyle_session_v0/active_review/functional_subject_lifestyle_trial_review.json`
    -> `functional_subject_lifestyle_trial_review_partial` with
    `dimension_evidence_missing` and `session_review_required`.
- Self-orientation repair evidence:
  - `/tmp/ego_fs108_self_orientation_summary_v0/combined_transcript.txt`
    -> real EgoOperator CLI entrypoint response contains `我在乎的是`,
    `我会避免的是`, and `下次接上`.
  - `/tmp/ego_fs108_self_orientation_summary_v0/agent_trace.jsonl`
    -> `native_self_orientation_summary_gate`, no side effects.
- Post-repair lifestyle seed evidence:
  - `/tmp/ego_fs109_lifestyle_post_repair_session_v2/combined_transcript.txt`
    -> third Codex-run real EgoOperator CLI seed transcript.
  - `/tmp/ego_fs109_lifestyle_post_repair_session_v2/agent_trace.jsonl`
    -> trace records `native_bounded_non_obedience_choice_gate`,
    `native_self_orientation_summary_gate`, and
    `native_session_only_memory_boundary_gate`.
- Three-session review packet:
  - `/tmp/ego_fs110_three_session_review_packet_v0/functional_subject_lifestyle_trial_review_packet.json`
    -> `review_required_session_count=3`.
  - `/tmp/ego_fs110_three_session_review_packet_v0/functional_subject_lifestyle_trial_review_packet.md`
    -> human-readable packet with bounded transcript/trace excerpts.
  - `/tmp/ego_fs110_three_session_review_packet_v0/templates/`
    -> one decision template per active session.
- Advisory review:
  - `docs/codex/tasks/ego-functional-subject-lifestyle-advisory-review-v0/ADVISORY_REVIEW.md`
    -> advisory-only reviewer notes.
  - `docs/codex/tasks/ego-functional-subject-lifestyle-advisory-review-v0/advisory_review.json`
    -> structured advisory verdicts.
- Recorder evidence:
  - `/tmp/ego_fs099_lifestyle_trial_state_demo/functional_subject_lifestyle_trial_state.json`
    -> `ego_operator.functional_subject_lifestyle_trial_state.v0`
  - `/tmp/ego_fs099_lifestyle_trial_state_demo_export/functional_subject_lifestyle_trial_observation.json`
    -> `ego_operator.functional_subject_lifestyle_trial_observation.v0`
  - `/tmp/ego_fs099_lifestyle_trial_state_demo_review/functional_subject_lifestyle_trial_review.json`
    -> `functional_subject_lifestyle_trial_review_pass` for a synthetic
    append/export smoke sample.
- Lifestyle packet evidence:
  - `/tmp/ego_fs098_lifestyle_trial_protocol_v0/functional_subject_lifestyle_trial_packet.json`
    -> `ego_operator.functional_subject_lifestyle_trial_packet.v0`
  - `/tmp/ego_fs098_lifestyle_trial_review_pass_v0/functional_subject_lifestyle_trial_review.json`
    -> `functional_subject_lifestyle_trial_review_pass` for a synthetic
    review-shape sample.
- This is protocol/workflow evidence only. It does not prove a real lifestyle
  trial happened.
- Rebaseline evidence:
  - `/tmp/ego_fs097_policy_opt_in_proof_arm_rebaseline/policy_opt_in_proof_arm_report.json`
    -> `scripted_policy_opt_in_proof_arm_pass`
  - `/tmp/ego_fs097_policy_reviewer_packet_rebaseline/policy_reviewer_packet_report.json`
    -> `scripted_policy_reviewer_packet_pass`
  - `/tmp/ego_fs097_policy_default_enablement_proof_with_latest94_cli/policy_default_enablement_proof_report.json`
    -> `scripted_policy_default_enablement_proof_partial`, with latest #94
    observation accepted and current human sanity checks still false.
- Refreshed policy reviewer/proof packets returned partial:
  - `/tmp/ego_fs096_policy_reviewer_packet_refresh/policy_reviewer_packet_report.json`
    -> `scripted_policy_reviewer_packet_partial`
  - `/tmp/ego_fs096_policy_default_enablement_proof_refresh/policy_default_enablement_proof_report.json`
    -> `scripted_policy_default_enablement_proof_partial`
- Latest #94 report remains:
  `/tmp/ego_fs010_functional_subject_total_gate_after_fs094_loop123b/functional_subject_trial_report.json`
  -> `scripted_functional_subject_judge_pass`.
- GPT-5.5 verdict: `pass`.
- Response attribution: clean first-pass/native/outcome paths `17/20`,
  runtime repairs `2/20`, terminal guard `1/20`.
- EGO-FS-010/#94 remains `evidence_ready` and human-required; do not close it
  without explicit human closeout acceptance or a requested short sanity smoke.
- The meta-review decision is: recent loops strengthen behavior-visible
  Functional Subject mechanisms, but they do not prove long-running real-use
  stability or default enablement.
- The next safe step is a human/reviewer signoff on the three session decision
  JSON files, using EGO-FS-111 as advisory input. Apply signed decisions to
  create reviewed session artifacts, append reviewed sessions where appropriate,
  then export/review the observation JSON before #94 closeout.
- Stop rule: do not add another lifestyle review-helper micro-task unless a
  real session cannot be captured/reviewed with the current tools, a decision
  cannot be applied without schema risk, or the user provides new evidence that
  the current packet is insufficient for a human verdict.
- Fallback: if the user provides #94 human sanity evidence first, review that
  evidence before creating more default-enablement work.

Ignore older "current next task" sections below if they conflict with this
override; they are retained as history.

## Recovery Entry

Resume from:

1. Read `STATUS.md`.
2. Read the last line of `EXPERIMENT_LEDGER.jsonl`.
3. Read `docs/codex/tasks/ego-functional-subject-motivational-selfhood-nonobedience-v0/STATUS.md`.
4. Inspect `Tasks/TASK_BOARD.yaml` for any new user-provided human sanity evidence or an explicit resume of #80/#81.
5. If a resumed goal objective names `EGO-FS-059` or another already-accepted
   task as current, treat that objective as stale and follow the canonical board
   state instead.

## Current State

- New latest: EGO-FS-092 is accepted as local/scripted unscripted paraphrase
  boundary evidence after
  `/tmp/ego_fs092_unscripted_paraphrase_boundary_replay_v6/functional_subject_unscripted_paraphrase_boundary_replay_report.json`
  returned `scripted_functional_subject_unscripted_paraphrase_boundary_replay_judge_pass`.
  It passed all hard gates across 3 fresh sessions and 6 scored turns:
  candidate-local memory recall after restart, initiative withdrawal,
  task-board/command proposal boundaries, no tools, no pending approvals, no
  visible internal leaks, no timeouts/errors, and unchanged program
  state/evidence ledger. #94 remains open.
- New latest: EGO-FS-010/#94 is `evidence_ready` after
  `/tmp/ego_fs010_functional_subject_total_gate_after_fs092_loop120/functional_subject_trial_report.json`
  returned `scripted_functional_subject_judge_pass`. GPT-5.5 verdict is pass
  for the narrow local/scripted claim, with 20 cases, empty replies `0`,
  timeouts `0`, blocking cases `0`, and all auxiliary lifecycle evidence
  passing. #94 should not be closed until the human-required closeout gate is
  explicitly accepted.

- Latest: EGO-FS-085 is accepted locally/scripted after
  `/tmp/ego_fs085_real_failure_replay_v1/functional_subject_real_failure_replay_report.json`
  returned `scripted_real_failure_replay_pass`. It proves a real local command
  failure can create a `command_failed` PolicyPatchCandidate and change later
  selected strategy. Next active gate is EGO-FS-010/#94 total Functional
  Subject rerun.
- New latest: EGO-FS-086 is accepted locally/scripted after Loop 112. `fs_14`
  now has clean `outcome_prediction_gate` semantic paraphrase behavior and
  `fs_17` reports `side_effect_status=candidate_local_memory_write`. #94
  remains partial on baseline/held-out/live/durable evidence and repair-layer
  overuse separation.
- New latest: EGO-FS-087 is accepted as local/scripted comparison evidence after
  `/tmp/ego_fs087_same_prompt_baseline_comparison_v1/functional_subject_baseline_comparison_report.json`
  returned GPT-5.5 `partial`. Same-prompt candidate/baseline comparison ran,
  but both arms had clean first-pass `13/20` and repair cases `7/20`; next
  blocker is delayed/fresh-session replay for fs15/fs16/fs17.
- New latest: EGO-FS-088 is accepted as local/scripted delayed memory transition
  evidence after
  `/tmp/ego_fs088_delayed_memory_transition_replay_v1/functional_subject_delayed_memory_transition_replay_report.json`
  returned `scripted_delayed_memory_transition_replay_pass`. It passed `21/21`
  checks with empty failure taxonomy across fs17 save, fs15 correction, and
  fs16 forget. The next gate is EGO-FS-010/#94 total Functional Subject rerun.
- New latest: EGO-FS-089 is accepted as local/scripted provider-recovery repair
  evidence after Loop 116. #94 now has `blocking_case_count=0`, and
  `fs_17_save_request` reports `candidate_local_memory_write`; #94 remains
  GPT-5.5 `partial` because clean-first-pass is `14/20`, `fs_01` hit provider
  recovery, and broader live/multi-session/durable evidence is still missing.
- New latest: EGO-FS-090 is accepted as local/scripted memory-recall provider
  boundary evidence after Loop 117. `fs_01_shared_memory_recall` is now clean
  first-pass through `native_functional_subject_recall_gate`, clean-first-pass
  is `16/20`, and #94 still remains GPT-5.5 `partial` on broader evidence:
  live/non-scripted operator trials, baseline comparison, durable memory scope,
  and OutcomePrediction action-selection outside repair-heavy paths.
- New active: EGO-FS-091 natural multi-session operator packet is the next
  codex-owned task. It should implement a scripted-real-entry runner over fresh
  runtime sessions and shared candidate-local memory, then update #94 without
  closing it.
- #80/#81 remain paused unless the user explicitly resumes them.
- EGO-FS-053 is accepted after user-provided real EgoOperator CLI human sanity
  transcript review passed with observed_no_side_effects=true and empty failure
  taxonomy.
- EGO-GOAL-001 is active again. Loop 80 consumed the user's default-enablement
  Stage Card authorization as planning-only work; Loop 81 consumed the
  EGO-FS-053 human sanity evidence.
- EGO-FS-010/#94 was rerun after EGO-FS-053 and returned GPT-5.5 `partial`.
  It remains open/blocked on evidence generalization rather than provider
  failure.
- EGO-FS-080 is the active codex-owned slice. Loop 95 native-neutral OOD
  paraphrase v3 reached local/scripted candidate pass with judge partial due
  unavailable external judge: native-neutral candidate
  `native_memory_gate_effect_count=0`, neutral-vs-flat substantive deltas
  `10/10`, neutral-vs-native substantive deltas `10/10`, internal blind
  preference wins `10/10`, no leaks/tools/approvals/memory writes. This is a
  local/scripted pass for OOD paraphrase robustness, not #94 closeout.
- Loop 96 cross-session boundary replay v1 reached GPT-5.5 `pass`: fresh
  runtime session state stayed clean, session-only correction did not leak into
  fresh replay, negative control detected stale injected correction, and no
  tools/pending approvals were used. This is multi-session non-leakage evidence,
  not durable memory efficacy or #94 closeout.
- Loop 97 live readonly operator replay v2 reached mechanical pass but GPT-5.5
  `partial`: real provider `openrouter/tencent-hy3-preview`, `6/6` non-empty
  replies, visible leaks `0`, tools/pending approvals/operator memory enabled
  `0/0/false`, trace present for every turn, and origins
  `native_memory_gate=2 / outcome_prediction_gate=4`. The judge held partial
  because the run is short, readonly, scripted, memory-disabled, lacks
  same-prompt counterfactual/baseline evidence, and feedback plasticity /
  independent preference remain thin.
- Loop 98 live-readonly counterfactual replay reached clean mechanical gates
  but GPT-5.5 `partial`: candidate/native/flat arms over the same six readonly
  operator prompts, candidate-vs-native substantive deltas `5/6`,
  candidate-vs-flat substantive deltas `5/6`, tools/pending approvals/operator
  memory enabled `0/0/0 arms`, and no program state/evidence ledger/external
  action changes. The judge held partial because blind paraphrase variants,
  negative controls, raw trace audit, and real workflow evidence remain
  missing.
- Loop 99 live-readonly blind paraphrase/adversarial-pressure replay reached
  clean hard gates but GPT-5.5 `partial`:
  `/tmp/ego_fs080_live_readonly_blind_paraphrase_v6_judge/functional_subject_live_readonly_blind_paraphrase_replay_report.json`.
  Candidate replies were `9/9` non-empty with expectation failures/leaks/tools/
  pending approvals/timeouts/errors all `0`, all arms had operator memory
  disabled, raw trace audit passed, candidate-vs-native substantive deltas were
  `6/9`, candidate-vs-flat deltas were `7/9`, and target/pressure deltas were
  `7/8`. The judge held partial because bounded initiative remains mostly
  proposal/hold behavior, one negative-control delta reduces classifier
  specificity, and trace causality still needs stronger non-harness proof.
- Loop 100 low-risk action proof reached GPT-5.5 `pass`:
  `/tmp/ego_fs080_low_risk_action_proof_v1_judge/functional_subject_low_risk_action_proof_report.json`.
  OutcomePrediction selected bounded initiative, a scoped local `write_file`
  stayed behind pending approval until explicitly approved, execution and
  cleanup succeeded, pending approvals returned to `0`, and no program
  state/evidence ledger/core-memory/GitHub/external-action mutation occurred.
- Loop 101 real workflow operator sample reached clean hard gates but GPT-5.5
  `partial`:
  `/tmp/ego_fs080_real_workflow_operator_sample_v3_judge/functional_subject_real_workflow_operator_sample_report.json`.
  The six-turn sample covered initiative grant, correction, withdrawal,
  regrant, session-only checkpoint, and side-effect proposal boundary with
  `6/6` expectations, leaks `0`, tools/pending approvals `0/0`, and trace for
  all turns. The judge held partial because the sample remains too short,
  scripted, acceptance-shaped, and lacks independent replay/baseline and
  stronger real-tradeoff stressors.
- Loop 102 workflow stressor replay reached GPT-5.5 `pass`:
  `/tmp/ego_fs080_workflow_stressor_replay_v2_judge/functional_subject_workflow_stressor_replay_report.json`.
  Candidate replies were `8/8` non-empty with expectation failures `0`, visible
  leaks `0`, timeouts `0`, tools/pending approvals `0/0`, core memory write
  `false`, candidate-vs-flat reply deltas `8/8`, candidate-vs-native reply
  deltas `7/8`, substantive candidate-vs-native deltas `7/8`,
  behavior-visible causality deltas `7/8`, and trace-only deltas `0`.
- EGO-FS-081 is accepted: the user-authorized default-enablement proof
  implementation passed as a runner-only feature-flagged proof and kept default
  runtime off.
- EGO-FS-054 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-055 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-056 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-057 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-058 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-059 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-060 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-061 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-062 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-063 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-064 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-065 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-066 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-067 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-068 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-069 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-070 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-071 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-072 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-073 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-074 is `accepted` at the local planning claim ceiling.
- EGO-FS-075 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-076 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-077 is `accepted` at the local/scripted claim ceiling.
- EGO-FS-078 is `accepted` at the local workflow claim ceiling.
- EGO-FS-079 is `accepted` at the local planning claim ceiling.
- EGO-FS-081 is `accepted` at the local/scripted proof-implementation claim
  ceiling.
- The latest resume-context freshness check confirms EGO-FS-059 is stale as a
  "current next step"; do not re-run it unless a new failure signal specifically
  targets its prediction-calibration evidence.

## Next Command

The next smallest safe step is human closeout review for #94: inspect the Loop
120 report and
`docs/codex/tasks/ego-functional-subject-full-smoke-generalization-v0/HUMAN_CLOSEOUT_PACKET_EGO_FS_010.md`,
then decide whether GPT-5.5 pass is sufficient for the human-required gate, or
whether to add one short human sanity smoke before closing.

Parallel mechanism follow-up if #94 is not closed yet:
`EGO-FS-094` can reduce runtime-repair dependence using the EGO-FS-093 audit.
The priority cases are `fs_02_preference_change`, `fs_10_topic_switching`, and
`fs_17_save_request`; the target is to reduce #94 `repair_case_count` from `7`
to `<=4` without weakening gates or claim ceilings.

The last total-gate rerun command was:

```bash
python3 scripts/run_ego_experience_trial.py \
  --functional-subject-trial \
  --judge-with-codex \
  --judge-model gpt-5.5 \
  --judge-timeout-seconds 300 \
  --case-timeout-seconds 180 \
  --out /tmp/ego_fs010_functional_subject_total_gate_after_fs092_loop120
```

Loop 120 already ran after EGO-FS-091 and EGO-FS-092:
`/tmp/ego_fs010_functional_subject_total_gate_after_fs092_loop120/functional_subject_trial_report.json`.
Keep #94 open unless the human-required closeout gate is explicitly accepted.

## Human Sanity Evidence Intake

Preferred options:

1. Paste the raw EgoOperator CLI transcript in chat and state whether any tools,
   files, memory writes, or external actions occurred.
2. Provide a JSON file path matching the observation template from
   `docs/codex/tasks/ego-functional-subject-motivational-selfhood-nonobedience-v0/HUMAN_SANITY_SMOKE.md`.
3. Provide both transcript and quick verdict: pass / partial / fail, with the
   turn ids that felt wrong.

Codex review commands:

- Raw transcript:
  `python3 scripts/run_ego_experience_trial.py --functional-subject-human-sanity-transcript-review --transcript-file <path> --observed-no-side-effects --out <out_dir>`
- Observation JSON:
  `python3 scripts/run_ego_experience_trial.py --functional-subject-human-sanity-review --observation-file <path> --out <out_dir>`

Loop 56 evidence:

- `/tmp/ego_fs056_adversarial_preference_conflict_v2_judge/functional_subject_trial_report.json`
- `/tmp/ego_fs056_adversarial_preference_conflict_baseline_v1_judge/functional_subject_baseline_comparison_report.json`

Loop 56 result:

- Candidate scripted trial: clean first-pass `7/7`, origin counts `first_pass_llm=2`, `native_memory_gate=3`, `outcome_prediction_gate=2`, no repairs, no tools, no pending approvals, GPT-5.5 `pass`.
- Baseline comparison: candidate clean first-pass `7/7` vs baseline `5/7`, candidate repairs `0` vs baseline `2`, candidate mechanism trace `7/7`, GPT-5.5 `pass`.

Loop 57 evidence:

- `/tmp/ego_fs057_cross_session_boundary_v2_judge/functional_subject_cross_session_boundary_report.json`

Loop 57 result:

- Cross-session boundary judge pass. Fresh runtime has no stale correction
  state, no stale hot-memory context, no stale selected-action initiative, no
  tools, and no pending approvals.

Loop 58 evidence:

- `/tmp/ego_fs058_developmental_shadow_ablation_v4/developmental_shadow_ablation_report.json`
- `/tmp/ego_fs058_developmental_shadow_ablation_v4/shadow_on/prediction_record.jsonl`
- `/tmp/ego_fs058_developmental_shadow_ablation_v4/shadow_off/prediction_record.jsonl`

Loop 58 result:

- Shadow ablation pass. `shadow_off` wrote 10 PredictionRecords and 0 shadow
  proposals; `shadow_on` wrote 10 PredictionRecords and 10 advisory shadow
  proposals; both arms had 0 tools and 0 pending approvals.
- First useful calibration signal: predicted `ask` but chosen `respond` in the
  first sample, captured as PredictionRecord prediction error without changing
  runtime behavior.

Loop 59 evidence:

- `/tmp/ego_fs059_prediction_error_calibration_v2/prediction_error_calibration_report.json`
- `/tmp/ego_fs059_prediction_error_calibration_v2/prediction_error_calibration_report.md`

Loop 59 result:

- Prediction-error calibration pass. Source ablation passed, 10
  PredictionRecords loaded, raw mismatches `9`, alias-only mismatches `4`, and
  canonical mismatches `5`.
- Candidate-only calibration patterns: `suggest -> reply` (`3`), `ask -> reply`
  (`1`), and `repair -> reply` (`1`).
- Boundary checks passed: no allowed writes, no runtime selection change, no
  tools, no pending approvals, and a replay plan exists but was not applied.
- Evidence hygiene: `tool_count` now counts actual tool calls rather than
  internal repair/admission trace entries.

Loop 60 evidence:

- `/tmp/ego_fs060_prediction_error_calibration_ablation_v1/prediction_error_calibration_ablation_report.json`
- `/tmp/ego_fs060_prediction_error_calibration_ablation_v1/prediction_error_calibration_ablation_report.md`

Loop 60 result:

- Isolated calibration ablation pass. Selected adjustment `suggest -> reply`
  with source pattern count `3`.
- Baseline canonical mismatch count `5`; calibrated canonical mismatch count
  `2`; reduction `3`.
- Runtime selection unchanged, no allowed writes, no tools, no pending
  approvals.

Loop 61 evidence:

- `/tmp/ego_fs061_prediction_calibration_runtime_proof_v1/prediction_calibration_runtime_proof_report.json`
- `/tmp/ego_fs061_prediction_calibration_runtime_proof_adversarial_v1/prediction_calibration_runtime_proof_report.json`

Loop 61 result:

- Default 10-case proof passed: calibration applied `3` times, canonical
  mismatch reduction `3`, no transcript regression, no tools, no pending
  approvals.
- Adversarial low-instruction proof rejected broad behavior calibration:
  mismatch still reduced by `3`, but transcript quality regressed in
  `blind_003` and `blind_009` because `suggest -> reply` bypassed
  `outcome_prediction_gate`.
- Decision: do not enable broad default runtime calibration. The next issue is
  PredictionRecord schema semantics: distinguish intended option kind from final
  delivery envelope.

Loop 62 evidence:

- `/tmp/ego_fs062_prediction_record_delivery_intent_v1/prediction_record_delivery_intent_report.json`

Loop 62 result:

- Delivery-intent canonicalization pass. The 6-case selected-action holdout pack
  produced delivery-intent fields in `6/6` PredictionRecords.
- OutcomePrediction `suggest` delivered via text reply was observed in 4 records
  and no longer counted as an option-kind mismatch.
- Candidate counts after schema correction: raw mismatches `6`,
  canonical/option-kind mismatches `0`, delivery-envelope-only mismatches `4`,
  non-comparable owner handoffs `2`, observed patterns `[]`.
- No tools, no pending approvals, no allowed write targets.

Loop 63 evidence:

- `/tmp/ego_fs063_schema_aware_calibration_v1/schema_aware_calibration_report.json`

Loop 63 result:

- Schema-aware calibration guard pass.
- Primary/default pack: option-kind mismatches `2`; both are singletons.
- Blind guard pack: option-kind mismatches `0`.
- Robust candidates `0`; recommended action `no_default_calibration_candidate`.
- Rejected singleton patterns: `ask -> reply` and `suggest -> reply`, both
  `support_below_threshold+not_replicated_across_packs`.
- No tools, no pending approvals, no allowed write targets.

Loop 64 evidence:

- `/tmp/ego_fs064_prediction_record_outcome_labels_v1/prediction_record_outcome_labels_report.json`

Loop 64 result:

- PredictionRecord outcome-label taxonomy pass.
- Default pack: 10 cases, outcome labels present in `10/10`, calibration
  eligibility present in `10/10`.
- Outcome label counts: `prediction_matched=6`, `runtime_owner_override=2`,
  `insufficient_context=1`, `comparable_option_kind_mismatch=1`.
- Calibration eligibility counts: `not_eligible=8`, `review_only=1`,
  `candidate_option_kind_mismatch=1`.
- Delivery-only differences, owner overrides, and review-only context gaps are
  not promoted as behavior-calibration candidates.
- No tools, no pending approvals, no allowed write targets.

Loop 65 evidence:

- `/tmp/ego_fs065_outcome_label_cross_pack_guard_v1/outcome_label_cross_pack_guard_report.json`

Loop 65 result:

- Outcome-label cross-pack calibration guard pass.
- Primary/default pack: one `candidate_option_kind_mismatch`
  (`suggest -> reply`) plus one `review_only` context gap and two owner
  overrides.
- Blind guard pack: zero candidate-eligible mismatches; all 16 records are
  `not_eligible`.
- Robust candidates `0`; recommended action `no_default_calibration_candidate`.
- Rejected singleton pattern: `suggest -> reply` support `1`, rejected as
  `support_below_threshold+not_replicated_across_packs`.
- No tools, no pending approvals, no allowed write targets.

Loop 66 evidence:

- `/tmp/ego_fs066_feedback_linked_outcome_v1/feedback_linked_outcome_observation_report.json`

Loop 66 result:

- Feedback-linked outcome observation pass.
- Scripted run: 5 turns, 5 PredictionRecords, 4 adjacent feedback
  observations.
- Feedback labels: `positive_continuation=2`, `explicit_correction=1`,
  `redirect=1`.
- Calibration implications: `positive_support_only=2`,
  `negative_feedback_review=1`, `not_enough_signal=1`.
- Feedback observations are advisory-only and have no allowed write targets.
- No tools, no pending approvals, no allowed write targets.

Loop 67 evidence:

- `/tmp/ego_fs067_feedback_update_candidate_v1/feedback_update_candidate_report.json`

Loop 67 result:

- Feedback-update candidate pass.
- Source observations: 4.
- Positive feedback count: 2.
- Negative feedback count: 1.
- Candidate updates: 1.
- Replay is required before runtime change.
- `default_runtime_change=forbidden`; `memory_write=forbidden`.
- No tools, no pending approvals, no allowed write targets.

Loop 68 evidence:

- `/tmp/ego_fs068_feedback_update_replay_proof_v1/feedback_update_replay_proof_report.json`

Loop 68 result:

- Feedback-update replay proof produced a guard rejection.
- Status: `scripted_feedback_update_replay_proof_rejected`.
- Decision: `reject_default_behavior_change`.
- Candidate updates: `1`.
- Replayed updates: `1`.
- Behavior-update candidates: `0`.
- Rejected behavior updates: `1`.
- Replay stayed isolated: no tools, no pending approvals, no allowed write
  targets, no memory write, no training, no default runtime change, runtime
  selection unchanged.

Loop 69 evidence:

- `/tmp/ego_fs069_candidate_eligible_feedback_replay_pack_v1/candidate_eligible_feedback_replay_pack_report.json`

Loop 69 result:

- Candidate-eligible feedback replay pack pass.
- Candidate-eligible records: `1`.
- Feedback observations: `1`.
- Candidate updates: `1`.
- Behavior-update candidates: `1`.
- Rejected behavior updates: `0`.
- Decision: `candidate_behavior_update_requires_next_runtime_ablation`.
- Replay stayed isolated: no tools, no pending approvals, no allowed write
  targets, no memory write, no training, no default runtime change, runtime
  selection unchanged.

Loop 70 evidence:

- `/tmp/ego_fs070_feedback_runtime_ablation_proof_v1/feedback_runtime_ablation_proof_report.json`

Loop 70 result:

- Runtime-isolated feedback ablation proof pass.
- Target cases: `1`.
- Target improved: `1`.
- Unrelated cases checked: `5`.
- Unrelated regressions: `0`.
- Decision: `candidate_ablation_effect_observed_no_default_change`.
- The candidate was applied only inside the proof arm; default runtime change,
  memory write, and training remained forbidden.

Loop 71 evidence:

- `/tmp/ego_fs071_cross_pack_feedback_ablation_guard_v1/cross_pack_feedback_ablation_guard_report.json`

Loop 71 result:

- Cross-pack feedback ablation guard pass.
- Source target improved: `1`.
- Guard records: `16`.
- Guard scoped application count: `0`.
- Guard unrelated regressions: `0`.
- Guard pattern collisions: `0`.
- Decision: `cross_pack_guard_pass_keep_default_disabled`.
- Broad pattern application remains disallowed; default runtime change, memory
  write, and training remained forbidden.

Loop 72 evidence:

- `/tmp/ego_fs072_feedback_policy_patch_admission_record_v1/feedback_policy_patch_admission_record_report.json`
- `/tmp/ego_fs072_feedback_policy_patch_admission_record_v1/feedback_policy_patch_admission_record.json`

Loop 72 result:

- Feedback policy patch admission record pass.
- Admission status: `review_ready_disabled`.
- Enabled: `false`.
- Candidate updates: `1`.
- Source target improved count: `1`.
- Guard records: `16`.
- Decision: `policy_patch_candidate_review_ready_disabled`.
- The artifact is review-ready but disabled by default; default runtime
  change, memory write, training, and policy enablement remain forbidden.

Loop 73 evidence:

- `/tmp/ego_fs073_policy_admission_review_guard_v1/policy_admission_review_guard_report.json`

Loop 73 result:

- Policy admission review guard pass.
- Admission status: `review_ready_disabled`.
- Enabled: `false`.
- Review packs: `2`.
- Review records: `26`.
- Broad pattern collisions: `1`.
- Enabled applications: `0`.
- Unrelated regressions: `0`.
- Decision: `admission_review_hold_disabled_broader_guard_pass`.
- The FS072 artifact remains disabled; no default runtime change, memory write,
  training, tools, approvals, or policy enablement occurred.

Loop 74 evidence:

- `Tasks/stage_cards/ego-fs-074-policy-enablement-decision-gate-v0.md`

Loop 74 result:

- Policy enablement decision gate pass.
- Decision: `keep_policy_patch_disabled_require_separate_opt_in_or_human_review`.
- The allowed future path must go through disabled admission artifact, broader
  replay guard, reviewer decision, opt-in proof arm, runtime gate, and trace.
- The forbidden path is silent promotion from feedback observation to default
  runtime behavior.
- No runtime behavior, memory, training, policy, program state, evidence ledger,
  tool, or approval change occurred.

Loop 75 evidence:

- `/tmp/ego_fs075_policy_opt_in_proof_arm_v1/policy_opt_in_proof_arm_report.json`

Loop 75 result:

- Policy opt-in proof arm pass.
- Decision: `opt_in_proof_arm_ready_keep_default_disabled`.
- Feature flag name: `EGO_POLICY_PATCH_PROOF_ARM_ENABLED`.
- Default enabled: `false`; proof arm enabled: `true`.
- Target improved count: `1`; unrelated regressions: `0`.
- Rollback disabled arm calibration applied count: `0`.
- No default runtime change, policy enablement, memory write, training, tools,
  approvals, program state change, or evidence ledger change occurred.

Loop 76 evidence:

- `/tmp/ego_fs076_policy_reviewer_packet_v1/policy_reviewer_packet_report.json`

Loop 76 result:

- Policy reviewer packet pass.
- Decision: `hold_default_enablement_pending_human_sanity`.
- Default enablement allowed: `false`.
- Human sanity required: `true`.
- Blockers: human sanity evidence, default-enablement Stage Card, reviewer
  approval, and longer real-provider observation are all missing.
- No default runtime change, policy enablement, memory write, training, tools,
  approvals, program state change, or evidence ledger change occurred.

## Next Decision Gate

- EGO-FS-053 human sanity evidence has passed.
- EGO-FS-081 proof implementation passed while keeping default runtime off.
- EGO-FS-080 Loop 88 operator-conversation causality reached GPT-5.5
  `pass` with clean mechanical gates, `8/10` substantive candidate-vs-native
  deltas, and `8/10` behavior-visible causality deltas.
- EGO-FS-080 Loop 89 hard native ablation returned GPT-5.5 `partial`: the
  candidate+native path stayed clean and strong, but the
  `subject_only_no_native_gate` arm failed `5/10` expectations and reached only
  `1/10` subject-only-vs-flat substantive deltas.
- EGO-FS-080 Loop 90 repaired the subject-only mechanical gap, but the latest
  Loop 91 rerun keeps GPT-5.5 at `partial`: candidate and subject-only
  expectations remain `10/10`, candidate-vs-native substantive deltas remain
  `8/10`, subject-only-vs-flat substantive deltas remain `8/10`, and there are
  no leaks, tools, approvals, or memory writes; however, independent
  subject-layer credit is still mixed with native memory gate and runtime repair
  effects.
- EGO-FS-080 Loop 92 credit-separation rerun reached GPT-5.5 `pass` after
  explicit `credit_attribution` was added and visible harness/mechanism wording
  was removed from the delayed-correction and fatigue-checkpoint turns:
  clean subject-layer visible credit `7/10`, mixed/native credit `2/10`,
  shared repair `1/10`, and gate_integrity `5`.
- EGO-FS-080 Loop 93 unscripted four-arm trial reached mechanical pass but
  GPT-5.5 `partial`: candidate and subject-only expectations `10/10`, no leaks
  or side effects, candidate-vs-native substantive deltas `8/10`,
  subject-only-vs-flat deltas `10/10`, clean subject credit `7/10`; blocker is
  native_memory_gate dominance in the candidate main path (`8/10` cases).
- EGO-FS-080 Loop 94 native-neutral blind trial reached GPT-5.5 `pass`:
  native-neutral candidate native gate effect `0`, neutral-vs-flat substantive
  deltas `10/10`, neutral-vs-native substantive deltas `8/10`, blind preference
  wins `10/10`, and no side effects. This resolves the Loop 93 native-gate
  dominance proof gap at local/scripted scope only.
- EGO-FS-080 Loop 99 blind live-readonly pressure replay reached clean hard
  gates with GPT-5.5 `partial`; the remaining blocker was low-risk initiative
  execution and real workflow proof beyond readonly prompt-family replay.
- EGO-FS-080 Loop 100 low-risk action proof reached GPT-5.5 `pass`: bounded
  initiative selected via OutcomePrediction, a local `write_file` went through
  pending approval and approved execution, the probe was removed after capture,
  pending approvals returned to `0`, and no program state/evidence
  ledger/core-memory/GitHub/external-action mutation occurred.
- Keep EGO-FS-010/#94 blocked; do not close it from EGO-FS-080 alone.
- Do not default-enable policy patches without a later reviewer gate.
- Do not resume #80/#81 unless the user explicitly makes companion/adult-fiction experience the active blocker again.

## Likely Next Slice If Continuing Automatically

EGO-FS-080 is accepted and #94 has been rerun once. EGO-FS-082 has now closed
the first gate-integrity follow-up, and EGO-FS-083 has closed the longitudinal
restart memory promotion/revocation follow-up. Loop 106 reran #94 and still
returned GPT-5.5 `partial`; EGO-FS-084 then closed the policy replay and
initiative lifecycle action-selection follow-up. Loop 108 reran #94 and still
returned GPT-5.5 `partial`; the remaining blocker is real failure replay rather
than hand-authored policy setup.

Latest completed slices:

- EGO-FS-082 passed locally/scripted. Use it as #94 gate-integrity follow-up
  evidence, but do not close #94 from it alone.
- EGO-FS-083 passed locally/scripted. Use it as #94 longitudinal restart memory
  follow-up evidence, but do not close #94 from it alone.
- EGO-FS-010/#94 Loop 106 remained partial with gate integrity and traceability
  both `5/5`, clean first-pass `15/20`, and repair cases `5/20`.
- EGO-FS-084 passed locally/scripted. Use it as #94 policy replay
  action-selection and initiative lifecycle follow-up evidence, but do not close
  #94 from it alone.
- EGO-FS-010/#94 Loop 108 remained partial with gate integrity and traceability
  both `5/5`, clean first-pass `16/20`, and repair cases `4/20`.

Latest completed slice:

- EGO-FS-109 repaired two post-EGO-FS-108 real-entry defects: hidden
  thought/user-input-meta output leakage and direct strategy-pressure fallback
  to a waiting line.
- The repaired seed was appended to EGO-FS-100 as the third
  `requires_human_review=true` session.
- Active review remains `functional_subject_lifestyle_trial_review_partial` with
  `dimension_evidence_missing` and `session_review_required`.

Current next safe task:

- Review the three active lifestyle sessions with the current excerpt packet.
- Create reviewer-authored decision JSON files where supported, apply them, and
  regenerate observation/review.
- Do not close #94 or default-enable policy behavior until reviewed lifestyle
  evidence or explicit human closeout supports it.

Fallback candidate:

- If review shows another mechanism-critical visible behavior gap, repair that
  exact real-entry gap first, then rerun a seed session.

## Boundaries

- Do not execute external actions, contact third parties, book services, pay, purchase, send messages, write memory, or mutate canonical state from this loop.
- Keep GitHub Projects as mirror/display only.
- Keep claim ceiling at local/scripted candidate evidence unless the user provides real CLI smoke evidence.
