"""Native flying finger-bone chains, independent quotas and source-pulse budget."""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path

os.environ.setdefault('KIMIMARO_OUT',str(Path(__file__).resolve().parents[1]/'.omx/state/kimimaro-finger-chains'))
import test_kimimaro as game
from playwright.sync_api import sync_playwright


def source_hashes():
    result=game.runtime_hashes()
    path='js/systems/ninja-tool-bounce.js'
    result[path]=hashlib.sha256((game.ROOT/path).read_bytes()).hexdigest()
    return result


HELPERS = r"""() => {
 const A=KAcceptance,K=A.K,id='naruto-kimimaro-bullets',p=A.p;
 function prepare(rank=1,quantity=0){
   A.reset();const m=A.fixture(id,rank),owner=p();owner.baseAtk=1;owner.atkMul=1;owner.buffs.atk.n=0;owner.critChance=0;
   owner.ninjaToolBouncePicks=0;
   owner.quantityPicks=owner.quantityBonus=quantity;A.near(owner.atk,1,'controlled finger attack');return m;
 }
 function watch(e){
   const events=[],hurt=e.hurt;e.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);
     events.push({raw:args[0],loss:hp-this.hp,time:K.stateFor(args[6])?.clock,
       player:args[6]===p(),clone:!!args[6]?.cloneId,id:args[7],x:this.x,y:this.y});return result;
   };return events;
 }
 function addCard(){
   const before=G.NinjaToolBounce.count(p()),card=G.LevelUp.offer(p(),100).find(c=>c.key==='stat:ninjaToolBounce');
   A.assert(card,'eligible native ninja-tool ricochet card was not offered');card.apply(p());
   A.assert(G.NinjaToolBounce.count(p())===before+1,'native ricochet card did not add exactly one jump');return card;
 }
 function single(rank=1,distance=190,cards=0){
   const m=prepare(rank);for(let n=0;n<cards;n++)addCard();
   const first=A.spawn(distance,0),hits=watch(first);p().target=first;A.cast(id);A.advance(.161);
   const s=K.stateFor(p()),action=s.action;
   A.assert(action?.kind==='bullets'&&s.bullets.length===1&&action.emitted===1,'native first pulse did not produce one actual bone');
   const bone=s.bullets[0];s.action=null;
   // Only the source's remaining four pulses stop. The emitted native bone
   // keeps its real movement, collision, damage and chain logic.
   return {m,first,hits,bone,action,startedAt:s.clock};
 }
 function until(predicate,limit=5,dt=.005){
   for(let time=0;time<limit;time+=dt){if(predicate())return;A.step(dt)}A.assert(predicate(),'finger-chain event timed out');
 }
 const live=(owner=p())=>K.bullets.filter(b=>b.owner===owner);
 function cluster(){return Array.from({length:6},(_,i)=>{const a=Math.PI+i*Math.PI/3;return A.spawn(230+Math.cos(a)*60,Math.sin(a)*60)})}
 function artTrace(){
   const canvas=document.createElement('canvas');canvas.width=800;canvas.height=600;const c=canvas.getContext('2d');c.translate(200,300);
   const color=document.createElement('canvas').getContext('2d'),commands=[];let points=0,closed=false;
   for(const name of ['beginPath','moveTo','lineTo','closePath']){
     const original=c[name].bind(c);c[name]=(...args)=>{
       if(name==='beginPath'){points=0;closed=false}else if(name==='closePath')closed=true;else points++;
       return original(...args);
     };
   }
   for(const name of ['stroke','fill']){
     const original=c[name].bind(c);c[name]=(...args)=>{
       const style=name==='stroke'?c.strokeStyle:c.fillStyle;color.clearRect(0,0,1,1);color.fillStyle=style;color.fillRect(0,0,1,1);
       const [r,g,b]=color.getImageData(0,0,1,1).data;
       commands.push({name,style,points,closed,cyan:g>=180&&b>=140&&g>r+10,alpha:c.globalAlpha});return original(...args);
     };
   }
   G.KimimaroArt.drawAir(c,K.renderStates());
   return {cyanStrokes:commands.filter(v=>v.cyan&&v.name==='stroke'),
     cyanDiamonds:commands.filter(v=>v.cyan&&v.closed&&v.points===4),commands};
 }
 window.KFinger={...A,K,p,id,prepare,addCard,watch,single,until,live,cluster,artTrace};
}"""

