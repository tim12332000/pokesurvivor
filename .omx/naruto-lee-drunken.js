/* Drunken Fist is a learned dodge with one nearby, owned counterpunch. */
(() => {
  if (G.NarutoDrunkenFist) return;
  const id = 'naruto-lee-drunken', states = new Map();
  const config = Object.freeze({ dodgeInvuln: .25, counterTime: .1, duration: .3 });
  const alive = actor => !!actor && !actor.dead && actor.hp > 0;
  const controlled = owner => G.SelfClones?.isControlled(owner) ?? owner === G.Game.player;
  const learned = owner => owner?.mon?.dex === 30006 && owner.moves?.find(move => move.id === id);
  const heavy = owner => G.NarutoGates?.performing(owner) || G.NarutoLee?.activeFor(owner) || G.DigimonSkills?.whirlwindFor(owner);
  function stage(owner = G.Game.player) {
    const move = learned(owner);
    return move && alive(owner) && controlled(owner) ? Math.max(1, Math.min(5, move.lvl | 0)) : 0;
  }
  function clear(owner) { if (owner) states.delete(owner); else states.clear(); }
  function activeFor(owner = G.Game.player) {
    const state = states.get(owner);
    return state && state.world === G.World && stage(owner) ? state : null;
  }
  function clearPath(owner, enemy) {
    const distance = Math.hypot(enemy.x - owner.x, enemy.y - owner.y);
    const steps = Math.max(1, Math.ceil(distance / 4));
    for (let i = 1; i <= steps; i++) {
      const x = owner.x + (enemy.x - owner.x) * i / steps, y = owner.y + (enemy.y - owner.y) * i / steps;
      if (G.World.isWall(x, y) || G.World.projectileBlock(x, y, 1)) return false;
    }
    return true;
  }
  const reachable = (owner, enemy, radius) => alive(enemy) && Math.hypot(enemy.x - owner.x, enemy.y - owner.y) <= radius && clearPath(owner, enemy);
  function counterTarget(owner, move, context) {
    const candidates = [...new Set(G.EnemyMgr.queryCircle(owner.x, owner.y, move.radius))]
      .filter(enemy => reachable(owner, enemy, move.radius));
    const contact = !Number.isFinite(context.vx) && !Number.isFinite(context.vy)
      ? candidates.find(enemy => Math.hypot(enemy.x - context.fromX, enemy.y - context.fromY) < .01) : null;
    return contact || candidates.sort((a, b) => Math.hypot(a.x - owner.x, a.y - owner.y) - Math.hypot(b.x - owner.x, b.y - owner.y))[0] || null;
  }
  const hurt = G.Player.prototype.hurt;
  G.Player.prototype.hurt = function(amount, type, pure, context) {
    const move = learned(this);
    if (!stage(this) || G.Game.state !== 'playing' || !(amount > 0) || !Number.isFinite(amount) || pure || this.invuln > 0 || this.frozen ||
        !Number.isFinite(context?.fromX) || !Number.isFinite(context?.fromY) || G.NarutoLee?.isInvulnerable(this) || G.NarutoGates?.performing(this) ||
        !(Math.random() < move.dodgeChance)) return hurt.apply(this, arguments);
    const target = heavy(this) ? null : counterTarget(this, move, context);
    this.invuln = config.dodgeInvuln;
    G.NarutoPursuit?.clear(this);
    const aim = Math.atan2((target?.y ?? context.fromY) - this.y, (target?.x ?? context.fromX) - this.x);
    states.set(this, { owner: this, world: G.World, age: 0, move: { ...move }, target, aim, resolved: false });
    G.FX.dmgText(this.x, this.y - this.bodyH - 6, '閃避', '#b9efab');
    G.FX.burst(this.x, this.y - 12, '#d5f3b0', 7, 65);
  };
  function counter(state) {
    state.resolved = true;
    const { owner, target, move } = state;
    if (!target || heavy(owner) || !reachable(owner, target, move.radius)) { state.target = null; return; }
    state.aim = Math.atan2(target.y - owner.y, target.x - owner.x);
    const mult = G.Types.mult(move.type, target.types), critical = Math.random() < (owner.critChance || 0);
    const damage = move.dmg * owner.atk * mult * G.Weather.mult(move.type) * (critical ? 1.5 : 1);
    target.hurt(damage, '#d5f3b0', target.x - owner.x, target.y - owner.y, target.boss ? 5 : move.knock, critical ? 'crit' : G.Types.label(mult), owner, id);
    owner.onDealt(damage); owner.dmgDealt += damage;
    G.FX.burst(target.x, target.y - 12, '#fff0c4', 8, 75);
  }
  function update(dt) {
    for (const [owner, state] of states) {
      if (!activeFor(owner)) { states.delete(owner); continue; }
      if (G.Game.state !== 'playing' || !(dt > 0) || !Number.isFinite(dt)) continue;
      state.age += dt;
      if (!state.resolved && state.age + 1e-9 >= config.counterTime) counter(state);
      if (state.age >= config.duration) states.delete(owner);
    }
  }
  function presentationFor(owner) {
    const state = activeFor(owner);
    if (!state || heavy(owner)) return null;
    const dodging = state.age < config.counterTime;
    const frame = dodging || !state.target ? 0 : Math.min(3, 1 + Math.floor((state.age - config.counterTime) / .07));
    return { state: 'skill', id, phase: dodging ? 'dodge' : state.target ? 'counter' : 'recovery', key: 'lee-attack', frame,
      aim: state.aim, mirror: Math.cos(state.aim) < 0,
      offsetX: dodging ? Math.sin(state.age / config.counterTime * Math.PI) * Math.cos(state.aim + Math.PI / 2) * 5 : 0,
      offsetY: dodging ? Math.sin(state.age / config.counterTime * Math.PI) * Math.sin(state.aim + Math.PI / 2) * 3 : 0 };
  }
  const C = G.Combat, tick = C.tick, updateFields = C.updateFields, clearFields = C.clearFields;
  C.tick = function(dt, owner, ...args) {
    if (activeFor(owner)) return;
    return tick.call(this, dt, owner, ...args);
  };
  C.updateFields = function(dt) { const result = updateFields.call(this, dt); update(dt); return result; };
  C.clearFields = function(owner) { const result = clearFields.call(this, owner); clear(owner); return result; };
  G.NarutoDrunkenFist = { config, stage, activeFor, update, clear, presentationFor };
})();
