/* Circular iris emblems: cached by evolution stage, resolved at draw time. */
(() => {
  if(G.SharinganIcons)return;
  const moveId='naruto-sharingan';
  const key=level=>'sharingan-'+Math.max(1,Math.min(5,Math.floor(level)||1));
  function eye(level){
    const rows=Array.from({length:16},()=>Array(16).fill('.'));
    const set=(x,y,color)=>{if(rows[y]?.[x]!==undefined)rows[y][x]=color;};
    for(let y=0;y<16;y++)for(let x=0;x<16;x++){
      const dx=x-7.5,dy=y-7.5,radius=Math.hypot(dx,dy);
      if(radius>7.4)continue;
      let color=radius>6.5?'k':dy>2?'d':'r';
      if(radius<1.4)color='k';
      if(level===4&&radius>1&&radius<5.6&&Math.sin(Math.atan2(dy,dx)*3+radius*.55)>.05)color='k';
      if(level===5&&radius>1&&radius<5.6&&Math.cos(Math.atan2(dy,dx)*6)>.05)color='k';
      set(x,y,color);
    }
    if(level<=3)for(let n=0;n<level;n++){
      const angle=-Math.PI/2+n*Math.PI*2/level;
      const x=Math.round(7.5+Math.cos(angle)*4),y=Math.round(7.5+Math.sin(angle)*4);
      set(x,y,'k');set(x-1,y,'k');set(x,y-1,'k');
      set(x-Math.round(Math.sin(angle)),y+Math.round(Math.cos(angle)),'k');
    }
    return {pal:{k:'#130c19',r:'#ee293f',d:'#a90f2c'},rows:rows.map(row=>row.join(''))};
  }
  for(let level=1;level<=5;level++)G.Icons.UI[key(level)]=eye(level);
  const forMove=move=>move.id===moveId?key(move.lvl):'move:'+move.id;
  const resolve=name=>name==='move:'+moveId?key(G.Game?.player?.moves.find(move=>move.id===moveId)?.lvl||1):name;
  const original={canvas:G.Icons.canvas,url:G.Icons.url,html:G.Icons.html,draw:G.Icons.draw};
  G.Icons.canvas=name=>original.canvas(resolve(name));
  G.Icons.url=name=>original.url(resolve(name));
  G.Icons.html=(name,...args)=>original.html(resolve(name),...args);
  G.Icons.draw=(ctx,name,...args)=>original.draw(ctx,resolve(name),...args);
  const offer=G.LevelUp.offer;
  G.LevelUp.offer=(owner,...args)=>offer(owner,...args).map(card=>{
    if(card.key==='new:'+moveId)return {...card,icon:key(1)};
    if(card.key==='up:'+moveId)return {...card,icon:key((owner.moves.find(move=>move.id===moveId)?.lvl||1)+1)};
    return card;
  });
  G.SharinganIcons={key,forMove};
})();
