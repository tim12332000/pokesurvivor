/* Mission objectives must be attainable with the currently selectable roster. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const G = { Ranking: { periodIds: () => ({ d: '2026-11-02', w: '2026-W45' }) } };
const context = vm.createContext({ G, window: { G } });
for (const file of ['js/core/util.js', 'js/data/pokedex.js', 'js/data/moves.js', 'js/data/missions.js', 'js/systems/progress.js']) {
  vm.runInContext(fs.readFileSync(path.join(__dirname, '..', file), 'utf8'), context);
}
const fresh = created => ({ created, coins: 123, tickets: { t1: 4, t10: 2 }, stats: {} });
// The unrestricted game still supports all mission templates.
const normal = new Set();
for (let i = 0; i < 300; i++) {
  const save = fresh(i); G.Progress.ensure(save);
  for (const mission of [...save.missions.daily, ...save.missions.weekly]) normal.add(mission.id);
}
assert(normal.has('evolve') && normal.has('wevolve'));

const types = ['fighting', 'flying', 'electric', 'fire', 'ground', 'steel', 'psychic'];
G.DEX = types.map((type, i) => ({ dex: 30001 + i, types: [type], naruto: true }));
const poolFor = G.Moves.poolFor;
G.Moves.poolFor = mon => mon.naruto ? ['naruto-shadow-clones'] : poolFor(mon);
let playTypes = 0, enemyOnlyTypes = 0;
function attainable(save) {
  for (const mission of [...save.missions.daily, ...save.missions.weekly]) {
    assert(!['evolve', 'wevolve'].includes(mission.id), 'unavailable evolution mission: '+mission.id);
    if (mission.id === 'playType') {
      playTypes++;
      assert(types.includes(mission.param), 'unavailable player type: '+mission.param);
    }
    if (mission.id === 'killType' && !types.includes(mission.param)) enemyOnlyTypes++;
  }
}
for (let i = 0; i < 1000; i++) {
  const save = fresh(i); G.Progress.ensure(save); attainable(save);
  G.DB = { save, commit() {} };
  G.Progress.reroll(0); attainable(save);
}
assert(playTypes > 0 && enemyOnlyTypes > 0, 'kill missions must retain enemy types');

function legacy() {
  const save = fresh(14);
  G.Progress.ensure(save);
  save.missions.rerolled = true;
  save.missions.daily = [
    { id:'playType',param:'poison',goal:3,prog:1,claimed:false,told:false },
    { id:'evolve',goal:1,prog:0,claimed:false,told:false },
    { id:'killType',param:'water',goal:30,prog:12,claimed:false,told:false }
  ];
  save.missions.weekly = [
    { id:'wevolve',goal:3,prog:1,claimed:false,told:false },
    { id:'wrift',goal:1,prog:0,claimed:false,told:false }
  ];
  return save;
}
const a = legacy(), b = legacy(), kill = a.missions.daily[2];
G.Progress.ensure(a); G.Progress.ensure(b); attainable(a);
assert.deepEqual(a, b, 'migration must be deterministic per account and period');
assert.equal(a.missions.daily[0].prog, 1, 'type repair discarded existing progress');
assert.equal(a.missions.daily[2], kill, 'valid enemy-type mission was replaced');
assert.equal(a.missions.rerolled, true, 'migration reset daily reroll allowance');
assert.equal(a.coins, 123); assert.deepEqual(a.tickets, { t1:4,t10:2 });
const snapshot = JSON.stringify(a); G.Progress.ensure(a); assert.equal(JSON.stringify(a), snapshot);
const rewards = legacy();
for (const m of [...rewards.missions.daily, ...rewards.missions.weekly]) m.prog = m.goal;
rewards.missions.weekly[0].claimed = true;
const completed = JSON.stringify(rewards); G.Progress.ensure(rewards);
assert.equal(JSON.stringify(rewards), completed, 'completed or claimed rewards changed');
console.log('Mission generation, rerolls and legacy repair are attainable; completed rewards and enemy types are preserved.');
