"""Descriptive readout. No inference tests, no resampling or scoring adjustment."""
import difflib
import json
import re
import statistics
from collections import Counter
from pathlib import Path
from gate_common_v3 import ROOT,read,resources
from growthlab.records import write_json

OUT=ROOT/'evidence/phase1/revision3_round2'
RUN=ROOT/'runs/phase1/revision3_round2/g0p2'


def lines(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []


def reason_statistics(decisions):
    rows=[];position_rows=[];similar=[]
    for index,(choice,truth) in enumerate(decisions):
        reason=choice.get('reason','')
        if choice.get('kind')=='action' and choice.get('action')=='do' and re.search(r'\btrees?\b|树',reason,re.I) and re.search(r'front|ahead|facing|前方|面前|正前',reason,re.I):
            rows.append({'decision_index':index,'reason':reason,'actual_front':truth,'wrong':truth['material']!='tree'})
        for match in re.finditer(r"(?:I\s+am(?:\s+at)?|I'm\s+at|my\s+(?:current\s+)?position|当前位置|我在|我位于)[^()\n]{0,30}\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)",reason,re.I):
            xy=list(map(int,match.groups()))
            position_rows.append({'decision_index':index,'position':xy,'nonzero':xy!=[0,0],'reason':reason})
        if index:
            normalize=lambda value:' '.join(value.lower().split())
            ratio=difflib.SequenceMatcher(None,normalize(decisions[index-1][0].get('reason','')),normalize(reason)).ratio()
            similar.append({'decision_index':index,'ratio':ratio,'at_least_0_9':ratio>=.9})
    return {'tree_claims':len(rows),'tree_claims_wrong':sum(x['wrong'] for x in rows),'tree_claim_records':rows,
            'explicit_position_decisions':len({x['decision_index'] for x in position_rows}),
            'nonzero_position_decisions':len({x['decision_index'] for x in position_rows if x['nonzero']}),'position_records':position_rows,
            'adjacent_pairs':len(similar),'similar_adjacent_pairs':sum(x['at_least_0_9'] for x in similar),'similarity_records':similar}


def live_episode(folder):
    trace=lines(folder/'trace.jsonl');assessments=[r for r in trace if r['type']=='front_assessment']
    decisions=[];current=None;navigation=[];packet=None
    for row in trace:
        if row['type']=='input':packet=json.loads(row['messages'][1]['content'])
        if row['type']=='front_assessment':current=row
        if row['type']=='decision':
            assert current is not None
            decisions.append((row['choice'],current['expected']))
        if row['type']=='execution':
            result=row['result']
            if 'target_name' in result:navigation.append(result)
            navigation+=result.get('navigation',[])
    summary=read(folder/'summary.json') if (folder/'summary.json').exists() else None
    direct_do=[(choice,truth) for choice,truth in decisions if choice['kind']=='action' and choice['action']=='do']
    return {'episode':folder.name,'summary':summary,'n':len(assessments),'front_correct':sum(x['correct'] for x in assessments),
            'invalid_outputs':sum(not x['protocol_valid'] for x in assessments),'assessments':assessments,
            'decisions':[{'choice':c,'actual_front':t} for c,t in decisions],
            'do_front_seen_tree_actual_not_tree':sum(c['front_seen']['material']=='tree' and t['material']!='tree' for c,t in direct_do),
            'direct_do_decisions':len(direct_do),'reason_audit':reason_statistics(decisions),
            'goto_calls':len(navigation),'goto_steps':sum(r['steps'] for r in navigation),
            'goto_stop_reasons':dict(Counter(r['status'] for r in navigation)),'navigation':navigation}


def aggregate_live(episodes):
    n=sum(e['n'] for e in episodes);correct=sum(e['front_correct'] for e in episodes)
    calls=[c for e in episodes if e['summary'] for c in e['summary']['calls']]
    latencies=[c['latency_s'] for c in calls];stop_counts=Counter()
    for e in episodes:stop_counts.update(e['goto_stop_reasons'])
    result={'episodes':len(episodes),'n':n,'front_correct':correct,'front_accuracy':correct/n if n else None,
            'invalid_outputs':sum(e['invalid_outputs'] for e in episodes),
            'latency_median_s':statistics.median(latencies) if latencies else None,
            'latency_max_s':max(latencies) if latencies else None,
            'reported_usd':sum(c.get('cost_usd') or 0 for c in calls),'unknown_receipts':sum(c.get('cost_usd') is None for c in calls),
            'do_front_seen_tree_actual_not_tree':sum(e['do_front_seen_tree_actual_not_tree'] for e in episodes),
            'goto_calls':sum(e['goto_calls'] for e in episodes),'goto_steps':sum(e['goto_steps'] for e in episodes),'goto_stop_reasons':dict(stop_counts)}
    for key in ('tree_claims','tree_claims_wrong','explicit_position_decisions','nonzero_position_decisions','adjacent_pairs','similar_adjacent_pairs'):
        result[key]=sum(e['reason_audit'][key] for e in episodes)
    return result


def history():
    result=[]
    for path in read(ROOT/'runs/phase1/pilot/status.json')['completed']:
        rows=lines(Path(path).parent/'trace.jsonl');obs=None;decisions=[]
        for row in rows:
            if row['type']=='input':obs=json.loads(row['messages'][1]['content'])['observation']
            if row['type']=='decision':
                front=next(c for c in obs['cells'] if [c['dx'],c['dy']]==obs['facing'])
                decisions.append((row['choice'],{'material':front['material'],'entity':front['entity'] or 'none'}))
        result.append({'episode':Path(path).parent.name,'decisions':len(decisions),**reason_statistics(decisions)})
    return result


def report():
    manifest=read(RUN/'manifest.json');status=read(RUN/'status.json');cases={c['id']:c for c in manifest['cases']}
    qa=[read(p) for p in sorted((RUN/'qa').glob('*.json'))];table=[]
    for label in ('K0','K1','K2'):
        group=[r for r in qa if r['job']['format']==label]
        entry={'format':label,'n':len(group),**{k:sum(r['score'][k] for r in group) for k in ('front_exact','tree_direction','tree_exact','invalid')}}
        for subset in ('front_differs_from_underfoot','front_material_differs_from_underfoot'):
            rows=[r for r in group if cases[r['job']['case']][subset]]
            entry[subset]={'n':len(rows),'front_exact':sum(r['score']['front_exact'] for r in rows)}
        rows=[r for r in group if cases[r['job']['case']]['answer']['nearest_trees'][0]['visible']]
        entry['visible_tree_only']={'n':len(rows),'tree_direction':sum(r['score']['tree_direction'] for r in rows),'tree_exact':sum(r['score']['tree_exact'] for r in rows)}
        table.append(entry)
    selected=status.get('selected');selected_row=next((r for r in table if r['format']==selected),None)
    qa_passed=bool(selected_row and selected_row['n']==60 and selected_row['front_exact']>=54 and selected_row['tree_direction']>=48)
    episodes=[live_episode(p) for p in sorted((RUN/'episodes').glob('*')) if p.is_dir()]
    arms={arm:aggregate_live([e for e in episodes if e['episode'].startswith(arm+'_')]) for arm in ('main','reasoning')}
    enough=arms['main']['episodes']==3 and arms['main']['n']>=90
    completed=all(g['n']==60 for g in table) and len(status['live_completed'])==6 and not status['stop']
    live_passed=arms['main']['front_accuracy']>=.9 if enough else None
    verdict='passed' if completed and enough and qa_passed and live_passed else ('failed' if completed and enough else 'unverified')
    result={'manifest':'G0p2_MANIFEST.json','verdict':verdict,'qa_passed':qa_passed,'live_passed':live_passed,'selected':selected,
            'qa_table':table,'live_arms':arms,'resources':resources(RUN),'status':status,'qa_results':qa,'episodes':episodes,
            'historical_reason_audit':history(),'methods':manifest['descriptive_methods'],
            'downstream':'G0a/b/c and pilot not started by this runner; allowed only after a passed gate and audit.'}
    write_json(OUT/'G0p2.json',result)
    text=['# G0p2：表示 v2 与真实决策读取','',f'状态：{verdict}；所选格式 {selected}；问答判据 {qa_passed}；主臂实战判据 {live_passed}。','',
          '| 格式 | n | 前方完全正确 | 树方向正确 | 树方向步数正确 | 非法输出 |','|---|---:|---:|---:|---:|---:|']
    for r in table:text.append(f"| {r['format']} | {r['n']} | {r['front_exact']}/{r['n']} | {r['tree_direction']}/{r['n']} | {r['tree_exact']}/{r['n']} | {r['invalid']} |")
    text+=['','K0 只作对照。K1/K2 按前方完全正确数 + 树完全正确数选择，同分 K2。问答门槛前方 54/60、树方向 48/60；实战主臂至少 90 次决定，前方材质与实体同时正确至少 90%。非法输出计错，不纠正或重问。','',
           '| 实战臂 | 局数 | 前方正确 / 决定 | 延迟中位秒 | 回执美元 | goto 次数 / 步数 |','|---|---:|---:|---:|---:|---:|']
    for label,r in arms.items():text.append(f"| {label} | {r['episodes']} | {r['front_correct']}/{r['n']} | {r['latency_median_s']} | {r['reported_usd']:.12f} | {r['goto_calls']} / {r['goto_steps']} |")
    text+=['','推理臂使用同三种子、同模型、同路由，仅 reasoning.enabled=true，输出上限 8192（主臂 2048）；只作描述，不进判据。每局独立空 B，40 次决定或结束，不因做成目标提前结束；不整理、不在局间传递经历。','',
           '## 子集和理由粗查','']
    for r in table:
        text.append(f"- {r['format']}：前方内容不同于脚下 {r['front_differs_from_underfoot']}；仅材质不同 {r['front_material_differs_from_underfoot']}；有树子集 {r['visible_tree_only']}。")
    for label,r in arms.items():
        text.append(f"- {label}：do 且自报树但实际非树 {r['do_front_seen_tree_actual_not_tree']} 次；理由声称前方树 {r['tree_claims']} 次、其中实际非树 {r['tree_claims_wrong']}；非零自身位置 {r['nonzero_position_decisions']} 次；相邻理由相似 ≥0.9 {r['similar_adjacent_pairs']}/{r['adjacent_pairs']}；goto 停止原因 {r['goto_stop_reasons']}。")
    text+=['','关键词方法在调用前冻结，包含否定句，只作粗查；Claude 原始粗查代码未提供，85/87 等精确复现未验证。JSON 同时保存按本轮同一方法重算的旧轨迹和新轨迹，不把两种查法直接等同。','',
           '## 费用、运行与停止','', '```json',json.dumps(result['resources'],ensure_ascii=False,indent=2),'```','',
           f"控制停止：{status['stop']}；完整运行：{completed}。CPU 温度未验证；GPU 为整机采样，不归因于云端推理。",'',
           '清单、逐次问答、实战 front_seen/理由/goto 均保留。未过或未验证时不做第三轮表示修复，不跑后续 G0/预实验。不作学习、有效性、组间优劣或显著性结论。','',
           '[冻结清单](G0p2_MANIFEST.json) · [完整 JSON](G0p2.json)']
    (OUT/'G0p2.md').write_text('\n'.join(text)+'\n',encoding='utf-8',newline='\n')
    print({'verdict':verdict,'qa':table,'live':arms,'stop':status['stop']})
    return result


if __name__=='__main__':report()
