"""Cyclone orbit acceptance using the production picker, cards, combat and rendering.

The open arena removes procedural obstacles only. Collision tests reintroduce
an explicit wall. No combat, damage, card or rendering implementation is mocked.
"""
import json
import math
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_temari as native

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/temari-typhoon'
ID = 'naruto-temari-typhoon'
REPORT = OUT / os.environ.get('TYPHOON_REPORT_NAME', 'report.json')

SETUP = r"""() => {
 const A=Acceptance,p=A.p();A.ty='naruto-temari-typhoon';
 // Production advances FX after combat every frame (js/game.js). Keep native
 // floating text and particle lifetimes in sync with manual combat time.
 const advance=A.advance;A.advance=(dt=.01)=>{advance(dt);A.resume();try{G.FX.update(dt)}finally{A.pause()}};
 A.tyLearn=()=>{A.learn();p.level=30;if(!p.hasMove(A.ty)){
   const c=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+A.ty);
   A.assert(c&&c.apply(p)!==false,'native typhoon learning card absent')}};
 A.tyCast=(Q=0,L=0,rank=1)=>{A.reset();A.mastery(L);A.rank(A.ty,rank);
   p.quantityBonus=p.quantityPicks=Q;const e=A.spawn(150,0,'boss');
   e.hp=e.maxHp=1e10;G.EnemyMgr.rebuildGrid();p.target=e;
   const hits=A.watch(e);A.castNative(A.ty);return {e,hits,f:G.NarutoTemari.stateFor(p).latest}};
}"""

PROGRESSION = r"""() => {
 const A=Acceptance,p=A.p(),out=[];A.assert(!p.hasMove(A.ty),'fresh character has typhoon');
 for(const level of [11,12]){p.level=level;const cards=G.LevelUp.offer(p,100);
   const c=cards.find(c=>c.key==='new:'+A.ty);A.assert(!!c===(level===12),'Lv12 card gate '+level);
   out.push({level,eligible:!!c,guaranteed:!!c?.guaranteed})}
 const mon=p.mon;try{for(const dex of [30001,30006,30009,30010]){
   p.mon=G.DEX.find(m=>m.dex===dex);A.assert(!G.Moves.poolFor(p.mon).includes(A.ty),'typhoon leaked into '+dex)}}finally{p.mon=mon}
 A.tyLearn();A.rank(A.ty,1);
 for(let rank=1;rank<=5;rank++){
   if(rank>1){const c=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+A.ty);A.assert(c&&c.apply(p)!==false,'rank card '+rank)}
   const m=p.moves.find(m=>m.id===A.ty);A.near(m.dmg,[24,28.8,35.2,43.2,52.8][rank-1],'rank damage');A.near(m.cd,8,'rank cooldown');
   A.assert(m.lvl===rank&&m.digiMode==='temari-typhoon'&&!m.passive,'rank/mode/slot');
   A.reset();A.mastery(0);p.target=A.spawn(150,0,'boss');A.castNative(A.ty);const f=G.NarutoTemari.stateFor(p).latest;
   A.near(f.radius,[240,270,300,330,360][rank-1],'rank circle');A.assert(f.C===[3,4,5,6,8][rank-1],'rank cuts');
   out.push({rank,radius:f.radius,C:f.C,damage:f.damage});
 }return out;
}"""

