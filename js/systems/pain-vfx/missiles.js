(function(G){
  'use strict';
  const TAU=Math.PI*2;
  const clamp=n=>Math.max(0,Math.min(1,n));
  function polygon(ctx,points,fill,stroke){
    ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.closePath();
    ctx.fillStyle=fill;ctx.fill();if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=1;ctx.stroke();}
  }
  function shot(ctx,p){
    if(p.kind!=='missile')return false;
    const age=Math.max(0,p.age||0),lift=Math.max(0,p.lift||0),rising=p.phase==='rise';
    const trail=Math.min(38,(rising?lift:(p.distance||0))*.6),pulse=1+Math.sin(age*61)*.15;
    const aim=p.angle||0;
    // Rise is vertical in screen space; seeking pitches slightly down as altitude is spent.
    const angle=rising?-Math.PI/2:Math.atan2(Math.sin(aim)+.3*clamp(lift/90),Math.cos(aim));
    const launchOffset=rising?48:12+36*clamp(lift/90);
    ctx.save();ctx.translate(p.x,p.y-launchOffset-lift);ctx.rotate(angle);
    // A short current-heading wake avoids inventing a historical flight path.
    for(let i=3;i>=1;i--){
      const d=trail*i/3;if(d<5)continue;
      ctx.globalAlpha=.22*(1-i/5);ctx.fillStyle='#b5aaa0';
      ctx.beginPath();ctx.arc(-11-d,Math.sin(age*17+i)*2,2+i,0,TAU);ctx.fill();
    }
    ctx.globalAlpha=1;
    polygon(ctx,[[-9,-2],[-9,2],[-22*pulse,0]],'#cb6c35');
    polygon(ctx,[[-9,-1],[-9,1],[-17*pulse,0]],'#ffe0a0');
    polygon(ctx,[[-8,-3],[-4,-7],[0,-7],[0,-2]],'#68727d','#202732');
    polygon(ctx,[[-8,3],[-4,7],[0,7],[0,2]],'#68727d','#202732');
    polygon(ctx,[[-10,-3],[5,-3],[11,0],[5,3],[-10,3]],'#a7adb2','#232a35');
    ctx.fillStyle='#e2e0d6';ctx.fillRect(-7,-2,10,1);
    ctx.fillStyle='#59616b';ctx.fillRect(-5,-2,2,5);ctx.fillRect(2,-2,1,5);
    ctx.fillStyle='#373b44';ctx.fillRect(-12,-2,3,4);
    ctx.restore();return true;
  }
  function launcher(ctx,x,y,angle,open,flash){
    ctx.save();ctx.translate(x,y-48);ctx.rotate(angle);
    for(let i=-1;i<=1;i++){
      const y=i*(2+open*2);
      polygon(ctx,[[-9,y-2],[7,y-2],[9,y],[7,y+2],[-9,y+2]],'#737983','#242936');
      ctx.fillStyle='#c3c4bc';ctx.fillRect(-7,y-1,12,1);
      ctx.fillStyle='#252a33';ctx.fillRect(6,y-1,3,2);
    }
    if(flash>0){
      ctx.globalAlpha=flash;polygon(ctx,[[8,-3],[16,-5],[13,-1],[21,0],[13,2],[16,5],[8,3]],'#ffca79');
    }
    ctx.restore();
  }
  function action(ctx,f){
    if(f.kind!=='missiles'||!f.body)return false;
    const age=Math.max(0,f.age||0);
    const interval=Math.max(.001,f.interval||.08),since=age-.12-Math.max(0,(f.emitted||0)-1)*interval;
    launcher(ctx,f.body.x,f.body.y,-Math.PI/2,clamp(age/.12),f.emitted?clamp(1-since/.06):0);
    return true;
  }
  function effect(ctx,e){
    if(e.kind==='missile-launch'){
      launcher(ctx,e.x,e.y,e.angle??-Math.PI/2,1,clamp(1-(e.age||0)/.08));return true;
    }
    if(e.kind!=='explosion')return false;
    const t=clamp((e.age||0)/(e.life||.25)),radius=48,fade=1-t;
    ctx.save();ctx.translate(e.x,e.y);ctx.globalAlpha=fade;
    // Damage resolves immediately: the first frame already fills the native blast footprint.
    const edge=radius*(1-.1*t);
    for(let i=0;i<8;i++){
      const a=i*TAU/8,r=edge*(.55+(i%3)*.13);
      ctx.fillStyle=i%2?'#c77c42':'#916c55';
      ctx.beginPath();ctx.arc(Math.cos(a)*r*.55,Math.sin(a)*r*.55-5*t,edge*.38,0,TAU);ctx.fill();
    }
    ctx.globalAlpha=fade*fade;
    polygon(ctx,Array.from({length:16},(_,i)=>{
      const a=i*TAU/16,r=radius*(i%2?.35:.82)*(1-t*.65);return [Math.cos(a)*r,Math.sin(a)*r];
    }),'#f4bb69');
    ctx.fillStyle='#fff0bd';ctx.beginPath();ctx.arc(0,0,14*fade,0,TAU);ctx.fill();
    ctx.globalAlpha=fade;ctx.strokeStyle='#f4d4a0';ctx.lineWidth=2;
    ctx.beginPath();ctx.arc(0,0,radius,0,TAU);ctx.stroke();
    for(let i=0;i<7;i++){
      const a=i*2.39996,d=radius*(.28+.65*t),x=Math.cos(a)*d,y=Math.sin(a)*d-12*Math.sin(t*Math.PI);
      ctx.fillStyle=i%2?'#514b46':'#807566';ctx.fillRect(Math.round(x),Math.round(y),3+(i%2),2+(i%3));
    }
    ctx.restore();return true;
  }
  (G.PainSkillVFX ||= {}).missiles={shot,action,effect};
})(G);
