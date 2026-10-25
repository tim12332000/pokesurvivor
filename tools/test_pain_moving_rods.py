"""Native moving-enemy acceptance for bounded falling receiver prediction.

Uses Enemy.update and the production enemy/combat/projectile/field ordering.
The old fixed-point comparison is geometry against the same movement trace;
no damage, collision, targeting or runtime implementation is replaced.
"""
import base64
import io
import json
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame
from test_ninja_tool_bounce import SETUP
from test_pain_falling_rods import CAPTURE

OUT = Path(__file__).resolve().parents[1] / '.omx/state/pain-moving-rods'
HARNESS = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain;
 A.movingFresh=(speed=120,angle=0,mode='chase')=>{
  A.bounceReset();const m=G.Moves.instance('naruto-pain',1);m.cd=999;m.quantityBaseCount=1;p.moves=[m];
  G.World.walkable=()=>true;G.Path.clear();
  const e=A.spawn(180*Math.cos(angle),180*Math.sin(angle));e.spd=speed;e.flying=false;
  if(mode==='strafe'){
   e.boss=true;e.ai={mode:'far',modeT:999,cd:999,side:1,fury:false,cast:null};
  }
  if(mode==='zigzag'){e.behavior='thief';e.life=999;}
  A.movingEnemy=e;A.movingTime=0;A.movingShots=[];A.movingHits=A.watchBounce([e])[0];return e;
 };
 A.nativeMovingStep=(dt=.01)=>{
  A.resume();try{
   // Match Game.update order, omitting procedural spawns and player input.
   G.Path.update(dt,[p]);G.EnemyMgr.update(dt,[p]);G.EnemyMgr.rebuildGrid();
   G.Combat.tick(dt,p,0);G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,0);G.Combat.updateFields(dt);
   p.anim.update(dt);G.FX.update(dt);A.movingTime+=dt;
   for(const shot of P.shots)if(shot.kind==='rod'&&!A.movingShots.includes(shot))A.movingShots.push(shot);
  }finally{A.pause()}
 };
}"""
CHECK = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,out={};
 out.motion=[];
 for(const mode of ['chase','strafe','zigzag'])for(const speed of [60,120,200]){
  let hits=0,fixedHits=0,trials=0,maxStep=0;
  for(const angle of [0,Math.PI/4,Math.PI/2,3*Math.PI/4,Math.PI,5*Math.PI/4,3*Math.PI/2,7*Math.PI/4]){
   const e=A.movingFresh(speed,angle,mode);let shot,launch,previous,impactPosition;
   for(let i=0;i<70;i++){
    const before=A.movingShots[0];A.nativeMovingStep();
    shot=A.movingShots[0];
    if(shot&&!launch){launch={x:shot.x,y:shot.y};previous={x:shot.x,y:shot.y};}
    if(shot){maxStep=Math.max(maxStep,Math.hypot(shot.x-previous.x,shot.y-previous.y));previous={x:shot.x,y:shot.y};}
    if(before&&P.shots.indexOf(before)<0&&!impactPosition)impactPosition={x:e.x,y:e.y};
   }
   A.assert(shot&&launch&&impactPosition,'native moving trial did not emit/land');
   A.assert(A.movingHits.length<=1,'moving target received repeated impact');
   A.assert(A.movingHits.every(h=>h.id==='naruto-pain'&&h.owner===p),'moving impact lost source/owner');
   hits+=A.movingHits.length?1:0;
   fixedHits+=Math.hypot(impactPosition.x-launch.x,impactPosition.y-launch.y)<=shot.r+e.r?1:0;
   trials++;
  }
  A.assert(hits/trials>=.8,'native '+mode+' '+speed+' hit rate '+hits+'/'+trials);
  A.assert(maxStep<=3.60001,'rod correction exceeded 360px/s '+maxStep);
  out.motion.push({mode,speed,hits,fixedHits,trials,maxCorrectionPer10ms:maxStep});
 }
 A.assert(out.motion.some(r=>r.hits>r.fixedHits),'prediction did not improve on fixed landing geometry');
 out.frameRates=[];
 for(const dt of [1/60,1/30,.05,.1]){
  let hits=0;
  for(const angle of [0,Math.PI/2,Math.PI,3*Math.PI/2]){
   const e=A.movingFresh(200,angle),trace=[];for(let i=0;i<Math.ceil(.65/dt);i++){
    A.nativeMovingStep(dt);const s=A.movingShots[0];trace.push({t:A.movingTime,x:e.x,y:e.y,r:e.r,shot:s&&{age:s.age,x:s.x,y:s.y,lift:s.lift,present:P.shots.includes(s)}});
   }
   A.assert(A.movingHits.length===1,'ordinary movement missed at timestep '+dt+' angle '+angle+' '+JSON.stringify(trace));hits++;
  }
  out.frameRates.push({dt,hits,trials:4});
 }
 // The last 80ms is a committed landing: ordinary late movement may dodge it.
 let e=A.movingFresh(120);for(let i=0;i<29;i++)A.nativeMovingStep();let s=A.movingShots[0];
 const locked={x:s.x,y:s.y};e.x+=35;e.y+=35;G.EnemyMgr.rebuildGrid();
 for(let i=0;i<15;i++)A.nativeMovingStep();
 A.assert(s.x===locked.x&&s.y===locked.y&&!A.movingHits.length,'late committed landing homed or hit dodging enemy');out.finalLock=true;
 // Discontinuous motion stops tracking, rather than warping a shot to the target.
 e=A.movingFresh(0);A.nativeMovingStep();s=A.movingShots[0];const origin={x:s.x,y:s.y};e.y+=70;
 for(let i=0;i<50;i++)A.nativeMovingStep();
 A.assert(s.trackingStopped&&s.x===origin.x&&s.y===origin.y&&!A.movingHits.length,'teleport was chased');out.teleportEscape=true;
 e=A.movingFresh(250);e.behavior='charger';e.phase='dash';e.pt=1;e.dx=-1;e.dy=0;
 for(let i=0;i<60;i++)A.nativeMovingStep();
 A.assert(A.movingHits.length===0,'falling rod guaranteed a hit against a native 850px/s dash');out.nativeDashEscape=true;
 out.invalidTargets=[];
 for(const reason of ['dead','outside','wall']){
  e=A.movingFresh(120);A.nativeMovingStep();s=A.movingShots[0];
  const block=G.World.projectileBlock;
  if(reason==='dead'){e.dead=true;e.hp=0;}
  else if(reason==='outside'){e.x=320;e.y=0;}
  else G.World.projectileBlock=x=>x>=80&&x<=100?{destructible:false}:false;
  try{
   for(let i=0;i<50;i++)A.nativeMovingStep();
   A.assert(s.trackingStopped&&!A.movingHits.length&&!P.shots.length,'invalid target was followed/hit '+reason);
   out.invalidTargets.push(reason);
  }finally{G.World.projectileBlock=block}
 }
 // Target is retained until impact; tracking never swaps to a nearby bystander.
 e=A.movingFresh(120);A.nativeMovingStep();s=A.movingShots[0];const other=A.spawn(150,55),otherHits=A.watchBounce([other]);e.dead=true;e.hp=0;
 for(let i=0;i<50;i++)A.nativeMovingStep();
 A.assert(s.target===e&&otherHits[0].length===0,'prediction reacquired a new enemy');out.noReacquire=true;
 e=A.movingFresh(120);A.nativeMovingStep();s=A.movingShots[0];const paused=[s.age,s.x,s.y];G.Combat.updateFields(.2);
 A.assert(JSON.stringify(paused)===JSON.stringify([s.age,s.x,s.y]),'pause moved tracking shot');out.pause=true;
 G.Combat.clearFields();A.assert(!P.shots.length&&!P.effects.length,'clear leaked tracking rod');out.clear=true;
 // Native cadence must not create another volley while the first one tracks.
 e=A.movingFresh(120);A.nativeMovingStep();const cooldown=P.snapshot(p).basicCooldown;
 for(let i=0;i<70;i++)A.nativeMovingStep();
 A.assert(A.movingShots.length===1&&P.snapshot(p).basicCooldown<cooldown&&P.snapshot(p).basicCooldown>0,'tracking modified quantity or cooldown');out.cooldown=true;
 A.bounceReset();return out;
}"""
VISUAL = r"""() => {
 const A=Acceptance;A.movingFresh(160,Math.PI/6);window.fallEnemies=[A.movingEnemy];
 Acceptance.p().moves[0].quantityBaseCount=5;A.nativeMovingStep();
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'viewports': {}, 'errors': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, vp in [('desktop', {'width': 1200, 'height': 900}), ('mobile', {'width': 390, 'height': 844})]:
            page = browser.new_page(viewport=vp, is_mobile=label == 'mobile', has_touch=label == 'mobile', service_workers='block')
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(URL)
            frame = game_frame(page)
            frame.wait_for_function("window.PS_REDRAWN_READY&&G.NarutoPain&&document.getElementById('boot').classList.contains('hidden')")
            if frame.locator('#tap-start').is_visible():
                frame.locator('#tap-start').click()
            frame.locator('[data-quick-naruto="30010"]').click()
            enter(frame)
            frame.evaluate(SETUP)
            frame.evaluate(HARNESS)
            report['viewports'][label] = frame.evaluate(CHECK)
            frame.evaluate(VISUAL)
            frames = []
            for i in range(30):
                if i:
                    frame.evaluate('Acceptance.nativeMovingStep(.02)')
                image = frame.evaluate(CAPTURE)
                png = base64.b64decode(image.split(',', 1)[1])
                frames.append(Image.open(io.BytesIO(png)).convert('RGB'))
                if i == 8:
                    (OUT / f'{label}-tracking.png').write_bytes(png)
                    page.screenshot(path=str(OUT / f'{label}-game.png'))
            frames[0].save(OUT / f'{label}-moving.gif', save_all=True, append_images=frames[1:], duration=55, loop=0)
            page.close()
            print(label + ' native moving rods PASS', flush=True)
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), 'utf-8')
    print('Moving falling rods PASS')


if __name__ == '__main__':
    main()
