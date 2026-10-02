"""Optional developer-only frontend fixture (Playwright not a runtime dependency).

This environment's managed Chromium rejects direct loopback navigation with
ERR_BLOCKED_BY_ADMINISTRATOR. Do not change browser policy. Test DOM/JS against
an in-process transport fixture instead; real HTTP security/commands are separately
covered by unittest. This does NOT certify a complete browser-to-HTTP deployment.
"""
from pathlib import Path
import json
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from playwright.sync_api import sync_playwright
from switchlab.runtime import Session,save_json
from switchlab.world import Config
from switchlab.agent import AgentConfig


def main():
    holder={'session':Session(Config(seed=41,horizon=96),AgentConfig())}
    def bridge(url,body):
        s=holder['session']
        if url=='/api/state':return s.public_view()
        if url!='/api/command':raise ValueError('fixture endpoint not supported')
        data=json.loads(body or '{}');command=data['command']
        if command=='step':
            for _ in range(min(data.get('count',1),s.world.config.horizon-s.world.observe()['tick'])):s.step()
        elif command=='compute':s.compute()
        elif command=='replay':s.replay_memory()
        elif command=='intervene':s.intervene(data['kind'])
        elif command=='reset':holder['session']=Session(Config(data['seed'],data['horizon'],data['scenario']),AgentConfig(policy=data['policy'],planner=data['planner']))
        else:raise ValueError('unknown fixture command')
        return holder['session'].public_view()
    checks=[];errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1080},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.expose_function('fixtureBridge',bridge)
        html=(ROOT/'switchlab/web/index.html').read_text().replace('__TOKEN__','fixture-token')
        html=re.sub(r'<link[^>]+stylesheet[^>]*>','',html)
        html=re.sub(r'<script[^>]+src[^>]*></script>','',html)
        page.set_content(html,wait_until='domcontentloaded')
        page.add_style_tag(content=(ROOT/'switchlab/web/style.css').read_text())
        page.add_script_tag(content="window.fetch=async(url,options)=>({ok:true,json:async()=>await window.fixtureBridge(url,options?.body||null)});")
        page.add_script_tag(content=(ROOT/'switchlab/web/app.js').read_text())
        page.wait_for_function("document.querySelector('#tick').textContent === '0 / 96'")
        checks.append('DOM loads assets and reads in-process actual Session state')
        page.click('#think');page.wait_for_function("document.querySelector('#status').textContent.includes('已思考')")
        assert holder['session'].world.observe()['tick']==0
        page.click('#step');page.wait_for_function("document.querySelector('#tick').textContent === '1 / 96'")
        assert holder['session'].agent.last_decision['used_cached_computation']
        checks.append('think keeps world tick; next step consumes cached plan')
        page.click('#batch');page.wait_for_function("document.querySelector('#tick').textContent === '13 / 96'")
        prior=holder['session'].agent.model.snapshot()
        page.click('[data-kind=damage_tool]');page.wait_for_timeout(200)
        assert holder['session'].world.snapshot()['hidden'][2]==0
        assert prior==holder['session'].agent.model.snapshot()
        checks.append('intervention does not directly inject a posterior')
        page.click('#batch');page.wait_for_function("document.querySelector('#tick').textContent === '25 / 96'")
        page.click('#play');page.wait_for_timeout(1100);page.click('#play');page.wait_for_timeout(100)
        stopped=holder['session'].world.observe()['tick'];page.wait_for_timeout(800)
        assert holder['session'].world.observe()['tick']==stopped
        checks.append('run/pause advances and then stops actual simulated world')
        page.screenshot(path=str(ROOT/'evidence/dashboard_desktop.png'),full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(100)
        page.screenshot(path=str(ROOT/'evidence/dashboard_mobile.png'),full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        checks.append('desktop and 390px viewport have no horizontal overflow')
        page.set_viewport_size({'width':1440,'height':1080})
        page.select_option('#policy','obs_only');page.once('dialog',lambda d:d.accept());page.click('#reset')
        page.wait_for_function("document.querySelector('#tick').textContent === '0 / 96'")
        assert holder['session'].agent.config.policy=='obs_only'
        checks.append('confirmed reset really switches policy and resets history')
        assert not errors,errors;checks.append('no JavaScript page errors')
        browser.close()
    result={'successful':True,'checks':checks,'count':len(checks),'page_errors':errors,
            'transport':'in-process Session fixture, NOT browser HTTP',
            'direct_browser_http':'BLOCKED_BY_ADMINISTRATOR in this build environment',
            'real_http_tests':'separate unittest HTTP server tests',
            'windows_tested':False}
    save_json(ROOT/'evidence/browser_test.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
