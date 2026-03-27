# Sample Index

## Scope

Real Telegram samples used for P3 closure evidence audit.

## Primary Samples

### A. Root-cause fix verification

`artifacts/telegram_real_mainline_v1/real_telegram/sample_20260326_225946_3059c964`
- local time: March 26, 2026 22:59
- input: typo probe `读取 ... 前 1 行3`
- result: planning-timeout style waiting-input sample
- purpose: records the pre-clean probe after the host fix deployment
- completeness: full E4 sample

### B. Real blocked execute-task/tool sample

`artifacts/telegram_real_mainline_v1/real_telegram/sample_20260326_230059_8ded092c`
- local time: March 26, 2026 23:00
- input: `读取 D:\Project\AIProject\MyProject\Test\missing_closure_probe.md 前 1 行`
- outcome:
  - `action_signature = tool:file`
  - `outcome_signature = blocked`
  - `closure_signature = 3e728db79c906f48`
  - `closure_family_id = 6824edaf39136534`
- purpose:
  - proves explicit-path request is now treated as a direct real file read
  - provides the real blocked half of the closure split
- completeness: full E4 sample

### C. Real retry-success sample

`artifacts/telegram_real_mainline_v1/real_telegram/sample_20260326_230231_74277be4`
- local time: March 26, 2026 23:02
- input: `如果刚才失败了，现在读取 D:\Project\AIProject\MyProject\Test\CLAUDE.md 前 1 行`
- outcome:
  - `action_signature = tool:file`
  - `outcome_signature = success`
  - `closure_signature = f92efd86648b35ec`
  - `closure_family_id = 7a053f9ff7c61219`
- purpose:
  - first real follow-up success after blocked read
  - real retry chain evidence
- completeness: full E4 sample

### D. Real repeated-success sample

`artifacts/telegram_real_mainline_v1/real_telegram/sample_20260326_230256_0fbd5ecc`
- local time: March 26, 2026 23:02
- input: `再读取一次 D:\Project\AIProject\MyProject\Test\CLAUDE.md 前 1 行`
- outcome:
  - `action_signature = tool:file`
  - `outcome_signature = success`
  - `closure_signature = f92efd86648b35ec`
  - `closure_family_id = 7a053f9ff7c61219`
  - `closure_consistency_score = 1.0`
- purpose:
  - repeated success strengthening evidence
  - shows post-fix sample capture remains stable
- completeness: full E4 sample

## Secondary Reference Samples

### E. Earlier upgraded real sample with old host bug still present

`artifacts/telegram_real_mainline_v1/real_telegram/sample_20260326_223526_208ba3ca`
- input: `读取 ... missing_closure_probe.md 前 1 行`
- outcome:
  - `action_signature = tool:read_lines`
  - host still followed stale task flow
- purpose:
  - useful contrast sample showing the pre-fix contamination bug

### F. Earlier incomplete real samples caused by collector mixing

`artifacts/telegram_real_mainline_v1/real_telegram/sample_20260326_223755_238449d4`
`artifacts/telegram_real_mainline_v1/real_telegram/sample_20260326_223842_b8d9e1f2`
- purpose:
  - demonstrate the pre-fix evidence collector corruption pattern
- issue:
  - `normalized_event / openemotion / response_plan` missing

## Cross-Checks

### Proto-Self trace

`EgoCore/logs/proto_self_trace.jsonl`
- contains real host-chain entries for:
  - ingress closure fields
  - blocked `tool:file`
  - success `tool:file`

### Agent-global state

`EgoCore/artifacts/proto_self_store/agent_global/proto_self_state.v1.json`
- current relevant signatures:
  - `3e728db79c906f48` -> `tool:file / blocked`
  - `f92efd86648b35ec` -> `tool:file / success`
  - `6d2632f5abecd172` -> ingress user-request family used by the latest samples

### Session/thread continuity

`EgoCore/artifacts/proto_self_store/sessions/telegram_dm_8420019401/session.json`
`EgoCore/artifacts/proto_self_store/threads/telegram_dm_8420019401/thread.json`

These confirm:
- live thread continuity was preserved
- agent-global state was not wiped by `/new`
- no migration event was required for this round

## Quick Verdict By Sample

`sample_20260326_230059_8ded092c`
- supports Q1
- supports Q2 blocked half
- supports execute-task mainline evidence

`sample_20260326_230231_74277be4`
- supports Q1
- supports Q2 success half
- supports retry path observation

`sample_20260326_230256_0fbd5ecc`
- supports Q1
- supports repeated success strengthening

## Important Limitation

No real sample in this round showed:
- `repair_closure = true`

So the retry path is real, but formal repair-closure recognition is still absent.

