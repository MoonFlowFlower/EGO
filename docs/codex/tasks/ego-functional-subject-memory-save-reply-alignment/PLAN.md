# Plan

1. Remove forget/delete/revoke wording from the save-success scoped fallback.
2. Tighten the memory-save rewrite instruction so it does not suggest removal paths for a save request.
3. Add regression assertions that the repaired reply keeps the target principle and does not include `/forget` or `撤销`.
4. Verify the Functional Subject classifier no longer flags the repaired reply.
5. Run targeted runtime/eval tests and scoped diff check.
