"""Native picker loading-order, readiness, retry and selection-race regressions.

Run tools/serve_animation_lab.py --port 8004 first. No production hooks are
replaced; only the network is delayed/failed to exercise actual user paths.
"""
import json
import os
import time
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/naruto-loading'
URL = os.environ.get('NARUTO_LOADING_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW')
PLAY = '#scr-menu [data-go="play"]'


def hero_asset(url):
    path = urlsplit(url).path
    if '/redrawn/' not in path or not path.endswith('.png'):
        return None
    for hero in ('pain', 'temari', 'naruto', 'sasuke', 'lee', 'gaara', 'tenten'):
        if path.rsplit('/', 1)[-1].startswith(hero + '-'):
            return hero
    if path.endswith('/one-tail-v2.png'):
        return 'naruto'
    return None


class Trace:
    def __init__(self, page):
        self.events = []
        self.start = time.monotonic()
        page.on('request', self.request)

    def request(self, request):
        if request.resource_type == 'image' or '-frames.json' in request.url:
            self.events.append({'ms': round((time.monotonic()-self.start)*1000),
                                'url': request.url, 'hero': hero_asset(request.url)})

    def heroes(self):
        return sorted({event['hero'] for event in self.events if event['hero']})


def enter(page, mobile=False, hero=None):
    url = URL + ('&layout=wide' if not mobile and 'layout=' not in URL else '')
    if hero:
        url += '&hero=' + hero
    page.goto(url)
    page.wait_for_function("window.G?.Naruto && document.getElementById('boot').classList.contains('hidden')", polling=20)
    if page.locator('#tap-start').is_visible():
        page.locator('#tap-start').click()
    page.locator('[data-quick-naruto="30011"]').wait_for(state='visible')


def select(page, dex):
    page.locator(f'[data-quick-naruto="{dex}"]').click()
    page.wait_for_function('(dex)=>+document.querySelector(".launch-detail").dataset.selectedHero===dex', arg=dex, polling=20)


def ready(page, dex):
    page.wait_for_function('(dex)=>G.Naruto.records.get(dex).ready && !document.querySelector("#scr-menu [data-go=play]").disabled', arg=dex, polling=20)


def preview(page, label):
    """Inspect actual selected full-body canvas, excluding translucent shadow."""
    result = page.locator('.launch-portrait canvas').evaluate('''canvas=>{
      const data=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;
      let minX=canvas.width,minY=canvas.height,maxX=-1,maxY=-1,pixels=0;
      for(let y=0;y<canvas.height;y++)for(let x=0;x<canvas.width;x++){
        const i=(y*canvas.width+x)*4;if(data[i+3]<210)continue;
        pixels++;minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);
      }return {width:canvas.width,height:canvas.height,pixels,bounds:[minX,minY,maxX,maxY]};}''')
    assert result['pixels'] > 300, result
    x0, y0, x1, y1 = result['bounds']
    assert 0 < x0 < x1 < result['width']-1 and 0 < y0 < y1 < result['height']-1, result
    assert y1-y0 > result['height']*.5, result
    page.locator('#scr-menu').screenshot(path=str(OUT / (label+'.png')))
    return result


def baseline(browser):
    context = browser.new_context(viewport={'width':1280,'height':900}, service_workers='block')
    page = context.new_page()
    trace = Trace(page)
    enter(page)
    page.wait_for_timeout(1000)
    before = len(trace.events)
    select(page, 30011)
    page.wait_for_timeout(1000)
    result = {'preselect':trace.events[:before], 'postselect':trace.events[before:], 'heroes':trace.heroes()}
    context.close()
    return result


def context_for(browser, mobile=False, saved=None):
    context = browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},
                                  is_mobile=mobile, has_touch=mobile, service_workers='block')
    if saved is not None:
        # The installed personal build restores its own sandbox key before boot.
        data = json.dumps(saved, ensure_ascii=False)
        context.add_init_script("""(() => {
          const save=SAVE_DATA;
          localStorage.setItem('ps.sandbox.digimon.v1',JSON.stringify(save));
        })();""".replace('SAVE_DATA', data))
    return context


def native_start(page):
    page.locator(PLAY).click()
    page.wait_for_function('G.Game.state==="playing" && G.Game.player?.dex===30011', polling=20)
    assert page.evaluate('G.TemariArt.loaded && G.Naruto.records.get(30011).ready')


def selected_only(browser, mobile=False, saved=None):
    context = context_for(browser, mobile, saved)
    page = context.new_page()
    trace = Trace(page)
    enter(page, mobile)
    initial = page.evaluate('G.DB.save.partner')
    page.wait_for_timeout(180)
    assert trace.heroes() == [], 'menu downloaded full atlases before any card action: '+str(trace.events)
    assert not any('/digimon/pixel/' in event['url'] for event in trace.events), 'hidden Digimon eagerly loaded'
    assert page.locator(f'[data-quick-naruto="{initial}"]').get_attribute('data-asset-state') == 'idle'
    if saved is None:
        assert initial == 30001, initial
        assert 'pain' not in trace.heroes() and 'temari' not in trace.heroes(), trace.events
        select(page, 30011)
    else:
        assert initial == 30011, initial
    page.wait_for_timeout(180)
    assert set(trace.heroes()) <= {'temari'}, trace.events
    native_start(page)
    assert trace.heroes() == ['temari'], trace.events
    # Return through the actual menu, retaining its native preview registration.
    page.evaluate('G.Flow.goMenu()')
    page.locator('.launch-portrait canvas').wait_for(state='visible')
    page.wait_for_timeout(120)
    assert page.locator('[data-quick-naruto="30011"]').get_attribute('data-asset-state') == 'ready'
    assert '已下載' in page.locator('[data-quick-naruto="30011"] .naruto-selection').inner_text()
    result = {'initial':initial,'heroes':trace.heroes(),
              'preview':preview(page, ('mobile' if mobile else 'desktop')+('-saved' if saved else '-fresh')),
              'requests':trace.events}
    saved_temari = page.evaluate('JSON.parse(JSON.stringify(G.DB.save))')
    native_start(page)
    result['startedDex'] = page.evaluate('G.Game.player.dex')
    context.close()
    return result, saved_temari


