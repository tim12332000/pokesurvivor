"""Rasengan phase, collision, protection and authored-art VFX regression."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright
import json
import mimetypes
import os

ROOT=Path(__file__).resolve().parent.parent
URL='https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&layout=wide&v=naruto-rasengan'
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
    page.goto(URL);page.wait_for_function("window.PS_REDRAWN_READY && G.SelfClones && document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    out=ROOT/'.omx/state/naruto-rasengan'
    out.mkdir(parents=True,exist_ok=True)
    page.evaluate("""async () => {G.Naruto.choose(30001);await G.Flow.play();if(G.Game.state==='playing')G.Game.togglePause();G.UI.hideAll();}""")
    result=page.evaluate("""() => {
      const assert=(v,m)=>{if(!v)throw Error(m)},p=G.Game.player,D=G.DigimonSkills,id='naruto-naruto';
      const reset=()=>{G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();G.FX.clear();p.flash=0;p.x=p.y=0;p.hp=p.maxHp;p.dead=false;p.invuln=0;p.cdMul=1;p.quantityBonus=0;p.critChance=0;p.percentHealthDamage=0;p.lifestealRate=0;p.moves=[];p.slots=[];p.bind={};p.active=0;p.addMove(id);p.aim=0;G.Camera.x=G.Camera.y=0;Object.assign(G.World,{isFree:()=>true,collide:()=>{},projectileBlock:()=>false,isWall:()=>false,isLiquid:()=>false});return p.moves[0]};
      const enemy=(x,y,boss=false)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:5,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];e.boss=boss;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e};
      const step=t=>{for(let a=0;a<t-1e-9;){const d=Math.min(.01,t-a);G.Combat.updateFields(d);a+=d}};
      let m=reset();
      assert(m.charge===.6,'extended charge');assert(m.cd===5&&G.Moves.instance(id,3).cd===4.5,'Rasengan cooldown progression');
      const main=enemy(70,0),sides=[enemy(40,60),enemy(60,-50),enemy(-40,55)],outside=enemy(0,165),boss=enemy(-60,10,true),behind=enemy(-35,0);
      const before=main.hp,sideHP=sides.map(e=>e.hp),hp=p.hp;
      assert(m.range===80&&m.cloneDashRange===125,'contact and clone ranges');
      assert(D.cast(p,m),'cast failed');step(.4);assert(p.x===0&&p.y===0,'charge forced movement');
      step(.25);assert(D.rasenganFor(p).phase==='strike'&&p.x===0&&p.y===0,'body still auto dashes');
      p.hurt(10);assert(p.hp===hp,'strike protection missing');step(.14);
      assert(D.rasenganFor(p).phase==='impact','impact missing');assert(main.hp<before,'no contact damage');const damage=before-main.hp;
      assert(sides.every((e,i)=>e.hp===sideHP[i])&&behind.hp===100000,'contact hit side or rear enemies');
      assert(sides.every(e=>e.x*e.kx+e.y*e.ky>0),'nearby targets not pushed');assert(outside.kx===0&&outside.ky===0,'outside target pushed');
      assert(boss.kx===0&&boss.ky===0,'boss launched');
      const endX=p.x;p.hurt(10);assert(p.hp===hp&&p.invuln>=.49,'arrival protection missing');step(.4);
      assert(!D.rasenganFor(p)&&main.hp===before-damage,'repeated contact damage');
      for(let i=0;i<60;i++)p.update(.01);p.hurt(10);assert(p.hp<hp,'protection never expired');
      // Real Player.update must keep input available during both charge and strike.
      m=reset();D.cast(p,m);const input=G.Input.axis;
      try{
        G.Input.axis=()=>[1,0];p.update(.05);const x=p.x;assert(x>0,'charge still locks input');step(.64);assert(p.x===x&&p.y===0,'skill displaced manual movement');
        G.Input.axis=()=>[0,1];p.update(.05);const y=p.y;assert(y>0,'strike still locks input');step(.5);assert(p.x===x&&p.y===y,'recovery snapped player back');
      }finally{G.Input.axis=input}
      m=reset();const blocked=enemy(70,0);G.World.isFree=x=>x<25;D.cast(p,m);step(.8);assert(blocked.hp===100000&&blocked.kx===0&&p.x===0,'contact or shock crossed wall');
      // Independent permanent card clones retain their former dash distance.
      m=reset();const card=G.LevelUp.STATS.find(c=>c.id==='selfClone').apply(p);card.x=card.y=0;card.aim=0;
      const cm=card.moves.find(move=>move.id===id);assert(D.cast(card,cm),'card clone cast rejected');step(.68);assert(card.x>0&&p.x===0,'card clone no longer dashes, or moved player');step(.4);assert(Math.abs(card.x-125)<1e-6,'clone dash distance changed');
      m=reset();const victim=enemy(80,0);G.NarutoClones.cast(p,G.Moves.instance('naruto-shadow-clones'));
      const shadow=G.NarutoClones.actors[0];for(const other of G.NarutoClones.actors)if(other!==shadow)other.dead=true;
      shadow.x=-120;shadow.y=0;shadow.cooldowns.set(id,0);step(.2);assert(shadow.x>-120&&p.x===0,'shadow no longer approaches independently');step(.6);assert(victim.hp<100000&&p.x===0,'shadow contact missing or moved player');
      m=reset();D.cast(p,m);step(.06);p.addMove('naruto-kunai');step(.4);assert(D.rasenganFor(p)&&p.x===0,'slot switch cancelled automatic charge');
      p.moves=p.moves.filter(move=>move.id!==id);step(.01);assert(!D.rasenganFor(p),'unlearning did not cancel automatic charge');
      m=reset();D.cast(p,m);step(.62);const deathX=p.x;p.dead=true;step(.5);assert(!D.rasenganFor(p)&&p.x===deathX,'death retained dash');
      m=reset();D.cast(p,m);G.Combat.clearFields();step(.5);assert(!D.rasenganFor(p)&&p.x===0,'clear retained dash');
      m=reset();p.target=enemy(80,0);p.moves[0].t=0;G.Combat.tick(.01,p,0);assert(D.rasenganFor(p)&&m.t>1,'native automatic cast failed');step(.1);const state=D.rasenganFor(p);assert(state.phaseAge<.11&&p.x===0,'charge moved prematurely');
      m=reset();enemy(150,0);p.addMove('naruto-nine-tails-cloak');D.cast(p,p.moves.find(move=>move.id==='naruto-nine-tails-cloak'));assert(G.KyuubiForm.active(p),'one-tail form missing');D.cast(p,m);step(.35);
      assert(G.KyuubiForm.poseFor(p.anim).animation==='rasenganCharge','one-tail charge pose missing');step(.3);
      assert(D.rasenganFor(p).phase==='strike'&&G.KyuubiForm.poseFor(p.anim).animation==='rasenganDash'&&p.x===0,'one-tail stationary strike missing');step(.14);
      assert(G.KyuubiForm.poseFor(p.anim).animation==='rasenganRecover','one-tail recovery missing');
      m=reset();D.cast(p,m);step(.35);
      const V=G.NarutoRasenganVFX,f=D.rasenganFor(p),pose=G.AnimationLab.stateFor(p.anim);
      assert(V&&pose.frame===1,'authored charge pose missing');
      const right=V.point(p.anim,pose,p.x,p.y),left=V.point(p.anim,{...pose,mirror:true},p.x,p.y);
      assert(Math.abs(right.x+left.x)<1e-6&&right.y===left.y&&right.r>0,'orb anchor mirror mismatch');
      const cv=document.createElement('canvas');cv.width=260;cv.height=200;const ctx=cv.getContext('2d');ctx.translate(100,100);
      const snapshot=()=>JSON.stringify({x:p.x,y:p.y,hp:p.hp,phase:f.phase,age:f.phaseAge,t:f.t,hits:f.hits.size,cd:m.t});
      const paint=()=>{ctx.clearRect(-100,-100,260,200);G.Combat.drawGroundFields(ctx);p.draw(ctx);G.Combat.drawAirFields(ctx);return cv.toDataURL()};
      const stateBefore=snapshot(),first=paint();assert(stateBefore===snapshot(),'render mutated combat');assert(first===paint(),'paused effects advanced');
      step(.05);assert(first!==paint(),'chakra flow not animated');
      let overlays=0;const draw=G.VFX.draw;G.VFX.draw=function(context,shape,...args){if(shape==='naruto-rasengan-flow')overlays++;return draw.call(this,context,shape,...args)};
      try{p.draw(ctx)}finally{G.VFX.draw=draw}assert(overlays===1,'missing or duplicated orb overlay');
      window.rasenganStep=step;window.rasenganReset=reset;window.rasenganEnemy=enemy;
      return {damage,endX,anchor:{right,left},checks:['charge','stationary contact','single front hit','manual movement during charge and strike','no recovery snapback','independent card-clone dash','shadow approach and contact','three nearby enemies pushed','outside unaffected','boss resistance','strike immunity','arrival protection','protection expires','wall-blocked contact','shock line of sight','automatic cast survives slot switch','unlearning cancels','death','clear','one-tail phases without player movement','authored orb anchor','mirrored anchor','render purity','paused effects frozen','chakra flow animated','one open flow overlay']};
    }""")
    page.evaluate("""()=>{const m=rasenganReset();G.Game.player.target=rasenganEnemy(70,0);G.DigimonSkills.cast(G.Game.player,m);G.Game.debugSpeed(1);if(G.Game.state!=='playing')G.Game.togglePause()}""")
    start_x=page.evaluate('G.Game.player.x')
    page.keyboard.down('d');page.wait_for_timeout(140);page.keyboard.up('d')
    movement=page.evaluate("""()=>{const p=G.Game.player,f=G.DigimonSkills.rasenganFor(p);if(G.Game.state==='playing')G.Game.togglePause();G.UI.hideAll();return {x:p.x,phase:f?.phase}}""")
    assert movement['x']>start_x, 'Real keyboard movement still locked during charge'
    assert movement['phase']=='charge', movement
    result['keyboardDuringCharge']=movement
    page.evaluate("""()=>{const m=rasenganReset();rasenganEnemy(70,0);G.EnemyMgr.rebuildGrid();G.DigimonSkills.cast(G.Game.player,m);document.querySelector('#tap-start').style.display='none';document.querySelectorAll('.toast,#ach-pop').forEach(e=>e.style.display='none')}""")
    for phase,dt in [('charge',0),('charge-ready',.45),('strike',.2),('impact',.16)]:
        if dt:page.evaluate('t=>rasenganStep(t)',dt)
        page.wait_for_timeout(100)
        page.screenshot(path=str(out/(phase+'.png')))
    page.set_viewport_size({'width':390,'height':844})
    page.evaluate("""() => {G.Combat.clearFields();G.FX.clear();G.EnemyMgr.clear();const p=G.Game.player;p.x=p.y=0;p.flash=p.invuln=0;p.aim=0;G.DigimonSkills.cast(p,p.moves[0]);rasenganStep(.68);}""")
    page.wait_for_timeout(120)
    page.screenshot(path=str(out/'mobile-strike.png'))
    assert not errors,errors
    (out/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result));browser.close()
