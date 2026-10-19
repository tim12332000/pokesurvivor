"""Exercise cumulative Sharingan evolution in the real sandbox browser."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import mimetypes
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW'

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    def route_file(route):
        file = ROOT / unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
        route.fulfill(status=200 if file.is_file() else 404, body=file.read_bytes() if file.is_file() else b'', content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
    context = browser.new_context(viewport={'width':1280,'height':820}, locale='zh-TW', service_workers='block')
    context.route('https://tim12332000.github.io/pokesurvivor/**', route_file)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda message: print(message.text, flush=True) if message.text.startswith('CHECK:') else None)
    def start(page):
        page.goto(URL, wait_until='domcontentloaded')
        page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible(): page.locator('#tap-start').click()
        page.evaluate('G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
    start(page)
    def evaluate(script):
        try:
            return page.evaluate(script)
        except Exception:
            browser.close()
            raise
    report = evaluate(r'''() => {
      const assert=(ok,msg)=>{if(!ok)throw Error(msg);},near=(a,b)=>Math.abs(a-b)<.00001;
      const pl=G.Game.player,S=G.NarutoSharingan,id='naruto-sharingan';
      assert(S&&G.NarutoSharinganPowers,'Sharingan runtime not loaded');
      const saved={};for(const k of ['isFree','isWall','collide','projectileBlock','propsInCircle','isLiquid'])saved[k]=G.World[k];
      const random=Math.random,sees=G.Camera.sees;
      Object.assign(G.World,{isFree:()=>true,isWall:()=>false,collide:()=>{},projectileBlock:()=>false,propsInCircle:()=>[],isLiquid:()=>false});G.Camera.sees=()=>true;
      const reset=(level=1)=>{
        G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();
        pl.mon=G.Naruto.records.get(30002);pl.dex=30002;pl.x=pl.y=pl.aim=0;pl.dead=false;pl.hp=pl.maxHp;pl.invuln=0;pl.frozen=0;
        pl.quantityBonus=0;pl.critChance=0;pl.atkMul=1;pl.dmgReduce=0;pl.lifestealRate=0;pl.magnet=100;pl.buffs.atk={n:0,t:0,amount:0};
        pl.moves=[];pl.slots=[];pl.bind={};pl.active=0;pl.target=null;
        pl.addMove('naruto-kunai');if(level){pl.addMove(id);Object.assign(pl.moves.find(m=>m.id===id),G.Moves.instance(id,level));}
        S.sync(pl);
      };
      const step=t=>{for(let elapsed=0;elapsed<t-1e-9;elapsed+=1/120){G.EnemyMgr.rebuildGrid();G.Combat.updateFields(Math.min(1/120,t-elapsed));}};
      const enemy=(x,y,hp=100000,boss=false)=>{const e=new G.Enemy({dex:19,hp,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];e.boss=boss;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;};
      const releaseTime=move=>move.id==='naruto-fireball'?G.NarutoFireball.config.sealDuration:move.charge||0;
      const countShot=(move)=>{G.Projectiles.clear();assert(G.DigimonSkills.cast(pl,move),'Cast failed '+move.id);step(releaseTime(move)+.02);return G.Projectiles.all().length;};
      const out={};
      try {
        reset(0);const offensive=pl.activeGroup(),kunai=offensive[0];kunai.t=.77;
        assert(pl.addMove(id),'Fresh Sharingan learn failed');
        assert(pl.activeGroup()===offensive&&pl.activeGroup().includes(kunai),'Learning passive selected Sharingan and stopped attacks');
        assert(near(kunai.t,.77),'Learning passive reset offensive cooldown');S.sync(pl);assert(S.stage(pl)===1&&near(pl.magnet,120),'Fresh learned passive did not apply');
        reset(0);pl.moves=[];pl.slots=[];pl.bind={};pl.active=0;
        for(const moveId of ['naruto-sasuke','naruto-kunai','naruto-shuriken','naruto-fireball'])assert(pl.addMove(moveId),'Full-slot fixture failed '+moveId);
        pl.level=6;pl.bind['naruto-kunai']=1;pl.arrange();pl.setActive(pl.slots.findIndex(s=>s.some(m=>m.id==='naruto-kunai')));
        const signature=G.LevelUp.offer(pl,100).find(c=>c.key==='new:'+id);
        assert(signature&&signature.apply(pl),'Guaranteed level-6 full-slot Sharingan replacement missing');
        assert(pl.slots.length===4&&pl.hasMove(id)&&!pl.hasMove('naruto-kunai'),'Sharingan did not replace shared kunai slot');
        assert(pl.bind[id]===1&&pl.bind['naruto-kunai']==null,'Replacement lost the shared-slot binding');
        assert(pl.activeGroup().some(m=>!m.passive)&&pl.activeGroup().every(m=>m.id!==id),'Full-slot passive replacement left attacks disabled');
        S.sync(pl);assert(S.stage(pl)===1&&near(pl.magnet,120),'Full-slot passive failed to apply stage 1');
        out.learning='fresh passive learning preserves offensive slot and cooldown; level-6 full-slot shared-tool replacement keeps offense active';
        for(let lv=1;lv<=5;lv++){reset(lv);assert(S.stage(pl)===lv,'Instance did not evolve to '+lv);assert(near(pl.magnet,120),'Magnet bonus missing');S.sync(pl);assert(near(pl.magnet,120),'Magnet stacked');}
        pl.magnet*=1.3;pl.moves=pl.moves.filter(m=>m.id!==id);S.sync(pl);assert(near(pl.magnet,130),'Unlearn erased later magnet card');
        reset(3);pl.setActive(0);assert(S.stage(pl)===3,'Switching active slot disabled learned Sharingan');
        pl.dex=30001;S.sync(pl);assert(S.stage(pl)===0&&near(pl.magnet,100),'Naruto inherited Sharingan');
        out.passive='five cumulative stages; learned independent of active slot; magnet composes and restores';
        console.log('CHECK: passive');

        reset(1);Math.random=()=>.049;const hp=pl.hp;pl.hurt(10);assert(pl.hp===hp,'5% dodge missing');assert(!G.Projectiles.count,'Stage 1 emitted counters');
        reset(1);Math.random=()=>.051;const before=pl.hp;pl.hurt(10);assert(pl.hp<before,'Dodge exceeded 5%');
        reset(2);Math.random=()=>.049;pl.hurt(10);assert(G.Projectiles.count===3,'Stage 2 must counter with three shuriken');
        assert(G.Projectiles.all().every(p=>p.owner===pl),'Counter lost ownership');
        reset(2);pl.quantityBonus=2;pl.hurt(10);assert(G.Projectiles.count===5,'Counter failed quantity +2');
        reset(2);pl.hurt(10);const firstCounter=G.Projectiles.count;pl.invuln=0;step(.17);pl.hurt(10);assert(G.Projectiles.count===firstCounter+3,'Second legitimate dodge failed to counter');
        const burst=G.FX.burst,sound=G.Audio.sfx;G.FX.burst=()=>{};G.Audio.sfx=()=>{};
        try{for(const [flag,value,amount,pure] of [['invuln',1,10,false],['frozen',1,10,false],['dead',true,10,false],['hp',0,10,false],['invuln',0,0,false],['invuln',0,10,true]]){
          reset(0);pl[flag]=value;let calls=0;Math.random=()=>{calls++;return .049;};pl.hurt(amount,null,pure);const ordinaryCalls=calls;
          reset(2);pl[flag]=value;calls=0;pl.hurt(amount,null,pure);
          assert(!G.Projectiles.count,'Ineligible hurt emitted counter: '+flag+'/'+pure);assert(calls===ordinaryCalls,'Ineligible hurt consumed extra dodge random: '+flag+'/'+pure);
        }}finally{G.FX.burst=burst;G.Audio.sfx=sound;}
        Math.random=()=>.9;out.dodge='5% boundary, stage 2 radial counters, quantity, ownership, ineligible hurt guards';
        console.log('CHECK: dodge');

        for(const moveId of ['naruto-kunai','naruto-shuriken','naruto-fireball','naruto-fuma-shuriken']){
          console.log('CHECK: projectile '+moveId);
          reset(2);pl.target=enemy(150,0);const base=G.Moves.instance(moveId),n=countShot(base);
          reset(3);pl.target=enemy(150,0);assert(countShot(G.Moves.instance(moveId))===n+1,moveId+' missing ranged +1');
          reset(3);pl.quantityBonus=2;pl.target=enemy(150,0);const snap=G.Quantity.snapshot(pl,G.Moves.instance(moveId));
          assert(snap.quantityBonusAtCast===2&&snap.count===base.count+3,'Quantity/Sharingan did not combine exactly once');
          assert(G.Quantity.snapshot(pl,snap).count===snap.count,'Snapshot applied bonus twice');
        }
        for(const moveId of ['naruto-fireball','naruto-fuma-shuriken']){
          console.log('CHECK: snapshot '+moveId);
          reset(3);pl.target=enemy(150,0);const m=G.Moves.instance(moveId);G.DigimonSkills.cast(pl,m);
          pl.moves.find(m=>m.id===id).lvl=1;step(releaseTime(m)+.02);
          assert(G.Projectiles.count===m.count+1,'Delayed '+moveId+' lost cast-time bonus');
        }
        reset(3);for(const moveId of ['naruto-sasuke','naruto-shadow-clones','naruto-nine-tails-cloak']){
          console.log('CHECK: excluded '+moveId);
          const m=G.Moves.instance(moveId),snap=G.Quantity.snapshot(pl,m);assert(snap.count===m.count,'Sharingan added nonprojectile count to '+moveId);
        }
        const vanilla=Object.assign(G.Moves.instance('ember'),{count:2,kind:'projectile',dmg:10,radius:500,range:500,speed:300,life:2,size:5,cd:1});
        for(const kind of ['projectile','nova','boomerang','cone']){reset(3);pl.target=enemy(150,0);const m={...vanilla,kind,t:0};pl.moves.push(m);pl.slots=[[m]];pl.active=0;G.Combat.tick(.001,pl,0);assert(G.Projectiles.count===(kind==='nova'?4:3),'Vanilla '+kind+' missing +1 actual='+G.Projectiles.count+' move='+JSON.stringify(m));}
        out.projectiles='custom and vanilla ranged +1; passive quantity stacks once; delayed cast snapshots; excluded melee/clones/buffs';
        console.log('CHECK: projectiles');

        const damage=(level)=>{reset(level);step(.01);pl.hp=100000;pl.dmgReduce=.2;const h=pl.hp;pl.hurt(100,'fire');return h-pl.hp;};
        assert(near(damage(5),damage(3)*.7),'Susanoo damage reduction failed to compose');
        out.defense='Susanoo reduces actual typed damage by 30%, preserving ordinary defense';
        console.log('CHECK: defense');
        reset(4);const center=enemy(200,0),pulled=enemy(245,20),boss=enemy(245,-20,100000,true);step(.21);
        assert(Math.hypot(pulled.x-200,pulled.y)<Math.hypot(boss.x-200,boss.y),'Boss pull was not weaker than ordinary pull');
        step(1);const P=G.NarutoSharinganPowers;
        assert(P.fields.length===1&&!P.holes.length,'Collapsed hole must leave one flame patch');
        const f=P.fields[0];G.EnemyMgr.clear();
        const victims=[enemy(f.x,f.y),enemy(f.x-25,f.y+20),enemy(f.x+25,f.y-20)],outside=enemy(450,0),elite=enemy(f.x,f.y+10,200000),burnBoss=enemy(f.x,f.y-10,100000,true);
        pl.lifestealRate=.01;pl.hp=pl.maxHp/2;const ownerHp=pl.hp,credited=pl.dmgDealt;
        step(.5);assert(victims.every(e=>near(e.maxHp-e.hp,1000)),'Flame did not burn three spread targets for 1% maxHP per tick');
        assert(outside.hp===outside.maxHp,'Flame hit outside actual radius');assert(near(elite.maxHp-elite.hp,2000),'Flame must scale with maximum HP');
        assert(near(burnBoss.maxHp-burnBoss.hp,250),'Boss flame rate must be 0.5% maxHP/s');
        assert(pl.dmgDealt>credited&&pl.hp>ownerHp,'Flame did not grant owner credit and lifesteal');
        const oldHp=victims[0].hp;step(.5);assert(near(oldHp-victims[0].hp,1000),'Flame scaled with current HP rather than maximum HP');
        enemy(f.x+90,f.y);step(9.1);assert(P.fields.length>=2,'Unburnt target did not produce a second permanent flame patch');
        G.EnemyMgr.clear();const overlap=enemy(f.x+45,f.y);const overlapHp=overlap.hp;step(.5);
        assert(near(overlapHp-overlap.hp,1000),'Overlapping flame patches multiplied burn damage');
        G.EnemyMgr.clear();step(61);assert(P.fields.length>=2&&P.fields[0]===f&&f.age>60,'Black flame expired with age');
        pl.moves=pl.moves.filter(m=>m.id!==id);step(.01);assert(!P.fields.length&&!P.holes.length&&!P.slashes.length,'Unlearn left permanent powers');
        out.amaterasu='real three-target AOE, radius exclusion, maximum HP scaling, reduced boss damage, weaker boss pull, nonstacking overlap, permanent ground and owner lifesteal';
        console.log('CHECK: amaterasu');
        reset(5);const swordTargets=[enemy(50,0),enemy(70,35),enemy(70,-35)],swordOutside=enemy(-100,0);const swordCredit=pl.dmgDealt;
        step(.01);assert(swordTargets.every(e=>e.hp<e.maxHp),'Susanoo sword missed spread AOE targets');assert(swordOutside.hp===swordOutside.maxHp,'Sword hit outside its circle');
        assert(pl.dmgDealt>swordCredit&&P.slashes.length===1,'Sword lost owner credit or visible slash');
        const first=swordTargets[0].hp;step(2);assert(swordTargets[0].hp<first,'Susanoo sword did not repeat');
        out.susanoo='actual repeated three-target sword AOE with outside exclusion and owner credit';
        reset(5);step(.01);pl.dead=true;step(.01);assert(S.stage(pl)===0&&near(pl.magnet,100),'Death retained passive');
        reset(5);G.Combat.clearFields();assert(near(pl.magnet,100),'Scene clear retained magnet');
        out.lifecycle='death and scene clear restore bonuses';
        return out;
      } finally {Math.random=random;Object.assign(G.World,saved);G.Camera.sees=sees;G.Combat.clearFields();G.Projectiles.clear();}
    }''')
    page.evaluate("G.Combat.clearFields();const pl=G.Game.player;pl.dead=false;pl.hp=pl.maxHp;pl.moves=[];pl.slots=[];pl.bind={};pl.active=0;pl.addMove('naruto-kunai');pl.addMove('naruto-sharingan')")
    for level, text in [(2,'二勾玉'),(3,'三勾玉'),(4,'天照'),(5,'須佐能乎')]:
        page.evaluate("""level => {const pl=G.Game.player,c=G.LevelUp.offer(pl,100).find(c=>c.key==='up:naruto-sharingan');if(!c)throw Error('Missing evolution upgrade card '+level);G.RunUI.showLevelUp(level,[c],picked=>picked.apply(pl));}""", level)
        card=page.locator('#cards .card').first
        assert text in card.inner_text(), f'Stage {level} card lacks evolution name'
        card.click()
        assert page.evaluate('G.NarutoSharingan.stage(G.Game.player)') == level
    assert page.evaluate("!G.LevelUp.offer(G.Game.player,100).some(c=>c.key==='up:naruto-sharingan')"),'Stage 5 still offers evolution upgrade'
    report['cards']='four actual rendered upgrade-card clicks evolve through stages 2–5 and stop at stage 5'
    capture = r'''() => {
      const pl=G.Game.player;G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();
      pl.dead=false;pl.hp=pl.maxHp;pl.invuln=0;pl.moves=[];pl.slots=[];pl.bind={};pl.active=0;
      pl.addMove('naruto-kunai');pl.addMove('naruto-sharingan');Object.assign(pl.moves.find(m=>m.id==='naruto-sharingan'),G.Moves.instance('naruto-sharingan',5));
      const create=(x,y)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});G.EnemyMgr.add(e);return e;};
      const target=create(pl.x+110,pl.y-15);G.EnemyMgr.rebuildGrid();pl.target=target;
      for(let t=0;t<1.12;t+=1/120)G.Combat.updateFields(1/120);
      create(pl.x+60,pl.y+40);create(pl.x+70,pl.y-55);G.EnemyMgr.rebuildGrid();
      for(let t=0;t<.92;t+=1/120)G.Combat.updateFields(1/120);
      G.Camera.x=pl.x;G.Camera.y=pl.y;document.getElementById('scr-pause').style.visibility='hidden';
    }'''
    page.evaluate(capture);page.wait_for_timeout(60)
    page.screenshot(path=str(ROOT/'.omx/sharingan-evolution-desktop.png'))
    mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='zh-TW',service_workers='block')
    mobile.route('https://tim12332000.github.io/pokesurvivor/**',route_file)
    phone=mobile.new_page();phone.on('pageerror',lambda e:errors.append(str(e)));start(phone);phone.evaluate(capture);phone.wait_for_timeout(60)
    phone.screenshot(path=str(ROOT/'.omx/sharingan-evolution-mobile.png'))
    page.evaluate('G.Game.quit();G.Flow.goMenu();G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
    assert page.evaluate('G.NarutoSharingan.stage(G.Game.player)===0&&!G.NarutoSharinganPowers.fields.length&&!G.NarutoSharinganPowers.holes.length'),'New run retained Sharingan evolution'
    assert not errors, errors
    print(json.dumps({'ok':True,'checks':report},ensure_ascii=False), flush=True)
    browser.close()
