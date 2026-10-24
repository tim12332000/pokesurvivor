/* Temari sends cast snapshots; only the host commits enemy projectile interception. */
(() => {
  if (G.TemariCoop || !G.Coop || !G.NarutoTemari) return;
  const net = G.Coop, combat = G.NarutoTemari;
  const petSeen = new Map();
  const orbitClaims = new Map(), liftClaims = new Map(), pushClaims = new Map(), pushSeen = new Map(), reflections = new Set(), pendingHazards = new Map();
  const reflectionSeen = new Map(), localWalls = new Map();
  let reflectedDamageSerial = 0, reflectionBound = false, wallSerial = 0;
  const casts = new Map(), actors = new Map(), seen = new Map(), removed = new Set(), retired = new Set();
  let session = '', scene = 0, clock = 0, shotSerial = 0, anticipatedResets = 0;
  const stamp = () => [session, scene];
  const same = token => Array.isArray(token) && token[0] === session && token[1] === scene;
  const ownsMove = move => /^naruto-temari(?:-|$)/.test(move?.id || '');
  const actorId = owner => owner.cloneId == null ? 'player' : 'clone:' + owner.cloneId;
  const localActor = owner => owner === net.local || (owner?.sourceOwner === net.local && G.SelfClones?.isActor(owner));
  const keyOf = (uid, packet) => uid + ':' + packet.actor + ':' + packet.castId;
  const finite = Number.isFinite;

  function clear() {
    for (const shot of G.Projectiles.all()) if (shot.temariPending) { delete shot.temariPending; delete shot.temariContactSent; }
    for (const mate of net.mates) { combat.clear?.(mate.pl); G.NarutoTemariReflect?.clear(mate.pl); }
    for (const actor of actors.values()) { combat.clear?.(actor); G.NarutoTemariReflect?.clear(actor); }
    for (const claim of orbitClaims.values()) combat.releaseNetworkOrbit?.(claim.enemy, claim.packet.castId);
    for (const claim of liftClaims.values()) combat.releaseNetworkLift?.(claim.enemy, claim.packet.castId);
    for (const claim of pushClaims.values()) combat.releaseNetworkPush?.(claim.enemy, claim.packet.castId);
    orbitClaims.clear(); liftClaims.clear(); pushClaims.clear(); pushSeen.clear(); reflections.clear(); pendingHazards.clear();
    reflectionSeen.clear(); localWalls.clear();
    casts.clear(); actors.clear(); seen.clear(); petSeen.clear(); removed.clear(); retired.clear();
    clock = 0;
  }
  function begin(cfg) {
    clear(); session = String(cfg.host) + ':' + String(cfg.seed); scene = 0; shotSerial = 0; anticipatedResets = 0;
  }
  function retireClaim(id, claim) {
    combat.releaseNetworkOrbit?.(claim.enemy, claim.packet.castId);
    orbitClaims.delete(id);
    if (net.active && net.isHost) net.temariEvent(['te', stamp(), claim.uid, claim.actor, id, claim.packet]);
  }
  function clearOwner(uid) {
    for (const [id, claim] of orbitClaims) if (claim.uid === uid) retireClaim(id, claim);
    for (const [id, claim] of liftClaims) if (claim.uid === uid) retireLift(id, claim);
    for (const [id, claim] of pushClaims) if (claim.uid === uid) retirePush(id, claim);
    const parent = net.mate(uid)?.pl;
    if (parent) { combat.clear?.(parent); G.NarutoTemariReflect?.clear(parent); }
    for (const [key, actor] of actors) if (key.startsWith(uid + ':')) { combat.clear?.(actor); G.NarutoTemariReflect?.clear(actor); actors.delete(key); }
    for (const [key, cast] of casts) if (cast.uid === uid) casts.delete(key);
  }
  function retireLift(id, claim) {
    combat.releaseNetworkLift?.(claim.enemy, claim.packet.castId);
    liftClaims.delete(id);
    if (net.active && net.isHost) net.temariEvent(['te', stamp(), claim.uid, claim.actor, id, claim.packet]);
  }
  function retirePush(id, claim) {
    combat.releaseNetworkPush?.(claim.enemy, claim.packet.castId);
    pushClaims.delete(id);
    if (net.active && net.isHost) net.temariEvent(['te', stamp(), claim.uid, claim.actor, id, claim.packet]);
  }
  function actorRemoved(actor) {
    if (!net.active || actor?.sourceOwner !== net.local || actor.cloneId == null || actor.mon?.dex !== 30011) return;
    const id = actorId(actor), key = G.Net.uid + ':' + id;
    if (retired.has(key)) return;
    retired.add(key); combat.clear(actor); G.NarutoTemariReflect?.clear(actor);
    for (const [castKey, cast] of casts) if (cast.owner === actor) casts.delete(castKey);
    net.temariEvent(['tx', stamp(), G.Net.uid, id]);
  }
  function resetScene() {
    clear();
    if (!net.active) return;
    if (!net.isHost && anticipatedResets > 0) anticipatedResets--;
    else scene++;
  }
  function hostFrame(token) {
    if (!Array.isArray(token) || token[0] !== session || !Number.isSafeInteger(token[1]) || token[1] <= scene) return;
    // Arena travel can reach a guest a frame after the host's scene stamp.
    anticipatedResets += token[1] - scene;
    clear(); scene = token[1];
  }
  function trackShot(shot) {
    if (!shot.coopShotId) shot.coopShotId = session + ':' + scene + ':' + (++shotSerial);
    return shot.coopShotId;
  }
  function acceptShot(id) {
    if (!id) return true; // Old peers do not append projectile identity.
    return id.startsWith(session + ':' + scene + ':') && !removed.has(id) && !G.Projectiles.all().some(p => p.coopShotId === id);
  }
  function blockable(shot) {
    return shot.friendly === false && shot.interceptable === true &&
      !['special', 'unblockable', 'guardUnblockable', 'uninterceptable', 'beam', 'laser', 'ground', 'groundField', 'bossSpecial', 'hazard', 'orb'].some(k => shot[k]);
  }
  function sector(packet, x, y, radius = 0, owner = null) {
    const d = packet.deflect;
    if (!d || !finite(x) || !finite(y)) return false;
    const ox = owner?.x ?? packet.x, oy = owner?.y ?? packet.y;
    const dx = x - ox, dy = y - oy, length = Math.hypot(dx, dy);
    const angle = Math.atan2(dy, dx) - packet.aim;
    if (length > d.range + radius || Math.cos(angle) < Math.cos(d.halfAngle)) return false;
    const steps = Math.max(1, Math.ceil(length / 6));
    for (let i = 1; i <= steps; i++) if (G.World.projectileBlock(ox + dx * i / steps, oy + dy * i / steps, 1)) return false;
    return true;
  }
  function remember(uid, owner, packet) {
    if (packet.kind !== 'typhoon' && (!packet.deflect || !packet.empowered || !(packet.deflect.budget > 0))) return;
    casts.set(keyOf(uid, packet), { uid, owner, packet, at: clock, used: 0 });
  }
  function commit(shot) {
    const id = trackShot(shot);
    if (removed.has(id)) return false;
    removed.add(id); G.Projectiles.remove(shot);
    net.temariEvent(['td', stamp(), id]);
    return true;
  }
  function inWindow(cast, grace = 0) {
    const age = clock - cast.at, d = cast.packet.deflect;
    if (!d) return false;
    return !cast.owner.dead && !cast.owner.frozen && cast.owner.hp > 0 && age >= d.start && age <= d.end + grace && cast.used < d.budget;
  }
  function interceptRemote() {
    if (!net.active || !net.isHost) return;
    for (const [key, cast] of casts) {
      if (clock - cast.at > (cast.packet.kind === 'typhoon' ? 5 : (cast.packet.deflect?.end || 0) + .5) || cast.owner.dead || cast.owner.hp <= 0) { casts.delete(key); continue; }
      if (cast.packet.kind === 'typhoon' || cast.uid === G.Net.uid || !inWindow(cast)) continue;
      for (const shot of [...G.Projectiles.all()]) {
        if (!inWindow(cast) || !blockable(shot)) continue;
        const path = Math.hypot(shot.x - (shot.px ?? shot.x), shot.y - (shot.py ?? shot.y));
        const steps = Math.max(1, Math.ceil(path / 6));
        let contact = false;
        for (let i = 0; i <= steps && !contact; i++) contact = sector(cast.packet,
          (shot.px ?? shot.x) + (shot.x - (shot.px ?? shot.x)) * i / steps,
          (shot.py ?? shot.y) + (shot.y - (shot.py ?? shot.y)) * i / steps, shot.r || 0, cast.owner);
        if (contact && commit(shot)) cast.used++;
      }
    }
  }
  function wireCast(owner, source) {
    if (!net.active || !localActor(owner)) return;
    const packet = JSON.parse(JSON.stringify(source));
    packet.actor = actorId(owner); packet.castId = source.castId ?? source.id;
    remember(G.Net.uid, owner, packet);
    net.temariEvent(['tc', stamp(), G.Net.uid, packet]);
  }
  function remoteOwner(uid, packet) {
    const mate = net.mate(uid);
    if (!mate?.connected || mate.pl.dead || mate.pl.net?.dead || retired.has(uid + ':' + packet.actor)) return null;
    if (packet.actor === 'player') return mate.pl;
    const key = uid + ':' + packet.actor;
    let actor = actors.get(key);
    if (!actor) {
      actor = new G.Player(mate.pl.mon, {}, mate.pl.shiny);
      actor.remote = true; actor.uid = uid; actor.sourceOwner = mate.pl;
      actor.cloneId = packet.actor; actors.set(key, actor);
    }
    actor.x = packet.x; actor.y = packet.y; actor.aim = packet.aim;
    if (G.Sprites?.dirFromAngle) actor.anim.dir = G.Sprites.dirFromAngle(packet.aim);
    return actor;
  }
  function validPacket(packet) {
    return packet && typeof packet.actor === 'string' && finite(packet.castId) &&
      ['x', 'y', 'aim'].every(key => finite(packet[key])) && ownsMove(packet.m || { id: packet.id }) &&
      (!packet.deflect || ['start', 'end', 'range', 'halfAngle', 'budget'].every(key => finite(packet.deflect[key])));
  }
  function receive(from, event) {
    if (!net.active || !same(event[1])) return;
    if (event[0] === 'tp') {
      const uid = net.isHost ? from : event[2], packet = event[3];
      if (uid === G.Net.uid || !packet || typeof packet.actor !== 'string' || !finite(packet.serial) ||
          !['x','y','aim'].every(k=>finite(packet[k])) || !Array.isArray(packet.pets) ||
          packet.pets.some(p=>!p || typeof p.id !== 'string' || !finite(p.x) || !finite(p.y) || typeof p.phase !== 'string')) return;
      const key = uid + ':' + packet.actor;
      if ((petSeen.get(key) ?? -1) >= packet.serial) return;
      const owner = remoteOwner(uid, packet);
      if (!owner) return;
      petSeen.set(key, packet.serial);
      combat.applyNetworkPets?.(owner, packet);
      if (net.isHost) net.temariEvent(['tp', stamp(), uid, packet], uid);
      return;
    }
    if (['trc','tr','trh'].includes(event[0])) { receiveReflection(from, event); return; }
    if (event[0] === 'to' || event[0] === 'te') {
      if (net.isHost) return;
      const uid = event[2], actor = event[3], id = event[4], packet = event[5];
      const enemy = G.EnemyMgr.get(id);
      if (!enemy || !packet || !finite(packet.castId)) return;
      if (packet.kind === 'push') {
        const key = uid + ':' + actor + ':' + id, previous = pushSeen.get(key);
        if (previous && (previous.castId > packet.castId || (previous.castId === packet.castId && previous.released))) return;
        if (event[0] === 'te') {
          pushSeen.set(key, {castId:packet.castId, released:true});
          const claim = pushClaims.get(id);
          if (claim && claim.uid === uid && claim.actor === actor && claim.packet.castId === packet.castId) {
            combat.releaseNetworkPush?.(enemy, packet.castId); pushClaims.delete(id);
          }
          return;
        }
        if (previous?.castId === packet.castId) return;
        if (!['x','y','dx','dy','distance','duration','age'].every(k => finite(packet[k])) ||
            packet.duration <= 0 || packet.distance < 0 || packet.age < 0 || packet.age >= packet.duration) return;
        const owner = findActor(uid, actor) || remoteOwner(uid, {actor, x:packet.x, y:packet.y, aim:0});
        if (!owner) return;
        if (combat.applyNetworkPush?.(owner, enemy, {...packet, authoritative:false})) {
          pushSeen.set(key, {castId:packet.castId, released:false});
          pushClaims.set(id, {uid, actor, owner, enemy, packet, at:clock});
        }
        return;
      }
      if (packet.kind === 'lift') {
        if (event[0] === 'te') {
          const claim = liftClaims.get(id);
          if (claim && claim.uid === uid && claim.actor === actor && claim.packet.castId === packet.castId) {
            combat.releaseNetworkLift?.(enemy, packet.castId); liftClaims.delete(id);
          }
          return;
        }
        if (!['x','y','duration','age'].every(k => finite(packet[k])) || packet.duration <= 0 || packet.age < 0 || packet.age >= packet.duration) return;
        const owner = findActor(uid, actor) || remoteOwner(uid, {actor, x:packet.x, y:packet.y, aim:0});
        if (!owner) return;
        if (combat.applyNetworkLift?.(owner, enemy, {...packet, authoritative:false})) {
          liftClaims.set(id, {uid, actor, enemy, packet, at:clock});
        }
        return;
      }
      if (event[0] === 'te') {
        const claim = orbitClaims.get(id);
        if (claim && claim.uid === uid && claim.actor === actor && claim.packet.castId === packet.castId) {
          combat.releaseNetworkOrbit?.(enemy, packet.castId); orbitClaims.delete(id);
        }
        return;
      }
      if (!['x', 'y', 'radius', 'startAngle', 'duration', 'age'].every(k => finite(packet[k])) || packet.duration <= 0) return;
      const owner = uid === G.Net.uid ? (actor === 'player' ? net.local : G.SelfClones?.actors?.().find(a => actorId(a) === actor)) : remoteOwner(uid, {actor, x:packet.x, y:packet.y, aim:packet.startAngle});
      if (!owner) return;
      orbitClaims.set(id, {uid, actor, enemy, packet, at:clock});
      combat.applyNetworkOrbit?.(owner, enemy, {...packet, authoritative:false});
    } else if (event[0] === 'tc') {
      const uid = net.isHost ? from : event[2], packet = event[3];
      if (uid === G.Net.uid || !validPacket(packet)) return;
      const key = uid + ':' + packet.actor;
      if ((seen.get(key) ?? -1) >= packet.castId) return;
      const owner = remoteOwner(uid, packet);
      if (!owner) return;
      seen.set(key, packet.castId); remember(uid, owner, packet); combat.ghost(owner, packet);
      if (net.isHost) net.temariEvent(['tc', stamp(), uid, packet], uid);
    } else if (event[0] === 'tx') {
      const uid = net.isHost ? from : event[2], id = event[3], key = uid + ':' + id;
      if (uid === G.Net.uid || typeof id !== 'string' || !id.startsWith('clone:')) return;
      retired.add(key);
      const owner = actors.get(key);
      if (owner) { combat.clear(owner); G.NarutoTemariReflect?.clear(owner); actors.delete(key); }
      for (const [enemyId, claim] of pushClaims) if (claim.uid === uid && claim.actor === id) retirePush(enemyId, claim);
      for (const [castKey, cast] of casts) if (cast.uid === uid && cast.packet.actor === id) casts.delete(castKey);
      if (net.isHost) net.temariEvent(['tx', stamp(), uid, id], uid);
    } else if (event[0] === 'td') {
      if (!net.isHost) {
        if (event[3] === false) {
          if (event[4] !== G.Net.uid) return;
          const shot = G.Projectiles.all().find(p => p.coopShotId === event[2]);
          if (shot) { delete shot.temariPending; if (finite(event[5]) && finite(event[6])) { shot.x = event[5]; shot.y = event[6]; } }
          return;
        }
        removed.add(event[2]);
        for (const shot of [...G.Projectiles.all()]) if (shot.coopShotId === event[2]) G.Projectiles.remove(shot);
        return;
      }
      const packet = event[3], cast = packet && casts.get(keyOf(from, packet));
      const shot = G.Projectiles.all().find(p => p.coopShotId === event[2]);
      const reject = () => net.temariEvent(['td', stamp(), event[2], false, from, shot?.x, shot?.y]);
      if (!cast || !shot || !blockable(shot) || !inWindow(cast, .25)) { reject(); return; }
      // Accept the reported contact only along this authoritative projectile's trajectory.
      const x = event[4], y = event[5], speed = Math.hypot(shot.vx, shot.vy);
      const distance = Math.hypot(shot.x - x, shot.y - y);
      const cross = speed ? Math.abs((x - shot.x) * shot.vy - (y - shot.y) * shot.vx) / speed : distance;
      if (!sector(cast.packet, x, y, shot.r || 0, cast.owner) || distance > speed * .35 + (shot.r || 0) + 8 || cross > (shot.r || 0) + 8) { reject(); return; }
      if (commit(shot)) cast.used++;
    }
  }

  const previousPets = combat.onPets;
  combat.onPets = (owner, source) => {
    previousPets?.(owner, source);
    if (!net.active || !localActor(owner)) return;
    // Remote pets only render; their damage and move definitions stay on the owner.
    const packet = JSON.parse(JSON.stringify({...source, pets:source.pets.map(p => ({
      ...p, cast:{radius:p.cast?.radius ?? 65, C:p.cast?.C ?? 0}
    }))}));
    Object.assign(packet, {actor:actorId(owner), x:owner.x, y:owner.y, aim:owner.aim || 0});
    net.temariEvent(['tp', stamp(), G.Net.uid, packet]);
  };
  const previousCast = combat.onCast, previousIntercept = combat.onIntercept, previousPolicy = combat.mayIntercept;
  combat.onCast = (owner, packet) => { previousCast?.(owner, packet); wireCast(owner, packet); };
  combat.mayIntercept = (owner, shot, cast) => {
    if (previousPolicy?.(owner, shot, cast) === false) return false;
    if (!net.active || net.isHost || !localActor(owner)) return true;
    const contactKey = actorId(owner) + ':' + (cast.castId ?? cast.serial);
    if (shot.coopShotId && shot.temariContactSent !== contactKey) {
      shot.temariContactSent = contactKey;
      shot.temariPending = { at: clock };
      net.temariEvent(['td', stamp(), shot.coopShotId, { actor: actorId(owner), castId: cast.castId ?? cast.serial }, shot.x, shot.y]);
    }
    return false; // Await the host's removal; a ghost never removes or damages anything.
  };
  combat.onIntercept = (owner, shot, cast) => {
    previousIntercept?.(owner, shot, cast);
    if (net.active && net.isHost && localActor(owner)) commit(shot);
  };
  function ownerIdentity(owner) {
    if (localActor(owner)) return {uid:G.Net.uid, actor:actorId(owner)};
    for (const mate of net.mates) if (mate.pl === owner) return {uid:mate.uid, actor:'player'};
    for (const [key, actor] of actors) if (actor === owner) return {uid:actor.uid, actor:key.slice(String(actor.uid).length + 1)};
    return null;
  }
  const previousControl = combat.mayControl, previousCapture = combat.onCapture, previousRelease = combat.onRelease;
  combat.mayControl = (owner, enemy, cast) => {
    if (previousControl?.(owner, enemy, cast) === false) return false;
    if (!net.active) return true;
    return net.isHost && !enemy.remote && !orbitClaims.has(enemy.id);
  };
  combat.onCapture = (owner, enemy, packet, cast) => {
    previousCapture?.(owner, enemy, packet, cast);
    if (!net.active || !net.isHost) return;
    const identity = ownerIdentity(owner);
    if (!identity) return;
    const claim = {...identity, enemy, packet:{...packet}, at:clock};
    orbitClaims.set(enemy.id, claim);
    net.temariEvent(['to', stamp(), identity.uid, identity.actor, enemy.id, claim.packet]);
  };
  combat.onRelease = (owner, enemy, packet, cast) => {
    previousRelease?.(owner, enemy, packet, cast);
    const claim = orbitClaims.get(enemy.id);
    if (!claim || claim.packet.castId !== packet.castId) return;
    orbitClaims.delete(enemy.id);
    if (net.active && net.isHost) net.temariEvent(['te', stamp(), claim.uid, claim.actor, enemy.id, claim.packet]);
  };
  // Guests do not request displacement from extrapolated enemy positions. The host
  // runs each received cast's actual sweeping front against its authoritative grid.
  combat.requestOrbit = () => false;
  const previousLiftPolicy = combat.mayLift, previousLift = combat.onLift, previousLiftRelease = combat.onLiftRelease;
  combat.mayLift = (owner, enemy, cast) => {
    if (previousLiftPolicy?.(owner, enemy, cast) === false) return false;
    return !net.active || (net.isHost && !enemy.remote);
  };
  combat.onLift = (owner, enemy, packet, cast) => {
    previousLift?.(owner, enemy, packet, cast);
    if (!net.active || !net.isHost) return;
    const identity = ownerIdentity(owner);
    if (!identity) return;
    const claim = {...identity, owner, enemy, packet:{...packet, kind:'lift', x:enemy.x, y:enemy.y}, at:clock};
    liftClaims.set(enemy.id, claim);
    net.temariEvent(['to', stamp(), identity.uid, identity.actor, enemy.id, claim.packet]);
  };
  combat.onLiftRelease = (owner, enemy, packet, cast) => {
    previousLiftRelease?.(owner, enemy, packet, cast);
    const claim = liftClaims.get(enemy.id);
    if (!claim || claim.owner !== owner || claim.packet.castId !== packet.castId) return;
    liftClaims.delete(enemy.id);
    if (net.active && net.isHost) net.temariEvent(['te', stamp(), claim.uid, claim.actor, enemy.id, claim.packet]);
  };
  const previousPushPolicy = combat.mayPush, previousPush = combat.onPush, previousPushRelease = combat.onPushRelease;
  combat.mayPush = (owner, enemy, cast) => {
    if (previousPushPolicy?.(owner, enemy, cast) === false) return false;
    return !net.active || (net.isHost && !enemy.remote);
  };
  combat.onPush = (owner, enemy, packet, cast) => {
    previousPush?.(owner, enemy, packet, cast);
    if (!net.active || !net.isHost) return;
    const identity = ownerIdentity(owner);
    if (!identity) return;
    const claim = {...identity, owner, enemy, packet:{...packet, kind:'push'}, at:clock};
    pushClaims.set(enemy.id, claim);
    net.temariEvent(['to', stamp(), identity.uid, identity.actor, enemy.id, claim.packet]);
  };
  combat.onPushRelease = (owner, enemy, packet, cast) => {
    previousPushRelease?.(owner, enemy, packet, cast);
    const claim = pushClaims.get(enemy.id);
    if (!claim || claim.owner !== owner || claim.packet.castId !== packet.castId) return;
    pushClaims.delete(enemy.id);
    if (net.active && net.isHost) net.temariEvent(['te', stamp(), claim.uid, claim.actor, enemy.id, {...packet, kind:'push'}]);
  };
  function findActor(uid, actor) {
    if (uid === G.Net.uid) return actor === 'player' ? net.local : G.SelfClones?.actors?.().find(a => actorId(a) === actor);
    return actor === 'player' ? net.mate(uid)?.pl : actors.get(uid + ':' + actor);
  }
  function receiveReflection(from, event) {
    const effect = G.NarutoTemariReflect;
    if (!effect) return;
    const uid = net.isHost ? from : event[2], actor = event[3], packet = event[4];
    if (typeof actor !== 'string' || !packet || !finite(packet.castId)) return;
    if (event[0] === 'trc') {
      if (uid === G.Net.uid || packet.mode !== 'temari-reflect') return;
      const key = uid + ':' + actor + ':reflect';
      const sequence = packet.syncSerial ?? packet.castId;
      if (!finite(sequence) || (reflectionSeen.get(key) ?? -1) >= sequence) return;
      if (packet.removed === true) {
        reflectionSeen.set(key, sequence);
        const owner = findActor(uid, actor);
        if (owner) effect.clear(owner);
        if (net.isHost) net.temariEvent(['trc', stamp(), uid, actor, packet], uid);
        return;
      }
      if (!['x','y','radius','duration','multiplier','copies','atk'].every(k=>finite(packet[k])) ||
          packet.radius <= 0 || (packet.permanent === true ? packet.duration !== 0 : packet.duration <= 0) || packet.copies < 1) return;
      const owner = remoteOwner(uid, {actor, x:packet.x, y:packet.y, aim:0});
      if (!owner) return;
      reflectionSeen.set(key, sequence); effect.ghost(owner, packet);
      if (net.isHost) net.temariEvent(['trc', stamp(), uid, actor, packet], uid);
      return;
    }
    if (net.isHost) return; // Only the host can remove sources, return damage, or credit healing.
    const owner = findActor(uid, actor);
    const tag = uid + ':' + actor + ':' + event[0] + ':' + (event[0] === 'trh' ? packet.damageId : packet.reflectionId);
    if (reflections.has(tag)) return;
    if (event[0] === 'trh') {
      if (uid !== G.Net.uid || !owner || !finite(packet.damage) || packet.damage <= 0) return;
      reflections.add(tag); owner.dmgDealt = (owner.dmgDealt || 0) + packet.damage; owner.onDealt?.(packet.damage); return;
    }
    if (!['reflectionId','x','y','angle','copies','damage'].every(k=>finite(packet[k])) || packet.copies < 1) return;
    reflections.add(tag);
    const id = packet.sourceNetId;
    if (id) {
      removed.add(id);
      for (const shot of [...G.Projectiles.all()]) if (shot.coopShotId === id) G.Projectiles.remove(shot);
      pendingHazards.delete(id);
      for (const h of G.Hazards.all) if ((h.coopShotId ?? h.netId) === id) {
        h.temariReturned = true;
        if (h.kind === 'beam') {
          h.len = Math.max(0, Math.hypot(packet.x-h.x, packet.y-h.y) - (h.w || 0));
          if (h.len === 0) { h.hit = true; h.t = h.delay; }
        } else { h.hit = true; h.t = h.delay; }
      }
    }
    if (owner && !owner.dead) effect.receiveReflection(owner, packet);
  }
  function wireWall(owner, source) {
    if (!net.active || !localActor(owner)) return;
    const previous = localWalls.get(owner);
    if (!source && !previous) return;
    const packet = source ? {...source, x:owner.x, y:owner.y} : {
      mode:'temari-reflect', castId:previous.castId, removed:true
    };
    packet.syncSerial = ++wallSerial;
    if (source) localWalls.set(owner, {castId:source.castId, at:clock});
    else localWalls.delete(owner);
    net.temariEvent(['trc', stamp(), G.Net.uid, actorId(owner), packet]);
  }
  function syncReflectionWalls() {
    if (!net.active || G.Game.state !== 'playing') return;
    const effect = G.NarutoTemariReflect;
    const owners = [net.local, ...(G.SelfClones?.actors?.() || [])].filter(localActor);
    for (const owner of owners) {
      const wall = effect?.activeFor(owner), previous = localWalls.get(owner);
      if (!wall) { if (previous) wireWall(owner, null); continue; }
      if (!previous || clock - previous.at >= 1) {
        // The wire snapshot excludes runtime owner/world/proxy references.
        const {owner:unusedOwner, world:unusedWorld, damageOwner:unusedDamageOwner, ...packet} = wall;
        wireWall(owner, packet);
      }
    }
    for (const owner of localWalls.keys()) if (!owners.includes(owner)) wireWall(owner, null);
  }
  function bindReflection() {
    const effect = G.NarutoTemariReflect;
    if (!effect || reflectionBound) return;
    reflectionBound = true;
    const sync = effect.onSync, reflected = effect.onReflect, policy = effect.mayReflect, damage = effect.onReflectionDamage;
    effect.onSync = (owner, packet) => { sync?.(owner, packet); wireWall(owner, packet); };
    effect.mayReflect = (owner, source) => {
      if (policy?.(owner, source) === false) return false;
      if (!net.active) return localActor(owner) || owner === G.Game.player || G.SelfClones?.isActor(owner);
      if (net.isHost) return true;
      if (localActor(owner)) {
        const id = source.coopShotId ?? source.netId;
        if (id && !removed.has(id)) {
          if (source.kind === 'beam' || source.kind === 'zone') {
            if (!pendingHazards.has(id)) pendingHazards.set(id, {source, at:clock});
          } else if (!source.temariPending) source.temariPending = {at:clock};
        }
      }
      return false;
    };
    effect.onReflect = (owner, packet, source) => {
      reflected?.(owner, packet, source);
      if (!net.active || !net.isHost) return;
      const identity = ownerIdentity(owner);
      if (!identity) return;
      if (packet.sourceNetId) removed.add(packet.sourceNetId);
      net.temariEvent(['tr', stamp(), identity.uid, identity.actor, {...packet,sourceKind:source.kind === 'beam' || source.kind === 'zone' ? 'hazard':'projectile'}]);
    };
    effect.onReflectionDamage = (owner, amount, wall) => {
      damage?.(owner, amount, wall);
      if (!net.active || !net.isHost || !finite(amount) || amount <= 0) return;
      const identity = ownerIdentity(owner);
      if (!identity || identity.uid === G.Net.uid) return;
      net.temariEvent(['trh', stamp(), identity.uid, identity.actor, {castId:wall.castId, damageId:++reflectedDamageSerial, damage:amount}]);
    };
  }
  bindReflection();
  const hazardUpdate = G.Hazards.update;
  G.Hazards.update = function(dt, ...args) {
    G.NarutoTemariReflect?.interceptHazards(dt);
    const held = [];
    for (const [id, pending] of pendingHazards) {
      if (clock-pending.at > 1 || !net.active || removed.has(id)) { pendingHazards.delete(id); continue; }
      const h = pending.source; held.push([h,h.t,h.hit]); h.hit=true; h.t=Math.min(h.t,h.delay-1);
    }
    try { return hazardUpdate.call(this,dt,...args); }
    finally { for (const [h,t,hit] of held) { h.t=t; h.hit=hit; } }
  };
  const update = G.Projectiles.update;
  G.Projectiles.update = function(dt, ...args) {
    bindReflection();
    if (net.active && G.Game.state === 'playing' && finite(dt) && dt > 0) clock += dt;
    syncReflectionWalls();
    for (const mate of net.mates) if (mate.pl.dead || mate.pl.net?.dead) clearOwner(mate.uid);
    for (const actor of actors.values()) actor.anim.update(dt);
    for (const [id, claim] of orbitClaims) {
      const orbit = combat.orbitFor?.(claim.enemy);
      const live = orbit && orbit.owner === findActor(claim.uid, claim.actor) &&
        (orbit.cast.castId ?? orbit.cast.serial) === claim.packet.castId;
      // A wind lift pauses the orbit's own clock. Wall time only expires an
      // orphaned claim; a live lease must finish its entire circular sweep.
      if (claim.enemy.dead || (!live && clock - claim.at > claim.packet.duration + .5)) retireClaim(id, claim);
    }
    for (const [id, claim] of liftClaims) {
      const lift = combat.liftForState?.(claim.enemy);
      const live = lift && lift.owner === findActor(claim.uid, claim.actor) &&
        (lift.cast.castId ?? lift.cast.serial) === claim.packet.castId;
      if (claim.enemy.dead || (!live && clock - claim.at > claim.packet.duration + .5)) retireLift(id, claim);
    }
    for (const [id, claim] of pushClaims) {
      const push = combat.pushFor?.(claim.enemy);
      const live = push && push.owner === findActor(claim.uid, claim.actor) &&
        (push.cast.castId ?? push.cast.serial) === claim.packet.castId;
      if (claim.enemy.dead || (!live && clock - claim.at > claim.packet.duration + .5)) retirePush(id, claim);
    }
    interceptRemote();
    const held = [];
    for (const shot of G.Projectiles.all()) if (shot.temariPending) {
      if (clock - shot.temariPending.at > 1) { delete shot.temariPending; continue; }
      held.push([shot, shot.vx, shot.vy]); shot.vx = shot.vy = 0;
    }
    let result;
    try { result = update.call(this, dt, ...args); }
    finally { for (const [shot, vx, vy] of held) { shot.vx = vx; shot.vy = vy; } }
    interceptRemote();
    return result;
  };
  const clearFields = G.Combat.clearFields;
  G.Combat.clearFields = function(owner) {
    if (!owner) resetScene();
    else actorRemoved(owner);
    return clearFields.call(this, owner);
  };
  const resolve = G.Combat.resolve;
  G.Combat.resolve = function(...args) {
    G.NarutoTemariReflect?.interceptProjectiles();
    const held = [];
    for (const shot of G.Projectiles.all()) if (shot.temariPending) {
      held.push([shot, shot.friendly, shot.ghost, shot.orb]);
      shot.friendly = shot.ghost = shot.orb = true;
    }
    try { return resolve.apply(this, args); }
    finally { for (const [shot, friendly, ghost, orb] of held) Object.assign(shot, { friendly, ghost, orb }); }
  };
  const drawAir = G.Combat.drawAirFields;
  G.Combat.drawAirFields = function(ctx) {
    const result = drawAir.call(this, ctx);
    for (const actor of [...actors.values()].sort((a, b) => a.y - b.y)) if (G.Camera.sees(actor.x, actor.y, 100)) {
      ctx.save(); ctx.globalAlpha *= .7; actor.draw(ctx); ctx.restore();
    }
    return result;
  };
  G.TemariCoop = { begin, clear, clearOwner, actorRemoved, stamp, trackShot, acceptShot, ownsMove, receive,
    hostFrame, remoteActors: () => [...actors.values()],
    inspect: () => ({ session, scene, casts: casts.size, actors: actors.size, seen: seen.size, removed: removed.size, orbits:orbitClaims.size, lifts:liftClaims.size, pushes:pushClaims.size, reflections:reflections.size, pendingHazards:pendingHazards.size, petActors:petSeen.size }) };
})();
