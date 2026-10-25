"""Six Paths player rescue through native lethal hurt, revive, and real RAF.

The controlled arena opens terrain only. Damage, repair, native death timer,
enemy targeting, hazards and the animation scheduler are never replaced.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame, HARNESS, SETUP as AUTO_SETUP

OUT = Path(__file__).resolve().parents[1] / '.omx/state/pain-player-revive'

SETUP = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain;
 A.reviveFresh=()=>{A.reset();G.Hazards.clear();p.invuln=0;
   p.regenFlat=p.lifestealRate=0; p.item=null;
   const repair=p.moves.find(m=>m.id==='naruto-pain-repair');if(repair)repair.lvl=1;
 };
 A.lethal=()=>{p.invuln=0;p.hurt(p.maxHp+1,null,true);A.assert(p.dead&&p.hp===0,'native lethal damage did not kill Tendo');};
 A.naraka=()=>P.actorsFor(p).find(b=>b.path==='naraka');
 A.rescue=()=>P.playerReviveState(p);
 A.reviveFresh();
}"""

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out={};
 A.reviveFresh();A.lethal();A.assert(P.canRevivePlayer(p),'formed living Naraka cannot rescue');
 A.advance(.01);let s=A.rescue();A.assert(s.waiting&&s.remaining>8.7&&s.remaining<=8.8,'base rescue must wait eight seconds plus .8 '+JSON.stringify(s));
 const remaining=s.remaining;G.Combat.updateFields(2);A.assert(A.rescue().remaining===remaining,'paused repair progressed');
 A.finish(7.8);A.assert(p.dead&&A.rescue().status==='waiting','base repair started early');
 A.finish(.3);A.assert(p.dead&&A.rescue().status==='repair','Naraka repair animation missing');
 for(let i=0;p.dead&&i<90;i++)A.advance();A.assert(!p.dead&&Math.abs(p.hp-p.maxHp)<1e-6,'native rescue must restore full HP');
 A.assert(A.rescue().protection>2.98&&p.invuln>=3,'rescue protection shorter than three seconds');
 const hp=p.hp;p.invuln=0;p.hurt(p.maxHp+1,null,true);A.assert(p.hp===hp&&!p.dead,'protection depends on normal invuln');
 G.Hazards.add({kind:'zone',x:p.x,y:p.y,r:60,delay:.001,dmg:10000,type:'normal',pure:true,color:'#f00'});
 A.resume();G.Hazards.update(.1);A.pause();A.assert(p.hp===hp&&!p.dead,'native ground zone bypassed rescue protection');G.Hazards.clear();
 A.finish(2.99);p.invuln=0;p.hurt(10000,null,true);A.assert(p.hp===hp&&!p.dead,'independent protection expired before 2.99 seconds');
 G.Hazards.add({kind:'zone',x:p.x,y:p.y,r:60,delay:.001,dmg:10000,type:'normal',pure:true,color:'#f00'});
 A.resume();G.Hazards.update(.1);A.pause();G.Hazards.clear();A.assert(p.hp===hp&&!p.dead,'late protected hazard bypassed rescue protection');
 A.finish(.03);A.lethal();A.finish(8.9);A.assert(!p.dead&&p.hp===hp,'second Tendo death cannot be rescued');out.repeat=true;

 A.reviveFresh();const original=p.moves;p.moves=original.filter(m=>m.id==='naruto-pain');p.level=1;
 A.lethal();A.advance();A.assert(P.canRevivePlayer(p)&&A.rescue().remaining>8.7,'Lv1 lacks intrinsic player rescue');
 A.finish(8.9);A.assert(!p.dead&&p.hp===p.maxHp,'unlearned repair cannot rescue player');p.moves=original;out.intrinsic=true;

 A.reviveFresh();A.lethal();A.finish(4);p.revive(.25);const external=p.hp;A.advance();
 A.assert(!A.rescue().waiting,'external native revive left pending repair');A.finish(12);
 A.assert(p.hp===external&&external===p.maxHp*.25,'cancelled rescue changed external quarter-health revive');out.external=true;

 A.reviveFresh();A.lethal();const free=G.World.isFree;G.World.isFree=()=>false;
 try{A.finish(12);A.assert(p.dead&&A.rescue().waiting&&A.rescue().status==='unsafe','unsafe resurrection was not deferred '+JSON.stringify(A.rescue()));}
 finally{G.World.isFree=free}
 A.finish(.3);A.assert(!p.dead&&A.rescue().protection>1.5,'safe retry did not rescue');out.unsafe=true;

 A.reviveFresh();A.lethal();A.advance();const world=G.World;G.World={...world};
 try{A.advance();A.assert(!P.canRevivePlayer(p)&&!P.actorsFor(p).length,'world switch retained rescue');}finally{G.World=world}
 A.reviveFresh();A.lethal();A.advance();G.Combat.clearFields();A.assert(!P.canRevivePlayer(p)&&!A.rescue().waiting,'clear retained pending player rescue');out.cleanup=true;

 A.reviveFresh();const n=A.naraka();n.formed=false;A.lethal();A.assert(!P.canRevivePlayer(p),'unformed Naraka can rescue');A.advance();
 A.assert(!P.actorsFor(p).length,'unformed Naraka prevented terminal cleanup');out.unformed=true;

 A.reviveFresh();A.lethal();A.finish(3);const naraka=A.naraka();naraka.hurt(naraka.maxHp+1,null,true);A.advance();
 A.assert(!P.canRevivePlayer(p)&&!P.actorsFor(p).length,'Naraka death retained pending rescue');A.finish(18);
 A.assert(p.dead&&p.hp===0&&!P.actorsFor(p).length,'dead Naraka naturally resurrected to rescue owner');out.narakaDeath=true;
 A.reviveFresh();return out;
}"""

TIERS = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,moves=p.moves,out={tiers:[]};
 const asura=()=>P.actorsFor(p).find(b=>b.path==='asura');
 function tier(rank,cd){
   p.moves=moves;A.reviveFresh();p.moves=moves.filter(m=>m.id!=='naruto-pain-repair').concat(G.Moves.instance('naruto-pain-repair',rank));p.cdMul=cd;
 }
 function waitForAnimation(period,player){
   A.finish(period-.1);A.assert(player?p.dead:asura().dead,'revived before repair preparation finished');
   A.assert(player?A.rescue().status==='waiting':P.stateFor(p).repair===null,'repair animation began before tier wait');
   let tail=0;while((player?A.rescue().status!=='repair':!P.stateFor(p).repair)&&tail++<20)A.advance();
   A.assert(tail<=12,'repair tier did not start at expected wait');
   A.finish(.79);A.assert(player?p.dead:asura().dead,'repair skipped fixed .8 second animation');
   for(let i=0;(player?p.dead:asura().dead)&&i<5;i++)A.advance();
   A.assert(player?!p.dead:!asura().dead,'repair animation did not finish');
 }
 try{
   for(const [rank,wait] of [[1,8],[2,7],[3,6],[4,5],[5,4]])for(const cd of [1,.5]){
     tier(rank,cd);A.lethal();waitForAnimation(wait*cd,true);
     A.assert(p.hp===p.maxHp&&A.rescue().protection>2.98&&p.invuln>=3,'tier rescue must grant full health and three seconds protection');
     A.assert(P.speedMultiplier(p)===2,'tier rescue lost five second speed');const ownerMax=p.maxHp;
     tier(rank,cd);const b=asura();b.hurt(b.maxHp+1,null,true);A.assert(b.dead,'native support death fixture failed');waitForAnimation(wait*cd,false);
     A.assert(b.hp===b.maxHp&&b.maxHp===p.maxHp*2,'tier repair did not fully restore double-health support');
     out.tiers.push({rank,cd,wait:wait*cd,animation:.8,ownerMax,supportMax:b.maxHp});
   }
   tier(5,1);const b=asura();b.hurt(b.maxHp+1,null,true);A.lethal();A.advance();
   A.assert(!P.stateFor(p).repair&&A.rescue().waiting,'support repair took priority over downed Tendo');
   for(let i=0;p.dead&&i<500;i++)A.advance();A.assert(!p.dead&&p.hp===p.maxHp&&b.dead,'priority rescue also revived a different body');
   p.hp-=20;const hp=p.hp;A.finish(.5);A.assert(p.hp===hp&&!A.rescue().waiting,'completed rescue repeated healing or restarted cooldown');
   A.finish(4.4);A.assert(!b.dead&&b.hp===b.maxHp&&p.hp===hp,'support repair failed to resume after Tendo priority');out.priority=true;
   p.moves=moves;A.reviveFresh();p.moves=moves.filter(m=>m.id!=='naruto-pain-repair');const natural=asura();natural.hurt(natural.maxHp+1,null,true);
   A.finish(15.8);A.assert(natural.dead,'natural support revive became shorter than sixteen seconds');A.finish(.3);A.assert(!natural.dead&&natural.hp===natural.maxHp,'natural sixteen second revive changed');out.naturalSixteenSeconds=true;
   return out;
 }finally{p.moves=moves;p.cdMul=1;A.reviveFresh()}
}"""

