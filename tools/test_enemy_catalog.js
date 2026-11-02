/* Filtering the character picker must not filter combat encounters. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const G = {};
const context = vm.createContext({ G, window: { G } });
for (const file of ['js/core/util.js', 'js/data/pokedex.js', 'js/data/sprites-meta.js', 'js/data/enemies.js']) {
  vm.runInContext(fs.readFileSync(path.join(__dirname, '..', file), 'utf8'), context);
}
function encounters() {
  vm.runInContext('letSeed = 123456; Math.random = () => ((letSeed = (Math.imul(letSeed, 1664525) + 1013904223) >>> 0) / 4294967296)', context);
  return JSON.parse(JSON.stringify({
    run: G.Enemies.rollRun(),
    hordes: G.Enemies.hordeTypes(500).map(type => [type, G.Enemies.hordeDefs(type, 500)]),
    upcoming: G.Enemies.upcomingDex(0, 900)
  }));
}
const expected = encounters();
assert(expected.run.cast.every(tier => tier.list.length > 0));
assert.equal(new Set(expected.run.bosses.map(boss => boss.dex)).size, 5);
// Naruto's picker removes the original Pokemon from DEX, retaining DEX_BY.
G.DEX.splice(0, G.DEX.length);
assert.deepEqual(encounters(), expected);
assert.equal(G.DEX.length, 0, 'combat must not restore hidden picker entries');
console.log('Enemy tiers, bosses, hordes and preload roster survive picker filtering.');
