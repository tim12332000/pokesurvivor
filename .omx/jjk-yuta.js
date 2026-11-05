/* Sendai Yuta: actor-owned sword, Rika, copied speech and timed manifestation. */
(() => {
  'use strict';
  if (G.JujutsuYuta) return;
  const DEX=30013,C=G.Combat,TAU=Math.PI*2,EPS=1e-8;
  const states=new Map(),leases=new Map(),drawableList=[];
  const kinds=new Set(['yuta-blade','yuta-rika','yuta-speech','yuta-manifest','yuta-resonance']);
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const controlled=a=>a===G.Game.player||!!G.SelfClones?.isControlled?.(a)||!!G.SelfClones?.isActor?.(a);
  const valid=a=>alive(a)&&controlled(a)&&(a.mon?.dex??a.dex)===DEX;
  const rank=m=>Math.max(1,Math.min(5,Math.floor(m?.lvl||1)));
  const clamp=n=>Math.max(0,Math.min(1,n));
  const supports=m=>kinds.has(m);
  const terminal=()=>G.Game.state==='ui'||G.Game.state==='over';
  const learned=(a,id)=>a.moves?.some(m=>m.id===id);
  const legal=s=>s&&states.get(s.owner)===s&&valid(s.owner)&&s.world===G.World&&s.runEpoch===G.CombatPulse.epoch&&!terminal();
  const power=()=>G.Jujutsu.power.yuta;
  function rikaProfile(owner,m,full=manifested(owner)){
    const c=power(),i=rank(m)-1,base=c.rikaBases[i]*(full?2:1);
    const count=Math.min(full?c.fullCap:c.rikaCap,G.Quantity.count(owner,base));
    return {count,range:c.rikaRanges[i],radius:c.rikaRadii[i]*(full?1.3:1),
      height:(full?c.fullHeights:c.normalHeights)[i],speed:c.rikaSpeeds[i],interval:Math.max(.09,1/Math.max(1,count-1))};
  }
  const duetActive=s=>!!(s.rika?.full&&s.rika.phase==='strike'&&s.manifestUntil>s.clock);
  const strong=e=>!!(e.boss||e.elite||e.legend||e.judge||e.remote);
  function state(owner) {
    let s=states.get(owner);
    if(s&&!legal(s)){clear(owner);s=null;}
    if(!s){s={owner,world:G.World,runEpoch:G.CombatPulse.epoch,clock:0,action:null,rika:null,duetPose:null,pendingResonance:[],marks:[],manifestUntil:0,manifestReadyAt:0,manifestPower:1.5,relay:null,
      companion:{owner,x:owner.x-40,y:owner.y-18,age:0,phase:'idle',visualPhase:'idle',full:false,aim:0,alpha:1,visible:false},
      casts:{},hits:0,damage:0,rikaHits:0};
      s.drawables={strike:makeDrawable(s,false),companion:makeDrawable(s,true)};
      states.set(owner,s);}
    return s;
  }
  function path(ax,ay,bx,by,target=null) {
    if(G.World.projectilePathClear)return G.World.projectilePathClear(ax,ay,bx,by,target,{radius:1,spacing:5,includeStart:false});
    const n=Math.min(256,Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/5)));
    for(let i=1;i<=n;i++) {
      const x=ax+(bx-ax)*i/n,y=ay+(by-ay)*i/n;
      if(G.World.isWall?.(x,y))return false;
      const p=G.World.projectileBlock?.(x,y,1);if(p&&p!==target)return false;
    }
    return true;
  }
  function nearby(x,y,r) {
    return [...new Set(G.EnemyMgr.queryCircle(x,y,r+80))].filter(e=>alive(e)&&!e.friendly&&
      Math.hypot(e.x-x,e.y-y)<=r+(e.r||0)&&path(x,y,e.x,e.y));
  }
  function geometry(m) {
    const i=rank(m)-1,kind=m.digiMode;
    if(kind==='yuta-rika')return {range:power().rikaRanges[i],radius:power().rikaRadii[i]};
    if(kind==='yuta-resonance')return {range:power().resonanceRadii[i],radius:power().resonanceRadii[i]};
    return {range:m.range??(kind==='yuta-rika'?300:kind==='yuta-blade'?125+i*5:160+i*5),
      radius:m.radius??(kind==='yuta-rika'?105+i*5:160+i*5)};
  }
  function target(owner,m) {
    const g=geometry(m),range=m.digiMode==='yuta-speech'?g.radius:g.range;
    const nearest=(a,b)=>Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y);
    const enemies=nearby(owner.x,owner.y,range),s=states.get(owner);
    if(m.digiMode==='yuta-rika'&&s?.relay&&s.relay.until>s.clock&&enemies.includes(s.relay.target))return s.relay.target;
    enemies.sort(nearest);
    // The sword handles close pressure; Rika extends the pair's reach instead
    // of routinely spending her long cooldown on that same nearby enemy.
    const blade=owner.moves?.find(move=>move.digiMode==='yuta-blade');
    const bladeRange=blade?geometry(blade).range:125;
    const remote=m.digiMode==='yuta-rika'?enemies.find(e=>Math.hypot(e.x-owner.x,e.y-owner.y)>bladeRange+(e.r||0)):null;
    const enemy=remote||enemies[0];
    if(enemy)return enemy;
    if(m.digiMode!=='yuta-blade'&&m.digiMode!=='yuta-rika')return null;
    return (G.World.propsInCircle?.(owner.x,owner.y,range)||[]).filter(p=>!p.dead&&p.hp>0&&p.destructible!==false&&
      Math.hypot(p.x-owner.x,p.y-owner.y)<=range+(p.r||0)&&path(owner.x,owner.y,p.x,p.y,p)).sort(nearest)[0]||null;
  }
  function manifested(owner) {const s=states.get(owner);return !!(legal(s)&&s.manifestUntil>s.clock);}
  function bodyPhase(f) {
    const blade=f.kind==='blade'||f.kind==='resonance',speech=f.kind==='speech';
    const contact=blade?.14:speech?.24:.3,recover=blade?.24:speech?.34:.5,end=f.kind==='manifest'?.65:.48;
    const start=f.age<contact?0:f.age<recover?contact:recover;
    f.visualPhase=f.age<contact?'windup':f.age<recover?(blade?'slash':'release'):'recovery';
    f.phaseProgress=clamp((f.age-start)/((f.age<contact?contact:f.age<recover?recover:end)-start));
    f.contactProgress=clamp((f.age-contact)/Math.max(.01,recover-contact));
    f.frameName=blade?(f.visualPhase==='windup'?'bladeWindup':f.visualPhase==='slash'?'bladeSlash':'bladeRecovery'):
      speech?(f.visualPhase==='windup'?'speechWindup':f.visualPhase==='release'?'speechRelease':'speechRecovery'):
      f.visualPhase==='windup'?'ringRaise':f.visualPhase==='release'?'ringGlow':'ringRecovery';
  }
  function rikaPhase(r) {
    if(r.phase!=='strike'){r.visualPhase=r.phase;r.phaseProgress=0;r.contactProgress=0;return;}
    const local=r.strikeIndex?Math.max(0,r.phaseAge-(.22+(r.strikeIndex-1)*r.interval)):r.phaseAge;
    r.pulseAge=local;
    const contact=Math.min(.055,r.interval*.35),prepare=Math.min(.08,r.interval*.4);
    r.visualPhase=!r.strikeIndex?'windup':local<contact?'smash':r.strikeIndex<r.strikeCount&&local>=r.interval-prepare?'windup':'recoil';
    r.phaseProgress=clamp(!r.strikeIndex?local/.22:r.visualPhase==='smash'?local/contact:r.visualPhase==='windup'?(local-r.interval+prepare)/prepare:(local-contact)/Math.max(.01,r.interval-prepare-contact));
    r.contactProgress=r.visualPhase==='smash'?clamp(local/contact):0;
    r.frameName=r.visualPhase==='windup'?'strikeWindup':r.visualPhase==='smash'?'strikeContact':'strikeRecoil';
    r.impactPulse=r.strikeIndex?clamp(1-local/contact):0;
  }
  function canCast(owner,m) {
    if(!valid(owner)||owner.frozen||G.Game.state!=='playing'||!supports(m?.digiMode)||!learned(owner,m.id)||(m.t||0)>EPS)return false;
    const s=state(owner);
    if(m.digiMode==='yuta-resonance')return false;
    if(m.digiMode==='yuta-rika'&&s.rika)return false;
    if(m.digiMode!=='yuta-rika'&&duetActive(s))return false;
    if(m.digiMode!=='yuta-rika'&&s.action)return false;
    if(m.digiMode==='yuta-manifest'&&(manifested(owner)||s.manifestReadyAt>s.clock))return false;
    return !!target(owner,m);
  }
  function autoPolicy(owner,m) {
    if(m.digiMode==='yuta-speech'){
      const enemies=nearby(owner.x,owner.y,geometry(m).radius);
      return enemies.length>=3||enemies.some(e=>Math.hypot(e.x-owner.x,e.y-owner.y)<=90+(e.r||0))?null:'pressure';
    }
    if(m.digiMode==='yuta-manifest'){
      const enemies=nearby(owner.x,owner.y,geometry(m).range);
      return enemies.length>=3||enemies.some(strong)?null:'encounter';
    }
    return null;
  }
  function cast(owner,move) {
    if(!canCast(owner,move))return false;
    const s=state(owner),m={...move},kind=m.digiMode.slice(5),e=target(owner,m),g=geometry(m);
    const aim=Math.atan2(e.y-owner.y,e.x-owner.x),full=manifested(owner);
    const f={owner,m,kind,age:0,aim,x:owner.x,y:owner.y,...g,full,
      damage:(m.dmg??({blade:30,rika:100,speech:35,manifest:0}[kind]))*(owner.atk??1)*(full?s.manifestPower:1),
      critChance:owner.critChance||0,released:false,hits:new Set()};
    f.cast=G.CombatPulse.create(owner,m.id,{channel:kind==='rika'?'companion':'body'});
    Object.assign(f,{castId:f.cast.castId,runEpoch:f.cast.runEpoch,channel:f.cast.channel});
    if(kind==='rika') {
      // One persistent companion owns every excursion; neither form changes
      // nor refreshes create another actor or reset her physical position.
      const profile=rikaProfile(owner,m,full),a=s.companion,x=a.x,y=a.y;
      Object.assign(a,f,profile,{x,y,tx:e.x,ty:e.y,phase:'travel',phaseAge:0,strikes:0,strikeIndex:0,strikeCount:profile.count,
        pursuitTarget:e,travelDistance:0,travelBudget:profile.range+profile.radius,finisher:false,resonanceQueued:false,visible:true,alpha:1});
      const blade=owner.moves?.find(move=>move.digiMode==='yuta-blade');
      a.blade=full&&blade?{...blade}:null;
      a.bladeCast=a.blade?G.CombatPulse.create(owner,blade.id,{channel:'duet'}):null;
      a.bladeDamage=a.blade?(a.blade.dmg||30)*(owner.atk??1)*s.manifestPower*.6:0;
      rikaPhase(a);s.rika=a;
    }else {
      s.action=f;
      if(kind==='manifest'){
        s.manifestUntil=s.clock+power().manifestDuration;s.manifestReadyAt=s.manifestUntil+power().recoveries[rank(m)-1]*(owner.cdMul??1);
        s.manifestPower=[1.5,1.6,1.7,1.8,2][rank(m)-1];f.full=true;
        // One refresh at activation makes the companion part of the burst.
        // An existing strike still owns the sole Rika actor until it returns.
        const rika=owner.moves?.find(move=>move.digiMode==='yuta-rika');
        if(rika)rika.t=0;
      }
      bodyPhase(f);
    }
    owner.aim=aim;owner.cast?.(move);
    move.t=kind==='manifest'?s.manifestReadyAt-s.clock:Math.max(.05,(kind==='rika'?(full?power().fullRikaCd:power().rikaCd):(move.cd??({blade:1,speech:8}[kind])))*(owner.cdMul??1));
    move.castAt=performance.now();
    s.casts[kind]=(s.casts[kind]||0)+1;
    return true;
  }
  function hitFor(s,f,e) {
    const type=f.m.type||'fighting',mult=G.Types.mult(type,e.types),crit=Math.random()<f.critChance;
    const damage=f.damage*mult*G.Weather.mult(type)*(crit?1.5:1)*(G.NarutoSupport?.precisionMultiplier(s.owner,e)||1);
    const dx=e.x-f.x,dy=e.y-f.y,d=Math.max(1,Math.hypot(dx,dy));
    return {target:e,primaryDirectDamage:damage,color:'#c9e5eb',dx:dx/d,dy:dy/d,knock:0,eff:crit?'crit':G.Types.label(mult),onHit(){
      // Native hurt/onDealt callbacks may clear the scene or remove this skill.
      // Invalidate the ledger before CombatPulse reaches the next direct hit.
      if(!legal(s)||!learned(s.owner,f.m.id))f.cast.runEpoch=-1;
    }};
  }
  function contact(s,f,enemies,pulse=0){
    if(!legal(s)||!learned(s.owner,f.m.id))return false;
    const result=G.CombatPulse.apply(f.cast,pulse,enemies.map(e=>hitFor(s,f,e)));
    if(result&&legal(s)){s.hits+=result.primaryHits;s.damage+=result.primaryDamage;if(f.kind==='rika')s.rikaHits+=result.primaryHits;}
    return result;
  }
  function lease(s,e,duration) {
    let list=leases.get(e);if(!list)leases.set(e,list=[]);
    const old=list.find(l=>l.s===s),until=s.clock+duration,factor=strong(e)?.65:0;
    if(old){old.until=Math.max(old.until,until);old.factor=factor;}
    else list.push({s,until,factor});
  }
  function circle(s,f,r,pulse=0) {
    const enemies=nearby(f.x,f.y,r),result=contact(s,f,enemies,pulse);
    if(!legal(s)||!learned(s.owner,f.m.id))return false;
    if(result&&f.kind==='speech')for(const e of enemies)if(alive(e))lease(s,e,strong(e)?.6:(f.m.speechDuration??1.2));
    if(f.kind!=='speech')for(const p of G.World.propsInCircle?.(f.x,f.y,r)||[])if(legal(s)&&learned(s.owner,f.m.id)&&p.hp>0&&p.destructible!==false&&
      Math.hypot(p.x-f.x,p.y-f.y)<=r+(p.r||0)&&path(f.x,f.y,p.x,p.y,p))G.World.damageProp?.(p,f.damage,'#c9e5eb');
    if(legal(s)&&learned(s.owner,f.m.id))s.marks.push({x:f.x,y:f.y,radius:r,age:0,born:s.clock,kind:f.kind,aim:f.aim,full:f.full,finisher:f.finisher,strikeIndex:f.strikeIndex,castId:f.castId});
    return result;
  }
  function sword(s,f,pulse=0) {
    const arc=f.m.bladeArc??Math.PI*2/3;
    const inside=e=>{
      const dx=e.x-f.x,dy=e.y-f.y,d=Math.hypot(dx,dy),a=Math.atan2(dy,dx)-f.aim;
      return d<=f.range+(e.r||0)&&Math.abs(Math.atan2(Math.sin(a),Math.cos(a)))<=arc/2+Math.asin(Math.min(1,(e.r||0)/Math.max(1,d)));
    };
    const enemies=nearby(f.x,f.y,f.range).filter(inside),result=contact(s,f,enemies,pulse);
    if(!legal(s)||!learned(s.owner,f.m.id))return false;
    if(result&&f.m.relayMarkDuration>0){
      const chosen=enemies.filter(alive).sort((a,b)=>Math.hypot(a.x-f.x,a.y-f.y)-Math.hypot(b.x-f.x,b.y-f.y))[0];
      if(chosen)s.relay={target:chosen,until:s.clock+f.m.relayMarkDuration};
    }
    for(const p of G.World.propsInCircle?.(f.x,f.y,f.range)||[])if(legal(s)&&learned(s.owner,f.m.id)&&p.hp>0&&p.destructible!==false&&inside(p)&&path(f.x,f.y,p.x,p.y,p))G.World.damageProp?.(p,f.damage,'#c9e5eb');
    if(legal(s)&&learned(s.owner,f.m.id))s.marks.push({x:f.x,y:f.y,radius:f.range,arc:f.m.bladeArc??Math.PI*2/3,age:0,born:s.clock,kind:'blade',aim:f.aim,full:f.full,finisher:f.finisher,strikeIndex:f.strikeIndex,castId:f.castId});
    return result;
  }
  function travel(r,tx,ty,amount) {
    const dx=tx-r.x,dy=ty-r.y,d=Math.hypot(dx,dy),step=Math.min(d,amount),n=Math.max(1,Math.ceil(step/5));
    if(d<EPS)return true;
    for(let i=0;i<n;i++){
      const x=r.x+dx/d*step/n,y=r.y+dy/d*step/n;
      if(!path(r.x,r.y,x,y))return false;
      r.x=x;r.y=y;
    }
    return Math.hypot(tx-r.x,ty-r.y)<.2;
  }
  function returnRika(s,r){r.phase='return';r.phaseAge=0;s.duetPose=null;}
  function companionHome(s){const p=s.owner,aim=s.action?.aim??p.aim??0;return {x:p.x+(Math.cos(aim)<0?40:-40),y:p.y-18};}
  function tracked(r){const e=r.pursuitTarget;return alive(e)&&!e.friendly&&G.EnemyMgr.all().includes(e)&&path(r.x,r.y,e.x,e.y)?e:null;}
  function approach(r,e,amount){
    const dx=e.x-r.x,dy=e.y-r.y,d=Math.hypot(dx,dy),distance=Math.max(0,d-35);
    if(d>EPS)r.aim=Math.atan2(dy,dx);
    r.tx=r.x+Math.cos(r.aim)*distance;r.ty=r.y+Math.sin(r.aim)*distance;
    const x=r.x,y=r.y,arrived=travel(r,r.tx,r.ty,Math.min(amount,Math.max(0,r.travelBudget-r.travelDistance)));
    r.travelDistance+=Math.hypot(r.x-x,r.y-y);return arrived;
  }
  function queueResonance(s,r,result){
    const m=s.owner.moves?.find(move=>move.digiMode==='yuta-resonance');
    if(!legal(s)||!m||r.resonanceQueued||!result?.primaryHits)return;
    r.resonanceQueued=true;
    s.pendingResonance.push({id:m.id,m:{...m},damage:(m.dmg||80)*(s.owner.atk??1)*(r.full?s.manifestPower:1),
      radius:power().resonanceRadii[rank(m)-1],aim:r.aim,full:r.full});
  }
  function duetStrike(s,r,pulse){
    if(!r.blade||!learned(s.owner,r.blade.id))return;
    const f={owner:s.owner,m:{...r.blade,bladeArc:2.6},kind:'blade',cast:r.bladeCast,castId:r.bladeCast.castId,
      x:s.owner.x,y:s.owner.y,aim:r.aim,range:power().duetRanges[rank(r.blade)-1],damage:r.bladeDamage,
      critChance:r.critChance,full:true,finisher:r.finisher,strikeIndex:r.strikeIndex};
    sword(s,f,pulse);
  }
  function advanceRika(s,dt) {
    const r=s.rika;if(!r)return;
    if(!learned(s.owner,r.m.id)){s.rika=null;s.duetPose=null;r.visible=false;return;}
    r.age+=dt;
    if(r.age>8){s.rika=null;s.duetPose=null;return;}
    if(r.full&&!manifested(s.owner)){
      r.full=false;r.height=power().normalHeights[rank(r.m)-1];returnRika(s,r);
    }
    // Finish a pre-existing body action before beginning the dual-actor rhythm.
    if(r.phase==='strike'&&r.full&&s.action){rikaPhase(r);return;}
    r.phaseAge+=dt;
    if(r.phase==='travel'){
      const e=tracked(r);
      if(!e||r.phaseAge>1.4||r.travelDistance>=r.travelBudget-EPS){returnRika(s,r);}
      else{
        const before=r.travelDistance,arrived=approach(r,e,r.speed*dt);
        if(arrived){r.phase='strike';r.phaseAge=0;}
        else if(r.travelDistance-before<EPS)returnRika(s,r);
      }
    }else if(r.phase==='strike'){
      // Reposition only in the recovery between real beats. Windup/contact has
      // a fixed origin; the same target can still escape behind an obstacle.
      const since=r.strikeIndex?r.phaseAge-(.22+(r.strikeIndex-1)*r.interval):0,e=tracked(r);
      if(r.strikeIndex&&r.strikeIndex<r.strikeCount&&since>.055&&since<r.interval-.035&&e&&r.travelDistance<r.travelBudget)
        approach(r,e,r.speed*dt);
      while(legal(s)&&s.rika===r&&r.strikeIndex<r.strikeCount&&r.phaseAge+EPS>=.22+r.strikeIndex*r.interval){
        const pulse=r.strikeIndex;r.finisher=pulse===r.strikeCount-1;
        const hit={...r,damage:r.damage*(r.finisher?(r.full?1.2:1):.65),strikeIndex:pulse};
        const result=circle(s,hit,r.radius,pulse);
        if(!legal(s)||s.rika!==r)return;
        if(!learned(s.owner,r.m.id)){s.rika=null;s.duetPose=null;r.visible=false;return;}
        if(s.owner===G.Game.player)G.Audio?.sfx('shot',{kind:'rika',finisher:r.finisher});
        if(r.full)duetStrike(s,r,pulse);
        if(!legal(s)||s.rika!==r)return;
        if(r.finisher)queueResonance(s,r,result);
        r.strikeIndex++;r.strikes=r.strikeIndex;
      }
      if(r.phaseAge>=.22+(r.strikeCount-1)*r.interval+.20)returnRika(s,r);
    }else{
      const home=companionHome(s);
      if(travel(r,home.x,home.y,(r.m.rikaReturnSpeed??720)*dt)){s.rika=null;s.duetPose=null;}
    }
    rikaPhase(r);
    if(duetActive(s)&&r.blade&&learned(s.owner,r.blade.id)){
      const visualPhase=r.visualPhase==='smash'?'slash':r.visualPhase==='windup'?'windup':'recovery';
      s.duetPose={owner:s.owner,kind:'blade',mode:'yuta-blade',m:r.blade,age:r.pulseAge,aim:r.aim,phaseAge:r.pulseAge,
        full:true,duet:true,strikeIndex:r.strikeIndex,strikeCount:r.strikeCount,pulseAge:r.pulseAge,finisher:r.finisher,
        visualPhase,phaseProgress:r.phaseProgress,contactProgress:r.contactProgress,
        frameName:visualPhase==='windup'?'bladeWindup':visualPhase==='slash'?'bladeSlash':'bladeRecovery'};
    }else s.duetPose=null;
  }
  function updateCompanion(s,dt) {
    const a=s.companion,m=s.owner.moves?.find(move=>move.digiMode==='yuta-rika'),full=manifested(s.owner);
    // Ring activation can be learned independently. Its full companion is a
    // visual actor until the attack skill is learned, never a free excursion.
    if(!m&&!full){a.visible=false;a.full=false;return;}
    a.visible=true;a.alpha=1;
    if(s.rika)return;
    const source=m||s.owner.moves.find(move=>move.digiMode==='yuta-manifest'),home=companionHome(s),before=Math.hypot(a.x-home.x,a.y-home.y);
    travel(a,home.x,home.y,720*dt);
    a.age=s.clock;a.phase=before>3?'follow':'idle';a.visualPhase=a.phase;a.full=full;
    a.height=rikaProfile(s.owner,source,full).height;a.aim=s.action?.aim??s.owner.aim??0;
    a.frameName=full?'manifestLoom1':null;
  }
  function startResonance(s){
    if(!s.pendingResonance.length||s.action||duetActive(s))return;
    const q=s.pendingResonance.shift();if(!learned(s.owner,q.id)||!legal(s))return;
    const cast=G.CombatPulse.create(s.owner,q.id,{channel:'resonance'});
    const f={...q,owner:s.owner,kind:'resonance',age:0,x:s.owner.x,y:s.owner.y,range:q.radius,cast,castId:cast.castId,
      critChance:s.owner.critChance||0,released:false};
    s.action=f;bodyPhase(f);s.owner.cast?.(q.m);s.casts.resonance=(s.casts.resonance||0)+1;
  }
  function update(dt) {
    for(const [owner,s] of states)if(!legal(s))clear(owner);
    if(G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    for(const s of states.values()){
      if(s.owner.frozen)continue;
      s.clock+=dt;
      if(!s.owner.moves?.some(m=>m.digiMode==='yuta-manifest'))s.manifestUntil=0;
      const f=s.action;
      if(f){
        if(!learned(s.owner,f.m.id))s.action=null;
        else {
          f.age+=dt;
          // Body attacks leave the moving caster at contact; the released hit
          // and its marks keep that exact position through recovery.
          if(!f.released&&(f.kind==='blade'||f.kind==='speech'||f.kind==='resonance')){f.x=s.owner.x;f.y=s.owner.y;}
          bodyPhase(f);
          if(!f.released&&f.age+EPS>=(f.kind==='blade'||f.kind==='resonance'?.14:f.kind==='speech'?.24:.3)){
            f.released=true;
            if(f.kind==='blade')sword(s,f);
            if(f.kind==='speech')circle(s,f,f.radius);
            if(f.kind==='resonance')circle(s,f,f.radius);
            if(f.kind==='resonance'&&legal(s)&&s.owner===G.Game.player)G.Audio?.sfx('shot',{kind:'rika',finisher:true});
          }
          if(!legal(s))continue;
          if(f.age>=(f.kind==='manifest'?.65:.48))s.action=null;
        }
      }
      advanceRika(s,dt);
      if(!legal(s))continue;
      startResonance(s);
      updateCompanion(s,dt);
      for(const m of s.marks)m.age=s.clock-m.born;s.marks=s.marks.filter(m=>m.age<.32);
    }
    for(const [e,list] of leases){
      const next=list.filter(l=>alive(e)&&legal(l.s)&&l.until>l.s.clock&&l.s.owner.moves?.some(m=>m.digiMode==='yuta-speech'));
      if(next.length)leases.set(e,next);else leases.delete(e);
    }
  }
  function clear(owner) {
    if(owner)states.delete(owner);else states.clear();
    drawableList.length=0;
    for(const [e,list] of leases){const next=list.filter(l=>states.get(l.s.owner)===l.s);if(next.length)leases.set(e,next);else leases.delete(e);}
  }
  function renderStates(){return [...states.values()].filter(legal);}
  function makeDrawable(s,companion) {
    // Two wrappers per state are reused for the entire run; no per-frame actor allocation.
    return {x:0,y:0,actor:null,owner:s.owner,kind:companion?'yuta-manifest-rika':'yuta-strike-rika',
      draw(ctx){
        const a=this.actor;
        if(states.get(s.owner)!==s||!legal(s)||!a||
          (companion?!a.visible||s.rika:s.rika!==a))return;
        G.JujutsuArt?.drawRika?.(ctx,a,{height:a.height??88,alpha:companion?a.alpha:1});
      }};
  }
  function drawables(cam=G.Camera) {
    drawableList.length=0;
    for(const s of states.values()){
      if(!legal(s))continue;
      const actor=s.rika||(s.companion.visible?s.companion:null);
      if(!actor||cam?.sees&&!cam.sees(actor.x,actor.y,actor.height||128))continue;
      const d=s.rika?s.drawables.strike:s.drawables.companion;
      d.actor=actor;d.x=actor.x;
      // Sort behind the owner while keeping the actual contact/foot coordinates untouched.
      d.y=Math.min(actor.y,s.owner.y-.01);drawableList.push(d);
    }
    return drawableList;
  }
  function drawMouthSeal(ctx,s,f) {
    const p=s.owner,x=p.x+Math.cos(f.aim)*6,y=p.y-(p.bodyH||48)*.78-(G.LIFT||0);
    const strength=f.visualPhase==='windup'?.3+.7*f.phaseProgress:1-f.phaseProgress*.6;
    ctx.globalAlpha=.85*strength;ctx.strokeStyle='#c4a7e1';ctx.lineWidth=1.5;
    for(const sign of [-1,1]){
      ctx.beginPath();ctx.arc(x+sign*6,y,3,sign<0?-.7:Math.PI-.7,sign<0?2.2:Math.PI+2.2);ctx.stroke();
    }
    ctx.beginPath();ctx.moveTo(x-3,y);ctx.lineTo(x+3,y);ctx.stroke();
  }
  function drawRingGlint(ctx,s,f) {
    const p=s.owner,x=p.x+Math.cos(f.aim)*9,y=p.y-(p.bodyH||48)*.9-(G.LIFT||0);
    const strength=f.visualPhase==='windup'?f.phaseProgress:f.visualPhase==='release'?1:.35*(1-f.phaseProgress);
    ctx.globalAlpha=.85*strength;ctx.strokeStyle='#9aeeff';ctx.lineWidth=1.5;
    ctx.beginPath();ctx.arc(x,y,2.5,0,TAU);ctx.stroke();
    ctx.beginPath();ctx.moveTo(x-7,y);ctx.lineTo(x+7,y);ctx.moveTo(x,y-5);ctx.lineTo(x,y+5);ctx.stroke();
  }
  function draw(ctx,ground=false) {
    for(const s of renderStates()){
      ctx.save();
      const action=s.action;
      if(!ground&&action?.kind==='speech')drawMouthSeal(ctx,s,action);
      if(!ground&&action?.kind==='manifest')drawRingGlint(ctx,s,action);
      if(!G.JujutsuVFX?.enabled&&ground&&s.rika?.phase==='strike'){
        const r=s.rika;ctx.globalAlpha=r.visualPhase==='windup'?.18:.1;ctx.strokeStyle='#c8dce5';ctx.lineWidth=1;
        ctx.beginPath();ctx.arc(r.x,r.y-(G.LIFT||0),r.radius,0,TAU);ctx.stroke();
      }
      for(const f of s.marks){
        if(G.JujutsuVFX?.enabled&&(f.kind==='blade'||f.kind==='rika'))continue;
        ctx.globalAlpha=(1-f.age/.32)*.65;ctx.strokeStyle=f.kind==='speech'?'#d4b5ff':'#d1f6ff';ctx.lineWidth=f.kind==='blade'?5:3;
        const y=f.y-(ground?0:12)-(G.LIFT||0);
        if(ground&&f.kind==='rika'){
          // Five bounded impact fissures point along the captured strike direction.
          for(let i=0;i<5;i++){
            const a=f.aim+(i-2)*.59,length=f.radius*(.55+.1*(i%3));
            ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(f.x,f.y-(G.LIFT||0));
            ctx.lineTo(f.x+Math.cos(a)*length*.45,f.y+Math.sin(a+.08)*length*.45-(G.LIFT||0));
            ctx.lineTo(f.x+Math.cos(a+.11)*length,f.y+Math.sin(a)*length-(G.LIFT||0));ctx.stroke();
          }
        }
        if(!ground&&f.kind==='speech'){
          // Leading footprint is the actual hit radius; trailing sound ripples stay inside it.
          ctx.globalAlpha*=.45;ctx.beginPath();ctx.arc(f.x,y,f.radius,0,TAU);ctx.stroke();
          for(let i=0;i<2;i++){
            const progress=clamp(f.age/.24-i*.26);if(progress<=0)continue;
            ctx.globalAlpha=(1-progress)*.7;ctx.lineWidth=2-i*.7;
            ctx.beginPath();ctx.arc(f.x,y,f.radius*progress,0,TAU);ctx.stroke();
          }
          ctx.globalAlpha=1-f.age/.32;ctx.font='bold 14px sans-serif';ctx.textAlign='center';ctx.fillStyle='#f4e8ff';ctx.fillText('別動',f.x,y-28);
        }
        if(!ground&&f.kind==='blade'){
          const sweep=clamp(f.age/.1),head=f.aim-Math.PI/3+sweep*Math.PI*2/3;
          ctx.lineWidth=2;ctx.globalAlpha*=.5;ctx.beginPath();ctx.arc(f.x,y,f.radius,f.aim-Math.PI/3,f.aim+Math.PI/3);ctx.stroke();
          ctx.globalAlpha=(1-f.age/.32)*.9;ctx.lineWidth=4;ctx.beginPath();ctx.arc(f.x,y,f.radius,Math.max(f.aim-Math.PI/3,head-.55),head);ctx.stroke();
        }
      }
      ctx.restore();
    }
  }
  const oldTick=C.tick,oldUpdate=C.updateFields,oldClear=C.clearFields,oldAir=C.drawAirFields,oldGround=C.drawGroundFields;
  C.tick=function(dt,owner,now){
    if((owner?.mon?.dex??owner?.dex)!==DEX)return oldTick.call(this,dt,owner,now);
    if(!valid(owner)||owner.frozen||G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    state(owner);
    const moves=(owner.moves||[]).filter(m=>supports(m.digiMode));
    for(const m of moves)m.t=Math.max(0,(m.t||0)-dt);
    // Manifestation and independent Rika do not starve the sword's body-action queue.
    for(const mode of ['yuta-manifest','yuta-rika','yuta-speech','yuta-blade']){
      const m=moves.find(x=>x.digiMode===mode);if(m&&canCast(owner,m)&&!autoPolicy(owner,m))cast(owner,m);
    }
  };
  C.updateFields=function(dt){const result=oldUpdate.call(this,dt);update(dt);return result;};
  C.clearFields=function(owner){const result=oldClear.call(this,owner);clear(owner);return result;};
  C.drawAirFields=function(ctx){oldAir.call(this,ctx);draw(ctx);};
  C.drawGroundFields=function(ctx){oldGround.call(this,ctx);draw(ctx,true);};
  const enemyUpdate=G.Enemy?.prototype.update;
  if(enemyUpdate)G.Enemy.prototype.update=function(...args){
    const x=this.x,y=this.y,result=enemyUpdate.apply(this,args),list=leases.get(this);
    if(G.Game.state==='playing'&&alive(this)&&list){
      const factors=list.filter(l=>legal(l.s)&&l.until>l.s.clock&&!l.s.owner.frozen).map(l=>l.factor);
      if(factors.length){const factor=Math.min(...factors);this.x=x+(this.x-x)*factor;this.y=y+(this.y-y)*factor;}
    }
    return result;
  };
  for(const method of ['toUI','quit'])if(typeof G.Game[method]==='function'){
    const previous=G.Game[method];G.Game[method]=function(...args){const result=previous.apply(this,args);if(terminal())clear();return result;};
  }
  const stateFor=(owner=G.Game.player)=>{const s=states.get(owner);return legal(s)?s:null;};
  function inspect(owner=G.Game.player){
    const s=stateFor(owner);return s?{clock:s.clock,casts:{...s.casts},hits:s.hits,damage:s.damage,rikaHits:s.rikaHits,
      manifestRemaining:Math.max(0,s.manifestUntil-s.clock),recoveryRemaining:Math.max(0,s.manifestReadyAt-Math.max(s.clock,s.manifestUntil)),manifestPower:s.manifestPower,relay:s.relay?.until>s.clock?s.relay:null,rika:s.rika,companion:s.companion,action:s.action,duetPose:s.duetPose,pendingResonance:s.pendingResonance.length,controls:[...leases.values()].flat().filter(l=>l.s===s).length}:null;
  }
  function statusFor(owner,m){
    const s=stateFor(owner),active=m.digiMode==='yuta-manifest'&&s&&s.manifestUntil>s.clock;
    const casting=s&&(s.action?.m.id===m.id||s.rika?.m.id===m.id);
    if(m.digiMode==='yuta-resonance')return {state:casting?'casting':s?.pendingResonance.length?'queued':'ready',remaining:0,reason:'finisher'};
    const reason=autoPolicy(owner,m);
    return {state:active?'active':casting?'casting':m.t>EPS?(m.digiMode==='yuta-manifest'?'recovery':'cooldown'):s?.action&&m.digiMode!=='yuta-rika'?'queued':reason?'waiting':'ready',remaining:m.t||0,reason};
  }
  G.JujutsuYuta={dex:DEX,supports,canCast,cast,autoPolicy,update,clear,draw,drawables,inspect,stateFor,statusFor,renderStates,rikaProfile,
    pose:(owner=G.Game.player)=>stateFor(owner)?.duetPose||stateFor(owner)?.action||null,activeFor:(owner=G.Game.player)=>stateFor(owner)?.duetPose||stateFor(owner)?.action||null,
    formFor:(owner=G.Game.player)=>manifested(owner)?'manifest':'normal',manifested,geometry};
})();
