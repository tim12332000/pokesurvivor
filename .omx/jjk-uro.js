/* Uro: finite sky screens and spatial fan attacks, owned by the casting actor. */
(() => {
  'use strict';
  if (G.JjkUro) return;
  const DEX=30015, C=G.Combat, states=new Map(), effects=[];
  const specs={
    'uro-sky':{cd:1.25,dmg:20,range:180,arc:1.6,release:.18,duration:.48},
    'uro-thin-ice':{cd:4.8,dmg:72,range:340,arc:2.5,release:.34,duration:1.64},
    'uro-screen':{cd:9,dmg:0,range:600,radius:110,release:0,duration:3.5},
    'uro-collapse':{cd:8,dmg:112,range:600,radius:210,release:.55,duration:2.05},
    'uro-echo':{cd:0,dmg:40,range:0,radius:0,release:.2,duration:1}
  };
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const controlled=a=>G.SelfClones?.isControlled?.(a)??(a===G.Game.player);
  const valid=a=>alive(a)&&controlled(a)&&(a.mon?.dex??a.dex)===DEX;
  const playing=()=>G.Game.state==='playing';
  const terminal=()=>G.Game.state==='ui'||G.Game.state==='over';
  const supports=mode=>Object.hasOwn(specs,mode);
  const learned=(owner,id)=>owner.moves?.find(m=>m.id===id);
  const rank=m=>Math.max(1,Math.min(5,Math.floor(m?.lvl||1)));
  const scales=[1,1.2,1.45,1.75,2.1];
  function fractureProfile(owner,m){
    const i=rank(m)-1,mode=m.digiMode,P=G.Jujutsu.power.uro,count=(base,cap)=>Math.min(cap,G.Quantity.count(owner,base));
    if(mode==='uro-sky')return {shape:'fan',range:P.palmRanges[i],arc:P.palmArcs[i],count:1,interval:0};
    if(mode==='uro-thin-ice'){const n=count(P.waveBases[i],P.waveCap);return {shape:'fan',range:P.thinRanges[i],arc:P.thinArcs[i],count:n,interval:Math.max(.09,1/Math.max(1,n-1))};}
    if(mode==='uro-collapse'){const n=count(P.waveBases[i],P.waveCap);return {shape:'circle',range:P.collapseRange,radius:P.collapseRadii[i],count:n,interval:Math.max(.10,1.2/Math.max(1,n-1))};}
    if(mode==='uro-screen'){const n=count(P.waveBases[i],P.waveCap);return {shape:'circle',range:P.counterRange,radius:P.screenRadii[i],count:n,interval:Math.max(.09,1/Math.max(1,n-1)),counterRadius:P.counterRadii[i],budget:count(P.screenBudgets[i],P.screenCap),duration:P.screenDurations[i]};}
    return {count:count(P.echoBases[i],P.echoCap),interval:.18};
  }
  const delta=(a,b)=>Math.atan2(Math.sin(a-b),Math.cos(a-b));
  const clearPath=(x,y,tx,ty,target=null)=>G.World.projectilePathClear?.(x,y,tx,ty,target,{radius:1,spacing:5,includeStart:false})??true;
  function state(owner){
    let s=states.get(owner);
    if(s&&(s.world!==G.World||s.runEpoch!==G.CombatPulse.epoch)){clear(owner);s=null;}
    if(!s){s={owner,world:G.World,runEpoch:G.CombatPulse.epoch,cooldowns:{},ready:new Map(),clock:0,pose:null,screen:null,castCounts:{},hits:0,intercepted:0,counterChains:0,echoChains:0};states.set(owner,s);}
    return s;
  }
  function targets(x,y,r){
    return [...new Set(G.EnemyMgr.queryCircle(x,y,r+60))].filter(e=>alive(e)&&!e.friendly&&Math.hypot(e.x-x,e.y-y)<=r+(e.r||0)&&clearPath(x,y,e.x,e.y));
  }
  function props(x,y,r){
    return [...new Set(G.World.propsInCircle?.(x,y,r)||[])].filter(p=>!p.dead&&p.destructible!==false&&p.hp>0&&Math.hypot(p.x-x,p.y-y)<=r+(p.r||0)&&clearPath(x,y,p.x,p.y,p));
  }
  function target(owner,m,choose=true){
    const r=fractureProfile(owner,m).range;
    const enemies=targets(owner.x,owner.y,r),candidates=enemies.length||m.digiMode==='uro-screen'?enemies:props(owner.x,owner.y,r);
    if(!choose)return candidates[0];
    if(m.digiMode==='uro-collapse'&&enemies.length){
      const radius=fractureProfile(owner,m).radius;
      const counts=new Map(enemies.map(e=>[e,enemies.filter(other=>
        Math.hypot(other.x-e.x,other.y-e.y)<=radius+(other.r||0)&&clearPath(e.x,e.y,other.x,other.y)).length]));
      return enemies.sort((a,b)=>counts.get(b)-counts.get(a)||
        Math.hypot(b.x-owner.x,b.y-owner.y)-Math.hypot(a.x-owner.x,a.y-owner.y))[0];
    }
    return candidates.sort((a,b)=>Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y))[0];
  }
  function canCast(owner,m){
    if(!playing()||!valid(owner)||owner.frozen||!supports(m?.digiMode)||m.digiMode==='uro-echo'||!learned(owner,m.id))return false;
    if((learned(owner,m.id).t||0)>1e-8)return false;
    const s=state(owner);
    if(m.digiMode==='uro-screen')return !s.screen&&threatened(owner,m);
    return !s.pose&&!!target(owner,m,false);
  }
  function threatened(owner,m){
    const radius=fractureProfile(owner,m).radius,horizon=m.threatHorizon??.8;
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
    const s=state(owner),spec=specs[m.digiMode],profile=fractureProfile(owner,m),e=target(owner,m),aim=e?Math.atan2(e.y-owner.y,e.x-owner.x):(owner.aim||0);
    const duration=m.digiMode==='uro-screen'?profile.duration:spec.release+(profile.count-1)*profile.interval+.30;
    const b={owner,world:G.World,runEpoch:G.CombatPulse.epoch,id:m.id,mode:m.digiMode,m:{...m},age:0,aim,x:owner.x,y:owner.y,tx:e?.x??owner.x,ty:e?.y??owner.y,
      state:s,shape:profile.shape,duration,bodyDuration:m.digiMode==='uro-screen'?.42:m.digiMode==='uro-collapse'?.85:duration,release:spec.release,
      range:profile.range,radius:profile.radius,arc:profile.arc,currentRange:profile.range,currentArc:profile.arc,currentRadius:profile.radius,
      sourceX:owner.x,sourceY:owner.y,pulseCount:profile.count,pulseIndex:-1,nextPulse:0,pulseAge:0,interval:profile.interval,contactMarks:[],
      damage:(m.dmg??spec.dmg)*(owner.atk??1),type:m.type||'psychic',crit:owner.critChance||0,done:false};
    b.cast=G.CombatPulse.create(owner,m.id,{channel:m.digiMode==='uro-screen'?'reaction':'body'});
    Object.assign(b,{castId:b.cast.castId,channel:b.cast.channel});
    const native=learned(owner,m.id),cooldown=Math.max(.05,(m.cd||spec.cd)*(owner.cdMul??1));
    native.t=m.t=cooldown;native.castAt=m.castAt=performance.now();s.cooldowns[m.id]=cooldown;
    s.castCounts[b.mode]=(s.castCounts[b.mode]||0)+1;
    // A defensive reaction must not replace an attack already being prepared.
    // Its pane and intercept channel can operate while the body finishes that hit.
    if(b.mode!=='uro-screen'||!s.pose){
      s.pose=b;owner.aim=aim;
    }
    s.ready.delete(m.id);owner.cast?.(m);
    if(b.mode==='uro-screen'){b.budget=b.initialBudget=profile.budget;b.flashes=[];b.counterTriggered=false;s.screen=b;}else effects.push(b);
    return true;
  }
  function hitFor(b,e,multiplier=1,control=false){
    const mult=G.Types.mult(b.type,e.types),crit=Math.random()<b.crit;
    const damage=b.damage*multiplier*mult*G.Weather.mult(b.type)*(crit?1.5:1)*(G.NarutoSupport?.precisionMultiplier(b.owner,e)||1);
    const special=!!(e.boss||e.elite||e.legend||e.judge),knock=b.mode==='uro-sky'?(special?0:(b.m.skyKnock??30)):
      control&&(b.mode==='uro-thin-ice'||b.mode==='uro-collapse')&&!special?28:0;
    return {target:e,primaryDirectDamage:damage,color:'#bfeaff',dx:Math.cos(b.aim),dy:Math.sin(b.aim),knock,eff:crit?'crit':G.Types.label(mult),onHit:target=>{
      // Shared pulses re-check cast legality between victims. Invalidate this
      // cast if a damage callback removed its field/skill before the next hit.
      if(!active(b)){b.cast.runEpoch=-1;return;}
      if(!alive(target)||!control)return;
      if(b.mode==='uro-collapse')target.applySlow?.(special?.15:(b.m.collapseSlow??.5),special&&b.m.collapseSlow!=null?.45:(b.m.slowDuration??.65));
      if(b.mode==='uro-thin-ice')target.applySlow?.(special?.1:(b.m.thinSlow??.25),special?.3:(b.m.thinSlowDuration??.45));
    }};
  }
  function independent(s,m,options){
    const b={owner:s.owner,state:s,world:G.World,runEpoch:G.CombatPulse.epoch,id:m.id,m:{...m},type:m.type||'psychic',crit:s.owner.critChance||0,
      age:0,nextPulse:0,pulseIndex:-1,pulseAge:0,contactMarks:[],done:false,...options};
    b.cast=G.CombatPulse.create(s.owner,m.id,{channel:b.mode==='uro-counter'?'reaction':'echo'});
    Object.assign(b,{castId:b.cast.castId,channel:b.cast.channel,currentRange:b.range,currentArc:b.arc,currentRadius:b.radius});
    b.duration=b.release+(b.pulseCount-1)*b.interval+.30;effects.push(b);return b;
  }
  function echo(b){
    const m=learned(b.owner,'jjk-uro-echo');if(!m||!legal(b))return;
    const p=fractureProfile(b.owner,m);
    independent(b.state,m,{mode:'uro-echo',shape:b.shape,x:b.x,y:b.y,tx:b.tx,ty:b.ty,sourceX:b.sourceX,sourceY:b.sourceY,
      aim:b.aim,range:b.range,arc:b.arc,radius:b.radius,pulseCount:p.count,interval:p.interval,release:.20,
      damage:(m.dmg??40*scales[rank(m)-1])*(b.owner.atk??1)});
    b.state.echoChains++;
  }
  function counter(s,w,source){
    if(!legal(w))return;const p=fractureProfile(s.owner,w.m),thin=learned(s.owner,'jjk-uro-thin-ice');
    const candidates=targets(s.owner.x,s.owner.y,p.range),chosen=candidates.includes(source)&&G.EnemyMgr.all().includes(source)?source:
      candidates.sort((a,b)=>Math.hypot(a.x-s.owner.x,a.y-s.owner.y)-Math.hypot(b.x-s.owner.x,b.y-s.owner.y))[0];
    independent(s,w.m,{mode:'uro-counter',shape:'circle',x:chosen?.x??s.owner.x,y:chosen?.y??s.owner.y,tx:chosen?.x??s.owner.x,ty:chosen?.y??s.owner.y,
      sourceX:s.owner.x,sourceY:s.owner.y,aim:chosen?Math.atan2(chosen.y-s.owner.y,chosen.x-s.owner.x):0,hasTarget:!!chosen,range:p.range,radius:p.counterRadius,pulseCount:p.count,interval:p.interval,release:.20,
      counterTarget:alive(source)&&G.EnemyMgr.all().includes(source)?source:null,
      damage:(thin?.dmg!=null?thin.dmg*.55:40*scales[rank(w.m)-1])*(s.owner.atk??1)});
    s.counterChains++;
  }
  function release(b,index){
    if(!active(b))return;
    const final=index===b.pulseCount-1,body=b.mode==='uro-sky'||b.mode==='uro-thin-ice';
    if(body){b.x=b.owner.x;b.y=b.owner.y;b.tx=b.x;b.ty=b.y;}
    if(b.mode==='uro-counter'){
      const candidates=targets(b.owner.x,b.owner.y,b.range),source=b.counterTarget;
      const chosen=candidates.includes(source)&&G.EnemyMgr.all().includes(source)?source:candidates.sort((a,c)=>Math.hypot(a.x-b.owner.x,a.y-b.owner.y)-Math.hypot(c.x-b.owner.x,c.y-b.owner.y))[0];
      b.hasTarget=!!chosen;if(!chosen)return;
      b.x=b.tx=chosen.x;b.y=b.ty=chosen.y;b.aim=Math.atan2(chosen.y-b.owner.y,chosen.x-b.owner.x);
    }
    b.sourceX=b.mode==='uro-echo'?b.sourceX:b.owner.x;b.sourceY=b.mode==='uro-echo'?b.sourceY:b.owner.y;
    const circle=b.shape==='circle',x=circle?b.tx:b.x,y=circle?b.ty:b.y,r=circle?b.radius:b.range;
    const inside=e=>circle||Math.abs(delta(Math.atan2(e.y-y,e.x-x),b.aim))<=b.arc/2+Math.asin(Math.min(1,(e.r||0)/Math.max(1,Math.hypot(e.x-x,e.y-y))));
    const multiplier=b.mode==='uro-thin-ice'?(index===0?1.2:final?1:.55):b.mode==='uro-collapse'?(index===0?1.3:final?1.1:.6):1;
    const result=G.CombatPulse.apply(b.cast,index,targets(x,y,r).filter(inside).map(e=>hitFor(b,e,multiplier,(index===0||final)&&(body||b.mode==='uro-collapse'))));
    if(!active(b))return;
    if(result)b.state.hits+=result.primaryHits;
    b.contactMarks.push({shape:b.shape,x,y,tx:x,ty:y,sourceX:b.sourceX,sourceY:b.sourceY,aim:b.aim,range:b.range,arc:b.arc,radius:b.radius,
      age:0,born:b.age,pulseIndex:index,pulseCount:b.pulseCount,finisher:final});
    for(const p of props(x,y,r)){if(!active(b))return;if(inside(p))G.World.damageProp?.(p,b.damage*multiplier,'#bfeaff');}
    if(final&&result?.primaryHits>0&&active(b)&&['uro-sky','uro-thin-ice','uro-collapse'].includes(b.mode))echo(b);
    if(active(b)&&b.owner===G.Game.player)G.Audio?.sfx?.('shot',{kind:'fracture',type:b.type,finisher:final});
  }
  function legal(b){return !terminal()&&b.world===G.World&&b.runEpoch===G.CombatPulse.epoch&&valid(b.owner)&&states.get(b.owner)===b.state&&
    b.owner.moves?.some(m=>m.id===b.id)&&(effects.includes(b)||b.state.screen===b);}
  const active=b=>playing()&&legal(b)&&!b.owner.frozen&&G.CombatPulse.legal(b.cast);
  function clear(owner){
    if(owner)states.delete(owner);else states.clear();
    for(let i=effects.length-1;i>=0;i--)if(!owner||effects[i].owner===owner)effects.splice(i,1);
  }
  function update(dt){
    if(terminal()){clear();return;}
    if(!playing()||!Number.isFinite(dt)||dt<=0)return;
    for(const [owner,s] of states){
      if(!valid(owner)||s.world!==G.World||s.runEpoch!==G.CombatPulse.epoch){clear(owner);continue;}
      if(owner.frozen)continue;s.clock+=dt;
      if(s.screen){s.screen.age+=dt;for(const flash of s.screen.flashes)flash.age+=dt;s.screen.flashes=s.screen.flashes.filter(f=>f.age<.22);if(!legal(s.screen)||s.screen.budget<=0||s.screen.age>=s.screen.duration)s.screen=null;}
    }
    for(const b of [...effects]){
      if(!legal(b)){const i=effects.indexOf(b);if(i>=0)effects.splice(i,1);continue;}
      if(b.owner.frozen)continue;
      if(!b.done&&(b.mode==='uro-sky'||b.mode==='uro-thin-ice')){b.x=b.owner.x;b.y=b.owner.y;}
      b.age+=dt;
      while(b.nextPulse<b.pulseCount&&b.age+1e-8>=b.release+b.nextPulse*b.interval&&active(b)){
        const index=b.nextPulse++;b.pulseIndex=index;release(b,index);
        if(!active(b))break;b.done=b.nextPulse>=b.pulseCount;
      }
      if(!legal(b)){const i=effects.indexOf(b);if(i>=0)effects.splice(i,1);continue;}
      b.pulseAge=b.pulseIndex<0?0:Math.max(0,b.age-(b.release+b.pulseIndex*b.interval));
      for(const mark of b.contactMarks)mark.age=b.age-mark.born;
      b.contactMarks=b.contactMarks.filter(mark=>mark.age<.40);
      if(b.age>=b.duration){const i=effects.indexOf(b);if(i>=0)effects.splice(i,1);}
    }
    for(const [owner,s] of states)if(!valid(owner)||s.world!==G.World||s.runEpoch!==G.CombatPulse.epoch)clear(owner);
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
        const w=s.screen;if(!w||owner.frozen||!legal(w)||w.budget<=0||w.age>=w.duration)continue;
        const t=entry(p,w);if(t!==null&&(!first||t<first.t))first={owner,s,w,t};
      }
      if(!first)continue;
      const {owner,s,w,t}=first,ax=p.px??p.x,ay=p.py??p.y,x=ax+(p.x-ax)*t,y=ay+(p.y-ay)*t;
      G.Projectiles.remove(p);w.budget--;s.intercepted++;w.flashes.push({x,y,age:0,incoming:{x:p.vx||0,y:p.vy||0},outgoing:{x:-(p.vx||0),y:-(p.vy||0)}});
      if(!w.counterTriggered){
        w.counterTriggered=true;
        counter(s,w,p.sourceEnemy);
      }
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
      const circle=b.shape==='circle',thin=b.mode==='uro-thin-ice',x=circle?b.tx:b.x,y=circle?b.ty:b.y;
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
    const reaction=moves.find(m=>m.digiMode==='uro-screen'&&canCast(owner,m));
    if(reaction)cast(owner,reaction);
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
  function statusFor(owner,m){
    const s=states.get(owner);
    if(m.digiMode==='uro-screen'){
      if(s?.screen&&legal(s.screen))return {state:'active',remaining:Math.max(0,s.screen.duration-s.screen.age)};
      if(m.t>1e-8)return {state:'cooldown',remaining:m.t};
      return threatened(owner,m)?{state:'ready',remaining:0}:{state:'waiting',reason:'projectile',remaining:0};
    }
    if(m.digiMode==='uro-echo')return {state:'passive',remaining:0};
    return {state:s?.pose?.id===m.id?'casting':m.t>1e-8?'cooldown':s?.pose?'queued':'ready',remaining:m.t||0};
  }
  G.JjkUro={dex:DEX,supports,canCast,cast,update,draw,clear,intercept,specs,threatened,statusFor,fractureProfile,
    poseFor:owner=>{const b=states.get(owner)?.pose;if(!b||!legal(b))return null;
      const until=b.release+b.nextPulse*b.interval-b.age,phase=b.mode==='uro-screen'?(b.age<.08?'windup':b.age<.22?'pull':b.age<.3?'shatter':'recovery'):
        b.pulseIndex>=0&&b.pulseAge<.13?'shatter':b.done?'recovery':until<.14?'pull':'windup';return {...b,phase,frameName:phase};},
    activeFor:owner=>{const b=states.get(owner)?.pose;return b&&legal(b)?b:null;},stateFor:(owner=G.Game.player)=>{const s=states.get(owner);return !terminal()&&s?.world===G.World&&s?.runEpoch===G.CombatPulse.epoch?s:null;},get effects(){return effects;}};
})();
