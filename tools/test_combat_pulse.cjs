const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const hits=[],enemies=[];
const owner={hp:100,dead:false,dmgDealt:0,moves:[{id:'test',dealt:0}],percentHealthDamage:.01,lifestealRate:.1,damageSplashPicks:1,
 onDealt(d){this.healed=(this.healed||0)+d*this.lifestealRate;},heal(d){this.healed=(this.healed||0)+d;}};
class Enemy{constructor(x,y){this.x=x;this.y=y;this.hp=this.maxHp=10000;this.dead=false;this.types=['normal'];}
 hurt(amount,col,dx,dy,knock,eff,actor,id){this.hp-=amount;if(this.hp<=0)this.dead=true;hits.push({enemy:this,amount,owner:actor,id,secondary:G.DamageSplash.isSecondary()});const move=actor.moves.find(m=>m.id===id);if(move)move.dealt+=amount;}}
const G={LevelUp:{STATS:[]},Enemy,Player:class{},World:{isWall:()=>false,projectileBlock:()=>false},Game:{state:'playing',everyone:()=>[owner]},
 EnemyMgr:{queryCircle:(x,y,r)=>enemies.filter(e=>Math.hypot(e.x-x,e.y-y)<=r)},SelfClones:{isControlled:a=>a===owner||a.clone,isActor:a=>!!a.clone},NarutoTemariReflect:null};
global.G=G;
for(const path of ['.omx/damage-splash.js','.omx/percent-health-damage.js','.omx/combat-pulse.js'])vm.runInThisContext(fs.readFileSync(path,'utf8'),{filename:path});
const P=G.CombatPulse;P.beginRun();
const a=new Enemy(0,0),b=new Enemy(10,0),outer=new Enemy(25,0),blocked=new Enemy(400,0);enemies.push(a,b,outer,blocked);
const packet=P.create(owner,'test'),batch=[{target:a,primaryDirectDamage:100},{target:b,primaryDirectDamage:200},{target:a,primaryDirectDamage:80}];
const result=P.apply(packet,0,batch);assert.equal(result.primaryHits,2);assert.equal(result.secondaryHits,1);assert.equal(a.maxHp-a.hp,200);assert.equal(b.maxHp-b.hp,300);assert.equal(outer.maxHp-outer.hp,20);assert.equal(owner.healed,50);assert.equal(owner.dmgDealt,520);assert.equal(owner.moves[0].dealt,520);
assert.equal(P.apply(packet,0,batch),false);assert(P.apply(packet,1,batch));assert.equal(outer.maxHp-outer.hp,40);
const reversed=P.create(owner,'test');assert.equal(P.apply(reversed,0,batch.toReversed()).secondaryDamage,20);
const clone={...owner,clone:true,healed:0,dmgDealt:0,moves:[{id:'test',dealt:0}],percentHealthDamage:0,damageSplashPicks:1};
const cloned=P.create(clone,'test');assert.equal(P.apply(cloned,0,[{target:a,primaryDirectDamage:30}]).primaryDamage,30);assert.equal(clone.dmgDealt,36);assert.equal(P.apply(cloned,1,[{target:a,primaryDirectDamage:30}]).primaryDamage,30);
const stale=P.create(owner,'test');P.beginRun();assert.equal(P.apply(stale,0,batch),false);
const paused=P.create(owner,'test');G.Game.state='paused';assert.equal(P.apply(paused,0,batch),false);G.Game.state='playing';assert(P.apply(paused,0,batch));
const wall=P.create(owner,'test');G.World.isWall=(x,y)=>x>15&&x<18;assert.equal(P.apply(wall,0,[{target:a,primaryDirectDamage:100}]).secondaryHits,1);G.World.isWall=()=>false;
owner.dead=true;assert.equal(P.apply(P.create(owner,'test'),0,batch),false);owner.dead=false;
const oldScope=G.DamageSplash.isSecondary();assert.throws(()=>G.DamageSplash.withSecondary(()=>{throw Error('fixture')}));assert.equal(G.DamageSplash.isSecondary(),oldScope);
for(let i=0;i<120;i++)P.apply(P.create(owner,'test'),0,[]);
assert.equal(P.telemetry.length,96);assert(hits.filter(h=>h.secondary).every(h=>h.amount%10===0||h.owner===clone));
console.log('PASS: primary batch/max outer, percent/lifesteal isolation, duplicate/second pulse, clone attribution, epoch/pause/death, occlusion and secondary scope.');
