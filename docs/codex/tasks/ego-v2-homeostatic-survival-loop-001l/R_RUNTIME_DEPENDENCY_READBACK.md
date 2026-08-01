# R formal runtime dependency readback

This post-formal readback records the runtime bytes used at R closeout before P3
changes them. It does not retroactively strengthen the preregistered freeze.

- R closeout commit: `fde853a351b1997f65a5ae33a0350c0afe53df9c`
- engine code-path hash: `06086fa182fab82b11a6be05545bc3c7000868b40d29bf1c1c231792c2d87b5d`
- engine.py SHA-256: `d28d4387c8a4ece153ef0d8501b7fed36a517480aceefdac07c98270e14b3af4`
- homeostatic_transfer.py SHA-256: `775d40c9b36e5689aa5b5bcb45029dbfc6f2f40a4c598a31449c9e9e162e9657`
- microworld.py SHA-256: `d87ba9530d32d2b504c75a132ae1163dfe8e8cd0a8879e6cbdd09807a9daa923`

Evidence limitation: candidate_freeze.json froze the producer, verifier,
configuration, dependencies and packet assignments, but did not separately
freeze these transitive runtime file hashes. The immutable Git commit retains
the bytes, while the formal stored rows and exact replay bind their produced
traces. Future live reproduction must check out the R closeout commit rather
than use the later P3 worktree.
