/* Private test entry uses its own browser save and changes only the next run. */
(() => {
  if(new URLSearchParams(location.search).get('painBeta')!=='1')return;
  let practice=true;
  const panel=document.createElement('section');
  panel.id='pain-beta-options';panel.translate=false;
  panel.innerHTML='<b>只管移動，六道自動出招</b><p>你控制天道，其他五道各自幫忙攻擊與防守。<br>電腦用方向鍵／WASD；手機拖曳左下搖桿。</p><details><summary>其他玩法</summary><div><button type="button" data-pain-mode="practice" aria-pressed="true">直接試全部招式</button><button type="button" data-pain-mode="normal" aria-pressed="false">從頭升級學招</button></div></details>';
  const action=document.querySelector('.launch-action');action.before(panel);
  for(const button of panel.querySelectorAll('button'))button.onclick=()=>{
    practice=button.dataset.painMode==='practice';
    for(const item of panel.querySelectorAll('button'))item.setAttribute('aria-pressed',String(item===button));
  };
  const menu=G.MenuUI.open;
  G.MenuUI.open=function(...args){const result=menu.apply(this,args);panel.hidden=+G.DB.save.partner!==30010;return result;};
  const start=G.Game.startRun;
  G.Game.startRun=function(...args){
    const result=start.apply(this,args),p=G.Game.player;
    if(practice&&p?.mon?.dex===30010){
      p.level=15;p.xp=0;p.xpNext=G.Player.xpFor(15);p.narutoMilestonesShown??=new Set();
      for(const id of G.NarutoSkillCatalog.extraPools.get(30010)||[]){p.addMove(id);p.narutoMilestonesShown.add(id);}
      G.UI.toast('只管移動，六道會各自自動出招。',3000);
    }
    return result;
  };
  const style=document.createElement('style');
  style.textContent='#pain-beta-options{padding:12px;margin:12px 0;border:1px solid #a77d8d;border-radius:10px;background:#191c2b;color:#f5dce6}#pain-beta-options p{font-size:12px;line-height:1.6;margin:6px 0}#pain-beta-options>div{display:flex;gap:7px;flex-wrap:wrap}#pain-beta-options button{font:inherit;font-size:12px;cursor:pointer;padding:9px;border-radius:6px;background:#242638;color:#ddd;border:1px solid #656078}#pain-beta-options button[aria-pressed=true]{background:#693e56;color:white;border-color:#e6a7bf}#pain-beta-options small{display:block;margin-top:8px;color:#bcaebf;font-size:10px}';
  document.head.append(style);
  style.textContent+='#pain-beta-options details{margin-top:12px;border-top:1px solid #4a4053;padding-top:9px}#pain-beta-options summary{cursor:pointer;font-size:12px;color:#d7c2d5}#pain-beta-options details>div{display:flex;gap:7px;flex-wrap:wrap;margin-top:9px}';
  style.textContent+='body #scr-menu.launch-menu .launch-detail>#pain-beta-options{display:block;grid-column:1 / -1;width:100%;min-width:0;margin:12px 0;text-align:left}body #scr-menu.launch-menu .launch-detail>#pain-beta-options[hidden]{display:none}';
})();
