"""Shared helpers for Claude's read-only audits. Usage: python <script>.py <growth_root>

<growth_root> is the growth/ directory that contains runs/ (on the owner's
machine: .publish/EGO/prototypes/sharedfield-desktop/growth). Nothing is written.
"""
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def root():
    if len(sys.argv) < 2: sys.exit('usage: python script.py <growth_root>')
    return Path(sys.argv[1])


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines()]


def episode_name(source):
    return source.replace(chr(92), '/').split('/')[-2]


def cells(obs):
    return {(c['dx'], c['dy']): c for c in obs['cells']}


def reason_of(record):
    text = json.dumps(record, ensure_ascii=False)
    m = re.search(r'"reason": "(.*?)"(,|\})', text)
    return m.group(1) if m else ''


def action_of(record):
    m = re.search(r'"action": "(\w+)"', json.dumps(record, ensure_ascii=False))
    return m.group(1) if m else ''
