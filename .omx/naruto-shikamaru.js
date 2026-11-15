/* Shikamaru: ground-connected possession, piercing shadows and physical paper traps. */
(() => {
  if(G.NarutoShikamaru)return;
  const C=G.Combat,DEX=30017,EPS=1e-8,states=new Map(),casts=[],leases=new Map(),effects=[];
  const modes=new Set(['shikamaru-shadow','shikamaru-sewing','shikamaru-trap','shikamaru-strangle','shikamaru-tactics']);
  let serial=0;
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const valid=a=>alive(a)&&(a===G.Game.player||!!G.SelfClones?.isActor(a))&&(a.mon?.dex??a.dex)===DEX;
  const rank=m=>Math.max(1,Math.min(5,Math.floor(m?.lvl||1)));
  const learned=(a,id)=>a.moves?.some(m=>m.id===id);
  const supports=m=>modes.has(typeof m==='string'?m:m?.digiMode);
  const strong=e=>!!(e.boss||e.elite||e.legend||e.judge);
  function state(a){let s=states.get(a);if(s&&s.world!==G.World){clear(a);s=null;}if(!s){s={owner:a,world:G.World,clock:0,cooldowns:{},pose:null,casts:{},hits:0,damage:0,bound:0,detonations:0,contacts:[]};states.set(a,s);}return s;}
  function profile(a,m){
    const L=rank(m),Q=Math.max(0,Math.min(16,Math.floor(G.Quantity?.bonus(a)??a.quantityPicks??a.quantityBonus??0)));
    const tactics=a.moves?.find(x=>x.digiMode==='shikamaru-tactics'),T=tactics?rank(tactics):0;
    const kind=(m?.digiMode||'shikamaru-shadow').replace('shikamaru-','');
    return {kind,L,Q,T,range:(m?.range||300)+24*(L-1)+12*Q,
      branches:Math.min(18,2+Q+Math.floor((L-1)/2)+T),pulses:kind==='sewing'?3+L+Math.min(4,Q):kind==='strangle'?2+L:1,
      traps:Math.min(10,1+Q+Math.floor((L-1)/2)),radius:(kind==='trap'?92:kind==='strangle'?70:13)+7*(L-1)+(kind==='trap'?5*Q:0),
      damage:(m?.dmg??(kind==='shadow'?12:kind==='sewing'?17:kind==='trap'?65:35))*(a.atk??1),
      bindDuration:1.25+.23*L+.12*T,cd:Math.max(.2,(m?.cd??(kind==='shadow'?1.5:kind==='sewing'?4:kind==='trap'?5.5:7))*(a.cdMul??1)),
      speed:620+35*L,release:kind==='trap'?.25:.18,interval:kind==='strangle'?.23:.16};
  }
  function clearPath(ax,ay,bx,by,r=1,target=null){
    if(G.World.projectilePathClear)return G.World.projectilePathClear(ax,ay,bx,by,target,{radius:r,spacing:5,includeStart:false});
    const n=Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/5));
    for(let i=1;i<=n;i++){const x=ax+(bx-ax)*i/n,y=ay+(by-ay)*i/n,b=G.World.projectileBlock?.(x,y,r);if(b&&b!==target)return false;if(!G.World.projectileBlock&&G.World.isWall?.(x,y))return false;}return true;
  }
  function targets(a,p){
    const list=[...new Set(G.EnemyMgr.queryCircle(a.x,a.y,p.range))].filter(e=>alive(e)&&!e.friendly&&Math.hypot(e.x-a.x,e.y-a.y)<=p.range+(e.r||0)&&clearPath(a.x,a.y,e.x,e.y)).sort((u,v)=>Number(!!leases.get(v))-Number(!!leases.get(u))||Math.hypot(u.x-a.x,u.y-a.y)-Math.hypot(v.x-a.x,v.y-a.y));
    if(list.length||p.kind!=='shadow')return list;
    return (G.World.propsInCircle?.(a.x,a.y,p.range)||[]).filter(e=>e.destructible&&e.hp>0&&clearPath(a.x,a.y,e.x,e.y,1,e));
  }
  function legal(b){return !b.cancelled&&valid(b.owner)&&b.world===G.World&&states.get(b.owner)===b.state&&learned(b.owner,b.m.id);}
  function held(e){const l=leases.get(e);return !!l&&legal(l.cast)&&alive(e)&&l.until>l.cast.state.clock&&clearPath(l.cast.owner.x,l.cast.owner.y,e.x,e.y);}
  const stopped=e=>held(e)&&!strong(e);
  function canCast(a,m){if(!valid(a)||a.frozen||!supports(m)||m.digiMode==='shikamaru-tactics')return false;const s=state(a),p=profile(a,m);if((s.cooldowns[m.id]||0)>EPS)return false;const t=targets(a,p);return p.kind==='strangle'?t.some(e=>held(e)&&leases.get(e)?.cast.owner===a):t.length>0;}
  function cast(a,m){
    if(!canCast(a,m))return false;
    const s=state(a),p=profile(a,m),t=targets(a,p).filter(e=>p.kind!=='strangle'||held(e)&&leases.get(e)?.cast.owner===a);
    const count=p.kind==='trap'?p.traps:p.branches;
    const b={serial:++serial,owner:a,state:s,world:G.World,m:{...m},spec:p,kind:p.kind,age:0,duration:p.kind==='trap'?1.3:p.release+(p.pulses-1)*p.interval+p.range/p.speed+.4,
      aim:Math.atan2(t[0].y-a.y,t[0].x-a.x),origin:{x:a.x,y:a.y},rays:[],traps:[],emitted:0,cancelled:false,hits:0};
    for(let i=0;i<count;i++){
      const e=t[i%t.length],spread=i>=t.length?(i-t.length+1)*.22:0;
      const angle=Math.atan2(e.y-a.y,e.x-a.x)+spread,dist=Math.min(p.range,Math.hypot(e.x-a.x,e.y-a.y)+30);
      b.rays.push({x:a.x+Math.cos(angle)*dist,y:a.y+Math.sin(angle)*dist,target:e});
      if(p.kind==='trap'){
        const offset=i>=t.length?40*Math.ceil((i+1)/t.length):0;
        const x=e.x+Math.cos(i*2.4)*offset,y=e.y+Math.sin(i*2.4)*offset;
        if(clearPath(a.x,a.y,x,y))b.traps.push({x,y,age:0,detonated:false});
      }
    }
    s.cooldowns[m.id]=p.cd;m.t=p.cd;s.casts[p.kind]=(s.casts[p.kind]||0)+1;s.pose=b;casts.push(b);a.aim=b.aim;
    return true;
  }
  function bind(b,e){if(!legal(b)||!alive(e))return;const old=leases.get(e),until=b.state.clock+b.spec.bindDuration;
    if(!old||old.until<until){leases.set(e,{cast:b,until,x:e.x,y:e.y});b.state.bound++;}}
  function hit(b,e,scale=1){
    if(!legal(b)||!alive(e))return false;
    const mult=G.Types?.mult?.(b.m.type||'dark',e.types)??1,crit=Math.random()<(b.owner.critChance||0);
    const damage=b.spec.damage*scale*mult*(G.Weather?.mult?.(b.m.type||'dark')??1)*(crit?1.5:1);
    e.hurt(damage,b.kind==='trap'?'#ffc27b':'#bca6db',0,0,0,crit?'crit':G.Types?.label?.(mult),b.owner,b.m.id);
    if(!legal(b))return false;
    b.owner.onDealt?.(damage);if(!legal(b))return false;
    b.owner.dmgDealt=(b.owner.dmgDealt||0)+damage;b.state.hits++;b.state.damage+=damage;b.hits++;
    if(b.state.contacts.length<120)b.state.contacts.push({cast:b.serial,mode:b.kind,pulse:b.emitted,x:e.x,y:e.y,damage});
    G.DamageSplash?.hit?.(b.owner,e,damage,b.kind==='trap'?'#ffc27b':'#bca6db',b.m.id);
    return legal(b);
  }
  function segmentDistance(x,y,ax,ay,bx,by){const dx=bx-ax,dy=by-ay,t=Math.max(0,Math.min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy||1)));return Math.hypot(x-ax-t*dx,y-ay-t*dy);}
  function pulse(b,index,current){
    const p=b.spec,owner=b.owner,seen=b.hitSets[index]??(b.hitSets[index]=new Set());
    // A persistent ground band can catch enemies entering its grown section.
    // Its tip uses only the current sim age; never predict a future endpoint.
    const ax=owner.x,ay=owner.y;
    for(const ray of b.rays){
      if(!legal(b))return;
      if(b.kind==='strangle'){
        const e=ray.target;
        if(!alive(e)||!held(e)||leases.get(e)?.cast.owner!==owner||Math.hypot(e.x-ax,e.y-ay)>p.range||!clearPath(ax,ay,e.x,e.y))continue;
        ray.source={x:ax,y:ay};ray.tip={x:e.x,y:e.y};
        if(current<.08||seen.has(e))continue;
        seen.add(e);b.emitted=index+1;if(!hit(b,e))return;
        effects.push({owner,world:b.world,kind:'strangle',x:e.x,y:e.y,bodyH:e.bodyH||Math.max(18,(e.r||12)*2),age:0,life:.43,radius:(e.r||12)+5});
        continue;
      }
      const d=Math.hypot(ray.x-ax,ray.y-ay),wanted=Math.min(d,p.range,current*p.speed),dx=d?(ray.x-ax)/d:0,dy=d?(ray.y-ay)/d:0;
      let reach=0;
      for(let distance=0;distance<=wanted;distance+=4){
        const x=ax+dx*distance,y=ay+dy*distance;
        if(G.World.projectileBlock?.(x,y,1)||(!G.World.projectileBlock&&G.World.isWall?.(x,y)))break;
        reach=distance;
      }
      const bx=ax+dx*reach,by=ay+dy*reach;
      ray.tip={x:bx,y:by};ray.source={x:ax,y:ay};
      const mx=(ax+bx)/2,my=(ay+by)/2,r=reach/2+p.radius+40;
      for(const e of new Set(G.EnemyMgr.queryCircle(mx,my,r))){
        if(!legal(b))return;
        if(!alive(e)||e.friendly||seen.has(e)||segmentDistance(e.x,e.y,ax,ay,bx,by)>p.radius+(e.r||0)||!clearPath(ax,ay,e.x,e.y))continue;
        if(b.kind==='strangle'&&(!held(e)||leases.get(e)?.cast.owner!==owner))continue;
        seen.add(e);b.emitted=index+1;
        if(!hit(b,e))return;
        if(b.kind==='shadow'||b.kind==='sewing')bind(b,e);
        effects.push({owner,world:b.world,kind:b.kind,x:e.x,y:e.y,age:0,life:b.kind==='sewing'?.36:.25,radius:p.radius+8});
      }
      for(const prop of G.World.propsInCircle?.(mx,my,r)||[]){
        if(!legal(b))return;
        if(!prop.destructible||prop.hp<=0||seen.has(prop)||segmentDistance(prop.x,prop.y,ax,ay,bx,by)>p.radius+(prop.r||0)||!clearPath(ax,ay,prop.x,prop.y,1,prop))continue;
        seen.add(prop);G.World.damageProp?.(prop,p.damage,'#bca6db');
      }
    }
  }
  function detonate(b,t){
    if(t.detonated||!legal(b))return;t.detonated=true;b.state.detonations++;
    effects.push({owner:b.owner,world:b.world,kind:'explosion',x:t.x,y:t.y,age:0,life:.5,radius:b.spec.radius});
    for(const e of new Set(G.EnemyMgr.queryCircle(t.x,t.y,b.spec.radius+40))){
      if(!legal(b))return;if(!alive(e)||e.friendly||Math.hypot(e.x-t.x,e.y-t.y)>b.spec.radius+(e.r||0)||!clearPath(t.x,t.y,e.x,e.y))continue;
      if(!hit(b,e,held(e)&&leases.get(e)?.cast.owner===b.owner?1.5:1))return;
    }
    for(const prop of G.World.propsInCircle?.(t.x,t.y,b.spec.radius)||[]){if(!legal(b))return;if(prop.destructible&&prop.hp>0&&Math.hypot(prop.x-t.x,prop.y-t.y)<=b.spec.radius+(prop.r||0)&&clearPath(t.x,t.y,prop.x,prop.y,1,prop))G.World.damageProp?.(prop,b.spec.damage,'#ffc27b');}
  }
  function clear(owner){
    for(const b of casts)if(!owner||b.owner===owner)b.cancelled=true;
    for(const [e,l]of leases)if(!owner||l.cast.owner===owner)leases.delete(e);
    for(let i=casts.length-1;i>=0;i--)if(!owner||casts[i].owner===owner)casts.splice(i,1);
    for(let i=effects.length-1;i>=0;i--)if(!owner||effects[i].owner===owner)effects.splice(i,1);
    if(owner)states.delete(owner);else states.clear();
  }
  function update(dt){
    if(G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    for(const [a,s]of states){if(!valid(a)||s.world!==G.World){clear(a);continue;}s.clock+=dt;if(s.pose&&s.pose.age>=.65)s.pose=null;}
    for(const [e,l]of leases)if(!held(e))leases.delete(e);
    for(const b of casts.slice()){
      if(!legal(b)){b.cancelled=true;const i=casts.indexOf(b);if(i>=0)casts.splice(i,1);continue;}
      b.age+=dt;
      if(b.kind==='trap')for(const t of b.traps){t.age=b.age;if(b.age>=.9)detonate(b,t);}
      else{b.hitSets??=[];for(let i=0;i<b.spec.pulses;i++){const start=b.spec.release+i*b.spec.interval;if(b.age<start)break;pulse(b,i,Math.max(0,b.age-start));}}
      if(b.age>=b.duration){const i=casts.indexOf(b);if(i>=0)casts.splice(i,1);}
    }
    for(let i=effects.length-1;i>=0;i--){const e=effects[i];e.age+=dt;if(e.age>=e.life||e.world!==G.World||!valid(e.owner))effects.splice(i,1);}
  }
  function tick(dt,a,now){
    if((a?.mon?.dex??a?.dex)!==DEX)return oldTick.call(this,dt,a,now);
    if(G.Game.state!=='playing'||!valid(a)||a.frozen||!Number.isFinite(dt)||dt<=0)return;
    const s=state(a);
    for(const m of a.moves||[]){if(!supports(m))continue;s.cooldowns[m.id]=Math.max(0,(s.cooldowns[m.id]||0)-dt);m.t=s.cooldowns[m.id];}
    // Traps are laid before captures; their fuse leaves a possession window.
    for(const kind of ['shadow','sewing','trap','strangle']){const m=a.moves?.find(m=>m.digiMode==='shikamaru-'+kind);if(m&&canCast(a,m)){a.cast?.(m);cast(a,m);m.castAt=performance.now();}}
  }
  function drawGround(ctx){
    for(const b of casts){if(!legal(b))continue;const p=b.spec;
      ctx.save();ctx.lineCap='round';ctx.lineJoin='round';
      if(b.kind==='trap')for(const t of b.traps){if(t.detonated||b.age<.55)continue;ctx.save();ctx.translate(t.x,t.y);ctx.rotate(.22);ctx.fillStyle='#e9d6a1';ctx.fillRect(-6,-10,12,20);ctx.strokeStyle='#663927';ctx.lineWidth=2;ctx.strokeRect(-6,-10,12,20);ctx.fillStyle='#613c35';ctx.fillRect(-2,-6,4,11);ctx.fillStyle='#ffb353';ctx.fillRect(3,-12,3,3);ctx.restore();}
      else for(const r of b.rays){if(!r.tip)continue;ctx.strokeStyle='#191723';ctx.lineWidth=b.kind==='strangle'?5:p.radius*2;ctx.beginPath();ctx.moveTo(r.source.x,r.source.y);ctx.lineTo(r.tip.x,r.tip.y);ctx.stroke();ctx.strokeStyle='#665276';ctx.lineWidth=b.kind==='strangle'?1:2;ctx.stroke();}
      ctx.restore();
    }
    for(const [e,l]of leases){if(!held(e))continue;const a=l.cast.owner;ctx.save();ctx.strokeStyle='#24202f';ctx.lineWidth=7;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(e.x,e.y);ctx.stroke();ctx.fillStyle='#201c2a';ctx.beginPath();ctx.ellipse(e.x,e.y,(e.r||12)+8,9,0,0,Math.PI*2);ctx.fill();ctx.restore();}
  }
  function drawAir(ctx){
    for(const b of casts)if(b.kind==='trap'&&legal(b)&&b.age>=b.spec.release&&b.age<.55){
      const u=Math.min(1,(b.age-b.spec.release)/(.55-b.spec.release));
      for(const t of b.traps){ctx.save();ctx.translate(b.origin.x+(t.x-b.origin.x)*u,b.origin.y+(t.y-b.origin.y)*u-24-Math.sin(u*Math.PI)*35);ctx.rotate(b.aim+u*5);ctx.fillStyle='#c8cbd1';ctx.beginPath();ctx.moveTo(12,0);ctx.lineTo(-4,-5);ctx.lineTo(-4,5);ctx.closePath();ctx.fill();ctx.strokeStyle='#3c3544';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(-4,0);ctx.lineTo(-12,0);ctx.stroke();ctx.fillStyle='#ead7a3';ctx.fillRect(-19,-4,8,15);ctx.fillStyle='#763c36';ctx.fillRect(-16,-1,2,8);ctx.restore();}
    }
    for(const e of effects){
      const t=e.age/e.life;ctx.save();ctx.globalAlpha=1-t;
      if(e.kind==='explosion'){
        ctx.fillStyle='#e58b38';for(let i=0;i<9;i++){const a=i*Math.PI*2/9,d=e.radius*t;ctx.beginPath();ctx.arc(e.x+Math.cos(a)*d,e.y+Math.sin(a)*d-12,12*(1-t)+3,0,Math.PI*2);ctx.fill();}
        ctx.strokeStyle='#ffd59b';ctx.lineWidth=4;ctx.beginPath();ctx.ellipse(e.x,e.y,e.radius*t,e.radius*t*.55,0,0,Math.PI*2);ctx.stroke();
      }else if(e.kind==='sewing'){
        const rise=Math.min(1,t*5),sink=Math.max(0,(t-.65)/.35),height=48*rise*(1-sink);
        for(let i=0;i<3;i++){
          const x=e.x+(i-1)*10,y=e.y+Math.abs(i-1)*4,lean=(i-1)*9;
          ctx.fillStyle='#191522';ctx.beginPath();ctx.moveTo(x-6,y);ctx.quadraticCurveTo(x-3,y-height*.55,x+lean,y-height);ctx.quadraticCurveTo(x+8,y-height*.3,x+7,y);ctx.closePath();ctx.fill();
          ctx.strokeStyle='#7c688e';ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(x+4,y-3);ctx.lineTo(x+lean,y-height+5);ctx.stroke();
        }
      }else if(e.kind==='strangle'){
        const rise=Math.min(1,t*3.5),neck=e.y-Math.max(12,e.bodyH*.65)*rise;
        const palmScale=Math.max(.5,Math.min(1.6,e.bodyH/52));
        ctx.strokeStyle='#211b2b';ctx.lineWidth=6*palmScale;ctx.beginPath();ctx.moveTo(e.x-7*palmScale,e.y);ctx.bezierCurveTo(e.x-20*palmScale,e.y-15*palmScale,e.x+20*palmScale,neck+13*palmScale,e.x+2*palmScale,neck);ctx.stroke();
        // The hand grows out of the connected shadow along the body, then closes.
        if(rise>.55){
          ctx.save();ctx.translate(e.x,neck);ctx.scale(palmScale,palmScale);
          const close=Math.min(1,(rise-.55)/.45);ctx.fillStyle='#211b2b';ctx.fillRect(-3,-3,12,10);
          ctx.strokeStyle='#211b2b';ctx.lineWidth=3;ctx.lineCap='round';
          for(let i=0;i<4;i++){const x=-3+i*3;ctx.beginPath();ctx.moveTo(x,1);ctx.quadraticCurveTo(x-7*(1-close),-13,x-8*close,-5+5*close);ctx.stroke();}
          ctx.beginPath();ctx.moveTo(7,5);ctx.lineTo(12-5*close,-2);ctx.stroke();ctx.restore();
        }
      }else{
        ctx.strokeStyle='#35283f';ctx.lineWidth=3;ctx.beginPath();ctx.ellipse(e.x,e.y,12+8*t,6+3*t,0,0,Math.PI*2);ctx.stroke();
      }
      ctx.restore();
    }
  }
  const oldEnemy=G.Enemy?.prototype.update;
  if(oldEnemy)G.Enemy.prototype.update=function(dt,...args){
    if(G.Game.state==='playing'&&held(this)){
      // The native stopped gate handles ordinary AI after status clocks run.
      // Strong enemies retain attacks; only their position is restrained.
      if(!strong(this))return oldEnemy.call(this,dt,...args);
      const x=this.x,y=this.y,result=oldEnemy.call(this,dt,...args);if(held(this)&&alive(this)){this.x=x;this.y=y;}return result;
    }
    return oldEnemy.call(this,dt,...args);
  };
  const oldTick=C.tick,oldUpdate=C.updateFields,oldClear=C.clearFields,oldGround=C.drawGroundFields,oldAir=C.drawAirFields;
  C.tick=tick;C.updateFields=function(dt){const r=oldUpdate.call(this,dt);update(dt);return r;};
  C.clearFields=function(a){clear(a);return oldClear.call(this,a);};
  C.drawGroundFields=function(ctx){oldGround.call(this,ctx);drawGround(ctx);};C.drawAirFields=function(ctx){oldAir.call(this,ctx);drawAir(ctx);};
  G.NarutoShikamaru={version:3,dex:DEX,supports,profile,canCast,cast,update,clear,held,stopped,clearPath,segmentDistance,
    activeFor:a=>{const b=states.get(a)?.pose;return b&&legal(b)&&b.age<.65?{...b,kind:b.kind,age:b.age,duration:.65}:null;},
    stateFor:(a=G.Game.player)=>states.get(a)||null,stats:(a=G.Game.player)=>{const s=states.get(a);return s?{casts:{...s.casts},hits:s.hits,damage:s.damage,bound:s.bound,detonations:s.detonations,contacts:s.contacts.slice()}:null;},
    get casts(){return casts;},get leases(){return leases;},get effects(){return effects;}};
})();