SPEED = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out={};
 A.reviveFresh();const originalSpeed=p.spd,originalMul=p.spdMul,originalSlow=p.slowT;
 const beforeCards={...p.statsTaken};
 A.assert(P.speedMultiplier(p)===1,'fresh Pain inherited revive speed');
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:spd');
 A.assert(card,'native movement speed card missing');card.apply(p);
 const normal=p.spd;A.assert(Math.abs(normal-originalSpeed*1.07)<1e-8,'native speed card changed unexpectedly');
 A.lethal();A.assert(P.speedMultiplier(p)===1,'dead player has revive speed');
 A.finish(8.9);A.assert(!p.dead&&P.speedMultiplier(p)===2&&Math.abs(p.spd-normal*2)<1e-8,'Naraka rescue did not double effective card speed');
 out.naraka={normal,revived:p.spd};
 p.slowT=10;A.assert(Math.abs(p.spd-normal)<1e-8,'revive speed bypassed native half-speed slow');p.slowT=0;
 G.Combat.updateFields(10);A.assert(P.speedMultiplier(p)===2,'pause consumed revive speed');
 p.frozen=true;try{A.advance(10);A.assert(P.speedMultiplier(p)===2,'frozen time consumed revive speed')}finally{p.frozen=false}
 A.finish(5);A.assert(P.speedMultiplier(p)===1&&Math.abs(p.spd-normal)<1e-8,'revive speed did not expire');
 A.lethal();p.revive(.5);A.assert(P.speedMultiplier(p)===2,'native external revive did not start speed');
 A.finish(4.9);A.assert(P.speedMultiplier(p)===2,'revive speed ended before five simulation seconds');
 p.revive(.5);A.assert(Math.abs(p.spd-normal*2)<1e-8,'live revive stacked speed');
 A.finish(.11);A.assert(P.speedMultiplier(p)===1,'live revive refreshed five-second timer');
 A.lethal();p.revive(.5);A.finish(.2);A.lethal();
 A.assert(P.speedMultiplier(p)===1,'second death retained active revive speed');
 p.revive(.5);A.assert(P.speedMultiplier(p)===2,'second native revive did not renew speed');
 A.finish(4.9);A.assert(P.speedMultiplier(p)===2,'second revive inherited old expiry');
 A.finish(.11);A.assert(P.speedMultiplier(p)===1,'second revive speed did not expire');
 A.lethal();p.revive(.5);const world=G.World;G.World={...world};
 try{A.assert(P.speedMultiplier(p)===1,'world replacement retained revive speed')}finally{G.World=world}
 G.Combat.clearFields();A.assert(P.speedMultiplier(p)===1,'field clear retained revive speed');
 p.spdMul=originalMul;p.slowT=originalSlow;p.statsTaken=beforeCards;A.reviveFresh();
 A.assert(P.speedMultiplier(p)===1,'new family retained revive speed');
 return {...out,pause:true,frozen:true,fiveSeconds:true,slow:true,repeat:true,noStack:true,cleanup:true};
}"""

LIVE_START = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain;A.reviveFresh();
 for(let i=0;i<10;i++){const c=G.LevelUp.offer(p,100).find(c=>c.key==='stat:cd');A.assert(c,'cooldown card absent '+i);c.apply(p)}
 A.assert(Math.abs(p.cdMul-Math.pow(.92,10))<1e-10,'native cooldown cards not applied');
 const n=A.naraka(),asura=P.actorsFor(p).find(b=>b.path==='asura');
 const enemy=A.spawn(asura.x+100,asura.y);enemy.dmg=0;enemy.spd=0;enemy.behavior='chase';
 for(const b of P.actorsFor(p))b.cooldown=0;A.ready('missiles');
 A.lethal();A.resume();window.RescueLive={started:performance.now(),hp:enemy.hp,enemy,expected:8*p.cdMul+.8,naraka:n,x:p.x,y:p.y};
 return {expected:RescueLive.expected,cdMul:p.cdMul};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for label, viewport, mobile in [('desktop', {'width': 1200, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
                context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
                outer = context.new_page()
                outer.on('pageerror', lambda e: report['errors'].append(str(e)))
                outer.goto(URL)
                page = game_frame(outer)
                enter(page)
                page.evaluate(SETUP)
                result = report['viewports'][label] = {}
                print(label, 'deterministic', flush=True)
                result['checks'] = page.evaluate(CHECK)
                result['tiers'] = page.evaluate(TIERS)
                result['speed'] = page.evaluate(SPEED)
                result['liveSetup'] = page.evaluate(LIVE_START)
                outer.wait_for_timeout(1800)
                result['pastNativeDeathTimer'] = page.evaluate(r"""() => {
                  const A=Acceptance,p=A.p(),P=G.NarutoPain;
                  A.assert(p.dead&&G.Game.state==='playing'&&P.actorsFor(p).length===5,'real RAF ended run at native 1.3s death timer');
                  A.assert(RescueLive.enemy.hp<RescueLive.hp,'helpers stopped fighting while Tendo dead');
                  A.assert(p.x===RescueLive.x&&p.y===RescueLive.y,'downed Tendo moved before repair');
                  A.assert(p.anim.cur==='Faint'&&p.anim.hold&&p.anim.done&&p.anim.frame===3,'support cast replaced held death animation '+p.anim.cur);
                  const draws=[],draw=G.PainArt.draw;
                  G.PainArt.draw=function(ctx,options){draws.push(options);return draw.apply(this,arguments)};
                  try{p.draw(document.createElement('canvas').getContext('2d'))}finally{G.PainArt.draw=draw}
                  const tendo=draws.find(d=>d.path==='tendo');
                  A.assert(tendo?.state==='death'&&G.PainArt.sample('tendo',tendo.state,tendo.time).index===3,'downed Tendo did not draw final lying frame');
                  const n=A.naraka(),hp=n.hp;
                  G.Hazards.add({kind:'zone',x:n.x,y:n.y,r:12,delay:.001,dmg:1,type:'normal',pure:true,color:'#f00'});
                  G.Hazards.update(.02);G.Hazards.clear();
                  A.assert(n.hp<hp,'Naraka became untargetable while Tendo dead');
                  const canvas=document.createElement('canvas');canvas.width=innerWidth;canvas.height=innerHeight;
                  const ctx=canvas.getContext('2d'),texts=[],fill=ctx.fillText.bind(ctx);
                  ctx.fillText=function(text,...args){texts.push(text);return fill(text,...args)};
                  G.HUD.draw(ctx,innerWidth,innerHeight,p,G.Game.st);
                  A.assert(texts.includes('天道倒下，等待地獄道修復'),'native HUD missing player waiting message '+JSON.stringify(texts));
                  A.assert(texts.some(t=>/約.*秒後復活/.test(t)),'native HUD missing rescue countdown '+JSON.stringify(texts));
                  return {state:G.Game.state,rescue:A.rescue(),enemyDamage:RescueLive.hp-RescueLive.enemy.hp,hud:texts};
                }""")
                outer.screenshot(path=str(OUT / f'{label}-waiting.png'))
                page.wait_for_function('!G.Game.player.dead', timeout=12000)
                result['nativeRescue'] = page.evaluate(r"""() => {const A=Acceptance,p=A.p();A.pause();
                  A.assert(G.Game.state==='paused'&&p.hp===p.maxHp,'real RAF rescue failed native full health');
                  A.assert(G.NarutoPain.speedMultiplier(p)===2,'real RAF rescue did not grant doubled movement speed');
                  A.assert((performance.now()-RescueLive.started)/1000>=RescueLive.expected-.1,'real RAF rescue skipped cooldown/animation');
                  return {elapsed:(performance.now()-RescueLive.started)/1000,hp:p.hp,maximum:p.maxHp,state:A.rescue()};
                }""")
                outer.screenshot(path=str(OUT / f'{label}-revived.png'))
                page.evaluate('Acceptance.reviveFresh();Acceptance.lethal();Acceptance.resume()')
                outer.wait_for_timeout(400)
                page.evaluate('Acceptance.naraka().hurt(100000,null,true)')
                page.wait_for_function('G.Game.state==="over"', timeout=6000)
                result['nativeTerminal'] = page.evaluate('({state:G.Game.state,dead:G.Game.player.dead,hp:G.Game.player.hp})')
                result['newRun'] = page.evaluate(r"""() => {const old=G.Game.player;G.Game.startRun();
                  Acceptance.assert(G.Game.player!==old&&!G.NarutoPain.canRevivePlayer(old),'new run retained old owner rescue');
                  return {changedOwner:G.Game.player!==old};}""")
                page.evaluate(HARNESS)
                page.evaluate(AUTO_SETUP)
                page.evaluate(SETUP)
                result['toUI'] = page.evaluate(r"""() => {Acceptance.lethal();Acceptance.advance();G.Game.toUI();
                  Acceptance.assert(!G.NarutoPain.canRevivePlayer(G.Game.player)&&!G.NarutoPain.actorsFor(G.Game.player).length,'return to menu retained pending rescue');return true;}""")
                page.evaluate('G.DB.save.partner=1;G.Game.startRun()')
                page.evaluate(HARNESS)
                result['nonPainStart'] = page.evaluate(r"""() => {const A=Acceptance;A.arena();const p=A.p();
                  A.assert(p.dex===1,'non-Pain starter fixture wrong');A.resume();p.invuln=0;p.hurt(p.maxHp+1,null,true);
                  A.assert(p.dead&&!G.NarutoPain.canRevivePlayer(p),'non-Pain inherited player rescue');
                  p.revive(.5);A.assert(G.NarutoPain.speedMultiplier(p)===1,'non-Pain native revive inherited doubled speed');
                  p.invuln=0;p.hurt(p.maxHp+1,null,true);return {dex:p.dex,dead:p.dead};}""")
                page.wait_for_function('G.Game.state==="over"', timeout=6000)
                result['nonPainEnd'] = page.evaluate('G.Game.state')
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
    except Exception as error:
        report.update(ok=False, failure=str(error))
        raise
    finally:
        (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': report['ok'], 'evidence': str(OUT)}))


def rift_main():
    """Focused native Rift regression; never replace arena or death handlers."""
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'viewports': {}}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for label, viewport, mobile in [('desktop', {'width': 1200, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
                context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
                outer = context.new_page()
                outer.on('pageerror', lambda e: report['errors'].append(str(e)))
                outer.goto(URL)
                page = game_frame(outer)
                enter(page)
                page.evaluate(SETUP)
                result = report['viewports'][label] = {}
                print(label, 'native Rift', flush=True)
                result['sceneCancellation'] = page.evaluate(r"""() => {
                  const A=Acceptance,p=A.p(),P=G.NarutoPain;A.lethal();A.advance();
                  A.assert(P.canRevivePlayer(p),'pending rescue fixture absent');
                  G.Rift.debugArena('normal');
                  A.assert(G.Rift.inArena&&!P.canRevivePlayer(p)&&!P.actorsFor(p).length&&!P.playerReviveState(p).waiting,'native Rift travel retained old pending rescue');
                  G.Game.startRun();return true;
                }""")
                page.evaluate(HARNESS)
                page.evaluate(AUTO_SETUP)
                page.evaluate(SETUP)
                result['arenaStart'] = page.evaluate(r"""() => {
                  const A=Acceptance,p=A.p(),P=G.NarutoPain;
                  G.Rift.debugArena('normal');A.assert(G.Rift.inArena,'native debugArena did not enter');
                  A.finish(1.6);const n=A.naraka();A.assert(n?.formed&&!n.dead,'Naraka failed native arena placement');
                  for(const e of G.EnemyMgr.all()){e.dmg=0;e.shotDmg=0;e.spd=0;}
                  A.lethal();A.advance();A.assert(P.canRevivePlayer(p),'arena Tendo cannot await living Naraka');
                  A.resume();return {arena:G.Rift.inArena,rescue:A.rescue()};
                }""")
                outer.wait_for_timeout(1800)
                result['arenaWait'] = page.evaluate(r"""() => {
                  const A=Acceptance,p=A.p();
                  A.assert(G.Rift.inArena&&G.Game.state==='playing'&&p.dead&&p.hp===0&&A.rescue().waiting,'native Rift ejected or revived Tendo before Naraka rescue');
                  return {arena:G.Rift.inArena,state:G.Game.state,dead:p.dead,hp:p.hp,rescue:A.rescue()};
                }""")
                outer.screenshot(path=str(OUT / f'{label}-rift-waiting.png'))
                page.evaluate('Acceptance.naraka().hurt(100000,null,true)')
                page.wait_for_function('G.Game.state==="over"', timeout=6000)
                result['arenaTerminal'] = page.evaluate(r"""() => {
                  const A=Acceptance,p=A.p();A.assert(p.dead&&p.hp===0,'Rift both-down restored player health');
                  return {state:G.Game.state,dead:p.dead,hp:p.hp};
                }""")
                context.close()
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
    except Exception as error:
        report.update(ok=False, failure=str(error))
        raise
    finally:
        (OUT / 'rift-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': report['ok'], 'evidence': str(OUT / 'rift-report.json')}))


if __name__ == '__main__':
    rift_main() if '--rift-only' in sys.argv else main()
