"""Native damage acceptance for Bracken's increased base and max-HP floor."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault('KIMIMARO_OUT',str(Path(__file__).resolve().parents[1]/'.omx/state/kimimaro-bracken-damage'))
import test_kimimaro as game
from playwright.sync_api import sync_playwright


HELPERS = r"""() => {
 const A=KAcceptance,p=A.p(),K=A.K,id='naruto-kimimaro-bracken';
 function prepare(rank=1,skill=id){
   A.reset();const m=A.fixture(skill,rank);p.baseAtk=1;p.atkMul=1;p.buffs.atk.n=0;p.critChance=0;
   A.near(p.atk,1,'controlled attack');A.near(G.Weather.mult(m.type),1,'controlled native weather');return m;
 }
 function enemy(maxHp=10001,special=null,current=maxHp,x=80,y=0){
   const e=A.spawn(x,y,special);e.maxHp=maxHp;e.hp=current;e.types=['normal'];return e;
 }
 // Isolate the first burst's complete hit before the next burst reaches this
 // near-origin fixture; the repeated-burst suite verifies the whole volley.
 function cast(e,skill=id,seconds=.90){
   p.target=e;const hp=e.hp,hits=A.watch(e);A.cast(skill);A.advance(seconds);
   return {hits,loss:hp-e.hp};
 }
 window.BDamage={...A,p,K,id,prepare,enemy,cast};
}"""

BASE_DAMAGE = r"""() => {
 const A=BDamage,out=[];
 for(let rank=1;rank<=5;rank++){
   const m=A.prepare(rank),base=[600,720,840,1020,1200][rank-1],e=A.enemy(1500);
   A.near(m.dmg,base,'increased base rank '+rank);A.near(m.minMaxHpFraction,.30,'max-HP floor metadata');
   const result=A.cast(e);
   A.assert(result.hits.length===1&&result.loss===base,'low-HP target did not use increased base rank '+rank);
   A.near(result.hits[0].raw,base,'native raw base damage');
   out.push({rank,base,loss:result.loss,hits:result.hits});
 }
 return out;
}"""

MAX_HP_FLOOR = r"""() => {
 const A=BDamage,out=[];
 for(const rank of [1,5])for(const special of [null,'elite','boss','judge']){
   A.prepare(rank);const e=A.enemy(10001,special),result=A.cast(e),floor=3001;
   A.assert(result.hits.length===1&&result.hits[0].raw===floor&&result.loss===floor,'max-HP floor reduced for '+special+' rank '+rank);
   out.push({rank,special:special||'ordinary',maxHp:10001,floor,loss:result.loss});
 }
 A.prepare();const wounded=A.enemy(10001,null,5000),result=A.cast(wounded);
 A.assert(result.loss===3001&&wounded.hp===1999,'floor was based on current HP rather than maximum HP');
 return {targets:out,wounded:{before:5000,maxHp:10001,loss:result.loss,after:wounded.hp}};
}"""

MODIFIERS = r"""() => {
 const A=BDamage,p=A.p,out=[];
 for(const type of ['grass','flying']){
   A.prepare();p.baseAtk=.01;const e=A.enemy(10001);e.types=[type];
   A.assert(G.Types.mult('ground',e.types)<1,'resistance fixture is not resistant');
   const result=A.cast(e);A.assert(result.loss===3001&&result.hits[0].raw===3001,'low attack or type resistance reduced the floor '+type);
   out.push({type,attack:p.atk,multiplier:G.Types.mult('ground',e.types),loss:result.loss});
 }
 A.prepare();p.baseAtk=20;const strong=A.enemy(30001),strongResult=A.cast(strong);
 A.assert(strongResult.hits[0].raw===12000&&strongResult.loss===12000,'floor capped a stronger normal hit');
 A.prepare();p.baseAtk=20;p.critChance=1;const crit=A.enemy(30001),critResult=A.cast(crit);
 A.assert(critResult.hits[0].raw===18000&&critResult.loss===18000,'critical multiplier was lost before floor comparison');
 A.prepare();p.baseAtk=20;const weak=A.enemy(30001);weak.types=['fire'];const weakResult=A.cast(weak);
 A.assert(weakResult.hits[0].raw===19200&&weakResult.loss===19200,'super-effective multiplier was lost before floor comparison');
 return {resisted:out,strong:strongResult,critical:critResult,superEffective:weakResult};
}"""

SHIELDS = r"""() => {
 const A=BDamage,out=[];
 for(const shield of [1000,4000]){
   A.prepare();const e=A.enemy(10001);e.shield=shield;e.shieldT=100;
   const result=A.cast(e),expectedLoss=shield<3001?3001-shield:0,expectedShield=Math.max(0,shield-3001);
   A.assert(result.hits.length===1&&result.hits[0].raw===3001,'shield altered or repeated the incoming floor hit');
   A.near(result.loss,expectedLoss,'native shield HP absorption');A.near(e.shield,expectedShield,'native shield capacity');
   out.push({initialShield:shield,shield:e.shield,hpLoss:result.loss,raw:result.hits[0].raw});
 }
 return out;
}"""

SIX_WAVES = r"""() => {
 const A=BDamage,p=A.p,m=A.prepare();
 const victims=Array.from({length:6},(_,i)=>A.enemy(10001,null,10001,(i+.75)*m.radius/6,0)),logs=victims.map(A.watch);
 p.target=victims[0];KAcceptance.cast(A.id);const waveTimes=[.48,.80,1.12,1.44,1.76,2.08];let age=0;
 for(let i=0;i<waveTimes.length;i++){
   A.advance(waveTimes[i]-.01-age);age=waveTimes[i]-.01;
   A.assert(logs[i].length===0,'floor damage arrived before wave '+i);
   A.advance(.02);age+=.02;
   A.assert(logs.slice(0,i+1).every(h=>h.length===1&&h[0].raw===3001),'wrong damage or hit count at wave '+i);
 }
 A.advance(3.4-age);A.assert(logs.every(h=>h.length===1),'later forest waves reapplied max-HP floor');
 return {waves:waveTimes,losses:victims.map(e=>10001-e.hp),hits:logs.map(h=>h.length)};
}"""

OTHER_SKILLS_AND_PROPS = r"""() => {
 const A=BDamage,p=A.p,out=[];
 // Fighting versus Normal is x1.6; native hurt rounds each separate hit.
 for(const [id,distance,expected] of [['naruto-kimimaro',50,48],['naruto-kimimaro-larch',50,154],
   ['naruto-kimimaro-flower',80,307],['naruto-kimimaro-bullets',190,45]]){
   A.prepare(1,id);const e=A.enemy(10001,null,10001,distance),result=A.cast(e,id,1.7);
   A.assert(result.loss===expected&&result.hits.every(h=>h.raw<3001),'max-HP floor leaked into '+id);
   out.push({id,loss:result.loss,hits:result.hits.length});
 }
 const props=[];
 for(const rank of [1,5]){
   A.prepare(rank);const prop={x:90,y:0,r:12,type:'chest',solid:true,destructible:true,hp:1000000,maxHp:1000000,tx:3,ty:0};
   G.World.propsInCircle=()=>[prop];const target=A.enemy(10001),result=A.cast(target);
   const expected=rank===1?600:1200;
   A.near(1000000-prop.hp,expected,'destructible prop inherited enemy max-HP floor');
   props.push({rank,maxHp:prop.maxHp,loss:1000000-prop.hp,enemyLoss:result.loss});
 }
 return {otherSkills:out,props};
}"""

CLONE_FLOOR = r"""() => {
 const A=BDamage,p=A.p,out=[];
 for(const special of [null,'boss']){
   A.prepare();const clone=G.SelfClones.summon(p);A.assert(clone,'native clone missing');
   for(const move of clone.moves)move.t=999;
   const copy=clone.moves.find(m=>m.id===A.id);copy.t=0;
   const e=A.enemy(10001,special,10001,clone.x+80,clone.y),hp=e.hp,events=[],hurt=e.hurt;
   e.hurt=function(...args){events.push({raw:args[0],ownerIsClone:args[6]===clone,id:args[7]});return hurt.apply(this,args)};
   clone.target=e;A.resume();try{G.Combat.tick(.001,clone,0)}finally{A.pause()}
   A.assert(A.K.activeFor(clone)?.kind==='bracken','clone did not use native automatic forest cast');
   A.advance(3.3);A.assert(events.length===1&&events[0].raw===3001&&events[0].ownerIsClone&&e.hp===hp-3001,'clone attack coefficient reduced max-HP floor '+special);
   A.assert(!(A.K.stateFor(p)?.castCounts.bracken),'parent auto cast contaminated clone fixture');
   out.push({special:special||'ordinary',cloneAttack:clone.atk,loss:hp-e.hp,events});
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
                for name,check in [('base',BASE_DAMAGE),('maxHpFloor',MAX_HP_FLOOR),('modifiers',MODIFIERS),('shields',SHIELDS),('sixWaves',SIX_WAVES),('otherSkillsAndProps',OTHER_SKILLS_AND_PROPS),('cloneFloor',CLONE_FLOOR)]:
                    print(label,name,flush=True)
                    try:result[name]=frame.evaluate(check)
                    except Exception as error:report['failures'].append(label+':'+name+': '+str(error))
            except Exception as error:report['failures'].append(label+':boot: '+str(error))
            finally:context.close()
        browser.close()
    report['sourceHashesAfter']=game.runtime_hashes()
    if report['sourceHashesAfter']!=report['sourceHashes']:report['failures'].append('runtime changed during acceptance')
    report['ok']=not(report['errors'] or report['failedRequests'] or report['failures'])
    path=game.OUT/'report-bracken-damage.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'report':str(path)},ensure_ascii=True))
    if not report['ok']:raise SystemExit(1)


if __name__=='__main__':main()