GROWTH = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];A.tyLearn();
 for(const Q of [0,5,10,20])for(const L of [0,1,5]){
   const {e,hits,f}=A.tyCast(Q,L,5),count=Math.floor(1.25**Q),C=8+(L?L+Q:0);
   A.assert(f.kind==='typhoon'&&f.T===count&&f.C===C&&f.count===count,'wrong T/C '+JSON.stringify({Q,L,T:f.T,C:f.C,count:f.count}));
   A.assert(f.potentialHits===count*C,'multiplicative potential capped');
   const start=performance.now();A.finish(4);
   A.assert(f.emitted===count&&f.cuts===count*C,'physical storm/pulse events capped '+JSON.stringify({Q,L,emitted:f.emitted,cuts:f.cuts}));
   A.assert(hits.length===count*C,'independent coincident storm hits missing '+hits.length+'/'+count*C);
   A.assert(hits.every(h=>h.owner&&h.id===A.ty&&h.damage>0&&!h.secondary),'owned native primary damage');
   A.near(e.maxHp-e.hp,hits.length*hits[0].damage,'actual total HP');
   A.assert(!T.storms.length,'expired storms retained');
   out.push({Q,L,T:count,C,potential:count*C,hits:hits.length,damage:e.maxHp-e.hp,updateMs:performance.now()-start});
 }return out;
}"""

GEOMETRY = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.tyLearn();A.reset();A.mastery(0);A.rank(A.ty,1);
 const es=[A.spawn(100,0,'boss'),A.spawn(0,130,'boss'),A.spawn(-150,0,'boss'),A.spawn(-350,0,'boss')],hits=es.map(A.watch);
 p.target=es[0];A.castNative(A.ty);A.finish(.43);
 A.assert(hits[0].length===1&&hits[1].length===0&&hits[2].length===0,'360 sweep hit entire circle immediately');
 p.x=400;p.y=400;A.finish(3);A.assert(hits.slice(0,3).every(h=>h.length===3)&&hits[3].length===0,'fixed cast eye or circle boundary wrong');
 A.reset();const target=A.spawn(100,0,'boss'),escape=A.watch(target);p.target=target;A.castNative(A.ty);A.finish(.45);
 A.assert(escape.length===1,'initial physical contact missing');target.x=700;G.EnemyMgr.rebuildGrid();A.finish(3);A.assert(escape.length===1,'escaped enemy received delayed cuts');
 A.reset();const near=A.spawn(100,0,'boss'),behind=A.spawn(0,130,'boss'),blocked=A.watch(behind);p.target=near;A.castNative(A.ty);
 const wall=G.World.projectileBlock;G.World.projectileBlock=(x,y)=>y>55&&y<75?{wall:true}:false;
 try{A.finish(3);A.assert(blocked.length===0,'sweep captured through wall')}finally{G.World.projectileBlock=wall}
 const strong=[];for(const special of ['boss','elite','legend','judge']){A.reset();const e=A.spawn(100,0,special),watched=A.watch(e);p.target=e;
   A.castNative(A.ty);A.finish(3);A.assert(e.x===100&&e.y===0&&watched.length===3,'strong enemy displaced or omitted '+special);strong.push(special)}
 return {counts:hits.map(h=>h.length),escaped:escape.length,blocked:blocked.length,strong};
}"""

