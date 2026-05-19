# LLM-in-Loop Whole-Chain Sampling - IMPLEMENT

## Scope

- task docs
- whole-chain simulated runner
- verifier
- one slice-local test

## Out of scope

- canonical runtime behavior changes
- real Telegram sampling
- challenger comparison
- repo-level truth updates

## Deliverables

1. bounded whole-chain runner
2. whole-chain sample bundles
3. execution report
4. failures table
5. trace-readiness report

## Validation floor

- `python3 -m py_compile ...`
- targeted `pytest`
- `python3 scripts/codex/run_llm_in_loop_whole_chain_sampling.py`
- `python3 scripts/codex/verify_llm_in_loop_whole_chain_sampling.py`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `git diff --check`
