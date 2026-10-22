/* Explicitly owned hits gain one flat max-HP component, never another hit. */
(() => {
  if (G.PercentHealthDamage) return;
  const perPick = .01, bossMultiplier = .1;
  G.LevelUp.STATS.push({
    id: 'percentHealthDamage', icon: 'fist', title: '生命剝奪 +1%',
    desc: '每次命中額外造成目標最大生命值 1% 的傷害；對首領、傳說與審判者效果為十分之一（每張 0.1%）。可重複疊加、不佔技能欄；不受暴擊與屬性倍率影響。',
    apply: owner => { owner.percentHealthDamage = Math.round(((owner.percentHealthDamage || 0) + perPick) * 100) / 100; }
  });
  const hurt = G.Enemy.prototype.hurt;
  G.Enemy.prototype.hurt = function(amount, color, dirX, dirY, knock, eff, owner, moveId) {
    const rate = owner?.percentHealthDamage;
    const boss = this.boss || this.legend || this.judge;
    const guardianBossHit = (moveId === 'naruto-sand-shield' || moveId === 'naruto-sand-guard') &&
      boss;
    const bonus = !guardianBossHit && !G.DamageSplash?.isSecondary() && !this.dead && this.hp > 0 && owner && !owner.dead && owner.hp > 0 &&
      (G.Game.everyone().includes(owner) || G.SelfClones?.isActor(owner)) && Number.isFinite(amount) && amount > 0 &&
      Number.isFinite(rate) && rate > 0 && Number.isFinite(this.maxHp) && this.maxHp > 0
        ? this.maxHp * rate * (boss ? bossMultiplier : 1) : 0;
    // One native hit preserves shields, knockback, death, networking and hit VFX.
    const result = hurt.call(this, amount + bonus, color, dirX, dirY, knock, eff, owner, moveId);
    if (bonus > 0) {
      // Match existing combat accounting, including damage absorbed by shields.
      owner.onDealt(bonus);
      owner.dmgDealt += bonus;
    }
    return result;
  };
  G.PercentHealthDamage = { perPick, bossMultiplier };
})();
