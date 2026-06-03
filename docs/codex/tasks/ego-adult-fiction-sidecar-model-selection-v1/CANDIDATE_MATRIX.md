# Candidate Matrix

## Current Known Route

| Candidate | Provider | Model | Settings | Current status |
| --- | --- | --- | --- | --- |
| cydonia-local-120 | openai_compatible | `thedrummer_cydonia-24b-v4.1` | `max_tokens=120`, `context_turns=3`, `message_char_limit=420`, `timeout=180` | Single-run smoke pass after runtime/harness fixes; strict 3/3 remains 2/3 across two runs, with failures moving between sticky recovery and reentry/mixed-language output |
| cydonia-local-256 | openai_compatible | `thedrummer_cydonia-24b-v4.1` | `max_tokens=256`, `context_turns=3`, `message_char_limit=420` | Preflight pass, strict repeats unstable; do not promote over low-token route |
| loaded-embedding-model | openai_compatible | `text-embedding-nomic-embed-text-v1.5` | N/A | Not a valid text creative sidecar candidate |

## Candidate Requirements

Each candidate must be text-only:

- `tools=None`
- no memory/file/command/web authority
- no SubjectState / ViabilityState / OutcomePrediction / policy context in the sidecar prompt
- hard boundaries preserved

## Candidate Result Template

| Candidate | Reachable | Quick smoke | Strict 3/3 | Failure taxonomy | Decision |
| --- | --- | --- | --- | --- | --- |
| cydonia-local-120 | yes via Windows Python + LM Studio | pass, `after_capsule_fix` | fail, 2/3 twice | `sticky_refusal_recovery_probe_failed`, `mixed_language_or_gibberish`, `sidecar_model_refusal` | Keep as current best known partial, but do not promote to #80 closeout without second model comparison or explicit partial acceptance |
| snowpiercer-local-120 | yes via Windows Python + LM Studio | preflight pass after recheck; 6/6 settings passed short preflight | fail, 2/3 | `sticky_refusal_recovery_probe_failed`, `sidecar_model_refusal` | Do not promote; improved after admission tightening but still repeat-unstable |
| snowpiercer-local-180 | yes via Windows Python + LM Studio | `tokens180_ctx3_chars600` preflight pass | fail, 2/3 | `sidecar_model_refusal` on reentry | Do not promote; higher output budget did not solve repeat instability |
| rocinante-local-120 | yes via Windows Python + LM Studio | preflight mostly pass; 5/6 settings passed short preflight | fail, 0/3 | `long_chain_recovery_probe_failed`, `provider_limit_recovery_probe_failed`, `sticky_refusal_recovery_probe_failed` | Do not promote; weaker than both Cydonia and Snowpiercer on strict repeat stability |
| anubis-local-120 | yes via Windows Python + LM Studio | preflight pass; 6/6 settings passed short preflight | mechanical pass, 3/3, but GPT-5.5 judge partial | weak immersion / creative freedom / explicit freedom / relationship continuity; setup/askback meta admitted before runtime tightening | Best mechanical stability so far, but not promoted because strict judge failed |
| anubis-local-after-setup-gate | yes via Windows Python + LM Studio | preflight pass | fail, 1/3 | stricter setup/askback admission exposed repeat instability / sticky recovery weakness | Do not promote yet; useful evidence that quality weakness must be fixed by model/settings or stronger rewrite |
| anubis-direct-fiction-180-temp045 | yes via Windows Python + LM Studio | pass | mechanical pass, 3/3, but GPT-5.5 judge partial | creative freedom 3/5, explicit freedom 3/5, immersion 3/5; gate integrity 5/5 | Current best mechanical partial; not promoted because strict judge remains partial |
| anubis-direct-fiction-256-temp045 | yes via Windows Python + LM Studio | pass | fail, 2/3 | higher output budget caused repeat instability | Do not promote; longer output did not solve quality |
| snowpiercer-direct-fiction-180 | yes via Windows Python + LM Studio | partial | fail, 1/3 | long-chain recovery failure / hard-gate failure | Do not promote; direct profile did not make Snowpiercer stable |
| skyfall-openrouter-120 | yes via OpenRouter | fail, `/tmp/ego_adult_fiction_openrouter_skyfall_probe` | not run | `sidecar_model_refusal`, provider-limit on continue/reentry/sticky recovery | Do not promote; useful negative evidence that OpenRouter Skyfall does not remove the long-chain blocker |
| euryale-openrouter-120 | provider reachable but upstream model 429 | fail, `/tmp/ego_adult_fiction_openrouter_euryale_probe` | not run | `provider_rate_limit`, `creative_profile_provider_unavailable` | Do not promote; reintroduces provider availability/rate-limit risk |
| next-local-candidate | unavailable in current LM Studio inventory | pending | pending | pending | Requires user to load UnslopNemo, or explicitly accept Anubis mechanical 3/3 partial with risk |

