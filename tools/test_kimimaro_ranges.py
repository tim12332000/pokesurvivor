"""Range acceptance in the normal game, with native actors and combat handlers."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault('KIMIMARO_OUT', str(Path(__file__).resolve().parents[1]/'.omx/state/kimimaro-ranges'))
import test_kimimaro as game
from playwright.sync_api import sync_playwright


RANGES = r"""() => {
 const A=KAcceptance,p=A.p(),out={ranks:[],casts:[]};
 const rows=[
  ['willow',[110,120,130,140,150],[30,36,42,51,60],.9],
  ['camellia',[220,240,260,280,300],[120,144,168,204,240],5,[40,44,48,52,56]],
  ['bullets',[380,400,420,440,460],[45,54,63,76.5,90],2.4],
  ['larch',[125,135,145,155,165],[96,115.2,134.4,163.2,192],6],
  ['vine',[320,340,360,380,400],[48,57.6,67.2,81.6,96],8],
  ['flower',[220,240,260,280,300],[192,230.4,268.8,326.4,384],8,[42,46,50,54,58]],
  ['lily',[200,220,240,260,280],[100,120,140,170,200],6],
  ['bracken',[400,450,500,550,600],[600,720,840,1020,1200],17]];
 for(const [key,ranges,damage,cd,widths] of rows){
  const id=key==='willow'?'naruto-kimimaro':'naruto-kimimaro-'+key;
  for(let rank=1;rank<=5;rank++){
   A.reset();const m=A.fixture(id,rank),radial=['larch','lily','bracken'].includes(key);
   A.near(m[radial?'radius':'range'],ranges[rank-1],key+' rank '+rank+' geometry');
   A.near(m.dmg,damage[rank-1],key+' damage');A.near(m.cd,cd,key+' cooldown');
   if(widths)A.near(m.halfWidth,widths[rank-1],key+' half width');
   out.ranks.push({key,rank,range:m.range,radius:m.radius,halfWidth:m.halfWidth,dmg:m.dmg,cd:m.cd,passive:!!m.passive});
   // All forty actual native casts put a victim beyond the old rank-one reach.
   const distance=ranges[rank-1]-12,e=A.spawn(distance,0),hits=A.watch(e);p.target=e;
   A.cast(id);A.advance(key==='bracken'?2.7:1.7);
   A.assert(hits.length>0,key+' rank '+rank+' extended-range victim missed at '+distance);
   A.assert(hits.every(h=>h.owner&&h.id===id),key+' lost native damage ownership');
   out.casts.push({key,rank,distance,hits:hits.length,loss:e.maxHp-e.hp});
  }
 }
 return out;
}"""

BOUNDARIES = r"""() => {
 const A=KAcceptance,p=A.p(),out={forests:[],lines:[]};
 for(const rank of [1,5]){
  A.reset();const m=A.fixture('naruto-kimimaro-bracken',rank);
  const coords=rank===1?[[350,0],[-240,280],[0,-390],[430,0]]:[[550,0],[-354,472],[0,-590],[630,0]];
  const es=coords.map(([x,y])=>A.spawn(x,y)),logs=es.map(A.watch);p.target=es[0];A.cast(m.id);A.advance(2.09);
  const loss=es.map(e=>e.maxHp-e.hp),expected=A.expected(m,1,es[0]);
  A.assert(loss.slice(0,3).every(v=>v===expected),'spread forest damage/range rank '+rank+' '+loss);
  A.assert(logs.slice(0,3).every(v=>v.length===1)&&loss[3]===0,'forest repeats or extends outside radius');
  // The next burst cannot reach these outer-ring victims before 2.58 seconds.
  A.advance(.48);A.assert(es.every((e,i)=>e.maxHp-e.hp===loss[i]),'first burst repeated an outer-ring hit');
  out.forests.push({rank,coords,loss,hits:logs.map(v=>v.length)});
 }
 for(const key of ['camellia','flower'])for(const rank of [1,5]){
  A.reset();const m=A.fixture('naruto-kimimaro-'+key,rank),primary=A.spawn(m.range-35,0);
  const side=A.spawn(m.range-20,m.halfWidth-1),outside=A.spawn(m.range-20,m.halfWidth+primary.r+15),far=A.spawn(m.range+20,0);
  p.target=primary;A.cast(m.id);A.advance(1);
  const losses=[primary,side,outside,far].map(e=>e.maxHp-e.hp);
  A.assert(losses[0]>0&&losses[1]>0&&losses[2]===0&&losses[3]===0,'line boundaries '+key+' rank '+rank+' '+losses);
  out.lines.push({key,rank,losses,range:m.range,halfWidth:m.halfWidth});
 }
 A.reset();const m=A.fixture('naruto-kimimaro-bracken'),boss=A.spawn(50,0,'boss'),jumper=A.spawn(0,50),flyer=A.spawn(-50,0);
 A.assert(boss.flying,'native boss flying fixture missing');flyer.flying=true;p.target=boss;A.cast(m.id);A.advance(.43);
 jumper.startJump(p);jumper.jump.t=.01;jumper.updateJump(0);
 for(let n=0;n<50;n++){jumper.updateJump(.01);A.step(.01)}
 A.assert(boss.hp<boss.maxHp&&jumper.hp===jumper.maxHp&&flyer.hp===flyer.maxHp,'boss/jump/flying ground eligibility');
 out.groundEligibility={bossLoss:boss.maxHp-boss.hp,jumperLoss:jumper.maxHp-jumper.hp,flyerLoss:flyer.maxHp-flyer.hp};
 return out;
}"""

BULLETS = r"""() => {
 const A=KAcceptance,p=A.p(),out={};A.reset();const m=A.fixture('naruto-kimimaro-bullets',3),e=A.spawn(420,0),hits=A.watch(e);
 p.target=e;A.cast(m.id);A.advance(.3);A.assert(e.hp===e.maxHp,'long shot bypassed flight time');A.advance(1.1);
 A.assert(hits.length===5&&e.maxHp-e.hp===5*A.expected(m,.2,e),'420px shot range or damage failed');out.longShot={hits:hits.length,loss:e.maxHp-e.hp};
 A.reset();A.fixture(m.id,3);const target=A.spawn(420,0);p.target=target;A.cast(m.id);A.advance(.17);
 const bone=A.K.bullets[0];A.assert(bone,'first bone missing');const velocity=[bone.vx,bone.vy];target.y=180;G.EnemyMgr.rebuildGrid();A.advance(.08);
 A.near(bone.vx,velocity[0],'bone homed x');A.near(bone.vy,velocity[1],'bone homed y');out.fixedReleasedDirection=true;
 A.reset();A.fixture(m.id,3);const front=A.spawn(200,0),rear=A.spawn(420,0);p.target=rear;A.cast(m.id);A.advance(1.5);
 A.assert(front.hp<front.maxHp&&rear.hp===rear.maxHp,'extended bones gained free piercing');out.noPierce=true;return out;
}"""

DENSITY = r"""() => {
 const A=KAcceptance,p=A.p();A.reset();const m=A.fixture('naruto-kimimaro-bracken',5);p.target=A.spawn(200,0);
 A.cast(m.id);A.advance(4.7);A.fields();const single={...G.KimimaroArt.debugLast};
 A.assert(single.forestColumns===96&&single.secondaryParticles<=20,'single mixed forest density/budget '+JSON.stringify(single));
 A.reset();A.fixture(m.id,5);p.target=A.spawn(200,0);const owners=[p,...Array.from({length:3},()=>G.SelfClones.summon(p))];
 A.assert(owners.every(Boolean),'native clones missing');
 for(const actor of owners)for(const move of actor.moves)move.t=999;
 A.advance(.11); // Native selection/clone setup has the same .10s exit pose.
 // Explicit shared engine casts isolate simultaneous-owner rendering budgets;
 // automatic targeting is independently exercised by the forty range casts.
 A.resume();try{for(const actor of owners){const move=actor.moves.find(v=>v.id===m.id);move.t=0;
  A.assert(G.DigimonSkills.cast(actor,move),'native owner forest cast failed '+owners.indexOf(actor))}}finally{A.pause()}
 A.advance(4.7);A.fields();const multiple={...G.KimimaroArt.debugLast};
 const forests=A.K.renderStates().filter(s=>s.forest).length;
 A.assert(forests===4&&multiple.forestColumns===96&&multiple.secondaryParticles<=20,'global four-owner budget '+JSON.stringify({forests,multiple}));
 return {single,forests,multiple};
}"""

STAGES = r"""() => {
 const A=KAcceptance,p=A.p();A.reset();const m=A.fixture('naruto-kimimaro-bracken');
 const victims=Array.from({length:6},(_,i)=>A.spawn((i+.75)*m.radius/6,0)),logs=victims.map(A.watch);
 p.target=victims[0];A.cast(m.id);const action=A.action(),counts=[],waves=[.48,.80,1.12,1.44,1.76,2.08];
 A.assert(action.hitTimes.length===6,'forest must have six stages');
 let age=0;
 for(let i=0;i<waves.length;i++){
   A.advance(waves[i]-.01-age);age=waves[i]-.01;
   A.assert(logs[i].length===0,'outer enemy hit before wave '+i);
   A.advance(.02);age+=.02;
   A.assert(logs.slice(0,i+1).every(h=>h.length===1)&&logs.slice(i+1).every(h=>!h.length),'wrong wave damage boundary '+i);
   A.fields();counts.push(G.KimimaroArt.debugLast.forestColumns);
 }
 A.advance(2.7-age);A.fields();counts.push(G.KimimaroArt.debugLast.forestColumns);
 A.assert(counts.at(-1)===96&&counts[1]<counts.at(-1),'forest did not grow gradually');
 A.assert(counts.every((n,i)=>i===0||n>=counts[i-1]),'forest shrank before final growth');
 A.advance(.51);A.fields();A.assert(!A.action()&&G.KimimaroArt.debugLast.forestColumns===0,'forest did not clear at 3.2 seconds');
 A.assert(logs.every(h=>h.length===1),'later wave repeated damage');
 return {waves,columns:counts,hits:logs.map(h=>h.length),cleanup:true};
}"""

SCENE = r"""({origin}) => {
 const A=KAcceptance,p=A.p();A.reset();Object.assign(G.World,A.nativeWorld);p.x=origin.x;p.y=origin.y;
 G.Camera.x=p.x;G.Camera.y=p.y;const m=A.fixture('naruto-kimimaro-bracken',5);
 let count=0;for(let ring=1;ring<=3;ring++)for(let n=0;n<18;n++){
  const angle=n*Math.PI/9+ring*.25,r=ring*115,x=p.x+Math.cos(angle)*r,y=p.y+Math.sin(angle)*r;
  if(G.World.isFree(x,y,12,true)&&!G.World.isWall(x,y)){A.spawn(x,y);count++}}
 A.assert(count>=3,'terrain scene lacks native targets');A.cast(m.id);A.advance(4.7);A.fields();
 return {nativeTerrain:true,spawned:count,...G.KimimaroArt.debugLast};
}"""


def main():
    game.OUT.mkdir(parents=True, exist_ok=True)
    report={'sourceHashes':game.runtime_hashes(),'assets':game.asset_inventory(),'viewports':{},'errors':[],'failures':[]}
    effects=report['assets']['sheets']['effects']
    assert effects['source']=='redrawn/kimimaro-effects-v5.png', 'forest must load the reviewed mixed atlas'
    assert 0<effects['transferBytes']<=512*1024, 'forest effect atlas exceeds its transfer budget'
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=game.CHROME,headless=True)
        for label,viewport,mobile in [('desktop',{'width':1280,'height':900},False),('mobile',{'width':390,'height':844},True)]:
            context=browser.new_context(viewport=viewport,is_mobile=mobile,has_touch=mobile,service_workers='block')
            page=context.new_page()
            page.on('pageerror',lambda e:report['errors'].append(str(e)))
            result=report['viewports'][label]={}
            try:
                frame=game.boot(page,label)
                origin=frame.evaluate('({x:G.Game.player.x,y:G.Game.player.y})')
                frame.evaluate('''() => {const A=KAcceptance,reset=A.reset;A.reset=()=>{
                    reset();const p=A.p();p.baseAtk=1;p.atkMul=1;p.buffs.atk.n=0;
                    A.near(p.atk,1,'controlled range fixture attack');
                }}''')
                for name,check in [('ranges',RANGES),('boundaries',BOUNDARIES),('bullets',BULLETS),('density',DENSITY),('stages',STAGES)]:
                    print(label,name,flush=True)
                    try:result[name]=frame.evaluate(check)
                    except Exception as error:report['failures'].append(f'{label}:{name}: {error}')
                result['scene']=frame.evaluate(SCENE,{'origin':origin})
                page.wait_for_timeout(80)
                page.screenshot(path=str(game.OUT/f'{label}-dense-forest-game.png'))
            except Exception as error:report['failures'].append(f'{label}: {error}')
            finally:context.close()
        browser.close()
    report['sourceHashesAfter']=game.runtime_hashes()
    if report['sourceHashesAfter']!=report['sourceHashes']:report['failures'].append('runtime sources changed during acceptance')
    report['ok']=not(report['failures'] or report['errors'])
    path=game.OUT/'report-ranges.json'
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'ok':report['ok'],'failures':report['failures'],'report':str(path)},ensure_ascii=True))
    if not report['ok']:raise SystemExit(1)


if __name__=='__main__':
    main()
