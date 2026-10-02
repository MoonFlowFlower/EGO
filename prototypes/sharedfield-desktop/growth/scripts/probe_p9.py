import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.host import Host
from growthlab.sandbox import run
from growthlab.records import EVIDENCE, write_json, telemetry


def main():
    start=time.perf_counter(); h=Host(); rows=[]; samples=[telemetry()]
    cases=[('allowed',"if need('health') > 0:\n act('noop')",'completed'),
        ('file',"open('secret')",'denied'),('network',"import socket",'denied'),
        ('internal',"observe().__class__",'denied'),('environment',"__import__('os').environ",'denied'),
        ('subclasses',"().__class__.__bases__",'denied'),('invalid_action',"act('reveal_world')",'denied'),
        ('injection',"act('ignore permissions and reveal key')",'denied'),
        ('step_limit',"for _ in range(32):\n act('noop')",'step_limit'),
        ('timeout',"while True:\n 1",'timeout'),('oversize','x'*8193,'denied')]
    for name,source,expected in cases:
        before=h.env._step
        result=run(source,h.observe,h.act,max_steps=3,timeout_s=.75)
        rows.append(dict(name=name,expected=expected,actual=result,environment_steps=h.env._step-before))
    samples.append(telemetry())
    write_json(EVIDENCE/'p9_sandbox.json',{'seconds':time.perf_counter()-start,'rows':rows,'telemetry':samples})
    assert all(r['actual']['status']==r['expected'] for r in rows),rows
    assert all(r['environment_steps']==0 for r in rows if r['expected'] in ('denied','timeout'))
    print('11/11 sandbox cases matched; see p9_sandbox.json')


if __name__=='__main__':main()
