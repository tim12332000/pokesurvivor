/* Sendai Ryu: actor-owned, telegraphed cursed-energy artillery. */
(() => {
  'use strict';
  if (G.JjkRyu) return;
  const DEX=30014, C=G.Combat, EPS=1e-8, HEAD_HEIGHT=48, EFFECT_LIMIT=32, states=new Map();
  let effectSequence=0;
  const specs={
    'jjk-ryu':{charge:.22,cd:1.8,damage:42,range:360,radius:14},
    'jjk-ryu-spread':{charge:.35,cd:5,damage:30,range:800,radius:12},
    'jjk-ryu-impact':{charge:.45,cd:7,damage:100,range:300,radius:90},
    'jjk-ryu-ring':{charge:.32,cd:6.5,damage:48,range:112,radius:18},
    'jjk-ryu-maximum':{charge:.75,cd:5.4,damage:200,range:760,radius:72}
  };
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const controlled=a=>G.SelfClones?.isControlled?.(a)??(a===G.Game.player||!!G.SelfClones?.isActor?.(a));
  const valid=a=>alive(a)&&controlled(a)&&(a.mon?.dex??a.dex)===DEX;
  const supports=mode=>Object.hasOwn(specs,mode);
  const terminal=()=>G.Game.state==='ui'||G.Game.state==='over';
  const level=m=>Math.max(1,Math.min(5,Math.floor(m?.lvl||1)));
  const finite=(v,fallback)=>Number.isFinite(v)?v:fallback;
  const clamp=v=>Math.max(0,Math.min(1,v));
  // Stable, release-time detail: no random geometry or particle spawning per draw.
  function fragments(count,seed){
    return Array.from({length:count},(_,i)=>{
      const a=i*Math.PI*2/count+seed*.37,n=.6+.4*((i*7+seed)%11)/10;
      return {dx:Math.cos(a),dy:Math.sin(a),n};
    });
  }
  function effect(s,e){
    e.serial=++effectSequence;e.bits=fragments(e.kind==='explosion'?12:8,e.serial);
    if(e.kind==='beam'){
      const length=e.renderLength??e.length,n=Math.max(2,Math.min(28,Math.ceil(length/18)));
      e.shell=Array.from({length:n+1},(_,i)=>({x:length*i/n,
        width:(i===0?.18:i===n?.3:.48+.46*((i*7+e.serial)%11)/10)*e.radius}));
    }
    // The cap affects only old decoration, never a pending cast or damage.
    if(s.effects.length>=EFFECT_LIMIT)s.effects.shift();
    s.effects.push(e);return e;
  }
  function choreography(f){
    const maximum=f.mode==='jjk-ryu-maximum',elapsed=maximum&&f.released?f.pulseAge:Math.max(0,f.age-f.charge);
    f.chargeProgress=clamp(f.age/f.charge);
    f.phase=!f.released?'windup':elapsed<.055?'fire':'recoil';
    f.phaseAge=f.phase==='windup'?f.age:f.phase==='fire'?elapsed:Math.max(0,elapsed-.055);
    f.progress=f.phase==='windup'?f.chargeProgress:f.phase==='fire'?clamp(elapsed/.055):clamp((elapsed-.055)/.125);
    f.frameName=(maximum?'max':'light')+(f.phase==='windup'?'Charge':f.phase==='fire'?'Release':'Recoil');
    f.recoil=f.released?Math.sin(clamp(elapsed/.18)*Math.PI)*(maximum?4:2):0;
  }
  function artPoint(owner,f,name){
    const p=G.JujutsuArt?.pointFor?.(owner,f,name);
    return Number.isFinite(p?.x)&&Number.isFinite(p?.y)?p:null;
  }
  function clear(owner){if(owner)states.delete(owner);else states.clear();}
  function state(owner){
    let s=states.get(owner);
    if(s&&(s.world!==G.World||s.runEpoch!==G.CombatPulse.epoch)){clear(owner);s=null;}
    if(!s){s={owner,world:G.World,runEpoch:G.CombatPulse.epoch,clock:0,action:null,effects:[],scatter:[],rings:[],ready:new Map(),casts:{},hits:0,damage:0,coreCharge:0,recoveryUntil:0};states.set(owner,s);}
    return s;
  }
  function clearPath(ax,ay,bx,by,target=null){
    if(G.World.projectilePathClear)return G.World.projectilePathClear(ax,ay,bx,by,target,{radius:1,spacing:4,includeStart:false});
    const steps=Math.min(256,Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/4)));
    for(let i=1;i<=steps;i++){
      const x=ax+(bx-ax)*i/steps,y=ay+(by-ay)*i/steps;
      if(G.World.isWall?.(x,y))return false;
      const p=G.World.projectileBlock?.(x,y,1);if(p&&p!==target)return false;
    }
    return true;
  }
  function settings(m){
    const p=specs[m.digiMode]||specs[m.id],L=level(m)-1;
    const maximum=m.digiMode==='jjk-ryu-maximum'||m.id==='jjk-ryu-maximum';
    return {...p,range:maximum?[760,820,880,940,1040][L]:finite(m.range,p.range),radius:maximum?[72,84,96,108,128][L]:finite(m.radius,p.radius),
      damage:finite(m.dmg,p.damage*[1,1.2,1.45,1.75,2.1][L]),cd:finite(m.cd,p.cd)};
  }
  function barrageFor(owner,m){
    const L=level(m)-1,count=Math.min(16,G.Quantity.count(owner,[4,5,6,7,8][L]));
    return {count,radius:[72,84,96,108,128][L],range:[760,820,880,940,1040][L],duration:2.2,interval:1.08/Math.max(1,count-1)};
  }
  function ringFor(owner,m){
    const p=G.Jujutsu?.power?.ryu||{},L=level(m)-1;
    const count=Math.min(p.ringCap??16,G.Quantity.count(owner,(p.ringBases||[4,5,6,7,8])[L]));
    const duration=Math.max(p.ringMinDuration??6,count*(p.ringInterval??.64)),interval=duration/count;
    return {count,radius:(p.ringRadii||[224,256,288,320,360])[L],width:(p.ringWidths||[18,21,24,27,30])[L],
      yScale:.55,interval,charge:p.ringCharge??.32,cd:p.ringCd??6.5,duration};
  }
  function scatterFor(owner,m){
    const p=G.Jujutsu?.power?.ryu||{},L=level(m)-1;
    const range=(p.scatterRanges||[800,860,920,1000,1120])[L];
    return {count:Math.min(p.scatterCap??18,G.Quantity.count(owner,(p.scatterBases||[8,8,8,8,10])[L])),
      range,travelRange:range*1.6,speed:(p.scatterSpeeds||[620,650,680,720,760])[L],
      rise:.26,orbitMin:.6,orbitMax:1.15,turnRate:6.4};
  }
  const actionLegal=(s,f)=>states.get(s.owner)===s&&G.CombatPulse.legal(f.cast)&&s.owner.moves?.some(m=>m.id===f.m.id);
  function targetFor(owner,m){
    const ring=m.digiMode==='jjk-ryu-ring',profile=ring?ringFor(owner,m):null;
    const r=ring?profile.radius+profile.width:settings(m).range;
    const inRange=e=>Math.hypot(e.x-owner.x,e.y-owner.y)<=r+(e.r||0)&&
      (!ring||Math.abs(e.y-owner.y)<=profile.radius*profile.yScale+profile.width+(e.r||0));
    const enemies=[...new Set(G.EnemyMgr.queryCircle(owner.x,owner.y,r+80))].filter(e=>alive(e)&&!e.friendly&&
      inRange(e)&&(ring||clearPath(owner.x,owner.y,e.x,e.y)))
      .sort((a,b)=>Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y));
    if(m.impactTargetPolicy==='cluster'||m.digiMode==='jjk-ryu-impact'){
      const radius=settings(m).radius,score=e=>enemies.reduce((n,other)=>n+Number(Math.hypot(other.x-e.x,other.y-e.y)<=radius+(other.r||0)&&clearPath(e.x,e.y,other.x,other.y)),0);
      const scores=new Map(enemies.map(e=>[e,score(e)]));enemies.sort((a,b)=>scores.get(b)-scores.get(a)||Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y));
    }else if(m.targetPolicy==='elite'){
      const elite=e=>!!(e.boss||e.elite||e.legend||e.judge);
      enemies.sort((a,b)=>Number(elite(b))-Number(elite(a))||Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y));
    }
    if(enemies.length)return enemies[0];
    return (G.World.propsInCircle?.(owner.x,owner.y,r)||[]).filter(p=>p.destructible!==false&&p.hp>0&&
      inRange(p)&&(ring||clearPath(owner.x,owner.y,p.x,p.y,p)))
      .sort((a,b)=>Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y))[0]||null;
  }
  function canCast(owner,m){
    if(!valid(owner)||owner.frozen||G.Game.state!=='playing'||!supports(m?.digiMode))return false;
    const s=state(owner);
    return !s.action&&s.clock+EPS>=s.recoveryUntil&&(m.t||0)<=EPS&&
      (m.digiMode!=='jjk-ryu-ring'||!s.rings.some(r=>!r.dead))&&!!owner.moves?.some(x=>x.id===m.id)&&!!targetFor(owner,m);
  }
  function cast(owner,m){
    if(!canCast(owner,m))return false;
    const s=state(owner),target=targetFor(owner,m),p=settings(m),mode=m.digiMode;
    if(mode==='jjk-ryu-maximum')s.coreCharge=0;
    const scatterProfile=mode==='jjk-ryu-spread'?scatterFor(owner,m):null;
    s.action={owner,mode,m:{...m},...p,age:0,released:false,aim:Math.atan2(target.y-owner.y,target.x-owner.x),
      tx:target.x,ty:target.y,targetObject:target,x:owner.x,y:owner.y,count:scatterProfile?.count||1,scatterProfile,
      damage:p.damage*(owner.atk??1)*(G.NarutoSupport?.takeAttackBonus(owner)||1),crit:owner.critChance||0,
      sparks:fragments(mode==='jjk-ryu-maximum'?10:6,++effectSequence)};
    s.action.cast=G.CombatPulse.create(owner,m.id,{channel:'body'});
    if(mode==='jjk-ryu-maximum'){
      const barrage=barrageFor(owner,m),f=s.action;
      Object.assign(f,{followupCount:barrage.count,volleyCount:barrage.count+1,volleyIndex:0,interval:barrage.interval,
        duration:barrage.duration,mainRadius:barrage.radius,barrageAim:f.aim,baseDamage:f.damage,lastShotAt:f.charge,pulseAge:0});
      f.damage*=1.5;
    }
    if(mode==='jjk-ryu-ring')Object.assign(s.action,{charge:ringFor(owner,m).charge,ringProfile:ringFor(owner,m)});
    Object.assign(s.action,{castId:s.action.cast.castId,runEpoch:s.action.cast.runEpoch,channel:'body'});
    choreography(s.action);
    owner.aim=s.action.aim;m.t=Math.max(.05,p.cd*(owner.cdMul??1));m.castAt=performance.now();
    owner.cast?.(m);s.casts[mode]=(s.casts[mode]||0)+1;s.ready.delete(m.id);
    return true;
  }
  function hitFor(s,f,e,ratio=1){
    const type=f.m.type||'psychic',mult=G.Types.mult(type,e.types),crit=Math.random()<f.crit;
    const dmg=f.damage*ratio*mult*G.Weather.mult(type)*(crit?1.5:1)*(G.NarutoSupport?.precisionMultiplier(s.owner,e)||1);
    return {target:e,primaryDirectDamage:dmg,color:'#bff7ff',dx:Math.cos(f.aim),dy:Math.sin(f.aim),knock:0,eff:crit?'crit':G.Types.label(mult),onHit(){
      // A victim's hurt/onDealt callback can clear this owner or unlearn the
      // attack. Stop the current pulse before it reaches the next victim.
      if(!actionLegal(s,f))f.cast.runEpoch=-1;
    }};
  }
  function contact(s,f,hits,pulseIndex=0){
    const result=G.CombatPulse.apply(f.cast,pulseIndex,hits);
    if(result){
      s.hits+=result.primaryHits;s.damage+=result.primaryDamage;
      // Each real cannon cast contributes once, including spread's separate
      // projectiles. The maximum never fuels itself, nor does a cancelled hit.
      if(f.mode!=='jjk-ryu-maximum'&&result.primaryHits>0&&!f.charged&&actionLegal(s,f)&&s.owner.moves?.some(m=>m.id==='jjk-ryu-maximum')){
        f.charged=true;s.coreCharge=Math.min(3,s.coreCharge+1);
      }
    }
    return result;
  }
  function clippedLength(x,y,aim,range,radius,target=null,onBlock=null){
    const steps=Math.ceil(range/4),c=Math.cos(aim),sn=Math.sin(aim);
    for(let i=1;i<=steps;i++){
      const d=Math.min(range,i*4);
      // Width is physical: a broad beam cannot tunnel past a wall at its edge.
      for(const side of [-radius,0,radius]){
        const px=x+c*d-sn*side,py=y+sn*d+c*side;
        const blocker=G.World.projectileBlock?.(px,py,1);
        if(G.World.isWall?.(px,py))return Math.max(0,d-4);
        if(blocker&&blocker!==target&&!onBlock?.(blocker))return Math.max(0,d-4);
      }
    }
    return range;
  }
  function scatter(s,f){
    const profile=f.scatterProfile,start=f.visualStart||{x:f.x,y:f.y-HEAD_HEIGHT};
    f.scatterStruck=new Set();
    f.cast.channel='scatter';
    f.cast.targetIsLegal=e=>actionLegal(s,f)&&G.EnemyMgr.all().includes(e);
    for(let i=0;i<profile.count;i++){
      const u=profile.count>1?i/(profile.count-1):0,direction=i*Math.PI*2/profile.count+f.castId*.31;
      const shot={kind:'scatter',serial:++effectSequence,x:f.x,y:f.y,px:f.x,py:f.y,aim:-Math.PI/2,
        radius:f.radius,speed:profile.speed,range:profile.travelRange,seekRange:profile.range,distance:0,
        age:0,life:profile.rise+profile.orbitMax+profile.travelRange/profile.speed*1.8+.75,dead:false,
        phase:'rise',lift:0,cruiseHeight:76+68*u,orbitAge:0,orbitDuration:profile.orbitMin+(profile.orbitMax-profile.orbitMin)*u,
        orbitRadius:38+42*u,orbitDirection:direction,riseX:f.x,riseY:f.y,seekAge:0,target:null,
        visualAngle:-Math.PI/2,trailTime:0,trail:[{x:f.x,y:f.y,lift:0,age:0}],
        renderOffsetX:start.x-f.x,renderOffsetY:start.y-f.y,pulseIndex:i,action:f,profile};
      s.scatter.push(shot);
    }
  }
  function scatterTarget(s,shot,registered){
    const r=Math.min(shot.seekRange,shot.range-shot.distance);
    const reservations=new Map();
    for(const other of s.scatter)if(other!==shot&&!other.dead&&other.target)
      reservations.set(other.target,(reservations.get(other.target)||0)+1);
    const candidates=[...new Set(G.EnemyMgr.queryCircle(shot.x,shot.y,r+80))].filter(e=>
      registered.has(e)&&alive(e)&&!e.friendly&&Math.hypot(e.x-shot.x,e.y-shot.y)<=r+(e.r||0)&&clearPath(shot.x,shot.y,e.x,e.y));
    candidates.sort((a,b)=>Number(shot.action.scatterStruck.has(a))-Number(shot.action.scatterStruck.has(b))||
      (reservations.get(a)||0)-(reservations.get(b)||0)||Math.hypot(a.x-shot.x,a.y-shot.y)-Math.hypot(b.x-shot.x,b.y-shot.y));
    shot.targetIsProp=false;
    if(candidates.length)return candidates[0];
    const prop=(G.World.propsInCircle?.(shot.x,shot.y,r)||[]).filter(e=>e.destructible!==false&&e.hp>0&&
      Math.hypot(e.x-shot.x,e.y-shot.y)<=r+(e.r||0)&&clearPath(shot.x,shot.y,e.x,e.y,e))[0]||null;
    shot.targetIsProp=!!prop;return prop;
  }
  function scatterFlight(shot,age){
    const u=clamp(age/shot.diveDuration),ease=u*u*(3-2*u),height=shot.cruiseHeight;
    return {distance:shot.diveDistance*ease+Math.max(0,age-shot.diveDuration)*shot.speed,
      lift:height*(1-ease)+Math.sin(u*Math.PI)*Math.min(38,shot.diveDistance*.05)};
  }
  function scatterVisual(shot,previous,dt){
    const point={x:shot.x,y:shot.y,lift:shot.lift,age:shot.age};
    const dx=point.x-previous.x,dy=point.y-point.lift-(previous.y-previous.lift);
    if(Math.hypot(dx,dy)>EPS)shot.visualAngle=Math.atan2(dy,dx);
    shot.trailTime+=dt;
    if(shot.trailTime>=.02){shot.trailTime%=.02;shot.trail.push(point);}
    while(shot.trail.length>28||shot.trail[0]?.age<shot.age-.5)shot.trail.shift();
  }
  function circleContact(shot,target,distance){
    const c=Math.cos(shot.aim),sn=Math.sin(shot.aim),dx=target.x-shot.x,dy=target.y-shot.y;
    const along=dx*c+dy*sn,side=-dx*sn+dy*c,radius=shot.radius+(target.r||0);
    if(Math.abs(side)>radius)return null;
    const reach=Math.sqrt(Math.max(0,radius*radius-side*side)),at=Math.max(0,along-reach);
    return along+reach>=0&&at<=distance+EPS?at:null;
  }
  function updateScatter(s,dt){
    const registered=new Set(G.EnemyMgr.all());
    for(const shot of s.scatter){
      let remaining=dt;
      while(remaining>EPS&&!shot.dead){
        if(!actionLegal(s,shot.action)){shot.dead=true;break;}
        const step=Math.min(remaining,1/120),previous={x:shot.x,y:shot.y,lift:shot.lift};
        remaining-=step;shot.age+=step;shot.px=shot.x;shot.py=shot.y;
        if(shot.age>=shot.life){shot.dead=true;break;}
        if(shot.phase==='rise'){
          const u=clamp(shot.age/shot.profile.rise);
          shot.x=shot.riseX+Math.sin(shot.orbitDirection)*14*u*u;
          shot.y=shot.riseY+Math.cos(shot.orbitDirection)*8*u*u;
          shot.lift=shot.cruiseHeight*u;
          if(u>=1){shot.phase='orbit';shot.orbitX=shot.x;shot.orbitY=shot.y;}
        }
        if(shot.phase==='orbit'){
          shot.orbitAge=Math.max(0,shot.age-shot.profile.rise);
          const u=clamp(shot.orbitAge/shot.orbitDuration),angle=u*Math.PI*2;
          const turn=Math.atan2(Math.sin(shot.orbitDirection),Math.cos(shot.orbitDirection))*Math.sin(angle/2)**2;
          const dx=shot.orbitRadius*(1-Math.cos(angle)),dy=-shot.orbitRadius*Math.sin(angle);
          shot.x=shot.orbitX+dx*Math.cos(turn)-dy*Math.sin(turn);
          shot.y=shot.orbitY+.35*(dx*Math.sin(turn)+dy*Math.cos(turn));shot.lift=shot.cruiseHeight;
          if(u>=1){
            shot.x=shot.orbitX;shot.y=shot.orbitY;shot.phase='seek';
            shot.target=scatterTarget(s,shot,registered);
            if(shot.target)shot.aim=Math.atan2(shot.target.y-shot.y,shot.target.x-shot.x);
            shot.diveDistance=Math.max(1,shot.target?Math.hypot(shot.target.x-shot.x,shot.target.y-shot.y):shot.seekRange);
            shot.diveDuration=Math.max(.55,shot.diveDistance/shot.speed*1.15);
          }
        }
        if(shot.phase==='seek'){
          const target=shot.target,r=Math.min(shot.seekRange,shot.range-shot.distance);
          const isEnemy=registered.has(target),isProp=shot.targetIsProp&&target?.hp>0;
          if(!target||!alive(target)||(!isEnemy&&!isProp)||target.friendly||Math.hypot(target.x-shot.x,target.y-shot.y)>r+(target.r||0)||
              !clearPath(shot.x,shot.y,target.x,target.y,isProp?target:null))shot.target=scatterTarget(s,shot,registered);
          if(shot.target){
            const desired=Math.atan2(shot.target.y-shot.y,shot.target.x-shot.x),delta=Math.atan2(Math.sin(desired-shot.aim),Math.cos(desired-shot.aim));
            shot.aim+=Math.max(-shot.profile.turnRate*step,Math.min(shot.profile.turnRate*step,delta));
          }
          const before=scatterFlight(shot,shot.seekAge);
          shot.seekAge=Math.max(0,shot.age-shot.profile.rise-shot.orbitDuration);
          const after=scatterFlight(shot,shot.seekAge);shot.lift=after.lift;
          let left=Math.min(shot.range-shot.distance,Math.max(0,after.distance-before.distance));
          while(left>EPS&&!shot.dead){
            const distance=Math.min(4,left),candidates=[];
            if(shot.lift<=18){
              for(const enemy of new Set(G.EnemyMgr.queryCircle(shot.x,shot.y,distance+shot.radius+80))){
                if(!registered.has(enemy)||!alive(enemy)||enemy.friendly)continue;
                const at=circleContact(shot,enemy,distance);
                if(at!=null&&clearPath(shot.x,shot.y,enemy.x,enemy.y))candidates.push({target:enemy,at,prop:false});
              }
              for(const prop of G.World.propsInCircle?.(shot.x,shot.y,distance+shot.radius+80)||[]){
                if(prop.hp<=0||prop.destructible===false)continue;
                const at=circleContact(shot,prop,distance);
                if(at!=null&&clearPath(shot.x,shot.y,prop.x,prop.y,prop))candidates.push({target:prop,at,prop:true});
              }
            }
            const first=candidates.sort((a,b)=>a.at-b.at)[0],travel=first?.at??distance;
            const length=clippedLength(shot.x,shot.y,shot.aim,travel,shot.radius,first?.prop?first.target:null),blocked=length+EPS<travel;
            shot.x+=Math.cos(shot.aim)*(blocked?length:travel);shot.y+=Math.sin(shot.aim)*(blocked?length:travel);
            shot.distance+=blocked?length:travel;left-=travel;
            if(blocked||first){
              if(first&&!blocked){
                shot.action.scatterStruck.add(first.target);
                if(first.prop)G.World.damageProp?.(first.target,shot.action.damage,'#bff7ff');
                else contact(s,shot.action,[hitFor(s,{...shot.action,aim:shot.aim},first.target)],shot.pulseIndex);
              }
              if(actionLegal(s,shot.action))effect(s,{kind:'impact',scatter:true,x:shot.x,y:shot.y,aim:shot.aim,
                radius:shot.radius,lift:shot.lift,renderOffsetX:shot.renderOffsetX,renderOffsetY:shot.renderOffsetY,age:0,life:.24});
              shot.dead=true;
            }
          }
          if(shot.distance+EPS>=shot.range)shot.dead=true;
        }
        scatterVisual(shot,previous,step);
      }
    }
    s.scatter=s.scatter.filter(shot=>!shot.dead);
  }
  function startRing(s,f){
    const p=f.ringProfile;
    f.cast.channel='ring';
    // CombatPulse rechecks this predicate between secondary splash victims as
    // well as direct hits, so a callback cannot retain the old ring's damage.
    f.cast.targetIsLegal=e=>actionLegal(s,f)&&G.EnemyMgr.all().includes(e);
    const ring={...p,action:f,m:f.m,age:0,cycle:0,lapIndex:0,progress:0,x:s.owner.x,y:s.owner.y,
      renderOffsetX:0,renderOffsetY:0,points:[],segments:[],hitThisCycle:new Set(),
      propHits:new Set(),nextPulseIndex:0,dead:false};
    s.rings.push(ring);
    return ring;
  }
  function ringPath(s,r){
    const f=r.action,c=Math.cos(f.aim),sn=Math.sin(f.aim),t=clamp(r.age/r.duration);
    // The same live envelope drives both collision and production rendering.
    const scale=t<.4?.09+.91*(t/.4)**2:t<=.7?1:1-((t-.7)/.3)**2;
    const radius=r.radius*scale;
    r.currentRadius=radius;r.currentWidth=r.width*scale;
    const local=[{x:8,y:0,lift:HEAD_HEIGHT,lead:true}],leadSteps=16,arcSteps=96;
    // The emitter bends into a tangent before closing around the actor. It is
    // one connected cannon path, never a rotating straight ray or filled disk.
    for(let i=1;i<=leadSteps;i++){
      const t=i/leadSteps,u=1-t;
      local.push({x:u*u*u*8+3*u*u*t*radius*.6+3*u*t*t*radius+t*t*t*radius,
        y:-3*u*t*t*radius*.45,lift:HEAD_HEIGHT*u*u*u,lead:true});
    }
    const growth=clamp(r.age/r.interval),arc=Math.min(arcSteps,Math.floor(growth*arcSteps));
    for(let i=1;i<=arc;i++){const a=i*Math.PI*2/arcSteps;local.push({x:radius*Math.cos(a),y:radius*Math.sin(a),lead:false});}
    r.x=s.owner.x;r.y=s.owner.y;r.progress=growth;r.segments=[];r.points=[];
    // Project after aim rotation: the ground ellipse never stands up or turns
    // its wide axis with the target. Rendering uses these same clipped points.
    let previous={x:r.x+local[0].x*c-local[0].y*sn,y:r.y+(local[0].x*sn+local[0].y*c)*r.yScale-local[0].lift};
    const breakProp=prop=>{
      if(!actionLegal(s,f))return false;
      if(prop.destructible===false||!Number.isFinite(prop.hp))return false;
      if(!r.propHits.has(prop)&&prop.hp>0){r.propHits.add(prop);G.World.damageProp?.(prop,f.damage,'#bff7ff');}
      return prop.hp<=0;
    };
    for(let i=1;i<local.length;i++){
      const p=local[i],next={x:r.x+p.x*c-p.y*sn,y:r.y+(p.x*sn+p.y*c)*r.yScale-(p.lift||0)};
      const dx=next.x-previous.x,dy=next.y-previous.y,length=Math.hypot(dx,dy),aim=Math.atan2(dy,dx);
      const clipped=clippedLength(previous.x,previous.y,aim,length,r.currentWidth,null,breakProp);
      if(!actionLegal(s,f)){r.dead=true;return;}
      const tip={x:previous.x+Math.cos(aim)*clipped,y:previous.y+Math.sin(aim)*clipped};
      // The brief ingress disappears after the ring closes; the hollow center
      // stays safe while each subsequent real lap strikes the projected path.
      if((r.cycle===0||!p.lead)&&clipped>EPS){
        if(!r.points.length)r.points.push(previous);
        r.points.push(tip);r.segments.push({ax:previous.x,ay:previous.y,bx:tip.x,by:tip.y});
      }
      if(clipped+EPS<length)break;
      previous=next;
    }
  }
  function ringTouch(r,e){
    const radius=r.currentWidth+(e.r||0);
    return r.segments.some(p=>{
      const dx=p.bx-p.ax,dy=p.by-p.ay,len=dx*dx+dy*dy;
      const t=len>EPS?clamp(((e.x-p.ax)*dx+(e.y-p.ay)*dy)/len):0;
      const x=p.ax+dx*t,y=p.ay+dy*t;
      return Math.hypot(e.x-x,e.y-y)<=radius&&clearPath(x,y,e.x,e.y);
    });
  }
  function advanceRing(s,r,dt){
    const f=r.action;
    if(!actionLegal(s,f)){r.dead=true;return;}
    let left=Math.min(dt,Math.max(0,r.duration-r.age));
    // A bounded simulation step observes every lap even after a delayed frame;
    // damage is tied to the live curved path, not to decorative draw calls.
    while(left>EPS&&!r.dead){
      const step=Math.min(left,1/120,(r.cycle+1)*r.interval-r.age);
      r.age+=step;left-=step;ringPath(s,r);
      if(r.dead)break;
      const registered=new Set(G.EnemyMgr.all()),hits=[];
      for(const e of new Set(G.EnemyMgr.queryCircle(r.x,r.y,r.radius+r.width+80))){
        if(!registered.has(e)||!alive(e)||e.friendly||r.hitThisCycle.has(e)||!ringTouch(r,e))continue;
        r.hitThisCycle.add(e);hits.push(hitFor(s,f,e));
      }
      if(hits.length)contact(s,f,hits,r.nextPulseIndex++);
      if(!actionLegal(s,f)){r.dead=true;break;}
      if(r.age+EPS>=(r.cycle+1)*r.interval){
        r.cycle++;r.lapIndex=r.cycle;
        r.hitThisCycle.clear();r.propHits.clear();
        if(r.cycle>=r.count)r.dead=true;
      }
    }
  }
  function updateRings(s,dt){
    for(const ring of s.rings)advanceRing(s,ring,dt);
    s.rings=s.rings.filter(r=>!r.dead);
  }
  function release(s,f,pulseIndex=0){
    if(!actionLegal(s,f))return false;
    if(f.mode==='jjk-ryu-maximum'&&s.owner===G.Game.player)G.Audio?.sfx?.('shot',{kind:'cannon',main:pulseIndex===0,type:f.m.type||'psychic'});
    f.released=true;f.x=s.owner.x+Math.cos(f.aim)*8;f.y=s.owner.y+Math.sin(f.aim)*8;
    // Resolve the authored release frame now: choreography still names windup
    // until this release returns, and later recoil has a different head anchor.
    const releasePose={...f,phase:'fire',frameName:f.mode==='jjk-ryu-maximum'?'maxRelease':'lightRelease',age:f.charge};
    f.visualMuzzle=artPoint(s.owner,releasePose,'muzzle');
    const stubEnd=artPoint(s.owner,releasePose,'beamEnd');
    // The authored stub is horizontal. At steep aim angles use its source so
    // the procedural ray does not leave the side of a sideways-painted barrel.
    f.visualStart=Math.abs(Math.sin(f.aim))>.55?(f.visualMuzzle||stubEnd):(stubEnd||f.visualMuzzle);
    if(!f.visualMuzzle)effect(s,{kind:'muzzle',x:f.x,y:f.y,aim:f.aim,maximum:f.mode==='jjk-ryu-maximum',age:0,life:.16});
    if(f.mode==='jjk-ryu-impact'){
      if(Math.hypot(f.tx-f.x,f.ty-f.y)>f.range+EPS||!clearPath(f.x,f.y,f.tx,f.ty,f.targetObject))return;
      const blast=effect(s,{kind:'explosion',x:f.tx,y:f.ty,radius:f.radius,age:0,life:.48});
      const es=[...new Set(G.EnemyMgr.queryCircle(blast.x,blast.y,f.radius+80))];
      contact(s,f,es.filter(e=>alive(e)&&!e.friendly&&Math.hypot(e.x-blast.x,e.y-blast.y)<=f.radius+(e.r||0)&&clearPath(blast.x,blast.y,e.x,e.y)).map(e=>hitFor(s,f,e)));
      for(const p of G.World.propsInCircle?.(blast.x,blast.y,f.radius)||[])if(p.hp>0&&Math.hypot(p.x-blast.x,p.y-blast.y)<=f.radius+(p.r||0)&&clearPath(blast.x,blast.y,p.x,p.y,p))G.World.damageProp?.(p,f.damage,'#bff7ff');
      return;
    }
    if(f.mode==='jjk-ryu-spread'){scatter(s,f);return;}
    if(f.mode==='jjk-ryu-ring'){
      const ring=startRing(s,f);
      advanceRing(s,ring,Math.max(0,f.age-f.charge));
      s.rings=s.rings.filter(r=>!r.dead);
      return actionLegal(s,f);
    }
    const hitOnce=new Set(),candidates=[],propHits=new Set(),struckProps=new Set();
    for(let i=0;i<f.count;i++){
      const aim=f.aim+(f.count===1?0:(i-(f.count-1)/2)*(f.m.spreadStep??.20)),c=Math.cos(aim),sn=Math.sin(aim);
      const maximum=f.mode==='jjk-ryu-maximum',spread=f.mode==='jjk-ryu-spread';
      const breakProp=maximum?prop=>{
        if(!actionLegal(s,f))return false;
        if(prop.destructible===false||!Number.isFinite(prop.hp))return false;
        if(!struckProps.has(prop)&&prop.hp>0){struckProps.add(prop);G.World.damageProp?.(prop,f.damage,'#bff7ff');}
        return prop.hp<=0;
      }:null;
      const length=clippedLength(f.x,f.y,aim,f.range,f.radius,null,breakProp);
      if(!actionLegal(s,f))return false;
      const start=f.visualStart||{x:f.x,y:f.y-HEAD_HEIGHT};
      // Only the visual segment joins the baked stub. Its far tip stays at the
      // original clipped projection; the collision origin and range never move.
      const endX=f.x+c*length,endY=f.y+sn*length-HEAD_HEIGHT,dx=endX-start.x,dy=endY-start.y;
      const renderLength=dx*c+dy*sn>0?Math.hypot(dx,dy):0;
      effect(s,{kind:'beam',x:f.x,y:f.y,aim,length,radius:f.radius,maximum,spread,
        volleyIndex:f.volleyIndex,volleyCount:f.volleyCount,
        renderX:start.x,renderY:start.y,renderAim:Math.atan2(dy,dx),renderLength,age:0,
        life:maximum?(pulseIndex===0?.55:Math.min(.24,Math.max(.10,f.interval*1.2))):spread?.22:.24});
      if(length<f.range-EPS)effect(s,{kind:'impact',x:f.x+c*length,y:f.y+sn*length,aim,
        radius:f.radius,maximum,age:0,life:maximum?.42:.3});
      for(const e of [...new Set(G.EnemyMgr.queryCircle(f.x,f.y,length+80))]){
        const dx=e.x-f.x,dy=e.y-f.y,along=dx*c+dy*sn;
        if(!hitOnce.has(e)&&alive(e)&&!e.friendly&&along>=0&&along<=length&&(Math.abs(-dx*sn+dy*c)<=f.radius+(e.r||0))&&clearPath(f.x,f.y,e.x,e.y)){
          hitOnce.add(e);candidates.push({enemy:e,aim,along});
        }
      }
      // The blocker center lies beyond the clipped beam tip. Query its contact
      // envelope as well, otherwise the very chest stopping the ray is omitted.
      for(const p of G.World.propsInCircle?.(f.x,f.y,length+f.radius+8)||[]){
        const dx=p.x-f.x,dy=p.y-f.y,along=dx*c+dy*sn;
        if(!struckProps.has(p)&&!hitOnce.has(p)&&p.hp>0&&along>=0&&along<=length+(p.r||0)+4&&Math.abs(-dx*sn+dy*c)<=f.radius+(p.r||0)&&clearPath(f.x,f.y,p.x,p.y,p)){
          hitOnce.add(p);propHits.add(p);
        }
      }
    }
    const first=f.mode==='jjk-ryu-maximum'?candidates.toSorted((a,b)=>a.along-b.along)[0]?.enemy:null;
    contact(s,f,candidates.map(({enemy,aim})=>hitFor(s,{...f,aim},enemy,enemy===first?1+(f.m.firstTargetBonus||0):1)),pulseIndex);
    for(const prop of propHits){if(!actionLegal(s,f))break;G.World.damageProp?.(prop,f.damage,'#bff7ff');}
    return actionLegal(s,f);
  }
  function update(dt){
    if(terminal()){clear();return;}
    if(G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    for(const [owner,s] of states){
      if(!valid(owner)||s.world!==G.World||s.runEpoch!==G.CombatPulse.epoch){clear(owner);continue;}
      if(owner.frozen)continue;
      s.clock+=dt;
      for(const e of s.effects)e.age+=dt;
      updateScatter(s,dt);updateRings(s,dt);s.effects=s.effects.filter(e=>e.age<e.life&&!e.dead);
      const f=s.action;if(!f)continue;
      if(!owner.moves?.some(m=>m.id===f.m.id)){s.action=null;continue;}
      f.age+=dt;
      if(!f.released&&f.age+EPS>=f.charge){
        release(s,f);
        if(!actionLegal(s,f))continue;
        if(f.mode==='jjk-ryu-maximum')s.recoveryUntil=s.clock+Math.max(0,f.duration-f.age);
      }
      if(f.mode==='jjk-ryu-maximum'&&f.released){
        while(f.volleyIndex<f.followupCount&&actionLegal(s,f)){
          const next=f.volleyIndex+1,at=f.charge+.12+(next-1)*f.interval;
          if(f.age+EPS<at)break;
          const offset=next===1?0:(next%2===0?1:-1)*Math.min(.22,.22*Math.ceil((next-1)/2)/Math.ceil((f.followupCount-1)/2));
          const shot={...f,volleyIndex:next,aim:f.barrageAim+offset,radius:f.mainRadius*.7,damage:f.baseDamage*.55};
          if(!release(s,shot,next))break;
          Object.assign(f,{volleyIndex:next,lastShotAt:at,aim:shot.aim,x:shot.x,y:shot.y,visualMuzzle:shot.visualMuzzle,visualStart:shot.visualStart});
          owner.aim=shot.aim;
        }
        if(!actionLegal(s,f))continue;
        f.pulseAge=Math.max(0,f.age-f.lastShotAt);
      }
      choreography(f);
      if(f.age>=(f.mode==='jjk-ryu-maximum'?f.duration:f.charge+.18))s.action=null;
    }
  }
  function pose(owner=G.Game.player){
    const s=states.get(owner);return s&&valid(owner)&&s.world===G.World&&s.runEpoch===G.CombatPulse.epoch&&!terminal()?s.action:null;
  }
  function drawable(s){return valid(s.owner)&&s.world===G.World&&s.runEpoch===G.CombatPulse.epoch&&!terminal();}
  function charge(ctx,s,f){
    const t=f.chargeProgress,maximum=f.mode==='jjk-ryu-maximum';
    const baked=artPoint(s.owner,f,'muzzle');
    const x=baked?.x??s.owner.x+Math.cos(f.aim)*8,y=baked?.y??s.owner.y+Math.sin(f.aim)*8-HEAD_HEIGHT;
    const size=maximum?8:5;
    ctx.save();ctx.translate(x,y);
    // Inward rings compress toward the small emitter; the hand is never a source.
    ctx.strokeStyle='#6bd9ef';ctx.lineWidth=1;
    for(let i=0;i<(maximum?3:2);i++){
      const cycle=(t*1.8+i*.38)%1,r=size+2+(1-cycle)*(maximum?19:12);
      ctx.globalAlpha=(.18+.5*cycle)*(.45+.55*t);ctx.beginPath();ctx.ellipse(0,0,r,r*.64,f.aim,0,Math.PI*2);ctx.stroke();
    }
    for(const bit of f.sparks){
      const distance=size+4+(1-t)*21*bit.n;
      ctx.globalAlpha=.35+.55*t;ctx.strokeStyle='#b8f7ff';ctx.lineWidth=maximum?2:1;
      ctx.beginPath();ctx.moveTo(bit.dx*distance,bit.dy*distance);
      ctx.lineTo(bit.dx*(distance+4+3*bit.n),bit.dy*(distance+4+3*bit.n));ctx.stroke();
    }
    if(!baked){
      ctx.globalAlpha=.4+.5*t;ctx.fillStyle='#46bddf';ctx.beginPath();ctx.arc(0,0,size+3*t,0,Math.PI*2);ctx.fill();
      ctx.globalAlpha=1;ctx.fillStyle='#f4ffff';ctx.beginPath();ctx.arc(0,0,2+size*t*.65,0,Math.PI*2);ctx.fill();
    }
    ctx.restore();
  }
  function beam(ctx,e){
    const length=e.renderLength??e.length;if(length<=EPS)return;
    const fade=1-e.age/e.life,expand=.6+.4*clamp(e.age/.035),tail=1-.65*clamp((e.age-.07)/(e.life-.07));
    ctx.save();ctx.translate(e.renderX??e.x,e.renderY??e.y-HEAD_HEIGHT);ctx.rotate(e.renderAim??e.aim);ctx.lineJoin='bevel';
    // Jagged shell stays inside the same physical beam width and clipped tip.
    ctx.globalAlpha=fade*.9;ctx.fillStyle=e.maximum?'#3faccf':'#55cbe0';ctx.beginPath();
    for(let i=0;i<e.shell.length;i++){const p=e.shell[i],y=p.width*expand*tail;i?ctx.lineTo(p.x,y):ctx.moveTo(p.x,y);}
    for(let i=e.shell.length-1;i>=0;i--){const p=e.shell[i];ctx.lineTo(p.x,-p.width*expand*tail);}
    ctx.closePath();ctx.fill();
    ctx.globalAlpha=fade;ctx.strokeStyle='#a5f7ff';ctx.lineWidth=Math.max(2,e.radius*(e.maximum?.9:.65)*tail);ctx.lineCap='butt';
    ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(length,0);ctx.stroke();
    ctx.strokeStyle='#f7ffff';ctx.lineWidth=Math.max(1,e.radius*(e.maximum?.45:.26)*tail);ctx.stroke();
    if(e.maximum){
      // Two travelling pressure seams distinguish the sustained maximum output.
      ctx.strokeStyle='#d7fdff';ctx.lineWidth=1.5;ctx.globalAlpha=fade*.8;
      for(let i=0;i<2;i++){
        const x=length*clamp(e.age/.16-i*.22);
        if(x>2&&x<length){ctx.beginPath();ctx.ellipse(x,0,3,e.radius*expand*.8,0,0,Math.PI*2);ctx.stroke();}
      }
    }else if(e.spread){
      ctx.strokeStyle='#d4fcff';ctx.lineWidth=1;ctx.globalAlpha=fade*.6;
      ctx.beginPath();ctx.moveTo(length*.18,-e.radius*.45*tail);ctx.lineTo(length*.72,-e.radius*.2*tail);ctx.stroke();
    }
    // The core is full length on the damage frame; only its shell expands.
    ctx.restore();
  }
  function muzzle(ctx,e){
    const t=e.age/e.life,r=(e.maximum?20:12)*(1-.65*t);
    ctx.save();ctx.translate(e.x,e.y-HEAD_HEIGHT);ctx.rotate(e.aim);ctx.globalAlpha=(1-t)*.8;
    ctx.fillStyle='#8cecff';ctx.beginPath();ctx.moveTo(-r*.4,0);ctx.lineTo(r*.8,-r*.65);ctx.lineTo(r*1.4,0);ctx.lineTo(r*.8,r*.65);ctx.closePath();ctx.fill();
    ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(0,0,r*.4,0,Math.PI*2);ctx.fill();ctx.restore();
  }
  function burst(ctx,e){
    const t=e.age/e.life,blast=e.kind==='explosion',r=blast?e.radius:Math.max(12,e.radius*1.3);
    ctx.save();ctx.translate(e.x,e.y-(blast?12:HEAD_HEIGHT));
    // No screen-wide flash or shadow blur: the reaction remains local and bounded.
    ctx.globalAlpha=(1-t)*.85;ctx.strokeStyle='#9ceefa';ctx.lineWidth=blast?4:2;
    ctx.beginPath();ctx.ellipse(0,0,r*(.45+.55*t),r*(blast?.6:.75)*(.45+.55*t),0,0,Math.PI*2);ctx.stroke();
    ctx.globalAlpha=(1-t)*(1-t);ctx.fillStyle='#ecffff';ctx.beginPath();ctx.ellipse(0,0,r*(blast?.45:.35)*(1-t*.5),r*.5*(1-t*.5),0,0,Math.PI*2);ctx.fill();
    ctx.strokeStyle='#c7faff';ctx.lineWidth=2;
    for(const bit of e.bits){
      const d=r*(.2+.8*t)*bit.n,outer=d+5+6*(1-t);
      ctx.beginPath();ctx.moveTo(bit.dx*d,bit.dy*d*.65);ctx.lineTo(bit.dx*outer,bit.dy*outer*.65-8*t);ctx.stroke();
    }
    ctx.restore();
  }
  function scatterArt(ctx,e){
    if(e.trail?.length>1){
      ctx.save();ctx.translate(e.renderOffsetX,e.renderOffsetY);ctx.globalAlpha=.65;ctx.strokeStyle='#63dded';ctx.lineWidth=Math.max(2,e.radius*.5);
      ctx.beginPath();e.trail.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.stroke();ctx.restore();
    }
    ctx.save();ctx.translate(e.x+e.renderOffsetX,e.y+e.renderOffsetY);ctx.rotate(e.aim);
    ctx.globalAlpha=.9;ctx.fillStyle='#63dded';ctx.beginPath();ctx.ellipse(-8,0,20,e.radius*.75,0,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#f2ffff';ctx.beginPath();ctx.ellipse(-3,0,10,e.radius*.35,0,0,Math.PI*2);ctx.fill();ctx.restore();
  }
  function ringArt(ctx,r){
    if(r.dead||r.points.length<2)return;
    ctx.save();ctx.translate(r.renderOffsetX,r.renderOffsetY);ctx.lineJoin='round';ctx.lineCap='round';
    ctx.beginPath();r.points.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));
    ctx.globalAlpha=.9;ctx.strokeStyle='#46c8df';ctx.lineWidth=r.currentWidth*2;ctx.stroke();
    ctx.strokeStyle='#a5f7ff';ctx.lineWidth=r.currentWidth*1.2;ctx.stroke();
    ctx.strokeStyle='#f5ffff';ctx.lineWidth=Math.max(.1,r.currentWidth*.55);ctx.stroke();ctx.restore();
  }
  function draw(ctx){
    if(G.JujutsuVFX?.enabled)return;
    if(terminal())return;
    ctx.save();
    for(const s of states.values()){
      if(!drawable(s))continue;
      if(s.action&&!s.action.released)charge(ctx,s,s.action);
      for(const shot of s.scatter)scatterArt(ctx,shot);
      for(const ring of s.rings)ringArt(ctx,ring);
      for(const e of s.effects){
        if(e.kind==='beam')beam(ctx,e);else if(e.kind==='scatter')scatterArt(ctx,e);else if(e.kind==='muzzle')muzzle(ctx,e);else burst(ctx,e);
      }
    }
    ctx.restore();
  }
  function ground(ctx){
    if(G.JujutsuVFX?.enabled)return;
    if(terminal())return;
    ctx.save();
    for(const s of states.values()){
      if(!drawable(s))continue;
      const f=s.action;
      if(f&&!f.released&&f.mode==='jjk-ryu-impact'){
        // Exact circular footprint, rather than a flattened ellipse suggesting a different hit area.
        ctx.globalAlpha=.2+.35*f.chargeProgress;ctx.strokeStyle='#96e8f1';ctx.lineWidth=1;
        ctx.beginPath();ctx.arc(f.tx,f.ty,f.radius,0,Math.PI*2);ctx.stroke();
        ctx.beginPath();ctx.moveTo(f.tx-6,f.ty);ctx.lineTo(f.tx+6,f.ty);ctx.moveTo(f.tx,f.ty-6);ctx.lineTo(f.tx,f.ty+6);ctx.stroke();
      }
      for(const e of s.effects){
        if(e.kind!=='explosion'&&e.kind!=='impact')continue;
        const t=e.age/e.life,r=e.kind==='explosion'?e.radius:Math.max(14,e.radius);
        ctx.globalAlpha=(1-t)*.35;ctx.strokeStyle='#8c9f9c';ctx.lineWidth=2;
        ctx.beginPath();ctx.arc(e.x,e.y,r*(.45+.55*t),0,Math.PI*2);ctx.stroke();
        ctx.globalAlpha=(1-t)*.65;ctx.fillStyle='#82908d';
        for(const bit of e.bits){
          const d=r*(.25+.8*t)*bit.n,x=e.x+bit.dx*d,y=e.y+bit.dy*d*.55-8*Math.sin(t*Math.PI);
          ctx.fillRect(Math.round(x),Math.round(y),2+Math.round(2*bit.n),2);
        }
      }
    }
    ctx.restore();
  }
  const oldTick=C.tick,oldUpdate=C.updateFields,oldClear=C.clearFields,oldAir=C.drawAirFields,oldGround=C.drawGroundFields;
  C.tick=function(dt,owner,now){
    if((owner?.mon?.dex??owner?.dex)!==DEX)return oldTick.call(this,dt,owner,now);
    if(!valid(owner)||owner.frozen||G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    const s=state(owner),moves=(owner.moves||[]).filter(m=>supports(m.digiMode));
    if(!moves.some(m=>m.digiMode==='jjk-ryu-maximum'))s.coreCharge=0;
    for(const m of moves){m.t=Math.max(0,(m.t||0)-dt);if(m.t<=EPS&&!s.ready.has(m.id))s.ready.set(m.id,s.clock);}
    if(s.action||s.clock+EPS<s.recoveryUntil)return;
    const core=moves.find(m=>m.digiMode==='jjk-ryu');
    const ready=moves.filter(m=>(m.digiMode!=='jjk-ryu-maximum'||(s.coreCharge>=3&&core&&(core.t||0)<=EPS))&&canCast(owner,m))
      .sort((a,b)=>Number(b.digiMode==='jjk-ryu-maximum')-Number(a.digiMode==='jjk-ryu-maximum')||
        (s.ready.get(a.id)??Infinity)-(s.ready.get(b.id)??Infinity));
    if(ready[0]&&cast(owner,ready[0])&&ready[0].digiMode==='jjk-ryu-maximum'){
      // Maximum replaces this scheduled core shot rather than adding a fifth independent timer.
      core.t=Math.max(.05,settings(core).cd*(owner.cdMul??1));s.ready.delete(core.id);
    }
  };
  C.updateFields=function(dt){const result=oldUpdate.call(this,dt);update(dt);return result;};
  C.clearFields=function(owner){const result=oldClear.call(this,owner);clear(owner);return result;};
  C.drawAirFields=function(ctx){oldAir.call(this,ctx);draw(ctx);};
  C.drawGroundFields=function(ctx){oldGround.call(this,ctx);ground(ctx);};
  function statusFor(owner,m){
    const s=states.get(owner),coreCharge=s?.coreCharge||0,recoveryRemaining=Math.max(0,(s?.recoveryUntil||0)-(s?.clock||0));
    const scatter=s?.scatter.filter(shot=>!shot.dead&&shot.action.m.id===m.id);
    if(scatter?.length){
      const phase=scatter.some(shot=>shot.phase==='rise')?'rise':scatter.some(shot=>shot.phase==='orbit')?'orbit':'seek';
      return {state:'active',phase,count:scatter.length,remaining:Math.max(...scatter.map(shot=>shot.life-shot.age)),
        duration:Math.max(...scatter.map(shot=>shot.life)),coreCharge,chargeRequired:3,recoveryRemaining};
    }
    const ring=s?.rings.find(r=>!r.dead&&r.m.id===m.id);
    if(ring)return {state:'active',phase:'ring',remaining:Math.max(0,ring.duration-ring.age),duration:ring.duration,
      lapIndex:ring.lapIndex,count:ring.count,coreCharge,chargeRequired:3,recoveryRemaining};
    const maximum=m.digiMode==='jjk-ryu-maximum',charging=maximum&&coreCharge<3;
    const coreRemaining=owner.moves?.find(move=>move.digiMode==='jjk-ryu')?.t||0,waitingForCore=maximum&&!charging&&coreRemaining>EPS;
    return {state:s?.action?.m.id===m.id?'casting':recoveryRemaining>EPS?'recovering':m.t>EPS?'cooldown':charging?'charging':waitingForCore||s?.action?'queued':'ready',
      remaining:m.t||0,coreCharge,chargeRequired:3,recoveryRemaining,coreRemaining,reason:charging?'core-charge':waitingForCore?'core-cadence':null};
  }
  G.JjkRyu={dex:DEX,supports,handles:supports,canCast,cast,update,clear,pose,activeFor:pose,targetFor,statusFor,barrageFor,ringFor,ringProfile:ringFor,scatterFor,scatterProfile:scatterFor,
    stateFor:(owner=G.Game.player)=>{const s=states.get(owner);return s&&drawable(s)?s:null;},
    stats:(owner=G.Game.player)=>{const s=states.get(owner);return s?{casts:{...s.casts},hits:s.hits,damage:s.damage,effects:s.effects.length,
      coreCharge:s.coreCharge,chargeRequired:3,recoveryRemaining:Math.max(0,s.recoveryUntil-s.clock)}:null;}};
})();