ORBIT = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.tyLearn();A.reset();A.mastery(0);A.rank(A.ty,1);
 const specs=[[70,0],[130,2],[210,-.15]],es=specs.map(([r,a])=>A.spawn(r*Math.cos(a),r*Math.sin(a))),hits=es.map(A.watch);
 const traces=es.map((e,i)=>({radius:specs[i][0],previous:Math.atan2(e.y,e.x),angle:0,maxStep:0,first:null,last:null,samples:[]}));
 p.target=es[0];A.castNative(A.ty);
 for(let i=0;i<700;i++){const old=es.map(e=>({x:e.x,y:e.y}));A.resume();try{for(const e of es)e.update(.005,p,i*.005)}finally{A.pause()}A.advance(.005);
   es.forEach((e,j)=>{const t=traces[j],angle=Math.atan2(e.y,e.x),delta=Math.atan2(Math.sin(angle-t.previous),Math.cos(angle-t.previous));
     t.angle+=delta;t.previous=angle;t.maxStep=Math.max(t.maxStep,Math.hypot(e.x-old[j].x,e.y-old[j].y));
     if(hits[j].length&&t.first===null)t.first=(i+1)*.005;if(Math.abs(delta)>.00001)t.last=(i+1)*.005;
     A.near(Math.hypot(e.x,e.y),t.radius,'orbit radius changed');if(i%10===0)t.samples.push({time:(i+1)*.005,x:e.x,y:e.y});});
   G.EnemyMgr.rebuildGrid();}
 traces.forEach((t,i)=>{A.assert(Math.abs(Math.abs(t.angle)-2*Math.PI)<.04,'enemy did not really travel complete2pi '+JSON.stringify(t));
   A.assert(t.maxStep<=8,'orbit teleported '+t.maxStep);A.assert(t.last-t.first>1.16,'last capture lost its own full orbit');A.assert(hits[i].length===3,'orbit contact cuts missing')});
 A.assert(traces[2].first>1.3&&traces[2].last>2.5,'late swept enemy released at common sweep end');
 A.assert(!T.orbits.length,'completed orbit lease retained');
 A.orbitEvidence={traces};
 // Multiple wind streams may hit independently while one global control lease
 // prevents conflicting trajectories or restarting the same enemy's angle.
 A.reset();A.mastery(5);A.rank(A.ty,5);p.quantityBonus=p.quantityPicks=10;const e=A.spawn(140,0),watched=A.watch(e);p.target=e;A.castNative(A.ty);
 let peak=0,last=0,travel=0,maxStep=0;for(let i=0;i<800;i++){const x=e.x,y=e.y;A.advance(.005);const a=Math.atan2(e.y,e.x);travel+=Math.atan2(Math.sin(a-last),Math.cos(a-last));last=a;
   maxStep=Math.max(maxStep,Math.hypot(e.x-x,e.y-y));const leases=T.orbits.filter(o=>o.enemy===e||o.target===e);peak=Math.max(peak,leases.length);A.assert(leases.length<=1,'multiple control leases for one enemy');G.EnemyMgr.rebuildGrid();}
 A.assert(peak===1&&Math.abs(Math.abs(travel)-2*Math.PI)<.04&&maxStep<=8,'stacked stream restarted orbit');
 A.assert(watched.length===Math.floor(1.25**10)*(8+5+10),'control dedup removed independent damage '+watched.length);
 A.reset();A.mastery(0);A.rank(A.ty,1);p.cdMul=.02;const repeat=A.spawn(140,0);p.target=repeat;A.castNative(A.ty);A.finish(.5);
 const lease=T.orbitFor(repeat);A.assert(lease,'overlap control fixture absent');const angle=lease.startAngle;
 const moves=p.moves;p.moves=moves.filter(m=>m.digiMode==='temari-mastery');A.resume();try{G.Combat.tick(.2,p,0)}finally{p.moves=moves;A.pause()}
 A.finish(.5);A.assert(T.orbitFor(repeat)===lease&&lease.startAngle===angle,'overlapping cast restarted active orbit');
 return {traces,stacked:{peak,travel,maxStep,hits:watched.length},overlapLeasePreserved:true};
}"""

ORBIT_COLLISION = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.tyLearn();A.reset();A.mastery(0);A.rank(A.ty,1);
 const e=A.spawn(120,0),hits=A.watch(e);p.target=e;A.castNative(A.ty);for(let i=0;i<100&&!hits.length;i++)A.advance(.005);A.assert(hits.length,'collision fixture not captured');
 const free=G.World.isFree,block=G.World.projectileBlock;
 const solid=(x,y,r=0)=>x+r>75&&x-r<95&&Math.abs(y)+r>60&&Math.abs(y)-r<105;
 G.World.isFree=(x,y,r=0)=>!solid(x,y,r);G.World.projectileBlock=(x,y,r=0)=>solid(x,y,r)?{wall:true}:false;
 let maxStep=0,travel=0,last=Math.atan2(e.y,e.x);const path=[];
 try{for(let i=0;i<500;i++){const x=e.x,y=e.y;A.advance(.005);const a=Math.atan2(e.y,e.x);travel+=Math.atan2(Math.sin(a-last),Math.cos(a-last));last=a;
   maxStep=Math.max(maxStep,Math.hypot(e.x-x,e.y-y));A.assert(!solid(e.x,e.y,e.r),'orbit entered wall');if(i%10===0)path.push([e.x,e.y]);G.EnemyMgr.rebuildGrid();}}
 finally{G.World.isFree=free;G.World.projectileBlock=block}
 A.assert(Math.abs(travel)<Math.PI&&maxStep<=8&&!T.orbits.length,'blocked orbit teleported across obstacle or retained lease');
 A.reset();A.mastery(0);A.rank(A.ty,1);const lagged=A.spawn(120,0),lagHits=A.watch(lagged);p.target=lagged;A.castNative(A.ty);
 for(let i=0;i<100&&!lagHits.length;i++)A.advance(.005);const from={x:lagged.x,y:lagged.y};
 G.World.isFree=(x,y,r=0)=>!solid(x,y,r);G.World.projectileBlock=(x,y,r=0)=>solid(x,y,r)?{wall:true}:false;
 try{A.advance(.6);A.assert(lagged.x>90&&Math.abs(lagged.y)<70&&!solid(lagged.x,lagged.y,lagged.r)&&!T.orbitFor(lagged),'large-dt arc checked endpoint only / crossed wall')}
 finally{G.World.isFree=free;G.World.projectileBlock=block}
 return {travel,maxStep,path,largeStep:{from,to:{x:lagged.x,y:lagged.y}}};
}"""

