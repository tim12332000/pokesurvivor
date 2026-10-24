"""Single-front Great Scythe acceptance through native combat and enemy update.

Terrain-only fixtures supply explicit collision boundaries. Damage, movement,
learning cards, clone attribution and Coop handlers are production code.
"""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_temari as native
import test_temari_coop as protocol

OUT = Path(__file__).resolve().parents[1] / '.omx/state/temari-great-scythe'
ID = 'naruto-temari-great-scythe'

SETUP = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari;A.heavy='naruto-temari-great-scythe';A.learn();
 const advance=A.advance;A.advance=(dt=.01)=>{A.resume();try{G.EnemyMgr.update(dt,[p])}finally{A.pause()}
   advance(dt);A.resume();try{G.FX.update(dt)}finally{A.pause()}};
 A.heavyCast=(Q=0,L=0,rank=1,special='boss')=>{A.reset();A.mastery(L);A.rank(A.heavy,rank);
   p.quantityBonus=p.quantityPicks=Q;const e=A.spawn(100,0,special),hits=A.watch(e);p.target=e;
   A.castNative(A.heavy);return {e,hits,f:T.stateFor(p).latest}};
}"""

GROWTH = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];
 for(let rank=1;rank<=5;rank++)for(const Q of [0,5,13,20])for(const L of [0,1,5]){
   const {e,hits,f}=A.heavyCast(Q,L,rank),power=[70,84,100.8,126,157.5][rank-1];
   A.assert(f.kind==='heavy'&&f.count===1&&f.W===1&&f.R===1&&f.potentialHits===1,'heavy regained repeated fronts/cuts');
   A.near(f.arc,Math.min(180,110+10*(rank-1)+2*Q)*Math.PI/180,'fan angle');
   A.near(f.range,[300,330,360,390,420][rank-1]+6*Q+(L?[40,70,110,160,220][L-1]:0),'range growth');
   A.near(f.pushDistance,[120,145,170,195,220][rank-1]+18*L+4*Q,'push growth');
   A.near(f.pushDuration,.35,'push duration');A.near(f.speed,720*(L?[1.15,1.25,1.4,1.6,1.85][L-1]:1),'speed');
   A.near(f.damage,power*p.atk,'full single hit power');A.near(T.stateFor(p).cooldowns[A.heavy],5,'cooldown');
   A.finish(2);A.assert(f.emitted===1&&f.cuts===1&&hits.length===1,'not exactly one physical front/contact '+JSON.stringify({rank,Q,L,emitted:f.emitted,cuts:f.cuts,hits:hits.length}));
   const expected=power*p.atk*G.Types.mult('flying',e.types)*G.Weather.mult('flying');
   A.near(hits[0].raw,expected,'native full damage');A.near(e.maxHp-e.hp,Math.round(expected),'actual HP');
   out.push({rank,Q,L,arc:f.arc,range:f.range,pushDistance:f.pushDistance,damage:e.maxHp-e.hp,hits:hits.length});
 }return out;
}"""

GEOMETRY = r"""() => {
 const A=Acceptance,p=A.p(),out={};A.reset();A.mastery(0);A.rank(A.heavy,1);
 const es=[[120,0],[125,65],[125,-65],[-120,0]].map(([x,y])=>A.spawn(x,y,'boss')),hits=es.map(A.watch);
 p.target=es[0];A.castNative(A.heavy);A.finish(2);A.assert(hits.map(h=>h.length).join(',')==='1,1,1,0','spread AOE/outside '+hits.map(h=>h.length));out.spread=hits.map(h=>h.length);
 for(const wallKind of ['solid','object']){A.reset();A.mastery(0);const e=A.spawn(180,0,'boss'),h=A.watch(e);p.target=e;A.castNative(A.heavy);
   const W=G.World,block=W.projectileBlock;W.projectileBlock=(x,y)=>x>65&&x<90?{destructible:wallKind==='object',hp:99}:false;
   try{A.finish(2);A.assert(!h.length,'front penetrated '+wallKind)}finally{W.projectileBlock=block}out[wallKind]=h.length;
 }return out;
}"""

