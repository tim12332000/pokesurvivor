"""Sharingan upgrade cards preview the resulting stage in icon and title."""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/sharingan-upgrade-cards'
URL = os.environ.get('SHARINGAN_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&hero=sasuke')
CHROME = os.environ.get('CHROME', r'C:\Program Files\Google\Chrome\Application\chrome.exe')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, viewport in [('desktop', {'width': 1200, 'height': 900}),
                                ('mobile', {'width': 390, 'height': 844})]:
            context = browser.new_context(viewport=viewport, is_mobile=label == 'mobile',
                                          has_touch=label == 'mobile', service_workers='block')
            outer = context.new_page()
            outer.on('pageerror', lambda error: report['errors'].append(str(error)))
            outer.goto(URL)
            outer.wait_for_function("window.G?.SharinganIcons || document.querySelector('#portrait-game')?.contentWindow?.G?.SharinganIcons")
            page = next(frame for frame in outer.frames if frame.evaluate('!!window.G?.SharinganIcons'))
            page.wait_for_function("document.querySelector('#boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30002 && G.Game.state==="playing"')
            page.evaluate('G.Game.togglePause();G.Game.player.level=6')
            page.evaluate("G.Game.player.addMove('naruto-sharingan')")
            results = []
            for level in range(1, 5):
                result = page.evaluate("""level => {
                  const p=G.Game.player,id='naruto-sharingan',m=p.moves.find(m=>m.id===id);
                  if(m.lvl!==level)throw Error('Previous selection did not upgrade the skill');
                  const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);
                  if(!card)throw Error('Missing Sharingan upgrade');
                  const next=G.Moves.instance(id,level+1);
                  G.RunUI.showLevelUp(p.level,[card],picked=>picked.apply(p));
                  return {title:card.title,expectedTitle:next.name,desc:card.desc,
                    expectedIcon:G.Icons.url('sharingan-'+(level+1)),
                    learnedIcon:G.Icons.url('sharingan-'+level),
                    currentIcon:G.Icons.url('move:'+id)};
                }""", level)
                card = page.locator('#cards .card').first
                assert card.locator('img').get_attribute('src') == result['expectedIcon'], (label, level, 'wrong preview icon')
                assert result['currentIcon'] == result['learnedIcon'], 'Preview changed the learned skill icon'
                if level == 2:
                    card.wait_for(state='visible')
                    outer.screenshot(path=str(OUT / f'{label}-two-to-three.png'), animations='disabled')
                assert result['title'] == result['expectedTitle'], (label, level, result['title'], result['expectedTitle'])
                assert result['expectedTitle'] in card.locator('.nm').inner_text()
                card.click()
                assert page.evaluate("G.Game.player.moves.find(m=>m.id==='naruto-sharingan').lvl") == level + 1
                results.append({'from': level, 'to': level + 1, 'title': result['title'], 'desc': result['desc']})
            assert not page.evaluate("G.LevelUp.offer(G.Game.player,100).some(c=>c.key==='up:naruto-sharingan')"), 'Max stage still offered'
            report['viewports'][label] = results
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, **report}, ensure_ascii=False))


if __name__ == '__main__':
    main()
