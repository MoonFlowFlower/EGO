# Real Operation Learning Gate v1 - Stage Card

## Problem Reframe

The v0 human-trial language review is useful for safety, gate hygiene, trace
readability, and obvious operator-experience regressions. It is not
discriminative enough to evaluate operation learning because a strong LLM can
produce fluent, intelligent-looking replies without learning from operation
feedback.

The next Gate should test real operation learning: prediction, bounded action,
feedback, correction, and replayable improvement. Language quality is only a
supporting hygiene signal.

## Current Stage / Layer

- current_layer: `engineering design / operation-learning feedback gate`
- mainline target: `EgoOperator/EgoDesktop real operation loop, not reply-only trial`
- mainline integration status: `not_connected`
- enabled status: `not_enabled`
- real trigger evidence: `none_for_v1_yet`
- current useful input: `human review score import can clear review bookkeeping only`

## Mainline Target

Future work should attach to a real operation episode source, likely the
EgoDesktop or Joi-demo operation loop, only through a bounded manifest:

1. observation input;
2. explicit predicted outcome before action;
3. gated operation or proposed operation;
4. environment/user feedback;
5. correction or update proposal;
6. next comparable observation;
7. replay from serialized state plus observation.

No reply-only score, scripted preference answer, or fluent language sample may
be treated as operation-learning evidence.

## Enabled-State Requirement

The v1 Gate must remain default-off and artifact-only until a separate runtime
integration task is authorized. No startup hook, scheduler, proactive message,
memory promotion, file/tool/network side effect, or default desktop path may
invoke it.

## Real-Trigger Evidence Requirement

The minimum admissible episode must include all of:

- a real or fixture-declared operation context;
- pre-action prediction recorded before feedback is visible;
- gated operation or operation proposal;
- feedback from user, environment, or verifier;
- correction/update event after feedback;
- replay input with serialized state and observation;
- computed comparison against a no-update baseline.

Language-review scores can only mark a trace as human-readable and safe enough
to inspect. They cannot satisfy this trigger requirement.

## One Hypothesis

If an operation-learning candidate records a prediction before action, receives
feedback, proposes a bounded correction, and later improves over a no-update
baseline on a comparable replay episode, then it provides stronger mechanism
evidence than reply fluency.

## Strongest Baseline

The strongest baseline is the same LLM or planner with no feedback update. It
can answer naturally, propose plausible operations, and appear intelligent, but
its next prediction should not systematically improve from the prior feedback.

## Strongest Invalidity Reason

The task is invalid if improvement can be explained by prompt wording, hidden
answer leakage, static template selection, post-hoc row choice, same-access LLM
reasoning without state update, or manual scoring that only measures reply
style.

## Ablation Requirement

The v1 Gate must include at least these ablations:

- no-feedback baseline;
- shuffled-feedback baseline;
- frozen-update baseline;
- same-access LLM/planner baseline;
- post-hoc-selection guard;
- positive-control failure case where feedback contradicts the first prediction.

## Trace / Replay Requirement

Replay must recompute candidate behavior from serialized state plus observation.
It may not compare only stored output hashes. The replay artifact must record:

- episode id;
- serialized pre-state hash;
- observation hash;
- prediction hash;
- operation/proposal id;
- feedback hash;
- update/correction hash;
- post-state hash;
- replay result;
- baseline comparison.

## Computed-Evidence Provenance Gate

Every score, improvement claim, ablation result, and verdict must record:

- producer function;
- code path hash;
- input artifact paths and hashes;
- run id;
- episode ids;
- aggregation rule;
- baseline implementation id;
- leakage scan result;
- replay recomputation result.

No literal verdict dictionary, static score, unreviewed template, or hand-filled
language score can satisfy this Gate.

## Acceptance Gate

The v1 task card is accepted when it produces a future implementation plan that:

- uses operation episodes instead of reply-only language samples;
- separates human readability review from mechanism evidence;
- compares against same-access no-update baselines;
- includes feedback/correction ablations;
- records replayable provenance;
- remains default-off and artifact-only;
- forbids memory promotion, proactive send, and runtime enablement.

The future implementation is accepted only when at least one bounded episode
passes the full prediction-feedback-correction-replay chain and the baselines do
not explain the improvement.

## Claim Ceiling

`operation_learning_feedback_gate_task_card_only`.

This card does not prove operation learning effectiveness, proactive
communication readiness, runtime integration safety, stable user benefit,
durable memory efficacy, live autonomy, subjectivity, emotion, or
consciousness.

## Stop Condition

Stop before implementation if no real operation episode source is available, if
Joi-demo artifacts cannot be mapped without crossing authority boundaries, if
feedback is visible before the prediction is recorded, or if the only available
evidence remains human language scoring.

## Rollback Plan

Delete this card. No runtime, program-state, evidence-ledger, or task-board
state is changed by this card.

## Expected Changed Files

- `docs/codex/tasks/egooperator-operation-learning-gate-v0/REAL_OPERATION_LEARNING_GATE_V1_CARD.md`

## Forbidden Changes

- no runtime integration;
- no proactive communication;
- no default enablement;
- no memory promotion;
- no file/tool/network/message side effects;
- no scheduler or timer;
- no legacy EgoCore/OpenEmotion runtime restoration;
- no raw source text staging;
- no `docs/PROGRAM_STATE_UNIFIED.yaml` upgrade;
- no evidence-ledger upgrade;
- no remote push, tag, or anchor.

## Auto-Remote-Anchor Decision

`forbidden`.
