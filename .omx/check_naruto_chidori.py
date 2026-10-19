"""Verify Chidori chaining against actual browser Player/Enemy combat objects."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright
import mimetypes, json
ROOT=Path(__file__).resolve().parent.parent
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    c=b.new_context(viewport={'width':1280,'height':820},locale='zh-TW',service_workers='block')
    def proxy(route):
        f=ROOT/unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
        route.fulfill(status=200 if f.is_file() else 404,body=f.read_bytes() if f.is_file() else b'',content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
    c.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
    page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW')
    page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.evaluate('G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
    result=page.evaluate(r'''() => {
      const pl=G.Game.player,A=G.NarutoChidori,assert=(v,m)=>{if(!v)throw Error(m)},report={};
      const orig={isFree:G.World.isFree,isLiquid:G.World.isLiquid,collide:G.World.collide};
      const camera={x:G.Camera.x,y:G.Camera.y,w:G.Camera.w,h:G.Camera.h};
      Object.assign(G.Camera,{x:0,y:0,w:20000,h:20000}); // Isolate progression math from separately tested screen clipping.
      G.World.isFree=()=>true;G.World.isLiquid=()=>false;G.World.collide=()=>{};
      let hitEvents=[];
      function setup(n){hitEvents=[];G.Combat.clearFields();G.EnemyMgr.clear();G.FX.clear();pl.x=pl.y=0;pl.hp=pl.maxHp;pl.dead=false;pl.invuln=0;pl.critChance=0;pl.quantityBonus=0;pl.item=null;
        return Array.from({length:n},(_,i)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},100+i*100,0,{hp:1,spd:1,dmg:1});e.types=['normal'];const hurt=e.hurt;e.hurt=function(damage,...args){hitEvents.push({enemy:e,damage});return hurt.call(this,damage,...args);};G.EnemyMgr.add(e);return e;});}
      function cast(){const m=G.Moves.instance('naruto-sasuke');assert(G.DigimonSkills.cast(pl,m),'cast rejected');return m;}
      function step(t){for(let i=0;i<Math.ceil(t*240);i++)G.Combat.updateFields(1/240);}
      setup(2);cast();
      const art=G.Naruto.records.get(30002).pixel.chidori,sourceCrops=[];
      const review=document.createElement('canvas');review.id='chidori-source-review';review.width=960;review.height=240;
      const rc=review.getContext('2d');rc.fillStyle='#28384d';rc.fillRect(0,0,960,240);rc.fillStyle='#fff';rc.font='14px sans-serif';
      for(let i=0;i<3;i++){
        if(i)G.Combat.updateFields(.031);
        const pose=A.poseFor(pl.anim);assert(pose.rect.join()===art.chargeFrames[i].rect.join(),'wrong original charge frame '+i);
        const cv=document.createElement('canvas');cv.width=cv.height=160;
        const ctx=cv.getContext('2d'),originalDraw=ctx.drawImage;let crop,feet;
        ctx.drawImage=function(image,sx,sy,sw,sh,dx,dy,dw,dh){crop=[sx,sy,sw,sh];feet=dy+pose.anchor[1]*(64*pl.anim.scale/44);return originalDraw.apply(this,arguments)};
        pl.anim.draw(ctx,80,110);assert(crop.join()===pose.rect.join(),'renderer ignored source pose');assert(Math.abs(feet)<.51,'charge feet shift with lightning bounds');sourceCrops.push(crop);
        rc.drawImage(cv,i*160,0);rc.fillText('Charge '+(i+1),i*160+40,150);
      }
      const preview=new G.Sprites.Animator(30002);assert(A.poseFor(preview)===null,'charge pose leaked into another Sasuke preview');
      pl.aim=Math.PI;assert(A.poseFor(pl.anim).mirror,'left charge not mirrored');pl.anim.draw(rc,560,110);rc.fillText('Charge left',520,150);
      G.Combat.updateFields(.029);assert(A.active.phase==='dash','charge timing changed');
      pl.aim=0;assert(A.poseFor(pl.anim).rect.join()===art.dashFrame.rect.join(),'dash uses generic casting pose');pl.anim.draw(rc,720,110);rc.fillText('Dash right',680,150);
      pl.aim=Math.PI;assert(A.poseFor(pl.anim).mirror,'left dash not mirrored');pl.anim.draw(rc,880,110);rc.fillText('Dash left',840,150);
      review.style.cssText='position:fixed;left:0;top:0;z-index:30000';document.body.append(review);
      A.clear();assert(A.poseFor(pl.anim)===null,'source pose remains after clear');
      report.sourceAnimation={chargeFrames:sourceCrops,dash:art.dashFrame.rect,mirror:'left only',anchors:'fixed character feet',scope:'active owner only'};
      setup(20);assert(G.DigimonSkills.cast(pl,G.Moves.instance('naruto-sasuke',5)),'acceleration cast rejected');
      G.Combat.updateFields(.09);
      const measuredSpeeds=[],turnDelays=[];
      for(let leg=0;leg<16;leg++){
        assert(A.active?.phase==='dash','missing acceleration leg '+leg);
        const x=pl.x,y=pl.y;G.Combat.updateFields(.004);
        const speed=Math.hypot(pl.x-x,pl.y-y)/.004;
        assert(Math.abs(speed-Math.min(3000,1000+leg*150))<.001,'actual dash speed mismatch '+leg+': '+speed);
        measuredSpeeds.push(Math.round(speed));
        while(A.active?.phase==='dash')G.Combat.updateFields(1/240);
        assert(A.active?.phase==='retarget','acceleration chain ended early');
        const delay=A.active.wait;turnDelays.push(delay);
        assert(Math.abs(delay-Math.max(.012,.045*Math.pow(.85,leg+1)))<.000001,'turn delay mismatch');
        G.Combat.updateFields(delay);
      }
      assert(measuredSpeeds[0]<measuredSpeeds[1]&&measuredSpeeds[1]<measuredSpeeds[2]&&measuredSpeeds[15]===3000,'acceleration/cap missing');
      assert(turnDelays[0]>turnDelays[1]&&turnDelays.at(-1)===.012,'turn delay floor missing');
      setup(2);cast();assert(A.active.speed===1000&&A.active.retargetDelay===.045,'new cast retained acceleration');
      G.Combat.updateFields(.09);const resetX=pl.x;G.Combat.updateFields(.004);
      assert(Math.abs(pl.x-resetX-4)<.001,'new cast first leg failed speed reset');
      report.acceleration={measuredSpeeds,turnDelayStart:turnDelays[0],turnDelayFloor:turnDelays.at(-1),newCast:'speed 1000 and delay 0.045 reset; actual movement verified'};
      for(let n=1;n<=7;n++){const es=setup(n);const m=cast();const before=pl.dmgDealt;step(2);const hit=hitEvents.length;
        assert(hit===(n===1?1:5),'target count '+n+': '+hit);assert(hitEvents.every((h,i)=>!i||h.enemy!==hitEvents[i-1].enemy),'consecutive repeat');assert(!A.active,'chain remained');
        const expected=Array.from({length:n===1?1:5},(_,i)=>Math.pow(1.05,i)).reduce((a,b)=>a+b,0)*m.dmg*pl.atk*G.Types.mult(m.type,['normal'])*G.Weather.mult(m.type);
        assert(Math.abs(pl.dmgDealt-before-expected)<.01,'owner damage credit mismatch');
      }report.chain='1..7 targets: revisits allowed; no consecutive same enemy; capped at 5; owner/type damage accounting';
      const pair=setup(2);cast();step(2);
      assert(hitEvents.length===5&&hitEvents.every((h,i)=>h.enemy===pair[i%2]),'A/B revisits did not alternate');
      const overlap=setup(2);overlap[1].x=overlap[0].x;cast();step(2);
      assert(hitEvents.length===5&&hitEvents.every((h,i)=>h.enemy===overlap[i%2]),'overlapping enemies repeated consecutive target');
      const isolated=setup(2),secondHurt=isolated[1].hurt;
      isolated[1].hurt=function(...args){const result=secondHurt.apply(this,args);isolated[0].dead=true;return result;};
      cast();step(2);assert(hitEvents.length===2&&!A.active&&pl.x===0,'only last surviving target was hit twice consecutively');
      report.revisits='A/B/A/B/A; overlapping targets alternate; sole remaining last target ends and returns';
      const boosted=setup(47);pl.quantityBonus=20;const boostedMove=G.Moves.instance('naruto-sasuke',5);
      const baseDamage=boostedMove.dmg*pl.atk*G.Types.mult(boostedMove.type,['normal'])*G.Weather.mult(boostedMove.type),creditBefore=pl.dmgDealt;
      assert(G.DigimonSkills.cast(pl,boostedMove),'damage chain cast rejected');step(12);
      for(let i=0;i<45;i++)assert(Math.abs(hitEvents[i].damage-baseDamage*Math.pow(1.05,i))<.000001,'damage progression mismatch at hit '+(i+1));
      assert(hitEvents.length===45&&hitEvents.every((h,i)=>!i||h.enemy!==hitEvents[i-1].enemy)&&!A.active,'damage bonus changed pursuit count');
      const total=baseDamage*Array.from({length:45},(_,i)=>Math.pow(1.05,i)).reduce((a,b)=>a+b,0);
      assert(Math.abs(pl.dmgDealt-creditBefore-total)<.001,'increasing damage missing from owner credit');
      const resetDamage=setup(2);assert(G.DigimonSkills.cast(pl,G.Moves.instance('naruto-sasuke',5)),'damage reset cast rejected');step(2);
      assert(Math.abs(hitEvents[0].damage-baseDamage)<.000001,'new chain retained damage growth');
      report.damageGrowth={hits:45,firstMultiplier:1,lastMultiplier:Math.pow(1.05,44),cap:'none',newCast:'resets to base damage'};
      const limits=[];
      for(let lv=1;lv<=5;lv++){
        const es=setup(27),m=G.Moves.instance('naruto-sasuke',lv);
        assert(m.lvl===lv&&A.limitOf(m)===lv*5,'wrong level field or limit');
        assert(G.DigimonSkills.cast(pl,m),'level cast rejected');step(6);
        const hits=hitEvents.length;
        assert(hits===lv*5&&!A.active,'wrong count at level '+lv+': '+hits);limits.push(hits);
      }
      const snapshotEnemies=setup(27),snapshotMove=G.Moves.instance('naruto-sasuke');
      assert(G.DigimonSkills.cast(pl,snapshotMove),'snapshot cast rejected');
      while(snapshotMove.lvl<5)G.Moves.levelUp(snapshotMove);
      step(6);assert(hitEvents.length===5,'mid-cast upgrade changed chain limit');
      assert(G.DigimonSkills.cast(pl,snapshotMove),'upgraded next cast rejected');
      assert(A.active.limit===25,'next cast did not use upgraded limit');G.Combat.clearFields();
      const quantityLimits=[];
      for(let lv=1;lv<=5;lv++)for(const bonus of [1,20]){
        const es=setup(47),m=G.Moves.instance('naruto-sasuke',lv);
        for(let pick=0;pick<bonus;pick++)G.LevelUp.STATS.find(s=>s.id==='quantity').apply(pl);
        assert(A.limitOf(m)===lv*5+bonus,'quantity limit mismatch');
        assert(G.DigimonSkills.cast(pl,m),'quantity cast rejected');step(12);
        const hits=hitEvents.length;
        assert(hits===lv*5+bonus&&!A.active,'quantity counted twice or missing: '+lv+'/'+bonus+'/'+hits);
        quantityLimits.push({lv,bonus,hits});
      }
      report.levels={limits,quantityLimits,snapshot:'upgrade during cast applies next cast only'};
      setup(0);assert(!G.DigimonSkills.cast(pl,G.Moves.instance('naruto-sasuke')),'zero targets cast');
      const distant=setup(5);distant.forEach((e,i)=>{e.x=100+i*350;const hurt=e.hurt;e.hurt=function(...args){const out=hurt.apply(this,args);this.dead=true;return out;};});cast();step(3);
      assert(distant.every(e=>e.hp<e.maxHp)&&!A.active,'350-spaced targets broke follow-up chain');
      const outside=setup(2);outside[1].x=700;cast();step(1);
      assert(outside[0].hp<outside[0].maxHp&&outside[1].hp===outside[1].maxHp&&!A.active,'follow-up exceeded 510 range');
      const firstOutside=setup(1);firstOutside[0].x=171;
      assert(!G.DigimonSkills.cast(pl,G.Moves.instance('naruto-sasuke'))&&!A.active,'first acquisition exceeded 170');
      const upgraded=setup(2);upgraded[1].x=600;
      assert(G.DigimonSkills.cast(pl,G.Moves.instance('naruto-sasuke',4)),'upgraded cast rejected');step(2);
      assert(upgraded.every(e=>e.hp<e.maxHp),'upgraded follow-up range did not scale');
      report.followup='five targets spaced 350 reached; beyond 510 stops; first cast remains 170; upgrades scale follow-up range';
      const es=setup(47);pl.quantityBonus=1;const m=cast();m.dmg=999;pl.quantityBonus=20;step(12);assert(hitEvents.length===6,'mid-cast quantity changed limit');assert(hitEvents[0].damage<900,'snapshot mutated');
      assert(G.DigimonSkills.cast(pl,G.Moves.instance('naruto-sasuke'))&&A.active.limit===25,'next cast missed new quantity');G.Combat.clearFields();report.snapshot='quantity captured once; mid-cast passive applies next cast; learned damage immutable';
      setup(2);cast();let hp=pl.hp;pl.hurt(1,null,true);assert(pl.hp<hp,'charge invulnerable');pl.invuln=0;step(.095);assert(A.active?.phase==='dash','dash not begun');hp=pl.hp;pl.hurt(10000,null,true);assert(pl.hp===hp,'dash pure damage got through');pl.invuln=0;pl.hurt(10,'fire');assert(pl.hp===hp,'dash typed damage got through');
      let oldx=pl.x,oldy=pl.y;const axis=G.Input.axis;G.Input.axis=()=>[1,1];pl.update(.01);G.Input.axis=axis;assert(pl.x===oldx&&pl.y===oldy,'normal movement fought dash');
      while(A.active?.phase==='dash')step(1/240);assert(A.active?.phase==='retarget','missing retarget window');pl.invuln=0;hp=pl.hp;pl.hurt(1,null,true);assert(pl.hp<hp,'retarget invulnerable');pl.invuln=0;step(1);assert(!A.active,'end pending');assert(pl.invuln===.3,'missing end protection');hp=pl.hp;pl.hurt(1,null,true);assert(pl.hp===hp,'end protection did not block');pl.update(.31);pl.hurt(1,null,true);assert(pl.hp<hp,'end protection did not expire');report.immunity='actual dash invulnerable; charge/retarget vulnerable; end protected 0.3 seconds then expires; joystick suppressed';
      setup(2);pl.invuln=3;cast();step(.095);G.Combat.clearFields();assert(pl.invuln===3,'overwrote independent invulnerability');
      setup(1);pl.invuln=3;cast();step(1);assert(pl.invuln===3,'end shortened existing protection');
      setup(1);cast();G.Combat.clearFields();assert(pl.invuln===0,'charge clear gave end protection');
      setup(1);cast();G.EnemyMgr.all()[0].dead=true;step(.2);assert(pl.invuln===0,'charge cancellation gave end protection');
      const wallTargets=setup(2);cast();G.World.isFree=x=>x<40||x>70;
      G.World.collide=p=>{if(p.x>=40&&p.x<=70)p.x=20;};
      let beyondWall=false;
      for(let i=0;i<240&&A.active;i++){pl.update(1/240);G.Combat.updateFields(1/240);if(pl.x>70)beyondWall=true;}
      assert(wallTargets.every(e=>e.hp<e.maxHp)&&beyondWall&&pl.x===0&&!A.active&&pl.invuln===.3,'wall interrupted pursuit or return');
      pl.x=50;pl.update(.01);assert(pl.x===20,'normal collision remained disabled');G.World.collide=()=>{};
      const propTargets=setup(2);cast();G.World.isFree=()=>false;step(1);
      assert(propTargets.every(e=>e.hp<e.maxHp)&&!A.active,'solid props interrupted pursuit');G.World.isFree=()=>true;report.walls='dash passes walls and solid props; normal collision resumes afterward';
      setup(2);cast();step(.095);pl.dead=true;step(.01);assert(!A.active&&pl.invuln===0,'death residue or added protection');
      setup(2);cast();step(.095);const world=G.World;G.World={...world};step(.01);assert(!A.active&&pl.invuln===0,'world residue or added protection');G.World=world;
      setup(2);cast();step(.095);G.Combat.clearFields(pl);assert(!A.active&&pl.invuln===0,'clear residue or added protection');
      setup(1);cast();step(1);pl.update(.1);const remaining=pl.invuln;step(1);assert(pl.invuln===remaining,'end protection refreshed repeatedly');
      setup(1);cast();G.EnemyMgr.all()[0].dead=true;step(.2);assert(!A.active,'dead target remained');
      assert(G.Moves.BY_ID['naruto-kakashi'].digiMode==='dash','Raikiri changed');assert(G.Moves.instance('naruto-sasuke',5).dmg>44,'upgrades lost');
      report.lifecycle='death/world change/dead target/owner clear clean; independent invulnerability preserved; Raikiri unchanged';
      const oldGroup=pl.activeGroup,oldMoves=pl.moves,oldCd=pl.cdMul;
      try{
        const learned=G.Moves.instance('naruto-sasuke',5);pl.moves=[learned];pl.activeGroup=()=>[learned];pl.cdMul=.01;
        setup(1);learned.t=0;G.Combat.tick(.001,pl,0);
        assert(A.active&&learned.t===.5,'cooldown reductions bypassed minimum');
        learned.t=0;step(1);assert(!A.active&&learned.t===.5,'chain end missing minimum cooldown');
        const oldSlots=pl.slots,oldActive=pl.active;
        pl.slots=[[],[learned]];pl.active=0;pl.setActive(1);
        assert(learned.t===.5,'switching skills bypassed minimum cooldown');pl.slots=oldSlots;pl.active=oldActive;
        setup(1);G.Combat.tick(.499,pl,1);assert(!A.active,'recast before half-second recovery');
        G.Combat.tick(.002,pl,1.501);assert(A.active&&learned.t===.5,'recast failed after minimum cooldown');
        learned.t=1.2;step(1);assert(learned.t===1.2,'minimum shortened a longer cooldown');
        report.cooldown='Lv5 with 99% reduction: 0.5-second minimum; end resets minimum; longer cooldown preserved';
      }finally{G.Combat.clearFields();pl.activeGroup=oldGroup;pl.moves=oldMoves;pl.cdMul=oldCd;}
      Object.assign(G.World,orig);Object.assign(G.Camera,camera);return report;
    }''')
    page.locator('#chidori-source-review').screenshot(path=str(ROOT/'.omx/chidori-original-frames.png'))
    page.evaluate("document.getElementById('chidori-source-review').remove()")
    capture=r'''() => {
      const pl=G.Game.player;G.Combat.clearFields();G.EnemyMgr.clear();G.FX.clear();
      pl.x=pl.y=0;pl.hp=pl.maxHp;pl.dead=false;pl.flash=0;pl.invuln=0;pl.aim=0;
      const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},130,0,{hp:1,spd:1,dmg:1});
      G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();pl.target=e;
      G.DigimonSkills.cast(pl,G.Moves.instance('naruto-sasuke'));G.Combat.updateFields(.095);
      G.World.isFree=()=>true;G.Combat.updateFields(.025);
      G.Camera.x=pl.x;G.Camera.y=pl.y;document.getElementById('scr-pause').style.visibility='hidden';
    }'''
    page.evaluate(capture);page.wait_for_timeout(60)
    page.screenshot(path=str(ROOT/'.omx/chidori-desktop.png'),animations='disabled')
    mobile=b.new_context(viewport={'width':390,'height':844},locale='zh-TW',is_mobile=True,has_touch=True,service_workers='block')
    mobile.route('https://tim12332000.github.io/pokesurvivor/**',proxy)
    phone=mobile.new_page();phone.on('pageerror',lambda e:errors.append(str(e)))
    phone.goto('https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW')
    phone.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if phone.locator('#tap-start').is_visible():phone.locator('#tap-start').click()
    phone.evaluate('G.Naruto.choose(30002);G.Flow.play();G.Game.togglePause()')
    phone.evaluate(capture);phone.wait_for_timeout(60)
    phone.screenshot(path=str(ROOT/'.omx/chidori-portrait.png'),animations='disabled')
    assert not errors, errors
    print(json.dumps({'ok':True,'checks':result},ensure_ascii=False));b.close()
