"""Physical curved-ring skill contracts through the production Sendai entry.

Terrain and stationary enemies are controlled fixtures; card offers, move
instances, actor ownership, collision, damage and rendering remain native.
"""
from __future__ import annotations

import json
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright
import test_jujutsu as base

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('RYU_RING_OUT', ROOT / '.omx/state/ryu-ring/mechanics'))

CHECK = r"""() => {
 const A=JAcceptance,p=A.p(),R=G.JjkRyu,assert=A.assert,id='jjk-ryu-ring',out={};
 const setup=(rank=1,q=0)=>{A.reset();const m=A.fixture(id,rank);p.quantityPicks=p.quantityBonus=q;return m;};
 const spawn=(x,y)=>{const e=A.spawn(x,y);e.r=4;return e;};
 const cast=(m,owner=p)=>{A.resume();try{assert(R.cast(owner,m),'ring did not cast')}finally{A.pause()};return R.pose(owner);};
 const finish=(profile)=>A.advance(profile.charge+profile.duration+.25);
 const rings=(owner=p)=>R.stateFor(owner)?.rings||[];
 assert(R.supports(id)&&typeof R.ringFor==='function','ring runtime/profile missing');
 for(const [rank,q,count,radius,width] of [[1,0,4,112,18],[1,1,5,112,18],[5,0,8,180,30],[5,20,16,180,30]]){
  const m=setup(rank,q),profile=R.ringFor(p,m),victims=[[radius,0],[0,radius],[-radius,0],[0,-radius]].map(v=>spawn(...v));
  const outside=spawn(radius+width+60,80),events=victims.map(A.watch);
  assert(profile.count===count&&profile.radius===radius&&profile.width===width,'profile/card/rank contract differs '+rank+'/'+q+': '+JSON.stringify(profile));
  const f=cast(m);A.advance(profile.charge+profile.interval+.01);
  // The visible first-lap ingress is physical. Only after it closes is the
  // entire inner region hollow, including the original muzzle feed corridor.
  const center=spawn(0,0);A.advance(profile.duration-profile.interval+.25);
  assert(events.every(h=>h.length===count),'one-hit-per-circuit failed '+rank+'/'+q+': '+events.map(h=>h.length));
  assert(center.hp===center.maxHp&&outside.hp===outside.maxHp,'ring became filled disk or exceeded physical boundary '+rank+'/'+q+' aim='+f.aim+' centerLoss='+(center.maxHp-center.hp)+' outsideLoss='+(outside.maxHp-outside.hp));
  assert(events.flat().every(h=>h.owner&&h.id===id&&h.loss>0),'ring lost owner/move attribution');
  assert(!rings().length&&!R.pose(p),'completed ring/body retained active state');
  out['rank'+rank+'q'+q]={profile,hits:events.map(h=>h.length),damage:victims.map(e=>e.maxHp-e.hp),castId:f.castId};
 }
 // Trigger range includes the physical tube, while a lone out-of-band enemy
 // cannot spend the cooldown on a ring that will never reach it.
 let outerMove=setup(),outerProfile=R.ringFor(p,outerMove),outerTarget=spawn(outerProfile.radius+outerProfile.width*.7,0);
 cast(outerMove);finish(outerProfile);assert(outerTarget.hp<outerTarget.maxHp,'valid outer tube failed to trigger/hit');
 outerMove=setup();outerProfile=R.ringFor(p,outerMove);spawn(outerProfile.radius+outerProfile.width+10,0);
 A.resume();try{assert(!R.canCast(p,outerMove),'unreachable outer target triggered ring')}finally{A.pause()};out.outerTrigger=true;
 // The head starts along a curved lead before the full hollow circle exists.
 let m=setup(),profile=R.ringFor(p,m),near=spawn(profile.radius-1,0),far=spawn(-profile.radius,0),a=A.watch(near),b=A.watch(far),f=cast(m);
 A.advance(profile.charge-.01);assert(!a.length&&!b.length,'damage preceded forehead release');
 A.advance(.05);assert(!b.length,'far-side ring appeared before curved beam reached it');
 const ring=rings()[0];assert(ring&&ring.points.length>1&&ring.segments.length,'release did not create physical growing curve');
 A.advance(profile.interval+.02);assert(a.length>0&&b.length>0,'first circle failed to reach both sides');
 out.curveTiming={nearHits:a.length,farHits:b.length,points:ring.points.length,segments:ring.segments.length};
 // Owner motion is sampled live; later circuits follow current position.
 m=setup();profile=R.ringFor(p,m);spawn(profile.radius,0);cast(m);A.advance(profile.charge+profile.interval+.01);
 const old=spawn(-profile.radius,0),moved=spawn(400-profile.radius,0);p.x=400;p.aim=0;G.EnemyMgr.rebuildGrid();A.advance(profile.interval+.04);
 assert(moved.hp<moved.maxHp&&old.hp===old.maxHp,'moving ring used stale origin or swept a teleport chord');
 out.movingOwner={newDamage:moved.maxHp-moved.hp,oldDamage:old.maxHp-old.hp};
 // Moving enemies are tested at the collision clock, not cast-time positions.
 m=setup();profile=R.ringFor(p,m);spawn(profile.radius,0);const enters=spawn(400,100),leaves=spawn(-profile.radius,0);cast(m);
 enters.x=0;enters.y=profile.radius;leaves.x=-400;G.EnemyMgr.rebuildGrid();finish(profile);
 assert(enters.hp<enters.maxHp&&leaves.hp===leaves.maxHp,'ring ignored live enemy positions');out.movingEnemy=true;
 // A wall on the lead/first arc clips subsequent physical beam travel.
 m=setup();profile=R.ringFor(p,m);const blocked=spawn(profile.radius,0);cast(m);
 G.World.isWall=(x,y)=>x>=40&&x<=55;G.World.projectileBlock=(x,y)=>G.World.isWall(x,y)?'wall':false;finish(profile);
 assert(blocked.hp===blocked.maxHp,'ring crossed solid wall');out.wall=true;
 // Damage callbacks must cancel both the rest of this contact and future laps.
 for(const mode of ['clear','unlearn']){
  m=setup();profile=R.ringFor(p,m);const first=spawn(profile.radius,0),second=spawn(profile.radius,0),h1=A.watch(first),h2=A.watch(second);cast(m);
  const previous=p.onDealt;p.onDealt=function(...args){if(mode==='clear')G.Combat.clearFields(p);else p.moves=[];return previous.apply(this,args)};
  try{finish(profile)}finally{p.onDealt=previous}
  assert(h1.length===1&&!h2.length,'same-contact cancellation hit second target '+mode+': '+h1.length+'/'+h2.length);
  A.advance(2);assert(h1.length===1&&!h2.length,'cancelled ring retained future damage '+mode);out['callback-'+mode]=true;
 }
 // A secondary victim can invalidate the cast too. It has no primary onHit
 // hook, so the cast validity guard must also protect the outer splash loop.
 for(const mode of ['clear','unlearn']){
  m=setup();profile=R.ringFor(p,m);spawn(profile.radius,0);const outer=[spawn(profile.radius+40,0),spawn(profile.radius+48,0)];
  p.damageSplashPicks=1;let secondaryHits=0;
  for(const e of outer){const hurt=e.hurt;e.hurt=function(...args){const result=hurt.apply(this,args);secondaryHits++;
   if(secondaryHits===1){if(mode==='clear')G.Combat.clearFields(p);else p.moves=[]}return result};}
  cast(m);finish(profile);assert(secondaryHits===1,'secondary callback reached subsequent victim '+mode+': '+secondaryHits);
  A.advance(2);assert(secondaryHits===1,'secondary cancellation retained later ring contacts '+mode);out['secondary-'+mode]=true;
 }
 m=setup();profile=R.ringFor(p,m);spawn(profile.radius,0);cast(m);A.advance(profile.charge+.04);
 const before=JSON.stringify({age:rings()[0]?.age,points:rings()[0]?.points,damage:R.stats(p)?.damage});R.update(5);
 assert(before===JSON.stringify({age:rings()[0]?.age,points:rings()[0]?.points,damage:R.stats(p)?.damage}),'pause advanced physical ring');out.pause=true;
 for(const mode of ['death','clear','unlearn','world','epoch']){
  m=setup();profile=R.ringFor(p,m);const e=spawn(-profile.radius,0);cast(m);A.advance(profile.charge+.02);const hp=e.hp,world=G.World;
  if(mode==='death'){p.dead=true;p.hp=0}if(mode==='clear')G.Combat.clearFields(p);if(mode==='unlearn')p.moves=[];
  if(mode==='world')G.World=Object.create(world);if(mode==='epoch')G.CombatPulse.beginRun();
  try{A.advance(2)}finally{G.World=world}
  assert(e.hp===hp&&!rings().length&&!R.pose(p),'cancel retained ring contacts '+mode);out[mode]=true;
 }
 // Draw from the production VFX path at two qualities and prove no simulation mutation.
 m=setup();profile=R.ringFor(p,m);spawn(profile.radius,0);cast(m);A.advance(profile.charge+profile.interval+.02);
 const c=document.createElement('canvas');c.width=c.height=700;const ctx=c.getContext('2d');
 const snapshot=()=>JSON.stringify({clock:R.stateFor(p).clock,damage:R.stats(p).damage,rings:rings().map(r=>({age:r.age,cycle:r.cycle,lapIndex:r.lapIndex,points:r.points,segments:r.segments}))});
 const stable=snapshot();out.draw={};
 for(const quality of ['high','low']){
  G.JujutsuVFX.setQuality(quality);ctx.clearRect(0,0,700,700);ctx.save();ctx.translate(350,350);G.Combat.drawAirFields(ctx);ctx.restore();
  const rgba=ctx.getImageData(0,0,700,700).data;let visible=0;for(let i=3;i<rgba.length;i+=4)visible+=Number(rgba[i]>30);
  assert(visible>100,'production '+quality+' ring is invisible');assert(snapshot()===stable,'drawing mutated ring simulation');
  out.draw[quality]={visible,draws:G.JujutsuVFX.inspect().draws.filter(d=>/ring/i.test(d.kind||''))};
 }
 // Short body animation ends while the independent circular cannon remains active.
 assert(!R.pose(p)&&rings().length,'ring monopolized body or expired before full circuit');
 assert(p.addMove('jjk-ryu'),'could not learn core alongside ring');const core=p.moves.find(x=>x.id==='jjk-ryu');core.t=0;
 assert(cast(core),'independent ring blocked core cannon');out.bodyParallel=true;
 m=setup();profile=R.ringFor(p,m);spawn(profile.radius,0);const clone=G.SelfClones.summon(p);assert(clone,'native clone missing');
 clone.x=clone.y=0;const cm=clone.moves.find(x=>x.id===id);assert(cm,'clone lacks ring');cm.t=0;const pcast=cast(m),ccast=cast(cm,clone);
 assert(pcast.castId!==ccast.castId,'clone shared ring cast');R.clear(p);A.advance(profile.charge+profile.duration+.1);
 assert(!R.stateFor(p)&&R.stats(clone)?.hits>0,'owner clear cancelled independent clone ring');out.clone={hits:R.stats(clone).hits};
 // Use actual card callbacks and pool gates; direct rank fixtures are separate.
 A.reset();p.moves=[];p.slots=[];p.level=4;
 assert(!G.Moves.poolFor(p.mon).includes(id),'ring unlocked below Lv5');p.level=5;
 const learn=G.LevelUp.offer(p,1000).find(c=>c.key==='new:'+id);assert(learn&&learn.apply(p)!==false,'normal Lv5 learn card missing');
 m=p.moves.find(x=>x.id===id);p.statsTaken={};const counts=[R.ringFor(p,m).count],previews=[];
 for(let i=0;i<3;i++){const q=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');assert(q,'useful quantity missing');previews.push(q.desc);q.apply(p);counts.push(R.ringFor(p,m).count)}
 assert(counts.join(',')==='4,5,6,7','actual quantity picks differ '+counts);
 for(let i=0;i<4;i++){const up=G.LevelUp.offer(p,1000).find(c=>c.key==='up:'+id);assert(up&&up.apply(p)!==false,'normal upgrade missing')}
 profile=R.ringFor(p,m);assert(m.lvl===5&&profile.radius===180&&profile.width===30,'upgrades did not change real ring geometry');
 const lastQuantity=G.LevelUp.offer(p,1000).find(c=>c.key==='stat:quantity');assert(lastQuantity,'last useful ring quantity card missing');lastQuantity.apply(p);
 assert(R.ringFor(p,m).count===16&&!G.LevelUp.offer(p,1000).some(c=>c.key==='stat:quantity'),'ring cap offered useless quantity card');
 const nativeMon=p.mon;
 for(const dex of [30001,30007,30013,30015]){p.mon=G.DEX_BY[dex];assert(!G.Moves.poolFor(p.mon).includes(id),'ring pool leaked to '+dex)}p.mon=nativeMon;
 out.legalGrowth={counts,previews,rank:m.lvl,profile,cap:R.ringFor(p,m).count,isolated:true};
 return out;
}"""


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base.OUT = OUT
    server = None
    base.URL = os.environ.get('JUJUTSU_URL')
    if not base.URL:
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(ROOT)))
        Thread(target=server.serve_forever, daemon=True).start()
        base.URL = f'http://127.0.0.1:{server.server_port}/.omx/digimon.html?lang=zh-TW'
    report = {'url': base.URL, 'viewports': {}, 'errors': []}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=base.CHROME, headless=True)
            for label, viewport, mobile in [('desktop', {'width': 1280, 'height': 900}, False), ('mobile390', {'width': 390, 'height': 844}, True)]:
                context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
                page = context.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                try:
                    frame = base.boot(page, 30014, label)
                    report['viewports'][label] = frame.evaluate(CHECK)
                except Exception:
                    page.screenshot(path=str(OUT / f'{label}-failure.png'))
                    raise
                finally:
                    context.close()
                    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
            browser.close()
        assert not report['errors'], report['errors']
        print(json.dumps({'ok': True, 'views': list(report['viewports']), 'evidence': str(OUT)}))
    finally:
        if server:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    main()
