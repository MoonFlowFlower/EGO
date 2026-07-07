# Joi-like Bounded Mechanism-Proxy 路线图 v1

> 任务类型：设计 + 探索（机制路线推导）
> claim ceiling（全局）：**bounded offline mechanism evidence under a specified trace/replay contract**
> 任何 capability score / green test / demo / artifact / memory card / Gate pass 都**不自动升级**为机制有效性或主体性证据。
> 标签约定：【事实】= 有公开证据；【推断】= 我从领域规律得出的判断，非测量；【假设】= 依赖未验证前提；【未知】= 当前无决定性证据。

---

## 框架校正（先于一切：你的问题里有两个隐藏 framing error）

1. **“Joi-like” 不是一个目标，是若干可分解能力的捆绑**。Joi 至少捆了：(a) 跨会话个性化记忆/关系连续性、(b) 社会推断/读人、(c) 主动发起（不被 prompt 也行动）、(d) 表面自我模型/自我保全、(e) 全息在场（**这是 renderer，不是机制**）、(f) 情绪响应。机制研究必须**分别验证各能力代理**，而**“合起来像活的”这个 gestalt 印象本身是独立的、最晚的、最高风险的 claim**，且永远停在 performance-simulation 层。把“造一个 Joi”当单一 track 是 framing error #1。

2. **A–J 不是同一轴上的竞争者**。它们混了三类东西：
   - **底座/substrate**：J（多时间尺度记忆）、B（tool-use 执行环）
   - **可组合模块/component**：A（记忆+反思）、H（用户建模）、I（受控主动性）、F（自我模型）、G（注意/salience）
   - **学习/世界模型承诺（互为替代）**：D（world-model+预测误差）、C（技能库）、E（active inference）
   把它们放进一个排名再“选一条”，是 framing error #2。正确做法：**排名 + 显式标注谁是替代、谁是互补/层**。

3. **“最可能的工程路线”——likely to what？** 通向“Joi 印象”最便宜的路（persona + memory 产品）恰恰是**机制含量最低、claim 风险最高**的路。你要的显然是另一个目标函数：**单位成本下最大化可证伪的判别性机制证据，subject to claim ceiling**。下面全部按这个目标函数推导。

---

## Part 0｜强制分类：六层 + 每层 allowed / disallowed

| 层 | 这层在问什么 | **允许说** | **禁止说** | 典型陷阱 |
|---|---|---|---|---|
| **L1 performance simulation** | 它*看起来*像不像 | “在条件 C 下产生行为 B，评分 S” | 任何“因为某机制”“内部状态”归因 | renderer / dialogue surface 被当因果机制；“看起来活的” |
| **L2 engineering implementation** | 组件是否存在并运行 | “模块 M 已实现、被入口 E 调用、延迟/吞吐、单测通过” | 存在 ≠ 有效；不得说“机制成立”“已接入主链生效” | green test 当机制证据 |
| **L3 mechanism hypothesis** | 提出一个因果结构 | “**假设** update rule U 在 latent M 上解释行为 B；形式对象如下” | 不得说已确证；不得说 proxy *就是* 机制 | 把 proxy 等同机制 |
| **L4 learning / adaptation** | 行为是否随经验**可测地**改变 | “held-out 上随 N episode 提升 ΔX（带 CI），ablate M 摧毁增益” | “像人一样学”；超分布泛化；adaptation = understanding | 分布内拟合冒充泛化 |
| **L5 agency / subject validation** | 是否是目标/发起/自我的载体 | **极窄**：“在契约 X 下系统无外部 prompt 发起动作 A，带 logged trigger T / veto V / downstream transition D——这是**控制流属性**，非 agency” | autonomy, goal, will, preference, self-awareness | initiative 被当 agency |
| **L6 philosophical consciousness** | 主观经验/现象性 | **空集**：“超出范围；我们跑的任何测量都不触及此问题” | 任何“有/无主观经验”的实证断言 | 用机制证据反推意识 |

**跨层硬规则**：L_n 的结果**永不自动升级**到 L_{n+1}。green test（L2）≠ 机制（L3）；形式化（L3）≠ 学习确证（L4）；学习增益（L4）≠ agency（L5）。**本项目的 claim ceiling 卡在 L3–L4 边界**；L5 只允许“控制流属性”这一窄义；**L6 永久 gated out**。

---

## Part 1｜一句话结论

**现阶段最可能产出诚实机制证据的，不是“造一条 Joi”，而是把它拆成可分别证伪的有界机制代理：以 (J) 多时间尺度记忆为底座、(B) tool-use 为执行环，第一梯队做 (I) 受控主动性 + (H) 用户建模 + (A) 记忆/反思——因为它们的 strongest baseline 清晰、负结果可用、成本低；机制前沿放 (D) world-model+预测误差 与 (C) 可验证技能组合（更难但最可证伪）；(E/F/G) 作为高 claim 风险的子机制谨慎纳入。任何组合产生的“像活的”印象只属于 L1，永不升级。** 关键判断：**最像活的那几条路（A/H/I/persona），恰是 strongest fair baseline 最容易抹平 gap 的路；机制含量最高的 D/C 反而最不负责“活感”。这条张力是整张图的核心。**【推断】

