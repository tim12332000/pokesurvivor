"""Native missile trajectory regression and frames from actual battle rendering."""
import base64
import io
import json
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame

OUT = Path(__file__).resolve().parents[1] / '.omx/state/pain-missile-curve'

SETUP = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain;
 window.curveMoves=p.moves.slice();
 A.curveReset=()=>{p.moves=curveMoves.slice();A.reset();p.moves=p.moves.filter(m=>m.id==='naruto-pain-missiles');
  const b=P.actorsFor(p).find(b=>b.path==='asura');b.x=b.y=0;};
 A.curveCast=(x=240,y=0)=>{A.curveReset();const e=A.spawn(x,y);A.ready('missiles');
  for(let i=0;i<30&&!P.shots.some(s=>s.kind==='missile');i++)A.advance();
  const shot=P.shots.find(s=>s.kind==='missile');A.assert(shot,'native missile emission missing');return {e,shot};};
 A.curveSample=s=>({age:s.age,x:s.x,y:s.y,lift:s.lift,cruiseHeight:s.cruiseHeight,orbitRadius:s.orbitRadius,orbitDuration:s.orbitDuration,offset:s.launchOffset||0,
  visualAngle:s.visualAngle,angle:s.angle,distance:s.distance,phase:s.phase,
  trail:s.trail?JSON.parse(JSON.stringify(s.trail)):[]});
}"""

TRAJECTORY = r"""() => {
 const A=Acceptance,P=G.NarutoPain,{e,shot:s}=A.curveCast(),samples=[];
 const turn=(a,b)=>Math.abs(Math.atan2(Math.sin(a-b),Math.cos(a-b)));
 const ground={x:s.x,y:s.y};let previous=null,maxTurn=0,maxAlignmentError=0;
 for(let i=0;i<180&&P.shots.includes(s);i++){
  const now=A.curveSample(s);samples.push(now);
  A.assert(Number.isFinite(now.visualAngle),'missile has no projected flight angle');
  if(now.phase==='rise')A.assert(now.x===ground.x&&now.y===ground.y&&e.hp===100000,'rise moved ground position or caused early damage');
  if(previous){
   maxTurn=Math.max(maxTurn,turn(now.visualAngle,previous.visualAngle));
   const dx=now.x-previous.x,dy=(now.y-now.lift-now.offset)-(previous.y-previous.lift-previous.offset);
   if(Math.hypot(dx,dy)>1e-7)maxAlignmentError=Math.max(maxAlignmentError,turn(now.visualAngle,Math.atan2(dy,dx)));
  }
  A.assert(now.trail.length<=8,'missile trail is unbounded');
  for(const point of now.trail){
   const actual=samples.find(v=>Math.abs(v.age-point.age)<1e-7);
   if(actual)A.assert(Math.hypot(point.x-actual.x,point.y-(actual.y-actual.lift-actual.offset))<1e-6,'trail point was invented instead of recording projected flight history');
   A.assert(now.age-point.age<=.180001,'stale trail point exceeded history lifetime');
  }
  previous=now;A.advance(.01);
 }
 A.assert(maxTurn<.3,'missile screen pitch changed abruptly '+maxTurn);
 A.assert(maxAlignmentError<.02,'missile sprite diverged from actual projected motion '+maxAlignmentError);
 const seek=samples.filter(v=>v.phase==='seek');
 A.assert(seek.length>10&&Math.max(...seek.map(v=>v.lift))>s.cruiseHeight,'arc lacks natural apex after launch');
 A.assert(seek.at(-1).lift<20,'arc did not descend before impact');
 A.assert(e.hp<100000,'curved missile failed to damage actual target');
 A.assert(seek[0].distance<2,'orbit-to-seek position discontinuity');
 const orbit=samples.filter(v=>v.phase==='orbit');
 A.assert(orbit.length>=60&&orbit.every(v=>v.lift===v.cruiseHeight),'horizontal orbit missing or altitude changed');
 const width=Math.max(...orbit.map(v=>v.x))-Math.min(...orbit.map(v=>v.x));
 const depth=Math.max(...orbit.map(v=>v.y))-Math.min(...orbit.map(v=>v.y));
 A.assert(width>s.orbitRadius*1.8&&depth>s.orbitRadius*.5&&width/depth>2.5,'first missile did not make a horizontal ellipse');
 A.assert(seek[0].age>=.87-1e-6,'missile sought before rise and orbit completed');
 return {samples,maxTurn,maxAlignmentError,damage:100000-e.hp};
}"""

RETARGET = r"""() => {
 const A=Acceptance,P=G.NarutoPain,{e,shot:s}=A.curveCast();
 while(s.phase!=='seek')A.advance();A.finish(.06);
 e.x=160;e.y=130;G.EnemyMgr.rebuildGrid();
 let previous=s.angle,maxTurn=0;
 for(let i=0;i<8;i++){A.advance();const d=Math.abs(Math.atan2(Math.sin(s.angle-previous),Math.cos(s.angle-previous)));
  maxTurn=Math.max(maxTurn,d);A.assert(d<=.038001,'homing target moved heading abruptly '+d);previous=s.angle;}
 e.dead=true;e.hp=0;G.EnemyMgr.rebuildGrid();const next=A.spawn(180,-30),height=s.lift;
 const angle=s.angle;A.advance();
 A.assert(s.target===next,'dead target did not reacquire');
 A.assert(Math.abs(s.lift-height)<8,'retarget restarted or jumped height arc');
 A.assert(Math.abs(Math.atan2(Math.sin(s.angle-angle),Math.cos(s.angle-angle)))<=.038001,'retarget snapped heading');
 const retargetHeightDelta=s.lift-height;
 A.finish(2);
 const dodge=A.curveCast();while(dodge.shot.phase!=='seek')A.advance();
 dodge.e.x=310;G.EnemyMgr.rebuildGrid();let extendedMaxTurn=0,checkedEnd=false;
 previous=dodge.shot.visualAngle;
 for(let i=0;i<90&&P.shots.includes(dodge.shot);i++){
  A.advance();const current=dodge.shot.visualAngle;
  const turn=Math.abs(Math.atan2(Math.sin(current-previous),Math.cos(current-previous)));
  extendedMaxTurn=Math.max(extendedMaxTurn,turn);previous=current;
  if(dodge.shot.seekAge>dodge.shot.diveDuration+.02)checkedEnd=true;
 }
 A.assert(checkedEnd,'dodging target did not extend pursuit past nominal descent');
 A.assert(extendedMaxTurn<.3,'extended pursuit snapped pitch at end of descent '+extendedMaxTurn);
 return {maxTurn,retargetHeightDelta,extendedMaxTurn,checkedEnd};
}"""

ORBIT_SELECTION = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain;
 const {e,shot:s}=A.curveCast();while(s.phase==='rise')A.advance();A.finish(.2);
 A.assert(s.phase==='orbit'&&!s.target&&e.hp===100000,'orbit locked target or hit early');
 e.dead=true;e.hp=0;G.EnemyMgr.rebuildGrid();const next=A.spawn(210,60);
 while(s.phase==='orbit'){
  A.assert(!s.target&&next.hp===100000&&s.lift===s.cruiseHeight,'orbit selected or damaged replacement early');A.advance();
 }
 A.assert(s.target===next,'orbit end did not choose current living enemy');A.finish(1.5);
 A.assert(next.hp<100000,'fresh orbit-end target never hit');
 const spread=[];
 for(const picks of [0,20]){
  A.curveReset();p.quantityBonus=p.quantityPicks=picks;A.spawn(240,0);A.ready('missiles');A.advance();
  const count=A.actions().find(f=>f.kind==='missiles').count,paths=new Map(),previous=new Map();
  A.assert(count===(picks===0?10:60),'doubled native volley or quantity ceiling changed '+count);
  let alignmentError=0;
  for(let i=0;i<240&&paths.size<count;i++){
   for(const shot of P.shots){
    const point={x:shot.x,y:shot.y-shot.lift-shot.launchOffset,radius:shot.orbitRadius};
    A.assert([point.x,point.y,shot.visualAngle].every(Number.isFinite),'spread trajectory became non-finite');
    const last=previous.get(shot);if(last){A.assert(last.radius===point.radius,'per-shot orbit radius changed during flight');const dx=point.x-last.x,dy=point.y-last.y;
     if(Math.hypot(dx,dy)>1e-7)alignmentError=Math.max(alignmentError,Math.abs(Math.atan2(Math.sin(shot.visualAngle-Math.atan2(dy,dx)),Math.cos(shot.visualAngle-Math.atan2(dy,dx)))));}
    previous.set(shot,point);
    if(shot.phase==='orbit'){
     A.assert(!shot.target&&shot.lift===shot.cruiseHeight,'spread lost fixed altitude or locked early');
     if(shot.orbitAge>=shot.orbitDuration*.5&&!paths.has(shot.emitted))paths.set(shot.emitted,{direction:shot.orbitDirection,height:shot.cruiseHeight,radius:shot.orbitRadius,x:shot.x-shot.orbitX,y:shot.y-shot.orbitY});
    }
   }A.advance(.01);
  }
  const points=[...paths.values()];
  A.assert(points.length===count&&new Set(points.map(v=>v.direction)).size===count,'volley reused missile directions '+count);
  A.assert(points.every(v=>v.height>=48&&v.height<=132)&&new Set(points.map(v=>v.height)).size===count,'volley lost bounded unique per-shot altitudes');
  A.assert(points.every(v=>v.radius>=40&&v.radius<=88)&&new Set(points.map(v=>v.radius)).size===count,'volley reused orbit radii or exceeded radius bounds');
  A.assert(points.some(v=>v.x < -80)&&points.some(v=>v.x>80)&&points.some(v=>v.y < -30)&&points.some(v=>v.y>30),'volley did not spread in different directions');
  A.assert(alignmentError<.02,'spread sprite diverged from actual travel '+alignmentError);
  spread.push({picks,count,alignmentError,paths:points});
 }
 A.curveReset();return {freshTarget:true,spread};
}"""

