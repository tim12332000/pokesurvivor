/* Learned Eight Gates compose with current stats and never consume an active slot. */
(() => {
  if (G.NarutoGates) return;
  const id = 'naruto-gates';
  const config = Object.freeze({
    duration: 15, cooldown: 25, openingDuration: 4, openingBurstDuration: 1, openingRadius: 140, openingDamageFraction: .3, openingBossDamageFraction: .1,
    stageNames: Object.freeze(['杜門', '景門', '死門']),
    effectTiers: Object.freeze([1, 3, 5]),
    atkMultipliers: Object.freeze([1.3, 1.4, 1.5]),
    trails: Object.freeze([
      { scale: 1.10, count: 6, life: .55, interval: .09, opacity: .48, color: '#55aaff' },
      { scale: 1.28, count: 8, life: .70, interval: .085, opacity: .56, color: '#70f5aa' },
      { scale: 1.50, count: 10, life: .86, interval: .08, opacity: .66, color: '#ff315b' }
    ].map(style => Object.freeze(style)))
  });
  const cycleDuration = config.openingDuration + config.openingBurstDuration + config.cooldown;
  const states = new Map(), openings = new Map(), cycles = new Map();
  const isClone = owner => !!owner?.sourceOwner;
  const controlled = owner => G.SelfClones?.isControlled(owner) ?? (owner === G.Game.player);
  const appliedHealth = new WeakMap();
  function maxHealthBonus(owner = G.Game.player) {
    if (isClone(owner)) return 0; // The summon snapshot already includes the source Gates health.
    const tier = effectTier(owner);
    return tier ? Math.max(1, Number.isFinite(owner.level) ? owner.level : 1) * tier : 0;
  }
  function syncMaxHealth(owner = G.Game.player) {
    if (isClone(owner)) return 0;
    if (!owner || !Number.isFinite(owner.maxHp) || !(owner.maxHp > 0)) return 0;
    const bonus = maxHealthBonus(owner), delta = bonus - (appliedHealth.get(owner) || 0);
    if (!delta) return bonus;
    // Keep the additive gate component separate from flat and percentage cards.
    owner.maxHp = Math.max(1, owner.maxHp + delta);
    if (delta > 0 && !owner.dead && owner.hp > 0) owner.hp = Math.max(owner.hp, Math.min(owner.maxHp, owner.hp + delta));
    // Closing removes temporary capacity, not HP already gained while the Gates were open.
    appliedHealth.set(owner, bonus);
    return bonus;
  }
  function learnedStage(owner = G.Game.player) {
    if (!owner || !controlled(owner) || owner.mon?.dex !== 30006 || owner.dead || !(owner.hp > 0)) return 0;
    const move = owner.moves?.find(m => m.id === id);
    return move ? Math.max(1, Math.min(config.stageNames.length, move.lvl | 0)) : 0;
  }
  function stage(owner = G.Game.player) {
    const level = learnedStage(owner);
    if (!level) return 0;
    const source = owner.sourceOwner || owner, cycle = cycles.get(source);
    return cycle?.world === G.World && cycle.active && cycle.age < config.duration ? level : 0;
  }
  const effectTier = owner => config.effectTiers[stage(owner) - 1] || 0;
  function status(owner = G.Game.player) {
    const source = owner?.sourceOwner || owner, cycle = cycles.get(source);
    const active = stage(owner) > 0;
    return { active, activeRemaining: active ? Math.max(0, config.duration - cycle.age) : 0,
      cooldownRemaining: learnedStage(owner) && cycle?.world === G.World ? Math.max(0, cycleDuration - Math.max(cycle.age, cycle.active ? config.openingDuration + config.openingBurstDuration : 0)) : 0,
      duration: config.duration, cooldown: config.cooldown };
  }
  function bonusPercent(owner = G.Game.player) {
    const tier = effectTier(owner);
    return tier ? 10 * tier + Math.max(1, Number.isFinite(owner.level) ? owner.level : 1) : 0;
  }
  const healingMultiplier = owner => 1 + bonusPercent(owner) / 100;
  const attackSpeedMultiplier = owner => 1 + effectTier(owner) * .1;
  // Clone getters inherit the source's Gates stats; do not apply the tier again.
  function inheritedRegen(owner) {
    if (!isClone(owner) || !stage(owner) || !stage(owner.sourceOwner)) return 0;
    return owner.sourceOwner.regen * (G.SelfClones?.ratio ?? 1 / 3);
  }
  function migrate(owner) {
    const move = owner?.moves?.find(m => m.id === id);
    if (!move || owner.mon?.dex !== 30006) return;
    // Old runs can still contain the five-second support version and its shortcut.
    move.lvl = Math.max(1, Math.min(config.stageNames.length, move.lvl | 0));
    move.passive = true;
    move.digiMode = 'gates-passive';
    move.cd = config.cooldown; move.t = status(owner).cooldownRemaining;
    move.name = '八門遁甲・' + config.stageNames[move.lvl - 1];
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
    beginOpening(this);
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
    if (result && move?.id === id && G.Game.player?.moves.includes(move)) {
      syncMaxHealth(G.Game.player); beginOpening(G.Game.player);
    }
    return result;
  };
  // Getter composition preserves stat cards, gear, slow effects, and other buffs.
  for (const key of ['atk', 'spd', 'regen']) {
    const descriptor = Object.getOwnPropertyDescriptor(G.Player.prototype, key);
    if (!descriptor?.get) continue;
    Object.defineProperty(G.Player.prototype, key, { ...descriptor, get() {
      const value = descriptor.get.call(this), level = stage(this);
      const innate = key === 'regen' && level ? this.maxHp * effectTier(this) * .01 : 0;
      const multiplier = key === 'atk' ? (level ? config.atkMultipliers[level - 1] : 1) :
        key === 'spd' ? attackSpeedMultiplier(this) : healingMultiplier(this);
      return (value + innate) * multiplier;
    } });
  }
  const heal = G.Player.prototype.heal;
  G.Player.prototype.heal = function(amount, ...args) {
    return heal.call(this, amount > 0 ? amount * healingMultiplier(this) : amount, ...args);
  };
  const hurt = G.Player.prototype.hurt;
  G.Player.prototype.hurt = function(...args) {
    const opening = openingFor(this), before = this.hp;
    const result = hurt.apply(this, args);
    // Refund only HP actually lost during this performance, after mitigation/dodges.
    // Restore the exact prior HP, including retained excess HP, without healing amplification.
    if (opening && openingFor(this) === opening && !this.dead && this.hp > 0 && this.hp < before) {
      this.hp = before;
    }
    return result;
  };
  function clear(owner) {
    const selected = owner ? [owner] : [...new Set([...states.keys(), ...openings.keys(), ...cycles.keys()])];
    for (const actor of selected) {
      states.delete(actor); openings.delete(actor);
      const cycle = cycles.get(actor);
      if (cycle) cycle.active = false;
      syncMaxHealth(actor);
    }
  }
  function openingFor(owner) {
    const f = openings.get(owner);
    return f && f.world === G.World && stage(owner) ? f : null;
  }
  const charging = owner => !!openingFor(owner) && !openingFor(owner).released;
  const performing = owner => !!openingFor(owner);
  function presentationFor(owner) {
    const f = openingFor(owner);
    if (!f) return null;
    const phase = f.age < .6 ? 'prepare' : !f.released ? (f.age < config.openingDuration - 1 ? 'charge' : 'intensify') : f.age < config.openingDuration + .6 ? 'burst' : 'recovery';
    return { state: 'skill', id, phase, key: 'lee-gates',
      frame: phase === 'prepare' ? 0 : ['charge', 'intensify'].includes(phase) ? 1 : phase === 'burst' ? 2 : 3,
      age: f.age, aim: f.aim, direction: 'down', mirror: phase === 'recovery' && Math.cos(f.aim) < 0 };
  }
  function beginOpening(owner) {
    if (!learnedStage(owner) || isClone(owner)) return;
    // Release existing techniques through the captured combat cleanup. Later scene/summon
    // cleanup wrappers must not delete card-created clones whenever the automatic cycle starts.
    clearFields.call(G.Combat, owner);
    states.delete(owner);
    cycles.set(owner, { world: G.World, age: 0, active: true });
    owner.svx = owner.svy = 0;
    openings.set(owner, { owner, world: G.World, x: owner.x, y: owner.y, aim: owner.aim || 0, dir: owner.anim.dir, age: 0, released: false });
    syncMaxHealth(owner);
    migrate(owner);
  }
  function releaseOpening(f) {
    const owner = f.owner, color = config.trails[stage(owner) - 1].color;
    f.released = true;
    G.FX.burst(f.x, f.y - 18, color, 72, 280);
    G.FX.burst(f.x, f.y - 28, '#fffbdc', 32, 220);
    G.Camera.shake = Math.max(G.Camera.shake || 0, 16);
  }
  function damageOpening(f) {
    const owner = f.owner, color = config.trails[stage(owner) - 1].color;
    for (const enemy of new Set(G.EnemyMgr.queryCircle(f.x, f.y, config.openingRadius))) {
      if (enemy.dead || !(enemy.hp > 0) || Math.hypot(enemy.x - f.x, enemy.y - f.y) > config.openingRadius) continue;
      const boss = enemy.boss || enemy.legend || enemy.judge;
      const damage = enemy.maxHp * (boss ? config.openingBossDamageFraction : config.openingDamageFraction);
      enemy.hurt(damage, color, enemy.x - f.x, enemy.y - f.y, boss ? 5 : 24, null, owner, id);
      owner.onDealt(damage); owner.dmgDealt += damage;
    }
  }
  const playerUpdate = G.Player.prototype.update;
  G.Player.prototype.update = function(dt) {
    if (!performing(this)) return playerUpdate.call(this, dt);
    const f = openingFor(this), frozen = this.frozen;
    this.frozen = true; this.svx = this.svy = 0;
    try { return playerUpdate.call(this, dt); }
    finally {
      this.frozen = frozen; this.x = f.x; this.y = f.y; this.walking = false;
      this.aim = f.aim; this.anim.dir = f.dir; this.svx = this.svy = 0;
    }
  };
  const playerCast = G.Player.prototype.cast;
  G.Player.prototype.cast = function(...args) {
    if (performing(this)) return;
    return playerCast.apply(this, args);
  };
  function snapshot(owner, style) {
    const image = document.createElement('canvas');
    image.width = image.height = 192;
    const tint = image.getContext('2d');
    // Freeze the actual pose now; later turns and attacks must not redraw history.
    owner.anim.draw(tint, 96, 160, { flash: true });
    tint.globalCompositeOperation = 'source-in';
    tint.fillStyle = style.color; tint.fillRect(0, 0, 192, 192);
    return { x: owner.x, y: owner.y, image, ttl: style.life, life: style.life,
      scale: style.scale, opacity: style.opacity, color: style.color };
  }
  function updateOpening(owner, elapsed) {
    const f = openings.get(owner);
    if (!f || !openingFor(owner)) { openings.delete(owner); return; }
    const duration = config.openingDuration + config.openingBurstDuration;
    const activeDt = Math.min(elapsed, Math.max(0, duration - f.age));
    f.age = Math.min(duration, f.age + activeDt);
    if (!f.released && f.age + 1e-9 >= config.openingDuration) releaseOpening(f);
    if (f.age >= duration) { damageOpening(f); openings.delete(owner); }
  }
  function update(dt) {
    const owners = [G.Game.player, ...(G.SelfClones?.actors() || [])].filter(Boolean);
    const running = G.Game.state === 'playing' && dt > 0 && Number.isFinite(dt);
    for (const [owner, cycle] of cycles) {
      if (!owners.includes(owner) || owner.mon?.dex !== 30006 || !owner.moves?.some(move => move.id === id)) {
        clear(owner); cycles.delete(owner); continue;
      }
      if (cycle.world !== G.World || owner.dead || !(owner.hp > 0)) {
        clear(owner); cycle.world = G.World; continue;
      }
      if (!running) continue;
      // At most one normal cycle is processed per gameplay update. Large test/debug deltas
      // discard fully skipped cycles rather than backfilling damage or healing.
      const elapsed = Math.min(dt, Math.max(0, cycleDuration - cycle.age));
      if (cycle.active) updateOpening(owner, Math.min(elapsed, Math.max(0, config.duration - cycle.age)));
      cycle.age = Math.min(cycleDuration, cycle.age + elapsed);
      if (Math.abs(cycle.age - config.duration) < 1e-9) cycle.age = config.duration;
      if (Math.abs(cycle.age - cycleDuration) < 1e-9) cycle.age = cycleDuration;
      if (cycle.active && cycle.age >= config.duration) {
        cycle.active = false; states.delete(owner); openings.delete(owner); syncMaxHealth(owner);
      }
      if (cycle.age >= cycleDuration) {
        const overflow = Math.max(0, dt - elapsed) % cycleDuration;
        const remainder = overflow < 1e-9 ? 0 : overflow;
        beginOpening(owner);
        const next = cycles.get(owner);
        if (remainder > 0) {
          updateOpening(owner, Math.min(remainder, config.duration)); next.age = remainder;
          if (next.age >= config.duration) { next.active = false; states.delete(owner); openings.delete(owner); syncMaxHealth(owner); }
        }
      }
    }
    for (const [owner, state] of states) if (!owners.includes(owner) || !stage(owner) || state.world !== G.World) states.delete(owner);
    for (const owner of owners) {
      if (!isClone(owner) && learnedStage(owner) && !cycles.has(owner)) beginOpening(owner);
      migrate(owner);
      syncMaxHealth(owner);
      const level = stage(owner);
      if (!level) { states.delete(owner); continue; }
      if (states.get(owner)?.world !== G.World) {
        states.set(owner, { owner, world: G.World, age: 0, sampleT: 0, images: [], lastX: owner.x, lastY: owner.y });
      }
      const state = states.get(owner);
      if(state.level!==level){state.images=[];state.sampleT=0;state.level=level;state.lastX=owner.x;state.lastY=owner.y;}
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
  // Both the authored body pose and these flames read opening.age; no second animation clock.
  function drawOpening(ctx, f, level, ground) {
    const { x, y, age } = f, color = config.trails[level - 1].color;
    const energy = Math.max(0, Math.min(1, (age - .6) / (config.openingDuration - .6)));
    const burst = Math.max(0, age - config.openingDuration);
    const fade = f.released ? Math.max(0, 1 - burst) : 1;
    const rhythm = Math.pow(Math.max(0, Math.sin(age * (energy > .7 ? 16 : 10))), 3);
    ctx.save(); ctx.strokeStyle = ctx.fillStyle = color;
    if (ground) {
      if (!f.released) {
        // Broad, curved tongues rise behind the body; the face and fists remain readable.
        const growth = .65 + energy * .35, pulse = 1 + rhythm * (.04 + energy * .09);
        // A continuous bright core gathers behind the body, surrounded by an outward flame crown.
        const halo = ctx.createRadialGradient(x, y - 42, 12, x, y - 60, 94 + energy * 28);
        halo.addColorStop(0, color + 'ef'); halo.addColorStop(.55, color + '99'); halo.addColorStop(1, color + '00');
        ctx.fillStyle = halo; ctx.globalAlpha = .6 + energy * .3;
        ctx.fillRect(x - 125, y - 190, 250, 200);
        for (let layer = 0; layer < 3; layer++) {
          const width = (52 + energy * 32) * [1, .72, .45][layer] * pulse;
          const height = (125 + energy * 145) * growth * pulse * [1, .88, .64][layer];
          const glow = ctx.createLinearGradient(x, y + 6, x, y - height);
          glow.addColorStop(0, color + 'ee'); glow.addColorStop(.65, color + 'bb'); glow.addColorStop(1, color + '30');
          ctx.fillStyle = layer === 2 ? '#eaffdc' : layer ? color : glow;
          ctx.globalAlpha = layer === 2 ? .45 + energy * .25 : layer ? .7 + rhythm * .12 : .95;
          for (let i = 0; i < 7; i++) {
            const side = (i - 3) / 3, baseX = x + side * width * .65;
            const sway = Math.sin(age * (7 + i * .3) - i) * (9 + energy * 8);
            const tipX = baseX + side * 12 + sway;
            const tipY = y - height * (1 - Math.abs(side) * .35) - Math.sin(age * 11 + i) * 11;
            const w = (18 + energy * 10) * [1, .7, .5][layer];
            ctx.beginPath(); ctx.moveTo(baseX - w, y + 4);
            ctx.bezierCurveTo(baseX - w * 2, y - height * .4, tipX + w, tipY + height * .28, tipX, tipY);
            ctx.bezierCurveTo(tipX - w * .45, tipY + height * .23, baseX + w * 1.5, y - height * .25, baseX + w, y + 4);
            ctx.closePath(); ctx.fill();
            if (layer === 1 && (i === 0 || i === 3 || i === 6)) {
              ctx.strokeStyle = '#eaffdc'; ctx.lineWidth = 1.5 + energy; ctx.stroke();
            }
          }
        }
        ctx.globalAlpha = .55 + energy * .3; ctx.strokeStyle = color; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.ellipse(x, y + 2, 32 + energy * 38, 10 + energy * 10, 0, 0, Math.PI * 2); ctx.stroke();
      } else {
        // Project the shockwave onto the ground at the feet, rather than facing the camera.
        const groundDepth = .4;
        const radius = config.openingRadius * Math.min(1, .45 + burst * 3.5);
        for (let ring = 0; ring < 3; ring++) {
          ctx.globalAlpha = fade * (.9 - ring * .2); ctx.lineWidth = ring ? 3 : 9 * fade;
          ctx.strokeStyle = ring === 1 ? '#fffbdc' : color;
          const ringRadius = radius * (1 - ring * .17);
          ctx.beginPath(); ctx.ellipse(x, y, ringRadius, ringRadius * groundDepth, 0, 0, Math.PI * 2); ctx.stroke();
        }
        // Radial pressure streaks share the same ground projection and remain below the actor.
        const force = Math.max(0, 1 - burst / .65);
        ctx.save(); ctx.translate(x, y); ctx.scale(1, groundDepth); ctx.globalAlpha = force * .95;
        for (let i = 0; i < 20; i++) {
          const angle = i * Math.PI / 10, dx = Math.cos(angle), dy = Math.sin(angle);
          const inner = 56 + burst * 100, outer = inner + force * (i % 2 ? 85 : 130), w = force * (i % 2 ? 4 : 8);
          ctx.beginPath(); ctx.moveTo(dx * inner - dy * w, dy * inner + dx * w);
          ctx.lineTo(dx * outer, dy * outer);
          ctx.lineTo(dx * inner + dy * w, dy * inner - dx * w); ctx.closePath(); ctx.fill();
          ctx.strokeStyle = '#fffbdc'; ctx.lineWidth = 1.5; ctx.beginPath();
          ctx.moveTo(dx * inner, dy * inner); ctx.lineTo(dx * outer, dy * outer); ctx.stroke();
        }
        ctx.restore();
      }
    } else if (!f.released) {
      // Only narrow edge flames cross the actor layer, never a solid full-body color mask.
      ctx.lineWidth = 2 + energy; ctx.globalAlpha = .75 + energy * .25;
      for (const side of [-1, 1]) {
        for (let i = 0; i < 3; i++) {
          const rise = (age * (85 + energy * 65) + i * 59) % (120 + energy * 100);
          const sx = x + side * (34 + energy * 13 + Math.sin(age * 8 + i) * 5);
          const sy = y - rise;
          ctx.beginPath(); ctx.moveTo(sx, sy + 22);
          ctx.bezierCurveTo(sx - side * 14, sy + 8, sx + side * 15, sy - 9, sx + side * 3, sy - 30 - energy * 13);
          ctx.stroke();
        }
      }
      // Short white-hot edge flickers punctuate the last charge without crossing the face.
      if (energy > .35) for (const side of [-1, 1]) {
        if (Math.sin(age * 24 + side * 2) < .55) continue;
        const edge = x + side * (32 + energy * 11);
        ctx.globalAlpha = .9; ctx.strokeStyle = '#fffde6'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(edge + side * 4, y - 12);
        ctx.lineTo(edge - side * 4, y - 34); ctx.lineTo(edge + side * 8, y - 44);
        ctx.lineTo(edge + side * 2, y - 64); ctx.lineTo(edge + side * 9, y - 83); ctx.stroke();
      }
      ctx.fillStyle = '#fffbdc';
      for (let i = 0; i < 16; i++) {
        const rise = (age * (100 + energy * 110) + i * 29) % (130 + energy * 120);
        const side = i % 2 ? -1 : 1;
        const px = x + side * (24 + (i % 5) * 10) + Math.sin(age * 5 + i) * 6;
        ctx.globalAlpha = (1 - rise / 260) * .85;
        ctx.fillRect(Math.round(px), Math.round(y - rise), 2, 5 + energy * 10);
      }
    } else {
      // Airborne embers lift above the horizontal shock front; no vertical concentric disk.
      ctx.globalAlpha = fade * .65; ctx.fillStyle = color;
      for (let i = 0; i < 12; i++) {
        const side = i % 2 ? -1 : 1;
        const px = x + side * (28 + i * 5 + burst * 28);
        ctx.fillRect(Math.round(px), Math.round(y - 12 - (i % 4) * 14 - burst * 70), 2, 5);
      }
    }
    // Twelve fixed pebbles make the pressure buildup legible; all motion comes from the same age.
    if (energy > .12 || f.released) for (let i = 0; i < 12; i++) {
      const angle = i * Math.PI / 6 + .2, baseRadius = 44 + (i % 3) * 15;
      const scatter = f.released ? (1 - Math.pow(1 - burst, 2)) * (80 + i % 4 * 13) : 0;
      const tremble = !f.released ? Math.sin(age * 47 + i * 3) * energy * 2 : 0;
      const px = x + Math.cos(angle) * (baseRadius + scatter) + tremble;
      const py = y + Math.sin(angle) * (baseRadius + scatter) * .4;
      const lift = f.released ? Math.max(0, 32 + (i % 3) * 5 + burst * 50 - burst * burst * 155) : energy * (18 + i % 4 * 7);
      ctx.globalAlpha = f.released ? fade * .9 : Math.min(1, energy * 2);
      if (ground) {
        ctx.fillStyle = '#18261c'; ctx.beginPath(); ctx.ellipse(px, py + 3, 3 + i % 2, 1.5, 0, 0, Math.PI * 2); ctx.fill();
      } else {
        const size = 3 + i % 3;
        ctx.fillStyle = '#273328'; ctx.fillRect(Math.round(px - size / 2), Math.round(py - lift), size + 1, size);
        ctx.fillStyle = '#b6c59b'; ctx.fillRect(Math.round(px - size / 2), Math.round(py - lift), size, 1);
      }
    }
    ctx.restore();
  }
  function draw(ctx, ground) {
    for (const state of states.values()) {
      const owner = state.owner, level = stage(owner);
      if (!level || state.world !== G.World || state.level !== level) continue;
      const phase = state.age, x = owner.x, y = owner.y;
      const opening = openingFor(owner);
      if (opening) drawOpening(ctx, opening, level, ground);
      ctx.save();
      if (ground) {
        const alpha = ctx.globalAlpha;
        ctx.imageSmoothingEnabled = false;
        for (const ghost of state.images) {
          ctx.save();
          ctx.globalAlpha = alpha * ghost.opacity * Math.sqrt(ghost.ttl / ghost.life);
          ctx.translate(Math.round(ghost.x), Math.round(ghost.y));
          ctx.scale(ghost.scale, ghost.scale);
          ctx.drawImage(ghost.image, -96, -160);
          ctx.restore();
        }
        ctx.strokeStyle = config.trails[level - 1].color; ctx.globalAlpha = .25 + level * .06; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.ellipse(Math.round(x), Math.round(y), 20 + level, 7, 0, 0, Math.PI * 2); ctx.stroke();
      } else {
        const count = level >= 3 ? 8 : 5;
        ctx.fillStyle = config.trails[level - 1].color; ctx.globalAlpha = .35 + level * .06;
        for (let i = 0; i < count; i++) {
          const rise = (phase * (23 + level * 3) + i * 11) % (35 + level * 2);
          const sway = Math.sin(i * 2.3 + phase * 2) * (13 + level);
          ctx.fillRect(Math.round(x + sway), Math.round(y - rise - 3), 2, level >= 3 ? 5 : 3);
        }
      }
      ctx.restore();
    }
  }
  const C = G.Combat, previousTick = C.tick;
  C.tick = function(dt, owner, ...args) {
    if (performing(owner)) return;
    return previousTick.call(this, dt, owner, ...args);
  };
  const updateFields = C.updateFields, clearFields = C.clearFields;
  const ground = C.drawGroundFields, air = C.drawAirFields;
  C.updateFields = function(dt) { const result = updateFields.call(this, dt); update(dt); return result; };
  C.clearFields = function(owner) { const result = clearFields.call(this, owner); clear(owner); return result; };
  C.drawGroundFields = function(ctx) { ground.call(this, ctx); draw(ctx, true); };
  C.drawAirFields = function(ctx) { air.call(this, ctx); draw(ctx, false); };
  const afterimagesFor = owner => (states.get(owner)?.world === G.World && stage(owner) && states.get(owner).level === stage(owner) ? states.get(owner).images : [])
    .map(({ x, y, ttl, life, scale, color, opacity }) => ({ x, y, ttl, life, scale, color, opacity }));
  G.NarutoGates = { config, openingFor, charging, performing, presentationFor, learnedStage, status, stage, effectTier, level: stage, bonusPercent, healingMultiplier, attackSpeedMultiplier, inheritedRegen, maxHealthBonus, syncMaxHealth, afterimagesFor,
    active: owner => stage(owner) > 0,
    redSkin: owner => stage(owner) > 0, redForm: owner => stage(owner) >= 3,
    intense: owner => stage(owner) >= 3, migrate, update, clear,
    get afterimages() { return afterimagesFor(G.Game.player); } };
})();
