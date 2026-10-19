"""IP matching, fail-closed behavior and actual one-level/choice interaction."""
from pathlib import Path
from urllib.parse import unquote,urlsplit
import hashlib,json,mimetypes,os
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
URL='https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=dev-controls'
fixture='198.51.100.42'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(locale='zh-TW',viewport={'width':1280,'height':820},service_workers='block')
    if os.environ.get('PAGES_LIVE')!='1':
        def proxy(route):
            file=ROOT/unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
            route.fulfill(status=200 if file.is_file() else 404,body=file.read_bytes() if file.is_file() else b'Not found',content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        context.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
    context.route('**/.omx/dev-network.json',lambda r:r.fulfill(json={'allowedIpv4Sha256':[hashlib.sha256(fixture.encode()).hexdigest()],'timeoutMs':300}))
    state={'ip':fixture,'fail':False}
    def ip(route):
        if state['fail']:route.abort()
        else:route.fulfill(json={'ip':state['ip']},headers={'Access-Control-Allow-Origin':'*'})
    context.route('https://api.ipify.org/**',ip)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(URL);page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    assert page.evaluate('G.DevControls.ready')
    assert page.locator('#dev-level-up').is_hidden()
    page.evaluate('G.Flow.play()');button=page.locator('#dev-level-up');button.wait_for(state='visible')
    before=page.evaluate('G.Game.player.level');button.evaluate('el=>{el.click();el.click();el.click()}')
    page.locator('#scr-levelup').wait_for(state='visible')
    assert page.evaluate('G.Game.player.level')==before+1
    assert button.is_hidden()
    page.locator('#cards .card').first.click();button.wait_for(state='visible')
    assert page.evaluate('G.Game.player.level')==before+1
    page.screenshot(path=str(ROOT/'.omx/dev-level-button.png'),animations='disabled')
    state['ip']='203.0.113.55';assert not page.evaluate('G.DevControls.refresh()');assert button.is_hidden()
    state['ip']=fixture;assert page.evaluate('G.DevControls.refresh()');button.wait_for(state='visible')
    state['fail']=True;assert not page.evaluate('G.DevControls.refresh()');assert button.is_hidden()
    state['fail']=False
    page.evaluate("window.devSavedFetch=fetch;window.fetch=(url,options)=>String(url).includes('api.ipify.org')?new Promise((resolve,reject)=>options.signal.addEventListener('abort',()=>reject(new DOMException('Timed out','AbortError')))):devSavedFetch(url,options)")
    assert not page.evaluate('G.DevControls.refresh()');assert button.is_hidden()
    page.evaluate('window.fetch=devSavedFetch;delete window.devSavedFetch')
    state['fail']=False;state['ip']='bad payload';assert not page.evaluate('G.DevControls.refresh()');assert button.is_hidden()
    state['ip']=fixture;assert page.evaluate('G.DevControls.refresh()')
    page.evaluate('G.Game.togglePause()');page.wait_for_function("document.body.dataset.gameState==='paused'")
    assert button.is_hidden()
    page.evaluate('G.Game.quit();G.Flow.goMenu()');assert button.is_hidden()
    assert not errors,errors
    print(json.dumps({'matchingIP':'button visible only while playing','click':'exactly one level despite rapid clicks, actual choice UI','otherIP':'hidden','lookupFailureAndTimeout':'hidden','invalidPayload':'hidden','pausedMenu':'hidden','pageErrors':errors}))
    browser.close()