ALTITUDE = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,volleys=[];
 A.curveReset();A.spawn(240,0);
 for(let cast=0;cast<2;cast++){
  const before=P.snapshot(p).castCounts.missiles||0,heights=new Map(),enteredSeek=new Set();
  A.ready('missiles');A.advance();p.moves.find(m=>m.id==='naruto-pain-missiles').t=999;
  A.assert(P.snapshot(p).castCounts.missiles===before+1,'altitude fixture did not use native cast');
  for(let i=0;i<300;i++){
   for(const s of P.shots.filter(s=>s.kind==='missile')){
    const height=s.cruiseHeight;
    A.assert(Number.isFinite(height)&&height>=48&&height<=132,'per-shot altitude outside visible variation band');
    if(heights.has(s.emitted))A.assert(heights.get(s.emitted)===height,'cruise altitude changed during flight');
    heights.set(s.emitted,height);
    if(s.phase==='rise')A.assert(Math.abs(s.lift-height*Math.min(1,s.age/.22))<1e-6,'rise did not interpolate to own altitude');
    if(s.phase==='orbit')A.assert(s.lift===height,'horizontal orbit developed altitude jitter');
    if(s.phase==='seek'&&!enteredSeek.has(s.emitted)){
     A.assert(Math.abs(s.lift-height)<6,'orbit-to-seek altitude jumped');enteredSeek.add(s.emitted);
    }
   }A.advance();
  }
  const values=[...heights.entries()].sort((a,b)=>a[0]-b[0]).map(v=>v[1]);
  A.assert(values.length===10&&new Set(values).size===10,'native ten-shot volley did not use ten different heights');
  A.assert(enteredSeek.size===10,'altitude fixture missed seek transition');volleys.push(values);A.finish(3);
 }
 A.assert(volleys[0].every((height,i)=>height!==volleys[1][i]),'subsequent native volley repeated same altitude pattern');
 A.curveReset();return {volleys,bounded:true,fixedOrbitHeight:true,continuousSeek:true};
}"""

COUNTS_SPLASH = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out=[];
 for(let level=1;level<=5;level++){
  if(level>1){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:naruto-pain-missiles');
   A.assert(card&&card.apply(p)!==false,'native missile upgrade absent '+level);}
  for(const picks of [0,4,20]){
   A.curveReset();p.quantityBonus=p.quantityPicks=picks;A.spawn(240,0);A.ready('missiles');A.advance();
   const action=A.actions().find(f=>f.kind==='missiles'),expected=Math.min(60,Math.floor([10,10,12,14,16][level-1]*Math.pow(1.25,picks)));
   A.assert(action?.count===expected,'curve changed native missile count '+level+'/'+picks);
   A.finish(.7);A.assert(P.shots.filter(s=>s.kind==='missile').length<=60,'curve exceeded live missile cap');
   out.push({level,picks,count:action.count});
  }
 }
 const {e}=A.curveCast();A.finish(.4);const inside=A.spawn(240,25),outside=A.spawn(320,0);
 A.finish(3.5);A.assert(e.hp<100000&&inside.hp<100000,'native missile explosion lost nearby victims '+JSON.stringify({target:e.hp,inside:inside.hp}));
 A.assert(outside.hp===100000,'48-radius missile explosion hit distant control');
 return {counts:out,splashDamage:100000-inside.hp,outsideDamage:100000-outside.hp};
}"""

