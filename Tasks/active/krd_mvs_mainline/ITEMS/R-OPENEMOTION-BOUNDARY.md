## [R-OE-BOUNDARY] OpenEmotion 边界回迁与 schema-first adapter

### 当前层级
- 策略级 / 实现级

### 主链接入状态
- 已接入候选

### 启用状态
- 已启用候选

### 真实触发证据
- evidence_id: proto-self real runtime + adapter traces
- source_type: targeted repo tests + direct_real trace consumption
- artifact_path:
  - `OpenEmotion/openemotion/contracts/event_v1.py`
  - `OpenEmotion/openemotion/contracts/result_v1.py`
  - `OpenEmotion/openemotion/proto_self/kernel.py`
  - `EgoCore/app/openemotion_adapter/event_builder.py`
  - `EgoCore/app/openemotion_adapter/result_consumer.py`
  - `EgoCore/app/openemotion_adapter/proto_self_adapter.py`
  - `EgoCore/app/openemotion_adapter/proto_self_restore.py`
  - `EgoCore/app/openemotion_adapter/proto_self_trace_bridge.py`
- proves:
  - 双核已经通过结构化 event/result 在主链上通信
  - OE 输出与 EgoCore 消费都已接入
- does_not_prove:
  - `event_v1` authority 归属已完全冻结到 EgoCore
  - adapter 中不存在主体语义漂移或宿主偷做本体更新

### 当前确定项
- `result_v1` 已在 OpenEmotion contracts 下，适合作为继续保留的主体输出 authority
- `event_v1` 仍需按迁移计划明确为 EgoCore 输入 authority、OE 侧 mirror
- `developmental_writeback.py` 这类宿主内主体语义残留必须进入删除池

### 关键未知
- `event_v1` authority 的 repo-tracked 文件应落在 EgoCore 哪个稳定路径，才能不新增第三真相源

### 六问门禁
1. 归属是谁：event 输入归 EgoCore；result/self-state/主体语义归 OpenEmotion
2. 权威源是谁：`event_v1`=EgoCore；`result_v1`=OpenEmotion
3. 与谁耦合：adapter、proto_self kernel、runtime_v2
4. 是否引入双主：当前有风险，必须通过 schema-first 收口
5. 是否把 shim 变成黑箱：如果 mirror/compat 不登记，就会变黑箱
6. 失败谁兜底：EgoCore adapter guard + contract tests

### 判定
- R

### 判定理由
- 这是双仓边界的最小正式收口点
- 不重收口 contract authority，后面任何目录调整都会继续漂

### 本轮最小闭环动作
- 冻结 authority 口径：
  - `event_v1` = EgoCore authority, OpenEmotion mirror
  - `result_v1` = OpenEmotion authority, EgoCore consume/mirror
- 不在本轮直接搬文件，只先把迁移矩阵和删除池写死

### 完成定义
- 第一实现轮开始前，不再存在“event/result 谁说了算”的模糊地带
- adapter 中哪些保留、哪些回迁、哪些进入 D 池已经可直接执行

### 若为迁移件
- 替代物：
  - `openemotion_adapter.schemas.event_v1`
  - `openemotion_adapter.from_kernel_output`
  - `openemotion_adapter.restore_injector`
  - `openemotion_adapter.trace_bridge`
- 迁移目标版本：schema-first adapter v1
- 删除条件：
  - contract test 通过
  - adapter regression 通过
  - 新 event/result authority 拿到 E3/E4

