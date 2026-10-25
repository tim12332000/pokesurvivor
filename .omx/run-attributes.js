// Run card bonuses, rendered in screen coordinates without covering touch controls.
(() => {
  const percent = value => Math.round(value * 1000) / 10;
  const labels = {
    hp: n => `生命 +${20*n}`,
    giant: n => `倍化之術 ×${n}（體積/生命 ×${Math.round((G.Giant?.size ?? 1.25)**n*100)/100}）`,
    selfClone: (n, pl) => `分身 ${G.SelfClones?.actors().filter(a=>a.sourceOwner===pl).length||0} 隻（已召喚 ${n} 次）`,
    maxHealthPercent: n => `生命成長 +${Math.round((G.MaxHealthPercent?.perPick ?? .1)*100)}% ×${n}`,
    atk: n => `攻擊 +${percent(1.1**n-1)}%`,
    spd: n => `移速 +${percent(1.07**n-1)}%`,
    cd: n => `冷卻 −${percent(1-.92**n)}%`,
    def: (n, pl) => `減傷 ${percent(pl.reduction)}%`,
    rgn: n => `回血 +${Math.round(.9*n*10)/10}/秒`,
    mag: n => `拾取 +${percent(1.3**n-1)}%`,
    xp: n => `經驗 +${percent(1.12**n-1)}%`,
    ninjaToolBounce: n => `忍具連彈 +${n} 次`,
    quantity: (n, pl) => pl.quantityPicks != null ? `數量 ×${Math.round((G.Quantity?.multiplier(pl)||1)*100)/100}` : `數量 +${pl.quantityBonus||0}`,
    damageSplash: (n, pl) => `傷害擴散 ${Math.round((G.DamageSplash?.rate(pl)||0)*100)}%`,
    lifesteal: (n, pl) => `吸血 ${percent(pl.lifestealRate||0)}%`,
    percentHealthDamage: (n, pl) => `生命剝奪 ${percent(pl.percentHealthDamage||0)}%`
  };
  const rows = pl => {
    const items=Object.entries(labels).filter(([id])=>(pl.statsTaken?.[id]||0)>0)
      .map(([id,label])=>({id,text:label(pl.statsTaken[id],pl)}));
    const growth=G.NarutoPain?.durabilityState(pl);
    if(growth?.healthBonus>0)items.unshift({id:'painHealthGrowth',text:`天道生命成長 +${growth.healthBonus}`},
      {id:'painDefenseGrowth',text:`實際減傷 ${percent(pl.reduction)}%`});
    return items;
  };
  const draw = G.HUD.draw;
  G.HUD.draw = function(ctx, w, h, pl, st) {
    draw.call(this, ctx, w, h, pl, st);
    const items = rows(pl);
    if(!items.length)return;
    const touch=G.Touch.active;
    const controls=touch?G.Touch.controlLayout(w,h,Math.max(1,pl.slots.length)):null;
    const portrait=!!controls?.portrait;
    const safeTop=portrait?Math.min(44,G.Touch.safeArea().top):0;
    const width=portrait?146:170, x=w-width-12, y=portrait?180+safeTop:102;
    const rowHeight=portrait?Math.min(16,Math.max(11,(controls.bar.y-y-36)/items.length)):16;
    const height=28+items.length*rowHeight;
    ctx.save();
    G.HUD.roundRect(ctx,x,y,width,height,8);
    ctx.fillStyle='rgba(5,14,32,.78)';ctx.fill();
    ctx.textAlign='left';ctx.textBaseline='top';
    ctx.font='700 11px "Segoe UI",system-ui,sans-serif';
    ctx.fillStyle='#ffcf7c';ctx.fillText('已獲得屬性',x+9,y+8,width-18);
    ctx.font=`${rowHeight<15?10:11}px "Segoe UI",system-ui,sans-serif`;
    for(let i=0;i<items.length;i++){
      ctx.fillStyle=['quantity','lifesteal','percentHealthDamage'].includes(items[i].id)?'#9fe7ff':'#eaf2ff';
      ctx.fillText(items[i].text,x+9,y+26+i*rowHeight,width-18);
    }
    ctx.restore();
  };
  G.RunAttributes={rows};
})();
