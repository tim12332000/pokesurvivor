"""Temari acceptance through the production picker, combat and damage pipeline.

Run an HTTP server at :8004 (or set TEMARI_URL). Controlled arenas remove
procedural terrain only. Damage, casts, cards, actors, collisions and input are
native. Each check records its evidence independently; any failure fails CI.
"""
import base64
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_gaara import CHROME, HARNESS

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('TEMARI_OUT', str(ROOT / '.omx/state/temari')))
URL = os.environ.get('TEMARI_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=temari')
REPORT = OUT / os.environ.get('TEMARI_REPORT_NAME', 'report.json' if not os.environ.get('TEMARI_CHECKS') else 'report-focused.json')
IDS = ['naruto-temari', 'naruto-temari-three-stars', 'naruto-temari-great-scythe', 'naruto-temari-blade-dance']

SETUP = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.assert(T,'native Temari module missing');
 A.nativeProps=G.World.propsInCircle;
 A.near=(a,b,label)=>A.assert(Math.abs(a-b)<1e-6*Math.max(1,Math.abs(b)),label+': '+a+' != '+b);
 A.petEnabled=false;
 A.reset=()=>{A.petEnabled=false;A.arena();G.World.propsInCircle=()=>[];G.SelfClones.clear();G.Pickups.clear();p.target=null;p.aim=0;p.xp=0;p.xpNext=1e12;
   p.quantityBonus=p.quantityPicks=0;p.percentHealthDamage=p.lifestealRate=p.critChance=p.damageSplashPicks=0;p.cdMul=1;
   p.item=null;for(const m of p.moves)m.t=999;};
 A.spawn=(x,y,special=null)=>{const e=new G.Enemy({dex:19,hp:1000000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
   e.types=['normal'];if(special)e[special]=true;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e};
 A.watch=e=>{const hits=[],hurt=e.hurt;e.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);
   hits.push({raw:args[0],damage:hp-this.hp,owner:args[6]===p,clone:!!G.SelfClones.isActor(args[6]),id:args[7],knock:args[4],secondary:!!G.DamageSplash?.isSecondary()});return result};return hits};
 // Hold automatic tick between explicit casts; preserve production ordering
 // for moving projectiles, contact resolution, then ongoing field updates.
 A.advance=(dt=.01)=>{A.resume();try{
   // Isolate finite wind fixtures from the separately tested autonomous passive.
   if(!A.petEnabled)for(const actor of [p,...G.SelfClones.actors()]){T.syncPets(actor);for(const pet of T.summons)if(pet.owner===actor)pet.cooldown=999;}
   p.anim.update(dt);G.Projectiles.update(dt,p,G.EnemyMgr.all());
   G.Combat.resolve(dt,p,0);G.Combat.updateFields(dt)}finally{A.pause()}};
 A.finish=(seconds=5)=>{for(let i=0;i<Math.ceil(seconds/.01);i++)A.advance(.01)};
 A.learn=()=>{p.level=30;for(const id of ['naruto-temari-three-stars','naruto-temari-great-scythe','naruto-temari-blade-dance'])
   if(!p.hasMove(id)){const c=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(c&&c.apply(p)!==false,'native learn '+id)}};
 A.rank=(id,rank)=>{const m=G.Moves.instance(id,rank),i=p.moves.findIndex(m=>m.id===id);
   if(i>=0){const old=p.moves[i];Object.assign(old,m);return old}A.assert(p.addMove(id),'add fixture '+id);return A.rank(id,rank)};
 A.mastery=L=>{const id='naruto-temari-three-stars';p.moves=p.moves.filter(m=>m.id!==id);if(L)p.moves.push(G.Moves.instance(id,L))};
 A.castNative=(id,actor=p)=>{const m=actor.moves.find(m=>m.id===id);A.assert(m,'unlearned '+id);
   // Permanent pets acquire targets through the native field update, never Player.cast.
   if(m.digiMode==='temari-blade-dance'){A.petEnabled=true;T.syncPets(actor);A.advance(.001);
     A.assert(T.summons.some(a=>a.owner===actor&&a.phase==='move'),'passive pet did not acquire target');return m;}
   if(!m.passive){const slot=actor.slots.findIndex(g=>g.some(n=>n.id===id));A.assert(slot>=0,'missing active slot '+id);actor.setActive(slot)}
   for(const move of actor.moves)move.t=move.id===id?0:999;
   const moves=actor.moves;actor.moves=moves.filter(n=>n.id===id||n.digiMode==='temari-mastery');
   const old=actor.cast;let calls=0;actor.cast=function(move,...args){if(move.id===id)calls++;return old.call(this,move,...args)};
   try{A.resume();G.Combat.tick(.001,actor,0)}finally{actor.cast=old;actor.moves=moves;A.pause()}
   A.assert(calls===1,'native cast count '+id+': '+calls);return m};
 A.pose=(actor=p)=>{const c=document.createElement('canvas');c.width=280;c.height=240;const ctx=c.getContext('2d',{willReadFrequently:true}),sources=[],rects=[];
   const draw=ctx.drawImage.bind(ctx);ctx.drawImage=(im,...args)=>{sources.push(im.src||im.dataset?.source||'');rects.push(args);return draw(im,...args)};
   actor.anim.draw(ctx,140,185);const rgba=ctx.getImageData(0,0,c.width,c.height).data;let pixels=0,x0=c.width,y0=c.height,x1=-1,y1=-1;
   for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++)if(rgba[(y*c.width+x)*4+3]>20){pixels++;x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}
   A.assert(sources.length&&sources.every(s=>/temari/i.test(s)),'wrong actor art '+sources);A.assert(pixels>80,'empty Temari art');
   A.assert(x0>0&&x1<c.width-1&&y0>0&&y1<c.height-1,'clipped Temari art');
   return {sources,rects,pixels,bounds:[x0,y0,x1,y1],png:c.toDataURL()}};
 A.commonPose=(cur,allowed,requireCur=true)=>{if(requireCur)A.assert(p.anim.cur===cur,'native animation '+p.anim.cur+' expected '+cur);const pose=A.pose(),sheet=G.TemariArt.metadata.sheets.common;
   A.assert(pose.sources.every(src=>src===G.TemariArt.images.common.src),'common pose used skill/foreign atlas '+cur);
   const frames=pose.rects.map(rect=>sheet.frames.findIndex(frame=>frame.rect.every((value,i)=>value===rect[i])));
   A.assert(frames.length&&frames.every(index=>allowed.includes(index)),'wrong native common frame '+cur+' '+frames+' allowed '+allowed);
   return {...pose,animation:p.anim.cur,expectedAnimation:cur,frames,animFrame:p.anim.frame,animTime:p.anim.t}};
 A.nativeDeathPose=()=>{A.assert(p.dead&&p.anim.cur==='Faint'&&p.flash>0,'native death/flash regression fixture absent');
   const c=document.createElement('canvas');c.width=280;c.height=240;const ctx=c.getContext('2d',{willReadFrequently:true}),calls=[],draw=ctx.drawImage.bind(ctx);
   ctx.drawImage=(image,...rect)=>{calls.push({source:image.src||null,isImage:image instanceof HTMLImageElement,rect});return draw(image,...rect)};
   ctx.translate(140-p.x,185-p.y);p.draw(ctx);const sheet=G.TemariArt.metadata.sheets.common;
   A.assert(calls.length&&calls.every(call=>call.isImage&&call.source===G.TemariArt.images.common.src),'native Player.draw death used white canvas or foreign art '+JSON.stringify(calls));
   const frames=calls.map(call=>sheet.frames.findIndex(frame=>frame.rect.every((value,i)=>value===call.rect[i])));
   A.assert(frames.every(frame=>frame===23),'native Player.draw did not use late death frame '+frames);
   const rgba=ctx.getImageData(0,0,c.width,c.height).data;let coloredPixels=0;
   for(let i=0;i<rgba.length;i+=4)if(rgba[i+3]>80&&Math.max(rgba[i],rgba[i+1],rgba[i+2])-Math.min(rgba[i],rgba[i+1],rgba[i+2])>30)coloredPixels++;
   A.assert(coloredPixels>100,'native death became white silhouette '+coloredPixels);return {calls,frames,coloredPixels,lethalFlash:p.flash,png:c.toDataURL()}};
 A.reset();
}"""

PROGRESSION = r"""() => {
 const A=Acceptance,p=A.p(),out=[];
 A.assert(p.dex===30011&&p.moves.length===1&&p.moves[0].id==='naruto-temari','fresh starter must contain only wind basic');
 A.assert(p.moves[0].passive&&p.slots.length===0,'starter must work with zero active slots');
 A.reset();p.target=A.spawn(100,0);A.castNative('naruto-temari');A.finish();A.assert(p.target.hp<p.target.maxHp,'zero-slot basic did not damage');
 const ids=['naruto-temari-three-stars','naruto-temari-great-scythe','naruto-temari-blade-dance'];
 for(let i=0;i<ids.length;i++){const id=ids[i],lv=[3,6,9][i];p.level=lv-1;
   A.assert(!G.LevelUp.offer(p,100).some(c=>c.key==='new:'+id),'premature unlock '+id);
   p.level=lv;const cards=G.LevelUp.offer(p,3),c=cards.find(c=>c.key==='new:'+id);A.assert(c?.guaranteed,'missing guaranteed milestone '+id);
   G.RunUI.showLevelUp(lv,cards,c=>c.apply(p));G.RunUI.closeLevelUp();
   A.assert(p.narutoMilestonesShown.has(id),'actual milestone display unrecorded '+id);
   A.assert(!G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id)?.guaranteed,'declined milestone forced repeatedly '+id);
   const slots=p.slots.length;if(i===0)p.maxMoves=slots;
   const learn=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(learn&&learn.apply(p)!==false,'native card failed '+id);p.maxMoves=5;
   A.assert(p.slots.length===slots+(i===1?1:0),'passive slot handling '+id);out.push({id,level:lv,slots:p.slots.length});
 }
 const mon=p.mon;p.mon=G.DEX.find(m=>m.dex===30009);try{A.assert(!G.Moves.poolFor(p.mon).some(id=>id.startsWith('naruto-temari')),'Temari leaked into Tenten')}finally{p.mon=mon}
 A.assert(p.moves.length===4&&p.slots.length===1,'Temari has extra/missing skills');return out;
}"""

GROWTH = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];A.learn();
 for(const id of ['naruto-temari','naruto-temari-great-scythe'])for(const L of [0,1,5])for(const Q of [0,5,10,20]){
   A.reset();A.rank(id,5);A.mastery(L);p.quantityBonus=p.quantityPicks=Q;
   const target=A.spawn(100,0,'boss'),hits=A.watch(target);p.target=target;A.castNative(id);
   const s=T.stateFor(p),f=s.latest,N=Math.floor(3*1.25**Q),R=id==='naruto-temari-great-scythe'?1:L?1+L+Q:1,W=1,K=Math.floor(1.25**Q),C=6+(L?L+Q:0);
   A.assert(f,'missing observable cast snapshot '+id);
   for(const [key,expected] of Object.entries({Q,L,R}))A.assert(f[key]===expected,'snapshot '+key+' '+id+' '+JSON.stringify(f));
   const expected=id==='naruto-temari'?N:id.endsWith('great-scythe')?W:K;
   A.assert(f.count===expected,'quantity cap or wrong multiplicative count '+id+' Q'+Q+' '+f.count+' != '+expected);
   const potential=expected*(id.endsWith('blade-dance')?C:R);A.assert(f.potentialHits===potential,'quantity/mastery must multiply '+id+' '+f.potentialHits+'/'+potential);
   if(id.endsWith('blade-dance'))A.assert(f.C===C,'summon slashes capped '+f.C+'/'+C);
   const before=performance.now();A.finish(6);const elapsed=performance.now()-before;
   A.assert(f.emitted===expected,'real actors not all emitted '+id+' '+f.emitted+'/'+expected);
   A.assert(f.cuts<=potential&&(id!=='naruto-temari'||f.cuts>0),'duplicate/missing physical cut events '+id+' '+f.cuts+'/'+potential);
   if(id!=='naruto-temari')A.assert(f.cuts===potential,'AOE/slash event schedule truncated '+id+' '+f.cuts+'/'+potential);
   A.assert(hits.length>0&&hits.length<=potential,'missing/duplicate actual collision events '+id+' '+hits.length+'/'+potential);
   A.assert(hits.every(h=>h.owner&&h.id===id&&h.damage>0),'hit attribution/HP pipeline '+id);
   out.push({id,L,Q,N,R,W,K,C,potential,actualHits:hits.length,missedCuts:potential-hits.length,damage:target.maxHp-target.hp,updateMs:elapsed});
 }
 // Keep geometry explicit: one large controlled collision body intersects the
 // complete fan. This locks repeated per-blade cuts against global target dedup.
 for(const Q of [0,5,10,20]){A.reset();A.mastery(5);p.quantityBonus=p.quantityPicks=Q;const e=A.spawn(80,0,'boss');e.r=300;e.hp=e.maxHp=1e10;
   G.EnemyMgr.rebuildGrid();const hits=A.watch(e);p.target=e;A.castNative('naruto-temari');const f=T.stateFor(p).latest;A.finish(6);
   A.assert(hits.length===Math.floor(3*1.25**Q)*(6+Q),'full-contact basic deduplicated/capped '+Q+' '+hits.length+'/'+f.potentialHits);
   out.push({fullContact:true,Q,hits:hits.length});}
 return out;
}"""

