/* Isolated visual study. No Combat, Player, World or production runtime hooks. */
(async()=>{
  'use strict';
  const canvas=document.querySelector('#demo'),ctx=canvas.getContext('2d'),ui=document.querySelector('#state'),seek=document.querySelector('#seek'),tierUI=document.querySelector('#tier');
  const clamp=x=>Math.max(0,Math.min(1,x)),ease=x=>{x=clamp(x);return x*x*(3-2*x);},mix=(a,b,t)=>a+(b-a)*t;
  let mode='body',tier=1,direction='right',spacing='near',time=0,playing=true,last=0,background,width=1000,height=600,bodyH=64;
  const descriptions={body:'雙足、身軀與頭肩的投影先由腳底拉長，細黑頸部再接向目標；只有確認接觸後才延到下一人。沒有圓盤、粗管或內部亮紋。',group:'被捕者的人體投影交疊成掌片：掌腹連續、指間留出地面；目標原地不被拖移。提高展示階段才能逐一接出更多目標。',sewing:'影縫從鹿丸兩足的同一片身影離地，高拱後將長曲尖端刺向目標側身；不是從敵腳冒出的垂直冰刺。',neck:'補充研究：黑影以皮膚覆層從踝爬上腿、胸，前沿抵達胸口後才長五指；黑層裁切於實際人物alpha，不在體外生成黑手。'};
  await ShikamaruArt.ready;
  const masks=new Map();
  function actorMask(pose='idle'){
    const key=pose+':'+bodyH;if(masks.has(key))return masks.get(key);
    const image=document.createElement('canvas');image.width=image.height=bodyH*2;const c=image.getContext('2d');
    ShikamaruArt.draw(c,{}, {x:bodyH,y:bodyH*1.85,height:bodyH,state:pose==='idle'?'idle':'cast',time:.4,dir:0,pose:pose==='idle'?null:{kind:'shadow',phase:'release',phaseAge:.2,phaseDuration:.4,aim:Math.PI/2}});
    c.globalCompositeOperation='source-in';c.fillStyle='#050506';c.fillRect(0,0,image.width,image.height);masks.set(key,image);return image;
  }
  function resize(){width=Math.round(canvas.clientWidth);height=width<500?480:620;bodyH=width<500?40:64;canvas.width=width;canvas.height=height;masks.clear();
    background=document.createElement('canvas');background.width=width;background.height=height;const c=background.getContext('2d');c.imageSmoothingEnabled=false;
    const n=12,tile=G.Tiles.paintChunk(0,0,n,()=> 'floor',(x,y)=>.57+.16*Math.sin(x*.016+y*.008),0,173);
    for(let y=0;y<height;y+=tile.height*2)for(let x=0;x<width;x+=tile.width*2)c.drawImage(tile,x,y,tile.width*2,tile.height*2);
  }
  function layout(){const mobile=width<500,count=tier===1?1:tier===2?2:mode==='sewing'?3:4;
    if(mode==='group'&&spacing==='near')return {owner:{x:width*.25,y:height*.77},targets:[{x:width*.48,y:height*.32},{x:width*.65,y:height*.31},{x:width*.79,y:height*.39},{x:width*.57,y:height*.47}],count};
    if(mode==='sewing'){
      const axis={right:{x:1,y:0},left:{x:-1,y:0},up:{x:0,y:-1},down:{x:0,y:1}}[direction],owner={x:width*(direction==='left'?.78:direction==='right'?.21:.5),y:height*(direction==='up'?.8:direction==='down'?.31:.69)},span=Math.min(width*.47,bodyH*3.6);
      const targets=Array.from({length:3},(_,i)=>{const d=span*(.72+i*.14),side=(i-1)*bodyH*.27;return {x:owner.x+axis.x*d-axis.y*side,y:owner.y+axis.y*d+axis.x*side};});return {owner,targets,count,axis};
    }
    return {owner:{x:width*(mobile?.29:.3),y:height*.74},targets:[{x:width*.64,y:height*.39},{x:width*.77,y:height*.55},{x:width*.56,y:height*.23},{x:width*.36,y:height*.4}],count};
  }
  function body(actor,pose='idle',target=false){ShikamaruArt.draw(ctx,{}, {x:actor.x,y:actor.y,height:bodyH,state:pose==='idle'?'idle':'cast',time:.4,dir:target?0:2,pose:pose==='idle'?null:{kind:'shadow',phase:'release',phaseAge:.2,phaseDuration:.4,aim:0}});}
  function projection(actor,dx,dy,length,alpha=1,pose='idle',across=null){
    const mask=actorMask(pose);ctx.save();ctx.globalAlpha=alpha;ctx.translate(actor.x,actor.y);ctx.transform(across===null?.54:-dy*across,across===null?0:dx*across,-dx*length/bodyH,-dy*length/bodyH,0,0);ctx.drawImage(mask,-bodyH,-bodyH*1.85);ctx.restore();
  }
  function narrowLink(a,b,progress,index=0,wide=2){
    if(progress<=0)return;const dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1,nx=-dy/d,ny=dx/d,points=[];
    const count=Math.max(2,Math.ceil(progress*32));
    for(let i=0;i<=count;i++){const u=i/count*progress,bend=Math.sin(u*Math.PI)*(Math.sin(u*4.3+index*1.9)*bodyH*.12);points.push({x:a.x+dx*u+nx*bend,y:a.y+dy*u+ny*bend});}
    ctx.fillStyle='#050506';ctx.beginPath();for(let side=0;side<2;side++)for(let j=0;j<points.length;j++){const i=side?points.length-1-j:j,p=points[i],w=wide*(1-i/(points.length-1)*.68)*(side?-1:1);if(!side&&!j)ctx.moveTo(p.x+nx*w,p.y+ny*w);else ctx.lineTo(p.x+nx*w,p.y+ny*w);}ctx.closePath();ctx.fill();
    return points.at(-1);
  }
  function palm(a,targets,amount){
    if(!targets.length||amount<=0)return;
    if(spacing==='far'){let previous=a;for(const target of targets){projection(target,-.4,.92,bodyH*.95,1,'idle',.95);narrowLink(previous,target,amount,0,width<500?1:1.7);previous=target;}return;}
    const cx=targets.reduce((v,p)=>v+p.x,0)/targets.length,cy=Math.max(...targets.map(p=>p.y))+bodyH*.75;
    // There is no centre wedge: the palm is only the union of real body projections.
    for(let i=0;i<targets.length;i++){
      const target=targets[i],end={x:cx+(i-(targets.length-1)/2)*bodyH*.13,y:cy+(i%2)*bodyH*.11},dx=end.x-target.x,dy=end.y-target.y,d=Math.hypot(dx,dy)||1;
      projection(target,dx/d,dy/d,d*amount,1,'idle',1.1+(i%2)*.15);
    }
    narrowLink(a,{x:cx,y:cy-bodyH*.08},amount,3,width<500?1.3:2.1);
  }
  function arch(a,b,progress,index){
    if(progress<=0)return {stage:'ground',progress,tip:{...a}};const dx=b.x-a.x,dy=b.y-a.y,points=[],steps=Math.max(2,Math.ceil(60*progress)),lift=Math.max(bodyH*(1.3+index*.22),Math.abs(dy)/Math.PI+bodyH*.7);
    const groundDY=dy+bodyH*.43,groundDistance=Math.hypot(dx,groundDY)||1,nx=-groundDY/groundDistance,ny=dx/groundDistance,verticalWeight=Math.abs(nx)**3;
    // A vertical ground ray needs a lateral bow before elevation is projected.
    // Even the single Lv1 tendril has a visible open C, not a straight stake.
    const sideBow=bodyH*(.9+index*.45)*(index%2?-1:1)*verticalWeight;
    for(let i=0;i<=steps;i++){const u=i/steps*progress,s=Math.sin(u*Math.PI);points.push({x:a.x+dx*u+s*((index-1)*bodyH*.12+nx*sideBow),y:a.y+dy*u+s*(ny*sideBow-lift)});}
    ctx.fillStyle='#030304';ctx.beginPath();for(let side=0;side<2;side++)for(let j=0;j<points.length;j++){const i=side?points.length-1-j:j,p=points[i],u=i/(points.length-1)*progress,previous=points[Math.max(0,i-1)],next=points[Math.min(points.length-1,i+1)],dx=next.x-previous.x,dy=next.y-previous.y,d=Math.hypot(dx,dy)||1,w=bodyH*(.045+.105*Math.sin(Math.PI*u)**.8)*Math.min(1,(progress-u)/.18)*(side?-1:1);if(!side&&!j)ctx.moveTo(p.x-dy/d*w,p.y+dx/d*w);else ctx.lineTo(p.x-dy/d*w,p.y+dx/d*w);}ctx.closePath();ctx.fill();
    const slope=dy+Math.PI*(ny*sideBow-lift)*Math.cos(Math.PI*progress);return {stage:progress>.995?'contact':Math.abs(slope)<bodyH*.3?'crest':slope>0?'descent':'rise',progress,tip:points.at(-1),lift,slope,sideBow,groundNormal:{x:nx,y:ny}};
  }
  function skinOverlay(actor,progress){
    const mask=actorMask(),layer=document.createElement('canvas');layer.width=layer.height=bodyH*2;const c=layer.getContext('2d'),foot=bodyH*1.85,top=foot-bodyH*.72*progress;
    c.strokeStyle='#030304';c.lineWidth=bodyH*.095;c.lineCap='round';
    for(let y=foot;y>top;y-=bodyH*.15){c.beginPath();c.moveTo(bodyH-bodyH*.26,y);c.bezierCurveTo(bodyH-bodyH*.1,y-bodyH*.18,bodyH+bodyH*.15,y+bodyH*.04,bodyH+bodyH*.29,y-bodyH*.15);c.stroke();}
    if(progress>.8)for(let i=0;i<5;i++){c.beginPath();c.moveTo(bodyH+(i-2)*bodyH*.04,top+bodyH*.18);c.quadraticCurveTo(bodyH+(i-2)*bodyH*.09,top+bodyH*.04,bodyH+(i-2)*bodyH*.065,top-bodyH*.04*(i%2+1));c.stroke();}
    c.globalCompositeOperation='destination-in';c.drawImage(mask,0,0);ctx.drawImage(layer,actor.x-bodyH,actor.y-foot);
  }
  function render(){
    ctx.clearRect(0,0,width,height);ctx.drawImage(background,0,0);ctx.imageSmoothingEnabled=false;
    const {owner,targets,count,axis}=layout(),t=time%8,release=ease((t-1)/1.15),retreat=1-ease((t-6.2)/1.3),active=targets.slice(0,count),connected=[],sewingFronts=[];
    const dx=active[0].x-owner.x,dy=active[0].y-owner.y,d=Math.hypot(dx,dy)||1;
    const projectionLength=bodyH*(.7+release*.45)*retreat;projection(owner,dx/d,dy/d,projectionLength,1,'seal');
    if(mode==='sewing'&&t>=1&&t<2.2){const bulge=ease((t-1)/1.05);projection(owner,axis.x,axis.y,bodyH*(.65+.42*bulge),1,'seal',.65+.35*bulge);}
    let source={x:owner.x+dx/d*projectionLength*.9,y:owner.y+dy/d*projectionLength*.9};
    if(mode==='body'||mode==='group')for(let i=0;i<count;i++){
      const progress=ease((t-(1.3+i*.78))/.7)*retreat;if(progress<=0)break;
      if(mode==='body'||t<3.1)narrowLink(source,active[i],progress,i,width<500?1.25:1.8);if(progress>.98)connected.push(active[i]);source=active[i];
    }
    if(mode==='group')palm({x:owner.x+dx/d*bodyH*.8,y:owner.y+dy/d*bodyH*.8},connected,ease((t-2.1)/.8)*retreat);
    for(let i=0;i<count;i++){const target=active[i];if(mode!=='group'||!connected.includes(target))projection(target,-.55,.65,bodyH*.65,1);}
    if(mode==='sewing'){
      const rises=Math.min(count,3);for(let i=0;i<rises;i++){const target=active[i],phase=clamp((t-2.1-i*.55)/1.15)*retreat;if(phase>.98)connected.push(target);}
    }
    const bodies=[{...owner,owner:true},...active.map((p,i)=>({...p,index:i}))].sort((a,b)=>a.y-b.y);
    for(const actor of bodies){body(actor,actor.owner&&t>1&&t<6?'seal':'idle',!actor.owner);if(!actor.owner){ctx.font='12px system-ui';ctx.textAlign='center';ctx.fillStyle='#f2f0dd';ctx.fillText(String.fromCharCode(65+actor.index),actor.x,actor.y-bodyH-8);}}
    if(mode==='sewing')for(let i=0;i<Math.min(count,3);i++)sewingFronts.push(arch({x:owner.x+(i-1)*bodyH*.06,y:owner.y}, {x:active[i].x,y:active[i].y-bodyH*.43},ease((t-2.1-i*.55)/1.15)*retreat,i));
    if(mode==='neck')skinOverlay(active[0],ease((t-1.2)/3.2)*retreat);
    const phase=t<1?'足底人體投影':mode==='sewing'&&t<2.1?'腳影形變 → 地面鼓起':t<2.5?'單根延伸':t<6.2?(mode==='sewing'?'離地上升 → 弧頂 → 下落刺入':mode==='neck'?'踝 → 腿 → 胸 → 五指':mode==='group'?'群影交疊／指間負空間':'A接觸 → A接B → B接C'):'沿原路收回';
    ui.textContent=`${phase}　${t.toFixed(2)}s｜${bodyH}px人物｜${count}個展示目標（純視覺）`;seek.value=t;document.querySelector('#explain').textContent=descriptions[mode];
    window.Prototype.state={mode,tier,direction,spacing,time:t,bodyH,owner,targets:active,phase,sewingFronts,connected:connected.length,visualOnly:true};
  }
  window.Prototype={state:null,seek(value){time=Number(value);render();},setMode(value){mode=value;time=0;document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.mode===mode));render();},setTier(value){tier=Number(value);tierUI.value=tier;time=0;render();},setDirection(value){direction=value;document.querySelector('#direction').value=value;time=0;render();},setSpacing(value){spacing=value;document.querySelector('#spacing').value=value;time=0;render();},setPlaying(value){playing=!!value;},render};
  for(const button of document.querySelectorAll('[data-mode]'))button.onclick=()=>{mode=button.dataset.mode;time=0;document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',b===button));render();};
  tierUI.onchange=()=>{tier=+tierUI.value;time=0;render();};document.querySelector('#pause').onclick=()=>{playing=!playing;document.querySelector('#pause').textContent=playing?'暫停':'播放';};document.querySelector('#restart').onclick=()=>{time=0;render();};seek.oninput=()=>{time=+seek.value;playing=false;document.querySelector('#pause').textContent='播放';render();};document.addEventListener('keydown',e=>{if(e.code==='Space'){e.preventDefault();playing=!playing;}});window.addEventListener('resize',()=>{resize();render();});
  document.querySelector('#direction').onchange=e=>window.Prototype.setDirection(e.target.value);document.querySelector('#spacing').onchange=e=>window.Prototype.setSpacing(e.target.value);
  resize();render();function frame(now){if(last&&playing)time+=Math.min(.05,(now-last)/1000);last=now;render();requestAnimationFrame(frame);}requestAnimationFrame(frame);
})().catch(error=>{document.querySelector('#state').textContent=error.stack;throw error;});
