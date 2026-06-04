# VirtualCatPSPC v0 Stage Card

## Frozen Boundary

- lane: `lab-only`
- runtime authority: `none`
- EgoOperator integration: `forbidden in v0`
- claim ceiling: `proto-self mechanism experiment only`
- mainline mutation: `forbidden`
- LLM action selection: `forbidden`

## Problem Reframe

The real target is not a virtual cat product, Joi-style companion chat, or a claim that the system is conscious. The target is a small replayable mechanism experiment for this chain:

`experience -> prediction error -> world/self model update -> future behavior change -> ablation-specific regression`

The useful evidence is causal and replayable behavior under controlled histories. Natural language output, personality prompts, and user interaction are out of scope for v0.

## One Hypothesis

If a gridworld cat learns predictive world and self consequences from unstable-object experience, then an MPC/CEM planner should become cautious around an unseen unstable tall object. Removing relevant memory, freezing the world model, freezing the self model, or disabling prediction-error learning should degrade the matching behavior or prediction metric.

## One Change Surface

Allowed surfaces:

- `docs/codex/tasks/virtual-cat-pspc-v0/`
- `labs/virtual_cat_pspc_v0/`
- `artifacts/virtual_cat_pspc_v0/`
- `artifacts/evidence_ledger/`
- governance scope needed for closeout

Forbidden surfaces:

- `EgoOperator/agent_base.py`
- `EgoOperator` runtime modes, gates, memory, trace, human-trial harness, and adapters
- Telegram, desktop, proactive channels, real user interaction, and production transport
- legacy EgoCore/OpenEmotion runtime activation

## Authority Source

This task package is the v0 lab authority. Repo-wide current phase, mainline owner, and evidence ceiling remain governed by `docs/PROGRAM_STATE_UNIFIED.yaml`.

The PSPC lab can create local deterministic evidence only. It cannot override the current EgoOperator human-operator trial gate or change the repo's active default lane.

## What Can Change

- A custom deterministic gridworld can be created for lab experiments.
- PyTorch world/self predictors can be trained from replayed experience.
- A homeostatic value function and MPC/CEM planner can score model rollouts.
- JSONL traces and Markdown reports can be generated for baseline and ablation evidence.
- Evidence ledger entries can record what the lab package proves and does not prove.

## What Cannot Be Proven

- stable real user benefit
- EgoOperator runtime efficacy
- live autonomy
- durable operator memory efficacy
- philosophical consciousness
- subjective experience
- production transport or proactive messaging safety

## Three-Level Verify

1. Contract verify: task docs explicitly freeze lab-only authority, forbidden integration, claim ceiling, and preregistered acceptance.
2. Local mechanism verify: unit tests prove gridworld feedback, model learning, planner use of world/self predictions, ablation regressions, and replay determinism.
3. Canonical evidence verify: reports under `artifacts/virtual_cat_pspc_v0/` include seeds, trace refs or hashes, what they prove, what they do not prove, failure meaning, and rollback notes.

## Rollback Plan

Remove the PSPC task directory, lab package, generated PSPC artifacts, PSPC evidence-ledger entry, and PSPC governance-scope additions. Because v0 has no runtime integration, rollback must not require EgoOperator code changes.

## Stop Conditions

Stop and roll back to a smaller gridworld-only mechanism if any of these become true:

- behavior is selected by object-name rules such as `if cup then avoid`
- behavior is mainly a scripted behavior tree
- memory is only RAG/log storage and does not affect future behavior
- prediction error does not update the world/self models
- the planner does not use world/self rollout predictions
- the value function collapses to a single scalar user-happiness reward
- an LLM selects actions or writes reasons before decisions

## Claim Ceiling

`VirtualCatPSPC v0 proto-self mechanism experiment local lab candidate`
