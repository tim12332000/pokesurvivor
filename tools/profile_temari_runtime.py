"""Native Temari sustained-load probe; instrumentation never changes outcomes."""
import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
import test_temari as native

ROOT = Path(__file__).resolve().parents[1]
PROBE = r"""({full,mobs,clones,seconds,instrument,quantity,mastery,speed,nativeWorld}) => {
 const A=Acceptance,p=A.p(),T=G.NarutoTemari,dt=speed/60;
 if(nativeWorld)G.World.reset(4242);
 A.reset();if(nativeWorld)Object.assign(G.World,window.__temariProfileWorld);
 window.__temariProfileSeed(0x74656d61);
 const worldProbe=nativeWorld?{seed:4242,biome:G.World.biomeName(),propsWithin600:G.World.propsInCircle(0,0,600).length}:null;
 p.level=50;p.hp=p.maxHp=1e12;p.atkMul=1;p.quantityBonus=p.quantityPicks=quantity;
 p.moves=[];p.slots=[];p.active=0;
 const ids=full?['naruto-temari','naruto-temari-three-stars','naruto-temari-great-scythe','naruto-temari-blade-dance','naruto-temari-typhoon','naruto-temari-reflect']:['naruto-temari','naruto-temari-three-stars'];
 for(const id of ids)p.addMove(id);
 for(const id of ids)A.rank(id,5);
 A.mastery(mastery);
 const targets=[];let hits=0,damage=0;
 for(let i=0;i<mobs+1;i++) {const theta=i*2.3999632297,r=i?70+i%9*19:100;
  const e=A.spawn(Math.cos(theta)*r,Math.sin(theta)*r,i?null:'boss');e.hp=e.maxHp=1e14;
  const original=e.hurt;e.hurt=function(...args){const before=this.hp,result=original.apply(this,args);hits++;damage+=before-this.hp;return result};targets.push(e);}
 p.target=targets[0];p.aim=0;
 const cloneCard=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');
 for(let i=0;i<clones;i++)cloneCard.apply(p);
 const actors=[p,...G.SelfClones.actors()];
 for(const actor of actors){actor.x=actor.y=0;actor.target=targets[0];actor.aim=0;for(const m of actor.moves)m.t=0;
  if(full){const n=actor.slots.findIndex(g=>g.some(m=>m.id==='naruto-temari-typhoon'));actor.setActive(n);}}
 const totals={},timed={},restores=[];
 const wrap=(obj,key,label)=>{const original=obj?.[key];if(!instrument||typeof original!=='function')return;
  obj[key]=function(...args){totals[label]=(totals[label]||0)+1;const start=performance.now();try{return original.apply(this,args)}finally{timed[label]=(timed[label]||0)+performance.now()-start}};restores.push(()=>obj[key]=original)};
 wrap(G.EnemyMgr,'queryCircle','queryCircle');wrap(G.World,'projectileBlock','projectileBlock');wrap(G.World,'propsInCircle','propsInCircle');
 wrap(T,'petSnapshots','petSnapshots');wrap(T,'onPets','onPets');
 const samples=[],slices=[],objects=[],heap=[];let markHits=0;
 const counts=()=>({casts:T.casts.length,waves:T.waves.length,pets:T.summons.length,storms:T.storms.length,projectiles:G.Projectiles.all().length});
 const summarize=a=>{const s=[...a].sort((a,b)=>a-b);return {sum:a.reduce((s,x)=>s+x,0),p50:s[Math.floor(s.length*.5)]||0,p95:s[Math.floor(s.length*.95)]||0,max:s.at(-1)||0}};
 A.resume();try{for(let frame=0;frame<seconds*60;frame++){
  const start=performance.now();
  // updateFields already runs native SelfClones.update, including clone AI/tick.
  // Tick only the player here to avoid artificially doubling clone attacks.
  p.target=targets[0];G.Combat.tick(dt,p,frame*dt);p.anim?.update(dt);
  G.Projectiles.update(dt,p,G.EnemyMgr.all());G.Combat.resolve(dt,p,frame*dt);G.Combat.updateFields(dt);G.FX.update(dt);
  samples.push(performance.now()-start);
  if(frame%6===5){slices.push({sim:(frame+1)*dt,calls:{...totals},cost:{...timed},hits:hits-markHits});markHits=hits;for(const k of Object.keys(totals))totals[k]=0;for(const k of Object.keys(timed))timed[k]=0;}
  if(frame%60===59){objects.push({sim:(frame+1)*dt,...counts()});heap.push(performance.memory?.usedJSHeapSize||null);}
 }}finally{A.pause();for(const restore of restores)restore()}
 const snapshotStart=performance.now();let snapshotPets=0;
 for(let i=0;i<100;i++)for(const actor of actors)snapshotPets+=T.petSnapshots(actor).length;
 const snapshotProbe={iterations:100,actors:actors.length,pets:snapshotPets,ms:performance.now()-snapshotStart};
 return {full,mobs,clones,seconds,instrument,quantity,mastery,speed,nativeWorld,worldProbe,actors:actors.length,timing:summarize(samples),hits,damage,slices,objects,heap,final:counts(),snapshotProbe,angle:T.stateFor(p)?.latest?.arc};
}"""

