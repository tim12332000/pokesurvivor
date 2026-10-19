/* Local Digimon skill layer. Loaded after systems/combat.js and entities/vfx.js. */
(() => {
  const C = G.Combat;
  if (!C || !G.VFX || C._digimonSkillEngineInstalled) return;
  C._digimonSkillEngineInstalled = true;
  const vanilla = { tick: C.tick, resolve: C.resolve, updateFields: C.updateFields,
    ground: C.drawGroundFields, air: C.drawAirFields, clear: C.clearFields };
  const fields = [], bombs = new Set();
  const CAP = 120, TAU = Math.PI * 2;
  const cloneMove = m => Object.assign({}, m, { digiVis: m.digiVis && Object.assign({}, m.digiVis), secondary: m.secondary && Object.assign({}, m.secondary) });
  const color = m => G.VFX.PAL[m.digiVis?.pal]?.[2] || G.U.TYPE_COLOR[m.type] || '#fff';
  const vis = m => Object.assign({}, G.VFX.forMove(m), m.digiVis || {});
  const valid = f => f.owner && f.owner === G.Game.player && !f.owner.dead && f.owner.hp > 0 && f.world === G.World;
  const cap = () => { const limit=CAP*(1+(G.Quantity?.bonus(G.Game.player)||0)); while (fields.length > limit) fields.shift(); };
  const targets = (x, y, r) => [...new Set(G.EnemyMgr.queryCircle(x, y, r))].filter(e => !e.dead);
  const techniqueFor = mode => [G.NarutoSupport,G.NarutoOffense,G.NarutoChidori].find(api=>api?.supports(mode));
  function hit(pl, m, e, base, dx, dy, knock = m.knock || 0) {
    if (!e || e.dead) return 0;
    const k = G.Types.mult(m.type, e.types) * G.Weather.mult(m.type), crit = pl.critChance > 0 && Math.random() < pl.critChance;
    const dmg = base * k * (crit ? 1.5 : 1) * (m.narutoSkill ? G.NarutoSupport?.precisionMultiplier(pl,e)||1 : 1);
    e.hurt(dmg, color(m), dx, dy, knock, crit ? 'crit' : G.Types.label(G.Types.mult(m.type, e.types)));
    pl.onDealt(dmg); pl.dmgDealt += dmg;
    if (m.burn) e.applyBurn(m.burn); if (m.poison) e.applyPoison(m.poison); if (m.slow) e.applySlow(m.slow);
    return dmg;
  }
  function propHits(pl, m, x, y, r, base = m.dmg * pl.atk, test = null) {
    for (const p of G.World.propsInCircle(x, y, r)) if (!test || test(p)) G.World.damageProp(p, base, color(m));
  }
  function area(pl, m, x, y, r, ratio = 1) {
    let dealt = 0;
    for (const e of targets(x, y, r)) dealt += hit(pl, m, e, m.dmg * pl.atk * ratio, e.x - x, e.y - y);
    propHits(pl, m, x, y, r, m.dmg * pl.atk * ratio);
    return dealt;
  }
  function projectile(pl, m, a, ratio = 1, explosive = false, origin = pl) {
    if(m.id==='naruto-fireball'&&pl.dex===30002&&origin===pl&&G.NarutoFireball) {
      const mouth=G.NarutoFireball.origin(pl,a),dx=mouth.x-pl.x,dy=mouth.y-pl.y,len=Math.hypot(dx,dy);
      origin={x:pl.x,y:pl.y};
      // Check the mouth offset as swept travel too: a nearby wall/prop cannot be skipped.
      for(let d=4;d<len+4;d+=4) {
        const t=Math.min(1,d/len),x=pl.x+dx*t,y=pl.y+dy*t;
        if(G.World.projectileBlock(x,y,1)){origin.x-=Math.cos(a)*3;origin.y-=Math.sin(a)*3;break;}
        origin={x,y};
      }
    }
    const v = vis(m), p = G.Projectiles.spawn({ x: origin.x + Math.cos(a) * 3, y: origin.y + Math.sin(a) * 3,
      vx: Math.cos(a) * m.speed, vy: Math.sin(a) * m.speed, dmg: m.dmg * pl.atk * ratio * (explosive ? .2 : 1),
      r: m.size, life: m.life, pierce: m.pierce | 0, color: color(m), homing: m.homing || 0,
      hits: new Set(), vis: v, owner: pl, mtype: m.type, burn: m.burn || 0, poison: m.poison || 0,
      slow: m.slow || 0, knock: m.knock || 0, digiBomb: explosive ? { m, owner: pl, r: m.blastRadius || m.radius } : null });
    if(m.fumaReturn)Object.assign(p,{fumaReturn:true,boom:m.boom,bsp:m.speed*1.1,fumaPierce:p.pierce});
    if(m.fireballGrowth) {
      p.fireballGrowth={...m.fireballGrowth,travelled:0,baseRadius:p.r,baseScale:v.projScale||1};
      p.r*=m.fireballGrowth.startRatio;
      p.vis.projScale=p.fireballGrowth.baseScale*m.fireballGrowth.startRatio;
    }
    if (explosive) { bombs.add(p); cap(); }
    return p;
  }
  function fireFrom(owner,move,x,y,aim,damageScale=1) {
    if(owner!==G.Game.player||owner.dead||owner.hp<=0||![x,y,aim,damageScale].every(Number.isFinite))return [];
    if(!['naruto-rasenshuriken','naruto-kunai','naruto-shuriken'].includes(move.id))return [];
    const m=cloneMove(G.Quantity?.snapshot(owner,move)||move);m.dmg*=Math.max(0,damageScale);
    const count=Math.max(1,m.count|0),out=[];
    for(let i=0;i<count;i++) {
      const angle=m.digiMode==='nova'?i*TAU/count:aim+(count===1?0:(i/(count-1)-.5)*(m.arc||0));
      const p=projectile(owner,m,angle,1,!!m.blastRadius,{x,y});p.narutoClone=true;out.push(p);
    }
    return out;
  }
  function line(pl, m, x, y, a, len, width, ratio = 1) {
    const ca = Math.cos(a), sa = Math.sin(a);
    for (let d = 8; d <= len; d += 8) if (G.World.isWall(x + ca * d, y + sa * d)) { len = d; break; }
    G.FX.beam(x, y - G.LIFT, a, len, width, color(m), vis(m));
    const mx = x + ca * len / 2, my = y + sa * len / 2;
    for (const e of targets(mx, my, len / 2 + width)) {
      const px = e.x - x, py = e.y - y, along = px * ca + py * sa;
      if (along >= -e.r && along <= len + e.r && Math.abs(-px * sa + py * ca) <= width / 2 + e.r)
        hit(pl, m, e, m.dmg * pl.atk * ratio, ca, sa);
    }
    const onBeam = p => { const px = p.x - x, py = p.y - y, along = px * ca + py * sa; return along >= -p.r && along <= len + p.r && Math.abs(-px * sa + py * ca) <= width / 2 + p.r; };
    propHits(pl, m, mx, my, len / 2 + width, m.dmg * pl.atk * ratio, onBeam);
  }
  function sweep(pl, m, x, y, aim, radius, arc, ratio = 1, hand = 0) {
    G.FX.slash(x, y - G.LIFT * .5, aim, radius, arc, color(m), vis(m));
    if(m.narutoSkill&&vis(m).melee==='naruto-lion') {
      const ca=Math.cos(aim),sa=Math.sin(aim),side=hand||1;
      G.FX.sp('naruto-lion',vis(m).pal,x+ca*27-sa*side*12,y-G.LIFT+sa*27+ca*side*12,
        {vx:ca*110,vy:sa*110,life:.24,scale:1.4,angle:aim,fade:false});
    }
    for (const e of targets(x, y, radius)) {
      const a = Math.atan2(e.y - y, e.x - x);
      if (Math.abs(((a - aim + Math.PI * 3) % TAU) - Math.PI) <= arc / 2)
        hit(pl, m, e, m.dmg * pl.atk * ratio, e.x - x, e.y - y);
    }
    propHits(pl, m, x, y, radius, m.dmg * pl.atk * ratio, p => Math.abs(((Math.atan2(p.y - y, p.x - x) - aim + Math.PI * 3) % TAU) - Math.PI) <= arc / 2);
  }
  function field(pl, m, kind, o = {}) { fields.push(Object.assign({ kind, owner: pl, world: G.World, m: cloneMove(m), x: pl.x, y: pl.y, t: 0, col: color(m), v: vis(m) }, o)); cap(); }
  function inSand(f, e, front = f.m.range) {
    const dx=e.x-f.x,dy=e.y-f.y,ca=Math.cos(f.aim),sa=Math.sin(f.aim);
    const along=dx*ca+dy*sa,across=-dx*sa+dy*ca;
    const radius=Number.isFinite(e.r)?e.r:0;
    if(along<0||along>front+radius||Math.abs(across)>f.m.width*.5*(.4+.6*Math.min(1,along/f.m.range))+radius)return false;
    const distance=Math.hypot(dx,dy);
    for(let d=8;d<=distance;d+=8)if(G.World.isWall(f.x+dx*d/distance,f.y+dy*d/distance))return false;
    return true;
  }
  function sandTargets(f, front = f.m.range) {
    const len=f.m.range;
    return [...new Set(targets(f.x+Math.cos(f.aim)*len*.5,f.y+Math.sin(f.aim)*len*.5,len*.5+f.m.width))].filter(e=>inSand(f,e,front));
  }
  function updateSand(f) {
    const burst=f.t>=f.burstTime;
    f.phase=burst?'burst':f.t>=f.flowDuration?'bind':'flow';
    if(!burst) {
      const front=f.m.range*Math.min(1,f.t/f.flowDuration);
      for(const e of sandTargets(f,front)) {
        if(!f.hits.has(e)) {
          f.hits.add(e);f.victims.push(e);
          hit(f.owner,f.m,e,f.m.dmg*f.owner.atk*.25,e.x-f.x,e.y-f.y,0);
        }
      }
      for(const e of f.victims)if(!e.dead)e.applySlow(e.boss ? .35 : .95,.2);
    } else if(!f.crushed) {
      f.crushed=true;
      // The whole swept area erupts, including enemies entering after the wave.
      for(const e of sandTargets(f))hit(f.owner,f.m,e,f.m.dmg*f.owner.atk*.75,e.x-f.x,e.y-f.y,f.m.knock);
      const ca=Math.cos(f.aim),sa=Math.sin(f.aim);
      propHits(f.owner,f.m,f.x+ca*f.m.range*.5,f.y+sa*f.m.range*.5,f.m.range*.5+f.m.width,
        f.m.dmg*f.owner.atk,p=>inSand(f,p));
      G.Audio.sfx('hit');
    }
  }
  function emit(pl, m, aim = pl.aim) {
    const mode = m.digiMode, a = aim, n = Math.max(1, m.count | 0), arc = m.arc || .8;
    if (mode === 'shot') for (let i = 0; i < n; i++) projectile(pl, m, a + (n === 1 ? 0 : (i / (n - 1) - .5) * arc), 1, !!m.blastRadius);
    else if (mode === 'nova') for (let i = 0; i < n; i++) projectile(pl, m, i * TAU / n, 1, !!m.blastRadius);
    else if (mode === 'melee') { for (let i = 0; i < n; i++) { const f = { kind: 'combo', owner: pl, world: G.World, m: cloneMove(m), t: 0, delay: i * (m.burstInterval || .12), x: pl.x, y: pl.y, aim: a, col: color(m), v: vis(m) }; fields.push(f); } cap(); }
    else if (mode === 'beam') line(pl, m, pl.x, pl.y, a, m.radius, m.width);
    else if (mode === 'dash') {
      let len = 0; for (let d = 8; d <= m.range; d += 8) { if (!G.World.isFree(pl.x + Math.cos(a) * d, pl.y + Math.sin(a) * d, pl.r * .8, true)) break; len = d; }
      const sx = pl.x, sy = pl.y; pl.x += Math.cos(a) * len; pl.y += Math.sin(a) * len; G.World.collide(pl); pl.invuln = Math.max(pl.invuln || 0, .3);
      for (const e of targets((sx + pl.x) / 2, (sy + pl.y) / 2, len / 2 + m.width)) { const dx = pl.x - sx, dy = pl.y - sy, t = Math.max(0, Math.min(1, ((e.x - sx) * dx + (e.y - sy) * dy) / (dx * dx + dy * dy || 1))); if (G.U.dist2(e.x, e.y, sx + dx * t, sy + dy * t) <= (m.width / 2 + e.r) ** 2) hit(pl, m, e, m.dmg * pl.atk, Math.cos(a), Math.sin(a)); }
      G.FX.slash(pl.x, pl.y - G.LIFT * .5, a, 34, 2.2, color(m), vis(m));
      if (m.narutoSkill) { const v=vis(m); G.FX.sp(v.proj||'wind',v.pal,pl.x,pl.y-G.LIFT,{life:.35,scale:1.7}); }
    } else if (mode === 'slam') { const x = pl.x + Math.cos(a) * m.range * .55, y = pl.y + Math.sin(a) * m.range * .55; G.FX.ring(x, y, 5, m.radius, color(m), .24, 3); area(pl, m, x, y, m.radius); }
    else if (mode === 'gate') { const target = pl.target && !pl.target.dead && G.U.dist(pl.x, pl.y, pl.target.x, pl.target.y) <= m.range ? pl.target : G.Projectiles.nearest(targets(pl.x, pl.y, m.range), pl.x, pl.y, m.range); if (target) field(pl, m, 'gate', { x: target.x, y: target.y, life: m.fieldDuration || 4, tick: m.fieldTick || .7, phase: 0 }); }
    else if (mode === 'sand-wave') {
      const flowDuration=m.waveDuration||.65,bindDuration=m.bindDuration||.5;
      field(pl,m,'sand-wave',{aim:a,flowDuration,bindDuration,burstTime:flowDuration+bindDuration,
        life:flowDuration+bindDuration+.35,phase:'flow',hits:new Set(),victims:[],crushed:false});
    }
    else if (mode === 'aura') {
      G.FX.ring(pl.x, pl.y, 4, m.radius, color(m), .28, 3);
      const v=vis(m);
      for(let i=0;i<12;i++) { const a=i*TAU/12; G.FX.sp(v.aura||v.proj||'star',v.pal,pl.x+Math.cos(a)*28,pl.y-G.LIFT+Math.sin(a)*20,{vx:Math.cos(a)*90,vy:Math.sin(a)*65,life:.6,scale:1}); }
      const dealt = area(pl, m, pl.x, pl.y, m.radius); if (m.healFraction && dealt > 0) pl.heal(Math.min(dealt, pl.maxHp * m.healFraction));
    }
    else if (mode === 'blizzard') { sweep(pl, m, pl.x, pl.y, a, m.range, arc); field(pl, m, 'frost', { x: pl.x + Math.cos(a) * m.range * .65, y: pl.y + Math.sin(a) * m.range * .65, life: m.fieldDuration || 3, tick: m.fieldTick || .65, radius: m.blastRadius || m.radius }); }
    else if (mode === 'dual') { const s = Object.assign({}, m, m.secondary || {}); line(pl, s, pl.x, pl.y, a, s.range || m.range, s.width || m.width, .55); sweep(pl, m, pl.x, pl.y, a, m.radius, m.arc || 2, .65); }
  }
  function cast(pl, move) {
    const m=cloneMove(G.Quantity?.snapshot(pl,move)||move);
    if(!m||!m.digimonSkill||!m.digiMode)return false;
    if(m.digiMode==='shadow-clones')return !!G.NarutoClones?.beginCast(pl,m);
    const handler=techniqueFor(m.digiMode);
    if(m.narutoSkill&&m.dmg>0&&!G.NarutoSupport?.supports(m.digiMode))m.dmg*=G.NarutoSupport?.takeAttackBonus(pl)||1;
    if(handler)return handler.cast(pl,m);
    if(m.id==='naruto-fireball'&&pl.dex===30002&&G.NarutoFireball)return G.NarutoFireball.cast(pl,m,(owner,move,aim)=>emit(owner,move,aim));
    if(m.charge>0)field(pl,m,'charge',{life:m.charge,aim:pl.aim,x:pl.x,y:pl.y});else emit(pl,m);
    return true;
  }
  function customUpdate(dt) {
    for (let i = fields.length - 1; i >= 0; i--) {
      const f = fields[i]; if (!valid(f)) { fields.splice(i, 1); continue; } f.t += dt;
      if (f.kind === 'charge' && f.t >= f.life) { emit(f.owner, f.m, f.aim); fields.splice(i, 1); continue; }
      if (f.kind === 'combo' && f.t >= f.delay) { sweep(f.owner, f.m, f.x, f.y, f.aim, f.m.radius, f.m.arc || 2, 1 / Math.max(1, (f.m.quantityBaseCount??f.m.count) | 0),Math.round(f.delay/(f.m.burstInterval||.12))%2?1:-1); fields.splice(i, 1); continue; }
      if (f.kind === 'sand-wave') updateSand(f);
      if (f.kind === 'gate' || f.kind === 'frost') {
        f.phase += dt; if (f.phase >= f.tick) { f.phase -= f.tick; const m = f.m;
          for (const e of targets(f.x, f.y, f.kind === 'gate' ? m.radius : f.radius)) { if (f.kind === 'gate') { const boss = !!e.boss, dx = f.x - e.x, dy = f.y - e.y, k = boss ? .12 : (m.pull || .4); if (G.U.dist2(e.x, e.y, f.x, f.y) > 36) { e.kx += dx * k; e.ky += dy * k; } e.applySlow(Math.max(m.slow || 0, .25)); } else if (m.slow) e.applySlow(m.slow); hit(f.owner, m, e, m.dmg * f.owner.atk * .2, e.x - f.x, e.y - f.y); }
        }
      }
      if (f.life && f.t >= f.life) fields.splice(i, 1);
    }
  }
  function update(dt) { vanilla.updateFields(dt); customUpdate(dt); }
  function draw(ctx, kinds) { const now = performance.now() / 1000; for (const f of fields) { if (!kinds.includes(f.kind) || !G.Camera.sees(f.x, f.y, 220)) continue; ctx.save(); if (f.kind === 'gate' || f.kind === 'frost' || f.kind === 'charge') { const r = f.kind === 'frost' ? f.radius : f.kind === 'gate' ? f.m.radius : 22; ctx.globalAlpha = f.kind === 'charge' ? .3 + .2 * Math.sin(now * 12) : .35; ctx.strokeStyle = f.col; ctx.lineWidth = 2; ctx.setLineDash([4, 4]); ctx.beginPath(); ctx.ellipse(f.x, f.y, r, r * .65, 0, 0, TAU); ctx.stroke(); if (f.kind === 'gate') G.VFX.draw(ctx, 'digi-gaia', 'holy', f.x, f.y - 5, { scale: 2, frame: Math.floor(now * 5) }); } ctx.restore(); } }
  function clear(owner) { vanilla.clear(owner); for (let i = fields.length - 1; i >= 0; i--) if (!owner || fields[i].owner === owner) fields.splice(i, 1); for (const p of [...bombs]) if (!owner || p.owner === owner) { p.digiBomb = null; G.Projectiles.remove(p); bombs.delete(p); } }
  C.tick = function(dt, pl, now) {
    if (!pl || pl.dead) return vanilla.tick(dt, pl, now);
    const original = pl.activeGroup; let custom = [];
    if (original) { const group = original.call(pl); custom = group.filter(m => m && m.digimonSkill); if (!custom.length) return vanilla.tick(dt, pl, now); pl.activeGroup = function() { return original.call(this).filter(m => !m.digimonSkill); }; }
    try { vanilla.tick(dt, pl, now); } finally { if (original) pl.activeGroup = original; }
    for(const m of custom) {
      m.t-=dt;if(m.t>0)continue;
      const target=pl.target,handler=techniqueFor(m.digiMode);
      if(handler?.canCast&&!handler.canCast(pl,m)){m.t=.15;continue;}
      if(m.digiMode==='shadow-clones'&&!G.NarutoClones?.canCast(pl,m)){m.t=.15;continue;}
      if(['shot','beam','melee','dash','slam','gate','blizzard','dual','sand-wave'].includes(m.digiMode)&&(!target||target.dead||G.U.dist(pl.x,pl.y,target.x,target.y)>(m.range||m.radius||520))){m.t=.05;continue;}
      m.t=Math.max(m.minCooldown||.05,m.cd*pl.cdMul);const snapshot=cloneMove(m);
      pl.cast(m);if(G.Coop.active)G.Coop.cast(pl,m);m.castAt=performance.now();
      if(!cast(pl,snapshot))m.t=.25;
    }
  };
  C.updateFields = update;
  C.drawGroundFields = ctx => { vanilla.ground(ctx); draw(ctx, ['gate','frost','charge']);
    for(const f of fields)if(f.kind==='sand-wave'&&valid(f))G.NarutoSandVFX?.drawGround(ctx,f);
  };
  C.drawAirFields = ctx => {
    vanilla.air(ctx);
    for(const f of fields) {
      if(!valid(f))continue;
      if(f.kind==='sand-wave'){G.NarutoSandVFX?.drawAir(ctx,f);continue;}
      if(f.kind==='charge') {
        const progress=Math.min(1,f.t/Math.max(.01,f.life));
        G.VFX.draw(ctx,f.v.proj||'ball',f.v.pal,f.owner.x,f.owner.y-f.owner.bodyH*.62,
          {scale:f.v.projScale||.6+progress*1.5,frame:Math.floor(f.t*12),alpha:.6+progress*.4});
      } else if(f.kind==='gate') {
        const cx=f.x,cy=f.y-G.LIFT-28,spin=f.t*1.5;
        ctx.save();
        for(let i=0;i<30;i++) {const a=i*TAU/30+spin;ctx.fillStyle=G.VFX.PAL.holy[i%3+2];ctx.fillRect(Math.round((cx+Math.cos(a)*24)/2)*2,Math.round((cy+Math.sin(a)*43)/2)*2,4,4);}
        ctx.restore();
      } else if(f.kind==='frost') {
        for(let i=0;i<7;i++){const a=i*TAU/7;G.VFX.draw(ctx,'shard','ice',f.x+Math.cos(a)*f.radius*.6,f.y-G.LIFT*.4+Math.sin(a)*f.radius*.45,{scale:.65,alpha:.55});}
      }
    }
  };
  C.clearFields = clear;
  C.resolve = function(dt, pl, now) { vanilla.resolve(dt, pl, now); const live=new Set(G.Projectiles.all()); for (const p of [...bombs]) { const b = p.digiBomb, alive = live.has(p); if (!b) { bombs.delete(p); continue; } if (!b.owner || b.owner !== G.Game.player || b.owner.dead || b.owner.hp <= 0) { p.digiBomb = null; G.Projectiles.remove(p); bombs.delete(p); continue; } if ((p.hits && p.hits.size) || !alive) { const m = b.m; if(m.id==='naruto-fireball')G.FX.sp('naruto-great-fireball-burst','naruto-fireball',p.x,p.y-G.LIFT,{life:.24,scale:b.r/51,frameRate:12}); G.FX.ring(p.x, p.y, 4, b.r, color(m), .25, 3); for (const e of targets(p.x, p.y, b.r)) hit(b.owner, m, e, m.dmg * b.owner.atk * .8, e.x - p.x, e.y - p.y); propHits(b.owner, m, p.x, p.y, b.r, m.dmg * b.owner.atk * .8); p.digiBomb = null; G.Projectiles.remove(p); bombs.delete(p); } } };
  // Native pixel additions; VFX's public tables are the same used by the cache.
  G.VFX.PAL.holy = ['#786022','#b38a32','#e2c56b','#fff0b0','#fffdf0'];
  G.VFX.PAL.blueflame = ['#133e70','#267ed1','#58c5ff','#b3f1ff','#fff'];
  G.VFX.SHAPES['digi-fish'] = { w: 15, h: 11, frames: 2, dir: true, gen(P,f) { P.fill((x,y) => { const d = Math.abs(x - 8) / 5 + Math.abs(y - 5) / 3; return d < 1 ? (y < 5 ? 'l' : 'm') : null; }); P.set(f ? 3 : 4,4,'l'); P.set(1,5,'m'); P.set(2,6,'d'); P.set(10,3,'w'); P.outline(); } };
  G.VFX.SHAPES['digi-missile'] = { w: 15, h: 7, dir: true, gen(P) { for(let x=1;x<11;x++) for(let y=2;y<5;y++) P.set(x,y,y===2?'l':'m'); P.set(11,3,'w'); P.set(0,1,'d'); P.set(0,5,'d'); P.outline(); } };
  G.VFX.SHAPES['digi-feather'] = { w:15,h:9,dir:true,gen(P) {
    P.line(1,6,13,3,'w');
    for(let x=4;x<12;x++){P.line(x,5-(x-4)*.2,x-2,1,'l');P.line(x,5-(x-4)*.2,x-3,7,'m');}
    P.outline();
  } };
  G.VFX.SHAPES['digi-gaia'] = { w: 15, h: 15, frames: 3, gen(P,f) { P.fill((x,y) => { const d=Math.hypot(x-7,y-7); return d<2?'w':d<4?'l':d<6?(f%2?'m':'d'):null; }); for(let i=0;i<4;i++){const a=i*Math.PI/2+f*.16;P.line(7+Math.cos(a)*3,7+Math.sin(a)*3,7+Math.cos(a)*6,7+Math.sin(a)*6,'m');} P.outline(); } };
  const priorForMove = G.VFX.forMove;
  G.VFX.forMove = m => { const v = priorForMove(m); return m && m.digimonSkill ? Object.assign(v, m.digiVis || {}) : v; };
  Object.assign(G.DigimonSkills = G.DigimonSkills || {}, { cast, fireFrom, update: customUpdate, clear, get activeEffects() { return fields; } });
})();
