/* Run-local lifesteal passive, shared by every owner-credited damage source. */
(() => {
  if(G.Lifesteal)return;
  const perPick=.01;
  G.LevelUp.STATS.push({id:'lifesteal',icon:'lifesteal',title:'吸血 +1%',
    desc:'造成傷害時回復生命，吸血比例 +1%。可重複選取疊加，僅本局有效。',
    apply:owner=>{owner.lifestealRate=Math.round(((owner.lifestealRate||0)+perPick)*100)/100;}
  });
  const onDealt=G.Player.prototype.onDealt;
  G.Player.prototype.onDealt=function(damage){
    onDealt.call(this,damage);
    if(!this.dead&&this.hp>0&&Number.isFinite(damage)&&damage>0&&this.lifestealRate>0)
      this.heal(damage*this.lifestealRate);
  };
  G.Lifesteal={perPick};
})();
