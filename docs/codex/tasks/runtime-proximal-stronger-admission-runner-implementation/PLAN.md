# Runtime-Proximal Stronger Admission Runner Implementation - PLAN

## Purpose

把已经冻结的 `stronger admission` planning card 收成一个可执行、可复核的 bounded aggregate runner。

## Work items

1. Freeze the runner contract
   - 只允许消费 `basic-standard admission` 与 `low-cue ownership` 两张 current artifact
2. Implement the aggregate gate
   - 把 lower-layer admission 结果与 low-cue resilience 结果组合成 stronger verdict
3. Keep the surface bounded
   - 明确检查 frozen host-consumable surface 与 bounded claim ceiling 没有漂移
4. Add focused regression coverage
   - manifest 校验 + current stack pass

## Planned outputs

The runner should emit at least:

- `admission_stack_status`
- `low_cue_resilience_status`
- `host_surface_integrity_status`
- `claim_ceiling_status`
- `stronger_admission_decision`
- `reviewer_gate_ready`
- `blocked_reasons`

## Validation

- `python3 -m py_compile scripts/codex/run_runtime_proximal_stronger_admission_runner.py EgoCore/tests/test_runtime_proximal_stronger_admission_runner.py`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_proximal_stronger_admission_runner.py -q -s`
- `python3 scripts/codex/run_runtime_proximal_stronger_admission_runner.py`

## Completion

This slice is complete when the stronger runner deterministically returns a bounded `pass / hold` verdict from the two frozen current artifacts, keeps host-surface / claim-ceiling checks green, and leaves runtime efficacy / live-benefit / consciousness claims out of bounds.
