/* Circular iris emblems: cached by evolution stage, resolved at draw time. */
(() => {
  if(G.SharinganIcons)return;
  const moveId='naruto-sharingan';
  const key=level=>'sharingan-'+Math.max(1,Math.min(5,Math.floor(level)||1));
  function eye(level){
    // The supplied chart: 1/2/3 tomoe, Sasuke's six-petal Mangekyo,
    // then its eternal pattern. More native pixels keep the petals distinct.
    const rows=Array.from({length:64},()=>Array(64).fill('.'));
    for(let y=0;y<64;y++)for(let x=0;x<64;x++){
      const dx=(x-31.5)/32,dy=(y-31.5)/32,r=Math.hypot(dx,dy);
      if(r>.94)continue;
      let black=r>.88;
      if(level<=3){
        black ||= r<.105||Math.abs(r-.47)<.042;
        for(let n=0;n<level;n++){
          const angle=-Math.PI/2+n*Math.PI*2/level;
          black ||= Math.hypot(dx-.51*Math.cos(angle),dy-.51*Math.sin(angle))<.105;
          for(let t=0;t<=1;t+=.1){
            const a=angle+t*.46,radius=.51+t*.10;
            black ||= Math.hypot(dx-radius*Math.cos(a),dy-radius*Math.sin(a))<.075*(1-t)+.012;
          }
        }
      }else if(r<=.88){
        let petal=false,seam=false;
        for(let n=0;n<3;n++){
          const angle=-Math.PI/2+n*Math.PI/3;
          const u=dx*Math.cos(angle)+dy*Math.sin(angle),v=-dx*Math.sin(angle)+dy*Math.cos(angle);
          const ellipse=(u/.83)**2+(v/.34)**2;
          if(ellipse<1)petal=true;
          if(Math.abs(ellipse-1)<.10&&r<.70)seam=true;
        }
        black=!petal||seam||r<.105;
        if(level===5)for(let n=0;n<3;n++){
          const angle=-Math.PI/2+n*Math.PI*2/3;
          const u=dx*Math.cos(angle)+dy*Math.sin(angle),v=-dx*Math.sin(angle)+dy*Math.cos(angle);
          if(u>0&&u<.65&&Math.abs(v-.11*Math.sin(Math.PI*u/.65))<.06+.04*u/.65)black=true;
          // Three inner connecting strokes distinguish the eternal pattern.
          if(u>-.23&&u<.22&&Math.abs(v-.24)<.04)black=true;
        }
      }
      rows[y][x]=black?'k':'r';
    }
    return {pal:{k:'#100c10',r:'#d83d38'},rows:rows.map(row=>row.join(''))};
  }
  for(let level=1;level<=5;level++)G.Icons.UI[key(level)]=eye(level);
  const forMove=move=>move.id===moveId?key(move.lvl):'move:'+move.id;
  const resolve=name=>name==='move:'+moveId?key(G.Game?.player?.moves.find(move=>move.id===moveId)?.lvl||1):name;
  const original={canvas:G.Icons.canvas,url:G.Icons.url,html:G.Icons.html,draw:G.Icons.draw};
  G.Icons.canvas=name=>original.canvas(resolve(name));
  G.Icons.url=name=>original.url(resolve(name));
  G.Icons.html=(name,size=20,cls='')=>{
    const resolved=resolve(name);
    return resolved.startsWith('sharingan-')?`<img class="${cls}" src="${original.url(resolved)}" width="${size}" height="${size}" alt="" draggable="false">`:original.html(resolved,size,cls);
  };
  G.Icons.draw=(ctx,name,x,y,size)=>{
    const resolved=resolve(name);
    if(!resolved.startsWith('sharingan-'))return original.draw(ctx,resolved,x,y,size);
    const smooth=ctx.imageSmoothingEnabled;
    ctx.imageSmoothingEnabled=true;ctx.drawImage(original.canvas(resolved),x,y,size,size);ctx.imageSmoothingEnabled=smooth;
  };
  const offer=G.LevelUp.offer;
  G.LevelUp.offer=(owner,...args)=>offer(owner,...args).map(card=>{
    if(card.key==='new:'+moveId)return {...card,icon:key(1)};
    if(card.key==='up:'+moveId){
      const next=G.Moves.instance(moveId,(owner.moves.find(move=>move.id===moveId)?.lvl||1)+1);
      return {...card,icon:key(next.lvl),title:next.name};
    }
    return card;
  });
  G.SharinganIcons={key,forMove};
})();
