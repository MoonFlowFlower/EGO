# EgoDesktop Joi Real-Loop G-ABLATION Selected Source Chat Smoke v0 Status

- status: `accepted_local`
- task_id: `EGODESKTOP-GABLATION-022`
- parent_task_id: `EGODESKTOP-GABLATION-021`
- claim_ceiling: `selected_source_desktop_trigger_smoke_only`
- mainline_connected: `false`
- enabled: `explicit_smoke_flags_only`
- real_trigger_evidence: `valid_direct_node_smoke_trace_hash_match`
- runtime_authority: `explicit_smoke_only`

## Current Readback

- current branch: `main`
- source HEAD before 022 edits: `fa14bffc80b716e62c1a764548fdb85b266dcdf8`
- source worktree before 022 edits: clean except ignored 019 raw cache files
- 021 status: `accepted`
- 021 commit: `fa14bffc feat: add egodesktop capture manifest builder`
- first smoke attempt rejected: `npm run smoke -- --joi-real-loop-chat-smoke-text ...` did not pass the argument to the
  intended chat-smoke field and produced no valid 022 trace row; that artifact was deleted and is not admitted.
- trigger materializer:
  `python scripts/codex/materialize_egodesktop_selected_source_trigger_input.py --selection-id dailydialog_hf:train:0 --out artifacts/egodesktop_joi_real_loop_g_ablation_selected_source_chat_smoke_v0`
- trigger report text hash: `0e0b41796bc603d3a3338e60d955000dc5c13b88900a46d554dc5fe61f2a78db`
- trigger report `user_text_hash`: `fef12a004cfca8ce6b04203ec40e70b9f46ba563d53a530ed94dc5af30ab88c8`
- trigger derivation rule: `first_row_utterance_as_single_chat_turn`
- smoke command: direct `node EgoDesktop/scripts/smoke.js ... --joi-real-loop-chat-smoke-text <materialized userText>` with
  explicit `JOI_REAL_LOOP_*` flags.
- smoke status: `live2d_desktop_smoke_pass`
- chat smoke status: `chat_turn_trace_smoke_pass`
- trace rows: `1`
- trace row `public_inputs.user_text_hash`:
  `fef12a004cfca8ce6b04203ec40e70b9f46ba563d53a530ed94dc5af30ab88c8`
- hash alignment: `pass`
- committed-report raw text scan: `pass` for trigger report, smoke report, trace runner report, and trace rows.
- backend raw trace handling: generated backend trace JSONL contained the selected source utterance and was deleted before
  staging; it is not part of the admitted artifact set.
- full 022 candidate artifact leak scan after deletion: `selected_source_utterance_leak_count=0` across `11` files.
- chat smoke side effects: `side_effects_executed=false`, `memory_write=false`, `tool_use=false`,
  `message_send=false`, `file_write=false`, `network_call=false`.

## Current Claim Ceiling

This can prove only selected-source desktop-trigger smoke provenance. It does not prove `CREATURE_ON`, replay validity,
same-access comparison, or mechanism attribution.

## Next Minimal Closed-Loop Action

Use this local-only selected-source trigger smoke as the next evidence boundary for a future replay/ablation slice only if
that future slice has a new task card and preserves the same no-raw-text staging boundary.
