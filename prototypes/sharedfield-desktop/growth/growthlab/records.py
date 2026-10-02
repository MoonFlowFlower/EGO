import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'runs' / 'phase0'
EVIDENCE = ROOT / 'evidence' / 'phase0'


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def telemetry():
    class Power(ctypes.Structure):
        _fields_ = [('ac', ctypes.c_ubyte), ('flag', ctypes.c_ubyte),
                    ('percent', ctypes.c_ubyte), ('reserved', ctypes.c_ubyte),
                    ('life', ctypes.c_ulong), ('full', ctypes.c_ulong)]
    power = Power()
    ok = ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(power))
    p = subprocess.run(['nvidia-smi', '--query-gpu=temperature.gpu,clocks.current.graphics,memory.used,power.draw',
                        '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=10)
    return {'unix_s': time.time(), 'ac_online': power.ac == 1 if ok else None,
            'gpu_csv_C_MHz_MiB_W': p.stdout.strip(), 'gpu_returncode': p.returncode}
