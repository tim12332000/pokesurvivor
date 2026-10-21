"""Behavior fixtures shared by the normal Gaara browser acceptance runner."""

PROJECTILES = r"""() => {
 const A=Acceptance,p=A.p(),out={},N=G.NarutoGaara,near=(a,b)=>Math.abs(a-b)<1e-5;
 const damage=(m,e)=>m.dmg*p.atk*G.Types.mult(m.type,e.types)*G.Weather.mult(m.type);
 A.gaaraArena();const far=A.spawn(230,0),side=A.spawn(230,45);p.target=far;
 let raw=0;const hurt=far.hurt;far.hurt=function(amount,...args){raw+=amount;return hurt.call(this,amount,...args)};
 const m=A.actualCast('naruto-gaara');A.assert(m.dmg===28,'starter nominal damage');A.advance(.13);
 A.assert(N.bullets.length===1&&far.hp===100000,'sand bullet did not launch before impact');
 const bullet=N.bullets[0],x=bullet.x;A.advance(.02);
 A.assert(bullet.x>x&&far.hp===100000&&side.hp===100000,'bullet teleported or dealt fan damage');
 const frozen=bullet.x;G.Combat.updateFields(.4);A.assert(bullet.x===frozen,'paused independent bullet moved');
 A.finish();A.assert(N.bullets.length>0,'action completion deleted flying sand bullets');A.advance(1);
 A.assert(near(raw,damage(m,far))&&near(100000-far.hp,Math.round(damage(m,far)/3)*3)&&side.hp===100000,'three bullet damage or splash wrong '+JSON.stringify({actual:100000-far.hp,expected:damage(m,far),raw,side:100000-side.hp,count:m.count,atk:p.atk,bullets:N.bullets.length}));
 A.assert(N.bullets.length===0,'spent bullets retained');out.flight={damage:100000-far.hp,nominal:m.dmg};
 // Physical interception and swept collision must work at large frame deltas.
 for(const large of [false,true]){
   A.gaaraArena();const target=A.spawn(230,0);p.target=target;A.actualCast('naruto-gaara');
   const blocker=A.spawn(100,0);blocker.r=2;
   if(large)A.advance(2);else {A.finish();A.advance(1)}
   A.assert(blocker.hp<100000&&target.hp===100000,'sand pierced small blocker, large dt='+large);
   out['intercept-'+large]=100000-blocker.hp;
 }
 for(const large of [false,true]){
   A.gaaraArena();const target=A.spawn(230,0);p.target=target;A.actualCast('naruto-gaara');
   const wall=G.World.isWall;G.World.isWall=(x,y)=>x>=90&&x<=94;
   try{if(large)A.advance(2);else {A.finish();A.advance(1)}}finally{G.World.isWall=wall}
   A.assert(target.hp===100000&&N.bullets.length===0,'sand tunneled through wall, large dt='+large);
 }
 A.gaaraArena();const target=A.spawn(230,0);p.target=target;A.actualCast('naruto-gaara');A.advance(.13);
 target.y=100;G.EnemyMgr.rebuildGrid();A.advance(2);
 A.assert(target.hp===100000&&N.bullets.length===0,'sand homed or exceeded range');
 for(const reason of ['clear','owner-death','world','owner']){
   A.gaaraArena();const e=A.spawn(230,0);p.target=e;A.actualCast('naruto-gaara');A.advance(.13);
   A.assert(N.bullets.length>0,'missing cleanup bullet');const world=G.World,game=G.Game;
   if(reason==='clear')G.Combat.clearFields(p);
   if(reason==='owner-death')p.dead=true;
   if(reason==='world')G.World={...world};
   if(reason==='owner')G.Game={...game,get state(){return game.state},player:{...p}};
   try{A.advance(.01);A.assert(N.bullets.length===0,'bullet leaked '+reason)}finally{G.World=world;G.Game=game;p.dead=false}
   A.advance(1);A.assert(e.hp===100000,'cancelled bullet delayed damage '+reason);
 }
 return {...out,wall:true,cleanup:true,pause:true,noHoming:true};
}"""

PRIORITY = r"""() => {
 const A=Acceptance,p=A.p(),out=[];
 for(const strong of ['elite','boss','legend','judge']){
   A.gaaraArena();const normal=A.spawn(50,0),elite=A.spawn(150,0),hidden=A.spawn(210,0,true);elite[strong]=true;p.target=normal;
   const wall=G.World.isWall;G.World.isWall=(x,y)=>x>=180&&x<=185;
   try{A.actualCast('naruto-sand-coffin');A.assert(G.NarutoGaara.active(p).target===elite,'coffin missed visible '+strong);A.finish()}
   finally{G.World.isWall=wall}
   A.assert(elite.hp<100000&&normal.hp===100000&&hidden.hp===100000,'coffin priority splashed');out.push(strong);
 }
 A.gaaraArena();const near=A.spawn(60,0),far=A.spawn(120,0);p.target=far;A.actualCast('naruto-sand-coffin');
 A.assert(G.NarutoGaara.active(p).target===near,'coffin did not fall back to nearest ordinary enemy');A.finish();
 return out;
}"""

