/* A separate, uncapped shadow possession field; existing Shikamaru combos stay independent. */
(() => {
  if(G.NarutoShikamaruMass)return;
  const S=G.NarutoShikamaru,C=G.Combat,ID='naruto-shikamaru-mass',MODE='shikamaru-mass';
  const states=new Map(),casts=[],leases=new Map();
  const alive=e=>!!e&&!e.dead&&e.hp>0;
  const valid=a=>alive(a)&&(a===G.Game.player||G.SelfClones?.isActor(a))&&(a.mon?.dex??a.dex)===30017;
  const learned=a=>a.moves?.find(m=>m.id===ID);
  const supports=m=>(typeof m==='string'?m:m?.digiMode)===MODE;
  function profile(a,m){
    const L=Math.max(1,Math.min(5,Math.floor(m?.lvl||1))),Q=Math.max(0,Math.floor(G.Quantity?.bonus(a)??a.quantityPicks??a.quantityBonus??0));
    return {kind:'mass',L,Q,radius:260+20*(L-1)+5*Math.min(12,Q),range:m?.range??440,
      bindDuration:3.2+.2*(L-1),cd:(m?.cd??32)*(a.cdMul??1),damage:(m?.dmg??45)*(a.atk??1),
      prepare:.32,speed:900,spread:.45,throwDelay:.55,bombFlight:.7,fuse:.32,aftermath:.7};
  }
  function legal(b){return !b.cancelled&&valid(b.owner)&&b.world===G.World&&states.get(b.owner)===b.state&&!!learned(b.owner);}
  function state(a){
    let s=states.get(a);if(s&&s.world!==G.World){clear(a);s=null;}
    if(!s){s={owner:a,world:G.World,cooldown:0,cast:null,casts:0,captured:0,hits:0,damage:0,contacts:[]};states.set(a,s);}return s;
  }
  function targets(center,radius){return G.EnemyMgr.queryCircle(center.x,center.y,radius+64).filter(e=>alive(e)&&!e.friendly&&Math.hypot(e.x-center.x,e.y-center.y)<=radius+(e.r||0)&&S.clearPath(center.x,center.y,e.x,e.y));}
  function canCast(a,m){return valid(a)&&!a.frozen&&supports(m)&&!!learned(a)&&state(a).cooldown<=1e-8&&targets(a,profile(a,m).radius).length>0;}
  function cast(a,m){
    if(!valid(a)||a.frozen||!supports(m)||!learned(a))return false;
    const s=state(a),p=profile(a,m),center={x:a.x,y:a.y},initial=targets(center,p.radius);
    if(s.cooldown>1e-8||!initial.length)return false;
    const farthest=initial.reduce((d,e)=>Math.max(d,Math.hypot(e.x-a.x,e.y-a.y)+Math.max(36,(e.r||12)+12)),0);
    const origin={...center},full=p.prepare+farthest/p.speed,arrive=p.prepare,throwAt=full+p.throwDelay,landAt=throwAt+p.bombFlight,blastAt=landAt+p.fuse,releaseAt=full+p.bindDuration;
    const b={owner:a,state:s,world:G.World,m:{...m},spec:p,origin,center,arrive,full,throwAt,landAt,blastAt,releaseAt,
      duration:Math.max(releaseAt+.35,blastAt+p.aftermath),age:0,radius:p.radius,initialTargets:new Set(initial),rays:new Map(),bound:new Set(),hitSet:new Set(),bomb:null,exploded:false,cancelled:false};
    s.cooldown=p.cd;m.t=p.cd;s.cast=b;s.casts++;casts.push(b);return true;
  }
  function held(e){
    const list=leases.get(e);return alive(e)&&!!list&&[...list].some(b=>legal(b)&&b.age<b.releaseAt&&b.bound.has(e));
  }
  function unbind(b,e){const list=leases.get(e);list?.delete(b);if(!list?.size)leases.delete(e);b.bound.delete(e);}
  function drop(b){b.cancelled=true;for(const e of b.bound)unbind(b,e);const i=casts.indexOf(b);if(i>=0)casts.splice(i,1);}
  function clear(owner){for(const b of casts.slice())if(!owner||b.owner===owner)drop(b);if(owner)states.delete(owner);else states.clear();}
  function explode(b){
    if(b.exploded||!legal(b))return;b.exploded=true;
    for(const e of new Set(G.EnemyMgr.queryCircle(b.center.x,b.center.y,b.spec.radius+64))){
      if(!legal(b))return;
      if(!alive(e)||e.friendly||b.hitSet.has(e)||Math.hypot(e.x-b.center.x,e.y-b.center.y)>b.spec.radius+(e.r||0)||!S.clearPath(b.center.x,b.center.y,e.x,e.y))continue;
      b.hitSet.add(e);const mult=G.Types?.mult?.(b.m.type||'fire',e.types)??1,damage=b.spec.damage*mult*(G.Weather?.mult?.(b.m.type||'fire')??1);
      e.hurt(damage,'#ffb461',0,0,0,G.Types?.label?.(mult),b.owner,ID);if(!legal(b))return;
      b.owner.onDealt?.(damage);if(!legal(b))return;
      b.owner.dmgDealt=(b.owner.dmgDealt||0)+damage;b.state.hits++;b.state.damage+=damage;
      if(b.state.contacts.length<256)b.state.contacts.push({targetId:e.id,x:e.x,y:e.y,damage,origin:{...b.center},radius:b.spec.radius});
    }
  }
  function update(dt){
    if(G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    for(const [a,s]of states)if(!valid(a)||s.world!==G.World){clear(a);}
    for(const b of casts.slice()){
      if(!legal(b)){drop(b);continue;}b.age+=dt;
      for(const e of [...b.bound])if(!alive(e)||b.age>=b.releaseAt||Math.hypot(e.x-b.center.x,e.y-b.center.y)>b.radius+(e.r||0)||!S.clearPath(b.owner.x,b.owner.y,e.x,e.y)||!S.clearPath(b.center.x,b.center.y,e.x,e.y))unbind(b,e);
      if(b.age>=b.spec.prepare&&b.age<b.releaseAt){
        for(const e of targets(b.center,b.radius))if(!b.rays.has(e))b.rays.set(e,{target:e,born:b.age-dt,travelled:0,source:{x:b.owner.x,y:b.owner.y,z:0},current:{x:b.owner.x,y:b.owner.y,z:0},previous:{x:b.owner.x,y:b.owner.y,z:0},hit:false,linked:true});
        for(const ray of b.rays.values()){
          const e=ray.target;if(!alive(e))continue;
          ray.source={x:b.owner.x,y:b.owner.y,z:0};ray.linked=S.clearPath(ray.source.x,ray.source.y,e.x,e.y)&&Math.hypot(e.x-b.center.x,e.y-b.center.y)<=b.radius+(e.r||0);
          if(!ray.linked)continue;
          const dx=e.x-ray.source.x,dy=e.y-ray.source.y,d=Math.hypot(dx,dy)||1,body=G.ShikamaruReferenceGeometry.bodyFor(e)||{bodyHeight:e.bodyH||24},height=body.bodyHeight*.45;
          const overrun=Math.max(36,(e.r||12)+12);ray.previous={...ray.current};ray.travelled=Math.min(d+overrun,ray.travelled+Math.max(0,Math.min(dt,b.age-b.spec.prepare))*b.spec.speed);
          // One straight, tapered shaft per target; its tip really sweeps through
          // the body before possession. Keep the whole shaft straight while moving.
          const reach=ray.hit?d+overrun:ray.travelled;ray.current={x:ray.source.x+dx/d*reach,y:ray.source.y+dy/d*reach,z:height*reach/Math.max(24,d)};
          if(!ray.hit){
            const probe={target:e,width:4},Ref=G.ShikamaruReferenceGeometry,contact=Ref.sweptBody(probe,ray.previous,ray.current,body,S.clearPath)||Ref.sweptBody(probe,ray.source,ray.current,body,S.clearPath);
            if(contact&&!ray.contact){ray.contact={...contact};ray.contactAge=b.age;}
            if(contact&&reach>=d+(e.r||12)+8){ray.hit=true;ray.boundAt=b.age;b.bound.add(e);if(!leases.has(e))leases.set(e,new Set());leases.get(e).add(b);b.state.captured++;}
          }
        }
      }
      const ready=[...b.initialTargets].every(e=>!alive(e)||Math.hypot(e.x-b.center.x,e.y-b.center.y)>b.radius+(e.r||0)||!S.clearPath(b.owner.x,b.owner.y,e.x,e.y)||b.rays.get(e)?.hit);
      if(!b.bomb&&b.age>=b.throwAt&&!ready){b.throwAt+=dt;b.landAt+=dt;b.blastAt+=dt;b.releaseAt+=dt;b.duration+=dt;}
      if(b.age>=b.throwAt&&!b.bomb){
        // A real hand-side release, saved once; moving afterwards cannot drag the bomb.
        const aim=Math.atan2(b.center.y-b.owner.y,b.center.x-b.owner.x),scale=b.owner.anim?.scale||1;
        b.bomb={source:{x:b.owner.x+Math.cos(aim)*12*scale,y:b.owner.y+Math.sin(aim)*7*scale-18*scale},aim};
      }
      if(b.age>=b.blastAt)explode(b);
      if(!legal(b)){drop(b);continue;}
      if(b.age>=b.duration){for(const e of [...b.bound])unbind(b,e);const i=casts.indexOf(b);if(i>=0)casts.splice(i,1);}
    }
  }
  function poseFor(a){
    const b=states.get(a)?.cast;if(!b||!legal(b)||b.age>=b.duration)return null;
    const aim=Math.atan2(b.center.y-a.y,b.center.x-a.x),moving=(G.NarutoShikamaru.stateFor(a)?.moving)||false;
    if(b.age<b.full)return {kind:'shadow',phase:'net',age:b.age,phaseAge:b.age,phaseDuration:b.full,aim,moving};
    if(b.age>=b.throwAt-.16&&b.age<b.throwAt+.25)return {kind:'trap',phase:b.age<b.throwAt?'prepare':'release',age:b.age-b.throwAt+.16,phaseAge:b.age<b.throwAt?b.age-b.throwAt+.16:b.age-b.throwAt,phaseDuration:b.age<b.throwAt?.16:.25,aim:b.bomb?.aim??aim,moving};
    return null;
  }
  function ground(ctx){
    for(const b of casts){if(!legal(b))continue;
      const fade=b.age>b.releaseAt?Math.max(0,1-(b.age-b.releaseAt)/.35):1;
      ctx.save();ctx.globalAlpha=fade;
      // A faint, soft-edged radius hint only; no opaque disk or decorative spokes.
      const r=b.radius,g=ctx.createRadialGradient(b.center.x,b.center.y,0,b.center.x,b.center.y,r);
      g.addColorStop(0,'rgba(20,14,28,.025)');g.addColorStop(.8,'rgba(20,14,28,.045)');g.addColorStop(1,'rgba(20,14,28,0)');
      ctx.fillStyle=g;ctx.beginPath();ctx.arc(b.center.x,b.center.y,r,0,Math.PI*2);ctx.fill();
      ctx.globalAlpha=fade;ctx.strokeStyle='#030304';ctx.lineWidth=4;
      for(const e of b.bound){ctx.beginPath();ctx.ellipse(e.x,e.y,(e.r||12)+4,5,0,0,Math.PI*2);ctx.stroke();ctx.beginPath();ctx.moveTo(e.x-(e.r||12),e.y);ctx.quadraticCurveTo(e.x,e.y-12,e.x+(e.r||12),e.y);ctx.stroke();}
      ctx.restore();
    }
  }
  function bomb(ctx,x,y,scale=1,spin=0){
    ctx.save();ctx.translate(x,y);ctx.scale(scale,scale);ctx.rotate(spin);ctx.fillStyle='#191a20';ctx.strokeStyle='#b9b6ac';ctx.lineWidth=1.5;
    ctx.beginPath();ctx.arc(0,0,12,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.fillStyle='#e8d6a5';ctx.fillRect(-4,-10,8,21);ctx.fillStyle='#874b36';ctx.fillRect(-1,-7,2,14);
    ctx.strokeStyle='#d5af72';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(5,-10);ctx.quadraticCurveTo(5,-20,13,-18);ctx.stroke();ctx.fillStyle='#ffd57e';ctx.fillRect(11,-21,5,5);ctx.restore();
  }
  function air(ctx){
    for(const b of casts){if(!legal(b))continue;
      if(b.age<b.releaseAt){ctx.save();ctx.fillStyle='#030304';for(const ray of b.rays.values()){
        if(!alive(ray.target)||!ray.linked||ray.travelled<=0)continue;const s=ray.source,t={x:ray.current.x,y:ray.current.y-ray.current.z},dx=t.x-s.x,dy=t.y-s.y,d=Math.hypot(dx,dy)||1,nx=-dy/d,ny=dx/d,neck=Math.max(0,d-22),w=3;
        ctx.beginPath();ctx.moveTo(s.x+nx,s.y+ny);ctx.lineTo(s.x+dx/d*neck+nx*w,s.y+dy/d*neck+ny*w);ctx.lineTo(t.x,t.y);ctx.lineTo(s.x+dx/d*neck-nx*w,s.y+dy/d*neck-ny*w);ctx.lineTo(s.x-nx,s.y-ny);ctx.closePath();ctx.fill();
      }ctx.restore();}
      if(b.bomb&&b.age<b.blastAt){const u=Math.max(0,Math.min(1,(b.age-b.throwAt)/b.spec.bombFlight)),s=b.bomb.source;
        bomb(ctx,s.x+(b.center.x-s.x)*u,s.y+(b.center.y-s.y)*u-Math.sin(Math.PI*u)*95,1.2,u*Math.PI*2);
      }
      if(b.exploded&&b.age<b.blastAt+b.spec.aftermath){
        const u=Math.min(1,(b.age-b.blastAt)/b.spec.aftermath),r=b.spec.radius*Math.min(1,u*2.2);
        ctx.save();ctx.globalAlpha=(1-u)*.9;ctx.strokeStyle='#ffe0a2';ctx.lineWidth=10*(1-u)+2;ctx.beginPath();ctx.arc(b.center.x,b.center.y,r,0,Math.PI*2);ctx.stroke();
        for(let i=0;i<16;i++){const a=i*Math.PI/8,d=r*.85;ctx.fillStyle=i%2?'#ea9b40':'#f9cf7b';ctx.beginPath();ctx.ellipse(b.center.x+Math.cos(a)*d,b.center.y+Math.sin(a)*d-12,18+15*(1-u),12+18*(1-u),a,0,Math.PI*2);ctx.fill();}
        ctx.globalAlpha=(1-u)*.8;ctx.fillStyle='#f3c781';ctx.beginPath();ctx.arc(b.center.x,b.center.y,48*(1-u)+12,0,Math.PI*2);ctx.fill();ctx.restore();
      }
    }
  }
  function statusFor(a,m){const s=states.get(a),b=s?.cast,cd=profile(a,m).cd,remaining=s?.cooldown||0;return {label:b&&legal(b)&&b.age<b.duration?(b.age<b.full?'展影':b.age<b.blastAt?'捕縛 '+b.bound.size:'起爆'):remaining>0?'大捕縛 '+Math.ceil(remaining)+'s':'大捕縛待命',fraction:1-Math.min(1,remaining/cd)};}
  const oldTick=C.tick,oldUpdate=C.updateFields,oldClear=C.clearFields,oldGround=C.drawGroundFields,oldAir=C.drawAirFields;
  C.tick=function(dt,a,...args){const result=oldTick.call(this,dt,a,...args);if(G.Game.state==='playing'&&valid(a)&&!a.frozen&&Number.isFinite(dt)&&dt>0){const m=learned(a);if(m){const s=state(a);s.cooldown=Math.max(0,s.cooldown-dt);m.t=s.cooldown;if(s.cooldown<=1e-8)cast(a,m);}}return result;};
  C.updateFields=function(dt){const result=oldUpdate.call(this,dt);update(dt);return result;};
  C.clearFields=function(a){clear(a);return oldClear.call(this,a);};
  C.drawGroundFields=function(ctx){oldGround.call(this,ctx);ground(ctx);};C.drawAirFields=function(ctx){oldAir.call(this,ctx);air(ctx);};
  const oldHeld=S.held,oldStopped=S.stopped,oldSUpdate=S.update,oldSClear=S.clear,oldSupports=S.supports,oldCanCast=S.canCast,oldCast=S.cast,oldProfile=S.profile,oldActive=S.activeFor,oldStatus=S.statusFor;
  S.held=e=>oldHeld(e)||held(e);S.stopped=e=>oldStopped(e)||held(e);
  S.update=function(dt){oldSUpdate(dt);update(dt);};S.clear=function(a){clear(a);oldSClear(a);};
  S.supports=m=>supports(m)||oldSupports(m);S.canCast=(a,m)=>supports(m)?canCast(a,m):oldCanCast(a,m);
  S.cast=(a,m)=>supports(m)?cast(a,m):oldCast(a,m);S.profile=(a,m)=>supports(m)?profile(a,m):oldProfile(a,m);
  S.activeFor=a=>poseFor(a)||oldActive(a);S.statusFor=(a,m)=>supports(m)?statusFor(a,m):oldStatus(a,m);
  G.NarutoShikamaruMass={profile,cast,canCast,update,clear,held,statusFor,poseFor,stateFor:a=>states.get(a),get casts(){return casts;},get leases(){return leases;}};
})();
