// Run with node tools/test_multiplayer.js; no network or dependencies.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ROOT = path.join(__dirname, '..');

function boot() {
  const queues = new Map(), writes = [], leave = [];
  const rtdb = { ref(key) {
    return {
      on(event, fn) { queues.set(key, fn); },
      off() { queues.delete(key); },
      push(value) { writes.push({ key, value: JSON.parse(value) }); return Promise.resolve(); }
    };
  } };
  const ctx = {
    G: { DB: { online: false, fb: { uid: 'me', rtdb }, onLeave(fn) { leave.push(fn); } } },
    console, setTimeout: () => 1, clearTimeout() {}, setInterval: () => 1, clearInterval() {},
    document: { addEventListener() {}, removeEventListener() {} },
    RTCPeerConnection: class {
      constructor() { throw Error('WebRTC unavailable in this test'); }
    }
  };
  ctx.window = ctx;
  vm.createContext(ctx);
  const load = file => vm.runInContext(fs.readFileSync(path.join(ROOT, file), 'utf8'), ctx, { filename: file });
  load('js/net/social.js');
  load('js/net/net.js');
  load('js/net/multiplayer.js');
  return { ctx, load, queues, writes, leave };
}

async function regression() {
  const { ctx, queues, writes } = boot();
  const net = ctx.G.createFirebaseTransport({ getSession: () => ctx.G.DB.fb });
  const social = ctx.G.createFirebaseSocial();
  assert.equal(await social.start(), 'off');
  assert.equal(social.room, null);
  const received = [];
  const onMessage = (from, msg) => received.push([from, msg]);
  net.on(onMessage);
  net.open('room', false, 'host');
  assert.equal(net.uid, 'me');
  assert.equal(net.hostUid, 'host');
  assert.equal(net.open_, true);
  assert.equal(net.slow('host'), true);
  // With the old relay disabled, game frames must never reach Firebase.
  net.toHost({ k: 'f', p: [10, 20] });
  assert.equal(writes.length, 0);
  net.toHost({ k: 'start', seed: 42 });
  assert.equal(writes.length, 1);
  assert.equal(writes[0].key, 'rooms/room/q/host');
  const incoming = queues.get('rooms/room/q/me');
  incoming({ val: () => JSON.stringify({ f: 'host', d: { k: 'f', t: 1 } }), ref: { remove: () => Promise.resolve() } });
  assert.equal(received.length, 1);
  assert.equal(received[0][0], 'host');
  assert.equal(received[0][1].t, 1);
  net.off(onMessage);
  incoming({ val: () => 'invalid JSON', ref: { remove: () => Promise.resolve() } });
  assert.equal(received.length, 1);
  net.close();
  assert.equal(net.open_, false);
  assert.equal(queues.size, 0);
  assert.equal(net.peers().length, 0);
  console.log('PASS: local social mode, host routing, disabled relay, message delivery and close cleanup');
}

