"""Controlled real-pipeline wind-chain regression; natural play is separate."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_temari as native

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.omx/state/temari-fun/mechanics'
SETUP=r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.chainLedger=[];
 // A controlled legal five-card Lv6 loadout; levels are fixtures, not natural XP.
 for(const [level,key] of [[2,'stat:atk'],[3,'new:naruto-temari-three-stars'],[4,'stat:atk'],[5,'stat:atk'],[6,'new:naruto-temari-great-scythe']]){
   p.level=level;const card=G.LevelUp.offer(p,100).find(c=>c.key===key);
   A.assert(card&&card.apply(p)!==false,'legal card absent '+key);A.chainLedger.push({level,key});
 }
 A.chainReset=(Q=0,L=1,H=1)=>{A.reset();p.hp=p.maxHp;p.dead=false;p.frozen=false;
   A.mastery(L);A.rank('naruto-temari',1);A.rank('naruto-temari-great-scythe',H);
   p.quantityPicks=p.quantityBonus=Q;p.level=6;for(const m of p.moves)m.t=999;};
 A.chainStep=(dt=.005,moving=false)=>{if(moving){A.resume();try{
   for(const e of G.EnemyMgr.all())if(!e.dead)e.update(dt,p);G.EnemyMgr.rebuildGrid();
 }finally{A.pause()}}A.advance(dt);};
 A.chainFinish=(seconds,moving=false,dt=.005)=>{for(let time=0;time<seconds-1e-8;time+=dt)A.chainStep(Math.min(dt,seconds-time),moving);};
 A.chainSeed=(target,beforeThird=null)=>{p.target=target;for(let i=0;i<3;i++){
   if(i===2)beforeThird?.();
   A.resume();try{G.Combat.tick(i?1.61:.001,p,0)}finally{A.pause()}A.chainFinish(1.5);
 }return T.stateFor(p)?.latest;};
 A.chainHeavy=target=>{p.target=target;const move=p.moves.find(m=>m.digiMode==='temari-great-scythe');
   p.setActive(p.slots.findIndex(g=>g.includes(move)));move.t=0;
   A.resume();try{G.Combat.tick(.001,p,0)}finally{A.pause()}
   const cast=T.stateFor(p)?.latest;A.assert(cast?.kind==='heavy','native heavy did not start');return cast;};
 A.chainHits=hits=>hits.filter(h=>h.id==='naruto-temari-wind-chain');
}"""

