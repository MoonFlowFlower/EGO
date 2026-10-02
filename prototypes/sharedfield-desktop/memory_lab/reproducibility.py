"""Prevent resumed comparisons from silently mixing implementation versions."""
import hashlib
import json
from .provider import ROOT, write_json

def code_manifest():
    files=list(ROOT.glob('*.py'))+[ROOT/'memos_bridge.cjs',ROOT/'upstream-lock.json',
          ROOT/'requirements.lock.txt',ROOT/'requirements-linux.lock.txt',ROOT/'memos-package-lock.json',
          ROOT/'model-revisions.json',ROOT/'scenarios/manifest.json',ROOT/'requirements-eval.lock.txt']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}

def freeze_run(root):
    path=root/'RUN_MANIFEST.json';current=code_manifest()
    from .adapters import http
    profile=http('http://127.0.0.1:18765/health')['profile']
    if path.exists():
        old=json.loads(path.read_text(encoding='utf-8'))
        if old['files']!=current:raise ValueError('Implementation/dependency manifest changed; do not mix versions in this comparison')
        if old.get('profile')!=profile:raise ValueError('Inference profile changed; restart entire comparison')
    else:
        if (root/'episodes').exists() or (root/'bases').exists():
            raise ValueError('Existing unversioned diagnostic run cannot become a formal comparison; choose a fresh run ID')
        write_json(path,{'files':current,'profile':profile,'status':'frozen before first episode'})
