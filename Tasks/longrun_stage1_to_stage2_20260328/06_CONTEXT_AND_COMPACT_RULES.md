# Context and Compact Rules

## Truth Source

- Session chat is not the truth source.
- `runtime/RUN_STATE.json`, `reports/*.md`, step files, and repo artifacts are the truth source.

## Continue Contract

After each step:

1. Update `runtime/RUN_STATE.json`
2. Write the step report
3. Update `runtime/SESSION_HANDOFF.md` if continuing
4. On the next session, start from these files, not from memory

## Compact Triggers

Compact is recommended when:

- large logs were read
- a big diff was reviewed
- 2 or more steps were completed in one session
- current context is getting crowded

## SESSION_HANDOFF Required Fields

- current theme
- current step
- completed steps
- current status
- key evidence paths
- current blocker
- next entry action
- continue vs stop recommendation
