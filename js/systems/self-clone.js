/* Card-created combat actors. They share skill implementations, never player controls or lives. */
(() => {
  if (G.SelfClones) return;
  const ratio = 1 / 3, list = [];
  const leash = Object.freeze({ soft: 320, resume: 220, hard: 640 });
  let nextId = 1, sceneTransitionDepth = 0;
  const isActor = actor => G.Game.state !== 'ui' && list.includes(actor) && !actor.dead && actor.hp > 0 && actor.world === G.World &&
    actor.sourceOwner === G.Game.player && !actor.sourceOwner.dead && actor.sourceOwner.hp > 0;
  const actors = () => list.filter(isActor);
  const isControlled = owner => owner === G.Game.player || isActor(owner);
  const buffFactor = (owner, key) => 1 + owner.buffs[key].n * owner.buffs[key].amount;
  const cloak = owner => G.NarutoSupport?.effects.find(f => f.owner === owner && f.world === G.World && f.mode === 'nine-tails-cloak' && f.age < f.ttl);
  function cloakFactor(owner, key) {
    const effect = cloak(owner);
    if (!effect) return 1;
    return key === 'atk' ? Math.min(1.8, effect.m.atkMul ?? 1.5) : Math.min(1.5, effect.m.speedMul ?? 1.25);
  }
  const clearFields = G.Combat.clearFields;
  function clear(owner) {
    for (const actor of [...list]) {
      if (owner && owner !== actor && owner !== actor.sourceOwner) continue;
      actor.dead = true;
      list.splice(list.indexOf(actor), 1);
      clearActorEffects(actor);
    }
  }
  function clearActorEffects(actor) {
    // This function uses the captured combat cleanup to avoid recursion. Later
    // networking wrappers still need an explicit actor expiry notification.
    G.TemariCoop?.actorRemoved?.(actor);
    clearFields.call(G.Combat, actor);
    clearActorProjectiles(actor);
  }
  function clearActorProjectiles(actor) {
    const shots = G.Projectiles.all();
    for (let i = shots.length - 1; i >= 0; i--) if (shots[i].owner === actor) shots.splice(i, 1);
  }
  function clearPath(x, y, tx, ty) {
    const steps = Math.max(1, Math.ceil(Math.hypot(tx - x, ty - y) / 4));
    for (let i = 0; i <= steps; i++) {
      const px = x + (tx - x) * i / steps, py = y + (ty - y) * i / steps;
      if (G.World.isWall(px, py) || G.World.projectileBlock(px, py, 1)) return false;
    }
    return true;
  }
  class Clone extends G.Player {
    constructor(owner) {
      super(owner.mon, {}, owner.shiny);
      this.cloneId = nextId++;
      this.sourceOwner = owner; this.world = G.World;
      this.maxHp = this.hp = owner.maxHp * ratio;
      this.r = owner.r; this.bodyH = owner.bodyH; this.anim.scale = owner.anim.scale;
      for (const key of Object.keys(this.buffs)) this.buffs[key] = { ...owner.buffs[key] };
      this.x = owner.x; this.y = owner.y; this.moveMap = new Map();
      this.item = null; this.bind = {}; this.maxMoves = owner.maxMoves;
    }
    get atk() {
      const owner = this.sourceOwner;
      return owner.atk / buffFactor(owner, 'atk') / cloakFactor(owner, 'atk') * buffFactor(this, 'atk') * cloakFactor(this, 'atk') * ratio;
    }
    get spd() {
      const owner = this.sourceOwner, liquid = G.World.liquidEffect(this.mon.types).slow || 1;
      return owner.spd / (G.NarutoTenten?.speedMultiplier(owner) ?? 1) / buffFactor(owner, 'spd') / cloakFactor(owner, 'spd') * buffFactor(this, 'spd') * cloakFactor(this, 'spd') *
        (this.inLiquid ? liquid : 1) / (owner.inLiquid ? liquid : 1) * (this.slowT > 0 ? .5 : 1) / (owner.slowT > 0 ? .5 : 1) * (G.NarutoTenten?.speedMultiplier(this) ?? 1);
    }
    get reduction() { return Math.min(.8, this.sourceOwner.dmgReduce + this.buffs.def.n * this.buffs.def.amount); }
    get regen() {
      const own = this.buffs.regen.n * this.buffs.regen.amount;
      if (!this.moves.some(m => m.id === 'naruto-gates')) return own;
      const source = this.sourceOwner.buffs.regen, inherited = G.NarutoGates?.inheritedRegen?.(this) || 0;
      return Math.max(0, inherited + (own - source.n * source.amount) * ratio * G.NarutoGates.healingMultiplier(this));
    }
    onDealt(damage) {
      if (!(damage > 0) || !Number.isFinite(damage)) return;
      this.sourceOwner.dmgDealt += damage;
      if (!this.dead && this.lifestealRate > 0) this.heal(damage * this.lifestealRate);
    }
    hurt(amount, type = null, pure = false, context = null) {
      if (!isActor(this) || this.invuln > 0 || this.frozen || !(amount > 0)) return;
      const chidori = G.NarutoChidori?.activeFor?.(this);
      if (G.NarutoLee?.isInvulnerable(this) || ['dash', 'return'].includes(chidori?.phase)) return;
      const armor = cloak(this);
      if (armor) amount *= Math.max(.5, Math.min(1, armor.m.damageTakenMul ?? .75));
      if (this.mon.dex === 30007 && G.NarutoGaara?.hurtClone) {
        return G.NarutoGaara.hurtClone(this, amount, type, pure, context,
          (amount, type, pure) => this.hurtHp(amount, type, pure));
      }
      if (this.mon.dex === 30002 && G.NarutoSharingan?.hurtClone) {
        return G.NarutoSharingan.hurtClone(this, amount, type, pure, context,
          (amount, type, pure) => this.hurtHp(amount, type, pure));
      }
      return this.hurtHp(amount, type, pure);
    }
    hurtHp(amount, type, pure) {
      const typed = type ? amount * G.Types.mult(type, this.mon.types) * G.Weather.mult(type) : amount;
      const close = this.activeGroup().some(m => m.kind === 'melee') ? .75 : 1;
      const damage = pure ? Math.max(1, typed) : Math.max(1, typed * (1 - this.reduction) * close);
      this.hp = Math.max(0, this.hp - damage); this.invuln = .45; this.flash = .14;
      this.anim.play('Hurt');
      G.FX.dmgText(this.x, this.y - this.bodyH - 4, '-' + Math.round(damage), '#9feaff');
      if (this.hp <= 0) {
        this.dead = true;
        G.FX.burst(this.x, this.y - this.bodyH * .4, '#ccecff', 12, 80);
        clear(this);
      }
    }
    draw(ctx) {
      ctx.save(); ctx.globalAlpha *= .75;
      super.draw(ctx);
      ctx.restore();
      const px = 1 / (G.Camera.scale || 1), width = 42 * px;
      const x = this.x - width / 2, y = this.y - this.bodyH - 9 * px;
      const health = Math.max(0, Math.min(1, this.hp / this.maxHp)), fill = (width - 2 * px) * health;
      ctx.fillStyle = '#101728'; ctx.fillRect(x, y, width, 7 * px);
      ctx.fillStyle = '#582636'; ctx.fillRect(x + px, y + px, width - 2 * px, 5 * px);
      ctx.fillStyle = '#ff6579'; ctx.fillRect(x + px, y + px, fill, 5 * px);
      ctx.fillStyle = '#ffb6c1'; ctx.fillRect(x + px, y + px, fill, px);
    }
  }
  function mirror(actor) {
    const owner = actor.sourceOwner;
    actor.level = owner.level; actor.cdMul = owner.cdMul; actor.critChance = owner.critChance;
    actor.quantityPicks = owner.quantityPicks; actor.quantityBonus = owner.quantityBonus;
    actor.giantPicks = owner.giantPicks; actor.damageSplashPicks = owner.damageSplashPicks;
    actor.ninjaToolBouncePicks = owner.ninjaToolBouncePicks || 0;
    actor.percentHealthDamage = (owner.percentHealthDamage || 0) * ratio;
    actor.lifestealRate = owner.lifestealRate || 0; actor.frozen = owner.frozen;
    const moves = owner.moves;
    for (const move of moves) {
      let copy = actor.moveMap.get(move.id);
      if (!copy) { copy = { ...move, t: 0, dealt: 0, castAt: 0 }; actor.moveMap.set(move.id, copy); }
      const timers = { t: copy.t, dealt: copy.dealt, castAt: copy.castAt };
      Object.assign(copy, move, timers);
      if (copy.burn) copy.burn *= ratio;
      if (copy.poison) copy.poison *= ratio;
    }
    actor.moves = moves.map(m => actor.moveMap.get(m.id));
    const selected = owner.activeGroup().map(m => m.id).join('|');
    const previous = actor.activeGroup().map(m => m.id).join('|');
    if (selected !== previous || !actor.slots.length) {
      actor.slots = owner.slots.map(group => group.map(m => actor.moveMap.get(m.id)).filter(Boolean)).filter(group => group.length);
      const index = actor.slots.findIndex(group => group.map(m => m.id).join('|') === selected);
      actor.active = -1;
      if (index >= 0) actor.setActive(index);
    }
  }
  function summon(owner) {
    if (owner !== G.Game.player || owner.dead || !(owner.hp > 0)) return null;
    const actor = new Clone(owner);
    placeNearOwner(actor);
    list.push(actor); mirror(actor);
    G.FX.burst(actor.x, actor.y - actor.bodyH * .4, '#ccecff', 12, 80);
    return actor;
  }
  function placeNearOwner(actor) {
    const owner = actor.sourceOwner, siblings = actors().filter(other => other !== actor);
    let fallback = null;
    actor.x = owner.x; actor.y = owner.y;
    for (let ring = 1; ring <= 6; ring++) for (let i = 0; i < 12; i++) {
      const angle = (i + actor.cloneId * .5) * Math.PI / 6, radius = owner.r + actor.r + 12 * ring;
      const x = owner.x + Math.cos(angle) * radius, y = owner.y + Math.sin(angle) * radius;
      if (!G.World.isFree(x, y, actor.r, true) || !clearPath(owner.x, owner.y, x, y)) continue;
      fallback ||= { x, y };
      if (siblings.some(other => Math.hypot(x - other.x, y - other.y) < actor.r + other.r + 6)) continue;
      actor.x = x; actor.y = y; return;
    }
    if (fallback) { actor.x = fallback.x; actor.y = fallback.y; }
  }
  function walk(actor, vx, vy, dt) {
    const speed = Math.hypot(vx, vy), limit = Math.max(0, actor.spd);
    if (!(speed > 0) || !(dt > 0)) return false;
    const scale = Math.min(1, limit / speed), dx = vx * scale * dt, dy = vy * scale * dt;
    const steps = Math.max(1, Math.ceil(Math.hypot(dx, dy) / 4));
    let moved = false;
    for (let i = 0; i < steps; i++) {
      const x = actor.x, y = actor.y, maxStep = Math.hypot(dx, dy) / steps;
      actor.x += dx / steps; actor.y += dy / steps;
      G.World.collide(actor);
      // Terrain may push an already crowded actor farther than its step budget.
      // Keep separation gradual; try each axis if the full step is obstructed.
      if (!G.World.isFree(actor.x, actor.y, actor.r, true) || Math.hypot(actor.x - x, actor.y - y) > maxStep + 1e-6) {
        actor.x = x; actor.y = y;
        if (G.World.isFree(x + dx / steps, y, actor.r, true)) actor.x += dx / steps;
        if (G.World.isFree(actor.x, y + dy / steps, actor.r, true)) actor.y += dy / steps;
      }
      moved ||= Math.hypot(actor.x - x, actor.y - y) > 1e-6;
    }
    return moved;
  }
  function separation(actor, crowd) {
    let x = 0, y = 0;
    for (const other of crowd) {
      if (other.actor === actor) continue;
      const gap = actor.r + other.r + 8, dx = actor.x - other.x, dy = actor.y - other.y;
      const distance = Math.hypot(dx, dy);
      if (distance >= gap) continue;
      // Each identical-position pair uses the same axis with opposite signs.
      const id = other.actor.cloneId || 0, low = Math.min(actor.cloneId, id), high = Math.max(actor.cloneId, id);
      const angle = low * 2.399963229728653 + high * 1.61803398875;
      const sign = actor.cloneId > id ? 1 : -1, strength = (gap - distance) / gap;
      x += (distance > 1e-6 ? dx / distance : Math.cos(angle) * sign) * strength;
      y += (distance > 1e-6 ? dy / distance : Math.sin(angle) * sign) * strength;
    }
    return { x, y };
  }
  // Only native Rift travel may preserve actors while clearing scene effects.
  function withSceneTransition(travel) {
    for (const actor of [...list]) if (!isActor(actor)) clear(actor);
    const survivors = actors();
    sceneTransitionDepth++;
    try { return travel(); }
    finally {
      sceneTransitionDepth--;
      for (const actor of survivors) {
        if (!list.includes(actor)) continue;
        if (actor.dead || !(actor.hp > 0) || actor.sourceOwner !== G.Game.player ||
          actor.sourceOwner.dead || !(actor.sourceOwner.hp > 0)) { clear(actor); continue; }
        actor.world = G.World; actor.target = null;
        placeNearOwner(actor); mirror(actor);
      }
    }
  }
  function update(dt) {
    const crowd = [G.Game.player, ...actors()].filter(Boolean).map(actor => ({ actor, x: actor.x, y: actor.y, r: actor.r }));
    const assignments = new Map();
    for (const { actor } of crowd) if (actor.cloneId && actor.target && !actor.target.dead && actor.target.hp > 0)
      assignments.set(actor.target, (assignments.get(actor.target) || 0) + 1);
    for (const actor of [...list]) {
      if (!isActor(actor)) { clear(actor); continue; }
      mirror(actor);
      if (actor.frozen) continue;
      const owner = actor.sourceOwner;
      let ownerDistance = Math.hypot(actor.x - owner.x, actor.y - owner.y);
      if (ownerDistance > leash.hard) {
        const abandoned = actor.target;
        if (abandoned && assignments.has(abandoned)) assignments.set(abandoned, Math.max(0, assignments.get(abandoned) - 1));
        // Cancel only position-owning actions. Defensive/passive state, health,
        // buffs and shield charge must survive an emergency reposition.
        G.NarutoChidori?.clear(actor);
        G.NarutoLee?.clear(actor);
        G.NarutoFireball?.clear(actor);
        clearActorProjectiles(actor);
        actor.target = null;
        placeNearOwner(actor);
        ownerDistance = Math.hypot(actor.x - owner.x, actor.y - owner.y);
      }
      actor.returningToOwner = ownerDistance > leash.soft || (actor.returningToOwner && ownerDistance > leash.resume);
      actor.invuln = Math.max(0, actor.invuln - dt); actor.flash = Math.max(0, actor.flash - dt);
      actor.attackFace = Math.max(0, actor.attackFace - dt);
      for (const buff of Object.values(actor.buffs)) if (buff.n > 0 && (buff.t -= dt) <= 0) buff.n = 0;
      actor.slowT = Math.max(0, actor.slowT - dt);
      if (actor.regen > 0) actor.hp = Math.min(actor.maxHp, actor.hp + actor.regen * dt);
      actor.inLiquid = G.World.isLiquid(actor.x, actor.y);
      if (actor.inLiquid) {
        const effect = G.World.liquidEffect(actor.mon.types);
        if (effect.dmg && (actor.lavaTick -= dt) <= 0) {
          actor.lavaTick = effect.every; actor.invuln = 0;
          actor.hurt(Math.max(effect.flat, actor.maxHp * effect.dmg * .5));
          if (!isActor(actor)) continue;
        }
      } else actor.lavaTick = 0;
      const busy = G.NarutoChidori?.activeFor?.(actor) || G.NarutoLee?.activeFor?.(actor) || G.NarutoFireball?.activeFor?.(actor);
      if (!busy) {
        const previous = actor.target;
        if (previous && assignments.has(previous)) assignments.set(previous, Math.max(0, assignments.get(previous) - 1));
        const candidates = actor.returningToOwner ? [] : G.EnemyMgr.queryCircle(actor.x, actor.y, 520).filter(e =>
          !e.dead && e.hp > 0 && Math.hypot(e.x - owner.x, e.y - owner.y) <= leash.soft);
        // Prefer an unclaimed foe; retain this actor's target on equal occupancy
        // so distance changes do not make clones swap targets every frame.
        candidates.sort((a, b) => (assignments.get(a) || 0) - (assignments.get(b) || 0) ||
          Number(b === previous) - Number(a === previous) ||
          Math.hypot(a.x - actor.x, a.y - actor.y) - Math.hypot(b.x - actor.x, b.y - actor.y));
        actor.target = candidates.find(enemy => clearPath(actor.x, actor.y, enemy.x, enemy.y)) || null;
        if (actor.target) assignments.set(actor.target, (assignments.get(actor.target) || 0) + 1);
      }
      let moving = false;
      if (!busy) {
        const move = actor.activeMove() || actor.moves.find(m => ['naruto-gaara','naruto-temari'].includes(m.id));
        const mastery = actor.moves.find(m => m.digiMode === 'temari-mastery');
        const masteryReach = move?.id === 'naruto-temari' && mastery ? [40,70,110,160,220][Math.max(0,Math.min(4,mastery.lvl-1))] : 0;
        const range = (move?.range || move?.radius || 100) + masteryReach, target = actor.target;
        const angle = actor.cloneId * 2.4, gap = owner.r + actor.r + 28;
        let x = owner.x + Math.cos(angle) * gap, y = owner.y + Math.sin(angle) * gap, stop = 14;
        if (target && !actor.returningToOwner) {
          const reach = Math.max(actor.r + (target.r || 8) + 6, Math.min(180, range * .7));
          let approachX = target.x + Math.cos(angle) * reach, approachY = target.y + Math.sin(angle) * reach;
          const fromOwner = Math.hypot(approachX - owner.x, approachY - owner.y), edge = leash.soft - 20;
          if (fromOwner > edge) {
            approachX = owner.x + (approachX - owner.x) * edge / fromOwner;
            approachY = owner.y + (approachY - owner.y) * edge / fromOwner;
          }
          if (G.World.isFree(approachX, approachY, actor.r, true) && clearPath(actor.x, actor.y, approachX, approachY)) {
            x = approachX; y = approachY; stop = 5;
          } else { x = target.x; y = target.y; stop = reach; }
        }
        const dx = x - actor.x, dy = y - actor.y, distance = Math.hypot(dx, dy);
        const speed = Math.min(actor.spd, Math.max(0, distance - stop) / dt), repel = separation(actor, crowd);
        const vx = (distance > 0 ? dx / distance * speed : 0) + repel.x * actor.spd;
        const vy = (distance > 0 ? dy / distance * speed : 0) + repel.y * actor.spd;
        moving = walk(actor, vx, vy, dt);
      }

      if (actor.target) actor.aim = Math.atan2(actor.target.y - actor.y, actor.target.x - actor.x);
      actor.anim.dir = G.Sprites.dirFromAngle(actor.aim);
      actor.anim.loop(moving ? 'Walk' : 'Idle', moving ? actor.spd / 110 : 1);
      if (!actor.returningToOwner || busy) G.Combat.tick(dt, actor, G.Game.st.time);
      actor.anim.update(dt);
    }
  }
  function contactTime(shot, actor) {
    const x = shot.px ?? shot.x, y = shot.py ?? shot.y, dx = shot.x - x, dy = shot.y - y;
    const fx = x - actor.x, fy = y - actor.y, r = (shot.r || 0) + actor.r;
    const c = fx * fx + fy * fy - r * r;
    if (c <= 0) return 0;
    const a = dx * dx + dy * dy, b = 2 * (fx * dx + fy * dy), d = b * b - 4 * a * c;
    if (!a || d < 0) return Infinity;
    const t = (-b - Math.sqrt(d)) / (2 * a);
    return t >= 0 && t <= 1 ? t : Infinity;
  }
  const resolve = G.Combat.resolve, updateFields = G.Combat.updateFields;
  G.Combat.resolve = function(dt, owner, now) {
    if (G.Game.state === 'playing') {
      G.NarutoSandGuard?.updateClones(dt, owner);
      const shots = G.Projectiles.all(), live = actors().filter(a => a.sourceOwner === owner && !a.frozen);
      for (let i = shots.length - 1; i >= 0; i--) {
        const shot = shots[i];
        if (shot.friendly !== false || G.World.projectileBlock(shot.x, shot.y, shot.r)) continue;
        let first = null, time = owner ? contactTime(shot, owner) : Infinity;
        for (const actor of live) {
          if (!isActor(actor)) continue;
          const t = contactTime(shot, actor);
          if (t < time && clearPath(shot.px ?? shot.x, shot.py ?? shot.y, actor.x, actor.y)) { first = actor; time = t; }
        }
        if (first) { shots.splice(i, 1); first.hurt(shot.dmg, shot.mtype); i = Math.min(i, shots.length); }
      }
      for (const actor of live) for (const enemy of G.EnemyMgr.queryCircle(actor.x, actor.y, actor.r + 40)) {
        if (!isActor(actor)) break;
        if (enemy.dead || enemy.touchCd > 0 || enemy.behavior === 'thief' || G.NarutoLee?.bound?.(enemy) || Math.hypot(enemy.x - actor.x, enemy.y - actor.y) > actor.r + enemy.r) continue;
        enemy.touchCd = .55; enemy.strike(actor); actor.hurt(enemy.dmg, enemy.atkType);
      }
    }
    return resolve.call(this, dt, owner, now);
  };
  G.Combat.updateFields = function(dt) {
    if (G.Game.state === 'playing' && dt > 0) update(dt);
    return updateFields.call(this, dt);
  };
  G.Combat.clearFields = function(owner) { const result = clearFields.call(this, owner); if (!sceneTransitionDepth) clear(owner); return result; };
  const enemyUpdate = G.Enemy.prototype.update;
  G.Enemy.prototype.update = function(dt, player) {
    let target = player, distance = player ? Math.hypot(this.x - player.x, this.y - player.y) : Infinity;
    if (!this.dead && !this.remote && this.behavior !== 'thief') for (const actor of actors()) {
      const d = Math.hypot(this.x - actor.x, this.y - actor.y);
      if (d < distance && clearPath(this.x, this.y, actor.x, actor.y)) { target = actor; distance = d; }
    }
    return enemyUpdate.call(this, dt, target);
  };
  G.LevelUp.STATS.push({ id: 'selfClone', icon: 'selfClone', title: '分身之術',
    desc: '召喚 1 個自身分身，最大生命為召喚時玩家的 1/3、傷害係數 1/3。跟隨玩家，使用目前選中的技能並繼承已學常駐／被動效果；技能升級同步，冷卻與受傷各自計算。死亡即消失，不自動重生。可重複選取，僅限本局。',
    apply: summon });
  G.SelfClones = { ratio, leash, summon, actors, isActor, isControlled, clear, withSceneTransition,
    drawables: cam => actors().filter(a => cam.sees(a.x, a.y, a.bodyH + 40)) };
})();
