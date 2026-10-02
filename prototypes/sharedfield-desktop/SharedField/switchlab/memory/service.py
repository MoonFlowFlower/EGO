"""Actual chat + prospective-memory + shared-world loop.

Language calls happen outside the state lock. Every observation and accepted
change commits before acknowledgement. Runtime enable/permission is never
controlled by retrieved text. On restart, life persists but execution is paused.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import json,os,sqlite3,tempfile,threading,time,uuid
from ..studio.service import Service,DirectoryLock
from ..studio.provider import Provider
from ..studio.protocol import parse_json
from ..runtime import save_json,load_json
from ..shared.core import SharedCore
from ..shared.grounding import contract,guard_speech
from .store import MemoryStore,string,only,encode,digest
from .timeutil import iso
from .protocol import SYSTEM,INTERPRET,EXPRESS,CONTACT
from .reading_service import ReadingMixin

OPTIONS={'language_mode':'local','auto_replay':False,'world_interval':1.4}
class MemoryService(ReadingMixin,Service):
    def __init__(self,directory,provider=None,clock=None):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.file_lock=DirectoryLock(self.directory);self.lock=threading.RLock();self.wake=threading.Event();self.stop_event=threading.Event()
        self.thread=None;self.busy=False;self.closed=False;self.generation=0;self.manual_request=None;self.step_ticket=False;self.reading_enabled=False
        self.auto_remaining=0;self.message_tickets=0;self.background=False;self.pending=None;self.active_phase=None;self.error='';self.last_transport='none'
        self.clock=clock or time.time;self.next_world=0;self.last_check=0;self.last_context=None;self.session_path=self.directory/'memory.sqlite3'
        self.status='记忆已保留，执行暂停。先聊一句；后台联系需要单独开启。'
        try:
            self.store=MemoryStore(self.session_path);self.store.sanity()
            path=self.directory/'provider.json';self.provider=provider or Provider(load_json(path) if path.exists() else None)
            path=self.directory/'memory_options.json';self.options={**OPTIONS,**(load_json(path) if path.exists() else {})};self._validate_options(self.options)
        except BaseException:
            if hasattr(self,'store'):self.store.close()
            self.file_lock.close();raise

    def _commit(self,kind,data,**kwargs):
        if kind=='usage' and 'usage' in data:data={**data['usage'],'model':data.get('model','unknown')}
        try:return self.store.apply(kind,data,at=self.clock(),**kwargs)
        except (OSError,sqlite3.Error) as e:
            self.auto_remaining=0;self.background=False;self.message_tickets=0;self.generation+=1
            self.error='本地保存失败，已停止；没有确认尚未可靠保存的内容。请检查磁盘和备份。'
            raise ValueError(self.error) from e

    @staticmethod
    def _validate_options(p):
        only(p,OPTIONS)
        if 'language_mode' in p and p['language_mode'] not in ('local','manual','api'):raise ValueError('invalid language mode')
        if 'auto_replay' in p and type(p['auto_replay']) is not bool:raise ValueError('auto_replay must be boolean')
        if 'world_interval' in p and (type(p['world_interval']) not in (int,float) or not .2<=p['world_interval']<=10):raise ValueError('world interval .2..10')
    def set_options(self,p):
        self._validate_options(p)
        with self.lock:
            if self.busy:raise ValueError('请暂停并等请求结束，再修改设置')
            proposed={**self.options,**p};save_json(self.directory/'memory_options.json',proposed)
            self.pause();self.options=proposed;self.error='';return deepcopy(self.options)
    def configure(self,data,key=None,clear_key=False):
        with self.lock:
            result=super().configure(data,key,clear_key);self.pause();self.error='';return result

    def set_memory_settings(self,p):
        with self.lock:
            self.reading_enabled=False
            result=self._commit('setting',p);self.generation+=1;self.manual_request=None;self.pending=None
            self.status='记忆设置已保存，旧的未提交语言结果不会覆盖新设置。';return result['result']

    def submit(self,content):
        string(content,'消息',24000)
        with self.lock:
            self.reading_enabled=False
            result=self._commit('message',{'text':content})
            self.generation+=1;self.manual_request=None;self.pending={'source':result['id'],'phase':'interpret','reads':0,'queries':[],'ids':[],'receipt':None}
            self.message_tickets=1;self.error='';self.status='原话已保存，正在理解。';self.wake.set();return result
    def resume_turn(self,source):
        with self.lock:
            self.store._user_source(source)
            self.generation+=1;self.manual_request=None;self.pending={'source':source,'phase':'express' if self.store.setting('interpreted:'+source) else 'interpret','reads':0,'queries':[],'ids':[],'receipt':{'resumed_existing_memory':True}}
            self.message_tickets=1;self.error='';self.wake.set()
    def pause(self):
        with self.lock:
            self.reading_enabled=False
            self.auto_remaining=0;self.background=False;self.message_tickets=0;self.manual_request=None;self.step_ticket=False;self.generation+=1;self.pending=None
            self.status='已暂停。经历和约定仍保留；已发请求可能计费，但迟到结果不执行。';self.wake.set()
    def start_background(self):
        with self.lock:
            self.background=True;self.error='';self.status='已允许本地后台检查有效约定和有界重放；只有有事可处理才工作。';self.wake.set()
    def start_auto(self,count=8):
        if type(count) is not int or not 1<=count<=600:raise ValueError('共享探索授权1..600步')
        with self.lock:self.auto_remaining=count;self.next_world=0;self.error='';self.wake.set()
    def request_step(self):
        with self.lock:self.step_ticket=True;self.error='';self.wake.set()
    def call_ceiling(self):
        return self.store.setting('call_ceiling') if self.store.setting('call_ceiling') is not None else self.provider.config.get('max_calls',48)
    def grant_calls(self,count):
        with self.lock:
            e=self._commit('grant_calls',{'count':count,'previous_ceiling':self.call_ceiling()});self.error='';return e['result']
    def _reserve_call(self,phase):
        if (self.store.setting('calls') or 0)>=self.call_ceiling():raise ValueError('本生命周期模型请求额度已用完，请在设置中明确提高上限；原记忆不清空')
        self._commit('call',{'phase':phase,'model':self.provider.config.get('model') or 'manual'})

    def world_view(self):
        c=SharedCore();snapshot=self.store.setting('world_snapshot')
        if snapshot:c._load(snapshot)
        return c.view()
    def world_command(self,kind,payload):
        with self.lock:
            result=self._commit('world',{'kind':kind,'payload':payload});self.error='';self.wake.set();return result
    def edit_commitment(self,data):
        """Maintenance/manual input uses the very same source/revision reducer."""
        with self.lock:
            only(data,('id','expected_revision','op','title','category','quote','when','accept'),('op','quote'))
            mid=self._commit('message',{'text':data['quote']})['id']
            result=self._commit('interpret',{'source':mid,'claims':[],'commitments':[data]})
            self.generation+=1;self.manual_request=None;self.pending=None;self.message_tickets=0;self.error=''
            self._commit('expression',{'text':'这项约定的变更已经保存。','source':mid,'evidence':[mid],'transport':'local'})
            self.wake.set();return result['result']
    def give_feedback(self,contact,outcome,explanation):
        with self.lock:
            mid=self._commit('message',{'text':string(explanation,'反馈说明',2000)})['id']
            result=self._commit('feedback',{'contact':contact,'outcome':outcome,'source':mid})
            self._commit('expression',{'text':'我会把这次是否方便联系的实际反馈记下来；它不是好感评分。','source':mid,'evidence':[mid],'transport':'local'})
            return result['result']

    def _build(self,phase,pending):
        from .reading import chat_context
        source=pending.get('source');selected=self.store.observation(source) if source else None
        query=selected['text'] if selected else self.store.commitment(pending['contact']['cid'])['title']
        memory=self.store.context(query,budget_bytes=self.store.setting('memory_budget_bytes'),extra_queries=pending.get('queries'),ids=pending.get('ids'),windows=pending.get('windows'))
        w=self.world_view();r=w['cognition'];focus=deepcopy(r.get('focus'))
        if focus:focus.pop('candidates',None);focus.pop('coefficients',None)
        shared={'namespace':'shared_world','world_tick':w['world']['tick'],'state_words':r['state_words'],'affect':r['affect'],'self_model':r['self_model'],
                'focus':focus,'basis':r['basis'],'boundary':'只描述内置环境状态，不等于现实情绪或用户位置'}
        data={'phase':phase,'context':{'memory':memory,'current_time':iso(self.clock(),self.store.setting('timezone')),'timezone':self.store.setting('timezone'),
                                     'shared_world_context':shared,'availability_model':self.store.model(),'busy_until':self.store.setting('busy_until')},
              'selected_input':selected,'write_receipt':pending.get('receipt')}
        data['context']['reading']=chat_context(self.store)
        refs=list(dict.fromkeys(memory['evidence_ids']+data['context']['reading']['evidence_ids']))
        if pending.get('page') is not None:
            page=self.store.commitments(limit=20,offset=pending['page'],include_closed=False);data['context']['commitment_page']=page
            refs=list(dict.fromkeys(refs+[c['source'] for c in page['items']]))
        recent_contacts=[]
        for row in self.store.db.execute('SELECT key FROM contacts ORDER BY rowid DESC LIMIT 4'):
            recent_contacts.append(self.store.contact(row[0]))
        data['context']['recent_contacts']=recent_contacts
        if phase=='contact':data['candidate']=pending['contact'];data['commitment']=self.store.commitment(pending['contact']['cid'])
        # The complete selected input is mandatory. It is never silently cut to fit.
        wire=encode(data)
        if len(wire.encode())>90000:raise ValueError('本次必要信息超过输入字节预算，请分次表达或调整记忆预算；原话已经保存')
        self.last_context=deepcopy(data)
        self._commit('context_read',{'source_ids':refs,'query':query[:1200],'bytes':len(wire.encode())})
        instructions=INTERPRET if phase=='interpret' else CONTACT if phase=='contact' else EXPRESS
        return [{'role':'system','content':SYSTEM+'\n'+instructions},{'role':'user','content':wire}],refs,shared

    def _recall(self,packet):
        only(packet,('queries','ids','commitment_offset','windows'))
        queries=packet.get('queries',[]);ids=packet.get('ids',[])
        if not isinstance(queries,list) or len(queries)>3 or not isinstance(ids,list) or len(ids)>12:raise ValueError('retrieval budget exceeded')
        for q in queries:string(q,'query',240)
        for oid in ids:self.store.observation(oid)
        page=packet.get('commitment_offset')
        if page is not None and (type(page) is not int or page<0):raise ValueError('invalid commitment page')
        windows=packet.get('windows',[])
        if not isinstance(windows,list) or len(windows)>4:raise ValueError('最多4个原文窗口')
        for w in windows:
            only(w,('id','start','length'),('id','start','length'));self.store.observation(w['id'])
            if type(w['start']) is not int or w['start']<0 or type(w['length']) is not int or not 1<=w['length']<=4000:raise ValueError('窗口范围无效')
        return queries,ids,page,windows

    def _finish(self,r,packet):
        if self.closed or r['generation']!=self.generation:raise ValueError('旧的语言结果已取消')
        phase=r['phase'];current=self.pending
        if phase=='interpret':
            only(packet,('claims','commitments','availability','recall','feedback','world_request'),('claims','commitments'))
            queries,ids,page,windows=self._recall(packet.get('recall',{}))
            body={k:packet[k] for k in ('claims','commitments','availability','feedback','world_request') if k in packet};body['source']=r['source']
            # Source and version constraints are checked atomically before acknowledgement.
            event=self._commit('interpret',body,expected_revision=r['memory_revision'])
            self.pending={'source':r['source'],'phase':'express','queries':queries,'ids':ids,'page':page,'windows':windows,'reads':0,'receipt':event['result']}
            self.status='已保存有来源的理解与约定，正在组织回答。'
        elif phase=='express':
            if 'recall' in packet:
                only(packet,('recall',),('recall',))
                if current.get('reads',0)>=2:raise ValueError('本轮额外回忆预算已用完；没有继续收费，请缩小问题或查阅记忆')
                queries,ids,page,windows=self._recall(packet['recall']);current.update(queries=queries,ids=ids,page=page,windows=windows,reads=current.get('reads',0)+1)
                self.status='正在按新线索查回原始经历。';return
            only(packet,('speech','evidence_ids'),('speech',));refs=packet.get('evidence_ids',[])
            if not isinstance(refs,list) or not set(refs)<=set(r['evidence']):raise ValueError('表达引用了本轮未读到的来源')
            self._commit('expression',{'text':packet['speech'],'source':r['source'],'evidence':r['evidence'],'transport':r['transport'],
                                      'snapshot':{'memory_revision':r['memory_revision'],'time':r['at'],'shared_world':r['shared']}},dependencies=r['evidence'])
            self.pending=None;self.message_tickets=0;self.status='这段对话与使用过的经历已保存。'
        else:
            only(packet,('action','speech','seconds','reason'),('action',))
            key=r['contact']['key']
            if packet['action']=='wait':self._commit('defer',{'contact':key,'seconds':packet.get('seconds'),'reason':packet.get('reason')})
            elif packet['action']=='contact':
                self._commit('expression',{'text':packet.get('speech'),'source':None,'evidence':r['evidence'],'contact':key,'transport':r['transport'],
                                          'snapshot':{'memory_revision':r['memory_revision'],'time':r['at']}},dependencies=r['evidence'])
            else:raise ValueError('background action must be contact or wait')
            self.pending=None;self.status='已处理这次约定，等待真实反馈；不会重复当作新事件。'
        self.error=''

    def run_once(self,force=False):
        reading_result=self.reading_run_once()
        if reading_result is not None:return reading_result
        with self.lock:
            if self.closed or self.busy or self.manual_request or self.error:return False
            now=self.clock();pending=self.pending
            last_contact=self.store.setting('last_contact_at')
            contact_window=(last_contact is None or now>=last_contact+120)
            if pending is None and self.background and contact_window:
                prepared=self.store.pending_contacts()
                # Recover a prepared local outbox item only after explicit re-enable.
                busy_until=self.store.setting('busy_until')
                for c in prepared:
                    cur=self.store.commitment(c['cid'])
                    if cur['revision']==c['revision'] and cur['status'] not in ('cancelled','completed') and (not busy_until or now>=busy_until):
                        pending={'phase':'contact','source':None,'contact':c,'queries':[],'ids':[c['source']]};break
                if pending is None:
                    due=self.store.due(now,limit=1)
                    if due:
                        result=self._commit('consider',{'id':due[0]['id'],'revision':due[0]['revision']})['result']
                        if result['action']=='wait':self.status='根据当前信息先等待，约定没有遗忘。';return True
                        pending={'phase':'contact','source':None,'contact':result['contact'],'queries':[],'ids':[due[0]['source']]}
                if pending is None and self.options['auto_replay'] and self.store.outcome_count()>(self.store.setting('consolidated_outcomes') or 0):
                    self._commit('replay',{});self.status='完成一次真实经验重放，没有制造新证据。';return True
                self.pending=pending
            if pending is None:
                if force or self.auto_remaining>0:
                    if not force and time.monotonic()<self.next_world:return False
                    last=self.store.setting('world_snapshot')
                    if last and not force and last['state'].get('last_result',{}).get('kind')=='waiting_for_partner':return False
                    event=self.world_command('agent_step',{})
                    if event['result']['kind'] in ('waiting_for_partner','sleep'):
                        if event['result']['kind']=='sleep':self.auto_remaining=0
                    else:self.auto_remaining=max(0,self.auto_remaining-1)
                    self.next_world=time.monotonic()+self.options['world_interval'];return True
                return False
            phase=pending['phase'];mode=self.options['language_mode']
            if mode=='local':
                if phase=='contact':
                    c=self.store.commitment(pending['contact']['cid'])
                    text='【本地联系 · 未调用语言模型】你之前说过「'+c['quote']+'」。现在情况有变化吗？'
                    self._commit('expression',{'text':text,'source':None,'evidence':[c['source']],'contact':pending['contact']['key'],'transport':'local'})
                else:
                    source=pending['source'];memory=self.store.context(self.store.observation(source)['text']);titles=[c['title'] for c in memory['effective_commitments'] if c['status'] not in ('cancelled','completed')]
                    text='【本地模式 · 未连接语言模型】原话已经可靠保存，但我还不能可靠解释新的口头约定。连接模型后可自然交流，或在“约定”中直接确认。'
                    if titles:text+='当前保存的约定包括：'+'、'.join(titles[:5])+'。'
                    self._commit('expression',{'text':text,'source':source,'evidence':memory['evidence_ids'],'transport':'local'})
                self.pending=None;self.message_tickets=0;return True
            try:
                if mode=='api':
                    if self.provider.config['mode']!='api':raise ValueError('请先配置已有的模型服务')
                    required=2 if phase=='interpret' else 1
                    if self.call_ceiling()-(self.store.setting('calls') or 0)<required:raise ValueError('本轮请求余额不足，没有发送；可在设置中提高上限')
                messages,refs,shared=self._build(phase,pending)
                revision=self.store.revision
                if mode=='api':self._reserve_call('memory_'+phase)
                r={'id':uuid.uuid4().hex,'phase':phase,'source':pending.get('source'),'generation':self.generation,'memory_revision':revision,
                   'evidence':refs,'messages':messages,'shared':shared,'at':now,'contact':pending.get('contact'),'transport':'api' if mode=='api' else 'manual-external'}
            except (ValueError,TypeError,KeyError,sqlite3.Error) as e:self.error=str(e);self.background=False;self.auto_remaining=0;return False
            if mode=='manual':
                r['prompt']='\n\n'.join(m['content'] for m in messages);self.manual_request=r;self.status='等待手动模型交换 · '+phase;return True
            self.busy=True;self.active_phase=phase;provider=self.provider
        try:
            response=provider.complete(messages)
            with self.lock:
                if not self.closed:
                    self._commit('usage',{'usage':response.get('usage',{}),'model':response.get('model','unknown')})
                    if r['generation']==self.generation:
                        self._finish(r,response['packet']);self.last_transport=response.get('model','unknown')
                    else:self.status='请求期间状态已改变，旧输出未提交；请求可能计费。'
        except (ValueError,TypeError,KeyError,OSError,sqlite3.Error) as e:
            with self.lock:
                if not self.closed and r['generation']==self.generation:
                    self.error=str(e);self.background=False;self.auto_remaining=0;self.status='处理停止，原始经历保留；没有生成假回复或自动收费重试。'
        finally:
            with self.lock:self.busy=False;self.active_phase=None
            self.wake.set()
        return True

    def accept_manual(self,request_id,raw):
        packet=parse_json(raw)
        with self.lock:
            r=self.manual_request
            if not r or r['id']!=request_id:raise ValueError('手动请求已过期')
            if r.get('phase')=='reading':
                self._reading_finish(r,packet,'manual-external',{});self.manual_request=None;self.wake.set();return
            self._finish(r,packet);self.manual_request=None;self.wake.set()
    def _loop(self):
        while not self.stop_event.is_set():
            with self.lock:force=self.step_ticket;self.step_ticket=False
            try:did=self.run_once(force)
            except Exception:
                with self.lock:self.background=False;self.auto_remaining=0;self.error='运行异常已停止，请备份并查看维护记录。'
                did=False
            if not did:self.wake.wait(.5);self.wake.clear()

    def view(self):
        with self.lock:
            messages=list(reversed(self.store.recent(limit=60)['items']))
            for m in messages:
                if m['actor']=='user':m['responded']=bool(self.store.setting('responded:'+m['id']))
            world=self.world_view()
            return {'version':'0.7.0','person_id':self.store.person_id,'name':world['name'],'messages':messages,
                    'commitments':self.store.commitments(limit=30),'claims':self.store.claims(limit=20),'events':self.store.sequence,
                    'learning':{**self.store.model(),'unique_outcomes':self.store.outcome_count(),'enabled':self.store.setting('learning')},
                    'world':world,'time':iso(self.clock(),self.store.setting('timezone')),
                    'memory_settings':{k:self.store.setting(k) for k in ('timezone','learning','memory_budget_bytes','busy_until')},
                    'runtime':{'busy':self.busy,'error':self.error,'status':self.status,'background':self.background,'auto_remaining':self.auto_remaining,'min_contact_gap_seconds':120,
                               'options':deepcopy(self.options),'provider':self.provider.public(),'manual_request':deepcopy(self.manual_request),
                               'call_ceiling':self.call_ceiling(),'calls':self.store.setting('calls') or 0,'input_tokens':self.store.setting('input_tokens') or 0,'output_tokens':self.store.setting('output_tokens') or 0,
                               'session_saved':True,'paused_on_restore':True,'last_model':self.last_transport}}

    def import_checkpoint(self,data,archive_current=False):
        with self.lock:
            if self.busy:raise ValueError('先暂停并等待当前请求结束')
            if self.store.sequence and archive_current is not True:raise ValueError('当前已有经历；需确认先备份或使用新目录')
            candidate_path=self.directory/('import_'+uuid.uuid4().hex+'.sqlite3');candidate=None
            try:
                if data.get('schema')=='sharedfield.memory.v6':
                    from .store import code_fingerprint
                    if data.get('initial',{}).get('source_sha256')==code_fingerprint():candidate=MemoryStore.from_export(candidate_path,data)
                    else:
                        from .migration_v06 import import_v06
                        candidate=import_v06(candidate_path,data)
                else:
                    from .migration import verify_legacy
                    verified=verify_legacy(data);candidate=MemoryStore(candidate_path)
                    candidate.apply('legacy',{'archive':data,'snapshot':verified['snapshot'],'report':verified['report']},at=self.clock())
                candidate.sanity();count=candidate.sequence;pid=candidate.person_id;candidate.close();candidate=None
                if self.store.sequence:self.store.backup(self.directory/'backups'/('before_import_'+uuid.uuid4().hex+'.sqlite3'))
                self.pause();self.store.close()
                try:os.replace(candidate_path,self.session_path)
                finally:self.store=MemoryStore(self.session_path)
                self.status='旧经历已验证接入；缺少的真实日期保持未知，当前暂停。';return {'ok':True,'events':count,'person_id':pid,'paused':True}
            finally:
                if candidate is not None:candidate.close()
                for suffix in ('','-wal','-shm'):
                    p=Path(str(candidate_path)+suffix)
                    if p.exists():p.unlink()
    def forget(self,source_ids,confirmed=False):
        if confirmed is not True:raise ValueError('需明确确认删除来源及其派生内容，并重置相应学习状态')
        with self.lock:
            if self.busy:raise ValueError('请先暂停并等当前请求结束')
            self.pause();result=self.store.forget(source_ids,at=self.clock());self.last_context=None
            removed=0
            for p in (self.directory/'backups').glob('*.sqlite3'):
                p.unlink();removed+=1
                for suffix in ('-wal','-shm'):
                    side=Path(str(p)+suffix)
                    if side.exists():side.unlink()
            result['managed_backups_deleted']=removed;self.error='';self.status='指定来源及派生内容已删除；已有外部导出与系统备份不受本程序控制。'
            return result

    def backup(self):
        with self.lock:
            path=self.directory/'backups'/('memory_'+uuid.uuid4().hex+'.sqlite3');self.store.backup(path);return {'ok':True,'file':path.name}
    def close(self):
        with self.lock:
            if self.closed:return
            self.closed=True;self.generation+=1;self.stop_event.set();self.wake.set();self.pending=None;self.background=False
        if self.thread and self.thread is not threading.current_thread():self.thread.join(timeout=2)
        self.store.close();self.file_lock.close()
