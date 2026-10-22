/* Sasuke's fire breath: a scoped pose composition, never a shared Shoot edit. */
(() => {
  if (G.NarutoFireball) return;
  const config = Object.freeze({sealDuration:.24, breathDuration:.16, recoveryDuration:.14});
  const states = new Map();
  const controlled = owner => G.SelfClones?.isControlled(owner) ?? (owner === G.Game.player);
  const activeFor = owner => { const f = states.get(owner); return valid(f) ? f : null; };
  const valid = f => f && controlled(f.owner) && f.world === G.World && !f.owner.dead && f.owner.hp > 0;
  const clear = owner => { if (owner) states.delete(owner); else states.clear(); };
  // The rendered projectile is lifted by LIFT; its rear clears the breathing face.
  const origin = (pl, angle) => ({x:pl.x + Math.cos(angle)*24, y:pl.y - 22 + Math.sin(angle)*24});
  function cast(pl, move, release) {
    if (!controlled(pl) || pl.dex !== 30002 || pl.dead || pl.hp <= 0 || activeFor(pl) || (G.NarutoChidori?.activeFor ? G.NarutoChidori.activeFor(pl) : G.NarutoChidori?.active?.owner === pl)) return false;
    states.set(pl, {owner:pl, world:G.World, move:{...move,digiVis:{...move.digiVis}}, release, aim:pl.aim, t:0, phase:'seal', released:false});
    return true;
  }
  function update(dt) {
    for (const [owner, f] of states) {
      if (!valid(f)) { clear(owner); continue; }
      f.t += Math.max(0,dt);
      if (!f.released && f.t >= config.sealDuration) {
        f.released = true;
        f.release(f.owner,f.move,f.aim);
      }
      f.phase = f.t < config.sealDuration ? 'seal' : f.t < config.sealDuration+config.breathDuration ? 'breath' : 'recovery';
      if (f.t >= config.sealDuration+config.breathDuration+config.recoveryDuration) clear(owner);
    }
  }
  const playerCast=G.Player.prototype.cast, playerUpdate=G.Player.prototype.update;
  G.Player.prototype.cast=function(m) {
    return playerCast.call(this, this.dex===30002 && m.id==='naruto-fireball' ? {...m,kind:'buff'} : m);
  };
  G.Player.prototype.update=function(dt) {
    if (states.has(this) && !activeFor(this)) clear(this);
    if (!activeFor(this)) return playerUpdate.call(this,dt);
    const frozen=this.frozen; this.frozen=true; this.svx=this.svy=0;
    try { return playerUpdate.call(this,dt); } finally { this.frozen=frozen; }
  };
  const Animator=G.Sprites.Animator, draw=Animator.prototype.draw;
  Animator.prototype.draw=function(ctx,x,y,opts={}) {
    const f=[...states.values()].find(f=>f.owner.anim===this), record=G.Naruto.records.get(30002);
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
    for (const f of states.values()) {
      if(!valid(f)||f.phase!=='breath')continue;
      const pl=f.owner, side=Math.cos(f.aim)>=0?1:-1, mouth={x:pl.x+side*16,y:pl.y-44};
      const end=origin(pl,f.aim), ex=end.x, ey=end.y-G.LIFT;
      ctx.save();
      for(let layer=0;layer<3;layer++) {
        ctx.fillStyle=['#ab3721','#ff8028','#ffe8a2'][layer];
        const width=[10,6,2][layer];
        for(let i=0;i<=12;i++) {const t=i/12;ctx.fillRect(Math.round((mouth.x+(ex-mouth.x)*t)/2)*2-width/2,Math.round((mouth.y+(ey-mouth.y)*t)/2)*2-width/2,width,width);}
      }
      ctx.restore();
    }
  };
  G.NarutoFireball={config,cast,clear,update,origin,activeFor,get active(){return activeFor(G.Game.player);}};
})();
