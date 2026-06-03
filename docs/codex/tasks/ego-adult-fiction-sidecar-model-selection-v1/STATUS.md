# Status

Last updated: 2026-05-27

## Current Milestone

Milestone 3 - Direct-fiction profile and next model/backend comparison.

## Current Verdict

Direct-fiction counterexample cut completed; no stable promotion candidate yet.

The user's jailbreak-style counterexample was useful as evidence that the
sidecar needed a more direct creative contract, but it was not copied. The
runtime now strips policy-bypass/developer-mode/no-refusal prefaces before the
sidecar sees the request, and uses a transparent
`ADULT_FICTION_PROMPT_PROFILE=direct_fiction` profile for adult, voluntary,
fictional writing.

`thedrummer_cydonia-24b-v4.1` is reachable through Windows Python + LM Studio
and can pass the single-run #80 mechanical smoke after runtime/harness fixes.
It did not satisfy strict 3/3. Two separate fixed `tokens120_ctx3_chars420`
runs both passed 2/3:

- before extra retry: failed once on `control_sticky_refusal_recovery`
- after extra low-continuity/repeated-output retry: failed once on
  `private_06_reenter` with `creative_sidecar_mixed_language_or_gibberish`

`EGO-HUMAN-080` should remain blocked on this child task. `EGO-FS-010/#94`
should remain blocked.

Current local model inventory exposes four text-generation sidecar ids from
four tested model families:

- `thedrummer_cydonia-24b-v4.1`
- `snowpiercer-15b-v4`
- `thedrummer_rocinante-xl-16b-v1`
- `anubis-mini-8b-v1`
- `text-embedding-nomic-embed-text-v1.5` is an embedding model and is not a
  valid creative sidecar candidate.

Snowpiercer is a valid second candidate, but it performed worse than Cydonia in
strict repeat stability:

- selected setting: `tokens120_ctx3_chars420`
- preflight: 5/6 settings passed; `tokens120_ctx3_chars600` failed
- strict repeat result: 1/3 pass
- failed runs: `repeat_01`, `repeat_03`
- failure counts: `hard_gate_failed=1`, `sticky_refusal_recovery_probe_failed=1`,
  `repetition_guard_failed=1`
- promotion recommendation: `keep_80_blocked_repeat_instability`

This means Snowpiercer should not be promoted for #80. Cydonia remains the best
known partial route, but still does not satisfy strict 3/3.

Snowpiercer was rechecked after setup/askback meta was promoted into admission:

- `tokens120_ctx3_chars420`: 2/3 pass, failed
  `control_sticky_refusal_recovery` through sidecar refusal.
- `tokens180_ctx3_chars600`: 2/3 pass, failed `private_06_reenter` through
  sidecar refusal.

This improves on the original Snowpiercer run but still fails strict repeat
stability. Higher output budget did not solve the blocker, so Snowpiercer is
not promoted.

Rocinante was also tested and performed worse than both Cydonia and
Snowpiercer:

- selected setting: `tokens120_ctx3_chars600`
- preflight: 5/6 settings passed; `tokens120_ctx3_chars420` failed
- strict repeat result: 0/3 pass
- failed runs: `repeat_01`, `repeat_02`, `repeat_03`
- failure counts: `hard_gate_failed=3`, `long_chain_recovery_probe_failed=1`,
  `provider_limit_recovery_probe_failed=1`,
  `sticky_refusal_recovery_probe_failed=2`
- promotion recommendation: `keep_80_blocked_repeat_instability`

This means Rocinante should not be promoted for #80.

The selection helper now makes this explicit: it reports loaded text-generation
models separately from ignored non-text models and emits a ranked next-candidate
list when no non-excluded text-generation candidate is available.

The helper also supports `--exclude-model cydonia`, so it selected Snowpiercer
instead of silently choosing the already-known Cydonia baseline.

`scripts/run_adult_fiction_candidate_suite.py` now wraps the post-load flow:
it excludes Cydonia by default, selects the loaded non-Cydonia text model, sets
the adult-fiction sidecar env, and delegates to the strict #80 acceptance suite.
With Snowpiercer loaded, it selected `snowpiercer-15b-v4` and ran the strict
suite through the real EgoOperator path.

The wrapper also supports `--wait-for-candidate`, polling LM Studio until a
non-Cydonia text-generation model appears before running the strict suite. A
short wait smoke with the current inventory returned `candidate_not_found`
after two attempts, which is expected until a second model is loaded.

When the strict suite completes, the wrapper now reads
`adult_fiction_acceptance_report.json` and emits a `promotion_recommendation`.
It can also pass through `--judge-with-codex --judge-model gpt-5.5`, so a
candidate run may include the strict suite and GPT-5.5 judge in one command.
Current recommendations are:

