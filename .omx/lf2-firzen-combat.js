/* Classic LF2 Firzen: held cannon stream, rising ice/fire chase and Arctic Volcano. */
(() => {
  'use strict';
  if (G.LF2Firzen) return;
  const DEX=30019,C=G.Combat,EPS=1e-8,states=new Map(),leases=new Map();
  // Registration, combat and card previews read this same profile inventory.
  const specs={
    'lf2-firzen-cannon':{name:'冰火砲 · Firzen Cannon',type:'normal',learnLevel:1,cd:2,damage:100,
      ranges:[620,670,720,780,840],radii:[14,16,18,20,22],counts:[4,5,6,7,8],cap:16,speed:450,
      sourceStart:265,charge:10/30,firstGap:5/30,interval:4/30,
      desc:'原版雙手推出冰火砲，第一發重砲後接持續前進的砲流。每段獨立穿過敵群，牆與障礙會截斷；原作按住續射改為有限連發。'},
    'lf2-firzen-disaster':{name:'冰火追擊 · Overwhelming Disaster',type:'ice',learnLevel:3,cd:5.8,damage:64,
      ranges:[720,780,840,900,980],radii:[20,22,24,26,28],counts:[8,10,12,14,16],cap:32,speed:330,
      sourceStart:240,charge:8/30,duration:18/30,rise:.32,freeze:1.2,
      desc:'舉手放出上升的冰火彈，短暫升空後各自追蹤可達敵人；冰彈凍結、火彈灼燒。每顆有獨立飛行與接觸，放出後不再占用身體。'},
    'lf2-firzen-volcano':{name:'極地火山 · Arctic Volcano',type:'fire',learnLevel:6,cd:8.5,damage:90,
      ranges:[160,180,200,220,250],radii:[38,42,46,50,56],counts:[6,7,8,9,10],cap:16,
      sourceStart:249,charge:17/30,duration:44/30,groundLife:1.1,freeze:1.2,
      desc:'原版凝聚後引爆中央火焰，兩側六組冰柱與六簇地火依次迸發，接續冰火追蹤彈。每組三根冰柱、每簇地火及追蹤彈都有獨立接觸；俯視排列與成長是本作改編。'}
  };
  const alive=a=>!!a&&!a.dead&&a.hp>0;
  const controlled=a=>G.SelfClones?.isControlled?.(a)??(a===G.Game.player||!!G.SelfClones?.isActor?.(a));
  const valid=a=>alive(a)&&controlled(a)&&(a.mon?.dex??a.dex)===DEX;
  const learned=(a,id)=>a.moves?.some(m=>m.id===id);
  const supports=m=>Object.hasOwn(specs,typeof m==='string'?m:m?.digiMode||m?.id);
  const terminal=()=>G.Game.state==='ui'||G.Game.state==='over';
  const finite=(n,fallback)=>Number.isFinite(n)?n:fallback;
  const strong=e=>!!(e.boss||e.elite||e.legend||e.judge);
  const clamp=n=>Math.max(0,Math.min(1,n));
  function profile(owner,m){
    const mode=m?.digiMode||m?.id,d=specs[mode];if(!d)return null;
    const L=Math.max(0,Math.min(4,(m.lvl||1)-1));
    const count=Math.min(d.cap,G.Quantity?.count(owner,d.counts[L])??d.counts[L]);
    const duration=mode==='lf2-firzen-cannon'?d.charge+d.firstGap+Math.max(0,count-2)*d.interval+4/30:d.duration;
    return {...d,mode,count,duration,range:finite(m.range,d.ranges[L]),radius:finite(m.radius,d.radii[L]),
      damage:finite(m.dmg,d.damage),cd:finite(m.cd,d.cd)};
  }
  function clear(owner){
    G.LF2Audio?.stop?.(owner);
    if(owner)states.delete(owner);else states.clear();
    for(const [e,list]of leases){const keep=owner?list.filter(l=>l.s.owner!==owner):[];if(keep.length)leases.set(e,keep);else leases.delete(e);}
  }
  function state(owner){
    let s=states.get(owner);
    if(s&&(s.world!==G.World||s.epoch!==G.CombatPulse.epoch)){clear(owner);s=null;}
    if(!s){s={owner,world:G.World,epoch:G.CombatPulse.epoch,clock:0,action:null,effects:[],ready:new Map(),casts:{},hits:0,damage:0,punchReady:0,punchSerial:0};states.set(owner,s);}
    return s;
  }
  const stateLegal=s=>states.get(s.owner)===s&&valid(s.owner)&&s.world===G.World&&s.epoch===G.CombatPulse.epoch;
  const legal=(s,f)=>stateLegal(s)&&learned(s.owner,f.m.id)&&G.CombatPulse.legal(f.cast);
  function firstBlock(ax,ay,bx,by,r=1){
    const steps=Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/4));
    for(let i=1;i<=steps;i++){
      const x=ax+(bx-ax)*i/steps,y=ay+(by-ay)*i/steps;
      if(G.World.isWall?.(x,y))return {x,y,wall:true};
      const prop=G.World.projectileBlock?.(x,y,r);if(prop)return {x,y,prop};
    }return null;
  }
  const path=(ax,ay,bx,by)=>!firstBlock(ax,ay,bx,by);
  function nearby(x,y,r){
    return [...new Set(G.EnemyMgr.queryCircle(x,y,r+96))].filter(e=>alive(e)&&!e.friendly&&Math.hypot(e.x-x,e.y-y)<=r+(e.r||0));
  }
  function targetFor(owner,m){
    const p=profile(owner,m);if(!p)return null;
    const enemies=nearby(owner.x,owner.y,p.range).filter(e=>path(owner.x,owner.y,e.x,e.y))
      .sort((a,b)=>Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y));
    return enemies[0]||(G.World.propsInCircle?.(owner.x,owner.y,p.range)||[]).filter(e=>e.hp>0&&e.destructible!==false&&
      Math.hypot(e.x-owner.x,e.y-owner.y)<=p.range+(e.r||0)&&!firstBlock(owner.x,owner.y,e.x,e.y)?.wall)
      .sort((a,b)=>Math.hypot(a.x-owner.x,a.y-owner.y)-Math.hypot(b.x-owner.x,b.y-owner.y))[0]||null;
  }
  function canCast(owner,m){
    return valid(owner)&&!owner.frozen&&G.Game.state==='playing'&&supports(m)&&learned(owner,m.id)&&
      !state(owner).action&&(m.t||0)<=EPS&&!!targetFor(owner,m);
  }
  function choreography(f){
    const last=f.mode==='lf2-firzen-cannon'?f.charge+(f.count>1?f.firstGap+(f.count-2)*f.interval:0):f.charge;
    f.phase=f.age<f.charge?'windup':f.age<last+EPS?'release':'recovery';
    f.phaseAge=Math.max(0,f.age-(f.phase==='windup'?0:f.phase==='release'?f.charge:last));
    f.progress=clamp(f.phase==='windup'?f.age/f.charge:f.phaseAge/Math.max(.01,f.duration-last));
    f.sourceAge=f.age;
    if(f.mode==='lf2-firzen-cannon'&&f.age>=last+2/30){f.sourceStart=280;f.sourceAge=f.age-last-2/30;}
  }
  function cast(owner,m){
    if(!canCast(owner,m))return false;
    const s=state(owner),p=profile(owner,m),target=targetFor(owner,m),aim=Math.atan2(target.y-owner.y,target.x-owner.x);
    const f={...p,owner,m:{...m},age:0,sourceAge:0,aim,phase:'windup',released:false,flashReleased:false,
      x:owner.x,y:owner.y,pulse:0,shotIndex:0,nextShot:p.charge,damage:p.damage*(owner.atk??1)*(G.NarutoSupport?.takeAttackBonus(owner)||1)};
    f.cast=G.CombatPulse.create(owner,m.id,{channel:'body'});f.cast.targetIsLegal=()=>legal(s,f);
    s.action=f;s.ready.delete(m.id);s.casts[m.id]=(s.casts[m.id]||0)+1;
    choreography(f);owner.aim=aim;owner.cast?.(m);m.t=Math.max(.05,p.cd*(owner.cdMul??1));m.castAt=performance.now();return true;
  }
  function freeze(s,f,e,duration){
    if(!alive(e)||!legal(s,f))return;
    let list=leases.get(e);if(!list)leases.set(e,list=[]);
    const old=list.find(l=>l.s===s&&l.id===f.m.id),until=s.clock+(strong(e)?Math.min(.28,duration):duration);
    if(old)old.until=Math.max(old.until,until);else list.push({s,id:f.m.id,until,duration});
  }
  function frozenTargets(){
    const out=[];for(const [enemy,list]of leases){
      if(!alive(enemy))continue;
      const active=list.filter(l=>stateLegal(l.s)&&learned(l.s.owner,l.id)&&l.until>l.s.clock);
      if(!active.length)continue;
      const best=active.reduce((a,b)=>a.until-a.s.clock>b.until-b.s.clock?a:b);
      out.push({enemy,remaining:best.until-best.s.clock,duration:best.duration});
    }return out;
  }
  function freezeStatus(enemy){
    if(!alive(enemy))return null;
    let best=null;
    for(const l of leases.get(enemy)||[])if(stateLegal(l.s)&&learned(l.s.owner,l.id)&&l.until>l.s.clock&&
      (!best||l.until-l.s.clock>best.until-best.s.clock))best=l;
    return best?{enemy,remaining:best.until-best.s.clock,duration:best.duration}:null;
  }
  const stopped=enemy=>!!freezeStatus(enemy);
  function contact(s,f,enemies,ratio=1,element='normal'){
    if(!legal(s,f))return false;
    const color=element==='ice'?'#adf4ff':element==='fire'?'#ffad66':'#f4ebff';
    const hits=enemies.map(e=>{
      const mult=G.Types?.mult?.(element,e.types)??1,crit=Math.random()<(s.owner.critChance||0);
      return {target:e,primaryDirectDamage:f.damage*ratio*mult*(G.Weather?.mult?.(element)??1)*(crit?1.5:1),
        color,eff:crit?'crit':G.Types?.label?.(mult),onHit(){
          if(!legal(s,f)){f.cast.runEpoch=-1;return;}
          if(element==='ice')freeze(s,f,e,f.freeze||1.2);
          if(element==='fire')e.applyBurn?.(1);
        }};
    });
    const result=G.CombatPulse.apply(f.cast,f.pulse++,hits);
    if(result&&stateLegal(s)){s.hits+=result.primaryHits;s.damage+=result.primaryDamage;}
    return result;
  }
  function damageProp(s,f,p,ratio=1){if(legal(s,f)&&p?.hp>0&&p.destructible!==false)G.World.damageProp?.(p,f.damage*ratio,'#e9e7ff');}
  function origin(s,f,frame){
    const lift=32*(s.owner.anim?.scale||1),pose={...f,sourceReleaseFrame:frame,sourceStart:frame,sourceAge:0};
    const socket=G.LF2BossArt?.pointFor?.(s.owner,pose,'release');
    return {x:finite(socket?.x,s.owner.x),y:Number.isFinite(socket?.y)?socket.y+lift:s.owner.y,lift};
  }
  function addEffect(s,f,e){if(legal(s,f))s.effects.push({...e,action:f,age:e.age??0,sourceAge:0,dead:false});}
  function cannonShot(s,f,index){
    const o=origin(s,f,index?272:270),block=firstBlock(s.owner.x,s.owner.y,o.x,o.y);
    if(block){damageProp(s,f,block.prop,index?.32:1);return;}
    addEffect(s,f,{kind:'cannon',...o,aim:f.aim,speed:f.speed,range:f.range,life:f.range/f.speed,
      radius:f.radius,scale:f.radius/13.5,sourceObject:'firzen_ball',sourceStart:index?2:0,
      sourceLoop:index?2:0,element:'normal',ratio:index?.32:1,hits:new Set(),traveled:0});
    G.LF2BossArt?.playSound?.(index?'070':'092',s.owner);
  }
  function disaster(s,f){
    const o=origin(s,f,244),block=firstBlock(s.owner.x,s.owner.y,o.x,o.y);
    if(block){damageProp(s,f,block.prop);return;}
    addEffect(s,f,{kind:'rising-emitter',...o,startLift:o.lift,topLift:o.lift+84,life:15/30,radius:18,scale:1,sourceObject:'firzen_chasef',sourceStart:50});
    for(let i=0;i<f.count&&legal(s,f);i++){
      const ice=i%2===0,aim=f.aim+(i%2?1:-1)*(.5+Math.floor(i/2)*.16);
      addEffect(s,f,{kind:'chase',...o,startLift:o.lift+84,age:-12/30-i*.035,aim,phase:'rise',rise:.2,life:4.5,speed:f.speed,range:f.range,
        radius:f.radius,scale:f.radius/19,sourceObject:ice?'firzen_chasei':'firzen_chasef',sourceStart:0,sourceLoop:ice?3:0,
        element:ice?'ice':'fire',target:null,traveled:0,index:i});
    }
  }
  function volcano(s,f){
    // Original engine hit_Fa11 creates six column mothers (each three columns),
    // six ground flames, the central explosion and a separate seeker controller.
    const axis={x:Math.cos(f.aim),y:Math.sin(f.aim)},side={x:-Math.sin(f.aim),y:Math.cos(f.aim)};
    const reach=Math.max(0,f.range-f.radius);
    const originalIce=[[.8,-.28],[1,0],[.8,.28],[-.8,-.28],[-1,0],[-.8,.28]];
    const originalFire=[[-.3,-.42],[.3,-.42],[-.3,.20],[.3,.20],[0,-.64],[0,.64]];
    const at=(u,v)=>({x:s.owner.x+(axis.x*u+side.x*v)*reach,y:s.owner.y+(axis.y*u+side.y*v)*reach});
    for(let i=0;i<f.count&&legal(s,f);i++){
      const extra=i>=6,turn=extra?(i-6)*Math.PI*2/Math.max(1,f.count-6):0;
      const ice=extra?[Math.cos(turn)*.9,Math.sin(turn)*.36]:originalIce[i];
      const flame=extra?[Math.cos(turn)*.52,Math.sin(turn)*.52]:originalFire[i];
      const sign=ice[0]>=0?1:-1;
      for(let j=0;j<3&&legal(s,f);j++){
        const offset=(2-j)*Math.min(18,reach*.15),point=at(ice[0]-sign*offset/Math.max(1,reach),ice[1]);
        const block=firstBlock(s.owner.x,s.owner.y,point.x,point.y);
        if(block){damageProp(s,f,block.prop,.7);continue;}
        const sourceStart=[60,50,0][j],baseRadius=[27,32.5,35][j];
        addEffect(s,f,{kind:'volcano-column',...point,lift:0,aim:f.aim,age:-(2+j*6)/30,life:19/30,
          radius:f.radius,scale:f.radius/baseRadius,sourceObject:'freeze_column',sourceStart,
          element:'ice',hits:new Set(),activeStart:0,activeEnd:13/30,index:i*3+j});
      }
      const point=at(flame[0],flame[1]),block=firstBlock(s.owner.x,s.owner.y,point.x,point.y);
      if(block){damageProp(s,f,block.prop,.7);continue;}
      addEffect(s,f,{kind:'volcano-flame',...point,lift:0,aim:f.aim,life:f.groundLife,radius:f.radius,
        scale:f.radius/18,sourceObject:'firen_flame',sourceStart:50,sourceLoop:52,
        element:'fire',nextTick:4/30,tick:16/30,ratio:.35,index:i});
    }
    addEffect(s,f,{kind:'eruption',x:s.owner.x,y:s.owner.y,lift:0,aim:f.aim,life:24/30,radius:f.radius*1.5,
      scale:f.radius*1.5/72,sourceObject:'firen_flame',sourceStart:109,element:'fire',hits:new Set(),activeStart:2/30,activeEnd:18/30,ratio:.9});
    // Engine action81 spawns another disaster after the eruption; this belongs
    // to Volcano and does not require buying or recursively triggering Disaster.
    const count=Math.min(20,Math.max(4,Math.floor(f.count*2/3)));
    const o={x:s.owner.x,y:s.owner.y,lift:100};
    for(let i=0;i<count&&legal(s,f);i++){
      const ice=i%2===0;
      addEffect(s,f,{kind:'chase',...o,startLift:100,age:-.2-i*.035,aim:f.aim+i*Math.PI*2/count,phase:'rise',rise:.2,life:4,speed:330,range:560,
        radius:20,scale:20/19,sourceObject:ice?'firzen_chasei':'firzen_chasef',sourceStart:0,sourceLoop:ice?3:0,
        element:ice?'ice':'fire',target:null,traveled:0,index:i,ratio:.55});
    }
    G.LF2BossArt?.playSound?.('071',s.owner);
  }
  function advanceProjectile(s,e,dt){
    const f=e.action,dx=Math.cos(e.aim),dy=Math.sin(e.aim),distance=Math.min(e.speed*dt,Math.max(0,e.range-e.traveled));
    const steps=Math.max(1,Math.ceil(distance/4));
    for(let i=0;i<steps&&legal(s,f)&&!e.dead;i++){
      const x=e.x+dx*distance/steps,y=e.y+dy*distance/steps,block=firstBlock(e.x,e.y,x,y,e.radius*.5);
      if(block){damageProp(s,f,block.prop,e.ratio??1);e.dead=true;impact(s,e);break;}
      e.x=x;e.y=y;e.traveled+=distance/steps;
      const scale=e.scale||1,offset=e.kind==='cannon'?-40.5*scale:0,half=e.kind==='cannon'?27.5*scale:0;
      const cx=x+dx*offset,cy=y+dy*offset;
      const inside=v=>{const vx=v.x-cx,vy=v.y-cy,along=vx*dx+vy*dy,t=clamp((along+half)/Math.max(.001,2*half));
        const px=cx+dx*(-half+2*half*t),py=cy+dy*(-half+2*half*t);
        return Math.hypot(v.x-px,v.y-py)<=e.radius+(v.r||0);};
      const victims=nearby(cx,cy,e.radius+half).filter(v=>(!e.hits||!e.hits.has(v))&&inside(v)&&path(cx,cy,v.x,v.y));
      if(victims.length){
        contact(s,f,victims,e.ratio??1,e.element);
        if(e.hits)for(const v of victims)e.hits.add(v);else{e.dead=true;impact(s,e);}
      }
    }
  }
  function impact(s,e){
    addEffect(s,e.action,{kind:'impact',x:e.x,y:e.y,lift:e.lift||0,aim:e.aim,life:8/30,radius:e.radius,
      scale:e.scale,sourceObject:e.sourceObject,sourceStart:10,element:e.element});
  }
  function areaContact(s,e,radius=e.radius){
    const f=e.action,victims=nearby(e.x,e.y,radius).filter(v=>(!e.hits||!e.hits.has(v))&&path(e.x,e.y,v.x,v.y));
    if(victims.length){contact(s,f,victims,e.ratio??1,e.element);if(e.hits)for(const v of victims)e.hits.add(v);}
    for(const p of G.World.propsInCircle?.(e.x,e.y,radius)||[]){
      if(!legal(s,f))break;
      if(e.hits?.has(p)||Math.hypot(p.x-e.x,p.y-e.y)>radius+(p.r||0)||firstBlock(e.x,e.y,p.x,p.y)?.wall)continue;
      damageProp(s,f,p,e.ratio??1);e.hits?.add(p);
    }
  }
  function step(s,dt){
    s.clock+=dt;const f=s.action;
    if(f){
      if(!legal(s,f))s.action=null;else{
        f.age+=dt;f.x=s.owner.x;f.y=s.owner.y;choreography(f);
        if(f.kind==='punch'&&!f.released&&f.age+EPS>=f.charge){
          f.released=true;const victims=nearby(s.owner.x,s.owner.y,f.range).filter(e=>Math.abs(Math.atan2(Math.sin(Math.atan2(e.y-s.owner.y,e.x-s.owner.x)-f.aim),Math.cos(Math.atan2(e.y-s.owner.y,e.x-s.owner.x)-f.aim)))<.9&&path(s.owner.x,s.owner.y,e.x,e.y));
          contact(s,f,victims,1,'fighting');G.LF2BossArt?.playSound?.('007',s.owner);
        }else if(f.mode==='lf2-firzen-cannon'){
          while(f.shotIndex<f.count&&f.age+EPS>=f.nextShot&&legal(s,f)){
            cannonShot(s,f,f.shotIndex);f.shotIndex++;f.released=true;f.nextShot=f.charge+f.firstGap+Math.max(0,f.shotIndex-1)*f.interval;
          }
        }else if(f.mode==='lf2-firzen-disaster'){
          if(!f.flashReleased&&f.age+EPS>=6/30){f.flashReleased=true;
            const o=origin(s,f,243);addEffect(s,f,{kind:'disaster-flash',...o,life:8/30,scale:1,radius:20,sourceObject:'firzen_chasef',sourceStart:70});}
          if(!f.released&&f.age+EPS>=f.charge){f.released=true;disaster(s,f);G.LF2BossArt?.playSound?.('020',s.owner);}
        }else if(f.mode==='lf2-firzen-volcano'&&!f.released&&f.age+EPS>=f.charge){f.released=true;volcano(s,f);}
        if(f.age+EPS>=f.duration&&s.action===f)s.action=null;
      }
    }
    for(const e of s.effects){
      if(!legal(s,e.action)){e.dead=true;continue;}
      e.age+=dt;if(e.age<0)continue;e.sourceAge=e.age;
      if(e.kind==='chase'){
        if(e.age<e.rise){e.lift=e.startLift??102;e.phase='forming';}
        else{
          e.phase='seek';e.lift=32+((e.startLift??102)-32)*Math.max(0,1-(e.age-e.rise)/.38);
          if(!alive(e.target)||!path(e.x,e.y,e.target.x,e.target.y))e.target=nearby(e.x,e.y,e.range-e.traveled).filter(v=>path(e.x,e.y,v.x,v.y))
            .sort((a,b)=>Math.hypot(a.x-e.x,a.y-e.y)-Math.hypot(b.x-e.x,b.y-e.y))[0]||null;
          if(e.target){const wanted=Math.atan2(e.target.y-e.y,e.target.x-e.x),diff=Math.atan2(Math.sin(wanted-e.aim),Math.cos(wanted-e.aim));e.aim+=Math.max(-6*dt,Math.min(6*dt,diff));}
          advanceProjectile(s,e,dt);
        }
      }else if(e.kind==='rising-emitter')e.lift=e.startLift+(e.topLift-e.startLift)*clamp(e.age/(12/30));
      else if(e.kind==='cannon')advanceProjectile(s,e,dt);
      else if(e.kind==='volcano-column'&&e.age+EPS>=e.activeStart&&e.age<e.activeEnd){
        const growth=e.age<2/30?.37:e.age<5/30?.65:1;areaContact(s,e,e.radius*growth);
      }else if(e.kind==='volcano-flame'&&e.age+EPS>=e.nextTick){e.nextTick+=e.tick;areaContact(s,e);}
      else if(e.kind==='eruption'&&e.age+EPS>=e.activeStart&&e.age<e.activeEnd)areaContact(s,e);
      if(e.age+EPS>=e.life||e.traveled>=e.range-EPS&&(e.kind==='cannon'||e.kind==='chase')){if(!e.dead&&(e.kind==='cannon'||e.kind==='chase'))impact(s,e);e.dead=true;}
    }
    s.effects=s.effects.filter(e=>!e.dead);
  }
  function update(dt){
    if(terminal()){clear();return;}
    if(G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    for(const [owner,s]of states){
      if(!stateLegal(s)){clear(owner);continue;}if(owner.frozen)continue;
      let left=dt;while(left>EPS&&stateLegal(s)){const part=Math.min(.02,left);step(s,part);left-=part;}
    }
    for(const [e,list]of leases){const keep=list.filter(l=>alive(e)&&stateLegal(l.s)&&learned(l.s.owner,l.id)&&l.until>l.s.clock);if(keep.length)leases.set(e,keep);else leases.delete(e);}
  }
  function punch(s,m){
    const target=nearby(s.owner.x,s.owner.y,58).filter(e=>path(s.owner.x,s.owner.y,e.x,e.y))[0];if(!target)return false;
    const owner=s.owner,f={kind:'punch',mode:'lf2-firzen-punch',owner,m:{...m},age:0,aim:Math.atan2(target.y-owner.y,target.x-owner.x),
      sourceStart:s.punchSerial++%2?65:60,sourceAge:0,range:58*(owner.anim?.scale||1),charge:2/30,duration:5/30,
      damage:Math.max(20,(m.dmg||100)*.25)*(owner.atk??1),pulse:0};
    f.cast=G.CombatPulse.create(owner,m.id,{channel:'body'});f.cast.targetIsLegal=()=>legal(s,f);
    s.action=f;s.punchReady=s.clock+.48*(owner.cdMul??1);owner.aim=f.aim;owner.cast?.(m);s.casts['lf2-firzen-punch']=(s.casts['lf2-firzen-punch']||0)+1;return true;
  }
  const pose=(owner=G.Game.player)=>{const s=states.get(owner);return s&&stateLegal(s)?s.action:null;};
  const renderStates=()=>[...states.values()].filter(s=>stateLegal(s)&&!terminal());
  const oldTick=C.tick,oldUpdate=C.updateFields,oldClear=C.clearFields,oldAir=C.drawAirFields;
  C.tick=function(dt,owner,now){
    if((owner?.mon?.dex??owner?.dex)!==DEX)return oldTick.call(this,dt,owner,now);
    if(!valid(owner)||owner.frozen||G.Game.state!=='playing'||!Number.isFinite(dt)||dt<=0)return;
    const s=state(owner),moves=(owner.moves||[]).filter(m=>supports(m));
    for(const m of moves){m.t=Math.max(0,(m.t||0)-dt);if(m.t<=EPS&&!s.ready.has(m.id))s.ready.set(m.id,s.clock);}
    if(s.action)return;
    const ready=moves.filter(m=>canCast(owner,m)).sort((a,b)=>(s.ready.get(a.id)??Infinity)-(s.ready.get(b.id)??Infinity));
    if(ready[0])cast(owner,ready[0]);else if(s.clock+EPS>=s.punchReady){const core=moves.find(m=>m.digiMode==='lf2-firzen-cannon');if(core)punch(s,core);}
  };
  C.updateFields=function(dt){const result=oldUpdate.call(this,dt);update(dt);return result;};
  C.clearFields=function(owner){const result=oldClear.call(this,owner);clear(owner);return result;};
  C.drawAirFields=function(ctx){oldAir.call(this,ctx);G.LF2BossArt?.drawEffects?.(ctx,DEX);};
  G.LF2Firzen={dex:DEX,specs,supports,handles:supports,profile,cast,canCast,targetFor,update,clear,pose,activeFor:pose,renderStates,freezeStatus,frozenTargets,stopped,
    stateFor:(owner=G.Game.player)=>{const s=states.get(owner);return s&&stateLegal(s)?s:null;},
    stats:(owner=G.Game.player)=>{const s=states.get(owner);return s?{casts:{...s.casts},hits:s.hits,damage:s.damage,effects:s.effects.length}:null;}};
})();
