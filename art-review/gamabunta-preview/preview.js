/* Replay the actual summoning module on an isolated canvas stage. */
(() => {
  const $=id=>document.getElementById(id),canvas=$('scene'),ctx=canvas.getContext('2d'),stage=window.GamabuntaStage;
  const durations=[2.6,3,3,7.2,8.8],damages=[160,192,192,192,240];
  const names={arrival:'通靈登場', 'heavy-drop':'屋台崩壞・巨體重壓',water:'水遁・鐵砲玉',rest:'文太支援', 'sword-windup':'蛤蟆短刀斬・拔刀', 'sword-hit':'蛤蟆短刀斬・揮斬', 'sword-recovery':'蛤蟆短刀斬・收勢', 'fire-windup':'蛤蟆油炎彈・準備',fire:'蛤蟆油炎彈',transform:'組合變化・鳴人結印', 'fox-ready':'組合變化・巨狐', 'fox-dash':'巨狐突襲・抓咬', 'fox-recovery':'巨狐・收勢'};
  let rank=5,time=0,playing=true,ready=false,last=0,move,field;
  function labels(){
    $('phase').textContent=time>=move.duration?'完成・煙霧退場':names[G.NarutoSummoning.phaseFor(field)]||'通靈術';
    $('clock').textContent=`${Math.min(time,move.duration).toFixed(2)} / ${move.duration.toFixed(2)} s`;$('seek').value=Math.round(time*1000);
  }
  function reset(){
    G.Combat.clearFields();G.Projectiles.clear();G.FX.clear();stage.reset(+$('direction').value);
    move={id:'naruto-toad-summon',digiMode:'toad-summon',lvl:rank,type:'normal',range:320,radius:rank>=3?128.8:115,windup:rank>=3?.9:.65,duration:durations[rank-1],dmg:damages[rank-1],knock:90};
    if(!G.NarutoSummoning.cast(stage.owner,move))throw Error('文太素材尚未就緒');
    field=G.NarutoSummoning.effects[0];field.mirror=+$('direction').value<0;time=0;
    $('seek').max=move.duration*1000;labels();
  }
  function step(seconds){
    for(let elapsed=0;elapsed<seconds-1e-8;){const dt=Math.min(.005,seconds-elapsed);
      G.Projectiles.update(dt,stage.owner,stage.enemies);G.Combat.resolve(dt,stage.owner,time);G.Combat.updateFields(dt);G.FX.update(dt);
      for(const e of stage.enemies)e.flash=Math.max(0,e.flash-dt);time+=dt;elapsed+=dt;
    }
    labels();
  }
  function draw(){
    ctx.fillStyle='#203b2d';ctx.fillRect(0,0,960,620);
    ctx.strokeStyle='#294733';ctx.lineWidth=1;
    for(let y=0;y<620;y+=40){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(960,y);ctx.stroke()}
    for(let x=0;x<960;x+=40){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,620);ctx.stroke()}
    ctx.save();ctx.translate(430,390);ctx.scale(1.55,1.55);ctx.imageSmoothingEnabled=false;
    G.Combat.drawGroundFields(ctx);
    for(const e of stage.enemies){ctx.fillStyle='#12251c';ctx.beginPath();ctx.ellipse(e.x,e.y,16,7,0,0,7);ctx.fill();ctx.fillStyle=e.flash?'#fff6d1':'#b7b396';ctx.fillRect(e.x-11,e.y-29,22,29);ctx.fillStyle='#5c695b';ctx.fillRect(e.x-9,e.y-22,18,5);ctx.fillRect(e.x-3,e.y-16,6,12)}
    const pose=G.NarutoSummoning.poseFor(stage.owner),side=+$('direction').value;
    const key=pose?.kind==='tag'?'naruto-throw':pose?.kind==='seal'||time<.65?'naruto-clones':'naruto-idle';
    const frame=pose?.kind==='tag'?2:key==='naruto-clones'?Math.min(3,Math.floor((pose?.age??time)/.65*4)):12;
    window.AnimationAssets.draw(ctx,key,frame,stage.owner.x,stage.owner.y,{mirror:pose?.mirror??side<0});
    G.Combat.drawAirFields(ctx);G.Projectiles.draw(ctx);G.FX.draw(ctx);ctx.restore();
  }
  function seek(t){if(!ready)return;playing=false;$('play').textContent='播放';reset();step(Math.max(0,Math.min(move.duration,t)));draw()}
  function select(n){rank=n;document.querySelectorAll('[data-tier]').forEach(b=>b.setAttribute('aria-pressed',String(+b.dataset.tier===rank)));document.querySelector('.badge').textContent=`第${rank}階・循環展示`;document.querySelectorAll('[data-unlock]').forEach(b=>b.disabled=+b.dataset.unlock>rank);if(ready){reset();draw()}}
  $('play').onclick=()=>{if(!ready)return;if(time>=move.duration)reset();playing=!playing;$('play').textContent=playing?'暫停':'播放'};
  $('replay').onclick=()=>{if(!ready)return;reset();playing=true;$('play').textContent='暫停'};
  $('seek').oninput=()=>seek(+$('seek').value/1000);
  $('direction').onchange=()=>{if(ready){const t=time;seek(t)}};
  document.querySelectorAll('[data-tier]').forEach(b=>b.onclick=()=>select(+b.dataset.tier));
  document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>seek(+b.dataset.time));
  window.preview={seek,select,get ready(){return ready},get time(){return time},get rank(){return rank},get field(){return field}};
  function tick(now){if(last&&playing){const dt=Math.min(.05,(now-last)/1000)*+$('speed').value;if(time+dt>move.duration+.8)reset();else step(dt)}last=now;draw();requestAnimationFrame(tick)}
  Promise.all([G.NarutoSummoning.ready,window.AnimationAssets.loadHero(30001)]).then(()=>{ready=true;select(rank);$('play').disabled=$('replay').disabled=$('seek').disabled=false;requestAnimationFrame(tick)}).catch(e=>{$('error').textContent='素材載入失敗：'+e.message});
})();
