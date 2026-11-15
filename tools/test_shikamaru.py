"""Controlled acceptance for Shikamaru; not a substitute for natural play.

Exercises the production normal entry, owned damage, geometry and lifecycle.
"""
from __future__ import annotations
import json
import hashlib
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('SHIKAMARU_CHECK_OUT',ROOT/'art-review/shikamaru/qa/controlled'))
URL=os.environ.get('SHIKAMARU_URL','http://127.0.0.1:8348/.omx/digimon.html?lang=zh-TW&layout=wide')
DEX=30017

SETUP=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;
 A.assert(S,'missing production Shikamaru module');
 A.nativePath=G.World.projectilePathClear;
 A.reset=()=>{A.arena();G.SelfClones.clear();G.Pickups.clear();p.target=null;p.aim=0;p.xp=0;p.xpNext=1e12;p.quantityBonus=p.quantityPicks=0;p.percentHealthDamage=p.lifestealRate=p.critChance=p.damageSplashPicks=0;p.cdMul=1;p.item=null;G.World.propsInCircle=()=>[];G.World.projectilePathClear=()=>true;};
 A.spawn=(x,y,boss=false)=>{const e=new G.Enemy({dex:19,hp:1000000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];e.boss=boss;G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e};
 A.watch=e=>{const hits=[],hurt=e.hurt;e.hurt=function(...args){const hp=this.hp,result=hurt.apply(this,args);hits.push({raw:args[0],loss:hp-this.hp,owner:args[6]===p,id:args[7]});return result};return hits};
 A.fixture=(id,rank=1)=>{p.moves=[G.Moves.instance(id,rank)];const m=p.moves[0];A.assert(m&&m.digiMode,'move registration absent '+id);m.t=999;return m};
 A.step=(dt=.01)=>{A.resume();try{S.update(dt);p.anim.update(dt)}finally{A.pause()}};
 A.finish=(seconds=4)=>{for(let i=0;i<Math.ceil(seconds/.01);i++)A.step(.01)};
 A.cast=m=>{A.resume();try{A.assert(S.cast(p,m)!==false,'cast rejected '+m.id)}finally{A.pause()}};
 A.reset();
}"""

PROGRESSION=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,ids=['naruto-shikamaru','naruto-shikamaru-sewing','naruto-shikamaru-trap','naruto-shikamaru-strangle','naruto-shikamaru-tactics'];
 A.assert(p.level===1&&p.moves.length===1&&p.moves[0].id===ids[0],'fresh Lv1 starter mismatch');
 const initial=p.moves.map(m=>m.id),mon=p.mon,offers=[];
 for(const level of [1,2,3,4,5]){p.level=level;const cards=G.LevelUp.offer(p,100);for(const [id,gate]of [[ids[1],2],[ids[2],3],[ids[4],4],[ids[3],5]])A.assert(cards.some(c=>c.key==='new:'+id)===(level>=gate),'learn gate mismatch '+id+' Lv'+level);offers.push({level,keys:cards.map(c=>c.key)});}p.level=20;
 for(const id of ids.slice(1)){const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(card&&card.apply(p)!==false,'cannot learn actual card '+id)}
 A.assert(ids.every(id=>p.hasMove(id)),'incomplete legal skill registration');
 p.mon=G.DEX.find(m=>m.dex===30006);try{A.assert(!G.Moves.poolFor(p.mon).some(id=>ids.includes(id)),'Shikamaru pool leaked into Lee')}finally{p.mon=mon}
 const growth=[];for(const id of ids){A.reset();const m=A.fixture(id),before=S.profile(p,m);const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:quantity');if(card){A.assert(card.apply(p)!==false,'quantity application rejected');const after=S.profile(p,m);growth.push({id,before,after})}}
 A.reset();const shadow=A.fixture(ids[0]),tactics=G.Moves.instance(ids[4],1);p.moves.push(tactics);const first=S.profile(p,shadow),oldDamage=tactics.dmg,up=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+ids[4]);A.assert(up&&up.apply(p)!==false,'tactics real upgrade unavailable');const after=S.profile(p,shadow);A.assert(after.branches===first.branches+1&&Math.abs(after.bindDuration-first.bindDuration-.12)<1e-9,'tactics upgrade has no real consumer');A.assert(tactics.dmg===oldDamage&&tactics.dmg===0,'tactics advertised fake damage');return {initial,offers,growth,tactics:{first,after}};
}"""

