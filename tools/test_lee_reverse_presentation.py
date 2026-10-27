"""Reverse Lotus presentation preserves native damage, timing, AOE and cleanup."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/lee-reverse-preview'
URL = 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&hero=lee&layout=wide'

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),L=G.NarutoLee,results=[];
 A.assert(typeof L.presentationFor==='function','missing reverse presentation');
 p.level=12;p.addMove('naruto-reverse-lotus');
 for(const [level,quantity,boss] of [[1,0,false],[5,2,false],[1,0,true]]){
   A.leeArena();p.quantityPicks=quantity;p.quantityBonus=quantity;
   if(level===5)p.addMove('naruto-gates');
   const m=A.select('naruto-reverse-lotus');Object.assign(m,G.Moves.instance(m.id,level));
   const e=A.spawn(35,0,boss),side=[0,Math.PI/2,Math.PI,Math.PI*1.5].map(a=>A.spawn(35+Math.cos(a)*m.radius*.65,Math.sin(a)*m.radius*.65)),outside=A.spawn(35+m.radius+70,0);
   const unbound=A.spawn(35,m.radius*.85);unbound.elite=true;
   const hits=[],splash=new Map(side.map(e=>[e,0])),sideDamage=new Map(side.map(e=>[e,[]]));
   for(const enemy of [e,...side,outside,unbound]){const hurt=enemy.hurt;enemy.hurt=function(...args){
     if(this===e)hits.push(args[0]);else splash.set(this,(splash.get(this)||0)+1);
     sideDamage.get(this)?.push(args[0]);
     return hurt.apply(this,args)};}
   p.target=e;p.aim=0;A.actualCast(m.id);const f=L.active;
   const seen=new Set(),offsets=new Set(),heights=[],angles=new Set(),victimXs=[];let draws=0,maxSeparation=0;
   for(let n=0;n<1500&&L.active;n++){
     G.Camera.follow(p.x,p.y,.005);
     A.resume();try{G.Combat.updateFields(.005);p.anim.update(.005);G.FX.update(.005)}finally{A.pause()}
     if(!L.active)break;seen.add(f.phase);
     if(boss)A.assert(!f.cameraLock,'ground boss incorrectly locked airborne camera');
     if(!boss&&['lift','combo','descent','slam','recovery'].includes(f.phase)){
       A.assert(f.cameraLock,'airborne action did not lock the camera');
       A.assert(G.Camera.x===f.cameraLock.x&&G.Camera.y===f.cameraLock.y,'airborne action moved the camera');
       G.Camera.kick(.3);G.Camera.follow(p.x+100,p.y-100,.005);
       A.assert(G.Camera.x===f.cameraLock.x&&G.Camera.y===f.cameraLock.y&&G.Camera.shake===0&&G.Camera._sx===0&&G.Camera._sy===0,'airborne follow or shake escaped camera lock');
     }
     A.assert(f.strikes.length<=6,'unbounded strike trails');
     if(f.phase==='combo'){
       const pose=G.AnimationLab.stateFor(p.anim);offsets.add(Math.round(pose.offsetX||0));
       heights.push(pose.offsetY||0);angles.add(Math.round((pose.rotation||0)*10));
       victimXs.push(L.victimPresentationFor(e)?.offsetX||0);
       const victim=L.victimPresentationFor(e);
       maxSeparation=Math.max(maxSeparation,Math.abs(p.x+(pose.offsetX||0)-e.x-(victim?.offsetX||0)));
       if(!boss){
         const actorX=p.x+pose.offsetX,targetX=e.x+victim.offsetX;
         A.assert(Math.min(actorX,targetX)-64>=G.Camera.left()-1&&Math.max(actorX,targetX)+64<=G.Camera.left()+G.Camera.w+1,'wide chase clipped horizontally');
         A.assert(p.y-f.visualLift+pose.offsetY-80>=G.Camera.top()-1,'high chase clipped above camera');
       }
       const age=f.age;G.Combat.updateFields(.1);A.assert(f.age===age,'pause advanced presentation');
     }
     const cv=document.createElement('canvas');cv.width=480;cv.height=440;
     const ctx=cv.getContext('2d');ctx.translate(200,330);
     G.Combat.drawGroundFields(ctx);e.draw(ctx);p.draw(ctx);G.Combat.drawAirFields(ctx);draws++;
   }
   const count=Math.floor((5+2*(level-1))*1.25**quantity),base=m.dmg*f.attack*G.Types.mult(m.type,e.types)*G.Weather.mult(m.type);
   const expected=[.1,...Array.from({length:count},(_,n)=>.12*1.1**(n+1)),.3];
   A.assert(!L.active&&f.age<=3.3+1e-8,'presentation exceeded full action deadline');
   A.assert(hits.length===expected.length,'changed primary hit count');
   hits.forEach((hit,i)=>A.assert(Math.abs(hit-base*expected[i])<1e-7,'changed primary damage '+i));
   A.assert(side.every(e=>splash.get(e)===(boss?1:expected.length))&&!splash.get(outside),'group hit count or outside coverage changed');
   if(!boss)for(const enemy of side)sideDamage.get(enemy).forEach((hit,i)=>A.assert(Math.abs(hit-base*expected[i])<1e-7,'group member damage differs from full combo'));
   A.assert(splash.get(unbound)===1,'unbound enemy received the group combo');
   A.assert(!L.liftFor(e)&&!L.isInvulnerable(p),'completed action retained lift/immunity');
   A.assert(boss||offsets.size>=2,'air pursuit never alternated sides');
   if(!boss){
     A.assert(Math.max(...heights)-Math.min(...heights)>70*(f.verticalScale||1),'pursuit stayed at one elevation');
     A.assert(angles.size>=4,'kick direction did not follow aerial pursuit');
     A.assert(Math.max(...victimXs)-Math.min(...victimXs)>350*(f.horizontalScale||1),'victim stayed in a small local area');
     const positions=[...offsets];
     A.assert(Math.max(...positions)-Math.min(...positions)>400*(f.horizontalScale||1),'Lee did not cross the arena');
     A.assert(maxSeparation>100*(f.horizontalScale||1),'pursuer never separated from the knocked-back target');
   }
   A.assert(!L.presentationFor(p),'completed action retained presentation offset');
   A.assert(!L.victimPresentationFor(e),'completed action retained victim offset');
   if(!boss)A.assert(G.Camera.x===p.x&&G.Camera.y===p.y,'completed action retained cinematic camera');
   results.push({level,quantity,boss,age:f.age,hits:hits.length,phases:[...seen],horizontalPositions:offsets.size,
     verticalTravel:Math.max(...heights)-Math.min(...heights),directions:angles.size,maxSeparation,draws});
 }
 A.leeArena();p.quantityPicks=0;const m=A.select('naruto-reverse-lotus'),e=A.spawn(35,0);p.target=e;A.actualCast(m.id);A.advance(.9);
 L.clear(p);A.assert(!L.active&&!L.liftFor(e)&&!L.isInvulnerable(p),'cancel retained presentation');
 A.assert(L.bindLimitOf(G.Moves.instance('naruto-reverse-lotus'),p)===10,'reverse base group not ten');
 A.assert(L.bindLimitOf(G.Moves.instance('naruto-lotus'),p)===3,'normal Lotus group changed');
 p.quantityPicks=20;A.assert(L.bindLimitOf(G.Moves.instance('naruto-reverse-lotus'),p)===24,'group cap changed');
 p.quantityPicks=p.quantityBonus=0;A.leeArena();const weak=[A.spawn(35,0),A.spawn(65,20),A.spawn(65,-20),A.spawn(25,65),A.spawn(25,-65)];
 weak.forEach(e=>{e.hp=1;e.xp=7});p.target=weak[0];A.select('naruto-reverse-lotus');A.actualCast('naruto-reverse-lotus');const weakFrame=L.active,before=p.kills;
 let airborne=false;for(let n=0;n<1500&&L.active;n++){
   A.advance(.005);if(L.active?.phase==='combo'){
     airborne=true;A.assert(weak.every(e=>!e.dead&&L.pendingDefeat(e)),'weak group died before landing');
     A.assert(weak.every(e=>L.liftFor(e)>0),'group did not rise together');
     A.assert(p.kills===before,'group rewarded before landing');
   }
 }
 A.assert(airborne&&weakFrame.boundTargets.length===0&&weak.every(e=>e.dead),'group did not finish landing');
 G.EnemyMgr.update(.001,[p]);
 A.assert(p.kills-before===5,'group kill rewards were not exactly once');
 G.EnemyMgr.update(.001,[p]);A.assert(p.kills-before===5,'group death rewards duplicated');
 weak.forEach(e=>A.assert(!L.pendingDefeat(e)&&!L.liftFor(e),'group death retained lift'));
 A.leeArena();p.target=A.spawn(35,0);const cancelled=A.spawn(50,40);cancelled.hp=1;A.select('naruto-reverse-lotus');A.actualCast('naruto-reverse-lotus');A.advance(1.2);L.clear(p);
 A.assert(!L.pendingDefeat(cancelled)&&!L.bound(cancelled)&&!L.liftFor(cancelled),'cancel left a group victim held');
 A.leeArena();p.quantityPicks=5;p.quantityBonus=5;const capMain=A.spawn(35,0),capEnemies=Array.from({length:27},(_,i)=>A.spawn(60+Math.cos(i*Math.PI*2/27)*70,Math.sin(i*Math.PI*2/27)*70));
 p.target=capMain;const capMove=A.select('naruto-reverse-lotus');Object.assign(capMove,G.Moves.instance(capMove.id,5));A.actualCast('naruto-reverse-lotus');
 A.assert(L.active.boundTargets.length===24,'actual crowded cast did not reach the twenty-four-member cap: '+L.active.boundTargets.length);
 L.clear(p);A.assert([capMain,...capEnemies].every(e=>!L.bound(e)&&!L.liftFor(e)),'capped group retained claims after cancel');
 const camera={x:G.Camera.x,y:G.Camera.y};G.Camera.follow(camera.x+80,camera.y+80,.1);
 A.assert(G.Camera.x>camera.x&&G.Camera.y>camera.y,'normal camera follow did not resume after cancel');
 return results;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, mobile in [('desktop', False), ('mobile', True)]:
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1200, 'height': 900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(URL)
            page.wait_for_function("window.G?.NarutoLee && document.querySelector('#boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30006 && G.Game.state==="playing"')
            page.evaluate('()=>G.Sprites.preload([19])')
            page.evaluate(HARNESS)
            page.evaluate(SETUP)
            report['viewports'][label] = page.evaluate(CHECK)
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    (OUT / 'regression.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, **report}))


if __name__ == '__main__':
    main()
