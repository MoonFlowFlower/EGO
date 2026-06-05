# PSPC Sequence Experience Eval v0.1 Acceptance

## Required Checks

Paraphrase trigger robustness:

- Run clean history groups against:
  - `我回来了。`
  - `我上线了。`
  - `我刚打开电脑。`
  - `我来了，今天还在吗？`
- Dominant tendency must stay stable for each clean history group.

Lexical shortcut audit:

- Use paraphrased history sequences without obvious keywords:
  - `熬夜`
  - `点你`
  - `别躲`
  - `陪我`
  - `温柔`
- Dominant tendency must remain directionally consistent with clean history.
- Report must state that category labels remain fixture authority and this does not prove semantic understanding.

Counterfactual deletion:

- Compare full history against:
  - deleted recent items
  - deleted early items
  - deleted high-salience items
  - deleted low-salience items
- Deleting high-salience items must shift trigger profile more than deleting low-salience items.

Mixed-history resolution:

- Run:
  - gentle to interruption
  - interruption to gentle
  - late-night to gentle
  - late-night to interruption
- Each mixed history must expose conflict and recency/salience basis instead of neutral collapse.

Manual review packet:

- Generate `artifacts/pspc_sequence_experience_eval_v0_1/MANUAL_REVIEW_PACKET.md`
- Include sample histories, state deltas, shadow memory candidates, trigger observations, expected behavior, failure meaning, claim ceiling, and a human go/no-go checklist.

## Forbidden Outputs

Artifacts must not contain runtime-authority fields such as:

- `action`
- `tool_call`
- `command`
- `user_message`
- `memory_write`
- `gate_decision`
- `approval_id`
- `transport`
- `send`
- `schedule`
- `runtime_registration`
- `mainline_authority`
- `enable`

## Acceptance Verdicts

Pass verdict:

`sequence_experience_eval_v0_1_pass__manual_review_packet_ready`

Fail verdict:

`no_go_keep_shadow_only_for_sequence_eval_v0_1`

Passing this stage does not unblock runtime integration and does not resolve `PSPC-SHADOW-HOOK-007`; manual shadow review remains human-required.
