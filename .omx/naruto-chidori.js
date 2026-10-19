/* Level-based Chidori pursuit is this edition's gameplay adaptation. */
(() => {
  if (G.NarutoChidori) return;
  const config = Object.freeze({ counts: Object.freeze([5,10,15,20,25]), followupRangeMultiplier: 3, endInvulnerability: .3, speed: 1000, retargetDelay: .045, step: 4 });
  const limitOf = move => config.counts[Math.max(0,Math.min(config.counts.length-1,(move?.lvl|0)-1))];
  let chain = null;
  const valid = c => c && c.owner === G.Game.player && c.world === G.World && !c.owner.dead && c.owner.hp > 0;
  const clear = owner => { if (!owner || chain?.owner === owner) chain = null; };
  function end(c) {
    if(chain!==c)return;
    if(valid(c)&&c.dashes>0)c.owner.invuln=Math.max(c.owner.invuln||0,config.endInvulnerability);
    clear();
  }
  const targetAlive = e => e && !e.dead && e.hp > 0 && G.EnemyMgr.all().includes(e);
  const rangeFor = c => c.move.range * (c.hits.size ? config.followupRangeMultiplier : 1);
  function next(c) {
    const pl = c.owner;
    return G.EnemyMgr.all().filter(e => targetAlive(e) && !c.hits.has(e) && Math.hypot(e.x-pl.x,e.y-pl.y) <= rangeFor(c))
      .sort((a,b) => Math.hypot(a.x-pl.x,a.y-pl.y)-Math.hypot(b.x-pl.x,b.y-pl.y))[0];
  }
  function begin(c) {
    if (c.dashes >= c.limit || !(c.target = next(c))) { end(c); return; }
    c.legRange = rangeFor(c); c.dashes++; c.travel = 0; c.phase = 'dash';
    c.owner.cast(c.move);
  }
  function finish(c) {
    if (c.dashes >= c.limit || !next(c)) { end(c); return; }
    c.phase = 'retarget'; c.wait = config.retargetDelay;
  }
  function hit(c, e, dx, dy) {
    c.hits.add(e);
    const m=c.move, pl=c.owner, k=G.Types.mult(m.type,e.types), crit=pl.critChance>0&&Math.random()<pl.critChance;
    const dmg=m.dmg*c.attack*k*G.Weather.mult(m.type)*(crit?1.5:1)*(G.NarutoSupport?.precisionMultiplier(pl,e)||1);
    e.hurt(dmg,'#9feaff',dx,dy,m.knock||0,crit?'crit':G.Types.label(k));
    pl.onDealt(dmg); pl.dmgDealt+=dmg;
    if(m.slow)e.applySlow(m.slow);
    G.FX.slash(pl.x,pl.y-G.LIFT*.5,pl.aim,34,2.2,'#9feaff',m.digiVis);
    finish(c);
  }
  function update(dt) {
    const c=chain;
    if(!valid(c)){clear();return;}
    if(c.phase!=='dash') {c.wait-=dt;if(c.wait<=0)begin(c);return;}
    if(!targetAlive(c.target)){finish(c);return;}
    const pl=c.owner,m=c.move,e=c.target;
    let budget=Math.min(config.speed*dt,c.legRange-c.travel);
    while(budget>0&&chain===c&&c.phase==='dash') {
      const dx=e.x-pl.x,dy=e.y-pl.y,d=Math.hypot(dx,dy),reach=m.width*.5+(e.r||0);
      if(d<=reach+.001){hit(c,e,dx,dy);break;}
      const step=Math.min(config.step,budget,d-reach),ux=dx/d,uy=dy/d;
      const x=pl.x+ux*step,y=pl.y+uy*step;
      if(!G.World.isFree(x,y,pl.r*.8,true)){end(c);break;}
      pl.x=x;pl.y=y;c.travel+=step;budget-=step;
      pl.aim=pl.moveAngle=Math.atan2(dy,dx);pl.attackFace=.15;pl.anim.dir=G.Sprites.dirFromAngle(pl.aim);
      c.trail+=step;
      if(c.trail>=20){c.trail=0;G.FX.sp('bolt','naruto-blue',x,y-G.LIFT,{life:.13,scale:.7,angle:pl.aim});}
    }
    if(chain===c&&c.phase==='dash'){
      if(Math.hypot(e.x-pl.x,e.y-pl.y)<=m.width*.5+(e.r||0)+.001)hit(c,e,e.x-pl.x,e.y-pl.y);
      else if(c.travel>=c.legRange-.001)end(c);
    }
  }
  const canCast = (pl,m) => pl === G.Game.player && pl.dex === 30002 && !pl.dead && pl.hp > 0 && !chain && !G.NarutoFireball?.active &&
    G.EnemyMgr.all().some(e=>targetAlive(e)&&Math.hypot(e.x-pl.x,e.y-pl.y)<=(m?.range||170));
  function cast(pl,m) {
    if(!canCast(pl,m))return false;
    const c={owner:pl,world:G.World,move:{...m,digiVis:{...m.digiVis}},limit:limitOf(m),attack:pl.atk,hits:new Set(),dashes:0,trail:0,phase:'charge',wait:Math.max(0,m.charge||0)};
    if(!next(c))return false;
    chain=c;return true;
  }
  // Keep independent damage immunity intact: no writes to pl.invuln, including lava's reset.
  const hurt=G.Player.prototype.hurt, playerUpdate=G.Player.prototype.update;
  G.Player.prototype.hurt=function(...args){if(valid(chain)&&chain.owner===this&&chain.phase==='dash')return;return hurt.apply(this,args);};
  G.Player.prototype.update=function(dt){
    if(!valid(chain)&&chain)clear();
    if(chain?.owner!==this||chain.phase!=='dash')return playerUpdate.call(this,dt);
    const frozen=this.frozen;this.frozen=true;this.svx=this.svy=0;
    try{return playerUpdate.call(this,dt);}finally{this.frozen=frozen;}
  };
  const C=G.Combat,oldUpdate=C.updateFields,oldClear=C.clearFields,oldAir=C.drawAirFields;
  C.updateFields=function(dt){oldUpdate.call(this,dt);update(dt);};
  C.clearFields=function(owner){oldClear.call(this,owner);clear(owner);};
  const clearSkills=G.DigimonSkills.clear;
  G.DigimonSkills.clear=function(owner){clearSkills(owner);clear(owner);};
  C.drawAirFields=function(ctx){oldAir.call(this,ctx);if(valid(chain)&&chain.phase==='dash'){
    const p=chain.owner;G.VFX.draw(ctx,'bolt','naruto-blue',p.x+Math.cos(p.aim)*18,p.y-G.LIFT+Math.sin(p.aim)*18,{scale:1.25,angle:p.aim,frame:Math.floor(performance.now()/65)});
  }};
  G.NarutoChidori={config,limitOf,supports:mode=>mode==='chidori-chain',canCast,cast,clear,update,get active(){return chain;}};
})();
