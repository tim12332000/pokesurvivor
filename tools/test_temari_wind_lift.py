"""Native wind-wave bump/control acceptance, including controlled JSON Coop.

Uses the production picker, cast collision, enemy AI/separation and rendering.
The Coop adapter is deterministic JSON forwarding, not real WebRTC coverage.
"""
import base64
import json
import os

from playwright.sync_api import sync_playwright
from test_temari import CHROME, OUT, URL, boot
from test_temari_coop import ADAPTER, pump


FIXTURE = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;
 A.assert(T.held&&T.liftFor&&T.liftForState,'wind lift runtime API missing');
 A.liftReset=()=>{A.reset();p.moves=p.moves.filter(m=>m.id==='naruto-temari');A.mastery(0)};
 A.liftStep=(dt=.01,enemyAI=true)=>{A.resume();try{
   if(enemyAI)G.EnemyMgr.update(dt,[p]);
   G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,0);
   G.Combat.updateFields(dt);G.FX.update(dt);p.anim.update(dt);
 }finally{A.pause()}};
 A.liftSpawn=(x,y,special=null)=>{const e=A.spawn(x,y,special);e.spd=65;return e};
 A.waitLift=e=>{for(let i=0;i<150&&!T.held(e);i++)A.liftStep(.005,false);A.assert(T.held(e),'wave did not bump native enemy');return T.liftForState(e)};
 A.liftPicture=()=>{const c=document.createElement('canvas');c.width=innerWidth;c.height=innerHeight;
   const x=c.getContext('2d');x.fillStyle='#223d38';x.fillRect(0,0,c.width,c.height);
   x.translate(c.width*.23,c.height*.54);x.imageSmoothingEnabled=false;
   G.Combat.drawGroundFields(x);const sources=[],draw=x.drawImage.bind(x);
   x.drawImage=(image,...args)=>{sources.push(image.src||'white-flash-canvas');return draw(image,...args)};
   for(const e of G.EnemyMgr.all())e.draw(x);x.drawImage=draw;
   A.assert(sources.some(src=>/assets\/pokemon\/19\//.test(src)),'native enemy body atlas did not load before evidence capture '+JSON.stringify(sources));p.draw(x);
   G.Projectiles.draw(x);G.Combat.drawAirFields(x);G.FX.draw(x);return c.toDataURL()};
}"""

LOCAL = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out={};
 A.liftReset();const spread=[-18,-9,0,9,18].map(deg=>A.liftSpawn(140*Math.cos(deg*Math.PI/180),140*Math.sin(deg*Math.PI/180)));
 const outside=A.liftSpawn(80,150),behind=A.liftSpawn(-90,0),far=A.liftSpawn(650,0);
 p.target=spread[2];A.castNative('naruto-temari');for(let i=0;i<110;i++)A.liftStep(.005,false);
 A.assert(spread.every(e=>T.held(e)),'45 degree wave failed to bump all five spread mobs');
 A.assert([outside,behind,far].every(e=>!T.held(e)&&e.hp===e.maxHp),'outside/unhit mob was damaged or held');
 out.spread=spread.map(e=>({x:e.x,y:e.y,lift:T.liftFor(e),hp:e.hp}));
 const e=spread[2],pos={x:e.x,y:e.y};e.jumpLift=7;
 // Deliberate overlap forces native EnemyMgr.separate as well as actual AI.
 const neighbor=A.liftSpawn(e.x+1,e.y);neighbor.spd=0;
 for(let i=0;i<8;i++){e.kx=150;e.ky=90;A.liftStep(.01);
   A.assert(e.x===pos.x&&e.y===pos.y,'held mob advanced through AI/knockback/separation');
   A.assert(e.jumpLift===7,'Temari bump overwrote native jumpLift');}
 A.assert(T.liftFor(e)>0,'held mob has no positive visual height');
 const hold=T.liftForState(e);out.hold={age:hold.age,duration:hold.duration,height:T.liftFor(e),x:e.x,y:e.y};
 for(let i=0;i<40;i++)A.liftStep(.01);
 A.assert(!T.held(e)&&T.liftFor(e)===0,'bump did not release at landing');
 A.assert(e.x!==pos.x||e.y!==pos.y,'enemy did not resume native forward movement');
 A.assert(e.jumpLift===7,'landing changed native jumpLift');out.resumed={x:e.x,y:e.y};
 out.specials=[];
 for(const special of ['boss','elite','legend','judge']){A.liftReset();const mob=A.liftSpawn(110,0,special);p.target=mob;
   A.castNative('naruto-temari');let max=0;for(let i=0;i<150;i++){A.liftStep(.01,false);max=Math.max(max,T.liftFor(mob));A.assert(!T.held(mob),'special held: '+special)}
   A.assert(mob.hp<mob.maxHp,'immune special unexpectedly missed wind damage');out.specials.push({special,max,damage:mob.maxHp-mob.hp});}
 out.growth=[];
 for(const Q of [0,5,10,20]){A.liftReset();A.mastery(5);p.quantityBonus=p.quantityPicks=Q;
   const mob=A.liftSpawn(150,0);p.target=mob;A.castNative('naruto-temari');let starts=0,was=false,first=null,last=null,total=0;
   for(let i=0;i<500;i++){A.liftStep(.01,false);const held=T.held(mob);if(held&&!was){starts++;first??=i*.01}if(held){last=i*.01;total+=.01}was=held;}
   A.assert(starts===1,'N/R recuts refreshed or repeated bump Q'+Q+': '+starts);
   A.assert(total>=.28&&total<=.31,'hold length amplified by quantity/mastery Q'+Q+': '+total);
   A.assert(!T.held(mob)&&T.liftFor(mob)===0,'high quantity left permanent control');out.growth.push({Q,starts,first,last,total,hits:T.stateFor(p).latest.hits});}
 out.cleanup=[];
 for(const mode of ['pause','clear','ownerDead','enemyDead','world']){A.liftReset();const mob=A.liftSpawn(130,0);p.target=mob;A.castNative('naruto-temari');A.waitLift(mob);
   if(mode==='pause'){const age=T.liftForState(mob).age;T.update(1);A.assert(T.liftForState(mob).age===age,'pause consumed control lifetime');}
   else if(mode==='clear')T.clear(p);
   else if(mode==='ownerDead'){p.dead=true;A.liftStep(.01,false);p.dead=false;}
   else if(mode==='enemyDead'){mob.dead=true;A.liftStep(.01,false);}
   else {const world=G.World;try{G.World=Object.create(world);A.liftStep(.01,false)}finally{G.World=world}}
   if(mode!=='pause')A.assert(!T.held(mob)&&T.liftFor(mob)===0,'stale bump after '+mode);out.cleanup.push(mode);}
 A.liftReset();const mob=A.liftSpawn(130,0),snap=T.snapshot(p,p.moves.find(m=>m.id==='naruto-temari'));snap.aim=0;snap.targetPositions=[{x:130,y:0}];
 const hp=mob.hp;T.ghost(p,snap);for(let i=0;i<150;i++)A.liftStep(.01,false);
 A.assert(mob.hp===hp&&!T.held(mob),'ghost visual applied damage/control');out.ghost={damage:hp-mob.hp,held:T.held(mob)};
 A.liftReset();const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');A.assert(card,'native clone card missing');card.apply(p);
 const clone=G.SelfClones.actors()[0];clone.x=clone.y=0;const cmob=A.liftSpawn(130,0);clone.target=cmob;A.castNative('naruto-temari',clone);A.waitLift(cmob);
 A.assert(T.liftForState(cmob).owner===clone,'clone control attributed to main player');G.SelfClones.clear();A.liftStep(.01,false);
 A.assert(!T.held(cmob)&&T.liftFor(cmob)===0,'clone expiry retained bump');out.cloneClean=true;
 return out;
}"""


def visual(page, label, report):
    # Async asset loading runs while the simulation clock remains paused.
    page.evaluate('G.Sprites.preload([19])')
    page.evaluate("""() => {const A=Acceptance,p=A.p();A.liftReset();window.VisualMob=A.liftSpawn(140,0);p.target=VisualMob;A.castNative('naruto-temari')}""")
    result = {}
    for phase, steps in [('before', 15), ('peak', 15), ('land', 35)]:
        state = page.evaluate("""([phase,n])=>{if(phase==='peak')for(let i=0;i<150&&!G.NarutoTemari.held(VisualMob);i++)Acceptance.liftStep(.01);
          for(let i=0;i<n;i++)Acceptance.liftStep(.01);const e=VisualMob;
          if(phase==='peak')for(let i=0;i<30&&e.flash>0&&G.NarutoTemari.held(e);i++)Acceptance.liftStep(.005);
          return {held:G.NarutoTemari.held(e),height:G.NarutoTemari.liftFor(e),jumpLift:e.jumpLift||0,png:Acceptance.liftPicture()}}""", [phase, steps])
        (OUT / f'{label}-wind-lift-{phase}.png').write_bytes(base64.b64decode(state.pop('png').split(',', 1)[1]))
        result[phase] = state
    assert not result['before']['held'] and result['peak']['height'] > 0 and result['land']['height'] == 0, result
    report['visuals'][label] = result


def coop(browser, report):
    pages, contexts = {}, []
    for uid in ['host', 'guest']:
        ctx = browser.new_context(viewport={'width': 1000, 'height': 800}, service_workers='block')
        ctx.add_init_script('window.requestAnimationFrame=()=>0')
        page = ctx.new_page()
        page.on('pageerror', lambda e: report['errors'].append(str(e)))
        boot(page)
        page.evaluate(ADAPTER, uid)
        page.evaluate(FIXTURE)
        page.evaluate("""() => {const p=Acceptance.p();p.moves=p.moves.filter(m=>m.id==='naruto-temari');Acceptance.mastery(0);
          CoopFixture.liftStep=n=>{for(let i=0;i<n;i++){Acceptance.liftStep(.005,false);Acceptance.resume();const moves=p.moves;p.moves=[];
            try{G.Combat.tick(.005,p,0);G.Coop.tick(.005)}finally{p.moves=moves;Acceptance.pause()}}}}""")
        pages[uid] = page
        contexts.append(ctx)
    host, guest = pages['host'], pages['guest']
    for uid in ['host', 'guest']:
        for page in pages.values():
            page.evaluate('G.EnemyMgr.clear();G.Combat.clearFields()')
        host.evaluate("""() => {window.CoopEnemy=Acceptance.spawn(140,0);window.CoopHits=Acceptance.watch(CoopEnemy);G.Coop.tick(.1)}""")
        pump(pages, report)
        guest.evaluate("window.CoopEnemy=G.EnemyMgr.all().find(e=>e.remote&&!e.dead);G.EnemyMgr.rebuildGrid()")
        for page in pages.values():
            page.evaluate("""() => {Acceptance.p().target=CoopEnemy;Acceptance.p().aim=0;
              CoopEnemy.jumpLift=9;window.LiftHistory=[];}""")
        print('coop cast', uid, flush=True)
        pages[uid].evaluate("Acceptance.castNative('naruto-temari')")
        pump(pages, report)
        for _ in range(200):
            for page in pages.values():
                page.evaluate("""() => {CoopFixture.liftStep(1);const T=G.NarutoTemari,e=CoopEnemy,s=T.liftForState(e);
                  LiftHistory.push({held:T.held(e),height:T.liftFor(e),remote:s?.remote,authoritative:s?.authoritative,jump:e.jumpLift,hp:e.hp});}""")
            pump(pages, report)
        histories = {key: page.evaluate('LiftHistory') for key, page in pages.items()}
        report['coop'][uid+'Debug'] = {key: page.evaluate("({casts:G.NarutoTemari.casts.map(b=>({ghost:b.ghost,kind:b.kind,age:b.age,emitted:b.emitted,targets:b.targets})),waves:G.NarutoTemari.waves.map(w=>({age:w.age,x:w.x,y:w.y,ghost:w.cast.ghost,aim:w.aim,reach:w.reach})),net:G.TemariCoop.inspect(),peak:Math.max(...LiftHistory.map(s=>s.height)),hp:CoopEnemy.hp})") for key,page in pages.items()}
        for key, history in histories.items():
            assert any(s['held'] and s['height'] > 0 for s in history), (uid, key, 'missing remote bump')
            assert not history[-1]['held'] and history[-1]['height'] == 0, (uid, key, 'release missing')
            assert all(s['jump'] == 9 for s in history), (uid, key, 'native jump overwritten')
        held_guest = [s for s in histories['guest'] if s['held']]
        assert all(not s.get('authoritative') for s in held_guest), 'guest received authoritative lease'
        assert host.evaluate('CoopEnemy.hp<CoopEnemy.maxHp'), 'host did not take actual wave contact damage'
        host_hits = host.evaluate('CoopHits.length')
        cast_hits = pages[uid].evaluate('G.NarutoTemari.stateFor(Acceptance.p()).latest.hits')
        assert host_hits == cast_hits and host_hits > 0, ('ghost duplicated or forwarding lost damage', uid, host_hits, cast_hits)
        report['coop'][uid] = {key: {'heldFrames': sum(s['held'] for s in h), 'peak': max(s['height'] for s in h)} for key, h in histories.items()}
        # Recover native private cooldown without permitting a second automatic cast.
        for page in pages.values():
            page.evaluate("""() => {const p=Acceptance.p(),moves=p.moves;p.moves=[];Acceptance.resume();try{G.Combat.tick(3,p,0)}finally{p.moves=moves;Acceptance.pause()}}""")
    assert report['eventKinds'].get('to', 0) >= 2 and report['eventKinds'].get('te', 0) >= 2, report['eventKinds']
    # A lift pauses an existing native typhoon orbit. Two real waves stretch
    # its wall-clock lifetime past the former 1.7s network claim timeout.
    for page in pages.values():
        page.evaluate('G.EnemyMgr.clear();G.Combat.clearFields()')
    host.evaluate("""() => {const A=Acceptance,p=A.p();p.quantityBonus=p.quantityPicks=0;p.cdMul=.1;A.rank('naruto-temari',5);
      p.addMove('naruto-temari-typhoon');window.CoopEnemy=A.spawn(140,0);p.target=CoopEnemy;
      window.OrbitLiftReleases=[];const old=G.NarutoTemari.onRelease;
      G.NarutoTemari.onRelease=(o,e,packet,b)=>{if(e===CoopEnemy)OrbitLiftReleases.push({...packet});old?.(o,e,packet,b)};
      CoopFixture.castPredictedBasic=()=>{const a=Math.atan2(CoopEnemy.y,CoopEnemy.x)-Math.PI/2;const lead=A.spawn(140*Math.cos(a),140*Math.sin(a),'boss');p.target=lead;G.EnemyMgr.rebuildGrid();A.castNative('naruto-temari');lead.dead=true};
      G.Coop.tick(.1);A.castNative('naruto-temari-typhoon')}""")
    pump(pages, report)
    guest.evaluate('window.CoopEnemy=G.EnemyMgr.all().find(e=>e.remote&&!e.boss&&!e.dead)')
    orbit_frames = []
    stage, was_held = 0, False
    for frame in range(650):
        for page in pages.values():
            page.evaluate('CoopFixture.liftStep(1)')
        pump(pages, report)
        state = host.evaluate("""() => {const T=G.NarutoTemari,o=T.orbitFor(CoopEnemy);
          return {held:T.held(CoopEnemy),orbit:o&&{age:o.age,angle:o.angle,start:o.startAngle},release:OrbitLiftReleases}}""")
        orbit_frames.append({'frame': frame, **state})
        if stage == 0 and state['orbit']:
            host.evaluate('CoopFixture.castPredictedBasic()')
            pump(pages, report)
            stage = 1
        elif stage == 1 and was_held and not state['held']:
            host.evaluate('CoopFixture.castPredictedBasic()')
            pump(pages, report)
            stage = 2
        was_held = state['held']
        if state['release']:
            break
    releases = host.evaluate('OrbitLiftReleases')
    transitions = sum(s['held'] and (i == 0 or not orbit_frames[i-1]['held']) for i, s in enumerate(orbit_frames))
    assert transitions == 2, ('native staggered basic waves did not make two holds', transitions, stage)
    assert releases and releases[-1]['reason'] == 'complete', ('orbit released early', releases)
    release = releases[-1]
    assert abs((release['startAngle']-release['angle'])-2*3.141592653589793) < 1e-6, release
    captured = next(s['frame'] for s in orbit_frames if s['orbit'])
    elapsed = (orbit_frames[-1]['frame']-captured)*.005
    assert elapsed > 1.7, ('test did not exercise extended network lifetime', elapsed)
    assert guest.evaluate('!G.NarutoTemari.orbitFor(CoopEnemy)&&!G.NarutoTemari.held(CoopEnemy)'), 'remote orbit/lift did not release'
    report['coop']['typhoonTwoBumps'] = {'holds': transitions, 'wallSecondsAfterCapture': elapsed, 'release': release}
    for mode in ['scene', 'disconnect']:
        for page in pages.values():
            page.evaluate('G.EnemyMgr.clear();G.Combat.clearFields()')
        host.evaluate("""() => {const A=Acceptance,p=A.p();window.CoopEnemy=A.spawn(140,0);p.target=CoopEnemy;G.Coop.tick(.1);A.castNative('naruto-temari')}""")
        pump(pages, report)
        guest.evaluate('window.CoopEnemy=G.EnemyMgr.all().find(e=>e.remote&&!e.dead)')
        for _ in range(150):
            for page in pages.values():
                page.evaluate('CoopFixture.liftStep(1)')
            pump(pages, report)
            if guest.evaluate('G.NarutoTemari.held(CoopEnemy)'):
                break
        assert guest.evaluate('G.NarutoTemari.held(CoopEnemy)'), mode+': active hold never synchronized'
        if mode == 'scene':
            host.evaluate('G.Combat.clearFields();Acceptance.resume();G.Coop.tick(.1);Acceptance.pause()')
            pump(pages, report)
        else:
            guest.evaluate("CoopFixture.disconnect('host')")
        assert guest.evaluate('!G.NarutoTemari.held(CoopEnemy)&&G.NarutoTemari.liftFor(CoopEnemy)===0&&G.TemariCoop.inspect().lifts===0'), mode+': stale remote hold'
        report['coop'][mode+'Clean'] = True
    for ctx in contexts:
        ctx.close()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'url': URL, 'ok': False, 'errors': [], 'local': {}, 'visuals': {}, 'coop': {}, 'packets': 0, 'eventKinds': {},
              'notCovered': ['Physical mobile hardware', 'Real WebRTC/signaling/internet/packet loss']}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROME, headless=True)
            for label, viewport in [('desktop', {'width': 1100, 'height': 800}), ('mobile', {'width': 390, 'height': 844})]:
                if os.environ.get('TEMARI_LIFT_LOCAL', '1') == '0':
                    continue
                print(label, flush=True)
                ctx = browser.new_context(viewport=viewport, is_mobile=label == 'mobile', has_touch=label == 'mobile', service_workers='block')
                ctx.add_init_script('window.requestAnimationFrame=()=>0')
                page = ctx.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                boot(page)
                page.evaluate(FIXTURE)
                report['local'][label] = page.evaluate(LOCAL)
                visual(page, label, report)
                ctx.close()
            if os.environ.get('TEMARI_LIFT_COOP', '1') != '0':
                print('coop', flush=True)
                coop(browser, report)
            browser.close()
        assert not report['errors'], report['errors']
        report['ok'] = True
    finally:
        path = OUT / 'report-wind-lift.json'
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(path, flush=True)


if __name__ == '__main__':
    main()
