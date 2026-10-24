// Local visual size profiles. These are gameplay presentation, not canonical measurements.
(() => {
  const records = G.Digimon.records;
  const worldScales = [1, 1, 1.3, 1.45, 1.6];
  const previewHeights = [56, 64, 76, 88, 96];
  const previews = new WeakSet();
  const isInitial = record => record.dex === record.baseDex;
  function prepareAnchors(record) {
    if (!record.image.naturalWidth || record.pixel.frame_rects || record.footAnchors) return;
    // Read the source alpha without changing or rewriting the sprite artwork.
    const source = document.createElement('canvas');
    source.width = record.image.naturalWidth; source.height = record.image.naturalHeight;
    const ctx = source.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(record.image, 0, 0);
    const data = ctx.getImageData(0, 0, source.width, source.height).data;
    const pixel = record.pixel;
    record.footAnchors = Array.from({ length: pixel.frame_count }, (_, frame) => {
      for (let y = source.height - 1; y >= 0; y--) {
        for (let x = frame * pixel.cell_width; x < (frame + 1) * pixel.cell_width; x++) {
          if (data[(y * source.width + x) * 4 + 3]) return y + 1;
        }
      }
      return pixel.anchor[1];
    });
  }
  for (const record of records.values()) {
    record.image.addEventListener('load', () => prepareAnchors(record));
    if (record.image.complete) prepareAnchors(record);
  }
  const sizeOf = dex => {
    const record = records.get(dex);
    return record && !isInitial(record) ? worldScales[record.stage] : 1;
  };
  const sprite = G.UI.sprite;
  G.UI.sprite = (canvas, dex, options) => {
    if (records.has(dex)) previews.add(canvas);
    return sprite(canvas, dex, options);
  };
  const spriteCanvas = G.UI.spriteCanvas;
  G.UI.spriteCanvas = (dex, width, height, options) => {
    const canvas = spriteCanvas(dex, width, height, options);
    if (records.has(dex)) previews.add(canvas);
    return canvas;
  };
  const draw = G.Sprites.Animator.prototype.draw;
  G.Sprites.Animator.prototype.draw = function(ctx, x, y, options) {
    const record = records.get(this.dex);
    if (!record) return draw.call(this, ctx, x, y, options);
    const original = this.scale;
    if (previews.has(ctx.canvas)) {
      const meta = G.Sprites.animMeta(this.dex, 'Idle');
      const stage = isInitial(record) ? 0 : record.stage;
      const targetHeight = Math.min(ctx.canvas.height * .86, previewHeights[stage] * ctx.canvas.height / 112);
      this.scale = Math.min(targetHeight / meta.ay, ctx.canvas.width * .9 / meta.w) / G.Sprites.PX;
    } else this.scale *= sizeOf(this.dex);
    ctx.save();
    if (record.footAnchors) {
      const group = [0,1,1,3,2,2,0,0][this.dir];
      const phase = this.cur === 'Walk' ? [0,1,0,2][this.frame % 4] : 0;
      const anchor = record.footAnchors[group * record.pixel.frames_per_direction + phase];
      ctx.translate(0, Math.round((record.pixel.anchor[1] - anchor) * record.pixel.scale * G.Sprites.PX * this.scale));
    }
    try { return draw.call(this, ctx, x, y, options); }
    finally { ctx.restore(); this.scale = original; }
  };
  const bodyHeight = G.Sprites.bodyHeight;
  G.Sprites.bodyHeight = (dex, scale = 1) => bodyHeight(dex, scale) * sizeOf(dex);
  const shadow = G.Sprites.drawShadow;
  G.Sprites.drawShadow = (ctx, dex, x, y, scale = 1) => {
    const record = records.get(dex);
    const minimum = record && !isInitial(record) && record.stage === 1 ? 1.05 : 1;
    return shadow(ctx, dex, x, y, scale * Math.max(minimum, sizeOf(dex)));
  };
  // Keep existing collision radii so larger artwork can traverse the existing map.
  // Camera framing leaves room for the head and the bottom attack controls.
  const follow = G.Camera.follow;
  G.Camera.follow = function(x, y, dt) {
    const canvas = document.getElementById('game');
    const width = canvas.clientWidth, height = canvas.clientHeight;
    const baseScale = this.viewportScale(width,height);
    const player = G.Game.player;
    const inRun = G.Game.state !== 'ui' && records.has(player?.dex);
    this.scale = inRun ? Math.min(baseScale, Math.max(32, height - 152) / player.bodyH) : baseScale;
    this.w = width / this.scale; this.h = height / this.scale;
    if (inRun) {
      const foot = Math.max(height / 2, Math.min(height - 88, 64 + player.bodyH * this.scale));
      y -= (foot - height / 2) / this.scale;
    }
    return follow.call(this, x, y, dt);
  };
  Object.assign(G.Digimon, { worldScales, previewHeights, sizeOf });
})();
