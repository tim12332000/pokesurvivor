"""Desktop portrait framing, real phone controls, keyboard and wide fallback."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/desktop-portrait'
URL = os.environ.get('PORTRAIT_URL', 'http://127.0.0.1:8004/.omx/digimon.html')
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'


def ready(frame):
    frame.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
    if frame.locator('#tap-start').is_visible():
        frame.locator('#tap-start').click()
    frame.locator('#scr-menu').wait_for(state='visible')


def dimensions(frame):
    return frame.evaluate("""() => ({w:innerWidth,h:innerHeight,touch:G.Touch.active,
      portrait:G.Touch.controlLayout(innerWidth,innerHeight,4).portrait,
      overflow:document.documentElement.scrollWidth>innerWidth+1,
      hero:G.DB.save.partner,canvas:[document.getElementById('game').clientWidth,document.getElementById('game').clientHeight]})""")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'desktop': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for width, height in [(1440, 900), (1366, 768), (800, 600)]:
            context = browser.new_context(viewport={'width': width, 'height': height}, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(URL + '?lang=zh-TW&hero=tenten#selected')
            page.wait_for_url('**/portrait.html?**')
            frame_element = page.locator('#portrait-game')
            frame_element.wait_for()
            frame = frame_element.element_handle().content_frame()
            ready(frame)
            state = dimensions(frame)
            assert state['touch'] and not state['overflow'], state
            assert state['portrait'] == (state['w'] <= 600), state
            assert state['hero'] == 30009 and abs(state['w']/state['h']-3/4) < .003, state
            assert frame.evaluate('location.hash') == '#selected'
            bounds = frame_element.bounding_box()
            assert abs(bounds['x']-(width-bounds['width'])/2) < 1, bounds
            page.screenshot(path=str(OUT / f'desktop-{width}-menu.png'))
            frame.locator('#scr-menu [data-go="play"]').click()
            frame.wait_for_function("G.Game.state==='playing'")
            frame.evaluate('G.World.collide=()=>{};G.World.isLiquid=()=>false;G.Game.player.invuln=999')
            frame.locator('#game').click(position={'x': 100, 'y': 200})
            before = frame.evaluate('G.Game.player.x')
            page.keyboard.down('KeyD')
            page.wait_for_timeout(180)
            page.keyboard.up('KeyD')
            assert frame.evaluate('G.Game.player.x') > before + 1, 'keyboard movement failed inside frame'
            pause = frame.evaluate('G.Touch.controlLayout(innerWidth,innerHeight,G.Game.player.slots.length).pause')
            frame.locator('#game').click(position={'x': pause['x']+pause['w']/2, 'y': pause['y']+pause['h']/2})
            frame.wait_for_function("G.Game.state==='paused'")
            page.keyboard.press('Escape')
            frame.wait_for_function("G.Game.state==='playing'")
            page.screenshot(path=str(OUT / f'desktop-{width}-game.png'))
            if width == 1440:
                page.set_viewport_size({'width': 1100, 'height': 720})
                frame.wait_for_function('innerHeight===720')
                assert dimensions(frame)['portrait'], 'resize lost portrait controls'
                page.locator('#wide-layout').click()
                page.wait_for_url('**/digimon.html?**layout=wide**')
                ready(page)
                wide = dimensions(page)
                assert wide['w'] == 1100 and not wide['touch'] and wide['hero'] == 30009, wide
                report['wide'] = wide
            report['desktop'].append(state)
            context.close()
            print(width, height, 'desktop portrait PASS', flush=True)
        for width, height in [(390, 844), (844, 390)]:
            context = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=True, has_touch=True, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(URL + '?lang=zh-TW&hero=tenten')
            ready(page)
            assert not page.locator('#portrait-game').count(), 'phone unexpectedly nested'
            state = dimensions(page)
            assert state['w'] == width and state['h'] == height and not state['overflow'], state
            assert state['portrait'] == (height>width), state
            if width == 390:
                page.screenshot(path=str(OUT / 'mobile-reference-menu.png'))
            report[f'mobile-{width}'] = state
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')


if __name__ == '__main__':
    main()
