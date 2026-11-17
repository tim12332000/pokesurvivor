/* Classic LF2 Firen: traveling fireballs, a burning run, mouth flames and Explosion. */
(() => {
  'use strict';
  if (G.LF2Firen) return;
  const DEX=30021,C=G.Combat,EPS=1e-8,states=new Map();
  const specs={
    'lf2-firen-ball':{name:'火球 · Fire Ball',type:'fire',learnLevel:1,cd:1.35,damage:48,
      ranges:[520,580,640,700,780],radii:[14,16,18,20,22],counts:[1,2,2,3,4],cap:8,speed:690,
      sourceStart:235,charge:6/30,cycle:13/30,
      desc:'從手前射出真正飛行的火球，命中灼燒後爆散；追加火球依次播放原235／241／247出手，不會同時隔空命中。牆與障礙擋住火球，數量卡增加完整發射輪次。'},
    'lf2-firen-blaze':{name:'烈焰衝刺 · Blaze',type:'fire',learnLevel:3,cd:5.5,damage:45,
      ranges:[120,132,144,156,168],radii:[18,20,22,24,26],counts:[1,1,2,2,3],cap:6,
      sourceStart:255,charge:6/30,moveStart:3/30,cycle:12/30,recovery:6/30,groundLife:2.8,
      desc:'移動時本體燃燒衝刺並留下真正地火，依照玩家方向前進；放開方向會熄火收勢，撤退不會被拉回敵人，牆與物件阻止穿越。每輪原12/30秒衝刺留下四處火焰，數量增加完整輪次；距離為每輪衝刺尺度、半徑為地火範圍。'},
    'lf2-firen-inferno':{name:'噴火 · Inferno',type:'fire',learnLevel:5,cd:6,damage:85,
      ranges:[180,210,240,270,300],radii:[14,16,18,20,22],counts:[4,5,6,7,8],cap:16,
      sourceStart:267,charge:9/30,interval:6/30,recovery:4/30,life:30/30,
      desc:'由嘴部連續吐出原版火舌，火焰前進、成長並逐一燒過敵群；每股火焰先顯形2/30秒再開始接觸。火舌與本體各有時計，數量增加真正吐火段數；航程放大屬本作成長，不另虛構落地火。'},
    'lf2-firen-explosion':{name:'烈焰爆炸 · Explosion',type:'fire',learnLevel:8,cd:8,damage:150,
      ranges:[112,128,144,160,180],radii:[112,128,144,160,180],counts:[1,1,2,2,3],cap:6,
      sourceStart:285,charge:8/30,fullDuration:34/30,life:24/30,interval:.3,hpCostRate:.08,
      desc:'抬手凝聚後在身旁引爆原版烈焰，從109空白起勢到110真正接觸再完整散去。首次釋放支付施放時最大生命的8%，追加爆炸不重複扣血；起手與釋放時生命不足則不施放，沒有免費爆炸或無敵。生命扣除延至釋放為自動戰鬥改編。'}
  };
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const controlled=a=>G.SelfClones?.isControlled?.(a)??(a===G.Game.player||!!G.SelfClones?.isActor?.(a));
  const valid=a=>alive(a)&&controlled(a)&&(a.mon?.dex??a.dex)===DEX;
  const learned=(a,id)=>!!a.moves?.some(m=>m.id===id);
  const supports=mode=>Object.hasOwn(specs,typeof mode==='string'?mode:mode?.digiMode||mode?.id);
  const terminal=()=>G.Game.state==='ui'||G.Game.state==='over';
  const finite=(value,fallback)=>Number.isFinite(value)?value:fallback;
  const clamp=n=>Math.max(0,Math.min(1,n));
  const angle=a=>Math.atan2(Math.sin(a),Math.cos(a));
  const giant=a=>1.25**Math.max(0,a?.giantPicks||0);
  function profile(owner,m){
    const mode=m?.digiMode||m?.id,p=specs[mode];if(!p)return null;
    const L=Math.max(0,Math.min(4,(m?.lvl||1)-1));
    const count=Math.min(p.cap,Math.max(1,G.Quantity?.count(owner,p.counts[L])??p.counts[L]));
    const range=finite(m?.range,p.ranges[L]),radius=finite(m?.radius,p.radii[L]);
    const duration=mode==='lf2-firen-ball'?count*p.cycle:
      mode==='lf2-firen-blaze'?p.charge+count*p.cycle+p.recovery:
      mode==='lf2-firen-inferno'?p.charge+(count-1)*p.interval+2/30+p.recovery:p.fullDuration;
    return {...p,mode,count,range,radius,duration,damage:finite(m?.dmg,p.damage),cd:finite(m?.cd,p.cd),
      bodyScale:giant(owner),bodyRadius:24*giant(owner),dashSpeed:mode==='lf2-firen-blaze'?range/p.cycle:0,
      maxHalfWidth:mode==='lf2-firen-inferno'?radius*49/25:radius,
      groundHalfWidth:mode==='lf2-firen-blaze'?radius*16/18:0,
      healthCost:p.hpCostRate?Math.max(0,finite(owner?.maxHp,0)*p.hpCostRate):0};
  }
  function state(owner){
    let s=states.get(owner);
    if(s&&(s.world!==G.World||s.epoch!==G.CombatPulse.epoch)){clear(owner);s=null;}
    if(!s){s={owner,world:G.World,epoch:G.CombatPulse.epoch,clock:0,action:null,effects:[],ready:new Map(),
      casts:{},hits:0,damage:0,punchReady:0,punchIndex:0,healthSpent:0,blazeDistance:0,groundFires:0};states.set(owner,s);}
    return s;
  }
  const stateLegal=s=>states.get(s.owner)===s&&valid(s.owner)&&s.world===G.World&&s.epoch===G.CombatPulse.epoch;
  const legal=(s,f)=>stateLegal(s)&&learned(s.owner,f.m.id)&&G.CombatPulse.legal(f.cast);
  function clear(owner){G.LF2FirenArt?.stopSounds?.(owner);if(owner)states.delete(owner);else states.clear();}
  function firstBlock(ax,ay,bx,by,r=1,target=null){
    const steps=Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/4));
    for(let i=1;i<=steps;i++){
      const x=ax+(bx-ax)*i/steps,y=ay+(by-ay)*i/steps;
      if(G.World.isWall?.(x,y))return {x,y,wall:true};
      const prop=G.World.projectileBlock?.(x,y,r);if(prop&&prop!==target)return {x,y,prop};
    }return null;
  }
  const path=(ax,ay,bx,by,target=null)=>!firstBlock(ax,ay,bx,by,1,target);
  function nearby(x,y,r){
    return [...new Set(G.EnemyMgr.queryCircle(x,y,r+96))].filter(e=>alive(e)&&!e.friendly&&Math.hypot(e.x-x,e.y-y)<=r+(e.r||0));
  }
  function input(owner){
    if(owner===G.Game.player&&G.Input?.axis){const [x,y]=G.Input.axis(),n=Math.hypot(x,y);return n?{x:x/n,y:y/n}:null;}
    const x=owner.svx??owner._vx??0,y=owner.svy??owner._vy??0,n=Math.hypot(x,y);return n>1?{x:x/n,y:y/n}:null;
  }
  function targetFor(owner,m){
    const p=profile(owner,m);if(!p)return null;
    const reach=p.mode==='lf2-firen-blaze'?Math.max(160,p.range):p.range;
    const enemies=nearby(owner.x,owner.y,reach).filter(e=>path(owner.x,owner.y,e.x,e.y))
      .sort((a,b)=>Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y));
    if(enemies[0])return enemies[0];
    return (G.World.propsInCircle?.(owner.x,owner.y,reach)||[]).filter(p=>p.hp>0&&p.destructible!==false&&
      Math.hypot(p.x-owner.x,p.y-owner.y)<=reach+(p.r||0)&&path(owner.x,owner.y,p.x,p.y,p))
      .sort((a,b)=>Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y))[0]||null;
  }
  function canCast(owner,m){
    if(!valid(owner)||owner.frozen||G.Game.state!=='playing'||!supports(m)||!learned(owner,m.id)||(m.t||0)>EPS)return false;
    const p=profile(owner,m);if(p.healthCost&&owner.hp<=p.healthCost)return false;
    if(p.mode==='lf2-firen-blaze'&&!input(owner))return false;
    return !state(owner).action&&!!targetFor(owner,m);
  }
  function choreography(f){
    f.sourceAge=f.age;
    if(f.kind==='punch'){f.sourceStart=f.punchIndex%2?65:60;f.phase=f.age<3/30?'windup':f.age<7/30?'release':'recovery';}
    else if(f.mode==='lf2-firen-ball'){
      const cycle=Math.min(f.count-1,Math.floor(f.age/f.cycle)),local=f.age-cycle*f.cycle;
      f.sourceStart=[235,241,247][cycle%3];f.sourceAge=local;
      f.phase=local<f.charge?'windup':local<8/30?'release':'recovery';
    }else if(f.mode==='lf2-firen-blaze'){
      const end=f.stopAt??f.charge+f.count*f.cycle;
      if(f.age>=end){f.sourceStart=218;f.sourceAge=f.age-end;f.phase='recovery';}
      else {f.sourceStart=255;f.phase=f.age<f.charge?'windup':'release';}
    }else if(f.mode==='lf2-firen-inferno'){
      const end=f.charge+(f.count-1)*f.interval+2/30;
      if(f.age>=end){f.sourceStart=283;f.sourceAge=f.age-end;f.phase='recovery';}
      else {f.sourceStart=267;f.phase=f.age<f.charge?'windup':'release';}
    }else f.phase=f.age<f.charge?'windup':f.age<27/30?'release':'recovery';
    f.phaseAge=Math.max(0,f.age-(f.phase==='windup'?0:f.charge));f.progress=clamp(f.age/Math.max(.01,f.duration));
  }
  function bodySound(s,f){
    if(f.kind==='punch'||!legal(s,f))return;
    const frame=G.LF2FirenArt?.sequence?.('firen',f.sourceStart,f.sourceAge,false);if(!frame)return;
    const key=f.sourceStart+':'+(frame.id??frame.pic)+':'+frame.name;
    if(f.audioFrame===key)return;f.audioFrame=key;
    const sound=frame.sound?.match(/(?:^|\/)(\d+)\.wav$/)?.[1];if(sound)G.LF2FirenArt?.playSound?.(sound,s.owner);
  }
  function cast(owner,m){
    if(!canCast(owner,m))return false;
    const s=state(owner),p=profile(owner,m),target=targetFor(owner,m),v=input(owner);
    const aim=p.mode==='lf2-firen-blaze'&&v?Math.atan2(v.y,v.x):Math.atan2(target.y-owner.y,target.x-owner.x);
    const f={...p,owner,m:{...m},target,aim,age:0,sourceAge:0,x:owner.x,y:owner.y,pulse:0,released:false,
      emitted:0,nextTrail:p.charge,trailIndex:0,bodyHits:new Map(),healthPaid:false,
      damage:p.damage*(owner.atk??1)*(G.NarutoSupport?.takeAttackBonus(owner)||1)};
    f.cast=G.CombatPulse.create(owner,m.id,{channel:'body'});f.cast.targetIsLegal=()=>legal(s,f);
    choreography(f);s.action=f;s.ready.delete(m.id);s.casts[m.id]=(s.casts[m.id]||0)+1;bodySound(s,f);
    owner.aim=aim;owner.cast?.(m);m.t=Math.max(.05,p.cd*(owner.cdMul??1));m.castAt=performance.now();return true;
  }
  function contact(s,f,enemies,ratio=1,element='fire'){
    if(!legal(s,f))return false;
    const result=G.CombatPulse.apply(f.cast,f.pulse++,enemies.map(e=>{
      const mult=G.Types?.mult?.(element,e.types)??1,crit=Math.random()<(s.owner.critChance||0);
      return {target:e,primaryDirectDamage:f.damage*ratio*mult*(G.Weather?.mult?.(element)??1)*(crit?1.5:1),
        color:element==='fire'?'#ffb264':'#fff0ce',eff:crit?'crit':G.Types?.label?.(mult),
        onHit(){if(!legal(s,f)){f.cast.runEpoch=-1;return;}if(element==='fire')e.applyBurn?.(1);}};
    }));
    if(result&&stateLegal(s)){s.hits+=result.primaryHits;s.damage+=result.primaryDamage;}return result;
  }
  function hurtProp(s,f,p,ratio=1){if(legal(s,f)&&p?.hp>0&&p.destructible!==false)G.World.damageProp?.(p,f.damage*ratio,'#ffb264');}
  function effect(s,f,e){if(legal(s,f))s.effects.push({...e,action:f,age:e.age??0,sourceAge:0,bornClock:s.clock,dead:false});}
  function origin(s,f,frame,ground=false){
    const pose={...f,sourceReleaseFrame:frame,sourceStart:frame,sourceAge:0};
    const socket=G.LF2FirenArt?.pointFor?.(s.owner,pose,f.mode==='lf2-firen-inferno'?'mouth':'release');
    const lift=ground?0:32*(s.owner.anim?.scale||1);
    return {x:finite(socket?.x,s.owner.x),y:Number.isFinite(socket?.y)?socket.y+lift:s.owner.y,lift};
  }
  function impact(s,e){effect(s,e.action,{kind:'impact',x:e.x,y:e.y,lift:e.lift||0,aim:e.aim,life:8/30,
    sourceObject:'firen_ball',sourceStart:10,sourceLoop:false,scale:e.scale,radius:e.radius,rotateToAim:true});
    if(legal(s,e.action))G.LF2FirenArt?.playSound?.('020',s.owner);}
  function ball(s,f,index){
    const o=origin(s,f,[238,244,250][index%3]),block=firstBlock(s.owner.x,s.owner.y,o.x,o.y);
    if(block){hurtProp(s,f,block.prop);return;}
    effect(s,f,{kind:'fireball',...o,aim:f.aim,speed:f.speed,range:f.range,traveled:0,life:f.range/f.speed,
      radius:f.radius,scale:f.radius/13.5,sourceObject:'firen_ball',sourceStart:0,sourceLoop:0,rotateToAim:true,hits:new Set()});
  }
  function flame(s,f,index){
    const o=origin(s,f,index%2?274:271),block=firstBlock(s.owner.x,s.owner.y,o.x,o.y);
    if(block){hurtProp(s,f,block.prop);return;}
    effect(s,f,{kind:'mouth-flame',...o,aim:f.aim,range:f.range,traveled:0,life:30/30,
      radius:f.radius,scale:f.radius/12.5,sourceObject:'firen_flame',sourceStart:0,sourceLoop:false,rotateToAim:true,hits:new Set()});
  }
  function ground(s,f,frame){
    const o=origin(s,f,frame,true),block=firstBlock(s.owner.x,s.owner.y,o.x,o.y);
    if(block){hurtProp(s,f,block.prop,.45);return;}
    effect(s,f,{kind:'ground-fire',...o,aim:f.aim+Math.PI,life:f.groundLife+8/30,activeLife:f.groundLife,
      radius:f.radius,scale:f.radius/18,sourceObject:'firen_flame',sourceStart:50,sourceLoop:52,
      victimReady:new Map(),child:false,childSpawned:false,ratio:.45});s.groundFires++;
  }
  function explosion(s,f){
    if(!legal(s,f))return;
    if(s.owner.hp<=f.healthCost){f.cast.runEpoch=-1;s.action=null;return;}
    s.owner.hp-=f.healthCost;f.healthPaid=true;s.healthSpent+=f.healthCost;
    const o=origin(s,f,289,true);
    for(let i=0;i<f.count&&legal(s,f);i++)effect(s,f,{kind:'explosion',...o,aim:f.aim,age:-i*f.interval,
      life:24/30,radius:f.radius,scale:f.radius/73,sourceObject:'firen_flame',sourceStart:109,sourceLoop:false,hits:new Set()});
  }
  function moveBlaze(s,f,previous){
    const start=Math.max(previous,f.moveStart),end=Math.min(f.age,f.stopAt??f.charge+f.count*f.cycle);if(end<=start)return;
    const v=input(s.owner);
    if(!v){f.stopAt=Math.min(f.age,f.charge+f.count*f.cycle);f.duration=Math.min(f.duration,f.stopAt+f.recovery);choreography(f);return;}
    const aim=Math.atan2(v.y,v.x);f.aim=aim;s.owner.aim=aim;
    const native=v?Math.max(0,(s.owner.svx||0)*v.x+(s.owner.svy||0)*v.y):0;
    const distance=Math.max(0,f.dashSpeed-native)*(end-start),steps=Math.max(1,Math.ceil(distance/3));
    let moved=0;
    for(let i=0;i<steps&&legal(s,f);i++){
      const x=s.owner.x+Math.cos(aim)*distance/steps,y=s.owner.y+Math.sin(aim)*distance/steps;
      if(G.World.isFree?!G.World.isFree(x,y,s.owner.r||12):!path(s.owner.x,s.owner.y,x,y)){
        const block=firstBlock(s.owner.x,s.owner.y,x,y,s.owner.r||12);hurtProp(s,f,block?.prop,.5);
        f.blocked=true;f.stopAt=Math.min(f.age,f.charge+f.count*f.cycle);f.duration=Math.min(f.duration,f.stopAt+f.recovery);choreography(f);break;
      }
      s.owner.x=x;s.owner.y=y;moved+=distance/steps;
    }
    s.blazeDistance+=moved;f.x=s.owner.x;f.y=s.owner.y;
  }
  function capsuleTargets(s,f,x,y,aim,half,width,hits,offset=0,perp=0){
    const dx=Math.cos(aim),dy=Math.sin(aim),cx=x+dx*offset-dy*perp,cy=y+dy*offset+dx*perp;
    const inside=e=>{const along=(e.x-cx)*dx+(e.y-cy)*dy,t=clamp((along+half)/Math.max(.001,2*half));
      const px=cx+dx*(-half+2*half*t),py=cy+dy*(-half+2*half*t);return Math.hypot(e.x-px,e.y-py)<=width+(e.r||0);};
    const targets=nearby(cx,cy,half+width).filter(e=>!hits?.has(e)&&inside(e)&&path(cx,cy,e.x,e.y));
    return {targets,inside,cx,cy};
  }
  function bodyBlaze(s,f,previous){
    if(f.phase==='recovery')return;
    const start=f.charge,end=f.stopAt??f.charge+f.count*f.cycle;if(f.age+EPS<start||previous>=end)return;
    const index=Math.max(0,Math.min(f.count-1,Math.floor((f.age-start)/f.cycle)));
    let hits=f.bodyHits.get(index);if(!hits)f.bodyHits.set(index,hits=new Set());
    const q=capsuleTargets(s,f,s.owner.x,s.owner.y,f.aim,24.5*64/65*f.bodyScale,f.bodyRadius,hits,5*64/65*f.bodyScale);
    if(q.targets.length){contact(s,f,q.targets);for(const e of q.targets)hits.add(e);}
    for(const p of G.World.propsInCircle?.(q.cx,q.cy,80*f.bodyScale)||[]){if(!legal(s,f))break;if(!hits.has(p)&&q.inside(p)&&path(s.owner.x,s.owner.y,p.x,p.y,p)){hurtProp(s,f,p);hits.add(p);}}
  }
  function sourceShape(e){
    const frame=G.LF2FirenArt?.sequence?.(e.sourceObject,e.sourceStart,e.sourceAge,e.sourceLoop);
    if(frame){const itr=frame.itr?.[0];if(!itr)return null;return {offset:(itr.x+itr.w/2-frame.centerx)*e.scale,
      perp:e.rotateToAim?(itr.y+itr.h/2-frame.centery)*e.scale:0,half:itr.w/2*e.scale,width:Math.max(2,itr.h/2*e.scale),frame};}
    if(e.kind==='fireball')return {offset:-1.5*e.scale,half:27.5*e.scale,width:e.radius};
    if(e.kind==='mouth-flame')return e.age+EPS<2/30?null:{offset:22*e.scale,half:24*e.scale,width:e.radius};
    if(e.kind==='explosion')return e.age+EPS>=2/30&&e.age<18/30?{offset:0,half:0,width:e.radius}:null;
    if(e.kind==='ground-fire')return e.age+EPS>=4/30?{offset:0,half:0,width:e.radius}:null;
    return null;
  }
  function projectile(s,e,dt){
    const f=e.action;
    const originalSpeeds=[3,3,2,2,2,3,4,4,4,3,3,2,2,2,2];
    const speed=e.kind==='fireball'?e.speed:e.range/82*originalSpeeds[Math.min(14,Math.floor(Math.max(0,e.age-dt)*15))]*30;
    const distance=Math.min(speed*dt,Math.max(0,e.range-e.traveled)),steps=Math.max(1,Math.ceil(distance/4));
    for(let i=0;i<steps&&!e.dead&&legal(s,f);i++){
      const x=e.x+Math.cos(e.aim)*distance/steps,y=e.y+Math.sin(e.aim)*distance/steps;
      const block=firstBlock(e.x,e.y,x,y,e.radius*.5);
      if(block){e.x=block.x;e.y=block.y;hurtProp(s,f,block.prop);e.dead=true;if(e.kind==='fireball')impact(s,e);break;}
      e.x=x;e.y=y;e.traveled+=distance/steps;
      const shape=sourceShape(e);if(!shape)continue;
      const q=capsuleTargets(s,f,e.x,e.y,e.aim,shape.half,shape.width,e.hits,shape.offset,shape.perp||0);
      if(q.targets.length){contact(s,f,q.targets);for(const target of q.targets)e.hits.add(target);if(e.kind==='fireball'){e.dead=true;impact(s,e);}}
    }
  }
  function area(s,e){
    const shape=sourceShape(e);if(!shape)return;
    const f=e.action,r=e.kind==='explosion'?Math.min(e.radius,shape.frame?.itr?.[0]?.w/2*e.scale||e.radius):Math.min(e.radius,shape.width);
    const candidates=nearby(e.x,e.y,r).filter(v=>!e.hits?.has(v)&&!(e.victimReady?.get(v)>e.age)&&path(e.x,e.y,v.x,v.y));
    if(candidates.length){contact(s,f,candidates,e.ratio??1);for(const v of candidates){e.hits?.add(v);e.victimReady?.set(v,e.age+20/30);}}
    for(const p of G.World.propsInCircle?.(e.x,e.y,r)||[]){
      if(!legal(s,f))break;if(e.hits?.has(p)||e.victimReady?.get(p)>e.age||Math.hypot(p.x-e.x,p.y-e.y)>r+(p.r||0)||!path(e.x,e.y,p.x,p.y,p))continue;
      hurtProp(s,f,p,e.ratio??1);e.hits?.add(p);e.victimReady?.set(p,e.age+20/30);
    }
  }
  function step(s,dt){
    s.clock+=dt;const f=s.action;
    if(f){
      if(!legal(s,f))s.action=null;
      else{
        const previous=f.age;f.age+=dt;choreography(f);f.x=s.owner.x;f.y=s.owner.y;
        if(f.kind==='punch'&&f.age+EPS>=3/30&&previous<7/30){
          if(!f.released){f.released=true;G.LF2FirenArt?.playSound?.('007',s.owner);}
          const q=capsuleTargets(s,f,s.owner.x,s.owner.y,f.aim,12*f.bodyScale,22*f.bodyScale,f.punchHits,24*f.bodyScale);
          if(q.targets.length){contact(s,f,q.targets,1,'fighting');for(const e of q.targets)f.punchHits.add(e);}
        }else if(f.mode==='lf2-firen-ball'){
          while(f.emitted<f.count&&f.age+EPS>=f.emitted*f.cycle+f.charge&&legal(s,f)){ball(s,f,f.emitted);f.emitted++;f.released=true;}
        }else if(f.mode==='lf2-firen-blaze'){
          moveBlaze(s,f,previous);bodyBlaze(s,f,previous);
          const end=f.stopAt??f.charge+f.count*f.cycle;
          while(f.nextTrail<end-EPS&&f.age+EPS>=f.nextTrail&&legal(s,f)){
            const frames=[257,261,258,259,260],frame=frames[f.trailIndex===0?0:1+(f.trailIndex-1)%4];
            ground(s,f,frame);f.trailIndex++;f.nextTrail=f.charge+f.trailIndex*3/30;f.released=true;
          }
        }else if(f.mode==='lf2-firen-inferno'){
          while(f.emitted<f.count&&f.age+EPS>=f.charge+f.emitted*f.interval&&legal(s,f)){flame(s,f,f.emitted);f.emitted++;f.released=true;}
        }else if(f.mode==='lf2-firen-explosion'&&!f.released&&f.age+EPS>=f.charge){f.released=true;explosion(s,f);}
        bodySound(s,f);if(f.age+EPS>=f.duration&&s.action===f)s.action=null;
      }
    }
    for(const e of s.effects.slice()){
      if(!legal(s,e.action)){e.dead=true;continue;}
      const elapsed=e.bornClock===s.clock?0:dt;
      e.age+=elapsed;if(e.age<0)continue;e.sourceAge=e.age;
      if(e.kind==='fireball'||e.kind==='mouth-flame')projectile(s,e,elapsed);
      else if(e.kind==='explosion')area(s,e);
      else if(e.kind==='ground-fire'){
        if(!e.child&&!e.childSpawned&&e.age+EPS>=2/30){
          e.childSpawned=true;const x=e.x-Math.cos(e.aim)*17*e.scale,y=e.y-Math.sin(e.aim)*17*e.scale;
          effect(s,e.action,{...e,x,y,age:0,sourceStart:54,sourceAge:0,sourceLoop:52,child:true,childSpawned:true,victimReady:new Map(),activeLife:2.6,life:2.6+8/30});
        }
        if(e.age<e.activeLife)area(s,e);
        else {e.sourceStart=70;e.sourceLoop=false;e.sourceAge=e.age-e.activeLife;}
      }
      if(e.age+EPS>=e.life||(e.kind==='fireball'&&e.traveled>=e.range-EPS)){if(!e.dead&&e.kind==='fireball')impact(s,e);e.dead=true;}
    }
    s.effects=s.effects.filter(e=>!e.dead);
  }
  function update(dt){
    if(terminal()){clear();return;}
    if(G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    for(const [owner,s]of states){if(!stateLegal(s)){clear(owner);continue;}if(owner.frozen)continue;
      let left=dt;while(left>EPS&&stateLegal(s)){const amount=Math.min(.01,left);step(s,amount);left-=amount;}}
  }
  function punch(s,m){
    const scale=giant(s.owner),target=nearby(s.owner.x,s.owner.y,58*scale).filter(e=>path(s.owner.x,s.owner.y,e.x,e.y))[0];if(!target)return false;
    const f={kind:'punch',mode:'lf2-firen-basic-punch',owner:s.owner,m:{...m},age:0,sourceAge:0,sourceStart:60,
      aim:Math.atan2(target.y-s.owner.y,target.x-s.owner.x),duration:7/30,charge:3/30,bodyScale:scale,
      punchIndex:s.punchIndex++,punchHits:new Set(),released:false,pulse:0,damage:Math.max(20,(m.dmg||48)*.5)*(s.owner.atk??1)};
    f.cast=G.CombatPulse.create(s.owner,m.id,{channel:'body'});f.cast.targetIsLegal=()=>legal(s,f);
    choreography(f);s.action=f;s.punchReady=s.clock+.48*(s.owner.cdMul??1);s.owner.aim=f.aim;s.owner.cast?.(m);s.casts[f.mode]=(s.casts[f.mode]||0)+1;return true;
  }
  const pose=(owner=G.Game.player)=>{const s=states.get(owner);return s&&stateLegal(s)?s.action:null;};
  const renderStates=()=>[...states.values()].filter(s=>stateLegal(s)&&!terminal());
  function statusFor(owner,m){
    const s=states.get(owner),p=profile(owner,m);if(!p)return null;
    if(s?.action?.m.id===m.id)return {label:s.action.phase==='windup'?'蓄力中':s.action.phase==='recovery'?'收勢中':'施放中',fraction:0};
    if(s?.action||(m.t||0)>EPS||s?.effects.some(e=>!e.dead&&e.action?.m.id===m.id))return null;
    if(p.healthCost&&owner.hp<=p.healthCost)return {label:'生命不足（需 '+Math.ceil(p.healthCost)+'）',fraction:0,reason:'health-cost'};
    if(p.mode==='lf2-firen-blaze'&&!input(owner))return {label:'移動時施放',fraction:0,reason:'movement'};
    return null;
  }
  const oldTick=C.tick,oldUpdate=C.updateFields,oldClear=C.clearFields,oldAir=C.drawAirFields;
  C.tick=function(dt,owner,now){
    if((owner?.mon?.dex??owner?.dex)!==DEX)return oldTick.call(this,dt,owner,now);
    if(!valid(owner)||owner.frozen||G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    const s=state(owner),moves=(owner.moves||[]).filter(m=>supports(m));
    for(const m of moves){m.t=Math.max(0,(m.t||0)-dt);if(m.t<=EPS&&!s.ready.has(m.id))s.ready.set(m.id,s.clock);}
    if(s.action)return;
    const ready=moves.filter(m=>canCast(owner,m)).sort((a,b)=>(s.ready.get(a.id)??Infinity)-(s.ready.get(b.id)??Infinity));
    if(ready[0])cast(owner,ready[0]);else if(s.clock+EPS>=s.punchReady){const base=moves.find(m=>m.digiMode==='lf2-firen-ball');if(base)punch(s,base);}
  };
  C.updateFields=function(dt){const result=oldUpdate.call(this,dt);update(dt);return result;};
  C.clearFields=function(owner){const result=oldClear.call(this,owner);clear(owner);return result;};
  C.drawAirFields=function(ctx){oldAir.call(this,ctx);G.LF2FirenArt?.drawEffects?.(ctx);};
  G.LF2Firen={dex:DEX,specs,supports,handles:supports,profile,cast,canCast,targetFor,update,clear,pose,activeFor:pose,renderStates,statusFor,
    stateFor:(owner=G.Game.player)=>{const s=states.get(owner);return s&&stateLegal(s)?s:null;},
    stats:(owner=G.Game.player)=>{const s=states.get(owner);return s?{casts:{...s.casts},hits:s.hits,damage:s.damage,effects:s.effects.length,
      healthSpent:s.healthSpent,blazeDistance:s.blazeDistance,groundFires:s.groundFires}:null;}};
})();
