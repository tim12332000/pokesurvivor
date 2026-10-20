"""Lethal Reverse Lotus victims remain hittable until the finisher, with a native hit total."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME, HARNESS
from test_rock_lee import SETUP

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.omx/state/lee-finisher-hold'
URL='http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW&test=lee-finisher-hold'

HELPERS=r"""() => {
 const A=Acceptance,p=A.p();p.level=12;p.xp=0;p.xpNext=G.Player.xpFor(12);
 for(const id of ['naruto-lotus','naruto-reverse-lotus','naruto-gates']){const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(card&&card.apply(p)!==false,'learn '+id)}
 const text=G.FX.dmgText,drop=G.Pickups.dropXp;
 G.FX.dmgText=function(x,y,value,...args){const r=A.hold;if(r&&x===r.e.x&&typeof value==='number')r.texts.push({value,owned:!!G.NarutoLee.active?.primaryHit});return text.call(this,x,y,value,...args)};
 G.Pickups.dropXp=function(x,y,xp,...args){const r=A.hold;if(r&&x===r.e.x&&y===r.e.y)r.drops.push(xp);return drop.call(this,x,y,xp,...args)};
 A.holdFixture=(level=5,quantity=0,kind='weak',id='naruto-reverse-lotus')=>{
   A.leeArena();G.Pickups.clear();G.Weather.reset();p.statsTaken.quantity=0;
   const m=A.select(id);while(m.lvl<level){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);A.assert(card&&card.apply(p)!==false,'upgrade hold skill')}
   for(let n=0;n<quantity;n++){let card;for(let k=0;k<150&&!card;k++)card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:quantity');A.assert(card,'quantity card');card.apply(p)}
   p.maxHp=1000000;p.hp=10;p.percentHealthDamage=.01;p.lifestealRate=.01;p.critChance=1;
   const e=A.spawn(35,0),side=A.spawn(35+m.radius*.7,0);e.hp=kind==='weak'||kind==='shield'?1:1000000;e.maxHp=1000000;e.xp=7;
   if(kind==='shield')e.shield=1000000000;
   side.hp=side.maxHp=10000000;const ledger=[],texts=[],drops=[];
   for(const enemy of [e,side]){const hurt=enemy.hurt;enemy.hurt=function(...args){ledger.push({primary:this===e,amount:args[0],maxHp:this.maxHp,owned:args[6]===p,critical:args[5]==='crit'});return hurt.apply(this,args)}}
   const r={m,e,side,ledger,texts,drops,kind,before:{hp:p.hp,credit:p.dmgDealt,kills:p.kills,xp:p.xp}};A.hold=r;p.target=e;p.aim=0;A.actualCast(id);r.f=G.NarutoLee.active;return r;
 };
 A.holdStep=(dt=.005)=>{A.resume();try{G.EnemyMgr.update(dt,[p]);G.Combat.tick(dt,p,0);G.Combat.updateFields(dt);p.anim.update(dt);G.FX.update(dt)}finally{A.pause()}};
 A.holdPhase=phase=>{for(let n=0;n<1000&&G.NarutoLee.active?.phase!==phase;n++)A.holdStep();A.assert(G.NarutoLee.active?.phase===phase,'missing hold phase '+phase)};
 A.hudTotal=()=>{
   const canvas=document.createElement('canvas');canvas.width=innerWidth;canvas.height=innerHeight;const ctx=canvas.getContext('2d'),texts=[],fill=ctx.fillText.bind(ctx);
   ctx.fillText=function(value,x,y,...args){texts.push({value:String(value),x,y,font:ctx.font});return fill(value,x,y,...args)};G.HUD.draw(ctx,innerWidth,innerHeight,p,{time:30});
   const total=texts.find(t=>t.value.includes('\u7e3d\u50b7\u5bb3'));A.assert(total&&total.y>50&&total.y<innerHeight-30,'combo total HUD missing or outside safe view');
   const owner=A.p(),groupCount=owner.slots.length+owner.moves.filter(m=>m.passive&&!owner.slots.some(group=>group.includes(m))).length;
   if(G.Touch.active){const controls=G.Touch.controlLayout(innerWidth,innerHeight,Math.max(1,groupCount));A.assert(total.y<=controls.bar.y-15&&total.font.includes('16px'),'touch combo total overlaps equipment/skill bar or lacks readable font')}
   else A.assert(total.y<=innerHeight-110&&total.font.includes('18px'),'desktop combo total overlaps active skill name or lacks readable font');
   const summary=G.NarutoLee.comboSummary;A.assert(total.value.includes(String(summary.totalHits))&&total.value.includes(summary.totalDamage.toLocaleString('zh-TW')),'HUD total differs from actual combo summary');return total;
 };
}"""

MATRIX=r"""() => {
 const A=Acceptance,p=A.p(),L=G.NarutoLee,out=[];
 for(const [level,quantity,air] of [[1,0,5],[5,2,15],[5,20,33]]){
   const r=A.holdFixture(level,quantity),f=r.f;let heldFrames=0;
   for(let n=0;n<1000&&L.active;n++){
     A.holdStep();
     const live=L.comboSummary,liveNumbers=r.texts.filter(t=>t.owned);
     if(live)A.assert(live.totalHits===liveNumbers.length&&live.totalDamage===liveNumbers.reduce((sum,t)=>sum+t.value,0),'live cumulative total lagged actual native hits');
     if(!r.midHUD&&f.phase==='combo'&&f.ticks>=Math.ceil(air/2))r.midHUD=A.hudTotal();
     if(['lift','combo','descent'].includes(f.phase)){
       A.assert(L.pendingDefeat(r.e)&&!r.e.dead&&r.e.hp===1&&r.e.anim.cur!=='Faint','native lethal hit ended victim early');
       A.assert(!r.drops.length&&p.kills===r.before.kills&&p.xp===r.before.xp,'early loot/XP or kill before landing');heldFrames++;
     }
   }
   G.EnemyMgr.update(.001,[p]);const own=r.ledger.filter(h=>h.owned),primary=own.filter(h=>h.primary),numbers=r.texts.filter(t=>t.owned).map(t=>t.value),summary=L.comboSummary;
   A.assert(!L.active&&f.age<=3.3+1e-8&&r.e.dead&&!L.pendingDefeat(r.e),'victim did not die at completed landing');
   A.assert(primary.length===air+2&&numbers.length===air+2&&heldFrames>100,'held target missed real hits/numbers');
   const sum=primary.reduce((s,h)=>s+Math.round(h.amount+h.maxHp*.01),0),shown=numbers.reduce((s,d)=>s+d,0);
   A.assert(summary&&Object.isFrozen(summary)&&summary.finished&&summary.totalHits===air+2&&summary.totalDamage===sum&&shown===sum,'integer cumulative total does not match native hit numbers');
   const raw=own.reduce((s,h)=>s+h.amount+h.maxHp*.01,0),near=(a,b)=>Math.abs(a-b)<Math.max(1,Math.abs(b))*1e-8;
   A.assert(own.every(h=>h.critical)&&near(p.dmgDealt-r.before.credit,raw)&&near(p.hp-r.before.hp,raw*.01*G.NarutoGates.healingMultiplier(p)),'held hits duplicated crit/percent credit/lifesteal');
   A.assert(r.drops.length===1&&r.drops[0]===7&&p.kills===r.before.kills+1,'final reward was not exactly once');
   G.EnemyMgr.update(.01,[p]);r.e.die();A.assert(r.drops.length===1&&p.kills===r.before.kills+1,'repeat native cleanup rewarded twice');
   A.assert(r.ledger.filter(h=>!h.primary&&h.owned).length===1,'landing AOE did not occur exactly once');
   out.push({air,hits:primary.length,totalDamage:sum,shownSum:shown,rawCredit:raw,healed:p.hp-r.before.hp,age:f.age,heldFrames,drops:r.drops.slice(),midHUD:r.midHUD,hud:A.hudTotal()});
 }
 return out;
}"""

EXTRAS=r"""() => {
 const A=Acceptance,p=A.p(),L=G.NarutoLee,out={};
 for(const kind of ['survivor','shield']){
   const r=A.holdFixture(5,0,kind);A.advance(4);A.assert(!r.e.dead&&!L.pendingDefeat(r.e)&&!r.drops.length,'nonlethal/shield target was forcibly killed');out[kind]={hp:r.e.hp,summary:L.comboSummary};
 }
 let r=A.holdFixture(5,0,'survivor');A.holdPhase('combo');const before={...L.comboSummary};
 r.e.hurt(2000000,'#fff',0,0,0,null,null);A.assert(L.pendingDefeat(r.e)&&r.e.hp===1&&!r.e.dead,'other incoming lethal damage escaped hold');
 A.assert(L.comboSummary.totalDamage===before.totalDamage&&L.comboSummary.totalHits===before.totalHits,'external damage inflated owned HUD total');
 const x=r.e.x,y=r.e.y;r.e.spd=180;let strikes=0;const strike=r.e.strike;r.e.strike=function(...args){strikes++;return strike.apply(this,args)};
 const radius=r.e.r;r.e.r=60;G.EnemyMgr.update(.2,[p]);G.Combat.resolve(.01,p,0);r.e.r=radius;
 A.assert(r.e.x===x&&r.e.y===y&&!strikes&&r.e.touchCd>0,'pending-defeat victim continued AI/contact attacks');out.pendingAI=true;
 for(let n=0;n<1000&&L.active;n++)A.holdStep();A.assert(r.e.dead&&r.drops.length===1,'externally lethal victim did not finish normally');out.externalNotCounted=true;
 // Final totals persist for a full simulated second, freezing while paused.
 const final={...L.comboSummary};G.Combat.updateFields(.5);A.assert(L.comboSummary.totalDamage===final.totalDamage,'pause expired final total');
 A.resume();G.Combat.updateFields(.6);A.pause();A.assert(L.comboSummary?.finished,'final total expired too soon');
 A.resume();G.Combat.updateFields(.41);A.pause();A.assert(!L.comboSummary,'final total did not expire after one second');out.finalTTL=true;
 for(const reason of ['clear','wall','owner-death']){
   r=A.holdFixture(5,0);A.holdPhase('lift');A.assert(L.pendingDefeat(r.e),'release fixture not pending');
   if(reason==='clear')G.Combat.clearFields(p);if(reason==='wall')G.World.isWall=()=>true;if(reason==='owner-death')p.dead=true;
   if(reason!=='clear')A.advance(.001);G.EnemyMgr.update(.001,[p]);
   A.assert(!L.active&&r.e.dead&&r.drops.length===1&&p.kills===r.before.kills+1&&!L.comboSummary,'cancel failed to release exactly once '+reason);p.dead=false;p.hp=p.maxHp;
 }out.cancelRelease=true;
 for(const stashed of [false,true]){
   r=A.holdFixture(5,0);A.holdPhase('lift');const world=G.World,target=r.e,progress=G.Progress.kill;let progressKills=0;
   G.Progress.kill=function(enemy,...args){if(enemy===target)progressKills++;return progress.call(this,enemy,...args)};
   try{if(stashed)G.EnemyMgr.stash();G.World={...world};A.advance(.001);if(stashed)G.EnemyMgr.restore();G.EnemyMgr.update(.001,[p]);
     A.assert(!r.drops.length&&p.kills===r.before.kills&&!progressKills&&!L.comboSummary,'discarded old-world target polluted new rewards/stats');
     A.assert(G.EnemyMgr.get(target.id)!==target&&!G.EnemyMgr.all().includes(target)&&!G.EnemyMgr.queryCircle(target.x,target.y,300).includes(target),'discarded target remained in byId/list/grid or returned from stash');
   }finally{G.Progress.kill=progress;G.World=world}
 }out.worldDiscard=true;out.stashedDiscard=true;
 r=A.holdFixture(1,0,'weak','naruto-lotus');A.advance(.3);A.assert(r.e.dead&&!L.pendingDefeat(r.e)&&r.drops.length===1,'normal Front Lotus gained finisher hold');out.normalFront=true;
 A.leeArena();G.Pickups.clear();const ordinary=A.spawn(35,0);ordinary.hp=1;ordinary.hurt(2);A.assert(ordinary.dead&&!L.pendingDefeat(ordinary),'ordinary lethal hit gained hold');out.ordinary=true;
 r=A.holdFixture(5,0,'survivor');r.e.remote=true;A.holdPhase('combo');G.EnemyMgr.removeRemote(r.e.id,true);
 A.assert(r.e.dead&&!L.pendingDefeat(r.e)&&!r.drops.length,'remote target was held/rewarded locally');out.remote=true;
 return out;
}"""

def main():
    OUT.mkdir(parents=True,exist_ok=True);report={'errors':[],'failedRequests':[],'viewports':{}}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=CHROME,headless=True)
            for mobile in (False,True):
                label='mobile' if mobile else 'desktop';ctx=browser.new_context(locale='zh-TW',viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
                page=ctx.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)));page.on('response',lambda r:report['failedRequests'].append(r.url) if r.status>=400 and '127.0.0.1' in r.url else None)
                page.goto(URL);page.wait_for_function("window.PS_REDRAWN_READY&&G.NarutoLee?.pendingDefeat&&document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30006"]').click();page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function('G.Game.player?.dex===30006&&G.Game.state==="playing"')
                page.evaluate('()=>G.Sprites.preload([19])');page.evaluate(HARNESS);page.evaluate(SETUP);page.evaluate(HELPERS)
                result={'matrix':page.evaluate(MATRIX)};report['viewports'][label]=result
                page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');page.screenshot(path=str(OUT/f'{label}-final-total.png'))
                if mobile:
                    page.set_viewport_size({'width':844,'height':390});page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');result['landscapeHUD']=page.evaluate('Acceptance.hudTotal()');page.screenshot(path=str(OUT/'landscape-final-total.png'));page.set_viewport_size({'width':390,'height':844})
                result['heldMidair']=page.evaluate(r"""() => {
                  const A=Acceptance,L=G.NarutoLee,r=A.holdFixture(5,2);
                  for(let n=0;n<1000&&L.active?.ticks<8;n++)A.holdStep();
                  A.assert(L.active?.phase==='combo'&&L.active.ticks===8&&L.pendingDefeat(r.e)&&r.e.hp===1&&!r.e.dead&&r.e.anim.cur!=='Faint','midair evidence is not a live held victim');
                  A.assert(L.liftFor(r.e)>100&&!r.drops.length,'held victim stopped following airborne combo or rewarded early');
                  return {airHits:L.active.ticks,victimHP:r.e.hp,dead:r.e.dead,animation:r.e.anim.cur,lift:L.liftFor(r.e),summary:{...L.comboSummary},hud:A.hudTotal()};
                }""")
                page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                page.screenshot(path=str(OUT/f'{label}-held-midair.png'))
                result['heldMidair']['continues']=page.evaluate(r"""before => {
                  const A=Acceptance,L=G.NarutoLee;
                  for(let n=0;n<300&&L.active?.ticks<=8;n++)A.holdStep();
                  A.assert(L.pendingDefeat(A.hold.e)&&A.hold.e.hp===1&&!A.hold.e.dead&&L.comboSummary.totalHits>before.totalHits&&L.comboSummary.totalDamage>before.totalDamage,'held victim did not continue taking real hits after screenshot');
                  const after={...L.comboSummary};A.advance(4);G.EnemyMgr.update(.001,[A.p()]);return after;
                }""",result['heldMidair']['summary'])
                result['extras']=page.evaluate(EXTRAS)
                result['newOwner']=page.evaluate(r"""() => {const A=Acceptance,p=A.p(),L=G.NarutoLee;A.holdFixture(5,0);A.holdPhase('lift');G.Game.toUI();G.Flow.play();G.Game.togglePause();const next=G.Game.player;A.assert(next!==p&&!L.comboSummary&&!G.Pickups.count&&next.kills===0,'old finisher polluted new run');return true}""")
                ctx.close()
            browser.close()
        assert not report['errors'],report['errors'];assert not report['failedRequests'],report['failedRequests'];report['ok']=True
    except Exception as error:report['ok']=False;report['failure']=str(error);raise
    finally:(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'ok':True,'viewports':list(report['viewports']),'evidence':str(OUT)},ensure_ascii=False))

if __name__=='__main__':main()