RANK_CHAINS = r"""() => {
 const A=KFinger,p=A.p,out=[];
 for(let rank=1;rank<=5;rank++){
   const {m,first,hits,bone,startedAt}=A.single(rank),targets=[first,...Array.from({length:rank+1},(_,i)=>A.spawn(190,(i+1)*70))],logs=[hits,...targets.slice(1).map(A.watch)];
   A.near(m.chainCount,rank,'rank chain count');A.near(m.chainRadius,180,'rank chain radius');A.near(m.cd,2.4,'finger cooldown');
   A.assert(bone.baseChainCount===rank&&bone.cardChains===0&&bone.chainCount===rank&&bone.remainingChains===rank&&bone.chainHops===0,'native shot did not snapshot its unbought rank chain allowance');
   A.advance(.15);A.assert(logs.every(log=>!log.length),'bone damage arrived before actual flight');
   let previousAge=bone.age,previousTravel=bone.travelled,maxLive=0;
   A.until(()=>{
     const live=A.live();maxLive=Math.max(maxLive,live.length);A.assert(live.length<=1&&live.every(b=>b===bone),'one bone split into additional chain projectiles');
     A.assert(bone.age>=previousAge&&bone.travelled>=previousTravel,'chain reset total age or traveled distance');previousAge=bone.age;previousTravel=bone.travelled;
     if(live.length)A.near(Math.hypot(bone.vx,bone.vy),600,'chain flight speed changed');return !live.length;
   });
   A.assert(logs.every((log,index)=>log.length===(index<=rank?1:0)),'rank did not hit exactly 2..6 different enemies');
   const raw=[9,10.8,12.6,15.3,18][rank-1],damage=[9,11,13,15,18][rank-1];
   const events=logs.slice(0,rank+1).map(log=>log[0]);
   for(const hit of events){A.near(hit.raw,raw,'chain hop split or reduced per-bone damage');A.assert(hit.loss===damage&&hit.player&&hit.id===A.id,'native chain hit lost rounding/ownership')}
   for(let i=1;i<events.length;i++)A.assert(events[i].time>events[i-1].time+.02,'chain hop teleported its damage without actual flight');
   A.assert(events[0].time-startedAt>.20,'first bone ignored launch-to-target flight delay');
   A.assert(bone.chainHops===rank&&bone.remainingChains===0&&bone.phaseHits.get(0).size===rank+1,'per-bone chain allowance or shared victim dedup failed');
   A.near(bone.age*600,bone.travelled,'cumulative flight age reset on a later hop');
   A.assert(A.K.stateFor(p()).emitted===1,'isolated real bone spawned new emission bodies');
   out.push({rank,chainHops:bone.chainHops,totalVictims:events.length,rawPerHit:raw,roundedPerHit:damage,events,travelled:bone.travelled,age:bone.age,maxLive});
 }
 return out;
}"""

