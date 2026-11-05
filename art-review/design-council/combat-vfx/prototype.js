/* All experiments are code-native Canvas2D; no image assets, shaders or libraries. */
(() => {
  'use strict';
  const A=VFXAlgorithms,canvas=document.getElementById('view'),ctx=canvas.getContext('2d'),W=860,H=490;
  const timeInput=document.getElementById('time'),status=document.getElementById('status');
  const bg=document.createElement('canvas');bg.width=W;bg.height=H;const back=bg.getContext('2d');
  let demo='beam',time=0,playing=true,last=performance.now(),frames=0,drawTimes=[],hitLog=[],lastStats={};
  const clocks={beam:new A.CastClock(.65,1.2),sky:new A.CastClock(.85,1.5),slash:new A.CastClock(.42,1.1)};
  const descriptions={
    beam:[' coherent profile ＋ conservative collision',[['視覺算法','固定種子分形噪聲、漸縮外殼、白熱內核。沿線形狀在施放時生成，繪製時只改包絡。'],['命中算法','射線與擴張AABB的slab相交，先截斷再用膠囊碰撞判定目標。裝飾永遠留在命中寬度內。'],['成本','桌機48個輪廓點、手機20點；無模糊陰影、無逐幀隨機幾何。']]],
    sky:[' shared mesh ＋ affine texture mapping',[['視覺算法','背景快照以共享頂點網格變形，再逐三角片仿射貼圖。亮摺線只保留主折角，避免滿屏線框。'],['機制邊界','折射只變畫面，不搬動敵人或碰撞。反射用 v−2(v·n)n，反射次數仍由技能狀態決定。'],['成本','全畫面桌機最多48貼圖三角片，手機12片。雙折面共享預算，超額保留兩片明暗面。原型共用靜態背景，未測正式截圖成本。']]],
    slash:[' cubic spline ＋ arc-length ribbon',[['視覺算法','三次Bezier曲線先建弧長查表，再等距取樣。帶狀拖尾沿曲線法線生成，頭部追隨出手進度。'],['命中算法','接觸事件只在0.42秒觸發一次；實際扇形與移動的刀痕分開，不能每幀碰到就傷害。'],['成本','桌機36個軌跡點、手機18點；12片固定撞擊碎片，取消／死亡不留下延遲事件。']]]
  };
  function paintBackground(){
    back.fillStyle='#193b40';back.fillRect(0,0,W,H);
    for(let y=0;y<H;y+=30)for(let x=0;x<W;x+=30){back.fillStyle=((x+y)/30)%2?'#1e4248':'#21484c';back.fillRect(x+1,y+1,28,28);}
    back.strokeStyle='#547c7d';back.lineWidth=2;
    for(let x=90;x<W;x+=140){back.beginPath();back.moveTo(x,80);back.lineTo(x+50,400);back.stroke();}
    back.fillStyle='#35616a';for(let i=0;i<5;i++)back.fillRect(140+i*133,160+(i%2)*65,40,120);
    back.font='15px system-ui';back.fillStyle='#88a9ad';back.fillText('SOURCE WORLD / 不變的背景與角色座標',24,38);
  }
  paintBackground();
  const walls=[{x:670,y:125,w:45,h:245}],origin={x:115,y:270};
  const beam=A.clippedBeam(origin,-.11,660,24,walls),profiles={high:A.beamProfile(beam,91,48),low:A.beamProfile(beam,91,20)};
  const targets=[{x:310,y:248,r:15},{x:475,y:230,r:15},{x:735,y:202,r:15},{x:450,y:340,r:15}];
  const slashControl=[{x:360,y:170},{x:610,y:105},{x:610,y:430},{x:360,y:365}];
  const slashSamples={high:A.arcLengthSamples(slashControl,36),low:A.arcLengthSamples(slashControl,18)};
  const slashOrigin={x:335,y:270},slashTargets=[{x:500,y:220,r:15},{x:540,y:280,r:15},{x:480,y:335,r:15},{x:220,y:260,r:15}];
  function text(value,x,y,color='#def6f4',size=15){ctx.fillStyle=color;ctx.font=`${size}px system-ui`;ctx.fillText(value,x,y);}
  function actor(x,y,r=15,hit=false){ctx.fillStyle='#0e2329';ctx.beginPath();ctx.ellipse(x,y+14,r+5,r*.4,0,0,Math.PI*2);ctx.fill();ctx.fillStyle=hit?'#b4f2d6':'#dbb9ae';ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();ctx.strokeStyle=hit?'#60d8a1':'#795f65';ctx.lineWidth=2;ctx.stroke();}
  function polygon(points,fill){if(points.length<3)return;ctx.fillStyle=fill;ctx.beginPath();ctx.moveTo(points[0].x,points[0].y);for(const p of points.slice(1))ctx.lineTo(p.x,p.y);ctx.closePath();ctx.fill();}
  function stage(contact,end){return time<contact?'準備 / 尚未傷害':time<end?'接觸 / 一次結算':'回復 / 保留走位';}
  function drawBeam(low,bounds){
    ctx.drawImage(bg,0,0);ctx.fillStyle='#7c6758';ctx.fillRect(walls[0].x,walls[0].y,walls[0].w,walls[0].h);
    text('牆體：外殼也會先被截斷',620,104,'#d9c1a5',13);actor(origin.x,origin.y,21);
    for(const t of targets){const hit=clocks.beam.hit&&A.beamHit(beam,t);actor(t.x,t.y,t.r,hit);text(hit?'命中':'未命中',t.x-20,t.y+41,hit?'#95efc6':'#e2b7a9',12);}
    ctx.save();ctx.translate(origin.x,origin.y);ctx.rotate(-.11);
    if(bounds){ctx.strokeStyle='#a4bfc588';ctx.setLineDash([5,6]);ctx.strokeRect(0,-beam.radius,beam.length,beam.radius*2);ctx.setLineDash([]);}
    if(time<.65){const r=3+15*A.ease(time/.65);ctx.strokeStyle='#a0eff8';ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(0,0,r*.5,r,0,0,Math.PI*2);ctx.stroke();ctx.fillStyle='#e8ffff';ctx.fillRect(-3,-3,6,6);}
    if(time>=.65&&time<1.2){const age=time-.65,fade=1-age/.55,profile=profiles[low?'low':'high'];ctx.globalAlpha=fade;
      polygon([...profile.map(p=>({x:p.x,y:p.width})),...profile.toReversed().map(p=>({x:p.x,y:-p.width}))],'#45cce9');
      ctx.strokeStyle='#ccfbff';ctx.lineWidth=13;ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(beam.length,0);ctx.stroke();ctx.strokeStyle='#fff';ctx.lineWidth=5;ctx.stroke();}
    ctx.restore();text(stage(.65,1.2),26,H-30);text('輪廓界線 ≠ 追加碰撞',W-220,H-30,'#93c2cc',13);
  }
  function drawSky(low,bounds){
    ctx.drawImage(bg,0,0);const double=document.getElementById('double').checked;
    const rectangles=double?[{x:195,y:110,w:270,h:270},{x:475,y:110,w:250,h:270}]:[{x:240,y:100,w:390,h:285}];
    const strength=time<.85?A.ease(time/.85):time<1.5?1-A.ease((time-.85)/.65):0;
    const allocation=A.allocateFolds(rectangles.map((r,i)=>({castId:i+1,local:i===0,distance:i*50})),low);let triangles=0,panels=0;
    for(let index=0;index<rectangles.length;index++){
      const rect=rectangles[index],budget=allocation.find(a=>a.castId===index+1),cols=double||low?3:6,rows=low?2:4;
      const mesh=A.skyMesh(rect,cols,rows,strength);
      // Source is shared immutable static background. Runtime pool/snapshot capture
      // costs are not claimed by this two-fold composite experiment.
      if(budget.snapshot){for(const tri of mesh.triangles)A.drawTriangle(ctx,bg,tri.map(i=>mesh.vertices[i].source),tri.map(i=>mesh.vertices[i].dest));triangles+=mesh.triangles.length;}
      else{const x=rect.x+rect.w*.5,y=rect.y,h=rect.h;polygon([{x:rect.x,y},{x,y:y+h*.12},{x,y:y+h},{x:rect.x,y:y+h*.88}],'#66919d55');polygon([{x,y:y+h*.12},{x:rect.x+rect.w,y},{x:rect.x+rect.w,y:y+h*.88},{x,y:y+h}],'#b6e5e92b');panels+=2;}
      const crease=mesh.vertices.filter((v,i)=>i%(cols+1)===Math.floor(cols/2));ctx.strokeStyle='#d7ffff';ctx.lineWidth=3;ctx.globalAlpha=.25+.65*strength;ctx.beginPath();crease.forEach((v,i)=>i?ctx.lineTo(v.dest.x,v.dest.y):ctx.moveTo(v.dest.x,v.dest.y));ctx.stroke();ctx.globalAlpha=1;
      if(bounds){ctx.strokeStyle='#b9d4d066';ctx.setLineDash([5,6]);ctx.strokeRect(rect.x,rect.y,rect.w,rect.h);ctx.setLineDash([]);}
    }
    lastStats={texturedTriangles:triangles,fallbackPanels:panels,folds:rectangles.length};
    actor(177,300,21);actor(505,275,15,clocks.sky.hit);text('背景折射；角色仍在原座標',395,326,'#b7e8db',13);
    const v={x:1,y:.3},n={x:-.8,y:-.6},ref=A.reflect(v,n),p={x:560,y:140};
    ctx.lineWidth=3;ctx.strokeStyle='#f5c79e';ctx.beginPath();ctx.moveTo(p.x-v.x*100,p.y-v.y*100);ctx.lineTo(p.x,p.y);ctx.stroke();ctx.strokeStyle='#9cf5ee';ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(p.x+ref.x*100,p.y+ref.y*100);ctx.stroke();
    text('v − 2(v·n)n',550,95,'#bff8ed',13);text(stage(.85,1.5),26,H-30);text(`${triangles} triangles / ${panels} fallback panels`,W-290,H-30,'#93c2cc',13);
  }
  function drawSlash(low,bounds){
    ctx.drawImage(bg,0,0);actor(slashOrigin.x,slashOrigin.y,21);
    for(const t of slashTargets)actor(t.x,t.y,t.r,clocks.slash.hit&&A.fanHit(slashOrigin,0,235,Math.PI*.72,t));
    if(bounds){ctx.strokeStyle='#b9d4d055';ctx.beginPath();ctx.moveTo(slashOrigin.x,slashOrigin.y);ctx.arc(slashOrigin.x,slashOrigin.y,235,-Math.PI*.36,Math.PI*.36);ctx.closePath();ctx.stroke();}
    const points=slashSamples[low?'low':'high'].points;
    if(time<.42){ctx.globalAlpha=.2;ctx.strokeStyle='#d9f8ff';ctx.lineWidth=1;ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.stroke();ctx.globalAlpha=1;}
    if(time>=.24&&time<.9){const head=A.clamp((time-.24)/.42);polygon(A.ribbon(points,12,head,.32),'#8bdde5');polygon(A.ribbon(points,3,head,.30),'#f4ffff');}
    if(time>=.42&&time<.7){const age=time-.42;ctx.globalAlpha=1-age/.28;ctx.strokeStyle='#d9fbff';ctx.lineWidth=2;
      for(let i=0;i<12;i++){const a=i*Math.PI/6,r=12+age*140;ctx.beginPath();ctx.moveTo(545+Math.cos(a)*r,270+Math.sin(a)*r);ctx.lineTo(545+Math.cos(a)*(r+13),270+Math.sin(a)*(r+13));ctx.stroke();}ctx.globalAlpha=1;}
    text(stage(.42,.9),26,H-30);text('同一接觸事件，只結算一次',W-245,H-30,'#93c2cc',13);
  }
  function updateInfo(){const [heading,items]=descriptions[demo];document.getElementById('title').textContent=heading;document.getElementById('details').innerHTML=items.map(([a,b])=>`<dt>${a}</dt><dd>${b}</dd>`).join('');}
  function reset(){time=0;for(const c of Object.values(clocks))c.reset();hitLog=[];}
  function draw(){const begin=performance.now(),low=document.getElementById('quality').value==='low',bounds=document.getElementById('bounds').checked;
    const dpr=+document.getElementById('density').value;if(canvas.width!==W*dpr){canvas.width=W*dpr;canvas.height=H*dpr;}
    ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,canvas.width,canvas.height);ctx.setTransform(dpr,0,0,dpr,0,0);
    if(document.getElementById('camera').checked)ctx.translate(Math.sin(time*1.8)*24,Math.cos(time*1.3)*12);
    ({beam:drawBeam,sky:drawSky,slash:drawSlash}[demo])(low,bounds);drawTimes.push(performance.now()-begin);if(drawTimes.length>180)drawTimes.shift();
    timeInput.value=Math.round(time*100);status.textContent=`t ${time.toFixed(2)}s　接觸事件 ${clocks[demo].events}　${low?'手機降階':'桌機品質'}　最近繪製平均 ${(drawTimes.reduce((a,b)=>a+b,0)/(drawTimes.length||1)).toFixed(2)}ms`;
  }
  function advance(dt){for(const [name,c] of Object.entries(clocks))if(c.advance(dt,playing))hitLog.push({name,time:c.age});}
  function frame(now){const dt=Math.min(.05,(now-last)/1000);last=now;if(playing){time+=dt;advance(dt);if(time>3.2)reset();}draw();frames++;requestAnimationFrame(frame);}
  document.querySelectorAll('[data-demo]').forEach(button=>button.onclick=()=>{demo=button.dataset.demo;document.querySelectorAll('[data-demo]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));reset();updateInfo();});
  document.getElementById('play').onclick=()=>{playing=!playing;document.getElementById('play').textContent=playing?'暫停':'播放';};
  timeInput.oninput=()=>{playing=false;document.getElementById('play').textContent='播放';time=+timeInput.value/100;for(const c of Object.values(clocks)){c.reset();c.advance(time,true);}draw();};
  window.VFXDemo={get state(){return {demo,time,playing,frames,hitLog:hitLog.slice(),events:clocks[demo].events,lastStats};},seek(t){timeInput.value=t*100;timeInput.oninput();},setDemo(name){document.querySelector(`[data-demo="${name}"]`).click();},draw};
  updateInfo();requestAnimationFrame(frame);
})();
