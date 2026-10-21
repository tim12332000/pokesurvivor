"""Same-revision native guard CPU/Canvas and deterministic interception comparison."""
import argparse, hashlib, json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS, SETUP
from test_gaara_sand_guard import FIXTURE
from profile_gaara_performance import PROBE as COMBINED
COMBINED=COMBINED.replace("if(guard)G.NarutoSandGuard.state(p);A.pause();","if(guard)G.NarutoSandGuard.state(p);if(skill==='naruto-sand-shield'){p.invuln=0;p.hurt(2,null,true,{fromX:100,fromY:0})}A.pause();")
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.omx/state/gaara-sand-flow'
FILES=['.omx/naruto-sand-guard.js','.omx/naruto-sand-vfx.js','.omx/naruto-gaara.js','.omx/naruto-skills.js','.omx/naruto-training.js','js/ui/hud.js']
INIT=r'''()=>{const A=Acceptance,p=A.p();p.level=25;p.maxMoves=20;for(const id of ['naruto-gaara','naruto-sand-coffin','naruto-sand-shield','naruto-sand-tsunami','naruto-sand-prison','naruto-sand-armor']){if(!p.hasMove(id))G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id).apply(p);while(p.moves.find(m=>m.id===id).lvl<5)G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id).apply(p)}A.pause();}'''
PROBE=r'''({scenario,count})=>{
const A=Acceptance,p=A.p();A.gaaraArena();p.level=count===3?1:25;p.moves.find(m=>m.id==='naruto-sand-shield').lvl=count===3?1:5;p.hp=p.maxHp=1e8;
const g=A.guard(),ctx=document.createElement('canvas').getContext('2d');ctx.canvas.width=1280;ctx.canvas.height=900;ctx.translate(640,450);
A.resume();const step=()=>{G.Projectiles.update(1/60,p,[]);G.Combat.resolve(1/60,p,0)};
for(let i=0;i<240;i++)step();
if(scenario==='pursuit')for(let i=0;i<10;i++){const a=i*Math.PI/5;A.nativeShot(Math.cos(a)*320,Math.sin(a)*320,-Math.cos(a),-Math.sin(a))}
if(scenario==='return')g.guardians.forEach(c=>{c.ready=false;c.charges=0;c.rechargeProgress=0;c.target=null});
if(scenario==='burst')for(const c of g.guardians)A.nativeShot(c.x,c.y,1,0);
if(scenario==='offscreen')ctx.translate(10000,10000);
const stats=a=>{a.sort((a,b)=>a-b);return {median:a[Math.floor(a.length*.5)],p95:a[Math.floor(a.length*.95)],p99:a[Math.floor(a.length*.99)]}};
const sim=[],draw=[],paint=[],commands=[],states=[],groupCosts=[];
const countDraw=()=>{let paint=0,commands=0;const undo=[];for(const name of ['beginPath','moveTo','lineTo','quadraticCurveTo','bezierCurveTo','arc','closePath','fill','stroke','fillRect','drawImage','save','restore','translate','rotate','scale']){const old=ctx[name];ctx[name]=function(...a){commands++;if(['fill','stroke','fillRect','drawImage'].includes(name))paint++;return old.apply(this,a)};undo.push(()=>ctx[name]=old)}try{G.NarutoSandVFX.drawGuardGroup(ctx,g)}finally{undo.forEach(f=>f())}return {paint,commands}};
let terrainCalls=0;const oldWall=G.World.isWall,oldBlock=G.World.projectileBlock;
G.World.isWall=(...a)=>{terrainCalls++;return oldWall(...a)};G.World.projectileBlock=(...a)=>{terrainCalls++;return oldBlock(...a)};
// Keep timed samples free of Canvas wrappers; counters use a separate draw.
try{for(let i=0;i<110;i++){
let t=performance.now();step();const s=performance.now()-t;
t=performance.now();G.NarutoSandVFX.drawGuardGroup(ctx,g);const d=performance.now()-t;
if(i>=10){sim.push(s);draw.push(d)}
if(i%10===0){states.push({frame:i,ready:g.readyCount,phases:g.guardians.map(c=>c.phase),groups:g.flowGroups?.filter(f=>f.active).length??null,pairChecks:g.flowPairChecks??0,flowAge:g.flowAge??null});const c=countDraw();paint.push(c.paint);commands.push(c.commands)}
}
const draws=Math.max(...paint),cmds=Math.max(...commands);
return {scenario,count,simulationMs:stats(sim),canvasCommandMs:stats(draw),paintCalls:draws,canvasCalls:cmds,terrainCalls,states,samples:100};
}finally{A.pause();G.World.isWall=oldWall;G.World.projectileBlock=oldBlock}
}'''
VOLLEY=r'''({pattern,moving})=>{
const A=Acceptance,p=A.p();A.gaaraArena();p.level=25;p.hp=p.maxHp=1e8;p.cdMul=1;p.invuln=0;const g=A.guard();
A.resume();const step=()=>{if(p.invuln>0)p.invuln-=.02;G.Projectiles.update(.02,p,[]);G.Combat.resolve(.02,p,0)};
for(let i=0;i<250;i++)step();
const initial=g.guardians.map(c=>({x:c.x,y:c.y,ready:c.ready})),shots=[],events=[],ready=[],removed=G.Projectiles.remove;
let guards=0,otherRemoves=0;G.Projectiles.remove=function(q){if(shots.includes(q)&&q.friendly===false){guards++;events.push({t:now,x:q.x,y:q.y})}return removed.call(this,q)};
const shield0=G.NarutoGaara.shieldState(p).amount,hp0=p.hp;let now=0;
try{for(let i=0;i<600;i++){now=i*.02;
if(moving){p.x=Math.sin(now*.7)*65;p.y=Math.sin(now*.43)*45}
if(i%15===0&&i<360){const n=i/15;const a=pattern==='eightDirections'?(n%8)*Math.PI/4:pattern==='oneSide'?((n%5)-2)*.13:(n%2?Math.PI:0)+((n%3)-1)*.13;
const q=A.nativeShot(p.x+Math.cos(a)*330,p.y+Math.sin(a)*330,-Math.cos(a),-Math.sin(a));A.assert(Math.abs(Math.hypot(q.vx,q.vy)-190)<.001&&q.life===2.4,'non-native volley');shots.push(q)}
step();if(i%50===0)ready.push(g.guardians.map(c=>({ready:c.ready,contact:!!c.contact,phase:c.phase})));
}
return {pattern,moving,shotCount:shots.length,guardRemovals:guards,interceptionRate:guards/shots.length,hpDamage:hp0-p.hp,shieldSpent:shield0-G.NarutoGaara.shieldState(p).amount,initial,events,ready};
}finally{A.pause();G.Projectiles.remove=removed}
}'''
def hashes(base):return {f:hashlib.sha256((base/f).read_bytes()).hexdigest() for f in FILES}
def repeat_combined():
 versions={'before':OUT/'before','after':ROOT}
 sources={phase:{f:(base/f).read_text(encoding='utf-8-sig') for f in FILES} for phase,base in versions.items()}
 initial={phase:hashes(base) for phase,base in versions.items()}
 result={'sourceHashes':initial,'scope':'Three independent 32-sample warmed mobile-viewport CPU4x batches per revision and scene; interleaved revision order before/after, after/before, before/after. Same native 240 enemies and 160 shots; each sample resets original native scene. Whole-scene simulation and Canvas measured separately. Descriptive repeat check, no hardware-dependent pass threshold.','runs':[]}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=CHROME,headless=True)
  for batch in range(3):
   for phase in (['before','after'] if batch%2==0 else ['after','before']):
    context=browser.new_context(viewport={'width':390,'height':844},service_workers='block')
    for f,source in sources[phase].items():context.route('**/'+f.split('/')[-1]+'*',lambda route,request,source=source:route.fulfill(body=source,content_type='application/javascript'))
    page=context.new_page();page.goto(URL);page.wait_for_function("window.PS_REDRAWN_READY && G.NarutoSandGuard && document.getElementById('boot').classList.contains('hidden')")
    if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
    page.locator('[data-quick-naruto="30007"]').click();page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"');page.evaluate(HARNESS);page.evaluate(SETUP);page.evaluate(FIXTURE);page.evaluate(INIT)
    context.new_cdp_session(page).send('Emulation.setCPUThrottlingRate',{'rate':4})
    for skill,age in [('naruto-sand-coffin',.7),('naruto-sand-tsunami',.5),('naruto-sand-shield',.1)]:
     row=page.evaluate(COMBINED,{'stress':True,'guard':True,'skill':skill,'samples':32,'wall':False,'age':age});row.update(phase=phase,batch=batch);result['runs'].append(row);print('repeat',batch,phase,skill,row['simulationMs'],flush=True)
    context.close()
  browser.close()
 result['endingHashes']={phase:hashes(base) for phase,base in versions.items()};assert initial==result['endingHashes'],'sources changed during repeat'
 (OUT/'combined-repeats.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 lines=['','## Repeated whole-scene check','',result['scope'],'','| Batch | Revision | Scene | CPU median / p95 ms | Canvas median / p95 ms |','|---|---|---|---:|---:|']
 for r in result['runs']:lines.append(f"| {r['batch']+1} | {r['phase']} | {r['skill']} | {r['simulationMs']['median']:.2f} / {r['simulationMs']['p95']:.2f} | {r['canvasCommandMs']['median']:.2f} / {r['canvasCommandMs']['p95']:.2f} |")
 with (OUT/'performance.md').open('a',encoding='utf-8') as stream:stream.write('\n'.join(lines)+'\n')

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['before','after'],default='after');parser.add_argument('--repeat-combined',action='store_true');parser.add_argument('--rates-only',action='store_true');args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
 if args.repeat_combined:
  repeat_combined();return
 base=OUT/'before' if args.phase=='before' else ROOT
 frozen_sources={f:(base/f).read_text(encoding="utf-8-sig") for f in FILES}
 report={'sourceHashes':hashes(base),'seed':'deterministic golden-angle idle, native 190 speed / 2.4 life, volleys every .30 sec from 330 range for 24 shots; 5 sec natural idle settle; 12 sec measured; native player invulnerability timer decremented each dt','scope':'Guard resolve CPU and guard-only Canvas command submission timed separately; API paint counters untimed. Combined simulation/render includes native enemies, projectiles, six merged skills; mobile viewport CPU4x is not physical mobile/GPU FPS.','runs':[],'volleys':[],'combined':[]}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=CHROME,headless=True)
  for mobile in ([False] if args.rates_only else [False,True]):
   context=browser.new_context(viewport={'width':390 if mobile else 1280,'height':844 if mobile else 900},service_workers='block')
   # Freeze every participating source for both passes, never mix live revisions.
   sources=frozen_sources
   for f,source in sources.items():context.route('**/'+f.split('/')[-1]+'*',lambda route,request,source=source:route.fulfill(body=source,content_type='application/javascript'))
   page=context.new_page();page.goto(URL);page.wait_for_function("window.PS_REDRAWN_READY && G.NarutoSandGuard && document.getElementById('boot').classList.contains('hidden')")
   if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
   page.locator('[data-quick-naruto="30007"]').click();page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"');page.evaluate(HARNESS);page.evaluate(SETUP);page.evaluate(FIXTURE);page.evaluate(INIT)
   if mobile:context.new_cdp_session(page).send('Emulation.setCPUThrottlingRate',{'rate':4})
   mode='mobileViewportCpu4x' if mobile else 'desktop'
   for scenario,count in ([] if args.rates_only else [('idle',3),('idle',10),('pursuit',10),('return',10),('burst',10),('offscreen',10)]):
    row=page.evaluate(PROBE,{'scenario':scenario,'count':count});row['mode']=mode;report['runs'].append(row);print(mode,scenario,row['simulationMs'],row['paintCalls'],flush=True)
   for stress,skill,age in ([] if args.rates_only else [(False,'naruto-sand-coffin',.7),(True,'naruto-sand-coffin',.7),(True,'naruto-sand-tsunami',.5),(True,'naruto-sand-shield',.1)]):
    row=page.evaluate(COMBINED,{'stress':stress,'guard':True,'skill':skill,'samples':24,'wall':False,'age':age});row['mode']=mode;report['combined'].append(row)
   # One identical deterministic functional comparison on desktop; simulation dt is fixed.
   if not mobile:
    for pattern in ['eightDirections','oneSide','alternating']:
     for moving in [False,True]:
      row=page.evaluate(VOLLEY,{'pattern':pattern,'moving':moving});report['volleys'].append(row);print('volley',pattern,moving,row['guardRemovals'],flush=True)
   context.close()
  browser.close()
 report['endingHashes']=hashes(base)
 checked=[f for f in FILES if not args.rates_only or 'vfx' not in f]
 assert all(report['sourceHashes'][f]==report['endingHashes'][f] for f in checked),'functional source changed during benchmark'
 suffix='rates' if args.rates_only else 'performance'
 (OUT/f'{args.phase}-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 if args.phase=='after' and not args.rates_only:
  before=json.loads((OUT/'before-performance.json').read_text(encoding='utf-8'));comparison={'runs':[],'volleys':[]}
  for old,new in zip(before['runs'],report['runs']):comparison['runs'].append({'scenario':new['scenario'],'mode':new['mode'],'count':new['count'],'before':old,'after':new})
  for old,new in zip(before['volleys'],report['volleys']):comparison['volleys'].append({'pattern':new['pattern'],'moving':new['moving'],'before':old['interceptionRate'],'after':new['interceptionRate'],'delta':new['interceptionRate']-old['interceptionRate']})
  (OUT/'comparison.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
  lines=['# Flowing sand native benchmark','',report['scope'],'','Peak paint measured separately every ten frames, including first burst/contact frame. 100 warmed frame samples per guard phase; 24 warmed samples per combined scenario. Guard phases evolve naturally during samples, rather than forced static node positions. No node position resets in rate comparison. p95/p99 are descriptive.','', '| Mode | Scenario | Nodes | CPU median before / after ms | Canvas median before / after ms | Peak paint before / after |','|---|---|---:|---:|---:|---:|']
  for row in comparison['runs']:
   a,b=row['before'],row['after'];lines.append(f"| {row['mode']} | {row['scenario']} | {row['count']} | {a['simulationMs']['median']:.3f} / {b['simulationMs']['median']:.3f} | {a['canvasCommandMs']['median']:.3f} / {b['canvasCommandMs']['median']:.3f} | {a['paintCalls']} / {b['paintCalls']} |")
  lines.extend(['','## Native volley parity','','| Pattern | Moving | Before | After |','|---|---|---:|---:|'])
  for row in comparison['volleys']:lines.append(f"| {row['pattern']} | {row['moving']} | {row['before']:.1%} | {row['after']:.1%} |")
  lines.extend(['','## Combined native scenes','','| Mode | Scene | Stress | CPU median before / after ms | Canvas median before / after ms | CPU p95 before / after ms | Canvas p95 before / after ms |','|---|---|---|---:|---:|---:|---:|'])
  for a,b in zip(before['combined'],report['combined']):
   lines.append(f"| {b['mode']} | {b['skill']} | {b['stress']} | {a['simulationMs']['median']:.2f} / {b['simulationMs']['median']:.2f} | {a['canvasCommandMs']['median']:.2f} / {b['canvasCommandMs']['median']:.2f} | {a['simulationMs']['p95']:.2f} / {b['simulationMs']['p95']:.2f} | {a['canvasCommandMs']['p95']:.2f} / {b['canvasCommandMs']['p95']:.2f} |")
  max_pairs=max((x['pairChecks'] for r in report['runs'] for x in r['states']),default=0)
  lines.extend(['',f'Observed grouping pair checks per refresh: at most {max_pairs}; guard-only peak paint: {max(r["paintCalls"] for r in report["runs"])}. Per-run median/p95/p99, source SHA256, actual populations, group states, shot events, ready/contact phases, and shield damage are in JSON. Terrain calls in this probe include native projectile walls; they are not guardian-only calls. No real GPU presentation or complete game RAF FPS claim.'])
  (OUT/'performance.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
if __name__=='__main__':main()
