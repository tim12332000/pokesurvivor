/* Classic LF2 2.0a: original move identities, adapted to automatic survival combat. */
(() => {
  'use strict';
  if(G.LF2)return;
  const DEX=30018,source='https://lf2.net/';
  const power={
    'lf2-iceball':{ranges:[500,550,600,650,720],radii:[16,18,20,22,24],counts:[1,2,2,3,3],speed:420,freeze:[1.2,1.3,1.4,1.5,1.6],cap:12},
    'lf2-sword':{ranges:[88,100,112,124,140],radii:[88,100,112,124,140],counts:[1,1,2,2,3],cap:8},
    'lf2-column':{ranges:[260,290,320,350,390],radii:[38,42,46,50,56],counts:[3,3,4,4,5],freeze:[1.2,1.2,1.2,1.2,1.2],cap:12},
    'lf2-whirlwind':{ranges:[480,510,540,570,620],radii:[62,70,78,86,96],counts:[1,1,1,2,2],life:2.7,tick:.22,speed:95,cap:4}
  };
  const rows=[
    ['lf2-iceball','lf2-iceball','冰波 · Ice Blast','ice',1,1.25,48,'向前推出直線飛行的冰波，碰到敵人使其短暫凍結；冰波會被牆與障礙擋住。未持冰劍時，出招空檔會以普通拳擊迎擊近敵。'],
    ['lf2-sword','lf2-sword','冰劍 · Ice Sword','ice',3,1.05,62,'先以原版姿勢召出冰劍，召劍動作本身不造成傷害；之後近敵進入劍程時揮砍，命中使普通敵人凍結1.2秒、強敵0.28秒。冰劍持續保留至退學、死亡或本局結束，劍隨身體出手。'],
    ['lf2-column','lf2-column','冰柱 · Icicles','ice',5,5.6,90,'往前依序升起三根冰柱，沿地面截住敵潮；每根各自命中與凍結，離開柱位的敵人可以避開。'],
    ['lf2-whirlwind','lf2-whirlwind','冰旋風 · Whirlwind','ice',8,8.5,30,'轉身放出往前推進的冰旋風，連續命中並捲動普通敵人；旋風放出後獨立持續，Freeze 可以繼續移動與出招。']
  ];
  const kit=[DEX,rows],ids=rows.map(row=>row[0]),scales=[1,1.2,1.45,1.75,2.1];
  const labels={'lf2-iceball':'冰波','lf2-sword':'揮砍','lf2-column':'冰柱','lf2-whirlwind':'旋風'};
  const shapes={
    'lf2-iceball':['............','......b.....','...b..w..b..','....bwwwb...','...bwwwwwb..','.bbwwwwwwwbb','...bwwwwwb..','....bwwwb...','...b..w..b..','......b.....','............','............'],
    'lf2-sword':['.........bw.','........bww.','.......bww..','......bww...','.....bww....','....bww.....','...bww......','..bbwb......','...bbwb.....','..b..b......','.b..........','............'],
    'lf2-column':['............','.....bw.....','....bwwb....','....bwwb....','..b.bwwb.b..','.bwbbwwbbwb.','.bwbbwwbbwb.','bwwbbwwbbwwb','bwwbbwwbbwwb','bwwbbwwbbwwb','bbbbbbbbbbbb','............'],
    'lf2-whirlwind':['............','..bbbbbbbb..','.bwwwwwwwwb.','...bbbbbbb..','..bwwwwwwb..','....bbbbb...','...bwwwwb...','.....bbb....','....bwwb....','.....bb.....','......b.....','............']
  };
  const catalog=G.NarutoSkillCatalog;
  for(const [id,mode,name,type,learnLevel,cd,dmg,description]of rows){
    const p=power[mode];
    G.Icons.UI[id]={pal:{w:'#e7fcff',b:'#60bbed'},rows:shapes[id],outline:true};
    const ups=scales.slice(1).map((scale,i)=>({
      t:`傷害提高；${labels[mode]}基數 ${p.counts[i]}→${p.counts[i+1]}，${mode==='lf2-sword'?'劍程':'射程'} ${p.ranges[i]}→${p.ranges[i+1]}${mode==='lf2-sword'?'':`，命中半徑 ${p.radii[i]}→${p.radii[i+1]}`}`,
      m:{dmg:scale/scales[i],range:p.ranges[i+1],radius:p.radii[i+1]/p.radii[i],width:p.radii[i+1]/p.radii[i]}
    }));
    const def={id,name,icon:id,type,kind:'melee',digiMode:mode,digimonSkill:true,narutoSkill:true,lf2Skill:true,
      passive:true,autoCast:true,learnLevel,cd,dmg,range:p.ranges[0],radius:p.radii[0],width:p.radii[0]*2,
      count:p.counts[0],speed:p.speed||420,life:p.life||1,arc:1.8,pierce:0,duration:p.life||0,maxLvl:5,ups,
      desc:description+' 自動施放、學習等級、數量與數值成長為本作改編；不占主動槽。',source_url:source};
    G.Moves.BY_ID[id]=def;G.Moves.ALL.push(def);catalog.definitions.set(id,def);
  }
  catalog.byDex.set(DEX,G.Moves.BY_ID[ids[0]]);catalog.extraPools.set(DEX,ids.slice(1));
  catalog.references.set(DEX,{name:'Little Fighter 2 · Freeze (classic 2.0a)',source_url:source});
  const record=G.Naruto.records.get(DEX);record.attack=G.Moves.BY_ID[ids[0]].name;
  Object.assign(record,{lf2:true});Object.assign(G.DEX_BY[DEX],{lf2:true});
  document.querySelectorAll(`[data-naruto-attack="${DEX}"]`).forEach(el=>el.textContent=record.attack);
  let startingRun=false;
  const startRun=G.Game.startRun;
  G.Game.startRun=function(...args){startingRun=true;try{return startRun.apply(this,args);}finally{startingRun=false;}};
  const poolFor=G.Moves.poolFor;
  G.Moves.poolFor=mon=>{
    if(mon.dex!==DEX)return poolFor(mon);
    const level=!startingRun&&G.Game.player?.mon===mon?Math.max(1,G.Game.player.level||1):1;
    return ids.filter(id=>G.Moves.BY_ID[id].learnLevel<=level);
  };
  const addMove=G.Player.prototype.addMove;
  G.Player.prototype.addMove=function(id,...args){
    if(ids.includes(id)){
      if(this.mon?.dex!==DEX||this.level<G.Moves.BY_ID[id].learnLevel||this.hasMove(id))return false;
      this.moves.push(G.Moves.instance(id,1));this.arrange();return true;
    }
    if(this.mon?.dex===DEX)return false;
    return addMove.call(this,id,...args);
  };
  // The shared growth layer reports floor thresholds instead of promising a
  // projectile on every quantity card (one base projectile needs four cards).
  for(const mode of ids)G.JujutsuGrowth?.registerQuantityConsumer(mode,(owner,m)=>{
    const p=G.LF2Freeze?.profile(owner,m);return p?{[labels[mode]]:p.count}:null;
  });
  const skillState=G.RunInsights?.skillState;
  if(skillState)G.RunInsights.skillState=(player,move)=>{
    if(player?.dex!==DEX||!move?.lf2Skill)return skillState(player,move);
    const api=G.LF2Freeze,pose=api?.pose(player),state=api?.stateFor(player);
    if(pose?.m?.id===move.id)return {label:pose.kind==='sword-summon'?'召出冰劍':pose.kind==='punch'?'近身拳擊':'出招中',fraction:0};
    const active=state?.effects?.filter(e=>!e.dead&&e.action?.m.id===move.id);
    if(active?.length)return {label:(move.id==='lf2-whirlwind'?'旋風 ':move.id==='lf2-column'?'冰柱 ':'冰波 ')+active.length,fraction:Math.max(0,Math.min(1,Math.max(...active.map(e=>(e.life-e.age)/Math.max(.01,e.life)))))};
    const t=Math.max(0,move.t||0);
    return {label:t>0?t.toFixed(1)+'s':pose?'待出手':move.id==='lf2-sword'?(state?.swordOwned?'持劍就緒':'待召冰劍'):'就緒',fraction:Math.min(1,t/Math.max(.05,move.cd*(player.cdMul??1)))};
  };
  const article=document.createElement('article');article.className='naruto-skill-entry';
  const title=document.createElement('h3');title.textContent='Freeze 冰人 · 經典 LF2 2.0a';article.append(title);
  const note=document.createElement('p');note.textContent='使用舊版 LF2 像素動作與四招原有概念。移動由玩家控制，招式自動施放；未持冰劍時以普通拳擊接住近身空檔。先學冰波，再逐步選卡學會冰劍、冰柱與冰旋風；召劍與揮劍是分開的動作。';article.append(note);
  for(const id of ids){
    const m=G.Moves.BY_ID[id],h=document.createElement('h4'),p=document.createElement('p'),s=document.createElement('small');
    h.textContent=m.name;p.textContent=m.desc;s.textContent=`Lv.${m.learnLevel} 可學 · 冷卻 ${m.cd} 秒 · 五階成長 · 數量卡上限 ${power[id].cap}`;
    article.append(h,p,s);
  }
  const link=document.createElement('a');link.href=source;link.target='_blank';link.rel='noopener noreferrer';link.textContent='Little Fighter 2 官方網站';article.append(link);
  document.querySelector('#scr-naruto-skills .naruto-skill-entries')?.append(article);
  G.LF2={dex:DEX,kit,power,ids,source};
  if(G.DB.save)G.Naruto.refreshSelection?.();
})();
