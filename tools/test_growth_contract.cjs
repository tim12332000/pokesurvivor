/* Exercise production move ladders, training and card selection in a small roster. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..');let G;
class Player {
  constructor(mon){Object.assign(this,{mon,dex:mon.dex,level:1,hp:100,maxHp:100,atkMul:1,spdMul:1,cdMul:.76,dmgReduce:.16,magnet:100,xpMul:1.4,
    moves:[],slots:[],active:0,maxMoves:4,bind:{},banned:new Set(),statsTaken:{},bonds:0,anim:{scale:1}});}
  get atk(){return this.atkMul;} get spd(){return this.spdMul;}
  hasMove(id){return this.moves.some(m=>m.id===id);}
  activeGroup(){return this.slots[this.active]||[];}
  arrange(){} setActive(i){this.active=i;}
  addMove(id){if(this.hasMove(id)||this.slots.length>=this.maxMoves)return false;const m=G.Moves.instance(id);this.moves.push(m);if(!m.passive)this.slots.push([m]);return true;}
  bondOptions(){const loose=this.slots.filter(g=>g.length===1).map(g=>g[0]);return loose.length>=2?{mode:'pair',loose}:null;}
  heal(n){this.hp=Math.min(this.maxHp,this.hp+n);}
}
G={Player,Game:{state:'playing',st:{time:0},startRun(){}},Icons:{UI:{}},Naruto:{records:new Map([30013,30014,30015].map(d=>[d,{}]))},
  DEX_BY:Object.fromEntries([30013,30014,30015].map(d=>[d,{dex:d,name:String(d),naruto:true}])),
  NarutoSkillCatalog:{byDex:new Map(),definitions:new Map(),extraPools:new Map(),references:new Map()},Combat:{clearFields(){}},SelfClones:{actors:()=>[]}};
const context=vm.createContext({G,window:{G},Math,document:{querySelectorAll:()=>[],querySelector:()=>null}});
const load=file=>vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),context,{filename:file});
load('js/core/util.js');load('js/data/moves.js');load('js/systems/levelup.js');load('.omx/naruto-training.js');load('.omx/quantity.js');load('.omx/jujutsu.js');load('.omx/jujutsu-growth.js');
const growth=G.JujutsuGrowth;
function hero(dex,ids){const p=G.Game.player=new Player(G.DEX_BY[dex]);p.level=20;for(const id of ids)p.addMove(id);return p;}
let p=hero(30013,['jjk-yuta','jjk-yuta-rika']);
assert.equal(growth.quantityBenefit(p).eligible,false,'Yuta cannot use Quantity');
assert(!growth.legalOffers(p,100).some(c=>c.key==='stat:quantity'),'native card pool leaked no-op Quantity');
assert(!growth.legalOffers(p,100).some(c=>c.key==='stat:heal'),'full-health immediate heal leaked');
p.hp=80;assert(growth.legalOffers(p,100).some(c=>c.key==='stat:heal'),'injured player cannot choose heal');
// Having a card-created clone is not a count consumer.
G.SelfClones.actors=()=>[{sourceOwner:p}];assert.equal(growth.quantityBenefit(p).eligible,false);G.SelfClones.actors=()=>[];
p=hero(30014,['jjk-ryu','jjk-ryu-spread']);
let b=growth.quantityBenefit(p);assert(b.eligible);assert.equal(b.consumers[0].before['砲道'],3);assert.equal(b.consumers[0].after['砲道'],3);assert.equal(b.consumers[0].nextChangeAt,2);
p.quantityPicks=p.quantityBonus=1;b=growth.quantityBenefit(p);assert.equal(b.consumers[0].after['砲道'],4);
p.quantityPicks=p.quantityBonus=6;assert.equal(growth.quantityBenefit(p).eligible,false,'all Ryu count consumers capped at9');
assert(!growth.legalOffers(p,100).some(c=>c.key==='stat:quantity'));
const rankCases=[
 ['jjk-yuta',3,'relayMarkDuration',1.2],['jjk-yuta',5,'bladeArc',2.5],['jjk-yuta-rika',3,'rikaSpeed',650],['jjk-yuta-rika',5,'radius',126],
 ['jjk-yuta-speech',5,'range',184],['jjk-yuta-manifest',3,'recovery',10.5],['jjk-yuta-manifest',5,'recovery',9],
 ['jjk-ryu',3,'targetPolicy','elite'],['jjk-ryu',5,'range',414],['jjk-ryu-spread',3,'spreadStep',.8],['jjk-ryu-spread',5,'baseCount',4],
 ['jjk-ryu-impact',3,'radius',108],['jjk-ryu-impact',5,'range',330],['jjk-ryu-maximum',3,'firstTargetBonus',.15],
 ['jjk-uro',3,'arc',1.3],['jjk-uro',5,'skyKnock',44],['jjk-uro-thin-ice',3,'arc',2.1],['jjk-uro-thin-ice',5,'thinSlow',.25],
 ['jjk-uro-screen',3,'threatHorizon',.8],['jjk-uro-screen',3,'reflectRefresh',true],['jjk-uro-screen',5,'counterBonus',.15],['jjk-uro-collapse',3,'radius',126.5],['jjk-uro-collapse',5,'collapseSlow',.6]
];
for(const [id,r,key,value] of rankCases){const actual=G.Moves.instance(id,r)[key];if(typeof value==='number')assert(Math.abs(actual-value)<1e-9,id+':'+key);else assert.equal(actual,value,id+':'+key);}
// Native upgrade application must install the same functional rank, not only instance previews.
const live=G.Moves.instance('jjk-ryu-spread');G.Moves.levelUp(live);G.Moves.levelUp(live);assert.equal(live.spreadStep,.8);
G.Moves.levelUp(live);G.Moves.levelUp(live);assert.equal(live.baseCount,4);
p=hero(30013,['jjk-yuta']);const beforeStats=JSON.stringify(p.statsTaken);
const cards=growth.legalOffers(p,3);assert(cards.some(c=>c.type==='stat'));assert.equal(JSON.stringify(p.statsTaken),beforeStats,'preview spent growth');assert(!p.narutoMilestonesShown,'offer consumed first-display milestone');
const up=growth.legalOffers(p,100).find(c=>c.key==='up:jjk-yuta');assert.match(up.desc,/30→36/);assert.equal(p.moves[0].lvl,1);up.apply(p);assert.equal(p.moves[0].lvl,2);
// Structural no-fusion uses a real legal card and spends exactly one bond.
p.bonds=1;let reward=growth.bondState(p);assert.equal(reward.mode,'growth');assert(reward.options.length>0);
const chosen=reward.options.find(c=>c.type==='up')||reward.options[0];assert(growth.applyBondCard(p,chosen));assert.equal(p.bonds,0);assert.equal(growth.applyBondCard(p,chosen),false);
p.bonds=1;reward=growth.bondState(p);const stale=reward.options[0];p.hp-=1;
assert.equal(growth.applyBondCard(p,stale),false,'changed-state reward offer was reused');assert.equal(p.bonds,1,'stale card spent a bond');
// Capability probe handles a future-active character without hard-coded dexes.
for(const id of ['test-active-a','test-active-b'])G.Moves.BY_ID[id]={id,name:id,type:'normal',kind:'projectile',cd:1,dmg:1,count:1,learnLevel:6,maxLvl:2,ups:[{t:'up',m:{dmg:1.1}}]};
const mon={dex:45001,name:'future active',types:['normal']};G.NarutoSkillCatalog.byDex.set(mon.dex,G.Moves.BY_ID['test-active-a']);G.NarutoSkillCatalog.extraPools.set(mon.dex,['test-active-b']);
p=G.Game.player=new Player(mon);p.level=1;p.addMove('test-active-a');p.bonds=1;assert.equal(growth.bondState(p).mode,'bank');assert.equal(p.moves.length,1,'future probe mutated real player');assert.equal(p.slots.length,1);
p.addMove('test-active-b');assert.equal(growth.bondState(p).mode,'fusion');
console.log(JSON.stringify({ok:true,nativeCardContracts:true,functionalRankCases:rankCases.length,quantityConsumerAndCap:true,rewards:'fusion/bank/growth and single-spend'}));
