"""Zero-cloud engineering acceptance with a spawn-safe Windows entry point."""
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import time
import unittest

from .validate import load_candidates, validate


def main():
    out=Path('evidence/u2');out.mkdir(parents=True,exist_ok=True)
    buffer=io.StringIO();loader=unittest.TestLoader()
    suite=unittest.TestSuite([loader.discover('companion',pattern='test_*.py',top_level_dir='.'),
                             loader.discover('u2',pattern='test_*.py',top_level_dir='.')])
    started=time.monotonic();result=unittest.TextTestRunner(stream=buffer,verbosity=2).run(suite)
    (out/'ENGINEERING_TESTS.txt').write_text(buffer.getvalue(),encoding='utf-8')
    report={'passed':result.wasSuccessful(),'tests_run':result.testsRun,'failures':len(result.failures),
        'errors':len(result.errors),'seconds':time.monotonic()-started,'utc':datetime.now(timezone.utc).isoformat(),
        'cloud_calls':0,'new_cloud_cost_usd':0,'candidate_validation':validate(load_candidates()),
        'scope':['canonical understanding/source/version deletion and physical erasure',
            'fresh process learning/testing with read-only unchanged SQLite',
            'daily midnight/late settle/unknown reservations/concurrent cap',
            'DPAPI token unchanged in fresh process',
            'real child crash and supervisor recovery without repeat simulated effects',
            'owner absence requires grant; no unsolicited initiative chat',
            'fixed decision order, full originals, identical arm prompt',
            'same-input one retry; second/nonretryable failure stops'],
        'not_verified':['live AIRI GUI reconfiguration and real MC runtime restart',
                        'model learning or naturally understanding the owner']}
    (out/'ENGINEERING.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)
    if not result.wasSuccessful():print(buffer.getvalue());raise SystemExit(1)


if __name__=='__main__':main()
