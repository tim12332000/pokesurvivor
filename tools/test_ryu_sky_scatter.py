"""Ryu's physical rise/orbit/seek volley through the normal game entry.

Enemy/terrain fixtures are controlled; casts, cards, movement, damage, owner
identity, world cancellation and renderer are production code.
"""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('RYU_SKY_OUT', ROOT / '.omx/state/ryu-sky-scatter/mechanics'))

CHECK = r"""() => {
 const A=JAcceptance,p=A.p(),R=G.JjkRyu,assert=A.assert,id='jjk-ryu-spread',out={};
 const setup=(rank=1,q=0)=>{A.reset();const m=A.fixture(id,rank);p.quantityPicks=p.quantityBonus=q;return m;};
 const shots=(owner=p)=>R.stateFor(owner)?.scatter||[];
 const cast=(m,owner=p)=>{A.resume();try{assert(R.cast(owner,m),'sky volley did not cast')}finally{A.pause()};return R.pose(owner);};
 const finish=()=>A.advance(8);
 const until=(test,seconds=6)=>{for(let t=0;t<seconds;t+=.01){if(test())return;A.advance(.01)}throw Error('sky phase timed out')};
 assert(typeof R.scatterFor==='function','shared scatter profile absent');
 for(const [rank,q,count,range] of [[1,0,8,800],[1,1,10,800],[5,0,10,1120],[5,20,18,1120]]){
  const m=setup(rank,q),profile=R.scatterFor(p,m),victim=A.spawn(620,0),events=A.watch(victim),f=cast(m);
  assert(profile.count===count&&profile.range===range&&profile.travelRange===range*1.6,'rank/card shared profile differs '+rank+'/'+q+': '+JSON.stringify(profile));
  A.advance(f.charge+.02);assert(shots().length===count,'doubled volley emitted wrong real bolt count');
  assert(shots().every(s=>s.phase==='rise'&&s.target==null),'bolts skipped physical rise or preselected targets');
  assert(events.length===0,'damage occurred during launch');
  A.advance(profile.rise+.12);
  assert(shots().every(s=>s.phase==='orbit'&&s.lift>40&&s.target==null),'independent airborne orbit missing');
  assert(new Set(shots().map(s=>s.orbitDuration)).size===count,'bolts reused one orbit departure clock');
  assert(events.length===0,'orbit damaged ground targets');
  const orbit=shots().map(s=>({x:s.x,y:s.y,lift:s.lift}));A.advance(.12);
  assert(shots().some((s,i)=>Math.hypot(s.x-orbit[i].x,s.y-orbit[i].y)>5),'orbit is only decorative rotation');
  assert(shots().every(s=>Number.isFinite(s.visualAngle)&&s.trail.length<=28),'non-finite angle or unbounded trail');
  finish();
  const contacts=G.CombatPulse.telemetry.filter(t=>t.castId===f.castId&&t.runEpoch===f.runEpoch);
  assert(events.length===count,'actual same-target payload differs from physical count '+rank+'/'+q+': '+events.length);
  assert(contacts.length===count&&contacts.every(t=>t.primaryHits===1)&&new Set(contacts.map(t=>t.contactPulseIndex)).size===count,'projectiles reused contact identities or pierced');
  assert(events.every(h=>h.owner&&h.id===id&&h.loss>0),'volley lost owner/move attribution');
  assert(!shots().length&&!R.pose(p),'completed volley retained projectiles/body');
  out['rank'+rank+'q'+q]={profile,hits:events.length,damage:events.reduce((n,h)=>n+h.loss,0),contacts:contacts.map(t=>t.contactPulseIndex)};
 }
 // Exercise real acquisition near both tier limits, including the native
 // automatic scheduler; count fixtures at620 alone cannot prove1120 reach.
 out.range=[];
 for(const [rank,distance,mode] of [[1,760,'manual'],[1,760,'automatic'],[5,1080,'automatic']]){
  const m=setup(rank),profile=R.scatterFor(p,m),victim=A.spawn(distance,0),events=A.watch(victim);
  A.resume();try{assert(R.canCast(p,m),'in-range distant target cannot trigger '+rank+'/'+mode)}finally{A.pause()}
  if(mode==='manual')cast(m);else{A.advance(.02,true);assert(R.stats(p)?.casts[id]===1,'automatic scheduler did not trigger distant volley '+rank)}
  finish();assert(events.length===profile.count&&victim.hp<victim.maxHp,'distant tier acquisition lost real payload '+rank+'/'+distance+'/'+mode+': '+events.length);
  out.range.push({rank,distance,mode,hits:events.length});
 }
 for(const rank of [1,5]){
  const m=setup(rank),profile=R.scatterFor(p,m),outside=A.spawn(profile.range+120,0);
  A.resume();try{assert(!R.canCast(p,m),'outside-tier lone target triggered a volley '+rank)}finally{A.pause()}
  A.advance(.4,true);assert(!R.stats(p)?.casts[id]&&!shots().length&&outside.hp===outside.maxHp,'automatic scheduler spent a volley beyond tier range '+rank);
 }
 // Selection happens after the orbit, so a target removed during preparation
 // cannot monopolize a volley or turn it into non-damaging decoration.
 let m=setup(),old=A.spawn(700,0),f=cast(m);A.advance(f.charge+.4);
 assert(shots().every(s=>s.target==null),'airborne preparation locked stale targets');
 old.dead=true;old.hp=0;G.EnemyMgr.removeRemote(old.id,false);
 const replacement=A.spawn(670,60);finish();
 assert(replacement.hp<replacement.maxHp,'orbit end failed to acquire the current live target');out.lateSelection=true;
 m=setup();const moving=A.spawn(620,0);cast(m);until(()=>shots().some(s=>s.phase==='seek'));
 for(let i=0;i<70;i++){moving.x+=.45;moving.y+=.2;G.EnemyMgr.rebuildGrid();A.advance(.01)}
 finish();assert(moving.hp<moving.maxHp,'far moving target escaped all live homing');out.movingTarget=true;
 m=setup();const doomed=A.spawn(620,0);cast(m);until(()=>shots().some(s=>s.phase==='seek'));
 doomed.dead=true;doomed.hp=0;G.EnemyMgr.removeRemote(doomed.id,false);const fresh=A.spawn(650,90);finish();
 assert(fresh.hp<fresh.maxHp,'seeking bolts did not retarget a removed enemy');out.retarget=true;
 // At least three separated approaches receive real damage; a distant control
 // outside the acquisition/travel footprint cannot be hit accidentally.
 m=setup();const group=[[520,0],[350,400],[-470,160]].map(v=>A.spawn(...v)),outside=A.spawn(2400,0);cast(m);finish();
 assert(group.every(e=>e.hp<e.maxHp)&&outside.hp===outside.maxHp,'distributed long-range coverage or outside boundary failed');out.distributed=group.map(e=>e.maxHp-e.hp);
 m=setup();const distant=A.spawn(700,0);cast(m);
 G.World.isWall=(x,y)=>x>=220&&x<=240;G.World.projectileBlock=(x,y)=>G.World.isWall(x,y)?'wall':false;
 finish();assert(distant.hp===distant.maxHp,'seeking cannon crossed a solid wall');out.wall=true;
 // The original cast can continue through several real contacts, but only
 // one earned maximum charge belongs to that entire volley.
 m=setup();assert(p.addMove('jjk-ryu-maximum'),'maximum learn failed');const chargeTarget=A.spawn(620,0);cast(m);finish();
 assert(R.stateFor(p).hits>=2&&R.stateFor(p).coreCharge===1&&chargeTarget.hp<chargeTarget.maxHp,'multi-bolt volley charged maximum more than once');out.chargeOnce=true;
 for(const mode of ['clear','unlearn']){
  m=setup();const first=A.spawn(620,0),second=A.spawn(620,0),events=[A.watch(first),A.watch(second)];cast(m);
  const previous=p.onDealt;p.onDealt=function(...args){if(mode==='clear')G.Combat.clearFields(p);else p.moves=[];return previous.apply(this,args)};
  try{finish()}finally{p.onDealt=previous}
  assert(events.reduce((n,h)=>n+h.length,0)===1&&!shots().length,'same-update callback allowed later bolt damage '+mode);out['callback-'+mode]=true;
 }
 for(const mode of ['death','clear','unlearn','world','epoch']){
  m=setup();const e=A.spawn(620,0);f=cast(m);A.advance(f.charge+.4);const hp=e.hp,world=G.World;
  if(mode==='death'){p.dead=true;p.hp=0}if(mode==='clear')G.Combat.clearFields(p);if(mode==='unlearn')p.moves=[];
  if(mode==='world')G.World=Object.create(world);if(mode==='epoch')G.CombatPulse.beginRun();
  try{finish()}finally{G.World=world}
  assert(e.hp===hp&&!shots().length,'airborne lifecycle retained later damage '+mode);out[mode]=true;
 }
 m=setup();A.spawn(620,0);f=cast(m);A.advance(f.charge+.4);
 const snapshot=()=>JSON.stringify({stats:R.stats(p),shots:shots().map(s=>({x:s.x,y:s.y,lift:s.lift,age:s.age,phase:s.phase,trail:s.trail}))});
 const frozen=snapshot();R.update(5);assert(snapshot()===frozen,'pause advanced the airborne volley');
 const canvas=document.createElement('canvas');canvas.width=canvas.height=1000;const ctx=canvas.getContext('2d');out.draw={};
 for(const quality of ['high','low']){
  G.JujutsuVFX.setQuality(quality);ctx.clearRect(0,0,1000,1000);ctx.save();ctx.translate(500,500);G.Combat.drawAirFields(ctx);ctx.restore();
  let visible=0;const rgba=ctx.getImageData(0,0,1000,1000).data;for(let i=3;i<rgba.length;i+=4)visible+=Number(rgba[i]>30);
  assert(visible>50&&snapshot()===frozen,'quality hid real bolts or drawing changed simulation '+quality);out.draw[quality]={visible};
 }
 assert(!R.pose(p)&&shots().length,'independent flight monopolized the body');out.pauseAndReadonly=true;
 m=setup();A.spawn(620,0);const clone=G.SelfClones.summon(p);assert(clone,'native clone absent');clone.x=clone.y=0;
 const cm=clone.moves.find(x=>x.id===id);assert(cm,'clone lost scatter');cm.t=0;const ownerCast=cast(m),cloneCast=cast(cm,clone);
 assert(ownerCast.castId!==cloneCast.castId,'clone shared owner cast identity');R.clear(p);finish();
 assert(!R.stateFor(p)&&R.stats(clone)?.hits>0,'owner clear cancelled independent clone flight');out.cloneHits=R.stats(clone).hits;
 // Genuine learn/upgrade/quantity callbacks, rather than fixture rank setters.
 A.reset();p.moves=[];p.slots=[];p.level=2;p.statsTaken={};p.addMove('jjk-ryu');p.arrange();
 assert(!G.Moves.poolFor(p.mon).includes(id),'spread unlocked before Lv3');p.level=3;
 const learn=G.LevelUp.offer(p,1000).find(c=>c.key==='new:'+id);assert(learn&&learn.apply(p)!==false,'normal Lv3 spread card absent');
 m=p.moves.find(x=>x.id===id);const counts=[R.scatterFor(p,m).count],previews=[];
 for(let i=0;i<3;i++){const q=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');assert(q,'useful quantity card absent');previews.push(q.desc);q.apply(p);counts.push(R.scatterFor(p,m).count)}
 assert(counts.join(',')==='8,10,12,15','actual quantity growth differs '+counts);
 for(let i=0;i<4;i++){const up=G.LevelUp.offer(p,1000).find(c=>c.key==='up:'+id);assert(up&&up.apply(p)!==false,'native spread upgrade missing')}
 assert(m.lvl===5&&R.scatterFor(p,m).range===1120,'rank growth failed to extend genuine tracking');
 assert(R.scatterFor(p,m).count===18&&!G.LevelUp.offer(p,1000).some(c=>c.key==='stat:quantity'),'capped scatter offered a useless quantity card');
 out.legalGrowth={counts,previews,profile:R.scatterFor(p,m)};
 return out;
}"""


class Server(ThreadingHTTPServer):
    request_queue_size = 128


class Handler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *_args):
        pass

    def do_GET(self):
        try:
            super().do_GET()
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            pass


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base.OUT = OUT
    base.URL = os.environ.get('RYU_SKY_URL') or os.environ.get('JUJUTSU_URL')
    server = None
    if not base.URL:
        server = Server(('127.0.0.1', 0), partial(Handler, directory=str(ROOT)))
        Thread(target=server.serve_forever, daemon=True).start()
        base.URL = f'http://127.0.0.1:{server.server_port}/.omx/digimon.html?lang=zh-TW'
    report = {'url': base.URL, 'views': {}, 'errors': []}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
            for label, width, mobile in [('desktop', 1280, False), ('mobile390', 390, True)]:
                context = browser.new_context(viewport={'width': width, 'height': 900 if not mobile else 844}, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                try:
                    frame = base.boot(page, 30014, label)
                    report['views'][label] = frame.evaluate(CHECK)
                except Exception:
                    page.screenshot(path=str(OUT / f'{label}-failure.png'))
                    raise
                finally:
                    context.close()
                    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
        (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        print(json.dumps({'ok': True, 'views': list(report['views']), 'evidence': str(OUT)}))
    finally:
        if server:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    main()
