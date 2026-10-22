/* Learned Sharingan evolves cumulatively; its benefits do not require an active slot. */
(() => {
  if (G.NarutoSharingan) return;
  const config = Object.freeze({
    dodgeChance: .05, magnetMul: 1.2, counterCount: 3, counterDamageMul: 1.35, projectileCount: 1,
    dodgeInvulnerability: .16, counterCooldown: 0, afterimageInterval: .065,
    afterimageLifetime: .2,
    stageNames: Object.freeze(['一勾玉', '二勾玉', '三勾玉', '天照', '須佐能乎'])
  });
  const states = new Map();
  let tintCanvas = null;
  const controlled = owner => G.SelfClones?.isControlled(owner) ?? (owner === G.Game.player);
  function migrate(owner) {
    if (owner?.mon?.dex !== 30002) return;
    const move = owner.moves?.find(m => m.id === 'naruto-sharingan');
    if (!move) return;
    move.passive = true;
    if (owner.bind) delete owner.bind[move.id];
    if (!owner.slots.some(group => group.includes(move))) return;
    const selected = owner.activeGroup();
    owner.slots = owner.slots.map(group => group.includes(move) ? group.filter(m => m !== move) : group).filter(group => group.length);
    const retained = owner.slots.findIndex(group => group.some(m => selected.includes(m)));
    owner.active = retained >= 0 ? retained : Math.max(0, Math.min(owner.active, owner.slots.length - 1));
  }
  function stage(owner) {
    if (!owner || !controlled(owner) || owner.dex !== 30002 || owner.dead || !(owner.hp > 0)) return 0;
    const learned = owner.moves?.find(move => move.id === 'naruto-sharingan');
    return learned ? Math.max(1, Math.min(5, learned.lvl | 0)) : 0;
  }
  function clear(owner) {
    for (const [actor, state] of states) {
      if (owner && actor !== owner) continue;
      states.delete(actor);
      actor.magnet /= config.magnetMul;
      G.NarutoSharinganPowers?.clear(actor);
    }
  }
  function sync(owner = G.Game.player) {
    if (!owner) return 0;
    migrate(owner);
    const level = stage(owner);
    let state = states.get(owner);
    if (state && (state.world !== G.World || !level)) { clear(owner); state = null; }
    if (!level) return 0;
    if (!state) {
      owner.magnet *= config.magnetMul;
      state = { owner, world: G.World, stage: level, counterT: 0, sampleT: 0, images: [] };
      states.set(owner, state);
    }
    state.stage = level;
    return level;
  }
  function projectileBonus(owner, move) {
    if (stage(owner) < 3 || !move) return 0;
    if (move.digiMode) return ['shot', 'nova', 'kusanagi-orbit'].includes(move.digiMode) ? config.projectileCount : 0;
    return ['projectile', 'nova', 'boomerang', 'cone'].includes(move.kind) ? config.projectileCount : 0;
  }
  function image(owner, life = config.afterimageLifetime) {
    const state = states.get(owner);
    if (!state) return;
    state.images.push({ x: owner.x, y: owner.y, life, ttl: life });
    if (state.images.length > 2) state.images.shift();
  }
  function counter(owner) {
    const state = states.get(owner);
    const base = G.Moves.BY_ID['naruto-shuriken'];
    if (!state || !base || !G.DigimonSkills?.fireFrom || state.counterT > 0) return;
    state.counterT = config.counterCooldown;
    const move = { ...base, digiMode: 'nova', count: config.counterCount, digiVis: { ...base.digiVis } };
    G.DigimonSkills.fireFrom(owner, move, owner.x, owner.y, owner.aim || 0, config.counterDamageMul);
  }
  const addMove=G.Player.prototype.addMove;
  G.Player.prototype.addMove=function(id,...args){
    if(id!=='naruto-sharingan'||this.mon?.dex!==30002)return addMove.call(this,id,...args);
    migrate(this);
    if(this.hasMove(id))return false;
    this.moves.push(G.Moves.instance(id,1));
    this.arrange();sync(this);
    return true;
  };
  function hurtOwner(owner, amount, type, pure, context, baseHurt) {
    const level = sync(owner), dash = G.NarutoChidori?.activeFor?.(owner) ?? G.NarutoChidori?.active;
    const immuneDash = dash?.owner === owner && ['dash','return'].includes(dash.phase) && dash.world === G.World;
    if (!level || owner.invuln > 0 || owner.dead || owner.frozen || pure || !(amount > 0) || immuneDash)
      return baseHurt(amount, type, pure, context);
    if (Math.random() < config.dodgeChance) {
      owner.invuln = Math.max(owner.invuln || 0, config.dodgeInvulnerability);
      image(owner, config.dodgeInvulnerability);
      G.FX.burst(owner.x, owner.y - 20, '#ff354f', 6, 35);
      if (level >= 2) counter(owner);
      return;
    }
    return baseHurt(amount * (G.NarutoSharinganPowers?.damageTakenMultiplier(owner) ?? 1), type, pure, context);
  }
  const hurt = G.Player.prototype.hurt;
  G.Player.prototype.hurt = function(amount, type = null, pure = false, context = null) {
    if (this !== G.Game.player) return hurt.call(this, amount, type, pure, context);
    return hurtOwner(this, amount, type, pure, context, (...args) => hurt.apply(this, args));
  };
  function update(dt) {
    for (const [owner] of states) if (!stage(owner) || states.get(owner).world !== G.World) clear(owner);
    for (const owner of [G.Game.player, ...(G.SelfClones?.actors() || [])]) {
      const level = sync(owner);
      if (!level) continue;
      const state = states.get(owner);
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
  }
  function draw(ctx) {
    for (const state of states.values()) {
      if (!stage(state.owner) || state.world !== G.World || !state.images.length) continue;
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
  }
  const C = G.Combat, updateFields = C.updateFields, clearFields = C.clearFields, ground = C.drawGroundFields;
  C.updateFields = function(dt) { const result = updateFields.call(this, dt); update(dt); return result; };
  C.clearFields = function(owner) { const result = clearFields.call(this, owner); clear(owner); return result; };
  C.drawGroundFields = function(ctx) { ground.call(this, ctx); draw(ctx); };
  if (G.DigimonSkills?.clear) {
    const previous = G.DigimonSkills.clear;
    G.DigimonSkills.clear = function(owner) { const result = previous.call(this, owner); clear(owner); return result; };
  }
  G.NarutoSharingan = { config, stage, sync, migrate, projectileBonus, clear, update, hurtClone: hurtOwner, stateFor: owner => states.get(owner), get state() { return states.get(G.Game.player); } };
})();
