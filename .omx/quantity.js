/* Run-local quantity passive. Balance settings live here; learned moves stay immutable. */
(() => {
  if (G.Quantity) return;
  const config = Object.freeze({ perPick: 1.25, maxPicks: 20 });
  // quantityBonus remains readable for old run fixtures and linear pierce growth.
  const bonus = owner => Math.max(0,Math.floor(owner?.quantityPicks ?? owner?.quantityBonus ?? 0));
  const multiplier = owner => config.perPick ** Math.max(0, Math.floor(owner?.quantityPicks || 0));
  const scaled = (base, minimum, scale, legacyBonus=0) =>
    Math.max(minimum, Math.floor(Math.max(minimum, Number(base) || 0) * scale) + legacyBonus);
  const count = (owner,base,minimum=1) => scaled(base, minimum, multiplier(owner), owner?.quantityPicks == null ? bonus(owner) : 0);
  const countAtCast = (owner,move,base,minimum=1) => move.quantityMultiplierAtCast != null
    ? scaled(base, minimum, move.quantityMultiplierAtCast, move.quantityLegacyBonusAtCast || 0)
    : move.quantityBonusAtCast != null ? scaled(base, minimum, 1, move.quantityBonusAtCast) : count(owner,base,minimum);
  function snapshot(owner,move) {
    if (move.quantityBonusAtCast != null) return {...move};
    const sharinganProjectilesAtCast=G.NarutoSharingan?.projectileBonus(owner,move)||0;
    return {...move,quantityBaseCount:Math.max(1,move.count|0),quantityBonusAtCast:bonus(owner),
      quantityMultiplierAtCast:multiplier(owner),quantityLegacyBonusAtCast:owner?.quantityPicks == null ? bonus(owner) : 0,sharinganProjectilesAtCast,
      count:count(owner,move.count)+sharinganProjectilesAtCast,
      ...(Number.isFinite(move.pierce)?{pierce:Math.max(0,move.pierce)+bonus(owner)}:{})};
  }
  G.Quantity={config,bonus,multiplier,count,countAtCast,snapshot};
  G.LevelUp.STATS.push({id:'quantity',icon:'star',title:`數量 ×${config.perPick}`,
    desc:`每張使投射物、分身、護衛、環繞物與連擊等數量 ×${config.perPick}。保留小數累乘，最後取整，既有上限不變；穿透每張 +1。最多選 ${config.maxPicks} 次。`,
    max:config.maxPicks,
    apply:owner=>{
      owner.quantityPicks=bonus(owner)+1;
      owner.quantityBonus=owner.quantityPicks;
      const clones=owner.moves.find(m=>m.id==='naruto-shadow-clones');
      if(clones)G.NarutoClones.cast(owner,clones);
    }});
})();
