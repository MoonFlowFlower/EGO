"""G0p: preselected actual practice observations, three frozen formats."""
import argparse
import json
import random
import secrets
import time
from pathlib import Path
from gate_common_v3 import ROOT,BASE,OUT,read,hashes,check_hashes,Client,GateStop,initial_status,finish,resources
from growthlab.records import write_json
from growthlab.forks import file_hash
from growthlab.spatial import FORMATS,representation,nearest_cells
from growthlab.changes import cell_at,appearance
from growthlab.contract import MATERIALS,ENTITIES,validate
from growthlab.decision import obj,string,format_schema

RUN=BASE/'g0p'
SYSTEM='''Read only the supplied structured Crafter observation. dx positive is right,
dy positive is down; all cells are relative to the CURRENT player at (0,0).
Facing is a direction vector. Report the contents of that facing cell and the
nearest visible tree by Manhattan offset. Any equally nearest tree is acceptable.
Return JSON only. Do not execute actions. Missing entity is none. plant_ripe is
null unless a visible plant state supplies it; arrow_direction is empty unless
a visible arrow state supplies it. If no tree is visible, visible=false and dx,
dy, steps are all zero. There are no hidden map or pathfinding questions.'''
SCHEMA=format_schema('perception',obj({'front':obj({'material':string(enum=list(MATERIALS)),
    'entity':string(enum=['none',*ENTITIES]),'plant_ripe':{'type':['boolean','null']},
    'arrow_direction':string(enum=['','up','down','left','right'])}),
    'nearest_tree':obj({'visible':{'type':'boolean'},'dx':{'type':'integer'},'dy':{'type':'integer'},'steps':{'type':'integer','minimum':0}})}))


def answer(obs):
    f=cell_at(obs,obs['facing']);state=f.get('visible_state') or {}
    front={'material':f['material'],'entity':f['entity'] or 'none','plant_ripe':state.get('plant_ripe'),
           'arrow_direction':state.get('arrow_direction','')}
    trees=nearest_cells(obs,'tree')
    return {'front':front,'nearest_trees':[{'visible':True,'dx':c['dx'],'dy':c['dy'],'steps':abs(c['dx'])+abs(c['dy'])} for c in trees]
            or [{'visible':False,'dx':0,'dy':0,'steps':0}]}


def prepare():
    RUN.mkdir(parents=True,exist_ok=False)
    assert read(OUT/'engineering.json')['passed']
    pilot=ROOT/'runs/phase1/pilot';completed=read(pilot/'status.json')['completed']
    seed=secrets.randbits(64);rng=random.Random(seed);cases=[]
    for summary in completed:
        path=Path(summary).parent/'trace.jsonl';entries=[]
        for line,raw in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
            row=json.loads(raw)
            if row['type']=='input':entries.append((line,json.loads(row['messages'][1]['content'])['observation']))
        for index in sorted(rng.sample(range(len(entries)),10)):
            line,obs=entries[index];validate(obs)
            cases.append({'id':f'p_{len(cases):02}','source':str(path.relative_to(ROOT)),'source_sha256':file_hash(path),
                          'line':line,'tick':obs['tick'],'observation':obs,'answer':answer(obs)})
    assert len(cases)==30
    jobs=[{'case':c['id'],'format':mode} for c in cases for mode in FORMATS];rng.shuffle(jobs)
    manifest={'implementation_revision':3,'sampling_seed':seed,'sampling':'Uniform 10 decision-input observations without replacement from each of the 3 completed revision-2 practices; no selection by rationale or answer.',
        'source_sha256':hashes([__file__]),'system':SYSTEM,'response_format':SCHEMA,'formats':list(FORMATS),'cases':cases,'jobs':jobs,
        'criteria':{'front':'exact material/entity/allowed visible state, >=27/30 for selected format',
                    'tree_direction':'same signed horizontal and vertical directions as any minimum-Manhattan tree (or correct absence), >=24/30',
                    'selection':'Highest front_exact + nearest_tree_exact score out of 60; tie: cells, assisted, map in that order. Steps and direction both required for nearest_tree_exact.',
                    'invalid_outputs':'count as incorrect, no content retry','stop':'Do not continue to G0a/b/c or pilot unless selected format satisfies both thresholds; incomplete run is unverified.',
                    'cells':'All three requested comparisons retain the original cell list; helpers and then map are added. No unmeasured list removal.'}}
    write_json(RUN/'manifest.json',manifest);write_json(OUT/'G0p_MANIFEST.json',manifest)
    print({'prepared':True,'observations':30,'decisions':90,'visible_tree_cases':sum(c['answer']['nearest_trees'][0]['visible'] for c in cases)})


