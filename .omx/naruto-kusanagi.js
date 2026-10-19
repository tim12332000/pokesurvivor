/* Sasuke's sword is canonical; autonomous orbit is this edition's adaptation. */
(() => {
  if (G.NarutoKusanagi) return;
  const id = 'naruto-kusanagi', states = new Map();
  const config = Object.freeze({ tick: .35, bladeHalfLength: 18, bladeRadius: 7, angularSpeed: 2.4 });
  const alive = owner => owner && !owner.dead && owner.hp > 0;
  const learned = owner => owner?.mon?.dex === 30002 && alive(owner) && owner.moves?.find(m => m.id === id);
  function clear(owner) { if (owner) states.delete(owner); else states.clear(); }
  function activate(owner) {
    if (!learned(owner) || !G.Game.everyone().includes(owner)) return false;
    if (states.get(owner)?.world !== G.World)
      states.set(owner, { owner, world: G.World, age: 0, hits: new Map(), blades: [] });
    return true;
  }
  const addMove = G.Player.prototype.addMove;
  G.Player.prototype.addMove = function(moveId, ...args) {
    if (this.mon?.dex === 30002) this.maxMoves = Math.max(5, this.maxMoves);
    const previous = this.activeGroup(), added = addMove.call(this, moveId, ...args);
    if (added && moveId === id && previous?.some(m => !m.passive)) {
      const index = this.slots.indexOf(previous); if (index >= 0) this.active = index;
    }
    return added;
  };
  function blades(state, move) {
    const count = Math.max(1, (move.count || 1) + (G.Quantity?.bonus(state.owner) || 0) + (G.NarutoSharingan?.projectileBonus(state.owner, move) || 0));
    return Array.from({ length: count }, (_, index) => {
      const angle = state.age * config.angularSpeed + index * Math.PI * 2 / count;
      return { x: state.owner.x + Math.cos(angle) * move.radius,
        y: state.owner.y + Math.sin(angle) * move.radius, angle: angle + Math.PI / 2 };
    });
  }
  function contact(enemy, blade) {
    const dx = Math.cos(blade.angle) * config.bladeHalfLength, dy = Math.sin(blade.angle) * config.bladeHalfLength;
    const ax = blade.x - dx, ay = blade.y - dy, vx = dx * 2, vy = dy * 2;
    const t = Math.max(0, Math.min(1, ((enemy.x - ax) * vx + (enemy.y - ay) * vy) / (vx * vx + vy * vy)));
    return Math.hypot(enemy.x - ax - t * vx, enemy.y - ay - t * vy) <= config.bladeRadius + (enemy.r || 0);
  }
  function update(dt) {
    const owners = G.Game.everyone();
    for (const [owner, state] of states) if (!owners.includes(owner) || !learned(owner) || state.world !== G.World) clear(owner);
    if (!(dt > 0) || !Number.isFinite(dt)) return;
    for (const owner of owners) {
      const move = learned(owner); if (!move) continue;
      const state = states.get(owner); if (!state) continue;
      const steps = Math.max(1, Math.ceil(Math.min(dt, .35) / (1 / 60))), step = Math.min(dt, .35) / steps;
      for (let i = 0; i < steps; i++) {
        state.age += step; state.blades = blades(state, move);
        const enemies = G.EnemyMgr.queryCircle(owner.x, owner.y, move.radius + config.bladeHalfLength + 40);
        for (const enemy of new Set(enemies)) {
          if (!alive(enemy) || (state.hits.get(enemy) ?? -Infinity) > state.age || !state.blades.some(blade => contact(enemy, blade))) continue;
          const mult = G.Types.mult(move.type, enemy.types), damage = move.dmg * owner.atk * mult * G.Weather.mult(move.type);
          if (!(damage > 0)) continue;
          state.hits.set(enemy, state.age + config.tick);
          enemy.hurt(damage, '#b6ddff', enemy.x - owner.x, enemy.y - owner.y, move.knock || 0, G.Types.label(mult), owner);
          owner.onDealt(damage); owner.dmgDealt += damage;
        }
      }
      for (const [enemy, until] of state.hits) if (!alive(enemy) || until < state.age - 1) state.hits.delete(enemy);
    }
  }
  function draw(ctx) {
    for (const state of states.values()) {
      if (!learned(state.owner) || state.world !== G.World) continue;
      for (const blade of state.blades) {
        if (!G.Camera.sees(blade.x, blade.y, 50)) continue;
        ctx.save(); ctx.translate(Math.round(blade.x), Math.round(blade.y - G.LIFT)); ctx.rotate(blade.angle);
        ctx.fillStyle = '#172239'; ctx.fillRect(-21, -3, 43, 6);
        ctx.fillStyle = '#bcecff'; ctx.fillRect(-10, -2, 29, 4); ctx.fillRect(19, -1, 3, 2);
        ctx.fillStyle = '#f0fbff'; ctx.fillRect(-9, -2, 28, 1);
        ctx.fillStyle = '#406080'; ctx.fillRect(-10, 1, 28, 1);
        ctx.fillStyle = '#69718b'; ctx.fillRect(-13, -5, 3, 10);
        ctx.fillStyle = '#9c96bd'; for (let x = -20; x < -13; x += 3) ctx.fillRect(x, -2, 1, 4);
        ctx.restore();
      }
    }
  }
  const C = G.Combat, previousUpdate = C.updateFields, previousDraw = C.drawAirFields, previousClear = C.clearFields;
  C.updateFields = function(dt) { const result = previousUpdate.call(this, dt); update(dt); return result; };
  C.drawAirFields = function(ctx) { previousDraw.call(this, ctx); draw(ctx); };
  C.clearFields = function(owner) { const result = previousClear.call(this, owner); clear(owner); return result; };
  G.NarutoKusanagi = { config, states, clear, activate, active: owner => states.get(owner)?.world === G.World };
})();
