/* Gaara's sand wave: native pixel canvas effects, driven by simulation time. */
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
  G.NarutoSandVFX = { drawGround, drawAir };
})();