ACCOUNTING = r"""() => {
 const A=Acceptance,p=A.p(),out=[];A.tyLearn();
 for(const boss of [false,true])for(const crit of [0,1]){
   A.reset();A.mastery(0);A.rank(A.ty,1);p.percentHealthDamage=.001;p.lifestealRate=.00001;p.damageSplashPicks=2;p.critChance=crit;p.hp=p.maxHp/2;
   const e=A.spawn(150,0,boss?'boss':null),side=A.spawn(150,20,boss?'boss':null),hits=A.watch(e),secondary=A.watch(side),hp=p.hp,credit=p.dmgDealt;
   p.target=e;A.castNative(A.ty);A.finish(3);
   const raw=30*p.atk*G.Types.mult('flying',e.types)*G.Weather.mult('flying')*(crit?1.5:1),bonus=e.maxHp*.001*(boss?.1:1),all=[...hits,...secondary];
   A.assert(hits.length===3&&secondary.length===3,'per-contact sweep damage');
   A.assert(all.every(h=>!h.secondary&&Math.abs(h.raw-raw)<1e-5&&h.damage===Math.round(raw+bonus)),'percent/crit/AOE splash accounting '+JSON.stringify(all));
   A.near(p.dmgDealt-credit,(raw+bonus)*all.length,'credit');A.near(p.hp-hp,(raw+bonus)*all.length*.00001,'lifesteal');out.push({boss,crit,hits:all.length,healed:p.hp-hp});
 }A.reset();A.mastery(5);p.item='lifeorb';p.target=A.spawn(150,0,'boss');const hp=p.hp;A.castNative(A.ty);A.finish(5);
 A.near(hp-p.hp,Math.max(1,p.maxHp*.01),'lifeorb per cast');return out;
}"""

SNAPSHOT_OVERLAP = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.tyLearn();const {hits,f}=A.tyCast(5,1,1),damage=f.damage,C=f.C,Tn=f.T;
 p.quantityBonus=p.quantityPicks=20;A.mastery(5);const atk=p.atkMul;p.atkMul*=3;A.rank(A.ty,5);A.finish(.8);
 A.assert(f.T===Tn&&f.C===C&&f.damage===damage,'cast snapshot mutated');A.finish(4);
 A.assert(hits.length===Tn*C&&hits.every(h=>Math.abs(h.raw-damage*G.Types.mult('flying',['normal'])*G.Weather.mult('flying'))<1e-6),'existing storms adopted later quantity/mastery/attack/rank');p.atkMul=atk;
 // A genuine cooldown card changes the next cast; private cooldown remains authoritative.
 A.reset();A.mastery(5);p.quantityBonus=p.quantityPicks=5;p.target=A.spawn(150,0,'boss');
 const cd=G.LevelUp.offer(p,100).find(c=>c.key==='stat:cd');A.assert(cd,'native cooldown card absent');cd.apply(p);
 p.cdMul=.02;A.castNative(A.ty);const first=T.stateFor(p).latest;A.finish(.5);const old=[...T.storms];
 const moves=p.moves;p.moves=moves.filter(m=>m.digiMode==='temari-mastery');A.resume();try{G.Combat.tick(.2,p,0)}finally{p.moves=moves;A.pause()}
 const second=T.stateFor(p).latest;A.finish(.5);
 A.assert(second!==first&&old.every(s=>T.storms.includes(s))&&T.storms.length===first.emitted+second.emitted,'new cast replaced old storms '+JSON.stringify({different:second!==first,old:old.length,retained:old.filter(s=>T.storms.includes(s)).length,total:T.storms.length,first:first.emitted,second:second.emitted}));
 const heavy=p.moves.find(m=>m.id==='naruto-temari-great-scythe');
 A.reset();p.target=A.spawn(150,0,'boss');A.select(A.ty);const group=p.activeGroup(),before=group.slice();group.push(heavy);for(const m of group)m.t=0;
 try{A.resume();G.Combat.tick(.001,p,0);A.pause();A.assert(T.casts.some(c=>c.mode==='temari-typhoon')&&T.casts.some(c=>c.mode==='temari-great-scythe'),'fusion starved active')}
 finally{group.splice(0,group.length,...before);A.pause()}
 A.finish(.5);const cuts=T.stateFor(p).totalCuts;const m=p.moves.find(m=>m.id===A.ty),cooldown=m.t;
 // Switch to another active skill; Kamatari is now passive and has no slot.
 A.select('naruto-temari-great-scythe');A.finish(.5);A.assert(T.stateFor(p).totalCuts>cuts,'cutaway deleted storms');A.near(m.t,cooldown,'cutaway refreshed cooldown');
 return {snapshot:{T:Tn,C,damage},overlap:first.T+second.T,fusion:true,cutaway:true};
}"""

CLONES_LIFECYCLE = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.tyLearn();const {e,hits,f}=A.tyCast(5,5,1);A.finish(6);const baseline=hits[0].raw;
 G.Combat.clearFields();hits.length=0;const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');A.assert(card,'clone card absent');card.apply(p);
 const clone=G.SelfClones.actors()[0];clone.x=clone.y=0;clone.target=e;clone.aim=0;A.castNative(A.ty,clone);const cf=T.stateFor(clone).latest;
 const ownerMoves=p.moves;p.moves=p.moves.filter(m=>m.digiMode==='temari-mastery');
 try{A.finish(6)}finally{p.moves=ownerMoves}
 A.assert(cf.T===f.T&&cf.C===f.C&&hits.length===cf.potentialHits,'clone lost quantity/cuts '+JSON.stringify({T:cf.T,C:cf.C,ownerT:f.T,ownerC:f.C,hits:hits.length,potential:cf.potentialHits}));
 A.assert(hits.every(h=>h.clone),'clone damage misattributed');hits.forEach(h=>A.near(h.raw*3,baseline,'clone one-third'));
 G.SelfClones.clear();A.advance();A.assert(!T.stateFor(clone)&&!T.storms.some(s=>s.owner===clone),'clone cleanup');
 for(const reason of ['pause','clear','death','world','owner']){A.reset();A.mastery(5);A.rank(A.ty,1);const victim=A.spawn(100,0);p.target=victim;A.castNative(A.ty);A.finish(.7);
   const cast=T.stateFor(p).latest,cuts=cast.cuts,world=G.World,game=G.Game,x=victim.x,y=victim.y;A.assert(T.orbitFor(victim),'lifecycle lacks live orbit');
   if(reason==='pause'){G.Combat.updateFields(1);A.assert(cast.cuts===cuts&&victim.x===x&&victim.y===y,'paused storm advanced damage/position')}
   if(reason==='clear')G.Combat.clearFields(p);if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};
   if(reason==='owner')G.Game={...game,get state(){return game.state},player:{...p}};
   try{if(reason!=='pause'){
     // Clear/world reset may immediately recreate the owner's passive state.
     // Prove the original storm and movement lease are gone independently.
     if(reason==='clear')A.assert(!T.storms.some(s=>s.owner===p)&&!T.orbitFor(victim),'clear retained live storm/orbit before next update');
     A.advance();const current=T.stateFor(p);
     A.assert(!T.storms.some(s=>s.owner===p)&&!T.orbitFor(victim),'stale storm/orbit after '+reason);
     A.assert(reason==='clear'||reason==='world'?current?.latest!==cast:!current,'old cast/invalid owner state retained after '+reason);
   }}finally{G.World=world;G.Game=game;p.dead=false}
 }return {cloneHits:hits.length,ratio:1/3,reasons:['pause','clear','death','world','owner']};
}"""

