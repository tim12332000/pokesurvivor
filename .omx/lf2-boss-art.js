/* Classic LF2 boss art: original dat frame chains and unmodified sprite cells. */
(() => {
  'use strict';
  if (G.LF2BossArt) return;
  const version = new URL(document.currentScript?.src || location.href).searchParams.get('data') || 'classic-bosses-1';
  const heroes = {30019:{slug:'firzen',height:64},30020:{slug:'julian',height:84}};
  const sheets = new Map(), pending = new Map();
  const dexFor = actor => +(actor?.mon?.dex ?? actor?.dex);
  const apiFor = dex => +dex === 30019 ? G.LF2Firzen : +dex === 30020 ? G.LF2Julian : null;
  const metadataFor = dex => sheets.get(+dex)?.metadata || null;
  const isReady = dex => !!sheets.get(+dex)?.loaded;
  function load(dex) {
    dex = +dex;
    if (!heroes[dex]) return Promise.resolve(false);
    if (isReady(dex)) return Promise.resolve(true);
    if (pending.has(dex)) return pending.get(dex);
    const task = (async () => {
      const response = await fetch(`assets/lf2/${heroes[dex].slug}/manifest.json?v=${version}`);
      if (!response.ok) throw Error('Classic LF2 manifest ' + response.status);
      const metadata = await response.json();
      const bundle = {metadata,images:{},flashes:{},frames:new Map(),loaded:false};
      await Promise.all(metadata.source.files.filter(f => f.runtime?.endsWith('.png')).map(f => new Promise((resolve,reject) => {
        const image = new Image(), key = f.runtime.split('/').pop();
        image.onload = () => { bundle.images[key] = image; resolve(); };
        image.onerror = () => reject(Error('Classic LF2 image ' + key));
        image.src = f.runtime + '?v=' + f.runtime_sha256.slice(0,12);
      })));
      bundle.loaded = true; sheets.set(dex,bundle); return true;
    })().finally(() => pending.delete(dex));
    pending.set(dex,task); return task;
  }
  function frame(dex,key,id) {
    const bundle = sheets.get(+dex), obj = bundle?.metadata.objects[key];
    if (!obj) return null;
    const cacheKey = key + ':' + id;
    if (bundle.frames.has(cacheKey)) return bundle.frames.get(cacheKey);
    const f = obj.frames[id], sheet = f && obj.sheets.find(s => f.pic >= s.start && f.pic <= s.end);
    if (!sheet) return null;
    const n = f.pic - sheet.start;
    const result = {...f,id:+id,object:key,image:sheet.image,rect:[n % sheet.columns * (sheet.w+1),Math.floor(n/sheet.columns)*(sheet.h+1),sheet.w,sheet.h]};
    bundle.frames.set(cacheKey,result); return result;
  }
  function sequence(dex,key,start,age,loop=false) {
    const obj = metadataFor(dex)?.objects[key]; if (!obj) return null;
    let id = start, ticks = Math.max(0,age || 0) * 30;
    for (let guard=0;guard<2048;guard++) {
      const f = obj.frames[id]; if (!f) return frame(dex,key,start);
      const duration = Math.max(1,(f.wait ?? 0)+1);
      if (ticks+1e-8 < duration) return frame(dex,key,id);
      ticks -= duration;
      if (f.next == null || f.next >= 999) {
        if (loop===false) return frame(dex,key,id);
        id = Number.isInteger(loop) ? loop : start;
      } else id = f.next;
    }
    return frame(dex,key,start);
  }
  function sample(dex,state='idle',time=0,dir=0,pose=null) {
    const hero = heroes[+dex]; if (!hero || !isReady(dex)) return null;
    const key = hero.slug;
    if (state==='death' || state==='faint') return sequence(dex,key,230,time);
    // Mirror's original empty frame is the actual evasion window. A flash
    // left over from the preceding hit must not replace it with a hurt body.
    if (+dex===30020 && pose?.mode==='lf2-julian-mirror') {
      const mirror=sequence(dex,key,pose.sourceStart??106,pose.sourceAge??pose.age??time);
      if (mirror?.id===103) return mirror;
    }
    if (state==='hurt') return sequence(dex,key,180,time);
    if (pose) {
      const start = pose.sourceStart ?? pose.startFrame;
      if (Number.isFinite(start)) return sequence(dex,key,start,pose.sourceAge ?? pose.age ?? time);
    }
    if (state==='walk' || state==='move') return frame(dex,key,5+Math.floor(Math.max(0,time)*7.5)%4);
    return sequence(dex,key,0,time,true);
  }
  function flashFor(dex,key) {
    const bundle = sheets.get(+dex); if (!bundle?.images[key]) return null;
    if (bundle.flashes[key]) return bundle.flashes[key];
    const image = bundle.images[key], canvas = document.createElement('canvas');
    canvas.width=image.width;canvas.height=image.height;
    const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0);ctx.globalCompositeOperation='source-in';
    ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);
    return bundle.flashes[key]=canvas;
  }
  function paint(ctx,dex,f,x,y,scale=1,left=false,alpha=1,flash=false) {
    const image = f && (flash ? flashFor(dex,f.image) : sheets.get(+dex)?.images[f.image]);
    if (!image) return false;
    const [sx,sy,w,h]=f.rect;
    ctx.save();ctx.translate(Math.round(x),Math.round(y));ctx.scale(left?-scale:scale,scale);
    ctx.imageSmoothingEnabled=false;ctx.globalAlpha*=alpha;
    ctx.drawImage(image,sx,sy,w,h,-(f.centerx??w/2),-(f.centery??h),w,h);
    ctx.restore();return true;
  }
  const heightFor = (dex,actor) => (heroes[+dex]?.height || 64)*(actor?.anim?.scale || 1);
  function draw(ctx,actor={},options={}) {
    const dex=+(options.dex??dexFor(actor)), hero=heroes[dex];
    if (!hero) return false;
    if (!isReady(dex)) { void load(dex).catch(()=>{});return false; }
    const pose=options.pose??apiFor(dex)?.pose?.(actor),dir=options.dir??actor.anim?.dir??0;
    const left=pose?.aim!=null?Math.cos(pose.aim)<0:dir>=5;
    const f=sample(dex,options.state||'idle',options.time??actor.age??0,dir,pose);
    const scale=(options.height??heightFor(dex,actor))/(metadataFor(dex).bodyHeight||65);
    return paint(ctx,dex,f,options.x??actor.x??0,options.y??actor.y??0,scale,left,options.alpha??1,options.flash);
  }
  function pointFor(actor,pose,name='release') {
    const dex=dexFor(actor),meta=metadataFor(dex),hero=heroes[dex];
    if (!meta || !hero) return null;
    const f=pose?.sourceReleaseFrame!=null?frame(dex,hero.slug,pose.sourceReleaseFrame):sample(dex,'cast',pose?.age||0,actor.anim?.dir||0,pose);
    const p=name==='grip'?f?.wpoint:name==='body'?f?.bpoint:f?.opoint||f?.bpoint;
    if (!p) return null;
    const scale=heightFor(dex,actor)/(meta.bodyHeight||65),sign=Math.cos(pose?.aim||0)<0?-1:1;
    return {x:actor.x+(p.x-f.centerx)*scale*sign,y:actor.y+(p.y-f.centery)*scale};
  }
  function effectFrame(dex,e) {
    const key=e.sourceObject;
    if (!key || !metadataFor(dex)?.objects[key]) return null;
    if (e.sourceFrame!=null) return frame(dex,key,e.sourceFrame);
    const remaining=(e.life??Infinity)-(e.age||0), ending=e.sourceEnd!=null && remaining<=(e.endDuration??.2);
    const start=ending?e.sourceEnd:e.sourceStart??0;
    const age=ending?(e.endDuration??.2)-remaining:e.sourceAge??e.age??0;
    return sequence(dex,key,start,age,ending?false:e.sourceLoop??true);
  }
  function drawEffects(ctx,apiOrDex) {
    const dex=typeof apiOrDex==='number'?apiOrDex:apiOrDex?.dex;
    if (!heroes[dex] || !isReady(dex)) return;
    const runtime=typeof apiOrDex==='object'?apiOrDex:apiFor(dex);
    const states=runtime?.renderStates?.()||[];
    for (const s of states) for (const e of s.effects||[]) {
      if (e.dead || e.age<0) continue;
      if (G.Camera?.sees && !G.Camera.sees(e.x,e.y,Math.max(250,(e.radius||0)*2))) continue;
      const f=effectFrame(dex,e); if (!f) continue;
      const scale=Number.isFinite(e.scale)?e.scale:e.visualBaseRadius?e.radius/e.visualBaseRadius:s.owner?.anim?.scale||1;
      paint(ctx,dex,f,e.x,e.y-(e.lift||0),scale,Math.cos(e.aim||0)<0,e.alpha??1);
    }
    const ice=sheets.get(dex)?.images['freeze_ice.png'];
    if (ice) for (const {enemy,remaining,duration} of runtime?.frozenTargets?.()||[]) {
      if (!enemy || G.Camera?.sees && !G.Camera.sees(enemy.x,enemy.y,100)) continue;
      const size=Math.max(28,Math.min(92,(enemy.r||14)*3.7)),index=remaining>duration-.12?0:1;
      ctx.save();ctx.imageSmoothingEnabled=false;ctx.globalAlpha*=Math.min(.86,remaining*6);
      ctx.drawImage(ice,index*80,0,79,79,enemy.x-size/2,enemy.y-size,size,size);ctx.restore();
    }
  }
  const playSound=(id,owner)=>G.LF2Audio?.play(id,owner,metadataFor(dexFor(owner)));
  const stopSounds=owner=>G.LF2Audio?.stop(owner);
  G.LF2BossArt={load,isReady,draw,pointFor,drawEffects,playSound,stopSounds,frame,sequence,sample,metadataFor,heightFor,
    get metadata(){return Object.fromEntries([...sheets].map(([dex,s])=>[dex,s.metadata]));},
    get images(){return Object.fromEntries([...sheets].map(([dex,s])=>[dex,s.images]));}};
})();
