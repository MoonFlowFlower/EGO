# EgoDesktop Joi Real-Loop G-ABLATION Trace Runner v0 Plan

> Implementation must use tests first. Do not edit default runtime behavior outside the explicit trace-runner hook.

## Goal

Add a default-off trace-runner slice that can collect bounded local trace artifacts from the EgoDesktop chat/render path
under explicit experiment flags.

## Architecture

- Reuse `EgoDesktop/src/joiRealLoopGAblationHarness.js` as the single contract and trace-row authority.
- Add a focused trace-runner module that validates env flags, builds trace rows, writes JSON/JSONL/Markdown artifacts,
  and reports blocked labels honestly.
- Add only a narrow `main.js` hook if needed to capture actual IPC chat-turn and renderer-ready payloads under the
  valid experiment contract.
- Keep default behavior identical when `JOI_REAL_LOOP_G_ABLATION` is absent.

## Tasks

### Task 1: Targeted Tests

Files:
- `EgoDesktop/tests/joi_real_loop_g_ablation_trace_runner.test.js`

- [ ] Test absent flags produce an inert runner and no trace write.
- [ ] Test missing required flags return `blocked_missing_ego_authorization` or contract blockers.
- [ ] Test unlocked LLM mode returns `blocked_missing_llm_replay_contract`.
- [ ] Test authority-bearing payloads are rejected before artifact write.
- [ ] Test a fixture chat/render event builds a valid trace row via the existing harness module.
- [ ] Test renderer idle params are recorded as excluded from `D`.
- [ ] Test report wording cannot claim route-B pass, product pass, agency, emotion, subjectivity, consciousness, alive
      status, or Bar-2.

### Task 2: Trace Runner Module

Files:
- `EgoDesktop/src/joiRealLoopGAblationTraceRunner.js`

- [ ] Build `createJoiRealLoopTraceRunner(env, options)`.
- [ ] Use `buildJoiRealLoopGAblationContract(env)` for all flag validation.
- [ ] Use `buildJoiRealLoopTraceRow(payload)` for trace rows.
- [ ] Write artifacts only when enabled and contract-ready.
- [ ] Record source hashes, producer function, run id, split, condition, prompt-pack hash, LLM replay id, and replay
      inputs.
- [ ] Reject runtime-authority fields using the existing contract validator.

### Task 3: Optional Runtime Hook

Files:
- optionally `EgoDesktop/src/main.js`

- [ ] Instantiate the runner only after the explicit contract is ready.
- [ ] Capture `ego-desktop:chat-turn` outputs and `ego-desktop:renderer-ready` metadata.
- [ ] Keep all writes under `JOI_REAL_LOOP_TRACE_DIR`.
- [ ] Leave disabled-default path byte-equivalent at behavior level.

### Task 4: Report And Board

Files:
- `artifacts/egodesktop_joi_real_loop_g_ablation_trace_runner_v0/TRACE_RUNNER_REPORT.md`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-trace-runner-v0/STATUS.md`
- `Tasks/TASK_BOARD.yaml`
- `artifacts/task_board/outbox.jsonl` if needed

- [ ] Record actual verification commands.
- [ ] Record what was triggered and what remains untriggered.
- [ ] Update task status without claiming real-loop effect.

### Task 5: Verification

Commands:
- `node --test EgoDesktop/tests/joi_real_loop_g_ablation_trace_runner.test.js`
- `node --test EgoDesktop/tests/joi_real_loop_g_ablation_harness.test.js`
- `cd EgoDesktop && npm test`
- `git diff --check`
- `python scripts/codex_session_guard.py --mutation-scope docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-trace-runner-v0/MUTATION_SCOPE.yaml closeout-check --format markdown`

## Self-Review Checklist

- No default runtime enablement.
- No duplicate verdict logic.
- No same-pack static replay positive evidence.
- No authority-bearing field accepted in trace or adapter payload.
- No program-state or evidence-ledger claim update.
- Final wording stays at trace-runner contract only unless a real-loop artifact proves more.
