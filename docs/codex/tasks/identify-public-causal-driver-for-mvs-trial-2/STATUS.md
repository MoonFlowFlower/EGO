# Trial-2 Public-Driver-First Spec - STATUS

## Current milestone

- name: `M4: Decision`
- owner: `Codex`
- state: completed
- type: decision

## Current state

- current_layer: `trial2_closed_h1_identified`
- main_chain_status: `bounded_e3_only`
- completion_class: `closed`
- candidate_vs_proof: `proof_passed`

## Milestone outcomes

- `M0 Problem Freeze`
  - result: `continue`
  - output:
    - bounded objective frozen
    - stop conditions frozen
    - candidate set frozen to `H1/H2/H3`
- `M1 Candidate Public-Driver Ranking`
  - result: `continue`
  - output:
    - ranking = `H1 > H2 > H3`
    - current hard set only pre-activates H1
- `M2 Minimal Discriminative Experiment Design`
  - result: `continue`
  - output:
    - split-sever experiment frozen
    - scorer ontology unchanged
    - hard set unchanged
- `M3 Minimal Implementation + Rerun`
  - result: `continue`
  - output:
    - `trial2_ablation_correction_public_path_sever`
    - `trial2_ablation_viability_public_path_sever`
    - Trial-2 decision evaluator
    - initial helper wiring bug found and fixed
    - fixed rerun/scoring completed
- `M4 Decision`
  - result: `close`
  - output:
    - `H1 counterfactual low-success guard` identified as the **current bounded active public driver**

## Completed work

- Trial-2 全部在现有 hard set + 现有 scorer 下完成
- repo-level state 未升级
- challenger 未评分
- replay suite 未扩
- scorer ontology 未改

## Last experiment

- question:
  - 在修复 split-ablation wiring 后，当前 bounded setup 是否能识别唯一 active public driver
- framing:
  - `frozen scorer + frozen hard set + split-sever rerun`
- result:
  - `trial1_ablation_counterfactual_public_path_sever`
    - `mean_weighted_gap = 0.05`
    - `positive_gap_case_count = 8`
  - `trial2_ablation_correction_public_path_sever`
    - `mean_weighted_gap = 0.0`
    - `positive_gap_case_count = 0`
  - `trial2_ablation_viability_public_path_sever`
    - `mean_weighted_gap = 0.0`
    - `positive_gap_case_count = 0`
  - pre-registered decision rule satisfied for H1
- evidence_upgraded: no

## What was learned

- 当前 hard set/scorer 下，真正驱动 public gap 的是：
  - `H1 counterfactual low-success guard`
- `H2 correction-pressure public guard` 与 `H3 viability-pressure public guard`
  - 当前在这个 bounded setup 上都不是 active public drivers
- split-sever 初版失败的主要原因不是任务 underdefined，而是 helper wiring bug

## What was ruled out

- 把 `reflection loop` 升成第 4 条候选
- 通过改 scorer 或扩 hard set 来“帮助”任务得出结论
- 把 `H1` 写成通用 causal core

## Claim ceiling

- allowed:
  - `Under the existing scorer and hard set, H1 counterfactual low-success guard is the current bounded active public driver.`
- disallowed:
  - `H1 is the universal MVS causal core`
  - `MVS is live in runtime`
  - `repo-level state should be upgraded`

## Last validation results

- mode: `slice-closeout`
- result: `conditional_pass`
- summary:
  - `git diff --check` scoped slice = pass
  - `verify_repo --mode fast` = pass
  - `verify_repo --mode full` 启动后已暴露与 Trial-2 无直接因果关系的全仓历史失败：
    - `tests/test_dashboard_server.py::*flow_detail*`
    - `tests/test_native_loop.py::test_native_loop_runs_tool_call_and_returns_reply`
    - `tests/test_developmental_writeback.py::test_real_telegram_mainline_turn_writes_developmental_projection`
    - `tests/test_doc_system_inventory_builder.py::test_doc_system_inventory_builder_generates_key_outputs`
  - 因此本任务口径维持为：
    - `Trial-2 slice complete`
    - 不是 `repo full gate clean`

## Decisions made

- Trial-2 closes here
- close reason:
  - bounded objective achieved under frozen decision rule
- H2/H3 status:
  - demoted as active-driver explanations for this bounded setup

## Open risks

- 这个结论只适用于当前 hard set + 当前 scorer
- 当前只有 `E3 controlled-integration` 级口径
- 还不能说明 runtime、生效、或跨 replay-corpus 稳定性

## Next step

- Trial-2 内无后续动作
- 若继续，只能新开任务测试：
  - H1 是否跨 replay corpus 保持
  - H1 是否在更接近 runtime 的 replay slice 仍成立

## Commands run / evidence

- `python3 -m py_compile OpenEmotion/openemotion/proto_self/trial1_shadow.py OpenEmotion/openemotion/proto_self/tests/test_trial1_shadow_contract.py EgoCore/tests/test_trial1_shadow_replay_minimal.py scripts/codex/score_trial1_shadow_replay.py scripts/codex/evaluate_trial2_public_driver_hypotheses.py`
- `PYTHONPATH=OpenEmotion python3 -m pytest OpenEmotion/openemotion/proto_self/tests/test_trial1_shadow_contract.py -q`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_trial1_shadow_replay_minimal.py -q`
- `python3 scripts/codex/run_trial1_hard_set_rerun.py --output-json artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_CURRENT.json --output-md artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_CURRENT.md --variants trial1_baseline_proto_self_mainline trial1_candidate_mvs_aligned_compact trial1_ablation_counterfactual_public_path_sever trial2_ablation_correction_public_path_sever trial2_ablation_viability_public_path_sever`
- `python3 scripts/codex/score_trial1_shadow_replay.py --input artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_CURRENT.json --output-json artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_SCORED_CURRENT.json --output-md artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_SCORED_CURRENT.md --causal-md artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_CAUSAL_TABLE_CURRENT.md --positive-buckets counterfactual_isolation restart_restore_boundary_cases --negative-control-buckets negative_controls --stability-buckets`
- `python3 scripts/codex/evaluate_trial2_public_driver_hypotheses.py --input artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_RERUN_SCORED_CURRENT.json --output-json artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_DECISION_CURRENT.json --output-md artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_DECISION_CURRENT.md`
- `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_DECISION_CURRENT.json`
- `git diff --check -- docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2 OpenEmotion/openemotion/proto_self/trial1_shadow.py OpenEmotion/openemotion/proto_self/tests/test_trial1_shadow_contract.py EgoCore/tests/test_trial1_shadow_replay_minimal.py scripts/codex/score_trial1_shadow_replay.py scripts/codex/evaluate_trial2_public_driver_hypotheses.py artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_*`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `python3 scripts/codex/verify_repo.py --mode full`