LIFECYCLE = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out=[];
 for(const reason of ['pause','wall','owner-death','world','clear']){
  const {e,shot:s}=A.curveCast();A.finish(.25);
  if(reason==='pause'){const before=JSON.stringify(A.curveSample(s));G.Combat.updateFields(.5);
   A.assert(before===JSON.stringify(A.curveSample(s)),'paused trajectory advanced');}
  if(reason==='wall'){const W=G.World,block=W.projectileBlock,wall=W.isWall;
   W.projectileBlock=x=>x>=80&&x<=120?{destructible:false}:false;W.isWall=x=>x>=80&&x<=120;
   try{A.finish(2.7);A.assert(e.hp===100000,'missile crossed solid wall');}finally{W.projectileBlock=block;W.isWall=wall;}}
  if(reason==='owner-death'){P.actorsFor(p).find(b=>b.path==='naraka').hurt(1e9,null,true);p.invuln=0;p.hurt(1e9,null,true);A.advance();p.dead=false;}
  if(reason==='world'){const world=G.World;G.World={...world};try{A.advance();}finally{G.World=world;}}
  if(reason==='clear')G.Combat.clearFields();
  if(['owner-death','world','clear'].includes(reason))A.assert(!P.shots.length,'missile lifecycle leaked '+reason);
  out.push(reason);
 }A.curveReset();return out;
}"""

CAPTURE_SETUP = r"""(level=1) => {
 const m=curveMoves.find(m=>m.id==='naruto-pain-missiles');m.lvl=level;m.count=[10,10,12,14,16][level-1];
 const {e}=Acceptance.curveCast();window.curveEnemy=e;
}"""

ALTITUDE_TIER5 = r"""() => {
 const A=Acceptance,P=G.NarutoPain,heights=new Map(),radii=new Map();
 for(let i=0;i<90;i++){
  for(const shot of P.shots.filter(s=>s.kind==='missile')){
   const height=shot.cruiseHeight;
   A.assert(height>=48&&height<=132,'tier-five altitude exceeded bounds');
   if(heights.has(shot.emitted))A.assert(heights.get(shot.emitted)===height,'tier-five altitude drifted');
   heights.set(shot.emitted,height);
   A.assert(shot.orbitRadius>=40&&shot.orbitRadius<=88,'tier-five radius exceeded bounds');
   if(radii.has(shot.emitted))A.assert(radii.get(shot.emitted)===shot.orbitRadius,'tier-five radius changed during flight');
   radii.set(shot.emitted,shot.orbitRadius);
   if(shot.phase==='orbit')A.assert(shot.lift===height,'tier-five orbit changed altitude');
  }A.advance();
 }
 const values=[...heights.values()].sort((a,b)=>a-b);
 A.assert(values.length===16&&new Set(values).size===16,'tier-five volley reused missile heights');
 const minGap=Math.min(...values.slice(1).map((height,i)=>height-values[i]));
 A.assert(minGap>=5-1e-9,'tier-five height separation too subtle '+minGap);
 A.assert(radii.size===16&&new Set(radii.values()).size===16,'tier-five volley reused orbit radii');
 return {count:values.length,heights:values,minGap,radii:[...radii.values()]};
}"""

STAGGER = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out=[];
 for(const picks of [0,20]){
  A.curveReset();p.quantityBonus=p.quantityPicks=picks;A.spawn(240,0);A.ready('missiles');A.advance();
  const count=A.actions().find(a=>a.kind==='missiles').count,times=new Map(),durations=new Map();
  A.assert(count===(picks===0?16:60),'stagger fixture did not use native volley');
  let mixedPhases=false;
  for(let i=0;i<300;i++){
   const missiles=P.shots.filter(s=>s.kind==='missile');
   if(missiles.some(s=>s.phase==='orbit')&&missiles.some(s=>s.phase==='seek'))mixedPhases=true;
   for(const shot of missiles){
    const duration=shot.orbitDuration;
    A.assert(duration>=.65&&duration<=1.55,'stagger orbit duration exceeded limits');
    if(durations.has(shot.emitted))A.assert(durations.get(shot.emitted)===duration,'per-shot duration changed in flight');
    durations.set(shot.emitted,duration);
    if(shot.phase==='orbit')A.assert(!shot.target&&shot.orbitAge<duration,'shot sought target before own orbit ended');
    if(shot.phase==='seek'&&!times.has(shot.emitted)){
     A.assert(shot.age>=.22+duration-1e-7,'shot departed before its own orbit duration');
     A.assert(shot.target&&!shot.target.dead,'independent departure did not acquire living target');
     times.set(shot.emitted,i*.01);
    }
   }A.advance();
  }
  const ordered=[...times.entries()].sort((a,b)=>a[0]-b[0]).map(v=>v[1]);
  A.assert(times.size===count&&durations.size===count,'stagger lost missiles before seek '+times.size+'/'+count);
  const gaps=ordered.slice(1).map((time,i)=>time-ordered[i]),span=ordered.at(-1)-ordered[0];
  A.assert(gaps.every(gap=>gap>0),'multiple missiles departed on same simulation step');
  if(picks===0)A.assert(Math.min(...gaps)>=.07-1e-7,'native sixteen-shot departures were insufficiently staggered');
  A.assert(span>=1.1&&mixedPhases,'volley did not visibly stagger orbit and independent seeking');
  out.push({count,departures:ordered,minGap:Math.min(...gaps),span,mixedPhases});
 }A.curveReset();return out;
}"""

