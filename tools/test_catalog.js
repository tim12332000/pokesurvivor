/* Catalog views must separate complete records from selection without snapshots. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const G = {};
const context = vm.createContext({ G, window: { G } });
for (const file of ['js/core/util.js', 'js/data/pokedex.js', 'js/core/catalog.js', 'js/data/starters.js']) {
  vm.runInContext(fs.readFileSync(path.join(__dirname, '..', file), 'utf8'), context);
}
const C = G.Catalog, ids = view => Array.from(view, record => record.dex);
const all = ids(C.all()), starters = ids(C.starters());
assert.deepEqual(ids(C.playable()), ids(G.DEX));
assert.equal(C.all()[0], G.DEX_BY[all[0]]);
C.restrictTo(['25', 1, 25]);
assert.deepEqual(ids(C.playable()), [1, 25]);
assert.deepEqual(ids(C.starters()), starters.filter(dex => dex === 1 || dex === 25));
assert(C.isPlayable('25')); assert(!C.isPlayable(2)); assert(!C.isPlayable(999999));
for (const invalid of [[999999], [1.5], [NaN], [Infinity], [''], [null], [true], {}]) {
  assert.throws(() => C.restrictTo(invalid));
  assert.deepEqual(ids(C.playable()), [1, 25], 'invalid policy changed current restriction');
}
for (const view of [C.all(), C.playable(), C.starters()]) view.splice(0, view.length);
assert.deepEqual(ids(C.all()), all);
assert.deepEqual(ids(C.playable()), [1, 25]);
assert.deepEqual(ids(G.DEX), all, 'restriction mutated complete character records');
assert.equal(G.STARTERS.length, starters.length, 'restriction mutated complete starters');

// Simulate a later add-on registration after consumers have already read views.
const mon = { dex: 30001, name: 'Late ninja', types: ['fighting'] };
const starter = { dex: mon.dex, start: 'late', traits: ['leal', 'valiente'] };
G.DEX.push(mon); G.DEX_BY[mon.dex] = mon;
G.STARTERS.push(starter); G.STARTER_BY[mon.dex] = starter;
assert.equal(C.all().at(-1), mon);
assert(!C.isPlayable(mon.dex));
C.restrictTo([mon.dex]);
assert.equal(C.playable()[0], mon); assert.equal(C.starters()[0], starter);
C.restrictTo([]); assert.equal(C.playable().length, 0); assert.equal(C.starters().length, 0);
C.restrictTo(null);
assert.deepEqual(ids(C.playable()), ids(G.DEX));
assert.equal(C.starters().at(-1), starter);
for (const record of G.DEX) assert.equal(G.DEX_BY[record.dex], record);
for (const record of G.STARTERS) assert.equal(G.STARTER_BY[record.dex], record);
assert.equal(C.all().length, G.DEX.length);
assert(Object.isFrozen(C));
console.log('Catalog restriction, atomic rejection, view isolation, identity and late registration passed.');
