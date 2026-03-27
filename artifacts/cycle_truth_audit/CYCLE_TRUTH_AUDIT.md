# CYCLE_TRUTH_AUDIT

## 审计范围说明

本次审计刻意区分两条链：

- `OpenEmotion/openemotion/cycle_core/` + `emotiond /cycle`：旧的 Cycle Core HTTP 链
- `OpenEmotion/openemotion/proto_self/` + `EgoCore/app/openemotion_adapter/proto_self_adapter.py`：当前 Proto-Self 主体核链

任务单要求同时看 Proto-Self / cycle 相关实现与 EgoCore 消费方式，因此本报告的正式判定以 **当前被 EgoCore 主动消费的 Proto-Self 链** 为主；旧 `/cycle` 链只作为历史/兼容参照，不拿来冒充当前 Proto-Self 结论。

---

## 当前层级

**结论：当前实现属于“带真实后果回流的 stateful biasing memory”，不是 closure / invariant prototype。**

更具体地说：

- `proto_self` 这条链已经有真实的 `external_result -> reflection -> state persistence`
- 但 `cycle_id` 仍然主要由输入桶 `psi_bucket` 决定
- `cycle` 本身还不是 event-action-outcome closure 的不变量
- 宿主对 `policy_hint / response_tendency` 的消费，仍以提示偏置为主，不是直接结构化动作裁决

**审计结论：B. 接近 stateful biasing memory**

---

## 主链接入状态

- 总仓 README 声明 Telegram 正式宿主主链已切到 native chain，但 OpenEmotion hooks 仍复用 `RuntimeV2ProtoSelfRuntime`
- `EgoCore/app/openemotion_hooks/native_hooks.py` 直接复用 `RuntimeV2ProtoSelfRuntime`
- `EgoCore/app/runtime_v2/loop.py` 仍保留完整 `proto_self` ingress / external_result 接线
- `OpenEmotion/emotiond/api.py` 里的 `/cycle` 端点仍指向旧 `openemotion.cycle_core.kernel.CycleCoreKernel`

因此当前仓内其实同时存在：

- **当前 Proto-Self 主体核链**
- **旧 `/cycle` HTTP 链**

本次分类结论针对前者。

---

## 启用状态

- `OpenEmotion/openemotion/proto_self/` 已实现并可直接调用
- `EgoCore/app/openemotion_adapter/proto_self_adapter.py` 已接入状态加载、镜像写入、trace bridge
- `EgoCore/app/runtime_v2/proto_self_runtime.py` 已把 ingress 和 tool `external_result` 回流接入 Proto-Self
- `EgoCore/app/openemotion_hooks/native_hooks.py` 已把 native Telegram 链入口复用到同一 Proto-Self runtime

**判定**：代码已启用，且不是纯设计稿。

---

## 真实触发证据

- 根仓 README 明确宣称 Proto-Self Kernel v1 已形成主链基础接线，并给出真实 Telegram 口径
- `EgoCore/artifacts/proto_self_v1/ACCEPTANCE_REPORT_CYCLE_STRENGTHEN_20260324.md` 给出真实 Telegram E2E 样本
- `EgoCore/logs/proto_self_trace.jsonl` 中可见真实 `tool_result` / `reflection_trigger=external_failure`
- `EgoCore/artifacts/proto_self_store/agent_global/proto_self_state.v1.json` 可见跨轮保留的 `self_model / drives / cycle_store / episodic_trace`
- `EgoCore/artifacts/proto_self_store/agent_global/manifest.json` 明确宿主角色是 `mirror_cache`，权威源仍指向 `openemotion.proto_self`

---

## 当前确定项

1. `external_result` 确实进入 `KernelEvent`，并被 `appraisal.py` 识别为 `external_outcome_type`
2. failure 会触发 `reflection_note`，并把 `self_model.current_mode` 写成 `repair`
3. `ProtoSelfState` 会通过 `ProtoSelfStateStore` 落到宿主镜像，跨轮保留
4. `cycle_store` 确实会跨轮累积 `hits / strength / promoted`
5. `decision_engine` 把 `policy_hint / response_tendency / reflection_note` 转成文本段落注入 system prompt
6. `contract_runtime` 也只把 `policy_hint` 变成字符串约束，而不是直接 action routing

