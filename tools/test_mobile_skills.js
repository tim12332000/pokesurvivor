// Run with node tools/test_mobile_skills.js. No browser or dependencies required.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const read = file => fs.readFileSync(path.join(__dirname, '..', file), 'utf8');
const settings = {};
const G = { Settings: { touch: true, get: key => settings[key] } };
const context = { G, innerWidth: 390, innerHeight: 844, addEventListener() {},
  document: { createElement: () => ({ style: {}, remove() {} }), body: { appendChild() {} } },
  getComputedStyle: () => ({ paddingTop: '0', paddingBottom: '34', paddingLeft: '0', paddingRight: '0' }) };
vm.runInNewContext(read('js/core/touch.js'), context);

for (const [w, h] of [[320,568], [360,640], [390,844], [430,932], [844,390]]) {
  context.innerWidth = w; context.innerHeight = h;
  for (const n of [1, 2, 4, 6]) {
    const layout = G.Touch.controlLayout(w, h, n);
    const slots = layout.slots, first = slots[0], last = slots.at(-1);
    assert.equal((first.x + last.x + last.w) / 2, w / 2, 'Skill row must be centered');
    assert(slots.every(slot => slot.y === first.y), 'Skills must share one row');
    assert(Math.abs(first.y + first.h - (h - 34 - 18)) < 1e-8, 'Row must respect bottom safe area');
    assert(layout.item.y + layout.item.h < first.y, 'Item must sit above skills');
    assert(first.x - first.w * .06 >= 0, 'Enlarged first skill must fit');
    assert(last.x + last.w * 1.06 <= w, 'Enlarged last skill must fit');
    assert(first.w * .06 + 2 < layout.GAP, 'Enlarged touch area must not reach neighbor');
  }
}
context.innerWidth = 390; context.innerHeight = 844;
settings.padPortrait = { bar: [.45, .65] };
const custom = G.Touch.controlLayout(390, 844, 4);
assert.equal(custom.bar.x + custom.bar.w / 2, 390 * .45, 'Keep custom control position');
assert.equal(custom.bar.y + custom.bar.h / 2, 844 * .65);
assert.equal(G.Touch.controlLayout(390, 844, 4, { defaults: true }).bar.x + custom.bar.w / 2, 195);

const notices = [];
G.UI = { toast: (...args) => notices.push(args) };
G.Projectiles = { clearOrbs() {} };
G.Audio = { sfx() {} };
G.FX = { ring() {}, dmgText() {} };
G.U = { TYPE_COLOR: { fire: '#f00' } };
G.LIFT = 1;
vm.runInNewContext(read('js/entities/player.js'), context);
const player = Object.create(G.Player.prototype);
const move = name => ({ name, type: 'fire', cd: 1, t: 1 });
Object.assign(player, { active: 0, slots: [[move('A')], [move('B')], [move('C'), move('D')]],
  hasItem: () => false, x: 0, y: 0, bodyH: 1, r: 1 });
player.setActive(1);
assert.equal(player.active, 1);
assert.deepEqual(notices.pop(), ['Cambiado a: B', 1600]);
player.setActive(1);
assert.equal(notices.length, 0, 'Repeated tap must not show a new notice');
player.hasItem = () => true;
player.setActive(0);
assert.equal(player.active, 1);
assert.equal(notices.length, 0, 'Blocked switch must not claim success');
player.hasItem = () => false;
player.setActive(2);
assert.deepEqual(notices.pop(), ['Cambiado a: C + D', 1600]);
player.remote = true;
player.setActive(0);
assert.equal(notices.length, 0, 'Remote player must not show a local notice');
console.log('Mobile skill layout and switch feedback checks passed');
