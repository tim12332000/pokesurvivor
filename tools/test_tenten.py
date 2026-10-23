"""Tenten acceptance in the normal game, using native actors and enemy HP.

Only the controlled arena's terrain and randomness are fixed. No replacement
combat, synthetic sprites, preview iframe, or shadow implementation is used.
"""
import base64
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_gaara import CHROME, HARNESS
from test_redrawn_heroes import AUDIT

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('TENTEN_OUT', str(ROOT / '.omx/state/tenten')))
URL = os.environ.get('TENTEN_URL', 'http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=tenten')
IDS = ['naruto-tenten', 'naruto-tenten-fuma', 'naruto-tenten-mastery', 'naruto-tenten-tags', 'naruto-tenten-twin']

SETUP = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten; A.assert(T,'native Tenten module missing');
 A.reset=()=>{A.arena();G.SelfClones.clear();p.target=null;p.quantityBonus=0;p.quantityPicks=0;p.percentHealthDamage=0;p.lifestealRate=0;p.critChance=0;
   for(const m of p.moves)m.t=999;};
 A.spawn=(x,y,boss=false)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
   e.types=['normal'];e.boss=boss;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;};
 A.advance=(dt=.01)=>{A.resume();try{G.Combat.updateFields(dt);p.anim.update(dt);G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,0)}finally{A.pause()}};
 A.castNative=id=>{const m=p.moves.find(m=>m.id===id);A.assert(m,'unlearned '+id);if(!m.passive)A.select(id);
   // Omit the concurrent passive only while measuring an active's damage.
   // A separate fixture below verifies their legitimate simultaneous release.
   const moves=p.moves;if(id!=='naruto-tenten')p.moves=moves.filter(m=>m.id!=='naruto-tenten');
   let calls=0,old=p.cast;p.cast=function(move,...args){if(move.id===id)calls++;return old.call(this,move,...args)};
   try{A.resume();G.Combat.tick(.001,p,0)}finally{p.cast=old;p.moves=moves;A.pause()}
   A.assert(calls===1,'native cast count '+id+' '+calls);return m;};
 A.finish=(seconds=2)=>{for(let i=0;i<seconds*100;i++)A.advance(.01)};
 A.near=(a,b,msg)=>A.assert(Math.abs(a-b)<1e-6*Math.max(1,Math.abs(b)),msg+' '+a+' != '+b);
 A.reset();
}"""

PROGRESSION = r"""() => {
 const A=Acceptance,p=A.p(),ids=['naruto-tenten-fuma','naruto-tenten-mastery','naruto-tenten-tags','naruto-tenten-twin'],levels=[3,6,9,12],out=[];
 A.assert(p.dex===30009&&p.hp>0&&p.moves.some(m=>m.id==='naruto-tenten'&&m.passive),'invalid native starter');
 A.assert(p.moves.length===1&&p.slots.length===0,'starter must be passive and slotless');
 for(let i=0;i<ids.length;i++){
   const id=ids[i];p.level=levels[i]-1;
   A.assert(!G.LevelUp.offer(p,100).some(c=>c.key==='new:'+id),'premature unlock '+id);
   p.level=levels[i];const cards=G.LevelUp.offer(p,3),c=cards.find(c=>c.key==='new:'+id);
   A.assert(c?.guaranteed,'first eligible milestone missing '+id);
   G.RunUI.showLevelUp(p.level,cards,c=>c.apply(p));G.RunUI.closeLevelUp();
   A.assert(p.narutoMilestonesShown.has(id),'actual display not consumed '+id);
   A.assert(!G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id)?.guaranteed,'skipped skill still forced '+id);
   const slots=p.slots.length;
   if(id.endsWith('mastery'))p.maxMoves=slots;
   const learn=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);
   A.assert(learn&&learn.apply(p)!==false,'cannot learn signature '+id);p.maxMoves=6;
   A.assert(p.slots.length===slots+(id.endsWith('mastery')?0:1),'passive/active slot count '+id);
   out.push({id,level:levels[i],slots:p.slots.length});
 }
 A.assert(p.moves.length===5&&p.slots.length===3,'complete loadout missing');return out;
}"""

COMBAT = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,out={},ids=['naruto-tenten','naruto-tenten-fuma','naruto-tenten-tags','naruto-tenten-twin'];
 for(const id of ids){
   A.reset();const es=[A.spawn(100,0),A.spawn(150,45),A.spawn(170,-50),A.spawn(-350,300)];p.target=es[0];p.aim=0;
   const hits=es.map(()=>[]);es.forEach((e,i)=>{const hurt=e.hurt;e.hurt=function(...args){hits[i].push({amount:args[0],owner:args[6]===p,id:args[7]});return hurt.apply(this,args)}});
   const m=A.castNative(id),initial=es.map(e=>e.hp);A.assert(initial.every(h=>h===100000),'instant global damage '+id);
   if(id.endsWith('twin')){const s=T.activeFor(p);A.assert(s&&s.emitted<s.count,'twin emitted every batch immediately');}
   A.finish();const damage=es.map(e=>100000-e.hp);
   A.assert(damage.slice(0,3).some(d=>d>0)&&damage[3]===0,'native physical attack coverage '+id+' '+damage);
   A.assert(hits.flat().every(h=>h.owner&&h.id===id),'native damage lost actor/move attribution '+id);
   if(id.endsWith('fuma'))A.assert(hits.every(h=>h.length<=2*m.count),'fuma duplicate per-leg boss damage');
   const before=damage.slice();A.finish();A.assert(es.every((e,i)=>100000-e.hp===before[i]),'completed weapons repeated damage '+id);
   out[id]={damage,hits:hits.map(h=>h.length)};
 }
 // Tagged kunai must land harmlessly, wait, then produce exactly one AOE.
 A.reset();const m=p.moves.find(m=>m.id==='naruto-tenten-tags'),old=m.count;m.count=1;
 const mid=A.spawn(100,0);p.target=mid;p.aim=0;A.castNative(m.id);
 for(let i=0;i<100&&!T.weapons.find(w=>w.landed);i++)A.advance();
 const w=T.weapons.find(w=>w.landed);A.assert(w,'tag never landed');A.assert(mid.hp===100000,'tag applied impact damage');
 const radius=w.m.blastRadius||w.m.radius||60;
 const es=[mid,A.spawn(w.x,w.y+radius*.55),A.spawn(w.x,w.y-radius*.55),A.spawn(w.x,w.y+radius+40)];
 const counts=es.map(()=>0);es.forEach((e,i)=>{const h=e.hurt;e.hurt=function(...args){counts[i]++;return h.apply(this,args)}});
 A.finish(.5);A.assert(es.every(e=>e.hp===100000),'tag fuse too short');A.finish(1);
 A.assert(counts.join(',')==='1,1,1,0','tag blast absent/duplicated/outside '+counts);m.count=old;out.tags={counts,radius};
 // A wall inserted AFTER firing proves flight collision, not target filtering.
 out.wall=[];
 for(const id of ids){A.reset();const target=A.spawn(150,0);p.target=target;A.castNative(id);
   const block=G.World.projectileBlock;G.World.projectileBlock=(x,y)=>x>45&&x<70?{destructible:false}:false;
   try{A.finish()}finally{G.World.projectileBlock=block}A.assert(target.hp===100000,'weapon passed through wall '+id);out.wall.push(id);
 }
 A.reset();p.target=A.spawn(120,0);A.select('naruto-tenten-fuma');A.resume();try{G.Combat.tick(.001,p,0)}finally{A.pause()}
 A.assert(T.weapons.some(w=>w.mode==='tenten-fuma')&&T.weapons.some(w=>w.mode==='tenten-kunai'),'active cast suppressed passive basic');out.concurrentBasic=true;
 out.percentHealth=[];
 for(const boss of [false,true]){
   A.reset();const m=p.moves.find(m=>m.id==='naruto-tenten'),saved=m.count;m.count=1;
   const target=A.spawn(100,0,boss);p.target=target;p.percentHealthDamage=.01;p.lifestealRate=.001;p.hp=p.maxHp/2;
   const hp=p.hp,credited=p.dmgDealt,damage=m.dmg*p.atk*G.Types.mult(m.type,target.types)*G.Weather.mult(m.type),bonus=target.maxHp*.01*(boss?.1:1);
   A.castNative(m.id);A.finish();m.count=saved;
   A.assert(100000-target.hp===Math.round(damage+bonus),'percent-health bonus absent/doubled '+boss);
   A.near(p.dmgDealt-credited,damage+bonus,'damage credit counted twice');A.near(p.hp-hp,(damage+bonus)*.001,'lifesteal counted twice');
   out.percentHealth.push({boss,damage:100000-target.hp,healed:p.hp-hp});
 }
 return out;
}"""

