# EgoDesktop Joi Real-Loop G-ABLATION Real Source Capture Design v0

- task_id: `EGODESKTOP-GABLATION-014`
- parent_task_id: `EGODESKTOP-GABLATION-013`
- status: `accepted_local_fallback_reviewed`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering implementation / data provenance and capture design`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `no_runtime_enablement`
- real_trigger_evidence: `none_for_014_design_card`
- claim_ceiling: `real_source_capture_design_only`
- auto_remote_anchor: `forbidden`

## User Authorization Readback

The operator explicitly authorized using existing EgoDesktop chat data and downloading public internet dialogue data for
the next real desktop-chat-turn capture design.

This authorization permits a bounded source-design task. It does not by itself authorize capture, scoring, verdicts,
program-state/evidence-ledger updates, push, tag, remote anchor, account login, gated dataset acceptance, or uploading
local/private data to third parties.

## What "Real Desktop-Chat-Turn Capture" Means

In this lane, `real` has three separate meanings that must not be conflated:

1. `real_source_text`: the user-turn text comes from a non-synthetic source, such as operator-authored EgoDesktop turns,
   existing local EgoDesktop/EgoOperator conversation artifacts, or public/licensed dialogue corpora.
2. `real_desktop_trigger`: the turn is injected through the real EgoDesktop chat-turn entrypoint,
   `window.egoDesktop.sendChatTurn(...)`, or an equivalent default IPC seam, not through a second evaluator-only code
   path.
3. `replayable_capture_row`: the existing G-ABLATION tap/writer produces trace rows with run id, condition, split,
   prompt/source id, source hashes, serialized state, public inputs, adapter output, D-field provenance, replay inputs,
   and row hash.

Only a row that satisfies all three can be used as future `real captured desktop-chat-turn` evidence. External datasets
and historical local chats can supply source text, but they do not become desktop capture evidence until they are
replayed or typed through the real EgoDesktop chat-turn path under a frozen design.

## Existing Local Data Readback

Local artifacts already show that the EgoDesktop seam and trace writer exist, but they do not yet provide a future
`CREATURE_ON` heldout comparison:

- `artifacts/egodesktop_joi_real_loop_g_ablation_chat_turn_trace_v0/trace/trace_rows.jsonl`
  - rows: `1`
  - run_id: `egodesktop_chat_turn_trace_v0_smoke`
  - condition_id: `CURRENT_SHIM`
  - split_id: `heldout`
  - claim ceiling: `egodesktop_real_loop_g_ablation_harness_contract_only`
  - limitation: smoke/contract row, not a preregistered `CREATURE_ON` heldout row.
- `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_predeclared_single/trace/trace_rows.jsonl`
  - rows: `1`
  - run_id: `egodesktop_gablation_009_calibration_capture_predeclared_single`
  - condition_id: `CURRENT_SHIM`
  - split_id: `calibration`
  - limitation: calibration source row only, not heldout and not `CREATURE_ON`.
- `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_turn2/selected_calibration_trace_rows.jsonl`
  - rows: `1`
  - run_id: `egodesktop_gablation_009_calibration_capture_ui_turn2`
  - condition_id: `CURRENT_SHIM`
  - split_id: `calibration`
  - limitation: blocked/superseded negative evidence only. This was the rejected 009 post-hoc positional-selection
    attempt and must not be admitted into a future source manifest, calibration basis, capture basis, score, or
    comparison.
- `artifacts/egodesktop_session_local_conversation_context_v0/session_context_report.json`
  - status: `pass`
  - message_count: `4`
  - claim ceiling: `local_session_context_only`
  - limitation: source-context example only; `enabled=false`, `mainline_connected=false`, no runtime authority.

## Public Data Candidate Readback

Current network metadata check found these source candidates:

- DailyDialog Hugging Face dataset card:
  - URL: `https://huggingface.co/datasets/daily_dialog`
  - license observed from raw dataset card: `cc-by-nc-sa-4.0`
  - size observed from card: downloaded files about `4.48 MB`
  - status: source candidate only; non-commercial/share-alike license constraints must be preserved.
- EmpatheticDialogues Hugging Face dataset card:
  - URL: `https://huggingface.co/datasets/facebook/empathetic_dialogues`
  - license observed from raw dataset card: `cc-by-nc-4.0`
  - size observed from card: downloaded files about `28.02 MB`
  - status: source candidate only; non-commercial license constraints must be preserved.
- LMSYS Chat 1M Hugging Face dataset:
  - URL: `https://huggingface.co/datasets/lmsys/lmsys-chat-1m`
  - raw card access returned `401 Unauthorized`
  - status: not admitted for automatic download in this task; gated or restricted access requires separate operator
    action and terms review.
- Persona-Chat / ParlAI:
  - URL: `https://github.com/facebookresearch/ParlAI/tree/main/projects/personachat`
  - current quick read did not establish a license for the data itself
  - status: not admitted until license and download path are verified.

