"""Bounded automatic Ryu cadence study; controlled trajectories, native combat.

This does not measure subjective fun, survival balance, native RAF or GPU cost.
Both rank recipes spend eleven legal learning/upgrade/stat cards. Clone variants
spend one additional legal self-clone card and exercise native clone updates.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('RYU_FEEL_OUT', ROOT / '.omx/state/jjk-feel/ryu'))
URL = os.environ.get('RYU_FEEL_URL', 'http://127.0.0.1:8341/.omx/digimon.html?lang=zh-TW')

CHECK = r"""({recipe,clone,encounter})=>{
 const A=JAcceptance,p=A.p(),R=G.JjkRyu,ids=['jjk-ryu','jjk-ryu-spread','jjk-ryu-impact','jjk-ryu-maximum'];
 A.reset();A.fixture(ids[0]);p.level=1;p.statsTaken={};
 const cards=[];
 for(let i=0;i<11;i++){
   p.level=i+2;
   const pool=G.JujutsuGrowth.legalOffers(p,100),learn=pool.find(c=>c.key.startsWith('new:')&&ids.includes(c.key.slice(4)));
   const ups=pool.filter(c=>c.key.startsWith('up:')&&ids.includes(c.key.slice(3))).sort((a,b)=>p.moves.find(m=>m.id===a.key.slice(3)).lvl-p.moves.find(m=>m.id===b.key.slice(3)).lvl);
   const choice=learn||(recipe==='rank3'?ups[0]:pool.find(c=>c.key==='stat:'+(i%2?'atk':'cd')));
   A.assert(choice&&choice.apply(p)!==false,'legal recipe failed '+i);cards.push(choice.key);
 }
 A.assert(p.moves.length===4,'missing skill');
 A.assert(p.moves.every(m=>m.lvl===(recipe==='rank3'?3:1)),'unexpected ranks '+p.moves.map(m=>m.lvl));
 if(clone){p.level++;const c=G.JujutsuGrowth.legalOffers(p,100).find(c=>c.key==='stat:selfClone');A.assert(c&&c.apply(p)!==false,'clone card failed');cards.push(c.key);}
 const enemies=[],offsets=encounter==='surrounding'?[[80,0],[130,50],[160,-65],[220,0],[235,40],[240,-40],[-70,130],[90,-150]]:[[220,0]];
 for(const [x,y] of offsets){const e=A.spawn(x,y,encounter==='moving-boss'?'boss':null);e.r=encounter==='moving-boss'?25:10;e.dmg=0;enemies.push(e);}
 const events=[],pulses=[],oldCast=G.Player.prototype.cast,oldPulse=G.CombatPulse.onPulse;
 let time=0;
 G.Player.prototype.cast=function(m,...args){
   if(ids.includes(m.id)){const s=R.stateFor(this),f=s?.action;if(f)events.push({time,id:m.id,clone:this!==p,castId:f.castId,x:f.x,y:f.y,aim:f.aim,
     cappedCore:m.id==='jjk-ryu'&&s.coreCharge>=3,maximumCooldown:this.moves.find(x=>x.id==='jjk-ryu-maximum')?.t||0});}
   return oldCast.call(this,m,...args);
 };
 G.CombatPulse.onPulse=function(info){if(ids.includes(info.moveId))pulses.push({time,id:info.moveId,clone:info.owner!==p,castId:info.castId,hits:info.primaryHits,damage:info.primaryDamage});oldPulse?.(info);};
 const wait={bodyReady:0,fullChargedCoreWaiting:0,fullChargedOwnCooldown:0,recovery:0,idleReady:0},dt=1/60,duration=60;
 const positions=[];
 for(const m of p.moves)m.t=0;
 try{
   for(let i=0;i<duration/dt;i++){
     time=i*dt;
     if(encounter!=='static'){
       p.x=30*Math.sin(time*1.8);p.y=40*Math.sin(time*1.3);
       for(let j=0;j<enemies.length;j++){
         const e=enemies[j],o=offsets[j];e.x=o[0]+35*Math.sin(time*.7+j);e.y=o[1]+(encounter==='moving-boss'?120:30)*Math.sin(time*1.2+j);
       }
       G.EnemyMgr.rebuildGrid();
     }
     const s=R.stateFor(p),core=p.moves.find(m=>m.id==='jjk-ryu'),max=p.moves.find(m=>m.id==='jjk-ryu-maximum');
     if(s){
       if(s.action&&p.moves.some(m=>m.t<=1e-8&&(m!==max||s.coreCharge>=3&&core.t<=1e-8)&&R.targetFor(p,m)))wait.bodyReady+=dt;
       if(s.coreCharge>=3&&core.t>1e-8)wait.fullChargedCoreWaiting+=dt;
       if(s.coreCharge>=3&&max.t>1e-8)wait.fullChargedOwnCooldown+=dt;
       if(s.recoveryUntil>s.clock)wait.recovery+=dt;
       if(!s.action&&s.recoveryUntil<=s.clock&&core.t<=1e-8)wait.idleReady+=dt;
     }
     A.step(dt,true);
     if(i%120===0)positions.push({time,x:p.x,y:p.y,enemyX:enemies[0].x,enemyY:enemies[0].y,charge:R.stateFor(p)?.coreCharge||0});
   }
 }finally{G.Player.prototype.cast=oldCast;G.CombatPulse.onPulse=oldPulse;}
 const summary={};
 for(const id of ids)for(const actor of ['player','clone']){
   const ev=events.filter(e=>e.id===id&&e.clone===(actor==='clone')),ps=pulses.filter(e=>e.id===id&&e.clone===(actor==='clone'));
   summary[id+':'+actor]={casts:ev.length,resolved:ev.filter(e=>ps.some(q=>q.castId===e.castId)).length,
     hitCasts:ev.filter(e=>ps.some(q=>q.castId===e.castId&&q.hits>0)).length,primaryHits:ps.reduce((n,q)=>n+q.hits,0),damage:ps.reduce((n,q)=>n+q.damage,0),
     times:ev.map(e=>+e.time.toFixed(3))};
 }
 return {recipe,clone,encounter,duration,cards,ranks:p.moves.map(m=>({id:m.id,lvl:m.lvl,cd:m.cd})),atk:p.atk,cdMul:p.cdMul,cloneCount:G.SelfClones.actors().length,wait,summary,events,pulses,positions};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base.OUT = OUT
    base.URL = URL
    source = ROOT / '.omx/jjk-ryu.js'
    report = {'url': URL, 'sourceHash': hashlib.sha256(source.read_bytes()).hexdigest(),
              'scope': '60 simulated seconds, prescribed moving positions, native automatic combat and clone update, no direct casts; not natural survival or RAF performance',
              'cases': [], 'errors': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
        for recipe in ['rank1', 'rank3']:
            for clone in [False, True]:
                for encounter in ['static', 'moving-boss', 'surrounding']:
                    context = browser.new_context(viewport={'width': 1280, 'height': 900}, service_workers='block')
                    page = context.new_page()
                    page.on('pageerror', lambda error: report['errors'].append(str(error)))
                    frame = base.boot(page, 30014, 'desktop')
                    case = frame.evaluate(CHECK, {'recipe': recipe, 'clone': clone, 'encounter': encounter})
                    report['cases'].append(case)
                    print(json.dumps({key: case[key] for key in ['recipe', 'clone', 'encounter', 'wait', 'summary']}), flush=True)
                    context.close()
        browser.close()
    report['sourceHashEnd'] = hashlib.sha256(source.read_bytes()).hexdigest()
    assert report['sourceHash'] == report['sourceHashEnd'], 'Ryu runtime changed during measurement'
    assert not report['errors'], report['errors']
    (OUT / 'cadence.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'cases': len(report['cases']), 'evidence': str(OUT / 'cadence.json')}))


if __name__ == '__main__':
    main()