EARLY=r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out={ledger:A.chainLedger};A.chainReset();
 const source=A.spawn(140,0),sourceHits=A.watch(source);source.hp=source.maxHp=1e6;
 A.chainSeed(source,()=>{source.hp=1;});const knots=(T.windKnots||[]).map(k=>({id:k.seedId,x:k.x,y:k.y,age:k.age}));
 // A valid source hit may kill: its ground resource survives for the next group.
 A.assert(source.dead,'sacrificial ordinary survived valid lethal contact');
 const idleHeavy=p.moves.find(m=>m.digiMode==='temari-great-scythe');
 A.assert(!T.canCast(p,idleHeavy),'corpse knot bypassed live-target gate');
 const targets=[[140,0],[200,70],[220,-70],[140,450]].map(([x,y])=>A.spawn(x,y));
 targets.forEach(e=>{e.spd=35;e.hp=e.maxHp=1e6;});const hits=targets.map(A.watch);
 const heavy=p.moves.find(m=>m.digiMode==='temari-great-scythe');heavy.dealt=0;
 const observed=[],old=T.onWindChainHit;T.onWindChainHit=info=>{old?.(info);if(!info.ghost)observed.push(info)};
 try{A.chainHeavy(targets[0]);A.chainFinish(1.4,true);}finally{T.onWindChainHit=old}
 const count=hits.map(h=>A.chainHits(h).length),direct=hits[0].filter(h=>h.id===heavy.id);
 A.assert(direct.length===1,'base heavy hit changed');
 out.knots=knots;out.derived=count;out.direct=direct.length;out.observed=observed.length;
 out.nativeDealt=heavy.dealt;out.sourceHits=sourceHits.length;
 if(!T.windChainProfile)return out;
 A.assert(knots.length===1,'empowered source failed to seed exactly once');
 A.assert(count[0]===3&&count[1]>0&&count[2]>0&&count[3]===0,'moving ordinary group geometry '+count);
 A.assert(targets[0].x>180,'ordinary heavy push disappeared');
 A.assert(observed.length===count.reduce((a,b)=>a+b,0),'observer did not match real hits');
 const displayed=hits.flat().reduce((n,h)=>n+Math.round(h.raw),0);
 A.assert(heavy.damageIds?.includes('naruto-temari-wind-chain'),'native damage alias absent');
 A.assert(heavy.dealt===displayed,'native heavy dealt omitted derived hits '+heavy.dealt+'/'+displayed);
 return out;
}"""

GROWTH=r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];
 A.assert(T.windChainProfile,'wind-chain API absent');
 for(const Q of [0,1,2,3,5]){
   A.chainReset();for(let q=0;q<Q;q++){
     const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:quantity');
     A.assert(card&&card.apply(p)!==false,'real quantity card absent');
   }
   const e=A.spawn(140,0,'boss'),h=A.watch(e);A.chainSeed(e);
   const profile=T.windChainProfile(p),knot=T.windKnots[0];A.assert(knot,'growth knot absent');
   A.chainHeavy(e);A.chainFinish(1.5);const chain=A.chainHits(h);
   A.assert(chain.length===profile.cuts,'growth did not change actual cuts '+Q+'/'+chain.length);
   const expectedCuts=Math.min(8,3+Math.min(Q,3));
   A.assert(profile.cuts===expectedCuts&&profile.seedLimit===Math.min(8,2+Math.min(Q,4)),'profile/card mismatch');
   A.assert(profile.radius===Math.min(440,138+4*Q+64+8*Q),'push-aware radius mismatch');
   out.push({Q,cuts:chain.length,radius:profile.radius,seeds:profile.seedLimit,raw:chain[0].raw});
 }
 for(const H of [1,3,5])for(const L of [0,1,5]){
   A.chainReset(20,L,H);const c=T.windChainProfile(p);
   A.assert(c.seedLimit<=8&&c.cuts<=8&&c.radius<=440,'profile exceeded finite bounds');
 }
 return out;
}"""