RADIUS_LOS_AND_RANGE = r"""() => {
 const A=KFinger,out=[];
 for(const [distance,expected] of [[180,1],[181,0]]){
   const {first,hits,bone}=A.single(),next=A.spawn(first.x+distance,0),nextHits=A.watch(next);A.until(()=>!A.live().length);
   A.assert(hits.length===1&&nextHits.length===expected&&bone.chainHops===expected,'victim-centered 180px chain radius boundary '+distance);
   out.push({distance,secondHits:nextHits.length,hops:bone.chainHops});
 }
 const {m,first,hits,bone}=A.single(1,370),distant=A.spawn(520,0),distantHits=A.watch(distant);A.until(()=>!A.live().length);
 A.assert(hits.length===1&&distantHits.length===1&&bone.chainHops===1,'chain segment stopped at the original firing range');
 A.assert(bone.travelled>m.range&&bone.range>180&&bone.distance<bone.range,'chain segment did not get its own complete physical travel budget');
 out.push({beyondOriginalRange:true,nominal:m.range,totalTravel:bone.travelled,hopBudget:bone.range});
 const blocked=A.single(),near=A.spawn(190,80),nearHits=A.watch(near),clear=A.spawn(280,0),clearHits=A.watch(clear);
 G.World.isWall=(x,y)=>y>35&&y<55;A.until(()=>!A.live().length);
 A.assert(blocked.hits.length===1&&!nearHits.length&&clearHits.length===1&&blocked.bone.chainTarget===clear,'nearest blocked target was not skipped for a reachable neighbor');
 out.push({nearestBlockedSkipped:true,clearNeighborHit:true});
 return out;
}"""

FIXED_NEXT_LEG_AND_OBSTACLES = r"""() => {
 const A=KFinger,out=[];
 const moving=A.single(),next=A.spawn(190,100),nextHits=A.watch(next);A.until(()=>moving.bone.chainHops===1);
 const b=moving.bone,velocity={vx:b.vx,vy:b.vy},before={age:b.age,travelled:b.travelled};next.x=350;next.y=140;G.EnemyMgr.rebuildGrid();A.advance(.02);
 A.assert(A.live().includes(b),'moving-target leg disappeared before finishing its shot snapshot');
 A.near(b.vx,velocity.vx,'chain leg homed horizontally');A.near(b.vy,velocity.vy,'chain leg homed vertically');
 A.near(b.travelled-before.travelled,12,'chain leg actual speed is not 600px/s');A.assert(b.age>before.age,'chain leg reset animation age');
 A.until(()=>!A.live().length);A.assert(moving.hits.length===1&&!nextHits.length,'chain leg followed a target that moved away');
 out.push({fixedSnapshotVelocity:velocity,missedMovedTarget:true});
 const wall=A.single(),wallTarget=A.spawn(190,100),wallHits=A.watch(wallTarget);A.until(()=>wall.bone.chainHops===1);
 G.World.isWall=(x,y)=>y>25&&y<45;A.until(()=>!A.live().length);
 A.assert(wall.hits.length===1&&!wallHits.length,'actual wall crossing did not stop an already emitted chain leg');
 out.push({wallStoppedInFlightLeg:true});
 const propCase=A.single(),propTarget=A.spawn(190,100),propHits=A.watch(propTarget);A.until(()=>propCase.bone.chainHops===1);
 const q=propCase.bone,prop={x:(q.x+propTarget.x)/2,y:(q.y+propTarget.y)/2,r:8,type:'chest',solid:true,destructible:true,hp:10000,tx:3,ty:0};
 G.World.projectileBlock=(x,y,r)=>Math.hypot(x-prop.x,y-prop.y)<=prop.r+r?prop:false;A.until(()=>!A.live().length);
 A.assert(propCase.hits.length===1&&!propHits.length&&prop.hp<10000,'solid prop did not stop the chain leg through native prop damage');
 out.push({propStoppedLeg:true,propLoss:10000-prop.hp});
 const none=A.single(5);A.until(()=>!A.live().length);A.assert(none.hits.length===1&&none.bone.chainHops===0,'no-neighbor hit did not finish without a split or extra hop');
 return out;
}"""

