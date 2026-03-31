## [K-FOUNDATION] 科学仪器层 / 真相链 / 治理壳

### 当前层级
- 收口级 / 观察级

### 主链接入状态
- 已接入真实主链

### 启用状态
- 已启用

### 真实触发证据
- evidence_id: real Telegram E4 bundles / dashboard / replay artifacts
- source_type: direct_real + replay artifacts
- artifact_path:
  - `EgoCore/artifacts/`
  - `EgoCore/data/session_logs/`
  - `EgoCore/app/telegram_evidence_collector.py`
  - `scripts/run_telegram_real_channel_capture.py`
- proves:
  - 宿主可记录 response_plan / outbox / raw update / runtime result / timeline
  - replay / audit / dashboard 已进入主链
- does_not_prove:
  - 不证明业务语义本身一定正确

### 当前确定项
- 这批模块是判定“重构是否真的变好”的真相链
- 当前任务单明确要求它们优先进 K 池

### 关键未知
- 哪些历史脚本已不再被主链调用，需要后续从 K 池细分成 K 或 D

### 六问门禁
1. 归属是谁：EgoCore
2. 权威源是谁：宿主 evidence / audit / replay / dashboard
3. 与谁耦合：Telegram 主链、runtime_v2、dashboard
4. 是否引入双主：否
5. 是否把 shim 变成黑箱：否
6. 失败谁兜底：没有兜底，失败就降完成口径

### 判定
- K

### 判定理由
- 它们不抢主体解释权
- 它们是后续 D 池绞杀的判真依据
- 重写收益明显低于保留收益

### 本轮最小闭环动作
- 保留
- 在总表与迁移矩阵中明确标记为不可随业务清理一起删除

### 完成定义
- 这些模块被主链任务显式纳入 K 池
- 后续实现任务不再把它们当“顺手清理对象”

### 若为迁移件
- 替代物：无
- 迁移目标版本：沿用现有主链
- 删除条件：无；仅允许局部路径整理，不允许职责删除

