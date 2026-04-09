# Repo Authority Cleanup - CLEAN CLONE CLOSEOUT PROOF

This is the final closeout proof surface.

Requirements:
- canonical docs boundary markers must be present
- archive docs boundary markers must be present
- current/archive artifact markers must be present
- generated inventory must be rebuild-only and include its README marker
- dirty-worktree boundary must declare local noise non-authority
- `python3 scripts/codex/verify_cleanup_admission.py` must pass
- `python3 scripts/codex/verify_repo.py --mode fast` must pass
- The proof must be reproducible in a clean clone or CI workspace.
- no physical archive moves are implied by local worktree state
