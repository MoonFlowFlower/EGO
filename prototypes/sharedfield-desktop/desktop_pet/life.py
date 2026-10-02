"""Durable life state. Time advances only while the app has a live connection."""
from __future__ import annotations
import copy
import hashlib
import json
import os
import re
from pathlib import Path
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from .letter_content import FORMAT,life_letter_content,fact_text

PERSONALITIES={
    'warm':('热情开朗','喜欢分享，亲近自然，也愿意学着给彼此留出空间。'),
    'gentle':('温柔体贴','说话轻一点，喜欢照顾小细节，也有自己的小心思。'),
    'shy':('慢热敏感','初见有一点拘谨，熟悉之后才慢慢打开话匣子。'),
    'curious':('独立好奇','喜欢琢磨小东西，享受独处，也想把发现告诉你。'),
}
ACTIVITIES={
    'idle':('在窗边发呆',[48,54],12),
    'eat':('吃一点热乎的',[76,66],12),
    'rest':('抱着枕头休息',[24,39],22),
    'write':('写一封小信',[77,35],15),
    'read':('看看你的便签',[49,64],18),
    'wander':('在小屋里走走',[37,69],10),
}


class Life:
    def __init__(self,directory,enable_life_sharing=True):
        # Only separated v3 facts/fiction can be dispatched; old prose stays sealed.
        self.enable_life_sharing=enable_life_sharing
        self.directory=Path(directory).resolve();self.directory.mkdir(parents=True,exist_ok=True)
        self.workspace=self.directory/'workspace';self.workspace.mkdir(exist_ok=True)
        note=self.workspace/'给悠小喵的便签.txt'
        if not note.exists():note.write_text('欢迎来到你的小屋。\n食物在餐桌旁，累了可以回床上休息。\n我忙的时候，你可以做自己的事，把想分享的话写成信，等我回来再看。',encoding='utf-8')
        self.lock=threading.RLock()
        with self.db() as db:
            db.executescript('CREATE TABLE IF NOT EXISTS state(id INTEGER PRIMARY KEY,value TEXT);'
                'CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,kind TEXT,text TEXT,created REAL);'
                'CREATE TABLE IF NOT EXISTS commands(id TEXT PRIMARY KEY);'
                'CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY,role TEXT,text TEXT,created REAL,mode TEXT);'
                'CREATE TABLE IF NOT EXISTS calls(id TEXT PRIMARY KEY,value TEXT);')
            row=db.execute('SELECT value FROM state WHERE id=1').fetchone()
            if row:self.state=json.loads(row[0])
            else:
                self.state=dict(version=1,name='悠小喵',personality='warm',onboarded=False,
                    hunger=64.0,energy=76.0,food=5,selfcare=False,quiet_sharing=True,
                    busy_until=None,busy_since=None,busy_minutes=5,active_seconds=0.0,
                    activity=None,position=[48,54],last_letter=-150.0,last_contact=-1000.0,
                    letters=[],diary=[],memories=[],last_note=None,model='qwen35',model_status='ready')
                self._save(db)
            self.state.setdefault('letter_jobs',[])
            self.state.setdefault('share_moments',[])
            self.state.setdefault('share_milestones',[])
            for job in self.state['letter_jobs']:
                if job['status']=='processing':job.update(status='error',error='上次回信中断，未自动重发。')
                elif job.get('kind')=='life' and job.get('format')!=FORMAT and job['status'] in ('waiting','queued'):
                    job.update(status='error',error='旧版生活信已封存，未自动重新生成。')
            self._save(db)

    @contextmanager
    def db(self):
        db=sqlite3.connect(self.directory/'life.sqlite',timeout=15)
        try:
            with db:yield db
        finally:db.close()

    def _save(self,db):
        db.execute('INSERT OR REPLACE INTO state VALUES(1,?)',(json.dumps(self.state,ensure_ascii=False),))

    def _event(self,db,kind,text):
        eid=uuid.uuid4().hex
        db.execute('INSERT INTO events VALUES(?,?,?,?)',(eid,kind,text,time.time()))
        return eid

    def _memory(self,text,source):
        self.state['memories']=[m for m in self.state['memories'] if m['text']!=text]
        self.state['memories'].append(dict(text=text,source=source,time=time.time()))

    def snapshot(self):
        with self.lock,self.db() as db:
            state=copy.deepcopy(self.state)
            state['life_sharing_enabled']=self.enable_life_sharing
            state['letter_work']=[{k:j[k] for k in ('id','status','error') if k in j}|{'name':j.get('title') or j['note']['name']} for j in state.pop('letter_jobs',[])][-10:]
            state.pop('share_moments',None)
            state['events']=[dict(id=r[0],kind=r[1],text=r[2],time=r[3]) for r in db.execute('SELECT * FROM events ORDER BY created DESC LIMIT 60')]
            state['messages']=[dict(id=r[0],role=r[1],text=r[2],time=r[3],mode=r[4]) for r in reversed(list(db.execute('SELECT * FROM messages ORDER BY created DESC LIMIT 80')))]
            state['workspace']=str(self.workspace)
            state['personalities']={k:{'name':v[0],'description':v[1]} for k,v in PERSONALITIES.items()}
            state['note_files']=[p.name for p in self.workspace.iterdir() if p.is_file() and p.suffix.lower() in ('.txt','.md')]
            return state

    def _start(self,kind,initiator='autonomous'):
        label,target,duration=ACTIVITIES[kind]
        self.state['activity']=dict(kind=kind,label=label,target=target,remaining=duration+4,total=duration+4,walking=4)
        self.state['activity']['initiator']=initiator
        if kind in ('eat','rest') and initiator=='autonomous':
            teaching=next((m for m in self.state['memories'] if m['text'].startswith('照顾自己的身体')),None)
            if teaching:self.state['activity']['teaching_source']=teaching['source']
        if kind=='write':
            job=next((j for j in self.state['letter_jobs'] if j['status']=='waiting' and self._job_enabled(j)),None)
            if job:self.state['activity']['letter_job']=job['id']

    def _diary(self,text,source):
        self.state['diary'].append(dict(id=uuid.uuid4().hex,text=text,time=time.time(),source=source))

    def _record_moment(self,db,a,eid,changes):
        if not self.enable_life_sharing:return
        row=db.execute('SELECT kind,text,created FROM events WHERE id=?',(eid,)).fetchone()
        moment=dict(id=eid,kind=row[0],text=row[1],time=row[2],actor='pet',actor_name='悠小喵',initiator=a.get('initiator','unknown'),changes=changes,source_ids=[eid])
        try:fact_text(moment)
        except ValueError:return
        source=a.get('teaching_source')
        teaching=db.execute('SELECT text FROM events WHERE id=?',(source,)).fetchone() if source else None
        if teaching:
            moment['teaching']={'id':source,'text':teaching[0]};moment['source_ids'].append(source)
        self.state['share_moments'].append(moment)
        # Only the first demonstrated self-care action of each kind gets an
        # automatic letter. Reopening or re-teaching never resets this quota.
        if teaching and moment['kind'] not in self.state['share_milestones']:
            self._queue_moment(moment)
            self.state['share_milestones'].append(moment['kind'])

    def _queue_moment(self,moment):
        title='自己照顾自己的一件小事' if moment.get('teaching') else '小屋里的一件小事'
        self.state['letter_jobs'].append(dict(id=uuid.uuid4().hex,kind='life',format=FORMAT,title=title,status='waiting',moment=copy.deepcopy(moment),personality=self.state['personality']))

    def _unshared_moment(self):
        if not self.enable_life_sharing:return None
        used={j['moment']['id'] for j in self.state['letter_jobs'] if j.get('kind')=='life'}
        return next((m for m in reversed(self.state['share_moments']) if m['id'] not in used and not m.get('invalidated')),None)

    def _invalidate_sharing(self,sources):
        sources=set(sources)
        for moment in self.state['share_moments']:
            if sources.intersection(moment['source_ids']):moment['invalidated']=True
        for job in self.state['letter_jobs']:
            if sources.intersection(job.get('moment',{}).get('source_ids',[])) and job['status'] not in ('done','error','cancelled'):
                job.update(status='cancelled',error='相关来源已删除或教学已取消，这封信不再发送。')
        for letter in self.state['letters']:
            if sources.intersection(letter.get('source_moment',{}).get('source_ids',[])):letter['withdrawn']=True
        a=self.state.get('activity')
        cancelled={j['id'] for j in self.state['letter_jobs'] if j['status']=='cancelled'}
        if a and (a.get('teaching_source') in sources or a.get('letter_job') in cancelled):self.state['activity']=None

    def _finish(self,db,a):
        s=self.state;kind=a['kind'];s['position']=a['target'];s['activity']=None
        if kind=='eat':
            if s['food']<1:
                self._event(db,'help','餐桌上的食物吃完了，想请你帮忙添一点。');return
            before={'food':s['food'],'hunger':s['hunger']}
            s['food']-=1;s['hunger']=4
            text='吃完了一份餐点。';eid=self._event(db,'eat',text)
            self._diary('吃完了，肚子暖暖的。'+('这次是自己照顾自己。' if a.get('teaching_source') else '谢谢你记得叫我吃饭。' if a.get('initiator')=='user' else ''),eid)
            self._record_moment(db,a,eid,{k:{'before':v,'after':s[k]} for k,v in before.items()})
        elif kind=='rest':
            before=s['energy']
            s['energy']=98;eid=self._event(db,'rest','在床上休息了一会儿，恢复了精力。')
            self._diary('抱着枕头歇了一会儿，现在精神好多了。',eid)
            self._record_moment(db,a,eid,{'energy':{'before':before,'after':s['energy']}})
        elif kind=='write':
            job=next((j for j in s['letter_jobs'] if j['id']==a.get('letter_job')),None)
            if job and job['status']=='waiting':job['status']='queued'
            s['last_letter']=s['active_seconds']
        elif kind=='read':
            note=s.get('last_note')
            text='读完了便签「'+note['name']+'」。' if note else '在窗边坐了一会儿。'
            eid=self._event(db,'read' if note else 'idle',text)
            self._diary(text+(('\n里面写着：'+note['text'][:180]) if note else ''),eid)
            if note and note['text'].strip() and note.get('version'):
                s['completed_note']=dict(note,source=eid)
                if not any(j.get('note',{}).get('version')==note['version'] and j.get('note',{}).get('name')==note['name'] for j in s['letter_jobs']):
                    s['letter_jobs'].append(dict(id=uuid.uuid4().hex,status='waiting',note=copy.deepcopy(s['completed_note']),personality=s['personality']))
        elif kind=='wander':self._event(db,'wander','在小屋里走了走。')
        s['activity']=None

    def advance(self,seconds):
        if not 0<seconds<=3:raise ValueError('Only bounded live time can advance')
        with self.lock,self.db() as db:
            s=self.state;s['active_seconds']+=seconds
            s['hunger']=min(100,s['hunger']+seconds*.075)
            s['energy']=max(0,s['energy']-seconds*.045)
            if s['activity']:
                a=s['activity'];a['remaining']-=seconds;a['walking']=max(0,a['walking']-seconds)
                if a['walking']==0:s['position']=a['target']
                if a['remaining']<=0:self._finish(db,a)
            else:
                if s['selfcare'] and s['hunger']>50 and s['food']>0:self._start('eat')
                elif s['selfcare'] and s['energy']<38:self._start('rest')
                elif self._has_new_note():self._start('write')
                else:
                    options=['idle','wander','idle','read'] if s.get('last_note') else ['idle','wander','idle']
                    self._start(options[int(s['active_seconds']//16)%len(options)])
                if s['selfcare'] and s['hunger']>50 and s['food']==0 and s['active_seconds']-s['last_contact']>120:
                    self._event(db,'help','想自己吃饭，可是餐桌上没有食物了。可以帮我添一点吗？');s['last_contact']=s['active_seconds']
                if s['busy_until'] and time.time()>s['busy_until']+({'warm':180,'gentle':420,'shy':600,'curious':900}[s['personality']]) and s['active_seconds']-s['last_contact']>300:
                    self._event(db,'contact','你忙完了吗？有一点想你。看到的时候回我就好。');s['last_contact']=s['active_seconds']
            self._save(db)

    def _note_path(self,name):
        if not isinstance(name,str) or not name.strip() or name!=name.strip() or name.endswith('.') or re.search(r'[<>:"/\\|?*\x00-\x1f]',name) or re.match(r'(?i)^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)',name):raise ValueError('请使用普通便签文件名')
        path=(self.workspace/name).resolve()
        if not path.is_relative_to(self.workspace) or path.suffix.lower() not in ('.txt','.md'):raise ValueError('只能使用小屋文件夹内的txt或md便签')
        return path

    def read_note(self,name):
        path=self._note_path(name)
        if not path.is_file():raise ValueError('便签不存在，请先保存')
        if path.stat().st_size>65536:raise ValueError('便签请小于64KB')
        content=path.read_bytes();text=content.decode('utf-8-sig')
        if len(text)>6000:raise ValueError('这张便签超过6000字，请在文件中缩短后再打开；原文件未修改')
        return dict(name=path.name,text=text,version=hashlib.sha256(content).hexdigest())

    def save_note(self,name,text,version):
        if not isinstance(text,str) or len(text)>6000:raise ValueError('便签最多6000字')
        with self.lock:
            path=self._note_path(name)
            current=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
            if current!=version:raise ValueError('便签已被其他窗口或编辑器修改，请重新打开再保存；你的草稿还在')
            temp=path.with_name('.'+uuid.uuid4().hex+'.tmp')
            try:
                temp.write_text(text,encoding='utf-8');os.replace(temp,path)
            finally:temp.unlink(missing_ok=True)
            return self.read_note(name)

    def _has_new_note(self):
        return any(j['status']=='waiting' and self._job_enabled(j) for j in self.state['letter_jobs'])

    def _job_enabled(self,job):
        return job.get('kind')!='life' or (self.enable_life_sharing and job.get('format')==FORMAT)

    def claim_letter_job(self):
        with self.lock,self.db() as db:
            job=next((j for j in self.state['letter_jobs'] if j['status']=='queued' and self._job_enabled(j)),None)
            if not job:return None
            job['status']='processing';self._save(db);return copy.deepcopy(job)

    def finish_letter_job(self,job_id,text=None,error=None):
        with self.lock,self.db() as db:
            job=next(j for j in self.state['letter_jobs'] if j['id']==job_id)
            if job['status']!='processing':return
            if error:job.update(status='error',error=error)
            else:
                is_life=job.get('kind')=='life'
                if is_life:
                    if not self._job_enabled(job):raise ValueError('此生活分享版本未启用')
                    content=life_letter_content(job['moment'],text)
                else:
                    if not isinstance(text,str) or not text.strip():raise ValueError('信件没有正文')
                    content={'text':text}
                title=job['title'] if is_life else '读到你写的「'+job['note']['name']+'」'
                eid=self._event(db,'letter','写下了信：'+title)
                source={'source_moment':job['moment']} if is_life else {'source_note':job['note']}
                self.state['letters'].append(dict(id=eid,title=title,time=time.time(),read=False,mode='model',**content,**source))
                self._diary('把一件生活小事写进信里。' if is_life else '读过便签后写下了回信。',eid);job['status']='done'
            self._save(db)

    def command(self,kind,data=None,request_id=None):
        data=data or {};request_id=request_id or uuid.uuid4().hex
        with self.lock,self.db() as db:
            if db.execute('SELECT 1 FROM commands WHERE id=?',(request_id,)).fetchone():return self.snapshot()
            # Validate before touching the mutable in-memory state.
            if kind=='personality' and data.get('value') not in PERSONALITIES:raise ValueError('未知性格')
            if kind=='busy':minutes=max(1,min(240,int(data.get('minutes',5))))
            if kind=='write' and not self._has_new_note() and not self._unshared_moment():raise ValueError('暂时没有新的小事可分享，等她完成一件事，或写张便签给她吧。')
            if kind=='read':
                note=self.read_note(data.get('name','给悠小喵的便签.txt'))
                if 'version' in data and data['version']!=note['version']:raise ValueError('便签刚被修改，请重新打开确认内容后再请她读')
            allowed={'personality','busy','return','teach','unlearn','letter_read','quiet','restock','read','eat','rest','write','wander','idle'}
            if kind not in allowed:raise ValueError('未知操作')
            s=self.state
            if kind=='personality':
                s['personality']=data['value'];s['onboarded']=True
                self._event(db,'setting','选择相处性格：'+PERSONALITIES[s['personality']][0])
            elif kind=='busy':
                s['busy_since']=time.time();s['busy_until']=time.time()+minutes*60;s['busy_minutes']=minutes
                eid=self._event(db,'user',f'用户说要忙{minutes}分钟，希望先不打扰。')
                self._memory('用户忙的时候先把分享写成信，等回来再聊。',eid)
                # Busy is not evidence of having something to write, and must
                # not interrupt the actual meal/rest/read already in progress.
                if not s['activity']:self._start('write' if self._has_new_note() else 'idle')
            elif kind=='return':
                s['busy_until']=None;s['busy_since']=None
                self._event(db,'user','用户回来了，之前等待用户忙完的约定已结束。')
            elif kind=='teach':
                s['selfcare']=True
                eid=self._event(db,'teaching','用户教我：饿了自己找食物吃，累了自己去休息；没有食物时求助。')
                self._memory('照顾自己的身体：饿了自己吃饭，累了自己休息，缺少东西就求助。',eid)
                s['activity']=None
            elif kind=='unlearn':
                teaching_sources=[m['source'] for m in s['memories'] if m['text'].startswith('照顾自己的身体')]
                teaching_sources += [m['teaching']['id'] for m in s['share_moments'] if m.get('teaching')]
                self._invalidate_sharing(teaching_sources)
                s['selfcare']=False
                s['memories']=[m for m in s['memories'] if not m['text'].startswith('照顾自己的身体')]
                self._event(db,'correction','用户取消了自主吃饭和休息的教学规则。')
            elif kind=='quiet':
                s['quiet_sharing']=bool(data.get('value',True))
                eid=self._event(db,'feedback','用户希望分享先留信。' if s['quiet_sharing'] else '用户喜欢在空闲时主动分享。')
                self._memory('分享方式：'+('先留信，等我来找你。' if s['quiet_sharing'] else '空闲时可以主动来找我。'),eid)
            elif kind=='restock':s['food']+=5;self._event(db,'supply','用户给餐桌补了5份食物。')
            elif kind=='letter_read':
                for letter in s['letters']:
                    if letter['id']==data.get('id'):letter['read']=True
            elif kind=='read':s['last_note']=note;self._start('read');self._event(db,'source','打开真实文件：'+note['name'])
            else:
                if kind=='eat' and s['food']<1:raise ValueError('餐桌没有食物啦，先添一些吧')
                if kind=='write' and not self._has_new_note():self._queue_moment(self._unshared_moment())
                self._start(kind,initiator='user');self._event(db,'instruction','用户邀请：'+ACTIVITIES[kind][0])
            db.execute('INSERT INTO commands VALUES(?)',(request_id,));self._save(db)
        return self.snapshot()

    def message(self,role,text,mode='model',message_id=None):
        with self.lock,self.db() as db:
            eid=message_id or uuid.uuid4().hex
            db.execute('INSERT OR IGNORE INTO messages VALUES(?,?,?,?,?)',(eid,role,text,time.time(),mode))
            if role=='user':
                db.execute('INSERT OR IGNORE INTO events VALUES(?,?,?,?)',(eid,'user',text,time.time()))
            return eid

    def set_model(self,model,status):
        with self.lock,self.db() as db:self.state.update(model=model,model_status=status);self._save(db)

    def record_call(self,value):
        with self.lock,self.db() as db:db.execute('INSERT INTO calls VALUES(?,?)',(uuid.uuid4().hex,json.dumps(value,ensure_ascii=False)))

    def remember_user(self,text,source):
        with self.lock,self.db() as db:self._memory('你说：'+text,source);self._save(db)

    def forget(self,source):
        with self.lock,self.db() as db:
            self._invalidate_sharing([source])
            removed=[m for m in self.state['memories'] if m['source']==source]
            if any(m['text'].startswith('照顾自己的身体') for m in removed):self.state['selfcare']=False
            if any(m['text'].startswith('用户忙的时候') for m in removed):self.state['busy_until']=None
            self.state['memories']=[m for m in self.state['memories'] if m['source']!=source]
            db.execute('DELETE FROM messages WHERE id=?',(source,))
            db.execute('DELETE FROM events WHERE id=?',(source,))
            self._save(db)