MOVEMENT = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out=[];
 for(const Q of [0,20])for(const L of [0,5]){
   const {e,hits,f}=A.heavyCast(Q,L,5,null),x=e.x,y=e.y;let lease=false,maxStep=0;
   for(let i=0;i<250;i++){const before=e.x;A.advance(.005);lease ||= !!T.pushFor(e);maxStep=Math.max(maxStep,Math.abs(e.x-before));}
   A.assert(lease&&hits.length===1&&!T.pushFor(e),'missing/nonexpiring movement lease');
   A.near(e.x-x,f.pushDistance,'actual displacement');A.near(e.y,y,'radial push drift');
   A.assert(maxStep<=f.pushDistance*.05,'displacement teleported');
   e.spd=55;p.x=e.x-80;const stop=e.x;A.finish(.3);A.assert(e.x<stop-1,'enemy never resumed approach '+JSON.stringify({stop,x:e.x,spd:e.spd}));
   out.push({Q,L,distance:f.pushDistance,maxStep,resumed:stop-e.x});
 }
 for(const special of ['boss','elite','legend','judge']){const {e,hits}=A.heavyCast(20,5,5,special);A.finish(2);
   A.assert(hits.length===1&&e.x===100&&e.y===0&&!T.pushFor(e),'special immunity omitted damage/displaced '+special);out.push({special,hits:hits.length});}
 const {e,f}=A.heavyCast(20,5,5,null),W=G.World,free=W.isFree,wall=W.isWall;
 W.isFree=(x,y,r=0)=>x+r<175;W.isWall=x=>x>=175;
 try{A.finish(2);A.assert(e.x<=175-(e.r||8)&&e.x>100&&!T.pushFor(e),'swept push crossed wall or never moved');out.push({wallStop:e.x})}
 finally{W.isFree=free;W.isWall=wall}return out;
}"""

LIFECYCLE = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,out={};
 for(const reason of ['pause','clear','death','world']){
   const {e,hits}=A.heavyCast(5,1,1,null);for(let i=0;i<200&&!T.pushFor(e);i++)A.advance(.005);
   A.assert(T.pushFor(e),'lifecycle fixture lacks push');const x=e.x,world=G.World;
   try{if(reason==='pause'){G.Combat.updateFields(.2);A.assert(e.x===x&&T.pushFor(e),'paused push moved');}
     if(reason==='clear')G.Combat.clearFields(p);if(reason==='death')p.dead=true;if(reason==='world')G.World={...world};
     if(reason!=='pause'){A.advance(.01);A.assert(!T.pushFor(e)&&e.x===x,'invalid push moved or survived '+reason)}out[reason]=true;
   }finally{p.dead=false;G.World=world;G.Combat.clearFields()}
 }
 const base=A.heavyCast(5,5,5);A.finish(2);const full=base.hits[0].raw;G.Combat.clearFields();
 const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');A.assert(card,'clone card missing');card.apply(p);
 const clone=G.SelfClones.actors()[0];clone.x=clone.y=0;clone.target=base.e;base.hits.length=0;A.castNative(A.heavy,clone);const ownMoves=p.moves;
 p.moves=p.moves.filter(m=>m.digiMode==='temari-mastery');try{A.finish(2)}finally{p.moves=ownMoves}
 A.assert(base.hits.length===1&&base.hits[0].clone,'clone missing or duplicate damage '+JSON.stringify(base.hits));A.near(base.hits[0].raw*3,full,'clone one-third');
 G.SelfClones.clear();A.advance();A.assert(!T.stateFor(clone),'clone retained state');out.cloneThird=true;
 // A heavy escape supersedes our short lift and circular carry without later snapping back.
 for(const kind of ['lift','orbit']){A.reset();A.mastery(0);A.rank(A.heavy,1);const e=A.spawn(100,0);p.target=e;
   A.castNative(A.heavy);A.finish(.49);
   const packet={castId:9000,x:0,y:0,radius:100,startAngle:0,age:0,duration:1.2};
   A.assert(kind==='lift'?T.applyNetworkLift(p,e,{castId:9000,age:0}):T.applyNetworkOrbit(p,e,packet),'control fixture failed '+kind);
   for(let i=0;i<200&&!T.pushFor(e);i++)A.advance(.005);
   A.assert(T.pushFor(e)&&!T.held(e)&&!T.orbitFor(e),'heavy failed to replace '+kind);A.finish(2);
   A.assert(e.x>180&&!T.orbitFor(e)&&!T.held(e),'old controller snapped enemy back '+kind);out[kind+'Superseded']=true;
 }return out;
}"""

