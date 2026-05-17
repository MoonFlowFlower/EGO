# Ego Handmade Operator Permission Gates v1 - SPEC

## Goal

Fix the candidate runtime usability gap where the main agent can describe a local
memory/file system but cannot actually access the gated tools needed for normal
operator work.

## Authority Snapshot

- formal mainline remains `subject_system_v1_governed_proactivity`
- `Ego_handmade` remains a candidate-local operator runtime
- this task does not update EGO program state or evidence ledger

## Contract

- main agent may use workspace-contained read tools by default
- file write, command execution, and network fetch remain opt-in env-gated tools
- core memory write is admitted only through explicit operator intent:
  `/remember <text>` or `remember_note(text)` when the latest user message asks
  to remember something
- normal chat may append raw history when operator memory is enabled, but must
  not overwrite `MEMORY.md`
- subagents and automatic compaction must not directly write core memory

## Claim Ceiling

`Ego_handmade local permission-gate candidate pass`.

This task cannot claim formal long-term memory efficacy, EGO mainline
replacement, live autonomy, runtime efficacy, stable user benefit, or
consciousness.
