"""Standalone preview: no game boot, all tiers, both directions and controls."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/naruto-summoning/standalone'
URL = 'http://127.0.0.1:8004/art-review/gamabunta-preview/'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reports = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in (False, True):
            label = 'mobile' if mobile else 'desktop'
            page = browser.new_page(viewport={'width':390,'height':844} if mobile else {'width':1100,'height':1000},
                                    is_mobile=mobile, has_touch=mobile, service_workers='block')
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(URL)
            page.wait_for_function('window.preview?.ready')
            assert page.locator('iframe').count() == 0
            assert page.evaluate('!G.Flow && !G.Game.startRun'), 'Preview booted the game'
            cases = []
            for side in ('1', '-1'):
                page.locator('#direction').select_option(side)
                for rank in range(1,6):
                    page.locator(f'[data-tier="{rank}"]').click()
                    result = page.evaluate('''() => {
                      const end=[2.6,3,3,7.2,8.8][preview.rank-1];preview.seek(end-.01);
                      return {rank:preview.rank,kinds:preview.field.events.map(e=>e.kind),time:preview.time};
                    }''')
                    kinds = result['kinds']
                    assert kinds.count('water') == 3, result
                    assert ('sword' in kinds) == (rank >= 2), result
                    assert ('heavy' in kinds) == (rank >= 3), result
                    assert ('fire' in kinds) == (rank >= 4), result
                    assert ('fox' in kinds) == (rank >= 5), result
                    cases.append(result)
            page.locator('#direction').select_option('1')
            page.locator('[data-tier="5"]').click()
            page.locator('[data-time="3.0"]').click()
            assert page.locator('#phase').inner_text() == '蛤蟆油炎彈・準備'
            page.locator('[data-time="3.5"]').click()
            assert '油炎彈' in page.locator('#phase').inner_text()
            assert page.evaluate('G.NarutoSummoning.phaseFor(preview.field)') == 'fire'
            assert not page.evaluate('preview.field.events.some(e => /oil|tag/.test(e.kind))')
            page.screenshot(path=str(OUT / f'{label}-fire.png'), full_page=True)
            page.locator('[data-time="8.05"]').click()
            first = page.evaluate('document.querySelector("canvas").toDataURL()')
            page.wait_for_timeout(80)
            assert page.evaluate('document.querySelector("canvas").toDataURL()') == first, 'Paused preview moved'
            page.screenshot(path=str(OUT / f'{label}-fox.png'), full_page=True)
            page.locator('#seek').fill('2500')
            assert abs(page.evaluate('preview.time') - 2.5) < .01
            assert '短刀' in page.locator('#phase').inner_text()
            page.locator('#replay').click()
            page.wait_for_timeout(150)
            assert 0 < page.evaluate('preview.time') < 1
            page.locator('#play').click()
            assert page.locator('#play').inner_text() == '播放'
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'Horizontal overflow'
            assert not page.locator('#error').inner_text()
            assert not errors, errors
            reports[label] = {'cases':cases,'noGameBoot':True,'pausedStable':True,'controls':True,'errors':errors}
            page.close()
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'ok':True,'viewports':list(reports),'cases':20,'url':URL}))


if __name__ == '__main__':
    main()
