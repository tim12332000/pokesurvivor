/* Native direct hits and non-recursive outer splash share a contact boundary. */
(() => {
  'use strict';
  if(G.CombatPulse)return;
  let epoch=0,serial=0,nextOwner=0;
  const ownerIds=new WeakMap(),telemetry=[];
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const controlled=a=>G.SelfClones?.isControlled?.(a)??(G.Game.everyone().includes(a)||!!G.SelfClones?.isActor?.(a));
  const legal=cast=>!!cast&&cast.runEpoch===epoch&&cast.world===G.World&&alive(cast.owner)&&!cast.owner.frozen&&controlled(cast.owner)&&G.Game.state==='playing';
  function beginRun(){epoch++;serial=0;telemetry.length=0;return epoch;}
  function create(owner,moveId,meta={}){
    if(!ownerIds.has(owner))ownerIds.set(owner,++nextOwner);
    return {...meta,owner,moveId,world:G.World,runEpoch:epoch,ownerId:ownerIds.get(owner),castId:++serial,pulses:new Set()};
  }
  function clearPath(x,y,tx,ty){
    const length=Math.hypot(tx-x,ty-y),steps=Math.max(1,Math.ceil(length/4));
    for(let i=0;i<=steps;i++){
      const px=x+(tx-x)*i/steps,py=y+(ty-y)*i/steps;
      if(G.World.isWall(px,py)||G.World.projectileBlock?.(px,py,1))return false;
    }
    return true;
  }
  function apply(cast,contactPulseIndex,hits){
    if(!legal(cast)||!Number.isInteger(contactPulseIndex)||contactPulseIndex<0||cast.pulses.has(contactPulseIndex))return false;
    cast.pulses.add(contactPulseIndex);
    const primary=new Map();
    for(const hit of hits){
      if(!alive(hit.target)||hit.target.friendly||cast.targetIsLegal&&!cast.targetIsLegal(hit.target)||!Number.isFinite(hit.primaryDirectDamage)||hit.primaryDirectDamage<=0)continue;
      const previous=primary.get(hit.target);
      if(!previous||previous.primaryDirectDamage<hit.primaryDirectDamage)primary.set(hit.target,{...hit,x:hit.target.x,y:hit.target.y});
    }
    const owner=cast.owner,rate=G.DamageSplash.rate(owner),radius=G.DamageSplash.radius,outer=new Map();
    if(rate>0)for(const hit of primary.values())for(const target of new Set(G.EnemyMgr.queryCircle(hit.x,hit.y,radius))){
      if(primary.has(target)||!alive(target)||target.friendly||cast.targetIsLegal&&!cast.targetIsLegal(target)||Math.hypot(target.x-hit.x,target.y-hit.y)>radius||!clearPath(hit.x,hit.y,target.x,target.y))continue;
      const amount=hit.primaryDirectDamage*rate,previous=outer.get(target);
      if(cast.targetIsLegal){const entry=previous||{sources:[]};entry.sources.push({amount,color:hit.color||'#fff',source:hit.target});outer.set(target,entry);}
      else if(!previous||previous.amount<amount)outer.set(target,{amount,color:hit.color||'#fff'});
    }
    const landed=new Set();
    let primaryHits=0,primaryDamage=0,secondaryHits=0,secondaryDamage=0;
    for(const hit of primary.values()){
      if(!legal(cast))break;
      if(!alive(hit.target)||cast.targetIsLegal&&!cast.targetIsLegal(hit.target))continue;
      const amount=hit.primaryDirectDamage;
      hit.target.hurt(amount,hit.color||'#fff',hit.dx||0,hit.dy||0,hit.knock||0,hit.eff??null,owner,cast.moveId);
      landed.add(hit.target);owner.onDealt?.(amount);owner.dmgDealt=(owner.dmgDealt||0)+amount;primaryHits++;primaryDamage+=amount;
      hit.onHit?.(hit.target);
    }
    if(legal(cast))G.DamageSplash.withSecondary(()=>{
      for(const [target,entry] of outer){
        if(!legal(cast))break;
        if(!alive(target)||cast.targetIsLegal&&!cast.targetIsLegal(target))continue;
        // Guarded casts cannot emit splash from a skipped stale primary.
        const hit=entry.sources?entry.sources.filter(source=>landed.has(source.source)).sort((a,b)=>b.amount-a.amount)[0]:entry;
        if(!hit)continue;
        target.hurt(hit.amount,hit.color,0,0,0,null,owner,cast.moveId);
        owner.dmgDealt=(owner.dmgDealt||0)+hit.amount;secondaryHits++;secondaryDamage+=hit.amount;
      }
    });
    const info={runEpoch:epoch,ownerId:cast.ownerId,castId:cast.castId,moveId:cast.moveId,channel:cast.channel||'body',contactPulseIndex,primaryHits,primaryDamage,secondaryHits,secondaryDamage};
    if(telemetry.length>=96)telemetry.shift();telemetry.push(info);
    api.onPulse?.({...info,owner,cast});
    return info;
  }
  const api={beginRun,create,apply,legal,get epoch(){return epoch;},get telemetry(){return telemetry;},onPulse:null};
  G.CombatPulse=api;
})();
