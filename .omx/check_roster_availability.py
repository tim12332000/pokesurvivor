"""Public beta selection guards and save compatibility in desktop/mobile browsers."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import mimetypes
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW'

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    errors = []
    for mobile in [False, True]:
        context = browser.new_context(locale='zh-TW', viewport={'width':390,'height':844} if mobile else {'width':1280,'height':820}, is_mobile=mobile, has_touch=mobile, service_workers='block')
        def proxy(route):
            file = ROOT / unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
            route.fulfill(status=200 if file.is_file() else 404, body=file.read_bytes() if file.is_file() else b'Not found', content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        context.route('https://tim12332000.github.io/pokesurvivor/**', proxy)
        context.route('**api.ipify.org**', lambda route:route.fulfill(json={'ip':'198.51.100.10'}))
        page = context.new_page()
        page.on('pageerror', lambda error:errors.append(str(error)))
        def enter(reload=False):
            page.reload() if reload else page.goto(URL)
            page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
            page.wait_for_timeout(60)
            if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
            page.locator('#scr-menu').wait_for(state='visible')
        enter()
        assert page.evaluate('G.DB.save.partner===30001')
        assert page.locator('#btn-digimon').is_hidden()
        page.locator('#btn-naruto').click()
        assert page.locator('.naruto-card[data-naruto]:visible').count() == 3
        assert page.locator('#naruto-to-digimon').is_hidden()
        assert page.locator('.naruto-skill-entry').count()==3
        page.screenshot(path=str(ROOT/f'.omx/roster-availability-{"mobile" if mobile else "desktop"}.png'), animations='disabled')
        assert page.evaluate('''() => {
            const original=G.DB.save.partner;
            G.Naruto.choose(30003);G.Digimon.choose(20001);G.Digimon.choose(20173);G.Digimon.openPicker();
            return G.DB.save.partner===original&&document.getElementById('scr-digimon').classList.contains('hidden')
                &&G.DEX.filter(m=>m.gen===11).map(m=>m.dex).join(',')==='30001,30002,30006'
                &&!G.DEX.some(m=>m.gen===10)&&!G.STARTERS.some(m=>m.dex>=20001&&m.dex<30001)
                &&!G.STARTERS.some(m=>m.dex>30002&&m.dex!==30006)&&G.Gacha.featured(11).join(',')==='30001,30002,30006'
                &&G.Gacha.pull(G.DB.save,1,10)===null&&G.Digimon.records.size===33&&G.Naruto.records.size===8;
        }''')
        page.evaluate('G.Naruto.choose(30002);G.DB.save.stats.runs=12;G.DB.save.stats.bestTime=321;G.DB.commit()')
        enter(True)
        assert page.evaluate('G.DB.save.partner===30002&&G.DB.save.stats.runs===12')
        for dex in [30003,30008,20001,20173]:
            page.evaluate('(dex)=>{G.DB.save.partner=G.DB.save.starter=dex;G.DB.save.owned[dex]=true;G.DB.commit()}',dex)
            enter(True)
            assert page.evaluate('(dex)=>G.DB.save.partner===30001&&G.DB.save.starter===30001&&!!G.DB.save.owned[dex]&&G.DB.save.stats.runs===12&&G.DB.save.stats.bestTime===321',dex)
        page.evaluate("G.DB.save.partner=G.DB.save.starter=1;G.DB.grant(1,'starter');G.DB.commit()")
        enter(True)
        assert page.evaluate('G.DB.save.partner===1&&G.DB.save.stats.runs===12')
        page.locator('#scr-menu [data-go=gacha]').click()
        assert page.locator('#gacha-gens [data-gen="10"]').count()==0
        page.locator('#gacha-gens [data-gen="11"]').click()
        assert page.locator('#gacha-feat canvas').count()==3
        page.evaluate('G.Flow.goMenu()')
        page.locator('#scr-menu [data-go=dex]').click()
        assert page.locator('#dex-gens .gen-tab').count()==10
        page.locator('#dex-gens .gen-tab').last.click()
        assert page.locator('#dex-grid .cell').count()==3
        page.evaluate('G.Flow.goMenu()')
        page.locator('#scr-menu [data-go=upgrades]').click()
        assert page.evaluate("[...document.querySelectorAll('#upg-mon option')].every(o=>+o.value<20001||[30001,30002,30006].includes(+o.value))")
        page.evaluate('G.Flow.goMenu();G.DB.save.partner=30007;G.Game.startRun();G.Game.togglePause()')
        assert page.evaluate('G.Game.player.dex===30001')
        context.close()
    assert not errors,errors
    print(json.dumps({'visibleNinjas':[30001,30002,30006],'digimon':'hidden and guarded','saves':'progress preserved; unavailable partner falls back to Naruto','pokemon':'preserved','desktopAndMobile':True,'pageErrors':errors}))
    browser.close()
