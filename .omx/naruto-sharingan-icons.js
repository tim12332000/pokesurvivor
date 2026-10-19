/* Native pixel eye emblems: cached by evolution stage, resolved at draw time. */
(() => {
  if(G.SharinganIcons)return;
  const moveId='naruto-sharingan';
  const key=level=>'sharingan-'+Math.max(1,Math.min(5,Math.floor(level)||1));
  function eye(level){
    const rows=Array.from({length:16},()=>Array(16).fill('.'));
    const set=(x,y,color)=>{if(rows[y]?.[x]!==undefined)rows[y][x]=color;};
    for(let y=3;y<=12;y++)for(let x=0;x<16;x++){
      const dx=x-7.5,dy=y-7.5,lid=Math.abs(dx)/7.5+dy*dy/14;
      if(lid>1.12)continue;
      const radius=Math.hypot(dx,dy);
      let color=lid>.8?'k':'w';
      if(radius<4.2)color='k';
      if(radius<3.6)color=dy>1?'d':'r';
      if(radius<1)color='k';
      if(level===4&&radius>1&&radius<3.5&&Math.sin(Math.atan2(dy,dx)*3+radius*.65)>.2)color='k';
      if(level===5&&radius>1&&radius<3.5&&Math.cos(Math.atan2(dy,dx)*6)>.05)color='k';
      set(x,y,color);
    }
    if(level<=3)for(let n=0;n<level;n++){
      const angle=-Math.PI/2+n*Math.PI*2/level;
      const x=Math.round(7.5+Math.cos(angle)*2.6),y=Math.round(7.5+Math.sin(angle)*2.6);
      set(x,y,'k');set(x-Math.round(Math.sin(angle)),y+Math.round(Math.cos(angle)),'k');
    }
    // A violet rim distinguishes Susanoo while keeping an eye, rather than an armor glyph.
    if(level===5){set(3,4,'p');set(4,3,'p');set(11,3,'p');set(12,4,'p');set(5,12,'p');set(10,12,'p');}
    return {pal:{k:'#130c19',w:'#f7e1df',r:'#ee293f',d:'#a90f2c',p:'#b282ef'},rows:rows.map(row=>row.join(''))};
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