MISS_TTL=r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];
 for(const mode of ['miss','wall','expired']){
   A.chainReset();const source=A.spawn(140,0,'boss');A.chainSeed(source);source.dead=true;
   const e=A.spawn(mode==='miss'?-140:220,0,'boss'),h=A.watch(e),W=G.World,oldBlock=W.projectileBlock;
   try{
     if(mode==='wall')W.projectileBlock=(x,y)=>x>60&&x<85?{destructible:false}:false;
     // The wall is introduced only after a valid start so it tests the actual
     // released front, not merely canCast's target gate.
     if(mode==='wall'){W.projectileBlock=oldBlock;A.chainHeavy(e);W.projectileBlock=(x,y)=>x>60&&x<85?{destructible:false}:false;}
     else{if(mode==='expired')A.chainFinish(6);A.chainHeavy(e);}
     A.chainFinish(1.5);A.assert(A.chainHits(h).length===0,'non-crossed knot detonated '+mode);
     out.push(mode);
   }finally{W.projectileBlock=oldBlock}
 }
 A.chainReset();const e=A.spawn(140,0,'boss');A.chainSeed(e);const knot=T.windKnots[0],age=knot.age;
 T.update(.5);A.near(knot.age,age,'paused TTL advanced');
 p.frozen=true;A.chainFinish(.2);p.frozen=false;A.assert(knot.age>age,'released resource freeze clock changed');
 A.chainFinish(6-knot.age-.001);A.assert(T.windKnots.includes(knot),'knot expired early');
 A.chainStep(.002);A.assert(!T.windKnots.includes(knot),'knot exceeded TTL');
 return {rejected:out,ttl:true,pause:true};
}"""

CANCEL=r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];
 for(const phase of ['hurt','onDealt'])for(const reason of ['clear','death','world','unlearn']){
   A.chainReset();const seed=A.spawn(140,0,'boss');A.chainSeed(seed);seed.dead=true;
   const first=A.spawn(140,0),second=A.spawn(141,2),one=A.watch(first),two=A.watch(second);
   const oldHurt=first.hurt,oldDealt=p.onDealt,moves=p.moves,world=G.World;let derived=false;
   const cancel=()=>{if(reason==='clear')T.clear(p);else if(reason==='death'){p.hp=0;p.dead=true;}
     else if(reason==='world')G.World=Object.create(world);else p.moves=p.moves.filter(m=>m.digiMode!=='temari-great-scythe');};
   first.hurt=function(...args){derived=args[7]==='naruto-temari-wind-chain';const r=oldHurt.apply(this,args);
     if(derived&&phase==='hurt')cancel();return r;};
   if(phase==='onDealt')p.onDealt=function(...args){if(derived)cancel();else return oldDealt?.apply(this,args)};
   try{
     A.chainHeavy(first);A.chainFinish(1.5);
     A.assert(A.chainHits(one).length===1&&A.chainHits(two).length===0,'reaction callback leaked damage '+phase+'/'+reason);
     A.assert(!T.windKnots.some(a=>a.owner===p)&&!T.windBursts.some(a=>a.owner===p),'reaction survived invalidation');
     if(reason==='clear')A.assert(!T.stateFor(p)||T.stateFor(p).windHits===0,'reaction recreated cleared statistics');
     out.push({phase,reason});
   }finally{p.moves=moves;G.World=world;p.onDealt=oldDealt;p.hp=p.maxHp;p.dead=false;T.clear();}
 }
 return out;
}"""

