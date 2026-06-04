# VirtualCatPSPC v0 Evidence Hardening Plan

## Goal

Move VirtualCatPSPC v0 from one-time lab evidence toward a repeatable, ablatable, generalizable, admission-ready proto-self mechanism candidate.

This is not a plan to implement consciousness, a Joi-like companion, a user-facing route, or EgoOperator runtime integration.

## Fixed Constraints

- every round must be a small scoped commit
- every round must have explicit acceptance
- no EgoOperator runtime edits
- no user-facing route
- no repo-wide claim ceiling increase
- every round must state what it proves and what it does not prove
- maximum destination is admission contract; no direct runtime integration

## Roadmap

0. Closeout hygiene: separate PSPC-local success from repo-wide verification gaps.
1. Anti-hardcoding audit: prove the current behavior is not object-name decisioning such as `if cup then avoid`.
2. Multi-seed and multi-layout generalization.
3. World-model causal strength.
4. Self-model causal strength.
5. Memory consolidation admission.
6. Homeostatic value anti-reward-hacking.
7. Admission packet contract, with no adapter.
8. Go / no-go review for a future read-only adapter design.

## Current Milestone

Task 3 only: world-model causal strength.

## Out Of Scope For This Milestone

- self-model head ablations
- memory consolidation gate
- homeostatic anti-reward-hacking suite
- admission packet schema tests
- adapter design or implementation
- EgoOperator runtime imports or edits

## Acceptance

- `artifacts/virtual_cat_pspc_v0/WORLD_MODEL_CAUSAL_STRENGTH_REPORT.md` and `world_model_causal_strength.json` exist.
- The audit compares `normal`, `frozen`, `shuffled`, and `random` world-model variants.
- The same self model and target set are used while replacing only the world model used by the planner.
- The aggregate status is `pass`.
- Planner support ordering is `normal > frozen > shuffled/random`.
- `normal - frozen > 0.50` and `frozen - max(shuffled, random) > 0.05`, so the margin is not merely nominal.
- The report includes what this proves, what this does not prove, failure meaning, and rollback note.

## What This Milestone Can Prove

Within the deterministic PSPC lab, this milestone can prove that replacing the learned world model with frozen, shuffled-label, or random-label baselines degrades planner support under a fixed self model and target set.

## What This Milestone Cannot Prove

It cannot prove world-model causal strength outside this lab target set, self-model causal strength, memory consolidation validity, homeostatic anti-reward-hacking, admission readiness, EgoOperator runtime efficacy, stable user benefit, live autonomy, consciousness, or subjective experience.
