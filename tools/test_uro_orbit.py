"""Verify captured enemy bullets complete an owner-following orbit before return."""
from __future__ import annotations
import json
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('URO_ORBIT_OUT',ROOT/'.omx/state/uro-orbit/combat'))

CHECK=r"""() => {
 const A=JAcceptance,p=A.p(),U=G.JjkUro,assert=A.assert,out={};
 const returns=()=>G.Projectiles.all().filter(s=>s.uroReturned);
 const orbits=()=>U.orbits||U.stateFor(p)?.orbits||U.effects.filter(s=>s.mode==='uro-orbit');
 const update=dt=>{A.resume();try{U.update(dt)}finally{A.pause()}};
 function setup(){
  A.reset();p.statsTaken={};const m=A.fixture('jjk-uro-screen',1);
  const source=A.spawn(320,0),shot=G.Projectiles.spawn({x:80,y:0,px:170,py:0,vx:-240,vy:0,r:6,life:3,dmg:7,mtype:'fire',friendly:false,sourceEnemy:source});
  A.resume();try{assert(U.cast(p,m),'screen cannot cast');U.intercept()}finally{A.pause()}
  assert(!G.Projectiles.all().includes(shot),'captured hostile bullet still native');
  assert(returns().length===0,'return launched before orbit');
  assert(orbits().length===1,'one capture did not create one orbit');
  return {m,source,orbit:orbits()[0],screen:U.stateFor(p).screen};
 }
 function position(o){return [o.x-p.x,o.y-p.y]}
 for(const quality of ['high','low']){
  G.JujutsuVFX.setQuality(quality);const {m,source,orbit,screen}=setup(),start=position(orbit),angles=[],distances=[];
  let last=Math.atan2(start[1],start[0]),turn=0,elapsed=0;
  // Only update the field clock here: no collision or enemy update can hide an early return.
  for(let i=0;i<300&&!returns().length;i++){
   update(.005);elapsed+=.005;
   const [x,y]=position(orbit),a=Math.atan2(y,x);
   turn+=Math.atan2(Math.sin(a-last),Math.cos(a-last));last=a;
   angles.push(turn);distances.push(Math.hypot(x,y));
   if(!returns().length)assert(orbits().includes(orbit),'orbit disappeared before native return');
  }
  assert(returns().length===1,'orbit never launched one return');
  assert(Math.abs(turn)>=Math.PI*2-.12,'bullet returned before a complete revolution: '+turn);
  assert(elapsed>=.4&&elapsed<=1.5,'orbit is too brief to read or stalls: '+elapsed);
  const returned=returns()[0];assert(returned.friendly&&returned.owner===p&&returned.mid===m.id&&returned.mtype==='fire','return attribution/type lost');
  assert(returned.vx*(source.x-returned.x)+returned.vy*(source.y-returned.y)>0,'return points away from original source');
  const budget=screen.budget;A.resume();try{U.intercept();U.intercept()}finally{A.pause()}
  assert(returns().length===1&&orbits().length===0&&screen.budget===budget,'returned bullet was captured twice');
  assert(screen.initialBudget-screen.budget===1&&U.stateFor(p).intercepted===1&&U.stateFor(p).counterChains===1,'orbit spent repeated shield/counter budget');
  const hp=source.hp,hits=A.watch(source);A.advance(2);
  assert(source.hp<hp&&hits.some(h=>h.id===m.id&&h.owner&&h.raw===7*p.atk),'returned bullet did not really collide with source');
  out[quality]={elapsed,turn,minRadius:Math.min(...distances),maxRadius:Math.max(...distances),returnedDamage:7*p.atk};
 }
 let {orbit,screen}=setup();update(.15);let before=position(orbit);p.x+=140;p.y-=70;update(.005);let after=position(orbit);
 assert(Math.hypot(after[0]-before[0],after[1]-before[1])<20,'orbit did not follow moving owner');out.follow=true;
 for(const mode of ['pause','frozen']){
  ({orbit}=setup());update(.1);const before=[orbit.age,orbit.x,orbit.y];
  if(mode==='pause')U.update(2);else{p.frozen=true;update(2);p.frozen=false}
  assert(orbit.age===before[0]&&orbit.x===before[1]&&orbit.y===before[2]&&!returns().length,'orbit advanced during '+mode);
  update(1.5);assert(returns().length===1,'paused orbit failed to resume '+mode);out[mode]=true;
 }
 for(const mode of ['death','clear','unlearn','world','epoch']){
  ({orbit}=setup());update(.1);const world=G.World;
  if(mode==='death'){p.dead=true;p.hp=0}if(mode==='clear')G.Combat.clearFields(p);if(mode==='unlearn')p.moves=[];
  if(mode==='world')G.World=Object.create(world);if(mode==='epoch')G.CombatPulse.beginRun();
  try{update(2);assert(!orbits().includes(orbit)&&!returns().length,'invalid orbit leaked return '+mode)}finally{G.World=world;A.pause()}
  out[mode]=true;
 }
 ({orbit,screen}=setup());screen.budget=0;update(.01);assert(!U.stateFor(p).screen&&orbits().includes(orbit),'spent screen prematurely cancelled captured bullet');
 update(1.5);assert(returns().length===1,'capture lost after screen expired');out.screenSpent=true;
 ({orbit}=setup());const clone=G.SelfClones.summon(p);assert(clone,'clone missing');clone.x=600;clone.y=0;const cm=clone.moves.find(m=>m.id==='jjk-uro-screen');cm.t=0;
 G.Projectiles.spawn({x:680,y:0,px:770,py:0,vx:-240,vy:0,r:6,life:3,dmg:7,friendly:false});
 A.resume();try{assert(U.cast(clone,cm),'clone screen failed');U.intercept()}finally{A.pause()}
 assert(orbits().length===2&&orbits().some(o=>o.owner===clone),'clone orbit shared player state');U.clear(p);
 assert(orbits().length===1&&orbits()[0].owner===clone,'player clear removed clone capture');update(1.5);
 assert(returns().length===1&&returns()[0].owner===clone,'clone return lost owner attribution');out.clone=true;
 ({orbit}=setup());G.Game.toUI();U.update(2);assert(!orbits().length&&!returns().length,'terminal state leaked captured return');out.terminal=true;
 return out;
}"""

class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def main():
 OUT.mkdir(parents=True,exist_ok=True);base.OUT=OUT
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)))
 Thread(target=server.serve_forever,daemon=True).start();base.URL=f'http://127.0.0.1:{server.server_port}/.omx/digimon.html?lang=zh-TW'
 report={}
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=base.CHROME,headless=True)
   for mobile in [False,True]:
    label='mobile' if mobile else 'desktop';context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));frame=base.boot(page,30015,label)
    report[label]=frame.evaluate(CHECK);assert not errors,errors;context.close()
   browser.close()
  (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'ok':True,'views':list(report),'evidence':str(OUT)}))
 finally:server.shutdown();server.server_close()

if __name__=='__main__':main()
