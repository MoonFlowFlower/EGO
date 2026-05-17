# Ego Handmade Operator Permission Gates v1 - PLAN

## Implementation

- expose `read_file`, `glob_files`, and `grep_files` to the main agent by default
- expose `write_file`, `run_command`, and `web_fetch` only when their existing
  environment flags are enabled
- add a model-callable `remember_note` tool only when operator memory is enabled
- require explicit memory-write intent in the latest user message before
  admitting `remember_note`
- keep all workspace path access behind containment checks
- add CLI permission status output so the runtime reports memory/tool capability
  accurately

## Validation

- add focused permission-gate tests for tool visibility, write opt-in,
  containment, explicit memory writes, blocked memory writes, slash remember,
  history-only chat, and status reporting
- rerun existing operator-cut, memory-system, extracted-primitives, and
  operator-comparison tests
- run syntax checks and scoped diff whitespace checks

## Rollback

Revert the `Ego_handmade` wiring/tests plus this task directory. Runtime memory
and trace artifacts remain ignored and can be deleted locally.
