import json,queue,sys,threading,time,urllib.request,urllib.error
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.live_runner import Runtime
from growthlab.observatory import Mailbox,make_server
from growthlab.records import EVIDENCE,write_json,telemetry
from probe_p8 import hashes

def main():
    start=time.perf_counter();checks={};samples=[telemetry()];out=queue.Queue(maxsize=1);controls=queue.Queue(maxsize=16)
    rt=Runtime(out,controls);box=Mailbox(out)
    original=rt.host.last_frame.copy();rng=hashes(rt.host.env)
    saved_render=rt.host.env.render
    rt.host.env.render=lambda *args:(_ for _ in ()).throw(AssertionError('observer_render_forbidden'))
    for _ in range(100):rt.publish(force=True)
    checks['publish_never_renders']=True
    checks['publish_does_not_change_world_or_rng']=hashes(rt.host.env)==rng
    snap=box.read();snap['observation']['needs']['health']=999;snap['owner_canary']='OWNER_CANARY'
    checks['snapshot_copy_not_live']=rt.host.observe()['needs']['health']==9 and not hasattr(box,'host')
    checks['backpressure_drops_frames']=rt.dropped>=99
    rt.host.env.render=saved_render
    rt.pending=['noop']*4;rt.control({'mode':'human'})
    checks['takeover_clears_macro']=not rt.pending
    rt.control({'mode':'agent'});rt.start_skill('while True:\n observe()')
    rt.control({'mode':'human'});rt.skill_thread.join(3)
    checks['takeover_cancels_skill']=not rt.skill_thread.is_alive() and rt.skill_result['status']=='cancelled'
    entered=threading.Event();release=threading.Event();captured=[]
    class Delayed:
        def decide(self,messages):
            captured.append(messages);entered.set()
            if len(captured)==1:release.wait(3)
            return '{"action":"noop","repeat":4,"reason":"fixture"}',{}
    race=Runtime(queue.Queue(maxsize=1),queue.Queue(),Delayed());race.start_decision();entered.wait(2)
    race.control({'mode':'human'});release.set()
    deadline=time.perf_counter()+2
    while race.responses.empty() and time.perf_counter()<deadline:time.sleep(.005)
    race.tick();checks['stale_response_zero_actions']=race.host.env._step==0 and not race.pending
    race.control({'action':'noop'});race.control({'mode':'agent'});race.tick()
    deadline=time.perf_counter()+2
    while len(captured)<2 and time.perf_counter()<deadline:time.sleep(.005)
    checks['handoff_fresh_observation']=json.loads(captured[1][1]['content'])['observation']['tick']==1
    checks['owner_canary_absent_policy']='OWNER_CANARY' not in json.dumps(captured)
    for formal,port in [(False,8767),(True,8768)]:
        q=queue.Queue(maxsize=16);server=make_server(box,q,formal,port);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        origin=f'http://127.0.0.1:{port}'
        def post(body,token=None,source=None):
            req=urllib.request.Request(origin+'/api/control',data=json.dumps(body).encode(),headers={'Origin':source or origin,'X-Control':token or server.session_token})
            try:
                with urllib.request.urlopen(req,timeout=2) as r:return r.status
            except urllib.error.HTTPError as e:return e.code
        if formal:
            checks['formal_server_rejects_control']=all(post(x)==403 for x in ({'mode':'human'},{'mode':'agent'},{'action':'noop'},{'chat':'hint'},{'code':'act("noop")'}))
            checks['formal_queue_empty']=q.empty()
        else:
            checks['bad_origin_rejected']=post({'mode':'human'},source='https://elsewhere.invalid')==403
            checks['bad_token_rejected']=post({'mode':'human'},token='wrong')==403
            checks['valid_control_queued']=post({'mode':'human'})==200 and q.get(timeout=1)=={'mode':'human'}
            checks['unknown_channel_denied']=post({'chat':'OWNER_CANARY'})==400
        checks['loopback_binding_'+str(formal)]=server.server_address[0]=='127.0.0.1'
        server.shutdown();server.server_close();thread.join(2)
    samples.append(telemetry())
    result={'seconds':time.perf_counter()-start,'checks':checks,'copy_publish_mean_ms':sum(rt.publish_s)/len(rt.publish_s)*1000,
        'copy_publish_max_ms':max(rt.publish_s)*1000,'dropped_frames':rt.dropped,'telemetry':samples,
        'scope':'copied step frames; closed-language skill cancellation; delayed transport fixture, not a real cancelled cloud request'}
    write_json(EVIDENCE/'p10_v03.json',result);assert all(checks.values()),checks;print(json.dumps(result,indent=2))
if __name__=='__main__':main()
