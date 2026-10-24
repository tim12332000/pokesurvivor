"""Native Temari procedural VFX evidence; keep particles and damage numbers live.

Run the repository server on port 8004, then python tools/test_temari_procedural_vfx.py.
Screenshots are review evidence, not an automated claim of artistic quality.
"""
import base64
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_temari as native
import test_temari_reflect as reflect
import test_temari_typhoon as typhoon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/temari-procedural-vfx'
GROUPS = {
    'basic': 'naruto-temari',
    'third-star': 'naruto-temari',
    'heavy': 'naruto-temari-great-scythe',
    'kamatari': 'naruto-temari-blade-dance',
    'cyclone': 'naruto-temari-typhoon',
    'reflect': 'naruto-temari-reflect',
}

SETUP = r"""() => {
 const A=Acceptance,p=A.p();A.learn();A.tyLearn();A.rfLearn();
 // Match the production combat -> field -> particle update sequence. Never hide
 // FX or replace hurt(): floating numbers must decay at the real game rate.
 A.vfxStep=(dt=.005)=>{A.advance(dt);A.resume();try{G.Hazards.update(dt);G.FX.update(dt)}finally{A.pause()}};
 A.vfxFinish=s=>{let left=s;while(left>1e-8){const dt=Math.min(.005,left);A.vfxStep(dt);left-=dt}};
 A.scalar=o=>Object.fromEntries(Object.entries(o||{}).filter(([k,v])=>v===null||['number','string','boolean'].includes(typeof v)));
 A.vfxSnapshot=()=>{
  const T=G.NarutoTemari,R=G.NarutoTemariReflect;
  return JSON.stringify({p:A.scalar(p),state:A.scalar(T.stateFor(p)),cooldowns:T.stateFor(p)?.cooldowns,
   reflection:A.scalar(R.stateFor(p)),wall:A.scalar(R.activeFor(p)),
   latest:A.scalar(T.stateFor(p)?.latest),enemies:G.EnemyMgr.all().map(A.scalar),
   actors:['blades','waves','summons','storms','casts','orbits'].map(k=>[k,(T[k]||[]).map(a=>({
    ...A.scalar(a),cast:A.scalar(a.cast),fronts:a.fronts?.map(A.scalar),
    contacts:a.contacts instanceof Map?[...a.contacts.values()].map(A.scalar):null}))]),
   projectiles:G.Projectiles.all().map(A.scalar),fx:G.FX.count});
 };
 A.vfxStart=({group,Q})=>{
  A.reset();A.mastery(group==='basic'?0:1);p.quantityBonus=p.quantityPicks=Q;
  A.petEnabled=group==='kamatari';
  const id={basic:'naruto-temari','third-star':'naruto-temari',heavy:'naruto-temari-great-scythe',
   kamatari:'naruto-temari-blade-dance',cyclone:A.ty,reflect:A.rf}[group];
  // Isolate each skill's presentation using a genuine learned loadout. The
  // permanent pet is covered separately rather than contaminating other hits.
  if(group!=='kamatari')p.moves=p.moves.filter(m=>m.id!=='naruto-temari-blade-dance');
  if(group!=='reflect')p.moves=p.moves.filter(m=>m.id!==A.rf);
  A.rank(id,1);const e=A.spawn(group==='reflect'?210:group==='basic'||group==='third-star'?85:115,0,'boss');
  if(group!=='basic'&&group!=='third-star'){A.spawn(-100,75);A.spawn(20,-110)}
  p.target=e;A.vfxTarget=e;A.vfxHits=A.watch(e);A.vfxGroup=group;A.vfxAge=0;
  if(group==='third-star')for(let i=0;i<2;i++){
   A.castNative(id);A.vfxFinish(1.7);
   // Private cast cooldown advances in Combat.tick, independently of fields.
   const moves=p.moves;p.moves=moves.filter(m=>m.digiMode==='temari-mastery');
   A.resume();try{G.Combat.tick(1.7,p,0)}finally{p.moves=moves;A.pause()}
  }
  if(group==='kamatari'){
   // Learning a passive enters the production tick before fields advance.
   const moves=p.moves;p.moves=moves.filter(m=>m.id===id||m.digiMode==='temari-mastery');
   A.resume();try{G.Combat.tick(.001,p,0)}finally{p.moves=moves;A.pause()}
   A.vfxStep();
  }else if(group==='reflect'){
   const pose=G.NarutoTemari.activeFor(p),animation=JSON.stringify(A.scalar(p.anim));
   G.NarutoTemariReflect.sync(p);
   A.assert(G.NarutoTemari.activeFor(p)===pose&&JSON.stringify(A.scalar(p.anim))===animation,
    'passive reflection changed owner pose or animation');
  }else A.castNative(id);
  A.vfxLatest=G.NarutoTemari.stateFor(p)?.latest;
  if(group==='reflect')A.rfShot();
 };
 A.vfxSeekCut=()=>{
  let n=0;while(!G.NarutoTemari.summons.some(a=>a.cuts>0)&&n++<400){A.vfxStep();A.vfxAge+=.005}
  A.assert(n<400,'native Kamatari never reached first cut '+JSON.stringify({
   moves:p.moves.map(m=>({id:m.id,passive:m.passive,mode:m.digiMode})),
   pets:G.NarutoTemari.summons.map(a=>({phase:a.phase,cuts:a.cuts,x:a.x,y:a.y,tx:a.tx,ty:a.ty}))}));return A.vfxAge;
 };
 A.vfxCapture=()=>{
  const c=document.createElement('canvas');c.width=900;c.height=700;
  const ctx=c.getContext('2d',{willReadFrequently:true});ctx.translate(400,370);
  const images=[],draw=ctx.drawImage.bind(ctx);ctx.drawImage=(im,...args)=>{images.push(im.src||'canvas');return draw(im,...args)};
  const before=A.vfxSnapshot(),cost=[];
  for(let i=0;i<25;i++){ctx.clearRect(-400,-370,900,700);const t=performance.now();
   G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);cost.push(performance.now()-t)}
  A.assert(before===A.vfxSnapshot(),'render changed HP, projectile, cut, cast, cooldown, FX or control state');
  A.assert(!images.some(s=>/temari[^/]*(?:wind|cyclone)|(?:wind|cyclone)[^/]*\.png/i.test(s)),'wind bitmap drawn '+JSON.stringify(images));
  const data=ctx.getImageData(0,0,c.width,c.height).data;
  let visible=0,opaque=0,centerOpaque=0,x0=900,y0=700,x1=-1,y1=-1;
  for(let y=0;y<700;y++)for(let x=0;x<900;x++){
   const a=data[(y*900+x)*4+3];if(a>10){visible++;x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}
   if(a>220){opaque++;if((x-400)**2+(y-370)**2<45**2)centerOpaque++}
  }
  A.assert(visible>10,'empty active VFX capture');
  if(['cyclone','reflect'].includes(A.vfxGroup))A.assert(centerOpaque<45**2*Math.PI*.65,'wind hides actor behind opaque disk');
  cost.sort((a,b)=>a-b);
  const T=G.NarutoTemari,R=G.NarutoTemariReflect,latest=T.stateFor(p)?.latest;
  return {png:c.toDataURL(),visible,opaque,centerOpaque,bounds:[x0,y0,x1,y1],images:[...new Set(images)],
   costMs:{median:cost[12],p95:cost[23],max:cost[24]},hits:A.vfxHits.length,targetHp:A.vfxTarget.hp,
   emitted:latest?.emitted,cuts:latest?.cuts,potential:latest?.potentialHits,empowered:latest?.empowered,
   phase:T.summons.map(a=>({phase:a.phase,cuts:a.cuts,age:a.age,lastCut:a.lastCut,moving:a.moving,
    x:a.x,y:a.y,ownerDistance:Math.hypot(a.x-p.x,a.y-p.y),restUntil:a.restUntil})),
   reflection:A.scalar(R.stateFor(p)),wall:A.scalar(R.activeFor(p)),
   waves:T.waves.map(a=>({kind:a.cast.kind,arc:a.cast.arc,fronts:a.fronts.length})),blades:T.blades.length,
   fx:G.FX.count,damageNumbers:G.Settings.get('dmgNumbers'),renderPure:true};
 };
 G.Settings.set('dmgNumbers',true);
}"""


