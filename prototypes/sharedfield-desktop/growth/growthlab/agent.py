"""Shared decision/execution loop. Only allowed observations cross into memory."""
import json
import time
from collections import Counter
from pathlib import Path
from .host import Host
from .contract import validate, ACTIONS
from .changes import changes, repeat_action
from .state import Store
from .skills import SkillLibrary
from .sandbox import run
from .decision import messages, decode, decision_format, assess_front, recent_view, VERSION
from .records import write_json, digest


class Episode:
    def __init__(self, host, store, folder, client, *, arm='B', goal='做出木镐 (wood_pickaxe)', memory=None, teaching=None,
                 observation_format=None, stop_on_success=True):
        self.host,self.store,self.client = host,store,client
        self.folder=Path(folder); self.folder.mkdir(parents=True,exist_ok=True)
        self.arm,self.goal,self.memory,self.teaching = arm,goal,memory,teaching
        self.observation_format,self.stop_on_success=observation_format,stop_on_success
        self.library=SkillLibrary(store,host.world,host.actions)
        self.trace=(self.folder/'trace.jsonl').open('a',encoding='utf-8')
        self.recent=[];self.events=[];self.calls=[];self.experiences=[];self.skill_results=[]
        self.counts=Counter();self.failures=0;self.predicted=0;self.eligible=0;self.match_count=0;self.prediction_count=0
        self.first_success=None;self.started=time.perf_counter();self.stop=None
        self.write({'type':'start','prompt_version':VERSION,'world':host.world,'arm':arm})
        if teaching:self.experience({'type':'teaching','text':teaching},'taught')

    def write(self,data):
        self.trace.write(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n');self.trace.flush()

    def experience(self,body,source='experienced'):
        identity=self.store.put('experience',body,source,world=self.host.world)
        self.experiences.append(identity);return identity

    def step(self,action):
        before=validate(self.host.observe())
        rules=self.memory.rules if self.memory is not None and self.arm=='B' else None
        predictions=rules.predict(before,action) if rules else []
        # Log program predictions BEFORE execution, independently of the model.
        self.write({'type':'prediction','tick':before['tick'],'action':action,'predictions':predictions})
        after=self.host.act(action);event=changes(before,after,action)
        identity=self.experience({'type':'transition','before':before,'after':after,'action':action,'change':event})
        scores=rules.score(before,after,action,identity) if rules else []
        self.events.append(event);self.counts.update(event['events'])
        canonical=ACTIONS[self.host.action_indices[action]]  # evaluator only, never serialized to model
        crafting=canonical.startswith(('make_','place_'))
        if crafting and 'no_visible_effect' in event['events']:self.failures+=1
        if crafting or action=='do':
            self.eligible+=1
            if predictions:self.predicted+=1
            self.prediction_count+=len(scores);self.match_count+=sum(x['match'] for x in scores)
        if after['inventory'].get('wood_pickaxe',0)>0 and self.first_success is None:self.first_success=after['tick']
        self.write({'type':'step','experience':identity,'before':before,'observation':after,'change':event,'prediction_scores':scores})
        return after

    def execute(self,choice,observation_experience):
        if choice['kind']=='action':
            result=repeat_action(choice['action'],choice['repeat'],self.host.observe,self.step)
        elif choice['kind']=='goto':
            from .navigation import goto
            result=goto(choice['name'],self.host.observe,self.step,max_steps=32)
        else:
            starting_observation=self.host.observe()
            if choice['kind']=='write':
                self.library.register(choice['name'],choice['description'],choice['source'],choice['completion'],parents=[observation_experience])
            if choice['name'] not in self.library.current():raise ValueError('unknown_skill')
            result=run('',self.host.observe,self.step,library=self.library,name=choice['name'],max_steps=32,timeout_s=5)
            identity=self.experience({'type':'skill_result','result':result,'taught':bool(self.teaching),'takeover':False,
                'context':{'goal':self.goal,'inventory':starting_observation['inventory'],
                    'public_actions':starting_observation['actions'],'restarted':getattr(self.memory,'restarted',False)}})
            self.skill_results.append(result)
        self.write({'type':'execution','result':result})
        return result

    def play(self,max_decisions=None,deadline=None):
        consecutive_invalid=0
        max_decisions=max_decisions or self.host.env._length*2
        try:
            while not self.host.done and (self.first_success is None or not self.stop_on_success):
                if deadline is not None and time.time()>=deadline:self.stop='wall_clock_stop';break
                if len(self.calls)>=max_decisions:self.stop='decision_limit';break
                obs=validate(self.host.observe())
                obs_id=self.experience({'type':'observation','observation':obs})
                memory=self.memory.retrieve(obs,self.goal) if self.memory else []
                if self.memory and self.arm=='B':
                    self.write({'type':'rule_applications','tick':obs['tick'],'applications':self.memory.rules.applied(obs)})
                prompt=messages(obs,self.goal,memory,self.recent,self.events,self.teaching,observation_format=self.observation_format)
                self.write({'type':'input','messages':prompt,'input_digest':digest(prompt)})
                content,meta=self.client.decide(prompt,response_format=decision_format(obs['actions']),max_tokens=2048)
                self.calls.append(meta);self.write({'type':'call','meta':meta})
                self.write({'type':'front_assessment','tick':obs['tick'],'output':content,**assess_front(content,obs)})
                try:
                    choice=decode(content,obs['actions'])
                    # Persist basis before any action or generated program runs.
                    self.write({'type':'decision','tick':obs['tick'],'choice':choice})
                    result=self.execute(choice,obs_id)
                except (ValueError,KeyError,TypeError):
                    consecutive_invalid+=1
                    self.write({'type':'rejected','code':'invalid_decision_or_skill','output':content})
                    self.recent.append({'boundary_error':'invalid_decision_or_skill'})
                    if consecutive_invalid>=2:self.stop='two_consecutive_invalid_outputs';break
                    continue
                consecutive_invalid=0
                self.recent.extend(recent_view([{'decision':choice,'execution_status':result['status'],'steps':result['steps']}]))
                self.write({'type':'progress','decisions':len(self.calls),'steps':self.host.observe()['tick']})
        except (RuntimeError,ValueError) as error:
            allowed=('http_429','http_404','http_403','http_401','http_402','http_502','http_503','http_504','budget_stop','prompt_size_stop','TimeoutError','URLError','ac_required','machine_time_limit')
            self.stop=str(error) if str(error) in allowed else type(error).__name__
            self.write({'type':'stop','code':self.stop})
        return self.summary()

    def summary(self):
        return {'arm':self.arm,'prompt_version':VERSION,'steps':self.host.observe()['tick'],
                'success':self.first_success is not None,'achievement_steps':self.first_success,
                'capped_steps':self.first_success if self.first_success is not None else self.host.env._length,
                'step_limit':self.host.env._length,'censored':self.first_success is None,
                'failure_attempts':self.failures,'decisions':sum(c.get('purpose')!='consolidation' for c in self.calls),
                'cloud_calls':len(self.calls),
                'reported_cost_usd':sum(c.get('cost_usd') or 0 for c in self.calls),
                'missing_receipts':sum(c.get('cost_usd') is None for c in self.calls),
                'seconds':time.perf_counter()-self.started,'stop':self.stop,
                'events':dict(self.counts),'prediction_eligible_actions':self.eligible,
                'predicted_actions':self.predicted,'prediction_coverage':self.predicted/self.eligible if self.eligible else None,
                'prediction_count':self.prediction_count,'prediction_matches':self.match_count,
                'prediction_accuracy':self.match_count/self.prediction_count if self.prediction_count else None,
                'calls':self.calls,'skill_executions':self.skill_results,
                'claim_ceiling':'descriptive pilot only; not E1; no learning or superiority claim'}

    def close(self):self.trace.close()
