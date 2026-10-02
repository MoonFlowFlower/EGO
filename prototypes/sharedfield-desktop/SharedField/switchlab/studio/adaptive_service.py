"""One persistent controller, bounded two-stage language transactions and local work."""
from __future__ import annotations
from copy import deepcopy
import json
import uuid
from .service import Service
from .adaptive_core import AdaptiveCore
from .adaptive_protocol import SYSTEM, ANALYSE_FORMAT, EXPRESS_FORMAT, WORK_FORMAT
from .protocol import obj, parse_json

class AdaptiveService(Service):
    CoreType=AdaptiveCore
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.continue_ticket=False
        self.status='已暂停。发送消息启动一次“提案→本地选择→表达”；内部推进需明确授权。'

    def _discard_pending(self):
        if self.core.cog['pending_decision'] is not None:self._commit('discard_decision',{})
        self.continue_ticket=False

    def submit(self,content):
        with self.lock:
            # Unlike v0.2, all phases depend on a coherent observation snapshot.
            if self.busy or self.manual_request:self.generation+=1;self.manual_request=None
            self._discard_pending()
            return super().submit(content)

    def pause(self):
        with self.lock:
            super().pause()
            self._discard_pending()

    def command(self,kind,payload):
        allowed=('feedback','goal_control','lab','intervene','consolidate','adaptation',
                 'outcome','withdraw_outcome','belief_control','selection_mode','deliberate')
        if kind not in allowed:raise ValueError('unknown local command')
        with self.lock:
            if self.busy or self.manual_request:self.generation+=1;self.manual_request=None
            self._discard_pending()
            e=self._commit(kind,payload);self.error='';self.wake.set();return e

    def _build_request(self,phase,source=None,job=None):
        context=self.core.context(job['goal_id'] if job else None)
        data={'phase':phase,'context':context}
        if phase in ('analyse','express'):
            data['source_event']=source
            data['selected_input']=deepcopy(next(o for o in self.core.state['observations'] if o['id']==source))
        if phase=='express':
            d=self.core._decision(self.core.cog['pending_decision'])
            data['local_decision']={'id':d['id'],'candidate':deepcopy(d['selected']['candidate']),
                                    'prediction':deepcopy(d['selected']['prediction'])}
        elif phase=='work':data['job']=deepcopy(job)
        encoded=json.dumps(data,ensure_ascii=False,separators=(',',':'))
        if len(encoded)>80000:raise ValueError('当前上下文超过8万字符；没有静默丢弃目标约束。导出后缩小当前任务。')
        fmt={'analyse':ANALYSE_FORMAT,'express':EXPRESS_FORMAT,'work':WORK_FORMAT}[phase]
        return [{'role':'system','content':SYSTEM+'\n'+fmt},{'role':'user','content':encoded}]

    def _finish_packet(self,request,packet):
        if self.closed or request['generation']!=self.generation:raise ValueError('stale output discarded')
        phase=request['phase']
        if phase=='analyse':
            self._commit('analyse',{'source':request['source_event'],'packet':packet})
            self.continue_ticket=True
            self.status='本地控制器已选择候选；尚未执行新目标，下一阶段表达所选意图。'
        elif phase=='express':
            obj(packet,('decision_id','speech'),('decision_id','speech'))
            if packet['decision_id']!=request['decision_id']:raise ValueError('expression decision ID mismatch')
            self._commit('express',packet);self.continue_ticket=False
            if request['reflection']:self.auto_remaining=max(0,self.auto_remaining-1)
            else:self.message_tickets=max(0,self.message_tickets-1)
            self.status='所选意图已表达并保存；实际工具执行仍受有限步数授权控制。'
        else:
            obj(packet,('content',),('content',))
            self._commit('work',{'job':request['job'],'content':packet['content']})
            self.auto_remaining=max(0,self.auto_remaining-1)
            self.status='实际本地产出已保存；等待验收或继续有限计划。'
        self.error=''

    def run_once(self,force=False):
        with self.lock:
            if self.closed or self.busy or self.manual_request:return False
            if self.error and not force:return False
            source=self.core.pending_turn();reflection=False
            pending=self.core.cog['pending_decision']
            if pending:
                source=self.core._decision(pending)['source']
                reflection=not any(m['id']==source and m['role']=='user' for m in self.core.state['messages'])
            if source is None and (force or self.auto_remaining>0):
                source=self.core.pending_reflection();reflection=source is not None
            permit=source is not None and (force or self.message_tickets>0 or self.auto_remaining>0 or self.continue_ticket)
            job=self.core.next_work() if source is None and (force or self.auto_remaining>0) else None
            if not permit and job is None:
                if (force or self.auto_remaining>0) and self.core.internal_ready():
                    self._commit('deliberate',{});self.auto_remaining=max(0,self.auto_remaining-1)
                    self.status='完成一次有预算的内部计算；没有制造新观测。';return True
                if self.auto_remaining>0:self.status='休眠：没有值得执行的内部工作或在等待真实反馈。'
                return False
            phase=('express' if pending else 'analyse') if permit else 'work'
            if phase=='work' and job['step']['tool'] not in ('draft','ask'):
                try:
                    self._commit('work',{'job':job});self.auto_remaining=max(0,self.auto_remaining-1)
                    self.status='一个真实本地工具步骤已完成，其结果进入同一认知状态。'
                except (ValueError,KeyError,TypeError) as e:
                    self.error=str(e);self.auto_remaining=0;self.message_tickets=0
                return True
            try:
                if phase=='analyse' and self.provider.config.get('max_calls',48)-self.core.state['calls']<2:
                    raise ValueError('余下调用预算不足以完成提案和表达两阶段；本次未发出请求。')
                messages=self._build_request(phase,source=source,job=job)
                self._reserve_call(phase)
            except (ValueError,KeyError,TypeError) as e:
                self.error=str(e);self.auto_remaining=0;self.message_tickets=0;self.continue_ticket=False
                return False
            request={'id':uuid.uuid4().hex,'phase':phase,'generation':self.generation,
                'source_event':source,'job':job,'messages':messages,'reflection':reflection,
                'decision_id':pending}
            self.active_phase=phase
            if self.provider.config.get('mode')=='manual':
                request['prompt']='\n\n'.join(m['content'] for m in messages)
                self.manual_request=request;self.status='手动交换 · '+phase+'：请复制本阶段请求并贴回完整 JSON。'
                return True
            self.busy=True;provider=self.provider
            self.status={'analyse':'语言提出候选…','express':'表达本地选择的意图…','work':'执行本地语言工作…'}[phase]
        try:
            response=provider.complete(messages)
            with self.lock:
                if self.closed or request['generation']!=self.generation:
                    self.status='旧观测对应的迟到输出已丢弃，没有执行其提案。'
                else:
                    self._finish_packet(request,response['packet']);self.last_transport=response.get('model','unknown')
                    self._commit('usage',{'usage':response.get('usage',{}),'model':self.last_transport})
        except (ValueError,KeyError,TypeError,OSError) as e:
            with self.lock:
                self.error=str(e);self.auto_remaining=0;self.message_tickets=0;self.continue_ticket=False
                self.status='请求失败并已停止；没有假回复或自动付费重试。可修复后点“推进一步”。'
        finally:
            with self.lock:self.busy=False;self.active_phase=None
            self.wake.set()
        return True

    def accept_manual(self,request_id,raw):
        packet=parse_json(raw)
        with self.lock:
            r=self.manual_request
            if not r or r['id']!=request_id:raise ValueError('manual request expired')
            self._finish_packet(r,packet);self.manual_request=None
            self.last_transport='manual-external-model (not authenticated)';self.wake.set()

    def check_protocol(self):
        """Explicit two-call opt-in check. Uses scratch state, never trains the real life."""
        with self.lock:
            if self.closed or self.busy or self.manual_request or self.core.cog['pending_decision']:
                raise ValueError('先完成或暂停当前请求，再检查两阶段协议。')
            if self.provider.config['mode']!='api':raise ValueError('手动模式请使用正常两阶段交换。')
            if self.provider.config.get('max_calls',48)-self.core.state['calls']<2:raise ValueError('协议检查需要2次调用预算。')
            self._reserve_call('protocol_analyse');self.busy=True;generation=self.generation;provider=self.provider
        scratch=AdaptiveCore();source=scratch.apply('message',{'text':'协议检查：请比较两个本地学习计划。不要执行文件、网络或外部操作。'})['id']
        models=[]
        try:
            for phase in ('analyse','express'):
                data={'phase':phase,'source_event':source,'selected_input':scratch.state['observations'][0],
                      'context':scratch.context()}
                if phase=='express':
                    d=scratch._decision(scratch.cog['pending_decision'])
                    data['local_decision']={'id':d['id'],'candidate':d['selected']['candidate'],'prediction':d['selected']['prediction']}
                    with self.lock:
                        if self.closed or generation!=self.generation:raise ValueError('protocol check cancelled')
                        self._reserve_call('protocol_express')
                response=provider.complete([{'role':'system','content':SYSTEM+'\n'+(ANALYSE_FORMAT if phase=='analyse' else EXPRESS_FORMAT)},
                    {'role':'user','content':json.dumps(data,ensure_ascii=False,separators=(',',':'))}])
                with self.lock:
                    if self.closed or generation!=self.generation:raise ValueError('protocol check cancelled; no result accepted')
                    self._commit('usage',{'usage':response.get('usage',{}),'model':response.get('model','unknown')})
                models.append(response.get('model','unknown'))
                if phase=='analyse':scratch.apply('analyse',{'source':source,'packet':response['packet']})
                else:scratch.apply('express',response['packet'])
            return {'ok':True,'stages':2,'models':models,'main_life_trained':False,
                    'proposed_goals':len(scratch.state['goals']),'tools_executed':0,
                    'scope':'two-stage transport/schema/local-arbitration check only; semantic quality unmeasured'}
        finally:
            with self.lock:self.busy=False
            self.wake.set()
