"""Ryu giant main beam + timed, physical follow-up barrage contracts."""
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('RYU_BARRAGE_OUT',ROOT/'.omx/state/ryu-barrage/mechanics'))

CHECK=r"""() => {
 const A=JAcceptance,p=A.p(),R=G.JjkRyu,assert=A.assert,out={};
 function setup(rank=1,q=0){A.reset();const m=A.fixture('jjk-ryu-maximum',rank);p.quantityPicks=p.quantityBonus=q;return m;}
 function cast(m,owner=p){A.resume();try{assert(R.cast(owner,m),'maximum did not cast')}finally{A.pause()};return R.pose(owner);}
 function pulses(f){return G.CombatPulse.telemetry.filter(e=>e.castId===f.castId&&e.runEpoch===f.runEpoch);}
 for(const [rank,q,count,radius,range] of [[1,0,4,72,760],[1,1,5,72,760],[5,0,8,128,1040],[5,20,16,128,1040]]){
  const m=setup(rank,q),e=A.spawn(100,0),hits=A.watch(e),config=R.barrageFor(p,m),events=[],native=p.cast;
  p.cast=function(move,...args){events.push(move.id);return native.call(this,move,...args)};
  let f;try{f=cast(m);A.advance(2.3)}finally{p.cast=native}
  assert(config.count===count&&config.radius===radius&&config.range===range,'rank/quantity geometry differs');
  assert(hits.length===count+1&&pulses(f).length===count+1,'barrage pulse missing or repeated '+rank+'/'+q+':'+hits.length);
  assert(new Set(pulses(f).map(e=>e.contactPulseIndex)).size===count+1,'pulse identities reused');
  assert(events.length===1&&R.stats(p).casts['jjk-ryu-maximum']===1&&!R.pose(p),'barrage emitted extra cast events or failed to finish');
  assert(hits.every(h=>h.owner&&h.id===m.id),'barrage lost damage attribution');
  out['rank'+rank+'q'+q]={config,hits:hits.map(h=>h.raw),pulses:pulses(f).map(e=>e.contactPulseIndex),casts:events.length};
 }
 let m=setup(),e=A.spawn(100,0),hits=A.watch(e),f=cast(m);A.advance(.74);
 assert(hits.length===0&&G.RunInsights.skillState(p,m).label==='巨砲蓄力','charge timing/HUD differs');A.advance(.02);assert(hits.length===1,'main shot not at .75s');
 assert(G.RunInsights.skillState(p,m).label==='連轟 1/5','main HUD omitted barrage count');
 assert(Math.abs(hits[0].raw/(m.dmg*p.atk)-1.5)<1e-8,'main shot multiplier differs');
 A.advance(.10);assert(hits.length===1,'followup fired before .12s');A.advance(.02);
 assert(hits.length===2&&Math.abs(hits[1].raw/(m.dmg*p.atk)-.55)<1e-8,'first followup time or damage differs');
 const main=R.stateFor(p).effects.find(e=>e.kind==='beam'&&e.volleyIndex===0),side=R.stateFor(p).effects.find(e=>e.kind==='beam'&&e.volleyIndex===1);
 assert(main.radius===72&&main.life===.55&&side.radius===72*.7&&side.life<=.24,'effect geometry/lifetime differs');
 out.timing={mainDamage:hits[0].raw,followDamage:hits[1].raw,mainLife:main.life,followLife:side.life};
 A.advance(1.08);assert(G.RunInsights.skillState(p,m).label==='連轟 5/5','last pulse HUD count differs');
 m=setup(1,1);A.spawn(100,0);cast(m);A.advance(.76);assert(G.RunInsights.skillState(p,m).label==='連轟 1/6','quantity did not update HUD total');out.hud=true;
 m=setup();const inside=[A.spawn(180,0),A.spawn(350,40),A.spawn(520,-45)],outside=A.spawn(300,250);f=cast(m);A.advance(.76);
 assert(inside.every(e=>e.hp<e.maxHp)&&outside.hp===outside.maxHp,'giant main beam 3in/1out boundary differs');
 out.boundary={inside:inside.map(e=>e.maxHp-e.hp),outside:outside.maxHp-outside.hp};
 m=setup();e=A.spawn(300,0);f=cast(m);G.World.isWall=(x,y)=>x>=150&&x<=165;A.advance(2.3);
 assert(e.hp===e.maxHp,'barrage crossed wall');out.wall=true;
 for(const hp of [1,100000]){
  m=setup();A.spawn(90,0);e=A.spawn(300,0);f=cast(m);
  const prop={x:150,y:0,r:15,hp,destructible:true},damage=G.World.damageProp,calls=[];
  G.World.propsInCircle=()=>prop.hp>0?[prop]:[];
  G.World.projectileBlock=(x,y,r)=>prop.hp>0&&Math.hypot(x-prop.x,y-prop.y)<=prop.r+r?prop:false;
  G.World.damageProp=(target,amount)=>{assert(target===prop,'wrong blocker');calls.push(amount);prop.hp-=amount};
  try{A.advance(2.3)}finally{G.World.damageProp=damage}
  assert(hp===1?prop.hp<=0&&e.hp<e.maxHp&&calls.length===1:e.hp===e.maxHp&&calls.length===5,'destructible blocker piercing/dedup differs '+hp);
  out['prop'+hp]={calls:calls.length,behindDamage:e.maxHp-e.hp};
 }
 m=setup();e=A.spawn(100,0);hits=A.watch(e);f=cast(m);const onDealt=p.onDealt;
 p.onDealt=function(...args){G.Combat.clearFields(p);return onDealt.apply(this,args)};
 try{A.resume();try{R.update(3)}finally{A.pause()}}finally{p.onDealt=onDealt}
 assert(hits.length===1&&!R.stateFor(p),'clear during main hit allowed catch-up followups');out.clearDuringMain={hits:hits.length};
 // Cancellation inside the first victim also stops other victims in that pulse.
 for(const mode of ['clear','unlearn']){
  m=setup();const first=A.spawn(100,0),second=A.spawn(180,0),firstHits=A.watch(first),secondHits=A.watch(second);f=cast(m);
  const previous=p.onDealt;
  p.onDealt=function(...args){if(mode==='clear')G.Combat.clearFields(p);else p.moves=[];return previous.apply(this,args)};
  try{A.resume();try{R.update(3)}finally{A.pause()}}finally{p.onDealt=previous}
  assert(firstHits.length===1&&secondHits.length===0,'same-wave '+mode+' damaged the next victim');
  A.advance(3);assert(firstHits.length===1&&secondHits.length===0,'same-wave '+mode+' retained future damage');
  out['sameWave'+mode]={first:firstHits.length,second:secondHits.length};
 }
 m=setup();A.spawn(90,0);e=A.spawn(300,0);f=cast(m);const damageProp=G.World.damageProp;
 const prop={x:150,y:0,r:15,hp:1,destructible:true};let propCalls=0;
 G.World.projectileBlock=(x,y,r)=>prop.hp>0&&Math.hypot(x-prop.x,y-prop.y)<=prop.r+r?prop:false;
 G.World.damageProp=(target,amount)=>{propCalls++;target.hp-=amount;G.Combat.clearFields(p)};
 try{A.resume();try{R.update(3)}finally{A.pause()}}finally{G.World.damageProp=damageProp}
 assert(propCalls===1&&e.hp===e.maxHp&&!R.stateFor(p),'prop callback clear allowed later beam damage');out.clearDuringProp=true;
 m=setup();e=A.spawn(300,0);f=cast(m);A.advance(.76);p.y=200;const target=A.spawn(250,200),old=e.hp;A.advance(.12);
 const beam=R.stateFor(p).effects.filter(e=>e.kind==='beam').at(-1);
 assert(beam.volleyIndex===1&&beam.y===200&&target.hp<target.maxHp&&e.hp===old,'followup source did not follow actual owner');
 out.moving={pulse:beam.volleyIndex,source:[beam.x,beam.y],newDamage:target.maxHp-target.hp};
 const paused=JSON.stringify({age:f.age,index:f.volleyIndex,damage:R.stats(p).damage});R.update(5);
 assert(JSON.stringify({age:f.age,index:f.volleyIndex,damage:R.stats(p).damage})===paused,'pause advanced barrage');out.pause=true;
 for(const cancel of ['death','clear','unlearn','world','epoch']){
  m=setup();e=A.spawn(100,0);f=cast(m);A.advance(.76);const hp=e.hp,world=G.World;
  if(cancel==='death'){p.dead=true;p.hp=0}if(cancel==='clear')G.Combat.clearFields(p);
  if(cancel==='unlearn')p.moves=[];if(cancel==='world')G.World=Object.create(world);if(cancel==='epoch')G.CombatPulse.beginRun();
  try{A.advance(2)}finally{G.World=world}
  assert(e.hp===hp&&!R.pose(p),'cancel retained delayed damage '+cancel);out[cancel]=true;
 }
 m=setup(5,20);e=A.spawn(100,0);hits=A.watch(e);f=cast(m);A.resume();try{R.update(3);R.update(3)}finally{A.pause()}
 assert(hits.length===17&&pulses(f).length===17&&!R.pose(p),'large dt dropped or repeated shots');out.largeDt={hits:hits.length};
 m=setup();e=A.spawn(100,0);f=cast(m);const sound=G.Audio.sfx,releaseSounds=[];
 G.Audio.sfx=function(name,data){if(name==='shot'&&data?.kind==='cannon')releaseSounds.push({age:f.age,type:data.type,main:data.main})};
 try{A.advance(2.3)}finally{G.Audio.sfx=sound}
 assert(releaseSounds.length===5&&Math.abs(releaseSounds[0].age-.75)<.011&&Math.abs(releaseSounds[1].age-.87)<.011,'release audio events not aligned');
 assert(releaseSounds[0].main&&releaseSounds.slice(1).every(s=>!s.main),'main and followup cannon audio are indistinguishable');
 out.releaseAudio=releaseSounds;
 m=setup();e=A.spawn(100,0);const clone=G.SelfClones.summon(p);assert(clone,'native clone missing');
 const cloneMove=clone.moves.find(move=>move.id===m.id);assert(cloneMove,'clone missing learned maximum');cloneMove.t=0;
 const ownerCast=cast(m),cloneCast=cast(cloneMove,clone);assert(ownerCast.castId!==cloneCast.castId,'owners shared cast');
 R.clear(p);A.advance(2.3);assert(!R.stateFor(p)&&R.stats(clone)?.hits>0,'module owner clear cancelled independent clone');
 out.clone={sourceCleared:true,cloneHits:R.stats(clone).hits};
 m=setup();p.statsTaken={};const growthCounts=[R.barrageFor(p,m).count],previews=[];
 for(let pick=0;pick<3;pick++){
  const card=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');assert(card,'legal quantity card missing');
  previews.push(card.desc);assert(card.apply(p)!==false,'quantity card rejected');growthCounts.push(R.barrageFor(p,m).count);
 }
 assert(growthCounts.join(',')==='4,5,6,7','real quantity picks did not grow barrage '+growthCounts);
 for(let pick=0;pick<4;pick++){
  const card=G.LevelUp.offer(p,1000).find(c=>c.key==='up:'+m.id);assert(card&&card.apply(p)!==false,'legal maximum upgrade missing');
 }
 assert(m.lvl===5&&m.radius===128&&m.range===1040&&R.barrageFor(p,m).count===15,'live upgrades diverged from cannon geometry');
 const capCard=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');assert(capCard&&capCard.apply(p)!==false,'missing final useful quantity card');
 assert(R.barrageFor(p,m).count===16&&!G.LevelUp.offer(p,1000).some(c=>c.key==='stat:quantity'),'max-only capped build offered useless quantity');
 out.legalGrowth={growthCounts,previews,final:{rank:m.lvl,quantity:p.quantityPicks,radius:m.radius,range:m.range,count:R.barrageFor(p,m).count}};
 // Every learned support cannon feeds the same earned burst, once per cast.
 out.supportCharge={};
 for(const id of ['jjk-ryu','jjk-ryu-spread','jjk-ryu-impact']){
  A.reset();const support=A.fixture(id);assert(p.addMove('jjk-ryu-maximum'),'maximum learn failed');
  const victims=[A.spawn(70,0),A.spawn(85,35),A.spawn(85,-35)];
  const action=cast(support);A.advance(1);const s=R.stateFor(p);
  assert(s.coreCharge===1,'support cast did not earn exactly one charge '+id+':'+s.coreCharge);
  if(id!=='jjk-ryu')assert(s.hits>=2,'support fixture did not exercise multi-target charge dedup '+id);
  assert(R.statusFor(p,p.moves.find(m=>m.id==='jjk-ryu-maximum')).coreCharge===1,'HUD charge source differs '+id);
  out.supportCharge[id]={charge:s.coreCharge,hits:s.hits};
  for(const cancel of ['clear','unlearn']){
   A.reset();const move=A.fixture(id);p.addMove('jjk-ryu-maximum');A.spawn(70,0);A.spawn(85,0);
   cast(move);const before=R.stateFor(p),previous=p.onDealt;
   p.onDealt=function(...args){if(cancel==='clear')G.Combat.clearFields(p);else p.moves=p.moves.filter(m=>m.id!==id);return previous.apply(this,args)};
   try{A.advance(1)}finally{p.onDealt=previous}
   assert(before.coreCharge===0,'cancelled contact granted charge '+id+'/'+cancel);
  }
  for(const miss of ['empty','wall','prop']){
   A.reset();const move=A.fixture(id);p.addMove('jjk-ryu-maximum');const enemy=A.spawn(70,0);cast(move);
   if(miss==='empty'){G.EnemyMgr.clear();G.EnemyMgr.rebuildGrid()}
   if(miss==='wall'){G.World.isWall=(x,y)=>x>=30&&x<=45;G.World.projectileBlock=(x,y)=>G.World.isWall(x,y)?'wall':false;}
   if(miss==='prop'){
    G.EnemyMgr.clear();G.EnemyMgr.rebuildGrid();const prop={x:70,y:0,r:15,hp:100000,destructible:true};
    G.World.propsInCircle=()=>[prop];
    G.World.projectileBlock=(x,y,r)=>Math.hypot(x-prop.x,y-prop.y)<=prop.r+r?prop:false;
   }
   A.advance(1);assert(R.stateFor(p).coreCharge===0,'miss/prop granted charge '+id+'/'+miss);
  }
 }
 m=setup();A.spawn(100,0);cast(m);A.advance(2.3);assert(R.stateFor(p).coreCharge===0,'maximum fueled itself');
 A.reset();const core=A.fixture('jjk-ryu');p.addMove('jjk-ryu-spread');p.addMove('jjk-ryu-impact');p.addMove('jjk-ryu-maximum');
 for(const move of p.moves)move.t=0;
 for(const [x,y]of [[70,0],[100,35],[100,-35]])A.spawn(x,y);
 A.advance(3.5,true);const earned=R.stats(p);
 assert(earned.casts['jjk-ryu']===1&&earned.casts['jjk-ryu-spread']===1&&earned.casts['jjk-ryu-impact']===1&&earned.casts['jjk-ryu-maximum']===1,
  'native support rotation did not cash earned burst '+JSON.stringify(earned));
 assert(G.CombatPulse.telemetry.some(hit=>hit.moveId==='jjk-ryu-maximum'&&hit.primaryHits>0),'earned maximum did not land through native scheduling');
 out.supportRotation=earned;
 // Branches use their actual curved flight path, and a first quantity pick
 // covers a fifth distinct approach instead of repainting the same hit.
 out.closeSpread=[];
 for(const distance of [60,100,140]){
  A.reset();const spread=A.fixture('jjk-ryu-spread'),enemy=A.spawn(distance,0),events=A.watch(enemy);
  cast(spread);A.advance(1);
  assert(events.length===1&&enemy.hp<enemy.maxHp,'single close target was allocated to an unreachable outer branch '+distance);
  out.closeSpread.push({distance,hits:events.length});
 }
 A.reset();const plain=A.fixture('jjk-ryu');
 const plainGroup=[A.spawn(130,0),...[-1.2,-.6,.6,1.2].map(a=>A.spawn(Math.cos(a)*180,Math.sin(a)*180))];
 cast(plain);A.advance(.8);out.withoutSpread=plainGroup.filter(enemy=>enemy.hp<enemy.maxHp).length;
 assert(out.withoutSpread===1,'ordinary cannon counterfactual covered the side approaches');
 out.curvedSpread=[];
 for(const q of [0,1]){
  A.reset();const spread=A.fixture('jjk-ryu-spread');p.quantityPicks=p.quantityBonus=q;
  const group=[A.spawn(130,0),...[-1.2,-.6,.6,1.2].map(a=>A.spawn(Math.cos(a)*180,Math.sin(a)*180))],outside=A.spawn(-220,0);
  const branches=cast(spread);A.advance(.36);const shots=[...R.stateFor(p).scatter];
  assert(shots.length===4+q,'first quantity pick did not add a real branch');
  assert(new Set(shots.map(shot=>shot.target)).size===4+q,'branches duplicated assigned enemy instead of covering another approach');
  const initial=shots.map(shot=>shot.aim);A.advance(.12);
  assert(shots.some((shot,i)=>Math.abs(shot.aim-initial[i])>.05&&shot.trail?.length>2),'scatter only changed decoration, no curved movement');
  A.advance(.5);const damaged=group.filter(enemy=>enemy.hp<enemy.maxHp).length;
  assert(damaged===4+q&&outside.hp===outside.maxHp,'curved spread did not create distinct within-range coverage '+q+':'+damaged);
  out.curvedSpread.push({q,branches:shots.length,damaged,curved:true});
 }
 for(const invalid of ['wall','removed','cancel']){
  A.reset();const spread=A.fixture('jjk-ryu-spread');p.addMove('jjk-ryu-maximum');
  const victims=[A.spawn(140,0),A.spawn(150,70),A.spawn(150,-70)],events=victims.map(A.watch);
  cast(spread);A.advance(.36);const original=p.onDealt;
  if(invalid==='wall'){G.World.isWall=(x,y)=>x>=40&&x<=60;G.World.projectileBlock=(x,y)=>G.World.isWall(x,y)?'wall':false;}
  if(invalid==='removed')for(const enemy of victims)G.EnemyMgr.removeRemote(enemy.id,false);
  if(invalid==='cancel')p.onDealt=function(...args){G.Combat.clearFields(p);return original.apply(this,args)};
  try{A.advance(.6)}finally{p.onDealt=original}
  const contacts=events.reduce((n,list)=>n+list.length,0);
  assert(contacts===(invalid==='cancel'?1:0),'curved scatter violated wall/removal/callback cleanup '+invalid+':'+contacts);
  if(invalid==='cancel')assert(!R.stateFor(p),'cancelled curved cast retained state');
  out['curved-'+invalid]={contacts};
 }
 A.reset();const capped=A.fixture('jjk-ryu-spread',5);p.quantityPicks=p.quantityBonus=20;A.spawn(150,0);cast(capped);A.advance(.36);
 assert(R.stateFor(p).scatter.length===9,'curved spread exceeded branch cap');out.curvedCap=9;
 return out;
}"""

