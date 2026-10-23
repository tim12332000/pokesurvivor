// Native co-op packet compatibility for immediate chest level rewards.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function boot(uid) {
  let receive;
  const sent = [], broken = [], holds = [];
  class Player {
    constructor() { Object.assign(this, { x: 0, y: 0, hp: 100, maxHp: 100, magnet: 78, xpMul: 1 }); }
    activeGroup() { return []; }
  }
  const G = {
    Net: { uid, on(fn) { receive = fn; }, onPeer() {}, slow: () => false,
      send(to, msg) { sent.push({ to, msg }); }, toHost(msg) { sent.push({ to: 'host', msg }); } },
    World: { breakAt(...args) { broken.push(args); } },
    Player, DEX_BY: { 30009: {} }, startMoveOf: () => 'naruto-tenten',
    Sprites: { preload() {} }, EnemyMgr: { all: () => [] }, Judgment: { netState: () => null },
    Social: { me: null }, Flow: {},
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../js/net/coop.js'), 'utf8'), { G, performance, document: { addEventListener() {} } });
  G.Coop.begin({ host: 'host', members: [{ uid: 'host', name: 'Host', dex: 30009 }, { uid: 'guest', name: 'Guest', dex: 30009 }] }, new Player(), {
    team: () => ({}), syncTeam() {}, hold(names) { holds.push(Array.from(names)); }, choosing: () => false,
  });
  return { G, sent, broken, holds, receive: (...args) => receive(...args) };
}

const host = boot('host');
host.receive('guest', { k: 'f', ev: [['pb', 12, 34, true], ['hs']] });
assert.deepEqual(Array.from(host.broken[0]), [12, 34, true]);
assert.ok(host.holds.at(-1).includes('Guest'), 'chest hold not applied');
host.receive('guest', { k: 'f', ev: [['he']] });
assert.equal(host.holds.at(-1).length, 0, 'chest hold did not release');
host.receive('guest', { k: 'f', ev: [['pb', 13, 34]] });
assert.deepEqual(Array.from(host.broken[1]), [13, 34, false], 'legacy packet changed reward behavior');

const guest = boot('guest');
guest.G.Coop.propBroken({ tx: 4, ty: 5, directLevelReward: true });
guest.G.Coop.tick(.01);
assert.deepEqual(Array.from(guest.sent.at(-1).msg.ev[0]), ['pb', 4, 5, true]);
guest.receive('host', { k: 'f', ev: [['pb', 4, 5, true]] });
assert.deepEqual(Array.from(guest.broken[0]), [4, 5, true]);
guest.receive('host', { k: 'f', ev: [['pb', 6, 7]] });
assert.deepEqual(Array.from(guest.broken[1]), [6, 7, false]);
console.log('PASS: host/client chest reward flag, old packets, hold and release');
