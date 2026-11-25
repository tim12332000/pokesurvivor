const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
let reads=0,paths=0;
const context={imageSmoothingEnabled:false,save(){},restore(){},translate(){},scale(){},drawImage(){},setTransform(){},fillRect(){},beginPath(){},lineTo(){},moveTo(){},closePath(){},clip(){},getImageData(x,y,w,h){reads++;const data=new Uint8ClampedArray(w*h*4);for(let y=4;y<28;y++)for(let x=8;x<24;x++)data[(y*w+x)*4+3]=255;return {data};}};
const G={World:{},Sprites:{PX:1,sheet(){return {ready:true,img:{src:'fixture.png'}}},animMeta(){return {n:1,r:1,w:32,h:32,ax:16,ay:28}}}};
vm.runInNewContext(fs.readFileSync('art-review/shikamaru/reference-shadow-geometry.js','utf8'),{G,document:{createElement(){return {width:0,height:0,getContext(){return context}}}},Math,Map,WeakMap,WeakSet});
const R=G.ShikamaruReferenceGeometry,actor={dex:19,x:0,y:0,r:10,anim:{cur:'Idle',frame:0,dir:0,scale:1}},clear=(ax,ay,bx)=>{paths++;return bx<30};
const p=R.project(actor,1,0,100,.7,()=>true);
assert.equal(reads,1,'only source frame may be read');
assert(p.points.length<=32,'contact candidates must be bounded');
assert(R.contains(p,50,0),'inverse alpha must find silhouette');
assert(!R.contains(p,50,20),'inverse alpha must reject empty space');
const poly=[{x:48,y:-2},{x:52,y:-2},{x:52,y:2},{x:48,y:2}];
assert(R.groundContact(p,poly),'ground contact missing');
for(let i=0;i<100;i++){actor.x=i/10;R.beginFrame();const q=R.project(actor,1,0,100,.7,clear);assert(q.points.every(v=>v.x<30));R.groundContact(q,poly);assert(!R.contains(q,40,0));}
assert.equal(reads,1,'movement/projection/collision must not read pixels');
const body=R.bodyFor(actor),arc={target:actor,width:4};actor.x=100;
assert(R.sweptBody(arc,{x:0,y:0,z:12},{x:120,y:0,z:12},body,()=>true),'fast sweep tunnelled through body');
assert(!R.sweptBody(arc,{x:0,y:0,z:100},{x:120,y:0,z:100},body,()=>true),'overhead sweep falsely hit');
assert(!R.sweptBody(arc,{x:0,y:0,z:12},{x:120,y:0,z:12},body,()=>false),'wall sweep falsely hit');
actor.x=0;
const sourceAlpha=Array.from(body.data),sourceCanvas=body.canvas;
let materialMask;
for(let i=0;i<120;i++){
 const q=R.project(actor,1,0,100,.7,()=>true,{phase:i/30,seed:3});
 assert(R.contains(q,50,0),'flow lost the occupied source alpha');
 assert(!R.contains(q,50,20),'flow captured transparent space');
 assert(q.points.length<=32&&q.points.every(p=>R.contains(q,p.x,p.y)),'flow contacts are unbounded or outside actual alpha');
 materialMask??=body.shadowCanvas;
 assert.equal(body.shadowCanvas,materialMask,'moving flow rebuilt its source mask');
}
assert.equal(reads,1,'flow must not read pixels per moving frame');
assert.equal(body.canvas,sourceCanvas,'flow replaced the normal body source');
assert.deepEqual(Array.from(body.data),sourceAlpha,'flow mutated source alpha for other projections');
let readyBody;
for(let i=0;i<90;i++){
 actor.anim.frame=i%2;actor.anim.dir=i%4;
 const q=R.project(actor,0,1,64,1,()=>true,{phase:i/30,seed:3,readyBase:true});
 assert.equal(q.body.kind,'ready-base');readyBody??=q.body;
 assert.equal(q.body,readyBody,'body pose replaced the permanent ready base');
 assert(R.contains(q,actor.x,actor.y),'ready base detached from the feet');
 assert.equal(q.matrix.e,actor.x);assert.equal(q.matrix.f,actor.y);
 assert.equal(q.matrix.b,0);assert.equal(q.matrix.c,0);assert.equal(q.matrix.d,.65);
}
actor.anim.frame=0;actor.anim.dir=0;
assert.equal(R.bodyFor(actor),body,'ready base replaced the physical body mask');
assert.equal(reads,1,'ready base scanned sprite pixels instead of using its cached outline');
console.log(JSON.stringify({ok:true,sourcePixelReads:reads,movingProjections:100,maximumContactCandidates:32,pathQueries:paths}));
