"""Scenario-paired estimates; repeated calls are not independent user samples."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import numpy as np
from .provider import ROOT, write_json

def paired(control,treatment):
    def group(rows):
        out=defaultdict(list)
        for r in rows:out[r['case']].append(r)
        return out
    a,b=group(control),group(treatment)
    if not a or set(a)!=set(b):raise ValueError('Incomplete scenario pairing')
    differences=[];families=[]
    for key in sorted(a):
        if sorted(r['repeat'] for r in a[key])!=sorted(r['repeat'] for r in b[key]):
            raise ValueError('Incomplete repeated-trial pairing')
        differences.append(np.mean([r['success'] for r in b[key]])-np.mean([r['success'] for r in a[key]]))
        families.append(a[key][0]['family'])
    d=np.array(differences);f=np.array(families);rng=np.random.default_rng(230923)
    boot=np.zeros(10000)
    for family in sorted(set(families)):
        values=d[f==family]
        boot+=rng.choice(values,size=(10000,len(values)),replace=True).sum(axis=1)/len(d)
    return {'scenario_n':len(d),'difference':float(d.mean()),'ci95':np.quantile(boot,[.025,.975]).tolist(),
            'method':'family-stratified bootstrap of paired scenario means; 10,000 draws; repeated calls averaged first'}

def choose(summaries,comparisons):
    blocked=[arm for arm,s in summaries.items() if s['gates'] or s.get('semantic_pending',0)]
    winner='baseline'
    viable=[arm for arm,p in comparisons.items() if arm not in blocked and p['difference']>.05 and p['ci95'][0]>0]
    if viable:
        best=max(summaries[a]['rate'] for a in viable)
        close=[a for a in viable if best-summaries[a]['rate']<=.05]
        winner=min(close,key=lambda a:(summaries[a].get('unknown_cost_calls',0)>0,summaries[a]['cost'], {'baseline':0,'memos':1,'hindsight':2}[a]))
    return {'research_backend':winner,'blocked_by_gates':blocked,
            'product_integration':'blocked' if winner in blocked else 'requires semantic claim audit and real pet validation',
            'rule':'Positive paired evidence and >5pp benefit required to replace baseline; ties favor cost then deployment simplicity.'}

def calls():
    result=[]
    for path in (ROOT/'runs').glob('batch-*/calls/*.json'):
        row=json.loads(path.read_text(encoding='utf-8'))
        if 'context' not in row and row.get('scope','').startswith('{'):
            row['context']=json.loads(row['scope'])
        result.append(row)
    return result

def attributable_calls(rows,run_id,arm,condition):
    return [r for r in rows if r.get('context',{}).get('run_id')==run_id
            and r['context'].get('split')=='heldout' and r['context'].get('arm')==arm
            and r['context'].get('condition') in (condition,'shared')]

def summary(rows,arm,all_calls,condition='memory',run_id=''):
    latencies=[x for r in rows for x in r['recall_s']]
    writes=[x for r in rows for x in r['write_s']]
    related=attributable_calls(all_calls,run_id,arm,condition)
    return {'episodes':len(rows),'scenarios':len({r['case'] for r in rows}),
        'rate':float(np.mean([r['success'] for r in rows])),
        'transfer_rate':float(np.mean([r['success'] for r in rows if r['family']==3])),
        'sharing_feedback_rate':float(np.mean([r['success'] for r in rows if r['family']==4])),
        'gates':sum(bool(r['gates']) for r in rows),'gate_types':dict(Counter(g for r in rows for g in r['gates'])),
        'semantic_pending':sum(bool(r.get('semantic_pending')) for r in rows),
        'rejected_action_attempts':dict(Counter(g for r in rows for g in r.get('rejected_action_attempts',[]))),
        'missed_contacts':sum(r['missed_contacts'] for r in rows),'false_contacts':sum(r['false_contacts'] for r in rows),
        'expected_contacts':sum(r['expected_contacts'] for r in rows),
        'recall_seconds':{'median':float(np.median(latencies)),'p95':float(np.quantile(latencies,.95))},
        'write_seconds':{'median':float(np.median(writes)),'p95':float(np.quantile(writes,.95))},
        'paid_calls':len(related),'cost':sum((c.get('usage') or {}).get('cost',0) or 0 for c in related),
        'unknown_cost_calls':sum((c.get('usage') or {}).get('cost') is None for c in related),
        'failed_or_incomplete_calls':sum(c['status']!='ok' for c in related)}

def collect(path,conditions,arms):
    expected={c['id'] for c in json.loads((ROOT/'scenarios/heldout.json').read_text(encoding='utf-8'))}
    profile=json.loads((path/'RUN_MANIFEST.json').read_text(encoding='utf-8'))['profile']
    rows=[]
    for file in path.glob('episodes/*/result.json'):
        r=json.loads(file.read_text(encoding='utf-8'))
        if r['case'].startswith('heldout-') and r['condition'] in conditions and r['arm'] in arms:
            if r.get('inference_profile')!=profile or not r.get('real_model'):raise ValueError('Mixed or non-real inference result')
            if not r.get('semantic_calibration'):raise ValueError('Semantic calibration/audit not completed')
            if any(a.get('profile')!=profile for a in r.get('semantic_audits',[])):raise ValueError('Mixed semantic judge profile')
            rows.append(r)
    for condition in conditions:
        for arm in arms:
            current=[r for r in rows if r['condition']==condition and r['arm']==arm]
            if len(current)!=72 or {(r['case'],r['repeat']) for r in current}!={(c,i) for c in expected for i in (1,2,3)}:
                raise ValueError(f'Comparison incomplete: {condition}/{arm} has {len(current)}/72 results')
    return rows

def memory_report(run):
    root=ROOT/'runs'/run;rows=collect(root,['memory'],['baseline','memos','hindsight']);all_calls=calls()
    groups={arm:[r for r in rows if r['arm']==arm] for arm in ['baseline','memos','hindsight']}
    summaries={arm:summary(group,arm,all_calls,run_id=run) for arm,group in groups.items()}
    comparisons={arm:paired(groups['baseline'],groups[arm]) for arm in ['memos','hindsight']}
    result={'kind':'memory','simulation':True,'summaries':summaries,'paired_against_baseline':comparisons,
            'selection':choose(summaries,comparisons),'failures':[r for r in rows if not r['success']]}
    write_json(root/'report.json',result);render(root,result);return result

def growth_report(run):
    root=ROOT/'runs'/run;training=json.loads((root/'training/frozen.json').read_text(encoding='utf-8'))
    arm=training['memory_arm'];rows=collect(root,['frozen','ace'],[arm]);all_calls=calls()
    groups={c:[r for r in rows if r['condition']==c] for c in ['frozen','ace']}
    summaries={c:summary(group,arm,all_calls,c,run_id=run) for c,group in groups.items()}
    comparison=paired(groups['frozen'],groups['ace'])
    adopt=summaries['ace']['gates']==0 and summaries['ace']['semantic_pending']==0 and comparison['ci95'][0]>0 and comparison['difference']>.05
    result={'kind':'growth','memory_arm':arm,'simulation':True,'summaries':summaries,'paired':comparison,
            'adopt_ace':adopt,'training_cost':sum((c.get('usage') or {}).get('cost',0) or 0 for c in all_calls
                if c.get('context',{}).get('run_id')==run and c['context'].get('split')=='development'),
            'failures':[r for r in rows if not r['success']]}
    write_json(root/'report.json',result);render(root,result);return result

def render(root,report):
    lines=['# 真实模型调用下的模拟生活实验','',
        '本报告仅涉及冻结的合成场景。不是独立用户试验，也不表示桌宠长期陪伴效果已得到验证。', '',
        '| 条件 | 行动成功 | 迁移成功 | 分享反馈 | 底线失败轮次 | 召回中位秒 | 召回P95秒 | 归属费用USD |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for arm,s in report['summaries'].items():
        lines.append(f'| {arm} | {s["rate"]:.1%} | {s["transfer_rate"]:.1%} | {s["sharing_feedback_rate"]:.1%} | {s["gates"]} | {s["recall_seconds"]["median"]:.3f} | {s["recall_seconds"]["p95"]:.3f} | {s["cost"]:.6f} |')
    lines+=['','每个保留场景独立存档重复3次。先平均同一场景的重复，再做按六类分层的配对bootstrap；区间仅描述此场景集的不确定性，不外推成人类用户差异。','']
    if report['kind']=='memory':
        for arm,p in report['paired_against_baseline'].items():
            lines.append(f'- {arm} 相对基线：{p["difference"]:+.1%}，95%区间 [{p["ci95"][0]:+.1%}, {p["ci95"][1]:+.1%}]。')
        lines+=['',f'研究后续底座：**{report["selection"]["research_backend"]}**。产品接入状态：{report["selection"]["product_integration"]}。']
    else:
        p=report['paired'];lines += [f'ACE 相对冻结经验：{p["difference"]:+.1%}，95%区间 [{p["ci95"][0]:+.1%}, {p["ci95"][1]:+.1%}]。',
            f'按预定规则默认接入 ACE：**{"是" if report["adopt_ace"] else "否"}**。开发期额外学习费用 ${report["training_cost"]:.6f}。']
    lines+=['','限制：', '',
        '- 自动底线检测覆盖执行器拒绝、来源ID、取消场景、状态恢复和去重；自然语言中的所有事实暗示尚需语义审查，不能仅凭无自动报错批准产品上线。',
        '- 原始输入为模拟材料；保存的提示词、调用回执、召回证据、执行状态和失败均可复查。',
        '- 表内费用按scope归属并包含各候选一次基础索引写入；重试不存在，冷启动、开发、ACE训练另列。共享网关模型加载及向量缓存会影响热运行延迟。',
        '- MemOS 来源删除采用整体重建派生库；Hindsight 初始隔离用clone，导出恢复用原生transfer ZIP重建新bank。真实换机仍需另行验收。','',
        f'失败轮次共 {len(report["failures"])}；详见同目录 report.json，按 case/phase 回查 episodes/*/trace.json。']
    (root/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['memory','growth']);p.add_argument('--run',required=True);a=p.parse_args()
    result=memory_report(a.run) if a.kind=='memory' else growth_report(a.run)
    print(json.dumps(result.get('selection',{'adopt_ace':result.get('adopt_ace')}),ensure_ascii=False))

if __name__=='__main__':main()
