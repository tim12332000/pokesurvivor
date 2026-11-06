/* Authored Sendai crossover animation sheets; rectangles preserve source anatomy. */
(() => {
  'use strict';
  const base=new URL('../art-review/',document.currentScript.src),images={},flashes={};
  const slugs={30013:'yuta',30014:'ryu',30015:'uro'};
  let metadata,pending;
  const loading=new Map();
  const veilMasks=new Map(),veilBackground=document.createElement('canvas');
  const previewBackgrounds=new WeakMap();
  let veilSource=null,veilWorld=null,veilStamp=null,veilCaptures=0,veilDraws=0;
  function captureUroBackground(ctx){
    const actors=[G.Game?.player,...(G.SelfClones?.actors?.()||[])];
    if(!actors.some(a=>a&&!a.dead&&(a.mon?.dex??a.dex)===30015))return;
    const limit=innerWidth<=700||G.Touch?.active?512:1024,ratio=Math.min(1,limit/Math.max(ctx.canvas.width,ctx.canvas.height));
    const width=Math.max(1,Math.round(ctx.canvas.width*ratio)),height=Math.max(1,Math.round(ctx.canvas.height*ratio));
    const matrix=ctx.getTransform(),stamp=[G.CombatPulse?.epoch,G.Game?.st?.time,width,height,G.Camera?.x,G.Camera?.y,matrix.a,matrix.d,matrix.e,matrix.f].join('/');
    if(veilSource===ctx.canvas&&veilWorld===G.World&&veilStamp===stamp)return;
    if(veilBackground.width!==width||veilBackground.height!==height){veilBackground.width=width;veilBackground.height=height;}
    const out=veilBackground.getContext('2d');out.clearRect(0,0,width,height);out.imageSmoothingEnabled=false;out.drawImage(ctx.canvas,0,0,width,height);
    veilSource=ctx.canvas;veilWorld=G.World;veilStamp=stamp;veilCaptures++;
  }
  function drawPreviewBackground(ctx){
    const w=ctx.canvas.width,h=ctx.canvas.height;ctx.save();ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,w,h);
    const sky=ctx.createLinearGradient(0,0,w,h);sky.addColorStop(0,'#658d9d');sky.addColorStop(.55,'#b4cbd0');sky.addColorStop(1,'#7898a2');
    ctx.fillStyle=sky;ctx.fillRect(0,0,w,h);ctx.lineCap='round';
    for(let i=0;i<4;i++){
      const y=h*(.12+i*.24);ctx.globalAlpha=.26;ctx.strokeStyle='#ecf5f3';ctx.lineWidth=h*.07;ctx.beginPath();ctx.moveTo(-w*.1,y);
      ctx.bezierCurveTo(w*.15,y-h*.1,w*.35,y+h*.13,w*.58,y);ctx.bezierCurveTo(w*.75,y-h*.09,w*.8,y+h*.05,w*1.1,y-h*.02);ctx.stroke();
    }
    ctx.restore();
    let background=previewBackgrounds.get(ctx.canvas);
    if(!background){background=document.createElement('canvas');previewBackgrounds.set(ctx.canvas,background);}
    if(background.width!==w||background.height!==h){background.width=w;background.height=h;}
    const copy=background.getContext('2d');copy.clearRect(0,0,w,h);copy.drawImage(ctx.canvas,0,0);
  }
  function veilMask(frame){
    const key=frame.sheet+':'+frame.index;if(veilMasks.has(key))return veilMasks.get(key);
    const [sx,sy,w,h]=frame.rect,source=document.createElement('canvas');source.width=w;source.height=h;
    const scan=source.getContext('2d',{willReadFrequently:true});scan.drawImage(images[frame.sheet],sx,sy,w,h,0,0,w,h);
    const pixels=scan.getImageData(0,0,w,h).data,mask=document.createElement('canvas');mask.width=w;mask.height=h;
    const ctx=mask.getContext('2d'),rows=[],spans=[],materialPixels=new Uint8Array(w*h);ctx.fillStyle='#fff';
    for(let y=0;y<h;y++){
      const columns=[];
      for(let x=0;x<w;x++){const i=(y*w+x)*4,r=pixels[i],g=pixels[i+1],b=pixels[i+2];
        if(pixels[i+3]>100&&g>r*1.08&&b>r*1.08&&b>100){columns.push(x);materialPixels[y*w+x]=1;}}
      const runs=[];for(const x of columns){const last=runs.at(-1);if(last&&x-last.right<=12)last.right=x;else runs.push({left:x,right:x});}
      for(const {left,right}of runs){
        // Cover the entire old material, including its black seam/highlight
        // holes. The expanded, broken silhouette is an optical plane, not a
        // recoloured garment; no new body pixels are synthesized.
        const edge=12+Math.round(Math.sin(y*.19)*4);ctx.fillRect(left-edge,y-5,right-left+edge*2+1,11);spans.push({left,right});
      }
      if(runs.length)rows.push(y);
    }
    // Preserve only skin/limb pixels already present in the modest source.
    // This restores hands crossing a sky sheet without synthesizing anatomy.
    const protectedPixels=new Uint8Array(w*h),coverage=ctx.getImageData(0,0,w,h);
    for(let y=0;y<h;y++)for(let x=0;x<w;x++){
      const i=(y*w+x)*4,r=pixels[i],g=pixels[i+1],b=pixels[i+2];
      if(pixels[i+3]>80&&r>120&&r>g*1.035&&r>b*1.04&&g>65)protectedPixels[y*w+x]=1;
    }
    for(let y=0;y<h;y++)for(let x=0;x<w;x++){
      const i=(y*w+x)*4;let protect=protectedPixels[y*w+x],clothingEdge=false;
      // Warm antialiased hem pixels can resemble skin. Material adjacency
      // wins for dark ink/shadow, before skin protection restores any pixels.
      if(pixels[i+3]>80&&pixels[i]<210&&pixels[i+1]<190&&pixels[i+2]<180)
        for(let dy=-6;dy<=6&&!clothingEdge;dy++)for(let dx=-6;dx<=6;dx++)if(x+dx>=0&&x+dx<w&&y+dy>=0&&y+dy<h&&materialPixels[(y+dy)*w+x+dx]){clothingEdge=true;break;}
      if(clothingEdge)coverage.data[i+3]=255;
      else{
        if(!protect&&pixels[i]<100&&pixels[i+1]<100&&pixels[i+2]<100)
          for(let dy=-2;dy<=2&&!protect;dy++)for(let dx=-2;dx<=2;dx++)if(x+dx>=0&&x+dx<w&&y+dy>=0&&y+dy<h&&protectedPixels[(y+dy)*w+x+dx]){protect=1;break;}
        if(protect)coverage.data[i+3]=0;
      }
    }
    ctx.putImageData(coverage,0,0);
    const cutout=document.createElement('canvas');cutout.width=w;cutout.height=h;cutout.dataset.source='jjk-uro-spatial-base:'+key;
    const clean=cutout.getContext('2d');clean.drawImage(source,0,0);clean.globalCompositeOperation='destination-out';clean.drawImage(mask,0,0);
    const flash=document.createElement('canvas');flash.width=w;flash.height=h;flash.dataset.source='jjk-uro-spatial-flash:'+key;
    const white=flash.getContext('2d');white.drawImage(cutout,0,0);white.globalCompositeOperation='source-in';white.fillStyle='#fff';white.fillRect(0,0,w,h);
    const result={mask,cutout,flash,patch:document.createElement('canvas'),middle:rows.length?(rows[0]+rows.at(-1))/2:h/2,top:rows[0]||0,bottom:rows.at(-1)||h,
      left:spans.length?Math.max(0,Math.min(...spans.map(s=>s.left))-16):0,right:spans.length?Math.min(w,Math.max(...spans.map(s=>s.right))+16):w,glints:[]};
    for(const [y,side]of [[result.top+12,1],[result.bottom-9,-1]]){
      const data=ctx.getImageData(0,Math.max(0,Math.min(h-1,Math.round(y))),w,1).data;
      let left=w,right=-1;for(let x=0;x<w;x++)if(data[x*4+3]){left=Math.min(left,x);right=x;}
      if(right>left){const span=(right-left)*.28;result.glints.push({x:side>0?left:right-span,y,side,span});}
    }
    result.patch.width=w;result.patch.height=h;result.patch.dataset.source='jjk-uro-optical-cover:'+key;veilMasks.set(key,result);return result;
  }
  function drawUroVeil(ctx,frame,options){
    const entry=veilMask(frame),patch=entry.patch,out=patch.getContext('2d'),w=patch.width,h=patch.height;
    const inverse=ctx.getTransform().inverse(),clock=G.Game?.st?.time||0,shift=24+Math.sin(clock*1.2)*5;
    out.setTransform(1,0,0,1,0,0);out.globalCompositeOperation='source-over';out.clearRect(0,0,w,h);
    for(const [top,bottom,side]of [[0,entry.middle,1],[entry.middle,h,-1]]){
      out.save();out.beginPath();out.rect(0,top,w,bottom-top);out.clip();
      // UI / transparent canvases receive an opaque abstract sky. Runtime
      // uses a clean pre-actor scene, never an earlier Uro frame.
      out.fillStyle=side>0?'#bddde5':'#b3d5dd';out.fillRect(0,top,w,bottom-top);
      const background=previewBackgrounds.get(ctx.canvas)||(ctx.canvas===veilSource&&veilBackground.width?veilBackground:null);
      if(background){
        out.setTransform(inverse.a,inverse.b,inverse.c,inverse.d,inverse.e+frame.anchor[0]+shift*side,inverse.f+frame.anchor[1]+side*3);
        out.imageSmoothingEnabled=false;out.drawImage(background,0,0,background.width,background.height,0,0,ctx.canvas.width,ctx.canvas.height);
      }
      out.restore();
    }
    out.globalCompositeOperation='destination-in';out.drawImage(entry.mask,0,0);out.globalCompositeOperation='source-over';
    out.save();out.globalCompositeOperation='source-atop';
    for(const [top,bottom,side]of [[entry.top,entry.middle,1],[entry.middle,entry.bottom,-1]]){
      const x=entry.left,width=entry.right-entry.left,dy=bottom-top;
      out.globalAlpha=side>0?.12:.1;out.fillStyle=side>0?'#fff':'#17272c';out.beginPath();
      out.moveTo(x,top+dy*.22);out.lineTo(x+width*.58,top+dy*.06);out.lineTo(x+width,bottom-dy*.18);out.lineTo(x+width*.3,bottom);out.closePath();out.fill();
    }out.restore();
    // A few broken optical glints communicate the shifted sightline without
    // closing into a collar, seam, grid or a continuous garment silhouette.
    out.save();out.globalCompositeOperation='source-atop';out.strokeStyle='#e1f4f7';out.globalAlpha=.75;out.lineWidth=3;
    for(const {x,y,side,span}of entry.glints){
      out.beginPath();out.moveTo(x,y+side*2);out.quadraticCurveTo(x+span*.5,y-side*4,x+span,y);out.stroke();
    }out.restore();
    ctx.drawImage(patch,-frame.anchor[0],-frame.anchor[1]);veilDraws++;
  }
  const keysFor=dex=>slugs[dex]?[slugs[dex]+'-common',slugs[dex]+'-skills',...(dex===30013?['rika-skills']:[])]:Object.keys(metadata?.sheets||{});
  function loadMetadata(){
    if(metadata)return Promise.resolve(metadata);
    if(!pending)pending=(async()=>{
      const response=await fetch(new URL('jjk-skills-v2.json?v=uro-midriff-v8',base));
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
    const uro=frame.sheet==='uro-common'||frame.sheet==='uro-skills';
    if(uro){const entry=veilMask(frame);ctx.drawImage(options.flash?entry.flash:entry.cutout,-frame.anchor[0],-frame.anchor[1]);drawUroVeil(ctx,frame,options);}
    else ctx.drawImage(image,sx,sy,sw,sh,-frame.anchor[0],-frame.anchor[1],sw,sh);
    ctx.restore();return true;
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
    const frame=frameFor('rika',semantic,age,left?'left':'right',phase==='strike'?actor:actor.releasePose||null);
    return !!frame&&paint(ctx,frame,{...options,x:options.x??actor.x,y:options.y??actor.y,height:options.height??(actor.full?112:72)});
  }
  function drawFrame(ctx,key,index,options={}){
    const sheet=metadata?.sheets[key],frame=sheet?.frames[index];
    return !!frame&&paint(ctx,{...frame,sheet:key,index,bodyHeight:sheet.bodyHeight,direction:options.direction||'right'},options);
  }
  const api={loaded:false,load,isReady,draw,drawFrame,drawRika,sample,pointFor,captureUroBackground,drawPreviewBackground,
    spatialVeil:{inspect:()=>({captures:veilCaptures,draws:veilDraws,masks:veilMasks.size,bytes:veilBackground.width*veilBackground.height*4,source:veilSource!==null})},
    get ready(){return load();},get metadata(){return metadata;},images};
  window.JujutsuArt=api;if(typeof G==='object')G.JujutsuArt=api;
})();