// Two interchangeable test providers. No Firebase SDK, sockets, or timers.
function adapters(uid, hub = new Map(), pathMode = 'connected') {
  const roomEvents = new Set(), messages = new Set(), peers = new Set();
  const rooms = {
    uid, me: null, room: null, started: false, stopped: 0,
    async start() { this.started = true; this.me = { uid, name: uid }; return 'ok'; },
    async stop() { this.stopped++; this.room = null; this.me = null; this.started = false; },
    async claimNick(name) { this.me = { uid, name }; return { ok: true }; },
    async createRoom() {
      this.room = { id: 'test-room', host: uid, isHost: true, open: true,
        members: [{ uid, name: this.me.name, dex: 25, shiny: false }] };
      this.emit('room');
      return this.room;
    },
    async joinRoom(id) {
      this.room = { id, host: 'host', isHost: false, open: true,
        members: [{ uid: 'host', name: 'host', dex: 25 }, { uid, name: uid, dex: 1 }] };
      this.emit('room');
      return { ok: true };
    },
    async leaveRoom() { this.room = null; this.emit('room'); },
    setOpen(open) { this.room.open = open; this.emit('room'); },
    refreshMember() {}, setPlaying(playing) { this.playing = playing; },
    on(fn) { roomEvents.add(fn); }, off(fn) { roomEvents.delete(fn); },
    emit(event) { for (const fn of roomEvents) fn(event); },
    get subscriptions() { return roomEvents.size; }
  };
  const transport = {
    uid, hostUid: null, isHost: false, open_: false, members: [], closes: 0, state: pathMode,
    open(id, host, hostUid) { this.roomId = id; this.isHost = host; this.hostUid = hostUid; this.open_ = true; hub.set(uid, this); },
    close() { this.open_ = false; this.closes++; this.members = []; hub.delete(uid); },
    syncMembers(uids) { this.members = uids.filter(u => u !== uid && (this.isHost || u === this.hostUid)); },
    send(to, msg) { if (this.open_) hub.get(to)?.receive(uid, structuredClone(msg)); },
    peers() { return this.members; },
    mode() { return this.open_ ? this.state : 'closed'; },
    slow() { return false; },
    on(fn) { messages.add(fn); }, off(fn) { messages.delete(fn); },
    onPeer(fn) { peers.add(fn); }, offPeer(fn) { peers.delete(fn); },
    receive(from, msg) { for (const fn of messages) fn(from, msg); },
    emitPeer(other, mode) { for (const fn of peers) fn(other, mode); },
    get subscriptions() { return messages.size + peers.size; },
    captureMessage() { return [...messages][0]; },
    capturePeer() { return [...peers][0]; }
  };
  return { rooms, transport };
}

async function contract() {
  const app = boot(), { G } = app.ctx;
  assert.equal(G.Multiplayer.configured, false);
  assert.equal(G.Social.available, false);
  assert.equal(await G.Social.start(), 'off');
  assert.equal((await G.Social.joinRoom('x')).ok, false);
  assert.equal((await G.Social.claimNick('name')).ok, false);
  assert.equal(G.Net.open_, false);
  assert.equal(G.Net.mode('any'), 'closed');
  assert.throws(() => G.Net.open('x', true, 'host'), /No multiplayer/);
  assert.equal(app.queues.size, 0, 'disabled default must not subscribe to Firebase');
  assert.equal(app.leave.length, 1, 'only the facade owns logout cleanup');

  const events = [], incoming = [], peerEvents = [];
  const offSocial = G.Social.on(event => events.push(event));
  const offMessage = G.Net.on((from, msg) => incoming.push([from, msg]));
  const offPeer = G.Net.onPeer((uid, state) => peerEvents.push([uid, state]));
  const first = adapters('host');
  await G.Multiplayer.configure(first);
  assert.equal(await G.Social.start(), 'ok');
  assert.equal(G.Social.available, true, 'local save mode must not block configured multiplayer');
  assert.equal(G.Social.me.uid, 'host');
  const room = await G.Social.createRoom();
  assert.equal(G.Social.room.id, 'test-room');
  assert.equal(room.members.length, 1);
  G.Social.setOpen(false);
  assert.equal(G.Social.room.open, false);
  G.Social.setPlaying(true);
  assert.equal(first.rooms.playing, true);
  await assert.rejects(G.Multiplayer.configure(adapters('other')), /Leave the multiplayer/);
  await G.Social.leaveRoom();
  G.Net.open('test-room', true, 'host');
  await assert.rejects(G.Multiplayer.configure(null), /Leave the multiplayer/);
  G.Net.close();
  G.Coop = { active: true };
  await assert.rejects(G.Multiplayer.configure(null), /Leave the multiplayer/);
  G.Coop.active = false;
  await assert.rejects(G.Multiplayer.configure({ rooms: first.rooms, transport: {} }), /transport.open/);
  assert.equal(first.rooms.stopped, 0, 'invalid adapters cannot tear down the current provider');

  const lateMessage = first.transport.captureMessage(), latePeer = first.transport.capturePeer();
  const second = adapters('host', new Map(), 'relay');
  await G.Multiplayer.configure(second);
  assert.equal(first.rooms.stopped, 1);
  assert.equal(first.rooms.subscriptions, 0);
  assert.equal(first.transport.subscriptions, 0);
  assert.equal(second.rooms.subscriptions, 1);
  assert.equal(second.transport.subscriptions, 2);
  lateMessage('old', { k: 'f' }); latePeer('old', 'failed');
  first.rooms.emit('room-closed');
  assert.equal(incoming.length, 0);
  assert.equal(peerEvents.length, 0);
  second.transport.receive('new', { k: 'f' });
  second.transport.emitPeer('new', 'relay');
  assert.equal(incoming.length, 1);
  assert.equal(peerEvents[0][1], 'connected');
  assert.equal(G.Net.slow('new'), false, 'update rate is an explicit capability, not a transport name');
  offSocial(); offMessage(); offPeer();
  const count = events.length;
  second.rooms.emit('room'); second.transport.receive('new', {}); second.transport.emitPeer('new', 'failed');
  assert.equal(events.length, count);
  assert.equal(incoming.length, 1);
  assert.equal(peerEvents.length, 1);
  assert.equal((await G.Social.request('friend')).ok, false, 'friends are optional');
  assert.equal(await G.Social.getProfile('other'), null);
  assert.equal(G.Social.friends.length, 0);

  await G.Social.start();
  G.Net.open('room', true, 'host');
  await app.leave[0]('logout');
  assert.equal(G.Net.open_, false);
  assert.equal(G.Social.started, false);
  await G.Multiplayer.configure(null);
  assert.equal(G.Multiplayer.configured, false);
  assert.equal(await G.Social.start(), 'off');
  assert.equal(second.transport.subscriptions, 0);
  console.log('PASS: disabled default, room contract, validation, safe replacement, stale events, unsubscribe and logout');
}

