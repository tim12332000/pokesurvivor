/* Procedural air edges. Every visible cut follows a live simulation event. */
(() => {
  'use strict';
  const TAU=Math.PI*2,WHITE='#f2ffff',CYAN='#a5e7ed';
  const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
  const lift=()=>G.LIFT||0;
  const visible=(a,r=80)=>a&&!a.dead&&Number.isFinite(a.x)&&Number.isFinite(a.y)&&(!G.Camera?.sees||G.Camera.sees(a.x,a.y,r));
  // Coincident quantity copies share presentation, never simulation state.
  function sample(list,radius=80,limit=80) {
    const result=[],seen=new Set();
    for(const a of list||[]) {
      if(!visible(a,typeof radius==='function'?radius(a):radius))continue;
      const key=[Math.round(a.x/9),Math.round(a.y/9),Math.round((a.aim||0)*18),a.phase||'',Math.floor((a.age||0)*20)].join(':');
      if(seen.has(key))continue;seen.add(key);result.push(a);if(result.length>=limit)break;
    }
    return result;
  }
  function fieldGroups(list,sizeKey,limit=24) {
    const owners=new Map(),groups=[];
    for(const a of list||[]) {
      const r=a.cast?.[sizeKey]||240;if(!visible(a,r))continue;
      const owner=a.owner||a.cast?.owner||null;
      let buckets=owners.get(owner);if(!buckets)owners.set(owner,buckets=new Map());
      const key=[Math.round(a.x/18),Math.round(a.y/18),Math.round(r/24),a.cast?.kind||'',Math.round((a.cast?.arc||0)*100)].join(':');
      let group=buckets.get(key);
      if(!group) {
        if(groups.length>=limit)continue;
        group=[];buckets.set(key,group);groups.push(group);
      }
      group.push(a);
    }
    return groups;
  }
  // A narrow tapered filled ribbon, with a short, clean leading edge.
  function edge(ctx,r,head,span,width,alpha=1,color=WHITE) {
    if(r<=0||alpha<=0)return;
    const n=Math.min(192,Math.max(20,Math.ceil(span*r/10))),w=Math.min(7,Math.max(.5,width));
    ctx.save();ctx.globalAlpha*=clamp(alpha);ctx.fillStyle=color;ctx.beginPath();
    for(let side=1;side>=-1;side-=2)for(let j=0;j<=n;j++) {
      const t=side===1?j/n:1-j/n,a=head-span+span*t;
      const taper=Math.pow(Math.sin(Math.PI*t),.8),rr=r+side*w*taper*.5;
      const x=Math.cos(a)*rr,y=Math.sin(a)*rr;
      if(side===1&&j===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);
    }
    ctx.closePath();ctx.fill();ctx.restore();
  }
  function streak(ctx,length,width,alpha=1) {
    ctx.save();ctx.globalAlpha*=clamp(alpha);ctx.fillStyle=WHITE;
    ctx.beginPath();ctx.moveTo(length*.2,0);
    ctx.quadraticCurveTo(-length*.25,-width,-length,0);
    ctx.quadraticCurveTo(-length*.23,width,length*.2,0);ctx.fill();
    ctx.restore();
  }
  function local(ctx,a,draw) {
    ctx.save();ctx.translate(a.x,a.y-lift());draw();ctx.restore();
  }
  function drawGround(ctx,{summons=[]}={}) {
    for(const a of sample(summons,100,32)) {
      const fade=a.phase==='fade'?clamp(1-(a.age-a.fadeAt)/.22):1;
      ctx.save();ctx.globalAlpha*=fade*.13;ctx.fillStyle='#17343a';ctx.beginPath();
      ctx.ellipse(a.x,a.y,15,4,0,0,TAU);ctx.fill();ctx.restore();
    }
  }
  function drawAir(ctx,{storms=[],orbits=[],waves=[],summons=[],states=[]}={}) {
    for(const group of fieldGroups(waves,'range',24)) {
      const a=group[0];local(ctx,a,()=>{
      const b=a.cast||{},fronts=[];
      for(const wave of group)for(const front of wave.fronts||[])if(!front.done&&front.reach>2)fronts.push({wave,front});
      fronts.sort((a,b)=>b.front.reach-a.front.reach);
      // A shared presentation budget covers coincident quantity copies and recuts.
      const selected=[];
      for(const f of fronts)if(selected.every(p=>Math.abs(p.front.reach-f.front.reach)>Math.max(34,(b.range||240)*.2))) {
        selected.push(f);if(selected.length===3)break;
      }
      for(let i=0;i<selected.length;i++) {
        const {wave,front}=selected[i],r=front.reach,arc=wave.cast?.arc||1.2;
        const fade=clamp(((wave.cast?.range||240)-r)/35)*clamp(r/18);
        edge(ctx,r,(wave.aim||0)+arc/2,arc,Math.min(5,r*.035),fade*(i? .24:.92),i?CYAN:WHITE);
      }
      });
    }
    for(const a of sample(summons,110,40)) {
      const fade=a.phase==='fade'?clamp(1-(a.age-a.fadeAt)/.22):1;
      // A local animation object prevents drawing from altering actors.
      G.TemariArt?.drawSummon?.(ctx,{...a,anim:{...a.anim}},{x:a.x,y:a.y-lift(),height:40,
        state:a.phase==='slash'?'slash':a.moving?'move':'idle',time:a.age,age:a.age,
        phase:a.phase,aim:a.aim,facing:Math.cos(a.aim)<0?-1:1,dir:a.dir,alpha:fade});
      if(a.moving)local(ctx,a,()=>{ctx.rotate(a.aim||0);ctx.translate(-16,7);streak(ctx,18,1,fade*.3);});
      const dt=a.age-a.lastCut;
      if(a.phase==='slash'&&dt>=0&&dt<.085)local(ctx,a,()=>{
        const r=a.cast?.radius||40,aim=(a.aim||0)+(a.cuts%2?-.4:.4);
        edge(ctx,r,aim+.9+dt*5,1.8,Math.min(4,r*.045),fade*(1-dt/.085));
      });
    }
    for(const s of states||[]) {
      const p=s.pose,o=s.owner;if(!p?.empowered||!visible(o))continue;
      const t=(p.age-.2)/.14;if(t<0||t>=1)continue;
      local(ctx,o,()=>{const r=25+t*38;edge(ctx,r,(p.aim||0)+.6,1.2,2.5,Math.sin(t*Math.PI)*.8);});
    }
    for(const group of fieldGroups(storms,'radius',24)) {
      const a=group.find(s=>(s.age||0)<=(s.sweepDuration||1.2));if(!a)continue;
      const age=a.age||0,duration=a.sweepDuration||1.2;if(age>duration)continue;
      const r=a.cast?.radius||240,head=a.angle??((a.aim||0)+TAU*age/duration);
      const fade=clamp(age/.05)*clamp((duration-age)/.12);
      local(ctx,a,()=>{
        edge(ctx,r,head,.88,Math.min(7,r*.035),fade*.95);
        edge(ctx,r*.91,head-.13,.58,2.2,fade*.32,CYAN);
        edge(ctx,r*.72,head-.22,.38,1.4,fade*.2,CYAN);
      });
    }
    let count=0;
    for(const o of orbits||[]) {
      const e=o.enemy;if(!visible(e,60)||e.hp<=0||count++>=24)continue;
      const r=Math.hypot(e.x-o.x,e.y-o.y);if(r<10)continue;
      // Captives travel counterclockwise, so their wake ends behind the real position.
      const angle=Math.atan2(e.y-o.y,e.x-o.x),fade=clamp(((o.duration||1.2)-(o.age||0))/.14);
      ctx.save();ctx.translate(o.x,o.y-lift());
      edge(ctx,r,angle+.27,.27,2,fade*.48,CYAN);ctx.restore();
    }
  }
  function drawReflection(ctx,{walls=[],projectiles=[],flashes=[]}={}) {
    const seenOwners=new Set();
    for(const w of walls||[]) {
      const o=w.owner||w;if(!visible(o,w.radius||100)||seenOwners.has(o))continue;seenOwners.add(o);
      const t=w.age||0,r=w.radius||100,fade=clamp(t*8)*(w.permanent?1:clamp(((w.duration||3)-t)*6));
      local(ctx,o,()=>{
        // Sparse fragments breathe in place, preserving a clear view of the actor.
        for(let i=0;i<3;i++) {
          const head=(w.aim||0)+i*TAU/3+Math.sin(t*2+i)*.09;
          edge(ctx,r,head,.31,1.4,fade*(.26+.1*Math.sin(t*3+i)),CYAN);
        }
      });
    }
    for(const p of sample(projectiles.filter(p=>p.temariReflected),70,48))local(ctx,p,()=>{
      ctx.rotate(Math.atan2(p.vy||0,p.vx||0));streak(ctx,29,2,.88);
    });
    for(const f of sample(flashes,80,24)) {
      const t=(f.age||0)/.16;if(t>=1)continue;
      local(ctx,f,()=>{
        ctx.rotate(f.angle||0);streak(ctx,12+t*18,2.5,(1-t)*.9);
        edge(ctx,8+t*15,.8,1.6,1.7,(1-t)*.8);
      });
    }
  }
  G.TemariCycloneVFX={drawAir,drawGround,drawReflection};
})();
