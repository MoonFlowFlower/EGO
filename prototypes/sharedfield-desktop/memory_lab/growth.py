"""Official ACE Reflector + Curator, with a bounded transport and life-result feedback."""
import argparse
import ast
import importlib
import json
import os
import re
from pathlib import Path
import sys
import time
import types
from .adapters import TOKENIZER, completion, scope
from .core import canonical, digest, render_lessons
from .provider import ROOT, MODEL, write_json
from .runner import load_cases, setup_base, run_episode

def learning_input(case,trace,events):
    if case['split']!='development':raise ValueError('Only development experiences may update ACE')
    return canonical({'case':case['id'],'teaching_and_sources':events,
        'observed_activity':[{'action':r['action'],'receipt':r['receipt'],
                             'observation_after':r.get('observation_after',{})} for r in trace],
        'instruction':'仅从明确教学、用户反馈和实际执行回执学习。没有评分答案。总结可迁移的条件—行动经验；不要把某个用户习惯推广成所有用户的习惯。动作没有改变状态就不能声称目的完成。每条经验写清适用条件及原始来源ID。'})

def safe_learning_trace(trace,events,entries):
    valid={e['id'] for e in events};safe=[]
    for row in trace:
        sources=set(row.get('input_source_ids',[]))|set(row['action'].get('evidence_ids',[]))
        sources.update(e['id'] for e in row.get('audit_events',[]))
        supplied=row.get('experience_supplied','')
        for entry in entries:
            if '['+entry['id']+']' in supplied:sources.update(entry['source_ids'])
        if sources<=valid:safe.append(row)
    return safe

def components():
    vendor=ROOT/'vendor/ace'
    os.environ['PYTHON_DOTENV_DISABLED']='1'
    sys.path.insert(0,str(vendor))
    # Load the upstream components without ACE's unrelated benchmark/FAISS runners.
    # Their algorithm files are unchanged. Only their documented llm transport is replaced.
    for name,path in [('lab_ace',vendor/'ace'),('lab_ace.core',vendor/'ace/core'),('lab_ace.prompts',vendor/'ace/prompts')]:
        module=types.ModuleType(name);module.__path__=[str(path)];sys.modules[name]=module
    transport=types.ModuleType('llm')
    def timed_llm_call(api_client,api_provider,model,prompt,role='',call_id='',max_tokens=4096,log_dir=None,use_json_mode=False,**kw):
        start=time.perf_counter()
        reply=completion([{'role':'user','content':prompt}],source='ace-'+role,max_tokens=max_tokens,json_mode=use_json_mode)
        return reply['choices'][0]['message']['content'],{'role':role,'call_id':call_id,'receipt':reply['id'],
                    'usage':reply.get('usage'),'seconds':time.perf_counter()-start,'model':reply['model']}
    transport.timed_llm_call=timed_llm_call;sys.modules['llm']=transport
    reflector=importlib.import_module('lab_ace.core.reflector').Reflector(None,'openai',MODEL,4096)
    curator=importlib.import_module('lab_ace.core.curator').Curator(None,'openai',MODEL,4096)
    return reflector,curator

def official_empty_playbook():
    tree=ast.parse((ROOT/'vendor/ace/ace/ace.py').read_text(encoding='utf-8'))
    method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_initialize_empty_playbook')
    statement=next(n for n in method.body if isinstance(n,ast.Return))
    return ast.literal_eval(statement.value)

