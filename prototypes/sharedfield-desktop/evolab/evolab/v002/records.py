"""Scoped append-only phase records and hardware sampling."""
import hashlib
import json
from pathlib import Path
import subprocess
import datetime


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def thermal():
    raw = subprocess.check_output(['nvidia-smi', '--query-gpu=temperature.gpu,clocks.current.graphics,clocks.current.memory,power.draw', '--format=csv,noheader,nounits'], text=True).strip()
    values = [float(x.strip()) for x in raw.split(',')]
    return dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                temperature_c=values[0], graphics_mhz=values[1], memory_mhz=values[2], power_w=values[3])


def progress(title, detail):
    p = Path('PROGRESS.md')
    data = p.read_bytes()
    i = data.index(b'## ')
    entry = f'## 2026-10-02 — EVOLAB-002A {title}\n\n{detail}\n\n'.encode('utf-8')
    p.write_bytes(data[:i]+entry+data[i:])


def board(text):
    p = Path('../TASK_BOARD.md')
    lines = p.read_bytes().splitlines(keepends=True)
    matches = [i for i, line in enumerate(lines) if line.startswith('最新研究推进（2026-10-02）：EVOLAB-'.encode())]
    if len(matches) != 1:
        raise RuntimeError('EVOLAB status line not uniquely found; preserve board')
    i = matches[0]
    ending = b'\r\n' if lines[i].endswith(b'\r\n') else b'\n'
    lines[i] = ('最新研究推进（2026-10-02）：EVOLAB-002A '+text).encode()+ending
    p.write_bytes(b''.join(lines))


def verify_protected():
    manifest = json.loads(Path('evidence/002A/legacy_manifest.json').read_text())
    for name, digest in manifest.items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
    assert hashlib.sha256(Path('PREREG_002A.md').read_bytes()).hexdigest() == '4d378b0c224550ee3a982f134a313edd341d40da1303e4f88a69cd102fe58a68'
