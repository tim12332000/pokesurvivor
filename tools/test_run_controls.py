"""Native desktop/touch acceptance for speed and automatic upgrade cards."""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/run-controls'
URL = os.environ.get('RUN_CONTROLS_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=run-controls')

SETUP = r"""() => {
 Acceptance.arena();
 // Controlled arena removes incidental spawns/XP; the real game loop,
 // simulation clock, input, card generation and application remain native.
 G.Spawner.update=()=>{};
 window.controlTexts=[];
 const context=document.querySelector('#game').getContext('2d'),fill=context.fillText;
 context.fillText=function(text,...args){
   if(String(text).includes('倍速')||String(text).includes('自動選卡'))controlTexts.push(String(text));
   return fill.call(this,text,...args);
 };
 window.nativeOffer=G.LevelUp.offer;
 window.appliedCards=[];
 G.LevelUp.offer=function(...args){return nativeOffer.apply(this,args).map(card=>{
   const apply=card.apply;return {...card,apply(p){appliedCards.push(card.key);return apply(p)}};
 })};
 Acceptance.resume();
}"""


def click_control(page, mobile, kind):
    # Touch de-duplicates matching native pointer/touch events for 350 ms.
    page.wait_for_timeout(380)
    point = page.evaluate("""kind => {
      const layout=G.Touch.controlLayout(innerWidth,innerHeight,G.Game.player.slots.length);
      const safe=layout.portrait?Math.min(44,G.Touch.safeArea().top):0;
      return {x:kind==='speed'?66:186,y:94+safe};
    }""", kind)
    if mobile:
        page.touchscreen.tap(point['x'], point['y'])
    else:
        page.mouse.click(point['x'], point['y'])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'failedRequests': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for mobile in (False, True):
                label = 'mobile' if mobile else 'desktop'
                context = browser.new_context(locale='zh-TW', viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.on('console', lambda m: report['errors'].append(m.text) if m.type=='error' and '[Game]' in m.text else None)
                page.on('response', lambda r: report['failedRequests'].append(r.url) if r.status>=400 and '127.0.0.1' in r.url else None)
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.querySelector('#boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30007"]').click()
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"')
                page.evaluate(HARNESS)
                page.evaluate(SETUP)
                result = {'speedMeasurements': []}
                report['viewports'][label] = result
                assert page.evaluate('G.Game.playbackSpeed===1 && !G.Game.autoPickUpgrades')
                for speed in (1,2,3):
                    if speed>1:
                        click_control(page,mobile,'speed')
                    page.wait_for_function('(speed)=>G.Game.playbackSpeed===speed',arg=speed)
                    measurement = page.evaluate("""async () => {
                      const t=G.Game.st.time,wall=performance.now();
                      await new Promise(resolve=>setTimeout(resolve,650));
                      return {simulation:G.Game.st.time-t,wall:(performance.now()-wall)/1000};
                    }""")
                    measurement['ratio']=measurement['simulation']/measurement['wall']
                    assert speed*.72 < measurement['ratio'] < speed*1.2, measurement
                    result['speedMeasurements'].append(measurement)
                click_control(page,mobile,'speed')
                page.wait_for_function('G.Game.playbackSpeed===1')
                click_control(page,mobile,'auto')
                page.wait_for_function('G.Game.autoPickUpgrades')
                active = page.evaluate('G.Game.player.active')
                page.evaluate('G.Game.debugLevelUp()')
                page.wait_for_function('appliedCards.length===1 && G.Game.state==="playing"')
                assert page.evaluate('(active)=>G.Game.player.active===active',active)
                result['automaticCard']=page.evaluate('appliedCards[0]')
                # Offer a real newly learned card, then use the same native loop
                # and random pick path, proving learning does not switch skills.
                result['newCard']=page.evaluate("""() => {
                  const p=G.Game.player;p.level=3;
                  const card=nativeOffer(p,100).find(c=>c.key==='new:naruto-sand-coffin');
                  Acceptance.assert(card,'native eligible new skill card absent');
                  window.previousGroup=p.slots[p.active];
                  window.activeSwitchCalls=0;window.originalSetActive=p.setActive;
                  p.setActive=function(...args){activeSwitchCalls++;return originalSetActive.apply(this,args)};
                  G.LevelUp.offer=()=>[card];G.Game.debugLevelUp();return card.key;
                }""")
                page.wait_for_function('G.Game.player.hasMove("naruto-sand-coffin") && G.Game.state==="playing"')
                assert page.evaluate('previousGroup ? G.Game.player.slots[G.Game.player.active]===previousGroup : G.Game.player.activeGroup().some(m=>m.id==="naruto-sand-coffin")')
                assert page.evaluate('previousGroup ? activeSwitchCalls===0 : activeSwitchCalls<=1'), 'automatic learning unexpectedly switched active skill'
                page.evaluate('() => {delete G.Game.player.setActive}')
                page.evaluate('() => {G.LevelUp.offer=nativeOffer}')
                page.screenshot(path=str(OUT/f'{label}-enabled.png'))
                click_control(page,mobile,'auto')
                page.wait_for_function('!G.Game.autoPickUpgrades')
                page.evaluate('G.Game.debugLevelUp()')
                page.wait_for_function('G.Game.state==="levelup"')
                page.wait_for_timeout(300)
                assert page.evaluate('G.Game.state==="levelup"')
                page.locator('#cards .card').first.click()
                page.wait_for_function('G.Game.state==="playing"')
                click_control(page,mobile,'auto')
                page.wait_for_function('G.Game.autoPickUpgrades')
                page.evaluate('G.Game.togglePause();G.Game.debugLevelUp()')
                page.wait_for_timeout(200)
                assert page.evaluate('G.Game.state==="paused"')
                page.evaluate('G.Game.togglePause()')
                page.wait_for_function('G.Game.state==="playing" && !G.UI.isOpen("scr-levelup")')
                click_control(page,mobile,'speed')
                page.wait_for_function('G.Game.playbackSpeed===2')
                result['labels']=page.evaluate('[...new Set(controlTexts)]')
                assert any('自動選卡' in text for text in result['labels']),result['labels']
                assert all(any('x'+str(n) in text or '×'+str(n) in text for text in result['labels']) for n in (1,2,3)),result['labels']
                page.evaluate('G.Game.startRun()')
                assert page.evaluate('G.Game.playbackSpeed===1 && !G.Game.autoPickUpgrades')
                result['newRunReset']=True
                page.wait_for_timeout(100)
                page.screenshot(path=str(OUT/f'{label}-reset.png'))
                context.close()
            browser.close()
        assert not report['errors'],report['errors']
        assert not report['failedRequests'],report['failedRequests']
        report['ok']=True
    except Exception as error:
        report.update(ok=False,failure=str(error))
        raise
    finally:
        (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':True,'viewports':list(report['viewports']),'evidence':str(OUT)}))


if __name__=='__main__':
    main()
