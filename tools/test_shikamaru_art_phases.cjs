// Phase-local upper-body intent and independent walking legs share one waist.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const metadata=JSON.parse(fs.readFileSync('art-review/shikamaru-frames.json','utf8'));
const drawCalls=[];
const context={URL,Image:class{decode(){return Promise.resolve()}},document:{currentScript:{src:'http://test/art-review/shikamaru-art.js'},createElement(){return {getContext(){return {drawImage(){},fillRect(){}}}}}},fetch:async()=>({ok:true,json:async()=>metadata}),window:{},G:{Sprites:{dirFromAngle:a=>a===Math.PI/2?0:a===-Math.PI/2?4:Math.abs(a)===Math.PI?6:2}}};
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
 for(const phase of ['drag','blast','finish','recover']){
  const frame=art.sample('cast',.1,'up',pose(phase,{moving:true}));
  assert.equal(frame.key,'backRun2');assert.equal(frame.lowerFrame,undefined);
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
 const directions=[['down',Math.PI/2,'front'],['up',-Math.PI/2,'back'],['right',0,''],['left',Math.PI,'']];
 for(const [moveDir,,movePrefix]of directions)for(const [aimDir,aim,aimPrefix]of directions){
  const frame=art.sample('cast',.1,moveDir,pose('sewing',{kind:'sewing',stage:'rise',moving:true,aim,walkTime:.15}));
  assert.equal(frame.key,aimPrefix?aimPrefix+'Seal':'seal');
  assert.equal(frame.direction,aimDir);assert.equal(frame.lowerFrame.direction,moveDir);
  assert.equal(frame.lowerFrame.key,movePrefix?movePrefix+'Run2':'run2');
  assert.equal(frame.splitHeight,.30);
 }
 for(const [phase,key]of [['mass-charge','backPrepare'],['mass-seal','backSeal'],['mass-conduct','backSeal'],['mass-throw-prepare','backThrowPrepare'],['mass-throw-release','backThrowRelease'],['mass-throw-recover','backThrowRecover']]){
  const frame=art.sample('cast',.1,'down',pose(phase,{kind:'mass',moving:true,aim:-Math.PI/2,phaseAge:.25,phaseDuration:.32}));
  assert.equal(frame.key,key);assert.equal(frame.lowerFrame.key,'frontRun2');
 }
 for(const [phase,extra,key]of [['release',{kind:'trap',phaseAge:.02,phaseDuration:.22},'throwRelease'],['net',{phaseAge:.5},'seal'],['checkmate',{kind:'checkmate',phaseAge:.5},'seal']]){
  const frame=art.sample('cast',.1,'up',pose(phase,{...extra,moving:true,aim:0}));
  assert.equal(frame.key,key);assert.equal(frame.lowerFrame.key,'backRun2');
 }
 const recovery=art.sample('cast',.1,'up',pose('sewing',{kind:'sewing',stage:'recover',moving:true,aim:0}));
 assert.equal(recovery.key,'backRun2');assert.equal(recovery.lowerFrame,undefined);
 assert.equal(art.sample('hurt',1,'up',pose('mass-conduct',{kind:'mass'})).key,'hurt');
 for(const state of ['hurt','faint','death'])assert.equal(art.sample(state,1,'up',pose('mass-conduct',{kind:'mass',moving:true,aim:0})).lowerFrame,undefined);
 let drawing={clips:[],scales:[]},path=null;const stack=[];
 const ctx={globalAlpha:1,save(){stack.push({drawing:{clips:drawing.clips.slice(),scales:drawing.scales.slice()},alpha:this.globalAlpha})},restore(){const saved=stack.pop();drawing=saved.drawing;this.globalAlpha=saved.alpha},translate(){},scale(...args){drawing.scales.push(args)},beginPath(){path=null},rect(...args){path=args},clip(){drawing.clips.push(path)},drawImage(...args){drawCalls.push({args,clips:drawing.clips.slice(),scales:drawing.scales.slice()})}};
 art.draw(ctx,{}, {state:'cast',time:.1,dir:4,pose:pose('drag',{moving:true,aim:0})});
 const expected=metadata.sheets.body.frames.backRun2.rect;
 assert.deepEqual(drawCalls.at(-1).args.slice(1,5),expected);
 const livePose=pose('mass-conduct',{kind:'mass',moving:true,aim:Math.PI}),actor={anim:{frame:1,t:.02,dir:4}},options={state:'cast',time:50,dir:4,pose:livePose,x:100,y:200,height:64};
 const before=JSON.stringify({actor,options,metadata}),count=drawCalls.length;
 art.draw(ctx,actor,options);
 assert.equal(drawCalls.length,count+2);assert.equal(JSON.stringify({actor,options,metadata}),before,'draw mutated actor, pose or atlas metadata');
 const lower=drawCalls.at(-2),upper=drawCalls.at(-1),k=64/92;
 assert.deepEqual(lower.args.slice(1,5),expected);assert.deepEqual(upper.args.slice(1,5),metadata.sheets.body.frames.seal.rect);
 assert.deepEqual(lower.scales.at(-1),[k,k]);assert.deepEqual(upper.scales.at(-1),[-k,k]);
 assert.equal(lower.clips.length,1);assert.equal(upper.clips.length,1);
 const waist=200-64*.30;
 assert.ok(lower.clips[0][1]<waist&&upper.clips[0][1]+upper.clips[0][3]>waist,'waist seam has a gap');
 assert.ok(upper.clips[0][1]+upper.clips[0][3]-lower.clips[0][1]<=1.01,'upper and lower bodies overlap beyond one display pixel');
 livePose.phaseAge=.01;livePose.age=0;art.draw(ctx,actor,{...options,time:0});
 assert.deepEqual(drawCalls.at(-2).args.slice(1,5),expected,'new effect phase restarted the leg cycle');
 actor.anim.frame=2;art.draw(ctx,actor,{...options,time:0});
 assert.deepEqual(drawCalls.at(-2).args.slice(1,5),metadata.sheets.body.frames.backRun1.rect,'walking legs did not advance with actor animation');
 const sampled=art.sample('cast',.1,'left',pose('sewing',{kind:'sewing',moving:true,stage:'descent',aim:Math.PI/2}));
 const sampleBefore=JSON.stringify(sampled);art.paint(ctx,sampled,{x:100,y:200,height:64});
 assert.equal(JSON.stringify(sampled),sampleBefore,'shared mask paint mutated sample');
 assert.equal(stack.length,0,'composite leaked canvas state');assert.equal(ctx.globalAlpha,1);
 console.log('Shikamaru phase art regressions passed');
})().catch(error=>{console.error(error);process.exitCode=1});
