/* Six Paths are one family of five support bodies, independent from card clones. */
(() => {
  if (G.NarutoPain) return;
  const C=G.Combat, TAU=Math.PI*2, paths=['asura','animal','human','preta','naraka'];
  const required={missiles:'asura',summon:'animal',soul:'human'};
  const visualHeights=Object.freeze({tendo:80,asura:84,animal:70,human:82,preta:74,naraka:78});
  const visualHeight=(path,owner)=>visualHeights[path]*(owner?.anim?.scale||1);
  const smoothStep=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
  const accelerate=t=>{t=Math.max(0,Math.min(1,t));return t*t;};
  const survivalConfig=Object.freeze({hpFraction:Object.freeze({asura:2,animal:2,human:2,preta:2,naraka:2}),protectionSeconds:1.5,retreatBelow:.35,resumeAbove:.5,safeRecoveryDelay:3,safeRecoveryRate:.04});
  const ready=b=>alive(b)&&b.formed&&b.protectionRemaining<=0;
  const shots=[], effects=[], batches=[], timers=new Map(); let family=null, sequence=0;
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const controlled=a=>a===G.Game.player||!!G.SelfClones?.isActor(a);
  const valid=a=>alive(a)&&controlled(a)&&a.mon?.dex===30010;
  const currentFamily=owner=>!!family&&family.owner===owner&&owner===G.Game.player&&owner.mon?.dex===30010&&family.world===G.World;
  const speedMultiplier=owner=>currentFamily(owner)&&alive(owner)&&family.playerSpeedRemaining>0?2:1;
  function canRevivePlayer(owner=G.Game.player) {
    return currentFamily(owner)&&G.Game.state!=='ui'&&G.Game.state!=='over'&&owner.dead&&family.bodies.some(b=>b.path==='naraka'&&alive(b)&&b.formed);
  }
  const familyActive=owner=>valid(owner)||(currentFamily(owner)&&canRevivePlayer(owner));
  const frameActive=f=>valid(f.owner)||(familyActive(f.owner)&&!!(f.body||required[f.kind]||f.support));
  function playerReviveState(owner=G.Game.player) {
    if(!currentFamily(owner))return {waiting:false,status:'idle',remaining:0,protection:0};
    const r=family.playerRevive,waiting=canRevivePlayer(owner);
    return {waiting,status:waiting?(r?.status||'waiting'):family.playerProtection>0?'protected':'idle',remaining:waiting?Math.max(0,(r?.period??10*(owner.cdMul||1))-(r?.wait||0)) + Math.max(0,.8-(r?.age||0)):0,protection:family.playerProtection||0};
  }
  const root=a=>a?.sourceOwner||a;
  const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
  const special=e=>e.boss||e.elite||e.legend||e.judge;
  const grounded=e=>!e.flying&&!(e.jumpLift>0)&&!(e.jumpT>0);
  const kind=m=>m?.id==='naruto-pain'?'basic':(m?.id||m?.digiMode||'').replace(/^naruto-pain-/, '').replace(/^pain-/, '');
  const supports=mode=>['basic','gravity','missiles','summon','soul','absorb','repair','planet'].includes(kind({id:mode}));
  const learned=(a,k)=>a?.moves?.find(m=>kind(m)===k);
  const selected=(a,m)=>!!a?.moves?.some(v=>v.id===m.id);
  const lane=f=>required[f.kind]||f.owner;
  const busy=f=>family.actions.some(a=>lane(a)===lane(f));
  function drawSkill(name,method,ctx,value) {
    const draw=G.PainSkillVFX?.[name]?.[method];if(!draw)return false;
    draw(ctx,value,family);return true;
  }
  function visualEffect(f,kind,life,extra={}) {
    if(effects.length<160)effects.push({...f,...extra,kind,age:0,life,visualOnly:true});
  }
  function finish(f){const i=family.actions.indexOf(f);if(i>=0)family.actions.splice(i,1);}
  function planetTarget(targets,radius=640) {
    return targets.find(special)||targets.find(e=>targets.filter(t=>!special(t)&&dist(e,t)<=radius&&clearPath(e.x,e.y,t.x,t.y)).length>=3);
  }
  const rank=m=>Math.max(0,Math.min(4,(m?.lvl||1)-1));
  function clearPath(ax,ay,bx,by,target=null) {
    return G.World.projectilePathClear(ax,ay,bx,by,target);
  }
  function nearby(a,r) {
    return [...new Set(G.EnemyMgr.queryCircle(a.x,a.y,r))].filter(e=>alive(e)&&dist(a,e)<=r&&clearPath(a.x,a.y,e.x,e.y)).sort((a1,b)=>dist(a,a1)-dist(a,b));
  }
  function soulLanding(b,e,owner) {
    if(dist(e,owner)>300||hazardous(e.x,e.y,b.r))return null;
    const angle=Math.atan2(b.y-e.y,b.x-e.x);
    for(let i=0;i<16;i++) {
      const a=angle+i*TAU/16,x=e.x+Math.cos(a)*30,y=e.y+Math.sin(a)*30;
      if(G.World.isFree(x,y,b.r,true)&&!hazardous(x,y,b.r)&&clearPath(b.x,b.y,x,y)&&clearPath(x,y,e.x,e.y))return {x,y};
    }
    return null;
  }
  function move(a,dx,dy) {
    const n=Math.max(1,Math.ceil(Math.hypot(dx,dy)/3));
    for(let i=0;i<n;i++) {
      if(G.World.isFree(a.x+dx/n,a.y,a.r||8,true))a.x+=dx/n;
      if(G.World.isFree(a.x,a.y+dy/n,a.r||8,true))a.y+=dy/n;
    }
  }
  function toward(a,b,length) {
    const d=dist(a,b);if(d>1e-8)move(a,(b.x-a.x)/d*Math.min(d,length),(b.y-a.y)/d*Math.min(d,length));
  }
  function hazardous(x,y,r) {
    return (G.Hazards.all||[]).some(h=>!h.hit&&G.Hazards.inside(h,x,y,r+12));
  }
  function hazardCost(x,y,r) {
    let cost=0;
    for(const h of G.Hazards.all||[])if(!h.hit&&G.Hazards.inside(h,x,y,r+12)) {
      const dx=x-h.x,dy=y-h.y;
      const depth=h.kind==='zone'?h.r+(r+12)*.6-Math.hypot(dx,dy):
        Math.min(h.w/2+(r+12)*.6-Math.abs(-dx*Math.sin(h.angle)+dy*Math.cos(h.angle)),
          dx*Math.cos(h.angle)+dy*Math.sin(h.angle)+r+12,h.len+r+12-dx*Math.cos(h.angle)-dy*Math.sin(h.angle));
      cost+=600+Math.max(0,depth)*10;
    }
    return cost;
  }
  function safePoint(a,owner,x,y,enemies) {
    return G.World.isFree(x,y,a.r,true)&&clearPath(owner.x,owner.y,x,y)&&!hazardous(x,y,a.r)&&
      !enemies.some(e=>alive(e)&&Math.hypot(e.x-x,e.y-y)<a.r+(e.r||8)+36)&&
      ![owner,...(G.SelfClones?.actors()||[]),...(family?.bodies||[])].some(b=>b!==a&&alive(b)&&b.formed!==false&&Math.hypot(b.x-x,b.y-y)<a.r+(b.r||10)+16);
  }
  function place(a,owner,index=0) {
    const enemies=[...new Set(G.EnemyMgr.queryCircle(owner.x,owner.y,280))];
    for(let ring=0;ring<8;ring++)for(let i=0;i<16;i++) {
      const angle=(i+index*3)*TAU/16,r=48+ring*16,x=owner.x+Math.cos(angle)*r,y=owner.y+Math.sin(angle)*r;
      if(safePoint(a,owner,x,y,enemies)) {a.x=x;a.y=y;return true;}
    }
    return false;
  }
  class Body extends G.Player {
    constructor(owner,path,index) {
      super(owner.mon,{},owner.shiny);this.path=path;this.index=index;this.id='pain-'+path+'-'+(++sequence);this.sourceOwner=owner;this.world=G.World;
      this.hpFraction=survivalConfig.hpFraction[path];this.maxHp=this.hp=owner.maxHp*this.hpFraction;this.r=10;this.bodyH=owner.bodyH||48;this.dead=false;this.reviveRemaining=0;
      this.formed=false;this.protectionRemaining=0;this.retreating=false;this.mode='waiting';this.placementRetry=0;
      this.sinceDamage=0;this.recovering=false;
      this.cooldown=0;this.pose=null;this.poseAge=0;this.target=null;this.invuln=0;this.flash=0;this.deathSerial=0;this.moves=[];
    }
    hurt(amount,type=null,pure=false) {
      if(!family||!ready(this)||family.owner.frozen||this.invuln>0||!(amount>0))return;
      const typed=type?G.Types.mult(type,this.mon.types)*G.Weather.mult(type):1;
      const damage=pure?amount:Math.max(1,amount*typed*(1-Math.min(.8,this.sourceOwner.dmgReduce||0)));
      this.hp=Math.max(0,this.hp-damage);this.invuln=.45;this.flash=.14;this.poseAge=0;
      this.sinceDamage=0;this.recovering=false;
      G.FX.dmgText(this.x,this.y-visualHeight(this.path,this.sourceOwner)-6,'-'+Math.round(damage),'#c5abd9');
      if(this.hp<=0){this.dead=true;this.reviveRemaining=16;this.deathSerial=++sequence;this.pose='death';this.target=null;this.mode='down';}
      else this.pose='hurt';
    }
    draw(ctx) {
      if(!family||family.world!==G.World||!this.formed)return;
      const height=visualHeight(this.path,this.sourceOwner);
      ctx.save();ctx.fillStyle='#0005';ctx.beginPath();ctx.ellipse(this.x,this.y,12,5,0,0,TAU);ctx.fill();
      G.PainArt?.draw(ctx,{path:this.path,x:this.x,y:this.y,height,state:this.dead?'death':this.protectionRemaining>0?'special':this.pose||'idle',time:this.poseAge,facing:Math.cos(this.aim||0)<0?-1:1,alpha:this.dead?.45:this.protectionRemaining>0?.65:1});
      if(this.protectionRemaining>0){ctx.strokeStyle='#c8b4f1';ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(this.x,this.y,17,8,0,0,TAU);ctx.stroke();}
      ctx.fillStyle='#181624';ctx.fillRect(this.x-15,this.y-height-8,30,4);ctx.fillStyle=this.dead?'#745e80':'#ba789a';ctx.fillRect(this.x-15,this.y-height-8,30*(this.dead?1-this.reviveRemaining/16:this.hp/this.maxHp),4);ctx.restore();
    }
  }
  function ensure(owner=G.Game.player) {
    const main=root(owner);if(!familyActive(main)||main!==G.Game.player)return null;
    if(family&&(family.owner!==main||family.world!==G.World))clear();
    if(!family) {
      family={owner:main,world:G.World,bodies:[],clock:0,decision:0,queue:[],actions:[],castCounts:{},absorbCooldown:0,repairCooldown:0,repairWait:0,repair:null,playerRevive:null,playerProtection:0,playerSpeedRemaining:0,sharedRecovery:0,intercepted:0,revives:0,lastCount:0};
      for(const [i,path]of paths.entries()){const b=new Body(main,path,i);family.bodies.push(b);if(place(b,main,i))reform(b);}
    }
    return family;
  }
  function body(path){return family?.bodies.find(b=>b.path===path);}
  function snapshotMove(owner,m) {
    const snap=G.Quantity?.snapshot(owner,m)||{...m};return {...snap,dmg:m.dmg??({basic:10,gravity:70,missiles:22,summon:90,soul:140,planet:240}[kind(m)]||4)};
  }
  function hit(f,e,base=f.m.dmg,origin=f,singleTarget=false,fixedDamage=false) {
    if(!frameActive(f)||f.world!==G.World||!alive(e)||!clearPath(origin.x,origin.y,e.x,e.y))return;
    const type=f.m.type||'dark',mult=fixedDamage?1:G.Types.mult(type,e.types),crit=!fixedDamage&&Math.random()<(f.owner.critChance||0);
    const damage=fixedDamage?base:base*f.attack*mult*G.Weather.mult(type)*(crit?1.5:1);
    e.hurt(damage,'#c6addd',e.x-origin.x,e.y-origin.y,0,crit?'crit':G.Types.label(mult),f.owner,f.m.id);
    if(alive(f.owner))f.owner.onDealt?.(damage);f.owner.dmgDealt=(f.owner.dmgDealt||0)+damage;
    if(singleTarget)G.DamageSplash?.hit(f.owner,e,damage,'#c6addd',f.m.id);
  }
  function frame(owner,m,extra={}) {return {owner,world:G.World,m:snapshotMove(owner,m),attack:owner.atk,age:0,x:owner.x,y:owner.y,...extra};}
  function canCast(owner,m) {
    if((!valid(owner)&&!(familyActive(owner)&&required[kind(m)]))||owner.frozen||!supports(m?.id||m?.digiMode))return false;
    const s=ensure(owner),k=kind(m);if(!s||['absorb','repair'].includes(k))return false;
    if(k==='basic')return nearby(owner,m.range||280).length>0;
    if(!selected(owner,m)||(m.t||0)>0||s.queue.some(q=>q.owner===owner&&lane(q)===lane({owner,kind:k}))||s.actions.some(f=>f.owner===owner&&lane(f)===lane({owner,kind:k})))return false;
    if(['gravity','planet'].includes(k)&&s.sharedRecovery>0)return false;
    const b=required[k]&&body(required[k]);if(b&&(!ready(b)||(k==='soul'&&b.retreating)||hazardous(b.x,b.y,b.r)))return false;
    const targets=nearby(b||owner,k==='gravity'?(m.triggerRadius||400):m.range||({missiles:320,summon:300,soul:180,planet:640}[k])).filter(e=>k!=='soul'||!!soulLanding(b,e,owner));
    return k==='planet'?!!planetTarget(targets,m.radius||640):targets.length>0;
  }
  function basic(owner,m) {
    const targets=nearby(owner,m.range||280);if(!targets.length)return false;
    const f=frame(owner,m),base=m.quantityBaseCount??[5,5,6,7,8][rank(m)],count=Math.min(40,G.Quantity?.countAtCast(owner,f.m,base)??base);
    f.toolBounceCount=G.NinjaToolBounce?.count(owner)||0;
    family.lastCount=count;
    batches.push({...f,kind:'rod',targets,count,emitted:0,interval:Math.min(.08,.32/Math.max(1,count-1)),range:m.range||280});
    family.castCounts.basic=(family.castCounts.basic||0)+1;owner.cast?.(m);return true;
  }
  function cast(owner,m) {
    if(!canCast(owner,m))return false;
    if(kind(m)==='basic')return basic(owner,m);
    // Each shared support body has its own bounded lane; Tendo lanes belong to their owner.
    const s=family,k=kind(m),key=lane({owner,kind:k});
    if(s.queue.filter(q=>lane(q)===key).length>=1+(G.SelfClones?.actors()?.length||0))return false;
    s.queue.push(frame(owner,m,{kind:kind(m),expires:s.clock+.75}));
    const actual=owner.moves.find(v=>v.id===m.id);if(actual)actual.t=.05;
    return true;
  }
  function beginCooldown(f) {
    if(f.cooldownStarted)return;
    const actual=f.owner.moves.find(v=>v.id===f.m.id);
    if(actual){actual.t=Math.max(.05,(f.m.cd||1)*(f.owner.cdMul||1));actual.castAt=performance.now();}
    f.cooldownStarted=true;
    // Support bodies keep fighting during rescue without animating fallen Tendo.
    if(alive(f.owner))f.owner.cast?.(actual||f.m);
  }
  function cancelRequest(f) {
    if(f.cooldownStarted)return;
    const actual=f.owner.moves.find(v=>v.id===f.m.id);if(actual)actual.t=f.kind==='soul'?.4:.15;
  }
  function start(f) {
    const k=f.kind,b=required[k]&&body(required[k]);
    if(!frameActive(f)||!selected(f.owner,f.m)||(b&&(!ready(b)||(k==='soul'&&b.retreating)||hazardous(b.x,b.y,b.r)))||(['gravity','planet'].includes(k)&&family.sharedRecovery>0))return false;
    const targets=nearby(b||f.owner,k==='gravity'?(f.m.triggerRadius||400):f.m.range||({missiles:320,summon:300,soul:180,planet:640}[k])).filter(e=>k!=='soul'||!!soulLanding(b,e,f.owner));
    if(!targets.length)return false;
    f.body=b;f.target=targets[0];f.phase='prepare';f.hit=new Set();f.emitted=0;
    if(k==='gravity') {
      f.target=targets.find(special)||targets[0];
      f.immediate=false;f.phase='pull';
      f.pulls=targets.map(target=>({target,distance:0,pullDistance:Math.max(0,dist(f.owner,target)-(f.m.pullRadius??100))}));
    }
    if(k==='missiles') {
      f.targets=targets;f.baseCount=f.m.quantityBaseCount??[10,10,12,14,16][rank(f.m)];f.count=Math.min(60,G.Quantity?.countAtCast(f.owner,f.m,f.baseCount)??f.baseCount);family.lastCount=f.count;
      f.interval=Math.min(.08,.32/Math.max(1,f.count-1));f.body.pose='special';f.body.poseAge=0;
    }
    if(k==='summon'){f.angle=Math.atan2(f.target.y-b.y,f.target.x-b.x);f.x=b.x;f.y=b.y;f.distance=0;b.pose='special';b.poseAge=0;}
    if(k==='soul') {
      const landing=soulLanding(b,f.target,f.owner);if(!landing)return false;
      visualEffect(f,'soul-blink',.22,{x:b.x,y:b.y,toX:landing.x,toY:landing.y});
      b.x=landing.x;b.y=landing.y;b.aim=Math.atan2(f.target.y-b.y,f.target.x-b.x);
      f.phase='grasp';f.grasp=0;b.pose='special';b.poseAge=0;
    }
    if(k==='planet') {
      f.target=planetTarget(targets,f.m.radius||640);if(!f.target)return false;
      f.x=f.target.x;f.y=f.target.y;f.ticks=0;
      family.sharedRecovery=Math.max(family.sharedRecovery,5);
      for(const a of [family.owner,...(G.SelfClones?.actors()||[])])for(const m of a.moves||[])if(kind(m)==='gravity')m.t=Math.max(m.t||0,5);
    }
    if(b)b.castRecovery=.45;
    beginCooldown(f);
    family.actions.push(f);family.castCounts[k]=(family.castCounts[k]||0)+1;return true;
  }
  function reform(b) {
    b.formed=true;b.protectionRemaining=survivalConfig.protectionSeconds;b.invuln=survivalConfig.protectionSeconds;
    b.retreating=false;b.target=null;b.mode='reforming';b.pose='special';b.poseAge=0;
    b.sinceDamage=0;b.recovering=false;
  }
  function revive(b,serial) {
    if(!b.dead||b.deathSerial!==serial||!place(b,family.owner,b.index))return false;
    b.dead=false;b.maxHp=family.owner.maxHp*b.hpFraction;b.hp=b.maxHp;b.reviveRemaining=0;reform(b);family.revives++;
    visualEffect(frame(family.owner,learned(family.owner,'repair')||{id:'naruto-pain-repair',dmg:0},{support:true}),'repair-complete',.45,{x:b.x,y:b.y,target:b});return true;
  }
  function anchor(b,owner) {
    const facing=owner.aim||0;
    const angle=b.path==='preta'?facing: facing+Math.PI+(b.index-2)*.5;
    const radius=b.retreating?54:b.path==='preta'?48:76+b.index*8;
    return {x:owner.x+Math.cos(angle)*radius,y:owner.y+Math.sin(angle)*radius};
  }
  function follow(b,owner,dt) {
    const goal=anchor(b,owner),enemies=[...new Set(G.EnemyMgr.queryCircle(b.x,b.y,240))].filter(alive);
    // Local steering scores a fixed set of reachable steps; unsafe ground never
    // becomes a teleport target and a blocked formation retries on later ticks.
    const step=Math.max(125,(owner.spd||108)*1.15)*dt;
    let best={x:b.x,y:b.y},score=Infinity;
    const desired=Math.atan2(goal.y-b.y,goal.x-b.x);
    const currentDanger=hazardous(b.x,b.y,b.r);
    for(let i=0;i<16;i++) {
      const angle=desired+i*TAU/16,x=b.x+Math.cos(angle)*step,y=b.y+Math.sin(angle)*step;
      if(!G.World.isFree(x,y,b.r,true)||!clearPath(b.x,b.y,x,y))continue;
      let cost=Math.hypot(x-goal.x,y-goal.y)+hazardCost(x,y,b.r);
      for(const e of enemies)cost+=Math.max(0,65+b.r+(e.r||8)-Math.hypot(x-e.x,y-e.y))*5;
      for(const other of family.bodies)if(other!==b&&alive(other)&&other.formed)cost+=Math.max(0,40-Math.hypot(x-other.x,y-other.y))*4;
      if(cost<score){score=cost;best={x,y};}
    }
    if(dist(b,goal)>12||currentDanger||enemies.some(e=>dist(b,e)<b.r+(e.r||8)+38))move(b,best.x-b.x,best.y-b.y);
  }
  function updateBodies(dt) {
    const s=family,owner=s.owner;
    for(const b of s.bodies) {
      b.level=owner.level;
      b.poseAge+=dt;b.flash=Math.max(0,b.flash-dt);b.invuln=Math.max(0,b.invuln-dt);b.protectionRemaining=Math.max(0,b.protectionRemaining-dt);
      b.cooldown=Math.max(0,b.cooldown-dt);b.castRecovery=Math.max(0,(b.castRecovery||0)-dt);b.placementRetry=Math.max(0,b.placementRetry-dt);
      const capacity=owner.maxHp*b.hpFraction;if(capacity!==b.maxHp){if(alive(b))b.hp=Math.max(1,Math.min(capacity,b.hp+capacity-b.maxHp));b.maxHp=capacity;}
      if(b.dead){b.mode='down';b.reviveRemaining=Math.max(0,b.reviveRemaining-dt);if(b.reviveRemaining<=0&&b.placementRetry<=0){b.placementRetry=.25;revive(b,b.deathSerial);}continue;}
      if(!b.formed){b.mode='waiting';if(b.placementRetry<=0){b.placementRetry=.25;if(place(b,owner,b.index))reform(b);}continue;}
      const fraction=b.hp/b.maxHp;
      if(fraction<survivalConfig.retreatBelow)b.retreating=true;
      else if(fraction>=survivalConfig.resumeAbove)b.retreating=false;
      b.sinceDamage+=dt;
      b.recovering=b.retreating&&ready(b)&&dist(b,owner)<=120&&b.sinceDamage>=survivalConfig.safeRecoveryDelay&&!hazardous(b.x,b.y,b.r)&&
        !G.EnemyMgr.queryCircle(b.x,b.y,160).some(e=>alive(e)&&dist(b,e)<=120+(e.r||8));
      if(b.recovering){b.hp=Math.min(b.maxHp*survivalConfig.resumeAbove,b.hp+b.maxHp*survivalConfig.safeRecoveryRate*dt);if(b.hp>=b.maxHp*survivalConfig.resumeAbove){b.retreating=false;b.recovering=false;}}
      if(b.poseAge>.4)b.pose=null;
      const threatened=hazardous(b.x,b.y,b.r);
      b.mode=b.protectionRemaining>0?'reforming':b.recovering?'recovering':b.retreating?'retreat':threatened?'evading':b.path==='preta'?'guard':'formation';
      // Low health and telegraphed danger interrupt an approach; the next skill
      // remains available after its short cancellation retry.
      if(b.retreating||threatened)for(const f of [...s.actions])if(f.body===b&&f.kind==='soul'){cancelRequest(f);finish(f);}
      if(s.actions.some(f=>f.body===b)&&!threatened&&!b.retreating){b.mode='casting';continue;}
      if(dist(b,owner)>640&&b.placementRetry<=0){b.placementRetry=.25;if(place(b,owner,b.index))reform(b);}
      const tx=b.x,ty=b.y;follow(b,owner,dt);
      // Contact strikes are opportunistic only. Ranged/support roles never
      // abandon formation to chase a four-damage melee hit.
      b.target=ready(b)&&!b.retreating&&!threatened?nearby(b,34).find(e=>dist(b,e)<=34):null;
      if(b.target&&b.cooldown<=0) {
        b.aim=Math.atan2(b.target.y-b.y,b.target.x-b.x);
        const f=frame(owner,{id:'naruto-pain',type:'dark',dmg:4},{x:b.x,y:b.y,support:true});hit(f,b.target,4,b,true);b.cooldown=1.8;b.pose='strike';b.poseAge=0;
      }
      if(Math.hypot(b.x-tx,b.y-ty)>.01&&!b.pose){b.pose='move';b.aim=Math.atan2(b.y-ty,b.x-tx);}
    }
  }
  function updatePassives(dt) {
    const s=family;s.absorbCooldown=Math.max(0,s.absorbCooldown-dt);s.repairCooldown=Math.max(0,s.repairCooldown-dt);
    const naraka=body('naraka'),m=learned(s.owner,'repair');
    if(s.owner.dead) {
      // Saving Tendo takes the same full preparation as repairing another body.
      // A formed Naraka has this fundamental ability even before its upgrade card.
      s.repair=null;s.repairWait=0;s.repairCooldown=0;
      if(!canRevivePlayer(s.owner)){s.playerRevive=null;return;}
      if(!s.playerRevive)s.playerRevive={wait:0,age:0,period:[10,9.5,9,8.5,8][rank(m)]*(s.owner.cdMul||1),status:'waiting',retry:0};
      const r=s.playerRevive;if(!ready(naraka))return;
      r.retry=Math.max(0,r.retry-dt);
      if(r.wait<r.period){r.wait=Math.min(r.period,r.wait+dt);if(r.wait+1e-8<r.period)return;r.status='repair';r.x=naraka.x;r.y=naraka.y;naraka.pose='special';naraka.poseAge=0;return;}
      r.age+=dt;
      if(r.age<.8)return;
      r.status='unsafe';if(r.retry>0)return;r.retry=.25;
      const owner=s.owner,enemies=[...new Set(G.EnemyMgr.queryCircle(owner.x,owner.y,300))];
      let point=safePoint(owner,owner,owner.x,owner.y,enemies)?{x:owner.x,y:owner.y}:null;
      for(let ring=0;ring<8&&!point;ring++)for(let i=0;i<16;i++) {
        const angle=i*TAU/16,radius=32+ring*16,x=owner.x+Math.cos(angle)*radius,y=owner.y+Math.sin(angle)*radius;
        if(safePoint(owner,owner,x,y,enemies)){point={x,y};break;}
      }
      if(!point)return;
      owner.x=point.x;owner.y=point.y;owner.revive(.5);s.playerProtection=2;s.playerRevive=null;
      visualEffect(frame(owner,m||{id:'naruto-pain-repair',dmg:0},{support:true}),'repair-complete',.45,{x:owner.x,y:owner.y,target:owner});
      return;
    }
    s.playerRevive=null;
    if(s.repair) {
      const r=s.repair;
      if(!m||!ready(naraka)||!r.target.dead||r.target.deathSerial!==r.serial)s.repair=null;
      else if((r.age+=dt)>=.8&&r.target.placementRetry<=0){r.target.placementRetry=.25;if(revive(r.target,r.serial))s.repair=null;}
    }
    const target=['asura','animal','human','preta'].map(body).find(b=>b.dead);
    if(!m||!ready(naraka)||!target){s.repairWait=0;s.repairCooldown=0;return;}
    if(!s.repair) {
      const period=[10,9.5,9,8.5,8][rank(m)]*(s.owner.cdMul||1);
      s.repairWait+=dt;s.repairCooldown=Math.max(0,period-s.repairWait);
      if(s.repairWait+1e-8>=period){s.repair={target,serial:target.deathSerial,age:0,x:naraka.x,y:naraka.y};s.repairWait=0;naraka.pose='special';naraka.poseAge=0;}
    }
  }
  function updateAction(dt,f) {
    const s=family;
    if(!frameActive(f)||!selected(f.owner,f.m)||(f.body&&(!ready(f.body)||(f.kind==='soul'&&f.body.retreating)))){cancelRequest(f);finish(f);return;}
    f.age+=dt;const k=f.kind;
    if(k==='gravity') {
      if(!f.immediate&&f.age-dt<.35) {
        const previous=accelerate((f.age-dt)/.35),progress=accelerate(f.age/.35),step=progress-previous;
        for(const entry of f.pulls) {
          const e=entry.target;
          if(!alive(e)||!grounded(e)||dist(f.owner,e)>(f.m.triggerRadius||400)||!clearPath(f.owner.x,f.owner.y,e.x,e.y))continue;
          const remaining=Math.max(0,dist(f.owner,e)-(f.m.pullRadius??100));
          const pull=special(e)?Math.min(remaining,Math.max(0,entry.pullDistance*.25-entry.distance),entry.pullDistance*.25*step):remaining*Math.min(1,step/Math.max(1e-9,1-previous));
          const x=e.x,y=e.y;toward(e,f.owner,pull);entry.distance+=Math.hypot(e.x-x,e.y-y);
        }
        G.EnemyMgr.rebuildGrid();
      }
      if(f.immediate||f.age>=.35) {
        f.x=f.owner.x;f.y=f.owner.y;const pushes=[];
        // Pull steps can leave an exact boundary target a few floating-point units outside.
        for(const e of nearby(f,(f.m.radius||300)+1e-7)){
          hit(f,e);
          if(alive(e)&&grounded(e)){
            const d=dist(f,e),goalRadius=d+Math.max(0,(f.m.pushRadius??380)-d)*(special(e)?.25:1);
            pushes.push({target:e,goalRadius,dirX:d>1e-8?(e.x-f.x)/d:Math.cos(f.owner.aim||0),dirY:d>1e-8?(e.y-f.y)/d:Math.sin(f.owner.aim||0)});
          }
        }
        // This new effect is updated later in the same tick; start its motion clock at zero then.
        effects.push({...f,kind:'push',age:-dt,life:.4,pushProgress:0,pushes});finish(f);
      }
    } else if(k==='missiles') {
      while(f.emitted<f.count&&f.age>=.12+f.emitted*f.interval) {
        const target=f.targets[f.emitted%f.targets.length],angle=Math.atan2(target.y-f.body.y,target.x-f.body.x);
        if(shots.filter(p=>p.kind==='missile').length<60) {
          const rank=f.emitted%2?f.count-1-Math.floor(f.emitted/2):Math.floor(f.emitted/2),volley=family.castCounts.missiles||0;
          const heightSlot=(rank+volley*7)%f.count,radiusSlot=(Math.floor(f.count/2)+rank+volley*5)%f.count;
          shots.push({...f,kind:'missile',phase:'rise',lift:0,
            cruiseHeight:90+(heightSlot-(f.count-1)/2)*Math.min(5,84/Math.max(1,f.count-1)),
            orbitRadius:f.count>1?40+48*radiusSlot/(f.count-1):64,
            orbitDuration:.65+.9*f.emitted/Math.max(1,f.count-1),
            launchOffset:48,visualAngle:-Math.PI/2,trail:[],trailTime:0,orbitDirection:TAU*f.emitted/f.count,
            x:f.body.x,y:f.body.y,angle,speed:f.m.speed||400,r:5,range:f.m.range||320,distance:0,target:null,age:0});
          visualEffect(f,'missile-launch',.15,{x:f.body.x,y:f.body.y,angle:-Math.PI/2});
        }f.emitted++;
      }
      if(f.emitted===f.count)finish(f);
    } else if(k==='summon') {
      if(f.age<.18)return;f.phase='charge';
      const travel=Math.min(500*dt,300-f.distance),n=Math.ceil(travel/3);
      for(let i=0;i<n;i++) {
        const dx=Math.cos(f.angle)*travel/n,dy=Math.sin(f.angle)*travel/n;
        if(!G.World.isFree(f.x+dx,f.y+dy,45,true)){visualEffect(f,'summon-end',.25);finish(f);break;}
        f.x+=dx;f.y+=dy;f.distance+=travel/n;
        for(const e of nearby(f,45+(30)))if(!f.hit.has(e)&&dist(f,e)<=45+(e.r||8)){hit(f,e);f.hit.add(e);visualEffect(f,'summon-hit',.2,{x:e.x,y:e.y});}
      }
      if(f.distance>=300-1e-7){visualEffect(f,'summon-end',.25);finish(f);}
    } else if(k==='soul') {
      const b=f.body,e=f.target;
      if(!alive(e)||dist(e,s.owner)>300||hazardous(e.x,e.y,b.r)||!clearPath(b.x,b.y,e.x,e.y)){cancelRequest(f);finish(f);return;}
      if(dist(b,e)>48){finish(f);return;}
      f.grasp+=dt;
      if(f.grasp>=.6){hit(f,e,f.m.dmg,b,true);effects.push({...f,kind:'soul',x:e.x,y:e.y,age:0,life:.35});finish(f);}
    } else if(k==='planet') {
      const radius=f.m.radius||640,enemies=nearby(f,radius);
      for(const e of enemies)if(grounded(e))toward(e,f,100*Math.min(dt,Math.max(0,1.5-(f.age-dt)))*(special(e)?.25:1));
      G.EnemyMgr.rebuildGrid();
      while(f.ticks<3&&f.age+1e-9>=(f.ticks+1)*.5){for(const e of nearby(f,radius))hit(f,e,f.m.dmg*.125);f.ticks++;}
      if(f.age>=1.5){effects.push({...f,kind:'collapse',age:0,life:.6,hit:new Set()});finish(f);}
    }
  }
  function explode(p) {
    for(const e of nearby(p,48))hit(p,e);
    for(const prop of G.World.propsInCircle?.(p.x,p.y,48)||[])if(prop.destructible&&prop.hp>0&&clearPath(p.x,p.y,prop.x,prop.y,prop))G.World.damageProp(prop,p.m.dmg*p.attack,'#d9ad8d');
    effects.push({...p,kind:'explosion',age:0,life:.25});
  }
  function missileFlight(p,age) {
    const u=Math.min(1,age/p.diveDuration),u2=u*u,u3=u2*u,height=p.cruiseHeight??90;
    return {distance:p.diveDistance*(2*u2-u3)+Math.max(0,age-p.diveDuration)*p.diveDistance/p.diveDuration,
      lift:Math.max(0,height*(2*u3-3*u2+1)+(height/.22*p.diveDuration)*(u3-2*u2+u)),
      offset:48-36*(3*u2-2*u3)};
  }
  function missileVisual(p,previous,dt) {
    const point={x:p.x,y:p.y-p.launchOffset-p.lift,age:p.age};
    const dx=point.x-previous.x,dy=point.y-previous.y;
    if(Math.hypot(dx,dy)>1e-6)p.visualAngle=Math.atan2(dy,dx);
    p.trailTime+=dt;
    if(p.trailTime>=.025){p.trailTime%=.025;p.trail.push(point);}
    while(p.trail.length>8||p.trail[0]?.age<p.age-.18)p.trail.shift();
  }
  function aimFallingRod(p,dt) {
    const previousAge=Math.max(0,p.age-dt),trackingDt=Math.min(dt,Math.max(0,.28-previousAge));
    if(p.trackingStopped||trackingDt<=0)return;
    const e=p.target;
    if(!alive(e)||Math.hypot(e.x-p.castX,e.y-p.castY)>p.range||!clearPath(p.castX,p.castY,e.x,e.y)){p.trackingStopped=true;return;}
    const dx=e.x-p.targetX,dy=e.y-p.targetY,sampleX=p.targetX+dx*trackingDt/dt,sampleY=p.targetY+dy*trackingDt/dt;
    p.targetX=e.x;p.targetY=e.y;
    const moved=Math.hypot(dx,dy);
    if(moved>Math.max(12,600*dt)){p.trackingStopped=true;return;}
    const impactAge=p.age+Math.max(0,Math.ceil((p.fallDuration-p.age-1e-9)/dt))*dt;
    const lead=Math.min(Math.max(0,impactAge-Math.min(p.age,.28))/dt,moved>0?72/moved:0);
    let x=sampleX+dx*lead,y=sampleY+dy*lead;
    if(Math.hypot(x-p.castX,y-p.castY)>p.range||G.World.isWall(x,y)||G.World.projectileBlock(x,y,p.r)||!clearPath(p.castX,p.castY,x,y)){x=e.x;y=e.y;}
    const distance=Math.hypot(x-p.x,y-p.y),step=Math.min(1,360*trackingDt/(distance||1));
    x=p.x+(x-p.x)*step;y=p.y+(y-p.y)*step;
    if(!G.World.isWall(x,y)&&!G.World.projectileBlock(x,y,p.r)&&clearPath(p.castX,p.castY,x,y)){p.x=x;p.y=y;}
  }
  function updateShots(dt) {
    for(let i=batches.length-1;i>=0;i--) {
      const f=batches[i];if(!valid(f.owner)||f.world!==G.World){batches.splice(i,1);continue;}
      f.age+=dt;
      while(f.emitted<f.count&&f.age+1e-9>=f.emitted*f.interval) {
        let targets=f.targets.filter(e=>alive(e)&&dist(f,e)<=f.range&&clearPath(f.x,f.y,e.x,e.y));
        if(!targets.length)targets=nearby(f,f.range);
        const target=targets[f.emitted%targets.length];
        if(target&&shots.filter(p=>p.kind==='rod').length<40) {
          shots.push({...f,kind:'rod',phase:'fall',x:target.x,y:target.y,castX:f.x,castY:f.y,angle:Math.PI/2,speed:440,distance:0,r:3,
            age:f.age-f.emitted*f.interval-dt,lift:180,fallDuration:.36,target,targetX:target.x,targetY:target.y,
            toolBounce:G.NinjaToolBounce?.create(f.owner,f.m.id,f.toolBounceCount)});
          visualEffect(f,'rod-launch',.12,{x:target.x,y:target.y,angle:Math.PI/2,phase:'fall',lift:180});
        }
        f.emitted++;
      }
      if(f.emitted>=f.count)batches.splice(i,1);
    }
    for(let i=shots.length-1;i>=0;i--) {
      const p=shots[i];if(!frameActive(p)||p.world!==G.World){shots.splice(i,1);continue;}
      const previousAge=p.age,previousScreen=p.kind==='missile'?{x:p.x,y:p.y-p.launchOffset-p.lift}:null;
      p.age+=dt;let flightDt=dt,missileTravel=null,missileLiftStart=p.lift;
      if(p.kind==='rod'&&p.phase==='fall') {
        aimFallingRod(p,dt);
        const t=Math.min(1,p.age/p.fallDuration);p.lift=180*(1-t*t);
        if(t<1)continue;
        const prop=G.World.projectileBlock(p.x,p.y,p.r);
        const blocked=G.World.isWall(p.x,p.y)||prop||!clearPath(p.castX,p.castY,p.x,p.y);
        if(blocked&&prop?.destructible)G.World.damageProp(prop,p.m.dmg*p.attack,'#c6addd');
        const e=!blocked&&G.EnemyMgr.queryCircle(p.x,p.y,60).find(e=>alive(e)&&dist(p,e)<=p.r+(e.r||8));
        if(e)hit(p,e,p.m.dmg,p,true);
        visualEffect(p,'rod-hit',.22,{phase:'fall'});
        if(e&&G.NinjaToolBounce?.redirectRod(p,e)){p.phase='bounce';p.age=0;continue;}
        shots.splice(i,1);continue;
      }
      if(p.kind==='rod')G.NinjaToolBounce?.aimRod(p);
      if(p.kind==='missile') {
        if(p.phase==='rise') {
          p.lift=(p.cruiseHeight??90)*Math.min(1,p.age/.22);
          if(p.age<.22){missileVisual(p,previousScreen,dt);continue;}
          p.phase='orbit';flightDt=Math.max(0,dt-Math.max(0,.22-previousAge));
          p.orbitX=p.x;p.orbitY=p.y;p.orbitAge=0;
        }
        if(p.phase==='orbit') {
          const duration=p.orbitDuration??.65,radius=p.orbitRadius??64,step=Math.min(flightDt,duration-p.orbitAge);
          p.orbitAge+=step;
          const angle=TAU*Math.min(1,p.orbitAge/duration);
          const direction=Math.atan2(Math.sin(p.orbitDirection),Math.cos(p.orbitDirection));
          const turn=direction*Math.sin(angle/2)**2,dx=radius*(1-Math.cos(angle)),dy=-radius*Math.sin(angle);
          p.x=p.orbitX+dx*Math.cos(turn)-dy*Math.sin(turn);p.y=p.orbitY+.35*(dx*Math.sin(turn)+dy*Math.cos(turn));p.lift=p.cruiseHeight??90;
          if(p.orbitAge<duration-1e-9){missileVisual(p,previousScreen,dt);continue;}
          p.x=p.orbitX;p.y=p.orbitY;p.lift=p.cruiseHeight??90;p.phase='seek';flightDt=Math.max(0,flightDt-step);
          const targets=nearby(p,p.range);p.target=targets[p.emitted%targets.length];
          if(p.target)p.angle=Math.atan2(p.target.y-p.y,p.target.x-p.x);
          p.seekAge=0;p.diveDistance=Math.max(1,p.target?dist(p,p.target):p.range);p.diveDuration=Math.max(.25,p.diveDistance/p.speed);
          missileLiftStart=p.cruiseHeight??90;
        } else if(p.target&&!alive(p.target)) {
          p.target=nearby(p,p.range-p.distance)[0];
        }
        const before=missileFlight(p,p.seekAge);p.seekAge+=flightDt;
        const after=missileFlight(p,p.seekAge);missileTravel=after.distance-before.distance;
        p.launchOffset=after.offset;p.lift=after.lift;
      }
      if(p.kind==='missile'&&alive(p.target)) {
        const desired=Math.atan2(p.target.y-p.y,p.target.x-p.x),delta=Math.atan2(Math.sin(desired-p.angle),Math.cos(desired-p.angle));p.angle+=Math.max(-3.8*flightDt,Math.min(3.8*flightDt,delta));
      }
      const travel=Math.min(missileTravel??p.speed*flightDt,p.range-p.distance),n=Math.max(1,Math.ceil(travel/2));let gone=false;
      const missileLiftEnd=p.lift;
      const candidates=[...new Set(G.EnemyMgr.queryCircle(p.x,p.y,travel+60))];
      for(let j=0;j<n&&!gone;j++) {
        const x=p.x+Math.cos(p.angle)*travel/n,y=p.y+Math.sin(p.angle)*travel/n;
        const prop=G.World.projectileBlock(x,y,p.r);
        if(G.World.isWall(x,y)||prop) {
          if(prop?.destructible&&p.kind==='rod')G.World.damageProp(prop,p.m.dmg*p.attack,'#c6addd');gone=true;
        } else {
          p.x=x;p.y=y;p.distance+=travel/n;
          if(p.kind==='missile')p.lift=missileLiftStart+(missileLiftEnd-missileLiftStart)*(j+1)/n;
          const e=candidates.find(e=>alive(e)&&!p.toolBounce?.seen.has(e)&&(p.kind!=='missile'||p.lift<=18)&&dist(p,e)<=p.r+(e.r||8));
          if(e){if(p.kind==='rod'){
            hit(p,e,p.m.dmg,p,true);const angle=p.angle;
            if(G.NinjaToolBounce?.redirectRod(p,e)){visualEffect(p,'rod-hit',.18,{x:e.x,y:e.y,angle});break;}
          }gone=true;}
        }
      }
      if(p.kind==='missile')missileVisual(p,previousScreen,dt);
      if(p.distance>=p.range-1e-8)gone=true;
      if(gone){if(p.kind==='missile')explode(p);else visualEffect(p,'rod-hit',.18);shots.splice(i,1);}
    }
  }
  function update(dt) {
    if(family&&(!familyActive(family.owner)||family.world!==G.World)){clear();return;}
    if(G.Game.state!=='playing'||!(dt>0)||!Number.isFinite(dt))return;
    const s=ensure();if(!s||s.owner.frozen)return;
    s.clock+=dt;s.sharedRecovery=Math.max(0,s.sharedRecovery-dt);s.playerProtection=Math.max(0,s.playerProtection-dt);
    s.playerSpeedRemaining=s.owner.dead?0:Math.max(0,s.playerSpeedRemaining-dt);
    if(s.owner.dead)automatic(dt,s.owner);
    updateBodies(dt);updatePassives(dt);for(const f of [...s.actions])updateAction(dt,f);
    for(let i=s.queue.length-1;i>=0;i--)if(s.queue[i].expires<s.clock||!frameActive(s.queue[i])||!selected(s.queue[i].owner,s.queue[i].m)){cancelRequest(s.queue[i]);s.queue.splice(i,1);}
    for(let i=0;i<s.queue.length;i++) {
      const pending=s.queue[i],b=required[pending.kind]&&body(required[pending.kind]);if(b?.castRecovery>0||busy(pending))continue;
      s.queue.splice(i,1);if(!start(pending))cancelRequest(pending);i--;
    }
    updateShots(dt);
    for(let i=effects.length-1;i>=0;i--) {
      const f=effects[i];f.age=Math.min(f.life,f.age+dt);
      if(f.visualOnly&&!frameActive(f)){effects.splice(i,1);continue;}
      if(f.kind==='push'){
        if(!frameActive(f)||f.world!==G.World||!selected(f.owner,f.m)){effects.splice(i,1);continue;}
        const progress=accelerate(f.age/(f.m.pushDuration??.24)),previous=f.pushProgress||0;
        if(progress>previous){
          const fraction=Math.min(1,(progress-previous)/Math.max(1e-9,1-previous));
          for(const entry of f.pushes||[]){
            const e=entry.target;if(!alive(e)||!grounded(e))continue;
            const d=dist(f,e),travel=Math.max(0,entry.goalRadius-d)*fraction;
            move(e,(d>1e-8?(e.x-f.x)/d:entry.dirX)*travel,(d>1e-8?(e.y-f.y)/d:entry.dirY)*travel);
          }
          G.EnemyMgr.rebuildGrid();f.pushProgress=progress;
        }
      }
      if(f.kind==='collapse') {
        if(!frameActive(f)||f.world!==G.World||!selected(f.owner,f.m)){effects.splice(i,1);continue;}
        const radius=(f.m.impactRadius||960)*f.age/f.life;
        for(const e of nearby(f,radius))if(!f.hit.has(e)){
          const fixedDamage=!(e.boss||e.legend||e.judge);
          const damage=fixedDamage?e.maxHp*(f.m.normalImpactHealthRatio??.3)+f.attack:f.m.dmg;
          hit(f,e,damage,f,false,fixedDamage);f.hit.add(e);
        }
      }
      if(f.age>=f.life)effects.splice(i,1);
    }
  }
  function contact(shot,a,r=a.r+(shot.r||4)) {
    const sx=shot.px??shot.x,sy=shot.py??shot.y,dx=shot.x-sx,dy=shot.y-sy,x=sx-a.x,y=sy-a.y;
    const c=x*x+y*y-r*r;if(c<=0)return 0;
    const aa=dx*dx+dy*dy,b=2*(x*dx+y*dy),d=b*b-4*aa*c;
    if(aa<=1e-12||d<0)return Infinity;const t=(-b-Math.sqrt(d))/(2*aa);return t>=0&&t<=1?t:Infinity;
  }
  function absorbable(p) {
    return p.friendly===false&&(p.painAbsorbable===true||p.ninjutsuAbsorbable===true||p.absorbable===true)&&!p.physical&&!p.unblockable&&!p.uninterceptable&&!p.beam&&!p.laser&&!p.ground&&!p.groundField&&!p.orb&&!p.hazard;
  }
  // Native Enemy.shoot is the ordinary typed energy-bolt producer. Mark only
  // this source's explicit elemental/mental bolt types; other producers and
  // physical/unknown types remain unmarked, including boss cast projectiles.
  const energyBolts=new Set(['fire','water','electric','psychic','ice','dark']);
  const originalShoot=G.Enemy.prototype.shoot,originalSpawn=G.Projectiles.spawn;let shootingEnergy=false;
  G.Enemy.prototype.shoot=function(...args) {
    const previous=shootingEnergy;shootingEnergy=energyBolts.has(this.atkType);
    try{return originalShoot.apply(this,args);}finally{shootingEnergy=previous;}
  };
  G.Projectiles.spawn=function(options) {
    if(shootingEnergy&&options.friendly===false&&options.interceptable===true&&
      options.painAbsorbable==null&&options.ninjutsuAbsorbable==null&&options.absorbable==null)
      options={...options,painAbsorbable:true};
    return originalSpawn.call(this,options);
  };
  const oldHazards=G.Hazards.update;
  G.Hazards.update=function(dt) {
    if(family&&family.world===G.World&&familyActive(family.owner)&&!family.owner.frozen&&G.Game.state==='playing') {
      for(const h of G.Hazards.all)if(!h.hit&&h.t+dt>=h.delay)for(const b of family.bodies)
        if(ready(b)&&G.Hazards.inside(h,b.x,b.y,b.r)) {
          b.hurt(h.pct?Math.max(h.dmg,b.maxHp*h.pct):h.dmg,h.type,!!h.pure);
        }
    }
    return oldHazards.call(this,dt);
  };
  function resolve(dt,owner) {
    const s=ensure(owner);if(!s||owner!==s.owner||s.owner.frozen||G.Game.state!=='playing')return;
    const preta=body('preta'),m=learned(s.owner,'absorb'),all=G.Projectiles.all(),others=[owner,...(G.SelfClones?.actors()||[])].filter(alive);
    const absorbReady=m&&ready(preta)&&s.absorbCooldown<=0&&dist(preta,owner)<=300;
    let absorbed=0;const absorbedPoints=[];
    for(let i=all.length-1;i>=0;i--) {
      const p=all[i];if(p.friendly!==false)continue;
      let first=null,time=Math.min(...others.map(a=>contact(p,a)));
      for(const b of s.bodies)if(ready(b)) {
        const t=contact(p,b);if(t<time&&clearPath(p.px??p.x,p.py??p.y,b.x,b.y)){time=t;first=b;}
      }
      if(absorbReady&&ready(preta)&&absorbable(p)) {
        const t=contact(p,preta,36+(p.r||4));
        if(t!==Infinity&&t<=time&&clearPath(p.px??p.x,p.py??p.y,preta.x,preta.y)) {
          if(absorbedPoints.length<8)absorbedPoints.push({x:(p.px??p.x)+(p.x-(p.px??p.x))*t,y:(p.py??p.y)+(p.y-(p.py??p.y))*t});
          G.Projectiles.remove(p);absorbed++;s.intercepted++;continue;
        }
      }
      if(first){G.Projectiles.remove(p);first.hurt(p.dmg,p.mtype);}
    }
    if(absorbed){s.absorbCooldown=[2.5,2.3,2.1,1.9,1.7][rank(m)]*(owner.cdMul||1);preta.pose='special';preta.poseAge=0;
      visualEffect(frame(owner,m,{support:true}),'absorb',.3,{x:preta.x,y:preta.y,angle:preta.aim,count:absorbed,points:absorbedPoints});}
    for(const b of s.bodies)if(ready(b))for(const e of nearby(b,b.r+45)) {
      if(e.touchCd>0||e.behavior==='thief'||G.NarutoLee?.bound?.(e)||dist(e,b)>b.r+(e.r||8))continue;
      // Native touch cooldown is shared with the player and other allied bodies.
      e.touchCd=.55;e.strike?.(b);b.hurt(e.dmg,e.atkType);
    }
  }
  function clear(owner) {
    if(!owner||owner===family?.owner){family=null;shots.length=0;effects.length=0;batches.length=0;timers.clear();return;}
    timers.delete(owner);for(let i=shots.length-1;i>=0;i--)if(shots[i].owner===owner)shots.splice(i,1);
    for(let i=batches.length-1;i>=0;i--)if(batches[i].owner===owner)batches.splice(i,1);
    if(family){family.queue=family.queue.filter(f=>f.owner!==owner);family.actions=family.actions.filter(f=>f.owner!==owner);}
  }
  function actionsFor(owner){return family?.actions.filter(f=>f.owner===owner)||[];}
  function activeFor(owner){return actionsFor(owner).find(f=>!f.body)||null;}
  function gravityPoseFor(owner) {
    if(!valid(owner)||!currentFamily(root(owner)))return null;
    const pull=actionsFor(owner).find(f=>f.kind==='gravity');
    const push=effects.find(f=>f.kind==='push'&&f.owner===owner&&f.world===G.World);
    if(!pull&&!push)return null;
    const facing=Math.cos(owner.aim||0)<0?-1:1;
    if(pull){const progress=Math.min(1,pull.age/.35),tension=Math.sin(Math.PI*progress);return {phase:'pull',age:pull.age,state:'special',time:0,offsetX:-facing*2*tension,offsetY:1.5*tension};}
    const release=Math.max(0,Math.min(1,push.age/push.life)),settle=smoothStep(release);
    return {phase:'push',age:push.age,state:release<.8?'special':'idle',time:release<.8?.125:0,offsetX:facing*3*(1-settle),offsetY:-1.5*Math.sin(Math.PI*release)};
  }
  function stateFor(owner) {
    const s=family;if(!s||root(owner)!==s.owner||s.world!==G.World)return null;
    return {...s,action:activeFor(owner)||s.actions[0]||null,actors:s.bodies,bodies:s.bodies,shots:shots.filter(p=>p.owner===owner).length,count:s.lastCount,basicCooldown:timers.get(owner)||0};
  }
  function snapshot(owner) {
    const s=stateFor(owner);if(!s)return null;
    return {clock:s.clock,count:s.count,shots:s.shots,basicCooldown:s.basicCooldown,sharedRecovery:s.sharedRecovery,
      absorbCooldown:s.absorbCooldown,repairCooldown:s.repairCooldown,repairWait:s.repairWait,playerRevive:playerReviveState(s.owner),
      repairStage:s.repair?'repair':s.repairWait>0?'waiting':'idle',repair:s.repair?{path:s.repair.target.path,age:s.repair.age,remaining:Math.max(0,.8-s.repair.age)}:null,
      intercepted:s.intercepted,revives:s.revives,queue:s.queue.length,castCounts:{...s.castCounts},actions:s.actions.map(f=>({kind:f.kind,phase:f.phase,age:f.age})),action:s.action?{kind:s.action.kind,phase:s.action.phase,age:s.action.age}:null,
      actors:s.bodies.map(b=>({id:b.id,path:b.path,x:b.x,y:b.y,hp:b.hp,maxHp:b.maxHp,dead:b.dead,reviveRemaining:b.reviveRemaining,hpFraction:b.hpFraction,formed:b.formed,protectionRemaining:b.protectionRemaining,retreating:b.retreating,recovering:b.recovering,sinceDamage:b.sinceDamage,mode:b.mode}))};
  }
  // Visual phases use simulation age, so pause and scene cleanup also freeze/remove them.
  function planetVisual(f) {
    const radius=f.m.radius||640,scale=f.m.visualScale??1.5,artRadius=320*scale,release=f.kind==='collapse'?Math.min(1,f.age/f.life):0;
    const age=f.kind==='collapse'?1.5:f.age,gather=Math.max(0,Math.min(1,(age-.18)/.87));
    const shell=artRadius*.29*gather,fall=Math.max(0,Math.min(1,(age-1.15)/.35));
    const height=f.kind==='collapse'?shell*(1-release):scale*(24+196*Math.min(1,age/.28))-(220*scale-shell)*fall*fall;
    return {radius,artRadius,scale,release,gather,height,waveRadius:(f.m.impactRadius||960)*release,
      shell:shell*(1-release*.5),
      phase:f.kind==='collapse'?'impact':age<.28?'rise':age<1.05?'gather':age<1.15?'seal':'fall'};
  }
  function planetRock(ctx,x,y,size,angle,tone=0,scale=1) {
    ctx.save();ctx.translate(Math.round(x),Math.round(y));ctx.rotate(angle);
    ctx.fillStyle=['#817967','#a0967e','#686354'][tone%3];ctx.strokeStyle='#38382f';ctx.lineWidth=2*scale;
    ctx.beginPath();ctx.moveTo(-size,-size*.35);ctx.lineTo(-size*.45,-size*.8);
    ctx.lineTo(size*.55,-size*.65);ctx.lineTo(size,size*.15);ctx.lineTo(size*.35,size*.75);
    ctx.lineTo(-size*.7,size*.6);ctx.closePath();ctx.fill();ctx.stroke();
    ctx.strokeStyle='#b6ab8e';ctx.beginPath();ctx.moveTo(-size*.65,-size*.3);ctx.lineTo(-size*.3,-size*.55);ctx.lineTo(size*.4,-size*.45);ctx.stroke();ctx.restore();
  }
  function planetGround(ctx,f) {
    const v=planetVisual(f),r=v.radius;
    ctx.save();ctx.translate(f.x,f.y);ctx.globalAlpha*=1-v.release;
    ctx.fillStyle='#23251f';ctx.globalAlpha*=.18;ctx.beginPath();ctx.ellipse(0,0,32*v.scale+v.shell*.8,12*v.scale+v.shell*.3,0,0,TAU);ctx.fill();
    ctx.globalAlpha/=.18;ctx.strokeStyle='#686252';ctx.lineWidth=2*v.scale;
    for(let i=0;i<12;i++) {
      const a=i*TAU/12+.13,len=v.artRadius*(.32+(i%3)*.17)*Math.min(1,f.age/.3);
      ctx.beginPath();ctx.moveTo(Math.cos(a)*24*v.scale,Math.sin(a)*24*v.scale);
      ctx.lineTo(Math.cos(a+.08)*len*.6,Math.sin(a+.08)*len*.6);
      ctx.lineTo(Math.cos(a)*len,Math.sin(a)*len);ctx.stroke();
    }
    ctx.strokeStyle='#aaa18a';ctx.globalAlpha*=.36;ctx.lineWidth=1;
    ctx.beginPath();ctx.arc(0,0,r,0,TAU);ctx.stroke();
    if(!v.release&&v.phase!=='fall')for(let i=0;i<12;i++) {
      const t=(f.age*1.25+i/12)%1,a=i*2.39996,d=v.artRadius*(1-t);
      ctx.beginPath();ctx.moveTo(Math.cos(a)*d,Math.sin(a)*d);
      ctx.lineTo(Math.cos(a+.025)*(d+18*v.scale),Math.sin(a+.025)*(d+18*v.scale));ctx.stroke();
    }
    ctx.restore();
  }
  function planetAir(ctx,f) {
    const v=planetVisual(f),r=v.artRadius;
    ctx.save();ctx.translate(f.x,f.y);ctx.globalAlpha*=1-v.release;
    if(f.kind==='collapse') {
      // The moon has contacted the ground; the visible front delivers one hit per enemy.
      for(let i=0;i<24;i++) {
        const a=i*2.39996,d=v.shell*(.35+(i%5)*.14)+v.release*r*.35;
        planetRock(ctx,Math.cos(a)*d,-v.height+Math.sin(a)*d*.7+v.release*v.release*80*v.scale,(8+(i%4)*3)*v.scale,a+v.release*2,i,v.scale);
      }
      ctx.strokeStyle='#e2d3aa';ctx.lineWidth=8*v.scale;ctx.globalAlpha*=.8;
      ctx.beginPath();ctx.arc(0,0,v.waveRadius,0,TAU);ctx.stroke();
      ctx.strokeStyle='#9a8b6e';ctx.lineWidth=14*v.scale;ctx.globalAlpha*=.5;
      ctx.beginPath();ctx.arc(0,0,Math.max(0,v.waveRadius-16*v.scale),0,TAU);ctx.stroke();ctx.restore();return;
    }
    // Independent fragments rise from all directions; they do not orbit flat around the core.
    if(f.age>.12&&f.age<1.05)for(let i=0;i<24;i++) {
      const t=(f.age*.9+i/24)%1,a=i*2.39996,d=r*(.45+(i%4)*.15)*(1-t);
      const x=Math.cos(a)*d,y=Math.sin(a)*d-v.height*t;
      ctx.strokeStyle='#a39b85';ctx.globalAlpha*=.32;ctx.lineWidth=v.scale;
      ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+Math.cos(a)*14*v.scale,y+18*v.scale);ctx.stroke();ctx.globalAlpha/=.32;
      planetRock(ctx,x,y,(5+(i%4)*2+t*4)*v.scale,a+t,i,v.scale);
    }
    if(v.phase==='fall') {
      ctx.strokeStyle='#c5b896';ctx.lineWidth=2*v.scale;ctx.globalAlpha*=.55;
      for(let i=0;i<7;i++) {
        const x=(i-3)*v.shell*.26,y=-v.height-v.shell*.65;
        ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x,y-(28+(i%3)*10)*v.scale);ctx.stroke();
      }
      ctx.globalAlpha/=.55;
    }
    ctx.translate(0,-v.height);
    ctx.fillStyle='#101018';ctx.beginPath();ctx.arc(0,0,(10+5*v.gather)*v.scale,0,TAU);ctx.fill();
    if(v.shell>5) {
      ctx.save();ctx.beginPath();
      for(let i=0;i<24;i++){const a=i*TAU/24,rr=v.shell*(i%3===0?.97:1),x=Math.round(Math.cos(a)*rr),y=Math.round(Math.sin(a)*rr);if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)}
      ctx.closePath();ctx.fillStyle='#655f50';ctx.fill();ctx.strokeStyle='#302f29';ctx.lineWidth=3*v.scale;ctx.stroke();ctx.clip();
      // Offset lithic plates give the moon volume while the lower rim stays dark.
      for(let i=0;i<38;i++) {
        const a=i*2.39996,d=Math.sqrt(i/38)*v.shell;
        planetRock(ctx,Math.cos(a)*d,Math.sin(a)*d,v.shell*(.19+(i%3)*.035),a,i,v.scale);
      }
      ctx.fillStyle='#292a26';ctx.globalAlpha*=.28;
      ctx.beginPath();ctx.ellipse(v.shell*.4,v.shell*.65,v.shell*.9,v.shell*.45,-.4,0,TAU);ctx.fill();ctx.restore();
    }
    ctx.restore();
  }
  function air(ctx) {
    if(!family)return;ctx.save();
    for(const p of shots) {
      if(drawSkill(p.kind==='rod'?'basic':'missiles','shot',ctx,p))continue;
      ctx.save();ctx.translate(p.x,p.y-12);ctx.rotate(p.angle);ctx.fillStyle=p.kind==='rod'?'#151521':'#8b929d';
      ctx.fillRect(-9,-2,18,4);if(p.kind==='missile'){ctx.fillStyle='#ee9c5b';ctx.fillRect(-14,-2,6,4);ctx.fillStyle='#414454';ctx.fillRect(-5,-5,5,10);}ctx.restore();
    }
    for(const f of family.actions) {
      if(f.kind!=='planet'&&drawSkill(f.kind,'action',ctx,f))continue;
      if(f.kind==='summon'&&f.phase==='charge') {
        G.PainArt?.draw(ctx,{path:'rhino',x:f.x,y:f.y,height:70,state:'move',time:f.age,facing:Math.cos(f.angle)<0?-1:1});
      }
      if(f.kind==='planet') {
        planetAir(ctx,f);
        drawSkill('planet','action',ctx,f);
      }
      if(f.kind==='soul'&&f.phase==='grasp'){ctx.strokeStyle='#dcccec';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(f.body.x,f.body.y-20);ctx.lineTo(f.target.x,f.target.y-20);ctx.stroke();}
    }
    if(!drawSkill('repair','support',ctx,family)) {
      if(family.repair){const r=family.repair;G.PainArt?.draw(ctx,{path:'king',x:r.x,y:r.y,height:88,state:'special',time:r.age});}
      if(family.playerRevive&&family.playerRevive.age>0){const r=family.playerRevive;G.PainArt?.draw(ctx,{path:'king',x:r.x,y:r.y,height:88,state:'special',time:r.age});}
    }
    drawSkill('absorb','support',ctx,family);
    for(const e of effects) {
      ctx.globalAlpha=1;
      if(e.kind==='collapse'){planetAir(ctx,e);drawSkill('planet','effect',ctx,e);continue;}
      const name={push:'gravity',explosion:'missiles',soul:'soul','soul-blink':'soul','rod-hit':'basic','rod-launch':'basic','missile-launch':'missiles','summon-hit':'summon','summon-end':'summon',absorb:'absorb','repair-complete':'repair'}[e.kind];
      if(name&&drawSkill(name,'effect',ctx,e))continue;
      if(e.visualOnly)continue;
      ctx.globalAlpha=1-e.age/e.life;ctx.strokeStyle=e.kind==='explosion'?'#e9ab7c':'#b8a1ce';ctx.lineWidth=3;ctx.beginPath();ctx.arc(e.x,e.y,e.kind==='push'?(e.m?.radius||300):48*e.age/e.life,0,TAU);ctx.stroke();
    }
    const owner=family.owner;
    if(alive(owner)){
      ctx.globalAlpha=1;ctx.font='700 10px "Segoe UI",system-ui,sans-serif';ctx.textAlign='center';ctx.textBaseline='bottom';
      const y=owner.y-visualHeight('tendo',owner)-5;
      ctx.lineWidth=3;ctx.strokeStyle='#18202c';ctx.strokeText('你',owner.x,y);ctx.fillStyle='#ffd778';ctx.fillText('你',owner.x,y);
    }
    ctx.restore();
  }
  function ground(ctx) {
    if(!family)return;ctx.save();ctx.strokeStyle='#9f85bb';ctx.lineWidth=1;ctx.globalAlpha=.45;
    for(const p of shots)if(p.kind==='rod'&&p.phase==='fall')drawSkill('basic','ground',ctx,p);
    for(const f of family.actions) {
      if(f.kind==='planet'){planetGround(ctx,f);drawSkill('planet','ground',ctx,f);continue;}
      if(drawSkill(f.kind,'ground',ctx,f))continue;
      if(f.kind==='gravity'){ctx.beginPath();ctx.arc(f.owner.x,f.owner.y,f.m.radius||300,0,TAU);ctx.stroke();}
    }
    for(const f of effects)if(f.kind==='collapse'){planetGround(ctx,f);drawSkill('planet','ground',ctx,f);}
    drawSkill('repair','ground',ctx,family);
    ctx.restore();
  }
  function automatic(dt,owner) {
    const moves=(owner.moves||[]).filter(m=>['gravity','missiles','summon','soul','planet'].includes(kind(m)));
    for(const m of moves)m.t=Math.max(0,(m.t||0)-dt);
    // Start the pull/push combo when ready; otherwise allow a worthwhile planet.
    const gravity=moves.find(m=>kind(m)==='gravity'),planet=moves.find(m=>kind(m)==='planet');
    if(gravity&&nearby(owner,gravity.triggerRadius||400).length&&canCast(owner,gravity))cast(owner,gravity);
    else if(planet&&canCast(owner,planet))cast(owner,planet);
    else if(gravity&&canCast(owner,gravity))cast(owner,gravity);
    for(const m of moves)if(required[kind(m)]&&canCast(owner,m))cast(owner,m);
  }
  const oldTick=C.tick,oldUpdate=C.updateFields,oldResolve=C.resolve,oldClear=C.clearFields,oldAir=C.drawAirFields,oldGround=C.drawGroundFields;
  C.tick=function(dt,owner,now) {
    const result=oldTick.call(this,dt,owner,now);
    if(valid(owner)&&G.Game.state==='playing'&&!owner.frozen&&dt>0) {
      ensure(owner);automatic(dt,owner);const m=learned(owner,'basic');if(m){const remaining=(timers.get(owner)||0)-dt;timers.set(owner,remaining);if(remaining<=0&&basic(owner,m))timers.set(owner,Math.max(.05,(m.cd||1.2)*(owner.cdMul||1)));}
    }
    return result;
  };
  C.updateFields=function(dt){const result=oldUpdate.call(this,dt);update(dt);return result;};
  C.resolve=function(dt,owner,now){resolve(dt,owner);return oldResolve.call(this,dt,owner,now);};
  C.clearFields=function(owner){const result=oldClear.call(this,owner);clear(owner);return result;};
  C.drawAirFields=function(ctx){oldAir.call(this,ctx);air(ctx);};
  C.drawGroundFields=function(ctx){oldGround.call(this,ctx);ground(ctx);};
  const enemyUpdate=G.Enemy.prototype.update;
  G.Enemy.prototype.update=function(dt,player) {
    let target=player,distance=alive(player)?dist(this,player):Infinity;
    if(family&&family.world===G.World&&familyActive(family.owner)&&!this.dead&&!this.remote&&this.behavior!=='thief') {
      const candidates=family.bodies.filter(ready).map(b=>({body:b,distance:dist(this,b)})).filter(b=>b.distance<distance).sort((a,b)=>a.distance-b.distance);
      for(const {body:b} of candidates)if(clearPath(this.x,this.y,b.x,b.y)){target=b;break;}
    }
    const x=this.x,y=this.y,result=enemyUpdate.call(this,dt,target),f=family?.actions.find(f=>f.kind==='soul'&&f.phase==='grasp'&&f.target===this);
    if(f?.kind==='soul'&&f.phase==='grasp'&&f.target===this&&alive(f.body)&&alive(this)&&G.Game.state==='playing') {
      // Own displacement correction leaves the native slow and jump timers intact.
      const amount=special(this)?.2:.7;move(this,(x-this.x)*amount,(y-this.y)*amount);
    }
    return result;
  };
  const originalHurt=G.Player.prototype.hurt,originalHeal=G.Player.prototype.heal,originalOnDealt=G.Player.prototype.onDealt;
  const originalRevive=G.Player.prototype.revive;
  G.Player.prototype.revive=function(...args){
    const wasDead=this.dead,result=originalRevive.apply(this,args);
    if(wasDead&&alive(this)&&currentFamily(this))family.playerSpeedRemaining=5;
    return result;
  };
  G.Player.prototype.hurt=function(...args){if(currentFamily(this)&&family.playerProtection>0)return;return originalHurt.apply(this,args);};
  G.Player.prototype.heal=function(...args){if(currentFamily(this)&&this.dead)return;return originalHeal.apply(this,args);};
  G.Player.prototype.onDealt=function(...args){if(currentFamily(this)&&this.dead)return;return originalOnDealt.apply(this,args);};
  G.NarutoPain={supports,canCast,cast,update,clear,activeFor,actionsFor,gravityPoseFor,stateFor,snapshot,canRevivePlayer,playerReviveState,speedMultiplier,visualHeights,visualHeight,survivalConfig,planetVisual,
    actors:()=>family?.bodies.filter(ready)||[],actorsFor:owner=>root(owner)===family?.owner?family.bodies:[],
    drawables:cam=>family?.bodies.filter(a=>a.formed&&cam.sees(a.x,a.y,Math.max(100,visualHeight(a.path,a.sourceOwner)+12)))||[],
    get shots(){return shots;},get effects(){return effects;},absorbable};
})();
