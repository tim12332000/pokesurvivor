/* Repeatable run-local size and health growth with movement and attack tradeoffs. */
(() => {
  if (G.Giant) return;
  const size = 1.25, health = 1.25, speed = .9, attackSpeed = .9;
  const interval = owner => attackSpeed ** -(owner?.giantPicks || 0);
  G.LevelUp.STATS.push({
    id: 'giant', icon: 'giant', title: '倍化之術',
    desc: '體積與碰撞範圍 ×1.25、最大生命 ×1.25、移動速度 ×0.9、攻擊速度 ×0.9，並補回新增生命。可重複選取，各效果逐張累乘；僅限本局。',
    apply: owner => {
      owner.giantPicks = (owner.giantPicks || 0) + 1;
      owner.anim.scale *= size;
      owner.r *= size;
      owner.bodyH *= size;
      owner.addMaxHp(owner.maxHp * (health - 1));
      owner.spdMul *= speed;
      owner.cdMul /= attackSpeed;
    }
  });
  G.Giant = { size, health, speed, attackSpeed, interval };
})();
