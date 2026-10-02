"""Developer-only UI probe. Requires Playwright and Chromium, not runtime dependencies.

Managed Chromium blocks native loopback here. TestTransport below is explicitly
an in-process service fixture, NOT a bypass or browser-to-HTTP/network test.
The separate unittest suite tests both actual application and provider HTTP.
All language output in this probe is named TEST_FIXTURE.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from switchlab.studio.adaptive_service import AdaptiveService
from switchlab.studio.http import ASSETS
from tests.test_adaptive_service import FixtureProvider
from tests.adaptive_fixtures import proposal

class DemoFixture(FixtureProvider):
    def complete(self,messages):
        data=json.loads(messages[-1]['content']);self.calls.append(data['phase'])
        if data['phase']=='analyse':
            raw=data.get('selected_input',{}).get('content','')
            raw=raw if isinstance(raw,str) else json.dumps(raw,ensure_ascii=False)
            packet=proposal(data['source_event'],'草稿' in raw)
            if isinstance(data.get('selected_input',{}).get('content'),str) and ('红色' in raw or '蓝色' in raw):
                value='蓝色' if '蓝色' in raw else '红色'
                packet['claims']=[{'holder':'user','subject':'用户','relation':'颜色偏好','value':value,
                    'source':data['source_event'],'quote':raw,'confidence':.7}]
            packet['summary']='TEST_FIXTURE：界面集成检查，不是真实模型表现'
        elif data['phase']=='express':
            packet={'decision_id':data['local_decision']['id'],'speech':'【TEST_FIXTURE · 非真实模型】已表达本地选择的候选；本条仅用于界面测试。'}
        else:packet={'content':'# TEST_FIXTURE · 实际写入的测试草稿\n\n保留约束并比较两个本地方案。不是实际语言能力成绩。'}
        return {'packet':packet,'usage':{'input_tokens':10,'output_tokens':20},'model':'TEST_FIXTURE'}

def run(out,chromium):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    records=[];errors=[]
    with tempfile.TemporaryDirectory() as directory:
        provider=DemoFixture();s=AdaptiveService(directory,provider=provider);s.start_worker()
        def bridge(path,body):
            try:
                if path=='/api/state':result=s.view()
                elif path=='/api/chat':s.submit(body['text']);result={'ok':True}
                elif path=='/api/command':s.command(body['kind'],body.get('payload',{}));result={'ok':True}
                elif path=='/api/auto':s.start_auto(body['steps']);result={'ok':True}
                elif path=='/api/advance':s.request_step();result={'ok':True}
                elif path=='/api/pause':s.pause();result={'ok':True}
                elif path=='/api/manual':s.accept_manual(body['request_id'],body['text']);result={'ok':True}
                else:raise ValueError('TestTransport does not implement '+path)
                return {'status':200,'data':result}
            except (ValueError,TypeError,KeyError) as e:return {'status':400,'data':{'error':str(e)}}
        try:
            with sync_playwright() as p:
                b=p.chromium.launch(executable_path=chromium,headless=True)
                page=b.new_page(viewport={'width':1440,'height':1080},device_scale_factor=1)
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('dialog',lambda d:d.accept())
                page.expose_function('testServiceTransport',bridge)
                html=(ASSETS/'index.html').read_text().replace('__TOKEN__','EXPLICIT_UI_TEST_TOKEN')
                html=re.sub(r'<link rel="stylesheet"[^>]*>|<script src="/app.js" defer></script>','',html)
                page.set_content(html)
                page.add_style_tag(content=(ASSETS/'style.css').read_text())
                page.evaluate("""window.fetch = async (path,opt={}) => {
                    const r=await window.testServiceTransport(path,opt.body?JSON.parse(opt.body):null);
                    return {ok:r.status<400,status:r.status,json:async()=>r.data};
                };""")
                page.add_script_tag(content=(ASSETS/'app.js').read_text())
                page.wait_for_selector('#cognitiveStats .stat')
                def wait(expr):
                    try:page.wait_for_function(expr,timeout=12000)
                    except Exception:
                        (out/'failure_state.json').write_text(json.dumps(s.view(),ensure_ascii=False,indent=2),encoding='utf-8')
                        (out/'failure_ui.txt').write_text(page.locator('body').inner_text(),encoding='utf-8')
                        print('FAILED WAIT',expr,'provider phases',provider.calls,'errors',errors,flush=True)
                        raise
                def check(name,fn):fn();records.append({'name':name,'passed':True})
                def send(text,count):
                    page.fill('#messageInput',text);page.click('#sendBtn')
                    wait(f"state.cognition.decisions.filter(d=>d.status==='expressed').length >= {count} && !state.runtime.busy")
                    wait('!polling');page.evaluate('refresh()')
                check('default cognitive panel and zero fresh samples',lambda:(
                    page.locator('#cognitionPanel').wait_for(state='visible'),
                    wait('state.cognition.learner.external_samples===0')))
                send('我喜欢红色，不要创建任务。',1)
                check('chat uses adaptive selection but no fake physical tick',lambda:wait('state.cognition.observations===1 && state.lab.observation.tick===0'))
                send('现在另一个情境我喜欢蓝色。',2)
                check('next real input trains local parameters',lambda:wait('state.cognition.learner.updates>0'))
                page.click('[data-tab="claims"]')
                check('grounded source-separated claims rendered',lambda:wait('document.querySelectorAll("#claimsList blockquote").length===2'))
                page.click('[data-tab="cognition"]');page.click('#thinkBtn')
                check('internal conflict computation without new external observation',lambda:wait('state.cognition.internal_steps>0 && state.cognition.observations===2'))
                page.click('#openOutcomeBtn');page.select_option('#outcomeTask','1');page.select_option('#outcomeConstraint','1');page.fill('#outcomeNote','TEST_FIXTURE：人工报告标签，不是真值');page.click('#saveOutcomeBtn')
                check('explicit outcome persists and trains',lambda:wait('state.cognition.decisions.at(-1).outcome!==null'))
                page.click('#openOutcomeBtn');page.click('#withdrawOutcomeBtn')
                check('erroneous label retracted with actual rebuild',lambda:wait('state.cognition.learner.withdrawn===1'))
                page.click('#learningToggle');wait('state.cognition.learner.enabled===false')
                before=s.core.learner.net.weight_digest()
                send('新的实际输入，但当前冻结数值学习。',3)
                if before!=s.core.learner.net.weight_digest():raise AssertionError('freeze changed weights')
                records.append({'name':'freeze retains messages but not learned weights','passed':True})
                page.click('#learningToggle');wait('state.cognition.learner.enabled===true')
                page.select_option('#selectionMode','similarity');check('predictor mode persisted',lambda:wait("state.cognition.mode==='similarity'"))
                page.click('[data-tab="world"]');page.click('[data-lab="calibrate"]')
                check('actual lab action enters same learner and physical clock',lambda:wait('state.lab.observation.tick===1'))
                page.click('[data-tab="goals"]')
                send('做一个可验收的草稿，保留资源约束。',4)
                page.click('#autoBtn');wait('state.artifacts.length>=1 && !state.runtime.busy')
                page.click('#pauseBtn');wait('state.runtime.auto_remaining===0')
                page.locator('#artifactList button').first.click()
                page.fill('#feedbackText','TEST_FIXTURE：遗漏一个约束，需要修订')
                page.click('[data-feedback="criteria_failed"]');page.click('[data-close="artifactDialog"]')
                page.click('#autoBtn');wait('state.artifacts.length>=2 && !state.runtime.busy')
                page.click('#pauseBtn');wait('state.runtime.auto_remaining===0')
                check('actual goal draft feedback revision retained',lambda:wait('state.artifacts.length===2 && state.cognition.learner.updates>0'))
                page.click('#settingsBtn');check('model connection and protocol check UI present',lambda:page.locator('#protocolCheckBtn').wait_for(state='visible'));page.click('[data-close="settingsDialog"]')
                page.click('[data-tab="cognition"]');page.evaluate('refresh()');page.wait_for_timeout(300)
                page.screenshot(path=str(out/'desktop.png'),full_page=True)
                page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(200)
                overflow=page.evaluate('document.documentElement.scrollWidth>window.innerWidth')
                if overflow:raise AssertionError('mobile horizontal overflow')
                records.append({'name':'390px mobile no horizontal overflow','passed':True})
                page.screenshot(path=str(out/'mobile.png'),full_page=True)
                if errors:raise AssertionError(errors)
                records.append({'name':'no JavaScript page errors','passed':True})
                b.close()
        finally:s.close()
    result={'checks':records,'count':len(records),'page_errors':errors,
        'language':'explicit TEST_FIXTURE; no real language model tested',
        'transport':'in-process TestTransport; not native browser HTTP',
        'native_browser_http':'attempted separately: ERR_BLOCKED_BY_ADMINISTRATOR; policy unmodified',
        'csp_execution':'not validated by set_content test; real HTTP response headers separately tested'}
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='evidence_v03/current/browser');parser.add_argument('--chromium',default='/usr/bin/chromium')
    args=parser.parse_args();run(args.out,args.chromium)
