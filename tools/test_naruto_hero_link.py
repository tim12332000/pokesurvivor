"""Native URL preselection, saved preferences and demand-loaded hero families."""
import json
import os
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

from playwright.sync_api import sync_playwright
import test_naruto_lazy_loading as loading

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/naruto-hero-link'
BASE = os.environ.get('HERO_LINK_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW')
LABEL = os.environ.get('HERO_LINK_LABEL', 'normal')


def url(hero):
    parts = urlsplit(BASE)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k != 'hero']
    if hero is not None:
        query.append(('hero', hero))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def menu(page):
    if page.locator('#tap-start').is_visible():
        page.locator('#tap-start').click()
    page.wait_for_function('!document.querySelector("#scr-menu").classList.contains("hidden")')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': BASE, 'errors': [], 'cases': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=loading.CHROME, headless=True)
        for hero, dex, prefix in [('tenten',30009,'tenten-'), ('naruto',30001,'naruto-'),
                                  ('sasuke',30002,'sasuke-'), ('lee',30006,'lee-'),
                                  ('gaara',30007,'gaara-'), ('30009',30009,'tenten-'),
                                  ('天天',30009,'tenten-'), (' SASUKE ',30002,'sasuke-')]:
            loading.URL = url(hero)
            context, page, requests, _ = loading.session(browser, report['errors'])
            assert page.evaluate('G.DB.save.partner') == dex, hero
            assert not [r for r in requests if loading.atlas(r)], 'downloaded hero atlases before selection UI'
            menu(page)
            assert page.locator(f'[data-quick-naruto="{dex}"]').get_attribute('aria-pressed') == 'true'
            loading.start(page, dex)
            files = [urlsplit(r).path.rsplit('/', 1)[-1] for r in requests if loading.atlas(r)]
            assert files and all(f.startswith(prefix) or dex==30001 and f=='one-tail-v2.png' for f in files), files
            report['cases'].append({'hero': hero, 'dex': dex, 'files': files})
            if hero == 'tenten':
                page.screenshot(path=str(OUT / f'{LABEL}-tenten-start.png'))
                # The link selects a default, it never locks later user choices.
                page.evaluate('G.Game.toUI();G.Naruto.choose(30007)')
                page.evaluate('() => G.DB.ready()')
                assert page.evaluate('G.DB.save.partner') == 30007
                assert page.locator('[data-quick-naruto="30007"]').get_attribute('aria-pressed') == 'true'
                # Invalid/hidden hero names preserve the saved partner.
                for invalid in ['itachi', '30008', 'no-such-hero', '']:
                    page.goto(url(invalid))
                    page.wait_for_function('window.G?.NarutoAssets && document.querySelector("#boot").classList.contains("hidden")')
                    assert page.evaluate('G.DB.save.partner') == 30007, invalid
                # A new explicit link overrides a returning player's last partner.
                page.goto(url('tenten'))
                page.wait_for_function('window.G?.NarutoAssets && document.querySelector("#boot").classList.contains("hidden")')
                assert page.evaluate('G.DB.save.partner') == 30009
                report['manualSwitchAndSavedOverride'] = True
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / f'{LABEL}-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True, 'cases':len(report['cases']), 'label':LABEL}))


if __name__ == '__main__':
    main()
