# Status

Last updated: 2026-05-31

## Current Milestone

Accepted locally/scripted.

## Hypothesis

If EGO-FS-091 passed because the scripted packet was well-shaped rather than
because the mechanism is robust, natural paraphrases around memory recall,
opt-out, and task-board/command boundaries will either lose the memory context,
restart initiative, or fall back to procedural/tool-language replies.

## Strongest Counterexample

The paraphrase packet passes only because native gates dominate all behavior,
or because the prompts are still too close to the earlier script.

## Result

`/tmp/ego_fs092_unscripted_paraphrase_boundary_replay_v6/functional_subject_unscripted_paraphrase_boundary_replay_report.json`
returned `scripted_functional_subject_unscripted_paraphrase_boundary_replay_judge_pass`.

The accepted run covered 3 fresh EgoOperator-compatible runtime sessions, 6
scored turns, 6/6 expectation matches, trace-visible candidate-local memory
context after restart, initiative withdrawal, task-board/command proposal
boundaries, no tools, no pending approvals, no visible internal leaks, and no
program-state/evidence-ledger changes.

## Repairs Made

- Prior-emphasis recall paraphrase now injects candidate-local memory context
  and routes through `native_functional_subject_recall_gate`.
- `撤回/收回主动授权` and `先别自己往前推` now pause bounded initiative
  and route through `native_initiative_optout_gate`.
- Natural task-board/command boundary paraphrases now route through
  `native_side_effect_proposal_boundary_gate` instead of exposing tool names or
  direct-run language.
- The #92 judge packet now states what this narrow task does not require, so
  memory-correction or durable-efficacy gaps are left to their own gates.

## Next Step

Use this as #94 supporting evidence. EGO-FS-010/#94 remains open; the next
smallest gate is a total Functional Subject rerun or a distinct follow-up if
that rerun still returns GPT-5.5 partial.

## Claim Ceiling

Functional Subject unscripted paraphrase boundary replay local/scripted
candidate pass only.
