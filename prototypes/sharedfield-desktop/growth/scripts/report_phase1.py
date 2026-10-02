"""Descriptive report from immutable pilot outputs. No significance tests."""
import datetime
import json
import shutil
import sqlite3
import statistics
import sys
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.records import ROOT,write_json

RUN=ROOT/'runs/phase1/pilot';OUT=ROOT/'evidence/phase1'
METRICS=['failure_attempts','capped_steps','decisions','cloud_calls','reported_cost_usd','wall_total_s','prediction_accuracy','prediction_coverage']


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def stats(values):
    values=[v for v in values if v is not None]
    return {'n':len(values),'mean':statistics.mean(values) if values else None,
            'sd':statistics.stdev(values) if len(values)>1 else None}


def fmt(value,digits=2):
    if value['mean'] is None:return '—'
    return f"{value['mean']:.{digits}f} ± {value['sd']:.{digits}f}" if value['sd'] is not None else f"{value['mean']:.{digits}f} (SD 未定义)"


def main():
    status=read(RUN/'status.json');manifest=read(RUN/'manifest.json')
    attempts=[]
    for path in sorted((RUN/'episodes').glob('*/summary.json')):
        row=read(path);job=row['job']
        # Total wall time includes interpreter, fork, environment, route preflight,
        # decision loop, consolidation and final export. Trace-loop time also kept.
        wall=path.stat().st_mtime-(path.parent/'job.json').stat().st_mtime
        row['wall_total_s']=wall;row['wall_measurement']='job-file write to summary-file write, filesystem timestamps'
        row['raw_path']=str(path.relative_to(ROOT));attempts.append(row)
    completed_paths=set(status['completed'])
    completed=[r for r in attempts if str(ROOT/r['raw_path']) in completed_paths]
    grouped=defaultdict(list)
    for row in completed:
        job=row['job'];grouped[f"{job['arm']}_{job['group']}_{job['phase']}"].append(row)
    aggregates={key:{'n':len(rows),'successes':sum(r['success'] for r in rows),
        'censored':sum(r['censored'] for r in rows),'metrics':{m:stats([r.get(m) for r in rows]) for m in METRICS},
        'events':dict(sum((Counter(r['events']) for r in rows),Counter())),
        'prediction_matches':sum(r['prediction_matches'] for r in rows),'prediction_count':sum(r['prediction_count'] for r in rows),
        'predicted_actions':sum(r['predicted_actions'] for r in rows),'eligible_actions':sum(r['prediction_eligible_actions'] for r in rows)} for key,rows in grouped.items()}
    comparisons=[]
    for arm in ('B','A'):
        comparisons += [(f'{arm}_F1_auto_test',f'{arm}_F1_fresh_test'),(f'{arm}_F1_teach_test',f'{arm}_F1_fresh_test'),
                        (f'{arm}_F1_teach_test',f'{arm}_F1_auto_test'),(f'{arm}_F2_train_test',f'{arm}_F2_fresh_test')]
    comparisons += [(f'B_{g}_test',f'A_{g}_test') for g in ('F1_auto','F1_teach','F1_fresh','F2_train','F2_fresh')]
    paired=[]
    for left,right in comparisons:
        l={r['job']['seed']:r for r in grouped[left]};r={x['job']['seed']:x for x in grouped[right]}
        seeds=sorted(set(l)&set(r))
        differences=[{'seed':s,**{m:(l[s][m]-r[s][m] if l[s].get(m) is not None and r[s].get(m) is not None else None) for m in METRICS}} for s in seeds]
        paired.append({'left':left,'right':right,'direction':'left minus right','n':len(seeds),'differences':differences,
                       'metrics':{m:stats([d[m] for d in differences]) for m in METRICS}})
    connection=sqlite3.connect(ROOT/'runs/phase1/budget.sqlite')
    ledger=[{'status':s,'requests':n,'usd':v} for s,n,v in connection.execute('SELECT status,count(*),sum(usd) FROM charges GROUP BY status')];connection.close()
    memory_paths=[]
    for path in sorted((RUN/'snapshots').glob('*_memory.json')):
        destination=OUT/'pilot_memory'/path.name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,destination)
        memory_paths.append(str(destination.relative_to(OUT)))
    # Practice memory after EACH completed episode: full cards/programs/reflections,
    # so appearance time and taught-but-not-persisted cases can be inspected.
    practice=[]
    for row in completed:
        job=row['job']
        if job['phase']!='practice':continue
        source=Path(job['folder'])/'memory_full.json';data=read(source)
        cards=[r for r in data['records'] if r['kind'] in ('general_rule','fact')]
        # Syntactic description only, not a semantic judgement by an LLM.
        table_cards=[r['id'] for r in cards if r['body']['action']=='make_wood_pickaxe' and 'table' in r['body']['preconditions']['nearby'] and r['body']['expected']['inventory'].get('wood_pickaxe')==1]
        destination=OUT/'pilot_memory'/f"{job['arm']}_{job['group']}_practice_{job['index']}.json";destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination)
        practice.append({'arm':job['arm'],'group':job['group'],'episode':job['index']+1,'rules':len(cards),
            'skills':sum(r['kind']=='skill' for r in data['records']),'reflections':sum(r['kind']=='reflection' for r in data['records']),
            'workbench_form_card_ids':table_cards,'sleep':row.get('sleep'),'memory_path':str(destination.relative_to(OUT))})
    latencies=[c['latency_s'] for r in attempts for c in r.get('calls',[]) if 'latency_s' in c]
    thermal=status.get('telemetry',[])+[t for r in attempts for t in r.get('telemetry',[])]
    gpu=[]
    for sample in thermal:
        try:gpu.append([float(x.strip()) for x in sample['gpu_csv_C_MHz_MiB_W'].split(',')])
        except (ValueError,KeyError):pass
    summary={'purpose':'descriptive pilot; not E1','status':status,'manifest':manifest,
        'attempts':attempts,'aggregates':aggregates,'paired':paired,'practice_memory':practice,
        'snapshot_memory_paths':memory_paths,'phase1_all_charges':ledger,
        'latency_s':{'n':len(latencies),'median':statistics.median(latencies) if latencies else None,'max':max(latencies) if latencies else None},
        'thermal':{'samples':len(thermal),'all_ac':all(t.get('ac_online') is True for t in thermal),
            'gpu_min_C_MHz_MiB_W':[min(x[i] for x in gpu) for i in range(4)] if gpu else None,
            'gpu_max_C_MHz_MiB_W':[max(x[i] for x in gpu) for i in range(4)] if gpu else None}}
    write_json(OUT/'pilot_summary.json',summary)
    lines=['# 阶段 1 描述性预实验','',
        '**不是 E1。不做显著性检验，不据此判断学会、有效或 B 优于 A。** 数字用于后续样本量和指标设计。','',
        f"完成 {len(completed)}/78 局（18 练习、60 测试）；已留存 {len(attempts)} 次有汇总的尝试。停止状态：`{status.get('stop') or ('完成' if status.get('finished_unix') else '运行中')}`。",'',
        '冻结设置见 [PILOT_MANIFEST.json](PILOT_MANIFEST.json)。逐局摘要、费用、所有配对差值和并发事件见 [pilot_summary.json](pilot_summary.json)。原始允许观察、执行前依据、逐动作预测、事件和模型输出在本机 `runs/phase1/pilot/episodes/`。测试种子未用于调试；提示词 v2 在开跑前冻结，测试间不传经历。','',
        '以下均值 ± 样本标准差（n−1）。未做出木镐的正常结束回合统一以步数上限截断，包括提前死亡；表中注明截断数。基础设施/协议中止的尝试单列，不伪装成正常完成样本。云决定不含回合末整理，费用和总调用包含整理；总墙钟由 job 文件写入到 summary 文件写入的时间差计量，包含启动、加载和整理。','',
        '| 组 | n | 做出木镐 | 截断 | 失败尝试 | 达成步数（截断） | 云决定 | 费用 USD | 墙钟秒 |',
        '|---|---:|---:|---:|---|---|---|---|---|']
    for arm in ('B','A'):
        for phase in ('practice','test'):
            for group in ('F1_auto','F1_teach','F1_fresh','F2_train','F2_fresh'):
                if phase=='practice' and group.endswith('fresh'):continue
                key=f'{arm}_{group}_{phase}';a=aggregates.get(key)
                if not a:lines.append(f'| {key} | 0 | 未运行/未完成 | — | — | — | — | — | — |');continue
                m=a['metrics'];lines.append(f"| {key} | {a['n']} | {a['successes']} | {a['censored']} | {fmt(m['failure_attempts'])} | {fmt(m['capped_steps'])} | {fmt(m['decisions'])} | {fmt(m['reported_cost_usd'],6)} | {fmt(m['wall_total_s'])} |")
    lines+=['','配对差值方向均为左组减右组；只使用双方都正常完成的相同种子。完整逐种子及全部指标见 JSON。','',
        '| 左组 − 右组 | 配对 n | 失败尝试差 | 截断达成步数差 | 云决定差 |', '|---|---:|---|---|---|']
    for pair in paired:
        m=pair['metrics'];lines.append(f"| {pair['left']} − {pair['right']} | {pair['n']} | {fmt(m['failure_attempts'])} | {fmt(m['capped_steps'])} | {fmt(m['decisions'])} |")
    lines+=['','B 的预测准确率按卡片预测逐条计分，覆盖率按有至少一条适用卡的制作/放置/do 动作计分；do 包含采集和实体互动，不借内部真值挑出成功采集。无预测时准确率未定义。以下同时给出分子/分母。','',
        '| 组 | 正确预测 / 全预测 | 覆盖动作 / 可计动作 | 回合准确率均值 ± SD | 回合覆盖率均值 ± SD |','|---|---|---|---|---|']
    for key,a in aggregates.items():
        if key.startswith('B_'):lines.append(f"| {key} | {a['prediction_matches']} / {a['prediction_count']} | {a['predicted_actions']} / {a['eligible_actions']} | {fmt(a['metrics']['prediction_accuracy'],3)} | {fmt(a['metrics']['prediction_coverage'],3)} |")
    lines+=['','练习结束的全文与出现时间：','', '| 组 / 回合 | 规则 / 技能 / 反思 | 符合工作台卡形式的编号 | 全文 |','|---|---|---|---|']
    for p in practice:lines.append(f"| {p['arm']}_{p['group']} / {p['episode']} | {p['rules']} / {p['skills']} / {p['reflections']} | {', '.join(p['workbench_form_card_ids']) or '无'} | [JSON]({p['memory_path']}) |")
    lines+=['','“符合工作台卡形式”只检查动作 make_wood_pickaxe、前提含 nearby table、预期 wood_pickaxe +1。它不证明必要性、完整性或学会；支持/反例仍以程序记录为准。教学是否送达见每局 teaching 记录；模型是否提出卡、程序是否拒收、重启后是否检索，分别可在 sleep_result、全文存储、input 中核对。没有提案只说明本轮未形成该持久记录，不能反推内部是否学到。','',
        '费用与资源（含失败尝试；阶段 1 账本还含工程调试）：','', '```json',json.dumps({'charges':ledger,'latency_s':summary['latency_s'],'thermal':summary['thermal'],'elapsed_seconds':status.get('elapsed_seconds')},ensure_ascii=False,indent=2),'```','',
        '失败、偏离与未验证：','',
        '- HTTP/协议失败、重试与并发调整保留在原始尝试和 status.events；任何未结束而被取消的在途请求仍保留费用预留。',
        '- 不跑 D8 无关经历组；这是本轮已允许的范围。没有接观察台自由演示，不混入实验数据。',
        '- 记忆采用 UTF-8 字节保守上界，没有伪称已运行该模型原生 tokenizer；两组上界相同。',
        '- GPU 为整机采样，不能归因于云模型；CPU 温度、跨机器复现、操作系统级通用代码沙箱未验证。',
        '- 不产生 E1 判决，不因本批数据修改已冻结提示词。']
    (OUT/'PILOT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    print({'completed':len(completed),'attempts':len(attempts),'stop':status['stop'],'report':str(OUT/'PILOT.md')})


if __name__=='__main__':main()