No public dataset was downloaded in this task.

## License / Provenance Gate

Future source-manifest tasks must serialize a `source_license_tier` and block or constrain downstream use before any
download or capture. This is a provenance gate for this evidence lane, not legal advice; the operator remains
responsible for final dataset-terms review.

Required license/provenance fields per source:

- `source_id`;
- `source_kind`: one of `local_operator_artifact`, `local_egodesktop_artifact`, `public_dataset`, `operator_authored`;
- `dataset_or_artifact_url`;
- `retrieved_at`;
- `license_name`;
- `license_url`;
- `license_text_hash_or_card_hash`;
- `source_license_tier`;
- `attribution_required`;
- `sharealike_required`;
- `noncommercial_only`;
- `gated_terms_required`;
- `operator_terms_review_required`;
- `allowed_in_capture_manifest`;
- `allowed_claim_ceiling`;
- `blocked_reason`.

Required `source_license_tier` meanings:

- `local_operator_private`: local operator/Ego artifacts. Allowed only for local evidence work; raw text must not be
  uploaded. Future capture manifests must specify PII/privacy minimization before serializing text into trace rows.
- `public_permissive`: public source with permissive reuse. Attribution and license URL/hash still must be recorded.
- `public_attribution_required`: public source requiring attribution. Downstream reports must preserve attribution
  fields.
- `public_noncommercial`: public source restricted to non-commercial use. It may be used only for local
  non-commercial research/evidence artifacts; derived evidence must not support product, companion-readiness,
  commercial, or user-benefit claims. This lane's claim ceiling must remain non-commercial evidence-compatible.
- `public_sharealike`: public source with share-alike obligations. Future derived source manifests and reports must
  preserve the same-license obligation or block the source.
- `public_nc_sa`: public source with both non-commercial and share-alike constraints. It inherits both restrictions.
- `gated_or_terms_required`: access requires login, request, click-through, restricted card, or terms acceptance. Block
  automatic download; operator must review and perform any required acceptance separately.
- `unknown_or_unclear`: license or terms are not established. Block automatic download and block capture-manifest use.

For 014, DailyDialog and EmpatheticDialogues are `public_nc_sa` and `public_noncommercial` candidates respectively, so
they are source candidates only under the local non-commercial evidence ceiling. LMSYS Chat 1M is
`gated_or_terms_required`. Persona-Chat/ParlAI remains `unknown_or_unclear` until the data license and download path are
verified.

## B-011 Carry-Forward Gates For Real Sources

Real source text does not automatically fix the prompt-pack failures that blocked 011. Any future real-source
preregistration must explicitly pass these carry-forward gates before capture:

- `b011_4_no_split_or_meta_leakage`: user-visible source text must not contain `calibration`, `heldout`, `evaluation`,
  `review split`, source-split labels, expected condition labels, or other meta markers that reveal split membership or
  desired outcome. Split/source labels may exist only in metadata outside the user text.
- `b011_5_effective_independence_not_unique_id`: source rows must prove effective independence at the chosen unit.
  Unique ids alone are insufficient. The manifest must cluster by dataset/source, speaker or session id when available,
  topic, template/near-duplicate surface, and affect band; repeated or clustered rows require family-level collapse or
  a cluster-robust equivalence design.
- `b011_6_causal_path_affect_coverage_and_antidegeneracy`: the manifest must state whether the tested path is
  prompt-affect generalization, internal-state trajectory behavior, or another causal path. It must predeclare affect
  coverage, expression-name base rate/entropy, `CREATURE_ON` vs `CREATURE_OFF/FROZEN` movement requirements, and a
  `blocked_degenerate_expression_channel` outcome for near-constant D channels.

If any carry-forward gate fails, the future source manifest is blocked before capture.

## Operator-Authored And Privacy Gates

Operator-authored source text has demand-characteristic risk. Future operator-authored source collection must freeze
source turns before capture and must not include D labels, expected expression labels, scoring hints, or result prompts
inside user-visible text.

Any local or public source text serialized into trace rows becomes evidence artifact content. Future download/capture
tasks must choose one of these privacy modes before row creation:

- `hash_only`: trace rows store only text hash and source id; raw text stays in a local source cache.
- `redacted_excerpt`: trace rows store a minimized, redacted text excerpt plus full text hash.
- `raw_local_only`: raw text is stored only in local artifacts with no upload or remote publication.

Sources containing obvious PII, private identifiers, account data, or sensitive personal details must be redacted,
excluded, or held for operator review before capture.

## Bounded Audit

- real objective: convert the operator's authorization into an auditable source/capture design without overclaiming
  existing chat logs or public corpora as capture evidence.
- strongest baseline explanation: external dialogue text may still be easy for same-access controllers to reproduce if
  the scored D channel is narrow or prompt distribution is weak.
- strongest invalidity risk: treating historical local logs or public corpora as if they were newly captured
  `CREATURE_ON` desktop rows.
