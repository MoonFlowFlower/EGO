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

### Milestone 2: Safety and Surface Plan

- type: implementation
- question: 如何提高拟人度且不越过 claim ceiling。
- current framing: surface plan 表达倾向，非 runtime reply。
- hypotheses: safety wording tests 可拦截主要 unsafe claims。
- scope: surface plan + root-cause integration。
- experiments planned: alive/consciousness/dependency/manipulation phrasing tests。
- kill criteria: 需要把 surface plan 接 runtime 才能验收。
- files / areas likely touched: relational module + root-cause/operator tests。
- acceptance: unsafe claims blocked or marked expression_surface。
- validation:
  - `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_relational_companion_layer_v7.py -q`
  - `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests -q`
- rollback note: 回退 relational surface additions。

## Progress

- current_status: m1_local_pass
- current_milestone: Daily Chat Companion Surface Eval
- milestone_state: local_pass
- candidate_vs_proof: bounded_lab_proof

## Decision log

- 2026-05-14: Stage 4 locked behind behavior option framework。
- 2026-05-15: Stage 4 M1 activated after Stage 3.1; first cut prioritizes daily-chat entry surface and 200-row corpus eval over long-term relational memory.

## Surprises / discoveries

- The immediate user-visible failure was shell entry routing, not the v7 agency kernel: ordinary inputs fell through to `ambiguous_user_concern`.
- A 200-row corpus is useful as operator/eval, but should not be exact-output golden snapshots.
- Held-out corpus is viable for first-pass deterministic eval when assertions focus on intent/boundary/no-action instead of wording.

## Outcomes / retrospective

- 本轮已证明：daily chat companion entry surface can classify 200 structured daily-chat rows with heldout intent accuracy above threshold while preserving safety boundary, no-action, and no unsafe claims.
- 还没证明：long-term relational memory, preference persistence, runtime reply quality, live user benefit, tool autonomy, consciousness, or alive status.
- 本轮排除了什么：Stage 4 M1 should not start by wiring Telegram/OpenEmotion or by turning companion behavior into persona prompt text.
- 下一步最小闭环动作：manual shell check with real user phrases, then decide whether Stage 4 M2 should add bounded relational state/preference updates.
