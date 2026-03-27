# CYCLE_GAP_MATRIX

| 维度 | 状态 | 证据 | 审计判断 |
|---|---|---|---|
| `external_result` 回流 | 已实现 | `KernelEvent.external_result`、`appraisal.py`、`reflection.py`、`RuntimeV2ProtoSelfRuntime.process_external_result()` | failure/success 确实进入主体核 |
| cycle 闭环依赖 | 未实现 | `cycle_id = stable_hash(psi_bucket)`；T1 证明 success/failure 可命中同一 cycle | cycle identity 仍主要看输入桶 |
| order invariance | 未实现 | `trace_types.py` 无 closure/order 字段；T2 明确只有逐事件 bucket | 不能声称已证明顺序不变性 |
| replay sufficiency | 已实现 | `trace_payload` 包含 `perceived/appraisal_delta/cycle_delta/policy_hint`；`test_kernel_replay.py` 通过 | 单轮 trace replay 口径成立 |
| anti-drift | 部分实现 | trace-driven replay 和 deterministic test 在；但 cycle identity 仍弱，closure-level anti-drift 不在 | 对单轮输出有约束，对闭环本体不足 |
| persistent memory ontology | 部分实现 | `ProtoSelfState` + `ProtoSelfStateStore` 持久化在；`promote_reflection` 仍只是 hint | 持久状态存在，但长期记忆本体未完全独立化 |
| direct behavioral causality | 部分实现 | failure 会改下一轮 `preferred_mode=repair`；但宿主消费主要是 prompt/contract 文本 | 有因果，但还是偏“软控制” |

---

## 说明

### 为什么 `external_result` 是“已实现”

- 回流已经进入正式 `KernelEvent`
- failure 会触发 `external_failure`
- 真实 trace 和 acceptance report 都能看到它

### 为什么 cycle 闭环依赖是“未实现”

- 当前 `cycle_id` 不编码 `action/outcome`
- promotion 只看 `hits/strength`
- outcome 更多影响的是 `reflection / self_model / policy_hint`

### 为什么 direct behavioral causality 不是“未实现”

- 因为 failure 的确会跨轮改变 `self_model.current_mode`
- 新增 T3 证明后续 tendency 会从 `respond` 变成 `repair`
- 但它还不是“结构化动作裁决”，所以只能算部分实现

### 为什么 persistent memory ontology 不是“已实现”

- `cycle_store` 与 `episodic_trace` 会持久化
- 但 `reflection promotion` 仍只是 hint
- `cycle_store` 也还没有成为真正的 closure memory ontology
