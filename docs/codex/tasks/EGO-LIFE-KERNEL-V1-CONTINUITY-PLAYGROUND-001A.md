# EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A

## 0. Draft status and authority boundary

```yaml
task_id: EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A
status: DRAFT_ONLY__IMPLEMENTATION_UNAUTHORIZED
execution_requested: false
implementation_authorized: false
authorized_implementation_targets: []
current_stage: visible_life_proxy_v0_product_core_authority_synced__v1_card_draft_only
current_layer: layer_2_engineering_product_capability_design
mainline_target: none__ego_runtime_mainline_forbidden
enabled_state: false
default_enabled: false
runtime_mainline_connected: false
runtime_authority: none
science_weight: 0
auto_remote_anchor: forbidden
```

本文件只完成 V1 implementation card 的设计草案。它不授权编码、实验、
runtime/mainline 接线、EgoOperator/EgoDesktop 修改、science successor、push、
tag 或 remote anchor。完成本草案后必须停止，等待 operator 单独授权 V1
implementation。

### 0.1 Pinned start state

- Ego: `main @ b852cedb1c1a31531a2f71e330e110539150c518`
- ITL: `codex/meta-theory-scaffold @ 619bff5fd9400bba00002af26f65ce73894a9dce`
- Route revision: `EGO_VISIBLE_LIFE_PROXY_V0_CORE_ADOPTION_001A`
- Route fingerprint:
  `2446c65920f96a9a49d9ae654a0f106e8fb0bcaf41e023d4405c46c083a0f005`
- Immutable V0 Git-object baseline:
  `Ego@546e3639299d7b11b599df3d00645666a6953bac`
- V0 parent/tree:
  `d5d98ac0783a7e67b6d003b460470bdf4350d4bd` /
  `fe79061dca2991c822cf2b0b5547a08d9b4682f9`

这些 pin 必须在未来 implementation 的 Mandatory Step 0 重新读取；本文件中的
值不能代替 live Git readback。

### 0.2 Conditional action resolution

ITL committed route state 保留 conditional action：

```text
draft_EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A_only_after_EGO_sync_validation
```

ITL transition card 明确规定：V1 card 只能在 callable cross-repo Ego sync
validation 后起草；V1 implementation 另需 operator-authorized card。Ego commit
`b852ced...` 消费 sync action，当前 callable program-state integrity、route
convergence、mainline clarity 与 V0 Git-object/SQLite validator 均已通过。因此本次
只消费 conditional **draft** action；不修改 ITL route objects，也不把 ITL 的
pre-consumption state 改写为新的 route authority。

任一 pin 或 callable sync validation 失败时，本草案不得继续进入 implementation。

### 0.3 Current allowed actions — verbatim

```text
draft_EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A_only_after_EGO_sync_validation
run_route_state_machine_validation
```

### 0.4 Current forbidden actions — verbatim

```text
reuse_implement_EGO-VISIBLE-LIFE-PROXY-V0-001A
create_parallel_visible_life_product_core
implement_EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A
modify_EgoDesktop_or_EgoOperator
add_LLM_or_network_integration
enable_runtime_or_runtime_mainline
grant_runtime_authority
register_or_satisfy_science_successor
claim_mechanism_learning_agency_or_electronic_life
repair_reopen_or_rerun_closed_card2_action
push_tag_or_remote_anchor
```

## 1. Problem definition

真实目标不是增加一个更像宠物的 renderer，而是把 V0 的离散按钮反应变成一个
可玩的、默认关闭、用户显式启动的连续产品闭环：

```text
logical product clock
-> continuous episode lifecycle
-> persistent causal state
-> explicit current goal
-> memory-conditioned candidate comparison
-> prediction / actual / error / update
-> atomic persistence
-> recomputed timeline and restart
```

V0 已有单一 `compute_step`、原子 SQLite command+trace commit、从 serialized
initial state + ordered commands 的重算、deficit goal proposals、tabular EMA、
episodic/consolidated memory bias 和 latest-step 可视化。当前缺口是：

1. `episode_id` 固定在 run metadata 中，没有真实 episode lifecycle；
2. goal 每 tick 重排后只写 trace，没有持久、可延续的 `current_goal`；
3. UI 只显示最新 trace，没有由 replay frames 构成的可检查 timeline；
4. 没有默认 paused 的 `Step / Run / Pause` product clock；
5. 没有统一且语义明确的 `Freeze Updates`；
6. `provenance_ids` 当前不参与 retrieval semantics，直接 shuffle 只会是 cosmetic；
7. banked V0 trigger 只有 5 commands / 1 fixed episode，所有 selected model refs
   都是 `hardcoded_prior`，selected memory bias/refs 都为 `0 / []`，没有执行覆盖
   cross-episode retention、learned-table read、natural memory influence 或
   consolidation。

