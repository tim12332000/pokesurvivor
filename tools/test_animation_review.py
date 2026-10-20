"""Verify the isolated export with the real curated images and review controls."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
BASE=os.environ.get('ANIMATION_REVIEW_BASE','http://127.0.0.1:8317').rstrip('/')
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'/art-review/index.html')
    page.wait_for_function("document.querySelectorAll('.card').length===7")
    page.locator('.card').last.scroll_into_view_if_needed()
    page.wait_for_function("[...document.images].every(i=>i.complete&&i.naturalWidth>0)")
    assert 'feat/animation-presentation-lab' in page.locator('#branch').inner_text()
    page.locator('#character').select_option('佐助');assert page.locator('.card').count()==2
    page.locator('#character').select_option('鳴人');assert page.locator('.card').count()==3
    page.locator('#character').select_option('\u5c0f\u674e');assert page.locator('.card').count()==2
    assert page.locator('[data-item-id="lee-common-v1"] .animation-controls select option').count()==12
    assert page.locator('[data-item-id="lee-skills-v1"] .animation-controls select option').count()==4
    for width,height in [(1440,1000),(390,844)]:
        page.set_viewport_size({'width':width,'height':height})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(ROOT/f'art-review/previews/gallery-lee-{width}.png'),full_page=True)
    page.set_viewport_size({'width':1440,'height':1000})
    page.locator('#character').select_option('all')
    page.locator('#category').select_option('common');assert page.locator('.card').count()==3
    assert page.locator('.animation-player').count()==3
    page.locator('#category').select_option('skill');assert page.locator('.card').count()==4
    page.locator('#category').select_option('common')
    death=page.locator('[data-item-id="naruto-common-v1"]');death.locator('canvas').scroll_into_view_if_needed()
    death.locator('.animation-controls select').select_option(label='倒下')
    death.locator('input[type=number]').fill('24');death.locator('input[type=number]').dispatch_event('change')
    page.wait_for_function("document.querySelector('[data-item-id=naruto-common-v1] canvas').dataset.frame==='27'")
    page.wait_for_timeout(200);assert death.locator('canvas').get_attribute('data-frame')=='27'
    page.locator('#category').select_option('all')
    first=page.locator('.card').first
    first.locator('[data-decision=revise]').click()
    first.locator('textarea').fill('QA: preserve poses, reduce lightning')
    page.reload();page.wait_for_function("document.querySelectorAll('.card').length===7")
    assert page.locator('.card').first.locator('[data-decision=revise]').get_attribute('aria-pressed')=='true'
    assert page.locator('.card').first.locator('textarea').input_value()=='QA: preserve poses, reduce lightning'
    with page.expect_download() as download:page.locator('#export').click()
    data=json.loads(Path(download.value.path()).read_text(encoding='utf-8'))
    assert len(data['reviews'])==7 and data['reviews'][0]['decision']=='revise'
    assert data['branch']=='feat/animation-presentation-lab'
    page.evaluate('localStorage.clear()');page.reload();page.wait_for_function("document.querySelectorAll('.card').length===7")
    for w,h in [(1440,1000),(390,844)]:
        page.set_viewport_size({'width':w,'height':h})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.evaluate('scrollTo(0,0)')
        page.screenshot(path=str(ROOT/f'art-review/previews/gallery-{w}.png'))
    assert not errors,errors
    # The review export has its own entry and no game runtime entry.
    output=ROOT/'dist-animation-review'
    assert (output/'art-review/index.html').is_file() and not (output/'.omx/digimon.html').exists()
    assert len(list((output/'art-review').rglob('*.png')))==7
    assert (output/'art-review/lee-skill-design.md').is_file()
    assert not (output/'art-review/candidates').exists()
    assert not (output/'art-review/references').exists()
    print(json.dumps({'ok':True,'candidates':7,'images':'all loaded, original atlases only','filters':'Naruto, Sasuke, Lee and action categories','reviews':'persist and export','viewports':[1440,390],'gameRuntimeExported':False,'errors':errors}))
    browser.close()
