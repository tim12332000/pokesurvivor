"""Uro real fracture waves, reaction counters and final-contact echoes."""
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('URO_FRACTURE_OUT',ROOT/'.omx/state/duet-fracture/uro/after'))

CHECK=r"""() => {
 const A=JAcceptance,p=A.p(),U=G.JjkUro,assert=A.assert,out={};
 function setup(id='jjk-uro-thin-ice',rank=1,q=0){A.reset();p.statsTaken={};const m=A.fixture(id,rank);p.quantityPicks=p.quantityBonus=q;return m;}
 function cast(m,owner=p){A.resume();try{assert(U.cast(owner,m),'cannot cast '+m.id)}finally{A.pause()};return U.activeFor(owner);}
 function reflect(source){const shot=G.Projectiles.spawn({x:80,y:0,px:170,py:0,vx:-200,vy:0,r:6,life:3,dmg:7,mtype:'psychic',friendly:false,sourceEnemy:source});
  A.resume();try{U.intercept()}finally{A.pause()};assert(!G.Projectiles.all().includes(shot),'did not actually reflect');}
 function screen(rank=1,thin=false,q=0){const m=setup('jjk-uro-screen',rank,q);if(thin)assert(p.addMove('jjk-uro-thin-ice'),'learn thin');
  G.Projectiles.spawn({x:180,y:0,vx:-200,vy:0,r:6,life:3,dmg:7,friendly:false});cast(m);G.Projectiles.clear();return m;}
 for(const rank of [1,5]){
  const palm=setup('jjk-uro',rank),profile=U.fractureProfile(p,palm),near=A.spawn(profile.range-20,0),far=A.spawn(profile.range+100,0),boss=A.spawn(100,30,'boss'),knock=[];
  const hurt=boss.hurt;boss.hurt=function(...args){knock.push(args[4]);return hurt.apply(this,args)};cast(palm);A.advance(.3);
  assert(near.hp<near.maxHp&&far.hp===far.maxHp&&boss.hp<boss.maxHp&&knock.length===1&&knock[0]===0,'palm range/special resistance '+rank);
  out['palm'+rank]=profile;
 }
 for(const id of ['jjk-uro-thin-ice','jjk-uro-collapse'])for(const [rank,q,count] of [[1,0,4],[1,1,5],[5,0,8],[5,20,16]]){
  const m=setup(id,rank,q),prof=U.fractureProfile(p,m),es=id.endsWith('collapse')?[A.spawn(450,0),A.spawn(480,65),A.spawn(470,-65)]:[A.spawn(150,0),A.spawn(200,75),A.spawn(240,-60)],outside=A.spawn(-500,600);
  const events=es.map(A.watch);cast(m);A.advance(3);
  assert(prof.count===count&&events.every(e=>e.length===count)&&outside.hp===outside.maxHp,'real wave count/boundary '+id+'/'+rank+'/'+q);
  assert(events.every(h=>h.every(e=>e.id===id&&e.owner)),'wave attribution differs');
  out[id+'-'+rank+'-'+q]={profile:prof,hits:events.map(e=>e.length),outside:outside.maxHp-outside.hp};
 }
 let m=setup(),e=A.spawn(150,0),hits=A.watch(e);cast(m);A.advance(.33);assert(hits.length===0,'thin hit before .34');A.advance(.02);
 assert(hits.length===1&&Math.abs(hits[0].raw/(m.dmg*p.atk)-1.2)<1e-8,'first thin multiplier/time');A.advance(1.1);
 assert(hits.length===4&&Math.abs(hits[1].raw/(m.dmg*p.atk)-.55)<1e-8&&Math.abs(hits[3].raw/(m.dmg*p.atk)-1)<1e-8,'middle/final thin multipliers');out.thinDamage=hits.map(e=>e.raw);
 m=setup();e=A.spawn(150,0);let b=cast(m);A.advance(.35);const mark={...b.contactMarks[0]};p.y=400;
 const moved=A.spawn(160,400);A.advance(.34);assert(moved.hp<moved.maxHp&&b.contactMarks.at(-1).y===400&&mark.y===0,'fan did not follow each contact or old mark moved');out.liveFan=true;
 m=setup('jjk-uro-collapse');e=A.spawn(450,0);b=cast(m);const center=[b.tx,b.ty];p.y=600;A.advance(.9);
 assert(!U.activeFor(p)&&U.effects.includes(b)&&b.tx===center[0]&&b.ty===center[1],'remote field kept body locked or followed caster');
 assert(p.addMove('jjk-uro'),'learn palm during field');const palm=p.moves.find(m=>m.id==='jjk-uro');palm.t=0;A.spawn(80,600);cast(palm);A.advance(1.2);assert(e.hp<e.maxHp&&b.done,'independent collapse failed');out.independentCollapse=true;
 m=setup();e=A.spawn(150,0);cast(m);G.World.projectilePathClear=()=>false;A.advance(3);assert(e.hp===e.maxHp,'waves crossed wall');G.World.projectilePathClear=()=>true;out.wall=true;
 m=setup();e=A.spawn(150,0);const slow=[],knocks=[],nativeSlow=e.applySlow,nativeHurt=e.hurt;e.applySlow=function(...args){slow.push(args);return nativeSlow.apply(this,args)};
 e.hurt=function(...args){knocks.push(args[4]);return nativeHurt.apply(this,args)};cast(m);A.advance(2);
 assert(slow.length===2&&knocks.join(',')==='28,0,0,28','thin reapplied control on middle waves');out.controlContacts={slow:slow.length,knocks};
 m=setup('jjk-uro-screen',1);const before=U.fractureProfile(p,m);G.Projectiles.spawn({x:200,y:0,vx:-200,vy:0,r:6,life:3,dmg:7,friendly:false});b=cast(m);
 assert(b.budget===12&&b.duration===3.5&&b.radius===110,'rank1 screen physical profile');G.Projectiles.clear();
 e=A.spawn(0,400);hits=A.watch(e);const counterKnocks=[],counterHurt=e.hurt;e.hurt=function(...args){counterKnocks.push(args[4]);return counterHurt.apply(this,args)};
 reflect(e);const s=U.stateFor(p),chain=U.effects.find(f=>f.mode==='uro-counter');
 assert(chain&&chain.pulseCount===4&&!p.hasMove('jjk-uro-thin-ice')&&s.counterChains===1,'rank1 did not make independent screen counter');
 reflect(e);assert(s.counterChains===1,'same screen duplicated counter');A.advance(1.5);
 assert(hits.length===4&&hits.every(h=>h.id==='jjk-uro-screen')&&counterKnocks.every(n=>n===0),'counter invented thin/control or missed source');out.counterUnlearned={hits:hits.length,budget:b.budget};
 for(const [rank,q,count,budget] of [[1,1,5,15],[5,20,16,64]]){
  screen(rank,false,q);e=A.spawn(0,400);hits=A.watch(e);const shield=U.stateFor(p).screen;assert(shield.budget===budget&&shield.initialBudget===budget,'quantity screen budget snapshot differs');
  reflect(e);A.advance(3);assert(hits.length===count&&hits.every(h=>h.id==='jjk-uro-screen'),'counter quantity count differs');
  out['counter-'+rank+'-'+q]={hits:hits.length,budget};
 }
 screen();assert(p.addMove('jjk-uro-echo'),'learn echo with counter');e=A.spawn(300,0);reflect(e);A.advance(2);
 assert(U.stateFor(p).echoChains===0&&!U.effects.some(f=>f.mode==='uro-counter'||f.mode==='uro-echo'),'counter recursed or outlived own chain');out.counterNoRecursion=true;
 m=setup();const near=A.spawn(100,0);b=cast(m);assert(p.addMove('jjk-uro-screen'),'learn concurrent screen');const shield=p.moves.find(m=>m.id==='jjk-uro-screen');shield.t=0;
 G.Projectiles.spawn({x:180,y:0,vx:-200,vy:0,r:6,life:3,dmg:7,friendly:false});cast(shield);assert(U.activeFor(p)===b,'screen replaced body wave');G.Projectiles.clear();e=A.spawn(0,450);reflect(e);
 const cd=m.t;A.advance(.21);assert(m.t===cd&&U.activeFor(p)===b&&U.effects.some(f=>f.mode==='uro-counter'&&f.pulseIndex===0),'counter refreshed/replaced thin instead of independent reaction');out.concurrent=true;
 for(const invalid of ['unknown','dead','range','removed','wall']){
  screen();const nearest=A.spawn(60,0),source=A.spawn(0,450);reflect(invalid==='unknown'?null:source);
  if(invalid==='dead'){source.dead=true;source.hp=0}if(invalid==='range')source.y=900;
  if(invalid==='removed'){G.EnemyMgr.clear();G.EnemyMgr.add(nearest);G.EnemyMgr.rebuildGrid()}
  if(invalid==='wall')G.World.projectilePathClear=(x,y,tx,ty)=>ty<300;
  A.advance(.21);const counter=U.effects.find(f=>f.mode==='uro-counter');assert(counter.contactMarks[0].tx===nearest.x&&counter.contactMarks[0].ty===nearest.y,'counter did not fallback '+invalid);
  G.World.projectilePathClear=()=>true;out['fallback-'+invalid]=true;
 }
 for(const id of ['jjk-uro','jjk-uro-thin-ice','jjk-uro-collapse']){
  m=setup(id);assert(p.addMove('jjk-uro-echo'),'learn fifth passive');const passive=p.moves.find(m=>m.id==='jjk-uro-echo');
  e=A.spawn(id.endsWith('collapse')?450:100,0);hits=A.watch(e);const echoKnocks=[],echoHurt=e.hurt;e.hurt=function(...args){if(args[7]===passive.id)echoKnocks.push(args[4]);return echoHurt.apply(this,args)};b=cast(m);A.advance(3);
  const parents=hits.filter(h=>h.id===id),echoes=hits.filter(h=>h.id===passive.id);
  assert(parents.length===b.pulseCount&&echoes.length===2&&U.stateFor(p).echoChains===1&&echoKnocks.every(n=>n===0),'final actual body hit failed once-only echo/control '+id);
  out['echo-'+id]={body:parents.length,echo:echoes.length};
 }
 for(const [rank,q,count] of [[3,0,3],[5,0,4],[5,20,8]]){
  m=setup('jjk-uro');assert(p.addMove('jjk-uro-echo'),'learn rank echo');const passive=p.moves.find(m=>m.id==='jjk-uro-echo');Object.assign(passive,G.Moves.instance(passive.id,rank));p.quantityPicks=p.quantityBonus=q;
  e=A.spawn(100,0);hits=A.watch(e);cast(m);A.advance(3);assert(hits.filter(h=>h.id===passive.id).length===count,'echo rank/quantity count differs');out['echo-'+rank+'-'+q]=count;
 }
 m=setup();assert(p.addMove('jjk-uro-echo'),'learn echo for miss');e=A.spawn(100,0);b=cast(m);e.x=-600;G.EnemyMgr.rebuildGrid();A.advance(3);assert(U.stateFor(p).echoChains===0,'missed final hit created fake echo');out.noFakeEcho=true;
 m=setup();assert(p.addMove('jjk-uro-echo'),'learn fixed echo');e=A.spawn(100,0);b=cast(m);A.advance(1.35);const echo=U.effects.find(f=>f.mode==='uro-echo'),locked=[echo.x,echo.y,echo.aim];
 p.y=500;A.advance(.4);assert(echo.x===locked[0]&&echo.y===locked[1]&&echo.aim===locked[2],'echo moved with caster');out.fixedEcho=true;
 m=setup();const growth=G.JujutsuGrowth.quantityBenefit(p),card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:quantity');assert(card&&growth.eligible,'legal quantity card missing');
 assert(U.fractureProfile(p,m).count===4&&card.apply(p)!==false&&U.fractureProfile(p,m).count===5,'first quantity card not real 4to5 waves');out.legalQuantity=growth.text;
 for(const cancel of ['pause','frozen','death','clear','unlearn','world','epoch']){
  m=setup();e=A.spawn(100,0);b=cast(m);A.advance(.35);const hp=e.hp,age=b.age,world=G.World;
  if(cancel==='pause')U.update(4);else if(cancel==='frozen'){p.frozen=true;A.advance(2)}else{
   if(cancel==='death'){p.dead=true;p.hp=0}if(cancel==='clear')G.Combat.clearFields(p);if(cancel==='unlearn')p.moves=[];
   if(cancel==='world')G.World=Object.create(world);if(cancel==='epoch')G.CombatPulse.beginRun();
   try{A.advance(2)}finally{G.World=world}
  }
  assert(e.hp===hp&&(cancel==='pause'||cancel==='frozen'?b.age===age:!U.effects.includes(b)),'lifecycle '+cancel);out[cancel]=true;
 }
 for(const mode of ['clear','death','epoch','unlearn']){
  m=setup();e=A.spawn(100,0);const next=A.spawn(140,0);hits=A.watch(e);b=cast(m);const onDealt=p.onDealt;p.onDealt=function(...args){
   if(mode==='clear')G.Combat.clearFields(p);if(mode==='death'){p.dead=true;p.hp=0}if(mode==='epoch')G.CombatPulse.beginRun();if(mode==='unlearn')p.moves=[];
   return onDealt.apply(this,args)};
  try{A.resume();try{U.update(4)}finally{A.pause()}}finally{p.onDealt=onDealt}
  assert(hits.length===1&&next.hp===next.maxHp&&!U.effects.length,'same-dt callback recreated state or later victim/wave damage '+mode);out['callback-'+mode]=true;
 }
 m=setup('jjk-uro-thin-ice',5,20);e=A.spawn(100,0);hits=A.watch(e);b=cast(m);A.resume();try{U.update(4);U.update(4)}finally{A.pause()}
 assert(hits.length===16&&!U.effects.includes(b),'large dt lost/repeated waves');out.largeDt=hits.length;
 m=setup();e=A.spawn(100,0);const clone=G.SelfClones.summon(p);assert(clone,'clone absent');const cm=clone.moves.find(x=>x.id===m.id);cm.t=0;
 const a=cast(m),c=cast(cm,clone);assert(a.castId!==c.castId,'clone shared cast');U.clear(p);A.advance(2);
 assert(U.stateFor(clone)?.hits>0&&!U.stateFor(p),'owner clear cancelled clone');out.clone=true;
 return out;
}"""

