# Legacy Pre-Operator Mainline Archived Pointer

Source of truth: `docs/PROGRAM_STATE_UNIFIED.yaml`.

Archive pointer: `legacy-pre-operator-mainline-before-purge`

Removed current-tree paths:

- `legacy/ego-pre-handmade-mainline/EgoCore/`
- `legacy/ego-pre-handmade-mainline/OpenEmotion/`
- `legacy/ego-pre-handmade-mainline/ego_desktop_lab/`

Reason:

The current authoritative runtime owner is `EgoOperator`. The old pre-operator runtime, subject kernel, and deterministic lab harness are preserved through git history and the archive pointer only. They have no runtime authority, no default path, and no task-routing authority in the current main working tree.

Reference boundaries:

- Thin reusable-idea inventory: `docs/archive/LEGACY_ALGORITHM_INVENTORY.md`
- Archive manifest and rollback details: `artifacts/archive/legacy_pre_operator_mainline_manifest.json`

Rollback:

```bash
git checkout legacy-pre-operator-mainline-before-purge -- legacy/ego-pre-handmade-mainline/EgoCore legacy/ego-pre-handmade-mainline/OpenEmotion legacy/ego-pre-handmade-mainline/ego_desktop_lab
```

After rollback, restored code is still reference only until a new Stage Card and evidence gate authorize reuse.

Claim ceiling:

This pointer proves only archival traceability for removed legacy code. It does not prove EgoOperator runtime efficacy, stable user benefit, live autonomy, durable memory efficacy, functional selfhood, consciousness, or subjective experience.
