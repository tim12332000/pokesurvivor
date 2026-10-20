/* Real technique code must return at fractional contact coordinates. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const owner = { x: 0, y: 0, r: 12, hp: 100, dex: 30006, atk: 1 };
const target = { x: 0, y: 0, r: 10, hp: 1000 };
const G = {
  Combat: { updateFields() {}, clearFields() {} }, Player: function() {}, Enemy: function() {},
  HUD: { draw() {} },
  Game: { player: owner, state: 'playing' },
  World: { isWall: () => false, projectileBlock: () => false, isFree: () => true },
  EnemyMgr: { queryCircle: () => [target] }, Sprites: { dirFromAngle: () => 0 }
};
G.Player.prototype.update = function() {};
const context = vm.createContext({ G, Math });
vm.runInContext(fs.readFileSync(path.join(__dirname, '../.omx/naruto-lee.js'), 'utf8'), context);
const reproduced = [245.2212490607053, 607.796689029783, 264.44099647663217, 639.8360687385729];
let seed = 123456;
const random = () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 4294967296);
let cases = 0;
for (const mode of ['lee-lotus', 'lee-reverse-lotus']) {
  for (let i = 0; i < 501; i++) {
    const x = random() * 100000, y = random() * 100000;
    const angle = random() * Math.PI * 2, distance = 34 + random() * 6;
    const coordinates = i === 0 ? reproduced : [x, y, x + Math.cos(angle) * distance, y + Math.sin(angle) * distance];
    [owner.x, owner.y, target.x, target.y] = coordinates;
    G.NarutoLee.clear();
    assert(G.NarutoLee.cast(owner, { digiMode: mode, range: 145, dmg: 70 }));
    vm.runInContext('G.NarutoLee.update(1/60)', context, { timeout: 100 });
    assert.equal(G.NarutoLee.active.phase, 'windup', `${mode} contact ${i}`);
    assert(Math.hypot(owner.x - coordinates[0], owner.y - coordinates[1]) <= 8.001);
    cases++;
  }
}
console.log(`PASS: ${cases} fractional contacts complete without blocking or teleporting`);
