# Reliability revision — execution ledger

Latest 2026-09-23 21:03Z: bounded offline protocol review delivered in ACCEPTANCE_PROTOCOL_REVIEW.md. Automatic semantic gate remains failed; campaign stopped with470 cumulative requests, no new calls this turn. automation-3 PAUSED pending the user's protocol choice. Recommended limited development-only action exploration is a proposal, not authorized execution or product acceptance. Historical logs below remain unchanged.

Authority: user-approved reliability plan, 2026-09-23. Real model calls in simulated life only.

## Work packages
- [x] R1 Atomic simulated action, outbox, checkpoints, resumable indexing, source/lesson invalidation.
- [x] R2 Immutable inference profiles, durable campaign budget, explicit 429 rotation.
- [ ] R3 Ragas 0.4.3 integration implemented and component-tested; Chinese calibration BLOCKED (11/12 after one bounded repair).
- [x] R4 Official ACE per-entry provenance, frozen artifact validation, report integration.
- [ ] R5 Regressions, real probes/smokes, review, report and task board delivered; memory/growth formal comparisons NOT RUN due to calibration gate.

## Decisions and evidence
- Existing project root has no Git repository. Work stays in memory_lab; retain old experiment data and record file hashes instead of making an unrelated repository/worktree.
- Shared interfaces: R1 durable steps feed R3 receipt audit; R2 profile and budget identity feed all calls, R4 frozen training, R5 pairing. Actor/ACE never receive evaluator verdicts or hidden answers.
- 429 rotation abandons the whole inference-profile comparison and restarts all arms. Global limit 5000 attempted requests includes probes, semantic evaluation and abandoned batches.
- Request timeouts with unknown completion/billing stop the campaign; never replay paid requests speculatively.
- Source dependency is conservative: a generated lesson depends on all material supplied to its generation, not merely IDs the model chooses to cite.
- No changes to original SharedField, personal saves, or vendor algorithm files. No model-weight training, fourth memory backend, UI, or machine control.

## Research evidence (read, not independently reproduced)
- AWS transactional outbox: https://docs.aws.amazon.com/en_en/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html — established dual-write pattern; consumers still need idempotency.
- FActScore: https://aclanthology.org/2023.emnlp-main.741/ — atomic factual claims evaluated on biographies, not pet interaction.
- Ragas faithfulness: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/ — implemented claim decomposition/support checking; Chinese life calibration required.
- ACE paper: https://arxiv.org/abs/2510.04618 — reported agent/task gains, no proof of companionship.
- ACE pinned playbook_utils.py: UPDATE/MERGE remain commented out; ADD is implemented. Local code inspected.
- LongMemEval: https://arxiv.org/abs/2410.10813 — useful update/abstention test categories, not proactive-life validation.
- Graphiti issue 1837: https://github.com/getzep/graphiti/issues/1837 — upstream user report of deleted source surviving in summary after restart; not independently reproduced here, supports keeping a regression case rather than assuming graph deletion solves provenance.

## Execution log
- Started: inspected existing runner/provider/core/ACE and test suite. Services remain stopped pending offline regressions.

- R1/R2/R4 implementations now pass regression tests; 42 offline tests pass. Runner resumes committed actions without a second model call.
- R3 Ragas 0.4.3 imported and official prompts exercised with a fake transport; false fact returned unsupported. Real Chinese calibration pending.
- Ruling: pin LangChain 0.3.x compatible modules in isolated evaluator; unconstrained latest LangChain breaks Ragas 0.4.3 import. Full transitive hashes saved.

- Independent review found five concrete gaps: received-reply replay; stale-learning laundering; deletion delivery loss; semantic profile/cache mismatch; native clone target collision. All corrected; bounded follow-up cleared those findings.
- 50 offline tests pass; isolated Ragas 0.4.3 official components load with compatible pins. Actual inference compatibility still requires per-profile probes/calibration.
- DeepSeek and Qwen3.7 each passed probes and native backend smokes, then hit 429 during calibration. Both archived; cumulative budget retained; Qwen3.5 next.

