# v0.6 implementation ledger

- Baseline: freshly ran 266 original tests successfully. Original v05 runtime frozen for migration; source ZIP unchanged.
- Store: atomic raw source, typed namespaces, versioned commitments and claims, Chinese FTS, bounded context with source windows and current-status expansion. Red/green logs 01–07.
- Service: real two-phase provider path, real-time app worker, late request cancellation, per-object versions, raw history on restart. Logs 08–13.
- Privacy: explicit source/derivative deletion rebases replay, removes managed backups and resets affected learned state. Logs 14–15 and 30–31. No external-copy/forensic-erasure guarantee.
- Runtime: dialogue no longer invalidated by unrelated world motion; explicit additive request grants, resumable raw inputs. Logs 16–17.
- UI + HTTP: new default memory route, old shared-world adapter retained; settings, manual exchange, source retrieval, editing, export/import. Logs 18–22.
- Policy correction: synthetic predictor probe favored simple category counts over online logistic. Default contact forecast uses unique outcome counts; gradient learner retained only as an explicit experiment. Automatic gradient replay is OFF, not run merely to show activity.
- Backlog control: two-minute minimum gap between app-initiated contacts, once per commitment version, plus explicit busy report and learned bounded deferral. Log 23–24.
- Real wall-clock worker: one-second due condition causes one actual app contact without new message. Log 25.
- UI bug found by actual screenshot: browser timezone differed from stored timezone. Fixed persisted due_display, red/green 26–27.
- Browser fixture bug: default prompt was answered with an empty string. Fixed the test to pass actual prompt default; production correctly rejected empty cancellation quote.
- Backup restore now verifies read-only source and a temporary copy before destination; logs 28–29.
- Security review: malformed privacy-root model previously survived import despite rehashed chain; added structural sanity validation before replacing active DB. No authenticity claim about editable privacy roots.

Self-review only; no independent reviewer, user repo or Codex access. Final delivery evidence is written after code freeze and clean extraction.

- Final visual inspection caught an actual import error toast despite a weak browser assertion reporting green. Root cause: multi-key setting reducer returned dict insertion order in its receipt, while SQLite JSON storage sorted the payload keys. Added RED tests for key-order invariant and real JSON export replay; sorted receipt keys. Strengthened browser import check with a post-export marker and required success receipt/projection equality. Earlier 25-check browser runs are not release evidence for import.
- Second real browser import exposed a distinct serialization defect: all event hashes matched, but projection digest hashed raw JSON-in-SQL TEXT spelling (1.0 versus 1). Added RED tests and normalized only schema-declared JSON columns for semantic projection hashing, preserving literal dialogue strings and the existing 12-decimal numeric contract. No hash check removed or recomputed to forgive a changed result.

- Final runtime freeze e99b570901f0de78848140d375a04fbd092137bdd7db85bd666fbfc9c5b62cbf: 332 full tests green, 27 strengthened browser checks green, 100k synthetic journal run/replay/backup complete. Source unchanged during final measurements. Private source continuation verified separately and not bundled. Packaging verification follows.
