/* The one-tail buff selects our redrawn animation family, including baked chakra. */
(() => {
  'use strict';
  const base=new URL('./',document.currentScript.src),installed=new WeakSet();
  let metadata,image,pending;
  function load(){
    if(pending)return pending;
    pending=(async()=>{
      const response=await fetch(new URL('kyuubi-frames.json',base));
      if(!response.ok)throw Error('九尾動作資料載入失敗');
      metadata=await response.json();
      const source=new Image();source.src=new URL(metadata.source,base).href;await source.decode();
      image=document.createElement('canvas');image.width=source.width;image.height=source.height;
      image.dataset.source=source.src;
      const ctx=image.getContext('2d',{willReadFrequently:true});ctx.drawImage(source,0,0);
      return window.KyuubiForm;
    })().catch(error=>{pending=null;throw error;});
    return pending;
  }
  function install(G,{enabled=()=>true}={}){
    if(installed.has(G))return G.KyuubiForm;
    installed.add(G);
    const effect=owner=>G.NarutoSupport?.effects.find(f=>f.owner===owner&&f.world===G.World&&f.mode==='nine-tails-cloak'&&f.age<f.ttl);
    const active=owner=>!!(image&&enabled()&&owner===G.Game.player&&owner?.dex===30001&&!owner.dead&&owner.hp>0&&effect(owner));
    function poseFor(animator){
      const owner=G.Game.player;
      if(owner?.anim!==animator||!active(owner))return null;
      const action=G.AnimationLab.stateFor(animator),buff=effect(owner);
      let animation='idle',age=action.age;
      if(action.state==='hurt')animation='hurt';
      else if(action.state==='skill'){
        if(action.id==='naruto-naruto')animation=action.phase==='windup'?'rasenganCharge':action.phase==='release'?'rasenganDash':'rasenganRecover';
        else if(['naruto-kunai','naruto-shuriken','naruto-rasenshuriken'].includes(action.id))animation='throw';
        else animation='activation';
      }else if(buff.age<.22){animation='activation';age=buff.age;}
      else if(buff.pulseFlash>0){animation='attack';age=.18-buff.pulseFlash;}
      else if(owner.walking||action.state==='movement')animation='run';
      const sequence=metadata.animations[animation];
      let index=Math.floor(Math.max(0,age)*sequence.fps);
      if(animation==='rasenganCharge')index=Math.floor(Math.min(.999,Math.max(0,age)/.12)*sequence.frames.length);
      if(animation==='rasenganDash')index=Math.floor(Math.max(0,age-.12)*sequence.fps);
      if(animation==='rasenganRecover')index=Math.floor(Math.max(0,age-.21)*sequence.fps);
      if(animation==='attack')index=Math.floor(Math.min(.999,Math.max(0,age)/.18)*sequence.frames.length);
      index=sequence.loop?index%sequence.frames.length:Math.min(index,sequence.frames.length-1);
      const frame=sequence.frames[index],direction=action.direction;
      const mirror=direction==='left'||(direction!=='right'&&Math.cos(owner.aim||0)<0);
      return {key:'naruto-one-tail',animation,frame:index,rect:frame.rect,anchor:frame.anchor,mirror,direction};
    }
    const draw=G.Sprites.Animator.prototype.draw;
    G.Sprites.Animator.prototype.draw=function(ctx,x,y,options={}){
      const pose=poseFor(this);
      if(!pose)return draw.apply(this,arguments);
      const scale=64*(this.scale||1)/metadata.bodyHeight,[sx,sy,w,h]=pose.rect;
      ctx.save();ctx.translate(x,y);ctx.scale((pose.mirror?-1:1)*scale,scale);ctx.imageSmoothingEnabled=false;
      ctx.globalAlpha*=options.alpha??1;
      ctx.drawImage(options.flash?G.Sprites.white(image):image,sx,sy,w,h,-pose.anchor[0],-pose.anchor[1],w,h);
      ctx.restore();
      const counters=G.AnimationLab.counters;counters.candidate++;
      counters.byState[actionState(pose)]=(counters.byState[actionState(pose)]||0)+1;
    };
    const cloak=G.NarutoCloakVFX.draw;
    G.NarutoCloakVFX.draw=function(ctx,f,ground){if(!active(f.owner))return cloak.apply(this,arguments);};
    G.KyuubiForm={active,poseFor,get image(){return image;},get metadata(){return metadata;}};
    return G.KyuubiForm;
  }
  function actionState(pose){return pose.animation==='idle'?'idle':pose.animation==='run'?'movement':pose.animation==='hurt'?'hurt':'skill';}
  window.KyuubiForm={load,install,get image(){return image;},get metadata(){return metadata;}};
})();
