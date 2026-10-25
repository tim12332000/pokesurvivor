"""Native desktop/mobile acceptance for uncapped, visible-area Universal Pull."""
import base64
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame

OUT = Path(__file__).resolve().parents[1] / '.omx/state/pain-gravity-all'

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,moves=p.moves,out={};
 p.moves=moves.filter(m=>m.id==='naruto-pain-gravity');const m=p.moves[0];
 const start=()=>{A.ready('gravity');A.advance();const f=A.actions().find(f=>f.kind==='gravity');A.assert(f&&!f.immediate&&f.phase==='pull','every trigger must begin the pull phase');return f};
 const complete=f=>{for(let i=0;i<40&&A.actions().includes(f);i++)A.advance();A.assert(!A.actions().includes(f),'pull did not complete after .35 seconds')};
 const settle=()=>A.finish(.26);
 const hitsOnly=h=>h.filter(v=>v.id===m.id);
 try {
  A.assert(m.range===400&&m.triggerRadius===400&&m.pullRadius===100&&m.radius===300&&m.pushRadius===380&&m.pushDuration===.24&&m.cd===3,'gravity configuration');
  out.boundaries=[];
  for(const radius of [70,90,100,299,300,301,399,400,401]) {
   A.reset();const e=A.spawn(radius,0),hits=A.watch([e]);A.ready('gravity');A.advance();
   const action=A.actions().find(f=>f.kind==='gravity');
   A.assert(!!action===(radius<=400),'400 trigger boundary '+radius);
   if(action){
    A.assert(!action.immediate&&action.phase==='pull','close enemy skipped Universal Pull '+radius);
    A.finish(.30);A.assert(!hitsOnly(hits).length&&A.actions().includes(action),'damage before .35 second pull completed '+radius);
    complete(action);
   }
   const pulled=radius<=400?Math.max(0,radius-100):0,afterPull=radius-pulled,n=hitsOnly(hits).length,damaged=radius<=400&&afterPull<=300;
   A.assert(n===(damaged?1:0),'post-pull 300 damage boundary '+JSON.stringify({radius,x:e.x,hits:n,pulled:action?.pulls[0]?.distance}));
   A.assert(Math.abs(e.x-afterPull)<1e-6,'pull must reach its endpoint before physical push '+radius);
   A.assert(radius<=400?m.t>2.6:m.t===0,'cooldown boundary '+radius);
   settle();A.assert(Math.abs(e.x-(damaged?380:afterPull))<1e-6,'push must finish at radius 380, not add 380 '+radius);
   A.assert(hitsOnly(hits).length===n,'push flight duplicated release damage');out.boundaries.push({radius,triggered:!!action,pulled,hits:n,x:e.x});
  }
  A.reset();const crowd=Array.from({length:32},(_,i)=>A.spawn(Math.cos(i*Math.PI/16)*380,Math.sin(i*Math.PI/16)*380)),outside=A.spawn(401,0),hs=A.watch([...crowd,outside]);
  complete(start());A.assert(hitsOnly(hs).length===32&&hitsOnly(hs).every(v=>v.owned),'uncapped owned group hit');
  A.assert(crowd.every(e=>Math.abs(Math.hypot(e.x,e.y)-100)<1e-6),'uncapped crowd did not finish gathering before push');settle();
  A.assert(crowd.every(e=>Math.abs(Math.hypot(e.x,e.y)-380)<1e-6)&&outside.x===401,'uncapped group displacement');
  A.finish(.8);A.assert(hitsOnly(hs).length===32,'duplicate gravity damage');out.crowd=32;
  A.reset();const regular=A.spawn(200,0),boss=A.spawn(-200,0,true),fly=A.spawn(0,200),jump=A.spawn(0,-200);fly.flying=true;jump.jumpLift=18;jump.jumpT=.8;
  const airHits=A.watch([regular,boss,fly,jump]);complete(start());
  A.assert(hitsOnly(airHits).length===4,'airborne or boss omitted from damage');
  settle();A.assert(Math.abs(regular.x-380)<1e-6&&Math.abs(boss.x+226.25)<1e-6&&fly.y===200&&jump.y===-200&&jump.jumpLift===18,'native displacement resistance');out.resistance=true;
  out.special=[];
  for(const flag of ['boss','elite','legend','judge']){
   A.reset();const target=A.spawn(200,0),h=A.watch([target]);target[flag]=true;complete(start());
   A.assert(Math.abs(target.x-175)<1e-6,'quarter initial pull budget failed '+flag);settle();
   A.assert(Math.abs(target.x-226.25)<1e-6&&hitsOnly(h).length===1,'quarter push resistance failed '+flag);out.special.push(flag);
  }
  A.reset();const airEdge=A.spawn(300,0),airOutside=A.spawn(301,0);airEdge.flying=airOutside.flying=true;const boundaryHits=A.watch([airEdge,airOutside]);complete(start());
  settle();A.assert(airEdge.x===300&&airOutside.x===301&&hitsOnly(boundaryHits).length===1,'unpulled airborne damage boundary must remain 300');out.airBoundary=true;
  A.reset();const farBoss=A.spawn(400,0,true),bossHits=A.watch([farBoss]);complete(start());
  settle();A.assert(Math.abs(farBoss.x-325)<1e-6&&!hitsOnly(bossHits).length,'resistant outer target was pulled fully or damaged outside 300');out.farBoss={x:farBoss.x,hits:bossHits.length};
  A.reset();const eased=A.spawn(400,0),easeAction=start(),samples={0:eased.x};
  for(let i=1;i<=34;i++){A.advance();samples[i]=eased.x}
  const first=samples[0]-samples[1],middle=samples[17]-samples[18],last=samples[33]-samples[34];
  A.assert(first>0&&middle>first&&last>middle&&last>first*30,'pull must accelerate throughout instead of decelerating near its end');
  complete(easeAction);A.assert(Math.abs(eased.x-100)<1e-6,'full 300-unit pull failed');out.easing={first,middle,last,samples,totalPull:300};
  const pushSamples=[eased.x];for(let i=0;i<24;i++){A.advance();pushSamples.push(eased.x)}
  const early=pushSamples[1]-pushSamples[0],late=pushSamples[24]-pushSamples[23];
  A.assert(early>0&&late>early*20&&Math.abs(pushSamples[12]-170)<1e-6&&Math.abs(eased.x-380)<1e-6,'physical push must accelerate quadratically to radius 380');
  out.pushAcceleration={early,late,half:pushSamples[12],endpoint:eased.x,samples:pushSamples};
  A.reset();const halfTarget=A.spawn(400,0),halfAction=start();A.advance(.175);
  A.assert(Math.abs(halfTarget.x-325)<1e-6&&A.actions().includes(halfAction),'halfway pull must cover one quarter of the gather distance');out.easing.half=halfTarget.x;complete(halfAction);
  out.frameSteps=[];
  for(const dt of [.01,1/30,.07]){
   A.reset();const target=A.spawn(400,0),h=A.watch([target]),action=start();let steps=0;
   while(A.actions().includes(action)&&steps<40){A.advance(dt);steps++}
   A.assert(!A.actions().includes(action)&&Math.abs(target.x-100)<1e-6&&hitsOnly(h).length===1,'pull endpoint depends on frame rate '+dt);
   for(let elapsed=0;elapsed<.25;elapsed+=dt)A.advance(dt);
   A.assert(Math.abs(target.x-380)<1e-6&&hitsOnly(h).length===1,'physical push endpoint depends on frame rate '+dt);
   out.frameSteps.push({dt,steps,x:target.x,hits:h.length});
  }
  A.reset();const moving=A.spawn(350,40),movingHits=A.watch([moving]),movingAction=start();moving.spd=60;let nativeUpdates=0;
  while(A.actions().includes(movingAction)&&nativeUpdates<40){moving.update(.01,p);nativeUpdates++;G.EnemyMgr.rebuildGrid();A.advance()}
  A.assert(!A.actions().includes(movingAction)&&Math.abs(Math.hypot(moving.x,moving.y)-100)<1e-6&&hitsOnly(movingHits).length===1,'moving native target did not converge to 100 before push');
  for(let i=0;i<24;i++){moving.update(.01,p);nativeUpdates++;G.EnemyMgr.rebuildGrid();A.advance()}
  A.assert(Math.abs(Math.hypot(moving.x,moving.y)-380)<1e-6&&hitsOnly(movingHits).length===1,'native pursuit defeated physical push endpoint');
  out.moving={nativeUpdates,radius:Math.hypot(moving.x,moving.y),hits:movingHits.length};
  A.reset();const leaving=A.spawn(350,0),valid=A.spawn(-200,0),rangeHits=A.watch([leaving,valid]);const rangeAction=start();leaving.x=450;complete(rangeAction);
  A.assert(leaving.x===450&&rangeAction.pulls.find(v=>v.target===leaving).distance===0&&hitsOnly(rangeHits).length===1,'per-target range revalidation failed');out.targetRange=true;
  A.reset();const blocked=A.spawn(350,0),W=G.World,old=W.projectileBlock;
  W.projectileBlock=(x,y)=>x>=250&&x<=270?{destructible:false}:false;
  try{A.ready('gravity');A.advance();A.assert(!A.actions().length&&m.t===0,'blocked enemy triggered')}finally{W.projectileBlock=old}
  A.reset();const inner=A.spawn(250,0),block=W.projectileBlock;A.spawn(-350,0);const wallHits=A.watch([inner]);start();
  W.projectileBlock=(x,y)=>x>=100&&x<=120?{destructible:false}:false;
  try{complete(A.actions().find(f=>f.kind==='gravity'));A.assert(!hitsOnly(wallHits).length&&inner.x===250,'pull or push crossed wall')}finally{W.projectileBlock=block}out.wall=true;
  A.reset();const swept=A.spawn(350,0),sweepHits=A.watch([swept]);complete(start());const free=W.isFree;
  W.isFree=(x,...rest)=>x>=220&&x<=240?false:free.call(W,x,...rest);
  try{settle();A.assert(swept.x>100&&swept.x<220&&hitsOnly(sweepHits).length===1,'physical push crossed a wall introduced after release')}finally{W.isFree=free}out.pushWall=swept.x;
  A.reset();const anchored=A.spawn(350,0);complete(start());const ownerX=p.x;p.x+=100;
  try{settle();A.assert(Math.abs(anchored.x-380)<1e-6,'push radius followed moving Tendo instead of release origin')}finally{p.x=ownerX}out.releaseAnchor=true;
  A.reset();A.spawn(400,0);const f=start(),age=f.age,t=m.t;
  G.Combat.tick(.5,p,0);G.Combat.updateFields(.5);A.assert(f.age===age&&m.t===t,'pause advanced push');
  p.frozen=true;try{A.advance(.5);A.assert(f.age===age&&m.t===t,'frozen push advanced')}finally{p.frozen=false}
  complete(f);out.pauseFreeze=true;
  const push=P.effects.find(e=>e.kind==='push'),pushAge=push.age,pushEnemy=G.EnemyMgr.all()[0],pushX=pushEnemy.x;
  G.Combat.tick(.1,p,0);G.Combat.updateFields(.1);A.assert(push.age===pushAge&&pushEnemy.x===pushX,'paused physical push advanced');
  p.frozen=true;try{A.advance(.1);A.assert(push.age===pushAge&&pushEnemy.x===pushX,'frozen physical push advanced')}finally{p.frozen=false}
  settle();A.assert(Math.abs(pushEnemy.x-380)<1e-6,'physical push failed after resume');out.pushPauseFreeze=true;
  p.moves=[m,moves.find(v=>v.id==='naruto-pain-planet')];A.reset();A.spawn(200,0,true);A.ready('planet');A.advance();A.assert(P.snapshot(p).sharedRecovery===5,'planet did not create shared recovery');p.moves=[m];A.ready('gravity');A.advance();
  A.assert(!A.actions().some(f=>f.kind==='gravity'),'shared planet recovery bypassed');A.finish(4.9);A.assert(!A.actions().length,'shared recovery expired early');A.finish(.12);A.assert(P.snapshot(p).castCounts.gravity===1,'shared recovery did not resume');out.sharedRecovery=true;
  out.cleanup=[];
  for(const reason of ['clear','world','owner-death']) {
   A.reset();const e=A.spawn(200,0),h=A.watch([e]);start();const world=G.World,n=P.actorsFor(p).find(b=>b.path==='naraka');
   if(reason==='clear')G.Combat.clearFields();else if(reason==='world')G.World={...world};else{n.dead=true;p.dead=true}
   try{A.advance();A.assert(!A.actions().length&&!hitsOnly(h).length,'cancelled combo damaged '+reason)}finally{G.World=world;p.dead=false}
   out.cleanup.push(reason);
  }
  out.pushCleanup=[];
  for(const reason of ['clear','world','owner-death','skill-removed']){
   A.reset();const target=A.spawn(350,0),h=A.watch([target]);complete(start());const x=target.x,world=G.World;
   if(reason==='clear')G.Combat.clearFields();else if(reason==='world')G.World={...world};else if(reason==='owner-death'){P.actorsFor(p).find(b=>b.path==='naraka').dead=true;p.dead=true}else p.moves=[];
   try{A.advance(.3);A.assert(target.x===x&&hitsOnly(h).length===1,'cancelled physical push moved target or repeated damage '+reason)}finally{G.World=world;p.dead=false;p.moves=[m]}
   out.pushCleanup.push(reason);
  }
  A.reset();A.spawn(250,0);const visual=start();
  const samplePose=()=>{const ctx=document.createElement('canvas').getContext('2d'),draw=G.PainArt.draw,calls=[];
    G.PainArt.draw=function(ctx,options,...rest){calls.push(options);return draw.call(this,ctx,options,...rest)};
    try{p.invuln=0;p.draw(ctx)}finally{G.PainArt.draw=draw}
    return calls.find(c=>c.path==='tendo');};
  const position={x:p.x,y:p.y},pullPose=P.gravityPoseFor(p),pullDraw=samplePose();
  A.assert(pullPose.phase==='pull'&&pullDraw.state==='special'&&pullDraw.time===0,'pull must hold the gathering palm pose');
  A.assert(p.x===position.x&&p.y===position.y,'pose rendering moved actual player');
  const c=document.createElement('canvas'),ctx=c.getContext('2d'),arcs=[],arc=ctx.arc.bind(ctx);ctx.arc=(...args)=>{arcs.push(args[2]);return arc(...args)};
  G.Combat.drawGroundFields(ctx);A.assert(arcs.includes(400)&&arcs.includes(300),'pull visual must mark outer 400 and inner 300');
  complete(visual);const e=P.effects.find(f=>f.kind==='push');A.assert(e,'native push visual missing');arcs.length=0;
  const pushPose=P.gravityPoseFor(p),pushDraw=samplePose();
  A.assert(pushPose.phase==='push'&&pushDraw.state==='special'&&pushDraw.time===.125,'push must hold the release palm pose');
  const previousCur=p.anim.cur;p.anim.cur='Hurt';
  try{A.assert(samplePose().state==='hurt','gravity pose suppressed native hurt')}finally{p.anim.cur=previousCur}
  const portrait=G.UI.spriteCanvas(30010,64,64),poseFor=P.gravityPoseFor;let uiPoseCalls=0;
  P.gravityPoseFor=function(...args){uiPoseCalls++;return poseFor.apply(this,args)};
  try{p.anim.draw(portrait.getContext('2d'),32,48)}finally{P.gravityPoseFor=poseFor}
  A.assert(G.Naruto.isPreview(portrait)&&uiPoseCalls===0,'gravity pose leaked into portrait');
  A.finish(.4);A.assert(!P.gravityPoseFor(p),'release pose did not finish');out.pose=true;
  G.PainSkillVFX.gravity.effect(ctx,{...e,age:0});A.assert(arcs.includes(300),'push visual radius differs from actual 300');out.visualRadius=300;
  return out;
 } finally {p.moves=moves;A.reset()}
}"""

SCENE = r"""() => {
 const A=Acceptance;A.reset();for(const [i,a] of [0,.8,1.7,2.6,3.5,4.4,5.3].entries())A.spawn(Math.cos(a)*(i%2?380:260),Math.sin(a)*(i%2?380:260));
 A.ready('gravity');A.finish(.16);
}"""

RENDER = r"""() => {
 const canvas=document.createElement('canvas');canvas.width=880;canvas.height=820;
 const ctx=canvas.getContext('2d');ctx.fillStyle='#23323d';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.translate(440,410);ctx.scale(.62,.62);ctx.imageSmoothingEnabled=false;
 G.Combat.drawGroundFields(ctx);
 const entities=[Acceptance.p(),...G.EnemyMgr.all(),...G.NarutoPain.actors()];entities.sort((a,b)=>a.y-b.y).forEach(e=>e.draw(ctx));
 G.Combat.drawAirFields(ctx);G.FX.draw(ctx);return canvas.toDataURL();
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, viewport, mobile in [('desktop', {'width': 1200, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
            context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
            outer = context.new_page()
            outer.on('pageerror', lambda error: report['errors'].append(str(error)))
            outer.goto(URL)
            frame = game_frame(outer)
            enter(frame)
            report['viewports'][label] = frame.evaluate(CHECK)
            frame.evaluate(SCENE)
            frame.evaluate(RENDER)  # Request the actual sprite assets before recording evidence.
            outer.wait_for_timeout(300)
            for phase in ['pull', 'push', 'fade']:
                if phase == 'push':
                    frame.evaluate('Acceptance.finish(.22)')
                if phase == 'fade':
                    frame.evaluate('Acceptance.finish(.08)')
                png = frame.evaluate(RENDER).split(',', 1)[1]
                (OUT / f'{label}-{phase}-combat.png').write_bytes(base64.b64decode(png))
                outer.screenshot(path=str(OUT / f'{label}-{phase}-game.png'), animations='disabled')
            print(label, 'all-target gravity PASS', flush=True)
            context.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Native all-target gravity PASS', flush=True)


if __name__ == '__main__':
    main()
