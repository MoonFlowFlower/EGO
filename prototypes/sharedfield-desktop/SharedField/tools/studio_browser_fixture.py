"""Developer-only UI fixture. Playwright is NOT a runtime dependency.

Managed Chromium blocks direct loopback navigation. Browser HTML/JS is exercised
with an explicit fetch bridge to the actual loopback HTTP server via Python.
This does not test the native browser-to-HTTP networking, origin headers or CSP
execution. Those server boundaries have independent HTTP tests. Model outputs
in this test are explicitly authored fixtures, not a live provider evaluation.
"""
from pathlib import Path
import json
import re
import sys
import tempfile
import threading
import urllib.request
import urllib.error
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from switchlab.studio.service import Service
from switchlab.studio.http import StudioServer
from switchlab.runtime import save_json
from playwright.sync_api import sync_playwright


def main():
    out=ROOT/'evidence_v02';out.mkdir(exist_ok=True)
    class Progress(list):
        def append(self,x):super().append(x);print('CHECK:',x,flush=True)
    checks=Progress();errors=[]
    with tempfile.TemporaryDirectory() as d:
        service=Service(d);service.start_worker()
        server=StudioServer(service,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        origin=f'http://127.0.0.1:{server.server_port}'
        def bridge(url,options=None):
            options=options or {};headers=options.get('headers',{}).copy()
            if options.get('body') is not None:headers['Origin']=origin
            body=options.get('body');req=urllib.request.Request(origin+url,data=body.encode() if body is not None else None,headers=headers,method=options.get('method','GET'))
            try:
                with urllib.request.urlopen(req,timeout=15) as r:return {'status':r.status,'body':r.read().decode(),'type':r.headers.get('Content-Type','')}
            except urllib.error.HTTPError as e:return {'status':e.code,'body':e.read().decode(),'type':'application/json'}
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
                page=browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
                page.set_default_timeout(7000)
                page.on('pageerror',lambda e:(errors.append(str(e)),print('JS ERROR',str(e),flush=True)))
                page.expose_function('fixtureBridge',bridge)
                html=urllib.request.urlopen(origin).read().decode()
                html=re.sub(r'<link[^>]+stylesheet[^>]*>','',html)
                html=re.sub(r'<script[^>]+src[^>]*></script>','',html)
                page.set_content(html,wait_until='domcontentloaded')
                page.add_style_tag(content=(ROOT/'switchlab/studio/web/style.css').read_text())
                page.add_script_tag(content="window.fetch=async(url,options)=>{const r=await window.fixtureBridge(url,options||{});return new Response(r.body,{status:r.status,headers:{'Content-Type':r.type}});};")
                page.add_script_tag(content=(ROOT/'switchlab/studio/web/app.js').read_text())
                page.wait_for_function("document.querySelector('#eventCount').textContent==='0 个事件'")
                assert not errors,errors;checks.append('initial DOM, JS and actual HTTP-backed state render')
                page.click('#settingsBtn');page.wait_for_selector('#settingsDialog[open]')
                page.select_option('#preset','ollama');assert page.input_value('#baseUrl')=='http://127.0.0.1:11434/v1'
                page.select_option('#preset','manual');page.locator('#settingsForm button[type=submit]').click()
                page.wait_for_function("!document.querySelector('#settingsDialog').open")
                assert service.provider.config['mode']=='manual';checks.append('settings preset and actual persisted manual config')
                page.fill('#messageInput','我想做四人合作探索游戏，但不想做复杂动作。帮我比较低成本方向；先保留两个方案。')
                page.click('#sendBtn');page.wait_for_function("!document.querySelector('#manualBanner').hidden")
                page.click('#openManualBtn');assert '四人合作探索' in page.input_value('#manualPrompt')
                source=service.manual_request['source_event']
                proposal={'speech':'我会先比较搬运与协作解谜两个方向，把动作成本和探索体验作为取舍依据。任务已经记录，尚未生成方案。',
                          'memories':[{'kind':'preference','key':'制作约束','text':'四人合作探索，低动作制作成本。','basis':[source]}],
                          'goals':[{'title':'比较两个低动作成本的合作探索方向','reason':'依据你的制作约束，先缩小选择而不是扩张功能。','success':'有两个可比较方向，解释动作成本、探索体验和最小测试。','basis':[source],
                                    'steps':[{'tool':'draft','instruction':'给出两个方向的比较，保留条件与最小验证。'}]}],
                          'revisions':[]}
                page.fill('#manualResponse',json.dumps(proposal,ensure_ascii=False));page.click('#applyManualBtn')
                page.wait_for_function("document.querySelector('#goalCount').textContent==='1 个未结束'")
                assert len(service.core.state['goals'])==1;checks.append('chat -> manual language packet -> actual persistent goal and memory')
                page.click('#onceBtn');page.wait_for_function("!document.querySelector('#manualBanner').hidden")
                page.click('#openManualBtn')
                draft='# 两个低动作成本方向\n\n## 方向 A：合作搬运与路线探索\n把挑战放在路线选择、道具组合和队友配合。操作以移动、拾取、放下为主。\n\n## 方向 B：分工观察与机关解谜\n不同玩家获得不同线索，通过沟通找到路。避免依赖大量敌人动作。\n\n## 首轮验证\n先搭一个十分钟空间，检查玩家是否会主动讨论路线，而不是立刻制作大地图。\n\n这份内容是界面测试示例，尚未证明玩法效果。'
                page.fill('#manualResponse',json.dumps({'content':draft},ensure_ascii=False));page.click('#applyManualBtn')
                page.wait_for_function("document.querySelector('#artifactCount').textContent==='1 份'")
                page.locator('#artifactList button').first.click();page.wait_for_selector('#artifactDialog[open]')
                assert '方向 A' in page.inner_text('#artifactContent');checks.append('real draft stored and readable in artifact dialog')
                page.fill('#feedbackText','需要支持手柄操作，且不要强制语音沟通。')
                page.click('[data-feedback=criteria_failed]')
                page.wait_for_function("document.querySelector('#evaluationStatus').textContent.includes('已有一次验收')")
                assert page.locator('[data-feedback=criteria_failed]').is_disabled()
                page.click('[data-close=artifactDialog]');page.click('#onceBtn')
                page.wait_for_function("!document.querySelector('#manualBanner').hidden");page.click('#openManualBtn')
                assert '不要强制语音沟通' in page.input_value('#manualPrompt')
                assert service.core.state['strategy_stats']['outline']['beta']==2
                page.fill('#manualResponse',json.dumps({'content':draft+'\n\n## 根据你的反馈修订\n两种方案均提供手柄操作；沟通使用标记和可共享线索，不要求语音。'},ensure_ascii=False));page.click('#applyManualBtn')
                page.wait_for_function("document.querySelector('#artifactCount').textContent==='2 份'")
                checks.append('criterion feedback updates strategy, revision context and actual second artifact; repeated rating disabled')
                page.click('[data-tab=memory]');assert '制作约束' in page.inner_text('#memoryList')
                page.click('#adaptationToggle');page.wait_for_timeout(150);assert not service.core.state['adaptation']
                page.click('#consolidateBtn');page.wait_for_timeout(150);assert len(service.core.state['consolidations'])==1
                checks.append('memory view, adaptation ablation and reconstruction commands mutate actual state')
                page.click('[data-tab=world]');prior=service.core.lab.agent.model.snapshot()
                page.locator('#worldPanel summary').click();page.click('[data-intervene=damage_tool]');page.wait_for_timeout(150);assert service.core.lab.world.snapshot()['hidden'][2]==0
                assert prior==service.core.lab.agent.model.snapshot()
                page.click('[data-lab=calibrate]');page.wait_for_timeout(250);assert service.core.lab.world.observe()['tick']==1
                assert prior!=service.core.lab.agent.model.snapshot();checks.append('intervention is hidden; actual calibration produces learned belief update')
                page.click('#pauseBtn');page.wait_for_timeout(200);assert service.auto_remaining==0 and not service.manual_request
                checks.append('pause stops authorized work and clears outstanding manual exchange')
                page.click('[data-tab=goals]');page.wait_for_timeout(350)
                page.screenshot(path=str(out/'studio_preview.png'),full_page=True)
                # Deliberate injection string must remain text. This is fixture data, never rendered as HTML.
                service.submit('<img src=x onerror="window.fixtureInjected=1">');page.wait_for_timeout(1200)
                assert not page.evaluate('window.fixtureInjected===1');assert page.locator('#chatLog img').count()==0
                checks.append('untrusted message markup does not execute')
                page.click('#pauseBtn');page.wait_for_timeout(150);page.click('[data-tab=goals]')
                page.screenshot(path=str(out/'studio_desktop.png'),full_page=True)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(150)
                page.screenshot(path=str(out/'studio_mobile.png'),full_page=True)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                checks.append('1440px and 390px layouts have no horizontal overflow')
                assert not errors,errors;checks.append('no JavaScript page errors')
                browser.close()
        finally:
            server.shutdown();server.server_close();service.close()
    result={'successful':True,'count':len(checks),'checks':checks,'page_errors':errors,
            'transport':'browser fetch fixture -> Python HTTP client -> actual local server',
            'native_browser_http':'blocked by administrator; NOT verified',
            'csp_in_browser':'NOT verified by this fixture; response headers tested separately',
            'language_outputs':'authored test fixtures, not live provider', 'windows_tested':False}
    save_json(out/'browser_test.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
