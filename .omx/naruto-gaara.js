/* Young Gaara: owned simulation-time sand techniques and a learned sand shield. */
(() => {
  if (G.NarutoGaara) return;
  const C = G.Combat, shieldId = 'naruto-sand-shield', prisonId = 'naruto-sand-prison';
  const modes = new Set(['gaara-sand-burst', 'gaara-coffin', 'gaara-tsunami']);
  const capacities = [45, 60, 75, 90, 110], basicTimers = new WeakMap();
  const durations = {
    'gaara-sand-burst': [['windup', .12], ['release', .24], ['recovery', .14]],
    'gaara-coffin': [['seal', .22], ['bind', 1.1], ['crush', .2], ['recovery', .22]],
    'gaara-tsunami': [['seal', .25], ['raise', .22], ['surge', .65], ['burial', .5], ['impact', .12], ['recovery', .16]]
  };
  let action = null, shield = null, prison = null;
  const bullets = [];
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
    choices.sort((a, b) => (move.digiMode === 'gaara-coffin' ? Number(elite(b)) - Number(elite(a)) : 0) ||
      Math.hypot(a.x - owner.x, a.y - owner.y) - Math.hypot(b.x - owner.x, b.y - owner.y));
    return move.digiMode !== 'gaara-coffin' && choices.includes(owner.target) ? owner.target : choices[0];
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
    if (action.kind === 'gaara-sand-burst') {
      action.baseCount = Math.max(1, (snapshot.quantityBaseCount ?? snapshot.count) | 0);
      action.count = snapshot.quantityBonusAtCast != null ? Math.max(1, snapshot.count | 0)
        : G.Quantity?.count(owner, action.baseCount, 1) ?? action.baseCount;
      action.interval = Math.min(.08, .32 / Math.max(1, action.count - 1));
      action.emitted = 0;
    }
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
  function emitBullet(f) {
    const vx = Math.cos(f.aim), vy = Math.sin(f.aim);
    f.emitted++;
    // The muzzle offset must not teleport sand through an adjacent wall.
    if (!clearPath(f.owner.x, f.owner.y, f.owner.x + vx * 12, f.owner.y + vy * 12)) return;
    bullets.push({ owner: f.owner, world: f.world, move: f.move, m: f.move, attack: f.attack,
      x: f.owner.x + vx * 12, y: f.owner.y + vy * 12, aim: f.aim,
      vx: vx * 420, vy: vy * 420, age: 0, range: f.move.range, distance: 0,
      radius: 4, damageRatio: 1 / f.baseCount });
  }
  function updateBullets(dt) {
    for (let i = bullets.length - 1; i >= 0; i--) {
      const b = bullets[i];
      if (!valid(b)) { bullets.splice(i, 1); continue; }
      const travel = Math.min(420 * dt, b.range - b.distance), steps = Math.max(1, Math.ceil(travel / 2));
      let gone = false;
      for (let j = 0; j < steps && !gone; j++) {
        b.x += Math.cos(b.aim) * travel / steps; b.y += Math.sin(b.aim) * travel / steps;
        b.distance += travel / steps;
        if (G.World.isWall(b.x, b.y) || G.World.projectileBlock(b.x, b.y, b.radius)) { gone = true; break; }
        const victims = [...new Set(G.EnemyMgr.queryCircle(b.x, b.y, 80))]
          .filter(e => alive(e) && Math.hypot(e.x - b.x, e.y - b.y) <= b.radius + (e.r || 8))
          .sort((a, c) => Math.hypot(a.x - b.x, a.y - b.y) - Math.hypot(c.x - b.x, c.y - b.y));
        if (victims.length) { hit(b, victims[0], b.damageRatio); gone = true; }
      }
      b.age += travel / 420;
      if (gone || b.distance >= b.range - 1e-9) bullets.splice(i, 1);
    }
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
  function releaseSlow(f, e) {
    const prior = f.slows.get(e);
    if (!prior) return;
    e.slowT = Math.max(0, prior.time - (f.age - prior.age));
    e.slow = e.slowT > 0 ? prior.value : 0;
    f.slows.delete(e);
  }
  function releaseSlows(f) { for (const e of f.slows.keys()) releaseSlow(f, e); }
  function footprint(f, front = f.move.range) {
    const cosine = Math.cos(f.aim), sine = Math.sin(f.aim), range = f.move.range;
    return nearby(f.x, f.y, Math.hypot(range, f.move.width / 2)).filter(e => {
      const dx = e.x - f.x, dy = e.y - f.y, along = dx * cosine + dy * sine;
      return along >= 0 && along <= front && Math.abs(-dx * sine + dy * cosine) <= f.move.width * (.2 + .3 * along / range);
    });
  }
  function stepAction(f) {
    if (f.kind === 'gaara-sand-burst' && f.phase === 'release') {
      while (f.emitted < f.count && f.phaseAge + 1e-9 >= f.emitted * f.interval) emitBullet(f);
    } else if (f.kind === 'gaara-coffin') {
      if (f.phase === 'bind') slow(f, f.target, elite(f.target) ? .3 : .95);
      if (f.phase === 'crush' && !f.hit) { f.hit = true; releaseSlows(f); hit(f, f.target, 1); }
    } else if (f.kind === 'gaara-tsunami') {
      if (f.phase === 'surge') {
        const front = f.move.range * Math.min(1, f.phaseAge / .65), previousFront = f.waveFront ?? 0;
        for (const enemy of footprint(f, front)) if (!f.waveHits.has(enemy) &&
          (enemy.x - f.x) * Math.cos(f.aim) + (enemy.y - f.y) * Math.sin(f.aim) >= previousFront) {
          f.waveHits.add(enemy); f.victims.push(enemy); hit(f, enemy, .25);
        }
        f.waveFront = front;
      }
      const inside = new Set(footprint(f));
      if (['surge', 'burial'].includes(f.phase)) for (const enemy of f.victims) {
        if (inside.has(enemy)) slow(f, enemy, elite(enemy) ? .35 : .95);
        else releaseSlow(f, enemy);
      }
      if (f.phase === 'impact' && !f.hit) {
        f.burialImpact = true;
        f.hit = true; releaseSlows(f);
        for (const enemy of f.victims) if (inside.has(enemy) && !f.burialHits.has(enemy)) { f.burialHits.add(enemy); hit(f, enemy, .75); }
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
    const capacity = capacities[stage - 1] + Math.max(1, owner.level || 1) * stage;
    if (!valid(shield)) shield = { owner, world: G.World, capacity, amount: capacity, progress: 0, flash: 0, flashAim: null, hitAim: null, broken: false, age: 0 };
    else if (shield.capacity !== capacity) {
      shield.amount = Math.max(0, Math.min(capacity, shield.amount + capacity - shield.capacity)); shield.capacity = capacity;
    }
  }
  function prisonMove(owner = G.Game.player) {
    return valid({ owner, world: G.World }) ? owner.moves.find(m => m.id === prisonId) : null;
  }
  function syncPrison(owner = G.Game.player) {
    if (!prisonMove(owner)) { prison = null; return; }
    if (!valid(prison)) prison = { owner, world: G.World, progress: 0, field: null };
  }
  // Ground control never changes native slow timers, and is checked at the enemy's
  // current position rather than from a stale list gathered on the previous frame.
  const grounded = enemy => !enemy.flying && !enemy.jump && !(enemy.jumpLift > 0);
  function insidePrison(enemy) {
    const field = prison?.field;
    return !!field && valid(prison) && !!prisonMove(prison.owner) && alive(enemy) && grounded(enemy) &&
      field.age < field.duration && Math.hypot(enemy.x - field.x, enemy.y - field.y) <= field.radius &&
      clearPath(field.x, field.y, enemy.x, enemy.y);
  }
  function updatePrison(dt) {
    syncPrison();
    const state = prison;
    if (!state) return;
    let left = dt;
    while (left > 1e-9 && prison === state && valid(state) && prisonMove(state.owner)) {
      const cooldown = Math.max(.05, 6 * (state.owner.cdMul || 1));
      const field = state.field;
      const step = Math.min(left, Math.max(0, (1 - state.progress) * cooldown),
        field ? Math.max(0, Math.min(field.nextTick, field.duration) - field.age) : Infinity);
      state.progress += step / cooldown;
      if (field) { field.age += step; field.t = field.age; field.remaining = Math.max(0, field.duration - field.age); }
      left -= step;
      if (field && field.age + 1e-9 >= field.nextTick && field.nextTick <= field.duration) {
        field.ticks++;
        for (const enemy of nearby(field.x, field.y, field.radius)) if (grounded(enemy)) hit(field, enemy, 1);
        field.nextTick = (field.ticks + 1) * field.tickInterval;
      }
      if (field && field.age + 1e-9 >= field.duration) state.field = null;
      if (state.progress + 1e-9 >= 1) {
        state.progress = 0;
        const move = prisonMove(state.owner);
        const target = nearby(state.owner.x, state.owner.y, move.range || 300).filter(grounded)
          .sort((a, b) => Math.hypot(a.x - state.owner.x, a.y - state.owner.y) - Math.hypot(b.x - state.owner.x, b.y - state.owner.y))[0];
        if (target) {
          const snapshot = { ...move };
          state.field = { owner: state.owner, world: state.world, move: snapshot, m: snapshot, attack: state.owner.atk,
            x: target.x, y: target.y, radius: snapshot.radius || 90, age: 0, t: 0,
            duration: 3, life: 3, remaining: 3, nextTick: .5, tickInterval: .5, ticks: 0 };
        }
      }
    }
  }
  const addMove = G.Player.prototype.addMove;
  G.Player.prototype.addMove = function(id, ...args) {
    if (![shieldId, prisonId].includes(id) || this.mon?.dex !== 30007) return addMove.call(this, id, ...args);
    if (this.hasMove(id)) return false;
    this.moves.push(G.Moves.instance(id));
    if (id === shieldId) syncShield(this); else syncPrison(this);
    return true;
  };
  const levelUp = G.Moves.levelUp;
  G.Moves.levelUp = function(move, ...args) {
    const changed = levelUp.call(this, move, ...args);
    if (changed && move.id === shieldId && G.Game.player?.moves.includes(move)) syncShield(G.Game.player);
    return changed;
  };
  const hurt = G.Player.prototype.hurt;
  G.Player.prototype.hurt = function(amount, type = null, pure = false, context = null) {
    if (this !== G.Game.player || this.invuln > 0 || this.dead || this.frozen || !(amount > 0)) return hurt.call(this, amount, type, pure, context);
    syncShield(this);
    if (!valid(shield) || shield.amount <= 0) return hurt.call(this, amount, type, pure, context);
    const typed = type ? amount * G.Types.mult(type, this.mon.types) * G.Weather.mult(type) : amount;
    const close = this.activeGroup().some(m => m.kind === 'melee') ? .75 : 1;
    const damage = pure ? Math.max(1, typed) : Math.max(1, typed * (1 - this.reduction) * close);
    const absorbed = Math.min(shield.amount, damage);
    shield.amount -= absorbed; shield.flash = .2; shield.broken = shield.amount <= 0;
    shield.flashAim = Number.isFinite(context?.fromX) && Number.isFinite(context?.fromY) &&
      Math.hypot(context.fromX - this.x, context.fromY - this.y) > 1e-9
      ? Math.atan2(context.fromY - this.y, context.fromX - this.x)
      : Number.isFinite(context?.vx) && Number.isFinite(context?.vy) && Math.hypot(context.vx, context.vy) > 1e-9
        ? Math.atan2(-context.vy, -context.vx) : null;
    shield.hitAim = shield.flashAim;
    G.FX.burst(this.x, this.y - 15, '#deb66d', 6, 40);
    if (absorbed >= damage) { this.invuln = .45; return; }
    const remaining = damage - absorbed;
    // Native hurt floors a hit to one point; shield overflow may legitimately be fractional.
    if (remaining < 1) this.hp += 1 - remaining;
    return hurt.call(this, amount * remaining / damage, type, pure, context);
  };
  function clear(owner) {
    for (let i = bullets.length - 1; i >= 0; i--) if (!owner || bullets[i].owner === owner) bullets.splice(i, 1);
    if (action && (!owner || action.owner === owner)) { releaseSlows(action); action = null; }
    if (shield && (!owner || shield.owner === owner)) shield = null;
    if (prison && (!owner || prison.owner === owner)) prison = null;
    if (owner) basicTimers.delete(owner);
  }
  function update(dt) {
    if (action && !valid(action)) { releaseSlows(action); action = null; }
    if (shield && !valid(shield)) shield = null;
    if (prison && (!valid(prison) || !prisonMove(prison.owner))) prison = null;
    for (let i = bullets.length - 1; i >= 0; i--) if (!valid(bullets[i])) bullets.splice(i, 1);
    if (G.Game.state !== 'playing' || !(dt > 0) || !Number.isFinite(dt)) return;
    syncShield(G.Game.player);
    updatePrison(dt);
    if (shield) {
      shield.age += dt; shield.flash = Math.max(0, shield.flash - dt);
      shield.progress += dt / Math.max(.05, 12 * shield.owner.cdMul);
      if (shield.progress >= 1) { shield.progress %= 1; shield.amount = shield.capacity; }
    }
    const f = action;
    if (!f) { updateBullets(dt); return; }
    if (f.kind === 'gaara-coffin' && (!alive(f.target) || !clearPath(f.x, f.y, f.target.x, f.target.y))) {
      releaseSlows(f); action = null; updateBullets(dt); return;
    }
    let left = dt;
    while (left > 1e-9 && action === f) {
      const duration = f.kind === 'gaara-sand-burst' && f.phase === 'release'
        ? (f.count - 1) * f.interval + .08 : durations[f.kind][f.phaseIndex][1];
      let step = Math.min(left, duration - f.phaseAge);
      if (f.kind === 'gaara-sand-burst' && f.phase === 'release' && f.emitted < f.count)
        step = Math.min(step, Math.max(0, f.emitted * f.interval - f.phaseAge));
      updateBullets(step);
      f.phaseAge += step; f.age += step; left -= step; stepAction(f);
      if (f.phaseAge >= duration - 1e-9) {
        f.phaseIndex++;
        if (f.phaseIndex >= durations[f.kind].length) { releaseSlows(f); action = null; break; }
        f.phase = durations[f.kind][f.phaseIndex][0]; f.phaseAge = 0; stepAction(f);
      }
    }
    if (left > 0) updateBullets(left);
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
    const inside = new Set(footprint(f));
    const victims = f.victims.filter(enemy => inside.has(enemy) &&
      (!['impact', 'recovery'].includes(f.phase) || f.burialHits.has(enemy)));
    return { ...f, victims, t: Math.max(0, f.age - start), flowDuration: f.kind === 'gaara-tsunami' ? .65 : .08,
      bindDuration: f.kind === 'gaara-tsunami' ? .5 : 0, burstTime: f.kind === 'gaara-tsunami' ? 1.15 : .18,
      life: f.kind === 'gaara-tsunami' ? 1.43 : .36 };
  }
  C.drawGroundFields = function(ctx) {
    ground.call(this, ctx);
    if (valid(shield)) G.NarutoSandVFX?.drawShield(ctx, shield, 'ground');
    if (valid(action) && action.kind === 'gaara-tsunami') G.NarutoSandVFX?.drawGround(ctx, sandField(action));
    if (valid(prison) && prisonMove(prison.owner) && prison.field) G.NarutoSandVFX?.drawPrison(ctx, prison.field);
  };
  C.drawAirFields = function(ctx) {
    air.call(this, ctx);
    if (valid(action)) {
      if (action.kind === 'gaara-tsunami') G.NarutoSandVFX?.drawAir(ctx, sandField(action));
      else if (action.kind === 'gaara-coffin') G.NarutoSandVFX?.drawCoffin(ctx, action);
      else G.NarutoSandVFX?.drawSandRelease(ctx, action);
    }
    for (const bullet of bullets) if (valid(bullet)) G.NarutoSandVFX?.drawBullet(ctx, bullet);
    if (valid(shield)) G.NarutoSandVFX?.drawShield(ctx, shield);
  };
  G.NarutoGaara = { supports, canCast, cast, clear, update, shieldStage, capacities,
    active: owner => valid(action) && (!owner || action.owner === owner) ? action : null,
    shieldState: owner => {
      syncShield(G.Game.player);
      return valid(shield) && (!owner || shield.owner === owner) ? { ...shield, remaining: Math.max(0, (1 - shield.progress) * 12 * shield.owner.cdMul) } : null;
    },
    sandPrisonState: owner => {
      if (prison && (!valid(prison) || !prisonMove(prison.owner))) prison = null;
      return prison?.field && (!owner || prison.owner === owner) ? { ...prison.field } : null;
    },
    prisonCooldownState: owner => valid(prison) && prisonMove(prison.owner) && (!owner || prison.owner === owner)
      ? { progress: prison.progress, remaining: (1 - prison.progress) * 6 * (prison.owner.cdMul || 1) } : null,
    rooted: enemy => insidePrison(enemy) && !elite(enemy),
    prisonSlow: enemy => insidePrison(enemy) && elite(enemy) ? .35 : 0,
    get bullets() { return bullets.filter(valid); },
    get effects() { return valid(action) ? [action] : []; } };
})();
