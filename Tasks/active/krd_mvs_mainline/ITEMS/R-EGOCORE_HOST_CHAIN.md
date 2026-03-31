## [R-EGOCORE-HOST] EgoCore 宿主主链壳

### 当前层级
- 策略级 / 表示级 / 实现级交界

### 主链接入状态
- 已接入候选

### 启用状态
- 部分启用

### 真实触发证据
- evidence_id: recent Telegram runtime_v2 real samples
- source_type: direct_real
- artifact_path:
  - `EgoCore/app/telegram_bot.py`
  - `EgoCore/app/telegram_runtime_bridge.py`
  - `EgoCore/app/runtime_v2/semantic_parser.py`
  - `EgoCore/app/runtime_v2/loop.py`
  - `EgoCore/app/runtime_v2/state.py`
  - `EgoCore/app/runtime_v2/tool_broker.py`
  - `EgoCore/app/response/verbalizer.py`
  - `EgoCore/app/response/verbalizer_v3.py`
- proves:
  - 宿主已能真实驱动 Telegram 主链、run/item、tool delivery
  - response_plan / delivery / blocked / final 已有 E4 正证据
- does_not_prove:
  - interaction control-plane 已有单一 authority
  - response contract 已从 renderer 中完全剥离

### 当前确定项
- interaction 分流仍散落在 Telegram ingress、semantic parser、runtime bridge 中
- response plan、memory claim、renderer 目前仍有权责混用
- session/task runtime 仍有继续拆层空间

### 关键未知
- 第一实现轮最小 host-chain skeleton 应该落在哪 2 到 3 个文件，能最便宜地产生 E3

### 六问门禁
1. 归属是谁：EgoCore
2. 权威源是谁：宿主 control plane / response contract / runtime state
3. 与谁耦合：Telegram ingress、runtime_v2、response verbalizer、tools
4. 是否引入双主：当前存在风险
5. 是否把 shim 变成黑箱：当前存在 risk，如果不显式抽层会继续扩大
6. 失败谁兜底：宿主 blocked / delivery / verify gate

### 判定
- R

### 判定理由
- 同类问题已经多轮出现过：交付断链、状态混用、回复 authority 漂移
- 它承担的是宿主主链壳，不应继续靠零散 bridge 和 verbalizer 隐式持有 authority

### 本轮最小闭环动作
- 第一实现轮只做：
  - `InteractionKind`
  - 最小 `ResponsePlan`
  - 最小 `MemoryClaimVerdict`
- 不顺手拆全 runtime

### 完成定义
- `chat/task/admin/ask/wait/resume` 有唯一 authority
- final / ask / blocked / resume 的宿主回复骨架不再由 verbalizer 自由决定
- “我记得你/已恢复”类声明能被 gate 拦住或放行

### 若为迁移件
- 替代物：
  - `interaction.classify_interaction`
  - `response_contract.response_plan`
  - `response_contract.memory_claim_gate`
- 迁移目标版本：MVS host-chain skeleton v1
- 删除条件：
  - 新 skeleton 达到 E3
  - Telegram 关键路径拿到 E4
  - 旧 generic fallback 不再主导

