# PREREG_ADDENDUM_003 — ego-pet-capability-conformance-001a — capability #3 (C-forage / prediction-error), honest decomposition

> Ex-ante pre-registration for capability-slice #3 of task `ego-pet-capability-conformance-001a`. All thresholds, seeds, intervention geography, metric definitions, and the verdict rule below are **frozen at the commit that banks this file**. This commit MUST be an ancestor of the #3 harness and of any gated run it judges (commit order = un-backdatable ex-ante proof). Changing any frozen value requires a NEW addendum that is itself an ancestor of the re-run. **No post-hoc tuning.**
>
> Kept a slice of task 001a (not a new task_id) so the existing `MUTATION_SCOPE.yaml` covers all paths (no new scope declaration). Does NOT edit or reinterpret `PREREG_ADDENDUM_001/002`, the 001 `INSTRUMENT_INVALID` bundle, or the `repair_001` bundle — those remain the preserved lineage record. New artifacts go under `artifacts/ego-pet-capability-conformance-001a/pe_forage_003/`.

## 0. Design premise (from a frozen-code reading — this is why #3 is a DECOMPOSITION, not an "adaptation" claim)
Two facts about the frozen pet code shape this card:
1. **`last_prediction_error` is set OUTSIDE the `if updates_enabled:` guard** (`creature.py:172`), and `frozen_updates` is **not** special-cased in `select_action` — it falls through to the same `if last_prediction_error > trigger: observe` path (`creature.py:110-119`). ⇒ **the PE→re-observe pathway is NOT update-gated**: `candidate`, `frozen_updates`, and `candidate_ablated` all compute PE and all re-observe on high PE. Ablation does NOT remove it.
2. The re-observe trigger `_derived_prediction_error_trigger(config)` (`creature.py:66-75`) is a **fixed constant derived from config drift magnitudes** (partial schedule knowledge; P0-audit B2), and the forage update `model[site]=actual` (`creature.py:168-171`) is a **direct single-site overwrite**, not inference.

