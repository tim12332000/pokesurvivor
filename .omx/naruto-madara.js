/* Reanimated Madara: interruptible body pursuit, owned contacts and timed wood doubles. */
(() => {
  'use strict';
  if(G.NarutoMadara)return;
  const DEX=30016,C=G.Combat,EPS=1e-8,states=new Map();
  const rows=[
    ['naruto-madara','basic','戰場演舞','fighting',1,.95,24,105,90,'踏步接敵，以掌、肘、踢連續追擊，優先換人、逐段加速，末段迴旋踢清身；數量增加真追擊，最多12段。正常收招沿可通行路線回位，移動輸入立即中止追擊與回位。二階踢掃、三階擴大接敵範圍，末擊真命中蓄勢一格。追擊與連打期間有80%機率閃避敵人攻擊，閃避不給無敵；起手、回位與收招後不適用。連續追擊為本作改編，仍可能受傷；木分身維持近身連打。'],
    ['naruto-madara-fire','fire','火遁・豪火滅卻','fire',2,18,42,430,210,'結印後從嘴部吐出4→6面寬火牆，每面固定當次原點與方向，向外推進才命中；數量至12面，身體0.74秒即收勢。三階留下真火線，四階交錯雙角火線。每輪真命中最多蓄勢一格。'],
    ['naruto-madara-susanoo','susanoo','須佐能乎・巨刃連斬','psychic',3,30,78,460,240,'須佐投射現身六秒，骨臂接觸成長為甲胄主刀連斬、另一刀護勢；數量增加實際刀線但維持六秒，不佔本體出手。二階後體術末擊與火牆真命中蓄滿三格，顯現六秒完成體巨刀與前推劍壓。完成體末斬蓄力5秒，再揮出一道向前擴張的大範圍圓弧斬波，斬波推進才命中。本作勢能改編，不給無敵。'],
    ['naruto-madara-meteor','meteor','天礙震星・雙重落石','rock',7,52,155,700,250,'第一巨岩撞裂地面，第二顆砸碎更大區域，接續4→8塊真碎岩落向不同地點；數量卡至16個碎岩落點。每塊有獨立預告、高度與碰撞，走出可閃避。三階殘岩可由本體火牆引爆一次碎岩接力；碎岩及連動為本作改編。'],
    ['naruto-madara-clones','clones','木遁・木分身','grass',1,36,32,500,180,'開局召喚兩名木分身，現身後協戰6秒便退場，至少間隔12秒再召喚。升階增至4／6／8／10名，數量卡至16名。學會豪火後兩翼吐火，學會須佐後全軍獨立揮斬；木分身二階全軍披甲胄須佐。僅使用已學能力，不複製完成體也不蓄勢。升階與數量只補新增分身，不延長本輪停留；火力100→210%。']
  ];
  const ids=new Set(rows.map(r=>r[0])),kit=[DEX,rows.map(([id,kind,name,type,level])=>[id,kind,name,type,level])];
  const rank=m=>Math.max(1,Math.min(5,Math.floor(m?.lvl||1)));
  const count=(a,n,cap)=>Math.min(cap,G.Quantity?.count(a,n)??n);
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const controlled=a=>G.SelfClones?.isControlled?.(a)??(a===G.Game.player||!!G.SelfClones?.isActor?.(a));
  const valid=a=>alive(a)&&controlled(a)&&(a.mon?.dex??a.dex)===DEX;
  const supports=m=>typeof m==='string'?m.startsWith('madara-'):ids.has(m?.id);
  function profile(a,m){
    const i=rank(m)-1,kind=m.madaraKind||m.digiMode?.replace('madara-','')||'basic',damage=m.dmg*(a.atk??1);
    const common={kind,rank:i+1,damage,range:m.range,radius:m.radius};
    if(kind==='basic'){const contacts=count(a,4+i,12);return {...common,range:180+30*i,contacts,pulses:contacts,contactRadius:12+2*i,contactReach:56+4*i,stepBudget:180+30*i,pursuitRange:340+40*i,pursuitSpeed:900+80*i,contactDuration:.22,dodgeChance:.8,returnDuration:.55,kickSweep:i>=1,duration:.18+contacts*.22,charge:.10};}
    if(kind==='fire'){const fronts=count(a,4+Math.floor(i/2),12);return {...common,fronts,pulses:fronts,width:320+65*i,speed:620+40*i,range:560+85*i,depth:36,release:.25,releaseWindow:.35,duration:.74,charge:.25,linger:i>=2?1.1:0,fork:i>=3,lingerTicks:i>=4?4:3};}
    if(kind==='susanoo'){const slashes=count(a,4+i,12);return {...common,slashes,pulses:slashes,duration:6,manifest:.35,sweepDuration:.28,recovery:.28,bladeLength:220+25*i,bladeRadius:24+3*i,perfectLength:430+25*i,pressureEvery:i>=3?2:3,finisherCharge:5,finisherSweep:.48,finisherRecovery:.45,finisherRange:1100,finisherArc:2.2,finisherDepth:48,perfectUnlocked:i>=1,form:i>=1?'armored':'rib',charge:.35};}
    if(kind==='meteor'){const fragments=count(a,4+i,16);return {...common,meteorCount:2,fragments,pulses:2+fragments,radius:220+25*i,secondRadius:330+30*i,fragmentRadius:90+10*i,fragmentSpread:310+25*i,delay:.85,release:.44,duration:.66,charge:.44,fallTime:.95,craterDuration:i>=2?6:3,craterRelay:i>=2};}
    const cloneCount=count(a,[2,4,6,8,10][i],16);return {...common,cloneCount,pulses:cloneCount,cloneDuration:6,cloneRest:12,cloneDamageMultiplier:m.dmg/32,duration:.66,charge:.36,release:.36,roles:2,relay:true,armyForm:i>=1?'armored':'rib'};
  }
  function vector(a,m){const p=profile(a,m);return p.kind==='basic'?{接觸連段:p.contacts}:p.kind==='fire'?{火牆:p.fronts}:p.kind==='susanoo'?{刀臂接觸:p.slashes,...(p.perfectUnlocked?{完成體劍壓:Math.floor(p.slashes/p.pressureEvery)+(p.slashes%p.pressureEvery?1:0)}:{})}:p.kind==='meteor'?{巨岩:2,碎岩落點:p.fragments}:{木分身:p.cloneCount};}
  function metrics(owner,m,en=false){
    const p=profile(owner,m),pair=(zh,eng,v)=>[en?eng:zh,v];
    if(p.kind==='basic')return Object.fromEntries([pair('接觸連段','Contacts',p.contacts),pair('肢體半徑','Limb radius',p.contactRadius),pair('接敵步幅','Footwork budget',p.stepBudget),pair('踢掃','Sweeping kick',p.kickSweep?(en?'On':'啟用'):(en?'Off':'未啟用'))]);
    if(p.kind==='fire')return Object.fromEntries([pair('火牆','Fire fronts',p.fronts),pair('火牆寬','Front width',p.width),pair('推進射程','Travel range',p.range),pair('留焰秒','Burn seconds',p.linger),pair('火線方向','Fire directions',p.fork?2:1)]);
    if(p.kind==='susanoo')return Object.fromEntries([pair('刀臂接觸','Blade contacts',p.slashes),pair('常態形態','Guardian form',p.form==='rib'?(en?'Ribcage':'骨架'):(en?'Armored':'甲胄')),pair('完成體解鎖','Perfect form unlocked',p.perfectUnlocked?(en?'Unlocked':'解鎖'):(en?'Locked':'未解鎖')),pair('完成體劍壓','Perfect pressure waves',p.perfectUnlocked?Math.floor(p.slashes/p.pressureEvery)+(p.slashes%p.pressureEvery?1:0):0)]);
    if(p.kind==='meteor')return Object.fromEntries([pair('碎岩落點','Fragment landings',p.fragments),pair('首岩半徑','First radius',p.radius),pair('次岩半徑','Second radius',p.secondRadius),pair('殘岩秒','Crater seconds',p.craterDuration),pair('火牆引爆殘岩','Fire crater relay',p.craterRelay?(en?'On':'啟用'):(en?'Off':'未啟用'))]);
    return Object.fromEntries([pair('木分身','Wood doubles',p.cloneCount),pair('分身火力%','Army power %',Math.round(p.cloneDamageMultiplier*100)),pair('軍團須佐','Army guardian',p.armyForm==='armored'?(en?'Armored':'甲胄'):(en?'Ribcage':'骨架')),pair('本體指令接力','Command relay',p.relay?(en?'On':'啟用'):(en?'Off':'未啟用'))]);
  }
  function growthText(owner,m,next,en=false){
    const a=profile(owner,m),b=profile(owner,next),before=metrics(owner,m,en),after=metrics(owner,next,en),parts=[];
    if(a.kind!=='clones')parts.push(`${en?'Damage':'傷害'} ${Math.round(a.damage)}→${Math.round(b.damage)}`);
    for(const key of Object.keys(before))if(before[key]!==after[key])parts.push(`${key} ${before[key]}→${after[key]}`);
    return parts.join(en?'; ':'；');
  }
  const catalog=G.NarutoSkillCatalog;
  for(const [id,kind,name,type,learnLevel,cd,dmg,range,radius,desc]of rows){
    const ups=Array.from({length:4},(_,i)=>({t:`傷害、範圍與真實段數成長；${kind==='clones'?'分身協戰強化':kind==='meteor'?'雙隕石衝擊波':'連段'}強化`,m:{dmg:[1.2,1.45/1.2,1.75/1.45,2.1/1.75][i]}}));
    const def={id,name,icon:id,type,kind:'melee',madaraKind:kind,digiMode:'madara-'+kind,digimonSkill:true,narutoSkill:true,passive:true,autoCast:true,learnLevel,cd,dmg,range,radius,width:radius*2,maxLvl:5,ups,desc:desc+' 自動施放，不占主動槽。',source_url:'https://naruto-action.bn-ent.net/special/dlc_09.php'};
    G.Moves.BY_ID[id]=def;G.Moves.ALL.push(def);catalog.definitions.set(id,def);
    G.Icons.UI[id]={pal:{r:'#c54a3e',b:'#71b6f3',w:'#f8dcac',k:'#151923'},outline:true,rows:kind==='fire'?['.....r......','....rr......','..r.rr.r....','..rrrrrrr...','.rrrrwwrrr..','rrrwwwwwrrr.','.rrwwwwwrr..','..rrwwwrr...','...rrrrr....','....rrr.....','.....r......','............']:kind==='meteor'?['rr..........','.rr.........','..rr........','...rr.......','....kkkk....','...kwwwwk...','..kwwrrwwk..','..kwrrrrwk..','..kwrrrrwk..','...kwwwwk...','....kkkk....','............']:kind==='clones'?['...kk..kk...','..kwwkkwwk..','..krwkkrwk..','...kk..kk...','..rrrrrrrr..','.rrrrrrrrrr.','..rrrrrrrr..','..rrrrrrrr..','...kk..kk...','..kkk..kkk..','..k.k..k.k..','............']:['...bbbbbb...','..bwwwwwwb..','.bwkwwkwb...','.bwwwwwwb...','..bbbbbb....','.bbwwwwbb...','bbwwwwwwbb..','b.bwwwwb.b..','..bwwwwb....','..bb..bb....','.bb....bb...','............']};
    if(kind==='basic')G.Icons.UI[id]={pal:{w:'#f5d4b0',r:'#b93e35',k:'#181b25'},outline:true,rows:['....ww......','...wwww.....','...wwww.....','....ww......','..rrwrr.....','.rrrwwwww...','..rrwrr.....','...rrrr.....','...k.kk.....','..kk..kkk...','.kk.....kk..','............']};
    if(kind==='susanoo')G.Icons.UI[id]={pal:{w:'#e9f8ff',b:'#6cb6ef',k:'#17264c'},outline:true,rows:['..........ww','..b...b..ww.','..bbbbb.ww..','.bbwbwbww...','..bwwwbwb...','.bbbbbbbb...','bb.bb.bb.bb.','b..bwbb..b..','...bwwb.....','...bbbb.....','..bb..bb....','.bb....bb...']};
    G.JujutsuGrowth?.registerQuantityConsumer(def.digiMode,vector);
  }
  const englishNames=['Battlefield Taijutsu','Fire Release: Majestic Destroyer Flame','Susanoo: Giant Blade Barrage','Heaven Concealed: Twin Meteors','Wood Release: Wood Clones'];
  const englishDescriptions=[
    'Step into a chain of real palm, elbow and kick contacts, preferring a new enemy each strike and accelerating through the chain. Quantity adds pursuits up to twelve. The final spinning kick earns one momentum on a true enemy hit. Return along a clear route after the chain; movement input immediately cancels pursuit and return. Rank 2 gains sweeping kicks; rank 3 expands pursuit reach. During pursuit and strikes, incoming enemy attacks have an 80% chance to be dodged, without granting invulnerability. The opening charge, return and time after the chain gain no dodge bonus. This pursuit is a game adaptation. Wood doubles keep their close-range combo.',
    'After a short seal, exhale four to six broad advancing fire fronts. Each snapshots its mouth origin and heading; enemies are struck only when the front arrives. Quantity adds fronts up to twelve without extending the 0.74-second body pose. Rank 3 leaves burning lines; rank 4 crosses two headings. A successful cast earns at most one momentum.',
    'An independent six-second guardian grows from skeletal limbs to armored blades. Quantity adds real blade sweeps without locking the body. Rank 2 unlocks a six-second Perfect Susanoo at three momentum, with gigantic blades and advancing sword pressure. The Perfect form ends with a five-second charged slash that releases one broad, expanding crescent wave, dealing damage only as it advances. Momentum and timing are game adaptations; no invulnerability.',
    'Two giant rocks land separately: the second shatters a wider area. Four to eight fragments then fall at separate marked locations; quantity adds fragments up to sixteen. Each has real height and a single landing collision. Rank 3 craters permit one fire-triggered rubble burst per cast, a non-recursive game adaptation.',
    'Start by summoning two wood doubles. They fight for six seconds after emerging, then withdraw for at least twelve seconds before another summon. Ranks increase the army to four, six, eight and ten; quantity grows it up to sixteen. Flanks use learned fire; every double independently uses learned skeletal Susanoo, armored at wood-clone rank 2. Growth adds actors without extending the current summon. Doubles never generate momentum or copy Perfect Susanoo. Army power grows from 100% to 210% of its base.'

  ];
  const dictionary={'宇智波斑・穢土轉生':'Madara Uchiha · Reanimated'};
  for(const [rowIndex,[id]]of rows.entries()){
    const def=G.Moves.BY_ID[id];dictionary[def.name]=englishNames[rowIndex];dictionary[`Lv.${def.learnLevel} ${def.name}`]=`Lv.${def.learnLevel} ${englishNames[rowIndex]}`;dictionary[def.desc]=englishDescriptions[rowIndex]+' Automatically cast; no active slot required.';
    for(let i=0;i<4;i++){
      const before=G.Moves.instance(id,i+1),after=G.Moves.instance(id,i+2),owner={atk:1,quantityPicks:0},text=growthText(owner,before,after);
      def.ups[i].t=text;dictionary[text]=growthText(owner,before,after,true);

    }
  }
  G.I18n.add(dictionary,'en');
  catalog.byDex.set(DEX,G.Moves.BY_ID['naruto-madara']);catalog.extraPools.set(DEX,rows.slice(1).map(r=>r[0]));
  catalog.references.set(DEX,{name:'Madara Uchiha',source_url:G.Moves.BY_ID['naruto-madara'].source_url});
  G.Naruto.records.get(DEX).attack='戰場演舞';
  const guide=document.querySelector('#scr-naruto-skills .naruto-skill-entries');
  if(guide){const article=document.createElement('article');article.className='naruto-skill-entry';const h=document.createElement('h3');h.textContent='宇智波斑・穢土轉生';article.append(h);for(const [id]of rows){const d=G.Moves.BY_ID[id],title=document.createElement('h4'),p=document.createElement('p');title.textContent=`Lv.${d.learnLevel} ${d.name}`;p.textContent=d.desc;article.append(title,p);}guide.append(article);}
  let starting=false;
  const startRun=G.Game.startRun;
  G.Game.startRun=function(...args){starting=true;try{const result=startRun.apply(this,args),owner=G.Game.player;if(owner?.mon?.dex===DEX){if(!owner.hasMove('naruto-madara-clones'))owner.addMove('naruto-madara-clones');const m=learned(owner,'naruto-madara-clones');if(m){const s=state(owner);spawnArmy(s,{m,spec:profile(owner,m)});m.t=Math.max(m.t||0,m.cd*(owner.cdMul??1));}}return result;}finally{starting=false;}};
  const pool=G.Moves.poolFor;
  G.Moves.poolFor=mon=>mon.dex===DEX?rows.filter(r=>r[4]<=(!starting&&G.Game.player?.mon===mon?G.Game.player.level:1)).map(r=>r[0]):pool(mon);
  const addMove=G.Player.prototype.addMove;
  G.Player.prototype.addMove=function(id,...args){
    if(ids.has(id)){if(this.mon?.dex!==DEX||this.level<G.Moves.BY_ID[id].learnLevel||this.hasMove(id))return false;this.moves.push(G.Moves.instance(id));this.arrange();return true;}
    if(this.mon?.dex===DEX)return false;return addMove.call(this,id,...args);
  };
  // Reserve one early army milestone; the remaining cards keep normal build choices.
  const offer=G.LevelUp.offer;
  G.LevelUp.offer=function(owner,n=3,...args){
    const cards=offer.call(this,owner,n,...args);
    if(owner.mon?.dex===DEX&&n<256&&n>0){
      const milestones=[['naruto-madara-fire',1],['naruto-madara-susanoo',1],['naruto-madara-clones',2],['naruto-madara-susanoo',2],['naruto-madara-meteor',1]];
      const milestone=milestones.find(([id,level])=>owner.level>=G.Moves.BY_ID[id].learnLevel&&!owner.banned?.has(id)&&(learned(owner,id)?.lvl||0)<level);
      if(milestone){const id=milestone[0],key=(learned(owner,id)?'up:':'new:')+id;
        if(!cards.some(c=>c.key===key)){const card=offer.call(this,owner,256,...args).find(c=>c.key===key);if(card){const index=cards.findIndex(c=>c.type!=='stat');if(cards.length<n)cards.push(card);else cards[index>=0?index:0]=card;}}
      }
    }
    return cards.map(card=>{
      if(card.type!=='up')return card;
      const id=card.key.slice(3),m=owner.moves?.find(move=>move.id===id);
      if(!ids.has(id)||!m||m.lvl>=m.def.maxLvl)return card;
      const next=G.Moves.instance(id,m.lvl+1);return {...card,desc:growthText(owner,m,next,G.I18n.lang==='en'),growthMove:m};
    });
  };
  let actorSequence=0;
  function state(owner){
    let s=states.get(owner);if(s&&(s.world!==G.World||s.epoch!==G.CombatPulse.epoch)){clear(owner);s=null;}
    if(!s){s={owner,world:G.World,epoch:G.CombatPulse.epoch,clock:0,body:null,guardian:null,fires:[],flames:[],meteors:[],pressures:[],army:[],craters:[],effects:[],contacts:[],hitContacts:[],casts:{},hits:0,damage:0,propHits:0,propDamage:0,impetus:0,perfectCount:0,readyAt:new Map(),command:null};Object.defineProperty(s,'action',{get(){return s.body;}});Object.defineProperty(s,'clones',{get(){return s.army;}});Object.defineProperty(s,'fields',{get(){return [...s.fires,...s.flames,...s.meteors,...s.pressures];}});states.set(owner,s);}return s;
  }
  function clear(owner){if(!owner){for(const a of [...states.keys()])clear(a);return;}const s=states.get(owner);if(!s)return;for(const f of [s.body,s.guardian,...s.fires,...s.flames,...s.meteors,...s.pressures,...s.army.flatMap(a=>[a.body,a.guardian])])if(f?.cast)f.cast.runEpoch=-1;states.delete(owner);}
  function path(x,y,tx,ty,target=null){if(G.World.projectilePathClear)return G.World.projectilePathClear(x,y,tx,ty,target,{radius:1,spacing:4,includeStart:false});const n=Math.max(1,Math.ceil(Math.hypot(tx-x,ty-y)/4));for(let i=1;i<=n;i++){const px=x+(tx-x)*i/n,py=y+(ty-y)*i/n;if(G.World.isWall?.(px,py))return false;const b=G.World.projectileBlock?.(px,py,1);if(b&&b!==target)return false;}return true;}
  function registered(e){return !!e&&G.EnemyMgr.get(e.id)===e;}
  function enemies(x,y,r){return [...new Set(G.EnemyMgr.queryCircle(x,y,r+100))].filter(e=>registered(e)&&alive(e)&&!e.friendly&&Math.hypot(e.x-x,e.y-y)<=r+(e.r||0));}
  function props(x,y,r){return [...new Set(G.World.propsInCircle?.(x,y,r)||[])].filter(p=>!p.dead&&p.destructible!==false&&p.hp>0&&Math.hypot(p.x-x,p.y-y)<=r+(p.r||0));}
  const learned=(a,id)=>a.moves?.find(m=>m.id===id);
  function nearest(origin,list,eligible){let best=null,distance=Infinity;for(const t of list){const d=(t.x-origin.x)**2+(t.y-origin.y)**2;if(d>=distance||!eligible(t))continue;best=t;distance=d;}return best;}
  function targetFor(owner,m,origin=owner,range=null){const r=range??profile(owner,m).range;return nearest(origin,enemies(origin.x,origin.y,r),e=>path(origin.x,origin.y,e.x,e.y))||nearest(origin,props(origin.x,origin.y,r),p=>path(origin.x,origin.y,p.x,p.y,p));}
  function drawable(s,f){return !!f&&states.get(s.owner)===s&&s.world===G.World&&s.epoch===G.CombatPulse.epoch&&valid(s.owner)&&!!learned(s.owner,f.m.id)&&(!f.actor||s.army.includes(f.actor)&&!!learned(s.owner,'naruto-madara-clones'))&&f.cast.runEpoch===s.epoch;}
  const legal=(s,f)=>drawable(s,f)&&G.CombatPulse.legal(f.cast);
  function source(s,m,channel,actor=null){return {owner:s.owner,actor,m:{...m},spec:profile(s.owner,m),age:0,pulseSequence:0,cast:G.CombatPulse.create(s.owner,m.id,{channel,targetIsLegal:registered}),hitEvents:0,credited:false};}
  const moving=a=>a===G.Game.player&&Math.hypot(...(G.Input?.axis?.()||[0,0]))>.18;
  const angle=(x,y,tx,ty)=>Math.atan2(ty-y,tx-x);
  function toward(actor,tx,ty,budget){let left=Math.min(Math.max(0,budget),Math.hypot(tx-actor.x,ty-actor.y)),travel=0;for(let i=0;i<40&&left>.001;i++){const step=Math.min(4,left),d=Math.hypot(tx-actor.x,ty-actor.y);if(d<.001)break;const x=actor.x+(tx-actor.x)/d*step,y=actor.y+(ty-actor.y)/d*step;if(!path(actor.x,actor.y,x,y)||G.World.isFree&&!G.World.isFree(x,y,actor.r||12,true))break;actor.x=x;actor.y=y;left-=step;travel+=step;}return travel;}
  function segmentDistance(x,y,ax,ay,bx,by){const dx=bx-ax,dy=by-ay,t=Math.max(0,Math.min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy||1)));return Math.hypot(x-ax-dx*t,y-ay-dy*t);}
  function inside(g,t){const r=t.r||0;if(g.kind==='arc'){const dx=t.x-g.x,dy=t.y-g.y,d=Math.hypot(dx,dy),a=Math.atan2(Math.sin(Math.atan2(dy,dx)-g.aim),Math.cos(Math.atan2(dy,dx)-g.aim));return d>=g.from-g.depth-r&&d<=g.to+g.depth+r&&Math.abs(a)<=g.arcAngle/2+Math.asin(Math.min(1,r/Math.max(1,d)));}if(g.kind==='circle')return Math.hypot(t.x-g.x,t.y-g.y)<=g.radius+r;if(g.kind==='capsule')return segmentDistance(t.x,t.y,g.ax,g.ay,g.bx,g.by)<=g.radius+r;if(g.kind==='wall'){const dx=t.x-g.x,dy=t.y-g.y,c=Math.cos(g.aim),sn=Math.sin(g.aim),u=dx*c+dy*sn,v=-dx*sn+dy*c;return u>=g.from-g.depth-r&&u<=g.to+g.depth+r&&Math.abs(v)<=g.width/2+r;}return false;}
  function bounds(g){if(g.kind==='arc')return {x:g.x,y:g.y,r:g.to+g.depth};if(g.kind==='circle')return {x:g.x,y:g.y,r:g.radius};if(g.kind==='capsule')return {x:(g.ax+g.bx)/2,y:(g.ay+g.by)/2,r:Math.hypot(g.bx-g.ax,g.by-g.ay)/2+g.radius};return {x:g.x+Math.cos(g.aim)*(g.from+g.to)/2,y:g.y+Math.sin(g.aim)*(g.from+g.to)/2,r:Math.hypot(g.to-g.from+g.depth*2,g.width)/2};}
  function remember(s,f,g,segment,info){if(s.contacts.length>=96)s.contacts.shift();s.contacts.push({time:s.clock,castId:f.cast.castId,channel:f.cast.channel,source:f.actor?.serial??'body',role:f.actor?.role??null,kind:f.spec.kind,phase:g.phase||f.phase||'contact',segment,geometry:{...g},primaryHits:info?.primaryHits||0,primaryDamage:info?.primaryDamage||0});if(info?.primaryHits){if(s.hitContacts.length>=96)s.hitContacts.shift();s.hitContacts.push(s.contacts[s.contacts.length-1]);}}
  function contact(s,f,g,segment,{ratio=1,hitSet=null,propSet=null,origin=null}={}){
    if(!legal(s,f))return null;const b=bounds(g),o=origin||{x:g.x??g.ax,y:g.y??g.ay},targets=enemies(b.x,b.y,b.r).filter(e=>(!hitSet||!hitSet.has(e))&&inside(g,e)&&path(o.x,o.y,e.x,e.y));
    const damage=f.spec.damage*(f.actor?f.actor.damageMultiplier:1)*ratio,hits=targets.map(e=>{hitSet?.add(e);const mult=G.Types.mult(f.m.type,e.types),crit=Math.random()<(s.owner.critChance||0);return {target:e,primaryDirectDamage:damage*mult*G.Weather.mult(f.m.type)*(crit?1.5:1),color:f.spec.kind==='fire'?'#ffab49':'#98c9ff',eff:crit?'crit':G.Types.label(mult),onHit(){if(!drawable(s,f))f.cast.runEpoch=-1;}};});
    const result=G.CombatPulse.apply(f.cast,f.pulseSequence++,hits);if(result){s.hits+=result.primaryHits;s.damage+=result.primaryDamage;f.hitEvents+=result.primaryHits;}remember(s,f,g,segment,result);
    for(const p of props(b.x,b.y,b.r)){if(!legal(s,f))break;if(propSet?.has(p)||!inside(g,p)||!path(o.x,o.y,p.x,p.y,p))continue;propSet?.add(p);const before=p.hp;G.World.damageProp?.(p,damage,'#cfbb92');s.propHits++;s.propDamage+=Math.min(before,damage);}return result;
  }
  function audio(id,options={},army=false){if(!army)G.Audio?.sfx?.(id,options);}
  function gain(s,f){if(f.actor||G.SelfClones?.isActor?.(s.owner)||f.credited||!f.hitEvents||!learned(s.owner,'naruto-madara-susanoo'))return;f.credited=true;s.impetus=Math.min(3,s.impetus+1);if(s.guardian&&profile(s.owner,s.guardian.m).perfectUnlocked&&s.impetus>=3)transform(s,s.guardian);}
  function transform(s,g){if(g.actor||G.SelfClones?.isActor?.(s.owner)||g.perfect||!g.spec.perfectUnlocked||s.impetus<3)return false;s.impetus=0;g.perfect=true;g.form='perfect';g.age=0;g.duration=6+g.spec.finisherCharge+g.spec.finisherSweep+g.spec.finisherRecovery;g.index=0;g.swing=null;g.phase='manifest';s.perfectCount++;audio('madara-form');return true;}
  function socket(actor,name,pose,height=64*(actor.anim?.scale||1)){const authored=G.MadaraArt?.socketFor?.(actor,name,{pose,dir:G.Sprites?.dirFromAngle?.(pose.aim)??2,height});if(authored)return {x:authored.x,y:authored.y+height*.5,visual:{x:authored.x,y:authored.y},sheet:authored.sheet,frame:authored.index};const reach=name==='elbow'?30:name==='foot'?48:name==='mouth'?18:41,side=name==='foot'?-6:0,x=actor.x+Math.cos(pose.aim)*reach-Math.sin(pose.aim)*side,y=actor.y+Math.sin(pose.aim)*reach+Math.cos(pose.aim)*side;return {x,y,visual:{x,y:y-height*.5}};}
  const basicContact=(f,index)=>index===f.spec.contacts-1?(f.pursuit?'kick':'landing'):['palm','elbow','kick','palm','kick','elbow','kick'][index%7];
  function basicPoseFor(f,index,progress){
    const contact=basicContact(f,index),sweep=contact==='kick'&&(f.spec.kickSweep||f.pursuit&&index===f.spec.contacts-1),interval=f.pursuit?(f.segmentDuration||f.spec.contactDuration):(f.spec.duration-.18)/f.spec.contacts,start=sweep?.15:.28,end=sweep?.85:.75,age=Math.max(0,progress)*interval;
    const aim=f.pursuit&&index===f.spec.contacts-1?f.aim+(Math.max(0,Math.min(1,(progress-start)/(end-start)))-.5)*Math.PI*2:f.aim;
    return {kind:'basic',phase:progress<start?'windup':progress<=end?'contact':'recover',contact,age,localAge:age,progress,castAge:f.age,aim,index,contacts:f.spec.contacts,contactStart:start,contactEnd:end};
  }
  function bodyPose(f){
    if(!f)return null;
    if(f.pursuit){const pose=basicPoseFor(f,Math.min(f.index,f.spec.contacts-1),f.pursuitPhase==='contact'?Math.min(1,f.segmentAge/f.segmentDuration):f.pursuitPhase==='return'?1:0);return {...pose,phase:f.pursuitPhase==='contact'?pose.phase:f.pursuitPhase==='return'?'recover':'windup'};}
    if(f.spec.kind==='basic'){const interval=(f.spec.duration-.18)/f.spec.contacts,index=Math.min(f.spec.contacts-1,Math.max(0,Math.floor((f.age-.1)/interval))),progress=Math.max(0,Math.min(1,(f.age-.1-index*interval)/interval));return basicPoseFor(f,index,progress);}
    return {kind:f.spec.kind,phase:f.age<f.spec.charge?'windup':f.age<f.spec.duration-.12?'contact':'recover',age:f.age,localAge:f.age,castAge:f.age,aim:f.aim,index:f.emitted||0};
  }

  function basicApproach(actor,target,p,aim=angle(actor.x,actor.y,target.x,target.y),index=null){
    let best=null;const f={spec:p,age:0,aim,pursuit:index!=null};
    for(let i=index??0;i<(index==null?p.contacts:index+1);i++){const pose=basicPoseFor(f,i,.5),name=pose.contact==='kick'||pose.contact==='landing'?'foot':pose.contact,point=socket(actor,name,pose),radius=p.contactRadius+(pose.contact==='landing'?8:0)+(target.r||0),distance=Math.hypot(target.x-point.x,target.y-point.y),gap=Math.max(0,distance-radius);
      if(!best||gap<best.gap)best={gap,point,distance,dx:target.x-point.x,dy:target.y-point.y};}
    return best;
  }
  const basicExtentCache=new Map();let basicExtentMetadata;
  function basicSearchRadius(actor,p,budget){
    const metadata=G.MadaraArt?.metadata,scale=actor.anim?.scale||1;
    if(metadata!==basicExtentMetadata){basicExtentMetadata=metadata;basicExtentCache.clear();}
    let extent=basicExtentCache.get(scale);
    if(extent==null){
      extent=64*scale;
      for(const aim of [0,Math.PI/2,Math.PI,-Math.PI/2])for(const contact of ['palm','elbow','kick','landing'])for(const phase of ['windup','contact','recover']){
        const name=contact==='kick'||contact==='landing'?'foot':contact,point=socket(actor,name,{kind:'basic',contact,phase,progress:.5,age:.1,aim});
        extent=Math.max(extent,Math.hypot(point.x-actor.x,point.y-actor.y));
      }
      basicExtentCache.set(scale,extent);
    }
    // Broad phase only: exact authored sockets, contact radii and path checks remain unchanged.
    return extent+p.contactRadius+8+Math.max(0,budget)+4;
  }
  function basicTarget(owner,m,actor=owner,budget=null){
    if(actor===owner&&moving(owner))return null;
    const p=profile(owner,m),allowed=budget??(actor===owner&&moving(owner)?0:p.stepBudget),r=basicSearchRadius(actor,p,allowed);
    return [...enemies(actor.x,actor.y,r),...props(actor.x,actor.y,r)].filter(t=>path(actor.x,actor.y,t.x,t.y,t.destructible?t:null)&&basicApproach(actor,t,p).gap<=allowed+.5).sort((a,b)=>Math.hypot(a.x-actor.x,a.y-actor.y)-Math.hypot(b.x-actor.x,b.y-actor.y))[0]||null;
  }
  function makeBody(s,m,actor=null,target=null){const f=source(s,m,actor?'army-body':'body',actor),origin=actor||s.owner;let p=f.spec;if(actor&&p.kind==='basic'){const i=p.rank-1,contacts=count(s.owner,4+(i>=3?1:0),8);p=f.spec={...p,contacts,stepBudget:i>=2?50:30,duration:Math.min(.82,.62+(contacts-4)*.045)};}const t=target||(p.kind==='basic'?basicTarget(s.owner,m,origin):targetFor(s.owner,m,origin,p.range));if(!t||p.kind==='fire'&&Math.hypot(t.x-origin.x,t.y-origin.y)>p.range+(t.r||0)||p.kind==='basic'&&basicApproach(origin,t,p).gap>(actor?0:moving(origin)?0:p.stepBudget)+.5)return null;Object.assign(f,{aim:angle(origin.x,origin.y,t.x,t.y),target:t,index:0,emitted:0,stepUsed:0,duration:p.duration,phase:'windup'});if(!actor&&p.kind==='basic')Object.assign(f,{pursuit:true,pursuitPhase:'approach',origin:{x:origin.x,y:origin.y},route:[{x:origin.x,y:origin.y}],segmentAge:0,travelAge:0,lastTarget:null});if(actor&&p.kind==='fire')f.spec={...p,fronts:Math.min(4,p.fronts)};return f;}
  function makeGuardian(s,m,actor=null,target=null){const g=source(s,m,actor?'army-guardian':'guardian',actor),origin=actor||s.owner,t=target||guardianTarget(s.owner,m,origin,!actor&&s.impetus>=3&&g.spec.perfectUnlocked);if(!t)return null;Object.assign(g,{duration:6,aim:angle(origin.x,origin.y,t.x,t.y),phase:'manifest',form:g.spec.form,perfect:false,index:0,swing:null,blade:null,prevBlade:null});if(actor){g.form=actor.rank>=2?'armored':'rib';g.spec={...g.spec,form:g.form,slashes:Math.min(8,g.spec.slashes),bladeLength:g.spec.bladeLength*.75};}else if(s.impetus>=3&&g.spec.perfectUnlocked)transform(s,g);if(!g.perfect)audio('madara-form',{perfect:false},!!actor);return g;}
  function canCast(owner,m){if(!valid(owner)||owner.frozen||G.Game.state!=='playing'||!ids.has(m?.id)||(m.t||0)>EPS||!learned(owner,m.id))return false;const s=state(owner),p=profile(owner,m);if(p.kind==='susanoo')return !s.guardian&&!!guardianTarget(owner,m,owner,!G.SelfClones?.isActor?.(owner)&&s.impetus>=3&&p.perfectUnlocked);if(s.body||p.kind==='clones'&&(s.army.length||s.clock<(s.armyReadyAt||0)))return false;if(p.kind==='clones')return true;return p.kind==='basic'?!!basicTarget(owner,m):!!targetFor(owner,m,owner,p.range);}
  function cast(owner,m){if(!canCast(owner,m))return false;const s=state(owner),p=profile(owner,m);if(p.kind==='susanoo'){s.guardian=makeGuardian(s,m);if(!s.guardian)return false;}else{if(p.kind==='clones'){s.body=source(s,m,'body');Object.assign(s.body,{aim:owner.aim||0,duration:p.duration,phase:'windup'});}else s.body=makeBody(s,m);if(!s.body)return false;owner.aim=s.body.aim;owner.cast?.(m);}m.t=Math.max(.1,m.cd*(owner.cdMul??1));m.castAt=performance.now();s.casts[m.id]=(s.casts[m.id]||0)+1;s.readyAt.delete(m.id);return true;}
  function advanceBasic(s,f){
    const actor=f.actor||s.owner,p=f.spec,interval=(p.duration-.18)/p.contacts,oldAge=f.previousBasicAge??0,newAge=f.age;
    f.basicSegments??=[];
    for(let index=0;index<p.contacts;index++){
      const begin=.1+index*interval;if(newAge<begin||oldAge>=begin+interval)continue;
      let segment=f.basicSegments[index];
      if(!segment){
        const retained=f.target&&alive(f.target)&&(registered(f.target)||f.target.destructible&&props(actor.x,actor.y,basicSearchRadius(actor,p,p.stepBudget)).includes(f.target))?f.target:null,t=basicTarget(s.owner,f.m,actor,f.actor||moving(actor)?0:Math.max(0,p.stepBudget-f.stepUsed))||retained;if(t){f.target=t;f.aim=angle(actor.x,actor.y,t.x,t.y);if(!f.actor&&!moving(actor)&&f.stepUsed<p.stepBudget){const reach=basicApproach(actor,t,p,f.aim),ratio=reach.distance?Math.min(1,(reach.gap+2)/reach.distance):0;f.stepUsed+=toward(actor,actor.x+reach.dx*ratio,actor.y+reach.dy*ratio,Math.min(12,p.stepBudget-f.stepUsed,reach.gap+2));}}
        segment={aim:f.aim,hitSet:new Set(),propSet:new Set(),hits:0,finalized:false,previousPoint:null,previousProgress:0};f.basicSegments[index]=segment;audio('madara-palm',{step:basicContact(f,index)},!!f.actor);
      }
      const name=basicContact(f,index),socketName=name==='kick'||name==='landing'?'foot':name,from=Math.max(0,Math.min(1,(oldAge-begin)/interval)),to=Math.max(0,Math.min(1,(newAge-begin)/interval)),start=name==='kick'&&p.kickSweep?.15:.28,end=name==='kick'&&p.kickSweep?.85:.75;
      const pose={...basicPoseFor(f,index,to),aim:segment.aim},point=socket(actor,socketName,pose),previous=segment.previousPoint||socket(actor,socketName,{...basicPoseFor(f,index,from),aim:segment.aim});
      if(to>=start&&from<=end){
        const span=to-from||1,a=Math.max(0,Math.min(1,(Math.max(start,from)-from)/span)),b=Math.max(0,Math.min(1,(Math.min(end,to)-from)/span)),radius=p.contactRadius+(name==='landing'?8:0),g={kind:'capsule',ax:previous.x+(point.x-previous.x)*a,ay:previous.y+(point.y-previous.y)*a,bx:previous.x+(point.x-previous.x)*b,by:previous.y+(point.y-previous.y)*b,radius,visual:point.visual,frame:{sheet:point.sheet,index:point.frame},previousFrame:{sheet:previous.sheet,index:previous.frame},phase:'contact'};
        const result=contact(s,f,g,index,{ratio:index===p.contacts-1?1.5:1,hitSet:segment.hitSet,propSet:segment.propSet,origin:{x:actor.x,y:actor.y}});segment.hits+=result?.primaryHits||0;
        if(result?.primaryHits&&legal(s,f))s.effects.push({kind:'contact',x:point.visual.x,y:point.visual.y,age:0,life:.13,radius:radius*.6,aim:segment.aim});
      }
      segment.previousPoint=point;segment.previousProgress=to;
      if(!segment.finalized&&to>=end){segment.finalized=true;f.index=index+1;if(index===p.contacts-1&&!f.actor&&segment.hits&&legal(s,f)){gain(s,f);s.command={target:f.target,x:f.target.x,y:f.target.y,expires:s.clock+2,kind:'finisher'};if(p.rank>=5)for(const a of s.army)if(a.role==='front')a.cooldown=0;}}
      if(!legal(s,f))break;
    }
    f.previousBasicAge=newAge;
  }

  function pursuitTarget(s,f){
    const a=s.owner,p=f.spec,r=p.stepBudget;
    const eligible=t=>alive(t)&&Math.hypot(t.x-f.origin.x,t.y-f.origin.y)<=p.pursuitRange+(t.r||0)&&path(a.x,a.y,t.x,t.y,t.destructible?t:null);
    const candidates=enemies(a.x,a.y,r).filter(eligible);
    return nearest(a,candidates,t=>t!==f.lastTarget)||nearest(a,candidates,()=>true)||nearest(a,props(a.x,a.y,r),eligible);
  }
  function returnFromPursuit(f){
    f.pursuitPhase='return';f.returnAge=0;f.returnIndex=f.route.length-1;
    let distance=0;for(let i=1;i<f.route.length;i++)distance+=Math.hypot(f.route[i].x-f.route[i-1].x,f.route[i].y-f.route[i-1].y);
    f.returnSpeed=Math.max(f.spec.pursuitSpeed,distance/(f.spec.returnDuration-.1));
  }
  function advancePursuit(s,f,dt){
    const a=s.owner,p=f.spec;
    // Real input wins even during recovery. Never drag a retreat back to the cast origin.
    if(moving(a))return false;
    if(f.pursuitPhase==='return'){
      f.returnAge+=dt;let budget=f.returnSpeed*dt;
      while(f.returnIndex>=0&&budget>.001){
        const point=f.route[f.returnIndex],distance=Math.hypot(point.x-a.x,point.y-a.y);
        if(distance<.5){f.returnIndex--;continue;}
        const moved=toward(a,point.x,point.y,Math.min(budget,distance));budget-=moved;
        if(moved<.001)return false;
      }
      return f.returnIndex>=0&&f.returnAge<p.returnDuration;
    }
    if(f.age<p.charge)return true;
    if(f.pursuitPhase==='approach'){
      const targetValid=t=>t&&alive(t)&&(registered(t)||props(a.x,a.y,p.stepBudget).includes(t))&&Math.hypot(t.x-f.origin.x,t.y-f.origin.y)<=p.pursuitRange+(t.r||0)&&path(a.x,a.y,t.x,t.y,t.destructible?t:null);
      if(!targetValid(f.target))f.target=pursuitTarget(s,f);
      if(!f.target){returnFromPursuit(f);return true;}
      const t=f.target;f.aim=angle(a.x,a.y,t.x,t.y);a.aim=a.moveAngle=f.aim;a.attackFace=.15;
      if(a.anim)a.anim.dir=G.Sprites.dirFromAngle(f.aim);
      const reach=basicApproach(a,t,p,f.aim,f.index),speed=p.pursuitSpeed*Math.min(2.5,1+f.index*.16);
      f.travelAge+=dt;
      if(reach.gap>.5){
        const ratio=reach.distance?Math.min(1,(reach.gap+3)/reach.distance):0;
        const moved=toward(a,a.x+reach.dx*ratio,a.y+reach.dy*ratio,Math.min(speed*dt,reach.gap+3));
        if(moved>0)f.route.push({x:a.x,y:a.y});
        if(moved<.001||f.travelAge>.6){returnFromPursuit(f);return true;}
        if(basicApproach(a,t,p,f.aim,f.index).gap>.5)return true;
      }
      f.pursuitPhase='contact';f.segmentAge=0;f.segmentDuration=Math.max(.115,p.contactDuration*Math.pow(.9,f.index));
      f.segment={aim:f.aim,hitSet:new Set(),propSet:new Set(),hits:0,previousPoint:null};
      audio('madara-palm',{step:basicContact(f,f.index)});
      return true;
    }
    const segment=f.segment,index=f.index,name=basicContact(f,index),socketName=name==='kick'||name==='landing'?'foot':name;
    const from=Math.min(1,f.segmentAge/f.segmentDuration);f.segmentAge+=dt;const to=Math.min(1,f.segmentAge/f.segmentDuration);
    const sweep=name==='kick'&&(p.kickSweep||index===p.contacts-1),start=sweep?.15:.28,end=sweep?.85:.75;
    const point=socket(a,socketName,basicPoseFor(f,index,to)),previous=segment.previousPoint||socket(a,socketName,basicPoseFor(f,index,from));
    if(to>=start&&from<=end){
      const span=to-from||1,lo=Math.max(0,(Math.max(start,from)-from)/span),hi=Math.min(1,(Math.min(end,to)-from)/span);
      const g={kind:'capsule',ax:previous.x+(point.x-previous.x)*lo,ay:previous.y+(point.y-previous.y)*lo,bx:previous.x+(point.x-previous.x)*hi,by:previous.y+(point.y-previous.y)*hi,radius:p.contactRadius+(index===p.contacts-1?22:0),visual:point.visual,frame:{sheet:point.sheet,index:point.frame},previousFrame:{sheet:previous.sheet,index:previous.frame},phase:'contact'};
      const result=contact(s,f,g,index,{ratio:(index===p.contacts-1?1.5:1)*(1+index*.05),hitSet:segment.hitSet,propSet:segment.propSet,origin:a});
      segment.hits+=result?.primaryHits||0;
      if(!legal(s,f))return false;
      if(result?.primaryHits&&index===p.contacts-1&&!f.finisherCommitted){
        f.finisherCommitted=true;gain(s,f);s.command={target:f.target,x:f.target.x,y:f.target.y,expires:s.clock+2,kind:'finisher'};
        if(p.rank>=5)for(const actor of s.army)if(actor.role==='front')actor.cooldown=0;
      }
      if(result?.primaryHits)s.effects.push({kind:'contact',x:point.visual.x,y:point.visual.y,age:0,life:.13,radius:g.radius*.6,aim:segment.aim});
    }
    segment.previousPoint=point;
    if(to>=1){
      f.lastTarget=f.target;f.index++;
      if(f.index>=p.contacts){
        returnFromPursuit(f);
      }else{f.target=pursuitTarget(s,f);f.travelAge=0;f.pursuitPhase='approach';}
    }
    return true;
  }

  function emitFire(s,f,index){if(!legal(s,f))return;const actor=f.actor||s.owner,p=f.spec,aim=f.aim+(p.fork?(index%2?1:-1)*.18:0),mouth=socket(actor,'mouth',{kind:'fire',phase:'contact',age:.35,aim:f.aim});const front={...source(s,f.m,f.actor?'army-fire':'field-fire',f.actor),spec:p,age:0,aim,x:mouth.x,y:mouth.y,visualOffsetY:mouth.visual.y-mouth.y,distance:0,previousDistance:0,width:p.width,hitSet:new Set(),propSet:new Set(),parent:f,index,phase:'advance'};s.fires.push(front);audio('madara-fire',{},!!f.actor||index>0);}
  function emitMeteors(s,f){
    const p=f.spec,t=f.target,center={x:t.x,y:t.y};f.firstLanded=false;f.fragmentsReleased=false;
    const pair=[{x:center.x,y:center.y,radius:p.radius,second:false,delay:p.fallTime,scale:1},{x:center.x,y:center.y,radius:p.secondRadius,second:true,delay:p.fallTime+p.delay,scale:1.65}];
    for(const [index,rock]of pair.entries())s.meteors.push({...source(s,f.m,'field-meteor'),spec:p,...rock,index,phase:'warning',age:0,landed:false,fallSound:false,hitSet:new Set(),propSet:new Set(),parent:f});
    s.command={x:center.x,y:center.y,target:f.target,expires:s.clock+5,kind:'meteor'};
  }
  function releaseFragments(s,second){
    const parent=second.parent,p=second.spec;if(parent.fragmentsReleased||!parent.firstLanded)return;parent.fragmentsReleased=true;
    for(let i=0;i<p.fragments;i++){const a=i*Math.PI*2/p.fragments+.35,d=p.fragmentSpread*(i%2?.65:1);s.meteors.push({...source(s,second.m,'field-meteor'),spec:p,x:second.x+Math.cos(a)*d,y:second.y+Math.sin(a)*d,radius:p.fragmentRadius,fragment:true,sourceX:second.x,sourceY:second.y,launchDelay:i*.08,flightTime:.70,flightProgress:0,height:0,delay:.70+i*.08,scale:.5,index:i+2,phase:'warning',age:0,landed:false,fallSound:false,hitSet:new Set(),propSet:new Set(),parent});}
  }

  function armyActor(s,p,index,life){
    const a=index*Math.PI*2/p.cloneCount,x=s.owner.x+Math.cos(a)*65,y=s.owner.y+Math.sin(a)*65,clearSpot=path(s.owner.x,s.owner.y,x,y);
    return {serial:++actorSequence,role:['flank-left','flank-right','front','front'][index%4],x:clearSpot?x:s.owner.x,y:clearSpot?y:s.owner.y,r:12,age:0,life,damageMultiplier:p.cloneDamageMultiplier*.65,rank:p.rank,relay:p.relay,cooldown:index*.12,guardianCooldown:index*.22,body:null,guardian:null,target:null,phase:'emerge',emerge:.60};
  }
  const armySignature=(owner,m)=>`${m.lvl}:${G.Quantity?.bonus(owner)??owner.quantityPicks??0}:${m.dmg}`;
  function spawnArmy(s,f){
    const p=f.spec;s.armyExpires=s.clock+p.cloneDuration+.60;s.armyReadyAt=s.armyExpires+p.cloneRest;s.armySignature=armySignature(s.owner,f.m);
    for(let i=s.army.length;i<p.cloneCount;i++)s.army.push(armyActor(s,p,i,p.cloneDuration+.60));audio('madara-wood');
  }
  function syncArmyGrowth(s){
    const m=learned(s.owner,'naruto-madara-clones');if(!m||!s.army.length)return;
    const signature=armySignature(s.owner,m);if(signature===s.armySignature)return;s.armySignature=signature;const p=profile(s.owner,m);
    for(const a of s.army){a.damageMultiplier=p.cloneDamageMultiplier*.65;a.rank=p.rank;a.relay=p.relay;}
    // Only new actors are added. Existing positions, actions, cooldowns and lifetime stay intact.
    for(let i=s.army.length;i<p.cloneCount;i++)s.army.push(armyActor(s,p,i,Math.max(0,s.armyExpires-s.clock)));
  }

  function advanceBody(s,f,dt){if(!legal(s,f))return false;f.age+=dt;const p=f.spec;if(f.pursuit)return advancePursuit(s,f,dt)&&legal(s,f);f.phase=bodyPose(f).phase;if(p.kind==='basic'){advanceBasic(s,f);}else if(p.kind==='fire'){while(f.emitted<p.fronts&&f.age+EPS>=p.release+p.releaseWindow*f.emitted/Math.max(1,p.fronts-1)){if(!legal(s,f))return false;emitFire(s,f,f.emitted++);}}else if(!f.released&&f.age>=p.release){f.released=true;if(p.kind==='meteor')emitMeteors(s,f);else spawnArmy(s,f);}return legal(s,f)&&f.age<p.duration;}
  function avatarOptions(g,origin,progress){return {x:origin.x,y:origin.y,height:g.actor?(g.form==='armored'?180:145):g.perfect?380:g.form==='armored'?235:170,form:g.form,phase:g.phase,age:g.swing?g.age-g.swing.start:g.age,progress,aim:g.aim,side:g.index%2?-1:1,alpha:(g.actor?.55:.6)*Math.min(1,g.age/.35,Math.max(0,(g.duration-g.age)/.30))};}
  function bladeAt(g,origin,progress){
    const options=avatarOptions(g,origin,progress),a=G.MadaraArt?.avatarSocketFor?.(origin,g.form==='rib'?'shoulder':'bladeBase',options),b=G.MadaraArt?.avatarSocketFor?.(origin,g.form==='rib'?'hand':'bladeTip',options);
    if(a&&b){g.authoredBlade=true;return {ax:a.x,ay:a.y+40,bx:b.x,by:b.y+40,radius:g.perfect?g.spec.bladeRadius*1.35:g.spec.bladeRadius,renderOffsetY:-40,frame:{sheet:b.sheet,index:b.index}};}
    g.authoredBlade=false;const length=g.perfect?g.spec.perfectLength:g.spec.bladeLength,side=g.index%2?-1:1,theta=g.aim+side*(1.2-2.4*progress);return {ax:origin.x+Math.cos(theta)*36,ay:origin.y+Math.sin(theta)*36,bx:origin.x+Math.cos(theta)*length,by:origin.y+Math.sin(theta)*length,radius:g.perfect?g.spec.bladeRadius*1.35:g.spec.bladeRadius,renderOffsetY:-40};
  }
  function guardianApproach(owner,m,actor,target,perfect=false){
    const spec=profile(owner,m),aim=angle(actor.x,actor.y,target.x,target.y),g={spec,actor:actor===owner?null:actor,form:perfect?'perfect':actor!==owner?(actor.rank>=2?'armored':'rib'):spec.form,perfect,index:0,aim,age:0,duration:6,swing:{start:0},phase:'draw'};if(actor!==owner)spec.bladeLength*=.75;let best=null;
    for(const [phase,progress]of [['draw',0],['sweep',.3],['sweep',.7]]){
      g.phase=phase;g.age=progress*spec.sweepDuration;const b=bladeAt(g,actor,progress),dx=b.bx-b.ax,dy=b.by-b.ay,t=Math.max(0,Math.min(1,((target.x-b.ax)*dx+(target.y-b.ay)*dy)/(dx*dx+dy*dy||1))),x=b.ax+dx*t,y=b.ay+dy*t,distance=Math.hypot(target.x-x,target.y-y),gap=Math.max(0,distance-b.radius-(target.r||0));
      if(!best||gap<best.gap)best={gap,distance,dx:target.x-x,dy:target.y-y};
    }return best;
  }
  function guardianTarget(owner,m,actor=owner,perfect=false){return nearest(actor,[...enemies(actor.x,actor.y,perfect?850:650),...props(actor.x,actor.y,650)],t=>path(actor.x,actor.y,t.x,t.y,t.destructible?t:null)&&guardianApproach(owner,m,actor,t,perfect).gap<=.5);}
  function emitPressure(s,g,releaseBlade=null){const o=g.actor||s.owner,b=releaseBlade||g.blade||{ax:o.x,ay:o.y,bx:o.x+Math.cos(g.aim)*40,by:o.y+Math.sin(g.aim)*40},f=source(s,g.m,'guardian-pressure',g.actor),final=!!g.finisher;Object.assign(f,{spec:{...g.spec,damage:g.spec.damage*(final?3.2:.65)},curved:final,startRadius:80,arcAngle:g.spec.finisherArc,depth:g.spec.finisherDepth,x:final?o.x:b.bx,y:final?o.y:b.by,aim:g.aim,distance:0,width:180+g.spec.rank*15,speed:final?900:850,range:final?g.spec.finisherRange:1000,hitSet:new Set(),propSet:new Set(),phase:'advance'});s.pressures.push(f);}
  function advanceGuardian(s,g,dt){
    if(!legal(s,g))return false;g.age+=dt;const p=g.spec,count=g.actor?Math.min(8,p.slashes):p.slashes,interval=(p.duration-.9)/count,at=.4+g.index*interval,origin=g.actor||s.owner;
    if(g.age>=at&&g.index<count){
      if(!g.swing){const assigned=g.actor?(guardianTarget(s.owner,g.m,origin)||g.actor.target):null,t=assigned&&registered(assigned)&&alive(assigned)?assigned:guardianTarget(s.owner,g.m,origin,g.perfect)||targetFor(s.owner,g.m,origin,g.perfect?850:650);if(t)g.aim=angle(origin.x,origin.y,t.x,t.y);g.swing={start:at,progress:0,hitSet:new Set(),propSet:new Set(),sound:false};}
      const swing=g.swing,local=g.age-swing.start;g.finisher=g.perfect&&!g.actor&&g.index===count-1;
      const progress=g.finisher?local<p.finisherCharge?.18*Math.max(0,local)/p.finisherCharge:local<p.finisherCharge+p.finisherSweep?.18+.70*(local-p.finisherCharge)/p.finisherSweep:Math.min(1,.88+.12*(local-p.finisherCharge-p.finisherSweep)/p.finisherRecovery):Math.max(0,Math.min(1,local/p.sweepDuration)),previous=swing.progress;
      g.chargeProgress=g.finisher?Math.min(1,local/p.finisherCharge):0;g.phase=progress<.18?'draw':progress<.88?'sweep':'recover';
      if(progress>=.18&&!swing.sound){swing.sound=true;audio('madara-blade',{perfect:g.perfect,finisher:g.index===count-1},!!g.actor);}
      const next=bladeAt(g,origin,progress),previousBlade=g.blade||next,n=Math.min(24,Math.max(1,Math.ceil(Math.max(Math.hypot(next.ax-previousBlade.ax,next.ay-previousBlade.ay),Math.hypot(next.bx-previousBlade.bx,next.by-previousBlade.by))/20)));
      g.prevBlade=previousBlade;g.blade=next;
      if(progress>=.18&&previous<=.88)for(let i=1;i<=n;i++){if(!legal(s,g))return false;const span=progress-previous||1,from=Math.max(0,(Math.max(.18,previous)-previous)/span),to=Math.min(1,(Math.min(.88,progress)-previous)/span),t=from+(to-from)*i/n,b={kind:'capsule',ax:previousBlade.ax+(next.ax-previousBlade.ax)*t,ay:previousBlade.ay+(next.ay-previousBlade.ay)*t,bx:previousBlade.bx+(next.bx-previousBlade.bx)*t,by:previousBlade.by+(next.by-previousBlade.by)*t,radius:next.radius,phase:'sweep',renderOffsetY:-40,frame:next.frame,previousFrame:previousBlade.frame};contact(s,g,b,g.index,{ratio:g.perfect?1.65:1,hitSet:swing.hitSet,propSet:swing.propSet,origin});}
      swing.progress=progress;
      if(!swing.pressureReleased&&progress>=.88&&g.perfect&&((g.index+1)%p.pressureEvery===0||g.index===count-1)){swing.pressureReleased=true;const release={...g,phase:'sweep',age:swing.start+p.sweepDuration*.88};emitPressure(s,g,bladeAt(release,origin,.88));}
      if(progress>=1){g.index++;g.swing=null;g.finisher=false;}
    }else if(!g.swing){g.phase=g.index>=count?'recover':g.age<.4?'manifest':g.age>g.duration-.3?'recover':'draw';g.blade=bladeAt(g,origin,0);}
    return legal(s,g)&&g.age<g.duration;
  }
  function advanceFront(s,f,dt,pressure=false){
    if(!legal(s,f))return false;const p=f.spec,speed=pressure?f.speed:p.speed,range=pressure?f.range:p.range,width=pressure?f.width:p.width;f.age+=dt;f.previousDistance=f.distance;f.distance=Math.min(range,f.distance+speed*dt);f.currentWidth=pressure?width:width*Math.min(1,.15+.85*f.distance/160);
    const geometry=f.curved?{kind:'arc',x:f.x,y:f.y,aim:f.aim,from:f.startRadius+f.previousDistance,to:f.startRadius+f.distance,arcAngle:f.arcAngle,depth:f.depth}:{kind:'wall',x:f.x,y:f.y,aim:f.aim,from:f.previousDistance,to:f.distance,width:f.currentWidth,depth:pressure?22:p.depth},result=contact(s,f,geometry,f.index??0,{hitSet:f.hitSet,propSet:f.propSet,origin:{x:f.x,y:f.y}});
    if(!legal(s,f))return false;if(!pressure&&result?.primaryHits){f.parent.hitEvents+=result.primaryHits;gain(s,f.parent);}
    if(!pressure&&!f.actor)for(const crater of s.craters){if(!crater.relay||f.parent.relayed||!path(f.x,f.y,crater.x,crater.y)||!inside(geometry,{x:crater.x,y:crater.y,r:crater.radius*.4}))continue;f.parent.relayed=true;const r=source(s,f.m,'field-rubble');r.spec={...p,damage:p.damage*.65};const circle={kind:'circle',x:crater.x,y:crater.y,radius:crater.radius*.72};contact(s,r,circle,0);s.effects.push({kind:'rubble',x:circle.x,y:circle.y,radius:circle.radius,age:0,life:.45});break;}
    if(f.distance>=range){if(!pressure&&p.linger){const end=range*.88,x=f.x+Math.cos(f.aim)*end,y=f.y+Math.sin(f.aim)*end;s.flames.push({...source(s,f.m,f.actor?'army-flame':'field-flame',f.actor),spec:{...p,damage:p.damage*.28},x,y,aim:f.aim,width,age:0,next:0,ticks:0,duration:p.linger,parent:f.parent,phase:'burn'});}return false;}return true;
  }
  function advanceFlame(s,f,dt){if(!legal(s,f))return false;f.age+=dt;const p=f.spec;while(f.ticks<p.lingerTicks&&f.age>=f.next){const g={kind:'capsule',ax:f.x-Math.sin(f.aim)*f.width/2,ay:f.y+Math.cos(f.aim)*f.width/2,bx:f.x+Math.sin(f.aim)*f.width/2,by:f.y-Math.cos(f.aim)*f.width/2,radius:25};contact(s,f,g,f.ticks++);f.next+=f.duration/p.lingerTicks;if(!legal(s,f))return false;}return f.age<f.duration;}
  function advanceMeteor(s,f,dt){
    if(!legal(s,f))return false;f.age+=dt;const left=f.delay-f.age;if(f.fragment){f.flightProgress=Math.max(0,Math.min(1,(f.age-f.launchDelay)/f.flightTime));f.height=Math.sin(f.flightProgress*Math.PI)*140;f.phase=f.age<f.launchDelay?'emerge':left>0?'flight':'impact';}else{f.height=Math.max(0,left)*650;f.phase=left>.65?'warning':left>0?'fall':'impact';}if(left<.65&&!f.fallSound){f.fallSound=true;audio('madara-fall',{second:f.second},f.fragment);}
    if(left<=0&&!f.landed){if(f.second&&!f.parent.firstLanded)return false;f.landed=true;contact(s,f,{kind:'circle',x:f.x,y:f.y,radius:f.radius},f.index,{ratio:f.scale,hitSet:f.hitSet,propSet:f.propSet});if(!legal(s,f))return false;audio('madara-meteor',{second:f.second},f.fragment);if(f.second)s.effects=s.effects.filter(e=>!e.first||e.pair!==f.parent);s.effects.push({kind:'meteor-impact',x:f.x,y:f.y,radius:f.radius,second:f.second,fragment:f.fragment,first:!f.fragment&&!f.second,pair:f.parent,age:0,life:!f.fragment&&!f.second?f.spec.delay+.1:.9});if(!f.fragment&&!f.second){f.parent.firstLanded=true;}if(!f.fragment&&!f.second)s.craters.push({moveId:f.m.id,x:f.x,y:f.y,radius:f.radius,age:0,duration:f.spec.craterDuration,relay:f.spec.craterRelay});if(f.second){releaseFragments(s,f);s.command={x:f.x,y:f.y,target:null,expires:s.clock+3,kind:'meteor'};for(const a of s.army)if(a.relay)a.cooldown=0;}}
    return f.age<f.delay+.4;
  }
  function armyLeash(){
    const camera=G.Camera,pixels=(camera.w||768)*(camera.scale||1),height=(camera.h||420)*(camera.scale||1),native=camera.viewportScale?.(pixels,height)||camera.scale||1;
    return Math.max(150,Math.min(280,pixels/native*.29));
  }
  function armyMove(s,a,dt){
    const fire=learned(s.owner,'naruto-madara-fire'),guard=learned(s.owner,'naruto-madara-susanoo'),basic=learned(s.owner,'naruto-madara'),desired=a.role.startsWith('flank')&&fire?fire:basic||fire;if(!desired)return;
    const leash=armyLeash();
    if(a.target&&(!registered(a.target)||!alive(a.target)||Math.hypot(a.target.x-s.owner.x,a.target.y-s.owner.y)>leash+550))a.target=null;
    if(a.target&&s.clock>=(a.pathCheckAt||0)){a.pathCheckAt=s.clock+.12;if(!path(a.x,a.y,a.target.x,a.target.y))a.target=null;}
    if(!a.target&&s.clock>=(a.acquireAt||0)){
      const claimed=new Set(s.army.filter(other=>other!==a&&other.target).map(other=>other.target)),command=a.relay&&s.command?.expires>s.clock?s.command:null;
      let score=Infinity;
      for(const e of enemies(s.owner.x,s.owner.y,leash+500)){const value=Number(claimed.has(e))+(command?Math.hypot(e.x-command.x,e.y-command.y)*.001:0);if(value>=score||!path(a.x,a.y,e.x,e.y))continue;a.target=e;score=value;}
      a.acquireAt=a.target?0:s.clock+.10+(a.serial%4)*.01;a.pathCheckAt=s.clock+.12;
    }
    const t=a.target,index=s.army.indexOf(a),side=a.role==='flank-left'?-1:a.role==='flank-right'?1:index%2?-1:1,ring=Math.floor(index/4),slot={x:s.owner.x+side*Math.min(leash*.85,100+ring*38),y:s.owner.y+30+(index%4>=2?55:0)};
    let x=slot.x,y=slot.y;
    if(t&&desired.madaraKind==='basic'){
      const reach=basicApproach(a,t,profile(s.owner,desired)),ratio=reach.distance?Math.min(1,(reach.gap+2)/reach.distance):0;x=a.x+reach.dx*ratio;y=a.y+reach.dy*ratio;
    }else if(t)y+=Math.max(-40,Math.min(45,(t.y-s.owner.y)*.15));
    // Keep the army beside its owner while walking normally; melee retains real contact.
    const dx=x-s.owner.x,dy=y-s.owner.y,d=Math.hypot(dx,dy);if(d>leash){x=s.owner.x+dx/d*leash;y=s.owner.y+dy/d*leash;}
    if(!a.body&&a.guardian?.phase!=='sweep')toward(a,x,y,Math.max(400,s.owner.spd||0)*dt);
    if(!t)return;
    // Guardian is an independent actor channel: it never reserves the clone's body.
    if(guard&&!a.guardian&&a.guardianCooldown<=EPS&&s.clock>=(a.guardianCheckAt||0)){a.guardianCheckAt=s.clock+.10;const victim=guardianApproach(s.owner,guard,a,t).gap<=.5?t:guardianTarget(s.owner,guard,a);if(victim){a.guardian=makeGuardian(s,guard,a,victim);if(a.guardian)a.guardianCooldown=Math.max(6.2,guard.cd*(s.owner.cdMul??1));}}
    if(a.body||a.cooldown>EPS)return;
    const bodyMove=desired.madaraKind==='basic'&&basicApproach(a,t,profile(s.owner,desired)).gap>.5?fire:desired;if(!bodyMove)return;
    a.body=makeBody(s,bodyMove,a,t);if(a.body)a.cooldown=Math.max(.7,bodyMove.cd*(s.owner.cdMul??1));
  }
  function update(dt){
    if(G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;const steps=Math.min(60,Math.max(1,Math.ceil(dt/.025))),h=dt/steps;
    for(let step=0;step<steps;step++)for(const [owner,s]of [...states]){
      if(!valid(owner)||s.world!==G.World||s.epoch!==G.CombatPulse.epoch){clear(owner);continue;}
      // Explicit contract: freeze suspends this owner's released fields as well as body/army.
      if(owner.frozen)continue;s.clock+=h;for(const e of s.effects)e.age+=h;s.effects=s.effects.filter(e=>e.age<e.life);for(const c of s.craters)c.age+=h;s.craters=s.craters.filter(c=>c.age<c.duration&&!!learned(owner,c.moveId));
      if(s.body&&!advanceBody(s,s.body,h))s.body=null;if(states.get(owner)!==s)continue;if(s.guardian&&!advanceGuardian(s,s.guardian,h))s.guardian=null;if(states.get(owner)!==s)continue;
      const advanceList=(key,fn)=>{for(const f of [...s[key]]){if(!fn(s,f,h)){const i=s[key].indexOf(f);if(i>=0)s[key].splice(i,1);}if(states.get(owner)!==s)break;}};
      advanceList('fires',advanceFront);advanceList('flames',advanceFlame);advanceList('meteors',advanceMeteor);advanceList('pressures',(state,f,delta)=>advanceFront(state,f,delta,true));if(states.get(owner)!==s)continue;
      if(!learned(owner,'naruto-madara-clones'))s.army.length=0;else syncArmyGrowth(s);
      for(const a of [...s.army]){a.age+=h;a.cooldown=Math.max(0,a.cooldown-h);a.guardianCooldown=Math.max(0,(a.guardianCooldown||0)-h);if(a.age>=a.life){s.effects.push({kind:'wood-dismiss',x:a.x,y:a.y,age:0,life:.45});s.army.splice(s.army.indexOf(a),1);continue;}if(a.age<a.emerge)continue;if(a.body&&!advanceBody(s,a.body,h))a.body=null;if(a.guardian&&!advanceGuardian(s,a.guardian,h))a.guardian=null;if(states.get(owner)!==s)break;a.phase=a.body?'cast':a.guardian?'guardian':'move';armyMove(s,a,h);}
    }
  }
  function tick(dt,owner,now){if((owner?.mon?.dex??owner?.dex)!==DEX)return oldTick.call(this,dt,owner,now);if(!valid(owner)||owner.frozen||G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;const s=state(owner),moves=owner.moves.filter(m=>ids.has(m.id));for(const m of moves){m.t=Math.max(0,(m.t||0)-dt);if(m.t<=EPS&&!s.readyAt.has(m.id))s.readyAt.set(m.id,s.clock);}const guardian=moves.find(m=>m.madaraKind==='susanoo');if(guardian&&canCast(owner,guardian))cast(owner,guardian);if(s.body)return;const ready=moves.filter(m=>m.madaraKind!=='susanoo'&&canCast(owner,m)).sort((a,b)=>(s.readyAt.get(a.id)??s.clock)-(s.readyAt.get(b.id)??s.clock));if(ready[0])cast(owner,ready[0]);}
  function pose(owner){const s=states.get(owner);return valid(owner)&&s?.world===G.World&&s.epoch===G.CombatPulse.epoch?bodyPose(s.body):null;}
  function guardianPose(owner){const s=states.get(owner);if(!valid(owner)||s?.world!==G.World||s.epoch!==G.CombatPulse.epoch)return null;const g=s.guardian;return g?{form:g.form,phase:g.phase,height:avatarOptions(g,g.actor||owner,g.swing?.progress||0).height,age:g.swing?g.age-g.swing.start:g.age,aim:g.aim,side:g.index%2?-1:1,blade:g.blade,prevBlade:g.prevBlade,perfect:g.perfect,remaining:g.duration-g.age}:null;}
  function drawBlade(ctx,g,alpha=1){const b=g.blade;if(!b||g.authoredBlade)return;ctx.save();ctx.globalAlpha*=alpha;ctx.lineCap='round';ctx.strokeStyle=g.perfect?'#7caaff':'#739ddd';ctx.lineWidth=b.radius*1.2;ctx.beginPath();ctx.moveTo(b.ax,b.ay+b.renderOffsetY);ctx.lineTo(b.bx,b.by+b.renderOffsetY);ctx.stroke();ctx.strokeStyle='#d6efff';ctx.lineWidth=b.radius*.36;ctx.beginPath();ctx.moveTo(b.ax,b.ay+b.renderOffsetY);ctx.lineTo(b.bx,b.by+b.renderOffsetY);ctx.stroke();ctx.restore();}
  function armyOpacity(s,x,y){const owner=G.Game.player;if(!owner||s.owner!==owner||s.army.length<4)return 1;const near=Math.max(0,1-Math.hypot(x-owner.x,(y-owner.y)*.75)/200),density=Math.min(1,(s.army.length-2)/10);return Math.max(.22,1-density*(.22+.56*near));}
  function drawGuardian(ctx,s,g){const o=g.actor||s.owner,options=avatarOptions(g,o,g.swing?.progress||0),opacity=g.actor?armyOpacity(s,o.x,o.y):1;options.alpha*=opacity;options.blade=g.blade;options.prevBlade=g.prevBlade;if(G.MadaraArt?.drawAvatar)G.MadaraArt.drawAvatar(ctx,options);else{ctx.save();ctx.globalAlpha=options.alpha;ctx.strokeStyle='#70a5e2';ctx.lineWidth=5;for(let i=0;i<4;i++){ctx.beginPath();ctx.ellipse(o.x,o.y-35-i*20,options.height*.27,options.height*.13,0,0,Math.PI);ctx.stroke();}ctx.restore();}if(g.phase==='sweep'||g.phase==='draw')drawBlade(ctx,g,(g.phase==='sweep'?.85:.3)*opacity);drawFinisherCharge(ctx,g);}
  function secondaryFireOpacity(){
    let layers=0;
    for(const s of states.values()){
      if(!valid(s.owner)||s.world!==G.World||s.epoch!==G.CombatPulse.epoch)continue;
      for(const f of s.fires)if((f.actor||s.owner!==G.Game.player)&&drawable(s,f))layers++;
      for(const f of s.flames)if((f.actor||s.owner!==G.Game.player)&&drawable(s,f))layers++;
    }
    // Preserve the main breath; many independent clone layers share a visual budget.
    return Math.min(1,12/Math.max(12,layers));
  }
  function drawCrescent(ctx,f){
    const radius=f.startRadius+f.distance,half=f.arcAngle/2,fade=Math.min(1,f.age/.08,Math.max(0,(f.range-f.distance)/150));
    ctx.save();ctx.translate(f.x,f.y-40);ctx.rotate(f.aim);ctx.lineJoin='round';
    for(const [thickness,alpha,color]of [[f.depth*1.35,.2,'#75b9ff'],[f.depth*.65,.72,'#a8d8ff'],[f.depth*.18,.95,'#edfaff']]){
      ctx.beginPath();
      for(let i=0;i<=40;i++){const u=i/40,a=-half+u*half*2,r=radius+Math.sin(u*Math.PI)*thickness;const x=Math.cos(a)*r,y=Math.sin(a)*r;if(!i)ctx.moveTo(x,y);else ctx.lineTo(x,y);}
      for(let i=40;i>=0;i--){const u=i/40,a=-half+u*half*2,r=radius-Math.sin(u*Math.PI)*thickness;ctx.lineTo(Math.cos(a)*r,Math.sin(a)*r);}
      ctx.closePath();ctx.fillStyle=color;ctx.globalAlpha=alpha*fade;ctx.fill();
    }
    ctx.restore();
  }
  function drawFinisherCharge(ctx,g){
    if(!g.finisher||g.phase!=='draw'||!g.blade)return;
    const b=g.blade,t=g.chargeProgress;
    ctx.save();ctx.globalAlpha=.3+.4*t;ctx.strokeStyle='#b2e6ff';ctx.lineWidth=3+5*t;
    ctx.beginPath();ctx.moveTo(b.ax,b.ay-40);ctx.lineTo(b.bx,b.by-40);ctx.stroke();
    for(let i=0;i<6;i++){const a=i*Math.PI/3+g.age*2,r=20+50*(1-t),x=b.bx+Math.cos(a)*r,y=b.by-40+Math.sin(a)*r*.65;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+Math.cos(a)*12,y+Math.sin(a)*8);ctx.stroke();}
    ctx.restore();
  }
  function drawFront(ctx,f,pressure=false,crowd=1){if(f.curved){drawCrescent(ctx,f);return;}const s=states.get(f.owner),opacity=(f.actor&&s?armyOpacity(s,f.x+Math.cos(f.aim)*f.distance,f.y+Math.sin(f.aim)*f.distance):1)*(!pressure&&(f.actor||f.owner!==G.Game.player)?crowd:1),p=f.spec,d=f.distance,width=f.currentWidth??(pressure?f.width:p.width),offset=pressure?-40:f.visualOffsetY;if(!pressure&&G.MadaraArt?.drawElement?.(ctx,{kind:'fire',phase:'wall',alpha:(f.actor?.50:.72)*opacity,x:f.x+Math.cos(f.aim)*d,y:f.y+Math.sin(f.aim)*d+offset,width,depth:p.depth*2,aim:f.aim,age:f.age,progress:d/p.range}))return;ctx.save();ctx.translate(f.x,f.y+offset);ctx.rotate(f.aim);ctx.globalAlpha=(pressure?.65:.67)*opacity;ctx.strokeStyle=pressure?'#a8d6ff':'#d84b22';ctx.lineWidth=pressure?18:26;ctx.beginPath();ctx.moveTo(d,-width/2);ctx.lineTo(d,width/2);ctx.stroke();const count=pressure?8:Math.max(8,Math.min(20,Math.round(width/25)));for(let i=0;i<count;i++){const y=(i/(count-1)-.5)*width,wave=Math.sin(f.age*16+i*2.4),length=pressure?30:28+wave*12;ctx.fillStyle=pressure?'#e3f7ff':i%3?'#fa8a28':'#ffd35b';ctx.beginPath();ctx.moveTo(d-18,y-12);ctx.quadraticCurveTo(d+length,y-15,d+length+6,y);ctx.quadraticCurveTo(d+length*.4,y+4,d-18,y+12);ctx.closePath();ctx.fill();}ctx.restore();}
  function drawArmy(ctx,s,a){ctx.save();const emergePhase=a.age<.18?'root':a.age<.40?'separate':'reveal';if(a.age<a.emerge)G.MadaraArt?.drawElement?.(ctx,{kind:'wood',phase:emergePhase,x:a.x,y:a.y,height:64,age:a.age,progress:a.age/a.emerge});ctx.globalAlpha=Math.max(0,Math.min(1,(a.age-.40)/.20))*.88;const p=bodyPose(a.body);G.MadaraArt?.draw(ctx,a,{x:a.x,y:a.y,height:64,state:p?'cast':a.phase==='move'?'walk':'idle',time:p?.age??a.age,dir:G.Sprites?.dirFromAngle?.(p?.aim??a.guardian?.aim??(a.target?angle(a.x,a.y,a.target.x,a.target.y):0))??2,pose:p});ctx.strokeStyle='#adbd82';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(a.x-8,a.y+1);ctx.lineTo(a.x+8,a.y+1);ctx.stroke();ctx.restore();}
  function drawables(){
    if(!['playing','paused','levelup'].includes(G.Game.state))return [];
    const result=[];
    for(const s of states.values()){
      if(!valid(s.owner)||s.world!==G.World||s.epoch!==G.CombatPulse.epoch)continue;
      if(s.guardian&&drawable(s,s.guardian)){const g=s.guardian;result.push({y:s.owner.y-.01,draw(ctx){drawGuardian(ctx,s,g);}});}
      for(const a of s.army){if(a.guardian&&drawable(s,a.guardian)){const g=a.guardian;result.push({y:a.y-.01,draw(ctx){drawGuardian(ctx,s,g);}});}result.push({y:a.y,draw(ctx){drawArmy(ctx,s,a);}});}
    }
    return result;
  }
  function drawImpactGround(ctx,e){
    const t=e.age/e.life;ctx.save();ctx.globalAlpha=e.first?1:1-t;
    if(!G.MadaraArt?.drawElement?.(ctx,{kind:e.kind==='meteor-impact'&&!e.second&&!e.fragment?'fracture':'rubble',phase:'impact',x:e.x,y:e.y,radius:e.radius,age:e.age,progress:t,second:e.second})){ctx.strokeStyle=e.second?'#b8a0e0':'#c49c77';ctx.lineWidth=6;ctx.beginPath();ctx.arc(e.x,e.y,e.radius*(.6+.4*t),0,Math.PI*2);ctx.stroke();}
    ctx.restore();
  }
  function draw(ctx,ground=false){
    if(!['playing','paused','levelup'].includes(G.Game.state))return;
    const crowd=ground?1:secondaryFireOpacity();
    for(const s of states.values()){
      if(!valid(s.owner)||s.world!==G.World||s.epoch!==G.CombatPulse.epoch)continue;
      if(ground){
        for(const e of s.effects)if(e.kind==='meteor-impact'||e.kind==='rubble')drawImpactGround(ctx,e);
        for(const c of s.craters){ctx.save();ctx.globalAlpha=.35*(1-c.age/c.duration);ctx.strokeStyle='#5c5060';ctx.lineWidth=5;for(let i=0;i<8;i++){const a=i*Math.PI/4;ctx.beginPath();ctx.moveTo(c.x+Math.cos(a)*c.radius*.35,c.y+Math.sin(a)*c.radius*.35);ctx.lineTo(c.x+Math.cos(a+.13)*c.radius,c.y+Math.sin(a+.13)*c.radius);ctx.stroke();}ctx.restore();}
        for(const f of s.meteors){if(!drawable(s,f)||f.landed)continue;ctx.save();ctx.globalAlpha=f.fragment?.24:.42;ctx.strokeStyle=f.second?'#c9b3e9':'#cba980';ctx.lineWidth=f.fragment?1:3;ctx.beginPath();ctx.arc(f.x,f.y,f.radius,0,Math.PI*2);ctx.stroke();ctx.fillStyle='#1b1426';ctx.globalAlpha=.15;ctx.beginPath();ctx.ellipse(f.x,f.y,f.radius*.65,f.radius*.3,0,0,Math.PI*2);ctx.fill();ctx.restore();}continue;
      }

      for(const f of s.fires)if(drawable(s,f))drawFront(ctx,f,false,crowd);for(const f of s.pressures)if(drawable(s,f))drawFront(ctx,f,true);
      for(const f of s.flames){if(!drawable(s,f))continue;const opacity=(f.actor?armyOpacity(s,f.x,f.y):1)*((f.actor||f.owner!==G.Game.player)?crowd:1);if(G.MadaraArt?.drawElement?.(ctx,{kind:'fire',phase:'tail',alpha:.55*(1-f.age/f.duration)*opacity,x:f.x,y:f.y-32,width:f.width,depth:50,aim:f.aim,age:f.age,progress:f.age/f.duration}))continue;ctx.save();ctx.translate(f.x,f.y-32);ctx.rotate(f.aim);ctx.globalAlpha=.55*(1-f.age/f.duration)*opacity;for(let i=0;i<12;i++){const y=(i/11-.5)*f.width,h=12+7*Math.sin(f.age*18+i*2);ctx.fillStyle=i%2?'#ec6a1e':'#ffc34b';ctx.beginPath();ctx.moveTo(-9,y-7);ctx.lineTo(h,y);ctx.lineTo(-9,y+7);ctx.closePath();ctx.fill();}ctx.restore();}
      for(const f of s.meteors){if(!drawable(s,f)||f.landed)continue;const left=f.delay-f.age;if(left>.65)continue;const h=f.height??Math.max(0,left)*650,r=f.radius*(f.fragment?.32:.58),px=f.fragment?f.sourceX+(f.x-f.sourceX)*f.flightProgress:f.x-h*.15,py=f.fragment?f.sourceY+(f.y-f.sourceY)*f.flightProgress:f.y;if(G.MadaraArt?.drawElement?.(ctx,{kind:'meteor',phase:f.fragment?'flight':'fall',x:px,y:py-h-r,radius:r,collisionRadius:f.radius,age:f.age,progress:f.fragment?f.flightProgress:1-left/.65,height:h,second:f.second,fragment:f.fragment}))continue;ctx.save();ctx.translate(px,py-h-r);ctx.globalAlpha=.94;ctx.fillStyle=f.fragment?'#74626a':f.second?'#756581':'#8e7666';ctx.strokeStyle='#c4a68e';ctx.lineWidth=f.fragment?2:5;ctx.beginPath();for(let i=0;i<12;i++){const a=i*Math.PI/6,rr=r*(.92+.08*Math.sin(i*5+f.index));i?ctx.lineTo(Math.cos(a)*rr,Math.sin(a)*rr):ctx.moveTo(Math.cos(a)*rr,Math.sin(a)*rr);}ctx.closePath();ctx.fill();ctx.stroke();ctx.strokeStyle='#3b3440';ctx.lineWidth=3;for(let i=0;i<4;i++){ctx.beginPath();ctx.moveTo(-r*.7+i*r*.4,-r*.55);ctx.lineTo(-r*.35+i*r*.3,r*.5);ctx.stroke();}ctx.restore();}
      for(const e of s.effects){const t=e.age/e.life;ctx.save();ctx.globalAlpha=e.first?1:1-t;if(['meteor-impact','rubble'].includes(e.kind)){ctx.fillStyle='#8f7468';for(let i=0;i<10;i++){const a=i*Math.PI/5,d=e.radius*t;ctx.fillRect(e.x+Math.cos(a)*d,e.y+Math.sin(a)*d-Math.sin(t*Math.PI)*65,5,5);}ctx.restore();continue;}if(e.kind==='wood-dismiss'){G.MadaraArt?.drawElement?.(ctx,{kind:'wood',phase:'dismiss',x:e.x,y:e.y,height:64,age:e.age,progress:t});}else if(e.kind==='contact'){ctx.strokeStyle='#f5d7af';ctx.lineWidth=2;ctx.beginPath();ctx.arc(e.x,e.y,e.radius*(.4+t),0,Math.PI*2);ctx.stroke();}else{ctx.strokeStyle=e.second?'#b8a0e0':'#c49c77';ctx.lineWidth=e.kind==='meteor-impact'?7:4;ctx.beginPath();ctx.arc(e.x,e.y,e.radius*(.6+.4*t),0,Math.PI*2);ctx.stroke();ctx.fillStyle='#8f7468';for(let i=0;i<12;i++){const a=i*Math.PI/6,d=e.radius*t;ctx.fillRect(e.x+Math.cos(a)*d,e.y+Math.sin(a)*d-Math.sin(t*Math.PI)*65,5,5);}}ctx.restore();}
    }
  }
  function drawLocalSilhouette(ctx){
    const owner=G.Game.player,s=states.get(owner);if(!valid(owner)||!s||s.world!==G.World||s.epoch!==G.CombatPulse.epoch||s.army.length<4||!['playing','paused','levelup'].includes(G.Game.state))return;
    if(!s.army.some(a=>Math.hypot(a.x-owner.x,a.y-owner.y)<220))return;
    const p=bodyPose(s.body),height=64*(owner.anim?.scale||1),time=p?.age??((owner.anim?.frame||0)*6+(owner.anim?.t||0))/60;
    ctx.save();ctx.shadowColor='#141320';ctx.shadowBlur=2;G.MadaraArt?.draw(ctx,owner,{x:owner.x,y:owner.y,height,state:p?'cast':owner.walking?'walk':'idle',time,dir:owner.anim?.dir??2,pose:p,flash:owner.flash>0});ctx.restore();
  }
  const oldTick=C.tick,oldUpdate=C.updateFields,oldClear=C.clearFields,oldAir=C.drawAirFields,oldGround=C.drawGroundFields;
  C.tick=tick;C.updateFields=function(dt){const r=oldUpdate.call(this,dt);update(dt);return r;};C.clearFields=function(owner){const r=oldClear.call(this,owner);clear(owner);return r;};C.drawAirFields=function(ctx){oldAir.call(this,ctx);draw(ctx);drawLocalSilhouette(ctx);};C.drawGroundFields=function(ctx){oldGround.call(this,ctx);draw(ctx,true);};
  function statusFor(owner,m){const s=states.get(owner),kind=m.madaraKind,active=kind==='susanoo'?s?.guardian:kind==='clones'?s?.army.length:kind==='fire'?s?.fires.some(f=>!f.actor):kind==='meteor'?s?.meteors.length:s?.body?.m.id===m.id;const remaining=Math.max(m.t||0,kind==='clones'?Math.max(0,(s?.armyReadyAt||0)-(s?.clock||0)):0);return {state:active?'active':remaining>EPS?'cooldown':kind!=='susanoo'&&s?.body?'queued':'ready',remaining:kind==='susanoo'&&s?.guardian?s.guardian.duration-s.guardian.age:remaining,impetus:s?.impetus||0,perfect:!!s?.guardian?.perfect,reason:kind==='susanoo'?'guardian':null};}
  const nativeHurt=G.Player.prototype.hurt;
  G.Player.prototype.hurt=function(amount,type=null,pure=false,context=null){
    const s=states.get(this),f=s?.body,attack=context?.cause==='contact'||context?.cause==='projectile';
    if(this===G.Game.player&&G.Game.state==='playing'&&!this.frozen&&this.invuln<=0&&Number.isFinite(amount)&&amount>0&&!pure&&attack&&
      f?.pursuit&&f.age>=f.spec.charge&&['approach','contact'].includes(f.pursuitPhase)&&legal(s,f)&&Math.random()<f.spec.dodgeChance){
      G.FX.dmgText(this.x,this.y-(this.bodyH||64)-6,G.I18n.lang==='en'?'Dodge':'閃避','#b9efab');
      return;
    }
    return nativeHurt.apply(this,arguments);
  };
  const nativeSkillState=G.RunInsights?.skillState;
  if(nativeSkillState)G.RunInsights.skillState=function(owner,m){if(!ids.has(m?.id))return nativeSkillState(owner,m);const s=states.get(owner),p=profile(owner,m),status=statusFor(owner,m),body=s?.body?.m.id===m.id?s.body:null,en=G.I18n.lang==='en';let label;if(p.kind==='susanoo')label=s?.guardian?(s.guardian.perfect?(en?'Perfect ':'完成體 '):(en?'Guardian ':'須佐 '))+status.remaining.toFixed(1)+'s':`${en?'Momentum':'勢能'} ${s?.impetus||0}/3`;else if(body)label=body.spec.kind==='basic'?`${en?'Contact':'接觸'} ${body.index}/${body.spec.contacts}`:en?'Casting':'施術中';else if(p.kind==='clones'&&s?.army.length)label=`${en?'Army':'軍團'} ${s.army.length}`;else if(p.kind==='fire'&&s?.fires.some(f=>!f.actor))label=`${en?'Fire fronts':'火牆'} ${s.fires.filter(f=>!f.actor).length}`;else if(p.kind==='meteor'&&s?.meteors.length)label=`${en?'Falling rocks':'落石'} ${s.meteors.filter(f=>!f.landed).length}`;else label=status.state==='queued'?(en?'Queued':'待本體'):status.remaining>EPS?status.remaining.toFixed(1)+'s':en?'Ready':'就緒';return {label,fraction:s?.guardian&&p.kind==='susanoo'?status.remaining/s.guardian.duration:Math.min(1,(m.t||0)/Math.max(.05,m.cd*(owner.cdMul??1)))};};
  G.NarutoMadara={version:3,dex:DEX,kit,supports,profile,vector,targetFor,canCast,cast,update,clear,pose,guardianPose,statusFor,draw,drawables,
    stateFor:(a=G.Game.player)=>states.get(a)||null,stats:(a=G.Game.player)=>{const s=states.get(a);return s?{casts:{...s.casts},hits:s.hits,damage:s.damage,propHits:s.propHits,propDamage:s.propDamage,impetus:s.impetus,perfectCount:s.perfectCount,army:s.army.length,fronts:s.fires.length,meteors:s.meteors.length,hitContacts:s.hitContacts.map(c=>({...c,geometry:{...c.geometry}})),contacts:s.contacts.map(c=>({...c,geometry:{...c.geometry}}))}:null;}};
})();
