# Studio v0.2 Implementation Plan

Goal: ship a runnable local language-facing persistent sandbox, preserving the old scientific comparison rather than tuning it into a pass.
Architecture: deterministic source-linked core + pluggable language transport + bounded asynchronous worker + local browser. Python >=3.10 standard library only at runtime.
Spec: docs/studio/DESIGN.md

1. Tests then protocol/core: strict payload contracts, free-language goal content with finite tool vocabulary, versioned persistent goals, actual drafts, outcome-vs-style feedback, recorded-input replay and secret-free persistence. Cases: invented evidence IDs, malicious file actions, cancelled/stale work, noise/replay does not create evidence, feedback doesn't overwrite scientific belief.
2. Tests then provider/service: configurable chat-completions HTTP, explicit JSON/prompt-only switch, bounded response sizes/timeouts, no redirect/secret logging, manual exchange, no fabricated fallback, paused/error/budget behavior, single worker and restart persistence.
3. Tests then real integration: Chinese conversational UI, settings, goal and artifact panels, real feedback buttons, numerical world and interventions, export, pause/manual run/auto finite run. Old lab remains available.
4. Run all tests; exercise browser; package, extract and test again. Record exact executed results and outstanding real-provider/Windows limitations. No commits to a user repository, no API key creation or paid calls.

Review focus: queued messages while working; user pause during HTTP request; failures after generating a draft but before persistence; corrupted checkpoint; missing credential/unsupported JSON mode; large Unicode inputs; untrusted HTML rendered only as text; repeated feedback idempotence; restart default paused; no source mismatch hidden by replay.
