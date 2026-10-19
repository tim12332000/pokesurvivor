"""Exercise stacking lifesteal via real level-up cards and actual Chidori damage."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
from playwright.sync_api import sync_playwright
import json
import mimetypes
import os

ROOT = Path(__file__).resolve().parent.parent
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=lifesteal'

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    context = browser.new_context(locale='zh-TW', viewport={'width':1280,'height':820}, service_workers='block')
    if os.environ.get('PAGES_LIVE') != '1':
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
        page.evaluate('G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
        assert page.evaluate('(G.Game.player.lifestealRate||0)===0'), 'Fresh run inherited lifesteal'
        page.evaluate(r'''() => {
          const pl=G.Game.player;
          if(!G.LevelUp.STATS.some(s=>s.id==='lifesteal'))throw Error('Missing lifesteal stat');
          G.EnemyMgr.clear();G.Combat.clearFields();G.Projectiles.clear();
          window.lifestealOriginalOffer=G.LevelUp.offer;
          window.lifestealMovesBefore=pl.moves.map(m=>m.id).join(',');
          G.LevelUp.offer=(owner,n=3)=>{
            for(let i=0;i<30;i++){
              const cards=window.lifestealOriginalOffer(owner,100),card=cards.find(c=>c.key==='stat:lifesteal');
              if(card)return [card,...cards.filter(c=>c!==card)].slice(0,n);
            }
            throw Error('Lifesteal not offered by real level-up pool');
          };
        }''')
        for picks in range(1,4):
            page.evaluate("if(G.Game.state==='paused')G.Game.togglePause();G.Game.debugLevelUp()")
            page.locator('#scr-levelup').wait_for(state='visible')
            assert page.locator('#cards .card').count() == 3
            assert '吸血 +1%' in page.locator('#cards .card').first.inner_text()
            page.locator('#cards .card').first.click()
            page.wait_for_function('(n)=>Math.abs(G.Game.player.lifestealRate-n*.01)<1e-10', arg=picks)
            page.evaluate("if(G.Game.state==='playing')G.Game.togglePause()")
            healed = page.evaluate('''() => {
              const pl=G.Game.player;pl.dead=false;pl.item=null;pl.hp=pl.maxHp-50;
              const before=pl.hp;pl.onDealt(100);return pl.hp-before;
            }''')
            assert abs(healed-picks)<1e-8, f'{picks} picks healed {healed} from 100 damage'
        result = page.evaluate(r'''() => {
          const assert=(v,m)=>{if(!v)throw Error(m)},pl=G.Game.player;
          assert(pl.moves.map(m=>m.id).join(',')===window.lifestealMovesBefore,'Lifesteal consumed or changed move slots');
          assert(pl.statsTaken.lifesteal===3,'Actual UI selections were not tracked');
          pl.item=null;pl.hp=pl.maxHp-50;
          const fractional=pl.hp;for(let i=0;i<10;i++)pl.onDealt(1);
          assert(Math.abs(pl.hp-fractional-.3)<1e-8,'Fractional healing was rounded away');
          pl.hp=pl.maxHp;pl.onDealt(1e6);assert(pl.hp===pl.maxHp,'Healing exceeded maximum HP');
          pl.dead=true;pl.hp=0;pl.onDealt(100);assert(pl.hp===0&&pl.dead,'Lifesteal resurrected player');
          pl.dead=false;pl.hp=0;pl.onDealt(100);assert(pl.hp===0,'Zero HP healed');
          pl.hp=pl.maxHp-50;const invalid=pl.hp;
          for(const damage of [0,-100,NaN,Infinity,-Infinity])pl.onDealt(damage);
          assert(pl.hp===invalid,'Invalid damage caused healing');
          pl.item='shellbell';pl.bellHeal=0;const shell=pl.hp;pl.onDealt(100);
          assert(pl.bellHeal===4&&Math.abs(pl.hp-shell-3)<1e-8,'Shell Bell original behavior changed');
          pl.item=null;pl.bellHeal=0;pl.hp=pl.maxHp-50;pl.dead=false;pl.invuln=0;pl.critChance=0;
          G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();G.FX.clear();
          const original={isFree:G.World.isFree,isLiquid:G.World.isLiquid,collide:G.World.collide};
          Object.assign(G.World,{isFree:()=>true,isLiquid:()=>false,collide:()=>{}});
          let healed,dealt;
          try{
            pl.x=pl.y=pl.aim=0;G.Camera.x=G.Camera.y=0;
            const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},100,0,{hp:1,spd:1,dmg:1});
            e.types=['normal'];G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();pl.target=e;
            const beforeHP=pl.hp,beforeDamage=pl.dmgDealt;
            assert(G.DigimonSkills.cast(pl,G.Moves.instance('naruto-sasuke')),'Actual Chidori cast rejected');
            for(let i=0;i<120;i++)G.Combat.updateFields(1/240);
            healed=pl.hp-beforeHP;dealt=pl.dmgDealt-beforeDamage;
            assert(e.hp<e.maxHp&&dealt>0,'Actual combat never hit enemy');
            assert(Math.abs(healed-dealt*.03)<1e-8,'Actual damage did not trigger lifesteal');
          }finally{Object.assign(G.World,original);G.Combat.clearFields();G.EnemyMgr.clear();}
          G.LevelUp.offer=window.lifestealOriginalOffer;
          return {actualChoices:3,healFrom100Damage:[1,2,3],fractionalHealing:.3,combat:{dealt,healed},shellBell:'original deferred healing preserved',guards:'full HP, death, zero HP and invalid damage'};
        }''')
        page.evaluate('G.Game.quit();G.Flow.goMenu();G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
        assert page.evaluate('(G.Game.player.lifestealRate||0)===0'), 'New run retained lifesteal'
        assert not errors, errors
        result['freshRunReset'] = 'passed'
        print(json.dumps({'ok':True,'checks':result,'pageErrors':errors},ensure_ascii=False))
    finally:
        browser.close()
