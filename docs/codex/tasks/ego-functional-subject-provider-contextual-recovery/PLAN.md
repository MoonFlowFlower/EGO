# Plan

1. Add contextual provider-error recovery inside the tool loop exception path.
2. Reuse existing topic-continuity and policy-replay renderers instead of creating new templates.
3. Add deterministic regressions for `fs_10` and `fs_19` provider-error paths.
4. Run targeted and full verification.
5. Rerun the 20-sample Functional Subject smoke and inspect GPT-5.5 judge output.