---

## Part 2｜路线排名表

评分 1–5（5 最好）。**baseline-erasure risk** 单独一列，**High = 坏**（强 baseline 容易抹平 gap）。"角色"列标 substrate / component / frontier(替代)。

| 路线 | 机制潜力 | 工程可行性(5=便宜) | 可证伪性 | baseline-erasure risk | claim ceiling（最高只能说到） | 角色 |
|---|---|---|---|---|---|---|
| **D** world-model+预测误差+planning | **5** | 2 | 4.5 | **Med** | model-based planning 在 held-out dynamics 上优于 model-free ΔX | frontier(替代) |
| **C** skill library/curriculum/self-verify | 4 | 2.5 | 4 | Med | 等算力下 verified 组合复用优于 flat ΔX | frontier(替代) |
| **I** controlled initiative | 3 | 4 | **5** | Med（threshold tuning 是雷，但可测） | 受控发起的**控制流属性**：net-utility 优于 best fixed-rule | component(产品价值高) |
| **B** ReAct/tool-use | 2.5 | **5** | 4 | Med（act-only 常追平） | 工具接地的闭环任务完成 + recovery | substrate |
| **H** 用户建模/ToM | 3 | 4 | 4.5 | **Med-High** | 在线更新的用户模型在 belief-change 探针上优于 history-conditioned | component |
| **A** 记忆+反思 | 2.5 | 4.5 | 4 | **High**（raw-RAG/long-context 常追平） | 抽象/反思步在 replay 契约下对 raw-RAG 的 ΔX | substrate+ |
| **J** 多时间尺度记忆 | 2 | **5** | 4 | **High** | 等 token 成本下 tiered 优于 flat-RAG 的长程 ΔX | substrate |
| **F** self-model latent | 2.5 | 4 | 4.5 | **High**（calibration 追平） | selective prediction（attempt/defer）优于校准基线 ΔX | sub-mechanism |
| **G** attention/salience/AST | 2.5 | 3.5 | 4 | **High**（top-k 追平） | 受限预算任务 ΔX + 预测自身 focus 的准确率 | sub-mechanism |
| **E** active-inference viability | 4(原理) / LLM 尺度未证 | 2 | 3.5 | **High**（curiosity-RL/Thompson 追平） | EFE 分解出的 info-seeking，pragmatic-only ablation 无 | frontier(替代, 易关route) |

**读法**：
- **近期最可能拿到诚实机制证据（feasibility × falsifiability × 低 baseline-risk）**：I > B > C。
- **机制含量天花板最高**：D > C > E，但 D/E 工程贵、E 极易被 curiosity-RL 抹平。
- **A/J/H/F/G 价值真实但 baseline-erasure risk 高**——它们更多是 substrate / 子机制，**负结果概率高，而负结果正是证据**（见 Part 5 的 stop 条件）。
- **不要把 J/A/H/I 当“替代关系”排他选择**：它们会**组合**成 companion gestalt；D/C/E 才是真正互斥的学习承诺。

> 每条路线的完整 S/O/A/M/U/J|V + 8 问形式化见下一节；表是它的压缩。

---

## 候选路线形式化（A–J）：每条都写成有界形式对象

通用骨架：**S** 真实(环境+用户隐状态，toy 中可 log)；**O** agent 实际收到的观测；**A** 动作(话语/工具/记忆写/发起/no-op)；**M** agent 跨步保留的内部状态(=agent 可控)；**U** M 的更新规则；**J|V** 目标/viability。**边界铁律：agent 控 A、M、π(A|O,M)；不控 S（含真实用户）、不控 O 的生成。** initiative 是 action，其后果落在 S。

每条回答 8 问：①解释什么 ②不能解释什么 ③更简 baseline 怎么模仿 ④哪个 ablation 摧毁它 ⑤哪个反例证伪 ⑥最小 toy env ⑦需要的 trace/replay ⑧claim ceiling。

### A. LLM + episodic/semantic memory + reflection/replay
- **S** 对话+任务世界（含用户隐状态、历史 ground truth）；**O** 当前消息 + 检索回的记忆项；**A** 话语 + 记忆写/改；**M** 外部记忆库（episodic 事件 / semantic 事实 / reflection insight）+ 检索索引；**U** write(event)→库；周期 reflect：摘要/抽象 episode→semantic+insight；读时 retrieval gating；**J|V** 跨会话任务成功 / 个性化准确 / 一致性。
1. 解释：跨会话连续、个性化、一致性、instance-specific 召回。
2. 不能解释：真正技能习得、novel dynamics 下规划、**行为为何改变**（这是召回不是策略适应）、因果世界理解。
3. 更简 baseline：**full-transcript long-context**（无记忆模块，召回到上限）；**raw-RAG over logs**（无反思/抽象）；**lookup/graph-cache**（key→fact）。判别问：reflection/abstraction 真比 raw-RAG 强吗？——**常常不强，这是 baseline-risk 热点**。
4. 摧毁性 ablation：去掉 reflection（只留原始库）→ 若不变，则“semantic/反思”机制没干活；scramble 检索项 provenance → 若性能仍在，检索非因果（renderer 效应）。
5. 证伪反例：raw-RAG 或 long-context 在同一 held-out 探针上落在 CI 内追平 → 反思机制 claim 被证伪，降级为“检索有效”。
6. toy env：多会话 persona-consistency 探针——早期注入事实，后期查询 + **矛盾消解**查询；测召回、矛盾处理、false-memory rate。
7. trace/replay：带写入 provenance 的事件日志、检索日志（每 query 取了哪些 id）、reflection diff（库前后）、冻结 replay 使同 query 命中确定的记忆态。
8. **claim ceiling**：“在 replay 契约 R 下，抽象步对 raw-RAG 在探针集 P 上产生 ΔX”。**不涉理解/自我。**

