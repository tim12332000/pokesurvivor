/* Production shield calculation: doubled capacity and delta-only growth. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const noop = () => {};
class Player {
  addMove() {}
  setActive() {}
  addMaxHp(n) { this.maxHp += n; this.hp += n; }
  activeGroup() { return []; }
  hurt(n) { this.hp -= n; }
}
class Enemy {}
Enemy.prototype.applySlow = noop;
const G = { Player, Enemy, LevelUp: { STATS: [] }, Combat: { tick: noop, updateFields: noop, clearFields: noop },
  World: {}, Game: { state: 'playing' }, FX: { burst: noop },
  Moves: { levelUp: move => { move.lvl++; return true; } } };
const p = G.Game.player = new Player();
Object.assign(p, { mon: { dex: 30007 }, hp: 136, maxHp: 136, level: 1, invuln: 0, cdMul: 1,
  moves: [{ id: 'naruto-sand-shield', lvl: 1 }] });
vm.runInNewContext(fs.readFileSync('.omx/naruto-gaara.js', 'utf8'), { G, performance });
const state = () => G.NarutoGaara.shieldState(p);
assert.equal(state().capacity, 92, 'Lv1 shield is twice 45+1');
p.hurt(10, null, true);
const damaged = state();
p.level = 2;
assert.equal(state().capacity, 94);
assert.equal(state().amount, damaged.amount + 2, 'level grants only new doubled capacity');
const before = state();
p.addMaxHp(20);
assert.equal(state().capacity, before.capacity + 40, 'health cards also double their shield contribution');
assert.equal(state().amount, before.amount + 40);
assert.equal(state().progress, before.progress, 'growth must preserve recharge progress');
const amount = state().amount;
assert.equal(state().amount, amount, 'sync cannot add the bonus twice');
vm.runInNewContext(fs.readFileSync('.omx/max-health-percent.js', 'utf8'), { G });
const growth = G.LevelUp.STATS.find(card => card.id === 'maxHealthPercent');
assert.equal(G.MaxHealthPercent.perPick, .1);
assert.equal(growth.title, '生命成長 +10%');
for (let i = 0; i < 3; i++) {
  const health = p.maxHp, shield = state();
  growth.apply(p);
  assert(Math.abs(p.maxHp - health * 1.1) < 1e-8, 'growth compounds by 10%');
  assert(Math.abs(state().capacity - shield.capacity - health * .1 * 2) < 1e-8, '10% growth adds doubled shield');
  assert.equal(state().progress, shield.progress);
}
G.NarutoGaara.clear();
p.level = 12; p.moves[0].lvl = 5; p.sandShieldHealthBonus = 0;
assert.equal(state().capacity, 340, 'Lv12 tier5 is twice 110+12*5');
console.log('Shield and health growth passed: doubled capacity, 10% compounding, delta-only growth and tier five.');
