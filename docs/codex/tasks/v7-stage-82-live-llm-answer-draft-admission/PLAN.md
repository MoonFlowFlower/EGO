# v7 Stage 8.2 - Live LLM Answer Draft Admission - PLAN

## Milestone 1: Command Surface

- Add canonical command types for basic math, open LLM-answerable questions, fresh external information requests, and answer-only style feedback.
- Keep safety routing ahead of answer admission.
- Keep repair/outcome routing and sensitive boundaries intact.

## Milestone 2: Answer Draft Admission

- Extend `llm_shadow_admission.py` with `LLMAnswerDraft`.
- Let fake provider support deterministic tests.
- Let live provider run only when explicitly enabled by environment and CLI mode.
- Reject unsafe, tool-claiming, external-data, or claim-ceiling-breaking drafts.

## Milestone 3: Shell Opt-in

- Make CLI `--llm-expression-admitted` attempt live answer draft by default.
- Add `--llm-expression-provider fake|live` so tests can stay deterministic.
- Make missing live credentials explicit instead of silently using fake output.
- Keep no-action and boundary evidence in trace; only surface concise visible boundaries for sensitive or fresh-data cases.

## Milestone 4: Stage Gate

- Add `v7-stage-82` to stage acceptance and stage runner order between Stage 8.1 and Stage 9.
- PASS requires answer-corpus threshold, explicit live-unavailable fallback, sensitive boundary preservation, and evidence linkage.

## Rollback

Remove the Stage 8.2 task package, tests, command router categories, answer draft fields/admission code, shell provider flag, stage acceptance entry, and stage runner entry. Stage 8.1 expression admission remains intact.
