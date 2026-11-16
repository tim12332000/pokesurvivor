/* Gaara's sand techniques: native pixel canvas effects, driven by simulation time. */
(() => {
  'use strict';
  const G = window.G;
  const COLORS = ['#625c4e', '#79705a', '#aaa28e', '#d4cdbb', '#f0ebdd'];
  const clamp = value => Math.max(0, Math.min(1, value));
  const pixel = value => Math.round(value / 2) * 2;
  // All effect seeds are deterministic integers. Share their exact original
  // values rather than evaluating the same sine thousands of times per frame.
  const grainValues = new Float64Array(4096);
  for (let index = 0; index < grainValues.length; index++) {
    const value = Math.sin(index * 127.1 + 311.7) * 43758.5453;
    grainValues[index] = value - Math.floor(value);
  }
  const grain = index => {
    const cached = grainValues[index];
    if (cached !== undefined) return cached;
    const value = Math.sin(index * 127.1 + 311.7) * 43758.5453;
    return value - Math.floor(value);
  };
  function geometry(f) {
    const flow = Math.max(.01, f.flowDuration || .65);
    const burst = f.burstTime || flow + (f.bindDuration || .5);
    const life = Math.max(burst + .01, f.life || 1.5);
    return {
      front: (f.m.range || 310) * clamp(f.t / flow),
      range: f.m.range || 310,
      width: f.m.width || 240,
      flow,
      burst,
      collapse: clamp((f.t - burst) / (life - burst)),
      alpha: 1 - clamp((f.t - burst) / (life - burst))
    };
  }
  let pointAim = NaN, pointCosine = 1, pointSine = 0;
  function point(f, along, across) {
    const aim = f.aim || 0;
    if (pointAim !== aim) {
      pointAim = aim; pointCosine = Math.cos(aim); pointSine = Math.sin(aim);
    }
    return [pixel(f.x + along * pointCosine - across * pointSine),
      pixel(f.y + along * pointSine + across * pointCosine)];
  }
  function polygon(ctx, points, color) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(pixel(points[0][0]), pixel(points[0][1]));
    for (let index = 1; index < points.length; index++) ctx.lineTo(pixel(points[index][0]), pixel(points[index][1]));
    ctx.closePath();
    ctx.fill();
  }
  function fan(ctx, f, g, offset, breadth, color) {
    const near = g.width * .2 * breadth;
    const far = g.width * (.2 + .3 * g.front / g.range) * breadth;
    polygon(ctx, [point(f, 0, offset - near), point(f, g.front, offset - far),
      point(f, g.front, offset + far), point(f, 0, offset + near)], color);
  }
  const waveMottles = Array.from({ length: 250 }, (_, patch) => {
    const length = 2 + grain(patch + 903) * 5;
    const breadth = 1 + grain(patch + 1004) * 3;
    return {
      along: grain(patch + 702), side: (grain(patch + 829) * 2 - 1) * .98,
      corners: Array.from({ length: 6 }, (_, corner) => {
        const angle = corner * Math.PI / 3;
        const rough = .65 + grain(patch * 11 + corner + 38) * .35;
        return [Math.cos(angle) * length * rough, Math.sin(angle) * breadth * rough];
      })
    };
  });
  function drawTsunamiBed(ctx, f, g) {
    // Overlapping deposits follow the wave, rather than painting its hitbox.
    const press = 1 - Math.pow(1 - g.collapse, 3);
    ctx.save();
    ctx.globalAlpha *= g.alpha;
    for (let ribbon = 0; ribbon < 63; ribbon++) {
      const lane = ribbon % 7, row = Math.floor(ribbon / 7);
      const side = (lane - 3 + (grain(ribbon + 2100) - .5) * .7) / 3.7;
      const center = g.range * (row + .35 + grain(ribbon + 2110) * .45) / 9;
      const length = g.range / 9 * (1.3 + grain(ribbon + 2120) * .8);
      const start = Math.max(0, center - length / 2);
      if (start >= g.front) continue;
      const banks = [[], []], ridge = [];
      for (let step = 0; step <= 10; step++) {
        const u = step / 10;
        const along = start + Math.min(length, Math.max(0, g.front - start) * (1 - grain(ribbon + 2130) * .25)) * u;
        const half = g.width * (.2 + .3 * along / g.range);
        const bend = Math.sin(u * 5 + ribbon * 2.3) * half * .05;
        const across = side * half * (1 - press * .09) + bend;
        const taper = Math.pow(Math.sin(Math.PI * u), .45);
        const breadth = half / 7 * (1.1 + grain(ribbon * 11 + step + 2200) * .6) * taper;
        const lift = (3 + grain(ribbon + 2600) * 5) * taper * (1 - press);
        for (let bank = 0; bank < 2; bank++) {
          const p = point(f, along, across + (bank ? 1 : -1) * breadth);
          banks[bank].push([p[0], p[1] - lift]);
        }
        const p = point(f, along, across);
        ridge.push([p[0], p[1] - lift - 2 * taper * (1 - press)]);
      }
      const outline = banks[0].concat(banks[1].slice().reverse());
      ctx.globalAlpha *= .28;
      polygon(ctx, outline.map(p => [p[0], p[1] + 3 * (1 - press)]), COLORS[1]);
      ctx.globalAlpha /= .28;
      polygon(ctx, outline, COLORS[3]);
      ctx.globalAlpha *= .24;
      polygon(ctx, banks[0].concat(ridge.slice().reverse()), COLORS[4]);
      ctx.globalAlpha /= .24;
    }
    // Sparse grains bridge the deposits without restoring a solid perimeter.
    for (let index = 0; index < 120; index++) {
      const u = grain(index + 2700), side = grain(index + 2900) * 2 - 1;
      const along = g.front * u * (1 - side * side * .2);
      const half = g.width * (.2 + .3 * along / g.range);
      const p = point(f, along, side * half * .94);
      const fall = (1 - press) * (f.t >= g.burst ? 7 : 2);
      ctx.fillStyle = COLORS[index % 4 === 0 ? 4 : 2];
      ctx.fillRect(p[0], pixel(p[1] - fall * grain(index + 3100)), 2, 2);
    }
    ctx.restore();
  }
  function drawGround(ctx, f) {
    const g = geometry(f);
    if (!g.alpha || g.front < 2) return;
    if (f.kind === 'gaara-tsunami') { drawTsunamiBed(ctx, f, g); return; }
    ctx.save();
    ctx.globalAlpha *= g.alpha;
    // Creamy sand stays connected behind the crest, with a noisy scalloped perimeter.
    ctx.globalAlpha *= .12;
    fan(ctx, f, g, 0, 1, COLORS[2]);
    ctx.globalAlpha /= .12;
    const bed = [];
    for (let edge = 0; edge < 2; edge++) {
      for (let step = 0; step <= 26; step++) {
        const along = g.front * (edge ? 1 - step / 26 : step / 26);
        const half = g.width * (.2 + .3 * along / g.range);
        const scallop = 1 + grain(step + edge * 82) * 7;
        bed.push(point(f, along, (edge ? 1 : -1) * Math.max(0, half - scallop)));
      }
    }
    ctx.globalAlpha *= .84;
    polygon(ctx, bed, COLORS[3]);
    ctx.globalAlpha /= .84;
    const travel = f.t * 37 * (1 - g.collapse);
    // Tiny overlapping mottles have no isolated outline or paired stone-like shadow.
    for (let patch = 0; patch < 250; patch++) {
      const mottle = waveMottles[patch];
      const along = (mottle.along * g.front + travel) % g.front;
      ctx.beginPath();
      for (let corner = 0; corner < 6; corner++) {
        const depth = Math.max(0, Math.min(g.front, along + mottle.corners[corner][0]));
        const half = g.width * (.2 + .3 * depth / g.range);
        const across = Math.max(-half, Math.min(half, mottle.side * half + mottle.corners[corner][1]));
        const px = pixel(f.x + depth * pointCosine - across * pointSine);
        const py = pixel(f.y + depth * pointSine + across * pointCosine);
        if (corner) ctx.lineTo(px, py); else ctx.moveTo(px, py);
      }
      const opacity = patch % 4 === 0 ? .32 : .46;
      ctx.globalAlpha *= opacity;
      ctx.fillStyle = COLORS[patch % 5 === 0 ? 4 : 2];
      ctx.closePath(); ctx.fill();
      ctx.globalAlpha /= opacity;
    }
    for (let index = 0; index < 160; index++) {
      const along = (grain(index + 1) * g.front + travel * 1.8) % g.front;
      const half = g.width * (.2 + .3 * along / g.range);
      const p = point(f, along, (grain(index + 113) * 2 - 1) * half);
      ctx.fillStyle = COLORS[index % 6 === 0 ? 4 : index % 7 === 0 ? 1 : 2];
      ctx.fillRect(p[0], p[1], 2, 2);
    }
    if (f.t >= g.burst) {
      // Small pressure creases and descending grains flatten into the same sand bed.
      for (let index = 0; index < 22; index++) {
        const along = g.front * grain(index + 310);
        const half = g.width * (.2 + .3 * along / g.range);
        const p = point(f, along, (grain(index + 414) * 2 - 1) * half * .92);
        const height = (1 - g.collapse) * (2 + grain(index + 510) * 5);
        ctx.fillStyle = COLORS[2];
        ctx.fillRect(p[0], pixel(p[1] - height), 2, Math.max(2, pixel(height)));
        ctx.fillStyle = COLORS[3];
        ctx.fillRect(p[0] - 2, p[1], 4, 2);
      }
    }
    ctx.restore();
  }
  function drawCrest(ctx, f, g) {
    if (f.t >= g.flow + .16 || g.front < 2) return;
    const settle = 1 - clamp((f.t - g.flow) / .16);
    // A connected sand face rolls over a darker trough; all lift stays screen-upright.
    for (let layer = 0; layer < 3; layer++) {
      const bottom = [], lip = [];
      for (let step = 0; step <= 32; step++) {
        const side = step / 16 - 1;
        const depth = Math.max(0, g.front - 17 + (1 - side * side) * 12 - layer * 6);
        const half = g.width * (.2 + .3 * depth / g.range);
        const base = point(f, depth, side * half);
        const fold = Math.sin(step * .63 - f.t * 8) * 3 + Math.sin(step * 1.53) * 2;
        const height = (10 + (1 - side * side) * 17 + fold) * settle * (1 - layer * .22);
        bottom.push([base[0], base[1] + 2]);
        const tip = point(f, Math.min(g.front, depth + 8 + layer * 2), side * half);
        lip.push([tip[0], tip[1] - height]);
      }
      polygon(ctx, bottom.concat(lip.slice().reverse()), COLORS[layer === 0 ? 1 : layer === 1 ? 3 : 2]);
      // Broken highlights keep a continuous curl without forming a row of pillars.
      ctx.strokeStyle = COLORS[layer === 1 ? 4 : 3];
      ctx.lineWidth = layer === 1 ? 4 : 2;
      ctx.beginPath();
      lip.forEach((p, i) => i ? ctx.lineTo(pixel(p[0]), pixel(p[1])) : ctx.moveTo(pixel(p[0]), pixel(p[1])));
      ctx.stroke();
    }
    for (let index = 0; index < 32; index++) {
      const side = grain(index + 44) * 2 - 1;
      const depth = Math.max(0, g.front - grain(index + 82) * 18);
      const half = g.width * (.2 + .3 * depth / g.range);
      const p = point(f, depth, side * half * .98);
      const fall = (index / 32 + f.t * 2) % 1;
      ctx.fillStyle = COLORS[index % 3 === 0 ? 4 : 2];
      ctx.fillRect(p[0], pixel(p[1] - (1 - fall) * 31 * settle), 2, index % 4 === 0 ? 4 : 2);
    }
  }
  function drawWrap(ctx, f, g, enemy, index) {
    if (!enemy || enemy.dead) return;
    if (G.Camera && G.Camera.sees && !G.Camera.sees(enemy.x, enemy.y, 100)) return;
    const dx = enemy.x - f.x, dy = enemy.y - f.y;
    const along = dx * Math.cos(f.aim || 0) + dy * Math.sin(f.aim || 0);
    const arrival = g.flow * clamp(along / g.range);
    const rise = clamp((f.t - arrival) / Math.max(.12, g.burst - arrival));
    if (rise <= 0) return;
    const lift = (enemy.flying && !enemy.boss ? 1 + Math.sin(enemy.bob || 0) * 1.5 : 0) + (enemy.jumpLift || 0);
    const x = pixel(enemy.x), y = pixel(enemy.y - lift);
    const body = Math.max(18, enemy.bodyH || 28);
    const radius = Math.max(8, Math.min(28, (enemy.r || 10) * 1.1));
    const height = body * (enemy.boss ? .45 : .78) * rise * (1 - g.collapse);
    // Short uneven streams build overlapping sand clumps, without complete rope coils.
    for (let clump = 0; clump < 23; clump++) {
      const seed = index * 61 + clump;
      const t = grain(seed + 1810);
      const side = Math.sin(t * 4.1 + (clump % 2 ? 2.2 : -.4) + f.t * 1.7);
      const cx = x + side * radius * (1 - t * .28);
      const cy = y - t * height;
      const width = (3 + grain(seed + 1860) * 5) * rise;
      const thick = (2 + grain(seed + 1903) * 4) * rise;
      polygon(ctx, [[cx - width, cy + 1], [cx - width * .7, cy - thick * .6],
        [cx - width * .2, cy - thick], [cx + width * .7, cy - thick * .55],
        [cx + width, cy + thick * .35], [cx + width * .1, cy + thick * .65]], COLORS[clump % 4 === 0 ? 1 : 2]);
      polygon(ctx, [[cx - width * .8, cy], [cx - width * .2, cy - thick],
        [cx + width * .55, cy - thick * .55], [cx + width * .6, cy + 1]], COLORS[3]);
      if (clump % 6 === 0) {
        ctx.fillStyle = COLORS[4];
        ctx.fillRect(pixel(cx - width * .2), pixel(cy - thick), 2, 2);
      }
    }
    for (let part = 0; part < 14; part++) {
      const phase = (part / 14 + f.t * 1.2) % 1;
      const side = Math.sin(part * 2.4 + f.t * 4);
      const spread = radius * (.8 + g.collapse * .65);
      const fall = f.t >= g.burst ? (1 - g.collapse) * height : phase * height;
      ctx.fillStyle = COLORS[part % 3 + 1];
      ctx.fillRect(pixel(x + side * spread), pixel(y - fall), part % 4 === 0 ? 4 : 2, 2);
      if (g.collapse > 0) {
        ctx.fillStyle = COLORS[2];
        ctx.fillRect(pixel(x + side * spread), y + 2, 4, 2);
      }
    }
  }
  function drawAir(ctx, f) {
    const g = geometry(f);
    if (!g.alpha) return;
    ctx.save();
    ctx.globalAlpha *= g.alpha;
    drawCrest(ctx, f, g);
    const victims = Array.isArray(f.victims) ? f.victims : [];
    for (let index = 0; index < Math.min(32, victims.length); index++) {
      drawWrap(ctx, f, g, victims[index], index);
    }
    ctx.restore();
  }
  function drawBullet(ctx, bullet) {
    if (G.Camera?.sees && !G.Camera.sees(bullet.x, bullet.y, 60)) return;
    const trail = Array.isArray(bullet.trail) ? bullet.trail : [], recent = [];
    // The same porous ribbon as a loose guardian follows the actual curved
    // route. Its leading point stays at the physical bullet, at hand height.
    for (let i = Math.max(0, trail.length - 16); i < trail.length; i++) {
      const p = trail[i];
      if ((p.age || 0) <= .24 && Math.hypot(p.x - bullet.x, p.y - bullet.y) <= 40) recent.push(p);
    }
    const spine = [], count = Math.min(5, recent.length);
    for (let i = 0; i < count; i++) {
      const p = recent[Math.floor(i * (recent.length - 1) / Math.max(1, count - 1))];
      spine.push([p.x, p.y - 18]);
    }
    if (spine.length < 2) {
      const heading = bullet.heading ?? bullet.aim ?? Math.atan2(bullet.vy || 0, bullet.vx || 0);
      spine.unshift([bullet.x - Math.cos(heading) * 24, bullet.y - 18 - Math.sin(heading) * 24]);
    }
    spine.push([bullet.x, bullet.y - 18]);
    // Ten bounded paints per bullet, including eight animated grains; quantity
    // cards reuse the guardian renderer without consuming its group allowance.
    guardRibbon(ctx, { left: 10 }, spine, 4.5, bullet.age || 0, 1, 4);
  }
  function drawSandRelease(ctx, f) {
    if (!['windup', 'release'].includes(f.phase)) return;
    const p = f.owner, side = Math.cos(f.aim || 0) < 0 ? -1 : 1, scale = p.anim?.scale || 1;
    const progress = f.phase === 'windup' ? clamp(f.phaseAge / .12) : 1;
    const source = { x: p.x - side * 10 * scale, y: p.y - 30 * scale };
    const hand = { x: p.x + Math.cos(f.aim || 0) * 12, y: p.y + Math.sin(f.aim || 0) * 12 - 18 };
    ctx.save();
    for (let index = 0; index < 18; index++) {
      const travel = (index / 18 + f.phaseAge * 3) % 1;
      const x = source.x + (hand.x - source.x) * travel;
      const y = source.y + (hand.y - source.y) * travel - Math.sin(travel * Math.PI) * 14 * scale;
      ctx.fillStyle = COLORS[index % 3 + 1];
      ctx.fillRect(pixel(x), pixel(y), 2, 2);
    }
    const size = 2 + pixel(progress * 4);
    ctx.fillStyle = COLORS[0];
    ctx.fillRect(pixel(hand.x - size / 2 - 2), pixel(hand.y - size / 2 - 2), size + 4, size + 4);
    ctx.fillStyle = COLORS[3];
    ctx.fillRect(pixel(hand.x - size / 2), pixel(hand.y - size / 2), size, size);
    ctx.fillStyle = COLORS[4];
    ctx.fillRect(pixel(hand.x - size / 2), pixel(hand.y - size / 2), Math.max(2, size - 2), 2);
    ctx.restore();
  }
  // Shared material, not per-target canvases: bounded to 48 x 72 x 204 RGBA pixels.
  const coffinShellCache = new Map();
  let coffinCanvasAvailable = true;
  function paintCoffinShell(ctx, x, y, half, height) {
      const outline = [];
      for (let side = 0; side < 2; side++) {
        for (let step = 0; step <= 8; step++) {
          const t = side ? 1 - step / 8 : step / 8;
          const bulge = Math.sqrt(Math.max(0, 1 - Math.pow(t * 1.7 - .65, 2)));
          const width = half * bulge * (.75 + grain(step + side * 93) * .25);
          outline.push([x + (side ? 1 : -1) * width,
            y - t * height]);
        }
      }
      polygon(ctx, outline, COLORS[1]);
      for (let clump = 0; clump < 100; clump++) {
        const t = grain(clump + 230);
        const bulge = Math.sqrt(Math.max(0, 1 - Math.pow(t * 1.7 - .65, 2)));
        const side = grain(clump + 431) * 2 - 1;
        const px = pixel(x + side * half * bulge * .84);
        const py = pixel(y - t * height);
        ctx.fillStyle = COLORS[side > .45 ? 2 : clump % 7 === 0 ? 4 : 3];
        ctx.fillRect(px, py, 2 + pixel(grain(clump + 612) * 4), 2 + pixel(grain(clump + 713) * 2));
        if (clump % 6 === 0) {
          ctx.fillStyle = COLORS[2]; ctx.fillRect(px + 2, py + 2, 4, 2);
        }
      }
  }
  function coffinShell(half, height) {
    if (!coffinCanvasAvailable) return null;
    const width = Math.max(2, pixel(half));
    const bodyHeight = Math.max(2, Math.min(192, pixel(height)));
    const key = width + ':' + bodyHeight;
    if (coffinShellCache.has(key)) {
      const cached = coffinShellCache.get(key);
      coffinShellCache.delete(key);
      coffinShellCache.set(key, cached);
      return cached;
    }
    let canvas, material;
    try {
      canvas = typeof OffscreenCanvas === 'function' ? new OffscreenCanvas(1, 1) :
        typeof document !== 'undefined' ? document.createElement('canvas') : null;
      if (!canvas) { coffinCanvasAvailable = false; return null; }
      canvas.width = width * 2 + 12;
      canvas.height = bodyHeight + 12;
      material = canvas.getContext('2d');
      if (!material) { coffinCanvasAvailable = false; return null; }
    } catch (_) { coffinCanvasAvailable = false; return null; }
    paintCoffinShell(material, width + 4, bodyHeight + 4, width, bodyHeight);
    const cached = { canvas, half: width, height: bodyHeight };
    if (coffinShellCache.size >= 48) coffinShellCache.delete(coffinShellCache.keys().next().value);
    coffinShellCache.set(key, cached);
    return cached;
  }
  function drawCoffin(ctx, f) {
    if (!['bind', 'crush', 'recovery'].includes(f.phase) || !f.target || f.target.dead) return;
    const e = f.target;
    if (G.Camera?.sees && !G.Camera.sees(e.x, e.y, 100)) return;
    const lift = (e.flying && !e.boss ? 1 + Math.sin(e.bob || 0) * 1.5 : 0) + (e.jumpLift || 0);
    const x = pixel(e.x), y = pixel(e.y - lift);
    const rise = f.phase === 'bind' ? clamp(f.phaseAge / .32) : 1;
    const crush = f.phase === 'crush' ? clamp(f.phaseAge / .2) : f.phase === 'recovery' ? 1 : 0;
    const fade = f.phase === 'recovery' ? 1 - clamp(f.phaseAge / .22) : 1;
    const half = Math.max(10, Math.min(30, (e.r || 10) * 1.2)) * (1 - crush * .45);
    const settle = f.phase === 'recovery' ? clamp(f.phaseAge / .22) : 0;
    const height = Math.max(24, e.bodyH || 30) * rise * (1 - crush * .25) * (1 - settle);
    ctx.save(); ctx.globalAlpha *= fade;
    // Uneven clumps accumulate into a weighted cocoon, rather than equal ropes.
    const shell = clamp((rise - .35) / .65);
    if (shell > 0) {
      const shellHeight = height * shell;
      const cached = typeof ctx.drawImage === 'function' ? coffinShell(half, shellHeight) : null;
      if (cached) {
        ctx.imageSmoothingEnabled = false;
        // Scale only the shared material; the original foot anchor and phase remain exact.
        const scaleX = half / cached.half, scaleY = shellHeight / cached.height;
        ctx.drawImage(cached.canvas, x - (cached.half + 4) * scaleX,
          y - (cached.height + 4) * scaleY,
          cached.canvas.width * scaleX, cached.canvas.height * scaleY);
      } else paintCoffinShell(ctx, x, y, half, shellHeight);
    }
    // Loose rising streams have gaps, variable thickness and crumbling tips.
    for (let ribbon = 0; ribbon < 3; ribbon++) {
      const reach = clamp(rise * 1.25 - ribbon * .1);
      for (let step = 0; step <= 24; step += 2) {
        const t = step / 24 * reach;
        const angle = ribbon * Math.PI * 2 / 3 + t * Math.PI * 1.4 - (f.t || f.phaseAge) * 2;
        const width = half * (1.05 - t * .4) + Math.sin(t * Math.PI) * 3;
        const px = pixel(x + Math.cos(angle) * width + (grain(step + ribbon * 37) - .5) * 3);
        const py = pixel(y - t * height + Math.sin(angle) * half * .23);
        const size = 2 + pixel(grain(step + ribbon * 73) * 4);
        ctx.fillStyle = COLORS[2]; ctx.fillRect(px, py, size, 3);
        ctx.fillStyle = COLORS[step % 5 === 0 ? 4 : 3];
        ctx.fillRect(px, py - 2, Math.max(2, size - 2), step % 3 === 0 ? 4 : 2);
      }
    }
    // Incoming loose grains become a low heap as the compressed shell crumbles.
    for (let index = 0; index < 30; index += 2) {
      const angle = index * 2.4;
      const travel = (grain(index + 87) + f.phaseAge * 1.8) % 1;
      const spread = f.phase === 'bind' ? half * (1.8 - travel * .85) : half + crush * (5 + grain(index + 34) * 16);
      const arc = f.phase === 'bind' ? Math.sin(travel * Math.PI) * 5 :
        Math.sin(crush * Math.PI) * (4 + grain(index + 18) * 13) * (1 - settle);
      const px = pixel(x + Math.cos(angle) * spread);
      const py = pixel(y + Math.sin(angle) * spread * .3 - arc);
      ctx.fillStyle = COLORS[index % 3 + 1];
      ctx.fillRect(px, py, index % 4 === 0 ? 6 : 4, 2);
      if (index % 4 === 0) {
        ctx.fillStyle = COLORS[4];
        ctx.fillRect(px, py - 2, 2, 2);
      }
    }
    ctx.restore();
  }
  function drawPrison(ctx, field) {
    const radius = field.radius || 90;
    if (G.Camera?.sees && !G.Camera.sees(field.x, field.y, radius + 8)) return;
    const age = field.age ?? field.t ?? 0;
    const duration = field.duration || field.life || 3;
    const fade = clamp(age / .16) * clamp((duration - age) / .3);
    if (!fade) return;
    const x = field.x, y = field.y;
    ctx.save();
    ctx.globalAlpha *= fade;
    // Every grain stays inside the exact ground-space hit circle.
    ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI * 2); ctx.clip();
    for (let row = -radius; row < radius; row += 4) {
      const edgeY = Math.max(Math.abs(row), Math.abs(Math.min(radius, row + 4)));
      const half = Math.floor(Math.sqrt(Math.max(0, radius * radius - edgeY * edgeY)) / 2) * 2;
      if (!half) continue;
      ctx.globalAlpha *= .08;
      ctx.fillStyle = COLORS[2];
      ctx.fillRect(pixel(x) - half, pixel(y + row), half * 2, 4);
      ctx.globalAlpha /= .08;
    }
    // Broken banks roll inward; their outer tips reveal the fixed boundary.
    for (let bank = 0; bank < 22; bank++) {
      const start = bank * Math.PI * 2 / 22 + grain(bank + 55) * .05;
      for (let step = 0; step < 9; step++) {
        const angle = start + step * .023;
        const roll = Math.sin(step / 8 * Math.PI);
        const distance = radius - 2 - roll * (4 + grain(bank + 16) * 10) + Math.sin(age * 3 - step) * 1.5;
        const px = pixel(x + Math.cos(angle) * distance);
        const py = pixel(y + Math.sin(angle) * distance);
        const width = 2 + pixel(roll * (3 + grain(bank + step) * 5));
        ctx.fillStyle = COLORS[1]; ctx.fillRect(px - width / 2, py, width + 2, 3);
        ctx.fillStyle = COLORS[3]; ctx.fillRect(px - width / 2, py - 2, width, 2 + pixel(roll * 2));
        if (step % 3 === 0) { ctx.fillStyle = COLORS[4]; ctx.fillRect(px - 2, py - 2, 2, 2); }
      }
    }
    // Staggered curved streams keep an open center and never resemble a rune.
    for (let stream = 0; stream < 16; stream++) {
      const start = grain(stream + 719) * Math.PI * 2;
      for (let step = 0; step < 12; step++) {
        const progress = (step / 12 + age * .32 + grain(stream + 911)) % 1;
        const distance = radius * (.12 + (1 - progress) * .82);
        const angle = start + progress * .62;
        const px = pixel(x + Math.cos(angle) * distance);
        const py = pixel(y + Math.sin(angle) * distance);
        ctx.globalAlpha *= .65 + (1 - progress) * .25;
        ctx.fillStyle = COLORS[step % 3 === 0 ? 3 : 2];
        ctx.fillRect(px, py, step % 3 === 0 ? 8 : 4, 2);
        if (step % 3 === 0) {
          ctx.fillStyle = COLORS[1]; ctx.fillRect(px + 2, py + 2, 6, 2);
          ctx.fillStyle = COLORS[3]; ctx.fillRect(px - 2, py - 2, 6, 2);
          ctx.fillStyle = COLORS[4]; ctx.fillRect(px, py, 2, 2);
        }
        ctx.globalAlpha /= .65 + (1 - progress) * .25;
      }
    }
    // Small dark depressions follow the damage cadence without a flashing ring.
    const pulse = 1 - ((age / (field.tickInterval || .5)) % 1);
    ctx.globalAlpha *= pulse * .28;
    for (let index = 0; index < 12; index++) {
      const angle = grain(index + 1501) * Math.PI * 2;
      const distance = radius * (.18 + grain(index + 1601) * .55);
      ctx.fillStyle = COLORS[1];
      ctx.fillRect(pixel(x + Math.cos(angle) * distance), pixel(y + Math.sin(angle) * distance), 4, 2);
    }
    ctx.restore();
  }
  function drawShield(ctx, s, layer = 'air') {
    const p = s.owner, reserve = clamp(s.amount / s.capacity);
    // NC3's GUARD reference uses pale flowing sand and a gray-brown edge.
    const sand = COLORS.slice(1);
    ctx.save();
    // Pale sand stays in motion before a hit. Split the orbit around the
    // sprite so the rear stream passes behind it and the near stream in front.
    if (reserve > 0) {
      ctx.save();
      ctx.globalAlpha *= .65 + reserve * .25;
      const time = (s.age || 0) * 1.2;
      for (let stream = 0; stream < 3; stream++) {
        for (let i = 0; i < 22; i++) {
          const t = i / 21;
          const angle = time + stream * Math.PI * 2 / 3 + t * 1.6;
          const near = Math.sin(angle) >= 0;
          if (near ? layer !== 'air' : layer !== 'ground') continue;
          const radius = 25 + Math.sin(angle * 2 + time * .4) * 2;
          const x = p.x + Math.cos(angle) * radius;
          const y = p.y - 15 + Math.sin(angle) * 11 + Math.sin(angle * 2 - time) * 3;
          const thickness = 2 + Math.sin(t * Math.PI) * 3;
          ctx.fillStyle = sand[1];
          ctx.fillRect(pixel(x), pixel(y), 4, thickness + 2);
          ctx.fillStyle = sand[2];
          ctx.fillRect(pixel(x), pixel(y - 1), 4, thickness);
          ctx.fillStyle = sand[3];
          ctx.fillRect(pixel(x), pixel(y - 1), 3, 2);
        }
      }
      // Loose grains keep the separated ribbons from reading as a solid hoop.
      for (let i = 0; i < 12; i++) {
        const angle = time + grain(i + 791) * Math.PI * 2;
        const near = Math.sin(angle) >= 0;
        if (near ? layer !== 'air' : layer !== 'ground') continue;
        const r = 28 + grain(i + 919) * 5;
        ctx.fillStyle = sand[i % 3 === 0 ? 3 : 2];
        ctx.fillRect(pixel(p.x + Math.cos(angle) * r),
          pixel(p.y - 15 + Math.sin(angle) * 12 + Math.sin(angle * 2 - time) * 4), 2, 2);
      }
      ctx.restore();
    }
    const sourceAim = s.flashAim ?? s.hitAim;
    const aim = sourceAim ?? Math.PI / 2;
    // A hit from above builds behind the sprite; frontal guards may cover the
    // lower body, but leave the head readable. This is depth, not a hitbox.
    const rear = Math.sin(aim) < -.25;
    if (!(s.flash > 0) || (rear ? layer !== 'ground' : layer !== 'air')) { ctx.restore(); return; }
    const age = 1 - clamp(s.flash / .2), broken = s.broken || s.amount <= 0;
    const settle = clamp((age - .45) / .55);
    const x = p.x + Math.cos(aim) * 24;
    const y = p.y - 22 + Math.sin(aim) * 12 + settle * settle * 8;
    const frontal = Math.abs(Math.sin(aim)) > .7;
    const width = frontal ? 27 : 15;
    const height = (rear ? 25 : frontal ? 17 : 28) * (1 - settle * .5);
    ctx.globalAlpha *= 1 - settle * .85;
    // An open, hooked crest with a spreading root, not a closed oval shield.
    // Side hits expose its concave interior; front/back hits show a low dune.
    const sideProfile = [[-1.3,1],[-.5,1.05],[.3,.85],[.9,.4],[1,-.2],[.85,-.65],
      [.4,-1.08],[-.15,-1.3],[.05,-.98],[.35,-.6],[.38,-.15],[.12,.2],[-.25,.45],[-.8,.63],[-1.2,.8]];
    const frontProfile = [[-1.2,.9],[-1.05,.4],[-1,-.2],[-.8,-.8],[-.4,-1.15],[-.65,-.55],
      [-.6,-.05],[-.35,.2],[0,.3],[.4,.05],[.65,-.4],[.65,-1.1],[.95,-.7],[1,-.1],
      [.9,.45],[1.2,.9],[.7,1.1],[.1,.9],[-.4,1.1]];
    const side = Math.cos(aim) < 0 ? -1 : 1;
    const surface = (frontal ? frontProfile : sideProfile).map(([u,v]) =>
      [x + u * width * (frontal ? 1 : side), y + v * height]);
    if (sourceAim != null && (!broken || age < .22)) {
      polygon(ctx, surface, sand[0]);
      polygon(ctx, surface.map(([px, py]) => [x + (px - x) * .94, y + (py - y) * .95]), sand[1]);
      polygon(ctx, surface.map(([px, py]) => [x - side + (px - x) * .88, y - 1 + (py - y) * .92]), sand[2]);
      // Long swept streams follow the hooked silhouette instead of striping it.
      ctx.save();
      ctx.beginPath();
      surface.forEach(([px, py], i) => i ? ctx.lineTo(pixel(px), pixel(py)) : ctx.moveTo(pixel(px), pixel(py)));
      ctx.closePath(); ctx.clip();
      for (let ribbon = 0; ribbon < 4; ribbon++) {
        const points = [];
        for (let i = 0; i <= 16; i++) {
          const t = i / 16;
          const sweep = Math.sin(t * Math.PI * .95);
          const px = frontal ? x + (t * 2 - 1) * width
            : x + side * (-1.1 + sweep * (1.65 + ribbon * .1)) * width;
          const py = frontal ? y + height * (.75 - Math.pow(t * 2 - 1, 2) * 1.7) + ribbon * 2
            : y + height * (.95 - t * 2.15) + ribbon * 2 + Math.sin(t * 6 + ribbon) * 1.5;
          points.push([px, py + age * 2]);
        }
        ctx.strokeStyle = sand[ribbon % 2 ? 1 : 3];
        ctx.lineWidth = 2; ctx.beginPath();
        points.forEach(([px, py], i) => i ? ctx.lineTo(pixel(px), pixel(py)) : ctx.moveTo(pixel(px), pixel(py)));
        ctx.stroke();
      }
      for (let i = 0; i < 30; i++) {
        const px = x + (grain(i + 103) * 2 - 1) * width;
        const py = y + (grain(i + 211) * 2 - 1) * height;
        ctx.fillStyle = sand[i % 4 === 0 ? 3 : 1];
        ctx.fillRect(pixel(px), pixel(py), 2, 2);
      }
      ctx.restore();
      // Sand stretches back to the feet as the crest falls. These broken
      // streams keep the guard connected to its supply instead of hand-held.
      for (let i = 0; i < 17; i++) {
        const t = i / 16;
        const px = p.x + (x - p.x) * t + Math.sin(t * 5 + age * 3) * 3;
        const py = p.y + 1 - Math.sin(t * Math.PI) * 5 + (y + height - p.y) * t;
        ctx.fillStyle = sand[i % 4 === 0 ? 3 : 2];
        ctx.fillRect(pixel(px), pixel(py), 2 + (i % 3) * 2, 2);
      }
    }
    // The outward spray settles down. A depleted shield breaks into larger
    // fragments instead of retaining the intact wall beneath the debris.
    const count = broken ? 26 : 13;
    for (let i = 0; i < count; i++) {
      const a = grain(i + 617) * Math.PI * 2;
      const distance = broken ? age * (12 + grain(i + 661) * 24) : age * (5 + grain(i + 661) * 11);
      const px = x + Math.cos(a) * (width * .65 + distance);
      const py = y + Math.sin(a) * height * .7 - age * (8 + grain(i + 709) * 12) + age * age * 35;
      const size = broken && i % 3 === 0 ? 4 : 2;
      ctx.fillStyle = sand[1]; ctx.fillRect(pixel(px), pixel(py), size + 2, size + 2);
      ctx.fillStyle = sand[i % 4 === 0 ? 3 : 2]; ctx.fillRect(pixel(px), pixel(py), size, size);
    }
    ctx.restore();
  }
  function drawArmor(ctx, state) {
    const p = state.owner;
    if (!p || p.dead) return;
    const age = state.age || 0, hits = Math.min(3, Math.max(0, state.hits || 0));
    const body = Math.max(28, p.bodyH || 48), scale = Math.min(1.4, Math.max(.65, p.anim?.scale || 1));
    if (G.Camera?.sees && !G.Camera.sees(p.x, p.y, body)) return;
    const forming = clamp(age / .18), flash = clamp((state.flash || 0) / .2);
    const shoulder = -body * .5 / scale, waist = -body * .29 / scale;
    const supplySide = Math.cos(p.aim || 0) < 0 ? 1 : -1;
    ctx.save();
    ctx.translate(pixel(p.x), pixel(p.y));
    ctx.scale(scale, scale);
    ctx.globalAlpha *= forming * .94;
    // Tiny overlapping clumps create a rough, porous coating, not shoulder
    // plates. The entire upper central column stays clear even on hurt frames.
    for (let i = 0; i < 60; i++) {
      const side = i < 34 ? -1 : 1;
      const seed = i + (side < 0 ? 211 : 401);
      const drift = Math.sin(age * 4 + grain(seed) * 8) * 1.5;
      const t = (grain(seed + 71) + age * .21) % 1;
      const x = side * (9 + grain(seed + 31) * 10) + drift;
      const y = shoulder + 7 + t * Math.max(8, waist - shoulder + 1);
      if (Math.abs(x) < 12 && y < shoulder + 12) continue;
      if (hits > 0 && i % 11 < hits) continue;
      const size = i % 7 === 0 ? 4 : 2;
      ctx.fillStyle = COLORS[1];
      ctx.fillRect(pixel(x), pixel(y + 2), size + 2, 2);
      ctx.fillStyle = COLORS[i % 5 === 0 ? 2 : 3];
      ctx.fillRect(pixel(x), pixel(y), size, 2);
      if (i % 8 === 0) {
        ctx.fillStyle = COLORS[4]; ctx.fillRect(pixel(x), pixel(y), 2, 2);
      }
    }
    // Supply grains move around the outer gourd flank below head height.
    for (let i = 0; i < 15; i++) {
      const t = (i / 15 + age * .7) % 1;
      const x = supplySide * (21 - t * 7) + Math.sin(t * 8) * 2;
      const y = shoulder + 10 + Math.sin(t * Math.PI) * 4 + t * 5;
      ctx.fillStyle = COLORS[i % 4 === 0 ? 1 : 3];
      ctx.fillRect(pixel(x), pixel(y), 2, 2);
    }
    // Each hit opens a dark interruption and drops grains from that patch.
    for (let hit = 0; hit < hits; hit++) {
      const side = hit % 2 ? 1 : -1;
      const x = side * (14 + hit), y = shoulder + 10 + hit * 3;
      ctx.fillStyle = COLORS[0];
      ctx.fillRect(pixel(x), pixel(y), 2, 4);
      ctx.fillRect(pixel(x + side * 2), pixel(y + 4), 2, 2);
      for (let i = 0; i < 7; i++) {
        const t = (age * 1.5 + i / 7 + hit * .23) % 1;
        const px = x + side * (2 + t * (4 + flash * 5)) + Math.sin(i * 4) * 2;
        const py = y + 4 + t * t * 22;
        ctx.fillStyle = COLORS[1]; ctx.fillRect(pixel(px), pixel(py + 2), 4, 2);
        ctx.fillStyle = COLORS[3]; ctx.fillRect(pixel(px), pixel(py), 2, 2);
      }
    }
    ctx.restore();
  }
  function drawArmorBurst(ctx, state) {
    const radius = state.radius || 110, age = state.age || 0;
    const progress = clamp(age / (state.life || state.duration || .4));
    if (progress >= 1 || (G.Camera?.sees && !G.Camera.sees(state.x, state.y, radius + 4))) return;
    ctx.save();
    ctx.translate(pixel(state.x), pixel(state.y));
    // Every tuft is contained by the same circle used by the damage test.
    ctx.beginPath(); ctx.arc(0, 0, radius, 0, Math.PI * 2); ctx.clip();
    ctx.globalAlpha *= 1 - progress * progress;
    // Irregular low sand banks reveal the full footprint without a solid disk.
    for (let i = 0; i < 110; i++) {
      const angle = grain(i + 1201) * Math.PI * 2;
      const r = radius * Math.sqrt(grain(i + 1241));
      if (r < 25) continue;
      const x = Math.cos(angle) * r, y = Math.sin(angle) * r;
      if (Math.abs(x) < 18 && y < -18) continue;
      ctx.fillStyle = COLORS[i % 4 === 0 ? 1 : 2];
      ctx.fillRect(pixel(x), pixel(y), i % 4 === 0 ? 4 : 2, 2);
    }
    // Short, grainy rolls break into individual 2-6px clumps. Unequal velocity
    // and gravity replace the former sharp pale sheets and regular ring.
    for (let i = 0; i < 24; i++) {
      const angle = grain(i + 1331) * Math.PI * 2;
      const c = Math.cos(angle), sn = Math.sin(angle);
      const speed = .7 + grain(i + 1371) * .7;
      const travel = clamp(progress * 2.4 * speed);
      const reach = 16 + (radius - 23) * travel;
      const width = 5 + grain(i + 1401) * 8;
      for (let j = 0; j < 9; j++) {
        const fragment = i * 9 + j;
        const spread = (grain(fragment + 1451) - .5) * width * 2;
        const r = Math.min(radius - 3, reach + (grain(fragment + 1501) - .5) * 24);
        const lift = Math.sin(progress * Math.PI) * (5 + grain(fragment + 1541) * 21);
        const x = c * r - sn * spread;
        const y = sn * r + c * spread - lift + progress * progress * 12;
        if (Math.abs(x) < 18 && y < -18) continue;
        const size = j % 4 === 0 && progress < .5 ? 4 : 2;
        ctx.fillStyle = COLORS[1]; ctx.fillRect(pixel(x - 2), pixel(y + 2), size + 2, 2);
        ctx.fillStyle = COLORS[j % 5 === 0 ? 2 : 3]; ctx.fillRect(pixel(x), pixel(y), size, 2);
        if (size === 4) {
          ctx.fillStyle = COLORS[2]; ctx.fillRect(pixel(x + 2), pixel(y - 2), 2, 2);
        }
      }
    }
    ctx.restore();
  }
  // A single paint allowance covers pooled bodies, loose fronts, trails and
  // simultaneous contacts. All animation is sampled from simulation state.
  const GUARD_PAINT_LIMIT = 200;
  function guardRect(ctx, budget, x, y, width, height, color, alpha = 1) {
    if (budget.left <= 0 || alpha <= .01) return;
    budget.left--;
    const previous = ctx.globalAlpha;
    ctx.globalAlpha *= alpha;
    ctx.fillStyle = color;
    ctx.fillRect(pixel(x), pixel(y), Math.max(2, pixel(width)), Math.max(2, pixel(height)));
    ctx.globalAlpha = previous;
  }
  function guardPolygon(ctx, budget, points, color, alpha = 1) {
    if (budget.left <= 0 || alpha <= .01) return;
    budget.left--;
    const previous = ctx.globalAlpha;
    ctx.globalAlpha *= alpha;
    polygon(ctx, points, color);
    ctx.globalAlpha = previous;
  }
  // Low segment ribbons have one open, tapered end, unequal edges and a sand
  // ridge. They do not use strokes, circular outlines or per-grain images.
  function guardRibbon(ctx, budget, spine, width, phase, alpha, grains) {
    if (alpha <= .01 || spine.length < 2) return;
    const frames = spine.map((p, i) => {
      const before = spine[Math.max(0, i - 1)], after = spine[Math.min(spine.length - 1, i + 1)];
      const dx = after[0] - before[0], dy = after[1] - before[1], length = Math.hypot(dx, dy) || 1;
      const t = i / (spine.length - 1);
      return { x: p[0], y: p[1], nx: -dy / length, ny: dx / length,
        w: width * (.16 + Math.sin(t * Math.PI * .82) * .84) *
          (.85 + Math.sin(phase * 2.3 + i * 1.7) * .15) };
    });
    const pooled = grains >= 8;
    for (let layer = 0; layer < 2; layer++) {
      const scale = pooled ? [1, .43][layer] : [1, .65][layer];
      const offset = layer ? -.2 : 0;
      const points = [];
      for (let edge = 0; edge < 2; edge++) for (let i = 0; i < frames.length; i++) {
        const f = frames[edge ? frames.length - 1 - i : i];
        const side = (edge ? -1 : 1) * scale + offset;
        points.push([f.x + f.nx * f.w * side, f.y + f.ny * f.w * side]);
      }
      guardPolygon(ctx, budget, points, COLORS[layer ? 3 : 2], alpha * (pooled ? .52 : layer ? .65 : .4));
    }
    if (pooled) {
      // Short, unequal sheets leave porous gaps; moving grains carry the mass.
      // A continuous bright ridge would make these loose folds read as blades.
      for (let i = 0; i < 8; i++) {
        const t = (i / 8 + phase * .31) % 1;
        const at = t * (frames.length - 1), first = Math.floor(at), next = Math.min(frames.length - 1, first + 1);
        const f = frames[first], h = frames[next], u = at - first;
        const side = (grain(i + 2631) - .5) * f.w * 1.6;
        const x = f.x + (h.x - f.x) * u + f.nx * side;
        const y = f.y + (h.y - f.y) * u + f.ny * side;
        const dx = -f.ny, dy = f.nx, length = 2 + grain(i + 2591) * 5;
        guardPolygon(ctx, budget, [[x - dx * length, y - dy * length],
          [x + f.nx * 2, y + f.ny * 2], [x + dx * length, y + dy * length],
          [x - f.nx * 1.5, y - f.ny * 1.5]], COLORS[i % 3 === 0 ? 2 : 3], alpha * .9);
      }
    }
    // Shared sparse grain streaks move along the spine rather than orbiting it.
    const grainCount = pooled ? 16 : grains >= 4 ? grains + 4 : grains;
    for (let i = 0; i < grainCount; i++) {
      const t = (i / grainCount + phase * .46) % 1;
      const at = t * (frames.length - 1), first = Math.floor(at), next = Math.min(frames.length - 1, first + 1);
      const f = frames[first], h = frames[next], u = at - first;
      const across = (grain(i + 2551) - .5) * f.w * (pooled ? 3.4 : grains >= 4 ? 2.8 : 1.5);
      guardRect(ctx, budget, f.x + (h.x - f.x) * u + f.nx * across,
        f.y + (h.y - f.y) * u + f.ny * across, i % 3 === 0 ? 4 : 2, 2,
        COLORS[i % 5 === 0 ? 4 : i % 3 === 0 ? 2 : 3], alpha * .85);
    }
  }
  function guardContact(ctx, state, budget) {
    const contact = state.contact;
    if (!contact || contact.age >= .3) return;
    const t = clamp(contact.age / .3), wrap = clamp(t / .35);
    // Only true collision records produce the two short closing sand folds.
    for (let side = -1; side <= 1; side += 2) {
      const points = [];
      for (let i = 0; i < 5; i++) {
        const angle = -.8 + i * .55 + wrap * .5;
        const radius = 10 - wrap * 5 + Math.max(0, t - .35) * 15;
        points.push([contact.x + Math.cos(angle) * radius * side,
          contact.y - 18 + Math.sin(angle) * radius + t * t * 9]);
      }
      guardRibbon(ctx, budget, points, 2.5 * (1 - t), t, 1 - t, 2);
    }
  }
  function guardFront(ctx, state, budget, merged = 0) {
    if (!state.owner || state.owner.dead) return;
    const age = (state.flowPhase === undefined ? state.age || 0 : state.flowPhase) + (state.index || 0) * .73;
    const fullness = state.ready === undefined ? clamp((state.charges || 0) / Math.max(1, state.capacity || 1)) :
      state.ready ? 1 : state.phase === 'recharge' ? clamp(state.rechargeProgress || 0) : 0;
    const size = state.ready ? 1 : state.phase === 'recharge' ? .2 + fullness * .3 : .62;
    const alpha = 1 - merged;
    const x = state.x, y = state.y - 18;
    if (alpha > .01) {
      const trail = Array.isArray(state.trail) ? state.trail : [];
      const spine = [];
      // Spread five samples across the whole recent route, rather than taking
      // five adjacent .01-second points that collapse into an invisible dot.
      const validTrail = trail.filter(p => (p.age || 0) <= .4 && Math.hypot(p.x - x, p.y - state.y) <= 40);
      for (let i = 0; i < Math.min(5, validTrail.length); i++) {
        const p = validTrail[Math.floor(i * (validTrail.length - 1) / Math.max(1, Math.min(5, validTrail.length) - 1))];
        spine.push([p.x, p.y - 18]);
      }
      if (spine.length < 2) {
        const heading = state.heading || 0;
        spine.length = 0;
        for (let i = 0; i < 5; i++) {
          const t = i / 4, along = (t - 1) * 24 * size;
          const across = Math.sin(t * Math.PI * 1.3 + age * 1.4) * 3 * size * (1 - t);
          spine.push([x + Math.cos(heading) * along - Math.sin(heading) * across,
            y + Math.sin(heading) * along + Math.cos(heading) * across]);
        }
      } else spine.push([x, y]);
      guardRect(ctx, budget, x - 6 * size, state.y + 2, 12 * size, 2, COLORS[0], .1 * alpha);
      guardRibbon(ctx, budget, spine, 5.5 * size, age, alpha, state.ready ? 4 : 2);
    }
    guardContact(ctx, state, budget);
  }
  function drawGuard(ctx, state) {
    if (!state || (G.Camera?.sees && !G.Camera.sees(state.x, state.y, 80))) return;
    guardFront(ctx, state, { left: GUARD_PAINT_LIMIT });
  }
  function drawGuardGroup(ctx, group) {
    if (!group || !group.owner || group.owner.dead || !Array.isArray(group.guardians)) return;
    const budget = { left: GUARD_PAINT_LIMIT }, merged = new Float64Array(group.guardians.length);
    const pools = Array.isArray(group.flowGroups) ? group.flowGroups : [];
    for (let poolIndex = 0; poolIndex < Math.min(3, pools.length); poolIndex++) {
      const pool = pools[poolIndex];
      if (!pool || pool.active === false || !Array.isArray(pool.members)) continue;
      let weight = 0, x = 0, y = 0;
      const close = [];
      for (const index of pool.members) {
        const s = group.guardians[index], blend = clamp(s?.flowBlend || 0);
        if (!s || !s.ready || s.phase === 'pursue' || s.flowGroupId !== pool.id || blend < .01 ||
          Math.hypot(s.x - pool.x, s.y - pool.y) > 40) continue;
        close.push(index); weight += blend; x += s.x * blend; y += s.y * blend;
      }
      if (weight < .01) continue;
      x /= weight; y /= weight;
      if (G.Camera?.sees && !G.Camera.sees(x, y, 90)) continue;
      for (const index of close) merged[index] = clamp(group.guardians[index].flowBlend || 0);
      const phase = pool.phase || 0, heading = pool.heading || 0;
      const length = 32 + Math.min(24, Math.sqrt(weight) * 9), width = Math.min(6.5, 3 + Math.sqrt(weight));
      const spine = [];
      for (let i = 0; i < 7; i++) {
        const t = i / 6, along = (t - .5) * length;
        const across = Math.sin(t * Math.PI * 1.65 + phase * .7) * (5 + Math.sqrt(weight));
        spine.push([x + Math.cos(heading) * along - Math.sin(heading) * across,
          y - 18 + Math.sin(heading) * along + Math.cos(heading) * across]);
      }
      guardRect(ctx, budget, x - length * .3, y + 3, length * .6, 2, COLORS[0], .1);
      guardRibbon(ctx, budget, spine, width, phase, clamp(weight), 8);
    }
    for (let i = 0; i < group.guardians.length; i++) {
      const s = group.guardians[i];
      if (s && (!G.Camera?.sees || G.Camera.sees(s.x, s.y, 80))) guardFront(ctx, s, budget, merged[i]);
    }
  }
  G.NarutoSandVFX = { drawGround, drawAir, drawBullet, drawSandRelease, drawCoffin, drawShield, drawPrison, drawArmor, drawArmorBurst, drawGuard, drawGuardGroup };
})();
