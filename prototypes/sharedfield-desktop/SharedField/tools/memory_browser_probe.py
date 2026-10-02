"""UI component probe, explicit in-process transport (not native network/CSP).
Real model substitute is labeled TEST FIXTURE; real HTTP is separately tested.
"""
from pathlib import Path
import sys,json,re,tempfile,threading,time
from urllib.parse import urlsplit,parse_qs
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from switchlab.memory.service import MemoryService
from switchlab.memory.http import ASSETS
from tests.test_memory_pipeline import provider_server

def run(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);checks=[];errors=[];clock=[time.time()]
 endpoint,et=provider_server()
 with tempfile.TemporaryDirectory() as t:
  s=MemoryService(t,clock=lambda:clock[0]);s.start_worker()
  def bridge(path,body):
   try:
    bits=urlsplit(path);p=bits.path;q=parse_qs(bits.query);one=lambda k,d='':q.get(k,[d])[0]
    with s.lock:
     if p=='/api/state':r=s.view()
     elif p=='/api/chat':r={'source':s.submit(body['text'])['id']}
     elif p=='/api/options':r=s.set_options(body)
     elif p=='/api/memory-settings':r=s.set_memory_settings(body)
     elif p=='/api/config':r=s.configure(body['config'],body.get('key'),body.get('clear_key',False))
     elif p=='/api/source':r=s.store.observation(one('id'))
     elif p=='/api/search':r=s.store.search(one('q'),offset=int(one('offset','0')))
     elif p=='/api/history':r=s.store.recent(limit=40,offset=int(one('offset','0')))
     elif p=='/api/commitments':r=s.store.commitments(offset=int(one('offset','0')),include_closed=one('closed')=='1')
     elif p=='/api/versions':r={'items':s.store.versions(one('id'))}
     elif p=='/api/context':r=s.last_context or {}
     elif p=='/api/commitment':r=s.edit_commitment(body)
     elif p=='/api/background':s.start_background();r={'ok':True}
     elif p=='/api/pause':s.pause();r={'ok':True}
     elif p=='/api/auto':s.start_auto(body['steps']);r={'ok':True}
     elif p=='/api/advance':s.request_step();r={'ok':True}
     elif p=='/api/world':s.world_command(body['kind'],body.get('payload',{}));r={'ok':True}
     elif p=='/api/feedback':r=s.give_feedback(body['contact'],body['outcome'],body['explanation'])
     elif p=='/api/forget':r=s.forget(body['source_ids'],body.get('confirmed',False))
     elif p=='/api/backup':r=s.backup()
     elif p=='/api/export':r=s.store.export()
     elif p=='/api/import':r=s.import_checkpoint(body['checkpoint'],body.get('archive_current',False))
     elif p=='/api/grant':r=s.grant_calls(body['count'])
     elif p=='/api/replay':r=s._commit('replay',{})['result']
     elif p=='/api/reindex':s.store.reindex();r={'ok':True}
     elif p=='/api/manual':s.accept_manual(body['request_id'],body['text']);r={'ok':True}
     elif p=='/api/resume-turn':s.resume_turn(body['source']);r={'ok':True}
     else:raise ValueError('explicit test transport missing '+p)
    return {'status':200,'data':r}
   except (ValueError,TypeError,KeyError) as e:return {'status':400,'data':{'error':str(e)}}
  try:
   with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True);page=b.new_page(viewport={'width':1440,'height':1080})
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept(d.default_value) if d.type=='prompt' else d.accept())
    page.expose_function('memoryTestTransport',bridge)
    html=(ASSETS/'index.html').read_text().replace('__TOKEN__','EXPLICIT_COMPONENT_TEST_TOKEN')
    html=re.sub(r'<link rel="stylesheet"[^>]*>|<script src="/app.js"></script>','',html)
    page.set_content(html);page.add_style_tag(content=(ASSETS/'style.css').read_text())
    page.evaluate('''()=>{window.fetch=async(path,opt={})=>{const r=await window.memoryTestTransport(path,opt.body?JSON.parse(opt.body):null);return {ok:r.status<400,status:r.status,json:async()=>r.data,blob:async()=>new Blob([JSON.stringify(r.data)],{type:'application/json'})};};}''')
    page.add_script_tag(content=(ASSETS/'app.js').read_text())
    def check(name,expr):
     print(name,flush=True)
     try:page.wait_for_function(expr,timeout=15000)
     except Exception:
      page.screenshot(path=str(out/'failure.png'),full_page=True);(out/'failure_ui.txt').write_text(page.locator('body').inner_text());(out/'failure_state.json').write_text(json.dumps(s.view(),ensure_ascii=False,indent=2));raise
     checks.append({'name':name,'passed':True})
    check('paused initial life; no fabricated earlier memories','state && state.messages.length===0 && !state.runtime.background')
    page.fill('#messageInput','普通聊天，不假造已理解的约定');page.click('#sendButton');check('local message saved, local mode honestly labeled','state.messages.length===2 && state.messages[1].text.includes("未连接")')
    page.click('#configButton');page.select_option('#languageMode','api');page.fill('#baseUrl',f'http://127.0.0.1:{endpoint.server_port}/v1');page.fill('#modelId','MEMORY_TEST_FIXTURE');page.fill('#timezone','UTC+08:00');page.click('#configForm button[type=submit]')
    check('real configuration path and explicit timezone','state.runtime.options.language_mode==="api" && state.memory_settings.timezone==="UTC+08:00"')
    page.fill('#messageInput','测试夹具：1分钟后一起看星空');page.click('#sendButton');check('two-phase chat creates actual persistent commitment','state.commitments.total===1 && state.messages.at(-1).text.includes("TEST FIXTURE") && !state.runtime.busy')
    page.screenshot(path=str(out/'v06_desktop.png'),full_page=True)
    page.click('#allCommitmentsButton');check('complete collection query UI','document.getElementById("memoryDialog").open && document.querySelectorAll("#memoryResults .commit-card").length===1')
    page.click('#memoryResults .commit-actions button:first-child');check('original source readback not summary','document.getElementById("sourceDialog").open && document.getElementById("sourceText").textContent.includes("1分钟后一起看星空")')
    page.click('[data-close=sourceDialog]');page.click('[data-close=memoryDialog]')
    page.click('#backgroundButton');clock[0]+=65;check('future memory causes contact without new chat; virtual clock in UI probe','state.messages.at(-1).text.includes("现在方便开始吗")')
    page.locator('#messages .message').last.get_by_role('button',name='这次不方便').click();check('actual contact outcome becomes one learning sample','state.learning.unique_outcomes===1')
    page.click('#pauseButton');page.click('#memoryButton');page.click('#freezeButton');check('freeze control affects learning state','state.learning.enabled===false')
    page.click('#replayButton');check('frozen replay does not create evidence','state.learning.unique_outcomes===1')
    page.fill('#searchInput','星空');page.click('#searchForm button');check('longterm source search in maintenance','document.querySelectorAll("#memoryResults .memory-row").length>=1')
    page.click('[data-close=memoryDialog]');page.click('#worldButton');check('same-life optional shared environment renders','document.querySelectorAll("#worldMap .room").length===3')
    page.click('#worldSurvey');check('actual world outcome increments only physical step','state.world.world.tick===1')
    page.click('#worldTogether');check('joint mode changes underlying mind','state.world.cognition.activity.mode==="together"')
    page.click('#worldWait');check('wait does not erase commitments','state.world.cognition.activity.mode==="wait" && state.commitments.total===1')
    page.click('[data-close=worldDialog]')
    page.click('#addCommitmentButton');page.fill('#commitmentTitle','以后一起读书');page.fill('#commitmentQuote','以后一起读书，日期还没确定');page.click('#commitmentForm button[type=submit]');check('untimed agreement saved without fabricated date','state.commitments.total===2 && state.commitments.items.some(c=>c.title==="以后一起读书" && c.due_at===null)')
    page.locator('#commitments .commit-card').filter(has_text='以后一起读书').get_by_role('button',name='取消',exact=True).click();check('cancel updates effective state','state.commitments.total===1')
    page.click('#backupButton');check('explicit local backup confirmation','document.getElementById("toast").textContent.includes("已建立备份")')
    page.click('#configButton');page.select_option('#languageMode','manual');page.click('#configForm button[type=submit]');check('manual mode explicit','state.runtime.options.language_mode==="manual"')
    page.fill('#messageInput','记忆交换测试');page.click('#sendButton');check('manual interpretation request contains real memory','state.runtime.manual_request && state.runtime.manual_request.phase==="interpret"')
    page.click('#manualButton');page.fill('#manualResponse',json.dumps({'claims':[],'commitments':[]}));page.click('#submitManualButton');check('manual expression follows committed interpretation','state.runtime.manual_request && state.runtime.manual_request.phase==="express"')
    page.click('#manualButton');page.fill('#manualResponse',json.dumps({'speech':'【TEST FIXTURE】读回有来源的经历。','evidence_ids':[]}));page.click('#submitManualButton');check('manual expression persisted','state.messages.at(-1).text.includes("读回有来源")')
    with page.expect_download() as download:page.click('#exportButton')
    saved=out/'synthetic_browser_checkpoint.json';download.value.save_as(str(saved));checks.append({'name':'download actual JSON export','passed':json.loads(saved.read_text())['schema']=='sharedfield.memory.v6'})
    # Mutate state after export: merely seeing an already-paused old message
    # cannot prove import succeeded. Require success receipt AND state rollback.
    page.click('#pauseButton');s.submit('TEST TEMP IMPORT MARKER');s.run_once()
    page.set_input_files('#importFile',str(saved))
    check('same-version export actually imported with success receipt','document.getElementById("toast").textContent.includes("接续完成") && !state.runtime.background && !state.messages.some(m=>m.text.includes("TEST TEMP IMPORT MARKER"))')
    assert s.store.projection_digest()==json.loads(saved.read_text())['projection_sha256']
    checks.append({'name':'imported projection equals exported projection, not stale UI','passed':True})
    page.wait_for_timeout(1200)
    page.set_viewport_size({'width':390,'height':844});check('mobile no horizontal overflow','document.documentElement.scrollWidth<=window.innerWidth')
    page.screenshot(path=str(out/'v06_mobile.png'),full_page=True)
    assert not errors,errors
    checks.append({'name':'no JavaScript errors','passed':True});b.close()
  finally:s.close();endpoint.shutdown();endpoint.server_close();et.join(2)
 result={'checks':checks,'js_errors':errors,'passed':all(x['passed'] for x in checks),'transport':'explicit in-process UI fixture; native networking and CSP NOT tested','language':'TEST FIXTURE; no real-model semantic claim','clock':'injected time for due-event UI check; actual wall-clock worker separately tested'}
 (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else 'evidence_v06/browser')
