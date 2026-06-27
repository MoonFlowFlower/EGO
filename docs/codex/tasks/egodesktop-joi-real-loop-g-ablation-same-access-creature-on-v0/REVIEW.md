# EgoDesktop Joi Real-Loop G-ABLATION Same-Access + CREATURE_ON v0 Review

- reviewer: `desktop_claude_source_limited`
- review_input: `010 card draft after local docs-only creation`
- verdict: `BLOCKING_FINDINGS`
- reviewed_scope: `task card/design only; no implementation or artifact execution reviewed`
- current_layer: `engineering implementation / decisive comparison design`
- claim_ceiling: `egodesktop_real_loop_g_ablation_same_access_creature_on_task_card_only`

## Blocking Findings

### B1 - Baseline Saturation Lacked Statistical Definition

Claude found that `baseline_saturated_stop` was treated as an equivalence conclusion without a predeclared equivalence
boundary, power target, minimum sample size, or TOST/equivalent decision rule. The repair requires epsilon, power, MDE,
minimum n, and an equivalence test before any saturation claim. Underpowered equivalence must route to repair/blocker,
not closure.

### B2 - Same-Access Battery Was Too Weak

Claude found that the first card capped the same-access battery at short-context or low-capacity controllers. The repair
requires a high-capacity full-public-history same-access steelman learner, or a computed low-order Markov upper-bound
proof showing that the short-context controllers upper-bound the candidate D path.

### B3 - Missing Capture-Before Preregistration Review Gate

Claude found that threshold, prompt-pack, baseline-battery, epsilon, and minimum-n freezing were deferred into a
post-review implementation plan without an independent checkpoint before `CREATURE_ON` capture. The repair requires a
hash-frozen preregistration manifest and independent source-limited review before any capture, scoring, or verdict.

## Advisories Accepted For Repair

- Add a creature-to-D mechanism-presence positive control before interpreting same-access equivalence.
- Add semantic near-duplicate leakage scanning with a positive-control paraphrase case.
- Clarify that independent same-access controllers mean independent callable implementation paths, not independent
  authorship.
- Complete the outcome-blind verdict matrix for the case where the candidate is worse than the static replay floor.

## Repaired Next Action

The repaired card was sent back to desktop Claude for source-limited re-review.

## Re-Review Verdict

- verdict: `NO_BLOCKING_FINDINGS (source-limited)`
- scope: `repaired 010 card/design only`
- accepted repairs: `B1`, `B2`, `B3`, `A1-A4`
- status caveat: this is not implementation approval for capture/scoring; it only permits a separate preregistration
  manifest slice.

Claude's next minimal action: open a separate preregistration-manifest slice that freezes epsilon, power, MDE, minimum
n, prompt packs, baseline battery, verdict matrix, and hashes, then send that manifest for independent source-limited
review.

`CREATURE_ON` capture, same-access execution, scoring, verdict, program-state update, evidence-ledger update, push, tag,
and remote anchor remain forbidden.
