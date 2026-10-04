# v2 预验收候选：旧存档反例保留

2026-10-04。78项Python回归、47项拾取Node检查及库存/空间/搜索/树木回归通过；最后的按需检索修改另通过12项针对性检查。56份源和场景已冻结，但尚未调用收费模型，也未接入Minecraft。

接正式存档前补做旧任务兼容检查：旧“捡8个原木”任务仍为gained(oak_log,8)，当前库存10。脚本化resume在现有候选下直接inspect后宣称completed，没有拾取来源证据。原始结果保留于runs/kernel_interaction_v2/legacy_defect_before.json。这是实际Harness缺陷复现，0云模型调用、0游戏动作。

结论LEGACY_CONTRACT_FAIL / MODEL_ACCEPTANCE_NOT_STARTED / NO_LIVE_INSTALL。冻结源码在本候选本地提交保留。下一修订需在resume/steer入口检查旧完成条件是否符合本次任务类别；不把既有库存差值迁移成领取证据。原A1–A7和M1–M4判据不变，新增该反例后另冻结，不覆盖本记录。
