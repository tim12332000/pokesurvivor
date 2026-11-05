/* Uro: finite sky screens and spatial fan attacks, owned by the casting actor. */
(() => {
  'use strict';
  if (G.JjkUro) return;
  const DEX=30015, C=G.Combat, states=new Map(), effects=[];
  const specs={
    'uro-sky':{cd:1.25,dmg:20,range:210,arc:.95,release:.18,duration:.48},
    'uro-thin-ice':{cd:4.8,dmg:72,range:250,arc:1.9,release:.34,duration:.8},
    'uro-screen':{cd:9,dmg:0,range:250,radius:82,release:0,duration:2.3},
    'uro-collapse':{cd:8,dmg:112,range:280,radius:110,release:.55,duration:1.05}
  };
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const controlled=a=>G.SelfClones?.isControlled?.(a)??(a===G.Game.player);
  const valid=a=>alive(a)&&controlled(a)&&(a.mon?.dex??a.dex)===DEX;
  const playing=()=>G.Game.state==='playing';
  const terminal=()=>G.Game.state==='ui'||G.Game.state==='over';
  const supports=mode=>Object.hasOwn(specs,mode);
  const learned=(owner,id)=>owner.moves?.find(m=>m.id===id);
  const rank=m=>Math.max(1,Math.min(5,Math.floor(m?.lvl||1)));
  const delta=(a,b)=>Math.atan2(Math.sin(a-b),Math.cos(a-b));
  const clearPath=(x,y,tx,ty,target=null)=>G.World.projectilePathClear?.(x,y,tx,ty,target,{radius:1,spacing:5,includeStart:false})??true;
  function state(owner){
    let s=states.get(owner);
    if(s&&(s.world!==G.World||s.runEpoch!==G.CombatPulse.epoch)){clear(owner);s=null;}
    if(!s){s={owner,world:G.World,runEpoch:G.CombatPulse.epoch,cooldowns:{},ready:new Map(),clock:0,pose:null,screen:null,counterUntil:0,counterBonus:0,castCounts:{},hits:0,intercepted:0};states.set(owner,s);}
    return s;
  }
  function targets(x,y,r){
    return [...new Set(G.EnemyMgr.queryCircle(x,y,r+60))].filter(e=>alive(e)&&!e.friendly&&Math.hypot(e.x-x,e.y-y)<=r+(e.r||0)&&clearPath(x,y,e.x,e.y));
  }
  function props(x,y,r){
    return [...new Set(G.World.propsInCircle?.(x,y,r)||[])].filter(p=>!p.dead&&p.destructible!==false&&p.hp>0&&Math.hypot(p.x-x,p.y-y)<=r+(p.r||0)&&clearPath(x,y,p.x,p.y,p));
  }
  function target(owner,m){
    const r=m.range||specs[m.digiMode].range;
    const enemies=targets(owner.x,owner.y,r),candidates=enemies.length||m.digiMode==='uro-screen'?enemies:props(owner.x,owner.y,r);
    return candidates.sort((a,b)=>Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y))[0];
  }
  function canCast(owner,m){
    if(!playing()||!valid(owner)||owner.frozen||!supports(m?.digiMode)||!learned(owner,m.id))return false;
    if(state(owner).pose)return false;
    if((learned(owner,m.id).t||0)>1e-8)return false;
    if(m.digiMode==='uro-screen'&&m.threatOnly)return threatened(owner,m);
    return !!target(owner,m)||(m.digiMode==='uro-screen'&&G.Projectiles.all().some(p=>!p.friendly&&Math.hypot(p.x-owner.x,p.y-owner.y)<260));
  }
  function threatened(owner,m){
    const radius=m.radius||82,horizon=m.threatHorizon??.55;
    return G.Projectiles.all().some(p=>{
      if(p.friendly||p.uroReturned)return false;
      const x=p.x-owner.x,y=p.y-owner.y,vx=p.vx||0,vy=p.vy||0,speed2=vx*vx+vy*vy;
      if(speed2<1e-8)return false;
      const approach=x*vx+y*vy;
      if(approach>=0&&Math.hypot(x,y)>(owner.r||14)+(p.r||0))return false;
      const t=Math.max(0,Math.min(horizon,-approach/speed2)),tx=p.x+vx*t,ty=p.y+vy*t;
      return Math.hypot(tx-owner.x,ty-owner.y)<=radius+(p.r||0)&&clearPath(p.x,p.y,tx,ty);
    });
  }
  function cast(owner,m){
    if(!canCast(owner,m))return false;
    const s=state(owner),spec=specs[m.digiMode],e=target(owner,m),aim=e?Math.atan2(e.y-owner.y,e.x-owner.x):(owner.aim||0);
    const counter=m.digiMode==='uro-thin-ice'&&s.counterUntil>s.clock?s.counterBonus:0;
    const b={owner,world:G.World,runEpoch:G.CombatPulse.epoch,id:m.id,mode:m.digiMode,m:{...m},age:0,aim,x:owner.x,y:owner.y,tx:e?.x??owner.x,ty:e?.y??owner.y,
      duration:spec.duration,bodyDuration:m.digiMode==='uro-screen'?.42:spec.duration,release:spec.release,range:m.range||spec.range,radius:m.radius||spec.radius,arc:m.arc??spec.arc,
      damage:(m.dmg??spec.dmg)*(owner.atk??1)*(1+counter),counterEmpowered:counter>0,type:m.type||'psychic',crit:owner.critChance||0,done:false};
    b.cast=G.CombatPulse.create(owner,m.id,{channel:m.digiMode==='uro-screen'?'reaction':'body'});
    Object.assign(b,{castId:b.cast.castId,channel:b.cast.channel});
    if(counter){s.counterBonus=0;s.counterUntil=0;}
    const native=learned(owner,m.id),cooldown=Math.max(.05,(m.cd||spec.cd)*(owner.cdMul??1));
    native.t=m.t=cooldown;native.castAt=m.castAt=performance.now();s.cooldowns[m.id]=cooldown;
    s.castCounts[b.mode]=(s.castCounts[b.mode]||0)+1;
    s.pose=b.mode==='uro-screen'?{...b,duration:.42}:b;s.ready.delete(m.id);owner.aim=aim;owner.cast?.(m);
    if(b.mode==='uro-screen'){b.budget=4+rank(m);b.flashes=[];b.counterTriggered=false;s.screen=b;}else effects.push(b);
    return true;
  }
  function hitFor(b,e){
    const mult=G.Types.mult(b.type,e.types),crit=Math.random()<b.crit;
    const damage=b.damage*mult*G.Weather.mult(b.type)*(crit?1.5:1)*(G.NarutoSupport?.precisionMultiplier(b.owner,e)||1);
    const special=!!(e.boss||e.elite||e.legend||e.judge),knock=b.mode==='uro-sky'?(special?0:(b.m.skyKnock??8)):28;
    return {target:e,primaryDirectDamage:damage,color:'#bfeaff',dx:Math.cos(b.aim),dy:Math.sin(b.aim),knock,eff:crit?'crit':G.Types.label(mult),onHit:target=>{
      if(!alive(target))return;
      if(b.mode==='uro-collapse')target.applySlow?.(special?.15:(b.m.collapseSlow??.5),special&&b.m.collapseSlow!=null?.45:(b.m.slowDuration??.65));
      if(b.mode==='uro-thin-ice'&&b.m.thinSlow>0)target.applySlow?.(special?.1:b.m.thinSlow,special?.3:(b.m.thinSlowDuration??.45));
    }};
  }
  function release(b){
    b.done=true;
    const circle=b.mode==='uro-collapse',x=circle?b.tx:b.x,y=circle?b.ty:b.y,r=circle?b.radius:b.range;
    const inside=e=>circle||Math.abs(delta(Math.atan2(e.y-y,e.x-x),b.aim))<=b.arc/2+Math.asin(Math.min(1,(e.r||0)/Math.max(1,Math.hypot(e.x-x,e.y-y))));
    const result=G.CombatPulse.apply(b.cast,0,targets(x,y,r).filter(inside).map(e=>hitFor(b,e)));
    if(result)state(b.owner).hits+=result.primaryHits;
    for(const p of props(x,y,r))if(inside(p))G.World.damageProp?.(p,b.damage,'#bfeaff');
  }
  function legal(b){return !terminal()&&b.world===G.World&&b.runEpoch===G.CombatPulse.epoch&&valid(b.owner)&&b.owner.moves?.some(m=>m.id===b.id);}
  function clear(owner){
    if(owner)states.delete(owner);else states.clear();
    for(let i=effects.length-1;i>=0;i--)if(!owner||effects[i].owner===owner)effects.splice(i,1);
  }
  function update(dt){
    if(terminal()){clear();return;}
    if(!playing()||!Number.isFinite(dt)||dt<=0)return;
    for(const [owner,s] of states){
      if(!valid(owner)||s.world!==G.World||s.runEpoch!==G.CombatPulse.epoch){clear(owner);continue;}
      s.clock+=dt;
      if(s.counterUntil<=s.clock){s.counterBonus=0;s.counterUntil=0;}
      if(s.pose?.mode==='uro-screen')s.pose.age+=dt;
      if(s.screen){s.screen.age+=dt;for(const flash of s.screen.flashes)flash.age+=dt;s.screen.flashes=s.screen.flashes.filter(f=>f.age<.22);if(!legal(s.screen)||s.screen.budget<=0||s.screen.age>=s.screen.duration)s.screen=null;}
    }
    for(let i=effects.length-1;i>=0;i--){
      const b=effects[i];if(!legal(b)){effects.splice(i,1);continue;}
      b.age+=dt;
      if(!b.done&&b.age+1e-8>=b.release)release(b);
      if(b.age>=b.duration)effects.splice(i,1);
    }
    for(const s of states.values())if(s.pose&&(!legal(s.pose)||s.pose.age>=s.pose.bodyDuration))s.pose=null;
  }
  function entry(p,w){
    const ax=p.px??p.x,ay=p.py??p.y,dx=p.x-ax,dy=p.y-ay,ox=ax-w.owner.x,oy=ay-w.owner.y,r=w.radius+(p.r||0);
    const c=ox*ox+oy*oy-r*r;if(c<=0)return 0;
    const a=dx*dx+dy*dy;if(a<1e-10)return null;
    const b=2*(ox*dx+oy*dy),disc=b*b-4*a*c;if(disc<0)return null;
    const t=(-b-Math.sqrt(disc))/(2*a);return t>=0&&t<=1?t:null;
  }
  function intercept(){
    if(!playing())return;
    for(const p of [...G.Projectiles.all()]){
      if(p.friendly||p.uroReturned)continue;
      let first=null;
      for(const [owner,s] of states){
        const w=s.screen;if(!w||!legal(w)||w.budget<=0||w.age>=w.duration)continue;
        const t=entry(p,w);if(t!==null&&(!first||t<first.t))first={owner,s,w,t};
      }
      if(!first)continue;
      const {owner,s,w,t}=first,ax=p.px??p.x,ay=p.py??p.y,x=ax+(p.x-ax)*t,y=ay+(p.y-ay)*t;
      G.Projectiles.remove(p);w.budget--;s.intercepted++;w.flashes.push({x,y,age:0});
      if(!w.counterTriggered&&w.m.counterBonus>0){w.counterTriggered=true;s.counterBonus=w.m.counterBonus;s.counterUntil=s.clock+(w.m.counterDuration??3);}
      G.Projectiles.spawn({x,y,vx:-(p.vx||0),vy:-(p.vy||0),r:Math.max(4,p.r||6),dmg:(p.dmg||10)*(owner.atk??1),life:Math.min(3,p.life||2),
        friendly:true,owner,mid:w.id,mtype:p.mtype||'psychic',color:'#bfeaff',vis:G.VFX.forType(p.mtype||'psychic'),pierce:0,hits:new Set(),uroReturned:true});
    }
  }
  function draw(ctx){
    if(G.JujutsuVFX?.enabled)return;
    if(terminal())return;
    ctx.save();ctx.lineWidth=1.5;
    for(const b of effects){
      if(!legal(b))continue;
      const circle=b.mode==='uro-collapse',thin=b.mode==='uro-thin-ice',x=circle?b.tx:b.x,y=circle?b.ty:b.y;
      const pull=Math.min(1,b.age/b.release),after=Math.max(0,b.age-b.release),fade=b.done?Math.max(0,1-after/(b.duration-b.release)):1;
      const r=circle?b.radius:b.range,segments=circle?8:thin?6:3,arc=circle?Math.PI*2:b.arc;
      ctx.save();ctx.translate(x,y);ctx.rotate(circle?0:b.aim);ctx.strokeStyle='#c9f4ff';ctx.fillStyle='#79cfe5';
      // Each trapezoid is a grasped strip of sky; a displaced ridge makes the
      // surface visibly bend before its crack opens at the real hit instant.
      for(let i=0;i<segments;i++){
        const a=-arc/2+arc*i/segments,z=a+arc/segments,mid=(a+z)/2;
        const inner=circle?r*.18:r*.22,edge=r,fold=r*(.56-.11*Math.sin(pull*Math.PI)),split=b.done?Math.min(1,after/.2)*r*.13:0;
        ctx.save();ctx.translate(Math.cos(mid)*split,Math.sin(mid)*split);
        ctx.globalAlpha=(b.done?.13:.08)*fade;ctx.beginPath();ctx.moveTo(Math.cos(a)*inner,Math.sin(a)*inner);
        ctx.lineTo(Math.cos(a)*edge,Math.sin(a)*edge);ctx.lineTo(Math.cos(z)*edge,Math.sin(z)*edge);ctx.lineTo(Math.cos(z)*inner,Math.sin(z)*inner);ctx.closePath();ctx.fill();
        ctx.globalAlpha=(b.done?.8:.22+.24*pull)*fade;ctx.beginPath();ctx.moveTo(Math.cos(a)*edge,Math.sin(a)*edge);ctx.lineTo(Math.cos(mid+.05)*fold,Math.sin(mid+.05)*fold);ctx.lineTo(Math.cos(z)*inner,Math.sin(z)*inner);ctx.stroke();
        ctx.beginPath();ctx.moveTo(Math.cos(a)*edge,Math.sin(a)*edge);ctx.lineTo(Math.cos(z)*edge,Math.sin(z)*edge);ctx.stroke();
        if(pull>.62){ctx.strokeStyle=b.done?'#f4fdff':'#b8e0ff';ctx.beginPath();ctx.moveTo(Math.cos(mid)*r*.35,Math.sin(mid)*r*.35);ctx.lineTo(Math.cos(mid+.045)*r*.58,Math.sin(mid+.045)*r*.58);ctx.lineTo(Math.cos(mid-.03)*r*.72,Math.sin(mid-.03)*r*.72);ctx.lineTo(Math.cos(mid)*r*.95,Math.sin(mid)*r*.95);ctx.stroke();}
        if(b.done){ctx.globalAlpha=.8*fade;const sr=3+5*fade,dr=r*.7+after*54;ctx.beginPath();ctx.moveTo(Math.cos(mid)*dr,Math.sin(mid)*dr);ctx.lineTo(Math.cos(mid)*dr+sr,Math.sin(mid)*dr-sr);ctx.lineTo(Math.cos(mid)*dr+sr*.6,Math.sin(mid)*dr+sr);ctx.closePath();ctx.fill();}
        ctx.restore();
      }
      // The fine, low-opacity outline is the exact fan/circle hit boundary,
      // distinct from the brighter folding ridges inside it.
      ctx.globalAlpha=.15*fade;ctx.beginPath();if(circle)ctx.arc(0,0,r,0,Math.PI*2);else{ctx.moveTo(0,0);ctx.arc(0,0,r,-arc/2,arc/2);ctx.closePath();}ctx.stroke();ctx.restore();
    }
    for(const [owner,s]of states){
      const w=s.screen;if(!w||!legal(w))continue;
      ctx.save();ctx.translate(owner.x,owner.y);ctx.strokeStyle='#b9eaff';ctx.fillStyle='#83d3e9';const r=w.radius;
      // Full circumference protection is shown as bent contiguous sky panes,
      // never a one-sided wall over an omnidirectional collision volume.
      for(let i=0;i<8;i++){
        const a=i*Math.PI/4,z=(i+1)*Math.PI/4,mid=(a+z)/2,fold=r*(.74+.035*Math.sin(w.age*3+i));
        ctx.globalAlpha=.055;ctx.beginPath();ctx.moveTo(Math.cos(a)*r,Math.sin(a)*r);ctx.lineTo(Math.cos(z)*r,Math.sin(z)*r);ctx.lineTo(Math.cos(z)*r*.64,Math.sin(z)*r*.64);ctx.lineTo(Math.cos(mid)*fold,Math.sin(mid)*fold);ctx.closePath();ctx.fill();
        ctx.globalAlpha=.35;ctx.beginPath();ctx.moveTo(Math.cos(a)*r,Math.sin(a)*r);ctx.quadraticCurveTo(Math.cos(mid)*r*1.05,Math.sin(mid)*r*1.05,Math.cos(z)*r,Math.sin(z)*r);ctx.lineTo(Math.cos(mid)*fold,Math.sin(mid)*fold);ctx.stroke();
      }
      ctx.globalAlpha=.1;ctx.beginPath();ctx.arc(0,0,r,0,Math.PI*2);ctx.stroke();ctx.globalAlpha=.8;ctx.fillStyle='#d5f5ff';for(let i=0;i<w.budget;i++)ctx.fillRect(-16+i*5,-44,3,3);ctx.restore();
      for(const f of w.flashes){const n=1-f.age/.22;ctx.globalAlpha=n;ctx.strokeStyle='#f2fcff';ctx.beginPath();ctx.moveTo(f.x-9*n,f.y-4);ctx.lineTo(f.x+2,f.y+6*n);ctx.lineTo(f.x+10*n,f.y-7*n);ctx.stroke();}
    }
    ctx.restore();
  }
  const oldTick=C.tick,oldUpdate=C.updateFields,oldAir=C.drawAirFields,oldClear=C.clearFields,oldResolve=C.resolve;
  C.tick=function(dt,owner,now){
    if((owner?.mon?.dex??owner?.dex)!==DEX)return oldTick.call(this,dt,owner,now);
    if(!playing()||!valid(owner)||owner.frozen||!Number.isFinite(dt)||dt<=0)return;
    const s=state(owner),moves=(owner.moves||[]).filter(m=>supports(m.digiMode));
    for(const m of moves){m.t=Math.max(0,(m.t||0)-dt);s.cooldowns[m.id]=m.t;if(m.t<=1e-8&&!s.ready.has(m.id))s.ready.set(m.id,s.clock);}
    const candidate=moves.filter(m=>canCast(owner,m)).sort((a,b)=>(s.ready.get(a.id)??s.clock)-(s.ready.get(b.id)??s.clock))[0];
    if(candidate)cast(owner,candidate);
  };
  C.updateFields=function(dt){const result=oldUpdate.call(this,dt);update(dt);return result;};
  C.drawAirFields=function(ctx){oldAir.call(this,ctx);draw(ctx);};
  C.clearFields=function(owner){clear(owner);return oldClear.call(this,owner);};
  C.resolve=function(...args){intercept();return oldResolve.apply(this,args);};
  for(const method of ['toUI','quit'])if(typeof G.Game[method]==='function'){
    const previous=G.Game[method];G.Game[method]=function(...args){const result=previous.apply(this,args);if(terminal())clear();return result;};
  }
  function statusFor(owner,m){const s=states.get(owner);return {state:s?.pose?.id===m.id?'casting':m.t>1e-8?'cooldown':s?.pose?'queued':'ready',remaining:m.t||0};}
  G.JjkUro={dex:DEX,supports,canCast,cast,update,draw,clear,intercept,specs,threatened,statusFor,
    poseFor:owner=>{const b=states.get(owner)?.pose;if(!b||!legal(b))return null;const phase=b.mode==='uro-screen'?(b.age<.08?'windup':b.age<.22?'pull':b.age<.3?'shatter':'recovery'):(b.age<b.release*.35?'windup':b.age<b.release?'pull':b.age<b.release+.13?'shatter':'recovery');return {...b,phase,frameName:phase};},
    activeFor:owner=>{const b=states.get(owner)?.pose;return b&&legal(b)?b:null;},stateFor:(owner=G.Game.player)=>{const s=states.get(owner);return !terminal()&&s?.world===G.World&&s?.runEpoch===G.CombatPulse.epoch?s:null;},get effects(){return effects;}};
})();
