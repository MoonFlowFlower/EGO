"""Read legacy v4/v5 exports with the exact frozen v5 runtime, never artifact code."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile,zipfile
ARCHIVE_SHA256='615791316b28ad9e645a90507dde1c6ccf099c8a38a8ae1d3021a4f21618c1de'
_CACHE={}
_SCRIPT=r'''
import json,sys
from switchlab.shared.core import SharedCore
try:
 d=json.load(sys.stdin)
 c=SharedCore.from_v04(d) if d.get('schema')=='switchlab.shared.v4' else SharedCore.restore(d)
 print(json.dumps({'snapshot':c.snapshot(),'report':{'source_version':d['metadata']['version'],
  'recorded_events':len(d['events']),'original_head':d['head'],'recorded_input_replay':True,
  'wall_clock_unknown':True,'model_rerun':False,'source_scope':'frozen legacy runtime only'}},ensure_ascii=False,allow_nan=False))
except Exception as e:
 print(type(e).__name__+': '+str(e),file=sys.stderr);sys.exit(2)
'''
def verify_legacy(data):
    if not isinstance(data,dict) or data.get('schema') not in ('switchlab.shared.v4','switchlab.shared.v5'):raise ValueError('仅支持v0.4、v0.5的共享探索存档')
    raw=json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
    if len(raw)>64*1024*1024:raise ValueError('旧存档超过64MiB，请使用原版本处理')
    archive=Path(__file__).resolve().parents[2]/'compatibility/shared_v05_runtime.zip'
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=ARCHIVE_SHA256:raise ValueError('冻结旧运行时代码不匹配')
    key=hashlib.sha256(raw).hexdigest()
    if key in _CACHE:return deepcopy(_CACHE[key])
    with tempfile.TemporaryDirectory(prefix='shared_v5_read_') as t:
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                p=Path(name)
                if p.is_absolute() or '..' in p.parts:raise ValueError('unsafe frozen path')
            z.extractall(t)
        try:r=subprocess.run([sys.executable,'-c',_SCRIPT],input=raw,capture_output=True,cwd=Path(t)/'SharedField',timeout=90)
        except subprocess.TimeoutExpired as e:raise ValueError('旧存档复算超时；没有改动当前个体') from e
    if r.returncode:raise ValueError('旧存档验证失败：'+r.stderr.decode('utf-8','replace')[-800:])
    result=json.loads(r.stdout)
    if len(_CACHE)>=2:_CACHE.pop(next(iter(_CACHE)))
    _CACHE[key]=deepcopy(result);return result

def restore_sqlite_backup(source,target):
    """Read-only source snapshot; validate a temporary copy before a new destination."""
    import sqlite3
    from .store import MemoryStore,code_fingerprint
    source=Path(source).resolve();target=Path(target)
    if target.exists():raise ValueError('恢复目标已存在，不覆盖')
    if not source.is_file() or source.stat().st_size<100:raise ValueError('这不是有效的SQLite记忆备份')
    readonly=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)
    try:
        try:
            row=readonly.execute("SELECT value FROM meta WHERE key='initial'").fetchone()
            if not row:raise ValueError('备份缺少个体元数据')
            initial=json.loads(row[0])
            if initial.get('schema')!='sharedfield.memory.v6' or initial.get('source_sha256')!=code_fingerprint():raise ValueError('备份版本与当前程序不符，请保留对应原包')
            if readonly.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('备份数据库完整性检查失败')
        except (sqlite3.Error,json.JSONDecodeError,KeyError) as e:raise ValueError('备份不是可识别的记忆数据库') from e
        with tempfile.TemporaryDirectory(prefix='memory_restore_') as t:
            path=Path(t)/'validated.sqlite3';conn=sqlite3.connect(path)
            try:readonly.backup(conn)
            finally:conn.close()
            copy=MemoryStore(path)
            try:copy.sanity();copy.backup(target)
            finally:copy.close()
    finally:readonly.close()
    return {'restored':True,'source_modified':False,'target':str(target),'scope':'consistent stored state; recorded-input replay is a separate check'}