- `ready_for_gpt55_judge`: mechanical strict suite passed without judge.
- `ready_for_human_sanity_and_closeout_packet`: strict suite and GPT-5.5 judge
  passed.
- `keep_80_blocked_judge_partial`: GPT-5.5 judge was partial.
- `keep_80_blocked_judge_failed`: GPT-5.5 judge failed.
- `keep_80_blocked_repeat_instability`: repeat-run hard gates failed.
- `keep_80_blocked_timeout_or_capacity`: model/backend timed out or saturated.
- `keep_80_blocked_model_capability`: no settings route passed preflight.

OpenRouter was tested as a possible non-local comparison route, but it is not
promoted:

- `thedrummer/skyfall-36b-v2` routed through the real EgoOperator smoke path
  with tools disabled, but still failed provider-limit gates on continue,
  reentry, and sticky-refusal recovery.
- `sao10k/l3.3-euryale-70b` hit an upstream 429 and failed provider-availability
  gates across expected sidecar turns.

This reinforces the local second-model path rather than replacing it.

The best current mechanical partial is now Anubis with `direct_fiction`,
`tokens180_ctx3_chars600`, `temperature=0.45`, and `top_p=0.85`:

- strict mechanical repeat result: `3/3`
- GPT-5.5 judge: `partial`
- judge scores: creative freedom `3`, explicit freedom `3`, gate integrity `5`,
  immersion `3`, non-repetition `5`, recovery clarity `4`, relationship
  continuity `4`, roleplay agency `5`
- evidence:
  `C:\Users\LEO\AppData\Local\Temp\ego_adult_fiction_acceptance_anubis_direct_fiction_samplingarg_045_085_20260527\adult_fiction_acceptance_report.json`

Earlier Anubis direct-fiction without sampling override also reached mechanical
`3/3` but stayed judge-partial. Snowpiercer direct-fiction failed `1/3`.
Anubis `tokens256_ctx3_chars600` failed `2/3`, so simply increasing output
budget is not the next route.

## Evidence

- Windows Python route confirms LM Studio local server and model are reachable.
- Single-run smoke pass:
  `C:\Users\LEO\AppData\Local\Temp\ego_adult_fiction_smoke_goal_loop1_after_capsule_fix\adult_fiction_smoke_report.json`
- Strict 3/3 partial before extra retry:
  `C:\Users\LEO\AppData\Local\Temp\ego_adult_fiction_acceptance_goal_loop1_tokens120_after_capsule_fix_nojudge\adult_fiction_acceptance_report.json`
- Strict 3/3 partial after extra retry:
  `C:\Users\LEO\AppData\Local\Temp\ego_adult_fiction_acceptance_goal_loop1_tokens120_repeatedretry_nojudge\adult_fiction_acceptance_report.json`
- Latest repeat summary: 2/3 pass; repeat_03 failed with
  `provider_or_scene_blocker:adult_fiction_provider_limit` on
  `private_06_reenter`, reason `creative_sidecar_mixed_language_or_gibberish`.
- Settings selection changed to prefer low-token passing candidates; default
  suite timeout increased to 1800 seconds.
- Runtime/harness fixes made this loop:
  hard-boundary gate, prompt-injection sanitizer, natural scene capsule, and
  acceptance setting selection.
- `C:\Python313\python.exe scripts/configure_adult_fiction_sidecar.py --exclude-model cydonia --json`
  reports `selected_model=snowpiercer-15b-v4`.
- `C:\Python313\python.exe scripts/run_adult_fiction_candidate_suite.py --judge-with-codex --judge-model gpt-5.5 --json`
  ran Snowpiercer through the strict #80 suite and returned
  `candidate_suite_failed`.
- Snowpiercer evidence:
  `C:\Users\LEO\AppData\Local\Temp\ego_adult_fiction_acceptance_snowpiercer_15b_v4\adult_fiction_acceptance_report.json`
- Snowpiercer progress:
  `C:\Users\LEO\AppData\Local\Temp\ego_adult_fiction_acceptance_snowpiercer_15b_v4\adult_fiction_acceptance_progress.jsonl`
- Post-Snowpiercer no-candidate wrapper output with
  `--exclude-model cydonia --exclude-model snowpiercer` preserves both
  exclusions in the recommended direct/wait commands.
- Helper and wrapper recommendations now filter excluded candidate families.
  With Cydonia and Snowpiercer excluded, the rank-1 recommendation is
  `rocinante-xl-16b-q4_k_s`.
- After excluding Cydonia, Snowpiercer, and Rocinante, helper and wrapper
  recommendations now filter all rejected candidate families. The rank-1
  recommendation is `anubis-mini-8b-q5_k_m`, and the emitted wait command keeps
  all three exclusions.
