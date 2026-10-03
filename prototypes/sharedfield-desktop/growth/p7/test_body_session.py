import json
import subprocess
import sys
import time
import unittest

from p7.body_session import Job


class ProcessBoundary(unittest.TestCase):
    def test_job_close_kills_waiting_child(self):
        job=Job()
        child=subprocess.Popen([r'C:\Program Files\nodejs\node.exe','-e',
                                "process.stdin.once('data',()=>{console.log('ready');setInterval(()=>{},1000)})"],
                               stdin=subprocess.PIPE,stdout=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            job.assign(child)
            child.stdin.write(b'go\n');child.stdin.flush()
            self.assertEqual(child.stdout.readline().strip(),b'ready')
            self.assertIsNone(child.poll())
            job.close()
            self.assertIsNotNone(child.wait(timeout=5))
        finally:
            job.close()
            if child.poll() is None:child.kill();child.wait()
            child.stdin.close();child.stdout.close()

    def test_parent_death_closes_job_and_kills_child(self):
        code='''import subprocess,sys,time
from p7.body_session import Job
j=Job()
p=subprocess.Popen([r"C:\\Program Files\\nodejs\\node.exe","-e","process.stdin.once('data',()=>{console.log('ready');setInterval(()=>{},1000)})"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
j.assign(p)
p.stdin.write(b"go\\n");p.stdin.flush()
assert p.stdout.readline().strip()==b"ready"
assert p.poll() is None
print(p.pid,flush=True)
sys.stdin.readline()
'''
        parent=subprocess.Popen([sys.executable,'-c',code],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                text=True,creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            pid=int(parent.stdout.readline())
            import ctypes
            api=ctypes.WinDLL('kernel32',use_last_error=True)
            from ctypes import wintypes
            api.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
            api.OpenProcess.restype=wintypes.HANDLE
            api.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
            api.CloseHandle.argtypes=[wintypes.HANDLE]
            handle=api.OpenProcess(0x100000,False,pid)
            self.assertTrue(handle)
            try:
                parent.kill();parent.wait(timeout=5)
                self.assertEqual(api.WaitForSingleObject(handle,5000),0)
            finally:api.CloseHandle(handle)
        finally:
            if parent.poll() is None:parent.kill();parent.wait()
            parent.stdin.close();parent.stdout.close()

    def test_public_address_refused_before_agent_start(self):
        payload={'root':'D:/Project/AIProject/MyProject/Ego_proejct_restart/p7_tools/mindcraft',
                 'local_token':'offline-local-fixture-token-000000000000000','host':'8.8.8.8','port':25575,'probe':True}
        result=subprocess.run([sys.executable,'-m','p7.body_session','--private-pipe'],input=json.dumps(payload)+'\n',
                              capture_output=True,text=True,encoding='utf-8',timeout=15)
        rows=[json.loads(s) for s in result.stdout.splitlines()]
        self.assertFalse(any(r.get('kind') in ('started','offline_probe','login') for r in rows))
        self.assertTrue(any(r.get('child_exit')==1 for r in rows))


if __name__=='__main__':unittest.main()
