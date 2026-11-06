/* Perfect-form framing must fit real atlas bounds and restore the native camera. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const metadata = JSON.parse(fs.readFileSync(path.join(root, 'art-review/madara/frames.json'), 'utf8'));

function fixture(width, height, touch) {
  const player = {x:0, y:0, hp:100, mon:{dex:30016}, anim:{scale:1}, moves:[{id:'naruto-madara-susanoo'}]};
  let active = true, poseQueries = 0;
  const G = {Game:{player,state:'playing'}, World:{}, CombatPulse:{epoch:1},
    Settings:{touch,get:()=>false}, Touch:{active:touch}, MadaraArt:{metadata},
    Digimon:{records:new Map()}, UI:{sprite(){},spriteCanvas(){}},
    Sprites:{Animator:class {draw(){}},bodyHeight:()=>64,drawShadow(){}}};
  const activationWorld = G.World;
  G.NarutoMadara = {guardianPose(){poseQueries++;return active && G.World === activationWorld && G.CombatPulse.epoch === 1 ? {perfect:true,height:380} : null;}};
  const document = {getElementById:()=>({clientWidth:width,clientHeight:height})};
  const context = vm.createContext({G,window:{G},Math,document});
  for (const file of ['js/core/util.js', 'js/core/camera.js', '.omx/digimon-size.js', '.omx/naruto-madara-camera.js'])
    vm.runInContext(fs.readFileSync(path.join(root, file), 'utf8'), context, {filename:file});
  G.Camera.resize(width,height);
  const native = G.Camera.scale;
  const settle = () => {for(let i=0;i<180;i++)G.Camera.follow(player.x,player.y,1/60);};
  return {G,player,native,settle,stop:()=>{active=false;},queries:()=>poseQueries};
}

for (const [width,height,touch] of [[1280,900,false],[1000,800,false],[1300,700,false],[390,844,true],[360,800,true]]) {
  const f = fixture(width,height,touch), {G,player,native} = f;
  f.settle();
  const framed = G.MadaraFraming.inspect();
  assert(framed?.active, 'missing Perfect cue');
  const top = (player.y-framed.top-G.Camera.top())*G.Camera.scale;
  const bottom = (player.y+framed.bottom-G.Camera.top())*G.Camera.scale;
  assert(top >= Math.min(112,height*.18)-1, 'authored crest still clipped at '+width+': '+top);
  assert(bottom <= height-Math.min(112,height*.18)+1, 'owner/feet overlap bottom controls');
  assert(Math.abs(G.Camera.w*G.Camera.scale-width)<1e-6, 'horizontal world/screen conversion drift');
  assert(Math.abs(G.Camera.h*G.Camera.scale-height)<1e-6, 'vertical world/screen conversion drift');

  for (const state of ['paused','levelup']) {
    G.Game.state=state;
    const before=JSON.stringify([G.Camera.x,G.Camera.y,G.Camera.scale,G.Camera.w,G.Camera.h]);
    G.Camera.follow(100,100,.5);
    assert.equal(JSON.stringify([G.Camera.x,G.Camera.y,G.Camera.scale,G.Camera.w,G.Camera.h]),before,'paused framing drift');
  }
  G.Game.state='playing';f.stop();f.settle();
  assert(Math.abs(G.Camera.scale-native)<1e-6,'scale not restored after window');
  assert(Math.abs(G.Camera.y-player.y)<.01,'focus not restored after window');
}

for (const boundary of ['world','epoch','death','hero']) {
  const f=fixture(1280,900,false),{G,player,native}=f;f.settle();
  if(boundary==='world')G.World={};
  if(boundary==='epoch')G.CombatPulse.epoch++;
  if(boundary==='death')player.dead=true;
  if(boundary==='hero')player.mon={dex:30006};
  G.Camera.follow(player.x,player.y,1/60);
  assert(Math.abs(G.Camera.scale-native)<1e-6,'framing survived '+boundary);
  assert.equal(G.MadaraFraming.inspect(),null,'cue survived '+boundary);
}

const other=fixture(1280,900,false);other.player.mon={dex:30006};
other.G.Camera.follow(20,30,.1);
assert.equal(other.queries(),0,'another character queried the Madara cue');
assert.equal(other.G.Camera.x,other.G.U.damp(0,20,9,.1));
assert.equal(other.G.Camera.y,other.G.U.damp(0,30,9,.1));
console.log('PASS: authored Perfect bounds, desktop/portrait, pause, recovery and lifecycle; other heroes keep native framing.');
