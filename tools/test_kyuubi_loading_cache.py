"""Normal-entry Naruto must not reuse the pre-directional metadata cache key."""
import json
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME

ROOT = Path(__file__).resolve().parents[1]
URL = 'http://127.0.0.1:8318/.omx/portrait.html?lang=zh-TW&hero=naruto&v=kyuubi-directions'


def main():
    stale = json.loads((ROOT / 'art-review/kyuubi-frames.json').read_text(encoding='utf-8'))
    stale.pop('directional', None)
    stale_hits = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page(viewport={'width': 390, 'height': 850}, service_workers='block')

        def route(request):
            if not urlsplit(request.request.url).query:
                stale_hits.append(request.request.url)
                request.fulfill(status=200, content_type='application/json', body=json.dumps(stale))
            else:
                request.continue_()

        page.route('**/art-review/kyuubi-frames.json*', route)
        page.goto(URL)
        page.wait_for_selector('#portrait-game')
        frame = page.locator('#portrait-game').element_handle().content_frame()
        frame.wait_for_function('window.PS_REDRAWN_READY && document.getElementById("boot").classList.contains("hidden")')
        if frame.locator('#tap-start').is_visible():
            frame.locator('#tap-start').click()
        frame.evaluate("""async()=>{await PS_REDRAWN_READY;await KyuubiForm.load();
          await G.Flow.play();if(G.Game.player?.dex!==30001)throw Error('Naruto failed normal entry');
          if(!G.KyuubiForm.directionalImage)throw Error('directional art unavailable');
        }""")
        assert not stale_hits, stale_hits
        browser.close()
    print('PASS: normal mobile entry ignores obsolete unversioned cloak metadata cache')


if __name__ == '__main__':
    main()
