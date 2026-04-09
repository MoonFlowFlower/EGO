# Repo Authority Cleanup - DIRTY WORKTREE BOUNDARY

Dirty worktree noise is non-authority.

Rules:
- Uncommitted local changes, generated files, and platform-specific residue do not count as final closeout proof.
- A dirty worktree may be used only as a staging area for scoped implementation.
- Final closeout proof must run in a clean clone or CI workspace.
- Repo-tracked canonical/archive markers win over local noise when they disagree.
- Any physical archive or delete decision must be based on clean-clone / CI verification, not on local residue.