## 2. First-principles bounded audit

- **Real objective:** 建立一个由同一 causal reducer 驱动、跨 episode 保留状态、
  可暂停/继续、可重启重算、用户能观察和塑形的本地 product loop。
- **Strongest baseline explanation:** deterministic deficit/FSM controller +
  cue/current-state/clock lookup + tabular EMA + keyed memory table + SQLite +
  timeline renderer 足以解释全部可见行为。
- **Strongest invalidating reason:** episode 标签、goal 文本和 timeline 可能只是
  renderer 装饰；history 可能没有因果进入 action comparison。
- **Framing falsifier:** clock scheduler 绕过 Controller/store；goal 不进入 score；
  memory refs 不进入 score；timeline 读取 stored selected action 作为行为输入；
  episode rollover 重置 persistent state；或 interventions 只改 report 字段。
- **Still insufficient evidence:** 连续动画、多 episode persistence、memory score
  差异、prediction error 下降、exact replay、用户觉得“更有生命感”或全部 tests
  通过，都不足以支持 mechanism、learning-generalization、initiative、agency、
  emotion understanding、subjectivity 或 consciousness claim。
- **What this tests:** product engineering continuity and causal wiring only；不是
  mechanism non-equivalence test，也不是 science Gate。
- **Hard-coding audit:** V0 outcome table、deficit scorer、goal rule、memory weights、
  EMA 与 deterministic tie 都必须公开；不得用 episode tick、cue name、fixture name、
  filenames 或 hidden labels 编码预期 action。
- **Local-optimum / Zeno audit:** 本卡不再修补 route/schema governance；若 product
  设计需要新的 route repair、第二 core 或第二 replay path，STOP 而不是扩卡。
- **Evidence-leakage audit:** commands 禁止包含 selected action、candidate score、
  actual delta、prediction error 或 future state；scanner 必须有正控。
- **Claim-inflation audit:** callable shortcut baseline 即使不能完全 match，也不得
  升级 claim；equal-access history/lookup baselines 的既有负证据继续封顶。

### 2.1 Relevant prior negative evidence

- `Ego/docs/RESEARCH_NEGATIVE_RESULTS_CROSSWALK_001A.md` 记录 equal-access
  identifiability ceiling、memory/graph-cache pressure 与 provenance/write-protection
  风险。
- `ITL/artifacts/SAME-AGENT-MINIMAL-KERNEL-BRIDGE-001A/result.json` 记录 candidate
  `1.0` 与 `drift_aware_regime_inferring_continual_replay` `1.0` 的
  `BASELINE_EQUIVALENCE`。
- `ITL/artifacts/gate1_replay_consolidation_exec_taskcard_001/result.json` 记录
  graph-cache family collapse。
- V0 自身在 `engine.py` 顶部披露它是 hard-coded toy outcome table + deficit scorer
  + tabular EMA + structured memory bias，而不是 mechanism evidence。

这些负证据不否定产品价值，但否定由本卡产出 mechanism headroom 或 science
success 的解释。

### 2.2 Hypothesis

**Bounded engineering hypothesis:** 如果同一个 V0-descendant canonical reducer 真正
接收 Tk product-clock commands，并把 persisted current goal、跨 episode memory read、
prediction/error/update 与 logical episode rollover 写入一个原子 command/trace chain，
那么冻结的 24-tick UI run 应同时产生：(a) 两次可重算 episode boundary；(b) 未完成
goal 的 boundary carry；(c) 至少一个 natural cross-episode nonzero memory read/score
effect；(d) fresh-process identical state/timeline；以及 (e) 三项 paired intervention 的
字段级预期差异。

**Falsifier:** 任一结果只能由 renderer/stored trace 生成、goal/history 不进入 score、
fresh-process 不能从 initial state + commands 重算、或 paired interventions 不改变其
声明的 read/write/hash path，即否定本 engineering hypothesis。即使 hypothesis survives，
也不支持 mechanism non-equivalence、general learning、initiative 或 subjectivity。

## 3. Collision record

### Candidate A — minimal UI/field patch（拒绝）

- **Approach:** 在 V0 外层加 episode counter、goal label、Tk timer 和 stored-trace
  timeline。
- **Evidence:** UI 连续、编号递增、历史可见。
- **Cheap match:** 一个 renderer wrapper 可完全复制。
- **Leakage/hard-coding risk:** goal 只是 label；timeline 直接信任 stored trace；
  episode tick 暗含固定 schedule。
- **Smallest falsifier:** 删除 current-goal display 后 score/action 不变，或 tamper
  stored trace 后 timeline 仍显示为真。
- **Expected failure:** `continuity_theater`。

### Candidate B — strongest shortcut baseline（保留为 claim ceiling）

