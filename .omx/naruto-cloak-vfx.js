/* One-tail Naruto: original sprite stays intact beneath a procedural pixel cloak. */
(() => {
  'use strict';
  const G = window.G;
  const snap = value => Math.round(value / 2) * 2;
  const polygon = (ctx, points, color) => {
    ctx.fillStyle = color;
    ctx.beginPath();
    points.forEach(([x, y], i) => i ? ctx.lineTo(snap(x), snap(y)) : ctx.moveTo(snap(x), snap(y)));
    ctx.closePath(); ctx.fill();
  };
  function tail(ctx, age, side, depth) {
    // Overlapping square cross-sections produce one tapering, moving tail.
    const points = [];
    for (let i = 0; i <= 18; i++) {
      const t = i / 18;
      points.push([side * (5 + 49 * t), -21 - depth * t - Math.sin(t * 2.7 + age * 5) * 9 * t]);
    }
    for (let layer = 0; layer < 3; layer++) {
      ctx.fillStyle = ['#71152d', '#d42b39', '#ff6749'][layer];
      for (let i = 0; i < points.length; i++) {
        const width = Math.max(2, snap((13 - i * .57) * [1, .73, .3][layer]));
        const [x, y] = points[i];
        ctx.fillRect(snap(x - width / 2), snap(y - width / 2), width, width);
      }
    }
  }
  function pulse(ctx, radius, flash) {
    // A short, broken pixel ring communicates the actual counterattack radius.
    if (!(flash > 0)) return;
    ctx.save(); ctx.globalAlpha *= Math.min(1, flash * 5);
    const r = Math.min(500, Math.max(12, radius));
    const advance = 1 - Math.min(1, flash / .25);
    ctx.fillStyle = '#ff6c55';
    for (let i = 0; i < 40; i++) {
      const angle = i * Math.PI / 20;
      ctx.fillRect(snap(Math.cos(angle) * r * (.8 + advance * .2)),
        snap(Math.sin(angle) * r * (.8 + advance * .2)), 4, 2);
    }
    ctx.restore();
  }
  function draw(ctx, f, ground) {
    const owner = f.owner;
    if (!owner || !Number.isFinite(owner.x) || !Number.isFinite(owner.y)) return;
    const age = Math.max(0, f.age || 0);
    const scale = Math.min(1.4, Math.max(.65, owner.anim?.scale ?? 1));
    const direction = owner.anim?.dir8 ?? owner.anim?.dir ?? 0;
    const side = direction >= 1 && direction <= 3 ? -1 : 1;
    const depth = direction >= 3 && direction <= 5 ? -18 : 14;
    ctx.save();
    ctx.translate(snap(owner.x), snap(owner.y)); ctx.scale(scale, scale);
    ctx.globalAlpha *= Math.min(1, age * 8, Math.max(0, f.ttl - age) * 4);
    if (ground) {
      ctx.globalAlpha *= .75;
      ctx.fillStyle = '#9f273844'; ctx.fillRect(-20, -2, 40, 6);
      tail(ctx, age, side, depth);
      polygon(ctx, [[-19, -28], [-17, -48], [-13, -50], [-15, -62], [-9, -58], [-3, -63],
        [3, -63], [10, -59], [16, -63], [14, -49], [18, -45], [20, -26], [14, -7], [-14, -7]], '#bd243d');
      return ctx.restore();
    }
    // Leave the face and central hair visible: the front sheath starts at the shoulders.
    ctx.globalAlpha *= .55 + Math.sin(age * 10) * .06;
    polygon(ctx, [[-15, -40], [-18, -34], [-17, -23], [-12, -19], [-10, -7], [-5, -7],
      [-5, -23], [5, -23], [5, -7], [11, -7], [13, -20], [18, -23], [18, -34], [14, -40],
      [10, -34], [8, -27], [-8, -27], [-11, -35]], '#f5453c');
    ctx.globalAlpha /= .55 + Math.sin(age * 10) * .06;
    polygon(ctx, [[-14, -53], [-17, -65], [-11, -61], [-7, -55]], '#e83543');
    polygon(ctx, [[8, -55], [15, -65], [14, -52]], '#e83543');
    ctx.fillStyle = '#ff8c60';
    for (const sign of [-1, 1]) {
      const fist = Math.sin(age * 9 + sign) * 2;
      ctx.fillRect(sign < 0 ? -18 : 14, snap(-29 + fist), 4, 6);
      for (let claw = 0; claw < 3; claw++) ctx.fillRect(sign < 0 ? -20 - claw * 2 : 18 + claw * 2,
        snap(-25 + fist + claw * 2), 2, 4);
    }
    // Deterministic boiling bubbles follow simulation time and freeze with pause.
    for (let i = 0; i < 12; i++) {
      const life = (age * .7 + i * .137) % 1;
      const x = Math.sin(i * 2.4 + age * 2) * (15 + i % 3 * 3);
      const y = -8 - life * 55;
      ctx.globalAlpha *= (1 - life) * .7;
      ctx.fillStyle = i % 3 ? '#ee3548' : '#ff9870';
      const size = i % 3 ? 2 : 4;
      ctx.fillRect(snap(x), snap(y), size, size);
      ctx.globalAlpha /= Math.max(.0001, (1 - life) * .7);
    }
    pulse(ctx, (f.m?.radius || 76) / scale, f.pulseFlash);
    ctx.restore();
  }
  G.NarutoCloakVFX = { draw };
})();
