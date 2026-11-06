/* Cumulative Mangekyo powers. The Sharingan controller owns simulation time. */
(() => {
  if (G.NarutoSharinganPowers) return;
  const config = Object.freeze({
    holeRange: 320, holeCooldown: 8, holeRadius: 70, holeDuration: 1,
    pullSpeed: 80, bossPullMultiplier: .1, flameRadius: 64, flameTick: .5,
    flameMaxHpPerSecond: .02, bossFlameMaxHpPerSecond: .005,
    susanooDamageTakenMultiplier: .7, swordCooldown: 2, swordRange: 180,
    swordRadius: 100, swordOffset: 55, swordDamage: 55, swordType: 'psychic', swordDuration: .22
  });
  const holes = [], fields = [], slashes = [];
  const states = new Map();
  const alive = e => e && !e.dead && e.hp > 0;
  const validOwner = owner => (G.SelfClones?.isControlled(owner) ?? owner === G.Game.player) && owner?.mon?.dex === 30002 && alive(owner);
  const valid = f => validOwner(f.owner) && f.world === G.World;
  const boss = e => !!(e.boss || e.legend || e.judge);
  const nearby = (x, y, radius) => [...new Set(G.EnemyMgr.queryCircle(x, y, radius))]
    .filter(e => alive(e) && Math.hypot(e.x - x, e.y - y) <= radius + (e.r || 0));
  function clear(owner) {
    for (const list of [holes, fields, slashes]) for (let i = list.length - 1; i >= 0; i--)
      if (!owner || list[i].owner === owner) list.splice(i, 1);
    if (owner) states.delete(owner); else states.clear();
  }
  function hit(owner, enemy, base, type, x, y) {
    if (!validOwner(owner) || !alive(enemy) || !(base > 0)) return;
    const mult = G.Types.mult(type, enemy.types), amount = base * mult * G.Weather.mult(type);
    if (!(amount > 0)) return;
    enemy.hurt(amount, type === 'fire' ? '#a265c9' : '#c593ff', enemy.x - x, enemy.y - y, 0, G.Types.label(mult), owner, 'naruto-sharingan');
    owner.onDealt(amount); owner.dmgDealt += amount;
  }
  function scorched(owner, enemy) {
    return fields.some(f => f.owner === owner && Math.hypot(enemy.x - f.x, enemy.y - f.y) <= f.radius + (enemy.r || 0));
  }
  function ignite(hole) {
    // Identical footprints may share one field; no age limit or field cap removes burned ground.
    if (!fields.some(f => f.owner === hole.owner && f.x === hole.x && f.y === hole.y))
      fields.push({ owner: hole.owner, world: hole.world, x: hole.x, y: hole.y, radius: config.flameRadius, age: 0 });
    G.FX.ring(hole.x, hole.y, 5, config.flameRadius, '#8d4db3', .3, 3);
  }
  function update(owner, stage, dt) {
    if (!validOwner(owner) || stage < 4) { clear(owner); return; }
    let state = states.get(owner);
    if (!state || state.world !== G.World) {
      clear(owner); state = { owner, world: G.World, stage, age: 0, holeCooldown: 0, swordCooldown: 0, burnClock: 0 };
      states.set(owner, state);
    }
    state.stage = stage;
    if (!(dt > 0) || !Number.isFinite(dt)) return;
    state.age += dt; state.holeCooldown -= dt; state.swordCooldown -= dt;
    for (const f of fields) if (f.owner === owner) f.age += dt;
    for (let i = slashes.length - 1; i >= 0; i--) {
      if (slashes[i].owner !== owner) continue;
      slashes[i].age += dt;
      if (slashes[i].age >= config.swordDuration || stage < 5) slashes.splice(i, 1);
    }
    for (let i = holes.length - 1; i >= 0; i--) {
      if (holes[i].owner !== owner) continue;
      const h = holes[i], step = Math.min(dt, Math.max(0, config.holeDuration - h.age));
      h.age += dt;
      for (const enemy of nearby(h.x, h.y, config.holeRadius)) {
        const distance = Math.hypot(h.x - enemy.x, h.y - enemy.y);
        if (distance < .001) continue;
        const movement = Math.min(distance, config.pullSpeed * step * (boss(enemy) ? config.bossPullMultiplier : 1));
        const x = enemy.x + (h.x - enemy.x) / distance * movement;
        const y = enemy.y + (h.y - enemy.y) / distance * movement;
        if (!G.World.isWall(x, y) && !G.World.projectileBlock(x, y, enemy.r || 1)) { enemy.x = x; enemy.y = y; }
      }
      if (h.age + 1e-9 >= config.holeDuration) { ignite(h); holes.splice(i, 1); }
    }
    // Each owner has one burn clock; overlapping patches from that owner do not multiply DPS.
    state.burnClock += dt;
    while (state.burnClock + 1e-9 >= config.flameTick) {
      state.burnClock -= config.flameTick;
      const burning = new Set();
      for (const f of fields.filter(f => f.owner === owner)) for (const enemy of nearby(f.x, f.y, f.radius)) burning.add(enemy);
      for (const enemy of burning) {
        const rate = boss(enemy) ? config.bossFlameMaxHpPerSecond : config.flameMaxHpPerSecond;
        hit(owner, enemy, enemy.maxHp * rate * config.flameTick * (G.SelfClones?.isActor(owner) ? G.SelfClones.ratio : 1), 'fire', enemy.x, enemy.y);
      }
    }
    if (state.holeCooldown <= 0) {
      const candidates = nearby(owner.x, owner.y, config.holeRange)
        .filter(enemy => !scorched(owner, enemy) && !holes.some(h => h.owner === owner && Math.hypot(h.x - enemy.x, h.y - enemy.y) <= config.flameRadius));
      candidates.sort((a, b) => Math.hypot(a.x - owner.x, a.y - owner.y) - Math.hypot(b.x - owner.x, b.y - owner.y));
      const target = candidates[0];
      if (target) {
        holes.push({ owner, world: G.World, x: target.x, y: target.y, age: 0, radius: config.holeRadius });
        state.holeCooldown = config.holeCooldown;
      }
    }
    if (stage >= 5 && state.swordCooldown <= 0) {
      const candidates = nearby(owner.x, owner.y, config.swordRange);
      candidates.sort((a, b) => Math.hypot(a.x - owner.x, a.y - owner.y) - Math.hypot(b.x - owner.x, b.y - owner.y));
      const target = candidates[0];
      if (target) {
        const angle = Math.atan2(target.y - owner.y, target.x - owner.x);
        const x = owner.x + Math.cos(angle) * config.swordOffset, y = owner.y + Math.sin(angle) * config.swordOffset;
        slashes.push({ owner, world: G.World, x, y, angle, age: 0, radius: config.swordRadius });
        for (const enemy of nearby(x, y, config.swordRadius)) hit(owner, enemy, config.swordDamage * owner.atk, config.swordType, x, y);
        state.swordCooldown = config.swordCooldown;
      }
    }
  }
  function ground(ctx) {
    ctx.save();
    for (const h of holes) if (valid(h)) {
      const p = Math.min(1, h.age / config.holeDuration);
      ctx.fillStyle = '#171020'; ctx.globalAlpha = .48;
      ctx.beginPath(); ctx.arc(h.x, h.y, h.radius, 0, Math.PI * 2); ctx.fill();
      ctx.globalAlpha = .85; ctx.strokeStyle = '#a66ade'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(h.x, h.y, h.radius, 0, Math.PI * 2); ctx.stroke();
      ctx.strokeStyle = '#e26291'; ctx.lineWidth = 2;
      for (let i = 0; i < 4; i++) {
        const angle = h.age * 5 + i * Math.PI / 2, r = h.radius * (1 - p * .65);
        ctx.beginPath(); ctx.arc(h.x, h.y, r, angle, angle + 1.1); ctx.stroke();
      }
    }
    for (const f of fields) if (valid(f) && G.Camera.sees(f.x,f.y,f.radius+20)) {
      ctx.globalAlpha = .4; ctx.fillStyle = '#170c20';
      ctx.beginPath(); ctx.arc(f.x, f.y, f.radius, 0, Math.PI * 2); ctx.fill();
      ctx.globalAlpha = .75; ctx.strokeStyle = '#7d4897'; ctx.lineWidth = 2; ctx.stroke();
      ctx.globalAlpha = 1;
      // Small hard-edged tongues preserve the existing sprite game's pixel vocabulary.
      for (let i = 0; i < 26; i++) {
        const angle = i * 2.39996, r = Math.sqrt((i + .5) / 26) * f.radius;
        const x = Math.round((f.x + Math.cos(angle) * r) / 2) * 2;
        const y = Math.round((f.y + Math.sin(angle) * r) / 2) * 2;
        const flicker = Math.floor(f.age * 10 + i) % 3;
        ctx.fillStyle = '#090710'; ctx.fillRect(x - 4, y - 8 - flicker * 2, 8, 12 + flicker * 2);
        ctx.fillRect(x - 2, y - 14 - flicker * 2, 4, 8);
        ctx.fillStyle = '#703e8b'; ctx.fillRect(x, y - 9, 2, 9); ctx.fillRect(x - 2, y - 3, 2, 4);
      }
    }
    ctx.restore();
  }
  function air(ctx) {
    ctx.save();
    for (const state of states.values()) if (state.stage >= 5 && valid(state)) {
      const x = Math.round(state.owner.x), y = Math.round(state.owner.y - 21);
      ctx.globalAlpha = .48 + Math.sin(state.age * 5) * .05;
      ctx.strokeStyle = '#a577eb'; ctx.lineWidth = 5;
      // Compact articulated ribs and shoulders; player sprite remains readable.
      for (let i = 0; i < 4; i++) {
        const width = 30 - i * 3, top = y - 21 + i * 11;
        ctx.beginPath(); ctx.moveTo(x - width, top - 5); ctx.lineTo(x - width, top + 3);
        ctx.lineTo(x - 8, top + 9); ctx.moveTo(x + width, top - 5);
        ctx.lineTo(x + width, top + 3); ctx.lineTo(x + 8, top + 9); ctx.stroke();
      }
      ctx.strokeStyle = '#d1abff'; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(x - 35, y - 24); ctx.lineTo(x - 45, y - 12); ctx.lineTo(x - 41, y + 17);
      ctx.moveTo(x + 35, y - 24); ctx.lineTo(x + 45, y - 12); ctx.lineTo(x + 41, y + 17); ctx.stroke();
    }
    for (const s of slashes) if (valid(s)) {
      const p = s.age / config.swordDuration;
      ctx.globalAlpha = (1 - p) * .25; ctx.fillStyle = '#a879eb';
      ctx.beginPath(); ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2); ctx.fill();
      ctx.globalAlpha = (1 - p) * .85; ctx.strokeStyle = '#d7b4ff'; ctx.lineWidth = 6;
      ctx.beginPath(); ctx.arc(s.x, s.y, s.radius * .88, s.angle - 1.8 + p, s.angle + 1.8 + p); ctx.stroke();
      ctx.strokeStyle = '#9660dd'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2); ctx.stroke();
    }
    ctx.restore();
  }
  const groundFields = G.Combat.drawGroundFields, airFields = G.Combat.drawAirFields;
  G.Combat.drawGroundFields = function(ctx) { groundFields.call(this, ctx); ground(ctx); };
  G.Combat.drawAirFields = function(ctx) { airFields.call(this, ctx); air(ctx); };
  G.NarutoSharinganPowers = {
    config, update, clear,
    damageTakenMultiplier(owner) { const state = states.get(owner); return state?.stage >= 5 && valid(state) ? config.susanooDamageTakenMultiplier : 1; },
    get fields() { return fields; }, get holes() { return holes; }, get slashes() { return slashes; }, stateFor: owner => states.get(owner), get state() { return states.get(G.Game.player); }
  };
})();