- **Approach:** 独立 cue/current-organism-bucket/episode-tick FSM+lookup controller，
  只从 pre-decision serialized state + typed observation 独立计算 action；另设一个明确
  分离的 stored-trace echo appearance control 来展示 renderer shortcut。
- **Evidence:** 可匹配连续动画、restart、prediction/error panel 和 deterministic
  history appearance。
- **Cheap match:** 它本身就是最便宜的 equal-access shortcut。
- **Leakage/hard-coding risk:** cue-to-action mapping、episode tick schedule、goal/action
  names 和 trace echo 可伪造 continuity。
- **Smallest falsifier:** 固定 state/cue 后替换合法 history/provenance，若输出与 read
  set 都不变，则 history 不是因果输入；删除/tamper stored action 后不能从 commands
  重算则 baseline 失败。
- **Expected failure:** FSM baseline 可能解释 action；trace-echo control 能通过 appearance，
  但不能通过 causal replay/tamper boundary。

### Candidate C — one-reducer continuity descendant（选择）

- **Approach:** 在同一个 `ego_life_playground_v0` lineage 内原位演进；一个 canonical
  reducer 同时服务 live tick、restart replay、timeline frame reconstruction 和
  intervention recomputation。
- **Evidence:** product-clock trigger、跨 episode state carry、persistent current goal、
  memory score contribution、prediction/update timeline、fresh-process recomputation。
- **Cheap match:** V0 式 deficit/lookup/EMA/memory-table baseline 仍可解释行为。
- **Leakage/hard-coding risk:** toy heuristic 和 keyed retrieval 仍可能覆盖全部效果。
- **Smallest falsifier:** 任一 live/replay/timeline/intervention path 未调用同一 reducer。
- **Expected failure:** 可能成为更连贯的 toy product，但仍没有 mechanism/science
  headroom。

**Selection:** Candidate C。Candidate B 永久保留为 claim-ceiling explanation；本卡
不尝试把它修补成“输给 candidate”的 pass 形状。

## 4. Current layer, lane and mainline boundary

- **Card drafting:** Layer 2 — engineering/product design only。
- **Future implementation if separately authorized:** Layer 2 product capability with a
  bounded Layer-4 tabular update surface；只可描述 toy distribution 内的 observed
  update，不得称 general learning。
- **Lane:** product/capability lane，不是 ITL science/evidence lane。
- **Ego runtime mainline:** `none / forbidden`。
- **Product entrypoint:** 仅显式执行
  `python scripts/run_ego_life_playground_v0.py`。
- **EgoOperator:** sole active default，保持不变。

## 5. Enabled-state requirement

Repository route 始终保持：

```text
enabled=false
default_enabled=false
runtime_mainline_connected=false
runtime_authority=none
science_weight=0
```

Tk app 启动后也必须默认 `paused`。只有用户显式按 `Step` 或 `Run` 才能产生 tick；
`Pause` 后不得再写 command/state；关闭窗口后不得留下 thread、subprocess、service 或
scheduled background behavior。

## 6. V0 baseline inheritance contract

Future implementation must be a declared descendant of
`Ego@546e3639299d7b11b599df3d00645666a6953bac` and edit the existing six-file
lineage in place。禁止创建 `labs/ego_life_playground_v1/`、第二 launcher 或第二 core。

下列 V0 constants 不得为了 V1 acceptance 调参：

- action set、cue set、organism keys；
- V0 toy outcome priors / cue bonuses；
- target level、EMA alpha、consolidation threshold；
- action costs、memory-bias coefficients、deterministic tie rule。

新增 goal contribution 的 coefficient 固定为 `1.0`；既有 total-deficit contribution
也固定为 `1.0`。任何需要看结果后改变这些值才能获得 action flip 或漂亮 timeline 的
情况都触发 STOP。

### 6.1 V0 database boundary

`engine.py` / `store.py` byte changes will intentionally change the code-path hash。V1 使用
新的 default DB namespace（`EgoLifePlaygroundV1/continuity.sqlite3`）；不得静默迁移、
覆盖或重写 V0 `EgoLifePlaygroundV0/playground.sqlite3`。旧 V0 DB 在 V1 code hash
下 fail closed 是允许且预期的边界。任何 migration 必须另起卡。

## 7. Product-clock contract

### 7.1 Logical clock

- Tk 提供 `Step / Run / Pause`。
- `Run` 只使用 Tk `after`；禁止 thread、subprocess、network。
- `Step` 与每个 scheduled tick 调用同一个 Controller dispatch。
- 用户选择当前 cue；每个 tick 把 cue 写入 typed command。
- wall-clock interval 只控制展示速度，不进入 causal state/hash。
- canonical clock 只有：`global_tick`、`episode_index`、`episode_tick`。
- `episode_span_ticks=8` 在 run metadata 创建时冻结，不可事后调参。
- tick 8 之后的 rollover 由同一个 reducer 完成，不得新增 episode transition writer。

