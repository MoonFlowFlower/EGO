## [D-LEGACY-SHIMS] 删除池：旧主链、暗协议、未登记 shim

### 当前层级
- 收口前准备级

### 主链接入状态
- 部分仍可达

### 启用状态
- 部分可能仍启用

### 真实触发证据
- evidence_id: legacy reachable path inventory pending
- source_type: repo inspection
- artifact_path:
  - `EgoCore/app/runtime/interaction_loop.py`
  - `EgoCore/app/handlers/social_chat_handler.py`
  - `EgoCore/app/openemotion_adapter/developmental_writeback.py`
  - prompt/bridge 中的隐式字段约定
- proves:
  - 仓库里仍有旧主链和兼容路径残留
- does_not_prove:
  - 它们今天一定全部仍在真实主链被触发

### 当前确定项
- 删除池不是第一实现轮的执行对象
- 但如果不先列出来，后续会继续形成双主和黑箱

### 关键未知
- 哪些 shim 需要登记后保留，哪些可以在 E3 后直接删除

### 六问门禁
1. 归属是谁：无正式归属，属于历史兼容或应删除对象
2. 权威源是谁：没有；正式权威应迁到新 host chain 或 OpenEmotion
3. 与谁耦合：legacy runtime、social chat、adapter、prompt
4. 是否引入双主：是
5. 是否把 shim 变成黑箱：是，高风险
6. 失败谁兜底：不能再让它们长期兜底

### 判定
- D

### 判定理由
- 它们正是“双主 / 暗协议 / 兼容黑箱”的载体
- 但删除必须晚于新主链证据，不可抢跑

### 本轮最小闭环动作
- 把删除对象显式登记进删除池
- 给每类对象绑定删除前提，不允许“想删就删”

### 完成定义
- D 池条目有明确删除条件
- 第一实现轮不会误删仍承担主链职责的对象

### 若为迁移件
- 替代物：
  - 新 host chain skeleton
  - schema-first adapter
  - interaction-aware router
  - response contract authority
- 迁移目标版本：待第一、二实现轮完成后再执行绞杀
- 删除条件：
  - 新路径已接入主链
  - 已启用
  - 至少 E3
  - 关键入口 E4
  - shim 已登记或已替代
