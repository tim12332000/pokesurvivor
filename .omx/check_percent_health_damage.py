"""Real card clicks, shield/death/credit semantics and owned combat integration."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
from playwright.sync_api import sync_playwright
import json
import mimetypes

ROOT = Path(__file__).resolve().parent.parent
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    context = browser.new_context(locale='zh-TW', viewport={'width':1280,'height':820}, service_workers='block')
    def proxy(route):
        f = ROOT / unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
        route.fulfill(status=200 if f.is_file() else 404, body=f.read_bytes() if f.is_file() else b'', content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
    context.route('https://tim12332000.github.io/pokesurvivor/**', proxy)
    page=context.new_page(); errors=[]
    page.on('pageerror', lambda e: errors.append(str(e)))
    try:
        page.goto('https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW')
        page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
        page.evaluate('G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
        assert page.evaluate('!(G.Game.player.percentHealthDamage||0)')
        page.evaluate('''() => {
          window.originalOffer=G.LevelUp.offer;
          window.movesBefore=G.Game.player.moves.map(m=>m.id).join(',');
          G.LevelUp.offer=(pl,n=3)=>{
            for(let i=0;i<100;i++){
              const cards=originalOffer(pl,100),card=cards.find(c=>c.key==='stat:percentHealthDamage');
              if(card)return [card,...cards.filter(c=>c!==card)].slice(0,n);
            }
            throw Error('Real pool never offered life stripping');
          };
        }''')
        for picks in (1,2):
            page.evaluate("if(G.Game.state==='paused')G.Game.togglePause();G.Game.debugLevelUp()")
            page.locator('#scr-levelup').wait_for(state='visible')
            assert page.locator('#cards .card').count()==3
            assert '生命剝奪 +1%' in page.locator('#cards .card').first.inner_text()
            assert '最大生命值 1%' in page.locator('#cards .card').first.inner_text()
            page.locator('#cards .card').first.click()
            page.wait_for_function('(n)=>G.Game.player.percentHealthDamage===n*.01', arg=picks)
            page.evaluate("if(G.Game.state==='playing')G.Game.togglePause()")
            assert page.evaluate('''() => {
              const e=new G.Enemy({dex:19,hp:1000,spd:0,dmg:0,xp:0,behavior:'chase'},0,0,{hp:1,spd:1,dmg:1});
              e.hurt(10,'#fff',0,0,0,null,G.Game.player);return 1000-e.hp;
            }''') == 10+picks*10, 'Each real pick must add another 1% max HP'
        report=page.evaluate(r'''() => {
          const pl=G.Game.player,assert=(v,m)=>{if(!v)throw Error(m)};
          assert(pl.moves.map(m=>m.id).join(',')===movesBefore,'Card consumed skill slot');
          assert(pl.statsTaken.percentHealthDamage===2,'Picks not tracked');
          G.LevelUp.offer=originalOffer;G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();
          pl.item=null;pl.dead=false;pl.critChance=0;pl.lifestealRate=.01;pl.hp=pl.maxHp-100;
          const enemy=(hp=1000)=>{
            const e=new G.Enemy({dex:19,hp,spd:0,dmg:0,xp:0,behavior:'chase'},100,0,{hp:1,spd:1,dmg:1});
            e.types=['normal'];G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;
          };
          const hit=e=>e.hurt(10,'#fff',0,0,0,null,pl);
          let e=enemy(),before=pl.dmgDealt,heal=pl.hp;
          hit(e);assert(e.hp===970,'2% normal target damage wrong');
          assert(pl.dmgDealt-before===20&&Math.abs(pl.hp-heal-.2)<1e-8,'Bonus accounting or lifesteal recursive');
          e=enemy(10000);e.boss=true;hit(e);assert(e.hp===9790,'Boss percentage differs');
          e=enemy();e.shield=100;hit(e);assert(e.hp===1000&&e.shield===70,'Full shield bypassed');
          e=enemy();e.shield=15;hit(e);assert(e.hp===985&&e.shield===0,'Shield spillover incorrect');
          e=enemy();e.hp=10;hit(e);assert(e.dead,'Bonus lethal hit did not kill normally');
          before=pl.dmgDealt;hit(e);assert(pl.dmgDealt===before,'Dead target credited again');
          e=enemy();e.hurt(10);assert(e.hp===990,'Unowned environmental damage procced');
          e.hurt(10,'#fff',0,0,0,null,{});assert(e.hp===980,'Nonplayer owner procced');
          pl.dead=true;hit(e);assert(e.hp===970,'Dead owner procced');pl.dead=false;
          const card=G.LevelUp.STATS.find(s=>s.id==='percentHealthDamage');
          assert(!card.max,'Arbitrary card cap');
          for(let i=0;i<101;i++)card.apply(pl);
          assert(pl.percentHealthDamage===1.03,'Stacking capped at 100%');pl.percentHealthDamage=.02;
          const world={};for(const k of ['isFree','isLiquid','collide','projectileBlock','propsInCircle','isWall'])world[k]=G.World[k];
          Object.assign(G.World,{isFree:()=>true,isLiquid:()=>false,collide:()=>{},projectileBlock:()=>false,propsInCircle:()=>[],isWall:()=>false});
          const originalHurt=G.Enemy.prototype.hurt,events=[];
          G.Enemy.prototype.hurt=function(amount,...args){
            const hp=this.hp,owner=args[5],result=originalHurt.call(this,amount,...args);
            if(owner===pl){assert(hp-this.hp===Math.round(amount+this.maxHp*.02),'Owned damage missing or doubled');events.push(this);}
            return result;
          };
          const reset=()=>{
            G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();events.length=0;
            pl.x=pl.y=pl.aim=0;pl.hp=pl.maxHp;pl.dead=false;pl.quantityBonus=0;pl.target=null;
            G.Camera.x=G.Camera.y=0;return enemy(1000000);
          };
          const step=t=>{for(let i=0;i<t*240;i++){
            G.Projectiles.update(1/240,pl,G.EnemyMgr.all());G.Combat.resolve(1/240,pl,i/240);G.Combat.updateFields(1/240);
          }};
          const sources={};
          try {
            e=reset();G.Projectiles.spawn({x:100,y:0,vx:0,vy:0,dmg:10,r:12,life:1,owner:pl,color:'#fff',mtype:'normal',hits:new Set(),pierce:0});
            step(.02);assert(events.length===1,'Vanilla projectile attribution missing');sources.vanilla=events.length;
            e=reset();pl.target=e;G.DigimonSkills.cast(pl,G.Moves.instance('naruto-sasuke'));step(.8);
            assert(events.length===1,'Actual Chidori attribution missing');sources.chidori=events.length;
            e=reset();e.x=300;pl.target=e;G.EnemyMgr.rebuildGrid();
            G.DigimonSkills.cast(pl,G.Moves.instance('naruto-fuma-shuriken'));step(2.5);
            assert(events.length===2,'Fuma outbound/return attribution missing');sources.fuma=events.length;
            e=reset();const e2=enemy(1000000);e.x=e2.x=90;e.y=-5;e2.y=5;G.EnemyMgr.rebuildGrid();
            G.DigimonSkills.cast(pl,G.Moves.instance('naruto-fireball'));G.Combat.updateFields(.241);
            const flame=G.Projectiles.all()[0];assert(flame,'Fireball not released');flame.vx=flame.vy=0;
            e.x=e2.x=flame.x;e.y=flame.y-2;e2.y=flame.y+2;G.EnemyMgr.rebuildGrid();step(.61);
            assert(events.includes(e)&&events.includes(e2)&&events.length>=4,'Fireball repeated multi-target attribution missing');sources.fireball=events.length;
            e=reset();e.x=50;G.EnemyMgr.rebuildGrid();
            const mon=pl.mon;pl.mon=G.DEX_BY[30001];
            try { assert(G.NarutoClones.cast(pl,G.Moves.instance('naruto-shadow-clones')),'Clone cast rejected');step(2); }
            finally {pl.mon=mon;}
            assert(events.length>0,'Clone punches not owner-attributed');sources.clones=events.length;
          } finally {G.Enemy.prototype.hurt=originalHurt;Object.assign(G.World,world);G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();}
          return {cardPicks:2,normal:'10 + 2% of 1000 = 30',boss:'10 + 2% of 10000 = 210',shields:'full absorb and spillover',guards:'dead target, dead owner, unowned damage, no recursive credit',uncapped:'103%',sources};
        }''')
        page.evaluate('G.Game.quit();G.Flow.goMenu();G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
        assert page.evaluate('!(G.Game.player.percentHealthDamage||0)'), 'New run retained bonus'
        assert not errors, errors
        print(json.dumps({'ok':True,'checks':report,'newRunReset':True,'errors':errors},ensure_ascii=False))
    finally:
        browser.close()
