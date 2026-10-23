"""Native browser fixtures for Tenten's recovery and physical tag combos.

Executed on desktop and touch layouts by test_tenten.py.
"""
COMBOS = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,out={};
 const fuma=p.moves.find(m=>m.id==='naruto-tenten-fuma'),tags=p.moves.find(m=>m.id==='naruto-tenten-tags');
 const counts=[fuma.count,tags.count];
 function recover(){A.reset();p.target=A.spawn(150,0);A.castNative(fuma.id);A.finish(1.6);
   A.assert(T.stateFor(p)?.chargeRemaining>0,'successful hit/return gave no charge');}
 try {
   // Quantity never creates a stack or repeated rewards from one volley.
   fuma.count=20;recover();const first=T.stateFor(p).chargeRemaining;
   A.assert(first<=6,'recovery charge exceeds lifetime');
   const clock=T.stateFor(p).chargeRemaining;G.Combat.updateFields(1);
   A.near(T.stateFor(p).chargeRemaining,clock,'pause consumed charge');
   A.castNative('naruto-tenten');A.assert(T.stateFor(p).chargeRemaining>0,'passive stole charge');
   const m=A.castNative('naruto-tenten-twin'),pose=T.activeFor(p);
   A.assert(pose.power===1.3&&T.stateFor(p).chargeRemaining===0,'active failed to consume exactly one charge');
   A.finish(.75);A.assert(pose.emitted===pose.count,'fourth empowered batch was not emitted');
   A.assert(T.weapons.filter(w=>w.mode==='tenten-twin').every(w=>Math.abs(w.damage-m.dmg*p.atk*1.3)<1e-8),'later batches lost snapshotted power');
   out.recovery={quantity:20,power:pose.power,passivePreserved:true,pauseFrozen:true};
   fuma.count=1;recover();A.finish(6.1);A.assert(T.stateFor(p).chargeRemaining===0,'charge did not expire');
   A.castNative('naruto-tenten-twin');A.assert(T.activeFor(p).power===1,'expired charge buffed attack');
   A.reset();const miss=A.spawn(150,0);p.target=miss;A.castNative(fuma.id);miss.dead=true;G.EnemyMgr.rebuildGrid();A.finish(2);
   A.assert(T.stateFor(p).chargeRemaining===0,'miss earned charge');
   A.reset();p.target=A.spawn(150,0);A.castNative(fuma.id);
   for(let i=0;i<100&&!T.weapons.some(w=>w.back);i++)A.advance();
   A.assert(T.weapons.some(w=>w.back),'return-wall fixture never turned');
   const block=G.World.projectileBlock;G.World.projectileBlock=(x,y)=>x>40&&x<60?{destructible:false}:false;
   try{A.finish(2);A.assert(T.stateFor(p).chargeRemaining===0,'blocked return earned charge')}finally{G.World.projectileBlock=block}
   out.blockedReturn=true;
   for(const reason of ['clear','death','world']) {
     recover();const world=G.World;
     if(reason==='clear')G.Combat.clearFields(p);
     if(reason==='death')p.dead=true;
     if(reason==='world')G.World={...world};
     try{A.advance();A.assert(!T.stateFor(p),'charge leaked '+reason)}finally{G.World=world;p.dead=false}
   }
   // A physical crossing triggers only the owning actor's planted paper tag.
   tags.count=1;
   for(const mode of ['naruto-tenten','naruto-tenten-fuma','naruto-tenten-twin']) {
     A.reset();p.target=A.spawn(100,0);A.castNative(tags.id);
     for(let i=0;i<100&&!T.weapons.some(w=>w.landed);i++)A.advance();
     const tag=T.weapons.find(w=>w.landed);A.assert(tag,'tag did not plant');
     p.target.dead=true;G.EnemyMgr.rebuildGrid();
     A.finish(.1);
     const radius=tag.m.blastRadius||tag.m.radius;
     const es=[A.spawn(tag.x,tag.y+radius*.8),A.spawn(tag.x,tag.y-radius*.8),A.spawn(tag.x+radius*.8,tag.y),A.spawn(tag.x,tag.y+radius+40)];
     const hits=es.map(()=>[]);es.forEach((e,i)=>{const hurt=e.hurt;e.hurt=function(...args){if(args[7]===tags.id)hits[i].push(args[0]);return hurt.apply(this,args)}});
     p.target=A.spawn(mode==='naruto-tenten-fuma'?tag.x:160,mode==='naruto-tenten-twin'?60:tag.y);A.castNative(mode);
     for(let i=0;i<40&&!tag.dead;i++)A.advance();
     A.assert(tag.dead&&tag.landedAge<.65&&T.stateFor(p).comboBlasts===1,'physical tool did not trigger early '+mode+' '+JSON.stringify({tag:[tag.x,tag.y,tag.landedAge,tag.dead],combo:T.stateFor(p).comboBlasts,shots:T.weapons.map(w=>[w.x,w.y,w.mode])}));
     A.assert(hits.map(h=>h.length).join(',')==='1,1,1,0','combo AOE missing/duplicate/outside '+mode+' '+JSON.stringify(hits));
     const expected=tags.dmg*p.atk*1.25*G.Types.mult(tags.type,es[0].types)*G.Weather.mult(tags.type);
     A.near(hits[0][0],expected,'combo damage multiplier');A.finish(1);
     A.assert(hits.map(h=>h.length).join(',')==='1,1,1,0','combo repeated after normal fuse');
     out[mode]={hits:hits.map(h=>h.length),power:1.25,early:true};
   }
   // No target means no cast and no lost charge. Siblings cannot spend it.
   recover();G.EnemyMgr.clear();p.target=null;
   A.assert(!T.cast(p,p.moves.find(m=>m.id==='naruto-tenten-twin'))&&T.stateFor(p).chargeRemaining>0,'failed cast consumed charge');
   const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');card.apply(p);
   const clone=G.SelfClones.actors()[0];clone.x=clone.y=0;clone.target=A.spawn(150,0);
   const before=T.stateFor(p).chargeRemaining;
   A.assert(T.cast(clone,clone.moves.find(m=>m.id===fuma.id)),'clone native cast failed');A.finish(2);
   A.assert(T.stateFor(clone)?.chargeRemaining>0,'clone did not earn independent charge');
   A.near(T.stateFor(p).chargeRemaining,before-2,'clone refreshed/spent player charge');
   T.clear(clone);A.assert(T.stateFor(p).chargeRemaining>0,'clone cleanup cleared player charge');
   out.cloneCharge=true;
   A.reset();p.target=A.spawn(100,0);A.castNative(tags.id);
   for(let i=0;i<100&&!T.weapons.some(w=>w.landed);i++)A.advance();
   const ownTag=T.weapons.find(w=>w.landed);A.finish(.1);card.apply(p);
   const sibling=G.SelfClones.actors()[0];sibling.x=sibling.y=0;sibling.target=A.spawn(ownTag.x,ownTag.y);
   A.assert(T.cast(sibling,sibling.moves.find(m=>m.id==='naruto-tenten')),'clone crossing cast failed');A.finish(.3);
   A.assert(!ownTag.dead&&T.stateFor(p).comboBlasts===0,'clone triggered player tag');out.ownedTags=true;
   recover();
   A.select('naruto-tenten-twin');
   const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d'),labels=[],fill=ctx.fillText.bind(ctx);
   ctx.fillText=(label,...args)=>{labels.push(String(label));return fill(label,...args)};
   G.HUD.draw(ctx,innerWidth,innerHeight,p,{time:20});
   A.assert(labels.filter(label=>label.startsWith('蓄勢 +30%')).length===3,'active charge HUD missing or displayed on passives');
   return out;
 } finally {fuma.count=counts[0];tags.count=counts[1]}
}"""
