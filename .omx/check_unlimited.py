from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:8001/.omx/unlimited.html?lang=zh-TW'
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    context = browser.new_context(locale='zh-TW', viewport={'width': 1280, 'height': 800})
    page = context.new_page()
    page.goto('http://127.0.0.1:8000/version.json')
    page.evaluate("localStorage.setItem('ps.session', 'normal-session-sentinel')")
    errors, firebase_requests = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: firebase_requests.append(r.url) if r.url.startswith('https://') and ('firebase' in r.url or 'firestore' in r.url) else None)
    page.goto(URL)
    page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
    page.locator('#test-a .answer').first.wait_for(state='visible')
    while page.locator('#scr-test').is_visible(): page.locator('#test-a .answer').first.click()
    page.locator('#res-ok').click()
    page.locator('#scr-menu [data-go="upgrades"]').click()
    before = page.evaluate('JSON.stringify(G.DB.save.pupg)')
    for _ in range(3): page.locator('[data-buy]:enabled').first.click()
    after = page.evaluate('JSON.stringify(G.DB.save.pupg)')
    assert before != after
    assert page.evaluate('G.DB.save.coins') == 1000000000
    assert page.locator('#coins').inner_text() == '∞'
    assert page.evaluate('G.DB.mode') == 'local'
    assert page.evaluate('G.DB.online') is False
    assert page.evaluate('G.DB.fb') is None
    draws = page.evaluate('''() => {
      const results = [G.Gacha.pull(G.DB.save, 1), G.Gacha.pull(G.DB.save, 10, 1, 't1'), G.Gacha.pull(G.DB.save, 10, 1, 't10')];
      G.DB.commit();
      return results.map(r => r.length);
    }''')
    assert draws == [1, 10, 10]
    assert page.evaluate('G.DB.save.tickets.t1') == 1000000000
    assert page.evaluate('G.DB.save.tickets.t10') == 1000000000
    page.evaluate('G.GachaUI.open()')
    assert page.locator('#pull-1').is_enabled()
    assert page.locator('#pull-10').is_enabled()
    assert page.locator('#pull-10b').is_enabled()
    page.wait_for_function("document.getElementById('gacha-tickets').textContent.includes('∞')")
    assert page.evaluate("JSON.parse(localStorage.getItem('ps.sandbox.unlimited.v1')).pupg !== undefined")
    page.screenshot(path='.omx/unlimited-coins.png')
    page.reload()
    page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    assert page.evaluate('JSON.stringify(G.DB.save.pupg)') == after
    page.evaluate('G.DB.save.coins = 0')
    assert page.evaluate('G.DB.save.coins') == 1000000000
    assert page.evaluate('G.DB.save.tickets.t1') == 1000000000
    assert page.evaluate('G.DB.save.tickets.t10') == 1000000000
    assert not firebase_requests, firebase_requests
    assert not errors, errors
    page.goto('http://127.0.0.1:8000/version.json')
    assert page.evaluate("localStorage.getItem('ps.session')") == 'normal-session-sentinel'
    assert page.evaluate("localStorage.getItem('ps.sandbox.unlimited.v1')") is None
    print('Purchases, inexhaustible coins, reload persistence, cloud isolation and normal-save isolation passed; JS errors: 0')
    browser.close()
