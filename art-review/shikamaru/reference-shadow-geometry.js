/* Reference-driven shadows: actual body alpha, ground projection, and swept xyz tips. */
(() => {
  const masks=new Map(),projectionCache=new WeakMap(),nativePolicies=new WeakSet(),scans=new Map();let revision=0,forcedRevision=0;
  const nativeWorld=G.World,nativeBlock=nativeWorld?.projectileBlock,nativePath=nativeWorld?.projectilePathClear,nativeWall=nativeWorld?.isWall,nativeWalkable=nativeWorld?.walkable;
  function obstacleState(actor,left,top,w,h,clip){
    const world=G.World;
    if(!clip)return {key:'open:'+forcedRevision,blocked:false};
    if(!nativePolicies.has(clip)||world?.projectileBlock!==nativeBlock||world?.projectilePathClear!==nativePath||world?.isWall!==nativeWall||world?.walkable!==nativeWalkable)return {key:'custom:'+revision+':'+forcedRevision,blocked:true};
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
    masks.set(key,body);if(masks.size>160)masks.delete(masks.keys().next().value);return body;
  }
  function alphaAt(body,x,y){x=Math.floor(x);y=Math.floor(y);return x>=0&&y>=0&&x<body.width&&y<body.height?body.data[(y*body.width+x)*4+3]:0;}
  function insidePolygon(poly,x,y){let inside=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if((a.y>y)!==(b.y>y)&&x<(b.x-a.x)*(y-a.y)/(b.y-a.y)+a.x)inside=!inside;}return inside;}
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
  function project(actor,dx,dy,length,across=.65,pathClear=null){
    const body=bodyFor(actor);if(!body)return null;const d=Math.hypot(dx,dy)||1;dx/=d;dy/=d;length=Math.max(1,length);
    const key=[body.key,dx,dy,length,across,actor.x,actor.y].join('|'),old=projectionCache.get(actor);
    const matrix={a:-dy*across,b:dx*across,c:-dx*length/body.bodyHeight,d:-dy*length/body.bodyHeight,e:actor.x,f:actor.y};
    const transform=p=>({x:matrix.a*(p.x-body.foot.x)+matrix.c*(p.y-body.foot.y)+actor.x,y:matrix.b*(p.x-body.foot.x)+matrix.d*(p.y-body.foot.y)+actor.y});
    const hull=body.silhouette.map(transform),corners=[[0,0],[body.width,0],[body.width,body.height],[0,body.height]].map(([x,y])=>transform({x,y}));
    const left=Math.floor(Math.min(...corners.map(p=>p.x)))-1,top=Math.floor(Math.min(...corners.map(p=>p.y)))-1,w=Math.ceil(Math.max(...corners.map(p=>p.x)))-left+2,h=Math.ceil(Math.max(...corners.map(p=>p.y)))-top+2;
    const obstacle=obstacleState(actor,left-actor.x,top-actor.y,w,h,pathClear);
    if(old?.key===key&&old.world===G.World&&old.obstacleKey===obstacle.key&&old.clip===pathClear&&old.path===G.World?.projectilePathClear&&old.block===G.World?.projectileBlock)return old.projection;
    const clip=obstacle.blocked?visibility(actor,Math.hypot(w,h)+Math.hypot(left-actor.x,top-actor.y)+2,obstacle,pathClear):null;
    const visible=p=>!obstacle.blocked||(obstacle.native?nativeVisible(actor.x,actor.y,p.x,p.y,obstacle):pathClear(actor.x,actor.y,p.x,p.y));
    const canvas=old?.projection.canvas||document.createElement('canvas');canvas.width=w;canvas.height=h;const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.save();
    if(clip){ctx.beginPath();clip.forEach((p,i)=>i?ctx.lineTo(p.x-left,p.y-top):ctx.moveTo(p.x-left,p.y-top));ctx.closePath();ctx.clip();}
    ctx.setTransform(matrix.a,matrix.b,matrix.c,matrix.d,actor.x-left,actor.y-top);ctx.drawImage(body.canvas,-body.foot.x,-body.foot.y);ctx.restore();
    const projection={body,matrix,canvas,x:left,y:top,width:w,height:h,points:hull.filter(visible),hull,clip,visible,sourceURL:body.sourceURL,rect:body.rect,anchor:body.anchor,length,across,revision};
    projectionCache.set(actor,{key,projection,world:G.World,obstacleKey:obstacle.key,clip:pathClear,path:G.World?.projectilePathClear,block:G.World?.projectileBlock});return projection;
  }
  function contains(projection,x,y){
    if(!projection||!projection.visible({x,y}))return false;const {matrix:m,body}=projection,det=m.a*m.d-m.b*m.c;if(!det)return false;
    const px=x-m.e,py=y-m.f;return alphaAt(body,(m.d*px-m.c*py)/det+body.foot.x,(-m.b*px+m.a*py)/det+body.foot.y)>=24;
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
  function drawProjection(ctx,projection,alpha=1){if(!projection)return;ctx.save();ctx.globalAlpha*=alpha;ctx.imageSmoothingEnabled=false;ctx.drawImage(projection.canvas,projection.x,projection.y);ctx.restore();}
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
  function drawArch(ctx,arc,alpha=1,remaining=1,from=0,to=1){
    if(arc.points.length<2||arc.progress<=0||arc.blocked||remaining<=0)return;
    const progress=arc.progress*clamp(remaining),start=Math.min(progress,clamp(from)),end=Math.min(progress,clamp(to));if(end<=start)return;
    const steps=Math.max(2,Math.ceil(48*(end-start))),spine=start>0||end<arc.progress||remaining<1?Array.from({length:steps+1},(_,i)=>archPoint(arc,start+(end-start)*i/steps)):arc.points;
    const points=spine.map(p=>({x:p.x,y:p.y-p.z}));ctx.save();ctx.globalAlpha*=alpha;ctx.fillStyle='#080a09';ctx.beginPath();
    for(let side=0;side<2;side++)for(let j=0;j<points.length;j++){const i=side?points.length-1-j:j,p=points[i],a=points[Math.max(0,i-1)],b=points[Math.min(points.length-1,i+1)],dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1,u=start+(end-start)*i/(points.length-1),w=arc.width*(.5+1.1*Math.sin(Math.PI*u)**.8)*Math.min(1,(progress-u)/.18)*(side?-1:1);if(!side&&!j)ctx.moveTo(p.x-dy/d*w,p.y+dx/d*w);else ctx.lineTo(p.x-dy/d*w,p.y+dx/d*w);}ctx.closePath();ctx.fill();ctx.restore();
  }
  G.ShikamaruReferenceGeometry={bodyFor,alphaAt,project,contains,groundContact,drawProjection,archPoint,makeArch,sweptBody,advanceArch,drawArch,registerNativePolicy(policy){nativePolicies.add(policy);},beginFrame(){revision++;scans.clear();},invalidateWorld(){revision++;forcedRevision++;scans.clear();}};
  // World is a stable singleton across runs; a reset can replace same-tile props.
  for(const name of ['reset','setBiome','setArena']){
    const previous=G.World?.[name];if(!previous)continue;
    G.World[name]=function(...args){try{return previous.apply(this,args);}finally{G.ShikamaruReferenceGeometry.invalidateWorld();}};
  }
})();
