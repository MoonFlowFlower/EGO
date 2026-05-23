# Plan

1. Add output guards for authorized reminder, high-risk destructive request, and topic-switch continuity replies.
2. Add a tool-loop intercept for low-instruction initiative requests that try to use `update_todos` instead of answering with one bounded next action.
3. Add deterministic regression tests for all four failure modes from the latest EGO-FS-010 run.
4. Run EgoOperator and Autopilot regression profiles.
5. Rerun EGO-FS-010 full real-provider smoke after local acceptance.
