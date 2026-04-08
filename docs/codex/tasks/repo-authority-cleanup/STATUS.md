# Repo Authority Cleanup - STATUS

## Current milestone

- name: Milestone 1 - Phase 0 Truth Map + Identity Baseline + Self-Model Wave
- owner: Codex
- state: completed

## Current state

- current_layer: repo_authority_cleanup
- main_chain_status: phase0_truth_map_landed_identity_baseline_confirmed_self_model_authority_wave_landed
- completion_class: conditional_complete

## Completed work

- 已创建 long-run task package：`docs/codex/tasks/repo-authority-cleanup/`
- 已确认当前 formal mainline 不变：`native_hooks -> proto_self_runtime -> proto_self_adapter -> proto_self_v2/kernel`
- 已确认 `identity` 代码级单一 authority baseline 已存在，可直接作为本轮基线复核
- 已确认 `self-model` formal owner 当前在主链上被 runtime projection/writeback 消费
- 已确认 `emotiond/self_model_adapter.py`、`emotiond/self_model_mirror.py`、`proto_self_restore.py` 当前 formal caller 为 0，但仍存在 tools/docs/generated caller
- 已完成 Phase 0 六个 ledger 首版落地：`AUTHORITY_MATRIX / CALLER_MATRIX / FILE_FATE_LEDGER / CANONICAL_DOCS_INDEX / ARTIFACT_LOG_INVENTORY / CONFLICT_REGISTER`
- 已完成 `self-model` 代码级 authority 收口：formal owner 自证、legacy adapter/mirror 自降级、single-authority static regression 落地

## Last validation results

- mode: milestone-1 scoped verification
- result: passed
- summary:
  - `python3 -m py_compile OpenEmotion/openemotion/self_model/model.py OpenEmotion/openemotion/self_model/__init__.py OpenEmotion/emotiond/self_model_adapter.py OpenEmotion/emotiond/self_model_mirror.py OpenEmotion/tests/test_self_model_single_authority.py scripts/codex/verify_proto_self_single_authority.py`
  - `cmd.exe /c "OpenEmotion\\.venv\\Scripts\\python.exe -m pytest OpenEmotion\\tests\\test_identity_single_authority.py OpenEmotion\\tests\\test_self_model_single_authority.py OpenEmotion\\openemotion\\proto_self_v2\\tests\\test_self_model_read_integration.py -q"` -> `12 passed`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_v2_proto_self_runtime.py -k "self_model or identity" -q -s` -> `8 passed`
  - `python3 scripts/codex/verify_proto_self_single_authority.py` -> passed
  - `python3 scripts/codex/lint_repo.py` -> passed
  - `python3 scripts/codex/verify_repo.py --mode fast` -> passed
  - scoped `git diff --check` -> passed

## Decisions made

- 第一轮 milestone 固定为 `Phase 0 + identity baseline closeout + self-model authority wave`
- `identity` 本轮不重复设计，只做 ledger/doc/gate 对齐
- `self-model` 本轮采取最小代码收口：formal owner 自证 + legacy adapter/mirror 自降级 + no-dual-authority static assertion
- `drives / reflection / developmental` 第一轮只进 ledger 与 conflict register，不进语义改造
- `self-model` 本轮后的唯一 authority 固定为 `openemotion.self_model/*`；`openemotion.proto_self.self_model` 仅保留 active compute/proposal substrate 角色
- `emotiond/self_model_adapter.py` 固定为 `compatibility_only`，`emotiond/self_model_mirror.py` 固定为 `reference_only`

## Open risks

- worktree 脏文件很多，提交必须极度 scoped
- `proto_self_restore` 因 `__init__.py` re-export 与历史 docs/generated caller，当前只能进 delete-admission ledger，不能直接删
- `self-model` dual-authority 已收口，但 legacy adapter/mirror 仍有 tool/docs caller，当前还不能删
- artifacts/logs 只做 inventory，不做物理迁移或删除；archive 边界仍待后续波次明确

## Next step

- 进入下一波：`drives / reflection / developmental` 只做 caller/authority ledger 收口，不做语义改造；同时继续推进 `proto_self_restore / self_model_adapter / self_model_mirror` 的 delete-admission 证明

## Commands run / evidence

- `sed -n '1,220p' PROJECT_MEMORY.md`
- `sed -n '1,220p' docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `sed -n '1,220p' docs/CODEX_CLOSED_LOOP_SELF_REVIEW_WORKFLOW.md`
- `sed -n '1,240p' README.md`
- `sed -n '1,240p' EgoCore/README.md`
- `sed -n '1,240p' OpenEmotion/README.md`
- `sed -n '1,220p' docs/codex/README.md`
- `python3 scripts/codex/new_task.py repo-authority-cleanup --title "Repo Authority Cleanup"`
- `sed -n '1,260p' docs/PROTO_SELF_SINGLE_AUTHORITY_DECISION.md`
- `sed -n '1,260p' docs/PROTO_SELF_MVP_AUTHORITY_AUDIT.md`
- `sed -n '1,260p' EgoCore/docs/05_DEPRECATED_AND_SHIMS.md`
- `find docs -maxdepth 2 -type f`
- `find artifacts -maxdepth 2`
- `find OpenEmotion/artifacts -maxdepth 2`
- `find EgoCore/artifacts -maxdepth 2`
- targeted `rg` on `self_model_adapter / self_model_mirror / proto_self_restore / identity_invariants / developmental_core`
