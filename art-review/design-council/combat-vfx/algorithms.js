/* Standalone design experiment. No game hooks and no dependencies. */
(function(root){
  'use strict';
  const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
  const mix=(a,b,t)=>a+(b-a)*t;
  const ease=t=>{t=clamp(t);return t*t*(3-2*t);};
  function hash(i,seed=1){let x=(i^seed)>>>0;x=Math.imul(x^x>>>16,0x7feb352d);x=Math.imul(x^x>>>15,0x846ca68b);return ((x^x>>>16)>>>0)/4294967295;}
  function noise(x,seed){const i=Math.floor(x);return mix(hash(i,seed),hash(i+1,seed),ease(x-i));}
  // Slab intersection: ray parameter is distance because direction is unit length.
  function rayBox(origin,dir,box,radius=0){
    let enter=-Infinity,exit=Infinity;
    for(const axis of ['x','y']){
      const lo=box[axis]-radius,hi=box[axis]+box[axis==='x'?'w':'h']+radius;
      if(Math.abs(dir[axis])<1e-9){if(origin[axis]<lo||origin[axis]>hi)return null;continue;}
      let a=(lo-origin[axis])/dir[axis],b=(hi-origin[axis])/dir[axis];if(a>b)[a,b]=[b,a];
      enter=Math.max(enter,a);exit=Math.min(exit,b);if(enter>exit)return null;
    }
    return exit<0?null:Math.max(0,enter);
  }
  function clippedBeam(origin,aim,range,radius,walls){
    const dir={x:Math.cos(aim),y:Math.sin(aim)};let length=range;
    for(const wall of walls){const hit=rayBox(origin,dir,wall,radius);if(hit!==null)length=Math.min(length,hit);}
    return {origin:{...origin},dir,length,radius,end:{x:origin.x+dir.x*length,y:origin.y+dir.y*length}};
  }
  function segmentDistance(p,a,b){const dx=b.x-a.x,dy=b.y-a.y,t=clamp(((p.x-a.x)*dx+(p.y-a.y)*dy)/(dx*dx+dy*dy||1));return Math.hypot(p.x-a.x-dx*t,p.y-a.y-dy*t);}
  function beamHit(beam,target){return segmentDistance(target,beam.origin,beam.end)<=beam.radius+(target.r||0);}
  function beamProfile(beam,seed=91,segments=36){
    segments=Math.max(2,Math.min(48,segments));
    return Array.from({length:segments+1},(_,i)=>{const u=i/segments;
      const envelope=.16+.84*Math.sin(Math.PI*u)**.35;
      const width=beam.radius*envelope*(.72+.28*(.67*noise(u*11,seed)+.33*noise(u*23,seed+3)));
      return {x:beam.length*u,width};});
  }
  // Map source triangle to destination triangle; destination area can be tiny,
  // but a singular source must be rejected rather than produce NaN transforms.
  function affineTriangle(s,d){
    const x1=s[1].x-s[0].x,y1=s[1].y-s[0].y,x2=s[2].x-s[0].x,y2=s[2].y-s[0].y;
    const det=x1*y2-x2*y1;if(Math.abs(det)<1e-8)return null;
    const u1=d[1].x-d[0].x,v1=d[1].y-d[0].y,u2=d[2].x-d[0].x,v2=d[2].y-d[0].y;
    const a=(u1*y2-u2*y1)/det,c=(u2*x1-u1*x2)/det;
    const b=(v1*y2-v2*y1)/det,f=(v2*x1-v1*x2)/det;
    return {a,b,c,d:f,e:d[0].x-a*s[0].x-c*s[0].y,f:d[0].y-b*s[0].x-f*s[0].y};
  }
  function transform(m,p){return {x:m.a*p.x+m.c*p.y+m.e,y:m.b*p.x+m.d*p.y+m.f};}
  function multiply(a,b){return {a:a.a*b.a+a.c*b.b,b:a.b*b.a+a.d*b.b,c:a.a*b.c+a.c*b.d,d:a.b*b.c+a.d*b.d,e:a.a*b.e+a.c*b.f+a.e,f:a.b*b.e+a.d*b.f+a.f};}
  function inverse(m){const det=m.a*m.d-m.b*m.c;if(Math.abs(det)<1e-8)return null;return {a:m.d/det,b:-m.b/det,c:-m.c/det,d:m.a/det,e:(m.c*m.f-m.d*m.e)/det,f:(m.b*m.e-m.a*m.f)/det};}
  function skyMesh(rect,cols=6,rows=4,strength=0){
    const vertices=[];strength=clamp(strength);
    for(let y=0;y<=rows;y++)for(let x=0;x<=cols;x++){
      const u=x/cols,v=y/rows,s={x:rect.x+u*rect.w,y:rect.y+v*rect.h};
      // Fold is continuous at shared vertices and fixed at the outer boundary.
      const window=Math.sin(Math.PI*u)*Math.sin(Math.PI*v);
      const crease=Math.sin(u*Math.PI*2+.3)*Math.min(rect.w/cols*.42,28)*window*strength;
      vertices.push({source:s,dest:{x:s.x+crease,y:s.y+Math.sin(u*Math.PI)*window*strength*rect.h*.13}});
    }
    const triangles=[];
    for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){
      const a=y*(cols+1)+x,b=a+1,c=a+cols+1,d=c+1;
      triangles.push([a,b,d],[a,d,c]);
    }
    return {vertices,triangles};
  }
  function drawTriangle(ctx,image,source,dest){
    const m=affineTriangle(source,dest);if(!m)return false;
    ctx.save();ctx.beginPath();ctx.moveTo(dest[0].x,dest[0].y);ctx.lineTo(dest[1].x,dest[1].y);ctx.lineTo(dest[2].x,dest[2].y);ctx.closePath();ctx.clip();
    ctx.transform(m.a,m.b,m.c,m.d,m.e,m.f);ctx.drawImage(image,0,0);ctx.restore();return true;
  }
  function reflect(v,n){const len=Math.hypot(n.x,n.y);if(len<1e-8)return {x:v.x,y:v.y};const nx=n.x/len,ny=n.y/len,dot=v.x*nx+v.y*ny;return {x:v.x-2*dot*nx,y:v.y-2*dot*ny};}
  function bezier(c,t){const a=1-t;return {x:a*a*a*c[0].x+3*a*a*t*c[1].x+3*a*t*t*c[2].x+t*t*t*c[3].x,y:a*a*a*c[0].y+3*a*a*t*c[1].y+3*a*t*t*c[2].y+t*t*t*c[3].y};}
  function arcLengthSamples(control,count=32,lutSteps=96){
    const lut=[{t:0,s:0}],points=[bezier(control,0)];let length=0;
    for(let i=1;i<=lutSteps;i++){const p=bezier(control,i/lutSteps),previous=points.at(-1);length+=Math.hypot(p.x-previous.x,p.y-previous.y);points.push(p);lut.push({t:i/lutSteps,s:length});}
    const result=[];let at=1;
    for(let i=0;i<count;i++){
      const desired=length*i/(count-1);while(at<lut.length-1&&lut[at].s<desired)at++;
      const a=lut[at-1],b=lut[at],t=mix(a.t,b.t,(desired-a.s)/(b.s-a.s||1));result.push(bezier(control,t));
    }
    return {points:result,length};
  }
  function ribbon(points,width,head=1,tailLength=.28){
    const left=[],right=[];
    for(let i=0;i<points.length;i++){
      const u=i/(points.length-1);if(u>head||u<head-tailLength)continue;
      const prev=points[Math.max(0,i-1)],next=points[Math.min(points.length-1,i+1)],len=Math.hypot(next.x-prev.x,next.y-prev.y)||1;
      const nx=-(next.y-prev.y)/len,ny=(next.x-prev.x)/len,w=width*Math.sin(Math.PI*clamp((u-head+tailLength)/tailLength));
      left.push({x:points[i].x+nx*w,y:points[i].y+ny*w});right.push({x:points[i].x-nx*w,y:points[i].y-ny*w});
    }
    return [...left,...right.reverse()];
  }
  function fanHit(origin,aim,range,arc,target){const dx=target.x-origin.x,dy=target.y-origin.y,d=Math.hypot(dx,dy),delta=Math.atan2(Math.sin(Math.atan2(dy,dx)-aim),Math.cos(Math.atan2(dy,dx)-aim));return d<=range+(target.r||0)&&Math.abs(delta)<=arc/2+Math.asin(Math.min(1,(target.r||0)/(d||1)));}
  class CastClock{
    constructor(contact,duration){this.contact=contact;this.duration=duration;this.reset();}
    reset(){this.age=0;this.hit=false;this.cancelled=false;this.events=0;}
    advance(dt,playing=true){if(!playing||this.cancelled||!Number.isFinite(dt))return false;this.age+=Math.max(0,dt);if(!this.hit&&this.age>=this.contact){this.hit=true;this.events++;return true;}return false;}
    cancel(){this.cancelled=true;}
  }
  // Design-contract experiment. No runtime actor is mutated by these helpers.
  function quantityBenefits(picks,consumers,maxPicks=20){
    return consumers.map(c=>{
      const count=q=>Math.min(c.cap,Math.floor(c.base*1.25**q));
      const before=count(picks),after=count(Math.min(maxPicks,picks+1));let nextChange=null;
      for(let q=picks+1;q<=maxPicks;q++)if(count(q)>before){nextChange=q-picks;break;}
      return {...c,before,after,nextChange,eligible:nextChange!==null};
    });
  }
  class PulseLedger{
    constructor(epoch){this.epoch=epoch;this.seen=new Set();}
    nextRun(epoch){this.epoch=epoch;this.seen.clear();}
    accept(packet,target){if(packet.runEpoch!==this.epoch)return false;const key=JSON.stringify([packet.owner,packet.castId,packet.pulse,target]);if(this.seen.has(key))return false;this.seen.add(key);return true;}
  }
  function outerSplash(primary,candidates,range,rate){
    const excluded=new Set(primary.map(p=>p.id)),packets=[];
    for(const target of candidates){
      if(excluded.has(target.id)||packets.some(p=>p.id===target.id))continue;
      let damage=0;
      for(const hit of primary)if(Math.hypot(hit.x-target.x,hit.y-target.y)<=range)damage=Math.max(damage,hit.primaryDirectDamage*rate);
      if(damage>0)packets.push({id:target.id,damage});
    }
    return packets;
  }
  function allocateFolds(casts,low=false){
    const ordered=casts.toSorted((a,b)=>Number(b.local)-Number(a.local)||a.distance-b.distance||a.castId-b.castId);
    const cap=low?1:2,selected=ordered.slice(0,cap),triangles=low?12:48;
    return ordered.map(c=>({castId:c.castId,snapshot:selected.includes(c),texturedTriangles:selected.includes(c)?triangles/selected.length:0,panels:selected.includes(c)?0:2}));
  }
  const api={clamp,mix,ease,hash,noise,rayBox,clippedBeam,segmentDistance,beamHit,beamProfile,affineTriangle,transform,multiply,inverse,skyMesh,drawTriangle,reflect,bezier,arcLengthSamples,ribbon,fanHit,CastClock,quantityBenefits,PulseLedger,outerSplash,allocateFolds};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.VFXAlgorithms=api;
})(typeof globalThis==='object'?globalThis:this);
