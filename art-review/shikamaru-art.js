/* Original Shikamaru artwork. Pose selection is read-only; combat owns all clocks. */
(() => {
  'use strict';
  const base=new URL('./',document.currentScript.src),images={},whites={};
  let metadata,pending;
  const direction=dir=>typeof dir==='string'?dir:['down','right','right','right','up','left','left','left'][((dir||0)%8+8)%8];
  async function load(){
    if(pending)return pending;
    pending=(async()=>{
      const response=await fetch(new URL('shikamaru-frames.json',base));
      if(!response.ok)throw Error('鹿丸動畫資料載入失敗');metadata=await response.json();
      await Promise.all(Object.entries(metadata.sheets).map(async([key,sheet])=>{
        const image=new Image(),url=new URL(sheet.source,base);url.searchParams.set('v',sheet.sha256);image.src=url.href;await image.decode();images[key]=image;
        const flash=document.createElement('canvas');flash.width=image.width;flash.height=image.height;
        const ctx=flash.getContext('2d');ctx.drawImage(image,0,0);ctx.globalCompositeOperation='source-in';ctx.fillStyle='#fff';ctx.fillRect(0,0,flash.width,flash.height);whites[key]=flash;
      }));api.loaded=true;return api;
    })().catch(error=>{pending=null;throw error;});return pending;
  }
  function sample(state='idle',time=0,dir=0,pose=null){
    if(!metadata)return null;
    const d=direction(dir),prefix=d==='down'?'front':d==='up'?'back':'',age=Math.max(0,Number(time)||0);
    const phase=pose?.phase,localAge=Math.max(0,Number(pose?.phaseAge)||0),phaseDuration=Math.max(.001,Number(pose?.phaseDuration)||.3),phaseProgress=Math.min(1,localAge/phaseDuration);
    const named=name=>prefix?prefix+name[0].toUpperCase()+name.slice(1):name;
    const idle=prefix?prefix+'Idle':'idle';let key=idle;
    if(state==='walk'||state==='move')key=prefix?prefix+'Run'+(1+Math.floor(age*10)%2):'run'+(1+Math.floor(age*10)%2);
    else if(state==='hurt')key='hurt';
    else if(state==='faint'||state==='death')key=age<.22?'exhausted':'faint';
    else if(phase){
      const moving=!!pose.moving;
      if(moving&&['drag','net','blast','finish','recover','sewing'].includes(phase))key=prefix?prefix+'Run'+(1+Math.floor(age*10)%2):'run'+(1+Math.floor(age*10)%2);
      else if(pose.kind==='trap'&&['prepare','release','recover'].includes(phase))key=named(phase==='prepare'?'throwPrepare':phase==='release'?(phaseProgress<.7?'throwRelease':'throwRecover'):'throwRecover');
      else if(phase==='drag'||phase==='blast'||phase==='recover')key=idle;
      else if(phase==='net')key=named(phaseProgress<.12?'prepare':'seal');
      else if(phase==='sewing'){
        // The reference-driven arc leaves from a standing rat seal; its
        // independent travel must not replay the retired ground-stab crouch.
        const stage=pose.stage;
        const recovering=stage==='recover'||stage==='return'||phaseProgress>=.92;
        const preparing=stage==='ground'?localAge<.1:!stage&&phaseProgress<.18;
        key=recovering?idle:named(preparing?'prepare':'seal');
      }
      else if(phase==='finish')key=pose.kind==='strangle'?named(phaseProgress<.35?'crouch':phaseProgress<.86?'seal':'idle'):idle;
      else key=named(phase==='prepare'?'prepare':'seal');
    }
    else if(state==='cast'||pose){
      const kind=pose?.kind||pose?.type||'',duration=Math.max(.3,pose?.duration||.9),progress=age/duration;
      if(/kunai|basic|throw|bomb|trap/.test(kind))key=(prefix||'')+(prefix?(progress<.24?'ThrowPrepare':progress<.65?'ThrowRelease':'ThrowRecover'):(progress<.24?'throwPrepare':progress<.65?'throwRelease':'throwRecover'));
      else key=prefix?prefix+(progress<.2?'Prepare':progress<.82?'Seal':'Idle'):(progress<.2?'prepare':progress<.82?'seal':'idle');
      if(/stitch|sew|strangle|neck|possession|bind/.test(kind)&&progress>=.30&&progress<.76)key=prefix?prefix+'Crouch':'crouch';
    }
    const frame=metadata.sheets.body.frames[key]||metadata.sheets.body.frames[idle];
    return {...frame,key,sheet:'body',direction:d,source:metadata.sheets.body.source,state};
  }
  function paint(ctx,frame,options={}){
    const [sx,sy,sw,sh]=frame.rect,k=(options.height??64)/frame.bodyHeight;
    ctx.save();ctx.translate(options.x??0,options.y??0);ctx.scale(frame.direction==='left'?-k:k,k);
    ctx.globalAlpha*=options.alpha??1;ctx.imageSmoothingEnabled=false;
    ctx.drawImage(images.body,sx,sy,sw,sh,-frame.anchor[0],-frame.anchor[1],sw,sh);
    if(options.flash){ctx.globalAlpha*=.55;ctx.drawImage(whites.body,sx,sy,sw,sh,-frame.anchor[0],-frame.anchor[1],sw,sh);}
    ctx.restore();return true;
  }
  function draw(ctx,actor={},options){
    if(!options){options=actor;actor={};}
    if(!api.loaded){void load().catch(()=>{});return false;}
    const pose=options.pose??G.NarutoShikamaru?.activeFor?.(actor),state=options.state||'idle';
    const frame=sample(state,options.time??pose?.age??0,pose&&!(pose.moving&&['drag','net','blast','finish','recover','sewing'].includes(pose.phase))&&Number.isFinite(pose.aim)?G.Sprites.dirFromAngle(pose.aim):(options.dir??actor.anim?.dir??0),pose);
    return !!frame&&paint(ctx,frame,options);
  }
  const api={loaded:false,load,sample,draw,get ready(){return load();},get metadata(){return metadata;},get images(){return images;}};
  window.ShikamaruArt=api;if(window.G)G.ShikamaruArt=api;
})();
