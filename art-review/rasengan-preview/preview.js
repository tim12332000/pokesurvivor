/* Seek a real cast in a paused native game, using its own scene and camera. */
(() => {
  'use strict';
  const $=id=>document.getElementById(id),duration=1.5;
  let G,owner,move,ready=false,playing=true,time=0,last=0;
  function labels(){
    $('phase').textContent=time<.6?'手心集氣・可自由走位':time<.76?'近身出掌・本體不位移':time<1.04?'命中・衝擊散開':'收勢';
    $('clock').textContent=time.toFixed(2)+' s';$('seek').value=Math.round(time*1000);
  }
  function reset(){
    G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();
    owner.x=owner.y=0;owner.dead=false;owner.hp=owner.maxHp;owner.flash=owner.invuln=0;
    owner.aim=+$('direction').value;owner.anim.loop('Idle');owner.anim.update(1);
    G.Camera.x=G.Camera.y=0;G.Camera.shake=0;
    const a=owner.aim,dx=Math.cos(a),dy=Math.sin(a);
    for(const [along,side] of [[70,0],[60,58],[50,-62]]){
      const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},dx*along-dy*side,dy*along+dx*side,{hp:1,spd:1,dmg:1});
      e.types=['normal'];e.touchCd=999;G.EnemyMgr.add(e);
    }
    G.EnemyMgr.rebuildGrid();owner.target=G.EnemyMgr.all()[0];
    owner.cast(move);G.DigimonSkills.cast(owner,move);time=0;labels();
  }
  function advance(seconds){
    let left=seconds;
    while(left>1e-8){
      const dt=Math.min(.005,left);G.Combat.updateFields(dt);G.FX.update(dt);owner.anim.update(dt);
      for(const e of G.EnemyMgr.all())e.update(dt,owner);
      G.EnemyMgr.rebuildGrid();G.Camera.follow(owner.x,owner.y,dt);left-=dt;
    }
    time+=seconds;labels();
  }
  function pause(){playing=false;$('play').textContent='播放'}
  function seek(t){if(!ready)return;pause();reset();advance(Math.max(0,Math.min(duration,t)))}
  $('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'暫停':'播放'};
  $('replay').onclick=()=>{if(!ready)return;reset();playing=true;$('play').textContent='暫停'};
  $('seek').oninput=()=>seek(+$('seek').value/1000);
  $('direction').onchange=()=>{const t=time;seek(t)};
  document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>seek(+b.dataset.time));
  window.preview={seek,get ready(){return ready},get time(){return time}};
  async function init(){
    const win=$('game').contentWindow,started=performance.now();
    await new Promise((resolve,reject)=>{function check(){if(win.G?.DB?.save&&win.PS_REDRAWN_READY&&win.G.NarutoRasenganVFX)resolve();else if(performance.now()-started>30000)reject(Error('遊戲載入逾時'));else setTimeout(check,80)}check()});
    await win.PS_REDRAWN_READY;G=win.G;
    win.document.querySelector('#tap-start')?.click();G.Naruto.choose(30001);await G.Flow.play();
    if(G.Game.state==='playing')G.Game.togglePause();G.UI.hideAll();
    win.document.querySelector('#tap-start').style.display='none';G.UI.toast=()=>{};
    win.document.querySelectorAll('.toast,#ach-pop').forEach(e=>e.style.display='none');
    owner=G.Game.player;owner.level=30;owner.moves=[];owner.slots=[];owner.bind={};owner.active=0;owner.addMove('naruto-naruto');move=owner.moves[0];
    owner.critChance=0;owner.percentHealthDamage=0;owner.lifestealRate=0;
    // The controlled demonstration opens terrain; normal gameplay retains its collisions.
    Object.assign(G.World,{isFree:()=>true,collide:()=>{},isWall:()=>false,isLiquid:()=>false,projectileBlock:()=>false});
    ready=true;reset();requestAnimationFrame(tick);
  }
  function tick(now){
    if(last&&playing){const dt=Math.min(.04,(now-last)/1000)*+$('speed').value;if(time+dt>=duration)reset();else advance(dt)}
    last=now;requestAnimationFrame(tick);
  }
  init().catch(e=>{$('error').textContent='預覽載入失敗：'+e.message});
})();
