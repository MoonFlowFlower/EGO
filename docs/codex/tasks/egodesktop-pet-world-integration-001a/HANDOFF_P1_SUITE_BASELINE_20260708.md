# Handoff — P1 suite baseline waiver STOP point

Date: 2026-07-08
Task/card: `CODEX-INSTRUCTION-PET-P1-SUITE-BASELINE-WAIVER-20260707K (Red)`
Task dir: `docs/codex/tasks/egodesktop-pet-world-integration-001a/`

## Current repo state at handoff

- Repo: `D:\Project\AIProject\MyProject\Ego`
- Branch: `main`
- HEAD: `5f5311a2cdd523bb54634c15f38f9f29f6d58837`
- Upstream state: ahead of `origin/main` by 1, behind 0
- Remote/push: **not pushed**
- Worktree: intentionally dirty because the preserved P1 working tree is still present.

Dirty paths currently expected / preserved:

```text
M  EgoDesktop/src/main.js
M  EgoDesktop/src/preload.js
?? EgoDesktop/src/petKernelBridge.js
?? EgoDesktop/src/petLive2dObserverMap.js
?? EgoDesktop/src/petMode.js
?? EgoDesktop/tests/pet_mode.test.js
?? EgoDesktop/tests/pet_static_gate_audit.test.js
?? EgoDesktop/viewer/pet.css
?? EgoDesktop/viewer/pet.html
?? EgoDesktop/viewer/petRenderer.js
?? artifacts/egodesktop_pet_world_integration_001a/p1/failure_manifest.json
?? artifacts/egodesktop_pet_world_integration_001a/p1/schema_report.json
?? artifacts/egodesktop_pet_world_integration_001a/p1/static_gate_audit.json
?? artifacts/egodesktop_pet_world_integration_001a/p1/trace.jsonl
?? docs/codex/tasks/egodesktop-pet-world-integration-001a/HANDOFF_P1_SUITE_BASELINE_20260708.md
```

Do **not** discard these P1 changes. They are the preserved P1 working tree for
the later Claude-cleared STEP4 rerun.

## What has been completed

Completed only STEP1–STEP3 of the Red Route B card:

1. P1 working tree was parked, P1-absent pytest baseline was captured at
   baseline commit `6948427a`, then P1 working tree was restored.
2. A closed 3-test suite baseline was recorded.
3. Addendum and suite-baseline helper were committed locally.
4. Execution stopped for Claude Red pre-check.

Baseline/addendum commit:

```text
5f5311a2cdd523bb54634c15f38f9f29f6d58837
pet-integration 001A: P1 suite baseline waiver (Red; no-NEW-failure gate + P1 EgoOperator-delta guard)
```

Committed files in that commit:

```text
EgoDesktop/src/petSuiteBaselineGate.js
EgoDesktop/tests/pet_suite_baseline_gate.test.js
artifacts/egodesktop_pet_world_integration_001a/p1/baseline_6948427a_pytest_q.log
artifacts/egodesktop_pet_world_integration_001a/p1/baseline_6948427a_pytest_targeted_vv_rA.log
artifacts/egodesktop_pet_world_integration_001a/p1/suite_baseline.json
docs/codex/tasks/egodesktop-pet-world-integration-001a/ADDENDUM_P1_SUITE_BASELINE.md
```

## Evidence and hashes

Source card:

```text
C:\Users\LEO\AppData\Local\Packages\CLAUDE~1\LOCALC~1\Roaming\Claude\LOCAL-~1\840EF4~1\5B836E~1\LO8D76~1\outputs\COAA6E~1.MD
SHA256 4650713279BEE8C08808C8F079841C3A99A747DE78722CFB2E29A1D9923DBBF4
```

Recorded artifacts:

```text
D:\Project\AIProject\MyProject\Ego\artifacts\egodesktop_pet_world_integration_001a\p1\suite_baseline.json
SHA256 FB6F06576F324E42F433AF8B8F859828095ED735CFA767831EBF39DC948ADA15

D:\Project\AIProject\MyProject\Ego\docs\codex\tasks\egodesktop-pet-world-integration-001a\ADDENDUM_P1_SUITE_BASELINE.md
SHA256 FC70CC117A07A554C711BB5948F361A1AFD71425B1D051847ECE8C46F8382026

D:\Project\AIProject\MyProject\Ego\artifacts\egodesktop_pet_world_integration_001a\p1\baseline_6948427a_pytest_q.log
SHA256 C109ACBA4572D47C679A87D10189231F74D8F54FB1D0B679D8D437673F84B2D9

D:\Project\AIProject\MyProject\Ego\artifacts\egodesktop_pet_world_integration_001a\p1\baseline_6948427a_pytest_targeted_vv_rA.log
SHA256 3222496637BD42DD9C948B609D3BB0C8F4080E2B0E673934F6704CFA59879072
```

P1-absent full pytest baseline:

```text
python -m pytest -q
observed in log: 3 failed, 1053 passed, 1 skipped in 607.06s (0:10:07)
```

The outer Codex shell timed out after pytest had printed the final summary; the
targeted verbose rerun below provides exact assertion evidence.

Targeted assertion capture:

```text
python -m pytest -q -vv -rA \
  labs/virtual_cat_pspc_v0/tests/test_admission_packet_contract.py::test_admission_packet_contract_has_no_egooperator_import_or_adapter_file \
  labs/virtual_cat_pspc_v0/tests/test_report_generation.py::test_experiment_runner_writes_canonical_reports \
  tests/test_ego_kernel_substrate.py::test_validation_runner_writes_contract_artifacts_and_passes

observed in log: 3 failed in 37.76s
```

