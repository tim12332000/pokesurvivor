/* Young Gaara: owned simulation-time sand techniques and a learned sand shield. */
(() => {
  if (G.NarutoGaara) return;
  const C = G.Combat, shieldId = 'naruto-sand-shield';
  const modes = new Set(['gaara-sand-burst', 'gaara-coffin', 'gaara-tsunami']);
  const capacities = [45, 60, 75, 90, 110], basicTimers = new WeakMap();
  const durations = {
    'gaara-sand-burst': [['windup', .16], ['release', .18], ['recovery', .18]],
    'gaara-coffin': [['seal', .22], ['bind', 1.1], ['crush', .2], ['recovery', .22]],
    'gaara-tsunami': [['seal', .25], ['raise', .22], ['surge', .65], ['burial', .5], ['recovery', .28]]
  };
  let action = null, shield = null;
  const alive = actor => !!actor && !actor.dead && actor.hp > 0;
  const valid = f => !!f && f.owner === G.Game.player && f.world === G.World && alive(f.owner) && f.owner.mon?.dex === 30007;
  const elite = e => !!(e.boss || e.elite || e.legend || e.judge);
  const supports = mode => modes.has(mode);
  function clearPath(ax, ay, bx, by) {
    const steps = Math.max(1, Math.ceil(Math.hypot(bx - ax, by - ay) / 4));
    for (let i = 1; i <= steps; i++) {
      const x = ax + (bx - ax) * i / steps, y = ay + (by - ay) * i / steps;
      if (G.World.isWall(x, y) || G.World.projectileBlock(x, y, 1)) return false;
    }
    return true;
  }
  const nearby = (x, y, range) => [...new Set(G.EnemyMgr.queryCircle(x, y, range))]
    .filter(e => alive(e) && Math.hypot(e.x - x, e.y - y) <= range && clearPath(x, y, e.x, e.y));
  function targetFor(owner, move) {
    const choices = nearby(owner.x, owner.y, move.range || 155);
    choices.sort((a, b) => Math.hypot(a.x - owner.x, a.y - owner.y) - Math.hypot(b.x - owner.x, b.y - owner.y));
    return choices.includes(owner.target) ? owner.target : choices[0];
  }
  function canCast(owner, move) {
    return supports(move?.digiMode) && !valid(action) && valid({ owner, world: G.World }) && !!targetFor(owner, move);
  }
  function cast(owner, move) {
    if (!canCast(owner, move)) return false;
    const target = targetFor(owner, move), snapshot = { ...move };
    action = { owner, world: G.World, move: snapshot, m: snapshot, kind: move.digiMode,
      phase: durations[move.digiMode][0][0], phaseAge: 0, age: 0, phaseIndex: 0,
      aim: Math.atan2(target.y - owner.y, target.x - owner.x), x: owner.x, y: owner.y,
      target, attack: owner.atk, victims: [], waveHits: new Set(), burialHits: new Set(), hit: false, slows: new Map() };
    return true;
  }
  function hit(f, e, ratio) {
    if (!valid(f) || !alive(e) || !clearPath(f.x, f.y, e.x, e.y)) return;
    const move = f.move, mult = G.Types.mult(move.type, e.types), crit = Math.random() < (f.owner.critChance || 0);
    const damage = move.dmg * ratio * f.attack * mult * G.Weather.mult(move.type) * (crit ? 1.5 : 1);
    e.hurt(damage, '#e6c985', e.x - f.x, e.y - f.y, move.knock || 0, crit ? 'crit' : G.Types.label(mult), f.owner);
    f.owner.onDealt(damage); f.owner.dmgDealt += damage;
    G.FX.burst(e.x, e.y - 10, '#e6c985', 5, 35);
  }
  function slow(f, e, strength) {
    let previous = f.slows.get(e);
    if (!previous) {
      previous = { value: e.slow || 0, time: e.slowT || 0, age: f.age, strength };
      f.slows.set(e, previous);
    }
    previous.strength = strength;
    const remaining = Math.max(0, previous.time - (f.age - previous.age));
    // Own only this pulse's timer. Native max(strength)/max(duration) would
    // accidentally grant our strong control the lifetime of a weaker slow.
    e.slow = Math.max(strength, remaining > 0 ? previous.value : 0);
    e.slowT = .12;
  }
  const applySlow = G.Enemy.prototype.applySlow;
  G.Enemy.prototype.applySlow = function(strength, duration = 1.2) {
    const f = action, prior = f?.slows.get(this);
    if (!prior) return applySlow.call(this, strength, duration);
    const remaining = Math.max(0, prior.time - (f.age - prior.age));
    prior.value = Math.max(remaining > 0 ? prior.value : 0, strength);
    prior.time = Math.max(remaining, duration); prior.age = f.age;
    this.slow = Math.max(prior.strength, prior.value); this.slowT = .12;
  };
  function releaseSlows(f) {
    for (const [e, prior] of f.slows) {
      e.slowT = Math.max(0, prior.time - (f.age - prior.age));
      e.slow = e.slowT > 0 ? prior.value : 0;
    }
    f.slows.clear();
  }
  function footprint(f, front = f.move.range) {
    const cosine = Math.cos(f.aim), sine = Math.sin(f.aim), range = f.move.range;
    return nearby(f.x, f.y, Math.hypot(range, f.move.width / 2)).filter(e => {
      const dx = e.x - f.x, dy = e.y - f.y, along = dx * cosine + dy * sine;
      return along >= 0 && along <= front && Math.abs(-dx * sine + dy * cosine) <= f.move.width * (.2 + .3 * along / range);
    });
  }
  function stepAction(f) {
    if (f.kind === 'gaara-sand-burst' && f.phase === 'release' && !f.hit) {
      f.hit = true;
      for (const enemy of footprint(f)) hit(f, enemy, 1);
    } else if (f.kind === 'gaara-coffin') {
      if (f.phase === 'bind') slow(f, f.target, elite(f.target) ? .3 : .95);
      if (f.phase === 'crush' && !f.hit) { f.hit = true; releaseSlows(f); hit(f, f.target, 1); }
    } else if (f.kind === 'gaara-tsunami') {
      if (f.phase === 'surge' || f.phase === 'burial') {
        const front = f.phase === 'surge' ? f.move.range * Math.min(1, f.phaseAge / .65) : f.move.range;
        for (const enemy of footprint(f, front)) if (!f.waveHits.has(enemy)) {
          f.waveHits.add(enemy); f.victims.push(enemy); hit(f, enemy, .25);
        }
        for (const enemy of f.victims) if (alive(enemy) && clearPath(f.x, f.y, enemy.x, enemy.y)) slow(f, enemy, elite(enemy) ? .35 : .95);
      }
      if (f.phase === 'recovery' && !f.hit) {
        f.hit = true; releaseSlows(f);
        for (const enemy of f.victims) if (!f.burialHits.has(enemy)) { f.burialHits.add(enemy); hit(f, enemy, .75); }
      }
    }
  }
  function shieldStage(owner = G.Game.player) {
    if (!owner || owner !== G.Game.player || owner.mon?.dex !== 30007 || !alive(owner)) return 0;
    const move = owner.moves.find(m => m.id === shieldId);
    return move ? Math.max(1, Math.min(5, move.lvl | 0)) : 0;
  }
  function syncShield(owner) {
    const stage = shieldStage(owner);
    if (!stage) { shield = null; return; }
    const capacity = capacities[stage - 1];
    if (!valid(shield)) shield = { owner, world: G.World, capacity, amount: capacity, progress: 0, flash: 0, age: 0 };
    else if (shield.capacity !== capacity) {
      shield.amount = Math.max(0, Math.min(capacity, shield.amount + capacity - shield.capacity)); shield.capacity = capacity;
    }
  }
  const addMove = G.Player.prototype.addMove;
  G.Player.prototype.addMove = function(id, ...args) {
    if (id !== shieldId || this.mon?.dex !== 30007) return addMove.call(this, id, ...args);
    if (this.hasMove(id)) return false;
    this.moves.push(G.Moves.instance(id)); syncShield(this); return true;
  };
  const levelUp = G.Moves.levelUp;
  G.Moves.levelUp = function(move, ...args) {
    const changed = levelUp.call(this, move, ...args);
    if (changed && move.id === shieldId && G.Game.player?.moves.includes(move)) syncShield(G.Game.player);
    return changed;
  };
  const hurt = G.Player.prototype.hurt;
  G.Player.prototype.hurt = function(amount, type = null, pure = false) {
    if (this !== G.Game.player || this.invuln > 0 || this.dead || this.frozen || !(amount > 0)) return hurt.call(this, amount, type, pure);
    syncShield(this);
    if (!valid(shield) || shield.amount <= 0) return hurt.call(this, amount, type, pure);
    const typed = type ? amount * G.Types.mult(type, this.mon.types) * G.Weather.mult(type) : amount;
    const close = this.activeGroup().some(m => m.kind === 'melee') ? .75 : 1;
    const damage = pure ? Math.max(1, typed) : Math.max(1, typed * (1 - this.reduction) * close);
    const absorbed = Math.min(shield.amount, damage);
    shield.amount -= absorbed; shield.flash = .2;
    G.FX.burst(this.x, this.y - 15, '#deb66d', 6, 40);
    if (absorbed >= damage) { this.invuln = .45; return; }
    const remaining = damage - absorbed;
    // Native hurt floors a hit to one point; shield overflow may legitimately be fractional.
    if (remaining < 1) this.hp += 1 - remaining;
    return hurt.call(this, amount * remaining / damage, type, pure);
  };
  function clear(owner) {
    if (action && (!owner || action.owner === owner)) { releaseSlows(action); action = null; }
    if (shield && (!owner || shield.owner === owner)) shield = null;
    if (owner) basicTimers.delete(owner);
  }
  function update(dt) {
    if (action && !valid(action)) { releaseSlows(action); action = null; }
    if (shield && !valid(shield)) shield = null;
    if (G.Game.state !== 'playing' || !(dt > 0) || !Number.isFinite(dt)) return;
    syncShield(G.Game.player);
    if (shield) {
      shield.age += dt; shield.flash = Math.max(0, shield.flash - dt);
      shield.progress += dt / Math.max(.05, 12 * shield.owner.cdMul);
      if (shield.progress >= 1) { shield.progress %= 1; shield.amount = shield.capacity; }
    }
    const f = action;
    if (!f) return;
    if (f.kind === 'gaara-coffin' && (!alive(f.target) || !clearPath(f.x, f.y, f.target.x, f.target.y))) {
      releaseSlows(f); action = null; return;
    }
    let left = dt;
    while (left > 1e-9 && action === f) {
      const duration = durations[f.kind][f.phaseIndex][1], step = Math.min(left, duration - f.phaseAge);
      f.phaseAge += step; f.age += step; left -= step; stepAction(f);
      if (f.phaseAge >= duration - 1e-9) {
        f.phaseIndex++;
        if (f.phaseIndex >= durations[f.kind].length) { releaseSlows(f); action = null; break; }
        f.phase = durations[f.kind][f.phaseIndex][0]; f.phaseAge = 0; stepAction(f);
      }
    }
  }
  const updateFields = C.updateFields, clearFields = C.clearFields, tick = C.tick;
  C.updateFields = function(dt) { const result = updateFields.call(this, dt); update(dt); return result; };
  C.clearFields = function(owner) { const result = clearFields.call(this, owner); clear(owner); return result; };
  C.tick = function(dt, owner, now) {
    if (owner?.mon?.dex === 30007 && G.Game.state !== 'playing') return;
    const result = tick.call(this, dt, owner, now);
    if (G.Game.state !== 'playing' || !valid({ owner, world: G.World }) || !(dt > 0)) return result;
    const selected = owner.activeGroup(), special = selected.find(m => ['gaara-coffin', 'gaara-tsunami'].includes(m.digiMode));
    if (!special || selected.some(m => m.digiMode === 'gaara-sand-burst')) return result;
    let timer = (basicTimers.get(owner) ?? .6) - dt;
    if (timer <= 0 && !action) {
      const basic = owner.moves.find(m => m.id === 'naruto-gaara');
      if (basic && canCast(owner, basic)) { owner.cast(basic); cast(owner, basic); timer = basic.cd * owner.cdMul; }
    }
    basicTimers.set(owner, timer);
    return result;
  };
  const ground = C.drawGroundFields, air = C.drawAirFields;
  function sandField(f) {
    const start = f.kind === 'gaara-tsunami' ? .47 : .16;
    return { ...f, t: Math.max(0, f.age - start), flowDuration: f.kind === 'gaara-tsunami' ? .65 : .08,
      bindDuration: f.kind === 'gaara-tsunami' ? .5 : 0, burstTime: f.kind === 'gaara-tsunami' ? 1.15 : .18,
      life: f.kind === 'gaara-tsunami' ? 1.43 : .36 };
  }
  C.drawGroundFields = function(ctx) {
    ground.call(this, ctx);
    if (valid(action) && action.kind !== 'gaara-coffin') G.NarutoSandVFX?.drawGround(ctx, sandField(action));
  };
  C.drawAirFields = function(ctx) {
    air.call(this, ctx);
    if (valid(action)) {
      if (action.kind !== 'gaara-coffin') G.NarutoSandVFX?.drawAir(ctx, sandField(action));
      else if (['bind', 'crush'].includes(action.phase)) {
        const f = action, g = { ...f, x: f.target.x - 10, y: f.target.y, aim: 0, m: { range: 20, width: 20 },
          t: .65 + (f.phase === 'crush' ? 1.1 + f.phaseAge : f.phaseAge), flowDuration: .65, bindDuration: 1.1,
          burstTime: 1.75, life: 2, victims: [f.target] };
        G.NarutoSandVFX?.drawAir(ctx, g);
      }
    }
    if (valid(shield)) {
      const s = shield, p = s.owner;
      ctx.save(); ctx.fillStyle = '#4d3014'; ctx.fillRect(Math.round(p.x - 19), Math.round(p.y + 7), 38, 4);
      ctx.fillStyle = '#edd395'; ctx.fillRect(Math.round(p.x - 18), Math.round(p.y + 8), 36 * s.amount / s.capacity, 2);
      if (s.amount > 0) {
        ctx.strokeStyle = s.flash > 0 ? '#fff0ca' : '#c79a53'; ctx.lineWidth = s.flash > 0 ? 5 : 2;
        ctx.beginPath(); ctx.ellipse(p.x, p.y - 18, 22, 29, 0, -.8, 1.7); ctx.stroke();
      }
      ctx.restore();
    }
  };
  G.NarutoGaara = { supports, canCast, cast, clear, update, shieldStage, capacities,
    active: owner => valid(action) && (!owner || action.owner === owner) ? action : null,
    shieldState: owner => valid(shield) && (!owner || shield.owner === owner) ? { ...shield, remaining: Math.max(0, (1 - shield.progress) * 12 * shield.owner.cdMul) } : null,
    get effects() { return valid(action) ? [action] : []; } };
})();
