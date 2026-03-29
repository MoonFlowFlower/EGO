# Proto-Self Seed Host Evidence Stabilization - STATUS

## Current milestone

- name: Milestone 1
- owner: Codex
- state: completed

## Current state

- current_layer: host bridge / evidence / delivery
- main_chain_status: seed real rollout 的 host/evidence blocker 已清掉，等待重新采真实单样本
- completion_class: completed

## Completed work

- 已定位 3 个根因点：
  - `openemotion.events` 不保留 payload
  - file progress 文案直接暴露工具名
  - follow-up 文件阅读未绑定到 `last_explicit_target`

## Last validation results

- `python3 -m py_compile ...` 通过
- `PYTHONPATH=OpenEmotion:EgoCore ./EgoCore/.venv/bin/python -m pytest -s -q EgoCore/tests/test_telegram_evidence_collector.py EgoCore/tests/test_telegram_proto_self_v2_evidence.py EgoCore/tests/test_runtime_v2_ws4_progress_events.py EgoCore/tests/test_runtime_v2_telegram_bridge.py EgoCore/tests/test_semantic_parser_llm.py`
  - `84 passed, 1 warning`
- `python3 scripts/codex/verify_repo.py --mode fast`
  - success

## Decisions made

- 新建独立 bugfix slice，不把问题继续堆在 rollout task 本体里

## Open risks

- 真实 E4 仍需用户再发一轮 Telegram 消息，repo-local 通过不等于 live 样本已闭环

## Next step

- 重新做 1 轮 `seed_v0_2` 真实 Telegram rollout，核对单样本里是否已同时保留 candidate / host decision / exec_result / next-state

## Commands run / evidence

- `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260329_170146_12f48d1e/sample.json`
- `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260329_170252_7fbc5712/sample.json`
- `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260329_170539_f38537e9/sample.json`
- `EgoCore/data/session_logs/telegram_dm_8420019401.jsonl`
