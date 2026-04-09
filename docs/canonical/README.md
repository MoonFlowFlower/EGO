# Canonical Docs Boundary

Physical canonical migration is not complete yet.

Use `docs/codex/tasks/repo-authority-cleanup/CANONICAL_DOCS_INDEX.md` as the current canonical index.

Rules:
- This directory is a boundary marker, not a second authority source.
- Do not move canonical docs here until caller, gate, and README references are cleared.
- The current canonical doc set remains defined by the cleanup task ledger and existing live doc paths.
- Generated inventory is rebuild-only and not part of the canonical authority set.
- The final closeout proof must run in a clean clone or CI workspace.