### 7.2 Canonical causal state v1

```yaml
schema_version: ego.life_playground.state.v1
clock:
  global_tick: int
  episode_index: int
  episode_id: deterministic_string
  episode_tick: int
organism:
  energy: float
  safety: float
  connection: float
  stimulation: float
current_goal:
  state_variable: string_or_null
  target: float
  selected_global_tick: int
  entry_deficit: float
  status: active_or_homeostasis
  selection_reason: initial_max_deficit_or_previous_goal_completed_or_no_active_deficit_or_deficit_reappeared
model: context_action_tabular_ema
memory:
  episodic: list
  consolidated: list
last_action: string_or_null
last_command_hash: string_or_null
last_trace_hash: string_or_null
```

`running/paused` 是 UI safety state，不持久化；restart 永远 paused。

#### 7.2.1 Non-cyclic hash and provenance order

以下 hash 定义与计算顺序冻结，禁止实现时另造等价但不同的 provenance path：

```text
command_hash = sha256(canonical_json(command without command_hash))
causal_state_hash = sha256(canonical_json(state without top-level last_trace_hash))
trace_hash = sha256(canonical_json(trace without trace_hash))

1. validate command and command_hash against the previous committed state
2. compute decision state, selected action, outcome and next causal state
3. set next_state.last_command_hash, but retain the previous last_trace_hash
4. compute state_after_hash from that causal next state
5. build trace with prev_trace_hash and all causal fields
6. compute trace_hash
7. only then assign next_state.last_trace_hash = trace_hash
```

Canonical memory provenance 保存 `source_command_hash`，不得在当前 tick 的 memory
record 中保存尚未存在的 `source_trace_hash`，否则形成
`trace -> state/memory -> trace` 自引用。Report 可以在 fresh recomputation 后按
`source_command_hash` join 出 `resolved_source_trace_hash`；该字段仅用于报告，既不写回
causal memory，也不进入 scoring/hash。

#### 7.2.2 Exact typed-command and intervention schema

V1 command 的 top-level keys 必须精确为：

```yaml
schema_version: ego.life_playground.command.v1
sequence: int
cue: resource_or_contact_or_novelty_or_threat_or_quiet
trigger_source: ui_step_button_or_ui_run_button_or_headless_acceptance_or_paired_intervention
interventions:
  memory_mode: canonical_or_off
  update_mode: enabled_or_frozen
  provenance_mode: canonical_or_shuffle_projection
prev_command_hash: sha256_or_null
command_hash: sha256
```

- `sequence == previous_state.clock.global_tick + 1`；previous hash 必须 exact match。
- missing/extra key、unknown enum 或 `memory_mode=off` 与
  `provenance_mode=shuffle_projection` 的组合一律 fail closed。
- `trigger_source` 只记录真实入口，不得进入 score、tie-break、outcome 或 update。
- 三项 paired rerun 分别只改变：
  - Memory OFF：`canonical/enabled/canonical -> off/enabled/canonical`；
  - Freeze Updates：`canonical/enabled/canonical -> canonical/frozen/canonical`；
  - Shuffle Provenance：
    `canonical/enabled/canonical -> canonical/enabled/shuffle_projection`。
- Pair report 必须记录
  `checkpoint_id=causal_state_hash(serialized_checkpoint)` 与
  `observation_id=hash(command projection excluding interventions and command_hash)`；同一
  pair 除 interventions/command_hash 外不得有差异。

Episode assignment and rollover are exact：

```text
initial state: global_tick=0, episode_index=0, episode_tick=0
action tick t: episode_index=floor((t-1)/8), episode_tick=((t-1) mod 8)+1
rollover: at the start of ticks 9, 17, 25, ... before action computation
```

因此 frozen 24-tick run 恰好发生 ticks 9/17 两次 boundary，action-bearing episode
indices 恰好是 `[0,1,2]`；tick 24 后仍为 episode 2 / episode_tick 8，直到 tick 25
才 rollover 到 index 3。

Rollover 只更新 episode counters/id。Trace 必须保留 `episode_before`、
`episode_transition`、`action_episode`，并比较 **previous committed state** 与
**post-rollover/pre-action state** 的 organism、model、memory、未完成 current_goal、
command/trace-chain bytes；不得拿 post-action state 做 carry comparison。

### 7.3 Current-goal rule

1. Initial goal = maximum **positive** deficit，tie 使用既有 state-key order。
2. Goal 在达到既有 `TARGET_LEVEL` 前保持，不得每 tick 抖动重选。
3. Goal completed 后才选择新的 maximum positive deficit。
4. 若所有 deficits 都为 `0`，persist
   `current_goal={state_variable:null,status:homeostasis,selection_reason:no_active_deficit}`；
   context 使用 `cue|homeostasis`，`current_goal_deficit_reduction=0.0`。
