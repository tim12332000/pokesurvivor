/* Preview-only instance renderer. Never writes gameplay objects or source sheets. */
(() => {
  'use strict';
  const iframe=document.querySelector('#game'), checkbox=document.querySelector('#candidate'), status=document.querySelector('#status');
  let config={sprites:{}}, attached=null, ready=false;
  const assets=new Map(), counters={source:0,candidate:0};
  function direction(angle){
    // Canvas/world: +y is down. Diagonals use the closest cardinal row.
    const n=((Math.round(angle/(Math.PI/2))%4)+4)%4;
    return ['right','down','left','up'][n];
  }
  async function loadAsset(spec){
    const url=new URL(spec.image,location.href);
    if(url.origin!==location.origin||!url.pathname.startsWith(new URL('./',location.href).pathname))throw Error('候選圖必須在審稿資料夾');
    const image=new Image();image.src=url.href;await image.decode();
    const cols=spec.columns, rows=spec.rows;
    if(!Number.isInteger(cols)||!Number.isInteger(rows)||cols<1||rows<1)throw Error('素材格數無效');
    const w=image.naturalWidth/cols,h=image.naturalHeight/rows,canvas=document.createElement('canvas');
    canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;
    const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(image,0,0);
    const pixels=ctx.getImageData(0,0,canvas.width,canvas.height).data,cells=[];
    for(let row=0;row<rows;row++)for(let col=0;col<cols;col++){
      let x0=w,y0=h,x1=-1,y1=-1;
      for(let y=0;y<Math.floor(h);y++)for(let x=0;x<Math.floor(w);x++){
        const px=Math.floor(col*w+x),py=Math.floor(row*h+y);
        if(pixels[(py*canvas.width+px)*4+3]>180){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}
      }
      cells.push(x1>=x0?{x:col*w+x0,y:row*h+y0,w:x1-x0+1,h:y1-y0+1}:null);
    }
    return {image,cells,spec};
  }
  async function reloadConfig(){
    try{
      const response=await fetch('playtest-config.json',{cache:'no-store'});
      config=response.ok?await response.json():{sprites:{}};
      assets.clear();
      await Promise.all(Object.entries(config.sprites||{}).map(async([dex,spec])=>{
        try{assets.set(Number(dex),await loadAsset(spec));}catch(e){console.warn('候選圖無法載入，保留原圖',e);}
      }));
    }catch(e){config={sprites:{}};assets.clear();}
  }
  function detach(){if(attached){attached.anim.draw=attached.original;attached=null;}}
  function attach(G){
    const player=G.Game.player;
    if(attached&&attached.player===player&&!player.dead&&!['ui','over'].includes(G.Game.state))return;
    detach();
    if(!player||player.dead||G.Game.state==='ui'||G.Game.state==='over')return;
    const anim=player.anim,original=anim.draw;
    attached={player,anim,original};
    anim.draw=function(ctx,x,y,opts={}){
      const asset=assets.get(player.dex);
      const use=checkbox.checked&&asset&&G.Game.player===player&&!player.dead&&player.walking&&!anim.busy()&&
        G.NarutoChidori?.active?.owner!==player&&G.NarutoFireball?.active?.owner!==player&&!G.CastContinuityLab?.active(player)&&!opts.flash;
      if(!use){counters.source++;return original.call(this,ctx,x,y,opts);}
      const angle=player.attackFace>0?player.aim:player.moveAngle;
      const row=asset.spec.directions[direction(angle)],frame=Math.floor(performance.now()/100)%asset.spec.columns;
      const cell=asset.cells[row*asset.spec.columns+frame];
      if(!cell){counters.source++;return original.call(this,ctx,x,y,opts);}
      counters.candidate++;
      const height=64*(anim.scale||1),scale=height/cell.h;
      ctx.save();ctx.imageSmoothingEnabled=false;ctx.globalAlpha*=opts.alpha??1;
      ctx.drawImage(asset.image,cell.x,cell.y,cell.w,cell.h,Math.round(x-cell.w*scale/2),Math.round(y-height),cell.w*scale,height);
      ctx.restore();
    };
  }
  function game(){return iframe.contentWindow?.G;}
  function focus(){iframe.focus();iframe.contentWindow.focus();}
  document.querySelector('#levelup').onclick=()=>{
    const G=game(),p=G?.Game.player;
    if(!p||p.dead||!['playing','paused'].includes(G.Game.state))return;
    document.querySelector('#levelup').disabled=true;
    if(G.Game.state==='paused')G.Game.togglePause();
    G.Game.debugLevelUp();focus();
  };
  document.querySelectorAll('[data-hero]').forEach(button=>button.onclick=()=>{
    const G=game();if(!ready)return;
    detach();G.Naruto.choose(Number(button.dataset.hero));G.Flow.play();focus();
  });
  document.querySelector('#training').onclick=()=>{
    const G=game(),p=G?.Game.player;if(!p||p.dead)return;
    const active=p.activeMove()?.id;
    // Explicit opt-in test control; normal starts, damage, cooldowns and movement are untouched.
    const catalog=G.NarutoSkillCatalog;
    const ids=[catalog.byDex.get(p.dex)?.id,...(catalog.extraPools.get(p.dex)||[])].filter(Boolean);
    p.maxMoves=Math.max(p.maxMoves,ids.length);
    for(const id of ids)if(!p.hasMove(id))p.addMove(id);
    const index=p.slots.findIndex(group=>group.some(m=>m.id===active));if(index>=0)p.setActive(index);
    focus();
  };
  checkbox.onchange=focus;
  setInterval(()=>{
    try{
      const G=game();ready=!!G?.Game&&!!G?.Naruto&&!!G.DB?.save&&iframe.contentDocument.querySelector('#boot')?.classList.contains('hidden');
      document.querySelectorAll('[data-hero]').forEach(b=>b.disabled=!ready);
      if(!ready)return;
      window.CastContinuityLab?.install(G);
      attach(G);
      const p=G.Game.player;
      document.querySelector('#levelup').disabled=!p||p.dead||!['playing','paused'].includes(G.Game.state);
      document.querySelector('#training').disabled=!p||p.dead||G.Game.state==='ui';
      const name=p?.dex===30002?'佐助':p?.dex===30001?'鳴人':'尚未開局';
      status.textContent=`${name} · ${G.Game.state} · ${checkbox.checked&&assets.has(p?.dex)?'實驗移動圖；施術沿用原版':'原版動作（無合格素材時自動保留）'} · 技能：${p?.activeMove()?.name||'—'}。這是實際遊戲，不是動畫播放影片。`;
    }catch(e){ready=false;detach();}
  },120);
  iframe.addEventListener('load',detach);
  window.addEventListener('pagehide',detach);
  window.GameplayLab={direction,reloadConfig,counters,get attached(){return attached;},get ready(){return ready;},get assets(){return assets;}};
  reloadConfig();
})();