GEOMETRY=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const id of ['naruto-shikamaru','naruto-shikamaru-sewing','naruto-shikamaru-trap']){
  A.reset();const m=A.fixture(id),near=A.spawn(80,0),middle=A.spawn(90,5),end=A.spawn(100,-5),outside=A.spawn(-600,600),nearHits=A.watch(near),otherHits=[A.watch(middle),A.watch(end)],outsideHits=A.watch(outside);p.target=near;A.cast(m);A.finish(4);
  A.assert(nearHits.some(h=>h.loss>0)&&otherHits.every(hits=>hits.some(h=>h.loss>0)),'three dispersed targets not damaged '+id);A.assert(!outsideHits.some(h=>h.loss>0),'out-of-range enemy damaged '+id);
  A.assert(nearHits.every(h=>h.owner&&h.id===id),'wrong damage attribution '+id);
  out.push({id,nearHits,otherHits,outsideHits});
 }
 // A wall must stop a launched ground shadow even if acquisition can see a target.
 A.reset();const m=A.fixture('naruto-shikamaru'),enemy=A.spawn(120,0),hits=A.watch(enemy);p.target=enemy;A.cast(m);G.World.projectilePathClear=()=>false;A.finish(3);
 A.assert(!hits.some(h=>h.loss>0),'shadow passed blocking wall');out.push({wall:true,hits});
 return out;
}"""

LIFECYCLE=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const reason of ['pause','clear','death','world']){
  A.reset();const m=A.fixture('naruto-shikamaru-sewing'),enemy=A.spawn(100,0),hits=A.watch(enemy);p.target=enemy;A.cast(m);
  if(reason==='pause'){const before=hits.length;S.update(3);A.assert(hits.length===before,'paused update dealt damage');out.push({reason,hits:before});continue}
  if(reason==='clear')S.clear(p);
  if(reason==='death')p.dead=true;
  const world=G.World;if(reason==='world')G.World={...world};
  try{A.finish(3)}finally{G.World=world;p.dead=false}
  A.assert(!hits.some(h=>h.loss>0),'cancelled action damaged enemy '+reason);out.push({reason,hits});
 }
 // First target's hurt callback cancels the action: later targets in the same
 // pulse and all future contacts must be cancelled, not just the next update.
 A.reset();const m=A.fixture('naruto-shikamaru-sewing',5);p.quantityBonus=p.quantityPicks=5;
 const first=A.spawn(90,-8),second=A.spawn(90,8),h1=A.watch(first),h2=A.watch(second);p.target=first;
 const hurt=first.hurt;first.hurt=function(...args){const result=hurt.apply(this,args);S.clear(p);return result};A.cast(m);A.finish(4);
 A.assert(h1.some(h=>h.loss>0),'cancel callback fixture never contacted first target');A.assert(!h2.some(h=>h.loss>0),'same-wave callback cancellation hit second target');
 out.push({callbackCancellation:true,first:h1,second:h2});return out;
}"""


GROWTH=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const mode of ['shadow','sewing','trap']){
  const id=mode==='shadow'?'naruto-shikamaru':'naruto-shikamaru-'+mode;
  const runs=[];
  for(const pick of [false,true]){A.reset();const m=A.fixture(id),before=S.profile(p,m);
   if(pick){const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:quantity');A.assert(card&&card.apply(p)!==false,'real first quantity unavailable '+id)}
   const spec=S.profile(p,m),targets=Array.from({length:3},(_,i)=>A.spawn(Math.cos(i*Math.PI*2/3)*120,Math.sin(i*Math.PI*2/3)*120)),hits=targets.map(A.watch);p.target=targets[0];A.cast(m);A.finish(3);
   runs.push({pick,before,spec,hits:hits.map(h=>h.length),damaged:hits.filter(h=>h.some(e=>e.loss>0)).length});
  }
  A.assert(runs[1].damaged>runs[0].damaged||runs[1].hits.reduce((a,b)=>a+b,0)>runs[0].hits.reduce((a,b)=>a+b,0),'first quantity has no real consumer '+id);out.push({mode,runs});
 }
 return out;
}"""



CONTROL=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru,out=[];
 for(const clone of [false,true])for(const boss of [false,true]){
  A.reset();const m=A.fixture('naruto-shikamaru'),actor=clone?G.SelfClones.summon(p):p;
  if(clone){actor.x=80;actor.y=0;}const e=A.spawn(actor.x,actor.y,boss);e.dmg=20;e.atkType='normal';p.target=e;
  const resolve=()=>{actor.invuln=0;e.touchCd=0;const hp=actor.hp;A.resume();try{G.Combat.resolve(.01,p,0)}finally{A.pause()}return hp-actor.hp};
  const before=resolve();A.assert(before>0,'baseline contact did not hurt '+clone+'/'+boss);
  A.cast(m);A.finish(.4);A.assert(S.held(e),'shadow did not bind contact fixture '+clone+'/'+boss);
  const during=resolve();A.assert(boss?during>0:during===0,'held contact contract failed '+clone+'/'+boss+' loss='+during);
  e.burn=1;e.burnT=1;e.burnTick=0;e.poison=1;e.poisonT=1;e.poisonTick=0;e.slow=.3;e.slowT=1;
  const hp=e.hp,xy=[e.x,e.y];A.resume();try{e.update(.1,p)}finally{A.pause()}
  A.assert(e.burnT<1&&e.poisonT<1&&e.slowT<1&&e.hp<hp,'bound enemy froze status clocks '+clone+'/'+boss);
  A.assert(Math.hypot(e.x-xy[0],e.y-xy[1])<1e-6,'bound enemy moved '+clone+'/'+boss);
  S.clear(p);const after=resolve();A.assert(after>0,'released contact did not resume '+clone+'/'+boss);
  out.push({clone,boss,before,during,after,statusDamage:hp-e.hp,burnT:e.burnT,poisonT:e.poisonT,slowT:e.slowT});
 }
 A.reset();const m=A.fixture('naruto-shikamaru'),enemy=A.spawn(100,0);p.target=enemy;
 const shot=G.Projectiles.spawn({x:40,y:0,vx:-100,vy:0,life:10,friendly:false,dmg:20,mtype:'normal'});
 A.cast(m);A.finish(.4);A.assert(S.held(enemy)&&G.Projectiles.all().includes(shot),'capture erased an in-flight hostile shot');
 p.invuln=0;const hp=p.hp;A.resume();try{G.Projectiles.update(.3,p,G.EnemyMgr.all());G.Combat.resolve(.01,p,0)}finally{A.pause()}
 A.assert(p.hp<hp,'held shooter disabled existing hostile projectile');out.push({inFlightProjectile:true,damage:hp-p.hp});
 return out;
}"""



