// Naruto crossover registration. Original sheet provenance lives in naruto/sources.json.
(() => {
  // Public beta roster. Keep all definitions so hidden characters can return later.
  const availableDexes=Object.freeze([30001,30002,30006,30007,30009,30010,30011]);
  const available=dex=>!records.has(+dex)||availableDexes.includes(+dex);
  const version='火影 beta 0.01';
  const roster = [
    ['naruto','Naruto Uzumaki','漩渦鳴人','第七班',['fighting','flying'],3,120,116],
    ['sasuke','Sasuke Uchiha','宇智波佐助','第七班',['electric','fire'],4,108,123],
    ['sakura','Sakura Haruno','春野櫻','第七班',['fighting'],2,146,108],
    ['kakashi','Kakashi Hatake','旗木卡卡西','第七班導師',['electric'],5,112,119],
    ['hinata','Hinata Hyuga','日向雛田','第八班',['fighting','psychic'],2,118,115],
    ['lee','Rock Lee','洛克李','第三班',['fighting'],1,180,132],
    ['gaara','Gaara','我愛羅','砂隱村',['ground'],4,136,104],
    ['itachi','Itachi Uchiha','宇智波鼬','曉',['psychic','fire'],5,110,117],
    ['tenten','Tenten','天天','第三班',['steel'],3,150,144],
    ['pain','Pain — Six Paths','沛恩六道','曉',['psychic'],5,120,108],
    ['temari','Temari','手鞠','砂隱村',['flying'],3,125,118]
  ];
  const records = new Map(), dictionary = {Naruto:'火影忍者'};
  for (const [index,[slug,name,chinese,team,types,rarity,hp,spd]] of roster.entries()) {
    const dex = 30001 + index, start = slug==='naruto'?'naruto-shadow-clones':'naruto-' + slug;
    const mon = {dex,name,types,hp,spd,atk:1.32,rarity,bst:400+rarity*38,starter:true,gen:11,naruto:true,start};
    G.DEX.push(mon);G.DEX_BY[dex]=mon;
    const starter={dex,start,traits:['valiente','leal']};
    G.STARTERS.push(starter);G.STARTER_BY[dex]=starter;
    // Temari has her own on-demand atlas; no legacy pixel sheet is required.
    const basePixel=slug==='temari'?{frames:{down:[[0,0,32,36]]},animations:{},mirror:[]}:window.PS_NARUTO_SPRITES[slug==='lee'?'rock-lee':slug];
    const pixel=['pain','temari'].includes(slug)?{...basePixel,preview:{source:'.omx/naruto/portraits/'+slug+'.png',w:96,h:112,ax:48,ay:110}}:basePixel,image=new Image();
    const geometry={w:32,h:36,ax:16,ay:36,n:1,r:1,d:[24]};
    G.SPRITE_META[dex]={s:1,sh:false,a:Object.fromEntries(G.Sprites.ANIMS.map(anim=>{
      const action=pixel.animations?.[anim];
      const count=slug==='temari'?4:anim==='Walk'?4:action?Math.max(...Object.values(action.frames).map(frames=>frames.length)):1;
      const duration=slug==='temari'?(anim==='Idle'?12:anim==='Faint'?9:6):anim==='Walk'?8:action?(action.duration||7):24;
      return [anim,{...geometry,n:count,d:action?.durations||Array(count).fill(duration)}];
    }))};
    const record={...mon,chinese,team,slug,pixel,image,ready:false,attack:''};
    let loading;
    Object.defineProperty(record,'loaded',{get(){
      if(record.ready)return Promise.resolve(true);
      if(slug==='pain'||slug==='temari')return (slug==='pain'?G.PainArt:G.TemariArt).ready.then(()=>{record.ready=true;return true;});
      if(loading)return loading;
      loading=new Promise(resolve=>{
      image.onload=()=>{
        if(pixel.background){
          const canvas=document.createElement('canvas');canvas.width=image.width;canvas.height=image.height;
          const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(image,0,0);
          const rgba=ctx.getImageData(0,0,canvas.width,canvas.height),key=pixel.background;
          for(let p=0;p<rgba.data.length;p+=4)if(key.every((v,i)=>rgba.data[p+i]===v))rgba.data[p+3]=0;
          ctx.putImageData(rgba,0,0);record.image=canvas;
        }
        record.ready=true;resolve(true);
      };
      image.onerror=()=>{loading=null;resolve(false);};
      image.src=pixel.source||'.omx/naruto/pixel/'+pixel.file;
      });return loading;
    }});
    records.set(dex,record);dictionary[name]=chinese;
  }
  G.I18n.add(dictionary,'zh-TW');
  G.MenuUI.GEN_NAMES.push('Naruto');
  G.Gacha.BANNERS.push({gen:11,name:'Naruto',color:['#57321b','#94431e','#252f56']});
  const featured=G.Gacha.featured;
  G.Gacha.featured=gen=>gen===11?[...availableDexes]:gen===10&&!G.Digimon.enabled?[]:featured(gen);

  const selectable=dex=>available(dex)&&(G.Digimon.enabled||!G.Digimon.records.has(+dex));
  // Filter discovery lists, retaining DEX_BY and records for save data and battle assets.
  G.DEX.splice(0,G.DEX.length,...G.DEX.filter(mon=>selectable(mon.dex)));
  G.STARTERS.splice(0,G.STARTERS.length,...G.STARTERS.filter(mon=>selectable(mon.dex)));
  if(!G.Digimon.enabled){delete G.MenuUI.GEN_NAMES[9];delete G.Gacha.BANNERS[9];}
  const pull=G.Gacha.pull;
  G.Gacha.pull=(save,n,gen=1,use='t1')=>gen===10&&!G.Digimon.enabled?null:pull(save,n,gen,use);
  const upgradePicker=document.getElementById('upg-mon');
  new MutationObserver(()=>{
    for(const option of [...upgradePicker.options])if(!selectable(option.value))option.remove();
  }).observe(upgradePicker,{childList:true});
  const restoreAvailablePartner=()=>{
    const save=G.DB.save;
    if(save.partner&&!selectable(save.partner)){
      save.partner=save.starter=30001;save.partnerShiny=false;
    }else if(save.starter&&!selectable(save.starter))save.starter=save.partner||30001;
  };

  const previews=new WeakSet(),Animator=G.Sprites.Animator;
  const frameFor=(record,anim,dir,index=0)=>{
    const pixel=record.pixel;
    const direction=['down','right','right','right','up','left','left','left'][dir];
    const action=pixel.animations?.[anim];
    const frames=action?.frames||pixel.frames;
    const group=frames[direction]||frames.default||frames.down;
    const phase=anim==='Walk'&&!action?[0,1,0,2][index%4]:index;
    return {rect:group[phase%group.length],direction,mirror:(action?.mirror||pixel.mirror||[]).includes(direction),action:!!action};
  };
  G.Sprites.Animator=class extends Animator {
    draw(ctx,x,y,opts={}) {
      const record=records.get(this.dex);
      if(!record)return super.draw(ctx,x,y,opts);
      const pixel=record.pixel;
      const ui=previews.has(ctx.canvas);
      if(ui&&pixel.preview){
        if(!record.previewImage){
          if(Date.now()<(record.previewRetryAt||0))return;
          record.previewImage=new Image();
          record.previewImage.onerror=()=>{record.previewImage=null;record.previewRetryAt=Date.now()+1000;};
          record.previewImage.src=pixel.preview.source;
        }
        const image=record.previewImage,frame=pixel.preview;
        if(!image.complete||!image.naturalWidth)return;
        const target=Math.min(ctx.canvas.height*.78,ctx.canvas.width*.75),k=Math.min(target/frame.h,ctx.canvas.width*.88/frame.w);
        ctx.save();ctx.translate(Math.round(x),Math.round(y));ctx.imageSmoothingEnabled=false;ctx.globalAlpha*=opts.alpha??1;
        ctx.drawImage(image,-Math.round(frame.ax*k),-Math.round(frame.ay*k),Math.round(frame.w*k),Math.round(frame.h*k));ctx.restore();return;
      }
      if(this.dex===30011){
        if(!record.ready){void record.loaded;return;}
        const actor=G.Game.player?.anim===this?G.Game.player:[...(G.SelfClones?.actors()||[]),...(G.Coop?.puppets?.()||[]),...(G.TemariCoop?.remoteActors?.()||[])].find(a=>a.anim===this);
        const actionPose=actor?G.NarutoTemari?.activeFor(actor):null;
        const reflectWall=actor?G.NarutoTemariReflect?.activeFor(actor):null;
        const pose=actionPose||(reflectWall&&!reflectWall.permanent?{kind:'reflect',age:reflectWall.age}:null);
        const dead=actor?.dead||this.cur==='Faint',hurt=actor?.flash>0||this.cur==='Hurt';
        const state=dead?'death':hurt?'hurt':pose?.kind||(this.cur==='Walk'?'move':'idle');
        const time=dead?(this.cur==='Faint'?(this.frame*9+this.t)/60:0):
          actor?.flash>0?Math.max(0,.14-actor.flash):
          this.cur==='Hurt'?(this.frame*6+this.t)/60:
          pose?.age??(this.frame*(state==='idle'?12:6)+this.t)/60;
        if(ui)G.TemariArt.draw(ctx,{x,y,height:Math.min(ctx.canvas.height*.78,ctx.canvas.width*.75),state:'idle',time,dir:this.dir,facing:this.dir>=5?-1:1,alpha:opts.alpha??1});
        else {
          const stars=actor?.moves?.some(move=>move.digiMode==='temari-mastery')?(pose?.empowered?3:pose?.stars||1):1;
          G.TemariArt.draw(ctx,actor||{},{x,y,height:72*this.scale,state,time,stars,dir:this.dir,facing:this.dir>=5?-1:1,flash:!dead&&opts.flash,alpha:opts.alpha??1});
        }
        return;
      }
      if(this.dex===30010){
        const actor=G.Game.player?.anim===this?G.Game.player:(G.SelfClones?.actors()||[]).find(a=>a.anim===this);
        const pose=actor?G.NarutoPain?.activeFor(actor):null;
        const dead=actor?.dead||this.cur==='Faint';
        const hurt=this.cur==='Hurt';
        const gravityPose=!ui&&!dead&&!hurt&&actor?G.NarutoPain?.gravityPoseFor?.(actor):null;
        const casting=!dead&&!hurt&&pose&&['gravity','planet'].includes(pose.kind);
        const state=dead?'death':hurt?'hurt':gravityPose?.state||(casting?'special':this.cur==='Walk'?'move':['Attack','Shoot','Charge'].includes(this.cur)?'strike':'idle');
        const fps=G.PainArt?.metadata?.bodies.tendo.animations[state]?.fps||2;
        const time=gravityPose?.time??(casting?pose.age:this.frame/fps);
        if(ui)G.PainArt?.draw(ctx,{path:'tendo',x,y,height:Math.min(ctx.canvas.height*.78,ctx.canvas.width*.75),state:'idle',time,facing:this.dir>=5?-1:1,alpha:opts.alpha??1});
        else {
          const height=G.NarutoPain?.visualHeight('tendo',actor||{anim:this})??80*this.scale;
          G.PainArt?.draw(ctx,{path:'tendo',x:x+(gravityPose?.offsetX||0),y:y+(gravityPose?.offsetY||0),height,state,time,facing:this.dir>=5?-1:1,alpha:opts.alpha??1});
        }
        return;
      }
      if(!record.ready){void record.loaded;return;}
      const pose=G.NarutoChidori?.poseFor(this)||frameFor(record,this.cur,this.dir,this.frame);
      const [sx,sy,sw,sh]=pose.rect;
      const target=ui?Math.min(ctx.canvas.height*.78,ctx.canvas.width*.75):64*this.scale;
      const stand=pixel.frames.down[0];
      const k=ui?Math.min(target/stand[3],ctx.canvas.width*.88/Math.max(sw,stand[2])):target/stand[3];
      ctx.save();ctx.translate(Math.round(x),Math.round(y));ctx.imageSmoothingEnabled=false;
      ctx.globalAlpha*=opts.alpha==null?1:opts.alpha;
      if(pose.mirror)ctx.scale(-1,1);
      if(this.cur==='Faint'&&!pose.action)ctx.scale(1,.45);
      ctx.drawImage(opts.flash?G.Sprites.white(record.image):record.image,sx,sy,sw,sh,
        -Math.round((pose.anchor?.[0]??sw/2)*k),-Math.round((pose.anchor?.[1]??sh)*k),Math.round(sw*k),Math.round(sh*k));
      ctx.restore();
    }
  };
  const preload=G.Sprites.preload;
  G.Sprites.preload=(dexes,timeout,shiny)=>Promise.all([
    preload(dexes.filter(d=>!records.has(d)),timeout,shiny),
    ...dexes.filter(d=>records.has(d)).map(d=>Promise.all([records.get(d).loaded,G.NarutoAssets?.ensure(d)?.catch(()=>false)]))
  ]);
  const sprite=G.UI.sprite,spriteCanvas=G.UI.spriteCanvas;
  G.UI.sprite=(canvas,dex,opts)=>{if(records.has(dex))previews.add(canvas);return sprite(canvas,dex,opts);};
  G.UI.spriteCanvas=(dex,w,h,opts)=>{const canvas=spriteCanvas(dex,w,h,opts);if(records.has(dex))previews.add(canvas);return canvas;};

  const picker=document.createElement('section');picker.id='scr-naruto';picker.className='scr dim hidden';picker.translate=false;
  picker.innerHTML=`<div class="box"><div class="naruto-heading"><div><h2>火影忍者</h2><p class="naruto-version">${version}</p><p class="sub">選擇忍者，踏上你的忍道。</p></div><button id="naruto-close" class="btn small ghost">返回</button></div>
    <div class="naruto-actions"><button id="naruto-to-digimon" class="btn small">數碼寶貝</button></div>
    <div class="naruto-grid"></div><p class="note">${availableDexes.length} 位忍者・招式為生存玩法改編・存檔保存在此瀏覽器</p>
    <p class="note">角色動畫使用本專案重繪素材；動作研究參考 <a href="https://spritedatabase.net/game/55" target="_blank" rel="noopener noreferrer">Ninja Council 3</a>。角色權利屬原權利人。</p></div>`;
  document.body.append(picker);
  const grid=picker.querySelector('.naruto-grid');
  const hideOverlays=()=>['scr-naruto','scr-naruto-skills','scr-digimon','scr-digimon-skills'].forEach(id=>document.getElementById(id)?.classList.add('hidden'));
  const choose=dex=>{
    if(!records.has(dex))throw Error('Unknown Naruto character');
    if(!available(dex))return false;
    const save=G.DB.save;save.partner=save.starter=dex;save.partnerShiny=false;
    G.DB.grant(dex,'starter');G.DB.commit(true);hideOverlays();G.Flow.goMenu();
    void G.NarutoAssets?.download?.(dex);
  };
  const openPicker=()=>{
    hideOverlays();G.UI.show('scr-menu');G.UI.chrome(!!G.DB.save.partner);
    if(!G.DB.save.partner)document.getElementById('scr-menu').classList.add('hidden');
    picker.classList.remove('hidden');document.getElementById('naruto-close').hidden=!G.DB.save.partner;
    for(const b of grid.querySelectorAll('[data-naruto]'))b.classList.toggle('on',+b.dataset.naruto===G.DB.save.partner);
  };
  for(const record of records.values()) {
    if(!available(record.dex))continue;
    const button=document.createElement('button');button.className='naruto-card';button.dataset.naruto=record.dex;
    button.append(G.UI.spriteCanvas(record.dex,128,112,{dir:0,shadow:true}));
    button.insertAdjacentHTML('beforeend',`<b>${record.chinese}</b><small>${record.team}</small><span data-naruto-attack="${record.dex}"></span>`);
    button.onclick=()=>choose(record.dex);grid.append(button);
  }
  // Keep available beta characters visible beside the play button.
  const quickPick=document.createElement('section');quickPick.id='naruto-quick-pick';quickPick.translate=false;
  quickPick.setAttribute('aria-label','選擇出戰角色');
  quickPick.innerHTML='<div class="launch-roster-heading"><div><span class="launch-eyebrow">忍者集結</span><h2>選擇出戰角色</h2></div><span class="launch-roster-count"></span></div><p>選一位夥伴，展開這次冒險。</p><div class="naruto-grid"></div>';
  quickPick.querySelector('.launch-roster-count').textContent=`${availableDexes.length} 位忍者`;
  for(const dex of availableDexes){
    const record=records.get(dex),button=document.createElement('button');
    button.type='button';button.className='naruto-card';button.dataset.quickNaruto=dex;
    button.append(G.UI.spriteCanvas(dex,128,112,{dir:0,shadow:true}));
    const identity={30001:'影分身・螺旋丸',30002:'千鳥・豪火球',30007:'砂術・砂縛柩・砂瀑大葬',30006:'體術・木葉旋風・蓮華',30009:'忍具連投・雙昇龍',30010:'六道協戰・神羅天征・地爆天星',30011:'風遁・大鐮鼬・斬斬舞'}[dex]||record.team;
    button.insertAdjacentHTML('beforeend',`<b>${record.chinese}</b><small>${identity}</small><span class="naruto-selection"></span>`);
    button.onclick=()=>choose(dex);quickPick.querySelector('.naruto-grid').append(button);
  }
  const menu=document.getElementById('scr-menu'),partnerCard=menu.querySelector('.partner-card');
  menu.classList.add('launch-menu');
  const shell=document.createElement('div');shell.className='launch-shell';
  const heading=menu.querySelector('.logo');heading.classList.add('launch-brand');
  const content=document.createElement('div');content.className='launch-content';
  const detail=document.createElement('section');detail.className='launch-detail';
  detail.setAttribute('aria-label','目前出戰角色');
  detail.innerHTML='<div class="launch-selected"><span class="launch-eyebrow">本次出戰</span><span class="launch-selected-badge">已選擇</span></div><div class="launch-portrait"></div><h2 class="launch-name"></h2><p class="launch-role"></p><p class="launch-description"></p>';
  const play=menu.querySelector('[data-go="play"]');
  const action=document.createElement('div');action.className='launch-action';action.append(play);
  detail.append(partnerCard,action);content.append(quickPick,detail);
  const secondary=menu.querySelector('.menu-right');secondary.className='menu-right launch-secondary';
  shell.append(heading,content,secondary);menu.replaceChildren(shell);
  const roles={
    30001:['分身協戰','召喚影分身並肩作戰，以螺旋丸突破包圍。'],
    30002:['雷遁突進','千鳥穿梭連擊，搭配火遁壓制成群敵人。'],
    30006:['近身體術','旋風掃開敵群，以繃帶拉近敵人、蓮華重摔。'],
    30007:['砂術防守','砂盾護身、砂兵協戰，掌控周圍戰場。'],
    30009:['忍具遠攻','連投忍具、鋪設陷阱，以卷軸展開大範圍攻勢。'],
    30010:['六道協同','天道引斥控場，五道分工護衛，以通靈、飛彈與地爆天星壓制敵群。']
  };
  let previewDex;
  const syncQuickPick=()=>{
    const selected=G.DB.save.partner;
    partnerCard.classList.toggle('hidden',availableDexes.includes(+selected));
    const record=records.get(+selected),isNaruto=availableDexes.includes(+selected);
    detail.dataset.selectedHero=selected;
    action.dataset.heroName=isNaruto?record.chinese:G.I18n.t(G.DEX_BY[selected]?.name||'');
    detail.classList.toggle('launch-fallback',!isNaruto);
    if(previewDex!==selected){
      const portrait=detail.querySelector('.launch-portrait');portrait.replaceChildren();
      if(isNaruto)portrait.append(G.UI.spriteCanvas(+selected,220,174,{dir:0,shadow:true,scale:4,hero:true}));
      previewDex=selected;
    }
    detail.querySelector('.launch-name').textContent=isNaruto?record.chinese:'';
    detail.querySelector('.launch-role').textContent=isNaruto?roles[selected]?.[0]||record.team:'';
    detail.querySelector('.launch-description').textContent=isNaruto?roles[selected]?.[1]||'選好角色，準備出發。':'';
    for(const button of quickPick.querySelectorAll('[data-quick-naruto]')){
      const on=+button.dataset.quickNaruto===selected;
      button.classList.toggle('on',on);button.setAttribute('aria-pressed',String(on));
      const dex=+button.dataset.quickNaruto,loaded=!!G.NarutoAssets?.ready(dex),pending=!!G.NarutoAssets?.loading(dex);
      button.dataset.assetState=loaded?'ready':pending?'loading':'idle';
      button.querySelector('.naruto-selection').textContent=on?(loaded?'✓ 已下載':pending?'下載中…':'下載素材'):'點選使用';
    }
  };
  const menuOpen=G.MenuUI.open;
  G.MenuUI.open=function(...args){const result=menuOpen.apply(this,args);syncQuickPick();return result;};
  const digimonOpen=G.Digimon.openPicker;
  G.Digimon.openPicker=()=>{hideOverlays();digimonOpen();};
  document.getElementById('btn-digimon').onclick=G.Digimon.openPicker;
  document.getElementById('naruto-to-digimon').onclick=G.Digimon.openPicker;
  document.getElementById('naruto-to-digimon').hidden=!G.Digimon.enabled;
  picker.querySelector('.naruto-grid + .note').textContent=`${availableDexes.length} 位忍者：鳴人、佐助、小李、我愛羅、天天、沛恩六道、手鞠。`;
  document.getElementById('naruto-close').onclick=()=>{hideOverlays();G.Flow.goMenu();};
  const nav=document.createElement('button');nav.id='btn-naruto';nav.className='btn small gold';nav.textContent='火影忍者';nav.translate=false;nav.onclick=openPicker;
  document.getElementById('btn-settings').before(nav);
  const shortcut=document.createElement('button');shortcut.id='digimon-to-naruto';shortcut.className='btn small';shortcut.textContent='火影忍者 →';shortcut.onclick=openPicker;
  document.querySelector('#scr-digimon .digimon-heading').after(shortcut);

  const ready=G.DB.ready;
  const requestedHero=new URLSearchParams(location.search).get('hero')?.trim().toLowerCase();
  const linkedHero=availableDexes.find(dex=>{
    const record=records.get(dex);
    return [record.slug,record.chinese,String(dex)].includes(requestedHero);
  });
  let linkApplied=false;
  G.DB.ready=async()=>{
    const restored=await ready(),save=G.DB.save;
    restoreAvailablePartner();
    for(const dex of records.keys())G.DB.grant(dex,'starter');
    if(!linkApplied){
      linkApplied=true;
      if(linkedHero){save.partner=save.starter=linkedHero;save.partnerShiny=false;}
    }
    if(!save.partner&&!(save.stats?.runs>0)){
      save.partner=save.starter=30001;save.partnerShiny=false;
    }
    G.DB.commit();return restored;
  };
  const starterGrid=document.getElementById('starter-grid');
  new MutationObserver(()=>{
    const cells=starterGrid.querySelectorAll('.cell');
    if(cells.length!==G.STARTERS.length||starterGrid.querySelector('.naruto-group-label'))return;
    const heading=document.createElement('h3');heading.className='naruto-group-label digimon-group-label';heading.textContent='火影忍者';
    starterGrid.insertBefore(heading,cells[G.STARTERS.findIndex(s=>s.dex===30001)]);
  }).observe(starterGrid,{childList:true});
  new MutationObserver(()=>{
    const tab=document.querySelector('#gacha-gens [data-gen="11"]');if(!tab)return;
    const small=tab.querySelector('small');if(small&&small.textContent!=='忍者')small.textContent='忍者';
    if(!tab.classList.contains('on'))return;
    const description=document.getElementById('banner-desc'),copy=`木葉與砂隱的忍者集結・${availableDexes.length} 位角色・招牌忍術`;
    if(description.textContent!==copy)description.textContent=copy;
    const rates=document.getElementById('gacha-rates');
    const shinyRow=rates.querySelectorAll(':scope > div')[5];if(shinyRow)shinyRow.remove();
    const note=rates.querySelector('.note'),noteText='十連抽至少獲得一位史詩忍者。\n同一轉蛋池連續 70 抽未獲得傳說，下次必定獲得。\n重複角色會轉換成金幣，本分類沒有異色版本。';
    if(note&&note.textContent!==noteText){note.translate=false;note.textContent=noteText;note.style.whiteSpace='pre-line';}
  }).observe(document.getElementById('scr-gacha'),{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['class']});
  document.querySelector('#scr-menu .logo .t2').textContent='寶可夢 × 數碼寶貝 × 火影忍者';
  document.querySelector('#scr-menu [data-go="gacha"] small').textContent='9 大世代＋數碼寶貝＋火影忍者';
  document.title=version+' · PokéSurvivor';
  const badge=document.querySelector('body>div[style*="pointer-events: none"]');
  if(badge)badge.remove();
  const style=document.createElement('style');style.textContent=`
    #scr-naruto{z-index:150;padding:20px;background:#08152bef}#scr-naruto>.box{width:min(680px,100%);max-height:92vh;overflow:auto;border-color:#e4a653}
    .naruto-heading{display:flex;justify-content:space-between;align-items:center;gap:12px}.naruto-heading h2{margin-bottom:4px;color:#ffd23f}.naruto-heading>button{flex-shrink:0;white-space:nowrap}
    .naruto-version{margin:0 0 4px;color:#ffcf7c;font-size:13px}
    .naruto-actions{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.naruto-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
    .naruto-card{display:flex;flex-direction:column;align-items:center;gap:6px;padding:12px 8px;color:white;background:#173564;border:2px solid #597fae;border-radius:12px;font:inherit;cursor:pointer}
    .naruto-card:hover,.naruto-card:focus-visible,.naruto-card.on{border-color:#ffc468;background:#244b80}.naruto-card b{font-size:19px;color:#ffd23f}.naruto-card small{color:#c9d8ef}
    .naruto-card canvas{display:block;width:128px;height:112px;max-width:100%;image-rendering:pixelated}.naruto-card span{font-size:14px}
    #naruto-quick-pick{width:min(420px,100%);margin:12px auto;text-align:center}#naruto-quick-pick h2{margin:0;color:#ffd23f;font-size:22px}#naruto-quick-pick>p{margin:6px 0 12px;color:#c9d8ef;font-size:14px}
    #naruto-quick-pick .naruto-card.on{box-shadow:0 0 0 2px #ffc468}#naruto-quick-pick .naruto-selection{color:#ffcf7c}
    @media(max-width:650px){#naruto-quick-pick{margin:6px auto}#naruto-quick-pick .naruto-card{gap:3px;padding:8px 6px}#naruto-quick-pick .naruto-card canvas{width:96px;height:84px}#naruto-quick-pick h2{font-size:19px}#naruto-quick-pick>p{margin:4px 0 8px}body:has(#scr-menu.hidden)>.naruto-credit{bottom:calc(env(safe-area-inset-bottom,0px) + 130px)!important;font-size:10px!important}}
    @media(max-width:650px){.naruto-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.topbar{gap:4px;max-width:calc(100vw - 12px);flex-wrap:wrap;justify-content:flex-end}.topbar .btn.small{padding:4px 6px;font-size:12px}#scr-naruto{padding:10px}}
  `;document.head.append(style);
  if(!G.Digimon.enabled){
    document.querySelector('#scr-menu .logo .t2').textContent='寶可夢 × 火影忍者';
    document.querySelector('#scr-menu [data-go="gacha"] small').textContent='9 大世代與 5 位火影忍者';
  }
  const startRun=G.Game.startRun;
  G.Game.startRun=function(...args){restoreAvailablePartner();return startRun.apply(this,args);};
  G.Naruto={version,records,availableDexes,choose,openPicker,frameFor,refreshSelection:syncQuickPick,isPreview:canvas=>previews.has(canvas)};
})();
