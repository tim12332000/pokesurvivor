/* Sasuke's fire breath: a scoped pose composition, never a shared Shoot edit. */
(() => {
  if (G.NarutoFireball) return;
  const config = Object.freeze({sealDuration:.24, breathDuration:.16, recoveryDuration:.14});
  let active = null;
  const valid = f => f && f.owner === G.Game.player && f.world === G.World && !f.owner.dead && f.owner.hp > 0;
  const clear = owner => { if (!owner || active?.owner === owner) active = null; };
  // The rendered projectile is lifted by LIFT; its rear clears the breathing face.
  const origin = (pl, angle) => ({x:pl.x + Math.cos(angle)*76, y:pl.y - 22 + Math.sin(angle)*76});
  function cast(pl, move, release) {
    if (pl !== G.Game.player || pl.dex !== 30002 || pl.dead || pl.hp <= 0 || active || G.NarutoChidori?.active) return false;
    active = {owner:pl, world:G.World, move:{...move,digiVis:{...move.digiVis}}, release, aim:pl.aim, t:0, phase:'seal', released:false};
    return true;
  }
  function update(dt) {
    const f = active;
    if (!valid(f)) { clear(); return; }
    f.t += Math.max(0,dt);
    if (!f.released && f.t >= config.sealDuration) {
      f.released = true;
      f.release(f.owner,f.move,f.aim);
    }
    f.phase = f.t < config.sealDuration ? 'seal' : f.t < config.sealDuration+config.breathDuration ? 'breath' : 'recovery';
    if (f.t >= config.sealDuration+config.breathDuration+config.recoveryDuration) clear();
  }
  const playerCast=G.Player.prototype.cast, playerUpdate=G.Player.prototype.update;
  G.Player.prototype.cast=function(m) {
    return playerCast.call(this, this.dex===30002 && m.id==='naruto-fireball' ? {...m,kind:'buff'} : m);
  };
  G.Player.prototype.update=function(dt) {
    if (active && !valid(active)) clear();
    if (active?.owner !== this) return playerUpdate.call(this,dt);
    const frozen=this.frozen; this.frozen=true; this.svx=this.svy=0;
    try { return playerUpdate.call(this,dt); } finally { this.frozen=frozen; }
  };
  const Animator=G.Sprites.Animator, draw=Animator.prototype.draw;
  Animator.prototype.draw=function(ctx,x,y,opts={}) {
    const f=active, record=G.Naruto.records.get(30002);
    if (!valid(f) || f.owner.anim!==this || !record?.ready) return draw.call(this,ctx,x,y,opts);
    const side=Math.cos(f.aim)>=0 ? 1 : -1, k=64/44*this.scale;
    ctx.save(); ctx.translate(Math.round(x),Math.round(y)); ctx.scale(side*k,k);
    ctx.imageSmoothingEnabled=false; ctx.globalAlpha*=opts.alpha??1;
    const image=opts.flash ? G.Sprites.white(record.image) : record.image;
    ctx.drawImage(image,104,49,36,44,-18,-44,36,44);
    // Repaint only the near arm. Original head, torso and planted feet stay intact.
    const pixel=(x,y,w,h,col)=>{ctx.fillStyle=col;ctx.fillRect(x,y,w,h);};
    const seal=f.phase==='seal', recover=f.phase==='recovery';
    if (seal) {
      pixel(0,-27,7,3,'#17203e'); pixel(4,-32,4,8,'#17203e');
      pixel(5,-31,2,6,'#e7b17b'); pixel(8,-30,2,5,'#f8d69c');
      pixel(1,-26,6,2,'#f8d69c');
    } else if (!recover) {
      pixel(0,-27,9,3,'#17203e'); pixel(7,-32,4,7,'#17203e');
      pixel(8,-31,2,6,'#f8d69c'); pixel(10,-31,3,3,'#e7b17b');
      pixel(11,-30,2,1,'#652b26');
    } else {
      pixel(1,-26,8,4,'#17203e'); pixel(7,-24,4,4,'#e7b17b');
    }
    ctx.restore();
  };
  const C=G.Combat, oldUpdate=C.updateFields, oldClear=C.clearFields, oldAir=C.drawAirFields;
  C.updateFields=function(dt){oldUpdate.call(this,dt);update(dt);};
  C.clearFields=function(owner){oldClear.call(this,owner);clear(owner);};
  const oldSkillsClear=G.DigimonSkills.clear;
  G.DigimonSkills.clear=function(owner){oldSkillsClear(owner);clear(owner);};
  C.drawAirFields=function(ctx) {
    oldAir.call(this,ctx);
    const f=active;if(!valid(f)||f.phase!=='breath')return;
    const pl=f.owner, side=Math.cos(f.aim)>=0?1:-1, mouth={x:pl.x+side*16,y:pl.y-44};
    const end=origin(pl,f.aim), ex=end.x-Math.cos(f.aim)*42, ey=end.y-G.LIFT-Math.sin(f.aim)*42;
    ctx.save();
    for(let layer=0;layer<3;layer++) {
      ctx.fillStyle=['#ab3721','#ff8028','#ffe8a2'][layer];
      const width=[10,6,2][layer];
      for(let i=0;i<=12;i++) {const t=i/12;ctx.fillRect(Math.round((mouth.x+(ex-mouth.x)*t)/2)*2-width/2,Math.round((mouth.y+(ey-mouth.y)*t)/2)*2-width/2,width,width);}
    }
    ctx.restore();
  };
  G.NarutoFireball={config,cast,clear,update,origin,get active(){return active;}};
})();
