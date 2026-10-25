/* Level-based Chidori pursuit is this edition's gameplay adaptation. */
(() => {
  if (G.NarutoChidori) return;
  const config = Object.freeze({ counts: Object.freeze([5,10,15,18,22]), minCooldown: .5, followupRange: 340, endInvulnerability: .3, flashDuration: .09,
    speed: 1000, speedStep: .15, maxSpeedMultiplier: 3, damageStep: .05,
    retargetDelay: .045, retargetDelayDecay: .85, minRetargetDelay: .012, screenPadding: 48, returnDuration: .12, step: 4 });
  const limitOf = (move,owner=G.Game.player) => {
    const base=config.counts[Math.max(0,Math.min(config.counts.length-1,(move?.lvl|0)-1))];
    return G.Quantity?.countAtCast(owner,move,base) ?? base;
  };
  const chains = new Map(), flashes = new Map();
  const activeFor = owner => chains.get(owner) || null;
  const controlled = owner => owner === G.Game.player || !!G.SelfClones?.isControlled(owner);
  const valid = c => c && controlled(c.owner) && c.world === G.World && !c.owner.dead && c.owner.hp > 0;
  const clear = owner => {
    for (const [actor] of chains) if (!owner || actor === owner) { actor.svx = actor.svy = 0; chains.delete(actor); }
    for (const actor of flashes.keys()) if (!owner || actor === owner) flashes.delete(actor);
  };
  function complete(c) {
    if(activeFor(c.owner)!==c)return;
    if(valid(c)&&c.dashes>0){
      c.owner.invuln=Math.max(c.owner.invuln||0,config.endInvulnerability);
      const learned=c.owner.moves.find(move=>move.id===c.move.id);
      if(learned)learned.t=Math.max(learned.t||0,config.minCooldown);
    }
    clear(c.owner);
  }
  function end(c) {
    if(activeFor(c.owner)!==c)return;
    if(!valid(c)||!c.dashes){clear(c.owner);return;}
    if(c.phase==='return')return;
    c.phase='return';c.returnFrom={x:c.owner.x,y:c.owner.y};c.returnAge=0;
    c.owner.svx=c.owner.svy=0;
  }
  const targetAlive = e => e && !e.dead && e.hp > 0 && G.EnemyMgr.all().includes(e);
  const inViewport = (e,camera) => Math.abs(e.x-camera.x)<=G.Camera.w/2+config.screenPadding && Math.abs(e.y-camera.y)<=G.Camera.h/2+config.screenPadding;
  const rangeFor = c => c.hitCount ? config.followupRange : c.move.range;
  const rangeOrigin = c => c.hitCount ? c.origin : (c.dashOrigin || c.owner);
  function next(c) {
    const pl = c.owner;
    const candidates=G.EnemyMgr.all().filter(e => targetAlive(e) && inViewport(e,c.camera) && e!==c.lastTarget && (!pl.sourceOwner || Math.hypot(e.x-pl.sourceOwner.x,e.y-pl.sourceOwner.y)<=(G.SelfClones?.leash?.soft??Infinity)) && Math.hypot(e.x-rangeOrigin(c).x,e.y-rangeOrigin(c).y) <= rangeFor(c))
      .sort((a,b) => Math.hypot(a.x-pl.x,a.y-pl.y)-Math.hypot(b.x-pl.x,b.y-pl.y));
    return pl!==G.Game.player&&!c.hitCount&&candidates.includes(pl.target)?pl.target:candidates[0];
  }
  const lockedTargetValid = c => targetAlive(c.target) && inViewport(c.target,c.camera) &&
    Math.hypot(c.target.x-rangeOrigin(c).x,c.target.y-rangeOrigin(c).y) <= rangeFor(c);
  function aimAt(c, target, initial=false) {
    if (!target || c.dashes >= c.limit) { end(c); return; }
    c.target=target;c.dashOrigin=null;c.legRange=rangeFor(c);
    c.phase=initial?'charge':'retarget';
    c.telegraphDuration=initial?(c.move.charge||0):c.retargetDelay;
    c.wait=c.telegraphDuration;
    c.owner.aim=Math.atan2(target.y-c.owner.y,target.x-c.owner.x);
    c.owner.svx=c.owner.svy=0;
  }
  function begin(c) {
    if (!lockedTargetValid(c)) { aimAt(c,next(c)); return; }
    if (!c.dashes) c.origin={x:c.owner.x,y:c.owner.y};
    c.legRange=c.hitCount ? config.followupRange*2 : rangeFor(c);c.dashOrigin={x:c.owner.x,y:c.owner.y};
    c.speed=config.speed*Math.min(config.maxSpeedMultiplier,1+c.hitCount*config.speedStep);
    c.dashes++;c.travel=0;c.phase='dash';
    flashes.set(c.owner,{owner:c.owner,world:c.world,dashes:c.dashes,age:0,
      start:{...c.dashOrigin},target:{x:c.target.x,y:c.target.y,dex:c.target.dex},telegraph:null});
    c.owner.cast(c.move);
  }
  function finish(c) {
    if (c.dashes >= c.limit) { end(c); return; }
    c.retargetDelay=Math.max(config.minRetargetDelay,config.retargetDelay*Math.pow(config.retargetDelayDecay,c.hitCount));
    aimAt(c,next(c));
  }
  function hit(c, e, dx, dy) {
    const damageMultiplier=Math.pow(1+config.damageStep,c.hitCount);
    c.hitCount++;c.lastTarget=e;
    const m=c.move, pl=c.owner, k=G.Types.mult(m.type,e.types), crit=pl.critChance>0&&Math.random()<pl.critChance;
    const dmg=m.dmg*c.attack*damageMultiplier*k*G.Weather.mult(m.type)*(crit?1.5:1)*(G.NarutoSupport?.precisionMultiplier(pl,e)||1);
    e.hurt(dmg,'#9feaff',dx,dy,m.knock||0,crit?'crit':G.Types.label(k),pl,m.id);
    pl.onDealt(dmg); pl.dmgDealt+=dmg;
    G.DamageSplash?.hit(pl, e, dmg, '#9feaff', m.id);
    if(m.slow)e.applySlow(m.slow);
    G.FX.slash(pl.x,pl.y-G.LIFT*.5,pl.aim,34,2.2,'#9feaff',m.digiVis);
    finish(c);
  }
  function updateChain(c,dt) {
    if(!valid(c)){clear(c.owner);return;}
    if(c.phase==='return') {
      c.returnAge=Math.min(config.returnDuration,c.returnAge+dt);
      const t=c.returnAge/config.returnDuration;
      c.owner.x=c.returnFrom.x+(c.origin.x-c.returnFrom.x)*t;
      c.owner.y=c.returnFrom.y+(c.origin.y-c.returnFrom.y)*t;
      c.owner.svx=c.owner.svy=0;
      if(t>=1){c.owner.x=c.origin.x;c.owner.y=c.origin.y;complete(c);}
      return;
    }
    if(c.phase!=='dash') {
      if(!lockedTargetValid(c)){aimAt(c,next(c),c.phase==='charge');return;}
      c.owner.aim=Math.atan2(c.target.y-c.owner.y,c.target.x-c.owner.x);
      const waiting=Math.max(0,c.wait);c.wait-=dt;
      if(c.wait>1e-9)return;
      begin(c);dt=Math.max(0,dt-waiting);
      if(c.phase!=='dash'||dt<=0)return;
    }
    if(!lockedTargetValid(c)){finish(c);return;}
    const pl=c.owner,m=c.move,e=c.target;
    let budget=Math.min(c.speed*dt,c.legRange-c.travel);
    while(budget>0&&activeFor(c.owner)===c&&c.phase==='dash') {
      const dx=e.x-pl.x,dy=e.y-pl.y,d=Math.hypot(dx,dy),reach=m.width*.5+(e.r||0);
      if(d<=reach+.001){hit(c,e,dx,dy);break;}
      const step=Math.min(config.step,budget,d-reach),ux=dx/d,uy=dy/d;
      const x=pl.x+ux*step,y=pl.y+uy*step;
      pl.x=x;pl.y=y;c.travel+=step;budget-=step;
      pl.aim=pl.moveAngle=Math.atan2(dy,dx);pl.attackFace=.15;pl.anim.dir=G.Sprites.dirFromAngle(pl.aim);
      c.trail+=step;
      if(c.trail>=20){c.trail=0;G.FX.sp('bolt','naruto-blue',x,y-G.LIFT,{life:.13,scale:.7,angle:pl.aim});}
    }
    if(activeFor(c.owner)===c&&c.phase==='dash'){
      if(Math.hypot(e.x-pl.x,e.y-pl.y)<=m.width*.5+(e.r||0)+.001)hit(c,e,e.x-pl.x,e.y-pl.y);
      else if(c.travel>=c.legRange-.001)end(c);
    }
  }
  function update(dt) {
    if(!(dt>0)||!Number.isFinite(dt))return;
    for(const [owner,flash] of flashes)if((flash.age+=dt)>=config.flashDuration||!valid(flash))flashes.delete(owner);
    for (const c of [...chains.values()]) updateChain(c,dt);
  }
  const canCast = (pl,m) => controlled(pl) && pl.dex === 30002 && !pl.dead && pl.hp > 0 && !activeFor(pl) && !(G.NarutoFireball?.activeFor?.(pl) || (pl === G.Game.player && G.NarutoFireball?.active)) &&
    G.EnemyMgr.all().some(e=>targetAlive(e)&&inViewport(e,G.Camera)&&Math.hypot(e.x-pl.x,e.y-pl.y)<=(m?.range||170));
  function cast(pl,m) {
    if(!canCast(pl,m))return false;
    const c={owner:pl,world:G.World,move:{...m,digiVis:{...m.digiVis}},limit:limitOf(m,pl),attack:pl.atk,hitCount:0,lastTarget:null,dashes:0,trail:0,
      origin:{x:pl.x,y:pl.y},camera:{x:G.Camera.x,y:G.Camera.y},chargeDistance:0,chargeMoving:false,
      speed:config.speed,retargetDelay:config.retargetDelay,phase:'charge',wait:Math.max(0,m.charge||0)};
    const first=next(c);if(!first)return false;
    aimAt(c,first,true);
    chains.set(pl,c);pl.svx=pl.svy=0;if(pl===G.Game.player)holdCamera(c);
    if(c.wait<=0)begin(c);return true;
  }
  function poseFor(animator){
    const c=[...chains.values()].find(c=>c.owner.anim===animator);
    if(!valid(c))return null;
    const source=G.Naruto.records.get(30002).pixel.chidori;
    if(!source)return null;
    const charging=['charge','retarget'].includes(c.phase),duration=Math.max(.001,c.telegraphDuration||c.move.charge||0);
    const index=Math.min(source.chargeFrames.length-1,Math.floor(Math.max(0,1-c.wait/duration)*source.chargeFrames.length));
    const frame=charging?source.chargeFrames[index]:source.dashFrame;
    const dir=G.Sprites.dirFromAngle(c.owner.aim),direction=['down','right','right','right','up','left','left','left'][dir];
    return {...frame,direction,mirror:source.mirror.includes(direction),action:true};
  }
  // Flight immunity never overwrites independent timers, including lava's reset.
  const hurt=G.Player.prototype.hurt, playerUpdate=G.Player.prototype.update;
  G.Player.prototype.hurt=function(...args){const c=activeFor(this);if(valid(c)&&['dash','return'].includes(c.phase))return;return hurt.apply(this,args);};
  G.Player.prototype.update=function(dt){
    const c=activeFor(this);
    if(c&&!valid(c))clear(this);
    if(!activeFor(this))return playerUpdate.call(this,dt);
    if(c.phase==='charge'){
      const x=this.x,y=this.y,result=playerUpdate.call(this,dt);
      const distance=Math.hypot(this.x-x,this.y-y);
      c.chargeMoving=distance>.001;
      c.chargeDistance+=distance;
      return result;
    }
    const frozen=this.frozen,x=this.x,y=this.y;this.frozen=true;this.svx=this.svy=0;
    // Dash movement owns position, including passage through solid scenery.
    try{return playerUpdate.call(this,dt);}finally{this.x=x;this.y=y;this.frozen=frozen;}
  };
  const setActive=G.Player.prototype.setActive;
  G.Player.prototype.setActive=function(...args){
    const result=setActive.apply(this,args),c=activeFor(this);
    if(c&&!this.activeGroup().some(move=>move.id===c.move.id))clear(this);
    return result;
  };
  function holdCamera(c) {Object.assign(G.Camera,{x:c.camera.x,y:c.camera.y,shake:0,_sx:0,_sy:0});}
  const follow=G.Camera.follow,kick=G.Camera.kick;
  G.Camera.follow=function(...args){
    const chain=activeFor(G.Game.player);
    if(chain&&!valid(chain))clear(G.Game.player);
    const result=follow.apply(this,args);
    if(valid(chain)&&chain.phase==='charge'){
      chain.camera={x:G.Camera.x,y:G.Camera.y};return result;
    }
    if(valid(chain))holdCamera(chain);
    return result;
  };
  G.Camera.kick=function(...args){const chain=activeFor(G.Game.player);if(valid(chain)){holdCamera(chain);return;}return kick.apply(this,args);};
  const C=G.Combat,oldUpdate=C.updateFields,oldClear=C.clearFields,oldAir=C.drawAirFields,oldGround=C.drawGroundFields;
  let rangeVisual = null;
  const rangeCohorts = new Map();
  // Josh Jersild, "Lightning Bolts": displaced midpoints, halved offsets,
  // shorter stochastic forks and two staggered generations. CPU canvas only.
  // https://www.drilian.com/posts/2009.02.25-lightning-bolts/
  function rangeCohort(radius, scale, generation) {
    const key = `${radius}:${scale}:${generation}`;
    if (rangeCohorts.has(key)) return rangeCohorts.get(key);
    const random = (index, salt) => G.U.hash(index, salt, generation + 731);
    const paths = [], roots = 3 + Math.floor(random(1, 3) * 3), TAU = Math.PI * 2;
    const rotation = random(1, 7) * TAU;
    const bound = point => {
      const distance = Math.hypot(...point), limit = radius * .998;
      return distance > limit ? point.map(value => value * limit / distance) : point;
    };
    for (let root = 0; root < roots; root++) {
      const angle = rotation + (root + (random(root, 11) - .5) * .65) * TAU / roots;
      const reach = root < 2 ? radius : radius * (.64 + random(root, 13) * .36);
      const origin = [Math.cos(angle) * 10 / scale, Math.sin(angle) * 10 / scale];
      const end = [Math.cos(angle) * reach, Math.sin(angle) * reach];
      const pending = [], main = { points: [origin], level: 0 };
      // At most 16 main + 32 fork segments per root, five roots per cohort:
      // 240 per cohort and 480 for both generations combined.
      let forkBudget = 32;
      function split(left, right, depth, offset, seed, points, level) {
        if (!depth) { points.push(right); return; }
        const dx = right[0] - left[0], dy = right[1] - left[1], distance = Math.max(.001, Math.hypot(dx, dy));
        const shift = (random(seed, depth + 31) * 2 - 1) * offset;
        const middle = bound([(left[0] + right[0]) / 2 - dy / distance * shift,
          (left[1] + right[1]) / 2 + dx / distance * shift]);
        split(left, middle, depth - 1, offset / 2, seed * 2 + 1, points, level);
        split(middle, right, depth - 1, offset / 2, seed * 2 + 2, points, level);
        if (depth < 2 || level >= 2 || random(seed, 47) > .32) return;
        const branchDepth = Math.min(2, depth - 1), cost = 1 << branchDepth;
        if (forkBudget < cost) return;
        forkBudget -= cost;
        const turn = (random(seed, 53) > .5 ? 1 : -1) * (.32 + random(seed, 59) * .55);
        const length = .5 + random(seed, 61) * .25;
        const bx = (middle[0] - left[0]) * length, by = (middle[1] - left[1]) * length;
        const tip = bound([middle[0] + bx * Math.cos(turn) - by * Math.sin(turn),
          middle[1] + bx * Math.sin(turn) + by * Math.cos(turn)]);
        pending.push({ start: middle, end: tip, depth: branchDepth, offset: offset / 2,
          seed: seed + 1009, level: level + 1 });
      }
      split(origin, end, 4, 22 / scale, root + 101, main.points, 0);
      paths.push(main);
      for (let i = 0; i < pending.length; i++) {
        const fork = pending[i], path = { points: [fork.start], level: fork.level };
        split(fork.start, fork.end, fork.depth, fork.offset, fork.seed, path.points, fork.level);
        paths.push(path);
      }
    }
    const cohort = { key, paths };
    rangeCohorts.set(key, cohort);
    return cohort;
  }
  function chakraRange(radius, scale, time) {
    const frame = Math.floor(time * 10), key = `${radius}:${scale}:${frame}`;
    if (rangeVisual?.key === key) return rangeVisual;
    const now = frame / 10, latest = Math.floor(now / 1.2), arcs = [], keep = new Set();
    for (const generation of [latest - 1, latest]) {
      const cohort = rangeCohort(radius, scale, generation), age = now - generation * 1.2;
      keep.add(cohort.key);
      const opacity = .22 * Math.sin(Math.PI * age / 2.4) ** 2;
      if (opacity < .004) continue;
      const reveal = radius * Math.min(1, .12 + age / .45);
      for (const line of cohort.paths) {
        if (Math.hypot(...line.points[0]) > reveal) continue;
        const path = new Path2D();path.moveTo(...line.points[0]);
        for (let i = 1; i < line.points.length; i++) {
          const point = line.points[i], previous = line.points[i - 1];
          if (Math.hypot(...point) > reveal) {
            // Solve the intersection so the advancing tip stops at the reveal radius.
            const dx = point[0] - previous[0], dy = point[1] - previous[1];
            const a = dx * dx + dy * dy, b = 2 * (previous[0] * dx + previous[1] * dy);
            const c = previous[0] ** 2 + previous[1] ** 2 - reveal ** 2;
            const t = Math.max(0, Math.min(1, (-b + Math.sqrt(Math.max(0, b * b - 4 * a * c))) / (2 * a)));
            path.lineTo(previous[0] + dx * t, previous[1] + dy * t);break;
          }
          path.lineTo(...point);
        }
        arcs.push({ path, level: line.level, opacity: opacity * .6 ** line.level });
      }
    }
    for (const cached of rangeCohorts.keys()) if (!keep.has(cached)) rangeCohorts.delete(cached);
    rangeVisual = { key, arcs };
    return rangeVisual;
  }
  C.drawGroundFields=function(ctx){
    oldGround.call(this,ctx);
    const owner=G.Game.player,move=owner?.activeGroup().find(m=>m.digiMode==='chidori-chain');
    if(owner?.mon?.dex!==30002||owner.dead||!move)return;
    const scale=G.Camera.scale||1,time=G.Settings?.get('calm')?1.8:performance.now()/1000;
    const visual=chakraRange(move.range,scale,time);
    const chain=activeFor(owner),anchor=valid(chain)?chain.origin:owner;
    ctx.save();ctx.translate(anchor.x,anchor.y);ctx.lineJoin='round';ctx.lineCap='round';
    ctx.beginPath();ctx.arc(0,0,move.range,0,Math.PI*2);ctx.clip();
    ctx.shadowBlur=0;ctx.strokeStyle='#fff0bd';
    for (const arc of visual.arcs) {
      ctx.globalAlpha=arc.opacity;ctx.lineWidth=(arc.level ? .65 : 1.05)/scale;ctx.stroke(arc.path);
    }
    ctx.restore();
  };
  C.updateFields=function(dt){oldUpdate.call(this,dt);update(dt);};
  C.clearFields=function(owner){oldClear.call(this,owner);clear(owner);};
  const clearSkills=G.DigimonSkills.clear;
  G.DigimonSkills.clear=function(owner){clearSkills(owner);clear(owner);};
  function targetTelegraph(c,scale) {
    // Purely visual bolt: both endpoints snapshot at emission, never combat targets.
    if(!c.telegraph){
      const seed=(c.target.dex||0)+(c.target.x|0)+(c.dashes+1)*71;
      const noise=(i,salt)=>G.U.hash(i,salt,seed),forks=[];
      function split(a,b,depth,offset,id,points,branch=false){
        if(!depth){points.push(b);return;}
        const m=[(a[0]+b[0])/2,(a[1]+b[1])/2+(noise(id,31)-.5)*offset];
        split(a,m,depth-1,offset/2,id*2+1,points,branch);
        split(m,b,depth-1,offset/2,id*2+2,points,branch);
        if(!branch&&depth>=3&&noise(id,47)<.65){
          const end=[Math.min(.97,m[0]+.08+noise(id,53)*.1),m[1]+(noise(id,59)>.5?1:-1)*(4+noise(id,61)*6)];
          const points=[m];split(m,end,2,3,id+301,points,true);forks.push(points);
        }
      }
      const points=[[0,0]];split(points[0],[1,0],5,22,1,points);
      c.telegraph={points,forks};
    }
    const t=c.telegraph,pl=c.start,e=c.target,reveal=1;
    const key=[pl.x,pl.y,e.x,e.y,scale,Math.floor(reveal*10)].join(':');
    if(t.key===key)return t;
    const main=new Path2D(),branches=new Path2D(),dx=e.x-pl.x,dy=e.y-pl.y,d=Math.max(.001,Math.hypot(dx,dy));
    const position=([u,v])=>[pl.x+dx*u-dy/d*v/scale,pl.y-G.LIFT*.5+dy*u+dx/d*v/scale];
    function trace(path,points){
      if(points[0][0]>reveal)return;
      path.moveTo(...position(points[0]));
      for(let i=1;i<points.length;i++){
        const p=points[i],previous=points[i-1];
        if(p[0]>reveal){const mix=(reveal-previous[0])/(p[0]-previous[0]);path.lineTo(...position([reveal,previous[1]+(p[1]-previous[1])*mix]));break;}
        path.lineTo(...position(p));
      }
    }
    trace(main,t.points);for(const fork of t.forks)trace(branches,fork);
    Object.assign(t,{key,main,branches});return t;
  }
  function drawTelegraphs(ctx){
    for(const flash of flashes.values()){
      if(!valid(flash)||flash.age>=config.flashDuration)continue;
      const scale=G.Camera.scale||1,t=targetTelegraph(flash,scale);
      const fade=1-flash.age/config.flashDuration;
      ctx.save();ctx.lineJoin=ctx.lineCap='round';ctx.shadowBlur=0;
      ctx.strokeStyle='#bc861c';ctx.lineWidth=3/scale;ctx.globalAlpha=.24*fade;ctx.stroke(t.main);
      ctx.strokeStyle='#ffe878';ctx.lineWidth=1.65/scale;ctx.globalAlpha=.82*fade;ctx.stroke(t.main);
      ctx.lineWidth=.9/scale;ctx.globalAlpha=.46*fade;ctx.stroke(t.branches);ctx.restore();
    }
  }
  C.drawAirFields=function(ctx){oldAir.call(this,ctx);drawTelegraphs(ctx);for(const chain of chains.values())if(valid(chain)&&['dash','return'].includes(chain.phase)){
    const p=chain.owner,pose=poseFor(p.anim),stand=G.Naruto.records.get(30002).pixel.frames.down[0];
    const k=64*p.anim.scale/stand[3],mirror=pose?.mirror?-1:1;
    const x=pose?.hand?p.x+(pose.hand[0]-pose.anchor[0])*k*mirror:p.x+Math.cos(p.aim)*18;
    const y=pose?.hand?p.y+(pose.hand[1]-pose.anchor[1])*k:p.y-G.LIFT+Math.sin(p.aim)*18;
    G.VFX.draw(ctx,'bolt','naruto-blue',x,y,{scale:1.25,angle:p.aim,frame:Math.floor(performance.now()/65)});
  }};
  G.NarutoChidori={config,limitOf,poseFor,supports:mode=>mode==='chidori-chain',canCast,cast,clear,update,activeFor,get active(){return activeFor(G.Game.player);}};
})();
