/* Sendai crossover registration. Numbers and automatic casting are game adaptations. */
(() => {
  if (G.Jujutsu) return;
  const source='https://jujutsukaisen.jp/news/20260322_02.php';
  // Use the native pixel-icon vocabulary, with a different silhouette per skill.
  const marks={
    'jjk-yuta':['..........ww','.........wwb','........wwb.','.......wwb..','......wwb...','.....wwb....','....wwb.....','...wwb......','..gpbg......','...gpg......','..pp........','.pp.........'],
    'jjk-yuta-rika':['...wwwww....','..wpppppw...','.wppwwwppw..','wppwkpkwppw.','wppwwwwwppw.','.wppkkkppw..','..wpppppw...','.wpppppppw..','wwpppppppww.','w.ppwwwpp.w.','..ww...ww...','..w.....w...'],
    'jjk-yuta-speech':['...wwwww....','..wpppppw...','.wpppppppw..','wpwppppwpw..','wppppppppw..','.wppppppw...','..wkkkkw....','...wwww.....','.bb....bb...','b..bbbb..b..','.bb....bb...','...bbbb.....'],
    'jjk-yuta-manifest':['.....w......','....bwb.....','.....w......','...ggggg....','..gwwwwwg...','.gww...wwg..','.gw.....wg..','.gw.....wg..','.gww...wwg..','..gwwwwwg...','...ggggg....','............'],
    'jjk-ryu':['......www...','.....wwbww..','......www...','......bbb...','......bbb...','.....bwwb...','...kkbwwbkk.','..kppppppppk','..kpkkkkkppk','...kppppppk.','....kppppk..','.....kkkk...'],
    'jjk-ryu-spread':['.w....w...w.','.bw...w..wb.','..bw..w.wb..','...bw.wbw...','....bwww....','.....www....','.....bbb....','....bwwwb...','...kpppppk..','...kpkkkpk..','....kpppk...','.....kkk....'],
    'jjk-ryu-impact':['.....b......','..b..w..b...','...b.w.b....','..bbwwwbb...','.bwwwwwwwb..','bwwwggwwwb..','.bwwwwwwwb..','..bbwwwbb...','...b.w.b....','..b..w..b...','.....b......','............'],
    'jjk-ryu-maximum':['....wwww....','...wwwwww...','...bwwwwb...','...bwwwwb...','...bwwwwb...','..bbwwwwbb..','..bbwwwwbb..','.kkbwwwwbkk.','kppppppppppk','kpkkkkkkkkpk','.kppppppppk.','..kkkkkkkk..'],
    'jjk-uro':['.bbbbbbbb...','.bwwwwwwwb..','..bwwwwwwwb.','...bwwwwwwb.','....bwwwbb..','...bwwwb....','..bwwwb.....','.bwwwb......','bwwwb.......','.bwwwbbbb...','..bwwwwwwb..','...bbbbbbb..'],
    'jjk-uro-thin-ice':['...b...b....','..bwb.bwb...','.bwwwbwwwb..','bwwpwwwwwb..','bwwwpwwwb...','.bwwwpwb....','..bwwwp.....','...bwb.p.b..','....b...p...','..b...b.....','...b....b...','............'],
    'jjk-uro-screen':['..bbbbbbb...','.bwwwwwwwb..','bwwwbbbwwwb.','bwwb...bwwb.','.bwb.w..bwb.','..bb.ww..bb.','.....www....','....wwww....','.....ww.....','....ww......','...ww.......','..ww........'],
    'jjk-uro-collapse':['...bbbbbb...','..bwwwwwwb..','.bwwwbbwwwb.','bwwwb..bwwwb','bwwb....bwwb','.bwwb..bwwb.','..bwwbbwwb..','...bwwwwb...','..bwwbbwwb..','.bwwb..bwwb.','..bb....bb..','............']
  };
  const palette={w:'#f5fbff',b:'#67d9ef',p:'#a995d7',g:'#e9c66c'};
  for(const [id,rows] of Object.entries(marks))G.Icons.UI[id]={pal:palette,rows,outline:true};
  const kits=[
    [30013,[
      ['jjk-yuta','yuta-blade','咒力刀斬','fighting',1,1,30,125,90,'向前揮刀，命中前跟隨走位，斬擊近身扇形內敵人。'],
      ['jjk-yuta-rika','yuta-rika','里香協擊','fighting',3,6,100,300,105,'里香優先追擊刀斬範圍外的敵人；有限追近移動強敵，起拳後鎖定落點重擊。刀術接力標記優先。'],
      ['jjk-yuta-speech','yuta-speech','咒言・別動','psychic',6,8,35,160,160,'90內有敵人，或範圍內至少三名敵人時，咒言震懾周圍；首領僅短暫受控。'],
      ['jjk-yuta-manifest','yuta-manifest','里香完全顯現','psychic',9,18,0,300,160,'遇敵群或強敵才顯現6秒，立即刷新里香一次；新施放傷害+50／60／70／80／100%，里香追加一次重擊。結束後恢復12秒，三／五階為10.5／9秒；冷卻卡有效。']
    ]],
    [30014,[
      ['jjk-ryu','jjk-ryu','花崗岩砲','psychic',1,1.8,42,360,14,'蓄力0.22秒，射出長距窄幅貫穿砲；學會全力砲後，每次真正命中蓄一格能量。'],
      ['jjk-ryu-spread','jjk-ryu-spread','散射咒力砲','psychic',3,5,30,200,12,'蓄力0.35秒，向短距廣角發射三顆砲彈；有飛行時間，碰到首個敵人或障礙即停止。數量強化增加砲彈，同次不重複直擊同一敵人。'],
      ['jjk-ryu-impact','jjk-ryu-impact','咒力爆破','psychic',6,7,100,300,90,'優先鎖定最密集的可達敵群，預告0.45秒後在固定爆點範圍引爆；敵人可離開爆點。'],
      ['jjk-ryu-maximum','jjk-ryu-maximum','全力咒力砲','psychic',9,5.4,200,760,72,'三次普通砲命中蓄滿後，蓄力0.75秒轟出巨型貫穿主砲（基傷×1.5），再連射4／5／6／7／8輪重砲（每輪×0.55）。數量卡增加連轟，最多16輪追加；射程760→1040、主砲半徑72→128，連轟時仍可移動。']
    ]],
    [30015,[
      ['jjk-uro','uro-sky','空面打擊','psychic',1,1.25,20,125,90,'近身掌擊扭曲空面，推開前方125內普通敵人；強敵不被搬動。'],
      ['jjk-uro-thin-ice','uro-thin-ice','宇守羅彈','psychic',3,4.8,72,250,110,'擊碎前方空面，造成大範圍扇形傷害。'],
      ['jjk-uro-screen','uro-screen','天空幕','psychic',6,9,0,90,82,'偵測即將來襲的敵彈才展開2.3秒空面，不打斷正在施放的攻擊。反射5／6／7／8／9顆，不阻擋近戰。'],
      ['jjk-uro-collapse','uro-collapse','空面震落','psychic',9,8,112,280,110,'鎖定最密集的可達敵群，同密度優先遠處；0.55秒後在固定爆點碎裂並減速，首領減速較弱。']
    ]]
  ];
  // Functional ranks spend the existing upgrade choice; they are not free talents.
  const functional={
    'jjk-yuta':{base:{bladeArc:Math.PI*2/3},third:{relayMarkDuration:1.2},fifth:{bladeArc:2.5},text3:'刀斬標記1.2秒，里香優先追擊該目標',text5:'近身斬擊角擴至約143度'},
    'jjk-yuta-rika':{base:{rikaSpeed:520,rikaReturnSpeed:600},third:{rikaSpeed:650},fifth:{radius:1.2,rikaReturnSpeed:720},text3:'里香接近速度520→650',text5:'重擊半徑105→126，返回速度600→720'},
    'jjk-yuta-speech':{base:{speechDuration:1.2},third:{speechDuration:1.5},fifth:{radius:1.15,range:184},text3:'普通敵人移動限制1.2→1.5秒，首領抗性不變',text5:'咒言半徑160→184'},
    'jjk-yuta-manifest':{base:{recovery:12},third:{recovery:10.5},fifth:{recovery:9},text3:'顯現結束後基礎恢復12→10.5秒',text5:'顯現結束後基礎恢復10.5→9秒'},
    'jjk-ryu':{third:{targetPolicy:'elite'},fifth:{range:414},text3:'優先可達精英，無精英才選最近敵人',text5:'穿線射程360→414'},
    'jjk-ryu-spread':{base:{baseCount:3,spreadStep:.65},third:{spreadStep:.8},fifth:{baseCount:4},text3:'相鄰砲彈角度0.65→0.80弧度',text5:'基礎砲彈3→4，數量乘算後最多9顆'},
    'jjk-ryu-impact':{base:{impactTargetPolicy:'cluster'},third:{radius:1.2},fifth:{range:330},text3:'爆心半徑90→108',text5:'群聚索敵射程300→330，爆點仍於起手鎖定'},
    'jjk-ryu-maximum':{base:{barrageBase:4},third:{firstTargetBonus:.15},fifth:{range:1040},text3:'追加6輪重砲；主砲半徑96、射程880，首個目標傷害+15%',text5:'追加8輪重砲；主砲半徑128、射程1040，數量可強化至16輪'},
    'jjk-uro':{base:{skyKnock:30},third:{arc:1.3/1.1},fifth:{skyKnock:44},text3:'近身掌擊角1.10→1.30弧度',text5:'普通敵人推退30→44，特殊敵人不搬動'},
    'jjk-uro-thin-ice':{third:{arc:2.1/1.9},fifth:{thinSlow:.25,thinSlowDuration:.45},text3:'碎面扇角1.9→2.1弧度',text5:'普通敵人減速25%持續0.45秒，首領僅弱減速'},
    'jjk-uro-screen':{base:{threatOnly:true,threatHorizon:.55},third:{threatHorizon:.8,reflectRefresh:true},fifth:{counterBonus:.15,counterDuration:3},text3:'預測0.80秒敵彈；首次反射刷新宇守羅彈，三秒內優先反擊射程內可達的原射手',text5:'真正反射後3秒內，下次宇守羅彈傷害+15%；每幕一次'},
    'jjk-uro-collapse':{third:{radius:1.15},fifth:{collapseSlow:.60,slowDuration:.8},text3:'震落半徑110→126.5',text5:'普通敵人減速60%持續0.8秒，首領效果較弱'}
  };
  const owners=new Map(),catalog=G.NarutoSkillCatalog;
  for(const [dex,rows] of kits){
    const ids=[];
    for(const [id,mode,name,type,learnLevel,cd,dmg,range,radius,desc] of rows){
      const scales=[1,1.2,1.45,1.75,2.1];
      const ups=scales.slice(1).map((scale,i)=>({t:dmg?'傷害提高':mode==='uro-screen'?'可反射飛彈 +1':`完全顯現傷害加成 ${[60,70,80,100][i]}%`,m:dmg?{dmg:scale/scales[i]}:{}}));
      const growth=functional[id];
      for(const [index,changes,text] of [[1,growth.third,growth.text3],[3,growth.fifth,growth.text5]]){
        Object.assign(ups[index].m,changes);ups[index].t+='；'+text;
      }
      if(mode==='jjk-ryu-maximum'){
        const radii=[72,84,96,108,128],ranges=[760,820,880,940,1040];
        for(let i=0;i<ups.length;i++){
          Object.assign(ups[i].m,{radius:radii[i+1]/radii[i],width:radii[i+1]/radii[i],range:ranges[i+1],barrageBase:5+i});
          ups[i].t+=`；追加${5+i}輪重砲，主砲半徑${radii[i+1]}、射程${ranges[i+1]}`;
        }
      }
      const def={id,name,icon:id,type,kind:dmg?'melee':'buff',digiMode:mode,digimonSkill:true,narutoSkill:true,jujutsuSkill:true,
        passive:true,autoCast:true,learnLevel,cd,dmg,range,radius,width:radius*2,speed:520,life:1,count:1,arc:1.6,pierce:0,
        duration:mode==='yuta-manifest'?6:mode==='uro-screen'?2.3:0,maxLvl:5,ups,...growth.base,
        desc:desc+' 自動施放，不占主動槽。',source_url:source};
      if(mode==='uro-sky')def.arc=1.1;
      if(mode==='uro-thin-ice'){def.arc=1.9;def.source_url='https://kotodaman.jp/info/detail/081584KEuwsxffR4nq.html';}
      G.Moves.BY_ID[id]=def;G.Moves.ALL.push(def);catalog.definitions.set(id,def);owners.set(id,dex);ids.push(id);
    }
    catalog.byDex.set(dex,G.Moves.BY_ID[ids[0]]);catalog.extraPools.set(dex,ids.slice(1));
    catalog.references.set(dex,{name:G.DEX_BY[dex].name,source_url:source});
    G.Naruto.records.get(dex).attack=G.Moves.BY_ID[ids[0]].name;
    document.querySelectorAll(`[data-naruto-attack="${dex}"]`).forEach(el=>el.textContent=G.Moves.BY_ID[ids[0]].name);
  }
  const guide=document.querySelector('#scr-naruto-skills .naruto-skill-entries');
  if(guide){
    for(const [dex,rows] of kits){
      const article=document.createElement('article');article.className='naruto-skill-entry';
      const title=document.createElement('h3');title.textContent=G.Naruto.records.get(dex).chinese;article.append(title);
      for(const [id] of rows){
        const def=G.Moves.BY_ID[id],heading=document.createElement('h4'),description=document.createElement('p'),stats=document.createElement('small');
        heading.textContent=def.name;description.textContent=def.desc;
        stats.textContent=`Lv.${def.learnLevel} 可學 · ${id==='jjk-yuta-manifest'?'顯現6秒・結束後恢復12／10.5／9秒（冷卻卡只縮恢復）':`冷卻 ${def.cd} 秒`} · 可升至 Lv.${def.maxLvl}`;
        article.append(heading,description,stats);
        const growth=document.createElement('p');growth.textContent=`三階：${functional[id].text3}。五階：${functional[id].text5}。`;article.append(growth);
      }
      const link=document.createElement('a');link.href=source;link.target='_blank';link.rel='noopener noreferrer';link.textContent='官方動畫參考';article.append(link);guide.append(article);
    }
    document.querySelector('#scr-naruto-skills h2').textContent='技能圖鑑與來源';
    document.getElementById('naruto-skill-guide').textContent='技能圖鑑與來源';
  }
  let startingRun=false;
  const startRun=G.Game.startRun;
  G.Game.startRun=function(...args){startingRun=true;try{return startRun.apply(this,args);}finally{startingRun=false;}};
  const poolFor=G.Moves.poolFor;
  G.Moves.poolFor=mon=>{
    const kit=kits.find(([dex])=>dex===mon.dex);
    if(!kit)return poolFor(mon);
    const p=G.Game.player,level=!startingRun&&p?.mon===mon?Math.max(1,p.level||1):1;
    return kit[1].filter(row=>row[4]<=level).map(row=>row[0]);
  };
  const addMove=G.Player.prototype.addMove;
  G.Player.prototype.addMove=function(id,...args){
    const owner=owners.get(id);
    if(owner){
      const def=G.Moves.BY_ID[id];
      if(this.mon?.dex!==owner||this.level<def.learnLevel||this.hasMove(id))return false;
      this.moves.push(G.Moves.instance(id,1));this.arrange();return true;
    }
    if(kits.some(([dex])=>dex===this.mon?.dex))return false;
    return addMove.call(this,id,...args);
  };
  G.Jujutsu={kits,owners,source,functional};
})();
