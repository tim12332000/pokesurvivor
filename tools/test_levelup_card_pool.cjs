/* Exercise production card selection without a browser or forced card offers. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
let seed = 0x13579bdf;
const randomMath = Object.create(Math);
randomMath.random = () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 2 ** 32);

// Skill fixtures only supply the roster; selection, training, and cards use real code.
const rosters = new Map([
  [30001, ['naruto-naruto', 'naruto-rasenshuriken', 'naruto-nine-tails-cloak']],
  [30002, ['naruto-fireball', 'naruto-sharingan', 'naruto-fuma-shuriken']],
  [30006, ['naruto-lotus', 'naruto-gates', 'naruto-reverse-lotus']],
  [30007, ['naruto-sand-shield', 'naruto-sand-coffin', 'naruto-sand-tsunami', 'naruto-sand-prison']]
]);
const definitions = {};
for (const ids of rosters.values()) ids.forEach((id, index) => {
  definitions[id] = { id, name: id, desc: id, type: 'ground', learnLevel: [3, 6, 9, 12][index],
    kind: 'projectile', passive: ['naruto-gates', 'naruto-sand-shield'].includes(id) };
});
class Player {
  constructor(dex, level = 15) {
    this.mon = { dex, naruto: rosters.has(dex), name: String(dex) };
    Object.assign(this, { level, moves: [], slots: [], maxMoves: 5, active: 0, bind: {},
      statsTaken: {}, banned: new Set(), hp: 100, maxHp: 100, atkMul: 1, spdMul: 1,
      cdMul: 1, dmgReduce: 0, regenFlat: 0, magnet: 1, xpMul: 1 });
  }
  hasMove(id) { return this.moves.some(m => m.id === id); }
  activeGroup() { return this.slots[this.active] || []; }
  arrange() {}
  setActive(index) { this.active = index; }
  addMove(id) { const move = G.Moves.instance(id); this.moves.push(move); this.slots.push([move]); return true; }
  addMaxHp(n) { this.maxHp += n; this.hp += n; }
  heal(n) { this.hp = Math.min(this.maxHp, this.hp + n); }
}
const G = {
  Player, Game: { state: 'playing', startRun() {} },
  Moves: { BY_ID: definitions, poolFor: mon => rosters.get(mon.dex) || [],
    evoInfo: () => null, nextUpText: () => null, instance: (id, lvl = 1) => ({ ...definitions[id], lvl, def: definitions[id] }) },
  NarutoSkillCatalog: { extraPools: rosters }
};
const context = vm.createContext({ G, window: { G }, Math: randomMath });
const load = file => vm.runInContext(fs.readFileSync(path.join(root, file), 'utf8'), context, { filename: file });
load('js/core/util.js');
G.U.TYPE_COLOR = { ground: '#aa8' }; G.U.TYPE_NAME = { ground: 'Ground' };
load('js/systems/levelup.js');
load('.omx/naruto-training.js');
load('.omx/quantity.js');
load('.omx/damage-splash.js');

const results = [];
for (const dex of [...rosters.keys(), 19]) {
  const p = G.Game.player = new Player(dex);
  const eligible = G.LevelUp.STATS.filter(s => !s.max || (p.statsTaken[s.id] || 0) < s.max);
  for (let i = 0; i < 10; i++) {
    const all = G.LevelUp.offer(p, 100);
    for (const stat of eligible)
      assert(all.some(c => c.key === 'stat:' + stat.id), `${dex}: preselection excluded ${stat.id}`);
  }
  assert(!p.narutoMilestonesShown, 'offer previews consumed milestone opportunities');
  // The native UI calls these hooks after rendering. This VM has no DOM;
  // model that one display before measuring the ordinary weighted card pool.
  for (const card of G.LevelUp.offer(p, 100)) card.onShown?.(p);
  let splash = 0, quantity = 0, nonSignatureOffers = 0;
  let splashChoice, quantityChoice;
  for (let i = 0; i < 1000; i++) {
    const choices = G.LevelUp.offer(p);
    assert.equal(choices.length, 3);
    assert.equal(new Set(choices.map(c => c.key)).size, 3, 'duplicate choice');
    splashChoice = choices.find(c => c.key === 'stat:damageSplash') || splashChoice;
    quantityChoice = choices.find(c => c.key === 'stat:quantity') || quantityChoice;
    splash += choices.some(c => c.key === 'stat:damageSplash');
    quantity += choices.some(c => c.key === 'stat:quantity');
    nonSignatureOffers += choices.some(c => c.type === 'stat');
  }
  assert(splash > 0 && quantity > 0 && nonSignatureOffers > 0, `${dex}: growth cards blocked`);
  assert(splash < 1000 && quantity < 1000, 'growth cards must not be guaranteed');
  splashChoice.apply(p); splashChoice.apply(p);
  assert.equal(p.statsTaken.damageSplash, 2);
  assert(Math.abs(G.DamageSplash.rate(p) - .2) < 1e-10);
  quantityChoice.apply(p); quantityChoice.apply(p);
  assert.equal(G.Quantity.multiplier(p), 1.5625);
  assert.equal(p.statsTaken.quantity, 2);
  p.statsTaken.quantity = 20;
  assert(!G.LevelUp.offer(p, 100).some(c => c.key === 'stat:quantity'), 'quantity pick cap ignored');
  p.slots = Array.from({ length: p.maxMoves }, () => []);
  const full = G.LevelUp.offer(p, 100);
  assert(full.some(c => c.key === 'stat:damageSplash'), 'full slots blocked splash');
  results.push({ dex, splash, quantity, trials: 1000 });
}
const lowLevel = G.Game.player = new Player(30006, 1);
assert(!G.LevelUp.offer(lowLevel, 100).some(c => c.type === 'new'), 'skill learning level ignored');

// A correct JS implementation is insufficient if HTML still asks for a cached old version.
const entryRoot = process.argv[2] ? path.resolve(process.argv[2]) : root;
const html = fs.readFileSync(path.join(entryRoot, '.omx/digimon.html'), 'utf8');
const scripts = new Map([...html.matchAll(/<script\b[^>]*\bsrc="([^"?]+)(?:\?v=([^"&]+))?"/g)]
  .map(match => [match[1], match[2]]));
for (const file of ['js/systems/levelup.js', '.omx/naruto-training.js', '.omx/quantity.js', '.omx/damage-splash.js']) {
  const hash = crypto.createHash('sha256').update(fs.readFileSync(path.join(entryRoot, file))).digest('hex').slice(0, 12);
  assert.equal(scripts.get(file), hash, `${file}: game entry cache version is stale`);
}
console.log(JSON.stringify({ ok: true, results, checked: 'real weighted selection after first display, read-only previews, repeat picks, limits, full slots, learning levels, entry hashes' }));
