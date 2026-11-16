/* The one-tail buff selects our redrawn animation family, including baked chakra. */
(() => {
  'use strict';
  const script=new URL(document.currentScript.src),base=new URL('./',script),installed=new WeakSet();
  const version=script.searchParams.get('v')||'one-tail-directions-v1';
  const assetURL=path=>{const url=new URL(path,base);url.searchParams.set('v',version);return url;};
  let metadata,image,directionalImage,pending;
  function load(){
    if(pending)return pending;
    pending=(async()=>{
      const response=await fetch(assetURL('kyuubi-frames.json'),{cache:'no-cache'});
      if(!response.ok)throw Error('九尾動作資料載入失敗');
      metadata=await response.json();
      async function loadAtlas(path){
        const source=new Image();source.src=assetURL(path).href;await source.decode();
        const canvas=document.createElement('canvas');canvas.width=source.width;canvas.height=source.height;
        canvas.dataset.source=source.src;
        canvas.getContext('2d',{willReadFrequently:true}).drawImage(source,0,0);
        return canvas;
      }
      [image,directionalImage]=await Promise.all([loadAtlas(metadata.source),loadAtlas(metadata.directional.source)]);
      return window.KyuubiForm;
    })().catch(error=>{pending=null;throw error;});
    return pending;
  }
  function install(G,{enabled=()=>true}={}){
    if(installed.has(G))return G.KyuubiForm;
    installed.add(G);
    const shadow=owner=>G.NarutoClones?.actors.includes(owner);
    const source=owner=>shadow(owner)?owner.owner:owner;
    const effect=owner=>G.NarutoSupport?.effects.find(f=>f.owner===source(owner)&&f.world===G.World&&f.mode==='nine-tails-cloak'&&f.age<f.ttl);
    const active=owner=>{
      const root=source(owner);
      return !!(image&&enabled()&&(root===G.Game.player||G.SelfClones?.isActor(root))&&root?.dex===30001&&!root.dead&&root.hp>0&&!owner.dead&&(!shadow(owner)||owner.world===G.World)&&effect(owner));
    };
    const smooth=value=>{const t=Math.max(0,Math.min(1,value));return t*t*(3-2*t);};
    function poseFor(animator){
      const owner=G.Game.player?.anim===animator?G.Game.player:G.SelfClones?.actors().find(a=>a.anim===animator)||G.NarutoClones?.actors.find(a=>a.anim===animator);
      if(owner?.anim!==animator||!active(owner))return null;
      const action=G.AnimationLab.stateFor(animator),buff=effect(owner);
      let animation='idle',age=action.age;
      if(shadow(owner)&&!owner.mimickedId&&animator.cur==='Attack'&&animator.busy()){
        animation='attack';age=Math.max(0,Math.min(1,animator.progress()))*.18;
      }
      else if(action.state==='hurt')animation='hurt';
      else if(action.state==='skill'){
        if(action.id==='naruto-naruto')animation=['windup','charge'].includes(action.phase)?'rasenganCharge':['release','dash','strike'].includes(action.phase)?'rasenganDash':'rasenganRecover';
        else if(['naruto-kunai','naruto-shuriken','naruto-rasenshuriken'].includes(action.id))animation='throw';
        else animation='activation';
      }else if(buff.age<.55){animation='activation';age=buff.age;}
      else if(shadow(owner)&&owner.comboT>0){animation='attack';age=.4-owner.comboT;}
      else if(!shadow(owner)&&buff.pulseFlash>0){animation='attack';age=.18-buff.pulseFlash;}
      else if(owner.walking||action.state==='movement')animation='run';
      const direction=action.direction,vertical=metadata.directional.animations[direction];
      const atlas=vertical?metadata.directional:metadata;
      const sequence=(vertical||metadata.animations)[animation];
      let index=Math.floor(Math.max(0,age)*sequence.fps);
      if(animation==='rasenganCharge')index=action.frame===0?0:1;
      if(animation==='attack')index=Math.floor(Math.min(.999,Math.max(0,age)/.18)*sequence.frames.length);
      index=sequence.loop?index%sequence.frames.length:Math.min(index,sequence.frames.length-1);
      const frame=sequence.frames[index];
      const aim=owner.comboT>0?owner.comboAim:owner.target?Math.atan2(owner.target.y-owner.y,owner.target.x-owner.x):source(owner).aim;
      const mirror=!vertical&&(direction==='left'||(direction!=='right'&&Math.cos(aim||0)<0));
      // Build chakra first, then make the body change brief enough to avoid a double silhouette.
      const blend=smooth((buff.age-.25)/.3)*smooth((buff.ttl-buff.age)/.3);
      const ordinary=action.id==='naruto-nine-tails-cloak';
      const moving=owner.walking||animator.base==='Walk';
      const normalKey=ordinary?'naruto-'+(moving?'movement':'idle'):null;
      const normalFrame=({down:0,up:1,left:2,right:3}[direction]||0)*4+Math.floor(buff.age*(moving?10:5))%4;
      return {key:'naruto-one-tail',animation,frame:index,rect:frame.rect,anchor:frame.anchor,mirror,direction,blend,normalKey,normalFrame,source:atlas.source,bodyHeight:atlas.bodyHeight,orb:frame.orb||null};
    }
    const draw=G.Sprites.Animator.prototype.draw;
    G.Sprites.Animator.prototype.draw=function(ctx,x,y,options={}){
      const pose=poseFor(this);
      if(!pose)return draw.apply(this,arguments);
      // A crouching body sits lower than the standing body; tail/flames are not height.
      const scale=55*(this.scale||1)/pose.bodyHeight,[sx,sy,w,h]=pose.rect;
      const atlasImage=pose.source===metadata.directional.source?directionalImage:image;
      if(pose.blend<1){
        const opts={...options,alpha:(options.alpha??1)*(1-pose.blend)};
        if(pose.normalKey)AnimationAssets.draw(ctx,pose.normalKey,pose.normalFrame,x,y,{...opts,scale:this.scale||1});
        else draw.call(this,ctx,x,y,opts);
      }
      ctx.save();ctx.translate(x,y);ctx.scale((pose.mirror?-1:1)*scale,scale);ctx.imageSmoothingEnabled=false;
      ctx.globalAlpha*=(options.alpha??1)*pose.blend;
      ctx.drawImage(options.flash?G.Sprites.white(atlasImage):atlasImage,sx,sy,w,h,-pose.anchor[0],-pose.anchor[1],w,h);
      ctx.restore();
      const counters=G.AnimationLab.counters;counters.candidate++;
      counters.byState[actionState(pose)]=(counters.byState[actionState(pose)]||0)+1;
    };
    const cloak=G.NarutoCloakVFX.draw;
    G.NarutoCloakVFX.draw=function(ctx,f,ground){
      if(!active(f.owner))return cloak.apply(this,arguments);
      // Chakra appears on the original body before the dedicated crouch takes over.
      if(f.age<.55||f.ttl-f.age<.45){
        ctx.save();ctx.globalAlpha*=1-(poseFor(f.owner.anim)?.blend??0);
        cloak.apply(this,arguments);ctx.restore();
      }
      if(ground&&f.pulseFlash>0){
        ctx.save();ctx.translate(f.owner.x,f.owner.y);ctx.globalAlpha*=f.pulseFlash/.18*.55;
        ctx.fillStyle='#ff8155';const r=f.m.radius;
        for(let i=0;i<32;i++){const a=i*Math.PI/16;ctx.fillRect(Math.round(Math.cos(a)*r),Math.round(Math.sin(a)*r),3,2);}
        ctx.restore();
      }
    };
    G.KyuubiForm={active,poseFor,get image(){return image;},get directionalImage(){return directionalImage;},get metadata(){return metadata;}};
    return G.KyuubiForm;
  }
  function actionState(pose){return pose.animation==='idle'?'idle':pose.animation==='run'?'movement':pose.animation==='hurt'?'hurt':'skill';}
  window.KyuubiForm={load,install,get image(){return image;},get metadata(){return metadata;}};
})();
