# PSPC Sequence Experience Eval v0.1

- lane: lab-only / shadow-only
- runtime authority: none
- EgoOperator integration: forbidden
- mainline mutation: forbidden
- LLM action selection: forbidden
- claim ceiling: lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only
- status: implemented robustness and counterfactual review

## Problem Reframe

v0 proved only that clean history groups can produce different proxy trigger profiles. The next useful question is whether that result is robust enough to survive obvious anti-shortcut checks before any closer runtime-adjacent discussion.

This stage tests:

- trigger paraphrase robustness
- lexical shortcut removal
- counterfactual deletion
- mixed-history resolution
- manual review readiness

## One Hypothesis

If the sequence eval is more than a clean-group demo, then dominant trigger tendencies should remain stable across trigger paraphrases, survive removal of obvious literal keywords, shift more when high-salience history is deleted than when low-salience history is deleted, and expose mixed-history conflict instead of collapsing to neutral.

## One Change Surface

Allowed:

- `scripts/run_pspc_sequence_experience_eval_v0_1.py`
- `tests/test_pspc_sequence_experience_eval_v0_1.py`
- `docs/codex/tasks/pspc-sequence-experience-eval-v0-1/`
- `artifacts/pspc_sequence_experience_eval_v0_1/`
- necessary task-board, project-contract, program-state, evidence-ledger, and generated-view entries

Forbidden:

- EgoOperator runtime import or registration
- EgoOperator main loop, gate, approval, memory, human-trial harness, transport, or proactive channel changes
- adapter creation
- user-visible PSPC reply generation
- mainline memory writes
- runtime gate invocation
- PSPC planner/training/model execution
- `enabled=true` or `mainline_connected=true`
- claim-ceiling upgrade

## Three-Level Verify

1. Unit/contract: v0.1 test suite validates trigger paraphrases, keyword removal, deletion, mixed-history, manual packet, no runtime-authority fields.
2. Artifact: runner writes report, JSON artifact, and manual review packet under `artifacts/pspc_sequence_experience_eval_v0_1/`.
3. Repo gate: program-state integrity, route convergence, mainline clarity, lint, session guard tests, diff check, closeout-check, scoped commit, push.

## Rollback

Delete v0.1 docs, runner, tests, artifacts, and matching governance/generated-view entries. Keep v0 sequence eval and manual shadow review state intact.

## What This Can Prove

This can prove the quote-sequence shadow eval is less brittle than the clean v0 grouping alone and is ready for human manual review packet inspection.

## What This Cannot Prove

It does not prove PSPC is integrated into EgoOperator, runtime integration safety, adapter readiness, model learning, world/self model causality, planner causality, durable memory efficacy, real user benefit, live autonomy, consciousness, subjective experience, or real emotion. It also does not fully remove fixture-label shortcut risk.