### B. ReAct / tool-use + environment feedback
- **S** 外部工具/世界态；**O** 观测串（工具返回/报错）；**A** thought + tool call + final；**M** context 内轨迹(+可选存成功轨迹)；**U** reason/act 交错、依观测调整、可选存储；**J|V** 有可校验结果的环境任务成功率。
1. 解释：接地多步完成、episode 内错误恢复。
2. 不能解释：跨 episode 学习（vanilla 不持久）、自我模型、initiative、世界模型预测。
3. 更简 baseline：**obs-only reactive**（无显式 thought）、**scripted/behavior-tree**、**单次 CoT 后 act**。判别：reason-act 交错真比同等工具权限的 act-only 强吗？——常常 thought 是 post-hoc 叙述，**hardcoding/post-hoc 风险**。
4. ablation：去掉 verbalized thought（act-only）→ 若成功率不变，推理是装饰；把 thought 换成等长随机文本 → 控 token 预算。
5. 反例：act-only 追平 → 该环境下“推理=机制”证伪。
6. toy env：小工具-API 任务 + 可校验成功 + 对抗性错误注入（工具偶发失败）测恢复。
7. trace/replay：完整 action/observation 轨迹、工具 I/O、可种子化环境、错误注入时间表。
8. **claim ceiling**：“工具接地闭环完成 + 可测错误恢复；推理轨迹在 ablation 下贡献 ΔX”。**非规划/理解。**

### C. skill library / curriculum / self-verification（Voyager 谱系）
- **S** 开放任务环；**O** 环境态 + 执行结果；**A** 提任务(curriculum) / 写技能代码 / 调技能 / self-verify；**M** 技能库（命名可执行行为 + embedding）+ curriculum 态；**U** self-verified 成功才入库、检索技能作积木、curriculum 推进；**J|V** 可校验完成任务数/质量、组合复用率。
1. 解释：累积胜任力增长、组合复用、开放习得。
2. 不能解释：连续性/个性化、自我模型、主观；对 verifier 质量脆弱。
3. 更简 baseline：**固定技能集+检索**（不增长）、**等算力 flat policy**（库真比多跑步数强？）、**canned 解 lookup**。判别：库的**组合**真比每次从零重推强吗（等算力）？
4. ablation：冻结库（不增）测增长贡献；去 self-verify（任何尝试都入库）测 verifier 角色；去 curriculum（随机任务）测 curriculum。
5. 反例：等算力 flat agent 追平 → “技能累积机制”证伪。
6. toy env：组合任务阶梯，后置任务**可证明**需组合先前技能；测 transfer。
7. trace/replay：技能库版本史(diff)、每任务 verifier 日志、curriculum 决策、可种子化环境。
8. **claim ceiling**：“在 composition-required 阶梯上 verified 组合复用对等算力 flat 的 ΔX”。**verifier 是命门，其 leakage 是头号造假向量。**

### D. world model + prediction-error update + planning
- **S** 环境 dynamics（隐参）；**O** 观测；**A** 由对学习模型 planning 选出；**M** 预测模型参数 ŝ_{t+1}=f(s_t,a_t) + belief；**U** 降预测误差更新模型(监督/变分)、用模型 rollout planning；**J|V** 预测 log-likelihood + 任务 reward + planning value。
1. 解释：预期、novel 态规划、样本高效适应、“想象”/replay。
2. 不能解释：个性化连续；且对 LLM——“世界模型”是真模型还是表面相关，存疑【未知】。
3. 更简 baseline：**model-free policy**、**history-conditioned transformer**（隐式预测下一观测）、小环境的 **transition lookup table**。判别：对模型显式 planning 真比等数据 model-free 强吗？模型对 held-out dynamics 泛化吗？
4. ablation：planning 时把学习模型换成**错误/冻结模型** → 若性能不变，planning 没用模型（模型是装饰）；planning horizon→0（reactive）测规划。
5. 反例：model-free 等数据追平；或 scrambled-model planning 追平 true-model planning → 世界模型机制证伪。
6. toy env：小 POMDP，dynamics 可变；训于一组 dynamics，测 held-out dynamics 的 zero-shot 适应（model-free **可证明**抄不了近路）。
7. trace/replay：predicted-vs-actual 下一观测日志（预测误差时序）、plan rollout、模型 checkpoint、可种子化 dynamics。
8. **claim ceiling**：“model-based planning 在 held-out dynamics 上对 model-free 的 ΔX；预测误差下降跟踪性能”。**这是机制含量最强的路，但用 LLM 诚实做最难。**

