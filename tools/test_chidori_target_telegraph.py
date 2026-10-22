"""Native concurrent Chidori flash: original cadence, anchored snapshots and cleanup."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT=Path(__file__).resolve().parents[1]/'.omx/state/chidori-target-telegraph'
CHECK=r"""() => {
 const A=Acceptance,assert=A.assert,N=G.NarutoChidori;
 G.Naruto.choose(30002);G.Flow.play();A.pause();A.arena();
 const p=G.Game.player,m=p.activeMove();p.critChance=0;p.percentHealthDamage=0;p.lifestealRate=0;
 const enemy=(x,y,hp=100000)=>{const e=new G.Enemy({dex:19,hp,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e};
 const reset=()=>{N.clear();G.SelfClones.clear();G.EnemyMgr.clear();G.Projectiles.clear();G.FX.clear();p.x=p.y=0;p.hp=p.maxHp;p.dead=false;p.frozen=false;p.invuln=0;p.target=null;for(const move of p.moves)move.t=999};
 const step=dt=>{A.resume();try{N.update(dt)}finally{A.pause()}};
 const start=(move=m)=>{assert(N.cast(p,move),'native cast failed');return N.active};
 const canvas=document.createElement('canvas');canvas.width=800;canvas.height=600;const ctx=canvas.getContext('2d');
 const NativePath=window.Path2D,hash=G.U.hash;let hashCalls=0,draws=[];
 window.Path2D=class extends NativePath{constructor(){super();this.points=[]}moveTo(x,y){this.points.push([x,y]);super.moveTo(x,y)}lineTo(x,y){this.points.push([x,y]);super.lineTo(x,y)}};
 G.U.hash=function(...args){hashCalls++;return hash.apply(this,args)};
 const stroke=ctx.stroke;ctx.stroke=function(path){draws.push({path,points:path.points||[],alpha:this.globalAlpha,style:this.strokeStyle,width:this.lineWidth});return stroke.call(this,path)};
 const render=()=>{draws=[];ctx.clearRect(0,0,800,600);G.Combat.drawAirFields(ctx);assert(ctx.globalAlpha===1&&ctx.lineWidth===1&&ctx.shadowBlur===0,'flash leaked canvas state');return draws.filter(d=>d.style==='#ffe878'&&Math.abs(d.width-1.65/(G.Camera.scale||1))<.001)};
 const near=(a,b)=>Math.abs(a-b)<1e-6;
 const translate=ctx.translate;let translations=[];ctx.translate=function(x,y){translations.push([x,y]);return translate.call(this,x,y)};
 const groundAnchor=()=>{translations=[];G.Combat.drawGroundFields(ctx);return translations.at(-1)};
 const emit=c=>{if(c.wait>0)step(c.wait);assert(c.phase==='dash','original charge failed to end')};
 let result;
 try{
   reset();const a=enemy(120,25),b=enemy(145,-45),c=start(),origin={x:p.x,y:p.y};
   const originalCharge=m.charge||0;assert(c.wait===originalCharge,'added initial telegraph delay');
   if(originalCharge>0){step(originalCharge/2);assert(p.x===0&&p.y===0&&!render().length,'flash emitted before original charge finished');step(c.wait)}
   assert(c.phase==='dash','dash did not begin after original charge');
   const line=render()[0];assert(line&&line.alpha>.8,'zero-age full yellow bolt missing');
   assert(near(line.points[0][0],origin.x)&&near(line.points[0][1],origin.y-G.LIFT*.5),'emission origin wrong');
   assert(near(line.points.at(-1)[0],a.x)&&near(line.points.at(-1)[1],a.y-G.LIFT*.5),'zero-age bolt did not immediately reach target');
   const beforeHash=hashCalls,endpoint=line.points.at(-1).slice(),hp=a.hp;step(.01);assert(p.x!==0&&render().length===1,'movement did not occur while flash was visible');
   const movedLine=render()[0];assert(movedLine.path===line.path&&hashCalls===beforeHash,'moving actor rebuilt or dragged anchored bolt');
   assert(near(movedLine.points[0][0],origin.x)&&near(movedLine.points.at(-1)[0],endpoint[0]),'flash endpoints followed actor');
   assert(a.hp===hp&&groundAnchor().every((v,i)=>near(v,i?origin.y:origin.x)),'flash dealt damage or range followed dash');
   let n=0;while(c.phase==='dash'&&n++<100)step(.001);
   assert(c.hitCount===1&&c.phase==='retarget','first hit did not enter original retarget');
   const expectedFollow=Math.max(N.config.minRetargetDelay,N.config.retargetDelay*N.config.retargetDelayDecay**c.hitCount);
   assert(near(c.wait,expectedFollow)&&c.wait<.05,'follow-up retains added delay');
   const at={x:p.x,y:p.y};step(c.wait+.005);assert(c.phase==='dash'&&p.x!==at.x,'leftover frame time was discarded at retarget boundary');
   const replaced=render()[0];assert(replaced&&near(replaced.points[0][0],at.x),'new dash failed to replace flash at new start');
   N.clear(p);assert(!render().length,'clear retained flash');
   // Very near lethal targets must retain emitted visual after arrival/death.
   reset();const nearEnemy=enemy(10,0,1),short=start({...m,charge:0});assert(render()[0]?.points.length>1,'instant cast lacked full bolt');
   step(.001);assert(nearEnemy.dead&&render().length===1&&short.phase==='return','fast lethal contact erased emitted flash');
   step(N.config.flashDuration);assert(!render().length&&N.active,'flash lifetime depends on return animation');
   N.clear(p);p.x=35;assert(groundAnchor().every((v,i)=>near(v,i?p.y:p.x)),'cleared ground anchor remained stale');
   // Invalid targets before emission safely reacquire without producing a line.
   reset();const doomed=enemy(100,0),safe=enemy(140,30),invalid=start({...m,charge:.05});doomed.hp=0;step(.001);
   assert(invalid.target===safe&&invalid.wait===.05&&!render().length,'invalid pre-emission target did not reacquire');
   safe.x=m.range+20;step(.001);assert(!N.active&&!render().length,'out-of-range target retained effect');
   // Rendering must not change damage, timing, combo limits, cooldown or immunity.
   function combat(draw){
     reset();const enemies=[enemy(100,0),enemy(135,30)],credit=p.dmgDealt,trace=[];const chain=start();let oldHits=0,tick=0;
     while(N.active&&tick++<3000){step(.002);if(draw)render();if(chain.hitCount!==oldHits){trace.push({tick,hits:chain.hitCount,x:p.x,y:p.y,wait:chain.wait});oldHits=chain.hitCount}}
     assert(!N.active&&chain.hitCount===chain.limit,'combo did not finish at native limit');
     return {tick,trace,hp:enemies.map(e=>e.hp),damage:p.dmgDealt-credit,limit:chain.limit,cooldown:p.moves.find(x=>x.id===m.id).t,invuln:p.invuln};
   }
   const noDraw=combat(false),withDraw=combat(true);assert(JSON.stringify(noDraw)===JSON.stringify(withDraw),'rendering altered combat cadence or damage');
   reset();enemy(120,0);const switched=start();emit(switched);p.addMove('naruto-fireball');assert(!N.active&&!render().length&&!groundAnchor(),'switch retained flash/range anchor');
   p.setActive(p.slots.findIndex(g=>g.includes(m)));reset();enemy(120,0);emit(start());p.dead=true;assert(!render().length,'dead owner retained flash');step(.001);p.dead=false;
   reset();enemy(120,0);emit(start());G.Combat.clearFields(p);assert(!N.active&&!render().length,'scene clear retained flash');
   reset();const first=enemy(120,0),second=enemy(120,110);
   G.LevelUp.STATS.find(s=>s.id==='selfClone').apply(p);const clone=G.SelfClones.actors()[0];clone.x=clone.y=0;clone.target=second;
   G.LevelUp.STATS.find(s=>s.id==='selfClone').apply(p);const twin=G.SelfClones.actors().at(-1);twin.x=twin.y=0;twin.target=first;
   const real=start();assert(N.cast(clone,clone.activeMove())&&N.cast(twin,twin.activeMove()),'clone cast failed');
   const copy=N.activeFor(clone);assert(real.target===first&&copy.target===second&&N.activeFor(twin).target===first,'assigned targets not isolated');
   if(real.wait>0)step(real.wait);assert(render().length===3,'actor flash isolation lost');
   N.clear(p);const camera={x:G.Camera.x,y:G.Camera.y};G.Camera.follow(p.x+20,p.y+20,.01);
   assert(N.activeFor(clone)===copy&&render().length===2&&p.invuln===0,'clone flash changed real actor');assert(G.Camera.x!==camera.x||G.Camera.y!==camera.y,'clone held camera');
   N.clear(clone);N.clear(twin);assert(!render().length,'clone cleanup retained flash');
   reset();const inside=enemy(0,100),outside=enemy(0,(G.SelfClones.leash?.soft||320)+10);G.LevelUp.STATS.find(s=>s.id==='selfClone').apply(p);const leashed=G.SelfClones.actors()[0];leashed.x=leashed.y=0;leashed.target=inside;
   assert(N.cast(leashed,leashed.activeMove()),'leash cast failed');const leash=N.activeFor(leashed);for(let i=0;i<100&&!leash.hitCount;i++)step(.01);assert(leash.hitCount===1&&leash.phase==='return'&&outside.hp===100000,'clone reacquired outside soft leash');
   reset();enemy(130,40);const capture=start();emit(capture);step(.01);p.frozen=true;
   result={originalCharge,originalFollowup:expectedFollow,instantFullBolt:true,movementConcurrent:true,anchoredFlash:true,flashSurvivesFastKill:true,flashExpires:true,renderCombatEquivalent:true,comboTicks:withDraw.tick,comboHits:withDraw.limit,damage:withDraw.damage,invalidReacquires:true,switchDeathSceneCleanup:true,cloneIsolation:true,cloneSoftLeash:true,rangeAnchored:true};
 }finally{window.Path2D=NativePath;G.U.hash=hash}
 return result;
}"""

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 report={}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=CHROME,headless=True)
  for mobile in [False,True]:
   context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile)
   page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(URL);page.wait_for_function("window.PS_REDRAWN_READY && document.getElementById('boot').classList.contains('hidden')")
   if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
   page.evaluate(HARNESS);label='mobile' if mobile else 'desktop';report[label]=page.evaluate(CHECK)
   # Render native dash pose while holding simulation at a visible 10ms flash age.
   page.evaluate('G.Combat.updateFields=()=>{};Acceptance.resume()');page.wait_for_timeout(60)
   page.screenshot(path=str(OUT/f'{label}.png'));assert not errors,errors;context.close()
  browser.close()
 (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps({'ok':True,**report}))

if __name__=='__main__':main()
