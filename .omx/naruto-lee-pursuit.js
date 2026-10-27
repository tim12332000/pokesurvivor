/* Learned high-speed taijutsu: a native, slotless attack between selected techniques. */
(() => {
  if(G.NarutoPursuit)return;
  const id='naruto-lee-pursuit',states=new Map();
  const config=Object.freeze({maxHits:12,rushSpeed:900,rushDuration:.2,guardDuration:.06,minimumCooldown:.5});
  const controlled=owner=>G.SelfClones?.isControlled(owner)??owner===G.Game.player;
  const alive=actor=>actor&&!actor.dead&&actor.hp>0;
  const boss=actor=>!!(actor.boss||actor.legend||actor.judge);
  const hitRange=(move,target)=>move.radius+(target.r||0);
  const contactRange=(owner,move,target)=>Math.max(move.radius*.65,(owner.r||12)+(target.r||10)+8);
  const learned=owner=>owner?.mon?.dex===30006&&owner.moves?.find(move=>move.id===id);
  const heavy=owner=>G.NarutoLee?.activeFor(owner)||G.DigimonSkills?.whirlwindFor(owner);
  const moving=owner=>owner===G.Game.player&&Math.hypot(...G.Input.axis())>.2;
  function clear(owner){if(owner)states.delete(owner);else states.clear();}
  function activeFor(owner){const state=states.get(owner);return state?.world===G.World&&alive(owner)&&controlled(owner)&&learned(owner)?state.active:null;}
  function path(ax,ay,bx,by){
    const count=Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/4));
    for(let i=1;i<=count;i++){
      const x=ax+(bx-ax)*i/count,y=ay+(by-ay)*i/count;
      if(G.World.isWall(x,y)||G.World.projectileBlock(x,y,1))return false;
    }
    return true;
  }
  function targetFor(owner,move){
    const range=moving(owner)?move.radius:move.range;
    const targets=[...new Set(G.EnemyMgr.queryCircle(owner.x,owner.y,range))]
      .filter(enemy=>alive(enemy)&&Math.hypot(enemy.x-owner.x,enemy.y-owner.y)<=range+(boss(enemy)?enemy.r||0:0)&&path(owner.x,owner.y,enemy.x,enemy.y));
    targets.sort((a,b)=>Number(boss(b))-Number(boss(a))||Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y));
    return targets[0];
  }
  function migrate(owner){
    const move=learned(owner);if(!move)return;
    move.passive=true;if(owner.bind)delete owner.bind[id];
    if(!owner.slots.some(group=>group.includes(move)))return;
    const selected=owner.activeGroup();
    owner.slots=owner.slots.map(group=>group.filter(m=>m!==move)).filter(group=>group.length);
    const index=owner.slots.findIndex(group=>group.some(m=>selected.includes(m)));owner.active=index>=0?index:0;
  }
  const addMove=G.Player.prototype.addMove;
  G.Player.prototype.addMove=function(moveId,...args){
    if(moveId!==id||this.mon?.dex!==30006)return addMove.call(this,moveId,...args);
    if(this.hasMove(id)){migrate(this);return false;}
    this.moves.push(G.Moves.instance(id,1));migrate(this);return true;
  };
  const arrange=G.Player.prototype.arrange;
  G.Player.prototype.arrange=function(...args){const result=arrange.apply(this,args);migrate(this);return result;};
  function beginAttack(active){
    const owner=active.owner;active.phase='attack';active.attackAge=0;
    owner.aim=active.aim;owner.cast(active.move);
  }
  function start(owner,move,target){
    const snapshot=G.Quantity?.snapshot(owner,move)||{...move};
    snapshot.dmg*=G.NarutoSupport?.takeAttackBonus(owner)||1;
    move.t=Math.max(config.minimumCooldown,move.cd*owner.cdMul);
    const active={owner,move:snapshot,target,phase:'rush',age:0,attackAge:0,hitIndex:0,
      hits:Math.min(config.maxHits,Math.max(1,snapshot.count|0)),aim:Math.atan2(target.y-owner.y,target.x-owner.x),
      duration:Math.min(.42,Math.max(.16,move.t*.65)),camera:{x:G.Camera.x,y:G.Camera.y}};
    if(moving(owner)||Math.hypot(target.x-owner.x,target.y-owner.y)<=contactRange(owner,move,target))beginAttack(active);
    return active;
  }
  function advance(active,dt){
    const owner=active.owner,move=active.move;let target=active.target;active.age+=dt;
    if(!alive(target)){
      target=targetFor(owner,{...move,range:active.phase==='attack'?move.radius:move.range});
      if(!target)return false;
      active.target=target;
    }
    if(!path(owner.x,owner.y,target.x,target.y))return false;
    if(active.phase==='attack'&&moving(owner)&&Math.hypot(target.x-owner.x,target.y-owner.y)>hitRange(move,target))return false;
    active.aim=Math.atan2(target.y-owner.y,target.x-owner.x);
    if(owner.anim)owner.anim.dir=G.Sprites.dirFromAngle(active.aim);
    if(active.phase==='rush'){
      const distance=Math.hypot(target.x-owner.x,target.y-owner.y);
      if(moving(owner)){
        if(distance>hitRange(move,target))return false;
        beginAttack(active);
      }else{
        let budget=Math.min(config.rushSpeed*dt,Math.max(0,distance-contactRange(owner,move,target)));
        const steps=Math.ceil(budget/4)+1;
        for(let i=0;i<steps&&budget>.001;i++){
          const step=Math.min(4,budget),x=owner.x+Math.cos(active.aim)*step,y=owner.y+Math.sin(active.aim)*step;
          if(!G.World.isFree(x,y,owner.r||12,true)||!path(owner.x,owner.y,x,y))return false;
          owner.x=x;owner.y=y;budget-=step;
        }
        owner.invuln=Math.max(owner.invuln||0,config.guardDuration);
        if(Math.hypot(target.x-owner.x,target.y-owner.y)<=contactRange(owner,move,target)+.01)beginAttack(active);
        else if(active.age>=config.rushDuration)return false;
      }
    }
    if(!alive(owner))return false;
    if(active.phase==='attack'){
      if(boss(target)&&!moving(owner)){
        let budget=Math.min(config.rushSpeed*dt,Math.max(0,Math.hypot(target.x-owner.x,target.y-owner.y)-contactRange(owner,move,target)));
        const steps=Math.ceil(budget/4)+1;
        for(let i=0;i<steps&&budget>.001;i++){
          const distance=Math.hypot(target.x-owner.x,target.y-owner.y);if(distance<.001)break;
          const step=Math.min(4,budget),x=owner.x+(target.x-owner.x)/distance*step,y=owner.y+(target.y-owner.y)/distance*step;
          if(!G.World.isFree(x,y,owner.r||12,true)||!path(owner.x,owner.y,x,y))return false;
          owner.x=x;owner.y=y;budget-=step;
        }
        if(Math.hypot(target.x-owner.x,target.y-owner.y)>hitRange(move,target))return active.age<active.duration+.6;
      }
      active.attackAge=Math.min(active.duration,active.attackAge+dt);
      while(active.hitIndex<active.hits&&active.attackAge+1e-9>=active.duration*(active.hitIndex+.5)/active.hits){
        const last=active.hitIndex===active.hits-1;
        G.DigimonSkills.meleeStrike(owner,{...move,knock:last?55:8},active.aim);
        active.hitIndex++;
      }
      if(active.attackAge>=active.duration)return false;
    }
    owner.aim=active.aim;owner.attackFace=Math.max(owner.attackFace||0,.08);
    return true;
  }
  function update(dt){
    const owners=[G.Game.player,...(G.SelfClones?.actors()||[])].filter(Boolean);
    for(const [owner,state]of states)if(!owners.includes(owner)||!alive(owner)||!learned(owner)||state.world!==G.World)clear(owner);
    for(const owner of owners){
      const move=learned(owner);if(!move||!alive(owner)||!controlled(owner))continue;
      migrate(owner);let state=states.get(owner);
      if(!state){state={world:G.World,active:null};states.set(owner,state);}
      if(G.Game.state!=='playing'||!(dt>0)||!Number.isFinite(dt))continue;
      move.t=Math.max(0,move.t-dt);
      if(heavy(owner)){state.active=null;continue;}
      if(state.active){if(!advance(state.active,dt))state.active=null;continue;}
      if(move.t<=0){const target=targetFor(owner,move);if(target)state.active=start(owner,move,target);else move.t=.08;}
    }
  }
  const C=G.Combat,updateFields=C.updateFields,clearFields=C.clearFields;
  C.updateFields=function(dt){const result=updateFields.call(this,dt);update(dt);return result;};
  C.clearFields=function(owner){const result=clearFields.call(this,owner);clear(owner);return result;};
  if(G.DigimonSkills?.clear){const previous=G.DigimonSkills.clear;G.DigimonSkills.clear=function(owner){const result=previous.call(this,owner);clear(owner);return result;};}
  G.NarutoPursuit={config,activeFor,clear,migrate,update};
})();
