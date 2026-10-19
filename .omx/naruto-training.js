// Each ninja learns signature choices at their explicit or default milestones.
(() => {
  const milestonesFor = dex => (G.NarutoSkillCatalog.extraPools.get(dex) || [])
    .map((id,index)=>({level:G.Moves.BY_ID[id].learnLevel||(index===0?3:6),id}));
  let startingRun=false;
  const startRun=G.Game.startRun;
  G.Game.startRun=function(...args){startingRun=true;try{return startRun.apply(this,args);}finally{startingRun=false;}};
  const poolFor=G.Moves.poolFor;
  G.Moves.poolFor=mon=>{
    const ids=poolFor(mon),player=G.Game.player;
    if(!mon.naruto||mon!==player?.mon||(G.Game.state==='ui'&&!startingRun))return ids;
    const milestones=milestonesFor(mon.dex);
    return ids.filter(id=>!milestones.some(m=>m.id===id&&player.level<m.level));
  };
  function replacement(player) {
    return player.moves.find(m=>['naruto-kunai','naruto-shuriken'].includes(m.id)&&player.slots.some(s=>s.length===1&&s[0]===m));
  }
  function signatureCard(player,milestone) {
    const def=G.Moves.BY_ID[milestone.id];
    const swap=player.slots.length>=player.maxMoves?replacement(player):null;
    if(player.slots.length>=player.maxMoves&&!swap)return null;
    const previousId=swap?.id;
    return {w:100,type:'new',key:'new:'+def.id,icon:'move:'+def.id,color:G.U.TYPE_COLOR[def.type],
      tag:`${player.mon.chinese||player.mon.name}特色招式`,title:def.name,
      desc:(swap?`替換「${swap.name}」。`:'')+def.desc,
      apply:p=>{
        if(p.hasMove(def.id))return false;
        if(!swap)return p.addMove(def.id);
        if(!p.moves.includes(swap)||swap.id!==previousId||!p.slots.some(s=>s.length===1&&s[0]===swap))return false;
        const next=G.Moves.instance(def.id);
        for(const key of Object.keys(swap))delete swap[key];Object.assign(swap,next);
        if(p.bind[previousId]!=null){p.bind[def.id]=p.bind[previousId];delete p.bind[previousId];}
        p.arrange();p.setActive(p.slots.findIndex(s=>s.includes(swap)));return true;
      }};
  }
  const offer=G.LevelUp.offer;
  G.LevelUp.offer=(player,n=3)=>{
    const cards=offer(player,n);
    if(!player.mon?.naruto)return cards;
    const milestones=milestonesFor(player.mon.dex);
    const guaranteed=milestones.filter(m=>player.level>=m.level&&!player.hasMove(m.id)&&!player.banned?.has(m.id))
      .map(m=>signatureCard(player,m)).filter(Boolean).slice(0,n);
    const keys=new Set(guaranteed.map(c=>c.key));
    return [...guaranteed,...cards.filter(c=>!keys.has(c.key))].slice(0,n);
  };
})();
