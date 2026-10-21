/* Gaara's sand techniques: native pixel canvas effects, driven by simulation time. */
(() => {
  'use strict';
  const G = window.G;
  const COLORS = ['#4d3014', '#91622b', '#c79a53', '#edd395', '#fff0ca'];
  const clamp = value => Math.max(0, Math.min(1, value));
  const pixel = value => Math.round(value / 2) * 2;
  const grain = index => {
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
  function point(f, along, across) {
    const cosine = Math.cos(f.aim || 0), sine = Math.sin(f.aim || 0);
    return [pixel(f.x + along * cosine - across * sine),
      pixel(f.y + along * sine + across * cosine)];
  }
  function polygon(ctx, points, color) {
    ctx.fillStyle = color;
    ctx.beginPath();
    points.forEach((p, index) => index ? ctx.lineTo(pixel(p[0]), pixel(p[1])) : ctx.moveTo(pixel(p[0]), pixel(p[1])));
    ctx.closePath();
    ctx.fill();
  }
  function fan(ctx, f, g, offset, breadth, color) {
    const near = g.width * .2 * breadth;
    const far = g.width * (.2 + .3 * g.front / g.range) * breadth;
    polygon(ctx, [point(f, 0, offset - near), point(f, g.front, offset - far),
      point(f, g.front, offset + far), point(f, 0, offset + near)], color);
  }
  function drawGround(ctx, f) {
    const g = geometry(f);
    if (!g.alpha || g.front < 2) return;
    ctx.save();
    ctx.globalAlpha *= g.alpha;
    // The full widening footprint remains visible beneath the enemies during binding.
    ctx.globalAlpha *= .65;
    fan(ctx, f, g, 0, 1, COLORS[0]);
    fan(ctx, f, g, 0, .94, COLORS[1]);
    fan(ctx, f, g, 0, .82, COLORS[2]);
    ctx.globalAlpha /= .65;
    const travel = (f.t * 108) % 32;
    for (let ribbon = 0; ribbon < 9; ribbon++) {
      const side = (ribbon / 8 - .5) * .88;
      const points = [];
      for (let step = 0; step <= 8; step++) {
        const along = g.front * step / 8;
        const half = g.width * (.2 + .3 * along / g.range);
        const ripple = Math.sin(step * 1.7 + ribbon + f.t * 8) * 4;
        points.push(point(f, along, side * half * 2 + ripple));
      }
      ctx.strokeStyle = COLORS[ribbon % 3 === 0 ? 3 : 1];
      ctx.lineWidth = 2;
      ctx.setLineDash([10 + ribbon % 3 * 6, 13 + ribbon % 4 * 3]);
      ctx.lineDashOffset = -travel;
      ctx.beginPath();
      points.forEach((p, index) => index ? ctx.lineTo(...p) : ctx.moveTo(...p));
      ctx.stroke();
    }
    ctx.setLineDash([]);
    for (let index = 0; index < 210; index++) {
      const along = (grain(index + 1) * g.front + travel) % g.front;
      const half = g.width * (.2 + .3 * along / g.range);
      const p = point(f, along, (grain(index + 113) * 2 - 1) * half * .92);
      ctx.fillStyle = COLORS[index % 5 === 0 ? 4 : index % 3 + 1];
      ctx.fillRect(p[0], p[1], index % 4 === 0 ? 4 : 2, 2);
    }
    if (f.t >= g.burst) {
      // The whole footprint sinks together when the caster presses down.
      const sinking = Math.sin(Math.min(1, g.collapse * 2) * Math.PI / 2);
      ctx.globalAlpha *= .6;
      fan(ctx, f, g, 0, .9 - sinking * .12, COLORS[0]);
      ctx.globalAlpha /= .6;
      // Compression fissures follow the same area, rather than an unrelated circular blast.
      ctx.strokeStyle = COLORS[0];
      ctx.lineWidth = 2;
      for (let crack = 0; crack < 9; crack++) {
        const along = g.range * (.15 + grain(crack + 50) * .8);
        const across = (grain(crack + 73) - .5) * g.width * .7;
        ctx.beginPath();
        for (let step = 0; step < 5; step++) {
          const p = point(f, along + step * 8, across + ((step % 2) * 2 - 1) * 5);
          if (!step) ctx.moveTo(...p); else ctx.lineTo(...p);
        }
        ctx.stroke();
      }
      for (let index = 0; index < 36; index++) {
        const along = g.range * grain(index + 310);
        const half = g.width * (.2 + .3 * along / g.range);
        const p = point(f, along, (grain(index + 414) * 2 - 1) * half);
        const rise = Math.sin(g.collapse * Math.PI) * (8 + grain(index + 510) * 22);
        ctx.fillStyle = COLORS[index % 2 + 2];
        ctx.fillRect(p[0], pixel(p[1] - rise), 4 + pixel(g.collapse * 6), 2);
      }
    }
    ctx.restore();
  }
  function drawCrest(ctx, f, g) {
    if (f.t >= g.flow + .16) return;
    const settle = 1 - clamp((f.t - g.flow) / .16);
    const half = g.width * (.2 + .3 * g.front / g.range);
    // Screen-upright blocks give the moving front height for every cast direction.
    for (let index = 0; index < 48; index++) {
      const across = (index / 47 * 2 - 1) * half;
      const curl = Math.sin(index / 47 * Math.PI) * 15 + Math.sin(index * .55 + f.t * 9) * 5;
      const p = point(f, g.front - 4 + grain(index + 12) * 8 + curl, across);
      const height = pixel((12 + grain(index + 33) * 18) * settle);
      const width = Math.max(4, pixel(half * 2 / 48 + 2));
      ctx.fillStyle = COLORS[0];
      ctx.fillRect(p[0] - 2, p[1] - height, width + 2, height + 2);
      ctx.fillStyle = COLORS[2];
      ctx.fillRect(p[0], p[1] - height, width, height);
      ctx.fillStyle = COLORS[3];
      ctx.fillRect(p[0], p[1] - height, width, 4);
      ctx.fillStyle = COLORS[1];
      ctx.fillRect(p[0] + 2, p[1] - height + 8, Math.max(2, width - 2), 4);
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
    // Animator.draw uses actual feet; G.LIFT would incorrectly float the whole cocoon.
    const footX = pixel(enemy.x), footY = pixel(enemy.y - lift);
    const body = Math.max(18, enemy.bodyH || 28);
    const radius = Math.max(8, Math.min(28, (enemy.r || 10) * 1.1));
    const height = pixel(body * (enemy.boss ? .45 : .78) * rise * (1 - g.collapse));
    if (height >= 2) {
      for (let row = 0; row < height; row += 4) {
        const fraction = row / Math.max(4, height);
        const half = pixel(radius * (.95 - fraction * .28));
        const seam = ((Math.floor(row / 4) + index) % 3 - 1) * 2;
        ctx.fillStyle = COLORS[0];
        ctx.fillRect(footX - half - 2, footY - row - 4, half * 2 + 4, 4);
        ctx.fillStyle = COLORS[1];
        ctx.fillRect(footX - half, footY - row - 4, half * 2, 4);
        ctx.fillStyle = COLORS[2];
        ctx.fillRect(footX - half + 2, footY - row - 4, Math.max(2, half * 2 - 6), 2);
        ctx.fillStyle = COLORS[3];
        ctx.fillRect(footX - half + 2 + seam, footY - row - 4, 4, 2);
        ctx.fillStyle = COLORS[0];
        ctx.fillRect(footX + seam, footY - row - 4, 2, 2);
      }
    }
    if (f.t >= g.burst) {
      for (let part = 0; part < 12; part++) {
        const angle = part * Math.PI * 2 / 12 + grain(index + 28);
        const spread = 4 + g.collapse * (18 + grain(part + index * 17) * 24);
        const arc = Math.sin(g.collapse * Math.PI) * (8 + grain(part + 19) * 16);
        ctx.fillStyle = COLORS[(part % 3) + 1];
        ctx.fillRect(pixel(footX + Math.cos(angle) * spread),
          pixel(footY + Math.sin(angle) * spread * .4 - arc), 4, 2);
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
    if (G.Camera?.sees && !G.Camera.sees(bullet.x, bullet.y, 40)) return;
    // Collision travels at ground level; the visible grains fly at hand height.
    bullet = { ...bullet, y: bullet.y - 18 };
    const aim = bullet.aim ?? Math.atan2(bullet.vy || 0, bullet.vx || 0);
    const cosine = Math.cos(aim), sine = Math.sin(aim);
    ctx.save();
    // Discrete grains and a compact pointed body read as a projectile, not a wave.
    for (let index = 0; index < 5; index++) {
      const back = 7 + index * 4;
      const wobble = (grain(index + Math.floor((bullet.age || 0) * 30)) - .5) * 5;
      ctx.globalAlpha = .7 - index * .12;
      ctx.fillStyle = COLORS[index % 2 + 1];
      ctx.fillRect(pixel(bullet.x - cosine * back - sine * wobble),
        pixel(bullet.y - sine * back + cosine * wobble), 2, 2);
    }
    ctx.globalAlpha = 1;
    polygon(ctx, [[bullet.x + cosine * 8, bullet.y + sine * 8],
      [bullet.x - cosine * 5 - sine * 5, bullet.y - sine * 5 + cosine * 5],
      [bullet.x - cosine * 7, bullet.y - sine * 7],
      [bullet.x - cosine * 5 + sine * 5, bullet.y - sine * 5 - cosine * 5]], COLORS[0]);
    ctx.fillStyle = COLORS[2];
    ctx.fillRect(pixel(bullet.x - 4), pixel(bullet.y - 3), 8, 6);
    ctx.fillStyle = COLORS[3];
    ctx.fillRect(pixel(bullet.x - 2), pixel(bullet.y - 3), 4, 2);
    ctx.restore();
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
    ctx.fillStyle = COLORS[2];
    ctx.fillRect(pixel(hand.x - size / 2), pixel(hand.y - size / 2), size, size);
    ctx.fillStyle = COLORS[3];
    ctx.fillRect(pixel(hand.x - size / 2), pixel(hand.y - size / 2), Math.max(2, size - 2), 2);
    ctx.restore();
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
    const height = Math.max(24, e.bodyH || 30) * rise * (1 - crush * .25);
    ctx.save(); ctx.globalAlpha *= fade;
    for (let row = 0; row < height; row += 4) {
      const taper = Math.sin(row / Math.max(1, height) * Math.PI) * 3;
      const width = pixel(half + taper);
      ctx.fillStyle = COLORS[0];
      ctx.fillRect(x - width - 2, y - row - 4, width * 2 + 4, 4);
      ctx.fillStyle = COLORS[1];
      ctx.fillRect(x - width, y - row - 4, width * 2, 4);
      ctx.fillStyle = COLORS[2];
      ctx.fillRect(x - width + 2, y - row - 4, Math.max(2, width * 2 - 6), 2);
      ctx.fillStyle = COLORS[3];
      ctx.fillRect(x - width + 2, y - row - 4, 4, 2);
    }
    for (let index = 0; index < 16; index++) {
      const angle = index * Math.PI * 2 / 16;
      const spread = f.phase === 'bind' ? half * (1.5 - rise * .4) : half + crush * 24;
      const arc = f.phase === 'bind' ? rise * height * .4 : Math.sin(crush * Math.PI) * 16;
      ctx.fillStyle = COLORS[index % 3 + 1];
      ctx.fillRect(pixel(x + Math.cos(angle) * spread), pixel(y + Math.sin(angle) * spread * .4 - arc), 4, 2);
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
    // Ground-space circle matches the hit test in both axes. Horizontal pixel
    // strips keep its edge crisp without turning the field into a raised wave.
    for (let row = -radius; row < radius; row += 4) {
      const edgeY = Math.max(Math.abs(row), Math.abs(Math.min(radius, row + 4)));
      const half = Math.floor(Math.sqrt(Math.max(0, radius * radius - edgeY * edgeY)) / 2) * 2;
      if (!half) continue;
      ctx.globalAlpha = fade * .44;
      ctx.fillStyle = COLORS[1];
      ctx.fillRect(pixel(x) - half, pixel(y + row), half * 2, 4);
      ctx.globalAlpha = fade * .7;
      ctx.fillStyle = COLORS[2];
      ctx.fillRect(pixel(x) - half, pixel(y + row), Math.min(4, half), 4);
      ctx.fillRect(pixel(x) + half - Math.min(4, half), pixel(y + row), Math.min(4, half), 4);
    }
    // Broken inward streams communicate persistent trapping, while the center
    // stays open enough to read enemy feet and overlapping damage numbers.
    ctx.globalAlpha = fade * .6;
    for (let index = 0; index < 52; index++) {
      const angle = grain(index + 719) * Math.PI * 2;
      const progress = (grain(index + 911) + age * .28) % 1;
      const distance = radius * (.16 + (1 - progress) * .76);
      const px = pixel(x + Math.cos(angle) * distance);
      const py = pixel(y + Math.sin(angle) * distance);
      ctx.fillStyle = COLORS[index % 4 === 0 ? 3 : 2];
      ctx.fillRect(px - 2, py - 1, 4, 2);
      if (index % 3 === 0) {
        ctx.fillStyle = COLORS[0];
        ctx.fillRect(pixel(px + Math.cos(angle) * 4), pixel(py + Math.sin(angle) * 4), 2, 2);
      }
    }
    // A subdued center pulse follows the half-second damage cadence.
    const pulse = 1 - ((age / (field.tickInterval || .5)) % 1);
    ctx.globalAlpha = fade * pulse * .35;
    for (let index = 0; index < 12; index++) {
      const angle = index * Math.PI * 2 / 12;
      const distance = radius * (.12 + pulse * .12);
      ctx.fillStyle = COLORS[3];
      ctx.fillRect(pixel(x + Math.cos(angle) * distance), pixel(y + Math.sin(angle) * distance), 4, 2);
    }
    ctx.restore();
  }
  function drawShield(ctx, s, layer = 'air') {
    const p = s.owner, reserve = clamp(s.amount / s.capacity);
    // NC3's GUARD reference uses pale flowing sand and a gray-brown edge.
    const sand = ['#79705a', '#aaa28e', '#d4cdbb', '#f0ebdd'];
    ctx.save();
    // Capacity already lives in the HUD. A few loose grains show readiness
    // without adding another bar or an opaque shell around the character.
    if (layer === 'ground' && reserve > 0) {
      ctx.globalAlpha *= .35 + reserve * .3;
      for (let i = 0; i < 10; i++) {
        const t = ((s.age || 0) * .35 + grain(i + 883)) % 1;
        const angle = grain(i + 791) * Math.PI * 2 + t * .6;
        const r = 13 + grain(i + 919) * 7;
        ctx.fillStyle = sand[i % 3 === 0 ? 3 : 2];
        ctx.fillRect(pixel(p.x + Math.cos(angle) * r), pixel(p.y + Math.sin(angle) * r * .4 - t * 4), 2, 2);
      }
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
  G.NarutoSandVFX = { drawGround, drawAir, drawBullet, drawSandRelease, drawCoffin, drawShield, drawPrison };
})();
