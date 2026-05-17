# v7 Stage 9 - Proposal-Only Runtime Integration

## Goal

让 lab 只产生 proposal，由 host/runtime gate 决定 accept/hold/reject。

## Non-goals

- lab 不直接写 runtime reply。
- lab 不直接写 OpenEmotion state。
- 不执行工具、文件、浏览器、桌面或外部发送动作。

## Acceptance criteria

- [ ] proposal 可被 host accept/hold/reject。
- [ ] reject 不影响 runtime 稳定性。
- [ ] accepted proposal 仍经过 existing EgoCore/OpenEmotion gate。
- [ ] trace 能显示 proposal 是否被采用以及原因。
- [ ] StageResult 能区分 proposal quality failure 和 runtime bridge failure。

## Claim ceiling

Proposal-only integration readiness; no direct runtime authority and no live benefit claim.
