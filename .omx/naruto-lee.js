/* Young Lee's contact taijutsu. Timing, damage and landing splash are game adaptations. */
(() => {
  if (G.NarutoLee) return;
  const C = G.Combat, modes = new Set(['lee-lotus', 'lee-reverse-lotus']);
  const durations = { windup: .24, lift: .40, suspend: .55, descent: .36, slam: .20, recovery: .22 };
  const reverseDurations = { windup: .28, lift: .48, combo: 1.65, descent: .32, slam: .24, recovery: .28 };
  const frontLift = 240;
  const basics = new WeakMap(), claims = new WeakMap();
  const bandageExtend = .10;
  const bindLimitOf=(move,owner=G.Game.player)=>{
    const reverse=move.digiMode==='lee-reverse-lotus',base=reverse?10:3;
    return Math.min(reverse?24:12,G.Quantity?.countAtCast(owner,move,base)??base);
  };
  const chains = new Map(), summaries = new Map(), releasingTargets = new WeakSet();
  const activeFor = owner => chains.get(owner) || null;
  const controlled = owner => owner === G.Game.player || !!G.SelfClones?.isControlled(owner);
  const member = (f, enemy) => f.target===enemy || f.boundTargets.includes(enemy) || f.pendingVictims?.has(enemy);
  const targetChain = enemy => [...chains.values()].filter(f => valid(f) &&
      (f.kind==='lee-reverse-lotus'?member(f,enemy):f.kind==='lee-lotus'&&f.target===enemy) &&
      ['lift', 'suspend', 'combo', 'descent', 'slam'].includes(f.phase))
    .sort((a, b) => Number(!!b.primaryHit) - Number(!!a.primaryHit) || Number(!!b.pendingDeath) - Number(!!a.pendingDeath))[0];
  const alive = actor => actor && !actor.dead && actor.hp > 0;
  const valid = f => f && controlled(f.owner) && f.world === G.World && alive(f.owner);
  const elite = e => !!(e.boss || e.elite || e.legend || e.judge);
  const boss = e => !!(e.boss || e.legend || e.judge);
  const targetRank=e=>boss(e)?0:1;
  const pullableTarget=e=>!elite(e)&&!e.remote&&!e.jump&&!e.flying&&!(e.jumpLift>0);
  const supports = mode => modes.has(mode);
  const launchedLotus = f => supports(f.kind) && ['lift', 'suspend', 'combo', 'descent', 'slam', 'recovery'].includes(f.phase);
  const isInvulnerable = owner => { const f = activeFor(owner); return !!valid(f) && f.kind === 'lee-reverse-lotus' &&
    ['lift', 'combo', 'descent'].includes(f.phase); };
  const reach = f => (f.owner.r || 12) + (f.target.r || 10) + 12;
  const chaseRange=f=>elite(f.target)?600:(f.move.range||145);
  function retreating(owner,target){
    if(owner!==G.Game.player||!elite(target))return false;
    const [x,y]=G.Input.axis(),dx=target.x-owner.x,dy=target.y-owner.y,length=Math.hypot(dx,dy);
    return length>.001&&(x*dx+y*dy)/length<-.35;
  }
  function clearPath(ax, ay, bx, by) {
    const steps = Math.max(1, Math.ceil(Math.hypot(bx - ax, by - ay) / 4));
    for (let i = 1; i <= steps; i++) {
      const x = ax + (bx - ax) * i / steps, y = ay + (by - ay) * i / steps;
      if (G.World.isWall(x, y) || G.World.projectileBlock(x, y, 1)) return false;
    }
    return true;
  }
  function claimFor(enemy) {
    const f=claims.get(enemy);
    if(f&&valid(f)&&activeFor(f.owner)===f&&alive(enemy))return f;
    if(f)claims.delete(enemy);
    return null;
  }
  const bound = enemy => {
    const f=claimFor(enemy);
    return !!f&&f.pullable&&pullableTarget(enemy)&&
      (f.phase==='approach'?f.bandageStage==='pull':['windup','lift','suspend','combo','descent'].includes(f.phase));
  };
  function targetFor(owner, move) {
    const range = move.range || 145;
    const candidates = [...new Set(G.EnemyMgr.queryCircle(owner.x, owner.y, Math.max(range,260)))]
      .filter(e => alive(e) && (!claimFor(e)||claimFor(e).owner===owner) &&
        Math.hypot(e.x-owner.x,e.y-owner.y)<=(elite(e)?Math.max(range,260)+(e.r||0):range)&&clearPath(owner.x,owner.y,e.x,e.y));
    candidates.sort((a,b)=>targetRank(a)-targetRank(b)||Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y));
    return candidates.includes(owner.target)&&targetRank(owner.target)===targetRank(candidates[0])?owner.target:candidates[0];
  }
  function releaseBinding(f,enemy) {
    if(claims.get(enemy)===f)claims.delete(enemy);
    f.bindings=f.bindings.filter(binding=>binding.target!==enemy);
    f.boundTargets=f.boundTargets.filter(target=>target!==enemy);
  }
  function releaseBindings(f){
    for(const enemy of f.boundTargets||[])if(claims.get(enemy)===f)claims.delete(enemy);
    f.boundTargets=[];f.bindings=[];
  }
  function landing(f){
    const angle=Math.atan2(f.target.y-f.owner.y,f.target.x-f.owner.x),r=reach(f);
    return f.phase==='approach'?{x:f.owner.x+Math.cos(angle)*r,y:f.owner.y+Math.sin(angle)*r}:f.target;
  }
  function reserveGroup(f){
    f.boundTargets=[];f.bindings=[];
    if(!f.pullable)return;
    f.boundTargets.push(f.target);claims.set(f.target,f);
    const range=f.move.range||145,center=landing(f);
    const assigned=new Set([...(G.SelfClones?.actors?.()||[]),G.Game.player]
      .filter(actor=>actor!==f.owner&&alive(actor)).map(actor=>actor.target));
    const candidates=[...new Set(G.EnemyMgr.queryCircle(f.owner.x,f.owner.y,range))]
      .filter(e=>e!==f.target&&alive(e)&&pullableTarget(e)&&!claimFor(e)&&!assigned.has(e)&&Math.hypot(e.x-f.owner.x,e.y-f.owner.y)<=range&&clearPath(f.owner.x,f.owner.y,e.x,e.y))
      .sort((a,b)=>Math.hypot(a.x-f.owner.x,a.y-f.owner.y)-Math.hypot(b.x-f.owner.x,b.y-f.owner.y));
    const occupied=[{x:0,y:0,r:f.target.r||10}];
    for(const enemy of candidates){
      if(f.boundTargets.length>=f.bindLimit)break;
      const spacing=2*Math.max(enemy.r||10,...occupied.map(s=>s.r))+3,slots=[];
      for(let y=-3;y<=3;y++)for(let x=-3;x<=3;x++){
        const ox=x*spacing,oy=y*spacing;
        if(Math.hypot(ox,oy)>(f.move.radius||60)*.9)continue;
        if(Math.hypot(center.x+ox-f.owner.x,center.y+oy-f.owner.y)<(f.owner.r||12)+(enemy.r||10)+6)continue;
        if(occupied.some(s=>Math.hypot(s.x-ox,s.y-oy)<s.r+(enemy.r||10)+2))continue;
        if(!G.World.isFree(center.x+ox,center.y+oy,enemy.r||10,true))continue;
        slots.push({x:ox,y:oy,r:enemy.r||10});
      }
      slots.sort((a,b)=>Math.hypot(a.x,a.y)-Math.hypot(b.x,b.y)||Math.abs(a.x)-Math.abs(b.x)||a.y-b.y);
      const slot=slots[0];if(!slot)continue;
      occupied.push(slot);f.bindings.push({target:enemy,offset:slot});f.boundTargets.push(enemy);claims.set(enemy,f);
    }
  }
  function pullSides(f,dt){
    if(!f.pullable||f.age<bandageExtend||['slam','recovery'].includes(f.phase))return;
    const center=landing(f),speed=420*Math.min(1,(f.age-bandageExtend)/.06);
    for(const binding of [...f.bindings]){
      const e=binding.target;
      if(!alive(e)||!pullableTarget(e)||Math.hypot(e.x-f.owner.x,e.y-f.owner.y)>(f.move.range||145)||!clearPath(f.owner.x,f.owner.y,e.x,e.y)){releaseBinding(f,e);continue;}
      const gx=center.x+binding.offset.x,gy=center.y+binding.offset.y;
      let budget=speed*dt,blocked=false;
      for(let n=0;n<Math.ceil(budget/4)+2&&budget>.001;n++){
        const dx=gx-e.x,dy=gy-e.y,d=Math.hypot(dx,dy);if(d<.001)break;
        const step=Math.min(4,budget,d),x=e.x+dx/d*step,y=e.y+dy/d*step;
        if(!G.World.isFree(x,y,e.r||10,true)||!clearPath(e.x,e.y,x,y)){blocked=true;break;}
        e.x=x;e.y=y;budget-=step;
      }
      if(blocked)releaseBinding(f,e);
    }
  }
  function removeLift(f) {
    if (f) { f.targetLift = 0; f.visualLift = 0; }
  }
  const hitLiftFor = enemy => Math.max(0, ...[...chains.values()].filter(f => valid(f) &&
    (f.target===enemy || f.kind==='lee-reverse-lotus'&&member(f,enemy))).map(f => f.targetLift));
  const liftFor = enemy => alive(enemy) ? hitLiftFor(enemy) : 0;
  function resetCamera(f) {
    if(f.cameraLock&&f.owner===G.Game.player&&f.world===G.World){
      G.Camera.shake=G.Camera._sx=G.Camera._sy=0;
    }
    f.cameraLock=null;
  }
  function lockCamera(f) {
    const camera=G.Camera;
    if(f.owner!==G.Game.player||!supports(f.kind)||elite(f.target)||!camera?.w||!camera.h)return;
    f.cameraLock={x:camera.x,y:camera.y};
    const group=f.boundTargets.length?f.boundTargets:[f.target];
    const spreadX=Math.max(...group.map(e=>Math.abs(e.x-f.target.x)*1.75));
    const spreadY=Math.max(...group.map(e=>Math.abs(e.y-f.owner.y)));
    // Fit actor travel into the fixed view once; never zoom or chase individual kicks.
    f.horizontalScale=Math.min(1,Math.max(16,camera.w/2-Math.abs(f.target.x-camera.x)-48)/(Math.max(243,195+spreadX)+70));
    f.verticalScale=Math.min(1,Math.max(16,camera.h/2-Math.abs(f.owner.y-camera.y)-spreadY-100)/(f.peakLift+240));
    if(f.kind==='lee-lotus'){
      f.horizontalScale=1;
      f.verticalScale=Math.min(1,Math.max(16,camera.h/2-Math.abs(f.owner.y-camera.y)-100)/(f.peakLift+64));
    }
    camera.shake=camera._sx=camera._sy=0;
  }
  const followCamera=G.Camera.follow;
  G.Camera.follow=function(...args){
    const whirlwind=G.DigimonSkills?.whirlwindFor?.(G.Game.player);
    if(whirlwind){this.x=whirlwind.camera.x;this.y=whirlwind.camera.y;this.shake=this._sx=this._sy=0;return;}
    const pursuit=G.NarutoPursuit?.activeFor(G.Game.player);
    if(pursuit&&!elite(pursuit.target)){this.x=pursuit.camera.x;this.y=pursuit.camera.y;this.shake=this._sx=this._sy=0;return;}
    const f=activeFor(G.Game.player);
    if(valid(f)&&f.cameraLock){
      this.x=f.cameraLock.x;this.y=f.cameraLock.y;this.shake=this._sx=this._sy=0;
      return;
    }
    return followCamera.apply(this,args);
  };
  function syncLift(f) {
    if (!['lift', 'suspend', 'combo', 'descent'].includes(f.phase) || elite(f.target)) { removeLift(f); return; }
    const reverse = f.kind === 'lee-reverse-lotus', base = reverse ? 60 : frontLift;
    const descent = Math.max(0, Math.min(1, f.phaseAge / f.durations.descent));
    // A short held apex leads into an accelerating plunge, within the existing phase.
    const fall = reverse ? Math.min(1, Math.max(0, (descent - .18) / .78)) ** 2 : descent ** 1.65;
    f.visualLift = f.phase === 'lift' ? Math.sin(Math.min(1, f.phaseAge / f.durations.lift) * Math.PI / 2) * base :
      f.phase === 'descent' ? f.peakLift * Math.max(0, 1 - fall) :
      f.phase === 'combo' ? base + f.ticks * 8 : base;
    f.visualLift*=f.verticalScale||1;
    f.targetLift = f.visualLift;
  }
  // Screen-space pursuit paths; world positions and all contact checks stay native.
  const airPositions = [[-48,18],[48,-18],[-30,-42],[44,32],[0,-58],[0,48]];
  const victimPositions = [[-180,-45],[185,-150],[-195,-85],[180,-200],[0,-160],[155,-80]];
  function airPath(f, points, pursuit = false) {
    const index = Math.max(0, f.ticks - 1), from = f.ticks ? points[index % points.length] : [0,0];
    if (f.ticks >= f.comboHits) return from;
    const start = f.ticks ? f.comboDeadlines[f.ticks - 1] : 0, end = f.comboDeadlines[f.ticks];
    const progress = (f.phaseAge - start) / Math.max(.001, end - start);
    // The victim flies first; Lee crosses the arena afterwards and arrives for contact.
    const t = Math.max(0, Math.min(1, (progress - (pursuit ? .34 : .08)) / (pursuit ? .64 : .62)));
    const ease = t * t * (3 - 2 * t), to = points[f.ticks % points.length];
    return [from[0] + (to[0] - from[0]) * ease, from[1] + (to[1] - from[1]) * ease];
  }
  function victimPose(f) {
    if (!valid(f) || f.kind !== 'lee-reverse-lotus' || elite(f.target) || !['combo','descent'].includes(f.phase)) return null;
    const point = f.phase === 'combo' ? airPath(f, victimPositions) : victimPositions[Math.max(0, f.ticks - 1) % victimPositions.length];
    const settle = f.phase === 'descent' ? 1 - Math.min(1, f.phaseAge / (f.durations.descent * .8)) : 1;
    return { offsetX: point[0] * settle * (f.horizontalScale||1), offsetY: point[1] * settle * (f.verticalScale||1) };
  }
  function victimPresentationFor(enemy) {
    if(!alive(enemy))return null;
    const f=targetChain(enemy);if(!f||elite(f.target))return null;
    if(f.kind==='lee-lotus'){
      if(f.phase==='lift')return {offsetX:0,offsetY:0};
      if(!['suspend','descent'].includes(f.phase))return null;
      const flip=f.phase==='descent'?1:Math.max(0,Math.min(1,(f.phaseAge/f.durations.suspend-.5)/.5));
      const spin=f.phase==='descent'?f.phaseAge/f.durations.descent*6*Math.PI:0;
      return {offsetX:Math.sin(spin)*4,offsetY:0,rotation:Math.PI*flip,pivotY:(enemy.bodyH||24)*.45};
    }
    const pose=victimPose(f);
    if(!pose&&f.phase!=='lift')return null;
    const spread=f.phase==='lift'?Math.min(1,f.phaseAge/f.durations.lift):
      f.phase==='descent'?1-Math.min(1,f.phaseAge/(f.durations.descent*.8)):1;
    return {offsetX:(pose?.offsetX||0)+(enemy.x-f.target.x)*.75*spread*(f.horizontalScale||1),
      offsetY:(pose?.offsetY||0)+(enemy.y-f.target.y)*.65*spread*(f.verticalScale||1)};
  }
  function frontPresentation(f) {
    if(elite(f.target)||!['suspend','descent','slam'].includes(f.phase))return null;
    const frame=f.phase==='slam'?3:f.phase==='descent'?2:
      f.phaseAge<f.durations.suspend*.22?0:f.phaseAge<f.durations.suspend*.72?1:2;
    const key=G.NarutoGates?.stage(f.owner)?'lee-opened-lotus-hold':'lee-lotus-hold';
    const asset=window.AnimationAssets?.get(key),art=asset?.frames[frame];
    if(!art?.grip)return null;
    const spin=f.phase==='descent'?f.phaseAge/f.durations.descent*6*Math.PI:0;
    const mirror=(Math.cos(f.owner.aim)<0)!==(f.phase==='descent'&&Math.cos(spin)<0);
    const side=mirror?-1:1,k=64*(f.owner.anim.scale||1)/asset.bodyHeight;
    const gx=(art.grip[0]-art.anchor[0])*k*side,gy=(art.grip[1]-art.anchor[1])*k;
    const victim=victimPresentationFor(f.target),release=f.phase==='slam'?Math.min(1,f.phaseAge/f.durations.slam):0;
    return {key:'lee-lotus-hold',frame,mirror,
      offsetX:f.target.x-f.owner.x+(victim?.offsetX||0)-gx-side*release*30,
      offsetY:f.target.y-f.owner.y-f.targetLift+(victim?.offsetY||0)-(f.target.bodyH||24)*.45+f.visualLift-gy+release*12};
  }
  function presentationFor(owner) {
    const f = activeFor(owner);
    if(valid(f)&&f.kind==='lee-lotus')return frontPresentation(f);
    if (!valid(f) || f.kind !== 'lee-reverse-lotus' || elite(f.target) ||
        !['combo', 'descent'].includes(f.phase)) return null;
    const point = f.phase === 'combo' ? airPath(f, airPositions, true) : [0,-52];
    const path = f.phase === 'combo' ? airPath(f, victimPositions, true) : null;
    const victim = path ? [path[0]*(f.horizontalScale||1),path[1]*(f.verticalScale||1)] : [victimPose(f).offsetX,victimPose(f).offsetY];
    const settle = f.phase === 'descent' ? 1 - Math.min(1, f.phaseAge / f.durations.descent) : 1;
    const mirror = point[0] > 0;
    let rotation = Math.atan2(-point[1], -point[0]) - (mirror ? Math.PI : 0);
    if (rotation < -Math.PI) rotation += Math.PI * 2;
    return { offsetX: (f.target.x - owner.x + victim[0] + point[0]) * settle,
      offsetY: (f.target.y - owner.y + victim[1] + (point[1] + 18)*(f.verticalScale||1)) * settle,
      mirror, rotation: rotation * settle };
  }
  function clear(owner) {
    for (const [actor, f] of chains) if (!owner || actor === owner) {
      if(elite(f.target)&&!f.primaryHits&&alive(actor)&&f.world===G.World){
        const move=actor.moves.find(m=>m.id===f.move.id);if(move)move.t=Math.min(move.t,.5);
      }
      releasePending(f); resetCamera(f); removeLift(f);
      releaseBindings(f);
      chains.delete(actor);
    }
    for (const actor of summaries.keys()) if (!owner || actor === owner) summaries.delete(actor);
  }
  const pendingDefeat = enemy => [...chains.values()].some(f => valid(f) && f.pendingVictims?.has(enemy) && !enemy.dead);
  function releasePending(f) {
    if (!f.pendingVictims.size || f.releasing) return;
    f.releasing = true;
    for (const target of f.pendingVictims.keys()) if (!target.dead) {
      target.hp = 0;
      if ((f.owner === G.Game.player || f.owner.sourceOwner === G.Game.player) && f.world === G.World) {
        releasingTargets.add(target);
        try { target.die(); } finally { releasingTargets.delete(target); }
      }
      else { G.EnemyMgr.discard(target); target.dead = true; target.fade = 0; }
    }
    f.pendingVictims.clear();
    f.pendingDeath = false;
    f.releasing = false;
  }
  const enemyDie = G.Enemy.prototype.die;
  G.Enemy.prototype.die = function(...args) {
    const f = targetChain(this);
    if (!releasingTargets.has(this) && valid(f) && supports(f.kind) && !this.remote &&
        !f.releasing && !this.dead && this.hp <= 0 && ['lift', 'suspend', 'combo', 'descent', 'slam'].includes(f.phase)) {
      if (!f.pendingVictims.has(this)) f.pendingVictims.set(this,{x:this.x,y:this.y});
      if (f.target===this&&!f.pendingDeath) { f.pendingDeath = true; f.anchorX = this.x; f.anchorY = this.y; }
      this.hp = 1; this.kx = this.ky = 0; this.touchCd = Math.max(.1, this.touchCd || 0);
      return;
    }
    return enemyDie.apply(this, args);
  };
  const enemyHurt = G.Enemy.prototype.hurt;
  G.Enemy.prototype.hurt = function(amount, ...args) {
    const f = [...chains.values()].find(f => valid(f) && f.hitTarget===this);
    const comboHit = valid(f) && f.kind==='lee-reverse-lotus' && !this.dead;
    const result = enemyHurt.call(this, amount, ...args);
    // Later percent-health wrappers pass the complete incoming hit through here.
    // Match the native displayed integer, retaining shield and critical semantics.
    if (comboHit && Number.isFinite(amount)) {
      f.totalDamage += Math.max(1, Math.round(amount));
      if(f.target===this)f.totalHits++;
    }
    return result;
  };
  function canCast(owner, move) {
    if(!supports(move?.digiMode)||activeFor(owner)||G.DigimonSkills?.whirlwindFor?.(owner)||owner?.dex!==30006||!valid({owner,world:G.World}))return false;
    const target=targetFor(owner,move);return !!target&&!retreating(owner,target);
  }
  function cast(owner, move) {
    if (!canCast(owner, move)) return false;
    const target = targetFor(owner, move);
    const snapshot = G.Quantity?.snapshot(owner, move) || { ...move };
    const reverse = move.digiMode === 'lee-reverse-lotus';
    const baseHits = 5 + 2 * (Math.max(1, Math.min(5, snapshot.lvl | 0)) - 1);
    const comboHits = G.Quantity?.countAtCast(owner,snapshot,baseHits) ?? baseHits;
    const comboDuration = reverseDurations.combo / (1 + .025 * Math.max(0, comboHits - 5));
    const firstInterval = comboDuration * .1 / (1 - .9 ** comboHits);
    let elapsed = 0;
    const comboDeadlines = reverse ? Array.from({ length: comboHits }, (_, i) => (elapsed += firstInterval * .9 ** i)) : [];
    const chain = { owner, world: G.World, target, kind: move.digiMode, move: snapshot,
      durations: reverse ? { ...reverseDurations, combo: comboDuration } : durations,
      comboHits, comboDeadlines, peakLift: reverse ? 60 + comboHits * 8 : frontLift,
      phase: 'approach', phaseAge: 0, age: 0, travel: 0, attack: owner.atk,
      pullable: pullableTarget(target),bandageStage:'extend',bindLimit:bindLimitOf(snapshot,owner),boundTargets:[],bindings:[],
      visualLift: 0, targetLift: 0, ticks: 0, totalDamage: 0, totalHits: 0, pendingDeath: false,
      strikes: [], pendingVictims: new Map(), primaryHits: 0 };
    chains.set(owner, chain); summaries.delete(owner);
    reserveGroup(chain);
    owner.svx = owner.svy = 0;
    return true;
  }
  function hit(f, enemy, ratio, singleTarget = true) {
    if (!valid(f) || !alive(enemy) || !clearPath(f.owner.x, f.owner.y, enemy.x, enemy.y)) return;
    if(enemy===f.target&&elite(enemy)&&Math.hypot(enemy.x-f.owner.x,enemy.y-f.owner.y)>reach(f)+24)return;
    const owner = f.owner, move = f.move, mult = G.Types.mult(move.type, enemy.types);
    const crit = owner.critChance > 0 && Math.random() < owner.critChance;
    const damage = move.dmg * ratio * f.attack * mult * G.Weather.mult(move.type) *
      (crit ? 1.5 : 1) * (G.NarutoSupport?.precisionMultiplier(owner, enemy) || 1);
    f.primaryHit = enemy === f.target;
    f.hitTarget = enemy;
    try { enemy.hurt(damage, '#f2ddab', enemy.x - owner.x, enemy.y - owner.y, 0, crit ? 'crit' : G.Types.label(mult), owner, move.id); }
    finally { f.primaryHit = false; f.hitTarget = null; }
    if(enemy===f.target)f.primaryHits++;
    owner.onDealt(damage); owner.dmgDealt += damage;
    if (singleTarget) G.DamageSplash?.hit(owner, enemy, damage, '#f2ddab', move.id);
    const pose=victimPresentationFor(enemy);
    if(f.kind==='lee-reverse-lotus'&&f.boundTargets.length>1)enemy.flash=Math.min(enemy.flash,.03);
    G.FX.burst(enemy.x+(pose?.offsetX||0), enemy.y+(pose?.offsetY||0) - (enemy.jumpLift || 0) - hitLiftFor(enemy), '#f2ddab', 5, 40);
  }
  function hitGroup(f, ratio, splash = true) {
    const targets=f.kind==='lee-reverse-lotus'?new Set([f.target,...f.boundTargets]):[f.target];
    for(const enemy of targets)hit(f,enemy,ratio,splash);
  }
  function enter(f, phase) {
    f.phase = phase; f.phaseAge = 0;
    if(phase==='windup')f.bandageStage='wrap';
    if (phase === 'windup' && f.kind === 'lee-reverse-lotus') {
      // Approach time is part of the full 3.3-second action, not extra time.
      const fixed = ['windup', 'lift', 'descent', 'slam', 'recovery'].reduce((sum, key) => sum + f.durations[key], 0);
      const budget = Math.max(1 / 120, 3.3 - f.age - fixed);
      const scale = Math.min(1, budget / reverseDurations.combo);
      f.durations.combo *= scale;
      f.comboDeadlines = f.comboDeadlines.map(time => time * scale);
    }
    if(phase==='lift')lockCamera(f);
    syncLift(f);
    if (phase === 'lift') {
      if(f.kind==='lee-reverse-lotus')hitGroup(f,.1);
      else hit(f,f.target,.2);
    }
    if (phase === 'slam') {
      f.clothRelease=(f.boundTargets.length?f.boundTargets:[f.target]).filter(alive)
        .map((e,i)=>({x:e.x,y:e.y-(e.bodyH||24)*.3,r:e.r||10,seed:i*79}));
      const pulled=f.boundTargets.slice();releaseBindings(f);
      removeLift(f);
      hit(f, f.target, f.kind === 'lee-lotus' ? .8 : .3, false);
      const group=f.kind==='lee-reverse-lotus'?new Set(pulled):new Set();
      for(const enemy of group)if(enemy!==f.target)hit(f,enemy,.3,false);
      const radius = f.move.radius || 60;
      for (const enemy of new Set([...pulled,...G.EnemyMgr.queryCircle(f.target.x, f.target.y, radius)])) {
        if (enemy !== f.target && !group.has(enemy) && Math.hypot(enemy.x - f.target.x, enemy.y - f.target.y) <= radius + (enemy.r || 0)) hit(f, enemy, .35, false);
      }
      if (f.kind === 'lee-reverse-lotus') {
        // The outside rim marks the actual damage radius from the landing frame.
        G.FX.ring(f.target.x, f.target.y, radius, radius, '#ffe0a3', .42, 4);
        G.FX.ring(f.target.x, f.target.y, 5, radius, '#f6a65e', .36, 6);
        G.FX.burst(f.target.x, f.target.y, '#ddc99a', 16, radius * .65);
        releasePending(f);
      } else {
        G.FX.ring(f.target.x, f.target.y, radius, radius, '#f2d5a0', .32, 3);
        G.FX.ring(f.target.x, f.target.y, 5, radius, '#ddc99a', .28, 4);
        G.FX.burst(f.target.x, f.target.y, '#ddc99a', 8, 65);
        releasePending(f);
      }
    }
  }
  function pull(f,dt) {
    const owner=f.owner,target=f.target;
    owner.aim=owner.moveAngle=Math.atan2(target.y-owner.y,target.x-owner.x);owner.attackFace=.15;
    if(owner.anim)owner.anim.dir=G.Sprites.dirFromAngle(owner.aim);
    if(f.age<bandageExtend){f.bandageStage='extend';return true;}
    f.bandageStage='pull';
    let budget=420*dt*Math.min(1,(f.age-bandageExtend)/.06);
    const maxSteps=Math.ceil(budget/4)+1;
    for(let steps=0;steps<maxSteps&&budget>.001;steps++){
      const dx=owner.x-target.x,dy=owner.y-target.y,distance=Math.hypot(dx,dy);
      if(distance<=reach(f)+.001){enter(f,'windup');return true;}
      const step=Math.min(4,budget,distance-reach(f));
      const x=target.x+dx/distance*step,y=target.y+dy/distance*step;
      if(!G.World.isFree(x,y,target.r||10,true)||!clearPath(target.x,target.y,x,y))return false;
      target.x=x;target.y=y;f.travel+=step;budget-=step;
    }
    if(Math.hypot(target.x-owner.x,target.y-owner.y)<=reach(f)+.001)enter(f,'windup');
    return true;
  }
  function approach(f, dt) {
    const owner = f.owner, target = f.target;
    let budget = Math.min((elite(target)?1000:480)*dt,chaseRange(f)-f.travel);
    // Rounding at contact can leave a subpixel gap whose step changes neither
    // the position nor budget. Tolerate that gap and bound collision sampling.
    const maxSteps = Math.ceil(budget / 4) + 1;
    for (let steps = 0; budget > .001 && steps < maxSteps; steps++) {
      const dx = target.x - owner.x, dy = target.y - owner.y, distance = Math.hypot(dx, dy);
      if (distance <= reach(f) + .001) { enter(f, 'windup'); return true; }
      const step = Math.min(4, budget, distance - reach(f));
      const x = owner.x + dx / distance * step, y = owner.y + dy / distance * step;
      if (!G.World.isFree(x, y, owner.r || 12, true) || !clearPath(owner.x, owner.y, x, y)) return false;
      owner.x = x; owner.y = y; f.travel += step; budget -= step;
      owner.aim = owner.moveAngle = Math.atan2(dy, dx); owner.attackFace = .15;
      if (owner.anim) owner.anim.dir = G.Sprites.dirFromAngle(owner.aim);
    }
    if (Math.hypot(target.x - owner.x, target.y - owner.y) <= reach(f) + .001) enter(f, 'windup');
    return f.phase !== 'approach' || f.travel < chaseRange(f) - .001;
  }
  function followBoss(f,dt){
    const owner=f.owner,target=f.target;
    if(retreating(owner,target))return false;
    let budget=Math.min(1000*dt,Math.max(0,Math.hypot(target.x-owner.x,target.y-owner.y)-reach(f)+4));
    const steps=Math.ceil(budget/4)+1;
    for(let i=0;i<steps&&budget>.001;i++){
      const dx=target.x-owner.x,dy=target.y-owner.y,length=Math.hypot(dx,dy);if(length<.001)break;
      const step=Math.min(4,budget),x=owner.x+dx/length*step,y=owner.y+dy/length*step;
      if(!G.World.isFree(x,y,owner.r||12,true)||!clearPath(owner.x,owner.y,x,y))return false;
      owner.x=x;owner.y=y;budget-=step;
      owner.aim=owner.moveAngle=Math.atan2(dy,dx);owner.attackFace=.15;
      if(owner.anim)owner.anim.dir=G.Sprites.dirFromAngle(owner.aim);
    }
    return true;
  }
  function update(dt) {
    for (const [owner, summary] of summaries) {
      if (!valid(summary) || (G.Game.state === 'playing' && dt > 0 && Number.isFinite(dt) && (summary.ttl -= dt) <= 0)) summaries.delete(owner);
    }
    if (!(dt > 0) || !Number.isFinite(dt)) return;
    for (const f of [...chains.values()]) updateChain(f, dt);
  }
  function updateChain(f, dt) {
    if (valid(f)) for(const [enemy,anchor] of f.pendingVictims){
      enemy.x=anchor.x;enemy.y=anchor.y;enemy.kx=enemy.ky=0;
    }
    if (!valid(f) || (!alive(f.target) && !launchedLotus(f)) || !clearPath(f.owner.x, f.owner.y, f.target.x, f.target.y)) { clear(f.owner); return; }
    if (G.Game.state !== 'playing') return;
    if(retreating(f.owner,f.target)){clear(f.owner);return;}
    if(f.pullable&&!pullableTarget(f.target)){
      releaseBindings(f);
      f.pullable=false;
    }
    removeLift(f);
    // Fixed simulation steps retain all combo hits under a delayed frame.
    let remaining = Math.min(dt, 4);
    while (remaining > 1e-9 && activeFor(f.owner) === f) {
      const phaseRemaining = f.kind === 'lee-reverse-lotus' && f.phase !== 'approach' ?
        Math.max(1e-9, f.durations[f.phase] - f.phaseAge) : Infinity;
      const step = Math.min(remaining, 1 / 120, phaseRemaining); remaining -= step;
      f.age += step; f.phaseAge += step;
      pullSides(f,step);
      if (f.phase === 'approach') {
        if (!(f.pullable?pull(f,step):approach(f, step)) || f.age > .6) { clear(f.owner); return; }
        continue;
      }
      if(elite(f.target)&&f.phase!=='recovery'&&!followBoss(f,step)){clear(f.owner);return;}
      if ((!alive(f.target) && !launchedLotus(f)) || (!elite(f.target)&&Math.hypot(f.target.x - f.owner.x, f.target.y - f.owner.y) > reach(f) + 24)) { clear(f.owner); return; }
      if (f.phase === 'combo') {
        // A defeated bound target stays hittable until the landing resolves it.
        while (f.ticks < f.comboHits && f.phaseAge + 1e-9 >= f.comboDeadlines[f.ticks]) {
          f.ticks++; syncLift(f); hitGroup(f,.12 * 1.1 ** f.ticks);
          const pose = presentationFor(f.owner);
          const victim = victimPose(f);
          f.strikes.push({ age: f.age, x: f.owner.x + (pose?.offsetX || 0), y: f.owner.y - f.visualLift + (pose?.offsetY || 0),
            tx: f.target.x + (victim?.offsetX || 0), ty: f.target.y + (victim?.offsetY || 0) - f.targetLift - (f.target.bodyH || 24) * .5,
            frame: 1 + f.ticks % 2, mirror: pose?.mirror ?? Math.cos(f.owner.aim) < 0,
            rotation: pose?.rotation || 0,
            key: G.NarutoGates?.stage(f.owner) ? 'lee-opened-reverse' : 'lee-reverse' });
          if (f.strikes.length > 6) f.strikes.shift();
        }
      }
      if (f.phaseAge + 1e-9 >= f.durations[f.phase]) {
        const next = f.phase === 'windup' ? 'lift' : f.phase === 'lift' ?
          (f.kind === 'lee-reverse-lotus' ? 'combo' : 'suspend') : ['combo', 'suspend'].includes(f.phase) ? 'descent' : f.phase === 'descent' ? 'slam' : f.phase === 'slam' ? 'recovery' : null;
        if (!next) {
          const summary = f.kind === 'lee-reverse-lotus' && f.totalHits ?
            { owner: f.owner, world: f.world, totalDamage: f.totalDamage, totalHits: f.totalHits, ttl: 1 } : null;
          clear(f.owner); if (summary) summaries.set(f.owner, summary); return;
        }
        enter(f, next);
      }
    }
    if (activeFor(f.owner) !== f) return;
    syncLift(f);
    if (f.visualLift > 0) f.target.applySlow(.95, .08);
  }
  // Contact movement belongs to the technique even when experimental art is disabled.
  // Keep the normal update for animation/status timers; restore only its ground motion.
  const playerHurt = G.Player.prototype.hurt;
  G.Player.prototype.hurt = function() {
    if (isInvulnerable(this)) return;
    return playerHurt.apply(this, arguments);
  };
  const playerUpdate = G.Player.prototype.update;
  G.Player.prototype.update = function(dt) {
    const chain = activeFor(this);
    if (chain && !valid(chain)) clear(this);
    if (!activeFor(this)) return playerUpdate.call(this, dt);
    const frozen = this.frozen, x = this.x, y = this.y;
    this.frozen = true; this.svx = this.svy = 0;
    try { return playerUpdate.call(this, dt); }
    finally { this.frozen = frozen; this.x = x; this.y = y; }
  };
  const setActive=G.Player.prototype.setActive;
  G.Player.prototype.setActive=function(...args){
    const result=setActive.apply(this,args),f=activeFor(this);
    if(f&&!launchedLotus(f)&&!this.activeGroup().some(move=>move.id===f.move.id))clear(this);
    return result;
  };
  // Original CPU cloth material: wide banks, a changing face, narrow folded
  // edges, and split front/back body wraps. No wire strokes or ellipse decals.
  const clothClamp=value=>Math.max(0,Math.min(1,value));
  function clothMesh(points,width,seed){
    const edge=new Path2D(),face=new Path2D(),light=new Path2D(),seam=new Path2D();
    const left=[],right=[],innerLeft=[],innerRight=[],ridge=[];
    for(let i=0;i<points.length;i++){
      const previous=points[Math.max(0,i-1)],next=points[Math.min(points.length-1,i+1)];
      const dx=next[0]-previous[0],dy=next[1]-previous[1],distance=Math.max(.001,Math.hypot(dx,dy));
      const u=i/Math.max(1,points.length-1),twist=.62+.38*Math.abs(Math.cos(u*5.2+seed*.07));
      const half=width*.5*(.65+.35*Math.sin(Math.PI*u))*twist;
      const nx=-dy/distance,ny=dx/distance,x=points[i][0],y=points[i][1];
      left.push([x+nx*half,y+ny*half]);right.push([x-nx*half,y-ny*half]);
      innerLeft.push([x+nx*half*.72,y+ny*half*.72]);innerRight.push([x-nx*half*.72,y-ny*half*.72]);
      ridge.push([x+nx*half*.12,y+ny*half*.12]);
      if(i>1&&i%4===0){seam.moveTo(x-nx*half*.65,y-ny*half*.65);seam.lineTo(x+nx*half*.35,y+ny*half*.35);}
    }
    function polygon(path,points){if(points.length<3)return;path.moveTo(...points[0]);for(let i=1;i<points.length;i++)path.lineTo(...points[i]);path.closePath();}
    polygon(edge,left.concat(right.slice().reverse()));polygon(face,innerLeft.concat(innerRight.slice().reverse()));
    polygon(light,innerLeft.concat(ridge.slice().reverse()));
    return {edge,face,light,seam};
  }
  function paintCloth(ctx,mesh,alpha=1,back=false){
    if(!mesh||alpha<=0)return;
    ctx.save();ctx.globalAlpha*=alpha;ctx.shadowBlur=0;
    ctx.fillStyle=back?'#938b78':'#a69b82';ctx.fill(mesh.edge);
    ctx.fillStyle=back?'#bab19a':'#d8ceb5';ctx.fill(mesh.face);
    ctx.fillStyle=back?'#c9bea5':'#f0e7cf';ctx.globalAlpha*=.66;ctx.fill(mesh.light);
    ctx.strokeStyle='#8f866f';ctx.globalAlpha*=.42;ctx.lineWidth=.45/(G.Camera.scale||1);ctx.stroke(mesh.seam);
    ctx.restore();
  }
  function clothVisuals(f){
    const targets=(f.boundTargets.length?f.boundTargets:[f.target]).filter(alive),p=f.owner;
    const measured=G.AnimationLab?.handForLee?.(p),hand=measured||{
      x:p.x+Math.cos(p.aim)*(p.r||12)*.95,y:p.y-(p.bodyH||G.LIFT*2)*.35-(f.visualLift||0)};
    const scale=G.Camera.scale||1,rate=f.phase==='approach'?60:24,time=Math.floor(f.age*rate)/rate;
    const key=[time,scale,f.phase,Math.floor(f.phaseAge*rate)/rate,hand.x,hand.y,...targets.flatMap(e=>[e.x,e.y,e.r,e.bodyH,e.jumpLift||0,hitLiftFor(e)])].join(':');
    if(f.clothCache?.key===key)return f.clothCache.items;
    if(!f.clothSeeds)f.clothSeeds=new WeakMap();
    const progress=f.phase==='approach'?clothClamp(time/bandageExtend):1;
    const tension=f.pullable?clothClamp((time-bandageExtend)/.10):0;
    const peel=f.phase==='descent'?clothClamp((f.phaseAge/f.durations.descent-.65)/.35):0;
    const items=[];
    for(let index=0;index<targets.length;index++){
      const e=targets[index];if(!f.clothSeeds.has(e))f.clothSeeds.set(e,index*79+(e.id|0));
      const seed=f.clothSeeds.get(e),lift=(e.jumpLift||0)+hitLiftFor(e),pose=victimPresentationFor(e);
      const ex=e.x+(pose?.offsetX||0),ey=e.y+(pose?.offsetY||0);
      const body=Math.max(16,e.bodyH||24),rx=Math.max(6,e.r||10)*.95,cy=ey-lift-body*.32;
      const dx=ex-hand.x,dy=cy-hand.y,distance=Math.max(1,Math.hypot(dx,dy)),nx=-dy/distance,ny=dx/distance;
      const entryAngle=hand.x<ex?Math.PI:0,wrapGrow=f.pullable?clothClamp((time-.075)/.085):0;
      const tx=f.pullable?ex+Math.cos(entryAngle)*rx*.94:ex-dx/distance*rx*.76;
      const ty=f.pullable?ey-lift-body*.49:cy-dy/distance*rx*.3;
      const head=progress<.5?.15*(progress/.5)**2:.15+.85*(progress-.5)/.5;
      const spine=[],width=Math.max(4.2,2.8/scale),bridgeAlpha=['approach','windup'].includes(f.phase)?1:f.phase==='lift'?1-clothClamp(f.phaseAge/.10):0;
      for(let i=0;i<=18;i++){
        const u=head*i/18,arc=Math.sin(Math.PI*u),loose=1-tension;
        const curl=Math.sin(u*7+time*4+seed*.1)*(3+loose*5)*arc;
        spine.push([hand.x+(tx-hand.x)*u+nx*curl,
          hand.y+(ty-hand.y)*u+ny*curl+arc*(loose*12+1.5)]);
      }
      const front=[],back=[];let wrapEnd=[tx,ty];
      if(f.pullable){
        const grow=wrapGrow,turns=(2.15+(seed%3)*.12)*grow*(1-peel);
        let chunk=[],lastFront=null;
        for(let i=0;i<=36;i++){
          const u=i/36,angle=entryAngle+turns*Math.PI*2*u+Math.sin(Math.PI*u)*Math.sin(time*2+seed)*.12;
          const point=[ex+Math.cos(angle)*rx*(.94+.06*Math.sin(u*8)),
            ey-lift-body*.49+body*.32*u*grow+Math.sin(angle)*rx*.19];
          if(i===36)wrapEnd=point;
          const isFront=Math.sin(angle)>=0;
          if(lastFront!==null&&isFront!==lastFront){
            chunk.push(point);if(chunk.length>1)(lastFront?front:back).push(clothMesh(chunk,Math.max(3.3,2/scale),seed));chunk=[point];
          }else chunk.push(point);
          lastFront=isFront;
        }
        if(turns>.05&&chunk.length>1)(lastFront?front:back).push(clothMesh(chunk,Math.max(3.3,2/scale),seed));
      }
      const tail=[];
      for(let i=0;i<=10;i++){
        const u=i/10,angle=time*3+u*3.4+seed*.1;
        tail.push([wrapEnd[0]+u*(5+peel*8)+Math.sin(angle)*u*3,
          wrapEnd[1]+u*(4+peel*7)+Math.cos(angle)*u*2]);
      }
      items.push({target:e,bridge:head>.005?clothMesh(spine,width,seed):null,bridgeAlpha,
        front,back,tail:clothMesh(tail,Math.max(1.8,1.1/scale)*(1-peel*.6),seed),wrapAlpha:wrapGrow*(1-peel)});
    }
    f.clothCache={key,items};return items;
  }
  function clothForEnemy(enemy){
    const f=claimFor(enemy);
    if(!f||!valid(f)||!['approach','windup','lift','suspend','combo','descent'].includes(f.phase))return null;
    return clothVisuals(f).find(item=>item.target===enemy);
  }
  const enemyDraw=G.Enemy.prototype.draw;
  G.Enemy.prototype.draw=function(ctx,...args){
    const cloth=clothForEnemy(this);
    if(cloth)for(const mesh of cloth.back)paintCloth(ctx,mesh,cloth.wrapAlpha*.82,true);
    const result=enemyDraw.call(this,ctx,...args);
    if(cloth){for(const mesh of cloth.front)paintCloth(ctx,mesh,cloth.wrapAlpha);paintCloth(ctx,cloth.tail,cloth.wrapAlpha*.85);}
    return result;
  };
  const previousAir=C.drawAirFields;
  function drawFrontSpiral(ctx,f){
    if(f.kind!=='lee-lotus'||elite(f.target)||!['suspend','descent'].includes(f.phase))return;
    const dive=f.phase==='descent',p=dive?f.phaseAge/f.durations.descent:f.phaseAge/f.durations.suspend;
    if(!dive&&p<.45)return;
    const rotation=f.age*(dive?36:16),x=f.target.x,y=f.target.y-f.targetLift-(f.target.bodyH||24)*.45;
    ctx.save();ctx.lineWidth=2;ctx.globalAlpha=dive?.65:.4;
    for(let i=0;i<26;i++){
      const u=i/26,v=(i+1)/26,a=rotation+u*Math.PI*5,b=rotation+v*Math.PI*5;
      ctx.strokeStyle=Math.sin(a)>0?'#f0e7cf':'#8f9d83';ctx.beginPath();
      ctx.moveTo(x+Math.cos(a)*(20+u*8),y-24+u*46);
      ctx.lineTo(x+Math.cos(b)*(20+v*8),y-24+v*46);ctx.stroke();
    }
    if(dive){ctx.strokeStyle='#d5e7c4';ctx.globalAlpha=.5;
      for(const side of [-1,1])for(let i=0;i<3;i++){
        const sx=x+side*(32+i*7);ctx.beginPath();ctx.moveTo(sx,y-64-i*5);ctx.lineTo(sx,y-17);ctx.stroke();
      }
    }
    ctx.restore();
  }
  function drawReverseAir(ctx, f) {
    if (f.kind !== 'lee-reverse-lotus') return;
    ctx.save();
    const lift = G.LIFT || 0, scale = f.owner.anim.scale || 1;
    const actorPose = presentationFor(f.owner), lastStrike = f.strikes.at(-1);
    if (f.phase === 'combo' && actorPose && lastStrike) {
      const x=f.owner.x+actorPose.offsetX,y=f.owner.y-f.visualLift+actorPose.offsetY-lift;
      const dx=x-lastStrike.x,dy=y-(lastStrike.y-lift),distance=Math.hypot(dx,dy);
      if (distance>18) {
        const ux=dx/distance,uy=dy/distance,length=Math.min(76,distance);
        ctx.globalAlpha=.5;ctx.strokeStyle='#b8db9c';ctx.lineWidth=2;
        for(let i=-1;i<=1;i++){
          const sx=x-uy*i*7,sy=y-28+ux*i*7;
          ctx.beginPath();ctx.moveTo(sx-ux*length,sy-uy*length);ctx.lineTo(sx-ux*12,sy-uy*12);ctx.stroke();
        }
      }
    }
    for (const strike of f.strikes) {
      const age = f.age - strike.age;
      if (age < 0 || age > .18) continue;
      const fade = 1 - age / .18;
      window.AnimationAssets?.draw(ctx, strike.key, strike.frame, strike.x, strike.y - lift,
        { scale, mirror: strike.mirror, rotation: strike.rotation, alpha: fade * .3 });
      // Small contact stars and tapered streaks follow real hit events only.
      const x = strike.tx, y = strike.ty - lift;
      const angle = strike.rotation + (strike.mirror ? Math.PI : 0);
      const dx = Math.cos(angle), dy = Math.sin(angle), nx = -dy, ny = dx;
      ctx.globalAlpha = fade;
      ctx.fillStyle = '#fff5cd';
      ctx.beginPath();ctx.moveTo(x - 13, y);ctx.lineTo(x - 3, y - 3);
      ctx.lineTo(x, y - 13);ctx.lineTo(x + 3, y - 3);ctx.lineTo(x + 13, y);
      ctx.lineTo(x + 3, y + 3);ctx.lineTo(x, y + 10);ctx.lineTo(x - 3, y + 3);ctx.closePath();ctx.fill();
      ctx.strokeStyle = '#b5e783';ctx.lineWidth = 2;
      for (let i = 0; i < 3; i++) {
        const sx = x + nx * (i - 1) * 8, sy = y + ny * (i - 1) * 8;
        ctx.beginPath();ctx.moveTo(sx - dx * (24 + age * 90), sy - dy * (24 + age * 90));
        ctx.lineTo(sx - dx * 6, sy - dy * 6);ctx.stroke();
      }
    }
    if (['lift', 'combo', 'descent'].includes(f.phase)) {
      const plunge = f.phase === 'descent', progress = plunge ? f.phaseAge / f.durations.descent : 0;
      const power = plunge ? Math.max(0, (progress - .18) / .82) : .28;
      const victim = victimPose(f);
      const x = f.target.x + (victim?.offsetX || 0), y = f.target.y + (victim?.offsetY || 0) - lift - f.targetLift - 22;
      ctx.globalAlpha = .25 + power * .45;ctx.strokeStyle = plunge ? '#fff4ce' : '#a9d887';ctx.lineWidth = 2;
      for (let i = 0; i < 7; i++) {
        const sx = x + (i - 3) * 12, length = 9 + power * 37 + (i % 3) * 5;
        ctx.beginPath();ctx.moveTo(sx, y - length - 8);ctx.lineTo(sx, y - 8);ctx.stroke();
      }
    }
    ctx.restore();
  }
  const previousGround = C.drawGroundFields;
  C.drawGroundFields = function(ctx) {
    previousGround.call(this, ctx);
    for (const f of chains.values()) {
      if (!valid(f) || !supports(f.kind) || !['slam', 'recovery'].includes(f.phase)) continue;
      const age = f.phase === 'slam' ? f.phaseAge : f.durations.slam + f.phaseAge;
      const p = Math.min(1, age / (f.durations.slam + f.durations.recovery));
      const radius = f.move.radius || 100, x = f.target.x, y = f.target.y;
      ctx.save();ctx.globalAlpha = (1 - p) * .8;ctx.lineWidth = 2;ctx.strokeStyle = '#18291e';
      for (let i = 0; i < 9; i++) {
        const angle = i * Math.PI * 2 / 9, length = radius * (.45 + (i % 3) * .12);
        ctx.beginPath();ctx.moveTo(x + Math.cos(angle) * 9, y + Math.sin(angle) * 9);
        ctx.lineTo(x + Math.cos(angle + .13) * length * .55, y + Math.sin(angle + .13) * length * .55);
        ctx.lineTo(x + Math.cos(angle) * length, y + Math.sin(angle) * length);ctx.stroke();
        const r = radius * Math.min(1, .25 + p * 1.8);
        ctx.fillStyle = i % 2 ? '#b8a57a' : '#dfcda1';
        ctx.fillRect(Math.round(x + Math.cos(angle) * r), Math.round(y + Math.sin(angle) * r - Math.sin(p * Math.PI) * 15), 4, 3);
      }
      ctx.strokeStyle = '#e3d5a6';ctx.globalAlpha *= .65;
      ctx.beginPath();ctx.arc(x, y, radius * Math.min(1, .2 + p * 2.8), 0, Math.PI * 2);ctx.stroke();ctx.restore();
    }
  };
  C.drawAirFields=function(ctx){
    previousAir.call(this,ctx);
    for(const f of chains.values()){
      if(!valid(f))continue;
      drawFrontSpiral(ctx,f);
      drawReverseAir(ctx, f);
      if(['approach','windup','lift','suspend','combo','descent'].includes(f.phase)){
        for(const cloth of clothVisuals(f))paintCloth(ctx,cloth.bridge,cloth.bridgeAlpha);
      }else if(f.phase==='slam'&&f.phaseAge<.12){
        const progress=clothClamp(f.phaseAge/.12);
        for(const released of f.clothRelease||[]){
          const points=[];
          for(let i=0;i<=9;i++){
            const u=i/9,angle=u*4.7+released.seed*.1+progress*2;
            points.push([released.x+released.r*.6+u*(5+progress*12)+Math.sin(angle)*3*u,
              released.y+u*5-progress*4+progress*progress*9+Math.cos(angle)*2*u]);
          }
          paintCloth(ctx,clothMesh(points,2*(1-progress*.6),released.seed),1-progress);
        }
      }
    }
  };
  const previousTick = C.tick;
  C.tick = function(dt, owner, now) {
    // Let a ready Lotus start first. Its complete contact sequence owns the body.
    const result = previousTick.call(this, dt, owner, now);
    if (G.Game.state !== 'playing' || !(dt > 0) || activeFor(owner) || G.NarutoPursuit?.activeFor(owner) || owner?.dex !== 30006 ||
        !valid({ owner, world: G.World }) ||
        !owner.activeGroup().some(move => supports(move.digiMode) && move.t > 0)) return result;
    let basic = basics.get(owner);
    if (!basic || basic.world !== G.World) {
      const move = G.Moves.instance('tackle');
      move.name = '體術普攻'; move.type = 'fighting';
      basic = { world: G.World, move }; basics.set(owner, basic);
    }
    const target = targetFor(owner, { range: basic.move.radius });
    if (!target) { basic.move.t = Math.max(0, basic.move.t - dt); return result; }
    const activeGroup = owner.activeGroup, selectedTarget = owner.target;
    owner.activeGroup = () => [basic.move]; owner.target = target;
    owner.aim = Math.atan2(target.y - owner.y, target.x - owner.x);
    try { previousTick.call(this, dt, owner, now); }
    finally { owner.activeGroup = activeGroup; owner.target = selectedTarget; }
    return result;
  };
  const previousUpdate = C.updateFields, previousClear = C.clearFields;
  C.updateFields = function(dt) { const result = previousUpdate.call(this, dt); update(dt); return result; };
  C.clearFields = function(owner) { previousClear.call(this, owner); clear(owner); };
  if (G.DigimonSkills?.clear) { const previous = G.DigimonSkills.clear; G.DigimonSkills.clear = owner => { previous(owner); clear(owner); }; }
  const comboSummary = () => {
    const chain = activeFor(G.Game.player), finalSummary = summaries.get(G.Game.player);
    const f = valid(chain) && chain.kind === 'lee-reverse-lotus' && chain.totalHits ? chain : finalSummary;
    return valid(f) ? Object.freeze({ totalDamage: f.totalDamage, totalHits: f.totalHits,
      pendingDeath: !!f.pendingDeath, finished: f === finalSummary }) : null;
  };
  const drawHud = G.HUD.draw;
  G.HUD.draw = function(ctx, w, h, owner, stats) {
    drawHud.call(this, ctx, w, h, owner, stats);
    const summary = owner === G.Game.player && comboSummary();
    if (!summary) return;
    const groupCount = owner.slots.length + owner.moves.filter(move => move.passive && !owner.slots.some(group => group.includes(move))).length;
    const controls = G.Touch.active ? G.Touch.controlLayout(w, h, Math.max(1, groupCount)) : null;
    const y = controls ? controls.bar.y - 16 : h - 110;
    ctx.save(); ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = `bold ${controls ? 16 : 18}px "Segoe UI",system-ui,sans-serif`; ctx.lineWidth = 4; ctx.strokeStyle = '#101627'; ctx.fillStyle = '#ffe0a3';
    const text = `${summary.totalHits} 連擊｜總傷害 ${summary.totalDamage.toLocaleString('zh-TW')}`;
    ctx.strokeText(text, w / 2, y, w - 24); ctx.fillText(text, w / 2, y, w - 24); ctx.restore();
  };
  G.NarutoLee = { bindLimitOf, bound, supports, canCast, cast, clear, update, liftFor, hitLiftFor, isInvulnerable, pendingDefeat, presentationFor, victimPresentationFor,
    get comboSummary() { return comboSummary(); }, activeFor, get active() { return activeFor(G.Game.player); } };
})();
