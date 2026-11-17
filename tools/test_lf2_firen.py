"""Complete classic Firen acceptance through the normal game entry.

Controlled fixtures isolate contacts/cancellation; --natural uses fresh Lv1
with real keyboard/touch and visible cards. Native cycles are separate footage.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
from playwright.sync_api import sync_playwright
import test_lf2_bosses as native

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art-review/firen/qa'
BASE=os.environ.get('LF2_FIREN_URL','http://127.0.0.1:8769/.omx/digimon.html')
HERO={'dex':30021,'api':'LF2Firen'}
IDS=['lf2-firen-ball','lf2-firen-blaze','lf2-firen-inferno','lf2-firen-explosion']


def hashes():
    names=['.omx/lf2-firen.js','.omx/lf2-firen-combat.js','.omx/lf2-firen-art.js','.omx/lf2-bosses.js',
           '.omx/lf2-boss-art.js','.omx/lf2-audio.js','.omx/naruto.js','.omx/digimon.html',
           'js/entities/enemy.js','js/systems/combat.js','js/systems/self-clone.js','js/systems/hazards.js']
    folder=ROOT/'assets/lf2/firen'
    if folder.exists():names.extend(p.relative_to(ROOT).as_posix() for p in folder.rglob('*') if p.is_file())
    result={}
    for name in names:
        path=ROOT/name
        if not path.is_file():continue
        data=path.read_bytes();digest=hashlib.sha256(data).hexdigest();result[name]=digest
        if path.suffix in {'.js','.html'}:
            target=OUT/'source-snapshots'/digest/path.name
            target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():target.write_bytes(data)
    return result


def boot(page,hero,label):
    url=BASE+('&' if '?' in BASE else '?')+'lang=zh-TW&hero=firen'
    if not label.startswith('mobile'):url+='&layout=wide'
    page.goto(url)
    page.wait_for_function("window.G?.LF2Firen&&G.LF2FirenKit&&document.getElementById('boot').classList.contains('hidden')",timeout=60000)
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.locator('[data-quick-naruto="30021"]').click()
    page.wait_for_function('G.NarutoAssets.ready(30021)',timeout=30000)
    page.screenshot(path=str(OUT/f'firen-{label}-selection.png'))
    learning=page.locator('.launch-kit>span').count()
    assert learning==4, f'Firen learning strip must expose all four skills: {learning}'
    page.locator('#scr-menu [data-go="play"]').click()
    page.wait_for_function('G.Game.player?.dex===30021&&G.Game.state==="playing"')
    page.screenshot(path=str(OUT/f'firen-{label}-normal-entry.png'))


SETUP=native.SETUP.replace('G.LF2Bosses.idsFor(dex)','G.LF2FirenKit.ids')
OBSERVE=native.OBSERVE.replace('G.LF2Bosses.idsFor(dex)','G.LF2FirenKit.ids')
# Observe actual cast-object closure independently from when the next cast starts.
OBSERVE=OBSERVE[:-1]+r'''
 {const Q=window.BossNatural,F=G.LF2Firen,closed={},oldSnapshot=Q.snapshot;let previous=new Map();
 Q.snapshot=()=>({...oldSnapshot(),completedWindows:{...closed}});
 function trackWindows(){
  if(G.Game.state==='playing'){
   const state=F.stateFor(G.Game.player),active=new Map();
   for(const f of [state?.action,...(state?.effects||[]).filter(e=>!e.dead).map(e=>e.action)]){
    if(!f||!Q.ids.includes(f.m?.id))continue;
    const key=f.cast?f.cast.runEpoch+':'+f.cast.castId:f;
    active.set(key,f.m.id);
   }
   for(const [key,id] of previous)if(!active.has(key))closed[id]=(closed[id]||0)+1;
   previous=active;
  }
  requestAnimationFrame(trackWindows);
 }requestAnimationFrame(trackWindows);}
}'''
PROGRESSION=native.PROGRESSION.replace('[30001,30006,30014,30017,30018,30019,30020]','[30001,30006,30014,30017,30018,30019,30020,30021]')
MECHANICS=r'''() => {
 const A=BAcceptance,p=A.p,F=A.F,out={};
 for(const id of A.ids){A.reset();const m=A.fixture(id),profile=F.profile(p(),m);
  A.assert(profile&&profile.damage>0,'missing real damage profile '+id);
  const e=A.spawn(id==='lf2-firen-ball'?250:45,0),hits=A.watch(e);
  if(id==='lf2-firen-blaze')A.input(1,0);
  A.cast(m);A.advance(8);
  A.assert(hits.some(h=>h.loss>0),'move did not cause actual contact '+id);
  A.assert(hits.every(h=>h.owner&&h.id===id),'move lost actor/id attribution '+id);
  out[id]={profile,hits};
 }
 return out;
}'''
IDENTITY=r'''() => {
 const A=BAcceptance,p=A.p,F=A.F,out={};
 A.reset();let m=A.fixture('lf2-firen-ball'),e=A.spawn(280,0),hits=A.watch(e);A.cast(m);A.advance(.19);
 A.assert(!hits.length&&!F.stateFor(p()).effects.some(e=>e.sourceObject==='firen_ball'),'FireBall emitted before original238');
 A.advance(.03);A.assert(!hits.length&&F.stateFor(p()).effects.some(e=>e.sourceObject==='firen_ball'),'FireBall skipped actual flight');A.advance(2);
 A.assert(hits.length>0&&hits.every(h=>h.owner&&h.id===m.id),'FireBall native contact or attribution failed');out.ballFlight=hits;
 A.reset();m=A.fixture('lf2-firen-ball');e=A.spawn(280,0);hits=A.watch(e);A.cast(m);G.World.isWall=(x,y)=>x>=105&&x<=125;A.advance(3);
 A.assert(!hits.length,'FireBall crossed wall');out.ballWall=true;
 A.reset();m=A.fixture('lf2-firen-blaze');e=A.spawn(60,0);hits=A.watch(e);A.input(1,0);A.cast(m);A.advance(.19);
 A.assert(!hits.length,'Blaze hurt before original257');A.advance(.06);A.assert(p().x>0&&hits.length>0,'Blaze did not really move/contact');out.blazeForward={x:p().x,hits};
 const previous=p().x;A.input(-1,0);A.advance(.25);A.assert(p().x<=previous+.01,'Blaze forced old forward pursuit against retreat input');out.blazeRetreat={before:previous,after:p().x};
 A.reset();m=A.fixture('lf2-firen-blaze');e=A.spawn(90,0);hits=A.watch(e);A.input(1,0);A.cast(m);
 G.World.isWall=(x,y)=>x>=20&&x<=30;G.World.isFree=(x,y)=>!G.World.isWall(x,y)&&x<=20;A.advance(3);
 A.assert(p().x<=20&&!hits.length,'Blaze crossed blocking floor or burned through wall');out.blazeWall={x:p().x,hits};
 A.reset();m=A.fixture('lf2-firen-blaze');A.spawn(55,0);A.input(1,0);A.cast(m);A.advance(.5);
 const old=F.stateFor(p()).effects.filter(e=>e.sourceObject==='firen_flame'&&e.sourceStart===50).map(e=>({ref:e,x:e.x,y:e.y}));
 A.assert(old.length>0,'Blaze omitted actual ground flame trail');A.input(0,1);A.advance(.3);
 A.assert(old.every(e=>e.ref.x===e.x&&e.ref.y===e.y),'Released Blaze ground flames dragged with owner');
 const duration=F.profile(p(),m).duration;A.advance(Math.max(0,duration-.8)+.03);
 const fire=F.stateFor(p()).effects.find(e=>e.sourceObject==='firen_flame'&&e.sourceStart===50&&e.life-e.age>.25);
 A.assert(fire&&!F.pose(p()),'Blaze left no independent fire after recovery');e=A.spawn(fire.x,fire.y);hits=A.watch(e);A.advance(.8);
 A.assert(hits.length>0,'Independent trail never damaged a new enemy');out.blazeTrail={old:old.map(e=>[e.x,e.y]),lateHits:hits};
 A.reset();m=A.fixture('lf2-firen-blaze');A.spawn(70,0);A.input(1,0);A.cast(m);A.advance(.3);
 G.EnemyMgr.clear();e=A.spawn(p().x+25,p().y);hits=A.watch(e);A.input(0,0);A.advance(.01);
 A.assert(!hits.length&&F.pose(p())?.phase==='recovery','Released Blaze still hit new victim in original218 recovery');A.advance(.2);
 A.assert(!hits.length,'Blaze recovery retained body contact');out.blazeRecovery=true;
 A.reset();m=A.fixture('lf2-firen-inferno');const cone=[[25,0],[70,5],[110,-5]].map(([x,y])=>A.spawn(x,y)),behind=A.spawn(-90,0),side=A.spawn(60,180),ch=cone.map(A.watch),bh=A.watch(behind),sh=A.watch(side);A.cast(m);A.advance(.35);
 A.assert(ch.every(h=>!h.length),'Inferno hurt before body271 plus visible particle0 warmup');A.advance(3);
 A.assert(ch.every(h=>h.length>0)&&!bh.length&&!sh.length,'Inferno did not produce directed true3in/2out stream');out.inferno={hits:ch,behind:bh,side:sh};
 A.reset();m=A.fixture('lf2-firen-inferno');e=A.spawn(100,0);hits=A.watch(e);A.cast(m);G.World.isWall=(x,y)=>x>=30&&x<=40;A.advance(4);
 A.assert(!hits.length,'Inferno or released flame crossed wall');out.infernoWall=true;
 A.reset();m=A.fixture('lf2-firen-explosion');const profile=F.profile(p(),m),hp=p().hp,cost=profile.healthCost,near=[[25,0],[-25,18],[0,-40]].map(([x,y])=>A.spawn(x,y)),far=A.spawn(profile.radius+180,0),nh=near.map(A.watch),fh=A.watch(far);p().invuln=0;A.cast(m);A.advance(.25);
 A.assert(p().hp===hp&&nh.every(h=>!h.length),'Explosion spent health or hit before release');A.advance(.06);
 A.assert(Math.abs((hp-p().hp)-cost)<1e-7&&nh.every(h=>!h.length),'Explosion payment/source109 warmup failed');A.advance(.05);
 A.assert(nh.every(h=>h.length===1)&&!fh.length&&p().invuln===0,'Explosion real area3in1out/no-free-immunity failed');A.advance(3);
 A.assert(nh.every(h=>h.length===1)&&Math.abs(hp-p().hp-cost)<1e-7,'Explosion fade repeated damage or paid twice');out.explosion={cost,hits:nh,outside:fh};
 A.reset();m=A.fixture('lf2-firen-explosion');e=A.spawn(30,0);hits=A.watch(e);A.cast(m);A.advance(8/30);
 const born=F.stateFor(p()).effects.find(e=>e.sourceObject==='firen_flame'&&e.sourceStart===109);
 A.assert(born&&Math.abs(born.age)<1e-8&&!hits.length,'Explosion effect pre-advanced its birth substep');A.advance(2/30-.0001);A.assert(!hits.length,'Explosion hit before full original109 warmup');A.advance(.0002);
 A.assert(hits.length===1,'Explosion missed original110 contact boundary');out.exactExplosionClock=true;
 A.reset();m=A.fixture('lf2-firen-explosion');e=A.spawn(80,0);hits=A.watch(e);A.cast(m);G.World.isWall=(x,y)=>x>=30&&x<=40;A.advance(3);A.assert(!hits.length,'Explosion crossed wall');out.explosionWall=true;
 A.reset();m=A.fixture('lf2-firen-explosion');A.spawn(35,0);const low=F.profile(p(),m).healthCost;p().hp=low;
 A.resume();try{A.assert(!F.canCast(p(),m)&&!F.cast(p(),m),'Insufficient health allowed suicide/free Explosion')}finally{A.pause()};A.advance(2);A.assert(p().hp===low,'Rejected Explosion changed health');out.insufficientHealth=true;
 A.reset();m=A.fixture('lf2-firen-explosion');e=A.spawn(30,0);hits=A.watch(e);A.cast(m);A.advance(.2);p().hp=F.profile(p(),m).healthCost;const lowDuring=p().hp;A.advance(3);
 A.assert(!hits.length&&p().hp===lowDuring,'Windup health loss produced free blast or self-kill');out.midWindupCancel=true;
 A.reset();m=A.fixture('lf2-firen-explosion');e=A.spawn(30,0);hits=A.watch(e);p().quantityPicks=p().quantityBonus=20;const q=F.profile(p(),m),startHp=p().hp;A.cast(m);A.advance(5);
 A.assert(q.count>1&&hits.length===q.count&&Math.abs(startHp-p().hp-q.healthCost)<1e-7,'Extra blast waves missing or charged extra health');out.multipleCostOnce={count:q.count,cost:q.healthCost,loss:startHp-p().hp,hits};
 A.reset();m=A.fixture('lf2-firen-explosion');A.spawn(30,0);const savedMax=p().maxHp,savedHp=p().hp,snapshotCost=F.profile(p(),m).healthCost;
 try{A.cast(m);p().maxHp*=1.5;A.advance(.28);A.assert(Math.abs(savedHp-p().hp-snapshotCost)<1e-7,'Explosion recomputed cost after release-time max-HP change');out.costSnapshot={cost:snapshotCost,loss:savedHp-p().hp};}
 finally{p().maxHp=savedMax;p().hp=savedHp;A.reset();}
 A.reset();m=A.fixture('lf2-firen-ball');m.t=999;e=A.spawn(40,0);hits=A.watch(e);A.advance(.09,true);
 A.assert(!hits.length,'Ordinary Firen punch hit before source61 at3ticks');A.advance(.03,true);A.assert(hits.length===1&&!e.burn,'Ordinary punch contact/burn differs');A.advance(.2,true);
 A.assert(hits.length===1,'Ordinary punch recovery repeated hit');out.ordinaryPunch=hits;
 return out;
}'''
LIFECYCLE=native.LIFECYCLE.replace("if(id==='lf2-julian-punch')A.input(1,0)","if(id==='lf2-firen-blaze')A.input(1,0)")
CONTACT_BOUNDARY=native.CONTACT_BOUNDARY.replace("if(id==='lf2-julian-punch')A.input(1,0)","if(id==='lf2-firen-blaze')A.input(1,0)")
GROWTH=native.GROWTH
QUANTITY_CONTACTS=r'''() => {
 const A=BAcceptance,p=A.p(),F=A.F,out=[];
 for(const id of ['lf2-firen-ball','lf2-firen-blaze','lf2-firen-inferno']){
  A.reset();const m=A.fixture(id),baseline=F.profile(p,m);
  for(let i=0;i<4;i++){const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:quantity');A.assert(card&&card.apply(p)!==false,'quantity card rejected '+id);}
  const profile=F.profile(p,m),e=A.spawn(id==='lf2-firen-ball'?280:id==='lf2-firen-blaze'?65:25,0),hits=A.watch(e);
  if(id==='lf2-firen-blaze')A.input(1,0);A.cast(m);A.advance(profile.duration+2);
  A.assert(profile.count>baseline.count,'quantity did not change count '+id);
  if(id==='lf2-firen-blaze')A.assert(F.stats(p).groundFires===profile.count*4&&F.stats(p).blazeDistance>baseline.range,'Blaze extra loops omitted actual trail/advance');
  else A.assert(hits.length===profile.count,'quantity did not produce the real independent contacts '+id+':'+hits.length+'/'+profile.count);
  out.push({id,baseline,profile,hits,stats:F.stats(p)});
 }
 return out;
}'''
GIANT=r'''() => {
 const A=BAcceptance,p=A.p(),F=A.F;A.reset();let m=A.fixture('lf2-firen-blaze');const before=F.profile(p,m);
 const saved={scale:p.anim.scale,r:p.r,bodyH:p.bodyH,maxHp:p.maxHp,hp:p.hp,spdMul:p.spdMul,cdMul:p.cdMul,giantPicks:p.giantPicks};
 let e=A.spawn(60,0);const extendedY=before.bodyRadius+e.r+3;e.y=extendedY;G.EnemyMgr.rebuildGrid();const baselineHits=A.watch(e);A.input(1,0);A.cast(m);A.advance(.4);
 A.assert(!baselineHits.length,'giant fixture was already inside normal body contact');
 A.reset();m=A.fixture('lf2-firen-blaze');e=A.spawn(60,extendedY);const hits=A.watch(e);A.input(1,0);
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:giant');A.assert(card,'real giant card absent');
 try{
  A.assert(card.apply(p)!==false,'giant card rejected');const after=F.profile(p,m);
  A.assert(after.bodyRadius>before.bodyRadius&&p.anim.scale>saved.scale,'Blaze giant body and physical reach did not grow');
  A.cast(m);A.advance(.4);A.assert(hits.length>0,'giant Blaze missed enlarged physical body contact');
  return {before,after,extendedY,baselineHits,hits};
 }finally{Object.assign(p,saved);p.anim.scale=saved.scale;delete p.scale;A.reset();}
}'''


def configure():
    native.OUT=OUT;native.BASE=BASE;native.HEROES={'firen':HERO}
    native.hashes=hashes;native.boot=boot;native.SETUP=SETUP;native.OBSERVE=OBSERVE


def controlled(browser,report):
    context=native.context_for(browser);page=context.new_page();native.observe_errors(page,report)
    boot(page,'firen','desktop');page.evaluate(SETUP,HERO)
    checks=[('progression',PROGRESSION),('mechanics',MECHANICS),('sourceIdentity',IDENTITY),
            ('growth',GROWTH),('quantityContacts',QUANTITY_CONTACTS),('giantBody',GIANT),('lifecycle',LIFECYCLE),('contactBoundary',CONTACT_BOUNDARY)]
    for name,check in checks:
        report['checks'][name]=page.evaluate(check);print('firen',name,'PASS',flush=True)
    context.close()


def natural(browser,report,mobile=False):
    native.natural(browser,report,'firen',mobile)
    label='mobile390' if mobile else 'desktop'
    record=report['natural'][label]
    closed=record['final'].get('completedWindows',{})
    assert all(closed.get(id,0)>0 for id in IDS), 'Native body/released-effect window not closed: '+str(closed)
    record['allFourNativeWindowsClosed']=True
    (OUT/'firen'/f'natural-{label}'/'report.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf-8')


def final_clip(browser,report):
    folder=OUT/'firen'/'final-cycles';folder.mkdir(parents=True,exist_ok=True)
    context=native.context_for(browser,folder);page=context.new_page();native.observe_errors(page,report)
    boot(page,'firen','final-cycles');page.evaluate(SETUP,HERO)
    page.evaluate(r'''() => {const A=BAcceptance;A.reset();const p=A.p();p.level=30;p.moves=A.ids.map(id=>G.Moves.instance(id,1));p.arrange();for(const m of p.moves)m.t=0;A.spawn(250,0);window.FinalCycleStart=G.Game.st.time;}''')
    page.evaluate(OBSERVE,HERO);page.evaluate('BAcceptance.resume()')
    page.wait_for_function('G.Game.st.time-FinalCycleStart>=1.7',timeout=10000)
    page.evaluate('for(const [x,y] of [[45,0],[125,20],[225,-20],[-40,0],[0,45],[0,-45],[90,80],[-90,-80]])BAcceptance.spawn(x,y)')
    held=None;started=time.monotonic();finished_at=None
    while time.monotonic()-started<120:
        scene=page.evaluate('''() => {const p=G.Game.player,F=BAcceptance.F,e=G.EnemyMgr.all().filter(e=>!e.dead).sort((a,b)=>Math.hypot(a.x-p.x,a.y-p.y)-Math.hypot(b.x-p.x,b.y-p.y))[0],snapshot=BossNatural.snapshot();return {mode:F.pose(p)?.mode,dx:e?e.x-p.x:0,dy:e?e.y-p.y:0,time:G.Game.st.time-FinalCycleStart,closed:snapshot.completedWindows,hitIds:[...new Set(BossNatural.hits.filter(h=>h.loss>0).map(h=>h.id))],activeLast:BossNatural.activeLast()}}''')
        complete=all(id in scene['hitIds'] and scene['closed'].get(id,0)>0 for id in IDS)
        if complete and finished_at is None:finished_at=scene['time']
        if finished_at is not None and scene['time']>=finished_at+4 and not scene['activeLast']:break
        key=None if scene['mode'] in ['lf2-firen-inferno','lf2-firen-explosion'] else ('KeyD' if scene['dx']>=0 else 'KeyA') if abs(scene['dx'])>=abs(scene['dy']) else ('KeyS' if scene['dy']>=0 else 'KeyW')
        if key!=held:
            if held:page.keyboard.up(held)
            if key:page.keyboard.down(key)
            held=key
        page.wait_for_timeout(65)
    if held:page.keyboard.up(held)
    data=page.evaluate('({frames:BossNatural.frames,stats:BAcceptance.F.stats(G.Game.player),hits:BossNatural.hits,hud:BossNatural.hud,snapshot:BossNatural.snapshot(),time:G.Game.st.time-FinalCycleStart,ids:BossNatural.ids})')
    data['scope']='Controlled Lv30/rank1, high-HP zero-damage targets; real keyboard/native RAF, no manual combat stepping. Separate from natural growth.'
    data['frames']=native.save_frames(folder,data['frames'])
    data['missingHits']=[id for id in IDS if not any(h['id']==id and h['loss']>0 for h in data['hits'])]
    data['closedWindows']=data['snapshot']['completedWindows']
    video=page.video;context.close();video.save_as(str(folder/'native-cycles.webm'));video.delete()
    report['finalCycles']=data;(folder/'report.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf-8')
    assert not data['missingHits'] and all(data['closedWindows'].get(id,0)>0 for id in IDS),'Native showcase omitted a real skill or full window'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--natural',action='store_true');parser.add_argument('--mobile',action='store_true');parser.add_argument('--final-cycles',action='store_true')
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True);configure()
    report={'hero':'firen','url':BASE,'errors':[],'checks':{},'natural':{},'sourceBefore':hashes()}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=native.CHROME,headless=True)
            if args.final_cycles:final_clip(browser,report)
            elif args.natural:natural(browser,report,args.mobile)
            else:controlled(browser,report)
            browser.close()
        assert not report['errors'],report['errors'];report['ok']=True
    except Exception as error:
        report['failure']=str(error);raise
    finally:
        report['sourceAfter']=hashes();report['sourceStable']=report['sourceBefore']==report['sourceAfter']
        report['changedPaths']=[name for name in set(report['sourceBefore'])|set(report['sourceAfter']) if report['sourceBefore'].get(name)!=report['sourceAfter'].get(name)]
        suffix='final-cycles-source' if args.final_cycles else 'natural-mobile-report' if args.natural and args.mobile else 'natural-report' if args.natural else 'report'
        (OUT/f'firen-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')


if __name__=='__main__':main()