SCALING = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,out=[];
 for(const id of ['naruto-tenten','naruto-tenten-fuma','naruto-tenten-tags','naruto-tenten-twin']){
   const m=p.moves.find(m=>m.id===id),baseCd=m.cd;
   for(let tier=1;tier<=5;tier++){
     if(tier>1){const c=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);A.assert(c&&c.apply(p)!==false,'upgrade '+id+' '+tier)}
     A.near(m.cd,baseCd,'tier changed cooldown');
     for(const picks of [0,4,20]){
       A.reset();p.quantityBonus=p.quantityPicks=picks;const target=A.spawn(120,0);p.target=target;A.castNative(id);
       const pose=T.activeFor(p),snapshot=G.Quantity.snapshot(p,m);A.assert(pose&&pose.count===snapshot.count,'quantity not applied once '+id+' '+picks);
       A.assert(pose.count===Math.floor(m.count*Math.pow(1.25,picks)),'wrong multiplicative quantity '+id+' '+pose.count);
       out.push({id,tier,picks,count:pose.count});
     }
   }
 }
 const master=p.moves.find(m=>m.id==='naruto-tenten-mastery');
 for(let tier=1;tier<=5;tier++){
   if(tier>1){const c=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+master.id);A.assert(c&&c.apply(p)!==false,'mastery tier '+tier)}
   A.reset();p.target=A.spawn(100,0);A.castNative('naruto-tenten');const state=T.stateFor(p);
   A.assert(state.masteryPierce===[1,1,2,2,3][tier-1],'mastery pierce '+tier);A.near(state.masterySpeed,1.05+.05*tier,'mastery speed');
 }
 A.reset();return out;
}"""

LIFECYCLE = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,out=[];
 for(const reason of ['pause','switch','clear','death','world']){
   A.reset();p.target=A.spawn(120,0);A.castNative('naruto-tenten-twin');const pose=T.activeFor(p),emitted=pose.emitted,world=G.World;
   if(reason==='pause'){G.Combat.updateFields(.5);A.assert(pose.age===0&&pose.emitted===emitted,'paused action advanced');}
   if(reason==='switch'){A.select('naruto-tenten-fuma');A.finish(1);A.assert(pose.emitted===emitted,'switched twin kept emitting');}
   if(reason==='clear')G.Combat.clearFields(p);
   if(reason==='death'){p.dead=true;A.advance();p.dead=false;}
   if(reason==='world'){G.World={...world};try{A.advance()}finally{G.World=world}}
   if(!['pause','switch'].includes(reason))A.assert(!T.activeFor(p)&&!T.weapons.some(w=>w.owner===p),'Tenten leaked '+reason);
   out.push(reason);
 }
 A.reset();A.select('naruto-tenten-twin');const cloneCard=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');
 A.assert(cloneCard,'clone card missing');cloneCard.apply(p);cloneCard.apply(p);const clones=G.SelfClones.actors();
 A.assert(clones.length===2,'two clones absent');const e=A.spawn(130,0);p.target=e;
 for(const actor of clones){
   A.near(actor.atk,p.atk/3,'clone damage ratio');A.near(actor.maxHp,p.maxHp/3,'clone HP');
   A.assert(actor.hasMove('naruto-tenten')&&actor.hasMove('naruto-tenten-mastery'),'clone passive mirror missing');
   actor.x=actor.y=0;actor.target=e;for(const m of actor.moves)m.t=999;
   const m=actor.moves.find(m=>m.id==='naruto-tenten-twin');m.t=0;
 }
 const hits=[],hurt=e.hurt;e.hurt=function(...args){const actor=args[6];if(clones.includes(actor)){
   const move=actor.moves.find(m=>m.id===args[7]);A.near(args[0],move.dmg*p.atk/3*G.Types.mult(move.type,e.types)*G.Weather.mult(move.type),'clone actual damage ratio applied twice');hits.push({actor:clones.indexOf(actor),id:args[7],damage:args[0]});}
   return hurt.apply(this,args)};
 A.advance();A.assert(clones.every(a=>T.weapons.some(w=>w.owner===a)),'clone selected attack/basic not independently owned');
 A.finish(.3);A.assert(clones.every((a,i)=>hits.some(h=>h.actor===i)),'both clones did not physically hit');
 const [a,b]=clones,own=T.weapons.filter(w=>w.owner===b).length;G.Combat.clearFields(a);
 A.assert(!T.weapons.some(w=>w.owner===a)&&T.weapons.filter(w=>w.owner===b).length===own,'one clone cleanup cleared sibling');
 const hp=b.hp;G.SelfClones.withSceneTransition(()=>G.Combat.clearFields());A.assert(G.SelfClones.actors().includes(b)&&b.hp===hp,'scene transition discarded living clone');
 out.push({twoClones:true,hits,ownedCleanup:true,scenePreserved:true});A.reset();return out;
}"""

