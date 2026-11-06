/* Rasengan accents follow the orb painted into each authored pose. Render only. */
(() => {
  'use strict';
  if(G.NarutoRasenganVFX)return;
  const TAU=Math.PI*2,PX=G.Sprites.PX;
  // Centers/radii measured in naruto-skills-v2.png's cropped frame coordinates.
  // Recheck against the atlas when replacing naruto-rasengan's authored poses.
  const orbPoints=[[62,148,12],[114,132,24],[274,115,31]];
  const colors=['#1767aa','#35bfff','#9feaff','#ffffff'];
  const snap=n=>Math.round(n/PX)*PX;
  function dot(ctx,x,y,color,size=PX){ctx.fillStyle=color;ctx.fillRect(snap(x),snap(y),size,size)}
  function line(ctx,x,y,tx,ty,color){
    const n=Math.max(1,Math.ceil(Math.hypot(tx-x,ty-y)/PX));
    for(let i=0;i<=n;i++)dot(ctx,x+(tx-x)*i/n,y+(ty-y)*i/n,color);
  }
  function arc(ctx,x,y,r,a,length,color,flat=.65){
    const n=Math.max(2,Math.ceil(r*length/PX));
    for(let i=0;i<=n;i++){const t=a+length*i/n;dot(ctx,x+Math.cos(t)*r,y+Math.sin(t)*r*flat,color)}
  }
  function ribbon(ctx,path,color,opacity,steps=26,thickness=1){
    ctx.save();let previous=path(0);
    for(let i=1;i<=steps;i++){
      const u=i/steps,p=path(u);ctx.globalAlpha=opacity*(1-u)**.65;
      line(ctx,previous.x,previous.y,p.x,p.y,color);
      if(thickness>1&&u<.65){
        const dx=p.x-previous.x,dy=p.y-previous.y,len=Math.hypot(dx,dy)||1;
        line(ctx,previous.x-dy/len*PX,previous.y+dx/len*PX,p.x-dy/len*PX,p.y+dx/len*PX,color);
      }
      previous=p;
    }
    ctx.restore();
  }
  function point(anim,pose,x,y){
    if(pose?.key!=='naruto-rasengan'||!orbPoints[pose.frame])return null;
    const asset=window.AnimationAssets?.get(pose.key),frame=asset?.frames[pose.frame];
    if(!frame)return null;
    const [ox,oy,r]=orbPoints[pose.frame],scale=64/asset.bodyHeight*(anim.scale||1);
    const side=!!pose.mirror!==!!frame.mirror?-1:1;
    return {x:x+(ox-frame.anchor[0])*scale*side,y:y+(oy-frame.anchor[1])*scale,r:r*scale,scale:anim.scale||1};
  }
  function hand(owner){const pose=G.AnimationLab?.stateFor(owner.anim);return point(owner.anim,pose,owner.x,owner.y)}
  G.VFX.SHAPES['naruto-rasengan-flow']={w:19,h:19,frames:12,gen(P,f){
    for(let i=0;i<3;i++){
      const a=f*TAU/12+i*TAU/3,r=3+i*2;
      P.arc(9,9,r,a,a+Math.PI*1.3,i===1?'m':'w');
      P.arc(9,9,r-1,a+.2,a+1,'l');
    }
  }};
  G.VFX.SHAPES['naruto-rasengan-contact']={w:35,h:29,frames:5,gen(P,f){
    for(let i=0;i<5;i++){
      const a=i*TAU/5+f*.4,r=5+f*2;
      P.arc(17,14,r,a,a+.8,i%2?'w':'l');
      P.line(17+Math.cos(a)*r,14+Math.sin(a)*r*.8,17+Math.cos(a)*(r+4),14+Math.sin(a)*(r+4)*.8,'m');
    }
  }};
  G.VFX.SHAPES['naruto-rasengan-pressure']={w:33,h:33,frames:12,gen(P,f){
    for(let i=0;i<4;i++){
      const a=f*TAU/12+i*TAU/4,r=10+i%2*3;
      P.arc(16,16,r,a,a+1.3,'l');
      P.arc(16,16,r-1,a+.15,a+1.25,'w');
      P.arc(16,16,r-2,a+.4,a+1,'w');
      const t=a+1.3;P.line(16+Math.cos(t)*r,16+Math.sin(t)*r,16+Math.cos(t+.2)*(r+2),16+Math.sin(t+.2)*(r+2),'m');
    }
  }};
  function drawOrb(ctx,anim,pose,x,y,opts={}){
    const p=point(anim,pose,x,y);if(!p||opts.flash)return;
    // Open filaments animate the existing ball; no second opaque sphere is drawn.
    G.VFX.draw(ctx,'naruto-rasengan-flow','naruto-blue',p.x,p.y,
      {frame:Math.floor((pose.age||0)*24),scale:p.r/18,alpha:(opts.alpha??1)*.9});
    const q=pose.phase==='charge'?Math.min(1,(pose.age||0)/.6):1;
    G.VFX.draw(ctx,'naruto-rasengan-pressure','naruto-blue',p.x,p.y,
      {frame:Math.floor((pose.age||0)*24),scale:(p.r+(7+q*17)*p.scale)/28,alpha:(opts.alpha??1)*(.45+q*.55)});
  }
  function drawAir(ctx,f){
    const p=hand(f.owner);if(!p)return;
    ctx.save();
    if(f.phase==='charge'){
      const q=Math.min(1,f.phaseAge/Math.max(.01,f.m.charge)),age=f.phaseAge;
      for(let i=0;i<9;i++){
        const a=i*TAU/9+age*8,r=(20+26*(1-q)+(i%2)*5)*p.scale;
        ribbon(ctx,u=>{const angle=a-u*1.5,rr=r+u*16*p.scale;return {x:p.x+Math.cos(angle)*rr,y:p.y+Math.sin(angle)*rr*.65-u*u*10*p.scale}},colors[2+i%2],.45+q*.45,20,i%3===0?2:1);
      }
      arc(ctx,p.x,p.y,p.r+5*p.scale,age*11,1.1,colors[2]);
    }else if(f.phase==='strike'){
      const q=Math.min(1,f.phaseAge/.16),dx=Math.cos(f.aim),dy=Math.sin(f.aim);
      ctx.globalAlpha=.8;
      for(let i=0;i<3;i++)arc(ctx,p.x+dx*Math.sin(q*Math.PI)*6,p.y+dy*Math.sin(q*Math.PI)*6,p.r+6+i*4,f.t*18+i*1.8,1.6,colors[i===0?3:2],.8);
    }else if(f.phase==='dash'){
      const dx=Math.cos(f.aim),dy=Math.sin(f.aim);
      for(let i=-2;i<=2;i++){
        ribbon(ctx,u=>{
          const back=(7+u*(125-Math.abs(i)*12))*p.scale;
          const side=(i*(5+u*15)+Math.sin(f.t*19+u*5+i*1.7)*u*16)*p.scale;
          return {x:p.x-dx*back-dy*side,y:p.y-dy*back+dx*side-u*u*24*p.scale};
        },colors[i===0?3:2],i===0?.95:.65,38,i===0?2:1);
      }
      ctx.globalAlpha=.8;arc(ctx,p.x,p.y,p.r+8*p.scale,f.phaseAge*21,1.5,colors[3]);
    }
    ctx.restore();
  }
  function drawGround(ctx,f){
    if(f.phase!=='impact')return;
    const q=Math.min(1,f.phaseAge/.28),r=f.m.radius*.75*(1-(1-q)**3);
    ctx.save();ctx.globalAlpha=(1-q)*.65;
    for(let i=0;i<3;i++)arc(ctx,f.x,f.y,r,i*TAU/3+q*1.2,.85,colors[2],.6);
    for(let i=0;i<5;i++){
      const a=i*2.399+f.aim+q*.4,rr=12+q*(18+i%3*8);
      const x=f.x+Math.cos(a)*rr,y=f.y+Math.sin(a)*rr*.6-Math.sin(q*Math.PI)*12;
      dot(ctx,x,y,'#b7ba83',PX);
    }
    ctx.restore();
  }
  function drawImpact(ctx,f){
    if(f.phase!=='impact')return;
    const q=Math.min(1,f.phaseAge/.28),expand=1-(1-q)**3,dx=Math.cos(f.aim),dy=Math.sin(f.aim);
    const x=f.x+dx*22,y=f.y-30+dy*12;
    ctx.save();ctx.globalAlpha=1-q;
    // Brief compression retains contact weight; its energy unravels into open curls.
    if(q<.3){
      for(let i=0;i<5;i++)arc(ctx,x,y,6+i*3+expand*10,i*.9+q*5,3.6,colors[i%2?3:2],.85);
    }
    for(let i=0;i<6;i++){
      ribbon(ctx,u=>{
        const angle=f.aim-1.5+i*TAU/6+q*3.4+u*2.6;
        const r=Math.min(f.m.radius*.52,12+expand*(25+i*4)+u*(16+expand*16));
        return {x:x+dx*expand*12+Math.cos(angle)*r,y:y+dy*expand*12+Math.sin(angle)*r*.75-u*u*(24+q*18)-Math.sin(q*Math.PI)*8};
      },colors[i%2?2:3],(1-q)*(i===0?.95:.8),40,i%2===0?2:1);
    }
    ctx.restore();
  }
  G.NarutoRasenganVFX={drawOrb,drawAir,drawGround,drawImpact,point};
})();
