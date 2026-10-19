/* Local Naruto shadow clones: temporary combat actors, never players or saves. */
(() => {
  if (G.NarutoClones) return;
  const actors = [], smoke = [], C = G.Combat, TAU = Math.PI * 2;
  // Balance knobs: UI descriptions, upgrades and actor limits all read this object.
  const config = Object.freeze({ counts: Object.freeze([8,16,24,32,40]), cooldown: 4,
    duration: 6, sealDuration: .4, punchDamage: 8, punchCooldown: .65 });
  const summons = [];
  let serial = 0;
  const valid = a => a.owner === G.Game.player && !a.owner.dead && a.owner.hp > 0 && a.world === G.World;
  const living = owner => actors.filter(a => !a.dead && a.owner === owner && valid(a));
  const limitOf = (move,owner=G.Game.player) => config.counts[Math.min(config.counts.length-1,Math.max(0,(move.lvl||1)-1))]+(move.quantityBonusAtCast??G.Quantity?.bonus(owner)??0);
  function formation(index) {
    let ring=0,slots=8;
    while(index>=slots){index-=slots;ring++;slots=8+ring*4;}
    const angle=index*TAU/slots+ring*.25,radius=90+ring*32;
    return {x:Math.cos(angle)*radius,y:Math.sin(angle)*radius*.87};
  }
  const mimicIds = new Set(['naruto-naruto', 'naruto-rasenshuriken', 'naruto-kunai', 'naruto-shuriken']);
  const selectedTechnique = owner => (owner.activeGroup?.() || []).find(m => mimicIds.has(m.id) && owner.moves?.some(learned => learned === m || learned.id === m.id)) || null;
  const canCast = (owner,move) => owner===G.Game.player&&!owner.dead&&owner.hp>0&&owner.mon?.dex===30001&&living(owner).length<limitOf(move,owner)&&!summons.some(s=>s.owner===owner);
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
    for (let i = summons.length - 1; i >= 0; i--) if (!owner || summons[i].owner === owner) summons.splice(i, 1);
    clearProjectiles(owner);
    // Smoke belongs to this local effect layer and must not survive a run reset.
    smoke.length = 0;
  }
  function clearProjectiles(owner) {
    const list = G.Projectiles.all();
    for (let i = list.length - 1; i >= 0; i--) if (list[i].narutoClone && (!owner || list[i].owner === owner)) list.splice(i, 1);
  }
  function cast(owner, move) {
    if (owner !== G.Game.player || owner.dead || owner.hp <= 0 || owner.mon?.dex !== 30001) return false;
    const lvl = move.lvl || 1, limit = limitOf(move,owner);
    let count = living(owner).length, spawned = false;
    const occupied=new Set(living(owner).map(a=>a.formationIndex));
    for(let n=0;n<Math.max(96,limit*12)&&count<limit;n++) {
      const angle=n*2.399963229728653,radius=56+18*Math.sqrt(n);
      const x = owner.x + Math.cos(angle) * radius, y = owner.y + Math.sin(angle) * radius;
      if (!G.World.isFree(x, y, 10, true) || !clearPath(owner.x, owner.y, x, y, 10) || living(owner).some(a => Math.hypot(a.x - x, a.y - y) < 25)) continue;
      let formationIndex=0;while(occupied.has(formationIndex))formationIndex++;occupied.add(formationIndex);
      const a = { id: ++serial, formationIndex, owner, world: G.World, x, y, r: 10, age: 0, ttl: move.cloneDuration || config.duration,
        lvl, dmg: Number.isFinite(move.dmg) ? move.dmg : config.punchDamage, punchCd: move.punchCd || config.punchCooldown,
        cd: .16 + count % 8 * .08, anim: new G.Sprites.Animator(30001, 1), target: null, dead: false, comboT: 0,
        cloneTechniqueCdMul: move.cloneTechniqueCdMul ?? 1, cloneTechniqueDamageMul: move.cloneTechniqueDamageMul ?? 1,
        // Retain one cooldown per technique across slot switches; phase spreads eight casts out.
        cooldowns: new Map([...mimicIds].map(id => [id, .16 + count % 8 * .08])), mimickedId: null };
      a.anim.dir = owner.anim.dir; actors.push(a); puff(a); count++; spawned = true;
    }
    return spawned;
  }
  function beginCast(owner, move) {
    if (!canCast(owner,move)) return false;
    // Reject blocked casts before consuming the full cooldown.
    if (!G.World.isFree(owner.x,owner.y,10,true)) return false;
    const duration=config.sealDuration;
    const meta=G.Sprites.animMeta(30001,'Charge');
    owner.anim.play('Charge',{speed:meta.d.reduce((sum,n)=>sum+n,0)/60/duration});
    summons.push({owner,world:G.World,move:{...move},t:0,duration});
    return true;
  }
  function hit(a, enemy, base, type, knock = 12) {
    if (enemy.dead || !valid(a)) return;
    const typeK = G.Types.mult(type, enemy.types), crit = a.owner.critChance > 0 && Math.random() < a.owner.critChance;
    const dmg = base * typeK * G.Weather.mult(type) * (crit ? 1.5 : 1);
    enemy.hurt(dmg, '#a9dcff', enemy.x - a.x, enemy.y - a.y, knock, crit ? 'crit' : G.Types.label(typeK), a.owner);
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
      for (let i=summons.length-1;i>=0;i--) {
        const s=summons[i];
        if (!valid(s)) { summons.splice(i,1); continue; }
        s.t+=sub;
        if (s.t+1e-9>=s.duration) {
          summons.splice(i,1);
          if (!cast(s.owner,s.move)) {
            const learned=s.owner.moves.find(m=>m.id===s.move.id);
            if (learned) learned.t=.25;
          }
        }
      }
      const claimed = new Set();
      const projectiles = G.Projectiles.all();
      for (let i = projectiles.length - 1; i >= 0; i--) {
        const p = projectiles[i];
        if (p.narutoClone && (p.owner !== G.Game.player || p.owner.dead || p.owner.hp <= 0)) projectiles.splice(i, 1);
      }
      for (const a of actors) {
        if (a.dead) continue;
        if (!valid(a)) { a.dead = true; continue; }
        a.age += sub; a.cd -= sub; a.comboT = Math.max(0, a.comboT - sub);
        for (const [id, remaining] of a.cooldowns) a.cooldowns.set(id, Math.max(0, remaining - sub));
        if (a.age >= a.ttl) { dismiss(a); continue; }
        const technique = selectedTechnique(a.owner);
        a.mimickedId = technique?.id || null;
        const range = technique?.id==='naruto-naruto'?280:technique?Math.min(600,technique.range||technique.speed*technique.life||280):280;
        const tethered = distance(a, a.owner) <= 420;
        const enemies = tethered ? nearby(a.owner.x, a.owner.y, technique ? 420 : 240).filter(e => distance(a, e) <= range) : [];
        enemies.sort((b, c) => (claimed.has(b) - claimed.has(c)) || distance(a, b) - distance(a, c));
        a.target = enemies.find(e => clearPath(a.x, a.y, e.x, e.y)) || null;
        let moving = false;
        if (a.target) {
          const e = a.target; claimed.add(e);
          const reach = 35 + (e.r || 0), rasengan = technique?.id === 'naruto-naruto';
          if ((!technique || rasengan) && distance(a, e) > reach) moving = moveToward(a, e.x, e.y, rasengan && a.cooldowns.get(technique.id) <= 0 ? 400 : Math.max(125, a.owner.spd || 0), sub);
          else {
            a.anim.dir = G.Sprites.dirFromAngle(Math.atan2(e.y - a.y, e.x - a.x));
            if (technique && a.cooldowns.get(technique.id) <= 0 && clearPath(a.x, a.y, e.x, e.y)) {
              const aim = Math.atan2(e.y - a.y, e.x - a.x);
              if (rasengan) {
                a.anim.play('Attack'); a.comboT = .4; a.comboAim = aim;
                hit(a, e, technique.dmg * a.owner.atk * a.cloneTechniqueDamageMul, technique.type || 'fighting', technique.knock || 28);
                G.FX.beam(a.x, a.y - G.LIFT, aim, distance(a, e), 8, '#83dcff', { pal: 'water' });
              } else if (G.DigimonSkills?.fireFrom) {
                const shots = G.DigimonSkills.fireFrom(a.owner, technique, a.x, a.y, aim, a.cloneTechniqueDamageMul) || [];
                for (const p of shots) p.narutoClone = true;
                a.anim.play('Shoot');
              }
              a.cooldowns.set(technique.id, Math.max(.1, (technique.cd || 1) * a.cloneTechniqueCdMul));
            } else if (!technique && a.cd <= 0 && clearPath(a.x, a.y, e.x, e.y)) {
              a.cd = a.punchCd; a.anim.play('Attack', { speed: 1.3 });
              hit(a, e, a.dmg * a.owner.atk, 'fighting');
              G.FX.spark(e.x, e.y - (e.bodyH || 30) * .5, '#a9dcff', e.x - a.x, e.y - a.y, 3);
            }
          }
        } else {
          const spot=formation(a.formationIndex),x=a.owner.x+spot.x,y=a.owner.y+spot.y;
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
  // Legacy player-cast hook stays inert; clones cast their selected technique autonomously.
  function combo() { return 0; }
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
        const aim = a.comboAim || 0, x = a.x + Math.cos(aim) * 18, y = a.y - G.LIFT + Math.sin(aim) * 12;
        ctx.save(); ctx.globalAlpha = Math.min(.85, a.comboT * 3); ctx.translate(x, y);
        ctx.fillStyle = '#b8f3ff'; ctx.beginPath(); ctx.arc(0, 0, 7, 0, TAU); ctx.fill();
        ctx.strokeStyle = '#3fafff'; ctx.lineWidth = 2; ctx.rotate(a.comboT * 22);
        ctx.beginPath(); ctx.ellipse(0, 0, 10, 4, 0, 0, TAU); ctx.ellipse(0, 0, 4, 10, 0, 0, TAU); ctx.stroke(); ctx.restore();
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
  const levelUp=G.Moves.levelUp;
  G.Moves.levelUp=function(move){
    const upgraded=levelUp(move),owner=G.Game.player;
    if(upgraded&&move.id==='naruto-shadow-clones'&&owner?.moves.includes(move)&&cast(owner,move))move.t=move.cd*owner.cdMul;
    return upgraded;
  };
  G.NarutoClones = { config, cast, beginCast, canCast, limitOf, update, draw, clear, combo, get actors() { return actors; } };
})();
