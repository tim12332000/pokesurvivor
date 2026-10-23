/* Reviewed, lab-only actor crops. World coordinates always identify the feet. */
(() => {
  'use strict';
  const base = new URL('./', document.currentScript.src);
  const assets = new Map();
  const flashes = new Map();
  let pending, ready=false;

  function load() {
    if (pending) return pending;
    pending = (async () => {
      const response = await fetch(new URL('animation-assets.json', base), { cache: 'no-cache' });
      if (!response.ok) throw new Error(`Animation crop metadata: ${response.status}`);
      const metadata = await response.json();
      const images = new Map();
      const decoded = await Promise.all(Object.entries(metadata).map(async ([key, spec]) => {
        if (!images.has(spec.source)) {
          const image = new Image();image.src = new URL(spec.source, base).href;
          images.set(spec.source, image.decode().then(() => image));
        }
        const image = await images.get(spec.source);
        return [key, {...spec, image}];
      }));
      decoded.forEach(([key, asset]) => assets.set(key, asset));
      ready=true;
      return window.AnimationAssets;
    })().catch(error => { pending = null; throw error; });
    return pending;
  }

  function flashImage(key, index, asset, frame) {
    const id = `${key}:${index}`;
    if (!flashes.has(id)) {
      const [x, y, width, height] = frame.rect;
      const canvas = document.createElement('canvas');
      canvas.dataset.source=asset.image.src;
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext('2d');
      context.drawImage(asset.image, x, y, width, height, 0, 0, width, height);
      context.globalCompositeOperation = 'source-in';
      context.fillStyle = '#fff';
      context.fillRect(0, 0, width, height);
      flashes.set(id, canvas);
    }
    return flashes.get(id);
  }

  function draw(context, key, index, x, y, options = {}) {
    const asset = assets.get(key), frame = asset?.frames[index];
    if (!frame) return false;
    const [sx, sy, width, height] = frame.rect;
    const [ax, ay] = frame.anchor;
    const scale = (64 / asset.bodyHeight) * (options.scale ?? 1);
    context.save();
    context.translate(x, y);
    if (options.rotation) context.rotate(options.rotation);
    context.scale((!!options.mirror !== !!frame.mirror ? -1 : 1) * scale, scale);
    context.imageSmoothingEnabled = false;
    context.globalAlpha *= options.alpha ?? 1;
    if (options.flash) {
      context.drawImage(flashImage(key, index, asset, frame), -ax, -ay);
    } else {
      context.drawImage(asset.image, sx, sy, width, height, -ax, -ay, width, height);
    }
    context.restore();
    return true;
  }

  window.AnimationAssets = Object.freeze({
    load,
    get: key => assets.get(key),
    draw,
    get ready() { return ready; },
    get keys() { return [...assets.keys()]; }
  });
})();