TIMING = r"""() => {
 const A=Acceptance,p=A.p(),out={},N=G.NarutoGaara,near=(a,b)=>Math.abs(a-b)<1e-5;
 const visualVictims=()=>{
   const vfx=G.NarutoSandVFX,ground=vfx.drawGround,air=vfx.drawAir,seen={};
   const ctx=document.createElement('canvas').getContext('2d');
   vfx.drawGround=function(ctx,f){if(f.kind==='gaara-tsunami')seen.ground=f.victims.slice();return ground.call(this,ctx,f)};
   vfx.drawAir=function(ctx,f){if(f.kind==='gaara-tsunami')seen.air=f.victims.slice();return air.call(this,ctx,f)};
   try{G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx)}finally{vfx.drawGround=ground;vfx.drawAir=air}
   A.assert(seen.ground&&seen.air,'missing native tsunami VFX pass');return seen;
 };
 const assertVisual=(expected,label)=>{
   const seen=visualVictims();for(const [layer,victims] of Object.entries(seen))
     A.assert(victims.length===expected.length&&expected.every(e=>victims.includes(e)),label+' visual victims '+layer);
   out[label]=Object.fromEntries(Object.entries(seen).map(([layer,victims])=>[layer,victims.length]));
 };
 A.gaaraArena();const stay=A.spawn(90,0),leave=A.spawn(120,25),late=A.spawn(150,170);p.target=stay;
 const m=A.actualCast('naruto-sand-tsunami'),total=m.dmg*p.atk*G.Types.mult(m.type,stay.types)*G.Weather.mult(m.type);
 A.assert(m.cd===8&&m.dmg===240,'tsunami nominal balance');
 for(let n=0;n<200&&N.active(p)?.phase!=='burial';n++)A.advance(.01);
 const wave=Math.round(total*.25),burial=Math.round(total*.75);
 const f=N.active(p);A.assert(f?.phase==='burial','missing burial phase');
 A.assert(near(100000-stay.hp,wave)&&near(100000-leave.hp,wave),'wave damage not 25 percent');
 leave.y=200;late.y=20;G.EnemyMgr.rebuildGrid();A.advance(.01);
 A.assert(leave.slow===0,'leaving sand kept Gaara slow');
 assertVisual([stay],'burial-wrap');
 A.assert(f.waveHits.has(leave)&&f.victims.includes(leave),'visual filtering erased historical wave hit');
 A.advance(.47);A.assert(N.active(p)?.phase==='burial'&&near(100000-stay.hp,wave),'burial did not hold full half second');
 A.advance(.021);A.assert(N.active(p)?.phase==='impact'&&N.active(p).burialImpact,'missing synchronized burial impact event');
 A.assert(near(100000-stay.hp,wave+burial)&&near(100000-leave.hp,wave)&&late.hp===100000,'impact hit departed or late enemy');
 assertVisual([stay],'impact-wrap');
 leave.y=25;G.EnemyMgr.rebuildGrid();assertVisual([stay],'returned-after-impact');
 A.assert(f.waveHits.has(leave)&&f.victims.includes(leave)&&!f.burialHits.has(leave),'returned enemy lost wave history or gained fake burial');
 const hp=stay.hp;A.advance(.10);A.assert(N.active(p)?.phase==='impact'&&stay.hp===hp,'impact hold or single damage wrong');
 A.advance(.03);A.assert(N.active(p)?.phase==='recovery'&&stay.hp===hp,'impact recovery timing');
 assertVisual([stay],'recovery-wrap');
 A.finish();A.advance(1);A.assert(stay.hp===hp,'tsunami dealt repeated burial');out.damage=[stay,leave,late].map(e=>100000-e.hp);
 return out;
}"""

SHIELD_CONTEXT = r"""() => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,out=[];
 const contexts=[{fromX:100,fromY:0},{fromX:0,fromY:100},{fromX:-100,fromY:0},{fromX:0,fromY:-100},{vx:-10,vy:0},null];
 for(const [i,context] of contexts.entries()){
   A.gaaraArena();A.select('naruto-sand-shield');A.advance(.001);const hp=p.hp;p.invuln=0;p.hurt(2,null,true,context);
   const s=N.shieldState(p),aim=s.flashAim,expected=[0,Math.PI/2,Math.PI,-Math.PI/2,0,null][i];
   A.assert(p.hp===hp&&s.flash>0,'directional hit bypassed shield');
   A.assert(expected===null?aim===null:Math.abs(Math.atan2(Math.sin(aim-expected),Math.cos(aim-expected)))<1e-6,'shield source direction '+i+' '+aim);
   out.push({context,aim});
 }
 A.gaaraArena();A.select('naruto-sand-shield');A.advance(1);p.invuln=0;p.hurt(8,null,true,{fromX:100,fromY:0});
 const before=N.shieldState(p);A.select('naruto-sand-coffin');
 const hp=p.hp;p.invuln=0;p.hurt(3,null,true,{fromX:100,fromY:0});
 A.assert(p.hp===hp-3&&!N.shieldState(p),'unselected shield absorbed native damage or remained visible');
 A.advance(15);A.select('naruto-sand-shield');const after=N.shieldState(p);
 A.assert(after.amount===before.amount&&Math.abs(after.progress-before.progress)<1e-6,'switching shield refilled capacity or advanced frozen clock');
 A.advance(.25);A.assert(N.shieldState(p).progress>before.progress,'reselected shield clock failed to resume');
 out.push({unselectedHurt:true,frozenProgress:true,noFreeRefill:true});
 return out;
}"""
