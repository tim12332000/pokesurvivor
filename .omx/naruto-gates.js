/* Learned Eight Gates compose with current stats and never consume an active slot. */
(() => {
  if (G.NarutoGates) return;
  const id = 'naruto-gates';
  const config = Object.freeze({
    stageNames: Object.freeze(['開門', '休門', '生門', '傷門', '杜門']),
    atkMultipliers: Object.freeze([1.3, 1.35, 1.4, 1.45, 1.5]),
    trails: Object.freeze([
      { scale: 1.04, count: 3, life: .16, interval: .075, opacity: .24 },
      { scale: 1.12, count: 4, life: .20, interval: .065, opacity: .28 },
      { scale: 1.22, count: 5, life: .24, interval: .055, opacity: .32 },
      { scale: 1.34, count: 6, life: .28, interval: .045, opacity: .36 },
      { scale: 1.48, count: 7, life: .32, interval: .035, opacity: .40 }
    ].map(style => Object.freeze(style)))
  });
  const states = new Map();
  const isClone = owner => !!owner?.sourceOwner;
  const controlled = owner => G.SelfClones?.isControlled(owner) ?? (owner === G.Game.player);
  const appliedHealth = new WeakMap();
  function maxHealthBonus(owner = G.Game.player) {
    if (isClone(owner)) return 0; // The summon snapshot already includes the source Gates health.
    const learned = owner?.mon?.dex === 30006 && owner.moves?.find(move => move.id === id);
    return learned ? Math.max(1, Number.isFinite(owner.level) ? owner.level : 1) * Math.max(1, Math.min(5, learned.lvl | 0)) : 0;
  }
  function syncMaxHealth(owner = G.Game.player) {
    if (isClone(owner)) return 0;
    if (!owner || !Number.isFinite(owner.maxHp) || !(owner.maxHp > 0)) return 0;
    const bonus = maxHealthBonus(owner), delta = bonus - (appliedHealth.get(owner) || 0);
    if (!delta) return bonus;
    // Keep the additive gate component separate from flat and percentage cards.
    owner.maxHp = Math.max(1, owner.maxHp + delta);
    if (delta > 0 && !owner.dead && owner.hp > 0) owner.hp += delta;
    owner.hp = Math.min(owner.hp, owner.maxHp);
    appliedHealth.set(owner, bonus);
    return bonus;
  }
  function stage(owner = G.Game.player) {
    if (!owner || !controlled(owner) || owner.mon?.dex !== 30006 || owner.dead || !(owner.hp > 0)) return 0;
    const move = owner.moves?.find(m => m.id === id);
    return move ? Math.max(1, Math.min(5, move.lvl | 0)) : 0;
  }
  function bonusPercent(owner = G.Game.player) {
    const level = stage(owner);
    return level ? 10 * level + Math.max(1, Number.isFinite(owner.level) ? owner.level : 1) : 0;
  }
  const healingMultiplier = owner => 1 + bonusPercent(owner) / 100;
  // Clone getters inherit the source's Gates stats; do not apply the tier again.
  function inheritedRegen(owner) {
    if (!isClone(owner) || !stage(owner) || !stage(owner.sourceOwner)) return 0;
    return owner.sourceOwner.regen * (G.SelfClones?.ratio ?? 1 / 3);
  }
  function migrate(owner) {
    const move = owner?.moves?.find(m => m.id === id);
    if (!move || owner.mon?.dex !== 30006) return;
    // Old runs can still contain the five-second support version and its shortcut.
    move.passive = true;
    move.digiMode = 'gates-passive';
    move.cd = move.t = 0;
    move.name = '八門遁甲・' + config.stageNames[Math.max(0, Math.min(4, (move.lvl | 0) - 1))];
    for (const key of ['fieldDuration', 'atkMul', 'speedMul', 'fatigueDuration', 'fatigueSpeedMul']) delete move[key];
    if (owner.bind) delete owner.bind[id];
    if (!owner.slots?.some(group => group.some(m => m.id === id))) return;
    const selected = owner.activeGroup();
    owner.slots = owner.slots.map(group => group.some(m => m.id === id) ? group.filter(m => m.id !== id) : group).filter(group => group.length);
    const retained = owner.slots.findIndex(group => group.some(m => selected.includes(m)));
    owner.active = retained >= 0 ? retained : Math.max(0, Math.min(owner.active, owner.slots.length - 1));
    owner.arrange();
  }
  const addMove = G.Player.prototype.addMove;
  G.Player.prototype.addMove = function(moveId, ...args) {
    if (moveId !== id || this.mon?.dex !== 30006) return addMove.call(this, moveId, ...args);
    if (this.hasMove(id)) { migrate(this); syncMaxHealth(this); return false; }
    this.moves.push(G.Moves.instance(id, 1));
    migrate(this);
    syncMaxHealth(this);
    return true;
  };
  const gainXp = G.Player.prototype.gainXp;
  G.Player.prototype.gainXp = function(...args) {
    const result = gainXp.apply(this, args);
    syncMaxHealth(this);
    return result;
  };
  const levelUp = G.Moves.levelUp;
  G.Moves.levelUp = function(move, ...args) {
    const result = levelUp.call(this, move, ...args);
    if (result && move?.id === id && G.Game.player?.moves.includes(move)) syncMaxHealth(G.Game.player);
    return result;
  };
  // Getter composition preserves stat cards, gear, slow effects, and other buffs.
  for (const key of ['atk', 'spd', 'regen']) {
    const descriptor = Object.getOwnPropertyDescriptor(G.Player.prototype, key);
    if (!descriptor?.get) continue;
    Object.defineProperty(G.Player.prototype, key, { ...descriptor, get() {
      const value = descriptor.get.call(this), level = stage(this);
      const innate = key === 'regen' && level ? this.maxHp * level * .01 : 0;
      return (value + innate) * (key === 'atk' ? (level ? config.atkMultipliers[level - 1] : 1) : healingMultiplier(this));
    } });
  }
  const heal = G.Player.prototype.heal;
  G.Player.prototype.heal = function(amount, ...args) {
    return heal.call(this, amount > 0 ? amount * healingMultiplier(this) : amount, ...args);
  };
  function clear(owner) { if (owner) states.delete(owner); else states.clear(); }
  function snapshot(owner, style) {
    const image = document.createElement('canvas');
    image.width = image.height = 192;
    const tint = image.getContext('2d');
    // Freeze the actual pose now; later turns and attacks must not redraw history.
    owner.anim.draw(tint, 96, 160, { flash: true });
    tint.globalCompositeOperation = 'source-in';
    tint.fillStyle = '#ff2248'; tint.fillRect(0, 0, 192, 192);
    return { x: owner.x, y: owner.y, image, ttl: style.life, life: style.life,
      scale: style.scale, opacity: style.opacity };
  }
  function update(dt) {
    const owners = [G.Game.player, ...(G.SelfClones?.actors() || [])].filter(Boolean);
    for (const [owner, state] of states) if (!owners.includes(owner) || !stage(owner) || state.world !== G.World) clear(owner);
    for (const owner of owners) {
      migrate(owner);
      syncMaxHealth(owner);
      const level = stage(owner);
      if (!level) { clear(owner); continue; }
      if (states.get(owner)?.world !== G.World) {
        states.set(owner, { owner, world: G.World, age: 0, sampleT: 0, images: [], lastX: owner.x, lastY: owner.y });
      }
      const state = states.get(owner);
      if (G.Game.state !== 'playing' || !(dt > 0) || !Number.isFinite(dt)) continue;
      state.age += dt; state.sampleT -= dt;
      state.images = state.images.filter(ghost => (ghost.ttl -= dt) > 0);
      const style = config.trails[level - 1];
      if (state.images.length > style.count) state.images.splice(0, state.images.length - style.count);
      if (state.sampleT <= 0 && Math.hypot(owner.x - state.lastX, owner.y - state.lastY) >= 2) {
        state.images.push(snapshot(owner, style));
        if (state.images.length > style.count) state.images.shift();
        state.sampleT = style.interval; state.lastX = owner.x; state.lastY = owner.y;
      }
    }
  }
  function draw(ctx, ground) {
    for (const state of states.values()) {
      const owner = state.owner, level = stage(owner);
      if (!level || state.world !== G.World) continue;
      const phase = state.age, x = owner.x, y = owner.y;
      ctx.save();
      if (ground) {
        const alpha = ctx.globalAlpha;
        ctx.imageSmoothingEnabled = false;
        for (const ghost of state.images) {
          ctx.save();
          ctx.globalAlpha = alpha * ghost.opacity * ghost.ttl / ghost.life;
          ctx.translate(Math.round(ghost.x), Math.round(ghost.y));
          ctx.scale(ghost.scale, ghost.scale);
          ctx.drawImage(ghost.image, -96, -160);
          ctx.restore();
        }
        ctx.strokeStyle = '#70f5aa'; ctx.globalAlpha = .25 + level * .06; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.ellipse(Math.round(x), Math.round(y), 20 + level, 7, 0, 0, Math.PI * 2); ctx.stroke();
      } else {
        const count = level >= 3 ? 8 : 5;
        ctx.fillStyle = '#8dffb4'; ctx.globalAlpha = .35 + level * .06;
        for (let i = 0; i < count; i++) {
          const rise = (phase * (23 + level * 3) + i * 11) % (35 + level * 2);
          const sway = Math.sin(i * 2.3 + phase * 2) * (13 + level);
          ctx.fillRect(Math.round(x + sway), Math.round(y - rise - 3), 2, level >= 3 ? 5 : 3);
        }
      }
      ctx.restore();
    }
  }
  const C = G.Combat, updateFields = C.updateFields, clearFields = C.clearFields;
  const ground = C.drawGroundFields, air = C.drawAirFields;
  C.updateFields = function(dt) { const result = updateFields.call(this, dt); update(dt); return result; };
  C.clearFields = function(owner) { const result = clearFields.call(this, owner); clear(owner); return result; };
  C.drawGroundFields = function(ctx) { ground.call(this, ctx); draw(ctx, true); };
  C.drawAirFields = function(ctx) { air.call(this, ctx); draw(ctx, false); };
  const afterimagesFor = owner => (states.get(owner)?.world === G.World && stage(owner) ? states.get(owner).images : [])
    .map(({ x, y, ttl, life, scale }) => ({ x, y, ttl, life, scale }));
  G.NarutoGates = { config, stage, level: stage, bonusPercent, healingMultiplier, inheritedRegen, maxHealthBonus, syncMaxHealth, afterimagesFor,
    active: owner => stage(owner) > 0,
    redSkin: owner => stage(owner) > 0, redForm: owner => stage(owner) >= 3,
    intense: owner => stage(owner) >= 3, migrate, update, clear,
    get afterimages() { return afterimagesFor(G.Game.player); } };
})();
