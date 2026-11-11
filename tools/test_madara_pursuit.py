"""Bounded production-menu regression for Madara's body pursuit.

Uses real enemies, authored limb sockets and production damage. Open-ground
fixtures and direct simulation steps are controlled tests, not natural play.
Run tools/serve_animation_lab.py --port 8347 first.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_jujutsu as base
import test_madara_rework_play as native

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art-review/madara-pursuit-20261111/qa'
URL = os.environ.get('MADARA_PURSUIT_URL', 'http://127.0.0.1:8347/.omx/digimon.html?lang=zh-TW&layout=wide')

HELPERS = r'''() => {
 const A=JAcceptance,M=G.NarutoMadara,p=A.p(),assert=A.assert;
 const nativeAxis=G.Input.axis;
 function scene(rank=1,q=0){G.Input.axis=nativeAxis;A.reset();const m=A.fixture('naruto-madara',rank);p.quantityPicks=q;p.quantityBonus=0;p.atk=1;p.critChance=0;return m;}
 function cast(m){A.resume();try{assert(M.cast(p,m),'pursuit cast rejected');}finally{A.pause()}const f=M.stateFor(p)?.body;assert(f?.pursuit,'new pursuit missing');return f;}
 function step(){A.resume();try{p.anim.update(.01);M.update(.01)}finally{A.pause()}}
 function until(predicate,seconds=5){for(let i=0;i<seconds*100&&!predicate();i++)step();assert(predicate(),'pursuit phase wait expired')}
 function run(seconds=10){const samples=[];for(let i=0;i<seconds*100;i++){const s=M.stateFor(p),f=s?.body;if(!f)break;samples.push({t:s.clock,x:p.x,y:p.y,index:f.index,phase:f.pursuitPhase,target:f.target?.id,pose:M.pose(p)?.contact});step()}return samples;}
 function hits(s){return s.hitContacts.filter(c=>c.kind==='basic'&&c.source==='body');}
 window.PursuitTest={A,M,p,assert,scene,cast,run,step,until,hits,nativeAxis};
}'''

CASES = {
    'afterimages_low_quality_keeps_newest': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene();A.spawn(145,0);T.cast(m);T.until(()=>M.stateFor(p)?.afterimages?.length>0);const s=M.stateFor(p),newest=s.afterimages.at(-1),quality=G.Settings.get('quality'),draw=G.MadaraArt.draw,ctx=document.createElement('canvas').getContext('2d');let newestDraws=0;
 try{G.Settings.set('quality','low');assert(G.Settings.fx===0,'fixture not low quality');G.MadaraArt.draw=function(c,a,o){if(o.pose===newest.pose&&o.alpha>0)newestDraws++;return draw.call(this,c,a,o)};for(const d of M.drawables())d.draw(ctx);assert(newestDraws===1,'low quality skipped newest/only echo');return {snapshots:s.afterimages.length,newestDraws};}finally{G.MadaraArt.draw=draw;G.Settings.set('quality',quality)}
}''',
    'afterimages_are_visual_snapshots': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene(),enemy=A.spawn(145,0);T.cast(m);T.until(()=>M.stateFor(p)?.afterimages?.length>=3);const s=M.stateFor(p),image=s.afterimages[0],point={x:image.x,y:image.y,aim:image.pose.aim};p.x+=12;s.body.aim+=.2;assert(image.x===point.x&&image.y===point.y&&image.pose.aim===point.aim,'afterimage followed live body');p.x-=12;s.body.aim-=.2;
 const before=JSON.stringify(s.afterimages),hp=enemy.hp,damage=s.damage,canvas=document.createElement('canvas'),ctx=canvas.getContext('2d'),draw=G.MadaraArt.draw;let calls=0;
 G.MadaraArt.draw=function(c,a,o){if(o?.alpha>0&&o.alpha<1){calls++;assert(o.pose&&o.state==='cast','echo lost authored pose')}return draw.call(this,c,a,o)};
 try{for(let i=0;i<3;i++)for(const d of M.drawables())d.draw(ctx)}finally{G.MadaraArt.draw=draw}
 assert(calls>0&&before===JSON.stringify(s.afterimages),'draw mutated afterimages');assert(enemy.hp===hp&&s.damage===damage,'afterimages caused damage');M.update(.3);assert(before===JSON.stringify(s.afterimages),'paused trail advanced');
 let maximum=s.afterimages.length;for(let i=0;i<60;i++){T.step();maximum=Math.max(maximum,s.afterimages.length)}assert(maximum<=6,'unbounded trail');G.Input.axis=()=>[-1,0];for(let i=0;i<30;i++)T.step();G.Input.axis=T.nativeAxis;assert(!s.body&&s.afterimages.length===0,'cancel left afterimages');return {drawCalls:calls,maxSnapshots:maximum,damageFromDrawing:0};
}''',
    'afterimages_clear_with_skill': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene();A.spawn(145,0);T.cast(m);T.until(()=>M.stateFor(p)?.afterimages?.length>0);const s=M.stateFor(p);p.moves=p.moves.filter(x=>x.id!==m.id);T.step();assert(s.afterimages.length===0,'unlearn retained afterimages');M.clear(p);assert(!M.stateFor(p),'clear retained afterimage owner');return true;
}''',
    'three_hits_before_switch': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene(5,4),one=A.spawn(145,0),two=A.spawn(230,75),three=A.spawn(110,-130);T.cast(m);const s=M.stateFor(p),sequence=[],seen=new Set();
 for(let i=0;i<1000&&s.body;i++){const f=s.body;if(f.pursuitPhase==='contact'&&!seen.has(f.index)){seen.add(f.index);sequence.push({index:f.index,target:f.target.id});}T.step();}
 assert(sequence.length===12,'missing focused contacts');assert(sequence[0].target===one.id&&sequence.slice(0,3).every(x=>x.target===one.id),'first enemy not retained for three strikes '+JSON.stringify(sequence));
 for(let i=0;i<sequence.length;i+=3){assert(sequence.slice(i,i+3).every(x=>x.target===sequence[i].target),'focus changed within three-hit group');if(i)assert(sequence[i].target!==sequence[i-1].target,'did not switch after third hit');}
 return {sequence};
}''',
    'focus_death_retargets_early': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene(),one=A.spawn(145,0),two=A.spawn(220,65),events=A.watch(two),hurt=one.hurt;let firstHits=0;
 one.hurt=function(...args){firstHits++;const r=hurt.apply(this,args);this.dead=true;this.hp=0;return r};T.cast(m);const s=M.stateFor(p),sequence=[],seen=new Set();
 for(let i=0;i<1000&&s.body;i++){const f=s.body;if(f.pursuitPhase==='contact'&&!seen.has(f.index)){seen.add(f.index);sequence.push(f.target.id)}T.step();}
 assert(firstHits===1&&events.length>0,'death did not continue real hits');assert(sequence[0]===one.id&&sequence[1]===two.id,'dead focus blocked early switch '+JSON.stringify(sequence));return {sequence,firstHits,replacementHits:events.length};
}''',
    'pursuit_dodge_eighty_percent': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene(),e=A.spawn(145,0);T.cast(m);T.until(()=>M.stateFor(p).body?.pursuitPhase==='contact');const originalRandom=Math.random,context={cause:'contact',sourceEnemy:e,fromX:e.x,fromY:e.y};let dodges=0,hits=0;
 function incoming(roll,c=context,pure=false){p.hp=p.maxHp;p.invuln=0;const hp=p.hp;Math.random=()=>roll;A.resume();try{p.hurt(10,null,pure,c)}finally{A.pause()}return {dodged:p.hp===hp,invuln:p.invuln};}
 try{for(let i=0;i<10;i++){const r=incoming((i+.5)/10);if(r.dodged){dodges++;assert(r.invuln===0,'dodge granted immunity')}else hits++;}assert(dodges===8&&hits===2,'wrong dodge fraction');
 assert(!incoming(.8).dodged,'80percent boundary should hit');assert(incoming(.799999,{cause:'projectile',fromX:145,fromY:0}).dodged,'projectile not dodged');assert(!incoming(0,{cause:'hazard'}).dodged,'hazard dodged');assert(!incoming(0,context,true).dodged,'pure damage dodged');
 let f=M.stateFor(p).body;f.pursuitPhase='return';assert(!incoming(0).dodged,'return granted dodge');f.pursuitPhase='approach';f.age=0;assert(!incoming(0).dodged,'opening granted dodge');M.clear(p);assert(!incoming(0).dodged,'cancel retained dodge');return {dodges,hits,dodgeInvulnerability:0};
 }finally{Math.random=originalRandom;}
}''',
    'wood_army_appears_in_windows': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T;T.scene();assert(p.addMove('naruto-madara-clones'),'learn wood');const m=p.moves.find(x=>x.id==='naruto-madara-clones');
 A.resume();try{assert(M.cast(p,m),'first summon')}finally{A.pause()}
 for(let i=0;i<50;i++)T.step();const s=M.stateFor(p),expiry=s.armyExpires,ready=s.armyReadyAt,first=s.army.map(a=>a.serial);assert(first.length===2,'first summon count');
 for(let i=0;i<250;i++)T.step();Object.assign(m,G.Moves.instance(m.id,5));p.quantityPicks=4;T.step();assert(s.army.length===16,'growth failed');assert(s.armyExpires===expiry&&s.armyReadyAt===ready,'growth extended window');
 while(s.clock<expiry+.05)T.step();assert(s.army.length===0,'army did not withdraw');m.t=0;p.cdMul=.01;
 A.resume();try{assert(!M.canCast(p,m)&&!M.cast(p,m),'cooldown reduction bypassed rest')}finally{A.pause()}
 assert(M.statusFor(p,m).state==='cooldown','HUD hides rest');
 while(s.clock<ready+.01)T.step();A.resume();try{assert(M.cast(p,m),'next summon rejected')}finally{A.pause()}
 for(let i=0;i<45;i++)T.step();assert(s.army.length===16&&s.army.every(a=>!first.includes(a.serial)),'second wave not fresh');return {expiry,ready,minimumRest:ready-expiry,secondWave:s.army.length};
}''',
    'chain_and_quantity': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,out=[];
 for(const q of [0,1,4]){const m=T.scene(1,q),targets=[[150,0],[230,90],[160,-100],[850,0]].map(v=>A.spawn(...v)),events=targets.map(A.watch),f=T.cast(m),s=M.stateFor(p),samples=T.run(),contacts=T.hits(s),segments=[...new Set(contacts.map(c=>c.segment))];
 assert(!s.body,'chain did not finish');assert(segments.length===f.spec.contacts,'quantity missing real contact: '+JSON.stringify({q,segments,spec:f.spec.contacts,hits:events.map(x=>x.length)}));
 assert(events.slice(0,3).filter(x=>x.length>0).length>=2,'chain did not hit multiple enemies');assert(events[3].length===0,'out-of-range target hit');
 assert(Math.hypot(p.x,p.y)<2,'normal finish did not return');assert(p.invuln===0,'pursuit added invulnerability');
 const phases=[...new Set(samples.map(x=>x.phase))],poses=[...new Set(samples.map(x=>x.pose).filter(Boolean))];assert(['palm','elbow','kick'].every(x=>poses.includes(x)),'lost authored palm/elbow/kick '+poses);assert(samples.some(x=>x.phase==='contact'&&x.index===f.spec.contacts-1&&x.pose==='kick'),'finisher not a spinning kick');
 const targetsSeen=samples.filter(x=>x.phase==='contact'&&x.target).reduce((a,x)=>{if(a.at(-1)!==x.target)a.push(x.target);return a},[]);assert(targetsSeen.length>=2,'never switched targets');
 out.push({q,expected:f.spec.contacts,segments,damage:events.map(x=>x.reduce((n,h)=>n+h.loss,0)),phases,poses,targetsSeen,seconds:s.clock});}
 assert(out[1].expected>out[0].expected&&out[2].expected>out[1].expected,'quantity did not increase contacts');return out;
}''',
    'single_target_and_impetus': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene();assert(p.addMove('naruto-madara-susanoo'),'learn guardian');Object.assign(p.moves.find(x=>x.id==='naruto-madara-susanoo'),G.Moves.instance('naruto-madara-susanoo',2));const e=A.spawn(145,0),events=A.watch(e),f=T.cast(m),s=M.stateFor(p);T.run();
 assert(events.length===f.spec.contacts,'single target could not receive all contacts '+events.length);assert(s.impetus===1,'finisher momentum should be one '+s.impetus);A.advance(1);assert(s.impetus===1,'momentum repeated');return {hits:events.length,impetus:s.impetus};
}''',
    'target_death': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene(),one=A.spawn(140,0),two=A.spawn(160,55),events=A.watch(two),f=T.cast(m);one.dead=true;one.hp=0;T.run();assert(events.length>0,'dead target did not retarget');assert(!M.stateFor(p).body,'dead target stalled chain');return {replacementHits:events.length};
}''',
    'movement_cancels': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene(),e=A.spawn(160,0),events=A.watch(e);T.cast(m);A.advance(.08);const before={x:p.x,y:p.y,hits:events.length};G.Input.axis=()=>[-1,0];A.advance(.1);assert(!M.stateFor(p).body,'movement did not cancel');assert(p.x===before.x&&p.y===before.y,'cancel forced return or pursuit');A.advance(1);assert(events.length===before.hits,'cancel retained future damage');G.Input.axis=T.nativeAxis;return before;
}''',
    'pause_death_clear': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,out={};let m=T.scene();A.spawn(160,0);T.cast(m);A.advance(.08);let s=M.stateFor(p),clock=s.clock,point=[p.x,p.y];M.update(.5);assert(s.clock===clock&&p.x===point[0]&&p.y===point[1],'pause advanced pursuit');out.pause=true;p.dead=true;A.resume();try{M.update(.01)}finally{A.pause()}assert(!M.stateFor(p),'dead body retained');out.death=true;
 m=T.scene();const one=A.spawn(155,0),two=A.spawn(155,0);let h1=0,h2=0;const hurt1=one.hurt,hurt2=two.hurt;one.hurt=function(...args){h1++;const r=hurt1.apply(this,args);G.Combat.clearFields(p);return r};two.hurt=function(...args){h2++;return hurt2.apply(this,args)};T.cast(m);T.run();assert(h1===1&&h2===0,'same-wave cancellation hit next target '+JSON.stringify({h1,h2}));assert(!M.stateFor(p),'clear retained state');out.callbackClear={h1,h2};return out;
}''',
    'wall_blocks': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene(),e=A.spawn(160,0),events=A.watch(e),nativePath=G.World.projectilePathClear;
 G.World.isWall=(x,y)=>x>=65&&x<=85;G.World.isFree=(x,y)=>!(x>=65&&x<=85);G.World.projectilePathClear=(x,y,tx,ty)=>!((x<65&&tx>=65)||(tx<65&&x>=65));
 try{A.resume();let accepted;try{accepted=M.cast(p,m)}finally{A.pause()}if(accepted)T.run();assert(p.x<65&&events.length===0,'pursuit crossed wall or hit through wall');return {accepted,hits:events.length,x:p.x};}finally{G.World.projectilePathClear=nativePath;G.World.isWall=()=>false;G.World.isFree=()=>true}
}''',
    'moving_enemy': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene(),e=A.spawn(160,0),events=A.watch(e),f=T.cast(m);
 for(let i=0;i<16;i++){e.x+=1.5;e.y+=1;G.EnemyMgr.rebuildGrid();T.step()}const samples=T.run();assert(events.length===f.spec.contacts,'moving enemy lost contacts '+events.length);assert(samples.some(x=>Math.hypot(x.x,x.y)>50),'body did not pursue drift');return {hits:events.length,enemy:{x:e.x,y:e.y}};
}''',
    'return_input': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene();A.spawn(160,0);const f=T.cast(m);T.until(()=>f.pursuitPhase==='return');const point={x:p.x,y:p.y};assert(Math.hypot(p.x,p.y)>30,'return fixture never moved');G.Input.axis=()=>[1,0];T.step();assert(!M.stateFor(p).body,'return input did not cancel');assert(p.x===point.x&&p.y===point.y,'return cancellation snapped position');G.Input.axis=T.nativeAxis;return point;
}''',
    'finisher_miss': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene();assert(p.addMove('naruto-madara-susanoo'),'learn guardian');const e=A.spawn(145,0),events=A.watch(e),f=T.cast(m),s=M.stateFor(p);T.until(()=>f.index===f.spec.contacts-1&&f.pursuitPhase==='contact');assert(events.length>0,'miss fixture needs earlier hits');e.x=950;e.y=950;G.EnemyMgr.rebuildGrid();T.run();assert(s.impetus===0,'earlier contacts charged a missed finisher');return {earlierHits:events.length,impetus:s.impetus};
}''',
    'identity_cancellation': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,out={};let m=T.scene();A.spawn(160,0);T.cast(m);T.step();p.moves=[];p.slots=[];T.step();assert(!M.stateFor(p)?.body,'unlearned pursuit retained');out.unlearn=true;
 m=T.scene();A.spawn(160,0);T.cast(m);const world=G.World;G.World={...world};try{T.step();assert(!M.stateFor(p),'new world retained pursuit')}finally{G.World=world}out.world=true;
 m=T.scene();A.spawn(160,0);T.cast(m);G.CombatPulse.beginRun();T.step();assert(!M.stateFor(p),'new run epoch retained pursuit');out.epoch=true;return out;
}''',
    'dynamic_wall': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,out={},nativePath=G.World.projectilePathClear;
 function barrier(x){G.World.isWall=(px,py)=>Math.abs(px-x)<2;G.World.isFree=(px,py)=>Math.abs(px-x)>=2;G.World.projectilePathClear=(px,py,tx,ty)=>!((px<x&&tx>=x)||(tx<x&&px>=x));}
 try{let m=T.scene();let e=A.spawn(170,0),events=A.watch(e),f=T.cast(m);T.until(()=>p.x>12&&f.pursuitPhase==='approach');let x=p.x+7;barrier(x);T.run();assert(p.x<x&&events.length===0,'new approach obstacle crossed or hit through');out.approach={wall:x,x:p.x,hits:events.length};
 G.World.projectilePathClear=nativePath;m=T.scene();A.spawn(170,0);f=T.cast(m);T.until(()=>f.pursuitPhase==='return');x=p.x/2;barrier(x);T.run();assert(p.x>x&& !M.stateFor(p).body,'new return obstacle crossed or stalled');out.return={wall:x,x:p.x};return out;
 }finally{G.World.projectilePathClear=nativePath;G.World.isWall=()=>false;G.World.isFree=()=>true}
}''',
    'directional_contacts': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,out=[];
 for(const rank of [1,5])for(const aim of [0,Math.PI/2,Math.PI,-Math.PI/2]){const m=T.scene(rank,rank===5?4:0),e=A.spawn(Math.cos(aim)*145,Math.sin(aim)*145),events=A.watch(e),f=T.cast(m),s=M.stateFor(p);T.run();const segments=[...new Set(T.hits(s).map(c=>c.segment))];assert(segments.length===f.spec.contacts,'direction missed real contacts '+JSON.stringify({rank,aim,segments,expected:f.spec.contacts}));assert(segments.includes(f.spec.contacts-1),'directional final kick missed');assert(Math.hypot(p.x,p.y)<2,'directional return failed');out.push({rank,aim,hits:events.length,segments});}return out;
}''',
    'retreat_after_finisher_hit': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene();assert(p.addMove('naruto-madara-susanoo'),'learn guardian');const e=A.spawn(145,0),events=A.watch(e),f=T.cast(m),s=M.stateFor(p);T.until(()=>f.index===f.spec.contacts-1&&f.pursuitPhase==='contact'&&f.segment?.hits>0);assert(s.impetus===1,'final real hit did not immediately credit momentum');const count=events.length,point={x:p.x,y:p.y};G.Input.axis=()=>[-1,0];T.step();assert(!s.body,'retreat after final hit retained pursuit');assert(s.impetus===1,'retreat erased final-hit momentum');assert(p.x===point.x&&p.y===point.y,'retreat moved player');for(let i=0;i<100;i++)T.step();assert(events.length===count&&s.impetus===1,'retreat retained future hit or double credit');G.Input.axis=T.nativeAxis;return {hits:count,impetus:s.impetus,cancelPoint:point};
}''',
    'three_finishers_transform_guardian': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene();assert(p.addMove('naruto-madara-susanoo'),'learn guardian');const guardian=p.moves.find(x=>x.id==='naruto-madara-susanoo');Object.assign(guardian,G.Moves.instance(guardian.id,2));A.spawn(90,0);A.resume();try{assert(M.cast(p,guardian),'actual guardian cast rejected')}finally{A.pause()}const s=M.stateFor(p),original=s.guardian,rounds=[];assert(original&&!original.perfect,'guardian not initially ordinary');for(let i=0;i<3;i++){m.t=0;T.cast(m);T.run();rounds.push({impetus:s.impetus,perfect:s.guardian?.perfect,clock:s.clock});}assert(s.guardian===original,'transform replaced or expired actual guardian');assert(original.perfect&&s.impetus===0&&s.perfectCount===1,'three finishers did not transform same guardian '+JSON.stringify(rounds));return {rounds,perfectCount:s.perfectCount,form:original.form};
}''',
    'wood_army_stays_local': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene(5,4);assert(p.addMove('naruto-madara-clones'),'learn wood doubles');assert(p.addMove('naruto-madara-susanoo'),'learn guardian for no-army-momentum check');const clones=p.moves.find(x=>x.id==='naruto-madara-clones');Object.assign(clones,G.Moves.instance(clones.id,2));A.spawn(90,0);A.spawn(-90,0);A.spawn(0,90);A.resume();try{assert(M.cast(p,clones),'actual army cast rejected')}finally{A.pause()}const s=M.stateFor(p),observed=[];for(let i=0;i<350;i++){T.step();for(const a of s.army){if(a.body?.spec.kind==='basic'){assert(!a.body.pursuit,'wood double copied body pursuit');assert(a.body.spec.contacts===8&&a.body.spec.duration<=.82,'legacy wood combo count/duration changed');if(!observed.some(x=>x.serial===a.serial))observed.push({serial:a.serial,contacts:a.body.spec.contacts,duration:a.body.spec.duration});}}}assert(observed.length>0,'army never performed a local combo');assert(s.hitContacts.some(c=>c.channel==='army-body'&&c.primaryHits>0),'army local combo did not deal real damage');assert(s.impetus===0,'wood army generated body momentum');return {observed,impetus:s.impetus,army:s.army.length};
}''',
    'real_quantity_card': r'''() => {
 const T=PursuitTest,{A,M,p,assert}=T,m=T.scene();const before=M.vector(p,m),card=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');assert(card,'real quantity card missing');assert(card.apply(p)!==false,'real quantity card rejected');const after=M.vector(p,m);assert(before['接觸連段']===4&&after['接觸連段']===5,'real quantity card preview not4to5');const e=A.spawn(145,0),events=A.watch(e),f=T.cast(m),s=M.stateFor(p);T.run();const segments=[...new Set(T.hits(s).map(c=>c.segment))];assert(segments.length===5&&events.length===5,'real quantity card did not yield five contacts');return {before,after,quantityPicks:p.quantityPicks,segments,hits:events.length};
}''',
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'scope': 'controlled production runtime regression', 'cases': {}, 'errors': [], 'sourceSha256': hashlib.sha256((ROOT / '.omx/naruto-madara.js').read_bytes()).hexdigest()}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 900}, service_workers='block')
        page = context.new_page()
        page.on('pageerror', lambda e: report['errors'].append(str(e)))
        page.goto(URL)
        frame = native.frame_for(page)
        frame.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
        if frame.locator('#tap-start').is_visible():
            frame.locator('#tap-start').click()
        frame.locator('[data-quick-naruto="30016"]').click()
        frame.wait_for_function('G.NarutoAssets.ready(30016)')
        frame.locator('#scr-menu [data-go="play"]').click()
        frame.wait_for_function('G.Game.player?.dex===30016&&G.Game.state==="playing"')
        frame.evaluate(base.SETUP)
        frame.evaluate(HELPERS)
        for name, script in CASES.items():
            try:
                result = frame.evaluate(script)
                report['cases'][name] = {'ok': True, 'result': result}
                print(name, 'PASS', flush=True)
            except Exception as exc:
                report['cases'][name] = {'ok': False, 'error': str(exc)}
                print(name, 'FAIL', str(exc).splitlines()[0], flush=True)
        context.close()
        browser.close()
    report['ok'] = all(c['ok'] for c in report['cases'].values()) and not report['errors']
    (OUT / 'mechanics.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    if not report['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
