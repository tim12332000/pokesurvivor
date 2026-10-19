"""Exercise Sasuke's Fuma Shuriken in the shipped browser combat and level-up UI."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
from playwright.sync_api import sync_playwright
import json
import mimetypes
import os

ROOT = Path(__file__).resolve().parent.parent
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=sasuke-fuma'
ID = 'naruto-fuma-shuriken'

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    context = browser.new_context(locale='zh-TW', viewport={'width':1280,'height':820}, service_workers='block')
    if os.environ.get('PAGES_LIVE') != '1':
        def proxy(route):
            file = ROOT / unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
            if file.is_file():
                route.fulfill(status=200, body=file.read_bytes(), content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
            else:
                route.fulfill(status=404, body='Not found')
        context.route('https://tim12332000.github.io/pokesurvivor/**', proxy)
    page = context.new_page()
    errors, missing = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('response', lambda response: missing.append(response.url) if response.status >= 400 else None)
    try:
        page.goto(URL)
        page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible():
            page.locator('#tap-start').click()
        page.evaluate('G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
        report = page.evaluate(r'''() => {
          const id='naruto-fuma-shuriken',pl=G.Game.player;
          const assert=(ok,msg)=>{if(!ok)throw Error(msg);};
          const saved={};
          for(const key of ['isWall','isFree','collide','propsInCircle','projectileBlock','isLiquid','damageProp'])saved[key]=G.World[key];
          const sees=G.Camera.sees;
          Object.assign(G.World,{isWall:()=>false,isFree:()=>true,collide:()=>{},propsInCircle:()=>[],projectileBlock:()=>false,isLiquid:()=>false});
          G.Camera.sees=()=>true;
          const setup=(points=[])=>{
            G.Combat.clearFields();G.Projectiles.clear();G.FX.clear();G.EnemyMgr.clear();
            pl.x=pl.y=0;pl.aim=0;pl.hp=pl.maxHp;pl.dead=false;pl.invuln=0;pl.level=1;
            pl.quantityBonus=0;pl.atkMul=1;pl.critChance=0;pl.moves=[];pl.slots=[];pl.bind={};pl.banned=new Set();pl.active=0;
            pl.addMove('naruto-sasuke');
            const enemies=points.map(([x,y])=>{
              const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
              e.types=['normal'];G.EnemyMgr.add(e);return e;
            });
            G.EnemyMgr.rebuildGrid();pl.target=enemies[0]||null;return enemies;
          };
          let time=0;
          const step=seconds=>{for(let t=0;t<seconds;t+=1/240){
            const dt=Math.min(1/240,seconds-t);time+=dt;
            G.Projectiles.update(dt,pl,G.EnemyMgr.all());G.Combat.resolve(dt,pl,time);G.Combat.updateFields(dt);
          }};
          const result={};
          try {
            assert(G.NarutoSkillCatalog.definitions.size===27,'Expected 27 ninja skills');
            const def=G.Moves.BY_ID[id];assert(def&&def.learnLevel===9,'Missing level 9 Fuma definition');
            for(const mon of G.Naruto.records.values()){
              // A non-current character exposes its complete catalog; current Sasuke needs level 9.
              pl.level=9;const pool=G.Moves.poolFor(mon);
              assert(pool.includes(id)===(mon.dex===30002),'Fuma escaped Sasuke-only pool: '+mon.dex);
            }
            setup();pl.level=2;assert(!G.LevelUp.offer(pl).some(c=>['new:naruto-fireball','new:naruto-sharingan','new:'+id].includes(c.key)),'Training unlocked early');
            pl.level=3;let card=G.LevelUp.offer(pl).find(c=>c.key==='new:naruto-fireball');assert(card,'Level 3 fireball changed');card.apply(pl);
            pl.level=6;card=G.LevelUp.offer(pl).find(c=>c.key==='new:naruto-sharingan');assert(card,'Level 6 Sharingan changed');card.apply(pl);
            pl.level=8;assert(!G.LevelUp.offer(pl,20).some(c=>c.key==='new:'+id)&&!G.Moves.poolFor(pl.mon).includes(id),'Fuma unlocked before level 9');
            pl.level=9;assert(G.LevelUp.offer(pl).some(c=>c.key==='new:'+id),'Level 9 guaranteed choice missing');
            result.training='Sasuke only; level 3/6 unchanged; Fuma guaranteed at level 9';

            setup();const learned=G.Moves.instance(id);pl.quantityBonus=2;
            assert(G.DigimonSkills.cast(pl,learned),'Cast rejected');assert(!G.Projectiles.count,'Charge released immediately');
            step(.19);assert(!G.Projectiles.count,'Projectile released before charge');
            pl.quantityBonus=7;learned.count=9;learned.dmg=999;
            step(.02);let shots=G.Projectiles.all();
            assert(shots.length===3&&shots.every(s=>s.pierce===5&&Math.abs(s.dmg-34*pl.atk)<.001),'Pending cast mutated after quantity/damage changes');
            assert(shots.every(s=>s.owner===pl&&!s.digiBomb&&!s.boom&&!s.homing&&s.vis.proj===id),'Projectile has wrong owner or invented behavior');
            assert(G.VFX.spins(id),'Large blade does not spin');
            // Casting itself must not mutate a learned instance or its definition.
            setup();const immutable=G.Moves.instance(id),baseline=JSON.stringify(immutable);pl.quantityBonus=2;
            G.DigimonSkills.cast(pl,immutable);step(.21);
            assert(JSON.stringify(immutable)===baseline&&def.count===1&&def.pierce===3,'Cast permanently changed learned skill');
            const quantities=[];
            for(const [level,bonus,expected] of [[1,0,1],[5,0,3],[1,2,3],[5,2,5]]){
              setup();pl.quantityBonus=bonus;G.DigimonSkills.cast(pl,G.Moves.instance(id,level));step(.21);
              assert(G.Projectiles.count===expected,'Wrong quantity at level '+level+' bonus '+bonus);quantities.push(expected);
            }
            result.quantity={baseAndLevel5:quantities.slice(0,2),withTwoPassiveStacks:quantities.slice(2),snapshot:'immutable through charge'};

            const victims=setup([[100,0],[210,0],[320,0],[210,120]]);
            const damageBefore=pl.dmgDealt,m=G.Moves.instance(id),expected=m.dmg*pl.atk*G.Types.mult(m.type,['normal'])*G.Weather.mult(m.type);
            G.DigimonSkills.cast(pl,m);step(1.5);
            assert(victims.slice(0,3).every(e=>100000-e.hp===Math.round(expected)),'Piercing damage expected '+Math.round(expected)+'; observed '+JSON.stringify(victims.map(e=>100000-e.hp)));
            assert(victims[3].hp===100000,'Straight blade gained an AOE explosion');
            assert(Math.abs((pl.dmgDealt-damageBefore)-3*expected)<.001,'Real player damage credit missing');
            assert(!G.Projectiles.count,'Expired blade survived');
            result.damage='three aligned enemies hit once; off-axis untouched; damage credited to player';

            const blocked=setup([[200,0]]);G.World.projectileBlock=x=>x>=65;G.World.isWall=G.World.projectileBlock;
            G.DigimonSkills.cast(pl,G.Moves.instance(id));step(.8);
            assert(blocked[0].hp===100000&&!G.Projectiles.count,'Blade crossed a wall');
            G.World.projectileBlock=()=>false;G.World.isWall=()=>false;
            setup();let propDamage=0;
            const prop={id:98765,x:80,y:0,r:12,solid:true};
            G.World.propsInCircle=(x,y,r)=>Math.hypot(x-prop.x,y-prop.y)<=r+prop.r?[prop]:[];
            G.World.damageProp=(p,d)=>{assert(p===prop,'Unexpected prop');propDamage+=d;};
            G.DigimonSkills.cast(pl,G.Moves.instance(id));step(.6);
            assert(Math.abs(propDamage-34*pl.atk)<.001,'Prop collision missed or hit repeatedly');
            G.World.propsInCircle=()=>[];
            result.collision='normal walls and props; each prop hit once';
            const shared=G.Moves.instance('naruto-shuriken');
            assert(shared.count===8&&shared.digiVis.proj!==id,'Common small shuriken changed');
            setup();pl.addMove('naruto-fireball');pl.addMove('naruto-sharingan');pl.addMove('naruto-kunai');
            pl.bind['naruto-kunai']=1;pl.arrange();pl.level=8;
            return result;
          }finally{Object.assign(G.World,saved);G.Camera.sees=sees;G.Combat.clearFields();G.Projectiles.clear();}
        }''')
        # The actual level-up UI must replace a full shared-tool slot and retain its binding.
        page.evaluate('G.Game.togglePause();G.Game.debugLevelUp()')
        page.locator('#scr-levelup').wait_for(state='visible')
        card = page.locator('#cards .card').filter(has_text='風魔').first
        card.wait_for(state='visible')
        page.screenshot(path=str(ROOT/'.omx/sasuke-fuma-level9.png'), animations='disabled')
        card.click()
        page.wait_for_function("G.Game.player.hasMove('naruto-fuma-shuriken')")
        assert page.evaluate("G.Game.player.slots.length===4&&G.Game.player.bind['naruto-fuma-shuriken']===1&&G.Game.player.bind['naruto-kunai']==null&&G.Game.player.hasMove('naruto-sasuke')&&G.Game.player.hasMove('naruto-fireball')&&G.Game.player.hasMove('naruto-sharingan')")
        report['ui'] = 'actual level 9 card click; four slots; shared-tool replacement preserves binding'
        # Capture the runtime-selected Shoot animation and an actual large projectile in flight.
        page.evaluate(r'''() => {
          G.Game.togglePause();const pl=G.Game.player;
          G.Projectiles.clear();G.Combat.clearFields();G.EnemyMgr.clear();
          const move=pl.moves.find(m=>m.id==='naruto-fuma-shuriken');
          pl.aim=0;pl.anim.update(10);pl.anim.loop('Idle');pl.cast(move);
          if(pl.anim.cur!=='Shoot')throw Error('Projectile did not select source Shoot action: '+pl.anim.cur+' kind '+move.kind);
          G.DigimonSkills.cast(pl,move);G.Combat.updateFields(.21);
          const panel=document.createElement('canvas');panel.id='sasuke-fuma-capture';panel.width=700;panel.height=240;
          panel.style.cssText='position:fixed;top:0;left:0;z-index:30000;max-width:100vw;height:auto';
          const ctx=panel.getContext('2d');ctx.fillStyle='#14233a';ctx.fillRect(0,0,panel.width,panel.height);
          ctx.fillStyle='#fff';ctx.font='18px sans-serif';ctx.fillText('Sasuke / actual Shoot frame and Fuma Shuriken',20,30);
          ctx.save();ctx.translate(140-pl.x,150-pl.y);pl.anim.draw(ctx,pl.x,pl.y);ctx.restore();
          const shot=G.Projectiles.all()[0];shot.x=390;shot.y=155;shot.t=.12;
          G.Projectiles.draw(ctx);document.body.append(panel);
        }''')
        page.screenshot(path=str(ROOT/'.omx/sasuke-fuma-review.png'), animations='disabled')
        prepare_capture = r'''() => {
          const pl=G.Game.player;
          G.Projectiles.clear();G.Combat.clearFields();G.EnemyMgr.clear();
          const move=pl.moves.find(m=>m.id==='naruto-fuma-shuriken');
          pl.aim=0;pl.anim.update(10);pl.anim.loop('Idle');pl.cast(move);pl.anim.update(.16);
          G.DigimonSkills.cast(pl,move);G.Combat.updateFields(.21);
          const shot=G.Projectiles.all()[0];shot.x=pl.x+110;shot.y=pl.y;shot.t=.12;
          G.Camera.x=pl.x;G.Camera.y=pl.y;
          document.getElementById('scr-pause').style.visibility='hidden';
        }'''
        page.evaluate("document.getElementById('sasuke-fuma-capture').remove()")
        page.evaluate(prepare_capture)
        page.wait_for_timeout(50)
        page.screenshot(path=str(ROOT/'.omx/sasuke-fuma-desktop.png'), animations='disabled')
        mobile = browser.new_context(locale='zh-TW', viewport={'width':390,'height':844}, is_mobile=True, has_touch=True, service_workers='block')
        if os.environ.get('PAGES_LIVE') != '1':
            mobile.route('https://tim12332000.github.io/pokesurvivor/**', proxy)
        phone = mobile.new_page()
        phone.on('pageerror', lambda error: errors.append(str(error)))
        phone.on('response', lambda response: missing.append(response.url) if response.status >= 400 else None)
        phone.goto(URL)
        phone.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
        if phone.locator('#tap-start').is_visible():
            phone.locator('#tap-start').click()
        phone.evaluate("G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause();G.Game.player.level=9;G.Game.player.addMove('naruto-fuma-shuriken');G.Game.player.setActive(G.Game.player.slots.findIndex(slot=>slot.some(move=>move.id==='naruto-fuma-shuriken')))")
        phone.evaluate(prepare_capture)
        phone.wait_for_timeout(50)
        phone.screenshot(path=str(ROOT/'.omx/sasuke-fuma-portrait.png'), animations='disabled')
        mobile.close()
        page.evaluate("G.DigimonSkills.cast(G.Game.player,G.Moves.instance('naruto-fuma-shuriken'));G.Game.quit();G.Flow.goMenu();G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()")
        assert page.evaluate('G.Projectiles.count===0&&G.DigimonSkills.activeEffects.length===0'), 'New run retained old projectiles/charged casts'
        report['lifecycle'] = 'normal quit/new run clears old projectiles and pending casts'
        assert not errors, errors
        assert not missing, missing
        print(json.dumps({'ok':True,'live':os.environ.get('PAGES_LIVE')=='1','checks':report}, ensure_ascii=False))
    finally:
        browser.close()
