# Archive Docs Boundary

Archive relocation is admission-controlled.

Do not move files here until caller and gate references are cleared.

Rules:
- This directory is a boundary marker, not an archive manifest by itself.
- Historical docs must remain recoverable by path or redirect before any physical move.
- Current canonical docs must never be moved here as part of a bulk cleanup.
- Dirty worktree noise is non-authority.
- Archive relocation remains admission-controlled until clean-clone / CI proof is available.

Current admitted lookup surface:
- `docs/archive/ARCHIVE_INDEX.yaml` is the repo-level archive index.
- The first admitted medium migration now lives under this boundary for two superseded top-level docs; current authority and current evidence paths remain in place.
- Current closeout is frozen at that slice. Do not continue archive moves by default; reopen only under the triggers recorded in `docs/archive/ARCHIVE_INDEX.yaml`.
