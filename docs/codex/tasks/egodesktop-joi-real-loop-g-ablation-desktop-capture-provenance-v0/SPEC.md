# EgoDesktop Joi Real-Loop G-ABLATION Desktop Capture Provenance v0

- task_id: `EGODESKTOP-GABLATION-020`
- parent_task_id: `EGODESKTOP-GABLATION-019`
- status: `accepted`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering implementation / capture provenance contract`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `no_runtime_enablement`
- real_trigger_evidence: `none_for_020_design_contract`
- claim_ceiling: `desktop_capture_provenance_contract_only`
- auto_remote_anchor: `forbidden`

## Objective

Freeze what future `real desktop-chat-turn capture` must mean after 018 repaired public source ids and 019 produced an
ignored local public raw-cache sample. This is a contract-only task: it does not type, replay, capture, score, compare,
or advance any route.

## Answer To The Operator Question

`real desktop-chat-turn capture` does not mean just "the text is real." In this lane, `real` has three separate gates:

1. `real_source_text`: the user turn is non-synthetic source material. It may come from local EgoDesktop/EgoOperator
   artifacts, operator-authored turns, or public/licensed datasets such as the 019 local raw-cache sample.
2. `real_desktop_trigger`: that text enters EgoDesktop through the real chat-turn path, such as
   `window.egoDesktop.sendChatTurn(...)` and the default IPC seam. A direct evaluator call or offline scorer is not a
   desktop trigger.
3. `replayable_capture_row`: the existing G-ABLATION trace tap/writer emits a row with source id/hash, run id,
   condition, split, prompt/source provenance, serialized state, public inputs, adapter output, D-field provenance,
   replay inputs, and row hash.

Only rows satisfying all three can be called future `real captured desktop-chat-turn` evidence. Existing EgoDesktop chat
data and downloaded public dialogue rows are real source material, but they are not capture evidence until they are
sent through EgoDesktop under a frozen capture design and serialized by the approved writer.

## Current Source State

- 018 repaired `dailydialog_hf` to `https://huggingface.co/datasets/roskoN/dailydialog` while preserving
  `public_nc_sa`, `noncommercial_only=true`, and `sharealike_required=true`.
- 019 created an ignored local raw-cache sample:
  - `dailydialog_hf`: 25 `train` rows via Hugging Face datasets-server rows API.
  - `empathetic_dialogues_hf`: 25 `train` rows extracted from the public
    `https://dl.fbaipublicfiles.com/parlai/empatheticdialogues/empatheticdialogues.tar.gz` archive.
- 019 committed only `RAW_CACHE_REPORT.*`; raw text remains under ignored
  `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/source_cache/`.

## Future Capture Preconditions

A later capture task must freeze a capture manifest before any desktop trigger:

- source ids and source cache hashes;
- exact selected row ids or deterministic row-sampling rule;
- raw-text privacy mode: `hash_only`, `redacted_excerpt`, or `raw_local_only`;
- license tier and downstream claim constraints;
- split assignment and leakage scan with positive controls;
- independence clustering by dataset/source, topic, speaker/session when available, near-duplicate surface, and affect
  band;
- `CREATURE_ON` / `CREATURE_OFF_OR_FROZEN` / `OFF_STATIC_REPLAY_HELDOUT` condition plan if comparison is attempted;
- same-access baseline battery plan if scoring is attempted;
- row schema and writer path hashes;
- explicit stop if any source row leaks split, target D labels, expected expression labels, condition labels, or verdict
  hints.

## Task Card

- problem definition: prevent source-realism, desktop-trigger-realism, and replay-row provenance from being conflated.
- current stage/layer: `engineering implementation / capture provenance contract`.
- mainline target: future explicit-flag desktop capture contract only, not runtime.
- enabled-state requirement: no runtime enablement.
- real-trigger evidence requirement: none in 020; future task must produce it.
- hypothesis: making the three gates explicit prevents false promotion of local logs/public corpora into capture
  evidence.
- strongest baseline: future same-access public-input controllers over the same source rows.
- ablation requirement: none in 020.
- trace/replay requirement: future rows must be emitted by the existing trace tap/writer, not a second path.
- computed-evidence provenance gate: no scores/verdicts; this task is docs/readback only.
- acceptance gate: contract distinguishes source text, desktop trigger, and replay row; carries forward 018/019 source
  boundaries; introduces no capture/scoring/runtime authority.
- claim ceiling: desktop capture provenance contract only.
- stop condition: any capture, score, comparison, runtime enablement, program-state/evidence-ledger update, push, tag,
  or remote anchor.
- rollback plan: delete 020 docs, remove task-board entry, regenerate route views.
- expected changed files:
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-desktop-capture-provenance-v0/`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- forbidden changes:
  - no raw text staging;
  - no desktop capture;
  - no same-access baseline execution;
  - no scoring, comparison, verdict, or route advancement;
  - no runtime enablement;
  - no `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update;
  - no push, tag, or remote anchor.
- Auto-Remote-Anchor decision: forbidden.

## What This Can Prove

Only that the next capture step has a bounded provenance contract and that existing local/public source material is not
being mislabeled as desktop capture evidence.

## What This Does Not Prove

This does not prove desktop-chat-turn capture, `CREATURE_ON` effect, replay, D-provenance, same-access saturation,
baseline score, candidate attribution, route advancement, product benefit, runtime integration safety, stable user
benefit, durable memory efficacy, agency, emotion, subjectivity, consciousness, alive status, or Bar-2 specialness.

## Next Minimal Closed-Loop Action

Open a separate explicit capture-manifest task that chooses a small heldout row set from the ignored local source cache
and freezes the trigger/replay schema before any EgoDesktop run.