5. Homeostasis 状态下若 action 后重新出现 positive deficit，next state 按既有 tie
   order 选择 maximum positive deficit，reason=`deficit_reappeared`。
6. Episode boundary 不自动更换 goal，也不得把 homeostasis 伪装成 active goal。
7. Candidate context 必须使用 persisted `current_goal`；goal 不是 renderer label。
8. Trace 必须记录 `goal_before`、`goal_progress`、`goal_transition`、`goal_after`；
   completed-to-homeostasis 和 homeostasis-to-active 都是显式 transition。

Frozen score:

```text
total_score =
    current_goal_deficit_reduction
  + total_deficit_reduction
  + memory_bias
  + untried_bonus
  - action_cost
  + deterministic_tie
```

这仍是公开 toy heuristic，不是内部动机或主观 goal 证据。

## 8. State / memory / action / update data flow

```text
Tk Step/Run widget event
-> Controller.dispatch(trigger_source, cue, intervention modes)
-> typed command schema/hash/sequence validation
-> last committed causal state
-> derive next global tick and apply optional episode rollover
-> decision state = post-rollover / pre-action causal state
-> carry or transition persisted current_goal
-> context = cue | current_goal
-> canonical or counterfactual memory read-view
-> all V0 action candidates
-> prediction from tabular EMA, else pinned V0 prior
-> goal gain + total deficit gain + memory bias + cost comparison
-> selected action
-> actual outcome from unchanged V0 toy table
-> organism delta
-> prediction error
-> conditional model/memory update
-> next state + command/trace hashes
-> atomic SQLite command+trace commit
-> only after commit: Controller state swap
-> redraw current state, goal, candidates, update and replay timeline
```

Renderer、timeline、headless acceptance 和 recovery 都不得自行选择 action 或计算第二份
state transition。

## 9. Strongest shortcut baseline contract

Future evidence producer must contain an **independent callable**
`run_cue_clock_fsm_baseline` outside the live engine/controller path。它只可访问
**pre-decision** serialized state、typed observation/cue、episode clock 和公开 V0
constants；它必须独立计算 candidate scores/action，不得调用 candidate reducer，不得
读取 candidate trace、stored selected action、actual outcome、post-action state、future
fields 或 hidden expected verdict。

另设 `run_stored_trace_echo_control` 作为 post-hoc **appearance/leakage control**。它可读
stored trace 并证明 UI appearance 容易被 echo，但它不属于 baseline score，不得进入
candidate-vs-baseline non-equivalence calculation。

`baseline_comparison.json` 记录：

- 两个 producer functions 及各自 code hash，并明确 `baseline` 与
  `post_hoc_appearance_control` role；
- exact input artifacts/run/seed/episode IDs；
- pre-decision FSM baseline 的 selected-action/state-transition match rate；
- trace-echo control 的 visible-row match rate；
- 两者在 deletion/tamper 后是否还能由 initial state + commands 重算；
- aggregation rule；
- verdict ceiling `SHORTCUT_BASELINE_REMAINS_PLAUSIBLE_OR_STRONGER_CEILING`。

本 product card 不要求 candidate beat baseline，也不允许 baseline difference 产生
mechanism non-equivalence claim。若 shortcut 完全匹配 appearance，保存为负证据；若不
匹配，也只说明这个 baseline 在该 fixture 上不等价。

## 10. Required interventions

三项 evidence 必须从同一个 serialized checkpoint + 同一个 observation command 重跑
canonical reducer；禁止比较手写 scores 或静态 verdict。

### 10.1 Memory OFF

- read set = `[]`；所有 candidate `memory_bias=0` / `memory_refs=[]`；
- 不写 episodic/consolidated memory；memory bytes pre/post 相同；
- model update 仍可发生，除非同时 Freeze Updates；
- trace reason = `memory_disabled`；
- paired canonical run 必须至少有一个非空 canonical read set 和非零 score delta。

不强制 natural run 每次都 action flip，以避免调参；但继承的 focused test 必须继续证明
一份合法 serialized memory 能经真实 score path 改变 action selection。

### 10.2 Freeze Updates

UI 文案必须是 **Freeze model + memory updates**：

- model/memory 仍可读取并影响 candidates；
- organism、clock、episode、goal 仍演进；
- model bytes 和 memory bytes pre/post 完全相同；
- 无 episodic/consolidated write；
- trace 分别记录 `model_update.applied=false`、
  `memory_update.applied=false`、reason=`adaptive_updates_frozen`。

### 10.3 Shuffle Provenance

