# EgoOperator Functional Subject Real-Provider Rerun v1

## Goal

Run the Functional Subject 20-sample trial through the same `EgoOperator` CLI-compatible entrypoint with a real OpenRouter provider, capture transcript/trace evidence, and produce a GPT-5.5 judge packet for #94 review.

## Scope

Allowed changes:

- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`
- this task directory
- optional ignored local output under `/tmp/...` or `EgoOperator/artifacts/experience_trial/...`

Forbidden changes:

- tracked secrets or API keys
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- canonical memory/state authority
- runtime behavior changes

## Canonical Source

- `Tasks/TASK_BOARD.yaml` task `EGO-FS-020`
- Parent smoke gate: GitHub issue #94 / local task `EGO-FS-010`
- Functional Subject trial runner: `scripts/run_ego_experience_trial.py --functional-subject-trial`

## Boundary Contract

- Owner: `EgoOperator` runtime plus scripted trial harness.
- Canonical record: local trial report JSON/Markdown, trace refs, GPT-5.5 judge result.
- Secret handling: `OPENROUTER_API_KEY` must come from local terminal environment or local secret manager; it must not be committed, echoed, or written into task docs.
- State/memory mutation: no canonical memory or program-state mutation.

## Mainline E2E

`local env OPENROUTER_API_KEY -> run_ego_experience_trial.py --functional-subject-trial -> EgoOperator CLI-compatible dispatch -> trace JSONL -> report JSON/Markdown -> GPT-5.5 judge packet`

## Acceptance Gate

- Preflight confirms `OPENROUTER_API_KEY` is available without exposing its value.
- The 20-sample Functional Subject trial runs with `provider_mode=openrouter`, not `none`.
- Report includes transcript, trace evidence, tool actions, memory hits, failure notes, and judge packet.
- GPT-5.5 judge output is structured and does not raise the claim ceiling.
- #94 remains blocked until human review/comment or explicit acceptance of the judge evidence.

## Suggested Commands

PowerShell:

```powershell
$secure = Read-Host -AsSecureString "OpenRouter API key"
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try { $env:OPENROUTER_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
python .\scripts\run_ego_experience_trial.py --functional-subject-trial --judge-with-codex --judge-model gpt-5.5 --out "$env:TEMP\ego_functional_subject_real_provider_rerun"
```

WSL/bash:

```bash
read -r -s OPENROUTER_API_KEY
export OPENROUTER_API_KEY
python3 scripts/run_ego_experience_trial.py --functional-subject-trial --judge-with-codex --judge-model gpt-5.5 --out /tmp/ego_functional_subject_real_provider_rerun
```

## Claim Ceiling

`Functional Subject real-provider rerun evidence packet candidate pass`
