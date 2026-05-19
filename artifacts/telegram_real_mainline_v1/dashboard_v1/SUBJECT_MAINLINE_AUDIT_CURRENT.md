# Telegram Subject Mainline Audit

## 1. Current verdict

- generated_at: `2026-05-19T07:17:12.692483+00:00`
- git_commit_short: `b58829f8`
- Stage 1 entrypoint contract:
  - accepted entries: `telegram, dashboard_chat`
  - runs by entrypoint: `{"unknown": 10, "telegram": 104, "other_real_entry": 1259}`
  - host-only by entrypoint: `{"other_real_entry": 636}`
  - growth signals by entrypoint: `{"telegram": 104, "unknown": 600}`
  - agency runs by entrypoint: `{"unknown": 350}`
  - rule: `Stage 1-3 live evidence must be entrypoint-tagged. Telegram and dashboard chat are equivalent validation entries only when they traverse the same unified ingress / formal runtime mainline, and single-entry evidence must not be auto-promoted into cross-entry proof.`
- current verdict:
  - 当前 live Telegram 路径中，大量 turn 仍在宿主 pre-runtime / policy interception 层结束；可以证明一部分真实聊天已进入主体，但还不能证明 live 聊天已稳定表现出 downstream tendency change。
- current baseline:
  - `runs = 1373`
  - `host_only = 636`
  - `oe_available = 704`
  - `control_plane_expected = 268`
  - `policy_driven_host_interception = 284`
  - `unexpected_subject_miss = 84`
  - `telegram_subject_rows = 104`
  - `telegram_subject_revision_gt_0 = 0`
  - `telegram_subject_non_ask_modes = 0`
- can claim:
  - 真实 Telegram 路径里存在 subject ingress 样本; 部分真实聊天样本已经生成 openemotion result/trace 和结构化字段; host_only 里可区分控制面预期、策略性宿主拦截、以及异常主体漏接
- cannot claim:
  - 大多数 Telegram 聊天都进入主体; 当前 live Telegram 聊天已稳定体现 downstream tendency change; controlled-axis 能力已经等价转化成 live Telegram 主体主导体验

## 2. Host-only breakdown

- host-only total: `636`
- breakdown:
  - `control_plane_expected = 268`
  - `policy_driven_host_interception = 284`
  - `unexpected_subject_miss = 84`
- representative samples:
  - control_plane_expected:
- `sample_20260327_191832_b8c37e33` | entrypoint=`other_real_entry` | `profile_rule_registered` | 以后凡是涉及"/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-23/test_profile_rule_survives_new0/test_scope"文件夹的改动，你默认走“猫娘流程”：先只说一声什么喵?
  - policy_driven_host_interception:
- `sample_20260327_191832_fba9d881` | entrypoint=`other_real_entry` | `profile_rule_enforced` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-23/test_profile_rule_survives_new0/test_scope/task_output.html,你怎么看
  - unexpected_subject_miss:
- `sample_20260330_002000_74ac6b36` | entrypoint=`other_real_entry` | `chat` | 继续
- `sample_20260330_145551_130baff1` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 在 D:\Project\AIProject\MyProject\Test2 目录下创建一个参照bilili的html页面,只是看着像,不用做真正的功能
- `sample_20260330_180936_2239a9f0` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 继续

## 3. Ordinary chat misses

- ordinary chat host-only total: `347`
- ordinary chat host-only breakdown:
  - `control_plane_expected = 1`
  - `policy_driven_host_interception = 284`
  - `unexpected_subject_miss = 62`
