/* Preta Path: only real interceptions produce inward energy. Presentation only. */
(() => {
  const TAU = Math.PI * 2;
  const clamp = n => Math.max(0, Math.min(1, n));

  function support(ctx, s) {
    const b = s?.bodies?.find(a => a.path === 'preta');
    const owner = s?.owner;
    const learned = owner?.moves?.some(m => (m.id || m.digiMode) === 'naruto-pain-absorb');
    if (!learned || !b || b.dead || b.hp <= 0 || !b.formed ||
        b.protectionRemaining > 0 || !(s.absorbCooldown <= 0) ||
        Math.hypot(b.x - owner.x, b.y - owner.y) > 110) return;
    const facing = Math.cos(b.aim || 0) < 0 ? -1 : 1;
    const pulse = .8 + .2 * Math.sin((s.clock || 0) * 3);
    ctx.save();
    ctx.translate(b.x + facing * 20, b.y - 30);
    // Two small open palm seals, never a body-sized invulnerability bubble.
    ctx.globalAlpha = .42 * pulse;
    ctx.strokeStyle = '#b6aecf';
    ctx.lineWidth = 1.5;
    for (let i = 0; i < 2; i++) {
      ctx.beginPath();
      ctx.arc(0, i ? 5 : -5, 4.5, -.8, 3.8);
      ctx.stroke();
    }
    ctx.restore();
  }

  function effect(ctx, e) {
    const t = clamp((e.age || 0) / (e.life || .3));
    if (t >= 1 || !(e.count > 0)) return;
    const facing = Math.cos(e.angle ?? e.aim ?? 0) < 0 ? -1 : 1;
    const palmX = facing * 20, palmY = -30;
    const fade = 1 - t;
    const points = e.points || [];
    ctx.save();
    ctx.translate(e.x, e.y);
    ctx.lineCap = 'round';
    // Draw only captured contacts; eight strands cap simultaneous-batch cost.
    for (let i = 0; i < Math.min(8, points.length); i++) {
      const p = points[i];
      if (!Number.isFinite(p.x) || !Number.isFinite(p.y)) continue;
      const dx = p.x - e.x - palmX, dy = p.y - e.y - 12 - palmY;
      const length = Math.hypot(dx, dy);
      const bound = Math.min(1, 48 / Math.max(1, length));
      const progress = 1 - Math.pow(1 - t, 2);
      const startX = palmX + dx * bound * (1 - progress);
      const startY = palmY + dy * bound * (1 - progress);
      const curl = (i % 2 ? -1 : 1) * 7 * fade;
      ctx.globalAlpha = .95 * fade;
      ctx.beginPath();
      ctx.moveTo(startX, startY);
      ctx.quadraticCurveTo((startX + palmX) / 2 + curl,
        (startY + palmY) / 2 - curl, palmX, palmY + (i % 2 ? 4 : -4));
      ctx.strokeStyle = '#251b38';
      ctx.lineWidth = 4;
      ctx.stroke();
      ctx.strokeStyle = i % 2 ? '#c8bbeb' : '#f0eaff';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = '#251b38';
      ctx.fillRect(Math.round(startX - 2), Math.round(startY - 2), 5, 5);
      ctx.fillStyle = '#e8dfff';
      ctx.fillRect(Math.round(startX - 1), Math.round(startY - 1), 3, 3);
    }
    // Local contracting seal communicates the whole batch resolving together.
    const strength = Math.min(8, e.count);
    ctx.globalAlpha = .9 * fade;
    ctx.strokeStyle = '#d8c9ff';
    ctx.lineWidth = 1.5 + strength * .14;
    ctx.beginPath();
    ctx.arc(palmX, palmY, 3 + (7 + strength * .4) * fade, .2, TAU - .5);
    ctx.strokeStyle = '#251b38';
    ctx.lineWidth = 4 + strength * .14;
    ctx.stroke();
    ctx.strokeStyle = '#d8c9ff';
    ctx.lineWidth = 1.5 + strength * .14;
    ctx.stroke();
    ctx.globalAlpha = .7 * Math.sin(t * Math.PI);
    ctx.fillStyle = '#f1eaff';
    ctx.fillRect(palmX - 2, palmY - 6, 4, 12);
    ctx.restore();
  }

  (G.PainSkillVFX ||= {}).absorb = { support, effect };
})();
