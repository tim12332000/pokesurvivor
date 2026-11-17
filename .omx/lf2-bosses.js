/* Classic LF2 hidden fighters: original identities with native survivor growth. */
(() => {
  'use strict';
  if (G.LF2Bosses) return;
  const source='https://lf2.net/', scales=[1,1.2,1.45,1.75,2.1];
  const heroes=[
    {dex:30019,name:'Firzen 冰火人',api:G.LF2Firzen,moves:[
      ['lf2-firzen-cannon','冰火砲 · Firzen Cannon','ice',1,'從手前持續射出冰火砲彈，首發重擊接續連射；砲彈真正飛行，牆與障礙會阻擋。'],
      ['lf2-firzen-disaster','冰火追擊 · Overwhelming Disaster','fire',3,'向上釋出冰火追擊彈，升空後各自追向敵人；火彈與冰彈分別命中，冰彈可凍結普通敵人，強敵時間較短。'],
      ['lf2-firzen-volcano','冰火大爆發 · Arctic Volcano','fire',6,'在周圍釋放原版冰火爆發，覆蓋包圍自己的敵群；每道爆發各有真實命中，離開本體後仍依原動畫收束。']
    ]},
    {dex:30020,name:'Julian 邪鬼',api:G.LF2Julian,moves:[
      ['lf2-julian-skull','骷髏彈 · Skull Blast','psychic',1,'連續射出原版骷髏彈追擊敵人，逐發飛行與命中；近身空檔以拳擊迎擊，朝敵人移動時可接原版衝拳。'],
      ['lf2-julian-uppercut','邪鬼上勾拳 · Uppercut','fighting',3,'以原版抬臂、上勾拳和收勢迎擊近身敵群，只有手臂真正掃過的接觸窗造成傷害。'],
      ['lf2-julian-ball','巨大能量球 · Soul Bomb','psychic',5,'蓄力後射出大型能量球，沿路壓制多名敵人；飛行、命中與消散各自保留原版圖格。'],
      ['lf2-julian-blast','邪鬼大爆炸 · Big Bang','psychic',8,'以原版蓄力和巨大爆發迎擊包圍，爆發真正覆蓋周圍敵人，完整播放釋放到消散。']
    ]}
  ];
  const marks={
    cannon:['............','............','wwb.........','bwwwwb......','..bwwwwwbb..','...bwwwwwwww','...bwwwwwwww','..bwwwwwbb..','bwwwwb......','wwb.........','............','............'],
    orbs:['.....bb.....','....bwwb....','.....bb.....','............','.bb......bb.','bwwb....bwwb','.bb......bb.','............','.....bb.....','....bwwb....','.....bb.....','............'],
    blast:['.....b......','..b..w..b...','...b.w.b....','..bbwwwbb...','.bwwwwwwwb..','bwwwbbwwwb..','.bwwwwwwwb..','..bbwwwbb...','...b.w.b....','..b..w..b...','.....b......','............'],
    skull:['...bbbbbb...','..bwwwwwwb..','.bwwwwwwwwb.','.bwwwwwwwwb.','.bwbwwbwwb..','.bwbwwbwwb..','..bwwwwwwb..','...bwwwwb...','...bwbwb....','...bbbbb....','............','............'],
    fist:['............','....bbbb....','...bwwwwb...','...bwwwwb...','...bwwwwb...','....bwwb....','....bwwb....','....bwwb....','...bwwwwb...','...bwwwwb...','....bbbb....','............']
  };
  const catalog=G.NarutoSkillCatalog,kits=[],owners=new Map(),power={};
  const countLabels={'lf2-firzen-cannon':'連射發數','lf2-firzen-disaster':'追擊彈數','lf2-firzen-volcano':'爆發組數',
    'lf2-julian-skull':'骷髏彈數','lf2-julian-uppercut':'上勾拳次數','lf2-julian-ball':'能量球數','lf2-julian-blast':'大爆發輪次'};
  for (const hero of heroes) {
    if (!hero.api?.specs) throw Error('Classic LF2 combat definitions missing: '+hero.dex);
    const rows=[];
    for (const [id,fallbackName,fallbackType,fallbackLevel,description] of hero.moves) {
      const p=hero.api.specs[id];
      if (!p) throw Error('Classic LF2 skill profile missing: '+id);
      const name=p.name||fallbackName,type=p.type||fallbackType,learnLevel=p.learnLevel??fallbackLevel;
      power[id]=p;
      const ranges=p.ranges,radii=p.radii,counts=p.counts;
      const icon=/skull/.test(id)?'skull':/uppercut/.test(id)?'fist':/disaster/.test(id)?'orbs':/volcano|blast/.test(id)?'blast':'cannon';
      G.Icons.UI[id]={pal:{w:hero.dex===30019?'#fff0c1':'#ddd7ff',b:hero.dex===30019?'#58cbe9':'#8463d5'},rows:marks[icon],outline:true};
      const ups=scales.slice(1).map((scale,i)=>({
        t:`傷害提高；${countLabels[id]}基數 ${counts[i]}→${counts[i+1]}，射程 ${ranges[i]}→${ranges[i+1]}，命中半徑 ${radii[i]}→${radii[i+1]}`,
        m:{dmg:scale/scales[i],range:ranges[i+1],radius:radii[i+1]/radii[i],width:radii[i+1]/radii[i]}
      }));
      const def={id,name,icon:id,type,kind:'melee',digiMode:id,digimonSkill:true,narutoSkill:true,lf2Skill:true,
        passive:true,autoCast:true,learnLevel,cd:p.cd,dmg:p.damage,range:ranges[0],radius:radii[0],width:radii[0]*2,
        count:counts[0],speed:p.speed||420,life:p.life||1,duration:p.life||0,arc:1.9,pierce:0,maxLvl:5,ups,
        desc:(p.desc||description)+' 自動施放、學習等級、數量與數值成長為本作改編；不占主動槽。',source_url:source};
      G.Moves.BY_ID[id]=def;G.Moves.ALL.push(def);catalog.definitions.set(id,def);owners.set(id,hero.dex);
      rows.push([id,id,name,type,learnLevel,p.cd,p.damage,ranges[0],radii[0],def.desc]);
    }
    kits.push([hero.dex,rows]);
    catalog.byDex.set(hero.dex,G.Moves.BY_ID[rows[0][0]]);catalog.extraPools.set(hero.dex,rows.slice(1).map(row=>row[0]));
    catalog.references.set(hero.dex,{name:hero.name+' · classic LF2 2.0a',source_url:source});
    const record=G.Naruto.records.get(hero.dex);record.attack=G.Moves.BY_ID[rows[0][0]].name;record.lf2=true;G.DEX_BY[hero.dex].lf2=true;
    document.querySelectorAll(`[data-naruto-attack="${hero.dex}"]`).forEach(el=>el.textContent=record.attack);
    for (const [id] of rows) G.JujutsuGrowth?.registerQuantityConsumer(id,(owner,move)=>({[countLabels[id]]:hero.api.profile(owner,move).count}));
  }
  const idsFor=dex=>kits.find(row=>row[0]===+dex)?.[1].map(row=>row[0])||[];
  let startingRun=false;
  const startRun=G.Game.startRun;
  G.Game.startRun=function(...args){startingRun=true;try{return startRun.apply(this,args);}finally{startingRun=false;}};
  const poolFor=G.Moves.poolFor;
  G.Moves.poolFor=mon=>{
    const hero=heroes.find(h=>h.dex===mon.dex);if(!hero)return poolFor(mon);
    const level=!startingRun&&G.Game.player?.mon===mon?Math.max(1,G.Game.player.level||1):1;
    return idsFor(mon.dex).filter(id=>G.Moves.BY_ID[id].learnLevel<=level);
  };
  const addMove=G.Player.prototype.addMove;
  G.Player.prototype.addMove=function(id,...args){
    if(owners.has(id)){
      if(this.mon?.dex!==owners.get(id)||this.level<G.Moves.BY_ID[id].learnLevel||this.hasMove(id))return false;
      this.moves.push(G.Moves.instance(id,1));this.arrange();return true;
    }
    if(heroes.some(h=>h.dex===this.mon?.dex))return false;
    return addMove.call(this,id,...args);
  };
  const skillState=G.RunInsights?.skillState;
  if(skillState)G.RunInsights.skillState=(player,move)=>{
    const hero=heroes.find(h=>h.dex===player?.dex);if(!hero||!owners.has(move?.id))return skillState(player,move);
    const pose=hero.api.pose(player),state=hero.api.stateFor(player);
    if(pose?.m?.id===move.id)return {label:pose.kind==='punch'?'近身拳擊':pose.kind==='soul-punch'?'衝拳':'出招中',fraction:0};
    const active=state?.effects?.filter(e=>!e.dead&&e.action?.m.id===move.id);
    if(active?.length)return {label:'作用中 '+active.length,fraction:Math.max(0,Math.min(1,Math.max(...active.map(e=>(e.life-e.age)/Math.max(.01,e.life)))))};
    const t=Math.max(0,move.t||0);return {label:t>0?t.toFixed(1)+'s':pose?'待出手':'就緒',fraction:Math.min(1,t/Math.max(.05,move.cd*(player.cdMul??1)))};
  };
  for(const hero of heroes){
    const article=document.createElement('article');article.className='naruto-skill-entry';
    const title=document.createElement('h3');title.textContent=hero.name+' · 經典 LF2 2.0a';article.append(title);
    for(const id of idsFor(hero.dex)){
      const m=G.Moves.BY_ID[id],heading=document.createElement('h4'),description=document.createElement('p'),stats=document.createElement('small');
      heading.textContent=m.name;description.textContent=m.desc;stats.textContent=`Lv.${m.learnLevel} 可學 · 冷卻 ${m.cd} 秒 · 五階成長`;article.append(heading,description,stats);
    }
    const link=document.createElement('a');link.href=source;link.target='_blank';link.rel='noopener noreferrer';link.textContent='Little Fighter 2 官方網站';article.append(link);
    document.querySelector('#scr-naruto-skills .naruto-skill-entries')?.append(article);
  }
  G.LF2Bosses={kits,idsFor,power,owners,source};
  if(G.DB.save)G.Naruto.refreshSelection?.();
})();
