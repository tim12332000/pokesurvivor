/* Run-local additive ricochets for physical, single-hit ninja tools. */
(() => {
  if (G.NinjaToolBounce) return;
  const range = 160;
  const tools = new Set(['naruto-pain','naruto-kunai','naruto-shuriken','naruto-fuma-shuriken',
    'naruto-tenten','naruto-tenten-fuma','naruto-tenten-twin','naruto-kimimaro-bullets']);
  const alive = e => !!e && !e.dead && e.hp > 0 && !e.friendly;
  const count = owner => Math.max(0, Math.floor(owner?.ninjaToolBouncePicks || 0));
  const eligibleMove = id => tools.has(id);
  const eligible = owner => !!owner?.moves?.some(m => eligibleMove(m.id));
  function create(owner, id, picks = count(owner)) {
    return eligibleMove(id) && picks > 0 ? { remaining:picks, seen:new Set(), range, chaining:false, world:G.World } : null;
  }
  function nearest(origin, seen, radius = range) {
    return [...new Set(G.EnemyMgr.queryCircle(origin.x,origin.y,radius))]
      .filter(e => alive(e) && !seen.has(e) && Math.hypot(e.x-origin.x,e.y-origin.y)<=radius)
      .sort((a,b) => (a.x-origin.x)**2+(a.y-origin.y)**2-(b.x-origin.x)**2-(b.y-origin.y)**2)
      .find(e => G.World.projectilePathClear(origin.x,origin.y,e.x,e.y));
  }
  function finishProjectile(p) {
    const state=p.toolBounce;if(!state?.chaining)return;
    state.chaining=false;p.ninjaToolTarget=null;
    if(p.fumaReturn) {
      p.back=!!state.returning;p.boom=p.t||Number.EPSILON;
      if(state.returning)p.returnAt=p.t-(state.returnElapsed||0);
      p.life=p.t+Math.hypot(p.x-p.owner.x,p.y-p.owner.y)/(p.bsp||Math.hypot(p.vx,p.vy)||1)+.5;
    }
  }
  function redirectProjectile(p, victim) {
    const state=p.toolBounce;if(!state)return false;
    state.seen.add(victim);
    const target=state.remaining>0&&!p.owner?.dead?nearest(victim,state.seen,state.range):null;
    if(!target){finishProjectile(p);return false;}
    if(!state.chaining){state.returning=!!p.back;state.returnElapsed=Math.max(0,p.t-(p.returnAt||0));}
    state.remaining--;state.chaining=true;p.ninjaToolTarget=target;
    const speed=Math.hypot(p.vx,p.vy)||1,angle=Math.atan2(target.y-victim.y,target.x-victim.x);
    p.x=p.px=victim.x;p.y=p.py=victim.y;p.vx=Math.cos(angle)*speed;p.vy=Math.sin(angle)*speed;
    p.t=0;p.life=state.range/speed+.2;
    if(p.fumaReturn){p.fumaCurve=null;p.fumaSweep=null;p.back=false;p.boom=Infinity;p.fumaSpent=false;}
    return true;
  }
  function aimProjectile(p) {
    const state=p.toolBounce;if(!state?.chaining)return;
    if(!alive(p.ninjaToolTarget))p.ninjaToolTarget=nearest(p,state.seen,state.range);
    const target=p.ninjaToolTarget;
    if(!target){finishProjectile(p);return;}
    const speed=Math.hypot(p.vx,p.vy),angle=Math.atan2(target.y-p.y,target.x-p.x);
    p.vx=Math.cos(angle)*speed;p.vy=Math.sin(angle)*speed;
  }
  function redirectRod(p, victim) {
    const state=p.toolBounce;if(!state)return false;
    state.seen.add(victim);
    const target=state.remaining>0&&!p.owner.dead?nearest(victim,state.seen,state.range):null;
    if(!target)return false;
    state.remaining--;state.chaining=true;p.ninjaToolTarget=target;
    p.x=victim.x;p.y=victim.y;p.angle=Math.atan2(target.y-p.y,target.x-p.x);p.distance=0;p.range=state.range;
    return true;
  }
  function aimRod(p) {
    const state=p.toolBounce;if(!state?.chaining)return;
    if(!alive(p.ninjaToolTarget))p.ninjaToolTarget=nearest(p,state.seen,Math.max(0,p.range-p.distance));
    if(p.ninjaToolTarget)p.angle=Math.atan2(p.ninjaToolTarget.y-p.y,p.ninjaToolTarget.x-p.x);
  }
  G.NinjaToolBounce={count,eligibleMove,eligible,create,nearest,redirectProjectile,aimProjectile,redirectRod,aimRod,range};
  G.LevelUp.STATS.push({id:'ninjaToolBounce',icon:'tentenBounce',title:'忍具連彈 +1',eligible,
    desc:'單體忍具額外連彈 +1 次，可與原有次數累加、重複選取。彈向附近未命中的敵人，牆會阻擋。一般每跳距離 160，專屬技能沿用原距離；爆炸與範圍傷害不適用。',
    apply:owner=>{owner.ninjaToolBouncePicks=count(owner)+1;}});
})();
