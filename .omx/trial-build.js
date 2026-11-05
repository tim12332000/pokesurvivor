/* Practice recipes spend the same legal level-up opportunities as a normal run. */
(() => {
  const routes={30013:['blade','rika'],30014:['precision','spread'],30015:['control','counter']};
  const focus={blade:['jjk-yuta','jjk-yuta-speech'],rika:['jjk-yuta-rika','jjk-yuta-manifest'],
    precision:['jjk-ryu','jjk-ryu-maximum'],spread:['jjk-ryu-spread','jjk-ryu-impact'],
    control:['jjk-uro-thin-ice','jjk-uro-collapse'],counter:['jjk-uro-screen','jjk-uro']};
  const names={blade:'刀術接力',rika:'里香窗口',precision:'精準直線',spread:'散射清線',control:'碎面控場',counter:'有限反擊',balanced:'均衡配裝'};
  function apply(player,route,budget=19){
    if(!routes[player.dex]||![...routes[player.dex],'balanced'].includes(route))throw Error('無效的角色配裝');
    if(player.level!==1||player.moves.length!==1||Object.values(player.statsTaken||{}).some(Boolean))throw Error('配裝必須從一級白板開始');
    const picks=[],ids=G.Jujutsu.kits.find(([dex])=>dex===player.dex)[1].map(row=>row[0]);
    const snapshot=()=>({atk:player.atk,cdMul:player.cdMul,maxHp:player.maxHp,ranks:Object.fromEntries(player.moves.map(m=>[m.id,m.lvl]))});
    const count=Math.max(0,Math.min(60,Math.floor(budget)));
    for(let i=0;i<count;i++){
      player.level=i+2;
      const cards=G.JujutsuGrowth?.legalOffers(player,100)||G.LevelUp.offer(player,100);
      const wanted=focus[route]||ids;
      const newMove=cards.find(c=>c.key?.startsWith('new:')&&ids.includes(c.key.slice(4)));
      const upgrades=cards.filter(c=>c.key?.startsWith('up:')&&wanted.includes(c.key.slice(3)));
      upgrades.sort((a,b)=>route==='balanced'?(player.moves.find(m=>m.id===a.key.slice(3))?.lvl||0)-(player.moves.find(m=>m.id===b.key.slice(3))?.lvl||0):wanted.indexOf(a.key.slice(3))-wanted.indexOf(b.key.slice(3)));
      const statKeys=route==='rika'||route==='counter'?['cd','def','atk']:route==='balanced'?['atk','def','cd']:['atk','cd','def'];
      const preferred=statKeys[i%statKeys.length];
      const card=newMove||upgrades[0]||cards.find(c=>c.key==='stat:'+preferred)||cards.find(c=>c.key==='stat:atk')||cards[0];
      const before=snapshot();
      if(!card||card.apply(player)===false)throw Error('無合法配裝選卡：Lv.'+player.level);
      card.onShown?.(player);picks.push({level:player.level,key:card.key,description:card.desc,before,after:snapshot()});
    }
    player.xp=0;player.xpNext=G.Player.xpFor(player.level);player.arrange();
    player.trialBuild={mode:'preset',route,name:names[route],picks};return picks;
  }
  G.TrialBuild={apply,routes,names};
  const local=['localhost','127.0.0.1','[::1]'].includes(location.hostname);
  if(!local)return;
  const params=new URLSearchParams(location.search);
  if(params.get('startLevel')!=='20')return;
  const panel=document.createElement('section');panel.id='trial-build-options';
  panel.style.cssText='grid-column:1/-1;margin:10px 0;padding:10px;font-size:11px;border:1px solid #58716a;border-radius:8px;background:#142725;color:#d6e6df';
  const description=document.createElement('p');description.textContent='試招：20級／四招一階，未配置19次成長。標準配裝：花19次合法選卡，含學招成本。';panel.append(description);
  const buttons=document.createElement('div');buttons.style.cssText='display:flex;flex-wrap:wrap;gap:5px';panel.append(buttons);
  document.querySelector('.launch-action')?.before(panel);
  function render(){
    const dex=+G.DB.save.partner;panel.hidden=!routes[dex];buttons.replaceChildren();if(!routes[dex])return;
    const url=new URL(location.href);let current=url.searchParams.get('build')||'';
    if(current&&![...routes[dex],'balanced'].includes(current)){current='balanced';url.searchParams.set('build',current);}
    url.searchParams.set('hero',G.Naruto.records.get(dex).slug);
    if(url.href!==location.href)history.replaceState(null,'',url);
    for(const route of ['',...routes[dex],'balanced']){
      const button=document.createElement('button');button.className='btn small'+(route===current?' gold':'');button.style.minHeight='44px';button.textContent=names[route]||'四招試招';button.setAttribute('aria-pressed',String(route===current));
      button.onclick=()=>{const url=new URL(location.href);if(route)url.searchParams.set('build',route);else url.searchParams.delete('build');history.replaceState(null,'',url);render();};buttons.append(button);
    }
  }
  const open=G.MenuUI.open;G.MenuUI.open=function(...args){const result=open.apply(this,args);render();return result;};
})();
