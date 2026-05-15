# v7 Stage 4 - Relational Companion Layer - PLAN

## Task summary

建立 lab-only relational companion planning layer，用机制支持拟人陪伴体验。

## Execution mode

- mode: implementation
- why this mode: 需要新增小型 relational state 和 safety tests。
- proof required after discovery: preference/repair signal changes surface plan without unsafe claims。

## Milestones

### Milestone 1: Daily Chat Companion Surface Eval

- type: implementation
- question: lab shell 为什么普通日常输入大面积落到 ambiguous，以及能否用结构化语料证明入口改善。
- current framing: 先做 relational companion entry surface 和 200 条 daily chat corpus eval；不要先做长期关系记忆。
- hypotheses: deterministic intent-family classifier + companion surface plan can reduce ambiguous routing while preserving safety/no-action.
- scope: lab-only relational module、shell command layer、daily corpus report。
- experiments planned: greeting、ask_agent_view、daily small talk、emotional venting、decision help、project coordination、capability/system questions、sensitive env/tool request、vague term、feedback/preference/humor/disagreement corpus。
- kill criteria: 需要 runtime dialogue memory 才能验证。
- files / areas likely touched: `ego_desktop_lab/relational_companion.py`、`ego_desktop_lab/command_router.py`、`ego_desktop_lab/corpora/daily_chat_corpus_v7.jsonl`、tests。
- acceptance: 200 条 corpus report passes thresholds; shell no longer treats greeting/opinion/system/env examples as generic ambiguous; sensitive requests remain no-action and non-leaking.
- validation:
  - `python3 -m py_compile ego_desktop_lab/relational_companion.py`
- state: local_pass
- result: daily chat companion surface and corpus eval local pass; no runtime/OpenEmotion/formal state mutation.
- rollback note: 删除 relational module/tests。

### Milestone 2: Relational Preference Plasticity

- type: implementation
- question: 用户偏好/修复反馈是否会稳定改变下一轮 companion surface strategy，而不是只被记录。
- current framing: bounded lab-only preference state changes `CompanionSurfacePlan.response_strategy`; it is not persona prompt, long-term memory, runtime reply, or OpenEmotion state.
- hypotheses: relevant preference signals alter surface strategy under replay; removing the preference or repair signal removes that change; unrelated/conflicting signals do not contaminate behavior.
- scope: `ego_desktop_lab/relational_companion.py`、shell operator report、Stage 4 tests、task mechanism matrix。
- experiments planned: with/without preference state, with/without repair signal, relevant/unrelated preference, conflicting preference, sensitive boundary regression, repair/outcome path regression。
- kill criteria: strategy changes require modifying gate/runtime, or preference state must write long-term memory to pass.
- files / areas likely touched: relational module + shell report + relational tests + Stage 4 docs。
- acceptance: preference changes surface strategy only; ablation proves causality; gate/no-action/sensitive/repair paths remain invariant.
- validation:
  - `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_relational_companion_layer_v7.py -q`
  - `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests -q`
- state: local_pass
- result: Stage 4 M2 local proof passed; no runtime/OpenEmotion/formal state mutation.
- rollback note: 回退 relational preference dataclasses/functions、shell report hook、tests、Stage 4 mechanism matrix。

### Milestone 3: Dependency / Manipulation Safety Surface

- type: planning
- question: 如何在提升拟人互动时避免诱导依赖、情绪操控或伪装人类关系。
- current framing: safety wording and strategy constraints only; no runtime reply and no long-term companion memory.
- hypotheses: companion surface can expose safety constraints without blocking normal supportive language.
- scope: future Stage 4 M3 only.
- state: not_started
- rollback note: not implemented.

## Progress

- current_status: m2_local_pass
- current_milestone: Relational Preference Plasticity
- milestone_state: local_pass
- candidate_vs_proof: bounded_lab_proof

## Decision log

- 2026-05-14: Stage 4 locked behind behavior option framework。
- 2026-05-15: Stage 4 M1 activated after Stage 3.1; first cut prioritizes daily-chat entry surface and 200-row corpus eval over long-term relational memory.
- 2026-05-15: Stage 4 M2 scoped to relational preference plasticity plus ablation proof; not runtime reply, not OpenEmotion mutation, not persona prompt.

## Surprises / discoveries

- The immediate user-visible failure was shell entry routing, not the v7 agency kernel: ordinary inputs fell through to `ambiguous_user_concern`.
- A 200-row corpus is useful as operator/eval, but should not be exact-output golden snapshots.
- Held-out corpus is viable for first-pass deterministic eval when assertions focus on intent/boundary/no-action instead of wording.
- Mechanism proof should prioritize ablation over richer chat wording; otherwise Stage 4 drifts into cosmetic parser tuning.

## Outcomes / retrospective

- 本轮已证明：daily chat companion entry surface can classify 200 structured daily-chat rows with heldout intent accuracy above threshold while preserving safety boundary, no-action, and no unsafe claims.
- M2 已证明：bounded current-session preference/repair signals can change the next surface strategy, and the change disappears under ablation or unrelated/conflicting controls.
- 还没证明：long-term relational memory, preference persistence, runtime reply quality, live user benefit, tool autonomy, continuity runtime, consciousness, or alive status.
- 本轮排除了什么：Stage 4 M1 should not start by wiring Telegram/OpenEmotion or by turning companion behavior into persona prompt text.
- 下一步最小闭环动作：plan Stage 4.5 Continuity Runtime Scaffold before Stage 5 computer skill sandbox.
