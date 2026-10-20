"""Real local-browser smoke test for level-up controls and mobile skill switching."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'.omx/state/local-mobile-check'
OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    reports=[]
    for width,height in [(390,844),(320,568),(844,390),(1280,820)]:
        mobile=width!=1280
        context=browser.new_context(locale='zh-TW',viewport={'width':width,'height':height},is_mobile=mobile,has_touch=mobile,device_scale_factor=1,service_workers='block')
        requests=[]
        context.route('https://api.ipify.org/**',lambda route:(requests.append(route.request.url),route.abort()))
        page=context.new_page();page.set_default_timeout(15000)
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://localhost:8765/.omx/digimon.html?lang=zh-TW',wait_until='domcontentloaded')
        page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
        assert page.evaluate('G.DevControls.ready')
        assert not requests,'Localhost must not query the public IP'
        page.evaluate('G.Naruto.choose(30001);G.Flow.goMenu()')
        page.locator('#scr-menu').wait_for(state='visible')
        assert page.locator('#dev-level-up').is_hidden()
        page.evaluate('G.Flow.play();G.Game.player.invuln=99999')
        button=page.locator('#dev-level-up');button.wait_for(state='visible')
        activate=lambda locator:locator.tap() if mobile else locator.click()
        for step in range(2):
            before=page.evaluate('G.Game.player.level')
            activate(button)
            page.locator('#scr-levelup').wait_for(state='visible')
            assert page.evaluate('G.Game.player.level')==before+1
            button.wait_for(state='hidden')
            if step==0:page.screenshot(path=str(OUT/f'{width}-levelup.png'),animations='disabled')
            activate(page.locator('#cards .card').first)
            button.wait_for(state='visible')
            assert page.evaluate('G.Game.player.level')==before+1
        if mobile:
            page.evaluate("""() => {
                const p=G.Game.player;
                p.moves=['naruto-shadow-clones','naruto-naruto','naruto-kunai','naruto-shuriken'].map(id=>G.Moves.instance(id));
                p.slots=p.moves.map(m=>[m]);p.active=0;
            }""")
            page.wait_for_function('G.Game.player.slots.length===4')
            layout=page.evaluate('G.Touch.controlLayout(innerWidth,innerHeight,4)')
            slots=layout['slots'];assert len(set(s['y'] for s in slots))==1
            assert abs((slots[0]['x']+slots[-1]['x']+slots[-1]['w'])/2-width/2)<1
            second=slots[1];page.touchscreen.tap(second['x']+second['w']/2,second['y']+second['h']/2)
            page.wait_for_function('G.Game.player.active===1')
            page.locator('.toast').filter(has_text='已切換').wait_for(state='visible')
            page.screenshot(path=str(OUT/f'{width}-switched.png'),animations='disabled')
            page.locator('.toast').wait_for(state='hidden')
            page.screenshot(path=str(OUT/f'{width}-playing.png'),animations='disabled')
        page.evaluate('G.Game.togglePause()')
        page.wait_for_function("G.Game.state==='paused'")
        page.wait_for_function("document.getElementById('dev-level-up').classList.contains('hidden')")
        assert not errors,errors
        reports.append({'size':[width,height],'actualLevelUpClicks':2,'choiceAndReturn':'pass','narutoLoaded':True,'mobileSwitch':mobile,'pageErrors':errors,'publicIPRequests':requests})
        context.close()
    browser.close()
    (OUT/'results.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(reports,ensure_ascii=False))