RANKS = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];A.learn();
 for(const [id,damage,cd] of [['naruto-temari',[8,9.6,11.52,14.4,18],1.6],['naruto-temari-great-scythe',[56,67.2,80.64,100.8,126],5]]){
   A.rank(id,1);for(let rank=1;rank<=5;rank++){
     if(rank>1){const c=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);A.assert(c&&c.apply(p)!==false,'native upgrade card missing '+id+' '+rank)}
     A.reset();A.mastery(0);const m=p.moves.find(m=>m.id===id);A.assert(m.lvl===rank,'native upgrade rank '+id);A.near(m.dmg,damage[rank-1],'full per-cut damage '+id);A.near(m.cd,cd,'base cooldown '+id);
     p.cdMul=.92;const attack=p.atkMul;p.atkMul*=1.1;p.target=A.spawn(100,0,'boss');A.castNative(id);const f=T.stateFor(p).latest;
     A.near(f.damage,damage[rank-1]*p.atk,'attack growth damage snapshot '+id);const remaining=id==='naruto-temari'?T.stateFor(p).basicCooldown:T.stateFor(p).cooldowns[id];
     A.near(remaining,cd*.92,'cooldown growth '+id);p.atkMul=attack;out.push({id,rank,damage:f.damage,cd:remaining});
   }
 }
 for(let L=1;L<=5;L++){A.reset();A.mastery(L);const m=p.moves.find(m=>m.id==='naruto-temari'),s=T.snapshot(p,m);
   A.near(s.speed,m.speed*[1.15,1.25,1.4,1.6,1.85][L-1],'mastery speed '+L);A.near(s.range,m.range+[40,70,110,160,220][L-1],'mastery reach '+L);
   A.assert(s.R===1+L,'mastery cuts '+L);out.push({L,speed:s.speed,range:s.range,R:s.R});}
 for(const [id,expected] of [['naruto-temari-blade-dance',[25.6,31.2,37.6,45.6,55.2]],['naruto-temari-typhoon',[24,28.8,35.2,43.2,52.8]]]){
   for(let rank=1;rank<=5;rank++){A.reset();A.mastery(0);const m=A.rank(id,rank),s=T.snapshot(p,m);
     A.near(m.dmg,expected[rank-1],'balanced rank '+id+' '+rank);A.near(s.damage,expected[rank-1]*p.atk,'balanced snapshot '+id+' '+rank);
     const fallback={...m};delete fallback.dmg;A.near(T.snapshot(p,fallback).damage,s.damage,'balanced fallback '+id+' '+rank);
     out.push({id,rank,damage:m.dmg});}
 }
 // Giant only enlarges the actor. It must leave the snapshotted wind reach intact.
 A.reset();A.mastery(5);const move=p.moves.find(m=>m.id==='naruto-temari'),range=T.snapshot(p,move).range;
 const giant=G.LevelUp.offer(p,100).find(c=>c.key==='stat:giant');A.assert(giant,'native giant card missing');giant.apply(p);
 A.near(T.snapshot(p,move).range,range,'giant incorrectly increased weapon reach');return out;
}"""

EMPOWERMENT = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];A.learn();A.reset();A.mastery(5);const e=A.spawn(100,0,'boss');p.target=e;
 for(let round=1;round<=6;round++){
   if(round>1){const moves=p.moves;p.moves=[];A.resume();try{G.Combat.tick(2,p,0)}finally{p.moves=moves;A.pause()}}
   A.castNative('naruto-temari');const f=T.stateFor(p).latest;A.assert(f.empowered===(round%3===0),'empowerment cadence '+round);
   A.near(f.damage,p.moves.find(m=>m.id==='naruto-temari').dmg*p.atk*(round%3===0?1.35:1),'third-round full wind multiplier');
   if(round===3){A.finish(.19);const shots=[],add=(x,y,extra={})=>{const shot=G.Projectiles.spawn({x,y,vx:0,vy:0,dmg:7,r:3,life:5,friendly:false,interceptable:true,...extra});shots.push(shot);return shot};
     const crossing=[-5,0,5].map(y=>add(30,y,{vx:-1000})),rear=add(-50,0),special=add(45,3,{bossSpecial:true}),unblock=add(40,-3,{unblockable:true}),extra=add(60,0),hp=p.hp;
     // Actual production order crosses .19 -> .22 and would reach the owner
     // before the fields update. The interception hook must protect that frame.
     A.advance(.03);A.assert(crossing.every(s=>!G.Projectiles.all().includes(s)),'swept forward projectiles not intercepted before contact resolution');
     A.assert([rear,special,unblock,extra].every(s=>G.Projectiles.all().includes(s)),'interception exceeded budget or removed rear/special/unblockable shot');
     A.near(p.hp,hp,'intercepted projectile injured owner before field update');
     out.push({productionOrder:true,age:f.age,intercepted:T.stateFor(p).intercepted,budget:f.budget});
   }
   A.finish(3);out.push({round,empowered:f.empowered,damage:f.damage});
 }
 return out;
}"""

