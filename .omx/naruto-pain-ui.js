/* Cached pixel emblems and screen-space Six Paths status. */
(() => {
  if (G.PainUI) return;
  const paths = ['tendo', 'asura', 'animal', 'human', 'preta', 'naraka'];
  const names = ['你', '修羅', '畜生', '人間', '餓鬼', '地獄'];
  const palette = { k:'#171421', p:'#bca0e7', s:'#69627d', w:'#ece4fa', o:'#f49a59', r:'#c85c7d', b:'#81d6e0' };
  function emblem(paint) {
    const rows = Array.from({length:16}, () => Array(16).fill('.'));
    const pixel = (x,y,c) => { if(x>=0&&x<16&&y>=0&&y<16) rows[y][x]=c; };
    const rect = (x,y,w,h,c) => { for(let j=y;j<y+h;j++)for(let i=x;i<x+w;i++)pixel(i,j,c); };
    const ring = (x,y,r,c) => { for(let j=0;j<16;j++)for(let i=0;i<16;i++)if(Math.abs(Math.hypot(i-x,j-y)-r)<.6)pixel(i,j,c); };
    paint(pixel,rect,ring);
    return {pal:palette,rows:rows.map(row=>row.join(''))};
  }
  const icons = {
    painRod: emblem((p,r,c) => { c(8,8,7,'p');r(6,2,3,12,'k');r(9,2,1,12,'s');r(4,5,8,2,'k');r(5,5,6,1,'w');r(7,1,2,2,'s'); }),
    painGravity: emblem((p,r,c) => { c(7.5,7.5,7,'p');c(7.5,7.5,4.5,'s');c(7.5,7.5,2,'w');r(7,6,2,4,'k');r(6,7,4,2,'k');r(0,7,3,2,'p');r(13,7,3,2,'p');r(7,0,2,3,'p');r(7,13,2,3,'p'); }),
    painMissile: emblem((p,r) => { for(const [x,y]of [[1,5],[6,1],[11,5]]){r(x,y+2,4,6,'k');r(x+1,y+1,2,6,'w');r(x+1,y,2,2,'s');r(x+1,y+8,2,3,'o');r(x,y+9,1,2,'r');} }),
    painSummon: emblem((p,r,c) => { c(7.5,8,7,'p');r(3,6,9,6,'s');r(9,5,4,7,'w');r(4,4,2,3,'k');r(2,10,2,4,'k');r(9,11,2,3,'k');p(12,6,'r');r(13,7,2,2,'w');p(14,6,'w');p(15,5,'w'); }),
    painSoul: emblem((p,r,c) => { c(7.5,5,3,'b');r(5,7,6,3,'b');r(6,10,4,2,'b');r(7,12,2,2,'p');p(8,14,'p');r(6,4,1,2,'k');r(9,4,1,2,'k');r(1,10,3,4,'o');r(3,9,2,3,'o');r(11,9,2,3,'o');r(12,10,3,4,'o'); }),
    painAbsorb: emblem((p,r,c) => { c(7.5,7.5,7,'b');c(7.5,7.5,4,'p');r(6,4,4,8,'w');r(5,7,1,4,'w');r(10,6,1,5,'w');r(3,7,2,2,'p');r(11,7,2,2,'p');r(7,7,2,3,'s'); }),
    painRepair: emblem((p,r,c) => { r(3,3,10,11,'p');r(4,4,8,9,'s');r(1,1,3,5,'w');r(12,1,3,5,'w');r(5,5,2,2,'r');r(9,5,2,2,'r');r(6,9,4,4,'k');r(7,8,2,6,'b');r(5,10,6,2,'b'); }),
    painPlanet: emblem((p,r,c) => { c(7.5,7.5,7,'p');c(7.5,7.5,4.5,'s');r(5,4,6,8,'k');r(4,6,8,4,'k');r(6,3,4,2,'w');r(1,2,3,2,'s');r(12,11,3,3,'s');r(2,12,2,2,'w');r(12,2,2,2,'w'); })
  };
  Object.assign(G.Icons.UI, icons);
  const cooldown = (owner, state, kind) => {
    if(kind==='repair'){
      const rescue=G.NarutoPain?.playerReviveState?.(owner);
      if(rescue?.waiting)return rescue.status==='unsafe'?'找位置':rescue.remaining.toFixed(1)+'s';
      if(!owner.moves?.some(move=>move.id==='naruto-pain-repair'))return '救援待命';
    }
    if (!owner.moves?.some(move => move.id === 'naruto-pain-' + kind)) return '未習得';
    const seconds = state[kind + 'Cooldown'];
    return seconds > 0 ? Math.ceil(seconds) + 's' : '就緒';
  };
  function layout(w,h,owner) {
    const groups = (owner.slots?.length||0)+(owner.moves||[]).filter(move=>move.passive&&!owner.slots?.some(group=>group.includes(move))).length;
    const controls = G.Touch?.active ? G.Touch.controlLayout(w,h,Math.max(1,groups)) : null;
    const portrait = !!controls?.portrait;
    const safeTop = portrait ? Math.min(44,G.Touch.safeArea().top) : 0;
    return {x:12,y:portrait?180+safeTop:124,width:198,height:87};
  }
  function draw(ctx,w,h,owner) {
    if (owner?.mon?.dex !== 30010 || owner !== G.Game.player) return;
    const state = G.NarutoPain?.snapshot(owner);
    if (!state) return;
    const actors = G.NarutoPain.actorsFor?.(owner) || state.bodies || [];
    const box = layout(w,h,owner);
    ctx.save();
    G.HUD.roundRect(ctx,box.x,box.y,box.width,box.height,7);
    ctx.fillStyle='rgba(17,13,29,.85)';ctx.fill();
    ctx.font='700 10px "Segoe UI",system-ui,sans-serif';ctx.textBaseline='top';ctx.textAlign='left';
    ctx.fillStyle='#d2b9ef';
    ctx.fillText('六道自動作戰',box.x+7,box.y+5,box.width-14);
    paths.forEach((path,index) => {
      const actor = index === 0 ? owner : actors.find(body=>body.path===path);
      const dead = !actor || actor.dead || actor.hp<=0;
      const x=box.x+6+index*31,y=box.y+20;
      ctx.fillStyle=dead?'#302638':'#433651';ctx.fillRect(x,y,29,30);
      ctx.save();ctx.globalAlpha=dead?.35:1;
      G.PainArt?.portrait(ctx,{path,x:x+1,y:y+1,width:27,height:27});ctx.restore();
      if(index===0){ctx.strokeStyle='#ffd778';ctx.lineWidth=1;ctx.strokeRect(x+.5,y+.5,28,29);}
      ctx.fillStyle='#15111e';ctx.fillRect(x,y+30,29,3);
      ctx.fillStyle=dead?'#a28aa9':'#b498df';
      const health=actor?.maxHp>0?Math.max(0,Math.min(1,actor.hp/actor.maxHp)):0;
      ctx.fillRect(x,y+30,29*health,3);
      ctx.textAlign='center';ctx.fillStyle=dead?'#b8a4bb':'#e9def5';
      const revive=actor?.reviveRemaining;
      const caption=dead&&revive>0?Math.ceil(revive)+'s':actor?.formed===false?'待命':actor?.protectionRemaining>0?'整備':actor?.recovering?'恢復':actor?.retreating?'撤退':names[index];
      ctx.fillText(caption,x+14.5,y+36,29);
    });
    ctx.textAlign='left';ctx.fillStyle='#a8dce1';
    ctx.fillText('吸收 '+cooldown(owner,state,'absorb'),box.x+7,box.y+72,88);
    ctx.fillStyle='#c9b4e8';ctx.fillText('修復 '+cooldown(owner,state,'repair'),box.x+102,box.y+72,90);
    const rescue=G.NarutoPain?.playerReviveState?.(owner);
    if(rescue?.waiting){
      const width=Math.min(w-32,304),x=(w-width)/2,y=Math.min(h-180,h*.59);
      G.HUD.roundRect(ctx,x,y,width,64,8);ctx.fillStyle='rgba(17,13,29,.92)';ctx.fill();
      ctx.textAlign='center';ctx.fillStyle='#eedbff';ctx.font='700 14px "Segoe UI",system-ui,sans-serif';
      ctx.fillText('天道倒下，等待地獄道修復',w/2,y+12,width-20);
      ctx.fillStyle='#d3c4df';ctx.font='12px "Segoe UI",system-ui,sans-serif';
      const label=rescue.status==='unsafe'?'正在尋找安全復活位置':rescue.status==='repair'?'閻王修復中':`約 ${rescue.remaining.toFixed(1)} 秒後復活`;
      ctx.fillText(label,w/2,y+36,width-20);
    }
    ctx.restore();
  }
  const originalDraw=G.HUD.draw;
  G.HUD.draw=function(ctx,w,h,owner,stats) {
    originalDraw.call(this,ctx,w,h,owner,stats);
    draw(ctx,w,h,owner);
  };
  function skillState(owner,move) {
    const state=G.NarutoPain?.stateFor(owner),kind=move.id==='naruto-pain'?'basic':move.id.slice('naruto-pain-'.length);
    if(owner.dead&&['basic','gravity','planet'].includes(kind))return {remaining:0,duration:1,label:'倒下'};
    const path={missiles:'asura',summon:'animal',soul:'human',absorb:'preta',repair:'naraka'}[kind];
    const actor=path&&state?.bodies.find(body=>body.path===path);
    if(path&&(!actor||actor.dead||actor.hp<=0))return {remaining:0,duration:1,label:'倒下'};
    if(actor?.formed===false)return {remaining:0,duration:1,label:'找位置'};
    if(actor?.protectionRemaining>0)return {remaining:actor.protectionRemaining,duration:G.NarutoPain.survivalConfig.protectionSeconds,label:'整備中'};
    if(kind==='soul'&&actor?.retreating)return {remaining:0,duration:1,label:actor.recovering?'恢復中':'撤退中'};
    const duration=Math.max(.05,(kind==='absorb'?move.absorbCooldown:kind==='repair'?move.repairCooldown:move.cd)*(owner.cdMul||1));
    const remaining=Math.max(0,kind==='basic'?state?.basicCooldown||0:kind==='absorb'?state?.absorbCooldown||0:kind==='repair'?state?.repairCooldown||0:kind==='gravity'?Math.max(move.t||0,state?.sharedRecovery||0):move.t||0);
    const action=G.NarutoPain?.actionsFor(owner).find(action=>action.kind===kind);
    const label=kind==='repair'&&state?.repair?'修復中':action?(action.phase==='approach'?'接近中':'施放中'):remaining>0?remaining.toFixed(1)+'s':kind==='repair'?'待命':'就緒';
    return {remaining,duration,label};
  }
  G.PainUI={draw,layout,icons,skillState};
})();
