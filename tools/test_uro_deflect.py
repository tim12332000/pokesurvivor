"""Source-owned sky deflections through the production damage/contact entry."""
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
OUT=Path(os.environ.get('URO_DEFLECT_OUT',ROOT/'.omx/state/uro-deflect'))

CHECK=r"""() => {
 const A=JAcceptance,p=A.p(),U=G.JjkUro,assert=A.assert,out={};
 function setup(rank=1,q=0){A.reset();p.statsTaken={};const m=A.fixture('jjk-uro-screen',rank);p.quantityPicks=p.quantityBonus=q;return m;}
 function contact(e,extra={}){return {cause:'contact',sourceEnemy:e,fromX:e.x,fromY:e.y,...extra};}
 function intercept(e,amount=10,pure=false,meta=contact(e)){
  A.resume();try{return U.deflectContact(p,amount,'normal',pure,meta)}finally{A.pause()}
 }
 let m=setup(),e=A.spawn(20,0);const hp=p.hp;
 assert(typeof U.deflectContact==='function','missing source-owned contact deflection');
 assert(intercept(e),'ready sky screen did not catch real melee contact');
 let s=U.stateFor(p),w=s.screen;
 assert(p.hp===hp&&p.invuln===0&&w.budget===w.initialBudget-1&&m.t>0,'deflection changed HP/invulnerability or failed budget/CD');
 assert(e.kx===0&&e.ky>0&&w.flashes.at(-1).kind==='contact','normal attacker was not visibly deflected sideways');
 assert(s.counterChains===1&&s.deflected===1&&U.effects.filter(b=>b.mode==='uro-counter').length===1,'first contact failed independent once-only counter');
 assert(!intercept(e)&&w.budget===w.initialBudget-1,'duplicate contact spent another capacity');
 A.resume();try{e.update(.05,p,0)}finally{A.pause()};assert(e.y>0,'deflection impulse did not change the attacker position');
 A.advance(.21);assert(e.hp<e.maxHp,'deflection did not create a real counterattack window');out.firstContact={budget:w.budget,counterChains:s.counterChains};
 // Invulnerability must never be granted to unrelated damage.
 p.invuln=0;A.resume();try{p.hurt(10,'normal',false,{cause:'hazard'})}finally{A.pause()}
 assert(p.hp<hp,'sky screen became a generic invulnerability circle');
 for(const kind of ['boss','elite','legend','judge']){
  setup();e=A.spawn(20,0,kind);const before=[e.x,e.y,e.kx,e.ky];assert(intercept(e),'strong contact not deflected '+kind);s=U.stateFor(p);w=s.screen;
  assert(w.budget===w.initialBudget-2&&[e.x,e.y,e.kx,e.ky].every((n,i)=>n===before[i]),'strong attacker moved or did not cost two '+kind);
  out[kind]={cost:2,moved:false};
 }
 for(const invalid of ['missing','unregistered','far','wall','friendly','dead-source','projectile','pure','zero','nan','paused','frozen','dead','invulnerable','unlearned','cooldown']){
  m=setup();e=A.spawn(20,0);let meta=contact(e),amount=10,pure=false;
  if(invalid==='missing')delete meta.sourceEnemy;
  if(invalid==='unregistered')G.EnemyMgr.removeRemote(e.id,false);
  if(invalid==='far')e.x=200;
  const path=G.World.projectilePathClear;if(invalid==='wall')G.World.projectilePathClear=()=>false;
  if(invalid==='friendly')e.friendly=true;if(invalid==='dead-source'){e.dead=true;e.hp=0}
  if(invalid==='projectile')meta.cause='projectile';if(invalid==='pure')pure=true;
  if(invalid==='zero')amount=0;if(invalid==='nan')amount=NaN;
  if(invalid==='frozen')p.frozen=true;if(invalid==='dead'){p.dead=true;p.hp=0}if(invalid==='invulnerable')p.invuln=1;
  if(invalid==='unlearned')p.moves=[];if(invalid==='cooldown')m.t=1;
  let result;try{result=invalid==='paused'?U.deflectContact(p,amount,'normal',pure,meta):intercept(e,amount,pure,meta)}finally{G.World.projectilePathClear=path}
  assert(!result&&!U.stateFor(p)?.screen,'invalid source/context created or spent screen '+invalid);out[invalid]=true;
 }
 for(const invalid of ['remove','kill','move','wall']){
  setup();e=A.spawn(20,0);const nativeCast=p.cast,path=G.World.projectilePathClear;
  p.cast=function(...args){const result=nativeCast.apply(this,args);
   if(invalid==='remove')G.EnemyMgr.removeRemote(e.id,false);
   if(invalid==='kill'){e.dead=true;e.hp=0}if(invalid==='move')e.x=600;
   if(invalid==='wall')G.World.projectilePathClear=()=>false;return result;
  };
  let caught;try{caught=intercept(e)}finally{p.cast=nativeCast;G.World.projectilePathClear=path}
  s=U.stateFor(p);w=s?.screen;
  assert(!caught&&w&&w.budget===w.initialBudget&&s.deflected===0&&s.counterChains===0&&(e.ky||0)===0&&!w.flashes.length,
   'cast callback invalidated source but deflection consumed capacity/moved it '+invalid);out['castCallback-'+invalid]=true;
 }
 // Actual contact resolution provides the source and consumes its attack CD.
 setup();e=A.spawn(20,0);e.dmg=10;const nativeHp=p.hp;A.resume();try{G.Combat.resolve(.01,p,0)}finally{A.pause()}
 assert(p.hp===nativeHp&&e.touchCd>0&&U.stateFor(p)?.deflected===1,'native contact did not supply/catch the real source');out.nativeContact=true;
 setup();e=A.spawn(20,0);e.dmg=10;m=p.moves[0];m.t=1;A.resume();try{G.Combat.resolve(.01,p,0)}finally{A.pause()}
 assert(p.hp<nativeHp&&!U.stateFor(p)?.screen,'cooldown contact silently became immune');out.cooldownDamage=true;
 setup();e=A.spawn(20,0);e.dmg=10;p.moves=[];A.resume();try{G.Combat.resolve(.01,p,0)}finally{A.pause()}
 assert(p.hp<nativeHp&&!U.stateFor(p)?.screen,'removing screen did not restore actual contact damage');out.withoutSkillDamage=true;
 for(const [rank,q,budget] of [[1,0,12],[1,1,15],[5,0,28]]){
  setup(rank,q);e=A.spawn(20,0);assert(intercept(e),'growth contact failed');w=U.stateFor(p).screen;
  assert(w.initialBudget===budget&&w.budget===budget-1,'melee capacity did not share real screen/quantity growth');out['capacity-'+rank+'-'+q]=budget;
 }
 // Enemy bullets and melee contacts share one first-interception reward.
 for(const order of ['melee-first','projectile-first']){
  setup();e=A.spawn(20,0);const shooter=A.spawn(300,0);
  function shot(){G.Projectiles.spawn({x:80,y:0,px:170,py:0,vx:-200,vy:0,r:6,life:3,dmg:7,friendly:false,sourceEnemy:shooter});A.resume();try{U.intercept()}finally{A.pause()}}
  if(order==='melee-first'){assert(intercept(e),'first melee');shot()}else{
   G.Projectiles.spawn({x:180,y:0,vx:-200,vy:0,r:6,life:3,dmg:7,friendly:false});A.resume();try{assert(U.cast(p,p.moves[0]),'cast projectile screen')}finally{A.pause()};G.Projectiles.clear();shot();assert(intercept(e),'melee after projectile');
  }
  s=U.stateFor(p);assert(s.counterChains===1&&s.intercepted===1&&s.deflected===1,'first-chain reward duplicated '+order);out[order]=true;
 }
 setup();e=A.spawn(20,0);assert(intercept(e),'capacity setup');s=U.stateFor(p);w=s.screen;w.budget=1;
 const strong=A.spawn(-20,0,'boss');assert(!intercept(strong)&&w.budget===1,'insufficient capacity caught strong hit');
 const normal=A.spawn(0,20);assert(intercept(normal)&&w.budget===0,'last capacity did not catch one normal hit');
 const extra=A.spawn(0,-20);assert(!intercept(extra)&&w.budget===0,'empty screen caught another hit');out.capacity=true;
 for(const invalid of ['clear','unlearn','world','epoch','expiry']){
  setup();e=A.spawn(20,0);assert(intercept(e),'lifecycle setup');const world=G.World;
  if(invalid==='clear')U.clear(p);if(invalid==='unlearn')p.moves=[];if(invalid==='world')G.World=Object.create(world);
  if(invalid==='epoch')G.CombatPulse.beginRun();if(invalid==='expiry')A.advance(4);
  try{assert(!intercept(A.spawn(-20,0)),'invalid screen caught contact '+invalid)}finally{G.World=world}
  out[invalid]=true;
 }
 setup();e=A.spawn(20,0);const clone=G.SelfClones.summon(p);assert(clone,'clone absent');clone.x=200;clone.y=0;clone.invuln=0;
 const cloneEnemy=A.spawn(220,0),cloneHp=clone.hp;A.resume();try{clone.hurt(10,'normal',false,contact(cloneEnemy))}finally{A.pause()}
 assert(clone.hp===cloneHp&&U.stateFor(clone)?.deflected===1&&!U.stateFor(p)?.screen,'clone contact shared owner screen');out.clone=true;
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