SOURCES=r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out={};A.chainReset();
 const moves=p.moves;p.moves=moves.filter(m=>m.digiMode!=='temari-great-scythe');
 const early=A.spawn(140,0,'boss');try{A.chainSeed(early);
   A.assert(!T.windChainProfile(p).enabled&&!T.windKnots.length,'unusable pre-heavy resource appeared');
 }finally{p.moves=moves}out.beforeHeavy=true;
 A.chainReset();const spread=[[140,0],[140,20],[170,60]].map(([x,y])=>A.spawn(x,y,'boss'));
 A.chainSeed(spread[0]);A.assert(T.windKnots.length===2,'overlap spent source budget');
 A.assert(Math.hypot(T.windKnots[0].x-T.windKnots[1].x,T.windKnots[0].y-T.windKnots[1].y)>=48,'overlapping seeds admitted');
 out.empoweredSeeds=T.windKnots.length;
 A.chainReset(5);p.level=12;const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:naruto-temari-typhoon');
 A.assert(card&&card.apply(p)!==false,'typhoon card absent');
 const targets=Array.from({length:8},(_,i)=>A.spawn(120*Math.cos(i*Math.PI/4),120*Math.sin(i*Math.PI/4),'boss'));
 p.target=targets[0];const m=p.moves.find(m=>m.digiMode==='temari-typhoon');p.setActive(p.slots.findIndex(g=>g.includes(m)));m.t=0;
 A.resume();try{G.Combat.tick(.001,p,0)}finally{A.pause()}
 const cast=T.casts.find(c=>c.owner===p&&c.kind==='typhoon');A.chainFinish(2.9);
 A.assert(cast?.windSeeded===6&&T.windKnots.length===6,'quantity streams flooded or omitted seed budget');
 out.typhoon={streams:cast.count,seeds:cast.windSeeded,knots:T.windKnots.length};
 return out;
}"""

CAP_GHOST=r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out={};A.chainReset();
 const remote={x:0,y:0,hp:100,dead:false};
 for(let id=1;id<=9;id++)A.assert(T.applyWindKnot(remote,{seedId:id,sourceCastId:1,x:id*60,y:0,age:0,ttl:6}),'ghost seed rejected');
 A.assert(T.windKnots.filter(a=>a.owner===remote).length===8&&!T.windKnots.some(a=>a.owner===remote&&a.seedId===1),'oldest replacement incorrect');
 A.assert(!T.applyWindKnot(remote,{seedId:1,sourceCastId:1,x:60,y:0,age:0,ttl:6}),'reordered oldest displaced new knot');
 T.clear(remote);A.chainReset();const seed=A.spawn(140,0,'boss');A.chainSeed(seed);seed.dead=true;
 const target=A.spawn(180,0,'boss'),hits=A.watch(target);A.chainHeavy(target);A.chainFinish(.39);
 for(let group=0;group<4;group++){
   const consumedIds=Array.from({length:8},(_,i)=>1000+group*8+i);
   const bursts=consumedIds.map((id,i)=>({id,x:1000+i*10,y:0,age:0,radius:202,cuts:8,interval:.1,travel:.08,damageType:'flying'}));
   A.assert(T.applyWindChain(p,{heavyCastId:900,activationId:100+group,consumedIds,bursts}),'pressure fixture failed');
 }
 A.chainFinish(.25);A.assert(!A.chainHits(hits).length&&T.windKnots.some(a=>a.owner===p&&!a.ghost),'full burst cap consumed knot or emitted partial damage');
 out.refusedAt32=true;T.clear();A.chainReset();
 const nextSeed=A.spawn(140,0,'boss');A.chainSeed(nextSeed);nextSeed.dead=true;
 const nextTarget=A.spawn(180,0,'boss');A.chainHeavy(nextTarget);A.chainFinish(.54);
 for(let group=0;group<4;group++){
   const consumedIds=Array.from({length:8},(_,i)=>2000+group*8+i);
   const bursts=consumedIds.map(id=>({id,x:1000,y:0,age:.89,radius:202,cuts:8,interval:.1,travel:.08,damageType:'flying'}));
   A.assert(T.applyWindChain(p,{heavyCastId:901,activationId:200+group,consumedIds,bursts}),'expiry pressure fixture failed');
 }
 A.chainStep(.02);A.assert(T.stateFor(p).windTriggered===1&&!T.windKnots.length,'expired bursts falsely occupied reaction cap');
 out.expiryFreesSlot=true;T.clear();A.chainReset();
 const ghost={x:0,y:0,hp:100,dead:false},e=A.spawn(100,0,'boss'),hp=e.hp;
 A.assert(T.applyWindKnot(ghost,{seedId:71,sourceCastId:1,x:100,y:0,age:0,ttl:6}),'ghost knot missing');
 const packet={heavyCastId:2,activationId:3,consumedIds:[71],bursts:[{id:72,x:100,y:0,age:0,radius:202,cuts:3,interval:.1,travel:.08,damageType:'flying'}]};
 const invalid={...packet,bursts:[{...packet.bursts[0],radius:441}]};
 A.assert(!T.applyWindChain(ghost,invalid,false)&&T.windKnots.some(a=>a.owner===ghost),'invalid whole packet mutated consumed state');
 A.assert(T.applyWindChain(ghost,packet),'valid ghost activation rejected');A.chainFinish(.5);
 A.assert(e.hp===hp&&!T.held(e)&&!T.pushFor(e)&&!T.orbitFor(e),'ghost reaction changed HP/control');
 A.assert(!T.windKnots.some(a=>a.owner===ghost)&&!T.windBursts.some(a=>a.owner===ghost),'ghost did not expire');
 A.assert(T.applyWindKnot(ghost,{seedId:73,sourceCastId:1,x:100,y:0,age:0,ttl:6}),'consumed-only seed missing');
 A.assert(T.applyWindChain(ghost,{...packet,activationId:4,consumedIds:[73]},false)&&!T.windKnots.some(a=>a.owner===ghost)&&!T.windBursts.some(a=>a.owner===ghost),'consumed-only presentation partially emitted');
 return {...out,ghostNoDamage:true,atomicValidation:true};
}"""