- falsifier for this framing: a future design that cannot distinguish source provenance, desktop trigger provenance,
  and replay-row provenance.
- evidence still insufficient: no new `CREATURE_ON` capture, same-access run, score, comparison, or verdict exists.
- mechanism vs resemblance: this task designs data provenance and capture requirements only; it does not test mechanism.
- hard-coding/leakage check: source text must be frozen before capture; no expected D labels, target expression labels,
  or heldout outcome hints may enter source rows.
- local optimum / Zeno check: do not repair synthetic prompt packs again; use local/operator/public real source text
  only if it improves provenance and distribution, and still stop at same-access saturation if fair baselines match.
- weak-baseline check: public datasets do not replace the full-public-history same-access steelman requirement.
- claim-inflation check: even real source text plus desktop trigger only yields capture evidence, not attribution or
  mechanism evidence.
- stop condition: any attempt in this task to download gated data, accept third-party terms, capture rows, run
  same-access baselines, score, compare, update program state/evidence ledger, push, tag, or remote-anchor.
- rollback plan: delete this task directory, remove `EGODESKTOP-GABLATION-014` from `Tasks/TASK_BOARD.yaml`, restore 010
  and 013 next-action text, and regenerate route-convergence views.

## Task Card

- problem definition: clarify and bound "real desktop-chat-turn capture" after operator authorization to use local and
  public dialogue sources.
- current stage/layer: `engineering implementation / data provenance and capture design`.
- mainline target: future explicit-flag EgoDesktop capture through `window.egoDesktop.sendChatTurn(...)` and the existing
  G-ABLATION trace tap/writer.
- enabled-state requirement: no default runtime enablement; future capture requires explicit flags and a later accepted
  preregistration boundary.
- real-trigger evidence requirement: future rows must be produced through the real EgoDesktop chat-turn path and existing
  writer; this design card has none.
- hypothesis: separating source-text realism from desktop-trigger realism prevents both synthetic prompt-pack collapse
  and false evidence promotion from offline logs.
- strongest baseline: full-public-history same-access controller over all public source text and calibration rows.
- ablation requirement: none in 014; future card must still include `CREATURE_ON`, `CREATURE_OFF/FROZEN`,
  `OFF_STATIC_REPLAY_HELDOUT`, and same-access battery.
- trace/replay requirement: none in 014; future capture rows must serialize source id/hash, source license tier,
  desktop trigger metadata, condition, split, state, public inputs, adapter output, and replay inputs.
- computed-evidence provenance gate: no score or verdict is produced; provenance is local artifact readback and
  source-license metadata checks.
- acceptance gate: source tiers are defined, local artifacts are classified, public candidates are license-gated, and no
  capture/scoring authority is introduced.
- claim ceiling: real source capture design only.
- stop condition: capture/scoring/remotes/gated data terms inside this task.
- rollback plan: remove 014, restore previous task-board text, regenerate route-convergence views.
- expected changed files:
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-real-source-capture-design-v0/`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- forbidden changes:
- no dataset download in 014;
  - no gated dataset access or terms acceptance;
  - no `CREATURE_ON` row capture;
  - no synthetic prompt-pack v3;
  - no same-access baseline execution;
  - no scoring, comparison, verdict, or route advancement;
  - no default runtime enablement;
  - no `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update;
  - no push, tag, or remote anchor.
- Auto-Remote-Anchor decision: forbidden.

## Acceptance Gate

This task is accepted only if:

- "real" is explicitly split into source text, desktop trigger, and replayable capture row.
- Existing EgoDesktop/EgoOperator data is admitted only at the correct tier.
- Blocked or superseded post-hoc capture artifacts are preserved only as negative evidence and are excluded from future
  source manifests and capture/calibration bases.
- Public data candidates are license/provenance gated and not silently downloaded.
- License tier meanings for non-commercial, attribution, share-alike, gated, and unknown sources are operationalized.
- B-011 split/meta leakage, effective independence, and affect/anti-degeneracy failures are carried forward as mandatory
  real-source preregistration gates.
- Operator-authored demand-characteristic risk and PII/privacy minimization are recorded for future source manifests.
- Future capture remains a separate task with explicit flags and preregistration.
- Local route checks pass.
- Independent review returns no blocking findings before any follow-up data download/capture task.

## What This Can Prove

Only that the next real-source capture path is specified and bounded after operator authorization.

## What This Does Not Prove

This does not prove `CREATURE_ON` effect, same-access saturation, baseline score, candidate attribution, route
advancement, product benefit, runtime integration safety, stable user benefit, durable memory efficacy, agency, emotion,
subjectivity, consciousness, alive status, or Bar-2 specialness.

## Next Minimal Closed-Loop Action

Open a separate source-manifest/download-boundary task. That task may build a source manifest and optionally download
only license-compatible, non-gated public datasets into a local source cache. Do not capture or score until a later
preregistered capture design is accepted.
