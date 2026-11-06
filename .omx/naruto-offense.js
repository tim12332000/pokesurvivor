/* Targeted Naruto techniques: simulation-time fields, owned by the current run. */
(() => {
  const controlled = owner => G.SelfClones?.isControlled(owner) ?? (owner === G.Game.player);
  if (G.NarutoOffense) return;
  const C = G.Combat, effects = [], modes = new Set(['lotus', 'sand-coffin', 'single-illusion', 'black-flames']);
  G.VFX.PAL['naruto-black-flame']=['#05050d','#111024','#29163f','#663772','#b66bc3'];
  const defaults = {
    lotus: { range: 145, radius: 60, dmg: 70, windup: .25, liftDuration: .35 },
    'sand-coffin': { range: 280, radius: 0, dmg: 80, fieldDuration: 1.1 },
    'single-illusion': { range: 260, dmg: 30, fieldDuration: 1.5 },
    'black-flames': { range: 280, radius: 80, dmg: 12, fieldDuration: 3, fieldTick: .5 }
  };
  const supports = mode => modes.has(mode);
  const modeOf = m => m.digiMode || m.narutoMode || m.mode;
  const alive = e => e && !e.dead && e.hp > 0;
  const elite = e => !!(e.boss || e.legend || e.judge || e.elite);
  const valid = f => controlled(f.owner) && alive(f.owner) && f.world === G.World;
  const nearby = (x, y, radius) => [...new Set(G.EnemyMgr.queryCircle(x, y, radius))]
    .filter(e => alive(e) && Math.hypot(e.x - x, e.y - y) <= radius + (e.r || 0));
  function clearPath(ax, ay, bx, by) {
    const steps = Math.max(1, Math.ceil(Math.hypot(bx - ax, by - ay) / 4));
    for (let i = 1; i <= steps; i++) {
      const x = ax + (bx - ax) * i / steps, y = ay + (by - ay) * i / steps;
      if (G.World.projectileBlock(x, y, 1) || G.World.isWall(x, y)) return false;
    }
    return true;
  }
  function targetFor(pl, m, mode) {
    const range = m.range ?? defaults[mode].range;
    const eligible = e => alive(e) && Math.hypot(e.x - pl.x, e.y - pl.y) <= range && clearPath(pl.x, pl.y, e.x, e.y);
    const candidates = nearby(pl.x, pl.y, range).filter(eligible);
    candidates.sort((a, b) => Math.hypot(a.x - pl.x, a.y - pl.y) - Math.hypot(b.x - pl.x, b.y - pl.y));
    if (mode === 'single-illusion') {
      const preferred = candidates.find(elite);
      if (preferred) return preferred;
    }
    return eligible(pl.target) ? pl.target : candidates[0];
  }
  function canCast(pl, m) {
    const mode = modeOf(m);
    return supports(mode) && valid({ owner: pl, world: G.World }) && !!targetFor(pl, m, mode);
  }
  function removeLift(f) {
    if (f.lift && f.target) f.target.jumpLift = Math.max(0, (f.target.jumpLift || 0) - f.lift);
    f.lift = 0;
  }
  function clear(owner) {
    for (let i = effects.length - 1; i >= 0; i--) if (!owner || effects[i].owner === owner) {
      removeLift(effects[i]); effects.splice(i, 1);
    }
  }
  function hit(f, e, amount, color) {
    if (!valid(f) || !alive(e)) return;
    const type = f.m.type || 'normal', mult = G.Types.mult(type, e.types), crit = f.owner.critChance > 0 && Math.random() < f.owner.critChance;
    const damage = amount * f.atk * mult * G.Weather.mult(type) * (crit ? 1.5 : 1);
    e.hurt(damage, color, e.x - f.x, e.y - f.y, 0, crit ? 'crit' : G.Types.label(mult), f.owner, f.m.id);
    f.owner.onDealt(damage); f.owner.dmgDealt += damage;
  }
  function cast(pl, move) {
    const mode = modeOf(move);
    if (!supports(mode) || !valid({ owner: pl, world: G.World })) return false;
    const m = { ...defaults[mode], ...move }, target = targetFor(pl, m, mode);
    if (!target) return false;
    const f = { kind: mode, owner: pl, world: G.World, m, target, x: target.x, y: target.y,
      originX: pl.x, originY: pl.y, atk: pl.atk, age: 0, hit: false, lift: 0, ticks: 0,
      duration: mode === 'lotus' ? m.windup + m.liftDuration + .3 : m.fieldDuration };
    if (mode === 'black-flames') {
      const patches = effects.filter(e => e.kind === mode && e.owner === pl);
      while (patches.length >= (G.Quantity?.count(pl,2)||2)) {
        const previous = patches.shift(); effects.splice(effects.indexOf(previous), 1);
      }
    }
    effects.push(f);
    return true;
  }
  function update(dt) {
    if (!(dt > 0) || !Number.isFinite(dt)) return;
    for (let i = effects.length - 1; i >= 0; i--) {
      const f = effects[i]; removeLift(f);
      if (!valid(f) || (f.kind !== 'black-flames' && (!alive(f.target) || !clearPath(f.originX, f.originY, f.target.x, f.target.y)))) { effects.splice(i, 1); continue; }
      f.age += dt;
      const e = f.target, m = f.m;
      if (f.kind === 'black-flames') {
        const due = Math.min(Math.floor(Math.min(f.age, f.duration) / m.fieldTick + 1e-8), Math.floor(f.duration / m.fieldTick + 1e-8));
        let budget = 6;
        while (f.ticks < due && budget-- > 0) {
          f.ticks++;
          if (!G.World.isWall(f.x, f.y)) for (const enemy of nearby(f.x, f.y, m.radius)) if (clearPath(f.x, f.y, enemy.x, enemy.y)) hit(f, enemy, m.dmg, '#9a5ad1');
        }
      } else if (f.kind === 'lotus') {
        f.x = e.x; f.y = e.y;
        const launchAge = f.age - m.windup;
        if (launchAge >= 0 && launchAge < m.liftDuration) {
          e.applySlow(elite(e) ? .25 : .95, .2);
          if (!elite(e)) { f.lift = Math.sin(launchAge / m.liftDuration * Math.PI) * 36; e.jumpLift = (e.jumpLift || 0) + f.lift; }
        }
        if (!f.hit && launchAge >= m.liftDuration) {
          f.hit = true;
          if (clearPath(f.originX, f.originY, e.x, e.y)) {
            hit(f, e, m.dmg * .7, '#ffd98d');
            for (const other of nearby(f.x, f.y, m.radius)) if (other !== e && clearPath(f.x, f.y, other.x, other.y)) hit(f, other, m.dmg * .3, '#ffd98d');
            G.FX.ring(f.x, f.y, 5, m.radius, '#f1d7a7', .3, 3);
            G.FX.burst(f.x, f.y, '#d9bf88', 16, 85);
          }
        }
      } else if (f.kind === 'sand-coffin') {
        f.x = e.x; f.y = e.y;
        if (f.age < f.duration) e.applySlow(elite(e) ? (m.bossSlow ?? .3) : (m.slow || .95), .2);
        if (!f.hit && f.age >= f.duration && clearPath(f.originX, f.originY, e.x, e.y)) {
          f.hit = true; hit(f, e, m.dmg, '#d5ac67');
          G.FX.burst(f.x, f.y - Math.max(8, e.r || 0), '#d5ac67', 22, 100);
        }
      } else {
        f.x = e.x; f.y = e.y;
        if (f.age < f.duration) e.applySlow(elite(e) ? (m.bossSlow ?? .25) : (m.slow || .9), .2);
        if (!f.hit && f.age >= .25 && clearPath(f.originX, f.originY, e.x, e.y)) { f.hit = true; hit(f, e, m.dmg, '#dd5360'); }
      }
      if (f.age >= f.duration) { removeLift(f); effects.splice(i, 1); }
    }
  }
  function ground(ctx) {
    ctx.save();
    for (const f of effects) if (valid(f)) {
      if (f.kind === 'black-flames') {
        ctx.fillStyle = '#211225'; ctx.globalAlpha = .35;
        ctx.beginPath(); ctx.arc(f.x, f.y, f.m.radius, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#9355b0'; ctx.lineWidth = 2; ctx.stroke();
        ctx.globalAlpha = 1;
        for (let i = 0; i < 20; i++) {
          const angle = i * 2.39996, r = Math.sqrt((i + .5) / 20) * f.m.radius;
          const x = Math.round(f.x + Math.cos(angle) * r), y = Math.round(f.y + Math.sin(angle) * r);
          G.VFX.draw(ctx,'fire','naruto-black-flame',x,y-11,
            {scale:.75+(i%3)*.12,frame:Math.floor(f.age*10+i)%3,angle:-Math.PI/2});
        }
      } else if (f.kind === 'lotus') {
        ctx.strokeStyle = '#f4dba0'; ctx.globalAlpha = .7;
        ctx.beginPath(); ctx.arc(f.x, f.y, f.m.radius, 0, Math.PI * 2); ctx.stroke(); ctx.globalAlpha = 1;
      }
    }
    ctx.restore();
  }
  function air(ctx) {
    ctx.save();
    for (const f of effects) if (valid(f) && alive(f.target)) {
      if (f.kind === 'sand-coffin') {
        const size = Math.max(14, (f.target.r || 10) + 5), squeeze = Math.min(1, f.age / f.duration);
        ctx.fillStyle = '#a47c43'; ctx.globalAlpha = .75;
        for (let i = 0; i < 7; i++) {
          const offset = Math.sin(i * 2 + f.age * 8) * 2;
          const width = size * (1.6 - squeeze * .25);
          ctx.fillRect(Math.round(f.x - width / 2 + offset), Math.round(f.y - size * 2 + i * size * 2 / 7), width, size * 2 / 7 - 1);
        }
        ctx.globalAlpha = 1; ctx.fillStyle = '#edd299';
        for (let i = 0; i < 8; i++) ctx.fillRect(f.x + Math.cos(i * 2.4 + f.age) * size, f.y - i % 3 * 8, 3, 3);
      } else if (f.kind === 'single-illusion') {
        const y = f.y - 34, pulse = .8 + Math.sin(f.age * 9) * .2;
        ctx.globalAlpha = pulse; ctx.fillStyle = '#25101d'; ctx.fillRect(f.x - 15, y - 5, 30, 11);
        ctx.fillStyle = '#d94b62'; ctx.beginPath(); ctx.ellipse(f.x, y, 12, 4, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#160c16'; ctx.fillRect(f.x - 2, y - 4, 4, 8); ctx.globalAlpha = 1;
      } else if (f.kind === 'lotus' && f.lift > 0) {
        ctx.strokeStyle = '#f9ecd1'; ctx.lineWidth = 2;
        for (let i = 0; i < 3; i++) { const y = f.y - f.lift - i * 7; ctx.beginPath(); ctx.moveTo(f.x - 13, y); ctx.lineTo(f.x + 13, y - 7); ctx.stroke(); }
      }
    }
    ctx.restore();
  }
  const updateFields = C.updateFields, groundFields = C.drawGroundFields, airFields = C.drawAirFields, clearFields = C.clearFields;
  C.updateFields = function(dt) { const result = updateFields.call(this, dt); update(dt); return result; };
  C.drawGroundFields = function(ctx) { groundFields.call(this, ctx); ground(ctx); };
  C.drawAirFields = function(ctx) { airFields.call(this, ctx); air(ctx); };
  C.clearFields = function(owner) { clearFields.call(this, owner); clear(owner); };
  if (G.DigimonSkills?.clear) { const previous = G.DigimonSkills.clear; G.DigimonSkills.clear = owner => { previous(owner); clear(owner); }; }
  G.NarutoOffense = { supports, canCast, cast, clear, get effects() { return effects; } };
})();
