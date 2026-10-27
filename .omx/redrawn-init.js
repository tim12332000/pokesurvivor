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
    const loading=new Map(),heroes=new Set([30001,30002,30006,30007,30009,30010,30011,30012]);
    const ready=dex=>+dex===30012?!!G.KimimaroArt?.loaded:+dex===30011?!!G.TemariArt?.loaded:+dex===30010?!!G.PainArt?.loaded:!heroes.has(+dex)||(AnimationAssets.heroReady(+dex)&&G.Naruto.records.get(+dex).ready&&(+dex!==30001||!!KyuubiForm.image));
    function ensure(dex) {
      dex=+dex;
      if(ready(dex))return Promise.resolve();
      if(loading.has(dex))return loading.get(dex);
      if(dex===30010||dex===30011||dex===30012){
        const promise=(dex===30012?G.KimimaroArt:dex===30011?G.TemariArt:G.PainArt).ready.then(()=>{G.Naruto.records.get(dex).ready=true;}).finally(()=>{loading.delete(dex);G.Naruto.refreshSelection?.();});
        loading.set(dex,promise);return promise;
      }
      const promise=Promise.all([
        AnimationAssets.loadHero(dex),
        G.Naruto.records.get(dex).loaded.then(ok=>{if(!ok)throw Error('角色素材載入失敗');}),
        dex===30001?KyuubiForm.load():Promise.resolve()
      ]).finally(()=>{loading.delete(dex);G.Naruto.refreshSelection?.();});
      loading.set(dex,promise);return promise;
    }
    function download(dex) {
      const pending=loading.has(+dex),promise=ensure(dex);
      G.Naruto.refreshSelection?.();
      return promise.then(()=>true,()=>{
        if(!pending&&+G.DB.save.partner===+dex)G.UI.toast('角色素材下載失敗，請點選角色卡重試。');
        return false;
      });
    }
    let request=0,lastPartner,busy;
    const button=document.querySelector('#scr-menu [data-go="play"]');
    function setBusy(on) {
      if(on&&!busy){busy={html:button.innerHTML,disabled:button.disabled};button.disabled=true;button.setAttribute('aria-busy','true');button.textContent='下載'+(G.Naruto.records.get(+G.DB.save.partner)?.chinese||'角色')+'素材…';}
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
      return result;
    };
    function startWhenReady(original,context,args,valid) {
      const dex=+G.DB.save.partner;
      if(ready(dex))return original.apply(context,args);
      const ticket=++request;setBusy(true);
      return ensure(dex).then(()=>{
        if(ticket!==request||+G.DB.save.partner!==dex||G.Game.state!=='ui'||!valid())return;
        return original.apply(context,args);
      }).catch(()=>{
        if(ticket===request)G.UI.toast('角色素材載入失敗，請再按開始重試。');
      }).finally(()=>{if(ticket===request)setBusy(false);});
    }
    for(const method of ['play','startCoop']) {
      const original=G.Flow[method];
      G.Flow[method]=function(...args){
        const room=G.Social.room;
        return startWhenReady(original,this,args,()=>method==='play'?!document.getElementById('scr-menu').classList.contains('hidden'):G.Social.room===room);
      };
    }
    const startRun=G.Game.startRun;
    G.Game.startRun=function(...args){
      return startWhenReady(startRun,this,args,()=>true);
    };
    G.NarutoAssets={ensure,ready,download,loading:dex=>loading.has(+dex)};
  });
})();
