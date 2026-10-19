/* Growing fireballs are moving flame areas, never impact-consumed bombs. */
(() => {
  if(G.NarutoFireballAOE)return;
  const active=new Set(),config=Object.freeze({tick:.2});
  function track(p,move,owner) {
    p.fireballAOE={owner,world:G.World,move:{...move},tick:move.fireballTick||config.tick,
      enemies:new Map(),props:new Map(),lastTime:0,lastX:p.x,lastY:p.y,lastRadius:p.r,
      damage:p.dmg,critChance:owner.critChance,blocked:false,blockedProp:null};
    p.digiBomb=null;active.add(p);return p;
  }
  function clear(owner) {
    for(const p of [...active])if(!owner||p.fireballAOE.owner===owner){G.Projectiles.remove(p);active.delete(p);}
  }
  function lineClear(x,y,e) {
    const dx=e.x-x,dy=e.y-y,d=Math.hypot(dx,dy);
    for(let n=4;n<d;n+=4)if(G.World.isWall(x+dx*n/d,y+dy*n/d))return false;
    return true;
  }
  function contact(p,e) {
    const f=p.fireballAOE,dx=p.x-f.lastX,dy=p.y-f.lastY,len2=dx*dx+dy*dy;
    const t=len2?Math.max(0,Math.min(1,((e.x-f.lastX)*dx+(e.y-f.lastY)*dy)/len2)):1;
    const x=f.lastX+dx*t,y=f.lastY+dy*t,r=f.lastRadius+(p.r-f.lastRadius)*t;
    return G.U.dist2(x,y,e.x,e.y)<=(r+(e.r||0))**2&&lineClear(x,y,e);
  }
  function countHits(p,e,registry,expired) {
    const f=p.fireballAOE,time=Math.min(p.t,p.life-1e-7);
    let seen=registry.get(e);
    if(!seen){if(expired)return 0;registry.set(e,{next:time+f.tick,lastSeen:time});return 1;}
    if(expired&&seen.lastSeen<f.lastTime-1e-7)return 0;
    // Re-entering an area never catches up damage for time spent outside it.
    if(seen.lastSeen<f.lastTime-1e-7)seen.next=Math.max(seen.next,time);
    seen.lastSeen=time;
    const hits=Math.max(0,Math.floor((time-seen.next+1e-8)/f.tick)+1);
    if(hits)seen.next+=hits*f.tick;
    return hits;
  }
  function pulse(p,expired) {
    const f=p.fireballAOE,pl=f.owner,m=f.move,base=f.damage*f.tick;
    const half=Math.hypot(p.x-f.lastX,p.y-f.lastY)/2;
    for(const e of new Set(G.EnemyMgr.queryCircle((p.x+f.lastX)/2,(p.y+f.lastY)/2,half+Math.max(p.r,f.lastRadius)))) {
      if(e.dead||!contact(p,e))continue;
      const hits=countHits(p,e,f.enemies,expired);if(!hits)continue;
      const k=G.Types.mult(m.type,e.types)*G.Weather.mult(m.type);
      if(k<=0)continue;
      for(let i=0;i<hits&&!e.dead;i++){
        const crit=f.critChance>0&&Math.random()<f.critChance,damage=base*k*(crit?1.5:1)*(G.NarutoSupport?.precisionMultiplier(pl,e)||1);
        if(damage<=0)continue;
        e.hurt(damage,p.color,e.x-p.x,e.y-p.y,m.knock||0,crit?'crit':G.Types.label(G.Types.mult(m.type,e.types)),pl);
        pl.dmgDealt+=damage;pl.onDealt(damage);if(m.burn)e.applyBurn(m.burn);
      }
    }
    const props=new Set(G.World.propsInCircle(p.x,p.y,p.r));
    if(f.blockedProp)props.add(f.blockedProp);
    for(const prop of props)if(!prop.dead&&G.U.dist2(p.x,p.y,prop.x,prop.y)<=(p.r+(prop.r||0)+4)**2&&lineClear(p.x,p.y,prop)){
      const hits=countHits(p,prop,f.props,expired);for(let i=0;i<hits;i++)G.World.damageProp(prop,base,p.color);
    }
  }
  function resolve() {
    const live=new Set(G.Projectiles.all());
    for(const p of [...active]) {
      const f=p.fireballAOE;
      if(f.owner!==G.Game.player||f.world!==G.World||f.owner.dead||f.owner.hp<=0||(!live.has(p)&&p.t<p.life)) {
        G.Projectiles.remove(p);active.delete(p);continue;
      }
      pulse(p,p.t>=p.life);
      f.lastTime=Math.min(p.t,p.life-1e-7);f.lastX=p.x;f.lastY=p.y;f.lastRadius=p.r;
      if(p.t>=p.life){G.Projectiles.remove(p);active.delete(p);}
    }
  }
  const C=G.Combat,oldResolve=C.resolve,oldClear=C.clearFields,oldSkillClear=G.DigimonSkills.clear;
  C.resolve=function(dt,pl,now){oldResolve.call(this,dt,pl,now);resolve();};
  C.clearFields=function(owner){oldClear.call(this,owner);clear(owner);};
  G.DigimonSkills.clear=function(owner){oldSkillClear(owner);clear(owner);};
  G.NarutoFireballAOE={config,track,resolve,clear,get active(){return [...active];}};
})();
