"""Verify v04 with frozen original code; continue explicitly under a new contract.

No imports, scripts, paths, API calls, or permissions are taken from the artifact.
The frozen archive contains the exact v04 fingerprint runtime, not user data.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile,zipfile
from .evidence import canonical

ARCHIVE_SHA256='49e306718f57e6e0503722e90812bbc42145e30ec3dbfe3cd4bd333458f91304'
_CACHE={}
_CODE=r'''
import sys,json,math
from switchlab.shared.core import SharedCore
from switchlab.studio.core import fingerprint,LIMIT_EVENTS
from switchlab.runtime import digest

def normalized(v):
    if isinstance(v,bool) or v is None or isinstance(v,str):return v
    if isinstance(v,float):
        if not math.isfinite(v):raise ValueError('nonfinite value')
        q=round(v,12);return int(q) if q.is_integer() else q
    if isinstance(v,list):return [normalized(x) for x in v]
    if isinstance(v,dict):return {k:normalized(x) for k,x in v.items()}
    return v

def equal(a,b):
    return json.dumps(normalized(a),sort_keys=True,ensure_ascii=False)==json.dumps(normalized(b),sort_keys=True,ensure_ascii=False)

try:
    d=json.load(sys.stdin)
    if d.get('schema')!='switchlab.shared.v4':raise ValueError('expected v04')
    if d['metadata']['source_sha256']!=fingerprint():raise ValueError('original v04 source fingerprint mismatch')
    if not isinstance(d['events'],list) or len(d['events'])>LIMIT_EVENTS:raise ValueError('event limit')
    c=SharedCore(**d['metadata']['config']);c.metadata=d['metadata'];c.head=digest(c.metadata)
    for e in d['events']:
        computed=c.apply(e['kind'],e['payload'])
        # Hashes are original computed strings. Numeric normalization does not
        # regenerate the stored chain or waive state/payload comparison.
        if not equal(computed,e):raise ValueError('v04 event recomputation mismatch '+str(e.get('id')))
    if c.head!=d['head']:raise ValueError('head mismatch')
    if not equal(c.snapshot(),{k:d[k] for k in ('state','world','mind')}):raise ValueError('v04 final snapshot mismatch')
    print(json.dumps({'snapshot':c.snapshot(),'events':len(c.events),'head':c.head,
      'original_hashes_match':True,'source_checked':True,
      'comparison':'12 decimals; integer-valued float JSON equivalence; boolean distinct',
      'strict_original_reader_used':False,'language_rerun':False},ensure_ascii=False,allow_nan=False))
except Exception as e:
    print(type(e).__name__+': '+str(e),file=sys.stderr);sys.exit(2)
'''


def verify_v04(data):
    if not isinstance(data,dict) or data.get('schema')!='switchlab.shared.v4':
        raise ValueError('只接受v0.4导出，不自动混用其他格式。')
    encoded=json.dumps(data,ensure_ascii=False,allow_nan=False).encode('utf-8')
    if len(encoded)>64*1024*1024:raise ValueError('旧导出超过64MiB')
    cachekey=hashlib.sha256(encoded).hexdigest()
    if cachekey in _CACHE:return deepcopy(_CACHE[cachekey])
    archive=Path(__file__).resolve().parents[2]/'compatibility/shared_v04_runtime.zip'
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=ARCHIVE_SHA256:
        raise ValueError('冻结的v04运行代码不匹配，拒绝迁移。')
    with tempfile.TemporaryDirectory(prefix='shared_v04_verify_') as folder:
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                p=Path(name)
                if p.is_absolute() or '..' in p.parts:raise ValueError('unsafe frozen archive path')
            z.extractall(folder)
        result=subprocess.run([sys.executable,'-c',_CODE],input=encoded,stdout=subprocess.PIPE,
             stderr=subprocess.PIPE,cwd=Path(folder)/'SharedField',timeout=90)
    if result.returncode:raise ValueError('旧记录验证失败：'+result.stderr.decode('utf-8','replace')[-600:])
    output=json.loads(result.stdout)
    if len(_CACHE)>=4:_CACHE.pop(next(iter(_CACHE)))
    _CACHE[cachekey]=deepcopy(output)
    return output