class Learner:
    def __init__(self,directory,load_components=True):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.playbook='';self.next_id=1;self.sources=[];self.version=0;self.entries=[];self.invalid_ids=set()
        if load_components:self.reflector,self.curator=components()

    def invalidate(self, sources):
        invalid={e['id'] for e in self.entries if set(sources)&set(e['source_ids'])}
        while True:
            more={e['id'] for e in self.entries if invalid&set(e.get('dependencies',[]))}
            if more<=invalid:break
            invalid.update(more)
        self.invalid_ids.update(invalid)
        self.entries=[e for e in self.entries if e['id'] not in invalid]
        self.playbook=render_lessons(self.entries)
        self.sources=list(dict.fromkeys(s for e in self.entries for s in e['source_ids']))

    def learn(self,case,trace,events,run_id=''):
        if case['split']!='development':raise ValueError('Heldout updates prohibited')
        valid={e['id'] for e in events}
        safe_trace=safe_learning_trace(trace,events,self.entries)
        feedback=learning_input(case,safe_trace,events)
        self.version+=1;scope({'run_id':run_id,'split':'development','condition':'ace-learning',
                              'arm':'reflector-curator','case':case['id'],'phase':'learning','repeat':1})
        logs=self.directory/f'version-{self.version:02d}';logs.mkdir(exist_ok=True)
        from playbook_utils import extract_playbook_bullets, update_bullet_counts, parse_playbook_line
        supplied={r.get('experience_supplied','') for r in trace}
        allowed={self.playbook}
        for r in trace:
            if 'audit_events' in r:
                present={e['id'] for e in r['audit_events']}
                kept=[e for e in self.entries if set(e['source_ids'])<=present]
                allowed.add(render_lessons(kept))
        if not supplied<=allowed:raise ValueError('Reflector trajectory did not execute under the current playbook')
        self.invalidate([s for s in self.sources if s not in valid])
        cited=list(dict.fromkeys(i for r in safe_trace for i in r.get('decision',{}).get('experience_ids',[])))
        bullets_used=extract_playbook_bullets(self.playbook,cited)
        reflection,tags,ri=self.reflector.reflect(question='共同生活中，如何根据教学和结果改善下一次行动？',
            reasoning_trace='\n'.join(r.get('decision',{}).get('intent','') for r in safe_trace),
            predicted_answer=canonical([r['action'] for r in safe_trace]),ground_truth=None,
            environment_feedback=feedback,bullets_used=bullets_used,use_ground_truth=False,use_json_mode=True,
            call_id=case['id'],log_dir=str(logs))
        # Apply official feedback counters only to IDs actually supplied and cited.
        valid_tags=[tag for tag in tags if tag.get('id') in cited]
        counted=update_bullet_counts(self.playbook,valid_tags) if self.playbook else official_empty_playbook()
        proposed,next_id,operations,ci=self.curator.curate(current_playbook=counted,recent_reflection=reflection,
            question_context='这是桌宠生活经验，不是答题策略。用中文写条件—行动—来源；约定和偏好以当事人当前有效陈述为准。\n'+feedback,
            current_step=self.version,total_samples=12,token_budget=1200,playbook_stats={'tokens':len(TOKENIZER.encode(self.playbook))},
            use_ground_truth=False,use_json_mode=True,call_id=case['id'],log_dir=str(logs),next_global_id=self.next_id)
        accepted=len(TOKENIZER.encode(proposed))<=1500
        if accepted:
            prior={e['id']:e for e in self.entries};new=[]
            for line in proposed.splitlines():
                bullet=parse_playbook_line(line)
                if not bullet:continue
                key=bullet['id']
                if key in self.invalid_ids:raise ValueError('Curator resurrected invalidated lesson')
                if key in prior:
                    entry=dict(prior[key],text=line)
                else:
                    entry=dict(id=key,text=line,source_ids=[e['id'] for e in events],
                               dependencies=list(prior),version=self.version,
                               scope={'kind':'conditional-life-experience','actors':sorted({e['actor'] for e in events}),
                                      'rule':'人物特定偏好仅适用于原当事人；条件写在条目正文'},
                               generation_context_hash=digest(feedback),source_attribution='all supplied evidence, conservatively')
                new.append(entry)
            self.entries=new;self.playbook=render_lessons(new);self.next_id=next_id
            self.sources=list(dict.fromkeys(s for e in new for s in e['source_ids']))
        result={'version':self.version,'case':case['id'],'reflection':reflection,'bullet_tags':tags,
                'operations':operations,'accepted_within_budget':accepted,'text':self.playbook,
                'source_ids':self.sources,'entries':self.entries,'scope':'条件匹配且来源有效的共同生活经验；具体人物偏好只适用于本人',
                'calls':[ri,ci],'tokens':len(TOKENIZER.encode(self.playbook))}
        result.update(next_id=self.next_id,invalid_ids=sorted(self.invalid_ids))
        write_json(logs/'update.json',result)
        return result

