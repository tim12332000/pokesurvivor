/* Sendai Yuta: actor-owned sword, Rika, copied speech and timed manifestation. */
(() => {
  'use strict';
  if (G.JujutsuYuta) return;
  const DEX=30013,C=G.Combat,TAU=Math.PI*2,EPS=1e-8;
  const states=new Map(),leases=new Map(),drawableList=[];
  const kinds=new Set(['yuta-blade','yuta-rika','yuta-speech','yuta-manifest']);
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const controlled=a=>a===G.Game.player||!!G.SelfClones?.isControlled?.(a)||!!G.SelfClones?.isActor?.(a);
  const valid=a=>alive(a)&&controlled(a)&&(a.mon?.dex??a.dex)===DEX;
  const rank=m=>Math.max(1,Math.min(5,Math.floor(m?.lvl||1)));
  const clamp=n=>Math.max(0,Math.min(1,n));
  const supports=m=>kinds.has(m);
  const terminal=()=>G.Game.state==='ui'||G.Game.state==='over';
  const learned=(a,id)=>a.moves?.some(m=>m.id===id);
  const legal=s=>s&&valid(s.owner)&&s.world===G.World&&s.runEpoch===G.CombatPulse.epoch&&!terminal();
  const strong=e=>!!(e.boss||e.elite||e.legend||e.judge||e.remote);
  function state(owner) {
    let s=states.get(owner);
    if(s&&!legal(s)){clear(owner);s=null;}
    if(!s){s={owner,world:G.World,runEpoch:G.CombatPulse.epoch,clock:0,action:null,rika:null,marks:[],manifestUntil:0,manifestReadyAt:0,manifestPower:1.5,relay:null,
      companion:{owner,x:owner.x,y:owner.y,age:0,phase:'manifest',visualPhase:'loom',full:true,aim:0,alpha:0},
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
    return {range:m.range??(kind==='yuta-rika'?300:kind==='yuta-blade'?125+i*5:160+i*5),
      radius:m.radius??(kind==='yuta-rika'?105+i*5:160+i*5)};
  }
  function target(owner,m) {
    const g=geometry(m),range=m.digiMode==='yuta-speech'?g.radius:g.range;
    const nearest=(a,b)=>Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y);
    const enemies=nearby(owner.x,owner.y,range),s=states.get(owner);
    if(m.digiMode==='yuta-rika'&&s?.relay&&s.relay.until>s.clock&&enemies.includes(s.relay.target))return s.relay.target;
    const enemy=enemies.sort(nearest)[0];
    if(enemy)return enemy;
    if(m.digiMode!=='yuta-blade'&&m.digiMode!=='yuta-rika')return null;
    return (G.World.propsInCircle?.(owner.x,owner.y,range)||[]).filter(p=>!p.dead&&p.hp>0&&p.destructible!==false&&
      Math.hypot(p.x-owner.x,p.y-owner.y)<=range+(p.r||0)&&path(owner.x,owner.y,p.x,p.y,p)).sort(nearest)[0]||null;
  }
  function manifested(owner) {const s=states.get(owner);return !!(legal(s)&&s.manifestUntil>s.clock);}
  function bodyPhase(f) {
    const blade=f.kind==='blade',speech=f.kind==='speech';
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
    const t=r.phaseAge,second=r.full&&t>=.36,local=second?t-.26:t;
    r.visualPhase=local<.22-EPS?'windup':local<.30?'smash':'recoil';
    r.phaseProgress=clamp(local<.22?local/.22:local<.30?(local-.22)/.08:(local-.30)/.14);
    r.contactProgress=clamp((local-.22)/.08);
    r.frameName=r.visualPhase==='windup'?'strikeWindup':r.visualPhase==='smash'?'strikeContact':'strikeRecoil';
    r.impactPulse=clamp(1-Math.abs(t-(second?.48:.22))/.10);
  }
  function canCast(owner,m) {
    if(!valid(owner)||owner.frozen||G.Game.state!=='playing'||!supports(m?.digiMode)||!learned(owner,m.id)||(m.t||0)>EPS)return false;
    const s=state(owner);
    if(m.digiMode==='yuta-rika'&&s.rika)return false;
    if(m.digiMode!=='yuta-rika'&&s.action)return false;
    if(m.digiMode==='yuta-manifest'&&(manifested(owner)||s.manifestReadyAt>s.clock))return false;
    return !!target(owner,m);
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
      // Rika travels to a captured, reachable destination; she never tracks through walls.
      const d=Math.max(0,Math.hypot(e.x-owner.x,e.y-owner.y)-Math.min(35,g.radius*.4));
      Object.assign(f,{tx:owner.x+Math.cos(aim)*d,ty:owner.y+Math.sin(aim)*d,phase:'travel',phaseAge:0,strikes:0});
      rikaPhase(f);s.rika=f;
    }else {
      s.action=f;
      if(kind==='manifest'){
        s.manifestUntil=s.clock+6;s.manifestReadyAt=s.manifestUntil+(m.recovery??12)*(owner.cdMul??1);
        s.manifestPower=[1.5,1.6,1.7,1.8,2][rank(m)-1];f.full=true;
      }
      bodyPhase(f);
    }
    owner.aim=aim;owner.cast?.(move);
    move.t=kind==='manifest'?s.manifestReadyAt-s.clock:Math.max(.05,(move.cd??({blade:1,rika:6,speech:8}[kind]))*(owner.cdMul??1));
    move.castAt=performance.now();
    s.casts[kind]=(s.casts[kind]||0)+1;
    return true;
  }
  function hitFor(s,f,e) {
    const type=f.m.type||'fighting',mult=G.Types.mult(type,e.types),crit=Math.random()<f.critChance;
    const damage=f.damage*mult*G.Weather.mult(type)*(crit?1.5:1)*(G.NarutoSupport?.precisionMultiplier(s.owner,e)||1);
    const dx=e.x-f.x,dy=e.y-f.y,d=Math.max(1,Math.hypot(dx,dy));
    return {target:e,primaryDirectDamage:damage,color:'#c9e5eb',dx:dx/d,dy:dy/d,knock:0,eff:crit?'crit':G.Types.label(mult)};
  }
  function contact(s,f,enemies,pulse=0){
    if(!legal(s))return false;
    const result=G.CombatPulse.apply(f.cast,pulse,enemies.map(e=>hitFor(s,f,e)));
    if(result){s.hits+=result.primaryHits;s.damage+=result.primaryDamage;if(f.kind==='rika')s.rikaHits+=result.primaryHits;}
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
    if(result&&f.kind==='speech')for(const e of enemies)if(alive(e))lease(s,e,strong(e)?.6:(f.m.speechDuration??1.2));
    if(f.kind!=='speech')for(const p of G.World.propsInCircle?.(f.x,f.y,r)||[])if(p.hp>0&&p.destructible!==false&&
      Math.hypot(p.x-f.x,p.y-f.y)<=r+(p.r||0)&&path(f.x,f.y,p.x,p.y,p))G.World.damageProp?.(p,f.damage,'#c9e5eb');
    s.marks.push({x:f.x,y:f.y,radius:r,age:0,born:s.clock,kind:f.kind,aim:f.aim});
  }
  function sword(s,f) {
    const arc=f.m.bladeArc??Math.PI*2/3;
    const inside=e=>{
      const dx=e.x-f.x,dy=e.y-f.y,d=Math.hypot(dx,dy),a=Math.atan2(dy,dx)-f.aim;
      return d<=f.range+(e.r||0)&&Math.abs(Math.atan2(Math.sin(a),Math.cos(a)))<=arc/2+Math.asin(Math.min(1,(e.r||0)/Math.max(1,d)));
    };
    const enemies=nearby(f.x,f.y,f.range).filter(inside),result=contact(s,f,enemies);
    if(result&&f.m.relayMarkDuration>0){
      const chosen=enemies.filter(alive).sort((a,b)=>Math.hypot(a.x-f.x,a.y-f.y)-Math.hypot(b.x-f.x,b.y-f.y))[0];
      if(chosen)s.relay={target:chosen,until:s.clock+f.m.relayMarkDuration};
    }
    for(const p of G.World.propsInCircle?.(f.x,f.y,f.range)||[])if(p.hp>0&&p.destructible!==false&&inside(p)&&path(f.x,f.y,p.x,p.y,p))G.World.damageProp?.(p,f.damage,'#c9e5eb');
    s.marks.push({x:f.x,y:f.y,radius:f.range,arc:f.m.bladeArc??Math.PI*2/3,age:0,born:s.clock,kind:'blade',aim:f.aim});
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
  function advanceRika(s,dt) {
    const r=s.rika;if(!r)return;
    if(!learned(s.owner,r.m.id)){s.rika=null;return;}
    r.age+=dt;r.phaseAge+=dt;r.full=manifested(s.owner);
    if(r.age>3.5){s.rika=null;return;}
    if(r.phase==='travel') {
      const previous=Math.hypot(r.tx-r.x,r.ty-r.y);
      if(travel(r,r.tx,r.ty,(r.m.rikaSpeed??520)*dt)){r.phase='strike';r.phaseAge=0;}
      else if(Math.abs(previous-Math.hypot(r.tx-r.x,r.ty-r.y))<EPS){r.phase='return';r.phaseAge=0;}
    }else if(r.phase==='strike') {
      const times=r.full?[.22,.48]:[.22];
      while(r.strikes<times.length&&r.phaseAge+EPS>=times[r.strikes]){circle(s,r,r.radius,r.strikes);r.strikes++;}
      if(r.phaseAge>.7){r.phase='return';r.phaseAge=0;}
    }else if(travel(r,s.owner.x,s.owner.y,(r.m.rikaReturnSpeed??600)*dt))s.rika=null;
    rikaPhase(r);
  }
  function updateCompanion(s) {
    const a=s.companion,p=s.owner,remaining=s.manifestUntil-s.clock;
    a.age=s.clock;a.aim=s.action?.aim??p.aim??0;
    a.x=p.x+(Math.cos(a.aim)<0?40:-40);
    a.y=p.y-18;
    a.phase='manifest';a.visualPhase='loom';a.frameName='manifestLoom1';
    a.alpha=manifested(p)?Math.min(1,remaining/.3,clamp((6-remaining)/.22)):0;
    // Only one Rika is shown: independent strike actor has visual priority.
    a.visible=a.alpha>0&&!s.rika;
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
          bodyPhase(f);
          if(!f.released&&f.age+EPS>=(f.kind==='blade'?.14:f.kind==='speech'?.24:.3)){
            f.released=true;
            if(f.kind==='blade')sword(s,f);
            if(f.kind==='speech')circle(s,f,f.radius);
          }
          if(f.age>=(f.kind==='manifest'?.65:.48))s.action=null;
        }
      }
      advanceRika(s,dt);
      updateCompanion(s);
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
        G.JujutsuArt?.drawRika?.(ctx,a,{height:112,alpha:companion?a.alpha:1});
      }};
  }
  function drawables(cam=G.Camera) {
    drawableList.length=0;
    for(const s of states.values()){
      if(!legal(s))continue;
      const actor=s.rika||(s.companion.visible?s.companion:null);
      if(!actor||cam?.sees&&!cam.sees(actor.x,actor.y,128))continue;
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
      const m=moves.find(x=>x.digiMode===mode);if(m&&canCast(owner,m))cast(owner,m);
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
      manifestRemaining:Math.max(0,s.manifestUntil-s.clock),recoveryRemaining:Math.max(0,s.manifestReadyAt-Math.max(s.clock,s.manifestUntil)),manifestPower:s.manifestPower,relay:s.relay?.until>s.clock?s.relay:null,rika:s.rika,companion:s.companion,action:s.action,controls:[...leases.values()].flat().filter(l=>l.s===s).length}:null;
  }
  function statusFor(owner,m){
    const s=stateFor(owner),active=m.digiMode==='yuta-manifest'&&s&&s.manifestUntil>s.clock;
    const casting=s&&(s.action?.m.id===m.id||s.rika?.m.id===m.id);
    return {state:active?'active':casting?'casting':m.t>EPS?(m.digiMode==='yuta-manifest'?'recovery':'cooldown'):s?.action&&m.digiMode!=='yuta-rika'?'queued':'ready',remaining:m.t||0};
  }
  G.JujutsuYuta={dex:DEX,supports,canCast,cast,update,clear,draw,drawables,inspect,stateFor,statusFor,renderStates,
    pose:(owner=G.Game.player)=>stateFor(owner)?.action||null,activeFor:(owner=G.Game.player)=>stateFor(owner)?.action||null,
    formFor:(owner=G.Game.player)=>manifested(owner)?'manifest':'normal',manifested,geometry};
})();
