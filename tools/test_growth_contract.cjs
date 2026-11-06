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
let p=hero(30013,['jjk-yuta']);
assert.equal(growth.quantityBenefit(p).eligible,false,'a lone sword is not a count consumer');
assert(!growth.legalOffers(p,100).some(c=>c.key==='stat:quantity'),'native card pool leaked no-op Quantity');
assert(!growth.legalOffers(p,100).some(c=>c.key==='stat:heal'),'full-health immediate heal leaked');
p.hp=80;assert(growth.legalOffers(p,100).some(c=>c.key==='stat:heal'),'injured player cannot choose heal');
// Having a card-created clone is not a count consumer.
G.SelfClones.actors=()=>[{sourceOwner:p}];assert.equal(growth.quantityBenefit(p).eligible,false);G.SelfClones.actors=()=>[];
p.addMove('jjk-yuta-rika');let yutaBenefit=growth.quantityBenefit(p);
assert.equal(yutaBenefit.consumers[0].before['協擊拳數'],4);assert.equal(yutaBenefit.consumers[0].after['協擊拳數'],5);
assert.equal(yutaBenefit.consumers[0].before['顯現拳數'],undefined,'unlearned manifestation promised full punches');
assert(growth.legalOffers(p,100).some(c=>c.key==='stat:quantity'),'Rika real combos did not enable quantity');
p.quantityPicks=p.quantityBonus=7;assert.equal(growth.quantityBenefit(p).eligible,false,'normal Rika cap offered a card for an unlearned form');
assert(!growth.legalOffers(p,100).some(c=>c.key==='stat:quantity'),'normal-only capped Rika offered quantity');
p.addMove('jjk-yuta-manifest');assert.equal(growth.quantityBenefit(p).eligible,false,'learning manifestation re-enabled a capped count card');
p.quantityPicks=p.quantityBonus=0;yutaBenefit=growth.quantityBenefit(p);
assert.equal(yutaBenefit.consumers[0].before['顯現拳數'],8);assert.equal(yutaBenefit.consumers[0].after['顯現拳數'],10);
p.quantityPicks=p.quantityBonus=7;assert.equal(growth.quantityBenefit(p).eligible,false,'Rika count card offered after both caps');
p=hero(30014,['jjk-ryu','jjk-ryu-spread']);
let b=growth.quantityBenefit(p);assert(b.eligible);assert.equal(b.consumers[0].before['追蹤砲彈'],8);assert.equal(b.consumers[0].after['追蹤砲彈'],10);assert.equal(b.consumers[0].nextChangeAt,1);
p.quantityPicks=p.quantityBonus=1;b=growth.quantityBenefit(p);assert.equal(b.consumers[0].after['追蹤砲彈'],12);
p.quantityPicks=p.quantityBonus=6;assert.equal(growth.quantityBenefit(p).eligible,false,'all Ryu count consumers capped at18');
assert(!growth.legalOffers(p,100).some(c=>c.key==='stat:quantity'));
const rankCases=[
 ['jjk-yuta',3,'relayMarkDuration',1.2],['jjk-yuta',5,'bladeArc',2.5],['jjk-yuta-rika',3,'rikaSpeed',760],['jjk-yuta-rika',5,'radius',250],
 ['jjk-yuta-rika',5,'range',600],['jjk-yuta-rika',3,'comboBase',6],['jjk-yuta-speech',5,'range',320],['jjk-yuta-speech',3,'speechDuration',2.4],['jjk-yuta-speech',5,'speechBossDuration',1],['jjk-yuta-manifest',3,'recovery',7],['jjk-yuta-manifest',5,'recovery',6],
 ['jjk-yuta-manifest',1,'duration',8],['jjk-yuta-resonance',3,'radius',300],['jjk-yuta-resonance',5,'radius',360],
 ['jjk-ryu',3,'targetPolicy','elite'],['jjk-ryu',5,'range',414],['jjk-ryu-spread',3,'range',920],['jjk-ryu-spread',5,'baseCount',10],
 ['jjk-ryu-impact',3,'radius',108],['jjk-ryu-impact',5,'range',330],['jjk-ryu-maximum',3,'firstTargetBonus',.15],
 ['jjk-ryu-maximum',1,'barrageBase',4],['jjk-ryu-maximum',3,'barrageBase',6],['jjk-ryu-maximum',5,'barrageBase',8],
 ['jjk-ryu-maximum',1,'radius',72],['jjk-ryu-maximum',3,'radius',96],['jjk-ryu-maximum',5,'radius',128],
 ['jjk-ryu-maximum',1,'range',760],['jjk-ryu-maximum',3,'range',880],['jjk-ryu-maximum',5,'range',1040],
 ['jjk-uro',3,'arc',1.8],['jjk-uro',5,'skyKnock',44],['jjk-uro-thin-ice',3,'arc',2.9],['jjk-uro-thin-ice',5,'thinSlow',.25],
 ['jjk-uro-screen',3,'threatHorizon',.8],['jjk-uro-screen',3,'reflectBudget',20],['jjk-uro-screen',5,'counterBase',8],['jjk-uro-collapse',3,'radius',270],['jjk-uro-collapse',5,'collapseSlow',.6],
 ['jjk-uro-echo',3,'echoBase',3],['jjk-uro-echo',5,'echoBase',4],['jjk-uro-screen',5,'duration',4.5]
];
for(const [id,r,key,value] of rankCases){const actual=G.Moves.instance(id,r)[key];if(typeof value==='number')assert(Math.abs(actual-value)<1e-9,id+':'+key);else assert.equal(actual,value,id+':'+key);}
p=hero(30014,['jjk-ryu-maximum']);b=growth.quantityBenefit(p);
assert.equal(b.consumers[0].before['追加重砲'],4);assert.equal(b.consumers[0].after['追加重砲'],5,'first quantity pick must add a real heavy shot');
assert(growth.legalOffers(p,100).some(c=>c.key==='stat:quantity'),'maximum-only build lost its quantity card');
p.moves[0]=G.Moves.instance('jjk-ryu-maximum',5);b=growth.quantityBenefit(p);
assert.equal(b.consumers[0].before['追加重砲'],8);assert.equal(b.consumers[0].after['追加重砲'],10);
p.quantityPicks=p.quantityBonus=4;assert.equal(growth.quantityBenefit(p).eligible,false,'barrage-only quantity should stop at sixteen followups');
p=hero(30015,['jjk-uro-thin-ice','jjk-uro-screen']);b=growth.quantityBenefit(p);
assert.equal(b.consumers.find(c=>c.id==='jjk-uro-thin-ice').after['裂面波次'],5);
const screen=b.consumers.find(c=>c.id==='jjk-uro-screen');assert.equal(screen.before['反射容量'],12);assert.equal(screen.after['反射容量'],15);assert.equal(screen.after['反擊波次'],5);
p.quantityPicks=p.quantityBonus=8;assert.equal(growth.quantityBenefit(p).eligible,false,'all fracture/screen consumers at cap still offered quantity');
// Upgrade previews use the current build's real count, including quantity rounding and caps.
const previewCases=[
 [30013,'jjk-yuta-rika',0,/協擊拳數 4→5/],
 [30014,'jjk-ryu-maximum',1,/追加重砲 5→6/],
 [30015,'jjk-uro-thin-ice',0,/裂面波次 4→5/],
 [30015,'jjk-uro-collapse',0,/裂面波次 4→5/],
 [30015,'jjk-uro-screen',0,/反射容量 12→16.*反擊波次 4→5.*持續秒數 3.5→3.75/],
 [30013,'jjk-yuta-manifest',0,/恢復秒數 8→7.5/]
];
for(const [dex,id,q,text]of previewCases){
 p=hero(dex,[id]);p.quantityPicks=p.quantityBonus=q;
 const card=growth.legalOffers(p,100).find(c=>c.key==='up:'+id);assert(card,'upgrade missing '+id);assert.match(card.desc,text,id);
 const before=growth.quantityBenefit(p),rankBefore=p.moves[0].lvl;assert.equal(rankBefore,1,'preview upgraded live move');
 card.apply(p);assert.equal(p.moves[0].lvl,2,'native upgrade failed '+id);
 if(before.eligible){const after=growth.quantityBenefit(p);assert(after.consumers.length,'upgrade lost count consumer '+id);}
}
p=hero(30013,['jjk-yuta-rika','jjk-yuta-manifest']);
assert.match(growth.legalOffers(p,100).find(c=>c.key==='up:jjk-yuta-rika').desc,/顯現拳數 8→10/);
p.quantityPicks=p.quantityBonus=20;
let capped=growth.legalOffers(p,100).find(c=>c.key==='up:jjk-yuta-rika');
assert(!/協擊拳數|顯現拳數/.test(capped.desc),'capped punches presented as rank gains');
p=hero(30015,['jjk-uro-echo']);p.moves[0]=G.Moves.instance('jjk-uro-echo',2);
assert.match(growth.legalOffers(p,100).find(c=>c.key==='up:jjk-uro-echo').desc,/殘響次數 2→3/);
p.quantityPicks=p.quantityBonus=20;
assert(!/殘響次數/.test(growth.legalOffers(p,100).find(c=>c.key==='up:jjk-uro-echo').desc),'capped echoes presented as rank gains');
for(const [dex,id] of [[30013,'jjk-yuta-resonance'],[30015,'jjk-uro-echo']]){
 p=hero(dex,[]);p.level=11;assert(!G.Moves.poolFor(p.mon).includes(id),'fifth skill leaked before level12');
 p.level=12;const learn=growth.legalOffers(p,100).find(c=>c.key==='new:'+id);assert(learn,'level12 linked skill missing');
 assert(learn.apply(p)!==false);const linked=p.moves.find(m=>m.id===id);assert(linked.passive&&!linked.autoCast&&!p.slots.length,'linked effect stole a manual slot');
}
// Native upgrade application must install the same functional rank, not only instance previews.
const live=G.Moves.instance('jjk-ryu-spread');G.Moves.levelUp(live);G.Moves.levelUp(live);assert.equal(live.range,920);
G.Moves.levelUp(live);G.Moves.levelUp(live);assert.equal(live.baseCount,10);assert.equal(live.range,1120);
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
