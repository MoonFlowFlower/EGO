# Task Board Sync Artifacts

`Tasks/TASK_BOARD.yaml` is the canonical task state. Files in this directory support low-frequency mirroring to GitHub.

- `sync_state.json`: tracked cache of known external mirror IDs and desired hashes.
- `sync_log.jsonl`: local sync evidence log; ignored by default.
- `outbox.jsonl`: local planned sync operations; ignored by default.

These files do not replace program state or the evidence ledger.
