"""Bounded storage/retrieval and predictor probes. Synthetic, not model semantics.

Run python tools/memory_benchmark.py --events 10000 --out evidence_v06/benchmark
No API, no user data, no modification to any live memory directory.
"""
from __future__ import annotations
from pathlib import Path
import argparse,json,random,statistics,tempfile,time,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from switchlab.memory.store import MemoryStore,encode,code_fingerprint
from switchlab.memory import learning
BASE=1800000000.
def run(out,events):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if not 100<=events<=100000:raise ValueError('events 100..100000')
    results={'source_sha256':code_fingerprint()};start=time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='memory_bench_') as folder:
        path=Path(folder)/'life.db';s=MemoryStore(path);sources=[]
        for title in ('星之海AZ009','雾中庭院BK037','蓝羽协议XY519'):
            raw='我们明天20:00一起读'+title;mid=s.apply('message',{'text':raw},at=BASE)['id']
            e=s.apply('interpret',{'source':mid,'claims':[],'commitments':[{'op':'create','title':title,'category':'reading','quote':raw,'when':'明天20:00','accept':True}]},at=BASE)
            sources.append((mid,title,e['result']['commitments'][0]))
        t=time.perf_counter()
        for i in range(events):s.apply('message',{'text':f'合成干扰消息{i:06d}：今天讨论天气、食物、散步，不修改此前约定。标记N{i:06d}'},at=BASE+i+1)
        results['writes']={'synthetic_distractors':events,'seconds':time.perf_counter()-t,'independent_roots':s.db.execute('SELECT count(*) FROM observations').fetchone()[0]}
        old=sources[0];raw='取消这次星之海AZ009';mid=s.apply('message',{'text':raw},at=BASE+events+2)['id']
        s.apply('interpret',{'source':mid,'claims':[],'commitments':[{'op':'cancel','id':old[2],'expected_revision':1,'quote':raw}]},at=BASE+events+2)
        pid=s.person_id;s.close();s=MemoryStore(path)
        t=time.perf_counter();checks=[]
        for mid,title,cid in sources:
            matches=s.search(title,limit=8)['items'];ctx=s.context(title,budget_bytes=12000)
            checks.append({'query':title,'raw_source_found':any(r['id']==mid for r in matches),
                'effective_revision_present':any(c['id']==cid and c['revision']==s.commitment(cid)['revision'] for c in ctx['effective_commitments']),
                'context_bytes':len(encode(ctx).encode())})
        results['retrieval']={'checks':checks,'seconds':time.perf_counter()-t,'semantic_paraphrases_tested':False}
        recent={r['id'] for r in s.recent(limit=16)['items']};results['recent_16_baseline']={'original_sources_visible':sum(mid in recent for mid,_,_ in sources),'total':len(sources)}
        due=s.due(BASE+3*86400);results['future_memory']={'due_count':len(due),'cancelled_present':any(c['id']==old[2] for c in due),'history_reloaded':pid==s.person_id,
            'simple_structured_ledger_baseline':'same due selection by indexed current status; no unique cognitive claim'}
        cp=s.export();t=time.perf_counter();r=MemoryStore.from_export(Path(folder)/'replay.db',cp)
        results['replay']={'events':len(cp['journal']),'seconds':time.perf_counter()-t,'equal':r.projection_digest()==s.projection_digest()};r.close()
        t=time.perf_counter();s.backup(Path(folder)/'backup.db');b=MemoryStore(Path(folder)/'backup.db')
        results['backup']={'equal':b.projection_digest()==s.projection_digest(),'seconds':time.perf_counter()-t,'db_bytes':path.stat().st_size};b.close();s.close()
    rows=[]
    for seed in range(12):
        rng=random.Random(seed);m=learning.initial();counts={0:[1.,1.],1:[1.,1.]};history=[]
        for i in range(160):
            category=rng.randrange(2);x=[1.,float(category),0.,0.];y=float(rng.random()<(0.2 if category else 0.8))
            p=learning.predict(m,x);a,b=counts[category];simple=a/(a+b)
            history.append(((p-y)**2,(simple-y)**2,(.5-y)**2))
            learning.update(m,x,y);counts[category][0 if y else 1]+=1
        rows.append({'seed':seed,'online_logistic_brier':statistics.mean(x[0] for x in history[-80:]),'category_count_brier':statistics.mean(x[1] for x in history[-80:]),'frozen_half_brier':.25})
    results['predictor']={'synthetic_lives':rows,'mean_online_brier':statistics.mean(r['online_logistic_brier'] for r in rows),'mean_frequency_brier':statistics.mean(r['category_count_brier'] for r in rows),
       'frozen_brier':.25,'meaning':'prediction in an engineered 2-category synthetic process, not human preferences/semantics'}
    if results['source_sha256']!=code_fingerprint():raise RuntimeError('Runtime changed during benchmark; do not publish these results')
    results['seconds_total']=time.perf_counter()-start
    results['contract']='Bounded synthetic engineering/proxy evidence. No real-model semantics, perpetual memory, world understanding, or EGO readiness claim.'
    (out/'result.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    text=f'''# v0.6 有界记忆与学习实验\n\n全部为合成事件，不是你的对话，也没有请求语言模型。\n\n- 干扰消息：{events:,} 条；独立保存根记录 {results['writes']['independent_roots']:,} 条。\n- 写入时间：{results['writes']['seconds']:.2f} 秒（仅当前容器，不是Windows性能承诺）。\n- 精确名字/中文片段召回：{sum(x['raw_source_found'] for x in checks)}/{len(checks)}；有效版本读入 {sum(x['effective_revision_present'] for x in checks)}/{len(checks)}。\n- 清空工作内存并重新打开后，个体ID保留：{results['future_memory']['history_reloaded']}。取消的旧约定进入到期集合：{results['future_memory']['cancelled_present']}。\n- 同一历史最近16条窗口能直接看到原始记录：{results['recent_16_baseline']['original_sources_visible']}/{len(sources)}。该比较只说明窗口截断的限制，不能证明混合召回优于所有记忆方法。\n- 索引化承诺表＋规则时钟也会得到相同的到期选择；本实验不支持独特自主性。\n- {results['replay']['events']:,} 条记录输入复算一致：{results['replay']['equal']}，用时 {results['replay']['seconds']:.2f} 秒；备份恢复一致：{results['backup']['equal']}。\n- 中文换说法、反讽与事实使用的真实LLM语义能力：**未测**。\n\n## 学习对照\n\n12条独立合成流；最后80步Brier误差均值，越低越好：\n\n| 方法 | Brier |\n|---|---:|\n| 在线逻辑预测器 | {results['predictor']['mean_online_brier']:.6f} |\n| 按类别计数的简单基线 | {results['predictor']['mean_frequency_brier']:.6f} |\n| 冻结0.5预测 | 0.250000 |\n\n这只测试预设特征中的反馈适应。简单频次基线有竞争力，不能将梯度更新包装为开放式价值起源。行为接入由test_memory_prospective中的历史/冻结干预另测；长期净收益仍未知。\n\n原始数据和逐种子结果见result.json。存储可靠性、语义理解、机制参与和比较价值是不同结论。\n'''
    (out/'BENCHMARK.md').write_text(text,encoding='utf8');print(json.dumps({k:v for k,v in results.items() if k!='predictor'},ensure_ascii=False,indent=2));return results
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--events',type=int,default=10000);p.add_argument('--out',default='evidence_v06/benchmark');a=p.parse_args();run(a.out,a.events)
