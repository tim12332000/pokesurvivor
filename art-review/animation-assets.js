/* Reviewed, lab-only actor crops. World coordinates always identify the feet. */
(() => {
  'use strict';
  const base = new URL('./', document.currentScript.src);
  const assets = new Map();
  const flashes = new Map();
  const images = new Map(), loadingImages = new Map();
  const heroes = {30001:'naruto',30002:'sasuke',30006:'lee',30007:'gaara',30009:'tenten'};
  let pending, metadataPending, metadataReady=false, ready=false;

  function loadMetadata() {
    if(metadataPending)return metadataPending;
    metadataPending=(async()=>{
      const response = await fetch(new URL('animation-assets.json', base), { cache: 'no-cache' });
      if (!response.ok) throw new Error(`Animation crop metadata: ${response.status}`);
      const metadata = await response.json();
      for(const [key,spec] of Object.entries(metadata))assets.set(key,{...spec,image:null});
      metadataReady=true;
      return window.AnimationAssets;
    })().catch(error=>{metadataPending=null;throw error;});
    return metadataPending;
  }
  function loadImage(source) {
    if(images.has(source))return Promise.resolve(images.get(source));
    if(loadingImages.has(source))return loadingImages.get(source);
    const promise=(async()=>{
      const image=new Image();image.src=new URL(source,base).href;await image.decode();
      images.set(source,image);
      for(const asset of assets.values())if(asset.source===source)asset.image=image;
      ready=[...assets.values()].every(asset=>!!asset.image);
      return image;
    })().finally(()=>loadingImages.delete(source));
    loadingImages.set(source,promise);return promise;
  }
  function heroKeys(dex) {
    const hero=heroes[dex];
    if(!hero)return [];
    return [...assets.keys()].filter(key=>key.startsWith(hero+'-'));
  }
  function heroReady(dex) {
    const keys=heroKeys(dex);
    return metadataReady&&(!heroes[dex]||keys.length>0&&keys.every(key=>!!assets.get(key).image));
  }
  async function loadHero(dex) {
    await loadMetadata();
    await Promise.all([...new Set(heroKeys(dex).map(key=>assets.get(key).source))].map(loadImage));
    return window.AnimationAssets;
  }
  function load() {
    if(pending)return pending;
    pending=(async()=>{
      await loadMetadata();
      await Promise.all([...new Set([...assets.values()].map(asset=>asset.source))].map(loadImage));
      return window.AnimationAssets;
    })().catch(error=>{pending=null;throw error;});
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
    if (!frame || !asset.image) return false;
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
    loadMetadata,
    loadHero,
    heroReady,
    get: key => assets.get(key),
    draw,
    get ready() { return ready; },
    get keys() { return [...assets.keys()]; }
  });
})();
