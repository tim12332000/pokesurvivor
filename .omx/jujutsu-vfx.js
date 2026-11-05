/* Procedural JJK presentation. Reads combat state; it never creates damage events. */
(() => {
  'use strict';
  if(G.JujutsuVFX)return;
  const C=G.Combat,TAU=Math.PI*2,EPS=1e-8;
  const limits=Object.freeze({high:{snapshots:2,size:512,triangles:48,beamProfiles:18,trailPoints:36},low:{snapshots:1,size:256,triangles:12,beamProfiles:6,trailPoints:18},shards:24});
  let epoch=0,quality='auto',serial=0,frameNumber=0,lastAir=-1;
  let beamCache=new WeakMap(),trailCache=new WeakMap();
  const ids=new WeakMap(),folds=new Map(),pool=[];
  let frame={number:0,triangles:0,shards:0,beamProfiles:0,captures:[],draws:[],fallbacks:0},capturesTotal=0;
  const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v)),mix=(a,b,t)=>a+(b-a)*t;
  const ease=v=>{const t=clamp(v);return t*t*(3-2*t);};
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const controlled=a=>a===G.Game.player||!!G.SelfClones?.isActor?.(a);
  const terminal=()=>G.Game.state==='ui'||G.Game.state==='over';
  const legal=a=>!terminal()&&alive(a)&&controlled(a);
  const validSource=b=>b.world===G.World&&legal(b.owner)&&
    (b.runEpoch==null||!G.CombatPulse||b.runEpoch===G.CombatPulse.epoch);
  const owners=()=>[G.Game.player,...(G.SelfClones?.actors?.()||[])].filter(legal);
  const low=()=>quality==='low'||quality!=='high'&&(innerWidth<=700||!!G.Touch?.active);
  const budget=()=>limits[low()?'low':'high'];
  function id(object){if(!ids.has(object))ids.set(object,++serial);return ids.get(object);}
  function hash(i,seed){let x=(i^seed)>>>0;x=Math.imul(x^x>>>16,0x7feb352d);x=Math.imul(x^x>>>15,0x846ca68b);return ((x^x>>>16)>>>0)/4294967295;}
  const noise=(x,seed)=>{const i=Math.floor(x);return mix(hash(i,seed),hash(i+1,seed),ease(x-i));};
  function inverse(m){const d=m.a*m.d-m.b*m.c;if(Math.abs(d)<EPS)return null;return {a:m.d/d,b:-m.b/d,c:-m.c/d,d:m.a/d,e:(m.c*m.f-m.d*m.e)/d,f:(m.b*m.e-m.a*m.f)/d};}
  function multiply(a,b){return {a:a.a*b.a+a.c*b.b,b:a.b*b.a+a.d*b.b,c:a.a*b.c+a.c*b.d,d:a.b*b.c+a.d*b.d,e:a.a*b.e+a.c*b.f+a.e,f:a.b*b.e+a.d*b.f+a.f};}
  function affine(s,d){
    const x1=s[1].x-s[0].x,y1=s[1].y-s[0].y,x2=s[2].x-s[0].x,y2=s[2].y-s[0].y,det=x1*y2-x2*y1;
    if(Math.abs(det)<EPS)return null;
    const u1=d[1].x-d[0].x,v1=d[1].y-d[0].y,u2=d[2].x-d[0].x,v2=d[2].y-d[0].y;
    const a=(u1*y2-u2*y1)/det,c=(u2*x1-u1*x2)/det,b=(v1*y2-v2*y1)/det,e=(v2*x1-v1*x2)/det;
    return {a,b,c,d:e,e:d[0].x-a*s[0].x-c*s[0].y,f:d[0].y-b*s[0].x-e*s[0].y};
  }
  function triangle(ctx,image,s,d){
    const m=affine(s,d);if(!m)return;
    ctx.save();ctx.beginPath();ctx.moveTo(d[0].x,d[0].y);ctx.lineTo(d[1].x,d[1].y);ctx.lineTo(d[2].x,d[2].y);ctx.closePath();ctx.clip();
    ctx.transform(m.a,m.b,m.c,m.d,m.e,m.f);ctx.drawImage(image,0,0);ctx.restore();frame.triangles++;
  }
  function beginFrame(){frame={number:++frameNumber,quality:low()?'low':'high',triangles:0,shards:0,beamProfiles:0,captures:[],draws:[],fallbacks:0};}
  function releaseSlot(entry){if(entry.slot){entry.slot.entry=null;entry.slot=null;}}
  function clear(owner){
    for(const [source,entry]of folds)if(!owner||entry.owner===owner){releaseSlot(entry);folds.delete(source);}
    if(!owner){beamCache=new WeakMap();trailCache=new WeakMap();}
  }
  function epochReset(){epoch++;clear();}
  function shapePath(ctx,b){
    ctx.beginPath();
    if(b.mode==='uro-screen')ctx.arc(b.owner.x,b.owner.y,b.radius,0,TAU);
    else if(b.mode==='uro-collapse')ctx.arc(b.tx,b.ty,b.radius,0,TAU);
    else{ctx.moveTo(b.x,b.y);ctx.arc(b.x,b.y,b.range,b.aim-b.arc/2,b.aim+b.arc/2);ctx.closePath();}
  }
  function foldRect(b){
    if(b.mode==='uro-screen')return {x:b.owner.x-b.radius,y:b.owner.y-b.radius,w:b.radius*2,h:b.radius*2};
    if(b.mode==='uro-collapse')return {x:b.tx-b.radius,y:b.ty-b.radius,w:b.radius*2,h:b.radius*2};
    const r=b.range,cx=b.x+Math.cos(b.aim)*r*.48,cy=b.y+Math.sin(b.aim)*r*.48;
    return {x:cx-r*.62,y:cy-r*.62,w:r*1.24,h:r*1.24};
  }
  function foldSources(){
    const list=[];
    for(const owner of owners())if((owner.mon?.dex??owner.dex)===30015){
      const state=G.JjkUro?.stateFor(owner);if(!state)continue;
      for(const b of G.JjkUro.effects||[])if(b.owner===owner&&validSource(b))list.push(b);
      if(state.screen&&validSource(state.screen))list.push(state.screen);
    }
    return list;
  }
  function prepareFolds(){
    const sources=foldSources(),current=new Set(sources),eligible=[];
    for(const [source,entry]of folds)if(!current.has(source)||!legal(entry.owner)||entry.epoch!==epoch){releaseSlot(entry);folds.delete(source);}
    for(const source of sources){
      const start=source.mode==='uro-screen'?0:Math.max(0,(source.release||0)-.22),local=source.age-start;
      if(local<0||local>.45)continue;
      let entry=folds.get(source);
      if(!entry){entry={source,owner:source.owner,epoch,castId:source.castId??id(source),rect:foldRect(source),start,captured:false,slot:null};folds.set(source,entry);}
      // Move the destination with the live attack. capture.rect keeps the
      // original sampled terrain; no extra snapshots are needed while moving.
      // Body attack coordinates freeze at contact, whereas a screen follows.
      entry.rect=foldRect(source);entry.local=local;eligible.push(entry);
    }
    const cam=G.Camera||{x:0,y:0};
    eligible.sort((a,b)=>Number(b.owner===G.Game.player)-Number(a.owner===G.Game.player)||
      Number(b.source.age>=(b.source.release||0))-Number(a.source.age>=(a.source.release||0))||
      Math.hypot(a.owner.x-cam.x,a.owner.y-cam.y)-Math.hypot(b.owner.x-cam.x,b.owner.y-cam.y)||a.castId-b.castId);
    return eligible;
  }
  function capture(ctx,entry,slot,size){
    const m=ctx.getTransform(),inv=inverse(m);if(!inv)return false;
    const r=entry.rect,n={a:size/r.w,b:0,c:0,d:size/r.h,e:-r.x*size/r.w,f:-r.y*size/r.h},t=multiply(n,inv);
    const image=slot.canvas;if(image.width!==size||image.height!==size){image.width=size;image.height=size;}
    const target=image.getContext('2d');target.setTransform(1,0,0,1,0,0);target.clearRect(0,0,size,size);
    target.setTransform(t.a,t.b,t.c,t.d,t.e,t.f);target.imageSmoothingEnabled=false;target.drawImage(ctx.canvas,0,0);target.setTransform(1,0,0,1,0,0);
    entry.captured=true;entry.slot=slot;slot.entry=entry;capturesTotal++;
    entry.capture={castId:entry.castId,owner:id(entry.owner),epoch,rect:{...r},size,worldToPixels:{a:m.a,b:m.b,c:m.c,d:m.d,e:m.e,f:m.f},stage:'background-before-hazards'};
    frame.captures.push(entry.capture);
    return true;
  }
  function foldStrength(entry){
    const crest=entry.source.mode==='uro-screen'?.18:Math.max(.08,(entry.source.release||0)-entry.start),t=entry.local;
    return t<=crest?ease(t/crest):1-ease((t-crest)/Math.max(.05,.45-crest));
  }
  function foldMesh(ctx,entry,cols,rows){
    const r=entry.rect,size=entry.slot.canvas.width,strength=foldStrength(entry),vertices=[];
    for(let y=0;y<=rows;y++)for(let x=0;x<=cols;x++){
      const u=x/cols,v=y/rows,window=Math.sin(Math.PI*u)*Math.sin(Math.PI*v);
      vertices.push({source:{x:u*size,y:v*size},dest:{x:r.x+u*r.w+Math.sin(u*TAU+.3)*Math.min(r.w/cols*.42,28)*window*strength,
        y:r.y+v*r.h+Math.sin(u*Math.PI)*window*strength*r.h*.13}});
    }
    ctx.save();shapePath(ctx,entry.source);ctx.clip();
    for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){
      const a=y*(cols+1)+x,b=a+1,c=a+cols+1,d=c+1;
      for(const indices of [[a,b,d],[a,d,c]])triangle(ctx,entry.slot.canvas,indices.map(i=>vertices[i].source),indices.map(i=>vertices[i].dest));
    }
    ctx.restore();
    frame.draws.push({kind:'textured-fold',castId:entry.castId,owner:id(entry.owner),rect:{...r},triangles:cols*rows*2,strength});
  }
  function foldPanels(ctx,b,entry){
    const r=entry?.rect||foldRect(b),strength=entry?foldStrength(entry):.35,x=r.x+r.w*.5,y=r.y+r.h*.5;
    ctx.save();shapePath(ctx,b);ctx.clip();
    for(const side of [-1,1]){ctx.globalAlpha=.05+.08*strength;ctx.fillStyle=side<0?'#87d9e8':'#d7f8ff';ctx.beginPath();
      ctx.moveTo(x,y-r.h*.48);ctx.lineTo(x+side*r.w*.38,y-r.h*.36);ctx.lineTo(x+side*r.w*.33,y+r.h*.42);ctx.lineTo(x+(side<0?-.06:.05)*r.w*strength,y+r.h*.48);ctx.closePath();ctx.fill();}
    ctx.globalAlpha=.35+.4*strength;ctx.strokeStyle='#c8f7ff';ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(x,y-r.h*.46);
    ctx.lineTo(x-r.w*.075*strength,y+r.h*.02);ctx.lineTo(x+r.w*.045*strength,y+r.h*.25);ctx.lineTo(x,y+r.h*.46);ctx.stroke();ctx.restore();
  }
  function drawBackground(ctx){
    beginFrame();if(!G.JujutsuVFX.enabled||terminal()){clear();return;}
    const spec=budget(),eligible=prepareFolds(),chosen=eligible.slice(0,spec.snapshots),chosenSet=new Set(chosen);
    while(pool.length<spec.snapshots){const canvas=document.createElement('canvas');canvas.dataset.source='procedural-jjk-fold';pool.push({canvas,entry:null});}
    for(let i=0;i<pool.length;i++){
      const slot=pool[i];if(slot.entry&&!chosenSet.has(slot.entry))releaseSlot(slot.entry);
      if(i>=spec.snapshots){if(slot.entry)releaseSlot(slot.entry);slot.canvas.width=slot.canvas.height=0;}
    }
    // Capture every selected region BEFORE compositing any fold: no texture feedback.
    for(const entry of chosen)if(!entry.slot&&!entry.captured){const slot=pool.slice(0,spec.snapshots).find(s=>!s.entry);if(slot)capture(ctx,entry,slot,spec.size);}
    const textured=chosen.filter(e=>e.slot),cols=low()?3:textured.length>1?4:6,rows=low()?2:textured.length>1?3:4;
    for(const entry of eligible){
      if(entry.slot)foldMesh(ctx,entry,cols,rows);else frame.fallbacks++;
      foldPanels(ctx,entry.source,entry);
    }
    // A long screen keeps its honest finite circumference without recapturing terrain.
    for(const b of foldSources())if(b.mode==='uro-screen'&&b.age>.45)foldPanels(ctx,b,null);
  }
  function beamProfile(e){
    let cached=beamCache.get(e);const segments=low()?20:48,length=e.renderLength??e.length;
    if(!cached||cached.segments!==segments){
      const seed=e.castId??e.serial??id(e),points=[];
      for(let i=0;i<=segments;i++){const u=i/segments,envelope=.16+.84*Math.sin(Math.PI*u)**.35;
        points.push({x:length*u,width:e.radius*envelope*(.72+.28*(.67*noise(u*11,seed)+.33*noise(u*23,seed+3)))});}
      cached={segments,points};beamCache.set(e,cached);
    }
    return cached.points;
  }
  function drawMaximumBeam(ctx,e,length){
    const main=(e.volleyIndex||0)===0,life=Math.max(.01,e.life),t=clamp(e.age/life);
    const fade=Math.pow(1-t,main?.75:.6),width=e.radius*(1-.48*ease(t));
    const detailed=frame.beamProfiles<budget().beamProfiles;
    // A real broad contact keeps its broad silhouette even when other actors
    // spend the profile budget. Only edge detail and pressure ribs degrade.
    if(detailed){
      const points=beamProfile(e);
      for(const [scale,color,alpha]of [[1,'#258ba9',.48],[.72,'#70ddeb',.54],[.34,'#c4faff',.62],[.12,'#ffffff',.94]]){
        ctx.globalAlpha=fade*alpha;ctx.fillStyle=color;ctx.beginPath();
        for(let i=0;i<points.length;i++){const p=points[i],y=p.width/e.radius*width*scale;i?ctx.lineTo(p.x,y):ctx.moveTo(p.x,y);}
        for(let i=points.length-1;i>=0;i--){const p=points[i];ctx.lineTo(p.x,-p.width/e.radius*width*scale);}ctx.closePath();ctx.fill();
      }
      frame.beamProfiles++;
    }else{
      const throat=Math.min(16,length*.08),shoulder=Math.min(length*.25,Math.max(throat,width*.8));
      ctx.globalAlpha=fade*.46;ctx.fillStyle='#56c7dc';ctx.beginPath();ctx.moveTo(0,-width*.12);
      ctx.lineTo(shoulder,-width*.86);ctx.lineTo(length,-width*.18);ctx.lineTo(length,width*.18);
      ctx.lineTo(shoulder,width*.86);ctx.lineTo(0,width*.12);ctx.closePath();ctx.fill();
      ctx.globalAlpha=fade*.85;ctx.strokeStyle='#d9ffff';ctx.lineWidth=Math.max(2,width*.19);
      ctx.beginPath();ctx.moveTo(throat,0);ctx.lineTo(length,0);ctx.stroke();
    }
    // These moving pressure ribs are inside the already resolved beam. Each
    // volley effect has its own age; no decorative rib becomes a damage pulse.
    const ribs=detailed&&!low()?3:1;
    ctx.strokeStyle='#e2ffff';ctx.lineWidth=main?2.5:1.5;
    for(let i=0;i<ribs;i++){
      const progress=e.age/(main?.25:Math.max(.06,life*.65))-i*.2;
      if(progress<=0||progress>=1)continue;
      const x=length*progress,envelope=.16+.84*Math.sin(Math.PI*progress)**.35;
      ctx.globalAlpha=fade*(main?.8:.65);ctx.beginPath();ctx.ellipse(x,0,Math.min(7,length*.015),width*envelope*.76,0,0,TAU);ctx.stroke();
    }
  }
  function drawBeam(ctx,e,owner){
    const length=e.renderLength??e.length;if(length<=EPS)return;
    const fade=clamp(1-e.age/e.life),tail=1-.6*ease((e.age-.06)/(e.life-.06));
    ctx.save();ctx.translate(e.renderX??e.x,e.renderY??e.y-48);ctx.rotate(e.renderAim??e.aim);ctx.globalAlpha=fade;
    if(e.maximum)drawMaximumBeam(ctx,e,length);
    else if(frame.beamProfiles<budget().beamProfiles){
      const points=beamProfile(e);
      for(const [scale,color]of [[1,e.maximum?'#319fc4':'#55cfdf'],[.66,'#b5f8ff'],[.25,'#fff']]){
        ctx.fillStyle=color;ctx.beginPath();
        for(let i=0;i<points.length;i++)i?ctx.lineTo(points[i].x,points[i].width*tail*scale):ctx.moveTo(points[i].x,points[i].width*tail*scale);
        for(let i=points.length-1;i>=0;i--)ctx.lineTo(points[i].x,-points[i].width*tail*scale);ctx.closePath();ctx.fill();
      }
      frame.beamProfiles++;
    }else{ctx.strokeStyle='#d5fcff';ctx.lineWidth=Math.min(3,e.radius*.25);ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(length,0);ctx.stroke();}
    ctx.restore();
    frame.draws.push({kind:'beam',owner:id(owner),castId:e.castId??e.serial,length,renderX:e.renderX??e.x,renderY:e.renderY??e.y-48,radius:e.radius,
      maximum:!!e.maximum,volleyIndex:e.volleyIndex??null,volleyCount:e.volleyCount??null,age:e.age});
  }
  function drawMaximumCharge(ctx,owner,f,p,t){
    const radius=Math.min(78,Math.max(42,(f.mainRadius||f.radius||72)*.72));
    ctx.save();ctx.translate(p.x,p.y);ctx.rotate(f.barrageAim??f.aim);
    // Three short inward streams compress into the actual forehead anchor;
    // the large tell is a loaded artillery chamber, not an orbiting summon.
    for(let i=0;i<3;i++){
      const side=i-1,cycle=(t*1.7+i*.28)%1,d=radius*(1-cycle),y=side*d*.75;
      ctx.globalAlpha=.3+.5*cycle;ctx.strokeStyle=i===1?'#e5ffff':'#6bd9e9';ctx.lineWidth=2+cycle*2;
      ctx.beginPath();ctx.moveTo(-d*.5,y);ctx.quadraticCurveTo(-d*.18,y*.6,4,0);ctx.stroke();
    }
    const compressed=10+(1-ease(t))*radius*.42;
    ctx.globalAlpha=.16+.3*t;ctx.fillStyle='#47bfdc';ctx.beginPath();ctx.ellipse(7,0,compressed,compressed*.7,0,0,TAU);ctx.fill();
    ctx.globalAlpha=.55+.4*t;ctx.fillStyle='#e8ffff';ctx.beginPath();ctx.ellipse(7,0,4+7*t,3+5*t,0,0,TAU);ctx.fill();
    for(const side of [-1,1]){
      ctx.strokeStyle='#9bedf8';ctx.lineWidth=1.5;ctx.globalAlpha=.35+.5*t;ctx.beginPath();
      ctx.moveTo(12+radius*.4,side*radius*.54*(1-t*.5));ctx.lineTo(17+radius*.24,side*radius*.19);ctx.lineTo(16,side*4);ctx.stroke();
    }
    // A short guide communicates commitment while leaving the far field clear.
    ctx.globalAlpha=.25+.4*t;ctx.strokeStyle='#d5fcff';ctx.lineWidth=1.5;
    ctx.beginPath();ctx.moveTo(12,0);ctx.lineTo(52,0);ctx.moveTo(44,-5);ctx.lineTo(52,0);ctx.lineTo(44,5);ctx.stroke();ctx.restore();
    frame.draws.push({kind:'aim-guide',owner:id(owner),castId:f.castId,aim:f.barrageAim??f.aim,x:p.x,y:p.y,length:52});
    frame.draws.push({kind:'artillery-compression',owner:id(owner),castId:f.castId,radius,progress:t});
  }
  function drawCharge(ctx,owner,f){
    const p=G.JujutsuArt?.pointFor?.(owner,f,'muzzle')||{x:owner.x+Math.cos(f.aim)*8,y:owner.y+Math.sin(f.aim)*8-48};
    const t=clamp(f.age/f.charge);
    if(f.mode==='jjk-ryu-maximum'){drawMaximumCharge(ctx,owner,f,p,t);return;}
    ctx.save();ctx.translate(p.x,p.y);ctx.strokeStyle='#9cebf6';ctx.lineWidth=1;
    for(let i=0;i<2;i++){const cycle=(t*1.8+i*.5)%1,r=5+(1-cycle)*14;ctx.globalAlpha=.2+.6*cycle;ctx.beginPath();ctx.ellipse(0,0,r,r*.6,f.aim,0,TAU);ctx.stroke();}
    ctx.restore();
  }
  function drawBarrageMuzzle(ctx,owner,f){
    if(f.mode!=='jjk-ryu-maximum'||!f.released||!Number.isFinite(f.pulseAge)||f.pulseAge>.14)return;
    const p=G.JujutsuArt?.pointFor?.(owner,f,'muzzle');if(!p)return;
    const t=clamp(f.pulseAge/.14),r=Math.min(48,(f.mainRadius||f.radius||72)*.35)*(1-.45*t);
    ctx.save();ctx.translate(p.x,p.y);ctx.rotate(f.aim);ctx.globalAlpha=(1-t)*.7;ctx.strokeStyle='#ceffff';ctx.lineWidth=2.5;
    ctx.beginPath();ctx.ellipse(13+t*12,0,4,r,0,0,TAU);ctx.stroke();ctx.restore();
    frame.draws.push({kind:'barrage-muzzle',owner:id(owner),castId:f.castId,volleyIndex:f.volleyIndex,volleyCount:f.volleyCount,age:f.pulseAge});
  }
  function drawScatter(ctx,e,owner){
    if(e.dead)return;
    const x=e.x+(e.renderOffsetX||0),y=e.y+(e.renderOffsetY??-48),r=e.radius;
    ctx.save();ctx.translate(x,y);ctx.rotate(e.aim);
    // Short moving pellets have a visible tail, not a full-length artillery ray.
    ctx.globalAlpha=.7;ctx.strokeStyle='#71dce9';ctx.lineWidth=Math.max(2,r*.4);
    ctx.beginPath();ctx.moveTo(-r*2.3,0);ctx.lineTo(-r*.5,0);ctx.stroke();
    ctx.globalAlpha=1;ctx.fillStyle='#71dce9';ctx.beginPath();
    ctx.moveTo(r,0);ctx.lineTo(-r*.2,-r*.65);ctx.lineTo(-r,-r*.35);
    ctx.lineTo(-r,r*.35);ctx.lineTo(-r*.2,r*.65);ctx.closePath();ctx.fill();
    ctx.fillStyle='#f4ffff';ctx.beginPath();ctx.ellipse(r*.05,0,r*.48,r*.24,0,0,TAU);ctx.fill();ctx.restore();
    frame.draws.push({kind:'scatter',owner:id(owner),castId:e.action?.castId,x,y,distance:e.distance,radius:r});
  }
  function shards(ctx,x,y,r,age,life,seed){
    const fade=clamp(1-age/life),count=Math.min(8,limits.shards-frame.shards);ctx.save();ctx.strokeStyle='#c5f5f5';ctx.lineWidth=2;ctx.globalAlpha=fade;
    for(let i=0;i<count;i++){const a=i*TAU/8+hash(i,seed)*.25,d=r*(.25+.65*age/life),len=4+7*fade;ctx.beginPath();ctx.moveTo(x+Math.cos(a)*d,y+Math.sin(a)*d*.65);ctx.lineTo(x+Math.cos(a)*(d+len),y+Math.sin(a)*(d+len)*.65);ctx.stroke();frame.shards++;}
    ctx.restore();
  }
  function drawRyu(ctx,owner,s,ground){
    if(!s)return;
    if(!ground&&s.action&&!s.action.released)drawCharge(ctx,owner,s.action);
    if(!ground&&s.action?.released)drawBarrageMuzzle(ctx,owner,s.action);
    if(!ground){
      for(const pellet of s.scatter||[])drawScatter(ctx,pellet,owner);
      if(owner.moves?.some(m=>m.id==='jjk-ryu-maximum')){
        ctx.save();ctx.translate(owner.x,owner.y-73);ctx.lineWidth=1;
        for(let i=0;i<3;i++){const x=(i-1)*7;ctx.beginPath();ctx.moveTo(x,-3);ctx.lineTo(x+2,0);ctx.lineTo(x,3);ctx.lineTo(x-2,0);ctx.closePath();
          ctx.fillStyle=i<(s.coreCharge||0)?'#c5faff':'#19333e';ctx.strokeStyle='#75a7b4';ctx.fill();ctx.stroke();}ctx.restore();
      }
    }
    for(const e of s.effects||[]){
      if(e.kind==='scatter')continue;
      if(e.kind==='beam'){if(!ground)drawBeam(ctx,e,owner);continue;}
      if(e.kind==='muzzle')continue;
      const t=clamp(e.age/e.life),r=e.kind==='explosion'?e.radius:Math.max(12,e.radius);
      ctx.save();ctx.globalAlpha=(1-t)*(ground?.3:.65);ctx.strokeStyle=ground?'#839c99':'#b4f6ff';ctx.lineWidth=ground?1:3;
      ctx.beginPath();ctx.ellipse(e.x,e.y-(ground?0:e.kind==='explosion'?12:48),r*(.4+.6*t),r*(ground?1:.65)*(.4+.6*t),0,0,TAU);ctx.stroke();ctx.restore();
      if(!ground)shards(ctx,e.x,e.y-(e.kind==='explosion'?12:48),r,e.age,e.life,e.serial||id(e));
    }
    if(ground&&s.action?.mode==='jjk-ryu-impact'&&!s.action.released){const f=s.action;ctx.save();ctx.globalAlpha=.3;ctx.strokeStyle='#9bf0f6';ctx.beginPath();ctx.arc(f.tx,f.ty,f.radius,0,TAU);ctx.stroke();ctx.restore();}
  }
  function bezier(c,t){const a=1-t;return {x:a*a*a*c[0].x+3*a*a*t*c[1].x+3*a*t*t*c[2].x+t*t*t*c[3].x,y:a*a*a*c[0].y+3*a*a*t*c[1].y+3*a*t*t*c[2].y+t*t*t*c[3].y};}
  function arcSamples(c,count){
    const lut=[{t:0,s:0}],first=bezier(c,0);let previous=first,length=0;
    for(let i=1;i<=96;i++){const p=bezier(c,i/96);length+=Math.hypot(p.x-previous.x,p.y-previous.y);lut.push({t:i/96,s:length});previous=p;}
    const points=[];let at=1;
    for(let i=0;i<count;i++){const wanted=length*i/(count-1);while(at<96&&lut[at].s<wanted)at++;const a=lut[at-1],b=lut[at];points.push(bezier(c,mix(a.t,b.t,(wanted-a.s)/(b.s-a.s||1))));}
    return points;
  }
  function bladeCurves(mark){
    const n=budget().trailPoints;let cached=trailCache.get(mark);if(cached?.count===n)return cached.curves;
    const curves=[],r=mark.radius*.89;
    if(mark.kind==='blade'){
      const arc=mark.arc??Math.PI*2/3,a=-arc/2,b=arc/2,k=4/3*Math.tan((b-a)/4),p0={x:r*Math.cos(a),y:r*Math.sin(a)},p3={x:r*Math.cos(b),y:r*Math.sin(b)};
      curves.push(arcSamples([p0,{x:p0.x-Math.sin(a)*r*k,y:p0.y+Math.cos(a)*r*k},{x:p3.x+Math.sin(b)*r*k,y:p3.y-Math.cos(b)*r*k},p3],n));
    }else for(let i=-1;i<=1;i++){const y=i*mark.radius*.24,w=mark.radius*.55;curves.push(arcSamples([{x:-w,y:y-w*.35},{x:-w*.2,y:y-w*.12},{x:w*.4,y:y+w*.2},{x:w,y:y+w*.45}],n));}
    trailCache.set(mark,{count:n,curves});return curves;
  }
  function ribbon(ctx,points,head,tail,width){
    const left=[],right=[];
    for(let i=0;i<points.length;i++){const u=i/(points.length-1);if(u>head||u<head-tail)continue;
      const a=points[Math.max(0,i-1)],b=points[Math.min(points.length-1,i+1)],len=Math.hypot(b.x-a.x,b.y-a.y)||1,w=width*Math.sin(Math.PI*clamp((u-head+tail)/tail));
      left.push({x:points[i].x-(b.y-a.y)/len*w,y:points[i].y+(b.x-a.x)/len*w});right.push({x:points[i].x+(b.y-a.y)/len*w,y:points[i].y-(b.x-a.x)/len*w});}
    if(left.length<2)return;ctx.beginPath();ctx.moveTo(left[0].x,left[0].y);for(const p of left.slice(1))ctx.lineTo(p.x,p.y);for(let i=right.length-1;i>=0;i--)ctx.lineTo(right[i].x,right[i].y);ctx.closePath();ctx.fill();
  }
  function drawYuta(ctx,s,ground){
    for(const mark of s?.marks||[]){if(!['blade','rika'].includes(mark.kind))continue;
      const fade=clamp(1-mark.age/.32);
      if(ground){if(mark.kind==='rika'){ctx.save();ctx.globalAlpha=fade*.12;ctx.strokeStyle='#b4d7d8';ctx.beginPath();ctx.arc(mark.x,mark.y,mark.radius,0,TAU);ctx.stroke();ctx.restore();}continue;}
      ctx.save();ctx.translate(mark.x,mark.y-(mark.kind==='blade'?12:0));ctx.rotate(mark.aim);ctx.globalAlpha=fade;
      const curves=bladeCurves(mark),head=clamp(.22+mark.age/.12);
      for(const points of curves){ctx.fillStyle='#75c9db';ribbon(ctx,points,head,.5,mark.kind==='blade'?5:3);ctx.fillStyle='#ecffff';ribbon(ctx,points,head,.43,1.25);}
      ctx.restore();frame.draws.push({kind:'arc-length-trail',mode:mark.kind,points:budget().trailPoints,curves:curves.length});
    }
  }
  function drawUroAir(ctx,owner,s){
    const screen=s?.screen;
    if(screen){
      ctx.save();ctx.strokeStyle='#b0e6ef';ctx.globalAlpha=.18;ctx.lineWidth=1;ctx.beginPath();ctx.arc(owner.x,owner.y,screen.radius,0,TAU);ctx.stroke();
      ctx.globalAlpha=.8;ctx.fillStyle='#d4f8ff';for(let i=0;i<screen.budget;i++)ctx.fillRect(owner.x-16+i*5,owner.y-44,3,3);ctx.restore();
      for(const f of screen.flashes||[])shards(ctx,f.x,f.y,8,f.age,.22,id(f));
    }
    for(const b of G.JjkUro?.effects||[])if(b.owner===owner){
      ctx.save();ctx.globalAlpha=.12*clamp(1-b.age/b.duration);ctx.strokeStyle='#b8dfe5';ctx.lineWidth=1;shapePath(ctx,b);ctx.stroke();ctx.restore();
      if(!b.done)continue;
      const t=b.age-b.release,life=Math.max(.05,b.duration-b.release),cx=b.mode==='uro-collapse'?b.tx:b.x,cy=b.mode==='uro-collapse'?b.ty:b.y;
      if(t<.18)shards(ctx,cx+Math.cos(b.aim)*(b.mode==='uro-collapse'?0:b.range*.6),cy+Math.sin(b.aim)*(b.mode==='uro-collapse'?0:b.range*.6),b.mode==='uro-collapse'?b.radius*.6:b.range*.15,t,life,id(b));
    }
  }
  function drawAir(ctx){
    if(lastAir===frameNumber)beginFrame();lastAir=frameNumber;if(!G.JujutsuVFX.enabled||terminal())return;
    for(const owner of owners()){
      const dex=owner.mon?.dex??owner.dex;
      if(dex===30014)drawRyu(ctx,owner,G.JjkRyu?.stateFor(owner),false);
      else if(dex===30013)drawYuta(ctx,G.JujutsuYuta?.stateFor(owner),false);
      else if(dex===30015)drawUroAir(ctx,owner,G.JjkUro?.stateFor(owner));
    }
  }
  function drawGround(ctx){if(!G.JujutsuVFX.enabled||terminal())return;for(const owner of owners()){const dex=owner.mon?.dex??owner.dex;if(dex===30014)drawRyu(ctx,owner,G.JjkRyu?.stateFor(owner),true);else if(dex===30013)drawYuta(ctx,G.JujutsuYuta?.stateFor(owner),true);}}
  const oldAir=C.drawAirFields,oldGround=C.drawGroundFields,oldClear=C.clearFields,start=G.Game.startRun;
  C.drawAirFields=function(ctx){oldAir.call(this,ctx);drawAir(ctx);};
  C.drawGroundFields=function(ctx){oldGround.call(this,ctx);drawGround(ctx);};
  C.clearFields=function(owner){clear(owner);return oldClear.call(this,owner);};
  G.Game.startRun=function(...args){epochReset();return start.apply(this,args);};
  G.JujutsuVFX={enabled:true,drawBackground,drawAir,drawGround,clear,limits,
    setQuality(value){quality=['high','low'].includes(value)?value:'auto';clear();},
    inspect(){return {epoch,capturesTotal,...frame,snapshots:pool.filter(s=>s.entry).length,bufferBytes:pool.reduce((sum,s)=>sum+s.canvas.width*s.canvas.height*4,0),
      folds:[...folds.values()].map(e=>({castId:e.castId,owner:id(e.owner),epoch:e.epoch,age:e.local,captured:e.captured,hasSnapshot:!!e.slot,rect:{...e.rect},capture:e.capture} ))};},
    algorithms:{affine,inverse,multiply,noise,arcSamples}};
})();