FULL_VOLLEY_AND_QUANTITY = r"""() => {
 const A=KFinger,p=A.p,out=[];
 for(const [quantity,expected] of [[0,5],[1,6],[12,15]]){
   const m=A.prepare(3,quantity),targets=A.cluster(),logs=targets.map(A.watch);p().target=targets[0];A.cast(A.id);
   const source=A.K.activeFor(p()),seen=new Set(),emissions=[];let maxLive=0,lastCount=0;
   A.assert(JSON.stringify(source.hitTimes)===JSON.stringify([.16,.23,.30,.37,.44]),'finger volley lost its original five pulse times');
   for(let n=0;n<360;n++){
     A.step(.005,true);const live=A.live();maxLive=Math.max(maxLive,live.length);for(const b of live){seen.add(b);A.assert(b.baseChainCount===3&&b.cardChains===0&&b.chainCount===3,'quantity cards added chain jumps')}
     A.assert(live.length<=expected&&live.length<=15,'chain hops grew the physical projectile budget');
     if(source.emitted!==lastCount){emissions.push({age:source.age,total:source.emitted});lastCount=source.emitted;}
   }
   A.assert(source.emitted===expected&&seen.size===expected&&A.K.stateFor(p()).emitted===expected,'chain duplicated shots or quantity count was incorrect');
   A.assert(emissions.length===5&&emissions.every((event,i)=>Math.abs(event.age-[.16,.23,.30,.37,.44][i])<.006),'five native emission pulses changed timing');
   const hits=logs.flat();A.assert(hits.length===expected*4,'each original bone did not get its own three-hop chain allowance');
   for(const b of seen)A.assert(b.chainHops===3&&b.remainingChains===0&&b.phaseHits.get(0).size===4,'one bone shared another bone chain quota or repeated a victim');
   for(const hit of hits){A.near(hit.raw,12.6,'quantity divided per-hop damage');A.assert(hit.loss===13&&hit.player&&hit.id===A.id,'quantity chain bypassed native full-hit damage')}
   A.assert(targets.reduce((sum,e)=>sum+e.maxHp-e.hp,0)===expected*4*13,'aggregate native chain HP damage was reduced or duplicated');
   A.assert(A.K.stateFor(p()).castCounts.bullets===1&&Math.abs(m.t-.6)<.011,'chains restarted the 2.4-second cast cooldown');
   A.assert(!A.live().length,'completed chain volley retained physical shots');
   out.push({quantity,count:expected,emissions,uniqueBones:seen.size,maxLive,totalHits:hits.length,chainCountPerBone:3,cooldown:m.t});
 }
 A.prepare();p().target=A.spawn(50,0);A.step(.01,true);
 A.assert(!A.K.activeFor(p())&&!A.live().length,'finger volley started while a close enemy required melee defense');
 return {volleys:out,noCloseEnemyRequirement:true};
}"""

UPGRADE_SNAPSHOT = r"""() => {
 const A=KFinger,p=A.p,{m,bone,first}=A.single(1,250),old={chains:bone.chainCount,remaining:bone.remainingChains,damage:bone.move.dmg};
 A.assert(G.Moves.levelUp(m)&&m.chainCount===2,'native skill upgrade did not add one chain');A.step(.001);
 A.assert(A.live()[0]===bone&&bone.chainCount===old.chains&&bone.remainingChains===old.remaining,'skill upgrade rewrote an already flying bone chain quota');
 A.near(bone.move.dmg,old.damage,'skill upgrade rewrote an already flying bone damage');
 p().target=first;A.cast(A.id);A.advance(.161);const s=A.K.stateFor(p());s.action=null;
 const newest=s.bullets.find(b=>b!==bone);A.assert(s.bullets.length===2&&newest&&newest.chainCount===2&&newest.remainingChains===2,'new native pulse did not use its upgraded chain snapshot');
 A.near(newest.move.dmg,54,'new pulse did not use upgraded per-bone damage');
 const levels=[{rank:m.lvl,chainCount:m.chainCount}];while(m.lvl<5){A.assert(G.Moves.levelUp(m),'native chain upgrade failed');levels.push({rank:m.lvl,chainCount:m.chainCount})}
 A.assert(levels.every(v=>v.chainCount===v.rank),'native upgrades did not progress through one to five additional jumps');
 A.assert(bone.chainCount===1&&newest.chainCount===2,'later upgrades rewrote independent live snapshots');
 return {oldSnapshot:old,newSnapshot:{chains:newest.chainCount,damage:newest.move.dmg},levels};
}"""

