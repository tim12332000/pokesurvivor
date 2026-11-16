/* Moon impact accents only: NarutoPain owns the moon, simulation and damage front. */
(() => {
  const TAU = Math.PI * 2;
  const visual = f => G.NarutoPain?.planetVisual?.(f);

  function action(ctx, f) {
    const v = visual(f);
    if (!v || v.phase !== 'fall') return;
    const scale = v.scale || 1;
    const t = Math.max(0, Math.min(1, (f.age - 1.15) / .35));
    ctx.save();
    ctx.translate(f.x, f.y - v.height);
    ctx.strokeStyle = '#c9bfa5';
    ctx.lineWidth = 2 * scale;
    ctx.globalAlpha *= .16 + t * .26;
    // Outside the intact silhouette: acceleration streaks never split the moon.
    for (let i = 0; i < 8; i++) {
      const side = i % 2 ? 1 : -1;
      const x = side * (v.shell + (9 + Math.floor(i / 2) * 9) * scale);
      const y = -v.shell * .2 + (i % 4) * 12 * scale;
      ctx.beginPath();
      ctx.moveTo(Math.round(x), Math.round(y));
      ctx.lineTo(Math.round(x), Math.round(y - (10 + t * t * 38) * scale));
      ctx.stroke();
    }
    ctx.restore();
  }

  function ground(ctx, f) {
    const v = visual(f);
    if (!v || v.phase !== 'fall') return;
    const t = Math.max(0, Math.min(1, (f.age - 1.15) / .35));
    ctx.save();
    ctx.translate(f.x, f.y);
    ctx.globalAlpha *= t * t * .22;
    ctx.fillStyle = '#302d27';
    ctx.beginPath();
    ctx.ellipse(0, 0, v.shell * (1 + t * .18), v.shell * .34, 0, 0, TAU);
    ctx.fill();
    ctx.restore();
  }

  function effect(ctx, e) {
    const v = visual(e);
    if (!v || e.kind !== 'collapse' || v.release >= 1) return;
    const scale = v.scale || 1;
    const t = v.release, fade = 1 - t;
    ctx.save();
    ctx.translate(e.x, e.y);
    // Broken terrain rides the exact damaging front, with dust strictly behind it.
    for (let i = 0; i < 28; i++) {
      const a = i * TAU / 28 + (i % 3) * .035;
      const front = v.waveRadius;
      const inner = Math.max(0, front - (9 + (i % 4) * 5) * scale);
      ctx.globalAlpha = fade * (i % 2 ? .44 : .6);
      ctx.strokeStyle = i % 2 ? '#847761' : '#d0c3a2';
      ctx.lineWidth = (i % 3 ? 2 : 3) * scale;
      ctx.beginPath();
      ctx.moveTo(Math.round(Math.cos(a - .012) * inner), Math.round(Math.sin(a - .012) * inner));
      ctx.lineTo(Math.round(Math.cos(a) * front), Math.round(Math.sin(a) * front));
      ctx.stroke();
      const d = Math.max(0, front - (16 + (i % 3) * 8) * scale);
      const lift = Math.sin(t * Math.PI) * (5 + i % 4) * scale;
      ctx.globalAlpha = fade * .35;
      ctx.fillStyle = '#b2a48a';
      ctx.fillRect(Math.round(Math.cos(a) * d), Math.round(Math.sin(a) * d - lift), (3 + i % 3) * scale, (2 + i % 2) * scale);
    }
    // Short contact dust stays near the impact rather than hiding the large wave.
    ctx.globalAlpha = Math.max(0, 1 - t * 3) * .3;
    ctx.strokeStyle = '#d2c3a2';
    ctx.lineWidth = 3 * scale;
    for (let i = 0; i < 8; i++) {
      const a = i * TAU / 8;
      ctx.beginPath();
      ctx.arc(0, 0, Math.min(v.waveRadius, (18 + t * 130) * scale), a, a + .3);
      ctx.stroke();
    }
    ctx.restore();
  }

  (G.PainSkillVFX ||= {}).planet = { action, ground, effect };
})();
