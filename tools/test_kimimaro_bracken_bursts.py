"""Native multi-burst Bracken timing, damage, rendering budgets and cleanup."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault('KIMIMARO_OUT',str(Path(__file__).resolve().parents[1]/'.omx/state/kimimaro-bracken-bursts'))
import test_kimimaro as game
from playwright.sync_api import sync_playwright


HELPERS = r"""() => {
 const A=KAcceptance,K=A.K,id='naruto-kimimaro-bracken';
 const p=()=>A.p();
 function prepare(rank=1){
   A.reset();const m=A.fixture(id,rank),owner=p();owner.baseAtk=1;owner.atkMul=1;owner.buffs.atk.n=0;owner.critChance=0;
   owner.quantityPicks=owner.quantityBonus=0;A.near(owner.atk,1,'controlled burst attack');return m;
 }
 function enemy(x,y=0,maxHp=10001,shield=1000000){
   const e=A.spawn(x,y);e.maxHp=maxHp;e.hp=maxHp;e.shield=shield;e.shieldT=100;return e;
 }
 function watch(e){
   const events=[],hurt=e.hurt;e.hurt=function(...args){
     const hp=this.hp,result=hurt.apply(this,args),s=K.stateFor(p()),f=K.activeFor(p());
     events.push({raw:args[0],loss:hp-this.hp,time:s?.clock,age:f?.age,owner:args[6]===p(),id:args[7]});return result;
   };return events;
 }
 function start(rank=1){
   const m=prepare(rank),near=enemy(40),far=enemy(m.radius-10,0,20003),nearHits=watch(near),farHits=watch(far);
   p().target=near;A.cast(id);const action=K.activeFor(p());A.assert(action?.kind==='bracken','native automatic Bracken cast missing');
   return {m,near,far,nearHits,farHits,action};
 }
 function columns(states=K.renderStates()){
   const canvas=document.createElement('canvas');canvas.width=1280;canvas.height=900;
   const ctx=canvas.getContext('2d'),draw=ctx.drawImage.bind(ctx),points=[];
   ctx.drawImage=(image,...args)=>{
     if((image.src||'').includes('kimimaro-effects-v1.png')){const t=ctx.getTransform();points.push({x:+t.e.toFixed(4),y:+t.f.toFixed(4)})}
     return draw(image,...args);
   };
   G.KimimaroArt.drawGround(ctx,states);G.KimimaroArt.drawAir(ctx,states);
   return {points,debug:{...G.KimimaroArt.debugLast}};
 }
 window.KBursts={...A,K,p,id,prepare,enemy,watch,start,columns};
}"""

RANK_TIMING_AND_DAMAGE = r"""() => {
 const A=KBursts,p=A.p,K=A.K,out=[];
 for(let rank=1;rank<=5;rank++){
   const {m,near,far,nearHits,farHits,action:f}=A.start(rank),origin={x:p().x,y:p().y},forests=[];
   A.assert(f.bursts.length===rank,'rank did not create the expected burst plans');
   A.near(f.duration,3.2+.5*(rank-1),'total burst action duration');
   f.bursts.forEach((burst,index)=>{
     A.near(burst.delay,index*.5,'authored burst delay');A.near(burst.startAt-f.clockStart,index*.5,'authored burst startAt');
     A.assert(JSON.stringify(burst.waves)===JSON.stringify([.48,.80,1.12,1.44,1.76,2.08]),'burst lost six authored expansion waves');
   });
   A.assert(K.movementLocked(p()),'initial ground press did not lock body');
   A.advance(.29,true);A.assert(K.movementLocked(p()),'ground press unlocked early');
   A.advance(.02,true);A.assert(!K.movementLocked(p()),'body remained locked after initial .3 seconds');
   p().x+=120;p().y-=70;p().walking=true;
   let age=.31;
   for(let index=0;index<rank;index++){
     if(index){A.advance(index*.5-.01-age,true);age=index*.5-.01;
       A.assert(f.burstLog.length===index&&f.bursts.filter(b=>b.started).length===index,'burst emitted before its half-second boundary');
       A.advance(.02,true);age+=.02;}
     A.assert(f.burstLog.length===index+1&&f.bursts.filter(b=>b.started).length===index+1,'burst did not emit at its half-second boundary');
     const active=K.stateFor(p()).forests;A.assert(active.length===index+1,'active forest list disagrees with burst emission');
     A.assert(K.stateFor(p()).forest===active[0],'legacy forest alias is not first active burst');
     const burst=f.bursts[index];forests.push(burst);
     A.near(burst.x,origin.x,'later burst followed moving owner x');A.near(burst.y,origin.y,'later burst followed moving owner y');
     A.near(f.burstLog[index].time-f.clockStart,index*.5,'actual burst emission interval');
   }
   A.assert(new Set(forests.map(b=>b.castId)).size===rank,'bursts reused their random seed/cast identity');
   A.assert(new Set(forests.map(b=>b.hitTargets)).size===rank,'bursts shared a victim-deduplication set');
   A.advance(f.duration+.05-age,true);
   A.assert(nearHits.length===rank&&farHits.length===rank,'each enemy did not receive exactly one hit per burst');
   for(let index=0;index<rank;index++){
     A.near(nearHits[index].raw,3001,'per-burst near max-HP floor was split');
     A.near(farHits[index].raw,6001,'per-burst far max-HP floor was split');
     A.assert(Math.abs(nearHits[index].age-(.48+index*.5))<.011,'near hit lost its burst-relative first wave');
     A.assert(Math.abs(farHits[index].age-(2.08+index*.5))<.011,'far hit lost its burst-relative last wave');
   }
   A.assert([...nearHits,...farHits].every(h=>h.owner&&h.id===A.id),'burst damage bypassed native technique ownership');
   A.assert(near.hp===10001&&far.hp===20003,'burst damage bypassed native shields');
   A.assert(!K.activeFor(p())&&K.stateFor(p()).forests.length===0,'completed burst sequence retained forests');
   A.assert(K.stateFor(p()).castCounts.bracken===1,'one burst sequence charged or counted as multiple casts');
   A.assert(Math.abs(m.t-(12-f.duration-.05))<.011,'later bursts reset the twelve-second cast cooldown');
   out.push({rank,burstLog:f.burstLog,castIds:forests.map(b=>b.castId),nearHits,farHits,remainingCooldown:m.t,unlockedMovement:true,originalCenter:origin});
 }
 return out;
}"""

ORIGINAL_TARGET_DEATH = r"""() => {
 const A=KBursts,p=A.p;A.prepare(5);const original=A.enemy(40,0,500,0),originalHits=A.watch(original);p().target=original;
 A.cast(A.id);const f=A.K.activeFor(p());A.advance(.60,true);
 A.assert(original.dead&&originalHits.length===1,'original target did not die in the first burst');
 A.assert(f.burstLog.length===2,'dead original target canceled the next scheduled burst');
 const late=A.enemy(40),lateHits=A.watch(late);A.advance(f.duration+.05-.60,true);
 A.assert(f.burstLog.length===5&&f.bursts.every(b=>b.started),'future bursts required the original target to remain alive');
 A.assert(lateHits.length===5&&lateHits.every(h=>h.raw===3001),'late enemy did not receive independent per-burst floor hits');
 return {originalHits:originalHits.length,originalDead:true,burstsAfterDeath:f.burstLog.length,lateHits:lateHits.length};
}"""

VISUAL_SEEDS_AND_STABILITY = r"""() => {
 const A=KBursts,{action:f}=A.start(5);A.advance(.99,true);
 const before=A.columns(),beforeSet=new Set(before.points.map(p=>p.x+':'+p.y));
 A.assert(beforeSet.size>0,'pre-burst renderer had no grown columns to compare');
 A.advance(.02,true);const after=A.columns(),afterSet=new Set(after.points.map(p=>p.x+':'+p.y));
 A.assert([...beforeSet].every(point=>afterSet.has(point)),'new burst resampled already-grown column positions');
 A.advance(4.7-1.01,true);const s=A.K.stateFor(A.p()),distributions=[];
 for(const forest of f.bursts){
   const copied={...s,forest,forests:[forest]},render=A.columns([copied]);
   const coords=[...new Set(render.points.map(p=>p.x+':'+p.y))].sort();
   A.assert(coords.length>0,'one emitted burst has no drawn bone columns');distributions.push({castId:forest.castId,coords});
 }
 A.assert(new Set(distributions.map(d=>JSON.stringify(d.coords))).size===5,'different burst seeds produced the same drawn column positions');
 const total=A.columns();A.assert(total.debug.forestColumns===72&&total.debug.secondaryParticles<=20,'five bursts multiplied the shared visual budget');
 return {stableColumnsAcrossThirdBurst:beforeSet.size,distributions,fullyGrownBudget:total.debug};
}"""

CLONE_BUDGET = r"""() => {
 const A=KBursts,p=A.p;A.prepare(5);const target=A.enemy(200,0,10001,10000000);p().target=target;
 const owners=[p(),...Array.from({length:3},()=>G.SelfClones.summon(p()))];A.assert(owners.every(Boolean),'native clone budget fixture missing actors');
 for(const owner of owners){owner.target=target;for(const m of owner.moves)m.t=999}
 A.advance(.11);
 A.resume();try{for(const owner of owners){const m=owner.moves.find(m=>m.id===A.id);m.t=0;A.assert(G.DigimonSkills.cast(owner,m),'native simultaneous burst cast failed')}}finally{A.pause()}
 A.advance(4.7);const states=A.K.renderStates(),forests=states.reduce((sum,s)=>sum+s.forests.length,0),render=A.columns();
 A.assert(states.length===4&&forests===20,'native clones did not produce independent five-burst sequences');
 A.assert(new Set(states.flatMap(s=>s.forests.map(f=>f.castId))).size===20,'clone bursts shared cast identities');
 A.assert(render.debug.forestColumns===72&&render.debug.secondaryParticles<=20,'four-owner burst sequences exceeded global bone/particle budget');
 G.Combat.clearFields(p());A.assert(A.K.renderStates().length===0&&!G.SelfClones.actors().length,'parent cleanup retained cloned burst sequences');
 return {owners:4,forests,globalBudget:render.debug,cleared:true};
}"""

FREEZE_AND_PAUSE = r"""() => {
 const A=KBursts,p=A.p,{action:f}=A.start(5);A.advance(.24,true);p().frozen=true;
 const frozen={age:f.age,clock:A.K.stateFor(p()).clock,emissions:f.burstLog.length};A.advance(1.3,true);
 A.near(f.age,frozen.age,'frozen owner advanced burst age');A.near(A.K.stateFor(p()).clock,frozen.clock,'frozen owner advanced burst clock');
 A.assert(f.burstLog.length===1,'frozen owner emitted a future burst');
 p().frozen=false;A.pause();G.Combat.updateFields(.9);
 A.near(f.age,frozen.age,'pause advanced scheduled bursts');A.assert(f.burstLog.length===1,'pause emitted future bursts');
 A.advance(.27,true);A.assert(f.burstLog.length===2&&f.bursts[1].started,'resume did not emit the next relative half-second burst');
 return {frozen,afterResumeAge:f.age,emissions:f.burstLog.length};
}"""

CLEANUP = r"""() => {
 const A=KBursts,p=A.p,K=A.K,out=[];
 for(const reason of ['clear','unlearn','death','world','quit','toUI']){
   const {action:f,nearHits,farHits}=A.start(5);A.advance(.20,true);const owner=p(),emissions=f.burstLog.length,originalWorld=G.World;
   if(reason==='clear')G.Combat.clearFields(owner);
   else if(reason==='unlearn'){owner.moves=owner.moves.filter(m=>m.id!==A.id);owner.arrange()}
   else if(reason==='death')owner.dead=true;
   else if(reason==='world')G.World={...originalWorld};
   else{A.resume();if(reason==='quit')G.Game.quit();else G.Game.toUI('menu')}
   try{
     if(reason==='quit'||reason==='toUI')K.update(3);else A.advance(3,true);
     A.assert(f.burstLog.length<=emissions,'abandoned sequence emitted a delayed burst after '+reason);
     A.assert(!K.activeFor(owner)&&!(K.stateFor(owner)?.forests.length),'abandoned sequence retained active forests after '+reason);
     A.assert(!nearHits.length&&!farHits.length,'abandoned future waves damaged victims after '+reason);
     out.push({reason,canceledBeforeFirstDamage:true,emissions:f.burstLog.length});
   }finally{
     if(reason==='world')G.World=originalWorld;if(reason==='death')owner.dead=false;
     if(reason==='quit'||reason==='toUI'){G.Game.startRun();A.pause()}
   }
 }
 return out;
}"""


def main():
    game.OUT.mkdir(parents=True,exist_ok=True)
    report={'url':game.URL,'errors':[],'failedRequests':[],'failures':[],'viewports':{},'sourceHashes':game.runtime_hashes()}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=game.CHROME,headless=True)
        for label,viewport,mobile in [('desktop',{'width':1280,'height':900},False),('mobile',{'width':390,'height':844},True)]:
            context=browser.new_context(viewport=viewport,is_mobile=mobile,has_touch=mobile,service_workers='block')
            page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
            page.on('response',lambda r:report['failedRequests'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            result=report['viewports'][label]={}
            try:
                frame=game.boot(page,label);frame.evaluate(HELPERS)
                for name,check in [('rankTimingAndDamage',RANK_TIMING_AND_DAMAGE),('originalTargetDeath',ORIGINAL_TARGET_DEATH),
                  ('visualSeedsAndStability',VISUAL_SEEDS_AND_STABILITY),('cloneBudget',CLONE_BUDGET),('freezeAndPause',FREEZE_AND_PAUSE),('cleanup',CLEANUP)]:
                    print(label,name,flush=True)
                    try:result[name]=frame.evaluate(check)
                    except Exception as error:report['failures'].append(label+':'+name+': '+str(error))
            except Exception as error:report['failures'].append(label+':boot: '+str(error))
            finally:context.close()
        browser.close()
    report['sourceHashesAfter']=game.runtime_hashes()
    if report['sourceHashesAfter']!=report['sourceHashes']:report['failures'].append('runtime changed during acceptance')
    report['ok']=not(report['errors'] or report['failedRequests'] or report['failures'])
    path=game.OUT/'report-bracken-bursts.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'report':str(path)},ensure_ascii=True))
    if not report['ok']:raise SystemExit(1)


if __name__=='__main__':main()
