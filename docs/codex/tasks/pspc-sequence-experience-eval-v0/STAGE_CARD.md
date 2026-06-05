# PSPC Sequence Experience Eval v0

- lane: lab-only / shadow-only
- runtime authority: none
- EgoOperator integration: forbidden
- mainline mutation: forbidden
- LLM action selection: forbidden
- claim ceiling: lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only
- status: implemented local eval package

## Problem Reframe

The useful question is not whether a virtual cat can produce cute replies. The useful question is whether a controlled history of interactions can change a bounded proxy state, and whether that changed state produces a different audit-only observation for the same neutral trigger.

This stage implements a sequence eval for:

`history inputs -> proxy relationship/self state deltas -> same trigger behavior-profile divergence`

## One Hypothesis

If the PSPC shadow layer has a useful sequence accumulator, then gentle interaction, frequent interruption, and late-night care histories should lead to different trigger observations for `我回来了。`.

Expected profiles:

- gentle interaction: approach/trust profile
- frequent interruption: avoidance/boundary profile
- late-night care: care/low-interrupt profile
- no history: neutral profile
- shuffled history: mixed profile that is not identical to clean sequence profiles

## One Change Surface

Allowed:

- `scripts/run_pspc_sequence_experience_eval.py`
- `scripts/pspc_shadow_contracts.py`
- `tests/test_pspc_sequence_experience_eval.py`
- `docs/codex/tasks/pspc-sequence-experience-eval-v0/`
- `artifacts/pspc_sequence_experience_eval_v0/`
- necessary task-board, project-contract, program-state, evidence-ledger, and generated-view entries

Forbidden:

- EgoOperator runtime import or registration
- EgoOperator main loop, gate, approval, memory, human-trial harness, transport, or proactive channel changes
- user-visible PSPC reply generation
- mainline memory writes
- runtime gate invocation
- PSPC planner/training/model execution
- `enabled=true` or `mainline_connected=true`
- claim-ceiling upgrade

## Three-Level Verify

1. Contract: dataset shape, control groups, runtime-authority field absence, disabled/mainline-disconnected flags.
2. Behavior proxy: three clean histories diverge on trigger profile and controls remain bounded.
3. Repo gate: governance checks, lint, closeout-check, scoped commit, push.

## Rollback

Delete the sequence eval runner, tests, task docs, generated artifacts, and matching task-board/program-state/evidence-ledger/generated-view entries. Keep prior PSPC shadow/manual harness evidence intact.

## What This Can Prove

This can prove a lab/shadow sequence accumulator can turn controlled history inputs into proxy state deltas and different audit-only trigger profiles without runtime side effects.

## What This Cannot Prove

It does not prove PSPC is integrated into EgoOperator, adapter readiness, runtime integration safety, real user benefit, durable memory efficacy, live autonomy, consciousness, subjective experience, or that proxy variables are real emotions.
