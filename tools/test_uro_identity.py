"""Uro's close palm, remote shatter and projectile reaction stay distinct."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('HERO_IDENTITY_OUT', str(ROOT / '.omx/state/hero-identity/uro')))

CHECK = r"""() => {
 const A=JAcceptance,p=A.p(),U=G.JjkUro,assert=A.assert,report={};
 const incoming=(options={})=>G.Projectiles.spawn({x:170,y:0,vx:-200,vy:0,r:6,life:3,dmg:7,mtype:'psychic',friendly:false,...options});
 const can=m=>{A.resume();try{return U.canCast(p,m)}finally{A.pause()}};
 function knock(e){const events=[],hurt=e.hurt;e.hurt=function(...args){events.push({id:args[7],knock:args[4]});return hurt.apply(this,args)};return events}
 function palm(rank){A.reset();const m=A.fixture('jjk-uro',rank),close=A.spawn(95,0),mid=A.spawn(185,0),boss=A.spawn(100,30,'boss');
  const hits=knock(close),resisted=knock(boss);p.target=close;A.cast(m.id);A.advance(.22);
  assert(close.hp<close.maxHp&&boss.hp<boss.maxHp,'palm missed close targets');
  assert(mid.hp===mid.maxHp,'close palm still reaches the midrange');
  assert(hits.length===1&&hits[0].knock===(rank===5?44:30),'palm ordinary displacement differs');
  assert(resisted.length===1&&resisted[0].knock===0,'palm moved special enemy');
  return {range:m.range,arc:m.arc,knock:hits[0].knock,specialKnock:resisted[0].knock};
 }
 report.palm=[palm(1),palm(5)];
 A.reset();let m=A.fixture('jjk-uro-thin-ice'),victims=[A.spawn(180,0),A.spawn(170,70),A.spawn(170,-70)],outside=A.spawn(-270,0);
 p.target=victims[0];A.cast(m.id);A.advance(.38);
 assert(victims.every(e=>e.hp<e.maxHp)&&outside.hp===outside.maxHp,'midrange shatter fan boundary differs');
 report.thinIce={inside:victims.map(e=>e.maxHp-e.hp),outside:outside.maxHp-outside.hp};

 A.reset();m=A.fixture('jjk-uro-collapse');const near=A.spawn(50,0),remote=[A.spawn(230,0),A.spawn(240,30),A.spawn(240,-30)];
 p.target=near;A.cast(m.id);let body=U.activeFor(p);const locked={x:body.tx,y:body.ty};
 assert(locked.x>200,'collapse chose nearby singleton over remote group');
 for(const e of remote)e.x+=300;const arrived=A.spawn(locked.x,locked.y),arrivedHP=arrived.hp;
 A.advance(.5);assert(arrived.hp===arrivedHP,'collapse damaged before fixed release');A.advance(.1);
 assert(arrived.hp<arrivedHP&&near.hp===near.maxHp&&remote.every(e=>e.hp===e.maxHp),'collapse chased targets or lost captured blast site');
 report.collapse={locked,arrivalDamage:arrivedHP-arrived.hp};
 A.reset();m=A.fixture('jjk-uro-collapse');A.spawn(-70,0);A.spawn(240,0);A.cast(m.id);
 assert(U.activeFor(p).tx===240,'equal-density collapse did not prefer distant site');
 A.reset();m=A.fixture('jjk-uro-collapse');A.spawn(60,0);A.spawn(230,0);A.spawn(230,25);
 G.World.projectilePathClear=(x,y,tx,ty)=>!(x===0&&tx>150);
 A.cast(m.id);assert(U.activeFor(p).tx===60,'collapse selected unreachable cluster');

 A.reset();m=A.fixture('jjk-uro-screen');A.spawn(70,0);assert(!can(m),'rank1 screen wasted on melee-only enemies');
 assert(U.statusFor(p,m).state==='waiting'&&U.statusFor(p,m).reason==='projectile','reactive screen HUD falsely reports a queued attack');
 const away=incoming({x:150,vx:200});assert(!can(m),'screen reacted to departing projectile');G.Projectiles.remove(away);
 const blocked=incoming();G.World.projectilePathClear=()=>false;assert(!can(m),'screen sensed projectile through wall');G.Projectiles.remove(blocked);G.World.projectilePathClear=()=>true;
 report.reactionGates={melee:false,departing:false,wall:false};

 A.reset();m=A.fixture('jjk-uro-thin-ice');const target=A.spawn(200,0),bodyHits=knock(target);p.target=target;A.cast(m.id);body=U.activeFor(p);
 assert(p.addMove('jjk-uro-screen'),'cannot learn reaction screen');const screenMove=p.moves.find(x=>x.id==='jjk-uro-screen');screenMove.t=0;
 incoming();assert(U.statusFor(p,screenMove).state==='ready','reaction HUD incorrectly waits behind a body cast');
 const aim=p.aim;A.resume();try{G.Combat.tick(.001,p,0)}finally{A.pause()}
 const screen=U.stateFor(p).screen;assert(screen&&screen.channel==='reaction','screen did not react during body action');
 assert(U.activeFor(p)===body&&p.aim===aim&&!body.done,'screen replaced pending body attack');
 assert(U.statusFor(p,screenMove).state==='active','active reaction not exposed to HUD');
 const budget=screen.budget;screenMove.t=0;assert(!can(screenMove),'screen refreshed before live capacity expired');
 screenMove.t=9;A.advance(.4);
 assert(bodyHits.some(h=>h.id==='jjk-uro-thin-ice'),'reaction dropped the pending shatter hit');
 report.concurrent={bodyRetained:true,bodyHit:true,capacity:budget};

 A.reset();m=A.fixture('jjk-uro-screen');incoming();A.cast(m.id);const state=U.stateFor(p),capacity=state.screen.budget;
 G.Projectiles.clear();const friendly=incoming({x:60,px:120,friendly:true,owner:p});
 for(let i=0;i<capacity;i++){const shot=incoming({x:60,px:120});A.resume();try{U.intercept()}finally{A.pause()};assert(!G.Projectiles.all().includes(shot),'screen failed native intercept')}
 const extra=incoming({x:60,px:120});A.resume();try{U.intercept()}finally{A.pause()};
 assert(G.Projectiles.all().includes(extra)&&G.Projectiles.all().includes(friendly),'screen exceeded capacity or affected friendly fire');
 const returned=G.Projectiles.all().filter(s=>s.uroReturned);assert(returned.length===capacity&&returned.every(s=>s.owner===p&&s.mid===m.id&&s.vx>0),'reflection attribution/direction differs');
 A.advance(2.4);assert(!U.stateFor(p).screen,'finite screen did not expire');report.finiteScreen={capacity,returned:returned.length};

 function reflectedSetup(rank,withThin=true){
  A.reset();const shield=A.fixture('jjk-uro-screen',rank);if(withThin)assert(p.addMove('jjk-uro-thin-ice'),'cannot learn riposte');
  incoming();A.cast(shield.id);G.Projectiles.clear();const thin=p.moves.find(m=>m.id==='jjk-uro-thin-ice');if(thin)thin.t=4;
  return {shield,thin,state:U.stateFor(p)};
 }
 function reflect(){const shot=incoming({x:60,px:120});A.resume();try{U.intercept()}finally{A.pause()};assert(!G.Projectiles.all().includes(shot),'riposte fixture failed actual reflection')}
 let r=reflectedSetup(1);reflect();assert(r.thin.t===4&&r.state.counterUntil===0,'rank1 screen granted free riposte');
 r=reflectedSetup(3);assert(r.thin.t===4&&r.state.counterUntil===0,'rank3 armed before actual interception');reflect();
 assert(r.thin.t===0&&r.state.counterUntil>r.state.clock&&r.state.counterBonus===0,'rank3 actual reflection did not refresh learned thin ice');
 const opportunity=r.state.counterUntil;r.thin.t=2;reflect();assert(r.thin.t===2&&r.state.counterUntil===opportunity,'later bolt refreshed the same screen twice');
 r=reflectedSetup(3,false);reflect();assert(!p.hasMove('jjk-uro-thin-ice')&&r.state.counterUntil===0,'screen invented unlearned attack');
 report.riposteRanks={rank1Refresh:false,rank3Refresh:true,oncePerScreen:true,unlearnedAttack:false};

 for(const rank of [3,5]){
  A.reset();m=A.fixture('jjk-uro-collapse');A.spawn(180,0);A.cast(m.id);body=U.activeFor(p);
  p.addMove('jjk-uro-thin-ice');p.addMove('jjk-uro');p.addMove('jjk-uro-screen');
  const thin=p.moves.find(m=>m.id==='jjk-uro-thin-ice'),basic=p.moves.find(m=>m.id==='jjk-uro'),shield=p.moves.find(m=>m.id==='jjk-uro-screen');
  Object.assign(shield,G.Moves.instance(shield.id,rank));thin.t=4;basic.t=shield.t=0;
  A.advance(.05,true);incoming();A.resume();try{G.Combat.tick(.001,p,0)}finally{A.pause()};G.Projectiles.clear();reflect();
  const s=U.stateFor(p);assert(U.activeFor(p)===body&&!body.done&&thin.t===0,'reflection replaced pending body or failed refund');
  assert(U.statusFor(p,thin).reason==='riposte'&&U.statusFor(p,thin).state==='queued','pending counter opportunity is not exposed');
  const age=body.age,deadline=s.counterUntil;U.update(2);assert(body.age===age&&s.counterUntil===deadline,'pause spent pending riposte');
  A.advance(1.03,true);const reply=U.activeFor(p);
  assert(body.done&&reply?.mode==='uro-thin-ice'&&reply.riposte,'automatic riposte did not wait for pending body to finish');
  assert((s.castCounts['uro-sky']||0)===0&&s.castCounts['uro-thin-ice']===1,'older ready palm displaced the armed riposte');
  assert(s.counterUntil===0&&s.counterBonus===0,'zero-bonus rank3 or rank5 opportunity was not consumed');
  const expected=thin.dmg*p.atk*(rank===5?1.15:1);assert(Math.abs(reply.damage-expected)<1e-8,'riposte bonus differs from rank contract');
  const cd=thin.t;reflect();assert(thin.t===cd&&s.counterUntil===0,'later bolt refreshed after counter was spent');
  A.advance(.85,true);assert(s.castCounts['uro-thin-ice']===1,'one reflection produced multiple free attacks');
 }
 report.automaticRiposte={ranks:[3,5],pendingBodyPreserved:true,prioritizedOnce:true,rank5Multiplier:1.15};
 for(const kind of ['death','owner']){
  r=reflectedSetup(3);reflect();assert(r.state.counterUntil>0,'missing armed lifecycle fixture');
  if(kind==='death'){p.dead=true;p.hp=0;A.resume();try{U.update(.01)}finally{A.pause()}}else G.Combat.clearFields(p);
  assert(!U.stateFor(p),'armed riposte survived '+kind);
 }

 report.lifecycle=[];
 for(const kind of ['pause','death','world','owner','restart']){
  A.reset();m=A.fixture('jjk-uro-screen');incoming();A.cast(m.id);const current=U.stateFor(p).screen,world=G.World;
  if(kind==='pause'){const age=current.age,budget=current.budget;U.update(2);assert(current.age===age&&current.budget===budget,'paused reaction advanced')}
  else if(kind==='restart'){A.resume();G.Game.startRun();A.pause();assert(!U.stateFor(p),'old-owner reaction survived restart');break}
  else{if(kind==='death'){p.dead=true;p.hp=0}if(kind==='world')G.World=Object.create(world);if(kind==='owner')G.Combat.clearFields(p);
   A.resume();try{U.update(.01)}finally{G.World=world;A.pause()};assert(!U.stateFor(p)?.screen,'reaction survived '+kind)}
  report.lifecycle.push(kind);
 }
 report.lifecycle.push('restart');return report;
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
    base.OUT = OUT
    report = {}
    server = None
    if not os.environ.get('JUJUTSU_URL'):
        server = Server(('127.0.0.1', 0), partial(Handler, directory=str(ROOT)))
        Thread(target=server.serve_forever, daemon=True).start()
        base.URL = f'http://127.0.0.1:{server.server_port}/.omx/digimon.html?lang=zh-TW'
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
            for mobile in (False, True):
                label = 'mobile' if mobile else 'desktop'
                context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1100, 'height': 850},
                                              is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                frame = base.boot(page, 30015, label)
                report[label] = frame.evaluate(CHECK)
                assert not errors, errors
                report[label]['errors'] = errors
                context.close()
            browser.close()
    finally:
        if server:
            server.shutdown()
            server.server_close()
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({'ok': True, 'viewports': list(report), 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
