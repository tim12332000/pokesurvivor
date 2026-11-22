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
  const path=(ax,ay,bx,by)=>S.clearPath(ax,ay,bx,by);
  function threats(a,p){
    return G.EnemyMgr.queryCircle(a.x,a.y,p.range).filter(e=>alive(e)&&!e.friendly&&!e.remote&&e.behavior!=='thief'&&Math.hypot(e.x-a.x,e.y-a.y)<=p.range&&path(a.x,a.y,e.x,e.y));
  }
  function canCast(a,m){
    return G.Game.state==='playing'&&valid(a)&&!a.frozen&&supports(m)&&!!learned(a)&&state(a).cooldown<=EPS&&threats(a,profile(a,m)).length>0;
  }
  function silhouette(owner,dir){
    const height=64*(owner.anim?.scale||1),canvas=document.createElement('canvas');canvas.width=Math.ceil(height*2);canvas.height=Math.ceil(height*1.5);
    const ctx=canvas.getContext('2d'),x=canvas.width/2,y=canvas.height-8;
    if(!G.ShikamaruArt?.draw(ctx,{}, {x,y,height,state:'idle',time:0,dir,pose:false}))return null;
    ctx.globalCompositeOperation='source-in';ctx.fillStyle='#08070b';ctx.fillRect(0,0,canvas.width,canvas.height);
    return {canvas,x,y};
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
        world:G.World,epoch:epoch(),enemies:new Set(),hurt:()=>false,onDealt:()=>{},heal:()=>{}};
      s.decoys.push(d);s.spawned++;
    }
    s.cooldown=p.cd;m.t=p.cd;s.casts++;return true;
  }
  function targetForEnemies(enemy,fallback){
    if(!alive(enemy)||enemy.friendly||enemy.remote||enemy.behavior==='thief')return fallback;
    const base=fallback?Math.hypot(fallback.x-enemy.x,fallback.y-enemy.y):Infinity;
    const otherDecoy=G.LF2Julian?.isDecoy?.(fallback)||isDecoy(fallback);
    let best=null,distance=otherDecoy?base:base*1.5;
    for(const d of decoys()){
      const range=Math.hypot(d.x-enemy.x,d.y-enemy.y);
      if(range>d.lureRange||range>distance||!path(enemy.x,enemy.y,d.x,d.y))continue;
      best=d;distance=range;
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
  function ground(ctx){
    for(const d of decoys()){
      const fade=Math.min(1,d.age/.12,(d.life-d.age)/.4);
      ctx.save();ctx.globalAlpha=.7*fade;ctx.fillStyle='#08070b';ctx.beginPath();ctx.ellipse(d.x,d.y+1,d.r+4,5,0,0,Math.PI*2);ctx.fill();ctx.restore();
    }
  }
  function silhouettes(ctx){
    for(const d of decoys()){
      const fade=Math.min(1,d.age/.12,(d.life-d.age)/.4);
      ctx.save();ctx.globalAlpha=.82*fade;
      if(d.image)ctx.drawImage(d.image.canvas,d.x-d.image.x,d.y-d.image.y);
      else{
        // Keep the hair knot, folded arms and split legs readable while assets load.
        const h=d.bodyH;ctx.translate(d.x,d.y);ctx.fillStyle='#08070b';ctx.beginPath();ctx.moveTo(-7,-h*.84);ctx.lineTo(-9,-h);ctx.lineTo(2,-h*.94);ctx.lineTo(8,-h*.81);ctx.lineTo(7,-h*.65);ctx.lineTo(14,-h*.5);ctx.lineTo(10,-h*.32);ctx.lineTo(7,-h*.3);ctx.lineTo(10,0);ctx.lineTo(2,0);ctx.lineTo(0,-h*.26);ctx.lineTo(-3,0);ctx.lineTo(-11,0);ctx.lineTo(-8,-h*.34);ctx.lineTo(-14,-h*.48);ctx.lineTo(-8,-h*.65);ctx.closePath();ctx.fill();
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
  G.NarutoShikamaruDecoy={supports,profile,canCast,cast,update,clear,decoys,isDecoy,targetForEnemies,statusFor,
    stateFor:(a=G.Game.player)=>states.get(a)||null,stats:(a=G.Game.player)=>{const s=states.get(a);return s?{casts:s.casts,spawned:s.spawned,redirects:s.redirects}:null;}};
})();
