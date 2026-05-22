# Plan

1. Add a case-local `policy_patch_setup` field to fs_19.
2. Teach the Functional Subject trial runner to seed repeated failure observations from that setup.
3. Include setup evidence in the case result and GPT-5.5 judge packet.
4. Add deterministic regression proving setup emission and replay count.
5. Run targeted tests and `autopilot_full`.
6. Mark `EGO-FS-013` accepted and return to `EGO-FS-010` for the next real-provider judge rerun.

## Rollback

Remove `policy_patch_setup`, setup seeding, setup evidence serialization, tests, docs, and board status changes.
