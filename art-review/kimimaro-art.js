/* Original Kimimaro gameplay art. No showcase scene or target simulation. */
(() => {
  'use strict';
  const base=new URL('./',document.currentScript.src),metadataVersion=new URL(document.currentScript.src).search,images={},frameWhites=new Map();
  const TAU=Math.PI*2, clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,Number(v)||0));
  const FOREST_LIMIT=96,RING_COUNTS=[10,12,14,18,20,22];
  const lerp=(a,b,t)=>a+(b-a)*t, ease=v=>{const t=clamp(v);return t*t*(3-2*t);};
  const rand=seed=>{let n=seed>>>0;return()=>{n=(Math.imul(n,1664525)+1013904223)>>>0;return n/4294967296;};};
  const normalize=state=>String(state||'idle').replace(/^naruto-kimimaro-?/,'').replace(/^kimimaro-/,'')||'willow';
  const direction=dir=>typeof dir==='string'?dir:['down','right','right','right','up','left','left','left'][((dir||0)%8+8)%8];
  let metadata,pending,planCache=null;
  const forests=new WeakMap();
  async function load() {
    if(pending)return pending;
    pending=(async()=>{
      const metadataURL=new URL('kimimaro-frames.json',base);metadataURL.search=metadataVersion;
      const response=await fetch(metadataURL);
      if(!response.ok)throw Error('君麻呂動畫資料載入失敗');metadata=await response.json();
      await Promise.all(Object.entries(metadata.sheets).map(async([key,sheet])=>{
        const image=new Image(),url=new URL(sheet.source,base);url.searchParams.set('v',sheet.sha256);image.src=url.href;await image.decode();images[key]=image;
      }));
      api.loaded=true;return api;
    })().catch(error=>{pending=null;throw error;});return pending;
  }
  function poseKey(state,time,dir) {
    const t=Math.max(0,Number(time)||0),d=direction(dir);
    if(state==='idle')return d==='down'?'frontIdle':d==='up'?'backIdle':'idle';
    if(state==='move')return d==='down'?'frontRun':d==='up'?'backRun':['run1','run2','run3'][Math.floor(t*11)%3];
    if(state==='hurt')return t<.10?'hurt1':'hurt2';
    if(state==='death')return t<.15?'death1':'death2';
    if(state==='curse')return 'larch';
    if(state==='boomerang-throw')return t<.12?'throwWindup':t<.20?'throwRelease':'throwRecover';
    if(state==='willow')return t<.12?'idle':Math.floor(t*18)%2?'willow1':'willow2';
    if(state==='camellia')return t<.16?'camellia1':Math.floor(t*12)%2?'camellia2':'camellia1';
    if(state==='bullets')return t<.12?'idle':t<.46?'bullets':'run2';
    if(state==='larch')return t<.18||t>.70?'idle':'larch';
    if(state==='vine')return t<.30||t>.62?'vine1':'vine2';
    if(state==='flower')return t<.43?'flower1':'flower2';
    if(state==='combo')return t<.30?'vine1':t<.54?'vine2':t<.97?'flower1':'flower2';
    if(state==='bracken')return t<.30?'bracken':t<.90?'idle':'run1';
    if(state==='lily')return t<.14?'vine1':t>.72?'idle':'lily';
    return 'idle';
  }
  function sample(state='idle',time=0,dir=0,form='normal') {
    if(!metadata)return null;
    state=normalize(state);form=form==='curse'?'curse':'normal';
    const key=poseKey(state,time,dir),sheet=metadata.sheets[form],frame=sheet.frames[key]||sheet.frames.idle;
    return {...frame,sheet:form,key,state,direction:direction(dir),source:sheet.source,bodyHeight:sheet.bodyHeight};
  }
  function tintedFrame(frame,color='#fff9e9') {
    const key=frame.sheet+'/'+frame.key+'/'+color;
    if(frameWhites.has(key))return frameWhites.get(key);
    const [x,y,w,h]=frame.rect,canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;
    const c=canvas.getContext('2d');c.drawImage(images[frame.sheet],x,y,w,h,0,0,w,h);
    c.globalCompositeOperation='source-in';c.fillStyle=color;c.fillRect(0,0,w,h);
    canvas.dataset.source=images[frame.sheet].src+'#tint='+encodeURIComponent(color);
    frameWhites.set(key,canvas);
    // Flash caches remain bounded even after every skill has been used.
    if(frameWhites.size>8)frameWhites.delete(frameWhites.keys().next().value);
    return canvas;
  }
  function paint(ctx,frame,options={}) {
    const image=images[frame.sheet];if(!image)return false;
    const [x,y,w,h]=frame.rect,k=(options.height??64)/frame.bodyHeight;
    const facing=options.facing??(frame.direction==='left'?-1:1);
    ctx.save();ctx.translate(options.x??0,options.y??0);ctx.scale(facing===-1||facing==='left'?-k:k,k);
    ctx.imageSmoothingEnabled=false;ctx.globalAlpha*=options.alpha??1;
    if(options.silhouette)ctx.drawImage(tintedFrame(frame,'#08070d'),-frame.anchor[0],-frame.anchor[1]);
    else ctx.drawImage(image,x,y,w,h,-frame.anchor[0],-frame.anchor[1],w,h);
    if(options.flash){ctx.globalAlpha*=.55;ctx.drawImage(tintedFrame(frame),-frame.anchor[0],-frame.anchor[1]);}
    ctx.restore();return true;
  }
  function draw(ctx,owner={},options) {
    if(!options){options=owner;owner={};}
    if(!api.loaded){void load().catch(()=>{});return false;}
    let state=normalize(options.state||'idle'),time=options.time??0;
    const form=options.form||G.NarutoKimimaro?.formFor?.(owner)||'normal';
    if(state==='boomerang-throw'){
      const frame=sample(state,time,options.dir,form);
      if(time<.12&&frame.hand){
        const k=(options.height??64)/frame.bodyHeight,facing=options.facing??(frame.direction==='left'?-1:1);
        ctx.save();ctx.globalAlpha*=options.alpha??1;
        ctx.translate((options.x??0)+(frame.hand[0]-frame.anchor[0])*k*(facing===-1?-1:1),
          (options.y??0)+(frame.hand[1]-frame.anchor[1])*k);
        ctx.scale(facing===-1?-1:1,1);ctx.imageSmoothingEnabled=false;
        ctx.drawImage(boomerangFrame(0),-44,-44);ctx.restore();
      }
      return paint(ctx,frame,options);
    }
    if(state==='curse'&&time>=0&&time<1){
      const rise=ease(time/.55),fade=ease(time/.14)*(1-ease((time-.68)/.32));
      const facing=options.facing??(direction(options.dir)==='left'?-1:1);
      const back=facing===-1||facing==='left'?1:-1;
      const shadow=sample('larch',time,options.dir,'curse'),height=options.height??64;
      // Two bounded silhouette draws share the existing pose and tint cache.
      for(const [scale,alpha,offset] of [[1.80,.22,15],[1.48,.78,8]]){
        paint(ctx,shadow,{...options,silhouette:true,flash:false,
          x:(options.x??0)+back*offset*height/64*rise,
          y:(options.y??0)-height*.18*rise,
          height:height*lerp(1,scale,rise),alpha:(options.alpha??1)*alpha*fade});
      }
    }
    if(state==='bracken'&&time>=.30){
      state=owner.walking?'move':'idle';time=G.NarutoKimimaro?.stateFor?.(owner)?.clock??time;
    }
    if(state==='curse'&&time>=.45&&time<1){
      const mix=ease((time-.45)/.30);
      const pose=owner.walking?'move':'larch';
      paint(ctx,sample(pose,time,options.dir,'normal'),{...options,alpha:(options.alpha??1)*(1-mix)});
      return paint(ctx,sample(pose,time,options.dir,'curse'),{...options,alpha:(options.alpha??1)*mix});
    }
    return paint(ctx,sample(state,time,options.dir,form),options);
  }
  function portrait(ctx,options={}) {
    if(!api.loaded){void load().catch(()=>{});return false;}
    const f=sample('idle',0,0,'normal'),[x,y,w,h]=f.rect;
    const height=Math.min(h,f.bodyHeight*.56),width=Math.min(w,height*.90);
    ctx.save();ctx.imageSmoothingEnabled=false;
    ctx.drawImage(images.normal,x+(w-width)/2,y,width,height,options.x??0,options.y??0,options.width??options.size??48,options.height??options.size??48);
    ctx.restore();return true;
  }
  function polygon(c,points,fill,stroke) {
    c.beginPath();points.forEach((p,i)=>i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]));c.closePath();
    if(fill){c.fillStyle=fill;c.fill();}if(stroke){c.strokeStyle=stroke;c.stroke();}
  }
  function bone(c,x1,y1,x2,y2,w) {
    const a=Math.atan2(y2-y1,x2-x1),d=Math.hypot(x2-x1,y2-y1);
    c.save();c.translate(x1,y1);c.rotate(a);c.lineWidth=1;
    polygon(c,[[-2,-w*.45],[d*.12,-w*.62],[d*.7,-w*.3],[d,0],[d*.7,w*.3],[d*.1,w*.5],[-2,w*.35]],'#f0ebde','#34384b');
    polygon(c,[[0,0],[d,0],[d*.7,w*.3],[d*.1,w*.5]],'#a7a1b5',null);c.restore();
  }
  function boneBoomerang(c) {
    // Three long, forked bone blades with large root spurs follow the user's sketch.
    c.save();c.scale(.88,.88);c.lineWidth=1.1;c.lineJoin='miter';
    for(let i=0;i<3;i++){
      c.save();c.rotate(i*TAU/3);
      polygon(c,[[-4,1],[-7,-5],[-11,-7],[-7,-10],[-9,-13],[-12,-15],
        [-7,-17],[-6,-21],[-1,-25],[7,-29],[3,-18],[13,-28],
        [7,-14],[4,-6],[5,0]],'#e0dac9','#29283d');
      polygon(c,[[7,-29],[3,-18],[13,-28],[7,-14],[4,-6],[5,0],
        [0,2],[-1,-8],[2,-19]],'#9d96a8');
      polygon(c,[[-7,-17],[-6,-21],[-1,-25],[7,-29],[-1,-19],[-3,-9],
        [-5,-5],[-7,-10],[-9,-13],[-12,-15]],'#f7f1dd');
      polygon(c,[[-7,-5],[-11,-7],[-7,-10],[-3,-9],[-4,-4]],'#b5abb0');
      c.restore();
    }
    polygon(c,[[-4,-3],[4,-3],[0,5]],'#c4bcb0','#29283d');
    polygon(c,[[-3,-2],[2,-2],[0,1]],'#f7f1dd');c.restore();
  }
  const boomerangFrames=new Map();
  function boomerangFrame(age) {
    const steps=64,index=((Math.floor(age*6/TAU*steps)%steps)+steps)%steps;
    if(boomerangFrames.has(index))return boomerangFrames.get(index);
    const canvas=document.createElement('canvas');canvas.width=canvas.height=88;
    const c=canvas.getContext('2d');c.translate(44,44);c.rotate(index*TAU/steps);boneBoomerang(c);
    // Rasterize each angle once, then remove the soft alpha fringe before pixel-art scaling.
    const pixels=c.getImageData(0,0,88,88);
    for(let i=3;i<pixels.data.length;i+=4)pixels.data[i]=pixels.data[i]>=128?255:0;
    c.putImageData(pixels,0,0);boomerangFrames.set(index,canvas);return canvas;
  }
  function slash(c,x,y,r,angle,alpha) {
    c.save();c.translate(x,y);c.rotate(angle);c.globalAlpha*=clamp(alpha);c.fillStyle='#fff7e4';
    c.beginPath();c.moveTo(r*.72,-r*.5);c.bezierCurveTo(r*1.05,-r*.24,r*.99,r*.24,r*.68,r*.47);
    c.bezierCurveTo(r*.90,r*.15,r*.92,-r*.24,r*.72,-r*.5);c.fill();c.restore();
  }
  function whip(c,points,alpha=1) {
    c.save();c.globalAlpha*=alpha;c.lineCap='round';c.lineJoin='round';
    c.strokeStyle='#303449';c.lineWidth=6;c.beginPath();points.forEach((p,i)=>i?c.lineTo(p.x,p.y):c.moveTo(p.x,p.y));c.stroke();
    c.strokeStyle='#eee9dd';c.lineWidth=3.8;c.stroke();
    for(let i=1;i<points.length;i+=2){
      const p=points[i],a=Math.atan2(p.y-points[i-1].y,p.x-points[i-1].x),q=i/points.length,k=3.5*(1-q*.4);
      c.save();c.translate(p.x,p.y);c.rotate(a);
      polygon(c,[[-3,-k*.6],[-1,-k*.75],[0,-k*1.45],[1.5,-k*.7],[3,k*.4],[1,k*.8],[0,k*1.2],[-1.5,k*.7],[-3,k*.45]],'#f2ecde','#414257');c.restore();
    }c.restore();
  }
  function local(owner,aim,forward,height,side=0) {
    return {x:owner.x+Math.cos(aim)*forward-Math.sin(aim)*side,
      y:owner.y+Math.sin(aim)*forward+Math.cos(aim)*side-height};
  }
  function muzzleFor(owner,aim=owner.aim||0){const p=local(owner,aim,12,0);return {...p,height:31};}
  function boomerangHandFor(owner,aim=owner.aim||0){
    const form=G.NarutoKimimaro?.formFor?.(owner)||'normal',frame=sample('boomerang-throw',.12,0,form);
    if(!frame?.hand)return muzzleFor(owner,aim);
    const k=64/ frame.bodyHeight,facing=Math.cos(aim)<0?-1:1;
    return {x:owner.x+(frame.hand[0]-frame.anchor[0])*k*facing,y:owner.y,
      height:(frame.anchor[1]-frame.hand[1])*k};
  }
  function value(move,key,fallback){return Number.isFinite(move?.[key])?move[key]:fallback;}
  function columns(forest,allowance) {
    let cached=forests.get(forest);
    if(!cached){cached=new Map();forests.set(forest,cached);}
    if(cached.has(allowance))return cached.get(allowance);
    const castId=(forest.castId||1)-(forest.index||0);
    const random=rand(castId*571+Math.round(forest.x*13+forest.y*7));
    const points=[];let reserved=0;
    for(let wave=0;wave<6;wave++){
      const next=reserved+RING_COUNTS[wave];
      const count=Math.floor(next*allowance/FOREST_LIMIT)-Math.floor(reserved*allowance/FOREST_LIMIT),distance=.13+wave*.164;
      reserved=next;
      const phase=random(),contour=random()*TAU;
      for(let slot=0;slot<count;slot++){
        const cluster=Math.sin(slot*TAU/count+contour)*.24;
        const angle=(slot+phase+cluster+(random()-.5)*.44)*TAU/count;
        const spread=wave===0?.035:.048;
        const radius=Math.min((wave+1)/6-.005,distance+Math.sin(angle*2+contour)*spread*.4+(random()*2-1)*spread*.6);
        points.push({nx:Math.cos(angle)*radius,ny:Math.sin(angle)*radius,distance:radius,wave,
          seed:random(),lean:0,variant:5+Math.floor(random()*4),flip:random()<.35,
          h:(76+wave*10)*(.50+random()*.70),w:5+wave*.5});
      }
    }
    for(const point of points){
      let gap=Infinity;
      for(const other of points)if(other!==point)gap=Math.min(gap,Math.hypot(point.nx-other.nx,point.ny-other.ny));
      const [width,height]=metadata.sheets.effects.frames['pillar'+point.variant].sourceSize;
      point.h=Math.min(point.h,gap*(forest.radius||180)*.72*height/width);
    }
    const candidates=[];
    for(const point of points){
      if(point.wave<2||Math.abs(point.nx)<.18)continue;
      const nearby=points.filter(other=>other!==point).sort((a,b)=>
        Math.hypot(a.nx-point.nx,a.ny-point.ny)-Math.hypot(b.nx-point.nx,b.ny-point.ny)).slice(0,6);
      if(nearby.length<4)continue;
      const heights=nearby.map(other=>other.h).sort((a,b)=>a-b);
      const referenceHeight=(heights[2]+heights[3])/2;
      candidates.push({point,referenceHeight});
    }
    const priority=point=>point.wave===2&&point.ny>0&&Math.abs(point.nx)<.36?2:point.wave===3?1:0;
    candidates.sort((a,b)=>priority(b.point)-priority(a.point)||b.point.seed-a.point.seed);
    const accents=[],accentCount=Math.min(random()<.5?3:4,Math.max(1,Math.floor(allowance/24)));
    for(const candidate of candidates){
      if(accents.length>=accentCount)break;
      if(accents.length===1&&candidate.point.nx*accents[0].nx>0)continue;
      if(accents.some(other=>Math.hypot(other.nx-candidate.point.nx,other.ny-candidate.point.ny)<.4))continue;
      const dramatic=accents.length<Math.max(1,accentCount-1);
      const height=dramatic?Math.min(320,Math.max(200,candidate.referenceHeight*(2+random()*.5))):
        Math.min(180,candidate.referenceHeight*(1.3+random()*.3));
      Object.assign(candidate.point,{h:height,referenceHeight:candidate.referenceHeight,accent:true,dramatic,variant:9+Math.floor(random()*4)});
      accents.push(candidate.point);
    }
    cached.set(allowance,points);return points;
  }
  function liveStates(states){return (states||G.NarutoKimimaro?.renderStates?.()||[]).filter(s=>s?.owner&&!s.owner.dead&&s.owner.hp>0&&s.world===G.World);}
  function plan(states) {
    states=liveStates(states);
    const signature=states.map(s=>`${s.clock}:${s.owner.x}:${s.owner.y}:${s.action?.castId||0}:${s.forest?.castId||0}:${s.bullets?.length||0}`).join('|');
    if(planCache?.signature===signature&&planCache.states.length===states.length&&
       states.every((state,index)=>state===planCache.states[index]))return planCache;
    const forestStates=[],selected=[],particles=[];let reservations=0;
    for(const state of states){
      const active=state.forests?.length?state.forests:state.forest?[state.forest]:[];
      if(!active.length)continue;
      // Overlapping bursts share one grove layout; damage still uses every burst.
      forestStates.push({state,forest:active[0],slot:reservations++});
    }
    const baseAllowance=Math.floor(FOREST_LIMIT/Math.max(1,reservations)),extras=FOREST_LIMIT%Math.max(1,reservations);
    for(const {state,forest:f,slot} of forestStates){
      const R=f.radius||180,age=f.age??state.action?.age??0,allowance=baseAllowance+Number(slot<extras);
      if(!allowance)continue;
      for(const p of columns(f,allowance)){
        const start=f.waves[p.wave]-.18;
        const grow=ease((age-start)/.18)*(1-ease((age-(f.duration-.38))/.38));
        if(grow<=.005)continue;
        selected.push({...p,x:f.x+p.nx*R,y:f.y+p.ny*R,height:p.h*grow,age,start,grow,owner:state.owner,forest:f});
        if(age-start>=0&&age-start<.28&&particles.length<20){
          const q=(age-start)/.28,a=p.seed*TAU;
          particles.push({kind:'earth',x:f.x+p.nx*R+Math.cos(a)*q*18,y:f.y+p.ny*R-Math.sin(q*Math.PI)*14,q,size:2+p.seed*2});
        }
      }
    }
    selected.sort((a,b)=>a.y-b.y);
    for(const state of states)for(const hit of (state.impacts||[]).slice(-8)){
      const age=hit.age??state.clock-(hit.time??state.clock);if(age<0||age>.26)continue;
      for(let i=0;i<2&&particles.length<20;i++){
        const q=age/.26,a=i*Math.PI+(Number(hit.x)||0)*.17;
        particles.push({kind:'bone',x:hit.x+Math.cos(a)*q*22,y:hit.y-22+Math.sin(a)*q*14+q*q*8,q,size:2});
      }
    }
    planCache={signature,states,columns:selected.slice(0,FOREST_LIMIT),particles:particles.slice(0,20)};
    api.debugLast={forestColumns:planCache.columns.length,secondaryParticles:planCache.particles.length,
      tallColumns:planCache.columns.filter(p=>p.accent).map(p=>({x:p.x,y:p.y,height:p.height,referenceHeight:p.referenceHeight,wave:p.wave,dramatic:p.dramatic}))};return planCache;
  }
  function pillar(ctx,col) {
    if(col.forest){
      const frame=metadata.sheets.effects.frames['pillar'+col.variant];
      const [sw,sh]=frame.sourceSize,width=col.height*sw/sh,scale=col.height/sh;
      const crosses=col.y>=col.owner.y-8&&col.y-col.height<col.owner.y-20&&Math.abs(col.x-col.owner.x)<width/2+24;
      ctx.save();ctx.translate(col.x,col.y);ctx.globalAlpha*=crosses?.22:.98;
      ctx.save();ctx.globalAlpha*=.28;ctx.fillStyle='#17281e';ctx.beginPath();ctx.ellipse(0,1,col.w*1.8+3,3,0,0,TAU);ctx.fill();ctx.restore();
      ctx.imageSmoothingEnabled=false;
      if(col.flip)ctx.scale(-1,1);
      const transform=ctx.getTransform(),pixelY=y=>(Math.round(y*transform.d+transform.f)-transform.f)/transform.d;
      for(const segment of frame.segments){
        const [sx,sy,w,h]=segment.rect;
        const top=pixelY((segment.offsetY-sh+1)*scale),bottom=pixelY((segment.offsetY+h-sh+1)*scale);
        ctx.drawImage(images.effects,sx,sy,w,h,-width/2,top,width,bottom-top);
      }
      ctx.restore();return;
    }
    const frame=metadata?.sheets.effects.frames['pillar'+col.variant];if(!frame)return;
    const [x,y,w,h]=frame.rect,a=frame.anchor||[w/2,h],dw=col.w*2.3;
    const crosses=col.y>=col.owner.y-8&&col.y-col.height<col.owner.y-20&&Math.abs(col.x-col.owner.x)<col.w+24;
    ctx.save();ctx.translate(col.x,col.y);ctx.globalAlpha*=crosses?.32:.98;
    ctx.save();ctx.globalAlpha*=.28;ctx.fillStyle='#17281e';ctx.beginPath();ctx.ellipse(0,1,col.w+4,4,0,0,TAU);ctx.fill();ctx.restore();
    ctx.rotate(col.forest?0:col.lean);ctx.imageSmoothingEnabled=false;
    ctx.drawImage(images.effects,x,y,w,h,-a[0]/w*dw,-a[1]/h*col.height,dw,col.height);ctx.restore();
  }
  function drawGround(ctx,states) {
    if(!api.loaded)return;
    const p=plan(states);
    drawBoneGuards(ctx,p.states,false);
    for(const col of p.columns){
      const age=col.age-col.start;
      if(age<.50){
        ctx.save();ctx.globalAlpha*=.65*(1-ease((age-.2)/.3));
        polygon(ctx,[[col.x-col.w-3,col.y+1],[col.x-5,col.y-5],[col.x+col.w+4,col.y-1],[col.x+5,col.y+5]],'#665335','#394329');ctx.restore();
      }
      if(col.y<col.forest.y)pillar(ctx,col);
    }
    for(const v of p.particles)if(v.kind==='earth'){
      ctx.save();ctx.globalAlpha*=1-v.q;
      polygon(ctx,[[v.x-v.size,v.y],[v.x,v.y-v.size],[v.x+v.size,v.y+1],[v.x+1,v.y+v.size]],'#8b754e','#3b3d30');ctx.restore();
    }
  }
  function drill(ctx,action,state,age) {
    const owner=state.owner,aim=action.aim||0,move=action.move||action.m;
    const a=action.kind==='combo'?age-.54:age;if(a<.12||a>.86)return;
    const power=ease((a-.12)/.18)*(1-ease((a-.64)/.22));
    const front=lerp(46,value(move,'range',220),ease((a-.22)/.36));
    const start=local(owner,aim,18,31),end=local(owner,aim,front,31);
    const target=action.target;
    if(target&&!target.dead){const h=clamp((target.bodyH||32)*.5,14,50);end.y=target.y-(target.jumpLift||0)-h;}
    const length=Math.hypot(end.x-start.x,end.y-start.y),angle=Math.atan2(end.y-start.y,end.x-start.x);
    const frame=metadata.sheets.effects.frames.drill2||metadata.sheets.effects.frames.drill1;
    const [x,y,w,h]=frame.rect,origin=frame.origin||[0,h/2],tip=frame.tip||[w,h/2];
    const sx=length/Math.max(1,tip[0]-origin[0]),sy=Math.max(30,value(move,'halfWidth',42)*1.1)*power/h;
    ctx.save();ctx.translate(start.x,start.y);ctx.rotate(angle);ctx.imageSmoothingEnabled=false;
    ctx.drawImage(images.effects,x,y,w,h,-origin[0]*sx,-origin[1]*sy,w*sx,h*sy);ctx.restore();
  }
  function drawAction(ctx,state) {
    const a=state.action;if(!a)return;
    const owner=state.owner,t=a.age||0,kind=normalize(a.kind),aim=a.aim||0;
    const m=a.move||a.m||{},hand=local(owner,aim,18,31);
    if(kind==='willow')for(const [i,hit] of (a.hitTimes||[.12,.306,.465,.6]).entries()){
      const age=t-hit;if(age<-.06||age>.09)continue;
      slash(ctx,hand.x,hand.y,value(m,'range',110)*.86,aim+(i%2?.45:-.45),1-clamp((age+.01)/.10));
    }
    if(kind==='camellia'){
      const ext=Math.max(...[.30,.43,.57].map(h=>Math.max(0,1-Math.abs(t-h)/.08)));
      if(ext>.05){const tip=local(owner,aim,lerp(35,value(m,'range',220),ext),31);bone(ctx,hand.x,hand.y,tip.x,tip.y,7);}
    }
    if(kind==='larch'&&t>.14&&t<.88){
      const out=ease((t-.14)/.16)*(1-ease((t-.62)/.26)),reach=value(m,'radius',125)/60;
      for(const [rx,ry,tx,ty,w] of [[-6,-36,-40,-59,6],[7,-35,48,-63,5],[-11,-26,-57,-32,7],[12,-27,60,-31,6],[-5,-15,-34,8,4],[8,-17,38,7,5]])
        bone(ctx,owner.x+rx,owner.y+ry,owner.x+lerp(rx,tx*reach,out),owner.y-27+lerp(ry+27,(ty+27)*reach,out),w*Math.sqrt(reach));
    }
    if((kind==='vine'||kind==='combo')&&t>.12&&t<(kind==='combo'?1.12:.70)&&a.target){
      const target=a.target,height=clamp((target.bodyH||32)*.5,14,48);
      const end={x:target.x,y:target.y-height},q=ease((t-.12)/.30),points=[];
      for(let i=0;i<=24;i++){const p=i/24;
        points.push({x:lerp(hand.x,lerp(hand.x,end.x,q),p),y:lerp(hand.y,lerp(hand.y,end.y,q),p)+Math.sin(p*Math.PI)*Math.sin(t*10)*(t<.42?26:3)});
      }whip(ctx,points);
    }
    if(kind==='flower'||kind==='combo')drill(ctx,a,state,t);
    if(kind==='lily'&&t>.10&&t<.90){
      const second=t>=.40,start=second?.44:.14,end=second?.62:.32,sign=second?-1:1;
      const angle=-.8+sign*clamp((t-start)/(end-start))*TAU,R=value(m,'radius',120)*ease((t-.1)/.08)*(1-ease((t-.65)/.25));
      const points=[];for(let i=0;i<=32;i++){const q=i/32,b=angle-sign*(1-q)*2.8,r=lerp(15,R,q),e=ease(q/.18);
        points.push({x:lerp(hand.x,owner.x+Math.cos(b)*r,e),y:lerp(hand.y,owner.y-27+Math.sin(b)*r,e)});
      }whip(ctx,points);
    }
  }
  function drawBoneGuards(ctx,states,front) {
    const rows=[];
    for(const state of states)for(const wall of state.boneGuard?.walls||[])
      if(wall.age<wall.duration)rows.push({state,wall});
    rows.sort((a,b)=>b.wall.born-a.wall.born||
      Math.hypot(a.wall.x-a.state.owner.x,a.wall.y-a.state.owner.y)-Math.hypot(b.wall.x-b.state.owner.x,b.wall.y-b.state.owner.y));
    let count=0;
    for(const {state,wall} of rows){
      if(count>=20)break;
      const owner=state.owner,nx=wall.nx||0,ny=wall.ny||0,remaining=wall.duration-wall.age,
        fade=wall.phase==='block'?ease(remaining/.25):1,offsets=[0,-24,24];
      for(let j=0;j<offsets.length&&count<20;j++,count++){
        const offset=offsets[j],x=wall.x-ny*offset,y=wall.y+nx*offset;
        if((y>=owner.y)!==front)continue;
        const rise=wall.phase==='block'?1:ease(Math.max(0,wall.age-j*.012)/.075);
        ctx.save();ctx.globalAlpha*=fade;
        polygon(ctx,[[x-15,y],[x-5,y-6],[x+17,y+1],[x+4,y+7]],'#665335','#394329');
        pillar(ctx,{x,y,owner,variant:1+(wall.slot+j)%4,w:20,
          height:[108,86,98][j]*rise,lean:-nx*(j===1?.12:.07)});
        if(wall.phase==='block'&&remaining<.25){
          const crumble=.25-remaining;
          for(let k=0;k<2;k++){
            const angle=k*2.7+wall.slot+j,travel=crumble*(40+k*25),cx=x+Math.cos(angle)*travel,
              cy=y-20+Math.sin(angle)*travel-crumble*20+crumble*crumble*120;
            polygon(ctx,[[cx-3,cy-4],[cx+4,cy-1],[cx+1,cy+4]],'#eee7cf','#a99e86');
          }
        }
        ctx.restore();
      }
      if(wall.flash>0&&((wall.y>=owner.y)===front)){
        ctx.save();ctx.globalAlpha*=fade*Math.min(1,wall.flash/.14);ctx.strokeStyle='#fff8da';ctx.lineWidth=3;
        const ix=wall.impactX,iy=wall.impactY-(G.LIFT||20);
        for(let j=0;j<5;j++){const a=j*TAU/5;ctx.beginPath();ctx.moveTo(ix+Math.cos(a)*5,iy+Math.sin(a)*5);
          ctx.lineTo(ix+Math.cos(a)*24,iy+Math.sin(a)*24);ctx.stroke();}
        ctx.restore();
      }
    }
  }
  function drawAir(ctx,states) {
    if(!api.loaded)return;
    const p=plan(states);
    drawBoneGuards(ctx,p.states,true);
    for(const state of p.states){
      drawAction(ctx,state);
      for(const lane of state.boomerang?.lanes||[]){
        const b=lane.projectile;if(!b)continue;
        ctx.save();ctx.strokeStyle=b.phase==='return'?'#c4b3d8':'#e5dbc5';ctx.lineWidth=2;ctx.globalAlpha*=.35;
        const height=b.height??31;
        ctx.beginPath();b.trail.forEach((point,i)=>i?ctx.lineTo(point.x,point.y-height):ctx.moveTo(point.x,point.y-height));ctx.stroke();ctx.restore();
        ctx.save();ctx.imageSmoothingEnabled=false;
        ctx.drawImage(boomerangFrame(b.age),Math.round(b.x)-44,Math.round(b.y-height)-44);ctx.restore();
      }
      for(const b of state.bullets||[]){
        const aim=b.aim??Math.atan2(b.vy,b.vx),height=lerp(31,18,clamp((b.travelled??b.distance??0)/100));
        if(b.chainHops>0&&b.chainTrail?.length){
          ctx.save();ctx.globalAlpha*=.85;ctx.strokeStyle='#83f5cb';ctx.lineWidth=3;ctx.lineJoin='bevel';ctx.beginPath();
          b.chainTrail.forEach((point,i)=>i?ctx.lineTo(point.x,point.y-height):ctx.moveTo(point.x,point.y-height));
          ctx.lineTo(b.x,b.y-height);ctx.stroke();ctx.restore();
        }
        const flash=b.chainFlash,flashAge=flash?b.age-flash.time:1;
        if(flash&&flashAge<.16){
          const radius=6+flashAge/.16*12;
          ctx.save();ctx.globalAlpha*=1-flashAge/.16;ctx.strokeStyle='#acffe0';ctx.lineWidth=2;ctx.beginPath();
          ctx.moveTo(flash.x-radius,flash.y-height);ctx.lineTo(flash.x,flash.y-height-radius);
          ctx.lineTo(flash.x+radius,flash.y-height);ctx.lineTo(flash.x,flash.y-height+radius);ctx.closePath();ctx.stroke();ctx.restore();
        }
        ctx.save();ctx.translate(b.x,b.y-height);ctx.rotate(aim);
        polygon(ctx,[[-5,-2],[4,-2],[10,0],[4,2],[-5,1.5]],'#f2eddf','#34394c');
        polygon(ctx,[[-2,0],[8,0],[4,1.5],[-3,1.5]],'#a39daf',null);ctx.restore();
      }
    }
    for(const col of p.columns)if(col.y>=col.forest.y)pillar(ctx,col);
    for(const v of p.particles)if(v.kind==='bone'){
      ctx.save();ctx.globalAlpha*=1-v.q;polygon(ctx,[[v.x-2,v.y-2],[v.x+2,v.y-1],[v.x+1,v.y+3]],'#f6f0e1','#8f899e');ctx.restore();
    }
  }
  const pal={w:'#f4efdf',s:'#a09bb0',p:'#80628f',g:'#78a58b'};
  const rows={
    kimimaroBoomerang:['..w......w..','.ww......ww.','.wsw....wsw.','..wsw..wsw..','...wswwsw...','....wwww....','.....ss.....','............','..pp....pp..','.p........p.','..p......p..','...pppppp...'],
    kimimaroBoneGuard:['..w..w..w...','..w.ww..w...','.ww.ww.ww...','.wwwww.ww...','wwwwwwwww...','wsswwsswww..','sssssssssss.','............','...ppppp....','..p.....p...','............','............'],
    kimimaroWillow:['.........ww.','........ww..','.......ww...','......ws....','.....ws.....','....ws......','...ws.......','..ws........','.pw.........','pp..........','p...........','............'],
    kimimaroCamellia:['..........w.','.........ww.','........ws..','.......ws...','......ws....','.....ws.....','....ws......','...ws.......','..ppp.......','...p........','..p.........','.p..........'],
    kimimaroBullets:['....w.......','......w.....','........w...','..........w.','............','..w.........','..ww........','.pww........','pppp........','.pp.........','............','............'],
    kimimaroLarch:['.....w......','..w..w..w...','...w.w.w....','....www.....','ww.wwwww.ww.','..wwpspww...','ww.wwwww.ww.','....www.....','...w.w.w....','..w..w..w...','.....w......','............'],
    kimimaroVine:['...wwwww....','..ws...sw...','.ws.....sw..','ws.......w..','w........w..','w.......sw..','sw.....sw...','.sw...sw....','..sw.sw.....','...ppp......','....p.......','............'],
    kimimaroFlower:['..........w.','........www.','......wwsww.','....wwwsww..','..wwwwsww...','wwwwwsww....','.swwsww.....','..ssww......','...pp.......','...p........','............','............'],
    kimimaroLily:['...wwwww....','..ws...sw...','.ws.....sw..','ws...p...sw.','w...ppp...w.','w....p....w.','sw.......sw.','.sw.....sw..','..sw...sw...','...wwwww....','............','............'],
    kimimaroBracken:['...w....w...','..ww....w...','..ww...ww...','..www..ww...','w.www..ww.w.','w.www.wwwww.','wwwww.wwwww.','wwwwwwwwwww.','wsswwwsswww.','sssss.ssssss','............','............'],
    kimimaroCurse:['..p.....p...','.ppp...ppp..','..ppp.ppp...','...ppppp....','..pgpppgp...','.ppppppppp..','..ppppppp...','...ppppp....','..p.ppp.p...','.p...p...p..','p....p....p.','............']
  };
  if(typeof G==='object'&&G.Icons?.UI)Object.assign(G.Icons.UI,Object.fromEntries(Object.entries(rows).map(([key,rows])=>[key,{pal,rows}])));
  const api={loaded:false,load,draw,sample,portrait,drawGround,drawAir,muzzleFor,boomerangHandFor,debugLast:{forestColumns:0,secondaryParticles:0},
    get ready(){return load();},get metadata(){return metadata;},get images(){return images;}};
  window.KimimaroArt=api;if(typeof G==='object')G.KimimaroArt=api;
})();
