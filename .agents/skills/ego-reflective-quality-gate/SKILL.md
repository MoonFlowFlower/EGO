---
name: "ego-reflective-quality-gate"
description: "Use for high-risk EGO/Codex planning, architecture, agent-design, implementation-order, memory/permission/tool/state decisions, repeated failures, or when the user points out that Codex missed a better framing. This skill adds a risk-graded reflective gate: compare the local best path against a better reframing, identify the strongest counterexample, define an evidence gate, and decide whether manual critic review or an allowed reviewer/subagent pass is required."
---

# Ego Reflective Quality Gate

Use this skill to reduce missed better framings. It does not replace task specs, GitHub Issues, `ego-operator-devloop`, `three-stage-delivery`, or `ego-review-against-acceptance`.

## Risk Levels

- `L0`: small deterministic edit or factual answer. Do a quick internal self-check only.
- `L1`: ordinary implementation or planning. State the real goal, one main path, one better-framing check, and the acceptance signal.
- `L2`: architecture, agent design, memory, permission, tool, state, or implementation-order decision. Explicitly include structure-risk self-check, counterexample gate, rollback, and claim ceiling.
- `L3`: repeated failure, user-corrected framing, mainline/state/evidence mutation, or high-blast-radius change. Require critic review before closeout; use an allowed reviewer/subagent only when the active environment and user authorization permit it, otherwise run a manual findings-first critic pass.

## Workflow

1. Restate the real target, not just the literal request.
2. Compare two paths:
   - current-path best solution
   - better framing outside the current path
3. Name the strongest counterexample that would prove the chosen path wrong.
4. Pick exactly one main path and one fallback.
5. Define the verification gate and what the result cannot prove.
6. For implementation tasks, add or update a deterministic regression before or alongside the fix when practical.
7. Before closeout, run a critic pass focused on wrong abstraction layer, second truth source, missing mainline proof, over-claiming, and scope noise.

## Pairing

- Pair with `ego-operator-devloop` for EgoOperator human-trial logs, GitHub comments, file/web_fetch/approval/memory gate regressions, and Project closeout.
- Pair with `ego-bugfix-root-cause` for concrete runtime bugs or failing tests.
- Pair with `ego-implement-milestone` when the user supplies a locked implementation plan.
- Pair with `ego-review-against-acceptance` for completion claims, release gates, or review findings.

## Claim Boundary

This gate can improve the chance of finding a better path. It cannot guarantee global optimality, real-provider success, stable user benefit, runtime efficacy, durable memory efficacy, live autonomy, or consciousness.
