// Naruto crossover registration. Original sheet provenance lives in naruto/sources.json.
(() => {
  const version='火影 beta 0.01';
  const roster = [
    ['naruto','Naruto Uzumaki','漩渦鳴人','第七班',['fighting','flying'],3,120,116],
    ['sasuke','Sasuke Uchiha','宇智波佐助','第七班',['electric','fire'],4,108,123],
    ['sakura','Sakura Haruno','春野櫻','第七班',['fighting'],2,146,108],
    ['kakashi','Kakashi Hatake','旗木卡卡西','第七班導師',['electric'],5,112,119],
    ['hinata','Hinata Hyuga','日向雛田','第八班',['fighting','psychic'],2,118,115],
    ['lee','Rock Lee','洛克李','第三班',['fighting'],1,130,132],
    ['gaara','Gaara','我愛羅','砂隱村',['ground'],4,136,104],
    ['itachi','Itachi Uchiha','宇智波鼬','曉',['psychic','fire'],5,110,117]
  ];
  const records = new Map(), dictionary = {Naruto:'火影忍者'};
  for (const [index,[slug,name,chinese,team,types,rarity,hp,spd]] of roster.entries()) {
    const dex = 30001 + index, start = slug==='naruto'?'naruto-shadow-clones':'naruto-' + slug;
    const mon = {dex,name,types,hp,spd,atk:1.32,rarity,bst:400+rarity*38,starter:true,gen:11,naruto:true,start};
    G.DEX.push(mon);G.DEX_BY[dex]=mon;
    const starter={dex,start,traits:['valiente','leal']};
    G.STARTERS.push(starter);G.STARTER_BY[dex]=starter;
    const pixel=window.PS_NARUTO_SPRITES[slug==='lee'?'rock-lee':slug],image=new Image();
    const geometry={w:32,h:36,ax:16,ay:36,n:1,r:1,d:[24]};
    G.SPRITE_META[dex]={s:1,sh:false,a:Object.fromEntries(G.Sprites.ANIMS.map(anim=>{
      const action=pixel.animations?.[anim];
      const count=anim==='Walk'?4:action?Math.max(...Object.values(action.frames).map(frames=>frames.length)):1;
      return [anim,{...geometry,n:count,d:action?.durations||Array(count).fill(anim==='Walk'?8:action?(action.duration||7):24)}];
    }))};
    const record={...mon,chinese,team,slug,pixel,image,ready:false,attack:''};
    record.loaded=new Promise(resolve=>{
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
      image.onerror=()=>resolve(false);
    });
    image.src='.omx/naruto/pixel/'+pixel.file;
    records.set(dex,record);dictionary[name]=chinese;
  }
  G.I18n.add(dictionary,'zh-TW');
  G.MenuUI.GEN_NAMES.push('Naruto');
  G.Gacha.BANNERS.push({gen:11,name:'Naruto',color:['#57321b','#94431e','#252f56']});
  const featured=G.Gacha.featured;
  G.Gacha.featured=gen=>gen===11?[30001,30002,30004]:featured(gen);

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
      if(!record.ready)return;
      const pixel=record.pixel;
      const pose=frameFor(record,this.cur,this.dir,this.frame);
      const [sx,sy,sw,sh]=pose.rect;
      const ui=previews.has(ctx.canvas);
      const target=ui?Math.min(ctx.canvas.height*.78,ctx.canvas.width*.75):64*this.scale;
      const stand=pixel.frames.down[0];
      const k=ui?Math.min(target/stand[3],ctx.canvas.width*.88/Math.max(sw,stand[2])):target/stand[3];
      ctx.save();ctx.translate(Math.round(x),Math.round(y));ctx.imageSmoothingEnabled=false;
      ctx.globalAlpha*=opts.alpha==null?1:opts.alpha;
      if(pose.mirror)ctx.scale(-1,1);
      if(this.cur==='Faint'&&!pose.action)ctx.scale(1,.45);
      ctx.drawImage(opts.flash?G.Sprites.white(record.image):record.image,sx,sy,sw,sh,
        -Math.round(sw*k/2),-Math.round(sh*k),Math.round(sw*k),Math.round(sh*k));
      ctx.restore();
    }
  };
  const preload=G.Sprites.preload;
  G.Sprites.preload=(dexes,timeout,shiny)=>Promise.all([
    preload(dexes.filter(d=>!records.has(d)),timeout,shiny),
    ...dexes.filter(d=>records.has(d)).map(d=>records.get(d).loaded)
  ]);
  const sprite=G.UI.sprite,spriteCanvas=G.UI.spriteCanvas;
  G.UI.sprite=(canvas,dex,opts)=>{if(records.has(dex))previews.add(canvas);return sprite(canvas,dex,opts);};
  G.UI.spriteCanvas=(dex,w,h,opts)=>{const canvas=spriteCanvas(dex,w,h,opts);if(records.has(dex))previews.add(canvas);return canvas;};

  const picker=document.createElement('section');picker.id='scr-naruto';picker.className='scr dim hidden';picker.translate=false;
  picker.innerHTML=`<div class="box"><div class="naruto-heading"><div><h2>火影忍者</h2><p class="naruto-version">${version}</p><p class="sub">選擇忍者，踏上你的忍道。</p></div><button id="naruto-close" class="btn small ghost">返回</button></div>
    <div class="naruto-actions"><button id="naruto-to-digimon" class="btn small">數碼寶貝</button></div>
    <div class="naruto-grid"></div><p class="note">8 位忍者・招式為生存玩法改編・存檔保存在此瀏覽器</p>
    <p class="note">像素素材：Path of the Ninja 2・Hwdphg 擷取・<a href="https://spritedatabase.net/game/59" target="_blank" rel="noopener noreferrer">Sprite Database</a>。角色與美術權利屬原權利人。</p></div>`;
  document.body.append(picker);
  const grid=picker.querySelector('.naruto-grid');
  const hideOverlays=()=>['scr-naruto','scr-naruto-skills','scr-digimon','scr-digimon-skills'].forEach(id=>document.getElementById(id)?.classList.add('hidden'));
  const choose=dex=>{
    if(!records.has(dex))throw Error('Unknown Naruto character');
    const save=G.DB.save;save.partner=save.starter=dex;save.partnerShiny=false;
    G.DB.grant(dex,'starter');G.DB.commit(true);hideOverlays();G.Flow.goMenu();
  };
  const openPicker=()=>{
    hideOverlays();G.UI.show('scr-menu');G.UI.chrome(!!G.DB.save.partner);
    if(!G.DB.save.partner)document.getElementById('scr-menu').classList.add('hidden');
    picker.classList.remove('hidden');document.getElementById('naruto-close').hidden=!G.DB.save.partner;
    for(const b of grid.querySelectorAll('[data-naruto]'))b.classList.toggle('on',+b.dataset.naruto===G.DB.save.partner);
  };
  for(const record of records.values()) {
    const button=document.createElement('button');button.className='naruto-card';button.dataset.naruto=record.dex;
    button.append(G.UI.spriteCanvas(record.dex,128,112,{dir:0,shadow:true}));
    button.insertAdjacentHTML('beforeend',`<b>${record.chinese}</b><small>${record.team}</small><span data-naruto-attack="${record.dex}"></span>`);
    button.onclick=()=>choose(record.dex);grid.append(button);
  }
  const digimonOpen=G.Digimon.openPicker;
  G.Digimon.openPicker=()=>{hideOverlays();digimonOpen();};
  document.getElementById('btn-digimon').onclick=G.Digimon.openPicker;
  document.getElementById('naruto-to-digimon').onclick=G.Digimon.openPicker;
  document.getElementById('naruto-close').onclick=()=>{hideOverlays();G.Flow.goMenu();};
  const nav=document.createElement('button');nav.id='btn-naruto';nav.className='btn small gold';nav.textContent='火影忍者';nav.translate=false;nav.onclick=openPicker;
  document.getElementById('btn-settings').before(nav);
  const shortcut=document.createElement('button');shortcut.id='digimon-to-naruto';shortcut.className='btn small';shortcut.textContent='火影忍者 →';shortcut.onclick=openPicker;
  document.querySelector('#scr-digimon .digimon-heading').after(shortcut);

  const ready=G.DB.ready;
  G.DB.ready=async()=>{const restored=await ready();for(const dex of records.keys())G.DB.grant(dex,'starter');G.DB.commit();return restored;};
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
    const description=document.getElementById('banner-desc'),copy='木葉與砂隱的忍者集結・8 位角色・招牌忍術';
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
  if(badge){badge.textContent=version+'・非官方跨界沙盒版・金幣與抽卡券無限・瀏覽器存檔';badge.style.maxWidth='calc(100vw - 16px)';}
  const style=document.createElement('style');style.textContent=`
    #scr-naruto{z-index:150;padding:20px;background:#08152bef}#scr-naruto>.box{width:min(960px,100%);max-height:92vh;overflow:auto;border-color:#e4a653}
    .naruto-heading{display:flex;justify-content:space-between;align-items:center;gap:12px}.naruto-heading h2{margin-bottom:4px;color:#ffd23f}.naruto-heading>button{flex-shrink:0;white-space:nowrap}
    .naruto-version{margin:0 0 4px;color:#ffcf7c;font-size:13px}
    .naruto-actions{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.naruto-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
    .naruto-card{display:flex;flex-direction:column;align-items:center;gap:6px;padding:12px 8px;color:white;background:#173564;border:2px solid #597fae;border-radius:12px;font:inherit;cursor:pointer}
    .naruto-card:hover,.naruto-card:focus-visible,.naruto-card.on{border-color:#ffc468;background:#244b80}.naruto-card b{font-size:19px;color:#ffd23f}.naruto-card small{color:#c9d8ef}
    .naruto-card canvas{display:block;width:128px;height:112px;max-width:100%;image-rendering:pixelated}.naruto-card span{font-size:14px}
    @media(max-width:650px){.naruto-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.topbar{gap:4px;max-width:calc(100vw - 12px);flex-wrap:wrap;justify-content:flex-end}.topbar .btn.small{padding:4px 6px;font-size:12px}#scr-naruto{padding:10px}}
  `;document.head.append(style);
  G.Naruto={version,records,choose,openPicker,frameFor};
})();
