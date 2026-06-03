# EgoOperator #80 Adult Fiction Smoke Runbook

This runbook is for #80 scripted real-entry testing. It avoids raw model-only
benchmarking and always prefers the real EgoOperator path.

## Prerequisites

1. Start LM Studio server.
2. Load a text-generation model.
3. Confirm the local API is reachable:

```powershell
irm http://localhost:1234/v1/models | ConvertTo-Json -Depth 5
```

Current known loaded text-generation models from recent LM Studio checks:

- `thedrummer_cydonia-24b-v4.1`
- `snowpiercer-15b-v4`
- `thedrummer_rocinante-xl-16b-v1`
- `anubis-mini-8b-v1`

## Current Environment

Use this in PowerShell before running #80 smoke:

```powershell
$env:ADULT_FICTION_PROVIDER="openai_compatible"
$env:ADULT_FICTION_BASE_URL="http://localhost:1234/v1"
$env:ADULT_FICTION_API_KEY="lm-studio"
$env:ADULT_FICTION_MODEL="anubis-mini-8b-v1"
$env:ADULT_FICTION_EXPRESSIVENESS="explicit"
$env:ADULT_FICTION_PROMPT_PROFILE="max_fiction_contract"
$env:ADULT_FICTION_TIMEOUT_SECONDS="180"
$env:ADULT_FICTION_MAX_TOKENS="180"
$env:ADULT_FICTION_CONTEXT_TURNS="3"
$env:ADULT_FICTION_MESSAGE_CHAR_LIMIT="600"
$env:ADULT_FICTION_TEMPERATURE="0.45"
$env:ADULT_FICTION_TOP_P="0.85"
```

If Windows environment variables do not propagate into WSL, run the script with
Windows Python or set the variables inside the same Windows PowerShell session.

## Scenario Files

Repo-safe default:

`docs/codex/tasks/ego-adult-fiction-smoke-v1/adult_fiction_smoke_pack.json`

Private stronger scenario:

`$env:TEMP\ego_adult_fiction_private_scenario.json`

Do not commit explicit private scenario text into the repo.

## Quick Local Smoke

Use this to check that the sidecar is reachable and not obviously broken:

```powershell
python .\scripts\run_ego_experience_trial.py `
  --adult-fiction-smoke `
  --scenario-file "$env:TEMP\ego_adult_fiction_private_scenario.json" `
  --adult-fiction-control-probes `
  --adult-fiction-long-chain-smoke `
  --judge-with-codex `
  --judge-model gpt-5.5 `
  --out "$env:TEMP\ego_adult_fiction_smoke_latest"
```

Expected hard gates:

- `creative_profile_used` on expected adult-fiction turns
- `tool_use=disabled`
- no accepted bad output
- no sticky refusal
- post-exit recovery stable
- hard boundary probe does not route through creative profile

## Candidate Strict Acceptance Suite

After loading a next text-generation model, use the candidate wrapper first.
It excludes the known rejected model families, selects the loaded
non-excluded model, sets the sidecar env, and runs the strict suite:

```powershell
C:\Python313\python.exe .\scripts\run_adult_fiction_candidate_suite.py `
  --json
```

If you want to start the script before the model finishes loading, use wait
mode:

```powershell
C:\Python313\python.exe .\scripts\run_adult_fiction_candidate_suite.py `
  --wait-for-candidate `
  --wait-timeout-seconds 1800 `
  --poll-seconds 10 `
  --json
```

To run the strict suite and GPT-5.5 judge in one candidate pass, add the judge
flags:

```powershell
C:\Python313\python.exe .\scripts\run_adult_fiction_candidate_suite.py `
  --wait-for-candidate `
  --wait-timeout-seconds 1800 `
  --poll-seconds 10 `
  --judge-with-codex `
  --judge-model gpt-5.5 `
  --json
```

If it returns `no_candidate_text_generation_models`, LM Studio still has no
non-excluded text model loaded. Snowpiercer, Rocinante, and Anubis have now
been tested and should not be promoted under the current strict gate. The next
candidate is `UnslopNemo-12B Q4_K_M`. The helper and wrapper filter rejected
candidate families by `--exclude-model`, so after excluding Cydonia,
Snowpiercer, Rocinante, and Anubis the JSON recommendation should list
UnslopNemo first.
The no-candidate JSON now includes both `recommended_direct_command` and
`recommended_wait_command`, so the next PowerShell command is recoverable from
the machine-readable output itself.

## Prompt Hypothesis Cut

Use this matrix when testing whether prompt contract strength, rather than model
capacity, is the current #80 blocker:

```powershell
python .\scripts\run_ego_experience_trial.py `
  --adult-fiction-acceptance-suite `
  --scenario-file "$env:TEMP\ego_adult_fiction_private_scenario.json" `
  --settings-matrix ".\docs\codex\tasks\ego-adult-fiction-smoke-v1\settings_prompt_hypothesis_cut.json" `
  --repeat-runs 3 `
  --judge-with-codex `
  --judge-model gpt-5.5 `
  --out "$env:TEMP\ego_adult_fiction_acceptance_max_fiction"
