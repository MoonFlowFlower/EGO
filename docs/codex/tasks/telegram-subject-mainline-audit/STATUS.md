# Telegram Subject Mainline Audit - STATUS

## Current milestone

- name: `Milestone 2: Current Audit Report`
- owner: `Codex`
- state: completed

## Current state

- current_layer: `live_mainline_audit`
- main_chain_status: `telegram_host_vs_subject_evidence_reported`
- completion_class: `verify_passed`

## Completed work

- 锁定审计范围：host-only 分类、ordinary chat 定义、subject ingress / tendency 证明规则
- 确认 dashboard 权威输入来自 `real_telegram/*/ledger.json`
- 确认当前快照中 `host_only = 484` 且不只是少量 control-plane 例外
- 新增 `scripts/codex/audit_telegram_subject_mainline.py`
- 生成 `SUBJECT_MAINLINE_AUDIT_CURRENT.md/.json`
- 冻结当前结论：live Telegram chat 有 subject ingress 证据，但 downstream tendency 只有弱结构信号，没有强证明

## Open risks

- `README.md` 的 Telegram 主链口径与当前代码早退行为存在 wording drift
- live Telegram 可能有 subject ingress，但 downstream tendency 证明仍不足

## Next step

- 如果继续，下一步最小 corrective slice 是修 `unexpected_subject_miss` 与 live chat ingress coverage，而不是扩 `WP17+`

## Last validation results

- mode: `audit closeout`
- result: `pass`
- summary:
  - `python3 -m py_compile scripts/codex/audit_telegram_subject_mainline.py` pass
  - `python3 scripts/codex/audit_telegram_subject_mainline.py` pass
  - `python3 scripts/codex/lint_repo.py` pass
  - `python3 scripts/codex/verify_repo.py --mode fast` pass
  - baseline reproduced:
    - `runs = 1097`
    - `host_only = 484`
    - `oe_available = 580`
    - `control_plane_expected = 206`
    - `policy_driven_host_interception = 228`
    - `unexpected_subject_miss = 50`
    - `telegram_subject_rows = 104`
    - `telegram_subject_revision_gt_0 = 0`
    - `telegram_subject_non_ask_modes = 0`

## Commands run / evidence

- `python3 -m py_compile scripts/codex/audit_telegram_subject_mainline.py`
- `python3 scripts/codex/audit_telegram_subject_mainline.py`
- `python3 scripts/codex/lint_repo.py`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `artifacts/telegram_real_mainline_v1/dashboard_v1/SUBJECT_MAINLINE_AUDIT_CURRENT.md`
- `artifacts/telegram_real_mainline_v1/dashboard_v1/SUBJECT_MAINLINE_AUDIT_CURRENT.json`
