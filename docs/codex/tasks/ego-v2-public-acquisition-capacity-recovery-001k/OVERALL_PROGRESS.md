# 001K research campaign progress

- Last updated: 2026-08-01
- Program goal: identify and repair the legal public acquisition bottleneck
  without touching 001J formal evidence or its heldout assignments.
- Current stage goal: diagnose public observability with the frozen legacy
  planner before changing navigation or acquisition policy.
- Stage success criteria: full-history, no-update, feedback-shuffle, and
  evaluator-only correct-posterior arms separate learning failure from planning
  failure on `search-dev`.
- Reviewer verdict: `needs_more_exploration`
- Validated evidence: 001J stored rows show 1,405/1,536 public actions were
  turns, only 64 were successful interactions, and no world identified all
  five tokens within 96 actions. This is diagnostic evidence, not yet a causal
  adjudication.
- Validated call-chain evidence: all 001J hashes match; AST order is
  plan -> transition -> actual outcome -> metabolism -> update; a synthetic
  public state intervention changed the final selected action. The posterior is
  connected, but its use may still be defective.
- Current blocker: none.
- Next frontier: run the four predeclared S1 observability candidates on
  repeatable `search-dev`, beginning with correct-posterior substitution under
  unchanged legacy navigation.