PERFORMANCE = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.tyLearn();A.reset();A.mastery(5);A.rank(A.ty,5);p.quantityBonus=p.quantityPicks=20;
 const target=A.spawn(150,0,'boss');target.hp=target.maxHp=1e10;G.EnemyMgr.rebuildGrid();p.target=target;const hits=A.watch(target);
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');for(let i=0;i<3;i++)card.apply(p);
 const actors=[p,...G.SelfClones.actors()];for(const a of actors){a.x=a.y=0;a.target=target;A.castNative(A.ty,a)}const casts=actors.map(a=>T.stateFor(a).latest);
 const c=document.createElement('canvas');c.width=1200;c.height=900;const ctx=c.getContext('2d'),updates=[],draws=[];let peak=0;
 const ownerMoves=p.moves;p.moves=p.moves.filter(m=>m.digiMode==='temari-mastery');
 // Freeze only new actor actions after release to measure exactly one cast
 // group; already emitted fields preserve the production damage schedule.
 p.frozen=true;
 try{for(let i=0;i<600;i++){let start=performance.now();A.resume();try{G.Combat.updateFields(1/60)}finally{A.pause()}updates.push(performance.now()-start);peak=Math.max(peak,T.storms.length);
   start=performance.now();ctx.clearRect(0,0,c.width,c.height);G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);draws.push(performance.now()-start)}}finally{p.moves=ownerMoves;p.frozen=false}
 A.assert(casts.every(f=>f.T===86&&f.C===33&&f.cuts===86*33),'high-quantity clone workload capped');
 A.assert(hits.length===4*86*33&&!T.storms.length,'high-quantity actual HP events or cleanup '+JSON.stringify({hits:hits.length,storms:T.storms.length}));
 const stats=a=>({total:a.reduce((s,v)=>s+v,0),p95:[...a].sort((a,b)=>a-b)[Math.floor(a.length*.95)],max:Math.max(...a)});
 return {actors:actors.length,T:86,C:33,peak,hits:hits.length,updateMs:stats(updates),drawMs:stats(draws),scope:'native CPU update and Canvas fields; excludes complete GPU frame'};
}"""


def visual(page, label):
    out = {}
    page.evaluate("G.Settings.set('dmgNumbers',true)")
    slot = page.evaluate("""() => {const A=Acceptance,p=A.p();A.tyLearn();A.reset();
      const index=p.slots.findIndex(g=>g.some(m=>m.id===A.ty));p.setActive((index+1)%p.slots.length);A.resume();return index}""")
    if label == 'mobile':
        rect = page.evaluate('''(index)=>{const p=G.Game.player,groups=[...p.slots,...p.moves.filter(m=>m.passive&&!p.slots.some(g=>g.includes(m))).map(m=>[m])];
          return G.Touch.controlLayout(innerWidth,innerHeight,groups.length).slots[index]}''', slot)
        page.touchscreen.tap(rect['x']+rect['w']/2, rect['y']+rect['h']/2)
    else:
        page.keyboard.press(f'Digit{slot+1}')
    page.wait_for_function('(index)=>G.Game.player.active===index', arg=slot)
    page.evaluate('Acceptance.pause()')
    out['nativeSlotInput'] = {'slot': slot, 'input': 'touch' if label == 'mobile' else 'keyboard'}
    quantities = [int(value) for value in os.environ.get('TYPHOON_VISUAL_QUANTITIES', '0,5,20').split(',')]
    for quantity in quantities:
        page.evaluate(r"""(Q) => {const A=Acceptance,p=A.p();A.tyLearn();A.reset();A.mastery(1);A.rank(A.ty,1);
          p.quantityBonus=p.quantityPicks=Q;p.target=A.spawn(55,65);A.spawn(-90,55);A.spawn(0,-120);A.castNative(A.ty);A.finish(.85);
          p.flash=0;for(const e of G.EnemyMgr.all())e.flash=0;
          A.assert(G.NarutoTemari.storms.length===Math.floor(1.25**Q),'visual phase lacks live storms')}
        """, quantity)
        result = page.evaluate(r"""() => {
      const c=document.createElement('canvas');c.width=600;c.height=480;const ctx=c.getContext('2d');ctx.translate(160,300);
      G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);const rgba=ctx.getImageData(0,0,c.width,c.height).data;
      let pixels=0,x0=c.width,x1=0,y0=c.height,y1=0;for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++)if(rgba[(y*c.width+x)*4+3]>10){pixels++;x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}
      Acceptance.assert(pixels>1000&&x1-x0>80&&y1-y0>40,'sweeping wind art missing '+JSON.stringify({pixels,x0,x1,y0,y1}));
      return {pixels,bounds:[x0,y0,x1,y1],png:c.toDataURL()};
        }""")
        import base64
        (OUT / f'{label}-q{quantity}-wind-column.png').write_bytes(base64.b64decode(result.pop('png').split(',', 1)[1]))
        page.screenshot(path=str(OUT / f'{label}-q{quantity}-gameplay.png'))
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'horizontal overflow'
        out[f'Q{quantity}'] = result
        # Record the whole cast, including late targets' completed orbits.
        page.evaluate(r"""(Q)=>{const A=Acceptance,p=A.p();A.reset();A.mastery(1);A.rank(A.ty,1);p.quantityBonus=p.quantityPicks=Q;
          p.target=A.spawn(80,0);A.spawn(-60,90);A.spawn(80,-15);A.castNative(A.ty)}""", quantity)
        age = 0
        sequence = []
        for phase in [.1, .4, .7, 1.0, 1.4, 1.8, 2.4, 3.0]:
            state = page.evaluate('''(dt)=>{const A=Acceptance;A.finish(dt);A.p().flash=0;for(const e of G.EnemyMgr.all())e.flash=0;
              const pose=A.pose(),sheet=G.TemariArt.metadata.sheets.spin;
              const spinFrames=pose.sources.flatMap((src,i)=>src===G.TemariArt.images.spin?.src?[sheet.frames.findIndex(f=>f.rect.every((v,j)=>v===pose.rects[i][j]))]:[]);
              return {storms:G.NarutoTemari.storms.length,orbits:G.NarutoTemari.orbits.length,fx:G.FX.count,damageNumbers:G.Settings.get('dmgNumbers'),spinFrames,actorSources:pose.sources,enemies:G.EnemyMgr.all().map(e=>({x:e.x,y:e.y,hp:e.hp}))}}''', phase-age)
            page.screenshot(path=str(OUT / f'{label}-q{quantity}-phase-{phase:.1f}.png'))
            sequence.append({'phase': phase, **state})
            age = phase
        out[f'Q{quantity}']['sequence'] = sequence
        spin_frames = {frame for state in sequence for frame in state['spinFrames'] if frame >= 0}
        assert len(spin_frames) >= 4, f'actual cast did not render distinct body rotation frames: {spin_frames}'
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'ok': False, 'errors': [], 'failedRequests': [], 'failures': [], 'viewports': {}}
    checks = [('progression', PROGRESSION), ('growth', GROWTH), ('geometry', GEOMETRY), ('orbit', ORBIT), ('orbitCollision', ORBIT_COLLISION), ('accounting', ACCOUNTING), ('snapshotOverlap', SNAPSHOT_OVERLAP), ('clonesLifecycle', CLONES_LIFECYCLE), ('performance', PERFORMANCE)]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=native.CHROME, headless=True)
        for label, size, mobile in [('desktop', {'width': 1200, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
            if os.environ.get('TYPHOON_VIEWPORTS') and label not in os.environ['TYPHOON_VIEWPORTS'].split(','):
                continue
            context = browser.new_context(viewport=size, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.on('response', lambda r: report['failedRequests'].append({'url': r.url, 'status': r.status}) if r.status >= 400 and '127.0.0.1' in r.url else None)
            native.boot(page)
            page.evaluate(SETUP)
            result = report['viewports'][label] = {}
            for name, check in checks:
                if os.environ.get('TYPHOON_CHECKS') and name not in os.environ['TYPHOON_CHECKS'].split(','):
                    continue
                print(label, name, flush=True)
                try:
                    result[name] = page.evaluate(check)
                except Exception as error:
                    result[name] = {'failure': str(error)}
                    if name == 'orbit':
                        result[name]['partialTrajectoryEvidence'] = page.evaluate('Acceptance.orbitEvidence || null')
                    report['failures'].append(f'{label}:{name}: {error}')
                    print(report['failures'][-1], flush=True)
                REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
            try:
                result['visual'] = visual(page, label)
            except Exception as error:
                report['failures'].append(f'{label}:visual: {error}')
            context.close()
        browser.close()
    report['ok'] = not (report['errors'] or report['failedRequests'] or report['failures'])
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': report['ok'], 'failures': report['failures'], 'evidence': str(OUT)}))
    if not report['ok']:
        raise SystemExit(1)


def coop():
    """Real host/guest game code over the established JSON adapter boundary."""
    import test_temari_coop as protocol
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'ok': False, 'packets': 0, 'eventKinds': {}, 'errors': [], 'scenarios': {},
              'coverage': 'Native host authority, guest damage forwarding and enemy replication over controlled JSON transport',
              'notCovered': ['internet transport', 'Firebase login', 'packet loss/reordering']}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=native.CHROME, headless=True)
            pages, contexts = {}, []
            for uid in ['host', 'guest']:
                context = browser.new_context(viewport={'width': 1000, 'height': 800}, service_workers='block')
                context.add_init_script('window.requestAnimationFrame=()=>0')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                try:
                    native.boot(page)
                except Exception as error:
                    diagnostic = page.evaluate('''({url:location.href,state:window.G?.Game?.state,dex:window.G?.Game?.player?.dex,
                      ready:window.PS_REDRAWN_READY,boot:document.getElementById('boot')?.outerHTML,
                      menu:document.getElementById('scr-menu')?.className,errors:window.onerror?.toString()})''')
                    raise AssertionError(f'{uid} boot failed: {error}; {diagnostic}') from error
                page.evaluate(SETUP)
                page.evaluate(protocol.ADAPTER, uid)
                page.evaluate('Acceptance.tyLearn();Acceptance.reset();Acceptance.mastery(0);Acceptance.rank(Acceptance.ty,1)')
                contexts.append(context)
                pages[uid] = page
            host, guest = pages['host'], pages['guest']
            host.evaluate("window.CoopEnemy=Acceptance.spawn(120,0);window.CoopHits=Acceptance.watch(CoopEnemy);G.Coop.tick(.1)")
            protocol.pump(pages, report)
            guest.evaluate('window.CoopEnemy=G.EnemyMgr.all().find(e=>e.remote);Acceptance.assert(CoopEnemy,"enemy replication absent")')
            for caster_uid in ['host', 'guest']:
                for page in pages.values():
                    page.evaluate('''() => {const p=G.Game.player;G.Combat.clearFields();G.Projectiles.clear();
                      p.x=p.y=0;p.target=CoopEnemy;p.quantityBonus=p.quantityPicks=0;p.cdMul=1;CoopEnemy.x=120;CoopEnemy.y=0;
                      if(CoopEnemy.net){CoopEnemy.net.x=120;CoopEnemy.net.y=0;CoopEnemy.net.vx=CoopEnemy.net.vy=0}
                      G.EnemyMgr.rebuildGrid()}''')
                before = host.evaluate('({hp:CoopEnemy.hp,hits:CoopHits.length})')
                pages[caster_uid].evaluate('Acceptance.castNative(Acceptance.ty)')
                protocol.pump(pages, report)
                packet = report['lastCastPacket']
                receiver = pages[packet['to']]
                count = receiver.evaluate('G.NarutoTemari.casts.length')
                receiver.evaluate('(m)=>CoopFixture.receive(m.from,m.msg)', packet)
                assert receiver.evaluate('G.NarutoTemari.casts.length') == count, 'duplicate packet created another ghost'
                samples, captured = [], False
                for frame in range(70):
                    for page in pages.values():
                        page.evaluate('''() => {CoopFixture.step(5);const A=Acceptance;A.resume();try{
                          for(const e of G.EnemyMgr.all())if(e.remote)e.netUpdate(.05);
                        }finally{A.pause()}}''')
                    protocol.pump(pages, report)
                    # Flush a native host snapshot and compare the actual
                    # authoritative coordinates with the guest's received
                    # position, before normal smoothing/extrapolation.
                    host.evaluate('G.Coop.tick(.1)')
                    protocol.pump(pages, report)
                    h = host.evaluate('({x:CoopEnemy.x,y:CoopEnemy.y,lease:!!G.NarutoTemari.orbitFor(CoopEnemy),hp:CoopEnemy.hp,hits:CoopHits.length})')
                    g = guest.evaluate('({x:CoopEnemy.x,y:CoopEnemy.y,nx:CoopEnemy.net.x,ny:CoopEnemy.net.y,lease:!!G.NarutoTemari.orbitFor(CoopEnemy)})')
                    assert abs(h['x']-g['nx']) <= 1 and abs(h['y']-g['ny']) <= 1, f'guest received stale host coordinates: {h} {g}'
                    if h['lease']:
                        captured = True
                        assert g['lease'], 'host capture was not replicated to guest'
                    if frame % 3 == 0:
                        samples.append({'time': (frame+1)*.05, 'host': h, 'guest': g})
                after = host.evaluate('({hp:CoopEnemy.hp,hits:CoopHits.length,x:CoopEnemy.x,y:CoopEnemy.y})')
                stats = pages[caster_uid].evaluate('''() => {const f=G.NarutoTemari.stateFor(G.Game.player).latest;return {hits:f.hits,cuts:f.cuts,T:f.T,C:f.C}}''')
                assert captured, caster_uid+': host never controlled the enemy'
                assert after['hits']-before['hits'] == stats['hits'] == 3, caster_uid+': ghost duplicated damage or guest forwarding lost hits'
                assert after['hp'] < before['hp'], caster_uid+': host HP unchanged'
                assert abs(after['x']-120) < .01 and abs(after['y']) < .01, caster_uid+': authoritative enemy did not complete full orbit'
                bearings = [math.atan2(sample['guest']['y'], sample['guest']['x']) for sample in samples]
                winding = sum(math.atan2(math.sin(b-a), math.cos(b-a)) for a, b in zip(bearings, bearings[1:]))
                assert abs(abs(winding)-2*math.pi) < .05, caster_uid+': guest actual smoothed coordinates did not travel one full circle'
                assert abs(samples[-1]['guest']['x']-120) < .1 and abs(samples[-1]['guest']['y']) < .1, 'guest never converged to released authoritative position'
                for page in pages.values():
                    assert page.evaluate('G.NarutoTemari.orbits.length===0'), 'expired network orbit retained'
                report['scenarios'][caster_uid] = {'samples': samples, 'guestActualWinding': winding, 'hostDamage': before['hp']-after['hp'], **stats}
            assert report['eventKinds'].get('to', 0) >= 2 and report['eventKinds'].get('te', 0) >= 2, 'missing capture/release protocol events'
            for page in pages.values():
                page.evaluate('G.Combat.clearFields();G.Game.player.target=CoopEnemy;G.EnemyMgr.rebuildGrid()')
            guest.evaluate('Acceptance.castNative(Acceptance.ty)')
            protocol.pump(pages, report)
            protocol.advance(pages, report, .7)
            assert host.evaluate('G.NarutoTemari.orbits.length>0'), 'disconnect fixture lacks active host orbit'
            host.evaluate("CoopFixture.disconnect('guest')")
            protocol.advance(pages, report, .2)
            assert host.evaluate('G.NarutoTemari.orbits.length===0'), 'disconnected caster retained authoritative control'
            assert host.evaluate('G.NarutoTemari.storms.every(s=>!s.owner.remote)'), 'disconnected caster retained ghost storms'
            report['scenarios']['disconnectCleanup'] = True
            assert not report['errors'], report['errors']
            for context in contexts:
                context.close()
            browser.close()
        report['ok'] = True
    except Exception as error:
        report['failure'] = str(error)
    (OUT / 'coop-orbit-acceptance.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': report['ok'], 'failure': report.get('failure'), 'packets': report['packets']}))
    if not report['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    if os.environ.get('TYPHOON_COOP'):
        coop()
    else:
        main()
