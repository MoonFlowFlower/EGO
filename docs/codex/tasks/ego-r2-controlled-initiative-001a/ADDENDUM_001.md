# ADDENDUM-001 — EGO-R2-CONTROLLED-INITIATIVE-001A — G-P0-DEGEN threshold-source correction

type: delta-supersede, single frozen constant (Red-tier threshold motion,
flagged; commit-order = this addendum must be an ancestor of any run it
gates)
parent_card: docs/codex/tasks/ego-r2-controlled-initiative-001a/STAGE_CARD.md
  (pin cfb652da80b16a9a5feffa64ab56c42cba9caf91a273bcdeee13976a80c34ac5 —
  card text otherwise UNCHANGED and still prevails)
trigger: banked P0 failure `instrument_invalid_part0`
  (commit 3cea41ba704d1e5a4936b1baeeffc3611f5fdb92, failing gate
  G-P0-DEGEN, observed always_act mean = -0.12148)
operator_approval: Zhouyu (Leo) / 2026-07-07   <- Codex MUST verify this line is
  filled (non-empty name + date) before landing; empty = STOP

## 1. What changes (exactly one row of the threshold_source table)

OLD: degenerate gate | always_silent == 0; always_act <= -0.2
NEW: degenerate gate | always_silent == 0; AND always_act mean <= -0.06 AND its 95% CI upper bound < 0
     (95% bootstrap CI, same frozen method as card §5: 10k resamples, seeded)

Nothing else changes: no other gate, floor, grid, seed, env constant,
candidate constant, kill condition, or ceiling moves. The env-revision grid
remains unconsumed. Candidate code remains untouched (P0 is candidate-free).

## 2. Grounds (structure-derived, not result-tuned)

The original -0.2 traces to a card-time derivation error, not an environment
defect: the drafting arithmetic assumed acts on neutral ticks (s=0.35) would
trigger annoyance cascades; the FROZEN dynamics trigger annoyance only at
s<0.30, so neutral spam costs -0.16/act and no cascade. Closed-form
expectation from the frozen constants: windows 20 acts x (+0.88) = +17.6;
dip 10 x (-0.92) = -9.2; post-dip suppressed tail ~3 x (-0.92) = -3.1; clean
neutral 50 x (-0.16) = -8.0; total ~ -2.7 raw / 18.48 = ~ -0.14 normalized
(band -0.12..-0.15 across cooldown phase alignments). The observed -0.12148
sits inside the analytic band — the instrument behaves exactly as designed;
-0.2 was unreachable ex ante under the frozen dynamics.

The corrected bound is derived from that same structure: -0.06 = one half of
the analytic expectation magnitude (sampling margin), plus the CI-upper<0
condition making "spam is materially harmful" a statistical requirement
rather than a point guess. It is NOT chosen to admit any candidate result:
G-P0-DEGEN is a candidate-free sanity gate; no candidate number exists yet;
held-out seeds remain unburned.

## 3. What the gate still certifies

always_act must be materially and significantly below always_silent (0),
i.e. the environment's false-positive asymmetry is real and a spam policy
cannot be confused with a viable one. At -0.12 normalized this is ~2.2 raw
utility points lost per episode versus silence.

## 4. Accounting

- This consumes the ONE rework round for the finding
  "G-P0-DEGEN threshold miscalibration" (one-round rule). If the rerun
  fails G-P0-DEGEN again, STOP: no second correction; the route decision
  (env-revision round per card §5 grid, or feasibility stop per K-D) goes
  back to the operator with Claude review.
- The banked v1 failure artifacts are evidence and remain untouched.
- Claude authored this correction and owns the original derivation error
  (same failure family as the pre-registered "gate cannot reach its target
  by design" class; the card-time ablation identity audit missed it).
