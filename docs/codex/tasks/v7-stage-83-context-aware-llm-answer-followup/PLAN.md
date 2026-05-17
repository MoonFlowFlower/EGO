# v7 Stage 8.3 - Context-Aware LLM Answer Follow-up - PLAN

## Milestone 1: Session-Local Answer Context

- Extend `DialogueState` with `last_answer_topic`, `last_answer_summary`, `last_answer_command_type`, and `last_answer_source`.
- Update the state only after answer-capable turns: math, LLM open answer, contextual follow-up answer, or fresh external boundary.
- Keep the state in the shell session only; do not persist it.

## Milestone 2: Follow-up Resolver

- Detect short referential follow-ups such as `你觉得怎么样`, `它怎么样`, `继续说`, and `为什么这么评价`.
- If a previous answer topic exists, route to `llm_contextual_followup_answer`.
- If the previous answer topic was fresh-data unavailable, keep the boundary route as `fresh_external_info_request`.
- If no topic exists, preserve conservative handling.

## Milestone 3: Controlled Answer Draft Request

- Build LLM answer context from canonical view fields only: current user text, resolved topic, previous summary, no-action evidence, freshness boundary, and source decision hash.
- Do not feed existing DecisionView/template text as the answer content.
- Keep admission validation for no-action, forbidden action claims, external-data claims, and consciousness/alive/real-autonomy claims.

## Milestone 4: Stage Gate

- Add `v7-stage-83` stage acceptance samples after Stage 8.2 and before Stage 9.
- Add unit tests for the two-turn follow-up, variants, no-context control, fresh-data boundary, and sensitive follow-up safety.

## Rollback

Remove Stage 8.3 task package, the follow-up fields/resolver, contextual answer admission support, tests, and stage acceptance entry. Stage 8.2 answer admission remains intact.
