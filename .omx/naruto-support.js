/* Naruto support skills use simulation time and never alter permanent stats or map tiles. */
(() => {
  const controlled = owner => G.SelfClones?.isControlled(owner) ?? (owner === G.Game.player);
  if (G.NarutoSupport) return;
  const C = G.Combat, effects = [], locks = [], TAU = Math.PI * 2;
  const modes = new Set(['medical-heal', 'regeneration', 'sharingan', 'byakugan', 'sand-shield', 'earth-wall', 'nine-tails-cloak']);
  const defaults = {
    'medical-heal': { healFraction: .22, fieldDuration: .5 },
    regeneration: { fieldDuration: 5, healFraction: .045 },
    sharingan: { fieldDuration: 3, nextDamageMul: 1.25 },
    byakugan: { fieldDuration: 5, radius: 280, damageMul: 1.2 },
    'sand-shield': { fieldDuration: 8, shieldAmount: 45, cd: 12 },
    'earth-wall': { fieldDuration: 3, width: 100, range: 72 },
    'nine-tails-cloak': { fieldDuration:8, atkMul:1.5, speedMul:1.25, damageTakenMul:.75, radius:76, pulseDamage:12, pulseInterval:.65, knock:18 }
  };
  const valid = f => controlled(f.owner) && f.world === G.World && !f.owner.dead && f.owner.hp > 0;
  const active = (owner, mode) => effects.find(f => f.owner === owner && f.mode === mode && valid(f));
  const nearby = (x, y, radius) => [...new Set(G.EnemyMgr.queryCircle(x, y, radius))].filter(e => !e.dead);
  const finite = (v, fallback) => Number.isFinite(v) ? v : fallback;
  function clearPath(ax, ay, bx, by) {
    const count = Math.min(160, Math.max(1, Math.ceil(Math.hypot(bx - ax, by - ay) / 5)));
    for (let i = 1; i <= count; i++) {
      const x = ax + (bx - ax) * i / count, y = ay + (by - ay) * i / count;
      if (G.World.isWall?.(x, y) || G.World.projectileBlock(x, y, 1)) return false;
    }
    return true;
  }
  function danger(owner) {
    return nearby(owner.x, owner.y, 300).length > 0 || G.Projectiles.all().some(p => p.friendly === false && Math.hypot(p.x - owner.x, p.y - owner.y) < 300);
  }
  function wallPosition(owner, m) {
    const angle = finite(owner.aim, Math.PI / 2), nx = Math.cos(angle), ny = Math.sin(angle), ux = -ny, uy = nx;
    const width = Math.min(150, Math.max(40, finite(m.width, 100))), range = Math.min(110, Math.max(48, finite(m.range, 72)));
    const x = owner.x + nx * range, y = owner.y + ny * range;
    // The whole wall must fit legal, empty ground, with an escape gap beside its ends.
    for (let i = -4; i <= 4; i++) if (!G.World.isFree(x + ux * width * i / 8, y + uy * width * i / 8, 10, true)) return null;
    if (nearby(x, y, width / 2 + 24).some(e => Math.abs((e.x - x) * nx + (e.y - y) * ny) < 12 + (e.r || 10) && Math.abs((e.x - x) * ux + (e.y - y) * uy) < width / 2 + (e.r || 10))) return null;
    return { x, y, ux, uy, nx, ny, width, thickness: 14 };
  }
  function canCast(owner, move) {
    const mode = move?.digiMode;
    if (!modes.has(mode) || !controlled(owner) || owner.dead || owner.hp <= 0 || !owner.mon?.naruto) return false;
    if (mode === 'nine-tails-cloak' && owner.mon.dex !== 30001) return false;
    if (active(owner, mode) || locks.some(f => f.owner === owner && f.mode === mode && valid(f))) return false;
    if (mode === 'medical-heal') return owner.hp < owner.maxHp;
    if (mode === 'regeneration') return owner.hp < owner.maxHp * .8;
    if (!danger(owner)) return false;
    return mode !== 'earth-wall' || !!wallPosition(owner, { ...defaults[mode], ...move });
  }
  function cast(owner, move) {
    if (!canCast(owner, move)) return false;
    for (const list of [effects, locks]) for (let i = list.length - 1; i >= 0; i--) if (!valid(list[i])) list.splice(i, 1);
    if (effects.length >= 16) return false;
    const mode = move.digiMode, m = { ...defaults[mode], ...move };
    const f = { owner, world: G.World, mode, m, age: 0, ttl: Math.max(.1, Math.min(12, finite(m.fieldDuration, 3))), tick: 0 };
    if (mode === 'medical-heal') owner.heal(owner.maxHp * Math.min(.35, Math.max(0, finite(m.healFraction, .22))));
    if (mode === 'sharingan') { f.dodges = 1; f.attackReady = true; }
    if (mode === 'sand-shield') f.shield = f.capacity = Math.max(1, finite(m.shieldAmount, 45));
    if (mode === 'earth-wall') { const p = wallPosition(owner, m); if (!p) return false; Object.assign(f, p); }
    effects.push(f);
    owner.anim?.play(mode === 'nine-tails-cloak' ? 'Idle' : 'Charge');
    return true;
  }
  function clear(owner) {
    for (const list of [effects, locks]) for (let i = list.length - 1; i >= 0; i--) if (!owner || list[i].owner === owner) list.splice(i, 1);
  }
  function takeAttackBonus(owner) {
    const f = active(owner, 'sharingan');
    if (!f?.attackReady) return 1;
    f.attackReady = false;
    return Math.max(1, Math.min(1.5, finite(f.m.nextDamageMul, 1.25)));
  }
  function precisionMultiplier(owner, enemy) {
    const f = active(owner, 'byakugan');
    return f && enemy && !enemy.dead && Math.hypot(enemy.x - owner.x, enemy.y - owner.y) <= Math.min(360, finite(f.m.radius, 280)) && clearPath(owner.x, owner.y, enemy.x, enemy.y) ? Math.max(1, Math.min(1.3, finite(f.m.damageMul, 1.2))) : 1;
  }
  // Getter composition leaves level-up, equipment, perks, and concurrent buffs intact.
  for (const key of ['atk', 'spd']) {
    const descriptor = Object.getOwnPropertyDescriptor(G.Player.prototype, key);
    if (!descriptor?.get) continue;
    Object.defineProperty(G.Player.prototype, key, { ...descriptor, get() {
      let value = descriptor.get.call(this);
      const cloak = active(this, 'nine-tails-cloak');
      return cloak ? value * (key === 'atk' ? Math.min(1.8,finite(cloak.m.atkMul,1.5)) : Math.min(1.5,finite(cloak.m.speedMul,1.25))) : value;
    } });
  }
  function breakShield(f) {
    const i = effects.indexOf(f); if (i >= 0) effects.splice(i, 1);
    locks.push({ owner: f.owner, world: f.world, mode: 'sand-shield', age: 0, ttl: Math.max(1, finite(f.m.cd, 12)) });
    G.FX.burst(f.owner.x, f.owner.y - 16, '#d6ae67', 10, 65);
  }
  const hurt = G.Player.prototype.hurt;
  G.Player.prototype.hurt = function(amount, type = null, pure = false, context = null) {
    if (!controlled(this) || this.invuln > 0 || this.dead || this.frozen || !(amount > 0) || pure) return hurt.call(this, amount, type, pure, context);
    const cloak = active(this, 'nine-tails-cloak');
    if (cloak) amount *= Math.max(.5,Math.min(1,finite(cloak.m.damageTakenMul,.75)));
    const eye = active(this, 'sharingan');
    if (eye?.dodges > 0) {
      eye.dodges--; this.invuln = Math.max(this.invuln || 0, .16);
      G.FX.burst(this.x, this.y - 20, '#ff5965', 6, 35);
      return;
    }
    const shield = active(this, 'sand-shield');
    if (!shield) return hurt.call(this, amount, type, pure, context);
    const typed = type ? amount * G.Types.mult(type, this.mon.types) * G.Weather.mult(type) : amount;
    const close = this.activeGroup().some(m => m.kind === 'melee') ? .75 : 1;
    const damage = Math.max(1, typed * (1 - this.reduction) * close);
    const absorb = Math.min(shield.shield, damage); shield.shield -= absorb;
    G.FX.burst(this.x, this.y - 14, '#d6ae67', 4, 35);
    if (shield.shield <= .0001) breakShield(shield);
    if (absorb >= damage) { this.invuln = Math.max(this.invuln || 0, .45); return; }
    // Preserve the original type, damage reduction, invulnerability and death handling.
    return hurt.call(this, amount * (damage - absorb) / damage, type, pure, context);
  };
  function wallIntersects(f, ax, ay, bx, by, radius = 0) {
    // Slab intersection in the wall's local coordinates catches fast projectiles.
    const px = (ax - f.x) * f.ux + (ay - f.y) * f.uy, py = (ax - f.x) * f.nx + (ay - f.y) * f.ny;
    const dx = (bx - ax) * f.ux + (by - ay) * f.uy, dy = (bx - ax) * f.nx + (by - ay) * f.ny;
    let lo = 0, hi = 1;
    for (const [p, d, extent] of [[px, dx, f.width / 2 + radius], [py, dy, f.thickness / 2 + radius]]) {
      if (Math.abs(d) < .00001) { if (Math.abs(p) > extent) return false; continue; }
      const a = (-extent - p) / d, b = (extent - p) / d;
      lo = Math.max(lo, Math.min(a, b)); hi = Math.min(hi, Math.max(a, b));
      if (lo > hi) return false;
    }
    return hi >= 0 && lo <= 1;
  }
  const resolve = C.resolve;
  C.resolve = function(dt, owner, now) {
    const walls = effects.filter(f => f.mode === 'earth-wall' && valid(f));
    for (const p of [...G.Projectiles.all()]) {
      if (p.friendly !== false) continue;
      const wall = walls.find(f => wallIntersects(f, p.px ?? p.x, p.py ?? p.y, p.x, p.y, p.r || 0));
      if (wall) { G.Projectiles.remove(p); G.FX.burst(p.x, p.y - (G.LIFT || 16), '#b59677', 3, 30); }
    }
    return resolve.call(this, dt, owner, now);
  };
  function repel(f, dt) {
    for (const e of nearby(f.x, f.y, f.width / 2 + 45)) {
      if (e.boss || e.legend || e.judge || e.remote) continue;
      const along = (e.x - f.x) * f.ux + (e.y - f.y) * f.uy, across = (e.x - f.x) * f.nx + (e.y - f.y) * f.ny;
      const reach = (e.r || 10) + f.thickness / 2;
      if (Math.abs(along) > f.width / 2 + (e.r || 10) || Math.abs(across) >= reach) continue;
      const sign = Math.sign(across) || 1, step = Math.min(reach - Math.abs(across) + 1, 200 * dt);
      const x = e.x + f.nx * sign * step, y = e.y + f.ny * sign * step;
      if (G.World.isFree(x, y, e.r || 10, true)) { e.x = x; e.y = y; }
    }
  }
  function update(dt) {
    if (!(dt > 0) || !Number.isFinite(dt)) return;
    for (let i = locks.length - 1; i >= 0; i--) { const f = locks[i]; f.age += dt; if (!valid(f) || f.age >= f.ttl) locks.splice(i, 1); }
    for (let i = effects.length - 1; i >= 0; i--) {
      const f = effects[i];
      if (!valid(f)) { effects.splice(i, 1); continue; }
      const delta = Math.min(dt, Math.max(0, f.ttl - f.age)); f.age += dt;
      if (f.mode === 'regeneration') { f.tick += delta; while (f.tick >= 1 - 1e-9) { f.tick -= 1; f.owner.heal(f.owner.maxHp * Math.min(.08, Math.max(0, finite(f.m.healFraction, .045)))); } }
      if (f.mode === 'earth-wall') repel(f, Math.min(dt, .1));
      if (f.mode === 'nine-tails-cloak') {
        f.tick+=delta; f.pulseFlash=Math.max(0,(f.pulseFlash||0)-dt);
        const interval=Math.max(.2,finite(f.m.pulseInterval,.65)),radius=Math.max(1,finite(f.m.radius,76));
        while(f.tick+1e-9>=interval) {
          f.tick-=interval;f.pulseFlash=.18;
          for(const enemy of nearby(f.owner.x,f.owner.y,radius)) {
            const dx=enemy.x-f.owner.x,dy=enemy.y-f.owner.y;
            if(Math.hypot(dx,dy)>radius+(enemy.r||0)||!clearPath(f.owner.x,f.owner.y,enemy.x,enemy.y))continue;
            const k=G.Types.mult(f.m.type||'fighting',enemy.types),crit=f.owner.critChance>0&&Math.random()<f.owner.critChance;
            const damage=finite(f.m.pulseDamage,12)*f.owner.atk*k*G.Weather.mult(f.m.type||'fighting')*(crit?1.5:1);
            enemy.hurt(damage,'#ff654f',dx,dy,enemy.boss?5:finite(f.m.knock,18),crit?'crit':G.Types.label(k),f.owner,f.m.id);
            f.owner.onDealt(damage);f.owner.dmgDealt+=damage;
          }
        }
      }
      if (f.age >= f.ttl) {
        effects.splice(i, 1);
      }
    }
  }
  function draw(ctx, ground) {
    ctx.save();
    for (const f of effects) {
      if (!valid(f)) continue;
      const x = f.owner.x, y = f.owner.y, phase = f.age * 5;
      ctx.globalAlpha = Math.min(1, (f.ttl - f.age) * 3);
      if (f.mode === 'nine-tails-cloak') { G.NarutoCloakVFX?.draw(ctx,f,ground); continue; }
      if (f.mode === 'earth-wall') {
        const corners = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([u, n]) => [f.x + f.ux * u * f.width / 2 + f.nx * n * f.thickness / 2, f.y + f.uy * u * f.width / 2 + f.ny * n * f.thickness / 2]);
        const polygon = points => { ctx.beginPath(); points.forEach(([px, py], i) => i ? ctx.lineTo(Math.round(px), Math.round(py)) : ctx.moveTo(Math.round(px), Math.round(py))); ctx.closePath(); ctx.fill(); };
        if (!ground) {
          const edges = corners.map((a, i) => [a, corners[(i + 1) % 4]]).sort((a, b) => a[0][1] + a[1][1] - b[0][1] - b[1][1]);
          for (const [a, b] of edges) {
            ctx.fillStyle = '#ac8d63'; polygon([a, b, [b[0], b[1] - 28], [a[0], a[1] - 28]]);
            ctx.strokeStyle = '#705536'; ctx.lineWidth = 1;
            for (const height of [0, 9, 18, 28]) { ctx.beginPath(); ctx.moveTo(a[0], a[1] - height); ctx.lineTo(b[0], b[1] - height); ctx.stroke(); }
            const count = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / 18));
            for (let j = 1; j < count; j++) { const bx = a[0] + (b[0] - a[0]) * j / count, by = a[1] + (b[1] - a[1]) * j / count; ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(bx, by - 28); ctx.stroke(); }
          }
          ctx.fillStyle = '#d0b789'; polygon(corners.map(([px, py]) => [px, py - 28]));
          ctx.strokeStyle='#96764e';ctx.lineWidth=1;
          for(let along=-f.width/2+18;along<f.width/2;along+=18){
            const px=f.x+f.ux*along,py=f.y+f.uy*along-28;
            ctx.beginPath();ctx.moveTo(px-f.nx*f.thickness/2,py-f.ny*f.thickness/2);ctx.lineTo(px+f.nx*f.thickness/2,py+f.ny*f.thickness/2);ctx.stroke();
          }
        } else { ctx.fillStyle = '#3d302e66'; polygon(corners.map(([px, py]) => [px + 3, py + 6])); }
        continue;
      }
      if (ground) {
        ctx.strokeStyle = f.mode === 'sharingan' ? '#ff6772' : f.mode === 'byakugan' ? '#f1e8ff' : f.mode === 'sand-shield' ? '#dab779' : '#7cfab4';
        ctx.lineWidth = 2; ctx.beginPath(); ctx.ellipse(x, y, 23 + Math.sin(phase) * 2, 8, 0, 0, TAU); ctx.stroke();
        if (f.mode === 'byakugan') for (const e of nearby(x, y, Math.min(360, finite(f.m.radius, 280))).slice(0, 40)) {
          if (!clearPath(x, y, e.x, e.y)) continue;
          ctx.strokeStyle = '#e8ddff'; ctx.strokeRect(Math.round(e.x - 7), Math.round(e.y - (e.bodyH || 28) - 8), 14, 5);
        }
      } else if (f.mode === 'sharingan' || f.mode === 'byakugan') {
        ctx.fillStyle = f.mode === 'sharingan' ? '#ff4659' : '#f8f2ff';
        const ey = y - (f.owner.bodyH || 35) + 13; ctx.fillRect(Math.round(x - 7), Math.round(ey), 5, 3); ctx.fillRect(Math.round(x + 3), Math.round(ey), 5, 3);
      } else if (f.mode === 'sand-shield') {
        ctx.strokeStyle = '#d6ae67'; ctx.lineWidth = 4; ctx.beginPath(); ctx.ellipse(x, y - 18, 27, 30, 0, Math.PI * 1.05, Math.PI * 1.95); ctx.stroke();
        ctx.fillStyle = '#6b4c2b'; ctx.fillRect(Math.round(x - 21), Math.round(y + 6), 42, 4);
        ctx.fillStyle = '#e8c684'; ctx.fillRect(Math.round(x - 21), Math.round(y + 6), 42 * f.shield / f.capacity, 3);
      } else {
        ctx.fillStyle = '#83ffb7';
        for (let i = 0; i < 8; i++) { const a = i * TAU / 8 + phase * .3, py = y - 10 - (f.age * 25 + i * 7) % 38; ctx.fillRect(Math.round(x + Math.cos(a) * 19), Math.round(py), 3, 6); }
        if (f.mode === 'medical-heal' || f.mode === 'regeneration') { ctx.fillRect(Math.round(x - 2), Math.round(y - 47), 4, 12); ctx.fillRect(Math.round(x - 6), Math.round(y - 43), 12, 4); }
      }
    }
    ctx.restore();
  }
  const updateFields = C.updateFields, ground = C.drawGroundFields, air = C.drawAirFields, clearFields = C.clearFields;
  C.updateFields = function(dt) { const result = updateFields.call(this, dt); update(dt); return result; };
  C.drawGroundFields = function(ctx) { ground.call(this, ctx); draw(ctx, true); };
  C.drawAirFields = function(ctx) { air.call(this, ctx); draw(ctx, false); };
  C.clearFields = function(owner) { clearFields.call(this, owner); clear(owner); };
  if (G.DigimonSkills?.clear) { const previous = G.DigimonSkills.clear; G.DigimonSkills.clear = owner => { previous(owner); clear(owner); }; }
  G.NarutoSupport = { supports: mode => modes.has(mode), canCast, cast, clear, update,
    takeAttackBonus, precisionMultiplier, geteffects: () => effects, getlocks: () => locks,
    get effects() { return effects; }, get locks() { return locks; } };
})();