AOE = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out={};A.learn();
 for(const id of ['naruto-temari-great-scythe']){
   A.reset();A.mastery(1);A.rank(id,1);const es=[A.spawn(130,0),A.spawn(145,32),A.spawn(145,-32),A.spawn(-400,400)],hits=es.map(A.watch);
   p.target=es[0];A.castNative(id);const f=T.stateFor(p).latest;A.finish(4);const damage=es.map(e=>e.maxHp-e.hp);
   A.assert(damage.slice(0,3).every(d=>d>0)&&damage[3]===0,'three inside/one outside '+id+' '+damage);
   A.assert(hits.every(h=>h.every(v=>v.owner&&v.id===id)),'AOE attribution '+id);
   A.assert(hits.slice(0,3).every(h=>h.length<=(id.endsWith('blade-dance')?f.C:f.R)*f.count),'duplicate per-cut target damage '+id);
   const counts=hits.map(h=>h.length);A.finish(1);A.assert(hits.every((h,i)=>h.length===counts[i]),'expired effects dealt damage '+id);out[id]={damage,counts};
 }
 out.knock=[];
 for(const special of [null,'boss','elite','legend','judge']){A.reset();A.mastery(5);const e=A.spawn(120,0,special),hits=A.watch(e);p.target=e;
   A.castNative('naruto-temari-great-scythe');A.finish();const knocks=hits.filter(h=>h.knock>0).length;
   A.assert(knocks===0,'heavy escape push must not add native velocity knockback '+special+' '+knocks);A.assert(hits.length===1,'heavy must damage once '+special);out.knock.push({special,hits:hits.length,knocks})}
 // A target which leaves before later cuts must not receive retroactive hits.
 A.reset();A.mastery(5);const escape=A.spawn(120,0,'boss'),hits=A.watch(escape);p.target=escape;A.castNative('naruto-temari-great-scythe');
 for(let i=0;i<100&&!hits.length;i++)A.advance();A.assert(hits.length,'escape fixture never contacted');escape.x=-1000;G.EnemyMgr.rebuildGrid();const before=hits.length;A.finish();A.assert(hits.length===before,'escaped target received delayed damage');out.escape=before;
 return out;
}"""

COLLISION = r"""() => {
 const A=Acceptance,p=A.p(),out=[];A.learn();
 for(const id of ['naruto-temari','naruto-temari-great-scythe']){
   A.reset();A.mastery(5);const e=A.spawn(180,0,'boss');p.target=e;A.castNative(id);
   const W=G.World,saved={isFree:W.isFree,isWall:W.isWall,projectileBlock:W.projectileBlock};
   Object.assign(W,{isFree:x=>x<45,isWall:x=>x>=45&&x<=90,projectileBlock:x=>x>=45&&x<=90?{destructible:false}:false});
   try{A.finish(6);A.assert(e.hp===e.maxHp,'in-flight attack crossed inserted solid wall '+id)}finally{Object.assign(W,saved)}out.push(id);
 }
 return out;
}"""

PROPS = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.reset();A.mastery(0);A.rank('naruto-temari',1);
 const prop=A.nativeProps(0,0,900).find(p=>p.type==='grass'&&p.destructible&&p.hp>0);A.assert(prop,'native procedural grass fixture absent');
 const saved=G.World.propsInCircle;G.World.propsInCircle=(x,y,r)=>prop.hp>0&&Math.hypot(prop.x-x,prop.y-y)<=r+prop.r?[prop]:[];
 p.x=prop.x-80;p.y=prop.y;p.target=null;const hp=prop.hp,slots=p.slots;p.slots=[];
 try{A.castNative('naruto-temari');A.finish();A.assert(prop.hp<hp,'zero-enemy starter could not physically damage native grass');
   A.assert(T.stateFor(p).propHits>0&&!G.EnemyMgr.all().length,'prop opening required a synthetic enemy');return {type:prop.type,before:hp,after:prop.hp,hits:T.stateFor(p).propHits}}
 finally{G.World.propsInCircle=saved;p.slots=slots}
}"""

