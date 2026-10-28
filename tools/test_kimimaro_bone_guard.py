"""Native hostile-projectile acceptance for Kimimaro's slotless bone wall."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault('KIMIMARO_OUT', str(Path(__file__).resolve().parents[1]/'.omx/state/kimimaro-bone-guard'))
import test_kimimaro as game
from playwright.sync_api import sync_playwright


SETUP = r"""() => {
 const A=KAcceptance,p=A.p,K=A.K,id='naruto-kimimaro-bone-guard';
 function prepare(rank=1){A.reset();const m=A.fixture(id,rank);p().invuln=0;return m}
 function shot(x=120,y=0,vx=-500,vy=0,extra={}){
   return G.Projectiles.spawn({x:p().x+x,y:p().y+y,vx,vy,r:5,dmg:30,mtype:'normal',friendly:false,life:4,...extra});
 }
 function exists(projectile){return G.Projectiles.all().includes(projectile)}
 function state(actor=p()){return K.boneGuardState(actor)}
 window.BGuard={A,p,K,id,prepare,shot,exists,state};
}"""

PROGRESSION = r"""() => {
 const B=BGuard,{A,p,id}=B;A.reset();p().moves=[];p().slots=[];
 p().level=5;A.assert(!G.Moves.poolFor(p().mon).includes(id)&&!p().addMove(id),'bone guard learned before Lv6');
 p().level=6;A.assert(G.Moves.poolFor(p().mon).includes(id),'Lv6 pool omitted bone guard');
 A.assert(G.LevelUp.offer(p(),100).some(c=>c.key==='new:'+id),'Lv6 learn choice omitted bone guard');
 A.assert(p().addMove(id),'cannot learn bone guard at Lv6');
 A.assert(p().moves.find(m=>m.id===id).passive&&p().slots.length===0,'bone guard consumed active slot');
 const cooldowns=[];for(let rank=1;rank<=5;rank++){
   const m=G.Moves.instance(id,rank);A.near(m.cd,[5,4.5,4,3.5,3][rank-1],'rank cooldown '+rank);cooldowns.push(m.cd);
 }
 return {learnLevel:6,slotless:true,cooldowns};
}"""

INTERCEPT = r"""() => {
 const B=BGuard,{A,p}=B,out=[];
 for(const [name,x,y,vx,vy,dt] of [
   ['front',120,0,-500,0,.10],['back',-120,0,500,0,.10],
   ['top',0,-120,0,500,.10],['bottom',0,120,0,-500,.10],
   ['diagonal',100,100,-500,-500,.10],['fast-crossing',120,0,-2000,0,.10]]){
   B.prepare();const hp=p().hp,q=B.shot(x,y,vx,vy);A.step(dt);A.advance(.25);
   A.assert(!B.exists(q),'threat not intercepted '+name);A.near(p().hp,hp,'guard failed to protect '+name);
   const state=B.state();A.assert(state&&state.cooldown>0,'block did not start cooldown '+name);
   out.push({name,protected:true,state});
 }
 return out;
}"""

EXCLUSIONS = r"""() => {
 const B=BGuard,{A}=B,out=[];
 const cases=[['friendly',120,0,-500,0,{friendly:true}],['away',70,0,500,0,{}],
   ['near-miss',120,100,-500,0,{}],['unblockable',120,0,-500,0,{unblockable:true}],
   ['guardUnblockable',120,0,-500,0,{guardUnblockable:true}],
   ['uninterceptable',120,0,-500,0,{uninterceptable:true}],
   ['ground',120,0,-500,0,{ground:true}],['beam',120,0,-500,0,{beam:true}],
   ['laser',120,0,-500,0,{laser:true}],['orb',120,0,-500,0,{orb:true,oa:0,ospeed:0,orad:120}],
   ['hazard',120,0,-500,0,{hazard:true}],['far',180,0,-10,0,{}]];
 for(const [name,x,y,vx,vy,flags] of cases){
   B.prepare();const q=B.shot(x,y,vx,vy,flags);A.step(.10);
   A.assert(B.exists(q),'guard deleted excluded projectile '+name);
   const state=B.state();A.assert(!state?.cooldown,'guard spent cooldown on excluded projectile '+name);
   out.push(name);
 }
 return {ignored:out};
}"""

WALL_AND_COOLDOWN = r"""() => {
 const B=BGuard,{A,p}=B;B.prepare();const hp=p().hp,first=B.shot();A.step(.10);A.advance(.12);
 A.assert(!B.exists(first),'first shot not blocked');
 const second=B.shot(90,0,-600,0);A.step(.10);A.advance(.04);
 A.assert(!B.exists(second)&&p().hp===hp,'active wall failed to block a second same-direction shot');
 const blocks=B.state().blocks,fastRear=B.shot(-120,0,2000,0);A.step(.10);
 A.assert(B.exists(fastRear)&&B.state().blocks===blocks,'wall blocked a backside projectile after it had crossed the owner');G.Projectiles.remove(fastRear);
 const rear=B.shot(-60,0,600,0);A.step(.10);
 A.assert(p().hp<hp&&!B.exists(rear),'short directional wall became a full invulnerability bubble');
 A.advance(.65);p().invuln=0;const before=p().hp,late=B.shot(60,0,-600,0);A.step(.10);
 A.assert(p().hp<before&&!B.exists(late),'cooldown did not allow later projectile damage');
 return {sameDirectionVolley:true,backsideStillDangerous:true,cooldownDamage:before-p().hp};
}"""

CLONES = r"""() => {
 const B=BGuard,{A,p}=B;B.prepare();const clone=G.SelfClones.summon(p());
 A.assert(clone,'native clone missing');clone.x=200;clone.y=120;
 const hp=clone.hp,hitCount=clone.hitsTaken,ownerHp=p().hp;
 const q=G.Projectiles.spawn({x:clone.x+120,y:clone.y,vx:-500,vy:0,friendly:false,r:5,dmg:30,mtype:'normal',life:4});
 A.step(.1);A.advance(.25);
 A.assert(!B.exists(q)&&clone.hp===hp&&clone.hitsTaken===hitCount,'clone guard failed before clone projectile damage');
 A.assert(B.state(clone)?.blocks>=1&&B.state(clone)?.cooldown>0,'clone has no independent guard state');
 A.assert(!B.state()?.cooldown,'clone guard consumed parent cooldown');
 const own=B.shot(-120,0,500,0);A.step(.1);A.advance(.25);
 A.assert(!B.exists(own)&&p().hp===ownerHp&&B.state()?.blocks>=1,'parent guard unavailable after clone defense');
 G.Combat.clearFields(p());A.assert(!B.state(clone),'parent cleanup retained clone guard');
 return {cloneProtected:true,parentIndependent:true,cleanup:true};
}"""

FIXED_COOLDOWN = r"""() => {
 const B=BGuard,{A,p}=B,out=[];
 for(let rank=1;rank<=5;rank++){
   B.prepare(rank);p().cdMul=.1;p().quantityPicks=12;
   B.shot(60,0,-600,0);A.step(.1);
   const state=B.state();A.assert(state?.triggers===1&&state.blocks===1,'rank guard did not activate '+rank);
   const cd=[5,4.5,4,3.5,3][rank-1];
   A.assert(state.cooldown>=cd-.100001&&state.cooldown<=cd,'guard cooldown changed with cooldown/quantity attributes '+rank);
   out.push({rank,cooldown:state.cooldown,triggers:state.triggers,blocks:state.blocks});
 }
 p().cdMul=1;p().quantityPicks=0;return out;
}"""

STATIONARY_AND_UNLEARN = r"""() => {
 const B=BGuard,{A,p,id}=B;B.prepare();B.shot();A.step(.1);A.advance(.15);
 const original=B.state(),wall=original.wall,anchor={x:wall.x,y:wall.y},blocks=original.blocks;
 p().x+=100;p().y+=100;p().walking=true;A.step(.05);
 A.near(B.state().wall.x,anchor.x,'wall followed owner horizontally');
 A.near(B.state().wall.y,anchor.y,'wall followed owner vertically');
 const atOldWall=G.Projectiles.spawn({x:anchor.x+80,y:anchor.y,vx:-500,vy:0,friendly:false,r:5,dmg:30,mtype:'normal',life:4});
 A.step(.18);A.assert(!B.exists(atOldWall)&&B.state().blocks===blocks+1,'stationary wall no longer blocks at its original position');
 B.prepare();B.shot();A.step(.1);A.advance(.15);
 p().moves=p().moves.filter(m=>m.id!==id);p().arrange();A.step(.01);
 A.assert(B.state()===null,'removed move retained guard state');
 const hp=p().hp,q=B.shot(60,0,-600,0);A.step(.1);
 A.assert(!B.exists(q)&&p().hp<hp,'removed guard continued intercepting hostile projectiles');
 return {fixedAnchor:anchor,blocksAfterMoving:blocks+1,unlearned:true};
}"""

INDEPENDENT_ACTION = r"""() => {
 const B=BGuard,{A,p,id}=B;B.prepare();A.assert(p().addMove('naruto-kimimaro-bracken'),'cannot add forest');
 p().target=A.spawn(80,0);
 A.cast('naruto-kimimaro-bracken');A.advance(.55);const action=A.action(),age=action.age,hp=p().hp;
 const q=B.shot();A.step(.10);A.advance(.2);
 A.assert(!B.exists(q)&&p().hp===hp,'guard did not defend during an existing cast');
 A.assert(A.action()===action&&A.action().kind==='bracken'&&A.action().age>age,'guard replaced existing body action');
 A.assert(p().moves.find(m=>m.id===id).passive,'guard lost passive status');
 return {preservedAction:'bracken',intercepted:true};
}"""

LIFECYCLE = r"""() => {
 const B=BGuard,{A,p,K}=B;B.prepare();const q=B.shot();A.pause();
 const before=JSON.stringify(B.state());G.Combat.resolve(.1,p(),0);G.Combat.updateFields(.1);
 A.assert(B.exists(q)&&JSON.stringify(B.state())===before,'pause triggered interception or advanced guard');
 A.step(.1);A.assert(B.state()?.cooldown>0,'resume did not activate guard');
 const active=JSON.stringify(B.state());A.pause();G.Combat.resolve(.2,p(),0);G.Combat.updateFields(.2);
 A.assert(JSON.stringify(B.state())===active,'pause advanced active wall/cooldown');
 G.Combat.clearFields(p());A.assert(!B.state()?.active&&!B.state()?.cooldown,'owner clear leaked guard');
 B.prepare();B.shot();A.step(.1);const oldWorld=G.World;G.World={...oldWorld};
 try{A.assert(!B.state()?.active&&!B.state()?.cooldown,'world switch retained guard')}finally{G.World=oldWorld}
 B.prepare();B.shot();A.step(.1);p().dead=true;
 A.assert(!B.state()?.active&&!B.state()?.cooldown,'death retained guard');p().dead=false;
 for(const method of ['quit','toUI']){
   B.prepare();B.shot();A.step(.1);A.resume();
   if(method==='toUI')G.Game.toUI('menu');else G.Game.quit();
   A.assert(!B.state()?.active&&!B.state()?.cooldown,'terminal method retained guard '+method);
   G.Game.startRun();A.pause();
 }
 return {paused:true,resumed:true,ownerClear:true,world:true,death:true,terminal:true};
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
                frame=game.boot(page,label);frame.evaluate(SETUP)
                for name,check in [('progression',PROGRESSION),('intercept',INTERCEPT),('exclusions',EXCLUSIONS),('wallAndCooldown',WALL_AND_COOLDOWN),('fixedCooldown',FIXED_COOLDOWN),('stationaryAndUnlearn',STATIONARY_AND_UNLEARN),('independentAction',INDEPENDENT_ACTION),('clones',CLONES),('lifecycle',LIFECYCLE)]:
                    print(label,name,flush=True)
                    try:result[name]=frame.evaluate(check)
                    except Exception as error:report['failures'].append(label+':'+name+': '+str(error))
            except Exception as error:report['failures'].append(label+':boot: '+str(error))
            finally:context.close()
        browser.close()
    report['sourceHashesAfter']=game.runtime_hashes()
    if report['sourceHashesAfter']!=report['sourceHashes']:report['failures'].append('runtime changed during acceptance')
    report['ok']=not(report['errors'] or report['failedRequests'] or report['failures'])
    path=game.OUT/'report-bone-guard.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'report':str(path)},ensure_ascii=True))
    if not report['ok']:raise SystemExit(1)


if __name__=='__main__':main()