def pending_selection(browser):
    context = context_for(browser)
    page = context.new_page()
    held = []
    page.route('**/temari-common-*.png*', lambda route: held.append(route))
    enter(page)
    select(page, 30011)
    page.wait_for_timeout(120)
    assert held, 'character card failed to initiate its selected asset download'
    assert page.locator('[data-quick-naruto="30011"]').get_attribute('data-asset-state') == 'loading'
    assert '下載中' in page.locator('[data-quick-naruto="30011"] .naruto-selection').inner_text()
    if page.locator(PLAY).is_enabled(): page.locator(PLAY).click()
    page.wait_for_function('!G.TemariArt.loaded', polling=20)
    page.wait_for_timeout(120)
    assert held, 'selected Temari did not request her common atlas'
    if page.locator(PLAY).is_enabled():
        page.locator(PLAY).click()
    assert page.locator(PLAY).is_disabled(), 'start was enabled before chosen hero decoded'
    assert page.evaluate('G.Game.state') != 'playing'
    select(page, 30010)
    for route in held:
        route.continue_()
    page.wait_for_function('G.TemariArt.loaded', polling=20)
    page.wait_for_timeout(120)
    assert page.evaluate('G.DB.save.partner') == 30010, 'stale Temari load reselected the old hero'
    assert page.locator('.launch-detail').get_attribute('data-selected-hero') == '30010'
    assert page.evaluate('G.Game.state') == 'ui', 'stale Temari completion unexpectedly started a run'
    assert page.locator(PLAY).is_enabled(), 'stale completion disabled the newly ready hero'
    page.locator(PLAY).click()
    page.wait_for_function('G.Game.state==="playing" && G.Game.player?.dex===30010', polling=20)
    context.close()
    return {'blockedStart':True,'staleCompletionKeptDex':30010}


def selected_retry(browser):
    context = context_for(browser)
    page = context.new_page()
    requests = []

    def fail_once(route):
        requests.append(route.request.url)
        if len(requests) == 1:
            route.fulfill(status=503, content_type='text/plain', body='selected atlas retry fixture')
        else:
            route.continue_()

    page.route('**/temari-common-*.png*', fail_once)
    enter(page)
    select(page, 30011)
    if page.locator(PLAY).is_enabled(): page.locator(PLAY).click()
    page.wait_for_timeout(250)
    assert requests, 'failure fixture did not intercept the selected hero'
    # Starting/retrying through the normal action must recover the failed atlas.
    if page.locator(PLAY).is_enabled() and page.evaluate('G.Game.state') != 'playing':
        page.locator(PLAY).click()
    ready(page, 30011)
    if page.evaluate('G.Game.state') != 'playing':
        native_start(page)
    assert page.evaluate('G.Game.player.dex') == 30011
    assert len(requests) >= 2, 'failed selected atlas was never retried'
    context.close()
    return {'failedThenRetried':len(requests),'startedDex':30011}


def explicit_digimon_preload(browser):
    context = context_for(browser)
    page = context.new_page()
    trace = Trace(page)
    enter(page)
    assert not any('/digimon/pixel/' in event['url'] for event in trace.events)
    page.evaluate('G.Sprites.preload([20001])')
    page.evaluate('G.Sprites.preload([20001])')
    requests = [event['url'] for event in trace.events if '/digimon/pixel/' in event['url']]
    assert len(requests) == 1 and requests[0].split('?')[0].endswith('/agumon.png'), requests
    assert page.evaluate('G.Digimon.records.get(20001).ready')
    context.close()
    return {'requests':requests,'repeatedPreloadShared':True}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=CHROME, headless=True)
        if os.environ.get('NARUTO_LOADING_BASELINE') == '1':
            report = {'baseline':baseline(browser)}
        else:
            fresh, saved = selected_only(browser)
            report = {'desktopFresh':fresh,
                      'desktopSaved':selected_only(browser, saved=saved)[0],
                      'mobileFresh':selected_only(browser, mobile=True)[0],
                      'mobileSaved':selected_only(browser, mobile=True, saved=saved)[0],
                      'pendingSelection':pending_selection(browser),
                      'selectedRetry':selected_retry(browser),
                      'explicitDigimonPreload':explicit_digimon_preload(browser)}
        (OUT / 'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        browser.close()
    print(json.dumps({'report':str(OUT/'report.json'),'checks':list(report),'passed':True},ensure_ascii=False))


if __name__ == '__main__':
    main()
