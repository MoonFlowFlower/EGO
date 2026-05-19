# Runtime-Proximal Low-Cue Ownership Runner - IMPLEMENT

## Implementation rules

- Reuse the deterministic runtime harness pattern from `run_runtime_proximal_host_consumption_runner.py`
- Keep the chat path provider-free
- Compare only compact host-contract surfaces and canonical trace handoff
- Allow family verdicts to be `pass` or `hold`
- Treat `hold` as a valid judgeable outcome for this stage

## Minimal change surface

- `docs/codex/tasks/runtime-proximal-low-cue-ownership-runner-implementation/*`
- `scripts/codex/run_runtime_proximal_low_cue_ownership_runner.py`
- `EgoCore/tests/test_runtime_proximal_low_cue_ownership_runner.py`
- campaign / state sync files after review
