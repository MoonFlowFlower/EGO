"""Private parent pipe + Windows kill-on-close job for one official Agent."""
import ctypes
from ctypes import wintypes
import json
import os
import queue
from pathlib import Path
import subprocess
import sys
import threading
import time

from growthlab.records import ROOT


class Job:
    def __init__(self):
        class Basic(ctypes.Structure):
            _fields_ = [('process_time',ctypes.c_int64),('job_time',ctypes.c_int64),('flags',wintypes.DWORD),
                        ('min_ws',ctypes.c_size_t),('max_ws',ctypes.c_size_t),('active',wintypes.DWORD),
                        ('affinity',ctypes.c_size_t),('priority',wintypes.DWORD),('scheduling',wintypes.DWORD)]
        class Io(ctypes.Structure):
            _fields_ = [(name,ctypes.c_uint64) for name in ('read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes')]
        class Extended(ctypes.Structure):
            _fields_ = [('basic',Basic),('io',Io),('process_memory',ctypes.c_size_t),('job_memory',ctypes.c_size_t),
                        ('peak_process',ctypes.c_size_t),('peak_job',ctypes.c_size_t)]
        self.api = ctypes.WinDLL('kernel32',use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p,wintypes.LPCWSTR]
        self.api.CreateJobObjectW.restype = wintypes.HANDLE
        self.api.SetInformationJobObject.argtypes = [wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]
        self.api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE,wintypes.HANDLE]
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        self.handle = self.api.CreateJobObjectW(None,None)
        if not self.handle: raise OSError('job_create_failed')
        info=Extended()
        info.basic.flags=0x2000 | 0x8 # KILL_ON_JOB_CLOSE and ACTIVE_PROCESS_LIMIT
        info.basic.active=1          # no browser/fork/generated-code subprocess
        if not self.api.SetInformationJobObject(self.handle,9,ctypes.byref(info),ctypes.sizeof(info)):
            self.close()
            raise OSError('job_limits_failed')

    def assign(self, process):
        if not self.api.AssignProcessToJobObject(self.handle,wintypes.HANDLE(int(process._handle))):
            raise OSError('job_assignment_failed')

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle=None


def main():
    if '--private-pipe' not in sys.argv or sys.stdout.isatty():
        raise ValueError('private_parent_pipe_required')
    request=json.loads(sys.stdin.readline())
    root=Path(request['root']).resolve()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True,creationflags=subprocess.CREATE_NO_WINDOW).strip()
    dirty=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=root,text=True,creationflags=subprocess.CREATE_NO_WINDOW).strip()
    if revision!='b36eaf7e61b3f6bd031fdb531812b2e3c42b6c73' or dirty:
        raise ValueError('unreviewed_or_modified_official_checkout')
    token=request['local_token']
    if not isinstance(token,str) or len(token)<32 or token.startswith('sk-'):
        raise ValueError('local_token_required')
    folder=ROOT/'runs/p7/body_connected_v2'/str(time.time_ns())
    folder.mkdir(parents=True)
    env={k:v for k,v in os.environ.items() if not any(s in k.upper() for s in ('KEY','TOKEN','SECRET','PASSWORD')) and k!='INSECURE_CODING'}
    node=request.get('node',r'C:\Program Files\nodejs\node.exe')
    child=None
    job=Job()
    try:
        child=subprocess.Popen([node,str(ROOT/'p7/mindcraft_body_v2.mjs'),'--private-pipe'],cwd=root,env=env,
                               stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',
                               creationflags=subprocess.CREATE_NO_WINDOW)
        # The child waits on this private first line before any third-party import.
        job.assign(child)
        child.stdin.write(json.dumps(request)+'\n');child.stdin.flush()
        print(json.dumps({'kind':'supervisor_started','child_pid':child.pid,'folder':str(folder),'job_kill_on_close':True,'active_process_limit':1}),flush=True)
        def forward(stream,name):
            with (folder/name).open('a',encoding='utf-8') as out:
                for line in stream:
                    clean=line.replace(token,'[LOCAL_TOKEN_REDACTED]')
                    out.write(clean);out.flush()
                    if name=='events.jsonl':
                        print(clean,end='',flush=True)
        readers=[threading.Thread(target=forward,args=(child.stdout,'events.jsonl'),daemon=True),
                 threading.Thread(target=forward,args=(child.stderr,'stderr.txt'),daemon=True)]
        for reader in readers:reader.start()
        if request.get('probe'):
            child.wait(timeout=30)
        else:
            controls=queue.Queue()
            def input_reader():
                for line in sys.stdin:controls.put(line)
                controls.put(None)
            threading.Thread(target=input_reader,daemon=True).start()
            while child.poll() is None:
                try:line=controls.get(timeout=.25)
                except queue.Empty:continue
                if line is None:break
                child.stdin.write(line);child.stdin.flush()
                if json.loads(line).get('op')=='shutdown':break
        if child.poll() is None:
            child.stdin.close()
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:pass
        for reader in readers:reader.join(timeout=1)
        print(json.dumps({'kind':'supervisor_closed','child_exit':child.poll(),'folder':str(folder)}),flush=True)
    finally:
        job.close()
        if child is not None:
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'kind':'supervisor_error','error_type':type(error).__name__}),flush=True)
        raise SystemExit(1) from None
