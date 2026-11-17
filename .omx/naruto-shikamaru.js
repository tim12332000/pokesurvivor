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
  function state(a){let s=states.get(a);if(s&&s.world!==G.World){clear(a);s=null;}if(!s){s={owner:a,world:G.World,clock:0,cooldowns:{},pose:null,casts:{},hits:0,damage:0,bound:0,detonations:0,contacts:[],board:[],plan:null,walkDistance:0,prevX:a.x,prevY:a.y,moving:false,travelled:0,dragged:0,cycles:0,sewingQueued:false};states.set(a,s);}return s;}
  function profile(a,m){
    const L=rank(m),Q=Math.max(0,Math.min(16,Math.floor(G.Quantity?.bonus(a)??a.quantityPicks??a.quantityBonus??0)));
    const tactics=a.moves?.find(x=>x.digiMode==='shikamaru-tactics'),T=tactics?rank(tactics):0;
    const kind=(m?.digiMode||'shikamaru-shadow').replace('shikamaru-','');
    const ultimate=kind==='checkmate';
    return {kind,L,Q,T,range:(m?.range||300)+24*(L-1)+12*Q,
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
  function projectionFor(actor){
    const body=Ref.bodyFor(actor);if(!body)return null;
    const height=body.bodyHeight;
    const dx=-.45,dy=.9,length=height*.92,across=valid(actor)?.6:.85;
    return Ref.project(actor,dx,dy,length,across,clearPath);
  }
  function legal(b){return !b.cancelled&&valid(b.owner)&&b.world===G.World&&states.get(b.owner)===b.state&&learned(b.owner,b.m.id);}
  function chainConnected(b,e){const chain=b.followChain||b;if(!chain.chain)return clearPath(b.owner.x,b.owner.y,e.x,e.y);if(!legal(chain))return false;const index=chain.chain.segments.findIndex(s=>s.target===e&&s.contact);return index>=0&&chain.chain.segments[index].linked!==false;}
  function held(e){const l=leases.get(e);return !!l&&legal(l.cast)&&alive(e)&&l.until>l.cast.state.clock&&chainConnected(l.cast,e);}
  const stopped=e=>held(e)&&!strong(e);
  function canCast(a,m){if(!valid(a)||a.frozen||!supports(m)||m.digiMode==='shikamaru-tactics'||m.digiMode==='shikamaru-strangle')return false;const s=state(a),p=profile(a,m);if((s.cooldowns[m.id]||0)>EPS)return false;if(p.kind==='shadow'&&(casts.some(b=>b.owner===a&&b.kind==='shadow'&&legal(b)&&!b.chain?.ended)||ownedCaptures(s).length))return false;if(p.kind==='sewing'||p.kind==='checkmate')return !!s.lastChain&&legal(s.lastChain)&&s.lastChain.chain.segments.some(x=>x.contact&&alive(x.target)&&chainConnected(s.lastChain,x.target)&&(p.kind!=='checkmate'||held(x.target)&&leases.get(x.target)?.cast.owner===a));const t=targets(a,p);return t.length>0;}
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
    const shadow=projectionFor(target),destination=shadow?.points.reduce((best,p)=>!best||Math.hypot(p.x-origin.x,p.y-origin.y)<Math.hypot(best.x-origin.x,best.y-origin.y)?p:best,null)||target;
    const seed=b.serial*1.713+(b.chain?.segments.length||0)*2.391,dx=destination.x-origin.x,dy=destination.y-origin.y,d=Math.hypot(dx,dy),nx=d?-dy/d:0,ny=d?dx/d:1;
    const points=[{...origin}],steps=Math.max(3,Math.ceil(d/5));let blocked=false;
    for(let i=1;i<=steps;i++){
      const u=i/steps,envelope=Math.sin(Math.PI*u),bend=envelope*(Math.sin(seed+u*4.7)*Math.min(35,d*.16)+Math.sin(seed*1.9+u*11.3)*Math.min(10,d*.045));
      let point={x:origin.x+dx*u+nx*bend,y:origin.y+dy*u+ny*bend},previous=points[points.length-1];
      if(!clearPath(previous.x,previous.y,point.x,point.y))point={x:origin.x+dx*u,y:origin.y+dy*u};
      if(!clearPath(previous.x,previous.y,point.x,point.y)){blocked=true;break;}
      points.push(point);
    }
    let totalLength=0;for(let i=1;i<points.length;i++)totalLength+=Math.hypot(points[i].x-points[i-1].x,points[i].y-points[i-1].y);
    return {index:b.chain?.segments.length||0,seed,origin:{...origin},sourceOffset:sourceActor?{x:origin.x-sourceActor.x,y:origin.y-sourceActor.y}:null,sourceActor,target,path:points,totalLength,travelled:0,grownPoints:[{...origin}],polygon:[],contact:false,contactPoint:null,blocked};
  }
  function chainMesh(segment,radius){
    const points=segment.grownPoints,left=[],right=[];let total=0,passed=0;
    for(let i=1;i<points.length;i++)total+=Math.hypot(points[i].x-points[i-1].x,points[i].y-points[i-1].y);
    for(let i=0;i<points.length;i++){
      if(i)passed+=Math.hypot(points[i].x-points[i-1].x,points[i].y-points[i-1].y);
      const prev=points[Math.max(0,i-1)],next=points[Math.min(points.length-1,i+1)],dx=next.x-prev.x,dy=next.y-prev.y,d=Math.hypot(dx,dy)||1,u=total?passed/total:0;
      const taper=Math.min(1,Math.max(0,(total-passed)/10)),width=Math.min(2.5,radius*.095)*taper;
      const edge=sign=>{const ox=-dy/d*width*sign,oy=dx/d*width*sign;let fraction=1;if(!clearPath(points[i].x,points[i].y,points[i].x+ox,points[i].y+oy)){let low=0,high=1;for(let step=0;step<5;step++){const t=(low+high)/2;if(clearPath(points[i].x,points[i].y,points[i].x+ox*t,points[i].y+oy*t))low=t;else high=t;}fraction=low;}return {x:points[i].x+ox*fraction,y:points[i].y+oy*fraction};};
      left.push(edge(1));right.push(edge(-1));
    }
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
    const root={x:source.x+(alive(segment.sourceActor)?segment.sourceOffset?.x||0:0),y:source.y+(alive(segment.sourceActor)?segment.sourceOffset?.y||0:0)},start=grown[0],end=grown.at(-1);
    const tip=segment.contact&&alive(segment.target)&&grown.length>1?{x:segment.target.x+(segment.contactOffset?.x||0),y:segment.target.y+(segment.contactOffset?.y||0)}:end;
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
    segment.grownPoints=grown;segment.polygon=chainMesh(segment,b.spec.radius);
    segment.linked=!grown.some((p,i,list)=>i&&!clearPath(list[i-1].x,list[i-1].y,p.x,p.y));
  }
  function reanchorContacts(s){
    const b=s.lastChain;if(!b||!legal(b))return;
    for(const segment of b.chain.segments){
      if(!segment.contact||!alive(segment.target))continue;
      const e=segment.target,projection=projectionFor(e),old={x:e.x+(segment.contactOffset?.x||0),y:e.y+(segment.contactOffset?.y||0)};
      if(projection&&!Ref.contains(projection,old.x,old.y)){
        const previous=segment.grownPoints.at(-2)||segment.origin;
        const point=projection.points.reduce((best,p)=>clearPath(previous.x,previous.y,p.x,p.y)&&(!best||Math.hypot(p.x-old.x,p.y-old.y)<Math.hypot(best.x-old.x,best.y-old.y))?p:best,null);
        if(!point){segment.linked=false;leases.delete(e);continue;}
        segment.contactOffset={x:point.x-e.x,y:point.y-e.y};segment.liveContactPoint={...point};
        for(const next of b.chain.segments)if(next.sourceActor===e)next.sourceOffset={...segment.contactOffset};
      }
      refreshSegment(b,segment);
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
      const projection=projectionFor(e),contact=e.destructible?(polygonContains(segment.polygon,e.x,e.y,e.r||0)?{x:e.x,y:e.y}:null):Ref.groundContact(projection,segment.polygon,polygonContains);
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
  function update(dt){
    if(G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    Ref.beginFrame?.();
    for(const [a,s]of states){if(!valid(a)||s.world!==G.World||(s.plan&&!moveFor(a,'shadow'))){clear(a);continue;}s.clock+=dt;if(s.pose&&s.pose.age>=.65)s.pose=null;
      const chain=s.lastChain;if(chain&&legal(chain))for(const segment of chain.chain.segments)if(segment.contact){refreshSegment(chain,segment);if(!segment.linked){leases.delete(segment.target);segment.finished=true;}}
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
      reanchorContacts(s);
      s.projection=projectionFor(s.owner);const targets=new Set(ownedCaptures(s).map(([e])=>e));
      for(const segment of s.lastChain?.chain.segments||[])if(alive(segment.target)&&!segment.target.destructible)targets.add(segment.target);
      s.projections=new Map([...targets].map(e=>[e,projectionFor(e)]));
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
  function drawPaperPacket(ctx,x,y,scale=1,turn=0,heat=0,layers=1){
    ctx.save();ctx.translate(x,y);ctx.rotate(turn);ctx.scale(scale,scale);
    for(let i=layers-1;i>0;i--){ctx.fillStyle='#bba16d';ctx.fillRect(-6+i*2,-17-i,12,28);}
    ctx.fillStyle='#fff0c7';ctx.strokeStyle='#6e392c';ctx.lineWidth=1.5;ctx.fillRect(-6,-18,12,28);ctx.strokeRect(-6,-18,12,28);
    ctx.fillStyle='#a63128';ctx.fillRect(-1,-14,2,20);ctx.fillRect(-4,-9,8,2);ctx.fillRect(-4,-1,8,2);ctx.fillRect(-3,5,6,2);
    ctx.fillStyle='#d8d6c7';ctx.strokeStyle='#38313b';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(0,-31);ctx.lineTo(-4,-21);ctx.lineTo(4,-21);ctx.closePath();ctx.fill();ctx.stroke();ctx.beginPath();ctx.moveTo(0,-21);ctx.lineTo(0,-16);ctx.stroke();
    if(heat>0){ctx.fillStyle='#ff9236';ctx.beginPath();ctx.arc(6,-19,3+2*heat,0,Math.PI*2);ctx.fill();ctx.fillStyle='#fff0b3';ctx.fillRect(4,-21,3,3);ctx.strokeStyle='#ffd57e';for(let i=0;i<3;i++){const a=i*Math.PI*2/3+heat*2;ctx.beginPath();ctx.moveTo(6+Math.cos(a)*4,-19+Math.sin(a)*4);ctx.lineTo(6+Math.cos(a)*(7+3*heat),-19+Math.sin(a)*(7+3*heat));ctx.stroke();}}
    ctx.restore();
  }
  function drawShadowContact(ctx,e){
    const u=Math.min(1,e.age/e.life),x=e.x,y=e.y,r=(e.radius||16)*(1+.45*u);
    ctx.save();ctx.globalAlpha=(1-u)*.9;
    if(e.kind==='kunai'){
      ctx.translate(x,y-18);ctx.strokeStyle='#211b25';ctx.lineWidth=5;ctx.beginPath();ctx.moveTo(-12-7*u,10+6*u);ctx.lineTo(12+7*u,-10-6*u);ctx.stroke();ctx.strokeStyle='#fff0c1';ctx.lineWidth=1.5;ctx.stroke();
      ctx.strokeStyle='#d7bd8f';ctx.lineWidth=1.5;for(let i=0;i<3;i++){const a=i*Math.PI*2/3+.3,d=7+14*u;ctx.beginPath();ctx.moveTo(Math.cos(a)*5,Math.sin(a)*5);ctx.lineTo(Math.cos(a)*d,Math.sin(a)*d);ctx.stroke();}
    }else{
      ctx.strokeStyle='#08070b';ctx.lineWidth=5*(1-u)+2;ctx.beginPath();ctx.ellipse(x,y,r,r*.38,0,0,Math.PI*2);ctx.stroke();
      ctx.strokeStyle=e.kind==='net'?'#c0a382':'#938294';ctx.lineWidth=1.4;for(const sign of [-1,1]){ctx.beginPath();ctx.moveTo(x+sign*r,y+3);ctx.quadraticCurveTo(x+sign*(r+6),y-13-8*(1-u),x+sign*r*.45,y-9);ctx.stroke();}
    }ctx.restore();
  }
  function drawShadowBlast(ctx,e,ultimate){
    const u=Math.max(0,Math.min(1,e.age/e.life)),growth=Math.min(1,u/(ultimate?.2:.26)),r=e.radius*growth,fade=(1-u)**1.15;
    ctx.save();ctx.globalAlpha=fade*.88;
    const count=ultimate?12:8;
    for(let i=0;i<count;i++){
      const a=i*Math.PI*2/count+.13*Math.sin(i*2.7),dx=Math.cos(a),dy=Math.sin(a),nx=-dy,ny=dx,d=r*(.58+.3*(.5+.5*Math.sin(i*1.9))),w=r*(ultimate?.12:.095)*(1-.3*u);
      ctx.fillStyle=i%2?'#f6b344':'#d7652c';ctx.beginPath();ctx.moveTo(e.x+nx*w*.4,e.y+ny*w*.4);ctx.quadraticCurveTo(e.x+dx*d*.46+nx*w,e.y+dy*d*.46+ny*w-12*(1-u),e.x+dx*d,e.y+dy*d);ctx.quadraticCurveTo(e.x+dx*d*.5-nx*w*.45,e.y+dy*d*.5-ny*w*.45,e.x-nx*w*.3,e.y-ny*w*.3);ctx.closePath();ctx.fill();
    }
    ctx.strokeStyle='#ffd17d';ctx.lineWidth=(ultimate?9:6)*(1-u)+1;ctx.beginPath();ctx.arc(e.x,e.y,r,0,Math.PI*2);ctx.stroke();
    ctx.strokeStyle='#fff0b8';ctx.lineWidth=2.5;for(let i=0;i<6;i++){const a=i*Math.PI/3+.08;ctx.beginPath();ctx.arc(e.x,e.y,r*.84,a,a+.3);ctx.stroke();}
    if(ultimate){
      const height=Math.min(e.radius,110)*Math.sin(Math.PI*Math.min(1,u*1.7));ctx.fillStyle='#e88431';ctx.beginPath();ctx.moveTo(e.x-r*.24,e.y);ctx.bezierCurveTo(e.x-r*.25,e.y-height*.38,e.x+9,e.y-height*.67,e.x-8,e.y-height);ctx.bezierCurveTo(e.x+r*.18,e.y-height*.7,e.x+r*.22,e.y-height*.3,e.x+r*.2,e.y);ctx.closePath();ctx.fill();
    }
    if(u<.24){const flash=1-u/.24;ctx.globalAlpha=flash*.85;ctx.fillStyle='#ffad43';ctx.beginPath();ctx.arc(e.x,e.y,Math.min(e.radius*.4,(ultimate?36:22)+r*.16),0,Math.PI*2);ctx.fill();ctx.fillStyle='#fff2c7';ctx.beginPath();ctx.arc(e.x,e.y,Math.min(e.radius*.2,(ultimate?17:10)+r*.07),0,Math.PI*2);ctx.fill();}
    ctx.globalAlpha=fade*Math.min(1,u*6)*.35;ctx.fillStyle='#5b4b43';for(let i=0;i<(ultimate?7:4);i++){const a=i*2.4,d=r*(.3+.06*i),size=(ultimate?13:8)*(1+u);ctx.beginPath();ctx.ellipse(e.x+Math.cos(a)*d,e.y+Math.sin(a)*d-20*u,size,size*.65,a,0,Math.PI*2);ctx.fill();}ctx.restore();
  }
  function referenceGround(ctx){
    for(const s of states.values()){
      if(!valid(s.owner)||s.world!==G.World)continue;Ref.drawProjection(ctx,s.projection);
      for(const projection of s.projections?.values()||[])Ref.drawProjection(ctx,projection);
      const tactics=moveFor(s.owner,'tactics');
      if(tactics&&s.plan){
        const strength=rank(tactics),phase=s.clock*3;ctx.save();ctx.fillStyle='#0a080d';ctx.strokeStyle='#8c765f';ctx.lineWidth=1.2;
        for(let i=0;i<2+Math.floor(strength/2);i++){const sign=i%2?1:-1,x=s.owner.x+sign*(8+i*3),y=s.owner.y+4,h=11+strength*2+3*Math.sin(phase+i);ctx.globalAlpha=.7;ctx.beginPath();ctx.moveTo(x-5,y);ctx.bezierCurveTo(x-12*sign,y-h*.3,x+8*sign,y-h*.7,x+3*sign,y-h);ctx.quadraticCurveTo(x+10*sign,y-h*.45,x+5,y);ctx.closePath();ctx.fill();ctx.globalAlpha=.4;ctx.beginPath();ctx.moveTo(x,y-2);ctx.quadraticCurveTo(x-3*sign,y-h*.5,x+3*sign,y-h+2);ctx.stroke();}ctx.restore();
      }
      for(const b of casts)if(b.owner===s.owner&&b.ultimate&&legal(b))for(const site of b.sites.values()){
        if(site.detonated)continue;const heat=Math.max(0,Math.min(1,(b.age-site.plantedAt)/Math.max(.01,b.blastAt-site.plantedAt)));
        ctx.save();ctx.strokeStyle='#e9ad5b';ctx.lineWidth=2+heat;ctx.globalAlpha=.16+.34*heat;for(let i=0;i<4;i++){const a=i*Math.PI/2+.15;ctx.beginPath();ctx.arc(site.x,site.y,b.spec.blastRadius,a,a+.85);ctx.stroke();}ctx.restore();
        for(let i=0;i<3;i++)drawPaperPacket(ctx,site.x,site.y-3,1.16,(i-1)*.55,heat);
      }
      const b=s.lastChain;if(b&&legal(b)&&(casts.includes(b)||ownedCaptures(s).length)){
        for(const segment of b.chain.segments){
          if(segment.linked===false||segment.polygon.length<3)continue;
          ctx.save();ctx.fillStyle='#030304';ctx.beginPath();segment.polygon.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.closePath();ctx.fill();ctx.clip();
          const points=segment.grownPoints;ctx.strokeStyle='#8b798b';ctx.lineWidth=1.3;ctx.globalAlpha=.28;ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.stroke();
          const start=Math.floor((s.clock*16+segment.index*7)%Math.max(1,points.length)),end=Math.min(points.length,start+5);ctx.strokeStyle='#d6c4a5';ctx.lineWidth=2;ctx.globalAlpha=.48;ctx.beginPath();for(let i=start;i<end;i++){const p=points[i];i===start?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);}ctx.stroke();ctx.restore();
        }
      }
      for(const node of s.board){
        if(!legal(node.cast)||s.clock-node.born<node.cast.spec.trapArm)continue;const heat=Number.isFinite(node.blastAt)?Math.max(0,Math.min(1,1-(node.blastAt-s.clock)/.5)):0;
        drawPaperPacket(ctx,node.x,node.y,1.15,.12,heat,Math.max(1,node.cast.spec.blastRounds-node.round));
      }
      for(const b of casts)if(b.owner===s.owner&&b.kind==='trap'&&legal(b)&&b.age>=.55)for(const t of b.traps)if(!t.detonated)drawPaperPacket(ctx,t.x,t.y,1.15,.12,Math.min(1,Math.max(0,(b.age-.55)/.5)));
      for(const b of casts)if(b.owner===s.owner&&b.kind==='sewing'&&legal(b))for(const arc of b.arcs||[]){
        const age=b.age-arc.born;if(age>=0&&age<b.spec.archPrepare){const progress=age/b.spec.archPrepare;Ref.drawProjection(ctx,s.projection,1);ctx.save();ctx.fillStyle='#030304';ctx.beginPath();ctx.moveTo(arc.source.x-7,arc.source.y);ctx.quadraticCurveTo(arc.source.x,arc.source.y-16*progress,arc.source.x+11,arc.source.y);ctx.fill();ctx.strokeStyle='#9d8875';ctx.globalAlpha=progress*.6;ctx.lineWidth=1.5;ctx.beginPath();ctx.ellipse(arc.source.x,arc.source.y,8+9*progress,3+3*progress,0,Math.PI,Math.PI*2);ctx.stroke();ctx.restore();}
      }
    }
  }
  function referenceAir(ctx){
    for(const b of casts)if(b.kind==='shadow'&&legal(b))for(const k of b.kunai||[]){
      ctx.save();ctx.translate(k.x,k.y-18);ctx.rotate(Math.atan2(k.vy,k.vx));ctx.lineCap='round';ctx.strokeStyle='#28222e';ctx.lineWidth=5;ctx.globalAlpha=.6;ctx.beginPath();ctx.moveTo(-42,0);ctx.lineTo(-7,0);ctx.stroke();ctx.strokeStyle='#e1cda7';ctx.lineWidth=1.5;ctx.globalAlpha=.8;ctx.stroke();ctx.globalAlpha=1;ctx.fillStyle='#e6e4d9';ctx.strokeStyle='#302936';ctx.lineWidth=1.5;
      ctx.beginPath();ctx.moveTo(17,0);ctx.lineTo(-3,-3.3);ctx.lineTo(-7,0);ctx.lineTo(-3,3.3);ctx.closePath();ctx.fill();ctx.stroke();ctx.strokeStyle='#fff8d9';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(-2,0);ctx.lineTo(13,0);ctx.stroke();ctx.strokeStyle='#39313e';ctx.lineWidth=2.5;ctx.beginPath();ctx.moveTo(-7,0);ctx.lineTo(-15,0);ctx.stroke();ctx.restore();
    }
    for(const s of states.values())if(valid(s.owner)&&s.world===G.World)for(const node of s.board){
      const b=node.cast,age=s.clock-node.born;if(!legal(b)||age<0||age>=b.spec.trapArm)continue;
      const u=Math.min(1,age/b.spec.trapArm),x=b.origin.x+(node.x-b.origin.x)*u,y=b.origin.y+(node.y-b.origin.y)*u-Math.sin(u*Math.PI)*52-(1-u)*18;drawPaperPacket(ctx,x,y,1.08,u*5.5,0);
    }
    for(const b of casts)if(b.kind==='trap'&&legal(b)&&b.age>=b.spec.release&&b.age<.55){
      const u=Math.min(1,(b.age-b.spec.release)/(.55-b.spec.release));for(const t of b.traps)drawPaperPacket(ctx,b.origin.x+(t.x-b.origin.x)*u,b.origin.y+(t.y-b.origin.y)*u-Math.sin(u*Math.PI)*52-(1-u)*18,1.08,b.aim+u*5.5,0);
    }
    for(const b of casts)if(b.kind==='sewing'&&legal(b))for(const arc of b.arcs||[]){
      const age=b.age-arc.born;if(age<0||age>b.spec.archPrepare+b.spec.archFlight+.16)continue;const alpha=Math.min(1,Math.max(0,(b.spec.archPrepare+b.spec.archFlight+.16-age)/.16));Ref.drawArch(ctx,arc,alpha);
      if(!arc.blocked&&arc.points.length>2&&arc.progress>0){ctx.save();ctx.globalAlpha=alpha*(b.ultimate?.7:.5);ctx.strokeStyle=b.ultimate?'#c8aa80':'#8b7d8e';ctx.lineWidth=Math.min(2.4,arc.width*.35);ctx.beginPath();for(let i=0;i<arc.points.length-1;i++){const p=arc.points[i];i?ctx.lineTo(p.x,p.y-p.z):ctx.moveTo(p.x,p.y-p.z);}ctx.stroke();ctx.restore();}
      if(arc.hit&&arc.contact){const contactAge=age-b.spec.archPrepare-b.spec.archFlight*arc.contact.progress,punch=Math.max(0,1-contactAge/.16),p=arc.contact.point;if(punch>0){ctx.save();ctx.translate(p.x,p.y-p.z);ctx.globalAlpha=punch;ctx.strokeStyle='#221a26';ctx.lineWidth=5;ctx.beginPath();ctx.moveTo(-9-8*(1-punch),9);ctx.lineTo(9+8*(1-punch),-11);ctx.stroke();ctx.strokeStyle='#ffe0a0';ctx.lineWidth=1.5;ctx.stroke();ctx.restore();}}
    }
    for(const e of effects){
      if(e.owner&&(!valid(e.owner)||e.world!==G.World)||e.castRef&&!legal(e.castRef))continue;
      if(e.kind==='explosion'||e.kind==='checkmate-blast')drawShadowBlast(ctx,e,e.kind==='checkmate-blast');
      else if(e.kind==='shadow'||e.kind==='kunai'||e.kind==='net')drawShadowContact(ctx,e);
      else if(e.kind==='strangle'&&e.castRef)drawStrangleActor(ctx,e.target,e,e.castRef,1);
    }
    const s=states.get(G.Game.player),b=s?.ultimate;
    if(b&&legal(b)&&b.age<b.duration){ctx.save();ctx.font='bold 17px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';const text=b.age<b.blastAt?'奈良流・詰將':'勝負已定',x=b.owner.x,y=b.owner.y-88,w=ctx.measureText(text).width+24;ctx.fillStyle='rgba(15,15,19,.86)';ctx.fillRect(x-w/2,y-15,w,30);ctx.fillStyle=b.age<b.blastAt?'#e8dbbe':'#ffd58c';ctx.fillText(text,x,y);ctx.restore();}
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
    for(const s of states.values())if(s.projections&&[...s.projections.keys()].some(e=>e.dex===dex&&e.x===x&&e.y===y))return;
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
  function sewingPoseFor(a,s,p){const pose=s?.sewingPose;if(!pose||!moveFor(a,'sewing')||['net','finish'].includes(p?.phase)||s.clock-pose.started>=pose.duration)return null;const cast=casts.findLast(b=>b.owner===a&&b.kind==='sewing'&&legal(b)),arc=cast?.arcs.find(arc=>arc.progress<1&&!arc.blocked);return {...pose,stage:arc?.phase||'ground',phaseAge:s.clock-pose.started,phaseDuration:pose.duration,age:s.clock-pose.started,moving:s.moving};}
  G.NarutoShikamaru={version:7,dex:DEX,supports,profile,canCast,cast,update,clear,held,stopped,clearPath,segmentDistance,statusFor,shadowVisualFor,ribbonGeometry,ribbonContains,polygonContains,sewingVisualFor,effectVisualFor,projectionFor,
    activeFor:a=>{const s=states.get(a),p=s?.plan,throwing=s?.throwPose,sewing=sewingPoseFor(a,s,p);if(s?.ultimate&&legal(s.ultimate)&&s.ultimate.age<s.ultimate.duration)return {kind:'checkmate',phase:'checkmate',phaseAge:s.ultimate.age,phaseDuration:s.ultimate.duration,age:s.ultimate.age,duration:s.ultimate.duration,moving:s.moving,aim:a.aim||0};if(sewing)return sewing;if(throwing&&s.clock-throwing.started<throwing.duration&&!s.moving)return {...throwing,phaseAge:s.clock-throwing.started,phaseDuration:throwing.duration,age:s.clock-throwing.started,moving:false};if(p){const m=moveFor(a,'shadow'),spec=profile(a,m),duration={prepare:spec.release,release:spec.captureWindow-spec.release,drag:spec.dragTimeout,net:spec.netPrepare,blast:Math.max(.4,(p.end||s.clock)-p.at),finish:p.finishDuration||.65,recover:spec.recoverTime}[p.phase];return {kind:p.phase==='finish'&&skillAction(s,'strangle')?'strangle':'shadow',phase:p.phase,phaseAge:s.clock-p.at,phaseDuration:duration,age:s.clock-p.at,duration,moving:s.moving,aim:a.aim||0};}const b=s?.pose;return b&&legal(b)&&b.age<.65?{...b,kind:b.kind,age:b.age,duration:.65}:null;},
    stateFor:(a=G.Game.player)=>states.get(a)||null,stats:(a=G.Game.player)=>{const s=states.get(a);return s?{casts:{...s.casts},hits:s.hits,damage:s.damage,bound:s.bound,detonations:s.detonations,contacts:s.contacts.slice(),phase:s.plan?.phase||'ready',cycles:s.cycles,travelled:s.travelled,dragged:s.dragged,board:s.board.length}:null;},
    get casts(){return casts;},get leases(){return leases;},get effects(){return effects;}};
})();
