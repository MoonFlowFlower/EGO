"""Read an old life with its exact original code; never relabel old hashes as new."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from .adaptive_core import AdaptiveCore
from .service import DirectoryLock
from switchlab.runtime import load_json, save_json

ARCHIVE=Path(__file__).resolve().parents[2]/'compatibility'/'original_v02.zip'
ARCHIVE_SHA256='f12c13057d2e16f8f3bc366fb9a1bd485a48c798f6fc1af31ac9f5244bb05586'
READER=r'''
import json,sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,sys.argv[1])
from switchlab.studio.core import Core
from switchlab.runtime import load_json
c=Core.restore(load_json(sys.argv[2]))
print(json.dumps({'messages':c.state['messages'][-40:], 'memories':c.state['memories'][-24:],
 'goals':c.state['goals'][-12:], 'old_head':c.head, 'source_verified':True},ensure_ascii=False))
'''

def migrate_v02(source,directory):
    source=Path(source).resolve();directory=Path(directory)
    if not source.is_file() or source.stat().st_size>32*1024*1024:raise ValueError('select an existing v0.2 JSON checkpoint smaller than 32 MiB')
    if (directory/'session.json').exists():raise ValueError('destination already has a life; use a NEW directory')
    if hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()!=ARCHIVE_SHA256:raise ValueError('original v0.2 reader archive was modified')
    with tempfile.TemporaryDirectory(prefix='switchlab-legacy-readonly-') as tmp:
        root=Path(tmp)
        with zipfile.ZipFile(ARCHIVE) as z:
            for member in z.infolist():
                if not (root/member.filename).resolve().is_relative_to(root):raise ValueError('invalid legacy archive path')
            z.extractall(root)
        result=subprocess.run([sys.executable,'-I','-c',READER,str(root/'SwitchLab'),str(source)],
                              capture_output=True,text=True,encoding='utf-8',timeout=120)
        if result.returncode!=0:raise ValueError('v0.2 source-bound recorded-input verification failed; old data was not modified')
        try:context=json.loads(result.stdout)
        except json.JSONDecodeError:raise ValueError('legacy verifier returned invalid output') from None
    # All old content remains explicitly historical, not neural examples or active commands.
    c=AdaptiveCore();c.apply('legacy_context',context)
    directory.mkdir(parents=True,exist_ok=True);lock=DirectoryLock(directory)
    try:
        if (directory/'session.json').exists():raise ValueError('destination already contains a life')
        save_json(directory/'session.json',c.checkpoint())
        save_json(directory/'legacy_original.json',load_json(source))
    finally:lock.close()
    return {'legacy_recorded_input_replay':True,'old_head':context['old_head'],
            'new_directory':str(directory.resolve()),'neural_samples_imported':0,
            'legacy_goals_auto_enabled':False,'original_untouched':True}
