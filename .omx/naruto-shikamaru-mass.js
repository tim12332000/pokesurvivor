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
      prepare:.32,speed:900,spread:.45,throwDelay:.55,bombFlight:.7,fuse:.32,aftermath:1.5,
      // Double both the launch span (.36 -> .72) and travel time; keep the 45% electric budget.
      shockPulses:6,shockGap:.144,shockSpeed:310,shockMinDuration:.48,shockScale:.075,bombScale:.55};
  }
  function legal(b){return !b.cancelled&&valid(b.owner)&&b.world===G.World&&states.get(b.owner)===b.state&&!!learned(b.owner);}
  function state(a){
    let s=states.get(a);if(s&&s.world!==G.World){clear(a);s=null;}
    if(!s){s={owner:a,world:G.World,cooldown:0,cast:null,casts:0,captured:0,hits:0,shockHits:0,bombHits:0,damage:0,contacts:[]};states.set(a,s);}return s;
  }
  const lineClear=(ax,ay,bx,by)=>G.ShikamaruReferenceGeometry?.lineClear?G.ShikamaruReferenceGeometry.lineClear(ax,ay,bx,by,S.clearPath):S.clearPath(ax,ay,bx,by);
  function targets(center,radius){return G.EnemyMgr.queryCircle(center.x,center.y,radius+64).filter(e=>alive(e)&&!e.friendly&&Math.hypot(e.x-center.x,e.y-center.y)<=radius+(e.r||0)&&lineClear(center.x,center.y,e.x,e.y));}
  function hasTarget(center,radius){for(const e of G.EnemyMgr.queryCircle(center.x,center.y,radius+64))if(alive(e)&&!e.friendly&&Math.hypot(e.x-center.x,e.y-center.y)<=radius+(e.r||0)&&lineClear(center.x,center.y,e.x,e.y))return true;return false;}
  function canCast(a,m){return valid(a)&&!a.frozen&&supports(m)&&!!learned(a)&&state(a).cooldown<=1e-8&&hasTarget(a,profile(a,m).radius);}
  function cast(a,m){
    if(!valid(a)||a.frozen||!supports(m)||!learned(a))return false;
    const s=state(a),p=profile(a,m),center={x:a.x,y:a.y},initial=targets(center,p.radius);
    if(s.cooldown>1e-8||!initial.length)return false;
    const farthest=initial.reduce((d,e)=>Math.max(d,Math.hypot(e.x-a.x,e.y-a.y)+Math.max(36,(e.r||12)+12)),0);
    const origin={...center},full=p.prepare+farthest/p.speed,arrive=p.prepare,throwAt=full+p.throwDelay,landAt=throwAt+p.bombFlight,blastAt=landAt+p.fuse,releaseAt=full+p.bindDuration;
    const b={owner:a,state:s,world:G.World,m:{...m},spec:p,origin,center,aim:a.aim||0,arrive,full,throwAt,landAt,blastAt,releaseAt,
      duration:Math.max(releaseAt+.35,blastAt+p.aftermath),age:0,radius:p.radius,initialTargets:new Set(initial),rays:new Map(),bound:new Set(),hitSet:new Set(),conductAt:null,bomb:null,exploded:false,cancelled:false};
    s.cooldown=p.cd;m.t=p.cd;s.cast=b;s.casts++;casts.push(b);return true;
  }
  function held(e){
    const list=leases.get(e);return alive(e)&&!!list&&[...list].some(b=>legal(b)&&b.age<b.releaseAt&&b.bound.has(e));
  }
  function unbind(b,e){const list=leases.get(e);list?.delete(b);if(!list?.size)leases.delete(e);b.bound.delete(e);}
  function drop(b){b.cancelled=true;for(const e of b.bound)unbind(b,e);const i=casts.indexOf(b);if(i>=0)casts.splice(i,1);}
  function clear(owner){for(const b of casts.slice())if(!owner||b.owner===owner)drop(b);if(owner)states.delete(owner);else states.clear();}
  function deal(b,e,scale,type,stage,pulse=0){
    if(!legal(b)||!alive(e))return false;
    const mult=G.Types?.mult?.(type,e.types)??1,damage=b.spec.damage*scale*mult*(G.Weather?.mult?.(type)??1);
    // Split each previous rounded shock across two arrivals so six hits preserve actual HP loss.
    const paired=stage==='shock'&&b.spec.shockPulses===6,pairDamage=Math.max(1,Math.round(damage*2));
    const amount=paired?(pulse%2?Math.floor(pairDamage/2):Math.ceil(pairDamage/2)):damage;
    if(!paired||amount>0)e.hurt(amount,stage==='shock'?'#ffe7a3':'#ffb461',0,0,0,G.Types?.label?.(mult),b.owner,ID);if(!legal(b))return false;
    b.owner.onDealt?.(damage);if(!legal(b))return false;
    b.owner.dmgDealt=(b.owner.dmgDealt||0)+damage;b.state.hits++;b.state[stage==='shock'?'shockHits':'bombHits']++;b.state.damage+=damage;
    if(b.state.contacts.length<256)b.state.contacts.push({stage,pulse,targetId:e.id,x:e.x,y:e.y,damage,origin:{...b.center},radius:b.spec.radius});
    return legal(b);
  }
  function explode(b){
    if(b.exploded||!legal(b))return;b.exploded=true;
    G.Audio?.sfx?.('shot',{kind:'cannon',type:'fire',main:true});
    for(const e of new Set(G.EnemyMgr.queryCircle(b.center.x,b.center.y,b.spec.radius+64))){
      if(!legal(b))return;
      if(!alive(e)||e.friendly||b.hitSet.has(e)||Math.hypot(e.x-b.center.x,e.y-b.center.y)>b.spec.radius+(e.r||0)||!S.clearPath(b.center.x,b.center.y,e.x,e.y))continue;
      b.hitSet.add(e);if(!deal(b,e,b.spec.bombScale,b.m.type||'fire','bomb'))return;
    }
  }
  function update(dt){
    if(G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    for(const [a,s]of states)if(!valid(a)||s.world!==G.World){clear(a);}
    for(const b of casts.slice()){
      if(!legal(b)){drop(b);continue;}b.age+=dt;
      const ox=b.owner.x,oy=b.owner.y,cx=b.center.x,cy=b.center.y,pathFn=G.World?.projectilePathClear;
      const ownerClearCache=new Map(),centerClearCache=new Map();
      const ownerClear=e=>{
        let v=ownerClearCache.get(e);if(v!==undefined)return v;
        const r=b.rays.get(e);
        if(r&&r._ocWorld===G.World&&r._ocPath===pathFn&&r._ocOx===ox&&r._ocOy===oy&&r._ocEx===e.x&&r._ocEy===e.y){v=r._ocVal;}
        else{v=lineClear(ox,oy,e.x,e.y);if(r){r._ocWorld=G.World;r._ocPath=pathFn;r._ocOx=ox;r._ocOy=oy;r._ocEx=e.x;r._ocEy=e.y;r._ocVal=v;}}
        ownerClearCache.set(e,v);return v;
      };
      const centerClear=e=>{
        let v=centerClearCache.get(e);if(v!==undefined)return v;
        const r=b.rays.get(e);
        if(r&&r._ccWorld===G.World&&r._ccPath===pathFn&&r._ccEx===e.x&&r._ccEy===e.y){v=r._ccVal;}
        else{v=lineClear(cx,cy,e.x,e.y);if(r){r._ccWorld=G.World;r._ccPath=pathFn;r._ccEx=e.x;r._ccEy=e.y;r._ccVal=v;}}
        centerClearCache.set(e,v);return v;
      };
      const inRadius=e=>{const dx=e.x-cx,dy=e.y-cy,lim=b.radius+(e.r||0);return dx*dx+dy*dy<=lim*lim;};
      for(const e of [...b.bound])if(!alive(e)||b.age>=b.releaseAt||!inRadius(e)||!ownerClear(e)||!centerClear(e))unbind(b,e);
      if(b.age>=b.spec.prepare&&b.age<b.releaseAt){
        for(const e of G.EnemyMgr.queryCircle(cx,cy,b.radius+64)){
          if(b.rays.has(e)||!alive(e)||e.friendly||!inRadius(e)||!centerClear(e))continue;
          b.rays.set(e,{target:e,born:b.age-dt,travelled:0,source:{x:ox,y:oy,z:0},current:{x:ox,y:oy,z:0},previous:{x:ox,y:oy,z:0},hit:false,linked:true,shocks:[],shockEvents:[]});
        }
        for(const ray of b.rays.values()){
          const e=ray.target;if(!alive(e))continue;
          ray.source={x:ox,y:oy,z:0};ray.linked=inRadius(e)&&ownerClear(e);
          if(!ray.linked)continue;
          const dx=e.x-ox,dy=e.y-oy,d=Math.hypot(dx,dy)||1;
          let body=ray.bodyCache;
          if(!body||ray.bodyFrame!==e.anim?.frame||ray.bodyCur!==e.anim?.cur||ray.bodyDir!==e.anim?.dir){
            body=G.ShikamaruReferenceGeometry.bodyFor(e)||{bodyHeight:e.bodyH||24};
            ray.bodyCache=body;ray.bodyFrame=e.anim?.frame;ray.bodyCur=e.anim?.cur;ray.bodyDir=e.anim?.dir;
          }
          const height=body.bodyHeight*.45;
          ray.bodyPoint={x:e.x,y:e.y,z:height};
          const overrun=Math.max(36,(e.r||12)+12);ray.previous={...ray.current};ray.travelled=Math.min(d+overrun,ray.travelled+Math.max(0,Math.min(dt,b.age-b.spec.prepare))*b.spec.speed);
          // One straight, tapered shaft per target; its tip really sweeps through
          // the body before possession. Keep the whole shaft straight while moving.
          const reach=ray.hit?d+overrun:ray.travelled;ray.current={x:ox+dx/d*reach,y:oy+dy/d*reach,z:height*reach/Math.max(24,d)};
          if(!ray.hit){
            const probe={target:e,width:4},Ref=G.ShikamaruReferenceGeometry,contact=Ref.sweptBody(probe,ray.previous,ray.current,body,S.clearPath)||Ref.sweptBody(probe,ray.source,ray.current,body,S.clearPath);
            if(contact&&!ray.contact){ray.contact={...contact};ray.contactAge=b.age;}
            if(contact&&reach>=d+(e.r||12)+8){ray.hit=true;ray.boundAt=b.age;b.bound.add(e);if(!leases.has(e))leases.set(e,new Set());leases.get(e).add(b);b.state.captured++;}
          }
        }
      }
      const ready=[...b.initialTargets].every(e=>!alive(e)||!inRadius(e)||!ownerClear(e)||b.rays.get(e)?.hit);
      if(ready&&b.conductAt===null)b.conductAt=b.age+.12;
      if(b.conductAt!==null)for(const ray of b.rays.values()){
        if(!legal(b))break;
        const e=ray.target,connected=alive(e)&&ray.linked&&b.bound.has(e)&&held(e)&&b.age<b.releaseAt;
        if(!connected){for(const packet of ray.shocks)if(!packet.done){packet.done=true;packet.cancelled=true;}continue;}
        const first=Math.max(b.conductAt,ray.boundAt+.1);
        while(ray.shocks.length<b.spec.shockPulses&&b.age>=first+ray.shocks.length*b.spec.shockGap){
          const born=first+ray.shocks.length*b.spec.shockGap,length=Math.hypot(ray.bodyPoint.x-ray.source.x,ray.bodyPoint.y-ray.source.y,ray.bodyPoint.z);
          ray.shocks.push({pulse:ray.shocks.length+1,born,duration:Math.max(b.spec.shockMinDuration,length/b.spec.shockSpeed),progress:0,done:false});
        }
        for(const packet of ray.shocks){
          if(!legal(b))break;if(packet.done)continue;packet.progress=Math.min(1,Math.max(0,(b.age-packet.born)/packet.duration));
          if(packet.progress>=1){packet.done=true;if(!deal(b,e,b.spec.shockScale,'electric','shock',packet.pulse))break;ray.shockEvents.push({at:b.age,pulse:packet.pulse,point:{...ray.bodyPoint}});}
        }
      }
      if(!legal(b)){drop(b);continue;}
      const charged=ready&&[...b.initialTargets].every(e=>!alive(e)||!b.bound.has(e)||!b.rays.get(e)?.linked||(b.rays.get(e).shocks.length===b.spec.shockPulses&&b.rays.get(e).shocks.every(p=>p.done)));
      if(!b.bomb&&b.age>=b.throwAt&&!charged){b.throwAt+=dt;b.landAt+=dt;b.blastAt+=dt;b.releaseAt+=dt;b.duration+=dt;}
      if(b.age>=b.throwAt&&!b.bomb){
        // A real hand-side release, saved once; moving afterwards cannot drag the bomb.
        const aim=Math.hypot(b.center.x-b.owner.x,b.center.y-b.owner.y)>4?Math.atan2(b.center.y-b.owner.y,b.center.x-b.owner.x):b.aim,scale=b.owner.anim?.scale||1;
        b.bomb={source:{x:b.owner.x+Math.cos(aim)*12*scale,y:b.owner.y+Math.sin(aim)*7*scale-18*scale},aim};
      }
      if(b.age>=b.blastAt)explode(b);
      if(!legal(b)){drop(b);continue;}
      if(b.age>=b.duration){for(const e of [...b.bound])unbind(b,e);const i=casts.indexOf(b);if(i>=0)casts.splice(i,1);}
    }
  }
  function poseFor(a){
    const b=states.get(a)?.cast;if(!b||!legal(b)||b.age>=b.duration)return null;
    const aim=Math.hypot(b.center.x-a.x,b.center.y-a.y)>4?Math.atan2(b.center.y-a.y,b.center.x-a.x):b.aim,moving=!!(G.NarutoShikamaru.stateFor(a)?.moving);
    const pose=(phase,started,duration)=>({kind:'mass',phase,age:b.age,phaseAge:b.age-started,phaseDuration:duration,aim:b.bomb?.aim??aim,moving});
    if(b.age<b.spec.prepare)return pose('mass-charge',0,b.spec.prepare);
    if(b.age<b.full+.08)return pose('mass-seal',b.spec.prepare,b.full+.08-b.spec.prepare);
    const sendDuration=b.spec.shockGap*(b.spec.shockPulses-1)+.16;
    if(b.conductAt!==null&&b.age>=b.conductAt-.1&&b.age<b.conductAt+sendDuration)return pose('mass-conduct',b.conductAt-.1,sendDuration+.1);
    if(b.age>=b.throwAt-.18&&b.age<b.throwAt)return pose('mass-throw-prepare',b.throwAt-.18,.18);
    if(b.age>=b.throwAt&&b.age<b.throwAt+.1)return pose('mass-throw-release',b.throwAt,.1);
    if(b.age>=b.throwAt+.1&&b.age<b.throwAt+.3)return pose('mass-throw-recover',b.throwAt+.1,.2);
    return null;
  }
  function rayVisualFor(b,ray){
    const since=ray.hit?Math.max(0,b.age-ray.boundAt):0,punch=ray.hit?Math.max(0,1-since/.12):1;
    return {width:.7+2.3*punch,head:8+20*punch,impact:ray.hit?Math.max(0,1-since/.1):0};
  }
  function shockPoint(ray,packet){const u=packet.progress;return {x:ray.source.x+(ray.bodyPoint.x-ray.source.x)*u,y:ray.source.y+(ray.bodyPoint.y-ray.source.y)*u,z:ray.bodyPoint.z*u};}
  function blastVisual(b){const age=Math.max(0,b.age-b.blastAt);return {age,u:Math.min(1,age/b.spec.aftermath),front:1-(1-Math.min(1,age/.24))**3,heat:Math.max(0,1-age/1.05),detail:(G.Settings?.fx??1)>0};}
  function drawBlastBack(ctx,b,v){
    const r=b.radius,x=b.center.x,y=b.center.y,growth=Math.min(1,v.age/.12),n=v.detail?9:6;
    ctx.save();
    for(let i=0;i<(v.detail?9:5);i++){const a=i*2.39996,d=r*(.12+.24*v.u),size=r*(.16+.035*(i%3))*(.7+v.u);ctx.globalAlpha=Math.sin(Math.PI*v.u)*.43;ctx.fillStyle=i%2?'#4c3930':'#9b7655';ctx.beginPath();ctx.ellipse(x+Math.cos(a)*d,y+Math.sin(a)*d*.5-r*(.08+.42*v.u),size,size*.85,a*.08,0,Math.PI*2);ctx.fill();}
    if(v.heat>0){
      ctx.globalAlpha=v.heat*.88;ctx.fillStyle='#b44820';ctx.beginPath();ctx.ellipse(x,y-r*.06,r*.52*growth,r*.34*growth,0,0,Math.PI*2);ctx.fill();
      for(let i=0;i<n;i++){
        const a=i*2.39996,d=r*(.04+.23*growth),px=x+Math.cos(a)*d,py=y+Math.sin(a)*d*.48-r*.1*growth,size=r*(.22+.045*Math.sin(i*1.7)**2)*(.55+.45*v.heat)*growth;
        ctx.globalAlpha=v.heat*.86;ctx.fillStyle=i%2?'#dc6825':'#f4a337';ctx.beginPath();ctx.moveTo(px-size,py+size*.45);ctx.bezierCurveTo(px-size*1.35,py-size*.65,px-size*.35,py-size*1.6,px+size*.12,py-size*(1.7+.4*Math.sin(i*2.1)));ctx.bezierCurveTo(px+size*.35,py-size*.65,px+size*1.3,py-size*.4,px+size,py+size*.45);ctx.closePath();ctx.fill();
        ctx.fillStyle='#ffd36d';ctx.beginPath();ctx.ellipse(px,py-size*.12,size*.66,size*.79,0,0,Math.PI*2);ctx.fill();
      }
      const h=r*(.58+.22*v.heat)*growth,w=r*.24*growth;ctx.globalAlpha=v.heat*.8;ctx.fillStyle='#ffb345';ctx.beginPath();ctx.moveTo(x-w,y);ctx.bezierCurveTo(x-w*1.2,y-h*.35,x+w*.45,y-h*.65,x-w*.12,y-h);ctx.bezierCurveTo(x+w*.8,y-h*.65,x+w*1.3,y-h*.3,x+w,y);ctx.closePath();ctx.fill();ctx.fillStyle='#ffe8a3';ctx.beginPath();ctx.ellipse(x,y-r*.07,w*.75,r*.19*growth,0,0,Math.PI*2);ctx.fill();
    }ctx.restore();
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
      if(b.bound.size){
        ctx.beginPath();
        for(const e of b.bound){const er=(e.r||12);ctx.moveTo(e.x+er+4,e.y);ctx.ellipse(e.x,e.y,er+4,5,0,0,Math.PI*2);ctx.moveTo(e.x-er,e.y);ctx.quadraticCurveTo(e.x,e.y-12,e.x+er,e.y);}
        ctx.stroke();
      }
      if(b.exploded&&b.age<b.blastAt+b.spec.aftermath){
        const v=blastVisual(b),r=b.radius*v.front;
        ctx.globalAlpha=(1-v.u)*.48;ctx.fillStyle='#2a1d19';ctx.beginPath();ctx.ellipse(b.center.x,b.center.y,r*.75,r*.44,0,0,Math.PI*2);ctx.fill();
        ctx.strokeStyle='#5a3425';ctx.lineWidth=3;for(let i=0;i<(v.detail?10:6);i++){const a=i*2.39996,d=r*(.54+.2*Math.sin(i*1.7));ctx.beginPath();ctx.moveTo(b.center.x+Math.cos(a)*r*.12,b.center.y+Math.sin(a)*r*.12);ctx.lineTo(b.center.x+Math.cos(a+.1)*d*.55,b.center.y+Math.sin(a+.1)*d*.55);ctx.lineTo(b.center.x+Math.cos(a)*d,b.center.y+Math.sin(a)*d);ctx.stroke();}
        drawBlastBack(ctx,b,v);
      }
      ctx.restore();
    }
  }
  function bomb(ctx,x,y,scale=1,spin=0,burn=0){
    ctx.save();ctx.translate(x,y);ctx.scale(scale,scale);ctx.rotate(spin);
    ctx.fillStyle='#17191c';ctx.strokeStyle='#ffd27a';ctx.lineWidth=1.8;ctx.beginPath();ctx.arc(0,0,10,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.fillStyle='#8a8063';ctx.fillRect(-5,-6,4,2);
    ctx.fillStyle='#fff0c3';ctx.fillRect(-5,4,11,20);ctx.strokeStyle='#703321';ctx.lineWidth=1;ctx.strokeRect(-5,4,11,20);ctx.fillStyle='#b33c25';ctx.fillRect(-1,7,2,14);ctx.fillRect(-3,11,6,2);ctx.fillRect(-3,16,6,2);
    ctx.strokeStyle='#e8b95f';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(3,-9);ctx.quadraticCurveTo(3,-17,10,-15);ctx.stroke();
    ctx.fillStyle='#ff8d30';ctx.beginPath();ctx.arc(11,-16,4+2*burn,0,Math.PI*2);ctx.fill();ctx.fillStyle='#fff5c1';ctx.fillRect(9,-18,4,4);
    ctx.strokeStyle='#ffe596';ctx.lineWidth=1;for(let i=0;i<4;i++){const a=i*Math.PI/2+burn*2;ctx.beginPath();ctx.moveTo(11+Math.cos(a)*5,-16+Math.sin(a)*5);ctx.lineTo(11+Math.cos(a)*(8+3*burn),-16+Math.sin(a)*(8+3*burn));ctx.stroke();}ctx.restore();
  }
  function bombPoint(b,u){const s=b.bomb.source,side=Math.cos(b.bomb.aim)<-.25?-1:1;return {x:s.x+(b.center.x-s.x)*u+Math.sin(Math.PI*u)*24*side,y:s.y+(b.center.y-s.y)*u-Math.sin(Math.PI*u)*84};}
  function air(ctx){
    for(const b of casts){if(!legal(b))continue;
      if(b.age<b.releaseAt){
        ctx.save();ctx.fillStyle='#030304';ctx.beginPath();
        const impacts=[],shocks=[],events=[];
        for(const ray of b.rays.values()){
          if(!alive(ray.target)||!ray.linked||ray.travelled<=0)continue;
          const s=ray.source,tx=ray.current.x,ty=ray.current.y-ray.current.z,dx=tx-s.x,dy=ty-s.y,d=Math.hypot(dx,dy)||1,inv=1/d,ux=dx*inv,uy=dy*inv,nx=-uy,ny=ux,v=rayVisualFor(b,ray),neck=Math.max(0,d-v.head),tail=Math.min(1,v.width),nxT=nx*tail,nyT=ny*tail,nxW=nx*v.width,nyW=ny*v.width,px=s.x+ux*neck,py=s.y+uy*neck;
          ctx.moveTo(s.x+nxT,s.y+nyT);ctx.lineTo(px+nxT,py+nyT);ctx.lineTo(px+nxW,py+nyW);ctx.lineTo(tx,ty);ctx.lineTo(px-nxW,py-nyW);ctx.lineTo(px-nxT,py-nyT);ctx.lineTo(s.x-nxT,s.y-nyT);ctx.closePath();
          if(v.impact&&ray.contact)impacts.push({ray,ux,uy,nx,ny,impact:v.impact});
          if(b.bound.has(ray.target)){
            for(const packet of ray.shocks)if(!packet.done&&packet.progress>0)shocks.push({ray,packet,ux,uy,nx,ny});
          }
          const event=ray.shockEvents.at(-1);if(event&&b.age-event.at<.2)events.push({ray,event});
        }
        ctx.fill();
        if(impacts.length){
          ctx.strokeStyle='#d3c4a6';ctx.lineWidth=1;
          for(const it of impacts){const x=it.ray.contact.x,y=it.ray.contact.y-it.ray.contact.z,span=10+5*it.impact;ctx.globalAlpha=it.impact;ctx.beginPath();for(const sign of [-1,1]){ctx.moveTo(x+it.nx*4*sign,y+it.ny*4*sign);ctx.lineTo(x+it.nx*span*sign-it.ux*4,y+it.ny*span*sign-it.uy*4);}ctx.stroke();}
          ctx.globalAlpha=1;
        }
        if(shocks.length){
          ctx.lineJoin='miter';
          const segs=[];
          for(const item of shocks){
            const s=item.ray.source,body=item.ray.bodyPoint,l=Math.hypot(body.x-s.x,body.y-body.z-s.y)||1,start=Math.max(0,item.packet.progress-Math.min(.25,34/l));
            const tip=shockPoint(item.ray,item.packet);
            segs.push({s,body,start,prog:item.packet.progress,endX:tip.x,endY:tip.y-tip.z,ux:item.ux,uy:item.uy,nx:item.nx,ny:item.ny});
          }
          ctx.beginPath();
          for(const g of segs){const bx=g.body.x-g.s.x,by=g.body.y-g.body.z-g.s.y;for(let j=0;j<=6;j++){const u=g.start+(g.prog-g.start)*j/6,off=j&&j<6?(j%2?1:-1)*5:0,x=g.s.x+bx*u+g.nx*off,y=g.s.y+by*u+g.ny*off;j?ctx.lineTo(x,y):ctx.moveTo(x,y);}}
          ctx.strokeStyle='#ffca28';ctx.lineWidth=4.5;ctx.stroke();
          ctx.strokeStyle='#fff6c8';ctx.lineWidth=1.8;ctx.stroke();
          ctx.beginPath();
          for(const g of segs){ctx.moveTo(g.endX-g.ux*10,g.endY-g.uy*10);ctx.lineTo(g.endX,g.endY);}
          ctx.stroke();
        }
        if(events.length){
          for(const it of events){
            const u=(b.age-it.event.at)/.2,x=it.event.point.x,y=it.event.point.y-it.event.point.z,r=(it.ray.target.r||12)+7;
            ctx.globalAlpha=1-u;ctx.beginPath();
            for(let j=0;j<9;j++){const a=j*Math.PI/4,d=r*(j%2?.6:1);const px=x+Math.cos(a)*d,py=y+Math.sin(a)*d*.7;j?ctx.lineTo(px,py):ctx.moveTo(px,py);}
            ctx.strokeStyle='#ffca28';ctx.lineWidth=3;ctx.stroke();
            ctx.strokeStyle='#fff6c8';ctx.lineWidth=1;ctx.stroke();
          }
        }
        ctx.restore();
      }
      if(b.bomb&&b.age<b.blastAt){const u=Math.max(0,Math.min(1,(b.age-b.throwAt)/b.spec.bombFlight)),point=bombPoint(b,u),burn=Math.max(0,(b.age-b.landAt)/b.spec.fuse);
        ctx.save();ctx.strokeStyle=burn>0?'#fff0aa':'#e8ad55';ctx.lineWidth=burn>0?4:2;ctx.globalAlpha=.7;ctx.beginPath();ctx.ellipse(b.center.x,b.center.y,26+6*burn,11+3*burn,0,0,Math.PI*2);ctx.stroke();
        if(u<1){ctx.globalAlpha=.85;ctx.strokeStyle='#ffb33e';ctx.lineWidth=5;ctx.beginPath();for(let i=0;i<=6;i++){const p=bombPoint(b,Math.max(0,u-.22+i*.22/6));i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y);}ctx.stroke();ctx.strokeStyle='#fff0b4';ctx.lineWidth=2;ctx.stroke();}ctx.restore();
        bomb(ctx,point.x,point.y,2.1,Math.sin(u*Math.PI*2)*.22,burn);
      }
      if(b.exploded&&b.age<b.blastAt+b.spec.aftermath){
        const v=blastVisual(b),r=b.radius,x=b.center.x,y=b.center.y;
        ctx.save();ctx.globalAlpha=(1-v.u)*.72;ctx.strokeStyle='#ffcf70';ctx.lineWidth=13*(1-v.u)+3;ctx.beginPath();ctx.arc(x,y,r*v.front,0,Math.PI*2);ctx.stroke();
        if(v.age>.09){ctx.globalAlpha=(1-v.u)*.55;ctx.strokeStyle='#fff0b4';ctx.lineWidth=5*(1-v.u)+1;ctx.beginPath();ctx.arc(x,y,r*Math.min(1,(v.age-.09)/.42),0,Math.PI*2);ctx.stroke();}
        for(let i=0;i<(v.detail?14:8);i++){const a=i*2.39996,t=Math.min(1,v.age/.98),d=r*(.45+.4*(i%3)/2)*t,px=x+Math.cos(a)*d,py=y+Math.sin(a)*d*.7-Math.sin(t*Math.PI)*r*.3,size=3+(i%3)*2;ctx.globalAlpha=(1-v.u)*.85;ctx.fillStyle=i%2?'#513426':'#e99534';ctx.fillRect(px-size/2,py-size/2,size,size);}
        if(v.age<.13){const flash=1-v.age/.13;ctx.globalAlpha=flash*.9;ctx.fillStyle='#ff9e3c';ctx.beginPath();ctx.arc(x,y,r*(.16+.2*(1-flash)),0,Math.PI*2);ctx.fill();ctx.fillStyle='#fff0c1';ctx.beginPath();ctx.arc(x,y,r*(.08+.06*(1-flash)),0,Math.PI*2);ctx.fill();}ctx.restore();
      }
    }
  }
  function statusFor(a,m){const s=states.get(a),b=s?.cast,cd=profile(a,m).cd,remaining=s?.cooldown||0;return {label:b&&legal(b)&&b.age<b.duration?(b.age<b.full?'展影':!b.bomb?(b.conductAt!==null?'影線導電':'捕縛 '+b.bound.size):b.age<b.landAt?'投彈':b.age<b.blastAt?'引爆中':b.age<b.blastAt+b.spec.aftermath?'終局爆破':'收勢'):remaining>0?'大捕縛 '+Math.ceil(remaining)+'s':'大捕縛待命',fraction:1-Math.min(1,remaining/cd)};}
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
  G.NarutoShikamaruMass={profile,cast,canCast,update,clear,held,statusFor,poseFor,rayVisualFor,shockPoint,stateFor:a=>states.get(a),get casts(){return casts;},get leases(){return leases;}};
})();