# Permanent pet population/cycle assertions live in test_temari_passive.py.

ACCOUNTING = r"""() => {
 const A=Acceptance,p=A.p(),out=[];A.learn();
 for(const boss of [false,true])for(const crit of [0,1]){A.reset();A.mastery(0);A.rank('naruto-temari',1);p.percentHealthDamage=.01;p.lifestealRate=.00001;p.critChance=crit;p.hp=p.maxHp/2;
   const e=A.spawn(100,0,boss?'boss':null),hits=A.watch(e),hp=p.hp,credited=p.dmgDealt;p.target=e;A.castNative('naruto-temari');A.finish();
   A.assert(hits.length>0,'accounting has no physical hits');const raw=8*p.atk*G.Types.mult('flying',e.types)*G.Weather.mult('flying')*(crit?1.5:1),bonus=e.maxHp*.01*(boss?.1:1);
   A.assert(hits.every(h=>Math.abs(h.raw-raw)<1e-5&&h.damage===Math.round(raw+bonus)),'crit/type/weather/percent actual HP event '+JSON.stringify(hits));
   A.near(p.dmgDealt-credited,(raw+bonus)*hits.length,'damage credit once per real hit');A.near(p.hp-hp,(raw+bonus)*hits.length*.00001,'lifesteal once per primary hit');
   out.push({boss,crit,hits:hits.length,damage:e.maxHp-e.hp,healed:p.hp-hp});}
 // Native item recoil is paid on each cast, independently of actor/cut count.
 A.reset();A.mastery(5);p.quantityBonus=p.quantityPicks=20;p.item='lifeorb';
 A.assert(p.hasItem('lifeorb'),'native lifeorb fixture missing');const hp=p.hp;p.target=A.spawn(100,0,'boss');A.castNative('naruto-temari');A.finish(6);
 A.near(hp-p.hp,Math.max(1,p.maxHp*.01),'life orb charged per cut');out.push({lifeorbLoss:hp-p.hp});
 // Both wind waves are area attacks and do not trigger single-target splash.
 for(const id of ['naruto-temari','naruto-temari-great-scythe']){A.reset();A.mastery(0);p.damageSplashPicks=1;p.percentHealthDamage=.01;
   const e=A.spawn(100,0,'boss'),side=A.spawn(100,45,'boss'),primaryHits=A.watch(e),hits=A.watch(side);p.target=e;A.castNative(id);A.finish();
   const secondary=[...primaryHits,...hits].filter(h=>h.secondary);A.assert(secondary.length===0,'AOE recursively splashed '+id);
   if(secondary.length)A.assert(secondary.every(h=>h.raw<e.maxHp*.001),'secondary reapplied percentage HP');out.push({id,secondary:secondary.length});}
 return out;
}"""

