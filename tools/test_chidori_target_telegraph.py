"""Native Chidori target acquisition, stationary telegraph and actor isolation."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT=Path(__file__).resolve().parents[1]/'.omx/state/chidori-target-telegraph'
CHECK=r"""() => {
 const A=Acceptance,assert=A.assert,N=G.NarutoChidori;
 G.Naruto.choose(30002);G.Flow.play();A.pause();A.arena();
 const p=G.Game.player,m=p.activeMove();p.critChance=0;p.percentHealthDamage=0;p.lifestealRate=0;
 const enemy=(x,y)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e};
 const reset=()=>{N.clear();G.SelfClones.clear();G.EnemyMgr.clear();G.Projectiles.clear();G.FX.clear();p.x=p.y=0;p.hp=p.maxHp;p.dead=false;p.frozen=false;p.invuln=0;p.target=null;for(const move of p.moves)move.t=999};
 const step=dt=>{A.resume();try{N.update(dt)}finally{A.pause()}};
 const start=()=>{assert(N.cast(p,m),'native cast failed');return N.active};
 const canvas=document.createElement('canvas');canvas.width=800;canvas.height=600;const ctx=canvas.getContext('2d');
 const NativePath=window.Path2D,hash=G.U.hash;let hashCalls=0,draws=[];
 window.Path2D=class extends NativePath{constructor(){super();this.points=[];this.starts=[]}moveTo(x,y){this.starts.push(this.points.length);this.points.push([x,y]);super.moveTo(x,y)}lineTo(x,y){this.points.push([x,y]);super.lineTo(x,y)}};
 G.U.hash=function(...args){hashCalls++;return hash.apply(this,args)};
 const stroke=ctx.stroke;ctx.stroke=function(path){draws.push({path,points:path.points||[],starts:path.starts||[],alpha:this.globalAlpha,style:this.strokeStyle,width:this.lineWidth});return stroke.call(this,path)};
 const render=()=>{draws=[];ctx.clearRect(0,0,800,600);G.Combat.drawAirFields(ctx);assert(ctx.globalAlpha===1&&ctx.lineWidth===1&&ctx.shadowBlur===0,'telegraph leaked canvas state');return draws.filter(d=>d.style==='#ffe878')};
 const near=(a,b)=>Math.abs(a-b)<1e-6;
 const translate=ctx.translate;let translations=[];ctx.translate=function(x,y){translations.push([x,y]);return translate.call(this,x,y)};
 const groundAnchor=()=>{translations=[];G.Combat.drawGroundFields(ctx);return translations.at(-1)};
 let result;
 try{
   reset();const a=enemy(120,25),b=enemy(145,-45),c=start(),origin={x:p.x,y:p.y},hp=a.hp,credit=p.dmgDealt;
   assert(c.target===a&&c.phase==='charge'&&c.wait>=.2&&c.wait>=(m.charge||0),'initial acquisition or windup duration');
   step(.08);p.update(.01);assert(p.x===origin.x&&p.y===origin.y&&a.hp===hp&&p.dmgDealt===credit,'windup moved or damaged');
   let line=render().find(d=>near(d.width,1.65/(G.Camera.scale||1)));assert(line,'strong yellow target indicator missing');
   assert(near(line.points[0][0],p.x)&&near(line.points[0][1],p.y-G.LIFT*.5),'telegraph origin wrong');
   assert(near(line.points.at(-1)[0],a.x)&&near(line.points.at(-1)[1],a.y-G.LIFT*.5),'telegraph missed acquired target');
   const length=Math.hypot(a.x-p.x,a.y-p.y),ux=(a.x-p.x)/length,uy=(a.y-p.y)/length;for(const q of line.points){const x=q[0]-p.x,y=q[1]-(p.y-G.LIFT*.5),u=(x*ux+y*uy)/length,v=-x*uy+y*ux;assert(u>=-1e-6&&u<=1.000001&&Math.abs(v)<=24/(G.Camera.scale||1),'target line escaped its bounded corridor')}
   const topology=c.telegraph,hashBefore=hashCalls;a.x=125;a.y=35;render();
   assert(hashCalls===hashBefore&&c.telegraph===topology,'moving target rebuilt cached topology');
   // A closer newcomer must not silently replace the indicated target.
   const newcomer=enemy(45,0);step(c.wait-.001);assert(c.target===a&&c.phase==='charge'&&a.hp===hp,'target changed or hit before windup');
   step(.002);assert(c.phase==='dash'&&c.target===a&&p.x===origin.x,'dash switched target or skipped stationary start');
   step(.005);assert(p.x!==origin.x,'dash never moved');assert(groundAnchor().every((v,i)=>near(v,i?origin.y:origin.x)),'range followed player during dash');
   let n=0;while(c.phase==='dash'&&n++<100)step(.005);
   assert(c.hitCount===1&&a.hp<hp&&c.phase==='aim'&&c.target!==a,'first dash or follow-up acquisition');
   const follow=c.target,followHp=follow.hp,at={x:p.x,y:p.y},wait=c.wait;
   assert(wait>=.2,'follow-up pause too short');step(wait-.001);
   assert(c.phase==='aim'&&p.x===at.x&&p.y===at.y&&follow.hp===followHp,'follow-up moved or hit early');
   step(.002);assert(c.phase==='dash'&&c.target===follow,'follow-up dash lost indicated target');
   assert(!render().some(d=>d.style==='#ffe878'),'target indicator survived into dash');
   N.active.phase='return';N.active.returnFrom={x:p.x,y:p.y};N.active.returnAge=0;step(.01);assert(groundAnchor().every((v,i)=>near(v,i?origin.y:origin.x)),'range moved during return');
   N.clear(p);assert(groundAnchor().every((v,i)=>near(v,i?p.y:p.x)),'range retained origin after cancellation');
   const completed=start();completed.phase='return';completed.dashes=1;completed.returnFrom={x:p.x,y:p.y};completed.returnAge=0;step(N.config.returnDuration);assert(!N.active,'return did not complete');p.x+=30;assert(groundAnchor().every((v,i)=>near(v,i?p.y:p.x)),'completed range retained old anchor');
   const limits={limit:c.limit,hitCount:c.hitCount,firstWait:Math.max(.2,m.charge||0),followWait:wait};
   reset();const doomed=enemy(100,0),safe=enemy(140,30),invalid=start();step(.05);doomed.hp=0;assert(!render().length,'dead target line remained before simulation');step(.01);
   assert(N.active===invalid&&invalid.target===safe&&invalid.wait>=.2&&safe.hp===100000&&p.x===0,'dead target did not reacquire with fresh pause');
   safe.x=m.range+20;step(.01);assert(!N.active&&p.x===0,'out-of-range target kept stale chain');assert(!render().length,'cancelled telegraph retained');
   reset();const off=enemy(100,0);start();off.x=G.Camera.x+G.Camera.w+500;step(.01);assert(!N.active,'out-of-view target kept chain');
   reset();enemy(100,0);start();p.addMove('naruto-fireball');assert(!N.active&&!render().length,'switch retained telegraph');assert(!groundAnchor(),'switched skill retained range anchor');
   p.setActive(p.slots.findIndex(g=>g.includes(m)));reset();enemy(100,0);start();p.dead=true;assert(!render().length,'dead owner retained line');step(.01);assert(!N.active,'dead owner retained chain');p.dead=false;
   reset();enemy(100,0);start();G.Combat.clearFields(p);assert(!N.active&&!render().length,'scene clear retained line');
   // Actor-scoped targeting and no real camera or immunity contamination.
   reset();const first=enemy(120,0),second=enemy(120,110);
   G.LevelUp.STATS.find(s=>s.id==='selfClone').apply(p);const clone=G.SelfClones.actors()[0];assert(clone,'native clone absent');clone.x=0;clone.y=0;clone.target=second;
   G.LevelUp.STATS.find(s=>s.id==='selfClone').apply(p);const twin=G.SelfClones.actors().at(-1);twin.x=0;twin.y=0;twin.target=first;
   start();assert(N.cast(clone,clone.activeMove())&&N.cast(twin,twin.activeMove()),'clone native cast failed');
   const real=N.active,copy=N.activeFor(clone),camera={x:G.Camera.x,y:G.Camera.y};
   assert(real.target===first&&copy.target===second&&N.activeFor(twin).target===first&&copy!==real,'clones ignored distinct assigned targets');
   step(.08);assert(render().filter(d=>near(d.width,1.65/(G.Camera.scale||1))).length===3,'actor indicator absent');
   N.clear(p);G.Camera.follow(p.x+20,p.y+20,.01);assert(!N.active&&N.activeFor(clone)===copy,'clearing real chain damaged clone chain');
   assert(p.invuln===0,'clone windup granted player immunity');assert(G.Camera.x!==camera.x||G.Camera.y!==camera.y,'clone windup locked real camera');
   N.clear(clone);N.clear(twin);assert(!render().length,'clone cleanup retained indicator');
   reset();const inside=enemy(0,100),outside=enemy(0,(G.SelfClones.leash?.soft||320)+10);G.LevelUp.STATS.find(s=>s.id==='selfClone').apply(p);const leashed=G.SelfClones.actors()[0];leashed.x=leashed.y=0;leashed.target=inside;assert(N.cast(leashed,leashed.activeMove()),'leash fixture cast');const leashChain=N.activeFor(leashed);for(let i=0;i<100&&!leashChain.hitCount;i++)step(.01);assert(leashChain.hitCount===1&&leashChain.phase==='return'&&outside.hp===100000,'clone reacquired a foe outside owner soft leash');
   reset();const target=enemy(130,40);const capture=start();step(.08);p.frozen=true;
   result={...limits,stationaryWindup:true,noEarlyDamage:true,lockedTarget:true,movingTargetTracks:true,cachedTopology:true,invalidTargetReacquires:true,followupPause:true,switchClears:true,deathClears:true,sceneClear:true,cloneIsolation:true,twoClonesDistinct:true,cloneSoftLeash:true,rangeAnchoredDuringDashAndReturn:true};
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
   # Render the native scene while leaving the controlled windup paused.
   page.evaluate('G.Combat.updateFields=()=>{};Acceptance.resume()');page.wait_for_timeout(60)
   page.screenshot(path=str(OUT/f'{label}.png'));assert not errors,errors;context.close()
  browser.close()
 (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps({'ok':True,**report}))

if __name__=='__main__':main()
