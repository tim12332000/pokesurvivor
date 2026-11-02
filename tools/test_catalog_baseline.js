/* Fingerprints captured before the refactor lock full-roster ordering and RNG. */
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm'), crypto = require('node:crypto');
const G = { Ranking: { periodIds: () => ({ d:'2026-11-02', w:'2026-W45' }) } };
const context = vm.createContext({ G, window: { G } });
for (const file of ['js/core/util.js','js/data/pokedex.js','js/core/catalog.js','js/data/sprites-meta.js','js/data/moves.js',
  'js/data/starters.js','js/data/enemies.js','js/data/missions.js','js/data/achievements.js','js/systems/progress.js']) {
  vm.runInContext(fs.readFileSync(path.join(__dirname,'..',file),'utf8'),context);
}
const seed = () => vm.runInContext('letSeed=123456;Math.random=()=>((letSeed=(Math.imul(letSeed,1664525)+1013904223)>>>0)/4294967296)',context);
const digest = value => crypto.createHash('sha256').update(JSON.stringify(value)).digest('hex');
seed();
const encounters = { run:G.Enemies.rollRun(), hordes:G.Enemies.hordeTypes(500).map(t=>[t,G.Enemies.hordeDefs(t,500)]), upcoming:G.Enemies.upcomingDex(0,900) };
const missions = [];
for (let created=0;created<300;created++) { const save={created}; G.Progress.ensure(save); missions.push(save.missions); }
seed();
const personality=Array.from({length:20},(_,i)=>G.personalityResult({valiente:i%3,leal:i%5,sereno:i%7,alegre:i%4}));
assert.equal(digest(encounters),'f3c2e35ca388641d688041176f5b9445963e8d5adfa0c9fc333514c4378ced32');
assert.equal(digest(missions),'05836f1615bea021d0630013e6cf3ff1200d052f9696fa95d60d7587178caed5');
assert.equal(digest(personality),'150e07230e5e76df0a03203c84c953843c72cae2b707f4f0e47709788421f234');
assert.equal(digest(G.AchDefs.LIST.map(({id,goal})=>({id,goal}))),'60e7556f4d7803dbc22f791c138963d0603d4f1007babd32b9b07da5c0e1b292');
console.log('Pre-refactor encounter, mission, personality and achievement baselines are unchanged.');
