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
    'naruto-lee-pursuit': 'native automatic pursuit and flurry using authored running and punch poses',
    'naruto-lotus': 'redrawn step-in, rising kick, airborne drive and landing',
    'naruto-gates': 'three-stage passive; red-skin action sets and dedicated red-haired Death Gate',
    'naruto-reverse-lotus': 'redrawn committed aerial taijutsu combo and finisher',
    'naruto-gaara': 'redrawn directed sand-release gesture; real sand projectiles',
    'naruto-sand-coffin': 'redrawn seal, enclosing fist, crush and recovery',
    'naruto-sand-shield': 'selected guard; orbiting sand and directional impact wall',
    'naruto-sand-tsunami': 'redrawn two-arm rise, downward burial and recovery',
    'naruto-tenten': 'original directional kunai throw sequence',
    'naruto-tenten-fuma': 'original prepare, release, catch and recover poses',
    'naruto-tenten-tags': 'original paper kunai preparation, toss and seal gesture',
    'naruto-tenten-twin': 'original twin-scroll opening, aerial release and landing',
    'naruto-tenten-mastery': 'original small-scroll inspection, seal and stow sequence',
    'naruto-tenten-guard': 'reuses authored tenten-mastery four-frame small-scroll open, seal and stow pose; independent eight-tool guard VFX preserves active twin, fuma and tags poses'
  });
  function install(G, { enabled = () => true } = {}) {
    if (installed.has(G)) return G.AnimationLab;
    installed.add(G);
    const assets = window.AnimationAssets;
    const states = new Map();
    const counters = { candidate: 0, source: 0, byState: {}, bySkill: {} };
    let world = G.World, owner = G.Game.player, drawingAir = false;
    const heroes={30001:'naruto',30002:'sasuke',30006:'lee',30007:'gaara',30009:'tenten'};
    const supported = anim => Object.hasOwn(heroes,anim?.dex);
    const hero = anim => heroes[anim.dex];
    const direction = anim => ['down', 'right', 'right', 'right', 'up', 'left', 'left', 'left'][((anim.dir || 0) % 8 + 8) % 8];
    const row = dir => ({ down: 0, up: 1, left: 2, right: 3 })[dir];
    function actor(anim) {
      if (G.Game.player?.anim === anim) return G.Game.player;
      return G.SelfClones?.actors().find(a => a.anim === anim) || G.NarutoClones?.actors.find(a => a.anim === anim) || null;
    }
    function entry(anim) {
      if (!states.has(anim)) states.set(anim, { age: 0, hurtAge: Infinity, deathAge: null, cast: null, sharingan: 0, gates: 0, gaaraShield: 0, kusanagi: false, tentenMastery: 0 });
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
      [G.NarutoSummoning, 'cast', 'naruto-toad-summon', .65],
      [G.NarutoChidori, 'cast', 'naruto-sasuke', .38],
      [G.NarutoFireball, 'cast', 'naruto-fireball', .68],
      [G.NarutoLee, 'cast', null, 1.8],
      [G.NarutoGaara, 'cast', null, .7],
      [G.NarutoSupport, 'cast', null, .5],
      [G.NarutoTenten, 'cast', null, .4]
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
      if (pl?.dex === 30009 && !pl.dead && pl.hp > 0) {
        const mastery = G.NarutoTenten?.stage?.(pl) || 0;
        if (mastery > state.tentenMastery && !G.NarutoTenten?.activeFor?.(pl)) record(pl, {id:'naruto-tenten-mastery'}, .45);
        state.tentenMastery = mastery;
      }
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
        const gaaraShield = pl.dex === 30007 ? (G.NarutoGaara?.shieldStage?.(pl) || 0) : 0;
        const sword = !!G.NarutoKusanagi?.active(pl);
        // Passive synchronization may run immediately after a scene clear or
        // accepted attack. It must never replace that attack's presentation.
        if (!state.cast && level !== state.sharingan && level) record(pl, { id: 'naruto-sharingan' }, .62);
        if (!state.cast && !G.NarutoGaara?.active?.(pl) && gaaraShield !== state.gaaraShield && gaaraShield) record(pl, { id: 'naruto-sand-shield' }, .2);
        if (!state.cast && sword && !state.kusanagi) record(pl, { id: 'naruto-kusanagi' }, .48);
        state.sharingan = level; state.gates = gates; state.gaaraShield = gaaraShield; state.kusanagi = sword;
      }
      for (const [anim] of states) if (anim !== pl?.anim && !G.SelfClones?.actors().some(a => a.anim === anim) && !G.NarutoClones?.actors.some(a => a.anim === anim)) states.delete(anim);
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
      const previous = this.active;
      const result = setActive.apply(this, arguments);
      if (this.dex === 30002 && this.active !== previous) {
        entry(this.anim).cast = null;
        this.comboT = 0; this.attackFace = 0;
      }
      const cast = states.get(this.anim)?.cast;
      if (cast && !this.activeGroup().some(m => m.id === cast.id) && !this.moves.some(m=>m.autoCast&&m.id===cast.id)) entry(this.anim).cast = null;
      return result;
    };
    function baseStateFor(anim) {
      sync();
      const state = entry(anim), pl = actor(anim), name = hero(anim), dir = direction(anim);
      const base = { state: 'idle', phase: 'loop', direction: dir, key: name + '-idle', frame: row(dir) * 4 + (name === 'lee' ? 0 : Math.floor(state.age * 5) % 4), age: state.age, treatment: 'candidate', mirror: false, rotation: 0 };
      if (state.deathAge !== null || pl?.dead || pl?.hp <= 0 || anim.cur === 'Faint') {
        const age = state.deathAge ?? 0;
        return { ...base, state: 'death', phase: age >= .8 ? 'hold' : 'collapse', key: name + '-death', frame: Math.min(3, Math.floor(age * 5)), mirror: dir === 'left', age };
      }
      const gatesOpening = G.NarutoGates?.presentationFor(pl);
      if (gatesOpening && pl?.anim === anim) return { ...base, ...gatesOpening };
      const rasengan=G.DigimonSkills?.rasenganFor?.(pl);
      if(rasengan?.owner?.anim===anim)return {...base,state:'skill',id:'naruto-naruto',phase:rasengan.phase,age:rasengan.t,aim:rasengan.aim,key:'naruto-rasengan',frame:rasengan.phase==='charge'?(rasengan.phaseAge/Math.max(.01,rasengan.m.charge)<.4?0:1):['dash','strike'].includes(rasengan.phase)?2:3,mirror:Math.cos(rasengan.aim)<0};
      const summonPose=G.NarutoSummoning?.poseFor(pl);
      if(name==='naruto'&&summonPose)return {...base,state:'skill',id:'naruto-toad-summon',phase:summonPose.kind,key:summonPose.kind==='tag'?'naruto-throw':'naruto-clones',frame:summonPose.kind==='tag'?2:Math.min(3,Math.floor(summonPose.age/.4*4)),mirror:!!summonPose.mirror,aim:summonPose.aim??pl.aim};
      const chidori = G.NarutoChidori?.activeFor?.(pl) || G.NarutoChidori?.active;
      if (chidori?.owner?.anim === anim) {
        if (chidori.phase === 'charge') {
          const elapsed = Math.max(0, chidori.move.charge - chidori.wait);
          // Four authored foot poses per 40 world units, measured after collision.
          const moving = chidori.chargeMoving;
          return { ...base, state: 'skill', id: 'naruto-sasuke', phase: 'charge', key: moving ? 'sasuke-chidori-charge-walk' : 'sasuke-chidori-charge', frame: moving ? Math.floor(chidori.chargeDistance / 10) % 4 : Math.floor(elapsed * 12) % 4, mirror: Math.cos(pl.aim) < 0 };
        }
        return { ...base, state: 'skill', id: 'naruto-sasuke', phase: chidori.phase, key: 'sasuke-chidori', frame: chidori.phase === 'return' ? 3 : 2, mirror: Math.cos(pl.aim) < 0 };
      }
      const fire = G.NarutoFireball?.activeFor?.(pl) || G.NarutoFireball?.active;
      if (fire?.owner?.anim === anim) return { ...base, state: 'skill', id: 'naruto-fireball', phase: fire.phase, key: 'sasuke-fireball', frame: fire.phase === 'seal' ? Math.min(1, Math.floor(fire.t / .24 * 2)) : fire.phase === 'recovery' ? 3 : 2, mirror: Math.cos(fire.aim) < 0 };
      const whirlwind=G.DigimonSkills?.whirlwindFor?.(pl);
      if(whirlwind?.owner?.anim===anim)return {...base,state:'skill',id:'naruto-lee',phase:whirlwind.phase,
        key:'lee-whirlwind-air',frame:whirlwind.frame,visualLift:whirlwind.visualLift,mirror:Math.cos(whirlwind.aim)<0};
      const lee=G.NarutoLee?.activeFor?.(pl)||G.NarutoLee?.active;
      if(lee?.owner?.anim===anim){
        const reverse=lee.kind==='lee-reverse-lotus';
        if(lee.phase==='approach'&&!lee.pullable)return {...base,state:'skill',id:lee.move.id,phase:lee.phase,key:'lee-movement',frame:row(dir)*4+Math.floor(state.age*12)%4};
        if ((lee.phase === 'approach' && lee.pullable) || lee.phase === 'windup') {
          const frame = lee.phase === 'windup' ? 3 : lee.bandageStage === 'extend' ? (lee.age < .05 ? 0 : 1) : 2;
          return {...base, state:'skill', id:lee.move.id, phase:lee.phase, key:'lee-bandage', frame,
            aim:pl.aim, mirror:Math.cos(pl.aim)<0, visualLift:lee.visualLift||0};
        }
        const frame=['approach','windup'].includes(lee.phase)?0:lee.phase==='lift'?(lee.phaseAge<lee.durations.lift*.5?1:2):lee.phase==='combo'?1+lee.ticks%2:['suspend','descent'].includes(lee.phase)?2:3;
        return {...base,state:'skill',id:lee.move.id,phase:lee.phase,key:reverse?'lee-reverse':'lee-lotus',frame,mirror:Math.cos(pl.aim)<0,visualLift:lee.visualLift||0,
          ...(G.NarutoLee.presentationFor?.(pl) || {})};
      }
      const drunken=G.NarutoDrunkenFist?.presentationFor(pl);
      if(drunken&&pl?.anim===anim)return {...base,...drunken};
      const pursuit=G.NarutoPursuit?.activeFor(pl);
      if(pursuit?.owner?.anim===anim)return {...base,state:'skill',id:'naruto-lee-pursuit',phase:pursuit.phase,
        key:pursuit.phase==='rush'?'lee-movement':'lee-attack',
        frame:pursuit.phase==='rush'?row(direction(anim))*4+Math.floor(pursuit.age*16)%4:Math.min(3,Math.floor(pursuit.attackAge/pursuit.duration*4)),
        mirror:pursuit.phase==='attack'&&Math.cos(pursuit.aim)<0};
      const gaara=G.NarutoGaara?.active?.(pl);
      if(gaara?.owner?.anim===anim){
        const phase=gaara.phase, id=gaara.move.id;
        const key=id==='naruto-sand-coffin'?'gaara-coffin':id==='naruto-sand-tsunami'?'gaara-tsunami':'gaara-sand-burst';
        const frame=id==='naruto-sand-tsunami'?
          (phase==='seal'?0:['raise','surge','burial'].includes(phase)?1:phase==='impact'?2:3):
          id==='naruto-gaara'&&phase==='windup'?(gaara.phaseAge<.06?0:1):
          ['windup','seal','charge'].includes(phase)?0:
          ['bind','close','raise','rise'].includes(phase)?1:
          ['release','crush','slam'].includes(phase)?2:3;
        return {...base,state:'skill',id,phase,key,frame,age:gaara.age,
          aim:gaara.aim,mirror:Math.cos(gaara.aim??pl.aim)<0};
      }
      const tenten = pl?.dex === 30009 ? G.NarutoTenten?.activeFor?.(pl) : null;
      const guard = pl?.dex === 30009 ? G.NarutoTenten?.guardFor?.(pl) : null;
      // Authored attack poses retain priority; guard VFX continue independently.
      const committedTenten = ['tenten-twin', 'tenten-fuma', 'tenten-tags'].includes(tenten?.mode || tenten?.kind);
      if (guard?.owner === pl && guard.age >= 0 && guard.age < .47 && !committedTenten) {
        const age = guard.age;
        return {...base, state:'skill', id:'naruto-tenten-guard', phase:guard.phase,
          key:'tenten-mastery', frame:age < .12 ? Math.min(1, Math.floor(age / .06)) : age < .32 ? 2 : 3,
          age, aim:guard.aim ?? pl.aim, mirror:Math.cos(guard.aim ?? pl.aim ?? 0) < 0};
      }
      if (tenten && (!tenten.owner || tenten.owner === pl)) {
        const mode = tenten.mode || tenten.kind;
        const suffix = ({'tenten-kunai':'throw', 'tenten-fuma':'fuma',
                         'tenten-tags':'tags', 'tenten-twin':'twin', 'tenten-mastery':'mastery'})[mode];
        if (suffix) {
          const age = Math.max(0, tenten.age || 0), duration = Math.max(.001, tenten.duration || .4);
          return {...base, state:'skill', id:mode === 'tenten-kunai' ? 'naruto-tenten' : 'naruto-' + mode,
            phase:tenten.phase || 'release', key:suffix==='twin'&&age>=.08?'tenten-twin-release':'tenten-' + suffix,
            frame:suffix === 'fuma' ? (tenten.phase === 'catch' ? (age < duration * .5 ? 2 : 3) : tenten.phase === 'recovery' ? 3 : tenten.phase === 'prepare' ? 0 : 1) : suffix==='twin' ? (age<.08?0:Math.min(3,Math.floor((age-.08)/(duration-.08)*4))) : Math.min(3, Math.floor(age / duration * 4)), age,
            aim:tenten.aim ?? pl.aim, mirror:Math.cos(tenten.aim ?? pl.aim ?? 0) < 0,
            visualLift:suffix === 'twin' ? Math.sin(Math.min(1,age/duration)*Math.PI)*12*(pl.anim.scale||1) : 0};
        }
      }
      if (state.hurtAge < .3) return { ...base, state: 'hurt', phase: 'recoil', key: name + '-hurt', frame: row(dir) * 4 + Math.min(3, Math.floor(state.hurtAge / .3 * 4)), age: state.hurtAge };
      let cast = state.cast;
      if (!cast && pl?.comboT > 0) cast = { id: pl.mimickedId || 'naruto-kunai', age: .4 - pl.comboT, duration: .4, charge: .12, aim: pl.comboAim || 0 };
      if (!cast && pl?.owner && anim.busy() && ['Shoot', 'Attack', 'Charge'].includes(anim.cur)) {
        const progress = Math.max(0, Math.min(1, anim.progress()));
        cast = { id: pl.mimickedId || 'naruto-kunai', age: progress * .36, duration: .36, charge: .08, aim: pl.target ? Math.atan2(pl.target.y - pl.y, pl.target.x - pl.x) : 0 };
      }
      if(cast?.id==='naruto-lee-pursuit'&&pl)cast=null;
      if (cast) {
        const phase = cast.age < cast.charge ? 'windup' : cast.age < cast.charge + .09 ? 'release' : 'recovery';
        const action = { ...base, state: 'skill', phase, id: cast.id, age: cast.age, treatment: 'redrawn', aim: cast.aim, mirror: Math.cos(cast.aim) < 0 };
        if (cast.id === 'naruto-toad-summon') return { ...action, phase: 'seal', key: 'naruto-clones', frame: Math.min(3, Math.floor(cast.age / .65 * 4)) };
        if (cast.id === 'naruto-shadow-clones') return { ...action, phase: cast.age < .4 ? 'seal' : 'recovery', key: 'naruto-clones', frame: cast.age < .4 ? Math.min(2, Math.floor(cast.age / .4 * 3)) : 3 };
        if (cast.id === 'naruto-sasuke') return { ...action, key: 'sasuke-chidori', frame: 3, phase: 'recovery' };
        if (cast.id === 'naruto-fireball') return { ...action, key: 'sasuke-fireball', frame: 3, phase: 'recovery' };
        if (cast.id === 'naruto-naruto') return { ...action, key: 'naruto-rasengan', frame: phase === 'windup' ? Math.min(1, Math.floor(cast.age / Math.max(.01, cast.charge) * 2)) : phase === 'release' ? 2 : 3 };
        if (cast.id === 'naruto-nine-tails-cloak') return { ...action, key: 'naruto-cloak', frame: Math.min(3, Math.floor(cast.age / cast.duration * 4)) };
        if (cast.id === 'naruto-kusanagi') return { ...action, key: 'sasuke-sword', frame: Math.min(3, Math.floor(cast.age / cast.duration * 4)) };
        if (cast.id === 'naruto-sharingan') return { ...action, key: 'sasuke-fireball', frame: cast.age < .4 ? 0 : 3 };
        if (cast.id === 'naruto-lee') return pl ? base : {...action,key:'lee-whirlwind',frame:Math.min(3,Math.floor(cast.age/cast.duration*4))};
        if (cast.id === 'naruto-gates') return {...action,key:'lee-gates',frame:Math.min(3,Math.floor(cast.age/cast.duration*4))};
        if (['naruto-gaara','naruto-sand-coffin','naruto-sand-shield','naruto-sand-tsunami'].includes(cast.id)) {
          const key={'naruto-gaara':'gaara-sand-burst','naruto-sand-coffin':'gaara-coffin','naruto-sand-shield':'gaara-shield','naruto-sand-tsunami':'gaara-tsunami'}[cast.id];
          return {...action,key,frame:Math.min(3,Math.floor(cast.age/cast.duration*4))};
        }
        if (cast.id === 'naruto-tenten' || cast.id.startsWith('naruto-tenten-')) {
          const suffix = cast.id === 'naruto-tenten' ? 'throw' : cast.id.slice('naruto-tenten-'.length);
          return {...action, key:'tenten-' + suffix, frame:Math.min(3,Math.floor(cast.age / cast.duration * 4))};
        }
        if (cast.id === 'naruto-lotus'||cast.id === 'naruto-reverse-lotus') return {...action,key:cast.id==='naruto-lotus'?'lee-lotus':'lee-reverse',frame:3,phase:'recovery'};
        if (['naruto-kunai','naruto-shuriken','naruto-fuma-shuriken','naruto-rasenshuriken'].includes(cast.id)) return { ...action, key: name + '-throw', frame: phase === 'windup' ? Math.min(1, Math.floor(cast.age / Math.max(.01, cast.charge) * 2)) : phase === 'release' ? 2 : 3 };
        return { ...action, key: name + '-attack', frame: Math.min(3, Math.floor(cast.age / cast.duration * 4)) };
      }
      const walking = pl ? (pl.walking || anim.base === 'Walk') : anim.cur === 'Walk';
      return walking ? { ...base, state: 'movement', key: name + '-movement', frame: row(dir) * 4 + Math.floor(state.age * 10) % 4 } : base;
    }
    function stateFor(anim) {
      const pose = baseStateFor(anim);
      const owner = actor(anim);
      if (anim.dex === 30006 && G.NarutoGates?.redSkin(owner?.sourceOwner || owner)) {
        const death = G.NarutoGates.redForm(owner?.sourceOwner || owner);
        return { ...pose, key: pose.key.replace(/^lee-/, death ? 'lee-death-' : 'lee-opened-'), form: death ? 'death-gate' : 'gates' };
      }
      return pose;
    }
    function handFor(pl, frame = 2) {
      if (!enabled() || pl?.dex !== 30002 || (pl !== G.Game.player && !G.SelfClones?.isActor(pl))) return null;
      const pose=stateFor(pl.anim),side=Math.cos(pose.aim ?? pl.aim ?? 0)<0?-1:1;
      const [x,y]=[[-15,-52],[-24,-42],[44,-33],[14,-32]][frame],scale=pl.anim.scale||1;
      return {x:pl.x+x*side*scale,y:pl.y+y*scale+G.LIFT};
    }
    function handForTenten(pl, side = 0, authoredPose = null) {
      if (pl?.dex !== 30009 || !pl.anim) return null;
      const pose = authoredPose || stateFor(pl.anim), asset = assets.get(pose.key), frame = asset?.frames[pose.frame];
      const point = side < 0 ? frame?.scrollLeft : side > 0 ? frame?.scrollRight : frame?.hand;
      if (!point) return null;
      const k = 64 * (pl.anim.scale || 1) / asset.bodyHeight;
      const mirror = !!pose.mirror !== !!frame.mirror ? -1 : 1;
      // Projectile coordinates include LIFT; drawing subtracts it again.
      return {x:pl.x + (point[0]-frame.anchor[0])*k*mirror,
              y:pl.y + (point[1]-frame.anchor[1])*k - (pose.visualLift||0) + G.LIFT};
    }
    function handForLee(pl) {
      if (!enabled() || pl?.dex !== 30006) return null;
      const pose = stateFor(pl.anim), asset = assets.get(pose.key), frame = asset?.frames[pose.frame];
      if (!frame?.hand) return null;
      const k = 64 * (pl.anim.scale || 1) / asset.bodyHeight;
      const side = !!pose.mirror !== !!frame.mirror ? -1 : 1;
      const x=(frame.hand[0]-frame.anchor[0])*k*side,y=(frame.hand[1]-frame.anchor[1])*k;
      const angle=pose.rotation||0;
      return {x:pl.x+(pose.offsetX||0)+x*Math.cos(angle)-y*Math.sin(angle),
              y:pl.y+(pose.offsetY||0)+x*Math.sin(angle)+y*Math.cos(angle)-(pose.visualLift||0)};
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
      if(pose.id==='naruto-naruto')G.NarutoRasenganVFX?.drawOrb(ctx,anim,pose,x,y,opts);
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
      if (!supported(this) || !enabled() || G.Naruto?.isPreview(ctx.canvas)) { counters.source++; return draw.apply(this, arguments); }
      const pose = stateFor(this);
      if (!assets.get(pose.key)?.image) { counters.source++; return draw.apply(this, arguments); }
      const rendered = assets.draw(ctx, pose.key, pose.frame, x+(pose.offsetX||0), y+(pose.offsetY||0)-(pose.visualLift||0), { scale: this.scale || 1, alpha: opts.alpha ?? 1, flash: !!opts.flash, mirror: pose.mirror, rotation: pose.rotation });
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
        if (assets.get(pose.key)?.image && pose.key === 'sasuke-chidori' && shape === 'bolt' && palette === 'naruto-blue' && nearOwner) return;
        if (assets.get(pose.key)?.image && pose.key === 'naruto-rasengan' && shape === 'wind' && palette === 'naruto-blue' && nearOwner) return;
      }
      return vfx.apply(this, arguments);
    };
    G.AnimationLab = { stateFor, handFor, handForLee, handForTenten, counters, clear, coverage: { common: ['idle', 'movement', 'hurt', 'death'], skills: skillCoverage, sasukeDeath: 'redrawn fall sequence' }, get enabled() { return !!enabled(); } };
    return G.AnimationLab;
  }
  window.AnimationRuntime = { install };
})();