---

## 关键未知

1. 当前生产主链里是否还有未审到的直接结构化消费点，会按 `policy_hint / response_tendency` 直接分支动作
2. 未来是否打算把旧 `/cycle` HTTP 链完全退役，避免“Cycle”一词同时指两套实现
3. 目前 `cycle_store` 虽持久化，但其内容是否计划进入后续真正的长期记忆本体，还没有在这条链里实现

---

## Q1. 当前 cycle 形成依赖闭环，还是只依赖重复模式？

**结论：当前 cycle 主要依赖重复模式，不依赖闭环。**

代码证据：

- `OpenEmotion/openemotion/proto_self/cycles.py`
  - `cycle_id = _stable_hash(psi_bucket)`
  - `psi_bucket` 只来自 `intent / event_type / source / risk_level`
  - `phi_signature` 被记录但不参与 `cycle_id`
- strengthen 条件只有 “这个 `cycle_id` 是否已存在”
- promotion 条件只有 `strength > 0.5 and hits > 3`
- `external_result` 进入的是 `appraisal / reflection / self_model`，不是 `cycle_id`

新增反证测试：

- `OpenEmotion/openemotion/proto_self/tests/test_cycle_truth_audit.py::test_cycle_identity_does_not_encode_outcome_closure`
  - 在相同 `tool_result` bucket、相同 risk bucket 下，`success` 与 `failure` 命中同一 `cycle_id`
  - 这直接反证了“outcome 已进入 cycle identity”

**判定**：当前 `cycle` 不是 closure identity，而是 bucketed repetition memory。

---

## Q2. 当前实现是否具备顺序不变性的证据？

**结论：未证明；就当前实现看，可判为未实现 closure-level order invariance。**

代码证据：

- `OpenEmotion/openemotion/proto_self/trace_types.py` 只记录单轮 `cycle_delta`
- 当前 trace 中没有 `closure_id`、`path_signature`、`order_invariance` 一类字段
- `cycles.py` 的固化单位是“单事件 psi bucket”，不是多步 closure

新增反证测试：

- `OpenEmotion/openemotion/proto_self/tests/test_cycle_truth_audit.py::test_reordered_paths_have_no_closure_level_order_invariance_mechanism`
  - 两条重排路径最终只留下逐事件 bucket
  - 当前状态里只有 3 个逐事件 signature，没有任何 closure-level invariant 对象

**判定**：没有足够证据证明顺序不变性；应按“未实现”处理，不能报已具备。

---

## Q3. memory 的持久性到底由什么承载？

### 1. `episodic_trace`

- 在 `ProtoSelfState` 内部保存最近事件与 `external_result`
- 通过 `ProtoSelfStateStore` 一起落盘
- 属于短中程轨迹，不是独立长期记忆本体

### 2. `cycle_store`

- 也是 `ProtoSelfState` 的一部分
- 宿主镜像落盘后会跨轮保留 `cycle_id / hits / strength / promoted`
- 但当前还没有看到它被直接用于下一轮动作路由

### 3. `reflection promotion`

- 当前只存在 `memory_update.promote_reflection` 这个 hint
- 这是“建议可晋升”，不是已经落入独立长期 memory ontology

### 4. host-side mirror / restore

- 真正跨轮持久化介质在 `EgoCore/app/openemotion_adapter/proto_self_state_store.py`
- `agent_global/proto_self_state.v1.json` 是当前主宿主镜像
- `artifacts/proto_self_mirror/state.json` 是 compatibility-only mirror

### 5. runtime prompt bias

- `EgoCore/app/runtime_v2/decision_engine.py` 把输出转成文本提示
- `EgoCore/app/agent_core/contract_runtime.py` 把 `policy_hint` 变成字符串 `Honor policy_hint: ...`

**必须回答的问题**

