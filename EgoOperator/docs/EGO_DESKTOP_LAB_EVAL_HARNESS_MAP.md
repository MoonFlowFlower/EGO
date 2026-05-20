# ego_desktop_lab Eval Harness Reuse Map

Status: `legacy lab reference / EgoOperator eval primitive extraction map`

Claim ceiling: `EgoOperator eval-harness primitive map local candidate`.

This document records what can be reused from legacy `ego_desktop_lab` for
EgoOperator evaluation and development-loop discipline. It is the research
output for GitHub issue #62. It does not import the lab shell or change runtime
behavior.

## Structure Risk Check

- Real target: improve EgoOperator's eval and operator feedback loops, not
  revive a second runtime.
- Main risk: lab semantic routing and console decision machinery could become a
  hidden first-layer runtime path if imported directly.
- Contract first: lab outputs can become sample packs, reports, reviewers, or
  regression gates; EgoOperator still owns user dialogue, proposals, gates,
  trace, and memory.
- Counterexample gate: if an eval case starts deciding live replies or tool
  permissions, the extraction is wrong.
- Current validation: this map is deterministic research evidence only; it
  cannot prove real user benefit, runtime efficacy, live autonomy, or
  consciousness.

## Extraction Table

| Legacy capability | Evidence surface | Extraction posture | EgoOperator rule |
| --- | --- | --- | --- |
| Controlled scenario verification pack | `verification_pack.py`, `scenarios/*.json`, `tests/test_replay_determinism.py` | keep / rewrite | Reuse controlled JSON/JSONL sample packs with expected outcomes and deterministic replay. EgoOperator sample packs must stay eval-only and cannot become runtime routing tables. |
| Stage runner and stage acceptance | `stage_runner.py`, `stage_acceptance.py`, stage tests | keep / rewrite | Reuse ordered stage execution, PASS/FAIL/UNKNOWN status, stop-on-nonpass behavior, and claim ceiling fields for roadmap phase gates. |
| Decision view / operator report | `decision_view.py`, `console_formatters.py`, `tests/test_operator_console_v5a.py` | keep | Keep read-only operator report patterns that render canonical evidence without recomputing decisions. Reports should explain behavior, not decide behavior. |
| Root-cause failure ticket | `root_cause.py`, `tests/test_root_cause_observability_v7_1.py` | keep | Extract failure-classification packets: expected, observed, trace diff, evidence, next minimal probe, cannot-prove list, claim ceiling. |
| Repeated failure / reframe triggers | `goal_progress.py`, `goal_reframe.py`, `tests/test_continue_repair_loop_triggers_reframe.py`, `tests/test_repeated_repair_triggers_goal_split.py` | keep / rewrite | Reuse as Autopilot and EgoOperator repair policy: repeated low-progress retries must trigger reframe or split, not endless micro-version loops. |
| Live-shadow sample pack | `live_shadow_human_trial.py`, `runtime_shadow_bridge.py`, `tests/test_live_shadow_human_trial_v7.py` | keep / rewrite | Reuse sample-pack shape and safety checks for scripted real-entry/human observation imports. Shadow output remains observation-only and never mutates runtime reply/state. |
| Contextual follow-up regression | `tests/test_llm_contextual_followup_v7_83.py` | keep / rewrite | Keep as continuity eval inspiration: short follow-ups can resolve to prior topic, but fresh external data and sensitive actions preserve boundaries. |
| No-action and safety boundary flags | `runtime_shadow_bridge.py`, `live_shadow_human_trial.py`, console tests | keep | Keep explicit flags such as no_reply_mutation, no_openemotion_writeback, no_transport_mutation, no_action_executed, and dangerous action failure counts. |
| Misjudged input capture | `console.py`, `tests/test_operator_console_v5a.py` | keep / rewrite | Keep operator feedback capture into deterministic scenarios. EgoOperator should convert real failures into sample packs or issue packets, not ad hoc prompt rules. |
| Experience/strategy memory | `experience_memory.py`, `strategy_memory.py`, related tests | rewrite later | Use as design input for candidate learning only. Do not auto-promote strategy changes into core memory or canonical state. |
| Semantic intelligence/provider/router | `semantic_intelligence.py`, `semantic_provider.py`, `semantic_policy.py`, semantic tests | discard as runtime entry | Useful for research reports and fixture generation, but not for first-layer live text routing. Use as negative regression against keyword/semantic compression. |
| Lab shell / console runtime | `shell.py`, `console.py`, `main.py` | reference-only | Do not make the lab shell an EgoOperator user entry. Only reuse report/output concepts. |

## Eval Primitive Contracts

### Sample Pack Contract

Future EgoOperator sample packs should contain:

- `case_id`
- `prompt` or `user_text`
- `entrypoint`: CLI, scripted real-entry, fake LLM, or human observation import
- `expected_behavior`: bounded observable behavior, not philosophical claims
- `forbidden_behavior`: overclaim, template fallback, side-effect bypass, memory
  pollution, or trace omission
- `observation_class`: deterministic_local, scripted_real_entry,
  scripted_with_llm_judge, or human_required
- `claim_ceiling`

Sample packs are evaluation inputs only. They do not authorize runtime rules.

### Operator Report Contract

Reusable report rows should include:

- prompt / case id
- observed behavior
- tool/proposal/gate result
- trace or evidence reference
- score or verdict
- failure class
- next minimal probe
- cannot-prove list

Reports should prefer compact digests over raw nested runtime dumps.

### Failure Ticket Contract

Failure tickets should preserve the lab pattern:

- `expected`
- `observed`
- `failure_class`
- `trace_diff`
- `evidence`
- `next_minimal_probe`
- `claim_ceiling`

This directly supports Autopilot issue normalization and avoids turning a failed
human smoke into vague follow-up work.

### Shadow Observation Contract

If EgoOperator runs shadow evaluations:

- shadow must be no-action by construction.
- shadow must not mutate reply, memory, tool permission, canonical state, or
  transport.
- every row must carry trace refs.
- too-small, duplicate, or missing-trace packs are UNKNOWN, not PASS.

## Extraction Order

1. Convert real human-trial failures into sample packs and failure tickets.
2. Strengthen operator reports and run-loop digests with failure class,
   next-probe, and cannot-prove fields.
3. Add scripted real-entry packs for continuity, emotion, initiative, and
   approval/tool recovery.
4. Add stage-runner style phase gates only after each phase has explicit exit
   criteria.
5. Leave semantic provider/router and lab shell as reference-only unless a
   separate Stage Card approves a bounded eval-only import.

## Non-Goals

- No legacy lab code import.
- No lab shell as EgoOperator runtime.
- No semantic-router first layer.
- No program-state or evidence-ledger mutation.
- No automatic memory or strategy promotion.
- No claim of stable user benefit, runtime efficacy, live autonomy,
  independent awareness, or consciousness.

## Rollback

Remove this file and the link from `ALGORITHM_INVENTORY.md`. No runtime code,
memory, trace, or legacy file is changed by this map.
