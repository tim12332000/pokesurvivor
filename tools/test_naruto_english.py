"""Verify the real crossover entry in English and Traditional Chinese."""
import json
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/naruto-english'
BASE = os.environ.get('NARUTO_EN_URL', 'http://127.0.0.1:8349/.omx/digimon.html')
CHROME = os.environ.get('CHROME', r'C:\Program Files\Google\Chrome\Application\chrome.exe')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'cases': [], 'errors': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        combat_baseline = None
        for locale, mobile in [('en', False), ('zh-TW', False), ('en', True)]:
            context = browser.new_context(service_workers='block', viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile)
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(f'{BASE}?lang={locale}&hero=kimimaro' + ('' if mobile else '&layout=wide'))
            page.wait_for_function('window.G?.Naruto && document.querySelector("#boot").classList.contains("hidden")')
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.wait_for_function('!document.querySelector("#scr-menu").classList.contains("hidden")')
            page.wait_for_timeout(200)
            menu = page.locator('#scr-menu').inner_text()
            assert page.evaluate('G.DB.save.partner') == 30012
            combat = page.evaluate('''() => [...G.NarutoSkillCatalog.definitions.values()].map(d=>Object.fromEntries(Object.entries(d).filter(([k,v])=>typeof v==='number'||typeof v==='boolean'||k==='id')))''')
            if combat_baseline is None:
                combat_baseline = combat
            assert combat == combat_baseline, 'Localization changed combat values'
            if locale == 'en':
                assert 'Kimimaro' in menu
                assert not re.search(r'[\u3400-\u9fff]', menu), menu
                definitions = page.evaluate('''() => [...G.NarutoSkillCatalog.definitions.values()].map(d=>({id:d.id,name:G.I18n.t(d.name),desc:G.I18n.t(d.desc),upgrades:(d.ups||[]).map(u=>G.I18n.t(u.t))}))''')
                leftovers = [item for item in definitions if re.search(r'[\u3400-\u9fff]', json.dumps(item, ensure_ascii=False))]
                (OUT / 'untranslated-skills.json').write_text(json.dumps(leftovers, ensure_ascii=False, indent=2), encoding='utf-8')
                assert not leftovers, json.dumps(leftovers, ensure_ascii=False)
                page.screenshot(path=str(OUT / ('menu-en-mobile.png' if mobile else 'menu-en.png')))
                page.locator('#btn-naruto').click()
                page.locator('#naruto-skill-guide').click()
                guide = page.locator('#scr-naruto-skills').inner_text()
                untranslated = [line for line in guide.splitlines() if re.search(r'[\u3400-\u9fff]', line)]
                (OUT / 'untranslated-guide.json').write_text(json.dumps(untranslated, ensure_ascii=False, indent=2), encoding='utf-8')
                assert not untranslated, 'Untranslated guide text: see .omx/state/naruto-english/untranslated-guide.json'
                page.locator('#naruto-skills-close').click()
                page.locator('#naruto-close').click()
                page.locator('#scr-menu [data-go="gacha"]').click()
                page.locator('#gacha-gens [data-gen="11"]').click()
                page.wait_for_timeout(300)
                gacha = page.locator('#banner-desc').inner_text()
                assert not re.search(r'[\u3400-\u9fff]', gacha), gacha
                page.evaluate('G.Flow.goMenu()')
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.state==="playing" && G.Game.player?.dex===30012')
                page.wait_for_timeout(200)
                page.evaluate('G.Game.togglePause()')
                page.wait_for_timeout(100)
                pause = page.locator('#scr-pause').inner_text()
                assert not re.search(r'[\u3400-\u9fff]', pause), pause
            else:
                assert '君麻呂' in menu and '選擇出戰角色' in menu
            report['cases'].append({'locale': locale, 'mobile': mobile, 'menu': menu})
            context.close()
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    assert not report['errors'], report['errors']
    print('English menus, all Naruto skill definitions, guide, gacha, hero link and Traditional Chinese passed.')


if __name__ == '__main__':
    main()
