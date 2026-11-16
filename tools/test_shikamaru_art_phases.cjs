// Regression: plan age must not replace phase-local timing, and moving plans
// must preserve leg articulation and the player's movement facing.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const metadata=JSON.parse(fs.readFileSync('art-review/shikamaru-frames.json','utf8'));
const drawCalls=[];
const context={URL,Image:class{decode(){return Promise.resolve()}},document:{currentScript:{src:'http://test/art-review/shikamaru-art.js'},createElement(){return {getContext(){return {drawImage(){},fillRect(){}}}}}},fetch:async()=>({ok:true,json:async()=>metadata}),window:{},G:{Sprites:{dirFromAngle:a=>a===Math.PI/2?0:a===-Math.PI/2?4:2}}};
context.window.G=context.G;
vm.runInNewContext(fs.readFileSync('art-review/shikamaru-art.js','utf8'),context);
(async()=>{
 const art=context.G.ShikamaruArt;await art.load();
 const pose=(phase,extra={})=>({phase,phaseAge:.2,phaseDuration:1,kind:'shadow',moving:false,age:50,...extra});
 assert.equal(art.sample('cast',50,'down',pose('prepare')).key,'frontPrepare');
 assert.equal(art.sample('cast',50,'up',pose('release')).key,'backSeal');
 assert.equal(art.sample('cast',50,'right',pose('net',{phaseAge:.1})).key,'prepare');
 assert.equal(art.sample('cast',50,'right',pose('net',{phaseAge:.5})).key,'seal');
 assert.equal(art.sample('cast',50,'down',pose('finish',{phaseAge:.95})).key,'frontIdle');
 for(const phase of ['drag','net','blast','finish','recover','sewing']){
  assert.equal(art.sample('cast',.1,'up',pose(phase,{moving:true})).key,'backRun2');
 }
 assert.equal(art.sample('cast',50,'up',pose('recover',{kind:'trap'})).key,'backThrowRecover');
 assert.equal(art.sample('cast',50,'down',pose('release',{kind:'trap',phaseAge:.02,phaseDuration:.22})).key,'frontThrowRelease');
 assert.equal(art.sample('cast',50,'down',pose('release',{kind:'trap',phaseAge:.2,phaseDuration:.22})).key,'frontThrowRecover');
 assert.equal(art.sample('cast',50,'down',pose('sewing',{kind:'sewing',phaseAge:.05})).key,'frontPrepare');
 assert.equal(art.sample('cast',50,'down',pose('sewing',{kind:'sewing',phaseAge:.4})).key,'frontSeal');
 assert.equal(art.sample('cast',50,'down',pose('sewing',{kind:'sewing',phaseAge:.8})).key,'frontSeal');
 assert.equal(art.sample('cast',50,'up',pose('finish',{kind:'strangle',phaseAge:.2})).key,'backCrouch');
 assert.equal(art.sample('cast',50,'up',pose('finish',{kind:'strangle',phaseAge:.5})).key,'backSeal');
 assert.equal(art.sample('cast',50,'up',pose('finish',{kind:'shadow',phaseAge:.2})).key,'backIdle');
 assert.equal(art.sample('cast',50,'down',pose('sewing',{kind:'sewing',stage:'ground',phaseAge:.05})).key,'frontPrepare');
 assert.equal(art.sample('cast',50,'down',pose('sewing',{kind:'sewing',stage:'rise',phaseAge:.2})).key,'frontSeal');
 assert.equal(art.sample('cast',50,'up',pose('sewing',{kind:'sewing',stage:'descent',phaseAge:.5})).key,'backSeal');
 assert.equal(art.sample('cast',50,'up',pose('sewing',{kind:'sewing',stage:'recover',phaseAge:.2})).key,'backIdle');
 assert.equal(art.sample('hurt',50,'right',pose('net')).key,'hurt');
 assert.equal(art.sample('cast',.05,'down',pose('mass-charge',{kind:'mass',phaseAge:.05,phaseDuration:.32})).key,'frontPrepare');
 assert.equal(art.sample('cast',.25,'up',pose('mass-charge',{kind:'mass',phaseAge:.25,phaseDuration:.32})).key,'backCrouch');
 for(const phase of ['mass-seal','mass-conduct'])assert.equal(art.sample('cast',.5,'down',pose(phase,{kind:'mass'})).key,'frontSeal');
 for(const [phase,key]of [['mass-throw-prepare','backThrowPrepare'],['mass-throw-release','backThrowRelease'],['mass-throw-recover','backThrowRecover']])assert.equal(art.sample('cast',1,'up',pose(phase,{kind:'mass'})).key,key);
 assert.equal(art.sample('cast',.1,'up',pose('mass-conduct',{kind:'mass',moving:true})).key,'backRun2');
 assert.equal(art.sample('hurt',1,'up',pose('mass-conduct',{kind:'mass'})).key,'hurt');
 const ctx={save(){},restore(){},translate(){},scale(){},drawImage(...args){drawCalls.push(args)}};
 art.draw(ctx,{}, {state:'cast',time:.1,dir:4,pose:pose('drag',{moving:true,aim:0})});
 const expected=metadata.sheets.body.frames.backRun2.rect;
 assert.deepEqual(drawCalls.at(-1).slice(1,5),expected);
 art.draw(ctx,{}, {state:'cast',time:.1,dir:4,pose:pose('mass-conduct',{kind:'mass',moving:true,aim:0})});
 assert.deepEqual(drawCalls.at(-1).slice(1,5),expected);
 console.log('Shikamaru phase art regressions passed');
})().catch(error=>{console.error(error);process.exitCode=1});
