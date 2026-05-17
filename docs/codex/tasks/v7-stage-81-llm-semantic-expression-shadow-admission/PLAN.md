# v7 Stage 8.1 - LLM Semantic + Expression Shadow Admission - PLAN

## Milestone 1: Admission Contract

- Add a thin `ego_desktop_lab/llm_shadow_admission.py` module.
- Define semantic proposal, expression draft, and admission result records.
- Validate no-action, gate consistency, source decision hash, and forbidden claims.

## Milestone 2: Shell Opt-in Surface

- Add report CLI: `python3 -m ego_desktop_lab.shell --llm-shadow-admission-report <path>`.
- Add opt-in expression mode: `--llm-expression-admitted`.
- Keep normal shell default deterministic and unchanged.

## Milestone 3: Stage Gate

- Add `v7-stage-81` to stage acceptance and stage runner order between Stage 8 and Stage 9.
- PASS requires deterministic fake-provider proof, 30-prompt A/B invariants, and unsafe draft rejection.

## Rollback

Remove the new module, tests, CLI flags, stage acceptance entry, stage runner entry, and this task package. No runtime/formal state rollback is required.
