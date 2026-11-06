// Each ninja learns signature choices at their explicit or default milestones.
(() => {
  const sandShieldId='naruto-sand-shield', sandGuardId='naruto-sand-guard', basicId='naruto-gaara';
  const narutoAutomatic=new Set(['naruto-naruto','naruto-rasenshuriken','naruto-toad-summon']);
  function migrateNarutoAutomatic(player){
    if(player.mon?.dex!==30001)return;
    for(const move of player.moves)if(narutoAutomatic.has(move.id)){
      if(move.id==='naruto-naruto'&&move.cloneDashRange==null){
        const current=G.Moves.instance(move.id,move.lvl||1);
        move.range=current.range;move.cloneDashRange=current.cloneDashRange;
      }
      if(!move.autoCast){
        const previous=move.cd,next=G.Moves.instance(move.id,move.lvl||1).cd;
        if(move.t>0&&previous>0)move.t*=next/previous;
        move.cd=next;move.autoCast=true;
      }
      move.passive=true;
      if(player.bind)delete player.bind[move.id];
    }
    if(!player.slots.some(group=>group.some(move=>narutoAutomatic.has(move.id))))return;
    const selected=player.slots[player.active];
    for(const group of player.slots)for(let i=group.length-1;i>=0;i--)if(narutoAutomatic.has(group[i].id))group.splice(i,1);
    player.slots=player.slots.filter(group=>group.length);
    const retained=player.slots.indexOf(selected);player.active=retained>=0?retained:0;
  }
  const gaaraPassives=new Set([sandShieldId,sandGuardId,'naruto-sand-armor']);
  const painMove=move=>move.id==='naruto-pain'||move.id.startsWith('naruto-pain-');
  const temariPassives=new Set(['naruto-temari','naruto-temari-three-stars','naruto-temari-blade-dance','naruto-temari-reflect']);
  const kimimaroPassives=new Set(['naruto-kimimaro','naruto-kimimaro-bullets','naruto-kimimaro-larch','naruto-kimimaro-vine',
    'naruto-kimimaro-curse','naruto-kimimaro-bone-guard','naruto-kimimaro-camellia','naruto-kimimaro-flower',
    'naruto-kimimaro-lily','naruto-kimimaro-bracken','naruto-kimimaro-boomerang']);
  function migrateKimimaroPassives(player) {
    if(player.mon?.dex!==30012)return;
    for(const move of player.moves)if(kimimaroPassives.has(move.id)){
      move.passive=true;
      if(player.bind)delete player.bind[move.id];
    }
    if(!player.slots.some(group=>group.some(move=>kimimaroPassives.has(move.id))))return;
    const selected=player.slots[player.active];
    for(const group of player.slots)for(let i=group.length-1;i>=0;i--)if(kimimaroPassives.has(group[i].id))group.splice(i,1);
    player.slots=player.slots.filter(group=>group.length);
    const retained=player.slots.indexOf(selected);
    player.active=retained>=0?retained:0;
  }
  function migrateTemariPassives(player) {
    if(player.mon?.dex!==30011)return;
    for(const move of player.moves)if(temariPassives.has(move.id)){
      move.passive=true;
      if(player.bind)delete player.bind[move.id];
    }
    if(!player.slots.some(group=>group.some(move=>temariPassives.has(move.id))))return;
    const selected=player.slots[player.active];
    for(const group of player.slots)for(let i=group.length-1;i>=0;i--)if(temariPassives.has(group[i].id))group.splice(i,1);
    player.slots=player.slots.filter(group=>group.length);
    const index=player.slots.indexOf(selected);
    player.active=index>=0?index:0;
  }
  function migratePainPassives(player) {
    if(player.mon?.dex!==30010)return;
    for(const move of player.moves)if(painMove(move)){
      move.passive=true;
      if(player.bind)delete player.bind[move.id];
    }
    if(!player.slots.some(group=>group.some(painMove)))return;
    const selected=player.slots[player.active];
    player.slots=player.slots.map(group=>group.filter(move=>!painMove(move))).filter(group=>group.length);
    const index=player.slots.findIndex(group=>group.some(move=>selected?.includes(move)));
    player.active=index>=0?index:0;
  }
  function migrateGaaraBasic(player) {
    const basic=player.moves.find(move=>move.id===basicId);
    if(!basic)return;
    basic.passive=true;
    if(player.bind)delete player.bind[basicId];
    if(!player.slots.some(group=>group.includes(basic)))return;
    const selected=player.activeGroup();
    player.slots=player.slots.map(group=>group.includes(basic)?group.filter(move=>move!==basic):group).filter(group=>group.length);
    const retained=player.slots.findIndex(group=>group.some(move=>selected.includes(move)));
    player.active=retained>=0?retained:Math.max(0,Math.min(player.active,player.slots.length-1));
  }
  function migrateGaaraPassives(player) {
    if(player.mon?.dex!==30007)return;
    migrateGaaraBasic(player);
    const first=player.moves.findIndex(move=>gaaraPassives.has(move.id));
    const current=player.moves[first];
    const cleanMove=!current||(current.id===sandShieldId&&current.passive===true&&
      current.def===G.Moves.BY_ID[sandShieldId]&&current.range===400&&current.guardCount!=null&&
      Number.isInteger(current.lvl)&&current.lvl>=1&&current.lvl<=5&&
      !player.moves.some((move,index)=>index!==first&&gaaraPassives.has(move.id)));
    const passiveSlots=player.slots.some(group=>group.some(skill=>gaaraPassives.has(skill.id)));
    const passiveBindings=player.bind&&(Object.hasOwn(player.bind,sandShieldId)||Object.hasOwn(player.bind,sandGuardId)||Object.hasOwn(player.bind,'naruto-sand-armor'));
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
    player.slots=player.slots.map(group=>group.some(skill=>gaaraPassives.has(skill.id))?group.filter(skill=>!gaaraPassives.has(skill.id)):group).filter(group=>group.length);
    const retained=player.slots.findIndex(group=>group.some(skill=>selected.includes(skill)));
    player.active=retained>=0?retained:Math.max(0,Math.min(player.active,player.slots.length-1));
  }
  G.NarutoSkillCatalog.migrateGaaraPassives=migrateGaaraPassives;
  G.NarutoSkillCatalog.migrateNarutoAutomatic=migrateNarutoAutomatic;
  G.NarutoSkillCatalog.migrateKimimaroPassives=migrateKimimaroPassives;
  const arrange=G.Player.prototype.arrange;
  G.Player.prototype.arrange=function(...args){G.NarutoSharingan?.migrate(this);migrateNarutoAutomatic(this);migrateGaaraPassives(this);migratePainPassives(this);migrateTemariPassives(this);migrateKimimaroPassives(this);return arrange.apply(this,args);};
  const addMove=G.Player.prototype.addMove;
  G.Player.prototype.addMove=function(id,...args){
    if(id==='naruto-toad-summon'&&(this.mon?.dex!==30001||this.level<12))return false;
    if(this.mon?.dex===30001&&narutoAutomatic.has(id)){
      if(this.hasMove(id)){migrateNarutoAutomatic(this);return false;}
      this.moves.push(G.Moves.instance(id,1));this.arrange();return true;
    }
    if(id==='naruto-lee-drunken'){
      if(this.mon?.dex!==30006||this.level<4||this.hasMove(id))return false;
      this.moves.push(G.Moves.instance(id,1));this.arrange();return true;
    }
    if(this.mon?.dex===30012){
      const def=G.Moves.BY_ID[id];
      if(def?.learnLevel>Math.max(1,this.level||1))return false;
      if(kimimaroPassives.has(id)){
        if(this.hasMove(id)){migrateKimimaroPassives(this);return false;}
        this.moves.push(G.Moves.instance(id,1));
        this.arrange();
        return true;
      }
    }
    if((this.mon?.dex===30001&&id==='naruto-shadow-clones')||this.mon?.dex===30009&&['naruto-tenten','naruto-tenten-mastery','naruto-tenten-bounce','naruto-tenten-guard'].includes(id)||this.mon?.dex===30010&&painMove({id})||this.mon?.dex===30011&&temariPassives.has(id)){
      if(this.hasMove(id))return false;
      this.moves.push(G.Moves.instance(id,1));
      this.arrange();
      if(id==='naruto-tenten-guard')G.NarutoTenten?.ensureTalisman(this);
      if(id==='naruto-temari-blade-dance')G.NarutoTemari?.syncPets(this);
      if(id==='naruto-temari-reflect')G.NarutoTemariReflect?.sync(this);
      return true;
    }
    if(id===basicId&&this.mon?.dex===30007){
      if(this.hasMove(id)){migrateGaaraBasic(this);return false;}
      this.moves.push(G.Moves.instance(id,1));
      this.arrange();
      return true;
    }
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
    if(player?.mon===mon){G.NarutoSharingan?.migrate(player);migrateNarutoAutomatic(player);migrateGaaraPassives(player);migratePainPassives(player);migrateTemariPassives(player);migrateKimimaroPassives(player);}
    const ids=poolFor(mon);
    if(mon.dex===30012){
      const level=startingRun?1:player?.mon===mon?Math.max(1,player.level||1):1;
      return ids.filter(id=>(G.Moves.BY_ID[id]?.learnLevel||1)<=level);
    }
    // startRun may ask for a second starting attack before all wrappers expose
    // the new player; Temari has no legal second attack at level one.
    if(startingRun&&mon.dex===30011)return ids.filter(id=>!G.Moves.BY_ID[id].learnLevel);
    if(startingRun&&[30001,30002].includes(mon.dex)){
      const milestones=milestonesFor(mon.dex);
      return ids.filter(id=>!milestones.some(m=>m.id===id&&m.level>1));
    }
    if(!mon.naruto||mon!==player?.mon||(G.Game.state==='ui'&&!startingRun))return ids;
    const milestones=milestonesFor(mon.dex);
    return ids.filter(id=>!milestones.some(m=>m.id===id&&player.level<m.level));
  };
  function replacement(player) {
    return player.moves.find(m=>['naruto-kunai','naruto-shuriken'].includes(m.id)&&player.slots.some(s=>s.length===1&&s[0]===m));
  }
  function signatureCard(player,milestone) {
    const def=G.Moves.BY_ID[milestone.id];
    const slotless=def.passive;
    const swap=!slotless&&player.slots.length>=player.maxMoves?replacement(player):null;
    if(!slotless&&player.slots.length>=player.maxMoves&&!swap)return null;
    const previousId=swap?.id;
    const firstOffer=!player.narutoMilestonesShown?.has(def.id);
    return {w:10,type:'new',key:'new:'+def.id,icon:'move:'+def.id,color:G.U.TYPE_COLOR[def.type],
      guaranteed:firstOffer,
      onShown:p=>{if(p===player)(p.narutoMilestonesShown??=new Set()).add(def.id);},
      tag:`${player.mon.chinese||player.mon.name}特色招式${firstOffer?'・首次解鎖':''}`,title:def.name,
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
  const gatesLevels=[4,8,16];
  G.LevelUp.offer=(player,n=3)=>{
    G.NarutoSharingan?.migrate(player);
    migrateNarutoAutomatic(player);
    migrateGaaraPassives(player);
    migratePainPassives(player);
    migrateTemariPassives(player);
    migrateKimimaroPassives(player);
    if(!player.mon?.naruto)return offer(player,n);
    const retired=['naruto-kunai','naruto-shuriken'];
    return offer(player,n,candidates=>{
      const cards=new Map(candidates.filter(c=>!retired.some(id=>c.key.endsWith(':'+id))).map(c=>[c.key,c]));
      if(player.mon.dex===30006){
        cards.delete('new:naruto-gates');
        cards.delete('up:naruto-gates');
      }
      for(const milestone of milestonesFor(player.mon.dex)){
        if(player.mon.dex===30006&&milestone.id==='naruto-gates')continue;
        if(player.level<milestone.level||player.hasMove(milestone.id)||player.banned?.has(milestone.id))continue;
        const card=signatureCard(player,milestone);
        if(card)cards.set(card.key,card);
      }
      const result=[...cards.values()];
      if(player.mon.dex===30006){
        const move=player.moves.find(move=>move.id==='naruto-gates');
        const tier=move?.lvl||0,required=player.level,opportunity='naruto-gates:'+required;
        if(tier<3&&gatesLevels.includes(required)&&!player.narutoMilestonesShown?.has(opportunity)&&(move||!player.banned?.has('naruto-gates'))){
          const card=move?candidates.find(card=>card.key==='up:naruto-gates'):signatureCard(player,{id:'naruto-gates'});
          if(card){
            card.guaranteed=true;
            card.onShown=p=>{if(p===player)(p.narutoMilestonesShown??=new Set()).add(opportunity);};
            card.tag=`Lv.${required}・${G.NarutoGates.config.stageNames[tier]}`;
            result.unshift(card);
          }
        }
      }
      if(player.mon.dex===30012)result.sort((a,b)=>{
        if(!a.guaranteed||!b.guaranteed)return Number(!!b.guaranteed)-Number(!!a.guaranteed);
        const level=card=>G.Moves.BY_ID[card.key.replace(/^new:/,'')]?.learnLevel||0;
        return level(b)-level(a);
      });
      return result;
    });
  };
})();