### E. active-inference-like viability objective
- **S** 环境 + agent homeostatic/viability 变量；**O** 含“内部 need”的观测；**A** 最小化 expected free energy(EFE)=pragmatic(达偏好观测)+epistemic(降不确定)；**M** 生成模型(状态/观测先验) + 后验 belief；**U** belief 变分更新、按 EFE 选动作；**J|V** V=留在 viable set / 最小化变分自由能；偏好编码为先验。
1. 解释：感知-动作-探索的**统一**、不手写 curiosity 的内在探索（epistemic value）、“为何行动”的原理性（维持 viability）。
2. 不能解释：LLM 尺度上**基本是 aspirational**——【未知】无公开的、自由能语义诚实的 LLM-scale active-inference agent；“free energy”常是 loss 改名。
3. 更简 baseline：**RL+curiosity bonus**（匹配 epistemic 探索）、**max-entropy RL**、**Thompson sampling**（匹配不确定性驱动）、**scripted explore-then-exploit**。判别：EFE 比 curiosity-RL 在同环境多买到什么？
4. ablation：去 epistemic 项（只 pragmatic）测信息搜寻贡献；去 priors-as-preferences 测偏好机制。
5. 反例：curiosity-RL 或 Thompson 追平 → active-inference 机制未被区分（**很可能**→ 高关route风险）。
6. toy env：小部分可观环境，**reward 前必须先搜集信息**（epistemic value 必要），如“探门找哪扇有奖”。
7. trace/replay：belief 轨迹、每步 EFE 分解（pragmatic vs epistemic）、预测误差。
8. **claim ceiling**：“EFE-分解控制器表现出 pragmatic-only ablation 所无的 info-seeking，且对 curiosity-RL 有 ΔX”。**禁止生物/意识相关性宣称。优雅方程当证据=最高风险，硬标。**

### F. self-model as bounded latent state（非主观自我）
- **S** 环境 + agent 自身过去行为/能力(关于自己的 ground truth)；**O** 含自身表现反馈的观测；**A** 动作 + 自报/能力估计/abstain；**M** 编码“我知道什么/能做什么/倾向什么/对什么不确定”的 latent/结构库；**U** 由结果更新自我模型(校准：我对了吗？我能做 X 吗？)；**J|V** 自预测的校准/准确、靠自知改善路由/abstain。
1. 解释：校准置信、knowing-when-you-don't-know、abstention、能力感知路由、**行为意义上的**自监控。
2. 不能解释：主观自我、身份、经验——**显式排除**；也不解释任务胜任本身。
3. 更简 baseline：**logit 校准**(temperature scaling)、**“我能解吗”分类器**(特征上训)、**post-hoc verifier**。判别：显式 latent 自我模型真比校准置信头/外部 verifier 强吗？
4. ablation：把自我模型换成校准 p(correct) 头 → 若等同，“自我模型”超不出校准；冻结自我模型测其更新。
5. 反例：校准 baseline 追平 → “自我模型机制”坍缩为置信校准（**很可能**）。此处负证据重要且诚实。
6. toy env：异质难度任务套，agent 须**决定 attempt 还是 defer**；对错赏罚、允许 defer；自知应提升净收益。
7. trace/replay：自估 vs 结果(校准曲线)、abstention 决策、自我模型态演化。
8. **claim ceiling**：“有界自我模型在 selective prediction(attempt/defer) 上对校准基线 ΔX；reliability diagram 改善”。**严格行为级自监控，无 selfhood。**

### G. attention / salience model（含 attention schema, AST）
- **S** 含可变任务相关特征的环境；**O** 高维观测；**A** where-to-attend / what-to-retrieve / what-to-include，再任务动作；**M** salience 权重 / attention schema(对自身 focus 的模型)；**U** 由 reward/预测误差更新 salience；**J|V** 信息瓶颈(有限 context/检索预算)下的任务表现。
1. 解释：瓶颈下高效选择、忽略干扰、**attention-schema=预测自身 focus 的模型**（Graziano AST 作**工程代理**，非意识）。
2. 不能解释：意识（AST 的宏大 claim 显式排除）、任务胜任本身。
3. 更简 baseline：**原生 transformer attention**、**TF-IDF/embedding top-k**、**random subset**、**full-context 上界**。判别：学习/显式 salience 在固定预算下真比 top-k 强吗？
4. ablation：去 salience 模型(均匀/随机选)同预算；scramble salience → 若性能仍在，salience 非因果。
5. 反例：embedding top-k 追平 → 无独立机制。
6. toy env：needle-in-haystack + 干扰 + 硬 context 预算；或可测 schema(预测未来 focus) vs 实际 attention 的任务。
7. trace/replay：每项 salience 分、admit vs drop、下游效应；AST：predicted-attention vs realized-attention 日志。
8. **claim ceiling**：“显式 salience/attention-schema 在受限预算上对 top-k 的 ΔX，且以准确率 Y 预测自身 focus”。**零意识宣称；AST 只作工程类比。**