def visuals(page, label):
    page.evaluate("G.Settings.set('dmgNumbers',true)")
    page.wait_for_function('G.TemariArt?.ready', polling=20)
    page.evaluate('''()=>{const A=Acceptance,p=A.p();p.moves=p.moves.filter(m=>m.digiMode!=='temari-blade-dance');
      A.heavyCast(5,1,3,null);A.spawn(100,48);A.spawn(100,-48);A.spawn(-100,50);
      G.Hazards.clear();G.FX.clear();G.Projectiles.clear();
      for(const e of G.EnemyMgr.all()){e.shotCd=e.skillCd=e.touchCd=999;if(e.ai)e.ai.cd=999;}
      A.assert(!G.NarutoTemari.summons.length,'isolated heavy visual contains passive pets');}''')
    samples = []
    age = 0
    for name, target in [('windup', .2), ('contact', .53), ('push', .62), ('clear', 1.7)]:
        state = page.evaluate('''dt=>{const A=Acceptance;A.finish(dt);const T=G.NarutoTemari,c=document.createElement('canvas'),ctx=c.getContext('2d');
          const snap=()=>JSON.stringify({enemies:G.EnemyMgr.all().map(e=>[e.x,e.y,e.hp]),pushes:G.EnemyMgr.all().map(e=>T.pushFor(e)).filter(Boolean).map(p=>[p.age,p.travelled,p.enemy.x,p.enemy.y]),
            waves:T.waves.map(w=>[w.reach,w.age,w.cast.cuts,w.cast.hits])});
          const before=snap();for(let i=0;i<5;i++){G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx)}
          A.assert(before===snap(),'render mutated active combat/push state');return {renderPure:true,waves:G.NarutoTemari.waves.length,
          enemies:G.EnemyMgr.all().map(e=>({x:e.x,y:e.y,hp:e.hp,pushed:!!G.NarutoTemari.pushFor(e)})),
          sources:A.pose().sources,damageNumbers:G.Settings.get('dmgNumbers')}}''', target-age)
        page.wait_for_timeout(80)
        page.screenshot(path=str(OUT / f'{label}-{name}.png'))
        samples.append({'phase': name, 'age': target, **state})
        age = target
    return samples


