"""Start every available ninja through the real menu on desktop and mobile."""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get('NARUTO_STARTUP_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW')
OUT = ROOT / '.omx/state/naruto-startup'


def check(browser, mobile):
    context = browser.new_context(
        viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900},
        is_mobile=mobile, has_touch=mobile, service_workers='block')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(URL + ('&layout=wide' if not mobile else ''))
    page.wait_for_function("window.G?.NarutoAssets && document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():
        page.locator('#tap-start').click()
    heroes = page.evaluate('G.Naruto.availableDexes')
    results = []
    for dex in heroes:
        page.locator(f'[data-quick-naruto="{dex}"]').click()
        page.locator('#scr-menu [data-go="play"]').click()
        page.wait_for_function("dex=>G.Game.state==='playing' && G.Game.player?.dex===dex", arg=dex, timeout=60000)
        page.wait_for_function('G.EnemyMgr.count>0', timeout=20000)
        result = page.evaluate('''()=>({dex:G.Game.player.dex,ready:G.NarutoAssets.ready(G.Game.player.dex),
          tiers:G.Enemies.cast.map(tier=>tier.list.length),bosses:G.Enemies.BOSSES.length,
          enemies:G.EnemyMgr.count})''')
        assert result['ready'] and all(result['tiers']) and result['bosses'] == 5, result
        assert not errors, errors
        results.append(result)
        print(json.dumps({'mobile': mobile, **result}), flush=True)
        page.evaluate('G.Flow.goMenu()')
    context.close()
    return results


if __name__ == '__main__':
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        report = {'desktop': check(browser, False), 'mobile': check(browser, True)}
        browser.close()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('All 16 menu-to-game starts passed.')
