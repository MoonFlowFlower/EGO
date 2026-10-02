"""Explicit frozen-version -> current migration, verified with source bytes.

The compatibility adapter accepts only two path spellings computed from the
verified archive. It does not edit the supplied artifact or skip reducer replay.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile

ARCHIVE_SHA256='38a70a230cb8e2f7a8f1fbdee273dee934a2f5fd4ba878ae5d12b6cfbe27bece'
# The first real activity predates the final adoption-provenance correction.
# Preserve its exact reducer as a named migration, never rewrite its hashes.
PRE_RELEASE_SOURCE='bf6af76534d00e650d03ac77ae86f3856871fb52ed89da8d707f6c0e0e99c387'
PRE_RELEASE_ARCHIVE_SHA256='357a26509277ab4a4fdd9d724753e4c75ab458486d23b9698b904588c3f8c637'
_CACHE={}
SCRIPT=r'''
import hashlib,json,pathlib,sys,tempfile
from switchlab.memory import store
from switchlab.shared.evidence import digest
d=json.load(sys.stdin)
root=pathlib.Path('.').resolve()
paths=sorted([p for p in (root/'switchlab').rglob('*') if p.is_file() and p.suffix in ('.py','.js','.html','.css')]+[root/'run.py'])
items=[(p.relative_to(root).as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
allowed={digest(items),digest([(name.replace('/','\\'),sha) for name,sha in items])}
expected=d['initial']['source_sha256']
if expected not in allowed:raise ValueError('v0.6 source bytes do not match this frozen archive')
# Explicit path-only adapter after source identity was independently verified.
store.code_fingerprint=lambda:expected
with tempfile.TemporaryDirectory() as tmp:
 s=store.MemoryStore.from_export(pathlib.Path(tmp)/'memory.db',d)
 try:print(json.dumps({'projection':s.projection(),'person_id':s.person_id,'sequence':s.sequence,
   'created_at':s._meta('initial')['created_at'],'projection_sha256':s.projection_digest(),
   'source_sha256':expected,'path_normalization_only':True,'recorded_input_replay':True},ensure_ascii=False))
 finally:s.close()
'''


def verify_v06(data):
    if not isinstance(data,dict) or data.get('schema')!='sharedfield.memory.v6':raise ValueError('不是v0.6记忆存档')
    raw=json.dumps(data,ensure_ascii=False,allow_nan=False).encode('utf-8')
    if len(raw)>128*1024*1024:raise ValueError('旧存档超过128MiB，请先在旧版拆分或备份')
    prerelease=data.get('initial',{}).get('source_sha256')==PRE_RELEASE_SOURCE
    name='shared_v07_pre_release_runtime.zip' if prerelease else 'shared_v06_runtime.zip'
    expected=PRE_RELEASE_ARCHIVE_SHA256 if prerelease else ARCHIVE_SHA256
    archive=Path(__file__).resolve().parents[2]/'compatibility'/name
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:raise ValueError('冻结源码不匹配')
    key=hashlib.sha256(raw).hexdigest()
    if key in _CACHE:return deepcopy(_CACHE[key])
    with tempfile.TemporaryDirectory(prefix='verify_v06_') as tmp:
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                target=(Path(tmp)/name).resolve()
                if not target.is_relative_to(Path(tmp).resolve()):raise ValueError('unsafe frozen archive')
            z.extractall(tmp)
        try:r=subprocess.run([sys.executable,'-c',SCRIPT],input=raw,capture_output=True,cwd=Path(tmp)/'SharedField',timeout=120)
        except subprocess.TimeoutExpired as e:raise ValueError('旧版复算超时，未替换当前记忆') from e
    if r.returncode:raise ValueError('v0.6复算失败：'+r.stderr.decode('utf-8','replace')[-600:])
    result=json.loads(r.stdout)
    if len(_CACHE)>=2:_CACHE.pop(next(iter(_CACHE)))
    _CACHE[key]=deepcopy(result);return result


def import_v06(path,data):
    from .store import MemoryStore,SCHEMA,code_fingerprint
    if Path(path).exists():raise ValueError('迁移必须写入新数据库')
    verified=verify_v06(data)
    initial={'schema':SCHEMA,'person_id':verified['person_id'],'created_at':verified['created_at'],
             'source_sha256':code_fingerprint(),'sequence_offset':verified['sequence'],
             'migration_origin':deepcopy(data),'migration_projection':verified['projection'],
             'migration_contract':'frozen reducer replay; source identity checked; path spelling normalized; subsequent current-version events'}
    return MemoryStore(path,initial=initial)


def validate_initial(initial):
    from ..shared.evidence import canonical
    verified=verify_v06(initial['migration_origin'])
    if (canonical(verified['projection'])!=canonical(initial.get('migration_projection')) or
        verified['person_id']!=initial.get('person_id') or verified['sequence']!=initial.get('sequence_offset') or
        verified['created_at']!=initial.get('created_at')):raise ValueError('迁移起点与已验证的旧经历不一致')
    return verified['projection']
