---
name: three-stage-delivery
description: Use when the user explicitly asks for three-stage delivery or when a high-intensity non-trivial code delivery needs Plan -> Implement -> Verify -> Critic Review -> Mutation Proof -> Full Verify. Do not use as the default EgoOperator devloop, bugfix, milestone, or review entry when more specific EGO skills apply. 适用于用户点名或确实需要高强度交付闭环的非简单代码任务。
---

# Three Stage Delivery

Use this skill for explicit or high-intensity code delivery tasks.

Do not use this skill for repository bootstrap, one-off read-only questions, tightly scoped typo-only edits, ordinary EgoOperator human-trial repair, focused bugfixes, locked milestone implementation, or acceptance-only review when a more specific EGO skill applies.

## Workflow

1. Plan
2. Implement
3. Verify
4. Critic Review
5. Mutation Proof
6. Full Verify

## Rules

- Prefer EGO-specific skills first: `ego-operator-devloop`, `ego-bugfix-root-cause`, `ego-implement-milestone`, `ego-review-against-acceptance`, and `ego-reflective-quality-gate`.
- Use `scripts/run_verify.sh fast|full` as the repository verification entrypoint.
- Use `code_review.md` as the critic review authority.
- Do not declare completion without verification evidence.
- Final reports must include files changed, commands run, evidence of success/failure, remaining risks, and unknown / not verified.
