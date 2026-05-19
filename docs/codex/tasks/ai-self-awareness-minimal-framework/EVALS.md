# Evaluation Harness

## Eval principle

评测对象不是 “看起来像不像有自我意识”，而是：

- 是否在 held-out tests 或 replay-style synthetic tests 上改善 `5` 个 operational targets

## Families

1. `sustained_identity`
2. `decision_impact`
3. `plasticity`
4. `tension_causality`
5. `corrective_trace`

## Held-out conditions

- session reset
- low explicit self cue
- conflicting prior identity cue
- repeated failure
- tension shock
- ambiguous choice pressure
- delayed correction

## Candidate set

- `baseline_chat`
- `narrative_identity_shell`
- `identity_only`
- `trace_only`
- `operational_self_loop_core`
- `mvs_aligned_compact`
- `active_inference_self_model`

## Post-closeout SubjectCore compare set

For the planning-only `SubjectCore` supplement, add one additional compare group:

- `memory_only_continuity_layer`
- `state_only_minimal_substrate`
- `hybrid_unified_subjectcore`

These do not replace the canonical build-first candidate set above.
They are a post-closeout architecture compare pack for the continuity/initiative question.

## Additional scored dimensions for the SubjectCore compare pack

- `C1 continuity`
- `C2 plasticity`
- `C3 autonomous_proposal`
- `C4 governor_integrity`
- `C5 readability`

Reading rule:

- `memory_only_continuity_layer` should mainly win `C1/C5`
- `state_only_minimal_substrate` should mainly win `C2/C4`
- `hybrid_unified_subjectcore` only wins if it is competitive on all five

## Pass thresholds

- `sustained_identity >= 0.68`
- `decision_impact >= 0.70`
- `plasticity >= 0.68`
- `tension_causality >= 0.70`
- `corrective_trace >= 0.72`
- composite `>= 0.74`

## Decision thresholds

### build now

- 五项全部过线
- 与 `baseline_chat` 的 composite 差值 `>= 0.20`
- 与最近的更小 partial candidate 差值 `>= 0.10`
- 依赖成本低于 backup candidate

### research more

- 只过部分目标
- 或过线但实现依赖不清
- 或 improvement 不稳定

### reject

- 改善主要来自 narrative / wording
- 或 held-out tests 下没有可重复 signal

## Validator order

1. 先跑最小 synthetic harness
2. 再跑 ranking robustness audit：
   - `>= 5` random seeds
   - `>= 3` held-out splits
   - score-weight perturbation `±10%` 到 `±20%`
3. 再冻结 prototype design 与 replay validator
4. 最后才决定是否值得做 repo prototype

## Planned command

- `python3 scripts/codex/run_operational_self_model_evals.py`
- `python3 scripts/codex/run_operational_selection_robustness.py`
