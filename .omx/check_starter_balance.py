"""Verify full permanent-upgrade baseline without changing purchase history."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
from playwright.sync_api import sync_playwright
import json
import mimetypes

ROOT = Path(__file__).resolve().parent.parent
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=starter-balance'

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    context = browser.new_context(locale='zh-TW', service_workers='block')
    def proxy(route):
        file = ROOT / unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
        route.fulfill(status=200 if file.is_file() else 404, body=file.read_bytes() if file.is_file() else b'Not found', content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
    context.route('https://tim12332000.github.io/pokesurvivor/**', proxy)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    try:
        page.goto(URL)
        page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible():
            page.locator('#tap-start').click()
        page.wait_for_function('!!G.StarterBalance')
        result = page.evaluate(r'''() => {
          const assert=(ok,msg)=>{if(!ok)throw Error(msg)},near=(a,b)=>Math.abs(a-b)<1e-8;
          const balance=G.StarterBalance,save=G.DB.save;
          assert(balance.enabled,'Baseline disabled');
          const levels=Object.fromEntries(G.Upgrades.LIST.map(u=>[u.id,u.max]));
          assert(JSON.stringify(levels)===JSON.stringify(balance.maxLevels),'Not derived from upgrade maxima');
          balance.enabled=false;
          const expected=G.Upgrades.perks(levels),oldEmpty=G.Upgrades.perks({});
          assert(oldEmpty.hp===0&&oldEmpty.startMoves===1,'Off flag did not restore original behavior');
          assert(!document.getElementById('starter-balance-notice'),'Off flag left misleading notice');
          balance.enabled=true;
          for(const bought of [{},levels,{hp:3,atk:2,moves:1}])
            assert(JSON.stringify(G.Upgrades.perks(bought))===JSON.stringify(expected),'Purchased levels duplicated or reduced baseline');
          assert(Object.keys(expected).length===13,'Missing upgrade modifiers');
          assert(expected.hp===80&&near(expected.atkMul,1.4)&&near(expected.spdMul,1.24)&&near(expected.cdMul,.76)&&near(expected.dmgReduce,.16)&&near(expected.regen,1)&&near(expected.magnetMul,1.72)&&near(expected.xpMul,1.4)&&near(expected.coinMul,1.64)&&near(expected.crit,.30)&&expected.startMoves===2&&expected.rerolls===5&&expected.bans===3,'Full-strength values incorrect');
          assert(document.getElementById('starter-balance-notice')?.textContent.includes('無需先購買'),'Menu explanation missing');
          const records=[];
          for(const dex of [30001,30002,1])for(const purchased of [{},levels]){
            G.Game.toUI();save.partner=save.starter=dex;save.partnerShiny=false;
            save.pupg[dex]={...purchased};
            const before=JSON.stringify({pupg:save.pupg,coins:save.coins,pban:save.pban,pbind:save.pbind});
            G.Flow.play();G.Game.togglePause();
            const pl=G.Game.player;
            assert(pl.dex===dex,'Wrong starting role');
            assert(pl.hp===pl.mon.hp+80&&pl.maxHp===pl.hp,'HP baseline incorrect');
            assert(near(pl.atkMul,expected.atkMul)&&near(pl.spdMul,expected.spdMul)&&near(pl.cdMul,expected.cdMul),'Core multipliers incorrect');
            assert(near(pl.dmgReduce,expected.dmgReduce)&&near(pl.regenFlat,expected.regen)&&near(pl.magnet,78*expected.magnetMul),'Defense, regeneration or magnet incorrect');
            assert(near(pl.xpMul,expected.xpMul)&&near(pl.coinMul,expected.coinMul)&&near(pl.critChance,expected.crit),'Reward/crit baseline incorrect');
            const expectedMoves=Math.min(expected.startMoves,G.Moves.poolFor(pl.mon).filter(id=>!pl.banned?.has(id)).length);
            assert(pl.rerollBonus===5&&pl.moves.length===expectedMoves,'Starting moves or rerolls missing');
            if(pl.mon.naruto)assert(pl.moves.every(m=>!G.NarutoSkillCatalog.extraPools.get(dex).includes(m.id)||(G.Moves.BY_ID[m.id].learnLevel||3)<=pl.level),'Starting extra move bypassed signature unlock gate');
            assert(before===JSON.stringify({pupg:save.pupg,coins:save.coins,pban:save.pban,pbind:save.pbind}),'Run start changed purchase history or currency');
            const atk=pl.atkMul,magnet=pl.magnet;
            G.LevelUp.STATS.find(s=>s.id==='atk').apply(pl);
            G.LevelUp.STATS.find(s=>s.id==='mag').apply(pl);
            assert(near(pl.atkMul,atk*1.1)&&near(pl.magnet,magnet*1.3),'In-run upgrades stopped stacking');
            records.push({dex,purchased:Object.keys(purchased).length,hp:pl.maxHp,moves:pl.moves.length});
          }
          G.Game.toUI();
          return {perks:expected,runs:records,saveHistory:'unchanged',inRunUpgrades:'stack normally',unlockGates:'preserved'};
        }''')
        assert not errors, errors
        print(json.dumps({'ok':True,'checks':result,'pageErrors':errors},ensure_ascii=False))
    finally:
        browser.close()
