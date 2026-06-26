# Closeout Scope Readback 006A

- status: `mutation_scope_loaded_for_readback`
- claim_ceiling: `egodesktop_real_loop_g_ablation_backend_trace_snapshot_contract_only`

## Correct Command

```powershell
python scripts\codex_session_guard.py --mutation-scope docs\codex\tasks\egodesktop-joi-real-loop-g-ablation-backend-trace-snapshot-v0\MUTATION_SCOPE.yaml closeout-check --format markdown
```

The `--mutation-scope` option is a top-level option and must appear before `closeout-check`.

## Latest Readback Before 006A Edits

With the correct command form, the guard reported:

- `mutation_scope: loaded`
- `dirty_scoped/task_scoped/local_only/unsafe: 0 / 0 / 0 / 0`
- blockers: `push_pending`, `no_staged_changes`

## Current 006A Dirty-Scope Readback

After the 006A blocker-repair edits, the same command reports:

- `mutation_scope: loaded`
- `dirty_scoped/task_scoped/local_only/unsafe: 3 / 11 / 0 / 0`
- blockers: `push_pending`, `no_staged_changes`, `remote_sync_unavailable`

This repairs the earlier packet's incorrect statement that the guard had no mutation-scope CLI option. For any >=007
scoring run, this command must be run after scoped staging. Any unsafe dirty path remains blocking.
