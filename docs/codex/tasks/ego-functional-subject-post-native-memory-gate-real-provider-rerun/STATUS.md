# Status

Status: accepted

## Decisions

- Run the same 20-case Functional Subject scripted real-provider trial used for EGO-FS-047.
- Do not modify EgoOperator runtime in this task.
- Treat GPT-5.5 judge as a strong scripted reviewer but not as authority to raise claim ceiling or close human-required gates.

## Verification

- Real provider run:
  - `python3 scripts/run_ego_experience_trial.py --functional-subject-trial --judge-with-codex --judge-model gpt-5.5 --case-timeout-seconds 60 --judge-timeout-seconds 600 --out /tmp/ego_fs_010_after_fs048_20260523_135605`
  - `status=scripted_functional_subject_judge_partial`
  - `provider_mode=openrouter`
  - GPT-5.5 judge `status=ok`, `verdict=partial`
- Scorecard:
  - `clean_first_pass=17/20`
  - `origin_counts={"first_pass_llm": 7, "native_memory_gate": 4, "outcome_prediction_gate": 6, "runtime_repair": 3}`
  - `provider_recovery_case_ids=[]`

## Evidence

- `EVIDENCE.post_native_memory_gate_real_provider_rerun.json`
- `/tmp/ego_fs_010_after_fs048_20260523_135605/functional_subject_trial_report.json`
- `/tmp/ego_fs_010_after_fs048_20260523_135605/functional_subject_trial_report.md`

## Remaining Risk

EGO-FS-010 remains blocked because GPT-5.5 judge is partial. Next work should target direct memory/approval/replay trace excerpts, negative baseline controls, adversarial persona-vs-gate cases, and restart/provider/context durability evidence.
