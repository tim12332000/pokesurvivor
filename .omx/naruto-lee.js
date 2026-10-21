/* Young Lee's contact taijutsu. Timing, damage and landing splash are game adaptations. */
(() => {
  if (G.NarutoLee) return;
  const C = G.Combat, modes = new Set(['lee-lotus', 'lee-reverse-lotus']);
  const durations = { windup: .24, lift: .36, suspend: .42, descent: .22, slam: .20, recovery: .22 };
  const reverseDurations = { windup: .28, lift: .48, combo: 1.65, descent: .32, slam: .24, recovery: .28 };
  const basics = new WeakMap();
  let chain = null, finalSummary = null;
  const alive = actor => actor && !actor.dead && actor.hp > 0;
  const valid = f => f && f.owner === G.Game.player && f.world === G.World && alive(f.owner);
  const elite = e => !!(e.boss || e.elite || e.legend || e.judge);
  const supports = mode => modes.has(mode);
  const launchedLotus = f => supports(f.kind) && ['lift', 'suspend', 'combo', 'descent', 'slam', 'recovery'].includes(f.phase);
  const isInvulnerable = owner => !!valid(chain) && chain.owner === owner && chain.kind === 'lee-reverse-lotus' &&
    ['lift', 'combo', 'descent'].includes(chain.phase);
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
  const hitLiftFor = enemy => valid(chain) && chain.target === enemy ? chain.targetLift : 0;
  const liftFor = enemy => alive(enemy) ? hitLiftFor(enemy) : 0;
  function resetCamera(f) {
    if (f.cameraRaised && f.owner === G.Game.player && f.world === G.World && G.Camera) G.Camera.y = f.owner.y;
    f.cameraRaised = false;
  }
  function syncLift(f) {
    if (!['lift', 'suspend', 'combo', 'descent'].includes(f.phase) || elite(f.target)) { removeLift(f); return; }
    const reverse = f.kind === 'lee-reverse-lotus', base = reverse ? 60 : 40;
    f.visualLift = f.phase === 'lift' ? Math.sin(Math.min(1, f.phaseAge / f.durations.lift) * Math.PI / 2) * base :
      f.phase === 'descent' ? f.peakLift * Math.max(0, 1 - f.phaseAge / f.durations.descent) :
      f.phase === 'combo' ? base + f.ticks * 8 : base;
    f.targetLift = f.visualLift;
    // Follow only the excess height, keeping high-quantity kicks below the HUD.
    const camera = G.Camera;
    if (reverse && camera?.h > 0 && Number.isFinite(camera.y)) {
      const ceiling = f.owner.y - f.visualLift - 140 + camera.h / 2;
      if (camera.y > ceiling) { camera.y = ceiling; f.cameraRaised = true; }
    }
  }
  function clear(owner) {
    if (chain && (!owner || chain.owner === owner)) { releasePending(chain); resetCamera(chain); removeLift(chain); chain = null; }
    if (finalSummary && (!owner || finalSummary.owner === owner)) finalSummary = null;
  }
  const pendingDefeat = enemy => !!chain?.pendingDeath && valid(chain) && chain.target === enemy && !enemy.dead;
  function releasePending(f) {
    if (!f.pendingDeath || f.releasing) return;
    f.releasing = true;
    const target = f.target;
    if (!target.dead) {
      target.hp = 0;
      if (f.owner === G.Game.player && f.world === G.World) target.die();
      else { G.EnemyMgr.discard(target); target.dead = true; target.fade = 0; }
    }
    f.pendingDeath = false;
  }
  const enemyDie = G.Enemy.prototype.die;
  G.Enemy.prototype.die = function(...args) {
    const f = chain;
    if (valid(f) && f.kind === 'lee-reverse-lotus' && f.target === this && !this.remote &&
        !f.releasing && !this.dead && this.hp <= 0 && ['lift', 'combo', 'descent', 'slam'].includes(f.phase)) {
      if (!f.pendingDeath) { f.pendingDeath = true; f.anchorX = this.x; f.anchorY = this.y; }
      this.hp = 1; this.kx = this.ky = 0; this.touchCd = Math.max(.1, this.touchCd || 0);
      return;
    }
    return enemyDie.apply(this, args);
  };
  const enemyHurt = G.Enemy.prototype.hurt;
  G.Enemy.prototype.hurt = function(amount, ...args) {
    const f = chain, primary = valid(f) && f.kind === 'lee-reverse-lotus' && f.primaryHit && f.target === this && !this.dead;
    const result = enemyHurt.call(this, amount, ...args);
    // Later percent-health wrappers pass the complete incoming hit through here.
    // Match the native displayed integer, retaining shield and critical semantics.
    if (primary && Number.isFinite(amount)) { f.totalDamage += Math.max(1, Math.round(amount)); f.totalHits++; }
    return result;
  };
  function canCast(owner, move) {
    return supports(move?.digiMode) && !chain && owner?.dex === 30006 && valid({ owner, world: G.World }) && !!targetFor(owner, move);
  }
  function cast(owner, move) {
    if (!canCast(owner, move)) return false;
    const target = targetFor(owner, move);
    const snapshot = G.Quantity?.snapshot(owner, move) || { ...move };
    const quantity = Number.isFinite(snapshot.quantityBonusAtCast) ? Math.max(0, Math.floor(snapshot.quantityBonusAtCast)) : 0;
    const reverse = move.digiMode === 'lee-reverse-lotus';
    const comboHits = 5 + 2 * (Math.max(1, Math.min(5, snapshot.lvl | 0)) - 1) + quantity;
    const comboDuration = reverseDurations.combo / (1 + .025 * Math.max(0, comboHits - 5));
    const firstInterval = comboDuration * .1 / (1 - .9 ** comboHits);
    let elapsed = 0;
    const comboDeadlines = reverse ? Array.from({ length: comboHits }, (_, i) => (elapsed += firstInterval * .9 ** i)) : [];
    chain = { owner, world: G.World, target, kind: move.digiMode, move: snapshot,
      durations: reverse ? { ...reverseDurations, combo: comboDuration } : durations,
      comboHits, comboDeadlines, peakLift: reverse ? 60 + comboHits * 8 : 40,
      phase: 'approach', phaseAge: 0, age: 0, travel: 0, attack: owner.atk,
      visualLift: 0, targetLift: 0, ticks: 0, totalDamage: 0, totalHits: 0, pendingDeath: false };
    finalSummary = null;
    owner.svx = owner.svy = 0;
    return true;
  }
  function hit(f, enemy, ratio) {
    if (!valid(f) || !alive(enemy) || !clearPath(f.owner.x, f.owner.y, enemy.x, enemy.y)) return;
    const owner = f.owner, move = f.move, mult = G.Types.mult(move.type, enemy.types);
    const crit = owner.critChance > 0 && Math.random() < owner.critChance;
    const damage = move.dmg * ratio * f.attack * mult * G.Weather.mult(move.type) *
      (crit ? 1.5 : 1) * (G.NarutoSupport?.precisionMultiplier(owner, enemy) || 1);
    f.primaryHit = enemy === f.target;
    try { enemy.hurt(damage, '#f2ddab', enemy.x - owner.x, enemy.y - owner.y, 0, crit ? 'crit' : G.Types.label(mult), owner, move.id); }
    finally { f.primaryHit = false; }
    owner.onDealt(damage); owner.dmgDealt += damage;
    G.FX.burst(enemy.x, enemy.y - (enemy.jumpLift || 0) - hitLiftFor(enemy), '#f2ddab', 5, 40);
  }
  function enter(f, phase) {
    f.phase = phase; f.phaseAge = 0;
    if (phase === 'windup' && f.kind === 'lee-reverse-lotus') {
      // Approach time is part of the full 3.3-second action, not extra time.
      const fixed = ['windup', 'lift', 'descent', 'slam', 'recovery'].reduce((sum, key) => sum + f.durations[key], 0);
      const budget = Math.max(1 / 120, 3.3 - f.age - fixed);
      const scale = Math.min(1, budget / reverseDurations.combo);
      f.durations.combo *= scale;
      f.comboDeadlines = f.comboDeadlines.map(time => time * scale);
    }
    syncLift(f);
    if (phase === 'lift') hit(f, f.target, f.kind === 'lee-lotus' ? .2 : .1);
    if (phase === 'slam') {
      resetCamera(f);
      removeLift(f);
      hit(f, f.target, f.kind === 'lee-lotus' ? .8 : .3);
      const radius = f.move.radius || 60;
      for (const enemy of new Set(G.EnemyMgr.queryCircle(f.target.x, f.target.y, radius))) {
        if (enemy !== f.target && Math.hypot(enemy.x - f.target.x, enemy.y - f.target.y) <= radius + (enemy.r || 0)) hit(f, enemy, .35);
      }
      if (f.kind === 'lee-reverse-lotus') {
        // The outside rim marks the actual damage radius from the landing frame.
        G.FX.ring(f.target.x, f.target.y, radius, radius, '#ffe0a3', .42, 4);
        G.FX.ring(f.target.x, f.target.y, 5, radius, '#f6a65e', .36, 6);
        G.FX.burst(f.target.x, f.target.y, '#ddc99a', 16, radius * .65);
        G.Camera.kick(.18);
        releasePending(f);
      } else {
        G.FX.ring(f.target.x, f.target.y, radius, radius, '#f2d5a0', .32, 3);
        G.FX.ring(f.target.x, f.target.y, 5, radius, '#ddc99a', .28, 4);
        G.FX.burst(f.target.x, f.target.y, '#ddc99a', 8, 65);
        G.Camera.kick(.1);
      }
    }
  }
  function approach(f, dt) {
    const owner = f.owner, target = f.target;
    let budget = Math.min(480 * dt, (f.move.range || 145) - f.travel);
    // Rounding at contact can leave a subpixel gap whose step changes neither
    // the position nor budget. Tolerate that gap and bound collision sampling.
    const maxSteps = Math.ceil(budget / 4) + 1;
    for (let steps = 0; budget > .001 && steps < maxSteps; steps++) {
      const dx = target.x - owner.x, dy = target.y - owner.y, distance = Math.hypot(dx, dy);
      if (distance <= reach(f) + .001) { enter(f, 'windup'); return true; }
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
    if (finalSummary) {
      if (!valid(finalSummary)) finalSummary = null;
      else if (G.Game.state === 'playing' && dt > 0 && Number.isFinite(dt) && (finalSummary.ttl -= dt) <= 0) finalSummary = null;
    }
    if (!(dt > 0) || !Number.isFinite(dt) || !chain) return;
    const f = chain;
    if (f.pendingDeath && valid(f)) { f.target.x = f.anchorX; f.target.y = f.anchorY; f.target.kx = f.target.ky = 0; }
    if (!valid(f) || (!alive(f.target) && !launchedLotus(f)) || !clearPath(f.owner.x, f.owner.y, f.target.x, f.target.y)) { clear(); return; }
    if (G.Game.state !== 'playing') return;
    removeLift(f);
    // Fixed simulation steps retain all combo hits under a delayed frame.
    let remaining = Math.min(dt, 4);
    while (remaining > 1e-9 && chain === f) {
      const phaseRemaining = f.kind === 'lee-reverse-lotus' && f.phase !== 'approach' ?
        Math.max(1e-9, f.durations[f.phase] - f.phaseAge) : Infinity;
      const step = Math.min(remaining, 1 / 120, phaseRemaining); remaining -= step;
      f.age += step; f.phaseAge += step;
      if (f.phase === 'approach') {
        if (!approach(f, step) || f.age > .6) { clear(); return; }
        continue;
      }
      if ((!alive(f.target) && !launchedLotus(f)) || Math.hypot(f.target.x - f.owner.x, f.target.y - f.owner.y) > reach(f) + 24) { clear(); return; }
      if (f.phase === 'combo') {
        // A defeated bound target stays hittable until the landing resolves it.
        while (f.ticks < f.comboHits && f.phaseAge + 1e-9 >= f.comboDeadlines[f.ticks]) {
          f.ticks++; syncLift(f); hit(f, f.target, .12 * 1.1 ** f.ticks);
        }
      }
      if (f.phaseAge + 1e-9 >= f.durations[f.phase]) {
        const next = f.phase === 'windup' ? 'lift' : f.phase === 'lift' ?
          (f.kind === 'lee-reverse-lotus' ? 'combo' : 'suspend') : ['combo', 'suspend'].includes(f.phase) ? 'descent' : f.phase === 'descent' ? 'slam' : f.phase === 'slam' ? 'recovery' : null;
        if (!next) {
          const summary = f.kind === 'lee-reverse-lotus' && f.totalHits ?
            { owner: f.owner, world: f.world, totalDamage: f.totalDamage, totalHits: f.totalHits, ttl: 1 } : null;
          clear(); finalSummary = summary; return;
        }
        enter(f, next);
      }
    }
    if (chain !== f) return;
    syncLift(f);
    if (f.visualLift > 0) f.target.applySlow(.95, .08);
  }
  // Contact movement belongs to the technique even when experimental art is disabled.
  // Keep the normal update for animation/status timers; restore only its ground motion.
  const playerHurt = G.Player.prototype.hurt;
  G.Player.prototype.hurt = function() {
    if (isInvulnerable(this)) return;
    return playerHurt.apply(this, arguments);
  };
  const playerUpdate = G.Player.prototype.update;
  G.Player.prototype.update = function(dt) {
    if (chain && !valid(chain)) clear();
    if (chain?.owner !== this) return playerUpdate.call(this, dt);
    const frozen = this.frozen, x = this.x, y = this.y;
    this.frozen = true; this.svx = this.svy = 0;
    try { return playerUpdate.call(this, dt); }
    finally { this.frozen = frozen; this.x = x; this.y = y; }
  };
  const previousTick = C.tick;
  C.tick = function(dt, owner, now) {
    // Let a ready Lotus start first. Its complete contact sequence owns the body.
    const result = previousTick.call(this, dt, owner, now);
    if (G.Game.state !== 'playing' || !(dt > 0) || chain || owner?.dex !== 30006 ||
        !valid({ owner, world: G.World }) ||
        !owner.activeGroup().some(move => supports(move.digiMode) && move.t > 0)) return result;
    let basic = basics.get(owner);
    if (!basic || basic.world !== G.World) {
      const move = G.Moves.instance('tackle');
      move.name = '體術普攻'; move.type = 'fighting';
      basic = { world: G.World, move }; basics.set(owner, basic);
    }
    const target = targetFor(owner, { range: basic.move.radius });
    if (!target) { basic.move.t = Math.max(0, basic.move.t - dt); return result; }
    const activeGroup = owner.activeGroup, selectedTarget = owner.target;
    owner.activeGroup = () => [basic.move]; owner.target = target;
    owner.aim = Math.atan2(target.y - owner.y, target.x - owner.x);
    try { previousTick.call(this, dt, owner, now); }
    finally { owner.activeGroup = activeGroup; owner.target = selectedTarget; }
    return result;
  };
  const previousUpdate = C.updateFields, previousClear = C.clearFields;
  C.updateFields = function(dt) { const result = previousUpdate.call(this, dt); update(dt); return result; };
  C.clearFields = function(owner) { previousClear.call(this, owner); clear(owner); };
  if (G.DigimonSkills?.clear) { const previous = G.DigimonSkills.clear; G.DigimonSkills.clear = owner => { previous(owner); clear(owner); }; }
  const comboSummary = () => {
    const f = valid(chain) && chain.kind === 'lee-reverse-lotus' && chain.totalHits ? chain : finalSummary;
    return valid(f) ? Object.freeze({ totalDamage: f.totalDamage, totalHits: f.totalHits,
      pendingDeath: !!f.pendingDeath, finished: f === finalSummary }) : null;
  };
  const drawHud = G.HUD.draw;
  G.HUD.draw = function(ctx, w, h, owner, stats) {
    drawHud.call(this, ctx, w, h, owner, stats);
    const summary = owner === G.Game.player && comboSummary();
    if (!summary) return;
    const groupCount = owner.slots.length + owner.moves.filter(move => move.passive && !owner.slots.some(group => group.includes(move))).length;
    const controls = G.Touch.active ? G.Touch.controlLayout(w, h, Math.max(1, groupCount)) : null;
    const y = controls ? controls.bar.y - 16 : h - 110;
    ctx.save(); ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = `bold ${controls ? 16 : 18}px "Segoe UI",system-ui,sans-serif`; ctx.lineWidth = 4; ctx.strokeStyle = '#101627'; ctx.fillStyle = '#ffe0a3';
    const text = `${summary.totalHits} 連擊｜總傷害 ${summary.totalDamage.toLocaleString('zh-TW')}`;
    ctx.strokeText(text, w / 2, y, w - 24); ctx.fillText(text, w / 2, y, w - 24); ctx.restore();
  };
  G.NarutoLee = { supports, canCast, cast, clear, update, liftFor, hitLiftFor, isInvulnerable, pendingDefeat,
    get comboSummary() { return comboSummary(); }, get active() { return chain; } };
})();
