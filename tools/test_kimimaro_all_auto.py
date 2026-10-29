"""Learned Kimimaro skills act automatically through the native game loop."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault('KIMIMARO_OUT',str(Path(__file__).resolve().parents[1]/'.omx/state/kimimaro-all-auto'))
import test_kimimaro as native
from playwright.sync_api import sync_playwright


HELPERS = r"""() => {
 const A=KAcceptance,p=A.p(),K=A.K,id=k=>k==='willow'?'naruto-kimimaro':'naruto-kimimaro-'+k;
 const keys=['willow','bullets','larch','vine','curse','bone-guard','camellia','flower','lily','bracken','boomerang'];
 function prepare(learned,rank=1){
   A.reset();p.level=30;p.moves=[];p.slots=[];p.bind={};p.active=0;p.maxMoves=4;
   for(const key of learned){A.assert(p.addMove(id(key)),'cannot learn '+key);
     const m=p.moves.find(m=>m.id===id(key));Object.assign(m,G.Moves.instance(m.id,rank));m.t=999;}
   p.arrange();A.advance(.11);return p.moves;
 }
 const move=k=>p.moves.find(m=>m.id===id(k));
 window.KAllAuto={...A,p,K,id,keys,prepare,move};
}"""

PROGRESSION = r"""() => {
 const A=KAllAuto,p=A.p,out={gates:[],ranks:[]};
 A.assert(p.level===1&&p.moves.length===1&&p.moves[0].id===A.id('willow')&&!p.slots.length,'fresh start bypassed learning gates');
 const gates={camellia:3,bullets:3,boomerang:2,larch:6,vine:6,'bone-guard':6,flower:9,lily:9,bracken:12,curse:15};
 for(const level of [1,2,3,5,6,8,9,11,12,14,15]){
   p.level=level;const pool=G.Moves.poolFor(p.mon),cards=G.LevelUp.offer(p,100);
   for(const [key,gate] of Object.entries(gates)){
     A.assert(pool.includes(A.id(key))===(level>=gate),'pool gate '+key+' at '+level);
     A.assert(cards.some(c=>c.key==='new:'+A.id(key))===(level>=gate),'learn choice gate '+key+' at '+level);
   }out.gates.push({level,pool});
 }
 for(const key of A.keys)for(let rank=1;rank<=5;rank++){
   const m=G.Moves.instance(A.id(key),rank);A.assert(m.passive,'skill is not slotless '+key+' rank '+rank);
   out.ranks.push({key,rank,passive:m.passive,cd:m.cd,dmg:m.dmg});
 }
 A.prepare(A.keys);A.assert(p.moves.length===11&&p.slots.length===0,'eleven learned skills consumed active slots');
 return out;
}"""

FORMER_ACTIVES = r"""() => {
 const A=KAllAuto,p=A.p,out=[];
 for(const key of ['camellia','flower','lily','bracken'])for(const rank of [1,5]){
   A.prepare([key],rank);const m=A.move(key),distance={camellia:160,flower:160,lily:150,bracken:350}[key];
   m.t=0;const e=A.spawn(distance,0),hits=A.watch(e);p.target=e;
   A.assert(p.slots.length===0&&p.activeGroup().length===0,'fixture has a selected group '+key);
   A.step(.001,true);A.assert(A.action()?.kind===key,'unselected learned skill did not auto cast '+key);
   A.assert(m.t>0,'auto cast omitted cooldown '+key);const started=m.t;
   A.advance(key==='bracken'?3.3+.5*(rank-1):1.2);
   const shares=key==='camellia'?[.25,.25,.5]:key==='lily'?[.5,.5]:[1];
   const perBurst=shares.reduce((sum,share)=>sum+A.expected(m,share,e),0);
   const expectedHits=key==='bracken'?Math.min(rank,Math.ceil(e.maxHp/perBurst)):null;
   const expected=key==='bracken'?expectedHits*perBurst:perBurst;
   A.assert(e.maxHp-e.hp===expected,'native automatic damage '+key+' rank '+rank);
   if(key==='bracken')A.assert(hits.length===expectedHits&&hits.every(h=>h.loss===perBurst),'automatic burst damage duplicated, split or damaged a dead target');
   A.assert(hits.every(h=>h.owner&&h.id===m.id),'automatic damage lost owner or technique '+key);
   A.assert(p.slots.length===0,'automatic cast created an active slot '+key);
   out.push({key,rank,hits:hits.length,loss:e.maxHp-e.hp,cooldownAtStart:started,expected});
 }
 return out;
}"""

COMBO = r"""() => {
 const A=KAllAuto,p=A.p;A.prepare(['vine','flower']);const vine=A.move('vine'),flower=A.move('flower');vine.t=flower.t=0;
 const e=A.spawn(155,0),hits=A.watch(e);p.target=e;A.step(.001,true);
 A.assert(A.action()?.kind==='combo'&&p.slots.length===0,'two unselected learned skills did not auto link');
 A.assert(vine.t>0&&flower.t===0,'Vine/Flower cooldowns were charged together');
 A.advance(.53);A.assert(!A.K.stateFor(p).castCounts.flower&&flower.t===0,'Flower started early');
 A.advance(.02);A.assert(A.K.stateFor(p).castCounts.flower===1&&Math.abs(flower.t-8)<.011,'Flower own cooldown missing at second phase');
 A.advance(.9);A.assert(hits.length===2&&e.maxHp-e.hp===A.expected(vine,1,e)+A.expected(flower,1,e),'linked native damage duplicated or dropped');
 const log=A.K.stateFor(p).castLog;A.near(log[1].time-log[0].time,.54,'independent second-stage start');
 return {slots:p.slots.length,log,hits};
}"""

FAIRNESS = r"""() => {
 const A=KAllAuto,p=A.p;A.prepare(A.keys);for(const m of p.moves)m.t=0;
 const close=A.spawn(55,0),hits=A.watch(close);p.target=close;A.step(.001,true);
 A.advance(.20,true);const action=A.action();
 const q=G.Projectiles.spawn({x:p.x+100,y:p.y,vx:-600,vy:0,r:5,dmg:30,mtype:'normal',friendly:false,life:4});
 const hp=p.hp;A.advance(.25,true);
 A.assert(!G.Projectiles.all().includes(q)&&p.hp===hp,'independent bone guard did not protect during body action');
 A.assert(A.action()===action,'bone guard interrupted body technique');
 A.advance(11.55,true);const state=A.K.stateFor(p),counts={...state.castCounts},log=[...state.castLog];
 for(const key of ['curse','willow','camellia','larch','vine','flower','lily','bracken'])
   A.assert(counts[key]>=1,'ready learned technique starved '+key+' '+JSON.stringify(counts));
 A.assert(p.slots.length===0&&state.boneGuard.blocks>=1,'fair scheduler created selection or lost guard');
 close.dead=true;G.EnemyMgr.rebuildGrid();A.advance(4);
 for(const m of p.moves)m.t=999;A.move('bullets').t=0;
 const far=A.spawn(250,0),rangedHits=A.watch(far);p.target=far;A.advance(2,true);
 const bulletHits=rangedHits.filter(h=>h.id===A.id('bullets'));
 A.assert(bulletHits.length>=5&&A.K.stateFor(p).castCounts.bullets>=1,'ranged auto did not resume when close pressure ended');
 A.assert(A.K.boomerangState(p).launches>=1,'independent learned boomerang did not launch alongside body actions');
 return {counts,log,guardBlocks:state.boneGuard.blocks,damageTechniques:[...new Set(hits.map(h=>h.id))],rangedHits,bulletHits};
}"""

MIGRATION = r"""() => {
 const A=KAllAuto,p=A.p;A.prepare(A.keys);
 const former=['camellia','flower','lily','bracken'].map((key,i)=>{
   const m=A.move(key);Object.assign(m,G.Moves.instance(m.id,i+2));m.passive=false;m.t=1.2+i;return m;
 });
 p.slots=former.map(m=>[m]);p.active=2;p.bind=Object.fromEntries(former.map((m,i)=>[m.id,i]));
 const saved=former.map(m=>({m,lvl:m.lvl,t:m.t,cd:m.cd}));
 G.Moves.poolFor(p.mon);p.arrange();G.Moves.poolFor(p.mon);p.arrange();
 A.assert(p.slots.length===0&&p.moves.length===11&&new Set(p.moves.map(m=>m.id)).size===11,'migration left slots or duplicated skills');
 for(const item of saved){
   A.assert(p.moves.includes(item.m)&&item.m.passive,'migration replaced skill object or retained active flag');
   A.near(item.m.lvl,item.lvl,'migration lost rank');A.near(item.m.t,item.t,'migration lost remaining cooldown');A.near(item.m.cd,item.cd,'migration lost cooldown stat');
   A.assert(!Object.hasOwn(p.bind,item.m.id),'migration retained active key binding');
 }
 return {slots:p.slots.length,moves:p.moves.map(m=>({id:m.id,lvl:m.lvl,t:m.t,passive:m.passive})),bind:p.bind};
}"""


def hud_capture(page,frame,label,mobile):
    frame.evaluate(r"""() => {
      const A=KAllAuto;A.prepare(A.keys);A.p.frozen=true;
      window.KAllHUD={buttons:[],clear:G.Touch.clearButtons,add:G.Touch.addButton,setActive:A.p.setActive,selectionCalls:0};
      A.p.setActive=function(...args){KAllHUD.selectionCalls++;return KAllHUD.setActive.apply(this,args)};
      G.Touch.clearButtons=function(...args){KAllHUD.buttons=[];return KAllHUD.clear.apply(this,args)};
      G.Touch.addButton=function(x,y,w,h,...args){KAllHUD.buttons.push({x,y,w,h});return KAllHUD.add.call(this,x,y,w,h,...args)};
      A.resume();
    }""")
    page.wait_for_timeout(150)
    geometry=frame.evaluate(r"""() => {
      const A=KAllAuto,n=11,layout=G.Touch.active?G.Touch.controlLayout(innerWidth,innerHeight,n):null;
      const size=layout?.S??54,buttons=KAllHUD.buttons.filter(b=>Math.abs(b.w-size)<.01&&Math.abs(b.h-size)<.01);
      A.assert(buttons.length===11,'HUD did not render all eleven learned skill icons '+JSON.stringify(KAllHUD.buttons));
      A.assert(buttons.every(b=>b.x>=0&&b.y>=0&&b.x+b.w<=innerWidth&&b.y+b.h<=innerHeight),'eleven-skill HUD overflow');
      for(let i=0;i<buttons.length;i++)for(let j=i+1;j<buttons.length;j++){
        const a=buttons[i],b=buttons[j];A.assert(a.x+a.w<=b.x+.01||b.x+b.w<=a.x+.01||a.y+a.h<=b.y+.01||b.y+b.h<=a.y+.01,'skill icons overlap');
      }
      A.assert(document.documentElement.scrollWidth<=innerWidth,'document horizontally overflowed');
      return {buttons,width:innerWidth,height:innerHeight,touch:G.Touch.active,active:A.p.active};
    }""")
    offset={'x':0,'y':0}
    if frame!=page.main_frame:
        box=page.locator('iframe').first.bounding_box();offset={'x':box['x'],'y':box['y']}
    click=page.touchscreen.tap if mobile else page.mouse.click
    for slot in geometry['buttons']:
        click(slot['x']+slot['w']/2+offset['x'],slot['y']+slot['h']/2+offset['y'])
    assert frame.evaluate('KAllHUD.selectionCalls')==0,'automatic info icon invoked skill selection'
    assert frame.evaluate('G.Game.player.slots.length')==0,'HUD click introduced active selection'
    # Each queued native achievement toast remains visible for 2.8 seconds.
    frame.locator('#ach-pop').wait_for(state='hidden',timeout=20000)
    page.screenshot(path=str(native.OUT/f'{label}-eleven-auto-skills-hud.png'))
    frame.evaluate('G.Touch.addButton=KAllHUD.add;G.Touch.clearButtons=KAllHUD.clear;KAllAuto.p.setActive=KAllHUD.setActive;KAllAuto.p.frozen=false;KAllAuto.pause()')
    return {'allElevenVisible':True,'selectionCalls':0,'geometry':geometry}


def main():
    native.OUT.mkdir(parents=True,exist_ok=True)
    report={'url':native.URL,'errors':[],'failedRequests':[],'failures':[],'viewports':{},'sourceHashes':native.runtime_hashes()}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=native.CHROME,headless=True)
        for label,viewport,mobile in [('desktop',{'width':1280,'height':900},False),('mobile',{'width':390,'height':844},True)]:
            context=browser.new_context(viewport=viewport,is_mobile=mobile,has_touch=mobile,service_workers='block')
            page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
            page.on('response',lambda r:report['failedRequests'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            result=report['viewports'][label]={}
            try:
                frame=native.boot(page,label);frame.evaluate(HELPERS)
                for name,check in [('progression',PROGRESSION),('formerActives',FORMER_ACTIVES),('combo',COMBO),('fairness',FAIRNESS),('migration',MIGRATION)]:
                    print(label,name,flush=True)
                    try:result[name]=frame.evaluate(check)
                    except Exception as error:report['failures'].append(label+':'+name+': '+str(error))
                try:result['hud']=hud_capture(page,frame,label,mobile)
                except Exception as error:report['failures'].append(label+':hud: '+str(error))
            except Exception as error:report['failures'].append(label+':boot: '+str(error))
            finally:context.close()
        browser.close()
    report['sourceHashesAfter']=native.runtime_hashes()
    if report['sourceHashesAfter']!=report['sourceHashes']:report['failures'].append('runtime changed during acceptance')
    report['ok']=not(report['errors'] or report['failedRequests'] or report['failures'])
    path=native.OUT/'report-all-auto.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'report':str(path)},ensure_ascii=True))
    if not report['ok']:raise SystemExit(1)


if __name__=='__main__':main()
