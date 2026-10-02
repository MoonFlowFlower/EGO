"""One finite write/recall/delete/restart contract check per real adapter."""
import argparse
import time
from .adapters import ADAPTERS, scope
from .core import Store
from .provider import ROOT, write_json

def main():
    p=argparse.ArgumentParser();p.add_argument('arm',choices=list(ADAPTERS));p.add_argument('--id',default='01');a=p.parse_args()
    folder=ROOT/'runs'/f'smoke-{a.arm}-{a.id}'
    if folder.exists():raise ValueError('Use a fresh smoke ID; automatic replay prohibited')
    folder.mkdir(parents=True)
    store=Store(folder/'raw.sqlite')
    e={'id':'smoke-event','kind':'user_statement','actor':'岚','at':100,
       'text':'岚明确说：我在做设计的时候不要弹窗，想分享可以写成信，等我空了再看。'}
    store.append(e);scope(folder.name)
    kw={'bank':'egolab-'+folder.name} if a.arm=='hindsight' else {}
    adapter=ADAPTERS[a.arm](store,folder/'backend',**kw)
    start=time.perf_counter();adapter.retain([e]);adapter.flush();write_time=time.perf_counter()-start
    start=time.perf_counter();evidence=adapter.recall('岚正在做设计，她有分享欲，应该如何联系岚？');read_time=time.perf_counter()-start
    write_json(folder/'recall-raw.json',adapter.last_raw)
    if not any('smoke-event' in r['source_ids'] for r in evidence):
        raise AssertionError('Recall did not resolve the original event')
    adapter.close()
    adapter=ADAPTERS[a.arm](store,folder/'backend',**kw)
    restored=adapter.recall('岚设计时希望怎么分享？')
    assert any('smoke-event' in r['source_ids'] for r in restored)
    store.forget(['smoke-event']);adapter.forget(['smoke-event'])
    after=adapter.recall('岚设计时希望怎么分享？')
    assert not after
    adapter.close();store.close()
    report={'arm':a.arm,'real_backend':True,'write_s':write_time,'recall_s':read_time,
            'evidence':evidence,'restart_ok':True,'deleted_recall':after}
    write_json(folder/'result.json',report);print({'arm':a.arm,'ok':True,'write_s':write_time,'recall_s':read_time})

if __name__=='__main__':main()
