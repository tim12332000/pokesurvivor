/* Local Digimon skill layer. Loaded after systems/combat.js and entities/vfx.js. */
(() => {
  const controlled = owner => G.SelfClones?.isControlled(owner) ?? (owner === G.Game.player);
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
  const valid = f => f.owner && controlled(f.owner) && !f.owner.dead && f.owner.hp > 0 && f.world === G.World;
  const cap = () => { const limit=G.Quantity?.count(G.Game.player,CAP)??CAP; while (fields.length > limit) fields.shift(); };
  const targets = (x, y, r) => [...new Set(G.EnemyMgr.queryCircle(x, y, r))].filter(e => !e.dead);
  const techniqueFor = mode => [G.NarutoGaara,G.NarutoSupport,G.NarutoLee,G.NarutoOffense,G.NarutoChidori,G.NarutoTenten,G.NarutoPain,G.NarutoTemari,G.NarutoTemariReflect].find(api=>api?.supports(mode));
  function hit(pl, m, e, base, dx, dy, knock = m.knock || 0) {
    if (!e || e.dead) return 0;
    const k = G.Types.mult(m.type, e.types) * G.Weather.mult(m.type), crit = pl.critChance > 0 && Math.random() < pl.critChance;
    const dmg = base * k * (crit ? 1.5 : 1) * (m.narutoSkill ? G.NarutoSupport?.precisionMultiplier(pl,e)||1 : 1);
    e.hurt(dmg, color(m), dx, dy, knock, crit ? 'crit' : G.Types.label(G.Types.mult(m.type, e.types)), pl, m.id);
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
  function projectile(pl, m, a, ratio = 1, explosive = false, origin = pl, shotIndex = 0) {
    if(m.fireballAOE)explosive=false;
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
      hits: new Set(), vis: v, owner: pl, mid: m.id, mtype: m.type, burn: m.burn || 0, poison: m.poison || 0,
      slow: m.slow || 0, knock: m.knock || 0, damageSplash: !explosive && !m.fireballAOE && !m.blastRadius,
      digiBomb: explosive ? { m, owner: pl, r: m.blastRadius || m.radius } : null });
    if(m.fumaReturn) {
      Object.assign(p,{fumaReturn:true,boom:m.boom,bsp:m.speed*1.1,fumaPierce:p.pierce,fumaLearned:pl.hasMove(m.id)});
      const target=pl.target,locked=target&&!target.dead&&G.EnemyMgr.all().includes(target)&&G.U.dist(pl.x,pl.y,target.x,target.y)<=m.range;
      const tx=locked?target.x:p.x+Math.cos(a)*m.speed*m.boom,ty=locked?target.y:p.y+Math.sin(a)*m.speed*m.boom;
      const [dx,dy]=G.U.norm(tx-p.x,ty-p.y),bend=(m.fumaCurve||130)*(shotIndex%2?-1:1)*(1+Math.min(2,shotIndex>>1)*.12);
      p.fumaCurve={sx:p.x,sy:p.y,tx,ty,cx:(p.x+tx)/2-dy*bend*2,cy:(p.y+ty)/2+dx*bend*2,duration:m.boom};
    }
    if(m.fireballGrowth) {
      p.fireballGrowth={...m.fireballGrowth,travelled:0,baseRadius:p.r,baseScale:v.projScale||1};
      p.r*=m.fireballGrowth.startRatio;
      p.vis.projScale=p.fireballGrowth.baseScale*m.fireballGrowth.startRatio;
    }
    if(m.fireballAOE)G.NarutoFireballAOE?.track(p,m,pl);
    if (explosive) { bombs.add(p); cap(); }
    return p;
  }
  function fireFrom(owner,move,x,y,aim,damageScale=1) {
    if(!controlled(owner)||owner.dead||owner.hp<=0||![x,y,aim,damageScale].every(Number.isFinite))return [];
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
  function sweep(pl, m, x, y, aim, radius, arc, ratio = 1, hand = 0, quiet = false) {
    if(!quiet)G.FX.slash(x, y - G.LIFT * .5, aim, radius, arc, color(m), vis(m));
    if(m.narutoSkill&&vis(m).melee==='naruto-lion') {
      const ca=Math.cos(aim),sa=Math.sin(aim),side=hand||1;
      G.FX.sp('naruto-lion',vis(m).pal,x+ca*27-sa*side*12,y-G.LIFT+sa*27+ca*side*12,
        {vx:ca*110,vy:sa*110,life:.24,scale:1.4,angle:aim,fade:false});
    }
    for (const e of targets(x, y, radius)) {
      const a = Math.atan2(e.y - y, e.x - x);
      if (Math.abs(((a - aim + Math.PI * 3) % TAU) - Math.PI) <= arc / 2 &&
          (!quiet || whirlwindPath(x,y,e.x,e.y)))
        hit(pl, m, e, m.dmg * pl.atk * ratio, e.x - x, e.y - y);
    }
    propHits(pl, m, x, y, radius, m.dmg * pl.atk * ratio, p => Math.abs(((Math.atan2(p.y - y, p.x - x) - aim + Math.PI * 3) % TAU) - Math.PI) <= arc / 2);
  }
  function whirlwindPath(ax,ay,bx,by){
    const n=Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/4));
    for(let i=1;i<=n;i++){
      const x=ax+(bx-ax)*i/n,y=ay+(by-ay)*i/n;
      if(G.World.isWall(x,y)||G.World.projectileBlock(x,y,1))return false;
    }
    return true;
  }
  const whirlwindValid=f=>valid(f)&&f.owner.activeGroup().some(move=>move.id==='naruto-lee');
  function whirlwindFor(owner){
    for(let i=fields.length-1;i>=0;i--){const f=fields[i];if(f.kind==='lee-whirlwind'&&f.owner===owner&&whirlwindValid(f))return f;}
    return null;
  }
  function startWhirlwind(owner,m){
    if(whirlwindFor(owner)||G.NarutoLee?.activeFor(owner))return false;
    const life=Math.min(.72,Math.max(.016,Math.max(m.minCooldown||.05,m.cd*owner.cdMul)*.8));
    const count=Math.max(1,m.count|0),target=owner.target;
    const distance=target?Math.hypot(target.x-owner.x,target.y-owner.y):0;
    const travel=Math.min(20,Math.max(0,distance-(owner.r||12)-(target?.r||10)-4));
    const key=G.NarutoGates?.stage(owner)?'lee-opened-whirlwind-air':'lee-whirlwind-air';
    const asset=window.AnimationAssets?.get(key),contact=asset?.frames[5];
    const footHeight=contact?.foot?(contact.anchor[1]-contact.foot[1])*64*(owner.anim.scale||1)/asset.bodyHeight:28;
    const contactLift=Math.max(6,Math.min(32,(target?.bodyH||24)*.9+4-footHeight));
    field(owner,m,'lee-whirlwind',{life,aim:owner.aim||0,phase:'step',frame:0,visualLift:0,
      travel,contactLift,travelled:0,nextHit:0,lastHit:-1,hitTimes:Array.from({length:count},(_,i)=>(.38+(count>1?.08*i/(count-1):0))*life/.72),
      camera:{x:G.Camera.x,y:G.Camera.y},startX:owner.x,startY:owner.y});
    return true;
  }
  function updateWhirlwind(f,dt){
    if(G.Game.state!=='playing'||!(dt>0)||!Number.isFinite(dt))return;
    const end=Math.min(f.life,f.t+dt),stepEnd=f.life*.08/.72;
    const goal=f.travel*Math.min(1,end/stepEnd);let budget=Math.max(0,goal-f.travelled);
    const steps=Math.ceil(budget/4)+2;
    for(let i=0;i<steps&&budget>.001;i++){
      const step=Math.min(4,budget),x=f.owner.x+Math.cos(f.aim)*step,y=f.owner.y+Math.sin(f.aim)*step;
      if(!G.World.isFree(x,y,f.owner.r||12,true)||!whirlwindPath(f.owner.x,f.owner.y,x,y))break;
      f.owner.x=x;f.owner.y=y;f.travelled+=step;budget-=step;
    }
    if(!f.takeoff&&end>=stepEnd){f.takeoff=true;G.FX.burst(f.owner.x,f.owner.y,'#b7b98b',4,20);}
    while(f.nextHit<f.hitTimes.length&&f.hitTimes[f.nextHit]<=end+1e-9){
      f.t=f.hitTimes[f.nextHit];f.phase='strike';f.frame=5;f.visualLift=f.contactLift;f.lastHit=f.t;
      sweep(f.owner,f.m,f.owner.x,f.owner.y,f.aim,f.m.radius,f.m.arc||3.9,
        1/Math.max(1,(f.m.quantityBaseCount??f.m.count)|0),0,true);
      f.nextHit++;
    }
    f.t=end;const age=f.t/f.life*.72;
    f.phase=age<.08?'step':age<.20?'rise':age<.30?'spread':age<.38?'turn':age<.46?'strike':age<.60?'descend':'recovery';
    f.frame=age<.08?0:age<.20?1:age<.30?2:age<.34?3:age<.38?4:age<.60?5:age<.66?6:7;
    const turn=Math.max(0,Math.min(1,(age-.30)/.08)),ease=turn*turn*(3-2*turn);
    f.visualLift=age<.08||age>=.60?0:age<.20?32*Math.sin((age-.08)/.12*Math.PI/2):age<.30?32:
      age<.38?32+(f.contactLift-32)*ease:age<.46?f.contactLift:f.contactLift*(1-((age-.46)/.14)**1.5);
    if(!f.landed&&age>=.60){f.landed=true;G.FX.burst(f.owner.x,f.owner.y,'#b7b98b',3,16);}
    f.x=f.owner.x;f.y=f.owner.y;
  }
  function drawWhirlwind(ctx,f){
    const age=f.t/f.life*.72;
    if(age<.34||age>.60)return;
    const fade=age<.46?1:Math.max(0,(.60-age)/.14),r=f.m.radius;
    const key=G.NarutoGates?.stage(f.owner)?'lee-opened-whirlwind-air':'lee-whirlwind-air';
    const asset=window.AnimationAssets?.get(key),frame=asset?.frames[f.frame];
    const footY=frame?.foot?(frame.foot[1]-frame.anchor[1])*64*(f.owner.anim.scale||1)/asset.bodyHeight:-26;
    ctx.save();ctx.globalAlpha=.65*fade;ctx.lineWidth=2;
    for(let i=0;i<3;i++){
      ctx.strokeStyle=i===0?'#e2f2bd':'#7abf80';ctx.beginPath();
      const start=f.aim-(f.m.arc||3.9)/2,end=f.aim+(f.m.arc||3.9)/2;
      ctx.arc(f.owner.x,f.owner.y-f.visualLift+footY,r-i*4,start,end);ctx.stroke();
    }
    ctx.restore();
  }
  function field(pl, m, kind, o = {}) { fields.push(Object.assign({ kind, owner: pl, world: G.World, m: cloneMove(m), x: pl.x, y: pl.y, t: 0, col: color(m), v: vis(m) }, o)); cap(); }
  const rasenganFor = owner => fields.find(f => f.kind === 'rasengan' && f.owner === owner && valid(f));
  function rasenganPath(x, y, tx, ty, radius) {
    const distance=Math.hypot(tx-x,ty-y),steps=Math.max(1,Math.ceil(distance/4));
    for(let i=1;i<=steps;i++)if(!G.World.isFree(x+(tx-x)*i/steps,y+(ty-y)*i/steps,radius,true))return false;
    return true;
  }
  function rasenganImpact(f) {
    const pl=f.owner,r=f.m.radius*.75;
    f.phase='impact';f.phaseAge=0;f.x=pl.x;f.y=pl.y;
    pl.invuln=Math.max(pl.invuln||0,.5);
    for(const e of targets(pl.x,pl.y,r)) {
      const dx=e.x-pl.x,dy=e.y-pl.y,d=Math.hypot(dx,dy);
      if(d>r+(e.r||0)||!rasenganPath(pl.x,pl.y,e.x,e.y,1))continue;
      const nx=d>1e-6?dx/d:Math.cos(f.aim),ny=d>1e-6?dy/d:Math.sin(f.aim);
      // The shockwave makes room without dealing a second copy of the dash damage.
      if(e.boss||e.legend||e.judge)continue;
      e.kx+=nx*300;e.ky+=ny*300;
      e.touchCd=Math.max(e.touchCd||0,.4);
    }
    G.FX.spark(pl.x+Math.cos(f.aim)*22,pl.y-G.LIFT+Math.sin(f.aim)*22,'#b9f5ff',Math.cos(f.aim),Math.sin(f.aim),12);
    G.Audio.sfx('hit');
  }
  function updateRasengan(f, dt) {
    if(!f.owner.activeGroup().some(m=>m.id===f.m.id))return false;
    let remaining=dt;
    while(remaining>1e-9) {
      const duration=f.phase==='charge'?Math.max(.01,f.m.charge||.6):f.phase==='dash'?.16:.28;
      const step=Math.min(remaining,duration-f.phaseAge);remaining-=step;f.phaseAge+=step;
      if(f.phase==='dash') {
        const pl=f.owner,travel=f.m.range/.16*step,pieces=Math.max(1,Math.ceil(travel/4));
        let blocked=false;
        for(let i=0;i<pieces;i++) {
          const x=pl.x+Math.cos(f.aim)*travel/pieces,y=pl.y+Math.sin(f.aim)*travel/pieces;
          if(!G.World.isFree(x,y,pl.r,true)){blocked=true;break;}
          pl.x=x;pl.y=y;
          for(const e of targets(x,y,f.m.width/2+32)) {
            if(f.hits.has(e)||Math.hypot(e.x-x,e.y-y)>f.m.width/2+e.r||!rasenganPath(x,y,e.x,e.y,1))continue;
            f.hits.add(e);hit(pl,f.m,e,f.m.dmg*pl.atk,Math.cos(f.aim),Math.sin(f.aim));
          }
        }
        if(blocked)f.phaseAge=duration;
      }
      if(f.phaseAge+1e-9<duration)break;
      if(f.phase==='charge'){f.phase='dash';f.phaseAge=0;}
      else if(f.phase==='dash')rasenganImpact(f);
      else return false;
    }
    return true;
  }
  const playerUpdate=G.Player.prototype.update,playerHurt=G.Player.prototype.hurt;
  G.Player.prototype.update=function(dt) {
    const f=rasenganFor(this);
    if(!f||f.phase==='impact')return playerUpdate.call(this,dt);
    const frozen=this.frozen;this.frozen=true;
    try{return playerUpdate.call(this,dt);}finally{this.frozen=frozen;}
  };
  G.Player.prototype.hurt=function(...args) {
    if(rasenganFor(this)?.phase==='dash')return;
    return playerHurt.apply(this,args);
  };
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
    if (mode === 'shot') for (let i = 0; i < n; i++) projectile(pl, m, a + (n === 1 ? 0 : (i / (n - 1) - .5) * arc), 1, !!m.blastRadius,pl,i);
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
    if(m.digiMode==='sharingan-evolution')return !!G.NarutoSharingan?.sync(pl);
    if(m.digiMode==='kusanagi-orbit')return !!G.NarutoKusanagi?.activate(pl);
    if(m.digiMode==='shadow-clones')return !!G.NarutoClones?.beginCast(pl,m);
    const handler=techniqueFor(m.digiMode);
    if(m.narutoSkill&&m.dmg>0&&!G.NarutoSupport?.supports(m.digiMode))m.dmg*=G.NarutoSupport?.takeAttackBonus(pl)||1;
    if(m.id==='naruto-lee')return startWhirlwind(pl,m);
    if(m.id==='naruto-naruto') {
      if(rasenganFor(pl))return false;
      field(pl,m,'rasengan',{phase:'charge',phaseAge:0,aim:pl.aim,hits:new Set()});
      return true;
    }
    if(handler)return handler.cast(pl,m);
    if(m.id==='naruto-fireball'&&pl.dex===30002&&G.NarutoFireball)return G.NarutoFireball.cast(pl,m,(owner,move,aim)=>emit(owner,move,aim));
    if(m.charge>0)field(pl,m,'charge',{life:m.charge,aim:pl.aim,x:pl.x,y:pl.y});else emit(pl,m);
    return true;
  }
  function customUpdate(dt) {
    for (let i = fields.length - 1; i >= 0; i--) {
      const f = fields[i]; if (!valid(f)) { fields.splice(i, 1); continue; }
      if(f.kind==='lee-whirlwind'){
        if(!whirlwindValid(f)){fields.splice(i,1);continue;}
        updateWhirlwind(f,dt);if(f.t>=f.life)fields.splice(i,1);continue;
      }
      f.t += dt;
      if(f.kind==='rasengan'){if(!updateRasengan(f,dt))fields.splice(i,1);continue;}
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
      if(m.passive||G.NarutoGaara?.maintains(pl,m))continue;
      if(m.digiMode==='kusanagi-orbit'&&G.NarutoKusanagi?.active(pl))continue;
      m.t-=dt;if(m.t>0)continue;
      if(m.id==='naruto-lee'&&(whirlwindFor(pl)||G.NarutoLee?.activeFor(pl))){m.t=.05;continue;}
      const target=pl.target,handler=techniqueFor(m.digiMode);
      if(handler?.canCast&&!handler.canCast(pl,m)){m.t=.15;continue;}
      if(m.digiMode==='shadow-clones'&&!G.NarutoClones?.canCast(pl,m)){m.t=.15;continue;}
      if(['shot','beam','melee','dash','slam','gate','blizzard','dual','sand-wave'].includes(m.digiMode)&&(!target||target.dead||G.U.dist(pl.x,pl.y,target.x,target.y)>(m.range||m.radius||520))){m.t=.05;continue;}
      m.t=Math.max(m.minCooldown||.05,m.cd*pl.cdMul);const snapshot=cloneMove(m);
      pl.cast(m);if(G.Coop.active&&!G.SelfClones?.isActor(pl))G.Coop.cast(pl,m);m.castAt=performance.now();
      if(!cast(pl,snapshot))m.t=.25;
    }
  };
  C.updateFields = update;
  C.drawGroundFields = ctx => { vanilla.ground(ctx); draw(ctx, ['gate','frost','charge']);
    for(const f of fields)if(f.kind==='sand-wave'&&valid(f))G.NarutoSandVFX?.drawGround(ctx,f);
    for(const f of fields)if(f.kind==='rasengan'&&valid(f)&&f.phase==='impact') {
      const progress=Math.min(1,f.phaseAge/.28),r=f.m.radius*.75*progress;
      ctx.save();ctx.globalAlpha=1-progress;ctx.strokeStyle='#b9f5ff';ctx.lineWidth=3;
      ctx.beginPath();ctx.ellipse(f.x,f.y,r,r*.87,0,0,TAU);ctx.stroke();
      ctx.strokeStyle='#45bfff';ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(f.x,f.y,r*.8,r*.696,0,0,TAU);ctx.stroke();ctx.restore();
    }
  };
  C.drawAirFields = ctx => {
    vanilla.air(ctx);
    for(const f of fields) {
      if(!valid(f))continue;
      if(f.kind==='rasengan') {
        if(f.phase==='charge') {
          const progress=Math.min(1,f.phaseAge/Math.max(.01,f.m.charge)),pl=f.owner;
          const x=pl.x+Math.cos(f.aim)*20,y=pl.y-G.LIFT+Math.sin(f.aim)*16;
          ctx.save();ctx.globalAlpha=.4+progress*.5;
          for(let i=0;i<8;i++) {
            const angle=i*TAU/8+f.phaseAge*10,radius=10+28*(1-progress)+Math.sin(i+f.phaseAge*20)*3;
            ctx.fillStyle=i%2?'#b9f5ff':'#45bfff';
            ctx.fillRect(Math.round((x+Math.cos(angle)*radius)/2)*2,Math.round((y+Math.sin(angle)*radius*.65)/2)*2,2,2);
          }
          ctx.restore();continue;
        }
        if(f.phase!=='dash')continue;
        const pl=f.owner,x=pl.x-Math.cos(f.aim)*15,y=pl.y-pl.bodyH*.5-Math.sin(f.aim)*15;
        // The authored pose already carries the hand-held Rasengan sphere.
        ctx.save();ctx.globalAlpha=.45;ctx.strokeStyle='#7cddff';ctx.lineWidth=2;
        for(let i=-1;i<=1;i++){const ox=-Math.sin(f.aim)*i*9,oy=Math.cos(f.aim)*i*9;ctx.beginPath();ctx.moveTo(x+ox,y+oy);ctx.lineTo(x+ox-Math.cos(f.aim)*42,y+oy-Math.sin(f.aim)*42);ctx.stroke();}
        ctx.restore();continue;
      }
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
  C.resolve = function(dt, pl, now) { vanilla.resolve(dt, pl, now); const live=new Set(G.Projectiles.all()); for (const p of [...bombs]) { const b = p.digiBomb, alive = live.has(p); if (!b) { bombs.delete(p); continue; } if (!b.owner || !controlled(b.owner) || b.owner.dead || b.owner.hp <= 0) { p.digiBomb = null; G.Projectiles.remove(p); bombs.delete(p); continue; } if ((p.hits && p.hits.size) || !alive) { const m = b.m; if(m.id==='naruto-fireball')G.FX.sp('naruto-great-fireball-burst','naruto-fireball',p.x,p.y-G.LIFT,{life:.24,scale:b.r/51,frameRate:12}); G.FX.ring(p.x, p.y, 4, b.r, color(m), .25, 3); for (const e of targets(p.x, p.y, b.r)) hit(b.owner, m, e, m.dmg * b.owner.atk * .8, e.x - p.x, e.y - p.y); propHits(b.owner, m, p.x, p.y, b.r, m.dmg * b.owner.atk * .8); p.digiBomb = null; G.Projectiles.remove(p); bombs.delete(p); } } };
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
  const drawAirWhirlwind=C.drawAirFields;
  C.drawAirFields=function(ctx){drawAirWhirlwind.call(this,ctx);for(const f of fields)if(f.kind==='lee-whirlwind'&&whirlwindValid(f))drawWhirlwind(ctx,f);};
  const meleeStrike=(owner,move,aim=owner.aim,ratio=1)=>sweep(owner,move,owner.x,owner.y,aim,move.radius,move.arc,ratio,0,true);
  Object.assign(G.DigimonSkills = G.DigimonSkills || {}, { cast, fireFrom, rasenganFor, whirlwindFor, meleeStrike, update: customUpdate, clear, get activeEffects() { return fields; } });
})();