CAPTURE = r"""() => {
 const c=document.createElement('canvas');c.width=640;c.height=400;
 const ctx=c.getContext('2d');ctx.fillStyle='#253c28';ctx.fillRect(0,0,c.width,c.height);
 ctx.translate(200,270);ctx.imageSmoothingEnabled=false;
 G.Combat.drawGroundFields(ctx);curveEnemy.draw(ctx);Acceptance.p().draw(ctx);
 for(const b of G.NarutoPain.actors())b.draw(ctx);G.Combat.drawAirFields(ctx);
 ctx.setTransform(1,0,0,1,0,0);ctx.fillStyle='white';ctx.font='16px monospace';
 const s=G.NarutoPain.shots.find(s=>s.kind==='missile'),m=Acceptance.p().moves[0];
 ctx.fillText('Lv.'+m.lvl+' / '+m.count+' missiles / '+(s?'flight '+s.age.toFixed(2)+'s':'impact'),16,24);
 return c.toDataURL();
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'errors': [], 'viewports': {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, viewport in [('desktop', {'width': 1200, 'height': 900}), ('mobile', {'width': 390, 'height': 844})]:
            page = browser.new_page(viewport=viewport, is_mobile=label == 'mobile', has_touch=label == 'mobile', service_workers='block')
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.goto(URL)
            frame = game_frame(page)
            enter(frame)
            frame.evaluate(SETUP)
            result = report['viewports'][label] = {}
            for name, check in [('trajectory', TRAJECTORY), ('orbitSelection', ORBIT_SELECTION), ('altitude', ALTITUDE), ('retarget', RETARGET), ('lifecycle', LIFECYCLE), ('countsSplash', COUNTS_SPLASH)]:
                result[name] = frame.evaluate(check)
                print(label, name, 'PASS', flush=True)
            frame.evaluate(CAPTURE_SETUP, 5)
            result['altitudeTier5'] = frame.evaluate(ALTITUDE_TIER5)
            print(label, 'altitudeTier5', 'PASS', flush=True)
            result['stagger'] = frame.evaluate(STAGGER)
            print(label, 'stagger', 'PASS', flush=True)
            frame.evaluate(CAPTURE_SETUP, 1)
            images = []
            for index in range(85):
                raw = base64.b64decode(frame.evaluate(CAPTURE).split(',', 1)[1])
                images.append(Image.open(io.BytesIO(raw)).convert('RGB'))
                frame.evaluate('Acceptance.finish(.04)')
            images[0].save(OUT / f'{label}-flight.gif', save_all=True, append_images=images[1:], duration=40, loop=0, disposal=2)
            selected = [images[i] for i in [8, 16, 24, 32, 42, 60]]
            strip = Image.new('RGB', (640 * 3, 400 * 2))
            for i, image in enumerate(selected):
                strip.paste(image, ((i % 3) * 640, (i // 3) * 400))
            strip.save(OUT / f'{label}-trajectory.png')
            images[36].save(OUT / f'{label}-preview.png')
            frame.evaluate(CAPTURE_SETUP, 5)
            max_images = []
            for index in range(85):
                raw = base64.b64decode(frame.evaluate(CAPTURE).split(',', 1)[1])
                max_images.append(Image.open(io.BytesIO(raw)).convert('RGB'))
                frame.evaluate('Acceptance.finish(.04)')
            max_images[0].save(OUT / f'{label}-tier5-flight.gif', save_all=True, append_images=max_images[1:], duration=40, loop=0, disposal=2)
            max_images[36].save(OUT / f'{label}-tier5-preview.png')
            page.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('Missile curve acceptance PASS', flush=True)


if __name__ == '__main__':
    main()