def save_image(path, data):
    path.write_bytes(base64.b64decode(data.split(',', 1)[1]))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'ok': False, 'failures': [], 'errors': [], 'viewports': {}}
    quantities = [int(q) for q in os.environ.get('TEMARI_VFX_QUANTITIES', '0,5,20').split(',')]
    groups = os.environ.get('TEMARI_VFX_GROUPS', ','.join(GROUPS)).split(',')
    assert all(group in GROUPS for group in groups), groups
    report['groups'] = groups
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=native.CHROME, headless=True)
        for label, viewport, mobile in [('desktop', {'width': 1280, 'height': 800}, False),
                                        ('mobile', {'width': 390, 'height': 844}, True)]:
            context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            try:
                native.boot(page)
                page.evaluate(typhoon.SETUP)
                # Restore the base advance after importing tyLearn; that suite
                # wraps FX.update itself, whereas this fixture owns that step.
                page.evaluate(native.SETUP)
                page.evaluate(reflect.SETUP)
                page.evaluate(SETUP)
                art = page.evaluate('''() => ({sheets:Object.keys(G.TemariArt.metadata.sheets),
                  frames:Object.values(G.TemariArt.metadata.sheets).reduce((n,s)=>n+s.frames.length,0),
                  bitmapWindAPI:typeof G.TemariArt.drawWind,procedural:typeof G.TemariCycloneVFX.drawReflection})''')
                assert art['frames'] == 56 and art['bitmapWindAPI'] == 'undefined', art
                assert art['procedural'] == 'function', art
                results = report['viewports'][label] = {'art': art, 'cases': {}}
                for group in groups:
                    for quantity in quantities:
                        key = f'{group}-q{quantity}'
                        try:
                            page.evaluate('Acceptance.vfxStart', {'group': group, 'Q': quantity})
                            cut_age = page.evaluate('Acceptance.vfxSeekCut()') if group == 'kamatari' else 0
                            # Each point is a real forward step in the event sequence.
                            phases = [.02, .06, .12] if group == 'kamatari' else {
                                'basic': [.23, .33, .45], 'third-star': [.23, .33, .45],
                                'heavy': [.45, .65, .85], 'cyclone': [.45, .8, 1.2],
                                'reflect': [.06, .12, .2],
                            }[group]
                            sequence = []
                            previous = 0
                            for phase in phases:
                                page.evaluate('Acceptance.vfxFinish', phase-previous)
                                evidence = page.evaluate('Acceptance.vfxCapture()')
                                name = f'{label}-{key}-{phase:.2f}'
                                save_image(OUT / f'{name}-effect.png', evidence.pop('png'))
                                page.screenshot(path=str(OUT / f'{name}-game.png'))
                                sequence.append({'time': cut_age+phase, **evidence})
                                previous = phase
                            assert all(s['damageNumbers'] and s['renderPure'] for s in sequence)
                            if group == 'third-star':
                                assert all(s['empowered'] for s in sequence), 'third cast lost empowerment'
                            if group in ('basic', 'third-star'):
                                assert all(s['blades'] == 0 for s in sequence), 'basic still creates knife actors'
                                assert any(any(w['kind'] == 'basic' and abs(w['arc']-0.7853981633974483) < .00001
                                               for w in s['waves']) for s in sequence), '45 degree wind wave missing'
                            persistent = []
                            if group == 'reflect':
                                # A learned passive remains visible beyond its
                                # former lifetime, with no recast or new pose.
                                page.evaluate('Acceptance.vfxFinish', 10-previous)
                                evidence = page.evaluate('Acceptance.vfxCapture()')
                                assert evidence['wall']['permanent'] and evidence['wall']['age'] >= 9.99, evidence
                                save_image(OUT / f'{label}-{key}-10.00-effect.png', evidence.pop('png'))
                                page.screenshot(path=str(OUT / f'{label}-{key}-10.00-game.png'))
                                persistent.append({'time': 10, **evidence})
                                page.evaluate('Acceptance.rfShot();Acceptance.vfxFinish(.2)')
                                assert page.evaluate('G.NarutoTemariReflect.stateFor(Acceptance.p()).intercepted') == 2
                            page.evaluate('Acceptance.vfxFinish(3)')
                            end = page.evaluate('''() => ({hits:Acceptance.vfxHits.length,
                              returned:G.NarutoTemariReflect.stateFor(Acceptance.p())?.returned,
                              emitted:Acceptance.vfxLatest?.emitted,potential:Acceptance.vfxLatest?.potentialHits,
                              count:Acceptance.vfxLatest?.count,cuts:Acceptance.vfxLatest?.cuts})''')
                            assert end['hits'] > 0, 'native enemy never took damage'
                            if group == 'reflect':
                                assert end['returned'] == 2*int(1.25**quantity), end
                                # Quantity returns fan out; a small target need
                                # not intersect every independent return ray.
                            elif group != 'kamatari':
                                assert end['emitted'] == end['count'], end
                            if group == 'kamatari':
                                # With no targets, pets keep roaming and resting
                                # nearby. Sample the native motion at 50 ms.
                                page.evaluate('G.EnemyMgr.clear();G.EnemyMgr.rebuildGrid();Acceptance.p().target=null')
                                motion = page.evaluate('''() => {const A=Acceptance,trace=[];
                                  for(let i=0;i<240;i++){A.vfxStep(.05);trace.push(G.NarutoTemari.summons.map(a=>({
                                    x:a.x,y:a.y,phase:a.phase,moving:!!a.moving,distance:Math.hypot(a.x-A.p().x,a.y-A.p().y),
                                    destinationDistance:a.roamTarget?Math.hypot(a.roamTarget.x-A.p().x,a.roamTarget.y-A.p().y):null})))}
                                  A.assert(trace.every(frame=>frame.length===Math.floor(1.25**A.p().quantityPicks)),'permanent roaming pet disappeared');
                                  A.assert(trace.some(frame=>frame.some(a=>a.moving))&&trace.some(frame=>frame.some(a=>!a.moving)),
                                    'pet never alternated roaming and rest');
                                  A.assert(trace.slice(80).every(frame=>frame.every(a=>a.distance<=180&&
                                    a.destinationDistance>=74.9&&a.destinationDistance<=145.1)),
                                    'idle pet chose destination outside nearby roaming area');
                                  A.assert(trace[0].every((_,index)=>trace.some(frame=>frame[index].distance>=74)),
                                    'idle pet stayed collapsed into owner');
                                  return trace}''')
                                evidence = page.evaluate('Acceptance.vfxCapture()')
                                save_image(OUT / f'{label}-{key}-wander-effect.png', evidence.pop('png'))
                                page.screenshot(path=str(OUT / f'{label}-{key}-wander-game.png'))
                                persistent.append({'phase': 'wander', 'trace': motion, **evidence})
                                for moving in (True, False):
                                    page.evaluate('''moving => {const A=Acceptance;let i=0;
                                      while(!G.NarutoTemari.summons.some(a=>!!a.moving===moving)&&i++<120)A.vfxStep(.05);
                                      A.assert(i<120,'roaming pet never reached requested motion state')}''', moving)
                                    pose = 'moving' if moving else 'rest'
                                    evidence = page.evaluate('Acceptance.vfxCapture()')
                                    save_image(OUT / f'{label}-{key}-wander-{pose}-effect.png', evidence.pop('png'))
                                    page.screenshot(path=str(OUT / f'{label}-{key}-wander-{pose}-game.png'))
                                    persistent.append({'phase': f'wander-{pose}', **evidence})
                            results['cases'][key] = {'sequence': sequence, 'persistent': persistent, 'end': end}
                            print(f'{label} {key}: hits={end["hits"]}', flush=True)
                        except Exception as error:
                            report['failures'].append(f'{label}/{key}: {error}')
                            print(f'FAIL {label} {key}: {error}', flush=True)
            except Exception as error:
                report['failures'].append(f'{label}/boot: {error}')
            finally:
                context.close()
        browser.close()
    report['ok'] = not report['failures'] and not report['errors']
    (OUT / os.environ.get('TEMARI_VFX_REPORT', 'report.json')).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'ok': report['ok'], 'failures': report['failures'], 'errors': report['errors']}, ensure_ascii=False))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
