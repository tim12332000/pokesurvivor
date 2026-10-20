"""Verify local preview cache versions and the visible three-character picker."""
import hashlib
import json
from pathlib import Path
import re

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/sandbox-cache'


def main():
    html = (ROOT / '.omx/digimon.html').read_text('utf-8')
    sources = re.findall(r'<script\b[^>]*src="([^"]+)"', html)
    local = [source for source in sources if not source.startswith(('http:', 'https:'))]
    for source in local:
        path, version = source.split('?v=')
        assert version == hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:12], source
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        context = browser.new_context(locale='zh-TW', viewport={'width':1280,'height':900})
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        for visit in range(2):
            page.goto('http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&v=lee-picker-fix')
            page.wait_for_function("window.G?.Naruto && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            cards = page.locator('#naruto-quick-pick [data-quick-naruto]')
            assert cards.count() == 3, cards.all_text_contents()
            page.locator('[data-quick-naruto="30006"]').click()
            assert page.evaluate('G.DB.save.partner') == 30006
        page.screenshot(path=str(OUT / 'three-character-picker.png'), full_page=True)
        assert not errors, errors
        print(json.dumps({'ok':True,'versionedScripts':len(local),'cards':cards.all_text_contents(),
                          'serviceWorker':page.evaluate('!!navigator.serviceWorker.controller')}, ensure_ascii=False))
        browser.close()


if __name__ == '__main__':
    main()
