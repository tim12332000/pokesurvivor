/* Install metadata first; load only the chosen ninja before entering combat. */
(() => {
  const params = new URLSearchParams(location.search);
  // The review wrapper owns installation inside its child game frame.
  if (params.get('animationLab') === '1' || params.get('originalArt') === '1') return;
  window.PS_REDRAWN_READY = Promise.resolve().then(async () => {
    await AnimationAssets.loadMetadata();
    CastContinuityLab.install(G, { controls: false });
    AnimationRuntime.install(G);
    KyuubiForm.install(G);
    const loading=new Map(),heroes=new Set([30001,30002,30006,30007,30009]);
    const ready=dex=>!heroes.has(+dex)||(AnimationAssets.heroReady(+dex)&&G.Naruto.records.get(+dex).ready&&(+dex!==30001||!!KyuubiForm.image));
    function ensure(dex) {
      dex=+dex;
      if(ready(dex))return Promise.resolve();
      if(loading.has(dex))return loading.get(dex);
      const promise=Promise.all([
        AnimationAssets.loadHero(dex),
        G.Naruto.records.get(dex).loaded.then(ok=>{if(!ok)throw Error('角色素材載入失敗');}),
        dex===30001?KyuubiForm.load():Promise.resolve()
      ]).finally(()=>loading.delete(dex));
      loading.set(dex,promise);return promise;
    }
    let request=0,lastPartner,busy;
    const button=document.querySelector('#scr-menu [data-go="play"]');
    function setBusy(on) {
      if(on&&!busy){busy={html:button.innerHTML,disabled:button.disabled};button.disabled=true;button.setAttribute('aria-busy','true');button.textContent='載入角色…';}
      else if(!on&&busy){button.innerHTML=busy.html;button.disabled=busy.disabled;button.removeAttribute('aria-busy');busy=null;}
    }
    document.addEventListener('click',event=>{
      if(busy&&event.target.closest('[data-go]:not([data-go="play"]),#btn-settings,#btn-naruto,#btn-digimon')){
        request++;setBusy(false);
      }
    },true);
    const menuOpen=G.MenuUI.open;
    G.MenuUI.open=function(...args){
      const result=menuOpen.apply(this,args),dex=+G.DB.save.partner;
      if(dex!==lastPartner){lastPartner=dex;request++;setBusy(false);}
      if(heroes.has(dex))void ensure(dex).catch(()=>{});
      return result;
    };
    for(const method of ['play','startCoop']) {
      const original=G.Flow[method];
      G.Flow[method]=function(...args){
        const dex=+G.DB.save.partner;
        if(ready(dex))return original.apply(this,args);
        const ticket=++request,room=G.Social.room,context=this;setBusy(true);
        return ensure(dex).then(()=>{
          if(ticket!==request||+G.DB.save.partner!==dex||G.Game.state!=='ui'||method==='play'&&document.getElementById('scr-menu').classList.contains('hidden')||method==='startCoop'&&G.Social.room!==room)return;
          return original.apply(context,args);
        }).catch(()=>{
          if(ticket===request)G.UI.toast('角色素材載入失敗，請再按開始重試。');
        }).finally(()=>{if(ticket===request)setBusy(false);});
      };
    }
    const startRun=G.Game.startRun;
    G.Game.startRun=function(...args){
      const dex=+G.DB.save.partner;
      if(!ready(dex))void ensure(dex).catch(()=>{});
      return startRun.apply(this,args);
    };
    G.NarutoAssets={ensure,ready};
  });
})();