为了避免 cosmetic toggle，语义冻结为 read-only counterfactual projection：

1. 不修改 canonical persisted memory；
2. 按 stable lineage key
   `(source_episode_id,source_command_hash,source_sequence,slot)` 建立 deterministic
   eligible set；opaque `memory_id` 不得进入 eligibility/order/seed/scoring；
3. retrieval slot `(cue,current_goal,action)` 与每个 slot 的条目数保持不变；
4. 将完整 evidence bundle
   `(utility,actual_delta,source_episode_id,source_command_hash)` 在 slots 间做 bijective
   permutation；
5. permutation seed = canonical hash of
   `(run_seed,global_tick,sorted(stable_lineage_keys))`；按固定 slot positions 做
   deterministic rotation；
6. trace 记录 source-memory hash、projected-view hash、permutation hash、eligibility
   count 与 marginal-preservation checks；
7. 必须有至少两个 records、两个 slots、两个不同 bundle hashes，且至少一次 cross-slot
   move；否则返回 `not_applied_insufficient_records`，不得计为完成；
8. 当前 tick 的新 memory 仍按 actual canonical provenance 写入，不把 projected view
   写回 DB。

Positive control：只重命名 opaque memory IDs、不改变 semantic binding 时，candidate
behavior 必须 bit-identical；否则 memory ID 泄漏进 score，STOP。

## 11. Trace, replay and timeline contract

SQLite 继续只把 initial state、ordered typed commands 和 stored traces 作为 durable
inputs。不得新增 authoritative timeline/snapshot table。

Recovery order 必须是：

1. 读取 serialized initial state + run metadata；
2. 逐 command 调用 canonical reducer；
3. 生成 recomputed state/trace/`ReplayFrame`；
4. 最后才读取 stored trace 比较 canonical bytes/hash；
5. 任一 mismatch fail closed。

`RecoveryResult` 在内存中提供 initial frame + every-tick recomputed frames。UI timeline
只能由这些 frames 构造。用户可以只读选择历史 frame；不得从历史 frame 分叉执行；
继续 Step/Run 前必须回到 latest committed frame。

每条 trace 至少包含：

```text
producer_function
input_artifacts
run_id / seed / episode_id / episode_index / global_tick / episode_tick
trigger_source / cue / intervention modes
state_before_hash / decision_state_hash / state_after_hash
goal_before / progress / transition / goal_after
all candidates and score components
prediction / model_ref / memory_refs
selected_action / actual_delta / prediction_error
model_update / memory_update / provenance projection
command_hash / prev_command_hash / trace_hash / prev_trace_hash
aggregation_rule / code_path_hash
```

Stored selected-action deletion/tamper，即使重新 hash，也必须导致 recovery fail closed 或
被 recomputed value 覆盖比较；stored action 永远不是 behavior input。

## 12. Computed-evidence provenance gate

所有 result、baseline、ablation、leakage、trigger 与 replay fields 必须来自 callable
producer。禁止 static PASS dictionaries、handwritten scores 或只 assert verdict strings 的
tests。

Every score/report must record：

- `producer_function`；
- input artifact paths + SHA-256；
- `run_id`；
- seed、episode IDs、context/checkpoint IDs；
- aggregation rule；
- per-producer code-path hash；
- six-file live product code manifest hash。

Leakage scanner 必须扫描 command/state/trace schema 中的 selected action、future state、
actual delta、prediction/error 和 expected verdict leakage，并至少注入一个已知 leaky
positive control 证明 scanner fires。

Frozen acceptance inputs：

```yaml
seed: 17
episode_span_ticks: 8
ui_cue: novelty
required_global_ticks: 24
required_episode_indices: [0, 1, 2]
intervention_checkpoint: first eligible checkpoint at or after global_tick 16
```

这些 inputs 不得在看到结果后替换。任何 unused frozen seed/context/checkpoint 都阻断
对应 evidence claim。

## 13. Real-trigger evidence requirement

Current V1 trigger evidence: `UNVERIFIED / NOT IMPLEMENTED`。

Future acceptance 必须通过真实 Tk widget path，而不是只调用 Controller：

```text
ttk Run button invoke
-> Tk after scheduler
-> Controller.dispatch(trigger_source=ui_run_button)
-> canonical reducer
-> atomic SQLite commit
-> committed callback
-> visible redraw + recomputed timeline row
```

Callable UI acceptance 必须实例化真实 `Tk` / `PlaygroundWindow` 并调用实际 widget
handler。Headless Controller smoke 只能作为补充，不能替代 real entrypoint evidence。

ITL / Ego trigger fields 继续分开：

```text
ITL trigger: UNVERIFIED_IN_THIS_ITL_TRANSITION
Ego V0 local trigger: BANKED_RECOMPUTING_PRODUCT_TRIGGER
V1 local UI trigger: UNVERIFIED until this card is separately authorized and executed
```

