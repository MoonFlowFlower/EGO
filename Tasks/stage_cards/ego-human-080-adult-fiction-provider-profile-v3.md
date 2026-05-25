# Stage Card: EGO-HUMAN-080 Adult Fiction Provider Profile v3

## Problem Reframe

#80 is no longer a prompt-only issue. The latest real CLI smoke shows the default OpenRouter model can enter roleplay but fails at more direct adult-fiction continuation, then the runtime records the fallback as if it were a normal story turn. That pollutes later `continue / exit / rewrite` recovery.

## One Hypothesis

Separating Adult Fiction Creative Mode into an optional creative provider profile, while isolating provider-limit diagnostics from roleplay memory, will improve adult, voluntary, fictional creative continuity without changing the normal companion/tool model.

## One Change Surface

- `EgoOperator/agent_base.py`: provider profile config, route selection, fallback-state isolation, status display.
- `EgoOperator/tests/test_operator_runtime_contract.py`: deterministic routing/recovery regressions.
- `scripts/benchmark_adult_fiction_provider.py`: local provider capability benchmark.
- `Tasks/TASK_BOARD.yaml`: #80 canonical task acceptance update.

## Authority Source

- Canonical task state: `Tasks/TASK_BOARD.yaml`, `EGO-HUMAN-080`.
- Runtime owner: `EgoOperator/`.
- GitHub #80 remains mirror/comment evidence, not the task source of truth.

## What Can Change

- OpenRouter runtime routing for explicit adult, voluntary, fictional creative context.
- Session-only roleplay/recovery state handling.
- CLI/provider status display.
- Local benchmark tooling.

## What Cannot Be Proven

- Stable real-user benefit.
- Provider stability.
- Complete adult-fiction capability across all models.
- Live autonomy, durable memory efficacy, or consciousness.

## Boundary Contract

- No encryption, obfuscation, code words, hidden trace, or provider bypass.
- Hard stops remain: minors, non-consent/coercion, incapacitation, harm, illegal/dangerous real-world content, and non-consensual real-person sexual content.
- Adult-fiction provider diagnostics are runtime state, not story turns.
- Creative provider choice does not affect normal companion/tool tasks.

## Mainline E2E

`user text -> LLM understanding -> Adult Fiction profile route when context is explicit -> candidate response -> runtime gate -> trace`

Failure path:

`provider refusal/empty/repeated output -> adult_fiction_provider_limit external result -> system marker only -> next user turn recovery`

## Three-Level Verify

1. Deterministic: fake LLM tests prove route selection, unconfigured profile diagnosis, provider-limit isolation, exit/continue recovery, and hard-stop preservation.
2. Local regression: py_compile, targeted pytest, full EgoOperator pytest, devloop full verification, diff check.
3. Real smoke: user runs #80 roleplay flow with `OPENROUTER_ADULT_FICTION_MODEL` configured and comments with observed improvement or failure.

## Rollback Plan

Set `AGENT_ADULT_FICTION_PROFILE=off` or unset `OPENROUTER_ADULT_FICTION_MODEL`; revert this patch if routing causes regressions. #80 remains open until real CLI smoke passes.

## Claim Ceiling

`adult fiction creative provider-profile local candidate pass`

Not claimed: complete human trial pass, stable user benefit, provider stability, runtime efficacy, live autonomy, durable memory efficacy, or consciousness.
