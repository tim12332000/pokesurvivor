(function (G) {
  'use strict';

  const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n));

  // Receivers remain opaque physical stakes; the short grey wake is displaced air.
  function shot(ctx, p) {
    ctx.save();
    try {
      ctx.translate(p.x, p.y - 12);
      ctx.rotate(p.angle || 0);
      const wake = clamp(p.distance || 0, 0, 24);
      ctx.globalAlpha *= .28;
      ctx.fillStyle = '#a8a4a3';
      ctx.fillRect(-12 - wake, -3, wake, 1);
      ctx.fillRect(-8 - wake * .65, 3, wake * .65, 1);
      ctx.globalAlpha /= .28;
      ctx.fillStyle = '#07090e';
      ctx.beginPath();
      ctx.moveTo(-13, -2); ctx.lineTo(8, -2); ctx.lineTo(14, 0);
      ctx.lineTo(8, 2); ctx.lineTo(-13, 2); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#747783';
      ctx.fillRect(-11, -2, 17, 1);
      ctx.fillStyle = '#292b35';
      ctx.fillRect(-11, 1, 18, 1);
      ctx.fillStyle = '#a4a3ad';
      ctx.fillRect(-9, -2, 2, 1);
    } finally { ctx.restore(); }
  }

  function effect(ctx, e) {
    if (e.kind !== 'rod-hit' && e.kind !== 'rod-launch') return;
    const t = clamp((e.age || 0) / (e.life || .18), 0, 1);
    if (t >= 1) return;
    ctx.save();
    try {
      ctx.translate(e.x, e.y - 12);
      ctx.rotate(e.angle || 0);
      ctx.globalAlpha *= 1 - t;
      if (e.kind === 'rod-launch') {
        // Two tiny pressure ticks frame the hand, never a muzzle flame or laser.
        ctx.strokeStyle = '#b1a9b4'; ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(3 + t * 8, -6); ctx.lineTo(9 + t * 10, -3);
        ctx.moveTo(3 + t * 8, 6); ctx.lineTo(9 + t * 10, 3);
        ctx.stroke();
        return;
      }
      ctx.strokeStyle = '#ded6c5'; ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(-3 - t * 3, -7 - t * 5); ctx.lineTo(3 + t * 3, 7 + t * 5);
      ctx.moveTo(-3 - t * 3, 7 + t * 5); ctx.lineTo(3 + t * 3, -7 - t * 5);
      ctx.stroke();
      // Fixed six slivers: bounded even when the number card produces forty rods.
      for (let i = 0; i < 6; i++) {
        const a = (i - 2.5) * .61;
        const d = 3 + t * (10 + i % 3 * 3);
        ctx.save();
        ctx.translate(Math.cos(a) * d, Math.sin(a) * d + t * t * 5);
        ctx.rotate(a);
        ctx.fillStyle = i % 2 ? '#292833' : '#999083';
        ctx.fillRect(-2, -1, 3 + i % 2, 2);
        ctx.restore();
      }
    } finally { ctx.restore(); }
  }

  (G.PainSkillVFX ||= {}).basic = { shot, effect };
})(G);
