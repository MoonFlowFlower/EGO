# Plan

1. Preflight local environment without printing the key.
2. Run the Functional Subject 20-sample trial with real OpenRouter provider.
3. Run GPT-5.5 judge through `codex exec` if available.
4. Save report JSON/Markdown and trace references under a local output directory.
5. Update `EGO-FS-010` / #94 only with evidence summary after the report exists.

## Stop Conditions

- `OPENROUTER_API_KEY` is missing.
- Provider returns repeated 429/503 across the fallback chain.
- GPT-5.5 judge runner is unavailable.
- Report status remains provider unavailable.
- Any proposed closeout would require human comment or claim-ceiling upgrade.

## Non-Goals

- No runtime code changes.
- No GitHub Project mutation during the rerun itself.
- No tracked secret files.
- No program-state or evidence-ledger update.
