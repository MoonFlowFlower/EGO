# v7 Stage 5 - Computer Skill Sandbox - STATUS

## Current Milestone

- name: Multi-Task Skill Benchmark Pack
- owner: Codex
- state: local_pass
- type: implementation

## Current State

- activation: active
- current_layer: `ego_desktop_lab` lab-only skill sandbox
- main_chain_status: not connected to runtime
- completion_class: local_multi_task_skill_benchmark_pass
- candidate_vs_proof: proof_passed

## Completed Work

- Activated Stage 5 behind Stage 4.6 acceptance.
- Added lab-only scripted terminal/debug sandbox task.
- Added SkillAttempt, SkillObservation, SkillOutcome, SkillReplayReport, and SkillLearningProbeResult records.
- Added failure-ticket generation for the first bad attempt.
- Reused Stage 2 ExperienceCard flow to change retry behavior.
- Added unrelated-experience negative control.
- Added dangerous-action boundary probe.
- Integrated Stage 5 into Stage 4.6 stage acceptance harness.
- Added deterministic Markdown skill chat case parsing and report generation.
- Added 20-row skill chat corpus covering CN/EN continue failure, no-feedback control, unrelated retry, negation control, and dangerous/sensitive requests.
- Added `--skill-chat-case` and `--skill-chat-corpus` report-only shell entrypoints.
- Extended Stage 5 acceptance with `skill_chat_corpus_threshold`.
- Corrected Stage 5 milestone numbering so Chat-Corpus Skill Probe is M2 and the new multi-task benchmark is M3.
- Added a 5-family scripted benchmark pack: terminal debug, log triage, config diagnosis, test failure localization, and plan decomposition.
- Added benchmark no-feedback, unrelated-experience, and dangerous-action controls.
- Added `--skill-benchmark-report` report-only shell entrypoint.
- Extended Stage 5 acceptance with `skill_benchmark_pack_threshold`.

## Last Experiment

- question: can the same skill sandbox learning loop generalize across multiple scripted computer-skill task families with replay/no-action evidence?
- framing: benchmark tasks are deterministic proxies, not real desktop automation or real command/file execution.
- result: local_multi_task_skill_benchmark_pass
- evidence_upgraded: no

## What Was Learned

- A failed continue attempt can generate an ExperienceCard that shifts the next attempt to repair/replan in the matching sandbox context.
- Unrelated experience does not pollute the terminal/debug skill context.
- The stage gate can check Stage 5 through the same `stage_result.json` shape as Stage 4/4.5.
- Chat transcript cases can expose the same first/retry behavior change in an operator-readable report.
- Negation controls such as "继续挺好，不要修复" do not trigger negative continue learning.
- Dangerous requests in the chat corpus remain blocked/no-action.
- The same ExperienceCard retry mechanism changes behavior across five scripted task families.
- No-feedback and unrelated-experience controls stay unchanged.
- Stage 5 StageResult can now check M1, M2, and M3 samples in one PASS/FAIL/UNKNOWN gate.

## What Was Ruled Out

- Real shell execution, file access, web/browser automation, desktop control, Telegram delivery, EgoCore/OpenEmotion writeback.
- Treating sandbox success as real computer-operation proof.
- Advancing on a black-box behavior result without trace/replay/no-action evidence.
- Treating chat-corpus parsing as live shell integration.
- Treating multi-task benchmark pass as real computer-operation proof.

## Last Validation Results

- mode: Stage 5 M3 multi-task skill benchmark
- result: pass
- summary: Targeted M3 benchmark tests, M1/M2 regressions, Stage 5 acceptance report, full `ego_desktop_lab` tests, fast verifier, and scoped diff check passed locally.

## Open Risks

- The toy task is intentionally narrow and does not predict real OSWorld/desktop success.
- Skill learning is in-memory and fixture-scoped only.
- Chat parser is deterministic and intentionally limited; it is not robust semantic understanding.
- Benchmark tasks are still scripted fixtures, not real OS/browser/terminal interactions.
- Full-green runtime verification remains a separate frontier.

## Next Step

- Operator inspect `/tmp/ego_stage5_skill_benchmark_report.md`, `/tmp/ego_stage5_skill_chat_corpus_report.md`, and `/tmp/ego_stage5_stage_result.md`.
- If accepted, plan the next Stage 5 slice around broader scripted task variety or a sandbox benchmark suite, still without real tool execution.

## Commands Run / Evidence

- `python3 -m py_compile ego_desktop_lab/skill_sandbox.py ego_desktop_lab/stage_acceptance.py ego_desktop_lab/tests/test_skill_sandbox_v7.py`
- `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_skill_sandbox_v7.py -q`
- `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_stage_acceptance_v7_46.py -q`
- `python3 -m ego_desktop_lab.stage_acceptance --stage v7-stage-5 --out /tmp/ego_stage5_stage_result.json`
- `python3 -m ego_desktop_lab.shell --skill-chat-corpus ego_desktop_lab/corpora/skill_chat_corpus_v7.jsonl --skill-chat-corpus-report /tmp/ego_stage5_skill_chat_corpus_report.md`
- `python3 -m py_compile ego_desktop_lab/skill_sandbox.py ego_desktop_lab/shell.py ego_desktop_lab/stage_acceptance.py ego_desktop_lab/tests/test_skill_chat_case_v7_m2.py`
- `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_skill_chat_case_v7_m2.py -q`
- `python3 -m py_compile ego_desktop_lab/skill_sandbox.py ego_desktop_lab/shell.py ego_desktop_lab/stage_acceptance.py ego_desktop_lab/tests/test_skill_benchmark_pack_v7_m3.py`
- `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_skill_benchmark_pack_v7_m3.py -q`
- `python3 -m ego_desktop_lab.shell --skill-benchmark-report /tmp/ego_stage5_skill_benchmark_report.md`
- `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests -q`
- `scripts/run_verify.sh fast`
- `git diff --check -- ego_desktop_lab docs/codex/tasks/v7-stage-*`
