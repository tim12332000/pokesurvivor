"""Real mobile touch, portrait controls, and responsive sandbox regression checks."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import mimetypes
import os
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=portrait'
SIZES = [(390, 844), (320, 568), (360, 640), (430, 932), (844, 390)]


def fit(page, label):
    result = page.evaluate('''() => {
      const w=innerWidth,h=innerHeight,L=G.Touch.controlLayout(w,h,4);
      const rects=[...L.slots,L.item,L.pause];
      return {w,h,portrait:L.portrait,key:G.Touch.padKey(),
        overflow:document.documentElement.scrollWidth>w+1,
        bad:rects.filter(r=>!r||r.x<0||r.y<0||r.x+r.w>w+1||r.y+r.h>h+1),L};
    }''')
    assert not result['overflow'], (label, 'horizontal page overflow', result)
    assert not result['bad'], (label, 'unreachable controls', result)
    expected = result['w'] <= 600 and result['h'] > result['w']
    assert result['portrait'] == expected, (label, result)
    assert result['key'] == ('padPortrait' if expected else 'pad'), result
    if expected:
        slots = result['L']['slots']
        assert len(slots) == 4 and slots[0]['y'] == slots[1]['y'], result
        assert slots[2]['y'] == slots[3]['y'] > slots[0]['y'], result
    return result


def point(rect):
    return {'x': round(rect['x'] + rect['w'] / 2), 'y': round(rect['y'] + rect['h'] / 2)}


with sync_playwright() as p:
    started = time.monotonic()
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    reports = []
    try:
        for width, height in SIZES:
            context = browser.new_context(locale='zh-TW', viewport={'width': width, 'height': height},
                                          is_mobile=True, has_touch=True, device_scale_factor=1,
                                          service_workers='block')
            if os.environ.get('PAGES_LIVE') != '1':
                def proxy(route):
                    file = ROOT / unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
                    route.fulfill(status=200 if file.is_file() else 404,
                                  body=file.read_bytes() if file.is_file() else b'Not found',
                                  content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
                context.route('https://tim12332000.github.io/pokesurvivor/**', proxy)
            page = context.new_page()
            page.set_default_timeout(6000)
            errors, missing = [], []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('response', lambda r: missing.append(r.url) if r.status >= 400 else None)
            page.goto(URL, wait_until='domcontentloaded')
            page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').tap()
            page.evaluate('G.Naruto.choose(30001);G.Flow.goMenu()')
            page.locator('#scr-menu').wait_for(state='visible')
            if width == 390:
                page.screenshot(path=str(ROOT / '.omx/mobile-portrait-menu.png'),animations='disabled')
            assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1'), 'Menu overflows'
            page.evaluate('''() => {
              G.Flow.play();
              const pl=G.Game.player;
              pl.moves=['naruto-shadow-clones','naruto-naruto','naruto-kunai','naruto-shuriken'].map(id=>G.Moves.instance(id));
              pl.slots=pl.moves.map(m=>[m]);pl.active=0;
              pl.hp=pl.maxHp;
            }''')
            page.wait_for_function("G.Game.state==='playing'")
            assert not page.locator('#rotate').is_visible(), 'Rotation blocker visible'
            layout = fit(page, f'{width}x{height}')
            before = page.evaluate('G.Game.st.time')
            page.wait_for_function('(before)=>G.Game.st.time>before', arg=before)
            if width <= 600:
                camera = page.evaluate('({w:G.Camera.w,h:G.Camera.h,scale:G.Camera.scale,iw:innerWidth,ih:innerHeight,cw:document.getElementById("game").clientWidth,ch:document.getElementById("game").clientHeight,touch:G.Settings.touch})')
                assert abs(camera['w'] - 540) < 1, ('Portrait camera too distant', camera)
            cdp = context.new_cdp_session(page)

            def touch(kind, points):
                cdp.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': points})

            # Open space isolates input from generated terrain, without replacing game simulation.
            page.evaluate('''() => {
              G.World.collide=()=>{};G.World.isLiquid=()=>false;
              window.mobileStart={x:G.Game.player.x,y:G.Game.player.y};
            }''')
            start = {'x': 55, 'y': height - 130, 'id': 1}
            held = {'x': 95, 'y': height - 130, 'id': 1}
            touch('touchStart', [start])
            touch('touchMove', [held])
            page.wait_for_function('Math.hypot(G.Game.player.x-mobileStart.x,G.Game.player.y-mobileStart.y)>2')
            slot = dict(point(layout['L']['slots'][3]), id=2)
            touch('touchStart', [held, slot])
            try:
                page.wait_for_function('G.Game.player.active===3')
            except Exception:
                print(json.dumps({'touchFailure':f'{width}x{height}','tap':slot,'state':page.evaluate('({state:G.Game.state,active:G.Game.player.active,stick:G.Touch.stick,layout:G.Touch.controlLayout(innerWidth,innerHeight,4)})'),'errors':errors}))
                raise
            assert page.evaluate('G.Touch.vector()&&G.Touch.vector()[0]>0'), 'Second finger cancelled joystick'
            if width == 390:
                page.screenshot(path=str(ROOT / '.omx/mobile-portrait-game.png'),animations='disabled')
            touch('touchCancel', [])
            assert page.evaluate('G.Touch.vector()===null'), 'Touch cancellation left movement stuck'
            pause = point(layout['L']['pause'])
            page.touchscreen.tap(**pause)
            page.wait_for_function("G.Game.state==='paused'")
            assert page.locator('#scr-pause').is_visible()
            page.evaluate('G.Game.togglePause()')
            if width == 390:
                # Rotation must not force pause or preserve an old finger position.
                touch('touchStart', [start])
                touch('touchMove', [held])
                page.set_viewport_size({'width': 844, 'height': 390})
                page.wait_for_function('innerWidth===844')
                fit(page, 'rotated landscape')
                assert page.evaluate("G.Game.state==='playing'&&G.Touch.vector()===null"), 'Rotation changed play state or kept stick'
                touch('touchCancel', [])
                page.set_viewport_size({'width': 390, 'height': 844})
                page.wait_for_function('innerWidth===390')
                fit(page, 'rotated portrait')
                assert page.evaluate("G.Game.state==='playing'")
                page.evaluate('G.Game.debugLevelUp()')
                try:
                    page.locator('#scr-levelup').wait_for(state='visible')
                except Exception:
                    print(json.dumps({'levelupFailure': page.evaluate('({state:G.Game.state,dead:G.Game.player.dead,hp:G.Game.player.hp,time:G.Game.st.time})'), 'errors':errors}))
                    raise
                assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1'), 'Level-up overflow'
                page.screenshot(path=str(ROOT / '.omx/mobile-portrait-levelup.png'),animations='disabled')
                page.locator('#cards .card').first.tap()
                page.wait_for_function("G.Game.state==='playing'")
                page.evaluate("G.Game.togglePause();G.Settings.set('pad',{pause:[.85,.13]});G.SettingsUI.open('ctl')")
                page.screenshot(path=str(ROOT / '.omx/mobile-portrait-settings.png'),animations='disabled')
                assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1'), 'Settings overflow'
                page.locator('#set-layout').tap()
                page.locator('#scr-layout').wait_for(state='visible')
                geometry = page.evaluate('''() => {
                  const slots=[...document.querySelectorAll('#scr-layout .lay-slot:not(.item)')].map(e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height};});
                  return{slots,actual:G.Touch.controlLayout(innerWidth,innerHeight,4).slots};
                }''')
                for actual, editor in zip(geometry['actual'], geometry['slots']):
                    assert all(abs(actual[k] - editor[k]) < 2 for k in ['x', 'y', 'w', 'h']), geometry
                page.screenshot(path=str(ROOT / '.omx/mobile-portrait-editor.png'),animations='disabled')
                bar = page.locator('#scr-layout [data-k=bar]').bounding_box()
                # Drag a real editor control; saved positions must use the portrait-only key.
                origin = {**point(geometry['slots'][0]), 'id': 1}
                target = {**origin, 'y': origin['y'] - 40}
                touch('touchStart', [origin]); page.wait_for_timeout(80)
                touch('touchMove', [target]); page.wait_for_timeout(80)
                touch('touchEnd', [])
                page.locator('#lay-save').tap()
                saved = page.evaluate("({portrait:G.Settings.get('padPortrait'),landscape:G.Settings.get('pad')})")
                assert saved['portrait'] and saved['landscape']['pause'][0] == .85, ('Editor did not save separately', saved)
                page.evaluate('G.SettingsUI.close();G.Game.togglePause()')
                page.set_viewport_size({'width': 320, 'height': 568})
                page.wait_for_function('innerWidth===320')
                fit(page, 'custom layout resized to small portrait')
                page.screenshot(path=str(ROOT / '.omx/mobile-portrait-small.png'),animations='disabled')
                page.evaluate("G.Game.togglePause();window.mobileLocks=0;screen.orientation.lock=()=>{mobileLocks++;return Promise.resolve()};document.documentElement.requestFullscreen=()=>Promise.resolve();G.SettingsUI.open('gfx')")
                page.locator('#set-full').evaluate('(e)=>e.click()')
                page.wait_for_timeout(30)
                assert page.evaluate('mobileLocks===0'), 'Fullscreen locks orientation'
            assert not errors, errors
            assert not missing, missing
            reports.append({'viewport': f'{width}x{height}', 'portrait': layout['portrait'], 'realTouchMove': True,
                            'simultaneousSlotTouch': True, 'pause': True, 'errors': errors})
            context.close()
        print(json.dumps({'passed': reports, 'rotation': True, 'choiceUI': True, 'separateSavedLayouts': True,
                          'editorMatchesHUD': True, 'elapsedSeconds': round(time.monotonic() - started, 2)}, ensure_ascii=False))
    finally:
        browser.close()
