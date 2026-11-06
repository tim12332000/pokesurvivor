/* Provider-independent room and transport facades. See docs/MULTIPLAYER.md.
 * No backend is selected by default; saving and multiplayer are independent.
 */
G.Multiplayer = (() => {
  let rooms = null, transport = null, switching = false, generation = 0, pendingRoomCalls = 0;
  const socialListeners = new Set(), messageListeners = new Set(), peerListeners = new Set();
  let detach = () => {};
  const emptyStats = Object.freeze({ sent: 0, recv: 0, relaySent: 0 });
  const roomMethods = ['start', 'stop', 'claimNick', 'createRoom', 'joinRoom', 'leaveRoom',
    'setOpen', 'refreshMember', 'setPlaying', 'on', 'off'];
  const transportMethods = ['open', 'close', 'syncMembers', 'send', 'peers', 'mode', 'slow',
    'on', 'off', 'onPeer', 'offPeer'];

  function emit(listeners, ...args) {
    for (const fn of listeners) {
      try { fn(...args); } catch (error) { console.error('[Multiplayer] listener:', error); }
    }
  }

  function subscribe(listeners, fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  }

  function validate(provider, methods, fields, label) {
    if (!provider || typeof provider !== 'object') throw new TypeError(label + ' adapter is required');
    for (const name of methods) {
      if (typeof provider[name] !== 'function') throw new TypeError(label + '.' + name + ' must be a function');
    }
    for (const name of fields) {
      if (!(name in provider)) throw new TypeError(label + '.' + name + ' is required');
    }
  }

  // The old WebRTC adapter's path names are accepted at this boundary only.
  function mode(value) { return value === 'direct' || value === 'relay' ? 'connected' : value; }

  async function configure(next) {
    if (switching) throw new Error('Multiplayer configuration is already changing');
    if (pendingRoomCalls) throw new Error('Wait for pending room operations before changing adapters');
    if ((G.Coop && G.Coop.active) || (rooms && rooms.room) || (transport && transport.open_)) {
      throw new Error('Leave the multiplayer game and room before changing adapters');
    }
    if (next !== null) {
      validate(next && next.rooms, roomMethods, ['uid', 'me', 'room', 'started'], 'rooms');
      validate(next && next.transport, transportMethods, ['uid', 'hostUid', 'isHost', 'open_'], 'transport');
      if (next.rooms.room || next.transport.open_) throw new Error('New adapters must not have an open room or connection');
    }
    switching = true;
    try {
      if (transport) transport.close();
      if (rooms) await rooms.stop('switch');
      generation++;
      detach();
      rooms = next ? next.rooms : null;
      transport = next ? next.transport : null;
      if (rooms) {
        const r = rooms, t = transport, version = generation;
        const current = () => !switching && version === generation;
        const social = event => { if (current()) emit(socialListeners, event); };
        const message = (from, msg) => { if (current()) emit(messageListeners, from, msg); };
        const peer = (uid, state) => { if (current()) emit(peerListeners, uid, mode(state)); };
        detach = () => { r.off(social); t.off(message); t.offPeer(peer); };
        try {
          r.on(social); t.on(message); t.onPeer(peer);
        } catch (error) {
          generation++;
          try { detach(); t.close(); await r.stop('configure-failed'); }
          finally { rooms = null; transport = null; detach = () => {}; }
          throw error;
        }
      } else detach = () => {};
    } finally {
      switching = false;
    }
    emit(socialListeners, 'provider');
  }

  function unavailable() {
    return { ok: false, code: 'unavailable', error: '多人連線服務尚未設定或不支援此功能。' };
  }

  const available = () => !switching && !!rooms && rooms.available !== false;
  function socialCall(name, args, fallback) {
    if (!switching && rooms && typeof rooms[name] === 'function') {
      const result = rooms[name](...args);
      if (result && typeof result.then === 'function') {
        pendingRoomCalls++;
        return Promise.resolve(result).finally(() => { pendingRoomCalls--; });
      }
      return result;
    }
    return fallback();
  }

  // Stable API for the existing lobby, UI, and cooperation engine.
  G.Social = {
    get available() { return available(); },
    get me() { return rooms ? rooms.me : null; },
    get uid() { return rooms ? rooms.uid : null; },
    get room() { return rooms ? rooms.room : null; },
    get started() { return rooms ? rooms.started : false; },
    get friends() { return rooms && rooms.friends ? [...rooms.friends] : []; },
    get invites() { return rooms && rooms.invites ? [...rooms.invites] : []; },
    MAX_PLAYERS: 4,
    VALID: /^[A-Za-z0-9_ñÑáéíóúÁÉÍÓÚ]{3,16}$/,
    on(fn) { return subscribe(socialListeners, fn); },
    off(fn) { socialListeners.delete(fn); },
    start() { return available() ? socialCall('start', [], () => Promise.resolve('off')) : Promise.resolve('off'); },
    async stop(reason) {
      G.Net.close();
      return socialCall('stop', [reason], () => undefined);
    },
    now() { return socialCall('now', [], Date.now); },
    profileData() {
      const s = G.DB.save, st = s.stats, prof = s.profile || {};
      const unlocked = G.AchDefs.LIST.filter(a => s.ach && s.ach[a.id]);
      const medals = unlocked.slice().sort((a, b) => (b.tier - a.tier) || (s.ach[b.id] - s.ach[a.id])).slice(0, 8).map(a => a.id);
      return {
        name: G.Social.me ? G.Social.me.name : G.DB.user,
        favs: (prof.favs || []).slice(0, 3).map(f => ({ dex: f.dex | 0, shiny: !!f.shiny })),
        title: prof.title || '',
        best: { solo: st.bestTime | 0, group: st.bestGroupTime | 0, level: st.bestLevel | 0, bosses: st.bossesTotal | 0,
          legends: Object.keys(s.legends || {}).length, kills: st.totalKills | 0, medals: unlocked.length },
        medals
      };
    }
  };
  for (const name of ['claimNick', 'createRoom', 'joinRoom', 'leaveRoom', 'request', 'accept', 'remove', 'invite', 'acceptInvite']) {
    G.Social[name] = (...args) => socialCall(name, args, () => Promise.resolve(unavailable()));
  }
  for (const name of ['setOpen', 'refreshMember', 'setPlaying', 'refreshPresence', 'declineInvite', 'publishProfile']) {
    G.Social[name] = (...args) => socialCall(name, args, () => undefined);
  }
  G.Social.getProfile = (...args) => socialCall('getProfile', args, () => Promise.resolve(null));

  G.Net = {
    open(id, host, hostId) {
      if (!available()) throw new Error('No multiplayer adapter configured');
      transport.open(id, host, hostId);
      if (transport.uid !== rooms.uid) {
        transport.close();
        throw new Error('Room and transport adapters must use the same player uid');
      }
    },
    close() { if (transport) transport.close(); },
    syncMembers(uids) { if (!switching && transport) transport.syncMembers(uids); },
    send(to, msg) { if (!switching && transport) transport.send(to, msg); },
    toHost(msg) { if (!G.Net.isHost && G.Net.hostUid) G.Net.send(G.Net.hostUid, msg); },
    broadcast(msg, except) { for (const uid of G.Net.peers()) if (uid !== except) G.Net.send(uid, msg); },
    on(fn) { return subscribe(messageListeners, fn); },
    off(fn) { messageListeners.delete(fn); },
    onPeer(fn) { return subscribe(peerListeners, fn); },
    offPeer(fn) { peerListeners.delete(fn); },
    mode(uid) { return transport ? mode(transport.mode(uid)) : 'closed'; },
    slow(uid) { return transport ? transport.slow(uid) : true; },
    peers() { return transport ? transport.peers() : []; },
    get open_() { return transport ? transport.open_ : false; },
    get isHost() { return transport ? transport.isHost : false; },
    get uid() { return transport ? transport.uid : null; },
    get hostUid() { return transport ? transport.hostUid : null; },
    get stats() { return transport && transport.stats ? transport.stats : emptyStats; }
  };

  G.DB.onLeave(reason => G.Social.stop(reason));
  return { configure, get configured() { return !!rooms && !!transport; } };
})();
