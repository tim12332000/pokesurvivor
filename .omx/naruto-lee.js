/* Young Lee's contact taijutsu. Timing, damage and landing splash are game adaptations. */
(() => {
  if (G.NarutoLee) return;
  const C = G.Combat, modes = new Set(['lee-lotus', 'lee-reverse-lotus']);
  const durations = { windup: .18, lift: .24, combo: .42, slam: .16, recovery: .18 };
  let chain = null;
  const alive = actor => actor && !actor.dead && actor.hp > 0;
  const valid = f => f && f.owner === G.Game.player && f.world === G.World && alive(f.owner);
  const elite = e => !!(e.boss || e.elite || e.legend || e.judge);
  const supports = mode => modes.has(mode);
  const reach = f => (f.owner.r || 12) + (f.target.r || 10) + 12;
  function clearPath(ax, ay, bx, by) {
    const steps = Math.max(1, Math.ceil(Math.hypot(bx - ax, by - ay) / 4));
    for (let i = 1; i <= steps; i++) {
      const x = ax + (bx - ax) * i / steps, y = ay + (by - ay) * i / steps;
      if (G.World.isWall(x, y) || G.World.projectileBlock(x, y, 1)) return false;
    }
    return true;
  }
  function targetFor(owner, move) {
    const range = move.range || 145;
    const candidates = [...new Set(G.EnemyMgr.queryCircle(owner.x, owner.y, range))]
      .filter(e => alive(e) && Math.hypot(e.x - owner.x, e.y - owner.y) <= range && clearPath(owner.x, owner.y, e.x, e.y));
    candidates.sort((a, b) => Math.hypot(a.x - owner.x, a.y - owner.y) - Math.hypot(b.x - owner.x, b.y - owner.y));
    return candidates.includes(owner.target) ? owner.target : candidates[0];
  }
  function removeLift(f) {
    if (f) { f.targetLift = 0; f.visualLift = 0; }
  }
  const liftFor = enemy => valid(chain) && alive(enemy) && chain.target === enemy ? chain.targetLift : 0;
  function clear(owner) {
    if (chain && (!owner || chain.owner === owner)) { removeLift(chain); chain = null; }
  }
  function canCast(owner, move) {
    return supports(move?.digiMode) && !chain && owner?.dex === 30006 && valid({ owner, world: G.World }) && !!targetFor(owner, move);
  }
  function cast(owner, move) {
    if (!canCast(owner, move)) return false;
    const target = targetFor(owner, move);
    chain = { owner, world: G.World, target, kind: move.digiMode, move: { ...move },
      phase: 'approach', phaseAge: 0, age: 0, travel: 0, attack: owner.atk,
      visualLift: 0, targetLift: 0, ticks: 0 };
    owner.svx = owner.svy = 0;
    return true;
  }
  function hit(f, enemy, ratio) {
    if (!valid(f) || !alive(enemy) || !clearPath(f.owner.x, f.owner.y, enemy.x, enemy.y)) return;
    const owner = f.owner, move = f.move, mult = G.Types.mult(move.type, enemy.types);
    const crit = owner.critChance > 0 && Math.random() < owner.critChance;
    const damage = move.dmg * ratio * f.attack * mult * G.Weather.mult(move.type) *
      (crit ? 1.5 : 1) * (G.NarutoSupport?.precisionMultiplier(owner, enemy) || 1);
    enemy.hurt(damage, '#f2ddab', enemy.x - owner.x, enemy.y - owner.y, 0, crit ? 'crit' : G.Types.label(mult), owner);
    owner.onDealt(damage); owner.dmgDealt += damage;
    G.FX.burst(enemy.x, enemy.y - (enemy.jumpLift || 0) - liftFor(enemy), '#f2ddab', 5, 40);
  }
  function enter(f, phase) {
    f.phase = phase; f.phaseAge = 0;
    if (phase === 'lift') hit(f, f.target, f.kind === 'lee-lotus' ? .2 : .1);
    if (phase === 'slam') {
      removeLift(f);
      hit(f, f.target, f.kind === 'lee-lotus' ? .8 : .3);
      const radius = f.move.radius || 60;
      for (const enemy of new Set(G.EnemyMgr.queryCircle(f.target.x, f.target.y, radius))) {
        if (enemy !== f.target && Math.hypot(enemy.x - f.target.x, enemy.y - f.target.y) <= radius + (enemy.r || 0)) hit(f, enemy, .35);
      }
      G.FX.ring(f.target.x, f.target.y, 5, radius, '#ddc99a', .28, 3);
    }
  }
  function approach(f, dt) {
    const owner = f.owner, target = f.target;
    let budget = Math.min(480 * dt, (f.move.range || 145) - f.travel);
    while (budget > 0) {
      const dx = target.x - owner.x, dy = target.y - owner.y, distance = Math.hypot(dx, dy);
      if (distance <= reach(f)) { enter(f, 'windup'); return true; }
      const step = Math.min(4, budget, distance - reach(f));
      const x = owner.x + dx / distance * step, y = owner.y + dy / distance * step;
      if (!G.World.isFree(x, y, owner.r || 12, true) || !clearPath(owner.x, owner.y, x, y)) return false;
      owner.x = x; owner.y = y; f.travel += step; budget -= step;
      owner.aim = owner.moveAngle = Math.atan2(dy, dx); owner.attackFace = .15;
      if (owner.anim) owner.anim.dir = G.Sprites.dirFromAngle(owner.aim);
    }
    if (Math.hypot(target.x - owner.x, target.y - owner.y) <= reach(f) + .001) enter(f, 'windup');
    return f.phase !== 'approach' || f.travel < (f.move.range || 145) - .001;
  }
  function update(dt) {
    if (!(dt > 0) || !Number.isFinite(dt) || !chain) return;
    const f = chain;
    if (!valid(f) || !alive(f.target) || !clearPath(f.owner.x, f.owner.y, f.target.x, f.target.y)) { clear(); return; }
    if (G.Game.state !== 'playing') return;
    removeLift(f);
    // Fixed simulation steps retain all combo hits under a delayed frame.
    let remaining = Math.min(dt, 3);
    while (remaining > 1e-9 && chain === f) {
      const step = Math.min(remaining, 1 / 120); remaining -= step;
      f.age += step; f.phaseAge += step;
      if (f.phase === 'approach') {
        if (!approach(f, step) || f.age > .6) { clear(); return; }
        continue;
      }
      if (!alive(f.target) || Math.hypot(f.target.x - f.owner.x, f.target.y - f.owner.y) > reach(f) + 24) { clear(); return; }
      if (f.phase === 'combo') {
        const due = Math.min(5, Math.floor(f.phaseAge / (durations.combo / 5) + 1e-8));
        while (f.ticks < due && alive(f.target)) { f.ticks++; hit(f, f.target, .12); }
      }
      if (f.phaseAge + 1e-9 >= durations[f.phase]) {
        const next = f.phase === 'windup' ? 'lift' : f.phase === 'lift' ?
          (f.kind === 'lee-reverse-lotus' ? 'combo' : 'slam') : f.phase === 'combo' ? 'slam' : f.phase === 'slam' ? 'recovery' : null;
        if (!next) { clear(); return; }
        enter(f, next);
      }
    }
    if (chain !== f) return;
    if (['lift', 'combo'].includes(f.phase) && !elite(f.target)) {
      f.visualLift = f.phase === 'lift' ? Math.sin(Math.min(1, f.phaseAge / durations.lift) * Math.PI / 2) * 30 : 30;
      f.targetLift = f.visualLift;
      f.target.applySlow(.95, .08);
    }
  }
  // Contact movement belongs to the technique even when experimental art is disabled.
  // Keep the normal update for animation/status timers; restore only its ground motion.
  const playerUpdate = G.Player.prototype.update;
  G.Player.prototype.update = function(dt) {
    if (chain && !valid(chain)) clear();
    if (chain?.owner !== this) return playerUpdate.call(this, dt);
    const frozen = this.frozen, x = this.x, y = this.y;
    this.frozen = true; this.svx = this.svy = 0;
    try { return playerUpdate.call(this, dt); }
    finally { this.frozen = frozen; this.x = x; this.y = y; }
  };
  const previousUpdate = C.updateFields, previousClear = C.clearFields;
  C.updateFields = function(dt) { const result = previousUpdate.call(this, dt); update(dt); return result; };
  C.clearFields = function(owner) { previousClear.call(this, owner); clear(owner); };
  if (G.DigimonSkills?.clear) { const previous = G.DigimonSkills.clear; G.DigimonSkills.clear = owner => { previous(owner); clear(owner); }; }
  G.NarutoLee = { supports, canCast, cast, clear, update, liftFor, get active() { return chain; } };
})();
