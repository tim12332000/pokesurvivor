/* Kimimaro's actor-owned bone techniques. Rendering is provided by KimimaroArt. */
(() => {
  'use strict';
  if (G.NarutoKimimaro) return;
  const DEX = 30012, BASIC = 'naruto-kimimaro', CURSE = BASIC + '-curse', BONE_GUARD = BASIC + '-bone-guard', BOOMERANG = BASIC + '-boomerang';
  const C = G.Combat, TAU = Math.PI * 2, EPS = 1e-8;
  const states = new Map(), heldTargets = new Map(), cloneSpeedInstalled = new WeakSet();
  let evolutions = new WeakMap();
  let nextCast = 1;
  const specs = {
    willow: { duration: .64, damage: 30, range: [110,120,130,140,150] },
    camellia: { duration: .74, damage: 120, range: [220,240,260,280,300], width: [40,44,48,52,56] },
    bullets: { duration: .60, damage: 45, range: [380,400,420,440,460] },
    larch: { duration: .70, damage: 96, radius: [125,135,145,155,165] },
    vine: { duration: .70, damage: 48, range: [320,340,360,380,400] },
    flower: { duration: .86, damage: 192, range: [220,240,260,280,300], width: [42,46,50,54,58] },
    lily: { duration: .90, damage: 100, radius: [200,220,240,260,280] },
    bracken: { duration: 3.20, damage: 600, radius: [400,450,500,550,600], waves: [.48,.80,1.12,1.44,1.76,2.08] },
    curse: { duration: 1, damage: 0, range: [220,220,220,220,220] }
  };
  const finite = (n, fallback = 0) => Number.isFinite(n) ? n : fallback;
  const rank = m => Math.max(1, Math.min(5, Math.floor(m?.lvl || 1)));
  const alive = a => !!a && !a.dead && a.hp > 0;
  const controlled = owner => G.SelfClones?.isControlled?.(owner) ?? owner === G.Game.player;
  const validOwner = owner => alive(owner) && controlled(owner) && (owner.mon?.dex ?? owner.dex) === DEX;
  const special = e => !!(e.boss || e.elite || e.legend || e.judge || e.remote);
  const jumping = e => !!(e.jump || (e.jumpLift || 0) > .01);
  const ordinary = e => alive(e) && !special(e) && !e.flying && !jumping(e);
  const modeKind = m => String(m?.digiMode || '').replace(/^kimimaro-/, '');
  const supports = mode => mode==='kimimaro-bone-guard'||mode==='kimimaro-boomerang'||String(mode || '').startsWith('kimimaro-') && !!specs[String(mode).slice(9)];
  const distance2 = (a,b) => (a.x-b.x)**2 + (a.y-b.y)**2;
  const group = owner => owner.activeGroup?.() || [];
  const signature = owner => group(owner).map(m => m.id).join('|');
  const learned = (owner,id) => owner.moves?.find(m => m.id === id);
  const automatic = m => !!specs[modeKind(m)];
  const rangeFor = (m,kind=modeKind(m)) => finite(m?.range, specs[kind]?.range?.[rank(m)-1] || 160);
  const radiusFor = (m,kind=modeKind(m)) => finite(m?.radius, specs[kind]?.radius?.[rank(m)-1] || rangeFor(m,kind));
  const halfWidth = (m,kind=modeKind(m)) => finite(m?.halfWidth, finite(m?.width, (specs[kind]?.width?.[rank(m)-1] || 24)*2)/2);
  const movesAreSelected = (owner,ids) => ids.every(id => group(owner).some(m => m.id === id && owner.moves.includes(m)));
  const requirementsPresent = (owner,ids) => ids.every(id => {
    const m=learned(owner,id);return m && (automatic(m)||movesAreSelected(owner,[id]));
  });

  function state(owner) {
    let s = states.get(owner);
    if (s && s.world !== G.World) { clear(owner); s = null; }
    if (!s) {
      s = {owner,world:G.World,clock:0,action:null,forest:null,bullets:[],impacts:[],
        readySince:new Map(),selection:signature(owner),exitUntil:0,guardUntil:0,guardMove:null,
        curse:{startAt:hasEvolution(owner)?-1:-Infinity,readyAt:0},boneGuard:{readyAt:0,wall:null,blocks:0,triggers:0},
        boomerang:{lanes:[],count:1,launches:0,catches:0,hits:0,pose:null,log:[]},
        castCounts:{},castLog:[],emitted:0,totalDamage:0};
      states.set(owner,s);
      installCloneSpeed(owner);
    }
    return s;
  }
  const terminal = () => G.Game.state === 'ui' || G.Game.state === 'over';
  const validState = s => !!s && !terminal() && s.world === G.World && validOwner(s.owner);
  function clearPath(ax,ay,bx,by,targetProp=null) {
    const steps = Math.min(256,Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/4)));
    for (let i=1;i<=steps;i++) {
      const x=ax+(bx-ax)*i/steps,y=ay+(by-ay)*i/steps;
      if (G.World.isWall(x,y)) return false;
      const prop=G.World.projectileBlock?.(x,y,1);
      if (prop && prop !== targetProp) return false;
    }
    return true;
  }
  function nearby(owner,r,props=false) {
    const found=[...new Set(G.EnemyMgr.queryCircle(owner.x,owner.y,r))].filter(e =>
      alive(e) && !e.friendly && distance2(e,owner)<=r*r && clearPath(owner.x,owner.y,e.x,e.y));
    if (props && !found.length) found.push(...(G.World.propsInCircle?.(owner.x,owner.y,r)||[]).filter(p =>
      p.hp>0 && p.destructible !== false && distance2(p,owner)<=r*r && clearPath(owner.x,owner.y,p.x,p.y,p)));
    return found.sort((a,b)=>distance2(a,owner)-distance2(b,owner));
  }
  function safeLanding(owner,target,aim) {
    const minimum=(owner.r||14)+(target.r||10)+8;
    const preferred=Math.max(minimum,Math.min(60,rangeFor(learned(owner,BASIC)||{},'willow')-8));
    for (const radius of [preferred,minimum,preferred+8]) for (const offset of [0,.18,-.18,.36,-.36]) {
      const x=owner.x+Math.cos(aim+offset)*radius,y=owner.y+Math.sin(aim+offset)*radius;
      if (!G.World.isFree(x,y,target.r||10,true) || !clearPath(target.x,target.y,x,y)) continue;
      const occupied=G.EnemyMgr.queryCircle(x,y,(target.r||10)+24).some(e => e!==target && alive(e) &&
        Math.hypot(e.x-x,e.y-y)<((e.r||8)+(target.r||10))*.8);
      if (!occupied) return {x,y};
    }
    return null;
  }
  function inLine(owner,target,aim,len,width) {
    const dx=target.x-owner.x,dy=target.y-owner.y,c=Math.cos(aim),s=Math.sin(aim);
    const along=dx*c+dy*s;
    return along>=0 && along<=len && Math.abs(-dx*s+dy*c)<=width+(target.r||0) && clearPath(owner.x,owner.y,target.x,target.y);
  }
  function candidates(owner,m) {
    const kind=modeKind(m),r=['larch','lily','bracken'].includes(kind)?radiusFor(m):rangeFor(m,kind);
    let list=nearby(owner,r,kind==='willow');
    if (kind==='bracken') list=list.filter(e => !jumping(e) && (special(e) || !e.flying));
    if (kind==='vine') list=list.filter(e => !heldTargets.has(e) && (!ordinary(e) || safeLanding(owner,e,Math.atan2(e.y-owner.y,e.x-owner.x))));
    if (kind==='flower') list.sort((a,b)=>Number(special(b))-Number(special(a))||distance2(a,owner)-distance2(b,owner));
    return list;
  }
  function targetFor(owner,m) { return candidates(owner,m)[0] || null; }
  function hasEvolution(owner) {
    const evolution=owner&&evolutions.get(owner);
    const valid=!!evolution&&!terminal()&&validOwner(owner)&&!!learned(owner,CURSE)&&
      evolution.world===G.World&&evolution.run===G.Game.st;
    if(evolution&&!valid)evolutions.delete(owner);
    return valid;
  }
  function resetEvolution(owner) {
    if(owner)evolutions.delete(owner);else evolutions=new WeakMap();
    for(const s of states.values())if(!owner||s.owner===owner){
      s.curse={startAt:-Infinity,readyAt:0};
      if(s.action?.kind==='curse')cancel(s,false);
    }
  }
  function curseState(owner=G.Game.player) {
    const s=states.get(owner),m=learned(owner,CURSE),evolved=hasEvolution(owner);
    if (!m || (!validState(s)&&!evolved)) return {active:false,permanent:false,transforming:false,remaining:0,cooldown:0,bonus:0};
    const started=Number.isFinite(s?.curse.startAt),elapsed=s?s.clock-s.curse.startAt:1,active=evolved||(started&&elapsed>=1-EPS);
    return {active,permanent:active,transforming:started&&elapsed>=0&&elapsed<1-EPS,remaining:0,
      cooldown:0,bonus:active?[.10,.125,.15,.175,.20][rank(m)-1]:0,
      startAt:s?.curse.startAt??-1,readyAt:0};
  }
  const damageBonus = owner => 1+curseState(owner).bonus;
  const speedMultiplier = owner => curseState(owner).active?1.1:1;
  function installCloneSpeed(owner) {
    if (!owner.sourceOwner || cloneSpeedInstalled.has(owner)) return;
    const descriptor=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(owner),'spd');
    if (!descriptor?.get) return;
    Object.defineProperty(owner,'spd',{configurable:true,get(){
      return descriptor.get.call(this)/speedMultiplier(this.sourceOwner)*speedMultiplier(this);
    }});
    cloneSpeedInstalled.add(owner);
  }
  function movementLocked(owner) {
    const f=states.get(owner)?.action;
    if (!f || !validState(states.get(owner))) return false;
    const t=f.age;
    return f.kind==='vine' ? t>=.42&&t<.62 : f.kind==='flower' ? t>=.46&&t<.58 :
      f.kind==='combo' ? (t>=.42&&t<.62)||(t>=1&&t<1.12) : f.kind==='bracken' ? t<.30 : false;
  }
  function releaseHold(f) {
    if (f?.hold && heldTargets.get(f.hold.target)===f) heldTargets.delete(f.hold.target);
    if (f) f.hold=null;
  }
  function cancel(s,exit=true) {
    releaseHold(s.action);s.action=null;s.forest=null;s.guardUntil=0;s.guardMove=null;
    if (exit) s.exitUntil=s.clock+.10;
  }
  function held(enemy) {
    const f=heldTargets.get(enemy),s=f&&states.get(f.owner);
    return !!f && validState(s) && s.action===f && ordinary(enemy) && f.hold &&
      f.age>=.42-EPS && f.age<f.hold.releaseAge-EPS;
  }
  function syncSelection(s) {
    const next=signature(s.owner);
    if (next!==s.selection) {s.selection=next;s.readySince.clear();}
    const f=s.action;
    if (f && !requirementsPresent(s.owner,f.requiredIds)) cancel(s);
    if (s.guardMove && !learned(s.owner,s.guardMove)) {s.guardUntil=0;s.guardMove=null;}
  }
  function canCast(owner,m) {
    if (!validOwner(owner) || owner.frozen || G.Game.state!=='playing' || !supports(m?.digiMode)) return false;
    if (m.id===BONE_GUARD||m.id===BOOMERANG) return false;
    const s=state(owner),kind=modeKind(m);
    if (s.committingFlower && kind==='flower') return true;
    if (s.action || s.exitUntil>s.clock+EPS || !learned(owner,m.id)) return false;
    if (kind==='curse') return learned(owner,CURSE) && !Number.isFinite(s.curse.startAt) && nearby(owner,220).length>0;
    return !!(s.scheduledMove?.id===m.id?s.scheduledTarget:targetFor(owner,m));
  }
  function hitTimes(kind,count=4) {
    if (kind==='willow') {
      const gaps=Array.from({length:count-1},(_,i)=>.85**i),sum=gaps.reduce((a,b)=>a+b,0),times=[.12];
      for(const gap of gaps)times.push(times.at(-1)+.48*gap/sum);return times;
    }
    return ({camellia:[.30,.43,.57],bullets:[.16,.23,.30,.37,.44],larch:[.30,.52],vine:[.42],flower:[.58],
      lily:[.32,.62],bracken:specs.bracken.waves,combo:[.42,1.12],curse:[]})[kind]||[];
  }
  function quantity(owner,m,base,cap) {
    return Math.min(cap,Math.max(base,G.Quantity?.countAtCast(owner,m,base) ?? base));
  }
  function comboAvailable(owner,vine,target) {
    const s=state(owner),flower=learned(owner,BASIC+'-flower');
    if (!flower || !learned(owner,vine.id) || (flower.t||0)>EPS) return false;
    const pairSince=Math.min(s.readySince.get(vine)??s.clock,s.readySince.get(flower)??s.clock);
    const older=scheduledMoves(owner).some(m => m!==vine && m!==flower && (m.t||0)<=EPS &&
      (s.readySince.get(m)??s.clock)<pairSince-EPS && scheduledTarget(owner,m));
    if (older) return false;
    if (!ordinary(target)) return inLine(owner,target,Math.atan2(target.y-owner.y,target.x-owner.x),rangeFor(flower),halfWidth(flower));
    return !!safeLanding(owner,target,Math.atan2(target.y-owner.y,target.x-owner.x));
  }
  function cast(owner,m) {
    const s=state(owner),kind=modeKind(m);
    if (s.committingFlower && kind==='flower') {
      const f=s.action;
      f.flowerMove={...m};f.flowerAttack=owner.atk*damageBonus(owner);f.flowerStarted=true;
      f.flowerStartedAt=f.clockStart+.54;
      s.castCounts.flower=(s.castCounts.flower||0)+1;
      s.castLog.push({kind:'flower',time:f.flowerStartedAt,castId:f.castId});if(s.castLog.length>100)s.castLog.shift();
      return true;
    }
    if (!canCast(owner,m)) return false;
    const source=learned(owner,m.id),target=kind==='curse'?null:
      (s.scheduledMove?.id===m.id?s.scheduledTarget:targetFor(owner,m));
    const count=kind==='willow'?quantity(owner,m,4,8):kind==='bullets'?quantity(owner,m,5,15):1;
    const combined=kind==='vine' && comboAvailable(owner,source,target);
    const actualKind=combined?'combo':kind;
    const f={owner,world:G.World,kind:actualKind,baseKind:kind,age:0,aim:target?Math.atan2(target.y-owner.y,target.x-owner.x):(owner.aim||0),
      x:owner.x,y:owner.y,startX:owner.x,startY:owner.y,move:{...m},m:{...m},source,rank:rank(m),
      duration:combined?1.40:specs[kind].duration,target,count,castId:nextCast++,hitTimes:hitTimes(actualKind,count),
      hitIndex:0,hitMarks:[],phaseHits:new Map(),attack:owner.atk*damageBonus(owner),requiredIds:[source.id],
      emitted:0,flowerStarted:false,clockStart:s.clock};
    if (combined) {f.flowerSource=learned(owner,BASIC+'-flower');f.requiredIds.push(f.flowerSource.id);}
    if (kind==='curse') {s.curse.startAt=s.clock;s.curse.readyAt=0;source.t=0;}
    if (kind==='bracken') {
      f.forest={owner,world:G.World,x:f.x,y:f.y,age:0,rank:f.rank,radius:radiusFor(m),castId:f.castId,
        waves:f.hitTimes,duration:f.duration,hitTargets:new Set()};
      s.forest=f.forest;
    }
    s.action=f;s.castCounts[kind]=(s.castCounts[kind]||0)+1;s.readySince.delete(source);
    s.castLog.push({kind,time:s.clock,castId:f.castId});if(s.castLog.length>100)s.castLog.shift();
    owner.aim=f.aim;
    return true;
  }
  function impact(s,f,e,damage,kind=f.kind) {
    const mark={x:e.x,y:e.y,time:s.clock,age:0,damage,kind,target:e,castId:f.castId};
    s.impacts.push(mark);if(s.impacts.length>20)s.impacts.shift();f.hitMarks?.push(mark);
  }
  function hit(s,f,e,share,phase,single=false,move=f.move,attack=f.attack) {
    if (!validState(s) || !alive(e) || !Number.isFinite(share) || share<=0) return 0;
    let seen=f.phaseHits.get(phase);if(!seen){seen=new Set();f.phaseHits.set(phase,seen);}
    if(seen.has(e))return 0;
    const origin=f.kind==='bracken'?f.forest:['bullets','boomerang'].includes(f.baseKind)?f:f.owner;
    if(!clearPath(origin.x,origin.y,e.x,e.y,e.destructible?e:null))return 0;
    seen.add(e);
    const base=finite(move.dmg,specs[f.baseKind]?.damage||30)*share*attack;
    if(e.destructible || typeof e.hurt!=='function') {
      G.World.damageProp(e,base*G.Weather.mult(move.type),'#ece9df');impact(s,f,e,base);return base;
    }
    const mult=G.Types.mult(move.type,e.types),crit=Math.random()<(f.owner.critChance||0);
    let damage=base*mult*G.Weather.mult(move.type)*(crit?1.5:1)*(G.NarutoSupport?.precisionMultiplier(f.owner,e)||1);
    if(f.kind==='bracken')damage=Math.max(damage,Math.ceil(Math.max(0,finite(e.maxHp))*finite(move.minMaxHpFraction,.30)));
    e.hurt(damage,'#eee9dc',e.x-origin.x,e.y-origin.y,0,crit?'crit':G.Types.label(mult),f.owner,move.id);
    f.owner.onDealt(damage);f.owner.dmgDealt+=damage;s.totalDamage+=damage;
    if(single)G.DamageSplash?.hit(f.owner,e,damage,'#eee9dc',move.id);
    impact(s,f,e,damage);return damage;
  }
  function circle(s,f,r,share,phase,ground=false) {
    const center=ground?f.forest:f.owner;
    for(const e of new Set(G.EnemyMgr.queryCircle(center.x,center.y,r))) {
      if(!alive(e)||distance2(e,center)>r*r || (ground&&(jumping(e)||(!special(e)&&e.flying))))continue;
      if(ground&&f.forest.hitTargets.has(e))continue;
      const damage=hit(s,f,e,share,phase,false);
      if(ground&&damage>0)f.forest.hitTargets.add(e);
      if(f.baseKind==='larch'&&phase===1&&damage>0&&alive(e)&&!special(e))push(e,f.owner,35);
    }
    for(const p of G.World.propsInCircle?.(center.x,center.y,r)||[]) {
      if(p.hp>0&&distance2(p,center)<=r*r&&clearPath(center.x,center.y,p.x,p.y,p))hit(s,f,p,share,phase,false);
    }
  }
  function push(e,from,amount) {
    const aim=Math.atan2(e.y-from.y,e.x-from.x),x=e.x,y=e.y;
    for(let i=1;i<=Math.ceil(amount/4);i++) {
      const d=Math.min(amount,i*4),nx=x+Math.cos(aim)*d,ny=y+Math.sin(aim)*d;
      if(!G.World.isFree(nx,ny,e.r||10,true))break;e.x=nx;e.y=ny;
    }
    G.EnemyMgr.rebuildGrid?.();
  }
  function line(s,f,share,phase,flower=false) {
    const m=flower?f.flowerMove||f.move:f.move,attack=flower?f.flowerAttack??f.attack:f.attack;
    const len=rangeFor(m,flower?'flower':'camellia'),width=halfWidth(m,flower?'flower':'camellia');
    const found=nearby(f.owner,len+32).filter(e=>inLine(f.owner,e,f.aim,len,width))
      .sort((a,b)=>distance2(a,f.owner)-distance2(b,f.owner));
    if (flower) {
      let secondary=0;
      for(const e of found)if(e===f.target)hit(s,f,e,share,phase,false,m,attack);
      else if(secondary++<3)hit(s,f,e,share*.5,phase,false,m,attack);
    } else for(const e of found.slice(0,quantity(f.owner,m,4,12)))hit(s,f,e,share,phase,false,m,attack);
    for(const p of G.World.propsInCircle?.(f.owner.x,f.owner.y,len+width)||[]) {
      if(p.hp>0&&inLine(f.owner,p,f.aim,len,width))hit(s,f,p,share,phase,false,m,attack);
    }
  }
  function beginHold(s,f) {
    const e=f.target;
    if(!ordinary(e))return;
    const dest=safeLanding(f.owner,e,f.aim);
    if(!dest)return;
    f.hold={target:e,sx:e.x,sy:e.y,x:dest.x,y:dest.y,releaseAge:f.kind==='combo'?1.12:.62};
    heldTargets.set(e,f);
  }
  function updateHold(s,f) {
    const h=f.hold;if(!h)return;
    if(!ordinary(h.target)||f.age>=h.releaseAge-EPS){releaseHold(f);return;}
    const q=Math.max(0,Math.min(1,(f.age-.42)/.20)),ease=q*q*(3-2*q);
    const x=h.sx+(h.x-h.sx)*ease,y=h.sy+(h.y-h.sy)*ease;
    if(!G.World.isFree(x,y,h.target.r||10,true)||!clearPath(h.target.x,h.target.y,x,y)) {releaseHold(f);return;}
    h.target.x=x;h.target.y=y;G.EnemyMgr.rebuildGrid?.();
  }
  function emitBullets(s,f,pulse) {
    const total=f.count,base=Math.floor(total/5),count=base+(pulse<total%5?1:0);
    for(let i=0;i<count;i++){
      const choices=nearby(f.owner,rangeFor(f.move,'bullets')).slice(0,3);if(!choices.length)return;
      const target=choices[f.emitted%choices.length],aim=Math.atan2(target.y-f.owner.y,target.x-f.owner.x);
      const desired=G.KimimaroArt?.muzzleFor?.(f.owner,aim)||{x:f.owner.x+Math.cos(aim)*12,y:f.owner.y+Math.sin(aim)*12};
      if(!clearPath(f.owner.x,f.owner.y,desired.x,desired.y))continue;
      const speed=finite(f.move.speed,600);
      s.bullets.push({owner:f.owner,world:f.world,x:desired.x,y:desired.y,startX:desired.x,startY:desired.y,
        vx:Math.cos(aim)*speed,vy:Math.sin(aim)*speed,aim,age:0,distance:0,range:rangeFor(f.move,'bullets'),
        rank:f.rank,move:f.move,m:f.move,attack:f.attack,damageRatio:1/5,castId:f.castId,phaseHits:new Map(),baseKind:'bullets',kind:'bullets'});
      f.emitted++;s.emitted++;
      f.aim=aim;f.owner.aim=aim;
    }
  }
  function updateBullets(s,dt) {
    for(let i=s.bullets.length-1;i>=0;i--){
      const b=s.bullets[i];if(!validState(s)||b.world!==G.World){s.bullets.splice(i,1);continue;}
      const speed=Math.hypot(b.vx,b.vy),travel=Math.min(speed*dt,b.range-b.distance);
      const steps=Math.min(256,Math.max(1,Math.ceil(travel/2))),step=travel/steps;
      let remove=false;
      for(let j=0;j<steps;j++){
        b.x+=Math.cos(b.aim)*step;b.y+=Math.sin(b.aim)*step;b.distance+=step;
        if(G.World.isWall(b.x,b.y)){remove=true;break;}
        const prop=G.World.projectileBlock?.(b.x,b.y,2);
        if(prop){hit(s,b,prop,b.damageRatio,0,true);remove=true;break;}
        const victims=G.EnemyMgr.queryCircle(b.x,b.y,42).filter(e=>alive(e)&&distance2(e,b)<=((e.r||8)+2)**2)
          .sort((a,b2)=>distance2(a,b)-distance2(b2,b));
        if(victims.length){hit(s,b,victims[0],b.damageRatio,0,true);remove=true;break;}
      }
      b.age+=dt;
      if(remove||b.distance>=b.range-EPS)s.bullets.splice(i,1);
    }
  }
  function commitFlower(s,f) {
    const source=f.flowerSource,target=f.target;
    if(!source||!alive(target)||!requirementsPresent(f.owner,f.requiredIds)){f.duration=.70;f.kind='vine';releaseHold(f);return;}
    const aim=Math.atan2(target.y-f.owner.y,target.x-f.owner.x);
    const viable=f.hold?inLine(f.owner,f.hold,aim,rangeFor(source),halfWidth(source)):
      inLine(f.owner,target,aim,rangeFor(source),halfWidth(source));
    if(!viable){f.duration=.70;f.kind='vine';releaseHold(f);return;}
    // A third technique that was already waiting keeps its place in the queue.
    const older=scheduledMoves(f.owner).some(m=>m!==source&&m!==f.source&&(m.t||0)<=EPS&&
      (s.readySince.get(m)??s.clock)<f.clockStart-EPS&&scheduledTarget(f.owner,m));
    if(older){f.duration=.70;f.kind='vine';releaseHold(f);return;}
    s.committingFlower=true;
    let success=false;
    try{success=G.DigimonSkills.cast(f.owner,source);}finally{s.committingFlower=false;}
    if(success){
      source.t=Math.max(0,Math.max(.05,source.cd*(f.owner.cdMul||1))-(s.clock-f.flowerStartedAt));source.castAt=performance.now();
      f.owner.cast(source);s.readySince.delete(source);
      if(G.Coop?.active&&!G.SelfClones?.isActor(f.owner))G.Coop.cast(f.owner,source);
    }else{f.duration=.70;f.kind='vine';releaseHold(f);}
  }
  function processHit(s,f,index) {
    if(f.kind==='willow'){
      const target=targetFor(f.owner,f.move);if(!target)return;
      f.aim=Math.atan2(target.y-f.owner.y,target.x-f.owner.x);f.owner.aim=f.aim;f.target=target;
      hit(s,f,target,1/4,index,true);
    }else if(f.kind==='camellia'){
      if(index===0){const e=targetFor(f.owner,f.move);if(e){f.target=e;f.aim=Math.atan2(e.y-f.owner.y,e.x-f.owner.x);}}
      line(s,f,[.25,.25,.5][index],index);
    }else if(f.kind==='bullets')emitBullets(s,f,index);
    else if(f.kind==='larch')circle(s,f,radiusFor(f.move),.5,index);
    else if(f.kind==='lily')circle(s,f,radiusFor(f.move),.5,index);
    else if(f.kind==='bracken')circle(s,f,f.forest.radius*(index+1)/f.hitTimes.length,1,0,true);
    else if(f.kind==='vine'||(f.kind==='combo'&&index===0)){
      const target=f.target;
      if(alive(target)&&distance2(target,f.owner)<=rangeFor(f.move,'vine')**2&&clearPath(f.owner.x,f.owner.y,target.x,target.y)){
        hit(s,f,target,1,0,true);beginHold(s,f);
      }
    }else if(f.kind==='flower')line(s,f,1,0,true);
    else if(f.kind==='combo'&&f.flowerStarted)line(s,f,1,1,true);
  }
  function advanceAction(s,dt) {
    const f=s.action;
    if(!f)return;
    let left=dt;
    // Split at authored events so newly released projectiles never receive a
    // full frame of movement before their actual release time.
    for(let guard=0;left>EPS&&s.action===f&&guard<64;guard++){
      const boundaries=[f.duration,...f.hitTimes.filter(t=>t>f.age+EPS)];
      if(f.kind==='combo'&&!f.flowerStarted&&f.age<.54-EPS)boundaries.push(.54);
      if((f.kind==='flower'&&f.age<.30-EPS)||(f.kind==='combo'&&f.age<.84-EPS))boundaries.push(f.kind==='combo'?.84:.30);
      const next=Math.min(...boundaries.filter(t=>t>f.age+EPS));
      const step=Math.min(left,Number.isFinite(next)?next-f.age:left);
      updateBullets(s,step);f.age+=step;left-=step;
      if(f.kind!=='bracken'){f.x=f.owner.x;f.y=f.owner.y;}
      if(f.forest)f.forest.age=f.age;
      updateHold(s,f);
      if(f.kind==='combo'&&!f.flowerStarted&&f.age>=.54-EPS)commitFlower(s,f);
      if((f.kind==='flower'&&f.age>=.30-EPS)||(f.kind==='combo'&&f.flowerStarted&&f.age>=.84-EPS)){
        if(!f.aimLocked){if(alive(f.target))f.aim=Math.atan2(f.target.y-f.owner.y,f.target.x-f.owner.x);f.aimLocked=true;}
      }
      while(f.hitIndex<f.hitTimes.length&&f.age+EPS>=f.hitTimes[f.hitIndex])processHit(s,f,f.hitIndex++);
      if(f.baseKind==='larch'&&f.age>=.18-EPS){s.guardUntil=Math.max(s.guardUntil,f.clockStart+.88);s.guardMove=f.source.id;}
      if(f.age+EPS>=f.duration){releaseHold(f);s.action=null;s.forest=null;}
    }
    if(left>EPS)updateBullets(s,left);
  }
  function boomerangHand(owner,aim=owner.aim||0) {
    return G.KimimaroArt?.muzzleFor?.(owner,aim)||{x:owner.x+Math.cos(aim)*12,y:owner.y+Math.sin(aim)*12,height:31};
  }
  function boomerangState(owner=G.Game.player) {
    const s=states.get(owner);if(!validState(s)||!learned(owner,BOOMERANG))return null;
    const b=s.boomerang,lanes=b.lanes.map(lane=>({...lane,cooldown:Math.max(0,lane.readyAt-s.clock),
      hand:boomerangHand(owner,lane.projectile?.aim??b.pose?.aim??owner.aim)})),first=lanes[0];
    return {...b,lanes,projectiles:lanes.map(lane=>lane.projectile).filter(Boolean),
      projectile:first?.projectile||null,readyAt:first?.readyAt||0,cooldown:first?.cooldown||0,
      hand:first?.hand||boomerangHand(owner)};
  }
  function boomerangPoseFor(owner) {
    const s=states.get(owner),pose=s?.boomerang.pose;
    return validState(s)&&learned(owner,BOOMERANG)&&pose&&s.clock-pose.time<.12
      ?{kind:'bullets',age:.20,aim:pose.aim}:null;
  }
  function boomerangEvent(g,lane,event) {
    event.lane=lane.index;g.log.push(event);lane.log.push(event);
    if(g.log.length>20)g.log.shift();if(lane.log.length>20)lane.log.shift();
  }
  function launchBoomerang(s,lane,time) {
    const owner=s.owner,m=learned(owner,BOOMERANG),g=s.boomerang;
    if(!m||lane.index>=g.count||lane.projectile||time+EPS<lane.readyAt)return false;
    const targets=nearby(owner,finite(m.range,600));if(!targets.length)return false;
    const target=targets[lane.index%targets.length];
    const aim=Math.atan2(target.y-owner.y,target.x-owner.x),hand=boomerangHand(owner,aim);
    if(!clearPath(owner.x,owner.y,hand.x,hand.y))return false;
    const speed=finite(m.speed,650),castId=nextCast++;
    const distance=Math.hypot(target.x-hand.x,target.y-hand.y),bend=(lane.index%2?1:-1)*Math.min(140,distance*.4);
    const cx=(hand.x+target.x)/2-Math.sin(aim)*bend,cy=(hand.y+target.y)/2+Math.cos(aim)*bend;
    const curve=Array.from({length:33},(_,i)=>{const t=i/32,u=1-t;
      return {x:u*u*hand.x+2*u*t*cx+t*t*target.x,y:u*u*hand.y+2*u*t*cy+t*t*target.y};});
    const firstAim=Math.atan2(curve[1].y-hand.y,curve[1].x-hand.x);
    const pierce=Math.max(0,Math.floor(finite(m.pierce)+(G.Quantity?.bonus(owner)||0)));
    lane.projectile={owner,world:G.World,x:hand.x,y:hand.y,vx:Math.cos(firstAim)*speed,vy:Math.sin(firstAim)*speed,
      aim,phase:'out',age:0,distance:0,range:finite(m.range,600),move:{...m},attack:owner.atk*damageBonus(owner),
      kind:'boomerang',baseKind:'boomerang',castId,lane:lane.index,pierce,remainingPierce:pierce,
      curve,curveIndex:1,phaseHits:new Map(),trail:[]};
    lane.readyAt=time+Math.max(.05,m.cd*(owner.cdMul||1));
    lane.launches++;g.launches++;g.pose={time,aim};
    boomerangEvent(g,lane,{kind:'launch',time,castId,x:hand.x,y:hand.y});
    return true;
  }
  function catchBoomerang(s,lane,hand,time) {
    const g=s.boomerang,b=lane.projectile;lane.catches++;g.catches++;
    boomerangEvent(g,lane,{kind:'catch',time,castId:b.castId,x:hand.x,y:hand.y});
    lane.projectile=null;g.pose={time,aim:b.aim};launchBoomerang(s,lane,time);
  }
  function updateBoomerang(s,dt) {
    const g=s.boomerang,m=learned(s.owner,BOOMERANG);
    if(!m){g.lanes=[];g.pose=null;return;}
    const baseCount=Math.max(1,finite(m.count,1));
    g.count=Math.min(16,Math.max(1,G.Quantity?.count(s.owner,baseCount)||baseCount));
    while(g.lanes.length<g.count)g.lanes.push({index:g.lanes.length,projectile:null,readyAt:0,launches:0,catches:0,hits:0,log:[]});
    // Each physical bone has its own launch clock and return state.
    for(const lane of g.lanes)updateBoomerangLane(s,lane,dt);
    // A quantity decrease retires surplus bones only after they reach the hand.
    while(g.lanes.length>g.count&&!g.lanes.at(-1).projectile)g.lanes.pop();
    m.t=g.lanes.reduce((time,lane)=>lane.index<g.count?Math.min(time,Math.max(0,lane.readyAt-s.clock)):time,Infinity);
  }
  function updateBoomerangLane(s,lane,dt) {
    const g=s.boomerang;
    let left=dt;
    // Both the launch cooldown and the physical catch must finish before firing.
    for(let steps=0;left>EPS&&steps<1024;steps++){
      if(!lane.projectile){
        const wait=Math.max(0,lane.readyAt-(s.clock-left));
        if(wait>left+EPS)break;
        left-=Math.min(left,wait);
        if(!launchBoomerang(s,lane,s.clock-left)||left<=EPS)break;
      }
      const b=lane.projectile,hand=boomerangHand(s.owner,b.aim);
      if(b.phase==='return'){
        const distance=Math.hypot(hand.x-b.x,hand.y-b.y);
        if(distance<=8){
          catchBoomerang(s,lane,hand,s.clock-left);continue;
        }
        const speed=finite(b.move.returnSpeed,900),travel=Math.min(4,speed*left,distance-8);
        b.vx=(hand.x-b.x)/distance*speed;b.vy=(hand.y-b.y)/distance*speed;
        b.x+=b.vx*travel/speed;b.y+=b.vy*travel/speed;b.age+=travel/speed;left-=travel/speed;
      }else{
        const speed=finite(b.move.speed,650),point=b.curve[b.curveIndex];
        const dx=point?point.x-b.x:Math.cos(b.aim),dy=point?point.y-b.y:Math.sin(b.aim),segment=Math.hypot(dx,dy);
        if(point&&segment<=EPS){b.curveIndex++;continue;}
        const travel=Math.min(4,speed*left,b.range-b.distance,point?segment:Infinity);
        if(travel<=EPS){b.phase='return';continue;}
        b.vx=dx/segment*speed;b.vy=dy/segment*speed;
        b.x+=b.vx*travel/speed;b.y+=b.vy*travel/speed;
        b.distance+=travel;b.age+=travel/speed;left-=travel/speed;
        const wall=G.World.isWall(b.x,b.y),prop=wall?null:G.World.projectileBlock?.(b.x,b.y,7);
        const victim=!wall&&!prop?G.EnemyMgr.queryCircle(b.x,b.y,48)
          .filter(e=>alive(e)&&!e.friendly&&!b.phaseHits.get(0)?.has(e)&&distance2(e,b)<=((e.r||8)+7)**2)
          .sort((a,c)=>distance2(a,b)-distance2(c,b))[0]:null;
        let exhausted=false;
        if(prop||victim){
          const damage=hit(s,b,prop||victim,1,0,true);
          if(victim&&damage>0){lane.hits++;g.hits++;if(b.remainingPierce>0)b.remainingPierce--;else exhausted=true;}
        }
        if(wall||prop||exhausted||b.distance>=b.range-EPS)b.phase='return';
      }
      b.trail.push({x:b.x,y:b.y});if(b.trail.length>4)b.trail.shift();
      // An overdue catch can still relaunch at the end of the same frame.
      if(b.phase==='return'&&Math.hypot(hand.x-b.x,hand.y-b.y)<=8+EPS){
        catchBoomerang(s,lane,hand,s.clock-left);
      }
    }
  }
  function boneGuardState(owner=G.Game.player) {
    const s=states.get(owner);
    if(!validState(s)||!learned(owner,BONE_GUARD))return null;
    const g=s.boneGuard,w=g.wall;
    return {active:!!w&&w.age<w.duration,cooldown:Math.max(0,g.readyAt-s.clock),
      blocks:g.blocks,triggers:g.triggers,wall:w};
  }
  function guardBlockable(p) {
    return p.friendly===false&&!p.unblockable&&!p.guardUnblockable&&!p.uninterceptable&&
      !p.hazard&&!p.laser&&!p.beam&&!p.ground&&!p.orb&&
      [p.x,p.y,p.vx,p.vy].every(Number.isFinite);
  }
  // Contact with a finite ground footprint, expanded by the projectile radius.
  function wallContact(p,w,horizon) {
    const ax=finite(p.px,p.x)-w.x,ay=finite(p.py,p.y)-w.y,r=Math.max(0,p.r||0);
    const values=[[ax*w.nx+ay*w.ny,p.vx*w.nx+p.vy*w.ny,6+r],
      [-ax*w.ny+ay*w.nx,-p.vx*w.ny+p.vy*w.nx,w.halfWidth+r]];
    let enter=0,exit=horizon;
    for(const [position,velocity,size] of values){
      if(Math.abs(velocity)<EPS){if(Math.abs(position)>size)return null;continue;}
      const first=(-size-position)/velocity,last=(size-position)/velocity;
      enter=Math.max(enter,Math.min(first,last));exit=Math.min(exit,Math.max(first,last));
      if(enter>exit)return null;
    }
    return enter;
  }
  function guardThreat(p,owner,dt) {
    const ax=finite(p.px,p.x),ay=finite(p.py,p.y),dx=ax-owner.x,dy=ay-owner.y;
    const speed2=p.vx*p.vx+p.vy*p.vy,r=(owner.r||12)+Math.max(0,p.r||0);
    const approach=dx*p.vx+dy*p.vy,c=dx*dx+dy*dy-r*r;
    if(speed2<EPS||approach>=0||c<=0)return null;
    const disc=approach*approach-speed2*c;if(disc<0)return null;
    const impact=(-approach-Math.sqrt(disc))/speed2;
    if(impact>dt+.22||impact>finite(p.life,Infinity)-finite(p.t)+dt)return null;
    const speed=Math.sqrt(speed2),nx=-p.vx/speed,ny=-p.vy/speed;
    const distance=Math.min(40,Math.max((owner.r||12)+6,Math.sqrt(dx*dx+dy*dy)-(p.r||0)-4));
    return {x:owner.x+nx*distance,y:owner.y+ny*distance,nx,ny,halfWidth:42,age:0,duration:.65};
  }
  function interceptBones(dt,owner) {
    if(G.Game.state!=='playing'||!(dt>0)||!Number.isFinite(dt))return;
    const actors=[owner,...(G.SelfClones?.actors?.()||[]).filter(a=>a.sourceOwner===owner)];
    const guards=[];
    for(const actor of actors){
      if(!validOwner(actor)||actor.frozen||!learned(actor,BONE_GUARD))continue;
      const s=state(actor);guards.push(s);
    }
    if(!guards.length)return;
    // Evaluate complete swept motion before native player and clone collisions.
    for(const p of [...G.Projectiles.all()]){
      if(!guardBlockable(p))continue;
      let first=null;
      for(const s of guards){
        const g=s.boneGuard;
        const existing=g.wall&&g.wall.age<g.wall.duration?g.wall:null;
        // A rear shot must not be erased after crossing the owner first.
        if(existing&&p.vx*existing.nx+p.vy*existing.ny>=0)continue;
        const wall=existing||(s.clock+EPS>=g.readyAt?guardThreat(p,s.owner,dt):null);
        if(!wall)continue;
        const horizon=existing?Math.min(dt,wall.duration-wall.age):dt+.22;
        const contact=wallContact(p,wall,horizon);
        if(contact!==null&&(!first||contact<first.contact))first={s,wall,contact,existing};
      }
      if(!first)continue;
      const {s,wall,contact,existing}=first,g=s.boneGuard;
      if(!existing){
        g.wall=wall;wall.born=s.clock;
        g.readyAt=s.clock+[5,4.5,4,3.5,3][rank(learned(s.owner,BONE_GUARD))-1];
        g.triggers++;learned(s.owner,BONE_GUARD).t=g.readyAt-s.clock;
      }
      if(contact<=dt+EPS){
        G.Projectiles.remove(p);g.blocks++;
        wall.flash=.16;wall.impactX=finite(p.px,p.x)+p.vx*contact;
        wall.impactY=finite(p.py,p.y)+p.vy*contact;
      }
    }
  }
  function update(dt) {
    for(const [owner,s] of states)if(!validState(s)){evolutions.delete(owner);clear(owner);}
    if(G.Game.state!=='playing'||!(dt>0)||!Number.isFinite(dt))return;
    for(const s of states.values()){
      syncSelection(s);
      if(s.owner.frozen)continue;
      s.clock+=dt;
      updateBoomerang(s,dt);
      const guard=learned(s.owner,BONE_GUARD),g=s.boneGuard;
      if(guard){
        guard.t=Math.max(0,g.readyAt-s.clock);
        if(g.wall){g.wall.age=s.clock-g.wall.born;g.wall.flash=Math.max(0,(g.wall.flash||0)-dt);
          if(g.wall.age>=g.wall.duration)g.wall=null;}
      }else g.wall=null;
      for(const mark of s.impacts)mark.age=Math.max(0,s.clock-mark.time);
      s.impacts=s.impacts.filter(mark=>mark.age<.45);
      const curse=learned(s.owner,CURSE);
      if(curse){
        curse.t=0;
        if(Number.isFinite(s.curse.startAt)&&s.clock-s.curse.startAt>=1-EPS&&!hasEvolution(s.owner))
          evolutions.set(s.owner,{world:G.World,run:G.Game.st});
      }
      if(s.action)advanceAction(s,dt);else updateBullets(s,dt);
    }
  }
  function scheduledMoves(owner) {
    // Every learned Kimimaro technique joins the same fair body-action queue.
    // Curse and the reactive bone wall keep their independent trigger rules.
    return [...new Set([...group(owner).filter(m=>!m.passive&&!automatic(m)),
      ...(owner.moves||[]).filter(m=>automatic(m)&&modeKind(m)!=='curse')])];
  }
  function scheduledTarget(owner,m) {
    const kind=modeKind(m);
    if(!supports(m.digiMode))return owner.target;
    const list=candidates(owner,m);
    if(kind!=='bullets'&&kind!=='vine')return list[0]||null;
    const melee=rangeFor(learned(owner,BASIC)||{},'willow')+12;
    if(kind==='bullets'){
      if(nearby(owner,melee).length)return null;
      return list.find(e=>distance2(owner,e)>melee*melee)||null;
    }
    const flower=learned(owner,BASIC+'-flower');
    const learnedFlower=!!flower;
    // Reserve Vine briefly for a learned Flower without idling the body:
    // Willow, threatened Larch and other ready techniques remain eligible.
    if(learnedFlower&&(flower.t||0)>EPS&&(flower.t||0)<=.54+EPS)return null;
    const linked=learnedFlower&&(flower.t||0)<=EPS;
    return list.find(e=>{
      if(ordinary(e))return distance2(owner,e)>melee*melee || linked;
      return linked&&inLine(owner,e,Math.atan2(e.y-owner.y,e.x-owner.x),rangeFor(flower),halfWidth(flower));
    })||null;
  }
  function startScheduled(s,m,target=scheduledTarget(s.owner,m)) {
    const owner=s.owner;
    if(!target)return false;
    s.scheduledMove=m;s.scheduledTarget=target;
    let success=false;
    try{if(canCast(owner,m))success=G.DigimonSkills.cast(owner,m);}
    finally{s.scheduledMove=null;s.scheduledTarget=null;}
    if(!success)return false;
    m.t=Math.max(.05,m.cd*(owner.cdMul||1));m.castAt=performance.now();
    owner.cast(m);s.readySince.delete(m);
    if(G.Coop?.active&&!G.SelfClones?.isActor(owner))G.Coop.cast(owner,m);
    return true;
  }
  function tick(dt,owner,now) {
    if(!validOwner(owner))return previousTick.call(C,dt,owner,now);
    if(G.Game.state!=='playing'||owner.frozen||!(dt>0)||!Number.isFinite(dt))return;
    const s=state(owner);syncSelection(s);
    const selected=scheduledMoves(owner);
    for(const m of selected){
      m.t=Math.max(0,finite(m.t)-dt);
      if(m.t<=EPS&&scheduledTarget(owner,m)){
        if(!s.readySince.has(m))s.readySince.set(m,s.clock);
      }else s.readySince.delete(m);
    }
    if(s.action||s.exitUntil>s.clock+EPS)return;
    const curse=learned(owner,CURSE);
    if(curse&&canCast(owner,curse)){
      if(G.DigimonSkills.cast(owner,curse)){owner.cast(curse);curse.t=0;curse.castAt=performance.now();}return;
    }
    const ready=selected.filter(m=>(m.t||0)<=EPS&&s.readySince.has(m)).sort((a,b)=>
      s.readySince.get(a)-s.readySince.get(b)||selected.indexOf(a)-selected.indexOf(b));
    const legal=ready.filter(m=>!!scheduledTarget(owner,m));
    const first=legal[0];
    if(first){
      const vine=learned(owner,BASIC+'-vine'),flower=selected.find(m=>modeKind(m)==='flower');
      if(vine&&flower&&(first===vine||first===flower)){
        const pending=first===vine?flower:vine;
        const target=scheduledTarget(owner,vine);
        // Pair only when both are ready. Waiting here would suppress Willow
        // and threatened Larch while the other move cools down.
        if((pending.t||0)<=EPS&&(vine.t||0)<=EPS&&(flower.t||0)<=EPS&&target&&comboAvailable(owner,vine,target)){
          if(startScheduled(s,vine,target))return;
        }
      }
      if(supports(first.digiMode)){if(startScheduled(s,first))return;}
      else if(G.DigimonSkills.cast(owner,first)){
        first.t=Math.max(.05,first.cd*(owner.cdMul||1));owner.cast(first);first.castAt=performance.now();s.readySince.delete(first);return;
      }
    }
  }
  function clear(owner) {
    if(owner){const s=states.get(owner);if(s)cancel(s,false);states.delete(owner);}
    else {for(const s of states.values())cancel(s,false);states.clear();heldTargets.clear();}
  }
  function activeFor(owner=G.Game.player){const s=states.get(owner);return validState(s)?s.action:null;}
  function formFor(owner=G.Game.player){if(hasEvolution(owner))return 'curse';const s=states.get(owner);if(!validState(s))return 'normal';
    const elapsed=s.clock-s.curse.startAt;return Number.isFinite(s.curse.startAt)&&elapsed>=.75?'curse':'normal';}
  function renderStates(){
    if(terminal()){clear();return [];}
    return [...states.values()].filter(validState).map(s=>{
    s.form=formFor(s.owner);return s;
  });}
  const previousTick=C.tick,previousUpdate=C.updateFields,previousClear=C.clearFields;
  const previousResolve=C.resolve;
  C.resolve=function(dt,owner,now){interceptBones(dt,owner);return previousResolve.call(this,dt,owner,now);};
  C.tick=tick;
  C.updateFields=function(dt){const result=previousUpdate.call(this,dt);update(dt);return result;};
  C.clearFields=function(owner){const result=previousClear.call(this,owner);clear(owner);return result;};
  const ground=C.drawGroundFields,air=C.drawAirFields;
  C.drawGroundFields=function(ctx){ground.call(this,ctx);G.KimimaroArt?.drawGround?.(ctx,renderStates());};
  C.drawAirFields=function(ctx){air.call(this,ctx);G.KimimaroArt?.drawAir?.(ctx,renderStates());};
  for(const method of ['toUI','quit']){
    const previous=G.Game[method];
    if(typeof previous!=='function')continue;
    G.Game[method]=function(...args){
      const result=previous.apply(this,args);
      if(terminal())clear();
      return result;
    };
  }
  const playerUpdate=G.Player.prototype.update,playerHurt=G.Player.prototype.hurt,setActive=G.Player.prototype.setActive;
  G.Player.prototype.update=function(dt){
    if(!validOwner(this)||!movementLocked(this))return playerUpdate.call(this,dt);
    const frozen=this.frozen;this.frozen=true;this.svx=this.svy=0;
    try{return playerUpdate.call(this,dt);}finally{this.frozen=frozen;}
  };
  G.Player.prototype.setActive=function(...args){
    const before=signature(this),result=setActive.apply(this,args);
    if(validOwner(this)&&signature(this)!==before){const s=state(this);cancel(s);s.selection=signature(this);s.readySince.clear();}
    return result;
  };
  function incomingAmount(owner,amount,pure){
    if(validOwner(owner)&&!pure&&amount>0){
      const s=states.get(owner);
      if(validState(s)&&s.guardUntil>s.clock&&learned(owner,s.guardMove))amount*=.8;
      if(!group(owner).length&&learned(owner,BASIC))amount*=.75;
    }
    return amount;
  }
  G.Player.prototype.hurt=function(amount,type=null,pure=false,...rest){
    return playerHurt.call(this,incomingAmount(this,amount,pure),type,pure,...rest);
  };
  const speed=Object.getOwnPropertyDescriptor(G.Player.prototype,'spd');
  if(speed?.get)Object.defineProperty(G.Player.prototype,'spd',{...speed,get(){
    return speed.get.call(this)*(validOwner(this)?speedMultiplier(this):1);
  }});
  G.NarutoKimimaro={dex:DEX,supports,handles:supports,canCast,cast,update,clear,resetEvolution,activeFor,formFor,curseState,boneGuardState,boomerangState,boomerangPoseFor,movementLocked,held,
    hurtClone:(owner,amount,type,pure,context,baseHurt)=>baseHurt(incomingAmount(owner,amount,pure),type,pure,context),
    stateFor:(owner=G.Game.player)=>{const s=states.get(owner);return validState(s)?s:null;},renderStates,speedMultiplier,
    get bullets(){return renderStates().flatMap(s=>s.bullets);},get effects(){return renderStates().map(s=>s.action).filter(Boolean);}};
})();
