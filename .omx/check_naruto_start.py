"""Fresh visitors start with Naruto; restored choices and history remain intact."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import mimetypes
import os
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
URL='https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=naruto-default'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(locale='zh-TW',viewport={'width':390,'height':844},is_mobile=True,has_touch=True,service_workers='block')
    if os.environ.get('PAGES_LIVE')!='1':
        def proxy(route):
            file=ROOT/unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
            route.fulfill(status=200 if file.is_file() else 404,body=file.read_bytes() if file.is_file() else b'Not found',content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        context.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    def enter(reload=False):
        if reload:page.reload()
        else:page.goto(URL)
        page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
        page.wait_for_function("['tap-start','scr-menu','scr-digimon'].some(id=>!document.getElementById(id).classList.contains('hidden'))")
        if page.locator('#tap-start').is_visible():page.locator('#tap-start').tap()
    enter()
    page.locator('#scr-menu').wait_for(state='visible')
    assert page.evaluate('G.DB.save.partner===30001&&G.DB.save.starter===30001&&!G.DB.save.partnerShiny')
    assert page.locator('#scr-digimon').is_hidden() and page.locator('#scr-test').is_hidden()
    cards=page.locator('#naruto-quick-pick [data-quick-naruto]')
    assert cards.count()==2
    assert page.locator('[data-quick-naruto="30001"]').get_attribute('aria-pressed')=='true'
    for width,height in [(1280,800),(390,844),(360,640)]:
        page.set_viewport_size({'width':width,'height':height})
        for card in cards.all():
            assert card.is_visible()
            bounds=card.bounding_box()
            assert bounds['x']>=0 and bounds['x']+bounds['width']<=width
            assert bounds['y']>=0 and bounds['y']+bounds['height']<=height
        assert page.locator('#scr-menu [data-go=play]').is_visible()
        page.screenshot(path=str(ROOT/f'.omx/naruto-quick-pick-{width}.png'),animations='disabled')
    page.locator('[data-quick-naruto="30002"]').tap()
    assert page.evaluate('G.DB.save.partner===30002&&G.DB.save.starter===30002')
    assert page.locator('[data-quick-naruto="30002"]').get_attribute('aria-pressed')=='true'
    page.locator('#scr-menu [data-go=play]').tap()
    page.wait_for_function("G.Game.player?.mon.dex===30002")
    page.evaluate('G.Game.quit();G.Flow.goMenu()')
    enter(True)
    assert page.locator('[data-quick-naruto="30002"]').get_attribute('aria-pressed')=='true'
    page.locator('[data-quick-naruto="30001"]').tap()
    page.locator('#scr-menu [data-go=play]').tap()
    page.wait_for_function("G.Game.player?.mon.dex===30001&&G.NarutoClones.actors.length===8")
    assert page.evaluate("G.Game.player.moves[0].id==='naruto-shadow-clones'")
    page.evaluate('G.Game.quit();G.Flow.goMenu();G.Naruto.choose(30002);G.DB.save.stats.runs=12;G.DB.save.stats.bestTime=321;G.DB.commit()')
    enter(True)
    assert page.evaluate('G.DB.save.partner===30002&&G.DB.save.stats.runs===12&&G.DB.save.stats.bestTime===321')
    page.evaluate('G.Digimon.choose(20001)')
    assert page.evaluate('G.DB.save.partner===30002&&G.DB.save.stats.runs===12')
    # Actual legacy Digimon saves migrate safely while retaining play history.
    page.evaluate('G.DB.save.partner=G.DB.save.starter=20001;G.DB.commit()');enter(True)
    assert page.evaluate('G.DB.save.partner===30001&&G.DB.save.starter===30001&&G.DB.save.stats.runs===12&&G.DB.save.stats.bestTime===321')
    page.evaluate("G.DB.save.partner=G.DB.save.starter=1;G.DB.grant(1,'starter');G.DB.commit()");enter(True)
    assert page.evaluate('G.DB.save.partner===1&&G.DB.save.stats.runs===12')
    assert page.locator('#scr-menu .partner-card').is_visible()
    assert page.locator('#naruto-quick-pick [aria-pressed=true]').count()==0
    # A visitor who previously opened the page but never chose or played also gets Naruto.
    page.evaluate('G.DB.save.partner=G.DB.save.starter=null;G.DB.save.stats.runs=0;G.DB.commit()');enter(True)
    assert page.evaluate('G.DB.save.partner===30001')
    # Incomplete saves with actual play history are not silently reassigned.
    page.evaluate('G.DB.save.partner=G.DB.save.starter=null;G.DB.save.stats.runs=12;G.DB.commit()');enter(True)
    assert page.evaluate('!G.DB.save.partner&&G.DB.save.stats.runs===12')
    assert not errors,errors
    print(json.dumps({'freshVisitor':'Naruto, main menu, shadow-clone starter','returningChoices':['Sasuke','Pokemon'],'disabledDigimon':'selection rejected; legacy save migrated to Naruto','history':'preserved','unplayedExistingVisit':'Naruto','pageErrors':errors}))
    browser.close()