class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def presentation(page,frame,label):
 evidence={}
 def shot(name):
  page.wait_for_timeout(55);page.screenshot(path=str(OUT/f'{label}-{name}.png'))
  evidence[name]=frame.evaluate("""()=>({fields:G.JjkUro.effects.map(b=>({id:b.id,mode:b.mode,pulse:b.pulseIndex,count:b.pulseCount,shape:b.shape,source:[b.sourceX,b.sourceY],center:[b.tx,b.ty],marks:b.contactMarks.map(m=>({x:m.x,y:m.y,pulse:m.pulseIndex,final:m.finisher}))})),hud:JAcceptance.p().moves.map(m=>({id:m.id,label:G.RunInsights.skillState(JAcceptance.p(),m).label})),vfx:G.JujutsuVFX.inspect().frame})""")
 frame.evaluate("""()=>{const A=JAcceptance;A.reset();A.fixture('jjk-uro-thin-ice',3);const p=A.p();p.quantityPicks=p.quantityBonus=1;p.invuln=999;
  p.addMove('jjk-uro-echo');for(const [x,y]of [[130,0],[250,60],[300,-90],[440,50]])A.spawn(x,y);
  A.resume();try{G.JjkUro.cast(p,p.moves[0])}finally{A.pause()};}""")
 for dt,name in [(.20,'thin-prepare'),(.15,'thin-first'),(.40,'thin-middle'),(.61,'thin-finisher'),(.23,'thin-echo')]:
  frame.evaluate('dt=>JAcceptance.advance(dt)',dt);shot(name)
 frame.evaluate("""()=>{const A=JAcceptance;A.reset();A.fixture('jjk-uro-collapse',3);const p=A.p();p.addMove('jjk-uro');p.addMove('jjk-uro-echo');
  for(const [x,y]of [[420,0],[450,80],[450,-80]])A.spawn(x,y);A.resume();try{G.JjkUro.cast(p,p.moves[0])}finally{A.pause()};A.advance(.9);
  const palm=p.moves.find(m=>m.id==='jjk-uro');palm.t=0;A.spawn(100,0);A.resume();try{G.JjkUro.cast(p,palm)}finally{A.pause()};A.advance(.19);}""")
 shot('collapse-body-parallel')
 frame.evaluate("""()=>{const A=JAcceptance;A.reset();A.fixture('jjk-uro-thin-ice',3);const p=A.p();p.addMove('jjk-uro-screen');p.addMove('jjk-uro-echo');A.spawn(130,0);const source=A.spawn(300,100);
  A.resume();try{G.JjkUro.cast(p,p.moves[0])}finally{A.pause()};A.advance(.1);
  const m=p.moves.find(m=>m.id==='jjk-uro-screen');m.t=0;G.Projectiles.spawn({x:170,y:0,vx:-220,vy:0,r:6,life:3,dmg:7,friendly:false});
  A.resume();try{G.JjkUro.cast(p,m)}finally{A.pause()};G.Projectiles.clear();G.Projectiles.spawn({x:70,y:0,px:170,py:0,vx:-220,vy:0,r:6,life:3,dmg:7,friendly:false,sourceEnemy:source});
  A.resume();try{G.JjkUro.intercept()}finally{A.pause()};}""")
 shot('screen-reflection');frame.evaluate('JAcceptance.advance(.22)');shot('independent-counter')
 frame.evaluate("G.JujutsuVFX.setQuality('low')");shot('counter-low-quality');frame.evaluate("G.JujutsuVFX.setQuality('auto')")
 evidence['stress']=frame.evaluate("""async()=>{
  const A=JAcceptance;A.reset();A.fixture('jjk-uro-collapse',5);const p=A.p();p.level=30;
  for(const id of ['jjk-uro-thin-ice','jjk-uro-screen','jjk-uro-echo'])p.addMove(id);
  for(const m of p.moves){Object.assign(m,G.Moves.instance(m.id,5));m.t=0}p.quantityPicks=p.quantityBonus=6;p.invuln=999;
  const actors=[p,...Array.from({length:3},()=>G.SelfClones.summon(p))];A.assert(actors.every(Boolean),'stress clones absent');
  for(const [i,actor]of actors.entries()){actor.x=i*180;actor.y=0;actor.invuln=999;A.spawn(actor.x+100,0);A.spawn(actor.x,400);
   A.resume();try{G.JjkUro.cast(actor,actor.moves.find(m=>m.id==='jjk-uro-collapse'))}finally{A.pause()}}
  A.advance(.9);
  for(const actor of actors){A.resume();try{G.JjkUro.cast(actor,actor.moves.find(m=>m.id==='jjk-uro-thin-ice'))}finally{A.pause()}
   const shield=actor.moves.find(m=>m.id==='jjk-uro-screen');shield.t=0;G.Projectiles.spawn({x:actor.x,y:180,vx:0,vy:-220,r:6,life:3,dmg:1,friendly:false});
   A.resume();try{G.JjkUro.cast(actor,shield)}finally{A.pause()};G.Projectiles.spawn({x:actor.x,y:70,px:actor.x,py:170,vx:0,vy:-220,r:6,life:3,dmg:1,friendly:false});
   A.resume();try{G.JjkUro.intercept()}finally{A.pause()}}
  const initialFields=G.JjkUro.effects.length;G.Spawner.update=()=>{};G.Game.debugSpeed(1);
  const samples=[],intervals=[],start=performance.now();let previous=start;A.resume();
  await new Promise(resolve=>{function sample(now){const v=G.JujutsuVFX.inspect();samples.push({snapshots:v.snapshots,triangles:v.triangles,shards:v.shards,captures:v.capturesTotal,fields:G.JjkUro.effects.length});
   intervals.push(now-previous);previous=now;if(now-start>=3000){resolve();return}requestAnimationFrame(sample)}requestAnimationFrame(sample)});A.pause();
  const captures=G.JujutsuVFX.inspect().capturesTotal;await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
  A.assert(G.JujutsuVFX.inspect().capturesTotal===captures,'paused stress recaptured background');
  const low=innerWidth<=700;A.assert(samples.every(s=>s.snapshots<=(low?1:2)&&s.triangles<=(low?12:48)&&s.shards<=24),'stress exceeded global VFX budgets');
  intervals.sort((a,b)=>a-b);return {scope:'3 native RAF seconds, four native owners, quantity6, simultaneous thin/collapse/counter/echo; frame intervals include full game and render',
   owners:actors.length,initialFields,samples: samples.filter((s,i)=>i%12===0),maxSnapshots:Math.max(...samples.map(s=>s.snapshots)),maxTriangles:Math.max(...samples.map(s=>s.triangles)),maxShards:Math.max(...samples.map(s=>s.shards)),
   frameCount:intervals.length,p50:intervals[Math.floor(intervals.length*.5)],p95:intervals[Math.floor(intervals.length*.95)],capturesAtPause:captures};
 }""")
 shot('four-owner-stress')
 clip=frame.evaluate("""async()=>{
  const A=JAcceptance;A.reset();const p=A.p();A.fixture('jjk-uro',3);p.level=20;for(const id of G.Moves.poolFor(p.mon))if(!p.hasMove(id))p.addMove(id);
  for(const m of p.moves){Object.assign(m,G.Moves.instance(m.id,3));m.t=0}p.quantityPicks=p.quantityBonus=2;p.invuln=999;
  for(let i=0;i<12;i++){const a=i*Math.PI/6;A.spawn(Math.cos(a)*230,Math.sin(a)*170)}
  G.Spawner.update=()=>{};G.Game.debugSpeed(1);G.Audio.unlock();G.Audio.settings.muted=false;G.Audio.setVolume('sfx',.7);G.Audio.setVolume('music',.05);
  const stream=document.getElementById('game').captureStream(24),audio=G.Audio.debugStream(true);if(audio)for(const track of audio.getAudioTracks())stream.addTrack(track);
  const mime=MediaRecorder.isTypeSupported('video/webm;codecs=vp9,opus')?'video/webm;codecs=vp9,opus':'video/webm',rec=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:2200000}),chunks=[];
  rec.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};const done=new Promise(resolve=>rec.onstop=()=>{const reader=new FileReader;reader.onload=()=>resolve(reader.result);reader.readAsDataURL(new Blob(chunks,{type:mime}))});
  const source=G.EnemyMgr.all()[0];let shots=0;const timer=setInterval(()=>{if(G.Game.state==='playing'){G.Projectiles.spawn({x:p.x+180,y:p.y,vx:-220,vy:0,r:6,life:2,dmg:1,friendly:false,sourceEnemy:source});shots++}},500);
  rec.start();A.resume();await new Promise(resolve=>setTimeout(resolve,4800));A.pause();clearInterval(timer);rec.stop();const data=await done,tracks=stream.getAudioTracks().length;
  for(const track of stream.getTracks())track.stop();return {data,audioTracks:tracks,shots,skills:p.moves.map(m=>m.id),fields:G.JjkUro.effects.map(b=>({mode:b.mode,pulse:b.pulseIndex,count:b.pulseCount}))};
 }""")
 (OUT/f'{label}-native-fracture-audio.webm').write_bytes(base64.b64decode(clip.pop('data').split(';base64,',1)[1]));evidence['clip']=clip
 return evidence

def main():
 OUT.mkdir(parents=True,exist_ok=True);base.OUT=OUT
 server=None;base.URL=os.environ.get('JUJUTSU_URL')
 if not base.URL:
  server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)));Thread(target=server.serve_forever,daemon=True).start();base.URL=f'http://127.0.0.1:{server.server_port}/.omx/digimon.html?lang=zh-TW'
 report={}
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
   for mobile in [False,True]:
    label='mobile' if mobile else 'desktop';context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));frame=base.boot(page,30015,label)
    report[label]=frame.evaluate(CHECK);report[label]['presentation']=presentation(page,frame,label);assert not errors,errors;context.close()
   browser.close()
  (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'ok':True,'views':list(report),'evidence':str(OUT)}))
 finally:
  if server:server.shutdown();server.server_close()

if __name__=='__main__':main()
