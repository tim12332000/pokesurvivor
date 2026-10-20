"""Verify the level-up button inside the actual local animation game iframe."""
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    results = []
    for width, height in [(1280, 820), (390, 844)]:
        context = browser.new_context(viewport={'width': width, 'height': height}, service_workers='block')
        requests, errors = [], []
        context.route('https://api.ipify.org/**', lambda route: (requests.append(route.request.url), route.abort()))
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://127.0.0.1:8318/art-review/playtest.html')
        page.wait_for_function('GameplayLab.ready')
        game = page.frame_locator('#game')
        if game.locator('#tap-start').is_visible():
            game.locator('#tap-start').click()
        page.locator('[data-hero="30002"]').click()
        frame = next(f for f in page.frames if '/.omx/digimon.html' in f.url)
        frame.evaluate('G.Game.player.invuln=99999')
        page.wait_for_function('AnimationAssets.ready')
        assert page.locator('#candidate').is_checked()
        assert page.locator('#continuity').is_checked()
        before_draws = page.evaluate('GameplayLab.counters.candidate')
        page.locator('#game').focus()
        page.keyboard.down('KeyD')
        page.wait_for_function('(before) => GameplayLab.counters.candidate > before', arg=before_draws)
        # Full presentation screenshots are collected by test_animation_complete.py.
        page.keyboard.up('KeyD')
        button = game.locator('#dev-level-up')
        for _ in range(2):
            button.wait_for(state='visible')
            before = frame.evaluate('G.Game.player.level')
            button.click()
            game.locator('#scr-levelup').wait_for(state='visible')
            assert frame.evaluate('G.Game.player.level') == before + 1
            game.locator('#cards .card').first.click()
        button.wait_for(state='visible')
        assert not requests, requests
        assert not errors, errors
        results.append({'viewport': [width, height], 'levelUps': 2, 'publicIPRequests': len(requests), 'errors': errors})
        context.close()
    browser.close()
    print(json.dumps(results))
