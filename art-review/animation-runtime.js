/* Lab presentation only: candidate bodies observe the existing combat simulation. */
(() => {
  'use strict';
  const installed = new WeakSet();
  const skillCoverage = Object.freeze({
    'naruto-shadow-clones': 'candidate seals; real clone actors',
    'naruto-naruto': 'candidate Rasengan phases',
    'naruto-rasenshuriken': 'redrawn throw sequence; four-blade projectile',
    'naruto-nine-tails-cloak': 'redrawn activation and dedicated transformed action set',
    'naruto-sasuke': 'candidate Chidori phases',
    'naruto-fireball': 'candidate seals and breath; original mouth projectile',
    'naruto-fuma-shuriken': 'redrawn throw sequence; hand-released weapon',
    'naruto-kusanagi': 'redrawn draw/slash/recovery sequence; straight blade orbit',
    'naruto-sharingan': 'redrawn seal sequence; five-tier eye effects',
    'naruto-kunai': 'redrawn throw sequence',
    'naruto-shuriken': 'redrawn throw sequence',
    'naruto-lee': 'redrawn sweeping roundhouse; close-range AOE',
    'naruto-lotus': 'redrawn step-in, rising kick, airborne drive and landing',
    'naruto-gates': 'learned five-stage passive; dedicated red-skin action set and green aura',
    'naruto-reverse-lotus': 'redrawn committed aerial taijutsu combo and finisher'
  });
  function install(G, { enabled = () => true } = {}) {
    if (installed.has(G)) return G.AnimationLab;
    installed.add(G);
    const assets = window.AnimationAssets;
    const states = new Map();
    const counters = { candidate: 0, source: 0, byState: {}, bySkill: {} };
    let world = G.World, owner = G.Game.player, drawingAir = false;
    const heroes={30001:'naruto',30002:'sasuke',30006:'lee'};
    const supported = anim => Object.hasOwn(heroes,anim?.dex);
    const hero = anim => heroes[anim.dex];
    const direction = anim => ['down', 'right', 'right', 'right', 'up', 'left', 'left', 'left'][((anim.dir || 0) % 8 + 8) % 8];
    const row = dir => ({ down: 0, up: 1, left: 2, right: 3 })[dir];
    function actor(anim) {
      if (G.Game.player?.anim === anim) return G.Game.player;
      return G.NarutoClones?.actors.find(a => a.anim === anim) || null;
    }
    function entry(anim) {
      if (!states.has(anim)) states.set(anim, { age: 0, hurtAge: Infinity, deathAge: null, cast: null, sharingan: 0, gates: 0, kusanagi: false });
      return states.get(anim);
    }
    function clear() { states.clear(); }
    function sync() {
      if (world !== G.World || owner !== G.Game.player) { clear(); world = G.World; owner = G.Game.player; }
    }
    function record(pl, move, duration) {
      if (!supported(pl?.anim) || pl.dead || !(pl.hp > 0)) return;
      const state = entry(pl.anim), id = move?.id || 'weapon';
      // Chidori calls Player.cast again for every dash. Its live state owns its pose.
      if (state.cast?.id === id && state.cast.age < .07) return;
      const charge = Math.max(0, move?.charge || 0);
      state.cast = { id, age: 0, charge, duration: duration || Math.max(.32, charge + .22), aim: pl.aim || 0 };
    }
    const playerCast = G.Player.prototype.cast;
    G.Player.prototype.cast = function(move) {
      const result = playerCast.apply(this, arguments);
      if (move?.kind !== 'trail') record(this, move);
      return result;
    };
    // These entry points include auto-casts whose implementation is lexical and
    // passive transitions that never invoke the exported DigimonSkills.cast.
    for (const [api, method, id, duration] of [
      [G.NarutoClones, 'beginCast', 'naruto-shadow-clones', .62],
      [G.NarutoChidori, 'cast', 'naruto-sasuke', .38],
      [G.NarutoFireball, 'cast', 'naruto-fireball', .68],
      [G.NarutoLee, 'cast', null, 1.8],
      [G.NarutoSupport, 'cast', null, .5]
    ]) {
      if (!api?.[method]) continue;
      const original = api[method];
      api[method] = function(pl, move) {
        const result = original.apply(this, arguments);
        if (result) record(pl, id ? { ...move, id } : move, duration);
        else if (supported(pl?.anim) && entry(pl.anim).cast?.id === move?.id) entry(pl.anim).cast = null;
        return result;
      };
    }
    const hurt = G.Player.prototype.hurt;
    G.Player.prototype.hurt = function() {
      const hp = this.hp, result = hurt.apply(this, arguments);
      if (supported(this.anim) && this.hp < hp) {
        const state = entry(this.anim);
        state.hurtAge = 0;
        if (this.dead || this.hp <= 0) { state.deathAge = 0; state.cast = null; }
      }
      return result;
    };
    const animatorUpdate = G.Sprites.Animator.prototype.update;
    G.Sprites.Animator.prototype.update = function(dt) {
      const result = animatorUpdate.apply(this, arguments);
      if (!supported(this) || !(dt > 0) || !Number.isFinite(dt) || G.Game.state === 'paused') return result;
      sync();
      const state = entry(this), pl = actor(this);
      state.age += dt; state.hurtAge += dt;
      if (pl?.dead || pl?.hp <= 0 || this.cur === 'Faint') state.deathAge = (state.deathAge ?? 0) + dt;
      else state.deathAge = null;
      if (state.cast) { state.cast.age += dt; if (state.cast.age > state.cast.duration) state.cast = null; }
      return result;
    };
    const updateFields = G.Combat.updateFields;
    G.Combat.updateFields = function(dt) {
      sync();
      const result = updateFields.apply(this, arguments);
      const pl = G.Game.player;
      if (supported(pl?.anim) && !pl.dead && pl.hp > 0) {
        const state = entry(pl.anim), level = G.NarutoSharingan?.stage(pl) || 0;
        const gates = G.NarutoGates?.stage(pl) || 0;
        const sword = !!G.NarutoKusanagi?.active(pl);
        // Passive synchronization may run immediately after a scene clear or
        // accepted attack. It must never replace that attack's presentation.
        if (!state.cast && level !== state.sharingan && level) record(pl, { id: 'naruto-sharingan' }, .62);
        if (!state.cast && gates !== state.gates && gates) record(pl, { id: 'naruto-gates' }, .5);
        if (!state.cast && sword && !state.kusanagi) record(pl, { id: 'naruto-kusanagi' }, .48);
        state.sharingan = level; state.gates = gates; state.kusanagi = sword;
      }
      for (const [anim] of states) if (anim !== pl?.anim && !G.NarutoClones?.actors.some(a => a.anim === anim)) states.delete(anim);
      return result;
    };
    const clearFields = G.Combat.clearFields;
    G.Combat.clearFields = function(pl) {
      const result = clearFields.apply(this, arguments);
      // A dying player's candidate corpse stays owned until its scene ends.
      if (!pl) clear(); else if (!pl.dead) states.delete(pl.anim);
      return result;
    };
    const setActive = G.Player.prototype.setActive;
    G.Player.prototype.setActive = function() {
      const result = setActive.apply(this, arguments);
      const cast = states.get(this.anim)?.cast;
      if (cast && !this.activeGroup().some(m => m.id === cast.id)) entry(this.anim).cast = null;
      return result;
    };
    function baseStateFor(anim) {
      sync();
      const state = entry(anim), pl = actor(anim), name = hero(anim), dir = direction(anim);
      const base = { state: 'idle', phase: 'loop', direction: dir, key: name + '-idle', frame: row(dir) * 4 + Math.floor(state.age * 5) % 4, age: state.age, treatment: 'candidate', mirror: false, rotation: 0 };
      if (state.deathAge !== null || pl?.dead || pl?.hp <= 0 || anim.cur === 'Faint') {
        const age = state.deathAge ?? 0;
        return { ...base, state: 'death', phase: age >= .8 ? 'hold' : 'collapse', key: name + '-death', frame: Math.min(3, Math.floor(age * 5)), mirror: dir === 'left', age };
      }
      const chidori = G.NarutoChidori?.active;
      if (chidori?.owner?.anim === anim) {
        const progress = 1 - chidori.wait / Math.max(.001, chidori.move.charge || .09);
        return { ...base, state: 'skill', id: 'naruto-sasuke', phase: chidori.phase, key: 'sasuke-chidori', frame: chidori.phase === 'charge' ? Math.min(1, Math.max(0, Math.floor(progress * 2))) : chidori.phase === 'return' ? 3 : 2, mirror: Math.cos(pl.aim) < 0 };
      }
      const fire = G.NarutoFireball?.active;
      if (fire?.owner?.anim === anim) return { ...base, state: 'skill', id: 'naruto-fireball', phase: fire.phase, key: 'sasuke-fireball', frame: fire.phase === 'seal' ? Math.min(1, Math.floor(fire.t / .24 * 2)) : fire.phase === 'recovery' ? 3 : 2, mirror: Math.cos(fire.aim) < 0 };
      const lee=G.NarutoLee?.active;
      if(lee?.owner?.anim===anim){
        const reverse=lee.kind==='lee-reverse-lotus';
        if(lee.phase==='approach')return {...base,state:'skill',id:lee.move.id,phase:lee.phase,key:'lee-movement',frame:row(dir)*4+Math.floor(state.age*12)%4};
        const frame=lee.phase==='windup'?0:lee.phase==='lift'?(lee.phaseAge<.12?1:2):lee.phase==='combo'?1+Math.floor(lee.phaseAge*18)%2:lee.phase==='descent'?2:3;
        return {...base,state:'skill',id:lee.move.id,phase:lee.phase,key:reverse?'lee-reverse':'lee-lotus',frame,mirror:Math.cos(pl.aim)<0,visualLift:lee.visualLift||0};
      }
      if (state.hurtAge < .3) return { ...base, state: 'hurt', phase: 'recoil', key: name + '-hurt', frame: row(dir) * 4 + Math.min(3, Math.floor(state.hurtAge / .3 * 4)), age: state.hurtAge };
      let cast = state.cast;
      if (!cast && pl?.comboT > 0) cast = { id: pl.mimickedId || 'naruto-kunai', age: .4 - pl.comboT, duration: .4, charge: .12, aim: pl.comboAim || 0 };
      if (!cast && pl?.owner && anim.busy() && ['Shoot', 'Attack', 'Charge'].includes(anim.cur)) {
        const progress = Math.max(0, Math.min(1, anim.progress()));
        cast = { id: pl.mimickedId || 'naruto-kunai', age: progress * .36, duration: .36, charge: .08, aim: pl.target ? Math.atan2(pl.target.y - pl.y, pl.target.x - pl.x) : 0 };
      }
      if (cast) {
        const phase = cast.age < cast.charge ? 'windup' : cast.age < cast.charge + .09 ? 'release' : 'recovery';
        const action = { ...base, state: 'skill', phase, id: cast.id, age: cast.age, treatment: 'redrawn', aim: cast.aim, mirror: Math.cos(cast.aim) < 0 };
        if (cast.id === 'naruto-shadow-clones') return { ...action, phase: cast.age < .4 ? 'seal' : 'recovery', key: 'naruto-clones', frame: cast.age < .4 ? Math.min(2, Math.floor(cast.age / .4 * 3)) : 3 };
        if (cast.id === 'naruto-sasuke') return { ...action, key: 'sasuke-chidori', frame: 3, phase: 'recovery' };
        if (cast.id === 'naruto-fireball') return { ...action, key: 'sasuke-fireball', frame: 3, phase: 'recovery' };
        if (cast.id === 'naruto-naruto') return { ...action, key: 'naruto-rasengan', frame: phase === 'windup' ? Math.min(1, Math.floor(cast.age / Math.max(.01, cast.charge) * 2)) : phase === 'release' ? 2 : 3 };
        if (cast.id === 'naruto-nine-tails-cloak') return { ...action, key: 'naruto-cloak', frame: Math.min(3, Math.floor(cast.age / cast.duration * 4)) };
        if (cast.id === 'naruto-kusanagi') return { ...action, key: 'sasuke-sword', frame: Math.min(3, Math.floor(cast.age / cast.duration * 4)) };
        if (cast.id === 'naruto-sharingan') return { ...action, key: 'sasuke-fireball', frame: cast.age < .4 ? 0 : 3 };
        if (cast.id === 'naruto-lee') return {...action,key:'lee-whirlwind',frame:Math.min(3,Math.floor(cast.age/cast.duration*4))};
        if (cast.id === 'naruto-gates') return {...action,key:'lee-gates',frame:Math.min(3,Math.floor(cast.age/cast.duration*4))};
        if (cast.id === 'naruto-lotus'||cast.id === 'naruto-reverse-lotus') return {...action,key:cast.id==='naruto-lotus'?'lee-lotus':'lee-reverse',frame:3,phase:'recovery'};
        if (['naruto-kunai','naruto-shuriken','naruto-fuma-shuriken','naruto-rasenshuriken'].includes(cast.id)) return { ...action, key: name + '-throw', frame: phase === 'windup' ? Math.min(1, Math.floor(cast.age / Math.max(.01, cast.charge) * 2)) : phase === 'release' ? 2 : 3 };
        return { ...action, key: name + '-attack', frame: Math.min(3, Math.floor(cast.age / cast.duration * 4)) };
      }
      const walking = pl ? (pl.walking || anim.base === 'Walk') : anim.cur === 'Walk';
      return walking ? { ...base, state: 'movement', key: name + '-movement', frame: row(dir) * 4 + Math.floor(state.age * 10) % 4 } : base;
    }
    function stateFor(anim) {
      const pose = baseStateFor(anim);
      if (anim.dex === 30006 && G.NarutoGates?.redSkin(actor(anim))) {
        return { ...pose, key: pose.key.replace(/^lee-/, 'lee-opened-'), form: 'gates' };
      }
      return pose;
    }
    function handFor(pl, frame = 2) {
      if (!enabled() || pl?.dex !== 30002 || pl !== G.Game.player) return null;
      const pose=stateFor(pl.anim),side=Math.cos(pose.aim ?? pl.aim ?? 0)<0?-1:1;
      const [x,y]=[[-15,-52],[-24,-42],[44,-33],[14,-32]][frame],scale=pl.anim.scale||1;
      return {x:pl.x+x*side*scale,y:pl.y+y*scale+G.LIFT};
    }
    function adapter(ctx, pose, anim, x, y, opts) {
      if (pose.state !== 'skill' || opts.flash) return;
      const scale = anim.scale || 1, side = Math.cos(pose.aim || 0) < 0 ? -1 : 1;
      ctx.save(); ctx.translate(x, y); ctx.scale(side * scale, scale); ctx.globalAlpha *= opts.alpha ?? 1;
      // Keep the complete candidate silhouette intact. The pose progression and
      // body lean carry the action; never graft a second forearm onto a board.
      if (pose.id === 'naruto-sharingan') {
        const level = G.NarutoSharingan.stage(G.Game.player);
        ctx.fillStyle = '#ff345d'; ctx.fillRect(3, -51, 6, 2);
        ctx.strokeStyle = level >= 4 ? '#bd53ff' : '#ff345d'; ctx.lineWidth = 1.5;
        for (let i = 0; i < level; i++) { const a = i * Math.PI * 2 / level + pose.age * 5; ctx.beginPath(); ctx.arc(8 + Math.cos(a) * 12, -51 + Math.sin(a) * 8, 1.5, 0, Math.PI * 2); ctx.stroke(); }
      }
      ctx.restore();
      if (pose.id === 'naruto-fuma-shuriken' && pose.phase === 'windup') {
        const pl=actor(anim),hand=handFor(pl,pose.frame);
        // The held weapon follows the new windup hand; release uses frame 2.
        G.VFX.draw(ctx, 'naruto-fuma-shuriken', 'naruto-fuma-steel',
          x+hand.x-pl.x,y+hand.y-pl.y-G.LIFT,
          { scale: .9, angle: pose.aim || 0, frame: 0, alpha: opts.alpha ?? 1 });
      }
    }
    const draw = G.Sprites.Animator.prototype.draw;
    G.Sprites.Animator.prototype.draw = function(ctx, x, y, opts = {}) {
      if (!supported(this) || !enabled()) { counters.source++; return draw.apply(this, arguments); }
      const pose = stateFor(this);
      if (!assets.get(pose.key)) { counters.source++; return draw.apply(this, arguments); }
      const rendered = assets.draw(ctx, pose.key, pose.frame, x, y-(pose.visualLift||0), { scale: this.scale || 1, alpha: opts.alpha ?? 1, flash: !!opts.flash, mirror: pose.mirror, rotation: pose.rotation });
      if (rendered === false) throw new Error('Animation frame unavailable: ' + pose.key + ':' + pose.frame);
      counters.candidate++; counters.byState[pose.state] = (counters.byState[pose.state] || 0) + 1;
      if (pose.id) counters.bySkill[pose.id] = (counters.bySkill[pose.id] || 0) + 1;
      adapter(ctx, pose, this, x, y, opts);
    };
    const air = G.Combat.drawAirFields, vfx = G.VFX.draw;
    G.Combat.drawAirFields = function() { const prior = drawingAir; drawingAir = true; try { return air.apply(this, arguments); } finally { drawingAir = prior; } };
    G.VFX.draw = function(ctx, shape, palette, x, y) {
      const pl = G.Game.player;
      if (enabled() && drawingAir && supported(pl?.anim)) {
        const pose = stateFor(pl.anim);
        // Retained boards already contain hand lightning / the Rasengan orb.
        const nearOwner = Math.hypot(x - pl.x, y - (pl.y - G.LIFT)) < 65 * (pl.anim.scale || 1);
        if (pose.key === 'sasuke-chidori' && shape === 'bolt' && palette === 'naruto-blue' && nearOwner) return;
        if (pose.key === 'naruto-rasengan' && shape === 'wind' && palette === 'naruto-blue' && nearOwner) return;
      }
      return vfx.apply(this, arguments);
    };
    G.AnimationLab = { stateFor, handFor, counters, clear, coverage: { common: ['idle', 'movement', 'hurt', 'death'], skills: skillCoverage, sasukeDeath: 'redrawn fall sequence' }, get enabled() { return !!enabled(); } };
    return G.AnimationLab;
  }
  window.AnimationRuntime = { install };
})();