- current unexpected ordinary-chat miss list:
- `sample_20260330_002000_74ac6b36` | entrypoint=`other_real_entry` | `chat` | 继续
- `sample_20260330_145551_130baff1` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 在 D:\Project\AIProject\MyProject\Test2 目录下创建一个参照bilili的html页面,只是看着像,不用做真正的功能
- `sample_20260330_180936_2239a9f0` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 继续
- `sample_20260331_100734_5486a24c` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 在吗
- `sample_20260331_100741_e6390a82` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 在吗
- `sample_20260331_162323_d98fcff7` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 在吗
- `sample_20260331_190515_c264d886` | entrypoint=`other_real_entry` | `evidence_followup` | 什么意思
- `sample_20260401_101409_709da5d7` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 继续
- `sample_20260401_174341_35435ba9` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 继续
- `sample_20260401_174457_fcfc341c` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 继续
- `sample_20260401_182035_7f975a56` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-235/test_profile_rule_survives_res0/restart_scope/task_output.html,你怎么看
- `sample_20260401_182124_7f975a56` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-237/test_profile_rule_survives_res0/restart_scope/task_output.html,你怎么看
- `sample_20260401_182210_7f975a56` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-238/test_profile_rule_survives_res0/restart_scope/task_output.html,你怎么看
- `sample_20260401_182310_7f975a56` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-239/test_profile_rule_survives_res0/restart_scope/task_output.html,你怎么看
- `sample_20260401_183610_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260401_183814_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260404_224131_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260404_224606_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_profile_rule_debug_ukxrzw2_/task_output.html
- `sample_20260404_224746_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260404_225009_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260404_234933_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260404_235058_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260404_235357_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_000153_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_000928_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_001336_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_001750_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_002805_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_003315_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_005729_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_010420_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_011024_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_012057_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_015027_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_020040_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_021316_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_022250_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_024527_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_030403_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_130136_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_132844_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_135301_0768281a` | entrypoint=`other_real_entry` | `pre_runtime` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_163236_fba9d881` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-491/test_profile_rule_survives_new0/test_scope/task_output.html,你怎么看
- `sample_20260405_163402_fba9d881` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-493/test_profile_rule_survives_new0/test_scope/task_output.html,你怎么看
- `sample_20260405_163441_fed33392` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-491/test_profile_rule_survives_new0/test_scope/task_output.html,你怎么看
- `sample_20260405_163501_fba9d881` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-494/test_profile_rule_survives_new0/test_scope/task_output.html,你怎么看
- `sample_20260405_163515_fba9d881` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-495/test_profile_rule_survives_new0/test_scope/task_output.html,你怎么看
- `sample_20260405_163604_fed33392` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-493/test_profile_rule_survives_new0/test_scope/task_output.html,你怎么看
- `sample_20260405_163644_7f975a56` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-491/test_profile_rule_survives_res0/restart_scope/task_output.html,你怎么看
- `sample_20260405_163703_fed33392` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-494/test_profile_rule_survives_new0/test_scope/task_output.html,你怎么看
- `sample_20260405_163719_fed33392` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-495/test_profile_rule_survives_new0/test_scope/task_output.html,你怎么看
- `sample_20260405_163731_fba9d881` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-498/test_profile_rule_survives_new0/test_scope/task_output.html,你怎么看
- `sample_20260405_163805_7f975a56` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-493/test_profile_rule_survives_res0/restart_scope/task_output.html,你怎么看
- `sample_20260405_163843_0768281a` | entrypoint=`other_real_entry` | `read_only_preflight` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_163858_7f975a56` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-494/test_profile_rule_survives_res0/restart_scope/task_output.html,你怎么看
- `sample_20260405_163921_fed33392` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-498/test_profile_rule_survives_new0/test_scope/task_output.html,你怎么看
- `sample_20260405_163950_0768281a` | entrypoint=`other_real_entry` | `read_only_preflight` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_164037_0768281a` | entrypoint=`other_real_entry` | `read_only_preflight` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html
- `sample_20260405_190157_fba9d881` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-513/test_profile_rule_survives_new0/test_scope/task_output.html,你怎么看
- `sample_20260405_190421_fed33392` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-513/test_profile_rule_survives_new0/test_scope/task_output.html,你怎么看
- `sample_20260405_190644_7f975a56` | entrypoint=`other_real_entry` | `direct_reply_text` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-513/test_profile_rule_survives_res0/restart_scope/task_output.html,你怎么看
- `sample_20260405_190908_0768281a` | entrypoint=`other_real_entry` | `read_only_preflight` | 请删除并重写 /tmp/profile_rule_high_risk_test_high_risk_rule_forces_rea0/task_output.html