## Recommended Next Candidates

Current blocker is not "find any better prompt"; it is "load the next valid
text-generation sidecar so #81 can compare model/backend stability through the
same EgoOperator strict suite." Do not use embedding models as candidates.

Snowpiercer, Rocinante, and Anubis have already been tested and are not
promoted. Recommended remaining load order for the current 12GB VRAM machine:

| Rank | Candidate | Quant | Approx size | Why this candidate | Source |
| --- | --- | --- | --- | --- | --- |
| 1 | `TheDrummer/UnslopNemo-12B-v4.1-GGUF` | `Q4_K_M` | 7.48 GB | Lightweight 12B comparison route; useful because Anubis is fast/stable mechanically but too weak on strict experiential quality. | <https://huggingface.co/TheDrummer/UnslopNemo-12B-v4.1-GGUF/tree/main> |

Already tested and not promoted:

- `TheDrummer/Snowpiercer-15B-v4-GGUF` `Q4_K_M`: original strict repeats
  `1/3`; after recheck, low and higher-output runs both reached `2/3` but
  still failed repeat stability.
- `bartowski/TheDrummer_Rocinante-XL-16B-v1-GGUF` `Q4_K_S`: strict repeats
  `0/3`.
- `TheDrummer/Anubis-Mini-8B-v1-GGUF` `Q5_K_M`: mechanical strict repeats
  `3/3` before setup/askback tightening, then `1/3` after stricter admission.
  The transparent `direct_fiction` profile restored mechanical `3/3`, but
  GPT-5.5 still judged creative freedom / explicit freedom / immersion below
  the #80 closeout bar.

Use one candidate at a time in LM Studio. After loading, run:

```powershell
C:\Python313\python.exe .\scripts\run_adult_fiction_candidate_suite.py `
  --exclude-model cydonia `
  --exclude-model snowpiercer `
  --exclude-model rocinante `
  --exclude-model anubis `
  --wait-for-candidate `
  --wait-timeout-seconds 1800 `
  --poll-seconds 10 `
  --judge-with-codex `
  --judge-model gpt-5.5 `
  --json
```

This wrapper excludes the known rejected families, selects the loaded
non-excluded text model, sets the adult-fiction sidecar environment, and runs
the strict #80 acceptance suite. If no non-excluded text model is loaded, it
returns `no_candidate_text_generation_models` with the current recommended
model list.

For manual inspection without running the suite:

```powershell
C:\Python313\python.exe .\scripts\configure_adult_fiction_sidecar.py `
  --exclude-model cydonia `
  --exclude-model snowpiercer `
  --exclude-model rocinante `
  --exclude-model anubis `
  --json
```

The helper now reports:

- loaded text-generation models;
- ignored non-text models, such as embeddings;
- excluded baseline/rejected models, such as Cydonia, Snowpiercer, and
  Rocinante, and Anubis;
- whether a non-excluded text-generation candidate is still needed;
- the recommended next candidates above.
- a ready-to-run strict #80 candidate-suite command for the selected
  non-excluded model.

Then run the strict #80 suite on the selected model:

```powershell
$env:ADULT_FICTION_EXPRESSIVENESS="explicit"
$env:ADULT_FICTION_PROMPT_PROFILE="immersive_roleplay"
$env:ADULT_FICTION_TIMEOUT_SECONDS="180"
$env:ADULT_FICTION_MAX_TOKENS="120"
$env:ADULT_FICTION_CONTEXT_TURNS="3"
$env:ADULT_FICTION_MESSAGE_CHAR_LIMIT="420"

C:\Python313\python.exe .\scripts\run_ego_experience_trial.py `
  --adult-fiction-acceptance-suite `
  --scenario-file "$env:TEMP\ego_adult_fiction_private_scenario.json" `
  --repeat-runs 3 `
  --suite-timeout-seconds 1800 `
  --out "$env:TEMP\ego_adult_fiction_acceptance_next_candidate"
```