### H. social inference / user modeling（ToM）
- **S** 用户真实隐状态(意图/知识/偏好/情绪-as-label)；**O** 用户消息/行为；**A** 话语/澄清/对用户的预测；**M** 用户模型(对用户隐状态的 belief)；**U** 由交互更新用户模型(理想为 Bayesian/显式)；**J|V** 预测用户下一动作/需求/答案的准确、conditioned on 正确用户-belief 的任务成功、校准的澄清。
1. 解释：预期需求、适配风格、知道何时澄清、“读”用户——Joi 式 attunement 的核心。
2. 不能解释：agent **在乎**(它不；value-claim 禁止)；世界胜任。
3. 更简 baseline：**majority/most-frequent intent**、**history-conditioned 下一动作预测器**(无显式 belief)、**persona-memory 产品基线**(存偏好+模板)。判别：显式/在线更新的用户模型真比 history-conditioned 与 stored-profile 强吗？
4. ablation：去用户模型更新(静态 profile)测在线 ToM；给真实用户态(oracle)作上界；scramble 用户模型证伪因果。
5. 反例：history-conditioned 或 stored-profile 追平 → “ToM 机制”只是个性化召回（**很可能**，高 baseline 风险）。
6. toy env：隐意图**会变**的用户模拟器(需 belief 更新，非仅 stored profile)；测预测准确 + 澄清效率；含 false-belief 探针(agent 须建模**用户**持错误信念)。
7. trace/replay：用户模型 belief 轨迹、预测 vs 实际用户动作、澄清决策、模拟器 ground-truth 隐状态。
8. **claim ceiling**：“在线用户模型对 history-conditioned+stored-profile 的 ΔX（尤其 belief-change 探针）”。**无 empathy/care 宣称。**

### I. controlled initiative（trigger / veto / cooldown / downstream transition）
> 最像“Joi 自发行动”，也最危险（易冒充 agency）。**重构为控制流属性，非 agency。**
- **S** 环境 + opportunity 结构(何时介入真有用) + 用户 receptivity；**O** 可能值得 unsolicited 动作的信号/上下文；**A** {intervene(content), 沉默}，介入带 typed trigger；**M** 发起策略参数 + cooldown 态 + 过往发起及结果日志；**U** 由 downstream outcome(unsolicited 动作被接受/有用？)更新发起策略，强制 veto/cooldown；**J|V** 净效用 = value(有用介入) − cost(误/扰介入)；须**同时**胜过 always-silent 与 always-act。
1. 解释：主动协助、“不请自来”地行动、timing。
2. 不能解释：autonomy/will/goal——**显式禁止**；trigger 是学习/指定函数，非欲望。
3. 更简 baseline：**always-silent**、**always-act**、**fixed-rate/scheduled**、**单信号 threshold**、**behavior-tree 规则**。判别：策略真比 best fixed-rule 净效用高吗？增益来自真读上下文，还是 threshold tuning？
4. ablation：去 downstream 更新(静态 trigger)测学习；去 veto/cooldown 测安全机制代价；**把学习 trigger 换成 tuned threshold**——“这只是 threshold tuning 吗”的关键检验；scramble trigger 特征。
5. 反例：tuned single-threshold 或 behavior-tree 追平净效用 → “受控主动性机制”只是 threshold tuning，降级。（**你显式担心的雷，必须前置。**）
6. toy env：上下文流 + 隐“值得介入”标签 + 误报代价模型 + receptivity 模型；测净效用、发起 precision/recall、**downstream 状态是否真转移**(介入是否改变了轨迹)。
7. trace/replay：每次发起决策(带 trigger 特征)、veto/cooldown 态、downstream 前后状态、可得的 counterfactual no-op。
8. **claim ceiling**：“gated-initiative 控制器在 cooldown/veto 约束下，净效用对 best fixed-rule 的 ΔX，附 logged trigger→effect transition”。**纯控制属性，无 agency/autonomy。**

### J. multi-timescale memory（working/episodic/semantic/procedural/compressed）
> 这是 substrate，不是单机制——A/F/H/I 跑在其上。
- **S** 长任务/对话世界；**O** 跨多步/会话观测；**A** 跨库 read/write/compress/promote + 任务动作；**M** 分层库{working(context)/episodic(事件)/semantic(事实)/procedural(技能)/compressed(capsule)} + promotion/eviction 策略；**U** write→episodic、consolidate→semantic、成功→procedural、compress→capsule、按策略 evict；**J|V** 长程下有界 context 的表现、截断后状态恢复、成本(token) vs 表现。
1. 解释：有界 context 下长程连续、抗漂移、你 CLAUDE.md 里的 “capsule + refs” 模式。
2. 不能解释：任何单一认知能力；它是底座。风险：schema 复杂度被当能力。
3. 更简 baseline：**flat append+RAG**、**long-context(无分层)**、**sliding-window**、**summary-only**。判别：tiers+promotion 在等成本下真比 flat-RAG/long-context 强吗？
4. ablation：塌成单库；去 consolidation；去 compression → 测各层边际价值。
5. 反例：flat-RAG 或 long-context 等预算追平 → 多时间尺度机制不成立，保 flat（更简）。**schema-hides-failure 风险此处最高。**
6. toy env：长多会话任务，交织召回、procedure 复用、截断/恢复事件；测表现与 token 成本。
7. trace/replay：各层随时内容、promotion/eviction 事件、compression diff、检索日志、成本账。
8. **claim ceiling**：“tiered 在 ≤ 等 token 成本下对 flat-RAG/long-context 的长程 ΔX，每层经 ablation 证成”。**仅 substrate 宣称。**

