/* Native game camera preview; presentation hooks affect only the paused child frame. */
(() => {
  'use strict';
  const $=id=>document.getElementById(id),TAU=Math.PI*2;
  let c,game,hero,targets=[],time=0,playing=true,last=0,original=false,ready=false;
  let pixelStyle=true;
  let spinOnly=new URLSearchParams(location.search).get('spin')==='1',spinAge=0;
  const phase=t=>t<.48?'聚風・球心成形':t<1.08?'投擲・四刃高速旋轉':t<1.38?'命中・風刃爆開':t<1.78?'餘風散去':'收勢';
  const clamp=t=>Math.max(0,Math.min(1,t));
  function arc(x,y,r,a,len,color,width=1,sy=1){c.save();c.translate(x,y);c.scale(1,sy);c.strokeStyle=color;c.lineWidth=width;c.beginPath();c.arc(0,0,r,a,a+len);c.stroke();c.restore();}
  function weapon(x,y,scale,age,alpha=1){
    if(original)return game.VFX.draw(c,'naruto-wind-shuriken','naruto-blue',x,y,{scale:1.5,angle:age*9,frame:Math.floor(age*12),alpha});
    game.NarutoRasenshurikenVFX.drawWeapon(c,x,y,{age,scale,alpha,pixelated:pixelStyle});
  }
  function burst(x,y,age){game.NarutoRasenshurikenVFX.drawBurst(c,x,y,age,110,{pixelated:pixelStyle})}
  function draw(t){
    $('phase').textContent=spinOnly?'原地旋轉檢視':phase(t);$('clock').textContent=(spinOnly?spinAge:t).toFixed(2)+' s';$('seek').value=Math.round(t*1000);
    $('spin').textContent=spinOnly?'播放完整演出':'原地看旋轉';$('spin').setAttribute('aria-pressed',String(spinOnly));
    if(!ready)return;
    const a=+$('direction').value,dx=Math.cos(a),dy=Math.sin(a);
    hero.aim=a;hero.anim.dir=game.Sprites.dirFromAngle(a);
    const tx=hero.x+dx*150,ty=hero.y+dy*150;
    targets.forEach((e,i)=>{e.x=tx+[0,-38,36][i];e.y=ty+[0,24,34][i];});
  }
  function effect(context){
    c=context;const t=time,a=+$('direction').value,dx=Math.cos(a),dy=Math.sin(a);
    const px=hero.x,py=hero.y,tx=px+dx*150,ty=py+dy*150;
    c.save();c.imageSmoothingEnabled=false;
    if(t>=.48&&t<1.08){
      const q=(t-.48)/.6,x=px+dx*(19+q*131),groundY=py+dy*(19+q*131),y=groundY-game.LIFT;
      c.fillStyle='rgba(12,29,35,.24)';c.beginPath();c.ellipse(x,groundY,29,10,0,0,TAU);c.fill();
      if(original)game.VFX.draw(c,'naruto-wind-shuriken','naruto-blue',x,y,{scale:1.5,angle:t*9,frame:Math.floor(t*12)});
      else{
        for(let i=0;i<3;i++){
          const back=25+i*13;
          c.globalAlpha=.24-i*.05;arc(x-dx*back,y-dy*back,17-i*3,a+1.4,.9,'#b5f6ff',1,.6);
        }c.globalAlpha=1;
        for(let i=0;i<4;i++){const side=i%2?1:-1,back=19+i*8;c.globalAlpha=.4;c.strokeStyle='#91e4ef';c.lineWidth=1;c.beginPath();c.moveTo(x-dx*back-dy*side*10,y-dy*back+dx*side*7);c.lineTo(x-dx*(back+9)-dy*side*9,y-dy*(back+9)+dx*side*7);c.stroke();}c.globalAlpha=1;
        weapon(x,y,.9,spinOnly?spinAge:t);
      }
    }
    if(t>=1.08&&t<1.78){
      if(original){c.globalAlpha=1-(t-1.08)/.7;arc(tx,ty,8+clamp((t-1.08)/.25)*110,0,TAU,'#35bfff',3);}
      else{
        const age=t-1.08,q=clamp(age/.65),r=110*(1-Math.pow(1-q,3));
        c.globalAlpha=(1-q)*.35;arc(tx,ty,r,0,TAU,'#a9eff4',1,.55);c.globalAlpha=1;
        burst(tx,ty-game.LIFT,age);
      }
    }
    c.restore();
  }
  function held(context){
    if(time>=.48)return;
    c=context;const side=Math.cos(+$('direction').value)<0?-1:1;
    const x=hero.x-28*side,y=hero.y-48;
    c.save();weapon(x,y,.22+.65*clamp(time/.4),time);
    for(let i=0;i<3;i++)arc(x,y,25-i*4,time*7+i*2,.8,'#83cde2',1,.55);
    c.restore();
  }
  function pause(){playing=false;$('play').textContent='播放'}
  $('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'暫停':'播放'};
  $('replay').onclick=()=>{spinOnly=false;time=0;playing=true;$('play').textContent='暫停';draw(time)};
  $('seek').oninput=()=>{spinOnly=false;pause();time=+$('seek').value/1000;draw(time)};
  document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>{spinOnly=false;pause();time=+b.dataset.time;draw(time)});
  $('spin').onclick=()=>{spinOnly=!spinOnly;time=spinOnly?.76:0;spinAge=0;playing=true;$('play').textContent='暫停';draw(time)};
  $('original').onclick=()=>{original=!original;$('original').setAttribute('aria-pressed',String(original));draw(time)};
  $('style').onclick=()=>{pixelStyle=!pixelStyle;$('style').textContent=pixelStyle?'對照第三版':'返回遊戲像素風';$('style').setAttribute('aria-pressed',String(!pixelStyle));draw(time)};
  $('direction').onchange=()=>draw(time);
  window.preview={seek(t){spinOnly=false;pause();time=clamp(t/2.2)*2.2;draw(time)},get time(){return time},get spinAge(){return spinAge},get ready(){return ready}};
  async function init(){
    const frame=$('game'),win=frame.contentWindow;
    await new Promise((resolve,reject)=>{const started=performance.now();const check=()=>{if(win.G?.Flow&&win.PS_REDRAWN_READY)resolve();else if(performance.now()-started>30000)reject(Error('??????'));else setTimeout(check,80)};check()});
    await win.PS_REDRAWN_READY;game=win.G;
    const tap=win.document.getElementById('tap-start');if(tap)tap.click();
    game.Naruto.choose(30001);await game.Flow.play();
    if(game.Game.state==='playing')game.Game.togglePause();game.UI.hideAll();
    if(tap)tap.style.display='none';
    game.UI.toast=()=>{};
    win.document.querySelectorAll('.toast,#ach-pop,#toast,#toasts').forEach(el=>el.style.display='none');
    game.Combat.clearFields();game.EnemyMgr.clear();game.Projectiles.clear();game.FX.clear();
    hero=game.Game.player;hero.flash=hero.invuln=0;hero.dead=false;hero.hp=hero.maxHp;
    game.Camera.x=hero.x;game.Camera.y=hero.y;game.Camera.shake=0;
    // Native world, camera, player scale and depth sorting remain in charge.
    // Only this iframe's renderer gets a presentation overlay; simulation stays paused.
    const heroDraw=hero.anim.draw.bind(hero.anim);
    hero.anim.draw=function(context,x,y,opts){
      if(time>=1.78)return heroDraw(context,x,y,opts);
      const f=time<.25?0:time<.48?1:time<.62?2:3;
      return win.AnimationAssets.draw(context,'naruto-throw',f,x,y,{scale:this.scale||1,mirror:Math.cos(hero.aim)<0});
    };
    for(let i=0;i<3;i++){const e=new game.Enemy({dex:19,hp:10000,spd:0,dmg:0,xp:0,behavior:'chase'},180,0,{hp:1,spd:1,dmg:1});game.EnemyMgr.add(e);targets.push(e);}
    const air=game.Combat.drawAirFields;game.Combat.drawAirFields=function(context){air.call(this,context);effect(context)};
    const ground=game.Combat.drawGroundFields;game.Combat.drawGroundFields=function(context){ground.call(this,context);held(context)};
    ready=true;if(spinOnly)time=.76;draw(time);requestAnimationFrame(tick);
  }
  function tick(now){if(last&&playing){const dt=Math.min(.05,(now-last)/1000)*+$('speed').value;if(spinOnly)spinAge=(spinAge+dt)%(TAU*3);else time=(time+dt)%2.2;}last=now;draw(time);requestAnimationFrame(tick)}
  init().catch(e=>{$('error').textContent='預覽載入失敗：'+e.message});
})();
