/* Focused quantity formulas and custom character cast snapshots. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const noop = () => {};
global.G = {
  LevelUp: { STATS: [] }, Combat: {}, World: { isWall: () => false, projectileBlock: () => false },
  Player: class {}, Enemy: class {}, Moves: { levelUp: noop }, HUD: { draw: noop },
  Game: {}, Camera: {}, DigimonSkills: { clear: noop }, EnemyMgr: { queryCircle: () => [target] }
};
for (const name of ['hurt', 'update', 'addMove', 'setActive', 'addMaxHp']) G.Player.prototype[name] = noop;
for (const name of ['hurt', 'update', 'die', 'applySlow']) G.Enemy.prototype[name] = noop;
const load = file => vm.runInThisContext(fs.readFileSync(path.join(__dirname, '..', '.omx', file), 'utf8'), { filename: file });
load('quantity.js');
const card = G.LevelUp.STATS.find(c => c.id === 'quantity');
const owner = { moves: [] };
for (let picks = 0; picks <= 10; picks++) {
  if (picks) card.apply(owner);
  assert.equal(G.Quantity.count(owner, 8), Math.floor(8 * 1.25 ** picks));
  assert.ok(G.Quantity.count(owner, 0) >= 1);
}
assert.equal(G.Quantity.count({ quantityBonus: 3 }, 8), 11, 'legacy additive fixtures');
const p = { quantityPicks: 3, moves: [], level: 10, hp: 100, atk: 1, dex: 30006, mon: { dex: 30007 }, x: 0, y: 0 };
G.Game.player = p;
G.NarutoSharingan = { projectileBonus: () => 2 };
const move = { count: 3, pierce: 0, lvl: 5 };
const snap = G.Quantity.snapshot(p, move);
assert.equal(snap.count, Math.floor(3 * 1.25 ** 3) + 2, 'Sharingan is added after multiplication');
assert.equal(snap.pierce, 3, 'pierce stays linear');
assert.equal(move.count, 3, 'learned move is immutable');
assert.deepEqual(G.Quantity.snapshot(p, snap), snap, 'snapshot is idempotent');
p.quantityPicks = 6;
assert.equal(G.Quantity.countAtCast(p, snap, 40), Math.floor(40 * 1.25 ** 3), 'custom bases use frozen multiplier');
G.NarutoSharingan = null;
load('naruto-clones.js');
load('naruto-chidori.js');
assert.equal(G.NarutoClones.limitOf(snap, p), 78);
assert.equal(G.NarutoChidori.limitOf(snap, p), 48);
const target = { hp: 100, x: 10, y: 0 };
load('naruto-lee.js');
const lotus = G.Quantity.snapshot(p, { count: 1, lvl: 5, digiMode: 'lee-reverse-lotus' });
assert.equal(G.NarutoLee.cast(p, lotus), true);
assert.equal(G.NarutoLee.active.comboHits, Math.floor(13 * 1.25 ** 6));
load('naruto-gaara.js');
assert.equal(G.NarutoGaara.cast(p, G.Quantity.snapshot(p, { count: 1, dmg: 1, digiMode: 'gaara-coffin' })), true);
assert.equal(G.NarutoGaara.effects[0].count, 30, 'coffin hard cap');
G.NarutoGaara.clear();
const sand = { count: 3, dmg: 28, digiMode: 'gaara-sand-burst' };
assert.equal(G.NarutoGaara.cast(p, G.Quantity.snapshot(p, sand)), true);
assert.equal(G.NarutoGaara.effects[0].baseCount, 3, 'sand bullet damage denominator stays original');
assert.equal(G.NarutoGaara.effects[0].count, Math.floor(3 * 1.25 ** 6));
load('naruto-sand-guard.js');
p.moves = [{ id: 'naruto-sand-shield', lvl: 5 }];
assert.equal(G.NarutoSandGuard.state(p).guardians.length, 53, 'guardian quantity below cap');
p.quantityPicks = 20;
assert.equal(G.NarutoSandGuard.state(p).guardians.length, 100, 'guardian hard cap');
console.log('Quantity multiplier checks passed: accumulation, legacy, snapshots, four characters, and Gaara caps.');
