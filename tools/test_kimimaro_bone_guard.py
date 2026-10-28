"""Native projectile acceptance for Kimimaro's one-second bone defense ring."""
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
   const m=G.Moves.instance(id,rank);A.near(m.cd,[2.5,2.25,2,1.75,1.5][rank-1],'rank cooldown '+rank);cooldowns.push(m.cd);
 }
 return {learnLevel:6,slotless:true,cooldowns};
}"""

INTERCEPT = r"""() => {
 const B=BGuard,{A,p}=B,out=[];
 for(const [name,x,y,vx,vy,dt,flags={}] of [
   ['front',120,0,-500,0,.10],['back',-120,0,500,0,.10],
   ['top',0,-120,0,500,.10],['bottom',0,120,0,-500,.10],
   ['diagonal',100,100,-500,-500,.10],['fast-crossing',120,0,-2000,0,.10],
   ['unblockable',120,0,-500,0,.10,{unblockable:true}],
   ['guardUnblockable',120,0,-500,0,.10,{guardUnblockable:true}],
   ['uninterceptable',120,0,-500,0,.10,{uninterceptable:true}],
   ['all-block-flags',120,0,-500,0,.10,{unblockable:true,guardUnblockable:true,uninterceptable:true}]]){
   B.prepare();const hp=p().hp,q=B.shot(x,y,vx,vy,flags);A.step(dt);A.advance(.25);
   A.assert(!B.exists(q),'threat not intercepted '+name);A.near(p().hp,hp,'guard failed to protect '+name);
   const state=B.state();A.assert(state&&state.cooldown>0,'block did not start cooldown '+name);
   out.push({name,protected:true,state});
 }
 return out;
}"""

EXCLUSIONS = r"""() => {
 const B=BGuard,{A}=B,out=[];
 const cases=[['friendly',120,0,-500,0,{friendly:true}],['away',70,0,500,0,{}],
   ['near-miss',120,100,-500,0,{}],
   ['ground',120,0,-500,0,{ground:true}],['beam',120,0,-500,0,{beam:true}],
   ['laser',120,0,-500,0,{laser:true}],['orb',120,0,-500,0,{orb:true,oa:0,ospeed:0,orad:120}],
   ['hazard',120,0,-500,0,{hazard:true}],['far',180,0,-10,0,{}]];
 for(const [name,x,y,vx,vy,flags] of cases){
   B.prepare();const q=B.shot(x,y,vx,vy,flags);A.step(.10);
   A.assert(B.exists(q),'guard deleted excluded projectile '+name);
   const state=B.state();A.assert(!state?.cooldown,'guard spent cooldown on excluded projectile '+name);
   out.push(name);
 }
 const active=[];
 for(const [name,flags] of [['friendly',{friendly:true}],['ground',{ground:true}],['beam',{beam:true}],
   ['laser',{laser:true}],['hazard',{hazard:true}],['orb',{orb:true,oa:0,ospeed:0,orad:40}]]){
   B.prepare();B.shot(60,0,-600,0);A.step(.1);const before=B.state();
   const q=B.shot(60,0,-100,0,flags);A.step(.1);
   A.assert(B.exists(q),'active defense consumed a non-bullet '+name);
   A.assert(B.state().blocks===before.blocks&&B.state().triggers===1,'non-bullet changed active interception counters '+name);
   active.push(name);
 }
 return {ignoredWhileIdle:out,ignoredDuringWindow:active};
}"""

WALL_AND_COOLDOWN = r"""() => {
 const B=BGuard,{A,p}=B;B.prepare();const hp=p().hp,first=B.shot(60,0,-600,0);A.step(.05);
 A.assert(!B.exists(first)&&B.state().active,'first threat did not activate defense');
 const initial=B.state(),volley=[];
 A.near(initial.wall.duration,1,'defense window duration');A.near(initial.wall.radius,46,'defense circle radius');
 for(let n=0;n<8;n++){const a=n*Math.PI/4;volley.push(B.shot(Math.cos(a)*90,Math.sin(a)*90,-Math.cos(a)*900,-Math.sin(a)*900))}
 volley.push(B.shot(-120,0,2000,0));
 volley.push(B.shot(90,0,-900,0,{unblockable:true}),B.shot(0,-90,0,900,{guardUnblockable:true}),B.shot(-90,0,900,0,{uninterceptable:true}));
 const far=B.shot(180,0,-10,0);A.step(.1);
 const state=B.state();A.assert(volley.every(q=>!B.exists(q))&&p().hp===hp,'one-second defense failed to block all directions or fast crossings');
 A.assert(B.exists(far),'active defense cleared a distant bullet that never touched its circle');
 A.assert(state.blocks===1+volley.length&&state.triggers===1,'continuous bullets restarted defense or failed to count blocks');
 A.near(state.wall.born,initial.wall.born,'continuous blocks refreshed defense window');
 A.near(initial.cooldown-state.cooldown,.1,'continuous blocks restarted cooldown');
 return {directions:8,fastBackside:true,flaggedBullets:true,blocked:state.blocks,windowDuration:state.wall.duration,triggers:state.triggers,distantBulletRetained:true};
}"""

WINDOW_BOUNDARY = r"""() => {
 const B=BGuard,{A,p}=B;B.prepare();B.shot(60,0,-600,0);A.step(.02);
 const born=B.state().wall.born;A.advance(.99-B.state().wall.age);
 const hp=p().hp,edge=B.shot(50,0,-600,0);A.step(.005);let state=B.state();
 A.assert(!B.exists(edge)&&p().hp===hp&&state.active&&state.wall.age<1,'defense stopped before its one-second boundary');
 A.near(state.wall.born,born,'boundary hit extended defense');
 const blocks=state.blocks;A.advance(.006);state=B.state();
 A.assert(!state.active&&state.cooldown>0,'defense remained active after its one-second boundary');
 p().invuln=0;const after=B.shot(36,0,-600,0);A.step(.06);
 A.assert(!B.exists(after)&&p().hp<hp&&B.state().blocks===blocks&&B.state().triggers===1,'expired window continued blocking bullets or restarted before cooldown');
 return {blockedAt:.995,expiredBy:1.001,hpLossAfterExpiry:hp-p().hp,windowWasNotRefreshed:true};
}"""

MELEE_AND_GROUND = r"""() => {
 const B=BGuard,{A,p}=B;B.prepare();B.shot(60,0,-600,0);A.step(.1);const active=B.state();
 const enemy=A.spawn(10,0);enemy.dmg=30;enemy.touchCd=0;const before=p().hp;p().invuln=0;A.step(.01);
 A.assert(p().hp<before&&B.state().active,'active bullet defense prevented native melee contact damage');
 const meleeLoss=before-p().hp;enemy.dead=true;p().invuln=0;
 const hp=p().hp,ground=B.shot(30,0,-600,0,{ground:true});A.step(.05);
 A.assert(!B.exists(ground)&&p().hp<hp&&B.state().blocks===active.blocks,'active bullet defense blocked native ground attack damage');
 return {meleeLoss,groundLoss:hp-p().hp,onlyBulletsBlocked:true};
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
   const cd=[2.5,2.25,2,1.75,1.5][rank-1];
   A.assert(state.cooldown>=cd-.100001&&state.cooldown<=cd,'guard cooldown changed with cooldown/quantity attributes '+rank);
   A.advance(state.cooldown-.02);
   const early=B.shot(60,0,-600,0);A.step(.01);
   A.assert(B.exists(early)&&B.state().triggers===1,'guard rearmed before its cooldown '+rank);G.Projectiles.remove(early);
   A.advance(.02);const hp=p().hp,ready=B.shot(60,0,-600,0);A.step(.1);
   A.assert(!B.exists(ready)&&p().hp===hp&&B.state().triggers===2&&B.state().blocks===2,'guard failed to rearm at halved cooldown '+rank);
   out.push({rank,cooldown:state.cooldown,triggers:B.state().triggers,blocks:B.state().blocks,rearmed:true});
 }
 p().cdMul=1;p().quantityPicks=0;return out;
}"""

MOVING_AND_UNLEARN = r"""() => {
 const B=BGuard,{A,p,id}=B;B.prepare();B.shot();A.step(.1);A.advance(.15);
 const original=B.state(),wall=original.wall,anchor={x:wall.x,y:wall.y},blocks=original.blocks;
 p().x+=100;p().y+=100;p().walking=true;A.step(.02);
 A.near(B.state().wall.x,p().x,'defense circle did not follow owner horizontally');
 A.near(B.state().wall.y,p().y,'defense circle did not follow owner vertically');
 const movingHp=p().hp,left=B.shot(-80,0,800,0),right=B.shot(80,0,-800,0);A.step(.1);
 A.assert(!B.exists(left)&&!B.exists(right)&&p().hp===movingHp&&B.state().blocks===blocks+2,'moving owner lost all-direction projectile protection');
 const old=G.Projectiles.spawn({x:anchor.x+30,y:anchor.y,vx:-100,vy:0,friendly:false,r:5,dmg:30,mtype:'normal',life:4});A.step(.1);
 A.assert(B.exists(old),'moved defense left an extra blocking circle at the original position');
 B.prepare();B.shot();A.step(.1);A.advance(.15);
 p().moves=p().moves.filter(m=>m.id!==id);p().arrange();A.step(.01);
 A.assert(B.state()===null,'removed move retained guard state');
 const hp=p().hp,q=B.shot(60,0,-600,0);A.step(.1);
 A.assert(!B.exists(q)&&p().hp<hp,'removed guard continued intercepting hostile projectiles');
 return {originalAnchor:anchor,followedTo:{x:100,y:100},blocksAfterMoving:blocks+2,oldPositionUnprotected:true,unlearned:true};
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
                for name,check in [('progression',PROGRESSION),('intercept',INTERCEPT),('exclusions',EXCLUSIONS),('wallAndCooldown',WALL_AND_COOLDOWN),
                  ('windowBoundary',WINDOW_BOUNDARY),('meleeAndGround',MELEE_AND_GROUND),('fixedCooldown',FIXED_COOLDOWN),('movingAndUnlearn',MOVING_AND_UNLEARN),
                  ('independentAction',INDEPENDENT_ACTION),('clones',CLONES),('lifecycle',LIFECYCLE)]:
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