---

## 跨切审计：通用作弊向量清单（你要求的有界深度审计）

对**每一条**路线，交付前必须过这张表。任一命中 = 该结果停在 hypothesis，禁用“已生效/已闭环”口径。

| 向量 | 它长什么样 | 检测动作 |
|---|---|---|
| **proxy 易作弊** | 指标可被与机制无关的捷径拉高（如长度、关键词、礼貌度） | 加“捷径基线”（majority/length-matched random）；若追平，proxy 失效 |
| **hard-coding** | if-else 直接编码答案/行为 | 读代码 + 输入扰动：换分布若仍“对”，是写死 |
| **if-else fake latent** | “latent state” 实为离散规则分支 | 检查 M 是否进入梯度/更新；scramble M 若不影响输出，是假 latent |
| **label leakage** | 决策时可见了 outcome/label | 在 trace 里验证 decision-time 视野**不含**结果；时间戳审计 |
| **threshold tuning** | 增益来自调阈值而非机制 | 用 tuned-threshold baseline 对照（尤其 I/F/G）；追平即降级 |
| **post-hoc explanation** | thought/reflection 是事后叙述非因果 | act-only / 去叙述 ablation；scramble 叙述 |
| **schema hides failure** | 改 schema/字段使失败不显形（尤其 J） | 固定评测 schema；对照旧 schema 的失败率；看 false-memory/drift |
| **renderer = mechanism** | dialogue surface/全息呈现被当因果 | scramble 内部状态但保表层；若“仍像活的”，活感属 L1 |
| **replay 太弱** | replay 不确定、不可复现 | 要求 seed+冻结模型版本+冻结记忆快照 → 同输入同输出的 bit/语义级一致 |
| **baseline 太弱** | 只比 naive chatbot | 强制 Part 5 的 baseline 阶梯 + oracle 上界 |
| **claim 膨胀** | L_n 结果说成 L_{n+1} | 对照 Part 0 表与 Part 7 禁列；每条 claim 标层 |

**总原则：Negative evidence is evidence。strongest fair baseline 抹平 gap → 关闭或重设计该路线，不许 patch 成 pass。**

---

## Part 3｜推荐的最小闭环架构（含 S/O/A/M/U/J|V）

**“user-simulator companion loop”**——一个能**同时**廉价、诚实测第一梯队机制（I/H/A/J），并把每个机制做成**独立可 ablate** 的底座。之所以用模拟器：它给 ground-truth，从而能算诚实 gap 与 oracle 上界——这正是 “bounded offline mechanism evidence under trace/replay contract” 的载体。

- **S（模拟器拥有，全 log）**：用户隐状态 u_t = (intent, knowledge, receptivity, 会变的 mood-as-label) ；任务/世界态 w_t ；介入机会标签 o_t（值不值得主动）。
- **O（agent 收到，**不含** u_t）**：用户消息、检索回的记忆、上下文信号。
- **A**：{ utterance, memory write/consolidate ops, **initiate-or-stay-silent(trigger)**, clarify }。
- **M（agent 可控）**：tiered memory{working/episodic/semantic/procedural/capsule} + 用户模型 belief b_t(u) + 发起策略态(cooldown) + 自我/校准估计。
- **U**：write/consolidate 规则 + 用户模型更新 + **发起策略由 downstream outcome 更新**。
- **J|V**：复合 = 任务成功 + 用户需求预测准确 + 发起净效用 − context 成本，**带 viability 约束**（token 预算内 + veto/cooldown 边界内）。
- **边界**：agent 控 M、π；模拟器拥有 S（含真实用户）。**全部写入带 provenance 的 replay 库。**

**关键设计点**：
1. 每个机制（I/H/A/J/F）挂 **feature flag**，可单独关而不动其余 → ablation 是开关不是 code-fork。
2. 每个机制的 **strong baseline 与 oracle 上界**直接接进同一 harness，跑同 trace/replay。
3. decision-time 视野与 outcome 在 trace 中物理分离 → 防 label leakage。
4. 先建这个 loop（≈ I 的 toy env 的超集），后续 T2/T3 复用其 trace/replay/baseline harness。
- **此架构的 claim ceiling**：它本身只是测量台，**不产生任何 L5/L6 结论**；它只把各机制的 ΔX 变成可复现数字。

---

## Part 4｜第一批 3 个最小 toy experiments