NATIVE_CARD_AND_TOTAL_CHAINS = r"""() => {
 const A=KFinger,p=A.p;A.prepare();
 A.assert(G.NinjaToolBounce.eligibleMove(A.id)&&G.NinjaToolBounce.eligible(p()),'finger bones did not enable the global ninja-tool card');
 p().moves=[];p().slots=[];
 A.assert(!G.NinjaToolBounce.eligible(p())&&!G.LevelUp.offer(p(),100).some(c=>c.key==='stat:ninjaToolBounce'),'card appeared without any eligible learned tool');
 A.assert(p().addMove(A.id),'could not restore native finger skill');A.addCard();A.addCard();
 A.assert(p().ninjaToolBouncePicks===2,'repeated native cards did not accumulate');
 const results=[];
 for(const [rank,cards,expectedHops] of [[1,1,2],[5,2,7],[1,3,4]]){
   const {first,hits,bone}=A.single(rank,190,cards),targets=[first,...Array.from({length:expectedHops+1},(_,i)=>A.spawn(190,(i+1)*70))],logs=[hits,...targets.slice(1).map(A.watch)];
   A.assert(bone.baseChainCount===rank&&bone.cardChains===cards&&bone.chainCount===expectedHops&&bone.remainingChains===expectedHops,'native card quota was capped, omitted or added more than once');
   A.until(()=>!A.live().length);
   A.assert(logs.every((log,index)=>log.length===(index<=expectedHops?1:0)),'global card did not allow the exact additional distinct targets');
   A.assert(bone.chainHops===expectedHops&&bone.phaseHits.get(0).size===expectedHops+1,'global card shared/repeated a per-bone victim ledger');
   const raw=rank===5?18:9;for(const log of logs.slice(0,expectedHops+1)){A.near(log[0].raw,raw,'global ricochet reduced each hop damage');A.assert(log[0].loss===raw&&log[0].player,'global ricochet bypassed native HP damage')}
   A.assert(A.K.stateFor(p()).emitted===1,'global ricochet split a bone into more projectiles');
   results.push({rank,cards,base:bone.baseChainCount,extra:bone.cardChains,hops:bone.chainHops,totalVictims:expectedHops+1,rawPerHit:raw});
 }
 return {nativeCardEligible:true,repeatedCardCount:2,results};
}"""

CARD_CAST_SNAPSHOT = r"""() => {
 const A=KFinger,p=A.p;A.prepare(2,1);A.addCard();const targets=A.cluster(),logs=targets.map(A.watch);p().target=targets[0];A.cast(A.id);
 const source=A.K.activeFor(p());A.advance(.161);const seen=new Set(A.live());
 A.assert(seen.size===2&&[...seen].every(b=>b.baseChainCount===2&&b.cardChains===1&&b.chainCount===3),'first quantity-adjusted pulse missed its cast card snapshot');
 A.addCard();A.assert(G.NinjaToolBounce.count(p())===2,'mid-cast card application failed');
 for(let n=0;n<300;n++){
   A.step(.005,true);for(const bone of A.live()){
     seen.add(bone);A.assert(bone.baseChainCount===2&&bone.cardChains===1&&bone.chainCount===3,'later pulse resampled a card added during the same five-pulse cast');
   }
 }
 A.assert(source.emitted===6&&seen.size===6&&[...seen].every(b=>b.chainHops===3&&b.phaseHits.get(0).size===4),'first complete volley did not retain identical card quotas');
 A.assert(logs.flat().length===24,'mid-cast card changed the already-cast volley total hits');
 for(const hit of logs.flat()){A.near(hit.raw,10.8,'card/quantity cast changed per-hop damage');A.assert(hit.loss===11,'card/quantity cast native rounding')}
 for(let n=0;n<1000&&A.K.stateFor(p()).castCounts.bullets<2;n++)A.step(.005,true);
 A.assert(A.K.stateFor(p()).castCounts.bullets===2,'next native cast did not resume after its source cooldown');
 const nextSource=A.K.activeFor(p());A.assert(nextSource?.kind==='bullets','second source cast missing');A.advance(.161);
 const next=A.live();A.assert(next.length===2&&next.every(b=>b.baseChainCount===2&&b.cardChains===2&&b.chainCount===4),'next cast did not use the new total card count exactly once');
 A.assert([...seen].every(b=>b.cardChains===1&&b.chainCount===3),'new cast mutated the old volley snapshots');
 A.K.stateFor(p()).action=null;
 return {firstVolleyCards:1,currentCards:2,firstVolleyBones:seen.size,firstVolleyHits:24,nextFirstPulseBones:next.length,nextCastChains:4};
}"""