- 真正跨轮保留的是哪一层：
  - `ProtoSelfState` 内的 `self_model / drives / cycle_store / episodic_trace`
  - 宿主介质是 `ProtoSelfStateStore agent_global mirror`
- 真正影响下一轮决策的是哪一层：
  - 直接可见的是 `policy_hint / response_tendency`
  - 但宿主消费方式主要是 prompt / contract 文本偏置，不是硬结构 action routing

---

## Q4. Proto-Self 输出是结构化控制，还是 LLM 提示偏置？

**结论：生产者侧是结构化输出，消费者侧主要是提示偏置。**

代码证据：

- 生产者：
  - `KernelOutput` 明确定义了 `policy_hint / response_tendency / reflection_note`
- 宿主消费：
  - `EgoCore/app/runtime_v2/decision_engine.py` 用 `build_policy_hint_context()` 把字段翻译成中文提示文本，再拼进 system prompt
  - `EgoCore/app/agent_core/contract_runtime.py` 只把 `policy_hint` 追加成 `hard_constraints` 里的字符串
  - 没看到 audited path 里存在 `if policy_hint == ... then route tool ...` 这类直接动作分支

**判定**：

- 不是纯文本生成，因为边界上输出是结构化对象
- 但也不是强结构控制，因为宿主当前主要把这些结构再翻译回提示文本

所以它更接近：**结构化生产 + 提示偏置消费**

---

## Q5. 当前实现更接近论文哪一层？

**三选一结论：B. 接近 stateful biasing memory**

理由：

- 不是 A：
  - `cycle_id` 不编码 closure
  - promotion 不看 outcome consistency
  - 没有 closure-level order invariance 证据
- 比 C 更强：
  - 有真实 `external_result` 回流
  - failure 会写入 `repair` 模式和 `revision_counter`
  - `ProtoSelfState` 会跨轮持久化
- 但仍未到 A：
  - `cycle` 对行为的直接因果作用太弱
  - 宿主消费仍以 prompt bias 为主

---

## 审计结论

**最终分类：B. 带真实后果回流的 stateful biasing memory**

补充口径：

- 如果只看 `cycle` 本身，它更像“bucketed repetition weighting”
- 但如果看整条 `proto_self` 链，它已经具备真实后果回流和持久状态，因此整体上应判 B，而不是降到纯 C

---

## 最小证据链

1. `README.md`：当前总仓宣称 Proto-Self 已接线并有真实 Telegram 证据
2. `OpenEmotion/openemotion/proto_self/cycles.py`：`cycle_id` 只由 `psi_bucket` 生成
3. `OpenEmotion/openemotion/proto_self/appraisal.py`：`external_result` 只进入 `external_outcome_type`
4. `OpenEmotion/openemotion/proto_self/reflection.py`：failure 触发 `external_failure`
5. `EgoCore/app/openemotion_adapter/proto_self_state_store.py`：ProtoSelfState 跨轮持久化
6. `EgoCore/app/runtime_v2/decision_engine.py`：`policy_hint` 被转成 prompt 文本
7. `EgoCore/app/agent_core/contract_runtime.py`：`policy_hint` 被转成字符串约束
8. `EgoCore/logs/proto_self_trace.jsonl`：真实 `tool_result` / `reflection_trigger` 证据
9. `OpenEmotion/openemotion/proto_self/tests/test_cycle_truth_audit.py`：四个最小反证

---

## 哪个前提一旦为假，结论就要改写

只要下面任一项被证伪，本报告的 B 结论就应重写：

1. 实际生产消费者并非主要做 prompt bias，而是直接用 `policy_hint / response_tendency` 做动作裁决
2. 当前线上 `cycle_id` 已经在别处编码了 action/outcome closure，而不仅仅是 `psi_bucket`
3. 已存在 closure-level trace / replay / order-invariance 机制，只是本次审计遗漏

---

## 下一步唯一最高优先级动作

**把 cycle identity 从“输入桶命中”升级为“closure-sensitive signature”，并补一条 closure-level trace 字段与 order-invariance 测试链。**

如果这一步不做，`cycle` 永远不能从“有状态偏置系统”升级到“closure / invariant prototype”。
