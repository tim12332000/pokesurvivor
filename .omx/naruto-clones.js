/* Local Naruto shadow clones: temporary combat actors, never players or saves. */
(() => {
  if (G.NarutoClones) return;
  const actors = [], smoke = [], C = G.Combat, TAU = Math.PI * 2;
  let serial = 0;
  const valid = a => a.owner === G.Game.player && !a.owner.dead && a.owner.hp > 0 && a.world === G.World;
  const living = owner => actors.filter(a => !a.dead && a.owner === owner && valid(a));
  const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
  const nearby = (x, y, r) => [...new Set(G.EnemyMgr.queryCircle(x, y, r))].filter(e => !e.dead);
  function clearPath(ax, ay, bx, by, radius = 0) {
    const d = Math.hypot(bx - ax, by - ay), steps = Math.max(1, Math.ceil(d / 5));
    for (let i = 1; i <= steps; i++) {
      const x = ax + (bx - ax) * i / steps, y = ay + (by - ay) * i / steps;
      if (radius ? !G.World.isFree(x, y, radius, true) : G.World.projectileBlock(x, y, 1)) return false;
    }
    return true;
  }
  function puff(a) {
    for (let i = 0; i < 12; i++) {
      const angle = i * TAU / 12;
      smoke.push({ x: a.x, y: a.y - 22, vx: Math.cos(angle) * (18 + i % 3 * 9), vy: Math.sin(angle) * 24 - 18, t: 0, life: .35 + i % 3 * .08 });
    }
    while (smoke.length > 180) smoke.shift();
  }
  function dismiss(a) { if (!a.dead) { a.dead = true; puff(a); } }
  function clear(owner) {
    for (let i = actors.length - 1; i >= 0; i--) if (!owner || actors[i].owner === owner) actors.splice(i, 1);
    // Smoke belongs to this local effect layer and must not survive a run reset.
    smoke.length = 0;
  }
  function cast(owner, move) {
    if (owner !== G.Game.player || owner.dead || owner.hp <= 0 || owner.mon?.dex !== 30001) return false;
    const lvl = move.lvl || 1, limit = Math.min(5, lvl >= 5 ? 5 : lvl >= 3 ? 4 : 3);
    let count = living(owner).length, spawned = false;
    for (let ring = 0; ring < 3 && count < limit; ring++) for (let n = 0; n < 12 && count < limit; n++) {
      const angle = n % limit * TAU / limit + Math.floor(n / limit) * .18 + ring * .22, radius = 56 + ring * 18;
      const x = owner.x + Math.cos(angle) * radius, y = owner.y + Math.sin(angle) * radius;
      if (!G.World.isFree(x, y, 10, true) || !clearPath(owner.x, owner.y, x, y, 10) || living(owner).some(a => Math.hypot(a.x - x, a.y - y) < 25)) continue;
      const a = { id: ++serial, owner, world: G.World, x, y, r: 10, age: 0, ttl: move.cloneDuration || 6,
        lvl, dmg: Number.isFinite(move.dmg) ? move.dmg : 8, punchCd: move.punchCd || .65,
        cd: .16 + count * .08, anim: new G.Sprites.Animator(30001, 1), target: null, dead: false, comboT: 0 };
      a.anim.dir = owner.anim.dir; a.anim.play('Charge'); actors.push(a); puff(a); count++; spawned = true;
    }
    if (spawned) owner.anim.play('Charge');
    return spawned;
  }
  function hit(a, enemy, base, type, knock = 12) {
    if (enemy.dead || !valid(a)) return;
    const typeK = G.Types.mult(type, enemy.types), crit = a.owner.critChance > 0 && Math.random() < a.owner.critChance;
    const dmg = base * typeK * G.Weather.mult(type) * (crit ? 1.5 : 1);
    enemy.hurt(dmg, '#a9dcff', enemy.x - a.x, enemy.y - a.y, knock, crit ? 'crit' : G.Types.label(typeK));
    a.owner.onDealt(dmg); a.owner.dmgDealt += dmg;
  }
  function moveToward(a, x, y, speed, dt) {
    const d = Math.hypot(x - a.x, y - a.y);
    if (d < 1) return false;
    const step = Math.min(d, speed * dt), dx = (x - a.x) / d * step, dy = (y - a.y) / d * step;
    const ox = a.x, oy = a.y;
    // Bounded steps and independent axes prevent tunnelling and corner cutting.
    const pieces = Math.max(1, Math.ceil(step / 4));
    for (let i = 0; i < pieces; i++) {
      if (G.World.isFree(a.x + dx / pieces, a.y, a.r, true)) a.x += dx / pieces;
      if (G.World.isFree(a.x, a.y + dy / pieces, a.r, true)) a.y += dy / pieces;
      G.World.collide(a);
    }
    a.anim.dir = G.Sprites.dirFromAngle(Math.atan2(y - oy, x - ox));
    return Math.hypot(a.x - ox, a.y - oy) > .1;
  }
  function update(dt) {
    if (!(dt > 0) || !Number.isFinite(dt)) return;
    // Run actor simulation in small steps even when a manual test advances a long frame.
    const steps = Math.max(1, Math.ceil(dt / .04)), sub = dt / steps;
    for (let step = 0; step < steps; step++) {
      const claimed = new Set();
      for (const a of actors) {
        if (a.dead) continue;
        if (!valid(a)) { a.dead = true; continue; }
        a.age += sub; a.cd -= sub; a.comboT = Math.max(0, a.comboT - sub);
        if (a.age >= a.ttl) { dismiss(a); continue; }
        const enemies = nearby(a.owner.x, a.owner.y, 240).filter(e => distance(a, e) <= 280);
        enemies.sort((b, c) => (claimed.has(b) - claimed.has(c)) || distance(a, b) - distance(a, c));
        a.target = enemies.find(e => clearPath(a.x, a.y, e.x, e.y)) || null;
        let moving = false;
        if (a.target) {
          const e = a.target; claimed.add(e);
          const reach = 35 + (e.r || 0);
          if (distance(a, e) > reach) moving = moveToward(a, e.x, e.y, Math.max(125, a.owner.spd || 0), sub);
          else {
            a.anim.dir = G.Sprites.dirFromAngle(Math.atan2(e.y - a.y, e.x - a.x));
            if (a.cd <= 0 && clearPath(a.x, a.y, e.x, e.y)) {
              a.cd = a.punchCd; a.anim.play('Attack', { speed: 1.3 });
              hit(a, e, a.dmg * a.owner.atk, 'fighting');
              G.FX.spark(e.x, e.y - (e.bodyH || 30) * .5, '#a9dcff', e.x - a.x, e.y - a.y, 3);
            }
          }
        } else {
          const angle = (a.id - 1) % 5 * TAU / 5, x = a.owner.x + Math.cos(angle) * 74, y = a.owner.y + Math.sin(angle) * 66;
          if (Math.hypot(a.x - x, a.y - y) > 20) moving = moveToward(a, x, y, 165, sub);
        }
        if (a.age >= .25) for (const e of nearby(a.x, a.y, a.r + 45)) {
          if (e.behavior === 'thief' || e.touchCd > 0) continue;
          if (distance(a, e) <= a.r + (e.r || 0) && clearPath(a.x, a.y, e.x, e.y)) {
            e.touchCd = .55; e.anim?.play('Attack'); dismiss(a); break;
          }
        }
        a.anim.loop(moving ? 'Walk' : 'Idle', moving ? 1.4 : 1); a.anim.update(sub);
      }
      for (let i = actors.length - 1; i >= 0; i--) if (actors[i].dead) actors.splice(i, 1);
      for (let i = smoke.length - 1; i >= 0; i--) {
        const p = smoke[i]; p.t += sub; p.x += p.vx * sub; p.y += p.vy * sub;
        if (p.t >= p.life) smoke.splice(i, 1);
      }
    }
  }
  function combo(owner, move) {
    if (!owner.hasMove?.('naruto-naruto')) return 0;
    const participants = living(owner).filter(a => a.lvl >= 3), hits = [];
    for (const a of participants) {
      const e = nearby(a.x, a.y, 90).sort((b, c) => distance(a, b) - distance(a, c)).find(e => clearPath(a.x, a.y, e.x, e.y, 2));
      if (e) hits.push([a, e]);
      if(hits.length===2)break;
    }
    // One shared damage budget, rather than a full Rasengan per clone.
    for (const [a, e] of hits) {
      a.anim.dir = G.Sprites.dirFromAngle(Math.atan2(e.y - a.y, e.x - a.x));
      a.anim.play('Attack'); a.comboT = .4;
      hit(a, e, move.dmg * owner.atk * .4 / hits.length, move.type || 'fighting', 28);
      G.FX.beam(a.x, a.y - G.LIFT, Math.atan2(e.y - a.y, e.x - a.x), distance(a, e), 8, '#83dcff', { pal: 'water' });
    }
    return hits.length;
  }
  function draw(ctx) {
    const owner=G.Game.player;
    if(owner&&living(owner).length){
      ctx.save();ctx.fillStyle='#ffd23f';const y=Math.round(owner.y-owner.bodyH-8),x=Math.round(owner.x);
      ctx.beginPath();ctx.moveTo(x-5,y-4);ctx.lineTo(x+5,y-4);ctx.lineTo(x,y+2);ctx.closePath();ctx.fill();ctx.restore();
    }
    for (const a of [...actors].sort((a, b) => a.y - b.y)) {
      if (!valid(a)) continue;
      const alpha = Math.min(.82, Math.max(0, a.ttl - a.age) * 2);
      a.anim.draw(ctx, a.x, a.y, { alpha });
      if (a.comboT > 0) {
        ctx.save(); ctx.globalAlpha = a.comboT * 2; ctx.fillStyle = '#b8f3ff';
        ctx.fillRect(Math.round(a.x + 10), Math.round(a.y - 29), 9, 9); ctx.restore();
      }
    }
    ctx.save(); ctx.fillStyle = '#dfedff';
    for (const p of smoke) { ctx.globalAlpha = .65 * (1 - p.t / p.life); const size = 5 + Math.floor(p.t * 12); ctx.fillRect(Math.round(p.x), Math.round(p.y), size, size); }
    ctx.restore();
  }
  function ground(ctx) {
    ctx.save();
    for (const a of actors) if (valid(a)) {
      ctx.globalAlpha = .22; ctx.fillStyle = '#081b3a'; ctx.beginPath(); ctx.ellipse(a.x, a.y, 13, 5, 0, 0, TAU); ctx.fill();
      ctx.globalAlpha = .25; ctx.strokeStyle = '#83caff'; ctx.strokeRect(Math.round(a.x - 12), Math.round(a.y - 3), 24, 4);
    }
    ctx.restore();
  }
  // Only basic pursuers can be distracted. The proxy never writes to the player.
  const enemyUpdate = G.Enemy.prototype.update;
  G.Enemy.prototype.update = function(dt, player) {
    if (!this.dead && !this.boss && !this.legend && !this.judge && !this.remote && ['chase', 'runner'].includes(this.behavior)) {
      const candidates = living(player).filter(a => distance(a, this) < 140 && distance(a, this) < distance(player, this) && clearPath(this.x, this.y, a.x, a.y));
      candidates.sort((a, b) => distance(a, this) - distance(b, this));
      if (candidates.length) {
        const clone = candidates[0];
        player = new Proxy(player, { get(target, key) { if (key === 'x' || key === 'y' || key === 'r') return clone[key]; if (key === '_vx' || key === '_vy') return 0; return Reflect.get(target, key); }, set() { return true; } });
      }
    }
    return enemyUpdate.call(this, dt, player);
  };
  const resolve = C.resolve;
  C.resolve = function(dt, owner, now) {
    const list = G.Projectiles.all();
    for (let i = list.length - 1; i >= 0; i--) {
      const p = list[i]; if (p.friendly !== false || G.World.projectileBlock(p.x, p.y, p.r)) continue;
      const sx = p.px ?? p.x, sy = p.py ?? p.y, dx = p.x - sx, dy = p.y - sy, length2 = dx * dx + dy * dy;
      const along = obj => length2 ? Math.max(0, Math.min(1, ((obj.x - sx) * dx + (obj.y - sy) * dy) / length2)) : 0;
      const playerT = owner && Math.hypot(owner.x - p.x, owner.y - p.y) < p.r + owner.r ? along(owner) : Infinity;
      const candidates = living(owner).filter(a => {
        const t = along(a); return a.age >= .25 && t <= playerT && Math.hypot(sx + dx * t - a.x, sy + dy * t - a.y) <= p.r + a.r && clearPath(sx, sy, a.x, a.y);
      }).sort((a, b) => along(a) - along(b));
      if (candidates.length) { dismiss(candidates[0]); list.splice(i, 1); }
    }
    return resolve.call(this, dt, owner, now);
  };
  const updateFields = C.updateFields, air = C.drawAirFields, oldGround = C.drawGroundFields, clearFields = C.clearFields;
  C.updateFields = function(dt) { const result = updateFields.call(this, dt); update(dt); return result; };
  C.drawAirFields = function(ctx) { air.call(this, ctx); draw(ctx); };
  C.drawGroundFields = function(ctx) { oldGround.call(this, ctx); ground(ctx); };
  C.clearFields = function(owner) { clearFields.call(this, owner); clear(owner); };
  if (G.DigimonSkills?.clear) { const previous = G.DigimonSkills.clear; G.DigimonSkills.clear = owner => { previous(owner); clear(owner); }; }
  G.NarutoClones = { cast, update, draw, clear, combo, get actors() { return actors; } };
})();
