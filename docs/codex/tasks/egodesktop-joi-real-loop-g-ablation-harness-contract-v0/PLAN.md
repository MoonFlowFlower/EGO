# EgoDesktop Joi Real-Loop G-ABLATION Harness Contract v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a default-off EgoDesktop real-loop G-ABLATION harness contract module with tests, without enabling runtime behavior.

**Architecture:** Add one focused CommonJS module under `EgoDesktop/src/` that owns flag parsing, no-authority validation,
condition declarations, trace-row construction, baseline-plan metadata, and verdict rule ordering. Add one Node test file
that exercises the contract directly. Keep runtime files unchanged in this slice.

**Tech Stack:** Node.js CommonJS, `node:test`, existing EgoDesktop test style, Markdown task docs.

---

## File Structure

- `EgoDesktop/src/joiRealLoopGAblationHarness.js`: pure contract/helper module. No Electron imports, no side effects.
- `EgoDesktop/tests/joi_real_loop_g_ablation_harness.test.js`: targeted Node tests.
- `artifacts/egodesktop_joi_real_loop_g_ablation_harness_v0/CONTRACT_REPORT.md`: local contract report from this slice.
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-harness-contract-v0/`: task docs and mutation scope.
- `Tasks/TASK_BOARD.yaml`: local task-board entry.

## Tasks

### Task 1: Contract Module

**Files:**
- Create: `EgoDesktop/src/joiRealLoopGAblationHarness.js`

- [ ] Define constants for claim ceiling, allowed verdicts, required conditions, diagnostic conditions, flag keys, static
      replay policies, and same-access reproducer families.
- [ ] Implement `buildJoiRealLoopGAblationContract(env)` so absent flags return a disabled, no-authority contract and
      enabled flags require condition, trace dir, replay-locked LLM mode, prompt pack, and split.
- [ ] Implement recursive `validateNoAuthorityFields(payload, label)` over executable fields such as `action`,
      `tool_call`, `user_message`, `memory_write`, `gate_decision`, `transport`, `send`, `schedule`, `enable`, and
      `mainline_authority`.
- [ ] Implement `buildJoiRealLoopTraceRow(payload)` with required field checks and deterministic hashes for row inputs.
- [ ] Implement `buildBaselineEvaluationPlan()` and `decideJoiRealLoopVerdict(signals)`.

### Task 2: Targeted Tests

**Files:**
- Create: `EgoDesktop/tests/joi_real_loop_g_ablation_harness.test.js`

- [ ] Test default-off contract is disabled and no-authority.
- [ ] Test enabled contract blocks when required flags are missing or LLM mode is not `replay_locked`.
- [ ] Test valid enabled contract is only ready for an explicit harness run, not default runtime registration.
- [ ] Test recursive authority-field rejection.
- [ ] Test trace-row construction records condition, split, hashes, public inputs, idle exclusion, and replay inputs.
- [ ] Test baseline plan preserves same-pack diagnostic replay, heldout static replay, and strongest same-access battery.
- [ ] Test verdict ordering blocks positive verdict for leakage, same-pack replay misuse, heldout replay equivalence,
      same-access equivalence, renderer idle, unlocked LLM, and no creature effect.

### Task 3: Report And Board

**Files:**
- Create: `artifacts/egodesktop_joi_real_loop_g_ablation_harness_v0/CONTRACT_REPORT.md`
- Create: `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-harness-contract-v0/STATUS.md`
- Create: `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-harness-contract-v0/MUTATION_SCOPE.yaml`
- Modify: `Tasks/TASK_BOARD.yaml`

- [ ] Record what this contract module proves and does not prove.
- [ ] Add `EGODESKTOP-GABLATION-002` as an implementation task.
- [ ] Mark `EGODESKTOP-GABLATION-001` accepted because the operator moved to implementation.
- [ ] Scope mutation to the new module, tests, docs, artifact report, task board, and task-board outbox.

### Task 4: Verification

**Commands:**
- `node --test EgoDesktop/tests/joi_real_loop_g_ablation_harness.test.js`
- `cd EgoDesktop && npm test`
- `git diff --check`
- `python scripts/codex_session_guard.py --mutation-scope docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-harness-contract-v0/MUTATION_SCOPE.yaml closeout-check --format markdown`

**Expected result:** targeted tests pass, all EgoDesktop tests pass, diff check passes, closeout has no unsafe dirty paths.
`remote_sync_unavailable` may remain if `gh` is unavailable; if so, ensure task-board outbox contains the task.

## Self-Review

- Spec coverage: every success criterion maps to module constants/helpers or tests.
- Placeholder scan: no placeholders or deferred validation.
- Type consistency: exported function names are `buildJoiRealLoopGAblationContract`,
  `buildJoiRealLoopTraceRow`, `buildBaselineEvaluationPlan`, `decideJoiRealLoopVerdict`, and
  `validateNoAuthorityFields`.
