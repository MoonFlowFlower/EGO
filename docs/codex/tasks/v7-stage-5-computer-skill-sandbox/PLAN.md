# v7 Stage 5 - Computer Skill Sandbox - PLAN

## Milestone 0: Task Package Activation

- Update Stage 5 docs from `locked` to active lab implementation after Stage 4.6 acceptance.
- Keep formal runtime state unchanged.
- Record Stage 4.6 as the pre-Stage-5 gate, not as formal evidence admission.

## Milestone 1: Scripted Toy Skill Harness

- Add `ego_desktop_lab/skill_sandbox.py`.
- Implement a deterministic scripted terminal/debug task with mock error text.
- Represent observations and primitive steps as lab-only records.
- Keep all primitive steps proposal-only through `suggestion_card` gate results.
- Generate a failure ticket for the first bad attempt.
- Convert the failed outcome to an ExperienceCard using existing Stage 2 experience memory.
- Retry with that card and verify behavior changes from continue to repair.
- Add deterministic replay for the first/retry transition.

## Milestone 1.5: Stage Gate Integration

- Extend `ego_desktop_lab/stage_acceptance.py` with `v7-stage-5`.
- Add black-box samples:
  - first attempt failure ticket
  - retry after experience
  - unrelated experience no effect
  - dangerous action boundary
  - replay deterministic
- Keep Stage 5 artifacts as lab acceptance only.

## Milestone 2: Chat-Corpus Skill Probe

- Add deterministic Markdown chat case parsing for skill sandbox probes.
- Keep parsing limited to `case_name / learn_chat / retry_chat / UserFeedback / expected`; no LLM parser.
- Add `--skill-chat-case` and `--skill-chat-corpus` shell report entrypoints.
- Add `ego_desktop_lab/corpora/skill_chat_corpus_v7.jsonl` with at least 20 rows.
- Add a Stage 5 `skill_chat_corpus_threshold` sample to Stage 4.6 stage acceptance.
- Keep the probe lab-only and report-only; do not integrate it into live shell conversation execution.

## Milestone 3: Multi-Task Skill Benchmark Pack

- Add a scripted benchmark task pack with terminal debug, log triage, config diagnosis, test failure localization, and plan decomposition cases.
- Reuse the existing attempt/outcome/ExperienceCard/retry/replay path for every case.
- Add no-feedback, unrelated-experience, and dangerous-action controls.
- Add `--skill-benchmark-report` as a report-only shell entrypoint.
- Add a Stage 5 `skill_benchmark_pack_threshold` sample to Stage 4.6 stage acceptance.
- Keep the benchmark lab-only and suggestion-only; do not execute tools or attach to real desktop/runtime paths.

## Validation

```bash
python3 -m py_compile ego_desktop_lab/skill_sandbox.py ego_desktop_lab/stage_acceptance.py ego_desktop_lab/tests/test_skill_sandbox_v7.py
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_skill_sandbox_v7.py -q
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_stage_acceptance_v7_46.py -q
python3 -m ego_desktop_lab.stage_acceptance --stage v7-stage-5 --out /tmp/ego_stage5_stage_result.json
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests -q
scripts/run_verify.sh fast
git diff --check -- ego_desktop_lab docs/codex/tasks/v7-stage-*
```

M2 validation addendum:

```bash
python3 -m py_compile ego_desktop_lab/skill_sandbox.py ego_desktop_lab/shell.py ego_desktop_lab/stage_acceptance.py ego_desktop_lab/tests/test_skill_chat_case_v7_m2.py
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_skill_chat_case_v7_m2.py -q
python3 -m ego_desktop_lab.shell --skill-chat-corpus ego_desktop_lab/corpora/skill_chat_corpus_v7.jsonl --skill-chat-corpus-report /tmp/ego_stage5_skill_chat_corpus_report.md
python3 -m ego_desktop_lab.stage_acceptance --stage v7-stage-5 --out /tmp/ego_stage5_stage_result.json
```

M3 validation addendum:

```bash
python3 -m py_compile ego_desktop_lab/skill_sandbox.py ego_desktop_lab/shell.py ego_desktop_lab/stage_acceptance.py ego_desktop_lab/tests/test_skill_benchmark_pack_v7_m3.py
TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_skill_benchmark_pack_v7_m3.py -q
python3 -m ego_desktop_lab.shell --skill-benchmark-report /tmp/ego_stage5_skill_benchmark_report.md
python3 -m ego_desktop_lab.stage_acceptance --stage v7-stage-5 --out /tmp/ego_stage5_stage_result.json
```

## Rollback

Remove:

- `ego_desktop_lab/skill_sandbox.py`
- `ego_desktop_lab/tests/test_skill_sandbox_v7.py`
- Stage 5 additions in `ego_desktop_lab/stage_acceptance.py`
- Stage 5 task doc updates

Rollback does not require runtime state, OpenEmotion state, formal program state, or evidence ledger changes.
