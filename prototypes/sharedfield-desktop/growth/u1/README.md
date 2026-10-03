# U1: convention learning

Run from `prototypes/sharedfield-desktop`, with `PYTHONPATH` pointing at `growth`:

```powershell
$env:PYTHONPATH=(Resolve-Path growth).Path
python -m u1.run engineering
python -m u1.run freeze
python -m u1.run run --reviewed-manifest-sha256 <reviewed SHA-256>
```

`engineering` makes no cloud calls. `freeze` is write-once and records source,
script, option, keyword, prompt and route hashes. The live runner refuses an
existing run folder or modified freeze. Each description arm has its own process
and result file. A failed main Ua does not bypass either description arm.

The shared five-dollar reservation ledger is `growth/runs/phase1/budget.sqlite`;
existing entries are never reset. Key loading is only through the existing
`growthlab.models.read_key`. No key is copied into this module, plans or logs.

`u1.conventions.ConventionLibrary` is the reusable P7 integration surface. It
depends on `growthlab.state`, not on this experiment's model, fixtures or scorer.
Use `utterance` to save provenance, `propose` for untrusted model proposals,
`annotate` before decisions, and `forget` for the complete source/version/derived
closure. `cards(active_only=False)` exposes superseded versions for audit.

The initial supported trigger types are normalized literal substring and
`周<weekday><HH:MM>以后上线`; the latter's structured predicate must agree with
the quoted text. Correction needs a cited literal sentence stating
`不再是「旧含义」，现在改成「新含义」`. This deliberate mechanical boundary is
not general semantic interpretation. Meaning text is quoted verbatim.

Raw model inputs/outputs and SQLite stores go only under ignored `growth/runs/u1`.
Public synthetic scripts, acceptance, frozen manifests, summaries and per-case
scores go under `growth/evidence/u1`. Deletion's byte check applies to saved state
and SQLite sidecars; synthetic fixture source and immutable research logs remain
for audit. It makes no wider filesystem erasure claim.

Ua uses 180 primary decisions plus 90 B-only decisions per available description
arm. If and only if the frozen switching rule fires, a new immutable manifest
reruns all 180 primary comparisons. Ub has 10 teaching conversations; Uc has 10
rounds. The complete chain has 360 decisions to retain 10 cases per family at
every stage and the same A/B schedule. No sample size is fitted to results.

Passing U1 establishes a bounded synthetic convention pipeline, not that she
understands the user. Only a passed U1 is eligible for live P7 learning hookup.
