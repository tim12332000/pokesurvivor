/* Classic LF2 Freeze: straight ice balls, a physical blade, columns and tornadoes. */
(() => {
  'use strict';
  if (G.LF2Freeze) return;
  const DEX = 30018, C = G.Combat, EPS = 1e-8, states = new Map(), leases = new Map();
  const defaults = {
    'lf2-iceball': { charge: .2, cd: 1.25, damage: 48, ranges: [500,550,600,650,720], radii: [16,18,20,22,24], counts: [1,2,2,3,3], speed: 420, freeze: 1.2, cap: 12 },
    'lf2-sword': { charge: 0, cd: 1.05, damage: 62, ranges: [88,100,112,124,140], radii: [88,100,112,124,140], counts: [1,1,2,2,3], freeze:1.2, cap: 8 },
    'lf2-column': { charge: 10/30, cd: 5.6, damage: 90, ranges: [260,290,320,350,390], radii: [38,42,46,50,56], counts: [3,3,4,4,5], freeze: 1.2, cap: 12 },
    'lf2-whirlwind': { charge: 11/30, cd: 8.5, damage: 30, ranges: [480,510,540,570,620], radii: [62,70,78,86,96], counts: [1,1,1,2,2], speed: 95, life: 2.7, tick: .22, cap: 4 }
  };
  const alive = a => !!a && !a.dead && a.hp > 0;
  const controlled = a => G.SelfClones?.isControlled?.(a) ?? (a === G.Game.player || !!G.SelfClones?.isActor?.(a));
  const valid = a => alive(a) && controlled(a) && (a.mon?.dex ?? a.dex) === DEX;
  const supports = mode => Object.hasOwn(defaults, mode);
  const terminal = () => G.Game.state === 'ui' || G.Game.state === 'over';
  const learned = (owner,id) => !!owner.moves?.some(m => m.id === id);
  const rank = m => Math.max(0, Math.min(4, (m.lvl || 1) - 1));
  const number = (n,fallback) => Number.isFinite(n) ? n : fallback;
  const angle = a => Math.atan2(Math.sin(a),Math.cos(a));
  const strong = e => !!(e.boss || e.elite || e.legend || e.judge);
  function profile(owner,m) {
    const mode=m?.digiMode || m?.id, d=defaults[mode];
    if (!d) return null;
    const p={...d,...(G.LF2?.power?.[mode] || {})}, L=rank(m);
    const rawCount=G.Quantity?.count(owner,p.counts[L]) ?? p.counts[L];
    const count=Math.min(p.cap,Math.max(1,rawCount)),bodyScale=mode==='lf2-sword'?1.25**Math.max(0,owner?.giantPicks||0):1;
    return {mode,charge:p.charge,cd:number(m.cd,p.cd),damage:number(m.dmg,p.damage),
      range:number(m.range,p.ranges[L])*bodyScale,radius:number(m.radius,p.radii[L])*bodyScale,count,
      speed:mode==='lf2-whirlwind'?Math.max(p.speed,(number(m.range,p.ranges[L])-45-number(m.radius,p.radii[L]))/p.life):p.speed || 0,
      freeze:Array.isArray(p.freeze)?p.freeze[L]:p.freeze || 0,
      life:p.life || 0,tick:p.tick || 0,arc:1.9,
      duration:mode==='lf2-sword'?count*8/30:mode==='lf2-column'?24/30:mode==='lf2-whirlwind'?25/30:14/30};
  }
  function state(owner) {
    let s=states.get(owner);
    if(s && (s.world!==G.World || s.epoch!==G.CombatPulse.epoch)){clear(owner);s=null;}
    if(!s){s={owner,world:G.World,epoch:G.CombatPulse.epoch,clock:0,action:null,effects:[],casts:{},hits:0,damage:0,ready:new Map(),swordOwned:false,punchReady:0};states.set(owner,s);}
    return s;
  }
  const stateLegal = s => states.get(s.owner)===s && valid(s.owner) && s.world===G.World && s.epoch===G.CombatPulse.epoch;
  const legal = (s,f) => stateLegal(s) && learned(s.owner,f.m.id) && G.CombatPulse.legal(f.cast);
  function clear(owner) {
    G.LF2Art?.stopSounds?.(owner);
    if(owner) states.delete(owner); else states.clear();
    for(const [e,list] of leases){const keep=owner?list.filter(l=>l.s.owner!==owner):[];if(keep.length)leases.set(e,keep);else leases.delete(e);}
  }
  function path(ax,ay,bx,by,target=null) {
    const steps=Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/4));
    for(let i=1;i<=steps;i++){
      const x=ax+(bx-ax)*i/steps,y=ay+(by-ay)*i/steps;
      if(G.World.isWall?.(x,y))return false;
      const p=G.World.projectileBlock?.(x,y,1);if(p && p!==target)return false;
    }
    return true;
  }
  function firstBlock(ax,ay,bx,by) {
    const steps=Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/4));
    for(let i=1;i<=steps;i++){
      const x=ax+(bx-ax)*i/steps,y=ay+(by-ay)*i/steps;
      if(G.World.isWall?.(x,y))return {wall:true};
      const prop=G.World.projectileBlock?.(x,y,1);if(prop)return {prop};
    }
    return null;
  }
  function nearby(x,y,r) {
    return [...new Set(G.EnemyMgr.queryCircle(x,y,r))].filter(e=>alive(e) && !e.friendly && Math.hypot(e.x-x,e.y-y)<=r+(e.r || 0));
  }
  function targetFor(owner,m) {
    const p=profile(owner,m),reach=p.mode==='lf2-sword'?(states.get(owner)?.swordOwned?p.range:500):p.range;
    return nearby(owner.x,owner.y,reach).filter(e=>path(owner.x,owner.y,e.x,e.y))
      .sort((a,b)=>Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y))[0] ||
      (G.World.propsInCircle?.(owner.x,owner.y,reach)||[]).filter(e=>e.hp>0 && e.destructible!==false && path(owner.x,owner.y,e.x,e.y,e))
        .sort((a,b)=>Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y))[0] || null;
  }
  function canCast(owner,m) {
    if(!valid(owner) || owner.frozen || G.Game.state!=='playing' || !supports(m?.digiMode) || !learned(owner,m.id))return false;
    const s=state(owner);
    return !s.action && (m.t||0)<=EPS && !!targetFor(owner,m);
  }
  function choreography(f) {
    const t=Math.max(0,f.age-f.charge);
    f.phase=f.age<f.charge?'windup':f.age<f.duration-.08?'release':'recovery';
    f.phaseAge=f.phase==='windup'?f.age:f.phase==='release'?t:Math.max(0,f.age-f.duration+.08);
    f.progress=Math.max(0,Math.min(1,f.phase==='windup'?f.age/f.charge:f.phase==='release'?t/(f.duration-f.charge-.08):f.phaseAge/.08));
    if(f.mode==='lf2-sword'){
      f.swingIndex=Math.min(f.count-1,Math.floor(t/(8/30)));
      f.swingAge=t-f.swingIndex*8/30;
      f.bladeAim=f.aim+(f.swingIndex%2?-1:1)*(-.95+1.9*Math.max(0,Math.min(1,(f.swingAge-4/30)/(2/30))));
    }
  }
  function cast(owner,m) {
    if(!canCast(owner,m))return false;
    const s=state(owner),target=targetFor(owner,m),p=profile(owner,m),aim=Math.atan2(target.y-owner.y,target.x-owner.x);
    const summon=p.mode==='lf2-sword' && !s.swordOwned;
    const f={...p,kind:summon?'sword-summon':p.mode==='lf2-sword'?'sword':p.mode,owner,m:{...m},age:0,released:false,aim,x:owner.x,y:owner.y,pulse:0,swingIndex:0,swordHits:new Map(),
      damage:p.damage*(owner.atk??1)*(G.NarutoSupport?.takeAttackBonus(owner)||1)};
    if(summon){f.charge=11/30;f.duration=14/30;}
    f.cast=G.CombatPulse.create(owner,m.id,{channel:p.mode==='lf2-whirlwind'?'cyclone':'body'});
    f.cast.targetIsLegal=()=>legal(s,f);
    choreography(f);s.action=f;s.ready.delete(m.id);s.casts[m.id]=(s.casts[m.id]||0)+1;
    owner.aim=aim;owner.cast?.(m);m.t=Math.max(.05,p.cd*(owner.cdMul??1));m.castAt=performance.now();
    return true;
  }
  function lease(s,f,e,duration) {
    if(!alive(e) || !legal(s,f))return;
    let list=leases.get(e);if(!list)leases.set(e,list=[]);
    const old=list.find(l=>l.s===s && l.id===f.m.id),until=s.clock+(strong(e)?Math.min(.28,duration):duration);
    if(old){old.until=Math.max(old.until,until);old.duration=duration;}
    else list.push({s,id:f.m.id,until,duration});
  }
  function freezeStatus(e) {
    if(!alive(e))return null;
    const list=leases.get(e);if(!list)return null;
    const active=list.filter(l=>stateLegal(l.s) && learned(l.s.owner,l.id) && l.until>l.s.clock);
    if(!active.length){leases.delete(e);return null;}
    leases.set(e,active);
    const best=active.reduce((a,b)=>a.until-a.s.clock>b.until-b.s.clock?a:b);
    return {remaining:best.until-best.s.clock,duration:best.duration};
  }
  const stopped = e => !!freezeStatus(e);
  function frozenTargets() {
    const result=[];
    for(const [enemy,list] of leases){
      if(!alive(enemy))continue;
      const active=list.filter(l=>stateLegal(l.s) && learned(l.s.owner,l.id) && l.until>l.s.clock);
      if(!active.length)continue;
      const best=active.reduce((a,b)=>a.until-a.s.clock>b.until-b.s.clock?a:b);
      result.push({enemy,remaining:best.until-best.s.clock,duration:best.duration});
    }
    return result;
  }
  function contact(s,f,enemies,ratio=1,freeze=0) {
    if(!legal(s,f))return false;
    const hits=enemies.map(e=>{
      const mult=G.Types?.mult?.(f.m.type||'ice',e.types)??1,crit=Math.random()<(s.owner.critChance||0);
      return {target:e,primaryDirectDamage:f.damage*ratio*mult*(G.Weather?.mult?.(f.m.type||'ice')??1)*(crit?1.5:1),
        color:'#bcefff',eff:crit?'crit':G.Types?.label?.(mult),knock:0,
        onHit(){if(!legal(s,f)){f.cast.runEpoch=-1;return;}if(freeze)lease(s,f,e,freeze);}};
    });
    const result=G.CombatPulse.apply(f.cast,f.pulse++,hits);
    if(result && stateLegal(s)){s.hits+=result.primaryHits;s.damage+=result.primaryDamage;}
    return result;
  }
  function props(s,f,x,y,r,test=()=>true,ratio=1) {
    for(const p of G.World.propsInCircle?.(x,y,r)||[]){
      if(!legal(s,f))break;
      if(p.hp>0 && p.destructible!==false && Math.hypot(p.x-x,p.y-y)<=r+(p.r||0) && test(p) && path(x,y,p.x,p.y,p))
        G.World.damageProp?.(p,f.damage*ratio,'#bcefff');
    }
  }
  function release(s,f) {
    f.released=true;
    const dx=Math.cos(f.aim),dy=Math.sin(f.aim);
    const sound=f.kind==='sword-summon'?'074':f.kind==='punch'?'007':f.mode==='lf2-iceball'?'064':f.mode==='lf2-column'?'072':f.mode==='lf2-whirlwind'?'073':null;
    if(sound)G.LF2Art?.playSound?.(sound,s.owner);
    if(f.kind==='sword-summon')s.swordOwned=true;
    if(f.kind==='punch'){
      contact(s,f,nearby(s.owner.x,s.owner.y,f.range).filter(e=>Math.abs(angle(Math.atan2(e.y-s.owner.y,e.x-s.owner.x)-f.aim))<.9 && path(s.owner.x,s.owner.y,e.x,e.y)),1,0);
      props(s,f,s.owner.x,s.owner.y,f.range,p=>Math.abs(angle(Math.atan2(p.y-s.owner.y,p.x-s.owner.x)-f.aim))<.9);
    }
    if(f.mode==='lf2-iceball')for(let i=0;i<f.count;i++){
      if(!legal(s,f))break;
      const lift=32*(s.owner.anim?.scale||1),socket=G.LF2Art?.pointFor?.(s.owner,f,'release');
      const ox=number(socket?.x,s.owner.x),oy=Number.isFinite(socket?.y)?socket.y+lift:s.owner.y;
      const offset=(i-(f.count-1)/2)*f.radius*1.9;
      const block=firstBlock(s.owner.x,s.owner.y,ox-dy*offset,oy+dx*offset);
      if(block){if(block.prop?.hp>0 && block.prop.destructible!==false)G.World.damageProp?.(block.prop,f.damage,'#bcefff');continue;}
      s.effects.push({kind:'iceball',action:f,x:ox-dy*offset,y:oy+dx*offset,lift,aim:f.aim,age:0,life:f.range/f.speed,
        radius:f.radius,range:f.range,speed:f.speed,hits:new Set(),traveled:0,dead:false});
    }
    if(f.mode==='lf2-column'){
      const spacing=(f.range-f.radius-28)/Math.max(1,f.count-1);
      for(let i=0;i<f.count;i++){
        const dist=28+i*spacing,x=s.owner.x+dx*dist,y=s.owner.y+dy*dist;
        // Columns emerge along open floor; they cannot be planted through a wall.
        const block=firstBlock(s.owner.x,s.owner.y,x,y);
        if(block){if(block.prop?.hp>0 && block.prop.destructible!==false && legal(s,f))G.World.damageProp?.(block.prop,f.damage,'#bcefff');break;}
        s.effects.push({kind:'column',action:f,x,y,index:i,aim:f.aim,age:-i*.1,life:.72,radius:f.radius,hit:false,dead:false});
      }
    }
    if(f.mode==='lf2-whirlwind')for(let i=0;i<f.count;i++){
      const offset=(i-(f.count-1)/2)*f.radius*1.6;
      const sx=s.owner.x-dy*offset,sy=s.owner.y+dx*offset;
      if(!path(s.owner.x,s.owner.y,sx,sy))continue;
      const open=path(sx,sy,sx+dx*45,sy+dy*45),x=sx+(open?dx*45:0),y=sy+(open?dy*45:0);
      s.effects.push({kind:'whirlwind',action:f,x,y,aim:f.aim,age:0,life:f.life,
        radius:f.radius,range:f.range,speed:f.speed,tick:f.tick,nextTick:.08,dead:false});
    }
  }
  function moveEffect(s,e,dt) {
    const f=e.action,dx=Math.cos(e.aim),dy=Math.sin(e.aim),distance=e.speed*dt;
    const steps=Math.max(1,Math.ceil(distance/4));
    for(let i=0;i<steps && !e.dead && legal(s,f);i++){
      const x=e.x+dx*distance/steps,y=e.y+dy*distance/steps;
      const block=G.World.projectileBlock?.(x,y,e.kind==='iceball'?e.radius*.55:e.radius*.25);
      if(G.World.isWall?.(x,y) || block){
        if(block && block.hp>0 && block.destructible!==false)G.World.damageProp?.(block,f.damage,'#bcefff');
        e.dead=true;break;
      }
      e.x=x;e.y=y;e.traveled=(e.traveled||0)+distance/steps;
      if(e.kind==='iceball'){
        const victims=nearby(x,y,e.radius).filter(v=>!e.hits.has(v) && path(x,y,v.x,v.y));
        if(victims.length){
          contact(s,f,victims,1,f.freeze);
          for(const v of victims)e.hits.add(v);
          e.dead=true;
        }
      }
    }
  }
  function swordStep(s,f,previousAge) {
    const previous=Math.max(0,previousAge-f.charge),current=Math.max(0,f.age-f.charge);
    for(let i=0;i<f.count && legal(s,f);i++){
      const start=i*8/30+4/30,end=i*8/30+6/30;
      if(current<start || previous>end)continue;
      if(!f.swordSounds)f.swordSounds=new Set();
      if(!f.swordSounds.has(i)){G.LF2Art?.playSound?.('008',s.owner);f.swordSounds.add(i);}
      const lo=Math.max(0,Math.min(1,(previous-start)/(2/30))),hi=Math.max(0,Math.min(1,(current-start)/(2/30)));
      const sign=i%2?-1:1,a=sign*(-.95+1.9*lo),b=sign*(-.95+1.9*hi),min=Math.min(a,b),max=Math.max(a,b);
      let hit=f.swordHits.get(i);if(!hit)f.swordHits.set(i,hit=new Set());
      const inside=e=>{
        const d=Math.hypot(e.x-s.owner.x,e.y-s.owner.y),delta=angle(Math.atan2(e.y-s.owner.y,e.x-s.owner.x)-f.aim);
        const tolerance=Math.asin(Math.min(1,(e.r||0)/Math.max(1,d)));
        return d<=f.range+(e.r||0) && delta+tolerance>=min && delta-tolerance<=max;
      };
      const enemies=nearby(s.owner.x,s.owner.y,f.range).filter(e=>!hit.has(e) && inside(e) && path(s.owner.x,s.owner.y,e.x,e.y));
      if(enemies.length){contact(s,f,enemies,1,f.freeze);for(const e of enemies)hit.add(e);}
      props(s,f,s.owner.x,s.owner.y,f.range,p=>!hit.has(p)&&inside(p));
      // Props share the swing ledger so a slow frame does not hit them every substep.
      for(const p of G.World.propsInCircle?.(s.owner.x,s.owner.y,f.range)||[])if(inside(p))hit.add(p);
    }
  }
  function step(s,dt) {
    s.clock+=dt;
    const f=s.action;
    if(f){
      if(!legal(s,f)){s.action=null;}else{
        const previous=f.age;f.age+=dt;f.x=s.owner.x;f.y=s.owner.y;choreography(f);
        if(!f.released && f.age+EPS>=f.charge)release(s,f);
        if(f.kind==='sword' && f.released)swordStep(s,f,previous);
        if(f.age+EPS>=f.duration && s.action===f)s.action=null;
      }
    }
    for(const e of s.effects){
      if(!legal(s,e.action)){e.dead=true;continue;}
      e.age+=dt;if(e.age<0)continue;
      if(e.kind==='iceball' || e.kind==='whirlwind')moveEffect(s,e,dt);
      if(!legal(s,e.action) || e.dead)continue;
      if(e.kind==='column' && !e.hit && e.age+EPS>=.13){
        e.hit=true;contact(s,e.action,nearby(e.x,e.y,e.radius).filter(v=>path(e.x,e.y,v.x,v.y)),1,e.action.freeze);
        props(s,e.action,e.x,e.y,e.radius);
      }
      if(e.kind==='whirlwind' && (e.age+EPS>=e.nextTick || e.age+EPS>=e.life)){
        e.nextTick+=e.tick;
        const victims=nearby(e.x,e.y,e.radius).filter(v=>path(e.x,e.y,v.x,v.y));
        contact(s,e.action,victims,1,0);
        if(legal(s,e.action))for(const v of victims){
          if(!alive(v) || strong(v))continue;
          const d=Math.max(1,Math.hypot(e.x-v.x,e.y-v.y));
          // Bounded native knock velocity pulls foes into the moving vortex.
          v.kx=(v.kx||0)+(e.x-v.x)/d*38;v.ky=(v.ky||0)+(e.y-v.y)/d*38;
        }
        props(s,e.action,e.x,e.y,e.radius,()=>true,.65);
      }
      if(e.age+EPS>=e.life)e.dead=true;
    }
    s.effects=s.effects.filter(e=>!e.dead);
  }
  function update(dt) {
    if(terminal()){clear();return;}
    if(G.Game.state!=='playing' || !Number.isFinite(dt) || dt<=0)return;
    for(const [owner,s] of states){
      if(!stateLegal(s)){clear(owner);continue;}
      if(!owner.moves?.some(m=>m.digiMode==='lf2-sword'))s.swordOwned=false;
      if(owner.frozen)continue;
      let left=dt;
      while(left>EPS && stateLegal(s)){
        const stepTime=Math.min(.02,left);step(s,stepTime);left-=stepTime;
      }
    }
    for(const [e] of leases)freezeStatus(e);
  }
  function pose(owner=G.Game.player){const s=states.get(owner);return s && stateLegal(s)?s.action:null;}
  const renderStates = () => [...states.values()].filter(s=>stateLegal(s) && !terminal());
  const oldTick=C.tick,oldUpdate=C.updateFields,oldClear=C.clearFields,oldAir=C.drawAirFields;
  function punch(s,m) {
    const target=nearby(s.owner.x,s.owner.y,56).filter(e=>path(s.owner.x,s.owner.y,e.x,e.y))[0];
    if(!target)return false;
    const owner=s.owner,aim=Math.atan2(target.y-owner.y,target.x-owner.x);
    const f={mode:'lf2-punch',kind:'punch',owner,m:{...m},age:0,released:false,aim,x:owner.x,y:owner.y,pulse:0,
      damage:Math.max(15,(m.dmg||48)*.55)*(owner.atk??1),range:56,radius:56,count:1,charge:.1,duration:.3,freeze:0};
    f.cast=G.CombatPulse.create(owner,m.id,{channel:'body'});f.cast.targetIsLegal=()=>legal(s,f);
    choreography(f);s.action=f;s.punchReady=s.clock+.55*(owner.cdMul??1);owner.aim=aim;owner.cast?.(m);
    s.casts['lf2-punch']=(s.casts['lf2-punch']||0)+1;
    return true;
  }
  C.tick=function(dt,owner,now){
    if((owner?.mon?.dex??owner?.dex)!==DEX)return oldTick.call(this,dt,owner,now);
    if(!valid(owner) || owner.frozen || G.Game.state!=='playing' || !Number.isFinite(dt) || dt<=0)return;
    const s=state(owner),moves=(owner.moves||[]).filter(m=>supports(m.digiMode));
    for(const m of moves){m.t=Math.max(0,(m.t||0)-dt);if(m.t<=EPS && !s.ready.has(m.id))s.ready.set(m.id,s.clock);}
    if(s.action)return;
    const ready=moves.filter(m=>canCast(owner,m)).sort((a,b)=>(s.ready.get(a.id)??Infinity)-(s.ready.get(b.id)??Infinity));
    if(ready[0])cast(owner,ready[0]);
    else if(!s.swordOwned && s.clock+EPS>=s.punchReady){const base=moves.find(m=>m.digiMode==='lf2-iceball');if(base)punch(s,base);}
  };
  C.updateFields=function(dt){const result=oldUpdate.call(this,dt);update(dt);return result;};
  C.clearFields=function(owner){const result=oldClear.call(this,owner);clear(owner);return result;};
  C.drawAirFields=function(ctx){oldAir.call(this,ctx);G.LF2Art?.drawEffects?.(ctx,G.Camera);};
  G.LF2Freeze={dex:DEX,supports,handles:supports,canCast,cast,update,clear,pose,activeFor:pose,profile,targetFor,stopped,freezeStatus,frozenTargets,renderStates,
    stateFor:(owner=G.Game.player)=>{const s=states.get(owner);return s && stateLegal(s)?s:null;},
    stats:(owner=G.Game.player)=>{const s=states.get(owner);return s?{casts:{...s.casts},hits:s.hits,damage:s.damage,effects:s.effects.length}:null;}};
})();
