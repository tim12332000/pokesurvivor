"""Native Gaara level growth and slotless quicksand acceptance fixtures."""

GROWTH = r"""() => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,near=(a,b)=>Math.abs(a-b)<1e-5;
 const m=p.moves.find(m=>m.id==='naruto-sand-shield'),snapshot={...m},level=p.level,cd=p.cdMul;
 const out={};
 try {
   m.lvl=1;p.level=12;p.cdMul=1;A.gaaraArena();A.advance(1);
   let s=N.shieldState(p);A.assert(s.capacity===57,'Lv12 stage1 capacity');
   const hp=p.hp;p.invuln=0;p.hurt(20,null,true);s=N.shieldState(p);
   const amount=s.amount,progress=s.progress;p.level=13;A.advance(.000001);s=N.shieldState(p);
   A.assert(s.capacity===58&&near(s.amount,amount+1)&&near(s.progress,progress+.000001/12),'player-level growth reset or refilled shield');
   A.assert(p.hp===hp,'player-level shield growth healed HP');out.playerLevel={capacity:s.capacity,amount:s.amount};
   const before={...s};const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+m.id);
   A.assert(card&&card.apply(p)!==false,'real shield upgrade card missing');s=N.shieldState(p);
   A.assert(s.capacity===86&&near(s.amount,before.amount+28)&&near(s.progress,before.progress),'skill-stage growth reset or refilled shield');
   A.assert(p.hp===hp,'skill-stage shield growth healed HP');out.skillLevel={capacity:s.capacity,amount:s.amount};
   p.invuln=0;p.hurt(s.amount+1,null,true);const damagedHp=p.hp;p.level=14;A.advance(.000001);s=N.shieldState(p);
   A.assert(s.amount===2&&s.capacity===88&&p.hp===damagedHp,'depleted shield growth must grant only capacity difference');
   out.depleted={capacity:s.capacity,amount:s.amount};
 } finally {Object.assign(m,snapshot);p.level=level;p.cdMul=cd;A.gaaraArena()}
 return out;
}"""

