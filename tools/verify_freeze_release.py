"""Compare the live Freeze package to its canonical artifact, then open it normally."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://tim12332000.github.io/pokesurvivor/'
OUT = ROOT / '.omx/state/freeze/public'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('artifact', type=Path)
    parser.add_argument('source')
    args = parser.parse_args()
    artifact = args.artifact.resolve()
    assert artifact.is_relative_to(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    paths = ['index.html', '.omx/digimon.html', '.omx/naruto.js', '.omx/redrawn-init.js',
             '.omx/lf2.js', '.omx/lf2-art.js', '.omx/lf2-audio.js', '.omx/lf2-freeze-combat.js',
             'js/core/audio.js', 'js/entities/enemy.js', 'js/systems/combat.js', 'js/systems/self-clone.js',
             'assets/lf2/freeze/manifest.json']
    paths += [p.relative_to(artifact).as_posix() for p in (artifact/'assets/lf2/freeze').iterdir()
              if p.is_file() and p.suffix in {'.png', '.wav'}]
    checked = {}
    for name in paths:
        expected = hashlib.sha256((artifact/name).read_bytes()).hexdigest()
        with urllib.request.urlopen(BASE + name + '?verify=' + args.source, timeout=45) as response:
            actual = hashlib.sha256(response.read()).hexdigest()
        assert actual == expected, 'Public file differs: ' + name
        checked[name] = actual
    (OUT/'bytes.json').write_text(json.dumps(checked, indent=2), 'utf-8')
    browser_report = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
        for name, viewport, mobile in [('desktop', {'width':1100,'height':850}, False),
                                       ('mobile390', {'width':390,'height':844}, True)]:
            context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile)
            page = context.new_page()
            errors, failed = [], []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('response', lambda r: failed.append({'status':r.status,'url':r.url}) if r.status >= 400 and 'github.io/pokesurvivor/' in r.url else None)
            url = BASE + '?lang=zh-TW&hero=freeze&release=' + args.source[:8]
            if not mobile: url += '&layout=wide'
            page.goto(url)
            page.wait_for_function("window.G?.LF2Freeze&&document.getElementById('boot').classList.contains('hidden')", timeout=60000)
            if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
            page.locator('[data-quick-naruto="30018"]').click()
            page.wait_for_function('G.NarutoAssets.ready(30018)', timeout=30000)
            page.screenshot(path=str(OUT/(name+'-selection.png')))
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30018&&G.Game.state==="playing"')
            page.keyboard.down('KeyD')
            page.wait_for_timeout(1500)
            page.keyboard.up('KeyD')
            page.screenshot(path=str(OUT/(name+'-play.png')))
            state = page.evaluate('({dex:G.Game.player.dex,level:G.Game.player.level,ready:G.LF2Art.loaded,moves:G.Game.player.moves.map(m=>m.id),label:document.querySelector(".launch-name")?.textContent||null})')
            assert state['dex'] == 30018 and state['ready'] and state['moves'][0] == 'lf2-iceball'
            assert not errors and not failed, {'errors':errors,'failed':failed}
            browser_report[name] = {**state, 'errors':errors, 'failed':failed, 'url':page.url}
            context.close()
        browser.close()
    (OUT/'browser.json').write_text(json.dumps(browser_report, indent=2), 'utf-8')
    print(json.dumps({'ok':True,'files':len(checked),'browsers':list(browser_report)}))


if __name__ == '__main__':
    main()