CAUSAL=r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];
 for(const coarse of [false,true]){
   A.chainReset();const e=A.spawn(140,0,'boss'),h=A.watch(e);p.target=e;
   for(let i=0;i<2;i++){A.resume();try{G.Combat.tick(i?1.61:.001,p,0)}finally{A.pause()}A.chainFinish(1.5);}
   const heavy=A.chainHeavy(e);A.chainFinish(.3);
   A.resume();try{G.Combat.tick(1.61,p,0)}finally{A.pause()}
   A.chainFinish(.11);if(coarse)A.chainStep(.5);else A.chainFinish(.5);
   A.assert(T.windKnots.length===1,'late empowered knot absent');
   A.assert(!heavy.windTriggered&&!A.chainHits(h).length,'front ignited a knot born behind its historical crossing');
   out.push({coarse,knotAge:T.windKnots[0].age,heavyTriggers:heavy.windTriggered||0});
 }
 return out;
}"""

CLONES=r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.chainReset();
 const e=A.spawn(140,0,'boss'),hits=A.watch(e);A.chainSeed(e);
 const ownKnot=T.windKnots[0],heavy=p.moves.find(m=>m.digiMode==='temari-great-scythe');
 p.setActive(p.slots.findIndex(g=>g.includes(heavy)));p.level=7;
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');A.assert(card&&card.apply(p)!==false,'clone card absent');
 const clone=G.SelfClones.actors()[0];clone.x=clone.y=0;clone.target=e;
 const tick=dt=>{p.frozen=false;clone.frozen=false;
   A.resume();try{G.Combat.tick(dt,clone,0)}finally{A.pause()}p.frozen=true;};
 try{
   for(const m of clone.moves)m.t=999;
   clone.moves.find(m=>m.id===heavy.id).t=0;tick(.001);A.chainFinish(.9);
   A.assert(T.windKnots.includes(ownKnot),'clone consumed parent knot');
   // Its first basic happened with the heavy. Two subsequent legal volleys
   // reach the clone's own third-round empowerment while new AI actions freeze.
   tick(1.61);A.chainFinish(1.5);tick(1.61);A.chainFinish(1.5);
   const knot=T.windKnots.find(a=>a.owner===clone);A.assert(knot&&knot!==ownKnot,'clone did not own independent seed');
   hits.length=0;tick(1.8);A.chainFinish(1.4);
   const chain=A.chainHits(hits).filter(h=>h.clone),expected=heavy.dmg*p.atk*.35*G.Types.mult('flying',e.types)*G.Weather.mult('flying');
   A.assert(chain.length===3,'clone reaction cut count '+chain.length);
   chain.forEach(h=>A.near(h.raw*3,expected,'clone reaction scaled more than once'));
   G.SelfClones.clear();A.chainStep(.01);
   A.assert(!T.windKnots.some(a=>a.owner===clone)&&!T.windBursts.some(a=>a.owner===clone),'removed clone retained reaction');
   return {ownerIsolation:true,cloneCuts:chain.length,ratio:1/3};
 }finally{p.frozen=false;}
}"""

