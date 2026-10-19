/* Learned Sharingan evolves cumulatively; its benefits do not require an active slot. */
(() => {
  if (G.NarutoSharingan) return;
  const config = Object.freeze({
    dodgeChance: .05, magnetMul: 1.2, counterCount: 3, counterDamageMul: 1.35, projectileCount: 1,
    dodgeInvulnerability: .16, counterCooldown: 0, afterimageInterval: .065,
    afterimageLifetime: .2,
    stageNames: Object.freeze(['一勾玉', '二勾玉', '三勾玉', '天照', '須佐能乎'])
  });
  let state = null, tintCanvas = null;
  function stage(owner) {
    if (!owner || owner !== G.Game.player || owner.dex !== 30002 || owner.dead || !(owner.hp > 0)) return 0;
    const learned = owner.moves?.find(move => move.id === 'naruto-sharingan');
    return learned ? Math.max(1, Math.min(5, learned.lvl | 0)) : 0;
  }
  function clear(owner) {
    if (!state || (owner && state.owner !== owner)) return;
    const previous = state;
    state = null;
    // Divide the applied factor only; later magnet cards and temporary buffs survive.
    previous.owner.magnet /= config.magnetMul;
    G.NarutoSharinganPowers?.clear(previous.owner);
  }
  function sync(owner = G.Game.player) {
    if (owner && owner !== G.Game.player) return 0;
    const level = stage(owner);
    if (state && (state.owner !== owner || state.world !== G.World || !level)) clear();
    if (!level) return 0;
    if (!state) {
      owner.magnet *= config.magnetMul;
      state = { owner, world: G.World, stage: level, counterT: 0, sampleT: 0, images: [] };
    }
    state.stage = level;
    return level;
  }
  function projectileBonus(owner, move) {
    if (stage(owner) < 3 || !move) return 0;
    if (move.digiMode) return ['shot', 'nova'].includes(move.digiMode) ? config.projectileCount : 0;
    return ['projectile', 'nova', 'boomerang', 'cone'].includes(move.kind) ? config.projectileCount : 0;
  }
  function image(owner, life = config.afterimageLifetime) {
    if (!state || state.owner !== owner) return;
    state.images.push({ x: owner.x, y: owner.y, life, ttl: life });
    if (state.images.length > 2) state.images.shift();
  }
  function counter(owner) {
    const base = G.Moves.BY_ID['naruto-shuriken'];
    if (!base || !G.DigimonSkills?.fireFrom || state.counterT > 0) return;
    state.counterT = config.counterCooldown;
    const move = { ...base, digiMode: 'nova', count: config.counterCount, digiVis: { ...base.digiVis } };
    G.DigimonSkills.fireFrom(owner, move, owner.x, owner.y, owner.aim || 0, config.counterDamageMul);
  }
  const addMove=G.Player.prototype.addMove;
  G.Player.prototype.addMove=function(id,...args){
    const previous=this.activeGroup(),added=addMove.call(this,id,...args);
    if(added&&id==='naruto-sharingan'&&previous?.some(move=>!move.passive)){
      const index=this.slots.indexOf(previous);
      if(index>=0)this.active=index;
    }
    return added;
  };
  const hurt = G.Player.prototype.hurt;
  G.Player.prototype.hurt = function(amount, type = null, pure = false) {
    if (this !== G.Game.player) return hurt.call(this, amount, type, pure);
    const level = sync(this), dash = G.NarutoChidori?.active;
    const immuneDash = dash?.owner === this && ['dash','return'].includes(dash.phase) && dash.world === G.World;
    if (!level || this.invuln > 0 || this.dead || this.frozen || pure || !(amount > 0) || immuneDash)
      return hurt.call(this, amount, type, pure);
    if (Math.random() < config.dodgeChance) {
      this.invuln = Math.max(this.invuln || 0, config.dodgeInvulnerability);
      image(this, config.dodgeInvulnerability);
      G.FX.burst(this.x, this.y - 20, '#ff354f', 6, 35);
      if (level >= 2) counter(this);
      return;
    }
    return hurt.call(this, amount * (G.NarutoSharinganPowers?.damageTakenMultiplier(this) ?? 1), type, pure);
  };
  function update(dt) {
    const owner = G.Game.player, level = sync(owner);
    if (!level) return;
    const elapsed = Math.max(0, Number.isFinite(dt) ? dt : 0);
    state.counterT = Math.max(0, state.counterT - elapsed);
    for (const ghost of state.images) ghost.ttl -= elapsed;
    state.images = state.images.filter(ghost => ghost.ttl > 0);
    state.sampleT -= elapsed;
    if (level >= 3 && state.sampleT <= 0) {
      state.sampleT = config.afterimageInterval;
      const previous = state.images[state.images.length - 1];
      if (!previous || Math.hypot(owner.x - previous.x, owner.y - previous.y) > 2) image(owner);
    }
    G.NarutoSharinganPowers?.update(owner, level, elapsed);
  }
  function draw(ctx) {
    if (!state || !stage(state.owner) || state.world !== G.World || !state.images.length) return;
    if (!tintCanvas) { tintCanvas = document.createElement('canvas'); tintCanvas.width = tintCanvas.height = 192; }
    const tint = tintCanvas.getContext('2d');
    tint.clearRect(0, 0, 192, 192);
    // Reuse the current sprite pose and direction; these are visual echoes, never actors.
    state.owner.anim.draw(tint, 96, 160, { flash: true });
    tint.globalCompositeOperation = 'source-in'; tint.fillStyle = '#ff354f'; tint.fillRect(0, 0, 192, 192);
    tint.globalCompositeOperation = 'source-over';
    ctx.save(); ctx.imageSmoothingEnabled = false;
    for (const ghost of state.images) {
      ctx.globalAlpha *= .32 * ghost.ttl / ghost.life;
      ctx.drawImage(tintCanvas, Math.round(ghost.x - 96), Math.round(ghost.y - 160));
      ctx.globalAlpha /= .32 * ghost.ttl / ghost.life;
    }
    ctx.restore();
  }
  const C = G.Combat, updateFields = C.updateFields, clearFields = C.clearFields, ground = C.drawGroundFields;
  C.updateFields = function(dt) { const result = updateFields.call(this, dt); update(dt); return result; };
  C.clearFields = function(owner) { const result = clearFields.call(this, owner); clear(owner); return result; };
  C.drawGroundFields = function(ctx) { ground.call(this, ctx); draw(ctx); };
  if (G.DigimonSkills?.clear) {
    const previous = G.DigimonSkills.clear;
    G.DigimonSkills.clear = function(owner) { const result = previous.call(this, owner); clear(owner); return result; };
  }
  G.NarutoSharingan = { config, stage, sync, projectileBonus, clear, update };
})();
