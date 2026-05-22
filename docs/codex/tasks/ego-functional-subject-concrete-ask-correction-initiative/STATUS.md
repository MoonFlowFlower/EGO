# Status

## Current

`accepted`

## Notes

- #94 v4 real-provider run reached GPT-5.5 judge successfully, but the judge returned `partial`.
- The remaining behavior blockers are concrete: `fs_07` generic ASK without questions, `fs_15` correction not visibly accepted, and `fs_20` menu-style initiative instead of one bounded next action.
- This task repairs those behavior-effect surfaces without closing the parent real-provider smoke gate.
- Local deterministic and NoLLM scripted trials now show:
  - `fs_07` asks concrete mechanism / observable-behavior / change-surface questions.
  - `fs_15` accepts the correction and restates the corrected intent without durable-memory overclaim.
  - `fs_20` selects one bounded next action with gate and stop condition.
- Real-provider v7 fast rerun reached GPT-5.5 judge and improved the target cases, but the total verdict remains `partial` due remaining blockers outside this task scope: generic model/provider fallback transcripts, `fs_17` memory-gate language overclaim, and weak transcript-visible planner/trace application.
- Next task: `EGO-FS-028`.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py scripts/tests/test_run_ego_experience_trial.py -q` -> pass.
- `python3 scripts/run_ego_experience_trial.py --functional-subject-trial --case-limit 20 --out /tmp/ego_fs_027_target_v4` -> local scripted target cases pass for this slice.
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, `277 passed`.
- Real-provider fast rerun:
  - `/mnt/c/Users/LEO/AppData/Local/Temp/ego_functional_subject_real_provider_rerun_v7_fast/functional_subject_trial_report.json`
  - GPT-5.5 verdict: `partial`.
  - Target cases: `fs_07`, `fs_15`, and `fs_20` improved enough to close this local/scripted behavior slice.
