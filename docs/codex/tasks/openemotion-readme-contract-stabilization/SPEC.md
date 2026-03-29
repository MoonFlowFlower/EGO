# OpenEmotion README Contract Stabilization

## Goal

Restore the OpenEmotion README runbook contract so repo-tracked documentation tests
pass without changing daemon behavior or widening scope beyond README and task
records.

## Non-goals

- Do not change OpenEmotion runtime behavior.
- Do not rewrite existing architecture sections unless needed for contract clarity.
- Do not fix unrelated OpenEmotion pytest failures outside README/documentation gates.

## Constraints

- Boundary: this is a documentation contract fix, not an implementation slice.
- Repo: reuse real commands, service files, scripts, and env vars already tracked in
  `OpenEmotion`.
- Environment: keep examples cross-platform where possible; do not invent commands
  not grounded in repo files.
- Release: keep diff scoped to README plus task accounting files.

## Acceptance criteria

- [ ] `OpenEmotion/tests/test_documentation.py` passes.
- [ ] `OpenEmotion/tests/test_comprehensive_fixed.py::TestDocumentationComprehensive::test_readme_content` passes.
- [ ] `python3 scripts/codex/verify_repo.py --mode fast` passes after the README fix.

## Known risks / dependencies

- Risk: README drift may reappear if future runtime changes are not reflected here.
- Dependency: commands and env vars referenced in README must exist in repo-tracked
  files such as `Makefile`, `pyproject.toml`, and `deploy/systemd/user/emotiond.service`.
- External blocker: none expected for this slice.

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `OpenEmotion/tests/test_documentation.py`
- `OpenEmotion/tests/test_comprehensive_fixed.py`
- `OpenEmotion/Makefile`
- `OpenEmotion/pyproject.toml`
- `OpenEmotion/deploy/systemd/user/emotiond.service`
- `OpenEmotion/README.md`
