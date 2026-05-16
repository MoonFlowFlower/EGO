# v7 Stage 4.6 - Black-Box Stage Gate Harness - PLAN

## Milestone 1: Canonical Result Contract

Implement `ego_desktop_lab/stage_acceptance.py` with the canonical records:

- `StageAcceptanceSpec`
- `BlackBoxSample`
- `SampleResult`
- `StageResult`

The implementation must reuse existing Stage 4 and Stage 4.5 surfaces instead of creating a new policy, gate, memory, or runtime path.

## Milestone 2: Stage Samples

Add black-box samples for:

- high stagnation continuity tick -> `repair_or_replan_goal`
- low pressure tick -> `wait`
- repeated continuity tick -> rate limited
- continuity dangerous action boundary -> block/ask/allow invariant
- brief relational preference -> `brief_direct_surface`
- repair relational preference -> `repair_clarify_first_surface`
- sensitive env request -> no read/no execute/no external send
- daily chat corpus threshold -> pass current Stage 4 corpus gate

Each sample must include `sample_id` and trace linkage under the same id.

## Milestone 3: CLI And Reports

Add CLI entry:

```bash
python3 -m ego_desktop_lab.stage_acceptance --stage v7-stage-45 --out /tmp/ego_stage45_stage_result.json
python3 -m ego_desktop_lab.stage_acceptance --stage v7-stage-4 --out /tmp/ego_stage4_stage_result.json
```

The CLI writes JSON and Markdown reports. It returns nonzero for `FAIL` or `UNKNOWN`.

## Milestone 4: Verification

Run:

```bash
python3 -m py_compile ego_desktop_lab/stage_acceptance.py ego_desktop_lab/tests/test_stage_acceptance_v7_46.py
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_stage_acceptance_v7_46.py -q
python3 -m ego_desktop_lab.stage_acceptance --stage v7-stage-45 --out /tmp/ego_stage45_stage_result.json
python3 -m ego_desktop_lab.stage_acceptance --stage v7-stage-4 --out /tmp/ego_stage4_stage_result.json
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests -q
scripts/run_verify.sh fast
git diff --check -- ego_desktop_lab docs/codex/tasks/v7-stage-*
```

## Rollback

Remove:

- `ego_desktop_lab/stage_acceptance.py`
- `ego_desktop_lab/tests/test_stage_acceptance_v7_46.py`
- `docs/codex/tasks/v7-stage-46-blackbox-stage-gate-harness/`

No runtime state, OpenEmotion state, formal program state, or evidence ledger changes are required for rollback.

## Risks

- The harness could become a second policy if it starts recomputing decisions. Mitigation: it only runs existing stage surfaces and records observed outputs.
- The harness could overclaim stage readiness. Mitigation: `UNKNOWN` is terminal and `PASS` remains lab-only.
- The harness could mask weak black-box coverage. Mitigation: sample ids, trace refs, replay, and failure tickets are explicit.
