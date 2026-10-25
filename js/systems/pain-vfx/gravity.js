/* Universal Pull / Almighty Push: presentation only; hit timing lives in NarutoPain. */
(() => {
  const TAU = Math.PI * 2;
  const clamp = n => Math.max(0, Math.min(1, n));
  const radius = 150;

  function ground(ctx, f) {
    if (!f.owner) return;
    ctx.save();
    ctx.translate(f.owner.x, f.owner.y);
    ctx.globalAlpha = .32;
    ctx.strokeStyle = '#b9a9c6';
    ctx.lineWidth = 1;
    // Sparse perimeter ticks expose the real radial hit area without a filled disc.
    for (let i = 0; i < 12; i++) {
      const a = i * TAU / 12;
      ctx.beginPath();
      ctx.arc(0, 0, radius, a, a + .11);
      ctx.stroke();
    }
    ctx.restore();
  }

  function action(ctx, f) {
    if (f.phase !== 'pull' || !f.owner || !f.target) return;
    const age = Math.max(0, f.age || 0);
    const dx = f.target.x - f.owner.x, dy = f.target.y - f.owner.y;
    const distance = Math.min(240, Math.hypot(dx, dy));
    if (distance < 4) return;
    const progress = clamp(age / .35);
    ctx.save();
    ctx.translate(f.owner.x, f.owner.y - 15);
    ctx.rotate(Math.atan2(dy, dx));
    ctx.lineWidth = 2;
    // Short moving dashes converge on the caster; there is deliberately no tether beam.
    for (let i = 0; i < 9; i++) {
      const travel = (i / 9 + progress * 1.65) % 1;
      const x = distance * (1 - travel);
      const side = ((i % 3) - 1) * (9 + x * .055);
      const strong = i % 3 === 0;
      ctx.globalAlpha = Math.max(.4, (.25 + .48 * Math.sin(travel * Math.PI)) * (1 - progress * .25));
      ctx.beginPath();
      ctx.moveTo(Math.round(x + 12), Math.round(side * 1.12));
      ctx.lineTo(Math.round(x + 5), Math.round(side));
      ctx.lineTo(Math.round(x), Math.round(side * .85));
      if (strong) {
        const tipY = Math.round(side * .85);
        ctx.moveTo(Math.round(x + 4), tipY - 3);
        ctx.lineTo(Math.round(x), tipY);
        ctx.lineTo(Math.round(x + 4), tipY + 3);
        ctx.strokeStyle = '#34323b';
        ctx.lineWidth = 3;
        ctx.stroke();
      }
      ctx.strokeStyle = strong ? '#e0d9e2' : '#b7b1bf';
      ctx.lineWidth = strong ? 1.5 : 2;
      ctx.stroke();
    }
    ctx.globalAlpha = .5;
    ctx.strokeStyle = '#c5b2d4';
    ctx.beginPath();
    ctx.arc(7, 0, 10 - progress * 4, -.9, .9);
    ctx.stroke();
    ctx.restore();
  }

  function effect(ctx, e) {
    const t = clamp((e.age || 0) / (e.life || .3));
    if (t >= 1) return;
    const fade = 1 - t;
    ctx.save();
    ctx.translate(e.x, e.y);
    // Damage already hit the whole radius at age zero. Keep this rim at 150;
    // expanding debris is an aftermath, never a delayed travelling damage front.
    ctx.globalAlpha = .68 * fade;
    ctx.strokeStyle = '#e2dce6';
    ctx.lineWidth = 1 + 3 * fade;
    ctx.beginPath();
    ctx.arc(0, 0, radius, 0, TAU);
    ctx.stroke();
    for (let i = 0; i < 16; i++) {
      const a = i * TAU / 16 + .06 * (i % 3);
      const d = 32 + (i % 4) * 23 + t * (15 + (i % 3) * 8);
      ctx.globalAlpha = fade * (i % 2 ? .43 : .62);
      ctx.strokeStyle = i % 2 ? '#b4aaa0' : '#d6d0dc';
      ctx.lineWidth = i % 3 === 0 ? 3 : 2;
      ctx.beginPath();
      ctx.moveTo(Math.round(Math.cos(a) * d), Math.round(Math.sin(a) * d));
      ctx.lineTo(Math.round(Math.cos(a) * Math.min(radius, d + 12)), Math.round(Math.sin(a) * Math.min(radius, d + 12)));
      ctx.stroke();
      if (i % 2 === 0) {
        const dust = 108 + t * 29;
        ctx.fillStyle = '#978d7b';
        ctx.fillRect(Math.round(Math.cos(a) * dust), Math.round(Math.sin(a) * dust - Math.sin(t * Math.PI) * 5), 3, 3);
      }
    }
    ctx.restore();
  }

  (G.PainSkillVFX ||= {}).gravity = { action, effect, ground };
})();
