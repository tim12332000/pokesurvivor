/* Original six-path production art. Right-facing animation and explicit left mirror. */
(() => {
  'use strict';
  const base = new URL('./', document.currentScript.src);
  const images = {}, flashes = {};
  let metadata;
  const aliases = { deva: 'tendo', tendō: 'tendo', ashura: 'asura', animalPath: 'animal', humanPath: 'human', hungry: 'preta', hell: 'naraka' };
  function keyFor(actor, options) {
    const key = options.path || actor.path || actor.kind || 'tendo';
    return aliases[key] || key;
  }
  function sample(path, state = 'idle', time = 0) {
    const body = metadata?.bodies[path];
    if (!body) return null;
    const sequence = body.animations[state] || body.animations.idle;
    const step = Math.floor(Math.max(0, Number(time) || 0) * sequence.fps);
    const index = sequence.loop ? step % sequence.frames.length : Math.min(step, sequence.frames.length - 1);
    return { ...body.frames[sequence.frames[index]], bodyHeight: body.bodyHeight, state, index };
  }
  function draw(ctx, actor = {}, options) {
    if (!options) { options = actor; actor = {}; }
    const path = keyFor(actor, options), image = images[path];
    const state = options.state || actor.pose || actor.state || (actor.walking ? 'move' : 'idle');
    const frame = sample(path, state, options.time ?? actor.poseAge ?? actor.age ?? 0);
    if (!image || !frame) return false;
    const [sx, sy, sw, sh] = frame.rect;
    const scale = (options.height ?? 48) / frame.bodyHeight;
    const facing = options.facing ?? actor.facing ?? (Math.cos(actor.aim || 0) < 0 ? -1 : 1);
    ctx.save();
    ctx.translate(options.x ?? actor.x ?? 0, options.y ?? actor.y ?? 0);
    ctx.scale((facing === -1 || facing === 'left' ? -1 : 1) * scale, scale);
    ctx.globalAlpha *= options.alpha ?? 1;
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(options.flash ? flashes[path] : image, sx, sy, sw, sh, -frame.anchor[0], -frame.anchor[1], sw, sh);
    ctx.restore();
    return true;
  }
  function portrait(ctx, options = {}) {
    const path = options.path || 'tendo', frame = sample(path), image = images[path];
    if (!frame || !image) return false;
    const [sx, sy, sw, sh] = frame.rect;
    const w = options.width ?? options.size ?? 48, h = options.height ?? options.size ?? 48;
    const cropHeight = Math.min(sh, frame.bodyHeight * .55), cropWidth = Math.min(sw, cropHeight);
    ctx.save();
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(image, sx + (sw - cropWidth) / 2, sy, cropWidth, cropHeight, options.x || 0, options.y || 0, w, h);
    ctx.restore();
    return true;
  }
  const api = { loaded: false, draw, portrait, sample, get metadata() { return metadata; }, get images() { return images; } };
  api.ready = (async () => {
    const response = await fetch(new URL('pain-frames.json', base));
    if (!response.ok) throw Error('沛恩六道動畫資料載入失敗');
    metadata = await response.json();
    await Promise.all(Object.entries(metadata.bodies).map(async ([path, body]) => {
      const source = new Image(); source.src = new URL(body.source, base).href;
      await source.decode(); images[path] = source;
      const white = document.createElement('canvas'); white.width = source.width; white.height = source.height;
      const ctx = white.getContext('2d'); ctx.drawImage(source, 0, 0); ctx.globalCompositeOperation = 'source-in';
      ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, white.width, white.height); flashes[path] = white;
    }));
    api.loaded = true;
    return api;
  })();
  window.PainArt = api;
  if (window.G) window.G.PainArt = api;
})();