- Qwen3.5 passed three backend smokes but original Ragas adapter calibration was 8/12: four fabricated statements produced empty extraction and were incorrectly accepted. No formal comparison started. Root cause: verification instructions were supplied during extraction and our adapter treated empty extraction as supported, unlike upstream NaN.
- Ruling: repair this integration defect, keep Qwen3.5/profile and the SAME budget, preserve failed calibration, permit ONE explicit --repair-calibration replay. Extraction now separates claim identification from truth judgment; empty extraction invokes bounded whole-text NLI instead of passing. New isolated-component regression observed RED then GREEN. No quality-based model switching or unlimited prompt tuning.

- Final bounded repair: Qwen3.5 11/12 calibration examples match; all six negatives rejected, future-intention positive falsely rejected. No semantic-baseline-pass claim. No further model switching based on quality or paid retries.
- Final verification: main suite 52 tests (51 pass, 1 isolated-dependency skip); isolated official Ragas component test passes. Native backend smokes 9/9 across 3 profiles. Independent review findings corrected; formal memory 0/216 and growth 0/144.
- Campaign stopped at calibration; 82 total attempted calls, 80 successful, 2 HTTP429 failures; known USD 0.00451975, 2 unknown-billing failures. Services stopped, data retained. No memory winner or ACE-benefit claim. Current report: REPORT.md; raw calibration and calls retained.
- Next work: validate Chinese intention/fact distinctions with fresh blinded cases before another formal campaign; do not keep tuning to these twelve cases. A new campaign must freeze the repaired implementation/scorer and rebuild all candidates. Current campaign remains closed.

