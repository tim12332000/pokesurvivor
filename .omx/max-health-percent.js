/* Repeatable run-local health growth uses the maximum at the moment of selection. */
(() => {
  if (G.MaxHealthPercent) return;
  const perPick = .01;
  G.LevelUp.STATS.push({
    id: 'maxHealthPercent', icon: 'heart', title: '生命成長 +1%',
    desc: '最大生命值提高選取當下的 1%，並補回新增的生命值。可重複選取，每次依目前上限計算；僅限本局。',
    apply: owner => owner.addMaxHp(owner.maxHp * perPick)
  });
  G.MaxHealthPercent = { perPick };
})();
