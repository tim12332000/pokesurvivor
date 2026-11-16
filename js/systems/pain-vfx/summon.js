(function (G) {
  'use strict';
  const TAU = Math.PI * 2;
  const clamp = v => Math.max(0, Math.min(1, v));

  // Effects derive exclusively from native action time: pause and cancellation
  // need no independent timers, particles, or cleanup registrations.
  function cloud(ctx, x, y, radius, alpha) {
    ctx.globalAlpha *= alpha;
    ctx.fillStyle = '#cfcbc3';
    ctx.strokeStyle = '#756e68';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.ellipse(x, y, radius, radius * .56, 0, 0, TAU);
    ctx.fill();
    ctx.stroke();
  }

  function ground(ctx, f) {
    if (f.kind !== 'summon') return;
    const age = Math.max(0, f.age || 0);
    const travelled = Math.max(0, f.distance || 0);
    const angle = f.angle || 0;
    const sx = f.x - Math.cos(angle) * travelled;
    const sy = f.y - Math.sin(angle) * travelled;
    const sealFade = 1 - clamp((age - .14) / .26);
    ctx.save();
    if (sealFade > 0) {
      ctx.translate(sx, sy);
      ctx.scale(1, .48);
      ctx.globalAlpha *= sealFade * .72;
      ctx.strokeStyle = '#29232c';
      ctx.lineWidth = 2;
      const radius = 19 + 13 * clamp(age / .18);
      ctx.beginPath();
      ctx.arc(0, 0, radius, 0, TAU);
      ctx.arc(0, 0, radius * .66, 0, TAU);
      ctx.stroke();
      for (let i = 0; i < 8; i++) {
        const a = i * TAU / 8;
        ctx.save();
        ctx.rotate(a);
        ctx.beginPath();
        ctx.moveTo(radius * .42, -2);
        ctx.lineTo(radius + 6, -2);
        ctx.lineTo(radius + 6, 4);
        ctx.stroke();
        ctx.restore();
      }
    }
    ctx.restore();
    if (f.phase !== 'charge') return;
    ctx.save();
    ctx.translate(f.x, f.y);
    ctx.rotate(angle);
    // Short lane edges mark forward movement without filling the hit corridor.
    ctx.strokeStyle = '#d8cbb3';
    ctx.lineWidth = 2;
    ctx.globalAlpha *= .42;
    for (let i = 0; i < 4; i++) {
      const pulse = (age * 8 + i * .25) % 1;
      const back = 12 + pulse * Math.min(78, travelled);
      const side = (i % 2 ? 1 : -1) * (20 + pulse * 9);
      ctx.beginPath();
      ctx.moveTo(-back, side);
      ctx.lineTo(-back - 12, side * 1.06);
      ctx.stroke();
    }
    ctx.restore();
  }

  function action(ctx, f) {
    if (f.kind !== 'summon') return;
    const age = Math.max(0, f.age || 0);
    ctx.save();
    if (f.phase === 'charge') {
      G.PainArt?.draw(ctx, {path:'rhino', x:f.x, y:f.y, height:70,
        state:'move', time:age, facing:Math.cos(f.angle || 0) < 0 ? -1 : 1});
      ctx.translate(f.x, f.y);
      ctx.rotate(f.angle || 0);
      ctx.save();
      ctx.strokeStyle = '#e2d7c1';
      ctx.lineWidth = 2;
      ctx.globalAlpha *= .55;
      for (let i = 0; i < 3; i++) {
        const pulse = ((age - .18) * 7 + i / 3) % 1;
        const back = 32 + pulse * 19;
        const side = (i - 1) * 11;
        ctx.beginPath();
        ctx.moveTo(-back, side);
        ctx.lineTo(-back - 9 - pulse * 5, side);
        ctx.stroke();
      }
      ctx.restore();
      // Bounded local dust puffs stay below the body and out of its silhouette.
      for (let i = 0; i < 6; i++) {
        const p = ((age - .18) * 5 + i / 6) % 1;
        ctx.save();
        cloud(ctx, -12 - p * 44, (i % 2 ? 1 : -1) * (15 + p * 9),
          3 + p * 6, (1 - p) * .5);
        ctx.restore();
      }
    }
    // Smoke opens at the true spawn position, then is left behind the rhino.
    if (age < .34) {
      const distance = f.distance || 0;
      const x = f.x - Math.cos(f.angle || 0) * distance;
      const y = f.y - Math.sin(f.angle || 0) * distance;
      const p = clamp(age / .34);
      for (let i = 0; i < 7; i++) {
        const a = i * TAU / 7;
        ctx.save();
        cloud(ctx, x + Math.cos(a) * (8 + p * 24),
          y - 10 + Math.sin(a) * (5 + p * 13) - p * 7,
          6 + p * 8, Math.sin(p * Math.PI) * .48);
        ctx.restore();
      }
    }
    ctx.restore();
  }

  function effect(ctx, e) {
    if (e.kind !== 'summon-hit' && e.kind !== 'summon-end') return false;
    const p = clamp((e.age || 0) / (e.life || .2));
    ctx.save();
    ctx.translate(e.x, e.y - 9);
    ctx.rotate(e.angle || 0);
    ctx.globalAlpha *= 1 - p;
    if (e.kind === 'summon-hit') {
      ctx.strokeStyle = '#eee0bc';
      ctx.lineWidth = 2;
      for (let i = 0; i < 5; i++) {
        const a = (i - 2) * .46;
        ctx.beginPath();
        ctx.moveTo(Math.cos(a) * 4, Math.sin(a) * 4);
        ctx.lineTo(Math.cos(a) * (12 + p * 16), Math.sin(a) * (12 + p * 16));
        ctx.stroke();
      }
    } else {
      for (let i = 0; i < 5; i++) {
        const a = i * TAU / 5;
        ctx.save();
        cloud(ctx, Math.cos(a) * p * 20, Math.sin(a) * p * 9,
          6 + p * 8, .42);
        ctx.restore();
      }
    }
    ctx.restore();
    return true;
  }

  (G.PainSkillVFX ||= {}).summon = {action, effect, ground};
})(G);
