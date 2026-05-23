# Plan

1. Add a terminal reply formatter for destructive proposal blocks.
2. Detect `destructive_command_requires_inventory_first` immediately after tool execution and return without another LLM call.
3. Add deterministic regression for a blocked destructive proposal after read-only inventory.
4. Run targeted and full verification.
5. Rerun the 20-sample Functional Subject smoke to check whether `fs_08` no longer reports provider failure.
