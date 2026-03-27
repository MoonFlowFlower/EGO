| event_type | psi_bucket | action_signature | outcome_signature | mode_signature | closure_signature | closure_family_id | repair_closure | reflection_trigger | preferred_mode | sample path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `tool_result` | `runtime:tool_result:general:risk_high` | `tool:file` | `blocked` | `exploration` | `3e728db79c906f48` | `6824edaf39136534` | `false` | `drive_spike` | `ask` | `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260326_230059_8ded092c` |
| `tool_result` | `runtime:tool_result:general` | `tool:file` | `success` | `exploration` | `f92efd86648b35ec` | `7a053f9ff7c61219` | `false` | `drive_spike` | `ask` | `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260326_230231_74277be4` |
| `tool_result` | `runtime:tool_result:general` | `tool:file` | `success` | `exploration` | `f92efd86648b35ec` | `7a053f9ff7c61219` | `false` | `drive_spike` | `ask` | `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260326_230256_0fbd5ecc` |

## Diff Readout

- `action_signature` is stable across all three real samples: `tool:file`.
- `mode_signature` is also stable across all three real samples: `exploration`.
- `closure_signature` correctly splits `blocked` vs `success`.
- `closure_family_id` also splits, which violates the intended same-family behavior.
- The only coarse-grained family input that differs across blocked/success is `psi_bucket`, where the blocked sample appends `:risk_high`.
- `repair_closure` remains `false` even on the retry-success sample, so the real retry chain is not being recognized as a repair closure.
