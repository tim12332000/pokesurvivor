/* Classic Julian: five seeking skulls, a rising strike, a heavy sphere and Big Bang. */
(() => {
  'use strict';
  if (G.LF2Julian) return;
  const DEX=30020, C=G.Combat, EPS=1e-8, states=new Map();
  const specs={
    'lf2-julian-skull':{name:'追魂骷髏 · Skull Blast',learnLevel:1,cd:2.4,damage:40,
      ranges:[560,620,680,740,820],radii:[28,30,32,34,38],counts:[5,6,7,8,10],cap:20,
      speed:450,turn:1.8,sourceStart:260,charge:4/30,fullDuration:33/30,
      releaseTimes:[4/30,9/30,16/30,21/30,26/30]},
    'lf2-julian-uppercut':{name:'邪昇拳 · Uppercut',learnLevel:3,cd:2.6,damage:80,
      ranges:[55,55,55,55,55],radii:[55,55,55,55,55],counts:[1,1,2,2,3],cap:6,
      sourceStart:235,charge:2/30,fullDuration:22/30},
    'lf2-julian-ball':{name:'毀滅巨彈 · Soul Bomb',learnLevel:5,cd:5.5,damage:110,
      ranges:[700,760,820,900,1000],radii:[61,66,71,76,84],counts:[1,1,2,2,3],cap:8,
      speed:540,sourceStart:280,charge:12/30,fullDuration:20/30},
    'lf2-julian-blast':{name:'邪神大爆發 · Big Bang',learnLevel:8,cd:8.2,damage:155,
      ranges:[104,116,128,144,160],radii:[104,116,128,144,160],counts:[1,1,2,2,3],cap:6,
      sourceStart:310,charge:12/30,fullDuration:43/30,interval:.3,life:19/30}
  };
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const controlled=a=>G.SelfClones?.isControlled?.(a)??(a===G.Game.player||!!G.SelfClones?.isActor?.(a));
  const valid=a=>alive(a)&&controlled(a)&&(a.mon?.dex??a.dex)===DEX;
  const learned=(owner,id)=>!!owner.moves?.some(m=>m.id===id);
  const supports=mode=>Object.hasOwn(specs,typeof mode==='string'?mode:mode?.digiMode);
  const terminal=()=>G.Game.state==='ui'||G.Game.state==='over';
  const finite=(v,fallback)=>Number.isFinite(v)?v:fallback;
  const angle=a=>Math.atan2(Math.sin(a),Math.cos(a));
  const giant=owner=>1.25**Math.max(0,owner?.giantPicks||0);
  function profile(owner,m){
    const mode=m?.digiMode||m?.id,base=specs[mode];if(!base)return null;
    const p={...base,...(G.LF2Bosses?.power?.[mode]||{})},L=Math.max(0,Math.min(4,(m?.lvl||1)-1));
    const count=Math.min(p.cap,Math.max(1,G.Quantity?.count(owner,p.counts[L])??p.counts[L]));
    const bodyScale=mode==='lf2-julian-uppercut'?giant(owner):1;
    return {...p,mode,count,range:finite(m?.range,p.ranges[L])*bodyScale,
      radius:finite(m?.radius,p.radii[L])*bodyScale,damage:finite(m?.dmg,p.damage),cd:finite(m?.cd,p.cd),
      duration:mode==='lf2-julian-uppercut'?p.fullDuration*count:p.fullDuration};
  }
  function state(owner){
    let s=states.get(owner);
    if(s&&(s.world!==G.World||s.epoch!==G.CombatPulse.epoch)){clear(owner);s=null;}
    if(!s){s={owner,world:G.World,epoch:G.CombatPulse.epoch,clock:0,action:null,effects:[],ready:new Map(),
      punchReady:0,punchIndex:0,casts:{},hits:0,damage:0};states.set(owner,s);}
    return s;
  }
  const stateLegal=s=>states.get(s.owner)===s&&valid(s.owner)&&s.world===G.World&&s.epoch===G.CombatPulse.epoch;
  const legal=(s,f)=>stateLegal(s)&&learned(s.owner,f.m.id)&&G.CombatPulse.legal(f.cast);
  function clear(owner){
    G.LF2BossArt?.stopSounds?.(owner);
    if(owner)states.delete(owner);else states.clear();
  }
  function firstBlock(ax,ay,bx,by,radius=1,target=null){
    const n=Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/4));
    for(let i=1;i<=n;i++){
      const x=ax+(bx-ax)*i/n,y=ay+(by-ay)*i/n;
      if(G.World.isWall?.(x,y))return {x,y,prop:null};
      const p=G.World.projectileBlock?.(x,y,radius);if(p&&p!==target)return {x,y,prop:p};
    }
    return null;
  }
  const path=(ax,ay,bx,by,target=null)=>!firstBlock(ax,ay,bx,by,1,target);
  function nearby(x,y,r){
    return [...new Set(G.EnemyMgr.queryCircle(x,y,r))].filter(e=>alive(e)&&!e.friendly&&Math.hypot(e.x-x,e.y-y)<=r+(e.r||0));
  }
  function targetFor(owner,m){
    const p=profile(owner,m);if(!p)return null;
    const enemies=nearby(owner.x,owner.y,p.range).filter(e=>path(owner.x,owner.y,e.x,e.y));
    enemies.sort((a,b)=>Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y));
    if(enemies.length)return enemies[0];
    return (G.World.propsInCircle?.(owner.x,owner.y,p.range)||[]).filter(p=>p.hp>0&&p.destructible!==false&&
      Math.hypot(p.x-owner.x,p.y-owner.y)<=profile(owner,m).range+(p.r||0)&&path(owner.x,owner.y,p.x,p.y,p))
      .sort((a,b)=>Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y))[0]||null;
  }
  function canCast(owner,m){
    return valid(owner)&&!owner.frozen&&G.Game.state==='playing'&&supports(m?.digiMode)&&learned(owner,m.id)&&
      !state(owner).action&&(m.t||0)<=EPS&&!!targetFor(owner,m);
  }
  function choreography(f){
    const local=f.mode==='lf2-julian-uppercut'?f.age%f.fullDuration:f.age;
    f.sourceAge=local;f.sourceStart=f.kind==='punch'?f.punchIndex%2?65:60:f.kind==='soul-punch'?300:f.sourceStart;
    f.phase=local+EPS<f.charge?'windup':local<f.duration-.08?'release':'recovery';
    if(f.mode==='lf2-julian-uppercut')f.phase=local<2/30?'windup':local<9/30?'release':'recovery';
    f.phaseAge=f.phase==='windup'?local:f.phase==='release'?Math.max(0,local-f.charge):Math.max(0,local-f.fullDuration+.08);
    f.progress=Math.max(0,Math.min(1,local/Math.max(.01,f.fullDuration||f.duration)));
  }
  function makeCast(s,m,p,aim,kind=p.mode){
    const f={...p,owner:s.owner,m:{...m},kind,aim,age:0,sourceAge:0,released:false,pulse:0,emitted:0,
      x:s.owner.x,y:s.owner.y,meleeHits:new Map(),damage:p.damage*(s.owner.atk??1)*(G.NarutoSupport?.takeAttackBonus(s.owner)||1)};
    f.cast=G.CombatPulse.create(s.owner,m.id,{channel:'body'});f.cast.targetIsLegal=()=>legal(s,f);
    choreography(f);return f;
  }
  function cast(owner,m){
    if(!canCast(owner,m))return false;
    const s=state(owner),p=profile(owner,m),target=targetFor(owner,m),aim=Math.atan2(target.y-owner.y,target.x-owner.x);
    const f=makeCast(s,m,p,aim);s.action=f;s.ready.delete(m.id);s.casts[m.id]=(s.casts[m.id]||0)+1;
    owner.aim=aim;owner.cast?.(m);m.t=Math.max(.05,p.cd*(owner.cdMul??1));m.castAt=performance.now();return true;
  }
  function contact(s,f,enemies,ratio=1){
    if(!legal(s,f))return false;
    const hits=enemies.map(e=>{
      const mult=G.Types?.mult?.(f.m.type||'psychic',e.types)??1,crit=Math.random()<(s.owner.critChance||0);
      return {target:e,primaryDirectDamage:f.damage*ratio*mult*(G.Weather?.mult?.(f.m.type||'psychic')??1)*(crit?1.5:1),
        color:'#db9bff',eff:crit?'crit':G.Types?.label?.(mult),knock:0,
        onHit(){if(!legal(s,f))f.cast.runEpoch=-1;}};
    });
    const result=G.CombatPulse.apply(f.cast,f.pulse++,hits);
    if(result&&stateLegal(s)){s.hits+=result.primaryHits;s.damage+=result.primaryDamage;}
    return result;
  }
  function hurtProp(s,f,p,ratio=1){
    if(legal(s,f)&&p?.hp>0&&p.destructible!==false)G.World.damageProp?.(p,f.damage*ratio,'#db9bff');
  }
  function props(s,f,x,y,r,test=()=>true,ratio=1){
    for(const p of G.World.propsInCircle?.(x,y,r)||[]){
      if(!legal(s,f))break;
      if(p.hp>0&&p.destructible!==false&&Math.hypot(p.x-x,p.y-y)<=r+(p.r||0)&&test(p)&&path(x,y,p.x,p.y,p))hurtProp(s,f,p,ratio);
    }
  }
  const sound=(id,owner)=>G.LF2BossArt?.playSound?.(id,owner);
  function releasePoint(s,f,time){
    const lift=49*84/86*giant(s.owner),socket=G.LF2BossArt?.pointFor?.(s.owner,{...f,sourceAge:time},'release');
    return {x:finite(socket?.x,s.owner.x),y:Number.isFinite(socket?.y)?socket.y+lift:s.owner.y,lift};
  }
  function spawnShot(s,f,index,total,time,kind){
    if(!legal(s,f))return;
    const socket=releasePoint(s,f,time),dx=Math.cos(f.aim),dy=Math.sin(f.aim),offset=(index-(total-1)/2)*f.radius*1.5;
    const x=socket.x-dy*offset,y=socket.y+dx*offset,block=firstBlock(s.owner.x,s.owner.y,x,y);
    if(block){hurtProp(s,f,block.prop);return;}
    const skull=kind==='skull';
    s.effects.push({kind,action:f,x,y,lift:socket.lift,aim:f.aim,age:0,sourceAge:0,life:f.range/f.speed+(skull?2/30:0),
      radius:f.radius,speed:f.speed,range:f.range,traveled:0,hits:new Set(),dead:false,
      sourceObject:skull?'julian_ball':'julian_ball2',sourceStart:skull?100:0,sourceLoop:skull?0:2,
      scale:f.radius/(skull?28:61),target:null,startup:skull?2/30:0});
  }
  function spawnBang(s,f,index){
    if(!legal(s,f))return;
    const x=s.owner.x,y=s.owner.y;
    s.effects.push({kind:'big-bang',action:f,x,y,lift:0,aim:f.aim,age:-index*f.interval,sourceAge:0,
      life:f.life,radius:f.radius,dead:false,hit:false,sourceObject:'julian_ball2',sourceStart:40,
      scale:f.radius/90,index});
  }
  function impact(s,e){
    if(!legal(s,e.action))return;
    const sphere=e.kind==='soul-ball';
    s.effects.push({kind:'impact',action:e.action,x:e.x,y:e.y,lift:e.lift,aim:e.aim,age:0,sourceAge:0,
      life:sphere?22/30:11/30,radius:e.radius,sourceObject:sphere?'julian_ball2':'julian_ball',
      sourceStart:sphere?110:10,scale:e.scale,dead:false});
    if(sphere){sound('089',s.owner);contact(s,e.action,nearby(e.x,e.y,e.radius*1.15).filter(v=>path(e.x,e.y,v.x,v.y)),.65);}
  }
  function release(s,f){
    if(f.mode==='lf2-julian-skull'){
      for(let i=f.emitted;i<f.releaseTimes.length&&legal(s,f);i++){
        if(f.age+EPS<f.releaseTimes[i])break;
        const before=Math.floor(i*f.count/5),after=Math.floor((i+1)*f.count/5),n=after-before;
        for(let j=0;j<n&&legal(s,f);j++)spawnShot(s,f,j,n,f.releaseTimes[i],'skull');
        f.emitted=i+1;f.released=true;sound('091',s.owner);
      }
    }else if(!f.released&&f.age+EPS>=f.charge){
      f.released=true;
      if(f.mode==='lf2-julian-ball'){for(let i=0;i<f.count&&legal(s,f);i++)spawnShot(s,f,i,f.count,f.charge,'soul-ball');sound('019',s.owner);}
      if(f.mode==='lf2-julian-blast'){for(let i=0;i<f.count&&legal(s,f);i++)spawnBang(s,f,i);sound('089',s.owner);}
    }
  }
  function meleeStep(s,f,previous){
    const upper=f.mode==='lf2-julian-uppercut',period=upper?f.fullDuration:f.duration;
    for(let i=0;i<(upper?f.count:1)&&legal(s,f);i++){
      const windows=upper?[[2/30,4/30,1],[6/30,9/30,.75]]:f.kind==='soul-punch'?[[0,6/30,1]]:[[3/30,5/30,1]];
      let ledger=f.meleeHits.get(i);if(!ledger)f.meleeHits.set(i,ledger=new Set());
      for(const [a,b,ratio]of windows){
        const start=i*period+a,end=i*period+b;if(f.age+EPS<start||previous>=end-EPS)continue;
        if(!f.hitSounds)f.hitSounds=new Set();
        if(!f.hitSounds.has(i)){sound(f.kind==='soul-punch'?'031':'007',s.owner);f.hitSounds.add(i);}
        const inside=e=>Math.hypot(e.x-s.owner.x,e.y-s.owner.y)<=f.range+(e.r||0)&&
          Math.abs(angle(Math.atan2(e.y-s.owner.y,e.x-s.owner.x)-f.aim))<=.9+Math.asin(Math.min(1,(e.r||0)/Math.max(1,Math.hypot(e.x-s.owner.x,e.y-s.owner.y))));
        const victims=nearby(s.owner.x,s.owner.y,f.range).filter(e=>!ledger.has(e)&&inside(e)&&path(s.owner.x,s.owner.y,e.x,e.y));
        if(victims.length){contact(s,f,victims,ratio);for(const e of victims)ledger.add(e);}
        props(s,f,s.owner.x,s.owner.y,f.range,p=>!ledger.has(p)&&inside(p),ratio);
        for(const p of G.World.propsInCircle?.(s.owner.x,s.owner.y,f.range)||[])if(inside(p))ledger.add(p);
      }
    }
  }
  function advanceShot(s,e,dt){
    const f=e.action;if(e.age<e.startup)return;
    if(e.kind==='skull'){
      e.sourceStart=0;e.sourceLoop=0;e.sourceAge=Math.max(0,e.age-e.startup);
      if(!alive(e.target)||e.target.friendly||!path(e.x,e.y,e.target.x,e.target.y)){
        e.target=nearby(e.x,e.y,Math.min(360,e.range-e.traveled+e.radius)).filter(v=>path(e.x,e.y,v.x,v.y))
          .sort((a,b)=>Math.hypot(a.x-e.x,a.y-e.y)-Math.hypot(b.x-e.x,b.y-e.y))[0]||null;
      }
      if(e.target){const delta=angle(Math.atan2(e.target.y-e.y,e.target.x-e.x)-e.aim);e.aim+=Math.max(-f.turn*dt,Math.min(f.turn*dt,delta));}
    }
    const distance=Math.min(e.speed*dt,Math.max(0,e.range-e.traveled)),steps=Math.max(1,Math.ceil(distance/4));
    for(let i=0;i<steps&&!e.dead&&legal(s,f);i++){
      const x=e.x+Math.cos(e.aim)*distance/steps,y=e.y+Math.sin(e.aim)*distance/steps;
      const block=firstBlock(e.x,e.y,x,y,Math.max(1,e.radius*.45));
      if(block){e.x=block.x;e.y=block.y;hurtProp(s,f,block.prop);e.dead=true;impact(s,e);break;}
      e.x=x;e.y=y;e.traveled+=distance/steps;
      const victims=nearby(x,y,e.radius).filter(v=>!e.hits.has(v)&&path(x,y,v.x,v.y));
      if(victims.length){
        contact(s,f,victims);for(const v of victims)e.hits.add(v);
        if(e.kind==='skull'){e.dead=true;impact(s,e);break;}
      }
    }
    if(e.traveled+EPS>=e.range){e.dead=true;if(e.kind==='soul-ball')impact(s,e);}
  }
  function step(s,dt){
    s.clock+=dt;const f=s.action;
    if(f){
      if(!legal(s,f))s.action=null;
      else{
        const previous=f.age;f.age+=dt;f.x=s.owner.x;f.y=s.owner.y;choreography(f);release(s,f);
        if(f.mode==='lf2-julian-uppercut'||f.kind==='punch'||f.kind==='soul-punch')meleeStep(s,f,previous);
        if(f.age+EPS>=f.duration&&s.action===f)s.action=null;
      }
    }
    // Effects born by an impact are processed on the next substep; drawing is read-only.
    const effects=s.effects.slice();
    for(const e of effects){
      if(!legal(s,e.action)){e.dead=true;continue;}
      e.age+=dt;e.sourceAge=e.age;if(e.age<0)continue;
      if(e.kind==='skull'||e.kind==='soul-ball')advanceShot(s,e,dt);
      if(!legal(s,e.action)||e.dead)continue;
      if(e.kind==='big-bang'&&!e.hit&&e.age+EPS>=0){
        e.hit=true;const victims=nearby(e.x,e.y,e.radius).filter(v=>path(e.x,e.y,v.x,v.y));
        contact(s,e.action,victims);props(s,e.action,e.x,e.y,e.radius);
      }
      if(e.age+EPS>=e.life)e.dead=true;
    }
    s.effects=s.effects.filter(e=>!e.dead);
  }
  function update(dt){
    if(terminal()){clear();return;}
    if(G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    for(const [owner,s]of states){
      if(!stateLegal(s)){clear(owner);continue;}
      if(owner.frozen)continue;
      let left=dt;while(left>EPS&&stateLegal(s)){const amount=Math.min(.02,left);step(s,amount);left-=amount;}
    }
  }
  function fallback(s,m){
    const reach=55*giant(s.owner),target=nearby(s.owner.x,s.owner.y,reach).filter(e=>path(s.owner.x,s.owner.y,e.x,e.y))[0];
    if(!target)return false;
    const owner=s.owner,dx=target.x-owner.x,dy=target.y-owner.y,aim=Math.atan2(dy,dx),speed=Math.hypot(owner._vx||0,owner._vy||0);
    const soul=speed>20&&((owner._vx||0)*dx+(owner._vy||0)*dy)>speed*Math.hypot(dx,dy)*.45;
    const p={mode:soul?'lf2-julian-soul-punch':'lf2-julian-punch',sourceStart:soul?300:s.punchIndex%2?65:60,
      damage:soul?Math.max(48,(m.dmg||40)*1.4):Math.max(26,(m.dmg||40)*.7),range:reach,radius:reach,count:1,
      charge:soul?0:3/30,fullDuration:soul?14/30:5/30,duration:soul?14/30:5/30};
    const f=makeCast(s,m,p,aim,soul?'soul-punch':'punch');f.punchIndex=s.punchIndex++;choreography(f);
    s.action=f;s.punchReady=s.clock+(soul?.7:.42)*(owner.cdMul??1);owner.aim=aim;owner.cast?.(m);
    s.casts[p.mode]=(s.casts[p.mode]||0)+1;return true;
  }
  function pose(owner=G.Game.player){const s=states.get(owner);return s&&stateLegal(s)?s.action:null;}
  const renderStates=()=>[...states.values()].filter(s=>stateLegal(s)&&!terminal());
  const oldTick=C.tick,oldUpdate=C.updateFields,oldClear=C.clearFields,oldAir=C.drawAirFields;
  C.tick=function(dt,owner,now){
    if((owner?.mon?.dex??owner?.dex)!==DEX)return oldTick.call(this,dt,owner,now);
    if(!valid(owner)||owner.frozen||G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    const s=state(owner),moves=(owner.moves||[]).filter(m=>supports(m.digiMode));
    for(const m of moves){m.t=Math.max(0,(m.t||0)-dt);if(m.t<=EPS&&!s.ready.has(m.id))s.ready.set(m.id,s.clock);}
    if(s.action)return;
    const ready=moves.filter(m=>canCast(owner,m)).sort((a,b)=>(s.ready.get(a.id)??Infinity)-(s.ready.get(b.id)??Infinity));
    if(ready[0])cast(owner,ready[0]);else if(s.clock+EPS>=s.punchReady){const base=moves.find(m=>m.digiMode==='lf2-julian-skull');if(base)fallback(s,base);}
  };
  C.updateFields=function(dt){const result=oldUpdate.call(this,dt);update(dt);return result;};
  C.clearFields=function(owner){const result=oldClear.call(this,owner);clear(owner);return result;};
  C.drawAirFields=function(ctx){oldAir.call(this,ctx);G.LF2BossArt?.drawEffects?.(ctx,DEX);};
  G.LF2Julian={dex:DEX,specs,supports,handles:supports,profile,canCast,cast,update,clear,pose,activeFor:pose,targetFor,renderStates,
    stateFor:(owner=G.Game.player)=>{const s=states.get(owner);return s&&stateLegal(s)?s:null;},
    stats:(owner=G.Game.player)=>{const s=states.get(owner);return s?{casts:{...s.casts},hits:s.hits,damage:s.damage,effects:s.effects.length}:null;}};
})();