CLONES = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];A.learn();
 for(const id of ['naruto-temari','naruto-temari-great-scythe']){
   A.reset();A.mastery(5);p.quantityBonus=p.quantityPicks=5;const e=A.spawn(100,0,'boss'),hits=A.watch(e);p.target=e;
   A.castNative(id);const owner=T.stateFor(p).latest;A.finish(6);const baseline=hits.find(h=>h.id===id&&!h.secondary)?.raw;A.assert(baseline>0,'owner baseline missing');
   G.Combat.clearFields();e.hp=e.maxHp;hits.length=0;const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');A.assert(card,'native clone card missing');card.apply(p);
   const clone=G.SelfClones.actors()[0];A.assert(clone,'native clone absent');clone.x=clone.y=0;clone.target=e;clone.aim=0;clone.critChance=0;
   A.castNative(id,clone);const state=T.stateFor(clone),f=state.latest;A.assert(f.count===owner.count&&f.R===owner.R&&f.C===owner.C,'clone reduced actor/cut counts');
   for(const m of clone.moves)m.t=999;const ownerMoves=p.moves;p.moves=p.moves.filter(m=>m.digiMode==='temari-mastery');
   try{A.finish(6)}finally{p.moves=ownerMoves}const actual=hits.filter(h=>h.clone&&h.id===id);A.assert(actual.length>0,'clone missed all contacts '+id);
   actual.forEach(h=>A.near(h.raw*3,baseline,'clone damage must be one third once '+id));
   A.assert(T.stateFor(p)!==state,'clone shares mastery/basic counter state');out.push({id,count:f.count,hits:actual.length,ratio:actual[0].raw/baseline});
   G.SelfClones.clear();A.advance();A.assert(!T.stateFor(clone)&&!T.summons.some(s=>s.owner===clone),'deleted clone retained effects');
 }
 return out;
}"""

PERFORMANCE = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];A.learn();
 for(const draw of [false,true]){A.reset();A.mastery(5);A.rank('naruto-temari',5);p.quantityBonus=p.quantityPicks=20;
   const target=A.spawn(80,0,'boss');target.r=300;target.hp=target.maxHp=1e10;G.EnemyMgr.rebuildGrid();const hits=A.watch(target);p.target=target;
   const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');for(let i=0;i<3;i++)card.apply(p);
   const actors=[p,...G.SelfClones.actors()];for(const a of actors){a.x=a.y=0;a.target=target;a.aim=0;A.castNative('naruto-temari',a)}
   const casts=actors.map(a=>T.stateFor(a).latest),moves=p.moves;p.moves=p.moves.filter(m=>m.digiMode==='temari-mastery');
   const cv=document.createElement('canvas');cv.width=1200;cv.height=900;const ctx=cv.getContext('2d'),samples=[],drawSamples=[];let peak=0,pending=0;
   try{for(let i=0;i<360;i++){const start=performance.now();A.advance(1/60);samples.push(performance.now()-start);
     peak=Math.max(peak,T.waves.length);pending=Math.max(pending,...actors.map(a=>T.stateFor(a)?.pendingCuts||0));
     if(draw){const at=performance.now();G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);drawSamples.push(performance.now()-at)}}}
   finally{p.moves=moves}
   A.assert(casts.every(c=>c.count===260&&c.emitted===260&&c.cuts===6760),'Q20 clone workload silently capped');
   A.assert(hits.length===4*6760,'Q20 clone physical event count '+hits.length);A.assert(!T.waves.length&&!T.casts.length,'Q20 workload failed to expire');
   const sum=a=>a.reduce((s,x)=>s+x,0),p95=a=>[...a].sort((a,b)=>a-b)[Math.floor(a.length*.95)]||0;
   out.push({draw,actors:actors.length,wavesPerActor:260,cutsPerActor:6760,hits:hits.length,damage:target.maxHp-target.hp,peak,pending,
     updateMs:sum(samples),updateP95:p95(samples),drawMs:sum(drawSamples),drawP95:p95(drawSamples)});
 }
 A.assert(out[0].hits===out[1].hits&&out[0].damage===out[1].damage,'rendering changed hit outcomes');return out;
}"""

