"""Normal launch menu: real selection/play, small screens and roster growth."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME

URL = os.environ.get('MENU_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW')
OUT = Path(os.environ.get('MENU_OUT', str(Path(__file__).resolve().parents[1] / '.omx/state/menu-layout')))
DEXES = [30001, 30002, 30006, 30007, 30009]

VISIBLE_PLAY = r"""() => {
 const button=document.querySelector('#scr-menu [data-go="play"]'),r=button.getBoundingClientRect();
 const hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
 return {visible:r.top>=0&&r.bottom<=innerHeight&&r.left>=0&&r.right<=innerWidth,
   hittable:hit===button||button.contains(hit),width:r.width,height:r.height,top:r.top,bottom:r.bottom};
}"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'views': {}, 'errors': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, width, height in [('desktop', 1440, 1000), ('laptop', 1366, 768), ('mobile', 390, 844), ('small', 320, 568), ('landscape', 844, 390)]:
            context = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=label in ['mobile', 'small', 'landscape'], has_touch=label in ['mobile', 'small', 'landscape'], service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.evaluate('G.Flow.goMenu()')
            page.wait_for_function("document.querySelector('#scr-menu.launch-menu .launch-detail')")
            assert page.locator('#scr-menu [data-go="play"]').count() == 1, 'duplicate launch button'
            assert page.locator('[data-quick-naruto]').count() == len(DEXES), 'roster lost a playable character'
            initial = page.evaluate(VISIBLE_PLAY)
            assert initial['visible'] and initial['hittable'], (label, 'initial launch inaccessible', initial)
            assert initial['height'] >= 44, (label, 'launch touch target too small')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), (label, 'horizontal overflow')
            played = []
            for dex in DEXES:
                button = page.locator(f'[data-quick-naruto="{dex}"]')
                button.click()
                assert button.get_attribute('aria-pressed') == 'true', (label, dex, 'selection state')
                assert page.locator('.launch-detail').get_attribute('data-selected-hero') == str(dex), (label, dex, 'preview mismatch')
                assert page.evaluate('G.DB.save.partner') == dex, (label, dex, 'selection not applied')
                assert page.locator('[data-quick-naruto][aria-pressed="true"]').count() == 1, 'ambiguous selected role'
                launch = page.evaluate(VISIBLE_PLAY)
                assert launch['visible'] and launch['hittable'], (label, dex, 'launch lost after selecting', launch)
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('dex=>G.Game.state==="playing"&&G.Game.player?.dex===dex', arg=dex)
                assert page.locator('#scr-menu').is_hidden(), 'menu overlay survived into game'
                played.append(dex)
                page.evaluate('G.Game.toUI();G.Flow.goMenu()')
                assert page.locator('.launch-detail').get_attribute('data-selected-hero') == str(dex), 'return lost chosen role'
            # A large future roster scrolls inside its grid while launch stays reachable.
            future = page.evaluate(r"""() => {
             const grid=document.querySelector('#naruto-quick-pick .naruto-grid'),original=grid.children.length;
             for(let i=original;i<12;i++){
              const card=grid.children[0].cloneNode(true);card.removeAttribute('data-quick-naruto');
              card.classList.remove('on');card.disabled=true;card.dataset.layoutSample='true';
              card.setAttribute('aria-hidden','true');grid.append(card);
             }
             grid.scrollTop=grid.scrollHeight;
             return {scrollable:grid.scrollHeight>grid.clientHeight,overflow:document.documentElement.scrollWidth>innerWidth};
            }""")
            assert future['scrollable'] and not future['overflow'], (label, 'future roster not bounded', future)
            launch = page.evaluate(VISIBLE_PLAY)
            assert launch['visible'] and launch['hittable'], (label, 'future roster displaced launch', launch)
            page.evaluate("document.querySelectorAll('[data-layout-sample]').forEach(e=>e.remove());document.querySelector('#naruto-quick-pick .naruto-grid').scrollTop=0")
            # The native secondary navigation still works after its original nodes move.
            for go, screen in [('settings', '#scr-settings'), ('dex', '#scr-dex'), ('gacha', '#scr-gacha')]:
                page.locator(f'#scr-menu [data-go="{go}"]').click()
                assert page.locator(screen).is_visible(), (label, go, 'native action lost')
                page.locator('#set-close' if go == 'settings' else f'{screen} [data-back]').click()
                assert page.locator(screen).is_hidden(), (label, go, 'native return lost')
            # Non-Naruto partners retain the original profile and can still launch.
            if label == 'desktop':
                page.evaluate('G.DB.save.partner=1;G.DB.save.starter=1;G.DB.grant(1,"starter");G.Flow.goMenu()')
                assert page.locator('#menu-partner').is_visible(), 'Pokemon fallback portrait missing'
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.state==="playing"&&G.Game.player?.dex===1')
                page.evaluate('G.Game.toUI();G.Naruto.choose(30009)')
            page.evaluate('document.querySelector("#scr-menu").scrollTop=0')
            page.screenshot(path=str(OUT / f'verified-{label}.png'))
            report['views'][label] = {'played': played, 'initialPlay': initial, 'futureRoster': future, 'secondaryNavigation': True}
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))

if __name__ == '__main__':
    main()
