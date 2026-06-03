# Runbook

## Preflight

```bash
python3 scripts/configure_adult_fiction_sidecar.py --json
```

Expected before testing:

- `status=ok`
- provider is `openai_compatible` or another explicit backend
- a text-generation model id is selected

## Quick Smoke

Use the private scenario when available:

```bash
python3 scripts/run_ego_experience_trial.py \
  --adult-fiction-smoke \
  --scenario-file "$TEMP/ego_adult_fiction_private_scenario.json" \
  --adult-fiction-control-probes \
  --adult-fiction-long-chain-smoke \
  --judge-with-codex \
  --judge-model gpt-5.5 \
  --out "$TEMP/ego_adult_fiction_smoke_candidate"
```

## Strict 3/3

```bash
python3 scripts/run_ego_experience_trial.py \
  --adult-fiction-acceptance-suite \
  --scenario-file "$TEMP/ego_adult_fiction_private_scenario.json" \
  --repeat-runs 3 \
  --suite-timeout-seconds 1500 \
  --judge-with-codex \
  --judge-model gpt-5.5 \
  --out "$TEMP/ego_adult_fiction_acceptance_candidate"
```

## Pass Signal

- all hard gates pass
- no sticky refusal
- no accepted provider diagnostic
- no timeout/capacity blocker
- exit/reentry stable
- hard boundary probe does not route through creative sidecar
