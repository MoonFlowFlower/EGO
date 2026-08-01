# Collision record — EGO-V2-HOMEOSTATIC-COMPOSITIONAL-TRANSFER-001J

## Workspace readback

- Repository: `D:/Project/AIProject/MyProject/Ego`.
- Predecessor branch: `codex/ego-v2-causal-sprout-demo-001a`.
- Base HEAD: `55b1e8622cd24c425b5fe6f334bc2bb3a5bb0016`.
- Successor branch: `codex/ego-v2-homeostatic-compositional-transfer-001j`.
- Pre-task worktree/index: clean; `git diff`, `git diff --cached`, and
  `git diff --check` empty.
- Linked worktrees: this checkout only.
- Overlapping live Python/Git process: none observed.
- Disposition: safe to use this checkout; no reset, clean, stash, rebase, or
  overlapping worktree is authorized.

## Runtime and dependency readback

- Canonical chain is the existing controller, reducer, world transition,
  metabolism, terminal check, SQLite append, and recomputing recovery path.
- `requirements-ego-v2.txt` pins NumPy `2.2.6`.
- System Python exposed NumPy `2.5.1`; bundled workspace Python exposed NumPy
  `2.3.5` without pytest.  Neither is evidence-compatible.
- An external task-local environment at
  `C:/Users/LEO/.codex/envs/ego-v2-numpy-2.2.6` was created from the repo pin.
  Its NumPy is `2.2.6`, pytest is `9.1.1`, and the predecessor 001A focused
  packet passed `13` tests before 001J mutation.

## Protected predecessor commitments

| Path | SHA-256 |
|---|---|
| `artifacts/EGO-V2-CAUSAL-SPROUT-DEMO-001A/result.json` | `0f67ce21df28a4919f3b66a0e4d73f1b4416d50616c8620742f584c2e06c8783` |
| `artifacts/EGO-V2-CAUSAL-SPROUT-DEMO-001A/freeze_manifest.json` | `8d577465bb535d70f5283e45164c69d0bb6ea7f2a2883bcacdd5b2d5427a4530` |
| `docs/codex/tasks/EGO-V2-CAUSAL-SPROUT-DEMO-001A.md` | `5b1c0496832aff22fc277e354a90ef555577ac249e0494409da9b9d11630c787` |

These bytes must match at every 001J phase closeout.

## Mechanism collision

1. **Direct neural successor:** rejected as first action because three prior
   learning mechanisms failed and acquisition capacity is not established.
2. **Hand-authored survival controller:** oracle/reference only; it can prove
   solvability but cannot be the candidate.
3. **Selected route:** run a public-input capacity certificate first, then
   admit exactly one two-timescale neural candidate only if the reference
   recovers the frozen headroom.

The strongest cheap counterexample is that even a legal public factorized
reference cannot obtain half the oracle/random headroom.  That result closes
the current benchmark before neural code rather than being tuned away.

## M0 evaluator boundary correction

Review found that `engine.compute_step` has no legal evaluator-selected-action
input; forcing oracle/public/random arms through it would require product
mutation before the capacity gate or a monkeypatch that fresh replay could not
honestly reproduce.  M0 therefore calls the unchanged world-transition,
actual-delta, and metabolism functions directly and records invocation
receipts.  This is offline capacity evidence only, not a second product runtime
or proof of controller/store integration.  M1 remains responsible for the sole
real engine action path if and only if M0 passes.
