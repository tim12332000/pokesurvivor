/* Native pursuit demo and isolated cooldown-gap sustain comparison. */
(() => {
  const $=id=>document.getElementById(id),canvas=$('preview'),ctx=canvas.getContext('2d');
  const actorSources=new Set();
  let G,actor,targets=[],front=[],primary,behind,outside,elapsed=0,running=false,manual=false,last=0,observations=[],completion=null,framing=null,audioAudit=null,comparisonResult=null;
  const active=()=>G?.NarutoPursuit?.activeFor(actor);
  const api=window.LeePursuitPreview={ready:false,replay,step,render,compare,installAudioTrap,report:()=>{
    const f=active(),move=actor?.moves.find(m=>m.id==='naruto-lee-pursuit'),pose=actor?G.AnimationLab.stateFor(actor.anim):null;
    return {elapsed,running,observations,completion,phase:f?.phase,age:f?.age,attackAge:f?.attackAge,duration:f?.duration,
      hitIndex:f?.hitIndex,hits:f?.hits,position:actor?{x:actor.x,y:actor.y}:null,guard:actor?actor.invuln>0:false,
      animation:pose?{key:pose.key,frame:pose.frame,phase:pose.phase,state:pose.state}:null,
      skill:move?{level:move.lvl,damage:move.dmg,count:move.count,cooldown:move.cd,range:move.range,radius:move.radius,arc:move.arc,passive:move.passive}:null,
      slots:actor?.slots.map(group=>group.map(m=>m.id)),actorSources:[...actorSources],framing,comparison:comparisonResult,
      audio:audioAudit?{...audioAudit,enabled:$('sound').checked,track:G.Audio.track,storedAfter:$('game-source').contentWindow.localStorage.getItem('ps.audio')}:null};
  }};
  const pause=()=>{if(G.Game.state==='playing')G.Game.togglePause();G.UI.hide('scr-pause');};
  const resume=()=>{if(G.Game.state==='paused')G.Game.togglePause();};
  function installAudioTrap(win){
    win.G=win.G||{};
    Object.defineProperty(win.G,'Audio',{configurable:true,set(audio){
      Object.defineProperty(win.G,'Audio',{value:audio,writable:true,configurable:true,enumerable:true});
      const music=audio.music,sfx=audio.sfx;
      audioAudit={storedBefore:win.localStorage.getItem('ps.audio'),blockedMusicRequests:0,blockedSfxRequests:0,playedSfxRequests:0};
      audio.settings.muted=false;music(null);
      audio.music=()=>{audioAudit.blockedMusicRequests++;return music(null);};
      audio.sfx=(...args)=>{if(!$('sound').checked){audioAudit.blockedSfxRequests++;return;}audioAudit.playedSfxRequests++;return sfx(...args);};
      $('sound').onchange=()=>{if($('sound').checked)audio.unlock();};
    }});
  }
  function openArena(){
    pause();G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();G.FX.clear();G.Pickups.clear();G.NarutoClones?.clear();G.AnimationLab.clear();G.Weather.reset();
    G.World.collide=()=>{};G.World.isLiquid=()=>false;G.World.isFree=()=>true;G.World.isWall=()=>false;G.World.projectileBlock=()=>false;
    actor.x=actor.y=0;actor.level=12;actor.hp=actor.maxHp;actor.dead=actor.frozen=false;actor.flash=actor.invuln=actor.attackFace=0;actor.walking=false;
    actor.quantityPicks=actor.quantityBonus=0;actor.critChance=actor.percentHealthDamage=actor.lifestealRate=0;actor.anim.once=false;actor.anim.done=false;
    const main=G.Moves.instance('naruto-lotus',1);main.t=999;
    actor.moves=[main];actor.slots=[[main]];actor.bind={};actor.active=0;
    if($('gates').checked)actor.addMove('naruto-gates');
    actor.arrange();actor.setActive(0);G.Camera.x=G.Camera.y=0;G.Camera.shake=G.Camera._sx=G.Camera._sy=0;G.Camera.resize(380,300,1);
  }
  function learnPursuit(level){
    actor.addMove('naruto-lee-pursuit');
    Object.assign(actor.moves.find(m=>m.id==='naruto-lee-pursuit'),G.Moves.instance('naruto-lee-pursuit',level));
    actor.arrange();
  }
  function spawn(x,y,dex,id,boss=false){
    const enemy=new G.Enemy({dex,hp:10000000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
    enemy.types=['normal'];enemy.previewId=id;
    if(boss){enemy.boss=true;enemy.bossInit();enemy.ai.mode='close';enemy.ai.modeT=enemy.ai.cd=1000000;}
    G.EnemyMgr.add(enemy);return enemy;
  }
  function replay(options={}){
    if(!api.ready)return;
    manual=!!options.manual;running=false;openArena();learnPursuit(Number($('level').value));
    observations=[];elapsed=0;completion=null;
    const move=actor.moves.find(m=>m.id==='naruto-lee-pursuit');
    primary=spawn(140,0,19,'front-1');front=[primary,spawn(145,-25,16,'front-2'),spawn(145,25,21,'front-3')];
    const contactX=primary.x-move.radius*.65;
    outside=spawn(contactX+move.radius+55,0,19,'outside');targets=[...front,outside];G.EnemyMgr.rebuildGrid();
    actor.target=primary;actor.aim=0;actor.anim.dir=G.Sprites.dirFromAngle(0);
    resume();G.Combat.updateFields(.001);pause();
    if(!active())throw Error('疾速追身沒有進入原生追擊');
    // Add a rear fixture after native target lock, so nearest-target selection stays intact.
    behind=spawn(contactX-move.radius*.65,40,19,'behind');targets.push(behind);G.EnemyMgr.rebuildGrid();
    running=true;render();
  }
  function step(dt){
    if(!running)return render();
    resume();
    try{
      let remaining=Math.min(.1,Math.max(0,dt));
      while(remaining>1e-8){
        const chunk=Math.min(1/120,remaining),before=targets.map(e=>e.hp);
        actor.update(chunk);G.EnemyMgr.update(chunk,[actor]);G.EnemyMgr.rebuildGrid();
        G.Combat.updateFields(chunk);G.FX.update(chunk);elapsed+=chunk;remaining-=chunk;
        targets.forEach((enemy,index)=>{if(enemy.hp<before[index])observations.push({targetId:enemy.previewId,time:elapsed,loss:before[index]-enemy.hp,x:enemy.x,y:enemy.y});});
      }
    }finally{pause();}
    if(!active()&&elapsed>.05){
      const result=enemy=>({id:enemy.previewId,damage:enemy.maxHp-enemy.hp,hpChanges:observations.filter(hit=>hit.targetId===enemy.previewId).length,x:enemy.x,y:enemy.y});
      completion={front:front.map(result),behind:result(behind),outside:result(outside),travel:Math.hypot(actor.x,actor.y)};running=false;
    }
    render();
  }
  function render(){
    if(!G||!actor||!primary)return;
    const f=active(),scale=1.7,originX=canvas.width/(2*scale)-90,originY=canvas.height/scale-100;
    framing={scale,originX,originY,width:canvas.width,height:canvas.height};
    ctx.setTransform(1,0,0,1,0,0);ctx.fillStyle='#172b24';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.imageSmoothingEnabled=false;
    ctx.save();ctx.scale(scale,scale);ctx.translate(originX,originY);
    G.World.drawGround(ctx,{left:()=>-originX,top:()=>-originY,w:canvas.width/scale,h:canvas.height/scale});
    G.Combat.drawGroundFields(ctx);for(const enemy of targets)enemy.draw(ctx);
    const drawImage=ctx.drawImage;ctx.drawImage=function(image,...args){if(image.src)actorSources.add(image.src);return drawImage.call(this,image,...args);};
    try{actor.draw(ctx);}finally{ctx.drawImage=drawImage;}
    G.Combat.drawAirFields(ctx);G.FX.draw(ctx);ctx.restore();
    ctx.font='16px system-ui';ctx.fillStyle='#d6e8cb';
    for(const [enemy,label]of [[behind,'背後'],[outside,'範圍外']])if(enemy)ctx.fillText(label,(enemy.x+originX)*scale-20,(enemy.y+originY)*scale+24);
    $('status').textContent=running?`${f?.phase==='rush'?'疾速追近':`近身連打 ${f?.hitIndex||0}／${f?.hits||0}`} · ${elapsed.toFixed(2)} 秒`:
      completion?`連打完成 · 前方 ${completion.front.filter(e=>e.damage>0).length} 名受傷 · 背後／範圍外傷害 ${completion.behind.damage}／${completion.outside.damage}`:'準備完成';
  }
  async function newOwner(){
    G.Game.toUI();await G.Flow.play();actor=G.Game.player;pause();return actor;
  }
  function nativeTick(dt,time){
    actor.update(dt);G.EnemyMgr.update(dt,[actor]);G.EnemyMgr.rebuildGrid();
    G.Combat.tick(dt,actor,time);G.Projectiles.update(dt,actor,G.EnemyMgr.all());G.Combat.resolve(dt,actor,time);G.Combat.updateFields(dt);G.FX.update(dt);
  }
  async function sustainCase(enabled,seconds,level){
    const owner=await newOwner();openArena();
    const boss=spawn(35,0,19,'sustain-boss',true);G.EnemyMgr.rebuildGrid();actor.target=boss;actor.aim=0;
    const stats={atk:actor.atk,spd:actor.spd,cdMul:actor.cdMul,maxHp:actor.maxHp,quantity:actor.quantityPicks,crit:actor.critChance};
    const main=actor.moves.find(m=>m.id==='naruto-lotus'),dt=1/120,warmup=1;
    resume();try{for(let tick=0;tick<120;tick++)nativeTick(dt,(tick+1)*dt);}finally{pause();}
    const warmupDamage=boss.maxHp-boss.hp;
    if(enabled)learnPursuit(level);
    const hp=boss.hp,dealt=actor.dmgDealt,points=[],start={player:{x:actor.x,y:actor.y},boss:{x:boss.x,y:boss.y}};
    resume();try{
      for(let tick=0;tick<Math.round(seconds/dt);tick++){
        nativeTick(dt,warmup+(tick+1)*dt);
        if((tick+1)%120===0)points.push({seconds:(tick+1)*dt,damage:hp-boss.hp});
      }
    }finally{pause();}
    return {enabled,level,seconds,warmup,warmupDamage,stats,mainCooldown:main.cd,mainCooldownRemaining:main.t,
      measuredHpLoss:hp-boss.hp,measuredDamageDealt:actor.dmgDealt-dealt,dps:(hp-boss.hp)/seconds,
      start,end:{player:{x:actor.x,y:actor.y},boss:{x:boss.x,y:boss.y}},points,owner};
  }
  async function compare(seconds=20,restoreManual=false){
    if(!api.ready)return;
    running=false;pause();const controls=['replay','compare','level','gates'];for(const id of controls)$(id).disabled=true;
    $('comparison').textContent='正在比較相同條件的持續輸出…';
    try{
      const level=Number($('level').value),without=await sustainCase(false,seconds,level),withSkill=await sustainCase(true,seconds,level);
      const freshOwners=without.owner!==withSkill.owner;delete without.owner;delete withSkill.owner;
      comparisonResult={level,seconds,without,withSkill,freshOwners,ratio:withSkill.measuredHpLoss/without.measuredHpLoss,
        methodology:'Fresh native owners; identical stats and stationary normal-type boss at35world. Both conditions warm up native fallback tackle for1s without pursuit; only treatment then learns pursuit. Main Lotus starts t999 inboth and is not cast, isolating cooldown-gap sustain rather than full-cycle build DPS. Native player/enemy/combat updates and HP losses; no hurt or damage/scheduler replacement.'};
      $('comparison').textContent=`${seconds}秒：未學 ${without.measuredHpLoss.toLocaleString()} 傷害 → 學會 ${withSkill.measuredHpLoss.toLocaleString()} 傷害（${comparisonResult.ratio.toFixed(2)}倍）`;
      await newOwner();replay({manual:restoreManual});return comparisonResult;
    }finally{for(const id of controls)$(id).disabled=false;}
  }
  function frame(now){const dt=last?Math.min(.05,(now-last)/1000):0;last=now;if(api.ready&&running&&!manual)step(dt*Number($('speed').value));requestAnimationFrame(frame);}
  async function boot(){
    const source=$('game-source'),url=new URL(source.dataset.src,location.href),response=await fetch(url);
    if(!response.ok)throw Error('無法載入遊戲');
    const html=(await response.text()).replace('<head>',`<head><script>history.replaceState(null,'',${JSON.stringify(url.href)});parent.LeePursuitPreview.installAudioTrap(window)</script>`)
      .replace('<base href="../">',`<base href="${new URL('../',url).href}">`);
    source.contentDocument.open();source.contentDocument.write(html);source.contentDocument.close();
    while(!source.contentWindow?.G?.NarutoAssets||!source.contentDocument?.querySelector('#boot')?.classList.contains('hidden'))await new Promise(r=>setTimeout(r,50));
    G=source.contentWindow.G;if(!G.NarutoPursuit)throw Error('疾速追身尚未載入');
    const tap=source.contentDocument.querySelector('#tap-start');if(tap&&!tap.classList.contains('hidden'))tap.click();
    G.Naruto.choose(30006);await G.NarutoAssets.ensure(30006);await G.Flow.play();actor=G.Game.player;pause();await G.Sprites.preload([19,16,21]);
    api.ready=true;for(const id of ['replay','compare'])$(id).disabled=false;$('replay').textContent='重播疾速追身';
    $('replay').onclick=()=>replay();$('level').onchange=()=>replay();$('gates').onchange=()=>replay();
    $('compare').onclick=()=>compare().catch(error=>{$('comparison').textContent='比較失敗：'+error.message;});
    replay();requestAnimationFrame(frame);
  }
  boot().catch(error=>{$('status').textContent='預覽載入失敗：'+error.message;console.error(error);});
})();
