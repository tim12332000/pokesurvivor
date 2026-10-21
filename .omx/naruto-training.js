// Each ninja learns signature choices at their explicit or default milestones.
(() => {
  const sandShieldId='naruto-sand-shield', sandGuardId='naruto-sand-guard';
  const gaaraPassives=new Set([sandShieldId,sandGuardId]);
  function migrateGaaraPassives(player) {
    if(player.mon?.dex!==30007)return;
    const first=player.moves.findIndex(move=>gaaraPassives.has(move.id));
    const current=player.moves[first];
    const cleanMove=!current||(current.id===sandShieldId&&current.passive===true&&
      current.def===G.Moves.BY_ID[sandShieldId]&&current.range===400&&current.guardCount!=null&&
      Number.isInteger(current.lvl)&&current.lvl>=1&&current.lvl<=5&&
      !player.moves.some((move,index)=>index!==first&&gaaraPassives.has(move.id)));
    const passiveSlots=player.slots.some(group=>group.some(skill=>gaaraPassives.has(skill.id)));
    const passiveBindings=player.bind&&(Object.hasOwn(player.bind,sandShieldId)||Object.hasOwn(player.bind,sandGuardId));
    // The runtime checks on every tick; already normalized players need no
    // allocation, replacement arrays, or writes, while late legacy additions
    // are still detected immediately without a persistent migration cache.
    if(cleanMove&&!passiveSlots&&!passiveBindings)return;
    const old=player.moves.filter(move=>gaaraPassives.has(move.id));
    const canonical=old.find(move=>move.id===sandShieldId)||old[0];
    if(canonical){
      const tier=Math.max(...old.map(move=>Math.max(1,Math.min(5,move.lvl|0))));
      if(canonical.id!==sandShieldId||canonical.lvl!==tier||canonical.def!==G.Moves.BY_ID[sandShieldId]||canonical.guardCount==null||canonical.range!==400){
        const next=G.Moves.instance(sandShieldId,tier);
        // Keep the existing instance and its timers/statistics; runtime defenses
        // hold references to it and apply only the capacity delta on their tick.
        const timing={t:canonical.t,dealt:canonical.dealt,since:canonical.since};
        Object.assign(canonical,next,timing);
      }
      canonical.passive=true;
      player.moves=player.moves.filter(move=>!gaaraPassives.has(move.id)||move===canonical);
    }
    if(player.bind)for(const id of gaaraPassives)delete player.bind[id];
    if(!player.slots.some(group=>group.some(skill=>gaaraPassives.has(skill.id))))return;
    const selected=player.activeGroup();
    player.slots=player.slots.map(group=>group.filter(skill=>!gaaraPassives.has(skill.id))).filter(group=>group.length);
    const retained=player.slots.findIndex(group=>group.some(skill=>selected.includes(skill)));
    player.active=retained>=0?retained:Math.max(0,Math.min(player.active,player.slots.length-1));
  }
  G.NarutoSkillCatalog.migrateGaaraPassives=migrateGaaraPassives;
  const arrange=G.Player.prototype.arrange;
  G.Player.prototype.arrange=function(...args){migrateGaaraPassives(this);return arrange.apply(this,args);};
  const addMove=G.Player.prototype.addMove;
  G.Player.prototype.addMove=function(id,...args){
    if(!gaaraPassives.has(id)||this.mon?.dex!==30007)return addMove.call(this,id,...args);
    migrateGaaraPassives(this);
    if(this.hasMove(sandShieldId)){this.arrange();return false;}
    this.moves.push(G.Moves.instance(sandShieldId,1));
    this.arrange();
    return true;
  };
  const milestonesFor = dex => (G.NarutoSkillCatalog.extraPools.get(dex) || [])
    .map((id,index)=>({level:G.Moves.BY_ID[id].learnLevel||(index===0?3:6),id}));
  let startingRun=false;
  const startRun=G.Game.startRun;
  G.Game.startRun=function(...args){startingRun=true;try{return startRun.apply(this,args);}finally{startingRun=false;}};
  const poolFor=G.Moves.poolFor;
  G.Moves.poolFor=mon=>{
    const player=G.Game.player;
    if(player?.mon===mon)migrateGaaraPassives(player);
    const ids=poolFor(mon);
    if(!mon.naruto||mon!==player?.mon||(G.Game.state==='ui'&&!startingRun))return ids;
    const milestones=milestonesFor(mon.dex);
    return ids.filter(id=>!milestones.some(m=>m.id===id&&player.level<m.level));
  };
  function replacement(player) {
    return player.moves.find(m=>['naruto-kunai','naruto-shuriken'].includes(m.id)&&player.slots.some(s=>s.length===1&&s[0]===m));
  }
  function armorReplacement(player,def) {
    if(player.mon?.dex!==30007||def.id!=='naruto-sand-armor')return null;
    const choices=player.slots.filter(s=>s.length===1&&s[0].id!=='naruto-gaara').map(s=>s[0]);
    return choices.find(m=>player.activeGroup().includes(m))||choices[choices.length-1]||null;
  }
  function signatureCard(player,milestone) {
    const def=G.Moves.BY_ID[milestone.id];
    const slotless=def.passive&&(def.id==='naruto-gates'||gaaraPassives.has(def.id));
    const swap=!slotless&&player.slots.length>=player.maxMoves?(replacement(player)||armorReplacement(player,def)):null;
    if(!slotless&&player.slots.length>=player.maxMoves&&!swap)return null;
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
        p.arrange();p.setActive(def.passive?p.slots.findIndex(s=>s.some(move=>!move.passive)):p.slots.findIndex(s=>s.includes(swap)));return true;
      }};
  }
  const offer=G.LevelUp.offer;
  G.LevelUp.offer=(player,n=3)=>{
    migrateGaaraPassives(player);
    if(!player.mon?.naruto)return offer(player,n);
    const retired=['naruto-kunai','naruto-shuriken'];
    const legacyCount=player.moves.filter(m=>retired.includes(m.id)).length;
    const cards=offer(player,n+legacyCount).filter(c=>!retired.some(id=>c.key.endsWith(':'+id)));
    const milestones=milestonesFor(player.mon.dex);
    const guaranteed=milestones.filter(m=>player.level>=m.level&&!player.hasMove(m.id)&&!player.banned?.has(m.id))
      .map(m=>signatureCard(player,m)).filter(Boolean).slice(0,n);
    const keys=new Set(guaranteed.map(c=>c.key));
    return [...guaranteed,...cards.filter(c=>!keys.has(c.key))].slice(0,n);
  };
})();
