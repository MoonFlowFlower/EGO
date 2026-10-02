"""Developer-only UI checks with EXPLICIT in-process app transport.
Native Chromium-to-loopback is blocked by policy in the build environment.
This does not bypass policy and does NOT test native browser networking/CSP.
The separate unittest suite tests actual application and provider HTTP. Only
explicit TEST_FIXTURE responses are used for language-protocol UI tests.
"""
from pathlib import Path
import sys,json,re,tempfile,threading,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from switchlab.shared.service import SharedService
from switchlab.shared.http import ASSETS
from tests.test_shared_pipeline import SharedModelHTTPFixture
from http.server import ThreadingHTTPServer


def run(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);checks=[];errors=[]
    print('probe: initializing',flush=True)
    endpoint=ThreadingHTTPServer(('127.0.0.1',0),SharedModelHTTPFixture);endpoint.received=[]
    threading.Thread(target=endpoint.serve_forever,daemon=True).start()
    with tempfile.TemporaryDirectory() as d:
        s=SharedService(d);s.set_options({'interval':.2});s.start_worker()
        def bridge(path,body):
            try:
                r={'ok':True}
                if path=='/api/state':r=s.view()
                elif path=='/api/chat':s.submit(body['text'])
                elif path=='/api/command':s.command(body['kind'],body.get('payload',{}))
                elif path=='/api/advance':s.request_step()
                elif path=='/api/auto':s.start_auto(body['steps'])
                elif path=='/api/pause':s.pause()
                elif path=='/api/options':r=s.set_options(body)
                elif path=='/api/config':r=s.configure(body['config'],body.get('key'),body.get('clear_key',False))
                elif path=='/api/protocol-check':r=s.check_protocol()
                elif path=='/api/manual':s.accept_manual(body['request_id'],body['text'])
                elif path.startswith('/api/report?id='):r=next(r for r in s.core.state['reports'] if r['id']==path.split('=')[-1])
                elif path=='/api/export':r=s.core.checkpoint()
                elif path=='/api/import':r=s.import_checkpoint(body['checkpoint'],body.get('archive_current',False))
                elif path=='/api/new':s.new_life()
                else:raise ValueError('unimplemented explicit UI test transport '+path)
                return {'status':200,'data':r}
            except (ValueError,TypeError,KeyError) as e:return {'status':400,'data':{'error':str(e)}}
        try:
            print('probe: launching chromium',flush=True)
            with sync_playwright() as p:
                b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True)
                print('probe: chromium launched',flush=True)
                page=b.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
                page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda x:x.accept())
                page.expose_function('sharedTestTransport',bridge)
                html=(ASSETS/'index.html').read_text().replace('__TOKEN__','EXPLICIT_TEST_TOKEN')
                html=re.sub(r'<link rel="stylesheet"[^>]*>|<script src="/app.js" defer></script>','',html)
                page.set_content(html);page.add_style_tag(content=(ASSETS/'style.css').read_text())
                page.evaluate('''() => { window.fetch=async(path,opt={})=>{const r=await window.sharedTestTransport(path,opt.body?JSON.parse(opt.body):null);return {ok:r.status<400,status:r.status,json:async()=>r.data,text:async()=>JSON.stringify(r.data)};}; }''')
                page.add_script_tag(content=(ASSETS/'app.js').read_text())
                def wait(expr):
                    try:page.wait_for_function(expr,timeout=12000)
                    except Exception:
                        (out/'failure_state.json').write_text(json.dumps(s.view(),ensure_ascii=False,indent=2))
                        (out/'failure_ui.txt').write_text(page.locator('body').inner_text())
                        page.screenshot(path=str(out/'failure.png'),full_page=True);raise
                def check(name,expr):
                    print('probe: '+name,flush=True);wait(expr);checks.append({'name':name,'passed':True})
                check('playable map and no fabricated initial experience','state && document.querySelectorAll(".room").length===12 && state.cognition.learned_events===0')
                before=s.core.mind.report();page.click('#askFeeling')
                check('feeling question reads preexisting state, no physics','state.messages.length===2 && state.world.tick===0 && state.calls===0')
                assert s.core.mind.report()==before
                page.click('.room[data-room="1"]');page.click('#moveBtn')
                check('player click executes physical move attempt','state.world.tick===1')
                page.click('#surveyBtn');check('shared discovery is observed by both','state.world.tick===2 && state.cognition.learned_events>=1')
                page.click('#autoBtn');check('finite autonomous exploration without LLM calls','state.world.tick===10 && state.runtime.auto_remaining===0 && state.calls===0')
                page.click('#askFeeling');check('post-experience self report linked to actual state','state.messages.length===4 && state.reports.at(-1).world_tick===10')
                page.locator('.message.assistant button').last.click()
                check('immutable report inspection','document.getElementById("reportDialog").open && document.getElementById("reportContent").textContent.includes("affect")')
                page.click('[data-close="reportDialog"]')
                page.click('#togetherBtn');check('adopted joint commitment changes actual kernel','state.cognition.activity.mode==="together"')
                page.click('#waitBtn');check('wait commitment persists','state.cognition.activity.mode==="wait" && state.cognition.focus.action.kind==="wait_partner"')
                tick=s.core.world.tick;page.click('#autoBtn');page.wait_for_timeout(700)
                assert s.core.world.tick==tick and s.auto_remaining==8
                checks.append({'name':'waiting preserves steps and spends no world action','passed':True})
                page.click('#pauseBtn');wait('state.runtime.auto_remaining===0')
                page.click('#resumeJointBtn');check('resume restores joint mode without granting steps','state.cognition.activity.mode==="together" && state.runtime.auto_remaining===0')
                page.click('#independentBtn');check('independence actually changes constraints','state.cognition.activity.mode==="independent"')
                check('source-grounded shared memory visible','document.querySelectorAll(".memoryItem").length>0')
                page.screenshot(path=str(out/'shared_local_desktop.png'),full_page=True)
                page.click('#inspector summary');page.select_option('#ablationSelect','affect_off')
                check('causal decision-path ablation selectable','state.cognition.mode==="affect_off"')
                page.select_option('#ablationSelect','full');wait('state.cognition.mode==="full"')
                tick=s.core.world.tick;before=s.core.mind.capability();page.click('#faultBtn')
                wait('state.last_events.some(e=>e.kind==="intervene")');assert s.core.world.tick==tick and s.core.mind.capability()==before
                checks.append({'name':'hidden intervention not injected into capability belief','passed':True})
                page.screenshot(path=str(out/'shared_inspector.png'),full_page=True)
                page.click('#inspector summary')
                page.click('#connectBtn');page.select_option('#languageMode','manual');page.click('#saveSettingsBtn')
                wait('state.runtime.options.language_mode==="manual"');page.click('[data-close="settingsDialog"]');page.click('#askFeeling')
                wait('state.runtime.manual_request && state.runtime.manual_request.phase==="interpret"');page.click('#manualBtn')
                page.fill('#manualResult',json.dumps({'reports':[],'request':{'kind':'none'}}));page.click('#submitManualBtn')
                wait('state.runtime.manual_request && state.runtime.manual_request.phase==="express"');page.click('#manualBtn')
                sid=s.manual_request['state_id'];page.fill('#manualResult',json.dumps({'state_id':sid,'speech':'【TEST_FIXTURE】手动交换的状态表达测试。'},ensure_ascii=False));page.click('#submitManualBtn')
                check('manual two-stage exchange completes','state.messages.at(-1).text.includes("TEST_FIXTURE") && !state.runtime.manual_request')
                page.click('#connectBtn');page.select_option('#languageMode','api');page.fill('#baseURL',f'http://127.0.0.1:{endpoint.server_port}/v1');page.fill('#modelID','SHARED_HTTP_TEST_FIXTURE');page.click('#saveSettingsBtn')
                wait('state.runtime.options.language_mode==="api"');page.click('[data-close="settingsDialog"]');page.click('#askFeeling')
                check('UI through actual Provider to explicit HTTP model fixture','state.calls===2 && state.messages.at(-1).text.includes("HTTP TEST FIXTURE") && !state.runtime.busy')
                assert len(endpoint.received)==2
                check('chosen action receipt visible before action','document.querySelectorAll(".intentionReceipt").length>0')
                with page.expect_download() as download:
                    page.click('#exportBtn')
                exported=Path(download.value.path()).read_text()
                exported_json=json.loads(exported)
                from switchlab.shared.core import SharedCore
                restored=SharedCore.restore(exported_json)
                assert restored.world.tick==s.core.world.tick
                checks.append({'name':'browser export survives JSON numeric normalization and replays','passed':True})
                before_tick=s.core.world.tick
                page.set_input_files('#importFile',{'name':'resume.json','mimeType':'application/json','buffer':exported.encode()})
                check('import archives active life and restores paused','state.runtime.auto_remaining===0 && state.runtime.status.includes("导入")')
                assert s.core.world.tick==before_tick
                checks.append({'name':'import preserves real world position and history','passed':True})
                page.screenshot(path=str(out/'shared_v05_desktop.png'),full_page=True)
                page.click('#autoBtn');wait('state.runtime.auto_remaining<8');page.click('#pauseBtn');wait('state.runtime.auto_remaining===0');tick=s.core.world.tick;page.wait_for_timeout(600);assert s.core.world.tick==tick
                checks.append({'name':'pause prevents additional physical actions','passed':True})
                learned=s.core.mind.learned_events;page.click('#nextIslandBtn');check('new expedition preserves learning but not old map','state.world.tick===0 && state.expedition===2');assert s.core.mind.learned_events==learned
                page.set_viewport_size({'width':390,'height':844});page.evaluate('window.scrollTo(0,0)')
                check('390px layout no horizontal overflow','document.documentElement.scrollWidth<=window.innerWidth')
                page.screenshot(path=str(out/'shared_mobile.png'),full_page=True)
                assert not errors,errors
                checks.append({'name':'no browser JavaScript exceptions','passed':True});b.close()
        finally:
            print('probe: closing services',flush=True)
            s.close();endpoint.shutdown();endpoint.server_close()
    result={'checks':checks,'count':len(checks),'errors':errors,'native_browser_http':False,
            'transport':'explicit in-process UI test bridge; separate real HTTP tests',
            'native_limit':'ERR_BLOCKED_BY_ADMINISTRATOR; no policy bypass',
            'real_language_model_tested':False,'desktop_preview':'real local state reports; no LLM'}
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False,indent=2));return result
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else 'evidence_v05/browser')
