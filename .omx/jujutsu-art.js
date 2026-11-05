/* Authored Sendai crossover animation sheets; rectangles preserve source anatomy. */
(() => {
  'use strict';
  const base=new URL('../art-review/',document.currentScript.src),images={},flashes={};
  const slugs={30013:'yuta',30014:'ryu',30015:'uro'};
  let metadata,pending;
  const loading=new Map();
  const keysFor=dex=>slugs[dex]?[slugs[dex]+'-common',slugs[dex]+'-skills',...(dex===30013?['rika-skills']:[])]:Object.keys(metadata?.sheets||{});
  function loadMetadata(){
    if(metadata)return Promise.resolve(metadata);
    if(!pending)pending=(async()=>{
      const response=await fetch(new URL('jjk-skills-v2.json',base));
      if(!response.ok)throw Error('咒術角色動畫資料載入失敗');
      metadata=await response.json();
      return metadata;
    })().catch(error=>{pending=null;throw error;});return pending;
  }
  function loadSheet(key){
    if(images[key])return Promise.resolve();
    if(!loading.has(key))loading.set(key,(async()=>{
      const image=new Image();image.src=new URL(metadata.sheets[key].source,base).href;
      await image.decode();images[key]=image;
    })().finally(()=>loading.delete(key)));
    return loading.get(key);
  }
  async function load(dex){
    await loadMetadata();await Promise.all(keysFor(+dex).map(loadSheet));api.loaded=true;return api;
  }
  const isReady=dex=>!!metadata&&keysFor(+dex).length>0&&keysFor(+dex).every(key=>!!images[key]);
  function flashFor(key){
    if(flashes[key])return flashes[key];
    const image=images[key],flash=document.createElement('canvas');flash.width=image.width;flash.height=image.height;
    const ctx=flash.getContext('2d');ctx.drawImage(image,0,0);ctx.globalCompositeOperation='source-in';
    ctx.fillStyle='#fff';ctx.fillRect(0,0,flash.width,flash.height);flashes[key]=flash;return flash;
  }
  function direction(dir=0){return typeof dir==='string'?dir:['down','right','right','right','up','left','left','left'][((dir%8)+8)%8];}
  function frameFor(slug,semantic,time=0,dir='right',pose=null){
    const sequence=metadata?.animations[slug]?.[semantic];if(!sequence)return null;
    const sheet=metadata.sheets[sequence.sheet],last=sequence.frames.length-1;
    let phase=Math.max(0,Math.floor(time*(sequence.fps||8)));
    if(pose){
      const named=sequence.frames.find(index=>sheet.frames[index].name===pose.frameName);
      if(named!=null)return {...sheet.frames[named],sheet:sequence.sheet,index:named,bodyHeight:sheet.bodyHeight,direction:dir,semantic};
      const stage=pose.visualPhase||pose.phase;
      phase=semantic==='sky'?(stage==='windup'?0:stage==='pull'?1:2):
        ['windup','pull'].includes(stage)?(stage==='pull'&&last>2?1:0):['slash','release','fire','shatter','smash'].includes(stage)?Math.min(last,semantic==='collapse'?2:1):last;
    }else phase=sequence.loop?phase%sequence.frames.length:Math.min(last,phase);
    const index=sequence.frames[Math.min(last,phase)];
    return {...sheet.frames[index],sheet:sequence.sheet,index,bodyHeight:sheet.bodyHeight,direction:dir,semantic};
  }
  function sample(dex,state='idle',time=0,dir=0,pose=null){
    const slug=slugs[dex];if(!metadata||!slug)return null;
    let d=direction(dir),side=d==='left'?'Side':d==='right'?'Side':d==='up'?'Back':'Front';
    let semantic='idle'+side;
    if(state==='faint'||state==='death'){semantic='faint';pose=null;}
    else if(state==='hurt'){semantic='hurt';pose=null;}
    else if(state==='cast'||pose){
      const mode=pose?.mode||pose?.kind||'';
      semantic=slug==='yuta'?(/speech/.test(mode)?'speech':/manifest/.test(mode)?'manifest':'blade'):
        slug==='ryu'?(/maximum/.test(mode)?'maximum':'light'):
        /thin-ice/.test(mode)?'thinIce':/screen/.test(mode)?'screen':/collapse/.test(mode)?'collapse':'sky';
      if(pose?.aim!=null)d=Math.cos(pose.aim)<0?'left':'right';
    }else if(state==='walk'||state==='move')semantic='walk'+side;
    return frameFor(slug,semantic,time,d,pose);
  }
  function paint(ctx,frame,options={}){
    if(!images[frame.sheet])return false;
    const image=options.flash?flashFor(frame.sheet):images[frame.sheet];
    const [sx,sy,sw,sh]=frame.rect,scale=(options.height??64)/frame.bodyHeight;
    ctx.save();ctx.translate(options.x??0,options.y??0);ctx.scale(frame.direction==='left'?-scale:scale,scale);
    ctx.globalAlpha*=options.alpha??1;ctx.imageSmoothingEnabled=false;
    ctx.drawImage(image,sx,sy,sw,sh,-frame.anchor[0],-frame.anchor[1],sw,sh);ctx.restore();return true;
  }
  function pointFor(actor,pose,name){
    const dex=+(actor?.mon?.dex??actor?.dex),frame=sample(dex,'cast',pose?.age||0,actor?.anim?.dir||0,pose);
    const point=frame?.points?.[name];if(!point)return null;
    const scale=64*(actor.anim?.scale||1)/frame.bodyHeight,sign=frame.direction==='left'?-1:1;
    return {x:actor.x+(point[0]-frame.anchor[0])*scale*sign,y:actor.y+(point[1]-frame.anchor[1])*scale};
  }
  function draw(ctx,actor={},options={}){
    const dex=+(options.dex??actor.mon?.dex??actor.dex),pose=options.pose??
      (dex===30013?G.JujutsuYuta?.pose?.(actor):dex===30014?G.JjkRyu?.pose?.(actor):G.JjkUro?.poseFor?.(actor));
    if(!isReady(dex)){void load(dex).catch(()=>{});return false;}
    const frame=sample(dex,options.state||'idle',options.time??actor.age??0,options.dir??actor.dir??0,pose);
    return !!frame&&paint(ctx,frame,options);
  }
  function drawRika(ctx,actor={},options={}){
    if(!api.loaded)return false;
    const phase=options.phase??actor.phase,age=options.time??actor.phaseAge??actor.age??0;
    const aim=options.angle??actor.aim??0,left=Math.cos(aim)<0;
    const semantic=phase==='strike'?'strike':phase==='return'?'return':phase==='manifest'?'manifest':'travel';
    const frame=frameFor('rika',semantic,age,left?'left':'right',phase==='strike'?actor:null);
    return !!frame&&paint(ctx,frame,{...options,x:options.x??actor.x,y:options.y??actor.y,height:options.height??(actor.full?112:72)});
  }
  const api={loaded:false,load,isReady,draw,drawRika,sample,pointFor,get ready(){return load();},get metadata(){return metadata;},images};
  window.JujutsuArt=api;if(typeof G==='object')G.JujutsuArt=api;
})();
