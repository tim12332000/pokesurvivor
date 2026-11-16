/* Reference-driven shadows: actual body alpha, ground projection, and swept xyz tips. */
(() => {
  const masks=new Map(),rasters=new Map(),projectionCache=new WeakMap();let revision=0;
  const clamp=x=>Math.max(0,Math.min(1,x));
  function bodyFor(actor){
    const dex=actor.mon?.dex??actor.dex,anim=actor.anim;if(!anim)return null;
    let image,rect,anchor,k,key,url,mirror=false;
    if(dex===30017){
      const art=G.ShikamaruArt;if(!art?.loaded)return null;
      const pose=G.NarutoShikamaru?.activeFor(actor),state=actor.dead||anim.cur==='Faint'?'faint':actor.flash>0||anim.cur==='Hurt'?'hurt':pose?'cast':anim.cur==='Walk'?'walk':'idle';
      const time=pose?.age??(anim.frame*6+anim.t)/60,dir=pose&&!(pose.moving&&['drag','net','blast','finish','recover','sewing'].includes(pose.phase))&&Number.isFinite(pose.aim)?G.Sprites.dirFromAngle(pose.aim):anim.dir;
      const frame=art.sample(state,time,dir,pose);if(!frame)return null;
      image=art.images.body;rect=frame.rect;anchor=frame.anchor;k=64*(anim.scale||1)/frame.bodyHeight;mirror=frame.direction==='left';key='shika:'+frame.key+':'+frame.direction+':'+k;url=frame.source;
    }else{
      let name=anim.cur,sheet=G.Sprites.sheet(dex,name,anim.shiny),meta=G.Sprites.animMeta(dex,name,anim.shiny),frame=anim.frame;
      if(!sheet?.ready){name='Idle';sheet=G.Sprites.sheet(dex,name,anim.shiny);meta=G.Sprites.animMeta(dex,name,anim.shiny);frame=0;}
      if(!sheet?.ready||!meta)return null;
      k=G.Sprites.PX*(anim.scale||1);image=sheet.img;rect=[Math.min(frame,meta.n-1)*meta.w,Math.min(anim.dir,meta.r-1)*meta.h,meta.w,meta.h];anchor=[meta.ax,meta.ay];key=[dex,name,frame,anim.dir,k,anim.shiny].join(':');url=image.src;
    }
    if(masks.has(key))return masks.get(key);
    const canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.ceil(rect[2]*k));canvas.height=Math.max(1,Math.ceil(rect[3]*k));const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.imageSmoothingEnabled=false;
    if(mirror){ctx.translate(canvas.width,0);ctx.scale(-1,1);}ctx.drawImage(image,...rect,0,0,rect[2]*k,rect[3]*k);ctx.setTransform(1,0,0,1,0,0);ctx.globalCompositeOperation='source-in';ctx.fillStyle='#030304';ctx.fillRect(0,0,canvas.width,canvas.height);
    const data=ctx.getImageData(0,0,canvas.width,canvas.height).data,foot={x:mirror?canvas.width-anchor[0]*k:anchor[0]*k,y:anchor[1]*k};
    let top=foot.y;for(let y=0;y<canvas.height;y++)for(let x=0;x<canvas.width;x++)if(data[(y*canvas.width+x)*4+3]>24)top=Math.min(top,y);
    const body={key,canvas,data,width:canvas.width,height:canvas.height,foot,bodyHeight:Math.max(1,foot.y-top),sourceURL:url,rect:rect.slice(),anchor:anchor.slice(),scale:k,mirror};
    masks.set(key,body);if(masks.size>160)masks.delete(masks.keys().next().value);return body;
  }
  function alphaAt(body,x,y){x=Math.floor(x);y=Math.floor(y);return x>=0&&y>=0&&x<body.width&&y<body.height?body.data[(y*body.width+x)*4+3]:0;}
  function project(actor,dx,dy,length,across=.65,pathClear=null){
    const body=bodyFor(actor);if(!body)return null;const d=Math.hypot(dx,dy)||1;dx/=d;dy/=d;length=Math.max(1,length);
    const rasterKey=[body.key,dx,dy,length,across].join('|'),key=[rasterKey,actor.x,actor.y].join('|'),old=projectionCache.get(actor);
    if(old?.key===key&&old.world===G.World&&old.revision===revision&&old.clip===pathClear&&old.path===G.World?.projectilePathClear&&old.block===G.World?.projectileBlock)return old.projection;
    const matrix={a:-dy*across,b:dx*across,c:-dx*length/body.bodyHeight,d:-dy*length/body.bodyHeight,e:actor.x,f:actor.y};
    const corners=[[0,0],[body.width,0],[body.width,body.height],[0,body.height]].map(([x,y])=>({x:matrix.a*(x-body.foot.x)+matrix.c*(y-body.foot.y),y:matrix.b*(x-body.foot.x)+matrix.d*(y-body.foot.y)}));
    const left=Math.floor(Math.min(...corners.map(p=>p.x)))-1,top=Math.floor(Math.min(...corners.map(p=>p.y)))-1,w=Math.ceil(Math.max(...corners.map(p=>p.x)))-left+2,h=Math.ceil(Math.max(...corners.map(p=>p.y)))-top+2;
    let raster=rasters.get(rasterKey);
    if(!raster){const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.imageSmoothingEnabled=false;ctx.setTransform(matrix.a,matrix.b,matrix.c,matrix.d,-left,-top);ctx.drawImage(body.canvas,-body.foot.x,-body.foot.y);ctx.setTransform(1,0,0,1,0,0);const raw=ctx.getImageData(0,0,w,h),opaque=[];for(let y=0;y<h;y++)for(let x=0;x<w;x++)if(raw.data[(y*w+x)*4+3]>=24)opaque.push({x,y});raster={canvas,raw,opaque};rasters.set(rasterKey,raster);if(rasters.size>160)rasters.delete(rasters.keys().next().value);}
    const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(raster.canvas,0,0);
    const pixels=new ImageData(new Uint8ClampedArray(raster.raw.data),w,h),points=[];let clipped=false;
    for(const local of raster.opaque){const {x,y}=local,i=(y*w+x)*4+3,wx=actor.x+left+x+.5,wy=actor.y+top+y+.5;
      if(pathClear&&!pathClear(actor.x,actor.y,wx,wy)){pixels.data[i]=0;clipped=true;continue;}
      points.push({x:wx,y:wy});
    }
    if(clipped)ctx.putImageData(pixels,0,0);
    const projection={body,matrix,canvas,pixels:pixels.data,x:actor.x+left,y:actor.y+top,width:w,height:h,points,sourceURL:body.sourceURL,rect:body.rect,anchor:body.anchor,length,across,revision};projectionCache.set(actor,{key,projection,world:G.World,revision,clip:pathClear,path:G.World?.projectilePathClear,block:G.World?.projectileBlock});return projection;
  }
  function contains(projection,x,y){if(!projection)return false;const px=Math.floor(x-projection.x),py=Math.floor(y-projection.y);return px>=0&&py>=0&&px<projection.width&&py<projection.height&&projection.pixels[(py*projection.width+px)*4+3]>=24;}
  function groundContact(projection,polygon,inside){if(!projection)return null;for(const point of projection.points)if(inside(polygon,point.x,point.y,0))return {...point};return null;}
  function drawProjection(ctx,projection,alpha=1){if(!projection)return;ctx.save();ctx.globalAlpha*=alpha;ctx.imageSmoothingEnabled=false;ctx.drawImage(projection.canvas,projection.x,projection.y);ctx.restore();}
  function archPoint(arc,u){
    u=clamp(u);const s=Math.sin(Math.PI*u);return {x:arc.source.x+(arc.destination.x-arc.source.x)*u+arc.normal.x*arc.sideBow*s,y:arc.source.y+(arc.destination.y-arc.source.y)*u+arc.normal.y*arc.sideBow*s,z:arc.destination.z*u+arc.lift*s};
  }
  function makeArch(owner,target,origin,index,width=5){
    const source={x:origin.x,y:origin.y,z:0},destination={x:target.x,y:target.y,z:Math.max(8,(target.bodyH||24)*.45)},dx=destination.x-source.x,dy=destination.y-source.y,d=Math.hypot(dx,dy)||1,H=64*(owner.anim?.scale||1),normal={x:-dy/d,y:dx/d};
    return {owner,target,source,destination,normal,sideBow:H*(.9+.3*(index%3))*(index%2?-1:1)*Math.abs(normal.x)**3,lift:Math.max(H*1.3,Math.abs(dy)/Math.PI+H*.7),width,progress:0,previous:{...source},current:{...source},points:[{...source}],phase:'ground',hit:false,blocked:false};
  }
  function sweptBody(arc,previous,current,body,pathClear){
    if(!body)return null;const target=arc.target,d=Math.hypot(current.x-previous.x,current.y-previous.y,current.z-previous.z),steps=Math.max(1,Math.ceil(d/3));
    for(let i=1;i<=steps;i++){const u=i/steps,p={x:previous.x+(current.x-previous.x)*u,y:previous.y+(current.y-previous.y)*u,z:previous.z+(current.z-previous.z)*u};
      if(pathClear&&!pathClear(previous.x,previous.y,p.x,p.y))return null;
      if(p.z<0||p.z>body.bodyHeight+2||Math.hypot(p.x-target.x,p.y-target.y)>(target.r||12)+3)continue;
      if(alphaAt(body,p.x-target.x+body.foot.x,p.y-p.z-target.y+body.foot.y)>=24)return p;
    }return null;
  }
  function advanceArch(arc,progress,pathClear){
    const previous=arc.current;arc.previous={...previous};arc.progress=clamp(progress);arc.current=archPoint(arc,arc.progress);
    arc.blocked=!!pathClear&&!pathClear(previous.x,previous.y,arc.current.x,arc.current.y);
    const steps=Math.max(2,Math.ceil(48*arc.progress));arc.points=Array.from({length:steps+1},(_,i)=>archPoint(arc,arc.progress*i/steps));
    const slope=(arc.destination.y-arc.source.y)-arc.destination.z+Math.PI*(arc.normal.y*arc.sideBow-arc.lift)*Math.cos(Math.PI*arc.progress);
    arc.phase=arc.progress>=1?'contact':Math.abs(slope)<8?'crest':slope>0?'descent':'rise';return arc.current;
  }
  function drawArch(ctx,arc,alpha=1){
    if(arc.points.length<2||arc.progress<=0||arc.blocked)return;const points=arc.points.map(p=>({x:p.x,y:p.y-p.z}));ctx.save();ctx.globalAlpha*=alpha;ctx.fillStyle='#030304';ctx.beginPath();
    for(let side=0;side<2;side++)for(let j=0;j<points.length;j++){const i=side?points.length-1-j:j,p=points[i],a=points[Math.max(0,i-1)],b=points[Math.min(points.length-1,i+1)],dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1,u=arc.progress*i/(points.length-1),w=arc.width*(.5+1.1*Math.sin(Math.PI*u)**.8)*Math.min(1,(arc.progress-u)/.18)*(side?-1:1);if(!side&&!j)ctx.moveTo(p.x-dy/d*w,p.y+dx/d*w);else ctx.lineTo(p.x-dy/d*w,p.y+dx/d*w);}ctx.closePath();ctx.fill();ctx.restore();
  }
  G.ShikamaruReferenceGeometry={bodyFor,alphaAt,project,contains,groundContact,drawProjection,archPoint,makeArch,sweptBody,advanceArch,drawArch,beginFrame(){revision++;},invalidateWorld(){revision++;}};
})();
