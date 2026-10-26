/* Review arena: native casts, collision, damage and animation only. */
(() => {
  const $=id=>document.getElementById(id),canvas=$('preview'),ctx=canvas.getContext('2d');
  const phases={step:'踏入',rise:'起跳',spread:'展腿',turn:'旋身',strike:'旋踢命中',descend:'下降',recovery:'落地收勢'};
  let G,actor,targets=[],front=[],primary,behind,outside,elapsed=0,running=false,manual=false,last=0,ledger=[],completion=null,framing=null,audioAudit=null;
  const active=()=>G?.DigimonSkills?.whirlwindFor?.(actor);
  const api=window.LeeWhirlwindPreview={ready:false,replay,step,render,installAudioTrap,report:()=>{
    const f=active(),m=actor?.moves[0],pose=actor?G.AnimationLab.stateFor(actor.anim):null;
    return {elapsed,running,ledger,completion,phase:f?.phase,frame:f?.frame,fieldTime:f?.t,life:f?.life,
      animation:pose?{key:pose.key,frame:pose.frame,state:pose.state,phase:pose.phase}:null,
      visualLift:f?.visualLift,position:actor?{x:actor.x,y:actor.y}:null,invulnerable:actor?actor.invuln>0:false,
      skill:m?{level:m.lvl,damage:m.dmg,cooldown:m.cd,range:m.range,radius:m.radius,arc:m.arc,knock:m.knock,mode:m.digiMode}:null,
      framing,camera:G?{x:G.Camera.x,y:G.Camera.y,scale:G.Camera.scale,sx:G.Camera._sx,sy:G.Camera._sy}:null,
      audio:audioAudit?{...audioAudit,enabled:$('sound').checked,track:G.Audio.track,storedAfter:$('game-source').contentWindow.localStorage.getItem('ps.audio')}:null};
  }};
  const pause=()=>{if(G.Game.state==='playing')G.Game.togglePause();G.UI.hide('scr-pause');};
  const resume=()=>{if(G.Game.state==='paused')G.Game.togglePause();};
  function installAudioTrap(win){
    win.G=win.G||{};
    Object.defineProperty(win.G,'Audio',{configurable:true,set(audio){
      Object.defineProperty(win.G,'Audio',{value:audio,writable:true,configurable:true,enumerable:true});
      const originalMusic=audio.music,originalSfx=audio.sfx;
      audioAudit={storedBefore:win.localStorage.getItem('ps.audio'),blockedMusicRequests:0,blockedSfxRequests:0,playedSfxRequests:0};
      audio.settings.muted=false;originalMusic(null);
      audio.music=()=>{audioAudit.blockedMusicRequests++;return originalMusic(null);};
      audio.sfx=(...args)=>{
        if(!$('sound').checked){audioAudit.blockedSfxRequests++;return;}
        audioAudit.playedSfxRequests++;return originalSfx(...args);
      };
      $('sound').onchange=()=>{if($('sound').checked)audio.unlock();};
    }});
  }
  function spawn(x,y,dex,id){
    const e=new G.Enemy({dex,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
    e.types=['normal'];e.previewId=id;
    const hurt=e.hurt;e.hurt=function(...args){const f=active();ledger.push({targetId:this.previewId,phase:f?.phase,time:f?.t,damage:args[0],x:this.x,y:this.y});return hurt.apply(this,args);};
    G.EnemyMgr.add(e);return e;
  }
  function replay(options={}){
    if(!api.ready)return;
    manual=!!options.manual;pause();G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();G.Pickups.clear();
    G.NarutoClones?.clear();G.AnimationLab.clear();
    G.World.collide=()=>{};G.World.isLiquid=()=>false;G.World.isFree=()=>true;G.World.isWall=()=>false;G.World.projectileBlock=()=>false;
    actor.x=actor.y=0;actor.dead=actor.frozen=false;actor.hp=actor.maxHp;actor.flash=actor.invuln=actor.attackFace=0;actor.walking=false;
    actor.quantityPicks=actor.quantityBonus=0;actor.critChance=actor.percentHealthDamage=actor.lifestealRate=0;actor.anim.once=false;actor.anim.done=false;
    const move=G.Moves.instance('naruto-lee',Number($('level').value));
    actor.moves=[move];actor.slots=[[move]];actor.active=0;actor.bind={};actor.level=12;
    if($('gates').checked)actor.addMove('naruto-gates');
    actor.arrange();actor.setActive(0);move.t=0;ledger=[];elapsed=0;completion=null;
    primary=spawn(70,0,19,'front-1');front=[primary,spawn(58,-25,16,'front-2'),spawn(58,25,21,'front-3')];
    behind=spawn(-40,0,19,'behind');outside=spawn(20+move.radius+35,0,19,'outside');targets=[...front,behind,outside];
    G.EnemyMgr.rebuildGrid();actor.target=primary;actor.aim=0;actor.anim.dir=G.Sprites.dirFromAngle(0);
    G.Camera.x=G.Camera.y=0;G.Camera.shake=G.Camera._sx=G.Camera._sy=0;G.Camera.resize(380,300,1);
    running=true;resume();G.Combat.tick(.001,actor,0);pause();
    if(!active())throw Error('木葉旋風沒有進入原生演出');
    render();
  }
  function step(dt){
    if(!running)return render();
    resume();
    try{
      let remaining=Math.min(.1,Math.max(0,dt));
      while(remaining>1e-8){
        const chunk=Math.min(1/120,remaining);G.Combat.updateFields(chunk);actor.anim.update(chunk);
        for(const enemy of targets)enemy.update(chunk,actor);
        G.EnemyMgr.rebuildGrid();G.FX.update(chunk);elapsed+=chunk;remaining-=chunk;
      }
    }finally{pause();}
    if(!active()&&elapsed>.1){
      const result=e=>({id:e.previewId,damage:100000-e.hp,hits:ledger.filter(h=>h.targetId===e.previewId).length,x:e.x,y:e.y});
      running=false;completion={front:front.map(result),behind:result(behind),outside:result(outside),stepDistance:Math.hypot(actor.x,actor.y)};
    }
    render();
  }
  function render(){
    if(!G||!actor)return;
    const f=active(),scale=2.2,originX=canvas.width/(2*scale)-20,originY=canvas.height/scale-actor.moves[0].radius-24;
    framing={scale,originX,originY,width:canvas.width,height:canvas.height};
    ctx.setTransform(1,0,0,1,0,0);ctx.fillStyle='#172b24';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.imageSmoothingEnabled=false;
    ctx.save();ctx.scale(scale,scale);ctx.translate(originX,originY);
    G.World.drawGround(ctx,{left:()=>-originX,top:()=>-originY,w:canvas.width/scale,h:canvas.height/scale});
    G.Combat.drawGroundFields(ctx);for(const e of targets)e.draw(ctx);actor.draw(ctx);G.Combat.drawAirFields(ctx);G.FX.draw(ctx);ctx.restore();
    ctx.font='16px system-ui';ctx.fillStyle='#d6e8cb';
    for(const [enemy,label]of [[behind,'背後'],[outside,'範圍外']])ctx.fillText(label,(enemy.x+originX)*scale-20,(enemy.y+originY)*scale+24);
    $('status').textContent=running?`${phases[f?.phase]||'準備'} · ${elapsed.toFixed(2)} 秒`:
      completion?`演出完成 · ${elapsed.toFixed(2)} 秒 · 前方 ${completion.front.filter(e=>e.hits>0).length} 名命中 · 背後／範圍外傷害 ${completion.behind.damage}／${completion.outside.damage}`:'準備完成';
  }
  function frame(now){
    const dt=last?Math.min(.05,(now-last)/1000):0;last=now;
    if(api.ready&&running&&!manual)step(dt*Number($('speed').value));
    requestAnimationFrame(frame);
  }
  async function boot(){
    const source=$('game-source'),url=new URL(source.dataset.src,location.href),response=await fetch(url);
    if(!response.ok)throw Error('無法載入遊戲');
    const html=(await response.text()).replace('<head>',`<head><script>history.replaceState(null,'',${JSON.stringify(url.href)});parent.LeeWhirlwindPreview.installAudioTrap(window)</script>`)
      .replace('<base href="../">',`<base href="${new URL('../',url).href}">`);
    source.contentDocument.open();source.contentDocument.write(html);source.contentDocument.close();
    while(!source.contentWindow?.G?.NarutoAssets||!source.contentDocument?.querySelector('#boot')?.classList.contains('hidden'))await new Promise(r=>setTimeout(r,50));
    G=source.contentWindow.G;if(!G.DigimonSkills?.whirlwindFor)throw Error('木葉旋風演出尚未載入');
    const tap=source.contentDocument.querySelector('#tap-start');if(tap&&!tap.classList.contains('hidden'))tap.click();
    G.Naruto.choose(30006);await G.NarutoAssets.ensure(30006);await G.Flow.play();
    while(!G.Game.player)await new Promise(r=>setTimeout(r,20));
    actor=G.Game.player;pause();await G.Sprites.preload([19,16,21]);
    api.ready=true;$('replay').disabled=false;$('replay').textContent='重播木葉旋風';
    $('replay').onclick=()=>replay();$('level').onchange=()=>replay();$('gates').onchange=()=>replay();
    replay();requestAnimationFrame(frame);
  }
  boot().catch(error=>{$('status').textContent='預覽載入失敗：'+error.message;console.error(error);});
})();
