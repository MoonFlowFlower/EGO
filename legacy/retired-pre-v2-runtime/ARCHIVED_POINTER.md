# Retired pre-V2 runtime pointer

`EgoOperator/` and `EgoDesktop/` are historical implementations, not current
product/runtime authority. They were removed from the current tree by
`EGO-ITL-V2-ONLY-SIMPLIFICATION-001A`.

Local recovery boundary:

```text
tag: ego-pre-v2-only-mainline-20260718-d1b72a3f
commit: d1b72a3f39564c2f1c4fe474974017ed3d5b17e9
tree: b70cc03b49df2708899611364efb1a3941eb605b
removed_path_count: 184
removed_path_set_sha256: 3d994afffb9218b420c6e7c4e1deb30ce531bc5d84b1a15bdda8f0f6118e5f28
publication: local only; push/tag publication forbidden
```

Ignored and otherwise untracked data from the retired roots was preserved
outside the active repository before those roots were removed:

```text
quarantine_root: D:\Project\AIProject\MyProject\.ego-retired-untracked-quarantine\ego-pre-v2-only-mainline-20260718-d1b72a3f
file_count: 4561
total_bytes: 524784031
entry_set_sha256: c90e4887391d2b6c9ef140ba3b5eb4959f6254f393527cfeb1d1839f62ecaa11
move_verification: pass
```

The exact per-path Git mode, blob OID, byte length, SHA-256, caller evidence,
rollback command, preserved-untracked-data inventory, and claim boundary are in
`artifacts/archive/pre_v2_runtime_retirement_manifest.json`.

Example read-only recovery:

```powershell
git show ego-pre-v2-only-mainline-20260718-d1b72a3f:EgoOperator/agent_base.py
```

This pointer proves only local Git-object recoverability plus the recorded
untracked-data move/hash verification. It does not grant the retired projects
current product authority and does not establish mechanism, learning, agency,
subjectivity, consciousness, or user-benefit claims.
