# 可复算的样例，而不是用户默认人格或记忆

`adaptive_sample.json` 由当前源码执行真实状态转移产生，但语言输出与反馈标签是明确的 TEST_FIXTURE。它验证目标/草稿/反馈/学习/恢复链，不验证真实语言能力。

```text
python run.py studio-verify examples/adaptive_sample.json
python run.py studio-import examples/adaptive_sample.json --data-dir example_session
python run.py studio --data-dir example_session
```

启动时暂停，不会自动请求模型。继续自动语言步骤需自行配置真实模型或使用手动交换。新实验不加载这个样例。

固定候选、不同反馈历史的样例位于 `evidence_v03/current/benchmark/causal_compare.json` 和 `causal_direct.json`。同样使用 `studio-verify` 复算。

`legacy_v02/studio_sample.json` 必须通过 `studio-migrate-v02` 或原始v0.2包读取。不能直接交给新版控制器。原始完整程序在 compatibility/original_v02.zip，仅供明确的旧版本验证和回滚；它不是当前默认执行器。