SEED = """() => {
 window.__temariProfileSeed=seed=>{let value=seed>>>0;Math.random=()=>{
  value=(Math.imul(value,1664525)+1013904223)>>>0;return value/4294967296;
 }};window.__temariProfileSeed(0x74656d61);
}"""

CAPTURE_WORLD = """window.__temariProfileWorld ||= Object.fromEntries(
 ['isWall','projectileBlock','isFree','propsInCircle','collide','isLiquid']
 .map(key=>[key,G.World[key]]));"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default=native.URL)
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('--out', default='.omx/state/temari/runtime-profile.json')
    parser.add_argument('--cases', default='basic0,full30,full60,full60clones')
    parser.add_argument('--plain', action='store_true', help='Disable per-call probes for native frame timings.')
    parser.add_argument('--quantity', type=int, default=13)
    parser.add_argument('--mastery', type=int, choices=range(6), default=5)
    parser.add_argument('--clone-count', type=int, help='Override the legacy per-case clone count.')
    parser.add_argument('--speed', type=float, default=1)
    parser.add_argument('--native-world', action='store_true', help='Restore actual terrain and prop methods after arena reset.')
    parser.add_argument('--before', action='store_true', help='Serve saved runtime/VFX baselines from .omx/state/temari-performance.')
    args = parser.parse_args()
    if args.seconds <= 0 or args.speed <= 0 or args.quantity < 0 or (args.clone_count is not None and args.clone_count < 0):
        parser.error('seconds/speed must be positive; quantity/clone count must be nonnegative')
    if args.native_world and not args.plain:
        parser.error('--native-world requires --plain: wrapping projectileBlock disables the native helper fast path')
    native.URL = args.url
    # Capture originals before SETUP's first A.reset opens the controlled arena.
    native.HARNESS = native.HARNESS.replace('  const assert=', '  '+CAPTURE_WORLD+'\n  const assert=', 1)
    report = {'url': args.url, 'baseline': args.before, 'scope': 'Controlled stationary enemies; native combat and optional native terrain. Excludes scene render and full-game FPS.', 'cases': [], 'errors': []}
    output = ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=native.CHROME, headless=True)
        for name in args.cases.split(','):
            # Each case gets the same procedural world and fresh object/AI state.
            context = browser.new_context(viewport={'width': 1200, 'height': 900}, service_workers='block')
            context.add_init_script('('+SEED+')()')
            if args.before:
                for filename in ['naruto-temari.js', 'temari-cyclone-vfx.js']:
                    baseline = ROOT / '.omx/state/temari-performance' / (filename+'.before')
                    source = baseline.read_bytes()
                    context.route('**/'+filename+'*', lambda route, request, body=source: route.fulfill(status=200, content_type='application/javascript', body=body))
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            native.boot(page)
            report['sources'] = page.evaluate('Array.from(document.scripts,s=>s.src).filter(s=>/temari/.test(s))')
            params = {'full': name.startswith('full'), 'mobs': 60 if '60' in name else 30 if '30' in name else 0,
                      'clones': args.clone_count if args.clone_count is not None else 3 if 'clones' in name else 0,
                      'seconds': args.seconds, 'instrument': not args.plain, 'quantity': args.quantity,
                      'mastery': args.mastery, 'speed': args.speed, 'nativeWorld': args.native_world}
            started = time.perf_counter()
            result = page.evaluate(PROBE, params)
            result['wallSeconds'] = time.perf_counter() - started
            result['name'] = name
            report['cases'].append(result)
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps({k: result[k] for k in ['name', 'timing', 'hits', 'final', 'wallSeconds']}), flush=True)
            context.close()
        browser.close()
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(output), flush=True)


if __name__ == '__main__':
    main()
