# CONTINUITY_OBSERVATION_LEDGER

## new
- status: `direct_real`
- sample_ids: `sample_20260327_172843_9dd30fcf`, `sample_20260327_181702_f2b07aa4`, `sample_20260327_181836_c62ec4ab`, `sample_20260327_192917_0fb99fcd`, `sample_20260327_193011_ba85afe6`, `sample_20260327_193036_85bb0b22`, `sample_20260327_193908_691109dd`, `sample_20260327_193950_5b0f3ace`, `sample_20260327_181726_a0a60957`, `sample_20260327_181746_3f0a0750`, `sample_20260327_181809_0b24c5a6`, `sample_20260327_181902_1981805c`, `sample_20260327_192938_6895514d`, `sample_20260327_193003_4f89937d`, `sample_20260327_193014_7167c17b`, `sample_20260327_193039_11781ed8`
- external_evidence_refs: 无
- what_it_proves: 多次 `/new` 直接真实样本、完整 continuity probe、显式默认规则在 `/new` 后继续命中。
- what_it_does_not_prove: 不证明 `restore continuity`、E5 稳定成立、Developmental Self 准入通过。
- blocker: `/new` 已成立；当前 continuity 主 blocker 已切到 `restore` 与 evidence gap。

## restart
- status: `cross_evidence`
- sample_ids: `sample_20260327_193954_7ab41a5b`, `sample_20260327_194005_25c165d3`, `sample_20260326_122012_a1eb9987`, `sample_20260326_130620_fa6a1303`, `sample_20260326_134949_b14ecef8`, `sample_20260326_135004_de5a2b74`, `sample_20260326_140841_7fd57d3e`, `sample_20260326_141603_c295f138`, `sample_20260326_141641_68a5a243`, `sample_20260326_142359_945ae501`, `sample_20260326_143224_1406bcb4`, `sample_20260326_143303_9df6b133`, `sample_20260326_143624_eb57644d`, `sample_20260326_143641_05b02d55`, `sample_20260326_143708_8a6c95fe`, `sample_20260326_154600_e34d5fbc`, `sample_20260326_154804_12ed4c28`, `sample_20260326_180956_097602f5`, `sample_20260326_181045_4e639441`, `sample_20260326_181325_7177ff8e`, `sample_20260326_184809_ab5a513f`, `sample_20260326_204952_a1ad48c9`, `sample_20260326_222703_9e2bb07b`, `sample_20260326_223755_238449d4`, `sample_20260326_223842_b8d9e1f2`, `sample_20260327_192938_6895514d`, `sample_20260327_193003_4f89937d`, `sample_20260327_193014_7167c17b`, `sample_20260327_193039_11781ed8`, `sample_20260327_193918_e117da7e`
- external_evidence_refs: ``scripts/restart_egocore.sh --telegram` 输出（`2026-03-27 19:39:39 CST -> 19:39:48 CST`, `PID 2586 -> 2657`）+ `sample_20260327_194005_25c165d3`：`restart continuity` 跨证据链正证据；重启后 `A3` 再次命中 `profile_rule_b811ed8829dcdc68``
- what_it_proves: 真实重启日志与 post-restart 命中样本已形成跨证据链正证据。
- what_it_does_not_prove: 仍不等于 post-restart 命中样本已成为完整单样本 E4 bundle。
- blocker: post-restart 命中样本仍非完整单样本 E4 bundle。

## restore
- status: `missing`
- sample_ids: 无
- external_evidence_refs: 无
- what_it_proves: 当前没有直接真实 `restore` 样本。
- what_it_does_not_prove: 不能证明 `restore continuity` 已成立。
- blocker: `restore` 仍是 continuity 的最高优先级缺口。