async function routing() {
  const hub = new Map();
  const host = boot(), guest = boot(), other = boot();
  for (const [app, uid] of [[host, 'host'], [guest, 'guest'], [other, 'other']]) {
    const pair = adapters(uid, hub);
    await app.ctx.G.Multiplayer.configure(pair);
    await app.ctx.G.Social.start();
    if (uid !== 'host') {
      assert.equal((await app.ctx.G.Social.joinRoom('room')).ok, true);
    }
    app.ctx.G.Net.open('room', uid === 'host', 'host');
    app.ctx.G.Net.syncMembers(['host', 'guest', 'other']);
  }
  const got = [], otherGot = [], starts = [];
  guest.ctx.G.Net.on((from, msg) => got.push([from, msg]));
  other.ctx.G.Net.on((from, msg) => otherGot.push([from, msg]));
  guest.ctx.G.Flow = { startCoop: cfg => starts.push(cfg) };
  guest.load('js/net/coop.js');
  host.ctx.G.Net.broadcast({ k: 'start', seed: 42, host: 'host', members: [] }, 'other');
  assert.equal(starts.length, 1, 'unchanged Coop consumes start messages through the facade');
  assert.equal(starts[0].seed, 42);
  assert.equal(got[0][0], 'host');
  assert.equal(otherGot.length, 0, 'broadcast exclusion is preserved');
  const fromGuest = [];
  host.ctx.G.Net.on((from, msg) => fromGuest.push([from, msg]));
  for (let i = 0; i < 5; i++) guest.ctx.G.Net.toHost({ k: 'f', p: [i, 20] });
  assert.deepEqual(fromGuest.map(x => x[1].p[0]), [0, 1, 2, 3, 4]);
  assert.equal(fromGuest[0][0], 'guest');
  host.ctx.G.Net.toHost({ k: 'f' });
  assert.equal(fromGuest.length, 5, 'host must not send to itself');

  const mismatch = boot(), bad = adapters('room-user');
  bad.transport.uid = 'different-user';
  await mismatch.ctx.G.Multiplayer.configure(bad);
  assert.throws(() => mismatch.ctx.G.Net.open('room', true, 'room-user'), /same player uid/);
  assert.equal(bad.transport.open_, false);
  console.log('PASS: interchangeable memory transports, ordered host routing, broadcast exclusion, Coop start and identity guard');
}

