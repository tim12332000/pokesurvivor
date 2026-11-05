/* Reanimated Madara: owned timed contacts, persistent wood doubles, no forced player movement. */
(() => {
  'use strict';
  if(G.NarutoMadara)return;
  const DEX=30016,C=G.Combat,EPS=1e-8,states=new Map();
  const rows=[
    ['naruto-madara','basic','戰場演舞','fighting',1,.95,24,105,90,'掌擊接續四段短距衝擊（本作改編），隨本體走位逐段索敵。數量卡增加真實連擊，最多12段。'],
    ['naruto-madara-fire','fire','火遁・豪火滅卻','fire',3,5,42,430,210,'從嘴部吐出寬幅火幕，連續4→8波覆蓋前方；數量卡至16波。每波跟隨本體位置與可達敵群，不強迫位移。'],
    ['naruto-madara-susanoo','susanoo','須佐能乎・巨刃連斬','psychic',6,7.5,78,460,240,'藍色須佐現出肋骨、頭與雙臂，交替巨刃橫掃4→8次。數量卡至16斬，收尾重斬更強；不改變本體碰撞或無敵。'],
    ['naruto-madara-meteor','meteor','天礙震星・雙重落石','rock',9,13,155,700,250,'短結印後兩顆巨石先後落向鎖定的固定位置；每顆有獨立預告與命中。再爆發共4→8輪衝擊波，數量卡至16波。可撤出落點的敵人不受傷。名稱與自動施放屬本作改編。'],
    ['naruto-madara-clones','clones','木遁・木分身','grass',12,18,32,500,180,'召出2→4名實體木分身協戰12秒，各自追近可達敵人；已學須佐時各自連斬，否則使用已學火遁或體術。數量卡至6名，火力段數同受數量成長；每階分身火力100→210%。不是玩家自身分身卡。']
  ];
  const ids=new Set(rows.map(r=>r[0])),kit=[DEX,rows.map(([id,kind,name,type,level])=>[id,kind,name,type,level])];
  const rank=m=>Math.max(1,Math.min(5,Math.floor(m?.lvl||1)));
  const count=(a,n,cap)=>Math.min(cap,G.Quantity?.count(a,n)??n);
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const controlled=a=>G.SelfClones?.isControlled?.(a)??(a===G.Game.player||!!G.SelfClones?.isActor?.(a));
  const valid=a=>alive(a)&&controlled(a)&&(a.mon?.dex??a.dex)===DEX;
  const supports=m=>typeof m==='string'?m.startsWith('madara-'):ids.has(m?.id);
  function profile(a,m){
    const i=rank(m)-1,kind=m.madaraKind||m.digiMode?.replace('madara-','')||'basic';
    const basic=kind==='basic',fire=kind==='fire',susanoo=kind==='susanoo',meteor=kind==='meteor';
    const pulses=count(a,4+i,basic?12:16),interval=basic?.14:fire?.19:susanoo?.27:.26;
    const charge=basic?.10:fire?.35:susanoo?.32:meteor?.60:.35;
    return {kind,pulses,interval,charge,range:m.range,radius:m.radius,arc:basic?2.5:fire?2.3:3.7,
      damage:m.dmg*(a.atk??1),cloneDamageMultiplier:kind==='clones'?m.dmg/32:1,duration:meteor?3.8+(pulses-4)*interval:charge+(pulses-1)*interval+.25,
      cloneCount:count(a,2+Math.floor(i/2),6),cloneDuration:12,meteorCount:2,meteorDelay:.85};
  }
  function vector(a,m){const p=profile(a,m);return p.kind==='clones'?{木分身:p.cloneCount}:p.kind==='meteor'?{隕石:2,衝擊波:p.pulses}:{[p.kind==='basic'?'體術段數':p.kind==='fire'?'火幕波次':'巨刃斬數']:p.pulses};}
  const catalog=G.NarutoSkillCatalog;
  for(const [id,kind,name,type,learnLevel,cd,dmg,range,radius,desc]of rows){
    const ups=Array.from({length:4},(_,i)=>({t:`傷害、範圍與真實段數成長；${kind==='clones'?'分身協戰強化':kind==='meteor'?'雙隕石衝擊波':'連段'}強化`,m:{dmg:[1.2,1.45/1.2,1.75/1.45,2.1/1.75][i],range:range+(kind==='basic'?15:40)*(i+1),radius:(radius+25*(i+1))/(radius+25*i)}}));
    const def={id,name,icon:id,type,kind:'melee',madaraKind:kind,digiMode:'madara-'+kind,digimonSkill:true,narutoSkill:true,passive:true,autoCast:true,learnLevel,cd,dmg,range,radius,width:radius*2,maxLvl:5,ups,desc:desc+' 自動施放，不占主動槽。',source_url:'https://naruto-action.bn-ent.net/special/dlc_09.php'};
    G.Moves.BY_ID[id]=def;G.Moves.ALL.push(def);catalog.definitions.set(id,def);
    G.Icons.UI[id]={pal:{r:'#c54a3e',b:'#71b6f3',w:'#f8dcac',k:'#151923'},outline:true,rows:kind==='fire'?['.....r......','....rr......','..r.rr.r....','..rrrrrrr...','.rrrrwwrrr..','rrrwwwwwrrr.','.rrwwwwwrr..','..rrwwwrr...','...rrrrr....','....rrr.....','.....r......','............']:kind==='meteor'?['rr..........','.rr.........','..rr........','...rr.......','....kkkk....','...kwwwwk...','..kwwrrwwk..','..kwrrrrwk..','..kwrrrrwk..','...kwwwwk...','....kkkk....','............']:kind==='clones'?['...kk..kk...','..kwwkkwwk..','..krwkkrwk..','...kk..kk...','..rrrrrrrr..','.rrrrrrrrrr.','..rrrrrrrr..','..rrrrrrrr..','...kk..kk...','..kkk..kkk..','..k.k..k.k..','............']:['...bbbbbb...','..bwwwwwwb..','.bwkwwkwb...','.bwwwwwwb...','..bbbbbb....','.bbwwwwbb...','bbwwwwwwbb..','b.bwwwwb.b..','..bwwwwb....','..bb..bb....','.bb....bb...','............']};
    G.JujutsuGrowth?.registerQuantityConsumer(def.digiMode,vector);
  }
  const englishNames=['Battlefield Palm Combo','Fire Release: Majestic Destroyer Flame','Susanoo: Giant Blade Barrage','Heaven Concealed: Twin Meteors','Wood Release: Wood Clones'];
  const englishDescriptions=[
    'Four short-range palm shockwaves, adapted for this game. Each rank adds a hit and range; quantity cards multiply hits, capped at 12. No forced movement.',
    'Exhale a broad cone of fire for 4 to 8 real waves, up to 16 with quantity cards. Each wave follows your position and retargets reachable enemies.',
    'A blue Susanoo with ribs, head and arms swings giant blades 4 to 8 times, up to 16 with quantity cards. The final slash is stronger. Grants no invulnerability.',
    'Two separately telegraphed meteors strike a fixed point, followed by 4 to 8 shockwaves, up to 16 with quantity cards. Moving outside the marked radius avoids damage.',
    'Summon 2 to 4 visible wood doubles for 12 seconds, up to 6 with quantity cards. Each independently approaches reachable enemies and uses your learned Susanoo, fire or palm combo. Clone skill ranks increase their damage from 100% to 210%. Separate from the self-clone card.'
  ];
  const dictionary={};
  for(const [rowIndex,[id]]of rows.entries()){
    const def=G.Moves.BY_ID[id];dictionary[def.name]=englishNames[rowIndex];dictionary[def.desc]=englishDescriptions[rowIndex]+' Automatically cast; no active slot required.';
    for(let i=0;i<4;i++){
      const before=G.Moves.instance(id,i+1),after=G.Moves.instance(id,i+2),a={atk:1,quantityPicks:0},v=vector(a,before),next=vector(a,after);
      const changes=Object.keys(v).filter(k=>v[k]!==next[k]).map(k=>`${k} ${v[k]}→${next[k]}`);
      const text=(def.madaraKind==='clones'?`分身火力 ${Math.round(before.dmg/32*100)}%→${Math.round(after.dmg/32*100)}%`:`傷害 ${Math.round(before.dmg)}→${Math.round(after.dmg)}；射程 ${before.range}→${after.range}`)+(def.madaraKind==='meteor'?`；半徑 ${Math.round(before.radius)}→${Math.round(after.radius)}`:'')+(changes.length?'；'+changes.join('、'):'');
      def.ups[i].t=text;dictionary[text]=(def.madaraKind==='clones'?`Wood double power ${Math.round(before.dmg/32*100)}% → ${Math.round(after.dmg/32*100)}%`:`Damage ${Math.round(before.dmg)} → ${Math.round(after.dmg)}; range ${before.range} → ${after.range}`)+(def.madaraKind==='meteor'?`; radius ${Math.round(before.radius)} → ${Math.round(after.radius)}`:'')+(changes.length?`; ${Object.keys(v).filter(k=>v[k]!==next[k]).map(k=>`${def.madaraKind==='clones'?'wood doubles':def.madaraKind==='meteor'?'shockwaves':'hits'} ${v[k]} → ${next[k]}`).join(', ')}`:'');
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
  G.Game.startRun=function(...args){starting=true;try{return startRun.apply(this,args);}finally{starting=false;}};
  const pool=G.Moves.poolFor;
  G.Moves.poolFor=mon=>mon.dex===DEX?rows.filter(r=>r[4]<=(!starting&&G.Game.player?.mon===mon?G.Game.player.level:1)).map(r=>r[0]):pool(mon);
  const addMove=G.Player.prototype.addMove;
  G.Player.prototype.addMove=function(id,...args){
    if(ids.has(id)){if(this.mon?.dex!==DEX||this.level<G.Moves.BY_ID[id].learnLevel||this.hasMove(id))return false;this.moves.push(G.Moves.instance(id));this.arrange();return true;}
    if(this.mon?.dex===DEX)return false;return addMove.call(this,id,...args);
  };
  // Upgrade offers use this owner's real quantity investment, not the q=0 guide.
  const offer=G.LevelUp.offer;
  G.LevelUp.offer=function(owner,...args){
    return offer.call(this,owner,...args).map(card=>{
      if(card.type!=='up')return card;
      const id=card.key.slice(3),m=owner.moves?.find(move=>move.id===id);
      if(!ids.has(id)||!m||m.lvl>=m.def.maxLvl)return card;
      const next=G.Moves.instance(id,m.lvl+1),before=profile(owner,m),after=profile(owner,next),v=vector(owner,m),nv=vector(owner,next),en=G.I18n.lang==='en';
      const parts=before.kind==='clones'?[`${en?'Wood double power':'分身火力'} ${Math.round(before.cloneDamageMultiplier*100)}%→${Math.round(after.cloneDamageMultiplier*100)}%`]:
        [`${en?'Damage':'傷害'} ${Math.round(before.damage)}→${Math.round(after.damage)}`,`${en?'Range':'射程'} ${before.range}→${after.range}`];
      if(before.kind==='meteor')parts.push(`${en?'Radius':'半徑'} ${Math.round(before.radius)}→${Math.round(after.radius)}`);
      for(const key of Object.keys(v))if(v[key]!==nv[key])parts.push(`${en?(before.kind==='clones'?'Wood doubles':before.kind==='meteor'?'Shockwaves':before.kind==='fire'?'Fire waves':before.kind==='susanoo'?'Blade strikes':'Palm hits'):key} ${v[key]}→${nv[key]}`);
      return {...card,desc:parts.join(en?'; ':'；'),growthMove:m};
    });
  };
  function state(owner){let s=states.get(owner);if(s&&(s.world!==G.World||s.epoch!==G.CombatPulse.epoch)){clear(owner);s=null;}if(!s){s={owner,world:G.World,epoch:G.CombatPulse.epoch,clock:0,action:null,fields:[],clones:[],effects:[],casts:{},hits:0,damage:0,contacts:0,propHits:0,propDamage:0};states.set(owner,s);}return s;}
  function clear(owner){if(owner){const s=states.get(owner);if(s){if(s.action)s.action.cast.runEpoch=-1;for(const f of s.fields)f.cast.runEpoch=-1;for(const c of s.clones)if(c.action)c.action.cast.runEpoch=-1;}states.delete(owner);}else{for(const a of [...states.keys()])clear(a);}}
  function path(x,y,tx,ty,target=null){
    if(G.World.projectilePathClear)return G.World.projectilePathClear(x,y,tx,ty,target,{radius:1,spacing:4,includeStart:false});
    const n=Math.max(1,Math.ceil(Math.hypot(tx-x,ty-y)/4));for(let i=1;i<=n;i++){const px=x+(tx-x)*i/n,py=y+(ty-y)*i/n;if(G.World.isWall?.(px,py))return false;const b=G.World.projectileBlock?.(px,py,1);if(b&&b!==target)return false;}return true;
  }
  function enemies(x,y,r){const registered=new Set(G.EnemyMgr.all());return [...new Set(G.EnemyMgr.queryCircle(x,y,r+80))].filter(e=>registered.has(e)&&alive(e)&&!e.friendly&&Math.hypot(e.x-x,e.y-y)<=r+(e.r||0));}
  function props(x,y,r){return [...new Set(G.World.propsInCircle?.(x,y,r)||[])].filter(p=>!p.dead&&p.destructible!==false&&p.hp>0&&Math.hypot(p.x-x,p.y-y)<=r+(p.r||0)&&path(x,y,p.x,p.y,p));}
  function targetFor(owner,m,origin=owner){const nearest=list=>list.sort((a,b)=>Math.hypot(a.x-origin.x,a.y-origin.y)-Math.hypot(b.x-origin.x,b.y-origin.y))[0]||null;return nearest(enemies(origin.x,origin.y,m.range).filter(e=>path(origin.x,origin.y,e.x,e.y)))||nearest(props(origin.x,origin.y,m.range));}
  function damageProps(s,f,x,y,r,ratio=1,inside=()=>true){
    for(const p of props(x,y,r)){if(!legal(s,f))break;if(!inside(p))continue;const before=p.hp,amount=f.damage*ratio;G.World.damageProp?.(p,amount,f.kind==='fire'?'#ffb753':'#85c4ff');s.propHits++;s.propDamage+=Math.min(before,amount);}
  }
  function drawable(s,f){return states.get(s.owner)===s&&s.world===G.World&&s.epoch===G.CombatPulse.epoch&&valid(s.owner)&&s.owner.moves?.some(m=>m.id===f.m.id)&&f.cast.runEpoch===s.epoch;}
  function legal(s,f){return states.get(s.owner)===s&&s.world===G.World&&s.epoch===G.CombatPulse.epoch&&valid(s.owner)&&!!s.owner.moves?.some(m=>m.id===f.m.id)&&(!f.clone||s.clones.includes(f.clone)&&s.owner.moves.some(m=>m.id==='naruto-madara-clones'))&&G.CombatPulse.legal(f.cast);}
  function canCast(owner,m){if(!valid(owner)||owner.frozen||G.Game.state!=='playing'||!ids.has(m?.id)||(m.t||0)>EPS||!owner.moves?.some(x=>x.id===m.id))return false;const s=state(owner);return !s.action&&!(m.madaraKind==='clones'&&s.clones.length)&&!!targetFor(owner,m);}
  function action(s,m,origin=s.owner,clone=null){const p=profile(s.owner,m),target=targetFor(s.owner,m,origin);if(!target)return null;if(clone)p.damage*=clone.damageMultiplier;return {...p,m:{...m},owner:s.owner,clone,age:0,index:0,x:origin.x,y:origin.y,aim:Math.atan2(target.y-origin.y,target.x-origin.x),tx:target.x,ty:target.y,cast:G.CombatPulse.create(s.owner,m.id,{channel:clone?'wood-clone':p.kind==='meteor'?'field':'body',targetIsLegal:target=>G.EnemyMgr.all().includes(target)}),meteorHits:0};}
  function cast(owner,m){if(!canCast(owner,m))return false;const s=state(owner),f=action(s,m);if(!f)return false;s.action=f;s.casts[m.id]=(s.casts[m.id]||0)+1;m.t=Math.max(.05,m.cd*(owner.cdMul??1));m.castAt=performance.now();owner.aim=f.aim;owner.cast?.(m);return true;}
  function hurt(s,f,list,index,ratio=1){
    if(!legal(s,f))return;
    const hits=list.map(e=>{const mult=G.Types.mult(f.m.type,e.types),crit=Math.random()<(s.owner.critChance||0),damage=f.damage*ratio*mult*G.Weather.mult(f.m.type)*(crit?1.5:1)*(G.NarutoSupport?.precisionMultiplier(s.owner,e)||1);return {target:e,primaryDirectDamage:damage,color:f.kind==='fire'?'#ffb753':f.kind==='meteor'?'#c9ab94':'#85c4ff',dx:Math.cos(f.aim),dy:Math.sin(f.aim),knock:0,eff:crit?'crit':G.Types.label(mult),onHit(){if(!legal(s,f))f.cast.runEpoch=-1;}};});
    const result=G.CombatPulse.apply(f.cast,index,hits);if(result){s.hits+=result.primaryHits;s.damage+=result.primaryDamage;s.contacts++;}return result;
  }
  function pulse(s,f,index){
    if(!legal(s,f))return;
    const origin=f.clone||s.owner;f.x=origin.x;f.y=origin.y;const t=targetFor(s.owner,f.m,origin);if(t)f.aim=Math.atan2(t.y-origin.y,t.x-origin.x);
    const list=enemies(f.x,f.y,f.range).filter(e=>path(f.x,f.y,e.x,e.y)&&Math.abs(Math.atan2(Math.sin(Math.atan2(e.y-f.y,e.x-f.x)-f.aim),Math.cos(Math.atan2(e.y-f.y,e.x-f.x)-f.aim)))<=f.arc/2);
    hurt(s,f,list,index,index===f.pulses-1?1.65:1);
    damageProps(s,f,f.x,f.y,f.range,index===f.pulses-1?1.65:1,p=>Math.abs(Math.atan2(Math.sin(Math.atan2(p.y-f.y,p.x-f.x)-f.aim),Math.cos(Math.atan2(p.y-f.y,p.x-f.x)-f.aim)))<=f.arc/2);
    if(legal(s,f))s.effects.push({kind:f.kind,x:f.x,y:f.y,aim:f.aim,range:f.range,arc:f.arc,age:0,life:f.interval+.10,index,last:index===f.pulses-1,clone:!!f.clone});
  }
  function rock(s,f,which){
    const x=f.tx,y=f.ty,targets=enemies(x,y,f.radius).filter(e=>path(x,y,e.x,e.y));
    hurt(s,f,targets,which,which===0?1:1.6);damageProps(s,f,x,y,f.radius,which===0?1:1.6);f.meteorHits++;
    if(legal(s,f))s.effects.push({kind:'impact',x,y,radius:f.radius,age:0,life:.8,second:which===1});
  }
  function spawn(s,f){
    for(let i=0;i<f.cloneCount;i++){const aim=i*Math.PI*2/f.cloneCount,x=s.owner.x+Math.cos(aim)*65,y=s.owner.y+Math.sin(aim)*65;
      s.clones.push({x:path(s.owner.x,s.owner.y,x,y)?x:s.owner.x,y:path(s.owner.x,s.owner.y,x,y)?y:s.owner.y,age:0,life:f.cloneDuration,damageMultiplier:f.cloneDamageMultiplier,cooldown:i*.18,action:null,serial:i});}
  }
  function advanceAction(s,f,dt){
    if(!legal(s,f))return false;f.age+=dt;
    if(f.kind==='clones'){if(f.age>=f.charge&&!f.released){f.released=true;spawn(s,f);}return f.age<f.charge+.25;}
    if(f.kind==='meteor'){
      if(f.age>=f.charge&&!f.released){f.released=true;s.fields.push(f);return false;}return true;
    }
    while(f.index<f.pulses&&f.age+EPS>=f.charge+f.index*f.interval){if(!legal(s,f))return false;pulse(s,f,f.index++);}
    return legal(s,f)&&f.age<f.duration;
  }
  function update(dt){
    if(G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    for(const [owner,s]of states){
      if(!valid(owner)||s.world!==G.World||s.epoch!==G.CombatPulse.epoch){clear(owner);continue;}
      if(owner.frozen)continue;s.clock+=dt;
      for(const e of s.effects)e.age+=dt;s.effects=s.effects.filter(e=>e.age<e.life);
      if(s.action&&!advanceAction(s,s.action,dt))s.action=null;
      if(states.get(owner)!==s)continue;
      for(const f of [...s.fields]){
        if(!legal(s,f)){s.fields.splice(s.fields.indexOf(f),1);continue;}f.age+=dt;
        for(let which=f.meteorHits;which<2;which++){if(f.age+EPS<f.charge+.65+which*f.meteorDelay)break;if(!legal(s,f))break;rock(s,f,which);}
        while(f.index<f.pulses&&f.age+EPS>=f.charge+.65+f.meteorDelay+.2+f.index*f.interval){
          if(!legal(s,f))break;hurt(s,f,enemies(f.tx,f.ty,f.radius).filter(e=>path(f.tx,f.ty,e.x,e.y)),2+f.index,.35);damageProps(s,f,f.tx,f.ty,f.radius,.35);f.index++;
          if(legal(s,f))s.effects.push({kind:'shock',x:f.tx,y:f.ty,radius:f.radius,age:0,life:.35});
        }
        if(!legal(s,f)||f.index>=f.pulses)s.fields.splice(s.fields.indexOf(f),1);
      }
      if(!owner.moves.some(m=>m.id==='naruto-madara-clones'))s.clones.length=0;
      for(const c of [...s.clones]){
        c.age+=dt;if(c.age>=c.life){s.clones.splice(s.clones.indexOf(c),1);continue;}
        if(c.action&&!advanceAction(s,c.action,dt))c.action=null;
        if(states.get(owner)!==s)break;
        c.cooldown=Math.max(0,c.cooldown-dt);
        const learned=['naruto-madara-susanoo','naruto-madara-fire','naruto-madara'].map(id=>owner.moves.find(m=>m.id===id)).find(Boolean);
        if(!learned)continue;
        const target=targetFor(owner,{...learned,range:700},c),destination=target||owner;
        const distance=Math.hypot(destination.x-c.x,destination.y-c.y),wanted=target?(learned.madaraKind==='basic'?90:180):75;
        if(!c.action&&distance>wanted){const step=Math.min(Math.max(0,distance-wanted),320*dt),n=Math.min(32,Math.max(1,Math.ceil(step/4)));for(let i=0;i<n;i++){const dx=(destination.x-c.x)/distance*step/n,dy=(destination.y-c.y)/distance*step/n;if(path(c.x,c.y,c.x+dx,c.y+dy)){c.x+=dx;c.y+=dy;}else break;}}
        if(!c.action&&c.cooldown<=EPS&&target){c.action=action(s,learned,c,c);if(c.action)c.cooldown=Math.max(1.2,learned.cd*(owner.cdMul??1));}
      }
    }
  }
  function tick(dt,owner,now){
    if((owner?.mon?.dex??owner?.dex)!==DEX)return oldTick.call(this,dt,owner,now);
    if(!valid(owner)||owner.frozen||G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    const s=state(owner),moves=owner.moves.filter(m=>ids.has(m.id));for(const m of moves)m.t=Math.max(0,(m.t||0)-dt);
    if(s.action)return;
    // Heavy techniques take priority only when ready; basic attacks fill every gap.
    const ready=[...moves].reverse().find(m=>canCast(owner,m));if(ready)cast(owner,ready);
  }
  function poseFor(f){
    if(!f)return null;
    const end=f.charge+(f.pulses-1)*f.interval,tail=Math.max(0,f.age-end);
    let age=f.age;
    if(f.kind==='basic'||f.kind==='susanoo')age=f.age<f.charge?f.age/f.charge*.1:tail>.08&&f.index>=f.pulses?.48+tail:(.1+((f.age-f.charge)%f.interval)/f.interval*.37);
    if(f.kind==='fire')age=f.age<f.charge?f.age/f.charge*.25:f.index>=f.pulses&&tail>.08?.78+tail:.25+Math.min(.5,(f.age-f.charge)*.1);
    return {kind:f.kind,age,castAge:f.age,aim:f.aim,phase:f.age<f.charge?'charge':f.index>=f.pulses?'recover':'release',index:f.index,pulses:f.pulses};
  }
  function pose(owner){return poseFor(states.get(owner)?.action);}
  function drawSusanoo(ctx,x,y,height,aim,age){
    ctx.save();ctx.translate(x,y);ctx.globalAlpha*=.6;ctx.strokeStyle='#73bfff';ctx.fillStyle='#183b8c';ctx.lineWidth=3;
    ctx.beginPath();ctx.moveTo(-height*.32,-height*.35);ctx.lineTo(-height*.3,-height*.8);ctx.lineTo(0,-height);ctx.lineTo(height*.3,-height*.8);ctx.lineTo(height*.32,-height*.35);ctx.closePath();ctx.fill();ctx.stroke();
    for(let i=0;i<4;i++){ctx.beginPath();ctx.ellipse(0,-height*(.38+i*.1),height*.27,height*.1,0,0,Math.PI);ctx.stroke();}
    // Horned head is distinct from the rib-cage torso.
    ctx.beginPath();ctx.moveTo(-height*.17,-height*.79);ctx.lineTo(-height*.2,-height*.97);ctx.lineTo(-height*.1,-height*.93);ctx.lineTo(0,-height*1.03);ctx.lineTo(height*.1,-height*.93);ctx.lineTo(height*.2,-height*.97);ctx.lineTo(height*.17,-height*.79);ctx.closePath();ctx.fill();ctx.stroke();
    ctx.beginPath();ctx.moveTo(-height*.28,-height*.65);ctx.lineTo(-height*.50,-height*.48);ctx.lineTo(-height*.42,-height*.25);ctx.moveTo(height*.28,-height*.65);ctx.lineTo(height*.50,-height*.48);ctx.lineTo(height*.42,-height*.25);ctx.lineWidth=height*.065;ctx.stroke();
    // Split skeletal jaw, central sternum and angular shoulder armour.
    ctx.lineWidth=2;ctx.strokeStyle='#b5ddff';ctx.beginPath();
    ctx.moveTo(-height*.15,-height*.8);ctx.lineTo(-height*.12,-height*.73);ctx.lineTo(0,-height*.69);ctx.lineTo(height*.12,-height*.73);ctx.lineTo(height*.15,-height*.8);
    ctx.moveTo(-height*.08,-height*.78);ctx.lineTo(0,-height*.81);ctx.lineTo(height*.08,-height*.78);ctx.moveTo(0,-height*.68);ctx.lineTo(0,-height*.31);
    for(let i=0;i<4;i++){const y=-height*(.38+i*.1);ctx.moveTo(-height*.26,y);ctx.lineTo(-height*.12,y+height*.05);ctx.lineTo(0,y+height*.07);ctx.lineTo(height*.12,y+height*.05);ctx.lineTo(height*.26,y);}
    for(const side of [-1,1]){ctx.moveTo(side*height*.24,-height*.72);ctx.lineTo(side*height*.42,-height*.7);ctx.lineTo(side*height*.52,-height*.59);ctx.lineTo(side*height*.38,-height*.56);}ctx.stroke();
    ctx.fillStyle='#b2e1ff';ctx.fillRect(-height*.13,-height*.84,height*.07,3);ctx.fillRect(height*.06,-height*.84,height*.07,3);
    const side=Math.sin(age*9)<0?-1:1,dx=Math.cos(aim),dy=Math.sin(aim);ctx.lineWidth=height*.08;ctx.beginPath();ctx.moveTo(side*height*.28,-height*.65);ctx.lineTo(side*height*.45,-height*.45);ctx.lineTo(dx*height*.65,dy*height*.4-height*.5);ctx.stroke();ctx.strokeStyle='#ceeaff';ctx.lineWidth=height*.035;ctx.beginPath();ctx.moveTo(dx*height*.65,dy*height*.4-height*.5);ctx.lineTo(dx*height*1.3,dy*height*.8-height*.5);ctx.stroke();ctx.restore();
  }
  function draw(ctx,ground=false){
    if(!['playing','paused','levelup'].includes(G.Game.state))return;
    for(const s of states.values()){
      if(!valid(s.owner)||s.world!==G.World||s.epoch!==G.CombatPulse.epoch)continue;
      if(!ground){
        const f=s.action;if(f?.kind==='susanoo')drawSusanoo(ctx,s.owner.x,s.owner.y,190+rank(f.m)*10,f.aim,f.age);
        for(const c of s.clones){ctx.save();ctx.globalAlpha=.86;G.MadaraArt?.draw(ctx,c,{x:c.x,y:c.y,height:62,state:c.action?'cast':'walk',time:c.action?.age??c.age,dir:Math.cos(c.action?.aim||0)<0?6:2,pose:poseFor(c.action)});ctx.strokeStyle='#b2c58a';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(c.x-9,c.y+1);ctx.lineTo(c.x+9,c.y+1);ctx.stroke();ctx.restore();if(c.action?.kind==='susanoo')drawSusanoo(ctx,c.x,c.y,170,c.action.aim,c.action.age);}
      }
      for(const f of s.fields){
        if(!drawable(s,f))continue;
        for(let which=f.meteorHits;which<2;which++){const left=f.charge+.65+which*f.meteorDelay-f.age;if(left<0)continue;ctx.save();ctx.translate(f.tx,f.ty);if(ground){ctx.globalAlpha=.35;ctx.strokeStyle=which?'#d4b7f4':'#edbd83';ctx.lineWidth=which?3:2;ctx.beginPath();ctx.arc(0,0,f.radius,0,Math.PI*2);ctx.stroke();ctx.beginPath();ctx.moveTo(-8,0);ctx.lineTo(8,0);ctx.moveTo(0,-8);ctx.lineTo(0,8);ctx.stroke();}else if(left<.8){const r=f.radius*.46,h=left*430;ctx.globalAlpha=.9;ctx.fillStyle=which?'#766989':'#8e7768';ctx.strokeStyle='#c4aa90';ctx.lineWidth=4;ctx.beginPath();ctx.arc(-h*.25,-h-r,r,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.strokeStyle='#3c3548';for(let j=0;j<4;j++){ctx.beginPath();ctx.moveTo(-h*.25-r*.7+j*r*.4,-h-r*.65);ctx.lineTo(-h*.25-r*.3+j*r*.3,-h-r*1.3);ctx.stroke();}}ctx.restore();}
      }
      for(const e of s.effects){const p=e.age/e.life;ctx.save();ctx.translate(e.x,e.y);ctx.globalAlpha=(1-p)*(e.kind==='fire'?.30:.6);
        if(e.kind==='impact'||e.kind==='shock'){if(ground){ctx.strokeStyle=e.second?'#c1abec':'#d6ab7e';ctx.lineWidth=e.kind==='impact'?8:3;ctx.beginPath();ctx.arc(0,0,e.radius*(.5+.5*p),0,Math.PI*2);ctx.stroke();}else if(e.kind==='impact'){ctx.fillStyle='#a48873';for(let i=0;i<12;i++){const a=i*Math.PI/6,d=e.radius*p;ctx.fillRect(Math.cos(a)*d,Math.sin(a)*d-70*Math.sin(p*Math.PI),8,6);}}}
        else if(!ground){if(e.kind==='fire')ctx.translate(0,-43);ctx.rotate(e.aim);const range=e.range;if(e.kind==='fire'){ctx.translate(15,0);ctx.fillStyle='#bf391a';ctx.beginPath();ctx.moveTo(0,0);ctx.arc(0,0,range,-e.arc/2,e.arc/2);ctx.closePath();ctx.fill();ctx.globalAlpha*=.75;ctx.fillStyle='#ffb13c';for(let i=0;i<7;i++){const a=-e.arc*.45+i*e.arc*.15,r=range*(.7+.12*Math.sin(i*3+e.index));ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(Math.cos(a)*r,Math.sin(a)*r);ctx.lineTo(Math.cos(a+.1)*r*.8,Math.sin(a+.1)*r*.8);ctx.closePath();ctx.fill();}
          // Irregular rolling flame front, rather than a flat targeting-sector edge.
          ctx.globalAlpha=(1-p)*.48;ctx.strokeStyle='#ed6425';ctx.lineWidth=10;ctx.beginPath();
          for(let j=0;j<=28;j++){const a=-e.arc/2+j*e.arc/28,r=range*(.89+.045*Math.sin(j*2.7+e.index*1.3));const x=Math.cos(a)*r,y=Math.sin(a)*r;j?ctx.lineTo(x,y):ctx.moveTo(x,y);}ctx.stroke();
          for(let j=0;j<14;j++){const a=-e.arc*.47+j*e.arc*.94/13,r=range*(.80+.055*Math.sin(j*2.3+e.index)),tip=range*(.99+.025*Math.sin(j*3.1));ctx.save();ctx.rotate(a);ctx.fillStyle=j%3?'#f88126':'#ffbf45';ctx.beginPath();ctx.moveTo(r-24,-13);ctx.quadraticCurveTo(tip-25,-21,tip,-3);ctx.quadraticCurveTo(tip-18,0,tip-9,16);ctx.quadraticCurveTo(r+8,9,r-24,-13);ctx.fill();ctx.restore();}
        }else{ctx.strokeStyle=e.kind==='susanoo'?'#92ceff':'#f1d7b2';ctx.lineWidth=e.last?10:5;ctx.beginPath();ctx.arc(0,-12,range*.88,-e.arc/2+e.arc*p*.25,e.arc/2);ctx.stroke();}}
        ctx.restore();}
    }
  }
  const oldTick=C.tick,oldUpdate=C.updateFields,oldClear=C.clearFields,oldAir=C.drawAirFields,oldGround=C.drawGroundFields;
  C.tick=tick;C.updateFields=function(dt){const r=oldUpdate.call(this,dt);update(dt);return r;};C.clearFields=function(owner){const r=oldClear.call(this,owner);clear(owner);return r;};C.drawAirFields=function(ctx){oldAir.call(this,ctx);draw(ctx);};C.drawGroundFields=function(ctx){oldGround.call(this,ctx);draw(ctx,true);};
  function statusFor(owner,m){const s=states.get(owner),f=s?.action?.m.id===m.id?s.action:s?.fields.find(f=>f.m.id===m.id);return {state:f?'casting':m.t>EPS?'cooldown':s?.action?'queued':'ready',remaining:m.t||0,index:f?.index||0,pulses:f?.pulses||0};}
  const nativeSkillState=G.RunInsights?.skillState;
  if(nativeSkillState)G.RunInsights.skillState=function(owner,m){if(!ids.has(m?.id))return nativeSkillState(owner,m);const s=states.get(owner),status=statusFor(owner,m),f=s?.action?.m.id===m.id?s.action:s?.fields.find(f=>f.m.id===m.id);return {label:f?(f.age<f.charge?'結印中':f.kind==='meteor'?'落石 '+f.meteorHits+'/2':`連擊 ${f.index}/${f.pulses}`):m.madaraKind==='clones'&&s?.clones.length?`協戰 ${s.clones.length}人`:status.state==='cooldown'?m.t.toFixed(1)+'s':status.state==='queued'?'待出手':'就緒',fraction:f?Math.max(0,1-f.age/f.duration):Math.min(1,(m.t||0)/Math.max(.05,m.cd*(owner.cdMul??1)))};};
  G.NarutoMadara={dex:DEX,kit,supports,profile,vector,targetFor,canCast,cast,update,clear,pose,statusFor,draw,
    stateFor:(a=G.Game.player)=>states.get(a)||null,stats:(a=G.Game.player)=>{const s=states.get(a);return s?{casts:{...s.casts},hits:s.hits,damage:s.damage,contacts:s.contacts,propHits:s.propHits,propDamage:s.propDamage,clones:s.clones.length,fields:s.fields.length}:null;}};
})();
