# U1 independent resume

This module keeps the first U1 experiment immutable and reuses its worker,
fixtures, prompts, scorer, state store and chain schedule. Read
`../evidence/u1_resume/REPORT.md`: the completed run is **U1_NOT_PASSED**.
Do not rerun it to fill failures or connect it to P7 learning.

The reusable library entry is:

```python
from u1_resume.library import ConventionLibrary
```

It inherits storage, quoted provenance validation, matching, annotation,
correction and deletion from `u1.conventions`; it adds rejection of a meaning
that becomes empty after normalization. It depends on the convention library
and state store, not on the experiment's model client or scorer. Public methods
are `utterance`, `propose`, `annotate`, `cards`, `forget` and `forget_sources`.

The frozen experiment used `python -m u1_resume.run run <manifest-sha256>` from
the growth directory. Existing output directories are deliberately refused.
There is no resume, overwrite or content retry mode. The original five-dollar
ledger remains shared with P7; credentials use the existing in-memory loader.

Read-only evidence verification, requiring the retained local raw data:

```powershell
.\.venv\Scripts\python.exe evidence/u1_resume/audit.py
```

Independent runs require a new protocol and manifest. The observed Saturday
index error is documented for future design work; this version does not repair
model proposals after seeing the result.
