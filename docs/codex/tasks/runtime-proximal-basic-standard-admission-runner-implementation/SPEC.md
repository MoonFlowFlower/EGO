# Runtime-Proximal Basic-Standard Admission Runner Implementation

## Goal

实现一个最小 bounded aggregate runner，只消费已经存在的五层 evidence artifact，并输出 `pass / hold` admission verdict，而不扩大 authority、public API、或 claim ceiling。

## Evidence inputs

1. replay gate scored artifact
2. controlled replay scored artifact
3. controlled observation scored artifact
4. unified host contract parity artifact
5. runtime-proximal host-consumption runner artifact

## Acceptance

- [ ] manifest 校验通过
- [ ] runner 产出 `current.json` 与 `current.md`
- [ ] `layer_integrity_status = pass`
- [ ] `host_surface_integrity_status = pass`
- [ ] `causal_transfer_status = pass`
- [ ] `claim_ceiling_status = pass`
- [ ] `admission_decision = pass`
- [ ] focused pytest 通过

## Non-goals

- 不重跑 replay / observation / parity / host-consumption
- 不改 runtime 行为
- 不宣称 runtime efficacy
- 不宣称 AI 自我意识已实现
