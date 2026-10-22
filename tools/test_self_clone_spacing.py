"""Native clone movement: separation, independent targets and owner leash."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/self-clone-spacing'
CHECK = r"""() => {
 const A=Acceptance,assert=A.assert,S=G.SelfClones;
 G.Naruto.choose(30001);G.Flow.play();A.pause();A.arena();
 const p=G.Game.player;p.x=p.y=0;p.target=null;
 const tick=G.Combat.tick,fire=G.NarutoFireball.activeFor;
 G.Combat.tick=()=>{}; // Isolate steering from attack-owned displacement.
 const step=(n=1)=>{A.resume();try{for(let i=0;i<n;i++)G.Combat.updateFields(1/60)}finally{A.pause()}};
 const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
 const spawn=(x,y)=>{const e=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e};
 const a=S.summon(p),b=S.summon(p),gap=a.r+b.r;
 const report={spawnDistance:dist(a,b)};
 try{
  assert(dist(a,b)>=gap+5,'summoned clones overlap');
  a.x=b.x=50;a.y=b.y=0;const px=p.x,py=p.y;
  step(120);report.idleDistance=dist(a,b);
  assert(dist(a,b)>=gap,'identical-position clones never separate');
  assert(p.x===px&&p.y===py,'steering moved owner');
  const e=spawn(160,0),f=spawn(180,60);p.target=e;
  step(1);assert(a.target&&b.target&&a.target!==b.target,'clones focus same foe despite alternatives');
  const ta=a.target,tb=b.target;step(60);
  assert(a.target===ta&&b.target===tb,'independent targets oscillate');
  assert(p.target===e,'clone selection changed owner target');
  f.dead=true;step(180);
  assert(a.target===e&&b.target===e,'single remaining enemy not shared');
  report.combatDistance=dist(a,b);assert(dist(a,b)>=gap,'shared-target clones overlap');
  assert(dist(a,e)<300&&dist(b,e)<300,'separation prevented attack approach');
  G.EnemyMgr.clear();a.x=b.x=50;a.y=b.y=0;
  G.NarutoFireball.activeFor=actor=>actor===a?{owner:a}:null;
  const busy={x:a.x,y:a.y};step(30);
  assert(a.x===busy.x&&a.y===busy.y,'ordinary steering moved busy skill actor');
  G.NarutoFireball.activeFor=fire;
  p.frozen=true;const frozen=[a.x,a.y,b.x,b.y];step(10);
  assert(JSON.stringify(frozen)===JSON.stringify([a.x,a.y,b.x,b.y]),'frozen clones moved');p.frozen=false;
  // Impassable half-plane: ordinary separation cannot push either actor across.
  const free=G.World.isFree,collide=G.World.collide;
  G.World.isFree=(x,y,r)=>x>=r;
  G.World.collide=actor=>{actor.x=Math.max(actor.r,actor.x)};
  a.x=b.x=a.r+1;a.y=b.y=0;p.x=80;
  let maxStep=0;
  for(let i=0;i<90;i++){
   const before=[{x:a.x,y:a.y},{x:b.x,y:b.y}];step();
   for(const [j,c] of [a,b].entries()){
    maxStep=Math.max(maxStep,dist(c,before[j]));
    assert(c.x>=c.r,'clone pushed into wall');
    assert(dist(c,before[j])<=c.spd/60+1e-5,'separation teleported ordinary actor');
   }
  }
  G.World.isFree=free;G.World.collide=collide;report.maxOrdinaryStep=maxStep;
  p.x=p.y=0;a.x=400;a.y=0;b.x=20;b.y=60;
  const outside=spawn(430,0),inside=spawn(100,80);step();
  assert(!a.target,'far clone continues attacking instead of returning');
  assert(a.x<400,'far clone not returning');
  step(240);assert(dist(a,p)<250,'clone did not return near player');
  assert(a.target!==outside&&b.target!==outside,'clone selected outside-leash enemy');
  const hp=a.hp=a.maxHp*.6,id=a.cloneId;
  a.x=900;a.y=0;step();
  assert(S.actors().includes(a)&&a.cloneId===id&&a.hp===hp,'hard recall replaced/healed clone');
  report.recalledDistance=dist(a,p);assert(dist(a,p)<220,'hard leash failed safe recall');
  assert(G.World.isFree(a.x,a.y,a.r,true),'hard recall placed clone in obstacle');
  report.independentTargets=true;report.stableTargets=true;report.busyPreserved=true;report.leash=true;
  return report;
 }finally{G.Combat.tick=tick;G.NarutoFireball.activeFor=fire;S.clear()}
}"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in [False, True]:
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY && G.SelfClones && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.evaluate(HARNESS)
            report['mobile' if mobile else 'desktop'] = page.evaluate(CHECK)
            assert not errors, errors
            context.close()
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, **report}))

if __name__ == '__main__':
    main()
