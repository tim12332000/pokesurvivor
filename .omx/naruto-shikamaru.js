/* Shikamaru: ground-connected possession, piercing shadows and physical paper traps. */
(() => {
  if(G.NarutoShikamaru)return;
  const C=G.Combat,DEX=30017,EPS=1e-8,states=new Map(),casts=[],leases=new Map(),effects=[];
  const Ref=G.ShikamaruReferenceGeometry;
  if(!Ref)throw Error('Shikamaru reference geometry must load before combat');
  const modes=new Set(['shikamaru-shadow','shikamaru-sewing','shikamaru-trap','shikamaru-strangle','shikamaru-tactics','shikamaru-checkmate']);
  let serial=0;
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const valid=a=>alive(a)&&(a===G.Game.player||!!G.SelfClones?.isActor(a))&&(a.mon?.dex??a.dex)===DEX;
  const rank=m=>Math.max(1,Math.min(5,Math.floor(m?.lvl||1)));
  const learned=(a,id)=>a.moves?.some(m=>m.id===id);
  const supports=m=>modes.has(typeof m==='string'?m:m?.digiMode);
  const strong=e=>!!(e.boss||e.elite||e.legend||e.judge);
  function state(a){let s=states.get(a);if(s&&(s.world!==G.World||s.epoch!==G.CombatPulse?.epoch)){clear(a);s=null;}if(!s){s={owner:a,world:G.World,epoch:G.CombatPulse?.epoch,clock:0,material:{clock:0,phase:0},reservoir:{feeds:[],revision:0},cooldowns:{},pose:null,casts:{},hits:0,damage:0,bound:0,detonations:0,contacts:[],board:[],plan:null,walkDistance:0,prevX:a.x,prevY:a.y,moving:false,travelled:0,dragged:0,cycles:0,sewingQueued:false,shadowReturns:[],visibleShadow:null};states.set(a,s);}return s;}
  function profile(a,m){
    const L=rank(m),Q=Math.max(0,Math.min(16,Math.floor(G.Quantity?.bonus(a)??a.quantityPicks??a.quantityBonus??0)));
    const tactics=a.moves?.find(x=>x.digiMode==='shikamaru-tactics'),T=tactics?rank(tactics):0;
    const kind=(m?.digiMode||'shikamaru-shadow').replace('shikamaru-','');
    const ultimate=kind==='checkmate';
    return {kind,L,Q,T,range:(m?.range||300)+24*(L-1)+12*Q,
      shadowWidthMin:(4.5+.65*(L-1))*(a.anim?.scale||1),shadowWidthMax:(14+1.4*(L-1))*(a.anim?.scale||1),
      branches:Math.min(16,L+Q+Math.floor(T/2)),chainTargets:Math.min(16,L+Q+Math.floor(T/2)),chainHops:0,simultaneousRoots:Math.min(16,L+Q+Math.floor(T/2)),chainRange:Math.min(240,((m?.range||300)+24*(L-1)+12*Q)*.75),pulses:ultimate?3+Math.floor((L-1)/2)+Math.min(2,Q):kind==='sewing'?2+Math.floor((L-1)/2)+Math.min(2,Q):kind==='strangle'?2+L:1,
      traps:Math.min(24,3+2*Q+Math.floor((L-1)/2)),radius:(kind==='trap'?108:kind==='strangle'?70:22)+7*(L-1)+(kind==='trap'?8*Q:0),
      damage:(m?.dmg??(kind==='shadow'?12:kind==='sewing'?17:kind==='trap'?65:35))*(a.atk??1),
      bindDuration:1.25+.23*L+.12*T,cd:Math.max(.2,(m?.cd??(kind==='shadow'?1.5:kind==='sewing'?4:kind==='trap'?5.5:7))*(a.cdMul??1)),
      kunaiRounds:3+Math.floor((L-1)/2),kunaiInterval:.13,kunaiSpeed:740,speed:620+35*L,release:ultimate?.3:kind==='trap'?.25:.18,interval:ultimate?.24:kind==='sewing'?.7:kind==='strangle'?.23:.16,archFlight:ultimate?.58:.5,archPrepare:.12,needleWidth:(ultimate?7:5)*(a.anim?.scale||1),blastRadius:145+15*(L-1)+5*Math.min(8,Q),blastScale:3,blastFuse:.2,
      trapLifetime:10,deployDistance:54,trapArm:.55,blastRounds:1+Math.min(3,Q)+Math.floor((L-1)/2),blastInterval:.16,chainInterval:.12,captureWindow:.55,dragTimeout:a.moves?.some(x=>x.digiMode==='shikamaru-trap')?2.4:.9,stopWindow:.25,netPrepare:.28,recoverTime:.35};
  }
  function clearPath(ax,ay,bx,by,r=1,target=null){
    if(G.World.projectilePathClear)return G.World.projectilePathClear(ax,ay,bx,by,target,{radius:r,spacing:5,includeStart:false});
    const n=Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/5));
    for(let i=1;i<=n;i++){const x=ax+(bx-ax)*i/n,y=ay+(by-ay)*i/n,b=G.World.projectileBlock?.(x,y,r);if(b&&b!==target)return false;if(!G.World.projectileBlock&&G.World.isWall?.(x,y))return false;}return true;
  }
  Ref.registerNativePolicy(clearPath);
  function targets(a,p){
    const list=[...new Set(G.EnemyMgr.queryCircle(a.x,a.y,p.range))].filter(e=>alive(e)&&!e.friendly&&Math.hypot(e.x-a.x,e.y-a.y)<=p.range+(e.r||0)&&(held(e)&&leases.get(e)?.cast.owner===a||clearPath(a.x,a.y,e.x,e.y))).sort((u,v)=>Number(held(u))-Number(held(v))||Math.hypot(u.x-a.x,u.y-a.y)-Math.hypot(v.x-a.x,v.y-a.y));
    if(list.length||p.kind!=='shadow')return list;
    return (G.World.propsInCircle?.(a.x,a.y,p.range)||[]).filter(e=>e.destructible&&e.hp>0&&clearPath(a.x,a.y,e.x,e.y,1,e));
  }
  const clamp01=x=>Math.max(0,Math.min(1,x));
  function projectionFor(actor,ownerState=null){
    const caster=valid(actor),s=ownerState||states.get(actor)||leases.get(actor)?.cast.state;
    const current=s&&s.world===G.World&&s.epoch===G.CombatPulse?.epoch;
    if(caster){
      const feeds=current&&s.reservoir?.feeds?.length?s.reservoir.feeds:[];
      const flow={phase:current?s.material.phase:0,seed:DEX*.713,strength:1.35,readyBase:true,feeds,revision:current?s.reservoir?.revision||0:0};
      return Ref.project(actor,0,1,64*(actor.anim?.scale||1),1,clearPath,flow);
    }
    const body=Ref.bodyFor(actor);if(!body)return null;
    const height=body.bodyHeight;
    const dx=-.45,dy=.9,length=height*.92,across=.85;
    const sharedPhase=states.get(G.Game.player)?.material.phase??s?.material.phase??0;
    const stagger=((Number.isFinite(actor.id)?actor.id:0)%6)/60;
    const flow=current&&learned(s.owner,'naruto-shikamaru')?{phase:Math.floor((sharedPhase+stagger)*10)/10,seed:(Number.isFinite(actor.id)?actor.id:actor.dex||DEX)*.713,strength:1}:null;
    return Ref.project(actor,dx,dy,length,across,clearPath,flow);
  }
  function segmentDirection(owner,segment){
    let tx=0,ty=0;
    if(segment.grownPoints?.length>1){
      const sample=segment.grownPoints.find(p=>Math.hypot(p.x-owner.x,p.y-owner.y)>16)||segment.grownPoints.at(-1);
      tx=sample.x-owner.x;ty=sample.y-owner.y;
    }
    if(Math.hypot(tx,ty)<=4&&segment.path?.length>1){
      const start=segment.path[0],sample=segment.path.find(p=>Math.hypot(p.x-start.x,p.y-start.y)>24)||segment.path.at(-1);
      tx=sample.x-start.x;ty=sample.y-start.y;
    }
    if(Math.hypot(tx,ty)<=4&&segment.target){tx=segment.target.x-owner.x;ty=segment.target.y-owner.y;}
    const d=Math.hypot(tx,ty)||1;return {dx:tx/d,dy:ty/d};
  }
  function boundaryJoin(projection,owner,dx,dy){
    const outline=projection?.readyOutline;
    if(!outline||outline.length<3)return {x:owner.x,y:owner.y};
    const hits=[];
    for(let i=0;i<outline.length;i++){
      const a=outline[i],b=outline[(i+1)%outline.length],ex=b.x-a.x,ey=b.y-a.y,det=dy*ex-dx*ey;
      if(Math.abs(det)<1e-9)continue;
      const wx=a.x-owner.x,wy=a.y-owner.y,t=(wy*ex-wx*ey)/det,u=(dx*wy-dy*wx)/det;
      if(t>1e-4&&u>=-1e-5&&u<=1+1e-5)hits.push({t,x:owner.x+dx*t,y:owner.y+dy*t});
    }
    hits.sort((u,v)=>v.t-u.t);
    for(const hit of hits)if(clearPath(owner.x,owner.y,hit.x,hit.y)&&Ref.contains(projection,hit.x,hit.y))return {x:hit.x,y:hit.y};
    if(hits.length){
      let low=0,high=hits[0].t;
      for(let i=0;i<8;i++){const mid=(low+high)/2,px=owner.x+dx*mid,py=owner.y+dy*mid;if(clearPath(owner.x,owner.y,px,py)&&Ref.contains(projection,px,py))low=mid;else high=mid;}
      return {x:owner.x+dx*low,y:owner.y+dy*low};
    }
    return {x:owner.x,y:owner.y};
  }
  function updateReservoir(s){
    const a=s.owner,scale=a.anim?.scale||1,feeds=[];
    if(valid(a)&&moveFor(a,'shadow')){
      const b=s.lastChain;
      if(b&&legal(b)&&(casts.includes(b)||ownedCaptures(s).length)){
        for(const segment of b.chain.segments){
          if(segment.sourceActor||segment.linked===false)continue;
          const activeHold=segment.contact&&alive(segment.target)&&held(segment.target);
          const gathering=b.age<b.spec.release&&casts.includes(b);
          const extending=b.age>=b.spec.release&&!segment.contact&&!segment.finished&&casts.includes(b);
          if(!gathering&&!extending&&!activeHold)continue;
          const {dx,dy}=segmentDirection(a,segment);
          const minW=b.spec.shadowWidthMin*2,maxW=b.spec.shadowWidthMax*2;
          const rootWidth=segment.flow?.rootWidth||minW;
          const pulse=clamp01((rootWidth-minW)/Math.max(1,maxW-minW));
          let stage='hold',pull=0,pinch=0,reach=segment.travelled,neckWidth=rootWidth;
          if(gathering){
            stage='gather';
            const u=clamp01(b.age/Math.max(EPS,b.spec.release));
            pinch=.2+.38*Math.pow(u,.8);
            pull=(4+18*Math.pow(u,1.15))*scale;
            reach=0;
            neckWidth=b.spec.shadowWidthMin*(1.5-.35*u);
          }else if(extending){
            stage='extend';
            const grow=clamp01(segment.travelled/Math.max(1,segment.totalLength));
            pull=(22+5*Math.sin(Math.PI*Math.min(1,grow*1.35))+3.5*pulse)*scale;
            pinch=.58+.06*Math.sin(Math.PI*grow)-.06*pulse;
          }else{
            stage='hold';
            pull=(19+5.5*pulse)*scale;
            pinch=.52-.08*pulse;
          }
          feeds.push({sourceCast:b.serial,segment:segment.index,stage,dx,dy,pull,pinch,reach,neckWidth});
        }
      }
      for(const trail of s.shadowReturns){
        const frac=clamp01(trail.remainingLength/Math.max(1,trail.length));
        if(frac<=1e-4)continue;
        feeds.push({sourceCast:trail.sourceCast,segment:trail.segmentIndex,stage:'return',dx:trail.dir.dx,dy:trail.dir.dy,
          pull:19*Math.pow(frac,.75)*scale,pinch:.48*Math.pow(frac,1.15),reach:trail.remainingLength,neckWidth:(trail.rootWidth||trail.maxWidth||10)*(.5+.5*frac)});
      }
    }
    const prev=s.reservoir?.feeds||[];
    const changed=prev.length!==feeds.length||feeds.some((f,i)=>{const o=prev[i];return !o||o.sourceCast!==f.sourceCast||o.segment!==f.segment||o.stage!==f.stage||Math.abs(o.dx-f.dx)>1e-5||Math.abs(o.dy-f.dy)>1e-5||Math.abs(o.pull-f.pull)>1e-4||Math.abs(o.pinch-f.pinch)>1e-4||Math.abs(o.reach-f.reach)>1e-3||Math.abs(o.neckWidth-f.neckWidth)>1e-4;});
    if(!s.reservoir)s.reservoir={feeds:[],revision:0};
    s.reservoir.feeds=feeds;
    if(changed)s.reservoir.revision=(s.reservoir.revision||0)+1;
  }
  function legal(b){return !b.cancelled&&valid(b.owner)&&b.world===G.World&&b.state.epoch===G.CombatPulse?.epoch&&states.get(b.owner)===b.state&&learned(b.owner,b.m.id);}
  function chainConnected(b,e){const chain=b.followChain||b;if(!chain.chain)return clearPath(b.owner.x,b.owner.y,e.x,e.y);if(!legal(chain))return false;const index=chain.chain.segments.findIndex(s=>s.target===e&&s.contact);return index>=0&&chain.chain.segments[index].linked!==false;}
  function held(e){const l=leases.get(e);return !!l&&legal(l.cast)&&alive(e)&&l.until>l.cast.state.clock&&chainConnected(l.cast,e);}
  const stopped=e=>held(e)&&!strong(e);
  function hasTarget(a,p){
    for(const e of G.EnemyMgr.queryCircle(a.x,a.y,p.range)){
      if(!alive(e)||e.friendly||Math.hypot(e.x-a.x,e.y-a.y)>p.range+(e.r||0))continue;
      if((held(e)&&leases.get(e)?.cast.owner===a)||Ref.lineClear(a.x,a.y,e.x,e.y,clearPath))return true;
    }
    if(p.kind!=='shadow')return false;
    for(const e of G.World.propsInCircle?.(a.x,a.y,p.range)||[])if(e.destructible&&e.hp>0&&clearPath(a.x,a.y,e.x,e.y,1,e))return true;
    return false;
  }
  function canCast(a,m){if(!valid(a)||a.frozen||!supports(m)||m.digiMode==='shikamaru-tactics'||m.digiMode==='shikamaru-strangle')return false;const s=state(a),p=profile(a,m);if((s.cooldowns[m.id]||0)>EPS)return false;if(p.kind==='shadow'&&(casts.some(b=>b.owner===a&&b.kind==='shadow'&&legal(b)&&!b.chain?.ended)||ownedCaptures(s).length))return false;if(p.kind==='sewing'||p.kind==='checkmate')return !!s.lastChain&&legal(s.lastChain)&&s.lastChain.chain.segments.some(x=>x.contact&&alive(x.target)&&chainConnected(s.lastChain,x.target)&&(p.kind!=='checkmate'||held(x.target)&&leases.get(x.target)?.cast.owner===a));return hasTarget(a,p);}
  function cast(a,m){
    if(!canCast(a,m))return false;
    const s=state(a),p=profile(a,m),t=targets(a,p).filter(e=>p.kind!=='strangle'||held(e)&&leases.get(e)?.cast.owner===a);
    if(p.kind==='sewing'||p.kind==='checkmate'){
      const ultimate=p.kind==='checkmate',blastAt=p.release+(p.pulses-1)*p.interval+p.archPrepare+p.archFlight+p.blastFuse;
      const b={serial:++serial,owner:a,state:s,world:G.World,m:{...m},spec:p,kind:'sewing',ultimate,age:0,duration:ultimate?blastAt+.5:p.release+p.pulses*p.interval+p.archFlight+.4,blastAt,sites:new Map(),aim:a.aim||0,rays:[],traps:[],arcs:[],emitted:0,cancelled:false,hits:0,followChain:s.lastChain};
      if(ultimate)for(const [e,l]of ownedCaptures(s))l.until=Math.max(l.until,s.clock+b.duration);
      s.cooldowns[m.id]=p.cd;m.t=p.cd;s.casts[p.kind]=(s.casts[p.kind]||0)+1;s.sewingPose={kind:'sewing',phase:'sewing',started:s.clock,duration:.55,aim:b.aim};if(ultimate)s.ultimate=b;casts.push(b);return true;
    }
    const count=p.kind==='trap'?p.traps:p.kind==='shadow'?Math.min(p.branches,t.length):p.branches;
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
    if(p.kind==='shadow'){
      b.chain={segments:[],visited:new Set(),current:0,ended:false,lastContact:null};
      b.duration=p.release+p.range/p.speed+p.bindDuration+1;
      b.kunai=[];
      for(const target of t.slice(0,p.branches))b.chain.segments.push(makeSegment(b,target,{x:a.x,y:a.y},null));s.lastChain=b;
      updateReservoir(s);s.projection=projectionFor(a,s);
    }
    return true;
  }
  function bind(b,e){if(!legal(b)||!alive(e))return;const old=leases.get(e),until=b.state.clock+b.spec.bindDuration;
    if(!old||old.until<until){leases.set(e,{cast:b,until,x:e.x,y:e.y});b.state.bound++;if(b.shared&&b.kind==='shadow'){b.state.sewingQueued=true;if(b.state.plan)b.state.plan.captureAt??=b.state.clock;}}}
  function hit(b,e,scale=1){
    if(!legal(b)||!alive(e))return false;
    const mult=G.Types?.mult?.(b.m.type||'dark',e.types)??1,crit=Math.random()<(b.owner.critChance||0);
    const damage=b.spec.damage*scale*mult*(G.Weather?.mult?.(b.m.type||'dark')??1)*(crit?1.5:1);
    e.hurt(damage,b.kind==='trap'?'#ffc27b':'#bca6db',0,0,0,crit?'crit':G.Types?.label?.(mult),b.owner,b.m.id);
    if(!legal(b))return false;
    b.owner.onDealt?.(damage);if(!legal(b))return false;
    b.owner.dmgDealt=(b.owner.dmgDealt||0)+damage;b.state.hits++;b.state.damage+=damage;b.hits++;
    if(b.state.contacts.length<120)b.state.contacts.push({cast:b.serial,moveId:b.m.id,targetId:e.id??null,mode:b.kind,pulse:b.emitted,x:e.x,y:e.y,damage});
    G.DamageSplash?.hit?.(b.owner,e,damage,b.kind==='trap'?'#ffc27b':'#bca6db',b.m.id);
    return legal(b);
  }
  function contactVisual(b,e,kind,pulseIndex,life){
    const existing=effects.find(v=>v.kind===kind&&v.castId===b.serial&&v.target===e);
    const data={owner:b.owner,world:b.world,kind,castId:b.serial,moveId:b.m.id,pulseIndex,sourceX:e.x,sourceY:e.y,targetId:e.id??null,target:e,bodyH:e.bodyH||Math.max(18,(e.r||12)*2),x:e.x,y:e.y,radius:(e.r||12)+5,castRef:b};
    if(existing){Object.assign(existing,data);existing.age=0;existing.life=life;existing.lastPulseAt=b.age;existing.pulseEvents.push({index:pulseIndex,age:b.age});return existing;}
    const visual={...data,age:0,life,lastPulseAt:b.age,pulseEvents:[{index:pulseIndex,age:b.age}]};effects.push(visual);return visual;
  }
  function segmentDistance(x,y,ax,ay,bx,by){const dx=bx-ax,dy=by-ay,t=Math.max(0,Math.min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy||1)));return Math.hypot(x-ax-t*dx,y-ay-t*dy);}
  function ribbonGeometry(ax,ay,bx,by,radius){
    const dx=bx-ax,dy=by-ay,length=Math.hypot(dx,dy),nx=length?-dy/length:0,ny=length?dx/length:1;
    return {ax,ay,bx,by,length,nx,ny,radius};
  }
  function ribbonContains(g,x,y,targetRadius=0){
    if(!g.length)return Math.hypot(x-g.ax,y-g.ay)<=targetRadius;
    const lx=g.ax+g.nx*g.radius,ly=g.ay+g.ny*g.radius,rx=g.ax-g.nx*g.radius,ry=g.ay-g.ny*g.radius;
    const cross=(ax,ay,bx,by)=>(bx-ax)*(y-ay)-(by-ay)*(x-ax);
    const a=cross(lx,ly,g.bx,g.by),b=cross(g.bx,g.by,rx,ry),c=cross(rx,ry,lx,ly);
    if((a>=-EPS&&b>=-EPS&&c>=-EPS)||(a<=EPS&&b<=EPS&&c<=EPS))return true;
    // Only the target's real body may overlap an edge; there is no round root cap.
    return Math.min(segmentDistance(x,y,lx,ly,g.bx,g.by),segmentDistance(x,y,g.bx,g.by,rx,ry),segmentDistance(x,y,rx,ry,lx,ly))<=Math.max(0,targetRadius);
  }
  function makeSegment(b,target,origin,sourceActor){
    // Aim into the footward part of the same live shadow, rather than stopping
    // at its closest deforming fringe. Capture still waits for true alpha contact.
    const shadow=projectionFor(target,b.state),destination=shadow?.points.filter(p=>Ref.contains(shadow,p.x,p.y)).reduce((best,p)=>!best||Math.hypot(p.x-target.x,p.y-target.y)<Math.hypot(best.x-target.x,best.y-target.y)?p:best,null)||target;
    const seed=b.serial*1.713+(b.chain?.segments.length||0)*2.391,dx=destination.x-origin.x,dy=destination.y-origin.y,d=Math.hypot(dx,dy),nx=d?-dy/d:0,ny=d?dx/d:1;
    const points=[{...origin}],steps=Math.max(3,Math.ceil(d/5));let blocked=false;
    for(let i=1;i<=steps;i++){
      const u=i/steps,launchRamp=clamp01((u-.14)/.22),envelope=Math.sin(Math.PI*u)*launchRamp;
      const bend=envelope*(Math.sin(seed+u*4.7)*Math.min(32,d*.15)+Math.sin(seed*1.9+u*11.3)*Math.min(9,d*.04));
      let point={x:origin.x+dx*u+nx*bend,y:origin.y+dy*u+ny*bend},previous=points[points.length-1];
      if(!clearPath(previous.x,previous.y,point.x,point.y))point={x:origin.x+dx*u,y:origin.y+dy*u};
      if(!clearPath(previous.x,previous.y,point.x,point.y)){blocked=true;break;}
      points.push(point);
    }
    let totalLength=0;for(let i=1;i<points.length;i++)totalLength+=Math.hypot(points[i].x-points[i-1].x,points[i].y-points[i-1].y);
    return {index:b.chain?.segments.length||0,seed,origin:{...origin},sourceOffset:sourceActor?{x:origin.x-sourceActor.x,y:origin.y-sourceActor.y}:null,sourceActor,target,path:points,totalLength,travelled:0,grownPoints:[{...origin}],polygon:[],contact:false,contactPoint:null,blocked};
  }
  function curveRegionClear(points,pad,extra=null){
    if(!Ref.isRegionClear||!points.length)return false;
    let minX=extra?extra.x:points[0].x,maxX=minX,minY=extra?extra.y:points[0].y,maxY=minY;
    for(const p of points){if(p.x<minX)minX=p.x;if(p.x>maxX)maxX=p.x;if(p.y<minY)minY=p.y;if(p.y>maxY)maxY=p.y;}
    return Ref.isRegionClear(minX-pad,minY-pad,maxX+pad,maxY+pad,clearPath);
  }
  function segmentPathLinked(owner,grown,open=false){
    if(!grown.length||open)return true;
    return Ref.polylineClear?Ref.polylineClear(owner,grown,clearPath):(clearPath(owner.x,owner.y,grown[0].x,grown[0].y)&&!grown.some((p,i,list)=>i&&!clearPath(list[i-1].x,list[i-1].y,p.x,p.y)));
  }
  function chainMesh(segment,spec,phase,openRegion=false){
    const points=segment.grownPoints,left=[],right=[];let total=0,passed=0;
    for(let i=1;i<points.length;i++)total+=Math.hypot(points[i].x-points[i-1].x,points[i].y-points[i-1].y);
    const stations=[],min=spec.shadowWidthMin,max=spec.shadowWidthMax,span=max-min;
    const open=openRegion||curveRegionClear(points,max+2);
    const connected=!!segment.contact;
    // Continuous liquid shadow stream: wide funnel root at the foot pool, sleek waist
    // through mid-flight (no bulbous dumbbell tip when short!), and a flared shadow-grasp
    // meld where it fuses into a captured enemy's foot shadow.
    const surge=(distance,offset,period,sharp)=>{const u=((distance-phase*56+segment.seed*19+offset)%period+period)%period-period*.5;return Math.exp(-u*u/sharp);};
    for(let i=0;i<points.length;i++){
      if(i)passed+=Math.hypot(points[i].x-points[i-1].x,points[i].y-points[i-1].y);
      const prev=points[Math.max(0,i-1)],next=points[Math.min(points.length-1,i+1)],dx=next.x-prev.x,dy=next.y-prev.y,d=Math.hypot(dx,dy)||1;
      const distFromTip=Math.max(0,total-passed);
      const tipSpan=Math.max(20,Math.min(44,total*.55));
      const taper=connected?(.78+.38*Math.exp(-distFromTip/16)):Math.pow(Math.sin(Math.min(Math.PI/2,distFromTip/tipSpan*Math.PI/2)),.92);
      const rootFunnel=Math.exp(-passed/34);
      const waveEnvelope=clamp01((total-42)/70)*Math.sin(Math.PI*clamp01(passed/Math.max(1,total)));
      const width=sign=>{
        const sideOff=sign>0?-24:29;
        const bodyWave=waveEnvelope*(.52*surge(passed,sideOff,128,860)+.28*surge(passed,-sideOff*.7,82,380)+.14*Math.sin(passed*.06-phase*3.4+segment.seed*(sign>0?1.3:2.1)));
        const baseProfile=.14+.52*rootFunnel+Math.max(0,bodyWave);
        return Math.max(connected?min*.75:.8,taper*(min+span*clamp01(baseProfile)));
      };
      const pointOpen=open||!!Ref.isPointOpen?.(points[i].x,points[i].y,max+1,clearPath);
      const edge=sign=>{const w=width(sign),ox=-dy/d*w*sign,oy=dx/d*w*sign;let fraction=1;if(!pointOpen&&!clearPath(points[i].x,points[i].y,points[i].x+ox,points[i].y+oy)){let low=0,high=1;for(let step=0;step<5;step++){const t=(low+high)/2;if(clearPath(points[i].x,points[i].y,points[i].x+ox*t,points[i].y+oy*t))low=t;else high=t;}fraction=low;}return {point:{x:points[i].x+ox*fraction,y:points[i].y+oy*fraction},width:w*fraction};};
      const l=edge(1),r=edge(-1);left.push(l.point);right.push(r.point);stations.push({distance:passed,left:l.width,right:r.width});
    }
    segment.flow={phase,stations,rootWidth:stations[0]?stations[0].left+stations[0].right:0,maxWidth:stations.reduce((n,s)=>Math.max(n,s.left,s.right),0)};
    return [...left,...right.reverse()];
  }
  function polygonContains(poly,x,y,radius=0){
    if(poly.length<3)return false;let inside=false;
    for(let i=0,j=poly.length-1;i<poly.length;j=i++){
      const a=poly[i],b=poly[j];
      if(segmentDistance(x,y,a.x,a.y,b.x,b.y)<=radius+1e-6)return true;
      if((a.y>y)!==(b.y>y)&&x<(b.x-a.x)*(y-a.y)/(b.y-a.y)+a.x)inside=!inside;
    }return inside;
  }
  function refreshSegment(b,segment){
    const grown=[];let remaining=segment.travelled;
    grown.push({...segment.path[0]});
    for(let i=1;i<segment.path.length;i++){
      const a=segment.path[i-1],z=segment.path[i],d=Math.hypot(z.x-a.x,z.y-a.y);
      if(remaining>=d){grown.push({...z});remaining-=d;}else{if(remaining>0)grown.push({x:a.x+(z.x-a.x)*remaining/d,y:a.y+(z.y-a.y)*remaining/d});break;}
    }
    const source=segment.sourceActor?(alive(segment.sourceActor)?segment.sourceActor:segment.origin):b.owner;
    let root={x:source.x+(alive(segment.sourceActor)?segment.sourceOffset?.x||0:0),y:source.y+(alive(segment.sourceActor)?segment.sourceOffset?.y||0:0)};
    const start=grown[0],end=grown.at(-1);
    const tip=segment.contact&&alive(segment.target)&&grown.length>1?{x:segment.target.x+(segment.contactOffset?.x||0),y:segment.target.y+(segment.contactOffset?.y||0)}:end;
    if(!segment.sourceActor){
      const projection=b.state.projection||projectionFor(b.owner,b.state);
      const {dx,dy}=segmentDirection(b.owner,segment);
      const join=boundaryJoin(projection,b.owner,dx,dy);
      segment.sourceJoin=join;segment.rootExit=join;
      const joinDist=Math.hypot(join.x-b.owner.x,join.y-b.owner.y),tipDist=Math.hypot(tip.x-b.owner.x,tip.y-b.owner.y);
      if(segment.contact||tipDist>joinDist+2)root={...join};
    }
    const ox=end.x-start.x,oy=end.y-start.y,oldLength=Math.hypot(ox,oy),dx=tip.x-root.x,dy=tip.y-root.y,length=Math.hypot(dx,dy);
    // Transport the entire grown curve in its chord's frame. Moving only the
    // first/last vertex leaves one long edge and a right-angle elbow behind.
    // The unreleased tip stays fixed; short links flatten instead of looping.
    if(grown.length>1&&oldLength>EPS){
      const bendScale=Math.min(1,length/oldLength),nx=length?-dy/length:0,ny=length?dx/length:0;
      for(let i=0;i<grown.length;i++){
        const px=grown[i].x-start.x,py=grown[i].y-start.y,u=Math.max(0,Math.min(1,(px*ox+py*oy)/(oldLength*oldLength))),bend=(-oy*px+ox*py)/oldLength*bendScale;
        grown[i]={x:root.x+dx*u+nx*bend,y:root.y+dy*u+ny*bend};
      }
      grown[grown.length-1]={...tip};
    }
    grown[0]=root;
    const open=curveRegionClear(grown,b.spec.shadowWidthMax+2,b.owner);
    const phase=b.state.material.phase,pathFn=G.World?.projectilePathClear;
    const sameMesh=segment.polygon.length>=3&&segment._mPhase===phase&&segment._mWorld===G.World&&segment._mPath===pathFn&&segment._mLen===grown.length&&segment._mRx===root.x&&segment._mRy===root.y&&segment._mTx===tip.x&&segment._mTy===tip.y&&segment._mTr===segment.travelled&&segment._mContact===!!segment.contact;
    segment.grownPoints=grown;
    if(!sameMesh){
      segment.polygon=chainMesh(segment,b.spec,phase,open);
      segment._mPhase=phase;segment._mWorld=G.World;segment._mPath=pathFn;segment._mLen=grown.length;segment._mRx=root.x;segment._mRy=root.y;segment._mTx=tip.x;segment._mTy=tip.y;segment._mTr=segment.travelled;segment._mContact=!!segment.contact;
    }
    segment.linked=segmentPathLinked(b.owner,grown,open);
  }
  function reanchorContacts(s,projMap){
    const b=s.lastChain;if(!b||!legal(b))return;
    for(const segment of b.chain.segments){
      if(!segment.contact||!alive(segment.target))continue;
      const e=segment.target,projection=projMap?.get(e)||projectionFor(e,s);
      if(projMap&&projection)projMap.set(e,projection);
      const old={x:e.x+(segment.contactOffset?.x||0),y:e.y+(segment.contactOffset?.y||0)};
      if(projection&&!Ref.contains(projection,old.x,old.y)){
        const previous=segment.grownPoints.at(-2)||segment.origin;
        const point=projection.points.reduce((best,p)=>Ref.contains(projection,p.x,p.y)&&clearPath(previous.x,previous.y,p.x,p.y)&&(!best||Math.hypot(p.x-old.x,p.y-old.y)<Math.hypot(best.x-old.x,best.y-old.y))?p:best,null);
        if(!point){segment.linked=false;leases.delete(e);continue;}
        segment.contactOffset={x:point.x-e.x,y:point.y-e.y};segment.liveContactPoint={...point};
        for(const next of b.chain.segments)if(next.sourceActor===e)next.sourceOffset={...segment.contactOffset};
      }
      refreshSegment(b,segment);
      if(!segment.linked){leases.delete(e);segment.finished=true;}
    }
  }
  function advanceChain(b,dt){
    if(b.age<b.spec.release||!legal(b))return;
    const chain=b.chain;
    for(const segment of chain.segments){
      if(!legal(b))return;
      if(segment.contact||segment.finished)continue;
      const e=segment.target;
      if(!alive(e)){segment.finished=true;continue;}
      segment.travelled=Math.min(segment.totalLength,segment.travelled+Math.min(dt,Math.max(0,b.age-b.spec.release))*b.spec.speed);refreshSegment(b,segment);
      if(!segment.linked){segment.finished=true;continue;}
      const projection=projectionFor(e,b.state),contact=e.destructible?(polygonContains(segment.polygon,e.x,e.y,e.r||0)?{x:e.x,y:e.y}:null):Ref.groundContact(projection,segment.polygon,polygonContains);
      if(contact&&clearPath(segment.grownPoints[0].x,segment.grownPoints[0].y,contact.x,contact.y)){
        if(e.destructible){G.World.damageProp?.(e,b.spec.damage,'#302936');segment.finished=true;continue;}
        const point={...contact};segment.contact=true;segment.contactPoint=point;segment.contactOffset={x:point.x-e.x,y:point.y-e.y};segment.targetProjection=projection;chain.visited.add(e);chain.lastContact=point;
        segment.path=segment.grownPoints.map(p=>({...p}));segment.path.push(point);segment.travelled=segment.totalLength=segment.path.slice(1).reduce((sum,p,i)=>sum+Math.hypot(p.x-segment.path[i].x,p.y-segment.path[i].y),0);refreshSegment(b,segment);
        segment.shots=0;segment.nextShot=b.age;bind(b,e);contactVisual(b,e,'shadow',segment.index+1,.25);
      }else if(segment.travelled>=segment.totalLength)segment.finished=true;
    }
    chain.ended=chain.segments.every(s=>s.contact||s.finished);
    advanceKunai(b,dt);
  }
  function advanceKunai(b,dt){
    for(const segment of b.chain.segments){
      if(!legal(b))return;
      if(!segment.contact||segment.linked===false||!alive(segment.target)||!held(segment.target)||leases.get(segment.target)?.cast!==b)continue;
      while(segment.shots<b.spec.kunaiRounds&&b.age+EPS>=segment.nextShot){
        const target=segment.target,source={x:b.owner.x,y:b.owner.y},dx=target.x-source.x,dy=target.y-source.y,d=Math.hypot(dx,dy)||1;
        b.kunai.push({x:source.x,y:source.y,vx:dx/d*b.spec.kunaiSpeed,vy:dy/d*b.spec.kunaiSpeed,target,round:++segment.shots,born:b.age,remaining:b.spec.range+40,done:false});
        segment.nextShot+=b.spec.kunaiInterval;
        b.state.throwPose={kind:'trap',phase:'release',started:b.state.clock,aim:Math.atan2(dy,dx),duration:.2};
      }
    }
    for(const k of b.kunai){
      if(!legal(b))return;if(k.done||!alive(k.target)){k.done=true;continue;}
      const travel=Math.min(k.remaining,Math.max(0,Math.min(dt,b.age-k.born))*b.spec.kunaiSpeed),ax=k.x,ay=k.y,bx=ax+k.vx/b.spec.kunaiSpeed*travel,by=ay+k.vy/b.spec.kunaiSpeed*travel;
      k.x=bx;k.y=by;k.remaining-=travel;
      const e=k.target,dx=bx-ax,dy=by-ay,u=Math.max(0,Math.min(1,((e.x-ax)*dx+(e.y-ay)*dy)/(dx*dx+dy*dy||1))),cx=ax+dx*u,cy=ay+dy*u;
      const contact=travel>0&&Math.hypot(e.x-cx,e.y-cy)<=(e.r||12)+3;
      if(!clearPath(ax,ay,contact?cx:bx,contact?cy:by,2)){k.done=true;continue;}
      if(contact){k.done=true;b.emitted=k.round;if(!hit(b,e))return;
        if(b.state.contacts.length)b.state.contacts.at(-1).geometry={kind:'kunai-sweep',previous:{x:ax,y:ay},current:{x:bx,y:by},point:{x:cx,y:cy},round:k.round};
        contactVisual(b,e,'kunai',k.round,.16);
      }else if(k.remaining<=EPS)k.done=true;
    }
    b.kunai=b.kunai.filter(k=>!k.done);
  }
  function advanceSewing(b){
    if(!legal(b.followChain)){b.cancelled=true;return;}
    if(!b.followChain.chain.segments.some(segment=>segment.contact&&alive(segment.target)&&chainConnected(b.followChain,segment.target)))b.emitted=b.spec.pulses;
    while(legal(b)&&b.emitted<b.spec.pulses&&b.age>=b.spec.release+b.emitted*b.spec.interval){
      const born=b.spec.release+b.emitted*b.spec.interval;b.emitted++;
      for(const segment of b.followChain.chain.segments){
        if(!legal(b))return;const e=segment.target;
        if(!segment.contact||segment.linked===false||!alive(e)||!chainConnected(b.followChain,e))continue;
        const origin=b.ultimate?segment.grownPoints[Math.floor((segment.grownPoints.length-1)*.4)]:b.owner;
        const arc=Ref.makeArch(b.owner,e,{x:origin.x,y:origin.y},b.arcs.length,b.spec.needleWidth);if(b.ultimate)arc.lift*=1.35;arc.born=born;arc.pulseIndex=b.emitted;arc.hitSet=new Set();arc.bodySource=Ref.bodyFor(e);b.arcs.push(arc);
      }
    }
    for(const arc of b.arcs){
      if(!legal(b))return;if(arc.blocked||arc.progress>=1)continue;
      const age=b.age-arc.born;if(age<0)continue;
      const progress=Math.max(0,Math.min(1,(age-b.spec.archPrepare)/b.spec.archFlight)),old={...arc.current},body=Ref.bodyFor(arc.target);arc.framePrevious=old;
      while(arc.progress<progress-EPS){
        const next=Math.min(progress,arc.progress+.025);Ref.advanceArch(arc,next,clearPath);if(arc.blocked)break;
        if(!arc.hit&&alive(arc.target)){
          const contact=Ref.sweptBody(arc,arc.previous,arc.current,body,clearPath);
          if(contact){
            arc.hit=true;arc.hitSet.add(arc.target);arc.contact={point:{...contact},previous:{...arc.previous},current:{...arc.current},progress:arc.progress,phase:arc.phase,targetId:arc.target.id,bodyKey:body?.key};
            const emitted=b.emitted;b.emitted=arc.pulseIndex;if(!hit(b,arc.target)){b.emitted=emitted;return;}b.emitted=emitted;
            if(b.state.contacts.length)b.state.contacts[b.state.contacts.length-1].geometry={kind:'xyz-tip-sweep',...arc.contact};
            if(b.ultimate&&!b.sites.has(arc.target))b.sites.set(arc.target,{x:contact.x,y:contact.y,plantedAt:b.age,detonated:false});
          }
        }
      }
      arc.previous=old;
    }
    if(b.ultimate&&b.age+EPS>=b.blastAt){
      const seen=b.blastSeen??(b.blastSeen=new Set());
      for(const site of b.sites.values()){
        if(!legal(b))return;if(site.detonated)continue;site.detonated=true;b.state.detonations++;
        effects.push({owner:b.owner,world:b.world,kind:'checkmate-blast',castRef:b,lastPulseAt:b.age,x:site.x,y:site.y,age:0,life:.48,radius:b.spec.blastRadius});
        for(const e of new Set(G.EnemyMgr.queryCircle(site.x,site.y,b.spec.blastRadius+40))){
          if(!legal(b))return;if(!alive(e)||e.friendly||seen.has(e)||Math.hypot(e.x-site.x,e.y-site.y)>b.spec.blastRadius+(e.r||0)||!clearPath(site.x,site.y,e.x,e.y))continue;
          seen.add(e);const emitted=b.emitted;b.emitted=b.spec.pulses+1;if(!hit(b,e,b.spec.blastScale)){b.emitted=emitted;return;}b.emitted=emitted;
          if(b.state.contacts.length)b.state.contacts.at(-1).geometry={kind:'planted-tag-blast',origin:{x:site.x,y:site.y},radius:b.spec.blastRadius};
        }
      }
    }
    if(!b.ultimate&&b.emitted>=b.spec.pulses&&!b.arcs.some(arc=>!arc.blocked&&arc.progress<1&&alive(arc.target)))b.duration=Math.min(b.duration,b.age+.16);
  }
  function shadowVisualFor(a){
    const s=states.get(a),m=moveFor(a,'shadow'),p=m?profile(a,m):null,b=s?.lastChain;let extensionTotal=0,branches=0;
    if(b&&legal(b)&&(casts.includes(b)||ownedCaptures(s).length))for(const segment of b.chain.segments){
      if(segment.linked===false)continue;
      const points=segment.grownPoints;for(let i=1;i<points.length;i++)extensionTotal+=Math.hypot(points[i].x-points[i-1].x,points[i].y-points[i-1].y);if(points.length>1)branches++;
    }
    const spent=Math.min(1,extensionTotal/Math.max(1,(p?.range||360)));
    return {x:a.x,y:a.y,poolRadius:34*Math.sqrt(1-.88*spent),spent,extensionTotal,branches};
  }
  function pulse(b,index,current){
    const p=b.spec,owner=b.owner,seen=b.hitSets[index]??(b.hitSets[index]=new Set());
    // A persistent ground band can catch enemies entering its grown section.
    // Its tip uses only the current sim age; never predict a future endpoint.
    const ax=owner.x,ay=owner.y;
    for(const ray of b.rays){
      if(!legal(b))return;
      if(b.kind==='strangle'){
        const e=ray.target;
        if(!alive(e)||!held(e)||leases.get(e)?.cast.owner!==owner||Math.hypot(e.x-ax,e.y-ay)>p.range)continue;
        ray.source={x:ax,y:ay};ray.tip={x:e.x,y:e.y};
        if(current<.08||seen.has(e))continue;
        seen.add(e);b.emitted=index+1;if(!hit(b,e))return;
        contactVisual(b,e,'strangle',index+1,Math.max(.24,b.duration-b.age+.18));
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
      const geometry=ribbonGeometry(ax,ay,bx,by,p.radius);
      const mx=(ax+bx)/2,my=(ay+by)/2,r=reach/2+p.radius+40;
      for(const e of new Set(G.EnemyMgr.queryCircle(mx,my,r))){
        if(!legal(b))return;
        if(!alive(e)||e.friendly||seen.has(e)||!ribbonContains(geometry,e.x,e.y,e.r||0)||!clearPath(ax,ay,e.x,e.y))continue;
        if(b.kind==='strangle'&&(!held(e)||leases.get(e)?.cast.owner!==owner))continue;
        seen.add(e);b.emitted=index+1;
        if(!hit(b,e))return;
        if(b.kind==='shadow'||b.kind==='sewing')bind(b,e);
        effects.push({owner,world:b.world,kind:b.kind,x:e.x,y:e.y,age:0,life:b.kind==='sewing'?.36:.25,radius:p.radius+8});
      }
      for(const prop of G.World.propsInCircle?.(mx,my,r)||[]){
        if(!legal(b))return;
        if(!prop.destructible||prop.hp<=0||seen.has(prop)||!ribbonContains(geometry,prop.x,prop.y,prop.r||0)||!clearPath(ax,ay,prop.x,prop.y,1,prop))continue;
        seen.add(prop);G.World.damageProp?.(prop,p.damage,'#bca6db');
      }
    }
  }
  function detonate(b,t){
    if(t.detonated||!legal(b))return;t.detonated=true;b.state.detonations++;
    effects.push({owner:b.owner,world:b.world,kind:'explosion',castId:b.serial,moveId:b.m.id,pulseIndex:b.emitted,sourceX:t.x,sourceY:t.y,targetId:null,x:t.x,y:t.y,age:0,life:.5,radius:b.spec.radius});
    for(const e of new Set(G.EnemyMgr.queryCircle(t.x,t.y,b.spec.radius+40))){
      if(!legal(b))return;if(!alive(e)||e.friendly||Math.hypot(e.x-t.x,e.y-t.y)>b.spec.radius+(e.r||0)||!clearPath(t.x,t.y,e.x,e.y))continue;
      if(!hit(b,e,held(e)&&leases.get(e)?.cast.owner===b.owner?1.5:1))return;
    }
    for(const prop of G.World.propsInCircle?.(t.x,t.y,b.spec.radius)||[]){if(!legal(b))return;if(prop.destructible&&prop.hp>0&&Math.hypot(prop.x-t.x,prop.y-t.y)<=b.spec.radius+(prop.r||0)&&clearPath(t.x,t.y,prop.x,prop.y,1,prop))G.World.damageProp?.(prop,b.spec.damage,'#ffc27b');}
  }
  const moveFor=(a,kind)=>a.moves?.find(m=>m.digiMode==='shikamaru-'+kind);
  const activeFront=s=>!!s.lastChain&&legal(s.lastChain)&&casts.includes(s.lastChain)&&!s.lastChain.chain.ended;
  function activeSewing(s){return casts.some(b=>b.owner===s.owner&&b.kind==='sewing'&&legal(b)&&((b.arcs||[]).some(arc=>!arc.blocked&&arc.progress<1&&alive(arc.target))||b.emitted<b.spec.pulses&&b.followChain.chain.segments.some(segment=>segment.contact&&alive(segment.target)&&chainConnected(b.followChain,segment.target))));}
  function relay(s,kind,finisher=false){
    const m=moveFor(s.owner,kind);if(!m)return null;
    s.cooldowns[m.id]=0;
    if(!cast(s.owner,m))return null;
    const b=casts[casts.length-1];b.shared=true;b.finisher=finisher;return b;
  }
  function ownedCaptures(s){return [...leases].filter(([e,l])=>l.cast.owner===s.owner&&held(e));}
  function deploy(s,x,y){
    const m=moveFor(s.owner,'trap');if(!m)return;
    const p=profile(s.owner,m);if(s.board.length>=p.traps||!clearPath(s.owner.x,s.owner.y,x,y))return;
    const b={serial:++serial,owner:s.owner,state:s,world:G.World,m:{...m},spec:p,kind:'trap',shared:true,origin:{x:s.owner.x,y:s.owner.y},cancelled:false,hits:0,emitted:0};
    s.board.push({x,y,born:s.clock,cast:b,blastAt:Infinity,round:0,detonated:false});
    s.throwPose={kind:'trap',phase:'release',started:s.clock,aim:Math.atan2(y-s.owner.y,x-s.owner.x),duration:.22};
  }
  function moveBoard(s,dt){
    const a=s.owner,dx=a.x-s.prevX,dy=a.y-s.prevY,d=Math.hypot(dx,dy),oldX=s.prevX,oldY=s.prevY;
    s.prevX=a.x;s.prevY=a.y;s.moving=d>.05;
    if(!Number.isFinite(d)||d>Math.max(80,dt*900))return;
    if(d){
      s.travelled+=d;
      const m=moveFor(a,'trap');if(m){
        const p=profile(a,m),total=s.walkDistance+d,count=Math.min(p.traps,Math.floor(total/p.deployDistance));
        for(let i=0;i<count;i++){const distance=p.deployDistance-s.walkDistance+i*p.deployDistance,u=Math.min(1,distance/d);deploy(s,oldX+dx*u,oldY+dy*u);}
        s.walkDistance=total%p.deployDistance;
      }
    }
    // Existing nodes retain their born/fuse when new capacity is learned.
    for(let i=s.board.length-1;i>=0;i--){const t=s.board[i],b=t.cast;
      if(!legal(b)||s.clock-t.born>b.spec.trapLifetime){s.board.splice(i,1);continue;}
      while(legal(b)&&t.round<b.spec.blastRounds&&s.clock+EPS>=t.blastAt+t.round*b.spec.blastInterval){
        t.detonated=false;b.emitted=t.round+1;detonate(b,t);t.round++;
      }
      if(!legal(b))return;
      if(t.round>=b.spec.blastRounds){s.board.splice(i,1);}
    }
  }
  function startNet(s){
    const p=s.plan;if(!p||p.phase!=='drag')return;
    p.phase='net';p.at=s.clock;p.stop=0;
    for(const [,l]of ownedCaptures(s))l.until=Math.max(l.until,s.clock+3);
  }
  function sharedPlan(s,dt){
    const a=s.owner,m=moveFor(a,'shadow');if(!m){clear(a);return;}
    const spec=profile(a,m);moveBoard(s,dt);if(states.get(a)!==s)return;
    let p=s.plan;
    if(!p){
      if(canCast(a,m)){
        const b=relay(s,'shadow');if(b&&b.rays.some(r=>!r.target?.destructible)){s.plan=p={phase:'prepare',at:s.clock,started:s.clock,stop:0,sewn:false,netHit:false,moved:s.moving,seedPlaced:false};s.cycles++;}
      }
      return;
    }
    const age=s.clock-p.at,heldList=ownedCaptures(s);
    if(s.moving)p.moved=true;
    if(!['finish','recover'].includes(p.phase))for(const [,l]of heldList)l.until=Math.max(l.until,s.clock+.65);
    // Standing has one modest tool fallback; movement is the source of a full route.
    if(!p.moved&&!p.seedPlaced&&moveFor(a,'trap')&&s.clock-p.started>=.65){deploy(s,a.x,a.y);p.seedPlaced=true;}
    if(p.phase==='prepare'&&age>=spec.release){p.phase='release';p.at=s.clock;}
    else if(p.phase==='release'&&s.clock-p.started>=spec.captureWindow){
      if(heldList.length){p.phase='drag';p.at=s.clock;}
      else if(!activeFront(s)&&s.clock-p.started>=spec.release+spec.range/spec.speed+.08){p.phase='recover';p.at=s.clock;p.empty=true;s.cooldowns[m.id]=Math.min(s.cooldowns[m.id]||0,.18);}
    }
    if(s.sewingQueued&&!p.sewn&&s.clock-p.started>=.4){p.sewn=true;s.sewingQueued=false;relay(s,'sewing');}
    if(['drag','blast'].includes(p.phase)&&canCast(a,m))relay(s,'shadow');
    if(p.phase==='drag'){
      if(!heldList.length&&!activeFront(s)&&!moveFor(a,'trap')){p.phase='recover';p.at=s.clock;p.empty=true;}
      const ready=heldList.length>=2&&(!moveFor(a,'trap')||s.board.some(t=>s.clock-t.born>=t.cast.spec.trapArm));
      p.stop=!s.moving&&ready&&s.clock-(p.captureAt??s.clock)>=.7?p.stop+dt:0;
      if(p.stop>=spec.stopWindow||s.clock-p.started>=spec.dragTimeout)startNet(s);
    }else if(p.phase==='net'&&age>=spec.netPrepare){
      // A Lv1 net is already a real second attack, even before any tool is learned.
      const net={serial:++serial,owner:a,state:s,world:G.World,m:{...m},spec,kind:'shadow',age:0,shared:true,finisher:true,cancelled:false,hits:0,emitted:1};
      for(const [e]of moveFor(a,'sewing')?[]:heldList){
        if(!legal(net))break;const segment=s.lastChain?.chain.segments.find(segment=>segment.target===e&&segment.contact),projection=projectionFor(e);
        const contact=segment&&Ref.groundContact(projection,segment.polygon,polygonContains);if(!contact)continue;
        if(!hit(net,e,2))break;if(s.contacts.length)s.contacts[s.contacts.length-1].geometry={kind:'ground-alpha-net',point:contact,bodyKey:projection?.body.key};
      }
      if(states.get(a)!==s)return;
      const ultimate=moveFor(a,'checkmate');
      const finishing=ultimate&&cast(a,ultimate)?casts.at(-1):relay(s,'sewing',true);
      if(finishing?.ultimate){s.ultimate=finishing;p.checkmate=true;}
      let scheduled=0,last=s.clock;
      for(const t of s.board){if(!legal(t.cast)||Number.isFinite(t.blastAt)||s.clock-t.born<t.cast.spec.trapArm)continue;
        t.blastAt=s.clock+scheduled*t.cast.spec.chainInterval;last=t.blastAt+(t.cast.spec.blastRounds-1)*t.cast.spec.blastInterval;scheduled++;
      }
      p.phase='blast';p.at=s.clock;p.end=Math.max(s.clock+.4,last+.2,finishing?.ultimate?s.clock+finishing.duration:0);p.nodes=scheduled;
    }else if(p.phase==='blast'&&s.clock>=p.end&&!activeFront(s)&&!activeSewing(s)){const finish=relay(s,'strangle',true);p.phase='finish';p.at=s.clock;p.finishDuration=finish?finish.spec.release+(finish.spec.pulses-1)*finish.spec.interval+.25:.45;for(const [,l]of ownedCaptures(s))l.until=Math.max(l.until,s.clock+p.finishDuration+.1);}
    else if(p.phase==='finish'&&age>=p.finishDuration){p.phase='recover';p.at=s.clock;for(const [e]of ownedCaptures(s))leases.delete(e);}
    else if(p.phase==='recover'&&s.clock-p.at>=(p.empty?.18:spec.recoverTime)){s.plan=null;s.sewingQueued=false;}
    if(states.get(a)!==s)return;
    const phase=s.plan?.phase||'ready',remaining=phase==='drag'?Math.max(0,spec.dragTimeout-(s.clock-p.started)):phase==='net'?Math.max(0,spec.netPrepare-(s.clock-p.at)):phase==='blast'?Math.max(0,p.end-s.clock):0;
    const captured=ownedCaptures(s).length,board=s.board.length,hasTrap=!!moveFor(a,'trap');
    const canStop=captured>=2&&(!hasTrap||s.board.some(t=>s.clock-t.born>=t.cast.spec.trapArm))&&s.clock-(p.captureAt??s.clock)>=.7;
    s.cue={phase,remaining,captured,board,label:phase==='drag'?`${hasTrap?'佈局｜札'+board+' ':''}捕捉${captured}${canStop?' · 停步收網':''}`:phase==='net'?'結印 · 影網收束':phase==='blast'?(activeFront(s)?'影模仿 · 多重捕捉':p.nodes?'起爆札接力':'影網絞擊'):phase==='finish'?(moveFor(a,'strangle')?'影首縛 · 終結':'影術收勢'):phase==='recover'?(p.empty?'重新結影':'整備'):'影模仿 · 捕捉'};
  }
  function clear(owner){
    for(const [a,s]of states)if(!owner||a===owner)for(const t of s.board)t.cast.cancelled=true;
    for(const b of casts)if(!owner||b.owner===owner)b.cancelled=true;
    for(const [e,l]of leases)if(!owner||l.cast.owner===owner)leases.delete(e);
    for(let i=casts.length-1;i>=0;i--)if(!owner||casts[i].owner===owner)casts.splice(i,1);
    for(let i=effects.length-1;i>=0;i--)if(!owner||effects[i].owner===owner)effects.splice(i,1);
    if(owner)states.delete(owner);else states.clear();
  }
  function prefixPoints(points,length){
    if(!points.length||length<=0)return [];
    const result=[{...points[0]}];let remaining=length;
    for(let i=1;i<points.length;i++){
      const a=points[i-1],b=points[i],d=Math.hypot(b.x-a.x,b.y-a.y);
      if(d<=remaining){result.push({...b});remaining-=d;}
      else{if(d>EPS)result.push({x:a.x+(b.x-a.x)*remaining/d,y:a.y+(b.y-a.y)*remaining/d});break;}
    }return result;
  }
  function transportCurve(points,root,tip){
    if(points.length<2)return points.map(p=>({...p}));
    const start=points[0],end=points.at(-1),ox=end.x-start.x,oy=end.y-start.y,oldLength=Math.hypot(ox,oy);
    const dx=tip.x-root.x,dy=tip.y-root.y,length=Math.hypot(dx,dy);
    if(oldLength<=EPS)return [{...root},{...tip}];
    const bendScale=Math.min(1,length/oldLength),nx=length?-dy/length:0,ny=length?dx/length:0;
    const result=points.map(p=>{const px=p.x-start.x,py=p.y-start.y,u=clamp01((px*ox+py*oy)/(oldLength*oldLength)),bend=(-oy*px+ox*py)/oldLength*bendScale;return {x:root.x+dx*u+nx*bend,y:root.y+dy*u+ny*bend};});
    result[0]={...root};result[result.length-1]={...tip};return result;
  }
  function refreshReturnTrail(s,trail){
    const end=trail.points.at(-1);if(!end)return;
    const vx=end.x-s.owner.x,vy=end.y-s.owner.y,vd=Math.hypot(vx,vy);
    if(vd>2)trail.dir={dx:vx/vd,dy:vy/vd};
    const join=boundaryJoin(s.projection,s.owner,trail.dir.dx,trail.dir.dy);
    trail.sourceJoin=join;
    const transported=transportCurve(trail.points,join,end);
    trail.remainingPoints=prefixPoints(transported,trail.remainingLength);
    if(trail.remainingPoints.length>=2){
      const meshSeg={grownPoints:trail.remainingPoints,seed:trail.seed};
      trail.polygon=chainMesh(meshSeg,trail.spec,s.material.phase);
      trail.rootWidth=meshSeg.flow?.rootWidth||trail.rootWidth;
    }else trail.polygon=[];
  }
  function updateShadowReturns(s,dt){
    if(!moveFor(s.owner,'shadow')){s.shadowReturns=[];s.visibleShadow=null;return;}
    for(const trail of s.shadowReturns){
      trail.age+=dt;trail.remainingLength=trail.length*Math.max(0,1-(trail.age/trail.life)**.85);
    }
    s.shadowReturns=s.shadowReturns.filter(trail=>trail.age<trail.life&&trail.remainingLength>2);
    const b=s.lastChain,visible=b&&legal(b)&&(casts.includes(b)||ownedCaptures(s).length);
    if(visible){s.visibleShadow=b;return;}
    const previous=s.visibleShadow;s.visibleShadow=null;if(!previous||!legal(previous))return;
    // This settled copy has no cast/target callbacks and cannot keep a lease alive.
    for(const segment of previous.chain.segments){
      if(segment.linked===false||segment.polygon.length<3||segment.grownPoints.length<2)continue;
      const points=segment.grownPoints.map(p=>({...p})),length=points.reduce((n,p,i)=>n+(i?Math.hypot(p.x-points[i-1].x,p.y-points[i-1].y):0),0);
      if(length<=2)continue;
      const dir=segmentDirection(s.owner,segment);
      s.shadowReturns.push({sourceCast:previous.serial,segmentIndex:segment.index,points,polygon:segment.polygon.map(p=>({...p})),seed:segment.seed,spec:previous.spec,dir,sourceJoin:segment.sourceJoin||points[0],rootWidth:segment.flow?.rootWidth||previous.spec.shadowWidthMin*2,maxWidth:segment.flow?.maxWidth||previous.spec.shadowWidthMax,age:0,life:.34,length,remainingLength:length,remainingPoints:points});
    }
  }
  function update(dt){
    if(G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    Ref.beginFrame?.();
    for(const [a,s]of states){if(!valid(a)||s.world!==G.World||s.epoch!==G.CombatPulse?.epoch||((s.plan||s.lastChain)&&!moveFor(a,'shadow'))){clear(a);continue;}s.clock+=dt;s.material.clock=s.clock;s.material.phase=Math.floor(s.clock*30)/30;if(s.pose&&s.pose.age>=.65)s.pose=null;
      const chain=s.lastChain;
      if(chain&&legal(chain)){
        if(casts.includes(chain)&&!chain.chain.ended){updateReservoir(s);s.projection=projectionFor(s.owner,s);}
        for(const segment of chain.chain.segments)if(segment.contact){
          const open=curveRegionClear(segment.grownPoints,2,s.owner);
          if(!segmentPathLinked(s.owner,segment.grownPoints,open)){segment.linked=false;leases.delete(segment.target);segment.finished=true;}
        }
      }
    }
    for(const [e,l]of leases)if(!held(e))leases.delete(e);
    for(const b of casts.slice()){
      if(!legal(b)){b.cancelled=true;const i=casts.indexOf(b);if(i>=0)casts.splice(i,1);continue;}
      b.age+=dt;
      if(b.kind==='shadow')advanceChain(b,dt);
      else if(b.kind==='sewing')advanceSewing(b);
      else if(b.kind==='trap')for(const t of b.traps){t.age=b.age;if(b.age>=.9)detonate(b,t);}
      else{b.hitSets??=[];for(let i=0;i<b.spec.pulses;i++){const start=b.spec.release+i*b.spec.interval;if(b.age<start)break;pulse(b,i,Math.max(0,b.age-start));}}
      if(b.age>=b.duration||(b.kind==='shadow'&&b.chain.ended&&!b.kunai.length&&b.chain.segments.every(s=>!s.contact||!alive(s.target)||!held(s.target)||s.linked===false||s.shots>=b.spec.kunaiRounds)&&b.age>=b.spec.release+.4)){const i=casts.indexOf(b);if(i>=0)casts.splice(i,1);}
    }
    for(let i=effects.length-1;i>=0;i--){const e=effects[i];e.age=e.castRef&&casts.includes(e.castRef)?Math.max(0,e.castRef.age-e.lastPulseAt):e.age+dt;if(e.age>=e.life||e.world!==G.World||!valid(e.owner)||e.castRef&&!legal(e.castRef))effects.splice(i,1);}
    for(const s of states.values())if(s.cue){
      s.cue.action=skillAction(s,'strangle')?'strangle':skillAction(s,'sewing')?'sewing':null;
      s.cue.actionLabel=s.cue.action==='strangle'?'影首縛 · 收緊':s.cue.action==='sewing'?'影縫 · 穿刺':'';
      if(s.cue.phase==='finish'&&s.cue.action!=='strangle')s.cue.label='影術收勢';
    }
    for(const s of states.values()){
      updateShadowReturns(s,dt);
      updateReservoir(s);
      s.projection=projectionFor(s.owner,s);
      if(s.shadowReturns.length){
        for(const trail of s.shadowReturns)refreshReturnTrail(s,trail);
        s.shadowReturns=s.shadowReturns.filter(trail=>trail.remainingPoints.length>=2&&segmentPathLinked(s.owner,trail.remainingPoints,curveRegionClear(trail.remainingPoints,2,s.owner)));
        updateReservoir(s);
        s.projection=projectionFor(s.owner,s);
      }
      const projMap=new Map();
      reanchorContacts(s,projMap);
      const chain=s.lastChain;if(chain&&legal(chain)&&(casts.includes(chain)||ownedCaptures(s).length))for(const segment of chain.chain.segments)if(!segment.contact&&!segment.finished&&segment.travelled>0)refreshSegment(chain,segment);
      for(const [e]of ownedCaptures(s))if(!projMap.has(e))projMap.set(e,projectionFor(e,s));
      for(const segment of s.lastChain?.chain.segments||[])if(alive(segment.target)&&!segment.target.destructible&&!projMap.has(segment.target))projMap.set(segment.target,projectionFor(segment.target,s));
      s.projections=projMap;
    }
  }
  function tick(dt,a,now){
    if((a?.mon?.dex??a?.dex)!==DEX)return oldTick.call(this,dt,a,now);
    if(G.Game.state!=='playing'||!valid(a)||a.frozen||!Number.isFinite(dt)||dt<=0)return;
    const s=state(a);
    for(const m of a.moves||[]){if(!supports(m))continue;s.cooldowns[m.id]=Math.max(0,(s.cooldowns[m.id]||0)-dt);m.t=s.cooldowns[m.id];}
    sharedPlan(s,dt);
  }
  function drawRibbon(ctx,g,alpha=.42){
    if(g.length<.5)return;
    const root=sign=>{const x=g.ax+g.nx*g.radius*sign,y=g.ay+g.ny*g.radius*sign;if(clearPath(g.ax,g.ay,x,y))return {x,y};let low=0,high=1;for(let i=0;i<6;i++){const t=(low+high)/2;if(clearPath(g.ax,g.ay,g.ax+(x-g.ax)*t,g.ay+(y-g.ay)*t))low=t;else high=t;}return {x:g.ax+(x-g.ax)*low,y:g.ay+(y-g.ay)*low};};
    const left=root(1),right=root(-1);
    ctx.save();ctx.globalAlpha=alpha;ctx.fillStyle='#191522';ctx.strokeStyle='#6b5878';ctx.lineWidth=1;
    ctx.beginPath();ctx.moveTo(left.x,left.y);ctx.lineTo(g.bx,g.by);ctx.lineTo(right.x,right.y);ctx.closePath();ctx.fill();ctx.stroke();
    ctx.globalAlpha=.55;ctx.strokeStyle='#211a2a';ctx.lineWidth=1;ctx.lineCap='butt';ctx.beginPath();ctx.moveTo(g.ax,g.ay);ctx.lineTo(g.bx,g.by);ctx.stroke();ctx.restore();
  }
  const vfxGrain=new Float32Array(1024);
  for(let i=0;i<vfxGrain.length;i++){const v=Math.sin(i*127.1+311.7)*43758.5453;vfxGrain[i]=v-Math.floor(v);}
  const grain=i=>vfxGrain[(i&1023)];
  const px=v=>Math.round(v*.5)*2;
  function drawPaperPacket(ctx,x,y,scale=1,turn=0,heat=0,layers=1,pinned=false){
    ctx.save();ctx.translate(x,y);ctx.rotate(turn);ctx.scale(scale*.88,scale*.88);
    if(pinned){
      ctx.fillStyle='rgba(8,6,12,.45)';ctx.fillRect(-7,5,14,4);
    }
    for(let i=Math.min(4,layers)-1;i>0;i--){
      ctx.fillStyle='#8c7248';ctx.fillRect(-5+i*2,-14-i,10,21);
      ctx.fillStyle='#d8c394';ctx.fillRect(-4+i*2,-13-i,8,19);
    }
    // Crisp ninja explosive tag (Kibaku Fuda) with dark border & vermilion seal script.
    ctx.fillStyle='#4a251d';ctx.fillRect(-6,-16,12,23);
    ctx.fillStyle=heat>.5?'#fff6d6':'#f5e6be';ctx.fillRect(-5,-15,10,21);
    ctx.fillStyle='#c9b282';ctx.fillRect(-5,3,10,3);
    ctx.fillStyle=heat>.35?'#e03c28':'#a82922';
    ctx.fillRect(-1,-12,2,15);ctx.fillRect(-3,-9,6,2);ctx.fillRect(-3,-4,6,2);ctx.fillRect(-2,1,4,2);
    ctx.fillRect(-4,-13,2,2);ctx.fillRect(2,-13,2,2);
    // Compact iron kunai pin at the top of the talisman.
    ctx.fillStyle='#231f29';ctx.beginPath();ctx.moveTo(0,-27);ctx.lineTo(-4,-18);ctx.lineTo(4,-18);ctx.closePath();ctx.fill();
    ctx.fillStyle='#cfd5dc';ctx.beginPath();ctx.moveTo(0,-25);ctx.lineTo(-2.3,-19);ctx.lineTo(0,-18);ctx.closePath();ctx.fill();
    ctx.fillStyle='#8c96a3';ctx.beginPath();ctx.moveTo(0,-25);ctx.lineTo(2.3,-19);ctx.lineTo(0,-18);ctx.closePath();ctx.fill();
    ctx.fillStyle='#2a2430';ctx.fillRect(-1,-18,2,3);
    if(heat>0){
      const pulse=.65+.35*Math.sin(heat*18);
      ctx.globalAlpha=.45+.45*heat;ctx.fillStyle='#ff6a1a';ctx.fillRect(-6,-16,12,23);
      ctx.globalAlpha=1;ctx.fillStyle='#ff9d2e';ctx.fillRect(2,-18,6,6);
      ctx.fillStyle='#fff7cc';ctx.fillRect(4,-16,3,3);
      for(let i=0;i<4;i++){
        const a=i*1.57+heat*5,d=(5+5*heat)*pulse;
        ctx.fillStyle=i%2?'#ffe37a':'#ff7724';
        ctx.fillRect(Math.round(5+Math.cos(a)*d),Math.round(-15+Math.sin(a)*d),2,2);
      }
    }
    ctx.restore();
  }
  function drawShadowContact(ctx,e){
    const u=clamp01(e.age/e.life),x=e.x,y=e.y,r=(e.radius||16)*(1+.38*u);
    ctx.save();
    if(e.kind==='kunai'){
      const fade=1-u;ctx.translate(x,y-18);
      // Crisp steel-and-shadow cross slash + pixel sparks on kunai impact.
      ctx.globalAlpha=fade*.85;ctx.strokeStyle='#140f1c';ctx.lineWidth=4.5*(1-.5*u);
      ctx.beginPath();ctx.moveTo(-14-6*u,9+4*u);ctx.lineTo(14+6*u,-9-4*u);ctx.stroke();
      ctx.strokeStyle='#fff7d6';ctx.lineWidth=2*(1-.4*u);
      ctx.beginPath();ctx.moveTo(-12-5*u,8+3*u);ctx.lineTo(12+5*u,-8-3*u);ctx.stroke();
      ctx.strokeStyle='#f5c469';ctx.lineWidth=1.4*(1-.4*u);
      ctx.beginPath();ctx.moveTo(-7-3*u,-8-4*u);ctx.lineTo(7+3*u,8+4*u);ctx.stroke();
      for(let i=0;i<5;i++){
        const a=i*1.256+.4,d=6+16*u;
        ctx.fillStyle=i%2?'#fff6cc':'#ffd166';
        ctx.fillRect(px(Math.cos(a)*d)-1,px(Math.sin(a)*d)-1,2,2);
      }
    }else{
      const fade=(1-u)*(1-u);
      // Shadow splash spikes erupting around the captured enemy's ankles.
      ctx.globalAlpha=fade*.85;ctx.fillStyle='#06050a';
      for(let i=0;i<6;i++){
        const a=i*Math.PI/3+.25,bx=x+Math.cos(a)*r*.78,by=y+Math.sin(a)*r*.34,h=(10+6*(i%2))*(1-.45*u),lean=Math.cos(a)*(5+4*u);
        ctx.beginPath();ctx.moveTo(bx-3,by);ctx.lineTo(bx+lean,by-h);ctx.lineTo(bx+3,by);ctx.closePath();ctx.fill();
      }
      ctx.globalAlpha=fade*.55;ctx.strokeStyle=e.kind==='net'?'#d4b483':'#4b3b63';ctx.lineWidth=2;
      ctx.beginPath();ctx.ellipse(x,y,r*.92,r*.36,0,0,Math.PI*2);ctx.stroke();
    }
    ctx.restore();
  }
  function drawPixelCloud(ctx,cx,cy,rx,ry,color){
    const x=px(cx),y=px(cy),w=Math.max(4,px(rx)),h=Math.max(4,px(ry));
    const h1=Math.max(2,px(h*.44)),h2=Math.max(h1,px(h*.78)),w1=Math.max(2,px(w*.84)),w2=Math.max(2,px(w*.56));
    ctx.fillStyle=color;
    ctx.fillRect(x-w,y-h1,w*2,h1*2);
    if(h2>h1){ctx.fillRect(x-w1,y-h2,w1*2,h2-h1);ctx.fillRect(x-w1,y+h1,w1*2,h2-h1);}
    if(h>h2){ctx.fillRect(x-w2,y-h,w2*2,h-h2);ctx.fillRect(x-w2,y+h2,w2*2,h-h2);}
  }
  function drawShadowBlast(ctx,e,ultimate){
    const u=clamp01(e.age/e.life),growth=1-Math.pow(1-clamp01(u/(ultimate?.22:.28)),3),r=e.radius*growth,fade=Math.pow(1-u,1.1);
    const detail=(G.Settings?.fx??1)>0,seed=Math.abs(Math.round(e.x*13+e.y*29+(e.castId||1)*7))&511;
    ctx.save();
    // 1. Subtle ground scorch & radial fissures (not a dark opaque circle plate).
    ctx.globalAlpha=fade*.34;
    drawPixelCloud(ctx,e.x,e.y+2,r*.48,r*.26,'#1c1210');
    ctx.strokeStyle='#3d231a';ctx.lineWidth=2;ctx.globalAlpha=fade*.48;
    for(let i=0;i<(detail?7:4);i++){
      const a=i*Math.PI*2/(detail?7:4)+grain(seed+i)*.5,len=r*(.42+.34*grain(seed+i+20));
      ctx.beginPath();ctx.moveTo(px(e.x+Math.cos(a)*6),px(e.y+Math.sin(a)*4));
      ctx.lineTo(px(e.x+Math.cos(a+.12)*len*.55),px(e.y+Math.sin(a+.12)*len*.34));
      ctx.lineTo(px(e.x+Math.cos(a)*len),px(e.y+Math.sin(a)*len*.6));ctx.stroke();
    }
    // 2. Thin segmented shockwave arcs at true blast radius for clear gameplay boundary without a cheap solid hoop.
    ctx.globalAlpha=fade*(u<.32?.58:.32);ctx.strokeStyle=ultimate?'#ffe49e':'#f7c97e';ctx.lineWidth=ultimate?2:1.5;
    const arcs=ultimate?6:5;
    for(let i=0;i<arcs;i++){
      const a=i*Math.PI*2/arcs+u*.35+grain(seed+i+40)*.25,span=.28+.12*grain(seed+i+60)*(1-.4*u);
      ctx.beginPath();ctx.arc(e.x,e.y,r,a,a+span);ctx.stroke();
    }
    // 3. Classic pixel-art billowing fireball clusters (no origami diamond polygons!).
    const puffs=detail?(ultimate?15:10):(ultimate?9:6);
    if(u>.1){
      ctx.globalAlpha=fade*clamp01((u-.08)*3)*.55;
      for(let i=0;i<Math.ceil(puffs*.7);i++){
        const g1=grain(seed+i*7+90),g2=grain(seed+i*13+120),a=i*2.39996+g1*.5;
        const dist=r*(.2+.52*g2)*Math.pow(u,.55),lift=(12+28*g1)*u*(ultimate?1.35:1);
        const sz=(ultimate?15:10)*(.7+.55*g2)*(1+.3*u);
        drawPixelCloud(ctx,e.x+Math.cos(a)*dist,e.y+Math.sin(a)*dist*.58-lift,sz,sz*.78,'#362827');
      }
    }
    const heat=clamp01(1-u/.78);
    if(heat>0){
      const palette=['#691c17','#c9381c','#f58020','#ffd659'];
      for(let layer=0;layer<4;layer++){
        const ratio=1-layer*.2;ctx.globalAlpha=heat*(layer>=2?.94:.86);
        const count=Math.max(3,Math.round(puffs*(1-layer*.18)));
        for(let i=0;i<count;i++){
          const g1=grain(seed+layer*31+i*11),g2=grain(seed+layer*17+i*23),a=i*2.39996+layer*.38;
          const dist=r*(.04+.46*g1)*ratio*Math.pow(growth,.85);
          const lift=((ultimate?32:18)*(.2+.8*g2)*(1-layer*.1)+layer*3)*Math.sin(Math.PI*Math.min(1,u*1.35));
          const w=(ultimate?19:13)*ratio*(.65+.5*g2)*(.55+.45*heat);
          drawPixelCloud(ctx,e.x+Math.cos(a)*dist,e.y+Math.sin(a)*dist*.55-lift,w,w*.86,palette[layer]);
        }
      }
      if(ultimate){
        const spireH=Math.min(e.radius*.76,88)*Math.sin(Math.PI*Math.min(1,u*1.55)),steps=6;
        for(let s=0;s<steps;s++){
          const t=s/(steps-1),sw=Math.max(4,(1-t*.72)*r*.16*heat);
          ctx.globalAlpha=heat*(.9-.1*t);
          drawPixelCloud(ctx,e.x+Math.sin(t*4+u*8)*3,e.y-spireH*t,sw,sw*1.15,s<2?'#ffd659':s<4?'#f58020':'#c9381c');
        }
      }
    }
    if(u<.22){
      const flash=1-u/.22,fr=Math.max(6,(ultimate?22:14)*flash);
      ctx.globalAlpha=flash*.95;
      drawPixelCloud(ctx,e.x,e.y-4,fr*1.25,fr,'#ffe678');
      drawPixelCloud(ctx,e.x,e.y-4,fr*.72,fr*.62,'#fffdf0');
    }
    // 4. Pixelated flying embers & burning paper-tag scraps.
    const sparks=detail?(ultimate?16:10):6;
    ctx.globalAlpha=fade*.95;
    for(let i=0;i<sparks;i++){
      const g1=grain(seed+i*19+200),g2=grain(seed+i*29+260),a=i*Math.PI*2/sparks+(g1-.5)*.5;
      const dist=r*(.26+.74*g2)*Math.pow(u,.68),arcLift=Math.sin(Math.PI*Math.min(1,u*1.2))*(16+28*g1)*(ultimate?1.3:1);
      const sx=px(e.x+Math.cos(a)*dist),sy=px(e.y+Math.sin(a)*dist*.64-arcLift);
      if(i%4===0){
        ctx.fillStyle='#4a261e';ctx.fillRect(sx-2,sy-2,4,4);
        ctx.fillStyle='#ff8c2e';ctx.fillRect(sx,sy-2,2,2);
      }else{
        ctx.fillStyle=i%2?'#fff3b0':'#ff9929';ctx.fillRect(sx,sy,2,2);
      }
    }
    ctx.restore();
  }
  function drawGroundInk(ctx,polygon,points,seed,clock,fade=1,returning=false,maxWidth=14,rootWidth=0,owner=null,connected=false){
    if(polygon.length<3||points.length<2||fade<=0)return;
    const a=points[0],b=points[Math.min(points.length-1,2)],dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1;
    ctx.save();
    // Soft ground-bleed fringe (<127 alpha) blends the shadow edge into pixel grass/dirt.
    ctx.fillStyle='#100c1a';ctx.globalAlpha=fade*.26;
    ctx.beginPath();polygon.forEach((p,i)=>i?ctx.lineTo(px(p.x),px(p.y)+1):ctx.moveTo(px(p.x),px(p.y)+1));ctx.closePath();ctx.fill();
    // Main unified shadow mass (#040307, identical to the foot pool!).
    ctx.fillStyle='#040307';ctx.globalAlpha=fade;
    // Concave liquid-meniscus funnel bridge from inside Shikamaru's foot pool smoothly
    // into the shadow stream's left & right banks—zero round-ball lump, zero seam!
    if(owner){
      const tipPt=points.at(-1),tipDist=Math.hypot(tipPt.x-owner.x,tipPt.y-owner.y);
      const odx=a.x-owner.x,ody=a.y-owner.y,od=Math.hypot(odx,ody);
      const reachBlend=clamp01((tipDist-22)/26);
      if(reachBlend>.02&&od<56&&clearPath(owner.x,owner.y,a.x,a.y)){
        const tdx=tipPt.x-owner.x,tdy=tipPt.y-owner.y,td=Math.hypot(tdx,tdy)||1;
        const ux=od>2?odx/od:tdx/td,uy=od>2?ody/od:tdy/td,nx=-uy,ny=ux;
        const scale=owner.anim?.scale||1,poolRx=(9+7.5*reachBlend)*scale,poolRy=(5.5+4.5*reachBlend)*scale;
        // Anchor smoothly on the foot pool's shoulders and curve concavely into the stream banks.
        const sxL=owner.x+ux*3+nx*poolRx,syL=owner.y+uy*2+ny*poolRy;
        const sxR=owner.x+ux*3-nx*poolRx,syR=owner.y+uy*2-ny*poolRy;
        const idxJoin=Math.min(Math.floor(polygon.length/2)-1,Math.max(0,Math.min(3,points.length-2)));
        const pL=polygon[idxJoin],pR=polygon[polygon.length-1-idxJoin];
        const midX=owner.x+(pL.x+pR.x-2*owner.x)*.54,midY=owner.y+(pL.y+pR.y-2*owner.y)*.54;
        const neckHalf=Math.max(2.5,Math.min(maxWidth*.82,(rootWidth||10)*(.3+.14*reachBlend)));
        const ctrlL={x:midX+nx*neckHalf,y:midY+ny*neckHalf};
        const ctrlR={x:midX-nx*neckHalf,y:midY-ny*neckHalf};
        if(clearPath(owner.x,owner.y,ctrlL.x,ctrlL.y)&&clearPath(owner.x,owner.y,ctrlR.x,ctrlR.y)){
          ctx.beginPath();
          ctx.moveTo(sxL,syL);
          ctx.quadraticCurveTo(ctrlL.x,ctrlL.y,pL.x,pL.y);
          ctx.lineTo(pR.x,pR.y);
          ctx.quadraticCurveTo(ctrlR.x,ctrlR.y,sxR,syR);
          ctx.closePath();
          ctx.fill();
        }
      }
    }
    ctx.beginPath();polygon.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.closePath();ctx.fill();
    // Where the stream meets a captured enemy's foot shadow, spread finger-like shadow
    // tendrils merging seamlessly into the victim's shadow pool.
    if(connected&&points.length>2){
      const tip=points.at(-1),prev=points.at(-2),tdx=tip.x-prev.x,tdy=tip.y-prev.y,td=Math.hypot(tdx,tdy)||1;
      const tux=tdx/td,tuy=tdy/td,tnx=-tuy,tny=tux;
      ctx.beginPath();ctx.ellipse(tip.x+tux*2,tip.y+tuy*1.5,10,5.5,0,0,Math.PI*2);ctx.fill();
      for(const sgn of [-1,0,1]){
        const bx=tip.x+tnx*sgn*6,by=tip.y+tny*sgn*3.5;
        ctx.beginPath();ctx.moveTo(bx-tnx*2.5,by-tny*1.5);
        ctx.lineTo(bx+tux*9+tnx*sgn*3.5,by+tuy*5.5+tny*sgn*2);
        ctx.lineTo(bx+tnx*2.5,by+tny*1.5);ctx.closePath();ctx.fill();
      }
    }
    // Very subtle internal ink sheen so the shadow reads as living dark fluid without breaking unity with the pool.
    if(!returning&&points.length>6&&(G.Settings?.fx??1)>0){
      const startIdx=Math.min(points.length-2,Math.max(3,Math.floor(points.length*.28))),endIdx=Math.max(startIdx+1,points.length-2);
      ctx.strokeStyle='#140f21';ctx.lineWidth=1.5;ctx.lineCap='round';ctx.globalAlpha=fade*.65;
      ctx.beginPath();
      for(let i=startIdx;i<=endIdx;i++){
        const p=points[i],prev=points[i-1],dx2=p.x-prev.x,dy2=p.y-prev.y,d2=Math.hypot(dx2,dy2)||1;
        const sway=Math.sin(i*.55-clock*6.5+seed*2.3)*1.6;
        const sx=p.x-dy2/d2*sway,sy=p.y+dx2/d2*sway;
        i===startIdx?ctx.moveTo(sx,sy):ctx.lineTo(sx,sy);
      }
      ctx.stroke();
    }
    ctx.restore();
  }
  function drawAnkleBind(ctx,e,clock,tighten=0){
    const er=Math.max(9,Math.min(22,e.r||12)),x=e.x,y=e.y;
    ctx.save();
    ctx.fillStyle='#050408';ctx.globalAlpha=.92;
    ctx.beginPath();ctx.ellipse(x,y+1,er+3-2*tighten,Math.max(4,er*.38),0,0,Math.PI*2);ctx.fill();
    // Four gripping shadow talons curling up around the bound target's ankles.
    for(let i=0;i<4;i++){
      const side=i<2?-1:1,inner=i%2===0,bx=x+side*(inner?er*.48:er*.92),by=y+(inner?3:0);
      const sway=Math.sin(clock*5.2+i*1.7+(e.id||0))*.9,h=(inner?9:12)+3*tighten+sway;
      const tipX=bx-side*(inner?2.5:4.5+2*tighten);
      ctx.beginPath();ctx.moveTo(bx-2.4,by);ctx.quadraticCurveTo(bx+side*2,by-h*.55,tipX,by-h);ctx.quadraticCurveTo(bx-side*1.2,by-h*.4,bx+2.4,by);ctx.closePath();ctx.fill();
    }
    if(tighten>0){
      ctx.strokeStyle='#4e3a69';ctx.lineWidth=1.5+tighten;ctx.globalAlpha=.5+.4*tighten;
      ctx.beginPath();ctx.ellipse(x,y-2,er+6*(1-tighten),Math.max(3,er*.34),0,0,Math.PI*2);ctx.stroke();
    }
    ctx.restore();
  }
  function drawCasterArch(ctx,b,arc,remaining,behind){
    const body=Ref.bodyFor(b.owner);if(!body){if(!behind)Ref.drawArch(ctx,arc,.95,remaining,0,1,b.ultimate);return;}
    const left=b.owner.x-body.foot.x,top=b.owner.y-body.foot.y,right=left+body.width,bottom=top+body.height,rootEnd=Math.min(.65,Math.max(0,(arc.contact?.progress??1)-.04));
    ctx.save();ctx.beginPath();
    if(behind)ctx.rect(left,top,body.width,body.height);
    else{
      const margin=arc.width*3+6,minX=Math.min(left,...arc.points.map(p=>p.x))-margin,maxX=Math.max(right,...arc.points.map(p=>p.x))+margin,minY=Math.min(top,...arc.points.map(p=>p.y-p.z))-margin,maxY=Math.max(bottom,...arc.points.map(p=>p.y-p.z))+margin;
      ctx.rect(minX,minY,maxX-minX,top-minY);ctx.rect(minX,bottom,maxX-minX,maxY-bottom);
      ctx.rect(minX,top,left-minX,body.height);ctx.rect(right,top,maxX-right,body.height);
    }
    ctx.clip();Ref.drawArch(ctx,arc,.95,remaining,0,behind?rootEnd:1,b.ultimate);ctx.restore();
    // The contact end stays in front of victims, including a victim next to the
    // caster. Only the source portion passes behind the living casting body.
    if(!behind){ctx.save();ctx.beginPath();ctx.rect(left,top,body.width,body.height);ctx.clip();Ref.drawArch(ctx,arc,.95,remaining,rootEnd,1,b.ultimate);ctx.restore();}
  }
  function drawCheckmateBanner(ctx,b){
    const finished=b.age>=b.blastAt,text=finished?'勝負已定':'奈良流・詰將';
    const unroll=clamp01(b.age/.1),flash=finished?clamp01(1-(b.age-b.blastAt)/.18):0,fade=b.duration-b.age<.22?clamp01((b.duration-b.age)/.22):1;
    ctx.save();ctx.font='bold 15px "Noto Serif TC","Microsoft JhengHei",serif';ctx.textAlign='center';ctx.textBaseline='middle';
    const tw=ctx.measureText(text).width,w=Math.max(44,(tw+34)*(.35+.65*unroll)),h=26,x=Math.round(b.owner.x),y=Math.round(b.owner.y-86);
    ctx.globalAlpha=fade;
    ctx.fillStyle='rgba(8,7,13,.9)';ctx.fillRect(x-w/2,y-h/2,w,h);
    ctx.fillStyle=finished?'#63211c':'#231b30';ctx.fillRect(x-w/2+2,y-h/2+2,w-4,3);ctx.fillRect(x-w/2+2,y+h/2-5,w-4,3);
    ctx.strokeStyle=finished?'#ffd275':'#bfa36f';ctx.lineWidth=1.4+flash;ctx.strokeRect(x-w/2+.5,y-h/2+.5,w-1,h-1);
    for(const side of [-1,1]){
      const rx=x+side*(w/2+1.5);
      ctx.fillStyle='#3b231b';ctx.fillRect(rx-2,y-h/2-2,4,h+4);
      ctx.fillStyle=finished?'#ffd275':'#d1b277';ctx.fillRect(rx-2,y-h/2-3,4,3);ctx.fillRect(rx-2,y+h/2,4,3);
    }
    if(unroll>.45){
      ctx.globalAlpha=fade*clamp01((unroll-.45)/.55);
      ctx.fillStyle='#050408';ctx.fillText(text,x+1,y+1.5);
      ctx.fillStyle=flash>.3?'#fffbe0':(finished?'#ffe08c':'#f2e7cf');ctx.fillText(text,x,y+.5);
    }
    ctx.restore();
  }
  function referenceGround(ctx){
    // The reservoir is part of the living caster, not an active cast. It also
    // exists on the first frame and after clearFields, without mutating state.
    for(const actor of [G.Game.player,...(G.SelfClones?.actors?.()||[])])if(valid(actor))Ref.drawProjection(ctx,projectionFor(actor));
    const drawnTargets=new Set();
    for(const s of states.values()){
      if(!valid(s.owner)||s.world!==G.World||s.epoch!==G.CombatPulse?.epoch)continue;
      if(s.projections?.size)for(const [e,projection]of s.projections){if(drawnTargets.has(e))continue;drawnTargets.add(e);Ref.drawProjection(ctx,projection);}
      const tactics=moveFor(s.owner,'tactics');
      if(tactics&&s.plan){
        // Pure shadow-chakra wisps rising from the ready-base rim (replaces brown mud droplets).
        const strength=rank(tactics),phase=s.clock*4.2,count=3+Math.floor(strength/2);
        ctx.save();
        for(let i=0;i<count;i++){
          const a=i*Math.PI*2/count+Math.sin(phase*.4+i)*.25,rx=s.owner.x+Math.cos(a)*17,ry=s.owner.y+Math.sin(a)*9+2;
          const h=8+strength*1.8+3*Math.sin(phase+i*1.7),sway=Math.cos(phase+i)*2.5;
          ctx.globalAlpha=.78;ctx.fillStyle='#07050c';
          ctx.beginPath();ctx.moveTo(rx-3.5,ry);ctx.quadraticCurveTo(rx-sway,ry-h*.55,rx+sway,ry-h);ctx.quadraticCurveTo(rx+3.5,ry-h*.4,rx+3.5,ry);ctx.closePath();ctx.fill();
          ctx.globalAlpha=.45;ctx.fillStyle='#2f2345';ctx.fillRect(px(rx+sway)-1,px(ry-h-2),2,2);
        }
        ctx.restore();
      }
      for(const b of casts)if(b.owner===s.owner&&b.ultimate&&legal(b))for(const site of b.sites.values()){
        if(site.detonated)continue;const heat=clamp01((b.age-site.plantedAt)/Math.max(.01,b.blastAt-site.plantedAt));
        ctx.save();
        // Tactical sealing perimeter: subtle dashed vermilion-gold ticks instead of thick yellow arcs.
        ctx.strokeStyle=heat>.6?'#ff9d47':'#c98a4b';ctx.lineWidth=1.4;ctx.globalAlpha=.18+.28*heat;
        const segs=12;
        for(let i=0;i<segs;i++){const a=i*Math.PI*2/segs+heat*.25;ctx.beginPath();ctx.arc(site.x,site.y,b.spec.blastRadius,a,a+.24);ctx.stroke();}
        ctx.globalAlpha=.55+.3*heat;ctx.fillStyle='#08060d';
        for(let i=0;i<4;i++){const a=i*Math.PI/2+.78;ctx.beginPath();ctx.moveTo(site.x,site.y);ctx.lineTo(site.x+Math.cos(a-.2)*14,site.y+Math.sin(a-.2)*8);ctx.lineTo(site.x+Math.cos(a+.2)*14,site.y+Math.sin(a+.2)*8);ctx.closePath();ctx.fill();}
        ctx.restore();
        for(let i=0;i<3;i++)drawPaperPacket(ctx,site.x+(i-1)*5,site.y-2+Math.abs(i-1)*2,1.02,(i-1)*.48,heat,1,true);
      }
      const b=s.lastChain,hasChain=b&&legal(b)&&(casts.includes(b)||ownedCaptures(s).length);
      const netU=s.plan?.phase==='net'?clamp01((s.clock-s.plan.at)/Math.max(.05,profile(s.owner,moveFor(s.owner,'shadow')).netPrepare)):0;
      if(hasChain){
        for(const segment of b.chain.segments){
          if(segment.linked===false||segment.polygon.length<3)continue;
          drawGroundInk(ctx,segment.polygon,segment.grownPoints,segment.seed,s.clock,1,false,b.spec.shadowWidthMax,segment.flow?.rootWidth||b.spec.shadowWidthMin*2,s.owner,!!segment.contact);
          if(netU>0&&segment.grownPoints.length>1){
            ctx.save();ctx.strokeStyle='#4c386e';ctx.lineWidth=1.5+netU*1.8;ctx.globalAlpha=.35+.45*netU;
            ctx.beginPath();segment.grownPoints.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.stroke();ctx.restore();
          }
        }
      }
      for(const trail of s.shadowReturns){
        const fade=clamp01(1-trail.age/Math.max(.05,trail.life)*.35);
        drawGroundInk(ctx,trail.polygon,trail.remainingPoints,trail.seed,s.clock,fade,true,trail.maxWidth,trail.rootWidth||0,s.owner);
      }
      for(const [e]of ownedCaptures(s))drawAnkleBind(ctx,e,s.clock,netU);
      const armedNodes=s.board.filter(n=>legal(n.cast)&&s.clock-n.born>=n.cast.spec.trapArm);
      if(armedNodes.length>1){
        // Subtle shadow-chakra fuse threads linking Shikamaru's laid paper-bomb formation.
        ctx.save();
        for(let i=1;i<armedNodes.length;i++){
          const n0=armedNodes[i-1],n1=armedNodes[i],dist=Math.hypot(n1.x-n0.x,n1.y-n0.y);
          if(dist>165||!clearPath(n0.x,n0.y,n1.x,n1.y))continue;
          const lit=Number.isFinite(n0.blastAt)||Number.isFinite(n1.blastAt);
          ctx.strokeStyle=lit?'#ff9b3d':'#1b1429';ctx.lineWidth=lit?1.8:1.2;ctx.globalAlpha=lit?.65:.34;
          ctx.beginPath();ctx.moveTo(n0.x,n0.y+2);ctx.quadraticCurveTo((n0.x+n1.x)/2,(n0.y+n1.y)/2+6,n1.x,n1.y+2);ctx.stroke();
        }
        ctx.restore();
      }
      for(const node of armedNodes){
        const heat=Number.isFinite(node.blastAt)?clamp01(1-(node.blastAt-s.clock)/.5):0;
        if(heat>0){ctx.save();ctx.strokeStyle='#f29b43';ctx.lineWidth=1.2;ctx.globalAlpha=.28*heat;for(let i=0;i<8;i++){const a=i*Math.PI/4;ctx.beginPath();ctx.arc(node.x,node.y,node.cast.spec.radius,a,a+.28);ctx.stroke();}ctx.restore();}
        drawPaperPacket(ctx,node.x,node.y,1.02,.1,heat,Math.max(1,node.cast.spec.blastRounds-node.round),true);
      }
      for(const b of casts)if(b.owner===s.owner&&b.kind==='trap'&&legal(b)&&b.age>=.55)for(const t of b.traps)if(!t.detonated)drawPaperPacket(ctx,t.x,t.y,1.02,.1,clamp01((b.age-.55)/.5),1,true);
      for(const b of casts)if(b.owner===s.owner&&b.kind==='sewing'&&legal(b))for(const arc of b.arcs||[]){
        const age=b.age-arc.born;if(age>=0&&age<b.spec.archPrepare+b.spec.archFlight+.16){
          const progress=clamp01(age/b.spec.archPrepare),settle=clamp01(1-(age-b.spec.archPrepare-b.spec.archFlight)/.16);
          // Jagged shadow lotus burst where the sewing needle pierces out of the ground.
          ctx.save();ctx.fillStyle='#050408';ctx.globalAlpha=.85*settle;
          ctx.beginPath();ctx.ellipse(arc.source.x,arc.source.y,7+4*progress,3.2+1.5*progress,0,0,Math.PI*2);ctx.fill();
          for(let k=-1;k<=1;k++){
            const sx=arc.source.x+k*4.5,sh=(k===0?14:9)*progress*settle;
            ctx.beginPath();ctx.moveTo(sx-2.5,arc.source.y+1);ctx.lineTo(sx+k*2.5,arc.source.y-sh);ctx.lineTo(sx+2.5,arc.source.y+1);ctx.closePath();ctx.fill();
          }
          ctx.restore();
          drawCasterArch(ctx,b,arc,settle,true);
        }
      }
    }
  }
  function referenceAir(ctx){
    for(const b of casts)if(b.kind==='shadow'&&legal(b))for(const k of b.kunai||[]){
      // Crisp forged ninja kunai with tapered steel-glint wake & red ring-cord.
      ctx.save();ctx.translate(k.x,k.y-18);ctx.rotate(Math.atan2(k.vy,k.vx));
      ctx.globalAlpha=.42;ctx.fillStyle='#1b1526';ctx.beginPath();ctx.moveTo(-30,0);ctx.lineTo(-6,-2.6);ctx.lineTo(-6,2.6);ctx.closePath();ctx.fill();
      ctx.globalAlpha=.78;ctx.fillStyle='#fff6d9';ctx.beginPath();ctx.moveTo(-24,0);ctx.lineTo(-5,-1.1);ctx.lineTo(-5,1.1);ctx.closePath();ctx.fill();
      ctx.globalAlpha=1;
      // Red cloth streamer & pommel ring
      const flutter=Math.sin((b.age||0)*28+k.round*2)*2.2;
      ctx.strokeStyle='#b8322a';ctx.lineWidth=1.6;ctx.beginPath();ctx.moveTo(-14,0);ctx.quadraticCurveTo(-19,flutter,-23,flutter*.6);ctx.stroke();
      ctx.strokeStyle='#8e96a0';ctx.lineWidth=1.4;ctx.beginPath();ctx.arc(-13,0,2.1,0,Math.PI*2);ctx.stroke();
      // Wrapped grip
      ctx.fillStyle='#d9d2c5';ctx.fillRect(-11,-1.3,5,2.6);ctx.strokeStyle='#241e2b';ctx.lineWidth=1;ctx.strokeRect(-11,-1.3,5,2.6);
      // Two-tone faceted steel blade
      ctx.fillStyle='#f0f4f8';ctx.beginPath();ctx.moveTo(15,0);ctx.lineTo(-4,-3.8);ctx.lineTo(-6,0);ctx.closePath();ctx.fill();
      ctx.fillStyle='#8c96a6';ctx.beginPath();ctx.moveTo(15,0);ctx.lineTo(-6,0);ctx.lineTo(-4,3.8);ctx.closePath();ctx.fill();
      ctx.strokeStyle='#1d1824';ctx.lineWidth=1.2;ctx.beginPath();ctx.moveTo(15,0);ctx.lineTo(-4,-3.8);ctx.lineTo(-6,0);ctx.lineTo(-4,3.8);ctx.closePath();ctx.stroke();
      ctx.restore();
    }
    for(const s of states.values())if(valid(s.owner)&&s.world===G.World)for(const node of s.board){
      const b=node.cast,age=s.clock-node.born;if(!legal(b)||age<0||age>=b.spec.trapArm)continue;
      const u=clamp01(age/b.spec.trapArm),x=b.origin.x+(node.x-b.origin.x)*u,y=b.origin.y+(node.y-b.origin.y)*u-Math.sin(u*Math.PI)*50-(1-u)*18;
      ctx.save();ctx.globalAlpha=.35*(1-u);ctx.strokeStyle='#e8d5a7';ctx.lineWidth=1.5;ctx.beginPath();
      const u0=Math.max(0,u-.14);ctx.moveTo(b.origin.x+(node.x-b.origin.x)*u0,b.origin.y+(node.y-b.origin.y)*u0-Math.sin(u0*Math.PI)*50-(1-u0)*18);ctx.lineTo(x,y);ctx.stroke();ctx.restore();
      drawPaperPacket(ctx,x,y,.96,u*5.5,0);
    }
    for(const b of casts)if(b.kind==='trap'&&legal(b)&&b.age>=b.spec.release&&b.age<.55){
      const u=clamp01((b.age-b.spec.release)/(.55-b.spec.release));for(const t of b.traps)drawPaperPacket(ctx,b.origin.x+(t.x-b.origin.x)*u,b.origin.y+(t.y-b.origin.y)*u-Math.sin(u*Math.PI)*50-(1-u)*18,.96,b.aim+u*5.5,0);
    }
    for(const b of casts)if(b.kind==='sewing'&&legal(b))for(const arc of b.arcs||[]){
      const age=b.age-arc.born;if(age<0||age>b.spec.archPrepare+b.spec.archFlight+.16)continue;const remaining=clamp01(1-Math.max(0,age-b.spec.archPrepare-b.spec.archFlight)/.16);drawCasterArch(ctx,b,arc,remaining,false);
      if(arc.hit&&arc.contact){
        const contactAge=age-b.spec.archPrepare-b.spec.archFlight*arc.contact.progress,punch=clamp01(1-contactAge/.24),p=arc.contact.point;
        if(punch>0){
          // Victim's own ground shadow erupts upward into crossed piercing spikes on Sewing / Checkmate impact!
          const tx=alive(arc.target)?arc.target.x:p.x,ty=alive(arc.target)?arc.target.y:p.y;
          const th=Math.max(26,Math.min(58,(arc.target?.bodyH||28)*1.35))*Math.sin(Math.PI*Math.min(1,(1-punch)*2.2+.18));
          ctx.save();ctx.globalAlpha=Math.min(1,punch*1.15);
          for(const [offX,leanX,scaleH]of [[-6,9,.84],[0,-3,1.06],[6,-9,.88]]){
            const bx=tx+offX,by=ty+2,sh=th*scaleH;
            ctx.fillStyle='#050408';
            ctx.beginPath();ctx.moveTo(bx-3.2,by);ctx.lineTo(bx+leanX,by-sh);ctx.lineTo(bx+3.2,by);ctx.closePath();ctx.fill();
            ctx.strokeStyle=b.ultimate?'#6e2c3e':'#36284f';ctx.lineWidth=1.1;
            ctx.beginPath();ctx.moveTo(bx,by-2);ctx.lineTo(bx+leanX*.88,by-sh+3);ctx.stroke();
          }
          ctx.translate(p.x,p.y-p.z);ctx.globalAlpha=punch;
          ctx.fillStyle='#07050c';
          ctx.beginPath();ctx.moveTo(-14-6*(1-punch),10);ctx.lineTo(0,-2);ctx.lineTo(14+6*(1-punch),-12);ctx.lineTo(2,2);ctx.closePath();ctx.fill();
          ctx.strokeStyle=b.ultimate?'#ffd27d':'#e6d4ff';ctx.lineWidth=1.8;
          ctx.beginPath();ctx.moveTo(-10-5*(1-punch),8);ctx.lineTo(10+5*(1-punch),-10);ctx.stroke();
          ctx.beginPath();ctx.moveTo(-6,-7);ctx.lineTo(6,6);ctx.stroke();
          for(let i=0;i<4;i++){const a=i*1.57+.4,d=5+11*(1-punch);ctx.fillStyle=i%2?'#09070f':(b.ultimate?'#ffb85c':'#9f87c4');ctx.fillRect(px(Math.cos(a)*d)-1,px(Math.sin(a)*d)-1,2,2);}
          ctx.restore();
        }
      }
    }
    for(const e of effects){
      if(e.owner&&(!valid(e.owner)||e.world!==G.World)||e.castRef&&!legal(e.castRef))continue;
      if(e.kind==='explosion'||e.kind==='checkmate-blast')drawShadowBlast(ctx,e,e.kind==='checkmate-blast');
      else if(e.kind==='shadow'||e.kind==='kunai'||e.kind==='net')drawShadowContact(ctx,e);
      else if(e.kind==='strangle'&&e.castRef)drawStrangleActor(ctx,e.target,e,e.castRef,1);
    }
    const s=states.get(G.Game.player),b=s?.ultimate;
    if(b&&legal(b)&&b.age<b.duration)drawCheckmateBanner(ctx,b);
  }
  function drawGround(ctx){
    for(const a of [G.Game.player,...(G.SelfClones?.actors?.()||[])])if(valid(a)){
      const visual=shadowVisualFor(a);ctx.save();ctx.fillStyle='#242126';ctx.globalAlpha=.78;ctx.beginPath();ctx.arc(visual.x,visual.y,visual.poolRadius,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#39363a';ctx.lineWidth=1;ctx.globalAlpha=.5;ctx.stroke();ctx.restore();
    }
    for(const s of states.values()){
      const b=s.lastChain;if(!b||!legal(b)||!casts.includes(b)&&!ownedCaptures(s).length)continue;
      ctx.save();ctx.fillStyle='#242126';ctx.globalAlpha=.84;
      for(const segment of b.chain.segments){
        if(segment.linked===false)continue;if(segment.polygon.length<3)continue;
        ctx.beginPath();segment.polygon.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.closePath();ctx.fill();
      }ctx.restore();
    }
    for(const b of casts){if(!legal(b))continue;const p=b.spec;
      ctx.save();ctx.lineCap='round';ctx.lineJoin='round';
      if(b.kind==='trap')for(const t of b.traps){if(t.detonated||b.age<.55)continue;ctx.save();ctx.translate(t.x,t.y);ctx.rotate(.22);ctx.fillStyle='#e9d6a1';ctx.fillRect(-6,-10,12,20);ctx.strokeStyle='#663927';ctx.lineWidth=2;ctx.strokeRect(-6,-10,12,20);ctx.fillStyle='#613c35';ctx.fillRect(-2,-6,4,11);ctx.fillStyle='#ffb353';ctx.fillRect(3,-12,3,3);ctx.restore();}
      ctx.restore();
    }
    for(const [e,l]of leases){if(!held(e))continue;ctx.save();ctx.fillStyle='#242126';ctx.beginPath();ctx.ellipse(e.x,e.y,(e.r||12)+8,9,0,0,Math.PI*2);ctx.fill();
      // Possession stays at the ankles; neither needles nor a neck-hand belong here.
      ctx.strokeStyle='#312a32';ctx.lineWidth=3;ctx.beginPath();ctx.ellipse(e.x,e.y-3,(e.r||12)+3,4,-.15,0,Math.PI*2);ctx.stroke();ctx.beginPath();ctx.moveTo(e.x-(e.r||12),e.y+2);ctx.quadraticCurveTo(e.x,e.y-7,e.x+(e.r||12),e.y);ctx.stroke();ctx.restore();}
    for(const s of states.values())if(s.plan?.phase==='net'){
      const u=Math.min(1,(s.clock-s.plan.at)/profile(s.owner,moveFor(s.owner,'shadow')).netPrepare);
      ctx.save();ctx.strokeStyle='#a99aba';ctx.lineWidth=2;ctx.globalAlpha=.45+.5*u;
      for(const [e]of ownedCaptures(s)){
        const radius=(e.r||12)+28*(1-u)+4;ctx.beginPath();ctx.ellipse(e.x,e.y,radius,radius*.5,0,0,Math.PI*2);ctx.stroke();
      }
      ctx.strokeStyle='#3f393f';ctx.lineWidth=2+u*2;
      for(const segment of s.lastChain?.chain.segments||[]){if(segment.linked===false||!segment.grownPoints.length)continue;ctx.beginPath();segment.grownPoints.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.stroke();}
      ctx.restore();
    }
    for(const s of states.values())for(const node of s.board){
      if(!legal(node.cast))continue;
      const age=s.clock-node.born,b=node.cast;
      if(age<b.spec.trapArm)continue;
      ctx.save();ctx.translate(node.x,node.y);ctx.rotate(.2);ctx.fillStyle='#ead7a3';ctx.fillRect(-7,-10,14,20);ctx.strokeStyle='#65402e';ctx.lineWidth=1.5;ctx.strokeRect(-7,-10,14,20);ctx.fillStyle='#713d33';ctx.fillRect(-2,-6,4,12);
      // More blast rounds are physical layered paper packets, never shadow explosions.
      for(let i=1;i<b.spec.blastRounds;i++){ctx.fillStyle='#c5b57f';ctx.fillRect(7+i*2,-7,2,17);}
      ctx.restore();ctx.save();ctx.strokeStyle=Number.isFinite(node.blastAt)?'#ffbe66':'#997d67';ctx.globalAlpha=Number.isFinite(node.blastAt)?.6:.2;ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(node.x,node.y,b.spec.radius,0,Math.PI*2);ctx.stroke();ctx.restore();
    }
  }
  function sewingVisualFor(b,target,visual=null){
    if(!legal(b))return null;
    const interval=b.spec.interval,retract=Math.min(.095,interval*.58),prepare=Math.min(.06,interval*.35);
    const since=visual?visual.age:Infinity,until=b.spec.release+b.emitted*interval-b.age;
    let height=0,stage='rest';
    if(since<retract){height=1-since/retract;stage=since<EPS?'contact':'withdraw';}
    else if(casts.includes(b)&&alive(target)&&b.emitted<b.spec.pulses&&until>=0&&until<=prepare){height=1-until/prepare;stage='rise';}
    const x=alive(target)?target.x:visual?.x,y=alive(target)?target.y:visual?.y;if(!Number.isFinite(x)||!Number.isFinite(y))return null;
    const bodyH=visual?.bodyH||target.bodyH||28;
    return {kind:'sewing',stage,x,y,height,maximum:Math.max(48,Math.min(112,bodyH+30)),pulseIndex:visual?.pulseIndex||b.emitted+1,retract,prepare};
  }
  function effectVisualFor(e){
    if(!e?.castRef||!legal(e.castRef))return null;
    if(e.kind==='sewing')return sewingVisualFor(e.castRef,e.target,e);
    if(e.kind==='strangle'){
      const b=e.castRef,y=alive(e.target)?e.target.y:e.y,tight=Math.max(0,1-e.age/Math.min(.16,b.spec.interval*.7));
      return {kind:e.kind,stage:e.age<EPS?'tighten':'hold',x:alive(e.target)?e.target.x:e.x,y,neckY:y-Math.max(12,e.bodyH*.65),progress:1,tight,close:Math.min(1,.45+.3*e.pulseIndex/b.spec.pulses+.25*tight),pulseIndex:e.pulseIndex};
    }
    return {kind:e.kind,stage:'contact',x:e.x,y:e.y,pulseIndex:e.pulseIndex};
  }
  function drawSewingActor(ctx,b,target,visual){
    const sample=sewingVisualFor(b,target,visual);if(!sample||sample.height<=0)return;
    const {x,y,height,maximum}=sample;
    const radius=target.r||12,pulse=visual?.pulseIndex||b.emitted+1;
    ctx.save();ctx.globalAlpha=1;ctx.fillStyle='#242126';
    for(let i=0;i<3;i++){
      const base=x+(i-1)*Math.min(15,radius*.7),floor=y+Math.abs(i-1)*3,h=maximum*height*(i===1?1:.78),lean=(i-1)*(13+3*(pulse%2));
      ctx.beginPath();ctx.moveTo(base-6,floor);ctx.bezierCurveTo(base-11,floor-h*.35,base+lean-3,floor-h*.76,base+lean,floor-h);ctx.bezierCurveTo(base+lean+6,floor-h*.52,base+9,floor-h*.16,base+7,floor);ctx.closePath();ctx.fill();
      ctx.strokeStyle='#51484e';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(base+3,floor-3);ctx.quadraticCurveTo(base+lean+3,floor-h*.48,base+lean,floor-h+4);ctx.stroke();
    }ctx.restore();
  }
  function drawStrangleActor(ctx,target,visual,b,progress){
    if(!legal(b))return;
    const x=alive(target)?target.x:visual?.x??target.x,y=alive(target)?target.y:visual?.y??target.y,bodyH=visual?.bodyH||target.bodyH||28;
    const scale=Math.max(.75,Math.min(1.7,bodyH/44)),neck=y-Math.max(12,bodyH*.65)*progress;
    const since=visual?.age??Infinity,tight=Number.isFinite(since)?Math.max(0,1-since/Math.min(.16,b.spec.interval*.7)):0;
    ctx.save();ctx.globalAlpha=visual?Math.min(1,Math.max(0,(visual.life-visual.age)/.16)):1;ctx.strokeStyle='#242126';ctx.lineWidth=(5+2*tight)*scale;
    ctx.beginPath();ctx.moveTo(x-7*scale,y);ctx.bezierCurveTo(x-18*scale,y-8*scale,x+17*scale,neck+10*scale,x+2*scale,neck);ctx.stroke();
    // Unlike ground nets or piercing needles, this is one continuous rising arm.
    for(let i=0;i<2;i++){const h=(y-neck)*(i+1)/3;ctx.beginPath();ctx.ellipse(x,y-h,Math.max(5,(target.r||12)*(1-.15*tight)),4*scale,.2*(i%2?1:-1),0,Math.PI*1.8);ctx.stroke();}
    if(progress>.5){
      ctx.translate(x,neck);ctx.scale(scale,scale);const close=visual?effectVisualFor(visual).close:.45;ctx.fillStyle='#242126';ctx.fillRect(-4,-2,12,10);ctx.lineWidth=3;ctx.lineCap='round';
      for(let i=0;i<4;i++){const fx=-4+i*3;ctx.beginPath();ctx.moveTo(fx,2);ctx.bezierCurveTo(fx-7*(1-close),-10,fx-5*close,-8,fx-7*close,1+2*close);ctx.stroke();}
      ctx.beginPath();ctx.moveTo(7,6);ctx.quadraticCurveTo(13-5*close,1,7-4*close,-2);ctx.stroke();
    }ctx.restore();
  }
  function drawAir(ctx){
    const sewingActors=new Map();
    for(const b of casts)if(b.kind==='sewing'&&legal(b)){const targets=new Set(b.followChain.chain.segments.filter(s=>s.contact&&s.linked!==false).map(s=>s.target));sewingActors.set(b,targets);}
    for(const e of effects)if(e.kind==='sewing'&&e.castRef&&legal(e.castRef)){if(!sewingActors.has(e.castRef))sewingActors.set(e.castRef,new Set());sewingActors.get(e.castRef).add(e.target);}
    for(const [b,targets]of sewingActors)for(const target of targets)drawSewingActor(ctx,b,target,effects.find(e=>e.kind==='sewing'&&e.castId===b.serial&&e.target===target));
    for(const b of casts)if(b.kind==='strangle'&&legal(b)&&b.age<b.spec.release+.08){
      const seen=new Set();for(const ray of b.rays){const target=ray.target;if(seen.has(target)||!alive(target)||!held(target))continue;seen.add(target);drawStrangleActor(ctx,target,null,b,Math.min(1,b.age/(b.spec.release+.08)));}
    }
    for(const s of states.values())for(const node of s.board){const b=node.cast,age=s.clock-node.born;if(!legal(b)||age>=b.spec.trapArm)continue;
      const u=age/b.spec.trapArm,x=b.origin.x+(node.x-b.origin.x)*u,y=b.origin.y+(node.y-b.origin.y)*u-Math.sin(u*Math.PI)*35;
      ctx.save();ctx.translate(x,y);ctx.rotate(u*8);ctx.fillStyle='#c5cbd2';ctx.beginPath();ctx.moveTo(12,0);ctx.lineTo(-6,-5);ctx.lineTo(-6,5);ctx.closePath();ctx.fill();ctx.fillStyle='#ead7a3';ctx.fillRect(-15,-4,9,16);ctx.fillStyle='#713d33';ctx.fillRect(-11,0,2,9);ctx.restore();
    }
    for(const b of casts)if(b.kind==='trap'&&legal(b)&&b.age>=b.spec.release&&b.age<.55){
      const u=Math.min(1,(b.age-b.spec.release)/(.55-b.spec.release));
      for(const t of b.traps){ctx.save();ctx.translate(b.origin.x+(t.x-b.origin.x)*u,b.origin.y+(t.y-b.origin.y)*u-24-Math.sin(u*Math.PI)*35);ctx.rotate(b.aim+u*5);ctx.fillStyle='#c8cbd1';ctx.beginPath();ctx.moveTo(12,0);ctx.lineTo(-4,-5);ctx.lineTo(-4,5);ctx.closePath();ctx.fill();ctx.strokeStyle='#3c3544';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(-4,0);ctx.lineTo(-12,0);ctx.stroke();ctx.fillStyle='#ead7a3';ctx.fillRect(-19,-4,8,15);ctx.fillStyle='#763c36';ctx.fillRect(-16,-1,2,8);ctx.restore();}
    }
    for(const e of effects){
      if(e.kind==='sewing')continue;
      const t=e.age/e.life;ctx.save();ctx.globalAlpha=1-t;
      if(e.kind==='explosion'){
        ctx.fillStyle='#e58b38';for(let i=0;i<9;i++){const a=i*Math.PI*2/9,d=e.radius*t;ctx.beginPath();ctx.arc(e.x+Math.cos(a)*d,e.y+Math.sin(a)*d-12,12*(1-t)+3,0,Math.PI*2);ctx.fill();}
        ctx.strokeStyle='#ffd59b';ctx.lineWidth=4;ctx.beginPath();ctx.ellipse(e.x,e.y,e.radius*t,e.radius*t*.55,0,0,Math.PI*2);ctx.stroke();
      }else if(e.kind==='net'){
        const r=e.radius*(1-.7*t);ctx.strokeStyle='#302137';ctx.lineWidth=7*(1-t)+2;
        ctx.beginPath();ctx.ellipse(e.x,e.y,r,r*.5,0,0,Math.PI*2);ctx.stroke();
        for(const sign of [-1,1]){ctx.beginPath();ctx.moveTo(e.x-sign*r,e.y-r*.4);ctx.quadraticCurveTo(e.x,e.y+8*(1-t),e.x+sign*r,e.y+r*.4);ctx.stroke();}
      }else if(e.kind==='strangle'){
        drawStrangleActor(ctx,e.target,e,e.castRef,1);
      }else{
        const x=alive(e.target)?e.target.x:e.x,y=alive(e.target)?e.target.y:e.y,r=e.radius||12;
        ctx.strokeStyle='#302a31';ctx.lineWidth=3;ctx.beginPath();ctx.ellipse(x,y-2,r,4,-.18,0,Math.PI*2);ctx.stroke();ctx.beginPath();ctx.moveTo(x-r,y+2);ctx.quadraticCurveTo(x,y-6,x+r,y);ctx.stroke();
      }
      ctx.restore();
    }
    const s=states.get(G.Game.player),cue=s?.cue;
    if(s&&cue&&valid(s.owner)&&s.plan){
      const text=(cue.actionLabel?cue.actionLabel+'｜':'')+cue.label+(cue.remaining>0?' '+cue.remaining.toFixed(1)+'s':'');ctx.save();ctx.font='bold 10px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';
      const w=ctx.measureText(text).width+14,x=s.owner.x,y=s.owner.y+30;
      ctx.fillStyle='rgba(20,18,28,.82)';ctx.fillRect(x-w/2,y-10,w,20);ctx.fillStyle=cue.phase==='net'||cue.phase==='blast'?'#ffda91':'#e4d8ed';ctx.fillText(text,x,y);ctx.restore();
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
  C.drawGroundFields=function(ctx){oldGround.call(this,ctx);referenceGround(ctx);};C.drawAirFields=function(ctx){oldAir.call(this,ctx);referenceAir(ctx);};
  const nativeShadow=G.Sprites.drawShadow;
  G.Sprites.drawShadow=function(ctx,dex,x,y,scale){
    if(dex===DEX)return;
    for(const s of states.values())if(s.projections?.size)for(const e of s.projections.keys())if(e.dex===dex&&e.x===x&&e.y===y)return;
    return nativeShadow.call(this,ctx,dex,x,y,scale);
  };
  function statusFor(a,m){
    const s=states.get(a);if(!s)return {label:'影網待命',fraction:0};
    if(m?.digiMode==='shikamaru-tactics')return {label:'戰術被動',fraction:0};
    if(m?.digiMode==='shikamaru-checkmate'){const b=s.ultimate,cd=profile(a,m).cd,remaining=s.cooldowns[m.id]||0;return {label:b&&legal(b)&&b.age<b.duration?(b.age<b.blastAt?'詰將連刺':'終局爆破'):remaining>0?'詰將 '+Math.ceil(remaining)+'s':'待收網・詰將',fraction:1-Math.min(1,remaining/cd)};}
    const c=s.cue;if(!c)return {label:'影網待命',fraction:0};
    const kind=m?.digiMode?.replace('shikamaru-',''),label=kind==='trap'?(c.phase==='blast'&&s.plan?.nodes?'連爆':'札'+c.board):kind==='sewing'?(skillAction(s,'sewing')?'影縫刺擊':'待接影縫'):kind==='strangle'?(skillAction(s,'strangle')?'首縛收緊':'待收網'):c.phase==='net'?'收網':c.phase==='recover'?'整備':'捕捉'+c.captured;
    return {label,fraction:c.phase==='drag'?Math.max(0,Math.min(1,1-c.remaining/2.4)):c.phase==='net'?Math.max(0,Math.min(1,1-c.remaining/.28)):c.phase==='blast'?1:0};
  }
  function skillAction(s,kind){
    for(const b of casts)if(b.owner===s.owner&&b.kind===kind&&legal(b)){
      if(kind==='sewing'&&((b.arcs||[]).some(arc=>!arc.blocked&&arc.progress<1&&alive(arc.target))||b.emitted<b.spec.pulses&&b.followChain.chain.segments.some(seg=>seg.contact&&alive(seg.target)&&chainConnected(b.followChain,seg.target))))return b;
      if(kind==='strangle'&&b.rays.some(ray=>alive(ray.target)&&held(ray.target)))return b;
    }
    const visual=effects.find(e=>e.owner===s.owner&&e.kind===kind&&e.castRef&&legal(e.castRef)&&(kind!=='sewing'||sewingVisualFor(e.castRef,e.target,e)?.height>0));return visual?.castRef||null;
  }
  function sewingPoseFor(a,s,p){
    const pose=s?.sewingPose;if(!pose||!moveFor(a,'sewing'))return null;
    const cast=casts.findLast(b=>b.owner===a&&b.kind==='sewing'&&!b.ultimate&&legal(b));if(!cast)return null;
    const duration=cast.spec.archPrepare+cast.spec.archFlight+.1,arc=cast.arcs.findLast(arc=>!arc.blocked&&cast.age-arc.born<duration),local=arc?Math.max(0,cast.age-arc.born):cast.age;
    if(!arc&&cast.emitted>=cast.spec.pulses)return null;
    const stage=!arc||local<cast.spec.archPrepare?'ground':local>=cast.spec.archPrepare+cast.spec.archFlight?'recover':arc.phase;
    return {...pose,stage,phaseAge:local,phaseDuration:arc?duration:cast.spec.release+cast.spec.archPrepare,age:local,duration,moving:s.moving,aim:cast.aim};
  }
  G.NarutoShikamaru={version:7,dex:DEX,supports,profile,canCast,cast,update,clear,held,stopped,clearPath,segmentDistance,statusFor,shadowVisualFor,ribbonGeometry,ribbonContains,polygonContains,sewingVisualFor,effectVisualFor,projectionFor,
    activeFor:a=>{const s=states.get(a),p=s?.plan,throwing=s?.throwPose,sewing=sewingPoseFor(a,s,p);if(s?.ultimate&&legal(s.ultimate)&&s.ultimate.age<s.ultimate.duration)return {kind:'checkmate',phase:'checkmate',phaseAge:s.ultimate.age,phaseDuration:s.ultimate.duration,age:s.ultimate.age,duration:s.ultimate.duration,moving:s.moving,aim:a.aim||0};if(sewing)return sewing;if(throwing&&s.clock-throwing.started<throwing.duration)return {...throwing,phaseAge:s.clock-throwing.started,phaseDuration:throwing.duration,age:s.clock-throwing.started,moving:s.moving};if(p){const m=moveFor(a,'shadow'),spec=profile(a,m),duration={prepare:spec.release,release:spec.captureWindow-spec.release,drag:spec.dragTimeout,net:spec.netPrepare,blast:Math.max(.4,(p.end||s.clock)-p.at),finish:p.finishDuration||.65,recover:spec.recoverTime}[p.phase];return {kind:p.phase==='finish'&&skillAction(s,'strangle')?'strangle':'shadow',phase:p.phase,phaseAge:s.clock-p.at,phaseDuration:duration,age:s.clock-p.at,duration,moving:s.moving,aim:a.aim||0};}const b=s?.pose;return b&&legal(b)&&b.age<.65?{...b,kind:b.kind,age:b.age,duration:.65}:null;},
    stateFor:(a=G.Game.player)=>states.get(a)||null,stats:(a=G.Game.player)=>{const s=states.get(a);return s?{casts:{...s.casts},hits:s.hits,damage:s.damage,bound:s.bound,detonations:s.detonations,contacts:s.contacts.slice(),phase:s.plan?.phase||'ready',cycles:s.cycles,travelled:s.travelled,dragged:s.dragged,board:s.board.length}:null;},
    get casts(){return casts;},get leases(){return leases;},get effects(){return effects;}};
})();
