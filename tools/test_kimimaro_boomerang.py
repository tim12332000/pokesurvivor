"""Native acceptance for quantity-scaled bone boomerangs and per-bone cooldowns."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault('KIMIMARO_OUT',str(Path(__file__).resolve().parents[1]/'.omx/state/kimimaro-boomerang'))
import test_kimimaro as game
from playwright.sync_api import sync_playwright


HELPERS = r"""() => {
 const A=KAcceptance,K=A.K,id='naruto-kimimaro-boomerang';let p=A.p();
 function prepare(rank=1){
   p=A.p();if(window.KBoom)KBoom.p=p;
   A.reset();const m=A.fixture(id,rank);p.baseAtk=1;p.atkMul=1;p.buffs.atk.n=0;p.critChance=0;
   p.quantityPicks=p.quantityBonus=0;A.near(G.Quantity.count(p,1),1,'single-bone fixture quantity');
   A.near(p.atk,1,'controlled throw attack');return m;
 }
 const state=(actor=p)=>K.boomerangState(actor);
 function start(distance=100,rank=1,cdMul=1){
   const m=prepare(rank);p.cdMul=cdMul;
   const e=A.spawn(distance,0),hits=A.watch(e);p.target=e;A.step(.001,true);
   A.assert(state()?.projectile?.phase==='out','native independent throw did not launch');
   A.assert(state().count===rank&&state().projectiles.length===rank,'zero-card fixture did not launch one bone per skill rank');
   A.assert(!A.action()&&p.slots.length===0,'throw created a body action or active slot');
   return {m,e,hits};
 }
 function until(predicate,limit=2,dt=.005){
   for(let elapsed=0;elapsed<limit;elapsed+=dt){if(predicate())return elapsed;A.step(dt,true)}
   A.assert(predicate(),'boomerang event timed out');return limit;
 }
 function single(rank=1,distance=400){
   const m=prepare(rank);m.count=1;const anchor=A.spawn(distance,0),hits=A.watch(anchor);p.target=anchor;A.step(.001,true);
   A.assert(state().count===1&&state().projectiles.length===1,'single-flight piercing fixture did not isolate count');
   return {m,anchor,hits,b:state().projectile};
 }
 window.KBoom={...A,p,K,id,prepare,state,start,until,single};
}"""

PROGRESSION = r"""() => {
 const A=KBoom,p=A.p;A.reset();p.moves=[];p.slots=[];p.level=2;
 A.assert(!G.Moves.poolFor(p.mon).includes(A.id)&&!p.addMove(A.id),'boomerang learned before Lv3');
 p.level=3;A.assert(G.Moves.poolFor(p.mon).includes(A.id),'Lv3 pool omitted boomerang');
 A.assert(G.LevelUp.offer(p,100).some(c=>c.key==='new:'+A.id),'Lv3 normal learn choice omitted boomerang');
 A.assert(p.addMove(A.id)&&p.slots.length===0,'learning bone boomerang consumed a slot');
 const ranks=[];for(let rank=1;rank<=5;rank++){
   const m=G.Moves.instance(A.id,rank);A.assert(m.passive&&m.cd===1,'throw is not slotless with a one-second base cooldown rank '+rank);
   A.near(m.dmg,[64,76.8,89.6,108.8,128][rank-1],'full-hit base rank '+rank);
   A.near(m.range,[600,650,700,750,800][rank-1],'throw range rank '+rank);
   A.near(m.count,rank,'base bone count rank '+rank);
   A.near(m.pierce,rank-1,'base piercing budget rank '+rank);
   ranks.push({rank,damage:m.dmg,range:m.range,count:m.count,pierce:m.pierce,cd:m.cd,passive:m.passive});
 }
 A.prepare();A.step(.001,true);A.advance(1,true);
 A.assert(!A.state()?.projectile&&!(A.state()?.launches),'idle throw escaped hand without a target');
 return {gate:3,slotless:true,idleInHand:true,ranks};
}"""

HIT_AND_RETURN = r"""() => {
 const A=KBoom,p=A.p,out=[];
 for(let rank=1;rank<=5;rank++){
   const {m,e,hits}=A.start(100,rank);A.until(()=>A.state().lanes.every(lane=>lane.hits===1));
   let hitState=A.state();const base=[64,76.8,89.6,108.8,128][rank-1];
   const raw=base*G.Types.mult(m.type,e.types)*G.Weather.mult(m.type);
   A.assert(hits.length===rank&&hitState.projectiles.length===rank,'each ranked bone did not hit once');
   A.assert(hitState.projectiles.every(q=>q.phase===(rank===1?'return':'out')),'first contact ignored the per-rank piercing budget');
   for(const hit of hits){
     A.near(hit.raw,raw,'multiple ranked bones split their individual damage');
     A.assert(hit.loss===Math.max(1,Math.round(raw))&&hit.owner&&hit.id===A.id,'native full hit lost damage/owner');
   }
   A.assert(e.maxHp-e.hp===rank*Math.max(1,Math.round(raw)),'rank damage was not full damage per bone');
   e.dead=true;p.target=null;
   if(rank>1)A.until(()=>A.state().projectiles.length===rank&&A.state().projectiles.every(q=>q.phase==='return'));
   hitState=A.state();const projectile=hitState.projectile;
   const returnTarget=A.spawn((projectile.x+hitState.hand.x)/2,(projectile.y+hitState.hand.y)/2),returnHits=A.watch(returnTarget);
   A.until(()=>A.state().catches===rank);
   A.assert(returnHits.length===0&&hits.length===rank,'ranked bones dealt another hit during return');
   const waitedInHand=A.state().projectiles.length===0;
   if(waitedInHand){
     A.assert(A.state().lanes.every(lane=>lane.cooldown>0),'early ranked catches ignored remaining launch cooldown');
     const launches=A.state().launches;A.until(()=>A.state().launches>launches);
   }
   A.assert(A.state().projectiles.length===rank&&A.state().projectiles.every(q=>q.phase==='out'),'ranked bones did not relaunch after hand wait and cooldown');
   out.push({rank,count:rank,rawPerBone:hits[0].raw,lossPerBone:hits[0].loss,totalLoss:rank*hits[0].loss,hits:hits.length,returnHits:returnHits.length,waitedInHand});
 }
 return out;
}"""

FIRST_TARGET_AND_CURVE = r"""() => {
 const A=KBoom,p=A.p;A.prepare();const front=A.spawn(95,0),rear=A.spawn(190,0),frontHits=A.watch(front),rearHits=A.watch(rear);
 p.target=rear;A.step(.001,true);A.until(()=>frontHits.length>0);
 A.assert(frontHits.length===1&&rearHits.length===0&&A.state().projectile.phase==='return','outbound pierced first body');
 const baseline=A.start(400),first={...A.state().projectile},samples=[];let previousTime=0;
 for(const time of [.05,.15,.25,.35]){
   A.advance(time-previousTime,true);previousTime=time;const q=A.state().projectile;
   A.assert(q?.phase==='out'&&q.castId===first.castId,'curve returned before reaching its initial target');
   A.near(Math.hypot(q.vx,q.vy),650,'curve does not preserve authored path speed');
   samples.push({time,x:q.x,y:q.y,vx:q.vx,vy:q.vy});
 }
 const maxDeviation=Math.max(...samples.map(q=>Math.abs(q.y)));
 const maxTurn=Math.max(...samples.map(q=>Math.abs(first.vx*q.vy-first.vy*q.vx)/(650*650)));
 A.assert(maxDeviation>20,'outbound throw stayed on the initial aiming line');
 A.assert(maxTurn>.15,'outbound velocity never visibly changed direction');
 A.until(()=>baseline.hits.length>0);
 A.assert(baseline.hits.length===1&&A.state().projectile.phase==='return','curved outbound path failed to hit its original stationary target');
 const moved=A.start(400);moved.e.y=180;G.EnemyMgr.rebuildGrid();previousTime=0;
 for(const sample of samples){
   A.advance(sample.time-previousTime,true);previousTime=sample.time;const q=A.state().projectile;
   A.assert(q?.phase==='out','moved-target curve unexpectedly returned');
   A.near(q.x,sample.x,'target motion rewrote outbound snapshot curve x');
   A.near(q.y,sample.y,'target motion rewrote outbound snapshot curve y');
   A.near(q.vx,sample.vx,'target motion changed authored tangent vx');
   A.near(q.vy,sample.vy,'target motion changed authored tangent vy');
 }
 return {firstBodyOnly:true,maxDeviation,maxTurn,originalTargetHit:true,snapshotCurve:true,samples};
}"""

CADENCE = r"""() => {
 const A=KBoom,out=[];
 for(const distance of [60,280]){
   A.start(distance);let waitedInHand=false;
   for(let n=0;n<600;n++){
     A.step(.005,true);const state=A.state();
     A.assert(state.launches-state.catches>=0&&state.launches-state.catches<=1,'an owner duplicated a flying throw');
     A.assert((state.launches-state.catches===1)===!!state.projectile,'flight count differs from actual boomerang ownership');
     if(!state.projectile){waitedInHand=true;A.assert(state.cooldown>0,'caught throw waited after its cooldown was ready');}
     A.assert(!A.action(),'independent boomerang occupied body scheduling');
   }
   const s=A.state(),log=s.log||[];
   A.assert(s.catches>=2&&log.some(v=>v.kind==='catch'),'catch event log missing');
   const launches=log.filter(v=>v.kind==='launch');
   for(let i=1;i<launches.length;i++)A.assert(launches[i].time-launches[i-1].time>=1-1e-8,'launch repeated before one-second cooldown');
   A.assert(s.launches<=4&&waitedInHand,'short round trip did not wait for its one-second cooldown');
   out.push({distance,launches:s.launches,catches:s.catches,hits:s.hits,waitedInHand,log});
 }
 A.start(60);A.until(()=>A.state().catches===1);const caught=A.state(),firstLaunch=caught.log.find(v=>v.kind==='launch');
 A.assert(!caught.projectile&&caught.cooldown>0,'near throw did not remain in hand until ready');
 A.advance(caught.cooldown-.005,true);A.assert(A.state().launches===1,'throw relaunched before readyAt');
 A.advance(.01,true);const ready=A.state(),next=ready.log.filter(v=>v.kind==='launch').at(-1);
 A.assert(ready.launches===2,'ready in-hand throw failed to relaunch');A.near(next.time-firstLaunch.time,1,'base launch cooldown');
 return out;
}"""

COOLDOWN_MODIFIERS = r"""() => {
 const A=KBoom,out=[];
 for(const [multiplier,expected] of [[.25,.25],[.01,.05]]){
   A.start(60,1,multiplier);
   const initial=A.state(),first=initial.log.find(v=>v.kind==='launch');
   A.near(initial.readyAt-first.time,expected,'launch cooldown multiplier/minimum');
   for(let n=0;n<400;n++){
     A.step(.005,true);const s=A.state();A.assert(s.launches-s.catches>=0&&s.launches-s.catches<=1,'cooldown modifier duplicated a flying bone');
   }
   const state=A.state(),launches=state.log.filter(v=>v.kind==='launch');
   A.assert(state.launches>3,'cooldown reduction had no effect');
   for(let i=1;i<launches.length;i++)A.assert(launches[i].time-launches[i-1].time>=expected-1e-8,'launch bypassed reduced cooldown/minimum');
   out.push({multiplier,expected,launches:state.launches,catches:state.catches,log:state.log});
 }
 return out;
}"""

MULTI_CADENCE = r"""() => {
 const A=KBoom,p=A.p;A.prepare();p.quantityPicks=p.quantityBonus=4;
 const near=A.spawn(60,0),far=A.spawn(-560,0),nearHits=A.watch(near),farHits=A.watch(far);p.target=near;
 A.step(.001,true);let state=A.state();
 A.assert(state.count===2&&state.projectiles.length===2&&state.lanes.length===2,'four quantity cards did not create two real flights');
 A.assert(state.lanes[0].projectile.vx>0&&state.lanes[1].projectile.vx<0,'lane indices did not distribute throws across separate targets');
 const ids=state.projectiles.map(q=>q.castId);A.assert(new Set(ids).size===2,'lanes share the same physical projectile');
 // Isolate round-trip/CD geometry here; actual card piercing is tested separately.
 for(const q of state.projectiles)q.remainingPierce=0;
 A.advance(.015,true);state=A.state();
 const offsets=state.lanes.map((lane,i)=>{
   const launch=lane.log.find(v=>v.kind==='launch'),target=i===0?near:far;
   const dx=target.x-launch.x,dy=target.y-launch.y,q=lane.projectile;
   A.assert(q?.phase==='out','left/right curve fixture returned before sampling');
   return (dx*(q.y-launch.y)-dy*(q.x-launch.x))/Math.hypot(dx,dy);
 });
 A.assert(offsets[0]*offsets[1]<0&&offsets.every(v=>Math.abs(v)>.1),'adjacent flight lanes did not bend in opposite relative directions');
 A.until(()=>A.state().lanes[0].catches===1);
 state=A.state();A.assert(!state.lanes[0].projectile&&state.lanes[0].cooldown>0,'near lane ignored its own remaining launch cooldown');
 A.assert(state.lanes[1].projectile&&state.lanes[1].catches===0,'far lane disappeared when the near lane caught');
 A.until(()=>A.state().lanes[0].launches===2);
 state=A.state();A.assert(state.lanes[1].launches===1&&state.lanes[1].catches===0,'near lane waited for or reset the far lane');
 A.until(()=>A.state().lanes[1].launches===2);
 state=A.state();const longLog=state.lanes[1].log,catchIndex=longLog.findIndex(v=>v.kind==='catch');
 A.assert(nearHits.length>=2&&farHits.length>=1,'separate flight lanes failed to damage their separate targets');
 A.assert(longLog[catchIndex+1]?.kind==='launch','late lane catch did not immediately relaunch independently');
 A.near(longLog[catchIndex+1].time,longLog[catchIndex].time,'late lane inherited another lane cooldown');
 A.assert(longLog[catchIndex].time-longLog[0].time>1,'far lane fixture did not outlast its cooldown');
 for(const lane of state.lanes){
   const launches=lane.log.filter(v=>v.kind==='launch');
   for(let i=1;i<launches.length;i++)A.assert(launches[i].time-launches[i-1].time>=1-1e-8,'one lane fired before its own cooldown');
 }
 return {count:state.count,initialPierceFixture:0,nearHits:nearHits.length,farHits:farHits.length,oppositeCurveOffsets:offsets,
   lanes:state.lanes.map(v=>({index:v.index,launches:v.launches,catches:v.catches,hits:v.hits,log:v.log}))};
}"""

QUANTITY_GROW_AND_RETIRE = r"""() => {
 const A=KBoom,p=A.p;A.prepare();p.quantityPicks=p.quantityBonus=4;
 const e=A.spawn(200,0),hits=A.watch(e);p.target=e;A.step(.001,true);A.advance(.02,true);
 const raw=A.K.stateFor(p).boomerang.lanes,saved=raw.map(lane=>({lane,projectile:lane.projectile,castId:lane.projectile.castId,readyAt:lane.readyAt}));
 p.quantityPicks=p.quantityBonus=8;A.step(.001,true);let state=A.state();
 A.assert(state.count===5&&state.projectiles.length===5,'new quantity lanes were not immediately ready');
 for(const item of saved){
   const lane=A.K.stateFor(p).boomerang.lanes[item.lane.index];
   A.assert(lane===item.lane&&lane.projectile===item.projectile&&lane.projectile.castId===item.castId,'quantity growth replaced an existing lane or its flight');
   A.near(lane.readyAt,item.readyAt,'quantity growth reset an existing lane cooldown');
 }
 A.assert(state.lanes.slice(2).every(lane=>lane.launches===1&&lane.readyAt>saved[0].readyAt+.015),'new lanes shared an older lane launch clock');
 // This case isolates quantity retirement before cooldown expires.
 for(const q of state.projectiles)q.remainingPierce=0;
 A.until(()=>A.state().hits===5);state=A.state();
 A.assert(hits.length===5&&hits.every(h=>h.owner&&h.id===A.id),'simultaneous bones did not each hit the same enemy once');
 A.assert(e.maxHp-e.hp===5*102,'same-target quantity damage was split or duplicated');
 const inFlight=state.projectiles.map(q=>q.castId),beforeLaunches=state.launches;
 A.assert(inFlight.length===5,'retirement fixture lost a throw before reduction');
 p.quantityPicks=p.quantityBonus=0;A.step(.001,true);state=A.state();
 A.assert(state.count===1&&state.projectiles.length===5,'quantity decrease deleted bones that had not reached the hand');
 A.assert(state.projectiles.every(q=>inFlight.includes(q.castId)),'quantity decrease replaced a returning bone');
 A.until(()=>A.state().catches===5);state=A.state();
 A.assert(state.projectiles.length===0&&state.lanes.length===1&&state.launches===beforeLaunches,'surplus bones relaunched instead of retiring after catch');
 A.until(()=>A.state().lanes[0].launches===2);state=A.state();
 A.assert(state.count===1&&state.projectiles.length===1&&state.launches===beforeLaunches+1,'reduced count did not retain exactly the original lane');
 A.assert(A.K.stateFor(p).boomerang.lanes[0]===saved[0].lane,'retirement recreated the remaining lane');
 return {grownTo:5,initialPierceFixture:0,sameTargetHits:hits.length,firstVolleyDamage:5*102,retired:4,
   retainedLane:state.lanes[0].index,totalLaunches:state.launches,totalCatches:state.catches};
}"""

QUANTITY_CAP = r"""() => {
 const A=KBoom,p=A.p,defaults=[];
 for(let rank=1;rank<=5;rank++){
   A.start(200,rank);A.assert(A.state().count===rank&&A.state().projectiles.length===rank,'rank did not add one base bone per level');defaults.push({rank,count:A.state().count});
 }
 const m=A.prepare(5);p.quantityPicks=p.quantityBonus=30;p.target=A.spawn(200,0);A.step(.001,true);
 const state=A.state();A.assert(G.Quantity.count(p,m.count)>16,'rank-five cap fixture did not exceed sixteen bones');
 A.assert(state.count===16&&state.lanes.length===16&&state.projectiles.length===16,'quantity cap is not sixteen simultaneous bones');
 A.assert(new Set(state.projectiles.map(q=>q.castId)).size===16,'quantity cap lanes reused flying projectiles');
 A.advance(.04,true);A.assert(A.state().projectiles.length===16&&A.state().launches===16,'capped lanes duplicated during flight');
 return {defaults,requested:G.Quantity.count(p,m.count),cap:state.count,launched:state.launches};
}"""

RANK_LEVEL_UP = r"""() => {
 const A=KBoom,p=A.p,{m}=A.start(400);A.advance(.02,true);const stages=[{rank:1,count:A.state().count}];
 const levelUp=G.Moves.levelUp;let nativeCalls=0;
 G.Moves.levelUp=function(...args){nativeCalls++;return levelUp.apply(this,args)};
 try{
   for(let rank=2;rank<=5;rank++){
     const before=A.K.stateFor(p).boomerang.lanes.map(lane=>({lane,projectile:lane.projectile,readyAt:lane.readyAt,damage:lane.projectile.move.dmg,remainingPierce:lane.projectile.remainingPierce}));
     const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+A.id);
     A.assert(card&&/數量\s*\+1/.test(card.desc),'native upgrade card omitted quantity +1 at rank '+rank);
     A.assert(/穿透\s*\+1/.test(card.desc),'native upgrade card omitted piercing +1 at rank '+rank);
     A.assert(card.apply(p)!==false,'native upgrade card failed');
     A.assert(m.lvl===rank&&m.count===rank&&m.pierce===rank-1,'native levelUp failed to add one base bone and piercing charge');
     A.step(.001,true);const state=A.state(),raw=A.K.stateFor(p).boomerang.lanes;
     A.assert(state.count===rank&&state.projectiles.length===rank,'new rank bone did not immediately join existing flights');
     for(const saved of before){
       const lane=raw[saved.lane.index];
       A.assert(lane===saved.lane&&lane.projectile===saved.projectile,'rank upgrade recreated a previous lane or flying bone');
       A.near(lane.readyAt,saved.readyAt,'rank upgrade reset previous lane cooldown');
       A.near(lane.projectile.move.dmg,saved.damage,'rank upgrade mutated an already launched damage snapshot');
       A.near(lane.projectile.remainingPierce,saved.remainingPierce,'rank upgrade changed an already launched piercing budget');
     }
     A.assert(state.lanes.at(-1).launches===1&&state.lanes.at(-1).projectile,'newly unlocked rank lane waited on an older cooldown');
     A.near(state.lanes.at(-1).projectile.remainingPierce,rank-1,'new rank lane did not receive the upgraded piercing budget');
     stages.push({rank,count:state.count,pierce:m.pierce,text:card.desc,newLaneReadyAt:state.lanes.at(-1).readyAt});
   }
   A.assert(nativeCalls===4,'upgrade cards bypassed the native levelUp path');
 }finally{G.Moves.levelUp=levelUp}
 A.assert(!G.Moves.levelUp(m)&&m.count===5,'max-rank upgrade added an unearned sixth base bone');
 return {nativeCalls,stages};
}"""

RANK_QUANTITY_STACK = r"""() => {
 const A=KBoom,p=A.p,m=A.prepare(3);p.quantityPicks=p.quantityBonus=4;p.target=A.spawn(400,0);A.step(.001,true);
 A.assert(m.count===3&&A.state().count===7&&A.state().projectiles.length===7,'rank-three base count was not multiplied by quantity cards');
 A.assert(A.state().projectiles.every(q=>q.pierce===6&&q.remainingPierce===6),'rank-three piercing did not add four quantity-card charges');
 const stages=[{rank:3,base:m.count,count:A.state().count}];
 for(const [rank,count] of [[4,9],[5,12]]){
   const saved=A.K.stateFor(p).boomerang.lanes.map(lane=>({lane,projectile:lane.projectile,readyAt:lane.readyAt,remainingPierce:lane.projectile.remainingPierce}));
   A.assert(G.Moves.levelUp(m),'native stacked rank upgrade failed');A.step(.001,true);
   const state=A.state(),raw=A.K.stateFor(p).boomerang.lanes;
   A.assert(m.lvl===rank&&m.count===rank&&state.count===count&&state.projectiles.length===count,'rank/quantity stacking order was incorrect');
   for(const item of saved){
     A.assert(raw[item.lane.index]===item.lane&&raw[item.lane.index].projectile===item.projectile,'stacked rank increase replaced an existing flight');
     A.near(item.lane.readyAt,item.readyAt,'stacked rank increase reset previous lane cooldown');
     A.near(item.lane.projectile.remainingPierce,item.remainingPierce,'stacked rank increase reset previous piercing budget');
   }
   A.assert(state.lanes.slice(saved.length).every(lane=>lane.launches===1&&lane.projectile),'additional stacked lanes did not launch immediately');
   A.assert(state.lanes.slice(saved.length).every(lane=>lane.projectile.remainingPierce===rank-1+4),'new stacked lanes missed rank/card piercing charges');
   stages.push({rank,base:m.count,count:state.count,newLanePierce:rank-1+4,added:count-saved.length});
 }
 return {quantityCards:4,formula:'floor(base count * 1.25^4)',stages};
}"""

PIERCE_LIMITS = r"""() => {
 const A=KBoom,out=[];
 for(let rank=1;rank<=5;rank++){
   const {m,anchor,hits:anchorHits,b}=A.single(rank),order=[];
   const targets=[5,10,15,20,25,30].map(index=>A.spawn(b.curve[index].x,b.curve[index].y)),logs=targets.map(A.watch);
   targets.forEach((e,index)=>{const hurt=e.hurt;e.hurt=function(...args){order.push(index);return hurt.apply(this,args)}});
   A.near(b.pierce,rank-1,'launch-time rank piercing snapshot');
   A.until(()=>A.state().projectile?.phase==='return');
   A.assert(order.length===rank&&order.every((value,index)=>value===index),'piercing hit order or different-enemy limit rank '+rank+' '+JSON.stringify(order));
   A.assert(logs.every((log,index)=>log.length===(index<rank?1:0))&&anchorHits.length===0,'piercing repeated a target or exceeded its allowance rank '+rank);
   const raw=[64,76.8,89.6,108.8,128][rank-1]*1.6;
   for(const log of logs.slice(0,rank)){A.near(log[0].raw,raw,'piercing divided full per-enemy damage');A.assert(log[0].loss===Math.round(raw)&&log[0].owner&&log[0].id===A.id,'piercing bypassed native hit ownership/damage')}
   A.assert(b.remainingPierce===0&&b.phaseHits.get(0).size===rank,'allowance did not deplete per distinct enemy');
   A.until(()=>A.state().catches===1);
   A.assert(order.length===rank&&logs.every((log,index)=>log.length===(index<rank?1:0)),'return through pierced enemies repeated damage');
   out.push({rank,isolatedCount:m.count,pierce:b.pierce,targetsHit:order,remaining:b.remainingPierce,rawPerTarget:raw});
 }
 return out;
}"""

PIERCE_OVERLAP_AND_QUANTITY = r"""() => {
 const A=KBoom,p=A.p,{b}=A.single(5),point=b.curve[10],large=A.spawn(point.x,point.y),largeHits=A.watch(large);
 large.r=60;G.EnemyMgr.rebuildGrid();A.until(()=>largeHits.length===1);A.advance(.06,true);
 const overlap=A.state().projectile;
 A.assert(overlap?.phase==='out'&&Math.hypot(overlap.x-large.x,overlap.y-large.y)<=large.r+7,'overlap fixture did not remain inside one victim');
 A.assert(largeHits.length===1&&overlap.remainingPierce===3,'continued overlap consumed extra hit/piercing charges');
 const overlapResult={hits:largeHits.length,remaining:overlap.remainingPierce,stillInside:true};
 A.prepare();p.quantityPicks=p.quantityBonus=4;const anchor=A.spawn(400,0),anchorHits=A.watch(anchor);p.target=anchor;A.step(.001,true);
 let state=A.state();A.assert(state.count===2&&state.projectiles.every(q=>q.pierce===4&&q.remainingPierce===4),'four quantity cards did not add four independent launch piercing charges');
 const shots=[...state.projectiles],groups=shots.map(q=>[5,10,15,20,25,30].map(index=>A.spawn(q.curve[index].x,q.curve[index].y))),logs=groups.map(group=>group.map(A.watch));
 A.until(()=>A.state().projectiles.length===2&&A.state().projectiles.every(q=>q.phase==='return'));
 state=A.state();A.assert(state.hits===10&&state.lanes.every(lane=>lane.hits===5),'quantity piercing did not allow five separate victims per bone');
 shots.forEach((q,lane)=>{
   A.assert(q.remainingPierce===0&&q.phaseHits.get(0).size===5,'one bone consumed another bone piercing state');
   A.assert(groups[lane].slice(0,5).every(e=>q.phaseHits.get(0).has(e)),'quantity bones lost their separate victim ledgers');
   A.assert(logs[lane].every((log,index)=>log.length===(index<5?1:0)),'quantity bone repeated a victim or pierced one too many');
 });
 A.assert(anchorHits.length===0,'quantity piercing exceeded its launch allowance');A.until(()=>A.state().catches===2);
 A.assert(logs.flat().reduce((sum,log)=>sum+log.length,0)===10,'quantity return paths applied extra hits');
 return {overlap:overlapResult,quantityCards:4,count:2,piercePerBone:4,hitsPerBone:5,totalHits:10};
}"""

PIERCE_UNUSED_AND_OBSTACLES = r"""() => {
 const A=KBoom,{b,hits}=A.single(5,200);A.until(()=>hits.length===1);
 A.assert(b.phase==='out'&&b.remainingPierce===3,'unused charges did not continue after the first enemy');
 A.until(()=>A.state().projectile?.phase==='return');
 A.near(b.distance,800,'unused piercing did not reach authored range before returning');
 A.assert(b.remainingPierce===3&&hits.length===1,'unused-range flight repeated the first victim');
 A.until(()=>A.state().catches===1);A.assert(hits.length===1,'unused-charge return hit its earlier victim');
 const rangeResult={distance:b.distance,unused:b.remainingPierce,hits:hits.length};
 const wall=A.single(5);G.World.isWall=(x,y)=>x>=100;A.until(()=>A.state().projectile?.phase==='return');
 A.assert(wall.b.remainingPierce===4&&wall.b.distance<800&&wall.hits.length===0,'wall did not return a bone with unused piercing');
 const blocked=A.single(5);A.advance(.10,true);const q=blocked.b,speed=Math.hypot(q.vx,q.vy);
 const prop={x:q.x+q.vx/speed*12,y:q.y+q.vy/speed*12,r:12,type:'chest',solid:true,destructible:true,hp:10000,tx:3,ty:0};
 G.World.projectileBlock=(x,y,r)=>Math.hypot(x-prop.x,y-prop.y)<=prop.r+r?prop:false;
 A.until(()=>A.state().projectile?.phase==='return');
 A.assert(blocked.b.remainingPierce===4&&blocked.b.distance<800&&blocked.hits.length===0,'prop did not stop a bone with unused piercing');
 return {range:rangeResult,wallReturnedWith:wall.b.remainingPierce,propReturnedWith:blocked.b.remainingPierce,propLoss:10000-prop.hp};
}"""

MULTI_CLONE_AND_UNLEARN = r"""() => {
 const A=KBoom,p=A.p;A.prepare();p.quantityPicks=p.quantityBonus=4;p.target=A.spawn(220,0);
 const clone=G.SelfClones.summon(p);A.assert(clone,'native quantity clone missing');clone.target=p.target;
 A.step(.001,true);A.advance(.02,true);
 let main=A.state(),copy=A.state(clone);
 A.assert(main.count===2&&copy.count===2&&main.projectiles.length===2&&copy.projectiles.length===2,'native clone did not inherit quantity while keeping independent flights');
 A.assert(new Set([...main.projectiles,...copy.projectiles].map(q=>q.castId)).size===4,'clone shared projectile identities with parent');
 G.Combat.clearFields(clone);A.assert(!A.state(clone)&&A.state().projectiles.length===2,'clone cleanup removed parent flight lanes');
 p.moves=p.moves.filter(m=>m.id!==A.id);p.arrange();A.step(.01);
 A.assert(!A.state(),'unlearned boomerang retained a public flight state');
 A.assert(!(A.K.stateFor(p)?.boomerang.lanes||[]).some(lane=>lane.projectile),'unlearning left invisible additional bones in flight');
 return {cloneCount:2,totalIndependentFlights:4,cloneCleanup:true,allUnlearnedFlightsCleared:true};
}"""

LATE_CATCH = r"""() => {
 const A=KBoom,p=A.p;
 A.start(560);A.until(()=>A.state().catches===1);
 const natural=A.state().log,naturalCatch=natural.findIndex(v=>v.kind==='catch');
 A.assert(natural[naturalCatch].time-natural[0].time>1,'extended stationary flight did not exceed cooldown');
 A.assert(natural[naturalCatch+1]?.kind==='launch','long-range catch failed to relaunch');
 A.near(natural[naturalCatch+1].time,natural[naturalCatch].time,'long-range catch restarted cooldown');
 const {e,hits}=A.start(100);A.until(()=>hits.length>0);e.dead=true;
 const flight=A.state().projectile.castId;p.x+=1400;const target=A.spawn(p.x+200,p.y);p.target=target;
 let expiredWhileFlying=false,steps=0;
 while(A.state().catches===0&&steps++<300){
   const state=A.state();
   A.assert(state.projectile?.castId===flight&&state.projectile.phase==='return','long return was replaced before actual catch');
   if(state.cooldown===0)expiredWhileFlying=true;
   A.assert(state.launches===1,'ready cooldown allowed another throw while old bone was still flying');
   A.step(.01,true);
 }
 const state=A.state(),log=state.log,catchIndex=log.findIndex(v=>v.kind==='catch');
 A.assert(expiredWhileFlying&&state.catches===1&&state.launches===2,'late real catch did not immediately relaunch');
 A.assert(state.projectile?.phase==='out'&&state.projectile.castId!==flight,'catch reused the old returning projectile');
 A.assert(catchIndex>=0&&log[catchIndex+1]?.kind==='launch','late catch omitted same-update relaunch event');
 A.near(log[catchIndex+1].time,log[catchIndex].time,'late catch added an unnecessary cooldown');
 A.assert(log[catchIndex].time-log[0].time>1,'late-catch fixture did not exceed base cooldown');
 return {naturalLongRange:natural,steps,expiredWhileFlying,log};
}"""

RANGE_AND_OBSTACLES = r"""() => {
 const A=KBoom,p=A.p,out=[];
 for(const rank of [1,5]){
   const {m,e}=A.start(200,rank),initial=A.state().projectile,sx=initial.x,sy=initial.y;
   e.dead=true;p.target=null;let walked=initial.distance,previous={x:sx,y:sy},outDistance=0;
   A.until(()=>{
     const q=A.state().projectile;if(!q)return false;
     walked+=Math.hypot(q.x-previous.x,q.y-previous.y);previous={x:q.x,y:q.y};outDistance=q.distance;
     return q.phase==='return';
   });
   A.near(outDistance,m.range,'missed curve did not return at authored traveled distance');
   A.assert(walked>=m.range-8&&walked<=m.range+8,'sampled curve travel disagrees with range budget');
   const chord=Math.hypot(previous.x-sx,previous.y-sy);
   A.assert(chord<outDistance-5,'range fixture did not distinguish curved travel from endpoint chord');
   A.until(()=>A.state().catches===rank);
   A.assert(A.state().projectiles.length===0&&A.state().launches===rank,'targetless ranked catches relaunched into empty space');
   out.push({rank,count:rank,range:m.range,traveled:outDistance,sampledTravel:walked,chord,caught:true});
 }
 A.start(200);G.World.isWall=(x,y)=>x>=100;
 A.until(()=>A.state().projectile?.phase==='return');const wallTurn={...A.state().projectile};
 A.assert(wallTurn.x<=106&&A.state().hits===0,'wall did not stop outward throw');
 A.until(()=>A.state().catches>=1);out.push({wallTurn:{x:wallTurn.x,y:wallTurn.y},caughtThroughReturnPath:true});
 const propFixture=A.start(200);A.advance(.10,true);const q=A.state().projectile,speed=Math.hypot(q.vx,q.vy);
 const prop={x:q.x+q.vx/speed*12,y:q.y+q.vy/speed*12,r:12,type:'chest',solid:true,destructible:true,hp:10000,tx:3,ty:0};
 G.World.projectileBlock=(x,y,r)=>Math.hypot(x-prop.x,y-prop.y)<=prop.r+r?prop:false;
 A.until(()=>A.state().projectile?.phase==='return');
 const turn=A.state().projectile;
 A.assert(Math.hypot(turn.x-prop.x,turn.y-prop.y)<=prop.r+11&&propFixture.hits.length===0,'solid prop on actual curve did not stop outward throw');
 out.push({propTurn:true,prop:{x:prop.x,y:prop.y},propLoss:10000-prop.hp});
 return out;
}"""

MOVING_CATCH = r"""() => {
 const A=KBoom,p=A.p,{e,hits}=A.start(100);A.until(()=>hits.length>0);e.dead=true;p.target=null;
 p.x+=120;p.y+=150;let steps=0;
 while(A.state().catches===0&&steps++<200){
   p.x+=1.2;p.y+=.3;const before=A.state(),q={...before.projectile},hand=before.hand;
   A.assert(q.phase==='return','returning throw changed phase without catching');
   const dx=hand.x-q.x,dy=hand.y-q.y,d=Math.hypot(dx,dy);A.step(.01,true);const after=A.state();
   if(after.catches){
     A.assert(d<=900*.01+8+.01,'throw caught without reaching moving hand');break;
   }
   const next=after.projectile,mx=next.x-q.x,my=next.y-q.y;
   A.assert(mx*dx+my*dy>0,'return moved away from the current hand');
   A.assert(Math.abs(mx*dy-my*dx)<1e-5*Math.max(1,d),'return spiraled instead of moving straight to hand');
   A.near(Math.hypot(mx,my),9,'return speed is not 900px/s');
 }
 A.assert(A.state().catches===1&&!A.state().projectile&&steps<200,'moving owner never truly caught the throw');
 return {steps,owner:{x:p.x,y:p.y},state:A.state()};
}"""

BODY_AND_GUARD = r"""() => {
 const A=KBoom,p=A.p;A.prepare();A.assert(p.addMove('naruto-kimimaro-bracken')&&p.addMove('naruto-kimimaro-bone-guard'),'cannot learn simultaneous skills');
 p.target=A.spawn(100,0);KAcceptance.cast('naruto-kimimaro-bracken');const body=A.action();
 A.assert(body?.kind==='bracken','native forest not started');A.advance(.1,true);
 const shot=G.Projectiles.spawn({x:p.x+100,y:p.y,vx:-600,vy:0,friendly:false,r:5,dmg:30,mtype:'normal',life:4});
 const hp=p.hp;A.advance(.3,true);
 A.assert(A.action()===body&&A.action().age>=.4,'throw replaced or interrupted native body action');
 A.assert(A.state().launches>=1&&A.state().hits>=1,'body action suppressed independent boomerang');
 A.assert(!G.Projectiles.all().includes(shot)&&p.hp===hp&&A.K.boneGuardState(p).blocks>=1,'boomerang interfered with bone defense');
 return {body:body.kind,bodyAge:body.age,launches:A.state().launches,throwHits:A.state().hits,guardBlocks:A.K.boneGuardState(p).blocks};
}"""

CLONE_AND_LIFECYCLE = r"""() => {
 const A=KBoom,p=A.p;A.prepare();p.target=A.spawn(220,0);
 const clone=G.SelfClones.summon(p);A.assert(clone,'native self clone missing');clone.target=p.target;
 A.step(.001,true);A.advance(.03,true);
 const main=A.state(),copy=A.state(clone);
 A.assert(main?.projectile&&copy?.projectile&&main.projectile!==copy.projectile,'clone shares or omits its independent boomerang');
 A.assert(main.launches===1&&copy.launches===1,'new owner duplicated boomerang');
 const paused=JSON.stringify({main:A.state(),copy:A.state(clone)});A.pause();G.Combat.updateFields(.3);
 A.assert(JSON.stringify({main:A.state(),copy:A.state(clone)})===paused,'pause advanced independent throw');
 G.Combat.clearFields(p);A.assert(!A.state()&&!A.state(clone),'owner cleanup leaked clone or own flying throw');
 A.start(100);const originalWorld=G.World;G.World={...originalWorld};
 try{A.K.update(0);A.assert(!A.state(),'world switch retained flying throw')}finally{G.World=originalWorld}
 A.start(100);p.moves=p.moves.filter(m=>m.id!==A.id);p.arrange();A.step(.01);
 A.assert(!A.state()?.projectile,'removed learned skill retained a throw');
 A.start(100);p.dead=true;A.K.update(0);A.assert(!A.state(),'death retained flying throw');p.dead=false;
 for(const method of ['quit','toUI']){
   A.start(100);A.resume();if(method==='quit')G.Game.quit();else G.Game.toUI('menu');
   A.assert(!A.state(),'terminal state retained throw '+method);G.Game.startRun();A.pause();
 }
 return {cloneIndependent:true,paused:true,clear:true,world:true,unlearn:true,death:true,terminal:true};
}"""


def main():
    game.OUT.mkdir(parents=True,exist_ok=True)
    report={'url':game.URL,'errors':[],'failedRequests':[],'failures':[],'viewports':{},'sourceHashes':game.runtime_hashes()}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=game.CHROME,headless=True)
        for label,viewport,mobile in [('desktop',{'width':1280,'height':900},False),('mobile',{'width':390,'height':844},True)]:
            context=browser.new_context(viewport=viewport,is_mobile=mobile,has_touch=mobile,service_workers='block')
            page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
            page.on('response',lambda r:report['failedRequests'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            result=report['viewports'][label]={}
            try:
                frame=game.boot(page,label);frame.evaluate(HELPERS)
                for name,check in [('progression',PROGRESSION),('hitAndReturn',HIT_AND_RETURN),('firstTargetAndCurve',FIRST_TARGET_AND_CURVE),
                  ('cadence',CADENCE),('cooldownModifiers',COOLDOWN_MODIFIERS),('multiCadence',MULTI_CADENCE),
                  ('quantityGrowAndRetire',QUANTITY_GROW_AND_RETIRE),('quantityCap',QUANTITY_CAP),('rankLevelUp',RANK_LEVEL_UP),
                  ('rankQuantityStack',RANK_QUANTITY_STACK),('pierceLimits',PIERCE_LIMITS),('pierceOverlapAndQuantity',PIERCE_OVERLAP_AND_QUANTITY),
                  ('pierceUnusedAndObstacles',PIERCE_UNUSED_AND_OBSTACLES),('multiCloneAndUnlearn',MULTI_CLONE_AND_UNLEARN),
                  ('lateCatch',LATE_CATCH),('rangeAndObstacles',RANGE_AND_OBSTACLES),('movingCatch',MOVING_CATCH),('bodyAndGuard',BODY_AND_GUARD),('cloneAndLifecycle',CLONE_AND_LIFECYCLE)]:
                    print(label,name,flush=True)
                    try:result[name]=frame.evaluate(check)
                    except Exception as error:report['failures'].append(label+':'+name+': '+str(error))
            except Exception as error:report['failures'].append(label+':boot: '+str(error))
            finally:context.close()
        browser.close()
    report['sourceHashesAfter']=game.runtime_hashes()
    if report['sourceHashesAfter']!=report['sourceHashes']:report['failures'].append('runtime changed during acceptance')
    report['ok']=not(report['errors'] or report['failedRequests'] or report['failures'])
    path=game.OUT/'report-boomerang.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'report':str(path)},ensure_ascii=True))
    if not report['ok']:raise SystemExit(1)


if __name__=='__main__':main()