class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def presentation(page,frame,label):
 results={}
 for rank,q in [(1,0),(5,4)]:
  key=f'{label}-rank{rank}-q{q}'
  frame.evaluate("""({rank,q})=>{const A=JAcceptance;A.reset();A.fixture('jjk-ryu-maximum',rank);const p=A.p();p.quantityPicks=p.quantityBonus=q;
   p.invuln=999;for(const [x,y]of [[180,0],[350,40],[520,-45],[640,90]])A.spawn(x,y);
   A.resume();try{G.JjkRyu.cast(p,p.moves[0])}finally{A.pause()};}""",{'rank':rank,'q':q})
  stages=[];previous=0
  for at,name in [(.50,'charge'),(.76,'main'),(.90,'follow'),(1.25,'barrage'),(1.96,'last'),(2.19,'recovery')]:
   frame.evaluate('dt=>JAcceptance.advance(dt)',at-previous);previous=at
   page.wait_for_timeout(45)
   page.screenshot(path=str(OUT/f'{key}-{name}.png'))
   stages.append(frame.evaluate("""()=>{const s=G.JjkRyu.stateFor(JAcceptance.p()),f=s.action;return {age:f?.age,phase:f?.phase,pulseAge:f?.pulseAge,
    volleyIndex:f?.volleyIndex,volleyCount:f?.volleyCount,hud:G.RunInsights.skillState(JAcceptance.p(),JAcceptance.p().moves[0]).label,
    effects:s.effects.filter(e=>e.kind==='beam').map(e=>({index:e.volleyIndex,radius:e.radius,life:e.life,age:e.age}))};}"""))
  results[key]=stages
 # A real 2.65-second canvas recording uses native RAF, not screenshots stitched
 # into a movie or manually advanced skill time.
 clip=frame.evaluate("""async()=>{
  const A=JAcceptance;A.reset();A.fixture('jjk-ryu-maximum',5);const p=A.p();p.quantityPicks=p.quantityBonus=4;p.invuln=999;
  for(const [x,y]of [[180,0],[350,40],[520,-45],[640,90]])A.spawn(x,y);G.Game.debugSpeed(1);
  const stream=document.getElementById('game').captureStream(24),audio=G.Audio.debugStream(true);
  if(audio)for(const track of audio.getAudioTracks())stream.addTrack(track);
  const mime=MediaRecorder.isTypeSupported('video/webm;codecs=vp9,opus')?'video/webm;codecs=vp9,opus':'video/webm';
  const recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:2200000}),chunks=[];
  recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
  const done=new Promise(resolve=>recorder.onstop=()=>{const reader=new FileReader;reader.onload=()=>resolve(reader.result);reader.readAsDataURL(new Blob(chunks,{type:mime}))});
  recorder.start();A.resume();G.JjkRyu.cast(p,p.moves[0]);await new Promise(resolve=>setTimeout(resolve,2650));A.pause();recorder.stop();
  const data=await done;for(const track of stream.getTracks())track.stop();return data;
 }""")
 (OUT/f'{label}-rank5-native-barrage.webm').write_bytes(base64.b64decode(clip.split(';base64,',1)[1]))
 # Normal RAF scatter flights expose real branching and steering at starter
 # rank and after the first quantity investment, with the same enemy layout.
 for quantity in [0,1]:
  frame.evaluate("""q=>{
   const A=JAcceptance;A.reset();const m=A.fixture('jjk-ryu-spread'),p=A.p();p.quantityPicks=p.quantityBonus=q;p.invuln=999;
   A.spawn(130,0);for(const a of [-1.2,-.6,.6,1.2])A.spawn(Math.cos(a)*180,Math.sin(a)*180);
   G.Game.debugSpeed(1);const stream=document.getElementById('game').captureStream(30),chunks=[];
   const recorder=new MediaRecorder(stream,{mimeType:'video/webm',videoBitsPerSecond:2200000});
   recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
   const done=new Promise(resolve=>recorder.onstop=()=>{const reader=new FileReader;reader.onload=()=>resolve(reader.result);reader.readAsDataURL(new Blob(chunks,{type:'video/webm'}))});
   window.RyuCurveClip={stream,recorder,done};recorder.start();A.resume();G.JjkRyu.cast(p,m);
  }""",quantity)
  page.wait_for_timeout(490)
  page.screenshot(path=str(OUT/f'{label}-curve-q{quantity}-native-flight.png'))
  results[f'{label}-curve-q{quantity}']=frame.evaluate("""()=>{const s=G.JjkRyu.stateFor(JAcceptance.p());return {fixture:'native RAF; same five approaches; rank 1',quantity:JAcceptance.p().quantityPicks,
    branches:s.scatter.map(e=>({x:e.x,y:e.y,aim:e.aim,trail:e.trail.length})),hits:s.hits};}""")
  page.wait_for_timeout(600)
  curve_clip=frame.evaluate("""async()=>{JAcceptance.pause();const clip=window.RyuCurveClip;clip.recorder.stop();const data=await clip.done;for(const track of clip.stream.getTracks())track.stop();return data;}""")
  (OUT/f'{label}-rank1-q{quantity}-native-curve.webm').write_bytes(base64.b64decode(curve_clip.split(';base64,',1)[1]))
 return results

def main():
 OUT.mkdir(parents=True,exist_ok=True);base.OUT=OUT
 server=None;base.URL=os.environ.get('JUJUTSU_URL')
 if not base.URL:
  server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)))
  Thread(target=server.serve_forever,daemon=True).start();base.URL=f'http://127.0.0.1:{server.server_port}/.omx/digimon.html?lang=zh-TW'
 report={}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
  for mobile in [False,True]:
   label='mobile' if mobile else 'desktop';context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
   page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   frame=base.boot(page,30014,label);report[label]=frame.evaluate(CHECK)
   report[label]['presentation']=presentation(page,frame,label);assert not errors,errors
   context.close()
  browser.close()
 (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
 print(json.dumps({'ok':True,'views':list(report),'evidence':str(OUT)}))
 if server:server.shutdown();server.server_close()

if __name__=='__main__':main()
