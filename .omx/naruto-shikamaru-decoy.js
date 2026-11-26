/* Stationary shadow bait: an AI aim point, never a solid body or an attacker. */
(() => {
  'use strict';
  if(G.NarutoShikamaruDecoy)return;
  const S=G.NarutoShikamaru,C=G.Combat,ID='naruto-shikamaru-decoy',MODE='shikamaru-decoy';
  const states=new Map(),EPS=1e-8;
  let serial=0;
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const valid=a=>alive(a)&&(a===G.Game.player||G.SelfClones?.isActor?.(a))&&(a.mon?.dex??a.dex)===30017;
  const learned=a=>a?.moves?.find(m=>m.id===ID);
  const supports=m=>(typeof m==='string'?m:m?.digiMode)===MODE;
  const terminal=()=>G.Game.state==='ui'||G.Game.state==='over';
  const epoch=()=>G.CombatPulse?.epoch;
  function profile(a,m){
    const L=Math.max(1,Math.min(5,Math.floor(m?.lvl||1))),Q=Math.max(0,Math.floor(G.Quantity?.bonus(a)??a.quantityPicks??a.quantityBonus??0));
    return {kind:'decoy',L,Q,count:Math.min(6,1+Math.floor((L-1)/2)+Q),life:3+.35*(L-1),range:280+20*(L-1)+12*Math.min(12,Q),cd:(m?.cd??8)*(a.cdMul??1),damage:0};
  }
  const stateLegal=s=>states.get(s.owner)===s&&valid(s.owner)&&!!learned(s.owner)&&s.world===G.World&&s.epoch===epoch()&&!terminal();
  function clear(owner){
    for(const [a,s]of states)if(!owner||a===owner){for(const d of s.decoys)d.dead=true;states.delete(a);}
  }
  function state(a){
    let s=states.get(a);if(s&&!stateLegal(s)){clear(a);s=null;}
    if(!s){s={owner:a,world:G.World,epoch:epoch(),clock:0,cooldown:0,decoys:[],casts:0,spawned:0,redirects:0};states.set(a,s);}return s;
  }
  const decoyLegal=(s,d)=>stateLegal(s)&&!d.dead&&d.hp>0&&d.age<d.life;
  function decoys(){const out=[];for(const s of states.values())for(const d of s.decoys)if(decoyLegal(s,d))out.push(d);return out;}
  function isDecoy(d){const s=states.get(d?.owner);return !!s&&s.decoys.includes(d)&&decoyLegal(s,d);}
  const path=(ax,ay,bx,by)=>G.ShikamaruReferenceGeometry?.lineClear?G.ShikamaruReferenceGeometry.lineClear(ax,ay,bx,by,S.clearPath):S.clearPath(ax,ay,bx,by);
  function threats(a,p){
    return G.EnemyMgr.queryCircle(a.x,a.y,p.range).filter(e=>alive(e)&&!e.friendly&&!e.remote&&e.behavior!=='thief'&&Math.hypot(e.x-a.x,e.y-a.y)<=p.range&&path(a.x,a.y,e.x,e.y));
  }
  function hasThreat(a,p){
    for(const e of G.EnemyMgr.queryCircle(a.x,a.y,p.range))if(alive(e)&&!e.friendly&&!e.remote&&e.behavior!=='thief'&&Math.hypot(e.x-a.x,e.y-a.y)<=p.range&&path(a.x,a.y,e.x,e.y))return true;
    return false;
  }
  function canCast(a,m){
    return G.Game.state==='playing'&&valid(a)&&!a.frozen&&supports(m)&&!!learned(a)&&state(a).cooldown<=EPS&&hasThreat(a,profile(a,m));
  }
  const silhouetteCache=new Map();
  const dpx=v=>Math.round(v*.5)*2;
  function silhouette(owner,dir){
    const height=64*(owner.anim?.scale||1),key=height+':'+dir;
    if(silhouetteCache.has(key))return silhouetteCache.get(key);
    const w=Math.ceil(height*2),h=Math.ceil(height*1.5);
    const mask=document.createElement('canvas');mask.width=w;mask.height=h;
    const mctx=mask.getContext('2d'),x=w/2,y=h-8;
    if(!G.ShikamaruArt?.draw(mctx,{}, {x,y,height,state:'idle',time:0,dir,pose:false}))return null;
    const rim=document.createElement('canvas');rim.width=w;rim.height=h;
    const rctx=rim.getContext('2d');rctx.drawImage(mask,0,0);
    rctx.globalCompositeOperation='source-in';rctx.fillStyle='#2a1f3d';rctx.fillRect(0,0,w,h);
    mctx.globalCompositeOperation='source-in';mctx.fillStyle='#06050a';mctx.fillRect(0,0,w,h);
    // Bake subtle 1px dark-violet chakra rim + deep ink core once per cached direction.
    const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;
    const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;
    ctx.globalAlpha=.72;
    for(const [ox,oy]of [[-1,0],[1,0],[0,-1]])ctx.drawImage(rim,ox,oy);
    ctx.globalAlpha=1;ctx.drawImage(mask,0,0);
    const entry={canvas,x,y,height};
    silhouetteCache.set(key,entry);if(silhouetteCache.size>24)silhouetteCache.delete(silhouetteCache.keys().next().value);
    return entry;
  }
  function cast(a,m){
    if(!canCast(a,m))return false;
    const s=state(a),p=profile(a,m),dir=a.anim?.dir||0,aim=a.aim||0,side=aim+Math.PI/2,image=silhouette(a,dir);
    for(let i=0;i<p.count;i++){
      const offset=i===0?0:Math.ceil(i/2)*(i%2?1:-1)*42,x=a.x+Math.cos(side)*offset,y=a.y+Math.sin(side)*offset;
      if(i>0&&(!path(a.x,a.y,x,y)||(G.World.isFree&&!G.World.isFree(x,y,a.r||12))))continue;
      const d={id:'shikamaru-decoy-'+(++serial),owner:a,isDecoy:true,shikamaruDecoy:true,intangible:true,
        dex:30017,mon:a.mon,level:a.level,r:a.r||12,bodyH:a.bodyH||64,x,y,hp:1,maxHp:1,dead:false,
        _vx:0,_vy:0,svx:0,svy:0,atk:0,spd:0,aim,dir,age:0,life:p.life,lureRange:p.range,image,
        world:G.World,epoch:epoch(),seed:serial,enemies:new Set(),hurt:()=>false,onDealt:()=>{},heal:()=>{}};
      s.decoys.push(d);s.spawned++;
    }
    s.cooldown=p.cd;m.t=p.cd;s.casts++;return true;
  }
  function targetForEnemies(enemy,fallback){
    if(!states.size||!alive(enemy)||enemy.friendly||enemy.remote||enemy.behavior==='thief')return fallback;
    let hasAny=false;for(const s of states.values())if(s.decoys.length){hasAny=true;break;}
    if(!hasAny)return fallback;
    const base=fallback?Math.hypot(fallback.x-enemy.x,fallback.y-enemy.y):Infinity;
    const otherDecoy=G.LF2Julian?.isDecoy?.(fallback)||isDecoy(fallback);
    let best=null,distance=otherDecoy?base:base*1.5,dist2=distance*distance;
    for(const s of states.values()){
      if(!stateLegal(s))continue;
      for(const d of s.decoys){
        if(d.dead||d.hp<=0||d.age>=d.life)continue;
        const dx=d.x-enemy.x,dy=d.y-enemy.y,r2=dx*dx+dy*dy,lure2=d.lureRange*d.lureRange;
        if(r2>lure2||r2>dist2)continue;
        if(!path(enemy.x,enemy.y,d.x,d.y))continue;
        best=d;dist2=r2;distance=Math.sqrt(r2);
      }
    }
    if(!best)return fallback;
    if(!best.enemies.has(enemy)){best.enemies.add(enemy);const s=states.get(best.owner);if(s)s.redirects++;}
    return best;
  }
  function update(dt){
    for(const [a,s]of states)if(!stateLegal(s))clear(a);
    if(G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    for(const s of states.values()){
      s.clock+=dt;s.cooldown=Math.max(0,s.cooldown-dt);const m=learned(s.owner);if(m)m.t=s.cooldown;
      for(const d of s.decoys){d.age+=dt;if(d.age>=d.life)d.dead=true;}
      s.decoys=s.decoys.filter(d=>!d.dead);
    }
  }
  const clamp=v=>Math.max(0,Math.min(1,v));
  const settle=v=>{const u=clamp(v);return u*u*(3-2*u);};
  function visualFor(d){
    if(!d)return null;
    const formTime=Math.min(.34,d.life*.2),collapseTime=Math.min(.48,d.life*.25),remaining=d.life-d.age;
    const phase=d.age<formTime?'form':remaining<collapseTime?'collapse':'hold';
    const progress=clamp(phase==='form'?d.age/formTime:phase==='collapse'?1-remaining/collapseTime:1);
    const height=phase==='form'?settle(progress):phase==='collapse'?1-settle(progress):1;
    return {phase,progress,height,spread:1+.45*(1-height),opacity:clamp(d.age/.07)*clamp(remaining/.13)};
  }
  function ground(ctx){
    for(const d of decoys()){
      const v=visualFor(d),r=(d.r+6)*v.spread,phase=d.age*2.6+d.seed;
      ctx.save();
      // Outer dark-violet ink bleed + subtle lure pulse ring when enemies are redirected
      ctx.globalAlpha=(.22+.1*v.height)*v.opacity;ctx.fillStyle='#191229';ctx.beginPath();
      for(let i=0;i<=14;i++){
        const a=i*Math.PI/7,lobe=1.16+.1*Math.sin(i*2.3+d.seed)+.05*Math.sin(phase+i*1.5);
        const x=d.x+Math.cos(a)*r*lobe,y=d.y+1.5+Math.sin(a)*6.8*lobe;
        i?ctx.lineTo(x,y):ctx.moveTo(x,y);
      }ctx.closePath();ctx.fill();
      if(d.enemies.size){
        const pulse=(d.age*1.4)%1;
        ctx.globalAlpha=(1-pulse)*.28*v.opacity;ctx.strokeStyle='#4e3a6e';ctx.lineWidth=1.4;
        ctx.beginPath();ctx.ellipse(d.x,d.y+1,r*(1+.55*pulse),6*(1+.45*pulse),0,0,Math.PI*2);ctx.stroke();
      }
      // Solid deep-black living shadow pool anchored under the bait's feet
      ctx.globalAlpha=(.82+.12*v.height)*v.opacity;ctx.fillStyle='#050408';ctx.beginPath();
      for(let i=0;i<=14;i++){
        const a=i*Math.PI/7,lobe=1+.11*Math.sin(i*2.1+d.seed)+.05*Math.sin(phase+i*1.7);
        const x=d.x+Math.cos(a)*r*lobe,y=d.y+1+Math.sin(a)*5.8*lobe;
        i?ctx.lineTo(x,y):ctx.moveTo(x,y);
      }ctx.closePath();ctx.fill();
      ctx.restore();
    }
  }
  function silhouettes(ctx){
    const detail=(G.Settings?.fx??1)>0;
    for(const d of decoys()){
      const v=visualFor(d);ctx.save();ctx.globalAlpha=.86*v.opacity;
      if(d.image){
        const image=d.image;
        ctx.imageSmoothingEnabled=false;
        if(v.phase==='hold'){
          const drift=Math.sin(d.age*2.4+d.seed)*.6;
          ctx.drawImage(image.canvas,Math.round(d.x-image.x+drift),Math.round(d.y-image.y));
        }else{
          const step=Math.max(2,Math.ceil(image.height/(detail?24:12)));
          // Ink accumulates from the feet in tight seamless bands; collapse melts back into the pool.
          for(let sy=Math.max(0,Math.floor(image.y-image.height-3));sy<image.y;sy+=step){
            const sh=Math.min(step,image.y-sy),distance=image.y-sy-sh,t=clamp(distance/image.height);
            const growth=v.phase==='form'?settle((v.progress-t*.26)/.74):1-settle(v.progress*(1+.24*t));
            if(growth<=0)continue;
            const spread=1+(1-growth)*.42,w=image.canvas.width*spread;
            const drift=Math.sin(d.age*2.4+d.seed+t*5)*Math.sin(t*Math.PI)*(.4+2*(1-growth));
            ctx.drawImage(image.canvas,0,sy,image.canvas.width,sh,d.x-image.x*spread+drift,d.y-(distance+sh)*growth-.4,w,Math.max(.6,sh*growth+.6));
          }
        }
      }
      else{
        const h=d.bodyH*v.height;ctx.translate(d.x,d.y);ctx.scale(v.spread,1);ctx.fillStyle='#06050a';ctx.beginPath();ctx.moveTo(-7,-h*.84);ctx.lineTo(-9,-h);ctx.lineTo(2,-h*.94);ctx.lineTo(8,-h*.81);ctx.lineTo(7,-h*.65);ctx.lineTo(14,-h*.5);ctx.lineTo(10,-h*.32);ctx.lineTo(7,-h*.3);ctx.lineTo(10,0);ctx.lineTo(2,0);ctx.lineTo(0,-h*.26);ctx.lineTo(-3,0);ctx.lineTo(-11,0);ctx.lineTo(-8,-h*.34);ctx.lineTo(-14,-h*.48);ctx.lineTo(-8,-h*.65);ctx.closePath();ctx.fill();
      }
      // Rising pixelated ink wisps around the standing shadow decoy
      if(detail&&v.height>.25){
        const h=d.bodyH*v.height;
        for(let i=0;i<4;i++){
          const cycle=(d.age*.9+i*.25+d.seed*.17)%1;
          const side=Math.sin(i*2.3+d.seed+cycle*3)*(10+4*(i%2));
          const wx=dpx(d.x+side),wy=dpx(d.y-4-cycle*h*.82);
          ctx.globalAlpha=(1-cycle)*.58*v.opacity;
          ctx.fillStyle=i%2?'#241a38':'#07050c';
          ctx.fillRect(wx,wy,2,cycle<.5?4:2);
        }
      }
      ctx.restore();
    }
  }
  function statusFor(a,m){const s=states.get(a),remaining=s?.cooldown||0,n=s?.decoys.filter(d=>decoyLegal(s,d)).length||0;return {label:n?'留影 '+n:remaining>0?'留影 '+Math.ceil(remaining)+'s':'留影待命',fraction:1-Math.min(1,remaining/profile(a,m).cd)};}
  const oldTick=C.tick,oldUpdate=C.updateFields,oldClear=C.clearFields,oldGround=C.drawGroundFields;
  C.tick=function(dt,a,...args){const result=oldTick.call(this,dt,a,...args);if(G.Game.state==='playing'&&valid(a)&&Number.isFinite(dt)&&dt>0){const m=learned(a);if(m)cast(a,m);}return result;};
  C.updateFields=function(dt){const result=oldUpdate.call(this,dt);update(dt);return result;};
  C.clearFields=function(a){clear(a);return oldClear.call(this,a);};
  // Living bodies render after the shadow bait, including during exact overlap.
  C.drawGroundFields=function(ctx){oldGround.call(this,ctx);ground(ctx);silhouettes(ctx);};
  const oldSUpdate=S.update,oldSClear=S.clear,oldSupports=S.supports,oldCanCast=S.canCast,oldCast=S.cast,oldProfile=S.profile,oldStatus=S.statusFor;
  S.update=function(dt){oldSUpdate(dt);update(dt);};S.clear=function(a){clear(a);oldSClear(a);};
  S.supports=m=>supports(m)||oldSupports(m);S.canCast=(a,m)=>supports(m)?canCast(a,m):oldCanCast(a,m);
  S.cast=(a,m)=>supports(m)?cast(a,m):oldCast(a,m);S.profile=(a,m)=>supports(m)?profile(a,m):oldProfile(a,m);
  S.statusFor=(a,m)=>supports(m)?statusFor(a,m):oldStatus(a,m);
  G.NarutoShikamaruDecoy={supports,profile,canCast,cast,update,clear,decoys,isDecoy,targetForEnemies,statusFor,visualFor,
    stateFor:(a=G.Game.player)=>states.get(a)||null,stats:(a=G.Game.player)=>{const s=states.get(a);return s?{casts:s.casts,spawned:s.spawned,redirects:s.redirects}:null;}};
})();