选“最便宜 × 最可证伪”，外加一条机制前沿留作下一批。

- **T1（路线 I，受控主动性）**：模拟器上的发起净效用。可证伪性最强、产品相关最直接，且把你最担心的 threshold-tuning 做成 kill 标准。**优先做——它顺便建好 T2/T3 复用的 replay+baseline harness。**
- **T2（路线 A+J，记忆连续性 + 反思价值）**：多会话 persona/事实一致性 + 矛盾消解；核心问：tiers/reflection 在等 token 成本下是否打得过 raw-RAG / long-context。
- **T3（路线 H，用户建模 + belief-change 探针）**：隐意图会变的用户模拟器；核心问：在线用户模型是否在 **belief-change/false-belief** 探针上打过 history-conditioned 与 stored-profile（静态 profile 在此**必败**才有区分力）。
- **下一批（不在这 3 个内）**：T4=D（小 POMDP held-out dynamics，model-based vs model-free）；T5=C（composition-required 技能阶梯）。D/C 机制含量更高但工程更贵，放第二批。

---

## Part 5｜每个实验的 strongest baseline / ablation / acceptance gate / stop-rollback

通则：**预注册** δ、seeds、探针集；冻结 replay；报 bootstrap CI；**负结果是决策结论，不是 patch 目标**。δ 建议预注册为相对 +10%（按环境校准），gate 要求 CI 不重叠。

### T1 — controlled initiative
- **strongest baselines**：always-silent；always-act；fixed-rate schedule；**best single-threshold（val 上调优）**；**behavior-tree 手写规则**；obs-only policy；**oracle（知 o_t）上界**。
- **ablations**：去 downstream 学习（静态 trigger）；去 veto/cooldown；**学习 trigger → tuned threshold**；scramble trigger 特征。
- **acceptance gate**：学习策略净效用 ≥ best baseline + δ（CI 不重叠）**且** 去 trigger-学习摧毁 ≥ 半增益 **且** logged trigger→downstream transition 显示介入**真的改变了轨迹**（非相关）。
- **stop / rollback**：tuned-threshold 或 behavior-tree 落 CI 内追平 → **关 route**：降级为“无超 threshold 的机制”，保 behavior-tree 作便宜解，记负证据。

### T2 — memory + reflection
- **strongest baselines**：no-memory；**full-transcript long-context**（召回近上界）；**raw-RAG**（无反思/分层）；summary-only；lookup/graph-cache；**persona-memory 产品基线**。
- **ablations**：去 reflection（原始库）；塌 tiers 为单库；去 consolidation；scramble 检索 provenance；去 compression。
- **acceptance gate**：tiered+reflection 在 held-out 多会话探针上对 raw-RAG ≥ δ **且** ≤ 等 token 成本 **且** reflection-ablation 摧毁 ≥ 半增益 **且** false-memory rate ≤ baseline。
- **stop / rollback**：raw-RAG 或 long-context 等成本追平 → **关反思/分层 claim**，保 raw-RAG（更简），记负证据。

### T3 — user-model / ToM
- **strongest baselines**：majority/most-frequent need；**history-conditioned 下一需求预测器**（无显式 belief）；**stored static profile**；**oracle（真 u_t）上界**；persona 产品基线。
- **ablations**：冻结用户模型（无在线更新）；去“对用户 false belief 的建模”；scramble belief 态。
- **acceptance gate**：在线用户模型对 history-conditioned + stored-profile ≥ δ **且** 在 **belief-change/false-belief 探针**上显著（静态 profile 必败处）**且** scramble belief 摧毁增益。
- **stop / rollback**：history-conditioned 在 belief-change 探针上追平 → **关 “ToM 机制”**，降级为“个性化召回”，记负证据。

---

## Part 6｜需要你提供哪些本地 artifact / trace / replay（unknown → fact 的转换器）

【假设】你的 EgoCore/OpenEmotion 已产出某种 trace。把 unknown 变 fact，**必须**这四件齐全；缺任一，所有“机制”claim 停在 hypothesis/unknown：

1. **确定性 replay 契约**：能 re-run 一条 logged episode，给定 (seed + 冻结模型版本 + 冻结记忆快照 + 冻结环境/模拟器) → 复现 A given (O,M)，并有哈希证明用了同输入。
2. **ground-truth 或 labeled outcome**：模拟器给隐状态；真实用户至少给 labeled 下一需求/介入是否被接受/任务是否成功。无 outcome 则无法算 gap。
3. **ablation hooks（feature flags）**：每个机制可单独关而不改其余代码 → ablation 干净。
4. **strong-baseline harness**：Part 5 的 baseline + oracle 能在**同** trace/replay 上跑。

具体 trace schema（每条都要）：
- **每步**：O、A、**M-diff**、检索集(带 id)、工具 I/O、latency、decision-time 视野快照（**证明不含 outcome** → 防 label leakage）。
- **I**：每次发起的 trigger 特征、veto/cooldown 态、downstream 前后状态、可得 counterfactual no-op。
- **A/J**：库随时快照、consolidation/compression diff、eviction 事件、token 成本账。
- **H**：belief 态对象随时；模拟器给 ground-truth u_t；真实用户给 labeled 结果。
- **F**：自估 vs 结果配对（校准数据）。
- **provenance 完整性**：内容哈希；并在 trace 里**机器可验** decision-time 不可见 outcome。

