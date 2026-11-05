/* Shared run-card benefits and capability-based legendary rewards. */
(() => {
  'use strict';
  if (G.JujutsuGrowth) return;
  const MAX_Q=G.Quantity?.config.maxPicks||20, factor=G.Quantity?.config.perPick||1.25;
  const nativeOffer=G.LevelUp.offer, probeCache=new Map(), rewardOffers=new WeakMap(), customConsumers=new Map();
  const finite=(n,fallback=0)=>Number.isFinite(n)?n:fallback;
  const rank=m=>Math.max(1,Math.min(5,m.lvl||1));
  const fmt=n=>String(Math.round(finite(n)*100)/100);
  const picks=p=>Math.max(0,Math.floor(p.quantityPicks??p.quantityBonus??0));
  const count=(p,base,cap=Infinity)=>Math.min(cap,G.Quantity?.count(p,base)??Math.max(1,Math.floor(base*factor**picks(p))));
  function withQuantity(p,q){
    const copy=Object.create(p);Object.defineProperties(copy,{quantityPicks:{value:q},quantityBonus:{value:q}});return copy;
  }
  function vector(p,m){
    const mode=m.digiMode||'',i=rank(m)-1;
    if(customConsumers.has(mode))return customConsumers.get(mode)(p,m);
    if(mode==='jjk-ryu-spread')return {砲道:count(p,m.baseCount||3,9)};
    if(mode==='jjk-ryu-maximum')return {追加重砲:count(p,m.barrageBase??[4,5,6,7,8][i],16)};
    if(mode==='yuta-rika'){
      const config=G.Jujutsu.power.yuta,base=config.rikaBases[i];
      return {協擊拳數:count(p,base,config.rikaCap),顯現拳數:count(p,base*2,config.fullCap)};
    }
    if(mode==='uro-thin-ice'||mode==='uro-collapse')return {裂面波次:count(p,G.Jujutsu.power.uro.waveBases[i],G.Jujutsu.power.uro.waveCap)};
    if(mode==='uro-screen'){
      const config=G.Jujutsu.power.uro;
      return {反射容量:count(p,config.screenBudgets[i],config.screenCap),反擊波次:count(p,config.waveBases[i],config.waveCap)};
    }
    if(mode==='uro-echo')return {殘響次數:count(p,G.Jujutsu.power.uro.echoBases[i],G.Jujutsu.power.uro.echoCap)};
    if(m.jujutsuSkill)return null;
    if(mode==='shadow-clones')return {影分身:count(p,G.NarutoClones?.config.counts[i]||[8,10,12,14,16][i])};
    if(mode==='chidori-chain')return {追擊:count(p,G.NarutoChidori?.config.counts[i]||[5,10,15,18,22][i])};
    if(mode==='lee-lotus')return {束縛目標:count(p,3,12)};
    if(mode==='lee-reverse-lotus')return {束縛目標:count(p,10,40),連擊:count(p,5+2*i)};
    if(mode==='gaara-sand-burst')return {砂彈:count(p,m.count||3)};
    if(mode==='gaara-coffin')return {束縛目標:count(p,Math.min(10,1+(p.level||1)),30)};
    if(m.id==='naruto-sand-shield'||mode==='gaara-shield'||mode==='gaara-sand-guard'){
      const c=G.NarutoSandGuard?.config;if(!c)return null;
      return {砂護衛:count(p,(c.capacities[i]||1)+Math.max(1,p.level||1),c.maxGuardians)};
    }
    if(mode==='kimimaro-willow')return {目標:count(p,4,8)};
    if(mode==='kimimaro-camellia')return {目標:count(p,4,12)};
    if(mode==='kimimaro-bullets')return {指骨:count(p,5,15)};
    if(mode==='kimimaro-boomerang')return {骨迴旋:count(p,m.count||1,16),穿透:(m.pierce||0)+picks(p)};
    if(mode==='temari-reflect')return {反射副本:Math.floor(factor**picks(p))};
    if(G.NarutoTemari?.supports(mode)&&mode!=='temari-mastery'){
      if(mode==='temari-great-scythe'){
        const h=G.NarutoTemari.heavyFor(p,m);return {射程:h.range,推退:h.pushDistance};
      }
      // snapshot() creates actor state; derive its public count formulas without
      // calling it for temporary quantity previews.
      const Q=picks(p),L=G.NarutoTemari.mastery(p).L,scale=factor**Q;
      if(mode==='temari-wind')return {風刃:Math.floor(3*scale),切擊:L?1+L+Q:1};
      if(mode==='temari-typhoon')return {颱風:Math.floor(scale),彈數:[3,4,5,6,8][i]+(L?L+Q:0)};
      return {協戰:Math.floor(scale),切擊:[4,4,5,5,6][i]+(L?L+Q:0)};
    }
    if(G.NarutoPain?.supports(mode)){
      const n=G.NarutoPain.projectileCount(p,m);return n>0?{投射物:n}:null;
    }
    if(mode.startsWith('tenten-')&&!['tenten-mastery','tenten-bounce','tenten-guard'].includes(mode))return {忍具:count(p,m.count||1)};
    if(mode==='kusanagi-orbit')return {草薙劍:count(p,m.count||1)};
    if(m.id==='naruto-lee')return {旋踢段數:count(p,m.count||1)};
    if(m.digimonSkill)return ['shot','nova','melee','dual'].includes(mode)?{數量:count(p,m.count||1)}:null;
    if(['projectile','nova','boomerang','chain','mine','meteor','turret','orbit','cone','trail','buff'].includes(m.kind))
      return {數量:count(p,m.kind==='trail'?18:m.count||m.stacks||1),...(['projectile','nova','cone'].includes(m.kind)?{穿透:(m.pierce||0)+picks(p)}:{})};
    return null;
  }
  const different=(a,b)=>Object.keys(a||{}).some(k=>a[k]!==b?.[k]);
  function quantityBenefit(p){
    const q=picks(p),after=withQuantity(p,Math.min(MAX_Q,q+1)),consumers=[];
    for(const m of p.moves||[]){
      const before=vector(p,m);if(!before)continue;
      const next=vector(after,m);let changeAt=null,changed=null;
      for(let n=q+1;n<=MAX_Q;n++){
        const v=vector(withQuantity(p,n),m);if(different(before,v)){changeAt=n;changed=v;break;}
      }
      if(changeAt!=null)consumers.push({id:m.id,name:m.name||m.id,before,after:next,nextChangeAt:changeAt,nextChanged:changed});
    }
    const eligible=q<MAX_Q&&consumers.length>0;
    const text=eligible?consumers.slice(0,3).map(c=>c.name+'：'+Object.keys(c.before).map(k=>`${k} ${fmt(c.before[k])}→${fmt(c.after[k])}`).join('、')+
      (!different(c.before,c.after)?`（累積；累計第${c.nextChangeAt}張達下一門檻）`:'')).join('；'):'沒有可增加數量的已學招式，或已達上限';
    return {id:'quantity',eligible,before:q,after:Math.min(MAX_Q,q+1),consumers,text};
  }
  function benefit(p,id){
    if(id==='quantity')return quantityBenefit(p);
    let before,after,label;
    if(id==='heal'){before=p.hp;after=Math.min(p.maxHp,p.hp+p.maxHp*.45);label='生命';}
    else if(id==='atk'){before=p.atk;after=before*1.1;label='攻擊';}
    else if(id==='spd'){before=p.spd;after=before*1.07;label='移速';}
    else if(id==='cd'){before=p.cdMul;after=before*.92;label='冷卻倍率';}
    else if(id==='mag'){before=p.magnet;after=before*1.3;label='拾取半徑';}
    else if(id==='xp'){before=p.xpMul;after=before*1.12;label='經驗倍率';}
    else if(id==='def'){before=p.dmgReduce||0;after=Math.min(.7,before+.06);label='基礎減傷';}
    else if(id==='lifesteal'){before=p.lifestealRate||0;after=before+.01;label='吸血比例';}
    else if(id==='damageSplash'){before=G.DamageSplash?.rate(p)||0;after=before+.1;label='擴散比例';}
    else if(id==='percentHealthDamage'){before=p.percentHealthDamage||0;after=before+.01;label='生命剝奪比例';}
    else if(id==='maxHealthPercent'){before=p.maxHp;after=before*1.1;label='最大生命';}
    else if(id==='selfClone'){before=G.SelfClones?.actors().filter(a=>a.sourceOwner===p).length||0;after=before+1;label='自身分身（非數量卡）';}
    else if(id==='giant'){before=p.anim?.scale||1;after=before*1.25;label='體積（另有生命、移速及攻速取捨）';}
    else return {id,eligible:true,text:''};
    const eligible=Number.isFinite(before)&&Number.isFinite(after)&&after>before;
    // CD benefits are a reduction, not an increase.
    const extra=id==='cd'?'；就緒仍可能等待動作'+(p.moves?.some(m=>m.id==='jjk-yuta-manifest')?'；完全顯現僅縮恢復段，有效期仍8秒':''):'';
    return {id,eligible:id==='cd'?after<before:eligible,before,after,text:`${label} ${fmt(before)}→${fmt(after)}${extra}`};
  }
  function preview(p,card){
    if(card.type==='stat'){
      const b=benefit(p,card.key.slice(5));return b.text?{...card,desc:card.desc+'\n'+b.text,growthPreview:b}:card;
    }
    if(card.type==='up'){
      const id=card.key.slice(3),m=p.moves.find(m=>m.id===id);
      if(m?.jujutsuSkill){
        const next=G.Moves.instance(id,m.lvl+1),parts=[];
        if(m.dmg!==next.dmg)parts.push(`傷害 ${fmt(m.dmg)}→${fmt(next.dmg)}`);
        if(m.range!==next.range)parts.push(`射程 ${fmt(m.range)}→${fmt(next.range)}`);
        if(m.radius!==next.radius)parts.push(`半徑 ${fmt(m.radius)}→${fmt(next.radius)}`);
        return {...card,desc:card.desc+(parts.length?'\n'+parts.join('；'):''),growthMove:m};
      }
    }
    return card;
  }
  for(const id of ['quantity','heal','def']){
    const stat=G.LevelUp.STATS.find(s=>s.id===id);if(!stat)continue;
    const eligible=stat.eligible;stat.eligible=p=>(!eligible||eligible(p))&&benefit(p,id).eligible;
  }
  function choose(pool){
    let r=Math.random()*pool.reduce((sum,c)=>sum+c.w,0),index=pool.length-1;
    for(let i=0;i<pool.length;i++){r-=pool[i].w;if(r<=0){index=i;break;}}
    return pool.splice(index,1)[0];
  }
  function legalOffers(p,n=3){
    const pool=nativeOffer(p,256).filter(c=>c.type!=='stat'||benefit(p,c.key.slice(5)).eligible).map(c=>preview(p,c));
    if(n>=pool.length)return pool;
    const result=[],evo=pool.findIndex(c=>c.type==='evo');if(evo>=0)result.push(pool.splice(evo,1)[0]);
    const stats=pool.filter(c=>c.type==='stat'),reserve=n>1&&stats.length>0?choose(stats):null;
    const limit=n-(reserve?1:0);
    for(let i=0;i<pool.length&&result.length<limit;){
      if(!pool[i].guaranteed){i++;continue;}result.push(pool.splice(i,1)[0]);
    }
    if(reserve){const index=pool.indexOf(reserve);if(index>=0)pool.splice(index,1);result.push(reserve);}
    while(result.length<n&&pool.length)result.push(choose(pool));
    return result;
  }
  G.LevelUp.offer=legalOffers;

  function fullPool(p){
    const c=G.NarutoSkillCatalog,signature=c?.byDex.get(p.mon.dex);
    const ids=signature?[signature.id,...(c.extraPools.get(p.mon.dex)||[])]:G.Moves.poolFor(p.mon);
    return [...new Set([...p.moves.map(m=>m.id),...ids])].filter(id=>G.Moves.BY_ID[id]&&(!p.banned?.has(id)||p.hasMove(id)));
  }
  function canFuseLater(p){
    const ids=fullPool(p),signature=[p.mon.dex,p.maxMoves,ids.join('|'),p.slots.map(g=>g.map(m=>m.id).join('+')).join('|'),p.moves.map(m=>`${m.id}:${!!m.passive}:${!!m.autoCast}`).join('|')].join('/');
    if(probeCache.has(signature))return probeCache.get(signature);
    const probe=new G.Player(p.mon,{}),byId=new Map();
    probe.level=Math.max(p.level,...ids.map(id=>G.Moves.BY_ID[id].learnLevel||1));probe.maxMoves=p.maxMoves;probe.bind={};probe.banned=new Set(p.banned||[]);
    probe.moves=p.moves.map(m=>{const copy={...m};byId.set(m.id,copy);return copy;});
    probe.slots=p.slots.map(g=>g.map(m=>byId.get(m.id)));probe.active=Math.min(p.active,Math.max(0,probe.slots.length-1));
    let possible=false;
    try{for(const id of ids)if(!probe.hasMove(id))probe.addMove(id);possible=!!probe.bondOptions();}
    finally{G.Combat?.clearFields?.(probe);}
    if(probeCache.size>128)probeCache.clear();probeCache.set(signature,possible);return possible;
  }
  function rewardSignature(p){return [p.level,p.bonds,p.hp,p.moves.map(m=>m.id+':'+m.lvl+':'+!!m.evolved).join('|'),JSON.stringify(p.statsTaken||{})].join('/');}
  function validCard(p,card){
    if(card.type==='stat'){
      const stat=G.LevelUp.STATS.find(s=>card.key==='stat:'+s.id);
      return !!stat&&(!stat.max||(p.statsTaken?.[stat.id]||0)<stat.max)&&(!stat.eligible||stat.eligible(p))&&benefit(p,stat.id).eligible;
    }
    if(card.type==='up'){
      const m=p.moves.find(m=>card.key==='up:'+m.id);return !!m&&m.lvl<m.def.maxLvl&&(!card.growthMove||card.growthMove===m);
    }
    if(card.type==='new')return !p.hasMove(card.key.slice(4))&&!p.banned?.has(card.key.slice(4))&&G.Moves.poolFor(p.mon).includes(card.key.slice(4));
    if(card.type==='evo'){
      const m=p.moves.find(m=>card.key==='evo:'+m.id);return !!m&&!!G.Moves.evoInfo(m,p.statsTaken)?.ready;
    }
    return false;
  }
  function bondState(p){
    if(!p||p.dead||!(p.hp>0))return {mode:'bank',reason:'角色目前無法選擇獎勵',options:[]};
    if(p.bondOptions())return {mode:'fusion',reason:'有合法技能群組可融合',options:[]};
    if(canFuseLater(p))return {mode:'bank',reason:'尚可學會能融合的主動招式，羈絆保留',options:[]};
    const signature=rewardSignature(p);let entry=rewardOffers.get(p);
    if(!entry||entry.signature!==signature||entry.spent){entry={signature,options:legalOffers(p,3),spent:false};rewardOffers.set(p,entry);}
    return entry.options.length?{mode:'growth',reason:'目前有效能力無可達的融合，選一次有效成長；不增加角色等級',options:entry.options}:
      {mode:'bank',reason:'目前沒有有效成長選項，羈絆保留',options:[]};
  }
  function applyBondCard(p,card){
    const entry=rewardOffers.get(p);
    if(!entry||entry.spent||!entry.options.includes(card)||entry.signature!==rewardSignature(p)||
      (G.Game.player&&G.Game.player!==p)||p.dead||!(p.hp>0)||!(p.bonds>0)||!validCard(p,card))return false;
    const result=card.apply(p);if(result===false)return false;
    entry.spent=true;p.bonds--;return true;
  }
  G.JujutsuGrowth={benefit,quantityBenefit,preview,legalOffers,bondState,applyBondCard,
    registerQuantityConsumer:(mode,read)=>{customConsumers.set(mode,read);probeCache.clear();}};
})();
