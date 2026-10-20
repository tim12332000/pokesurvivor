/* Red one-tail cloak, referenced to the official Valley of the End frames. */
(() => {
  'use strict';
  const G=window.G,TAU=Math.PI*2,cache=new WeakMap();
  const snap=value=>Math.round(value/2)*2;
  function silhouette(owner,age){
    let frame=cache.get(owner.anim);
    const stamp=[age,owner.anim.cur,owner.anim.frame,owner.anim.dir,G.AnimationLab?.enabled].join(':');
    if(frame?.stamp===stamp)return frame;
    if(!frame){
      const mask=document.createElement('canvas'),tint=document.createElement('canvas');
      mask.width=tint.width=192;mask.height=tint.height=192;
      frame={mask,tint};cache.set(owner.anim,frame);
    }
    const ctx=frame.mask.getContext('2d',{willReadFrequently:true});
    ctx.clearRect(0,0,192,192);
    owner.anim.draw(ctx,96,152,{flash:true});
    const pixels=ctx.getImageData(0,0,192,192).data;
    let top=152,left=96,right=96;
    for(let y=0;y<192;y++)for(let x=0;x<192;x++){
      if(pixels[(y*192+x)*4+3]<100)continue;
      top=Math.min(top,y);left=Math.min(left,x);right=Math.max(right,x);
    }
    Object.assign(frame,{stamp,top:top-152,left:left-96,right:right-96});
    const tint=frame.tint.getContext('2d');
    tint.clearRect(0,0,192,192);tint.drawImage(frame.mask,0,0);
    tint.globalCompositeOperation='source-in';tint.fillStyle='#ff511f';tint.fillRect(0,0,192,192);
    tint.globalCompositeOperation='source-over';
    return frame;
  }
  function polygon(ctx,points,color){
    ctx.fillStyle=color;ctx.beginPath();
    points.forEach(([x,y],i)=>i?ctx.lineTo(snap(x),snap(y)):ctx.moveTo(snap(x),snap(y)));
    ctx.closePath();ctx.fill();
  }
  function tail(ctx,age,direction){
    const angles=[Math.PI/2,Math.PI/4,0,-Math.PI/4,-Math.PI/2,-Math.PI*3/4,Math.PI,Math.PI*3/4];
    const angle=angles[direction]??0,back=-Math.cos(angle);
    const side=Math.abs(back)<.25?(direction===4?1:-1):Math.sign(back);
    const points=[];
    for(let i=0;i<=26;i++){
      const t=i/26;
      // One continuous tail: a thick lower-back root, an arched rise, a fine tip.
      const x=side*(5+47*t+Math.sin(t*Math.PI)*9)+Math.sin(age*3.5+t*4)*5*t;
      const y=-17-53*t+Math.sin(t*Math.PI)*16-Math.sin(angle)*8*t;
      points.push([x,y]);
    }
    for(const [color,factor] of [['#9e252b',1],['#f24a29',.76],['#ff8c49',.28]]){
      ctx.fillStyle=color;
      for(let i=0;i<points.length;i++){
        const t=i/(points.length-1),width=Math.max(2,snap((17*(1-t)+2)*factor));
        ctx.fillRect(snap(points[i][0]-width/2),snap(points[i][1]-width/2),width,width);
      }
    }
  }
  function pulse(ctx,radius,flash){
    if(!(flash>0))return;
    ctx.save();ctx.globalAlpha*=Math.min(.55,flash*4);
    const advance=1-Math.min(1,flash/.18),r=Math.max(12,Math.min(500,radius));
    ctx.fillStyle='#ff8155';
    for(let i=0;i<40;i++){const a=i*TAU/40;ctx.fillRect(snap(Math.cos(a)*r*(.8+advance*.2)),snap(Math.sin(a)*r*(.8+advance*.2)),4,2);}
    ctx.restore();
  }
  function draw(ctx,f,ground){
    const owner=f.owner;
    if(!owner?.anim||owner.dead||!(owner.hp>0)||!Number.isFinite(owner.x)||!Number.isFinite(owner.y))return;
    const age=Math.max(0,f.age||0),scale=Math.min(1.4,Math.max(.65,owner.anim.scale??1));
    const fade=Math.max(0,Math.min(1,age/.2,(f.ttl-age)/.3));
    if(!fade)return;
    const frame=silhouette(owner,age),direction=owner.anim.dir??0;
    ctx.save();ctx.translate(owner.x,owner.y);ctx.imageSmoothingEnabled=false;ctx.globalAlpha*=fade;
    if(ground){
      ctx.save();ctx.scale(scale,scale);ctx.globalAlpha*=.68;tail(ctx,age,direction);ctx.restore();
      // A dilated silhouette follows the actual knees, hands, head and casting pose.
      ctx.save();ctx.globalAlpha*=.20;
      for(const [dx,dy] of [[-3,0],[3,0],[0,-3],[0,2],[-2,-2],[2,-2]])ctx.drawImage(frame.tint,-96+dx*scale,-152+dy*scale);
      ctx.restore();
      ctx.save();ctx.globalAlpha*=.7;ctx.scale(scale,scale);
      const top=frame.top/scale;
      polygon(ctx,[[-13,top+16],[-13,top-5],[-7,top+3],[-3,top+12]],'#ec4d2b');
      polygon(ctx,[[5,top+12],[9,top-4],[15,top+5],[14,top+18]],'#f15a2d');
      ctx.restore();
    }else{
      // Thin translucent chakra sheath, with the outfit still visible underneath.
      ctx.save();ctx.globalAlpha*=.22+Math.sin(age*9)*.035;
      ctx.drawImage(frame.tint,-96,-152);ctx.restore();
      ctx.save();ctx.scale(scale,scale);
      // Deterministic boiling motes cling to the silhouette instead of a fixed coat.
      const top=frame.top/scale,left=frame.left/scale,right=frame.right/scale;
      for(let i=0;i<18;i++){
        const life=(age*.8+i*.173)%1,side=i%2?-1:1;
        const edge=side<0?left:right;
        const x=edge+side*(2+Math.sin(i*2.7+age*4)*2),y=-5-life*Math.max(12,-top-4);
        ctx.save();ctx.globalAlpha*=(1-life)*.55;ctx.fillStyle=i%3?'#fb5a31':'#ffad6b';
        const size=i%4?2:4;ctx.fillRect(snap(x),snap(y),size,size);ctx.restore();
      }
      // The existing counter pulse briefly stretches a single chakra claw forward.
      if(f.pulseFlash>0){
        const t=1-Math.min(1,f.pulseFlash/.18),angle=owner.aim||0;
        ctx.save();ctx.translate(0,-28);ctx.rotate(angle);ctx.globalAlpha*=Math.sin(t*Math.PI)*.55;
        polygon(ctx,[[7,-5],[22+t*25,-7],[31+t*25,-4],[24+t*25,-1],[34+t*25,1],[23+t*25,3],[29+t*25,6],[18+t*25,7],[7,4]],'#ff633d');
        ctx.restore();
      }
      pulse(ctx,(f.m?.radius||76)/scale,f.pulseFlash);ctx.restore();
    }
    ctx.restore();
  }
  G.NarutoCloakVFX={draw};
})();
