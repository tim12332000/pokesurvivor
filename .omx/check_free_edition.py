"""Verify free/non-profit credits and absence of donation entry points."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import mimetypes
import os
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
URL='https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=free-edition&layout=wide'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(locale='zh-TW',viewport={'width':1280,'height':820},service_workers='block')
    if os.environ.get('PAGES_LIVE')!='1':
        def proxy(route):
            file=ROOT/unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
            route.fulfill(status=200 if file.is_file() else 404,body=file.read_bytes() if file.is_file() else b'Not found',content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        context.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
    page=context.new_page();errors=[];missing=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:missing.append(r.url) if r.status>=400 else None)
    page.goto(URL);page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.evaluate('G.Naruto.choose(30001);G.Flow.goMenu()')
    assert page.locator('#btn-support, #scr-support').count()==0
    assert page.evaluate('!G.Funding&&!G.SupportUI')
    assert page.locator('#free-project-notice,.naruto-credit,#sandbox-badge').count()==0
    assert '非營利' not in page.locator('#scr-menu').inner_text()
    page.screenshot(path=str(ROOT/'.omx/free-edition-menu.png'),animations='disabled')
    page.evaluate("G.SettingsUI.open('about')")
    assert all(s in page.locator('#set-body').inner_text() for s in ['免費','非營利','JPTER78','感謝'])
    page.screenshot(path=str(ROOT/'.omx/free-edition-about.png'),animations='disabled')
    page.locator('#set-body [data-legal]').click()
    assert all(s in page.locator('#scr-legal').inner_text() for s in ['免費','非營利','JPTER78','感謝'])
    assert not page.evaluate("[...document.querySelectorAll('a[href]')].some(a=>/ko-fi|paypal|patreon|buymeacoffee|github.com\\/sponsors/i.test(a.href))")
    assert not page.locator('script[src*="funding"],script[src*="support-ui"]').count()
    page.locator('#legal-close').click();page.evaluate('G.SettingsUI.close();G.Flow.play()')
    page.evaluate('''() => {
      G.Game.togglePause();G.DB.save.stats.runs=10;localStorage.removeItem('ps.ask');
      G.RunUI.showOver({dead:true,time:60,level:2,kills:10,bosses:0,coins:0,breakdown:'',moves:G.Game.player.moves,record:true,caught:[]},()=>{});
    }''')
    assert page.locator('#scr-over').is_visible()
    assert page.locator('#over-ask,.support-ask').count()==0
    page.set_viewport_size({'width':390,'height':844})
    page.evaluate('G.Game.quit();G.Flow.goMenu()')
    assert page.locator('#free-project-notice,.naruto-credit,#sandbox-badge').count()==0
    page.screenshot(path=str(ROOT/'.omx/free-edition-mobile.png'),animations='disabled')
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
    assert not errors,errors
    assert not missing,missing
    print(json.dumps({'menuNotices':'removed','aboutLegal':'free/non-profit and original-author thanks retained','paymentLinks':0,'postRunPrompt':'removed even after record or tenth run','startupErrors':errors,'missingAssets':missing}))
    browser.close()
