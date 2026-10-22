/* Focused passive rules: secondary hits must never multiply percent-health procs. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const owner = { hp: 100, dmgDealt: 0, percentHealthDamage: .5, onDealt() { throw Error('Secondary hit proc'); } };
let targets = [], wall = false;
const G = { LevelUp: { STATS: [] }, Game: { everyone: () => [owner] },
  EnemyMgr: { queryCircle: () => targets }, World: { isWall: x => wall && x >= 20 },
  Enemy: class {
    constructor(x, hp = 1000) { this.x = x; this.y = 0; this.hp = this.maxHp = hp; this.r = 0; }
    hurt(amount, color, dx, dy, knock, effect, creditedOwner, moveId) {
      this.hp -= amount;
      assert.equal(knock, 0); assert.equal(effect, null);
      assert.equal(creditedOwner, owner); assert.equal(moveId, 'direct');
      // Even a future hook attempting to splash again cannot recurse.
      G.DamageSplash.hit(owner, this, amount, color, moveId);
    }
  }
};
const context = vm.createContext({ G });
for (const name of ['damage-splash', 'percent-health-damage'])
  vm.runInContext(fs.readFileSync(`.omx/${name}.js`, 'utf8'), context);
const card = G.LevelUp.STATS.find(c => c.id === 'damageSplash');
assert(card); assert.equal(card.max, undefined);
vm.runInContext(fs.readFileSync('js/ui/icons.js', 'utf8'), context);
assert.equal(card.icon, 'damageSplash', 'splash must use its dedicated icon');
assert(G.Icons.UI[card.icon], 'card icon must exist instead of falling back to the star');
assert.notEqual(G.Icons.url(card.icon), G.Icons.url('fist'), 'splash must look different from attack');
const primary = new G.Enemy(0), nearby = new G.Enemy(10), outside = new G.Enemy(61), dead = new G.Enemy(5);
dead.dead = true;
targets = [primary, nearby, nearby, outside, dead];
assert.equal(G.DamageSplash.hit(owner, primary, 100, '#fff', 'direct'), 0);
card.apply(owner); card.apply(owner); card.apply(owner);
G.DamageSplash.hit(owner, primary, 100, '#fff', 'direct');
assert.equal(nearby.hp, 970, '3 picks copy 30%, without max-HP proc');
assert.equal(primary.hp, 1000); assert.equal(outside.hp, 1000); assert.equal(dead.hp, 1000);
assert(Math.abs(owner.dmgDealt - 30) < 1e-8);
primary.dead = true;
G.DamageSplash.hit(owner, primary, 100, '#fff', 'direct');
assert.equal(nearby.hp, 940, 'Lethal primary still splashes');
targets = [new G.Enemy(30)]; wall = true;
G.DamageSplash.hit(owner, primary, 100, '#fff', 'direct');
assert.equal(targets[0].hp, 1000, 'Walls block splash');
wall = false;
targets = [{ x: 5, y: 0, hp: 100, hurt() { throw Error('Expected failure'); } }];
assert.throws(() => G.DamageSplash.hit(owner, primary, 100), /Expected failure/);
assert.equal(G.DamageSplash.isSecondary(), false, 'Suppression always unwinds');
console.log('Damage splash rules passed');