HUD = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,cv=document.createElement('canvas');cv.width=innerWidth;cv.height=innerHeight;
 const ctx=cv.getContext('2d'),fill=ctx.fillText.bind(ctx),text=[];ctx.fillText=(value,...args)=>{text.push(String(value));return fill(value,...args)};
 const read=()=>{text.length=0;G.HUD.draw(ctx,innerWidth,innerHeight,p,{time:20});return [...text]};
 A.reset();const base=p.moves.find(m=>m.id==='naruto-tenten'),count=base.count;base.count=3;
 A.assert(read().includes('忍具 3'),'base HUD count absent');p.quantityPicks=p.quantityBonus=4;
 A.assert(read().includes('忍具 7'),'quantity HUD applied wrong count');
 A.assert(read().includes('貫穿 +3'),'tier5 mastery HUD missing');base.count=count;
 A.reset();p.target=A.spawn(180,0);A.castNative('naruto-tenten-twin');A.advance(.21);
 const pose=T.activeFor(p),snapshot=pose.count,label='忍具 '+pose.emitted+'/'+snapshot;
 A.assert(read().includes(label),'active twin emitted/count missing '+label);p.quantityPicks=p.quantityBonus=4;
 A.assert(pose.count===snapshot&&read().includes(label),'midcast HUD changed snapshotted total');
 const frozen={count:snapshot,emitted:pose.emitted,label};
 A.reset();p.target=A.spawn(150,0);A.castNative('naruto-tenten-fuma');let returning=0;
 for(let i=0;i<100&&!returning;i++){A.advance();returning=T.stateFor(p)?.returning||0}
 A.assert(returning>0&&read().includes('回收 '+returning),'fuma returning HUD absent');
 A.reset();return {base:3,quantity4:7,mastery:3,twin:frozen,returning};
}"""

PRESENTATION = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,out={};
 for(const id of ['naruto-tenten','naruto-tenten-fuma','naruto-tenten-tags','naruto-tenten-twin']){
   const outcomes=[];
   for(const drawing of [false,true,'disabled']){
     window.__TentenArtEnabled=drawing!=='disabled';A.assert(G.AnimationLab.enabled===window.__TentenArtEnabled,'renderer flag fixture not installed');
     A.reset();p.aim=0;p.anim.dir=2;const e=A.spawn(145,0);p.target=e;
     const random=Math.random;Math.random=()=>.5;
     try{A.castNative(id);const origins=T.weapons.map(w=>({x:w.x,y:w.y,dx:w.dx,dy:w.dy}));
       const hands=T.weapons.map(w=>{const h=G.AnimationLab.handForTenten(p,w.mode==='tenten-twin'?w.side:0);return {origin:[w.x,w.y],hand:h&&[h.x,h.y]}});
       A.assert(hands.every(h=>h.hand&&Math.hypot(h.origin[0]-h.hand[0],h.origin[1]-h.hand[1])<.001),'weapon origin detached from hand '+id+' '+JSON.stringify(hands));
       const state=G.AnimationLab.stateFor(p.anim);A.assert(id!=='naruto-tenten-fuma'||state.frame===1,'fuma release retained heldblade');
       const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');
       for(let i=0;i<150;i++){A.advance();if(drawing===true)A.render();else if(drawing==='disabled')p.anim.draw(ctx,100,100)}
       outcomes.push({origins,damage:100000-e.hp,remaining:T.weapons.length,hp:p.hp,x:p.x,y:p.y});
     }finally{Math.random=random;window.__TentenArtEnabled=true}
   }
   A.assert(outcomes.every(o=>JSON.stringify(outcomes[0])===JSON.stringify(o)),'rendering changed combat '+id+' '+JSON.stringify(outcomes));out[id]={...outcomes[0],compared:['no-draw','drawn','renderer-disabled']};
 }
 A.reset();return out;
}"""

