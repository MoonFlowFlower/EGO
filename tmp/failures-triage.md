# Failure Triage (Step 1)

Date: 2026-03-02
Scope: First 5 failures from `PYTHONPATH=. .venv/bin/pytest -q --maxfail=5`

## 1) tests/test_knob_registry.py::TestKnobRegistry::test_load_config
- Type: A (旧测试不兼容 / fixture bug)
- Evidence: `JSONDecodeError` reading temp JSON config (`s=''`)
- Root cause: fixture writes JSON to `NamedTemporaryFile` but does not flush/fsync before registry re-opens file.
- Action: update fixture to `f.flush(); os.fsync(f.fileno())` before `yield`
- Impact: low (test-only)

## 2) tests/test_knob_registry.py::TestKnobRegistry::test_allowlist_parameter_allowed
- Type: A
- Evidence: setup fails in shared `registry` fixture with same `JSONDecodeError`
- Action: same fixture fix
- Impact: low

## 3) tests/test_knob_registry.py::TestKnobRegistry::test_hard_freeze_parameter_rejected
- Type: A
- Evidence: setup fails in shared `registry` fixture with same `JSONDecodeError`
- Action: same fixture fix
- Impact: low

## 4) tests/test_knob_registry.py::TestKnobRegistry::test_unknown_parameter_rejected
- Type: A
- Evidence: setup fails in shared `registry` fixture with same `JSONDecodeError`
- Action: same fixture fix
- Impact: low

## 5) tests/test_knob_registry.py::TestKnobRegistry::test_range_validation
- Type: A
- Evidence: setup fails in shared `registry` fixture with same `JSONDecodeError`
- Action: same fixture fix
- Impact: low

## Decision
All five are **A类（旧测试 fixture 不稳定）**. No evidence of core regression yet.
