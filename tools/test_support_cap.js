// Run with node tools/test_support_cap.js; exercises the real public spawner API.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../js/systems/spawner.js'), 'utf8');
const definition = behavior => ({ dex: 1, behavior, hp: 10, dmg: 2, xp: 3 });

function boot(behaviors) {
  const enemies = [], player = { x: 0, y: 0, dead: false };
  let bag = behaviors.map(definition);
  const G = {
    U: { pick: list => list[0], rand: (a, b) => (a + b) / 2,
      dist2: (x, y, a, b) => (x-a)**2 + (y-b)**2 },
    Camera: { outerRadius: () => 300, kick() {} },
    World: { isFree: () => true },
    Sprites: { hovers: () => false, hasShiny: () => false, preload() {} },
    Enemies: { bagAt: () => bag, scale: () => ({hp: 1}), upcomingDex: () => [], rollRun() {}, BOSSES: [] },
    EnemyMgr: { all: () => enemies, add: enemy => enemies.push(enemy),
      get count() { return enemies.filter(enemy => !enemy.dead).length; }, bossAlive: () => false },
    Enemy: class { constructor(def, x, y, scale) { Object.assign(this, def, {x, y, dead: false});this.hp=this.maxHp=def.hp*scale.hp; } },
    Coop: { scaleHp: () => 1, scaleRate: () => 1, isHost: false },
    Events: { golden: false }, Rift: { inArena: false }, Judgment: { active: false },
    Audio: { sfx() {} }, Game: { player, st: { time: 0 } }
  };
  vm.runInNewContext(source, { G, Math }, { filename: 'spawner.js' });
  G.Spawner.reset();G.Spawner.update(0, player, 0);
  return { G, enemies, player, bag: roles => {bag=roles.map(definition);},
    count: role => enemies.filter(enemy => !enemy.dead && enemy.behavior === role).length };
}

for (const role of ['healer', 'shielder', 'summoner']) {
  const f=boot([role]);
  f.G.Spawner.burst(12);assert.equal(f.count(role), 3, role+' exceeded its cap');
  f.G.Spawner.burst(4);assert.equal(f.enemies.length, 3, 'Full-only pool must skip spawning');
  f.enemies[0].dead=true;f.G.Spawner.burst(1);
  assert.equal(f.count(role), 3, 'Dead support must release its slot');
  assert.equal(f.enemies.length, 4);
}

const independent=boot(['healer']);independent.G.Spawner.burst(5);
independent.bag(['shielder','healer']);independent.G.Spawner.burst(5);
independent.bag(['summoner','healer','shielder']);independent.G.Spawner.burst(5);
for(const role of ['healer','shielder','summoner'])assert.equal(independent.count(role), 3);
assert.equal(independent.enemies.length, 9, 'Roles must have separate caps');
independent.bag(['healer','shielder','summoner','chase']);independent.G.Spawner.burst(10);
assert.equal(independent.count('chase'), 10, 'Full support pools must fall back to ordinary enemies');
assert.equal(independent.G.Spawner.CAP, 64, 'Total enemy limit changed');
const ordinary=independent.enemies.find(enemy=>enemy.behavior==='chase');
assert.equal(ordinary.maxHp,33);assert.equal(ordinary.dmg,4.8);assert.equal(ordinary.xp,17);

const waves=boot(['healer','chase']);waves.G.Spawner.update(40,waves.player,0);
assert.equal(waves.count('healer'),3);assert.ok(waves.count('chase')>0, 'Normal and surge waves stopped');
const coop=boot(['summoner','chase']);coop.G.Spawner.update(0,[coop.player,{x:20,y:0,dead:false}],0);
coop.G.Spawner.burst(12);assert.equal(coop.count('summoner'),3, 'Cap must be shared across players');
coop.enemies.length=0;coop.G.Spawner.reset();coop.G.Spawner.burst(4);
assert.equal(coop.count('summoner'),3,'New run retained a full-support counter');
console.log('Support caps passed: each role, fallback, dead-slot refill, wave/burst, shared coop cap and reset.');