PRISON = r"""() => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,id='naruto-sand-prison',near=(a,b)=>Math.abs(a-b)<1e-5,out={};
 const originalLevel=p.level,originalCd=p.cdMul,originalQuantity=p.quantityBonus;
 const wall=G.World.isWall;
 p.level=11;A.assert(!G.Moves.poolFor(p.mon).includes(id)&&!G.LevelUp.offer(p,100).some(c=>c.key==='new:'+id),'prison unlocked before Lv12');
 p.level=12;A.assert(G.Moves.poolFor(p.mon).includes(id),'prison absent from Lv12 pool');
 const slots=p.slots.length,card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);
 A.assert(card&&card.apply(p)!==false,'prison real learn card missing');
 const m=p.moves.find(m=>m.id===id);A.assert(m.passive&&p.moves.length===5&&p.slots.length===slots&&!p.slots.some(s=>s.includes(m)),'fifth passive consumed active slot');
 p.cdMul=1;A.gaaraArena();A.spawn(180,0);A.advance(5.99);
 A.assert(!N.sandPrisonState(p)&&near(N.prisonCooldownState(p).remaining,.01),'passive cast immediately after learn');
 A.advance(.01);A.assert(N.sandPrisonState(p)?.radius===90,'prison did not spawn after six seconds');
 out.slotless=true;
 // Native Enemy.update and knockback, rather than only checking a status flag.
 A.gaaraArena();const e=A.spawn(180,0);e.spd=60;A.advance(6);
 const field=N.sandPrisonState(p),x=e.x,y=e.y;e.kx=100;e.ky=50;
 A.assert(N.rooted(e),'ordinary ground enemy was not rooted');A.resume();try{e.update(.1,p)}finally{A.pause()}
 A.assert(e.x===x&&e.y===y&&e.kx===0&&e.ky===0,'native rooted enemy still moved/knocked back');
 const age=N.sandPrisonState(p).age,progress=N.prisonCooldownState(p).progress;
 G.Combat.updateFields(1);A.assert(N.sandPrisonState(p).age===age&&N.prisonCooldownState(p).progress===progress,'pause advanced prison');
 out.root={dx:e.x-x,dy:e.y-y,pause:true};
 // Three victims spread across the circle, with a fourth beyond its boundary.
 A.gaaraArena();const es=[A.spawn(180,0),A.spawn(240,0),A.spawn(180,60),A.spawn(280,0)];
 const hits=es.map(()=>0),owners=es.map(()=>true);es.forEach((e,i)=>{const hurt=e.hurt;e.hurt=function(...args){hits[i]++;owners[i]&&=args[6]===p;return hurt.apply(this,args)}});
 A.advance(9);const damage=es.map(e=>100000-e.hp),expected=Math.round(12*p.atk*G.Types.mult(m.type,es[0].types)*G.Weather.mult(m.type))*6;
 A.assert(damage.slice(0,3).every(n=>n===expected)&&damage[3]===0&&hits.slice(0,3).every(n=>n===6)&&hits[3]===0,'large-dt circle damage/ticks wrong '+JSON.stringify({damage,hits,expected}));
 A.assert(owners.every(Boolean)&&!N.sandPrisonState(p)&&es.every(e=>!N.rooted(e)),'expired prison retained control or lost ownership');out.circle={damage,hits};
 // Boss resistance uses the stronger native slow without overwriting its timer.
 A.gaaraArena();const boss=A.spawn(180,0,true);boss.spd=100;boss.flying=false;boss.bossInit();boss.ai.mode='close';boss.ai.modeT=100;boss.ai.cd=100;A.advance(6);
 const speed=G.Weather.speedFor(boss.types),bx=boss.x;A.resume();try{boss.update(.1,p)}finally{A.pause()}
 A.assert(!N.rooted(boss)&&N.prisonSlow(boss)===.35&&near(bx-boss.x,100*.65*speed*1.1*.1),'boss native movement not slowed 35%');
 boss.applySlow(.8,5);const slowT=boss.slowT,bx2=boss.x;A.resume();try{boss.update(.1,p)}finally{A.pause()}
 A.assert(near(bx2-boss.x,100*.2*speed*1.1*.1)&&boss.slow===.8&&near(boss.slowT,slowT-.1),'prison weakened or rewrote external slow');
 G.Combat.clearFields(p);A.assert(boss.slow===.8&&near(boss.slowT,slowT-.1),'cleanup erased external slow');out.boss=true;
 // Airborne victims neither anchor a field nor receive its root or tick damage.
 A.gaaraArena();const ground=A.spawn(180,0),fly=A.spawn(190,0),jump=A.spawn(195,0),lift=A.spawn(200,0);
 fly.flying=true;jump.jump={sx:195,sy:0,tx:260,ty:0,t:0,dur:1};lift.jumpLift=30;
 A.advance(6);A.assert(N.rooted(ground)&&![fly,jump,lift].some(e=>N.rooted(e)||N.prisonSlow(e)),'airborne enemy rooted');
 A.advance(.5);A.assert(ground.hp<100000&&[fly,jump,lift].every(e=>e.hp===100000),'airborne enemy damaged');
 const jumpState=JSON.stringify(jump.jump);const liftAmount=lift.jumpLift;G.Combat.clearFields(p);
 A.assert(JSON.stringify(jump.jump)===jumpState&&lift.jumpLift===liftAmount,'cleanup modified native jump/lift');out.airborne=true;
 // Targeting respects range/LOS, and missed intervals do not bank future casts.
 for(const reason of ['range','wall','air']){
   A.gaaraArena();const target=A.spawn(reason==='range'?320:180,0);if(reason==='air')target.flying=true;
   if(reason==='wall')G.World.isWall=(x,y)=>x>=90&&x<=94;
   try{A.advance(6);A.assert(!N.sandPrisonState(p),'invalid target spawned field '+reason)}finally{G.World.isWall=wall}
 }
 A.gaaraArena();A.advance(12);A.spawn(180,0);A.advance(.1);A.assert(!N.sandPrisonState(p),'missed intervals caused immediate banked cast');A.advance(5.9);A.assert(N.sandPrisonState(p),'fresh cooldown did not produce field');
 A.gaaraArena();const target=A.spawn(180,0);A.advance(6);const hidden=A.spawn(240,0);G.World.isWall=(x,y)=>x>=210&&x<=214;
 try{A.advance(.5);A.assert(target.hp<100000&&hidden.hp===100000&&!N.rooted(hidden),'field damaged/rooted through wall')}finally{G.World.isWall=wall}
 out.targeting=true;
 // Real cooldown card changes the periodic passive clock; quantity never multiplies fields.
 const counts={...p.statsTaken};p.statsTaken={...counts,cd:0};p.cdMul=1;
 try{let cd;for(let n=0;n<40&&!cd;n++)cd=G.LevelUp.offer(p,100).find(c=>c.key==='stat:cd');A.assert(cd&&cd.apply(p)!==false,'prison real cooldown card missing');
   A.gaaraArena();p.quantityBonus=20;A.spawn(180,0);A.advance(5.51);A.assert(!N.sandPrisonState(p),'cooldown card prison early');A.advance(.01);A.assert(N.sandPrisonState(p),'cooldown card ignored');A.advance(5.52);A.assert(N.sandPrisonState(p)&&near(N.sandPrisonState(p).age,0),'periodic prison doubled or missed');
 }finally{p.statsTaken=counts;p.cdMul=1;p.quantityBonus=0}
 out.cooldownCard=true;
 for(let level=1;level<=5;level++){
   if(level>1){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);A.assert(card&&card.apply(p)!==false,'prison upgrade missing '+level)}
   A.assert(m.lvl===level&&m.dmg===[12,15,15,18,24][level-1]&&m.radius===[90,90,105,105,120][level-1]&&m.cd===6,'prison stage contract '+level);
 }
 out.stages=5;
 for(const reason of ['clear','owner-death','world','owner','unlearn']){
   A.gaaraArena();const e=A.spawn(180,0);A.advance(6);A.assert(N.rooted(e),'cleanup fixture missing '+reason);
   const world=G.World,game=G.Game,moves=p.moves;
   if(reason==='clear')G.Combat.clearFields(p);if(reason==='owner-death')p.dead=true;if(reason==='world')G.World={...world};
   if(reason==='owner')G.Game={...game,get state(){return game.state},player:{...p}};if(reason==='unlearn')p.moves=p.moves.filter(x=>x!==m);
   try{A.advance(.01);A.assert(!N.sandPrisonState(p)&&!N.rooted(e),'prison cleanup leaked '+reason)}finally{G.World=world;G.Game=game;p.dead=false;p.moves=moves}
 }
 out.cleanup=true;p.level=originalLevel;p.cdMul=originalCd;p.quantityBonus=originalQuantity;A.gaaraArena();return out;
}"""