## 14. Product-visible acceptance gate

未来 implementation 只有在以下全部由 live path / callable evidence 满足时，才可报告
`local_v1_continuity_product_acceptance`：

1. 显式 launcher 打开，UI 初始 paused；route/default/runtime flags 不变。
2. Run widget 产生 `trigger_source=ui_run_button` 的真实 command/trace。
3. 连续 24 logical ticks 跨过 2 个 boundaries，出现 episode indices `0,1,2`。
4. UI 同时可见 global/episode tick、current goal/age/switch reason、organism、全部
   candidates、goal gain/total gain/memory bias/cost/total、selected action、prediction、
   actual、error、model/memory update reason、provenance refs。
5. 至少一个未完成 goal 跨 episode boundary 原样 carry；goal 进入 context/score。
6. Pause 后跨至少两个 display intervals 无新 command/state；关闭窗口后无后台行为。
7. 关闭并 fresh-process 重开同一 V1 DB：final state/model/memory/current goal/clock hashes
   相同；timeline 逐 command 重算恢复。
8. 选择前一 episode 的 timeline row 显示对应 recomputed frame；只有 latest frame 可继续。
9. Memory OFF、Freeze Updates、Shuffle Provenance 从同一 checkpoint 产生第 10 节规定的
   computed read/write/hash effect 或明确 blocking negative result。
10. SQLite second-write failure 不 redraw，command/trace row parity 保持原子性。
11. Stored trace/action、command、initial state、code-path tamper controls 全部 fail closed。
12. Independent shortcut baseline 与 leakage positive control 被实际调用并记录。
13. 无第二 logic/replay/timeline truth path，无 forbidden imports/runtime registration。

如果 continuity/replay 通过但 natural cross-episode memory 没有产生 nonzero read/score
effect，必须报告 `continuity_only__memory_conditioning_not_observed`，不得写成完整 V1
acceptance。若 selected action 未改变，必须明确报告“selection-level shaping not observed”。

## 15. Evidence artifacts and acceptance aggregation

`result.json` 的 aggregation rule：只有第 14 节全部 hard requirements 为 true 且
`failure_manifest.blocking_failures=[]` 时，engineering verdict 才可为
`local_v1_continuity_product_acceptance`。Baseline equivalence 不把 product verdict 改成
science pass；它固定 claim ceiling。

Artifact set 必须可由 authorized verifier 重新生成：

- `continuity.sqlite3` — live UI path 的 serialized initial state + commands + traces；
- `trace.jsonl` — recovery 后导出的 recomputed timeline；
- `product_trigger_receipt.json` — widget-to-commit-to-redraw computed receipt；
- `baseline_comparison.json` — independent shortcut callable output；
- `ablation_report.json` — 三项 paired reruns；
- `replay_report.json` — fresh process + tamper/recovery checks；
- `leakage_report.json` — scanner + positive control；
- `failure_manifest.json` — 总是由 checks 计算生成，成功时也保留空 blocking list；
- `claim_ceiling.txt`；
- `result.json`。

## 16. Stop conditions

任一条件成立立即 STOP，不修补成 pass：

- branch/HEAD/worktree/pin drift 或 callable sync/route validation failure；
- operator 尚未单独授权 implementation；
- 新建 parallel core、第二 launcher 或第二 causal/replay/timeline path；
- 修改 EgoOperator、EgoDesktop、LLM/network/runtime/mainline；
- 修改 V0 immutable Git object/history，或静默迁移/覆盖 V0 DB；
- 需要调 V0 constants、goal coefficient 或 episode span 才产生预期 effect；
- goal、memory、provenance、update 或 timeline 仅是 cosmetic；
- wall clock、filename、cue/action name、fixture name 或 hidden label 泄漏 expected action；
- stored action/trace 驱动 replay；
- Shuffle Provenance 没有 eligible records 却被记为 pass；
- leakage scanner positive control 不 fire；
- independent baseline 未调用、共享 candidate reducer、读取 candidate trace/post-action
  fields 或 expected verdict；
- 任一 frozen seed/context/checkpoint 未使用；
- path expansion、failed focused/replay/tamper/UI/route check；
- 需要新的 governance repair、route transition 或 science claim 才能继续。

## 17. Rollback plan

- Implementation 前失败：保留本 draft；只移除 task-owned untracked implementation
  outputs，不触碰任何 pre-existing user work。
- V1 使用独立 DB namespace；rollback 不迁移或删除 V0 DB。
- Implementation commit 后若需撤销，只能用新的 additive operator-authorized reversal；
  禁止 reset/amend/history rewrite。
- Immutable baseline 始终通过 Git object `546e363...` 回读；不得把 working-tree rollback
  伪装成修改 baseline。
