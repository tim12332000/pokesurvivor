/* Rasenshuriken presentation: approved pixel art, no combat or timing changes. */
(() => {
  'use strict';
  if(G.NarutoRasenshurikenVFX)return;
  const game=G,TAU=Math.PI*2;
  let c,pixelStyle=true;
  const sprites=new Map();
  // Use the production VFX art pixel and palette, keeping the approved silhouette.
  // These are runtime canvases, like G.VFX.sprite; no bitmap assets are imported.
  function pixelSprite(context,key,x,y,extent,scale,paint,outline=true){
    let sprite=sprites.get(key);
    const pixel=game.Sprites.PX;
    if(!sprite){
      const size=Math.ceil(extent*2/pixel)+3,center=Math.floor(size/2);
      sprite=document.createElement('canvas');sprite.width=sprite.height=size;
      const raster=sprite.getContext('2d',{willReadFrequently:true}),prior=c;
      raster.translate(center,center);raster.scale(1/pixel,1/pixel);
      c=raster;try{paint()}finally{c=prior}
      const data=raster.getImageData(0,0,size,size),rgba=data.data;
      const pal=game.VFX.PAL['naruto-blue'].map(hex=>{const v=parseInt(hex.slice(1),16);return [v>>16&255,v>>8&255,v&255]});
      const solid=new Uint8Array(size*size);
      for(let i=0;i<rgba.length;i+=4){
        if(rgba[i+3]<48){rgba[i+3]=0;continue}
        let nearest=pal[0],distance=Infinity;
        for(const color of pal){const d=(rgba[i]-color[0])**2+(rgba[i+1]-color[1])**2+(rgba[i+2]-color[2])**2;if(d<distance){distance=d;nearest=color}}
        rgba[i]=nearest[0];rgba[i+1]=nearest[1];rgba[i+2]=nearest[2];
        rgba[i+3]=rgba[i+3]<150?110:255;solid[i/4]=rgba[i+3]===255?1:0;
      }
      if(outline)for(let py=1;py<size-1;py++)for(let px=1;px<size-1;px++){
        const n=py*size+px,i=n*4;
        if(rgba[i+3]===0&&(solid[n-1]||solid[n+1]||solid[n-size]||solid[n+size])){
          rgba[i]=pal[0][0];rgba[i+1]=pal[0][1];rgba[i+2]=pal[0][2];rgba[i+3]=255;
        }
      }
      raster.putImageData(data,0,0);sprites.set(key,sprite);
      if(sprites.size>100)sprites.delete(sprites.keys().next().value);
    }
    context.save();context.imageSmoothingEnabled=false;
    const k=pixel*scale,anchor=Math.floor(sprite.width/2);
    context.drawImage(sprite,Math.round(x)-anchor*k,Math.round(y)-anchor*k,sprite.width*k,sprite.height*k);context.restore();
  }
  const clamp=t=>Math.max(0,Math.min(1,t));
  function arc(x,y,r,a,len,color,width=1,sy=1){c.save();c.translate(x,y);c.scale(1,sy);c.strokeStyle=color;c.lineWidth=width;c.beginPath();c.arc(0,0,r,a,a+len);c.stroke();c.restore();}
  function sphere(x,y,r,t){
    c.save();c.translate(x,y);
    // Offset colour bands shade a volume; the filaments follow its curved surface.
    const bands=pixelStyle?[[0,0,1,'#1767aa'],[-.04,-.08,.91,'#35bfff'],[-.11,-.15,.75,'#9feaff'],[-.19,-.2,.47,'#ffffff']]:[[0,0,1,'#379fd3'],[-.05,-.06,.94,'#88e8fb'],[-.08,-.09,.78,'#c3f8ff'],[-.12,-.12,.55,'#eeffff']];
    for(const [ox,oy,rr,col] of bands){
      c.fillStyle=col;c.beginPath();c.arc(ox*r,oy*r,rr*r,0,TAU);c.fill();
    }
    c.beginPath();c.arc(0,0,r-.5,0,TAU);c.clip();
    const strands=pixelStyle?3:7;
    for(let j=0;j<strands;j++){
      c.strokeStyle=pixelStyle?'#35bfff':j%3?'#f4ffff':'#48b9e1';c.lineWidth=pixelStyle?2.5:j%3?1.2:1;
      c.beginPath();
      for(let k=0;k<=36;k++){
        const u=k/36,a=u*TAU*1.15-t*13+j*TAU/strands;
        const rr=r*Math.sin(u*Math.PI)*.96;
        const xx=Math.cos(a)*rr,yy=Math.sin(a)*rr*.57+(u-.5)*r*.65;
        if(k===0)c.moveTo(xx,yy);else c.lineTo(xx,yy);
      }c.stroke();
    }
    c.restore();arc(x,y,r-.7,-2.8,2.1,'#efffff',1.5);
  }
  function weapon(x,y,s,t,alpha=1){
    if(!pixelStyle)return smoothWeapon(x,y,s,t,alpha);
    const frame=Math.floor(t*24),context=c;
    context.save();context.globalAlpha*=alpha;
    pixelSprite(context,'weapon:'+frame,x,y,70,s,()=>smoothWeapon(0,0,1,frame/24));context.restore();
  }
  function smoothWeapon(x,y,s,t,alpha=1){
    c.save();c.globalAlpha=alpha;c.translate(Math.round(x),Math.round(y));c.scale(s,s);
    // Studied anime frames show swept ribbons and a changing wind envelope,
    // rather than an identical rigid star turning as a single solid object.
    for(let j=0;j<3;j++){
      c.globalAlpha=alpha*(.32-j*.075);
      arc(0,0,44+j*5,t*27+j*2,1.05+j*.17,'#9feaff',j===0?2.5:1.5,.6);
      arc(0,0,46+j*5,-t*19+j*2.2,.45,'#ffffff',1,.6);
    }
    // Avoid 90-degree steps between sampled frames: four identical blades alias to stillness.
    c.globalAlpha=alpha;c.save();c.scale(1,.6);c.rotate(t*10);
    for(let i=0;i<4;i++){
      c.save();c.rotate(i*TAU/4);
      const sweep=3*Math.sin(t*21+i*Math.PI),tip=60+2*Math.sin(t*17+i);
      for(let wake=2;wake>0;wake--){
        c.save();c.rotate(-wake*.2);c.globalAlpha=alpha*(wake===1?.18:.09);c.fillStyle='#9feaff';
        c.beginPath();c.moveTo(9,-8);c.bezierCurveTo(25,-18,46,-17,tip,-9+sweep);c.quadraticCurveTo(30,-6,13,7);c.closePath();c.fill();c.restore();
      }
      c.fillStyle='#35bfff';c.beginPath();c.moveTo(8,-8);c.bezierCurveTo(22,-19,44,-19,tip,-9+sweep);c.quadraticCurveTo(34,-5,12,11);c.closePath();c.fill();
      c.fillStyle='#ffffff';c.beginPath();c.moveTo(10,-7);c.bezierCurveTo(25,-16,44,-17,tip,-9+sweep);c.quadraticCurveTo(33,-5,13,6);c.closePath();c.fill();
      c.strokeStyle='#9feaff';c.lineWidth=1.5;c.beginPath();c.moveTo(15,5);c.quadraticCurveTo(31,-5,46,-10);c.stroke();c.restore();
    }
    c.restore();sphere(0,0,18,t);
    arc(0,2,21,t*17,1.8,'#d5fcff',1.2,.6);
    arc(0,-2,23,t*17+Math.PI,1.1,'#f4ffff',1,.6);c.restore();
  }
  function burst(x,y,age){
    if(!pixelStyle)return smoothBurst(x,y,age);
    const frame=Math.floor(age*20),context=c;
    pixelSprite(context,'burst:'+frame,x,y,122,1,()=>smoothBurst(0,0,frame/20),false);
  }
  function smoothBurst(x,y,age){
    const q=clamp(age/.65),r=15+97*(1-Math.pow(1-q,3)),fade=Math.pow(1-q,1.3);
    c.save();c.globalAlpha=fade;
    // Translucent blue envelope, with curved white ribbons instead of concentric rings.
    c.globalAlpha=fade*.16;c.fillStyle='#6fd9f4';c.beginPath();c.ellipse(x,y,r*.92,r*.8,0,0,TAU);c.fill();
    c.globalAlpha=fade;
    for(let i=0;i<4;i++){
      const a=age*9+i*TAU/4;
      c.save();c.translate(x,y);c.scale(1,.8);c.rotate(a);
      c.fillStyle=i%2?'#c8faff':'#85ddeb';
      c.beginPath();c.moveTo(-r*.83,-r*.15);
      c.bezierCurveTo(-r*.3,-r*.98,r*.85,-r*.65,r*.9,r*.12);
      c.bezierCurveTo(r*.55,-r*.63,-r*.22,-r*.7,-r*.83,-r*.15);c.fill();c.restore();
    }
    for(let i=0;i<6;i++){
      const rr=r*(.32+i*.105),a=age*12+i*1.9;
      arc(x,y,rr,a,1.65,i%2?'#d6faff':'#63bed9',i%2?2.5:1.5,.84);
      arc(x,y,rr+2,a+.12,.9,'#eefeff',1,.84);
    }
    // Open arcs reveal the target throughout the expanding wind envelope.
    for(let i=0;i<9;i++){
      const a=i*TAU/9+age*(i%2?7:-5),rr=r*(.7+(i%3)*.12);
      arc(x,y,rr,a,.55+i%3*.2,i%3===0?'#f3ffff':'#9ae5f4',i%3===0?2:1,.84);
      arc(x,y,rr-3,a+.08,.33,'#438eb7',1,.84);
    }
    for(let i=0;i<22;i++){
      const a=i*2.399+age*2,rr=r*(.35+(i%7)*.1),len=(1-q)*(4+i%5);
      c.strokeStyle=i%3?'#a3ebf3':'#f0ffff';c.lineWidth=1;c.beginPath();c.moveTo(x+Math.cos(a)*rr,y+Math.sin(a)*rr*.84);c.lineTo(x+Math.cos(a+.05)*(rr+len),y+Math.sin(a+.05)*(rr+len)*.84);c.stroke();
    }
    if(age<.17){const v=1-age/.17;c.globalAlpha=v*.85;sphere(x,y,12+age*80,age);for(let i=0;i<4;i++){c.save();c.translate(x,y);c.rotate(i*TAU/4+.3);c.fillStyle='#e1ffff';c.beginPath();c.moveTo(4,-2);c.lineTo(44*v,-3);c.lineTo(12,2);c.closePath();c.fill();c.restore()}}
    c.restore();
  }

  const effects=[];
  const controlled=owner=>G.SelfClones?.isControlled(owner)??owner===G.Game.player;
  const valid=f=>f.world===G.World&&controlled(f.owner)&&!f.owner.dead&&f.owner.hp>0;
  function drawWeapon(ctx,x,y,{age=0,scale=.9,alpha=1,pixelated=true}={}) {
    const previous=c,style=pixelStyle;c=ctx;pixelStyle=pixelated;
    try{weapon(x,y,scale,age,alpha)}finally{c=previous;pixelStyle=style}
  }
  function drawBurst(ctx,x,y,age,radius=110,{pixelated=true}={}) {
    const previous=c,style=pixelStyle;c=ctx;pixelStyle=pixelated;
    ctx.save();ctx.translate(x,y);ctx.scale(radius/110,radius/110);
    try{burst(0,0,age)}finally{ctx.restore();c=previous;pixelStyle=style}
  }
  function drawProjectile(ctx,p) {
    if(p.mid!=='naruto-rasenshuriken')return false;
    if(!p.owner||p.owner.dead||p.owner.hp<=0)return true;
    const alpha=Math.min(1,(p.life-p.t)*4);
    drawWeapon(ctx,p.x,p.y-G.LIFT,{age:p.t,scale:.9,alpha});
    return true;
  }
  function impact(owner,x,y,radius) {
    const f={owner,world:G.World,x,y,radius,age:0};
    if(valid(f))effects.push(f);
  }
  function clear(owner) {
    for(let i=effects.length-1;i>=0;i--)if(!owner||effects[i].owner===owner)effects.splice(i,1);
  }
  const C=G.Combat,update=C.updateFields,air=C.drawAirFields,clearFields=C.clearFields,clearSkills=G.DigimonSkills.clear;
  C.updateFields=function(dt){
    update.call(this,dt);
    for(let i=effects.length-1;i>=0;i--){const f=effects[i];f.age+=dt;if(!valid(f)||f.age>=.65)effects.splice(i,1)}
  };
  C.drawAirFields=function(ctx){
    air.call(this,ctx);
    for(const f of effects)if(valid(f)&&G.Camera.sees(f.x,f.y,f.radius+20))drawBurst(ctx,f.x,f.y-G.LIFT,f.age,f.radius);
  };
  C.clearFields=function(owner){clearFields.call(this,owner);clear(owner)};
  G.DigimonSkills.clear=function(owner){clearSkills.call(this,owner);clear(owner)};
  G.NarutoRasenshurikenVFX={drawWeapon,drawBurst,drawProjectile,impact,clear,get activeBursts(){return effects.slice()},get cachedFrames(){return sprites.size}};
})();
