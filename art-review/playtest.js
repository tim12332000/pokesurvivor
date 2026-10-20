/* Embed the original game with one complete lab presentation layer. */
(() => {
  'use strict';
  const iframe=document.querySelector('#game'),checkbox=document.querySelector('#candidate'),status=document.querySelector('#status');
  const skill=document.querySelector('#skill');
  let ready=false,assetsReady=false,loadError='',skillKey='';
  const game=()=>iframe.contentWindow?.G;
  const focus=()=>{iframe.focus();iframe.contentWindow.focus();};
  const direction=angle=>['right','down','left','up'][((Math.round(angle/(Math.PI/2))%4)+4)%4];
  async function reloadConfig(){
    assetsReady=false;loadError='';
    try{await Promise.all([AnimationAssets.load(),KyuubiForm.load()]);assetsReady=true;}
    catch(error){loadError=error.message;status.textContent='動作素材載入失敗：'+loadError+'。請重新整理。';}
  }
  document.querySelector('#levelup').onclick=()=>{
    const G=game(),p=G?.Game.player;
    if(!p||p.dead||!['playing','paused'].includes(G.Game.state))return;
    if(G.Game.state==='paused')G.Game.togglePause();
    G.Game.debugLevelUp();focus();
  };
  document.querySelectorAll('[data-hero]').forEach(button=>button.onclick=()=>{
    if(!ready)return;
    const G=game();G.Naruto.choose(Number(button.dataset.hero));G.Flow.play();skillKey='';focus();
  });
  document.querySelector('#training').onclick=()=>{
    const G=game(),p=G?.Game.player;if(!p||p.dead)return;
    const active=p.activeMove()?.id,catalog=G.NarutoSkillCatalog;
    const ids=[...new Set([catalog.byDex.get(p.dex)?.id,...(catalog.extraPools.get(p.dex)||[]),'naruto-kunai','naruto-shuriken'].filter(Boolean))];
    p.maxMoves=Math.max(p.maxMoves,ids.length);
    for(const id of ids)if(!p.hasMove(id))p.addMove(id);
    const index=p.slots.findIndex(group=>group.some(m=>m.id===active));if(index>=0)p.setActive(index);
    skillKey='';focus();
  };
  skill.onchange=()=>{
    const G=game(),p=G?.Game.player;if(!p||p.dead)return;
    const index=p.slots.findIndex(group=>group.some(m=>m.id===skill.value));
    if(index>=0)p.setActive(index);
    focus();
  };
  checkbox.onchange=focus;
  setInterval(()=>{
    try{
      const G=game();ready=assetsReady&&!!G?.Game&&!!G?.Naruto&&!!G.DB?.save&&iframe.contentDocument.querySelector('#boot')?.classList.contains('hidden');
      document.querySelectorAll('[data-hero]').forEach(b=>b.disabled=!ready);
      if(!ready){if(!loadError)status.textContent='載入完整動作素材與原遊戲中…';return;}
      CastContinuityLab.install(G);
      AnimationRuntime.install(G,{enabled:()=>checkbox.checked});
      KyuubiForm.install(G,{enabled:()=>checkbox.checked});
      const p=G.Game.player,live=!!p&&!p.dead&&['playing','paused'].includes(G.Game.state);
      document.querySelector('#levelup').disabled=!live;
      document.querySelector('#training').disabled=!live;
      skill.disabled=!live;
      const key=p?.moves.map(m=>m.id+':'+m.lvl+':'+m.name).join('|')||'';
      if(skillKey!==key){
        skill.replaceChildren();
        for(const move of p?.moves||[]){const option=document.createElement('option');option.value=move.id;option.textContent=move.name+(move.passive?'（被動）':'');skill.append(option);}
        skillKey=key;
      }
      if(p?.activeMove())skill.value=p.activeMove().id;
      const name=p?.dex===30002?'佐助':p?.dex===30001?'鳴人':'尚未開局';
      status.textContent=name+' · '+(checkbox.checked?'統一重繪版':'原版對照')+' · '+G.Game.state+' · '+(p?.activeMove()?.name||'先選角色開局')+'。角色圖重新繪製；可升級選卡或解鎖招式逐招測試。';
    }catch(error){ready=false;status.textContent='內測載入失敗：'+error.message;}
  },120);
  window.GameplayLab={direction,reloadConfig,get ready(){return ready;},get counters(){return game()?.AnimationLab?.counters||{source:0,candidate:0};}};
  reloadConfig();
})();
