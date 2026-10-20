/* Personal test controls: the public IP is checked in memory and never saved. */
(() => {
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(location.hostname);
  const button=document.createElement('button');
  button.id='dev-level-up';button.className='btn small gold hidden';button.translate=false;
  button.textContent='升一等';button.title='測試用：升一等並選擇升級';
  button.style.cssText='position:fixed;left:12px;top:calc(env(safe-area-inset-top,0px) + 72px);z-index:50;min-width:84px;min-height:44px;touch-action:manipulation';
  document.body.append(button);
  const notice=document.createElement('p');notice.translate=false;notice.id='dev-network-notice';
  notice.textContent='測試按鈕會透過 ipify 查詢目前的公網 IPv4，用於判斷是否顯示個人測試控制。本網站不將完整 IP 寫入遊戲存檔；查詢失敗不影響一般遊玩。';
  if (!local) document.querySelector('#scr-legal .box')?.append(notice);
  let allowed=false,pending=false,controller=null,generation=0;
  function render() {
    const state=G.Game.state,player=G.Game.player;
    if(state!=='playing')pending=false;
    button.classList.toggle('hidden',!allowed||state!=='playing'||!player||player.dead||G.Coop.active);
    button.disabled=pending;
  }
  button.onclick=()=>{
    if(!allowed||pending||G.Game.state!=='playing'||!G.Game.player||G.Game.player.dead||G.Coop.active)return;
    pending=true;button.disabled=true;G.Game.debugLevelUp();
  };
  new MutationObserver(render).observe(document.body,{attributes:true,attributeFilter:['data-game-state']});
  async function refresh() {
    const current=++generation;
    controller?.abort();const request=new AbortController();controller=request;
    const signal=request.signal;
    if (local) { allowed=true;render();return true; }
    allowed=false;render();
    let timer=setTimeout(()=>request.abort(),5000);
    try {
      if(!crypto.subtle)return false;
      const settings=await fetch('.omx/dev-network.json',{cache:'no-store',signal});
      if(!settings.ok)return false;
      const config=await settings.json();
      clearTimeout(timer);timer=setTimeout(()=>request.abort(),Math.max(250,Math.min(10000,Number(config.timeoutMs)||5000)));
      const response=await fetch('https://api.ipify.org?format=json',{cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer',signal});
      if(!response.ok)return false;
      const data=await response.json(),parts=String(data.ip||'').trim().split('.');
      if(parts.length!==4||parts.some(p=>!/^\d{1,3}$/.test(p)||Number(p)>255))return false;
      const normalized=parts.map(Number).join('.');
      const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(normalized));
      const hash=[...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join('');
      if(current===generation)allowed=Array.isArray(config.allowedIpv4Sha256)&&config.allowedIpv4Sha256.includes(hash);
    } catch (_) { /* Optional controls stay hidden when the network cannot be verified. */ }
    finally {clearTimeout(timer);if(current===generation)render();}
    return allowed;
  }
  G.DevControls={refresh,get allowed(){return allowed;},ready:null};
  G.DevControls.ready=refresh();
  addEventListener('online',refresh);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
})();
