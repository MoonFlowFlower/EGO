"""Read-only G0 scoring/reporting; thresholds and action targets are frozen."""
import copy
import datetime
import json
import sqlite3
import statistics
from collections import Counter
from pathlib import Path

from gate_phase1 import RUN, OUT, ROOT, read, a_messages, check_lock
from growthlab.contract import validate
from growthlab.decision import MEMORY_TOKENS, SYSTEM
from growthlab.consolidation import B_SYSTEM
from growthlab.memory import compact
from growthlab.records import write_json


def fraction(k,n):
    return f'{k}/{n} ({k/n:.0%})' if n else '0/0（未验证）'


def main():
    manifest=read(RUN/'manifest.json');status=read(RUN/'status.json')
    if (RUN/'interruption.json').exists():
        interruption=read(RUN/'interruption.json')
        status={**status,'interruption':interruption,'stop':'superseded_by_revision3',
                'finished_unix':interruption['stopped_unix'],
                'elapsed_seconds':interruption['stopped_unix']-status['started_unix']}
    raw=[json.loads(line) for line in (RUN/'calls.jsonl').read_text(encoding='utf-8').splitlines()]
    results={p.stem:read(p) for p in sorted((RUN/'results').glob('*.json'))}
    cases={c['id']:c for c in manifest['a_cases']}
    a={k:v for k,v in results.items() if k.startswith('a_')}
    b={k:v for k,v in results.items() if k.startswith('b_')}
    c={k:v for k,v in results.items() if k.startswith('c_')}
    groups=[]
    for fact in ('neutral','supplement','contrary'):
        for condition in ('none','true','false'):
            for arm in ('B','A'):
                rows=[v for v in a.values() if cases[v['job']['case']]['fact']==fact and v['job']['condition']==condition and v['job']['arm']==arm]
                true=sum(r['follow_true_target'] for r in rows);false=sum(r['follow_false_target'] for r in rows)
                groups.append({'fact':fact,'condition':condition,'arm':arm,'completed':len(rows),'planned':10,
                               'follow_true_target':true,'follow_false_target':false,
                               'follow_memory':true if condition=='true' else false if condition=='false' else None,
                               'invalid_outputs':sum(r['decode_error'] is not None for r in rows),
                               'next_actions':dict(Counter(str(r['next_action']) for r in rows))})
    neutral=[g for g in groups if g['fact']=='neutral' and g['arm']=='B' and g['condition']!='none']
    a_pass=all(g['follow_memory']>=8 for g in neutral) if all(g['completed']==10 for g in neutral) else None
    b_pass=sum(r['passed'] for r in b.values())>=8 if len(b)==10 else None
    c_pass=all(r['passed'] for r in c.values()) if len(c)==10 else (False if any(not r['passed'] for r in c.values()) else None)
    # Independently check actual request packets against the pre-call specification.
    audit=Counter();errors=[]
    job_by_id={'a_'+j['case']+'_'+j['arm']+'_'+j['condition']:j for j in manifest['a_jobs']}
    for event in raw:
        if event['type']!='request':continue
        context=event['context'];prompt=event['messages'];packet=json.loads(prompt[1]['content'])
        try:
            assert len(compact(packet['memory']).encode())<=MEMORY_TOKENS
            assert len(json.dumps({'messages':prompt,'response_format':event['response_format']}).encode())<=60000
            if context['stage']=='G0a':
                j=job_by_id[context['id']]
                assert prompt==a_messages(cases[j['case']],j['arm'],j['condition'])
                validate(packet['observation']);assert prompt[0]['content']==SYSTEM
                assert set(packet)=={'observation','goal','memory','recent','previous_changes'}
                assert packet['recent']==[] and packet['previous_changes']==[]
                audit['frozen_a_request_packets']+=1
            else:
                assert prompt[0]['content']==B_SYSTEM
                assert set(packet)=={'goal','actions','memory','experiences'}
                assert all(e['type']=='transition' for e in packet['experiences'])
                audit['bounded_frozen_consolidation_packets']+=1
        except (AssertionError,ValueError,KeyError,TypeError) as error:
            errors.append({'context':context,'error':type(error).__name__})
    assert all(v['executed_actions']==0 for v in a.values())
    check_lock(manifest);audit['frozen_source_hashes']=len(manifest['source_sha256'])
    responses=[e for e in raw if e['type']=='response'];failures=[e for e in raw if e['type']=='error']
    charge_ids={e['meta']['charge_id'] for e in responses}|{x['id'] for e in failures for x in e['charges']}
    charge_ids|={x['id'] for x in status.get('interruption',{}).get('unreturned_reservations',[])}
    connection=sqlite3.connect((ROOT/'runs/phase1/budget.sqlite').as_uri()+'?mode=ro',uri=True)
    charges=[dict(zip(('id','usd','status'),r)) for r in connection.execute('SELECT id,usd,status FROM charges')];connection.close()
    gate_charges=[x for x in charges if x['id'] in charge_ids]
    totals=lambda rows:{'reported_usd':sum(x['usd'] for x in rows if x['status']=='reported'),
                        'unknown_reserved_usd':sum(x['usd'] for x in rows if x['status']!='reported'),
                        'occupied_usd':sum(x['usd'] for x in rows),'requests':len(rows)}
    closing=read(OUT/'pilot_budget_close.json')
    pre_g0=[x for x in charges if x['id'] not in charge_ids]
    if status.get('finished_unix'):
        for row in closing['charges']:
            subset=[x for x in pre_g0 if x['status']==row['status']]
            assert len(subset)==row['requests'] and abs(sum(x['usd'] for x in subset)-row['usd'])<1e-12
        audit['pre_g0_ledger_reconciled']=1
    latency=[e['meta']['latency_s'] for e in responses]
    gpu=[]
    for sample in status['telemetry']:
        try:gpu.append([float(x) for x in sample['gpu_csv_C_MHz_MiB_W'].split(',')])
        except (ValueError,KeyError):pass
    thermal={'samples':len(status['telemetry']),'all_ac':all(s['ac_online'] is True for s in status['telemetry']),
             'gpu_min_C_MHz_MiB_W':[min(s[i] for s in gpu) for i in range(4)] if gpu else None,
             'gpu_max_C_MHz_MiB_W':[max(s[i] for s in gpu) for i in range(4)] if gpu else None}
    saved_results=copy.deepcopy(results)
    for v in saved_results.values():
        if 'memory' in v:v['memory']['records']=[r for r in v['memory']['records'] if r['kind']!='experience']
    result={'purpose':'G0 only; not E1; no learning claim','status':status,'criteria':manifest['criteria'],
            'a_groups':groups,'gates':{'G0a':a_pass,'G0b':b_pass,'G0c':c_pass},
            'counts':{'a_decisions':len(a),'b_datasets':len(b),'b_passed':sum(r['passed'] for r in b.values()),
                      'c_rounds':len(c),'c_passed':sum(r['passed'] for r in c.values()),
                      'requests_including_retries':sum(e['type']=='request' for e in raw),'returned_calls':len(responses)},
            'gate_charges':gate_charges,'gate_cost':totals(gate_charges),'phase1_all_cost':totals(charges),
            'latency_s':{'median':statistics.median(latency) if latency else None,'max':max(latency) if latency else None},
            'thermal':thermal,'audit':{'passed':not errors,'checks':dict(audit),'errors':errors},
            'results':saved_results,'raw_folder':str(RUN.relative_to(ROOT))}
    seed_path=RUN/'c/seed.json'
    if seed_path.exists():
        seed=read(seed_path);seed['memory']['records']=[r for r in seed['memory']['records'] if r['kind']!='experience']
        write_json(OUT/'G0_seed.json',seed)
    write_json(OUT/'G0.json',result)
    verdict=lambda value:'通过预先登记判据' if value is True else '未通过预先登记判据' if value is False else '未验证（样本未齐）'
    lines=['# G0：实现修订 2 的历史记录','',
        '**本批被实现修订 3 的新指令替代，已停止，不与新数据混用。** 本轮只检查管道，不作学习、能力或 A/B 优劣结论。预实验在 G0 授权到达前已因 HTTP 502 停止；没有重启。未修改冻结运行时代码、提示词、测试种子、日程或写入校验规则。','',
        '开跑前固定的局面、种子、顺序、判据和计分方式见 [G0_MANIFEST.json](G0_MANIFEST.json)，逐次决定、卡片、程序评分及费用见 [G0.json](G0.json)。原始请求/回执、数据库与逐次整理全文在本机 `runs/phase1/g0/`。','',
        f"G0a：**{verdict(a_pass)}**；G0b：**{verdict(b_pass)}**（{sum(r['passed'] for r in b.values())}/{len(b)} 份）；G0c：**{verdict(c_pass)}**（{sum(r['passed'] for r in c.values())}/{len(c)} 轮保留要求成立）。",'',
        'G0a 使用 30 个独立构造的允许观察局面，每类 10 个；每个局面只改变记忆，真卡/假卡/无记忆及 A/B 的观察、目标、系统提示完全一致。B 直接输入规则卡，A 输入逐字段等价文字笔记，均绕过检索。只询问下一决定，不执行动作或生成程序。','',
        '计分预先固定：中性事实选卡中声称放工作台的符号；补充先验真卡选 place_table、假卡选 make_wood_pickaxe；违背先验真卡选朝成熟植物的唯一最短路径第一步、假卡选面前牛的 do。复杂程序若没有第一句字面 act 则不计跟随；无记忆条件分别列两个目标动作的比例。此处的窄动作定义与所有原始理由一并保留。违背先验使用约定的合成后果，没有运行牛的变体环境。','',
        '| 事实 | 记忆条件 | B 跟随 | A 跟随 |','|---|---|---|---|']
    for fact in ('neutral','supplement','contrary'):
        for condition in ('none','true','false'):
            values=[]
            for arm in ('B','A'):
                g=next(g for g in groups if g['fact']==fact and g['condition']==condition and g['arm']==arm)
                values.append((f"真目标 {fraction(g['follow_true_target'],g['completed'])}；假目标 {fraction(g['follow_false_target'],g['completed'])}"
                               if condition=='none' else fraction(g['follow_memory'],g['completed'])))
            lines.append(f"| {fact} | {condition} | {values[0]} | {values[1]} |")
    lines+=['','通过线只用于 B 中性真卡、假卡，各至少 8/10；补充先验、违背先验与 A 均只报告。没有显著性检验。','',
        f'G0b 已完成 {len(b)}/10 次整理。预登记的 10 份数据为评估器清场后的合成记录集：5 份工作台先失败再放置并制作成功，5 份改名动作各 3 次放出工作台。转向、清场和试次间移动属于夹具构造；这不属于自主练习。计划调用冻结的 consolidate，每份一次；判据要求至少一张被接受卡，且所有被接受卡都有有效引用、至少一条引用经历满足前提，并在该数据集所有适用经历上预测正确。空提案、引用不适用的空泛卡不算成功。','',
        '| 记录集 | 正确 / 接受卡 | 整理拒收数 | 判据 |','|---|---:|---:|---|']
    for name,v in b.items():
        rejected=sum(not p.get('accepted',False) for p in v['sleep'].get('results',[]))
        lines.append(f"| {name} | {sum(r['correct'] for r in v['cards'])} / {len(v['cards'])} | {rejected} | {'满足' if v['passed'] else '不满足'} |")
    lines+=['',f'G0c 已完成 {len(c)}/10 轮。预登记计划是在独立存储里注入两张有真实夹具见证的正确全局卡，隔离首次抽取的不确定性。每轮复用相同的 b_00 证据编号，加一个新世界的 3 步无关记录，连续整理同一份记忆 10 轮。程序核对种子卡的每个具名预期仍有活动卡覆盖，并核对活动卡在全部适用证据上有无矛盾。运行时仍使用原有写入机制，未提前加预测正确或反例约束。','',
        '| 轮次 | 保留的种子预测 | 矛盾预测条数 | 判据 |','|---|---:|---:|---|']
    for name,v in c.items():lines.append(f"| {v['round']} | {sum(bool(r['equivalent_active_ids']) for r in v['retained'])} / 2 | {len(v['contradictions'])} | {'满足' if v['passed'] else '不满足'} |")
    lines+=['','调用、费用与资源：','', '```json', json.dumps({k:result[k] for k in ('counts','gate_cost','phase1_all_cost','latency_s','thermal')},ensure_ascii=False,indent=2),
            json.dumps({'concurrency':1,'elapsed_seconds':status.get('elapsed_seconds'),'stop':status['stop'],'audit':result['audit']},ensure_ascii=False,indent=2),'```','',
            '失败、偏离和后续边界：','',
            f"- 当前传输停止：{status['stop'] or '无'}；错误/重试 {len(failures)} 次；未完成的逻辑调用 {200-len(a)-len(b)-len(c)} 次。未知费用保留，不当作零费用。",
            '- G0a/G0b 若未过，不恢复预实验；当前预实验已经停止。G0c 单独失败不触发该暂停条件。没有自动改表示、改提示词或重跑以跨过判据。',
            '- 新卡/改卡在引用经历上预测正确，以及替换必须引用矛盾经历，这两项运行时写入规则尚未添加，按授权留到 G0c 后、E1 之前。',
            '- G0a 绕过检索，不验证检索质量；G0b/G0c 使用清楚的合成记录，不证明自主探索后抽取或迁移；G0c 只覆盖这批证据和十轮。',
            '- 费用是回执与保守预留；GPU 为整机采样，不能归因于云端推理；CPU 温度未验证。']
    (OUT/'G0.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    print({k:result[k] for k in ('gates','counts','gate_cost','phase1_all_cost','audit')})


if __name__=='__main__':main()
