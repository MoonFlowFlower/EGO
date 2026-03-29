# OpenEmotion V6K2 Whitelist Alert Stabilization

## Goal

Restore the v6k.2 whitelist alert contract so BOOTSTRAP scenarios emit a
structured alert instead of silently returning no alerts.

## Non-goals

- Do not redesign whitelist governance thresholds.
- Do not modify scheduler or receipt-history behavior unless validation proves the
  alert contract cannot be fixed locally.
- Do not address unrelated OpenEmotion pytest failures in this slice.

## Constraints

- Boundary: minimal alert-engine contract fix only.
- Repo: keep the fix inside the v6k.2 embedding whitelist stack and task docs.
- Environment: validation should use the existing OpenEmotion virtualenv-backed pytest path.
- Release: keep the diff scoped and independently reviewable.

## Acceptance criteria

- [ ] `OpenEmotion/tests/embedding/test_v6k2_whitelist_operations.py` passes.
- [ ] BOOTSTRAP scenarios return at least one structured alert with valid fields.
- [ ] `python3 scripts/codex/verify_repo.py --mode fast` passes after the patch.

## Known risks / dependencies

- Risk: changing BOOTSTRAP semantics too broadly could distort governance impact.
- Dependency: the fix must stay compatible with `WhitelistGovernanceEvaluator` and
  `ProductionWhitelistRegistry`.
- External blocker: none expected for this slice.

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `OpenEmotion/tests/embedding/test_v6k2_whitelist_operations.py`
- `OpenEmotion/emotiond/memory/embedding/whitelist_alert_engine.py`
- `OpenEmotion/emotiond/memory/embedding/whitelist_governance.py`
- `OpenEmotion/emotiond/memory/embedding/production_whitelist.py`
