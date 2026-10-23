/* Tenten's actor-owned physical ninja tools. Visual poses never gate combat. */
(() => {
  if (G.NarutoTenten) return;
  const C = G.Combat, TAU = Math.PI * 2, states = new Map(), weapons = [], blasts = [];
  const modes = new Set(['tenten-kunai','tenten-fuma','tenten-mastery','tenten-tags','tenten-twin']);
  const alive = a => a && !a.dead && a.hp > 0;
  const controlled = a => a === G.Game.player || !!G.SelfClones?.isActor(a);
  const valid = a => alive(a) && controlled(a) && (a.mon?.dex ?? a.dex) === 30009;
  const supports = mode => modes.has(mode);
  const stage = m => m?.moves ? (m.moves.find(x=>x.id==='naruto-tenten-mastery')?.lvl||0) : Math.max(1, Math.min(5, m?.lvl || 1));
  function state(owner) {
    let s = states.get(owner);
    if (!s) { s = {owner, world:G.World, basicCooldown:0, batches:[], pose:null, lastCount:0, clock:0, totalEmitted:0, emittedByMode:{}, castCounts:{}, counts:{}}; states.set(owner,s); }
    return s;
  }
  function mastery(owner) {
    const m = owner.moves?.find(m => m.id === 'naruto-tenten-mastery');
    const i = stage(m)-1;
    return {pierce:m ? [1,1,2,2,3][i] : 0, speed:m ? [1.10,1.15,1.20,1.25,1.30][i] : 1};
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
    const r = m.range || 300;
    const list = [...new Set(G.EnemyMgr.queryCircle(owner.x,owner.y,r))].filter(e => alive(e) &&
      Math.hypot(e.x-owner.x,e.y-owner.y)<=r && clearPath(owner.x,owner.y,e.x,e.y));
    // An actor's assigned target remains first; following weapons spread through the others.
    return list.sort((a,b) => (a===owner.target?-1:0)-(b===owner.target?-1:0) ||
      (a.x-owner.x)**2+(a.y-owner.y)**2-(b.x-owner.x)**2-(b.y-owner.y)**2);
  }
  function canCast(owner,m) { return valid(owner) && supports(m?.digiMode) && m.digiMode!=='tenten-mastery' && targets(owner,m).length>0; }
  const selected = (owner,id) => owner.activeGroup?.().some(m=>m.id===id);
  function origin(owner,aim,side=0) {
    const authored=G.AnimationLab?.handForTenten?.(owner,side);
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
    w.owner.onDealt(damage); w.owner.dmgDealt+=damage;
    G.DamageSplash?.hit(w.owner,e,damage,'#dce3df',m.id);
    if(m.burn)e.applyBurn(m.burn); if(m.poison)e.applyPoison(m.poison); if(m.slow)e.applySlow(m.slow);
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
    const o=b.origins?.get(originKey)||origin(owner,mode==='tenten-twin'?b.aim:aim,originSide), range=m.range||300;
    b.origins?.set(originKey,o);
    if(mode!=='tenten-twin'&&target)aim=Math.atan2(target.y-o.y,target.x-o.x);
    if(mode==='tenten-twin') {
      const distance=Math.max(50,target?Math.hypot(target.x-owner.x,target.y-owner.y):range);
      aim=Math.atan2(owner.y+Math.sin(aim)*distance-o.y,owner.x+Math.cos(aim)*distance-o.x);
    }
    const speed=(m.speed|| (mode==='tenten-fuma'?480:560))*master.speed;
    const w={owner,world:G.World,m,x:o.x,y:o.y,sx:o.x,sy:o.y,age:0,angle:aim,dx:Math.cos(aim),dy:Math.sin(aim),
      speed,range,travel:0,damage:m.dmg*owner.atk,r:m.size|| (mode==='tenten-fuma'?7:3),mode,
      hits:new Set(),phits:new Set(),pierce:Math.max(0,m.pierce||0)+(mode==='tenten-kunai'?master.pierce:0),side,
      seed:i,back:false,spent:false};
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
    const m=G.Quantity?.snapshot(owner,move)||{...move}, list=targets(owner,m), s=state(owner);
    const count=Math.max(1,Math.floor(m.count||1)), mode=m.digiMode;
    const b={owner,world:G.World,m,mode,kind:mode,age:0,duration:mode==='tenten-twin'?.85:.3,
      aim:Math.atan2(list[0].y-owner.y,list[0].x-owner.x),targets:list,count,emitted:0,phase:'release',started:s.clock};
    if(mode!=='tenten-kunai'||!s.pose||s.pose.mode==='tenten-kunai')s.pose=b; s.lastCount=count;s.counts[mode]=count;s.castCounts[mode]=(s.castCounts[mode]||0)+1;
    // Four simultaneous sub-batches span .6 seconds even with thousands of tools.
    b.schedule=mode==='tenten-twin' ? [0,.2,.4,.6] : mode==='tenten-kunai' ? [0,.055,.11] : [0];
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
  function land(w) { w.landed=true; w.landedAge=0; w.dx=w.dy=0; }
  function sweep(w,x,y) {
    const sx=w.x,sy=w.y, distance=Math.hypot(x-sx,y-sy);
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
      if(w.mode==='tenten-tags') { w.x=sx+(x-sx)*t;w.y=sy+(y-sy)*t;land(w);return; }
      w.hits.add(key);hit(w,e);
      if(w.pierce>0)w.pierce--;
      else if(w.mode==='tenten-fuma')w.spent=true;
      else {w.x=sx+(x-sx)*t;w.y=sy+(y-sy)*t;w.dead=true;return;}
    }
    if(w.mode!=='tenten-tags')for(const p of G.World.propsInCircle((x+sx)/2,(y+sy)/2,half+w.r)) {
      if(!p.solid&&!w.phits.has(p)&&segmentDistance(sx,sy,x,y,p).d<=(w.r+p.r)**2) {w.phits.add(p);G.World.damageProp(p,w.damage,'#dce3df');}
    }
    w.travel+=Math.hypot(x-sx,y-sy);w.x=x;w.y=y;
    if(block) {
      if(block.destructible&&!w.phits.has(block)&&w.mode!=='tenten-tags') {w.phits.add(block);G.World.damageProp(block,w.damage,'#dce3df');}
      if(w.mode==='tenten-tags')land(w);else w.dead=true;
    }
  }
  function explode(w) {
    const radius=w.m.blastRadius||w.m.radius||60;
    for(const e of new Set(G.EnemyMgr.queryCircle(w.x,w.y,radius))) if(alive(e) &&
      Math.hypot(e.x-w.x,e.y-w.y)<=radius+(e.r||0) && clearPath(w.x,w.y,e.x,e.y)) hit(w,e);
    for(const p of G.World.propsInCircle(w.x,w.y,radius))if(clearPath(w.x,w.y,p.x,p.y,1,p))G.World.damageProp(p,w.damage,'#edaa60');
    blasts.push({owner:w.owner,world:w.world,x:w.x,y:w.y,radius,age:0,life:.34});
    w.dead=true;
  }
  function advance(w,dt) {
    if(w.mode==='tenten-tags' && w.landed) { w.landedAge+=dt; if(w.landedAge+1e-8>=w.fuse)explode(w);return; }
    if(w.mode==='tenten-fuma') {
      const steps=Math.max(1,Math.ceil(dt*120)), step=dt/steps;
      for(let i=0;i<steps&&!w.dead;i++) {
        w.age+=step;
        if(!w.back) {
          const t=Math.min(1,w.age/w.duration), bend=Math.sin(t*Math.PI)*w.bend;
          sweep(w,w.sx+(w.tx-w.sx)*t-w.dy*bend,w.sy+(w.ty-w.sy)*t+w.dx*bend);
          if(t>=1&&!w.dead) {w.back=true;w.returnAge=0;w.rx=w.x;w.ry=w.y;w.hits=w.returnHits;w.spent=false;w.pierce=Math.max(0,w.m.pierce||0);}
        } else {
          w.returnAge+=step;
          const t=Math.min(1,w.returnAge/w.duration), bend=Math.sin(t*Math.PI)*w.bend;
          // Rejoin the moving actor over a finite trip, rather than chase forever.
          sweep(w,w.rx+(w.owner.x-w.rx)*t+w.dy*bend,w.ry+(w.owner.y-w.ry)*t-w.dx*bend);
          if(t>=1) {
            w.dead=true;
            const s=state(w.owner);
            if(!s.pose||s.pose.mode==='tenten-kunai')s.pose={kind:'tenten-fuma',mode:'tenten-fuma',m:w.m,phase:'catch',
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
    if(owner)states.delete(owner);else states.clear();
    for(const list of [weapons,blasts])for(let i=list.length-1;i>=0;i--)if(!owner||list[i].owner===owner)list.splice(i,1);
  }
  function update(dt) {
    if(G.Game.state!=='playing'||!(dt>0))return;
    for(const [owner,s] of states) {
      if(!valid(owner)||s.world!==G.World){clear(owner);continue;}
      s.clock+=dt;
      if(s.pose) { s.pose.age=s.clock-s.pose.started; if(s.pose.age>=s.pose.duration)s.pose=null; }
      for(let i=s.batches.length-1;i>=0;i--) {
        const b=s.batches[i];
        if(b.mode!=='tenten-kunai'&&!selected(owner,b.m.id)){s.batches.splice(i,1);continue;}
        b.age=s.clock-b.started;
        emitDue(b); if(b.batch>=b.schedule.length)s.batches.splice(i,1);
      }
    }
    for(let i=weapons.length-1;i>=0;i--) {
      const w=weapons[i];if(!valid(w.owner)||w.world!==G.World)w.dead=true;else advance(w,dt);
      if(w.dead)weapons.splice(i,1);
    }
    for(let i=blasts.length-1;i>=0;i--) {const b=blasts[i];b.age+=dt;if(!valid(b.owner)||b.world!==G.World||b.age>=b.life)blasts.splice(i,1);}
  }
  // Small cached material silhouettes; no particles or decorative cap can discard damage.
  const sprites=new Map();
  function sprite(kind) {
    if(sprites.has(kind))return sprites.get(kind);
    const c=document.createElement('canvas');c.width=c.height=40;const ctx=c.getContext('2d');ctx.translate(20,20);
    ctx.strokeStyle='#273442';ctx.fillStyle='#c5d2d6';ctx.lineWidth=2;
    if(kind==='fuma') {
      for(let i=0;i<4;i++){ctx.rotate(Math.PI/2);ctx.beginPath();ctx.moveTo(-3,2);ctx.lineTo(0,-17);ctx.lineTo(7,-7);ctx.lineTo(3,4);ctx.closePath();ctx.fill();ctx.stroke();}
      ctx.fillStyle='#273442';ctx.fillRect(-2,-2,4,4);
    } else if(kind==='shuriken') {
      ctx.beginPath();for(let i=0;i<8;i++){const a=i*Math.PI/4,r=i%2?3:10;ctx.lineTo(Math.cos(a)*r,Math.sin(a)*r);}ctx.closePath();ctx.fill();ctx.stroke();
    } else {
      ctx.beginPath();ctx.moveTo(13,0);ctx.lineTo(-1,-4);ctx.lineTo(-5,0);ctx.lineTo(-1,4);ctx.closePath();ctx.fill();ctx.stroke();
      ctx.fillStyle='#384859';ctx.fillRect(-12,-2,8,4);ctx.strokeRect(-16,-3,5,6);
      if(kind==='tag'){ctx.fillStyle='#f3e5bc';ctx.fillRect(-10,1,7,15);ctx.strokeStyle='#a83f3d';ctx.strokeRect(-8,4,3,8);}
    }
    sprites.set(kind,c);return c;
  }
  function air(ctx) {
    ctx.save();
    for(const w of weapons) {
      if(!valid(w.owner)||w.world!==G.World||!G.Camera.sees(w.x,w.y,45))continue;
      const kind=w.mode==='tenten-fuma'?'fuma':w.mode==='tenten-tags'?'tag':w.mode==='tenten-twin'&&w.seed%3===0?'shuriken':'kunai';
      ctx.save();ctx.translate(w.x,w.y-(w.landed?0:G.LIFT));ctx.rotate(kind==='fuma'||kind==='shuriken'?w.age*18:w.angle);
      ctx.drawImage(sprite(kind),-20,-20);ctx.restore();
    }
    for(const b of blasts) {
      if(b.world!==G.World)continue;
      const t=b.age/b.life;ctx.save();ctx.globalAlpha=1-t;
      ctx.fillStyle=t<.3?'#f9df9a':'#a89d8c';
      // Visible material burst stays within exactly the damaging blast radius.
      for(let i=0;i<12;i++){const a=i*2.39996,r=b.radius*(.25+.65*t)*Math.sqrt((i+1)/12),z=b.radius*(.22-.13*t);ctx.fillRect(b.x+Math.cos(a)*r-z/2,b.y+Math.sin(a)*r-z/2,z,z);}
      ctx.restore();
    }
    ctx.restore();
  }
  function ground(ctx) {
    ctx.save();ctx.lineWidth=1;
    // The atlas owns both held rolls. Only paper extending behind the body is drawn here.
    for(const s of states.values())if(valid(s.owner)&&s.world===G.World&&s.pose?.mode==='tenten-twin') {
      const p=s.pose,scale=s.owner.anim?.scale||1,extend=Math.min(1,p.age/.16),alpha=Math.min(1,(p.duration-p.age)/.18);
      for(const side of [-1,1]) {
        const hand=G.AnimationLab?.handForTenten?.(s.owner,side)||origin(s.owner,p.aim,side);
        const outward=Math.sign(hand.x-s.owner.x)||side;
        const x=hand.x,y=hand.y-G.LIFT,length=(14+26*extend)*scale;
        ctx.save();ctx.globalAlpha=.8*Math.max(0,alpha);ctx.lineJoin='round';ctx.lineCap='butt';
        ctx.beginPath();ctx.moveTo(x,y);
        ctx.bezierCurveTo(x+outward*length*.45,y-9*scale,x+outward*length*.9,y+17*scale,
          x+outward*length,y+8*scale+Math.sin(p.age*12+side)*4*scale);
        ctx.strokeStyle='#5b493b';ctx.lineWidth=7*scale;ctx.stroke();
        ctx.strokeStyle='#e8d6b0';ctx.lineWidth=5*scale;ctx.stroke();ctx.restore();
      }
    }
    for(const w of weapons)if(w.mode==='tenten-tags'&&w.landed&&valid(w.owner)&&w.world===G.World){
      ctx.strokeStyle='#b38d60';ctx.globalAlpha=.22;ctx.setLineDash([3,5]);ctx.beginPath();ctx.arc(w.x,w.y,w.m.blastRadius||w.m.radius||60,0,TAU);ctx.stroke();
    }
    ctx.restore();
  }
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
      shots:own.length,tagCount:own.filter(w=>w.mode==='tenten-tags').length,returning:own.filter(w=>w.back).length,
      masteryPierce:p.pierce,masterySpeed:p.speed};
  }
  function activeFor(owner) {
    const s=states.get(owner);if(!valid(owner)||s?.world!==G.World)return null;
    if(s.pose)return s.pose;
    const m=owner.activeGroup?.().find(m=>m.digiMode==='tenten-fuma'&&m.t>0&&m.t<=.08);
    const target=owner.target;
    if(m&&alive(target)&&Math.hypot(target.x-owner.x,target.y-owner.y)<=(m.range||300))return {
      owner,kind:'tenten-fuma',mode:'tenten-fuma',m,phase:'prepare',age:.08-m.t,duration:.08,
      aim:Math.atan2(target.y-owner.y,target.x-owner.x),count:0,emitted:0};
    return null;
  }
  G.NarutoTenten={supports,canCast,cast,clear,update,stage,stateFor,
    activeFor,
    get weapons(){return weapons;},get blasts(){return blasts;}};
})();
