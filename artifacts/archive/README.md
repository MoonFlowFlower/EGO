# Archive Artifacts Boundary

Archive artifact boundary marker.

Do not archive replay / trace / audit evidence without explicit admission proof.

Rules:
- Historical artifacts may move here only after inventory and caller references are updated.
- Archive moves must preserve provenance and recovery notes.
- This directory is a future target, not proof that a path is already safe to archive.
- Archive moves still require explicit admission proof from a clean clone or CI workspace.

Current admitted lookup surface:
- `docs/archive/ARCHIVE_INDEX.yaml` is the canonical archive lookup index.
- `artifacts/archive/repo_cleanup_history/` now preserves the first admitted medium migration for historical cleanup bundles `P0` through `P7`.
- This archive closeout is frozen. Do not continue moving artifacts here by default unless a new archive slice is explicitly authorized or decisive caller proof exists.
