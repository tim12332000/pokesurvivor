/* Actor-owned fan winds. Quantity creates actors; mastery creates real timed cuts. */
(() => {
  if (G.NarutoTemari) return;
  const combat=G.Combat, TAU=Math.PI*2, EPS=1e-8;
  const states=new Map(), casts=[], blades=[], waves=[], summons=[], storms=[], orbits=new Map(), lifts=new Map(), pushes=new Map();
  const modes=new Set(['temari-wind','temari-mastery','temari-great-scythe','temari-blade-dance','temari-typhoon']);
  let sequence=0, petSequence=0, petPacketSequence=0;
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const controlled=a=>a===G.Game.player||!!G.SelfClones?.isActor(a);
  const valid=a=>alive(a)&&controlled(a)&&(a.mon?.dex??a.dex)===30011;
  const supports=mode=>modes.has(mode);
  const rank=m=>Math.max(1,Math.min(5,Math.floor(m?.lvl||1)));
  const quantity=a=>Math.max(0,Math.floor(G.Quantity?.bonus(a)??a.quantityPicks??a.quantityBonus??0));
  const passive=a=>a.moves?.find(m=>m.digiMode==='temari-mastery'||m.id==='naruto-temari-three-stars'||m.id==='naruto-temari-mastery');
  const selected=(a,m)=>!!a.activeGroup?.().some(x=>x.id===m.id);
  function state(owner) {
    let s=states.get(owner);
    if(s&&s.world!==G.World){clear(owner);s=null;}
    if(!s){s={owner,world:G.World,clock:0,basicCooldown:0,cooldowns:{},basicRounds:0,pose:null,latest:null,
      totalEmitted:0,emittedByMode:{},castCounts:{},counts:{},totalCuts:0,hitEvents:0,propHits:0,intercepted:0};states.set(owner,s);}
    return s;
  }
  function clearPath(ax,ay,bx,by,r=1,target=null) {
    if(G.World.projectilePathClear)return G.World.projectilePathClear(ax,ay,bx,by,target,{radius:r,spacing:5,includeStart:false});
    const n=Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/5));
    for(let i=1;i<=n;i++) {
      const x=ax+(bx-ax)*i/n,y=ay+(by-ay)*i/n;
      const block=G.World.projectileBlock?.(x,y,r);
      if(block&&block!==target)return false;
      if(!G.World.projectileBlock&&G.World.isWall?.(x,y))return false;
    }
    return true;
  }
  function mastery(owner) {
    const p=passive(owner),L=p?rank(p):0,Q=quantity(owner);
    return {L,Q,R:L?1+L+Q:1,speed:L?[1.15,1.25,1.4,1.6,1.85][L-1]:1,
      reach:L?[40,70,110,160,220][L-1]:0,power:L?[1.15,1.2,1.25,1.3,1.35][L-1]:1,
      budget:L?Math.floor([1,1,2,2,3][L-1]*1.25**Q):0};
  }
  function heavyFor(owner,m) {
    const i=rank(m)-1,p=mastery(owner);
    return {range:[300,330,360,390,420][i]+6*p.Q+p.reach,
      arc:Math.min(180,110+10*i+2*p.Q)*Math.PI/180,
      pushDistance:[120,145,170,195,220][i]+18*p.L+4*p.Q,pushDuration:.35,speed:720*p.speed};
  }
  function rangeFor(owner,m) {if(m.digiMode==='temari-great-scythe')return heavyFor(owner,m).range;if(m.digiMode==='temari-typhoon')return [240,270,300,330,360][rank(m)-1];return (m.range||[240,250,270,290,310][rank(m)-1])+mastery(owner).reach;}
  function targets(owner,m,candidates=null) {
    const r=rangeFor(owner,m);
    const summonPriority=m.digiMode==='temari-blade-dance'&&owner===G.Game.player;
    const strong=e=>!!(e.boss||e.legend||e.judge||e.elite);
    const enemies=(candidates||[...new Set(G.EnemyMgr.queryCircle(owner.x,owner.y,r))]).filter(e=>alive(e)&&!e.friendly&&
      Math.hypot(e.x-owner.x,e.y-owner.y)<=r+(e.r||0)&&clearPath(owner.x,owner.y,e.x,e.y))
      .sort((a,b)=>(summonPriority?Number(strong(b))-Number(strong(a)):(a===owner.target?-1:0)-(b===owner.target?-1:0))||
        Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y));
    if(enemies.length||m.digiMode!=='temari-wind')return enemies;
    return props(owner.x,owner.y,r).filter(p=>p.destructible&&p.hp>0&&
      Math.hypot(p.x-owner.x,p.y-owner.y)<=r+(p.r||0)&&clearPath(owner.x,owner.y,p.x,p.y,1,p))
      .sort((a,b)=>Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y));
  }
  function canCast(owner,m) {
    if(!valid(owner)||owner.frozen||!supports(m?.digiMode)||(m.digiMode==='temari-mastery'||m.digiMode==='temari-blade-dance'))return false;
    const s=state(owner),basic=m.digiMode==='temari-wind';
    if(basic?s.basicCooldown>EPS:!selected(owner,m)||(s.cooldowns[m.id]||0)>EPS)return false;
    return targets(owner,m).length>0;
  }
  function snapshot(owner,move) {
    const m={...move},modeslot=m.digiMode,i=rank(m)-1,p=mastery(owner),scale=1.25**p.Q;
    const N=Math.floor(3*scale),W=1,K=Math.floor(scale);
    const C=(modeslot==='temari-typhoon'?[3,4,5,6,8]:[4,4,5,5,6])[i]+(p.L?p.L+p.Q:0);
    const basic=modeslot==='temari-wind',heavy=modeslot==='temari-great-scythe',typhoon=modeslot==='temari-typhoon';
    const T=Math.floor(scale),P=C;
    const s=state(owner),empowered=basic&&p.L>0&&(s.basicRounds+1)%3===0;
    const fallback=basic?[8,9.6,11.52,14.4,18][i]:heavy?[56,67.2,80.64,100.8,126][i]:typhoon?[24,28.8,35.2,43.2,52.8][i]:[25.6,31.2,37.6,45.6,55.2][i];
    const h=heavy?heavyFor(owner,m):null;
    return {id:m.id,mode:modeslot,kind:basic?'basic':heavy?'heavy':typhoon?'typhoon':'summon',m,Q:p.Q,L:p.L,N,R:heavy?1:p.R,W,K,C,T,P,
      count:basic?N:heavy?1:typhoon?T:K,potentialHits:basic?N*p.R:heavy?1:typhoon?T*P:K*C,
      damage:(Number.isFinite(m.dmg)?m.dmg:fallback)*(owner.atk??1)*(empowered?p.power:1),
      critChance:owner.critChance||0,range:rangeFor(owner,m),speed:h?.speed??(m.speed||(basic?420:500))*p.speed,
      arc:h?.arc??(basic?[45,75,105,135,180][i]*Math.PI/180:m.arc||100*Math.PI/180),radius:basic?(m.contactRadius||30):heavy?(m.radius||160):typhoon?[240,270,300,330,360][i]:(m.radius||65),
      pushDistance:h?.pushDistance??0,pushDuration:h?.pushDuration??0,
      empowered,budget:empowered?p.budget:0,atk:owner.atk??1,emitted:0,cuts:0,hits:0,props:0};
  }
  function start(owner,snap,ghost=false) {
    const s=state(owner),list=ghost?(snap.targetPositions||[]):targets(owner,snap.m);
    if(!ghost&&!list.length)return false;
    const aim=Number.isFinite(snap.aim)?snap.aim:list.length?Math.atan2(list[0].y-owner.y,list[0].x-owner.x):owner.aim||0;
    const b={...snap,serial:++sequence,castId:snap.castId,owner,world:G.World,ghost,age:0,started:s.clock,x:snap.x??owner.x,y:snap.y??owner.y,
      aim,targets:list.map(e=>({x:e.x,y:e.y})),emitted:0,cuts:0,hits:0,props:0,duration:snap.kind==='basic'?.5:snap.kind==='heavy'?.8:snap.kind==='typhoon'?1.7:.65,
      release:snap.kind==='basic'?.18:.4,deflected:0,done:false,lifted:new Set()};
    if(!ghost){
      if(b.kind==='basic'){s.basicRounds++;b.stars=(s.basicRounds-1)%3+1;s.basicCooldown=Math.max(.05,(snap.m.cd||1.6)*(owner.cdMul??1));}
      else s.cooldowns[snap.id]=Math.max(.05,(snap.m.cd||(b.kind==='heavy'?5:b.kind==='typhoon'?8:10))*(owner.cdMul??1));
      s.latest=b;s.counts[b.mode]=b.count;s.castCounts[b.mode]=(s.castCounts[b.mode]||0)+1;
    }
    // An active fan pose has visual priority without locking movement or existing actors.
    if(b.kind!=='basic'||!s.pose||s.pose.kind==='basic')s.pose=b;
    casts.push(b);owner.aim=aim;
    if(!ghost&&typeof G.NarutoTemari.onCast==='function') {
      const packet={...snap,m:{...snap.m},castId:b.serial,stars:b.stars,aim,x:b.x,y:b.y,
        targetPositions:list.map(e=>({x:e.x,y:e.y})),
        deflect:{start:.2,end:.4,range:80,halfAngle:Math.PI*.36,budget:b.budget}};
      G.NarutoTemari.onCast(owner,packet);
    }
    return true;
  }
  function cast(owner,m) {return canCast(owner,m)&&start(owner,snapshot(owner,m));}
  function ghost(owner,packet) {
    if(!owner||!packet||!supports(packet.mode??packet.m?.digiMode))return false;
    const m={...packet.m,id:packet.id,digiMode:packet.mode};
    return start(owner,{...packet,m},true);
  }
  function emitted(b) {
    b.emitted++;
    if(b.ghost)return;
    const s=state(b.owner);s.totalEmitted++;s.emittedByMode[b.mode]=(s.emittedByMode[b.mode]||0)+1;
  }
  const legal=b=>b.world===G.World&&(b.ghost?alive(b.owner):valid(b.owner));
  function recordCut(b) {b.cuts++;if(!b.ghost)state(b.owner).totalCuts++;}
  function hit(b,e,dx,dy,knock=0,splash=false) {
    if(b.ghost||!legal(b)||!alive(e))return;
    const owner=b.owner,m=b.m,mult=G.Types.mult(m.type||'flying',e.types),crit=Math.random()<b.critChance;
    const damage=b.damage*mult*G.Weather.mult(m.type||'flying')*(crit?1.5:1)*(G.NarutoSupport?.precisionMultiplier(owner,e)||1);
    e.hurt(damage,'#bcebd9',dx,dy,knock,crit?'crit':G.Types.label(mult),owner,m.id);
    owner.onDealt?.(damage);owner.dmgDealt=(owner.dmgDealt||0)+damage;
    if(splash)G.DamageSplash?.hit(owner,e,damage,'#bcebd9',m.id);
    if(m.burn)e.applyBurn?.(m.burn);if(m.poison)e.applyPoison?.(m.poison);if(m.slow)e.applySlow?.(m.slow);
    b.hits++;state(owner).hitEvents++;
  }
  function propHit(b,p) {
    if(b.ghost||!p||p.dead||p.hp<=0||!legal(b))return;
    G.World.damageProp(p,b.damage,'#bcebd9');b.props++;state(b.owner).propHits++;
  }
  function circleTargets(x,y,r) {
    return [...new Set(G.EnemyMgr.queryCircle(x,y,r+80))].filter(e=>alive(e)&&!e.friendly&&
      Math.hypot(e.x-x,e.y-y)<=r+(e.r||0)&&clearPath(x,y,e.x,e.y));
  }
  function props(x,y,r) {return G.World.propsInCircle?.(x,y,r)||[];}
  function emit(b,i) {
    const target=b.targets[i%b.targets.length],spread=b.kind==='basic'||b.kind==='heavy'?0:((i%5)/4-.5)*.14;
    const aim=b.aim+spread;
    const base={cast:b,owner:b.owner,world:b.world,index:i,x:b.x,y:b.y,sx:b.x,sy:b.y,aim,
      dx:Math.cos(aim),dy:Math.sin(aim),age:0,travel:0,phase:'travel',cuts:0,dead:false};
    if(b.kind==='basic'||b.kind==='heavy')waves.push({...base,phase:'grow',reach:0,fronts:[],knocked:new Set()});
    else if(b.kind==='typhoon') {
      const initial=b.aim+TAU*i/b.count;
      storms.push({...base,x:b.x,y:b.y,aim:initial,angle:initial,phase:'sweep',
        sweepDuration:1.2,lifetime:2.4,contacts:new Map(),propContacts:new Map(),previousPositions:new Map()});
    }
    else {
      // Fixed destinations are captured once. Obstacles stop travel before the obstacle.
      const distance=target?Math.min(b.range,Math.hypot(target.x-b.x,target.y-b.y)):b.range*.65;
      const angle=target?Math.atan2(target.y-b.y,target.x-b.x):b.aim;
      const offset=b.count>1?((i%5)-2)*Math.min(9,b.radius*.13):0;
      const tx=b.x+Math.cos(angle)*distance-Math.sin(angle)*offset,ty=b.y+Math.sin(angle)*distance+Math.cos(angle)*offset;
      summons.push({...base,tx,ty,aim:angle,dir:Math.cos(angle)<0?'left':'right',phase:'move',nextCut:Infinity,slash:0,
        anim:{},hp:1});
    }
    emitted(b);
  }
  const angleDelta=(a,b)=>Math.atan2(Math.sin(a-b),Math.cos(a-b));
  function inWave(w,e,previous) {
    const b=w.cast,r=e.r||0;
    if(b.geometryAge!==b.age){b.geometryAge=b.age;b.geometry=new WeakMap();}
    let g=b.geometry.get(e);
    if(!g||g.x!==e.x||g.y!==e.y||g.r!==r||g.ox!==w.x||g.oy!==w.y||g.aim!==w.aim||g.arc!==b.arc) {
      g={x:e.x,y:e.y,r,ox:w.x,oy:w.y,aim:w.aim,arc:b.arc,d:Math.hypot(e.x-w.x,e.y-w.y)};
      b.geometry.set(e,g);
    }
    if(g.d+r<previous-EPS||g.d>w.reach+r)return false;
    if(g.angle===undefined)g.angle=Math.abs(angleDelta(Math.atan2(e.y-w.y,e.x-w.x),w.aim))<=b.arc/2+Math.asin(Math.min(1,r/Math.max(1,g.d)));
    return g.angle;
  }
  function waveCandidates(b) {
    const count=G.EnemyMgr.all().length;
    if(b.waveQueryAge!==b.age||b.waveEnemyCount!==count) {
      b.waveQueryAge=b.age;b.waveEnemyCount=count;
      // Quantity copies share an origin. Cache only the raw broad phase;
      // each real front still checks live positions, life and line of sight.
      b.waveCandidates=[...new Set(G.EnemyMgr.queryCircle(b.x,b.y,b.range+80))];
    }
    return b.waveCandidates;
  }
  function advanceWave(w,dt) {
    const b=w.cast;w.age+=dt;
    w.reach=Math.min(b.range,b.speed*w.age);
    // Every recut is another advancing front, .08s behind the previous one.
    // A front only damages circles it actually crosses, once per target.
    while(w.cuts<b.R&&w.age+EPS>=w.cuts*.08) {
      w.fronts.push({started:w.cuts*.08,reach:0,hits:new Set(),props:new Set(),done:false});
      recordCut(b);w.cuts++;
    }
    for(const f of w.fronts) {
      if(f.done)continue;
      const previous=f.reach;f.reach=Math.min(b.range,Math.max(0,w.age-f.started)*b.speed);
      const reach=w.reach;w.reach=f.reach;
      if(!b.ghost||b.kind==='basic'||b.kind==='heavy')for(const e of waveCandidates(b))if(!f.hits.has(e)&&alive(e)&&!e.friendly&&
        inWave(w,e,previous)&&clearPath(w.x,w.y,e.x,e.y)) {
        f.hits.add(e);
        hit(b,e,Math.cos(w.aim),Math.sin(w.aim));
        if(b.kind==='basic')claimLift(b.owner,e,b);
        else claimPush(b.owner,e,b);
      }
      if(b.wavePropAge!==b.age){b.wavePropAge=b.age;b.waveProps=props(b.x,b.y,b.range);}
      for(const p of b.waveProps)if(!f.props.has(p)&&!p.dead&&p.hp>0&&
        inWave(w,p,previous)&&clearPath(w.x,w.y,p.x,p.y,1,p)) {
        f.props.add(p);propHit(b,p);
      }
      w.reach=reach;if(f.reach>=b.range-EPS)f.done=true;
    }
    if(w.cuts>=b.R&&w.fronts.every(f=>f.done))w.dead=true;
  }
  const petMove=owner=>owner.moves?.find(m=>m.digiMode==='temari-blade-dance');
  function petHome(a) {
    const serial=a.roamSerial=(a.roamSerial||0)+1;
    const noise=n=>{const v=Math.sin((a.index+1)*127.1+(serial+n)*311.7)*43758.5453;return v-Math.floor(v);};
    const free=(x,y)=>!G.World.projectileBlock?.(x,y,9)&&(!G.World.isFree||G.World.isFree(x,y,9,true));
    // Pick independent nearby destinations, rather than an offset that follows
    // every owner step. Prefer a clear route and keep resting space around them.
    for(const radiusScale of [1,.7,.4])for(let i=0;i<16;i++) {
      const angle=noise(i*2)*TAU,radius=(75+70*noise(i*2+1))*radiusScale;
      const x=a.owner.x+Math.cos(angle)*radius,y=a.owner.y+Math.sin(angle)*radius;
      if(free(x,y)&&clearPath(a.owner.x,a.owner.y,x,y,9)&&clearPath(a.x,a.y,x,y,9))return {x,y};
    }
    return {x:a.owner.x,y:a.owner.y};
  }
  // Short swept steps keep pets out of walls without teleporting them to a moving owner.
  function petTravel(a,tx,ty,distance) {
    const dx=tx-a.x,dy=ty-a.y,d=Math.hypot(dx,dy),amount=Math.min(d,distance);
    const steps=Math.max(1,Math.ceil(amount/5));let blocked=false;
    a.moving=amount>.1;
    if(d>.1){a.aim=Math.atan2(dy,dx);a.dir=dx<0?'left':'right';}
    for(let i=0;i<steps;i++) {
      const sx=dx/(d||1)*amount/steps,sy=dy/(d||1)*amount/steps;
      const free=(x,y)=>!G.World.projectileBlock?.(x,y,9)&&(!G.World.isFree||G.World.isFree(x,y,9,true));
      if(free(a.x+sx,a.y+sy)){a.x+=sx;a.y+=sy;}
      else if(free(a.x+sx,a.y)){a.x+=sx;blocked=true;}
      else if(free(a.x,a.y+sy)){a.y+=sy;blocked=true;}
      else {
        blocked=true;
        if(a.phase==='wander'||a.phase==='follow'||a.phase==='return') {
          const side=a.index%2?-1:1,length=Math.hypot(sx,sy);
          for(const turn of [Math.PI/3,Math.PI/2,Math.PI*2/3]) {
            const angle=a.aim+turn*side,x=a.x+Math.cos(angle)*length,y=a.y+Math.sin(angle)*length;
            if(free(x,y)){a.x=x;a.y=y;break;}
          }
        }
        break;
      }
    }
    return {arrived:Math.hypot(tx-a.x,ty-a.y)<3,blocked};
  }
  function petSnapshots(owner) {
    return summons.filter(a=>a.permanent&&a.owner===owner&&!a.dead).map(a=>({
      id:a.petId,index:a.index,x:a.x,y:a.y,tx:a.tx,ty:a.ty,phase:a.phase,age:a.age,
      aim:a.aim,dir:a.dir,cuts:a.cuts,slash:a.slash,lastCut:a.lastCut??null,
      cooldown:a.cooldown,moving:!!a.moving,cast:{...a.cast,owner:undefined,world:undefined,m:{...a.cast.m}}
    }));
  }
  function publishPets(owner) {
    const s=states.get(owner);if(!s||s.remotePets)return;
    s.petSync=0;G.NarutoTemari.onPets?.(owner,{serial:++petPacketSequence,pets:petSnapshots(owner)});
  }
  function syncPets(owner) {
    if(!valid(owner))return;
    const s=state(owner),m=petMove(owner),count=m?Math.floor(1.25**quantity(owner)):0;
    const owned=summons.filter(a=>a.owner===owner&&a.permanent&&!a.remotePet);
    let changed=false;
    for(const a of owned)if(a.index>=count){a.dead=true;summons.splice(summons.indexOf(a),1);changed=true;}
    const indices=new Set(owned.filter(a=>!a.dead).map(a=>a.index));
    for(let i=0;i<count;i++)if(!indices.has(i)) {
      indices.add(i);
      const b={...snapshot(owner,m),owner,world:G.World,ghost:false,serial:++sequence};
      const a={owner,world:G.World,cast:b,permanent:true,petId:'pet-'+(++petSequence),index:i,
        x:owner.x,y:owner.y,age:0,phase:'wander',roamTarget:null,roamSerial:0,restUntil:0,cuts:0,slash:0,nextCut:Infinity,cooldown:0,
        aim:owner.aim||0,dir:owner.dir||'right',anim:{},hp:1,dead:false};
      summons.push(a);changed=true;
      s.totalEmitted++;s.emittedByMode[b.mode]=(s.emittedByMode[b.mode]||0)+1;
    }
    if(changed)publishPets(owner);
    s.hasPetRoster=count>0;
  }
  function applyNetworkPets(owner,packet) {
    if(!owner||!packet||!Array.isArray(packet.pets))return false;
    if(packet.pets.some(p=>!p||typeof p.id!=='string'||![p.x,p.y,p.age,p.index].every(Number.isFinite)))return false;
    const s=state(owner);s.remotePets=true;
    const ids=new Set(packet.pets.map(p=>p.id));
    for(let i=summons.length-1;i>=0;i--)if(summons[i].owner===owner&&summons[i].remotePet&&!ids.has(summons[i].petId))summons.splice(i,1);
    for(const p of packet.pets) {
      let a=summons.find(a=>a.owner===owner&&a.remotePet&&a.petId===p.id);
      if(!a){a={owner,world:G.World,permanent:true,remotePet:true,petId:p.id,anim:{},hp:1};summons.push(a);}
      Object.assign(a,{index:p.index,x:p.x,y:p.y,tx:p.tx,ty:p.ty,phase:p.phase,age:p.age,aim:p.aim,dir:p.dir,
        cuts:p.cuts,slash:p.slash,lastCut:p.lastCut,cooldown:p.cooldown,moving:p.moving,dead:false,
        cast:{...p.cast,m:{...p.cast?.m},owner,world:G.World,ghost:true,kind:'summon'}});
    }
    return true;
  }
  function beginPetAttack(a,m,target) {
    const owner=a.owner,s=state(owner),b={...snapshot(owner,m),owner,world:G.World,ghost:false,serial:++sequence};
    a.cast=b;a.phase='move';a.roamTarget=null;a.restUntil=0;a.cuts=0;a.slash=0;a.nextCut=Infinity;
    const dx=target.x-a.x,dy=target.y-a.y,angle=Math.atan2(dy,dx);
    const offset=b.K>1?((a.index%5)-2)*Math.min(9,b.radius*.13):0;
    a.tx=target.x-Math.sin(angle)*offset;
    a.ty=target.y+Math.cos(angle)*offset;
    a.aim=angle;a.cooldown=Math.max(.05,(m.cd||10)*(owner.cdMul??1));
    s.latest=b;s.counts[b.mode]=b.K;s.castCounts[b.mode]=(s.castCounts[b.mode]||0)+1;
    G.NarutoTemari.onPetAttack?.(owner,a,{...b,owner:undefined,world:undefined,m:{...b.m}});
  }
  function petTargets(owner,m,queries) {
    const r=rangeFor(owner,m),enemies=G.EnemyMgr.all();
    let q=queries?.get(owner);
    // queryCircle already filters live positions. Guard its full input so a
    // hit callback that moves/replaces an enemy cannot hide a later target.
    if(!q||q.x!==owner.x||q.y!==owner.y||q.r!==r||q.inputs.length!==enemies.length||
      q.inputs.some((s,i)=>s.e!==enemies[i]||s.x!==s.e.x||s.y!==s.e.y||s.r!==s.e.r||s.dead!==s.e.dead)) {
      q={x:owner.x,y:owner.y,r,inputs:enemies.map(e=>({e,x:e.x,y:e.y,r:e.r,dead:e.dead})),
        candidates:[...new Set(G.EnemyMgr.queryCircle(owner.x,owner.y,r))]};
      queries?.set(owner,q);
    }
    // Range, life, priority and line of sight remain live for each pet.
    return targets(owner,m,q.candidates);
  }
  function advanceSummon(a,dt,queries) {
    if(a.remotePet)return;
    const m=petMove(a.owner);if(!m){a.dead=true;return;}
    a.age+=dt;a.cooldown=Math.max(0,a.cooldown-dt);a.moving=false;
    if(a.phase==='follow')a.phase='wander';
    if(a.phase==='wander'||a.phase==='return') {
      const ownerDistance=Math.hypot(a.x-a.owner.x,a.y-a.owner.y);
      const destination=a.roamTarget;
      const destinationDistance=destination?Math.hypot(destination.x-a.owner.x,destination.y-a.owner.y):Infinity;
      if(!destination||(destination.arrived&&a.age>=a.restUntil)||destinationDistance>175||destinationDistance<55||a.blockedTime>.45) {
        a.roamTarget=petHome(a);a.restUntil=0;a.blockedTime=0;
      }
      if(ownerDistance>220){a.phase='return';a.restUntil=0;}
      if(a.age>=a.restUntil) {
        const speed=a.phase==='return'?Math.max(a.cast.speed,(a.owner.speed||140)*1.25):100*mastery(a.owner).speed;
        const travel=petTravel(a,a.roamTarget.x,a.roamTarget.y,speed*dt);
        a.blockedTime=travel.blocked?(a.blockedTime||0)+dt:0;
        if(travel.arrived) {
          a.phase='wander';a.moving=false;
          a.restUntil=a.age+.55+((a.roamSerial*37+a.index*19)%100)/100;
          a.roamTarget={...a.roamTarget,arrived:true};
        }
      }
      if(a.phase==='wander'&&!a.owner.frozen&&a.cooldown<=EPS) {
        const list=petTargets(a.owner,m,queries);
        if(list.length)beginPetAttack(a,m,list[a.index%list.length]);
      }
    } else if(a.phase==='move') {
      const travel=petTravel(a,a.tx,a.ty,a.cast.speed*dt);
      if(travel.blocked){a.phase='return';a.roamTarget=null;}
      else if(travel.arrived){a.phase='prepare';a.nextCut=a.age+.16;}
    }
    const b=a.cast;
    while((a.phase==='prepare'||a.phase==='slash')&&a.cuts<b.C&&a.age+EPS>=a.nextCut) {
      a.phase='slash';a.slash=a.cuts;recordCut(b);a.cuts++;
      const aim=a.aim+(a.cuts%2?.35:-.35);
      for(const e of circleTargets(a.x,a.y,b.radius))hit(b,e,Math.cos(aim),Math.sin(aim));
      for(const p of props(a.x,a.y,b.radius))if(Math.hypot(p.x-a.x,p.y-a.y)<=b.radius+(p.r||0)&&clearPath(a.x,a.y,p.x,p.y,1,p))propHit(b,p);
      a.lastCut=a.nextCut;a.nextCut+=.12;
    }
    if(a.phase==='slash'&&a.cuts>=b.C&&a.age-a.lastCut>=.16){a.phase='return';a.roamTarget=null;}
  }
  function liftPacket(lift,reason) {
    return {castId:lift.cast.castId??lift.cast.serial,age:lift.age,duration:lift.duration,height:lift.height,reason};
  }
  function releaseLift(e,reason='complete',silent=false) {
    const lift=lifts.get(e);if(!lift)return false;lifts.delete(e);
    if(!silent&&!lift.remote)G.NarutoTemari.onLiftRelease?.(lift.owner,e,liftPacket(lift,reason),lift.cast);
    return true;
  }
  function claimLift(owner,e,b,packet=null,remote=false) {
    if(!alive(e)||e.boss||e.elite||e.legend||e.judge||pushes.has(e))return false;
    if(!remote) {
      if(b.mode!=='temari-wind'||b.lifted.has(e))return false;
      b.lifted.add(e);
      const authority=G.NarutoTemari.mayLift?.(owner,e,b);
      if(b.ghost?authority!==true:authority===false)return false;
    }
    if(lifts.has(e))return false;
    const lift={enemy:e,owner,cast:b,world:G.World,age:packet?.age??0,duration:.30,height:22,
      remote,authoritative:packet?.authoritative!==false};
    lifts.set(e,lift);if(lift.authoritative)e.kx=e.ky=0;
    if(!remote)G.NarutoTemari.onLift?.(owner,e,liftPacket(lift),b);
    return true;
  }
  function applyNetworkLift(owner,e,packet) {
    if(!owner||!e||!packet||packet.castId==null||!Number.isFinite(packet.age??0)||(packet.age??0)<0||(packet.age??0)>=.30)return false;
    const existing=lifts.get(e);
    if(existing)return (existing.cast.castId??existing.cast.serial)===packet.castId;
    const b={owner,world:G.World,ghost:true,castId:packet.castId,serial:packet.castId,kind:'basic',mode:'temari-wind'};
    return claimLift(owner,e,b,packet,true);
  }
  function releaseNetworkLift(e,castId) {
    const lift=lifts.get(e);
    return !!lift&&(castId==null||(lift.cast.castId??lift.cast.serial)===castId)&&releaseLift(e,'network',true);
  }
  function held(e) {
    const lift=lifts.get(e);return !!lift&&lift.world===G.World&&alive(e)&&alive(lift.owner)&&lift.age<lift.duration-EPS;
  }
  function liftFor(e) {
    const lift=lifts.get(e);return held(e)?Math.sin(Math.PI*lift.age/lift.duration)*lift.height:0;
  }
  function advanceLifts(dt) {
    for(const [e,lift] of lifts) {
      if(lift.world!==G.World||!alive(e)||!legal(lift.cast)){releaseLift(e,'invalid');continue;}
      lift.age=Math.min(lift.duration,lift.age+dt);
      if(lift.authoritative)e.kx=e.ky=0;
      if(lift.age>=lift.duration-EPS)releaseLift(e);
    }
  }
  const strong=e=>!!(e.boss||e.elite||e.legend||e.judge);
  const externallyHeld=e=>!!(G.NarutoLee?.bound?.(e)||G.NarutoGaara?.rooted?.(e));
  function pushPacket(p,reason) {
    return {castId:p.cast.castId??p.cast.serial,x:p.x,y:p.y,dx:p.dx,dy:p.dy,distance:p.distance,
      age:p.age,duration:p.duration,travelled:p.travelled,reason};
  }
  function releasePush(e,reason='complete',silent=false) {
    const p=pushes.get(e);if(!p)return false;pushes.delete(e);
    if(!silent&&!p.remote)G.NarutoTemari.onPushRelease?.(p.owner,e,pushPacket(p,reason),p.cast);
    return true;
  }
  function claimPush(owner,e,b,packet=null,remote=false) {
    if(!alive(e)||strong(e)||externallyHeld(e)||pushes.has(e))return false;
    if(!remote) {
      const authority=G.NarutoTemari.mayPush?.(owner,e,b);
      if(b.ghost?authority!==true:authority===false)return false;
    }
    const angle=Math.atan2(e.y-b.y,e.x-b.x),p={enemy:e,owner,cast:b,world:G.World,
      x:packet?.x??e.x,y:packet?.y??e.y,dx:packet?.dx??Math.cos(angle),dy:packet?.dy??Math.sin(angle),
      distance:packet?.distance??b.pushDistance,duration:.35,age:packet?.age??0,travelled:packet?.travelled??0,
      remote,authoritative:packet?.authoritative!==false};
    // Escape takes priority over our own lifts and circular carry. External
    // character controllers retain their movement lease.
    releaseLift(e,'push');releaseOrbit(e,'push');pushes.set(e,p);
    if(p.authoritative)e.kx=e.ky=0;
    if(!remote)G.NarutoTemari.onPush?.(owner,e,pushPacket(p),b);
    return true;
  }
  function applyNetworkPush(owner,e,packet) {
    if(!owner||!e||!packet||packet.castId==null||
      ![packet.x,packet.y,packet.dx,packet.dy,packet.distance,packet.age??0,packet.travelled??0].every(Number.isFinite)||
      packet.distance<0||(packet.age??0)<0||(packet.age??0)>=.35||
      Math.abs(Math.hypot(packet.dx,packet.dy)-1)>.01||
      (packet.travelled??0)<0||(packet.travelled??0)>packet.distance)return false;
    const current=pushes.get(e);
    if(current)return (current.cast.castId??current.cast.serial)===packet.castId;
    const b={owner,world:G.World,ghost:true,kind:'heavy',mode:'temari-great-scythe',castId:packet.castId,serial:packet.castId};
    return claimPush(owner,e,b,packet,true);
  }
  function releaseNetworkPush(e,castId) {
    const p=pushes.get(e);return !!p&&(castId==null||(p.cast.castId??p.cast.serial)===castId)&&releasePush(e,'network',true);
  }
  function pushed(e) {
    const p=pushes.get(e);return !!p&&p.world===G.World&&alive(e)&&alive(p.owner)&&p.age<p.duration-EPS;
  }
  function advancePushes(dt) {
    for(const [e,p] of pushes) {
      if(p.world!==G.World||!alive(e)||!alive(p.owner)||(!p.remote&&!legal(p.cast))||externallyHeld(e)) {
        releasePush(e,'invalid');continue;
      }
      p.age=Math.min(p.duration,p.age+dt);
      const t=p.age/p.duration,target=p.distance*(1-(1-t)**3),distance=Math.max(0,target-p.travelled);
      if(p.authoritative) {
        const steps=Math.max(1,Math.ceil(distance/4));let blocked=false;
        if(steps>2048){releasePush(e,'step-limit');continue;}
        for(let i=0;i<steps;i++) {
          const amount=distance/steps,x=e.x+p.dx*amount,y=e.y+p.dy*amount;
          if((G.World.isFree&&!G.World.isFree(x,y,e.r||8,true))||G.World.isWall?.(x,y)) {blocked=true;break;}
          e.x=x;e.y=y;p.travelled+=amount;
        }
        e.kx=e.ky=0;
        if(blocked){releasePush(e,'blocked');continue;}
      } else p.travelled=target;
      if(p.age>=p.duration-EPS)releasePush(e);
    }
  }
  function orbitPacket(o,reason) {
    return {castId:o.cast.castId??o.cast.serial,x:o.x,y:o.y,radius:o.radius,startAngle:o.startAngle,
      angle:o.angle,age:o.age,duration:o.duration,reason};
  }
  function releaseOrbit(e,reason='complete',silent=false) {
    const o=orbits.get(e);if(!o)return false;orbits.delete(e);
    if(!silent&&!o.remote)G.NarutoTemari.onRelease?.(o.owner,e,orbitPacket(o,reason),o.cast);
    return true;
  }
  function claimOrbit(owner,e,b,packet=null,remote=false) {
    if(orbits.has(e)||pushes.has(e)||!alive(e)||strong(e))return null;
    const x=packet?.x??b.x,y=packet?.y??b.y;
    const o={enemy:e,owner,cast:b,world:G.World,x,y,radius:packet?.radius??Math.hypot(e.x-x,e.y-y),
      startAngle:packet?.startAngle??Math.atan2(e.y-y,e.x-x),age:packet?.age??0,duration:1.2,
      angle:packet?.startAngle??Math.atan2(e.y-y,e.x-x),remote,authoritative:packet?.authoritative!==false};
    orbits.set(e,o);
    if(!remote)G.NarutoTemari.onCapture?.(owner,e,orbitPacket(o),b);
    return o;
  }
  function applyNetworkOrbit(owner,e,packet) {
    if(!owner||!e||!packet||![packet.x,packet.y,packet.radius,packet.startAngle].every(Number.isFinite))return false;
    const existing=orbits.get(e);
    if(existing)return (existing.cast.castId??existing.cast.serial)===packet.castId;
    const b={owner,world:G.World,ghost:true,castId:packet.castId,serial:packet.castId,x:packet.x,y:packet.y};
    return !!claimOrbit(owner,e,b,packet,true);
  }
  function releaseNetworkOrbit(e,castId) {
    const o=orbits.get(e);return !!o&&(castId==null||(o.cast.castId??o.cast.serial)===castId)&&releaseOrbit(e,'network',true);
  }
  function advanceOrbits(dt) {
    for(const [e,o] of orbits) {
      if(o.world!==G.World||!alive(e)||!alive(o.owner)||(!o.remote&&!legal(o.cast))) {releaseOrbit(e,'invalid');continue;}
      if(held(e))continue;
      const next=Math.min(o.duration,o.age+dt),end=o.startAngle-TAU*next/o.duration;
      if(o.authoritative) {
        // Subdivide the true circular path, including any small native separation drift.
        const distance=Math.abs(end-o.angle)*o.radius;
        const steps=Math.max(1,Math.ceil(distance/4));
        if(steps>2048){releaseOrbit(e,'step-limit');continue;}
        let blocked=false;
        for(let i=1;i<=steps;i++) {
          const angle=o.angle+(end-o.angle)*i/steps,x=o.x+Math.cos(angle)*o.radius,y=o.y+Math.sin(angle)*o.radius;
          if((G.World.isFree&&!G.World.isFree(x,y,e.r||8,true))||G.World.isWall?.(x,y)) {blocked=true;break;}
          e.x=x;e.y=y;
        }
        e.kx=e.ky=0;
        if(blocked){releaseOrbit(e,'blocked');continue;}
      }
      o.age=next;o.angle=end;
      if(next>=o.duration-EPS)releaseOrbit(e);
    }
  }
  function advanceStorm(a,dt) {
    const b=a.cast,previous=Math.min(1,a.age/a.sweepDuration);a.age+=dt;
    const progress=Math.min(1,a.age/a.sweepDuration);a.angle=a.aim+TAU*progress;
    a.phase=progress<1?'sweep':a.age<a.lifetime?'tail':'fade';
    if(previous<1) {
      // All phases share one fixed eye: reuse this frame's spatial query.
      if(b.stormQueryAge!==b.age) {b.stormQueryAge=b.age;b.stormCandidates=circleTargets(a.x,a.y,b.radius);}
      const crossed=e=>{
        const bearing=Math.atan2(e.y-a.y,e.x-a.x),saved=a.previousPositions.get(e);
        const before=saved&&Math.abs(saved.age-(a.age-dt))<EPS?saved.bearing:bearing;
        a.previousPositions.set(e,{bearing,age:a.age});
        const from=before-a.aim-previous*TAU;
        const to=from+angleDelta(bearing,before)-(progress-previous)*TAU;
        const padding=Math.asin(Math.min(1,(e.r||0)/Math.max(1,Math.hypot(e.x-a.x,e.y-a.y))));
        // Test the swept relative angles, rather than only the end-of-frame pose.
        // Counter-rotating carried enemies genuinely cross each independent front.
        return Math.ceil((Math.min(from,to)-padding-EPS)/TAU)<=Math.floor((Math.max(from,to)+padding+EPS)/TAU);
      };
      for(const e of b.stormCandidates)if(alive(e)&&!a.contacts.has(e)&&crossed(e)) {
        const contact={started:a.age,cuts:0};a.contacts.set(e,contact);
        if(!strong(e)&&!orbits.has(e)&&!pushes.has(e)) {
          const authority=G.NarutoTemari.mayControl?.(b.owner,e,b);
          if(b.ghost?authority===true:authority!==false)claimOrbit(b.owner,e,b);
          else if(!b.ghost)G.NarutoTemari.requestOrbit?.(b.owner,e,{castId:b.castId??b.serial,x:a.x,y:a.y,
            radius:Math.hypot(e.x-a.x,e.y-a.y),startAngle:Math.atan2(e.y-a.y,e.x-a.x),age:0,duration:1.2},b);
        }
      }
      if(!b.ghost)for(const p of props(a.x,a.y,b.radius))if(!a.propContacts.has(p)&&crossed(p)&&
        Math.hypot(p.x-a.x,p.y-a.y)<=b.radius+(p.r||0)&&clearPath(a.x,a.y,p.x,p.y,1,p))a.propContacts.set(p,{started:a.age,cuts:0});
    }
    for(const [e,c] of a.contacts)while(c.cuts<b.C&&a.age+EPS>=c.started+c.cuts*1.2/Math.max(1,b.C-1)) {
      c.cuts++;a.cuts++;recordCut(b);
      if(alive(e)&&Math.hypot(e.x-a.x,e.y-a.y)<=b.radius+(e.r||0)&&clearPath(a.x,a.y,e.x,e.y))hit(b,e,a.x-e.x,a.y-e.y);
    }
    for(const [p,c] of a.propContacts)while(c.cuts<b.C&&a.age+EPS>=c.started+c.cuts*1.2/Math.max(1,b.C-1)) {
      c.cuts++;if(Math.hypot(p.x-a.x,p.y-a.y)<=b.radius+(p.r||0)&&clearPath(a.x,a.y,p.x,p.y,1,p))propHit(b,p);
    }
    if(a.age>=a.lifetime+.24)a.dead=true;
  }
  function blockable(p) {
    return p.friendly===false&&p.interceptable===true&&!p.unblockable&&!p.guardUnblockable&&!p.uninterceptable&&
      !p.special&&!p.bossSpecial&&!p.orb&&!p.beam&&!p.laser&&!p.ground&&!p.groundField&&!p.hazard&&
      [p.x,p.y,p.vx,p.vy].every(Number.isFinite);
  }
  function deflect(b,previous) {
    if(b.ghost||!b.empowered||b.deflected>=b.budget||b.age<=previous+EPS||b.age<.2||previous>.4)return;
    const lo=Math.max(.2,previous),hi=Math.min(.4,b.age);if(hi<lo)return;
    const dt=b.age-previous;
    for(const p of [...(G.Projectiles?.all()||[])]) {
      if(b.deflected>=b.budget)break;if(!blockable(p))continue;
      // Test the actual projectile segment inside this frame's active window.
      const sx=Number.isFinite(p.px)?p.px:p.x-p.vx*dt,sy=Number.isFinite(p.py)?p.py:p.y-p.vy*dt;
      const n=Math.max(1,Math.ceil(Math.hypot(p.x-sx,p.y-sy)/4));let contact=false;
      for(let i=0;i<=n;i++) {
        const t=i/n,age=previous+dt*t;if(age<lo-EPS||age>hi+EPS)continue;
        const x=sx+(p.x-sx)*t,y=sy+(p.y-sy)*t,dx=x-b.owner.x,dy=y-b.owner.y;
        if(Math.hypot(dx,dy)<=80+(p.r||0)&&Math.abs(angleDelta(Math.atan2(dy,dx),b.aim))<=Math.PI*.36&&
          clearPath(b.owner.x,b.owner.y,x,y)){contact=true;break;}
      }
      if(contact&&G.NarutoTemari.mayIntercept?.(b.owner,p,b)!==false){G.Projectiles.remove(p);b.deflected++;state(b.owner).intercepted++;
        G.NarutoTemari.onIntercept?.(b.owner,p,b);}
    }
  }
  function clear(owner) {
    for(const [e,p] of pushes)if(!owner||p.owner===owner)releasePush(e,'clear');
    for(const [e,lift] of lifts)if(!owner||lift.owner===owner)releaseLift(e,'clear');
    for(const [e,o] of orbits)if(!owner||o.owner===owner)releaseOrbit(e,'clear');
    for(const [actor,s] of states)if((!owner||actor===owner)&&!s.remotePets&&s.hasPetRoster)G.NarutoTemari.onPets?.(actor,{serial:++petPacketSequence,pets:[]});
    if(owner)states.delete(owner);else states.clear();
    for(const list of [casts,blades,waves,summons,storms])for(let i=list.length-1;i>=0;i--)if(!owner||list[i].owner===owner)list.splice(i,1);
  }
  function update(dt) {
    if(G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    for(const owner of [G.Game.player,...(G.SelfClones?.actors?.()||[])])if(valid(owner))syncPets(owner);
    advancePushes(dt);
    advanceLifts(dt);
    advanceOrbits(dt);
    for(const [owner,s] of states) {
      const remote=alive(owner)&&(s.remotePets||casts.some(b=>b.owner===owner&&b.ghost)||[...lifts.values()].some(lift=>lift.owner===owner&&lift.cast.ghost)||[...pushes.values()].some(p=>p.owner===owner&&p.cast.ghost));
      if(s.world!==G.World||(!valid(owner)&&!remote)){clear(owner);continue;}
      // Freeze prevents new actions; already released winds and summons keep time.
      s.clock+=dt;
      if(!s.remotePets&&s.hasPetRoster){s.petSync=(s.petSync||0)+dt;if(s.petSync+EPS>=.1)publishPets(owner);}
      if(s.pose&&s.clock-s.pose.started>=s.pose.duration)s.pose=null;
    }
    for(let i=casts.length-1;i>=0;i--) {
      const b=casts[i];if(!legal(b)){casts.splice(i,1);continue;}
      const previous=b.age;b.age=state(b.owner).clock-b.started;deflect(b,Math.max(previous,b.interceptedThrough||0));
      const releaseSpan=b.kind==='typhoon'?0:b.kind==='basic'?.12:.16;
      while(b.emitted<b.count&&b.age+EPS>=b.release+releaseSpan*b.emitted/b.count)emit(b,b.emitted);
      if(b.emitted===b.count&&b.age>Math.max(.41,b.release+releaseSpan)&&
        !blades.some(a=>a.cast===b)&&!waves.some(a=>a.cast===b)&&!summons.some(a=>a.cast===b)&&!storms.some(a=>a.cast===b))casts.splice(i,1);
    }
    const petQueries=new Map();
    for(const [list,advance] of [[waves,advanceWave],[summons,advanceSummon],[storms,advanceStorm]])for(let i=list.length-1;i>=0;i--) {
      const a=list[i];if(!legal(a.cast)){list.splice(i,1);continue;}
      // A new actor only receives time after its individual release in this frame.
      const born=a.cast.release+(a.cast.kind==='typhoon'?0:a.cast.kind==='basic'?.12:.16)*a.index/a.cast.count;
      const elapsed=a.permanent?dt:Math.min(dt,Math.max(0,a.cast.age-born-a.age));if(elapsed>0)advance(a,elapsed,petQueries);
      // Cast age continues after release scheduling has completed.
      if(a.dead)list.splice(i,1);
    }
  }
  function activeFor(owner) {
    const s=states.get(owner);return s?.world===G.World&&alive(owner)?s.pose:null;
  }
  function stateFor(owner) {
    const s=states.get(owner);if(!s||!valid(owner)||s.world!==G.World)return null;
    const p=mastery(owner),q=s.latest;
    return {owner,pose:s.pose,latest:q,Q:p.Q,L:p.L,N:Math.floor(3*1.25**p.Q),R:p.R,W:1,K:Math.floor(1.25**p.Q),C:petMove(owner)?snapshot(owner,petMove(owner)).C:q?.C||0,
      petPhases:summons.filter(a=>a.owner===owner&&a.permanent&&!a.dead).reduce((out,a)=>(out[a.phase]=(out[a.phase]||0)+1,out),{}),
      T:Math.floor(1.25**p.Q),P:[3,4,5,6,8][rank(owner.moves?.find(m=>m.digiMode==='temari-typhoon'))-1]+(p.L?p.L+p.Q:0),
      basicRounds:s.basicRounds,basicCooldown:s.basicCooldown,cooldowns:{...s.cooldowns},totalEmitted:s.totalEmitted,
      emittedByMode:{...s.emittedByMode},castCounts:{...s.castCounts},counts:{...s.counts},totalCuts:s.totalCuts,hitEvents:s.hitEvents,propHits:s.propHits,
      intercepted:s.intercepted,blades:blades.filter(a=>a.owner===owner).length,waves:waves.filter(a=>a.owner===owner).length,
      orbits:[...orbits.values()].filter(o=>o.owner===owner).length,summons:summons.filter(a=>a.owner===owner).length,storms:storms.filter(a=>a.owner===owner).length,pendingCuts:[...waves,...summons,...storms].filter(a=>a.owner===owner).reduce((n,a)=>n+(a.cast.kind==='typhoon'?[...a.contacts.values()].reduce((v,c)=>v+a.cast.C-c.cuts,0):(a.cast.kind==='summon'?(['wander','follow','return'].includes(a.phase)?a.cuts:a.cast.C):a.cast.R)-a.cuts),0)};
  }
  function air(ctx) {
    G.TemariCycloneVFX?.drawAir(ctx,{storms,orbits:[...orbits.values()],pushes:[...pushes.values()],blades,waves,summons,states:[...states.values()]});
  }
  function ground(ctx) {
    G.TemariCycloneVFX?.drawGround(ctx,{storms,orbits:[...orbits.values()],summons});
  }
  // Projectile movement precedes native hit resolution. Intercept here so a shot
  // crossing both the fan and the owner cannot damage the owner first.
  const oldProjectiles=G.Projectiles.update;
  if(oldProjectiles)G.Projectiles.update=function(dt,owner,enemies) {
    const result=oldProjectiles.call(this,dt,owner,enemies);
    if(G.Game.state==='playing'&&Number.isFinite(dt)&&dt>0)for(const b of casts) {
      if(!legal(b)||b.ghost||!b.empowered)continue;
      const age=b.age,end=state(b.owner).clock-b.started+dt;
      b.age=end;deflect(b,Math.max(age,b.interceptedThrough||0));b.interceptedThrough=end;b.age=age;
    }
    return result;
  };
  const oldEnemyUpdate=G.Enemy?.prototype.update;
  if(oldEnemyUpdate)G.Enemy.prototype.update=function(...args) {
    const lease=orbits.get(this),lift=lifts.get(this),push=pushes.get(this),x=this.x,y=this.y;
    const result=oldEnemyUpdate.apply(this,args);
    if(((lease?.authoritative&&orbits.get(this)===lease)||(lift?.authoritative&&lifts.get(this)===lift&&held(this))||
      (push?.authoritative&&pushes.get(this)===push&&!externallyHeld(this)))&&alive(this)) {this.x=x;this.y=y;this.kx=this.ky=0;}
    return result;
  };
  const oldTick=combat.tick,oldUpdate=combat.updateFields,oldClear=combat.clearFields,oldAir=combat.drawAirFields,oldGround=combat.drawGroundFields;
  combat.tick=function(dt,owner,now) {
    if((owner?.mon?.dex??owner?.dex)!==30011)return oldTick.call(this,dt,owner,now);
    if(G.Game.state!=='playing'||!valid(owner)||owner.frozen||!Number.isFinite(dt)||dt<=0)return;
    const s=state(owner);s.basicCooldown=Math.max(0,s.basicCooldown-dt);
    // Active recovery follows the selected group, matching the native move timer.
    // The private remaining time still rejects setActive's shortened move.t.
    const active=owner.activeGroup?.()||[];
    for(const move of active)if(Object.hasOwn(s.cooldowns,move.id)) {
      const remaining=s.cooldowns[move.id];
      if(remaining>0)move.t=Math.max(move.t||0,remaining);
      s.cooldowns[move.id]=Math.max(0,remaining-dt);
    }
    const result=oldTick.call(this,dt,owner,now),m=owner.moves?.find(m=>m.digiMode==='temari-wind');
    if(m&&canCast(owner,m)) {
      const move={...m,dmg:m.dmg*(G.NarutoSupport?.takeAttackBonus(owner)||1)};
      owner.cast?.(m);cast(owner,move);m.castAt=performance.now();
    }
    return result;
  };
  combat.updateFields=function(dt){const result=oldUpdate.call(this,dt);update(dt);return result;};
  combat.clearFields=function(owner){const result=oldClear.call(this,owner);clear(owner);return result;};
  combat.drawAirFields=function(ctx){oldAir.call(this,ctx);air(ctx);};
  combat.drawGroundFields=function(ctx){oldGround.call(this,ctx);ground(ctx);};
  G.NarutoTemari={supports,canCast,cast,clear,update,activeFor,stateFor,snapshot,ghost,mastery,rangeFor,heavyFor,
    pushed,pushFor:e=>pushes.get(e)||null,pushForState:e=>pushes.get(e)||null,applyNetworkPush,releaseNetworkPush,mayPush:null,onPush:null,onPushRelease:null,
    syncPets,petSnapshots,applyNetworkPets,onPets:null,onPetAttack:null,
    held,liftFor,liftForState:e=>lifts.get(e)||null,applyNetworkLift,releaseNetworkLift,mayLift:null,onLift:null,onLiftRelease:null,
    onCast:null,onIntercept:null,mayIntercept:null,mayControl:null,onCapture:null,onRelease:null,requestOrbit:null,applyNetworkOrbit,releaseNetworkOrbit,
    orbitFor:e=>orbits.get(e)||null,get orbits(){return [...orbits.values()];},get casts(){return casts;},get blades(){return blades;},get waves(){return waves;},get summons(){return summons;},get storms(){return storms;}};
})();
