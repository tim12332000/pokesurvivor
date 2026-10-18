from pathlib import Path
from playwright.sync_api import sync_playwright
import json

URL = 'http://127.0.0.1:8002/.omx/digimon.html?lang=zh-TW'
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    context = browser.new_context(locale='zh-TW', viewport={'width': 1280, 'height': 820})
    page = context.new_page()
    errors, missing, cloud = [], [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('response', lambda r: missing.append(r.url) if r.status >= 400 else None)
    page.on('request', lambda r: cloud.append(r.url) if r.url.startswith('https://') and ('firebase' in r.url or 'firestore' in r.url) else None)
    page.goto(URL)
    page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
    page.locator('#scr-digimon').wait_for(state='visible')
    assert page.locator('[data-digimon]').count() == 8
    assert page.locator('#scr-digimon canvas').count() == 8
    page.wait_for_function("[...G.Digimon.records.values()].every(r => r.ready)")
    pixel_proof = page.evaluate('''() => [...G.Digimon.records.values()].map(record => {
      const p = record.pixel;
      if (!p.frame_rects && (record.image.naturalWidth !== p.cell_width * 12 || record.image.naturalHeight !== p.cell_height)) throw Error('Invalid sprite dimensions');
      const canvas = document.createElement('canvas'); canvas.width = canvas.height = 640;
      const ctx = canvas.getContext('2d');
      const actor = new G.Sprites.Animator(record.dex, 1);
      actor.loop('Walk');
      const snapshot = () => { ctx.clearRect(0, 0, 640, 640); actor.draw(ctx, 320, 560); return canvas.toDataURL(); };
      const poses = [1,3,5,7].map(dir => { actor.dir = dir; return snapshot(); });
      if (new Set(poses).size !== 4) throw Error('Missing directional art: ' + record.name);
      const before = snapshot(); actor.update(8 / 60); const after = snapshot();
      if (before === after) throw Error('Walk frame did not change: ' + record.name);
      return { name: record.name, directions: 4, walk_frames_change: true };
    })''')
    assert len(pixel_proof) == 33
    page.wait_for_timeout(300)
    page.screenshot(path='.omx/digimon-picker.png', animations='disabled')
    page.locator('[data-digimon="20001"]').click()
    assert page.locator('#menu-partner-name').inner_text() == '亞古獸'
    assert page.evaluate('G.DEX.length') == 1007
    assert page.evaluate('G.Gacha.BANNERS.length') == 11
    assert page.evaluate('G.MenuUI.GEN_NAMES[9]') == 'Digimon'
    assert page.evaluate('G.DB.mode') == 'local'
    assert not page.evaluate('G.DB.online')
    assert page.evaluate('G.DB.save.coins') == 1000000000
    assert page.evaluate('G.DB.save.tickets.t1') == 1000000000
    page.locator('#scr-menu [data-go="dex"]').click()
    tabs = page.locator('#dex-gens .gen-tab')
    assert tabs.count() == 11
    tabs.nth(9).click()
    assert page.locator('#dex-grid .cell').count() == 33
    assert page.locator('#dex-grid .locked').count() == 0
    page.screenshot(path='.omx/digimon-collection.png', animations='disabled')
    page.evaluate('G.MenuUI.open()')
    page.locator('#scr-menu [data-go="gacha"]').click()
    page.locator('#gacha-gens [data-gen="10"]').click()
    assert page.locator('#gacha-gens .gen-tab').count() == 11
    assert '數碼' in page.locator('#banner-title').inner_text()
    draws = page.evaluate('G.Gacha.pull(G.DB.save, 10, 10, "t10")')
    assert len(draws) == 10 and page.evaluate('(draws) => draws.every(x => G.Digimon.records.has(x.dex))', draws)
    assert page.evaluate('G.DB.save.tickets.t10') == 1000000000
    page.wait_for_function("document.getElementById('banner-desc').textContent.includes('數碼寶貝大冒險')")
    page.wait_for_timeout(350)
    page.screenshot(path='.omx/digimon-gacha.png', animations='disabled')
    page.evaluate('G.MenuUI.open()')
    # Exercise actual combat startup for each of the eight partner/start-move pairs.
    for dex in range(20001, 20009):
        page.evaluate('(dex) => G.Digimon.choose(dex)', dex)
        page.locator('#scr-menu [data-go="play"]').click()
        page.wait_for_function('G.Game.state === "playing"')
        assert page.evaluate('G.Game.player.dex') == dex
        assert page.evaluate('G.Game.player.moves[0].id').startswith('digimon-')
        page.keyboard.press('d')
        page.wait_for_timeout(200)
        if dex == 20008: page.screenshot(path='.omx/digimon-gameplay.png')
        page.evaluate('G.Game.quit(); G.Flow.goMenu()')
    page.evaluate('G.DB.commit()')
    page.reload()
    page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    assert page.evaluate('G.DB.save.partner') == 20008
    assert page.evaluate("localStorage.getItem('ps.sandbox.digimon.v1') !== null")
    assert page.evaluate("localStorage.getItem('ps.sandbox.unlimited.v1')") is None
    assert not errors, errors
    assert not missing, missing
    assert not cloud, cloud
    context.close()
    mobile = browser.new_context(locale='zh-TW', viewport={'width': 844, 'height': 390}, is_mobile=True, has_touch=True)
    page = mobile.new_page()
    page.goto(URL)
    page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
    page.locator('#scr-digimon').wait_for(state='visible')
    page.locator('[data-digimon="20008"]').scroll_into_view_if_needed()
    page.locator('[data-digimon="20008"]').click()
    assert page.locator('#menu-partner-name').inner_text() == '迪路獸'
    print(json.dumps({'partners': 8, 'generation_tabs': 11, 'combat_startups': 8,
                      'gacha': 'passed', 'saved_partner': 20008, 'mobile_selection': 'passed',
                      'page_errors': errors, 'missing_resources': missing, 'cloud_requests': cloud}))
    browser.close()
