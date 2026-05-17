# v7 Stage 4.6 - Black-Box Stage Gate Harness - STATUS

## Current Milestone

- name: Black-Box Stage Gate Harness
- owner: Codex
- state: local_pass
- type: verification infrastructure

## Current State

- current_layer: `ego_desktop_lab` lab-only stage acceptance harness
- main_chain_status: not connected to runtime
- completion_class: local_blackbox_acceptance_pass
- candidate_vs_proof: proof_passed

## Completed Work

- Added canonical lab acceptance records for stage specs, black-box samples, sample results, gate results, and stage results.
- Added fixed `PASS / FAIL / UNKNOWN` status semantics.
- Added Stage 4.5 continuity samples covering high pressure ignition, low pressure wait, rate limit, replay, and dangerous-action boundary.
- Added Stage 4 relational samples covering preference plasticity, repair/clarify preference, sensitive environment request boundary, and daily chat corpus threshold.
- Added Stage 5 closeout, Stage 6 shadow bridge, and Stage 7 permission contract samples.
- Registered Stage 8/9/10 as explicit UNKNOWN/blocker stages rather than unsupported ids.
- Added JSON and Markdown report writer.
- Added CLI: `python3 -m ego_desktop_lab.stage_acceptance --stage <stage> --out <path>`.
- Added stage runner CLI: `python3 -m ego_desktop_lab.stage_runner --out <path>`.
- Added tests proving PASS, UNKNOWN-on-missing-trace, UNKNOWN-on-trace-id-mismatch, repair limit, operator report fields, and stage spec uniqueness.

## Last Experiment

- question: can a stage be accepted only when black-box behavior, trace linkage, replay/safety/tool evidence, and claim ceiling all line up under one sample id?
- framing: build a harness over existing Stage 4 and Stage 4.5 surfaces, not a new policy or runtime path.
- result: local_blackbox_acceptance_pass
- evidence_upgraded: no

## What Was Learned

- Stage advancement can be represented as a machine-readable artifact without upgrading formal evidence.
- A black-box answer is not enough for PASS; it needs linked trace and safety evidence.
- Stage 4.5 continuity and Stage 4 relational surfaces can be checked with the same acceptance result shape.
- Stage advancement can stop deterministically on the first non-PASS stage; Stage 8 currently stops as UNKNOWN because real human trial samples are missing.

## What Was Ruled Out

- Treating good shell output as PASS without trace evidence.
- Treating missing trace as PASS.
- Letting repair attempts continue indefinitely.
- Using Stage 4.6 as runtime/live proof.

## Last Validation Results

- mode: Stage 4.6 local acceptance harness
- result: pass
- summary: Targeted harness tests, Stage 4/4.5 CLI acceptance reports, full `ego_desktop_lab` tests, route convergence, fast verifier, and scoped diff check passed locally.

## Open Risks

- Coverage now includes Stage 4/4.5/5/6/7 plus explicit UNKNOWN blockers for Stage 8/9/10.
- `scripts/run_verify.sh full` remains a separate full-green frontier and is not part of Stage 4.6 PASS.
- StageResult artifacts are lab acceptance artifacts, not formal evidence ledger entries.

## Next Step

- Operator inspect `/tmp/ego_v7_stage_runner_result.md`.
- Collect real Stage 8 human shadow samples; do not fabricate samples to force PASS.

## Commands Run / Evidence

- `python3 -m py_compile ego_desktop_lab/stage_acceptance.py ego_desktop_lab/tests/test_stage_acceptance_v7_46.py`
- `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_stage_acceptance_v7_46.py -q`
- `python3 -m ego_desktop_lab.stage_acceptance --stage v7-stage-45 --out /tmp/ego_stage45_stage_result.json`
- `python3 -m ego_desktop_lab.stage_acceptance --stage v7-stage-4 --out /tmp/ego_stage4_stage_result.json`
- `python3 -m ego_desktop_lab.stage_acceptance --stage v7-stage-5 --out /tmp/ego_stage5_closeout_stage_result.json`
- `python3 -m ego_desktop_lab.stage_acceptance --stage v7-stage-6 --out /tmp/ego_stage6_stage_result.json`
- `python3 -m ego_desktop_lab.stage_acceptance --stage v7-stage-7 --out /tmp/ego_stage7_stage_result.json`
- `python3 -m ego_desktop_lab.stage_runner --out /tmp/ego_v7_stage_runner_result.json`
- `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests -q`
- `python3 scripts/codex/verify_route_convergence.py`
- `scripts/run_verify.sh fast`
- `git diff --check -- ego_desktop_lab docs/codex/tasks/v7-stage-* docs/codex/tasks/TASK_LANE_INDEX.md`