def capture_prison(page, label, out):
    result = page.evaluate(r"""() => {
      const A=Acceptance,p=A.p();p.cdMul=1;A.gaaraArena();A.select('naruto-gaara');
      A.spawn(170,0);A.spawn(205,20);A.spawn(140,-25);A.advance(6.8);
      const s=G.NarutoGaara.sandPrisonState(p);A.assert(s&&s.radius===120,'missing native prison screenshot fixture');
      return {x:s.x,y:s.y,radius:s.radius,age:s.age,ticks:s.ticks};
    }""")
    page.locator('#game').screenshot(path=str(out / f'{label}-effect-sand-prison.png'))
    return result


RESTART = r"""() => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara;A.gaaraArena();p.cdMul=1;const e=A.spawn(180,0);A.advance(6);
 A.assert(N.sandPrisonState(p)&&N.rooted(e),'native restart fixture missing');
 G.Game.startRun();
 A.assert(G.Game.player!==p&&!N.sandPrisonState(p)&&!N.rooted(e)&&!G.Game.player.hasMove('naruto-sand-prison'),'native restart retained field or passive');
 G.Combat.updateFields(.01);A.pause();
 A.assert(!N.sandPrisonState()&&!N.prisonCooldownState(),'native restart recreated learned passive');return true;
}"""
