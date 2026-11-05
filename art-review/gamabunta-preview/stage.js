/* Small, isolated stage adapter. No game boot, save, menus, spawners or input. */
(() => {
  const enemies=[];
  G.Sprites={PX:2};G.Settings={fx:2,get:()=>true};
  G.Camera={scale:1,sees:()=>true};G.Types={mult:()=>1,label:()=>null};G.Weather={mult:()=>1};
  G.World={isFree:()=>true,isWall:()=>false,projectileBlock:()=>false,projectilePathClear:()=>true,propsInCircle:()=>[]};
  G.EnemyMgr={queryCircle:(x,y,r)=>enemies.filter(e=>!e.dead&&Math.hypot(e.x-x,e.y-y)<=r+e.r)};
  G.Player=class{hurt(){}update(){}};
  const owner=new G.Player();Object.assign(owner,{x:-135,y:0,mon:{dex:30001},hp:100,maxHp:100,atk:1,critChance:0,dmgDealt:0,onDealt(){}});
  G.Game={player:owner};G.DigimonSkills={clear(){}};
  function distance(x,y,ax,ay,bx,by){const dx=bx-ax,dy=by-ay,t=Math.max(0,Math.min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy||1)));return Math.hypot(x-ax-dx*t,y-ay-dy*t)}
  G.Combat={updateFields(){},drawGroundFields(){},drawAirFields(){},clearFields(){},resolve(){
    for(const shot of [...G.Projectiles.all()])for(const e of enemies){
      if(e.dead||shot.hits?.has(e.id)||distance(e.x,e.y,shot.px??shot.x,shot.py??shot.y,shot.x,shot.y)>shot.r+e.r)continue;
      shot.hits.add(e.id);if(!shot.ghost)e.hurt(shot.dmg,shot.color);
      G.Projectiles.remove(shot);break;
    }
  }};
  let id=0;
  window.GamabuntaStage={enemies,owner,reset(side){
    enemies.length=0;owner.x=-135*side;owner.hp=100;owner.dead=false;
    for(const [x,y] of [[0,0],[100,40],[100,80],[200,0]]){
      enemies.push({id:++id,x:x*side,y,r:10,hp:1e6,types:['normal'],flash:0,hurt(amount,color){this.flash=.15;G.FX.dmgText(this.x,this.y-34,Math.round(amount),color||'#ffe3aa')}});
    }
  }};
})();
