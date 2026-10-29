"""Native projectile acceptance for independently recharging defensive bones."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault('KIMIMARO_OUT', str(Path(__file__).resolve().parents[1]/'.omx/state/kimimaro-bone-guard'))
import test_kimimaro as game
from playwright.sync_api import sync_playwright


SETUP = r"""() => {
 const A=KAcceptance,p=A.p,K=A.K,id='naruto-kimimaro-bone-guard';
 function prepare(rank=1){A.reset();const m=A.fixture(id,rank);p().invuln=0;A.step(.001);return m}
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
   const m=G.Moves.instance(id,rank);A.near(m.cd,3,'independent root cooldown rank '+rank);cooldowns.push(m.cd);
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
   const state=B.state();A.assert(state&&state.blocks===1&&state.readyCount===state.count-1,'block did not consume exactly one root '+name);
   A.assert(state.slots.filter(slot=>slot.blocks===1&&slot.cooldown>0).length===1,'blocked bullet did not start one independent cooldown '+name);
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
   const state=B.state();A.assert(state.blocks===0&&state.readyCount===state.count&&!state.walls.length,'guard spent a root or grew a bone for excluded projectile '+name);
   out.push(name);
 }
 const active=[];
 for(const [name,flags] of [['friendly',{friendly:true}],['ground',{ground:true}],['beam',{beam:true}],
   ['laser',{laser:true}],['hazard',{hazard:true}],['orb',{orb:true,oa:0,ospeed:0,orad:40}]]){
   B.prepare();B.shot(60,0,-600,0);A.step(.1);const before=B.state();
   const q=B.shot(60,0,-100,0,flags);A.step(.1);
   A.assert(B.exists(q),'active defense consumed a non-bullet '+name);
   A.assert(B.state().blocks===before.blocks&&B.state().triggers===1&&B.state().readyCount===before.readyCount,'non-bullet spent a root while another visual bone remained '+name);
   active.push(name);
 }
 return {ignoredWhileIdle:out,ignoredBesideVisualBone:active};
}"""

WALL_AND_COOLDOWN = r"""() => {
 const B=BGuard,{A,p}=B,out=[];
 for(let rank=1;rank<=5;rank++){
   B.prepare(rank);p().quantityPicks=p().quantityBonus=30;p().cdMul=.01;A.step(.001);
   const count=[10,12,15,18,20][rank-1],idle=B.state();
   A.assert(idle.count===count&&idle.readyCount===count&&!idle.walls.length,'rank capacity changed with quantity/CD attributes or grew idle columns');
   const hp=p().hp,volley=Array.from({length:count+1},()=>B.shot(60,0,-600,0));A.step(.1);
   const state=B.state();
   A.assert(state.blocks===count&&state.triggers===count&&state.readyCount===0,'rank did not intercept exactly one bullet per available root');
   A.assert(state.slots.every(slot=>slot.blocks===1&&slot.cooldown>0),'one root blocked multiple simultaneous bullets');
   A.assert(p().hp<hp&&volley.every(q=>!B.exists(q)),'capacity overflow did not deal native projectile damage');
   A.assert(state.walls.length===count&&new Set(state.walls.map(w=>w.slot)).size===count,'blocked bullets did not each create exactly one visual root');
   for(const wall of state.walls)A.near(state.slots[wall.slot].readyAt-wall.hitAt,3,'root cooldown did not start at its own contact time');
   p().invuln=0;const before=p().hp,extra=B.shot(40,0,-800,0);A.step(.05);
   A.assert(!B.exists(extra)&&p().hp<before&&B.state().blocks===count,'remaining visual columns acted as a persistent shield');
   A.assert(B.state().walls.length===count,'overflow bullet created an unearned additional column');
   A.advance(.5);A.assert(B.state().walls.length===0&&B.state().readyCount===0,'visual bones did not disappear independently of recharge');
   out.push({rank,count,blocked:state.blocks,overflowDamage:hp-p().hp,oneBulletPerRoot:true,visualOnly:true});
 }
 return out;
}"""

WINDOW_BOUNDARY = r"""() => {
 const B=BGuard,{A,p,K}=B;B.prepare();B.shot(60,0,-600,0);A.step(.05);
 const first=B.state(),firstReady=first.slots[0].readyAt;
 A.advance(.45);B.shot(60,0,-600,0);A.step(.05);
 const second=B.state(),secondReady=second.slots[1].readyAt;
 A.near(secondReady-firstReady,.5,'staggered roots did not preserve independent contact times');
 A.near(second.slots[0].readyAt,firstReady,'using a second root refreshed the first cooldown');
 for(let n=0;n<8;n++)B.shot(60,0,-600,0);A.step(.05);
 A.assert(B.state().readyCount===0&&B.state().blocks===10,'staggered cooldown fixture did not exhaust remaining roots');
 A.advance(firstReady-.005-K.stateFor(p()).clock);p().invuln=0;
 const hp=p().hp,early=B.shot(5,0,-600,0);A.step(.001);
 A.assert(!B.exists(early)&&p().hp<hp&&B.state().blocks===10&&B.state().readyCount===0,'root rearmed before its three-second contact boundary');
 A.advance(.01);A.assert(B.state().readyCount===1&&B.state().slots[0].cooldown===0&&B.state().slots[1].cooldown>0,'roots recovered globally instead of independently');
 const ready=B.shot(60,0,-600,0);A.step(.05);let state=B.state();
 A.assert(!B.exists(ready)&&state.slots[0].blocks===2&&state.slots[1].blocks===1,'earliest recovered root did not intercept independently');
 const firstAgain=state.slots[0].readyAt;
 A.near(state.slots[1].readyAt,secondReady,'reusing the first root reset the second cooldown');
 A.advance(secondReady+.001-K.stateFor(p()).clock);A.assert(B.state().readyCount===1,'second root missed its separate recharge boundary');
 const next=B.shot(60,0,-600,0);A.step(.04);state=B.state();
 A.assert(!B.exists(next)&&state.slots[1].blocks===2,'second root could not fire while the first recharged again');
 A.near(state.slots[0].readyAt,firstAgain,'second reuse refreshed the first root');
 return {firstReady,secondReady,stagger:.5,firstAgain,blocks:state.blocks,independent:true};
}"""

RISE_CONTACT_CANCEL = r"""() => {
 const B=BGuard,{A,p,K}=B;B.prepare();const q=B.shot(150,0,-500,0);
 A.step(.01);const rising=B.state(),wall=rising.wall;
 A.assert(B.exists(q)&&rising.blocks===0&&rising.readyCount===9,'pre-rise erased bullet or failed to reserve a root');
 A.assert(wall?.phase==='rise'&&wall.x>80&&wall.x<105,'bone did not grow on outer interception ring');
 A.assert(rising.slots[0].reserved&&rising.slots[0].readyAt===0,'reservation consumed cooldown before contact');
 const next=B.shot(150,0,-500,0);A.step(.01);
 A.assert(B.state().readyCount===8&&B.state().slots.filter(s=>s.reserved).length===2,'reserved root reused for another bullet');
 A.advance(.04);A.assert(B.exists(q)&&B.exists(next)&&B.state().blocks===0,'bullet disappeared before physical contact');
 A.advance(.05);const hit=B.state();
 A.assert(!B.exists(q)&&!B.exists(next)&&hit.blocks===2,'physical contact failed to consume assigned bullets');
 A.assert(hit.walls.every(w=>w.phase==='impact'&&w.flash>0),'contact lacked visible impact');
 for(const w of hit.walls)A.near(hit.slots[w.slot].readyAt-w.hitAt,3,'cooldown did not start at physical contact');
 A.advance(.35);A.assert(B.state().walls.length===2,'impact bones vanished too quickly');
 A.advance(.17);A.assert(B.state().walls.length===0,'impact bones did not crumble away');
 B.prepare();const canceled=B.shot(150,0,-500,0);A.step(.01);G.Projectiles.remove(canceled);A.step(.01);
 A.assert(B.state().readyCount===10&&B.state().blocks===0&&!B.state().walls.length,'disappearing shot consumed reserved root');
 const veer=B.shot(150,0,-500,0);A.step(.01);veer.vx=0;veer.vy=500;A.step(.01);
 A.assert(B.exists(veer)&&B.state().readyCount===10&&!B.state().walls.length,'veering shot was erased or left a reservation');
 return {preRise:true,outerContact:wall.x,oneReservationPerBullet:true,contactCooldown:3,canceledWithoutCooldown:true,impactDuration:.5};
}"""

MELEE_AND_GROUND = r"""() => {
 const B=BGuard,{A,p}=B;B.prepare();B.shot(60,0,-600,0);A.step(.1);const active=B.state();
 const enemy=A.spawn(10,0);enemy.dmg=30;enemy.touchCd=0;const before=p().hp;p().invuln=0;A.step(.01);
 A.assert(p().hp<before&&B.state().walls.length>0,'visible defensive bone prevented native melee contact damage');
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
 A.assert(B.state(clone)?.blocks>=1&&B.state(clone).readyCount===B.state(clone).count-1,'clone has no independent guard inventory');
 A.assert(!B.state()?.blocks&&B.state().readyCount===B.state().count,'clone guard consumed parent inventory');
 const own=B.shot(-120,0,500,0);A.step(.1);A.advance(.25);
 A.assert(!B.exists(own)&&p().hp===ownerHp&&B.state()?.blocks>=1,'parent guard unavailable after clone defense');
 G.Combat.clearFields(p());A.assert(!B.state(clone),'parent cleanup retained clone guard');
 return {cloneProtected:true,parentIndependent:true,cleanup:true};
}"""

FIXED_COOLDOWN = r"""() => {
 const B=BGuard,{A,p,K}=B,m=B.prepare();B.shot(60,0,-600,0);A.step(.1);const stages=[];
 for(let rank=2;rank<=5;rank++){
   const saved=K.stateFor(p()).boneGuard.slots.map(slot=>({slot,readyAt:slot.readyAt,blocks:slot.blocks}));
   A.assert(G.Moves.levelUp(m),'native defensive-bone upgrade failed');A.step(.001);
   const state=B.state(),raw=K.stateFor(p()).boneGuard.slots,count=[10,12,15,18,20][rank-1];
   A.assert(state.count===count&&state.readyCount===count-1,'rank upgrade did not add ready roots while retaining the used one');
   for(const item of saved){
     A.assert(raw[item.slot.index]===item.slot,'rank upgrade replaced an existing defensive root');
     A.near(item.slot.readyAt,item.readyAt,'rank upgrade reset an existing root cooldown');
     A.assert(item.slot.blocks===item.blocks,'rank upgrade reset root usage history');
   }
   A.assert(state.slots.slice(saved.length).every(slot=>slot.blocks===0&&slot.cooldown===0),'new rank roots were not immediately ready');
   A.assert(state.walls.length===1,'upgrading grew idle visual bones');
   stages.push({rank,count,ready:state.readyCount,retainedReadyAt:state.slots[0].readyAt,added:count-saved.length});
 }
 p().quantityPicks=p().quantityBonus=40;p().cdMul=.01;A.step(.001);
 A.assert(B.state().count===20&&B.state().readyCount===19,'quantity/cooldown cards changed the fixed rank inventory');
 return {stages,fixedCooldown:3,quantityIgnored:true,cooldownMultiplierIgnored:true};
}"""

MOVING_AND_UNLEARN = r"""() => {
 const B=BGuard,{A,p,id}=B;B.prepare();B.shot();A.step(.1);A.advance(.15);
 const original=B.state(),wall=original.wall,anchor={x:wall.x,y:wall.y},blocks=original.blocks;
 p().x+=100;p().y+=100;p().walking=true;A.step(.02);
 A.near(B.state().wall.x,anchor.x,'already-grown visual bone followed owner horizontally');
 A.near(B.state().wall.y,anchor.y,'already-grown visual bone followed owner vertically');
 const movingHp=p().hp,left=B.shot(-80,0,800,0);A.step(.1);
 A.assert(!B.exists(left)&&p().hp===movingHp&&B.state().blocks===blocks+1,'moving owner could not use another ready root');
 A.assert(B.state().slots[0].blocks===1&&B.state().slots[1].blocks===1,'old visual bone blocked another bullet without a separate root');
 const secondVisual=B.state().walls[1];
 const old=G.Projectiles.spawn({x:anchor.x+30,y:anchor.y,vx:-100,vy:0,friendly:false,r:5,dmg:30,mtype:'normal',life:4});A.step(.01);
 A.assert(B.exists(old)&&B.state().blocks===blocks+1,'old visual bone kept intercepting non-threatening bullets');
 B.prepare();B.shot();A.step(.1);A.advance(.15);
 p().moves=p().moves.filter(m=>m.id!==id);p().arrange();A.step(.01);
 A.assert(B.state()===null,'removed move retained guard state');
 const hp=p().hp,q=B.shot(60,0,-600,0);A.step(.1);
 A.assert(!B.exists(q)&&p().hp<hp,'removed guard continued intercepting hostile projectiles');
 return {originalVisualFixed:anchor,newVisual:{x:secondVisual.x,y:secondVisual.y},blocksAfterMoving:blocks+1,oldPositionUnprotected:true,unlearned:true};
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
 A.step(.2);A.assert(B.state()?.blocks===1&&B.state().readyCount===B.state().count-1,'resume did not consume a root for the actual bullet contact');
 p().frozen=true;const frozen=JSON.stringify(B.state());A.advance(.5,true);
 A.assert(JSON.stringify(B.state())===frozen,'freeze advanced defensive root cooldowns or visuals');p().frozen=false;
 const active=JSON.stringify(B.state());A.pause();G.Combat.resolve(.2,p(),0);G.Combat.updateFields(.2);
 A.assert(JSON.stringify(B.state())===active,'pause advanced active wall/cooldown');
 G.Combat.clearFields(p());A.assert(!B.state()?.active&&!B.state()?.cooldown,'owner clear leaked guard');
 B.prepare();B.shot(60,0,-600,0);A.step(.1);const oldWorld=G.World;G.World={...oldWorld};
 try{A.assert(!B.state()?.active&&!B.state()?.cooldown,'world switch retained guard')}finally{G.World=oldWorld}
 B.prepare();B.shot(60,0,-600,0);A.step(.1);p().dead=true;
 A.assert(!B.state()?.active&&!B.state()?.cooldown,'death retained guard');p().dead=false;
 for(const method of ['quit','toUI']){
   B.prepare();B.shot(60,0,-600,0);A.step(.1);A.resume();
   if(method==='toUI')G.Game.toUI('menu');else G.Game.quit();
   A.assert(!B.state()?.active&&!B.state()?.cooldown,'terminal method retained guard '+method);
   G.Game.startRun();A.pause();
 }
 return {paused:true,resumed:true,frozen:true,ownerClear:true,world:true,death:true,terminal:true};
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
                  ('riseContactCancel',RISE_CONTACT_CANCEL),('independentRecovery',WINDOW_BOUNDARY),('meleeAndGround',MELEE_AND_GROUND),('rankUpgrade',FIXED_COOLDOWN),('movingAndUnlearn',MOVING_AND_UNLEARN),
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
