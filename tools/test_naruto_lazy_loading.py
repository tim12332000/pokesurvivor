"""Exercise native Naruto loading boundaries, retries and races in Chromium."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/naruto-lazy-loading'
URL = os.environ.get('NARUTO_LOADING_URL', os.environ.get('TENTEN_URL',
    'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW'))
CHROME = os.environ.get('CHROME', r'C:\Program Files\Google\Chrome\Application\chrome.exe')
LABEL = os.environ.get('NARUTO_LOADING_LABEL', 'normal')
PLAY = '#scr-menu [data-go="play"]'


def atlas(url):
    return '/art-review/redrawn/' in url and urlsplit(url).path.endswith('.png')


def session(browser, errors, mobile=False):
    context = browser.new_context(service_workers='block', viewport={'width': 390, 'height': 844} if mobile else {'width': 1200, 'height': 900}, is_mobile=mobile, has_touch=mobile)
    page = context.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    requests, finished = [], []
    page.on('request', lambda request: requests.append(request.url))
    cdp = context.new_cdp_session(page)
    cdp.send('Network.enable')
    cdp.send('Network.setCacheDisabled', {'cacheDisabled': True})
    cdp.on('Network.loadingFinished', lambda event: finished.append(event['encodedDataLength']))
    page.goto(URL)
    page.wait_for_function('window.G?.NarutoAssets && document.querySelector("#boot").classList.contains("hidden")')
    return context, page, requests, finished


def enter_menu(page, dex):
    page.evaluate('(dex)=>{G.DB.save.partner=G.DB.save.starter=dex;G.DB.save.partnerShiny=false;}', dex)
    page.locator('#tap-start').click()
    page.wait_for_function('document.querySelector("#scr-menu") && !document.querySelector("#scr-menu").classList.contains("hidden")')


def start(page, dex):
    page.locator(PLAY).click()
    page.wait_for_function('(dex)=>G.Game.state==="playing" && G.Game.player?.dex===dex && G.NarutoAssets.ready(dex)', arg=dex)


def released(routes):
    while routes:
        routes.pop().continue_()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'errors': [], 'checks': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            context, page, requests, sizes = session(browser, report['errors'])
            assert not any(atlas(url) for url in requests), 'full atlas requested before tap'
            assert not page.evaluate('AnimationAssets.ready'), 'all-atlas ready before tap'
            report['checks']['beforeTap'] = {'requests': len(requests), 'transferredBytes': sum(sizes), 'atlases': 0}
            enter_menu(page, 30009)
            page.wait_for_function('G.Naruto.availableDexes.every(d=>G.Naruto.records.get(d).previewImage?.naturalWidth>0)')
            portraits = page.evaluate('G.Naruto.availableDexes.map(d=>({dex:d,source:G.Naruto.records.get(d).previewImage.src}))')
            assert len(portraits) == 5 and all('/naruto/portraits/' in p['source'] for p in portraits)
            start(page, 30009)
            page.evaluate('G.Game.togglePause()')
            sources = page.evaluate('[...new Set(AnimationAssets.keys.map(k=>AnimationAssets.get(k)).filter(a=>a.image).map(a=>a.source))]')
            assert sources and all('/tenten-' in source for source in sources), sources
            assert not any('one-tail' in url for url in requests)
            assert page.evaluate('AnimationAssets.keys.filter(k=>k.startsWith("tenten-")).every(k=>!!AnimationAssets.get(k).image)')
            assert page.evaluate('''()=>{const c=document.createElement('canvas');c.width=c.height=300;const before=G.AnimationLab.counters.source,drawn=G.AnimationLab.counters.candidate;G.Game.player.anim.draw(c.getContext('2d'),150,250);return G.AnimationLab.counters.source===before&&G.AnimationLab.counters.candidate===drawn+1;}'''), 'selected actor fell back to legacy render'
            sync = page.evaluate('''()=>{G.Game.toUI();G.Flow.goMenu();const result=G.Flow.play();const ok=G.Game.state==='playing'&&G.Game.player.dex===30009&&!(result instanceof Promise);G.Game.togglePause();return ok;}''')
            assert sync, 'cached restart lost synchronous fast path'
            before = len(requests)
            page.evaluate('Promise.all([G.NarutoAssets.ensure(30009),G.NarutoAssets.ensure(30009)])')
            assert len(requests) == before, 'cached ensure downloaded again'
            report['checks']['tenten'] = {'portraits': portraits, 'sources': sources, 'cachedRestartSynchronous': sync,
                                          'requests': len(requests), 'transferredBytes': sum(sizes)}
            page.screenshot(path=str(OUT / f'{LABEL}-tenten-ready.png'))
            # No-argument load remains the deliberate lab all-atlas boundary.
            page.evaluate('AnimationAssets.load()')
            assert page.evaluate('AnimationAssets.ready && AnimationAssets.keys.every(k=>!!AnimationAssets.get(k).image)')
            report['checks']['labFullPreload'] = True
            context.close()

            context, page, requests, _ = session(browser, report['errors'], mobile=True)
            enter_menu(page, 30009)
            page.wait_for_function('G.Naruto.availableDexes.every(d=>G.Naruto.records.get(d).previewImage?.naturalWidth>0)')
            page.wait_for_timeout(100)
            pixels = page.evaluate('''()=>[...document.querySelectorAll('#naruto-quick-pick canvas')].map(c=>{const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0,edge=0;for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++)if(d[(y*c.width+x)*4+3]){n++;if(!x||!y||x===c.width-1||y===c.height-1)edge++;}return {pixels:n,edge};})''')
            assert len(pixels) == 5 and all(p['pixels'] > 100 and p['edge'] == 0 for p in pixels), pixels
            page.screenshot(path=str(OUT / f'{LABEL}-mobile-menu.png'), full_page=True)
            report['checks']['mobilePortraits'] = pixels
            context.close()

            context, page, requests, _ = session(browser, report['errors'])
            enter_menu(page, 1)
            assert page.evaluate("()=>{const result=G.Flow.play();return G.Game.player?.dex===1&&G.Game.state==='playing'&&!(result instanceof Promise);}")
            assert not any(atlas(url) for url in requests), 'Pokemon requested reviewed atlases'
            report['checks']['pokemonSynchronous'] = True
            context.close()

            # Hold only Tenten atlas requests while selecting a different actor.
            context, page, requests, _ = session(browser, report['errors'])
            held = []
            page.route('**/art-review/redrawn/tenten-*.png', lambda route: held.append(route))
            enter_menu(page, 30009)
            page.locator(PLAY).click()
            page.wait_for_function('document.querySelector("[data-go=play]").getAttribute("aria-busy")==="true"')
            page.locator('[data-quick-naruto="30002"]').click()
            released(held)
            page.wait_for_function('G.NarutoAssets.ready(30009) && G.NarutoAssets.ready(30002)')
            assert page.evaluate('G.Game.state==="ui" && G.DB.save.partner===30002'), 'stale Tenten completion started run'
            start(page, 30002)
            report['checks']['selectionRace'] = True
            context.close()

            context, page, requests, _ = session(browser, report['errors'])
            held = []
            page.route('**/art-review/redrawn/tenten-*.png', lambda route: held.append(route))
            enter_menu(page, 30009)
            page.locator(PLAY).click()
            page.wait_for_function('document.querySelector("[data-go=play]").getAttribute("aria-busy")==="true"')
            page.locator('#scr-menu [data-go="settings"]').click()
            released(held)
            page.wait_for_function('G.NarutoAssets.ready(30009) && !document.querySelector("[data-go=play]").hasAttribute("aria-busy")')
            assert page.evaluate('G.Game.state==="ui"'), 'loading launched after navigation away'
            assert page.locator('#scr-settings').is_visible()
            report['checks']['navigationRace'] = True
            context.close()

            # Abort one native request. Failed launch must return to a retryable menu.
            context, page, requests, _ = session(browser, report['errors'])
            held, intercepted = [], {'count': 0}
            def fail_once(route):
                if intercepted['count'] == 0:
                    intercepted['count'] += 1
                    held.append(route)
                else:
                    route.continue_()
            page.route('**/art-review/redrawn/tenten-*.png', fail_once)
            enter_menu(page, 30009)
            page.locator(PLAY).click()
            page.wait_for_function('document.querySelector("[data-go=play]").getAttribute("aria-busy")==="true"')
            assert held, 'failure fixture did not intercept atlas'
            held.pop().abort('failed')
            page.wait_for_function('!document.querySelector("[data-go=play]").hasAttribute("aria-busy")')
            assert page.evaluate('G.Game.state==="ui" && !G.NarutoAssets.ready(30009)')
            start(page, 30009)
            report['checks']['failureRetry'] = True
            context.close()

            for dex, prefix in [(30001, 'naruto-'), (30006, 'lee-')]:
                context, page, requests, _ = session(browser, report['errors'])
                held = []
                page.route(f'**/art-review/redrawn/{prefix}*.png', lambda route: held.append(route))
                enter_menu(page, dex)
                page.evaluate('(dex)=>{window.loadingA=G.NarutoAssets.ensure(dex);window.loadingB=G.NarutoAssets.ensure(dex);}', dex)
                assert page.evaluate('window.loadingA===window.loadingB'), 'concurrent ensure not deduplicated'
                page.locator(PLAY).click()
                assert page.evaluate('G.Game.state==="ui"'), 'cold start entered gameplay early'
                released(held)
                page.wait_for_function('(dex)=>G.Game.state==="playing" && G.NarutoAssets.ready(dex)', arg=dex)
                page.evaluate('G.Game.togglePause()')
                count = len([url for url in requests if atlas(url)])
                if dex == 30001:
                    assert page.evaluate('!!KyuubiForm.image'), 'Naruto form not ready before combat'
                    page.evaluate('''()=>{const p=G.Game.player;p.addMove('naruto-nine-tails-cloak');p.target=null;const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},p.x+30,p.y,{hp:1,spd:1,dmg:1});G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();G.NarutoSupport.cast(p,p.moves.find(m=>m.id==='naruto-nine-tails-cloak'));}''')
                    assert page.evaluate('G.KyuubiForm.active(G.Game.player)'), 'native nine-tail did not activate'
                else:
                    page.evaluate("G.Game.player.addMove('naruto-gates')")
                    assert page.evaluate('G.AnimationLab.stateFor(G.Game.player.anim).key.startsWith("lee-opened-") && AnimationAssets.keys.filter(k=>k.startsWith("lee-opened-")).every(k=>!!AnimationAssets.get(k).image)')
                assert len([url for url in requests if atlas(url)]) == count, 'first transformation requested new atlases'
                paths = [urlsplit(url).path for url in requests if atlas(url)]
                assert len(paths) == len(set(paths)), 'duplicate atlas requests'
                report['checks'][str(dex)] = {'transformationReady': True, 'concurrentDedup': True, 'atlases': paths}
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        prior = ROOT / '.omx/state/loading-audit/report.json'
        if prior.exists():
            old = json.loads(prior.read_text(encoding='utf-8'))
            report['previousColdBootBytes'] = old['transferredBytes']
        report['ok'] = True
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        (OUT / f'{LABEL}-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
