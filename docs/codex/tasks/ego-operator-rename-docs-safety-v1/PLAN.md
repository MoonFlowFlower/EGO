# EgoOperator Rename + Docs Reader Safety Pass v1 - PLAN

## Stage Card

- Stage: `ego_operator_first_transition`
- Hypothesis: a name/path transition plus reader-safety banners makes the current operator route clear without touching legacy runtime code.
- Change surface: `EgoOperator/**`, current authority/docs/scripts, generated route/state views, and selected banner-only old docs.
- Claim ceiling: `EgoOperator naming/docs safety transition recorded`.

## Steps

1. Move tracked `Ego_handmade/**` runtime files to `EgoOperator/**`.
2. Update runtime constants, schemas, prompts, tests, and report labels to `EgoOperator` / `ego_operator`.
3. Update current authority docs, route scripts, program state, and evidence ledger.
4. Add top reader-safety banners to high-risk old entry docs without rewriting historical content.
5. Regenerate derived views and run targeted static/runtime/governance checks.
6. Stage only the scoped transition diff, commit, and push.

## Rollback

Use one revert of the task commit, or move tracked files back from `EgoOperator/` to `Ego_handmade/` and revert the docs/state/script naming changes.
