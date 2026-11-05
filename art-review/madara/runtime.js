/* Original generated Madara sprites. Side views are mirrored, not eight authored directions. */
(() => {
  'use strict';
  const base = new URL('./', document.currentScript.src);
  let metadata, image, white, pending;
  const api = {loaded:false, load, sample, draw, get metadata(){return metadata;}};
  function load() {
    if (pending) return pending;
    pending = (async () => {
      const response = await fetch(new URL('frames.json', base));
      if (!response.ok) throw Error('Madara animation metadata unavailable');
      metadata = await response.json();
      image = new Image(); image.src = new URL(metadata.source, base).href; await image.decode();
      white = document.createElement('canvas'); white.width = image.width; white.height = image.height;
      const ctx = white.getContext('2d'); ctx.drawImage(image, 0, 0);
      ctx.globalCompositeOperation = 'source-in'; ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, white.width, white.height);
      api.loaded = true; return api;
    })().catch(error => { pending = null; throw error; });
    return pending;
  }
  function sample(state='idle', time=0, dir=0, pose=null) {
    if (!metadata) return null;
    const age = Math.max(0, Number(time)||0);
    let index = 0;
    if (state === 'faint' || state === 'death') index = age < .16 ? 14 : 15;
    else if (state === 'hurt') index = age < .12 ? 12 : 13;
    else if (pose || state === 'cast') {
      const kind = pose?.kind || 'basic', t = Math.max(0, pose?.age ?? age);
      if (kind === 'fire') index = t < .12 ? 4 : t < .25 ? 5 : t < .78 ? 6 : 7;
      else if (kind === 'meteor') index = t < .18 ? 4 : t < .42 ? 10 : t < 1.1 ? 10 : 11;
      else if (kind === 'clones') index = t < .14 ? 4 : t < .5 ? 5 : 7;
      else index = t < .10 ? 8 : t < .32 ? 9 : t < .48 ? 11 : 7;
    } else if (state === 'walk' || state === 'move') index = [1,0,2,0][Math.floor(age*9)%4];
    const direction = typeof dir === 'string' ? dir : ['down','right','right','right','up','left','left','left'][((dir||0)%8+8)%8];
    const mirror = pose?.aim != null ? Math.cos(pose.aim) < 0 : direction === 'left';
    return {...metadata.frames[index], index, bodyHeight:metadata.bodyHeight, mirror, source:metadata.source};
  }
  function draw(ctx, actor={}, options={}) {
    const {x=0,y=0,height=64,state='idle',time=0,dir=0,pose=null,flash=false,alpha=1} = options;
    const frame = sample(state,time,dir,pose); if (!frame || !api.loaded) return false;
    const [sx,sy,sw,sh] = frame.rect, k = height/frame.bodyHeight;
    ctx.save(); ctx.translate(Math.round(x),Math.round(y)); ctx.imageSmoothingEnabled = false;
    ctx.globalAlpha *= alpha; if(frame.mirror)ctx.scale(-1,1);
    ctx.drawImage(flash?white:image,sx,sy,sw,sh,-Math.round(frame.anchor[0]*k),-Math.round(frame.anchor[1]*k),Math.round(sw*k),Math.round(sh*k));
    ctx.restore(); return true;
  }
  Object.defineProperty(api,'ready',{get:load});
  G.MadaraArt = api;
})();
