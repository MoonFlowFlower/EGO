# Skill Routing Replay Test 2026-03-28

目标：用仓库里真实存在的任务单、模板、handoff 与 session archive 回放当前 skill 路由，判断是否仍有 description 过宽、过窄、或根 `AGENTS.md` 路由不够明确的问题。

## Sample Set

本轮回放使用的真实文件：

1. `Tasks/templates/type_design.md`
2. `Tasks/templates/layer3_dual_repo.md`
3. `Tasks/active/L3-20260328-proto-self-v2-dual-repo.md`
4. `Tasks/active/PROTO_SELF_KERNEL_V2_IMPLEMENTATION_TASK.md`
5. `Tasks/active/SELF_AWARE_STEP_08A_real_developmental_evidence_closure.md`
6. `Tasks/templates/type_troubleshoot.md`
7. `Tasks/templates/type_verify.md`
8. `Tasks/longrun_stage1_to_stage2_20260328/runtime/SESSION_HANDOFF.md`
9. `Tasks/archive/20260325-session-archive-e5-admission.md`
10. `Tasks/active/EXAMPLE_TASK.md`

## Mapping Table

| Real file | Expected skill | Why |
|-----------|----------------|-----|
| `Tasks/templates/type_design.md` | `ego-plan-from-spec` | 设计任务，强调方案比较、约束、实施计划，不应直接编码 |
| `Tasks/templates/layer3_dual_repo.md` | `ego-plan-from-spec` | 双仓大任务模板，默认先做 full spec 和 staged handoff |
| `Tasks/active/L3-20260328-proto-self-v2-dual-repo.md` | `ego-implement-milestone` | 已是 published dual-repo implementation card，有明确 success criteria 和实施顺序 |
| `Tasks/active/PROTO_SELF_KERNEL_V2_IMPLEMENTATION_TASK.md` | `ego-implement-milestone` | implementation entry，目标与验收字段已固定 |
| `Tasks/active/SELF_AWARE_STEP_08A_real_developmental_evidence_closure.md` | `ego-implement-milestone` | in-progress step file，要求直接推进当前主链里程碑 |
| `Tasks/templates/type_troubleshoot.md` | `ego-bugfix-root-cause` | 明确是排障、最小复现、根因修复模板 |
| `Tasks/templates/type_verify.md` | `ego-review-against-acceptance` | 明确是验收、verify、release gate、真实触发证据检查 |
| `Tasks/longrun_stage1_to_stage2_20260328/runtime/SESSION_HANDOFF.md` | `ego-resume-context` | 典型继续/恢复上下文输入，不应误触发实现或 review |
| `Tasks/archive/20260325-session-archive-e5-admission.md` | `ego-resume-context` by default; `ego-review-against-acceptance` if asked to rejudge | archive 默认用于恢复状态；只有在用户要求重新裁决 E5 结论时才进入 verify/review |
| `Tasks/active/EXAMPLE_TASK.md` | `ego-implement-milestone` | 已完成的 L2 functional example，结构上属于 milestone implementation card |

## Findings

### 1. Design and dual-repo planning needed a more concrete hint

原问题：

- `ego-plan-from-spec` 只写了“complex, cross-module, ambiguous”
- 对 repo 内常见的 `type_design` / `layer3_dual_repo` 模板提示不够直接

修正：

- description 现在显式包含 `repo design tasks` 和 `early layer3 dual-repo planning`

### 2. Implementation skill needed to recognize repo-native task cards

原问题：

- `ego-implement-milestone` 虽然语义正确，但没有明确覆盖 `step file`、`implementation task document`、`published/in-progress layer2/layer3 task card`

修正：

- description 现在显式包含这些 repo 内真实任务形态

### 3. Review skill needed to claim verify/admission territory explicitly

原问题：

- `type_verify`、release gate、admission review 在 root routing 里可以推断，但 description 还不够直接

修正：

- root `AGENTS.md` 增加了 `type_verify / release gate / admission review`
- `ego-review-against-acceptance` description 也显式吸收了这些任务

### 4. Resume skill needed a concrete file-class boundary

原问题：

- `SESSION_HANDOFF` 与 session archive 这种 repo 常见输入，更像 `resume`，但原描述没点明

修正：

- `ego-resume-context` description 现在显式指向 `session handoff / archive / status documents`

### 5. Bugfix skill benefited from naming the repo-native troubleshoot pattern

原问题：

- `type_troubleshoot` 是 repo 原生模板，但 `ego-bugfix-root-cause` 之前没有显式点名

修正：

- description 现在显式覆盖 `troubleshoot tasks` 和 `failure-case replay work`

## Root AGENTS Check

根 `AGENTS.md` 仍保持短协议，不需要继续下压：

- real commands
- directory routing
- acceptance / done
- do-not rules
- skill routing

当前没有发现新的常驻冗余段落。

## Remaining Ambiguity

只有一个保留灰区：

- 某些 archive / report 文档既可用于 resume，也可用于重新裁决旧结论

当前规则：

- 默认 `resume`
- 若用户明确要“复核 / 复判 / 判断是否仍成立 / 对照 acceptance 重新看”，则切到 `ego-review-against-acceptance`

这条规则已经足够，不需要再拆新 skill。

## Final Assessment

- 当前 skill 集合覆盖了 repo 里最常见的任务单形态
- 本轮修正后，description 更贴近真实文件类型
- 没有发现必须新增第 7 个主 workflow skill 的缺口