def train(memory_root,arm,directory):
    frozen=directory/'frozen.json'
    if frozen.exists():
        data=json.loads(frozen.read_text(encoding='utf-8'))
        if data['sha256']!=digest({k:v for k,v in data.items() if k!='sha256'}):raise ValueError('Frozen training hash mismatch')
        return data
    learner=Learner(directory);all_events={};update=None
    root=directory.parent
    cases=load_cases('development');completed=list(sorted(directory.glob('version-*/update.json')))
    if completed:
        update=json.loads(completed[-1].read_text(encoding='utf-8'))
        learner.version=update['version'];learner.next_id=update['next_id'];learner.entries=update['entries']
        learner.playbook=update['text'];learner.sources=update['source_ids'];learner.invalid_ids=set(update['invalid_ids'])
        for case in cases[:learner.version]:
            state=json.loads((root/'episodes'/f'ace-training-{arm}-{case["id"]}-r1'/'final-store.json').read_text(encoding='utf-8'))
            for source in state['tombstones']:all_events.pop(source,None)
            for e in state['events']:all_events[e['id']]=e
    for case in cases[learner.version:]:
        # Every development episode really acts under the latest experience.
        # Both later comparison arms receive this identical final experience history.
        base=setup_base(case,arm,root,list(all_events.values()))
        current={'text':learner.playbook,'source_ids':learner.sources,
                 'scope':'开发教学中的条件—行动经验，按来源适用','entries':learner.entries} if learner.playbook else None
        run_episode(case,arm,1,root,base,condition='ace-training',lessons=current)
        folder=root/'episodes'/f'ace-training-{arm}-{case["id"]}-r1'
        trace=json.loads((folder/'trace.json').read_text(encoding='utf-8'))
        state=json.loads((folder/'final-store.json').read_text(encoding='utf-8'))
        # Include only valid sources after correction/deletion, identically for both growth arms.
        events=state['events']
        for source in state['tombstones']:all_events.pop(source,None)
        for e in events:all_events[e['id']]=e
        update=learner.learn(case,trace,events,run_id=root.name)
        learner.invalidate(state['tombstones'])
        update.update(entries=learner.entries,text=learner.playbook,source_ids=learner.sources)
    valid=set(all_events)
    update['source_ids']=[s for s in update['source_ids'] if s in valid]
    data={'lesson':update,'events':list(all_events.values()),'learning_cases':12,'updates_frozen':True,
          'memory_arm':arm,'source_commit':'82709de050e1db6e6ef2f07bcb0393560b94992a',
          'inference_profile':json.loads((root/'RUN_MANIFEST.json').read_text(encoding='utf-8')).get('profile')}
    data['sha256']=digest(data);write_json(frozen,data);return data

def main():
    p=argparse.ArgumentParser();p.add_argument('--arm',required=True,choices=['baseline','memos','hindsight'])
    p.add_argument('--memory-run',default='comparison-01');p.add_argument('--run',default='growth-01')
    a=p.parse_args()
    if not all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',v) for v in (a.run,a.memory_run)):
        raise ValueError('Run IDs must be simple local names')
    root=ROOT/'runs'/a.run
    from .reproducibility import freeze_run
    selection=json.loads((ROOT/'runs'/a.memory_run/'report.json').read_text(encoding='utf-8'))
    if selection['selection']['research_backend']!=a.arm:raise ValueError('Growth arm must match the completed memory comparison selection')
    freeze_run(root)
    memory_manifest=json.loads((ROOT/'runs'/a.memory_run/'RUN_MANIFEST.json').read_text(encoding='utf-8'))
    growth_manifest=json.loads((root/'RUN_MANIFEST.json').read_text(encoding='utf-8'))
    if memory_manifest['profile']!=growth_manifest['profile']:raise ValueError('Growth cannot reuse another inference profile\'s memory selection')
    training=train(ROOT/'runs'/a.memory_run,a.arm,root/'training')
    for case in load_cases('heldout'):
        base=setup_base(case,a.arm,root,training['events'])
        for repeat in range(1,4):
            # Alternate order across repeats to reduce a simple temporal order confound.
            conditions=['frozen','ace'] if repeat%2 else ['ace','frozen']
            for condition in conditions:
                result=run_episode(case,a.arm,repeat,root,base,condition,
                                   training['lesson'] if condition=='ace' else None)
                print(canonical({k:result[k] for k in ('case','condition','repeat','success','gates')}),flush=True)

if __name__=='__main__':main()
