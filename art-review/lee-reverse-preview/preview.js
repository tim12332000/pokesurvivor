/* Review-only arena. All action phases, actor art and damage run in the real game. */
(() => {
  const $=id=>document.getElementById(id),canvas=$('preview'),ctx=canvas.getContext('2d');
  const phases={approach:'繃帶拉近',windup:'蓄勢',lift:'挑空',combo:'空中連踢',descent:'最後重摔',slam:'落地震擊',recovery:'收招'};
  let G,actor,targets=[],group=[],primary,splash,outside,elapsed=0,running=false,manual=false,last=0,ledger=[],completion=null,framing=null,audioAudit=null;
  const api=window.LeeReversePreview={ready:false,replay,step,render,installAudioTrap,report:()=>({elapsed,running,ledger,completion,
    phase:G?.NarutoLee.activeFor(actor)?.phase,ticks:G?.NarutoLee.activeFor(actor)?.ticks,
    actorPose:G?.NarutoLee.presentationFor(actor),victimPose:G?.NarutoLee.victimPresentationFor(primary),framing,
    audio:audioAudit?{...audioAudit,enabled:$('sound').checked,track:G.Audio.track,storedAfter:$('game-source').contentWindow.localStorage.getItem('ps.audio')}:null})};
  const pause=()=>{if(G.Game.state==='playing')G.Game.togglePause();G.UI.hide('scr-pause');};
  const resume=()=>{if(G.Game.state==='paused')G.Game.togglePause();};
  function installAudioTrap(win){
    win.G=win.G||{};
    Object.defineProperty(win.G,'Audio',{configurable:true,set(audio){
      Object.defineProperty(win.G,'Audio',{value:audio,writable:true,configurable:true,enumerable:true});
      const originalMusic=audio.music,originalSfx=audio.sfx;
      audioAudit={storedBefore:win.localStorage.getItem('ps.audio'),blockedMusicRequests:0,blockedSfxRequests:0,playedSfxRequests:0};
      // This iframe has its own live settings object; the checkbox owns its mute.
      audio.settings.muted=false;
      originalMusic(null);
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
    const hurt=e.hurt;e.hurt=function(...args){ledger.push({targetId:this.previewId,primary:this===primary,phase:G.NarutoLee.activeFor(actor)?.phase,damage:args[0]});return hurt.apply(this,args);};
    G.EnemyMgr.add(e);return e;
  }
  function replay(options={}){
    if(!api.ready)return;
    manual=!!options.manual;
    pause();G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();
    G.NarutoClones?.clear();G.AnimationLab.clear();G.Pickups.clear();
    G.World.collide=()=>{};G.World.isLiquid=()=>false;G.World.isFree=()=>true;
    G.World.isWall=()=>false;G.World.projectileBlock=()=>false;
    actor.x=actor.y=0;actor.dead=false;actor.hp=actor.maxHp;actor.frozen=false;actor.flash=actor.invuln=0;
    actor.attackFace=0;actor.walking=false;actor.quantityPicks=actor.quantityBonus=0;
    actor.critChance=actor.percentHealthDamage=actor.lifestealRate=0;actor.anim.once=false;actor.anim.done=false;
    const level=Number($('level').value),move=G.Moves.instance('naruto-reverse-lotus',level);
    actor.moves=[move];actor.slots=[[move]];actor.active=0;actor.bind={};
    if($('gates').checked)actor.addMove('naruto-gates');
    actor.level=12;actor.arrange();actor.setActive(0);move.t=0;
    ledger=[];elapsed=0;completion=null;
    primary=spawn(65,0,19,'group-1');
    group=[primary,spawn(65,-55,16,'group-2'),spawn(90,45,21,'group-3'),spawn(115,-20,23,'group-4'),spawn(120,40,27,'group-5')];
    splash=spawn(130,0,19,'splash');outside=spawn(65+move.radius+55,50,19,'outside');
    targets=[...group,splash,outside];G.EnemyMgr.rebuildGrid();
    actor.target=primary;actor.aim=0;actor.anim.dir=G.Sprites.dirFromAngle(0);
    G.Camera.x=G.Camera.y=0;G.Camera.resize(380,300,1);
    running=true;resume();G.Combat.tick(.001,actor,0);pause();render();
  }
  function step(dt){
    if(!running)return render();
    resume();
    try{
      let remaining=Math.min(.1,Math.max(0,dt));
      while(remaining>1e-8){
        const chunk=Math.min(1/120,remaining);
        G.Combat.updateFields(chunk);actor.anim.update(chunk);
        for(const enemy of targets)enemy.update(chunk,actor);
        G.FX.update(chunk);elapsed+=chunk;remaining-=chunk;
      }
    }finally{pause();}
    if(!G.NarutoLee.activeFor(actor)&&elapsed>.1){
      const result=e=>({id:e.previewId,damage:100000-e.hp,hits:ledger.filter(h=>h.targetId===e.previewId).length});
      running=false;completion={group:group.map(result),splash:result(splash),outside:100000-outside.hp,hits:ledger.filter(h=>h.primary).length};
    }
    render();
  }
  function render(){
    if(!G||!actor)return;
    const f=G.NarutoLee.activeFor(actor);
    const radius=actor.moves.find(m=>m.id==='naruto-reverse-lotus').radius;
    const scale=Math.min(1.3,(canvas.width-64)/620,(canvas.height-60)/(360+radius+20));
    const originX=canvas.width/(2*scale)-primary.x,originY=(canvas.height/scale+390-radius)/2;
    framing={scale,originX,originY,width:canvas.width,height:canvas.height};
    ctx.setTransform(1,0,0,1,0,0);ctx.fillStyle='#172b24';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.imageSmoothingEnabled=false;
    ctx.save();ctx.scale(scale,scale);ctx.translate(originX,originY);
    G.World.drawGround(ctx,{left:()=>-originX,top:()=>-originY,w:canvas.width/scale,h:canvas.height/scale});
    // Ground marker uses the actual landing radius; it does not deal damage.
    if(f){ctx.save();ctx.strokeStyle='#9fbf87';ctx.globalAlpha=.3;ctx.setLineDash([3,5]);ctx.beginPath();ctx.arc(primary.x,primary.y,f.move.radius,0,Math.PI*2);ctx.stroke();ctx.restore();}
    G.Combat.drawGroundFields(ctx);
    for(const e of targets)e.draw(ctx);
    actor.draw(ctx);G.Combat.drawAirFields(ctx);G.FX.draw(ctx);ctx.restore();
    ctx.font='16px system-ui';ctx.fillStyle='#d6e8cb';ctx.fillText('範圍外',Math.min(canvas.width-70,((outside?.x||0)+originX)*scale-24),Math.min(canvas.height-14,((outside?.y||0)+originY)*scale+24));
    const phase=f?.phase;
    $('status').textContent=running?`${phases[phase]||'準備'} · ${elapsed.toFixed(2)} 秒${phase==='combo'?` · ${f.ticks}／${f.comboHits} 次連踢`:''}`:
      completion?`演出完成 · ${elapsed.toFixed(2)} 秒 · ${completion.group.length} 名目標各 ${completion.hits} 次命中 · 範圍外傷害 ${completion.outside}`:'準備完成';
  }
  function frame(now){
    const dt=last?Math.min(.05,(now-last)/1000):0;last=now;
    if(api.ready&&running&&!manual)step(dt*Number($('speed').value));
    requestAnimationFrame(frame);
  }
  async function boot(){
    const source=$('game-source');
    const url=new URL(source.dataset.src,location.href),response=await fetch(url);
    if(!response.ok)throw Error('無法載入遊戲');
    const html=(await response.text()).replace('<head>',`<head><script>history.replaceState(null,'',${JSON.stringify(url.href)});parent.LeeReversePreview.installAudioTrap(window)</script>`)
      .replace('<base href="../">',`<base href="${new URL('../',url).href}">`);
    // Install the preview-only audio gate before the native boot can unlock sound.
    source.contentDocument.open();source.contentDocument.write(html);source.contentDocument.close();
    while(!source.contentWindow?.G?.NarutoAssets||!source.contentDocument?.querySelector('#boot')?.classList.contains('hidden'))await new Promise(r=>setTimeout(r,50));
    G=source.contentWindow.G;
    const tap=source.contentDocument.querySelector('#tap-start');if(tap&&!tap.classList.contains('hidden'))tap.click();
    G.Naruto.choose(30006);await G.NarutoAssets.ensure(30006);await G.Flow.play();
    while(!G.Game.player)await new Promise(r=>setTimeout(r,20));
    actor=G.Game.player;pause();await G.Sprites.preload([19,16,21,23,27]);
    api.ready=true;$('replay').disabled=false;$('replay').textContent='重播裏蓮華';
    $('replay').onclick=()=>replay();$('level').onchange=()=>replay();$('gates').onchange=()=>replay();
    replay();requestAnimationFrame(frame);
  }
  boot().catch(error=>{$('status').textContent='預覽載入失敗：'+error.message;console.error(error);});
})();
