# STATUS — EGO V2 transfer mechanism 001M

- Status: completed_with_bounded_transfer_negative
- Base HEAD: `b94c61b6f74be9f2f86a67e74437e0850d82be39`
- Branch: `codex/ego-v2-transfer-mechanism-001m`
- Product default: unchanged within-world Bayesian posterior
- 001L product qualification consumed: no
- Original 001J heldout consumed: no
- New 001M qualification consumed: no
- Candidate 1: early gain `-0.836750`, 7/16 positive worlds.
- Candidate 2: early gain `-1.773000`, 3/16 positive worlds.
- Candidate 3: early gain `-1.752375`, 3/16 positive worlds.
- Within-world scratch effect-sign accuracy: `1.0`; history shuffle reduced it
  to `0.35-0.36875`, and no-update to `0.0`.
- Confidence capping reduced negative transfer relative to uncapped priors but
  did not make any legal candidate positive.
- The valid evaluator-owned latent-alignment reference improved early AUC by
  `1.498375` versus scratch. Candidate state and the candidate wrapper were not
  used; this is a diagnostic upper bound, not learner evidence.
- Independent row recomputation, leakage/tamper controls and protected artifact
  readback: pass.
- The initial diagnostic rows are preserved but invalidated because a TDD audit
  found `HISTORY_SHUFFLE_FAST_META_PAIRING_BYPASS`. Final numbers above are from
  the repaired `history_shuffle_wiringfix` run of the same three candidates.
- The latent-alignment arms embedded in both search runs are also invalid as
  diagnostics because alignment entered candidate state. They never affected a
  gate. `latent_alignment_reference_result.json` is the corrected evaluator-only
  reference; the failed external-geometry reference attempt is also preserved.
- Terminal verdict:
  `WITHIN_WORLD_LEARNING_ESTABLISHED_COMPOSITIONAL_TRANSFER_STILL_ABSENT`.
- Next frontier: do not consume qualification or tune these three candidates;
  keep the within-world Bayesian posterior as the product default.
