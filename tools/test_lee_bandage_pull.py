"""Native Lee cloth pull, ownership, collision, resistant targets and combat parity."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME,URL,HARNESS
OUT=Path(__file__).resolve().parents[1]/'.omx/state/lee-bandage-pull'
CHECK=r"""() => {
 const A=Acceptance,assert=A.assert,L=G.NarutoLee;
 G.Naruto.choose(30006);G.Flow.play();A.pause();A.arena();
 const p=G.Game.player;p.level=20;p.critChance=0;p.percentHealthDamage=0;p.lifestealRate=0;
 p.addMove('naruto-lotus');p.addMove('naruto-reverse-lotus');
 const select=id=>{p.setActive(p.slots.findIndex(g=>g.some(m=>m.id===id)));return p.moves.find(m=>m.id===id)};
 const reset=()=>{L.clear();G.SelfClones.clear();G.EnemyMgr.clear();G.Projectiles.clear();G.FX.clear();p.x=p.y=0;p.hp=p.maxHp;p.dead=false;p.frozen=false;p.invuln=0;p.target=null;for(const m of p.moves)m.t=999};
 const enemy=(x=120,y=0)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:12,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e};
 const step=dt=>{A.resume();try{L.update(dt)}finally{A.pause()}};
 const start=(m,owner=p)=>{assert(L.cast(owner,m),'native lotus cast failed');return L.activeFor(owner)};
 const toWindup=f=>{for(let n=0;n<100&&f.phase==='approach';n++)step(.005);assert(f.phase==='windup','pull did not reach windup')};
 const canvas=document.createElement('canvas');canvas.width=800;canvas.height=600;const ctx=canvas.getContext('2d'),stroke=ctx.stroke;
 let strokes=[],fills=[],stage='air';const fill=ctx.fill;ctx.stroke=function(path){strokes.push({path,style:this.strokeStyle,width:this.lineWidth});return stroke.call(this,path)};
 const clothColors=new Set(['#938b78','#a69b82','#bab19a','#d8ceb5','#c9bea5','#f0e7cf']);
 ctx.fill=function(path,...args){if(clothColors.has(this.fillStyle))fills.push({path,style:this.fillStyle,stage});return fill.call(this,path,...args)};
 const render=()=>{strokes=[];fills=[];for(const enemy of G.EnemyMgr.all()){stage='body';enemy.draw(ctx)}stage='air';G.Combat.drawAirFields(ctx);assert(ctx.globalAlpha===1&&ctx.lineWidth===1&&ctx.shadowBlur===0,'cloth leaked canvas state');return fills.filter(x=>x.style==='#d8ceb5'&&x.stage==='air')};
 const nativePath=window.Path2D;window.Path2D=class extends nativePath{constructor(){super();this.ops=[]}moveTo(...a){this.ops.push(['M',...a]);super.moveTo(...a)}lineTo(...a){this.ops.push(['L',...a]);super.lineTo(...a)}closePath(){this.ops.push(['Z']);super.closePath()}ellipse(...a){this.ops.push(['E',...a]);super.ellipse(...a)}};
 let result;
 try{
  reset();const preferredMove=select('naruto-lotus'),preferredMain=enemy(90,0),assignedSide=enemy(95,10),unassignedA=enemy(115,-30),unassignedB=enemy(120,35);G.LevelUp.STATS.find(s=>s.id==='selfClone').apply(p);const assignedClone=G.SelfClones.actors()[0];assignedClone.target=assignedSide;p.target=preferredMain;const preferred=start(preferredMove);assert(!preferred.boundTargets.includes(assignedSide)&&preferred.boundTargets.includes(unassignedA)&&preferred.boundTargets.includes(unassignedB),'extra ties stole another clones assigned foe despite unassigned alternatives');
  reset();const gm=select('naruto-lotus'),ga=enemy(100,0),gb=enemy(115,-30),gc=enemy(120,35),spare=enemy(140,0),far=enemy(gm.range+25,0),unboundBoss=enemy(140,30);unboundBoss.boss=true;p.target=ga;
  const group=[ga,gb,gc],groupHits=group.map(()=>[]),bossHits=[];
  group.forEach((e,i)=>{const hurt=e.hurt;e.hurt=function(...args){if(args[6]===p)groupHits[i].push(args[0]);return hurt.apply(this,args)}});
  const bossHurt=unboundBoss.hurt;unboundBoss.hurt=function(...args){if(args[6]===p)bossHits.push(args[0]);return bossHurt.apply(this,args)};
  const gf=start(gm);assert(gf.bindLimit===3&&gf.boundTargets.length===3&&group.every(e=>gf.boundTargets.includes(e))&&!gf.boundTargets.includes(far)&&!gf.boundTargets.includes(unboundBoss),'base3 group acquisition failed');
  step(.15);assert(p.x===0&&group.every(e=>L.bound(e))&&gb.x<115&&gc.x<120,'three-target stationary pull failed');
  assert(render().length===3&&fills.some(x=>x.stage==='body'),'each group member lacks ribbon material and body wraps');
  for(let n=0;n<200&&gf.phase!=='lift';n++)step(.005);assert(gf.phase==='lift'&&L.bound(gb)&&L.bound(gc)&&L.liftFor(gb)===0&&L.liftFor(gc)===0,'secondary ground hold lost during primary lift');
  for(let i=0;i<group.length;i++)for(let j=i+1;j<group.length;j++)assert(Math.hypot(group[i].x-group[j].x,group[i].y-group[j].y)>=group[i].r+group[j].r+1.9,'landing slots overlap');
  const sidePositions=[{x:gb.x,y:gb.y},{x:gc.x,y:gc.y}];gb.spd=gc.spd=90;G.EnemyMgr.update(.01,[p]);assert(gb.x===sidePositions[0].x&&gc.y===sidePositions[1].y,'native AI moved secondary holds');
  unboundBoss.x=ga.x+gm.radius*.5;unboundBoss.y=ga.y;const bossAt={x:unboundBoss.x,y:unboundBoss.y};G.EnemyMgr.rebuildGrid();
  while(L.active&&gf.phase!=='slam')step(.005);assert(!gf.boundTargets.length&&!L.bound(gb)&&!L.bound(gc),'slam did not release secondary holds');while(L.active)step(.005);
  const sideDamage=gm.dmg*gf.attack*G.Types.mult(gm.type,gb.types)*G.Weather.mult(gm.type)*.35;
  assert(groupHits[0].length===2&&groupHits[1].length===1&&groupHits[2].length===1&&Math.abs(groupHits[1][0]-sideDamage)<1e-6&&Math.abs(groupHits[2][0]-sideDamage)<1e-6,'side AOE duplicated primary damage or missed original .35');
  assert(bossHits.length===1&&Math.abs(bossHits[0]-sideDamage)<1e-6&&unboundBoss.x===bossAt.x&&unboundBoss.y===bossAt.y&&!L.bound(gb)&&!gf.boundTargets.length,'boss duplicated AOE damage, moved, or completed claims retained');
  reset();select('naruto-lotus');const collisionMain=enemy(100,0),collisionSide=enemy(120,40);p.target=collisionMain;const collisionGroup=start(gm),sideFree=G.World.isFree;
  G.World.isFree=(x,y,r,...args)=>Math.abs(y)>1&&x<106?false:sideFree.call(G.World,x,y,r,...args);
  try{step(.3)}finally{G.World.isFree=sideFree}
  assert(L.active===collisionGroup&&!collisionGroup.boundTargets.includes(collisionSide)&&!L.bound(collisionSide),'blocked side cancelled primary or retained claim');
  L.clear();reset();select('naruto-lotus');const deathMain=enemy(100,0),deathSide=enemy(120,35);p.target=deathMain;const deathGroup=start(gm);step(.15);deathSide.dead=true;step(.01);assert(L.active===deathGroup&&!deathGroup.boundTargets.includes(deathSide)&&!L.bound(deathSide),'dead side cancelled primary or retained claim');
  reset();const m=select('naruto-lotus'),e=enemy(),f=start(m),initial=e.x;
  assert(f.pullable&&f.bandageStage==='extend'&&!L.bound(e),'initial extension ownership');step(.05);assert(p.x===0&&e.x===initial,'cloth extension moved actor or foe');
  assert(render()[0].path.ops.some(x=>x[0]==='L')&&render()[0].path.ops.some(x=>x[0]==='Z'),'wide offwhite cloth material missing');
  step(.10);assert(p.x===0&&e.x<initial&&L.bound(e)&&f.bandageStage==='pull','ordinary target was not pulled to stationary player');
  const paths=render();assert(paths.length===1&&fills.some(x=>x.stage==='body'&&x.style==='#bab19a')&&fills.some(x=>x.stage==='body'&&x.style==='#d8ceb5'),'front/back cloth wrap material missing');
  assert(fills.every(x=>!x.path.ops.some(op=>op[0]==='E')),'cloth reverted to ellipse decals');
  const vertices=paths[0].path.ops.filter(x=>x[0]==='M'||x[0]==='L'),hand=G.AnimationLab.handForLee(p);assert(hand&&Math.abs((vertices[0][1]+vertices.at(-1)[1])/2-hand.x)<1e-6&&Math.abs((vertices[0][2]+vertices.at(-1)[2])/2-hand.y)<1e-6,'cloth missed measured wrist anchor');
  const cachedPath=paths[0].path;assert(render()[0].path===cachedPath,'stationary material geometry was not reused');
  const ordered=[],animDraw=e.anim.draw;let watching=false;const materialFill=ctx.fill;
  ctx.fill=function(path,...args){if(watching&&clothColors.has(this.fillStyle))ordered.push('cloth');return materialFill.call(this,path,...args)};
  e.anim.draw=function(...args){ordered.push('sprite');return animDraw.apply(this,args)};
  watching=true;e.draw(ctx);watching=false;e.anim.draw=animDraw;ctx.fill=materialFill;
  assert(ordered.indexOf('sprite')>0&&ordered.lastIndexOf('cloth')>ordered.indexOf('sprite'),'wrap is not drawn behind/body/infront');
  const pausedMaterial=JSON.stringify(render().map(x=>x.path.ops));L.update(.1);assert(JSON.stringify(render().map(x=>x.path.ops))===pausedMaterial,'paused cloth moves');
  // Native timers advance while AI, contact and separation cannot fight the pull.
  e.slow=.3;e.slowT=1;e.burn=1;e.burnT=2;e.burnTick=.5;e.poison=1;e.poisonT=2;e.poisonTick=.6;e.spd=90;e.shield=50;e.shieldT=.01;
  const held={x:e.x,y:e.y,slowT:e.slowT,burnT:e.burnT,poisonT:e.poisonT,jumpLift:e.jumpLift};
  enemy(e.x+1,e.y);G.EnemyMgr.update(.02,[p]);
  assert(e.shield===0&&e.shieldT<=0,'bound shield timer failed to expire');
  assert(e.x===held.x&&e.y===held.y&&e.slowT<held.slowT&&e.burnT<held.burnT&&e.poisonT<held.poisonT&&e.jumpLift===held.jumpLift,'native timers or separation fought binding');
  const liquid=G.World.isLiquid,effect=G.World.liquidEffect,lavaHp=e.hp;e.lavaTick=.001;G.World.isLiquid=()=>true;G.World.liquidEffect=()=>({dmg:true,every:1,color:'#f80'});try{e.update(.02,p)}finally{G.World.isLiquid=liquid;G.World.liquidEffect=effect}assert(e.hp<lavaHp&&L.bound(e),'bound enemy skipped native lava damage');
  e.x=1;e.y=0;G.EnemyMgr.rebuildGrid();const hp=p.hp;A.resume();try{G.Combat.resolve(.01,p,0)}finally{A.pause()}assert(p.hp===hp,'bound target contact still damaged player');
  e.x=held.x;e.y=held.y;toWindup(f);assert(p.x===0&&Math.hypot(e.x,e.y)<=p.r+e.r+12.001,'pull did not stop at contact reach');
  step(.03);const heldPath=render()[0].path;step(.002);assert(render()[0].path===heldPath,'held cloth rebuilds geometry every simulation tick');
  const touch= L.bound(e);L.clear(p);assert(touch&&!L.bound(e),'clear retained control claim');const x=e.x;e.spd=90;G.EnemyMgr.update(.02,[p]);assert(e.x!==x,'native AI did not resume after clear');
  // Full-radius collision checks abort without crossing terrain.
  reset();select('naruto-lotus');const wallTarget=enemy(),wall=start(m),isFree=G.World.isFree;let samples=[];
  G.World.isFree=(x,y,r,...args)=>{samples.push({x,y,r});return x>=96?isFree.call(G.World,x,y,r,...args):false};
  try{step(.4)}finally{G.World.isFree=isFree}
  assert(!L.active&&!L.bound(wallTarget)&&wallTarget.x>=96&&p.x===0,'pull crossed obstacle or retained control');
  assert(samples.every(s=>s.r===wallTarget.r)&&samples.slice(1).every((s,i)=>Math.abs(s.x-samples[i].x)<=4.001),'pull collision sampling/radius incorrect');
  const resistant=[];
  for(const flag of ['boss','elite','legend','judge']){reset();select('naruto-lotus');const e=enemy();e[flag]=true;const f=start(m);step(.05);assert(!f.pullable&&p.x>0&&e.x===120&&!L.bound(e)&&L.liftFor(e)===0,'resistant target was pulled/lifted '+flag);resistant.push(flag)}
  reset();select('naruto-lotus');const airborne=enemy();airborne.jump={sx:120,sy:0,tx:140,ty:0,t:0,dur:1};const flight=start(m);assert(!flight.pullable&&!L.bound(airborne),'jumping target bound');airborne.update(.05,p);assert(airborne.jump.t===.05&&airborne.jumpLift>0,'native jump lifecycle frozen');
  // Damage ratios, upgraded hit count, cooldown snapshot and reverse deadline.
  const damage=[];
  for(const id of ['naruto-lotus','naruto-reverse-lotus'])for(const level of [1,5]){
   reset();const move=select(id);while(move.lvl<level)G.Moves.levelUp(move);const e=enemy(),ledger=[],hurt=e.hurt;e.hurt=function(...args){if(args[6]===p)ledger.push(args[0]);return hurt.apply(this,args)};
   const f=start(move),cd=move.cd;let n=0;while(L.active&&n++<1000)step(.005);
   assert(!L.active&&f.move.cd===cd&&move.cd===cd,'cooldown or completion changed');
   const ratios=id==='naruto-lotus'?[.2,.8]:[.1,...Array.from({length:f.comboHits},(_,i)=>.12*1.1**(i+1)),.3];
   const base=move.dmg*f.attack*G.Types.mult(move.type,e.types)*G.Weather.mult(move.type);
   assert(ledger.length===ratios.length&&ledger.every((d,i)=>Math.abs(d-base*ratios[i])<1e-6),'native skill damage changed');
   if(id==='naruto-reverse-lotus')assert(f.age<=3.3+1e-7,'reverse exceeded 3.3s');
   damage.push({id,level:move.lvl,hits:ledger.length,age:f.age,cd});
  }
  reset();const qmove=select('naruto-reverse-lotus');G.LevelUp.STATS.find(s=>s.id==='quantity').apply(p);G.LevelUp.STATS.find(s=>s.id==='quantity').apply(p);const qenemy=enemy();enemy(115,-30);enemy(120,35);enemy(125,-50);p.target=qenemy;const qf=start(qmove);assert(qf.bindLimit===4&&qf.boundTargets.length===4,'twoquantitycards did not grow binding3to4');while(L.active)step(.005);assert(qf.comboHits===20&&qf.totalHits===22&&qf.age<=3.3+1e-7,'LV5 Q2 native 22hit contract failed');
  // Pause, switch, owner death, target death and world/scene clear release claims.
  reset();select('naruto-lotus');const pausedEnemy=enemy(),paused=start(m);step(.15);const pausedX=pausedEnemy.x;L.update(.2);assert(pausedEnemy.x===pausedX&&L.active===paused,'pause advanced pull');
  p.setActive(p.slots.findIndex(g=>g.some(x=>x.id==='naruto-lee')));assert(!L.active&&!L.bound(pausedEnemy),'switch retained uncommitted pull');
  for(const cause of ['owner','target','scene','world']){reset();select('naruto-lotus');const e=enemy(),f=start(m);step(.15);if(cause==='owner')p.dead=true;else if(cause==='target')e.dead=true;else if(cause==='scene')G.Combat.clearFields(p);else f.world={};step(.01);assert(!L.active&&!L.bound(e),'claim survived '+cause)}
  reset();select('naruto-lotus');const launchedEnemy=enemy(),launched=start(m);for(let i=0;i<200&&launched.phase!=='lift';i++)step(.005);assert(launched.phase==='lift','launch fixture');p.setActive(p.slots.findIndex(g=>g.some(x=>x.id==='naruto-lee')));assert(L.active===launched,'switch cancelled launched lotus');while(L.active)step(.01);
  reset();select('naruto-lotus');const jumping=enemy(),jchain=start(m);jumping.jump={sx:120,sy:0,tx:140,ty:0,t:0,dur:1};assert(!L.bound(jumping),'extension grabbed newly airborne target');step(.02);jumping.update(.02,p);assert(!jchain.pullable&&jumping.jump.t>0&&jumping.jumpLift>0,'extension froze newly started native jump');
  // Claims are actor-scoped and skip an already reserved ordinary target.
  reset();select('naruto-lotus');const first=enemy(90,0);enemy(95,-25);enemy(100,-40);enemy(105,-50);const second=enemy(115,65);enemy(120,70);G.LevelUp.STATS.find(s=>s.id==='selfClone').apply(p);const clone=G.SelfClones.actors()[0];clone.x=clone.y=0;p.target=first;const real=start(m);clone.target=first;const copy=start(clone.activeMove(),clone);assert(real.target===first&&copy.target===second,'two actors controlled same enemy');
  const camera={x:G.Camera.x,y:G.Camera.y};step(.15);assert(p.x===0&&clone.x===0&&L.bound(first)&&L.bound(second),'actors failed independent pulls');assert(G.Camera.x===camera.x&&G.Camera.y===camera.y,'clone pull moved camera');const cloneHp=clone.hp;second.x=clone.x+1;second.y=clone.y;first.x=250;G.EnemyMgr.rebuildGrid();A.resume();try{G.Combat.resolve(.01,p,0)}finally{A.pause()}assert(clone.hp===cloneHp,'bound target hit clone through native contact');
  L.clear(p);assert(!L.bound(first)&&L.bound(second)&&L.activeFor(clone)===copy,'clearing real pull destroyed clone control');L.clear(clone);
  for(const cloneFirst of [false,true]){
   reset();const sharedMove=select('naruto-reverse-lotus'),assignedEnemies=[enemy(60,0),enemy(75,15),enemy(90,30)];
   G.LevelUp.STATS.find(s=>s.id==='selfClone').apply(p);G.LevelUp.STATS.find(s=>s.id==='selfClone').apply(p);const actors=[p,...G.SelfClones.actors()];
   actors.forEach((actor,i)=>{actor.x=actor.y=0;actor.target=assignedEnemies[i]});
   for(const actor of (cloneFirst?[actors[1],actors[2],p]:actors))start(actor===p?sharedMove:actor.activeMove(),actor);
   assert(actors.every((actor,i)=>L.activeFor(actor)?.target===assignedEnemies[i]&&L.activeFor(actor).boundTargets.length===1),'group extras stole another actors assigned primary');
  }
  reset();select('naruto-lotus');const one=enemy();start(m);G.LevelUp.STATS.find(s=>s.id==='selfClone').apply(p);const blocked=G.SelfClones.actors()[0];assert(!L.canCast(blocked,blocked.activeMove()),'occupied sole target allowed second claim');
  reset();select('naruto-lotus');const boss=enemy();boss.boss=true;start(m);G.LevelUp.STATS.find(s=>s.id==='selfClone').apply(p);const bossCopy=G.SelfClones.actors()[0];assert(L.canCast(bossCopy,bossCopy.activeMove()),'boss improperly reserved by ordinary pull claim');
  reset();select('naruto-lotus');const capMain=enemy(125,0);enemy(120,-40);enemy(120,45);p.target=capMain;const capture=start(m);step(.16);p.frozen=true;
  window.LeeClothCapture={
   reset(opened=false,boss=false){
    reset();if(opened&&!p.hasMove('naruto-gates'))p.addMove('naruto-gates');const move=select('naruto-lotus');
    const primary=enemy(125,0);if(boss)primary.boss=true;else{enemy(120,-40);enemy(120,45)}p.target=primary;
    start(move);p.frozen=true;return this.state();
   },
   advance(dt){step(dt);return this.state()},
   phase(name){for(let n=0;n<1000&&L.active?.phase!==name;n++)step(.005);assert(L.active?.phase===name,'capture phase '+name);return this.state()},
   state(){const f=L.active,pose=G.AnimationLab.stateFor(p.anim);return{phase:f?.phase,stage:f?.bandageStage,age:f?.age,targets:f?.boundTargets.length,pose:pose.key,frame:pose.frame,primaryLift:f?.targetLift||0}}
  };
  result={baseBindCount:3,quantity2BindCount:4,reservesOtherActorsAssignedPrimaries:true,groupSideDamageOnce:true,bossSideAoeOnce:true,groupGroundHold:true,groupCollisionIndividualRelease:true,stationaryCaster:true,pullsEnemy:true,clothNative:true,materialPolygons:true,frontBackWraps:true,measuredHandAnchor:true,bodyOcclusion:true,geometryReused:true,liveHoldGeometryReused:true,pauseMaterialStatic:true,nativeStatusTimers:true,shieldExpiry:true,lavaDamage:true,noContactConflict:true,collisionRadius:true,resistant,airborneNative:true,damage,reverseDeadline:true,pauseAndCleanup:true,cloneClaims:true,cloneContact:true,bossShared:true,quantity2Hits:22,launchedSwitchCompletes:true};
 }finally{window.Path2D=nativePath}
 return result;
}"""

def main():
 OUT.mkdir(parents=True,exist_ok=True);report={}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=CHROME,headless=True)
  for mobile in [False,True]:
   context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile)
   page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(URL)
   page.wait_for_function("window.PS_REDRAWN_READY && document.getElementById('boot').classList.contains('hidden')")
   if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
   page.evaluate(HARNESS);page.evaluate('G.Sprites.preload([19],10000)');label='mobile' if mobile else 'desktop';report[label]=page.evaluate(CHECK)
   page.evaluate('G.Combat.updateFields=()=>{};Acceptance.resume()');page.wait_for_timeout(60);page.screenshot(path=str(OUT/f'{label}.png'))
   sequence=[]
   stages=[('unwind','LeeClothCapture.reset();LeeClothCapture.advance(.03)'),('throw','LeeClothCapture.advance(.04)'),('pull','LeeClothCapture.advance(.09)'),('taut',"LeeClothCapture.phase('windup')"),('lift',"LeeClothCapture.phase('lift');LeeClothCapture.advance(.08)"),('peel',"LeeClothCapture.phase('descent');LeeClothCapture.advance(.18)"),('release',"LeeClothCapture.phase('slam');LeeClothCapture.advance(.035)"),('boss','LeeClothCapture.reset(false,true);LeeClothCapture.advance(.15)'),('opened','LeeClothCapture.reset(true);LeeClothCapture.advance(.16)')]
   for name,script in stages:
    state=page.evaluate('() => {Acceptance.pause();'+script+';const state=LeeClothCapture.state();Acceptance.resume();return state}')
    page.wait_for_timeout(35);page.screenshot(path=str(OUT/f'{label}-{name}.png'));sequence.append({'capture':name,**state})
   report[label]['choreography']=sequence
   assert not errors,errors;context.close()
  browser.close()
 (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({'ok':True,**report}))
if __name__=='__main__':main()
