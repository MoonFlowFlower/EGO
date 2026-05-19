# LLM-in-Loop Whole-Chain Sampling - STATUS

## Current milestone

- Milestone 3: Verify and close

## Current status

- state: closed
- completion_class: conditional_complete
- candidate_vs_proof: proof_passed

## Goal

证明 simulated Telegram 可以在 LLM-in-loop 条件下穿过完整主体主链，并留下后续 whole-chain replay 需要的最小 artifact 集合。

## Constraints

- no repo-level state upgrade
- no runtime efficacy claim
- no relabel to replay unless trace capture is replay-sufficient

## Completed work

- implemented a bounded whole-chain simulated runner over two frozen `execute_task` cases
- exercised `simulated telegram -> unified ingress -> native_loop -> contract_runtime -> llm_client -> openemotion hooks -> delivery`
- captured canonical evidence bundle plus whole-chain extra traces:
  - `ingress_event.json`
  - `native_loop_trace.json`
  - `contract_runtime_trace.json`
  - `model_trace.json`
  - `tool_trace.json`
- produced run / manifest / failures / execution / trace-readiness reports under `artifacts/telegram_simulated_whole_chain_v1/reports/`

## Final result

- bounded cases: `2`
- failures: `0`
- replay_ready_without_requery cases: `2`
- current ceiling:
  - `bounded simulated whole-chain LLM-in-loop sampling complete`
  - not `runtime efficacy`
  - not `real Telegram / E4`
  - not repo-level enablement

## Validation

- `python3 -m py_compile scripts/codex/run_llm_in_loop_whole_chain_sampling.py scripts/codex/verify_llm_in_loop_whole_chain_sampling.py EgoCore/tests/test_llm_in_loop_whole_chain_sampling.py`
- `PYTHONPATH=.:EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_llm_in_loop_whole_chain_sampling.py -q`
- `PYTHONPATH=.:EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_llm_in_loop_whole_chain_sampling.py`
- `python3 scripts/codex/verify_llm_in_loop_whole_chain_sampling.py`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `git diff --check -- docs/codex/tasks/llm-in-loop-whole-chain-sampling scripts/codex/run_llm_in_loop_whole_chain_sampling.py scripts/codex/verify_llm_in_loop_whole_chain_sampling.py EgoCore/tests/test_llm_in_loop_whole_chain_sampling.py artifacts/telegram_simulated_whole_chain_v1/reports`

## Open limits

- current samples are simulated and bounded
- model trace comes from deterministic fake LLM, not external provider behavior
- this slice proves artifact sufficiency for later whole-chain replay on these samples, not generalized replay fidelity

## Next step

- if continuing, open a new task that consumes these replay-ready whole-chain bundles without re-querying the model
