/* Level-based Chidori pursuit is this edition's gameplay adaptation. */
(() => {
  if (G.NarutoChidori) return;
  const config = Object.freeze({ counts: Object.freeze([5,10,15,20,25]), minCooldown: .5, followupRangeMultiplier: 3, endInvulnerability: .3,
    speed: 1000, speedStep: .15, maxSpeedMultiplier: 3, damageStep: .05,
    retargetDelay: .045, retargetDelayDecay: .85, minRetargetDelay: .012, screenPadding: 48, returnDuration: .12, step: 4 });
  const limitOf = (move,owner=G.Game.player) =>
    config.counts[Math.max(0,Math.min(config.counts.length-1,(move?.lvl|0)-1))] +
    Math.max(0,Math.floor(move?.quantityBonusAtCast ?? G.Quantity?.bonus(owner) ?? 0));
  let chain = null;
  const valid = c => c && c.owner === G.Game.player && c.world === G.World && !c.owner.dead && c.owner.hp > 0;
  const clear = owner => { if (!owner || chain?.owner === owner) { if(chain)chain.owner.svx=chain.owner.svy=0;chain=null; } };
  function complete(c) {
    if(chain!==c)return;
    if(valid(c)&&c.dashes>0){
      c.owner.invuln=Math.max(c.owner.invuln||0,config.endInvulnerability);
      const learned=c.owner.moves.find(move=>move.id===c.move.id);
      if(learned)learned.t=Math.max(learned.t||0,config.minCooldown);
    }
    clear();
  }
  function end(c) {
    if(chain!==c)return;
    if(!valid(c)||!c.dashes){clear();return;}
    if(c.phase==='return')return;
    c.phase='return';c.returnFrom={x:c.owner.x,y:c.owner.y};c.returnAge=0;
    c.owner.svx=c.owner.svy=0;
  }
  const targetAlive = e => e && !e.dead && e.hp > 0 && G.EnemyMgr.all().includes(e);
  const inViewport = (e,camera) => Math.abs(e.x-camera.x)<=G.Camera.w/2+config.screenPadding && Math.abs(e.y-camera.y)<=G.Camera.h/2+config.screenPadding;
  const rangeFor = c => c.move.range * (c.hitCount ? config.followupRangeMultiplier : 1);
  function next(c) {
    const pl = c.owner;
    return G.EnemyMgr.all().filter(e => targetAlive(e) && inViewport(e,c.camera) && e!==c.lastTarget && Math.hypot(e.x-pl.x,e.y-pl.y) <= rangeFor(c))
      .sort((a,b) => Math.hypot(a.x-pl.x,a.y-pl.y)-Math.hypot(b.x-pl.x,b.y-pl.y))[0];
  }
  function begin(c) {
    if (c.dashes >= c.limit || !(c.target = next(c))) { end(c); return; }
    c.legRange = rangeFor(c); c.speed = config.speed*Math.min(config.maxSpeedMultiplier,1+c.hitCount*config.speedStep);
    c.dashes++; c.travel = 0; c.phase = 'dash';
    c.owner.cast(c.move);
  }
  function finish(c) {
    if (c.dashes >= c.limit || !next(c)) { end(c); return; }
    c.phase = 'retarget';
    c.retargetDelay = Math.max(config.minRetargetDelay,config.retargetDelay*Math.pow(config.retargetDelayDecay,c.hitCount));
    c.wait = c.retargetDelay;
  }
  function hit(c, e, dx, dy) {
    const damageMultiplier=Math.pow(1+config.damageStep,c.hitCount);
    c.hitCount++;c.lastTarget=e;
    const m=c.move, pl=c.owner, k=G.Types.mult(m.type,e.types), crit=pl.critChance>0&&Math.random()<pl.critChance;
    const dmg=m.dmg*c.attack*damageMultiplier*k*G.Weather.mult(m.type)*(crit?1.5:1)*(G.NarutoSupport?.precisionMultiplier(pl,e)||1);
    e.hurt(dmg,'#9feaff',dx,dy,m.knock||0,crit?'crit':G.Types.label(k),pl);
    pl.onDealt(dmg); pl.dmgDealt+=dmg;
    if(m.slow)e.applySlow(m.slow);
    G.FX.slash(pl.x,pl.y-G.LIFT*.5,pl.aim,34,2.2,'#9feaff',m.digiVis);
    finish(c);
  }
  function update(dt) {
    const c=chain;
    if(!valid(c)){clear();return;}
    if(c.phase==='return') {
      c.returnAge=Math.min(config.returnDuration,c.returnAge+dt);
      const t=c.returnAge/config.returnDuration;
      c.owner.x=c.returnFrom.x+(c.origin.x-c.returnFrom.x)*t;
      c.owner.y=c.returnFrom.y+(c.origin.y-c.returnFrom.y)*t;
      c.owner.svx=c.owner.svy=0;
      if(t>=1){c.owner.x=c.origin.x;c.owner.y=c.origin.y;complete(c);}
      return;
    }
    if(c.phase!=='dash') {c.wait-=dt;if(c.wait<=0)begin(c);return;}
    if(!targetAlive(c.target)||!inViewport(c.target,c.camera)){finish(c);return;}
    const pl=c.owner,m=c.move,e=c.target;
    let budget=Math.min(c.speed*dt,c.legRange-c.travel);
    while(budget>0&&chain===c&&c.phase==='dash') {
      const dx=e.x-pl.x,dy=e.y-pl.y,d=Math.hypot(dx,dy),reach=m.width*.5+(e.r||0);
      if(d<=reach+.001){hit(c,e,dx,dy);break;}
      const step=Math.min(config.step,budget,d-reach),ux=dx/d,uy=dy/d;
      const x=pl.x+ux*step,y=pl.y+uy*step;
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
    G.EnemyMgr.all().some(e=>targetAlive(e)&&inViewport(e,G.Camera)&&Math.hypot(e.x-pl.x,e.y-pl.y)<=(m?.range||170));
  function cast(pl,m) {
    if(!canCast(pl,m))return false;
    const c={owner:pl,world:G.World,move:{...m,digiVis:{...m.digiVis}},limit:limitOf(m,pl),attack:pl.atk,hitCount:0,lastTarget:null,dashes:0,trail:0,
      origin:{x:pl.x,y:pl.y},camera:{x:G.Camera.x,y:G.Camera.y},
      speed:config.speed,retargetDelay:config.retargetDelay,phase:'charge',wait:Math.max(0,m.charge||0)};
    const first=next(c);if(!first)return false;
    pl.aim=Math.atan2(first.y-pl.y,first.x-pl.x);
    chain=c;pl.svx=pl.svy=0;holdCamera(c);return true;
  }
  function poseFor(animator){
    const c=chain;
    if(!valid(c)||c.owner.anim!==animator)return null;
    const source=G.Naruto.records.get(30002).pixel.chidori;
    if(!source)return null;
    const charging=c.phase==='charge',duration=Math.max(.001,c.move.charge||0);
    const index=Math.min(source.chargeFrames.length-1,Math.floor(Math.max(0,1-c.wait/duration)*source.chargeFrames.length));
    const frame=charging?source.chargeFrames[index]:source.dashFrame;
    const dir=G.Sprites.dirFromAngle(c.owner.aim),direction=['down','right','right','right','up','left','left','left'][dir];
    return {...frame,direction,mirror:source.mirror.includes(direction),action:true};
  }
  // Flight immunity never overwrites independent timers, including lava's reset.
  const hurt=G.Player.prototype.hurt, playerUpdate=G.Player.prototype.update;
  G.Player.prototype.hurt=function(...args){if(valid(chain)&&chain.owner===this&&['dash','return'].includes(chain.phase))return;return hurt.apply(this,args);};
  G.Player.prototype.update=function(dt){
    if(!valid(chain)&&chain)clear();
    if(chain?.owner!==this)return playerUpdate.call(this,dt);
    const frozen=this.frozen,x=this.x,y=this.y;this.frozen=true;this.svx=this.svy=0;
    // Dash movement owns position, including passage through solid scenery.
    try{return playerUpdate.call(this,dt);}finally{this.x=x;this.y=y;this.frozen=frozen;}
  };
  function holdCamera(c) {Object.assign(G.Camera,{x:c.camera.x,y:c.camera.y,shake:0,_sx:0,_sy:0});}
  const follow=G.Camera.follow,kick=G.Camera.kick;
  G.Camera.follow=function(...args){
    if(chain&&!valid(chain))clear();
    const result=follow.apply(this,args);
    if(valid(chain))holdCamera(chain);
    return result;
  };
  G.Camera.kick=function(...args){if(valid(chain)){holdCamera(chain);return;}return kick.apply(this,args);};
  const C=G.Combat,oldUpdate=C.updateFields,oldClear=C.clearFields,oldAir=C.drawAirFields;
  C.updateFields=function(dt){oldUpdate.call(this,dt);update(dt);};
  C.clearFields=function(owner){oldClear.call(this,owner);clear(owner);};
  const clearSkills=G.DigimonSkills.clear;
  G.DigimonSkills.clear=function(owner){clearSkills(owner);clear(owner);};
  C.drawAirFields=function(ctx){oldAir.call(this,ctx);if(valid(chain)&&['dash','return'].includes(chain.phase)){
    const p=chain.owner,pose=poseFor(p.anim),stand=G.Naruto.records.get(30002).pixel.frames.down[0];
    const k=64*p.anim.scale/stand[3],mirror=pose?.mirror?-1:1;
    const x=pose?.hand?p.x+(pose.hand[0]-pose.anchor[0])*k*mirror:p.x+Math.cos(p.aim)*18;
    const y=pose?.hand?p.y+(pose.hand[1]-pose.anchor[1])*k:p.y-G.LIFT+Math.sin(p.aim)*18;
    G.VFX.draw(ctx,'bolt','naruto-blue',x,y,{scale:1.25,angle:p.aim,frame:Math.floor(performance.now()/65)});
  }};
  G.NarutoChidori={config,limitOf,poseFor,supports:mode=>mode==='chidori-chain',canCast,cast,clear,update,get active(){return chain;}};
})();
