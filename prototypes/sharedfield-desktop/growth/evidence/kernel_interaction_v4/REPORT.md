# v4：走近与拾取通过，组合条件被误拒绝

2026-10-04，run1791150754064223000。14项相关离线检查通过，58份文件冻结后运行8次固定DeepSeek V4.1 Flash/Wafer调用，34.5秒，费用0.001114548美元。原正式库与源码一致，无MC连接。

S0正确阻止旧库存条件假完成；S1建立独立near_owner目标并走近/核对；S2实际选择entity41并按pickup_events+库存核对8原木，没有找树或采树。

S3模型正确为“先走近再拾取”生成near_owner与picked_up两个完成条件。程序却要求pickup目标只能有picked_up，连续拒绝合理组合，未执行approach，场景前置条件未达到。S4–S6未执行。结论COMPOSITE_CONTRACT_FAIL / NO_LIVE_INSTALL；问题在程序条件校验，不能归因于模型不会规划。

下一修订允许pickup与near_owner/inventory_clear联合，仍必须有picked_up、仍不允许gained替代。隔离身体拾取需像实际导航一样更新自身位置。保留原判据阈值和旧失败，再冻结。
