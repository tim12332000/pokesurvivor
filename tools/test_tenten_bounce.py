"""Native Tenten ricochet: passive learning, real flight, counts and cleanup."""
import json
import os
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_tenten import CHROME, HARNESS, SETUP, PROGRESSION

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/tenten-bounce'
URL = os.environ.get('TENTEN_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW')

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,id='naruto-tenten-bounce',out={};
 p.level=1;A.assert(!G.LevelUp.offer(p,100).some(c=>c.key==='new:'+id),'premature bounce passive');
 p.level=2;const slots=p.slots.length,max=p.maxMoves;p.maxMoves=slots;
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);
 A.assert(card&&card.apply(p)!==false,'slotless passive learning failed');p.maxMoves=max;p.level=12;
 const skill=p.moves.find(m=>m.id===id);A.assert(skill.passive&&p.slots.length===slots&&!p.slots.flat().includes(skill),'passive consumed active slot');
 A.assert(!T.canCast(p,skill),'passive can be cast');
 out.learning={level:2,slotless:true,icon:G.Icons.url('move:'+id).slice(0,22)};
 for(const dex of [30001,30002,30006,30007,20001]){
   const mon=G.DEX.find(m=>m.dex===dex)||{dex,gen:10,types:['normal']};A.assert(!G.Moves.poolFor(mon).includes(id),'bounce leaked to '+dex);
 }
 const original=p.moves;p.moves=original.filter(m=>m.id!=='naruto-tenten-mastery');
 const base=p.moves.find(m=>m.id==='naruto-tenten'),baseCount=base.count;base.count=1;
 function arena(n){A.reset();const es=[];for(let i=0;i<n;i++)es.push(A.spawn(100+i*90,i%2?65:0));p.target=es[0];return es;}
 function single(move){const cast=T.cast(p,{...move,count:1,quantityBonusAtCast:G.Quantity.bonus(p),quantityMultiplierAtCast:1});if(move.id.endsWith('twin'))A.advance(.12);return cast;}
 try {
   out.tiers=[];
   for(let tier=1;tier<=5;tier++){
     if(tier>1)G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id).apply(p);
     const es=arena(tier+2);A.assert(T.bounceCount(p)===tier,'tier count not skill level');
     A.castNative(base.id);const w=T.weapons[0];A.finish(3);
     A.assert(es.filter(e=>e.hp<100000).length===tier+1&&es[tier+1].hp===100000,'wrong extra bounce count at tier '+tier);
     A.assert(w.bounced===tier&&w.dead,'ricochet did not end');out.tiers.push({tier,bounces:w.bounced,hits:tier+1});
   }
   const es=arena(47);p.quantityPicks=p.quantityBonus=40;
   A.assert(T.bounceCount(p)===45,'quantity must add linearly');single(base);const many=T.weapons[0];A.finish(15);
   A.assert(many.bounced===45&&es.filter(e=>e.hp<100000).length===46&&es[46].hp===100000,'ricochet capped or quantity reapplied');
   out.uncapped={quantity:40,bounces:many.bounced,hits:46};
   arena(1);p.quantityPicks=p.quantityBonus=1000;A.assert(T.bounceCount(p)===1005,'hidden count ceiling');single(base);const longChain=T.weapons[0];A.finish(110);
   A.assert(longChain.bounced===1005&&!T.weapons.length,'repeat hits exceeded or lost finite bounce budget');
   out.repeatTiers=[];
   for(let tier=1;tier<=5;tier++){
     skill.lvl=tier;arena(1);const victim=p.target;single(base);const shot=T.weapons[0];A.finish(3);
     A.near(100000-victim.hp,Math.max(1,Math.round(base.dmg*p.atk*G.Types.mult(base.type,victim.types)*G.Weather.mult(base.type)))*(tier+1),'single victim repeat damage');
     A.assert(shot.bounced===tier&&shot.dead,'single victim did not exhaust bounce budget');
     out.repeatTiers.push({tier,hits:tier+1});
   }
   skill.lvl=5;
   out.tools={};
   for(const moveId of ['naruto-tenten-fuma','naruto-tenten-tags','naruto-tenten-twin']){
     const targets=arena(7);single(p.moves.find(m=>m.id===moveId));const w=T.weapons[0];
     for(let i=0;i<800&&!w.dead;i++)A.advance();
     A.assert(w.bounced===5,'tool did not ricochet '+moveId+' '+w.bounced);
     if(moveId.endsWith('tags'))A.assert(targets.slice(0,5).every(e=>e.hp===100000)&&targets[5].hp<100000&&targets[6].hp===100000,'tag exploded before final landing');
     if(moveId.endsWith('fuma'))A.assert(T.stateFor(p).chargeRemaining>0,'ricochet blade failed to return/recover');
     out.tools[moveId]={bounces:w.bounced,damage:targets.map(e=>100000-e.hp)};
   }
   A.reset();
   for(let x=64;x<=320;x+=32)for(let y=-192;y<=128;y+=32)A.spawn(x,y);
   p.target=A.spawn(180,0);
   const arsenal=p.moves.find(m=>m.id==='naruto-tenten-twin'),arsenalShots=new Set();
   T.cast(p,{...arsenal,count:8,quantityBonusAtCast:0});
   for(let i=0;i<500;i++){A.advance();for(const w of T.weapons)if(w.mode==='tenten-twin')arsenalShots.add(w);}
   const ricochetKinds=[...new Set([...arsenalShots].filter(w=>w.bounced>0).map(w=>w.appearance.kind))].sort();
   A.assert(['shuriken','kunai','axe','senbon','spear','sickle','chakram','sword'].every(kind=>ricochetKinds.includes(kind)),'some twin tools do not ricochet '+ricochetKinds);
   out.allTwinTools=ricochetKinds;
   // Repeated hits retain the existing protected-target exclusions.
   arena(1);const first=p.target,protectedTargets=[A.spawn(160,40,true),A.spawn(170,-40),A.spawn(180,60),A.spawn(190,-60)];
   protectedTargets[1].elite=true;protectedTargets[2].legend=true;protectedTargets[3].judge=true;
   single(base);A.finish(1.5);A.assert(first.hp<100000&&protectedTargets.every(e=>e.hp===100000),'chain targeted protected enemies');
   // Twin tools can revisit a boss after first reaching it from a mob.
   arena(1);const mob=p.target,boss=A.spawn(180,60,true),twinMove=p.moves.find(m=>m.id==='naruto-tenten-twin');
   single(twinMove);const bossShot=T.weapons[0];A.finish(3);
   A.assert(mob.hp<100000&&boss.hp<100000&&bossShot.bounced===5&&bossShot.visited.size===2,'twin failed repeat mob-to-boss ricochet');
   out.bossRicochet={bounces:bossShot.bounced,uniqueHits:bossShot.visited.size};
   A.reset();p.target=A.spawn(180,0,true);const soloBoss=p.target;
   single(twinMove);const soloShot=T.weapons[0];A.finish(3);
   A.near(100000-soloBoss.hp,Math.max(1,Math.round(twinMove.dmg*p.atk*G.Types.mult(twinMove.type,soloBoss.types)*G.Weather.mult(twinMove.type)))*6,'solo boss repeat damage');
   A.assert(soloShot.bounced===5&&soloShot.dead,'solo boss chain did not stop');out.soloBossHits=6;
   arena(1);const timed=p.target;single(base);const timedShot=T.weapons[0];
   for(let i=0;i<100&&timed.hp===100000;i++)A.advance();
   const firstHP=timed.hp;A.advance(.04);A.assert(timed.hp===firstHP,'repeat interval was skipped');
   const delay=timedShot.repeatDelay;G.Combat.updateFields(1);A.near(timedShot.repeatDelay,delay,'pause consumed repeat interval');
   A.advance(.05);A.assert(timed.hp<firstHP,'repeat did not resume after interval');
   timed.dead=true;A.finish(1);A.assert(timedShot.dead,'dead repeat target kept chain alive');out.repeatTiming=true;
   arena(1);const tagVictim=p.target,tagMove=p.moves.find(m=>m.id==='naruto-tenten-tags');single(tagMove);
   const tagShot=T.weapons[0];A.finish(.4);A.assert(tagVictim.hp===100000,'repeated tag contact dealt damage');A.finish(3);
   A.near(100000-tagVictim.hp,Math.max(1,Math.round(tagMove.dmg*p.atk*G.Types.mult(tagMove.type,tagVictim.types)*G.Weather.mult(tagMove.type))),'repeated tag exploded more than once');
   A.assert(tagShot.bounced===5&&tagShot.dead,'single-target tag did not finish');out.repeatTagSingleBlast=true;
   // Skip a nearer blocked target and keep the farther reachable choice.
   arena(1);const blocked=A.spawn(180,0),reachable=A.spawn(150,80),blockPath=G.World.projectileBlock;
   single(base);G.World.projectileBlock=(x,y)=>x>135&&x<145&&Math.abs(y)<15?{destructible:false}:false;
   try {
     const shot=T.weapons[0];for(let i=0;i<100&&!shot.chaining;i++)A.advance();
     A.assert(shot.chainTarget===reachable,'ricochet did not choose nearest reachable victim');
     for(let i=0;i<100&&reachable.hp===100000;i++)A.advance();
     A.assert(reachable.hp<100000&&blocked.hp===100000,'ricochet crossed blocked route');
   } finally {G.World.projectileBlock=blockPath;}
   out.nearestReachable=true;
   // Base piercing works without the ricochet passive and stops after two victims.
   const withBounce=p.moves;p.moves=withBounce.filter(m=>m.id!==id);
   try {
     arena(1);const first=p.target;single(twinMove);const shot=T.weapons[0];
     const second=A.spawn(shot.sx+shot.dx*220,shot.sy+shot.dy*220),third=A.spawn(shot.sx+shot.dx*300,shot.sy+shot.dy*300);
     A.finish(3);A.assert(first.hp<100000&&second.hp<100000&&third.hp===100000&&shot.hits.size===2,'twin base piercing absent or exceeded');
     A.reset();p.target=A.spawn(600,0);const distant=p.target;single(twinMove);A.finish(3);
     A.assert(distant.hp<100000,'twin cannot reach beyond previous range');
     out.twinPierceAndRange={uniqueHits:shot.hits.size,distantTarget:600};
   } finally {p.moves=withBounce;}
   arena(1);const outside=A.spawn(400,100);single(base);A.finish(2);A.assert(outside.hp===100000,'chain selected outside 160');
   arena(2);single(base);const w=T.weapons[0];
   for(let i=0;i<100&&!w.chaining;i++)A.advance();
   A.assert(w.chaining,'wall fixture did not begin hop');const wall=G.World.projectileBlock;
   G.World.projectileBlock=(x,y)=>x>140&&x<160?{destructible:false}:false;
   try{A.finish(2);A.assert(w.dead&&w.chainTarget.hp===100000,'hop passed through new wall')}finally{G.World.projectileBlock=wall}
   out.blocked=true;
   arena(3);single(base);const moving=T.weapons[0];for(let i=0;i<100&&!moving.chaining;i++)A.advance();
   moving.chainTarget.dead=true;A.finish(3);A.assert(moving.dead,'dead chain target caused stalled flight');out.deadTarget=true;
   // Batch count is fixed at cast; upgrades affect subsequent casts.
   arena(10);const twin=p.moves.find(m=>m.id==='naruto-tenten-twin');
   T.cast(p,{...twin,quantityBonusAtCast:0,count:12});const pose=T.activeFor(p);p.quantityPicks=p.quantityBonus=40;A.advance(.61);
   A.assert(pose.bounces===5&&T.weapons.every(w=>w.bounced+w.bounces===5),'midcast quantity changed later batches');
   out.snapshot=true;
   for(const reason of ['pause','clear','death','world']){
     arena(4);single(base);const w=T.weapons[0];A.advance(.21);const world=G.World;
     if(reason==='pause'){const x=w.x,y=w.y;G.Combat.updateFields(1);A.assert(w.x===x&&w.y===y,'pause advanced ricochet');continue;}
     if(reason==='clear')G.Combat.clearFields(p);
     if(reason==='death')p.dead=true;
     if(reason==='world')G.World={...world};
     try{A.advance();A.assert(!T.weapons.some(w=>w.owner===p),'ricochet leaked '+reason)}finally{p.dead=false;G.World=world}
   }
   arena(4);const cloneCard=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');cloneCard.apply(p);
   const clone=G.SelfClones.actors()[0];clone.x=clone.y=0;clone.target=p.target;
   A.assert(clone.hasMove(id)&&T.bounceCount(clone)===5,'clone lost passive');
   const seen=[],hurt=p.target.hurt;p.target.hurt=function(...args){if(args[6]===clone)seen.push(args[0]);return hurt.apply(this,args)};
   const cm=clone.moves.find(m=>m.id===base.id);T.cast(clone,{...cm,count:1,quantityBonusAtCast:0});A.finish(2);
   A.near(seen[0],cm.dmg*p.atk/3*G.Types.mult(cm.type,p.target.types)*G.Weather.mult(cm.type),'clone damage scaled twice');out.clone=true;
   // Prepare a real visible zigzag with the full passive HUD.
   A.reset();const display=[A.spawn(110,0),A.spawn(175,-85),A.spawn(245,15),A.spawn(180,100),A.spawn(95,90),A.spawn(70,-75)];p.target=display[0];
   A.castNative(base.id);A.advance(.4);
   const cv=document.createElement('canvas'),ctx=cv.getContext('2d'),labels=[],fill=ctx.fillText.bind(ctx);
   ctx.fillText=(t,...args)=>{labels.push(String(t));return fill(t,...args)};G.HUD.draw(ctx,innerWidth,innerHeight,p,{time:20});
   A.assert(labels.includes('連彈 5'),'passive HUD count absent');
   return out;
 } finally {base.count=baseCount;p.moves=original;}
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, size, mobile in [('desktop', {'width': 1200, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
            context = browser.new_context(viewport=size, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.locator('[data-quick-naruto="30009"]').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30009 && G.Game.state==="playing"')
            page.evaluate(HARNESS)
            page.evaluate(SETUP)
            page.evaluate(PROGRESSION)
            report['viewports'][label] = page.evaluate(CHECK)
            page.screenshot(path=str(OUT / f'{label}-bounce.png'))
            frames = []
            for i in range(24):
                page.evaluate('Acceptance.advance(.05)')
                page.screenshot(path=str(OUT / f'{label}-hop-{i:02}.png'))
                frames.append(page.screenshot(type='jpeg', quality=92))
            context.close()
            ffmpeg = Path(os.environ.get('LOCALAPPDATA', '')) / 'ms-playwright/ffmpeg-1011/ffmpeg-win64.exe'
            subprocess.run([str(ffmpeg), '-y', '-f', 'image2pipe', '-framerate', '10', '-c:v', 'mjpeg', '-i', 'pipe:0',
                            '-c:v', 'libvpx', '-b:v', '1800k', str(OUT / f'{label}-bounce.webm')],
                           check=True, input=b''.join(frames), capture_output=True)
            print(label, 'ricochet PASS', flush=True)
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