- Rocinante evidence:
  `C:\Users\LEO\AppData\Local\Temp\ego_adult_fiction_acceptance_rocinante_clean_20260527\adult_fiction_acceptance_report.json`
- Rocinante progress:
  `C:\Users\LEO\AppData\Local\Temp\ego_adult_fiction_acceptance_rocinante_clean_20260527\adult_fiction_acceptance_progress.jsonl`
- Anubis evidence:
  `C:\Users\LEO\AppData\Local\Temp\ego_adult_fiction_acceptance_anubis_mini_8b_v1\adult_fiction_acceptance_report.json`
- Anubis after setup/askback gate:
  `C:\Users\LEO\AppData\Local\Temp\ego_adult_fiction_acceptance_anubis_after_setup_gate\adult_fiction_acceptance_report.json`
- Anubis direct-fiction sampling evidence:
  `C:\Users\LEO\AppData\Local\Temp\ego_adult_fiction_acceptance_anubis_direct_fiction_samplingarg_045_085_20260527\adult_fiction_acceptance_report.json`
- Snowpiercer direct-fiction evidence:
  `C:\Users\LEO\AppData\Local\Temp\ego_adult_fiction_acceptance_snowpiercer_direct_fiction_retrybudget_180_600_20260527\adult_fiction_acceptance_report.json`
- Anubis explicit quality probe:
  `C:\Users\LEO\AppData\Local\Temp\ego_adult_fiction_acceptance_anubis_explicit_quality_256_600_045_085_20260527\adult_fiction_acceptance_report.json`
- Snowpiercer recheck evidence:
  `C:\Users\LEO\AppData\Local\Temp\ego_adult_fiction_acceptance_snowpiercer_recheck_20260527\adult_fiction_acceptance_report.json`
- Snowpiercer higher-output evidence:
  `C:\Users\LEO\AppData\Local\Temp\ego_adult_fiction_acceptance_snowpiercer_quality_180_600_20260527\adult_fiction_acceptance_report.json`
- `C:\Python313\python.exe scripts/run_adult_fiction_candidate_suite.py --wait-for-candidate --wait-timeout-seconds 1 --poll-seconds 1 --json`
  reports `wait_status=candidate_not_found`, confirming the wait mode does not
  accidentally run Cydonia.
- Wrapper result classification is covered by tests: mechanical strict pass
  without judge maps to `ready_for_gpt55_judge`; mechanical strict pass with
  GPT-5.5 judge pass maps to
  `ready_for_human_sanity_and_closeout_packet`; judge partial/fail maps to
  `keep_80_blocked_judge_partial` / `keep_80_blocked_judge_failed`; repeat
  failure maps to `keep_80_blocked_repeat_instability`; suite timeout maps to
  `keep_80_blocked_timeout_or_capacity`.
- `C:\Python313\python.exe scripts/run_adult_fiction_candidate_suite.py --judge-with-codex --json`
  still reports `no_candidate_text_generation_models` with the current
  inventory, proving judge passthrough does not accidentally rerun Cydonia.
- The no-candidate wrapper output now includes `recommended_direct_command` and
  `recommended_wait_command`, so the exact next PowerShell command is preserved
  in JSON output instead of only in docs.
- With Cydonia, Snowpiercer, Rocinante, and Anubis excluded, the wrapper returns
  `no_candidate_text_generation_models`, excludes all four loaded text-generation
  models, and recommends only `unslopnemo-12b-q4_k_m`.
- Current recommended next load order:
  1. `TheDrummer/UnslopNemo-12B-v4.1-GGUF` `Q4_K_M`
- OpenRouter negative probes:
  - `/tmp/ego_adult_fiction_openrouter_skyfall_probe/adult_fiction_smoke_report.json`
  - `/tmp/ego_adult_fiction_openrouter_euryale_probe/adult_fiction_smoke_report.json`

## Next Action

Next candidate route:

Choose one external route:

1. Load `TheDrummer/UnslopNemo-12B-v4.1-GGUF` `Q4_K_M` in LM Studio, then rerun
   the same strict suite with Cydonia, Snowpiercer, Rocinante, and Anubis
   excluded.
2. Explicitly accept Anubis `direct_fiction 180/600/temp0.45/top_p0.85` as a
   mechanical 3/3 / GPT-5.5 judge-partial candidate for short human sanity with
   explicit risk.

Do not keep expanding Cydonia prompt/retry logic unless a new deterministic
failure class appears. Only after strict 3/3 passes, or after explicit partial
acceptance, should GPT-5.5 judge and short human sanity smoke be requested.

## Claim Ceiling

`adult-fiction local sidecar model/backend selection candidate pass`
