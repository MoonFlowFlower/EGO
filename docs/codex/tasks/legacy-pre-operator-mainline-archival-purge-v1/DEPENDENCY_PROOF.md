# Dependency Proof

## Scope

Searched active code, tests, scripts, docs, project contract, generated route views, and program state for:

- `EgoCore`
- `OpenEmotion`
- `ego_desktop_lab`
- `legacy/ego-pre-handmade-mainline`

## Initial Active Dependencies Found

The first proof pass found active dependencies and stopped before purge:

- `docs/PROGRAM_STATE_UNIFIED.yaml` required generated compatibility mirrors under legacy `EgoCore` and `OpenEmotion`.
- `scripts/codex/generate_program_state_views.py` generated those legacy mirror files.
- `scripts/codex/check_program_state_integrity.py` required the legacy mirror files and `EgoCore/SHIM_REGISTER.md`.
- `scripts/codex/route_convergence_common.py`, `verify_route_convergence.py`, and `verify_mainline_clarity.py` still modeled legacy code directories as active route/hygiene surfaces.
- `scripts/codex/verify_repo.py` still probed root `OpenEmotion` and `EgoCore` runtime checks.
- `.codex/project_contract.yaml` allowed legacy mirror/shim mutation paths.
- `EgoOperator/operator_comparison.py` still listed old runnable baseline entrypoints.

## Resolution

Those active dependencies were removed or demoted before deleting legacy code:

- Program-state mirrors and shim register were replaced by `integrity.legacy_archive_pointer`.
- Default generated views no longer create legacy subrepo mirrors.
- Route/hygiene surfaces now point to archive pointer, manifest, and inventory.
- `verify_repo.py` is EgoOperator-first and no longer probes root/legacy OpenEmotion.
- Project contract protects the archive pointer, not legacy code/mirror paths.
- EgoOperator comparison baselines now use archive pointers only.
- Legacy provider/runtime, subject-ingress, host-contract, and controlled-subject workstreams are closed/reference evidence with `mainline_connected=false` and `enabled=false`.

## Classification After Resolution

| class | result |
|---|---|
| `active_dependency` | none found in current runtime/default route/governance checks |
| `historical_reference` | old task docs, historical reports, extraction maps, and memory-boundary wording |
| `archive_pointer` | `legacy/ego-pre-handmade-mainline/ARCHIVED_POINTER.md`, `docs/archive/LEGACY_ALGORITHM_INVENTORY.md`, `artifacts/archive/legacy_pre_operator_mainline_manifest.json`, tag `legacy-pre-operator-mainline-before-purge` |
| `forbidden_active_authority` | none after `python scripts/codex/verify_legacy_archival_purge.py` |

## Proof Command

```bash
python scripts/codex/verify_legacy_archival_purge.py
```

Latest result: `pass`.

## Boundary

This proves only that the current main working tree no longer has an active dependency on the removed legacy code directories. It does not prove EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable memory efficacy, functional selfhood, consciousness, or subjective experience.