STRANGLE=r"""() => {
 const A=Acceptance,p=A.p(),S=G.NarutoShikamaru;A.reset();const shadow=A.fixture('naruto-shikamaru'),bound=A.spawn(100,0);p.target=bound;A.cast(shadow);A.finish(.4);
 A.assert(S.held(bound),'strangle fixture failed to possess target');const unbound=A.spawn(100,70),bh=A.watch(bound),uh=A.watch(unbound),m=G.Moves.instance('naruto-shikamaru-strangle',1);p.moves.push(m);
 A.cast(m);A.finish(.27);A.assert(bh.some(h=>h.id===m.id&&h.loss>0),'strangle lacked independent bound-target contact');
 A.assert(!uh.some(h=>h.id===m.id&&h.loss>0),'strangle damaged unbound nearby enemy');
 const first=bh.filter(h=>h.id===m.id).length;A.finish(.5);const last=bh.filter(h=>h.id===m.id).length;
 A.assert(last>first,'strangle later pulses absent');S.clear(p);const cancelled=bh.length;A.finish(2);A.assert(bh.length===cancelled,'cancelled strangle continued contacts');
 return {first,last,bound:bh,unbound:uh};
}"""


def boot(page):
    page.goto(URL)
    page.wait_for_function('window.PS_REDRAWN_READY&&window.G?.NarutoShikamaru&&document.getElementById("boot").classList.contains("hidden")',polling=20)
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.locator(f'[data-quick-naruto="{DEX}"]').click()
    page.locator('#scr-menu [data-go="play"]').click()
    page.wait_for_function(f'G.Game.player?.dex==={DEX}&&G.Game.state==="playing"',polling=20)
    page.evaluate(HARNESS);page.evaluate(SETUP)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sources=['.omx/naruto-shikamaru.js','.omx/naruto-skills.js','js/entities/enemy.js','js/systems/combat.js','js/systems/self-clone.js','art-review/shikamaru-art.js','art-review/shikamaru-frames.json','art-review/shikamaru/atlas-v1.png','.omx/naruto.js','.omx/naruto-training.js','.omx/jujutsu-growth.js']
    hashes=lambda:{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources}
    report={'url':URL,'controlled':True,'sourceBefore':hashes(),'checks':{},'errors':[]}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=CHROME,headless=True)
            page=browser.new_page(viewport={'width':1100,'height':850},service_workers='block')
            page.on('pageerror',lambda e:report['errors'].append(str(e)))
            boot(page)
            for name,check in [('progression',PROGRESSION),('geometry',GEOMETRY),('lifecycle',LIFECYCLE),('growth',GROWTH),('control',CONTROL),('strangle',STRANGLE)]:
                report['checks'][name]=page.evaluate(check);print(name,'PASS',flush=True)
            page.screenshot(path=str(OUT/'controlled.png'));browser.close()
        assert not report['errors'],report['errors'];report['ok']=True
    except Exception as error:
        report['failure']=str(error);raise
    finally:
        report['sourceAfter']=hashes();report['sourceStable']=report['sourceAfter']==report['sourceBefore']
        (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':main()