Closed baseline node ids:

```text
labs/virtual_cat_pspc_v0/tests/test_admission_packet_contract.py::test_admission_packet_contract_has_no_egooperator_import_or_adapter_file
labs/virtual_cat_pspc_v0/tests/test_report_generation.py::test_experiment_runner_writes_canonical_reports
tests/test_ego_kernel_substrate.py::test_validation_runner_writes_contract_artifacts_and_passes
```

Exact assertion summaries:

1. `assert not adapter_path.exists()` failed because
   `EgoOperator/adapters/pspc_lab_adapter.py` exists.
2. `assert summary["go_no_go_review_status"] == "go"` failed because actual was
   `"no_go"`.
3. `assert result["verdict"] == "r0_substrate_pass"` failed because actual was
   `"r0_substrate_fail_hygiene"`.

P1 independence evidence:

- P1-added pet files grep for literal `EgoOperator`: `0` hits.
- P1 touched source delta scope currently has only the two pre-existing
  `EgoDesktop/src/main.js` hits.
- `p1_egooperator_ref_delta`: `0`.
- Pre-existing EgoDesktop JavaScript/report/test reference enumeration: `12`
  references, recorded in `suite_baseline.json`.

## Gate rule now registered

Suite gate is re-scoped as:

```text
set(current repo_pytest failing_tests) - set(closed_baseline) == empty
AND p1_egooperator_ref_delta == 0
```

The helper also emits:

```text
unexpectedly_passing = set(closed_baseline) - set(current repo_pytest failing_tests)
```

Any fourth pytest failure fails the gate. Wildcard waivers remain forbidden.

## Verification run before handoff

Passed:

```text
node --test EgoDesktop/tests/pet_suite_baseline_gate.test.js EgoDesktop/tests/pet_static_gate_audit.test.js EgoDesktop/tests/pet_mode.test.js
# 9 pass

node --test EgoDesktop/tests/*.test.js
# 112 pass

git diff --cached --check
# pass before commit

git diff --check
# pass after commit

python scripts/codex/lint_repo.py
# pass
```

Known failure / not repaired in this handoff:

```text
python scripts/codex/verify_repo.py --mode fast
# fail: generated file drift detected:
# D:\Project\AIProject\MyProject\Ego\docs\codex\tasks\TASK_LANE_INDEX.md
```

This was not repaired because the card scope was P1 suite-baseline governance,
and regenerating route views would be unrelated scope expansion.

Closeout gate:

```text
python scripts/codex_session_guard.py closeout-check --format markdown
# eligible=false
# blockers include push_pending, unsafe_dirty_paths, no_staged_changes
```

This is expected at this STOP point because the commit is local-only, push is not
authorized here, and the P1 working tree must remain dirty until Claude clears
STEP4.

## Hard stop / do-not rules for the next session

Do not run STEP4 until Claude Red pre-check explicitly clears this commit and
the preserved P1 working tree.

Do not:

- edit `EgoOperator/`;
- edit any of the three failing tests to make them pass;
- discard or stash-drop the preserved P1 working tree;
- push;
- commit final P1 wiring;
- widen the baseline beyond the exact three node ids;
- introduce wildcard waivers;
- mask a P1-introduced `EgoOperator` reference;
- touch P0 frozen modules or `scripts/ego_kernel`.

## Next action

Hand the following to Claude for Red pre-check:

1. commit `5f5311a2cdd523bb54634c15f38f9f29f6d58837`;
2. `suite_baseline.json` and `ADDENDUM_P1_SUITE_BASELINE.md` hashes above;
3. P1-absent pytest logs and exact assertions;
4. P1 `EgoOperator` grep evidence (`0` in P1-added pet files);
5. current dirty P1 working tree list.

If and only if Claude clears:

1. run STEP4 on the preserved P1 working tree;
2. rerun baseline-scoped G-PET-SCHEMA + G-PET-STATIC-GATE;
3. if no new failure and `p1_egooperator_ref_delta == 0`, scoped-commit P1
   wiring/artifacts;
4. only push if the card/user explicitly authorizes publication.

## Suggested first prompt for a new Codex session

```text
继续执行 EGO PET P1 Route B，但先不要跑 STEP4。

Repo: D:\Project\AIProject\MyProject\Ego
Start by reading:
1. AGENTS.md
2. docs/PROGRAM_STATE_UNIFIED.yaml
3. docs/codex/tasks/egodesktop-pet-world-integration-001a/HANDOFF_P1_SUITE_BASELINE_20260708.md
4. docs/codex/tasks/egodesktop-pet-world-integration-001a/ADDENDUM_P1_SUITE_BASELINE.md
5. artifacts/egodesktop_pet_world_integration_001a/p1/suite_baseline.json

Current STOP point: local commit 5f5311a2cdd523bb54634c15f38f9f29f6d58837
landed the P1 suite baseline waiver and addendum. P1 working tree is intentionally
dirty and must be preserved. Do not run STEP4, do not commit final P1, do not
push, and do not edit EgoOperator or the three failing tests unless Claude Red
pre-check has explicitly cleared this baseline/addendum commit.

First report: branch, HEAD, ahead/behind, dirty paths, exact baseline hashes, and
whether Claude clearance is available. If Claude clearance is unavailable, stop
and prepare the Claude Red pre-check packet only.
```

## Claim ceiling

`p1_suite_baseline_governance_record_only`.

This handoff does not prove P1 pass, product readiness, runtime integration
safety, learning attribution, stable user benefit, autonomy, agency,
subjectivity, consciousness, or real emotion.
