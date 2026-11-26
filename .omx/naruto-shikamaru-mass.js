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
  const massGrain=new Float32Array(1024);
  for(let i=0;i<massGrain.length;i++){const v=Math.sin(i*127.1+311.7)*43758.5453;massGrain[i]=v-Math.floor(v);}
  const mgrain=i=>massGrain[(i&1023)];
  const mpx=v=>Math.round(v*.5)*2;
  const clamp01=v=>Math.max(0,Math.min(1,v));
  function rayVisualFor(b,ray){
    const since=ray.hit?Math.max(0,b.age-ray.boundAt):0,punch=ray.hit?Math.max(0,1-since/.16):1;
    return {width:1.4+2.6*punch,head:12+22*punch,impact:ray.hit?Math.max(0,1-since/.14):0};
  }
  function shockPoint(ray,packet){const u=packet.progress;return {x:ray.source.x+(ray.bodyPoint.x-ray.source.x)*u,y:ray.source.y+(ray.bodyPoint.y-ray.source.y)*u,z:ray.bodyPoint.z*u};}
  function blastVisual(b){const age=Math.max(0,b.age-b.blastAt);return {age,u:Math.min(1,age/b.spec.aftermath),front:1-(1-Math.min(1,age/.24))**3,heat:Math.max(0,1-age/1.05),detail:(G.Settings?.fx??1)>0};}
  function mPixelCloud(ctx,cx,cy,rx,ry,color){
    const x=mpx(cx),y=mpx(cy),w=Math.max(4,mpx(rx)),h=Math.max(4,mpx(ry));
    const h1=Math.max(2,mpx(h*.44)),h2=Math.max(h1,mpx(h*.78)),w1=Math.max(2,mpx(w*.84)),w2=Math.max(2,mpx(w*.56));
    ctx.fillStyle=color;
    ctx.fillRect(x-w,y-h1,w*2,h1*2);
    if(h2>h1){ctx.fillRect(x-w1,y-h2,w1*2,h2-h1);ctx.fillRect(x-w1,y+h1,w1*2,h2-h1);}
    if(h>h2){ctx.fillRect(x-w2,y-h,w2*2,h-h2);ctx.fillRect(x-w2,y+h2,w2*2,h-h2);}
  }
  function drawBlastBack(ctx,b,v){
    const r=b.radius,x=b.center.x,y=b.center.y,growth=1-Math.pow(1-Math.min(1,v.age/.16),3),detail=v.detail;
    const seed=Math.abs(Math.round(x*11+y*23))&511;
    ctx.save();
    // Billowing pixel smoke plumes behind & around the explosion
    const smokeN=detail?14:7;
    if(v.u>.08){
      ctx.globalAlpha=Math.sin(Math.PI*v.u)*.48;
      for(let i=0;i<smokeN;i++){
        const g1=mgrain(seed+i*7),g2=mgrain(seed+i*13+40),a=i*2.39996+g1*.4;
        const d=r*(.18+.56*g2)*Math.pow(v.u,.52),lift=r*(.06+.3*v.u)*(.6+.7*g1);
        const sz=r*(.09+.05*g2)*(.8+.35*v.u);
        mPixelCloud(ctx,x+Math.cos(a)*d,y+Math.sin(a)*d*.58-lift,sz,sz*.76,'#332624');
      }
    }
    if(v.heat>0){
      const palette=['#661b16','#c9381c','#f58020','#ffd861'];
      const baseCount=detail?16:9;
      for(let layer=0;layer<4;layer++){
        const ratio=1-layer*.2;ctx.globalAlpha=v.heat*(layer>=2?.92:.84);
        const n=Math.max(4,Math.round(baseCount*(1-layer*.16)));
        for(let i=0;i<n;i++){
          const g1=mgrain(seed+layer*29+i*11),g2=mgrain(seed+layer*19+i*17),a=i*2.39996+layer*.34;
          const d=r*(.04+.46*g1)*ratio*growth,lift=r*(.06+.32*g2)*(1-layer*.1)*Math.sin(Math.PI*Math.min(1,v.u*1.45));
          const w=r*(.13+.05*g2)*ratio*(.55+.45*v.heat)*growth;
          mPixelCloud(ctx,x+Math.cos(a)*d,y+Math.sin(a)*d*.55-lift,w,w*.84,palette[layer]);
        }
      }
      // Rising central pixel-art flame column
      const colH=r*(.44+.22*v.heat)*growth,steps=7;
      for(let s=0;s<steps;s++){
        const t=s/(steps-1),cw=r*.16*growth*(1-t*.68)*(.6+.4*v.heat);
        ctx.globalAlpha=v.heat*(.9-.1*t);
        mPixelCloud(ctx,x+Math.sin(t*4+v.u*9)*4,y-colH*t,cw,cw*1.05,s<2?'#fff0a6':s<4?'#ffd861':s<6?'#f58020':'#c9381c');
      }
    }
    ctx.restore();
  }
  function ground(ctx){
    for(const b of casts){if(!legal(b))continue;
      const fade=b.age>b.releaseAt?Math.max(0,1-(b.age-b.releaseAt)/.35):1;
      ctx.save();ctx.globalAlpha=fade;
      // Faint, soft-edged radius hint + subtle Nara tactical perimeter ticks so the 32s field feels intentional without hiding ground hazards.
      const r=b.radius,g=ctx.createRadialGradient(b.center.x,b.center.y,0,b.center.x,b.center.y,r);
      g.addColorStop(0,'rgba(16,12,24,.03)');g.addColorStop(.82,'rgba(16,12,24,.055)');g.addColorStop(1,'rgba(16,12,24,0)');
      ctx.fillStyle=g;ctx.beginPath();ctx.arc(b.center.x,b.center.y,r,0,Math.PI*2);ctx.fill();
      if(b.age<b.releaseAt){
        const expand=clamp01(b.age/Math.max(.12,b.full)),pr=r*expand;
        ctx.strokeStyle='#181224';ctx.lineWidth=1.4;ctx.globalAlpha=fade*.26;
        for(let i=0;i<16;i++){const a=i*Math.PI/8+b.age*.06;ctx.beginPath();ctx.arc(b.center.x,b.center.y,pr,a,a+.14);ctx.stroke();}
        if(b.conductAt!==null&&!b.exploded){
          const pulse=.5+.5*Math.sin(b.age*16);
          ctx.strokeStyle='#ffd43b';ctx.lineWidth=1.5;ctx.globalAlpha=fade*(.28+.24*pulse);
          ctx.beginPath();ctx.ellipse(b.owner.x,b.owner.y+1,22+3*pulse,12+2*pulse,0,0,Math.PI*2);ctx.stroke();
        }
      }
      // Subtle ground-skimming shadow tracks under active binding spears so rays feel anchored to the earth.
      if(b.age<b.releaseAt&&b.rays.size){
        ctx.fillStyle='#08060e';ctx.globalAlpha=fade*.38;ctx.beginPath();
        for(const ray of b.rays.values()){
          if(!alive(ray.target)||!ray.linked||ray.travelled<=8)continue;
          const s=ray.source,gx=ray.hit?ray.target.x:ray.current.x,gy=ray.hit?ray.target.y:ray.current.y;
          const dx=gx-s.x,dy=gy-s.y,d=Math.hypot(dx,dy)||1,nx=-dy/d,ny=dx/d,startOff=Math.min(14,d*.22);
          const ax=s.x+dx/d*startOff,ay=s.y+dy/d*startOff;
          ctx.moveTo(ax+nx*3.2,ay+ny*3.2);ctx.lineTo(gx+nx*1.1,gy+ny*1.1);ctx.lineTo(gx-nx*1.1,gy-ny*1.1);ctx.lineTo(ax-nx*3.2,ay-ny*3.2);ctx.closePath();
        }
        ctx.fill();
      }
      // Jagged shadow talons locking each bound enemy's feet instead of flat geometric wire ovals.
      if(b.bound.size){
        ctx.fillStyle='#050408';ctx.globalAlpha=fade*.92;
        for(const e of b.bound){
          const er=Math.max(9,Math.min(22,e.r||12)),ex=e.x,ey=e.y;
          ctx.beginPath();ctx.ellipse(ex,ey+1,er+3,Math.max(4,er*.36),0,0,Math.PI*2);ctx.fill();
          for(let i=0;i<4;i++){
            const side=i<2?-1:1,inner=i%2===0,bx=ex+side*(inner?er*.46:er*.92),by=ey+(inner?2.5:0),h=inner?8.5:11.5;
            ctx.beginPath();ctx.moveTo(bx-2.2,by);ctx.lineTo(bx-side*3.2,by-h);ctx.lineTo(bx+2.2,by);ctx.closePath();ctx.fill();
          }
        }
      }
      if(b.exploded&&b.age<b.blastAt+b.spec.aftermath){
        const v=blastVisual(b),cr=b.radius*v.front,seed=Math.abs(Math.round(b.center.x*7+b.center.y*13))&511;
        ctx.globalAlpha=(1-v.u)*.5;ctx.fillStyle='#1f1411';ctx.beginPath();ctx.ellipse(b.center.x,b.center.y,cr*.64,cr*.38,0,0,Math.PI*2);ctx.fill();
        ctx.strokeStyle='#4a281c';ctx.lineWidth=2.2;
        for(let i=0;i<(v.detail?12:7);i++){
          const a=i*2.39996,d=cr*(.46+.28*mgrain(seed+i));
          ctx.beginPath();ctx.moveTo(mpx(b.center.x+Math.cos(a)*cr*.1),mpx(b.center.y+Math.sin(a)*cr*.08));
          ctx.lineTo(mpx(b.center.x+Math.cos(a+.09)*d*.54),mpx(b.center.y+Math.sin(a+.09)*d*.36));
          ctx.lineTo(mpx(b.center.x+Math.cos(a)*d),mpx(b.center.y+Math.sin(a)*d*.66));ctx.stroke();
        }
        drawBlastBack(ctx,b,v);
      }
      ctx.restore();
    }
  }
  function bomb(ctx,x,y,scale=1,spin=0,burn=0){
    // Nara tactical multi-tag explosive bundle (replaces the oversized cartoon cannonball bomb).
    ctx.save();ctx.translate(x,y);ctx.rotate(spin);ctx.scale(scale*.62,scale*.62);
    // Dark iron cylinder / kunai-core bundle with rope lashing
    ctx.fillStyle='#1f1c26';ctx.strokeStyle='#4b4357';ctx.lineWidth=1.5;
    ctx.fillRect(-7,-9,14,18);ctx.strokeRect(-7,-9,14,18);
    ctx.fillStyle='#8c6b43';ctx.fillRect(-8,-3,16,2.5);ctx.fillRect(-8,2,16,2.5);
    // Twin fluttering explosive talismans wrapped around the bundle
    for(const [ox,oy,ang]of [[-5,3,-.22],[4,4,.24]]){
      ctx.save();ctx.translate(ox,oy);ctx.rotate(ang+Math.sin(burn*10)*.08);
      ctx.fillStyle='#4a251d';ctx.fillRect(-5,-8,10,19);
      ctx.fillStyle=burn>.4?'#fff5d1':'#f5e4ba';ctx.fillRect(-4,-7,8,17);
      ctx.fillStyle=burn>.3?'#e33b26':'#a82922';ctx.fillRect(-1,-5,2,13);ctx.fillRect(-3,-2,6,2);ctx.fillRect(-3,3,6,2);
      ctx.restore();
    }
    // Iron kunai point & burning fuse sparkler
    ctx.fillStyle='#cfd6de';ctx.strokeStyle='#1d1824';ctx.lineWidth=1.2;
    ctx.beginPath();ctx.moveTo(0,-19);ctx.lineTo(-4.5,-9);ctx.lineTo(4.5,-9);ctx.closePath();ctx.fill();ctx.stroke();
    ctx.strokeStyle='#e0ad58';ctx.lineWidth=1.8;ctx.beginPath();ctx.moveTo(3,-9);ctx.quadraticCurveTo(8,-15,12,-13);ctx.stroke();
    const glow=4+3*burn;
    ctx.fillStyle='#ff7b24';ctx.fillRect(10,-15,glow,glow);
    ctx.fillStyle='#fff8cf';ctx.fillRect(11,-14,Math.max(2,glow-2),Math.max(2,glow-2));
    for(let i=0;i<4;i++){
      const a=i*1.57+burn*6,d=5+4*burn;
      ctx.fillStyle=i%2?'#ffe680':'#ff8826';ctx.fillRect(Math.round(12+Math.cos(a)*d),Math.round(-13+Math.sin(a)*d),2,2);
    }
    ctx.restore();
  }
  function bombPoint(b,u){const s=b.bomb.source,side=Math.cos(b.bomb.aim)<-.25?-1:1;return {x:s.x+(b.center.x-s.x)*u+Math.sin(Math.PI*u)*24*side,y:s.y+(b.center.y-s.y)*u-Math.sin(Math.PI*u)*84};}
  function air(ctx){
    const detail=(G.Settings?.fx??1)>0;
    for(const b of casts){if(!legal(b))continue;
      if(b.age<b.releaseAt){
        ctx.save();
        const impacts=[],shocks=[],events=[];
        // 1. Tapered piercing shadow lances: during core detonation glare, start outside the fireball heart so dark wires never cross over the flame column.
        const blastGlare=b.exploded?Math.max(0,1-(b.age-b.blastAt)/.75):0;
        ctx.fillStyle='#050408';ctx.globalAlpha=1-.38*blastGlare;ctx.beginPath();
        for(const ray of b.rays.values()){
          if(!alive(ray.target)||!ray.linked||ray.travelled<=0)continue;
          const s=ray.source,tx=ray.current.x,ty=ray.current.y-ray.current.z,dx=tx-s.x,dy=ty-s.y,d=Math.hypot(dx,dy)||1,inv=1/d,ux=dx*inv,uy=dy*inv,nx=-uy,ny=ux;
          const v=rayVisualFor(b,ray),rim=Math.min(d*.72,Math.max(12,blastGlare*b.radius*.44)),sx=s.x+ux*rim,sy=s.y+uy*rim;
          const neck=Math.max(rim+2,d-v.head),rootW=Math.max(1.6,v.width*.85*(1-.4*blastGlare)),midW=Math.max(1,v.width*.52),headW=v.width*1.15;
          const px=s.x+ux*neck,py=s.y+uy*neck;
          ctx.moveTo(sx+nx*rootW,sy+ny*rootW);ctx.lineTo(px+nx*midW,py+ny*midW);ctx.lineTo(px+nx*headW,py+ny*headW);
          ctx.lineTo(tx,ty);
          ctx.lineTo(px-nx*headW,py-ny*headW);ctx.lineTo(px-nx*midW,py-ny*midW);ctx.lineTo(sx-nx*rootW,sy-ny*rootW);ctx.closePath();
          if(v.impact&&ray.contact)impacts.push({ray,ux,uy,nx,ny,impact:v.impact});
          if(b.bound.has(ray.target)){
            for(const packet of ray.shocks)if(!packet.done&&packet.progress>0)shocks.push({ray,packet,ux,uy,nx,ny});
          }
          const event=ray.shockEvents.at(-1);if(event&&b.age-event.at<.22)events.push({ray,event});
        }
        ctx.fill();ctx.globalAlpha=1;
        if(impacts.length){
          for(const it of impacts){
            const x=it.ray.contact.x,y=it.ray.contact.y-it.ray.contact.z,span=9+7*it.impact;
            ctx.globalAlpha=it.impact;ctx.strokeStyle='#140e1f';ctx.lineWidth=3;
            ctx.beginPath();for(const sign of [-1,1]){ctx.moveTo(x+it.nx*3*sign,y+it.ny*3*sign);ctx.lineTo(x+it.nx*span*sign-it.ux*5,y+it.ny*span*sign-it.uy*5);}ctx.stroke();
            ctx.strokeStyle='#f2dec0';ctx.lineWidth=1.3;ctx.stroke();
          }
          ctx.globalAlpha=1;
        }
        // 2. Jagged golden chakra lightning arcs with branching forks & pixel sparks (replaces uniform sawtooth zigzags).
        if(shocks.length){
          ctx.lineJoin='bevel';ctx.lineCap='round';
          const mainPaths=[],forkPaths=[],sparkPts=[];
          const sparkBudget=detail?Math.max(1,Math.min(3,Math.floor(36/shocks.length))):0;
          for(const item of shocks){
            const s=item.ray.source,body=item.ray.bodyPoint,bx=body.x-s.x,by=body.y-body.z-s.y,l=Math.hypot(bx,by)||1;
            const minU=Math.min(.32,20/l),prog=Math.max(minU+.02,item.packet.progress),span=Math.min(.28,42/l),start=Math.max(minU,prog-span);
            if(prog<=start+.005)continue;
            const seed=((item.ray.target.id||1)*37+item.packet.pulse*19+Math.floor(b.age*24)*7)&511;
            const pts=[];const knots=6;
            for(let j=0;j<=knots;j++){
              const t=j/knots,u=start+(prog-start)*t;
              // Radial amplitude scales cleanly with distance u so bolts fan out sharply from Shikamaru instead of tangling at the center.
              const radialScale=clamp01((u*l-16)/42);
              const env=Math.sin(Math.PI*t)*radialScale,jag=j&&j<knots?(mgrain(seed+j*5)*2-1)*6.5*env+(j%2?1:-1)*2.6*env:0;
              pts.push({x:s.x+bx*u+item.nx*jag,y:s.y+by*u+item.ny*jag});
            }
            mainPaths.push(pts);
            if(detail&&pts.length>4){
              const mid=pts[3],fSign=mgrain(seed+31)>.5?1:-1,fLen=7+6*mgrain(seed+43);
              forkPaths.push([mid,{x:mid.x+item.ux*fLen*.6+item.nx*fSign*fLen*.7,y:mid.y+item.uy*fLen*.6+item.ny*fSign*fLen*.7},{x:mid.x+item.ux*fLen*1.1+item.nx*fSign*fLen*1.05,y:mid.y+item.uy*fLen*1.1+item.ny*fSign*fLen*1.05}]);
            }
            for(let k=0;k<sparkBudget;k++){
              const sp=pts[Math.min(pts.length-1,2+k*2)];
              sparkPts.push({x:mpx(sp.x+(mgrain(seed+70+k)*2-1)*5),y:mpx(sp.y+(mgrain(seed+90+k)*2-1)*5),bright:k===0});
            }
          }
          // Outer warm amber aura
          ctx.globalAlpha=.55;ctx.strokeStyle='#f59e0b';ctx.lineWidth=5.2;ctx.beginPath();
          for(const pts of mainPaths)pts.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));
          ctx.stroke();
          // Mid gold bolt + forks
          ctx.globalAlpha=.95;ctx.strokeStyle='#ffd43b';ctx.lineWidth=2.6;ctx.beginPath();
          for(const pts of mainPaths)pts.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));
          for(const f of forkPaths)f.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));
          ctx.stroke();
          // Crisp white-hot core
          ctx.strokeStyle='#fffbeb';ctx.lineWidth=1.2;ctx.beginPath();
          for(const pts of mainPaths)pts.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));
          ctx.stroke();
          for(const sp of sparkPts){ctx.fillStyle=sp.bright?'#fffbeb':'#ffd43b';ctx.fillRect(sp.x,sp.y,2,2);}
        }
        // 3. Body-wrapping electric crackle arcs on shock arrival.
        if(events.length){
          for(const it of events){
            const u=clamp01((b.age-it.event.at)/.22),x=it.event.point.x,y=it.event.point.y-it.event.point.z,r=(it.ray.target.r||12)+5;
            const seed=((it.ray.target.id||1)*23+it.event.pulse*13)&511;
            ctx.globalAlpha=1-u;
            for(let arcIdx=0;arcIdx<3;arcIdx++){
              const baseA=arcIdx*2.09+u*2.5+mgrain(seed+arcIdx)*1.2;
              ctx.beginPath();
              for(let j=0;j<=4;j++){
                const a=baseA+(j-2)*.38,rad=r*(.75+.45*mgrain(seed+arcIdx*9+j));
                const px=x+Math.cos(a)*rad,py=y+Math.sin(a)*rad*.78;
                j?ctx.lineTo(px,py):ctx.moveTo(px,py);
              }
              ctx.strokeStyle='#ffb703';ctx.lineWidth=3.2*(1-.4*u);ctx.stroke();
              ctx.strokeStyle='#fffbeb';ctx.lineWidth=1.2;ctx.stroke();
            }
            for(let s=0;s<3;s++){
              const a=s*2.1+seed,d=r*(.6+.7*u);
              ctx.fillStyle='#fff7cc';ctx.fillRect(mpx(x+Math.cos(a)*d)-1,mpx(y+Math.sin(a)*d*.7)-1,2,2);
            }
          }
        }
        ctx.restore();
      }
      if(b.bomb&&b.age<b.blastAt){
        const u=clamp01((b.age-b.throwAt)/b.spec.bombFlight),point=bombPoint(b,u),burn=Math.max(0,(b.age-b.landAt)/b.spec.fuse);
        ctx.save();
        // Subtle dashed sealing mark at landing point instead of a thick glowing oval
        ctx.strokeStyle=burn>0?'#ff9e42':'#d99b4e';ctx.lineWidth=1.5+burn*1.2;ctx.globalAlpha=.45+.35*burn;
        for(let i=0;i<6;i++){const a=i*Math.PI/3+burn*.6;ctx.beginPath();ctx.ellipse(b.center.x,b.center.y,20+4*burn,9+2*burn,0,a,a+.34);ctx.stroke();}
        if(u<1){
          // Crisp smoke-and-ember parabolic wake
          for(let i=0;i<7;i++){
            const tu=Math.max(0,u-(i+1)*.032),tp=bombPoint(b,tu),fade=(7-i)/7;
            ctx.globalAlpha=fade*.55;ctx.fillStyle=i<2?'#ffd166':i<4?'#ff7b24':'#cfc5b9';
            const sz=i<3?2:4;ctx.fillRect(mpx(tp.x)-sz/2,mpx(tp.y)-sz/2,sz,sz);
          }
        }
        ctx.restore();
        bomb(ctx,point.x,point.y,1.45,u*Math.PI*3.2,burn);
      }
      if(b.exploded&&b.age<b.blastAt+b.spec.aftermath){
        const v=blastVisual(b),r=b.radius,x=b.center.x,y=b.center.y,seed=Math.abs(Math.round(x*17+y*31))&511;
        ctx.save();
        // Thin razor shockwave arcs marking the real explosion perimeter (replaces the huge 16px opaque yellow hoop!).
        ctx.globalAlpha=(1-v.u)*.68;ctx.strokeStyle='#ffe28a';ctx.lineWidth=2.4*(1-.5*v.u)+.8;
        for(let i=0;i<8;i++){
          const a=i*Math.PI/4+v.u*.22+mgrain(seed+i)*.18,span=.3+.12*(1-v.u);
          ctx.beginPath();ctx.arc(x,y,r*v.front,a,a+span);ctx.stroke();
        }
        if(v.age>.07&&v.age<.65){
          const u2=clamp01((v.age-.07)/.58);ctx.globalAlpha=(1-u2)*.42;ctx.strokeStyle='#fff6cc';ctx.lineWidth=1.4;
          for(let i=0;i<6;i++){const a=i*Math.PI/3-.2;ctx.beginPath();ctx.arc(x,y,r*(.45+.52*u2),a,a+.25);ctx.stroke();}
        }
        // Flying pixel embers, scorched debris, and burning paper-tag fragments
        const count=v.detail?26:12;
        for(let i=0;i<count;i++){
          const g1=mgrain(seed+i*11+80),g2=mgrain(seed+i*19+150),a=i*2.39996+(g1-.5)*.35;
          const t=Math.min(1,v.age/(.85+.3*g2)),d=r*(.22+.76*g1)*Math.pow(t,.65),pyLift=Math.sin(t*Math.PI)*r*(.12+.22*g2);
          const px=mpx(x+Math.cos(a)*d),py=mpx(y+Math.sin(a)*d*.68-pyLift);
          ctx.globalAlpha=(1-v.u)*.92;
          if(i%5===0){
            ctx.fillStyle='#4a251d';ctx.fillRect(px-2,py-2,4,6);
            ctx.fillStyle='#ff8c29';ctx.fillRect(px-2,py-2,4,2);
          }else{
            const sz=i%3===0?4:2;ctx.fillStyle=i%2?'#fff2ad':'#ff8824';ctx.fillRect(px-sz/2,py-sz/2,sz,sz);
          }
        }
        if(v.age<.16){
          const flash=1-v.age/.16,fr=r*(.13+.1*(1-flash));
          ctx.globalAlpha=flash*.94;
          mPixelCloud(ctx,x,y-4,fr*1.25,fr*.95,'#ffbf47');
          mPixelCloud(ctx,x,y-4,fr*.68,fr*.55,'#fffdf0');
        }
        ctx.restore();
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
