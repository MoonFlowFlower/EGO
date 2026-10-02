"""Reading jobs share the real worker, cancellation generation and call budget."""
from copy import deepcopy
import hashlib
import json
import sqlite3
import uuid
from . import reading


class ReadingMixin:
    def reading_view(self):
        with self.lock:
            state=reading.view(self.store)
            state['running']=getattr(self,'reading_enabled',False)
            return state

    def reading_command(self,data):
        with self.lock:
            op=data.get('op')
            if op not in ('material','start','feedback','adopt','withdraw','compare','score','cancel','resume'):
                raise ValueError('阅读成果只能由当前模型请求提交，不能通过操作入口伪造')
            if op=='resume':
                if set(data)!={'op'}:raise ValueError('resume没有附加字段')
                if self.busy:raise ValueError('请等当前请求结束')
                self.reading_enabled=True;self.error='';self.wake.set();return {'resumed':True}
            if (self.busy or self.pending) and op!='cancel':raise ValueError('正在处理对话或阅读，请先暂停或等当前请求结束')
            result=self._commit('reading',data)['result']
            self.generation+=1;self.manual_request=None;self.error=''
            if op in ('start','feedback','compare'):self.reading_enabled=True
            elif op=='cancel':self.reading_enabled=False
            self.status='阅读进展已保存。';self.wake.set();return result

    def _reading_finish(self,request,packet,model,usage):
        if self.closed or request['generation']!=self.generation:raise ValueError('阅读状态已改变，拒绝迟到结果')
        self._commit('reading',{'op':'result','job_id':request['job_id'],'packet':packet,
            'receipt':{'model':model,'transport':request['transport'],'input_bytes':request['input_bytes'],
                       'input_sha256':request['input_sha256'],'usage':usage,'provider_signature':request.get('provider_signature')}})
        self.status='阅读成果已保存，可以一起讨论或纠正。';self.error=''

    def reading_run_once(self):
        with self.lock:
            if not getattr(self,'reading_enabled',False):return None
            if self.closed or self.busy or self.manual_request or self.error or self.pending:return None
            job=reading.next_job(self.store)
            if not job:self.reading_enabled=False;return None
            mode=self.options['language_mode']
            if mode=='local':
                self.error='阅读需要连接真实模型，或选择手动模型交换；材料已保存，没有生成替代成果。'
                self.reading_enabled=False;return False
            try:
                messages=reading.build_request(self.store,job)
                wire=json.dumps(messages,ensure_ascii=False,sort_keys=True).encode('utf-8')
                if mode=='api':
                    if self.provider.config['mode']!='api':raise ValueError('请先配置已有模型服务')
                    self._reserve_call('reading_'+job['phase'])
                request={'id':uuid.uuid4().hex,'phase':'reading','job_id':job['id'],'generation':self.generation,
                         'messages':messages,'input_bytes':len(wire),'input_sha256':hashlib.sha256(wire).hexdigest(),
                         'transport':'api' if mode=='api' else 'manual-external'}
                if mode=='api':
                    identity={k:self.provider.config.get(k) for k in ('base_url','model','max_output_tokens','json_mode','token_parameter')}
                    request['provider_signature']=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
                if mode=='manual':
                    request['prompt']='\n\n'.join(m['content'] for m in messages);self.manual_request=request
                    self.status='等待这次阅读的真实模型回复。';return True
                provider=self.provider;self.busy=True;self.active_phase='reading'
            except (ValueError,TypeError,KeyError,sqlite3.Error) as e:
                self.error=str(e);self.reading_enabled=False;return False
        try:
            response=provider.complete(messages)
            with self.lock:
                if not self.closed:
                    self._commit('usage',{'usage':response.get('usage',{}),'model':response.get('model','unknown')})
                    if request['generation']==self.generation:
                        self._reading_finish(request,response['packet'],response.get('model','unknown'),response.get('usage',{}))
                    else:self.status='阅读已暂停或状态已改变，迟到结果未提交；请求可能计费。'
        except (ValueError,TypeError,KeyError,OSError,sqlite3.Error) as e:
            with self.lock:
                if not self.closed and request['generation']==self.generation:
                    self.error=str(e);self.reading_enabled=False;self.status='阅读停止，原文与已有成果保留。不会自动重试收费请求。'
        finally:
            with self.lock:self.busy=False;self.active_phase=None
            self.wake.set()
        return True
