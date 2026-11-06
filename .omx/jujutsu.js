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
    'jjk-yuta-resonance':['w.........w.','.w.......w..','..w..p..w...','...wwpww....','....www.....','..ppwwwpp...','.ppwwwwwpp..','..ppwwwpp...','....www.....','...ww.ww....','..w.....w...','.w.......w..'],
    'jjk-yuta-love':['............','pp..........','pwwb........','.pwwwbb.....','..pwwwwwbbbb','...pwwwwwwww','...pwwwwwwww','..pwwwwwbbbb','.pwwwbb.....','pwwb........','pp..........','............'],
    'jjk-ryu':['......www...','.....wwbww..','......www...','......bbb...','......bbb...','.....bwwb...','...kkbwwbkk.','..kppppppppk','..kpkkkkkppk','...kppppppk.','....kppppk..','.....kkkk...'],
    'jjk-ryu-spread':['.w....w...w.','.bw...w..wb.','..bw..w.wb..','...bw.wbw...','....bwww....','.....www....','.....bbb....','....bwwwb...','...kpppppk..','...kpkkkpk..','....kpppk...','.....kkk....'],
    'jjk-ryu-ring':['...bbbbbb...','..bwwwwwwb..','.bww....wwb.','bww......wwb','bw...pp...wb','bw..pwwp..wb','bw..pwwp..wb','bw...pp...wb','bww......wwb','.bww....wwb.','..bwwwwwwb..','...bbbbbb...'],
    'jjk-ryu-impact':['.....b......','..b..w..b...','...b.w.b....','..bbwwwbb...','.bwwwwwwwb..','bwwwggwwwb..','.bwwwwwwwb..','..bbwwwbb...','...b.w.b....','..b..w..b...','.....b......','............'],
    'jjk-ryu-maximum':['....wwww....','...wwwwww...','...bwwwwb...','...bwwwwb...','...bwwwwb...','..bbwwwwbb..','..bbwwwwbb..','.kkbwwwwbkk.','kppppppppppk','kpkkkkkkkkpk','.kppppppppk.','..kkkkkkkk..'],
    'jjk-uro':['.bbbbbbbb...','.bwwwwwwwb..','..bwwwwwwwb.','...bwwwwwwb.','....bwwwbb..','...bwwwb....','..bwwwb.....','.bwwwb......','bwwwb.......','.bwwwbbbb...','..bwwwwwwb..','...bbbbbbb..'],
    'jjk-uro-thin-ice':['...b...b....','..bwb.bwb...','.bwwwbwwwb..','bwwpwwwwwb..','bwwwpwwwb...','.bwwwpwb....','..bwwwp.....','...bwb.p.b..','....b...p...','..b...b.....','...b....b...','............'],
    'jjk-uro-screen':['..bbbbbbb...','.bwwwwwwwb..','bwwwbbbwwwb.','bwwb...bwwb.','.bwb.w..bwb.','..bb.ww..bb.','.....www....','....wwww....','.....ww.....','....ww......','...ww.......','..ww........'],
    'jjk-uro-collapse':['...bbbbbb...','..bwwwwwwb..','.bwwwbbwwwb.','bwwwb..bwwwb','bwwb....bwwb','.bwwb..bwwb.','..bwwbbwwb..','...bwwwwb...','..bwwbbwwb..','.bwwb..bwwb.','..bb....bb..','............'],
    'jjk-uro-echo':['b.........b.','.b.......b..','..b..w..b...','...bw.wb....','....bwb.....','...bw.wb....','..bw...wb...','.bw..w..wb..','..bw...wb...','...bw.wb....','....bwb.....','.....w......']
  };
  const palette={w:'#f5fbff',b:'#67d9ef',p:'#a995d7',g:'#e9c66c'};
  for(const [id,rows] of Object.entries(marks))G.Icons.UI[id]={pal:palette,rows,outline:true};
  const kits=[
    [30013,[
      ['jjk-yuta','yuta-blade','咒力刀斬','fighting',1,1,30,125,90,'向前揮刀，命中前跟隨走位，斬擊近身扇形內敵人。'],
      ['jjk-yuta-rika','yuta-rika','里香協擊','fighting',3,4,100,440,160,'學會後里香常駐協戰，每次追擊連打4→8拳，數量卡至16拳；擊倒目標後接續追打可達敵人，終擊更重。完全顯現時巨大化、基礎拳數加倍至24拳，逐拳接乙骨刀斬。'],
      ['jjk-yuta-speech','yuta-speech','咒言・別動','psychic',6,8,35,240,240,'近身壓力或敵群來襲時喝停240→320範圍內敵人：普通敵人2→2.8秒停止移動、新攻擊、施法與接觸傷害，強敵0.7→1秒；已飛出的敵彈仍危險。可與里香連拳並行。'],
      ['jjk-yuta-love','yuta-love','純愛砲','psychic',8,9,100,600,38,'里香短暫完整顯形，與乙骨共同蓄力0.55秒；手部與里香口部咒力匯成同一砲道，雙人各自造成真傷害，連續3→7段，數量卡最多12段；射程600→840、砲道半徑38→70。等待協擊收勢後出砲，可邊移動邊轟擊；完全顯現期間享有傷害加成。獨立短暫顯形與多段脈衝為本作改編，不附送完全顯現增益。'],
      ['jjk-yuta-manifest','yuta-manifest','里香完全顯現','psychic',9,16,0,600,160,'遇敵群或強敵顯現8秒，刷新里香一次，傷害+50→100%，刀拳雙人連打。每次顯現待連段收勢後，乙骨與同一里香短蓄0.55秒，從兩個起點各放出一道寬幅貫穿咒力，射程600→840；未學協擊也可放出，沒有免費拳擊。結束後恢復8→6秒，冷卻卡有效。'],
      ['jjk-yuta-resonance','yuta-resonance','協戰共鳴','fighting',12,0,80,240,240,'被動：里香終結重擊真正命中後，乙骨接一記寬幅共鳴終擊；半徑240→360。等待當前身體動作結束，不遞迴觸發。']
    ]],
    [30014,[
      ['jjk-ryu','jjk-ryu','花崗岩砲','psychic',1,1.8,42,360,14,'蓄力0.22秒，射出長距窄幅貫穿砲；學會全力砲後，每次真正命中蓄一格能量。'],
      ['jjk-ryu-spread','jjk-ryu-spread','散射咒力砲','psychic',3,5,30,800,12,'蓄力0.35秒，額前噴出8→10發咒力砲；先升空0.26秒，再各自迴旋0.6～1.15秒，結束後才分配當下活敵並俯衝追蹤。索敵800→1120、實際追擊航程1280→1792。第一張數量卡8→10發，最多18發；每發獨立命中一次，多發可打同一敵人。牆與障礙會截斷追擊。學會全力砲後，每次施放真正命中最多蓄一格；升空迴旋追蹤是本作演出改編。'],
      ['jjk-ryu-ring','jjk-ryu-ring','花崗岩砲・圓環','psychic',5,6.5,48,112,18,'近敵來襲時蓄力0.32秒，額前砲束彎曲成繞身圓環，連續4→8輪真實環帶切擊。數量卡第一張4→5輪，最多16輪；環半徑112→180、砲道半寬18→30。可移動，不附帶無敵、控場或擋彈；牆會截斷砲道。學會全力砲後，每次施放真正命中最多蓄一格。圓環繞身取自動畫，輪次與成長為本作改編。'],
      ['jjk-ryu-impact','jjk-ryu-impact','咒力爆破','psychic',6,7,100,300,90,'優先鎖定最密集的可達敵群，預告0.45秒後在固定爆點範圍引爆；敵人可離開爆點。學會全力砲後，每次施放真正命中最多蓄一格。'],
      ['jjk-ryu-maximum','jjk-ryu-maximum','全力咒力砲','psychic',9,5.4,200,760,72,'普通砲、散射、圓環或爆破共三次施放命中蓄滿後，蓄力0.75秒轟出巨型貫穿主砲（基傷×1.5），再連射4／5／6／7／8輪重砲（每輪×0.55）。數量卡增加連轟，最多16輪追加；射程760→1040、主砲半徑72→128，連轟時仍可移動。'],
    ]],
    [30015,[
      ['jjk-uro','uro-sky','空面打擊','psychic',1,1.25,20,180,90,'近身掌擊扭曲空面，推開前方180→260內普通敵人；強敵不被搬動。'],
      ['jjk-uro-thin-ice','uro-thin-ice','宇守羅彈','psychic',3,4.8,72,340,110,'抓裂大片天空，連續4→8波真實扇形碎面；數量卡至16波，射程340→540。首波與末波更強，隨走位逐波追蹤目標，目標倒下後轉向可達敵潮。'],
      ['jjk-uro-screen','uro-screen','天空幕','psychic',6,9,0,600,110,'敵彈或近身攻擊來襲時展開3.5→4.5秒空面，偏折接觸攻擊；敵彈繞身一圈再射回敵人。容量12→28，數量卡至64，強敵近身攻擊消耗兩份且不被搬動。首次真攔截接4→8波獨立反擊、數量至16波，不打斷身體攻擊。'],
      ['jjk-uro-collapse','uro-collapse','空面震落','psychic',9,8,112,600,210,'鎖定敵群後連續4→8波巨型破裂、數量至16波，半徑210→340。首末波減速，首領較弱；手勢結束後裂區繼續。'],
      ['jjk-uro-echo','uro-echo','裂面殘響','psychic',12,0,40,180,90,'被動：身體招式末波真正命中後，在該處追加2→4次固定裂面殘響，數量卡至8次。獨立持續，不再觸發殘響或反擊。']
    ]]
  ];
  // Shared combat profiles also drive card previews; new power is real geometry
  // and contact count, not a separate decorative progression.
  const power={
    ryu:{ringRadii:[112,128,144,160,180],ringWidths:[18,21,24,27,30],ringBases:[4,5,6,7,8],ringCap:16,ringInterval:.22,ringCharge:.32,ringCd:6.5},
    yuta:{rikaBases:[4,5,6,7,8],rikaCap:16,fullCap:24,rikaRanges:[440,480,520,560,600],rikaRadii:[160,180,200,220,250],rikaSpeeds:[640,700,760,820,880],normalHeights:[88,91,94,97,100],fullHeights:[156,162,168,174,180],rikaCd:4,fullRikaCd:2.4,manifestDuration:8,recoveries:[8,7.5,7,6.5,6],duetRanges:[180,200,220,240,260],resonanceRadii:[240,270,300,330,360]},
    uro:{palmRanges:[180,200,220,240,260],palmArcs:[1.6,1.7,1.8,1.9,2],waveBases:[4,5,6,7,8],waveCap:16,thinRanges:[340,380,430,480,540],thinArcs:[2.5,2.7,2.9,3.1,3.3],collapseRange:600,collapseRadii:[210,240,270,300,340],screenRadii:[110,120,130,140,150],screenBudgets:[12,16,20,24,28],screenCap:64,screenDurations:[3.5,3.75,4,4.25,4.5],counterRange:600,counterRadii:[130,150,170,190,210],echoBases:[2,2,3,3,4],echoCap:8}
  };
  Object.assign(power.ryu,{scatterBases:[8,8,8,8,10],scatterCap:18,scatterRanges:[800,860,920,1000,1120],scatterSpeeds:[620,650,680,720,760]});
  Object.assign(power.yuta,{speechRadii:[240,260,280,300,320],speechDurations:[2,2.2,2.4,2.6,2.8],speechBossDurations:[.7,.775,.85,.925,1]});
  Object.assign(power.yuta,{releaseRanges:[600,660,720,780,840],releaseRadii:[38,46,54,62,70],releaseDamage:[150,190,230,270,320],releaseCharge:.55});
  Object.assign(power.yuta,{loveBases:[3,4,5,6,7],loveCap:12,loveInterval:.12});
  // Functional ranks spend the existing upgrade choice; they are not free talents.
  const functional={
    'jjk-yuta':{base:{bladeArc:Math.PI*2/3},third:{relayMarkDuration:1.2},fifth:{bladeArc:2.5},text3:'刀斬標記1.2秒，里香優先追擊該目標',text5:'近身斬擊角擴至約143度'},
    'jjk-yuta-rika':{base:{rikaSpeed:640,rikaReturnSpeed:800,comboBase:4},third:{rikaSpeed:760},fifth:{rikaReturnSpeed:960},text3:'普通6拳／顯現12拳基數，重擊半徑200',text5:'普通8拳／顯現16拳基數，重擊半徑250，數量上限16／24拳'},
    'jjk-yuta-speech':{base:{speechDuration:2,speechBossDuration:.7},third:{},fifth:{},text3:'喝停半徑280，普通敵人2.4秒／強敵0.85秒',text5:'喝停半徑320，普通敵人2.8秒／強敵1秒'},
    'jjk-yuta-love':{base:{},third:{},fifth:{},text3:'基礎5段雙源貫穿，射程720、每路半徑54',text5:'基礎7段雙源貫穿，射程840、每路半徑70，數量卡最多12段'},
    'jjk-yuta-manifest':{base:{recovery:8},third:{recovery:7},fifth:{recovery:6},text3:'顯現後基礎恢復7秒',text5:'顯現後基礎恢復6秒'},
    'jjk-yuta-resonance':{third:{radius:1.25,range:300},fifth:{radius:1.2,range:360},text3:'共鳴終擊半徑300',text5:'共鳴終擊半徑360'},
    'jjk-ryu':{third:{targetPolicy:'elite'},fifth:{range:414},text3:'優先可達精英，無精英才選最近敵人',text5:'穿線射程360→414'},
    'jjk-ryu-spread':{base:{baseCount:8},third:{},fifth:{baseCount:10},text3:'基礎8發升空迴旋砲，索敵920、追擊航程1472',text5:'基礎10發，索敵1120、追擊航程1792，數量卡最多18發'},
    'jjk-ryu-ring':{base:{ringBase:4},third:{},fifth:{},text3:'基礎6輪繞身切擊，環半徑144、砲道半寬24',text5:'基礎8輪繞身切擊，環半徑180、砲道半寬30，數量卡最多16輪'},
    'jjk-ryu-impact':{base:{impactTargetPolicy:'cluster'},third:{radius:1.2},fifth:{range:330},text3:'爆心半徑90→108',text5:'群聚索敵射程300→330，爆點仍於起手鎖定'},
    'jjk-ryu-maximum':{base:{barrageBase:4},third:{firstTargetBonus:.15},fifth:{range:1040},text3:'追加6輪重砲；主砲半徑96、射程880，首個目標傷害+15%',text5:'追加8輪重砲；主砲半徑128、射程1040，數量可強化至16輪'},
    'jjk-uro':{base:{skyKnock:30},third:{},fifth:{skyKnock:44},text3:'掌擊射程220、扇角1.8',text5:'掌擊射程260，普通敵人推退44'},
    'jjk-uro-thin-ice':{base:{waveBase:4},third:{},fifth:{thinSlow:.25,thinSlowDuration:.45},text3:'6波碎面，射程430、扇角2.9',text5:'8波碎面，射程540、扇角3.3，首末波弱減速'},
    'jjk-uro-screen':{base:{threatOnly:true,threatHorizon:.55,counterBase:4,reflectBudget:12},third:{threatHorizon:.8},fifth:{},text3:'6波反擊、反射20顆，預測0.8秒敵彈',text5:'8波反擊、反射28顆，空面持續4.5秒'},
    'jjk-uro-collapse':{base:{waveBase:4},third:{},fifth:{collapseSlow:.60,slowDuration:.8},text3:'6波巨裂，半徑270',text5:'8波巨裂，半徑340，普通敵人首末波減速60%'},
    'jjk-uro-echo':{base:{echoBase:2},third:{echoBase:3},fifth:{echoBase:4},text3:'基礎3次殘響',text5:'基礎4次殘響，數量卡最多8次'}
  };
  const ladders={
    'jjk-ryu-spread':{range:power.ryu.scatterRanges,speed:power.ryu.scatterSpeeds,baseCount:power.ryu.scatterBases},
    'jjk-ryu-ring':{range:power.ryu.ringRadii,radius:power.ryu.ringWidths,ringBase:power.ryu.ringBases},
    'yuta-speech':{range:power.yuta.speechRadii,radius:power.yuta.speechRadii,speechDuration:power.yuta.speechDurations,speechBossDuration:power.yuta.speechBossDurations},
    'yuta-rika':{range:power.yuta.rikaRanges,radius:power.yuta.rikaRadii,rikaSpeed:power.yuta.rikaSpeeds,comboBase:power.yuta.rikaBases},
    'yuta-love':{range:power.yuta.releaseRanges,radius:power.yuta.releaseRadii},
    'yuta-manifest':{duration:[8,8,8,8,8],recovery:power.yuta.recoveries},
    'yuta-resonance':{range:power.yuta.resonanceRadii,radius:power.yuta.resonanceRadii},
    'uro-sky':{range:power.uro.palmRanges,arc:power.uro.palmArcs},
    'uro-thin-ice':{range:power.uro.thinRanges,arc:power.uro.thinArcs,waveBase:power.uro.waveBases},
    'uro-screen':{range:[600,600,600,600,600],radius:power.uro.screenRadii,reflectBudget:power.uro.screenBudgets,counterBase:power.uro.waveBases,duration:power.uro.screenDurations},
    'uro-collapse':{range:[600,600,600,600,600],radius:power.uro.collapseRadii,waveBase:power.uro.waveBases},
    'uro-echo':{echoBase:power.uro.echoBases}
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
      if(mode==='jjk-ryu-spread')for(let i=0;i<ups.length;i++){
        const c=power.ryu;
        ups[i].t=`傷害提高；${c.scatterBases[i+1]}發升空迴旋砲，索敵${c.scatterRanges[i+1]}、追擊航程${c.scatterRanges[i+1]*1.6}`;
      }
      if(mode==='jjk-ryu-ring')for(let i=0;i<ups.length;i++){
        const c=power.ryu;
        ups[i].t=`傷害提高；基礎${c.ringBases[i+1]}輪繞身切擊，環半徑${c.ringRadii[i+1]}、砲道半寬${c.ringWidths[i+1]}`;
      }
      const ladder=ladders[mode];
      if(ladder)for(const [key,values]of Object.entries(ladder))for(let i=0;i<ups.length;i++){
        ups[i].m[key]=['radius','arc'].includes(key)?values[i+1]/values[i]:values[i+1];
        if(key==='radius')ups[i].m.width=values[i+1]/values[i];
      }
      const linked=mode==='yuta-resonance'||mode==='uro-echo';
      const def={id,name,icon:id,type,kind:dmg?'melee':'buff',digiMode:mode,digimonSkill:true,narutoSkill:true,jujutsuSkill:true,
        passive:true,autoCast:!linked,learnLevel,cd,dmg,range,radius,width:radius*2,speed:520,life:1,count:1,arc:1.6,pierce:0,
        duration:0,maxLvl:5,ups,...growth.base,
        desc:desc+(linked?' 本作改編被動，不占主動槽。':' 自動施放，不占主動槽。'),source_url:source};
      if(ladder)for(const [key,values]of Object.entries(ladder))def[key]=values[0];
      def.width=def.radius*2;
      if(mode==='uro-thin-ice')def.source_url='https://kotodaman.jp/info/detail/081584KEuwsxffR4nq.html';
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
        stats.textContent=`Lv.${def.learnLevel} 可學 · ${!def.autoCast?'被動連動':id==='jjk-yuta-manifest'?'顯現8秒・結束後恢復8→6秒（冷卻卡縮恢復）':`冷卻 ${def.cd} 秒`} · 可升至 Lv.${def.maxLvl}`;
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
  G.Jujutsu={kits,owners,source,functional,power};
})();