def solo():
    report = {'ok': False, 'checks': {}, 'errors': [], 'failures': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=native.CHROME, headless=True)
        for label, viewport, mobile in [('desktop', {'width': 1100, 'height': 800}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
            context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            try:
                native.boot(page)
                page.evaluate(SETUP)
                for name, check in [('growth', GROWTH), ('geometry', GEOMETRY), ('movement', MOVEMENT), ('lifecycle', LIFECYCLE)]:
                    if os.environ.get('TEMARI_HEAVY_CHECKS') and name not in os.environ['TEMARI_HEAVY_CHECKS'].split(','):
                        continue
                    try:
                        report['checks'][label+'-'+name] = page.evaluate(check)
                        print(label, name, 'PASS', flush=True)
                    except Exception as error:
                        report['failures'].append(label+'-'+name+': '+str(error))
                        print(label, name, 'FAIL', str(error), flush=True)
                try:
                    report['checks'][label+'-visual'] = visuals(page, label)
                except Exception as error:
                    report['failures'].append(label+'-visual: '+str(error))
            except Exception as error:
                report['failures'].append(label+'-boot: '+str(error))
            context.close()
        browser.close()
    report['ok'] = not report['errors'] and not report['failures']
    return report


def coop():
    report = {'ok': False, 'packets': 0, 'eventKinds': {}, 'errors': [], 'scenarios': {},
              'notCovered': ['real WebRTC transport', 'internet signaling', 'packet loss']}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=native.CHROME, headless=True)
            pages, contexts = {}, []
            for uid in ['host', 'guest']:
                ctx = browser.new_context(viewport={'width': 1100, 'height': 800}, service_workers='block')
                ctx.add_init_script('window.requestAnimationFrame=()=>0')
                page = ctx.new_page()
                page.on('pageerror', lambda e: report['errors'].append(str(e)))
                native.boot(page)
                page.evaluate(protocol.ADAPTER, uid)
                page.evaluate('Acceptance.reset();Acceptance.mastery(0);Acceptance.rank("naruto-temari-great-scythe",1)')
                pages[uid] = page
                contexts.append(ctx)
            host, guest = pages['host'], pages['guest']
            host.evaluate('window.HeavyEnemy=Acceptance.spawn(120,0);window.HeavyHits=Acceptance.watch(HeavyEnemy);G.Coop.tick(.1)')
            protocol.pump(pages, report)
            guest.evaluate('()=>{window.HeavyEnemy=G.EnemyMgr.all().find(e=>e.remote);window.HeavyGhostHits=0;const hurt=HeavyEnemy.hurt;HeavyEnemy.hurt=function(...args){HeavyGhostHits++;return hurt.apply(this,args)}}')
            for caster in ['host', 'guest']:
                for page in pages.values():
                    page.evaluate('''() => {G.Combat.clearFields();const p=G.Game.player;p.x=p.y=0;p.target=HeavyEnemy;p.quantityBonus=p.quantityPicks=0;
                      HeavyEnemy.x=120;HeavyEnemy.y=0;if(HeavyEnemy.net){HeavyEnemy.net.x=120;HeavyEnemy.net.y=0;HeavyEnemy.net.vx=HeavyEnemy.net.vy=0}G.EnemyMgr.rebuildGrid()}''')
                before = host.evaluate('({hp:HeavyEnemy.hp,hits:HeavyHits.length})')
                forwarded_before = guest.evaluate('HeavyGhostHits')
                pages[caster].evaluate('Acceptance.castNative("naruto-temari-great-scythe")')
                protocol.pump(pages, report)
                samples = []
                for frame in range(40):
                    for page in pages.values():
                        page.evaluate('''() => {Acceptance.resume();try{G.EnemyMgr.update(.05,[G.Game.player])}finally{Acceptance.pause()}CoopFixture.step(5)}''')
                    protocol.pump(pages, report)
                    if frame % 3 == 0:
                        samples.append(host.evaluate('({x:HeavyEnemy.x,y:HeavyEnemy.y,hits:HeavyHits.length,push:!!G.NarutoTemari.pushFor(HeavyEnemy)})'))
                after = host.evaluate('({hp:HeavyEnemy.hp,hits:HeavyHits.length,x:HeavyEnemy.x,y:HeavyEnemy.y})')
                assert after['hits']-before['hits'] == 1, f'{caster}: damage duplicated or lost: {before} {after}'
                assert abs(after['x']-240) < .1 and abs(after['y']) < .1, f'{caster}: authoritative push wrong {after}'
                assert after['hp'] < before['hp'], f'{caster}: HP unchanged'
                forwarded = guest.evaluate('HeavyGhostHits')-forwarded_before
                assert forwarded == (1 if caster == 'guest' else 0), f'{caster}: ghost hurt duplicate {forwarded}'
                assert any(x['push'] for x in samples), f'{caster}: no active host push'
                assert all(page.evaluate('!G.NarutoTemari.pushFor(HeavyEnemy)') for page in pages.values()), 'expired push retained'
                report['scenarios'][caster] = {'samples': samples, 'damage': before['hp']-after['hp'], 'guestForwardedHits': forwarded}
            assert not report['errors'], report['errors']
            for ctx in contexts:
                ctx.close()
            browser.close()
        report['ok'] = True
    except Exception as error:
        report['failure'] = str(error)
    return report


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    is_coop = bool(os.environ.get('TEMARI_HEAVY_COOP'))
    result = coop() if is_coop else solo()
    destination = OUT / ('coop-report.json' if is_coop else ('report-focused.json' if os.environ.get('TEMARI_HEAVY_CHECKS') else 'report.json'))
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'ok': result['ok'], 'report': str(destination), 'failures': result.get('failures'), 'failure': result.get('failure')}))
    raise SystemExit(0 if result['ok'] else 1)