def score(content,truth):
    try:
        value=json.loads(content);t=value['nearest_tree']
        assert set(value)=={'front','nearest_tree'} and set(t)=={'visible','dx','dy','steps'}
        assert type(t['visible']) is bool and all(type(t[k]) is int for k in ('dx','dy','steps'))
        sign=lambda n:(n>0)-(n<0)
        direction=any(t['visible']==x['visible'] and sign(t['dx'])==sign(x['dx']) and sign(t['dy'])==sign(x['dy']) for x in truth['nearest_trees'])
        return {'front_exact':value['front']==truth['front'],'tree_direction':direction,
                'tree_exact':t in truth['nearest_trees'],'parsed':value,'invalid':False}
    except (ValueError,KeyError,TypeError,AssertionError):return {'front_exact':False,'tree_direction':False,'tree_exact':False,'parsed':None,'invalid':True}


def report():
    manifest=read(RUN/'manifest.json');status=read(RUN/'status.json')
    results=[read(p) for p in sorted((RUN/'results').glob('*.json'))];table=[]
    for mode in FORMATS:
        group=[r for r in results if r['job']['format']==mode]
        table.append({'format':mode,'n':len(group),**{k:sum(r['score'][k] for r in group) for k in ('front_exact','tree_direction','tree_exact','invalid')}})
    complete=all(g['n']==30 for g in table)
    selected=max(table,key=lambda g:g['front_exact']+g['tree_exact']) if complete else None
    passed=selected['front_exact']>=27 and selected['tree_direction']>=24 if selected else None
    result={'manifest_path':'G0p_MANIFEST.json','status':status,'formats':table,'selected':selected['format'] if selected else None,
            'passed':passed,'resources':resources(RUN),'results':results}
    write_json(OUT/'G0p.json',result)
    lines=['# G0p：实现修订 3 的观察格式闸门','',
        f"完成 {len(results)}/90 次读取；选择：{result['selected'] or '未定'}；达到预登记判据：{passed if passed is not None else '未验证'}。",'',
        '| 格式 | n | 正前方完全正确 | 最近树方向正确 | 最近树方向和步数正确 | 非法输出 |','|---|---:|---:|---:|---:|---:|']
    for r in table:lines.append(f"| {r['format']} | {r['n']} | {r['front_exact']}/{r['n']} | {r['tree_direction']}/{r['n']} | {r['tree_exact']}/{r['n']} | {r['invalid']} |")
    lines+=['','30 个观察在调用前从三个已完成练习各随机抽 10 个，未按理由或答案筛选；只使用旧练习轨迹，不用测试种子。标准答案与辅助表示都仅从同一份允许观察计算。最近树有并列时接受任一并列最小曼哈顿偏移。无树样本要求回答不可见。','',
        '按前方完全正确数 + 最近树精确偏移正确数选择最高格式；同分按 cells → assisted → map。通过线为所选格式前方至少 27/30、方向至少 24/30。非法输出计错，不为内容重试。三种格式均保留原列表；不删除未经该比较检验的字段。','',
        '[冻结清单](G0p_MANIFEST.json) / [逐次结果](G0p.json)。只证明这些格式下的读取记录，不作学习或能力判决。','',
        '```json',json.dumps(result['resources'],ensure_ascii=False,indent=2),'```']
    (OUT/'G0p.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    print({'formats':table,'selected':result['selected'],'passed':passed,'stop':status['stop']})


def run():
    manifest=read(RUN/'manifest.json');check_hashes(manifest['source_sha256'])
    if (RUN/'status.json').exists():raise ValueError('g0p_already_started')
    status=initial_status();write_json(RUN/'status.json',status);client=None
    try:
        client=Client(RUN,status);cases={c['id']:c for c in manifest['cases']}
        for job in manifest['jobs']:
            identity=job['case']+'_'+job['format'];client.context={'stage':'G0p','id':identity}
            c=cases[job['case']]
            prompt=[{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps(representation(c['observation'],job['format']),ensure_ascii=False,separators=(',',':'))}]
            content,meta=client.decide(prompt,response_format=SCHEMA,max_tokens=512)
            write_json(RUN/'results'/(identity+'.json'),{'job':job,'output':content,'score':score(content,c['answer']),'meta':meta})
            status['completed'].append(identity);write_json(RUN/'status.json',status)
    except Exception as error:status['stop']=str(error) if isinstance(error,(GateStop,ValueError)) else type(error).__name__
    finally:finish(RUN,status,client,manifest['source_sha256'])
    report()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','run','report']);args=p.parse_args()
    {'prepare':prepare,'run':run,'report':report}[args.mode]()