LIFECYCLE = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];A.learn();
 for(const reason of ['pause','switch','clear','death','world']){A.reset();A.mastery(5);p.target=A.spawn(140,0,'boss');A.castNative('naruto-temari-great-scythe');A.finish(.5);
   const f=T.stateFor(p).latest,age=T.activeFor(p)?.age,cuts=f.cuts,world=G.World;
   if(reason==='pause'){G.Combat.updateFields(.5);A.assert(f.cuts===cuts&&T.activeFor(p)?.age===age,'pause advanced cuts or pose')}
   if(reason==='switch'){p.level=30;if(!p.hasMove('naruto-temari-typhoon'))p.addMove('naruto-temari-typhoon');A.select('naruto-temari-typhoon');A.finish(.4);
     A.assert(T.stateFor(p).latest===f,'switch replaced in-flight wind')}
   if(reason==='clear'){G.Combat.clearFields(p);A.assert(!T.stateFor(p),'clear retained owner state')}
   if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};
   try{if(['death','world'].includes(reason)){A.advance();A.assert(!T.stateFor(p)||!T.waves.some(a=>a.cast===f),'stale events after '+reason)}}finally{G.World=world;p.dead=false}
   out.push(reason);
 }
 return out;
}"""


def boot(page):
    url = URL
    if page.viewport_size['width'] > 600 and 'layout=' not in url:
        url += ('&' if '?' in url else '?')+'layout=wide'
    page.goto(url)
    # Protocol fixtures freeze RAF; these entry waits must poll on a real timer.
    try:
        page.wait_for_function("window.PS_REDRAWN_READY && window.G?.NarutoTemari && document.getElementById('boot').classList.contains('hidden')", polling=20)
    except Exception as error:
        diagnostic = page.evaluate('({url:location.href,game:!!window.G,temari:!!window.G?.NarutoTemari,ready:!!window.PS_REDRAWN_READY,boot:document.getElementById("boot")?.outerHTML})')
        raise AssertionError('normal boot failed: '+json.dumps(diagnostic)) from error
    if page.locator('#tap-start').is_visible():
        page.locator('#tap-start').click()
    page.locator('[data-quick-naruto="30011"]').click()
    assert page.evaluate('G.DB.save.partner===30011'), 'normal picker failed to select Temari'
    page.locator('#scr-menu [data-go="play"]').click()
    page.wait_for_function('G.Game.player?.dex===30011 && G.Game.state==="playing"', polling=20)
    page.evaluate(HARNESS)
    page.evaluate(SETUP)


def save_pose(label, pose):
    (OUT / f'{label}.png').write_bytes(base64.b64decode(pose.pop('png').split(',', 1)[1]))
    return pose


def input_and_art(page, context, mobile, label):
    result = {'poses': {}}
    page.evaluate('Acceptance.learn();Acceptance.reset()')
    for direction, key in [('right', 'KeyD'), ('down', 'KeyS'), ('left', 'KeyA'), ('up', 'KeyW')]:
        page.evaluate('Acceptance.reset();Acceptance.finish(.6)')
        page.keyboard.down(key)
        pose = page.evaluate("""() => {const A=Acceptance,p=A.p(),x=p.x,y=p.y;A.resume();p.update(.08);A.pause();
          A.assert(p.walking&&Math.hypot(p.x-x,p.y-y)>0,'keyboard movement failed');return A.pose()}""")
        page.keyboard.up(key)
        result['poses']['walk-'+direction] = save_pose(f'{label}-walk-{direction}', pose)
    page.evaluate('''() => {const A=Acceptance,p=A.p();A.reset();p.attackFace=0;p.walking=false;A.resume();try{p.update(.08)}finally{A.pause()}
      A.assert(!p.walking&&p.anim.cur==='Idle','native no-input update did not enter Idle')}''')
    result['poses']['idle'] = save_pose(f'{label}-idle', page.evaluate("Acceptance.commonPose('Idle',[0,1,2,3,4,5])"))
    page.evaluate('''() => {const A=Acceptance,p=A.p();A.reset();p.invuln=0;const hp=p.hp;A.resume();try{p.hurt(7,null,true)}finally{A.pause()}
      A.assert(p.hp===hp-7&&p.flash>0&&!p.dead,'native nonlethal hurt failed')}''')
    result['poses']['hurt'] = save_pose(f'{label}-hurt', page.evaluate("Acceptance.commonPose('Hurt',[16,17,18,19],false)"))
    page.evaluate('''() => {const A=Acceptance,p=A.p();A.reset();p.invuln=0;p.hp=1;A.resume();try{p.hurt(10,null,true)}finally{A.pause()}
      A.assert(p.dead&&p.hp===0&&p.anim.cur==='Faint','native lethal hurt did not enter Faint')}''')
    result['poses']['death-start'] = save_pose(f'{label}-death-start', page.evaluate("Acceptance.commonPose('Faint',[20])"))
    page.evaluate('''() => {const A=Acceptance;A.resume();try{A.p().update(.5)}finally{A.pause()}}''')
    result['poses']['death'] = save_pose(f'{label}-death', page.evaluate("Acceptance.commonPose('Faint',[23])"))
    result['nativeDeath'] = save_pose(f'{label}-death-native', page.evaluate('Acceptance.nativeDeathPose()'))
    for skill in [IDS[0], IDS[2], IDS[3]]:
        page.evaluate('(id)=>{Acceptance.reset();G.Game.player.target=Acceptance.spawn(150,0);Acceptance.castNative(id);Acceptance.finish(.16)}', skill)
        result['poses'][skill] = save_pose(f'{label}-{skill}-actor', page.evaluate('Acceptance.pose()'))
        if skill.endswith('blade-dance'):
            page.evaluate('Acceptance.finish(.65)')
            result['summonArt'] = page.evaluate('''() => {const c=document.createElement('canvas');c.width=440;c.height=300;const ctx=c.getContext('2d'),sources=[],draw=ctx.drawImage.bind(ctx);
              ctx.drawImage=(im,...args)=>{sources.push(im.src||'');return draw(im,...args)};ctx.translate(140,180);G.Combat.drawAirFields(ctx);
              Acceptance.assert(sources.includes(G.TemariArt.images.kamatari.src),'native summon failed to draw own Kamatari PNG');
              return {sources,png:c.toDataURL()}}''')
            result['summonArt'] = save_pose(f'{label}-kamatari-runtime', result['summonArt'])
        page.screenshot(path=str(OUT / f'{label}-{skill}.png'))
    page.evaluate('Acceptance.reset();G.Game.player.level=30;if(!G.Game.player.hasMove("naruto-temari-typhoon"))G.Game.player.addMove("naruto-temari-typhoon");Acceptance.select("naruto-temari-great-scythe");Acceptance.resume()')
    page.evaluate("window.__temariInputPhase='keyboard2'")
    page.keyboard.press('Digit2')
    page.wait_for_function('G.Game.player.active===1',polling=20)
    result['keyboardSwitch'] = page.evaluate('Acceptance.pause();G.Game.player.activeGroup().map(m=>m.id)')
    if mobile:
        page.evaluate('Acceptance.reset();Acceptance.resume()')
        client = context.new_cdp_session(page)
        base = page.evaluate('G.Touch.stickBase()')
        client.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': base['x'], 'y': base['y']}]})
        client.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': base['x']+45, 'y': base['y']}]})
        result['touchMove'] = page.evaluate("""() => {const A=Acceptance,p=A.p(),x=p.x;A.assert(G.Touch.vector()?.[0]>0,'touch vector missing');p.update(.08);A.pause();A.assert(p.x>x,'touch did not move');return p.x-x}""")
        client.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
        page.evaluate('Acceptance.resume()')
        slot = page.evaluate('(()=>{const p=G.Game.player,n=p.slots.length+p.moves.filter(m=>m.passive&&!p.slots.some(g=>g.includes(m))).length;return G.Touch.controlLayout(innerWidth,innerHeight,Math.max(1,n)).slots[0]})()')
        page.evaluate("window.__temariInputPhase='touch0'")
        page.touchscreen.tap(slot['x']+slot['w']/2, slot['y']+slot['h']/2)
        page.wait_for_function('G.Game.player.active===0',polling=20)
        page.evaluate('Acceptance.pause()')
        result['touchSwitch'] = True
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'horizontal overflow'
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'requestedChecks': os.environ.get('TEMARI_CHECKS', 'all'), 'errors': [], 'failedRequests': [], 'viewports': {}, 'failures': []}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for label, viewport, mobile in [('desktop', {'width': 1200, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
                if os.environ.get('TEMARI_VIEWPORTS') and label not in os.environ['TEMARI_VIEWPORTS'].split(','):
                    continue
                context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.on('response', lambda r: report['failedRequests'].append({'url': r.url, 'status': r.status}) if r.status >= 400 and '127.0.0.1' in r.url else None)
                boot(page)
                page.screenshot(path=str(OUT / f'{label}-normal-entry.png'))
                report['viewports'][label] = result = {}
                checks = [('progression', PROGRESSION), ('ranks', RANKS), ('growth', GROWTH), ('empowerment', EMPOWERMENT), ('aoe', AOE), ('collision', COLLISION), ('props', PROPS), ('accounting', ACCOUNTING), ('clones', CLONES), ('lifecycle', LIFECYCLE), ('performance', PERFORMANCE)]
                for name, check in checks:
                    if os.environ.get('TEMARI_CHECKS') and name not in os.environ['TEMARI_CHECKS'].split(','):
                        continue
                    print(label, name, flush=True)
                    try:
                        result[name] = page.evaluate(check)
                    except Exception as error:
                        result[name] = {'failure': str(error)}
                        report['failures'].append(label+':'+name+': '+str(error))
                        print(json.dumps({'check': name, 'failure': str(error)}), flush=True)
                    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
                try:
                    result['inputAndArt'] = input_and_art(page, context, mobile, label)
                except Exception as error:
                    report['failures'].append(label+':inputAndArt: '+str(error)+' '+json.dumps(page.evaluate('({phase:window.__temariInputPhase,state:G.Game.state,active:G.Game.player.active,slots:G.Game.player.slots.map(g=>g.map(m=>m.id)),touch:!!G.Touch.active})')))
                context.close()
            browser.close()
        report['ok'] = not (report['errors'] or report['failedRequests'] or report['failures'])
    except Exception as error:
        report['ok'] = False
        report['failures'].append(str(error))
    finally:
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': report['ok'], 'failures': report['failures'], 'evidence': str(OUT)}))
    if not report['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