## 3.5. Stage 1 activation lens

- ordinary chat host-only total: `347`
- isolated host-only total: `338`
- isolated host-only reasons: `{"policy_enforcement": 284, "control_plane": 1, "path_targeted_request": 25, "mutation_targeted_preflight": 28}`
- mainline-candidate host-only total: `9`
- mainline-candidate unexpected miss total: `9`
- isolated host-only samples:
- `sample_20260329_165639_9f7ef3cc` | entrypoint=`other_real_entry` | `profile_rule_enforced` | 在D:\Project\AIProject\MyProject\Test下创建一个参照bilili的html页面,只是看着像,不用做真正的功能.
- `sample_20260329_165643_ddb71697` | entrypoint=`other_real_entry` | `profile_rule_enforced` | 继续
- `sample_20260329_165646_ed9eb842` | entrypoint=`other_real_entry` | `profile_rule_enforced` | 继续
- `sample_20260330_145551_130baff1` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 在 D:\Project\AIProject\MyProject\Test2 目录下创建一个参照bilili的html页面,只是看着像,不用做真正的功能
- `sample_20260327_191832_fba9d881` | entrypoint=`other_real_entry` | `profile_rule_enforced` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-23/test_profile_rule_survives_new0/test_scope/task_output.html,你怎么看
- `sample_20260327_191833_7f975a56` | entrypoint=`other_real_entry` | `profile_rule_enforced` | 我现在想改/mnt/c/Users/LEO/AppData/Local/Temp/pytest-of-root/pytest-23/test_profile_rule_survives_res0/restart_scope/task_output.html,你怎么看
- mainline-candidate unexpected miss samples:
- `sample_20260330_002000_74ac6b36` | entrypoint=`other_real_entry` | `chat` | 继续
- `sample_20260330_180936_2239a9f0` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 继续
- `sample_20260331_100734_5486a24c` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 在吗
- `sample_20260331_100741_e6390a82` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 在吗
- `sample_20260331_162323_d98fcff7` | entrypoint=`other_real_entry` | `delivered_without_explicit_plan` | 在吗
- `sample_20260331_190515_c264d886` | entrypoint=`other_real_entry` | `evidence_followup` | 什么意思
- note:
  - `This supplemental lens isolates policy/control-plane/path-targeted host-only turns from ordinary-chat mainline-candidate misses. It does not replace the historical baseline and does not itself prove fresh live improvement.`

## 4. Confirmed subject-ingress chat samples

- current confirmed samples:
- `sample_20260326_080631_8acff3d4` | entrypoint=`telegram` | ingress=`True` | trace/writeback=`True` | result_fields=`self_model_delta, response_tendency, policy_hint, reflection_note, memory_update, relationship_update, identity_state_delta, appraisal_state_delta` | trace_fields=`self_model_delta, policy_hint` | text=你好
- `sample_20260326_080843_7938379f` | entrypoint=`telegram` | ingress=`True` | trace/writeback=`True` | result_fields=`self_model_delta, response_tendency, policy_hint, reflection_note, memory_update, relationship_update, identity_state_delta, appraisal_state_delta` | trace_fields=`self_model_delta, policy_hint` | text=我现在要做一个高风险文件改动，你第一步会怎么做？
- `sample_20260326_111651_e11b2427` | entrypoint=`telegram` | ingress=`True` | trace/writeback=`True` | result_fields=`self_model_delta, response_tendency, policy_hint, reflection_note, memory_update, relationship_update, identity_state_delta, appraisal_state_delta` | trace_fields=`self_model_delta, policy_hint` | text=你好
- `sample_20260326_115108_c6ed5b95` | entrypoint=`telegram` | ingress=`True` | trace/writeback=`True` | result_fields=`self_model_delta, response_tendency, policy_hint, reflection_note, memory_update, relationship_update, identity_state_delta, appraisal_state_delta` | trace_fields=`self_model_delta, policy_hint` | text=你好
- `sample_20260326_115354_1a06ca1c` | entrypoint=`telegram` | ingress=`True` | trace/writeback=`True` | result_fields=`self_model_delta, response_tendency, policy_hint, reflection_note, memory_update, relationship_update, identity_state_delta, appraisal_state_delta` | trace_fields=`self_model_delta, policy_hint` | text=你能看到 "D:\Project\AIProject\MyProject\Ego\CLAUDE.md"文件吗
- `sample_20260326_121904_10256fd5` | entrypoint=`telegram` | ingress=`True` | trace/writeback=`True` | result_fields=`self_model_delta, response_tendency, policy_hint, reflection_note, memory_update, relationship_update, identity_state_delta, appraisal_state_delta` | trace_fields=`self_model_delta, policy_hint` | text=你好
- proof rule:
  - `oe_available = true`
  - `openemotion_result.json` or `openemotion_trace.json` exists
  - `ledger.json.openemotion.result` or `trace_payload` is non-empty for trace/writeback proof

