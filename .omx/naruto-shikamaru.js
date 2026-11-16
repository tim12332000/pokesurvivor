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
  function state(a){let s=states.get(a);if(s&&s.world!==G.World){clear(a);s=null;}if(!s){s={owner:a,world:G.World,clock:0,cooldowns:{},pose:null,casts:{},hits:0,damage:0,bound:0,detonations:0,contacts:[],board:[],plan:null,walkDistance:0,prevX:a.x,prevY:a.y,moving:false,travelled:0,dragged:0,cycles:0,sewingQueued:false};states.set(a,s);}return s;}
  function profile(a,m){
    const L=rank(m),Q=Math.max(0,Math.min(16,Math.floor(G.Quantity?.bonus(a)??a.quantityPicks??a.quantityBonus??0)));
    const tactics=a.moves?.find(x=>x.digiMode==='shikamaru-tactics'),T=tactics?rank(tactics):0;
    const kind=(m?.digiMode||'shikamaru-shadow').replace('shikamaru-','');
    return {kind,L,Q,T,range:(m?.range||300)+24*(L-1)+12*Q,
      branches:Math.min(32,4+2*Q+Math.floor((L-1)/2)+T),pulses:kind==='sewing'?3+L+Math.min(4,Q):kind==='strangle'?2+L:1,
      traps:Math.min(24,3+2*Q+Math.floor((L-1)/2)),radius:(kind==='trap'?108:kind==='strangle'?70:22)+7*(L-1)+(kind==='trap'?8*Q:0),
      damage:(m?.dmg??(kind==='shadow'?12:kind==='sewing'?17:kind==='trap'?65:35))*(a.atk??1),
      bindDuration:1.25+.23*L+.12*T,cd:Math.max(.2,(m?.cd??(kind==='shadow'?1.5:kind==='sewing'?4:kind==='trap'?5.5:7))*(a.cdMul??1)),
      speed:620+35*L,release:kind==='trap'?.25:.18,interval:kind==='strangle'?.23:.16,
      trapLifetime:10,deployDistance:54,trapArm:.55,blastRounds:1+Math.min(3,Q)+Math.floor((L-1)/2),blastInterval:.16,chainInterval:.12,captureWindow:.55,dragTimeout:2.4,stopWindow:.25,netPrepare:.28,recoverTime:.35};
  }
  function clearPath(ax,ay,bx,by,r=1,target=null){
    if(G.World.projectilePathClear)return G.World.projectilePathClear(ax,ay,bx,by,target,{radius:r,spacing:5,includeStart:false});
    const n=Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/5));
    for(let i=1;i<=n;i++){const x=ax+(bx-ax)*i/n,y=ay+(by-ay)*i/n,b=G.World.projectileBlock?.(x,y,r);if(b&&b!==target)return false;if(!G.World.projectileBlock&&G.World.isWall?.(x,y))return false;}return true;
  }
  function targets(a,p){
    const list=[...new Set(G.EnemyMgr.queryCircle(a.x,a.y,p.range))].filter(e=>alive(e)&&!e.friendly&&Math.hypot(e.x-a.x,e.y-a.y)<=p.range+(e.r||0)&&clearPath(a.x,a.y,e.x,e.y)).sort((u,v)=>Number(held(u))-Number(held(v))||Math.hypot(u.x-a.x,u.y-a.y)-Math.hypot(v.x-a.x,v.y-a.y));
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
    if(!old||old.until<until){leases.set(e,{cast:b,until,x:e.x,y:e.y});b.state.bound++;if(b.shared&&b.kind==='shadow'){b.state.sewingQueued=true;if(b.state.plan)b.state.plan.captureAt??=b.state.clock;}}}
  function hit(b,e,scale=1){
    if(!legal(b)||!alive(e))return false;
    const mult=G.Types?.mult?.(b.m.type||'dark',e.types)??1,crit=Math.random()<(b.owner.critChance||0);
    const preparation=b.shared&&!b.finisher?(b.kind==='shadow'?.22:b.kind==='sewing'?.3:1):1;
    const damage=b.spec.damage*scale*preparation*mult*(G.Weather?.mult?.(b.m.type||'dark')??1)*(crit?1.5:1);
    e.hurt(damage,b.kind==='trap'?'#ffc27b':'#bca6db',0,0,0,crit?'crit':G.Types?.label?.(mult),b.owner,b.m.id);
    if(!legal(b))return false;
    b.owner.onDealt?.(damage);if(!legal(b))return false;
    b.owner.dmgDealt=(b.owner.dmgDealt||0)+damage;b.state.hits++;b.state.damage+=damage;b.hits++;
    if(b.state.contacts.length<120)b.state.contacts.push({cast:b.serial,mode:b.kind,pulse:b.emitted,x:e.x,y:e.y,damage});
    G.DamageSplash?.hit?.(b.owner,e,damage,b.kind==='trap'?'#ffc27b':'#bca6db',b.m.id);
    return legal(b);
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
  function shadowVisualFor(a){
    const s=states.get(a),m=moveFor(a,'shadow'),p=m?profile(a,m):null,targets=new Set();let extensionTotal=0,branches=0;
    for(const b of casts){if(b.owner!==a||!legal(b)||!['shadow','sewing'].includes(b.kind))continue;
      for(const r of b.rays){if(!r.tip)continue;extensionTotal+=Math.hypot(r.tip.x-a.x,r.tip.y-a.y);branches++;targets.add(r.target);}
    }
    if(s)for(const [e]of ownedCaptures(s))if(!targets.has(e)){extensionTotal+=Math.hypot(e.x-a.x,e.y-a.y);branches++;}
    const spent=Math.min(1,extensionTotal/Math.max(1,(p?.range||360)*(p?.branches||4)));
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
    effects.push({owner:b.owner,world:b.world,kind:'explosion',x:t.x,y:t.y,age:0,life:.5,radius:b.spec.radius});
    for(const e of new Set(G.EnemyMgr.queryCircle(t.x,t.y,b.spec.radius+40))){
      if(!legal(b))return;if(!alive(e)||e.friendly||Math.hypot(e.x-t.x,e.y-t.y)>b.spec.radius+(e.r||0)||!clearPath(t.x,t.y,e.x,e.y))continue;
      if(!hit(b,e,held(e)&&leases.get(e)?.cast.owner===b.owner?1.5:1))return;
    }
    for(const prop of G.World.propsInCircle?.(t.x,t.y,b.spec.radius)||[]){if(!legal(b))return;if(prop.destructible&&prop.hp>0&&Math.hypot(prop.x-t.x,prop.y-t.y)<=b.spec.radius+(prop.r||0)&&clearPath(t.x,t.y,prop.x,prop.y,1,prop))G.World.damageProp?.(prop,b.spec.damage,'#ffc27b');}
  }
  const moveFor=(a,kind)=>a.moves?.find(m=>m.digiMode==='shikamaru-'+kind);
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
      for(const [e,l]of ownedCaptures(s)){
        if(strong(e))continue;
        const steps=Math.max(1,Math.ceil(d/4));
        for(let i=0;i<steps;i++){
          const x=e.x+dx/steps,y=e.y+dy/steps;
          if(!G.World.isFree?.(x,y,e.r||10,true)||!clearPath(a.x,a.y,x,y))break;
          e.x=x;e.y=y;s.dragged+=d/steps;
        }
        e.anim?.loop?.('Walk');
      }
      G.EnemyMgr.rebuildGrid?.();
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
      else if(s.clock-p.started>=spec.release+spec.range/spec.speed+.08){p.phase='recover';p.at=s.clock;p.empty=true;s.cooldowns[m.id]=Math.min(s.cooldowns[m.id]||0,.18);}
    }
    if(s.sewingQueued&&!p.sewn&&s.clock-p.started>=.4){p.sewn=true;s.sewingQueued=false;relay(s,'sewing');}
    if(['drag','blast'].includes(p.phase)&&canCast(a,m))relay(s,'shadow');
    if(p.phase==='drag'){
      const ready=heldList.length>=2&&(!moveFor(a,'trap')||s.board.some(t=>s.clock-t.born>=t.cast.spec.trapArm));
      p.stop=!s.moving&&ready&&s.clock-(p.captureAt??s.clock)>=.7?p.stop+dt:0;
      if(p.stop>=spec.stopWindow||s.clock-p.started>=spec.dragTimeout)startNet(s);
    }else if(p.phase==='net'&&age>=spec.netPrepare){
      // A Lv1 net is already a real second attack, even before any tool is learned.
      const net={serial:++serial,owner:a,state:s,world:G.World,m:{...m},spec,kind:'shadow',shared:true,finisher:true,cancelled:false,hits:0,emitted:1};
      for(const [e]of heldList){if(!legal(net)||!hit(net,e,2))break;effects.push({owner:a,world:G.World,kind:'net',x:e.x,y:e.y,age:0,life:.4,radius:(e.r||12)+12});}
      if(states.get(a)!==s)return;
      relay(s,'sewing',true);
      let scheduled=0,last=s.clock;
      for(const t of s.board){if(!legal(t.cast)||Number.isFinite(t.blastAt)||s.clock-t.born<t.cast.spec.trapArm)continue;
        t.blastAt=s.clock+scheduled*t.cast.spec.chainInterval;last=t.blastAt+(t.cast.spec.blastRounds-1)*t.cast.spec.blastInterval;scheduled++;
      }
      p.phase='blast';p.at=s.clock;p.end=Math.max(s.clock+.4,last+.2);p.nodes=scheduled;
    }else if(p.phase==='blast'&&s.clock>=p.end){const finish=relay(s,'strangle',true);p.phase='finish';p.at=s.clock;p.finishDuration=finish?finish.spec.release+(finish.spec.pulses-1)*finish.spec.interval+.25:.45;for(const [,l]of ownedCaptures(s))l.until=Math.max(l.until,s.clock+p.finishDuration+.1);}
    else if(p.phase==='finish'&&age>=p.finishDuration){p.phase='recover';p.at=s.clock;for(const [e]of ownedCaptures(s))leases.delete(e);}
    else if(p.phase==='recover'&&s.clock-p.at>=(p.empty?.18:spec.recoverTime)){s.plan=null;s.sewingQueued=false;}
    if(states.get(a)!==s)return;
    const phase=s.plan?.phase||'ready',remaining=phase==='drag'?Math.max(0,spec.dragTimeout-(s.clock-p.started)):phase==='net'?Math.max(0,spec.netPrepare-(s.clock-p.at)):phase==='blast'?Math.max(0,p.end-s.clock):0;
    const captured=ownedCaptures(s).length,board=s.board.length,hasTrap=!!moveFor(a,'trap');
    const canStop=captured>=2&&(!hasTrap||s.board.some(t=>s.clock-t.born>=t.cast.spec.trapArm))&&s.clock-(p.captureAt??s.clock)>=.7;
    s.cue={phase,remaining,captured,board,label:phase==='drag'?`${hasTrap?'佈局｜札'+board+' ':''}捕捉${captured}${canStop?' · 停步收網':''}`:phase==='net'?'結印 · 影網收束':phase==='blast'?(p.nodes?'起爆札接力':'影網絞擊'):phase==='finish'?(moveFor(a,'strangle')?'影首縛 · 終結':'影術收勢'):phase==='recover'?(p.empty?'未捕獲 · 重新結影':'整備'):'影模仿 · 廣捕'};
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
    for(const [a,s]of states){if(!valid(a)||s.world!==G.World||(s.plan&&!moveFor(a,'shadow'))){clear(a);continue;}s.clock+=dt;if(s.pose&&s.pose.age>=.65)s.pose=null;}
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
  function drawGround(ctx){
    for(const a of [G.Game.player,...(G.SelfClones?.actors?.()||[])])if(valid(a)){
      const visual=shadowVisualFor(a);ctx.save();ctx.fillStyle='#211b2c';ctx.globalAlpha=.78;ctx.beginPath();ctx.arc(visual.x,visual.y,visual.poolRadius,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#60516f';ctx.lineWidth=1;ctx.globalAlpha=.5;ctx.stroke();ctx.restore();
    }
    for(const b of casts){if(!legal(b))continue;const p=b.spec;
      ctx.save();ctx.lineCap='round';ctx.lineJoin='round';
      if(b.kind==='trap')for(const t of b.traps){if(t.detonated||b.age<.55)continue;ctx.save();ctx.translate(t.x,t.y);ctx.rotate(.22);ctx.fillStyle='#e9d6a1';ctx.fillRect(-6,-10,12,20);ctx.strokeStyle='#663927';ctx.lineWidth=2;ctx.strokeRect(-6,-10,12,20);ctx.fillStyle='#613c35';ctx.fillRect(-2,-6,4,11);ctx.fillStyle='#ffb353';ctx.fillRect(3,-12,3,3);ctx.restore();}
      else for(const r of b.rays){if(!r.tip)continue;drawRibbon(ctx,ribbonGeometry(b.owner.x,b.owner.y,r.tip.x,r.tip.y,b.kind==='strangle'?2.5:p.radius));}
      ctx.restore();
    }
    for(const [e,l]of leases){if(!held(e))continue;const a=l.cast.owner;drawRibbon(ctx,ribbonGeometry(a.x,a.y,e.x,e.y,3.5),.72);ctx.save();ctx.fillStyle='#201c2a';ctx.beginPath();ctx.ellipse(e.x,e.y,(e.r||12)+8,9,0,0,Math.PI*2);ctx.fill();ctx.restore();}
    for(const s of states.values())if(s.plan?.phase==='net'){
      const u=Math.min(1,(s.clock-s.plan.at)/profile(s.owner,moveFor(s.owner,'shadow')).netPrepare);
      ctx.save();ctx.strokeStyle='#a99aba';ctx.lineWidth=2;ctx.globalAlpha=.45+.5*u;
      for(const [e]of ownedCaptures(s)){
        const radius=(e.r||12)+28*(1-u)+4;ctx.beginPath();ctx.ellipse(e.x,e.y,radius,radius*.5,0,0,Math.PI*2);ctx.stroke();
        ctx.strokeStyle='#302137';ctx.lineWidth=4+u*3;ctx.beginPath();ctx.moveTo(s.owner.x,s.owner.y);ctx.quadraticCurveTo((s.owner.x+e.x)/2,(s.owner.y+e.y)/2-28*(1-u),e.x,e.y);ctx.stroke();ctx.strokeStyle='#a99aba';ctx.lineWidth=2;
      }ctx.restore();
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
  function drawAir(ctx){
    for(const s of states.values())for(const node of s.board){const b=node.cast,age=s.clock-node.born;if(!legal(b)||age>=b.spec.trapArm)continue;
      const u=age/b.spec.trapArm,x=b.origin.x+(node.x-b.origin.x)*u,y=b.origin.y+(node.y-b.origin.y)*u-Math.sin(u*Math.PI)*35;
      ctx.save();ctx.translate(x,y);ctx.rotate(u*8);ctx.fillStyle='#c5cbd2';ctx.beginPath();ctx.moveTo(12,0);ctx.lineTo(-6,-5);ctx.lineTo(-6,5);ctx.closePath();ctx.fill();ctx.fillStyle='#ead7a3';ctx.fillRect(-15,-4,9,16);ctx.fillStyle='#713d33';ctx.fillRect(-11,0,2,9);ctx.restore();
    }
    for(const b of casts)if(b.kind==='trap'&&legal(b)&&b.age>=b.spec.release&&b.age<.55){
      const u=Math.min(1,(b.age-b.spec.release)/(.55-b.spec.release));
      for(const t of b.traps){ctx.save();ctx.translate(b.origin.x+(t.x-b.origin.x)*u,b.origin.y+(t.y-b.origin.y)*u-24-Math.sin(u*Math.PI)*35);ctx.rotate(b.aim+u*5);ctx.fillStyle='#c8cbd1';ctx.beginPath();ctx.moveTo(12,0);ctx.lineTo(-4,-5);ctx.lineTo(-4,5);ctx.closePath();ctx.fill();ctx.strokeStyle='#3c3544';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(-4,0);ctx.lineTo(-12,0);ctx.stroke();ctx.fillStyle='#ead7a3';ctx.fillRect(-19,-4,8,15);ctx.fillStyle='#763c36';ctx.fillRect(-16,-1,2,8);ctx.restore();}
    }
    for(const e of effects){
      const t=e.age/e.life;ctx.save();ctx.globalAlpha=1-t;
      if(e.kind==='explosion'){
        ctx.fillStyle='#e58b38';for(let i=0;i<9;i++){const a=i*Math.PI*2/9,d=e.radius*t;ctx.beginPath();ctx.arc(e.x+Math.cos(a)*d,e.y+Math.sin(a)*d-12,12*(1-t)+3,0,Math.PI*2);ctx.fill();}
        ctx.strokeStyle='#ffd59b';ctx.lineWidth=4;ctx.beginPath();ctx.ellipse(e.x,e.y,e.radius*t,e.radius*t*.55,0,0,Math.PI*2);ctx.stroke();
      }else if(e.kind==='net'){
        const r=e.radius*(1-.7*t);ctx.strokeStyle='#302137';ctx.lineWidth=7*(1-t)+2;
        ctx.beginPath();ctx.ellipse(e.x,e.y,r,r*.5,0,0,Math.PI*2);ctx.stroke();
        for(const sign of [-1,1]){ctx.beginPath();ctx.moveTo(e.x-sign*r,e.y-r*.4);ctx.quadraticCurveTo(e.x,e.y+8*(1-t),e.x+sign*r,e.y+r*.4);ctx.stroke();}
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
    const s=states.get(G.Game.player),cue=s?.cue;
    if(s&&cue&&valid(s.owner)&&s.plan){
      const text=cue.label+(cue.remaining>0?' '+cue.remaining.toFixed(1)+'s':'');ctx.save();ctx.font='bold 10px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';
      const w=ctx.measureText(text).width+14,x=s.owner.x,y=s.owner.y+30;
      ctx.fillStyle='rgba(20,18,28,.82)';ctx.fillRect(x-w/2,y-10,w,20);ctx.fillStyle=cue.phase==='net'||cue.phase==='blast'?'#ffda91':'#e4d8ed';ctx.fillText(text,x,y);ctx.restore();
    }
  }
  const oldEnemy=G.Enemy?.prototype.update;
  if(oldEnemy)G.Enemy.prototype.update=function(dt,...args){
    if(G.Game.state==='playing'&&held(this)){
      // The native stopped gate handles ordinary AI after status clocks run.
      // Strong enemies retain attacks; only their position is restrained.
      if(!strong(this)){const r=oldEnemy.call(this,dt,...args);if(held(this)&&leases.get(this)?.cast.state.moving)this.anim?.loop?.('Walk');return r;}
      const x=this.x,y=this.y,result=oldEnemy.call(this,dt,...args);if(held(this)&&alive(this)){this.x=x;this.y=y;}return result;
    }
    return oldEnemy.call(this,dt,...args);
  };
  const oldTick=C.tick,oldUpdate=C.updateFields,oldClear=C.clearFields,oldGround=C.drawGroundFields,oldAir=C.drawAirFields;
  C.tick=tick;C.updateFields=function(dt){const r=oldUpdate.call(this,dt);update(dt);return r;};
  C.clearFields=function(a){clear(a);return oldClear.call(this,a);};
  C.drawGroundFields=function(ctx){oldGround.call(this,ctx);drawGround(ctx);};C.drawAirFields=function(ctx){oldAir.call(this,ctx);drawAir(ctx);};
  function statusFor(a,m){
    const s=states.get(a);if(!s)return {label:'影網待命',fraction:0};
    if(m?.digiMode==='shikamaru-tactics')return {label:'戰術被動',fraction:0};
    const c=s.cue;if(!c)return {label:'影網待命',fraction:0};
    const kind=m?.digiMode?.replace('shikamaru-',''),label=kind==='trap'?(c.phase==='blast'&&s.plan?.nodes?'連爆':'札'+c.board):kind==='sewing'?(c.phase==='net'||c.phase==='blast'?'影縫接力':'待接影縫'):kind==='strangle'?(c.phase==='finish'?'首縛終結':'待收網'):c.phase==='net'?'收網':c.phase==='recover'?'整備':'捕捉'+c.captured;
    return {label,fraction:c.phase==='drag'?Math.max(0,Math.min(1,1-c.remaining/2.4)):c.phase==='net'?Math.max(0,Math.min(1,1-c.remaining/.28)):c.phase==='blast'?1:0};
  }
  G.NarutoShikamaru={version:4,dex:DEX,supports,profile,canCast,cast,update,clear,held,stopped,clearPath,segmentDistance,statusFor,shadowVisualFor,ribbonGeometry,ribbonContains,
    activeFor:a=>{const s=states.get(a),p=s?.plan,throwing=s?.throwPose;if(throwing&&s.clock-throwing.started<throwing.duration&&!s.moving)return {...throwing,phaseAge:s.clock-throwing.started,phaseDuration:throwing.duration,age:s.clock-throwing.started,moving:false};if(p){const m=moveFor(a,'shadow'),spec=profile(a,m),duration={prepare:spec.release,release:spec.captureWindow-spec.release,drag:spec.dragTimeout,net:spec.netPrepare,blast:Math.max(.4,(p.end||s.clock)-p.at),finish:p.finishDuration||.65,recover:spec.recoverTime}[p.phase];return {kind:p.phase==='finish'&&moveFor(a,'strangle')?'strangle':'shadow',phase:p.phase,phaseAge:s.clock-p.at,phaseDuration:duration,age:s.clock-p.at,duration,moving:s.moving,aim:a.aim||0};}const b=s?.pose;return b&&legal(b)&&b.age<.65?{...b,kind:b.kind,age:b.age,duration:.65}:null;},
    stateFor:(a=G.Game.player)=>states.get(a)||null,stats:(a=G.Game.player)=>{const s=states.get(a);return s?{casts:{...s.casts},hits:s.hits,damage:s.damage,bound:s.bound,detonations:s.detonations,contacts:s.contacts.slice(),phase:s.plan?.phase||'ready',cycles:s.cycles,travelled:s.travelled,dragged:s.dragged,board:s.board.length}:null;},
    get casts(){return casts;},get leases(){return leases;},get effects(){return effects;}};
})();
