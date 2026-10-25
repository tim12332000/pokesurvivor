(function (G) {
  'use strict';

  const TAU = Math.PI * 2;
  const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n));
  const progress = e => clamp((e.age || 0) / (e.life || .35), 0, 1);

  function afterimage(ctx, x, y, alpha, direction) {
    ctx.save();
    try {
      ctx.translate(x, y);
      ctx.globalAlpha *= alpha;
      ctx.fillStyle = '#d4c9df';
      ctx.beginPath(); ctx.arc(0, -31, 5, 0, TAU); ctx.fill();
      // Broken coat silhouette reads as displacement, never a second actor.
      for (let i = 0; i < 5; i++) {
        const offset = direction * i * 1.5;
        ctx.fillRect(-5 - i * .6 + offset, -24 + i * 4, 10 + i, 3);
      }
      ctx.strokeStyle = '#d4c9df'; ctx.lineWidth = 1;
      for (let i = 0; i < 3; i++) {
        ctx.beginPath(); ctx.moveTo(-direction * 5, -26 + i * 9);
        ctx.lineTo(-direction * (12 + i * 3), -26 + i * 9); ctx.stroke();
      }
    } finally { ctx.restore(); }
  }

  function action(ctx, f) {
    if (f.kind !== 'soul' || f.phase !== 'grasp' || !f.body || !f.target) return;
    const b = f.body, e = f.target;
    const t = clamp((f.grasp || 0) / .6, 0, 1);
    const h = clamp(e.bodyH || 28, 20, 48);
    const dx = b.x - e.x, dy = b.y - e.y;
    const d = Math.max(1, Math.hypot(dx, dy)), ux = dx / d, uy = dy / d;
    const palmX = e.x + ux * 3, palmY = e.y - h * .8;
    const pull = 4 + (4 + 14 * t) * Math.sin(t * Math.PI * .5);
    const soulX = e.x + ux * pull, soulY = e.y - h * .72 - 3 - 5 * t + uy * pull * .3;
    ctx.save();
    try {
      // A pale head and tapering shoulders separate from the target, not its body.
      const alpha = ctx.globalAlpha;
      const fillAlpha = .18 + .2 * t, edgeAlpha = .6 + .22 * t;
      ctx.fillStyle = '#d4d5e8'; ctx.strokeStyle = '#dbd3eb'; ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(e.x - 3, e.y - h * .16);
      ctx.quadraticCurveTo(e.x - 7 + ux * pull * .35, e.y - h * .55, soulX - 6, soulY + 5);
      ctx.quadraticCurveTo(soulX, soulY + 1, soulX + 6, soulY + 5);
      ctx.quadraticCurveTo(e.x + 7 + ux * pull * .35, e.y - h * .55, e.x + 3, e.y - h * .16);
      ctx.closePath();
      ctx.globalAlpha = alpha * fillAlpha; ctx.fill();
      ctx.globalAlpha = alpha * edgeAlpha; ctx.stroke();
      ctx.beginPath(); ctx.ellipse(soulX, soulY, 4, 5, 0, 0, TAU);
      ctx.globalAlpha = alpha * fillAlpha; ctx.fill();
      ctx.globalAlpha = alpha * edgeAlpha; ctx.stroke();
      ctx.globalAlpha = alpha;
      // Sleeve, wrist and small fingers connect to the head throughout the grasp.
      ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      ctx.strokeStyle = '#161923'; ctx.lineWidth = 7;
      ctx.beginPath(); ctx.moveTo(b.x + ux * -3, b.y - 23);
      ctx.lineTo(palmX - ux * 5, palmY + 2); ctx.stroke();
      ctx.strokeStyle = '#b89383'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(palmX - ux * 5, palmY + 2);
      ctx.lineTo(palmX, palmY); ctx.stroke();
      ctx.strokeStyle = '#e0ba9f'; ctx.lineWidth = 1;
      for (let i = 0; i < 3; i++) {
        ctx.beginPath(); ctx.moveTo(palmX - 2 + i * 2, palmY - 2);
        ctx.lineTo(palmX - 2 + i * 2, palmY + 2); ctx.stroke();
      }
      // Two inward tension strokes replace a persistent glowing tether.
      ctx.globalAlpha *= .35 + .25 * t; ctx.strokeStyle = '#d3c6e1';
      for (let i = 0; i < 2; i++) {
        const x = e.x + ux * (5 + 8 * t), y = e.y - h * .55 + i * 5;
        ctx.beginPath(); ctx.moveTo(x - ux * 4, y + 1);
        ctx.lineTo(x + ux * 3, y - 1); ctx.stroke();
      }
    } finally { ctx.restore(); }
  }

  function effect(ctx, e) {
    if (e.kind !== 'soul' && e.kind !== 'soul-blink') return;
    const t = progress(e);
    if (t >= 1) return;
    if (e.kind === 'soul-blink') {
      const direction = (e.toX ?? e.x) >= e.x ? 1 : -1;
      afterimage(ctx, e.x - direction * t * 7, e.y, .3 * (1 - t), direction);
      afterimage(ctx, e.toX ?? e.x, e.toY ?? e.y, .2 * (1 - t), -direction);
      return;
    }
    ctx.save();
    try {
      ctx.translate(e.x, e.y - 22);
      ctx.globalAlpha *= (1 - t) * .75;
      const dx = (e.body?.x ?? e.x - 1) - e.x;
      const sign = dx >= 0 ? 1 : -1;
      // A single snapping release accompanies the existing one damage event.
      ctx.strokeStyle = '#eee6ed'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(-5 - t * 3, -6 - t * 4);
      ctx.lineTo(4 + t * 3, 4 + t * 4); ctx.stroke();
      ctx.fillStyle = '#cbc8dd';
      for (let i = 0; i < 5; i++) {
        const x = sign * (4 + t * (10 + i * 2));
        const y = (i - 2) * 3 - t * (5 + i);
        ctx.fillRect(Math.round(x), Math.round(y), 2, 2);
      }
    } finally { ctx.restore(); }
  }

  (G.PainSkillVFX ||= {}).soul = { action, effect };
})(G);
