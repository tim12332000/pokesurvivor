/* Isolated audit plus switchable source-frame/hand-origin throw prototype. */
(() => {
  const installed=new WeakSet();
  function install(G,{controls=true}={}){
    if(installed.has(G))return;installed.add(G);
    let clock=0;const casts=new Map(),events=[];
    const toggle=document.createElement('label'),checkbox=document.createElement('input');checkbox.type='checkbox';checkbox.id='continuity';checkbox.checked=true;
    toggle.append(checkbox,document.createTextNode('實驗：投擲出手銜接'));if(controls)document.querySelector('header')?.append(toggle);
    checkbox.onchange=()=>{const frame=document.querySelector('#game');frame.focus();frame.contentWindow.focus();};
    const valid=c=>c&&c.world===G.World&&c.owner===G.Game.player&&!c.owner.dead&&c.owner.hp>0;
    const selected=p=>p.activeGroup().some(m=>m.id==='naruto-fuma-shuriken');
    const active=p=>{const c=casts.get(p);return !!(checkbox.checked&&valid(c)&&c.id==='naruto-fuma-shuriken'&&selected(p)&&clock-c.time<=c.duration+.14&&!G.NarutoChidori?.active&&!G.NarutoFireball?.active);};
    const frames=[{rect:[100,97,29,50],anchor:[14.5,50],hand:[24,28]},{rect:[140,104,50,43],anchor:[25,43],hand:[47,13]},
      {rect:[196,107,50,40],anchor:[25,40],hand:[47,11]},{rect:[252,108,48,39],anchor:[24,39],hand:[45,14]}];
    const pose=c=>frames[c.released?3:Math.min(2,Math.floor(Math.max(0,(clock-c.time)/c.duration)*3))];
    const hand=(p,c,frame=frames[3])=>{const redrawn=G.AnimationLab?.handFor?.(p);if(redrawn)return redrawn;const k=64*p.anim.scale/44,side=Math.cos(c.aim)>=0?1:-1;return {x:p.x+(frame.hand[0]-frame.anchor[0])*k*side,y:p.y+(frame.hand[1]-frame.anchor[1])*k+G.LIFT};};
    // Replace only the generic center-of-body charge ornament, not flying shots.
    const air=G.Combat.drawAirFields,fx=G.VFX.draw;let drawingAir=false;
    G.Combat.drawAirFields=function(...args){const previous=drawingAir;drawingAir=true;try{return air.apply(this,args);}finally{drawingAir=previous;}};
    G.VFX.draw=function(ctx,shape,...args){const c=casts.get(G.Game.player);if(drawingAir&&checkbox.checked&&valid(c)&&c.id==='naruto-fuma-shuriken'&&!c.released&&shape==='naruto-fuma-shuriken')return;return fx.call(this,ctx,shape,...args);};
    const render=G.Sprites.Animator.prototype.draw;
    G.Sprites.Animator.prototype.draw=function(ctx,x,y,opts={}){
      const p=G.Game.player;if(!p||p.anim!==this||!active(p))return render.apply(this,arguments);
      const c=casts.get(p),f=pose(c),r=G.Naruto.records.get(30002),k=64*this.scale/44,side=Math.cos(c.aim)>=0?1:-1;
      if(!c.released){const h=hand(p,c,f);G.VFX.draw(ctx,'naruto-fuma-shuriken','naruto-fuma-steel',h.x,h.y-G.LIFT,{scale:c.move.digiVis?.projScale||.9,angle:0,frame:0});}
      ctx.save();ctx.translate(Math.round(x),Math.round(y));ctx.scale(side*k,k);ctx.imageSmoothingEnabled=false;ctx.globalAlpha*=opts.alpha??1;
      ctx.drawImage(opts.flash?G.Sprites.white(r.image):r.image,...f.rect,-f.anchor[0],-f.anchor[1],f.rect[2],f.rect[3]);ctx.restore();
    };
    const cast=G.DigimonSkills.cast,playerCast=G.Player.prototype.cast,spawn=G.Projectiles.spawn,update=G.Combat.updateFields,clear=G.Combat.clearFields,setActive=G.Player.prototype.setActive;
    const recordCast=(owner,move)=>{if(owner===G.Game.player&&owner.dex===30002&&['naruto-fireball','naruto-fuma-shuriken'].includes(move.id))casts.set(owner,{id:move.id,owner,move,time:clock,aim:owner.aim,world:G.World,duration:move.charge||.2,released:false});};
    // The real auto-cast loop calls a lexical skill function, not the exported API.
    G.Player.prototype.cast=function(move){
      recordCast(this,move);const result=playerCast.apply(this,arguments);
      if(checkbox.checked&&this===G.Game.player&&this.dex===30002&&move.id==='naruto-fuma-shuriken'){
        const timing=G.Sprites.animMeta(this.dex,'Attack'),seconds=timing.d.reduce((a,b)=>a+b,0)/60;
        this.anim.play('Attack',{speed:seconds/((move.charge||.2)+.14)});
      }
      return result;
    };
    G.Combat.clearFields=function(owner){const result=clear.apply(this,arguments);if(owner)casts.delete(owner);else casts.clear();return result;};
    G.Player.prototype.setActive=function(...args){const result=setActive.apply(this,args),c=casts.get(this);if(checkbox.checked&&valid(c)&&c.id==='naruto-fuma-shuriken'&&!c.released&&!selected(this))c.cancelledBeforeRelease=true;return result;};
    G.Combat.updateFields=function(dt){clock+=Math.max(0,dt||0);for(const [owner,c] of casts)if(!valid(c))casts.delete(owner);return update.apply(this,arguments);};
    G.DigimonSkills.cast=function(owner,move){
      const result=cast.apply(this,arguments);
      if(result)recordCast(owner,move);
      return result;
    };
    G.Projectiles.spawn=function(options){
      const c=casts.get(options.owner);
      const shape=options.vis?.proj;
      if(!valid(c)||!['naruto-great-fireball','naruto-fuma-shuriken'].includes(shape))return spawn.apply(this,arguments);
      const owner=options.owner,fire=shape==='naruto-great-fireball';
      let expected;
      if(fire){const mouth=G.NarutoFireball.origin(owner,c.aim);expected={x:mouth.x+Math.cos(c.aim)*3,y:mouth.y+Math.sin(c.aim)*3};}
      else{
        expected=hand(owner,c);
      }
      if(!fire&&checkbox.checked&&(c.cancelledBeforeRelease||!selected(owner))){
        const projectile=spawn.apply(this,arguments);G.Projectiles.remove(projectile);
        events.push({skill:c.id,time:clock,cancelled:true,reason:'switched-before-release'});return projectile;
      }
      const prototype=!fire&&checkbox.checked&&active(owner);
      if(prototype){
        c.released=true;
        const distance=Math.hypot(expected.x-owner.x,expected.y-owner.y);
        for(let step=4;step<distance+4;step+=4){const t=Math.min(1,step/distance);
          if(G.World.projectileBlock(owner.x+(expected.x-owner.x)*t,owner.y+(expected.y-owner.y)*t,1)){
            const projectile=spawn.apply(this,arguments);G.Projectiles.remove(projectile);
            events.push({skill:c.id,time:clock,cancelled:true,reason:'blocked-hand-origin'});return projectile;
          }
        }
        options={...options,x:expected.x,y:expected.y};
      }
      const projectile=spawn.call(this,options);
      const actorPose=prototype?frames[3]:G.Naruto.frameFor(G.Naruto.records.get(owner.dex),owner.anim.cur,owner.anim.dir,owner.anim.frame);
      const event={skill:c.id,time:clock,castAge:clock-c.time,actorAnimation:prototype?'Attack':owner.anim.cur,sourceFrame:actorPose.rect,
        spawn:{x:options.x,y:options.y},expected,originError:Math.hypot(options.x-expected.x,options.y-expected.y),
        phase:fire?(G.NarutoFireball.active?.t>=G.NarutoFireball.config.sealDuration?'breath':'seal'):prototype?'release':'generic-cast',mode:prototype?'prototype':'audit-only'};
      events.push(event);if(events.length>100)events.shift();
      const host=document.getElementById('cast-audit');
      if(host)host.textContent=`${fire?'豪火球':'風魔手裏劍'} · 出手 ${(event.castAge*1000).toFixed(0)}ms · ${event.actorAnimation} · 發射點距參考 ${event.originError.toFixed(1)}px · ${event.mode}`;
      return projectile;
    };
    G.CastContinuityLab={events,active,clear:()=>{casts.clear();events.length=0;},get enabled(){return checkbox.checked;}};
    if(controls&&!document.getElementById('cast-audit')){
      const panel=document.createElement('aside');panel.id='cast-audit';panel.textContent='施放連貫性紀錄：選用豪火球或風魔手裏劍，等待實際出手。';
      panel.style.cssText='flex:0 0 auto;padding:6px 12px;background:#102034;color:#ffcf7c;border-top:1px solid #607c99;font:11px system-ui;pointer-events:none';
      document.querySelector('#game').before(panel);
    }
  }
  window.CastContinuityLab={install};
})();