> 你给我这些后，我能把 Part 2 表里每个“【推断】baseline 会追平”变成“【事实】在你的数据上追平/未追平 ΔX (CI)”。**在此之前，凡是“已生效/机制成立”的话都不许说。**

---

## Part 7｜明确不能宣称的内容（claim 禁列）

无论 demo 多像、test 多绿、memory card / Gate 多漂亮，**禁止**宣称以下任意一条（除非有该层直接证据，而本 ceiling 下 L5/L6 永久无证据）：

- consciousness / subjective experience / qualia / sentience / phenomenality
- real emotion（区别于一个 labeled affect 变量）、empathy、care、“在乎用户”
- self-awareness / 真实自我 / 身份 / 真实人格
- genuine understanding（区别于分布内拟合）
- autonomy / agency / free will / goals / desires / intentions（作为心理状态）
- “alive” / 真实生命 / EGO readiness
- stable user benefit / 长期用户福祉（无纵向证据）
- 超出受测分布的泛化
- **green test / demo / artifact / memory card / Gate pass = 机制有效 或 主体性**（类别错误）
- **looking alive = being alive**（L1 不升级）
- **renderer / dialogue surface = 因果机制**
- **优雅方程（free energy）/ 生物·神经类比 = 证据**（理论只有产出对独立 baseline 的判别性预测才升级）
- **多个已验证 proxy 的组合 = 一个 subject**（组合本身是独立的、最高风险 claim，仍停 L1/L3）

**全局唯一允许的最高 claim**：*bounded offline mechanism evidence under a specified trace/replay contract*，且每条都标注其所在层与 ΔX(CI)。

---

## Part 8｜2 周内可执行 bounded task card（选 T1）

选 T1（受控主动性）作 2 周卡：最小的诚实可证伪面、产品相关最高、且**内建你最怕的 threshold-tuning kill 标准**；它还顺手建出 T2/T3 复用的 replay+baseline harness。

| 字段 | 内容 |
|---|---|
| **problem** | “受控主动性”是真机制，还是 threshold tuning / behavior-tree 的改名？现状【未知】。 |
| **layer** | 主体 L3→L4（机制假设→学习适应的有界证据）；发起属性最多到 L5 的**窄义控制流**，不碰 agency。 |
| **mainline target** | 在 user-simulator 上，gated-initiative 控制器净效用**显著且机制性地**超过 best fixed-rule，并有 logged trigger→downstream-transition。 |
| **hypothesis** | 由 downstream outcome 在线更新的发起策略，在净效用上 ≥ best single-threshold + δ，且去掉该更新摧毁 ≥ 半增益。 |
| **strongest baseline** | always-silent / always-act / fixed-rate / **best tuned single-threshold** / behavior-tree / obs-only / **oracle(知 o_t) 上界**。 |
| **ablation** | 去 downstream 学习（静态 trigger）；去 veto/cooldown；**学习 trigger→tuned threshold**；scramble trigger 特征。 |
| **trace-replay** | 每次发起：trigger 特征 + cooldown/veto 态 + downstream 前后状态 + counterfactual no-op；seed+冻结模型+冻结模拟器 → 确定性复现；decision-time 视野证明不含 outcome。 |
| **acceptance gate** | 净效用 ≥ best baseline + δ（预注册，CI 不重叠）**且** trigger-学习 ablation 摧毁 ≥ 半增益 **且** transition 证明介入改变轨迹。 |
| **claim ceiling** | “在 replay 契约下，gated-initiative 对 best fixed-rule 有净效用 ΔX(CI)，受 cooldown/veto 约束”。**禁止** autonomy/agency/will/主动意图。 |
| **stop / rollback** | tuned-threshold 或 behavior-tree 落 CI 内追平 → **关 route**：降级为“无超 threshold 的机制”，保 behavior-tree 作便宜解，把负证据写入 docs；harness 仍保留供 T2/T3。 |

**2 周分解**（建议）：W1 = 建 simulator + trace/replay + baseline 阶梯 + flag 化机制；W2 = 跑 ablation/gate + 出 CI + 写结论（含可能的“关 route”负结论）。

---

### 本文档 fact/inference/unknown 边界（自审）
- 【事实】Voyager/MemGPT/MIRIX/RMM/MemMachine/ReAct/Reflexion 等系统及其结构存在；active inference 有 LLM 集成尝试（见 Sources）。
- 【推断】“强 baseline 常抹平 A/H/I/F/G/J 的 gap”——来自领域规律与这些方法的已知失败模式，**非**对你系统的测量。
- 【假设】你本地有可做 replay 的 EgoCore/OpenEmotion trace。
- 【未知】LLM 尺度 active inference 是否真胜过 curiosity-RL；你系统里各机制的真实 ΔX——须等 Part 6 的 artifact。
