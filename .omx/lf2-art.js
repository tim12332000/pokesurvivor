// Classic LF2 2.0a pixels and dat choreography. See assets/lf2/freeze/manifest.json.
(() => {
  const ROOT = 'assets/lf2/freeze/';
  const DATA_VERSION = new URL(document.currentScript?.src || location.href).searchParams.get('data') || 'classic-1';
  let metadata = null, pending = null;
  const images = {}, flashes = {};
  function load() {
    if (pending) return pending;
    pending = fetch(ROOT + 'manifest.json?v=' + DATA_VERSION).then(r => {
      if (!r.ok) throw new Error('Freeze manifest ' + r.status);
      return r.json();
    }).then(async data => {
      metadata = data;
      await Promise.all(data.source.files.filter(f => f.runtime?.endsWith('.png')).map(f => new Promise((resolve, reject) => {
        const key = f.runtime.split('/').pop(), img = new Image();
        img.onload = () => { images[key] = img; resolve(); };
        img.onerror = () => reject(new Error('Freeze image ' + key));
        img.src = f.runtime + '?v=' + f.runtime_sha256.slice(0, 12);
      })));
      api.loaded = true;
      return true;
    }).catch(error => { pending = null; throw error; });
    return pending;
  }
  const object = key => metadata?.objects[key];
  function frame(key, id) {
    const obj = object(key), f = obj?.frames[id];
    if (!f) return null;
    const sheet = obj.sheets.find(s => f.pic >= s.start && f.pic <= s.end);
    if (!sheet) return null;
    const n = f.pic - sheet.start;
    return {...f, id:+id, object:key, image:sheet.image, rect:[n % sheet.columns * (sheet.w + 1), Math.floor(n / sheet.columns) * (sheet.h + 1), sheet.w, sheet.h]};
  }
  function sequence(key, start, age, loop = false) {
    const obj = object(key); if (!obj) return null;
    let id = start, ticks = Math.max(0, age) * 30;
    for (let guard = 0; guard < 512; guard++) {
      const f = obj.frames[id]; if (!f) return frame(key,start);
      const duration = Math.max(1, (f.wait ?? 0) + 1);
      if (ticks < duration) return frame(key,id);
      ticks -= duration;
      if (f.next >= 999 || f.next == null) {
        if (!loop) return frame(key,id);
        id = start;
      } else id = f.next;
    }
    return frame(key,start);
  }
  function sample(state = 'idle', time = 0, dir = 0, pose = null) {
    if (!metadata) return null;
    if (state === 'faint' || state === 'death') return sequence('freeze',230,time);
    if (state === 'hurt') return sequence('freeze',180,time);
    if (pose) {
      const mode = pose.kind || pose.mode || '';
      if (/summon/.test(mode)) return sequence('freeze',270,pose.age || 0);
      if (/punch/.test(mode)) return sequence('freeze',pose.swingIndex % 2 ? 65 : 60,pose.swingAge ?? pose.age ?? 0);
      if (/sword/.test(mode)) {
        // Each actual swing plays the original windup, contact, and followthrough.
        const age = pose.swingAge ?? pose.age ?? 0;
        return sequence('freeze',pose.swingIndex % 2 ? 25 : 20,age);
      }
      if (/whirl/.test(mode)) return sequence('freeze',260,pose.age || 0);
      if (/column|icicle/.test(mode)) return sequence('freeze',245,pose.age || 0);
      return sequence('freeze',235,pose.age || 0);
    }
    if (state === 'walk' || state === 'move') return frame('freeze',5 + Math.floor(Math.max(0,time) * 7.5) % 4);
    return sequence('freeze',0,time,true);
  }
  function flashFor(key) {
    if (flashes[key]) return flashes[key];
    const src = images[key], canvas = document.createElement('canvas');
    canvas.width = src.width; canvas.height = src.height;
    const ctx = canvas.getContext('2d'); ctx.drawImage(src,0,0);
    ctx.globalCompositeOperation = 'source-in'; ctx.fillStyle = '#fff'; ctx.fillRect(0,0,canvas.width,canvas.height);
    return flashes[key] = canvas;
  }
  function paint(ctx, f, x, y, scale = 1, left = false, alpha = 1, flash = false, anchor = null) {
    if (!f || !images[f.image]) return false;
    const [sx,sy,w,h] = f.rect, ax = anchor?.[0] ?? f.centerx ?? w / 2, ay = anchor?.[1] ?? f.centery ?? h;
    ctx.save(); ctx.translate(Math.round(x), Math.round(y)); ctx.scale(left ? -scale : scale, scale);
    ctx.globalAlpha *= alpha; ctx.imageSmoothingEnabled = false;
    ctx.drawImage(flash ? flashFor(f.image) : images[f.image],sx,sy,w,h,-ax,-ay,w,h);
    ctx.restore(); return true;
  }
  function draw(ctx, actor = {}, options = {}) {
    if (!api.loaded) { void load().catch(() => {}); return false; }
    const pose = options.pose ?? G.LF2Freeze?.pose?.(actor), dir = options.dir ?? actor.anim?.dir ?? 0;
    const left = pose?.aim != null ? Math.cos(pose.aim) < 0 : dir >= 5;
    const f = sample(options.state || 'idle',options.time ?? actor.age ?? 0,dir,pose);
    const scale = (options.height ?? 64) / metadata.bodyHeight;
    const x = options.x ?? actor.x ?? 0, y = options.y ?? actor.y ?? 0;
    const equipped = G.LF2Freeze?.stateFor?.(actor)?.swordOwned && options.state !== 'faint' && options.state !== 'death';
    const weapon = equipped && f?.wpoint ? frame('weapon7',f.wpoint.weaponact) : null;
    const wp = f?.wpoint, grip = weapon?.wpoint;
    const move = actor.moves?.find(m => m.digiMode === 'lf2-sword');
    const reach = pose?.kind === 'sword' ? pose.range : move ? G.LF2Freeze?.profile?.(actor,move)?.range : 88;
    // The original horizontal blade reaches ~60 px beyond its grip, which is
    // ~29 px in front of the body on the contact frame. Range investment must
    // change the real blade silhouette while the hand stays attached.
    const weaponScale = Math.max(.5,((reach || 88) - 29 * scale) / 60);
    const drawWeapon = () => {
      if (!weapon || !grip) return;
      const sign = left ? -1 : 1;
      paint(ctx,weapon,x + sign * (wp.x - f.centerx) * scale,y + (wp.y - f.centery) * scale,weaponScale,left,options.alpha ?? 1,options.flash,[grip.x,grip.y]);
    };
    if (wp?.cover === 1) drawWeapon();
    paint(ctx,f,x,y,scale,left,options.alpha ?? 1,options.flash);
    if (wp?.cover !== 1) drawWeapon();
    return true;
  }
  function pointFor(actor, pose, name = 'release') {
    const f = sample('cast',pose?.age || 0,actor.anim?.dir || 0,pose);
    if (!f) return null;
    const p = name === 'grip' ? f.wpoint : f.opoint || f.bpoint;
    if (!p) return null;
    const scale = 64 * (actor.anim?.scale || 1) / metadata.bodyHeight;
    return {x:actor.x + (p.x - f.centerx) * scale * (Math.cos(pose?.aim || 0) < 0 ? -1 : 1),y:actor.y + (p.y - f.centery) * scale};
  }
  function drawEffects(ctx) {
    if (!api.loaded) return;
    const states = G.LF2Freeze?.renderStates?.() || [];
    for (const f of states.flatMap(s => s.effects || [])) {
      if (f.dead || f.age < 0) continue;
      if (G.Camera?.sees && !G.Camera.sees(f.x,f.y,Math.max(220,f.radius || 0))) continue;
      const age = f.age || 0, left = Math.cos(f.aim || 0) < 0;
      if (f.kind === 'iceball') {
        const sprite = sequence('freeze_ball',0,age,true);
        const scale = Math.max(.65,(f.radius || 20) / 20);
        paint(ctx,sprite,f.x,f.y - (f.lift ?? 32),scale,left);
      } else if (f.kind === 'column') {
        const variant = f.variant ?? f.index ?? 0;
        const sprite = sequence('freeze_column',[60,50,0][variant % 3],age);
        const scale = Math.max(.65,(f.radius || 35) / 45);
        paint(ctx,sprite,f.x,f.y,scale,left);
      } else if (f.kind === 'whirlwind') {
        const ending = f.life != null && f.life - age < .2;
        const sprite = sequence('freeze_column',ending ? 158 : 150,ending ? .2 - (f.life - age) : age);
        paint(ctx,sprite,f.x,f.y,Math.max(.8,(f.radius || 70) / 70),left);
      } else if (f.kind === 'impact') {
        paint(ctx,sequence('freeze_ball',10,age),f.x,f.y,.7,left,Math.max(0,1-age/.3));
      }
    }
    const ice = images['freeze_ice.png'];
    if (ice) for (const {enemy:e,remaining,duration} of G.LF2Freeze?.frozenTargets?.() || []) {
      if (G.Camera?.sees && !G.Camera.sees(e.x,e.y,100)) continue;
      const size = Math.max(28,Math.min(92,(e.r || 14) * 3.7));
      const index = remaining > duration - .12 ? 0 : 1;
      ctx.save(); ctx.imageSmoothingEnabled = false;
      ctx.globalAlpha *= Math.min(.86,remaining * 6);
      ctx.drawImage(ice,index*80,0,79,79,e.x-size*.5,e.y-size,size,size);
      ctx.restore();
    }
  }
  // Original samples are emitted by simulation events, never by drawing.
  const playSound = (id,owner) => G.LF2Audio?.play(id,owner);
  const stopSounds = owner => G.LF2Audio?.stop(owner);
  const api = {loaded:false,load,draw,drawEffects,pointFor,sample,frame,sequence,playSound,stopSounds,images,
    get ready() { return load(); }, get metadata() { return metadata; }};
  G.LF2Art = api;
})();
