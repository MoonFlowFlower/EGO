# SharedField v0.6 memory integration implementation plan

Approved design: EGO_Memory_Architecture_v1.md. Scope: bounded engineering + learning/adaptation, no subject claims.

1. SQLite canonical memory store: atomic raw observations, versioned commitments/claims, UTC timestamps, Chinese fulltext, cursor pages, source references, bounded context. Tests: save/restart; correction/cancel; fake source/fiction; >10k irrelevant events; rollback.
2. Prospective loop and small contact-outcome learner: due candidate query independent of context, once-per-version in-app outbox, busy-state deferral, offline stale review, learning freeze/replay with unique evidence. Tests: same clock/different history; no repeated contacts; cancellation while model in flight.
3. Integrate new memory service and dialogue protocol with existing provider and numeric shared-world adapter. Default entrypoint switches to memory service; legacy modules remain runnable/regression tested. Context is bounded and sources retrievable. Real model outputs recorded as exogenous; no hardcoded general language responses presented as AI.
4. Local UI: conversational main view, optional shared exploration, maintenance memory search/receipts, settings/timezone, backup/export/import. Legacy v4/v5 verifier frozen; never bypass fingerprints. Fresh startup paused.
5. Full regression, HTTP + optional browser checks, long-history replay/backup, negative controls, package/clean unzip re-run. No real-cloud or Windows claims without execution.

Constraints: local-only/no arbitrary shell or file paths from LLM; no real email/phone/MC added; secrets process-only; no paid background before local authorization. Need caller-configured IANA timezone or explicit UTC offset; unresolved time preserved, not guessed.

Rulings: work in a fresh extracted sandbox copy; no user repo accessible. Implement I–III as a narrow integrated loop; optional embedding services, neural lifelong learning, unlimited memory claims excluded. Single implementer self-review, no independent audit tool. Exact event records kept separately from model output/summary.
