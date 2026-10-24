/* Original Temari atlas facade. Image data is loaded only when this ninja is requested. */
(() => {
  'use strict';
  const base=new URL('./',document.currentScript.src),images={},flashes={};
  let metadata,pending;
  const common={
    idle:{down:[0,1],up:[2,3],right:[4,5]},
    move:{down:[6,7],up:[12,13,14,15],right:[8,9,10,11]},
    hurt:{down:[16,17],up:[18,19],right:[18,19]},
    death:{down:[20,21,22,23],up:[20,21,22,23],right:[20,21,22,23]}
  };
  const direction=dir=>typeof dir==='string'?dir:['down','right','right','right','up','left','left','left'][((dir||0)%8+8)%8];
  function load() {
    if(pending)return pending;
    pending=(async()=>{
      const response=await fetch(new URL('temari-frames.json',base));
      if(!response.ok)throw Error('手鞠動畫資料載入失敗');
      metadata=await response.json();
      await Promise.all(Object.entries(metadata.sheets).map(async([key,sheet])=>{
        const image=new Image();image.src=new URL(sheet.source,base).href;await image.decode();images[key]=image;
        const flash=document.createElement('canvas');flash.width=image.width;flash.height=image.height;
        const ctx=flash.getContext('2d');ctx.drawImage(image,0,0);ctx.globalCompositeOperation='source-in';
        ctx.fillStyle='#fff';ctx.fillRect(0,0,flash.width,flash.height);flashes[key]=flash;
      }));
      api.loaded=true;return api;
    })().catch(error=>{pending=null;throw error;});
    return pending;
  }
  function sample(state='idle',time=0,dir=0,stars=1) {
    if(!metadata)return null;
    let key='common',sequence,index;
    const d=direction(dir),side=d==='left'?'right':d,age=Math.max(0,Number(time)||0);
    if(common[state]) {
      sequence=common[state][side]||common[state].right;
      const fps=state==='idle'?5:state==='death'?6.6666666667:10;
      const step=Math.floor(age*fps);
      index=sequence[state==='hurt'||state==='death'?Math.min(sequence.length-1,step):step%sequence.length];
    } else {
      key='skills';
      if(state==='typhoon'&&age>=.4) {
        key='spin';index=Math.min(7,Math.floor((age-.4)/1.2*8));
      }
      else if(state==='reflect') {index=age<.16?8:6;}
      else if(state==='heavy'||state==='typhoon') {sequence=[8,9,10,11];index=sequence[age<.16?0:age<.4?1:age<.53?2:3];}
      else if(state==='summon') {sequence=[12,13,14,15];index=sequence[age<.35?0:age<.53?1:age<.65?2:3];}
      else {sequence=stars>=3?[0,6,7,3]:stars===2?[0,4,5,3]:[0,1,2,3];index=sequence[age<.10?0:age<.18?1:age<.31?2:3];}
    }
    const sheet=metadata.sheets[key],frame=sheet.frames[index];
    return {...frame,sheet:key,source:sheet.source,bodyHeight:frame.bodyHeight||sheet.bodyHeight,index,state,direction:d};
  }
  function paint(ctx,frame,options) {
    const image=options.flash?flashes[frame.sheet]:images[frame.sheet];
    if(!image)return false;
    const [sx,sy,sw,sh]=frame.rect,scale=(options.height??64)/frame.bodyHeight;
    const face=options.facing??(frame.direction==='left'?-1:1);
    ctx.save();ctx.translate(options.x??0,options.y??0);ctx.scale(face===-1||face==='left'?-scale:scale,scale);
    ctx.globalAlpha*=options.alpha??1;ctx.imageSmoothingEnabled=false;
    ctx.drawImage(image,sx,sy,sw,sh,-frame.anchor[0],-frame.anchor[1],sw,sh);ctx.restore();return true;
  }
  function draw(ctx,actor={},options) {
    if(!options){options=actor;actor={};}
    if(!api.loaded){void load().catch(()=>{});return false;}
    const state=options.state||actor.pose||'idle',pose=actor.owner?G.NarutoTemari?.activeFor(actor.owner):null;
    const round=actor.basicRounds??0,stars=options.stars??pose?.stars??(pose?.empowered?3:round%3+1);
    const frame=sample(state,options.time??actor.age??0,options.dir??actor.dir??0,stars);
    return !!frame&&paint(ctx,frame,options);
  }
  function drawSummon(ctx,actor={},options={}) {
    if(!api.loaded)return false;
    const phase=options.phase||actor.phase||'move',time=options.time??actor.age??0;
    const moving=(phase==='move'||phase==='return'||phase==='follow'||phase==='wander')&&actor.moving;
    const index=moving?[1,2,3,2][Math.floor(time*12)%4]:phase==='slash'?4+((actor.slash??Math.floor(time/.12))%4):
      phase==='fade'?7:0;
    const sheet=metadata.sheets.kamatari,frame=sheet.frames[index];
    return paint(ctx,{...frame,sheet:'kamatari',bodyHeight:frame.bodyHeight||sheet.bodyHeight,direction:options.dir||actor.dir||'right'},
      {...options,x:options.x??actor.x,y:options.y??actor.y,height:options.height??36,
        alpha:(options.alpha??1)*(phase==='fade'?Math.max(0,1-(time-(actor.fadeAt??time))/.22):1)});
  }
  function portrait(ctx,options={}) {
    if(!api.loaded){void load().catch(()=>{});return false;}
    const f=sample('idle'),[sx,sy,sw,sh]=f.rect,image=images.common;
    const cropHeight=Math.min(sh,f.bodyHeight*.48),cropWidth=Math.min(sw,cropHeight);
    ctx.save();ctx.imageSmoothingEnabled=false;
    ctx.drawImage(image,sx+(sw-cropWidth)/2,sy,cropWidth,cropHeight,options.x??0,options.y??0,
      options.width??options.size??48,options.height??options.size??48);ctx.restore();return true;
  }
  const api={loaded:false,load,draw,drawSummon,portrait,sample,get ready(){return load();},get metadata(){return metadata;},get images(){return images;}};
  window.TemariArt=api;if(window.G)G.TemariArt=api;
})();
