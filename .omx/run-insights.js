/* Run-local feedback and choices. Recorded losses are HP+shield, not overkill DPS. */
(() => {
  let run=null,overlay=null,suppressedUntil=0;
  const causes={contact:'近身碰撞',projectile:'敵方飛彈',hazard:'地面危險',other:'其他／持續傷害'};
  const alive=a=>a&&!a.dead&&a.hp>0;
  const controlled=a=>a===G.Game.player||G.SelfClones?.isActor(a);
  function reset(){overlay?.remove();overlay=null;suppressedUntil=0;run={owner:G.Game.player,damage:{},received:{},casts:{},waits:{},fifthBossDefeated:false,fifthEnemy:null,fifthProcessed:false,milestoneShown:false};}
  function current(){if(!run||run.owner!==G.Game.player)reset();return run;}
  function snapshot(){const s=current();return {damage:{...s.damage},received:{...s.received},casts:{...s.casts},waits:{...s.waits},fifthBossDefeated:s.fifthBossDefeated,milestoneShown:s.milestoneShown};}
  const start=G.Game.startRun;
  G.Game.startRun=function(...args){const result=start.apply(this,args);if(result?.then)return result.then(value=>{reset();return value;});reset();return result;};
  const enemyHurt=G.Enemy.prototype.hurt;
  G.Enemy.prototype.hurt=function(amount,color,dx,dy,knock,eff,owner,moveId){
    const before=Math.max(0,this.hp)+Math.max(0,this.shield||0),result=enemyHurt.apply(this,arguments);
    if(controlled(owner)&&moveId){const lost=Math.max(0,before-Math.max(0,this.hp)-Math.max(0,this.shield||0));
      if(lost){const s=current(),category=G.DamageSplash?.isSecondary()?'擴散':owner!==G.Game.player?'分身':moveId==='jjk-yuta-rika'?'里香':moveId==='jjk-uro-screen'?'反射':'直接';
        const key=category+'・'+(G.Moves.BY_ID[moveId]?.name||moveId);s.damage[key]=(s.damage[key]||0)+lost;}}
    return result;
  };
  const playerHurt=G.Player.prototype.hurt;
  G.Player.prototype.hurt=function(amount,type,pure,meta){const hp=this.hp,result=playerHurt.apply(this,arguments);
    if(this===G.Game.player&&hp>this.hp){const cause=causes[meta?.cause]||causes.other,s=current();s.received[cause]=(s.received[cause]||0)+hp-this.hp;}return result;};
  const cast=G.Player.prototype.cast;
  G.Player.prototype.cast=function(move,...args){if(controlled(this)&&move?.id){const s=current(),key=(this===G.Game.player?'本體':'分身')+'・'+move.name;s.casts[key]=(s.casts[key]||0)+1;}return cast.call(this,move,...args);};
  const die=G.Enemy.prototype.die;
  G.Enemy.prototype.die=function(...args){const wasDead=this.dead,result=die.apply(this,args);if(!wasDead&&this.dead&&this.mainBossSlot===4&&!this.remote&&!this.judge){const s=current();s.fifthBossDefeated=true;s.fifthEnemy=this;}return result;};
  const enemyUpdate=G.EnemyMgr.update;
  G.EnemyMgr.update=function(...args){const result=enemyUpdate.apply(this,args),s=current();if(s.fifthEnemy&&!G.EnemyMgr.all().includes(s.fifthEnemy))s.fifthProcessed=true;return result;};
  function showChoice(title,description,choices){
    if(overlay)return false;
    return G.Game.openChoice(finish=>{
      overlay=document.createElement('div');overlay.id='council-choice';overlay.setAttribute('role','dialog');overlay.setAttribute('aria-label',title);
      overlay.style.cssText='position:fixed;inset:0;z-index:1000;display:grid;place-items:center;background:#08111dd9;padding:16px';
      const box=document.createElement('section');box.className='box';box.style.cssText='max-width:620px;width:100%;max-height:85vh;overflow:auto;padding:20px';
      const h=document.createElement('h2');h.textContent=title;const p=document.createElement('p');p.textContent=description;box.append(h,p);
      for(const choice of choices){const button=document.createElement('button');button.className='btn';button.style.cssText='width:100%;min-height:48px;margin-top:10px;white-space:normal;text-align:left';
        button.textContent=choice.title+(choice.desc?' — '+choice.desc:'');button.onclick=()=>{if(choice.apply?.()===false)return;overlay?.remove();overlay=null;finish();choice.after?.();};box.append(button);}
      overlay.append(box);document.body.append(overlay);box.querySelector('button')?.focus();
    });
  }
  function offerMastery(player){
    if(player!==G.Game.player||!alive(player)||G.Game.st.time<suppressedUntil)return false;
    const state=G.JujutsuGrowth?.bondState(player);if(state?.mode!=='growth'||!state.options?.length)return false;
    return showChoice('羈絆精通','這位角色無可融合招式，改選一次有效成長。僅選擇成功後消耗一個羈絆。',[
      ...state.options.slice(0,3).map(card=>({title:card.title,desc:card.desc,apply:()=>G.JujutsuGrowth.applyBondCard(player,card)})),
      {title:'暫存羈絆',desc:'稍後再選',apply:()=>{suppressedUntil=G.Game.st.time+30;}}
    ]);
  }
  const update=G.Combat.updateFields;
  G.Combat.updateFields=function(dt){const result=update.call(this,dt),s=current();
    if(G.Game.state==='playing'&&dt>0&&alive(G.Game.player))for(const move of G.Game.player.moves){
      const api=G.Game.player.dex===30013?G.JujutsuYuta:G.Game.player.dex===30014?G.JjkRyu:G.JjkUro;
      if(move.jujutsuSkill&&api?.statusFor?.(G.Game.player,move).state==='queued')s.waits[move.name]=(s.waits[move.name]||0)+dt;
    }
    if(s.fifthBossDefeated&&s.fifthProcessed&&!s.milestoneShown&&G.Game.state==='playing'&&alive(G.Game.player)){
      if(showChoice('五首領里程碑','已擊敗第五個既定主線首領。可結算，或繼續無盡與30分鐘挑戰；現在離開不會自動拾取地上戰利品。',[
        {title:'繼續挑戰',apply:()=>{s.milestoneShown=true;}},
        {title:'現在結算',apply:()=>{s.milestoneShown=true;},after:()=>G.Game.quit()}
      ]))s.milestoneShown=true;
    }return result;
  };
  const escaped=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function summary(){const s=snapshot(),list=(data,limit)=>Object.entries(data).sort((a,b)=>b[1]-a[1]).slice(0,limit).map(([name,value])=>`<li>${escaped(name)}：${Math.round(value*10)/10}</li>`).join('')||'<li>尚無紀錄</li>';
    return `<section class="box" id="run-insights" style="grid-column:1/-1;min-width:0"><h3>本局回顧</h3><p>傷害按實際生命與護盾減少記錄，不含過量傷害。</p><h4>主要承傷來源</h4><ul>${list(s.received,3)}</ul><h4>輸出貢獻</h4><ul>${list(s.damage,10)}</ul><h4>實際施放次數</h4><ul>${list(s.casts,10)}</ul><h4>就緒時動作等待（遊戲秒）</h4><ul>${list(s.waits,6)}</ul></section>`;}
  const over=G.RunUI.showOver;
  G.RunUI.showOver=function(...args){const result=over.apply(this,args);document.getElementById('over-stats')?.insertAdjacentHTML('beforeend',summary());return result;};
  function skillState(player,move){
    if(!move?.id?.startsWith('jjk-'))return null;
    const api=player.dex===30013?G.JujutsuYuta:player.dex===30014?G.JjkRyu:G.JjkUro;
    if(player.dex===30013){
      const s=api?.stateFor?.(player);
      if(move.id==='jjk-yuta-manifest'&&s?.manifestUntil>s.clock){const left=s.manifestUntil-s.clock;return {label:'顯現 '+left.toFixed(1)+'s',fraction:left/G.Jujutsu.power.yuta.manifestDuration};}
      if(move.id==='jjk-yuta-rika'&&s?.rika){const r=s.rika;return {label:r.phase==='strike'?(r.full?'雙人 ':'協擊 ')+r.strikeIndex+'/'+r.strikeCount:r.phase==='return'?'回身中':'追擊中',fraction:r.phase==='strike'?1-r.strikeIndex/r.strikeCount:0};}
      if(move.id==='jjk-yuta-resonance')return {label:s?.action?.kind==='resonance'?'共鳴終擊':s?.pendingResonance?.length?'待共鳴':'終擊連動',fraction:0};
    }
    if(player.dex===30015){
      const field=api?.effects?.findLast(b=>b.owner===player&&b.id===move.id);
      if(field&&move.id!=='jjk-uro')return {label:(field.mode==='uro-counter'?'反擊 ':field.mode==='uro-echo'?'殘響 ':'裂波 ')+Math.max(0,field.pulseIndex+1)+'/'+field.pulseCount,fraction:1-Math.max(0,field.pulseIndex+1)/field.pulseCount};
      if(move.id==='jjk-uro-screen'){const screen=api?.stateFor?.(player)?.screen;if(screen)return {label:'反射 '+screen.budget,fraction:Math.min(1,screen.budget/Math.max(1,screen.initialBudget??api.fractureProfile(player,move).budget))};}
      if(move.id==='jjk-uro-echo')return {label:'殘響連動',fraction:0};
    }
    if(move.id==='jjk-ryu-maximum'){
      const barrage=api?.pose?.(player);
      if(barrage?.mode==='jjk-ryu-maximum')return barrage.released?
        {label:'連轟 '+(barrage.volleyIndex+1)+'/'+barrage.volleyCount,fraction:1-(barrage.volleyIndex+1)/barrage.volleyCount}:
        {label:'巨砲蓄力',fraction:Math.max(0,1-barrage.age/barrage.charge)};
    }
    const status=api?.statusFor?.(player,move);
    if(status){const remaining=Math.max(0,(status.state==='recovering'?status.recoveryRemaining:status.remaining)||0),labels={casting:'施放中',queued:'待出手',ready:'就緒'},waiting={pressure:'等近敵',encounter:'等敵群',projectile:'等敵彈'};
      const label=status.state==='active'?(move.id==='jjk-yuta-manifest'?'顯現 ':'作用 ')+remaining.toFixed(1)+'s':
        ['recovery','recovering'].includes(status.state)?'恢復 '+remaining.toFixed(1)+'s':status.state==='charging'?'蓄能 '+(status.coreCharge||0)+'/'+(status.chargeRequired||3):
        status.state==='waiting'?(waiting[status.reason]||'等待時機'):status.state==='cooldown'?remaining.toFixed(1)+'s':
        status.reason==='riposte'?(status.state==='queued'?'待反擊':'反擊就緒'):labels[status.state]||'就緒';
      return {label,fraction:status.state==='charging'?1-(status.coreCharge||0)/(status.chargeRequired||3):status.state==='active'?remaining/(move.duration||6):Math.min(1,remaining/Math.max(.05,(move.recovery||move.cd)*player.cdMul))};}
    const s=api?.stateFor(player),action=api?.pose?.(player)||api?.poseFor?.(player)||s?.action;
    const manifest=player.dex===30013?G.JujutsuYuta.inspect(player)?.manifestRemaining||0:0;
    if(move.id==='jjk-yuta-manifest'&&manifest>0)return {label:'顯現 '+manifest.toFixed(1)+'s',fraction:manifest/8};
    if(move.id==='jjk-yuta-rika'&&s?.rika)return {label:'協擊中',fraction:0};
    if(action&&(action.m?.id||action.id)===move.id)return {label:'施放中',fraction:0};
    if(move.t>0)return {label:(move.id==='jjk-yuta-manifest'?'恢復 ':'')+move.t.toFixed(1)+'s',fraction:Math.min(1,move.t/Math.max(.05,move.cd*player.cdMul))};
    return {label:action?'待出手':'就緒',fraction:0};
  }
  G.RunInsights={snapshot,skillState,offerMastery,summary};
})();