## 2026-09-23 authorized continuation: fact-scope revision
- User explicitly agreed to continue after the calibration stop. Ruling: permit one named scorer revision (`scope-v2`) of the same Qwen3.5 profile; archive the closed campaign state, use new batch/run/smoke paths, retain the original budget.sqlite and 82 attempted requests. Earlier 429 profiles remain closed. This is a scorer repair, not score-driven model substitution.
- Research: VeriScore (https://aclanthology.org/2024.findings-emnlp.552/ ; official code https://github.com/Yixiao-Song/VeriScore) distinguishes verifiable claims from subjective/hypothetical content. Borrow the applicability distinction; do not import its web-search exclusion of private experiences: shared experiences ARE factual here and need local evidence. Ragas faithfulness remains the factual extraction/NLI component, not a validator of desires.
- Ruling: classify exact original-text segments as factual/nonfactual/uncertain; require complete ordered byte-equivalent text coverage (Unicode string equality), reject missing/ambiguous spans. Only then run official Ragas decomposition and NLI on factual spans. Empty factual extraction still receives full-span NLI. Model classification remains fallible; no rule that any sentence with “想” automatically passes.
- New fixtures are evaluator-only, authored independently after implementation; labels never enter model prompts. Keep all twelve old regression examples as well. Freeze scorer+fixture hashes before calls; one prospective pass, no tuning to new failed cases this round. New formal comparisons only after all required calibration cases match.
- Offline RED→GREEN evidence: scope-red-tests.txt, scope-green-tests.txt; explicit revision keeps budget and archives failure. No training, fourth memory backend, UI or original runtime changes.

- Review finding: exact scope coverage did not prevent a nonempty Ragas extraction from dropping another factual span. Fixed by adding every original factual span to the NLI statement list alongside its decomposition, without adding a separate model call. Counterexample observed failing then passing; empty/nonempty extraction omissions share this coverage protection.

- scope-v2 prospective result: 24/28; original regressions11/12, independent new cases13/16. All14 negative examples rejected. Four false rejections were generated by referent mismatch: raw-text I/you interpreted from evaluator viewpoint; extraction replaced I inside user quotations with desktop pet; abstention falsely required proving the declared speaker exists. Cumulative163 calls,161ok/2old429, knownUSD0.01086453,2unknown fees. No formal comparison.
- Ruling after new evidence: stop that revision and preserve all failed cases as exposed regressions. The observed problem is missing utterance reference-frame metadata and a globally applied first-person replacement, not evidence that memory systems fail. One further bounded representation correction (`frame-v3`) carries speaker/addressee/quote-local referents through ALL three components, retains complete original factual spans and existing gates. This changes the input representation, not gold labels or thresholds. A different fresh independent16-case challenge is required; no rebranding of the exposed set as blind, no quality-driven model hopping. If unresolved after this pass, stop further automatic scorer repair and report the representation/verification limits.
- frame-v3 reuses saved successful compatibility probes only when the entire inference configuration matches; Qwen3.5 already has6 direct probes, so no additional direct probes. Native smoke may rerun; all costs remain on the same5000-request ledger. Original12 + exposed16 + fresh16 =44 cases. Prompt/model outputs stay isolated from actor/ACE.

- frame-v3 frozen real result:41/44 (original12/12, exposed15/16, independent new14/16); all22 negatives rejected. Three false rejections: NLI was asked to treat factual scope fragments such as “你说过：” or a dangling attribution clause as standalone claims. Scope and grammatical claim boundaries differ. Result does not support product adoption or memory/ACE selection.
- Bounded paid execution stopped as committed. Deterministic post-run fix coalesces adjacent factual scope segments before decomposition/NLI, preserving quote and modifier context while still verifying all original factual text. Offline counterexample RED→GREEN; NO new real-model calibration after this change. Frozen real-tested semantic.py saved as evidence/semantic-frame-v3-tested.py, with old scorer hash; current hash differs. Do not present41/44 as current-code verification.
- This turn added205 calls; entire original campaign287 attempts (285ok,2 earlier429), knownUSD0.023624485 and2unknown fees. Same5000 global budget; Qwen3.5 direct probes remain6, DeepSeek3,Qwen3.7 3. Native backend smoke total15/15 across versions, not independent efficacy measurements. Formal memory0/216,growth0/144. Services stopped and all records retained.
- Next meaningful validation: test deterministic assembly with a new frozen evaluator-only set before formal comparison. All44 now exposed and only regression data. No inference that the memory backends or ACE are ineffective; the blocked component is semantic evaluation integration. No automatic fourth scorer run this turn.

## Authorized next item: fragment-v4 calibration then formal comparison
- User explicitly requested continuation. Resume the same reliability-01 campaign via a named new revision; preserve closed frame-v3 state and287 attempted calls. Reuse identical successful probes, keep new batch/stores. No runtime/learning/prompt changes for this validation beyond the already completed deterministic adjacent-fragment assembly fix.
- One prospective new16-case challenge plus all44 exposed regression cases; scorer/fixture hashes frozen before API calls. Independent reviewer authors the new set without reading existing calibration or heldout contents. Synthetic independent-context authorship is not independent human annotation.
- If the frozen gate passes, campaign proceeds directly to original12-development/24-heldout memory comparison and same-backend frozen/ACE comparison. Existing5000 cumulative request cap and explicit429 rules still apply. Report existing failures and current-version evidence separately.

## fragment-v4 outcome and closeout
- 56/60 calibration cases completed;53 exact matches against unchanged frozen labels. Prior three fragment false rejections all passed. Provider returned nested502 at case57; no automatic retry/rotation, remaining4 incomplete. Formal memory/growth still0.
- Author adjudication identified unjustified inventory/backpack aliases in09/11 gold. Preserve labels and original metrics; post-exposure errata is not blind passing evidence.11 also ignores a real successful eat receipt in its rationale; frame-v3-04 safely abstains. Full semantic gate not passed.
- Fix durable nested completion error classification and partial-report denominators. RED→GREEN regressions;59 main tests pass,7 isolated tests skipped here and previously passed in eval environment. Independent closeout review11/11, no blocking findings.
- Offline reconciliation preserves raw response/usage; backed up original receipt/status/STOPPED and SQLite ledger, records SHA256.446 total attempts,443ok/3error, knownUSD0.03986857,2 unknown-billing prior429. No paid calls during reconciliation.
- New observed error and ambiguous samples require an explicit bounded recovery/revalidation design, not deletion of failures, automatic retry, score-driven switching, or bypassing evaluation. Do not claim memory/ACE benefits.
