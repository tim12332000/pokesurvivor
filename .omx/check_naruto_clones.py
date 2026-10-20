"""Browser checks for shadow clone actors, training choices and lifecycle."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright
import json
import mimetypes
import os

ROOT=Path(__file__).resolve().parent.parent
URL='https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=naruto-shadow-clones'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(locale='zh-TW',viewport={'width':1280,'height':820},service_workers='block')
    if os.environ.get('PAGES_LIVE')!='1':
        def proxy(route):
            file=ROOT/unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
            if file.is_file():route.fulfill(status=200,body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
            else:route.fulfill(status=404,body='Not found')
        context.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
    page=context.new_page();errors=[];missing=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:missing.append(r.url) if r.status>=400 else None)
    page.goto(URL);page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.evaluate('G.Naruto.choose(30001);G.Flow.play();G.Game.togglePause()')
    report=page.evaluate('''() => {
      const assert=(ok,msg)=>{if(!ok)throw Error(msg);};
      const pl=G.Game.player,A=G.NarutoClones;
      const saved={isFree:G.World.isFree,collide:G.World.collide,projectileBlock:G.World.projectileBlock,isWall:G.World.isWall,propsInCircle:G.World.propsInCircle,isLiquid:G.World.isLiquid};
      const oldPath=G.Path.dirFor;
      Object.assign(G.World,{isFree:()=>true,collide:()=>{},projectileBlock:()=>false,isWall:()=>false,propsInCircle:()=>[],isLiquid:()=>false});
      const setup=(points=[])=>{
        G.Combat.clearFields();G.Projectiles.clear();G.FX.clear();G.EnemyMgr.clear();
        pl.x=pl.y=0;pl.hp=pl.maxHp;pl.dead=false;pl.level=1;pl.atkMul=1;pl.critChance=0;pl.moves=[];pl.slots=[];pl.bind={};pl.active=0;
        pl.addMove('naruto-shadow-clones');
        const enemies=points.map(([x,y])=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:5,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];G.EnemyMgr.add(e);return e;});
        G.EnemyMgr.rebuildGrid();return enemies;
      };
      const cast=level=>A.cast(pl,G.Moves.instance('naruto-shadow-clones',level));
      const step=seconds=>{for(let t=0;t<seconds;t+=1/60)G.Combat.updateFields(1/60);};
      try {
        assert(pl.moves[0].id==='naruto-shadow-clones','Wrong Naruto starting move');
        setup();assert(cast(1)&&A.actors.length===8,'Initial eight clones');
        assert(G.Moves.BY_ID['naruto-shadow-clones'].cd===4,'Clone cooldown was not shortened');
        assert(A.actors.every(a=>!(a instanceof G.Player)&&!a.moves&&!a.slots),'Clones became full players');
        step(1);const old=A.actors.map(a=>({id:a.id,age:a.age}));cast(1);
        assert(A.actors.length===8&&old.every(x=>A.actors.find(a=>a.id===x.id).age===x.age),'Recast refreshed TTL');
        cast(3);assert(A.actors.length===24,'Level3 quantity');cast(5);cast(5);assert(A.actors.length===40,'Level5 quantity');
        setup();cast(1);const quantity=pl.moves[0];
        const quantityCard=G.LevelUp.offer(pl,20).find(c=>c.key==='up:naruto-shadow-clones');
        assert(quantityCard&&quantityCard.desc.includes('16'),'Quantity upgrade missing from level-up choices');
        const counts=[8];
        quantityCard.apply(pl);counts.push(A.actors.length);
        while(quantity.lvl<quantity.def.maxLvl){G.Moves.levelUp(quantity);counts.push(A.actors.length);}
        assert(JSON.stringify(counts)==='[8,16,24,32,40]','Upgrade quantities differ from requested progression');
        assert(JSON.stringify(counts)===JSON.stringify(A.config.counts),'UI and actor config diverged');
        assert(quantity.def.maxLvl===A.config.counts.length&&quantity.def.ups.length===A.config.counts.length-1,'Configured levels and choices diverged');
        setup();
        const spell=pl.moves[0],seal=G.Naruto.records.get(30001);
        G.Combat.tick(.01,pl,0);
        assert(!A.actors.length&&pl.anim.cur==='Charge'&&!A.canCast(pl,spell),'Missing seal windup or duplicate summon permitted');
        assert(JSON.stringify(G.Naruto.frameFor(seal,'Charge',0,2).rect)==='[129,240,14,29]','Incorrect source row for seal');
        step(A.config.sealDuration-.02);assert(!A.actors.length,'Clones appeared before seal completed');
        step(.04);assert(A.actors.length===8&&A.actors.every(a=>a.anim.cur!=='Charge'),'Clones did not emerge after seal, or recursively performed summon pose');
        setup();A.beginCast(pl,spell);pl.dead=true;step(.5);pl.dead=false;assert(!A.actors.length,'Dead owner released pending summon');
        A.beginCast(pl,spell);G.Combat.clearFields();step(.5);assert(!A.actors.length,'Scene clear left pending summon');
        setup();let summons=0;const originalCast=pl.cast;
        pl.cast=function(m){summons++;return originalCast.call(this,m);};
        try {
          for(let t=0;t<7;t+=1/60){G.Combat.tick(1/60,pl,t);G.Combat.updateFields(1/60);}
          assert(summons===2&&A.actors.length===8&&A.actors.every(a=>a.age<.5),'Full-cap poll wasted cooldown or spammed casting');
        }finally{delete pl.cast;}
        cast(5);
        pl.addMove('naruto-naruto');assert(A.actors.length===40,'Slot switch dismissed clones');
        step(7.2);assert(A.actors.length===0,'Inactive clones survived their TTL');
        const enemies=setup([[120,0],[90,95],[-75,100]]);cast(1);const before=A.actors.map(a=>[a.x,a.y]);
        const resources=[pl.xp,pl.coins,pl.t1,pl.t10,localStorage.getItem('ps.sandbox.digimon.v1')];
        step(1.5);assert(enemies.every(e=>e.hp<100000),'Clones did not spread attacks');
        assert(A.actors.some((a,i)=>Math.hypot(a.x-before[i][0],a.y-before[i][1])>4),'Clones never moved');
        assert(JSON.stringify(resources)===JSON.stringify([pl.xp,pl.coins,pl.t1,pl.t10,localStorage.getItem('ps.sandbox.digimon.v1')]),'Clones wrote rewards/storage');
        setup();G.World.isFree=()=>false;assert(!cast(1)&&A.actors.length===0,'Spawned inside a wall');
        G.Combat.tick(.02,pl,0);assert(pl.moves[0].t<=.25,'Failed summon consumed full cooldown');
        G.World.isFree=()=>true;G.Combat.tick(.3,pl,.3);step(A.config.sealDuration+.02);assert(A.actors.length===8,'Failed summon did not recover');
        setup([[130,0]]);G.World.isFree=(x)=>x<65;G.World.projectileBlock=(x)=>x>=65;cast(1);
        const target=G.EnemyMgr.all()[0];step(1);
        assert(A.actors.every(a=>a.x<65)&&target.hp===100000,'Clone crossed or hit through a wall');
        G.World.isFree=()=>true;G.World.projectileBlock=()=>false;
        // A contact hit consumes the clone, without damaging the owner.
        setup();cast(1);step(.3);let clone=A.actors[0],hp=pl.hp;
        const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:5,xp:0,behavior:'chase'},clone.x,clone.y,{hp:1,spd:1,dmg:1});G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();step(.03);
        assert(A.actors.length===7&&pl.hp===hp,'Contact did not consume one clone');
        setup();cast(1);step(.3);clone=A.actors[0];
        const hostile=G.Projectiles.spawn({x:clone.x,y:clone.y,px:clone.x-30,py:clone.y,friendly:false,r:3,dmg:5});
        const friendly=G.Projectiles.spawn({x:clone.x,y:clone.y,friendly:true,r:3,dmg:5,hits:new Set(),mtype:'normal'});
        G.Combat.resolve(.01,pl,0);assert(A.actors.filter(a=>!a.dead).length===7&&!G.Projectiles.all().includes(hostile)&&G.Projectiles.all().includes(friendly),'Projectile interception');
        // Ordinary pursuers can target a closer clone; bosses still receive the real owner.
        setup();cast(1);clone=A.actors[0];clone.x=70;clone.y=50;
        for(const a of A.actors.slice(1)){a.x=-100;a.y=-100;}
        let seen;G.Path.dirFor=(e,who)=>{seen=who;return null;};
        const pursuer=new G.Enemy({dex:19,hp:100000,spd:50,dmg:5,xp:0,behavior:'chase'},70,95,{hp:1,spd:1,dmg:1});
        pursuer.update(.1,pl);assert(seen&&seen.x===clone.x&&seen.y===clone.y,'Ordinary enemy ignored closer clone');
        const boss=new G.Enemy({dex:19,hp:100000,spd:50,dmg:5,xp:0,behavior:'chase'},70,95,{hp:1,spd:1,dmg:1});boss.boss=true;boss.flying=true;
        boss.bossMove=(dt,who,dist,dx,dy,spd)=>{seen=who;return [dx*spd,dy*spd,'Walk'];};boss.update(.1,pl);
        assert(seen===pl,'Boss aggro was redirected');G.Path.dirFor=oldPath;
        const circle=Array.from({length:8},(_,i)=>[Math.cos(i*Math.PI/4)*130,Math.sin(i*Math.PI/4)*130]);
        const victims=setup(circle);cast(1);pl.addMove('naruto-naruto');
        step(1);
        const loss=victims.reduce((sum,e)=>sum+100000-e.hp,0),budget=48*pl.atk*G.Types.mult('fighting',['normal']);
        assert(A.actors.every(a=>a.mimickedId==='naruto-naruto')&&victims.every(e=>e.hp<100000),'Switched skill not used by clones');
        assert(loss>=budget*7&&A.combo(pl,G.Moves.instance('naruto-naruto'))===0,'Clones still share a damage budget');
        const high=setup(circle);for(const e of high)e.hp=e.maxHp=1e16;
        cast(1);pl.addMove('naruto-naruto');pl.moves.find(m=>m.id==='naruto-naruto').dmg=1e6;pl.atkMul=1e5;
        step(1);assert(high.some(e=>1e16-e.hp>1e10),'Large damage was capped');pl.atkMul=1;
        const fireFrom=G.DigimonSkills.fireFrom,mirrored=[];
        const frames=seconds=>{for(let t=0;t<seconds;t+=1/120){G.Projectiles.update(1/120,pl,G.EnemyMgr.all());G.Combat.resolve(1/120,pl,t);G.Combat.updateFields(1/120);}};
        try {
          G.DigimonSkills.fireFrom=(owner,move,x,y,aim,scale)=>{
            const shots=fireFrom(owner,move,x,y,aim,scale);
            assert(owner===pl&&shots.every(p=>p.owner===pl&&p.narutoClone),'Mimic projectiles lost real ownership');
            assert(Math.abs(scale-1)<1e-9,'Clone damage was divided');
            if(move.id==='naruto-rasenshuriken')assert(shots.every(p=>p.digiBomb&&Math.abs(p.digiBomb.m.dmg-move.dmg)<1e-9),'Splash was still divided');
            mirrored.push({id:move.id,count:shots.length});return shots;
          };
          for(const id of ['naruto-rasenshuriken','naruto-kunai','naruto-shuriken']) {
            const enemies=setup(circle);cast(1);pl.addMove(id);const before=mirrored.length;
            frames(.8);
            const casts=mirrored.slice(before);
            assert(casts.length===8&&casts.every(c=>c.id===id),'Not all eight clones mimicked '+id);
            assert(casts.reduce((sum,c)=>sum+c.count,0)===(id==='naruto-shuriken'?64:8),'Wrong projectile count');
            assert(A.actors.every(a=>a.mimickedId===id),'Wrong active mimic marker');
            frames(.5);assert(enemies.some(e=>e.hp<100000),'Mimic projectiles dealt no damage');
            if(id==='naruto-rasenshuriken')assert(enemies.reduce((sum,e)=>sum+100000-e.hp,0)>58*pl.atk*8,'Total splash retained the old budget');
          }
          setup(circle);cast(1);pl.addMove('naruto-kunai');pl.addMove('naruto-naruto');pl.setActive(1);frames(.35);
          const clone=A.actors[0],remaining=clone.cooldowns.get('naruto-kunai');
          assert(remaining>0,'Kunai cooldown not tracked');pl.setActive(2);frames(.02);pl.setActive(1);frames(.02);
          assert(clone.cooldowns.get('naruto-kunai')>0&&clone.cooldowns.get('naruto-kunai')<remaining,'Switching reset clone cooldown');
          // Scene clear removes clone shots while retaining an ordinary player shot.
          setup(circle);cast(1);pl.addMove('naruto-rasenshuriken');frames(.3);
          const ownShot=G.Projectiles.spawn({x:-100,y:-100,owner:pl,hits:new Set(),mtype:'normal'});
          assert(G.Projectiles.all().some(p=>p.narutoClone),'No clone shots to clear');G.Combat.clearFields();
          assert(!G.Projectiles.all().some(p=>p.narutoClone)&&G.Projectiles.all().includes(ownShot),'Cleanup removed ordinary shots or left clone shots');
        }finally{G.DigimonSkills.fireFrom=fireFrom;}
        setup();cast(1);pl.dead=true;step(.05);assert(!A.actors.length,'Dead-owner clones survived');pl.dead=false;
        cast(1);G.Combat.clearFields();assert(!A.actors.length,'Scene clear leaked clones');
        // Fixed training options and explicit tool replacement when slots are full.
        setup();pl.level=2;assert(!G.LevelUp.offer(pl).some(c=>c.key==='new:naruto-naruto'),'Rasengan unlocked too early');
        pl.level=3;let card=G.LevelUp.offer(pl).find(c=>c.key==='new:naruto-naruto');assert(card,'Missing level3 Rasengan');card.apply(pl);
        pl.addMove('naruto-kunai');pl.addMove('naruto-shuriken');pl.level=6;
        pl.bind['naruto-kunai']=1;pl.arrange();
        card=G.LevelUp.offer(pl).find(c=>c.key==='new:naruto-rasenshuriken');assert(card&&card.desc.includes('替換'),'Full slots hide character skill');
        card.apply(pl);assert(pl.hasMove('naruto-rasenshuriken')&&pl.hasMove('naruto-naruto')&&pl.hasMove('naruto-shadow-clones')&&pl.slots.length===4,'Skill replacement broke slots');
        assert(pl.bind['naruto-rasenshuriken']===1&&pl.bind['naruto-kunai']==null,'Replacement lost binding');
        return {quantity:counts,seal:'original hands-together frames, delayed release and cancellation passed',punches:'three spread enemies',walls:'passed',contact:'passed',projectiles:'passed',aggro:'ordinary only',mimic:['Rasengan','Rasenshuriken','Kunai','Shuriken'],mimicDamage:'full damage per clone; no total budget',switchCooldown:'preserved',lifecycle:'passed',training:'quantity upgrade plus Lv3/Lv6 choices',resources:'unchanged'};
      }finally{Object.assign(G.World,saved);G.Path.dirFor=oldPath;G.Combat.clearFields();pl.dead=false;}
    }''')
    # Capture actual animator/actor states across the seal, not hand-picked idle art.
    page.evaluate('''() => {
      const pl=G.Game.player,A=G.NarutoClones,free=G.World.isFree,block=G.World.projectileBlock;
      G.Combat.clearFields();G.EnemyMgr.clear();pl.hp=pl.maxHp;pl.dead=false;
      try {
        G.World.isFree=()=>true;G.World.projectileBlock=()=>false;
        const panel=document.createElement('canvas');panel.id='clone-seal-timeline';panel.width=1200;panel.height=270;
        panel.style.cssText='position:fixed;top:0;left:0;z-index:30000';
        const ctx=panel.getContext('2d');ctx.fillStyle='#102442';ctx.fillRect(0,0,1200,270);
        const move=G.Moves.instance('naruto-shadow-clones');
        A.beginCast(pl,move);
        let elapsed=0;
        for(const [index,time] of [0,.11,.25,.43].entries()) {
          const dt=time-elapsed;pl.anim.update(dt);A.update(dt);elapsed=time;
          if(index===2&&pl.anim.frame!==2)throw Error('Final seal pose not held until release');
          ctx.save();ctx.beginPath();ctx.rect(index*300,35,300,235);ctx.clip();
          ctx.translate(index*300+150-pl.x,180-pl.y);
          pl.anim.draw(ctx,pl.x,pl.y);A.draw(ctx);ctx.restore();
          ctx.fillStyle='#ffffff';ctx.font='16px sans-serif';
          ctx.fillText(time.toFixed(2)+'s / '+pl.anim.cur+' / clones: '+A.actors.length,index*300+12,25);
        }
        document.body.append(panel);
      } finally {G.World.isFree=free;G.World.projectileBlock=block;G.Combat.clearFields();}
    }''')
    page.locator('#clone-seal-timeline').screenshot(path=str(ROOT/'.omx/naruto-seal-timeline.png'))
    page.evaluate("document.getElementById('clone-seal-timeline').remove()")
    page.evaluate('''() => {
      G.Game.quit();G.Flow.goMenu();
      const perks=G.Upgrades.perks,pick=G.U.pick;
      try {
        G.Upgrades.perks=(...args)=>({...perks(...args),startMoves:2});
        G.U.pick=list=>list.find(id=>id==='naruto-rasenshuriken')||list.find(id=>id==='naruto-naruto')||pick(list);
        G.Naruto.choose(30001);G.Flow.play();
        const ids=G.Game.player.moves.map(m=>m.id);
        if(ids.length!==1||ids[0]!=='naruto-shadow-clones')throw Error('Extra starter perk bypassed training levels');
      }finally{G.Upgrades.perks=perks;G.U.pick=pick;G.Game.quit();G.Flow.goMenu();}
    }''')
    # A fresh live run proves automatic summoning, and pause freezes actual actors.
    page.evaluate('G.Game.quit();G.Flow.goMenu();G.Naruto.choose(30001);G.Flow.play()')
    page.wait_for_function('G.NarutoClones.actors.length===8')
    page.evaluate('G.Game.togglePause()')
    age=page.evaluate('G.NarutoClones.actors[0]?.age')
    assert isinstance(age,(int,float))
    page.wait_for_timeout(900)
    assert page.evaluate('G.NarutoClones.actors[0]?.age')==age
    page.evaluate('G.Game.togglePause()')
    page.wait_for_timeout(700)
    page.screenshot(path=str(ROOT/'.omx/naruto-shadow-clones.png'),animations='disabled')
    page.evaluate('G.Sprites.preload([19])')
    page.evaluate('''() => {
      const pl=G.Game.player,points=[];
      for(let i=0;i<12&&points.length<3;i++) {
        const a=i*Math.PI/6,x=pl.x+Math.cos(a)*125,y=pl.y+Math.sin(a)*125;
        if(G.World.isFree(x,y,15,true)&&points.every(p=>Math.hypot(p[0]-x,p[1]-y)>60)) {
          points.push([x,y]);G.EnemyMgr.add(new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1}));
        }
      }G.EnemyMgr.rebuildGrid();
    }''')
    page.wait_for_timeout(1300)
    page.screenshot(path=str(ROOT/'.omx/naruto-shadow-clone-combat.png'),animations='disabled')
    page.evaluate("G.Game.player.level=6;G.Game.player.addMove('naruto-rasenshuriken')")
    page.wait_for_timeout(100)
    page.screenshot(path=str(ROOT/'.omx/naruto-eight-rasenshuriken.png'),animations='disabled')
    page.evaluate('G.Game.quit();G.Flow.goMenu()');assert page.evaluate('G.NarutoClones.actors.length')==0
    page.evaluate('G.Naruto.choose(30001);G.Flow.play()')
    page.wait_for_function('G.NarutoClones.actors.length===8')
    page.evaluate('''() => {
      window.originalQuantityOffer=G.LevelUp.offer;
      G.LevelUp.offer=(player,n=3)=>{
        const cards=window.originalQuantityOffer(player,20),quantity=cards.find(c=>c.key==='up:naruto-shadow-clones');
        return [quantity,...cards.filter(c=>c!==quantity)].filter(Boolean).slice(0,n);
      };G.Game.debugLevelUp();
    }''')
    page.locator('#scr-levelup').wait_for(state='visible')
    assert '16' in page.locator('#cards .card').first.inner_text()
    page.screenshot(path=str(ROOT/'.omx/naruto-quantity-card.png'),animations='disabled')
    page.locator('#cards .card').first.click()
    page.wait_for_function('G.NarutoClones.actors.length===16')
    page.evaluate('G.LevelUp.offer=window.originalQuantityOffer;G.Game.quit();G.Flow.goMenu()')
    mobile=browser.new_context(locale='zh-TW',viewport={'width':844,'height':390},is_mobile=True,has_touch=True,service_workers='block')
    if os.environ.get('PAGES_LIVE')!='1':mobile.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
    phone=mobile.new_page();phone.on('pageerror',lambda e:errors.append(str(e)))
    phone.goto(URL);phone.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if phone.locator('#tap-start').is_visible():phone.locator('#tap-start').click()
    phone.evaluate('G.Naruto.choose(30001);G.Flow.play()');phone.wait_for_function('G.NarutoClones.actors.length===8');phone.wait_for_timeout(650)
    phone.screenshot(path=str(ROOT/'.omx/naruto-shadow-clone-mobile.png'),animations='disabled')
    assert not errors,errors
    assert not missing,missing
    print(json.dumps(report,ensure_ascii=True));browser.close()