- 任何 rollback 都不得改变 route/default/runtime/science firewall。

## 18. Exact expected changed files for a future separately authorized implementation

以下是未来 implementation 的冻结 exact path set，**当前全部未授权**。Operator 的
后续 implementation authorization 必须逐路径确认这一完整集合；若设计需要增删路径，
必须先修订并重新审查本卡，禁止在执行中静默扩缩 allowlist。

### 18.1 Task-local mutation scope

- `docs/codex/tasks/EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A-MUTATION_SCOPE.yaml`

本 card 在 implementation 中只读，不得修改。

### 18.2 Existing product lineage

- `labs/ego_life_playground_v0/__init__.py`
- `labs/ego_life_playground_v0/engine.py`
- `labs/ego_life_playground_v0/store.py`
- `labs/ego_life_playground_v0/app.py`
- `scripts/run_ego_life_playground_v0.py`
- `tests/test_ego_life_playground_v0.py`

### 18.3 Callable verifier and focused verifier tests

- `scripts/codex/verify_ego_life_kernel_v1_continuity.py`
- `scripts/tests/test_verify_ego_life_kernel_v1_continuity.py`
- `scripts/tests/test_verify_ego_life_core_v0_baseline.py`

最后一个 path 只能修复测试 evidence producer：V0 database/trace 必须从 pinned
`Ego@546e3639299d7b11b599df3d00645666a6953bac` engine/store Git-object payload 生成，
不得从 live V1 descendant imports 生成。它不得修改 V0 validator 或历史 pins；assertion
必须验证 descendant path parity 仅为 informational/not-required，而不是要求 live path
byte-identical。

### 18.4 Frozen local product evidence

- `artifacts/EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A/continuity.sqlite3`
- `artifacts/EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A/trace.jsonl`
- `artifacts/EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A/product_trigger_receipt.json`
- `artifacts/EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A/baseline_comparison.json`
- `artifacts/EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A/ablation_report.json`
- `artifacts/EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A/replay_report.json`
- `artifacts/EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A/leakage_report.json`
- `artifacts/EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A/failure_manifest.json`
- `artifacts/EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A/claim_ceiling.txt`
- `artifacts/EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A/result.json`

## 19. Forbidden changes

- `docs/PROGRAM_STATE_UNIFIED.yaml`、`docs/STATUS.md`、
  `docs/codex/tasks/TASK_LANE_INDEX.md`、任何 route state/schema/validator；
- ITL repository files and artifacts；
- `EgoOperator/`、`EgoDesktop/`、`packages/`、legacy runtime；
- LLM、provider、network、API keys、transport、deployment、service、subprocess；
- runtime/mainline registry、default enablement、runtime authority；
- old K0/Card2 closure、science successor、formal scoring/Gate；
- V0 frozen evidence artifacts；
- any new `ego_life_playground_v1` package or alternate launcher；
- push、tag、remote anchor。

## 20. Acceptance signal and claim ceiling

### Acceptance signal

最强允许 verdict：

```text
local_v1_continuity_product_acceptance
```

它只表示：显式本地 V0-descendant product entrypoint 在默认关闭边界内，观察到由同一
reducer 驱动的 logical clock、跨 episode persistent state/current goal、memory-
conditioned score、prediction/error/update、atomic persistence 与 recomputed timeline。

### Claim ceiling

```text
Local default-off V0-descendant continuity-playground engineering evidence:
continuous logical episodes, persistent causal state, explicit current goal,
memory-conditioned candidate scoring, visible prediction/error/update, and
fresh-process recomputed timeline only.
```

### What this does not prove

不证明：general learning、associative understanding、thinking、emotion understanding、
controlled initiative、self-boundary、continuity of a subject、mechanism validity、baseline
non-equivalence、agency、autonomy、subjectivity、consciousness、electronic life、EGO
readiness、runtime/mainline effect、stable user benefit 或 product-market value。

## 21. Auto-Remote-Anchor

`Auto-Remote-Anchor: forbidden`

不 push、不 tag、不 remote-anchor。

## 22. Red-field and next-action gate

本 draft 复述了 inherited sole/frozen/authorized boundaries，属于 Red-review-sensitive
documentation。没有 operator-authorized commit transition 与 independent Claude
pre-check 时，不得 local commit。本次 draft 不修改 authority files，也不自行创建 Red
receipt。

Operator 已在独立指令中授权
`EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-READY-TRANSITION-001A`。该授权先允许把本
prereg card 经过 exact staged Claude Red review 后 bank；随后必须依次完成 ITL additive
READY descendant route 与 Ego field-by-field authority transcription。只有最终 machine
authority 暴露 exact **20-path** nonempty target set 后才允许编码；在此之前仍停止。