Therefore #3 certifies a **decomposition of two separable, separately-gated facts**, each with a mandatory disclosure, and explicitly records that **the frozen code contains no update-gated adaptation mechanism in this pathway**:
- **(P) PE-reflex** — the prediction error is genuinely computed and is load-bearing for the re-observe decision (vs a rate-matched, PE-blind schedule), BUT it is a **fixed-threshold reflex that is NOT ablation-sensitive** (it survives `updates_enabled=False`).
- **(W) Forage-write** — the single-site experiential model write is directional and **ablation-sensitive** (the experiential analog of #1's oracle write; still a direct write, not inference).

## 1. Frozen inputs
- World: `world_config_v0.json` (read-only); 600 ticks; R0[0,199]/R1[200,399]/R2[400,599]; 6 sites; designations derived + asserted (as in #1).
- Frozen mechanism under test (import-only): `select_action` (PE-observe trigger), `update_creature_after_feedback` (PE computation `|pred−actual|`, forage single-site write, `last_prediction_error`), `_derived_prediction_error_trigger`, `_best_site`, `_prediction_for_action`.

## 2. Arms
- `candidate` (updates_enabled=True).
- `frozen_updates` (updates_enabled=False) — write-control; **predeclared to still show the PE-reflex** (re-observe contingency), write absent.
- `static` (needs-only `static_policy_action`) — PE-blind (never PE-observes) and write-blind. Control for both P and W.
- `candidate_ablated` (candidate, updates forced False) — write-ablation arm; **predeclared to still show the PE-reflex**, write absent.
- `schedule_reobserve` (NEW harness arm, not frozen code) — re-observes on a deterministic, per-seed schedule whose marginal observe rate is matched to the candidate's, and whose observe decisions are **independent of the induced PE** (PE-blind). The primary falsifier for sub-claim P. Otherwise forages `_best_site` like the default policy.

`schedule_reobserve` construction (frozen): measure the candidate arm's marginal observe rate ρ on the same seed's baseline run; realize a fixed-phase periodic observe schedule with period `round(1/ρ)` (deterministic, PE-blind), offset so the intervention tick t is NOT a scheduled observe (so any observe at t+1 cannot be the schedule "coincidentally" firing). This makes the discriminative signal the CONTINGENCY on PE, not the rate.

## 3. Seeds (fresh, disjoint; assert fail-closed)
- Dev probe: `1107` (fresh; run first).
- Scored: `M=20`, seeds `5101…5120`; assert disjoint from ALL prior reserved blocks: S_dev 1101-1107, P0 scored 2101-2120, capability-001 scored 3101-3120, capability-repair 4101-4120. Fail closed otherwise.

## 4. Intervention protocol (matched pairs on FORAGE feedback; harness supplies variants; frozen pet code unchanged)
Scored intervention points: the candidate's **first `forage_energy` and first `seek_comfort` in each regime** (R0/R1/R2), tick t. Share world+seed+state to t; then run A/B/C forward. The harness modifies the `feedback["action_yield"]` passed to `update_creature_after_feedback`; frozen code is never edited.

- **Pair A (real)**: `action_yield` = the true site yield.
- **Pair B (prediction-matched, PE≈0)**: `action_yield` = the arm's own model prediction for the visited site (`model[s]` per-arm) → PE = 0 → must NOT PE-trigger a re-observe, and no model change.
- **Pair C (prediction-divergent, directional)**: `action_yield` = a frozen value set so that (i) `|pred − actual| > trigger` (crosses the fixed threshold → PE-reflex should fire), AND (ii) the visited site's post-write score makes `_best_site(need)` move to a **pre-registered target site** that differs from the pre-intervention `best_site` (so the write pathway has an observable, de-degenerate directional effect). The harness derives the target from the config + current model and **asserts** `target ≠ pre_intervention_best_site` per scored intervention (fail-closed → INSTRUMENT_INVALID if degenerate).

## 5. Metrics
Deterministic, RNG-free where possible. `_best_site(model, need)` and `last_prediction_error` are deterministic functions of model + feedback.

**Sub-claim P (PE-reflex), k=1 (the PE persists exactly one tick — `last_prediction_error` is overwritten at the next action; disclosed):**
- Re-observe contingency per arm: `C(arm) = rate[ observe at t+1 | Pair C ] − rate[ observe at t+1 | Pair B ]`, over scored forage interventions × seeds.
- PE-fidelity per arm (integrity): `last_prediction_error` recorded at t equals `|pred − actual|` (energy+comfort L1) within 1e-9 for A/B/C.

**Sub-claim W (forage-write), windowed:** directional match over the persistence window `[t+1, min(t+50, next_overwrite_of_s − 1)]`:
- `W(arm) = rate[ _best_site(model, need) == pre-registered Pair-C target | Pair C ]`, per scored intervention × seeds.

## 6. Gates (thresholds frozen; inherited from the sound 001 G-A family — 0.60 discriminative / 0.05 floor — NOT read off any #3 run)
- **G-PE-FIDELITY**: for every scored intervention, all arms' recorded `last_prediction_error == |pred−actual|` within 1e-9. (Confirms PE is genuinely the prediction-error quantity, not a degenerate/constant/label.) Else → INSTRUMENT_INVALID.
- **G-P (PE-reflex load-bearing vs schedule)**: `C(candidate) ≥ 0.60`; `C(schedule_reobserve) ≤ 0.05` AND `C(static) ≤ 0.05`. **Predeclared (reported, NOT gated as failure):** `C(frozen_updates)` and `C(candidate_ablated)` are EXPECTED to be ≈ `C(candidate)` (high) — the reflex is not update-gated. This is the honest disclosure, recorded in the artifact; it is NOT a control-contamination failure.
- **G-W (forage-write directional + ablation-sensitive)**: `W(candidate) ≥ 0.60`; `W(candidate_ablated) ≤ 0.05` AND `W(frozen_updates) ≤ 0.05` AND `W(static) ≤ 0.05`. (The write IS update-gated → ablation removes it.)
- **G-D replay**: 2 fresh-process replays, 0 mismatches, all pairs.
- **G-E channel**: 100% of nonzero re-observe/divergence/directional records attributed to the disclosed channels — `C-PE` (re-observe reflex) or `C-forage` (single-site write); report the split; the report MUST restate the fixed-threshold and direct-write disclosures.
- RNG audit: fail-able AST audit with positive control retained; frozen import-only; no unseeded RNG (`schedule_reobserve` uses only deterministic scheduling or `consume_registered_rng`).

## 7. Verdict rule (frozen — names the decomposition and the no-adaptation finding)
- `PE_REFLEX_AND_WRITE_PRESENT_DISCLOSED` iff G-PE-FIDELITY ∧ G-P ∧ G-W ∧ G-D ∧ G-E all pass. Meaning: PE genuinely computed + load-bearing for re-observe vs a rate-matched PE-blind schedule (disclosed fixed-threshold reflex, NOT update-gated / NOT adaptation), AND the forage single-site write is directional + ablation-sensitive (disclosed direct write, NOT inference). **This is the maximal positive and it explicitly does NOT assert an adaptation mechanism.**
- `WRITE_ONLY` iff G-W passes but G-P fails (`C(candidate)` not separated from schedule) — the PE-reflex is indistinguishable from a rate-matched schedule.
- `PE_REFLEX_ONLY` iff G-P passes but G-W fails (write not ablation-sensitive/ directional — unexpected).
- `DEGRADES_TO_SCHEDULE` iff `C(candidate) − C(schedule_reobserve) ≤ 0.05` (the re-observe carries no PE-contingency beyond a matched-rate schedule).
- `CAPABILITY_ABSENT` iff both G-P and G-W fail.
- `INSTRUMENT_INVALID` iff G-PE-FIDELITY fails; OR G-D fails; OR G-E incomplete; OR any Pair-C target-degeneracy assertion fails; OR seed-disjointness fails; OR a PE-blind control (`schedule_reobserve`/`static`) shows `C > 0.05` (contingency contamination); OR a write-control (`candidate_ablated`/`frozen_updates`/`static`) shows `W > 0.05` (write contamination).

Note: `C(frozen_updates)` / `C(candidate_ablated)` being high is **explicitly not** an INSTRUMENT_INVALID trigger for sub-claim P — it is the predeclared reflex disclosure. (They ARE gated to ≤0.05 for sub-claim W.)

## 8. Predeclared failure geography (G3)
- Sub-claim W (write) MUST be absent (`W ≤ chance/0.05`) under `candidate_ablated`, `frozen_updates`, `static`, and Pair B; present only for `candidate` under Pair C.
- Sub-claim P (reflex) MUST be absent (`C ≤ 0.05`) under `schedule_reobserve` and `static`; present for `candidate` under Pair C-vs-B; and is PREDECLARED present for `frozen_updates`/`candidate_ablated` (reflex, not update-gated).
- PE-fidelity holds for all arms (PE is computed regardless of updates).

## 9. Artifacts + preservation
Under `artifacts/ego-pet-capability-conformance-001a/pe_forage_003/`: `result.json` (verdict + verdict_subtype + per-arm C(·) and W(·) tables + the reflex-survives-ablation disclosure + claim_ceiling + config_shas incl. PREREG_ADDENDUM_003), `trace.jsonl` (gate-scoped), `baseline_comparison.json`, `ablation_report.json`, `replay_report.json`, `channel_report.json`, `failure_manifest.json` if any fail. The 001/repair_001 bundles and PREREG_001/002 are preserved unchanged.

## 10. Claim ceiling (honest, binding)
Bounded offline evidence, under `world_config_v0` + seeds 5101-5120, that (P) the pet computes a genuine action-conditioned prediction error from forage feedback and this error is load-bearing for a subsequent re-observe decision that a rate-matched PE-blind schedule does not reproduce — via a **fixed config-derived threshold** and **NOT ablation-sensitive (a reflex, not adaptation)**; and (W) forage feedback drives an ablation-sensitive **single-site direct model write** that is directional to the injected content (not inference). **Explicitly records that the frozen code contains no update-gated adaptation mechanism in this pathway.** Proves NO learning, adaptation quality, world-modeling, understanding, uncertainty-driven behavior, self/agency/autonomy, subjectivity, emotion, consciousness, or EGO/companion readiness. A PASS here is a mechanism-proxy-COMPONENT characterization (prediction + error + reflexive use + experiential write), not an adaptation claim.
