/* Explicit single-target hit extension. Secondary damage never triggers hit passives. */
(() => {
  if (G.DamageSplash) return;
  const radius = 60, perPick = .1;
  let secondary = 0;
  const rate = owner => Math.max(0, owner?.damageSplashPicks || 0) * perPick;
  G.LevelUp.STATS.push({ id: 'damageSplash', icon: 'damageSplash', title: '傷害擴散 +10%',
    desc: '單體命中時，對周圍其他敵人造成直接傷害的 10%；每張再加 10 個百分點（10%／20%／30%…）。不連鎖、不複製百分比生命附傷，也不觸發吸血或控制。',
    apply: owner => { owner.damageSplashPicks = (owner.damageSplashPicks || 0) + 1; }
  });
  function clearPath(x, y, tx, ty) {
    const length = Math.hypot(tx - x, ty - y), steps = Math.max(1, Math.ceil(length / 4));
    for (let i = 0; i <= steps; i++) {
      const px = x + (tx - x) * i / steps, py = y + (ty - y) * i / steps;
      if (G.World.isWall(px, py) || G.World.projectileBlock?.(px, py, 1)) return false;
    }
    return true;
  }
  function hit(owner, target, directDamage, color = '#fff', moveId = null) {
    const fraction = rate(owner);
    if (secondary || !fraction || !target || !owner || owner.dead || owner.hp <= 0 ||
        (!G.Game.everyone().includes(owner) && !G.SelfClones?.isActor(owner) && !G.NarutoTemariReflect?.isDamageOwner(owner)) || !Number.isFinite(directDamage) || directDamage <= 0) return 0;
    const amount = directDamage * fraction;
    let dealt = 0;
    secondary++;
    try {
      for (const enemy of new Set(G.EnemyMgr.queryCircle(target.x, target.y, radius))) {
        if (enemy === target || enemy.dead || enemy.hp <= 0 || enemy.friendly ||
            Math.hypot(enemy.x - target.x, enemy.y - target.y) > radius ||
            !clearPath(target.x, target.y, enemy.x, enemy.y)) continue;
        // Reuse the primary hit's resolved damage: no second crit/type/weather roll.
        enemy.hurt(amount, color, 0, 0, 0, null, owner, moveId);
        owner.dmgDealt += amount;
        dealt += amount;
      }
    } finally { secondary--; }
    return dealt;
  }
  G.DamageSplash = { hit, rate, radius, perPick, isSecondary: () => secondary > 0 };
})();