async function lifecycle() {
  const { ctx } = boot(), { G } = ctx;
  const first = adapters('host');
  await G.Multiplayer.configure(first);
  let finish;
  first.rooms.start = () => new Promise(resolve => { finish = resolve; });
  const pending = G.Social.start();
  await assert.rejects(G.Multiplayer.configure(adapters('next')), /pending room operations/);
  finish('ok'); await pending;
  first.rooms.joinRoom = () => new Promise((resolve, reject) => { finish = reject; });
  const failedJoin = G.Social.joinRoom('room');
  await assert.rejects(G.Multiplayer.configure(null), /pending room operations/);
  finish(Error('join failed'));
  await assert.rejects(failedJoin, /join failed/);

  first.rooms.stop = () => new Promise(resolve => { finish = resolve; });
  const second = adapters('second');
  const replacing = G.Multiplayer.configure(second);
  await assert.rejects(G.Multiplayer.configure(null), /already changing/);
  assert.equal(await G.Social.start(), 'off');
  finish(); await replacing;
  const broken = adapters('broken');
  broken.transport.onPeer = () => { throw Error('subscription failed'); };
  await assert.rejects(G.Multiplayer.configure(broken), /subscription failed/);
  assert.equal(G.Multiplayer.configured, false);
  assert.equal(broken.rooms.subscriptions, 0);
  assert.equal(broken.transport.subscriptions, 0);
  assert.equal(broken.rooms.stopped, 1);
  assert.equal(broken.transport.closes, 1);
  await G.Multiplayer.configure(adapters('recovered'));
  assert.equal(G.Social.available, true);

  // Local profile preview remains usable without a cloud provider.
  G.DB.user = 'Local';
  G.DB.save = { stats: { bestTime: 12 }, profile: { title: 'hero', favs: [{ dex: 25 }] }, ach: { medal: 1 } };
  G.AchDefs = { LIST: [{ id: 'medal', tier: 1 }] };
  const profile = G.Social.profileData();
  assert.equal(profile.name, 'Local');
  assert.equal(profile.title, 'hero');
  assert.equal(profile.best.solo, 12);
  assert.equal(profile.medals[0], 'medal');
  console.log('PASS: pending operations, concurrent replacement, failed subscription cleanup, recovery and local profiles');
}

async function lobby() {
  const app = boot(), { G } = app.ctx, pair = adapters('host');
  await G.Multiplayer.configure(pair);
  await G.Social.start();
  await G.Social.createRoom();
  pair.rooms.room.members.push({ uid: 'guest', name: 'guest', dex: 1 });
  const elements = new Map();
  G.UI = {
    $(id) { if (!elements.has(id)) elements.set(id, { dataset: {} }); return elements.get(id); },
    isOpen: () => false
  };
  let starts = 0;
  G.Flow = { startCoop: () => starts++ };
  app.load('js/ui/social-ui.js');
  G.LobbyUI.init();
  const click = elements.get('lobby-start').onclick;
  click(); // closed
  G.Net.open('test-room', true, 'host');
  for (const state of ['connecting', 'failed']) { pair.transport.state = state; click(); }
  assert.equal(starts, 0, 'closed, connecting and failed peers cannot start a game');
  pair.transport.state = 'connected';
  click();
  assert.equal(starts, 1);
  assert.equal(G.Social.room.open, false);
  console.log('PASS: lobby start requires every peer to be connected');
}

async function main() {
  await regression();
  await contract();
  await routing();
  await lifecycle();
  await lobby();
}
main().catch(error => { console.error(error); process.exitCode = 1; });
