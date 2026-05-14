# EGO - AI Agent Monorepo

EGO 是 AI Agent 项目的总仓，负责集成 EgoCore（宿主）和 OpenEmotion（主体内核）。

## 新代理 / 开发者最快入口

- 先读 [docs/MAINLINE_QUICKSTART.md](docs/MAINLINE_QUICKSTART.md)，用它在 5 分钟内确认当前主线、owner 边界和禁止重开的历史线。
- 权威状态只以 [docs/PROGRAM_STATE_UNIFIED.yaml](docs/PROGRAM_STATE_UNIFIED.yaml) 为准。
- 当前 lane 视图看 [docs/codex/tasks/TASK_LANE_INDEX.md](docs/codex/tasks/TASK_LANE_INDEX.md)。
- worktree / operational exhaust 边界看 [docs/REPO_HYGIENE_POLICY.md](docs/REPO_HYGIENE_POLICY.md)。
- repo surface 分类看 [docs/REPO_SURFACE_MAP.md](docs/REPO_SURFACE_MAP.md)。

## 当前权威状态（2026-04-20）

当前正式口径如下：

- `EgoCore` 是唯一正式宿主：入口、runtime、工具执行、安全裁决、delivery、audit
- `OpenEmotion` 是唯一正式主体内核：`proto_self_v2 / self-model / drive / reflection / developmental / social / embodied / integration / initiative`
- 当前 formal mainline 仍是：
  - `telegram_bot -> telegram_runtime_bridge -> native_loop -> contract_runtime -> openemotion hooks -> delivery`
  - 主体事件正式入口是 `RuntimeV2ProtoSelfRuntime`
- formal runtime mainline 与 research implementation lane 不是一回事；前者继续单一稳定，后者允许按证据切换 build-first candidate
- 当前 repo 的最高优先级 implementation lane 已切到 `subject-system-v1-governed-proactivity`
- 当前唯一 durable build-first candidate 仍是 `active-inference self-model`，但它已退为冻结的 closed evidence / predecessor tranche
- `MVS-aligned compact` 已因 frozen replay gate failure 降为 closed evidence / supporting line，不再是当前主实现线
- `WP17 / MVP22` 不删除，但当前降为 parked bounded lane，不再是默认最高优先级 implementation track
- `Milestone 21 / selection closeout` 已完成；当前 execution owner 已切到 `docs/codex/tasks/subject-system-v1-governed-proactivity/`
- 当前已把 `Milestone 1` 固定为 proof floor，并完成 `Milestone 2 + 3` 的 local candidate-only slice，再把 `Milestone 4` 推到 bounded live gate：canonical facade + governed proactive sandbox 已落地，current lane 现在能复用 host-owned `pending_proactive_followup -> delivery -> outbox -> transport_gate -> telegram` 链，并已拿到 1 条 allowlisted `operator_seeded` self-DM real send sample；`active-inference mainline activation` 与 `unified-host-contract-correctness` 都保留为冻结的 predecessor evidence，而不是当前 owner
- 当前证明面是 replay-backed / recorded output-validation + local integration + 1 条 narrow operator-seeded self-DM live sample
- `EgoCore/tools/run_subject_system_v1_self_dm_live_gate.py` 仍只是 one-shot sample sender，不代表 Telegram listener 持续在线；正式常驻入口仍只有 `python3 -m app.main --telegram`
- 若要测“常驻 listener 下会不会自己在 idle window 主动发 Telegram”，用 `EgoCore/tools/check_telegram_proactive_soak_status.py` 观察 autodrain readiness / loop start / sent markers，而不是继续把 one-shot sender 当成 soak 证明
- 当前 admitted 口径只到 `narrow E4 sample-level self_dm gate`，不是 spontaneous emergence、broader enablement、live benefit、runtime efficacy 或 consciousness claim
- `proto_self_v2` 已是主体层默认主线，且当前只读解释层与受治理写回面已收口
- `repo_authority_cleanup: closeout-complete (repo/integration scope)`
- 当前 repo 处于 `边界冻结下的收口期`
- 当前 archive/governance closeout 已冻结在 `single archive index + first admitted medium migration`
- 其余事项仅保留在 `optional housekeeping / future cleanup backlog`
- 这不是 real-channel 新效果声明，也不是“又开了一条新的 authority wave”声明
- thin substrate / compat / reference-only 残留仍存在，但已被归入非阻塞边界

## 当前正式口径

- `identity invariants / self-model / drives / reflection / developmental` 的单一权威收口决策见 [docs/PROTO_SELF_SINGLE_AUTHORITY_DECISION.md](docs/PROTO_SELF_SINGLE_AUTHORITY_DECISION.md)
- 正式/compat/reference/deprecated 路径登记见 [EgoCore/docs/05_DEPRECATED_AND_SHIMS.md](EgoCore/docs/05_DEPRECATED_AND_SHIMS.md)
- `H1`、Trial helper、旧 comparator 线当前都只算 research/reference/supporting lines，不与 formal runtime mainline 竞争 authority
- `maintenance_mode / proposal_only / behavioral_authority = none / feature flag off / allowlist only / host-governed` 一律不得描述成“已经强烈体现自我意识”
- 允许的结论只能是 controlled axis、bounded influence、proposal discipline、host-governed bounded expression