CAP_CAUSAL=r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];
 for(const coarse of [false,true]){
   A.chainReset();const source=A.spawn(109.232,0,'boss');A.chainSeed(source);source.dead=true;
   const e=A.spawn(180,0,'boss'),heavy=A.chainHeavy(e);A.chainFinish(.39);
   for(let group=0;group<4;group++){
     const consumedIds=Array.from({length:8},(_,i)=>3000+group*8+i);
     const bursts=consumedIds.map(id=>({id,x:1000,y:0,age:.74,radius:202,cuts:8,interval:.1,travel:.08,damageType:'flying'}));
     A.assert(T.applyWindChain(p,{heavyCastId:902,activationId:300+group,consumedIds,bursts}),'causal pressure fixture failed');
   }
   A.chainFinish(.15);if(coarse)A.chainStep(.02);else A.chainFinish(.02);
   A.assert(!heavy.windTriggered&&T.windKnots.length===1,'slot freed after front exit retroactively ignited knot');
   out.push({coarse,triggers:heavy.windTriggered||0});
 }
 return out;
}"""

SETTLEMENT=r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];
 for(const phase of ['none','hurt','onDealt']){
   A.chainReset();A.rank('naruto-temari',3);for(const m of p.moves)m.t=999;
   const lower=A.spawn(140,-50,'boss'),upper=A.spawn(140,50,'boss'),low=A.watch(lower),high=A.watch(upper);
   A.chainSeed(lower);A.assert(T.windKnots.length===2,'two-cluster setup failed');
   p.x=100;p.y=0;p.cdMul=.01;
   const observed=[],previousObserver=T.onWindChainHit,previousDealt=p.onDealt,upperHurt=upper.hurt;
   T.onWindChainHit=info=>{previousObserver?.(info);if(!info.ghost)observed.push(info)};
   try{
     const first=A.chainHeavy(lower);A.chainFinish(.405);p.target=upper;
     A.resume();try{G.Combat.tick(.051,p,0)}finally{A.pause()}
     const second=T.casts.find(b=>b.owner===p&&b.kind==='heavy'&&b!==first);
     A.assert(second,'second legal fast-CD heavy absent');A.chainFinish(.07);
     const old=T.windBursts.find(a=>a.owner===p&&!a.ghost),remaining=(old.cuts-1)*old.interval+old.travel+old.fade-old.age;
     A.assert(old&&old.emitted===1,'old real burst did not retain pending pulses');
     let nextId=4000;
     for(const count of [8,8,8,7]){
       const consumedIds=Array.from({length:count},()=>nextId++),bursts=consumedIds.map(id=>({id,x:1000,y:0,age:.9-remaining,radius:202,cuts:8,interval:.1,travel:.08,damageType:'flying'}));
       A.assert(T.applyWindChain(p,{heavyCastId:903,activationId:nextId,consumedIds,bursts}),'real+31 pressure setup failed');
     }
     const extra=A.spawn(140,70,'boss'),extraHits=A.watch(extra);let derived=false;
     upper.hurt=function(...args){derived=args[7]==='naruto-temari-wind-chain';const value=upperHurt.apply(this,args);
       if(derived&&phase==='hurt')T.clear(p);return value;};
     if(phase==='onDealt')p.onDealt=function(...args){if(derived)T.clear(p);else return previousDealt?.apply(this,args)};
     A.chainStep(.405);
     if(phase==='none'){
       A.assert(old.cast.cuts===3&&old.dead,'expired real burst was dropped without completing pulses');
       A.assert(observed.filter(h=>h.burstId===old.id&&h.enemyId===lower.id).length===3,'old real lower cuts lost');
       A.assert(observed.filter(h=>h.burstId===old.id&&h.enemyId===upper.id).length===3,'old real upper cuts lost');
       A.assert(second.windTriggered===1,'post-expiry crossing was rejected');
     }else{
       A.assert(!second.windTriggered&&!T.windBursts.length&&!T.windKnots.length&&!T.stateFor(p),'old settlement callback resurrected new chain/state');
       A.assert(!A.chainHits(extraHits).length,'settlement callback damaged next valid target');
       A.assert(A.chainHits(low).length===1&&A.chainHits(high).length===1,'settlement continued after cancelling target');
     }
     out.push({phase,oldCuts:old.cast.cuts,newTriggers:second.windTriggered||0});
   }finally{upper.hurt=upperHurt;p.onDealt=previousDealt;T.onWindChainHit=previousObserver;T.clear();}
 }
 return out;
}"""

