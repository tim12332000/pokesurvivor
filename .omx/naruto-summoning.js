/* Gamabunta: fixed landing site, one impact, simulation-time animation. */
(() => {
  if (G.NarutoSummoning) return;
  const effects = [], shots = new Set(), C = G.Combat, image = new Image(), waterArt = new Image();
  const swordArt = new Image(), oilArt = new Image(), foxArt = new Image(), flameArt = new Image();
  const loaded = img => new Promise(resolve => { img.onload = () => resolve(true); img.onerror = () => resolve(false); });
  const ready = Promise.all([image,waterArt,swordArt,oilArt,foxArt,flameArt].map(loaded));
  image.src = 'art-review/redrawn/gamabunta-summon-v2.png';
  waterArt.src = 'art-review/redrawn/gamabunta-water-v1.png';
  swordArt.src = 'art-review/redrawn/gamabunta-sword-v1.png';
  oilArt.src = 'art-review/redrawn/gamabunta-breath-actor-v1.png';
  flameArt.src = 'art-review/redrawn/gamabunta-oil-flame-v1.png';
  foxArt.src = 'art-review/redrawn/gamabunta-combo-fox-v2.png';
  // Authored alpha bounds plus four pixels of padding; one shared body scale.
  const frames = [[69,312,434,279],[585,157,458,383],[1121,297,448,287],[1672,209,408,375]];
  const waterFrames = [[265,114,690,515,345,511],[1206,143,786,487,373,483]];
  const swordFrames=[[40,239,433,335,230,331],[526,122,516,455,238,451],[1057,256,680,319,228,315],[1739,221,392,359,186,355]];
  const oilFrames=[[120,112,706,522,355,518],[1084,139,1042,497,390,493]];
  // Explicit bounds and emitter anchors; generated frames are not an equal grid.
  const flameFrames=[
    [28,215,330,180,18,86,120],[465,150,475,280,15,150,185],
    [945,110,590,360,16,190,240],[0,590,528,360,2,194,240],
    [528,590,555,360,7,194,240],[1083,685,453,230,6,99,150]
  ];
  const flameWidths=[287,440,567,513,535,360];
  const foxFrames=[[111,221,385,305,239,301],[656,220,401,306,244,302],[1172,220,386,280,213,302],[1715,221,371,305,245,301]];
  const mouth = (f, mirror = f.mirror) => { const scale = f.m.radius * 1.5 / 720; return { x:f.x + 306 * scale * (mirror ? -1 : 1), y:f.y - 281 * scale + G.LIFT }; };
  // Oil-spit art has a different mouth anchor from the water-spit atlas.
  const flameMouth = f => { const scale=f.m.radius*1.5/720;return {x:f.x+206*scale*(f.mirror?-1:1),y:f.y-267*scale+G.LIFT}; };
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
    const art = [image,waterArt,...(tier(move)>=2?[swordArt]:[]),...(tier(move)>=4?[oilArt,flameArt]:[]),...(tier(move)>=5?[foxArt]:[])];
    return supports(move.digiMode) && valid({ owner, world: G.World }) && art.every(img=>img.complete&&img.naturalWidth>0) &&
      !effects.some(f => f.owner === owner) && !!targetFor(owner, move);
  }
  function cast(owner, move) {
    if (!canCast(owner, move)) return false;
    const target = targetFor(owner, move);
    effects.push({ owner, world: G.World, m: { ...move }, rank:tier(move), x: target.x, y: target.y, age: 0, hit: false, atk: owner.atk, volley: 0, spitAt: -Infinity, mirror: false, events:[], swordHit:false, fireAttempted:false, foxHits:new Set() });
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
  function breathe(f) {
    f.fireAttempted=true;
    const target=rangedTarget(f)||targetFor(f,f.m);
    if(target)f.mirror=target.x<f.x;
    const origin=flameMouth(f);
    if(G.World.projectileBlock(origin.x,origin.y,10)||!clearPath(f.x,f.y,origin.x,origin.y))return;
    const side=f.mirror?-1:1;
    f.fireAt=f.age;f.fireOrigin=origin;
    // Keep the oil jet and flames on the same axis, including after a wave dies.
    f.fireAim=Math.atan2(.25,side);
    f.fireHits=new Set();f.fireProps=new Set();event(f,'fire');
  }
  // The widening breath grows from the mouth. Visuals and damage share this geometry.
  function flameFrame(f){
    const t=f.age-f.fireAt;
    return t<.08?0:t<.17?1:t<.6?2+Math.floor((t-.17)*14)%3:5;
  }
  function flameLength(f){
    const t=f.age-f.fireAt;
    return Math.min(flameFrames[flameFrame(f)][6],240*Math.min(1,Math.max(0,t/.25),Math.max(0,(.75-t)/.15)));
  }
  function inFlame(f,e){
    const o=f.fireOrigin,dx=e.x-o.x,dy=e.y-o.y,c=Math.cos(f.fireAim),s=Math.sin(f.fireAim);
    const along=dx*c+dy*s,width=12+55*Math.max(0,along)/240;
    return along>=0&&along<=flameLength(f)&&Math.abs(-dx*s+dy*c)<=width+(e.r||0)&&clearPath(o.x,o.y,e.x,e.y,e);
  }
  function burn(f){
    const o=f.fireOrigin;
    for(const e of new Set(G.EnemyMgr.queryCircle(o.x,o.y,310)))if(alive(e)&&!f.fireHits.has(e.id)&&inFlame(f,e)){
      f.fireHits.add(e.id);deal(f,e,.5,'fire');
    }
    for(const prop of G.World.propsInCircle(o.x,o.y,310))if(!f.fireProps.has(prop)&&inFlame(f,prop)){
      f.fireProps.add(prop);G.World.damageProp(prop,f.m.dmg*.5*f.atk,'#ffb846');
    }
  }
  function segmentDistance(x,y,ax,ay,bx,by) {
    const dx=bx-ax,dy=by-ay,t=Math.max(0,Math.min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy||1)));
    return Math.hypot(x-ax-dx*t,y-ay-dy*t);
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
      if(f.rank>=4&&!f.fireAttempted&&f.age>=3.1){if(f.age<3.35)breathe(f);else f.fireAttempted=true;}
      if(f.fireAt!=null&&f.age-f.fireAt<.75)burn(f);
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
      if(phase==='fire-windup'||phase==='fire'){
        drawActor(ctx,oilArt,oilFrames[phase==='fire-windup'?0:1],f.x,f.y,m.radius*1.5/720,f.mirror);
        if(phase==='fire')drawFlame(ctx,f);continue;
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
  function drawFlame(ctx,f){
    const o=f.fireOrigin,c=Math.cos(f.fireAim),s=Math.sin(f.fireAim),length=flameLength(f),t=f.age-f.fireAt;
    const frame=flameFrame(f),[sx,sy,sw,sh,ax,ay,reach]=flameFrames[frame],scale=reach/flameWidths[frame];
    const scaleX=length/flameWidths[frame],scaleY=scale*(.5+.5*Math.min(1,length/reach));
    ctx.save();ctx.translate(o.x,o.y-G.LIFT);ctx.rotate(f.fireAim);
    ctx.globalAlpha*=Math.min(1,(.75-t)/.12);ctx.beginPath();
    // Clip the authored plume against the same world paths used for damage.
    for(let d=0;d<length;d+=8)for(let offset=-90;offset<90;offset+=12){
      const x=o.x+c*(d+4)-s*(offset+6),y=o.y+s*(d+4)+c*(offset+6);
      if(clearPath(o.x,o.y,x,y)&&!G.World.projectileBlock(x,y,2))ctx.rect(d,offset,Math.min(8,length-d),12);
    }
    ctx.clip();ctx.imageSmoothingEnabled=true;
    ctx.drawImage(flameArt,sx,sy,sw,sh,-ax*scaleX,-ay*scaleY,sw*scaleX,sh*scaleY);
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
  C.resolve = function(...args) { pruneInvalid(); return previous.resolve.apply(this,args); };

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
    if(f.rank>=4&&f.age>=2.95)return f.age<3.1?'fire-windup':f.fireAt!=null&&f.age-f.fireAt<.75?'fire':'rest';
    if(f.rank>=2&&f.age>=2.15&&f.age<2.8)return f.age<2.45?'sword-windup':f.age<2.6?'sword-hit':'sword-recovery';
    return f.age<f.m.windup?(f.rank>=3?'heavy-drop':'arrival'):f.age>=.95&&f.age<2.2?'water':'rest';
  }
  const poseFor=owner=>{
    const f=effects.find(f=>f.owner===owner&&valid(f));if(!f)return null;
    if(f.rank>=5&&f.age>=7.3&&f.age<7.7)return {kind:'seal',age:f.age-7.3};
    return null;
  };
  G.NarutoSummoning = { supports, canCast, cast, clear, ready, mouth, flameMouth, flameFrame, phaseFor,poseFor, get effects() { return effects; }, get shots() { return [...shots]; } };
})();