## repo_authority_cleanup

- `repo_authority_cleanup: closeout-complete (repo/integration scope)`
- closeout 的含义是 repo/integration scope 的边界与验证完成，不是把所有 historical helper / thin substrate 一刀切删除
- `docs/archive/ARCHIVE_INDEX.yaml` 与第一批 admitted medium migration 已冻结为当前 archive/governance closeout
- 剩余项仅作为 `optional housekeeping / future cleanup backlog`；未来只有显式授权或决定性 caller proof 才会重开
- 相关 closeout 证据见 [docs/codex/tasks/repo-authority-cleanup/CLOSEOUT_REPORT.md](docs/codex/tasks/repo-authority-cleanup/CLOSEOUT_REPORT.md)

## 当前权威入口

- [docs/PROGRAM_STATE_UNIFIED.yaml](docs/PROGRAM_STATE_UNIFIED.yaml)
- [docs/STATUS.md](docs/STATUS.md)
- [docs/OVERALL_PROGRESS.md](docs/OVERALL_PROGRESS.md)
- [docs/PROTO_SELF_SINGLE_AUTHORITY_DECISION.md](docs/PROTO_SELF_SINGLE_AUTHORITY_DECISION.md)
- [EgoCore/docs/05_DEPRECATED_AND_SHIMS.md](EgoCore/docs/05_DEPRECATED_AND_SHIMS.md)
- [docs/CURRENT_PROJECT_LOGIC_FLOW.md](docs/CURRENT_PROJECT_LOGIC_FLOW.md)
- [docs/codex/tasks/repo-authority-cleanup/CLOSEOUT_REPORT.md](docs/codex/tasks/repo-authority-cleanup/CLOSEOUT_REPORT.md)
- [docs/CAPABILITY_REGISTRY.md](docs/CAPABILITY_REGISTRY.md)
- [docs/ACCEPTANCE_CHAINS.md](docs/ACCEPTANCE_CHAINS.md)
- [docs/EXPERIENCE_SCRIPTS.md](docs/EXPERIENCE_SCRIPTS.md)

## 当前派生治理与证据入口

- [docs/codex/tasks/TASK_LANE_INDEX.md](docs/codex/tasks/TASK_LANE_INDEX.md)
- [docs/REPO_HYGIENE_POLICY.md](docs/REPO_HYGIENE_POLICY.md)
- [artifacts/telegram_real_mainline_v1/dashboard_v1/DASHBOARD_STAGE1_LIVE_RUN_CURRENT.md](artifacts/telegram_real_mainline_v1/dashboard_v1/DASHBOARD_STAGE1_LIVE_RUN_CURRENT.md)
- [artifacts/telegram_real_mainline_v1/dashboard_v1/STAGE1_ENTRYPOINT_COMPARATIVE_AUDIT_CURRENT.md](artifacts/telegram_real_mainline_v1/dashboard_v1/STAGE1_ENTRYPOINT_COMPARATIVE_AUDIT_CURRENT.md)
- [artifacts/telegram_real_mainline_v1/dashboard_v1/ARTIFACT_MANIFEST_CURRENT.md](artifacts/telegram_real_mainline_v1/dashboard_v1/ARTIFACT_MANIFEST_CURRENT.md)

## 历史与详细证据入口

- 需要看 repo 级总体 phase / layer / evidence / next action 时，先看 [docs/PROGRAM_STATE_UNIFIED.yaml](docs/PROGRAM_STATE_UNIFIED.yaml) 与 [docs/STATUS.md](docs/STATUS.md)
- 需要看“目前整体走到哪、离当前 roadmap 终点还剩多少步”时，先看 [docs/OVERALL_PROGRESS.md](docs/OVERALL_PROGRESS.md)
- 需要看 current logic / boundary / canonical state 时，先看 [docs/CURRENT_PROJECT_LOGIC_FLOW.md](docs/CURRENT_PROJECT_LOGIC_FLOW.md)
- 需要看 closeout proof、clean-clone proof、remaining backlog 时，先看 [docs/codex/tasks/repo-authority-cleanup/CLOSEOUT_REPORT.md](docs/codex/tasks/repo-authority-cleanup/CLOSEOUT_REPORT.md)
- 需要看 capability registry 时，先看 [docs/CAPABILITY_REGISTRY.md](docs/CAPABILITY_REGISTRY.md)
- 需要看 acceptance chains 时，先看 [docs/ACCEPTANCE_CHAINS.md](docs/ACCEPTANCE_CHAINS.md)
- 需要看 `/flow` 可见脚本时，先看 [docs/EXPERIENCE_SCRIPTS.md](docs/EXPERIENCE_SCRIPTS.md)