CHAIN_ART = r"""() => {
 const A=KFinger,{bone}=A.single(),initial=A.artTrace();
 A.assert(bone.chainHops===0&&initial.cyanStrokes.length===0&&initial.cyanDiamonds.length===0,'initial bone was glowing before any chain');
 A.spawn(370,0);A.until(()=>bone.chainHops===1);A.advance(.06);
 A.assert(A.live().includes(bone)&&bone.chainHops===1,'chain-art fixture finished its long next leg too early');
 A.assert(bone.chainTrail.length===8&&bone.age-bone.chainFlash.time<.16,'chain trail was not bounded to eight samples or turn flash expired early');
 const turning=A.artTrace();
 A.assert(turning.cyanStrokes.some(command=>!command.closed&&command.points>=2&&command.points<=9),'actual renderer omitted the bright cyan-green chain trail');
 A.assert(turning.cyanDiamonds.length>0,'actual renderer omitted the four-point turn flash');
 A.advance(.12);const expired=A.artTrace();
 A.assert(A.live().includes(bone)&&bone.chainHops===1&&bone.age-bone.chainFlash.time>.16,'flash-expiry fixture had already entered another hop');
 A.assert(expired.cyanDiamonds.length===0&&expired.cyanStrokes.some(command=>!command.closed),'turn flash did not expire independently of persistent trail');
 return {initialBoneWhite:true,trailSamples:bone.chainTrail.length,trailColor:turning.cyanStrokes.find(command=>!command.closed).style,
   turnFlashColor:turning.cyanDiamonds[0].style,turnFlashDuration:.16,expiredWithoutNewHop:true};
}"""

