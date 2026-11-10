"""Perfect Susanoo final slash contracts through the production menu.

Open-ground fixtures isolate attack geometry; native enemies, limb art, damage
callbacks and the public combat API remain in use. Requires localhost:8347.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import test_jujutsu as base
import test_madara_rework_play as native

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art-review/madara-final-slash-20261111/qa'
URL=os.environ.get('MADARA_FINAL_URL','http://127.0.0.1:8347/.omx/digimon.html?lang=zh-TW&layout=wide')

HELPERS=r'''() => {
 const A=JAcceptance,M=G.NarutoMadara,p=A.p(),assert=A.assert;
 function step(dt=.01){A.resume();try{p.anim.update(dt);M.update(dt)}finally{A.pause()}}
 function advance(seconds){for(let left=seconds;left>1e-8;){const dt=Math.min(.01,left);step(dt);left-=dt}}
 function until(predicate,seconds=12){for(let i=0;i<seconds*100&&!predicate();i++)step();assert(predicate(),'final phase wait expired')}
 function scene(perfect=true,rank=2){A.reset();p.atk=1;const m=A.fixture('naruto-madara-susanoo',rank),target=A.spawn(90,0);A.resume();try{assert(M.cast(p,m),'guardian cast rejected')}finally{A.pause()}const s=M.stateFor(p),g=s.guardian;assert(g&&!g.perfect,'ordinary guardian missing');if(perfect){assert(p.addMove('naruto-madara'),'learn body');const body=p.moves.find(m=>m.id==='naruto-madara');s.impetus=2;A.resume();try{assert(M.cast(p,body),'body cast rejected')}finally{A.pause()}until(()=>g.perfect,3);}assert(g.perfect===perfect,'guardian form wrong');return {m,s,g,target};}

 function charge(){const c=scene();until(()=>c.g.finisher&&c.g.phase==='draw');c.s.pressures.length=0;c.target.dead=true;c.target.hp=0;return c;}
 function point(radius,offset=0,aim=0){return [Math.cos(aim+offset)*radius,Math.sin(aim+offset)*radius]}
 window.FinalSlashTest={A,M,p,assert,step,advance,until,scene,charge,point};
}'''

CASES={
 'charge_and_expanded_duration':r'''() => {
 const T=FinalSlashTest,{A,M,assert}=T,{s,g}=T.charge(),start=g.age;
 assert(g.spec.finisherCharge===5,'charge too short');assert(g.duration>11,'perfect duration not expanded');
 const e=A.spawn(...T.point(760,0,g.aim)),events=A.watch(e);T.advance(4.9);assert(!s.pressures.some(f=>f.curved),'final wave emitted before charge');assert(events.length===0,'distant enemy damaged during charge');assert(!s.contacts.some(c=>c.channel==='guardian'&&c.segment===g.spec.slashes-1),'final blade contact occurred during charge');
 T.until(()=>s.pressures.some(f=>f.curved),7);const wave=s.pressures.find(f=>f.curved),releaseAge=g.age;assert(releaseAge-start>=5,'charge did not last five seconds');assert(wave.arcAngle>2&&wave.range>=1000,'final coverage too small');return {start,releaseAge,charge:releaseAge-start,duration:g.duration,arcAngle:wave.arcAngle,range:wave.range};
}''',
 'advancing_arc_hits_spread_once':r'''() => {
 const T=FinalSlashTest,{A,M,assert}=T,{s,g}=T.charge(),aim=g.aim;
 const targets=[T.point(760,-.65,aim),T.point(760,0,aim),T.point(760,.65,aim),T.point(760,1.6,aim),T.point(1450,0,aim)].map(v=>A.spawn(...v)),events=targets.map(A.watch);T.until(()=>s.pressures.some(f=>f.curved),7);const wave=s.pressures.find(f=>f.curved),atRelease=events.map(e=>e.length);assert(atRelease.every(x=>x===0),'wave hit distant targets instantly');
 T.advance(.3);assert(events.every(x=>x.length===0),'wave outran visible radius');T.advance(1.3);assert(events.slice(0,3).every(x=>x.length===1),'spread targets not hit exactly once '+events.map(x=>x.length));assert(events.slice(3).every(x=>x.length===0),'outside arc or range hit');assert(s.contacts.some(c=>c.channel==='guardian-pressure'&&c.geometry.kind==='arc'),'missing real arc geometry');assert(!s.pressures.some(f=>f.curved),'wave did not expire');return {counts:events.map(x=>x.length),damage:events.map(x=>x.reduce((n,e)=>n+e.loss,0)),castId:wave.cast.castId};
}''',
 'pause_and_skill_removal':r'''() => {
 const T=FinalSlashTest,{A,M,p,assert}=T,{s}=T.charge();T.until(()=>s.pressures.some(f=>f.curved),7);const wave=s.pressures.find(f=>f.curved),distance=wave.distance,clock=s.clock;M.update(.5);assert(wave.distance===distance&&s.clock===clock,'pause advanced slash');p.moves=p.moves.filter(m=>m.id!=='naruto-madara-susanoo');T.step();assert(!s.guardian&&!s.pressures.some(f=>f.curved),'unlearn retained slash');return {distance,pause:true,unlearn:true};
}''',
 'same_wave_callback_clear':r'''() => {
 const T=FinalSlashTest,{A,M,p,assert}=T,{s,g}=T.charge();T.until(()=>s.pressures.some(f=>f.curved),7);const wave=s.pressures.find(f=>f.curved),xy=T.point(760,0,wave.aim),one=A.spawn(...xy),two=A.spawn(...xy);let h1=0,h2=0;const hurt1=one.hurt,hurt2=two.hurt;one.hurt=function(...args){h1++;const r=hurt1.apply(this,args);G.Combat.clearFields(p);return r};two.hurt=function(...args){h2++;return hurt2.apply(this,args)};T.advance(2);assert(h1===1&&h2===0,'callback clear hit second target '+JSON.stringify({h1,h2}));assert(!M.stateFor(p),'clear retained state');return {h1,h2};
}''',
 'death_and_world_cancel':r'''() => {
 const T=FinalSlashTest,{A,M,p,assert}=T;let c=T.charge();T.until(()=>c.s.pressures.some(f=>f.curved),7);p.dead=true;T.step();assert(!M.stateFor(p),'death retained guardian');c=T.charge();const original=G.World;G.World={...original};try{T.step();assert(!M.stateFor(p),'world change retained guardian')}finally{G.World=original}return {death:true,world:true};
}''',
 'ordinary_guardian_excludes_finisher':r'''() => {
 const T=FinalSlashTest,{M,assert}=T,{s,g}=T.scene(false,2);let final=false,arc=false;for(let i=0;i<750;i++){T.step();final ||=!!g.finisher;arc ||=s.pressures.some(f=>f.curved);}assert(!final&&!arc,'ordinary guardian gained perfect finisher');assert(!s.guardian,'ordinary guardian extended');return {duration:g.duration,finisher:final,arc};
}''',
 'army_guardian_excludes_finisher':r'''() => {
 const T=FinalSlashTest,{A,M,p,assert}=T;A.reset();p.atk=1;const m=A.fixture('naruto-madara-clones',2);assert(p.addMove('naruto-madara'),'learn basic');assert(p.addMove('naruto-madara-susanoo'),'learn guardian');Object.assign(p.moves.find(m=>m.id==='naruto-madara-susanoo'),G.Moves.instance('naruto-madara-susanoo',2));A.spawn(90,0);A.spawn(-90,0);A.resume();try{assert(M.cast(p,m),'army summon')}finally{A.pause()}const s=M.stateFor(p);let observed=0,final=false,arc=false;for(let i=0;i<600;i++){T.step();for(const actor of s.army)if(actor.guardian){observed++;final ||=!!actor.guardian.finisher;assert(!actor.guardian.perfect,'army gained perfect form')}arc ||=s.pressures.some(f=>f.actor&&f.curved);}assert(observed>0,'army guardian never appeared');assert(!final&&!arc,'army gained final slash');return {observed,finisher:final,arc};
}''',
}

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 report={'scope':'Controlled real-enemy final-slash contracts, not natural growth or subjective visual approval','sourceSha256':hashlib.sha256((ROOT/'.omx/naruto-madara.js').read_bytes()).hexdigest(),'cases':{},'errors':[]}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=base.CHROME,headless=True);context=browser.new_context(viewport={'width':1280,'height':900},service_workers='block');page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));page.goto(URL);frame=native.frame_for(page);frame.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
  if frame.locator('#tap-start').is_visible():frame.locator('#tap-start').click()
  frame.locator('[data-quick-naruto="30016"]').click();frame.wait_for_function('G.NarutoAssets.ready(30016)');frame.locator('#scr-menu [data-go="play"]').click();frame.wait_for_function('G.Game.player?.dex===30016&&G.Game.state==="playing"');frame.evaluate(base.SETUP);frame.evaluate(HELPERS)
  for name,script in CASES.items():
   try:result=frame.evaluate(script);report['cases'][name]={'ok':True,'result':result};print(name,'PASS',flush=True)
   except Exception as exc:report['cases'][name]={'ok':False,'error':str(exc)};print(name,'FAIL',str(exc).splitlines()[0],flush=True)
  context.close();browser.close()
 report['ok']=all(c['ok'] for c in report['cases'].values()) and not report['errors'];(OUT/'mechanics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 if not report['ok']:raise SystemExit(1)

if __name__=='__main__':main()
