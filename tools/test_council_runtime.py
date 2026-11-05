"""Council implementation acceptance through the normal entry and native damage.

Controlled fixtures flatten terrain only in combat tests. Production render tests
use a separate unmodified world; no screenshot mockups or fake actor compositor.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT=Path(__file__).resolve().parents[1]
HEROES={30013:'yuta',30014:'ryu',30015:'uro'}

def runtime_hashes(url):
    root=ROOT/'dist-digimon' if '/dist-digimon/' in url else ROOT
    names=['.omx/digimon.html','.omx/jujutsu.js','.omx/jujutsu-growth.js','.omx/combat-pulse.js','.omx/jujutsu-vfx.js','.omx/trial-build.js','.omx/run-insights.js','.omx/dev-controls.js','.omx/jjk-yuta.js','.omx/jjk-ryu.js','.omx/jjk-uro.js','.omx/jujutsu-art.js','.omx/naruto.js','.omx/redrawn-init.js','.omx/menu-layout.css','js/game.js','js/systems/combat.js','js/systems/spawner.js','js/systems/levelup.js','js/entities/player.js','js/entities/enemy.js','js/systems/pathing.js','js/core/camera.js','js/systems/hazards.js','art-review/jjk-skills-v2.json']
    m=root/'art-review/jjk-skills-v2.json'
    if m.exists():names+=['art-review/'+s['source'] for s in json.loads(m.read_text('utf8'))['sheets'].values()]
    return {n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names if (root/n).exists()}

CARDS=r"""() => {
 const A=JAcceptance,p=A.p(),assert=A.assert,out={};A.reset();p.level=20;p.statsTaken={};
 const offer=()=>G.LevelUp.offer(p,1000),has=id=>offer().some(c=>c.key==='stat:'+id);
 assert(!has('heal'),'full-health immediate healing offered');p.hp-=10;assert(has('heal'),'injured player cannot choose healing');p.hp=p.maxHp;
 if(p.dex===30013||p.dex===30015){
  assert(!has('quantity'),'quantity offered without actual consumer');
  G.SelfClones.summon(p);assert(!has('quantity'),'mere card clone incorrectly enables quantity');out.noFalseConsumer=true;
 }else{
  p.moves=[];p.slots=[];p.bind={};assert(p.addMove('jjk-ryu'),'missing basic');
  assert(!has('quantity'),'basic beam alone incorrectly consumes quantity');assert(p.addMove('jjk-ryu-spread'),'spread learn failed');
  const enemy=A.spawn(150,0);p.target=enemy;out.counts=[];out.previews=[];
  function count(){G.Combat.clearFields(p);const m=p.moves.find(m=>m.id==='jjk-ryu-spread');m.t=0;
   A.resume();try{assert(G.JjkRyu.cast(p,m),'native spread cast failed');out.counts.push(G.JjkRyu.stateFor(p).action.count)}finally{A.pause()}}
  count();for(let i=0;i<2;i++){const c=offer().find(c=>c.key==='stat:quantity');assert(c,'missing useful/carry quantity card');out.previews.push(c.desc);c.apply(p);count()}
  assert(out.counts.join(',')==='3,3,4','quantity does not use exact multiplicative carry '+out.counts);
  assert(/[→⇒]/.test(out.previews[0]),'quantity lacks current-to-next preview');
  p.quantityPicks=p.quantityBonus=20;assert(!has('quantity'),'all consumers at count cap still offered quantity');out.atCap=true;
 }
 return out;
}"""

PULSES=r"""() => {
 const A=JAcceptance,p=A.p(),P=G.CombatPulse,assert=A.assert;assert(P,'pulse engine missing');A.reset();
 p.level=30;p.statsTaken={};p.damageSplashPicks=1;p.percentHealthDamage=0;p.lifestealRate=0;
 const move=p.moves[0],out={};
 function run(reverse=false){A.reset();p.damageSplashPicks=1;
  const a=A.spawn(100,0),b=A.spawn(115,0),outer=A.spawn(110,50),far=A.spawn(110,120);
  const packet=P.create(p,move.id,{channel:'body'}),hits=[{target:a,primaryDirectDamage:100,color:'#fff',dx:1,dy:0,knock:0},{target:b,primaryDirectDamage:200,color:'#fff',dx:1,dy:0,knock:0}];
  A.resume();try{P.apply(packet,0,reverse?hits.slice().reverse():hits)}finally{A.pause()}
  const losses=[a.maxHp-a.hp,b.maxHp-b.hp,outer.maxHp-outer.hp,far.maxHp-far.hp];
  assert(losses.join(',')==='100,200,20,0','primary mutual-splash or outer max violated '+losses);
  A.resume();try{P.apply(packet,0,hits)}finally{A.pause()};assert(outer.maxHp-outer.hp===20&&a.maxHp-a.hp===100,'same contact duplicate damage');
  A.resume();try{P.apply(packet,1,hits)}finally{A.pause()};assert(outer.maxHp-outer.hp===40&&a.maxHp-a.hp===200,'second real contact suppressed');
  return losses;
 }
 out.forward=run();out.reverse=run(true);
 A.reset();p.damageSplashPicks=1;p.lifestealRate=.1;p.hp=80;
 const a=A.spawn(100,0),b=A.spawn(115,0),outer=A.spawn(110,50),packet=P.create(p,move.id,{channel:'body'});
 A.resume();try{P.apply(packet,0,[{target:a,primaryDirectDamage:100},{target:b,primaryDirectDamage:200}])}finally{A.pause()}
 assert(Math.abs(p.hp-110)<1e-6,'secondary damage triggered healing '+p.hp);out.healing=p.hp-80;
 A.reset();p.damageSplashPicks=1;p.percentHealthDamage=.01;
 const primary=A.spawn(100,0),secondary=A.spawn(110,50),q=P.create(p,move.id,{channel:'body'});
 A.resume();try{P.apply(q,0,[{target:primary,primaryDirectDamage:100}])}finally{A.pause()}
 assert(secondary.maxHp-secondary.hp===10,'secondary inherited percentage-health bonus');out.secondaryLoss=secondary.maxHp-secondary.hp;
 const old=P.create(p,move.id,{channel:'body'}),untouched=A.spawn(200,0);const epoch=P.epoch;P.beginRun();
 A.resume();try{P.apply(old,0,[{target:untouched,primaryDirectDamage:100}])}finally{A.pause()}
 assert(P.epoch!==epoch&&untouched.hp===untouched.maxHp,'stale run pulse accepted');out.epochRejected=true;
 A.reset();const clone=G.SelfClones.summon(p),victim=A.spawn(100,0),host=P.create(p,move.id),copy=P.create(clone,move.id),direct=100*p.atk,copied=100*clone.atk;
 assert(host.ownerId!==copy.ownerId,'different actors share one pulse owner identity');A.resume();try{P.apply(host,0,[{target:victim,primaryDirectDamage:direct}]);P.apply(copy,0,[{target:victim,primaryDirectDamage:copied}])}finally{A.pause()}
 assert(victim.maxHp-victim.hp===Math.round(direct)+Math.round(copied),'clone direct damage suppressed or scaled twice');out.clone={direct,copied,actual:victim.maxHp-victim.hp};
 A.reset();p.damageSplashPicks=1;const front=A.spawn(100,0),blocked=A.spawn(110,50),wallPacket=P.create(p,move.id),wall=G.World.isWall;
 G.World.isWall=(x,y)=>y>20&&y<30;A.resume();try{P.apply(wallPacket,0,[{target:front,primaryDirectDamage:100}])}finally{A.pause();G.World.isWall=wall};
 assert(front.maxHp-front.hp===100&&blocked.hp===blocked.maxHp,'outer splash crossed blocking wall');out.wallBlocked=true;
 A.reset();const pausedTarget=A.spawn(100,0),paused=P.create(p,move.id);assert(P.apply(paused,0,[{target:pausedTarget,primaryDirectDamage:100}])===false&&pausedTarget.hp===pausedTarget.maxHp,'paused pulse was accepted');
 A.resume();try{P.apply(paused,0,[{target:pausedTarget,primaryDirectDamage:100}])}finally{A.pause()};assert(pausedTarget.maxHp-pausedTarget.hp===100,'paused refusal consumed future legal contact');
 const dead=P.create(p,move.id);p.dead=true;A.resume();try{assert(P.apply(dead,0,[{target:pausedTarget,primaryDirectDamage:100}])===false,'dead owner pulse accepted')}finally{A.pause();p.dead=false};out.pausedAndDeadRejected=true;
 return out;
}"""

MANIFEST=r"""() => {
 const A=JAcceptance,p=A.p(),Y=G.JujutsuYuta,assert=A.assert,out=[];
 for(const cd of [1,.76*.92**10]){
  A.reset();const m=A.fixture('jjk-yuta-manifest'),e=A.spawn(100,0);p.cdMul=cd;p.target=e;
  A.cast(m.id);assert(Y.manifested(p),'manifest did not start');const initial=m.t;
  A.advance(6.02,true);assert(!Y.manifested(p),'manifest active period exceeded six seconds');
  const gap=m.t;assert(gap>0,'manifest became permanent at high CDR');const casts=Y.inspect(p).casts.manifest;
  A.advance(Math.max(.01,gap-.03),true);assert(Y.inspect(p).casts.manifest===casts,'manifest recast before recovery end');
  A.advance(.08,true);assert(Y.inspect(p).casts.manifest>casts,'manifest never resumed after recovery');out.push({cd,initial,gap});
 }
 return out;
}"""

BONDS=r"""() => {
 const A=JAcceptance,p=A.p(),F=G.JujutsuGrowth,assert=A.assert;
 assert(F?.bondState,'reward capability API missing');p.level=1;
 const before=JSON.stringify({moves:p.moves.map(m=>[m.id,m.lvl]),slots:p.slots.map(g=>g.map(m=>m.id)),hp:p.hp,bonds:p.bonds});
 const state=F.bondState(p);
 assert(before===JSON.stringify({moves:p.moves.map(m=>[m.id,m.lvl]),slots:p.slots.map(g=>g.map(m=>m.id)),hp:p.hp,bonds:p.bonds}),'capability preview mutated player');
 return {dex:p.dex,state};
}"""

FUNCTIONAL=r"""slug => {
 const A=JAcceptance,p=A.p(),assert=A.assert,out={};
 function cast(id,rank,setup,seconds){A.reset();const m=A.fixture(id,rank),objects=setup();p.target=objects[0];A.cast(id);A.advance(seconds);return {m,objects};}
 if(slug==='yuta'){
  const arc=rank=>{const r=cast('jjk-yuta',rank,()=>[A.spawn(65,0),A.spawn(120*Math.cos(1.18),120*Math.sin(1.18))],.3);return r.objects[1].maxHp-r.objects[1].hp};
  out.arc=[arc(1),arc(5)];assert(out.arc[0]===0&&out.arc[1]>0,'Yuta fifth rank has no actual wider cleave');
  A.reset();A.fixture('jjk-yuta',3);const marked=A.spawn(100,0);p.target=marked;A.cast('jjk-yuta');A.advance(.2);
  assert(G.JujutsuYuta.inspect(p).relay?.target===marked,'blade rank3 did not create relay mark');
  p.addMove('jjk-yuta-rika');const closer=A.spawn(45,0);A.cast('jjk-yuta-rika');const r=G.JujutsuYuta.inspect(p).rika;
  assert(r&&r.tx>55,'Rika ignored marked target for newly closer enemy');out.relayDestination=r.tx;
  const speed=rank=>{A.reset();A.fixture('jjk-yuta-rika',rank);p.target=A.spawn(250,0);A.cast('jjk-yuta-rika');A.advance(.2);return G.JujutsuYuta.inspect(p).rika.x};
  out.travel=[speed(1),speed(3)];assert(out.travel[1]>out.travel[0]*1.15,'Rika rank3 travel speed not consumed');
  const radius=rank=>{const r=cast('jjk-yuta-rika',rank,()=>[A.spawn(170,0),A.spawn(135,120)],1.5);return r.objects[1].maxHp-r.objects[1].hp};
  out.rikaRadius=[radius(1),radius(5)];assert(out.rikaRadius[0]===0&&out.rikaRadius[1]>0,'Rika rank5 radius not functional');
  const speech=rank=>{const r=cast('jjk-yuta-speech',rank,()=>[A.spawn(100,0),A.spawn(175,0)],.3);return r.objects[1].maxHp-r.objects[1].hp};
  out.speechRadius=[speech(1),speech(5)];assert(out.speechRadius[0]===0&&out.speechRadius[1]>0,'speech rank5 range not functional');
  const duration=rank=>{const r=cast('jjk-yuta-speech',rank,()=>[A.spawn(100,0)],1.55),e=r.objects[0];e.spd=60;const x=e.x;A.resume();try{e.update(.1,p,0)}finally{A.pause()}return Math.abs(e.x-x)};
  out.speechDuration=[duration(1),duration(3)];assert(out.speechDuration[0]>0&&out.speechDuration[1]===0,'speech rank3 control duration not consumed');
  out.recovery=[];for(const rank of [1,3,5]){A.reset();const m=A.fixture('jjk-yuta-manifest',rank);p.target=A.spawn(100,0);A.cast(m.id);out.recovery.push(m.t)}
  assert(out.recovery[0]>out.recovery[1]&&out.recovery[1]>out.recovery[2],'manifest functional recovery ranks identical');
 }else if(slug==='ryu'){
  A.reset();let m=A.fixture('jjk-ryu',3),near=A.spawn(70,0),elite=A.spawn(170,70,'elite');p.target=near;A.cast(m.id);
  let f=G.JjkRyu.stateFor(p).action;assert(f.tx===elite.x&&f.ty===elite.y,'rank3 beam did not prefer reachable elite');out.elite={tx:f.tx,ty:f.ty};
  const reach=(id,rank,x)=>{A.reset();const m=A.fixture(id,rank);p.target=A.spawn(x,0);A.resume();try{return G.JjkRyu.canCast(p,m)}finally{A.pause()}};
  out.range=[reach('jjk-ryu',1,400),reach('jjk-ryu',5,400),reach('jjk-ryu-maximum',1,480),reach('jjk-ryu-maximum',5,480)];
  assert(out.range.join(',')==='false,true,false,true','rank5 artillery reach not used '+out.range);
  const fan=rank=>{const r=cast('jjk-ryu-spread',rank,()=>[A.spawn(85,0),A.spawn(160*Math.cos(.38),160*Math.sin(.38))],.5);return r.objects[1].maxHp-r.objects[1].hp};
  out.spreadArc=[fan(1),fan(3)];assert(out.spreadArc[0]===0&&out.spreadArc[1]>0,'spread rank3 angular coverage unchanged');
  A.reset();m=A.fixture('jjk-ryu-spread',5);p.target=A.spawn(120,0);A.cast(m.id);out.baseCount=G.JjkRyu.stateFor(p).action.count;assert(out.baseCount===4,'rank5 spread does not start four rays');
  const blast=rank=>{const r=cast('jjk-ryu-impact',rank,()=>[A.spawn(180,0),A.spawn(200,105)],.7);return r.objects[1].maxHp-r.objects[1].hp};
  out.blastRadius=[blast(1),blast(3)];assert(out.blastRadius[0]===0&&out.blastRadius[1]>0,'impact rank3 radius not functional');
  A.reset();m=A.fixture('jjk-ryu-impact',5);near=A.spawn(60,0);const cluster=[A.spawn(220,0),A.spawn(225,35),A.spawn(225,-35)];p.target=near;A.cast(m.id);
  f=G.JjkRyu.stateFor(p).action;assert(f.tx>180,'rank5 impact ignored dense reachable group');out.cluster={tx:f.tx,ty:f.ty};
  const first=cast('jjk-ryu-maximum',3,()=>[A.spawn(100,0),A.spawn(200,0)],1);const losses=first.objects.map(e=>e.maxHp-e.hp);assert(losses[0]>losses[1]*1.1&&losses[0]<losses[1]*1.2,'rank3 maximum first-target bonus absent');out.firstTarget=losses;
 }else{
  const arc=(id,rank,a)=>{const r=cast(id,rank,()=>[A.spawn(75,0),A.spawn(150*Math.cos(a),150*Math.sin(a))],.6);return r.objects[1].maxHp-r.objects[1].hp};
  out.skyArc=[arc('jjk-uro',1,.62),arc('jjk-uro',3,.62)];assert(out.skyArc[0]===0&&out.skyArc[1]>0,'rank3 sky arc unchanged');
  out.thinArc=[arc('jjk-uro-thin-ice',1,1.05),arc('jjk-uro-thin-ice',3,1.05)];assert(out.thinArc[0]===0&&out.thinArc[1]>0,'rank3 thin-ice arc unchanged');
  A.reset();A.fixture('jjk-uro',5);const knocks=[],ordinary=A.spawn(80,0),special=A.spawn(110,20,'boss');
  for(const e of [ordinary,special]){const native=e.hurt;e.hurt=function(...args){knocks.push({boss:!!this.boss,knock:args[4]});return native.apply(this,args)}}p.target=ordinary;A.cast('jjk-uro');A.advance(.3);
  assert(knocks.find(k=>!k.boss)?.knock===18&&knocks.find(k=>k.boss)?.knock===0,'rank5 sky push ignored or moved boss');out.skyKnock=knocks;
  const r=cast('jjk-uro-thin-ice',5,()=>[A.spawn(80,0),A.spawn(110,20,'boss')],.36);
  out.thinSlow=r.objects.map(e=>({slow:e.slow,time:e.slowT}));assert(out.thinSlow[0].slow>=.25&&out.thinSlow[1].slow<out.thinSlow[0].slow,'rank5 thin slow/boss resistance absent');
  const collapse=rank=>{const r=cast('jjk-uro-collapse',rank,()=>[A.spawn(180,0),A.spawn(180,130)],.7);return r.objects[1].maxHp-r.objects[1].hp};
  out.collapseRadius=[collapse(1),collapse(3)];assert(out.collapseRadius[0]===0&&out.collapseRadius[1]>0,'rank3 collapse radius unchanged');
  const fifth=cast('jjk-uro-collapse',5,()=>[A.spawn(100,0),A.spawn(120,30,'boss')],.56);out.collapseSlow=fifth.objects.map(e=>({slow:e.slow,time:e.slowT}));
  assert(out.collapseSlow[0].slow===.6&&out.collapseSlow[0].time===.8&&out.collapseSlow[1].slow===.15&&out.collapseSlow[1].time===.45,'rank5 collapse slow/boss timing contract incorrect');
  A.reset();let m=A.fixture('jjk-uro-screen',3);p.target=A.spawn(70,0);A.resume();let noThreat;try{noThreat=G.JjkUro.canCast(p,m)}finally{A.pause()};assert(!noThreat,'rank3 screen wasted on enemy with no incoming projectile');
  G.Projectiles.spawn({x:180,y:0,vx:-200,vy:0,friendly:false,dmg:8,mtype:'psychic',life:2,r:6});A.resume();let threatened;try{threatened=G.JjkUro.canCast(p,m)}finally{A.pause()};assert(threatened,'rank3 screen failed real incoming threat');out.threatOnly={noThreat,threatened};
  const baseThin=cast('jjk-uro-thin-ice',1,()=>[A.spawn(100,0)],.5);const baseDamage=baseThin.objects[0].maxHp-baseThin.objects[0].hp;
  A.reset();m=A.fixture('jjk-uro-screen',5);p.target=A.spawn(100,0);G.Projectiles.spawn({x:180,y:0,vx:-200,vy:0,friendly:false,dmg:8,mtype:'psychic',life:2,r:6});A.cast(m.id);
  G.Projectiles.spawn({x:60,y:0,px:120,py:0,vx:-100,vy:0,friendly:false,dmg:7,mtype:'psychic',life:2});A.resume();try{G.JjkUro.intercept()}finally{A.pause()};
  let s=G.JjkUro.stateFor(p);assert(s.counterBonus===.15,'rank5 actual intercept did not grant one counter bonus');G.Projectiles.clear();p.addMove('jjk-uro-thin-ice');A.advance(.45);A.cast('jjk-uro-thin-ice');
  s=G.JjkUro.stateFor(p);assert(s.counterBonus===0&&s.counterUntil===0,'counter bonus not consumed by next thin ice');const hp=p.target.hp;A.advance(.5);const boosted=hp-p.target.hp;
  assert(boosted>baseDamage*1.13&&boosted<baseDamage*1.17,'rank5 counter flag did not strengthen actual next hit');out.counterOnce={baseDamage,boosted};
 }
 return out;
}"""

CAPABILITY=r"""({full,expected})=>{
 const A=JAcceptance,p=A.p(),F=G.JujutsuGrowth,assert=A.assert;
 if(full){p.level=30;const c=G.NarutoSkillCatalog,signature=c.byDex.get(p.dex);for(const id of [signature?.id,...(c.extraPools.get(p.dex)||[])].filter(Boolean))if(!p.hasMove(id))p.addMove(id)}
 p.bonds=1;const before={level:p.level,moves:p.moves.map(m=>m.id+':'+m.lvl),slots:p.slots.map(g=>g.map(m=>m.id)),hp:p.hp,clones:G.SelfClones.actors().length};
 const state=F.bondState(p);assert(state.mode===expected,'reward capability '+p.dex+' expected '+expected+' actual '+state.mode);
 const after={level:p.level,moves:p.moves.map(m=>m.id+':'+m.lvl),slots:p.slots.map(g=>g.map(m=>m.id)),hp:p.hp,clones:G.SelfClones.actors().length};assert(JSON.stringify(before)===JSON.stringify(after),'reward preview changed native player/actors');
 if(expected==='growth'){const card=state.options[0],level=p.level;assert(card&&F.applyBondCard(p,card),'fallback native card could not spend bond');assert(p.bonds===0&&p.level===level,'reward spent wrong amount/added level');assert(!F.applyBondCard(p,card),'same reward card spent twice')}
 return {dex:p.dex,mode:state.mode,slots:p.slots.length,reason:state.reason};
}"""

LEGACY_QUANTITY=r"""()=>{
 const A=JAcceptance,p=A.p(),assert=A.assert,F=G.JujutsuGrowth;A.reset();A.fixture('naruto-sand-shield');p.level=20;p.quantityPicks=p.quantityBonus=0;p.statsTaken={};
 const native=G.NarutoSandGuard.state(p),before=native.count,benefit=F.quantityBenefit(p),consumer=benefit.consumers.find(c=>c.id==='naruto-sand-shield');
 assert(consumer&&benefit.eligible,'actual gaara-shield guardian generator falsely has no quantity benefit');
 const card=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');assert(card,'guardian-only player cannot select useful quantity');card.apply(p);
 const after=G.NarutoSandGuard.state(p).count;assert(before===consumer.before['砂護衛']&&after===consumer.after['砂護衛']&&after>before,'guardian preview diverges from native count');return {before,after,consumer};
}"""

FEEDBACK=r"""()=>{
 const A=JAcceptance,p=A.p(),assert=A.assert,I=G.RunInsights;A.reset();p.hp=p.maxHp;p.invuln=0;
 const e=A.spawn(5,0);e.dmg=10;e.atkType='normal';A.resume();try{G.Combat.resolve(.01,p,0)}finally{A.pause()};
 p.invuln=0;G.EnemyMgr.clear();G.Projectiles.spawn({x:p.x,y:p.y,vx:1,vy:0,friendly:false,dmg:10,mtype:'normal',life:1,r:6});A.resume();try{G.Combat.resolve(.01,p,0)}finally{A.pause()};
 G.Hazards.add({kind:'zone',x:p.x,y:p.y,r:40,delay:0,dmg:10,type:'normal',color:'#ff44aa'});A.resume();try{G.Hazards.update(.01)}finally{A.pause()};
 const s=I.snapshot();for(const key of ['近身碰撞','敵方飛彈','地面危險'])assert(s.received[key]>0,'native damage cause missing '+key);return s;
}"""

PRODUCTION_VFX=r"""async quality=>{
 const A=JAcceptance,p=A.p(),assert=A.assert,V=G.JujutsuVFX;assert(V,'procedural VFX module missing');
 G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();G.SelfClones.clear();p.level=30;
 for(const id of ['jjk-uro-thin-ice','jjk-uro-screen','jjk-uro-collapse'])if(!p.hasMove(id))assert(p.addMove(id),'native VFX skill learn');
 // The world is untouched: this test deliberately never calls A.reset().
 let target=null;for(let i=0;i<16&&!target;i++){const a=i*Math.PI/8,x=p.x+Math.cos(a)*80,y=p.y+Math.sin(a)*80;
  if(G.World.isFree(x,y,15,true)&&G.World.projectilePathClear(p.x,p.y,x,y,null,{radius:1,spacing:5,includeStart:false})){
   target=new G.Enemy({dex:19,hp:1000000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});G.EnemyMgr.add(target);}}
 assert(target,'no reachable native-world reference target');G.EnemyMgr.rebuildGrid();
 for(let i=0;i<3;i++)G.SelfClones.summon(p);const actors=[p,...G.SelfClones.actors()];
 A.resume();try{for(const owner of actors){const m=owner.moves.find(m=>m.id==='jjk-uro-thin-ice');m.t=0;assert(G.JjkUro.cast(owner,m),'native owner fold cast failed')}}finally{A.pause()};A.advance(.2);
 V.setQuality(quality);const game=document.getElementById('game'),main=game.getContext('2d'),proto=CanvasRenderingContext2D.prototype;
 const original={ground:G.World.drawGround,liquid:G.World.drawLiquid,bg:V.drawBackground,hazards:G.Hazards.draw,player:G.Player.prototype.draw,image:proto.drawImage};
 let events=[],composites=0,captures=[],frameDiff=0,marks={};const colors=[[237,0,201],[18,101,237]];
 const marker=(ctx,x,y,color,key)=>{ctx.save();ctx.globalAlpha=1;ctx.fillStyle=color;ctx.fillRect(x-3,y-3,6,6);const m=ctx.getTransform();marks[key]={x:m.a*x+m.c*y+m.e,y:m.b*x+m.d*y+m.f};ctx.restore()};
 G.World.drawGround=function(...args){events=[];composites=0;return original.ground.apply(this,args)};
 G.World.drawLiquid=function(...args){events.push('liquid');return original.liquid.apply(this,args)};
 V.drawBackground=function(ctx){events.push('fold');const before=ctx.getImageData(0,0,game.width,game.height).data,result=original.bg.call(this,ctx),after=ctx.getImageData(0,0,game.width,game.height).data;frameDiff=0;for(let i=0;i<after.length;i+=4)if(before[i]!==after[i]||before[i+1]!==after[i+1]||before[i+2]!==after[i+2])frameDiff++;return result};
 G.Hazards.draw=function(ctx,...args){events.push('hazard');const r=original.hazards.call(this,ctx,...args);marker(ctx,p.x+80,p.y+70,'#ed00c9','hazard');return r};
 G.Player.prototype.draw=function(ctx,...args){const r=original.player.call(this,ctx,...args);if(this===p){events.push('player');marker(ctx,p.x+80,p.y+40,'#1265ed','player')}return r};
 proto.drawImage=function(image,...args){const capture=image===game&&this.canvas!==game,result=original.image.call(this,image,...args);
  if(capture){const data=this.getImageData(0,0,this.canvas.width,this.canvas.height).data;let forbidden=0;for(let i=0;i<data.length;i+=4)if(colors.some(c=>c.every((v,j)=>v===data[i+j])))forbidden++;
   captures.push({before:events.slice(),width:this.canvas.width,height:this.canvas.height,forbiddenPixels:forbidden});}
  if(this.canvas===game&&image.dataset?.source==='procedural-jjk-fold')composites++;return result};
 try{
  for(let i=0;i<4;i++)await new Promise(r=>requestAnimationFrame(r));
  const info=V.inspect(),limit=quality==='low'?12:48,cap=quality==='low'?1:2;
  assert(captures.length===cap,'actual native snapshot budget/capture mismatch '+captures.length);
  assert(captures.every(c=>!c.before.includes('hazard')&&!c.before.includes('player')&&c.forbiddenPixels===0),'captured foreground actors/hazards');
  assert(events.indexOf('liquid')<events.indexOf('fold')&&events.indexOf('fold')<events.indexOf('hazard')&&events.indexOf('hazard')<events.indexOf('player'),'native production draw stage order wrong '+events);
  assert(composites>0&&composites<=limit&&info.triangles===composites,'actual textured-triangle calls not bounded/match');
  assert(frameDiff>20,'production background did not visibly change');assert(info.shards<=24&&info.snapshots<=cap,'global VFX budget exceeded');
  const count=info.capturesTotal;G.Camera.x+=15;for(let i=0;i<2;i++)await new Promise(r=>requestAnimationFrame(r));assert(V.inspect().capturesTotal===count,'paused/camera change recaptured same cast');
  const enabledInfo=V.inspect(),enabledComposites=composites,enabledOrder=events.slice(),enabledChanges=frameDiff,captureCount=captures.length;
  V.enabled=false;for(let i=0;i<3;i++)await new Promise(r=>requestAnimationFrame(r));const disabled=V.inspect();
  assert(captures.length===captureCount&&composites===0&&disabled.triangles===0&&disabled.shards===0&&disabled.draws.length===0,'disabled procedural renderer still captured/composited geometry');
  return {quality,actualCaptures:captures,actualComposites:enabledComposites,actualFrameOrder:enabledOrder,pixelChanges:enabledChanges,info:enabledInfo,markerPositions:marks,disabled:{captures:captures.length-captureCount,composites,triangles:disabled.triangles,shards:disabled.shards,draws:disabled.draws.length}};
 }finally{V.enabled=true;G.World.drawGround=original.ground;G.World.drawLiquid=original.liquid;V.drawBackground=original.bg;G.Hazards.draw=original.hazards;G.Player.prototype.draw=original.player;proto.drawImage=original.image;}
}"""

MILESTONE_SETUP=r"""()=>{
 const A=JAcceptance,p=A.p(),assert=A.assert;A.reset();p.bosses=99;G.Game.debugTime(900);
 A.resume();try{G.Combat.updateFields(.01)}finally{A.pause()};assert(!document.getElementById('council-choice'),'clock900/boss count opened milestone');
 const other=A.spawn(50,0,'boss');other.mainBossSlot=3;other.die();A.resume();try{G.EnemyMgr.update(.01,[p]);G.Combat.updateFields(.01)}finally{A.pause()};assert(!document.getElementById('council-choice'),'wrong main boss opened fifth milestone');
 const fifth=A.spawn(80,0,'boss');fifth.mainBossSlot=4;fifth.die();A.resume();G.Combat.updateFields(.01);assert(!document.getElementById('council-choice'),'milestone opened before fifth boss accounting');
 G.EnemyMgr.update(.01,[p]);G.Combat.updateFields(.01);assert(!!document.getElementById('council-choice'),'accounted fifth boss did not open milestone');return G.RunInsights.snapshot();
}"""

STRESS=r"""async cloneCount=>{
 const A=JAcceptance,p=A.p(),assert=A.assert;A.reset();p.level=30;p.maxHp=p.hp=100000;p.xpNext=1e12;
 for(const row of G.Jujutsu.kits.find(([dex])=>dex===p.dex)[1])if(!p.hasMove(row[0]))p.addMove(row[0]);
 for(const m of p.moves)Object.assign(m,G.Moves.instance(m.id,5));p.arrange();p.quantityPicks=p.quantityBonus=20;p.cdMul=.76*.92**10;p.damageSplashPicks=3;p.percentHealthDamage=.01;p.lifestealRate=.01;
 for(let i=0;i<64;i++){const a=i*Math.PI*2/64,r=90+(i%5)*28,behavior=['chase','ranged','fan','beamer'][i%4];
  const e=new G.Enemy({dex:19,hp:1000000000,spd:32,dmg:4,xp:0,behavior,shotCd:1.4,shotDmg:4,range:260},Math.cos(a)*r,Math.sin(a)*r,{hp:1,spd:1,dmg:1});
  const native=e.hurt;e.hurt=function(...args){const result=native.apply(this,args);if(!this.dead)this.hp=this.maxHp;return result};G.EnemyMgr.add(e);}
 for(let i=0;i<cloneCount;i++)G.SelfClones.summon(p);G.EnemyMgr.rebuildGrid();
 const times=[],dt=1/60,begin=performance.now();let moved=0;A.resume();
 try{for(let i=0;i<600;i++){const start=performance.now(),before=G.EnemyMgr.all().map(e=>[e.x,e.y]);
   p.update(dt);G.Path.update(dt,[p]);G.EnemyMgr.update(dt,[p]);G.EnemyMgr.rebuildGrid();G.Combat.tick(dt,p,i*dt);G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,i*dt);G.Combat.updateFields(dt);G.Hazards.update(dt);G.FX.update(dt);
   if(i===0)moved=G.EnemyMgr.all().filter((e,j)=>Math.hypot(e.x-before[j][0],e.y-before[j][1])>0).length;times.push(performance.now()-start);}
  assert(moved>0&&G.EnemyMgr.all().filter(e=>!e.dead).length===64,'stress fixture lost moving native enemy load');assert(G.SelfClones.actors().length===cloneCount,'stress cloned actors disappeared');
  const intervals=[],metrics={maxTriangles:0,maxSnapshots:0,maxShards:0,maxBeams:0,maxProjectiles:0};let last=performance.now();
  for(let i=0;i<90;i++){await new Promise(r=>requestAnimationFrame(r));const now=performance.now();if(i)intervals.push(now-last);last=now;
   const v=G.JujutsuVFX.inspect();metrics.maxTriangles=Math.max(metrics.maxTriangles,v.triangles);metrics.maxSnapshots=Math.max(metrics.maxSnapshots,v.snapshots);metrics.maxShards=Math.max(metrics.maxShards,v.shards);metrics.maxBeams=Math.max(metrics.maxBeams,v.beamProfiles);metrics.maxProjectiles=Math.max(metrics.maxProjectiles,G.Projectiles.all().length);}
  const low=innerWidth<=700||G.Touch.active;assert(metrics.maxTriangles<=(low?12:48)&&metrics.maxSnapshots<=(low?1:2)&&metrics.maxShards<=24,'global decorative resource cap exceeded');
  times.sort((a,b)=>a-b);intervals.sort((a,b)=>a-b);const pct=(a,p)=>a[Math.min(a.length-1,Math.floor(a.length*p))];
  return {scope:'10 simulated seconds plus90 native RAF frames;64 moving native enemies retained by refilling HP after real hurt, high player HP. Performance fixture, not balance.',cloneCount,dpr:devicePixelRatio,width:innerWidth,moved,wallMs:performance.now()-begin,update:{p50:pct(times,.5),p95:pct(times,.95),p99:pct(times,.99),max:times.at(-1)},render:{p50:pct(intervals,.5),p95:pct(intervals,.95),p99:pct(intervals,.99),max:intervals.at(-1)},metrics};
 }finally{A.pause();}
}"""

def natural_attempt(page,frame,out):
    frame.evaluate("""()=>{window.CouncilLiveOffers=[];const show=G.RunUI.showLevelUp;G.RunUI.showLevelUp=function(level,list,...args){window.CouncilLiveOffers=list.map(c=>({key:c.key,type:c.type,guaranteed:!!c.guaranteed,title:c.title}));return show.call(this,level,list,...args)};JAcceptance.resume()}""")
    started=time.monotonic();held=set();samples=[];choices=[];last=-1
    while time.monotonic()-started<125:
        data=frame.evaluate("""()=>{const p=G.Game.player,state=G.Game.state,enemies=G.EnemyMgr.all().filter(e=>!e.dead);const out={state,time:G.Game.st.time,level:p.level,hp:p.hp,maxHp:p.maxHp,kills:p.kills,bosses:p.bosses,mainBosses:enemies.filter(e=>e.mainBossSlot!=null).map(e=>({slot:e.mainBossSlot,hp:e.hp,maxHp:e.maxHp})),stats:{...p.statsTaken}};
          if(state==='levelup'){out.offers=window.CouncilLiveOffers;return out}if(state!=='playing')return out;
          const xp=G.Pickups.all().filter(a=>['xp','xpBig'].includes(a.kind)).sort((a,b)=>Math.hypot(a.x-p.x,a.y-p.y)-Math.hypot(b.x-p.x,b.y-p.y))[0];
          const target=xp||enemies.sort((a,b)=>Math.hypot(a.x-p.x,a.y-p.y)-Math.hypot(b.x-p.x,b.y-p.y))[0]||p;let best={score:-Infinity,x:0,y:0};
          for(let n=0;n<9;n++){const a=n*Math.PI/4,dx=n===8?0:Math.cos(a),dy=n===8?0:Math.sin(a),x=p.x+dx*30,y=p.y+dy*30;if(!G.World.isFree(x,y,p.r,true))continue;
            const d=enemies.length?Math.min(...enemies.map(e=>Math.hypot(e.x-x,e.y-y))):200;let score=-Math.hypot(target.x-x,target.y-y)*.03+Math.min(120,d)*.06-Math.max(0,62-d)*1.1;
            for(const h of G.Hazards.all)if(!h.hit&&G.Hazards.inside(h,x,y,p.r))score-=120;
            for(const shot of G.Projectiles.all())if(!shot.friendly&&Math.hypot(shot.x+shot.vx*.2-x,shot.y+shot.vy*.2-y)<p.r+(shot.r||6)+8)score-=80;
            if(score>best.score)best={score,x:dx,y:dy};}
          out.keys=[...(Math.abs(best.x)>.3?[best.x>0?'KeyD':'KeyA']:[]),...(Math.abs(best.y)>.3?[best.y>0?'KeyS':'KeyW']:[])];return out;}""")
        if int(data['time']//30)>last:
            last=int(data['time']//30);samples.append(data);page.screenshot(path=str(out/f'natural-yuta-{last*30}s.png'));print('natural',round(data['time']),data['level'],data['hp'],flush=True)
        if data['state']=='over' or data['time']>=185:break
        if data['state']=='levelup':
            offers=data.get('offers',[]);priority=['stat:heal','stat:maxHealthPercent','stat:lifesteal','stat:def'] if data['hp']<data['maxHp']*.55 else ['up:jjk-yuta-rika','up:jjk-yuta','stat:lifesteal','stat:atk','stat:cd']
            index=next((i for i,c in enumerate(offers) if c['guaranteed']),None)
            if index is None:index=next((i for key in priority for i,c in enumerate(offers) if c['key']==key),0)
            choices.append({'time':data['time'],'level':data['level'],'offers':offers,'chosen':index});frame.locator('#cards .card').nth(index).click()
        elif data['state'] not in ['playing','paused']:
            samples.append({'stoppedForPrompt':data});break
        desired=set(data.get('keys',[]))
        for k in held-desired:page.keyboard.up(k)
        for k in desired-held:page.keyboard.down(k)
        held=desired;page.wait_for_timeout(75)
    for k in held:page.keyboard.up(k)
    page.screenshot(path=str(out/'natural-yuta-end.png'))
    return {'scope':'One normal level1 native keyboard/card-choice agent attempt, no clock/stat/world/XP injection; automated heuristic not a human study. Default2x game speed.','wallSeconds':time.monotonic()-started,'samples':samples,'choices':choices,'final':data,'firstMainBossReached':any(s.get('mainBosses') for s in samples)}

def boot(context,dex,out,url):
    page=context.new_page();errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:requests.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
    slug='jjk-'+HEROES[dex] if dex in HEROES else {30001:'naruto',30007:'gaara',30010:'pain',30011:'temari',30012:'kimimaro'}[dex]
    wide='&layout=wide' if (page.viewport_size or {}).get('width',0)>=700 and 'layout=' not in url else ''
    page.goto(url+'&hero='+slug+wide);frame=base.frame_for(page)
    frame.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if frame.locator('#tap-start').is_visible():frame.locator('#tap-start').click()
    frame.locator(f'[data-quick-naruto="{dex}"]').click();frame.locator('#scr-menu [data-go="play"]').click()
    frame.wait_for_function(f'G.Game.state==="playing"&&G.Game.player?.dex==={dex}')
    frame.evaluate(base.SETUP)
    return page,frame,errors,requests

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--url',default=os.getenv('COUNCIL_URL','http://127.0.0.1:8337/.omx/digimon.html?lang=zh-TW'))
    ap.add_argument('--out',default=str(ROOT/'.omx/state/council-runtime/final'));ap.add_argument('--checks',default='cards,pulses,manifest,bonds,functional,capability,legacyquantity,feedback,production,choices,presets,stress');args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True);selected=set(args.checks.split(','))
    report={'url':args.url,'sourceHashes':runtime_hashes(args.url),'cases':{},'failures':[],'errors':[],'missing':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
        for dex,slug in HEROES.items():
            ctx=browser.new_context(viewport={'width':1280,'height':900},service_workers='block')
            page,f,errors,missing=boot(ctx,dex,out,args.url)
            for name,code in [('cards',CARDS),('pulses',PULSES),('manifest',MANIFEST),('bonds',BONDS),('functional',FUNCTIONAL),('feedback',FEEDBACK)]:
                if name not in selected or (name in ['pulses','manifest','feedback'] and slug!='yuta'):continue
                key=slug+'-'+name;print(key,flush=True)
                try:report['cases'][key]=f.evaluate(code,slug) if name=='functional' else f.evaluate(code)
                except Exception as e:
                    report['failures'].append(key+': '+str(e));page.screenshot(path=str(out/(key+'-failure.png')))
            report['errors'].extend(errors);report['missing'].extend(missing);ctx.close()
            (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        if 'capability' in selected:
            for dex,full,expected in [(30011,False,'bank'),(30011,True,'fusion'),(30007,True,'fusion'),(30001,True,'growth'),(30010,True,'growth'),(30012,True,'growth'),(30013,True,'growth')]:
                ctx=browser.new_context(viewport={'width':1280,'height':900},service_workers='block');page,f,errors,missing=boot(ctx,dex,out,args.url);key=f'capability-{dex}-{full}'
                try:report['cases'][key]=f.evaluate(CAPABILITY,{'full':full,'expected':expected})
                except Exception as e:report['failures'].append(key+': '+str(e));page.screenshot(path=str(out/(key+'-failure.png')))
                report['errors'].extend(errors);report['missing'].extend(missing);ctx.close()
        if 'production' in selected:
            for quality,dpr,mobile in [('high',1,False),('low',2,True)]:
                ctx=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},device_scale_factor=dpr,is_mobile=mobile,has_touch=mobile,service_workers='block');page,f,errors,missing=boot(ctx,30015,out,args.url);key='production-'+quality
                try:
                    report['cases'][key]=f.evaluate(PRODUCTION_VFX,quality);page.screenshot(path=str(out/(key+'-clean.png')))
                except Exception as e:report['failures'].append(key+': '+str(e));page.screenshot(path=str(out/(key+'-failure.png')))
                report['errors'].extend(errors);report['missing'].extend(missing);ctx.close()
        if 'legacyquantity' in selected:
            ctx=browser.new_context(viewport={'width':1280,'height':900},service_workers='block');page,f,errors,missing=boot(ctx,30007,out,args.url)
            try:report['cases']['gaara-native-quantity']=f.evaluate(LEGACY_QUANTITY)
            except Exception as e:report['failures'].append('legacyquantity: '+str(e));page.screenshot(path=str(out/'legacyquantity-failure.png'))
            report['errors'].extend(errors);report['missing'].extend(missing);ctx.close()
        if 'choices' in selected:
            ctx=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,service_workers='block');page,f,errors,missing=boot(ctx,30013,out,args.url)
            try:
                f.evaluate('JAcceptance.p().bonds=1;JAcceptance.resume();G.Game.offerBond()');f.locator('#council-choice button').first.click()
                report['cases']['mastery-native-ui']=f.evaluate('({state:G.Game.state,bonds:G.Game.player.bonds})')
                assert report['cases']['mastery-native-ui']=={'state':'playing','bonds':0},'mastery UI did not spend exactly one/return playing'
                f.evaluate('G.Game.startRun()');f.evaluate(base.SETUP);report['cases']['milestone-negative-gates']=f.evaluate(MILESTONE_SETUP)
                page.screenshot(path=str(out/'milestone-mobile.png'));f.locator('#council-choice button',has_text='繼續挑戰').click()
                f.evaluate('G.Combat.updateFields(1)');assert not f.locator('#council-choice').count(),'milestone repeated after continue'
            except Exception as e:report['failures'].append('choices: '+str(e));page.screenshot(path=str(out/'choices-failure.png'))
            report['errors'].extend(errors);report['missing'].extend(missing);ctx.close()
        if 'presets' in selected:
            ctx=browser.new_context(viewport={'width':360,'height':800},is_mobile=True,has_touch=True,service_workers='block');page,f,errors,missing=boot(ctx,30013,out,args.url+'&startLevel=20')
            try:
                assert f.evaluate('G.Game.player.level===20&&G.Game.player.moves.every(m=>m.lvl===1)&&G.Game.player.trialBuild.mode==="skills"&&G.Game.player.trialBuild.picks.length===0'),'plain trial unexpectedly has preset investments'
                f.evaluate('G.Game.toUI();G.Flow.goMenu()');panel=f.locator('#trial-build-options');assert panel.is_visible(),'360px preset selector invisible'
                panel.locator('button',has_text='刀術接力').click();f.locator('[data-quick-naruto="30014"]').click()
                assert f.evaluate('new URLSearchParams(location.search).get("build")==="balanced"'),'incompatible hero preset was not normalized'
                page.screenshot(path=str(out/'preset-mobile-360.png'));f.locator('#scr-menu [data-go="play"]').click();f.wait_for_function('G.Game.state==="playing"&&G.Game.player?.dex===30014')
                data=f.evaluate('({level:G.Game.player.level,picks:G.Game.player.trialBuild.picks,route:G.Game.player.trialBuild.route,width:innerWidth,scroll:document.documentElement.scrollWidth})')
                assert data['level']==20 and len(data['picks'])==19 and sum(p['key'].startswith('new:') for p in data['picks'])==3,'preset free/missing legal card costs'
                assert all('before' in p and 'after' in p for p in data['picks']),'preset lacks before/after investment trace'
                assert data['scroll']<=data['width'],'360px horizontal overflow';report['cases']['native-preset-switch']=data
            except Exception as e:report['failures'].append('presets: '+str(e));page.screenshot(path=str(out/'presets-failure.png'))
            report['errors'].extend(errors);report['missing'].extend(missing);ctx.close()
        if 'stress' in selected:
            for dex,slug in HEROES.items():
                for dpr,mobile in [(1,False),(2,True)]:
                    for count in [0,2,6]:
                        key=f'stress-{slug}-dpr{dpr}-clones{count}';print(key,flush=True)
                        ctx=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},device_scale_factor=dpr,is_mobile=mobile,has_touch=mobile,service_workers='block');page,f,errors,missing=boot(ctx,dex,out,args.url)
                        try:report['cases'][key]=f.evaluate(STRESS,count)
                        except Exception as e:report['failures'].append(key+': '+str(e));page.screenshot(path=str(out/(key+'-failure.png')))
                        report['errors'].extend(errors);report['missing'].extend(missing);ctx.close()
                        (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        if 'natural' in selected:
            ctx=browser.new_context(viewport={'width':1280,'height':900},service_workers='block');page,f,errors,missing=boot(ctx,30013,out,args.url)
            try:report['cases']['natural-first-boss-attempt']=natural_attempt(page,f,out)
            except Exception as e:report['failures'].append('natural: '+str(e));page.screenshot(path=str(out/'natural-failure.png'))
            report['errors'].extend(errors);report['missing'].extend(missing);ctx.close()
        browser.close()
    report['sourceHashesAfter']=runtime_hashes(args.url)
    if report['sourceHashesAfter']!=report['sourceHashes']:report['failures'].append('runtime changed during acceptance; rerun after freeze')
    report['ok']=not(report['failures'] or report['errors'] or report['missing'])
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'errors':report['errors']},ensure_ascii=True))
    if not report['ok']:raise SystemExit(1)

if __name__=='__main__':main()
