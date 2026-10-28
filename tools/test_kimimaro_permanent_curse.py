"""Permanent in-run Kimimaro curse: native transformation, combat and cleanup."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault('KIMIMARO_OUT',str(Path(__file__).resolve().parents[1]/'.omx/state/kimimaro-permanent-curse'))
import test_kimimaro as native
from playwright.sync_api import sync_playwright


TRANSFORMATION = r"""() => {
 const A=KAcceptance,p=A.p(),K=A.K;A.reset();p.level=14;
 A.assert(!G.Moves.poolFor(p.mon).includes('naruto-kimimaro-curse')&&!p.addMove('naruto-kimimaro-curse'),'curse bypassed Lv15 gate');
 p.level=15;A.assert(p.addMove('naruto-kimimaro-curse'),'cannot learn curse at Lv15');
 const m=p.moves.find(m=>m.id==='naruto-kimimaro-curse');
 A.assert(m.passive&&m.cd===0&&m.fieldDuration===0&&!p.slots.length,'permanent curse retained active slot or duration/cooldown');
 for(const move of p.moves)move.t=999;
 const far=A.spawn(260,0);p.target=far;A.step(.01,true);
 A.assert(!K.curseState(p).active&&!A.action(),'curse activated without a nearby enemy');
 A.reset();A.fixture(m.id);const enemy=A.spawn(80,0);p.target=enemy;const speed=p.spd,hp=p.hp;
 A.cast(m.id);A.advance(.90);
 A.assert(K.curseState(p).transforming&&!K.curseState(p).active,'curse buff began before one second');
 A.near(p.spd,speed,'transforming curse gave early speed bonus');
 const before=JSON.stringify(K.curseState(p));G.Combat.updateFields(.4);
 A.assert(JSON.stringify(K.curseState(p))===before,'pause advanced transformation');
 A.advance(.12);const active=K.curseState(p);
 A.assert(active.active&&active.permanent&&!active.transforming&&active.remaining===0&&active.cooldown===0,'curse did not become permanent after transformation');
 A.assert(Object.values(active).filter(v=>typeof v==='number').every(Number.isFinite),'curse exposed a nonfinite timer');
 A.near(p.spd,speed*1.1,'curse speed bonus missing');A.near(p.hp,hp,'curse charged HP');
 A.assert(!K.canCast(p,p.moves.find(move=>move.id===m.id)),'permanent curse can be recast');
 return {gate:15,oneSecondTransformation:true,paused:true,active,speed:p.spd};
}"""

LONGEVITY = r"""() => {
 const A=KAcceptance,p=A.p(),K=A.K;A.reset();const m=A.fixture('naruto-kimimaro-curse',1),enemy=A.spawn(80,0);
 p.target=enemy;const baseSpeed=p.spd,baseAtk=p.atk,hp=p.hp;A.cast(m.id);A.advance(1.1);
 const started=K.curseState(p).startAt,checkpoints=[];
 for(const clock of [9.2,30.2,120.2]){
   A.advance(Math.max(0,clock-K.stateFor(p).clock),true);const state=K.curseState(p);
   A.assert(state.active&&state.permanent&&K.formFor(p)==='curse','curse returned to normal at '+clock);
   A.assert(state.startAt===started&&K.stateFor(p).castCounts.curse===1,'curse repeated transformation at '+clock);
   A.assert(state.remaining===0&&state.cooldown===0,'permanent curse retained countdown');
   A.near(p.spd,baseSpeed*1.1,'curse speed stacked at '+clock);A.near(p.atk,baseAtk,'curse mutated base attack');A.near(p.hp,hp,'curse charged HP');
   checkpoints.push({clock,casts:K.stateFor(p).castCounts.curse,state});
 }
 const bonuses=[];
 for(let rank=1;rank<=5;rank++){
   Object.assign(m,G.Moves.instance(m.id,rank));p.arrange();const state=K.curseState(p);
   A.near(state.bonus,[.10,.125,.15,.175,.20][rank-1],'rank upgrade did not update permanent bonus');
   A.assert(state.active&&state.startAt===started&&K.stateFor(p).castCounts.curse===1,'rank upgrade restarted transformation');
   A.near(p.spd,baseSpeed*1.1,'rank upgrade stacked movement speed');bonuses.push(state.bonus);
 }
 A.assert(p.addMove('naruto-kimimaro-flower'),'cannot learn post-evolution flower');
 const flower=p.moves.find(m=>m.id==='naruto-kimimaro-flower'),hits=A.watch(enemy);A.cast(flower.id);A.advance(.7);
 const expected=Math.round(flower.dmg*baseAtk*1.2*G.Types.mult(flower.type,enemy.types)*G.Weather.mult(flower.type));
 A.assert(hits.length===1&&hits[0].loss===expected,'long-lived curse damage applied more than once');
 return {checkpoints,bonuses,enhancedDamage:expected};
}"""

CLONES = r"""() => {
 const A=KAcceptance,p=A.p(),K=A.K;A.reset();A.fixture('naruto-kimimaro-curse',5);const enemy=A.spawn(90,0);p.target=enemy;
 const baseSpeed=p.spd;A.cast('naruto-kimimaro-curse');A.advance(1.1);
 const parentStart=K.curseState(p).startAt,clone=G.SelfClones.summon(p);A.assert(clone,'native clone summon failed');
 A.advance(.2);A.assert(K.curseState(clone).transforming&&!K.curseState(clone).active,'clone inherited completed parent transformation');
 A.near(clone.spd,baseSpeed,'clone inherited parent speed bonus before own transformation');
 A.advance(1.1);A.assert(K.curseState(clone).active&&K.curseState(clone).permanent,'clone did not transform permanently');
 A.near(clone.spd,baseSpeed*1.1,'clone doubled parent speed bonus');
 A.advance(121,true);
 A.assert(K.curseState(p).startAt===parentStart&&K.stateFor(p).castCounts.curse===1,'parent recast curse');
 A.assert(K.curseState(clone).active&&K.formFor(clone)==='curse'&&K.stateFor(clone).castCounts.curse===1,'clone reverted or transformed repeatedly');
 A.near(p.spd,baseSpeed*1.1,'parent speed stacked after clone transformation');A.near(clone.spd,baseSpeed*1.1,'clone permanent speed stacked');
 G.Combat.clearFields(p);A.assert(!K.stateFor(clone)&&!K.curseState(clone).active,'parent cleanup retained despawned clone evolution');
 A.assert(K.curseState(p).active,'same-run cleanup removed parent evolution');
 return {independentOnce:true,permanent:true,cleanup:true};
}"""

CLEAR_AND_RIFT = r"""() => {
 const A=KAcceptance,p=A.p(),K=A.K;A.reset();const curse=A.fixture('naruto-kimimaro-curse',5);
 p.target=A.spawn(80,0);const speed=p.spd;A.cast(curse.id);A.advance(1.1);const run=G.Game.st;
 const snapshots=[];
 for(const scope of ['owner','rift-scene','judgment-port']){
   if(scope==='owner')G.Combat.clearFields(p);else G.Combat.clearFields();
   A.assert(G.Game.st===run,'fixture unexpectedly changed the run');
   A.assert(K.stateFor(p)===null,'temporary action state survived '+scope);
   A.assert(K.curseState(p).active&&K.curseState(p).permanent&&K.formFor(p)==='curse','temporary cleanup removed evolution '+scope);
   A.near(p.spd,speed*1.1,'temporary cleanup removed evolution speed '+scope);
   A.assert(!K.canCast(p,curse),'temporary cleanup made permanent curse recastable '+scope);
   p.x+=30;p.y+=20;A.step(.01,true);A.advance(1.1,true);
   const state=K.stateFor(p);
   A.assert(K.curseState(p).active&&!K.curseState(p).transforming,'evolution replayed after '+scope);
   A.assert(!(state.castCounts.curse>0),'new temporary state cast curse again '+scope);
   snapshots.push({scope,active:K.curseState(p).active,recasts:state.castCounts.curse||0,speed:p.spd});
 }
 K.resetEvolution(p);A.assert(!K.curseState(p).active&&K.formFor(p)==='normal','explicit evolution reset retained permanent form');
 A.near(p.spd,speed,'explicit evolution reset retained speed');
 return {sameRun:true,snapshots,explicitReset:true};
}"""

CLEANUP = r"""() => {
 const A=KAcceptance,p=A.p(),K=A.K,out={};
 for(const reason of ['death','world','role']){
   A.reset();A.fixture('naruto-kimimaro-curse');p.target=A.spawn(80,0);const speed=p.spd;A.cast('naruto-kimimaro-curse');A.advance(1.1);
   A.assert(K.curseState(p).active,'cleanup fixture did not evolve');const oldWorld=G.World,oldMon=p.mon;
   if(reason==='death'){p.dead=true;p.hp=0}
   if(reason==='world')G.World={...G.World};
   if(reason==='role')p.mon=G.DEX_BY[30007];
   try{A.advance(.01);A.assert(!K.curseState(p).active&&K.formFor(p)==='normal'&&!K.stateFor(p),'permanent curse leaked through '+reason)}
   finally{G.World=oldWorld;p.mon=oldMon;p.dead=false;p.hp=p.maxHp}
   A.near(p.spd,speed,'cleanup retained curse speed '+reason);out[reason]=true;
 }
 return out;
}"""

HUD = r"""() => {
 const A=KAcceptance,p=A.p(),K=A.K;A.reset();A.fixture('naruto-kimimaro-curse');p.target=A.spawn(80,0);A.cast('naruto-kimimaro-curse');A.advance(31,true);
 const canvas=document.createElement('canvas');canvas.width=innerWidth;canvas.height=innerHeight;const ctx=canvas.getContext('2d'),labels=[];
 const fill=ctx.fillText.bind(ctx);ctx.fillText=function(label,...args){labels.push(String(label));return fill(label,...args)};
 G.HUD.draw(ctx,innerWidth,innerHeight,p,G.Game.st);
 A.assert(labels.some(s=>s.includes('咒印')&&s.includes('常駐'))&&!labels.some(s=>/咒印 .*s/.test(s)),'curse HUD retained a seconds countdown '+JSON.stringify(labels));
 return {permanentLabel:true,labels};
}"""


def main():
    native.OUT.mkdir(parents=True,exist_ok=True)
    selected=set(os.environ.get('KIMIMARO_PERMANENT_CURSE_CHECKS','').split(','))-{''}
    report={'url':native.URL,'errors':[],'failedRequests':[],'failures':[],'viewports':{},'sourceHashes':native.runtime_hashes()}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=native.CHROME,headless=True)
        for label,viewport,mobile in [('desktop',{'width':1280,'height':900},False),('mobile',{'width':390,'height':844},True)]:
            context=browser.new_context(viewport=viewport,is_mobile=mobile,has_touch=mobile,service_workers='block')
            page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
            page.on('response',lambda r:report['failedRequests'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            result=report['viewports'][label]={}
            try:
                frame=native.boot(page,label)
                for name,check in [('transformation',TRANSFORMATION),('longevity',LONGEVITY),('clones',CLONES),('sameRunClear',CLEAR_AND_RIFT),('cleanup',CLEANUP),('terminal',native.TERMINAL),('restart',native.RESTART),('hud',HUD)]:
                    if selected and name not in selected:continue
                    print(label,name,flush=True)
                    try:result[name]=frame.evaluate(check)
                    except Exception as error:report['failures'].append(label+':'+name+': '+str(error))
            except Exception as error:report['failures'].append(label+':boot: '+str(error))
            finally:context.close()
        browser.close()
    report['sourceHashesAfter']=native.runtime_hashes()
    if report['sourceHashesAfter']!=report['sourceHashes']:report['failures'].append('runtime changed during acceptance')
    report['ok']=not(report['errors'] or report['failedRequests'] or report['failures'])
    path=native.OUT/'report-permanent-curse.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'report':str(path)},ensure_ascii=True))
    if not report['ok']:raise SystemExit(1)


if __name__=='__main__':main()
