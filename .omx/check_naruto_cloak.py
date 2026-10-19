"""Verify Naruto's temporary chakra cloak in the real sandbox browser runtime."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import mimetypes
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=naruto-cloak'

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    context = browser.new_context(locale='zh-TW', viewport={'width': 1280, 'height': 820}, service_workers='block')
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
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('response', lambda r: missing.append(r.url) if r.status >= 400 else None)
    try:
        page.goto(URL)
        page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible():
            page.locator('#tap-start').click()
        page.evaluate('G.Naruto.choose(30001);G.Flow.play();G.Game.togglePause()')
        report = page.evaluate(r'''() => {
          const assert=(ok,msg)=>{if(!ok)throw Error(msg);},near=(a,b)=>Math.abs(a-b)<.0001;
          const pl=G.Game.player,S=G.NarutoSupport,id='naruto-nine-tails-cloak',mode='nine-tails-cloak';
          const saved={};for(const k of ['isFree','isWall','collide','projectileBlock','propsInCircle','isLiquid'])saved[k]=G.World[k];
          Object.assign(G.World,{isFree:()=>true,isWall:()=>false,collide:()=>{},projectileBlock:()=>false,propsInCircle:()=>[],isLiquid:()=>false});
          const enemy=(x,y)=>{const e=new G.Enemy({dex:19,hp:1e7,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;};
          const reset=(points=[[180,0]])=>{
            G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();
            pl.mon=G.Naruto.records.get(30001);pl.dex=30001;pl.x=pl.y=pl.aim=0;
            pl.dead=false;pl.hp=pl.maxHp;pl.invuln=0;pl.frozen=0;pl.level=1;pl.critChance=0;pl.atkMul=pl.spdMul=1;
            pl.quantityBonus=0;pl.dmgReduce=0;pl.moves=[];pl.slots=[];pl.bind={};pl.active=0;pl.banned=new Set();
            pl.buffs.atk={n:0,t:0,amount:0};pl.addMove('naruto-shadow-clones');
            const es=points.map(([x,y])=>enemy(x,y));pl.target=es[0]||null;return es;
          };
          const move=(level=1)=>G.Moves.instance(id,level),cast=m=>G.DigimonSkills.cast(pl,m||move());
          const active=()=>S.effects.find(f=>f.mode===mode);
          const step=t=>{for(let elapsed=0;elapsed<t-1e-9;elapsed+=.01)G.Combat.updateFields(Math.min(.01,t-elapsed));};
          const out={};
          try {
            assert(G.NarutoSkillCatalog.definitions.size===26,'Expected 26 definitions');
            for(const mon of G.Naruto.records.values()) {
              reset();pl.mon=mon;pl.dex=mon.dex;pl.level=9;
              assert(G.Moves.poolFor(mon).includes(id)===(mon.dex===30001),'Cloak leaked into another ninja pool');
            }
            reset();pl.addMove('naruto-naruto');pl.addMove('naruto-rasenshuriken');
            for(const level of [1,3,6,8]){pl.level=level;assert(!G.LevelUp.offer(pl,20).some(c=>c.key==='new:'+id),'Cloak unlocked before level 9');}
            pl.level=9;assert(G.LevelUp.offer(pl).some(c=>c.key==='new:'+id),'Missing guaranteed level 9 cloak');
            out.pool='Naruto only; guaranteed at level 9';

            reset([]);assert(!S.canCast(pl,move())&&!cast(),'Cloak wasted cooldown without danger');
            reset();pl.mon=G.Naruto.records.get(30002);pl.dex=30002;assert(!cast(),'Another ninja could cast Naruto cloak');
            reset();const m=move(),atk=pl.atk,spd=pl.spd;assert(cast(m),'Cloak did not activate');
            assert(near(pl.atk,atk*m.atkMul)&&near(pl.spd,spd*m.speedMul),'Buff getters not composed');
            const f=active();step(.3);const age=f.age;
            assert(!cast()&&active()===f&&f.age===age,'Cloak refreshed or stacked');
            pl.addMove('naruto-kunai');pl.setActive(pl.slots.findIndex(s=>s.some(m=>m.id==='naruto-kunai')));
            assert(active()===f&&near(pl.atk,atk*m.atkMul),'Switching skills removed cloak');
            pl.atkMul*=1.2;pl.spdMul*=1.1;
            assert(near(pl.atk,atk*1.2*m.atkMul)&&near(pl.spd,spd*1.1*m.speedMul),'Concurrent upgrades were overwritten');
            G.Combat.clearFields();assert(near(pl.atk,atk*1.2)&&near(pl.spd,spd*1.1),'Cleanup erased permanent upgrades');
            out.stats='temporary, nonstacking, switch-safe, concurrent upgrades retained';

            const damage=(cloaked,type,pure=false)=>{
              reset();pl.hp=100000;pl.dmgReduce=.2;pl.addMove('naruto-kunai');pl.setActive(pl.slots.findIndex(s=>s.some(m=>m.id==='naruto-kunai')));
              if(cloaked)cast();const hp=pl.hp;pl.hurt(100,type,pure);return hp-pl.hp;
            };
            for(const type of [null,'fire','water'])assert(near(damage(true,type),damage(false,type)*move().damageTakenMul),'Typed/reduction damage did not preserve defense: '+type);
            assert(near(damage(true,null,true),damage(false,null,true)),'Pure damage no longer bypasses cloak');
            reset();cast();pl.invuln=1;const hp=pl.hp;pl.hurt(100,'fire');assert(pl.hp===hp,'Cloak bypassed invulnerability');pl.dmgReduce=0;
            out.defense='typed damage, ordinary reduction, pure bypass, invulnerability';

            const victims=reset([[30,0],[-35,20],[0,-45],[250,0],[50,0],[-80,0]]),attackMove=move();
            G.World.isWall=(x,y)=>x>38&&x<42&&Math.abs(y)<10;G.World.projectileBlock=G.World.isWall;
            const dealt=pl.dmgDealt;cast(attackMove);step(attackMove.pulseInterval+.01);
            assert(victims.slice(0,3).every(e=>e.hp<1e7),'Pulse failed to hit three spread enemies');
            assert(victims[3].hp===1e7&&victims[4].hp===1e7,'Pulse hit outside radius or through wall');
            assert(victims[5].hp<1e7,'Pulse ignored a hitbox overlapping the radius boundary');
            assert(pl.dmgDealt>dealt,'Pulse damage was not credited to owner');
            const firstLoss=1e7-victims[0].hp;step(attackMove.pulseInterval+.01);
            assert(1e7-victims[0].hp>firstLoss,'Pulse did not repeat on simulation interval');
            G.World.isWall=()=>false;G.World.projectileBlock=()=>false;
            out.aoe='spread targets and radius-edge hitbox, repeated pulses, outside and wall excluded, owner credit';

            reset();const full=move(5);assert(cast(full),'Upgraded cloak activation failed');
            const ttl=active().ttl;assert(near(ttl,full.fieldDuration),'Upgraded duration ignored');step(ttl-.05);assert(active(),'Upgraded cloak expired early');step(.1);assert(!active(),'Cloak never expired');
            assert(near(pl.atk,pl.baseAtk*pl.atkMul),'Attack boost survived expiration');
            reset();cast();pl.dead=true;step(.01);assert(!active(),'Dead owner retained cloak');
            reset();cast();G.DigimonSkills.clear();assert(!active(),'Skill reset retained cloak');
            reset();cast();G.Combat.clearFields();assert(!active(),'Scene reset retained cloak');
            reset();cast();active().world={};step(.01);assert(!active(),'Effect retained a stale world reference');
            out.lifecycle={upgradedDuration:ttl,death:'cleared',skillReset:'cleared',sceneReset:'cleared'};

            reset();pl.quantityBonus=20;assert(cast(),'Quantity-enhanced cloak failed');
            assert(S.effects.filter(f=>f.mode===mode).length===1&&G.NarutoClones.actors.length===0,'Quantity created duplicate cloaks or recursive clones');
            const kunai=G.Moves.instance('naruto-kunai');
            const empowered=G.DigimonSkills.fireFrom(pl,kunai,0,0,0);
            assert(empowered.length&&empowered.every(p=>p.owner===pl&&p.narutoClone),'Copied technique lost clone tag or owner');
            const empoweredDamage=empowered[0].dmg;
            assert(S.effects.filter(f=>f.mode===mode).length===1,'Mirrored technique recursively cast cloak');
            G.Combat.clearFields();G.Projectiles.clear();
            const ordinary=G.DigimonSkills.fireFrom(pl,kunai,0,0,0);
            assert(near(empoweredDamage,ordinary[0].dmg*move().atkMul),'Clone copy did not inherit owner cloak attack multiplier');
            out.quantity='one cloak; no recursive summoning';out.cloneDamage='full owner cloak attack multiplier';return out;
          }finally{Object.assign(G.World,saved);G.Combat.clearFields();G.Projectiles.clear();pl.dead=false;pl.dmgReduce=0;}
        }''')
        # Exercise the real milestone UI, including full-slot tool replacement and binding.
        page.evaluate('''() => {
          G.Game.quit();G.Flow.goMenu();G.Naruto.choose(30001);G.Flow.play();
          const pl=G.Game.player;pl.level=8;pl.addMove('naruto-naruto');pl.addMove('naruto-rasenshuriken');pl.addMove('naruto-kunai');
          pl.bind['naruto-kunai']=1;pl.arrange();G.Game.debugLevelUp();
        }''')
        page.locator('#scr-levelup').wait_for(state='visible')
        card = page.locator('#cards .card').filter(has_text='九尾').first
        card.wait_for(state='visible')
        page.screenshot(path=str(ROOT / '.omx/naruto-cloak-card.png'), animations='disabled')
        card.click()
        page.wait_for_function("G.Game.player.hasMove('naruto-nine-tails-cloak')")
        assert page.evaluate("G.Game.player.slots.length===4&&G.Game.player.bind['naruto-nine-tails-cloak']===1&&G.Game.player.bind['naruto-kunai']==null")
        page.evaluate('''() => {
          const pl=G.Game.player;G.EnemyMgr.clear();G.Combat.clearFields();
          G.EnemyMgr.add(new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},pl.x+70,pl.y,{hp:1,spd:1,dmg:1}));G.EnemyMgr.rebuildGrid();
          if(!G.DigimonSkills.cast(pl,pl.moves.find(m=>m.id==='naruto-nine-tails-cloak')))throw Error('Live cloak cast failed');
        }''')
        page.wait_for_timeout(180)
        page.evaluate('G.Game.togglePause()')
        age = page.evaluate("G.NarutoSupport.effects.find(f=>f.mode==='nine-tails-cloak').age")
        page.wait_for_timeout(200)
        assert page.evaluate("G.NarutoSupport.effects.find(f=>f.mode==='nine-tails-cloak').age") == age
        page.locator('#scr-pause').evaluate("el=>el.style.visibility='hidden'")
        page.screenshot(path=str(ROOT / '.omx/naruto-cloak-game.png'), animations='disabled')
        page.locator('#scr-pause').evaluate("el=>el.style.visibility=''")
        page.evaluate('G.Game.togglePause()')
        page.wait_for_function("G.NarutoSupport.effects.find(f=>f.mode==='nine-tails-cloak')?.pulseFlash>.1")
        page.evaluate('G.Game.togglePause()')
        page.locator('#scr-pause').evaluate("el=>el.style.visibility='hidden'")
        page.screenshot(path=str(ROOT / '.omx/naruto-cloak-pulse.png'), animations='disabled')
        page.locator('#scr-pause').evaluate("el=>el.style.visibility=''")
        page.evaluate('G.Game.quit();G.Flow.goMenu()')
        assert page.evaluate("!G.NarutoSupport.effects.some(f=>f.mode==='nine-tails-cloak')")
        assert not errors, errors
        assert not missing, missing
        print(json.dumps({'passed': report, 'actualLevel9Choice': 'passed; full slot replacement preserves binding', 'pause': 'simulation age frozen', 'pageErrors': errors, 'missing': missing}, ensure_ascii=False))
    finally:
        browser.close()
