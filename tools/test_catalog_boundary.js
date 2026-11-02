/* An architectural regression gate for the mutable-picker failure class. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const ROOT = path.join(__dirname, '..');
const writers = new Set(['.omx/digimon.js', '.omx/digimon-evolution.js', '.omx/naruto.js']);
function violations(file, source) {
  if (file === 'js/core/catalog.js' || file === 'js/data/pokedex.js') return [];
  const code = source.replace(/\/\*[\s\S]*?\*\/|\/\/[^\n]*/g, comment => comment.replace(/[^\n]/g, ' '));
  const errors = [];
  for (const match of code.matchAll(/\bG\.(DEX|STARTERS)\b/g)) {
    const tail = code.slice(match.index);
    const line = code.slice(code.lastIndexOf('\n', match.index) + 1, code.indexOf('\n', match.index) < 0 ? undefined : code.indexOf('\n', match.index));
    if (writers.has(file) && /^G\.(DEX|STARTERS)\.push\(/.test(tail)) continue;
    if (file === 'js/data/starters.js' && (/^G\.STARTERS = \[/.test(tail) || line.includes('for (const s of G.STARTERS) G.STARTER_BY[s.dex] = s;'))) continue;
    errors.push(`${file}: ambiguous ${match[0]} collection read/write`);
  }
  if (/Object\.(values|entries)\s*\(\s*G\.DEX_BY\s*\)/.test(code)) errors.push(`${file}: use Catalog.all() for full enumeration`);
  return errors;
}
assert(violations('.omx/naruto.js', 'G.DEX.splice(0,G.DEX.length,...G.DEX.filter(p=>p.naruto));').length);
assert(violations('js/systems/rift.js', 'const pool=G.DEX.filter(p=>p.leg);').length);
assert(violations('js/systems/rift.js', 'Object.values(G.DEX_BY).filter(p=>p.leg);').length);
assert.equal(violations('.omx/naruto.js', 'G.DEX.push(mon);G.DEX_BY[mon.dex]=mon;').length, 0);
assert.equal(violations('js/systems/rift.js', '// G.DEX.filter is a previous bug\nG.Catalog.all();').length, 0);
const files = execFileSync('git', ['ls-files', '-z', '--', 'js', '.omx', 'tools/export_data.js'], { cwd: ROOT }).toString().split('\0')
  .filter(file => file.endsWith('.js') && file !== 'js/app.min.js' && !file.startsWith('.omx/state/'));
const errors = files.flatMap(file => violations(file, fs.readFileSync(path.join(ROOT, file), 'utf8')));
assert.deepEqual(errors, [], errors.join('\n'));
for (const file of ['dev.html', '.omx/digimon.html']) {
  const sources = [...fs.readFileSync(path.join(ROOT, file), 'utf8').matchAll(/<script\b[^>]*\bsrc="([^"?]+)(?:\?[^"]*)?"/g)].map(match => match[1]);
  assert.equal(sources.filter(source => source === 'js/core/catalog.js').length, 1, file);
  assert(sources.indexOf('js/data/pokedex.js') < sources.indexOf('js/core/catalog.js'), file);
  assert(sources.indexOf('js/core/catalog.js') < sources.indexOf('js/data/achievements.js'), file);
}
console.log('Runtime consumers use explicit catalog scopes; destructive filtering fixture is rejected.');
