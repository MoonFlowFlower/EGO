# Simulated Shadow H1 Mainline Sampling - EXPLORE

## E00

- Question:
  - 为什么 frozen prompts 只产出 task-conflict / idle-overwrite，而不是目标样本？
- Why this framing:
  - 先排除 harness 污染，再谈 H1 telemetry
- Experiment:
  - disable autonomy orchestration in the simulated runner; reset active task context between rows
- Observed result:
  - intended prompt paths恢复；task-conflict 不再主导样本
- What it proves:
  - host run orchestration 不是当前 simulated slice 的 authority path
- What it does not prove:
  - canonical H1 telemetry 已经可见
- What path is ruled out:
  - “继续调 pending_task_conflict 就能解决全部问题”
- Decision for next step:
  - 检查 openemotion bundle 是否仍被 finalized/idle 覆盖

## E01

- Question:
  - bundle capture 为什么一直看到 idle/finalized，而不是 external-result？
- Why this framing:
  - H1 telemetry 只在 external-result 拍上有因果价值
- Experiment:
  - freeze simulated bundle on external-result stage; skip finalized/idle capture in this harness
- Observed result:
  - `openemotion_result.event_id` 进入 `..._tool_0`
- What it proves:
  - bundle capture fidelity 可以在 runner-local 层面收口
- What it does not prove:
  - H1 telemetry 在 canonical path 一定存在
- What path is ruled out:
  - “缺失只是 evidence collector 读错最后一拍”
- Decision for next step:
  - 对比 plain vs seed subject profile

## E02

- Question:
  - `shadow_h1` 缺失是 canonical 主线问题，还是 subject-profile 问题？
- Why this framing:
  - isolated debug 已表明 plain external-result path 能产生 H1
- Experiment:
  - compare `build_external_result_event -> adapter.handle_event` under `plain` vs `seed_v0_2`
  - clear `proto_self_subject_profile_override` from the simulated session snapshot
- Observed result:
  - `plain` path emits `shadow_h1`
  - `seed_v0_2` suppresses `shadow_h1`
  - simulated non-seed bundle now shows H1 on positive rows
- What it proves:
  - current simulated harness is usable
  - subject-profile suppression is a separate problem
- What it does not prove:
  - real Telegram / E4
  - runtime efficacy
  - negative control discipline
- What path is ruled out:
  - “canonical H1 patch is dead on the formal mainline”
- Decision for next step:
  - close this task as conditional_complete; open a narrow follow-up on negative-control `shadow_h1`

## E03

- Question:
  - negative control 为什么会产出 non-guarding `shadow_h1`？
- Why this framing:
  - 当前样本和 scorer 都已稳定，剩下的 failure 来自 canonical observable-path gating
- Experiment:
  - inspect `perceived` for the negative-control row
  - patch `build_shadow_h1_summary()` to emit only on eligible `tool_result` paths
  - add a direct negative-control regression test in `test_h1_shadow_canonical.py`
- Observed result:
  - negative-control `user_message` no longer emits `shadow_h1`
  - positive rows `S1/S2/S4` keep their expected telemetry
  - simulated report closes with `failure_count = 0` and `decision = simulated_sample_observation_ready`
- What it proves:
  - the remaining failure was a real canonical gating bug, not just a report artifact
- What it does not prove:
  - real Telegram / E4
  - runtime efficacy
  - `seed_v0_2` compatibility
- What path is ruled out:
  - “negative-control leak lives only in host report logic”
- Decision for next step:
  - close this slice and, if needed, open a new narrow task for `seed_v0_2` suppression

## E04

- Question:
  - 为什么 `seed_v0_2` external-result path 会压掉 `shadow_h1`，以及能否在不改变 live decision surfaces 的前提下修复？
- Why this framing:
  - negative control 已修完，剩下唯一明确的 canonical gap 就是 seed profile compatibility
- Experiment:
  - direct repro 比较 plain vs `seed_v0_2` external-result path
  - patch `seed_kernel._perceive()` 补齐 `runtime_summary / h1_shadow_active / action_class_seed`
  - patch v2 seed path 在 `exec_result` 上复用 canonical `build_shadow_h1_summary()`
  - let H1 observable-path accept seed `exec_result` tool feedback
- Observed result:
  - pre-patch: seed path `perceived` 里没有 `h1_shadow_active / action_class_seed`，`trace_payload.shadow_h1 = None`
  - post-patch: 在同一份 preloaded eligible shadow state 下，plain 与 `seed_v0_2` 都暴露相同 `shadow_h1`
  - non-tool seed paths 仍不发 `shadow_h1`
- What it proves:
  - `seed_v0_2` suppression 是 canonical seed-path glue 缺失，不是 report artifact
  - seed profile 现在可以暴露已有的 canonical H1 telemetry，而不碰 live policy / response
- What it does not prove:
  - real Telegram / E4
  - runtime efficacy
  - seed path 会稳定生成 H1 backing shadow state
- What path is ruled out:
  - “seed profile 与 H1 telemetry 结构性不兼容”
- Decision for next step:
  - close this task as conditional_complete; if needed, open a narrower follow-up on seed-path H1 backing-state generation
