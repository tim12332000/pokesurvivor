"""Ryu's core cadence, travelling scatter, cluster blast and recovery identity."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('RYU_IDENTITY_OUT') or os.environ.get('HERO_IDENTITY_OUT') or ROOT / '.omx/state/hero-identity/ryu')
URL = os.environ.get('RYU_IDENTITY_URL') or os.environ.get('HERO_IDENTITY_URL') or os.environ.get('JUJUTSU_URL')

CHECK = r"""() => {
 const A=JAcceptance,p=A.p(),R=G.JjkRyu,assert=A.assert,checks=[],out={};
 const ids=['jjk-ryu','jjk-ryu-spread','jjk-ryu-impact','jjk-ryu-maximum'];
 function setup(wanted=ids,rank=1){
  A.reset();A.fixture(wanted[0],rank);p.level=30;
  for(const id of wanted.slice(1)){assert(p.addMove(id),'learn '+id);Object.assign(p.moves.find(m=>m.id===id),G.Moves.instance(id,rank))}
  for(const m of p.moves)m.t=999;p.arrange();return p.moves;
 }
 function manual(id){const m=p.moves.find(m=>m.id===id);m.t=0;A.resume();
  try{assert(R.cast(p,m),'manual native cast '+id)}finally{A.pause()};return R.stateFor(p).action}
 function until(test,seconds=12){for(let t=0;t<seconds;t+=.01){if(test())return;A.step(.01,true)}throw Error('native scheduler condition timed out')}
 const hp=es=>es.map(e=>e.hp),loss=(es,before)=>es.map((e,i)=>before[i]-e.hp);

 setup(['jjk-ryu']);A.spawn(100,0);manual('jjk-ryu');A.advance(.3);
 assert(R.stats(p).coreCharge===0,'unlearned maximum accumulated invisible energy');
 checks.push('core energy starts only after learning maximum');

 setup(['jjk-ryu','jjk-ryu-maximum']);const zeroTarget=A.spawn(100,0);
 p.moves.find(m=>m.id==='jjk-ryu-maximum').t=0;A.advance(1,true);
 assert(!R.stats(p)?.casts['jjk-ryu-maximum'],'maximum automatically fired without successful basics');
 assert(R.statusFor(p,p.moves[1]).state==='charging','uncharged maximum lacks charging status');
 const miss=manual('jjk-ryu');zeroTarget.dead=true;zeroTarget.hp=0;A.advance(.5);
 assert(R.stats(p).coreCharge===0,'a missed core cast generated charge');
 checks.push('maximum waits for successful core casts','missed core cast gives no charge');

 setup(['jjk-ryu','jjk-ryu-maximum']);
 const line=[A.spawn(100,0),A.spawn(180,0),A.spawn(280,0)],offLine=A.spawn(160,60),lineHP=hp(line);
 const core=p.moves[0],maximum=p.moves[1],events=[],nativeCast=p.cast;
 p.cast=function(m,...args){events.push({id:m.id,clock:R.stateFor(p).clock});return nativeCast.call(this,m,...args)};
 core.t=maximum.t=0;
 try{
  until(()=>R.stats(p)?.coreCharge===1);
  assert(loss(line,lineHP).every(n=>n>0)&&offLine.hp===offLine.maxHp,'core beam lost its long narrow piercing identity');
  assert(R.stats(p).casts['jjk-ryu']===1,'three victims counted as multiple core casts');
  until(()=>R.stateFor(p)?.action?.mode==='jjk-ryu-maximum');
  assert(events.map(e=>e.id).join(',')==='jjk-ryu,jjk-ryu,jjk-ryu,jjk-ryu-maximum','automatic maximum is not the fourth core opportunity: '+JSON.stringify(events));
  assert(events[3].clock-events[2].clock>=core.cd-.02,'maximum added an independent attack before the next core opportunity');
  assert(R.stats(p).coreCharge===0&&core.t>core.cd-.02,'maximum failed to consume charge and core cooldown');
  A.advance(.76,true);const recovering=R.stats(p).recoveryRemaining;
  assert(recovering>1.4&&R.pose(p)?.volleyCount===5,'maximum lacks the four follow-up barrage window');
  const frozen=JSON.stringify(R.stats(p));G.Combat.tick(5,p,0);G.Combat.updateFields(5);
  assert(JSON.stringify(R.stats(p))===frozen,'pause advanced charge/recovery');
  p.x=7;A.advance(.2,true);
  assert(p.x===7&&R.pose(p)?.volleyIndex>=1&&R.statusFor(p,core).state==='recovering','barrage locked movement or dropped follow-up pose');
  assert(R.stats(p).casts['jjk-ryu']===3,'core fired through maximum recovery');
  A.advance(1,true);assert(R.stats(p).casts['jjk-ryu']===3&&R.pose(p)?.volleyIndex===4,'other body action interrupted the full barrage');
  assert(R.stats(p).recoveryRemaining>.2,'last shot lacks final quarter-second recovery');
  out.cadence={events,releaseRecovery:recovering,charge:R.stats(p).coreCharge};
 }finally{p.cast=nativeCast}
 checks.push('three hit casts charge once per cast','maximum replaces next scheduled core','recovery blocks only casting','pause freezes recovery');
 p.dead=true;p.hp=0;A.step(.01);assert(!R.stateFor(p),'death retained actor charge or recovery');
 checks.push('death clears charge, projectiles and recovery');

 setup(['jjk-ryu-spread']);
 const front=A.spawn(520,0),left=A.spawn(350,-340),right=A.spawn(-380,220),outside=A.spawn(2400,0);
 const victims=[front,left,right,outside],before=hp(victims);
 const spread=manual('jjk-ryu-spread');assert(spread.range===800&&spread.count===8,'spread is not the doubled long-range baseline');
 A.advance(.36);assert(loss(victims,before).every(n=>n===0),'scatter damaged at launch without airborne flight');
 assert(R.stateFor(p).scatter.length===8&&R.stateFor(p).scatter.every(s=>s.phase==='rise'&&s.target==null),'scatter skipped rise or preselected a target');
 A.advance(.5);assert(R.stateFor(p).scatter.every(s=>s.phase==='orbit'&&s.lift>40&&s.target==null),'scatter lacks independent airborne orbit');
 A.advance(7);out.scatterDamage=loss(victims,before);
 assert(out.scatterDamage.slice(0,3).every(n=>n>0)&&out.scatterDamage[3]===0,'long-range distributed coverage/outside boundary failed: '+out.scatterDamage);
 const contacts=G.CombatPulse.telemetry.filter(t=>t.castId===spread.castId&&t.runEpoch===spread.runEpoch);
 assert(contacts.length===8&&new Set(contacts.map(t=>t.contactPulseIndex)).size===8&&contacts.every(t=>t.primaryHits===1),'distinct physical contacts dropped, repeated or pierced');
 out.scatterContacts=contacts;checks.push('doubled airborne bolts and delayed live acquisition','long-range three-approach coverage','separate physical contact pulses under one cast');

 setup(['jjk-ryu-spread']);const wallFront=A.spawn(500,0),wallSide=A.spawn(60,420);
 const wallHP=hp([wallFront,wallSide]);manual('jjk-ryu-spread');
 G.World.isWall=(x,y)=>x>=180&&x<=200;G.World.projectileBlock=(x,y)=>G.World.isWall(x,y)?'wall':false;
 A.advance(8);assert(wallFront.hp===wallHP[0]&&wallSide.hp<wallHP[1],'scatter crossed a solid wall or failed to use the open side: '+loss([wallFront,wallSide],wallHP));
 checks.push('wall blocks seeking while a reachable side remains available');

 setup(['jjk-ryu-spread']);
 const chest={x:110,y:0,r:12,hp:1000000,destructible:true,solid:true},behindChest=A.spawn(300,0),chestCalls=[];
 G.World.propsInCircle=(x,y,r)=>chest.hp>0&&Math.hypot(x-chest.x,y-chest.y)<=r+chest.r?[chest]:[];
 G.World.projectileBlock=(x,y,r)=>chest.hp>0&&Math.hypot(x-chest.x,y-chest.y)<=chest.r+r?chest:false;
 const damageProp=G.World.damageProp;G.World.damageProp=(prop,damage)=>{assert(prop===chest,'wrong prop');chest.hp-=damage;chestCalls.push(damage)};
 try{manual('jjk-ryu-spread');A.advance(8);assert(chestCalls.length>0&&chestCalls.length<=8&&behindChest.hp===behindChest.maxHp,'scatter missed or pierced its first destructible blocker')}
 finally{G.World.damageProp=damageProp}
 checks.push('each bolt stops on its first destructible blocker');

 setup(['jjk-ryu-spread'],5);p.quantityPicks=p.quantityBonus=20;
 const shared=A.spawn(620,0);shared.r=65;const sharedEvents=A.watch(shared);const overlap=manual('jjk-ryu-spread');
 assert(overlap.count===18,'scatter doubled quantity cap changed');A.advance(.36);
 const shots=R.stateFor(p).scatter;
 assert(shots.length===18&&shots.every(s=>s.phase==='rise'),'high quantity lost real airborne bolts');
 A.advance(8);assert(sharedEvents.length===18&&sharedEvents.every(e=>e.id==='jjk-ryu-spread'&&e.owner),'independent bolts lost real same-target payload or attribution');
 checks.push('eighteen-bolt cap and one genuine direct hit per projectile');

 setup(['jjk-ryu-impact']);const lone=A.spawn(60,0),pack=[A.spawn(220,-20),A.spawn(230,0),A.spawn(220,20)],clusterHP=hp([lone,...pack]);
 const impact=manual('jjk-ryu-impact'),locked={x:impact.tx,y:impact.ty};
 assert(locked.x>=200,'rank-one blast chose nearest lone enemy over the remote cluster');
 p.x=-10;A.advance(.44);assert(loss([lone,...pack],clusterHP).every(n=>n===0),'cluster blast damaged before telegraph completed');
 A.advance(.03);out.clusterDamage=loss([lone,...pack],clusterHP);
 assert(out.clusterDamage[0]===0&&out.clusterDamage.slice(1).every(n=>n>0),'cluster blast footprint differs from captured target');
 assert(impact.tx===locked.x&&impact.ty===locked.y,'cluster telegraph followed owner movement');
 out.clusterTarget=locked;checks.push('rank-one remote densest pack target','locked delayed cluster blast');

 setup(['jjk-ryu-spread']);A.spawn(150,0);manual('jjk-ryu-spread');A.advance(.36);
 const active=R.stateFor(p).scatter.length;assert(active===8,'missing in-flight cleanup fixture');
 const pausedShots=JSON.stringify(R.stateFor(p).scatter.map(({x,y,age})=>({x,y,age})));
 G.Combat.updateFields(4);assert(JSON.stringify(R.stateFor(p).scatter.map(({x,y,age})=>({x,y,age})))===pausedShots,'pause moved travelling bolts');
 p.dead=true;p.hp=0;A.step(.01);assert(!R.stateFor(p),'death retained travelling scatter');
 checks.push('pause freezes travelling bolts','death removes in-flight bolts before contact');
 setup(['jjk-ryu-spread']);A.spawn(150,0);manual('jjk-ryu-spread');A.advance(.36);
 const oldWorld=G.World;G.World=Object.create(oldWorld);
 try{A.step(.01);assert(!R.stateFor(p),'world change retained travelling scatter')}finally{G.World=oldWorld}
 checks.push('world changes cancel in-flight bolts');
 setup(['jjk-ryu-spread']);A.spawn(150,0);manual('jjk-ryu-spread');A.advance(.36);
 G.CombatPulse.beginRun();A.step(.01);assert(!R.stateFor(p),'new run epoch retained travelling scatter');
 checks.push('new run epoch clears previous bolts');
 setup(['jjk-ryu','jjk-ryu-maximum']);A.spawn(100,0);manual('jjk-ryu');A.advance(.3);
 assert(R.stats(p).coreCharge===1,'cleanup charge fixture failed');G.Combat.clearFields(p);
 assert(!R.stateFor(p),'owner clear retained charge');
 out.checks=checks;return out;
}"""


class Handler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *_args):
        pass

    def do_GET(self):
        try:
            super().do_GET()
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            pass


class Server(ThreadingHTTPServer):
    request_queue_size = 128


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    server = None
    if not URL:
        server = Server(('127.0.0.1', 0), partial(Handler, directory=str(ROOT)))
        Thread(target=server.serve_forever, daemon=True).start()
    base.URL = URL or f'http://127.0.0.1:{server.server_port}/.omx/digimon.html?lang=zh-TW'
    base.OUT = OUT
    report = {}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
            for mobile in (False, True):
                label = 'mobile' if mobile else 'desktop'
                context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900},
                                              is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                frame = base.boot(page, 30014, label)
                report[label] = frame.evaluate(CHECK)
                assert not errors, errors
                report[label]['errors'] = errors
                context.close()
            browser.close()
        (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
        print(json.dumps({'ok': True, 'views': {key: len(value['checks']) for key, value in report.items()}, 'evidence': str(OUT)}))
    finally:
        if server:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    main()
