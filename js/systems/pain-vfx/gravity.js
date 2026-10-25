/* Pull gathers smoothly; the full-radius flash marks the instantaneous native hit. */
(() => {
  const TAU = Math.PI * 2;
  const clamp = n => Math.max(0, Math.min(1, n));
  function ground(ctx, f) {
    if (!f.owner) return;
    const radius = f.m?.radius || 300, progress = clamp((f.age || 0) / .35);
    const tension = Math.sin(progress * Math.PI);
    ctx.save();ctx.translate(f.owner.x, f.owner.y);
    ctx.strokeStyle = '#b9a9c6';ctx.lineWidth = 1;
    const rings = f.phase === 'pull' ? [radius, f.m?.triggerRadius || 400] : [radius];
    for (const reach of rings) {
      ctx.globalAlpha = (reach === radius ? .25 : .16) * (.65 + .35 * tension);
      for (let i = 0; i < 12; i++) {
        const a = i * TAU / 12;
        ctx.beginPath();ctx.arc(0, 0, reach, a, a + .13);ctx.stroke();
      }
    }
    // Small ground arcs mark gathering distance without obscuring targets.
    ctx.globalAlpha = .12 + .15 * tension;
    for (let i = 0; i < 4; i++) {
      const a = i * TAU / 4 + progress * .12;
      ctx.beginPath();ctx.arc(0, 0, f.m?.pullRadius ?? 100, a, a + .27);ctx.stroke();
    }
    ctx.restore();
  }
  function action(ctx, f) {
    if (f.phase !== 'pull' || !f.owner) return;
    const progress = clamp((f.age || 0) / .35),reach = f.m?.triggerRadius || 400;
    const gather = f.m?.pullRadius ?? 100,pulls = f.pulls || [];
    for (let i = 0; i < pulls.length; i++) {
      const e = pulls[i].target;
      if (!e || e.dead || !(e.hp > 0) || e.flying || e.jumpLift > 0 || e.jumpT > 0) continue;
      const dx = e.x - f.owner.x,dy = e.y - f.owner.y,distance = Math.hypot(dx, dy);
      if (distance <= gather || distance > reach || !G.World.projectilePathClear(f.owner.x, f.owner.y, e.x, e.y)) continue;
      inwardTrail(ctx, f.owner, dx, dy, distance, progress, i);
    }
    // Pressure collects at the palm, disappearing on the native release frame.
    const tension = progress*progress,facing = Math.cos(f.owner.aim || 0) < 0 ? -1 : 1;
    const height = G.NarutoPain?.visualHeight('tendo', f.owner) || 80;
    ctx.save();ctx.translate(f.owner.x + facing * 15, f.owner.y - height * .48);
    ctx.globalAlpha = .55 * tension;ctx.strokeStyle = '#cdb8df';ctx.lineWidth = 1.5;
    ctx.beginPath();ctx.arc(0, 0, 10 - 3 * progress, -.8, 2.5);ctx.stroke();
    ctx.globalAlpha = .22 * tension;ctx.fillStyle = '#ded1e7';ctx.fillRect(-2, -2, 4, 4);ctx.restore();
  }
  function inwardTrail(ctx, owner, dx, dy, distance, progress, seed) {
    const height = G.NarutoPain?.visualHeight('tendo', owner) || 80;
    ctx.save();ctx.translate(owner.x, owner.y - height * .35);ctx.rotate(Math.atan2(dy, dx));ctx.lineCap = 'round';
    for (let i = 0; i < 2; i++) {
      const travel = (progress*progress * 1.65 + i * .5 + (seed % 5) * .07) % 1;
      const fade = Math.pow(Math.sin(travel * Math.PI), 2) * Math.min(1,progress/.12) * (.3+.7*progress);
      const x = 24 + (distance + 20) * (1 - travel),bend = (i ? -1 : 1) * (5 + (seed % 3) * 3);
      const y = bend * Math.sin(travel * Math.PI),length = 15 + 32*progress + 8 * Math.sin(travel * Math.PI);
      ctx.globalAlpha = .72 * fade;ctx.strokeStyle = '#d9ccdf';ctx.lineWidth = 1.5;
      ctx.beginPath();ctx.moveTo(x + length, y + bend * .3);
      ctx.quadraticCurveTo(x + length * .45, y - bend * .2, x, y);ctx.stroke();
      ctx.globalAlpha = .22 * fade;ctx.strokeStyle = '#a699b6';ctx.lineWidth = 3;ctx.stroke();
    }
    ctx.restore();
  }
  function effect(ctx, e) {
    const radius = e.m?.radius || 300,age = e.age || 0,t = clamp(age / (e.life || .3));
    if (t >= 1) return;
    const duration=e.m?.pushDuration??.24,speed=clamp(age/duration),release=speed*speed;
    const fade=1-clamp((age-duration)/Math.max(.001,(e.life||.4)-duration));
    const gather=e.m?.pullRadius??100,reach=e.m?.pushRadius??380,front=gather+(reach-gather)*release;
    ctx.save();ctx.translate(e.x, e.y);
    // Flash the entire real hit radius now; moving arcs below are aftermath.
    ctx.globalAlpha = .72 * Math.exp(-age / .075);ctx.strokeStyle = '#e6dfe9';ctx.lineWidth = 1 + 3 * (1 - release);
    ctx.beginPath();ctx.arc(0, 0, radius, 0, TAU);ctx.stroke();
    ctx.globalAlpha = .19 * fade * (.3+.7*speed);ctx.lineWidth = 1.5;
    for (let i = 0; i < 8; i++) {
      const a = i * TAU / 8 + .1;
      ctx.beginPath();ctx.arc(0, 0, front, a, a + .24);ctx.stroke();
    }
    for (let i = 0; i < 16; i++) {
      const a = i * TAU / 16 + .035 * (i % 3),head = front*(.94+(i%3)*.03);
      const tail = Math.max(0,head-(18+(64+(i%3)*12)*speed)),side = (i % 2 ? -1 : 1) * 3;
      ctx.globalAlpha = fade * (.25+.75*speed) * (i % 2 ? .35 : .6);ctx.strokeStyle = i % 2 ? '#b9b0a8' : '#ded4e1';ctx.lineWidth = i % 3 === 0 ? 2.5 : 1.5;
      ctx.beginPath();ctx.moveTo(Math.cos(a) * tail, Math.sin(a) * tail);
      ctx.quadraticCurveTo(Math.cos(a) * (tail + head) / 2 - Math.sin(a) * side,
        Math.sin(a) * (tail + head) / 2 + Math.cos(a) * side, Math.cos(a) * head, Math.sin(a) * head);ctx.stroke();
      if (i % 2 === 0) {
        const dust = gather+(reach-gather)*release*(.85+(i%3)*.05);
        ctx.globalAlpha = .38 * fade;ctx.fillStyle = '#a69a86';
        ctx.fillRect(Math.round(Math.cos(a) * dust), Math.round(Math.sin(a) * dust - Math.sin(speed * Math.PI) * 6), 3, 2);
      }
    }
    ctx.restore();
  }
  (G.PainSkillVFX ||= {}).gravity = { action, effect, ground };
})();
