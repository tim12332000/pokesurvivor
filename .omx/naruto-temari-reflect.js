/* Wind return: physical interception, then real owner-attributed countershots. */
(() => {
  if (G.NarutoTemariReflect) return;
  const MODE = 'temari-reflect', ID = 'naruto-temari-reflect';
  const states = new Map(), flashes = [], damageOwners = new WeakSet();
  let serial = 0;
  const alive = a => !!a && !a.dead && a.hp > 0;
  const controlled = a => a === G.Game.player || !!G.SelfClones?.isActor(a);
  const valid = a => alive(a) && controlled(a) && (a.mon?.dex ?? a.dex) === 30011;
  const playing = () => G.Game.state === 'playing';
  const supports = mode => mode === MODE;
  const rank = m => Math.max(1, Math.min(5, Math.floor(m?.lvl || 1)));
  const quantity = a => Math.max(0, Math.floor(G.Quantity?.bonus(a) ?? a.quantityPicks ?? a.quantityBonus ?? 0));
  function state(owner) {
    let s = states.get(owner);
    if (s?.world !== G.World) { states.delete(owner); s = null; }
    if (!s) { s = { owner, world: G.World, clock: 0, wall: null, casts: 0, intercepted: 0, returned: 0 }; states.set(owner, s); }
    return s;
  }
  // This technique is learned once and remains present independently of slots.
  const learned = owner => owner?.moves?.find(m => m.id === ID || m.digiMode === MODE);
  function canCast() { return false; }
  function cast() { return false; }
  function sync(owner) {
    if (!valid(owner)) return null;
    const m = learned(owner), previous = states.get(owner);
    if (!m) { if (previous) clear(owner); return null; }
    const s = state(owner), i = rank(m) - 1, Q = quantity(owner);
    const packet = { id: ID, mode: MODE, permanent: true, duration: 0,
      radius: [85, 95, 110, 125, 140][i], multiplier: [1, 1.2, 1.4, 1.7, 2][i],
      copies: Math.floor(1.25 ** Q), atk: owner.atk ?? 1, lvl: i + 1, Q,
      stats: { critChance: owner.critChance || 0, percentHealthDamage: owner.percentHealthDamage || 0,
        lifestealRate: owner.lifestealRate || 0, damageSplashPicks: owner.damageSplashPicks || 0,
        item: owner.item || null, maxHp: owner.maxHp || 1 } };
    const signature = JSON.stringify(packet);
    if (s.signature !== signature || !s.wall) {
      const old = s.wall;
      const wire = { ...packet, castId: old?.castId ?? ++serial, revision: (old?.revision || 0) + 1,
        x: owner.x, y: owner.y, aim: owner.aim || 0 };
      s.wall = { ...wire, owner, world: G.World, ghost: false, age: old?.age || 0,
        pulse: old?.pulse || 0, started: old?.started ?? s.clock };
      s.signature = signature;
      G.NarutoTemariReflect.onSync?.(owner, wire);
    }
    return s.wall;
  }
  function syncLocal() {
    for (const owner of [G.Game.player, ...(G.SelfClones?.actors?.() || [])]) if (valid(owner)) sync(owner);
  }
  function ghost(owner, packet) {
    if (!owner || packet?.mode !== MODE) return false;
    if (packet.removed) { clear(owner); return true; }
    const s = state(owner), old = s.wall;
    s.wall = { ...packet, owner, world: G.World, ghost: true, age: old?.age || 0,
      pulse: old?.pulse || 0, started: old?.started ?? s.clock };
    return true;
  }
  function activeFor(owner) {
    const w = states.get(owner)?.wall;
    return w && w.world === G.World && alive(owner) && (w.permanent || w.age < w.duration) ? w : null;
  }
  function stateFor(owner) {
    const wall = activeFor(owner), s = states.get(owner);
    return s && s.world === G.World && alive(owner) ? { ...s, wall, cooldowns: {} } : null;
  }
  function clear(owner) {
    if (owner) {
      const s = states.get(owner); states.delete(owner);
      if (s?.wall && !s.wall.ghost) G.NarutoTemariReflect.onSync?.(owner, null);
    } else { for (const actor of [...states.keys()]) clear(actor); flashes.length = 0; }
  }
  function walls() { syncLocal(); return [...states.keys()].map(activeFor).filter(w => w && (w.ghost || valid(w.owner))); }
  function permitted(w, attack) {
    const decision = G.NarutoTemariReflect.mayReflect?.(w.owner, attack);
    return decision === undefined || decision === null ? !w.ghost : decision === true;
  }
  function damageOwner(w) {
    if (!w.ghost) return w.owner;
    if (!w.damageOwner) {
      const proxy = Object.create(w.owner);
      for (const [key, value] of Object.entries(w.stats || {})) Object.defineProperty(proxy, key, { value, writable: true, configurable: true });
      Object.defineProperty(proxy, 'atk', { value: w.atk, configurable: true });
      proxy.onDealt = damage => G.NarutoTemariReflect.onReflectionDamage?.(w.owner, damage, w);
      proxy.dmgDealt = 0;
      damageOwners.add(proxy);
      w.damageOwner = proxy;
    }
    return w.damageOwner;
  }
  // Intercept the first boundary contact, or immediately return hostile attacks
  // already inside the permanent wind's full footprint.
  function entry(ax, ay, bx, by, w, padding = 0) {
    const cx = w.owner.x, cy = w.owner.y, r = w.radius + padding;
    const dx = bx - ax, dy = by - ay, ox = ax - cx, oy = ay - cy;
    const a = dx * dx + dy * dy, b = 2 * (ox * dx + oy * dy), c = ox * ox + oy * oy - r * r;
    if (c <= 0) return { t: 0, x: ax, y: ay };
    if (a < 1e-10) return null;
    const disc = b * b - 4 * a * c;
    if (disc < 0) return null;
    const t = (-b - Math.sqrt(disc)) / (2 * a);
    return t >= 0 && t <= 1 ? { t, x: ax + dx * t, y: ay + dy * t } : null;
  }
  function emit(owner, packet, visualOnly = false) {
    const speed = Math.max(260, packet.speed || 0), count = packet.copies;
    for (let i = 0; i < count; i++) {
      // Parallel wind lanes preserve the exact reverse incoming direction.
      const lane = (i - (count - 1) / 2) * 3, dx = Math.cos(packet.angle), dy = Math.sin(packet.angle);
      G.Projectiles.spawn({ x: packet.x - dy * lane, y: packet.y + dx * lane,
        vx: dx * speed, vy: dy * speed, r: Math.max(5, Math.min(18, packet.r || 7)),
        dmg: packet.damage, life: Math.max(1.5, Math.min(5, packet.life || 3)), friendly: true,
        owner, mid: ID, mtype: packet.type || 'flying', ghost: visualOnly,
        color: '#cdf9ec', vis: G.VFX.forType(packet.type || 'flying'),
        pierce: packet.beam ? 4 : 0, hits: new Set(), damageSplash: true, temariReflected: true });
    }
    flashes.push({ x: packet.x, y: packet.y, angle: packet.angle, age: 0 });
  }
  function reflect(w, attack, point, angle, beam = false) {
    const owner = w.owner, base = attack.pct ? Math.max(attack.dmg || 0, (w.stats?.maxHp ?? owner.maxHp) * attack.pct) : attack.dmg || 0;
    const packet = { castId: w.castId, reflectionId: ++serial, x: point.x, y: point.y, angle,
      copies: w.copies, damage: base * w.multiplier * w.atk,
      type: attack.mtype || attack.type || 'flying', r: attack.r || (attack.w || 14) / 2,
      speed: Math.hypot(attack.vx || 0, attack.vy || 0), life: attack.life, beam,
      sourceKind: attack.kind ? 'hazard' : 'projectile',
      sourceNetId: attack.coopShotId ?? attack.netId ?? null };
    emit(damageOwner(w), packet);
    const s = state(owner); s.intercepted++; s.returned += packet.copies; w.pulse = .24;
    G.NarutoTemariReflect.onReflect?.(owner, packet, attack);
  }
  function receiveReflection(owner, packet) {
    if (!owner || !packet || !Number.isFinite(packet.angle) || !(packet.copies > 0)) return false;
    emit(owner, packet, true); return true;
  }
  function interceptProjectiles() {
    if (!playing()) return;
    const active = walls();
    for (const p of [...G.Projectiles.all()]) {
      if (p.friendly || p.temariReflected) continue;
      const ax = p.px ?? p.x, ay = p.py ?? p.y;
      let first = null;
      for (const w of active) {
        const hit = entry(ax, ay, p.x, p.y, w, p.r || 0);
        if (hit && permitted(w, p) && (!first || hit.t < first.point.t)) first = { w, point: hit };
      }
      if (!first) continue;
      G.Projectiles.remove(p);
      reflect(first.w, p, first.point, Math.atan2(-(p.vy || 0), -(p.vx || 0)));
    }
  }
  function interceptHazards(dt) {
    if (!playing()) return;
    for (const h of G.Hazards.all) {
      if (h.hit || h.t + dt < h.delay || h.temariReturned || h.ranged === false) continue;
      const beam = h.kind === 'beam';
      if (!beam && !h.ranged) continue;
      let first = null;
      for (const w of walls()) {
        let hit;
        if (beam) {
          hit = entry(h.x, h.y, h.x + Math.cos(h.angle) * h.len, h.y + Math.sin(h.angle) * h.len, w, (h.w || 0) / 2);
        } else {
          if (Number.isFinite(h.sourceX) && Number.isFinite(h.sourceY)) hit = entry(h.sourceX, h.sourceY, h.x, h.y, w, 0);
          // Falling attacks physically contact the dome above its footprint.
          if (!hit && Math.hypot(h.x - w.owner.x, h.y - w.owner.y) <= w.radius + (h.r || 0)) hit = { t: 1, x: h.x, y: h.y };
        }
        if (hit && permitted(w, h) && (!first || hit.t < first.point.t)) first = { w, point: hit };
      }
      if (!first) continue;
      h.temariReturned = true;
      const angle = beam ? h.angle + Math.PI : Math.atan2((h.sourceY ?? h.y) - first.point.y, (h.sourceX ?? h.x) - first.point.x);
      reflect(first.w, h, first.point, angle, beam);
      if (beam) {
        // Keep the original beam on the attacker's side of the wind wall.
        h.len = Math.max(0, h.len * first.point.t - (h.w || 0));
        if (h.len === 0) { h.hit = true; h.t = h.delay; }
      } else { h.hit = true; h.t = h.delay; }
    }
  }
  function update(dt) {
    if (!playing() || !Number.isFinite(dt) || dt <= 0) return;
    syncLocal();
    for (const [owner, s] of states) {
      if (s.world !== G.World || !alive(owner) || (!controlled(owner) && !s.wall?.ghost)) { clear(owner); continue; }
      s.clock += dt;
      if (s.wall) { s.wall.age += dt; s.wall.pulse = Math.max(0, s.wall.pulse - dt); if (!s.wall.permanent && s.wall.age >= s.wall.duration) s.wall = null; }
    }
    for (let i = flashes.length - 1; i >= 0; i--) { flashes[i].age += dt; if (flashes[i].age > .3) flashes.splice(i, 1); }
  }
  function draw(ctx) {
    G.TemariCycloneVFX?.drawReflection(ctx,{
      walls:[...states.keys()].map(activeFor).filter(Boolean),
      projectiles:G.Projectiles.all().filter(p=>p.temariReflected),flashes
    });
  }
  G.NarutoTemariReflect = { supports, canCast, cast, sync, ghost, receiveReflection, activeFor, stateFor, clear,
    update, draw, interceptProjectiles, interceptHazards, onCast: null, onSync: null, onReflect: null,
    mayReflect: null, onReflectionDamage: null, isDamageOwner: owner => damageOwners.has(owner) };
  const resolve = G.Combat.resolve, fields = G.Combat.updateFields, air = G.Combat.drawAirFields, clearFields = G.Combat.clearFields;
  G.Combat.resolve = function(...args) { interceptProjectiles(); return resolve.apply(this, args); };
  G.Combat.updateFields = function(dt) { const result = fields.call(this, dt); update(dt); return result; };
  G.Combat.drawAirFields = function(ctx) { const result = air.call(this, ctx); draw(ctx); return result; };
  G.Combat.clearFields = function(owner) { clear(owner); return clearFields.call(this, owner); };
  const hazards = G.Hazards.update;
  G.Hazards.update = function(dt) { interceptHazards(dt); return hazards.call(this, dt); };
})();
