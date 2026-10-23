/* Tenten's actor-owned physical ninja tools. Visual poses never gate combat. */
(() => {
  if (G.NarutoTenten) return;
  const C = G.Combat, TAU = Math.PI * 2, states = new Map(), weapons = [], blasts = [], impacts = [];
  const modes = new Set(['tenten-kunai','tenten-fuma','tenten-mastery','tenten-bounce','tenten-guard','tenten-tags','tenten-twin']);
  const tagGrid = new Map(), CELL = 64;
  const twinTools=[
    {kind:'shuriken',scale:1.1,palette:'silver'}, {kind:'kunai',scale:.85,palette:'blue'},
    {kind:'axe',scale:1.5,palette:'bronze'}, {kind:'senbon',scale:.7,palette:'silver'},
    {kind:'spear',scale:1.35,palette:'blue'}, {kind:'sickle',scale:1.2,palette:'dark'},
    {kind:'chakram',scale:1.05,palette:'bronze'}, {kind:'sword',scale:1.25,palette:'silver'}
  ];
  const alive = a => a && !a.dead && a.hp > 0;
  const controlled = a => a === G.Game.player || !!G.SelfClones?.isActor(a);
  const valid = a => alive(a) && controlled(a) && (a.mon?.dex ?? a.dex) === 30009;
  const supports = mode => modes.has(mode);
  const stage = m => m?.moves ? (m.moves.find(x=>x.id==='naruto-tenten-mastery')?.lvl||0) : Math.max(1, Math.min(5, m?.lvl || 1));
  function state(owner) {
    let s = states.get(owner);
    if (!s) { s = {owner, world:G.World, basicCooldown:0, batches:[], pose:null, lastCount:0, clock:0, chargeUntil:0, recoveredAt:-Infinity, release:null, comboBlasts:0, totalEmitted:0, emittedByMode:{}, castCounts:{}, counts:{}}; states.set(owner,s); }
    return s;
  }
  function mastery(owner) {
    const m = owner.moves?.find(m => m.id === 'naruto-tenten-mastery');
    const i = stage(m)-1;
    return {pierce:m ? [2,3,4,5,6][i] : 0, speed:m ? [1.10,1.20,1.40,1.80,2.00][i] : 1,
      range:m ? (i+1)*100 : 0};
  }
  const rangeBonus = (owner,m) => m.tentenRangeBonusAtCast ?? mastery(owner).range;
  const rangeFor = (owner,m) => (m.range||300)+rangeBonus(owner,m);
  function bounceCount(owner) {
    const skill=owner?.moves?.find(m=>m.id==='naruto-tenten-bounce');
    return skill ? Math.max(1,Math.floor(skill.lvl||1))+(G.Quantity?.bonus(owner)||0) : 0;
  }
  function clearPath(ax,ay,bx,by,r=1,targetProp=null) {
    const n = Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/6));
    for(let i=1;i<=n;i++) {
      const block=G.World.projectileBlock(ax+(bx-ax)*i/n,ay+(by-ay)*i/n,r);
      // An AOE may reach the surface of its own target prop, never unrelated cover.
      if(block&&block!==targetProp)return false;
    }
    return true;
  }
  function targets(owner,m) {
    const r = rangeFor(owner,m);
    const list = [...new Set(G.EnemyMgr.queryCircle(owner.x,owner.y,r))].filter(e => alive(e) &&
      Math.hypot(e.x-owner.x,e.y-owner.y)<=r && clearPath(owner.x,owner.y,e.x,e.y));
    // An actor's assigned target remains first; following weapons spread through the others.
    return list.sort((a,b) => (a===owner.target?-1:0)-(b===owner.target?-1:0) ||
      (a.x-owner.x)**2+(a.y-owner.y)**2-(b.x-owner.x)**2-(b.y-owner.y)**2);
  }
  function canCast(owner,m) { return valid(owner) && supports(m?.digiMode) && !['tenten-mastery','tenten-bounce','tenten-guard'].includes(m.digiMode) && targets(owner,m).length>0; }
  function guardFor(owner) {
    if(!valid(owner))return null;
    const m=owner.moves?.find(m=>m.id==='naruto-tenten-guard');if(!m)return null;
    const s=states.get(owner);if(!s||s.world!==G.World)return null;
    const g=s.guard, v=g?.visual, age=v?s.clock-v.started:Infinity;
    const boostRemaining=Math.max(0,(g?.boostUntil||0)-s.clock),cooldownRemaining=g?.cooldown||0;
    return {owner,m,age,duration:.47,tools:8,
      phase:age<.12?'prepare':age<.47?'sweep':boostRemaining>0?'escape':cooldownRemaining>0?'cooldown':'ready',
      ready:cooldownRemaining<=0,boostRemaining,cooldownRemaining,
      radius:v?.radius??m.guardRadius,knock:v?.knock??m.guardKnock,speedBonus:g?.boostBonus??m.guardSpeedBonus,
      x:age<.12?owner.x:v?.x??owner.x,y:age<.12?owner.y:v?.y??owner.y,aim:v?.aim??owner.aim??0,
      activations:g?.activations||0,pushed:g?.pushed||0,intercepted:g?.intercepted||0};
  }
  function speedMultiplier(owner) {
    const s=states.get(owner),g=s?.guard;
    return valid(owner)&&s?.world===G.World&&owner.moves?.some(m=>m.id==='naruto-tenten-guard')&&g?.boostUntil>s.clock ? 1+g.boostBonus : 1;
  }
  function sweepGuard(s,g) {
    const owner=s.owner,v=g.visual;v.swept=true;v.x=owner.x;v.y=owner.y;
    v.rays=[];
    for(let i=0;i<48;i++) {
      const angle=i*TAU/48,dx=Math.cos(angle),dy=Math.sin(angle);let reach=0;
      for(let r=0;r<=v.radius;r+=4) {
        if(G.World.projectileBlock(v.x+dx*r,v.y+dy*r,1))break;reach=r;
      }
      v.rays.push({dx,dy,reach});
    }
    g.boostBonus=v.speedBonus;g.boostUntil=s.clock+1.5;g.pushed=0;g.intercepted=0;
    for(const enemy of new Set(G.EnemyMgr.queryCircle(v.x,v.y,v.radius))) {
      if(!alive(enemy)||enemy.boss||enemy.elite||enemy.legend||enemy.judge||enemy.remote||
        Math.hypot(enemy.x-v.x,enemy.y-v.y)>v.radius||!clearPath(v.x,v.y,enemy.x,enemy.y))continue;
      const angle=Math.atan2(enemy.y-v.y,enemy.x-v.x),dx=Math.cos(angle),dy=Math.sin(angle);
      const sx=enemy.x,sy=enemy.y,steps=Math.ceil(v.knock/4);
      for(let i=1;i<=steps;i++) {
        const distance=Math.min(v.knock,i*4),x=sx+dx*distance,y=sy+dy*distance;
        if(!G.World.isFree(x,y,enemy.r||10,true))break;
        enemy.x=x;enemy.y=y;
      }
      if(enemy.x!==sx||enemy.y!==sy)g.pushed++;
    }
    if(g.pushed)G.EnemyMgr.rebuildGrid();
    for(const shot of [...G.Projectiles.all()]) {
      if(shot.friendly!==false||shot.interceptable!==true||shot.orb||shot.special||shot.unblockable||shot.beam||shot.groundField||shot.bossSpecial||
        Math.hypot(shot.x-v.x,shot.y-v.y)>v.radius||!clearPath(v.x,v.y,shot.x,shot.y))continue;
      G.Projectiles.remove(shot);g.intercepted++;
      impact({owner},shot.x,shot.y,'metal');
    }
    if(owner===G.Game.player)G.Audio?.sfx('shot',{kind:'buff',type:'steel'});
  }
  function updateGuard(s,dt) {
    const owner=s.owner,m=owner.moves?.find(m=>m.id==='naruto-tenten-guard');
    if(!m){delete s.guard;delete s.talisman;return;}
    ensureTalisman(owner);
    if(owner.frozen){
      const g=s.guard;
      if(g){if(g.visual)g.visual.started+=dt;if(g.boostUntil>0)g.boostUntil+=dt;}
      return;
    }
    const g=s.guard??(s.guard={cooldown:0,detectIn:0,boostUntil:0,boostBonus:0,visual:null,activations:0});
    g.cooldown=Math.max(0,g.cooldown-dt);
    if(g.visual&&!g.visual.swept&&s.clock-g.visual.started+1e-8>=.12)sweepGuard(s,g);
    if(g.cooldown>0)return;
    g.detectIn-=dt;if(g.detectIn>0)return;g.detectIn=.1;
    const threat=G.EnemyMgr.queryCircle(owner.x,owner.y,80).find(e=>alive(e)&&
      Math.hypot(e.x-owner.x,e.y-owner.y)<=80&&clearPath(owner.x,owner.y,e.x,e.y));
    if(!threat)return;
    g.cooldown=Math.max(3,m.cd*(owner.cdMul??1));g.activations++;
    g.visual={started:s.clock,x:owner.x,y:owner.y,aim:Math.atan2(threat.y-owner.y,threat.x-owner.x),
      radius:m.guardRadius,knock:m.guardKnock,speedBonus:m.guardSpeedBonus,swept:false};
  }
  function talismanFor(owner) {
    const s=states.get(owner),g=s?.talisman;
    if(!valid(owner)||s?.world!==G.World||!g||!owner.moves.some(m=>m.id==='naruto-tenten-guard'))return null;
    return {...g,ready:g.cooldown<=1e-8,cooldownRemaining:g.cooldown};
  }
  function talismanHome(owner,aim=0) {
    for(const radius of [32,20,0])for(let i=0;i<8;i++) {
      const angle=aim+i*TAU/8,x=owner.x+Math.cos(angle)*radius,y=owner.y+Math.sin(angle)*radius;
      if(!G.World.projectileBlock(x,y,10)&&clearPath(owner.x,owner.y,x,y,10))return {x,y};
    }
    return {x:owner.x,y:owner.y};
  }
  function ensureTalisman(owner) {
    if(!valid(owner)||!owner.moves?.some(m=>m.id==='naruto-tenten-guard'))return null;
    let s=states.get(owner);
    if(s&&s.world!==G.World){clear(owner);s=null;}
    s??=state(owner);
    return s.talisman??(s.talisman={...talismanHome(owner),aim:0,cooldown:0,flash:0,intercepted:0,target:null});
  }
  function guardBlockable(p) {
    return p.friendly===false&&!p.unblockable&&!p.guardUnblockable&&!p.uninterceptable&&
      !p.hazard&&!p.laser&&!p.beam&&!p.ground&&!p.groundField&&!p.orb&&
      [p.x,p.y,p.vx,p.vy].every(Number.isFinite);
  }
  function contactTime(dx,dy,vx,vy,r) {
    const c=dx*dx+dy*dy-r*r;if(c<=0)return 0;
    const a=vx*vx+vy*vy,b=2*(dx*vx+dy*vy),d=b*b-4*a*c;
    return a>1e-12&&b<0&&d>=0 ? (-b-Math.sqrt(d))/(2*a) : Infinity;
  }
  function interceptGuard(owner,dt) {
    if(!valid(owner)||owner.frozen||!(dt>0)||!Number.isFinite(dt))return;
    const g=ensureTalisman(owner);if(!g)return;
    const s=state(owner),m=owner.moves.find(m=>m.id==='naruto-tenten-guard');
    // Recall only the prop, without sweeping across walls or restoring a charge.
    if(!Number.isFinite(g.x)||!Number.isFinite(g.y)||G.World.projectileBlock(g.x,g.y,10)||
      Math.hypot(g.x-owner.x,g.y-owner.y)>228+(stage(m)-1)*20||!clearPath(owner.x,owner.y,g.x,g.y,10)) {
      Object.assign(g,talismanHome(owner,s.clock*.7));g.target=null;
    }
    const shots=G.Projectiles.all().filter(guardBlockable).map(p=>({p,
      x:Number.isFinite(p.px)?p.px:p.x-p.vx*dt,y:Number.isFinite(p.py)?p.py:p.y-p.vy*dt,
      vx:Number.isFinite(p.px)?(p.x-p.px)/dt:p.vx,vy:Number.isFinite(p.py)?(p.y-p.py)/dt:p.vy}));
    const steps=Math.min(240,Math.max(1,Math.ceil(dt/.01))),h=dt/steps;
    for(let i=0;i<steps;i++) {
      g.cooldown=Math.max(0,g.cooldown-h);g.flash=Math.max(0,g.flash-h);g.target=null;
      const threats=g.cooldown>1e-8?[]:shots.map(q=>{
        const x=q.x+q.vx*i*h,y=q.y+q.vy*i*h;
        return {...q,x,y,time:contactTime(x-owner.x,y-owner.y,q.vx,q.vy,(owner.r||10)+(q.p.r||0)+16)};
      }).filter(q=>Math.hypot(q.x-owner.x,q.y-owner.y)<=180+(stage(m)-1)*20&&Number.isFinite(q.time)&&
        clearPath(owner.x,owner.y,q.x,q.y)&&clearPath(g.x,g.y,q.x,q.y));
      threats.sort((a,b)=>a.time-b.time);
      const target=threats[0];g.target=target?.p||null;
      const aim=target?Math.atan2(target.y-owner.y,target.x-owner.x):s.clock*.7;
      const tx=target?target.x:owner.x+Math.cos(aim)*32,ty=target?target.y:owner.y+Math.sin(aim)*32;
      const distance=Math.hypot(tx-g.x,ty-g.y),travel=Math.min(distance,(owner.spd+240)*h);
      const vx=distance>1e-8?(tx-g.x)/distance*travel/h:0,vy=distance>1e-8?(ty-g.y)/distance*travel/h:0;
      const nx=g.x+vx*h,ny=g.y+vy*h;
      const free=clearPath(g.x,g.y,nx,ny,10),mx=free?vx:0,my=free?vy:0;
      let first=null;
      for(const q of threats) {
        const time=contactTime(q.x-g.x,q.y-g.y,q.vx-mx,q.vy-my,10+(q.p.r||0));
        const ownerHit=contactTime(q.x-owner.x,q.y-owner.y,q.vx,q.vy,(owner.r||10)+(q.p.r||0));
        if(time<=h&&time<ownerHit&&(!first||time<first.time))first={q,time};
      }
      if(first) {
        g.x+=mx*first.time;g.y+=my*first.time;g.cooldown=3;g.flash=.22;g.intercepted++;g.target=null;
        G.Projectiles.remove(first.q.p);shots.splice(shots.findIndex(q=>q.p===first.q.p),1);
        impact({owner,world:G.World},g.x,g.y,'metal');
        if(owner===G.Game.player)G.Audio?.sfx('shot',{kind:'buff',type:'steel'});
      } else {g.x+=mx*h;g.y+=my*h;}
      g.aim=aim;
    }
  }
  const selected = (owner,id) => owner.activeGroup?.().some(m=>m.id===id);
  function origin(owner,aim,side=0,pose=null) {
    const authored=G.AnimationLab?.handForTenten?.(owner,side,pose);
    if(authored&&Number.isFinite(authored.x)&&Number.isFinite(authored.y)) {
      // A drawn hand cannot launch a tool through nearby cover.
      const length=Math.hypot(authored.x-owner.x,authored.y-owner.y),steps=Math.max(1,Math.ceil(length/4));
      let result={x:owner.x,y:owner.y};
      for(let i=1;i<=steps;i++) {
        const x=owner.x+(authored.x-owner.x)*i/steps,y=owner.y+(authored.y-owner.y)*i/steps;
        if(G.World.projectileBlock(x,y,1))break;result={x,y};
      }
      return result;
    }
    return {x:owner.x+Math.cos(aim)*8-Math.sin(aim)*side*14,
      y:owner.y+Math.sin(aim)*8+Math.cos(aim)*side*14};
  }
  function hit(w,e) {
    if (!alive(e) || !valid(w.owner)) return;
    const m=w.m, mult=G.Types.mult(m.type,e.types), crit=Math.random()<(w.owner.critChance||0);
    const damage=w.damage*mult*G.Weather.mult(m.type)*(crit?1.5:1)*(G.NarutoSupport?.precisionMultiplier(w.owner,e)||1);
    e.hurt(damage,'#dce3df',w.dx,w.dy,m.knock||0,crit?'crit':G.Types.label(mult),w.owner,m.id);
    if(w.mode!=='tenten-tags')impact(w,e.x-w.dx*(e.r||0)*.6,e.y-w.dy*(e.r||0)*.6,'metal');
    if(w.mode==='tenten-fuma')w.volley.hit=true;
    w.owner.onDealt(damage); w.owner.dmgDealt+=damage;
    G.DamageSplash?.hit(w.owner,e,damage,'#dce3df',m.id);
    if(m.burn)e.applyBurn(m.burn); if(m.poison)e.applyPoison(m.poison); if(m.slow)e.applySlow(m.slow);
  }
  function twinScroll(owner,pose,side,age=pose.age) {
    const anchor=pose.hands?.[side]||{x:side*22,y:-28},rise=Math.min(1,Math.max(0,age)/.22);
    const mirror=Math.cos(pose.aim)<0?-1:1,outward=Math.sign(anchor.x)||side;
    const scale=owner.anim?.scale||1,height=150*scale*Math.min(1,Math.max(0,age)/.78),turn=age*TAU*1.8*mirror;
    const points=[];
    for(let i=0;i<=32;i++) {
      const t=i/32,angle=(outward<0?Math.PI:0)+turn*t;
      const radius=(20+38*t)*rise*scale,centerX=owner.x+anchor.x*(1-rise*t);
      const x=centerX+Math.cos(angle)*radius*t,y=owner.y+anchor.y-height*t;
      const behindHead=Math.abs(x-owner.x)<23*scale&&y>owner.y-84*scale&&y<owner.y-30*scale;
      points.push({x,y,front:Math.sin(angle)*mirror>=0&&!behindHead});
    }
    const head=points[points.length-1],prev=points[points.length-2];
    return {points,head:{...head,angle:Math.atan2(head.y-prev.y,head.x-prev.x)+Math.PI/2},height};
  }
  function addWeapon(b,i) {
    const m=b.m, n=b.count, mode=m.digiMode, owner=b.owner, master=mastery(owner);
    const assigned=b.targets[i%b.targets.length], target=alive(assigned)?assigned:targets(owner,m)[0], side=i%2?-1:1;
    let aim=b.aim;
    if(mode==='tenten-twin') {
      const first=Math.ceil(b.batch*n/b.schedule.length),end=Math.ceil((b.batch+1)*n/b.schedule.length);
      const local=i-first,total=end-first;
      aim+=(local===0?0:((local-1)/Math.max(1,total-2)-.5))*(m.arc||110*Math.PI/180);
    }
    else if(target) aim=Math.atan2(target.y-owner.y,target.x-owner.x)+(Math.floor(i/b.targets.length)%3-1)*.025;
    const originSide=mode==='tenten-twin'?side:0;
    const originKey=G.AnimationLab?.handForTenten?originSide:`${originSide}:${aim.toFixed(3)}`;
    const o=b.origins?.get(originKey)||(mode==='tenten-twin'?twinScroll(owner,b,side).head:origin(owner,aim,originSide)), range=rangeFor(owner,m);
    b.origins?.set(originKey,o);
    if(mode!=='tenten-twin'&&target)aim=Math.atan2(target.y-o.y,target.x-o.x);
    if(mode==='tenten-twin') {
      const distance=Math.max(50,target?Math.hypot(target.x-owner.x,target.y-owner.y):range);
      aim=Math.atan2(owner.y+Math.sin(aim)*distance-o.y,owner.x+Math.cos(aim)*distance-o.x);
    }
    const speed=(m.speed|| (mode==='tenten-fuma'?480:560))*master.speed;
    const appearance=mode==='tenten-twin'?twinTools[i%twinTools.length]:null;
    const w={owner,world:G.World,m,x:o.x,y:o.y,sx:o.x,sy:o.y,age:0,angle:aim,dx:Math.cos(aim),dy:Math.sin(aim),
      speed,range,travel:0,damage:m.dmg*owner.atk*b.power,r:(m.size|| (mode==='tenten-fuma'?7:3))*(appearance?.scale||1),mode,volley:b,appearance,
      hits:new Set(),phits:new Set(),pierce:Math.max(0,m.pierce||0)+(mode==='tenten-kunai'?master.pierce:0),side,
      bounceRange:160+rangeBonus(owner,m),
      seed:i,back:false,spent:false,bounces:b.bounces,bounced:0,visited:new Set(),chainTarget:null,chaining:false,
      trail:i<24?[]:null};
    if(mode==='tenten-twin'&&!clearPath(owner.x,owner.y,o.x,o.y,w.r))w.dead=true;
    if(mode==='tenten-fuma') {
      const distance=Math.min(range,target?Math.hypot(target.x-o.x,target.y-o.y):range);
      w.tx=o.x+w.dx*distance; w.ty=o.y+w.dy*distance;
      w.duration=Math.max(.12,distance/speed); w.bend=side*(m.fumaCurve||46);
      w.returnHits=new Set();
    } else if(mode==='tenten-tags') {
      const distance=Math.min(range,target?Math.hypot(target.x-o.x,target.y-o.y):range);
      w.range=distance; w.fuse=m.fuse??m.fieldDuration??.65; w.landed=false; w.landedAge=0;
    }
    weapons.push(w);
    b.emitted++;
    const s=state(owner); s.lastCount=n; s.lastEmission=s.clock;s.totalEmitted++;s.emittedByMode[mode]=(s.emittedByMode[mode]||0)+1;
    if(s.pose===b)s.pose.emitted=b.emitted;
  }
  function cast(owner,move) {
    if(!canCast(owner,move)) return false;
    const m=G.Quantity?.snapshot(owner,move)||{...move};
    m.tentenRangeBonusAtCast=rangeBonus(owner,move);
    const list=targets(owner,m), s=state(owner);
    const count=Math.max(1,Math.floor(m.count||1)), mode=m.digiMode;
    const b={owner,world:G.World,m,mode,kind:mode,age:0,duration:mode==='tenten-twin'?1.05:.3,
      aim:Math.atan2(list[0].y-owner.y,list[0].x-owner.x),targets:list,count,emitted:0,phase:'release',started:s.clock};
    b.power=mode!=='tenten-kunai'&&s.chargeUntil>s.clock ? 1.3 : 1;
    b.bounces=bounceCount(owner);
    if(b.power>1){s.chargeUntil=0;s.release={started:s.clock,aim:b.aim,mode,id:m.id};if(owner===G.Game.player)G.Audio?.sfx('shot',{kind:'buff',type:'steel'});}
    if(mode!=='tenten-kunai'||!s.pose||s.pose.mode==='tenten-kunai')s.pose=b; s.lastCount=count;s.counts[mode]=count;s.castCounts[mode]=(s.castCounts[mode]||0)+1;
    // Four simultaneous sub-batches span .6 seconds even with thousands of tools.
    b.schedule=mode==='tenten-twin' ? [.12,.32,.52,.72] : mode==='tenten-kunai' ? [0,.055,.11] : [0];
    if(mode==='tenten-twin') {
      b.hands={};for(const side of [-1,1]){const hand=origin(owner,b.aim,side);b.hands[side]={x:hand.x-owner.x,y:hand.y-owner.y};}
    }
    b.batch=0; s.batches.push(b);
    emitDue(b); return true;
  }
  function emitDue(b) {
    while(b.batch<b.schedule.length && b.age+1e-8>=b.schedule[b.batch]) {
      const end=Math.ceil((b.batch+1)*b.count/b.schedule.length);b.origins=new Map();
      while(b.emitted<end)addWeapon(b,b.emitted);
      b.batch++;
    }
  }
  function segmentDistance(ax,ay,bx,by,e) {
    const dx=bx-ax,dy=by-ay, t=Math.max(0,Math.min(1,((e.x-ax)*dx+(e.y-ay)*dy)/(dx*dx+dy*dy||1)));
    return {t,d:(ax+dx*t-e.x)**2+(ay+dy*t-e.y)**2};
  }
  function impact(w,x,y,kind) {
    // Only short-lived material flecks are budgeted; every weapon still hits.
    if(impacts.length>=64)impacts.shift();
    impacts.push({owner:w.owner,world:w.world,x,y,age:0,life:kind==='metal'?.18:.22,kind});
  }
  function land(w) { w.landed=true; w.landedAge=0; w.dx=w.dy=0;w.chaining=false;w.chainTarget=null;impact(w,w.x,w.y,'paper'); }
  function redirect(w,spend=true) {
    if(spend&&w.bounces<=0)return false;
    const range=spend?w.bounceRange:Math.max(0,w.range-w.travel);
    const list=[...new Set(G.EnemyMgr.queryCircle(w.x,w.y,range))].filter(e=>alive(e)&&
      ((w.mode==='tenten-twin'&&e.boss)||(!e.boss&&!e.elite&&!e.legend&&!e.judge))&&
      Math.hypot(e.x-w.x,e.y-w.y)<=range);
    // Reach new enemies first; remaining hops may revisit a surviving target.
    list.sort((a,b)=>Number(w.visited.has(a))-Number(w.visited.has(b)) ||
      (a.x-w.x)**2+(a.y-w.y)**2-(b.x-w.x)**2-(b.y-w.y)**2);
    // Only test farther candidates when the nearer ones are actually blocked.
    const target=list.find(e=>clearPath(w.x,w.y,e.x,e.y,w.r));
    if(!target)return false;
    if(spend){w.bounces--;w.bounced++;w.travel=0;w.range=w.bounceRange;w.bounceAt={x:w.x,y:w.y};w.bounceFlash=.16;}
    // Only reopen the selected victim, once per paid hop, with a repeat interval.
    w.repeatDelay=w.visited.has(target) ? .08 : 0;
    w.hits.delete(target.id??target);
    w.chainTarget=target;w.chaining=true;w.spent=false;
    w.angle=Math.atan2(w.chainTarget.y-w.y,w.chainTarget.x-w.x);w.dx=Math.cos(w.angle);w.dy=Math.sin(w.angle);
    return true;
  }
  function finishChain(w) {
    w.chaining=false;w.chainTarget=null;
    if(w.mode==='tenten-tags'){land(w);return;}
    if(w.mode!=='tenten-fuma'){w.dead=true;return;}
    w.back=true;w.returnAge=0;w.rx=w.x;w.ry=w.y;w.hits=w.returnHits;w.spent=false;
    w.duration=Math.max(.12,Math.hypot(w.owner.x-w.x,w.owner.y-w.y)/w.speed);
    w.pierce=Math.max(0,w.m.pierce||0);
  }
  function triggerTags(w,ax,ay,bx,by) {
    if(w.mode==='tenten-tags'||!tagGrid.size)return;
    const r=w.r+8;
    for(let x=Math.floor((Math.min(ax,bx)-r)/CELL);x<=Math.floor((Math.max(ax,bx)+r)/CELL);x++)
      for(let y=Math.floor((Math.min(ay,by)-r)/CELL);y<=Math.floor((Math.max(ay,by)+r)/CELL);y++)
        for(const tag of tagGrid.get(x+','+y)||[]) {
          if(tag.dead||tag.triggered||tag.owner!==w.owner||tag.world!==w.world||tag.landedAge<.08)continue;
          if(segmentDistance(ax,ay,bx,by,tag).d<=r*r&&clearPath(tag.x,tag.y,bx,by)) {
            tag.damage*=1.25;tag.triggered=true;tag.ignitionAge=0;
            tag.ignitionDelay=Math.min(.12,Math.max(0,tag.fuse-tag.landedAge));
          }
        }
  }
  function sweep(w,x,y) {
    const sx=w.x,sy=w.y, distance=Math.hypot(x-sx,y-sy);
    if(w.trail&&(!w.trail.length||Math.hypot(sx-w.trail[w.trail.length-1].x,sy-w.trail[w.trail.length-1].y)>4)) {
      w.trail.push({x:sx,y:sy});if(w.trail.length>8)w.trail.shift();
    }
    // Sample cheap world occupancy, then query the spatial enemy grid once per segment.
    const steps=Math.max(1,Math.ceil(distance/6));let block=null;
    for(let j=1;j<=steps;j++) {
      const nx=sx+(x-sx)*j/steps,ny=sy+(y-sy)*j/steps;
      block=G.World.projectileBlock(nx,ny,w.r);
      if(block) { x=sx+(x-sx)*(j-1)/steps;y=sy+(y-sy)*(j-1)/steps;break; }
    }
    const half=Math.hypot(x-sx,y-sy)/2;
    const candidates=[...new Set(G.EnemyMgr.queryCircle((x+sx)/2,(y+sy)/2,half+w.r))]
      .filter(alive).map(e=>({e,...segmentDistance(sx,sy,x,y,e)}))
      .filter(p=>p.d<=(w.r+(p.e.r||0))**2).sort((a,b)=>a.t-b.t);
    for(const {e,t} of candidates) {
      const key=e.id??e;
      if(w.hits.has(key)||w.spent||!clearPath(sx,sy,e.x,e.y))continue;
      if(w.mode==='tenten-tags') {
        w.hits.add(key);w.visited.add(e);w.x=sx+(x-sx)*t;w.y=sy+(y-sy)*t;
        if(!redirect(w))land(w);return;
      }
      w.hits.add(key);hit(w,e);
      w.visited.add(e);
      if(w.bounces>0||w.chaining) {
        w.x=sx+(x-sx)*t;w.y=sy+(y-sy)*t;triggerTags(w,sx,sy,w.x,w.y);
        if(redirect(w))return;
        if(w.chaining){finishChain(w);return;}
      }
      if(w.pierce>0)w.pierce--;
      else if(w.mode==='tenten-fuma')w.spent=true;
      else {w.x=sx+(x-sx)*t;w.y=sy+(y-sy)*t;triggerTags(w,sx,sy,w.x,w.y);w.dead=true;return;}
    }
    if(w.mode!=='tenten-tags')for(const p of G.World.propsInCircle((x+sx)/2,(y+sy)/2,half+w.r)) {
      if(!p.solid&&!w.phits.has(p)&&segmentDistance(sx,sy,x,y,p).d<=(w.r+p.r)**2) {w.phits.add(p);G.World.damageProp(p,w.damage,'#dce3df');}
    }
    triggerTags(w,sx,sy,x,y);
    w.travel+=Math.hypot(x-sx,y-sy);w.x=x;w.y=y;
    if(block) {
      if(block.destructible&&!w.phits.has(block)&&w.mode!=='tenten-tags') {w.phits.add(block);G.World.damageProp(block,w.damage,'#dce3df');}
      if(w.mode==='tenten-tags')land(w);else w.dead=true;
    }
  }
  function explode(w,combo=false) {
    const radius=w.m.blastRadius||w.m.radius||60;
    for(const e of new Set(G.EnemyMgr.queryCircle(w.x,w.y,radius))) if(alive(e) &&
      Math.hypot(e.x-w.x,e.y-w.y)<=radius+(e.r||0) && clearPath(w.x,w.y,e.x,e.y)) hit(w,e);
    for(const p of G.World.propsInCircle(w.x,w.y,radius))if(clearPath(w.x,w.y,p.x,p.y,1,p))G.World.damageProp(p,w.damage,'#edaa60');
    if(combo)state(w.owner).comboBlasts++;
    if(w.owner===G.Game.player)G.Audio?.sfx('break');
    blasts.push({owner:w.owner,world:w.world,x:w.x,y:w.y,radius,age:0,life:combo?.6:.46,combo});
    w.dead=true;
  }
  function advance(w,dt) {
    w.bounceFlash=Math.max(0,(w.bounceFlash||0)-dt);
    if(w.mode==='tenten-tags' && w.landed) {
      w.landedAge+=dt;
      if(w.triggered){w.ignitionAge+=dt;if(w.ignitionAge+1e-8>=w.ignitionDelay)explode(w,true);}
      else if(w.landedAge+1e-8>=w.fuse)explode(w);
      return;
    }
    if(w.chaining) {
      if(!alive(w.chainTarget)&&!redirect(w,false)){finishChain(w);return;}
      if(w.repeatDelay>0){const wait=Math.min(dt,w.repeatDelay);w.repeatDelay-=wait;w.age+=wait;dt-=wait;if(dt<=1e-8)return;}
      w.angle=Math.atan2(w.chainTarget.y-w.y,w.chainTarget.x-w.x);w.dx=Math.cos(w.angle);w.dy=Math.sin(w.angle);
      const distance=Math.min(w.range-w.travel,w.speed*dt);
      sweep(w,w.x+w.dx*distance,w.y+w.dy*distance);w.age+=dt;
      if(!w.dead&&!w.landed&&w.chaining&&w.travel+1e-6>=w.range)finishChain(w);
      return;
    }
    if(w.mode==='tenten-fuma') {
      const steps=Math.max(1,Math.ceil(dt*120)), step=dt/steps;
      for(let i=0;i<steps&&!w.dead;i++) {
        w.age+=step;
        if(!w.back) {
          const t=Math.min(1,w.age/w.duration), bend=Math.sin(t*Math.PI)*w.bend;
          sweep(w,w.sx+(w.tx-w.sx)*t-w.dy*bend,w.sy+(w.ty-w.sy)*t+w.dx*bend);
          if(w.chaining)break;
          if(t>=1&&!w.dead) {w.back=true;w.returnAge=0;w.rx=w.x;w.ry=w.y;w.hits=w.returnHits;w.spent=false;w.pierce=Math.max(0,w.m.pierce||0);}
        } else {
          w.returnAge+=step;
          const t=Math.min(1,w.returnAge/w.duration), bend=Math.sin(t*Math.PI)*w.bend;
          // Finish at the authored catch hand, including mirroring and growth.
          const s=state(w.owner),catchPose=!s.pose||s.pose===w.volley||s.pose.mode==='tenten-kunai'||s.pose.phase==='catch';
          const hand=origin(w.owner,w.angle,0,catchPose?{key:'tenten-fuma',frame:2,mirror:Math.cos(w.angle)<0}:null);
          sweep(w,w.rx+(hand.x-w.rx)*t+w.dy*bend,w.ry+(hand.y-w.ry)*t-w.dx*bend);
          if(w.chaining)break;
          if(t>=1&&!w.dead) {
            w.dead=true;
            if(!w.volley.recovered&&w.volley.hit&&!G.World.projectileBlock(w.owner.x,w.owner.y,w.r)) {
              w.volley.recovered=true;s.chargeUntil=s.clock+6;s.recoveredAt=s.clock;
              if(w.owner===G.Game.player)G.Audio?.sfx('confirm');
            }
            if(catchPose)s.pose={kind:'tenten-fuma',mode:'tenten-fuma',m:w.m,phase:'catch',
              age:0,duration:.2,aim:w.angle,count:1,emitted:1,started:s.clock};
          }
        }
      }
    } else {
      const distance=Math.min(w.range-w.travel,w.speed*dt);
      sweep(w,w.x+w.dx*distance,w.y+w.dy*distance);
      w.age+=dt;
      if(!w.dead&&!w.landed&&w.travel+1e-6>=w.range) {if(w.mode==='tenten-tags')land(w);else w.dead=true;}
    }
  }
  function clear(owner) {
    tagGrid.clear();
    if(owner)states.delete(owner);else states.clear();
    for(const list of [weapons,blasts,impacts])for(let i=list.length-1;i>=0;i--)if(!owner||list[i].owner===owner)list.splice(i,1);
  }
  function update(dt) {
    if(G.Game.state!=='playing'||!(dt>0))return;
    for(const actor of [G.Game.player,...(G.SelfClones?.actors()||[])])
      if(valid(actor)&&actor.moves?.some(m=>m.id==='naruto-tenten-guard'))state(actor);
    tagGrid.clear();
    for(const w of weapons)if(w.mode==='tenten-tags'&&w.landed&&!w.dead&&valid(w.owner)&&w.world===G.World) {
      const key=Math.floor(w.x/CELL)+','+Math.floor(w.y/CELL);
      if(!tagGrid.has(key))tagGrid.set(key,[]);tagGrid.get(key).push(w);
    }
    for(const [owner,s] of states) {
      if(!valid(owner)||s.world!==G.World){clear(owner);continue;}
      s.clock+=dt;
      updateGuard(s,dt);
      if(s.release&&(s.clock-s.release.started>.7||!selected(owner,s.release.id)))s.release=null;
      if(s.pose) { s.pose.age=s.clock-s.pose.started; if(s.pose.age>=s.pose.duration)s.pose=null; }
      if(s.pose&&s.pose.mode!=='tenten-kunai'&&s.pose.phase!=='catch'&&!selected(owner,s.pose.m.id))s.pose=null;
      for(let i=s.batches.length-1;i>=0;i--) {
        const b=s.batches[i];
        if(b.mode!=='tenten-kunai'&&!selected(owner,b.m.id)){s.batches.splice(i,1);continue;}
        b.age=s.clock-b.started;
        emitDue(b); if(b.batch>=b.schedule.length)s.batches.splice(i,1);
      }
    }
    for(let i=weapons.length-1;i>=0;i--) {
      const w=weapons[i];if(!valid(w.owner)||w.world!==G.World)w.dead=true;else if(!w.dead)advance(w,dt);
      if(w.dead)weapons.splice(i,1);
    }
    for(let i=blasts.length-1;i>=0;i--) {const b=blasts[i];b.age+=dt;if(!valid(b.owner)||b.world!==G.World||b.age>=b.life)blasts.splice(i,1);}
    for(let i=impacts.length-1;i>=0;i--) {const p=impacts[i];p.age+=dt;if(!valid(p.owner)||p.world!==G.World||p.age>=p.life)impacts.splice(i,1);}
  }
  // Small cached material silhouettes; no particles or decorative cap can discard damage.
  const sprites=new Map();
  function sprite(kind,palette='silver') {
    const key=kind+':'+palette;if(sprites.has(key))return sprites.get(key);
    const c=document.createElement('canvas');c.width=c.height=40;c.dataset.source='tenten-tool-'+kind+':'+palette;const ctx=c.getContext('2d');ctx.translate(20,20);
    const metal=({silver:'#d6e4e3',blue:'#8fbddd',bronze:'#dcbd77',dark:'#84929d'})[palette]||'#d6e4e3';
    ctx.strokeStyle='#273442';ctx.fillStyle=metal;ctx.lineWidth=2;
    if(kind==='fuma') {
      for(let i=0;i<4;i++){ctx.rotate(Math.PI/2);ctx.beginPath();ctx.moveTo(-3,2);ctx.lineTo(0,-17);ctx.lineTo(7,-7);ctx.lineTo(3,4);ctx.closePath();ctx.fill();ctx.stroke();}
      ctx.fillStyle='#273442';ctx.fillRect(-2,-2,4,4);
    } else if(kind==='shuriken') {
      ctx.beginPath();for(let i=0;i<8;i++){const a=i*Math.PI/4,r=i%2?3:10;ctx.lineTo(Math.cos(a)*r,Math.sin(a)*r);}ctx.closePath();ctx.fill();ctx.stroke();
    } else if(kind==='senbon') {
      ctx.fillStyle='#71858e';ctx.fillRect(-15,-2,28,4);ctx.fillStyle=metal;ctx.fillRect(-12,-1,27,2);
      ctx.fillStyle='#c17189';ctx.fillRect(-16,-3,5,6);
    } else if(kind==='sickle') {
      ctx.fillStyle='#65484b';ctx.fillRect(-12,-2,23,4);ctx.strokeRect(-12,-2,23,4);
      ctx.beginPath();ctx.moveTo(6,-3);ctx.lineTo(2,-14);ctx.lineTo(13,-11);ctx.lineTo(18,-2);ctx.lineTo(12,10);ctx.lineTo(12,0);ctx.closePath();ctx.fillStyle=metal;ctx.fill();ctx.stroke();
    } else if(kind==='axe') {
      ctx.fillStyle='#785d52';ctx.fillRect(-16,-2,27,4);ctx.strokeRect(-16,-2,27,4);
      ctx.fillStyle=metal;ctx.beginPath();ctx.moveTo(2,-3);ctx.lineTo(-1,-14);ctx.lineTo(13,-12);ctx.lineTo(18,-5);ctx.lineTo(18,6);ctx.lineTo(8,10);ctx.lineTo(9,1);ctx.closePath();ctx.fill();ctx.stroke();
    } else if(kind==='spear'||kind==='sword') {
      ctx.fillStyle='#715263';ctx.fillRect(-17,-2,17,4);ctx.strokeRect(-17,-2,17,4);
      ctx.fillStyle=metal;ctx.beginPath();ctx.moveTo(18,0);ctx.lineTo(kind==='sword'?-5:3,-4);ctx.lineTo(kind==='sword'?-5:0,4);ctx.closePath();ctx.fill();ctx.stroke();
      ctx.fillStyle='#dabf7c';ctx.fillRect(-6,-6,3,12);
    } else if(kind==='chakram') {
      ctx.strokeStyle='#273442';ctx.lineWidth=8;ctx.beginPath();ctx.arc(0,0,11,0,TAU);ctx.stroke();ctx.strokeStyle=metal;ctx.lineWidth=4;ctx.stroke();
    } else {
      ctx.beginPath();ctx.moveTo(13,0);ctx.lineTo(-1,-4);ctx.lineTo(-5,0);ctx.lineTo(-1,4);ctx.closePath();ctx.fill();ctx.stroke();
      ctx.fillStyle='#384859';ctx.fillRect(-12,-2,8,4);ctx.strokeRect(-16,-3,5,6);
      if(kind==='tag'){ctx.fillStyle='#f3e5bc';ctx.fillRect(-10,1,7,15);ctx.strokeStyle='#a83f3d';ctx.strokeRect(-8,4,3,8);}
    }
    sprites.set(key,c);return c;
  }
  function paperScroll(ctx,x,y,open=1,angle=0) {
    ctx.save();ctx.translate(Math.round(x),Math.round(y));ctx.rotate(angle);
    const h=8+24*open;
    ctx.fillStyle='#302b30';ctx.fillRect(-13,-h/2-4,26,h+8);
    ctx.fillStyle='#efd8a4';ctx.fillRect(-10,-h/2,20,h);
    ctx.fillStyle='#bc7053';ctx.fillRect(-15,-h/2-4,30,5);ctx.fillRect(-15,h/2-1,30,5);
    ctx.fillStyle='#f4ddae';ctx.fillRect(-12,-h/2-3,24,2);ctx.fillRect(-12,h/2,24,2);
    if(open>.3){ctx.fillStyle='#8d3438';ctx.font='bold 16px serif';ctx.textAlign='center';ctx.fillText('封',0,6);}
    ctx.restore();
  }
  function paperRibbon(ctx,points,width,alpha=1) {
    ctx.save();ctx.globalAlpha*=alpha;ctx.lineJoin='bevel';ctx.lineCap='butt';
    ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(Math.round(p.x),Math.round(p.y)):ctx.moveTo(Math.round(p.x),Math.round(p.y)));
    ctx.strokeStyle='#41332e';ctx.lineWidth=width+4;ctx.stroke();
    ctx.strokeStyle='#f0dcab';ctx.lineWidth=width;ctx.stroke();
    ctx.fillStyle='#a44c46';
    for(let i=2;i<points.length;i+=3){const p=points[i];ctx.fillRect(Math.round(p.x)-2,Math.round(p.y)-2,4,4);ctx.fillRect(Math.round(p.x)+3,Math.round(p.y)+2,2,4);}
    ctx.restore();
  }
  function scrollEffects(ctx,s) {
    const owner=s.owner,now=s.clock,calm=G.Settings?.get('calm'),p=s.pose;
    if(p?.mode==='tenten-twin')drawTwin(ctx,owner,p,true);
    if(s.chargeUntil>now) {
      const x=owner.x-28,y=owner.y-G.LIFT-28;
      // Recovered Fuma uses a steel insignia, never an extra scroll.
      ctx.save();ctx.translate(x,y);ctx.drawImage(sprite('fuma'),-12,-12,24,24);
      ctx.strokeStyle='#b8e8d7';ctx.lineWidth=2;ctx.beginPath();ctx.arc(0,0,17,-Math.PI/2,-Math.PI/2+TAU*Math.min(1,(s.chargeUntil-now)/6));ctx.stroke();ctx.restore();
    }
    if(s.release) {
      const age=now-s.release.started,t=age/.7,spread=Math.sin(Math.min(1,t*2)*Math.PI/2);
      const x=owner.x,y=owner.y-G.LIFT-60;
      ctx.save();ctx.globalAlpha*=Math.max(0,1-t);
      if(s.release.mode==='tenten-twin') {
        // Emphasize only the two real rising rolls; never add a second pair.
        ctx.strokeStyle='#fff0bc';ctx.lineWidth=2;
        for(const side of [-1,1]){const coil=scrollFor(owner,side);if(!coil)continue;const h=coil.head,r=calm?17:12+t*16;
          for(let i=0;i<4;i++){const a=i*Math.PI/2;ctx.beginPath();ctx.moveTo(h.x+Math.cos(a)*r,h.y-G.LIFT+Math.sin(a)*r);ctx.lineTo(h.x+Math.cos(a)*(r+7),h.y-G.LIFT+Math.sin(a)*(r+7));ctx.stroke();}}
      } else if(s.release.mode==='tenten-fuma') {
        const hand=origin(owner,s.release.aim),r=calm?12:8+t*18;
        ctx.strokeStyle='#b9f1dd';ctx.lineWidth=2;
        for(let i=0;i<4;i++){const a=i*Math.PI/2+.4;ctx.beginPath();ctx.moveTo(hand.x+Math.cos(a)*r,hand.y-G.LIFT+Math.sin(a)*r);ctx.lineTo(hand.x+Math.cos(a)*(r+8),hand.y-G.LIFT+Math.sin(a)*(r+8));ctx.stroke();}
      } else {
        paperRibbon(ctx,[{x:x-64*spread,y:y-9},{x:x-30*spread,y:y+4},{x,y:y-5},{x:x+30*spread,y:y+4},{x:x+64*spread,y:y-9}],13);
        paperScroll(ctx,x-64*spread,y-9,.1,-.2);paperScroll(ctx,x+64*spread,y-9,.1,.2);
        ctx.strokeStyle='#fff2c5';ctx.lineWidth=2;
        for(let i=0;i<8;i++){const a=i*Math.PI/4,r=18+t*35;ctx.beginPath();ctx.moveTo(x+Math.cos(a)*r,y+Math.sin(a)*r);ctx.lineTo(x+Math.cos(a)*(r+12),y+Math.sin(a)*(r+12));ctx.stroke();}
      }
      ctx.restore();
    }
  }
  function drawTwin(ctx,owner,pose,front) {
    if(pose.age<.08)return;
    const fade=Math.max(0,Math.min(1,(pose.duration-pose.age)/.18));
    for(const side of [-1,1]) {
      const coil=twinScroll(owner,pose,side),points=coil.points.map(p=>({...p,y:p.y-G.LIFT}));
      let run=[];
      for(let i=1;i<points.length;i++) {
        const visible=points[i].front===front;
        if(visible){if(!run.length)run.push(points[i-1]);run.push(points[i]);}
        if((!visible||i===points.length-1)&&run.length){paperRibbon(ctx,run,front?(pose.power>1?10:8):6,fade*(front?.95:.5));run=[];}
      }
      if(coil.head.front===front){ctx.save();ctx.globalAlpha*=fade;paperScroll(ctx,coil.head.x,coil.head.y-G.LIFT,.03,coil.head.angle);ctx.restore();}
    }
  }
  function drawBlast(ctx,b) {
    const t=b.age/b.life,calm=G.Settings?.get('calm');
    const reach=b.radius*Math.min(1,.28+t*3.2),fade=Math.min(1,(1-t)*2);
    ctx.save();ctx.translate(b.x,b.y);ctx.globalAlpha*=fade;
    // A sharp paper-and-fire silhouette expands only inside the actual AOE.
    const burst=(radius,color,phase)=>{
      ctx.fillStyle=color;ctx.strokeStyle='#553e36';ctx.lineWidth=2;ctx.beginPath();
      for(let i=0;i<24;i++){const a=i*TAU/24+phase,r=radius*(i%2?.65:1);ctx.lineTo(Math.round(Math.cos(a)*r),Math.round(Math.sin(a)*r));}
      ctx.closePath();ctx.fill();ctx.stroke();
    };
    if(t<.7){burst(reach,b.combo?'#dc7d39':'#b87040',.08);burst(reach*.7,'#ffd274',.18);burst(reach*(t<.18?.62:.35),'#fff3c4',0);}
    ctx.fillStyle='#ead5ab';
    for(let i=0;i<10;i++){
      const a=i*2.39996,r=b.radius*Math.min(.92,.24+t*.9)*Math.sqrt((i+1)/10);
      ctx.save();ctx.translate(Math.round(Math.cos(a)*r),Math.round(Math.sin(a)*r));if(!calm)ctx.rotate(a+t*3);
      ctx.fillRect(-3,-6,6,12);ctx.fillStyle='#ad5545';ctx.fillRect(-1,-3,2,5);ctx.fillStyle='#ead5ab';ctx.restore();
    }
    ctx.restore();
  }
  function guardGround(ctx,s) {
    const g=guardFor(s.owner),v=s.guard?.visual;
    if(!g||g.age>=.47)return;
    ctx.save();
    if(g.phase==='prepare') {
      ctx.strokeStyle='#f3d99b';ctx.globalAlpha=.45;ctx.lineWidth=1.5;
      ctx.beginPath();ctx.arc(g.x,g.y,18+10*Math.min(1,g.age/.12),0,TAU);ctx.stroke();
      for(let i=0;i<8;i++){
        const a=i*TAU/8,r=24;ctx.beginPath();ctx.moveTo(g.x+Math.cos(a)*r,g.y+Math.sin(a)*r);
        ctx.lineTo(g.x+Math.cos(a)*(r+5),g.y+Math.sin(a)*(r+5));ctx.stroke();
      }
    } else if(v?.rays) {
      const t=Math.min(1,(g.age-.12)/.35),r=g.radius*Math.min(1,t*2.4),alpha=1-t;
      ctx.lineWidth=2;ctx.strokeStyle='#a9e8d3';ctx.fillStyle='#8bcdb7';ctx.globalAlpha=.07*alpha;
      ctx.beginPath();v.rays.forEach((ray,i)=>{
        const d=Math.min(r,ray.reach),x=g.x+ray.dx*d,y=g.y+ray.dy*d;
        if(i)ctx.lineTo(x,y);else ctx.moveTo(x,y);
      });ctx.closePath();ctx.fill();ctx.globalAlpha=.65*alpha;ctx.stroke();
    }
    ctx.restore();
  }
  function guardAir(ctx,s) {
    const owner=s.owner,g=guardFor(owner);if(!g)return;
    const calm=G.Settings?.get('calm');
    if(g.phase==='prepare') {
      const hand=origin(owner,g.aim);
      ctx.save();ctx.translate(hand.x,hand.y-G.LIFT+9);ctx.scale(.6,.6);
      paperScroll(ctx,0,0,.12+g.age*2,g.aim*.12);ctx.restore();
    } else if(g.phase==='sweep') {
      const t=Math.min(1,(g.age-.12)/.35),radius=g.radius*Math.min(1,t*2.4),v=s.guard.visual;
      for(let i=0;i<8;i++) {
        const angle=i*TAU/8+(calm?0:t*.32),ray=v.rays[Math.round((angle/TAU*48)%48)];
        const reach=Math.min(radius,ray?.reach??radius),x=g.x+Math.cos(angle)*reach,y=g.y+Math.sin(angle)*reach-G.LIFT;
        if(reach<12)continue;
        ctx.save();ctx.globalAlpha=Math.max(0,1-t)*.95;ctx.translate(x,y);ctx.rotate(angle);ctx.scale(.68,.68);
        ctx.drawImage(sprite(i%2?'kunai':'shuriken','silver'),-20,-20);ctx.restore();
      }
    }
    if(g.boostRemaining>0) {
      const angle=owner.walking?owner.moveAngle:g.aim,dx=Math.cos(angle),dy=Math.sin(angle);
      ctx.save();ctx.globalAlpha=Math.min(1,g.boostRemaining/.25)*.6;ctx.strokeStyle='#a7e8d2';ctx.lineWidth=2;
      for(let i=0;i<3;i++) {
        const side=(i-1)*7,offset=calm?0:Math.sin(s.clock*20+i)*3;
        const x=owner.x-dx*(12+offset)-dy*side,y=owner.y-dy*(12+offset)+dx*side-5;
        ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x-dx*(10+i*3),y-dy*(10+i*3));ctx.stroke();
      }
      ctx.restore();
    }
  }
  function talismanGround(ctx,s) {
    const g=talismanFor(s.owner);if(!g)return;
    ctx.save();ctx.globalAlpha=g.ready ? .24 : .1;ctx.fillStyle='#17232b';
    ctx.beginPath();ctx.ellipse(g.x,g.y,10,4,0,0,TAU);ctx.fill();ctx.restore();
  }
  function talismanAir(ctx,s) {
    const g=talismanFor(s.owner);if(!g)return;
    ctx.save();ctx.translate(Math.round(g.x),Math.round(g.y-G.LIFT));
    ctx.globalAlpha=g.ready?1:.38;
    ctx.fillStyle='#253c47';ctx.fillRect(-8,-12,16,24);
    ctx.fillStyle='#e7d8b2';ctx.fillRect(-6,-10,12,20);
    ctx.fillStyle='#90bdbb';ctx.fillRect(-7,-11,14,4);ctx.fillRect(-7,7,14,4);
    ctx.strokeStyle='#ad5545';ctx.lineWidth=2;ctx.beginPath();
    ctx.moveTo(-3,-5);ctx.lineTo(3,-5);ctx.lineTo(-2,0);ctx.lineTo(3,2);ctx.lineTo(-3,5);ctx.stroke();
    if(!g.ready){ctx.globalAlpha=.8;ctx.strokeStyle='#a9ded8';ctx.lineWidth=2;ctx.beginPath();
      ctx.arc(0,0,16,-Math.PI/2,-Math.PI/2+TAU*(1-g.cooldownRemaining/3));ctx.stroke();}
    if(g.flash>0){ctx.globalAlpha=g.flash/.22;ctx.strokeStyle='#fff1b8';ctx.lineWidth=2;
      for(let i=0;i<6;i++){const a=i*TAU/6;ctx.beginPath();ctx.moveTo(Math.cos(a)*12,Math.sin(a)*12);
        ctx.lineTo(Math.cos(a)*21,Math.sin(a)*21);ctx.stroke();}}
    ctx.restore();
  }
  function air(ctx) {
    ctx.save();const calm=G.Settings?.get('calm');
    for(const s of states.values())if(valid(s.owner)&&s.world===G.World){scrollEffects(ctx,s);guardAir(ctx,s);talismanAir(ctx,s);}
    for(const w of weapons) {
      if(w.dead||!valid(w.owner)||w.world!==G.World||!G.Camera.sees(w.x,w.y,60))continue;
      if(w.mode==='tenten-fuma'&&w.seed<2) {
        const hand=origin(w.owner,w.angle),sag=w.back?0:12;
        ctx.save();ctx.globalAlpha=.75;ctx.lineWidth=2;ctx.strokeStyle='#26333c';ctx.beginPath();ctx.moveTo(hand.x,hand.y-G.LIFT);
        ctx.quadraticCurveTo((hand.x+w.x)/2,(hand.y+w.y)/2-G.LIFT+sag,w.x,w.y-G.LIFT);ctx.stroke();
        ctx.lineWidth=1;ctx.strokeStyle=w.back?'#f7e4bb':'#b7d2cf';ctx.stroke();ctx.restore();
      }
      if(w.trail?.length>1&&(!calm||w.chaining)) {
        ctx.save();ctx.lineJoin='bevel';ctx.strokeStyle=w.chaining?'#83f5cb':w.appearance?({silver:'#d6eeff',blue:'#80ccff',bronze:'#ffd68d',dark:'#cda9e1'})[w.appearance.palette]:w.volley.power>1?'#f2c46d':'#b8d7d2';ctx.globalAlpha=w.chaining?.8:w.back?.65:.4;ctx.lineWidth=w.mode==='tenten-fuma'?5:2+(w.appearance?.scale||0);
        ctx.beginPath();w.trail.forEach((p,i)=>i?ctx.lineTo(p.x,p.y-G.LIFT):ctx.moveTo(p.x,p.y-G.LIFT));ctx.lineTo(w.x,w.y-G.LIFT);ctx.stroke();ctx.restore();
      }
      if(w.bounceFlash>0&&w.bounceAt) {
        ctx.save();ctx.globalAlpha=calm?.65:w.bounceFlash/.16;ctx.strokeStyle='#acffe0';ctx.lineWidth=2;
        const p=w.bounceAt,r=calm?8:6+(1-w.bounceFlash/.16)*12;
        ctx.beginPath();ctx.moveTo(p.x-r,p.y-G.LIFT);ctx.lineTo(p.x,p.y-G.LIFT-r);ctx.lineTo(p.x+r,p.y-G.LIFT);ctx.lineTo(p.x,p.y-G.LIFT+r);ctx.closePath();ctx.stroke();ctx.restore();
      }
      if(w.mode==='tenten-tags'&&w.landed) {
        ctx.save();ctx.translate(w.x,w.y);ctx.strokeStyle=w.triggered?'#ffe09b':'#dfaa68';ctx.lineWidth=w.triggered?3:1;ctx.globalAlpha=w.triggered?.95:.6;
        ctx.setLineDash(w.triggered?[]:[5,5]);ctx.beginPath();ctx.arc(0,0,w.m.blastRadius||w.m.radius||60,0,TAU);ctx.stroke();ctx.setLineDash([]);ctx.globalAlpha=1;
        ctx.fillStyle='#3a2c30';ctx.fillRect(-8,-24,16,27);ctx.fillStyle=w.triggered?'#ffe9a4':'#f3deb5';ctx.fillRect(-6,-22,12,23);
        ctx.fillStyle='#ac4340';ctx.font='bold 12px serif';ctx.textAlign='center';ctx.fillText('爆',0,-7);
        const burn=w.triggered?Math.min(1,w.ignitionAge/Math.max(.001,w.ignitionDelay)):w.landedAge/w.fuse;
        ctx.fillStyle='#f7b84f';ctx.fillRect(-8,-24+burn*24,16,3);
        if(w.triggered){ctx.strokeStyle='#fff0ae';ctx.lineWidth=2;for(let i=0;i<6;i++){const a=i*TAU/6;ctx.beginPath();ctx.moveTo(Math.cos(a)*12,-12+Math.sin(a)*12);ctx.lineTo(Math.cos(a)*(20+burn*12),-12+Math.sin(a)*(20+burn*12));ctx.stroke();}}
        ctx.restore();continue;
      }
      const kind=w.appearance?.kind||(w.mode==='tenten-fuma'?'fuma':w.mode==='tenten-tags'?'tag':'kunai');
      ctx.save();ctx.translate(w.x,w.y-(w.landed?0:G.LIFT));ctx.rotate(!calm&&['fuma','shuriken','sickle','axe','chakram'].includes(kind)?w.age*18:w.angle);
      ctx.scale(w.appearance?.scale||1,w.appearance?.scale||1);
      ctx.drawImage(sprite(kind,w.appearance?.palette),-20,-20);ctx.restore();
    }
    for(const b of blasts)if(b.world===G.World)drawBlast(ctx,b);
    for(const p of impacts)if(p.world===G.World&&valid(p.owner)) {
      const t=p.age/p.life,r=calm?6:4+t*10;
      ctx.save();ctx.globalAlpha=(1-t)*.9;ctx.fillStyle=p.kind==='metal'?'#dceee8':'#d7bc89';
      const y=p.y-(p.kind==='metal'?G.LIFT:0);
      for(let i=0;i<(calm?2:4);i++){const a=i*Math.PI/2+.4;ctx.fillRect(Math.round(p.x+Math.cos(a)*r)-1,Math.round(y+Math.sin(a)*r)-1,3,p.kind==='metal'?2:4);}
      ctx.restore();
    }
    ctx.restore();
  }
  function ground(ctx) {
    ctx.save();ctx.lineWidth=1;
    for(const s of states.values())if(valid(s.owner)&&s.world===G.World){guardGround(ctx,s);talismanGround(ctx,s);}
    for(const s of states.values())if(valid(s.owner)&&s.world===G.World&&s.pose?.mode==='tenten-twin')drawTwin(ctx,s.owner,s.pose,false);
    for(const w of weapons)if(w.mode==='tenten-tags'&&w.landed&&valid(w.owner)&&w.world===G.World){
      const radius=w.m.blastRadius||w.m.radius||60;
      ctx.strokeStyle='#e9b66d';ctx.globalAlpha=.55;ctx.setLineDash([3,5]);ctx.beginPath();ctx.arc(w.x,w.y,radius,0,TAU);ctx.stroke();
      ctx.setLineDash([]);ctx.globalAlpha=.85;ctx.beginPath();ctx.arc(w.x,w.y,10,-Math.PI/2,-Math.PI/2+TAU*Math.min(1,w.landedAge/w.fuse));ctx.stroke();
    }
    ctx.restore();
  }
  const updateProjectiles=G.Projectiles.update;
  G.Projectiles.update=function(dt,owner,enemies) {
    const result=updateProjectiles.call(this,dt,owner,enemies);
    if(G.Game.state==='playing')for(const actor of [owner,...(G.SelfClones?.actors()||[])])
      if(valid(actor)&&actor.moves.some(m=>m.id==='naruto-tenten-guard'))interceptGuard(actor,dt);
    return result;
  };
  const oldTick=C.tick,oldUpdate=C.updateFields,oldClear=C.clearFields,oldAir=C.drawAirFields,oldGround=C.drawGroundFields;
  C.tick=function(dt,owner,now) {
    if((owner?.mon?.dex??owner?.dex)===30009&&G.Game.state!=='playing')return;
    const result=oldTick.call(this,dt,owner,now);
    if(G.Game.state!=='playing'||!valid(owner)||owner.frozen||!(dt>0))return result;
    const s=state(owner),m=owner.moves.find(m=>m.id==='naruto-tenten');if(!m)return result;
    s.basicCooldown-=dt;
    if(s.basicCooldown<=0&&canCast(owner,m)) {
      owner.cast(m);cast(owner,m);m.castAt=performance.now();
      s.basicCooldown=Math.max(.05,m.cd*(owner.cdMul||1));
    }
    return result;
  };
  C.updateFields=function(dt){const result=oldUpdate.call(this,dt);update(dt);return result;};
  C.clearFields=function(owner){const result=oldClear.call(this,owner);clear(owner);return result;};
  C.drawAirFields=function(ctx){oldAir.call(this,ctx);air(ctx);};
  C.drawGroundFields=function(ctx){oldGround.call(this,ctx);ground(ctx);};
  function stateFor(owner) {
    const s=states.get(owner);if(!s||!valid(owner)||s.world!==G.World)return null;
    const own=weapons.filter(w=>w.owner===owner),p=mastery(owner);
    return {owner,pose:s.pose,count:s.lastCount,emitted:s.pose?.emitted||0,basicCooldown:s.basicCooldown,
      totalEmitted:s.totalEmitted,emittedByMode:{...s.emittedByMode},castCounts:{...s.castCounts},counts:{...s.counts},
      chargeRemaining:Math.max(0,s.chargeUntil-s.clock),comboBlasts:s.comboBlasts,
      bounceCount:bounceCount(owner),
      shots:own.length,tagCount:own.filter(w=>w.mode==='tenten-tags').length,returning:own.filter(w=>w.back).length,
      masteryPierce:p.pierce,masterySpeed:p.speed,masteryRange:p.range};
  }
  function activeFor(owner) {
    const s=states.get(owner);if(!valid(owner)||s?.world!==G.World)return null;
    if(s.pose)return s.pose;
    const m=owner.activeGroup?.().find(m=>m.digiMode==='tenten-fuma'&&m.t>0&&m.t<=.08);
    const target=owner.target;
    if(m&&alive(target)&&Math.hypot(target.x-owner.x,target.y-owner.y)<=rangeFor(owner,m))return {
      owner,kind:'tenten-fuma',mode:'tenten-fuma',m,phase:'prepare',age:.08-m.t,duration:.08,
      aim:Math.atan2(target.y-owner.y,target.x-owner.x),count:0,emitted:0};
    return null;
  }
  function scrollFor(owner,side=1) {
    const pose=activeFor(owner);return pose?.mode==='tenten-twin'?twinScroll(owner,pose,side):null;
  }
  G.NarutoTenten={supports,canCast,cast,clear,update,stage,bounceCount,stateFor,guardFor,talismanFor,ensureTalisman,speedMultiplier,
    activeFor,scrollFor,
    get weapons(){return weapons;},get blasts(){return blasts;},get impacts(){return impacts;}};
})();
