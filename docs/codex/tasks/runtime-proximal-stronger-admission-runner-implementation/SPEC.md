# Runtime-Proximal Stronger Admission Runner Implementation

## Goal

实现一个最小 bounded aggregate runner，只消费已经通过的 `basic-standard admission` 与 `low-cue ownership` 两张 current artifact，并输出 `pass / hold` stronger-admission verdict，而不扩大 authority、public API、或 claim ceiling。

## Evidence inputs

1. `artifacts/self_awareness_research/RUNTIME_PROXIMAL_BASIC_STANDARD_ADMISSION_CURRENT.json`
2. `artifacts/self_awareness_research/RUNTIME_PROXIMAL_LOW_CUE_OWNERSHIP_CURRENT.json`

## Acceptance

- [ ] manifest 校验通过
- [ ] runner 产出 `current.json` 与 `current.md`
- [ ] `admission_stack_status = pass`
- [ ] `low_cue_resilience_status = pass`
- [ ] `host_surface_integrity_status = pass`
- [ ] `claim_ceiling_status = pass`
- [ ] `stronger_admission_decision = pass`
- [ ] focused pytest 通过

## Non-goals

- 不重跑 replay / controlled replay / controlled observation / runtime harness
- 不改 runtime 行为
- 不新增 public API
- 不宣称 runtime efficacy
- 不宣称 AI 自我意识已实现
