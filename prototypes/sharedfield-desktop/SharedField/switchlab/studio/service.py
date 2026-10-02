"""Bounded work scheduler and durable local state. Network runs outside the core lock."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import json
import os
import threading
import uuid
from switchlab.runtime import load_json, save_json
from .core import Core
from .provider import Provider, DEFAULT
from .protocol import SYSTEM, TURN_FORMAT, WORK_FORMAT, parse_json, text, obj


class DirectoryLock:
    def __init__(self, directory):
        self.file = open(Path(directory)/'studio.lock','a+b')
        self.file.seek(0);self.file.write(b'0');self.file.flush();self.file.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.file.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except (OSError,IOError):
            self.file.close();raise ValueError('this data directory is already open in another Studio process') from None
    def close(self):
        if self.file.closed:return
        try:
            self.file.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.file.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(),fcntl.LOCK_UN)
        finally:self.file.close()


class Service:
    CoreType = Core
    def __init__(self, directory, provider=None, seed=41, horizon=240):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.file_lock=DirectoryLock(self.directory)
        self.lock=threading.RLock();self.wake=threading.Event();self.stop_event=threading.Event()
        self.thread=None;self.busy=False;self.closed=False;self.generation=0
        self.auto_remaining=0;self.message_tickets=0;self.manual_request=None;self.step_ticket=False
        self.error='';self.status='已暂停；发送消息只处理对话，不自动恢复后台任务。';self.last_transport='none'
        self.session_path=self.directory/'session.json'
        try:
            self.core=self.CoreType.restore(load_json(self.session_path)) if self.session_path.exists() else self.CoreType(seed,horizon)
            config=load_json(self.directory/'provider.json') if (self.directory/'provider.json').exists() else None
            self.provider=provider or Provider(config)
            # No ambient API credentials; never silently reuse a key with a new endpoint.
        except Exception:
            self.file_lock.close();raise

    def _commit(self, kind, data):
        before=self.core.checkpoint()
        result=self.core.apply(kind,data)
        try:save_json(self.session_path,self.core.checkpoint())
        except OSError as e:
            self.core=self.CoreType.restore(before)
            self.auto_remaining=0;self.message_tickets=0;self.generation+=1
            self.error='本地保存失败，已停止推进；请检查磁盘或目录权限。'
            raise ValueError(self.error) from e
        return result

    def start_worker(self):
        if self.thread is not None:return
        self.thread=threading.Thread(target=self._loop,daemon=True,name='StudioBoundedWorker');self.thread.start()

    def _loop(self):
        while not self.stop_event.is_set():
            with self.lock:
                force=self.step_ticket;self.step_ticket=False
            try:did=self.run_once(force=force)
            except Exception:
                # Avoid spilling prompts, credentials or arbitrary provider errors into logs.
                with self.lock:
                    self.error='运行时发生异常，已停止。请导出本地轨迹检查。'
                    self.auto_remaining=0;self.message_tickets=0
                did=False
            if not did:
                self.wake.wait(.25);self.wake.clear()

    def submit(self, content):
        with self.lock:
            pending=sum(m['role']=='user' and m['id'] not in self.core.state['handled'] for m in self.core.state['messages'])
            if pending>=8:raise ValueError('已有8条未处理消息；请先处理或暂停后检查。')
            event=self._commit('message',{'text':text(content,'message',6000)})
            # New constraints invalidate a not-yet-committed background draft.
            if self.manual_request and self.manual_request['phase']=='work':
                self.generation+=1;self.manual_request=None
            elif self.busy and getattr(self,'active_phase',None)=='work':self.generation+=1
            self.message_tickets+=1;self.error='';self.wake.set()
            return event

    def request_step(self):
        with self.lock:
            if self.busy:raise ValueError('当前请求尚未结束；可以暂停，但不能并发推进。')
            if self.manual_request:raise ValueError('先完成或暂停当前手动交换。')
            self.step_ticket=True;self.error='';self.wake.set()

    def new_life(self):
        with self.lock:
            self.pause()
            if self.busy:raise ValueError('请等待已发请求结束，再开启新实验。')
            old=self.core
            archive=self.directory/'archive'/('life_'+uuid.uuid4().hex+'.json')
            save_json(archive,old.checkpoint())
            fresh=self.CoreType()
            save_json(self.session_path,fresh.checkpoint())
            self.core=fresh;self.error='';self.step_ticket=False
            self.status='新实验已建立；上一轮完整状态已归档，未删除。'

    def start_auto(self, count=6):
        if type(count) is not int or not 1<=count<=20:raise ValueError('每次自动推进限1..20步')
        with self.lock:
            self.auto_remaining=count;self.error=''
            self.message_tickets=sum(m['role']=='user' and m['id'] not in self.core.state['handled'] for m in self.core.state['messages'])
            self.status='允许有限推进；没有可执行目标时休眠。';self.wake.set()

    def pause(self):
        with self.lock:
            self.auto_remaining=0;self.message_tickets=0;self.manual_request=None;self.step_ticket=False;self.generation+=1
            self.status='已暂停。已发出的网络请求可能仍被计费，但其迟到结果不会再提交。';self.wake.set()

    def configure(self, config, key=None, clear_key=False):
        with self.lock:
            if self.busy:raise ValueError('有请求正在返回，请先暂停并等该请求结束再修改连接。')
            old=self.provider
            same=config.get('base_url',DEFAULT['base_url']).rstrip('/')==old.config.get('base_url','').rstrip('/')
            secret='' if clear_key or not same else getattr(old,'key','')
            if key is not None and key!='':secret=text(key,'API key',4096)
            new=Provider(config,secret)
            save_json(self.directory/'provider.json',new.config)
            self.provider=new;self.manual_request=None;self.generation+=1;self.error=''
            self.status='连接设置已保存；密钥仅保留在当前进程内。'
            return new.public()

    def command(self, kind, payload):
        if kind not in ('feedback','goal_control','lab','intervene','consolidate','adaptation'):
            raise ValueError('unknown local command')
        with self.lock:
            if kind in ('feedback','goal_control','lab','intervene','consolidate','adaptation') and self.busy:
                # All model requests get a coherent snapshot; new observations invalidate old snapshots.
                self.generation+=1
            if self.manual_request:
                self.generation+=1;self.manual_request=None
            e=self._commit(kind,payload);self.error='';self.wake.set();return e

    def _build_request(self, phase, source=None, job=None):
        context=self.core.context(job['goal_id'] if job else None)
        data={'phase':phase,'context':context}
        if source:
            data['source_event']=source
            observation=next(o for o in self.core.state['observations'] if o['id']==source)
            data['selected_input']=deepcopy(observation)
        else:data['job']=deepcopy(job)
        # If the raw context overflows, do NOT silently cut mid-JSON or silently drop constraints.
        encoded=json.dumps(data,ensure_ascii=False,separators=(',',':'))
        if len(encoded)>80000:raise ValueError('上下文超过本版8万字符上限；请缩小当前任务或导出并开始新实验。')
        return [{'role':'system','content':SYSTEM+'\n'+(TURN_FORMAT if phase=='turn' else WORK_FORMAT)},
                {'role':'user','content':encoded}]

    def _reserve_call(self, phase):
        if self.core.state['calls']>=self.provider.config.get('max_calls',48):
            raise ValueError('本生命周期模型请求预算已用完；在设置中明确提高上限后才会继续。')
        self._commit('call',{'phase':phase,'model':self.provider.config.get('model') or 'manual-external-model'})

    def _finish_packet(self, request, packet):
        if request['generation']!=self.generation:raise ValueError('stale request discarded after pause or new observation')
        if request['phase']=='turn':
            self._commit('turn',{'source':request['source_event'],'packet':packet})
            if request.get('reflection'):self.auto_remaining=max(0,self.auto_remaining-1)
            else:self.message_tickets=max(0,self.message_tickets-1)
        else:
            obj(packet,('content',),('content',))
            self._commit('work',{'job':request['job'],'content':packet['content']})
            self.auto_remaining=max(0,self.auto_remaining-1)
        self.error='';self.status='本轮已提交；没有可执行工作时休眠。'

    def run_once(self, force=False):
        with self.lock:
            if self.closed or self.busy or self.manual_request is not None:return False
            if self.error and not force:return False
            source=self.core.pending_turn();reflection=False
            if source is None and (force or self.auto_remaining>0):
                source=self.core.pending_reflection();reflection=source is not None
            permit_turn=source is not None and (force or self.message_tickets>0 or self.auto_remaining>0)
            job=self.core.next_work() if source is None and (force or self.auto_remaining>0) else None
            if not permit_turn and job is None:
                if self.auto_remaining>0:self.status='休眠：没有可执行目标。等待真实输入、反馈或新观测。'
                return False
            self.error='';phase='turn' if permit_turn else 'work'
            if phase=='work' and job['step']['tool'] not in ('draft','ask'):
                try:
                    self._commit('work',{'job':job});self.auto_remaining=max(0,self.auto_remaining-1)
                    self.status='已执行一个本地工具步骤；反馈进入后续上下文。'
                except (ValueError,TypeError,KeyError) as e:
                    self.error=str(e);self.auto_remaining=0;self.message_tickets=0
                return True
            try:
                messages=self._build_request(phase,source=source if permit_turn else None,job=job)
                self._reserve_call(phase)
            except (ValueError,TypeError,KeyError) as e:
                self.error=str(e);self.auto_remaining=0;self.message_tickets=0;return False
            request={'id':uuid.uuid4().hex,'phase':phase,'generation':self.generation,
                     'source_event':source if permit_turn else None,'job':job,'messages':messages,'reflection':reflection}
            self.active_phase=phase
            if self.provider.config.get('mode')=='manual':
                request['prompt']='\n\n'.join(m['content'] for m in messages)
                self.manual_request=request;self.status='等待手动语言交换：复制请求到你选择的模型，再粘贴完整 JSON。'
                return True
            provider=self.provider;self.busy=True;self.status='语言模块处理中；暂停按钮仍然可用。'
        try:
            response=provider.complete(messages)
            with self.lock:
                if request['generation']!=self.generation:
                    self.status='暂停或新观测前的迟到输出已丢弃；没有执行其提案。'
                else:
                    self._finish_packet(request,response['packet'])
                    self.last_transport=response.get('model','unknown')
                    # Usage is reported by the provider; it is not an independently measured bill.
                    self._commit('usage',{'usage':response.get('usage',{}),'model':self.last_transport})
        except (ValueError,TypeError,KeyError,OSError) as e:
            with self.lock:
                self.error=str(e);self.auto_remaining=0;self.message_tickets=0
                self.status='请求失败：未生成假回复、未自动付费重试。'
        finally:
            with self.lock:self.busy=False;self.active_phase=None
            self.wake.set()
        return True

    def accept_manual(self, request_id, raw):
        packet=parse_json(raw)
        with self.lock:
            r=self.manual_request
            if r is None or r['id']!=request_id:raise ValueError('manual request expired or already applied')
            self._finish_packet(r,packet)
            self.manual_request=None;self.last_transport='manual-external-model (not authenticated)';self.wake.set()

    def check_connection(self):
        with self.lock:
            if self.busy or self.manual_request:raise ValueError('finish or pause current request first')
            if self.provider.config['mode']!='api':raise ValueError('手动模式没有远程连接；直接使用请求交换。')
            self._reserve_call('connection_check');self.busy=True;provider=self.provider;generation=self.generation
        try:
            result=provider.complete([{'role':'system','content':'Return one JSON object only.'},
                                      {'role':'user','content':'Return {"speech":"connection ok"} as JSON.'}])
            with self.lock:
                if self.closed or generation!=self.generation:
                    raise ValueError('connection result discarded after close, pause or new observation')
                self._commit('usage',{'usage':result.get('usage',{}),'model':result.get('model','unknown')})
                self.last_transport=result.get('model','unknown')
            return {'ok':True,'model':result.get('model'),'scope':'HTTP and JSON response only, not mechanism evaluation'}
        finally:
            with self.lock:self.busy=False

    def view(self):
        with self.lock:
            v=self.core.view()
            v['runtime']={'busy':self.busy,'auto_remaining':self.auto_remaining,'error':self.error,
                          'status':self.status,'pending_turn':self.core.pending_turn(),
                          'manual_request':deepcopy(self.manual_request),'last_model':self.last_transport,
                          'provider':self.provider.public(),'session_saved':self.session_path.exists()}
            return v

    def close(self):
        with self.lock:
            if self.closed:return
            self.closed=True;self.generation+=1;self.stop_event.set();self.wake.set()
            self.auto_remaining=0;self.message_tickets=0;self.manual_request=None
        if self.thread and self.thread is not threading.current_thread():self.thread.join(timeout=2)
        self.file_lock.close()
