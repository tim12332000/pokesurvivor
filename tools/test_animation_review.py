"""Verify the isolated export with the real curated images and review controls."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8317/art-review/index.html')
    page.wait_for_function("document.querySelectorAll('.card').length===4")
    page.locator('.card').last.scroll_into_view_if_needed()
    page.wait_for_function("[...document.images].every(i=>i.complete&&i.naturalWidth>0)")
    assert 'feat/animation-presentation-lab' in page.locator('#branch').inner_text()
    page.locator('#character').select_option('佐助');assert page.locator('.card').count()==2
    page.locator('#character').select_option('鳴人');assert page.locator('.card').count()==2
    page.locator('#character').select_option('all')
    first=page.locator('.card').first
    first.locator('[data-decision=revise]').click()
    first.locator('textarea').fill('QA: preserve poses, reduce lightning')
    page.reload();page.wait_for_function("document.querySelectorAll('.card').length===4")
    assert page.locator('.card').first.locator('[data-decision=revise]').get_attribute('aria-pressed')=='true'
    assert page.locator('.card').first.locator('textarea').input_value()=='QA: preserve poses, reduce lightning'
    with page.expect_download() as download:page.locator('#export').click()
    data=json.loads(Path(download.value.path()).read_text(encoding='utf-8'))
    assert len(data['reviews'])==4 and data['reviews'][0]['decision']=='revise'
    assert data['branch']=='feat/animation-presentation-lab'
    page.evaluate('localStorage.clear()');page.reload();page.wait_for_function("document.querySelectorAll('.card').length===4")
    for w,h in [(1440,1000),(390,844)]:
        page.set_viewport_size({'width':w,'height':h})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(ROOT/f'art-review/previews/gallery-{w}.png'),full_page=True)
    assert not errors,errors
    # The review export has its own entry and no game runtime entry.
    output=ROOT/'dist-animation-review'
    assert (output/'art-review/index.html').is_file() and not (output/'.omx/digimon.html').exists()
    print(json.dumps({'ok':True,'candidates':4,'images':'all loaded','filters':'both characters','reviews':'persist and export','viewports':[1440,390],'gameRuntimeExported':False,'errors':errors}))
    browser.close()
