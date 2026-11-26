/* Reference-driven shadows: actual body alpha, ground projection, and swept xyz tips. */
(() => {
  const masks=new Map(),readyBases=new Map(),projectionCache=new WeakMap(),nativePolicies=new WeakSet(),scans=new Map(),clearScans=new Map();let revision=0,forcedRevision=0;
  const nativeWorld=G.World,nativeBlock=nativeWorld?.projectileBlock,nativePath=nativeWorld?.projectilePathClear,nativeWall=nativeWorld?.isWall,nativeWalkable=nativeWorld?.walkable;
  function isNativePolicy(clip){
    const world=G.World;
    return !!clip&&nativePolicies.has(clip)&&world?.projectileBlock===nativeBlock&&world?.projectilePathClear===nativePath&&world?.isWall===nativeWall&&world?.walkable===nativeWalkable;
  }
  function isRegionClear(minX,minY,maxX,maxY,clip){
    const world=G.World;
    if(!clip)return true;
    if(!isNativePolicy(clip)||!world?.isWall||!world?.walkable)return false;
    const tile=world.TS||32,x0=Math.floor(minX/tile)-1,y0=Math.floor(minY/tile)-1,x1=Math.floor(maxX/tile)+1,y1=Math.floor(maxY/tile)+1;
    const region=x0+':'+y0+':'+x1+':'+y1+':'+forcedRevision;
    const cached=clearScans.get(region);
    if(cached?.world===world)return cached.clear;
    let clear=true;
    outer:for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++){
      if(world.isWall((x+.5)*tile,(y+.5)*tile)||!world.walkable(x,y)){clear=false;break outer;}
    }
    if(clearScans.size>512)clearScans.clear();
    clearScans.set(region,{world,clear});
    return clear;
  }
  function lineClear(ax,ay,bx,by,clip){
    if(!clip)return true;
    if(!isNativePolicy(clip))return clip(ax,ay,bx,by);
    const minX=Math.min(ax,bx),minY=Math.min(ay,by),w=Math.abs(bx-ax)+2,h=Math.abs(by-ay)+2;
    const obs=obstacleState({x:ax,y:ay},minX-ax-1,minY-ay-1,w+2,h+2,clip);
    return !obs.blocked||nativeVisible(ax,ay,bx,by,obs);
  }
  function polylineClear(owner,points,clip){
    if(!points.length)return true;
    if(!clip)return true;
    if(!isNativePolicy(clip))return clip(owner.x,owner.y,points[0].x,points[0].y)&&!points.some((p,i,list)=>i&&!clip(list[i-1].x,list[i-1].y,p.x,p.y));
    let minX=owner.x,maxX=owner.x,minY=owner.y,maxY=owner.y;
    for(const p of points){if(p.x<minX)minX=p.x;if(p.x>maxX)maxX=p.x;if(p.y<minY)minY=p.y;if(p.y>maxY)maxY=p.y;}
    const obs=obstacleState(owner,minX-owner.x-1,minY-owner.y-1,maxX-minX+2,maxY-minY+2,clip);
    if(!obs.blocked)return true;
    if(!nativeVisible(owner.x,owner.y,points[0].x,points[0].y,obs))return false;
    for(let i=1;i<points.length;i++)if(!nativeVisible(points[i-1].x,points[i-1].y,points[i].x,points[i].y,obs))return false;
    return true;
  }
  function isPointOpen(x,y,pad,clip){
    const world=G.World;
    if(!clip)return true;
    if(!isNativePolicy(clip)||!world?.isWall||!world?.walkable)return false;
    const tile=world.TS||32,x0=Math.floor((x-pad)/tile)-1,y0=Math.floor((y-pad)/tile)-1,x1=Math.floor((x+pad)/tile)+1,y1=Math.floor((y+pad)/tile)+1;
    for(let ty=y0;ty<=y1;ty++)for(let tx=x0;tx<=x1;tx++)if(world.isWall((tx+.5)*tile,(ty+.5)*tile)||!world.walkable(tx,ty))return false;
    return true;
  }
  function obstacleState(actor,left,top,w,h,clip){
    const world=G.World;
    if(!clip)return {key:'open:'+forcedRevision,blocked:false,native:true};
    if(!isNativePolicy(clip))return {key:'custom:'+revision+':'+forcedRevision,blocked:true,native:false};
    const tile=world.TS||32,x0=Math.floor((Math.min(actor.x,actor.x+left)-1)/tile)-1,y0=Math.floor((Math.min(actor.y,actor.y+top)-1)/tile)-1,x1=Math.floor((Math.max(actor.x,actor.x+left+w)+1)/tile)+1,y1=Math.floor((Math.max(actor.y,actor.y+top+h)+1)/tile)+1;
    const region=[x0,y0,x1,y1,forcedRevision].join(':');let state=scans.get(region);if(state?.world===world)return state;
    let bits='';const rectangles=[],circles=[];
    for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++){
      const wall=world.isWall((x+.5)*tile,(y+.5)*tile);if(wall){rectangles.push({left:x*tile,top:y*tile,right:(x+1)*tile,bottom:(y+1)*tile});bits+='w';continue;}
      if(!world.walkable(x,y)){
        // Native makeProp anchors solid props at the tile's lower foot point.
        const prop=world.projectileBlock((x+.5)*tile,(y+1)*tile-4,0);
        if(prop&&prop!=='wall'&&!circles.some(p=>p.id===prop.id)){circles.push({id:prop.id,x:prop.x,y:prop.y,r:prop.r+1});bits+='p'+prop.id+','+prop.x+','+prop.y+','+prop.r+';';continue;}
      }bits+='.';
    }
    state={world,key:region+':'+bits,blocked:rectangles.length+circles.length>0,native:true,rectangles,circles};scans.set(region,state);return state;
  }
  function nativeVisible(ax,ay,bx,by,obstacles){
    const dx=bx-ax,dy=by-ay,length2=dx*dx+dy*dy;
    for(const circle of obstacles.circles){const t=Math.max(0,Math.min(1,((circle.x-ax)*dx+(circle.y-ay)*dy)/(length2||1)));if((ax+t*dx-circle.x)**2+(ay+t*dy-circle.y)**2<circle.r*circle.r)return false;}
    for(const wall of obstacles.rectangles){
      let near=0,far=1;
      if(Math.abs(dx)<1e-12){if(ax<wall.left||ax>=wall.right)continue;}else{const a=(wall.left-ax)/dx,b=(wall.right-ax)/dx;near=Math.max(near,Math.min(a,b));far=Math.min(far,Math.max(a,b));}
      if(Math.abs(dy)<1e-12){if(ay<wall.top||ay>=wall.bottom)continue;}else{const a=(wall.top-ay)/dy,b=(wall.bottom-ay)/dy;near=Math.max(near,Math.min(a,b));far=Math.min(far,Math.max(a,b));}
      if(near<far&&far>0&&near<=1)return false;
    }return true;
  }
  const clamp=x=>Math.max(0,Math.min(1,x));
  function bodyFor(actor){
    const dex=actor.mon?.dex??actor.dex,anim=actor.anim;if(!anim)return null;
    let image,rect,anchor,k,key,url,mirror=false,compositeFrame=null,paintComposite=null;
    if(dex===30017){
      const art=G.ShikamaruArt;if(!art?.loaded)return null;
      const active=G.NarutoShikamaru?.activeFor(actor),pose=active?{...active,walkTime:(anim.frame*6+anim.t)/60}:null,state=actor.dead||anim.cur==='Faint'?'faint':actor.flash>0||anim.cur==='Hurt'?'hurt':pose?'cast':anim.cur==='Walk'?'walk':'idle';
      const time=pose?.age??(anim.frame*6+anim.t)/60,dir=pose&&!pose.moving&&Number.isFinite(pose.aim)?G.Sprites.dirFromAngle(pose.aim):anim.dir;
      const frame=art.sample(state,time,dir,pose);if(!frame)return null;
      image=art.images.body;rect=frame.rect;anchor=frame.anchor;k=64*(anim.scale||1)/frame.bodyHeight;mirror=frame.direction==='left';key='shika:'+frame.key+':'+frame.direction+':'+k;url=frame.source;
      if(frame.lowerFrame&&art.paint){compositeFrame=frame;paintComposite=art.paint;key+=':'+frame.lowerFrame.key+':'+frame.lowerFrame.direction+':'+frame.splitHeight;}
    }else{
      let name=anim.cur,sheet=G.Sprites.sheet(dex,name,anim.shiny),meta=G.Sprites.animMeta(dex,name,anim.shiny),frame=anim.frame;
      if(!sheet?.ready){name='Idle';sheet=G.Sprites.sheet(dex,name,anim.shiny);meta=G.Sprites.animMeta(dex,name,anim.shiny);frame=0;}
      if(!sheet?.ready||!meta)return null;
      k=G.Sprites.PX*(anim.scale||1);image=sheet.img;rect=[Math.min(frame,meta.n-1)*meta.w,Math.min(anim.dir,meta.r-1)*meta.h,meta.w,meta.h];anchor=[meta.ax,meta.ay];key=[dex,name,frame,anim.dir,k,anim.shiny].join(':');url=image.src;
    }
    if(masks.has(key))return masks.get(key);
    const canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.ceil(rect[2]*k));canvas.height=Math.max(1,Math.ceil(rect[3]*k));const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.imageSmoothingEnabled=false;
    const foot={x:mirror?canvas.width-anchor[0]*k:anchor[0]*k,y:anchor[1]*k};
    if(compositeFrame)paintComposite(ctx,compositeFrame,{x:foot.x,y:foot.y,height:64*(anim.scale||1)});
    else{if(mirror){ctx.translate(canvas.width,0);ctx.scale(-1,1);}ctx.drawImage(image,...rect,0,0,rect[2]*k,rect[3]*k);}
    ctx.setTransform(1,0,0,1,0,0);ctx.globalCompositeOperation='source-in';ctx.fillStyle='#030304';ctx.fillRect(0,0,canvas.width,canvas.height);
    const data=ctx.getImageData(0,0,canvas.width,canvas.height).data;
    let top=foot.y;const support=Array.from({length:32},(_,i)=>({dx:Math.cos(i*Math.PI/16),dy:Math.sin(i*Math.PI/16),dot:-Infinity,point:null}));
    // Scan a source frame once, never a transformed projection or a collision area.
    for(let y=0;y<canvas.height;y++){let left=canvas.width,right=-1;for(let x=0;x<canvas.width;x++)if(data[(y*canvas.width+x)*4+3]>24){left=Math.min(left,x);right=x;top=Math.min(top,y);}if(right<0)continue;for(const x of [left,right])for(const v of support){const dot=(x+.5)*v.dx+(y+.5)*v.dy;if(dot>v.dot){v.dot=dot;v.point={x:x+.5,y:y+.5};}}}
    const silhouette=support.map(v=>v.point).filter((v,i,list)=>v&&(!i||v.x!==list[i-1]?.x||v.y!==list[i-1]?.y));
    const body={key,canvas,data,silhouette,width:canvas.width,height:canvas.height,foot,bodyHeight:Math.max(1,foot.y-top),sourceURL:url,rect:rect.slice(),anchor:anchor.slice(),scale:k,mirror};
    masks.set(key,body);if(masks.size>512)masks.delete(masks.keys().next().value);return body;
  }
  function alphaAt(body,x,y){x=Math.floor(x);y=Math.floor(y);return x>=0&&y>=0&&x<body.width&&y<body.height?body.data[(y*body.width+x)*4+3]:0;}
  function insidePolygon(poly,x,y){let inside=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if((a.y>y)!==(b.y>y)&&x<(b.x-a.x)*(y-a.y)/(b.y-a.y)+a.x)inside=!inside;}return inside;}
  function readyBaseFor(actor){
    const scale=actor.anim?.scale||1,key='shika-ready-base:'+scale;if(readyBases.has(key))return readyBases.get(key);
    const canvas=document.createElement('canvas');canvas.width=canvas.height=Math.max(1,Math.ceil(80*scale));
    const foot={x:40*scale,y:40*scale};
    // Clean, grounded oval shadow pool centered under Shikamaru's feet (replaces
    // the awkward 4-pronged star/amoeba cutout while keeping ground perspective).
    const rx=21.5*scale,ry=18.8*scale,count=48;
    const points=Array.from({length:count},(_,i)=>{
      const a=i*Math.PI*2/count;
      return {x:foot.x+Math.cos(a)*rx,y:foot.y+Math.sin(a)*ry};
    });
    const data=new Uint8ClampedArray(canvas.width*canvas.height*4),ctx=canvas.getContext('2d');
    ctx.fillStyle='#040307';
    for(let y=0;y<canvas.height;y++)for(let x=0;x<canvas.width;){
      if(!insidePolygon(points,x+.5,y+.5)){x++;continue;}
      const start=x++;while(x<canvas.width&&insidePolygon(points,x+.5,y+.5))x++;
      ctx.fillRect(start,y,x-start,1);
      for(let px=start;px<x;px++){const i=(y*canvas.width+px)*4;data[i]=4;data[i+1]=3;data[i+2]=7;data[i+3]=255;}
    }
    const body={kind:'ready-base',key,canvas,shadowCanvas:canvas,data,silhouette:points,width:canvas.width,height:canvas.height,foot,bodyHeight:64*scale,sourceURL:'procedural:nara-ready-pool',rect:[0,0,canvas.width,canvas.height],anchor:[foot.x,foot.y],scale,mirror:false};
    readyBases.set(key,body);if(readyBases.size>24)readyBases.delete(readyBases.keys().next().value);return body;
  }
  function visibility(actor,radius,obstacle,pathClear){
    const angles=Array.from({length:48},(_,i)=>i*Math.PI/24);
    if(obstacle.native)for(const wall of obstacle.rectangles)for(const [x,y]of [[wall.left,wall.top],[wall.right,wall.top],[wall.right,wall.bottom],[wall.left,wall.bottom]]){const angle=Math.atan2(y-actor.y,x-actor.x);angles.push(angle-.00001,angle,angle+.00001);}
    return angles.sort((a,b)=>a-b).map(angle=>{
      const dx=Math.cos(angle)*radius,dy=Math.sin(angle)*radius;
      const clear=t=>obstacle.native?nativeVisible(actor.x,actor.y,actor.x+dx*t,actor.y+dy*t,obstacle):pathClear(actor.x,actor.y,actor.x+dx*t,actor.y+dy*t);
      let low=0,high=1;if(clear(1))low=1;else for(let i=0;i<10;i++){const t=(low+high)/2;if(clear(t))low=t;else high=t;}
      return {x:actor.x+dx*low,y:actor.y+dy*low};
    });
  }
  function flowRow(body,flow,y){
    if(!flow)return {scale:1,offset:0};
    const row=Math.floor(y/flow.band)*flow.band,sample=row+Math.min(flow.band,body.height-row)*.5;
    const distance=body.kind==='ready-base'?Math.abs(body.foot.y-sample)/(body.bodyHeight*.65):(body.foot.y-sample)/body.bodyHeight;
    const u=clamp(distance),envelope=u*(.45+.55*Math.sin(Math.PI*u*.85));
    const phase=flow.phase*2.4-u*4.6+flow.seed+(body.kind==='ready-base'&&sample>body.foot.y?1.3:0);
    return {scale:1+envelope*(.18*Math.sin(phase)+.04*Math.sin(phase*1.7+.8)),offset:envelope*flow.strength*(5.8*Math.sin(phase)+1.8*Math.sin(flow.phase*1.3+u*6.2+flow.seed))};
  }
  function opaqueShadow(body){
    if(body.shadowCanvas)return body.shadowCanvas;
    const canvas=document.createElement('canvas');canvas.width=body.width;canvas.height=body.height;
    const ctx=canvas.getContext('2d');ctx.fillStyle='#030304';
    // Reuse the cached source alpha and the same contact threshold. This is
    // built once per body frame, never read back from a moving projection.
    for(let y=0;y<body.height;y++)for(let x=0;x<body.width;){
      if(body.data[(y*body.width+x)*4+3]<24){x++;continue;}
      const start=x++;while(x<body.width&&body.data[(y*body.width+x)*4+3]>=24)x++;
      ctx.fillRect(start,y,x-start,1);
    }
    body.shadowCanvas=canvas;return canvas;
  }
  function readyOutline(body,matrix,material){
    const scale=body.scale,phase=material?.phase||0,seed=material?.seed||0,feeds=material?.feeds||[];
    // Subtle volume conservation: when shadow mass flows outward into active tongues,
    // the non-feeding side of the foot pool tightens slightly while keeping feet planted.
    let activeLoad=0;
    for(const f of feeds)activeLoad=Math.max(activeLoad,clamp(f.pull/(22*scale)));
    const conserve=1-.13*activeLoad;
    return body.silhouette.map((p,idx)=>{
      const bx=(p.x-body.foot.x),by=(p.y-body.foot.y)*matrix.d;
      const ang=Math.atan2(by,bx);
      // Calm, organic liquid rim breathing (no erratic sideways sloshing).
      const ripple=1+.055*Math.sin(ang*3-phase*3.2+seed)+.035*Math.cos(ang*2+phase*2.3+seed*.7);
      const driftX=1.15*scale*Math.sin(phase*2.6+ang*2+seed);
      const driftY=.7*scale*Math.cos(phase*2.2-ang*3+seed);
      let x=bx*ripple*conserve+driftX,y=by*ripple*conserve+driftY;
      const r=Math.hypot(x,y)||1,ux=x/r,uy=y/r;
      // Smooth liquid meniscus funnel pulled toward the active shadow cast direction.
      let strongest=0,moveX=0,moveY=0;
      for(const feed of feeds){
        const cosA=ux*feed.dx+uy*feed.dy;
        if(cosA<=0)continue;
        const focus=Math.pow(cosA,2.6);
        const pullAmt=feed.pull*.68*focus;
        const sideProj=-x*feed.dy+y*feed.dx;
        const waist=Math.pow(cosA,1.4)*(1-focus*.45)*feed.pinch*.55;
        const influence=pullAmt+Math.abs(sideProj)*waist;
        if(influence<=strongest)continue;
        strongest=influence;
        moveX=feed.dx*pullAmt+feed.dy*(sideProj*waist);
        moveY=feed.dy*pullAmt-feed.dx*(sideProj*waist);
      }
      return {x:matrix.e+x+moveX,y:matrix.f+y+moveY};
    });
  }
  function project(actor,dx,dy,length,across=.65,pathClear=null,flow=null){
    const body=flow?.readyBase?readyBaseFor(actor):bodyFor(actor);if(!body)return null;const d=Math.hypot(dx,dy)||1;dx/=d;dy/=d;length=Math.max(1,length);
    const bandDiv=body.kind==='ready-base'?32:6;
    const material=flow?{phase:Number(flow.phase)||0,seed:Number(flow.seed)||0,band:Math.max(body.kind==='ready-base'?1:4,Math.floor(body.bodyHeight/bandDiv)),strength:Math.max(.6,Math.min(2,body.bodyHeight/64))*(Number(flow.strength)||1)}:null;
    if(material&&body.kind==='ready-base'){material.feeds=(flow.feeds||[]).map(feed=>({...feed}));material.revision=Number(flow.revision)||0;}
    const key=[body.key,dx,dy,length,across,actor.x,actor.y,material?.phase??'',material?.seed??'',material?.strength??'',material?.revision??'',...(material?.feeds||[]).map(feed=>[feed.sourceCast,feed.segment,feed.stage,feed.dx,feed.dy,feed.pull,feed.pinch,feed.reach,feed.neckWidth].join(':'))].join('|'),old=projectionCache.get(actor);
    const nativeFast=!pathClear||isNativePolicy(pathClear);
    if(old?.key===key&&old.world===G.World&&old.clip===pathClear&&old.path===G.World?.projectilePathClear&&old.block===G.World?.projectileBlock&&old.forcedRevision===forcedRevision&&nativeFast&&old.obstacleNative)return old.projection;
    const matrix=body.kind==='ready-base'?{a:1,b:0,c:0,d:.65,e:actor.x,f:actor.y}:{a:-dy*across,b:dx*across,c:-dx*length/body.bodyHeight,d:-dy*length/body.bodyHeight,e:actor.x,f:actor.y};
    const transform=(p,warp=flowRow(body,material,p.y))=>{const x=(p.x-body.foot.x)*warp.scale+warp.offset,y=p.y-body.foot.y;return {x:matrix.a*x+matrix.c*y+actor.x,y:matrix.b*x+matrix.d*y+actor.y};};
    const outline=body.kind==='ready-base'?readyOutline(body,matrix,material):null,hull=outline||body.silhouette.map(p=>transform(p));
    let minX=Infinity,minY=Infinity,maxX=-Infinity,maxY=-Infinity;
    const include=p=>{if(p.x<minX)minX=p.x;if(p.x>maxX)maxX=p.x;if(p.y<minY)minY=p.y;if(p.y>maxY)maxY=p.y;};
    if(outline)for(const p of outline)include(p);
    else if(material){
      for(let y=0;y<body.height;y+=material.band){const h=Math.min(material.band,body.height-y),warp=flowRow(body,material,y+.5);for(const x of [0,body.width]){include(transform({x,y},warp));include(transform({x,y:y+h},warp));}}
    }else for(const [x,y]of [[0,0],[body.width,0],[body.width,body.height],[0,body.height]])include(transform({x,y}));
    const left=Math.floor(minX)-1,top=Math.floor(minY)-1,w=Math.ceil(maxX)-left+2,h=Math.ceil(maxY)-top+2;
    const obstacle=obstacleState(actor,left-actor.x,top-actor.y,w,h,pathClear);
    if(old?.key===key&&old.world===G.World&&old.obstacleKey===obstacle.key&&old.clip===pathClear&&old.path===G.World?.projectilePathClear&&old.block===G.World?.projectileBlock)return old.projection;
    const clipRadius=Math.hypot(w,h)+Math.hypot(left-actor.x,top-actor.y)+2;
    const reuseClip=obstacle.blocked&&obstacle.native&&old?.clipPoly&&old.obstacleKey===obstacle.key&&old.actorX===actor.x&&old.actorY===actor.y&&old.clipRadius>=clipRadius;
    const clip=obstacle.blocked?(reuseClip?old.clipPoly:visibility(actor,clipRadius+8,obstacle,pathClear)):null;
    const visible=p=>!obstacle.blocked||(obstacle.native?nativeVisible(actor.x,actor.y,p.x,p.y,obstacle):pathClear(actor.x,actor.y,p.x,p.y));
    const canvas=old?.projection.canvas||document.createElement('canvas');
    const needResize=canvas.width<w||canvas.height<h||canvas.width>w+64||canvas.height>h+64;
    if(needResize){canvas.width=w;canvas.height=h;}
    const ctx=canvas.getContext('2d');
    if(!needResize)ctx.clearRect?.(0,0,w,h);
    ctx.imageSmoothingEnabled=false;ctx.save();
    if(clip){ctx.beginPath();clip.forEach((p,i)=>i?ctx.lineTo(p.x-left,p.y-top):ctx.moveTo(p.x-left,p.y-top));ctx.closePath();ctx.clip();}
    if(outline){
      ctx.fillStyle='#040307';ctx.beginPath();outline.forEach((p,i)=>i?ctx.lineTo(p.x-left,p.y-top):ctx.moveTo(p.x-left,p.y-top));ctx.closePath();ctx.fill();
    }else if(material){
      ctx.setTransform(matrix.a,matrix.b,matrix.c,matrix.d,actor.x-left,actor.y-top);
      const source=opaqueShadow(body);
      // Slight band overlap seals sub-pixel seams without expensive self-blits.
      for(let row=0;row<body.height;row+=material.band){const sh=Math.min(material.band,body.height-row),warp=flowRow(body,material,row+.5);ctx.drawImage(source,0,row,body.width,sh,-body.foot.x*warp.scale+warp.offset,row-body.foot.y,body.width*warp.scale,sh+.6);}
    }else{ctx.setTransform(matrix.a,matrix.b,matrix.c,matrix.d,actor.x-left,actor.y-top);ctx.drawImage(body.canvas,-body.foot.x,-body.foot.y);}
    ctx.restore();
    const projection={body,matrix,flow:material,canvas,x:left,y:top,width:w,height:h,points:hull.filter(visible),hull,clip,visible,sourceURL:body.sourceURL,rect:body.rect,anchor:body.anchor,length,across,revision};
    if(outline){projection.readyOutline=outline;projection.feeds=material?.feeds||[];}
    else if(material)projection.points=projection.points.filter(p=>contains(projection,p.x,p.y));
    projectionCache.set(actor,{key,projection,world:G.World,obstacleKey:obstacle.key,obstacleNative:!!obstacle.native,forcedRevision,clip:pathClear,clipPoly:clip,clipRadius:reuseClip?old.clipRadius:clipRadius+8,actorX:actor.x,actorY:actor.y,path:G.World?.projectilePathClear,block:G.World?.projectileBlock});return projection;
  }
  function contains(projection,x,y){
    if(!projection||!projection.visible({x,y}))return false;
    if(projection.readyOutline){
      const outline=projection.readyOutline;if(insidePolygon(outline,x,y))return true;
      return outline.some((a,i)=>{const b=outline[(i+1)%outline.length],dx=b.x-a.x,dy=b.y-a.y,t=clamp(((x-a.x)*dx+(y-a.y)*dy)/(dx*dx+dy*dy||1));return Math.hypot(x-a.x-dx*t,y-a.y-dy*t)<1e-6;});
    }
    const {matrix:m,body}=projection,det=m.a*m.d-m.b*m.c;if(!det)return false;
    const px=x-m.e,py=y-m.f,sourceY=(-m.b*px+m.a*py)/det+body.foot.y,warp=flowRow(body,projection.flow,sourceY);
    const sourceX=((m.d*px-m.c*py)/det-warp.offset)/warp.scale+body.foot.x;
    return alphaAt(body,sourceX,sourceY)>=24;
  }
  function intersection(a,b,c,d){
    const dx=b.x-a.x,dy=b.y-a.y,ex=d.x-c.x,ey=d.y-c.y,det=dx*ey-dy*ex;if(Math.abs(det)<1e-9)return null;
    const u=((c.x-a.x)*ey-(c.y-a.y)*ex)/det,v=((c.x-a.x)*dy-(c.y-a.y)*dx)/det;
    return u>=0&&u<=1&&v>=0&&v<=1?{x:a.x+dx*u,y:a.y+dy*u}:null;
  }
  function groundContact(projection,polygon,inside=insidePolygon){
    if(!projection||polygon.length<3)return null;
    for(const p of polygon)if(contains(projection,p.x,p.y))return {...p};
    for(const p of projection.points)if(inside(polygon,p.x,p.y,0))return {...p};
    // At most 32 silhouette support edges; work is independent of sprite pixels.
    for(let i=0;i<polygon.length;i++)for(let j=0;j<projection.hull.length;j++){
      const p=intersection(polygon[i],polygon[(i+1)%polygon.length],projection.hull[j],projection.hull[(j+1)%projection.hull.length]);
      if(p&&contains(projection,p.x,p.y))return p;
    }return null;
  }
  function drawProjection(ctx,projection,alpha=1){if(!projection)return;ctx.save();ctx.globalAlpha*=alpha;ctx.imageSmoothingEnabled=false;ctx.drawImage(projection.canvas,0,0,projection.width,projection.height,projection.x,projection.y,projection.width,projection.height);ctx.restore();}
  function archPoint(arc,u){
    u=clamp(u);const s=Math.sin(Math.PI*u);return {x:arc.source.x+(arc.destination.x-arc.source.x)*u+arc.normal.x*arc.sideBow*s,y:arc.source.y+(arc.destination.y-arc.source.y)*u+arc.normal.y*arc.sideBow*s,z:arc.destination.z*u+arc.lift*s};
  }
  function makeArch(owner,target,origin,index,width=5){
    const source={x:origin.x,y:origin.y,z:0},destination={x:target.x,y:target.y,z:Math.max(8,(target.bodyH||24)*.45)},dx=destination.x-source.x,dy=destination.y-source.y,d=Math.hypot(dx,dy)||1,H=64*(owner.anim?.scale||1),normal={x:-dy/d,y:dx/d};
    return {owner,target,source,destination,normal,sideBow:H*(.9+.3*(index%3))*(index%2?-1:1)*Math.abs(normal.x)**3,lift:Math.max(H*1.3,Math.abs(dy)/Math.PI+H*.7),width,progress:0,previous:{...source},current:{...source},points:[{...source}],phase:'ground',hit:false,blocked:false};
  }
  function sweptBody(arc,previous,current,body,pathClear){
    if(!body||pathClear&&!pathClear(previous.x,previous.y,current.x,current.y))return null;
    const target=arc.target,dx=current.x-previous.x,dy=current.y-previous.y,dz=current.z-previous.z,ox=previous.x-target.x,oy=previous.y-target.y,r=(target.r||12)+Math.max(2,(arc.width||0)/2);
    let low=0,high=1;const a=dx*dx+dy*dy,b=2*(ox*dx+oy*dy),c=ox*ox+oy*oy-r*r;
    if(a<1e-12){if(c>0)return null;}else{const det=b*b-4*a*c;if(det<0)return null;const root=Math.sqrt(det);low=Math.max(low,(-b-root)/(2*a));high=Math.min(high,(-b+root)/(2*a));}
    if(Math.abs(dz)<1e-12){if(previous.z<0||previous.z>body.bodyHeight+2)return null;}else{const bottom=-previous.z/dz,top=(body.bodyHeight+2-previous.z)/dz;low=Math.max(low,Math.min(bottom,top));high=Math.min(high,Math.max(bottom,top));}
    if(low>high)return null;return {x:previous.x+dx*low,y:previous.y+dy*low,z:previous.z+dz*low};
  }
  function advanceArch(arc,progress,pathClear){
    const previous=arc.current;arc.previous={...previous};arc.progress=clamp(progress);arc.current=archPoint(arc,arc.progress);
    arc.blocked=!!pathClear&&!pathClear(previous.x,previous.y,arc.current.x,arc.current.y);
    const steps=Math.max(2,Math.ceil(48*arc.progress));arc.points=Array.from({length:steps+1},(_,i)=>archPoint(arc,arc.progress*i/steps));
    const slope=(arc.destination.y-arc.source.y)-arc.destination.z+Math.PI*(arc.normal.y*arc.sideBow-arc.lift)*Math.cos(Math.PI*arc.progress);
    arc.phase=arc.progress>=1?'contact':Math.abs(slope)<8?'crest':slope>0?'descent':'rise';return arc.current;
  }
  const archGrain=new Float32Array(512);
  for(let i=0;i<archGrain.length;i++){const v=Math.sin(i*127.1+311.7)*43758.5453;archGrain[i]=v-Math.floor(v);}
  const px2=v=>Math.round(v*.5)*2;
  function drawArch(ctx,arc,alpha=1,remaining=1,from=0,to=1,ultimate=false){
    if(arc.points.length<2||arc.progress<=0||arc.blocked||remaining<=0)return;
    const progress=arc.progress*clamp(remaining),start=Math.min(progress,clamp(from)),end=Math.min(progress,clamp(to));if(end<=start)return;
    const steps=Math.max(4,Math.ceil(48*(end-start))),spine=start>0||end<arc.progress||remaining<1?Array.from({length:steps+1},(_,i)=>archPoint(arc,start+(end-start)*i/steps)):arc.points;
    const points=spine.map(p=>({x:p.x,y:p.y-p.z}));
    const widthAt=u=>{
      const tipTaper=Math.pow(clamp((progress-u)/Math.max(.14,progress*.42)),.72);
      const bodyProfile=1.22-.52*Math.pow(u,.58)+.22*Math.sin(Math.PI*Math.min(1,u*1.15));
      return arc.width*bodyProfile*tipTaper;
    };
    ctx.save();
    // Soft dark-ink fringe blends the needle silhouette into the pixel ground/air.
    ctx.globalAlpha=alpha*.34;ctx.fillStyle=ultimate?'#1f1024':'#151022';ctx.beginPath();
    for(let side=0;side<2;side++)for(let j=0;j<points.length;j++){
      const i=side?points.length-1-j:j,p=points[i],a=points[Math.max(0,i-1)],b=points[Math.min(points.length-1,i+1)],dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1;
      const u=start+(end-start)*i/(points.length-1),w=(widthAt(u)+(u<progress-.03?1.4:0))*(side?-1:1);
      if(!side&&!j)ctx.moveTo(p.x-dy/d*w,p.y+dx/d*w);else ctx.lineTo(p.x-dy/d*w,p.y+dx/d*w);
    }
    ctx.closePath();ctx.fill();
    // Core razor shadow body.
    ctx.globalAlpha=alpha;ctx.fillStyle='#050408';ctx.beginPath();
    for(let side=0;side<2;side++)for(let j=0;j<points.length;j++){
      const i=side?points.length-1-j:j,p=points[i],a=points[Math.max(0,i-1)],b=points[Math.min(points.length-1,i+1)],dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1;
      const u=start+(end-start)*i/(points.length-1),w=widthAt(u)*(side?-1:1);
      if(!side&&!j)ctx.moveTo(p.x-dy/d*w,p.y+dx/d*w);else ctx.lineTo(p.x-dy/d*w,p.y+dx/d*w);
    }
    ctx.closePath();ctx.fill();
    // Faceted blade ridge along the upper edge gives crisp 3D needle sharpness.
    if(points.length>=3){
      ctx.globalAlpha=alpha*(ultimate?.78:.62);ctx.strokeStyle=ultimate?'#5c283c':'#312645';ctx.lineWidth=ultimate?1.8:1.3;ctx.lineCap='butt';ctx.beginPath();
      let started=false;
      for(let i=1;i<points.length-1;i++){
        const u=start+(end-start)*i/(points.length-1);if(u>progress-.04)break;
        const p=points[i],a=points[i-1],b=points[i+1],dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1,off=widthAt(u)*.36;
        const rx=p.x-dy/d*off,ry=p.y+dx/d*off;
        if(!started){ctx.moveTo(rx,ry);started=true;}else ctx.lineTo(rx,ry);
      }
      if(started)ctx.stroke();
    }
    // Pixelated ink motes trailing off the rising shadow needle.
    if((G.Settings?.fx??1)>0&&end-start>.18){
      const seedBase=((Math.abs(Math.round(arc.source.x*7+arc.source.y*13+(arc.pulseIndex||1)*31)))&255);
      ctx.fillStyle=ultimate?'#2a1326':'#14101e';ctx.globalAlpha=alpha*.68*clamp(remaining);
      for(let m=0;m<(ultimate?6:4);m++){
        const g1=archGrain[(seedBase+m*19)&511],g2=archGrain[(seedBase+m*37+11)&511];
        const u=start+(end-start)*(.12+.72*g1);if(u>=progress-.05)continue;
        const idx=Math.min(points.length-1,Math.max(0,Math.round((u-start)/Math.max(1e-4,end-start)*(points.length-1))));
        const p=points[idx],a=points[Math.max(0,idx-1)],b=points[Math.min(points.length-1,idx+1)],dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1;
        const spread=(widthAt(u)+2+3*g2)*(m%2?1:-1);
        ctx.fillRect(px2(p.x-dy/d*spread),px2(p.y+dx/d*spread),2,2);
      }
    }
    ctx.restore();
  }
  G.ShikamaruReferenceGeometry={bodyFor,alphaAt,project,contains,groundContact,drawProjection,archPoint,makeArch,sweptBody,advanceArch,drawArch,isRegionClear,isPointOpen,lineClear,polylineClear,registerNativePolicy(policy){nativePolicies.add(policy);},beginFrame(){revision++;scans.clear();clearScans.clear();},invalidateWorld(){revision++;forcedRevision++;scans.clear();clearScans.clear();}};
  // World is a stable singleton across runs; a reset can replace same-tile props.
  for(const name of ['reset','setBiome','setArena']){
    const previous=G.World?.[name];if(!previous)continue;
    G.World[name]=function(...args){try{return previous.apply(this,args);}finally{G.ShikamaruReferenceGeometry.invalidateWorld();}};
  }
})();
