/* Naraka restoration: presentation only; revive eligibility and HP stay in NarutoPain. */
(() => {
  const clamp = n => Math.max(0, Math.min(1, n));

  function current(s) {
    if (s?.repair) return { ...s.repair, target: s.repair.target };
    const r = s?.playerRevive;
    if (r && r.status !== 'waiting' && Number.isFinite(r.x) && Number.isFinite(r.y)) {
      return { ...r, target: s.owner };
    }
    return null;
  }

  function ground(ctx, f, s) {
    const r = current(s || f);
    if (!r) return;
    const age = Math.max(0, r.age || 0), emerge = clamp(age / .16);
    ctx.save();
    ctx.translate(r.x, r.y);
    ctx.globalAlpha *= .32 * emerge;
    ctx.fillStyle = '#241e2e';
    ctx.beginPath();
    ctx.ellipse(0, 1, 31, 9, 0, 0, Math.PI * 2);
    ctx.fill();
    // Short cracks sit under the summoned head, never marking an attack radius.
    ctx.strokeStyle = '#766781';
    ctx.lineWidth = 2;
    for (let i = 0; i < 6; i++) {
      const side = i % 2 ? -1 : 1, x = side * (14 + i * 4);
      ctx.beginPath();
      ctx.moveTo(x, 2);
      ctx.lineTo(x + side * 6, 6);
      ctx.lineTo(x + side * 12, 5);
      ctx.stroke();
    }
    ctx.restore();
  }

  function support(ctx, s) {
    const r = current(s);
    if (!r || !r.target?.dead) return;
    const age = Math.max(0, r.age || 0), progress = clamp(age / .8);
    const emerge = clamp(age / .16), target = r.target;
    ctx.save();
    // Clip the existing King sprite at ground level as it rises out of the earth.
    ctx.beginPath();
    ctx.rect(r.x - 58, r.y - 100, 116, 102);
    ctx.clip();
    ctx.globalAlpha *= .5 + .5 * emerge;
    // Existing atlas has shut / opening / tongue / shut frames. Sample once,
    // without looping the mouth while waiting for a safe resurrection point.
    const artTime = age >= .8 ? .26 : Math.min(.374, progress * .375);
    G.PainArt?.draw(ctx, { path: 'king', x: r.x, y: r.y + 34 * (1 - emerge),
      height: 88, state: 'special', time: artTime });
    ctx.restore();

    const active = clamp((age - .14) / .16) * (age >= .8 ? .32 : 1);
    if (active <= 0) return;
    ctx.save();
    ctx.translate(target.x, target.y);
    ctx.globalAlpha *= .92 * active;
    // Separate stepped strips close around the actual fallen body. Their
    // upward movement denotes repair in progress, not a resurrected silhouette.
    for (let i = 0; i < 8; i++) {
      const phase = (age * 1.6 + i / 8) % 1;
      const side = i % 2 ? -1 : 1;
      const x = Math.round(side * (10 + (1 - phase) * 11));
      const y = Math.round(-3 - phase * 24);
      // Dark one-pixel backing keeps each repair fragment readable on grass.
      ctx.fillStyle = '#252b2c';
      ctx.fillRect(x - 1, y - 1, 5, 7);
      ctx.fillRect(x - side * 3 - 1, y + 3, 5, 4);
      ctx.fillStyle = i % 3 ? '#c8ded0' : '#f0e5c9';
      ctx.fillRect(x, y, 3, 5);
      ctx.fillRect(x - side * 3, y + 4, 3, 2);
    }
    // Three separated low stitches bind the feet and torso visually without
    // resembling a health bar or a completed resurrection silhouette.
    for (let i = 0; i < 3; i++) {
      const x = -17 + i * 14, y = i === 1 ? -13 : 1;
      ctx.fillStyle = '#252b2c';
      ctx.fillRect(x - 1, y - 1, 8, 4);
      ctx.fillStyle = '#d2dfce';
      ctx.fillRect(x, y, 6, 2);
    }
    ctx.restore();
  }

  function effect(ctx, e) {
    if (e.kind !== 'repair-complete') return;
    const t = clamp((e.age || 0) / (e.life || .45));
    if (t >= 1) return;
    ctx.save();
    ctx.translate(e.x, e.y);
    ctx.globalAlpha *= (1 - t) * .78;
    // This release appears only when gameplay confirms revival; no HP text,
    // full-health symbol, or lingering protective bubble is fabricated here.
    for (let i = 0; i < 10; i++) {
      const a = i * Math.PI * 2 / 10;
      const x = Math.round(Math.cos(a) * (7 + t * 19));
      const y = Math.round(-15 + Math.sin(a) * (10 + t * 18) - t * 9);
      ctx.fillStyle = i % 3 ? '#b6c7bb' : '#eee4cc';
      ctx.fillRect(x, y, 2, i % 2 ? 4 : 2);
    }
    ctx.restore();
  }

  (G.PainSkillVFX ||= {}).repair = { support, effect, ground };
})();
