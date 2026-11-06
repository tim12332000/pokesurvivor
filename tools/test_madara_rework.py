"""Independent Madara acceptance through the production menu and combat loop.

Uses native enemies, collision, legal growth cards and damage callbacks. Controlled
fixtures are reported separately from native RAF/input presentation evidence.
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('MADARA_OUT', ROOT / 'art-review/madara/rework-play/mechanics'))
URL = os.environ.get('MADARA_URL', 'http://127.0.0.1:8347/.omx/digimon.html?lang=zh-TW')
DEX = 30016


def runtime(page):
    for _ in range(300):
        for frame in page.frames:
            try:
                if frame.evaluate("typeof G==='object'&&!!G.Game&&G.NarutoMadara?.version===2"):
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
    runtime = Path(os.environ.get('MADARA_SITE', ROOT))
    paths = [runtime / '.omx/naruto.js', runtime / '.omx/naruto-skills.js',
             runtime / '.omx/naruto-training.js', runtime / '.omx/digimon.html',
             runtime / 'js/game.js', runtime / 'js/main.js', runtime / 'js/core/audio.js', runtime / '.omx/digimon-size.js',
             runtime / '.omx/combat-pulse.js', runtime / 'art-review/madara/runtime.js',
             runtime / 'art-review/madara/madara-actions-v1.png']
    paths += list((runtime / '.omx').glob('*madara*'))
    for suffix in ['*.json', '*.js', '*.png']:
        paths += list((runtime / 'art-review/madara').glob(suffix))
    return {str(p.relative_to(runtime)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
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


MECHANICS = r"""() => {
 const A=JAcceptance,p=A.p(),M=G.NarutoMadara,assert=A.assert,out={failures:[]};
 assert(M.version===2,'rework engine is not loaded');
 let contacts=[],seen=new Set(),pulses=[],traceArmy=false,armyHistory=[];const previousPulse=G.CombatPulse.onPulse;
 G.CombatPulse.onPulse=info=>{pulses.push({time:M.stateFor(info.owner)?.clock,...info,owner:info.owner===p?'body':'self-clone',cast:undefined});previousPulse?.(info)};
 function check(name,fn){try{out[name]=fn()}catch(e){out.failures.push(name+': '+e.message);(out.failureEvidence??={})[name]={stats:M.stats(p),position:{x:p.x,y:p.y},lastContacts:contacts.slice(-80)}}finally{traceArmy=false}}
 function collect(){const stats=M.stats(p);for(const c of [...(stats?.contacts||[]),...(stats?.hitContacts||[])]){const key=JSON.stringify(c);if(!seen.has(key)){seen.add(key);contacts.push(c)}}
  const s=M.stateFor(p);if(traceArmy&&s&&(!armyHistory.length||s.clock-armyHistory.at(-1).time>=.05))armyHistory.push({time:s.clock,owner:{x:p.x,y:p.y},actors:s.army.map(a=>({serial:a.serial,role:a.role,x:a.x,y:a.y,target:a.target?.id,targetPosition:a.target?{x:a.target.x,y:a.target.y}:null,phase:a.phase,body:a.body?.spec.kind,guardian:!!a.guardian}))});
 }
 function advance(seconds,tick=false,move=false){for(let left=seconds;left>1e-8;){const dt=Math.min(.01,left);
  if(move){A.resume();try{p.update(dt);if(tick)G.Combat.tick(dt,p,0);G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,0);G.Combat.updateFields(dt)}finally{A.pause()}}
  else A.step(dt,tick);collect();left-=dt;
 }}
 function setup(id='naruto-madara',rank=1,q=0){A.reset();p.statsTaken={};const m=A.fixture(id,rank);p.quantityPicks=p.quantityBonus=q;contacts=[];seen=new Set();pulses=[];return m;}
 function add(id,rank=1){assert(p.addMove(id),'cannot learn '+id);const m=p.moves.find(m=>m.id===id);Object.assign(m,G.Moves.instance(id,rank));m.t=999;p.arrange();return m;}
 function cast(m,owner=p){A.resume();try{assert(M.cast(owner,m),'cast rejected '+m.id)}finally{A.pause()};return m.madaraKind==='susanoo'?M.stateFor(owner).guardian:M.stateFor(owner).body;}
 try{
 check('body-short-contact-not-old-sector',()=>{
  const m=setup(),inside=[[35,0],[43,13],[44,-13]].map(([x,y])=>A.spawn(x,y)),outside=A.spawn(130,0),logs=inside.map(A.watch);cast(m);advance(.9);
  assert(logs.every(h=>h.length>0)&&outside.hp===outside.maxHp,'real limb contacts missed near body or hit remote old sector');
  const events=contacts.filter(c=>c.kind==='basic');assert(events.length&&events.every(c=>c.geometry.kind==='capsule'),'body is not using short limb capsules');
  assert(new Set(events.map(c=>c.segment)).size===4,'four distinct contact phases missing');
  assert(logs.flat().every(h=>h.owner&&h.id===m.id),'body source attribution differs');
  return {hits:logs.map(h=>h.length),outsideDamage:outside.maxHp-outside.hp,contacts:events};
 });
 check('moving-cast-cannot-hit-old-fan-edge',()=>{
  const m=setup(),guard=add('naruto-madara-susanoo',3),e=A.spawn(105,30),hits=A.watch(e),axis=G.Input.axis;
  let accepted;G.Input.axis=()=>[1,0];try{A.resume();try{accepted=M.canCast(p,m)}finally{A.pause()};if(accepted)cast(m);advance(.9,true)}finally{G.Input.axis=axis}
  assert(hits.length===0&&M.stateFor(p).impetus===0,'remote fan-edge enemy got hit or miss granted momentum');
  assert(p.x===0&&p.y===0,'moving intent allowed automatic chase step');return {accepted,hits:hits.length,impetus:M.stateFor(p).impetus};
 });
 for(const [direction,x,y]of [['up65',0,-65],['up80',0,-80],['up35',0,-35],['right65',65,0],['left65',-65,0],['down65',0,65]])check('accepted-stationary-engagement-'+direction,()=>{
  const m=setup('naruto-madara',2),e=A.spawn(x,y),hits=A.watch(e);A.resume();let accepted;try{accepted=M.canCast(p,m)}finally{A.pause()}
  if(direction==='up35')assert(accepted,'near upward enemy wrongly rejected');
  advance(1.8,true);if(accepted)assert(hits.length>0,'native repeated accepted engagement spent cooldown but every authored limb whiffed at '+direction);
  assert(Math.hypot(p.x,p.y)<=M.profile(p,m).stepBudget*Math.max(1,M.stateFor(p).casts[m.id]||0)+1e-6,'stationary footwork exceeded per-round budget across native retries');
  return {accepted,hits:hits.length,casts:{...M.stateFor(p).casts},moved:{x:p.x,y:p.y},scope:'native automatic tick retries; true authored direction; rejection at genuinely unreachable range is permitted'};
 });
 check('kick-does-not-prescan-future-foot',()=>{
  const m=setup('naruto-madara',2),old=G.MadaraArt.socketFor,axis=G.Input.axis;A.spawn(30,0);
  G.Input.axis=()=>[1,0];G.MadaraArt.socketFor=(actor,name,{pose,height=64})=>{const a=name==='foot'?-.4+.8*pose.progress:0,r=name==='foot'?60:30;return {x:actor.x+Math.cos(a)*r,y:actor.y+Math.sin(a)*r-height*.5}};
  try{cast(m);advance(.32);const e=A.spawn(Math.cos(.4)*60,Math.sin(.4)*60);e.r=1;const hits=A.watch(e);advance(.03);
   assert(!hits.length,'early kick contacted a future leg position');advance(.065);assert(hits.length===1,'actual later foot sweep failed contact');
   return {hits:hits.length,contacts:contacts.filter(c=>c.kind==='basic'&&c.segment===2),scope:'adversarial authored socket, narrow target; not visual acceptance'};
  }finally{if(old)G.MadaraArt.socketFor=old;else delete G.MadaraArt.socketFor;G.Input.axis=axis}
 });
 check('moving-body-caches-previous-world-socket',()=>{
  const m=setup('naruto-madara',2),old=G.MadaraArt.socketFor,axis=G.Input.axis;A.spawn(30,0);G.Input.axis=()=>[1,0];
  G.MadaraArt.socketFor=(actor,name,{height=64})=>({x:actor.x+20,y:actor.y-height*.5});
  try{cast(m);advance(.265);const e=A.spawn(80,0);e.r=1;const hits=A.watch(e);p.x=100;advance(.01);
   assert(hits.length===1,'limb recomputed previous endpoint at new owner position and skipped travel');
   return {hits:hits.length,contacts:contacts.filter(c=>c.primaryHits&&c.segment===1),scope:'controlled moving-origin geometry; true retreat input separately checked'};
  }finally{if(old)G.MadaraArt.socketFor=old;else delete G.MadaraArt.socketFor;G.Input.axis=axis}
 });
 check('quantity-kick-tail-window-not-dropped',()=>{
  const m=setup('naruto-madara',2,4),old=G.MadaraArt.socketFor,axis=G.Input.axis;A.spawn(30,0);G.Input.axis=()=>[1,0];
  G.MadaraArt.socketFor=(actor,name,{pose,height=64})=>({x:actor.x+(name==='foot'&&pose.contact==='kick'&&pose.progress>.8?150:40),y:actor.y-height*.5});
  try{cast(m);advance(.625);const e=A.spawn(110,0);e.r=1;const hits=A.watch(e);advance(.025);
   assert(hits.length===1&&contacts.some(c=>c.segment===6&&c.primaryHits),'8-contact sixth-kick tail skipped when update crossed next segment');
   return {hits:hits.length,contacts:contacts.filter(c=>c.segment===6&&c.primaryHits),scope:'adversarial socket trajectory; tests elapsed tail clipping only'};
  }finally{if(old)G.MadaraArt.socketFor=old;else delete G.MadaraArt.socketFor;G.Input.axis=axis}
 });
 check('actual-hit-socket-and-drawn-body-frame-agree',()=>{
  const m=setup('naruto-madara',2),original=G.MadaraArt.socketFor,observed=[];assert(original,'authored body socket API missing');A.spawn(30,0);
  G.MadaraArt.socketFor=function(actor,name,options){const result=original.call(this,actor,name,options),drawPose=M.pose(p);
   if(actor===p&&drawPose?.kind==='basic'&&options.pose?.index===drawPose.index&&Math.abs(options.pose.progress-drawPose.progress)<1e-6){
    const frame=G.MadaraArt.sample('cast',drawPose.age,p.anim.dir,drawPose);observed.push({contact:drawPose.contact,progress:drawPose.progress,drawPhase:drawPose.phase,socketPhase:options.pose.phase,drawSheet:frame?.sheet,drawIndex:frame?.index,socketSheet:result?.sheet,socketIndex:result?.index});
   }return result;
  };
  try{cast(m);advance(.62)}finally{G.MadaraArt.socketFor=original}
  const active=observed.filter(c=>c.socketPhase==='contact');assert(active.length&&active.every(c=>c.drawSheet===c.socketSheet&&c.drawIndex===c.socketIndex),'physics socket and actual drawn sprite sampled different contact frame '+JSON.stringify(active.filter(c=>c.drawSheet!==c.socketSheet||c.drawIndex!==c.socketIndex)));
  return {samples:active,scope:'real loaded sprite frames and sockets, excludes retrospective previous-segment tail samples'};
 });
 check('fire-front-near-before-far-and-side-boundary',()=>{
  const m=setup('naruto-madara-fire'),near=A.spawn(100,0),middle=A.spawn(260,80),far=A.spawn(460,-100),outside=A.spawn(260,250),logs=[near,middle,far].map(A.watch);cast(m);
  advance(.28);assert(logs.every(h=>h.length===0),'fire damaged at cast instead of front arrival');advance(.18);
  assert(logs[0].length>0&&logs[2].length===0,'near/far did not separate by firefront travel');advance(1.6);
  assert(logs.every(h=>h.length===4)&&outside.hp===outside.maxHp,'four independent advancing fronts/side boundary differs '+logs.map(h=>h.length));
  const events=contacts.filter(c=>c.kind==='fire'&&c.channel==='field-fire');assert(events.some(c=>c.geometry.kind==='wall'&&c.geometry.to>c.geometry.from),'missing swept front geometry');
  return {hits:logs.map(h=>h.length),outsideDamage:outside.maxHp-outside.hp,firstHitTimes:events.filter(c=>c.primaryHits).map(c=>c.time),contacts:events.filter(c=>c.primaryHits)};
 });
 check('fire-released-origins-stay-in-world',()=>{
  const m=setup('naruto-madara-fire');A.spawn(220,0);cast(m);advance(.28);const first=M.stateFor(p).fires[0];assert(first,'first firefront absent');
  const frozen={x:first.x,y:first.y,aim:first.aim};p.x=120;p.y=100;p.aim=Math.PI;advance(.34);
  const later=M.stateFor(p).fires.filter(f=>f!==first);assert(later.length===3&&later.every(f=>f.x>first.x+90),'later fronts did not use live mouth origin');
  assert(first.x===frozen.x&&first.y===frozen.y&&first.aim===frozen.aim,'released front teleported/rotated with owner');
  return {first:frozen,later:later.map(f=>({x:f.x,y:f.y,aim:f.aim})),scope:'controlled moving-origin fixture; true input separately checked'};
 });
 check('guardian-real-blade-contact',()=>{
  const m=setup('naruto-madara-susanoo',2),victims=[[100,0],[140,40],[170,-50]].map(([x,y])=>A.spawn(x,y)),outside=A.spawn(700,-350),hits=victims.map(A.watch),g=cast(m);
  advance(.40);assert(hits.every(h=>!h.length),'guardian damaged during manifestation/draw');advance(5.8);
  assert(hits.every(h=>h.length>0)&&outside.hp===outside.maxHp,'blade sweep missed true path or hit outside');
  const events=contacts.filter(c=>c.channel==='guardian');assert(events.length&&events.every(c=>c.geometry.kind==='capsule'),'guardian still uses sector damage');
  assert(new Set(events.filter(c=>c.primaryHits).map(c=>c.segment)).size>=4,'guardian did not perform separate true sweeps');
  return {hits:hits.map(h=>h.length),form:g.form,contacts:events.filter(c=>c.primaryHits)};
 });
 check('authored-avatar-four-directions-and-blade-sockets',()=>{
  const samples=[];for(const form of ['rib','armored','perfect'])for(const [direction,aim]of [['right',0],['left',Math.PI],['up',-Math.PI/2],['down',Math.PI/2]]){
   const frame=G.MadaraArt.avatarSample(form,'sweep',.15,aim,{progress:.5});assert(frame,'authored '+form+'/'+direction+' missing');samples.push({form,direction,sheet:frame.sheet,index:frame.index,mirror:frame.mirror});
  }
  for(const form of ['rib','armored','perfect']){const up=samples.find(s=>s.form===form&&s.direction==='up'),down=samples.find(s=>s.form===form&&s.direction==='down'),right=samples.find(s=>s.form===form&&s.direction==='right');
   assert(up.sheet!==right.sheet&&down.sheet!==right.sheet&&up.index!==down.index,'avatar up/down reused the side frame '+form);}
  const m=setup('naruto-madara-susanoo',2);A.spawn(100,0);const g=cast(m);advance(.54);assert(g.authoredBlade&&g.blade,'guardian still using algorithmic fallback blade');
  const options={x:p.x,y:p.y,height:235,form:g.form,phase:g.phase,age:g.swing?g.age-g.swing.start:g.age,progress:g.swing?.progress||0,aim:g.aim,side:g.index%2?-1:1};
  const a=G.MadaraArt.avatarSocketFor(p,'bladeBase',options),b=G.MadaraArt.avatarSocketFor(p,'bladeTip',options);
  assert(a&&b&&Math.abs(g.blade.ax-a.x)<1e-6&&Math.abs(g.blade.ay-a.y-40)<1e-6&&Math.abs(g.blade.bx-b.x)<1e-6&&Math.abs(g.blade.by-b.y-40)<1e-6,'true collision blade endpoints differ from authored visible blade sockets');
  return {samples,blade:g.blade,authoredBase:a,authoredTip:b,scope:'frame/socket transform agreement, not visual depth or enjoyment approval'};
 });
 check('q4-cd05-guardian-body-and-fire-overlap',()=>{
  const basic=setup('naruto-madara',5,4),fire=add('naruto-madara-fire',5),guard=add('naruto-madara-susanoo',5);p.cdMul=.5;
  const victims=[[42,0],[55,18],[140,20],[300,-70],[450,60]].map(([x,y])=>A.spawn(x,y));fire.t=basic.t=0;guard.t=0;const nativeCast=p.cast,events=[];
  p.cast=function(move,...args){events.push({time:M.stateFor(p).clock,id:move.id});return nativeCast.call(this,move,...args)};
  try{cast(guard);advance(5.8,true)}finally{p.cast=nativeCast}
  const s=M.stateFor(p),body=contacts.filter(c=>c.channel==='body'&&c.kind==='basic'&&c.primaryHits),fronts=contacts.filter(c=>c.channel==='field-fire'&&c.primaryHits),blades=contacts.filter(c=>c.channel==='guardian'&&c.primaryHits);
  assert(s.guardian&&blades.length,'fixture lost continuing guardian');
  assert((s.casts['naruto-madara']||0)>=2&&(s.casts['naruto-madara-fire']||0)>=1&&body.length&&fronts.length,'guardian starved actual body/fire, despite ready status '+JSON.stringify(s.casts));
  const perfectStarted=s.guardian.perfect?s.clock-s.guardian.age:null;
  if(perfectStarted!==null)for(const [id,hitEvents]of [['naruto-madara',body],['naruto-madara-fire',fronts]])assert(events.some(e=>e.id===id&&e.time>perfectStarted+.05)&&hitEvents.some(e=>e.time>perfectStarted+.05),'perfect window specifically starved new '+id+' casts or real contacts');
  return {casts:{...s.casts},events,perfectStarted,bodyHitContacts:body.length,fireHitContacts:fronts.length,guardianHitContacts:blades.length,guardianAge:s.guardian.age,perfectCount:s.perfectCount};
 });
 check('momentum-once-per-valid-body-round',()=>{
  const m=setup();add('naruto-madara-susanoo',3);const victims=[A.spawn(35,0),A.spawn(43,10),A.spawn(44,-10),A.spawn(20,30)];cast(m);advance(.9);
  assert(M.stateFor(p).impetus===1,'multi-target basic granted other than one momentum');m.t=0;cast(m);advance(.9);
  assert(M.stateFor(p).impetus===2,'second valid round failed single credit');
  return {impetus:M.stateFor(p).impetus,contacts:contacts.filter(c=>c.primaryHits).length};
 });
 check('q4-cd05-earned-perfect-window-automatic-body-fire',()=>{
  const basic=setup('naruto-madara',5,4),fire=add('naruto-madara-fire',5),guard=add('naruto-madara-susanoo',5);p.cdMul=.5;
  for(const [x,y]of [[35,0],[100,0],[180,30],[350,-60]])A.spawn(x,y);guard.t=0;cast(guard);
  for(let round=0;round<3;round++){fire.t=0;cast(fire);advance(round===2?.8:1.5)}
  const s=M.stateFor(p);assert(s.guardian?.perfect&&s.perfectCount===1,'three real fire rounds failed to earn controlled perfect window');
  const start=s.clock,native=p.cast,events=[];p.cast=function(move,...args){events.push({time:s.clock,id:move.id});return native.call(this,move,...args)};
  try{advance(5.2,true)}finally{p.cast=native}
  assert(s.guardian?.perfect,'fixture ended its perfect window before automatic overlap observation');
  const bodyEvents=events.filter(e=>e.id===basic.id),fireEvents=events.filter(e=>e.id===fire.id);
  assert(bodyEvents.length>=2&&fireEvents.length>=1,'perfect guardian starved automatic fresh body/fire casts '+JSON.stringify(events));
  assert(contacts.some(c=>c.time>start&&c.channel==='body'&&c.primaryHits)&&contacts.some(c=>c.time>fireEvents[0].time+.2&&c.channel==='field-fire'&&c.primaryHits),'perfect overlap casts were cosmetic without true contacts');
  return {start,end:s.clock,events,perfectRemaining:s.guardian.duration-s.guardian.age,bodyCasts:bodyEvents.length,freshFireCasts:fireEvents.length};
 });
 check('earlier-hit-final-miss-gives-no-momentum',()=>{
  const m=setup();add('naruto-madara-susanoo',3);const e=A.spawn(35,0),finalTarget=A.spawn(20,30),hits=A.watch(e);cast(m);advance(.35);assert(hits.length>0,'early-hit fixture did not contact');
  e.x=600;e.y=600;finalTarget.x=650;finalTarget.y=650;G.EnemyMgr.rebuildGrid();advance(.6);assert(M.stateFor(p).impetus===0,'whole-round earlier hit incorrectly credited missed final contact');
  return {earlierHits:hits.length,impetus:M.stateFor(p).impetus};
 });
 check('fire-many-fronts-once-and-empty-cast-zero',()=>{
  const m=setup('naruto-madara-fire',3,4);add('naruto-madara-susanoo',3);for(const [x,y]of [[100,0],[220,50],[410,-60]])A.spawn(x,y);cast(m);advance(2.8);
  assert(M.stateFor(p).impetus===1,'fire fronts/linger/splash recursively gained momentum');
  const before=M.stateFor(p).impetus;m.t=0;cast(m);G.EnemyMgr.clear();G.EnemyMgr.rebuildGrid();advance(2.8);
  assert(M.stateFor(p).impetus===before,'cast without enemy contact gained momentum');return {impetus:before};
 });
 check('earned-perfect-six-second-window-and-fields-survive',()=>{
  const basic=setup(),guard=add('naruto-madara-susanoo',3),fire=add('naruto-madara-fire',3);A.spawn(35,0);A.spawn(20,30);A.spawn(240,30);guard.t=0;cast(guard);advance(.05);
  for(let round=0;round<3;round++){basic.t=0;cast(basic);advance(.9)}
  const s=M.stateFor(p);assert(s.perfectCount===1&&s.guardian?.perfect&&s.guardian.form==='perfect','three valid body rounds did not earn complete form');
  const started=s.clock-s.guardian.age;for(let i=0;i<180&&!s.pressures.length;i++)advance(.02);assert(s.pressures.length,'complete form emitted no sword pressure');
  const pressure=s.pressures[0],victim=A.spawn(pressure.x+Math.cos(pressure.aim)*200,pressure.y+Math.sin(pressure.aim)*200),pressureHits=A.watch(victim);
  advance(.36);assert(pressureHits.length>0&&contacts.some(c=>c.channel==='guardian-pressure'&&c.primaryHits),'sword pressure had no true forward hit');
  assert(s.impetus===0,'sword pressure recursively generated momentum');advance(Math.max(0,4.9-s.guardian.age));fire.t=0;cast(fire);advance(.5);const references=[...s.fires];assert(references.length,'released field fixture missing');
  const left=6-s.guardian.age;advance(left+.02);assert(!s.guardian,'perfect window exceeded six seconds');
  assert(references.some(f=>s.fires.includes(f)),'perfect end cleared unrelated released fire fronts');
  assert(contacts.some(c=>c.channel==='guardian-pressure'&&c.geometry.kind==='wall'),'complete form produced no true forward sword pressure');
  return {perfectCount:s.perfectCount,started,ended:s.clock,remainingFronts:s.fires.length,pressureContacts:contacts.filter(c=>c.channel==='guardian-pressure'&&c.primaryHits).length};
 });
 check('self-clone-does-not-feed-perfect',()=>{
  const basic=setup(),guard=add('naruto-madara-susanoo',3),clone=G.SelfClones.summon(p);assert(clone,'self clone missing');clone.x=clone.y=0;
  const cm=clone.moves.find(m=>m.id===basic.id);A.spawn(35,0);for(let round=0;round<3;round++){
   cm.t=0;cast(cm,clone);advance(.45);const pose=M.pose(clone),point=G.MadaraArt.socketFor(clone,'foot',{pose:{...pose,phase:'contact',progress:.5},height:64,dir:Math.cos(pose.aim)<0?6:2});
   assert(point,'last-limb socket probe absent');A.spawn(point.x,point.y+32);advance(.45);
  }
  const s=M.stateFor(clone),finals=M.stats(clone).hitContacts.filter(c=>c.kind==='basic'&&c.segment===3&&c.primaryHits);
  assert(new Set(finals.map(c=>c.castId)).size===3,'self-clone comparison did not exercise real final limb hits');
  assert(s?.hits>0&&s.impetus===0&&s.perfectCount===0,'self-clone final contacts fed forbidden momentum');
  return {hits:s.hits,validFinals:finals.length,impetus:s.impetus,perfectCount:s.perfectCount,scope:'source-isolation fixture places a target at the real authored last-limb contact, not natural play'};
 });
 check('self-clone-fire-does-not-feed-perfect',()=>{
  const fire=setup('naruto-madara-fire');add('naruto-madara-susanoo',3);const clone=G.SelfClones.summon(p);assert(clone,'self clone missing');clone.x=clone.y=0;
  const cm=clone.moves.find(m=>m.id===fire.id);A.spawn(100,0);A.spawn(200,30);for(let round=0;round<3;round++){cm.t=0;cast(cm,clone);advance(2)}
  const s=M.stateFor(clone);assert(s.hits>0&&s.impetus===0&&s.perfectCount===0,'self-clone fire rounds fed forbidden momentum');return {hits:s.hits,impetus:s.impetus,perfectCount:s.perfectCount};
 });
 check('army-role-sources-no-recursive-momentum',()=>{
  const m=setup('naruto-madara-clones',3);add('naruto-madara');add('naruto-madara-fire',3);add('naruto-madara-susanoo',3);
  for(const [x,y]of [[90,0],[230,-140],[230,140],[-150,50],[300,0]])A.spawn(x,y);traceArmy=true;armyHistory=[];cast(m);advance(1.3);
  const first=M.stateFor(p).army.find(a=>a.role==='front'),retained=first.target;assert(retained,'front actor selected no target');A.spawn(first.x+3,first.y);advance(.08);assert(first.target===retained,'front abandoned a still-valid target for newly closer prey');
  G.EnemyMgr.removeRemote(retained.id,false);advance(.08);assert(first.target!==retained&&G.EnemyMgr.all().includes(first.target),'army did not reassign removed live target');advance(5);
  const s=M.stateFor(p),roles=new Set(s.army.map(a=>a.role)),ids=new Set(s.army.map(a=>a.serial));
  assert(roles.has('front')&&roles.has('flank-left')&&roles.has('flank-right')&&roles.has('guard')&&ids.size===s.army.length,'army lacks stable four-role actor identities');
  const landed=contacts.filter(c=>c.primaryHits&&String(c.channel).startsWith('army-'));
  assert(landed.some(c=>c.role==='front'&&c.kind==='basic')&&landed.some(c=>c.role?.startsWith('flank')&&c.kind==='fire')&&landed.some(c=>c.role==='guard'&&c.channel==='army-guardian'),'army roles did not create distinct real attack sources');
  assert(s.impetus===0&&s.perfectCount===0&&s.army.length===5,'army recursively fed momentum, perfect or nested summons');
  assert(new Set(s.army.map(a=>a.x.toFixed(1)+','+a.y.toFixed(1))).size===s.army.length,'army sources collapsed into the same position');
  return {roles:[...roles],actors:s.army.map(a=>({serial:a.serial,role:a.role,x:a.x,y:a.y})),retarget:{old:retained.id,reassigned:first.target.id},history:armyHistory,landedByRole:landed.map(c=>({time:c.time,source:c.source,role:c.role,channel:c.channel,kind:c.kind,geometry:c.geometry})),impetus:s.impetus};
 });
 check('army-two-legal-upgrades-unlock-real-rear-guardian',()=>{
  const m=setup('naruto-madara-clones');add('naruto-madara');add('naruto-madara-fire');add('naruto-madara-susanoo');
  function encounter(){G.Combat.clearFields(p);G.EnemyMgr.clear();G.EnemyMgr.rebuildGrid();contacts=[];seen=new Set();armyHistory=[];traceArmy=true;m.t=0;
   for(const [x,y]of [[90,0],[200,-100],[200,100],[-120,40],[300,0]])A.spawn(x,y);cast(m);advance(6);
   const s=M.stateFor(p),guard=s.army.find(a=>a.role==='guard'),landed=contacts.filter(c=>c.source===guard.serial&&c.primaryHits);return {rank:m.lvl,guardId:guard.serial,actorCount:s.army.length,landed:landed.map(c=>({channel:c.channel,kind:c.kind,geometry:c.geometry})),history:armyHistory};}
  const before=encounter(),cards=[];assert(before.landed.some(c=>c.kind==='basic')&&!before.landed.some(c=>c.channel==='army-guardian'),'rank1 guard fallback was not real basic combat');
  for(let i=0;i<2;i++){const card=G.LevelUp.offer(p,1000).find(c=>c.key==='up:'+m.id);assert(card&&card.apply(p)!==false,'legal army upgrade unavailable');cards.push(card.desc);}
  const after=encounter();assert(after.rank===3&&after.landed.some(c=>c.channel==='army-guardian'),'two legal army upgrades changed count but failed to unlock actual rear guardian contact');
  assert(cards[1].includes('分工類別 2→3'),'army functional role upgrade missing from live card preview');return {before,after,cards,cost:2};
 });
 check('live-army-growth-adds-only-difference-and-keeps-clocks',()=>{
  const m=setup('naruto-madara-clones');add('naruto-madara');add('naruto-madara-fire');add('naruto-madara-susanoo');
  for(const [x,y]of [[35,0],[120,30],[200,-80],[-100,0]])A.spawn(x,y);cast(m);advance(1.4);const s=M.stateFor(p),old=s.army.map(a=>({a,serial:a.serial,x:a.x,y:a.y,age:a.age,life:a.life,cooldown:a.cooldown,body:a.body,bodyAge:a.body?.age})),cd=m.t,oldIds=new Set(old.map(a=>a.serial));
  assert(old.length===4,'rank1 army fixture differs');
  const before=contacts.find(c=>c.source===old[0].serial&&c.kind==='basic'&&c.segment===0&&c.primaryHits);assert(before,'front rank1 true palm contact missing');
  const quantity=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');assert(quantity&&quantity.apply(p)!==false,'live quantity card unavailable');advance(.01);
  const added=s.army.filter(a=>!oldIds.has(a.serial));assert(s.army.length===5&&added.length===1&&added[0].age<.1&&!added[0].body&&!added[0].guardian,'quantity did not add exactly one genuinely emerging actor');
  for(const a of old){assert(s.army.includes(a.a)&&Math.abs(a.a.age-a.age-.01)<1e-6&&a.a.life===a.life,'quantity reset original actor identity/life/clock');
   if(a.body&&a.body.spec.duration-a.bodyAge>.03)assert(a.a.body===a.body&&Math.abs(a.a.body.age-a.bodyAge-.01)<1e-6&&a.a.x===a.x&&a.a.y===a.y,'quantity reset ongoing source action or position');
  }
  assert(Math.abs((added[0].life-added[0].age)-(old[0].a.life-old[0].a.age))<.025&&m.t===cd,'new actor gained fresh cohort duration or free skill cooldown');
  advance(.3);assert(!contacts.some(c=>c.source===added[0].serial),'new source attacked before real emerge phase');
  const rank=G.LevelUp.offer(p,1000).find(c=>c.key==='up:'+m.id),rankAt=s.clock,actorState=old.map(({a})=>({a,serial:a.serial,age:a.age,life:a.life,cooldown:a.cooldown,body:a.body}));
  assert(rank&&rank.apply(p)!==false,'live clone upgrade unavailable');advance(.01);
  for(const item of actorState)assert(s.army.includes(item.a)&&item.a.serial===item.serial&&item.a.life===item.life&&Math.abs(item.a.age-item.age-.01)<1e-6&&item.a.rank===2,'live rank changed actor identity/lifetime or failed role rank update');
  advance(2);const after=contacts.find(c=>c.time>rankAt+.1&&c.source===old[0].serial&&c.kind==='basic'&&c.segment===0&&c.primaryHits);
  assert(after&&Math.abs((after.primaryDamage/after.primaryHits)/(before.primaryDamage/before.primaryHits)-1.2)<1e-7,'live rank1→2 did not change same front actor real hurt by 1.2x');
  assert(m.t===cd,'growth reset summon cooldown');return {oldSerials:[...oldIds],newSerial:added[0].serial,rank1Palm:before.primaryDamage/before.primaryHits,rank2Palm:after.primaryDamage/after.primaryHits,quantityPreview:quantity.desc,rankPreview:rank.desc,cohortExpires:s.armyExpires};
 });
 check('army-rear-guardian-relocates-into-real-distant-blade-path',()=>{
  const m=setup('naruto-madara-clones',3);add('naruto-madara');add('naruto-madara-fire');add('naruto-madara-susanoo',3);
  for(const [x,y]of [[360,0],[410,-140],[410,140],[500,25],[450,-50]])A.spawn(x,y);traceArmy=true;armyHistory=[];cast(m);advance(10);
  const s=M.stateFor(p),guard=s.army.find(a=>a.role==='guard'),hits=contacts.filter(c=>c.source===guard.serial&&c.channel==='army-guardian'&&c.primaryHits);
  assert(hits.length>0,'rear guardian remained near owner and swung out of actual blade range');
  const history=armyHistory.flatMap(sample=>sample.actors.filter(a=>a.serial===guard.serial).map(a=>({time:sample.time,...a})));
  assert(history.some(a=>Math.hypot(a.x,a.y)>100),'rear source did not reposition for distant targets');
  return {guardId:guard.serial,history,landed:hits.map(c=>({time:c.time,geometry:c.geometry,hits:c.primaryHits}))};
 });
 check('meteor-two-impacts-and-distinct-fragment-landings',()=>{
  const m=setup('naruto-madara-meteor'),e=A.spawn(400,0),f=cast(m);advance(.5);const s=M.stateFor(p),rocks=s.meteors.filter(r=>!r.fragment);
  assert(rocks.length===2&&rocks[1].radius>rocks[0].radius,'two materially different main rocks missing');
  assert(!s.meteors.some(r=>r.fragment),'fragments pre-spawned before actual second impact');
  const center=rocks.map(r=>[r.x,r.y]);p.x=-500;p.y=400;advance(1.05);
  assert(s.craters.length===1&&contacts.filter(c=>c.channel==='field-meteor'&&c.primaryHits).length===1,'first actual impact/crater cause missing');
  advance(.9);assert(contacts.filter(c=>c.channel==='field-meteor'&&c.geometry.radius>=220).length>=2,'second main impact missing');
  const fragments=s.meteors.filter(r=>r.fragment);assert(fragments.length===4&&new Set(fragments.map(r=>r.x+','+r.y)).size===4,'quantity fragments are not distinct true landing sites');
  assert(fragments.every(r=>r.sourceX===rocks[1].x&&r.sourceY===rocks[1].y)&&fragments.some(r=>r.flightProgress>0&&r.flightProgress<1&&r.height>0),'fragments did not physically launch from second-impact material source');
  assert(rocks.every((r,i)=>r.x===center[i][0]&&r.y===center[i][1]),'main rocks followed caster');advance(2);
  const small=contacts.filter(c=>c.channel==='field-meteor'&&c.geometry.kind==='circle'&&c.geometry.radius<220);
  assert(new Set(small.map(c=>c.geometry.x+','+c.geometry.y)).size===4,'fragment landing geometry did not change real impact locations');
  return {mainCenters:center,mainRadii:rocks.map(r=>r.radius),fragmentLandings:small.map(c=>({time:c.time,geometry:c.geometry,hits:c.primaryHits}))};
 });
 check('cancelled-first-rock-cannot-create-second-shatter',()=>{
  const m=setup('naruto-madara-meteor');A.spawn(300,0);cast(m);advance(.5);const s=M.stateFor(p),first=s.meteors.find(r=>!r.second&&!r.fragment);assert(first,'first rock source absent');
  first.cast.runEpoch=-1;advance(3);assert(!s.craters.length&&!s.meteors.some(r=>r.fragment)&&!contacts.some(c=>c.channel==='field-meteor'),'second shatter occurred without a valid first landing event');
  return {craters:s.craters.length,fragmentContacts:contacts.length,scope:'controlled independent cancellation of first rock source'};
 });
 check('crater-fire-relay-once-not-through-wall',()=>{
  const meteor=setup('naruto-madara-meteor',3),fire=add('naruto-madara-fire',3),target=A.spawn(300,0);add('naruto-madara-susanoo',3);cast(meteor);advance(2.7);
  const s=M.stateFor(p);assert(s.craters.length,'true first-impact crater missing');p.x=0;p.y=0;fire.t=0;cast(fire);
  const old=G.World.projectilePathClear;G.World.projectilePathClear=(x,y,tx,ty,...args)=>tx>=150?false:old(x,y,tx,ty,...args);
  try{advance(2)}finally{G.World.projectilePathClear=old}
  assert(!contacts.some(c=>c.channel==='field-rubble'),'crater relay crossed an occluding wall');
  fire.t=0;cast(fire);advance(2);const relays=contacts.filter(c=>c.channel==='field-rubble');assert(relays.length===1&&relays[0].primaryHits>0,'one fire round did not cause exactly one true rubble relay '+relays.length);
  assert(s.impetus===1,'rubble relay or meteor fed extra momentum');
  return {relays:relays.map(c=>({castId:c.castId,geometry:c.geometry,hits:c.primaryHits}))};
 });
 // Common cancellation and native integration boundaries retain the existing guarantees.
 for(const id of ['naruto-madara','naruto-madara-fire','naruto-madara-susanoo','naruto-madara-meteor'])check('no-enemy-prop-'+id,()=>{
  const m=setup(id),prop={x:45,y:0,r:12,type:'chest',solid:true,destructible:true,hp:1,tx:999999,ty:999999};
  G.World.propsInCircle=(x,y,r)=>prop.hp>0&&Math.hypot(prop.x-x,prop.y-y)<=r+prop.r?[prop]:[];
  G.World.projectileBlock=(x,y,r=1)=>prop.hp>0&&Math.hypot(prop.x-x,prop.y-y)<=prop.r+r?prop:false;
  const old=G.World.damageProp,events=[];G.World.damageProp=function(t,amount,...args){events.push({same:t===prop,amount});return old.call(this,t,amount,...args)};
  try{cast(m);advance(4)}finally{G.World.damageProp=old}assert(prop.hp<=0&&events.length&&events.every(e=>e.same),'native no-enemy prop cannot be destroyed');return {hp:prop.hp,events};
 });
 for(const cancel of ['clear','unlearn','death','world','epoch'])check('cancel-'+cancel,()=>{
  const m=setup('naruto-madara-fire'),e=A.spawn(100,0),hits=A.watch(e);cast(m);advance(.46);assert(hits.length>0,'cancel fixture did not release first front');const count=hits.length,world=G.World;
  if(cancel==='clear')G.Combat.clearFields(p);if(cancel==='unlearn')p.moves=[];if(cancel==='death'){p.dead=true;p.hp=0}if(cancel==='world')G.World=Object.create(world);if(cancel==='epoch')G.CombatPulse.beginRun();
  try{advance(3)}finally{G.World=world}assert(hits.length===count&&!M.pose(p),'cancel retained late contact');return {hits:count};
 });
 for(const callback of ['hurt','onDealt'])for(const mode of ['clear','unlearn','remove-next'])check('same-wave-'+callback+'-'+mode,()=>{
  const m=setup('naruto-madara-fire'),first=A.spawn(100,0),second=A.spawn(100,0),h1=A.watch(first),h2=A.watch(second);cast(m);
  const target=callback==='hurt'?first:p,original=target[callback];target[callback]=function(...args){if(mode==='clear')G.Combat.clearFields(p);else if(mode==='unlearn')p.moves=[];else G.EnemyMgr.removeRemote(second.id,false);return original.apply(this,args)};
  try{advance(3)}finally{target[callback]=original}assert(h1.length>0&&h2.length===0,'same-wave callback hit cancelled/removed second actor '+h1.length+'/'+h2.length);return {first:h1.length,second:h2.length};
 });
 check('stale-grid-primary-and-outer',()=>{
  const m=setup('naruto-madara-fire'),first=A.spawn(100,0),stale=A.spawn(100,30),h1=A.watch(first),h2=A.watch(stale);p.damageSplashPicks=1;G.EnemyMgr.removeRemote(stale.id,false);cast(m);advance(2);
  assert(h1.length===4&&!h2.length,'removed grid actor received primary or outer damage');return {liveHits:h1.length,removedHits:h2.length};
 });
 for(const [id,x]of [['naruto-madara',45],['naruto-madara-fire',100],['naruto-madara-susanoo',100],['naruto-madara-meteor',300]])check('occlusion-'+id,()=>{
  const m=setup(id),e=A.spawn(x,0);cast(m);const original=G.World.projectilePathClear;G.World.projectilePathClear=()=>false;
  try{advance(6.5)}finally{G.World.projectilePathClear=original}assert(e.hp===e.maxHp,'contact crossed occluding path');return true;
 });
 check('prop-callback-cancels-next-prop',()=>{
  const m=setup(),props=[40,45].map(x=>({x,y:0,r:12,hp:10000,destructible:true}));G.World.propsInCircle=()=>props;G.World.projectileBlock=()=>false;
  const original=G.World.damageProp,calls=[];G.World.damageProp=(target,damage)=>{calls.push(props.indexOf(target));target.hp-=damage;G.Combat.clearFields(p)};
  try{cast(m);advance(2)}finally{G.World.damageProp=original}assert(calls.join(',')==='0'&&props[1].hp===10000,'prop callback retained another contact '+calls);return {calls};
 });
 check('self-clone-owner-clear-isolation',()=>{
  const m=setup('naruto-madara-fire'),clone=G.SelfClones.summon(p);assert(clone,'native self clone missing');clone.x=clone.y=0;A.spawn(100,0);
  const cm=clone.moves.find(move=>move.id===m.id);cm.t=0;const body=cast(m),copy=cast(cm,clone);assert(body.cast.castId!==copy.cast.castId,'owners shared cast');
  M.clear(p);advance(2);assert(!M.stateFor(p)&&M.stats(clone)?.hits>0,'module owner clear cancelled independent source');return {cloneHits:M.stats(clone).hits};
 });
 check('unlearn-army-clears-pending-sources',()=>{
  const m=setup('naruto-madara-clones',3);add('naruto-madara');add('naruto-madara-fire');add('naruto-madara-susanoo');A.spawn(40,0);A.spawn(200,40);cast(m);advance(2);
  const s=M.stateFor(p),before=s.hits;assert(s.army.length>0&&before>0,'army cleanup fixture did not attack');p.moves=p.moves.filter(m=>m.id!=='naruto-madara-clones');advance(4);
  assert(!s.army.length&&s.hits===before,'unlearned army retained live sources');return {hits:before};
 });
 check('pause-and-levelup-readonly',()=>{
  const m=setup('naruto-madara-meteor');A.spawn(300,0);cast(m);advance(.8);const s=M.stateFor(p),snapshot=()=>JSON.stringify({clock:s.clock,rocks:s.meteors.map(r=>({age:r.age,x:r.x,y:r.y,landed:r.landed})),hits:s.hits});
  const draw=()=>{const c=document.createElement('canvas');c.width=1200;c.height=1000;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.translate(400,600);M.draw(ctx,true);M.draw(ctx,false);const data=ctx.getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<data.length;i+=4)if(data[i])n++;return n};
  const before=snapshot();A.resume();const playing=draw();A.pause();const paused=draw();M.update(4);const desc=Object.getOwnPropertyDescriptor(G.Game,'state');let levelup;
  try{Object.defineProperty(G.Game,'state',{configurable:true,value:'levelup'});levelup=draw();M.update(4)}finally{Object.defineProperty(G.Game,'state',desc)}
  assert(playing>500&&paused===playing&&levelup===playing&&snapshot()===before,'pause/levelup draw hid or advanced released rocks');return {playing,paused,levelup,scope:'render-state override for levelup, no natural level grant'};
 });
 check('frozen-owner-suspends-released-fields',()=>{
  const m=setup('naruto-madara-fire'),e=A.spawn(100,0);cast(m);advance(.4);const s=M.stateFor(p),snapshot=()=>JSON.stringify({clock:s.clock,bodyAge:s.body?.age,fronts:s.fires.map(f=>({age:f.age,distance:f.distance})),hp:e.hp});
  const before=snapshot();p.frozen=true;try{advance(2);assert(snapshot()===before,'freeze advanced this owner released fields contrary to explicit clock contract')}finally{p.frozen=false}
  const hp=e.hp;advance(2);assert(e.hp<hp,'unfreeze failed to resume firefronts');return {suspended:true,resumedDamage:hp-e.hp};
 });
 check('legal-growth-and-live-preview',()=>{
  const fire=setup('naruto-madara-fire'),quantity=[];
  for(let i=0;i<3;i++){const before=M.profile(p,fire).fronts,card=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');assert(card&&card.apply(p)!==false,'legal quantity missing');quantity.push({before,after:M.profile(p,fire).fronts,desc:card.desc});}
  assert(quantity[0].before===4&&quantity[0].after===5&&quantity.every(s=>s.after>s.before),'first cards did not produce additional real fronts');
  const upgrades=[];for(let i=0;i<4;i++){const next=G.Moves.instance(fire.id,fire.lvl+1),before=M.profile(p,fire).fronts,after=M.profile(p,next).fronts,card=G.LevelUp.offer(p,1000).find(c=>c.key==='up:'+fire.id);
   assert(card,'legal upgrade missing');if(before!==after)assert(card.desc.includes(before+'→'+after),'live quantity-adjusted preview differs '+card.desc);assert(card.apply(p)!==false,'upgrade rejected');upgrades.push(card.desc);}
  const previews=[];while(G.LevelUp.offer(p,1000).some(c=>c.key==='stat:quantity')){const card=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');previews.push(card.desc);assert(card.apply(p)!==false,'quantity cap card rejected');assert(previews.length<21,'quantity cap infinite');}
  assert(M.profile(p,fire).fronts===12,'new firefront cap differs');const e=A.spawn(200,0),hits=A.watch(e);fire.t=0;cast(fire);advance(2.5);
  assert(hits.length>=12,'quantity fronts were preview-only instead of true contact');return {quantity,upgrades,capFronts:12,realHits:hits.length,profile:M.profile(p,fire)};
 });
 check('native-restart-clears-all-channels',()=>{
  const army=setup('naruto-madara-clones',3),basic=add('naruto-madara'),guard=add('naruto-madara-susanoo',3),fire=add('naruto-madara-fire',3),meteor=add('naruto-madara-meteor',3),e=A.spawn(40,0);A.spawn(100,0);
  cast(army);advance(.7);guard.t=0;cast(guard);fire.t=0;cast(fire);advance(.8);meteor.t=0;cast(meteor);advance(.5);
  const before=M.stateFor(p),hp=e.hp;assert(before.army.length&&before.guardian&&before.meteors.length,'restart fixture missing parallel channels');
  G.Game.startRun();A.pause();const current=A.p();assert(current!==p&&current.level===1&&current.moves.length===1,'native restart changed starter contract');
  assert(!M.stateFor(p),'old multi-channel state survived restart');advance(4);assert(e.hp===hp,'previous run source damaged after restart');return {newLevel:current.level,newSkills:current.moves.map(m=>m.id)};
 });
 }finally{G.CombatPulse.onPulse=previousPulse}
 return out;
}"""


RETREAT = r"""() => {
 const A=JAcceptance,p=A.p(),M=G.NarutoMadara;A.reset();const m=A.fixture('naruto-madara');A.spawn(-35,0);
 const start={x:p.x,y:p.y};A.resume();try{A.assert(M.cast(p,m),'retreat fixture cast failed')}finally{A.pause()}
 const xs=[];for(let i=0;i<70;i++){A.resume();try{p.update(.01);G.Combat.updateFields(.01)}finally{A.pause()}xs.push(p.x)}
 A.assert(xs.every((x,i)=>x>=(i?xs[i-1]:start.x)-1e-8)&&p.x>start.x+10,'automatic chase overrode rightward retreat');
 return {start,end:{x:p.x,y:p.y},minimumX:Math.min(...xs),scope:'real KeyD held; native player.update and skill simulation'};
}"""


def retreat_input(page, frame):
    if frame != page.main_frame:
        page.locator('iframe').first.focus()
    page.keyboard.down('KeyD')
    try:
        return frame.evaluate(RETREAT)
    finally:
        page.keyboard.up('KeyD')


def presentation(page, frame, label):
    """Actual RAF phase images; controlled stationary enemies, not natural growth."""
    result = {}
    frame.evaluate('window.MadaraPhotoSpawner=G.Spawner.update;G.Spawner.update=()=>{}')

    def until(target):
        frame.evaluate('JAcceptance.resume()')
        frame.wait_for_function('t=>(G.NarutoMadara.stateFor(G.Game.player)?.clock||0)>=t', arg=target, polling=10, timeout=15000)
        frame.evaluate('JAcceptance.pause()')

    try:
        scenes = [('body', 2, 0), ('fire', 3, 1), ('rib', 1, 0), ('armored', 2, 0), ('perfect', 3, 1), ('meteor', 3, 1), ('army', 3, 1)]
        for scene, rank, quantity in scenes:
            config = frame.evaluate(r"""({scene,rank,quantity})=>{
             const A=JAcceptance,M=G.NarutoMadara;A.reset();const p=A.p(),id=scene==='body'?'naruto-madara':scene==='fire'?'naruto-madara-fire':['rib','armored','perfect'].includes(scene)?'naruto-madara-susanoo':scene==='meteor'?'naruto-madara-meteor':'naruto-madara-clones';
             const m=A.fixture(id,rank);p.quantityPicks=p.quantityBonus=quantity;
             if(scene==='perfect'){A.assert(p.addMove('naruto-madara-fire'),'photo learn fire');const fire=p.moves.find(m=>m.id==='naruto-madara-fire');Object.assign(fire,G.Moves.instance(fire.id,3));}
             if(scene==='army')for(const id of ['naruto-madara','naruto-madara-fire','naruto-madara-susanoo']){A.assert(p.addMove(id),'photo army support '+id);const move=p.moves.find(m=>m.id===id);Object.assign(move,G.Moves.instance(id,3));}
             const positions=scene==='body'?[[35,0],[20,30]]:scene==='meteor'?[[100,0],[140,40],[160,-40]]:[[100,0],[180,35],[300,-50]];
             for(const [x,y]of positions)A.spawn(x,y);
             A.resume();try{A.assert(M.cast(p,m),'photo source cast rejected '+scene)}finally{A.pause()}
             for(const move of p.moves)move.t=999;return {id,profile:M.profile(p,m),clock:M.stateFor(p).clock};
            }""", {'scene': scene, 'rank': rank, 'quantity': quantity})
            if scene == 'perfect':
                for index in range(3):
                    start = frame.evaluate(r"""()=>{const p=G.Game.player,m=p.moves.find(m=>m.id==='naruto-madara-fire');m.t=0;JAcceptance.resume();try{JAcceptance.assert(G.NarutoMadara.cast(p,m),'earned photo fire rejected')}finally{JAcceptance.pause()}m.t=999;return G.NarutoMadara.stateFor(p).clock;}""")
                    if index < 2:
                        until(start + .95)
                    else:
                        frame.evaluate('JAcceptance.resume()')
                        frame.wait_for_function('G.NarutoMadara.stateFor(G.Game.player)?.guardian?.perfect', polling=10, timeout=15000)
                        frame.evaluate('JAcceptance.pause()')
                origin = frame.evaluate('(()=>{const s=G.NarutoMadara.stateFor(G.Game.player);return s.clock-s.guardian.age})()')
            else:
                origin = config['clock']
            if scene == 'body':
                phases = [(.04, 'windup'), (.15, 'palm'), (.26, 'elbow'), (.37, 'kick'), (.47, 'landing'), (.58, 'recovery'), (.74, 'settled')]
            elif scene == 'fire':
                phases = [(.15, 'seal'), (.35, 'mouth-near'), (.65, 'front-advance'), (1.1, 'far-front'), (2.4, 'tail')]
            elif scene in ['rib', 'armored', 'perfect']:
                slashes = config['profile']['slashes']
                second = .4 + 5.1 / slashes + .14
                last = .4 + (slashes - 1) * 5.1 / slashes + .14
                phases = [(.12, 'manifest'), (.43, 'draw'), (.54, 'contact'), (.76, 'recover'), (second, 'second-contact')]
                if scene == 'perfect':
                    phases.append((.4 + 2 * 5.1 / slashes + .28 + .18, 'pressure-flight'))
                phases.extend([(last, 'last-contact'), (5.85, 'fade'), (6.35, 'fade-end')])
            elif scene == 'meteor':
                phases = [(.7, 'warnings'), (1.24, 'first-fall'), (1.48, 'first-impact'), (2.08, 'second-fall'), (2.34, 'second-shatter'), (2.62, 'fragment-flight'), (3.7, 'fragment-landings')]
            else:
                phases = [(.5, 'wood-emerge'), (1.15, 'reveal'), (2.6, 'role-attack'), (6.6, 'role-relocate'), (13.2, 'dismiss')]
            stages = []
            for at, phase in phases:
                until(origin + at)
                page.wait_for_timeout(40)
                path = f'{label}-{scene}-rank{rank}-q{quantity}-{phase}.png'
                page.screenshot(path=str(OUT / path))
                state = frame.evaluate(r"""()=>{
                 const p=G.Game.player,M=G.NarutoMadara,s=M.stateFor(p);return {clock:s.clock,pose:M.pose(p),guardian:M.guardianPose(p),
                  camera:{x:G.Camera.x,y:G.Camera.y,scale:G.Camera.scale},impetus:s.impetus,perfectCount:s.perfectCount,
                  fronts:s.fires.map(f=>({x:f.x,y:f.y,distance:f.distance,aim:f.aim,width:f.currentWidth})),
                  rocks:s.meteors.map(r=>({x:r.x,y:r.y,phase:r.phase,second:!!r.second,fragment:!!r.fragment,sourceX:r.sourceX,sourceY:r.sourceY,height:r.height,flightProgress:r.flightProgress})),
                  army:s.army.map(a=>({serial:a.serial,role:a.role,x:a.x,y:a.y,phase:a.phase})),hits:M.stats(p).hitContacts.slice(-6)};
                }""")
                stages.append({'targetAge': at, 'phaseLabel': phase, 'path': path, **state})
            result[scene] = {'rank': rank, 'quantity': quantity, 'profile': config['profile'], 'stages': stages,
                             'fixture': 'controlled rank/quantity, stationary high-HP targets; native RAF/camera; native random spawns held; no natural growth claim'}
    finally:
        frame.evaluate('G.Spawner.update=window.MadaraPhotoSpawner;delete window.MadaraPhotoSpawner')
    return result


def write_gallery(report):
    sections = []
    for label, case in report['cases'].items():
        for scene, data in case.get('presentation', {}).items():
            figures = []
            for stage in data['stages']:
                path = html.escape(stage['path'], quote=True)
                caption = html.escape(f"{stage['phaseLabel']} · native clock {stage['clock']:.2f}")
                figures.append(f'<figure><a href="{path}"><img loading="lazy" src="{path}"></a><figcaption>{caption}</figcaption></figure>')
            sections.append(f'<h2>{html.escape(label)} / {html.escape(scene)} · rank {data["rank"]}, Q{data["quantity"]}</h2><div class="row">'+''.join(figures)+'</div>')
    if sections:
        (OUT / 'gallery.html').write_text('<!doctype html><meta charset="utf-8"><title>Madara rework native phase evidence</title>'
            '<style>body{background:#101927;color:#e5edf8;font:16px/1.5 system-ui;margin:20px}.row{display:flex;gap:12px;overflow:auto}figure{margin:0;flex:0 0 300px}img{width:300px}figcaption{font-size:12px}h2{margin-top:32px}</style>'
            '<h1>重製原生RAF相位</h1><p>受控階數／數量與靜態高HP敵人，隨機出生暫停；相機與技能由原生RAF推進。不是自然養成，也不是美術／動漫放行。點圖看原始尺寸；真相位與幾何見report.json。</p>'
            + ''.join(sections), encoding='utf8')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'scope': 'Madara version2 controlled geometry/lifecycle contracts; not natural growth or visual approval',
              'url': URL, 'sourceHashes': source_hashes(), 'cases': {}, 'errors': [], 'missing': [], 'failures': []}
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
                checks = [('progression', lambda: frame.evaluate(PROGRESSION)), ('starterGates', lambda: frame.evaluate(STARTER_GATES)),
                          ('inputAndBody', lambda: input_and_body(page, frame, context, mobile, label)),
                          ('retreat', lambda: retreat_input(page, frame)), ('mechanics', lambda: frame.evaluate(MECHANICS))]
                if os.environ.get('MADARA_PRESENTATION') == '1':
                    checks.append(('presentation', lambda: presentation(page, frame, label)))
                for name, check in checks:
                    try:
                        print(label, name, flush=True)
                        result[name] = check()
                        if isinstance(result[name], dict):
                            report['failures'].extend(label + ':' + name + ':' + failure for failure in result[name].get('failures', []))
                    except Exception as error:
                        report['failures'].append(label + ':' + name + ': ' + str(error))
                        page.screenshot(path=str(OUT / f'{label}-{name}-failure.png'))
            except Exception as error:
                report['failures'].append(label + ':boot: ' + str(error))
            finally:
                context.close()
                (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        browser.close()
    report['sourceHashesAfter'] = source_hashes()
    if report['sourceHashesAfter'] != report['sourceHashes']:
        report['failures'].append('runtime changed during controlled check; do not treat as frozen acceptance')
    report['ok'] = not (report['errors'] or report['missing'] or report['failures'])
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    write_gallery(report)
    print(json.dumps({'ok': report['ok'], 'failures': report['failures'], 'errors': report['errors'], 'evidence': str(OUT)}, ensure_ascii=True))
    if not report['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
