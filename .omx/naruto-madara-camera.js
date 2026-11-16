/* Frame only the local player's Perfect Susanoo; keep world geometry unchanged. */
(() => {
  'use strict';
  if (G.MadaraFraming) return;
  const camera = G.Camera, follow = camera.follow;
  let owner = null, world = null, epoch = null, adjusted = false, last = null;
  let boundsMetadata = null, boundsHeight = null, authoredBounds = null;

  function bounds(player, height) {
    const metadata = G.MadaraArt?.metadata;
    if (metadata !== boundsMetadata || height !== boundsHeight) {
      boundsMetadata = metadata;
      boundsHeight = height;
      let top = 0, bottom = 0;
      for (const key of ['perfect', 'perfectDirections']) {
        const sheet = metadata?.sheets?.[key];
        if (!sheet?.bodyHeight) continue;
        for (const frame of sheet.frames) {
          top = Math.max(top, frame.anchor[1] * height / sheet.bodyHeight);
          bottom = Math.max(bottom, (frame.rect[3] - frame.anchor[1]) * height / sheet.bodyHeight);
        }
      }
      authoredBounds = top > 0 ? {top:top + 12, bottom:Math.max(70, bottom + 12)} : null;
    }
    if (!authoredBounds) return null;
    return {...authoredBounds, top:Math.max(authoredBounds.top, 64 * (player.anim?.scale || 1) + 12)};
  }

  function viewport(view) {
    const width = view.w * view.scale, height = view.h * view.scale;
    if (!(width > 0 && height > 0 && Number.isFinite(width + height))) return null;
    return {width, height, nativeScale:view.viewportScale(width, height)};
  }

  function restore(view, size, center = null) {
    if (size) {
      view.scale = size.nativeScale;
      view.w = size.width / view.scale;
      view.h = size.height / view.scale;
    }
    if (center) { view.x = center.x; view.y = center.y; }
    owner = world = epoch = null;
    adjusted = false;
    last = null;
  }

  camera.follow = function(tx, ty, dt) {
    const player = G.Game.player, currentEpoch = G.CombatPulse?.epoch;
    const alive = player && !player.dead && player.hp > 0;
    const inRun = ['playing', 'paused', 'levelup'].includes(G.Game.state);
    const eligible = inRun && alive && player.mon?.dex === 30016 && player.moves?.some(m => m.id === 'naruto-madara-susanoo');
    const contextChanged = adjusted && (owner !== player || world !== G.World || epoch !== currentEpoch || !eligible);
    let size;
    if (contextChanged) restore(this, viewport(this), player || {x:tx, y:ty});
    if (adjusted && (G.Game.state === 'paused' || G.Game.state === 'levelup')) return;

    const pose = eligible ? G.NarutoMadara?.guardianPose?.(player) : null;
    const box = pose?.perfect ? bounds(player, pose.height) : null;
    if (!box && !adjusted) return follow.call(this, tx, ty, dt);
    size = viewport(this);
    if (!size || !(dt > 0 && Number.isFinite(dt))) return follow.call(this, tx, ty, dt);

    if (box) {
      owner = player; world = G.World; epoch = currentEpoch; adjusted = true;
    }
    const topPixels = Math.min(112, size.height * .18);
    const bottomPixels = Math.min(112, size.height * .18);
    const fitScale = box ? Math.min(size.nativeScale,
      Math.max(96, size.height - topPixels - bottomPixels) / (box.top + box.bottom)) : size.nativeScale;
    const nextScale = G.U.damp(this.scale, fitScale, 10, dt);
    const appliedScale = Math.abs(nextScale - fitScale) < .0001 ? fitScale : nextScale;

    // Use a stable union of all form frames, never chase an individual blade.
    const halfTargetView = size.height / fitScale / 2;
    const offset = box ? Math.max(0, box.top + topPixels / fitScale - halfTargetView) : 0;
    const result = follow.call(this, tx, ty - offset, dt);
    // Existing size adapters recalculate their scale inside follow(). Apply this
    // character's temporary view afterwards, with matching world dimensions.
    this.scale = appliedScale;
    this.w = size.width / this.scale;
    this.h = size.height / this.scale;
    last = {active:!!box, scale:this.scale, nativeScale:size.nativeScale, targetScale:fitScale,
      offset, top:box?.top || 0, bottom:box?.bottom || 0, width:size.width, height:size.height};
    if (!box && this.scale === size.nativeScale && Math.abs(this.y - ty) < .25) restore(this, size);
    return result;
  };
  G.MadaraFraming = {inspect:() => last ? {...last} : null};
})();
