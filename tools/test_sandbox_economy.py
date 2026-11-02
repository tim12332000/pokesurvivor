"""Normal currency spending and migration of former unlimited sandbox saves."""
import mimetypes
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&layout=wide'
KEY = 'ps.sandbox.digimon.v1'


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            headless=True)
        context = browser.new_context(service_workers='block')

        def route(request):
            path = unquote(urlsplit(request.request.url).path).removeprefix('/pokesurvivor/')
            file = ROOT / path
            request.fulfill(status=200 if file.is_file() else 404,
                            body=file.read_bytes() if file.is_file() else b'Not found',
                            content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')

        context.route('https://tim12332000.github.io/pokesurvivor/**', route)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))

        def load():
            page.goto(URL)
            page.wait_for_function('typeof G !== "undefined" && G.DB.save && document.getElementById("boot").classList.contains("hidden")')
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()

        load()
        balances = page.evaluate('[G.DB.save.coins,G.DB.save.tickets.t1,G.DB.save.tickets.t10]')
        assert 500 <= balances[0] < 1000000000 and all(0 <= n < 1000000000 for n in balances[1:]), balances
        assert page.locator('#sandbox-badge').count() == 0
        page.evaluate("""() => {
            G.Naruto.choose(30001);
            G.MenuUI.open();
            G.DB.save.coins = 1000000000;
            G.DB.save.tickets = {t1:1000000000,t10:1000000000};
            G.DB.save.pity[1] = 12;
            G.DB.commit();
        }""")
        load()
        assert page.evaluate('[G.DB.save.coins,G.DB.save.tickets.t1,G.DB.save.tickets.t10]') == [500, 0, 0]
        assert page.evaluate('G.DB.save.partner === 30001 && G.DB.save.pity[1] === 12 && G.DB.owns(30001)')
        page.locator('#scr-menu [data-go="upgrades"]').click()
        before = page.evaluate('G.DB.save.coins')
        page.locator('[data-buy]:enabled').first.click()
        after = page.evaluate('G.DB.save.coins')
        assert 0 <= after < before
        page.evaluate('G.DB.commit()')
        load()
        assert page.evaluate('G.DB.save.coins') == after
        result = page.evaluate("""() => {
            const s=G.DB.save;
            s.tickets={t1:11,t10:1};
            const blocked=[G.Gacha.pull(s,1,1,'t1'),
                G.Gacha.pull(s,10,1,'t1'),G.Gacha.pull(s,10,1,'t10')];
            G.GachaUI.open();G.DB.commit();
            return {blocked,t1:s.tickets.t1,t10:s.tickets.t10,open:G.UI.isOpen('scr-gacha')};
        }""")
        assert result == {'blocked': [None, None, None], 't1': 11, 't10': 1, 'open': False}, result
        page.evaluate("""() => {
            G.DB.grant(1,'starter');G.DB.grant(20001,'starter');
            G.DB.save.pupg[1]={hp:2};
            G.DB.save.partner=G.DB.save.starter=1;G.DB.commit();
        }""")
        load()
        assert page.evaluate('G.DB.save.partner') == 30001
        assert page.evaluate('G.DB.owns(1) && G.DB.save.pupg[1].hp===2')
        assert page.evaluate('G.Catalog.playable().every(p=>p.naruto) && G.Catalog.starters().every(p=>G.Naruto.availableDexes.includes(p.dex))')
        assert page.locator('#scr-menu [data-go="dex"]').is_hidden()
        assert page.locator('#scr-menu [data-go="gacha"]').is_hidden()
        page.evaluate("G.UI.show('scr-dex');G.UI.show('scr-gacha')")
        assert page.locator('#scr-dex').is_hidden()
        assert page.locator('#scr-gacha').is_hidden()
        page.locator('#scr-menu [data-go="upgrades"]').click()
        options=page.locator('#upg-mon option').evaluate_all('(els)=>els.map(el=>+el.value)')
        assert options and all(d in page.evaluate('G.Naruto.availableDexes') for d in options), options
        page.select_option('#upg-mon','30002')
        coins=page.evaluate('G.DB.save.coins')
        page.locator('[data-buy]:enabled').first.click()
        assert page.evaluate('G.DB.save.coins') < coins
        assert page.evaluate('Object.keys(G.DB.save.pupg[30002]).length>0 && G.DB.save.pupg[1].hp===2')
        page.evaluate('G.MenuUI.open()')
        assert page.locator('#scr-menu .logo .t1').inner_text() == 'Naruto Survivor'
        assert 'Naruto Survivor' in page.title()
        assert '/pokesurvivor/.omx/digimon.html' in page.url
        out=ROOT/'.omx/state/naruto-only'
        out.mkdir(parents=True,exist_ok=True)
        page.screenshot(path=str(out/'desktop.png'))
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path=str(out/'mobile.png'))
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.evaluate('G.Progress.checkAch();G.DB.save.tickets={t1:7,t10:2};G.DB.commit()')
        expected_coins = page.evaluate('G.DB.save.coins')
        load()
        assert page.evaluate('[G.DB.save.coins,G.DB.save.tickets.t1,G.DB.save.tickets.t10]') == [expected_coins, 7, 2]
        assert page.evaluate(f"localStorage.getItem('{KEY}') !== null")
        assert not errors, errors
        browser.close()
    print('PASS: normal economy, old-save migration, Naruto-only roster/upgrades, blocked collection/gacha, preserved progress, desktop/mobile branding, unchanged URL, reload persistence; JS errors: 0')


if __name__ == '__main__':
    main()