CLONE_AND_LIFECYCLE = r"""() => {
 const A=KFinger,p=A.p;A.prepare();A.addCard();A.addCard();p().moves[0].t=999;const clone=G.SelfClones.summon(p());A.assert(clone,'native self-clone missing');
 A.assert(G.NinjaToolBounce.count(clone)===2,'native clone did not inherit global ricochet picks');
 const targets=Array.from({length:4},(_,i)=>A.spawn(clone.x+190,clone.y+i*70)),logs=targets.map(A.watch);clone.target=targets[0];
 A.resume();try{G.Combat.tick(.001,clone,0)}finally{A.pause()}
 A.advance(.161);const s=A.K.stateFor(clone);A.assert(s.bullets.length===1,'clone first native pulse did not emit one bone');
 const b=s.bullets[0];A.assert(b.baseChainCount===1&&b.cardChains===2&&b.chainCount===3,'clone applied card chains incorrectly or more than once');s.action=null;A.until(()=>!A.live(clone).length);
 A.assert(logs.every(log=>log.length===1&&log[0].clone&&!log[0].player&&log[0].id===A.id),'clone chain lost independent native ownership');
 for(const log of logs){A.near(log[0].raw,3,'clone chain damage applied owner ratio more than once');A.assert(log[0].loss===3,'native clone hop rounding')}
 A.assert(b.chainHops===3&&b.phaseHits.get(0).size===4&&!A.K.stateFor(p())?.castCounts.bullets,'parent cast contaminated clone card-chain fixture');
 G.Combat.clearFields(p());A.assert(!A.live().length&&!G.SelfClones.actors().length,'parent cleanup retained clone bones');
 const paused=A.single(),snapshot=()=>JSON.stringify({x:paused.bone.x,y:paused.bone.y,age:paused.bone.age,travelled:paused.bone.travelled,hops:paused.bone.chainHops,remaining:paused.bone.remainingChains});
 const before=snapshot();A.pause();G.Combat.updateFields(.5);A.assert(snapshot()===before,'pause advanced a flying chain bone');
 p().frozen=true;A.advance(.5,true);A.assert(snapshot()===before,'freeze advanced chain flight or quota');p().frozen=false;
 const cleanup=[];
 for(const reason of ['clear','death','world','quit','toUI']){
   const f=A.single();const neighbor=A.spawn(190,70),neighborHits=A.watch(neighbor),owner=p(),originalWorld=G.World;
   if(reason==='clear')G.Combat.clearFields(owner);else if(reason==='death')owner.dead=true;else if(reason==='world')G.World={...originalWorld};
   else{A.resume();if(reason==='quit')G.Game.quit();else G.Game.toUI('menu')}
   try{
     if(reason==='quit'||reason==='toUI')A.K.update(1);else A.advance(1,true);
     A.assert(!A.live(owner).length&&!f.hits.length&&!neighborHits.length,'abandoned emitted bone or future chain damaged enemies after '+reason);
     cleanup.push(reason);
   }finally{if(reason==='world')G.World=originalWorld;if(reason==='death')owner.dead=false;if(reason==='quit'||reason==='toUI'){G.Game.startRun();A.pause()}}
 }
 return {nativeCloneHits:4,cloneInheritedCards:2,cloneDamagePerHop:3,pause:true,freeze:true,cleanup};
}"""


def main():
    game.OUT.mkdir(parents=True,exist_ok=True)
    report={'url':game.URL,'errors':[],'failedRequests':[],'failures':[],'viewports':{},'sourceHashes':source_hashes()}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=game.CHROME,headless=True)
        for label,viewport,mobile in [('desktop',{'width':1280,'height':900},False),('mobile',{'width':390,'height':844},True)]:
            context=browser.new_context(viewport=viewport,is_mobile=mobile,has_touch=mobile,service_workers='block')
            page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
            page.on('response',lambda r:report['failedRequests'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            result=report['viewports'][label]={}
            try:
                frame=game.boot(page,label);frame.evaluate(HELPERS)
                for name,check in [('rankChains',RANK_CHAINS),('radiusLosAndRange',RADIUS_LOS_AND_RANGE),('fixedLegAndObstacles',FIXED_NEXT_LEG_AND_OBSTACLES),
                  ('fullVolleyAndQuantity',FULL_VOLLEY_AND_QUANTITY),('upgradeSnapshot',UPGRADE_SNAPSHOT),
                  ('nativeCardAndTotalChains',NATIVE_CARD_AND_TOTAL_CHAINS),('cardCastSnapshot',CARD_CAST_SNAPSHOT),('chainArt',CHAIN_ART),('cloneAndLifecycle',CLONE_AND_LIFECYCLE)]:
                    print(label,name,flush=True)
                    try:result[name]=frame.evaluate(check)
                    except Exception as error:report['failures'].append(label+':'+name+': '+str(error))
            except Exception as error:report['failures'].append(label+':boot: '+str(error))
            finally:context.close()
        browser.close()
    report['sourceHashesAfter']=source_hashes()
    if report['sourceHashesAfter']!=report['sourceHashes']:report['failures'].append('runtime changed during acceptance')
    report['ok']=not(report['errors'] or report['failedRequests'] or report['failures'])
    path=game.OUT/'report-finger-chains.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'report':str(path)},ensure_ascii=True))
    if not report['ok']:raise SystemExit(1)


if __name__=='__main__':main()