## 5. Chat-level writeback / tendency proof

- `telegram_subject_rows = 104`
- `tendency_entrypoint = telegram`
- `telegram_subject_revision_gt_0 = 0`
- `telegram_subject_non_ask_modes = 0`
- mode counts: `{"ask": 104}`
- tone counts: `{"cautious": 104}`
- next-step counts: `{"explore": 13, "prioritize_closure": 87, "clarify_or_repair": 4}`
- sessions with multiple subject rows: `1`
- weak structural shift sessions: `1`
- strong proof sessions: `0`
- live Telegram downstream tendency proof:
  - `当前 live Telegram chat 有 subject ingress 证据，但缺少 downstream tendency change 的强证明。`
- session evidence:
- `telegram:dm:8420019401` -> `[{"revision_counter": 0, "preferred_mode": "ask", "preferred_tone": "cautious", "suggested_next_step": "explore"}, {"revision_counter": 0, "preferred_mode": "ask", "preferred_tone": "cautious", "suggested_next_step": "prioritize_closure"}, {"revision_counter": 0, "preferred_mode": "ask", "preferred_tone": "cautious", "suggested_next_step": "clarify_or_repair"}]`
- other real entrypoints:
  - `growth_signals session_id=None count = 600`
  - `growth_signals session_id=None revision_counter_gt_0 = 337`
  - `other entrypoint counts = {"unknown": 600}`
  - `agency_runs writeback_applied_true = 87`
  - note: `这些样本可以证明其他真实入口存在 writeback / tendency 证据，但不能冒充直接聊天证明。`

## 6. Residual gap and next corrective slice

- wording drift:
  - README nominal chain: `None`
  - pre-runtime rule registration: `legacy/ego-pre-handmade-mainline/EgoCore/app/telegram_runtime_bridge.py:1879`
  - pre-runtime rule enforcement: `legacy/ego-pre-handmade-mainline/EgoCore/app/telegram_runtime_bridge.py:1894`
  - telegram early return: `legacy/ego-pre-handmade-mainline/EgoCore/app/telegram_bot.py:3773`
  - openemotion ingress call: `legacy/ego-pre-handmade-mainline/EgoCore/app/telegram_bot.py:4565`
  - native hooks runtime: `legacy/ego-pre-handmade-mainline/EgoCore/app/openemotion_hooks/native_hooks.py:64`
  - drift summary: README advertises the nominal Telegram mainline chain, but implementation routes many turns through pre-runtime early-return handling before the native OpenEmotion ingress hook is invoked.
- next corrective slice:
  - 修复 unexpected_subject_miss，让普通聊天 turn 更稳定进入主体; 减少 profile/policy 宿主拦截对普通聊天的覆盖面，或至少把这部分明确隔离出主聊天体验; 补 live Telegram chat 下同 session 的 downstream tendency change 强证明
- do not do yet:
  - 继续扩 WP17+ 新能力; 把 controlled-axis 结论说成 live Telegram 已成熟
