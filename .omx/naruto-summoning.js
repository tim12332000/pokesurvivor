/* Gamabunta: fixed landing site, one impact, simulation-time animation. */
(() => {
  if (G.NarutoSummoning) return;
  const effects = [], shots = new Set(), C = G.Combat, image = new Image(), waterArt = new Image();
  const swordArt = new Image(), oilArt = new Image(), foxArt = new Image();
  const loaded = img => new Promise(resolve => { img.onload = () => resolve(true); img.onerror = () => resolve(false); });
  const ready = Promise.all([image,waterArt,swordArt,oilArt,foxArt].map(loaded));
  image.src = 'art-review/redrawn/gamabunta-summon-v2.png';
  waterArt.src = 'art-review/redrawn/gamabunta-water-v1.png';
  swordArt.src = 'art-review/redrawn/gamabunta-sword-v1.png';
  oilArt.src = 'art-review/redrawn/gamabunta-oil-v1.png';
  foxArt.src = 'art-review/redrawn/gamabunta-combo-fox-v2.png';
  G.VFX.PAL['toad-oil']=['#2d1e18','#5f3a21','#a26b32','#d9a659','#f3d598'];
  G.VFX.PAL['toad-tag']=['#1b1b25','#9e2935','#889bad','#f0dbad','#ffffff'];
  G.VFX.SHAPES['toad-tag']={w:19,h:12,dir:true,frames:1,gen(P){
    P.line(3,4,16,4,'m',1);P.line(14,2,18,4,'w');P.line(18,4,14,6,'m');
    for(let y=6;y<11;y++)for(let x=3;x<8;x++)P.set(x,y,'l');
    P.line(5,7,5,9,'d');P.set(4,8,'d');P.set(6,8,'d');P.outline();
  }};
  // Authored alpha bounds plus four pixels of padding; one shared body scale.
  const frames = [[69,312,434,279],[585,157,458,383],[1121,297,448,287],[1672,209,408,375]];
  const waterFrames = [[265,114,690,515,345,511],[1206,143,786,487,373,483]];
  const swordFrames=[[40,239,433,335,230,331],[526,122,516,455,238,451],[1057,256,680,319,228,315],[1739,221,392,359,186,355]];
  const oilFrames=[[120,112,706,522,355,518],[1084,139,1042,497,390,493]];
  const foxFrames=[[111,221,385,305,239,301],[656,220,401,306,244,302],[1172,220,386,280,213,302],[1715,221,371,305,245,301]];
  const mouth = (f, mirror = f.mirror) => { const scale = f.m.radius * 1.5 / 720; return { x:f.x + 306 * scale * (mirror ? -1 : 1), y:f.y - 281 * scale + G.LIFT }; };
  const alive = actor => actor && !actor.dead && actor.hp > 0;
  const controlled = owner => G.SelfClones?.isControlled(owner) ?? (owner === G.Game.player);
  const valid = f => controlled(f.owner) && alive(f.owner) && f.owner.mon?.dex === 30001 && f.world === G.World;
  const supports = mode => mode === 'toad-summon';
  const tier = m => Math.max(1,Math.min(5,m.lvl|0));
  const clearPath = (...args) => G.World.projectilePathClear(...args);
  function targetFor(owner, move, eligible = () => true) {
    return [...new Set(G.EnemyMgr.queryCircle(owner.x, owner.y, move.range))]
      .filter(e => alive(e) && Math.hypot(e.x - owner.x, e.y - owner.y) <= move.range && eligible(e) && clearPath(owner.x, owner.y, e.x, e.y))
      .sort((a, b) => Math.hypot(a.x - owner.x, a.y - owner.y) - Math.hypot(b.x - owner.x, b.y - owner.y))[0];
  }
  function canCast(owner, move) {
    const art = [image,waterArt,...(tier(move)>=2?[swordArt]:[]),...(tier(move)>=4?[oilArt]:[]),...(tier(move)>=5?[foxArt]:[])];
    return supports(move.digiMode) && valid({ owner, world: G.World }) && art.every(img=>img.complete&&img.naturalWidth>0) &&
      !effects.some(f => f.owner === owner) && !!targetFor(owner, move);
  }
  function cast(owner, move) {
    if (!canCast(owner, move)) return false;
    const target = targetFor(owner, move);
    effects.push({ owner, world: G.World, m: { ...move }, rank:tier(move), x: target.x, y: target.y, age: 0, hit: false, atk: owner.atk, volley: 0, spitAt: -Infinity, mirror: false, events:[], swordHit:false, oilAttempted:false, foxHits:new Set() });
    return true;
  }
  function clear(owner) {
    for (let i = effects.length - 1; i >= 0; i--) if (!owner || effects[i].owner === owner) effects.splice(i, 1);
    for (const shot of shots) if (!owner || shot.owner === owner) { G.Projectiles.remove(shot); shots.delete(shot); }
  }
  function pruneInvalid() {
    for (let i = effects.length - 1; i >= 0; i--) if (!valid(effects[i])) effects.splice(i, 1);
    if (!shots.size) return;
    const live = new Set(G.Projectiles.all());
    for (const shot of shots) {
      if (!valid(shot.summon) || (shot.summonKind!=='water'&&!effects.includes(shot.summon))) { G.Projectiles.remove(shot); shots.delete(shot); }
      else if (!live.has(shot)) shots.delete(shot);
    }
  }
  function rangedTarget(f) {
    return targetFor(f, f.m, e => {
      const mirror = e.x < f.x, origin = mouth(f, mirror), side = mirror ? -1 : 1;
      return side * (e.x - origin.x) > 0 && !G.World.projectileBlock(origin.x, origin.y, 13) &&
        clearPath(f.x, f.y, origin.x, origin.y) && clearPath(origin.x, origin.y, e.x, e.y);
    });
  }
  const event = (f,kind) => f.events.push({kind,age:f.age});
  function deal(f,e,ratio,type=f.m.type,knock=0) {
    if(!valid(f)||!alive(e))return;
    const mult=G.Types.mult(type,e.types),crit=Math.random()<(f.owner.critChance||0);
    const damage=f.m.dmg*ratio*f.atk*mult*G.Weather.mult(type)*(crit?1.5:1)*(G.NarutoSupport?.precisionMultiplier(f.owner,e)||1);
    const boss=e.boss||e.elite||e.legend||e.judge;
    e.hurt(damage,'#dfb879',e.x-f.x,e.y-f.y,boss?0:knock,crit?'crit':G.Types.label(mult),f.owner,f.m.id);
    f.owner.onDealt(damage);f.owner.dmgDealt+=damage;
  }
  function area(f,x,y,radius,ratio,type=f.m.type,knock=0,test=()=>true) {
    for(const e of new Set(G.EnemyMgr.queryCircle(x,y,radius)))if(alive(e)&&Math.hypot(e.x-x,e.y-y)<=radius+(e.r||0)&&test(e)&&clearPath(x,y,e.x,e.y))deal(f,e,ratio,type,knock);
    for(const prop of G.World.propsInCircle(x,y,radius))if(test(prop)&&clearPath(x,y,prop.x,prop.y,prop))G.World.damageProp(prop,f.m.dmg*ratio*f.atk,'#dfb879');
  }
  function spit(f) {
    const target = rangedTarget(f);
    if (!target) return;
    f.mirror = target.x < f.x;
    const { x, y } = mouth(f);
    const angle = Math.atan2(target.y - y, target.x - x);
    const shot = G.Projectiles.spawn({ x, y, vx: Math.cos(angle) * 300, vy: Math.sin(angle) * 300,
      dmg: f.m.dmg * f.atk / 6, r: 13, life: 1.25, pierce: 0, hits: new Set(),
      owner: f.owner, mid: f.m.id, mtype: 'water', damageSplash: false,
      color: '#8ccaff', vis: { proj: 'ball', pal: 'water', trail: 'drip', projScale: 1.6 }, summon: f, summonKind:'water' });
    shots.add(shot); f.spitAt = f.age;
    event(f,'water');
  }
  function oil(f) {
    f.oilAttempted=true;
    const target=rangedTarget(f);if(!target)return;
    f.mirror=target.x<f.x;
    const origin=mouth(f),angle=Math.atan2(target.y-origin.y,target.x-origin.x);
    const shot=G.Projectiles.spawn({...origin,vx:Math.cos(angle)*300,vy:Math.sin(angle)*300,dmg:0,r:13,life:1.25,pierce:0,hits:new Set(),ghost:true,
      owner:f.owner,mid:f.m.id,mtype:'normal',damageSplash:false,color:'#a26b32',vis:{proj:'ball',pal:'toad-oil',projScale:1.6},summon:f,summonKind:'oil'});
    f.oilTarget=target;f.oilShot=shot;shots.add(shot);f.oilSpitAt=f.age;event(f,'oil-fired');
  }
  function tag(f) {
    const x=f.owner.x+(f.oil.x<f.owner.x?-16:16),y=f.owner.y-28+G.LIFT;
    if(!clearPath(f.owner.x,f.owner.y,x,y)||G.World.projectileBlock(x,y,5))return;
    const angle=Math.atan2(f.oil.y-y,f.oil.x-x);
    const shot=G.Projectiles.spawn({x,y,vx:Math.cos(angle)*400,vy:Math.sin(angle)*400,dmg:0,r:5,life:1.6,pierce:0,hits:new Set(),ghost:true,
      owner:f.owner,mid:f.m.id,mtype:'normal',damageSplash:false,color:'#f5dca6',vis:{proj:'toad-tag',pal:'toad-tag'},summon:f,summonKind:'tag'});
    shots.add(shot);f.tagAt=f.age;f.tagAim=angle;event(f,'tag-fired');
  }
  function segmentDistance(x,y,ax,ay,bx,by) {
    const dx=bx-ax,dy=by-ay,t=Math.max(0,Math.min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy||1)));
    return Math.hypot(x-ax-dx*t,y-ay-dy*t);
  }
  function resolveSupport() {
    const live=new Set(G.Projectiles.all());
    for(const shot of [...shots]) {
      const f=shot.summon;if(!valid(f)||!effects.includes(f))continue;
      if(shot.summonKind==='oil'&&!f.oil&&shot.hits.has(f.oilTarget.id)) {
        f.oil={x:f.oilTarget.x,y:f.oilTarget.y,radius:80,ignited:false};event(f,'oil-coated');tag(f);
      }
      if(shot.summonKind==='tag'&&f.oil&&!f.oil.ignited) {
        const touched=(live.has(shot)||shot.hits.size>0)&&segmentDistance(f.oil.x,f.oil.y,shot.px??shot.x,shot.py??shot.y,shot.x,shot.y)<=shot.r+f.oil.radius;
        if(touched&&!G.World.projectileBlock(shot.x,shot.y,shot.r)&&clearPath(shot.px??shot.x,shot.py??shot.y,f.oil.x,f.oil.y)) {
          f.oil.ignited=true;f.fireAt=f.age;event(f,'fire');area(f,f.oil.x,f.oil.y,110,.5,'fire');
          G.FX.burst(f.oil.x,f.oil.y-15,'#ffb846',28,100);G.FX.ring(f.oil.x,f.oil.y,8,110,'#ffb846',.35,3);G.Projectiles.remove(shot);shots.delete(shot);
        }
      }
    }
  }
  function sword(f) {
    f.swordHit=true;event(f,'sword');
    f.mirror=f.swordMirror;
    const side=f.mirror?-1:1;
    area(f,f.x,f.y,160,.35,'normal',45,e=>Math.hypot(e.x-f.x,e.y-f.y)<=(e.r||0)||Math.abs(Math.atan2(e.y-f.y,(e.x-f.x)*side))<=1.1);
  }
  function fox(f) {
    if(f.foxX==null){f.foxX=f.x;f.foxY=f.y;const target=targetFor(f,f.m);if(target)f.mirror=target.x<f.x;event(f,'fox');}
    const side=f.mirror?-1:1,goal=f.x+side*140*Math.min(1,Math.max(0,(f.age-7.8)/.45)),start=f.foxX;
    for(let n=0;n<36&&Math.abs(goal-f.foxX)>.001&&!f.foxBlocked;n++) {
      const next=f.foxX+Math.sign(goal-f.foxX)*Math.min(4,Math.abs(goal-f.foxX));
      if(!G.World.isFree(next,f.foxY,24)||!clearPath(f.foxX,f.foxY,next,f.foxY)){f.foxBlocked=true;break;}f.foxX=next;
    }
    const head=50*side,x=(start+f.foxX)/2+head,reach=Math.abs(f.foxX-start)/2+45;
    for(const e of new Set(G.EnemyMgr.queryCircle(x,f.foxY,reach)))if(alive(e)&&!f.foxHits.has(e.id)&&segmentDistance(e.x,e.y,start+head,f.foxY,f.foxX+head,f.foxY)<=45+(e.r||0)&&clearPath(f.foxX,f.foxY,e.x,e.y)){
      f.foxHits.add(e.id);deal(f,e,.65,'normal',65);
    }
    if(f.age>=8.25)f.foxDone=true;
  }
  function update(dt) {
    pruneInvalid();
    for (let i = effects.length - 1; i >= 0; i--) {
      const f = effects[i], m = f.m;
      if (!valid(f)) { effects.splice(i, 1); continue; }
      if (!(dt > 0) || !Number.isFinite(dt)) continue;
      f.age += dt;
      if (f.age >= m.duration) { G.FX.burst(f.x, f.y - 30, '#e6e2d8', 18, 65); effects.splice(i, 1); continue; }
      if (!f.hit && f.age >= m.windup) {
        f.hit = true;
        event(f,f.rank>=3?'heavy':'landing');
        if (!G.World.isWall(f.x, f.y)) {
          area(f,f.x,f.y,m.radius,f.rank>=3?.75:.5,m.type,m.knock);
          G.FX.ring(f.x, f.y, 8, m.radius, '#ead6aa', .35, 4);
          G.FX.burst(f.x, f.y, '#ded4bf', 24, 90);
        }
      }
      const due = Math.min(3, Math.max(0, Math.floor((f.age - 1.1 + 1e-8) / .4) + 1));
      // Slow frames discard missed volley slots instead of releasing a late burst.
      if (due > f.volley) { f.volley = due; spit(f); }
      if(f.rank>=2&&!f.swordPrepared&&f.age>=2.15){f.swordPrepared=true;const target=targetFor(f,f.m);if(target)f.mirror=target.x<f.x;f.swordMirror=f.mirror;}
      if(f.rank>=2&&!f.swordHit&&f.age>=2.45){if(f.age<2.6)sword(f);else f.swordHit=true;}
      if(f.rank>=4&&!f.oilAttempted&&f.age>=3.1){if(f.age<3.35)oil(f);else f.oilAttempted=true;}
      if(f.rank>=5&&f.age>=7.3&&!f.transformed){f.transformed=true;if(f.age<7.7){event(f,'transform');G.FX.burst(f.x,f.y-35,'#ecede9',30,85);}}
      if(f.rank>=5&&f.age>=7.8&&!f.foxDone){if(f.age<=8.25)fox(f);else f.foxDone=true;}
    }
  }
  function ground(ctx) {
    ctx.save();
    for (const f of effects) if (valid(f)) {
      ctx.globalAlpha = f.hit ? .15 * Math.max(0, 1 - (f.age - f.m.windup) / .35) : .3;
      ctx.fillStyle = '#e2c99a'; ctx.strokeStyle = '#ffe4b0'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(f.x, f.y, f.m.radius, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      if (!f.hit) {
        ctx.globalAlpha = .8;
        ctx.beginPath(); ctx.arc(f.x, f.y, f.m.radius * Math.min(1, f.age / f.m.windup), 0, Math.PI * 2); ctx.stroke();
        ctx.strokeStyle = '#242331'; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.arc(f.x, f.y, 34, 0, Math.PI * 2); ctx.stroke();
        for (let i = 0; i < 8; i++) {
          const a = i * Math.PI / 4;
          ctx.beginPath(); ctx.moveTo(f.x + Math.cos(a) * 18, f.y + Math.sin(a) * 18);
          ctx.lineTo(f.x + Math.cos(a) * 42, f.y + Math.sin(a) * 42); ctx.stroke();
        }
      }
      if(f.oil){
        ctx.globalAlpha=f.oil.ignited?Math.max(0,.5*(1-(f.age-f.fireAt))):.65;
        ctx.fillStyle=f.oil.ignited?'#ea7d28':'#755027';
        ctx.beginPath();ctx.arc(f.oil.x,f.oil.y,f.oil.ignited?110:f.oil.radius,0,Math.PI*2);ctx.fill();
      }
    }
    ctx.restore();
  }
  function air(ctx) {
    if (!image.complete || !image.naturalWidth) return;
    ctx.save(); ctx.imageSmoothingEnabled = false;
    for (const f of effects) if (valid(f)) {
      const m = f.m, progress = Math.min(1, f.age / m.windup);
      ctx.globalAlpha = Math.min(1, f.age / .12, (m.duration - f.age) / .25);
      const phase=phaseFor(f);
      if(f.fireAt!=null&&f.age-f.fireAt<1){
        const t=f.age-f.fireAt;
        for(let n=0;n<9;n++){const a=n*2.4,r=Math.sqrt(n/9)*85;G.VFX.draw(ctx,'fire','fire',f.oil.x+Math.cos(a)*r,f.oil.y+Math.sin(a)*r-22,{scale:2.2*(1-t),frame:Math.floor(t*12+n)%3});}
      }
      if(phase==='transform'){
        ctx.strokeStyle='#9cecff';ctx.lineWidth=3;ctx.globalAlpha=.6;
        ctx.beginPath();ctx.moveTo(f.owner.x,f.owner.y-30);ctx.lineTo(f.x,f.y-60);ctx.stroke();
        ctx.save();ctx.globalAlpha=Math.min(1,(f.age-7.3)/.4);drawFox(ctx,f,'fox-ready');ctx.restore();
        ctx.globalAlpha=Math.max(0,1-(f.age-7.3)/.4);
      }
      if(phase.startsWith('fox')){drawFox(ctx,f,phase);continue;}
      if(phase.startsWith('sword')){
        const frame=f.age<2.3?0:f.age<2.45?1:f.age<2.6?2:3;
        drawActor(ctx,swordArt,swordFrames[frame],f.x,f.y,m.radius*1.5/460,f.mirror);continue;
      }
      if(phase==='oil-windup'||phase==='oil-spit'){
        drawActor(ctx,oilArt,oilFrames[phase==='oil-windup'?0:1],f.x,f.y,m.radius*1.5/720,f.mirror);continue;
      }
      if(f.age >= .95 && f.age < 2.2){
        const pose = f.age - f.spitAt < .16 ? 1 : 0;
        const [sx,sy,sw,sh,ax,ay] = waterFrames[pose], scale = m.radius * 1.5 / 720;
        ctx.save();ctx.translate(f.x,f.y);if(f.mirror)ctx.scale(-1,1);
        ctx.drawImage(waterArt,sx,sy,sw,sh,-ax*scale,-ay*scale,sw*scale,sh*scale);ctx.restore();
        continue;
      }
      const frame = !f.hit ? (progress < .28 ? 0 : 1) : f.age < m.windup + .2 ? 2 : 3;
      const lift = !f.hit ? Math.sin(Math.max(0, (progress - .28) / .72) * Math.PI) * (f.rank>=3?180:100) : 0;
      const [sx, sy, sw, sh] = frames[frame], scale = m.radius * 1.5 / 458;
      const width = sw * scale, height = sh * scale;
      ctx.drawImage(image, sx, sy, sw, sh,
        Math.round(f.x - width / 2), Math.round(f.y - (sh - 4) * scale - lift), width, height);
    }
    ctx.restore();
  }
  function drawActor(ctx,art,frame,x,y,scale,mirror){
    const [sx,sy,sw,sh,ax,ay]=frame;
    ctx.save();ctx.translate(x,y);if(mirror)ctx.scale(-1,1);
    ctx.drawImage(art,sx,sy,sw,sh,-ax*scale,-ay*scale,sw*scale,sh*scale);ctx.restore();
  }
  function drawFox(ctx,f,phase){
    const frame=phase==='fox-ready'?0:phase==='fox-dash'?(f.age<8.02?1:2):3;
    drawActor(ctx,foxArt,foxFrames[frame],f.foxX??f.x,f.foxY??f.y,f.m.radius*2.1/400,f.mirror);
  }
  const previous = { update: C.updateFields, resolve: C.resolve, ground: C.drawGroundFields, air: C.drawAirFields, clear: C.clearFields, skillClear: G.DigimonSkills.clear };
  C.resolve = function(...args) { pruneInvalid(); const result=previous.resolve.apply(this,args);resolveSupport();return result; };
  C.updateFields = function(dt) { const result = previous.update.call(this, dt); update(dt); return result; };
  C.drawGroundFields = function(ctx) { previous.ground.call(this, ctx); ground(ctx); };
  C.drawAirFields = function(ctx) { previous.air.call(this, ctx); air(ctx); };
  C.clearFields = function(owner) { previous.clear.call(this, owner); clear(owner); };
  G.DigimonSkills.clear = function(owner) { previous.skillClear.call(this, owner); clear(owner); };
  // The native faint loop skips combat updates but still draws projectiles.
  const playerHurt = G.Player.prototype.hurt, playerUpdate = G.Player.prototype.update;
  G.Player.prototype.hurt = function(...args) {
    const result = playerHurt.apply(this, args);
    if (!alive(this)) pruneInvalid();
    return result;
  };
  G.Player.prototype.update = function(...args) {
    pruneInvalid();
    const result = playerUpdate.apply(this, args);
    if (!alive(this)) pruneInvalid();
    return result;
  };
  function phaseFor(f) {
    if(f.rank>=5&&f.age>=7.3)return f.age<7.7?'transform':f.age<7.8?'fox-ready':f.age<8.25?'fox-dash':'fox-recovery';
    if(f.rank>=4&&f.age>=2.95)return f.fireAt!=null&&f.age-f.fireAt<1?'fire':f.age<3.1?'oil-windup':f.oilSpitAt!=null&&f.age-f.oilSpitAt<.25?'oil-spit':'oil-wait';
    if(f.rank>=2&&f.age>=2.15&&f.age<2.8)return f.age<2.45?'sword-windup':f.age<2.6?'sword-hit':'sword-recovery';
    return f.age<f.m.windup?(f.rank>=3?'heavy-drop':'arrival'):f.age>=.95&&f.age<2.2?'water':'rest';
  }
  const poseFor=owner=>{
    const f=effects.find(f=>f.owner===owner&&valid(f));if(!f)return null;
    if(f.rank>=5&&f.age>=7.3&&f.age<7.7)return {kind:'seal',age:f.age-7.3};
    if(f.tagAt!=null&&f.age-f.tagAt<.3)return {kind:'tag',age:f.age-f.tagAt,aim:f.tagAim,mirror:Math.cos(f.tagAim)<0};
    return null;
  };
  G.NarutoSummoning = { supports, canCast, cast, clear, ready, mouth, phaseFor,poseFor, get effects() { return effects; }, get shots() { return [...shots]; } };
})();