ORIGINS = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,out=[],scale=p.anim.scale;
 try{for(const id of ['naruto-tenten','naruto-tenten-fuma','naruto-tenten-tags','naruto-tenten-twin'])for(const aim of [0,Math.PI,Math.PI/2,-Math.PI/2])for(const growth of [1,1.25]){
   A.reset();p.anim.scale=scale*growth;p.aim=aim;p.anim.dir=aim===Math.PI?6:aim===Math.PI/2?0:aim===-Math.PI/2?4:2;
   p.target=A.spawn(Math.cos(aim)*160,Math.sin(aim)*160);A.castNative(id);
   const shots=T.weapons.filter(w=>w.owner===p);A.assert(shots.length,'origin fixture emitted nothing '+id);
   for(const w of shots){const hand=G.AnimationLab.handForTenten(p,w.mode==='tenten-twin'?w.side:0);
     A.assert(hand&&Math.hypot(w.x-hand.x,w.y-hand.y)<.001,'mirrored/grown tool detached from hand');
     A.assert(w.dx*Math.cos(aim)+w.dy*Math.sin(aim)>0,'tool fired behind target-facing actor '+id+' '+aim);
     A.assert(Math.hypot(w.x-p.x,w.y-p.y)<100*growth,'origin escaped actor');}
   out.push({id,aim,growth,shots:shots.length});
 }}finally{p.anim.scale=scale;A.reset()}return out;
}"""

SOLID_PROPS = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,W=G.World,native=window.NativeTentenWorld,saved=Object.fromEntries(Object.entries(W).filter(([,v])=>typeof v==='function')),out={};
 const m=p.moves.find(m=>m.id==='naruto-tenten-tags'),count=m.count,baseDamage=m.dmg;m.count=1;m.dmg=36;
 const trace=(a,b,ignore)=>{const d=Math.hypot(b.x-a.x,b.y-a.y);for(let i=0;i<=Math.ceil(d/3);i++){
   const k=i/Math.max(1,Math.ceil(d/3)),block=native.projectileBlock(a.x+(b.x-a.x)*k,a.y+(b.y-a.y)*k,1);
   if(block&&block!==ignore)return block;}return null;};
 function plant(point,back){
   A.reset();Object.assign(W,native);p.x=point.x-back.x*80;p.y=point.y-back.y*80;p.aim=Math.atan2(back.y,back.x);
   const e=A.spawn(point.x,point.y);p.target=e;A.castNative(m.id);e.dead=true;G.EnemyMgr.rebuildGrid();
   let w;for(let i=0;i<100;i++){A.advance();w=T.weapons.find(w=>w.owner===p&&w.landed);if(w)break}
   A.assert(w,'native-world tagged kunai failed to plant');return w;
 }
 try{
   const props=native.propsInCircle(0,0,3200).filter(q=>q.solid&&q.destructible&&q.hp>0);
   let chosen;
   for(const rock of props.filter(q=>q.type==='rock')){for(let i=0;i<16;i++){
     const angle=i*Math.PI/8,d={x:Math.cos(angle),y:Math.sin(angle)},point={x:rock.x-d.x*(rock.r+18),y:rock.y-d.y*(rock.r+18)},launch={x:point.x-d.x*80,y:point.y-d.y*80};
     if(!trace(launch,point)&&trace(point,rock,rock)===null){chosen={rock,point,d};break}
   }if(chosen)break}
   A.assert(chosen,'no native destructible solid rock with an open firing lane');
   const {rock,point,d}=chosen,before=rock.hp,w=plant(point,d);A.assert(rock.hp===before,'tag impact damaged solid rock');
   const expected=w.damage;A.finish(.5);A.assert(rock.hp===before,'rock damaged before fuse');A.finish(.3);
   A.near(before-rock.hp,expected,'own solid rock skipped/damaged twice by blast');const after=rock.hp;A.finish(1);A.near(rock.hp,after,'rock damaged repeatedly after blast');
   out.ownRock={type:rock.type,position:[rock.x,rock.y],baseDamage:m.dmg,damage:before-rock.hp};
   let pair;
   for(const target of props.filter(q=>q.type==='rock'&&q.hp>0)){
     for(const barrier of props){if(barrier===target||barrier.hp<=0)continue;
       const distance=Math.hypot(target.x-barrier.x,target.y-barrier.y);if(distance<20||distance>45)continue;
       const dir={x:(target.x-barrier.x)/distance,y:(target.y-barrier.y)/distance},point={x:barrier.x-dir.x*(barrier.r+16),y:barrier.y-dir.y*(barrier.r+16)},launch={x:point.x-dir.x*80,y:point.y-dir.y*80};
       if(Math.hypot(target.x-point.x,target.y-point.y)>m.radius-4)continue;
       if(trace(point,target,target)!==barrier||trace(launch,point))continue;
       pair={target,barrier,point,dir};break;
     }if(pair)break;
   }
   A.assert(pair,'no native adjacent solid props for independent blocker fixture');
   const barrierHp=pair.barrier.hp;pair.barrier.hp=100000;
   try{const before=pair.target.hp;plant(pair.point,pair.dir);A.finish(1);
     A.near(pair.target.hp,before,'blast crossed another solid prop');out.blockedRock={target:[pair.target.x,pair.target.y],barrierType:pair.barrier.type,barrier:[pair.barrier.x,pair.barrier.y],damage:before-pair.target.hp};
   }finally{pair.barrier.hp=barrierHp}
 }finally{m.count=count;m.dmg=baseDamage;Object.assign(W,saved);A.reset()}
 return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'failedRequests': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for label, viewport, mobile in [('desktop', {'width': 1200, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
                context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                # Exercise the installer's public enabled option on the same
                # normal-entry runtime, without replacing combat or art assets.
                page.add_init_script('''Object.defineProperty(window,'AnimationRuntime',{configurable:true,set(runtime){
                  Object.defineProperty(window,'AnimationRuntime',{value:runtime,writable:true,configurable:true});
                  const install=runtime.install;runtime.install=function(G,options={}){return install.call(this,G,{...options,enabled:()=>window.__TentenArtEnabled!==false})};
                }});window.__TentenArtEnabled=true;''')
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.on('response', lambda r: report['failedRequests'].append(r.url) if r.status >= 400 and '127.0.0.1' in r.url else None)
                page.goto(URL)
                page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():
                    page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30009"]').click()
                assert page.evaluate('G.DB.save.partner===30009'), 'normal picker did not select Tenten'
                page.screenshot(path=str(OUT / f'{label}-menu.png'))
                page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30009 && G.Game.state==="playing"')
                page.evaluate("window.NativeTentenWorld=Object.fromEntries(Object.entries(G.World).filter(([,v])=>typeof v==='function'))")
                page.evaluate(HARNESS)
                page.evaluate(SETUP)
                page.evaluate(AUDIT)
                result = {}
                report['viewports'][label] = result
                for name, check in [('progression', PROGRESSION), ('combat', COMBAT), ('scaling', SCALING), ('lifecycle', LIFECYCLE), ('hud', HUD), ('presentationEquivalence', PRESENTATION), ('origins', ORIGINS), ('solidProps', SOLID_PROPS)]:
                    print(label, name, flush=True)
                    result[name] = page.evaluate(check)
                page.evaluate('Acceptance.reset();Acceptance.select("naruto-tenten-fuma");Acceptance.resume()')
                page.keyboard.press('Digit2')
                page.wait_for_function('G.Game.player.active===1')
                result['keyboardSwitch'] = page.evaluate('Acceptance.pause();G.Game.player.activeGroup().map(m=>m.id)')
                if mobile:
                    page.evaluate('Acceptance.resume()')
                    slot = page.evaluate('G.Touch.controlLayout(innerWidth,innerHeight,5).slots[2]')
                    page.touchscreen.tap(slot['x']+slot['w']/2, slot['y']+slot['h']/2)
                    page.wait_for_function('G.Game.player.active===2')
                    result['touchSwitch'] = page.evaluate('Acceptance.pause();G.Game.player.activeGroup().map(m=>m.id)')
                page.evaluate('Acceptance.reset()')
                page.keyboard.down('KeyD')
                result['keyboard'] = page.evaluate('''() => {const A=Acceptance,p=A.p(),x=p.x;A.resume();p.update(.08);A.pause();A.assert(p.x>x&&p.walking,'keyboard movement');return p.x-x}''')
                page.keyboard.up('KeyD')
                if mobile:
                    page.evaluate('Acceptance.reset();Acceptance.resume()')
                    client = context.new_cdp_session(page)
                    base = page.evaluate('G.Touch.stickBase()')
                    client.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': base['x'], 'y': base['y']}]})
                    client.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': base['x']+45, 'y': base['y']}]})
                    result['touch'] = page.evaluate('''() => {const A=Acceptance,p=A.p(),x=p.x;A.assert(G.Touch.vector()?.[0]>0,'native touch vector absent');p.update(.08);A.pause();A.assert(p.x>x,'native mobile touch failed');return p.x-x}''')
                    client.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                page.evaluate('''() => {const render=Acceptance.render;Acceptance.render=(...args)=>{
                  const calls=[],saved=CanvasRenderingContext2D.prototype.drawImage;
                  CanvasRenderingContext2D.prototype.drawImage=function(image,...rect){calls.push({src:image.src||image.dataset?.source||null,rect});return saved.call(this,image,...rect)};
                  try{const out=render(...args);out.drawCalls=calls;return out}finally{CanvasRenderingContext2D.prototype.drawImage=saved}}}''')
                result['art'] = {}
                for direction, key in [('right', 'KeyD'), ('down', 'KeyS'), ('left', 'KeyA'), ('up', 'KeyW')]:
                    page.evaluate('Acceptance.reset();Acceptance.finish(.6);Acceptance.resume()')
                    page.keyboard.down(key)
                    pose = page.evaluate('''() => {G.Game.player.update(.08);Acceptance.pause();return Acceptance.render()}''')
                    page.keyboard.up(key)
                    assert pose['state']['direction'] == direction, pose
                    assert pose['state']['state'] == 'movement', pose
                    assert pose['sources'] and all('tenten' in s for s in pose['sources']), pose
                    (OUT / f'{label}-walk-{direction}.png').write_bytes(base64.b64decode(pose.pop('png').split(',', 1)[1]))
                    result['art']['walk-'+direction] = pose
                for name, code in [('idle', 'Acceptance.reset()'), ('hurt', 'Acceptance.reset();Acceptance.resume();G.Game.player.hurt(7,null,true);Acceptance.pause()'), ('death', 'Acceptance.reset();G.Game.player.dead=true')]:
                    page.evaluate('() => {' + code + '}')
                    pose = page.evaluate('Acceptance.render()')
                    assert pose['sources'] and all('tenten' in s for s in pose['sources']), pose
                    (OUT / f'{label}-{name}.png').write_bytes(base64.b64decode(pose.pop('png').split(',', 1)[1]))
                    result['art'][name] = pose
                for id in [IDS[0], IDS[1], IDS[3], IDS[4]]:
                    page.evaluate('(id)=>{Acceptance.reset();G.Game.player.target=Acceptance.spawn(160,0);Acceptance.castNative(id);Acceptance.advance(id.endsWith("twin")?.35:.12);if(document.getElementById("ach-pop"))G.UI.hide("ach-pop");document.querySelectorAll(".toast").forEach(el=>el.style.display="none")}', id)
                    pose = page.evaluate('Acceptance.render()')
                    assert all('tenten' in s for s in pose['sources']), pose
                    (OUT / f'{label}-{id}-actor.png').write_bytes(base64.b64decode(pose.pop('png').split(',', 1)[1]))
                    result['art'][id] = pose
                    page.screenshot(path=str(OUT / f'{label}-{id}.png'))
                result['cloneArt'] = page.evaluate('''() => {const A=Acceptance,p=A.p();A.reset();A.select('naruto-tenten-twin');
                  const c=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');c.apply(p);c.apply(p);p.target=A.spawn(150,0);
                  for(const a of G.SelfClones.actors()){a.target=p.target;a.x=a.y=0;for(const m of a.moves)m.t=999;a.moves.find(m=>m.id==='naruto-tenten-twin').t=0;}
                  A.advance(.12);return G.SelfClones.actors().map(actor=>A.render(actor.anim));}''')
                for index, pose in enumerate(result['cloneArt']):
                    assert pose['sources'] and all('tenten' in s for s in pose['sources']), pose
                    (OUT / f'{label}-clone-{index}.png').write_bytes(base64.b64decode(pose.pop('png').split(',', 1)[1]))
                result['overflow'] = page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                assert result['overflow'], 'horizontal mobile overflow'
                result['newRun'] = page.evaluate('''() => {const old=G.Game.player;G.Game.toUI();G.Naruto.choose(30009);G.Flow.play();Acceptance.pause();
                  const p=G.Game.player;Acceptance.assert(p!==old&&p.dex===30009&&p.moves.length===1&&p.moves[0].id==='naruto-tenten','fresh playable starter');
                  Acceptance.assert(!G.SelfClones.actors().length&&!G.NarutoTenten.weapons.length&&!G.NarutoTenten.stateFor(old),'old run Tenten effects survived');
                  return {dex:p.dex,slots:p.slots.length,moves:p.moves.map(m=>m.id)}}''')
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        assert not report['failedRequests'], report['failedRequests']
        report['ok'] = True
    except Exception as error:
        report['ok'] = False
        report['failure'] = str(error)
        raise
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': report['ok'], 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
