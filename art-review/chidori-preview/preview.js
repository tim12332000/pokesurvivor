/* Standalone presentation study. Does not load or mutate the game. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const ctx = $('stage').getContext('2d');
  const sheet = new Image(), original = new Image(), oldSheet = new Image(), fullCharge = new Image();
  let frames, old, playing = true, time = 0, last = 0;
  const duration = 1.8;
  const smooth = t => t*t*(3-2*t);
  const phase = t => t < .2 ? '結印' : t < .5 ? '沉身・左手聚電' : t < 1 ? '蓄勢・黃色放電' : t < 1.17 ? '突進' : t < 1.27 ? '命中' : t < 1.45 ? '返回' : '收勢';
  function pose(t) {
    if (t < .08) return 1;
    if (t < .16) return 3;
    if (t < .25) return 4;
    if (t < .94) return 5;
    if (t < 1) return 7;
    if (t < 1.08) return 10;
    return 11;
  }
  function actor(c, index, x, y, scale = 1, alpha = 1, mirror = false) {
    if (time < 1) {
      const frame = Math.floor(Math.max(0,time)*12)%4, k=64/390*scale;
      c.save();c.translate(x,y);c.scale(mirror?-k:k,k);c.globalAlpha=alpha;c.imageSmoothingEnabled=false;
      c.drawImage(fullCharge,frame*543,0,543,724,-240,-610,543,724);c.restore();return;
    }
    const f = frames[index], k = 64/320*scale;
    c.save();c.translate(x,y);c.scale(mirror?-k:k,k);c.globalAlpha=alpha;c.imageSmoothingEnabled=false;
    c.drawImage(sheet,...f.rect,-f.anchor[0],-f.anchor[1],f.rect[2],f.rect[3]);c.restore();
  }
  function recovery(c, x, y, scale, mirror) {
    const f=old.frames[3],k=64/old.bodyHeight*scale;
    c.save();c.translate(x,y);c.scale(mirror?-k:k,k);c.imageSmoothingEnabled=false;
    c.drawImage(oldSheet,...f.rect,-f.anchor[0],-f.anchor[1],f.rect[2],f.rect[3]);c.restore();
  }
  function draw(t) {
    const scale=+$('zoom').value, mirror=$('mirror').checked, sign=mirror?-1:1;
    ctx.fillStyle='#101b2b';ctx.fillRect(0,0,960,440);
    ctx.strokeStyle='#1d2b40';ctx.lineWidth=1;
    for(let x=0;x<960;x+=48){ctx.beginPath();ctx.moveTo(x,70);ctx.lineTo(x,390);ctx.stroke();}
    for(let y=102;y<=390;y+=48){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(960,y);ctx.stroke();}
    ctx.fillStyle='#17263b';ctx.fillRect(0,320,960,3);
    ctx.fillStyle='#9eacc0';ctx.font='13px system-ui';ctx.fillText('蓄力前置 1.000 秒',28,34);
    ctx.fillStyle='#efcd79';ctx.fillText(phase(t),28,58);
    const start=mirror?650:310, end=start+sign*170, y=320;
    let x=start;
    if(t>=1&&t<1.17)x=start+sign*170*((t-1)/.17);
    else if(t>=1.17&&t<1.27)x=end;
    else if(t>=1.27&&t<1.45)x=end-sign*170*smooth((t-1.27)/.18);
    const f=pose(t);
    ctx.fillStyle='#192f47';ctx.beginPath();ctx.ellipse(x,y+3,24*scale,4*scale,0,0,Math.PI*2);ctx.fill();
    ctx.save();ctx.strokeStyle='#77849a';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(end+sign*40,y);ctx.lineTo(end+sign*40,y-65);ctx.moveTo(end+sign*20,y-50);ctx.lineTo(end+sign*60,y-50);ctx.stroke();ctx.restore();
    if(t>=1&&t<1.27)for(let i=3;i>0;i--)actor(ctx,f,x-sign*i*15,y,scale,.08*(4-i),mirror);
    if(t<1.45)actor(ctx,f,x,y,scale,1,mirror);else recovery(ctx,x,y,scale,mirror);
    // The charge's complete energy effect is authored into its four sprites.
    if(t>=1.17&&t<1.27) {
      const a=1-(t-1.17)/.1;ctx.save();ctx.strokeStyle='#fff1ac';ctx.globalAlpha=a;ctx.lineWidth=2;
      for(let i=0;i<8;i++){const r=i*Math.PI/4;ctx.beginPath();ctx.moveTo(end+sign*40+Math.cos(r)*6,y-45+Math.sin(r)*6);ctx.lineTo(end+sign*40+Math.cos(r)*22,y-45+Math.sin(r)*22);ctx.stroke();}ctx.restore();
    }
    ctx.fillStyle='#91a7c3';ctx.font='12px system-ui';ctx.fillText('1 秒內保持原地蓄力',28,405);
    ctx.fillStyle='#edc66a';ctx.fillRect(28,420,904*Math.min(t,1),3);
    $('clock').textContent=t.toFixed(3)+' s';$('phase').textContent=phase(t);$('seek').value=Math.round(t*1000);
  }
  function pause(){playing=false;$('play').textContent='播放';}
  $('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'暫停':'播放';};
  $('replay').onclick=()=>{time=0;playing=true;$('play').textContent='暫停';draw(time);};
  $('step').onclick=()=>{pause();time=Math.min(duration,Math.round((time+.1)*10)/10);draw(time);};
  $('seek').oninput=()=>{pause();time=+$('seek').value/1000;draw(time);};
  $('zoom').onchange=$('mirror').onchange=()=>draw(time);
  function tick(now){if(last&&playing)time=(time+Math.min(.05,(now-last)/1000)*+$('speed').value)%(duration+.7);last=now;draw(Math.min(time,duration));requestAnimationFrame(tick);}
  async function load() {
    const [meta,legacy]=await Promise.all([fetch('frames.json').then(r=>r.json()),fetch('../animation-assets.json').then(r=>r.json())]);
    frames=meta.frames;old=legacy['sasuke-chidori'];
    sheet.src='sasuke-chidori-charge-v1.png';original.src='../references/sasuke-original.png';oldSheet.src='../redrawn/sasuke-skills-v2.png';
    fullCharge.src='sasuke-chidori-full-v3.png';
    await Promise.all([sheet.decode(),original.decode(),oldSheet.decode(),fullCharge.decode()]);
    const ref=$('reference').getContext('2d');ref.imageSmoothingEnabled=false;ref.fillStyle='#ffff99';ref.fillRect(0,0,480,190);
    [[93,371,30,45,15,45],[132,372,78,70,26,44],[218,371,80,65,39,45]].forEach(([sx,sy,w,h,ax,ay],i)=>ref.drawImage(original,sx,sy,w,h,70+i*153-ax*2,123-ay*2,w*2,h*2));
    const strip=$('strip').getContext('2d');strip.fillStyle='#101b2b';strip.fillRect(0,0,480,190);
    strip.drawImage(fullCharge,0,0,2172,724,0,15,480,160);
    window.ChidoriPreview={seek(t){pause();time=t;draw(t);},get time(){return time;},frames,chargeSeconds:1};
    draw(0);requestAnimationFrame(tick);
  }
  load().catch(e=>{$('error').textContent='素材讀取失敗：'+e.message;console.error(e);});
})();
