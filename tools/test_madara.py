"""Independent Madara acceptance through the production menu and combat loop.

Uses native enemies, collision, legal growth cards and damage callbacks. Controlled
fixtures are reported separately from native RAF/input presentation evidence.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('MADARA_OUT', ROOT / 'art-review/madara/verification'))
URL = os.environ.get('MADARA_URL', 'http://127.0.0.1:8347/.omx/digimon.html?lang=zh-TW')
DEX = 30016


def runtime(page):
    for _ in range(300):
        for frame in page.frames:
            try:
                if frame.evaluate("typeof G==='object'&&!!G.Game&&!!G.NarutoMadara"):
                    return frame
            except Exception:
                pass
        page.wait_for_timeout(100)
    raise AssertionError('Madara production runtime did not load')


def boot(page, label):
    page.goto(URL + ('&layout=wide' if label == 'desktop' else ''))
    frame = runtime(page)
    frame.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
    if frame.locator('#tap-start').is_visible():
        frame.locator('#tap-start').click()
    frame.locator(f'[data-quick-naruto="{DEX}"]').click()
    assert frame.evaluate(f'G.DB.save.partner==={DEX}'), 'normal picker failed'
    frame.wait_for_function(f'G.NarutoAssets.ready({DEX})')
    page.wait_for_timeout(100)
    page.screenshot(path=str(OUT / f'{label}-selection.png'))
    frame.locator('#scr-menu [data-go="play"]').click()
    frame.wait_for_function(f'G.Game.player?.dex==={DEX}&&G.Game.state==="playing"')
    page.screenshot(path=str(OUT / f'{label}-normal-entry.png'))
    frame.evaluate(base.SETUP)
    return frame


PROGRESSION = r"""() => {
 const A=JAcceptance,p=A.p(),assert=A.assert;
 const ids=Object.keys(G.Moves.BY_ID).filter(id=>id==='naruto-madara'||id.startsWith('naruto-madara-'));
 assert(ids.length>=3,'Madara skill registration missing');
 assert(p.moves.length===1&&p.moves[0].id==='naruto-madara','normal starter differs');
 const out={starter:p.moves[0].id,ids,levels:[]};
 for(const level of [1,2,3,5,6,8,9,11,12,15]){
  p.level=level;const pool=G.Moves.poolFor(p.mon),cards=G.LevelUp.offer(p,1000);
  for(const id of ids){const required=G.Moves.BY_ID[id].learnLevel||1;
   assert(pool.includes(id)===(level>=required),'skill pool gate '+id+' at '+level);
   if(id!=='naruto-madara')assert(cards.some(c=>c.key==='new:'+id)===(level>=required),'learn card gate '+id+' at '+level);
  }
  assert(!pool.some(id=>(id.startsWith('naruto-')||id.startsWith('jjk-'))&&!ids.includes(id)),'foreign crossover skill in Madara pool');
  out.levels.push({level,pool:pool.filter(id=>ids.includes(id))});
 }
 p.level=30;
 for(const id of ids.filter(id=>!p.hasMove(id))){const card=G.LevelUp.offer(p,1000).find(c=>c.key==='new:'+id);
  assert(card&&card.apply(p)!==false,'legal learn failed '+id);}
 assert(ids.every(id=>p.hasMove(id)),'legal learn omitted skills');
 const mon=p.mon;
 for(const dex of [30001,30002,30006,30007,30009,30010,30011,30012,30013,30014,30015]){
  p.mon=G.DEX_BY[dex];assert(!G.Moves.poolFor(p.mon).some(id=>ids.includes(id)),'Madara leaked to '+dex);
 }p.mon=mon;
 out.learned=p.moves.map(m=>({id:m.id,rank:m.lvl,passive:!!m.passive}));return out;
}"""

STARTER_GATES = r"""() => {
 const A=JAcceptance,assert=A.assert,native=G.Upgrades.perks,pick=G.U.pick,out=[];
 G.Upgrades.perks=function(...args){return {...native.apply(this,args),startMoves:2}};
 G.U.pick=values=>values.at(-1);
 try{for(let run=0;run<4;run++){
  A.p().level=30;const previous=A.p();G.Game.startRun();A.pause();const p=A.p();
  assert(p!==previous&&p.level===1,'native restart did not create level-one actor');
  assert(p.moves.every(m=>(G.Moves.BY_ID[m.id].learnLevel||1)<=1),'second starting move bypassed learn gate '+p.moves.map(m=>m.id));
  assert(p.moves.length===1&&p.moves[0].id==='naruto-madara','unexpected starter with repertoire perk');
  assert(!G.NarutoMadara.stateFor(previous),'previous-run state survived native restart');
  out.push({run,level:p.level,skills:p.moves.map(m=>m.id)});
 }}finally{G.Upgrades.perks=native;G.U.pick=pick}return out;
}"""


def save_data(name, value):
    (OUT / name).write_bytes(base64.b64decode(value.split(';base64,', 1)[1]))


def source_hashes():
    paths = [ROOT / '.omx/naruto.js', ROOT / '.omx/naruto-skills.js',
             ROOT / '.omx/naruto-training.js', ROOT / '.omx/digimon.html',
             ROOT / '.omx/combat-pulse.js', ROOT / 'art-review/madara/runtime.js',
             ROOT / 'art-review/madara/madara-actions-v1.png']
    paths += list((ROOT / '.omx').glob('*madara*'))
    paths += list((ROOT / 'art-review/madara').glob('*.json'))
    return {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths if p.is_file()}


POSE = r"""() => {
 const p=G.Game.player,c=document.createElement('canvas');c.width=220;c.height=180;
 const ctx=c.getContext('2d',{willReadFrequently:true}),draw=ctx.drawImage.bind(ctx),sources=[];
 ctx.drawImage=(image,...args)=>{sources.push({source:image.src||image.dataset?.source||'canvas',rect:args});return draw(image,...args)};
 p.anim.draw(ctx,110,145);const rgba=ctx.getImageData(0,0,c.width,c.height).data;
 let pixels=0;for(let i=3;i<rgba.length;i+=4)if(rgba[i]>30)pixels++;
 JAcceptance.assert(pixels>80,'production body is empty');
 return {pixels,sources,dir:p.anim.dir,animation:p.anim.cur,png:c.toDataURL()};
}"""


def input_and_body(page, frame, context, mobile, label):
    frame.evaluate('JAcceptance.reset()')
    if frame != page.main_frame:
        page.locator('iframe').first.focus()
    result = {}
    for direction, key in [('right', 'KeyD'), ('left', 'KeyA'), ('down', 'KeyS'), ('up', 'KeyW')]:
        page.keyboard.down(key)
        result[direction] = frame.evaluate(r"""()=>{
         const A=JAcceptance,p=A.p(),before=[p.x,p.y];A.resume();try{p.update(.08)}finally{A.pause()}
         A.assert(p.walking&&Math.hypot(p.x-before[0],p.y-before[1])>0,'keyboard did not move');
         return {dx:p.x-before[0],dy:p.y-before[1],dir:p.anim.dir};
        }""")
        page.keyboard.up(key)
        pose = frame.evaluate(POSE)
        save_data(f'{label}-body-{direction}.png', pose.pop('png'))
        result[direction]['pose'] = pose
    if mobile:
        frame.evaluate('JAcceptance.reset();JAcceptance.resume()')
        client = context.new_cdp_session(page)
        point = frame.evaluate('G.Touch.stickBase()')
        if frame != page.main_frame:
            box = page.locator('iframe').first.bounding_box()
            point = {'x': point['x'] + box['x'], 'y': point['y'] + box['y']}
        client.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [point]})
        client.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': point['x'] + 42, 'y': point['y']}]})
        result['touch'] = frame.evaluate(r"""()=>{
         const A=JAcceptance,p=A.p(),x=p.x;A.assert(G.Touch.vector()[0]>0,'touch vector missing');
         p.update(.08);A.pause();A.assert(p.x>x,'touch did not move');return p.x-x;
        }""")
        client.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
        client.detach()
    assert not frame.evaluate('document.documentElement.scrollWidth>innerWidth'), 'horizontal overflow'
    result['viewport'] = frame.evaluate('({width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth})')
    return result


NATIVE_START = r"""() => {
 const A=JAcceptance,p=A.p();A.reset();p.level=12;p.statsTaken={};
 const ids=Object.keys(G.Moves.BY_ID).filter(id=>id==='naruto-madara'||id.startsWith('naruto-madara-'));
 p.moves=[];p.slots=[];p.bind={};A.assert(p.addMove('naruto-madara'),'restore natural starter');
 for(const id of ids.filter(id=>!p.hasMove(id))){const card=G.LevelUp.offer(p,1000).find(c=>c.key==='new:'+id);
  A.assert(card&&card.apply(p)!==false,'native learning failed '+id);}
 A.assert(p.moves.length===ids.length&&p.moves.every(m=>m.lvl===1),'native fixture granted ranks or omitted skill');
 for(const m of p.moves)m.t=0;
 p.invuln=999;p.xpNext=1e12;G.Spawner.update=()=>{};G.World.walkable=()=>true;G.Path.clear();
 const enemies=[];for(const [x,y]of [[70,0],[110,35],[145,-40],[220,0],[240,55],[250,-55],[150,160],[-90,60]]){
  const e=A.spawn(x,y);e.spd=8;e.dmg=0;enemies.push(e);
 }
 const events=[],native=p.cast;
 p.cast=function(m,...args){events.push({time:G.Game.st.time,id:m.id,x:this.x,y:this.y});return native.call(this,m,...args)};
 G.Game.debugSpeed(1);const start=G.Game.st.time;
 window.MadaraNative={start,events,positions:[],fixture:{level:p.level,skills:p.moves.map(m=>({id:m.id,rank:m.lvl})),quantity:p.quantityPicks}};
 const canvas=document.getElementById('game'),stream=canvas.captureStream(24),chunks=[];
 const recorder=new MediaRecorder(stream,{mimeType:'video/webm',videoBitsPerSecond:2200000});
 recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
 const done=new Promise(resolve=>recorder.onstop=()=>{const reader=new FileReader;reader.onload=()=>resolve(reader.result);reader.readAsDataURL(new Blob(chunks,{type:'video/webm'}))});
 Object.assign(MadaraNative,{stream,recorder,done});recorder.start();
 function sample(){const run=window.MadaraNative;if(!run)return;
  if(G.Game.state==='playing'&&(!run.positions.length||G.Game.st.time-start-run.positions.at(-1).t>.3))
   run.positions.push({t:G.Game.st.time-start,x:p.x,y:p.y});requestAnimationFrame(sample);
 }requestAnimationFrame(sample);A.resume();return MadaraNative.fixture;
}"""


def native_play(page, frame, context, mobile, label):
    fixture = frame.evaluate(NATIVE_START)
    for index, at in enumerate([1, 4, 8, 12, 18]):
        frame.wait_for_function('t=>G.Game.st.time-MadaraNative.start>=t', arg=at, timeout=40000)
        if mobile:
            client = context.new_cdp_session(page)
            point = frame.evaluate('G.Touch.stickBase()')
            if frame != page.main_frame:
                box = page.locator('iframe').first.bounding_box()
                point = {'x': point['x'] + box['x'], 'y': point['y'] + box['y']}
            client.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [point]})
            client.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': point['x'] + (25 if index % 2 == 0 else -25), 'y': point['y']}]})
            page.wait_for_timeout(140)
            client.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
            client.detach()
        else:
            key = 'KeyD' if index % 2 == 0 else 'KeyA'
            page.keyboard.down(key)
            page.wait_for_timeout(140)
            page.keyboard.up(key)
        page.screenshot(path=str(OUT / f'{label}-native-{at}s.png'))
    result = frame.evaluate(r"""async()=>{
     const A=JAcceptance,p=A.p(),run=MadaraNative;A.pause();run.recorder.stop();
     const video=await run.done;for(const track of run.stream.getTracks())track.stop();
     const counts={};for(const event of run.events)counts[event.id]=(counts[event.id]||0)+1;
     A.assert(p.moves.every(m=>counts[m.id]>0),'learned role never auto cast '+JSON.stringify(counts));
     A.assert(run.positions.some(v=>Math.hypot(v.x,v.y)>3),'native input did not move player');
     return {video,counts,events:run.events,positions:run.positions,damage:p.dmgDealt,stats:G.NarutoMadara.stats(p),
      hud:p.moves.map(m=>({id:m.id,...G.RunInsights.skillState(p,m)}))};
    }""")
    save_data(f'{label}-native-rank1-legal-kit.webm', result.pop('video'))
    return {'fixture': fixture, **result}


MECHANICS = r"""() => {
 const A=JAcceptance,p=A.p(),M=G.NarutoMadara,assert=A.assert,out={failures:[]};
 function check(name,fn){try{out[name]=fn()}catch(e){out.failures.push(name+': '+e.message)}}
 function setup(id='naruto-madara-fire',rank=1,q=0){A.reset();p.statsTaken={};const m=A.fixture(id,rank);p.quantityPicks=p.quantityBonus=q;return m;}
 function cast(m,owner=p){A.resume();try{assert(M.cast(owner,m),'cast failed '+m.id)}finally{A.pause()};return M.stateFor(owner).action;}
 const cases=[
  ['naruto-madara',[[45,0],[65,25],[85,-25]],[-200,0],4],
  ['naruto-madara-fire',[[160,0],[210,100],[300,-120]],[-450,0],4],
  ['naruto-madara-susanoo',[[180,0],[220,130],[260,-120]],[-550,0],4],
  ['naruto-madara-meteor',[[400,0],[460,100],[500,-100]],[400,400],6]
 ];
 for(const [id,inside,outside,count]of cases)check('aoe-'+id,()=>{
  const m=setup(id),victims=inside.map(([x,y])=>A.spawn(x,y)),far=A.spawn(...outside),logs=victims.map(A.watch);
  const f=cast(m);A.advance(6);
  assert(logs.every(events=>events.length===count),'three in-range targets expected '+count+' contacts; got '+logs.map(h=>h.length));
  assert(far.hp===far.maxHp,'out-of-range enemy damaged');
  assert(logs.flat().every(hit=>hit.id===id&&hit.owner&&hit.loss>0),'damage source attribution differs');
  const events=G.CombatPulse.telemetry.filter(e=>e.castId===f.cast.castId&&e.runEpoch===f.cast.runEpoch);
  assert(events.length===count&&new Set(events.map(e=>e.contactPulseIndex)).size===count,'pulse identities missing/repeated');
  assert(!M.stateFor(p).action&&!M.stateFor(p).fields.length,'completed cast retained active damage');
  return {inside,outside,hits:logs.map(h=>h.length),damage:logs.map(h=>h.map(e=>e.loss)),profile:M.profile(p,m),pulses:events.map(e=>e.contactPulseIndex)};
 });
 for(const id of cases.map(c=>c[0]))check('wall-'+id,()=>{
  const m=setup(id),e=A.spawn(100,0);cast(m);
  const old=G.World.projectilePathClear;G.World.projectilePathClear=()=>false;
  try{A.advance(6)}finally{G.World.projectilePathClear=old}
  assert(e.hp===e.maxHp,'attack crossed wall');return true;
 });
 for(const id of cases.map(c=>c[0]))check('no-enemy-prop-'+id,()=>{
  const m=setup(id),prop={x:65,y:0,r:12,type:'chest',solid:true,destructible:true,hp:1,tx:999999,ty:999999};
  G.World.propsInCircle=(x,y,r)=>prop.hp>0&&Math.hypot(prop.x-x,prop.y-y)<=r+prop.r?[prop]:[];
  G.World.projectileBlock=(x,y,r=1)=>prop.hp>0&&Math.hypot(prop.x-x,prop.y-y)<=prop.r+r?prop:false;
  const old=G.World.damageProp,events=[];G.World.damageProp=function(target,amount,...args){events.push({same:target===prop,amount});return old.call(this,target,amount,...args)};
  try{cast(m);A.advance(6)}finally{G.World.damageProp=old}
  assert(prop.hp<=0&&events.length>0&&events.every(e=>e.same&&e.amount>0),'no-enemy destructible prop was not hit');
  return {hp:prop.hp,events};
 });
 check('legal-quantity-growth',()=>{
  const m=setup(),counts=[M.profile(p,m).pulses],previews=[],upgradePreviews=[];
  for(let i=0;i<3;i++){const card=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');
   assert(card&&card.desc.includes((4+i)+'→'+(5+i))&&card.apply(p)!==false,'legal quantity card missing/rejected or preview differs');previews.push(card.desc);counts.push(M.profile(p,m).pulses);}
  assert(counts.join(',')==='4,5,6,7','first three quantity cards did not add real fire waves '+counts);
  const victims=[A.spawn(150,0),A.spawn(200,30),A.spawn(240,-35)],logs=victims.map(A.watch);cast(m);A.advance(4);
  assert(logs.every(h=>h.length===7),'quantity profile is not real damage '+logs.map(h=>h.length));
  for(let i=0;i<4;i++){const c=G.LevelUp.offer(p,1000).find(c=>c.key==='up:'+m.id);
   assert(c&&c.desc.includes([7,9,11,13][i]+'→'+[9,11,13,15][i])&&c.apply(p)!==false,'live quantity-adjusted upgrade preview/learning differs '+c?.desc);upgradePreviews.push(c.desc);}
  assert(m.lvl===5&&m.range>430&&M.profile(p,m).pulses>7,'legal ranks failed to change coverage/contacts');
  const final=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');assert(final&&final.apply(p)!==false,'last useful quantity card absent');
  assert(M.profile(p,m).pulses===16&&!G.LevelUp.offer(p,1000).some(c=>c.key==='stat:quantity'),'capped fire build offered useless quantity');
  return {counts,previews,upgradePreviews,finalProfile:M.profile(p,m)};
 });
 check('wood-clone-every-legal-rank-deals-more',()=>{
  const m=setup('naruto-madara-clones');assert(p.addMove('naruto-madara-susanoo'),'learn common comparison attack');
  const samples=[],previews=[];
  for(let rank=1;rank<=5;rank++){
   A.reset();m.t=0;const e=A.spawn(180,0),hits=A.watch(e);cast(m);A.advance(.80);
   assert(hits.length>0,'rank '+rank+' clone comparison had no real hurt');samples.push({rank,raw:hits[0].raw,loss:hits[0].loss,quantity:p.quantityPicks,cloneCount:M.stateFor(p).clones.length});
   if(rank<5){const card=G.LevelUp.offer(p,1000).find(c=>c.key==='up:'+m.id);
    assert(card&&card.desc.includes([100,120,145,175][rank-1]+'%→'+[120,145,175,210][rank-1]+'%')&&card.apply(p)!==false,'legal clone rank '+(rank+1)+' preview/learning differs '+card?.desc);previews.push(card.desc);}
  }
  for(let i=1;i<samples.length;i++)assert(Math.abs(samples[i].raw/samples[0].raw-[1,1.2,1.45,1.75,2.1][i])<1e-7,'clone rank failed real damage multiplier '+JSON.stringify(samples));
  assert(samples[0].cloneCount===samples[1].cloneCount&&samples[2].cloneCount===samples[3].cloneCount,'equal-count clone rank comparison fixture differs');
  return {fixture:'legal clone rank cards; same rank1 Susanoo, enemy, quantity=0',samples,previews};
 });
 for(const cancel of ['clear','unlearn','death','world','epoch'])check('cancel-'+cancel,()=>{
  const m=setup(),e=A.spawn(150,0),hits=A.watch(e),f=cast(m);A.advance(.36);assert(hits.length===1,'fixture missed first fire wave');
  const world=G.World;
  if(cancel==='clear')G.Combat.clearFields(p);if(cancel==='unlearn')p.moves=[];
  if(cancel==='death'){p.dead=true;p.hp=0}if(cancel==='world')G.World=Object.create(world);if(cancel==='epoch')G.CombatPulse.beginRun();
  try{A.advance(4)}finally{G.World=world}
  assert(hits.length===1&&!M.pose(p),'cancelled cast retained damage '+hits.length);return {hits:hits.length};
 });
 for(const callback of ['hurt','onDealt'])for(const cancel of ['clear','unlearn'])check('same-wave-'+callback+'-'+cancel,()=>{
  const m=setup(),first=A.spawn(100,0),second=A.spawn(180,0),h1=A.watch(first),h2=A.watch(second);cast(m);
  const target=callback==='hurt'?first:p,previous=target[callback];
  target[callback]=function(...args){if(cancel==='clear')G.Combat.clearFields(p);else p.moves=[];return previous.apply(this,args)};
  try{A.advance(4)}finally{target[callback]=previous}
  assert(h1.length===1&&h2.length===0,'same-wave callback failed cancellation '+h1.length+'/'+h2.length);
  A.advance(3);assert(h1.length===1&&h2.length===0,'cancelled callback retained future contacts');return {first:h1.length,second:h2.length};
 });
 check('same-wave-removal-skips-next-live-victim',()=>{
  const m=setup(),first=A.spawn(100,0),second=A.spawn(180,0),h1=A.watch(first),h2=A.watch(second),hurt=first.hurt;cast(m);
  first.hurt=function(...args){G.EnemyMgr.removeRemote(second.id,false);return hurt.apply(this,args)};
  try{A.advance(4)}finally{first.hurt=hurt}
  assert(h1.length===4&&h2.length===0,'same-wave callback damaged removed next actor '+h1.length+'/'+h2.length);
  return {first:h1.length,removedSecond:h2.length};
 });
 for(const mode of ['already-stale','removed-during-primary'])check('splash-outer-'+mode,()=>{
  const m=setup('naruto-madara'),first=A.spawn(90,0),outer=A.spawn(135,0),h1=A.watch(first),h2=A.watch(outer),hurt=first.hurt;
  p.damageSplashPicks=1;
  if(mode==='already-stale')G.EnemyMgr.removeRemote(outer.id,false);
  else first.hurt=function(...args){G.EnemyMgr.removeRemote(outer.id,false);return hurt.apply(this,args)};
  try{cast(m);A.advance(3)}finally{first.hurt=hurt}
  assert(h1.length===4&&h2.length===0,'stale outer splash damaged removed actor '+h1.length+'/'+h2.length);
  return {primary:h1.length,removedOuter:h2.length};
 });
 check('prop-callback-cancels-same-wave',()=>{
  const m=setup(),props=[60,90].map(x=>({x,y:0,r:10,type:'chest',destructible:true,hp:10000}));
  G.World.propsInCircle=(x,y,r)=>props.filter(p=>p.hp>0&&Math.hypot(p.x-x,p.y-y)<=r+p.r);
  G.World.projectileBlock=()=>false;
  const old=G.World.damageProp,calls=[];G.World.damageProp=(target,amount)=>{calls.push(props.indexOf(target));target.hp-=amount;G.Combat.clearFields(p)};
  try{cast(m);A.advance(4)}finally{G.World.damageProp=old}
  assert(calls.join(',')==='0'&&props[1].hp===10000,'prop cancellation damaged later target/pulse '+calls);
  return {calls,hp:props.map(p=>p.hp)};
 });
 check('pause-and-live-origin',()=>{
  const m=setup(),old=A.spawn(150,0),hits=A.watch(old),f=cast(m);M.update(5);
  assert(f.age===0&&hits.length===0,'pause advanced cast');A.advance(.36);assert(hits.length===1,'resume did not release first wave');
  const mark=M.stateFor(p).effects.find(e=>e.kind==='fire'),origin=[mark.x,mark.y];
  p.y=1000;const moved=A.spawn(150,1000);A.advance(.19);
  assert(moved.hp<moved.maxHp&&hits.length===1,'next wave did not use moving owner and new enemy');
  assert(mark.x===origin[0]&&mark.y===origin[1],'previous contact mark moved');
  return {oldHits:hits.length,movedDamage:moved.maxHp-moved.hp,frozenMark:origin};
 });
 check('moving-enemy-and-removed-grid-actor',()=>{
  const m=setup(),e=A.spawn(150,0),hits=A.watch(e);cast(m);A.advance(.36);assert(hits.length===1,'first moving target contact missing');
  const first=M.stateFor(p).effects.find(e=>e.kind==='fire');e.x=-150;G.EnemyMgr.rebuildGrid();A.advance(.19);
  assert(hits.length===2&&Math.abs(Math.abs(M.stateFor(p).effects.at(-1).aim)-Math.PI)<1e-7,'wave did not follow moved reachable enemy');
  assert(first.aim===0,'moving enemy changed previous effect direction');
  const fallback=A.spawn(160,0),hp=e.hp;G.EnemyMgr.removeRemote(e.id,false);
  assert(!e.dead&&G.EnemyMgr.queryCircle(0,0,500).includes(e)&&!G.EnemyMgr.all().includes(e),'stale-grid fixture invalid');
  A.advance(.19);assert(e.hp===hp&&fallback.hp<fallback.maxHp,'next wave hit removed live grid actor instead of live replacement');
  return {movedContacts:2,removedActorDamage:e.maxHp-e.hp,replacementDamage:fallback.maxHp-fallback.hp};
 });
 check('meteor-fixed-center-and-two-impacts',()=>{
  const m=setup('naruto-madara-meteor'),e=A.spawn(400,0),hits=A.watch(e),f=cast(m),center=[f.tx,f.ty];
  A.advance(1);assert(!hits.length,'meteor damaged during descent telegraph');p.x=-800;p.y=500;
  A.advance(.35);assert(hits.length===1,'first meteor impact missing');A.advance(.85);assert(hits.length===2,'second independent impact missing');
  assert(f.tx===center[0]&&f.ty===center[1],'meteor center followed moving owner');
  const escape=A.spawn(400,400);A.advance(3);assert(escape.hp===escape.maxHp,'escaped target damaged outside fixed impact');
  assert(hits.length===6,'two rocks + four shock contacts missing');return {center,damage:hits.map(h=>h.raw)};
 });
 check('large-dt-cap',()=>{
  const m=setup('naruto-madara-fire',5,20),e=A.spawn(120,0),hits=A.watch(e);cast(m);
  A.resume();try{M.update(10);M.update(10)}finally{A.pause()}
  assert(hits.length===16&&!M.pose(p),'large dt dropped/repeated/capped damage '+hits.length);return {hits:hits.length};
 });
 check('meteor-paused-levelup-readonly-render',()=>{
  const m=setup('naruto-madara-meteor'),e=A.spawn(400,0),hits=A.watch(e),f=cast(m);A.advance(1);
  const snap=()=>JSON.stringify({clock:M.stateFor(p).clock,age:f.age,index:f.index,meteorHits:f.meteorHits,hp:e.hp});
  function image(){const c=document.createElement('canvas');c.width=1400;c.height=1200;const ctx=c.getContext('2d',{willReadFrequently:true});
   ctx.translate(400,600);M.draw(ctx,true);M.draw(ctx,false);const a=ctx.getImageData(0,0,c.width,c.height).data;let pixels=0;
   for(let i=3;i<a.length;i+=4)if(a[i]>0)pixels++;return pixels;}
  const before=snap();A.resume();const playing=image();A.pause();const paused=image();M.update(5);
  const descriptor=Object.getOwnPropertyDescriptor(G.Game,'state');let levelup;
  try{Object.defineProperty(G.Game,'state',{configurable:true,value:'levelup'});levelup=image();M.update(5)}
  finally{Object.defineProperty(G.Game,'state',descriptor)}
  assert(playing>500&&paused===playing&&levelup===playing,'meteor vanished or changed on paused/levelup render '+playing+'/'+paused+'/'+levelup);
  assert(before===snap()&&hits.length===0,'draw or paused update mutated meteor/damage');
  A.advance(.35);assert(hits.length===1,'resume skipped first meteor after pause');
  return {playingPixels:playing,pausedPixels:paused,levelupPixels:levelup,drawReadOnly:true,levelupFixture:'render-state override, no battle advance'};
 });
 check('wood-clone-sources-and-unlearn',()=>{
  const m=setup('naruto-madara-clones');assert(p.addMove('naruto-madara-susanoo'),'learn clone attack');
  const e=A.spawn(180,0);cast(m);A.advance(2);
  const s=M.stateFor(p),telemetry=G.CombatPulse.telemetry.filter(e=>e.channel==='wood-clone');
  assert(s.clones.length===2&&new Set(s.clones.map(c=>[c.x,c.y].join(','))).size===2,'two persistent spatial clones missing');
  assert(new Set(telemetry.map(e=>e.castId)).size>=2&&telemetry.every(e=>e.moveId==='naruto-madara-susanoo'),'clones lack independent attack identity');
  const hit=e.maxHp-e.hp;assert(hit>0,'clone sources did no real damage');p.moves=p.moves.filter(m=>m.id!=='naruto-madara-clones');
  A.advance(4);assert(!M.stateFor(p).clones.length&&e.maxHp-e.hp===hit,'unlearned clones retained pending damage');
  return {sources:new Set(telemetry.map(e=>e.castId)).size,damage:hit};
 });
 check('self-clone-owner-isolation',()=>{
  const m=setup(),enemy=A.spawn(150,0),clone=G.SelfClones.summon(p);assert(clone,'native self clone missing');
  clone.x=0;clone.y=0;const cm=clone.moves.find(m=>m.id==='naruto-madara-fire');assert(cm,'clone lost learned fire');cm.t=0;
  const a=cast(m),b=cast(cm,clone);assert(a.cast.castId!==b.cast.castId,'owners shared cast ID');
  M.clear(p);A.advance(3);assert(!M.stateFor(p)&&M.stats(clone)?.hits>0,'module owner clear cancelled another owner');
  return {clearedOwner:true,cloneHits:M.stats(clone).hits};
 });
 return out;
}"""


def presentation(page, frame, label):
    results = {}
    for rank, quantity in [(1, 0), (5, 4)]:
        for kind in ['fire', 'susanoo', 'meteor', 'clones']:
            key = f'{label}-rank{rank}-q{quantity}-{kind}'
            profile = frame.evaluate(r"""({rank,quantity,kind})=>{
             const A=JAcceptance;A.reset();const p=A.p(),m=A.fixture('naruto-madara-'+kind,rank);
             if(kind==='clones')A.assert(p.addMove('naruto-madara-susanoo'),'clone presentation learn susanoo');
             p.quantityPicks=p.quantityBonus=quantity;p.invuln=999;
             const positions=kind==='meteor'?[[210,0],[270,50],[300,-55]]:[[110,0],[210,55],[260,-55]];
             for(const [x,y]of positions)A.spawn(x,y);
             A.resume();try{A.assert(G.NarutoMadara.cast(p,m),'presentation cast')}finally{A.pause()};
             return G.NarutoMadara.profile(p,m);
            }""", {'rank': rank, 'quantity': quantity, 'kind': kind})
            if kind == 'meteor':
                phases = [(0.7, 'telegraph'), (1.20, 'first-descent'), (1.30, 'first-impact'), (2.05, 'second-descent'), (2.17, 'second-impact'), (2.5, 'shock'), (6.8, 'recovery')]
            elif kind == 'clones':
                phases = [(0.20, 'sign'), (0.45, 'appear'), (1.0, 'independent-first'), (2.0, 'independent-late'), (12.8, 'expired')]
            else:
                first = profile['charge'] + 0.035
                last = profile['charge'] + (profile['pulses'] - 1) * profile['interval'] + 0.035
                phases = [(profile['charge'] * .5, 'charge'), (first, 'first'), (first + profile['interval'], 'second'), (last, 'last'), (profile['duration'] + .12, 'recovery')]
            stages = []
            previous = 0
            for at, phase in phases:
                frame.evaluate('dt=>JAcceptance.advance(dt)', at - previous)
                previous = at
                page.wait_for_timeout(50)
                page.screenshot(path=str(OUT / f'{key}-{phase}.png'))
                stage = frame.evaluate(r"""()=>{
                 const p=G.Game.player,M=G.NarutoMadara,s=M.stateFor(p);
                 return {pose:M.pose(p),stats:M.stats(p),effects:s.effects.map(e=>({kind:e.kind,index:e.index,last:e.last,x:e.x,y:e.y,age:e.age})),
                  fields:s.fields.map(f=>({age:f.age,index:f.index,meteorHits:f.meteorHits,tx:f.tx,ty:f.ty})),
                  clones:s.clones.map(c=>({x:c.x,y:c.y,age:c.age,kind:c.action?.kind,index:c.action?.index})),
                  hud:p.moves.map(m=>({id:m.id,...G.RunInsights.skillState(p,m)}))};
                }""")
                stages.append({'at': at, 'phase': phase, **stage})
            results[key] = {'fixture': 'controlled cast and manually advanced native combat clock', 'rank': rank, 'quantity': quantity, 'profile': profile, 'stages': stages}
    return results


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'sourceHashes': source_hashes(), 'cases': {}, 'errors': [], 'missing': [], 'failures': []}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
            for label, width, height, mobile in [('desktop', 1280, 900, False), ('mobile390', 390, 844, True), ('mobile360', 360, 800, True)]:
                if label not in os.environ.get('MADARA_VIEWS', 'desktop,mobile390,mobile360').split(','):
                    continue
                context = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                page.on('response', lambda r: report['missing'].append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
                result = report['cases'][label] = {}
                try:
                    print(label, 'boot', flush=True)
                    frame = boot(page, label)
                    if os.environ.get('MADARA_LOW') == '1':
                        frame.evaluate("G.Settings.set('quality','low')")
                    result['quality'] = frame.evaluate("({setting:G.Settings.get('quality'),fx:G.Settings.fx})")
                    checks = [('progression', lambda: frame.evaluate(PROGRESSION)),
                              ('starterGates', lambda: frame.evaluate(STARTER_GATES)),
                              ('inputAndBody', lambda: input_and_body(page, frame, context, mobile, label)),
                              ('mechanics', lambda: frame.evaluate(MECHANICS))]
                    if os.environ.get('MADARA_SKIP_PRESENTATION') != '1':
                        checks.append(('presentation', lambda: presentation(page, frame, label)))
                    for name, check in checks:
                        try:
                            print(label, name, flush=True)
                            result[name] = check()
                            if isinstance(result[name], dict):
                                report['failures'].extend(label + ':' + name + ':' + failure for failure in result[name].get('failures', []))
                        except Exception as e:
                            report['failures'].append(label + ':' + name + ': ' + str(e))
                            page.screenshot(path=str(OUT / f'{label}-{name}-failure.png'))
                    if os.environ.get('MADARA_SKIP_NATIVE') != '1':
                        try:
                            print(label, 'nativePlay', flush=True)
                            result['nativePlay'] = native_play(page, frame, context, mobile, label)
                        except Exception as e:
                            report['failures'].append(label + ':nativePlay: ' + str(e))
                            page.screenshot(path=str(OUT / f'{label}-native-failure.png'))
                except Exception as e:
                    report['failures'].append(label + ':boot: ' + str(e))
                    page.screenshot(path=str(OUT / f'{label}-boot-failure.png'))
                finally:
                    context.close()
                    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
            browser.close()
    finally:
        report['sourceHashesAfter'] = source_hashes()
        if report['sourceHashesAfter'] != report['sourceHashes']:
            report['failures'].append('runtime changed during acceptance; rerun')
        report['ok'] = not (report['errors'] or report['missing'] or report['failures'])
        (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'ok': report['ok'], 'failures': report['failures'], 'errors': report['errors'], 'evidence': str(OUT)}, ensure_ascii=True))
    if not report['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
