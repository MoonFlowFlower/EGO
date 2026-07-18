# Collision record — EGO-V2-PRODUCT-MAIN-TAKEOVER-001A

## Candidate 1 — direct copy / overlay

- Evidence produced: folder appearance only.
- Cheap baseline: ordinary recursive copy.
- Leakage/hard-coding risk: high; provenance and the 19-path negative state are lost.
- Smallest falsifier: compare checkpoint bytes, Git parent, tree, and ref topology.
- Expected failure: all 19 dirty paths collide with the 80-path V2 delta.

## Candidate 2 — external archive only

- Evidence produced: exact raw bytes.
- Cheap baseline: zip/patch archive.
- Leakage/hard-coding risk: medium; parent, mode, and tracked-state lineage are weak.
- Smallest falsifier: reconstruct Git parent/modes/branch from the archive alone.
- Expected failure: cannot establish repository ancestry by itself.

## Candidate 3 — checkpoint commit + recovery package + CAS + transcription

- Evidence produced: exact byte recovery, Git lineage, exact fast-forward tree, and
  one field-by-field authority projection.
- Cheap baseline: direct copy cannot match the lineage and reconstruction predicates.
- Leakage/hard-coding risk: bounded by exact manifests, source-object pins, hostile
  mutation controls, and no product-source edits.
- Smallest falsifier: mutate one byte/path/ref or open one runtime switch.
- Expected failure: fail closed before commit.

## Selection

Candidate 3 is selected. Candidate 1 is rejected for destructive provenance loss;
Candidate 2 is retained only as the raw-byte half of the combined recovery package.

## Negative evidence retained

A vanilla Windows checkout of the Git bundle does not reproduce every mixed-EOL
working byte. This is not relabelled as pass. The verified recovery package uses the
bundle for Git lineage and the separately hashed 19-entry raw archive for exact bytes;
the resulting files are byte-exact and Git clean-filter-equivalent.

## Claim ceiling

This collision decision concerns repository integration and preservation only. It
does not establish runtime enablement, learning, memory causality, agency,
subjectivity, consciousness, or electronic life.
