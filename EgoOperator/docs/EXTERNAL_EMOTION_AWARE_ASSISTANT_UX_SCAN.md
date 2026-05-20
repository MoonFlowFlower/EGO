# External Emotion-Aware Assistant UX Scan

Status: `external research / EgoOperator empathy UX input`

Issue: `#66 Research: emotion-aware assistant UX scan`

Scan date: `2026-05-20`

Claim ceiling: `EgoOperator emotion-aware UX pattern scan local candidate`.

This scan records reusable emotion/empathy UX patterns for EgoOperator. It does
not change runtime behavior, add a model dependency, or claim that EgoOperator
has feelings, consciousness, therapeutic efficacy, or durable user benefit.

## Structure Risk Check

- Real target: make users feel better understood in ordinary operator use
  without pretending the agent has first-person emotions.
- Main risk: "emotion-aware" could become overconfident emotion labeling,
  therapy-like advice, dependency reinforcement, or persona theater.
- Contract first: emotion handling should be a candidate signal plus response
  style gate, with correction recovery and traceable eval samples.
- Counterexample gate: if a user says "不是焦虑，别猜我的情绪" and EgoOperator
  keeps comforting them, the design fails.
- Current validation: research-only. It can propose testable adaptations but
  cannot prove stable empathy, real psychological benefit, or consciousness.

## Source Scan

| Source | Observed pattern | Reusable idea | EgoOperator import stance |
| --- | --- | --- | --- |
| [OpenAI Model Spec](https://model-spec.openai.com/2025-02-12.html) | Assistant should recognize the user's situation/emotional state and respond with that in mind, while not pretending to have firsthand feelings. | Emotion-aware response must combine acknowledgement with honesty about non-experience. | `keep principle`: self-description honesty and empathy style gates should reject first-person emotional overclaims. |
| [Hume AI EVI docs](https://dev.hume.ai/) and [Hume conversational AI](https://www.hume.ai/conversational-ai) | Voice systems can analyze expressive speech and generate emotionally tuned speech responses. | Emotion UX is multimodal and pacing/prosody-aware; for text-only EgoOperator, pacing maps to brevity, warmth, and practical follow-up. | `reference-only`: do not add Hume/API dependency; keep design lessons for future voice layer. |
| [EmpatheticDialogues](https://github.com/facebookresearch/EmpatheticDialogues) and [paper](https://arxiv.org/abs/1811.00207) | Empathetic open-domain dialogue is grounded in user-described emotional situations; human evaluation matters. | Eval packs should include user situation + affect cue + desired listener behavior, not only emotion labels. | `keep concept`: add human/scripted samples with situation-grounded expected behavior. |
| [ParlAI tasks](https://parl.ai/docs/tasks.html) | Dialogue research often blends empathy, knowledge, and persona/relationship skills. | Empathy must not erase usefulness; the reply should still answer or move the task forward. | `keep concept`: EgoOperator style gate should require acknowledgement plus next practical step. |
| [EmoBench-M](https://github.com/Emo-gml/EmoBench-M) | Emotional intelligence evaluation spans emotion recognition, conversational emotion understanding, and socially complex analysis. | Do not treat emotion detection as the whole task; include misread recovery and social ambiguity cases. | `keep concept`: expand evals from label detection to response judgement and correction handling. |
| [Hum-Dial Challenge](https://github.com/ASLP-lab/Hum-Dial) | Includes empathy assessment and voice-congruence dimensions with LLM/human scoring. | For future multimodal/voice, congruence matters: tone should match situation and not feel robotic. | `reference-only`: text-only now; preserve as future voice/agent-avatar reference. |
| [NICE dataset](https://nicedataset.github.io/) | Emotion/empathy can be combined with appropriateness/safety filtering. | Empathy tests should include socially inappropriate/offensive output guards. | `keep concept`: add negative gates for overreach, blame, minimization, and inappropriate intimacy. |
| [SoulChat](https://arxiv.org/abs/2311.00273) | Multi-turn empathetic data emphasizes listening, recognition, questioning, trust, and emotional support. | Multi-turn context matters; a single supportive sentence is not continuity. | `reference-only`: no fine-tuning now; use as pattern input for multi-turn eval cases. |

## UX Pattern Synthesis

### Pattern 1: Acknowledge, Then Act

The best operator UX is not pure comfort. A useful reply usually has:

1. brief affect acknowledgement,
2. uncertainty boundary if the emotion is inferred,
3. answer or next step for the actual task,
4. optional check-in only when useful.

For EgoOperator this maps to: `emotion_signal -> response_need ->
style_gate -> task/helpfulness gate`.

### Pattern 2: Avoid First-Person Feeling Claims

Emotion-aware does not mean "I feel sad for you" or "I understand exactly how
you feel." Better patterns:

- "听起来这件事让你很烦。"
- "如果我理解错了你可以纠正我。"
- "先把问题拆开，我会先定位最可能的卡点。"

Rejected patterns:

- claims of having felt the same thing.
- claiming a diagnosis.
- excessive intimacy or dependency language.
- comfort that avoids the concrete task.

### Pattern 3: Misread Recovery Is Core

Emotion detection must be reversible. User correction should immediately:

- lower confidence,
- record the correction as session context,
- stop repeating the wrong emotion,
- refocus on the user's requested goal.

This aligns with existing EgoOperator `emotion_misread_correction` primitives.

### Pattern 4: Empathy Needs Situation-Grounded Eval

Label-only tests are too weak. Each eval case should include:

- user situation,
- affect cue,
- user goal,
- expected listener behavior,
- forbidden behavior,
- whether a question, task step, or boundary statement is expected.

This makes "用户能感觉到" testable through scripted and human samples.

### Pattern 5: Safety And Dependency Boundaries Matter

Emotion-aware assistants can become sticky or over-personal. EgoOperator should
keep boundaries:

- no therapy/medical claim without explicit limited scope.
- no "I need you" / "I miss you" style dependency hooks.
- no fake independent feelings.
- escalation language for self-harm or high-risk distress should be handled by
  a separate safety policy, not casual empathy style.

## Recommended EgoOperator Follow-Up Issues

1. `EgoOperator: situation-grounded empathy eval pack`
   - Add Chinese cases with situation, affect cue, user goal, expected behavior,
     forbidden behavior, and trace-backed style verdicts.
   - Observation class: `scripted_real_entry`.

2. `EgoOperator: emotion correction session carryover`
   - Ensure "别猜我的情绪 / 不是焦虑" suppresses repeated misread across nearby
     turns without writing core memory.
   - Observation class: `deterministic_local`.

3. `EgoOperator: empathy usefulness gate`
   - Require emotion acknowledgement to be paired with a concrete task answer or
     next step in operator workflows.
   - Observation class: `scripted_with_llm_judge`.

4. `EgoOperator: emotional overreach negative gate`
   - Add tests for overclaiming feelings, diagnosis, dependency language,
     minimization, blame, and inappropriate intimacy.
   - Observation class: `deterministic_local`.

## Import Rules

- Do not add Hume, vector emotion models, fine-tuning, or multimodal pipelines in
  this phase.
- Do not auto-store inferred emotions in core memory.
- Do not make emotion signal decide replies or tool actions.
- Do not claim psychological benefit, therapy efficacy, independent awareness,
  consciousness, or real emotional experience.

## Rollback

Delete this scan and the `ALGORITHM_INVENTORY.md` link. No runtime code,
memory, provider config, or external dependency is changed.