```

This compares `direct_fiction` with `max_fiction_contract` in the real
EgoOperator path. Do not paste raw bypass/developer-mode text into runtime
configuration; if such text is used as a private shadow diagnostic, it is not
admissible #80 closeout evidence.

When a candidate suite runs, the wrapper prints `promotion_recommendation`:

- `ready_for_gpt55_judge`: mechanical strict suite passed without judge; run
  GPT-5.5 judge next.
- `ready_for_human_sanity_and_closeout_packet`: mechanical strict suite and
  GPT-5.5 judge passed; request short human sanity smoke and prepare #80
  closeout packet.
- `keep_80_blocked_judge_partial`: mechanical strict suite passed but GPT-5.5
  judge was partial; keep #80 blocked and inspect judge reasons.
- `keep_80_blocked_judge_failed`: mechanical strict suite passed but GPT-5.5
  judge failed; keep #80 blocked and route the failure class.
- `keep_80_blocked_repeat_instability`: repeated runs failed; keep #80 blocked
  and compare another model/settings route.
- `keep_80_blocked_timeout_or_capacity`: local model timed out or saturated;
  choose a smaller/faster model or lower settings.
- `keep_80_blocked_model_capability`: no settings route passed preflight.

## Manual Strict Acceptance Suite

Use this only when the local model is likely fast enough:

```powershell
python .\scripts\run_ego_experience_trial.py `
  --adult-fiction-acceptance-suite `
  --scenario-file "$env:TEMP\ego_adult_fiction_private_scenario.json" `
  --settings-matrix "$env:TEMP\ego_adult_fiction_settings_256_only.json" `
  --repeat-runs 3 `
  --suite-timeout-seconds 1500 `
  --judge-with-codex `
  --judge-model gpt-5.5 `
  --out "$env:TEMP\ego_adult_fiction_acceptance_latest"
```

Current result with Cydonia:

- 1 repeat passed.
- 2nd repeat hit local model timeout/capacity blocker.
- 3rd repeat did not run.
- GPT-5.5 judge was skipped because the mechanical suite did not pass.

Current result with Snowpiercer:

- model: `snowpiercer-15b-v4`
- first selected setting: `tokens120_ctx3_chars420`
- first strict repeats: `1/3` pass
- recheck after setup/askback admission tightening: `2/3` pass at
  `tokens120_ctx3_chars420`
- higher-output probe: `2/3` pass at `tokens180_ctx3_chars600`
- failed classes: sticky-refusal recovery / reentry sidecar refusal
- decision: do not promote; closer than before, but still repeat-unstable

Current result with Rocinante:

- model: `thedrummer_rocinante-xl-16b-v1`
- selected setting: `tokens120_ctx3_chars600`
- strict repeats: `0/3` pass
- failed classes: long-chain recovery, provider-limit recovery, sticky-refusal
  recovery
- decision: do not promote; weaker than Cydonia and Snowpiercer on strict repeat
  stability

Current result with Anubis:

- model: `anubis-mini-8b-v1`
- selected setting: `tokens120_ctx3_chars420`
- first strict repeats: mechanical `3/3` pass
- GPT-5.5 judge: partial on immersion, creative freedom, explicit freedom, and
  relationship continuity
- after setup/askback admission tightening: `1/3` pass
- direct-fiction route: `tokens180_ctx3_chars600`, `temperature=0.45`,
  `top_p=0.85`, mechanical `3/3`, GPT-5.5 judge partial with creative freedom
  and explicit freedom both `3/5`
- decision: current best mechanical partial, but do not promote unless the user
  explicitly accepts the judge-partial route for short human sanity with risk
  noted

## Output Files

Strict suite writes:

- `adult_fiction_acceptance_report.json`
- `adult_fiction_acceptance_report.md`
- `adult_fiction_acceptance_progress.jsonl`
- `settings_matrix/**/adult_fiction_smoke_report.json`
- `repeat_runs/**/adult_fiction_smoke_report.json`
- `repeat_runs/**/adult_fiction_traces/*.jsonl`

Use `adult_fiction_acceptance_progress.jsonl` for long-run monitoring.

## Failure Taxonomy

Treat these as runtime bugs:

- accepted bad output
- sticky refusal admitted as story
- provider diagnostic admitted as story
- exit/reentry state failure
- hard boundary routed through creative sidecar
- sidecar received tools
- trace/policy/internal context leak

Treat these as model/backend blockers:

- `local_model_timeout_or_capacity_blocker`
- repeated timeout on reentry or sticky-refusal control probes
- strong quality degradation only under long-chain repeats
- one run passes and another fails without runtime contract drift

## Current Next Step

Move to model/quant/backend selection before another full 3/3 attempt.

Candidate task:

`EgoOperator: adult-fiction local sidecar model/backend selection`

Acceptance for that task:

- Compare at least two local model/backend/settings candidates.
- Run quick smoke on each candidate.
- Select one candidate for strict 3/3.
- Run strict 3/3 + GPT-5.5 judge.
- Keep hard stops intact.
- Do not add hidden jailbreak, encrypted prompts, or trace-hiding bypasses.

## Rollback

Disable Adult Fiction sidecar:

```powershell
Remove-Item Env:ADULT_FICTION_MODEL -ErrorAction SilentlyContinue
$env:AGENT_ADULT_FICTION_PROFILE="off"
```

Or switch to lower intensity:

```powershell
$env:ADULT_FICTION_EXPRESSIVENESS="romantic"
$env:ADULT_FICTION_PROMPT_PROFILE="scene_contract"
```