RETIRE=r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out={};A.chainReset();
 const packets=[],previous=T.onWindChain;T.onWindChain=(owner,packet)=>{previous?.(owner,packet);if(packet.removed)packets.push(packet)};
 try{
   const e=A.spawn(140,0,'boss');A.chainSeed(e);A.chainHeavy(e);A.chainFinish(1.5);A.chainFinish(6);
   A.assert(!T.windKnots.length&&!T.windBursts.length,'retirement setup not idle');
   const heavy=p.moves.find(m=>m.digiMode==='temari-great-scythe');p.moves=p.moves.filter(m=>m!==heavy);
   A.chainStep(.01);A.assert(packets.length===1&&packets[0].seedThrough>0&&packets[0].activationThrough>0,'idle issued sequences not retired');
   A.chainFinish(.1);A.assert(packets.length===1,'unlearn retirement spammed');p.moves.push(heavy);
   out.localFloor=packets[0];
 }finally{T.onWindChain=previous;}
 T.clear();A.chainReset();const remote={x:0,y:0,hp:100,dead:false};
 for(const id of [10,20])T.applyWindKnot(remote,{seedId:id,sourceCastId:1,x:id*20,y:0,age:0,ttl:6});
 for(const id of [11,21])T.applyWindChain(remote,{heavyCastId:2,activationId:id,consumedIds:[100+id],bursts:[{id,x:1000,y:0,age:0,radius:202,cuts:3,interval:.1,travel:.08,damageType:'flying'}]});
 const base={...T.snapshot(p,p.moves.find(m=>m.digiMode==='temari-wind')),castId:500,aim:0,targetPositions:[{x:140,y:0}]};
 A.assert(T.ghost(remote,base),'baseline ghost setup absent');let echoed=0;const previousRemote=T.onWindChain;
 T.onWindChain=(...args)=>{echoed++;previousRemote?.(...args)};
 try{
   A.assert(T.clearWindChain(remote,{seedThrough:10,activationThrough:11}),'selective clear rejected');
   A.assert(T.windKnots.filter(a=>a.owner===remote).map(a=>a.seedId).join()=== '20','selective clear removed future seed');
   A.assert(T.windBursts.filter(a=>a.owner===remote).map(a=>a.activationId).join()==='21','selective clear removed future activation');
   A.assert(T.casts.some(b=>b.owner===remote&&b.castId===500),'selective clear removed baseline attack');
   A.assert(echoed===0,'remote selective clear echoed');
 }finally{T.onWindChain=previousRemote;}
 out.selective=true;return out;
}"""

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path)
    parser.add_argument('--baseline',action='store_true')
    parser.add_argument('--checks',default='early,growth,missTTL,cancel,sources,capGhost,causal,clones,capCausal,settlement,retire')
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    report={'source':str(args.source or '.omx/naruto-temari.js'),'viewports':{},'failures':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=native.CHROME,headless=True)
        for label,viewport in [('desktop',{'width':1200,'height':900}),('mobile',{'width':390,'height':844})]:
            page=browser.new_page(viewport=viewport,is_mobile=label=='mobile',has_touch=label=='mobile')
            if args.source:page.route('**/.omx/naruto-temari.js*',lambda route:route.fulfill(path=str(args.source.resolve()),content_type='application/javascript'))
            native.boot(page);page.evaluate(SETUP);report['viewports'][label]={}
            checks=[('early',EARLY)] if args.baseline else [('early',EARLY),('growth',GROWTH),('missTTL',MISS_TTL),('cancel',CANCEL),('sources',SOURCES),('capGhost',CAP_GHOST),('causal',CAUSAL),('clones',CLONES),('capCausal',CAP_CAUSAL),('settlement',SETTLEMENT),('retire',RETIRE)]
            for name,check in checks:
                if name not in args.checks.split(','):continue
                try:report['viewports'][label][name]=page.evaluate(check)
                except Exception as error:report['failures'].append(label+':'+name+': '+str(error))
                print(label,name,'done',flush=True)
            page.close()
        browser.close()
    report['ok']=not report['failures'];path=OUT/('baseline.json' if args.baseline else 'report.json')
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'report':str(path)}))
    if not report['ok']:raise SystemExit(1)

if __name__=='__main__':main()
