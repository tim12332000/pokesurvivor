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
  function targetPoint(a,p){
    const eligible=e=>alive(e)&&!e.friendly&&Math.hypot(e.x-a.x,e.y-a.y)<=p.range&&S.clearPath(a.x,a.y,e.x,e.y);
    const aimed=e=>{
      const dx=e.x-a.x,dy=e.y-a.y,d=Math.hypot(dx,dy)||1;
      // Bias the huge circle toward the player so its bomb landing stays visible.
      // The chosen enemy still lies inside; explicitly specified points are unchanged.
      const inset=Math.min(p.radius*.35,Math.max(40,(G.Camera.w||768)/2-p.radius-16));
      const offset=Math.min(d,Math.max(inset,d-p.radius+24));
      return {x:a.x+dx/d*offset,y:a.y+dy/d*offset};
    };
    if(eligible(a.target))return aimed(a.target);
    const list=G.EnemyMgr.queryCircle(a.x,a.y,p.range).filter(eligible);
    const e=list.reduce((best,e)=>!best||Math.hypot(e.x-a.x,e.y-a.y)<Math.hypot(best.x-a.x,best.y-a.y)?e:best,null);
    return e?aimed(e):null;
  }
  function canCast(a,m){return valid(a)&&!a.frozen&&supports(m)&&!!learned(a)&&state(a).cooldown<=1e-8&&!!targetPoint(a,profile(a,m));}
  function footprint(b){
    const points=[];
    for(let i=0;i<96;i++){
      const angle=i*Math.PI*2/96,dx=Math.cos(angle),dy=Math.sin(angle);let low=0,high=b.spec.radius;
      if(S.clearPath(b.center.x,b.center.y,b.center.x+dx*high,b.center.y+dy*high))low=high;
      else for(let k=0;k<7;k++){const mid=(low+high)/2;if(S.clearPath(b.center.x,b.center.y,b.center.x+dx*mid,b.center.y+dy*mid))low=mid;else high=mid;}
      points.push({x:b.center.x+dx*low,y:b.center.y+dy*low});
    }
    b.footprint=points;b.maskAge=b.age;
  }
  function cast(a,m,point=null){
    if(!valid(a)||a.frozen||!supports(m)||!learned(a))return false;
    const s=state(a),p=profile(a,m),center=point?{x:point.x,y:point.y}:targetPoint(a,p);
    if(s.cooldown>1e-8||!center||!Number.isFinite(center.x)||!Number.isFinite(center.y)||Math.hypot(center.x-a.x,center.y-a.y)>p.range||!S.clearPath(a.x,a.y,center.x,center.y))return false;
    const origin={x:a.x,y:a.y},distance=Math.hypot(center.x-origin.x,center.y-origin.y),arrive=p.prepare+distance/p.speed,full=arrive+p.spread,throwAt=full+p.throwDelay,landAt=throwAt+p.bombFlight,blastAt=landAt+p.fuse,releaseAt=full+p.bindDuration;
    const b={owner:a,state:s,world:G.World,m:{...m},spec:p,origin,center,distance,arrive,full,throwAt,landAt,blastAt,releaseAt,
      duration:Math.max(releaseAt+.35,blastAt+p.aftermath),age:0,radius:0,bound:new Set(),hitSet:new Set(),bomb:null,exploded:false,cancelled:false,tether:{source:{...origin},tip:{...origin},linked:true}};
    footprint(b);s.cooldown=p.cd;m.t=p.cd;s.cast=b;s.casts++;casts.push(b);return true;
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
      if(!b.bomb&&!S.clearPath(b.origin.x,b.origin.y,b.center.x,b.center.y)){drop(b);continue;}
      const progress=Math.max(0,Math.min(1,(b.age-b.spec.prepare)/(b.arrive-b.spec.prepare||1))),source={x:b.owner.x,y:b.owner.y},tip={x:b.origin.x+(b.center.x-b.origin.x)*progress,y:b.origin.y+(b.center.y-b.origin.y)*progress};
      b.tether={source,tip,linked:S.clearPath(source.x,source.y,tip.x,tip.y)};
      b.radius=b.spec.radius*Math.max(0,Math.min(1,(b.age-b.arrive)/b.spec.spread));
      if(b.age-b.maskAge>=.25)footprint(b);
      for(const e of [...b.bound])if(!alive(e)||b.age>=b.releaseAt||Math.hypot(e.x-b.center.x,e.y-b.center.y)>b.radius+(e.r||0)||!S.clearPath(b.center.x,b.center.y,e.x,e.y))unbind(b,e);
      if(b.radius>0&&b.age<b.releaseAt)for(const e of G.EnemyMgr.queryCircle(b.center.x,b.center.y,b.radius+64)){
        if(!legal(b))break;
        if(!alive(e)||e.friendly||b.bound.has(e)||Math.hypot(e.x-b.center.x,e.y-b.center.y)>b.radius+(e.r||0)||!S.clearPath(b.center.x,b.center.y,e.x,e.y))continue;
        b.bound.add(e);if(!leases.has(e))leases.set(e,new Set());leases.get(e).add(b);b.state.captured++;
      }
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
  function path(ctx,points){ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.closePath();}
  function ground(ctx){
    for(const b of casts){if(!legal(b))continue;
      const fade=b.age>b.releaseAt?Math.max(0,1-(b.age-b.releaseAt)/.35):1;
      ctx.save();ctx.globalAlpha=fade;
      // The fixed circle is the chosen footprint, never a target-count budget.
      ctx.strokeStyle='#a69aa8';ctx.lineWidth=1.5;ctx.setLineDash([9,10]);ctx.beginPath();ctx.arc(b.center.x,b.center.y,b.spec.radius,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);
      if(b.age>=b.spec.prepare&&b.age<b.releaseAt&&b.tether.linked){
        const {source,tip}=b.tether,dx=tip.x-source.x,dy=tip.y-source.y,d=Math.hypot(dx,dy)||1,nx=-dy/d,ny=dx/d,bend=Math.min(19,d*.15);
        ctx.fillStyle='#030304';ctx.beginPath();ctx.moveTo(source.x+nx*5,source.y+ny*5);ctx.quadraticCurveTo((source.x+tip.x)/2+nx*bend,(source.y+tip.y)/2+ny*bend,tip.x+nx*13,tip.y+ny*13);ctx.lineTo(tip.x-nx*13,tip.y-ny*13);ctx.quadraticCurveTo((source.x+tip.x)/2-nx*bend*.5,(source.y+tip.y)/2-ny*bend*.5,source.x-nx*5,source.y-ny*5);ctx.closePath();ctx.fill();
      }
      if(b.radius>0){
        ctx.save();path(ctx,b.footprint);ctx.clip();ctx.beginPath();ctx.arc(b.center.x,b.center.y,b.radius,0,Math.PI*2);ctx.clip();
        ctx.globalAlpha=fade*.68;ctx.fillStyle='#030304';ctx.fillRect(b.center.x-b.spec.radius,b.center.y-b.spec.radius,b.spec.radius*2,b.spec.radius*2);
        // Broad grounded fingers show the advancing black front without hiding actors.
        ctx.globalAlpha=fade;ctx.strokeStyle='#030304';ctx.lineCap='round';
        for(let i=0;i<9;i++){const a=i*Math.PI*2/9+.13,r=b.radius*.96;ctx.lineWidth=6+3*Math.sin(i*2);ctx.beginPath();ctx.moveTo(b.center.x,b.center.y);ctx.quadraticCurveTo(b.center.x+Math.cos(a+.28)*r*.6,b.center.y+Math.sin(a+.28)*r*.6,b.center.x+Math.cos(a)*r,b.center.y+Math.sin(a)*r);ctx.stroke();}
        ctx.restore();
      }
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
