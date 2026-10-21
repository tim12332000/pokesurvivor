/* Passive Sand Shield guardians: independent physical clouds. */
(() => {
  if (G.NarutoSandGuard) return;
  const C = G.Combat, id = 'naruto-sand-shield';
  const config = Object.freeze({
    ranges: Object.freeze([400, 400, 400, 400, 400]),
    speedBonus: 200,
    capacities: Object.freeze([2, 2, 3, 3, 4]),
    attackDamages: Object.freeze([20, 25, 30, 35, 40]), attackCooldown: 1,
    recharge: 2.5, radius: 14, turnRate: 3.6
  });
  let guard = null;
  const finite = Number.isFinite;
  const learned = owner => {
    G.NarutoSkillCatalog?.migrateGaaraPassives?.(owner);
    return owner?.moves?.find(m => m.id === id);
  };
  function valid(s) {
    return s && s.owner === G.Game.player && s.world === G.World &&
      !s.owner.dead && s.owner.hp > 0 && s.owner.mon?.dex === 30007 && !!learned(s.owner);
  }
  function clear(owner) { if (!owner || guard?.owner === owner) guard = null; }
  function state(owner = G.Game.player) {
    if (guard && !valid(guard)) guard = null;
    if (owner !== G.Game.player || owner?.dead || !(owner?.hp > 0) || owner.mon?.dex !== 30007) return null;
    const move = learned(owner);
    if (!move) return null;
    const tier = Math.max(1, Math.min(5, move.lvl | 0)), count = Math.min(10, config.capacities[tier - 1] + Math.max(1, owner.level | 0));
    if (!guard) guard = { owner, world: G.World, guardians: [], flowAge: 0, flowClock: .1,
      flowPairChecks: 0, flowPoolCount: 1,
      flowDwell: new Float32Array(100), flowJoined: new Uint8Array(100),
      flowGroups: Array.from({ length: 3 }, (_, id) => ({ id, x: owner.x, y: owner.y,
        aimX: owner.x, aimY: owner.y, heading: 0, phase: 0, blend: 0, active: false, members: [] })) };
    // Growth creates only the added clouds; existing returns and recharge persist.
    while (guard.guardians.length < count) {
      const index = guard.guardians.length, angle = index * 2.399963229728653;
      const x = owner.x + Math.cos(angle) * 46, y = owner.y + Math.sin(angle) * 46;
      guard.guardians.push({ owner, world: G.World, index,
        x, y, age: 0,
        ready: true, charges: 1, capacity: 1, phase: 'wander', target: null, rechargeProgress: 0,
        attackTarget: null, attackCooldown: 0,
        vx: 0, vy: 0, heading: angle, contact: null, flash: 0, trail: [],
        flowGroupId: -1, flowHome: 0, flowSlot: 0, flowSlots: 1,
        flowBlend: 0, flowMerge: false, flowPhase: 0, flowAimX: x, flowAimY: y });
    }
    guard.guardians.length = count;
    const playerSpeed = owner.spd;
    const speed = Math.max(0, finite(playerSpeed) ? playerSpeed : 0) + config.speedBonus;
    guard.tier = tier; guard.count = count; guard.range = config.ranges[tier - 1]; guard.speed = speed; guard.move = move;
    for (const s of guard.guardians) { s.tier = tier; s.range = guard.range; s.speed = speed; s.move = move; }
    guard.readyCount = guard.guardians.reduce((n, s) => n + Number(s.ready), 0);
    return guard;
  }
  function blockable(p) {
    return p.friendly === false && !p.unblockable && !p.guardUnblockable && !p.uninterceptable &&
      !p.hazard && !p.laser && !p.beam && !p.ground && !p.orb &&
      finite(p.x) && finite(p.y) && finite(p.vx) && finite(p.vy);
  }
  // Only visual grouping runs at 10 Hz. Combat assignment and swept contact
  // continue at their original substep frequency. All pair storage is bounded.
  function regroup(group, elapsed, assignments) {
    let available = 0;
    for (const s of group.guardians) if (s.ready && !assignments.has(s)) available++;
    const pools = group.flowPoolCount = Math.max(1, Math.min(3, Math.ceil(available / 4)));
    for (const pool of group.flowGroups) { pool.members.length = 0; pool.active = false; }
    let rank = 0;
    for (const s of group.guardians) {
      s.flowMerge = false;
      if (!s.ready || assignments.has(s)) { s.flowGroupId = -1; continue; }
      s.flowHome = rank % pools; s.flowSlot = Math.floor(rank / pools);
      s.flowSlots = Math.ceil((available - s.flowHome) / pools);
      s.flowGroupId = s.flowHome;
      group.flowGroups[s.flowHome].members.push(s.index);
      rank++;
    }
    if (available < 2) {
      group.flowDwell.fill(0); group.flowJoined.fill(0); group.flowPairChecks = 0;
      return;
    }
    let checks = 0;
    for (let i = 0; i < group.guardians.length; i++) {
      const a = group.guardians[i];
      for (let j = i + 1; j < group.guardians.length; j++) {
        const b = group.guardians[j], key = i * 10 + j;
        checks++;
        const eligible = a.flowGroupId >= 0 && a.flowGroupId === b.flowGroupId;
        if (!eligible) {
          group.flowJoined[key] = 0; group.flowDwell[key] = 0;
          continue;
        }
        const dx = a.x - b.x, dy = a.y - b.y, distance2 = dx * dx + dy * dy;
        const alignment = Math.cos(a.heading - b.heading);
        if (group.flowJoined[key]) {
          if (!eligible || distance2 > 900 || alignment < -.25) {
            group.flowJoined[key] = 0; group.flowDwell[key] = 0;
          }
        } else if (eligible && distance2 <= 324 && alignment > .3) {
          group.flowDwell[key] += elapsed;
          if (group.flowDwell[key] >= .15) group.flowJoined[key] = 1;
        } else group.flowDwell[key] = 0;
        if (group.flowJoined[key]) a.flowMerge = b.flowMerge = true;
      }
    }
    group.flowPairChecks = checks;
  }
  function advanceFlow(group, h, assignments) {
    group.flowAge += h; group.flowClock += h;
    if (group.flowClock >= .1) {
      const elapsed = group.flowClock; group.flowClock %= .1;
      regroup(group, elapsed, assignments);
    }
    let available = 0;
    for (const s of group.guardians) {
      s.flowPhase = group.flowAge;
      if (s.ready && !assignments.has(s)) available++;
      else { s.flowGroupId = -1; s.flowMerge = false; }
      const merging = s.ready && !assignments.has(s) && s.flowMerge;
      s.flowBlend = Math.max(0, Math.min(1, s.flowBlend + (merging ? h : -h) / .3));
    }
    // Pursuit needs no idle anchors. In a full volley every guardian already
    // has an assigned shot; do not compute invisible formation geometry.
    if (!available) return;
    const pools = group.flowPoolCount;
    for (const pool of group.flowGroups) {
      if (pool.id >= pools) continue;
      // Three evenly spaced inner pools preserve coverage on every side.
      const angle = group.flowAge * .12 + pool.id * Math.PI * 2 / pools;
      const radius = (pools === 3 ? 108 : 138) + Math.sin(group.flowAge * .37 + pool.id * 1.7) * 8;
      pool.aimX = group.owner.x + Math.cos(angle) * radius;
      pool.aimY = group.owner.y + Math.sin(angle) * radius;
      pool.heading = angle + Math.PI / 2; pool.phase = group.flowAge;
    }
    for (const s of group.guardians) {
      if (!s.ready || assignments.has(s)) continue;
      const pool = group.flowGroups[s.flowHome];
      const offset = (s.flowSlot - (s.flowSlots - 1) * .5) * 5;
      s.flowAimX = pool.aimX + Math.cos(pool.heading) * offset;
      s.flowAimY = pool.aimY + Math.sin(pool.heading) * offset;
    }
  }
  function flowCenters(group) {
    for (const pool of group.flowGroups) {
      let x = 0, y = 0, blend = 0, count = 0, seed = null;
      // A center is drawable only after physical nodes have really joined.
      for (const index of pool.members) {
        const s = group.guardians[index];
        if (!s || s.flowGroupId !== pool.id || !s.flowMerge || s.flowBlend <= 0 || !s.ready || s.phase !== 'wander') continue;
        // Two distant pairs assigned to one anchor are still separate streams.
        // Never put a painted body at their empty midpoint while they converge.
        if (!seed) seed = s;
        const dx = s.x - seed.x, dy = s.y - seed.y;
        if (dx * dx + dy * dy > 900) continue;
        x += s.x; y += s.y; blend += s.flowBlend; count++;
      }
      pool.active = count > 1;
      pool.blend = count ? blend / count : 0;
      if (count) { pool.x = x / count; pool.y = y / count; }
    }
  }
  // First contact with a circle under relative constant velocity; null means a miss.
  function contactTime(dx, dy, vx, vy, radius) {
    const c = dx * dx + dy * dy - radius * radius;
    if (c <= 0) return 0;
    const a = vx * vx + vy * vy, b = 2 * (dx * vx + dy * vy);
    if (a < 1e-12 || b >= 0) return null;
    const discriminant = b * b - 4 * a * c;
    if (discriminant < 0) return null;
    return (-b - Math.sqrt(discriminant)) / (2 * a);
  }
  function threat(s, q, elapsed) {
    const x = q.x + q.vx * elapsed, y = q.y + q.vy * elapsed;
    const lifetime = finite(q.p.life) ? q.p.life - (q.p.t || 0) + q.dt - elapsed : Infinity;
    if (lifetime <= 0 || Math.hypot(x - s.owner.x, y - s.owner.y) > s.range + q.r) return null;
    const ownerImpact = contactTime(x - s.owner.x, y - s.owner.y, q.vx, q.vy, (s.owner.r || 10) + q.r);
    if (ownerImpact !== null && ownerImpact <= 1e-9) return null;
    const impact = ownerImpact !== null && ownerImpact <= lifetime ? ownerImpact : Infinity;
    // Predict a reachable intercept when possible. Faster or off-axis hostile
    // shots still deserve pursuit; the cloud must make contact to erase them.
    const dx = x - s.x, dy = y - s.y, r = config.radius + q.r;
    const a = q.vx * q.vx + q.vy * q.vy - s.speed * s.speed;
    const b = 2 * (dx * q.vx + dy * q.vy - r * s.speed), c = dx * dx + dy * dy - r * r;
    let intercept = 0;
    if (c > 0) {
      const d = b * b - 4 * a * c;
      if (Math.abs(a) < 1e-9) intercept = b < 0 ? -c / b : Infinity;
      else if (d < 0) intercept = Infinity;
      else {
        const root = Math.sqrt(d), first = (-b - root) / (2 * a), second = (-b + root) / (2 * a);
        intercept = Math.min(first >= 0 ? first : Infinity, second >= 0 ? second : Infinity);
      }
    }
    const reachable = finite(intercept) && intercept < Math.min(impact, lifetime);
    const lead = reachable ? intercept : Math.min(.15, lifetime, Math.hypot(dx, dy) / s.speed);
    return { q, x, y, impact, reachable, distance: Math.hypot(dx, dy),
      aimX: x + q.vx * lead, aimY: y + q.vy * lead };
  }
  function attackable(enemy, group) {
    return enemy && !enemy.dead && enemy.hp > 0 && !enemy.friendly &&
      finite(enemy.x) && finite(enemy.y) &&
      (enemy.x - group.owner.x) ** 2 + (enemy.y - group.owner.y) ** 2 <= group.range ** 2;
  }
  function attack(s, enemy, group) {
    if (!attackable(enemy, group)) return false;
    const owner = group.owner, move = group.move;
    const mult = G.Types.mult(move.type, enemy.types), crit = Math.random() < (owner.critChance || 0);
    const damage = config.attackDamages[group.tier - 1] * owner.atk * mult *
      G.Weather.mult(move.type) * (crit ? 1.5 : 1);
    enemy.hurt(damage, '#d4cdbb', enemy.x - s.x, enemy.y - s.y, move.knock || 0,
      crit ? 'crit' : G.Types.label(mult), owner, move.id);
    owner.onDealt(damage); owner.dmgDealt += damage;
    return true;
  }
  function update(dt, owner) {
    const group = state(owner);
    if (!group || G.Game.state !== 'playing' || owner.frozen || !finite(dt) || !(dt > 0)) return;
    const projectiles = [];
    for (const p of G.Projectiles.all()) if (blockable(p)) projectiles.push({ p, r: Math.max(0, p.r || 0), dt,
      x: finite(p.px) ? p.px : p.x - p.vx * dt, y: finite(p.py) ? p.py : p.y - p.vy * dt,
      vx: finite(p.px) ? (p.x - p.px) / dt : p.vx, vy: finite(p.py) ? (p.y - p.py) / dt : p.vy });
    const missed = new Set(), removed = new Set();
    // Lazily shared by every offensive guardian/substep: no terrain queries,
    // and at most one enemy spatial lookup for this whole simulation update.
    let enemies = null;
    const count = Math.min(240, Math.max(1, Math.ceil(dt / .02))), h = dt / count;
    for (let i = 0; i < count; i++) {
      const elapsed = i * h;
      const claimed = new Set(), contacts = [], motions = [];
      const candidates = new Map(), assignments = new Map();
      let defending = false;
      for (const q of projectiles) {
        if (removed.has(q.p)) continue;
        const x = q.x + q.vx * elapsed, y = q.y + q.vy * elapsed;
        if ((!finite(q.p.life) || (q.p.t || 0) - q.dt + elapsed < q.p.life) &&
          Math.hypot(x - owner.x, y - owner.y) <= group.range + q.r) { defending = true; break; }
      }
      for (const s of group.guardians) {
        const list = [];
        if (s.ready) for (const q of projectiles) {
          if (removed.has(q.p) || missed.has(q.p)) continue;
          const candidate = threat(s, q, elapsed);
          if (candidate) list.push(candidate);
        }
        candidates.set(s, list);
      }
      // Pair urgent shots with the nearest available guardian across the group,
      // so array order cannot strand a nearby guardian or leave extra shots idle.
      for (let slot = 0; slot < group.count; slot++) {
        let best = null;
        for (const s of group.guardians) {
          if (!s.ready || assignments.has(s) || Math.hypot(s.x - owner.x, s.y - owner.y) > s.range) continue;
          for (const candidate of candidates.get(s)) {
            if (claimed.has(candidate.q.p)) continue;
            const current = best?.candidate;
            if (!current || candidate.impact < current.impact ||
              (candidate.impact === current.impact && (Number(candidate.reachable) > Number(current.reachable) ||
                (candidate.reachable === current.reachable && candidate.distance < current.distance)))) {
              best = { s, candidate };
            }
          }
        }
        if (!best) break;
        const t = best.candidate;
        if (Math.hypot(t.aimX - owner.x, t.aimY - owner.y) > best.s.range) { t.aimX = t.x; t.aimY = t.y; }
        assignments.set(best.s, best.candidate); claimed.add(best.candidate.q.p);
      }
      const busy = new Set(assignments.keys());
      for (const s of group.guardians) {
        s.attackWait = s.attackCooldown;
        s.attackCooldown = Math.max(0, s.attackCooldown - h);
        if (defending || !s.ready || s.attackCooldown > 0 ||
          Math.hypot(s.x - owner.x, s.y - owner.y) > s.range) s.attackTarget = null;
        else {
          if (!attackable(s.attackTarget, group)) {
            if (!enemies) enemies = G.EnemyMgr.queryCircle(owner.x, owner.y, group.range);
            let nearest = null, distance = Infinity;
            for (const enemy of enemies) {
              if (!attackable(enemy, group)) continue;
              const d = (enemy.x - s.x) ** 2 + (enemy.y - s.y) ** 2;
              if (d < distance) { nearest = enemy; distance = d; }
            }
            s.attackTarget = nearest;
          }
          if (s.attackTarget) busy.add(s);
        }
      }
      advanceFlow(group, h, busy);
      for (const s of group.guardians) {
        const wasReady = s.ready;
        s.age += h;
        if (s.contact) { s.contact.age += h; if (s.contact.age > .3) s.contact = null; }
        s.flash = s.contact ? Math.max(0, 1 - s.contact.age / .3) : 0;
        const threats = candidates.get(s), target = assignments.get(s);
        s.target = target?.q.p || null;
        const angle = s.index * 2.399963229728653;
        let aimX = owner.x + Math.cos(angle) * 24, aimY = owner.y + Math.sin(angle) * 24;
        if (target) { aimX = target.aimX; aimY = target.aimY; }
        else if (s.attackTarget) { aimX = s.attackTarget.x; aimY = s.attackTarget.y; }
        else if (s.ready && Math.hypot(s.x - owner.x, s.y - owner.y) <= s.range) {
          aimX = s.flowAimX; aimY = s.flowAimY;
        }
        const ax = s.x, ay = s.y, near = Math.hypot(ax - owner.x, ay - owner.y) <= 40;
        const dx = aimX - ax, dy = aimY - ay, distance = Math.hypot(dx, dy);
        // Heading belongs to the cloud, not its target. Retargeting, waypoint
        // changes and return/reform transitions therefore keep a continuous arc.
        if (distance > .01) {
          const wanted = Math.atan2(dy, dx);
          const turn = Math.atan2(Math.sin(wanted - s.heading), Math.cos(wanted - s.heading));
          s.heading += Math.max(-config.turnRate * h, Math.min(config.turnRate * h, turn));
        }
        const alignment = distance > .01 ? Math.cos(Math.atan2(dy, dx) - s.heading) : 0;
        // Brake before tight turns/arrivals instead of orbiting a waypoint.
        const speed = Math.min(s.speed, distance * 3) * Math.max(0, alignment);
        const travel = !s.ready && near ? 0 : speed * h;
        const bx = ax + Math.cos(s.heading) * travel, by = ay + Math.sin(s.heading) * travel;
        // A stranded cloud returns physically; never teleport it when the owner moves.
        if ((!target && !s.attackTarget) || Math.hypot(bx - owner.x, by - owner.y) <= s.range) {
          s.x = bx; s.y = by;
        }
        s.vx = (s.x - ax) / h; s.vy = (s.y - ay) / h;
        s.phase = target || s.attackTarget ? 'pursue' : s.ready ? 'wander' : near ? 'recharge' : 'return';
        if (s.phase !== 'wander') { s.flowGroupId = -1; s.flowMerge = false; }
        const motion = { s, near, wasReady, interceptAt: null, attackTarget: s.attackTarget, attackAt: null };
        if (s.attackTarget) {
          const wait = Math.min(h, s.attackWait);
          const time = contactTime(s.attackTarget.x - ax - s.vx * wait, s.attackTarget.y - ay - s.vy * wait,
            -s.vx, -s.vy, config.radius + Math.max(0, s.attackTarget.r || 0));
          if (time !== null && time + wait <= h) motion.attackAt = time + wait;
        }
        motions.push(motion);
        if (s.ready) {
          for (const t of threats) {
            const time = contactTime(t.x - ax, t.y - ay, t.q.vx - s.vx, t.q.vy - s.vy, config.radius + t.q.r);
            if (time !== null && time <= h && time < t.impact) {
              contacts.push({ motion, q: t.q, time, x: ax + s.vx * time, y: ay + s.vy * time });
            }
          }
        }
      }
      // Resolve actual contacts in time order across the group. Each cloud and
      // projectile can participate once; another guardian stays fully active.
      for (let n = 0; n < group.count; n++) {
        let first = null;
        for (const contact of contacts) {
          if (contact.motion.s.ready && !removed.has(contact.q.p) && (!first || contact.time < first.time)) first = contact;
        }
        if (!first) break;
        const s = first.motion.s;
        G.Projectiles.remove(first.q.p); removed.add(first.q.p);
        s.ready = false; s.charges = 0; s.rechargeProgress = 0; s.target = null; s.attackTarget = null;
        s.phase = 'return'; first.motion.interceptAt = first.time;
        s.contact = { x: first.x, y: first.y, age: 0 };
        s.contactX = first.x; s.contactY = first.y; s.flash = 1;
      }
      // Projectile contacts always resolve first. An offensive cooldown never
      // spends an interception charge or prevents next-step defensive pursuit.
      for (const motion of motions) {
        const s = motion.s;
        if (!defending && s.ready && motion.attackAt !== null && !s.attackCooldown &&
          attack(s, motion.attackTarget, group)) {
          s.attackCooldown = Math.max(0, config.attackCooldown - (h - motion.attackAt));
          s.attackTarget = null; s.phase = 'wander';
          s.contact = { x: s.x, y: s.y, age: 0 };
          s.contactX = s.x; s.contactY = s.y; s.flash = 1;
        }
      }
      // Remember owner crossings even for projectiles blocked from acquisition.
      // A later cloud contact must never undo damage that already happened.
      for (const q of projectiles) {
        if (removed.has(q.p) || missed.has(q.p)) continue;
        const impact = contactTime(q.x + q.vx * elapsed - owner.x, q.y + q.vy * elapsed - owner.y,
          q.vx, q.vy, (owner.r || 10) + q.r);
        if (impact !== null && impact <= h) missed.add(q.p);
      }
      for (const { s, near, wasReady, interceptAt } of motions) {
        if (removed.has(s.target)) s.target = null;
        if (near && Math.hypot(s.x - owner.x, s.y - owner.y) <= 40 && !s.ready) {
          const cd = finite(owner.cdMul) ? Math.max(.03, owner.cdMul) : 1;
          const rechargeTime = wasReady && interceptAt !== null ? h - interceptAt : h;
          s.rechargeProgress += rechargeTime / Math.max(.05, config.recharge * cd);
          s.phase = 'recharge';
          if (s.rechargeProgress >= 1) {
            s.ready = true; s.charges = 1; s.rechargeProgress = 0; s.phase = 'wander';
          }
        }
        for (const point of s.trail) point.age += h;
        s.trail = s.trail.filter(point => point.age < .24);
        s.trail.push({ x: s.x, y: s.y, age: 0 });
        if (s.trail.length > 16) s.trail.shift();
      }
    }
    flowCenters(group);
    group.readyCount = group.guardians.reduce((n, s) => n + Number(s.ready), 0);
  }
  const resolve = C.resolve, clearFields = C.clearFields, drawAir = C.drawAirFields;
  C.resolve = function(dt, owner, now) { update(dt, owner); return resolve.call(this, dt, owner, now); };
  C.clearFields = function(owner) { clear(owner); return clearFields.call(this, owner); };
  C.drawAirFields = function(ctx) {
    drawAir.call(this, ctx);
    if (guard && !valid(guard)) guard = null;
    if (guard) {
      if (G.NarutoSandVFX?.drawGuardGroup) G.NarutoSandVFX.drawGuardGroup(ctx, guard);
      else for (const s of guard.guardians) G.NarutoSandVFX?.drawGuard?.(ctx, s);
    }
  };
  G.NarutoSandGuard = { state, clear, config };
})();
