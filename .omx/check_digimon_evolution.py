from playwright.sync_api import sync_playwright
import json

URL = 'http://127.0.0.1:8002/.omx/digimon.html?lang=zh-TW&v=evolution'
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    context = browser.new_context(locale='zh-TW', viewport={'width':1280,'height':900})
    page = context.new_page()
    errors, missing, cloud = [], [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('response', lambda r: missing.append(r.url) if r.status >= 400 else None)
    page.on('request', lambda r: cloud.append(r.url) if r.url.startswith('https://') and ('firebase' in r.url or 'firestore' in r.url) else None)
    page.goto(URL)
    page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
    page.locator('#btn-digimon').click()
    page.locator('#scr-digimon').wait_for(state='visible')
    page.wait_for_function('[...G.Digimon.records.values()].every(r => r.ready)')
    assert page.locator('[data-evo-tab]').count() == 5
    counts = []
    for stage in range(5):
        page.locator(f'[data-evo-tab="{stage}"]').click()
        counts.append(page.locator('[data-digimon]').count())
    assert counts == [8,8,8,9,1], counts
    page.locator('[data-evo-tab="3"]').click()
    page.wait_for_timeout(300)
    page.screenshot(path='.omx/digimon-evolutions-picker.png', animations='disabled')
    page.locator('[data-digimon="20103"]').click()
    # Each main line crosses the correct stages; preserve move slot references and health ratio.
    chains = {20001:[20101,20102,20103],20002:[20111,20112,20113],20003:[20121,20122,20123],
              20004:[20131,20132,20133],20005:[20141,20142,20143],20006:[20151,20152,20153],
              20007:[20161,20162,20163],20008:[20172,20173]}
    for base, expected in chains.items():
        result = page.evaluate('''([base, expected]) => {
          G.Digimon.choose(base); G.DB.save.digimon.auto=false; G.DB.save.digimon.branch='holydramon';
          G.DB.upgradesOf(base).hp = 2;
          G.Flow.play();
          const player=G.Game.player, moves=player.slots[0], x=player.x, y=player.y;
          player.hp=player.maxHp*.5;
          if (G.Digimon.evolve()) throw Error('Evolved below level requirement');
          const actual=[];
          for (const dex of expected) {
            player.level=G.Digimon.levels[G.Digimon.records.get(dex).stage];
            if (!G.Digimon.evolve()) throw Error('Evolution rejected');
            if (player.slots[0] !== moves || !player.moves.includes(moves[0])) throw Error('Move slots broken');
            if (Math.abs(player.hp/player.maxHp-.5)>.00001) throw Error('Health ratio lost');
            if (player.x!==x || player.y!==y) throw Error('Position changed');
            if (player.moves[0].id!==player.mon.start) throw Error('Signature move not updated');
            if (G.DB.upgradesOf(dex).hp!==2) throw Error('Permanent upgrades lost');
            actual.push(player.dex);
          }
          if (G.DB.save.starter!==base) throw Error('Base lineage lost');
          G.Game.quit();G.Flow.goMenu();return actual;
        }''', [base,expected])
        assert result == expected, (base,result)
    # Branch and fusion both use real player transformations.
    result = page.evaluate('''() => {
      G.Digimon.choose(20008);G.DB.save.digimon.auto=false;G.DB.save.digimon.branch='ophanimon';G.Flow.play();
      G.Game.player.level=10;G.Digimon.evolve();G.Game.player.level=15;G.Digimon.evolve();
      const branch=G.Game.player.dex;G.Game.quit();G.Flow.goMenu();
      G.Digimon.choose(20103);G.Flow.play();G.Game.player.level=20;
      const owned=G.DB.save.owned[20113];delete G.DB.save.owned[20113];
      if(G.Digimon.evolve())throw Error('Fusion accepted without partner form');
      G.DB.save.owned[20113]=owned;
      if(!G.Digimon.evolve())throw Error('Fusion rejected');
      return {branch,fusion:G.Game.player.dex};
    }''')
    assert result == {'branch':20174,'fusion':20201}, result
    page.wait_for_timeout(350)
    page.screenshot(path='.omx/digimon-omnimon-gameplay.png', animations='disabled')
    page.evaluate('G.Game.quit();G.Flow.goMenu();G.Digimon.choose(20001);G.DB.save.digimon.auto=true;G.Flow.play();G.Game.player.level=15')
    page.wait_for_function('G.Game.player.dex===20103')
    page.evaluate('G.Game.quit();G.Flow.goMenu();G.DB.commit()')
    page.reload()
    page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    assert page.evaluate('G.DB.save.partner') == 20103
    assert page.evaluate('G.DB.save.digimon.auto') is True
    assert page.evaluate('G.DB.save.coins') == 1000000000
    assert page.evaluate('G.DB.save.tickets.t10') == 1000000000
    # Manual UI operation and compatibility with the previous base-form save shape.
    if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
    page.evaluate('G.Digimon.choose(20001);G.DB.save.digimon.auto=false;G.Flow.play();G.Game.player.level=5')
    page.locator('#digimon-evolve-now').wait_for(state='visible')
    page.wait_for_function("!document.getElementById('digimon-evolve-now').disabled")
    page.locator('#digimon-evolve-now').click()
    assert page.evaluate('G.Game.player.dex') == 20101
    page.evaluate('''() => { G.Game.quit();G.Flow.goMenu();G.Digimon.choose(20002);
      G.DB.save.stats.bestTime=1234;G.DB.upgradesOf(20002).hp=3;delete G.DB.save.digimon;G.DB.commit(); }''')
    page.reload()
    page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    assert page.evaluate('G.DB.save.partner') == 20002
    assert page.evaluate('G.DB.save.stats.bestTime') == 1234
    assert page.evaluate('G.DB.upgradesOf(20002).hp') == 3
    if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
    page.locator('#btn-digimon').click()
    assert page.locator('#digimon-auto-evolve').is_checked()
    assert not errors, errors
    assert not missing, missing
    assert not cloud, cloud
    # The final branch remains selectable on a small landscape screen.
    context.close()
    mobile=browser.new_context(locale='zh-TW',viewport={'width':844,'height':390},is_mobile=True,has_touch=True)
    page=mobile.new_page();page.goto(URL)
    page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.locator('[data-evo-tab="3"]').click()
    page.locator('[data-digimon="20174"]').scroll_into_view_if_needed()
    page.locator('[data-digimon="20174"]').click()
    assert page.evaluate('G.DB.save.partner')==20174
    print(json.dumps({'main_lines':8,'evolution_forms':25,'total_forms':33,'picker_counts':counts,
                      'branch_and_fusion':result,'automatic_evolution':'passed',
                      'health_slots_position_upgrades':'preserved','save_reload':'passed','legacy_save':'passed',
                      'manual_evolution':'passed','mobile_branch_selection':'passed','page_errors':errors}))
    browser.close()
