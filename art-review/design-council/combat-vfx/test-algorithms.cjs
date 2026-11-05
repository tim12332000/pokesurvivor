const assert=require('node:assert/strict');
const A=require('./algorithms.js');
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-7,`${a} != ${b}`);
const beam=A.clippedBeam({x:0,y:0},0,500,10,[{x:200,y:-50,w:20,h:100}]);
close(beam.length,190);assert(A.beamHit(beam,{x:100,y:8,r:1}));assert(!A.beamHit(beam,{x:250,y:0,r:5}));assert(!A.beamHit(beam,{x:100,y:30,r:5}));
assert.equal(A.rayBox({x:0,y:0},{x:0,y:1},{x:10,y:5,w:3,h:10}),null);
assert.equal(A.rayBox({x:12,y:8},{x:0,y:1},{x:10,y:5,w:3,h:10}),0);
const profile=A.beamProfile(beam,41);assert.deepEqual(profile,A.beamProfile(beam,41));assert(profile.every(p=>p.width<=beam.radius&&p.width>=0));
const s=[{x:0,y:0},{x:2,y:0},{x:0,y:2}],d=[{x:4,y:3},{x:8,y:4},{x:5,y:9}],m=A.affineTriangle(s,d);
s.forEach((p,i)=>{const q=A.transform(m,p);close(q.x,d[i].x);close(q.y,d[i].y);});assert.equal(A.affineTriangle([s[0],s[0],s[2]],d),null);
const mesh=A.skyMesh({x:10,y:20,w:300,h:200},6,4,1);assert.equal(mesh.triangles.length,48);assert.equal(new Set(mesh.triangles.flat()).size,35);assert(mesh.vertices.every(v=>Number.isFinite(v.dest.x)&&Number.isFinite(v.dest.y)));
assert.equal(A.skyMesh({x:10,y:20,w:300,h:200},3,2,1).triangles.length,12);
for(const v of [mesh.vertices[0],mesh.vertices[6],mesh.vertices[28],mesh.vertices[34]]){close(v.source.x,v.dest.x);close(v.source.y,v.dest.y);}
const r=A.reflect({x:2,y:-3},{x:0,y:1});close(r.x,2);close(r.y,3);close(Math.hypot(r.x,r.y),Math.hypot(2,-3));
const curve=A.arcLengthSamples([{x:0,y:0},{x:30,y:-100},{x:90,y:100},{x:120,y:0}],40);const lengths=curve.points.slice(1).map((p,i)=>Math.hypot(p.x-curve.points[i].x,p.y-curve.points[i].y));assert(Math.max(...lengths)/Math.min(...lengths)<1.07);
assert(A.ribbon(curve.points,7,.7,.3).every(p=>Number.isFinite(p.x)&&Number.isFinite(p.y)));
assert(A.fanHit({x:0,y:0},0,100,1,{x:50,y:0,r:5}));assert(!A.fanHit({x:0,y:0},0,100,1,{x:-50,y:0,r:5}));
const c=new A.CastClock(.4,1);assert(!c.advance(.3));assert(!c.advance(1,false));assert.equal(c.age,.3);assert(c.advance(.11));assert(!c.advance(2));assert.equal(c.events,1);c.reset();c.cancel();assert(!c.advance(2));
// The effective current engine does not add card-clone population from Quantity.
// Proposed eligibility receives only actual consuming moves, never a cloned flag.
assert.deepEqual(A.quantityBenefits(2,[]),[]);
const q=A.quantityBenefits(0,[{actor:'main',move:'spread',base:3,cap:9}])[0];assert.equal(q.before,3);assert.equal(q.after,3);assert.equal(q.nextChange,2);assert(q.eligible);
assert(!A.quantityBenefits(5,[{actor:'main',move:'spread',base:3,cap:9}])[0].eligible);
const inherited=A.quantityBenefits(2,[{actor:'main',move:'spread',base:3,cap:9},{actor:'clone1',move:'spread',base:3,cap:9}]);assert.equal(inherited[0].after,inherited[1].after);
const ledger=new A.PulseLedger(7),packet={runEpoch:7,owner:'main',castId:12,pulse:0};
assert(ledger.accept(packet,'outer'));assert(!ledger.accept(packet,'outer'));assert(ledger.accept({...packet,pulse:1},'outer'));assert(ledger.accept({...packet,owner:'clone1',castId:13},'outer'));ledger.nextRun(8);assert(!ledger.accept(packet,'outer'));
const primary=[{id:'a',x:0,y:0,primaryDirectDamage:100},{id:'b',x:10,y:0,primaryDirectDamage:200}],outer=[{id:'a',x:0,y:0},{id:'b',x:10,y:0},{id:'c',x:20,y:0},{id:'c',x:20,y:0}];
assert.deepEqual(A.outerSplash(primary,outer,60,.1),[{id:'c',damage:20}]);assert.deepEqual(A.outerSplash(primary.toReversed(),outer,60,.1),[{id:'c',damage:20}]);
for(const n of [1,3,10])for(const m of [0,3,20]){
 const p=Array.from({length:n},(_,i)=>({id:'p'+i,x:i,y:0,primaryDirectDamage:100})),o=Array.from({length:m},(_,i)=>({id:'o'+i,x:i,y:10}));
 const result=A.outerSplash(p,[...o,...p],60,.1);assert.equal(result.length,m);close(result.reduce((a,b)=>a+b.damage,0),m*10);
}
for(const dpr of [1,2])for(const camera of [{x:0,y:0},{x:75,y:-43}]){
 const worldToScreen={a:dpr,b:0,c:0,d:dpr,e:-camera.x*dpr,f:-camera.y*dpr};
 const composed=A.multiply(worldToScreen,m),point={x:.4,y:1.2},projected=A.transform(composed,point),expected=A.transform(worldToScreen,A.transform(m,point));close(projected.x,expected.x);close(projected.y,expected.y);
 const world=A.transform(A.inverse(worldToScreen),projected),mapped=A.transform(m,point);close(world.x,mapped.x);close(world.y,mapped.y);
}
const casts=[{castId:4,local:false,distance:20},{castId:2,local:true,distance:70},{castId:3,local:false,distance:30},{castId:1,local:false,distance:15}];
for(const low of [false,true]){const budget=A.allocateFolds(casts,low);assert.equal(budget.filter(c=>c.snapshot).length,low?1:2);assert.equal(budget.reduce((n,c)=>n+c.texturedTriangles,0),low?12:48);assert(budget.find(c=>c.castId===2).snapshot);assert(budget.filter(c=>!c.snapshot).every(c=>c.panels===2));assert.deepEqual(budget,A.allocateFolds(casts.toReversed(),low));}
console.log('PASS: beam bounds/seed; affine+DPR/camera; shared mesh/global budget; ribbon/clock; Quantity consumers; Splash primary/pulse/clone/epoch and n*m matrix.');
