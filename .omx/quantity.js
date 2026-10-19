/* Run-local quantity passive. Balance settings live here; learned moves stay immutable. */
(() => {
  if (G.Quantity) return;
  const config = Object.freeze({ perPick: 1, maxPicks: 20 });
  const bonus = owner => Math.max(0,Math.floor(owner?.quantityBonus||0));
  const count = (owner,base,minimum=1) => Math.max(minimum,base|0)+bonus(owner);
  function snapshot(owner,move) {
    if (move.quantityBonusAtCast != null) return {...move};
    return {...move,quantityBaseCount:Math.max(1,move.count|0),quantityBonusAtCast:bonus(owner),
      count:count(owner,move.count),
      ...(Number.isFinite(move.pierce)?{pierce:count(owner,move.pierce,0)}:{})};
  }
  G.Quantity={config,bonus,count,snapshot};
  G.LevelUp.STATS.push({id:'quantity',icon:'star',title:'數量增幅',
    desc:`投射物、分身、環繞物、連鎖目標、連擊、穿透、疊層及場上數量上限 +${config.perPick}。最多選 ${config.maxPicks} 次。`,
    max:config.maxPicks,
    apply:owner=>{
      owner.quantityBonus=bonus(owner)+config.perPick;
      const clones=owner.moves.find(m=>m.id==='naruto-shadow-clones');
      if(clones)G.NarutoClones.cast(owner,clones);
    }});
})();
