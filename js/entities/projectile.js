/* ============ projectile.js — proyectiles y orbes ============
 * Una sola lista para todo lo que vuela: disparos del jugador, disparos
 * enemigos y los orbes que giran alrededor del Pokémon (los orbes son
 * proyectiles con `orb`, anclados al jugador y que vuelven a golpear cada
 * `rehit` segundos).
 *
 * Viven en el plano del SUELO (como los pies de las entidades) y se dibujan
 * elevados G.LIFT unidades con su sombra debajo. Las paredes y los objetos
 * sólidos los paran (ver combat.js).
 */
G.Projectiles = (() => {
  let list = [];
  let nextId = 1;

  function clear() { list = []; }
  function all() { return list; }

  /** Proyectil del jugador. */
  function spawn(o) {
    const p = Object.assign({
      id: nextId++, x: 0, y: 0, vx: 0, vy: 0,
      dmg: 10, r: 6, life: 1.4, t: 0,
      pierce: 0, hits: null, friendly: true,
      color: '#fff', homing: 0, slow: 0, burn: 0, poison: 0, knock: 0,
      orb: false, rehit: 0.34, hitLog: null, phits: null
    }, o);
    if (p.friendly && !p.orb && !p.phits) p.phits = new Set();
    if(p.friendly&&!p.orb&&!p.ghost&&!p.digiBomb&&!p.fireballAOE)
      p.toolBounce=G.NinjaToolBounce?.create(p.owner,p.mid);
    list.push(p);
    return p;
  }

  /** Orbe anclado a un jugador (`owner`): vive mientras el movimiento esté activo. */
  function spawnOrb(o) {
    return spawn(Object.assign({
      orb: true, life: Infinity, pierce: Infinity, hitLog: new Map()
    }, o));
  }

  /** Borra los orbes de un jugador (o todos) al cambiar de movimiento activo. */
  function clearOrbs(owner) { list = list.filter(p => !p.orb || (owner && p.owner !== owner)); }

  function update(dt, player, enemies) {
    for (let i = list.length - 1; i >= 0; i--) {
      const p = list[i];
      if(p.toolBounce&&p.toolBounce.world!==G.World){list.splice(i,1);continue;}
      p.t += dt;
      if(p.fireballAOE&&(!p.owner||(p.owner!==player&&!G.SelfClones?.isActor(p.owner))||p.owner.dead||p.owner.hp<=0)){list.splice(i,1);continue;}
      if(p.fumaReturn&&(!p.owner||(p.owner!==player&&!G.SelfClones?.isActor(p.owner))||p.owner.dead||p.owner.hp<=0||(p.fumaLearned&&!p.owner.hasMove('naruto-fuma-shuriken')))) { list.splice(i,1);continue; }

      if (p.orb) {
        // Gira alrededor de su jugador.
        const o = p.owner || player;
        p.oa += p.ospeed * dt;
        p.x = o.x + Math.cos(p.oa) * p.orad;
        p.y = o.y + Math.sin(p.oa) * p.orad * 0.7;
        continue;
      }

      if (p.t >= p.life) { list.splice(i, 1); continue; }

      // Fuma's outward arc ends at a launch-time target snapshot, never an infinite chase.
      let moveDt=dt;
      if(p.fumaCurve) {
        p.px=p.x;p.py=p.y;p.fumaSweep=[[p.x,p.y]];
        if(!p.back) {
          const c=p.fumaCurve,start=Math.min(c.duration,p.t-dt),end=Math.min(c.duration,p.boom,p.t);
          const steps=Math.max(1,Math.ceil(Math.max(0,end-start)*120));
          for(let n=1;n<=steps;n++) {
            const t=Math.max(0,Math.min(1,(start+(end-start)*n/steps)/c.duration)),u=1-t;
            p.x=u*u*c.sx+2*u*t*c.cx+t*t*c.tx;p.y=u*u*c.sy+2*u*t*c.cy+t*t*c.ty;
            p.fumaSweep.push([p.x,p.y]);
            p.vx=2*(u*(c.cx-c.sx)+t*(c.tx-c.cx))/c.duration;
            p.vy=2*(u*(c.cy-c.sy)+t*(c.ty-c.cy))/c.duration;
          }
          moveDt=Math.max(0,p.t-Math.max(p.t-dt,p.boom));
        }
      }

      // Bumerán: a los `boom` segundos se da la vuelta (y puede volver a
      // golpear a los mismos) y vuelve a su dueño; al llegar, desaparece.
      if (p.boom) {
        const o = p.owner || player;
        if (!p.back && p.t >= p.boom) {
          p.back = true; p.hits = new Set();
          if(p.fumaReturn) { p.returnAt=p.t;p.pierce=p.fumaPierce;p.fumaSpent=false;p.phits=new Set(); }
        }
        if (p.back) {
          let [dx, dy] = G.U.norm(o.x - p.x, o.y - p.y);
          if(p.fumaReturn) {
            const bend=.85*Math.max(0,1-(p.t-p.returnAt)/.4),angle=Math.atan2(dy,dx)+bend;
            dx=Math.cos(angle);dy=Math.sin(angle);
          }
          p.vx = G.U.damp(p.vx, dx * p.bsp, 7, dt);
          p.vy = G.U.damp(p.vy, dy * p.bsp, 7, dt);
          if (G.U.dist2(p.x, p.y, o.x, o.y) < (o.r + 8) ** 2) { list.splice(i, 1); continue; }
        }
      }

      // Teledirigido: curva la velocidad hacia el enemigo más cercano.
      G.NinjaToolBounce?.aimProjectile(p);
      if (p.homing > 0 && p.friendly && !p.ninjaToolTarget) {
        const tg = nearest(enemies, p.x, p.y, 340);
        if (tg) {
          const [dx, dy] = G.U.norm(tg.x - p.x, tg.cy() - p.y);
          const sp = Math.hypot(p.vx, p.vy);
          p.vx = G.U.damp(p.vx, dx * sp, p.homing, dt);
          p.vy = G.U.damp(p.vy, dy * sp, p.homing, dt);
        }
      }

      if(!p.fumaCurve) { p.px = p.x; p.py = p.y; } // para la colisión barrida (ver combat.js)
      if (p.vis && p.vis.trail && G.Camera.sees(p.x, p.y, 20)) {
        p.trailT = (p.trailT || 0) - dt;
        if (p.trailT <= 0) { p.trailT = 0.04; G.FX.trail(p.vis.trail, p.vis.pal, p.x, p.y - G.LIFT, p.vx, p.vy); }
      }
      if(p.fireballAOE) {
        const f=p.fireballAOE;
        if(!f.blocked) {
          const dx=p.vx*moveDt,dy=p.vy*moveDt,length=Math.hypot(dx,dy),steps=Math.max(1,Math.ceil(length/4)),sx=p.x,sy=p.y;
          for(let n=1;n<=steps;n++) {
            const fraction=n/steps,x=sx+dx*fraction,y=sy+dy*fraction,g=p.fireballGrowth;
            const ratio=g?g.startRatio+(g.endRatio-g.startRatio)*Math.min(1,(g.travelled+length*fraction)/g.distance):1;
            const radius=g?g.baseRadius*ratio:p.r,block=G.World.projectileBlock(x,y,radius);
            if(block){f.blocked=true;f.blockedProp=typeof block==='object'?block:null;p.vx=p.vy=0;break;}
            p.x=x;p.y=y;
          }
        }
      } else {
        p.x += p.vx * moveDt;
        p.y += p.vy * moveDt;
      }
      if(p.fumaSweep)p.fumaSweep.push([p.x,p.y]);
      if(p.fireballGrowth) {
        const g=p.fireballGrowth;
        g.travelled+=Math.hypot(p.x-p.px,p.y-p.py);
        const ratio=g.startRatio+(g.endRatio-g.startRatio)*Math.min(1,g.travelled/g.distance);
        p.r=g.baseRadius*ratio;
        p.vis.projScale=g.baseScale*ratio;
      }

      // Fuera de la vista con margen generoso -> se descarta.
      if (!p.fireballAOE && !G.Camera.sees(p.x, p.y, 260)) { list.splice(i, 1); continue; }
    }
  }

  function nearest(enemies, x, y, maxDist) {
    let best = null, bd = maxDist * maxDist;
    for (const e of enemies) {
      if (e.dead) continue;
      const d = G.U.dist2(x, y, e.x, e.cy());
      if (d < bd) { bd = d; best = e; }
    }
    return best;
  }

  function remove(p) {
    const i = list.indexOf(p);
    if (i >= 0) list.splice(i, 1);
  }

  function draw(ctx) {
    const L = G.LIFT;
    // Sombras primero, todas juntas.
    ctx.fillStyle = 'rgba(0,0,0,.25)';
    for (const p of list) {
      ctx.beginPath(); ctx.ellipse(p.x, p.y, p.r * 0.9, p.r * 0.38, 0, 0, 6.2832); ctx.fill();
    }
    // Los disparos enemigos llevan un aro rojo en el suelo: "esto te hace daño".
    ctx.fillStyle = 'rgba(255,60,80,.35)';
    for (const p of list) {
      if (p.friendly) continue;
      ctx.beginPath(); ctx.ellipse(p.x, p.y, p.r * 1.5, p.r * 0.6, 0, 0, 6.2832); ctx.fill();
    }
    for (const p of list) {
      if (p.temariReflected && G.TemariCycloneVFX?.drawReflection) continue;
      if (G.NarutoRasenshurikenVFX?.drawProjectile(ctx, p)) continue;
      const v = p.vis || G.VFX.forType('normal');
      const shape = v.proj;
      const a = p.orb ? 1 : Math.min(1, (p.life - p.t) * 4);
      let angle = 0;
      if (G.VFX.isDir(shape)) angle = p.orb ? p.oa + Math.PI / 2 : Math.atan2(p.vy, p.vx);
      else if (G.VFX.spins(shape)) angle = p.t * 9;
      G.VFX.draw(ctx, shape, v.pal, p.x, p.y - L, {
        angle, alpha: a, scale: v.projScale || (p.r >= 8 ? 1.5 : 1),
        frame: Math.floor(p.t * 12)
      });
    }
  }

  return { clear, all, spawn, spawnOrb, clearOrbs, update, remove, draw, nearest,
           get count() { return list.length; } };
})();
