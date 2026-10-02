"""Bounded persistent run loop. User messages are not the only clock.

Inherits proven storage/locking/provider boundaries from Studio. External action
is confined to the built-in environment. Local computation never requires an API.
"""
from __future__ import annotations
from copy import deepcopy
import json,time,uuid
from ..studio.service import Service
from ..studio.protocol import obj,text,parse_json
from ..runtime import load_json,save_json
from .core import SharedCore
from .protocol import SYSTEM,INTERPRET,EXPRESS

OPTIONS={'language_mode':'local','narrate':False,'interval':1.4}

class SharedService(Service):
    CoreType=SharedCore
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        try:
            self.options=deepcopy(OPTIONS)
            p=self.directory/'shared_options.json'
            if p.exists():self.options.update(self._options(load_json(p)))
        except Exception:self.file_lock.close();raise
        self.next_action_at=0.;self.narration_ticket=False;self.last_narration_tick=-10
        self.status='已暂停；可一起探索，也可直接询问感觉、想法与意愿。默认本地状态报告，不调用模型。'

    @staticmethod
    def _options(p):
        obj(p,OPTIONS.keys())
        if 'language_mode' in p and p['language_mode'] not in ('local','manual','api'):raise ValueError('language_mode must be local/manual/api')
        if 'narrate' in p and type(p['narrate']) is not bool:raise ValueError('narrate must be boolean')
        if 'interval' in p and (type(p['interval']) not in (int,float) or not .2<=p['interval']<=10):raise ValueError('interval must be .2..10 seconds')
        return p

    def set_options(self,p):
        self._options(p)
        with self.lock:
            if self.busy:raise ValueError('请先暂停并等待正在返回的模型请求结束。')
            proposed={**self.options,**p};save_json(self.directory/'shared_options.json',proposed)
            self.pause();self.options=proposed;self.error='';return deepcopy(self.options)

    def submit(self,content):
        with self.lock:
            self.generation+=1;self.manual_request=None;self.narration_ticket=False
            result=self._commit('message',{'text':text(content,'message',6000)})
            self.message_tickets=1;self.error='';self.wake.set();return result

    def pause(self):
        with self.lock:
            super().pause();self.narration_ticket=False
            if self.core.state['pending']:self._commit('discard',{})

    def start_auto(self,count=6):
        if type(count) is not int or not 1<=count<=600:raise ValueError('每次授权1..600个内置动作；仅共享环境')
        with self.lock:
            self.auto_remaining=count;self.error='';self.wake.set()
            self.next_action_at=0.;self.status='已授权有限内置环境行动；每步使用当前模型与目标。不会控制真实电脑。'

    def command(self,kind,payload):
        allowed=('player_action','reflect','invite','intervene','ablation','new_expedition','withdraw_report','name','activity')
        if kind not in allowed:raise ValueError('not an authorized shared-environment command')
        with self.lock:
            # A player action is new evidence, not withdrawal of their question.
            # Keep in-flight language pinned; explicitly label older snapshots.
            if kind not in ('player_action','activity','invite'):
                if self.busy or self.manual_request or self.core.state['pending']:self.message_tickets=0
                self.generation+=1;self.manual_request=None;self.narration_ticket=False
            if kind=='new_expedition':self.auto_remaining=0;self.message_tickets=0
            result=self._commit(kind,payload);self.error='';self.wake.set();return result

    def _build(self,phase,source=None):
        data={'phase':phase,'context':self.core.context(expression=phase=='express')}
        if phase=='interpret':data.update(source_event=source,selected_input=self.core._source(source))
        else:
            p=self.core.state['pending'];data.update(state_id=p['state_id'],narration=p['narration'])
            if not p['narration']:data['selected_input']=self.core._source(p['source'])
        encoded=json.dumps(data,ensure_ascii=False,separators=(',',':'))
        if len(encoded)>80000:raise ValueError('上下文超过8万字符，停止请求；请导出检查而不是静默截断关键来源。')
        return [{'role':'system','content':SYSTEM+'\n'+(INTERPRET if phase=='interpret' else EXPRESS)},
                {'role':'user','content':encoded}]

    def _finish(self,r,packet):
        if self.closed or r['generation']!=self.generation:raise ValueError('stale language output')
        if r['phase']=='interpret':
            event=self._commit('interpret',{'source':r['source'],'packet':packet})
            if event['result']['request']=='pause':
                self.auto_remaining=0;self.step_ticket=False
            self.status='来源解释已记录；以实际内部状态组织回答。'
        else:
            obj(packet,('state_id','speech','decision_id'),('state_id','speech'))
            if packet['state_id']!=r['state_id']:raise ValueError('returned state_id does not match this request')
            self._commit('expression',packet)
            if r['narration']:self.narration_ticket=False
            else:self.message_tickets=0
            self.status='回答对应一个可查看的真实状态快照；可以继续共同探索。'
        self.error=''

    def run_once(self,force=False):
        with self.lock:
            if self.closed or self.busy or self.manual_request:return False
            if self.error and not force:return False
            source=self.core.pending_turn();pending=self.core.state['pending'];phase=None
            permit=(source is not None and (force or self.message_tickets>0)) or (pending and self.narration_ticket)
            if permit:
                if self.options['language_mode']=='local':
                    self._commit('local_reply',{});self.message_tickets=0;self.status='已呈现实际状态；自然对话需连接语言模型。';return True
                phase='express' if pending else 'interpret'
            elif force or self.auto_remaining>0:
                last=self.core.state['last_result'] or {}
                if (not force and last.get('kind')=='waiting_for_partner'
                    and last.get('world_tick')==self.core.world.tick
                    and last.get('activity_source')==self.core.mind.activity['source']):return False
                if not force and time.monotonic()<self.next_action_at:return False
                if self.core.world.tick>=self.core.world.horizon:
                    self.auto_remaining=0;self.status='本次探索步数用完，可保留经历开始新探索。';return False
                event=self._commit('agent_step',{})
                if event['result']['kind']=='waiting_for_partner':
                    self.status=event['result']['reason'];return True
                if event['result']['kind']=='sleep':
                    self.auto_remaining=0;self.status='没有未完成的探索机会，进入休息；不因空闲而捏造目标。';return True
                self.auto_remaining=max(0,self.auto_remaining-1);self.next_action_at=time.monotonic()+self.options['interval']
                self.status='已执行真实内置动作；预测、评价状态、学习和下一步选择已经更新。'
                transition=event['result']['transition'];salient=transition.get('finding',{}).get('new') or not transition['success']
                if (salient and self.options['narrate'] and self.options['language_mode']!='local'
                        and self.core.world.tick-self.last_narration_tick>=4):
                    self._commit('prepare_narration',{});self.narration_ticket=True;self.last_narration_tick=self.core.world.tick
                return True
            else:return False
            try:
                if self.options['language_mode']=='api' and self.provider.config['mode']!='api':raise ValueError('先在模型连接中保存一个API端点，再启用API语言。')
                required=2 if phase=='interpret' else 1
                if self.options['language_mode']=='api' and self.provider.config.get('max_calls',48)-self.core.state['calls']<required:
                    raise ValueError('剩余请求预算不足；本次未发出请求。')
                messages=self._build(phase,source)
                if self.options['language_mode']=='api':self._reserve_call('shared_'+phase)
            except (ValueError,TypeError,KeyError) as e:
                self.error=str(e);self.auto_remaining=0;self.message_tickets=0;self.narration_ticket=False;return False
            pending=self.core.state['pending']
            r={'id':uuid.uuid4().hex,'phase':phase,'generation':self.generation,'source':source,'messages':messages,
               'state_id':pending['state_id'] if pending else None,'narration':bool(pending and pending['narration'])}
            if self.options['language_mode']=='manual':
                r['prompt']='\n\n'.join(m['content'] for m in messages);self.manual_request=r
                self.status='手动语言交换 · '+phase+'；世界等待这次输入，不调用远程API。';return True
            self.busy=True;self.active_phase=phase;provider=self.provider
            self.status='理解有来源的输入…' if phase=='interpret' else '依据已存在的状态自然表达…'
        try:
            response=provider.complete(messages)
            with self.lock:
                if not self.closed:
                    self._commit('usage',{'usage':response.get('usage',{}),'model':response.get('model','unknown')})
                    if r['generation']==self.generation:
                        self._finish(r,response['packet']);self.last_transport=response.get('model','unknown')
                    else:self.status='状态已经变化，迟到语言输出未提交；请求可能已计费。'
        except (ValueError,TypeError,KeyError,OSError) as e:
            with self.lock:
                if not self.closed and r['generation']==self.generation:
                    self.error=str(e);self.auto_remaining=0;self.message_tickets=0;self.narration_ticket=False
                    self.status='语言请求失败并停止；没有自动收费重试，也不伪造模型回答。'
        finally:
            with self.lock:self.busy=False;self.active_phase=None
            self.wake.set()
        return True

    def accept_manual(self,request_id,raw):
        packet=parse_json(raw)
        with self.lock:
            r=self.manual_request
            if not r or r['id']!=request_id:raise ValueError('manual request expired')
            self._finish(r,packet);self.manual_request=None;self.last_transport='manual-external-not-authenticated';self.wake.set()

    def check_protocol(self):
        # Use explicit scratch message lifecycle via the same protocol, without
        # adding imagined evidence to the current life. Counts real API calls.
        with self.lock:
            if self.busy or self.manual_request:raise ValueError('先完成或暂停当前语言请求。')
            if self.provider.config['mode']!='api':raise ValueError('需要已配置的API端点。')
            if self.provider.config.get('max_calls',48)-self.core.state['calls']<2:raise ValueError('协议检查需要2次请求预算。')
            self._reserve_call('shared_protocol_interpret');self.busy=True;gen=self.generation;p=self.provider
        scratch=SharedCore();source=scratch.apply('message',{'text':'协议检查：你现在在想什么？'})['id']
        try:
            for phase in ('interpret','express'):
                data={'phase':phase,'context':scratch.context(expression=phase=='express'),'source_event':source,'selected_input':scratch._source(source)}
                if phase=='express':
                    data.update(state_id=scratch.state['pending']['state_id'],narration=False)
                    with self.lock:
                        if self.closed or gen!=self.generation:raise ValueError('protocol check cancelled')
                        self._reserve_call('shared_protocol_express')
                response=p.complete([{'role':'system','content':SYSTEM+'\n'+(INTERPRET if phase=='interpret' else EXPRESS)},
                    {'role':'user','content':json.dumps(data,ensure_ascii=False)}])
                with self.lock:
                    if self.closed or gen!=self.generation:raise ValueError('protocol result discarded')
                    self._commit('usage',{'usage':response.get('usage',{}),'model':response.get('model','unknown')})
                if phase=='interpret':scratch.apply('interpret',{'source':source,'packet':response['packet']})
                else:scratch.apply('expression',response['packet'])
            return {'ok':True,'calls':2,'main_life_learned':False,'scope':'transport/schema; actual semantic quality not measured'}
        finally:
            with self.lock:self.busy=False
            self.wake.set()

    def import_checkpoint(self,data,archive_current=False):
        if not isinstance(data,dict):raise ValueError('checkpoint must be a JSON object')
        if type(archive_current) is not bool:raise ValueError('archive confirmation must be boolean')
        with self.lock:
            if self.busy or self.manual_request:raise ValueError('先暂停并等待当前模型请求结束，再导入。')
            if self.core.events and not archive_current:raise ValueError('当前已有经历；请选择新目录或明确允许先归档。')
            candidate=SharedCore.from_v04(data) if data.get('schema')=='switchlab.shared.v4' else SharedCore.restore(data)
            # Verify before replacing anything. Archive and save use atomic writes.
            if self.core.events:
                archive=self.directory/'archive'/('before_import_'+uuid.uuid4().hex+'.json')
                save_json(archive,self.core.checkpoint())
            self.pause()
            save_json(self.session_path,candidate.checkpoint())
            self.core=candidate;self.generation+=1;self.auto_remaining=0;self.message_tickets=0
            self.manual_request=None;self.narration_ticket=False;self.error=''
            self.status='旧经历与地图已导入，当前暂停。未完成的远端请求不会自动重发。'
            return {'ok':True,'world_tick':candidate.world.tick,'origin_version':data['metadata']['version'],
                    'events_preserved':len(data['events']),'paused':True,
                    'numeric_normalization_disclosed':data.get('schema')=='switchlab.shared.v4'}

    def view(self):
        v=super().view();v['runtime']['options']=deepcopy(self.options);return v
