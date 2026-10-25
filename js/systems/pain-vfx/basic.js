(function (G) {
  'use strict';

  const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n));

  function fallingRod(ctx, length) {
    ctx.fillStyle = '#07090e';
    ctx.beginPath();
    ctx.moveTo(-2, -length); ctx.lineTo(2, -length);
    ctx.lineTo(2, -6); ctx.lineTo(0, 0); ctx.lineTo(-2, -6);
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#747783';
    ctx.fillRect(-2, -length + 2, 1, length - 10);
    ctx.fillStyle = '#292b35';
    ctx.fillRect(1, -length + 2, 1, length - 10);
    ctx.fillStyle = '#a4a3ad';
    ctx.fillRect(-2, -length + 6, 1, 3);
  }

  function ground(ctx, p) {
    if (p.phase !== 'fall') return;
    const approach = 1 - clamp((p.lift || 0) / 180, 0, 1);
    ctx.save();
    try {
      ctx.translate(p.x, p.y);
      ctx.globalAlpha *= .2 + approach * .3;
      ctx.fillStyle = '#080a11';
      ctx.beginPath(); ctx.ellipse(0, 0, 5 + approach * 3, 3, 0, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = '#b6a89b'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.ellipse(0, 0, 9, 5, 0, 0, Math.PI * 2); ctx.stroke();
      ctx.fillStyle = '#ded6c5';
      ctx.fillRect(-12, 0, 3, 1); ctx.fillRect(10, 0, 3, 1);
    } finally { ctx.restore(); }
  }

  // Receivers remain opaque physical stakes; the short grey wake is displaced air.
  function shot(ctx, p) {
    ctx.save();
    try {
      if (p.phase === 'fall') {
        ctx.translate(p.x, p.y - (p.lift || 0));
        const progress = 1 - clamp((p.lift || 0) / 180, 0, 1);
        ctx.globalAlpha *= .35;
        ctx.fillStyle = '#b1a9b4';
        ctx.fillRect(-6, -53 - progress * 17, 1, 10 + progress * 16);
        ctx.fillRect(5, -43 - progress * 12, 1, 8 + progress * 13);
        ctx.globalAlpha /= .35;
        fallingRod(ctx, 46);
        return;
      }
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
      if (e.phase === 'fall') {
        ctx.translate(e.x, e.y);
        ctx.globalAlpha *= 1 - t;
        if (e.kind === 'rod-launch') {
          ctx.translate(0, -(e.lift || 180));
          ctx.fillStyle = '#b1a9b4';
          ctx.fillRect(-6, -48 - t * 8, 1, 8);
          ctx.fillRect(5, -36 - t * 8, 1, 7);
          return;
        }
        // A short planted receiver marks the actual impact, with dust at its foot.
        fallingRod(ctx, 34);
        ctx.strokeStyle = '#49423c'; ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(-2, 1); ctx.lineTo(-8 - t * 3, 4); ctx.lineTo(-12 - t * 3, 3);
        ctx.moveTo(2, 1); ctx.lineTo(7 + t * 3, 3); ctx.lineTo(10 + t * 3, 1);
        ctx.moveTo(0, 2); ctx.lineTo(1, 6 + t * 2);
        ctx.stroke();
        for (let i = 0; i < 6; i++) {
          const a = i * Math.PI / 3;
          const d = 4 + t * (9 + i % 3 * 3);
          ctx.fillStyle = i % 2 ? '#706354' : '#b2a18c';
          ctx.fillRect(Math.round(Math.cos(a) * d) - 2,
            Math.round(Math.sin(a) * d * .45 - Math.sin(t * Math.PI) * (3 + i % 2 * 3)), 3, 2);
        }
        return;
      }
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

  (G.PainSkillVFX ||= {}).basic = { ground, shot, effect };
})(G);
