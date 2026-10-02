"""Simulation process. Only this side owns the live environment."""
import base64,io,json,queue,threading,time
from PIL import Image
from .host import Host
from .models import LMStudio
from .sandbox import run as run_skill

class Runtime:
    def __init__(self,output,controls,model=None,formal=False):
        self.host=Host(length=180);self.output=output;self.controls=controls
        self.model=LMStudio(model) if isinstance(model,str) else model;self.formal=formal
        self.lock=threading.RLock();self.mode='agent';self.epoch=0;self.pending=[]
        self.responses=queue.Queue();self.inflight=False;self.skill_cancel=threading.Event();self.skill_thread=None
        self.basis='尚未选择';self.events=[];self.last_publish=0.;self.publish_s=[];self.dropped=0
        self.goal='尝试生存和基础制作' if model else '固定 noop 工程诊断'
        self.policy_input=None;self.human_started=None;self.human_seconds=0.
        self.publish(force=True)

    def control(self,command):
        if self.formal:raise ValueError('formal_read_only')
        if not isinstance(command,dict) or set(command)-{'mode','action'}:raise ValueError('command_denied')
        with self.lock:
            if 'mode' in command:
                if command['mode'] not in ('agent','human'):raise ValueError('mode_denied')
                self.epoch+=1;self.pending.clear();self.skill_cancel.set();self.mode=command['mode']
                now=time.monotonic()
                if self.human_started is not None:self.human_seconds+=now-self.human_started
                self.human_started=now if self.mode=='human' else None
                self.events.append({'type':'control','mode':self.mode,'tick':self.host.env._step})
            if 'action' in command:
                if self.mode!='human':raise ValueError('takeover_required')
                self.step(command['action'],'human')
            self.publish(force=True)

    def step(self,action,source):
        obs=self.host.act(action)
        self.events.append({'type':'step','source':source,'action':action,'tick':obs['tick'],'change':self.host.last_event})
        if 'health_lost' in self.host.last_event['events']: self.pending.clear()
        if action.startswith('move_') and obs['displacement']==[0,0]:self.pending.clear()
        self.publish()

    def publish(self,force=False):
        now=time.perf_counter()
        if not force and now-self.last_publish<.2:return
        start=time.perf_counter();self.last_publish=now
        frame=self.host.last_frame.copy();buf=io.BytesIO();Image.fromarray(frame).save(buf,format='PNG')
        snapshot={'observation':self.host.observe(),'policy_input':self.policy_input,
            'frame':'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode(),
            'mode':self.mode,'formal':self.formal,'thinking':self.inflight,'goal':self.goal,'basis':self.basis,
            'active_skill':'sandbox' if self.skill_thread and self.skill_thread.is_alive() else ('repeat' if self.pending else None),
            'events':self.events[-8:],'human_seconds':round(self.human_seconds+(time.monotonic()-self.human_started if self.human_started else 0),2)}
        try:self.output.put_nowait(snapshot)
        except queue.Full:
            try:self.output.get_nowait()
            except queue.Empty:pass
            try:self.output.put_nowait(snapshot)
            except queue.Full:pass
            self.dropped+=1
        self.publish_s.append(time.perf_counter()-start)

    def start_skill(self,source):
        with self.lock:
            self.skill_cancel=threading.Event();epoch=self.epoch
            def act(action):
                with self.lock:
                    if epoch!=self.epoch or self.mode!='agent':raise ValueError('stale_skill')
                    self.step(action,'skill');return self.host.observe()
            def observe():
                with self.lock:return self.host.observe()
            def work():self.skill_result=run_skill(source,observe,act,max_steps=32,timeout_s=5,cancel=self.skill_cancel)
            self.skill_thread=threading.Thread(target=work,daemon=True);self.skill_thread.start()

    def start_decision(self):
        epoch=self.epoch;obs=self.host.observe();self.policy_input=json.loads(json.dumps(obs));self.inflight=True
        messages=[{'role':'system','content':'Play Crafter. Choose a listed action. Reply JSON action, repeat 1..4, reason. No code.'},
                  {'role':'user','content':json.dumps({'observation':obs})}]
        def request():
            try:
                if self.model:content,_=self.model.decide(messages);choice=json.loads(content)
                else:choice={'action':'noop','repeat':1,'reason':'固定 noop 工程诊断，非模型决策。'}
                self.responses.put((epoch,choice))
            except Exception:self.responses.put((epoch,None))
        threading.Thread(target=request,daemon=True).start()

    def tick(self):
        with self.lock:
            while True:
                try:command=self.controls.get_nowait()
                except queue.Empty:break
                try:self.control(command)
                except ValueError:self.events.append({'type':'control_denied','tick':self.host.env._step})
            while True:
                try:epoch,choice=self.responses.get_nowait()
                except queue.Empty:break
                self.inflight=False
                if epoch!=self.epoch or self.mode!='agent':continue
                if choice is None:self.mode='paused';self.basis='调用失败，已暂停。';continue
                action=choice.get('action');repeat=choice.get('repeat',1)
                if action not in self.host.actions or type(repeat) is not int or not 1<=repeat<=4:
                    self.mode='paused';self.basis='动作协议拒绝，已暂停。';continue
                self.basis=str(choice.get('reason',''))[:400];self.pending=[action]*repeat
            if self.mode=='agent' and not self.host.done and not (self.skill_thread and self.skill_thread.is_alive()):
                if self.pending:self.step(self.pending.pop(0),'agent')
                elif not self.inflight:self.start_decision()
            self.publish()

def run_live(output,controls,stop,model=None,formal=False):
    runtime=Runtime(output,controls,model,formal)
    while not stop.wait(.1):runtime.tick()
