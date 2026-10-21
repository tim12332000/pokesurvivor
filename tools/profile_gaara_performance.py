"""Deterministic native Gaara CPU/Canvas command benchmark, not a GPU FPS test."""
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS, SETUP

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/gaara-performance'
SOURCES = ['naruto-gaara.js', 'naruto-sand-guard.js', 'naruto-sand-vfx.js']

def compare_reports():
    comparisons={}
    for suffix in ['full','phases','raf']:
        before=json.loads((OUT/f'before-{suffix}-report.json').read_text(encoding='utf-8'))
        after=json.loads((OUT/f'after-{suffix}-report.json').read_text(encoding='utf-8'))
        assert before['sourceHashes']==before['endingHashes'],f'baseline sources changed: {suffix}'
        assert after['sourceHashes']==after['endingHashes'],f'after sources changed: {suffix}'
        key=lambda row:tuple(row.get(k) for k in ['mode','stress','guard','skill','wall','age'])
        indexed={key(row):row for row in before['runs']}
        rows=[]
        for row in after['runs']:
            old=indexed[key(row)]
            rows.append({'scenario':dict(zip(['mode','stress','guard','skill','wall','age'],key(row))),'before':old,'after':row})
        assert len(rows)==len(indexed),f'incomplete matched scenarios: {suffix}'
        comparisons[suffix]=rows
    result={'note':'Guardian wall phasing is an explicit user behavior change; its removed terrain cost must not be attributed to equivalent-gameplay optimization. CPU4x mobile viewport is not physical mobile hardware. Canvas times measure command submission (browser queue/driver waits may contribute), not GPU raster/presentation directly. Fixed-phase Canvas uses the same 1280x900 surface in both viewport modes. RAF is the headless native complete update/render loop on controlled OPEN terrain with naturally evolving phases and 120–160 sustained enemy shots; frame medians are not fixed-phase FPS.','comparisons':comparisons}
    (OUT/'comparison.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    lines=['# Gaara native CPU and Canvas command profile','',result['note'],'','Core tests: 90 enemies / 48 native hostile shots, or 240 / 160; with and without 10 physical guardians. Each timed sample resets the same positions, real learn/upgrade cards and skill phase. API counters run separately. Simulation includes native enemies/grid, combat tick, projectile update, resolve, fields, FX and actor animation. Canvas includes ground/air fields, player/enemies, projectiles and FX; excludes world/HUD unless labeled RAF.','', 'Warm medians and p95/p99 are descriptive; no hardware-dependent test threshold. Full matrix uses 48 samples after 8 warmups, phase matrix uses 16. At 16 samples, p95/p99 are the observed maximum. Initial main-matrix sand shower reference at 0.7s has no live basic bullet; the phase matrix explicitly covers live release bullets.','', '| Mode | Skill (stress, 10 guardians) | Simulation median before → after ms | Canvas median before → after ms | Simulation p95 before → after ms |','| --- | --- | ---: | ---: | ---: |']
    for row in comparisons['full']:
        scenario=row['scenario']
        if not scenario['stress'] or not scenario['guard'] or scenario['wall']:continue
        old,new=row['before'],row['after']
        metric=lambda kind,percentile:f"{old[kind][percentile]:.2f} → {new[kind][percentile]:.2f}"
        lines.append(f"| {scenario['mode']} | {scenario['skill']} | {metric('simulationMs','median')} | {metric('canvasCommandMs','median')} | {metric('simulationMs','p95')} |")
    lines.extend(['','Source SHA256 and initial population/phase/target assertions are in the JSON reports. Immutable original source copies are under `before/`.'])
    (OUT/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

PROBE = r"""({stress,guard,skill,samples,wall,age})=>{
 const A=Acceptance,p=A.p(),N=G.NarutoGaara,ids=['naruto-gaara','naruto-sand-coffin','naruto-sand-shield','naruto-sand-tsunami','naruto-sand-prison','naruto-sand-armor'];
 const stats=a=>{a.sort((x,y)=>x-y);return {median:a[Math.floor(a.length*.5)],p95:a[Math.min(a.length-1,Math.floor(a.length*.95))],p99:a[Math.min(a.length-1,Math.floor(a.length*.99))]}};
 p.level=25;p.maxMoves=20;
 for(const id of ids){if(!p.hasMove(id)){const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(card,'missing card '+id);card.apply(p)}
  while(p.moves.find(m=>m.id===id).lvl<5){const card=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);A.assert(card,'missing upgrade '+id);card.apply(p)}}
 const allMoves=p.moves.slice(),canvas=document.createElement('canvas');canvas.width=1280;canvas.height=900;const ctx=canvas.getContext('2d');ctx.translate(640,450);
 const size=stress?240:90,shots=stress?160:48;
 function prepare(){p.moves=allMoves.slice();A.gaaraArena();p.level=25;p.quantityBonus=20;p.hp=p.maxHp=1e8;p.invuln=0;
  if(!guard)p.moves=p.moves.filter(m=>m.id!=='naruto-sand-shield');
  if(wall){G.World.isWall=(x,y)=>x>95&&x<115&&Math.abs(y)<140;G.World.projectileBlock=(x,y)=>G.World.isWall(x,y)?'wall':false;}
  for(let i=0;i<size;i++){const angle=i*2.399963229728653,r=45+(i%9)*24;A.spawn(Math.cos(angle)*r,Math.sin(angle)*r)}
  p.target=G.EnemyMgr.all()[0];p.aim=0;
  A.select(skill==='naruto-sand-shield'||p.moves.find(m=>m.id===skill)?.passive?'naruto-gaara':skill);A.resume();
  G.Combat.tick(.001,p,0);G.Combat.updateFields(age??(skill==='naruto-sand-prison'?6:.7));
  if(skill==='naruto-sand-armor'){G.Combat.updateFields(0.001)}
  for(let i=0;i<shots;i++){const angle=i*2.399963229728653,x=Math.cos(angle)*(230+(i%4)*30),y=Math.sin(angle)*(230+(i%4)*30),e=G.EnemyMgr.all()[i%size];
   const ex=e.x,ey=e.y;e.x=x;e.y=y;e.shoot(-Math.cos(angle),-Math.sin(angle));e.x=ex;e.y=ey;}
  if(guard)G.NarutoSandGuard.state(p);A.pause();
 }
 function update(){G.EnemyMgr.update(1/60,[p]);G.EnemyMgr.rebuildGrid();G.Combat.tick(1/60,p,0);G.Projectiles.update(1/60,p,G.EnemyMgr.all());G.Combat.resolve(1/60,p,0);G.Combat.updateFields(1/60);G.FX.update(1/60);p.anim.update(1/60)}
 function draw(){ctx.clearRect(-640,-450,1280,900);G.Combat.drawGroundFields(ctx);for(const e of G.EnemyMgr.all())e.draw(ctx);p.draw(ctx);G.Projectiles.draw(ctx);G.Combat.drawAirFields(ctx);G.FX.draw(ctx)}
 prepare();const actual={enemies:G.EnemyMgr.all().length,hostile:G.Projectiles.all().filter(q=>!q.friendly).length,guardians:guard?G.NarutoSandGuard.state(p).count:0,phase:N.active(p)?.phase,targets:N.active(p)?.targets?.length,prison:!!N.sandPrisonState(p),armor:!!N.armorState(p),basicBullets:N.bullets.length};
 A.assert(actual.enemies===size&&actual.hostile===shots,'native population mismatch');
 A.assert(actual.guardians===(guard?10:0),'guardian population mismatch');
 if(skill==='naruto-sand-coffin'&&!wall)A.assert(actual.targets===30,'coffin target count changed');
 if(skill==='naruto-sand-prison')A.assert(actual.prison,'prison field missing');
 if(skill==='naruto-gaara'&&age&&age<.35)A.assert(actual.basicBullets>0,'basic release bullets missing');
 const firstStart=performance.now();draw();const firstCanvasCommandMs=performance.now()-firstStart;
 const calls={},undo=[];function wrap(obj,key,label=key){if(typeof obj[key]!=='function')return;const old=obj[key];obj[key]=function(...a){calls[label]=(calls[label]||0)+1;return old.apply(this,a)};undo.push(()=>obj[key]=old)}
 for(const key of ['isWall','projectileBlock'])wrap(G.World,key);wrap(G.EnemyMgr,'queryCircle');for(const key of ['burst','ring'])wrap(G.FX,key,'FX.'+key);for(const key of ['fillRect','fill','drawImage','stroke'])wrap(ctx,key);
 A.resume();update();draw();A.pause();for(const restore of undo)restore();
 const sim=[],render=[];
 for(let i=0;i<samples+8;i++){prepare();A.resume();let t=performance.now();update();let elapsed=performance.now()-t;A.pause();t=performance.now();draw();let painted=performance.now()-t;if(i>=8){sim.push(elapsed);render.push(painted)}}
 p.moves=allMoves;A.pause();return {skill,stress,guard,wall,age,actual,calls,firstCanvasCommandMs,simulationMs:stats(sim),canvasCommandMs:stats(render),samples};
}"""

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',default='before');parser.add_argument('--quick',action='store_true');parser.add_argument('--snapshot',action='store_true');parser.add_argument('--phases',action='store_true');parser.add_argument('--impact-only',action='store_true');parser.add_argument('--raf',action='store_true');parser.add_argument('--samples',type=int);parser.add_argument('--compare',action='store_true');args=parser.parse_args()
    if args.impact_only:args.phases=True
    if args.compare:
        compare_reports();return
    sample_count=args.samples or (20 if args.quick else 48)
    OUT.mkdir(parents=True,exist_ok=True)
    source_dir=OUT/'before' if args.snapshot else ROOT/'.omx'
    hashes={name:hashlib.sha256((source_dir/name).read_bytes()).hexdigest() for name in SOURCES}
    report={'sourceHashes':hashes,'scope':'Native enemy update/grid, Combat.tick/projectile update/resolve/fields, FX and actor animation; separate Canvas command submission including enemies/player/projectiles/fields/FX. Open controlled terrain plus wall stress. No GPU presentation or real mobile hardware claim. Timings descriptive, no CI limits.','runs':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=CHROME,headless=True)
        for mobile in ([False] if args.quick else [False,True]):
            context=browser.new_context(viewport={'width':390 if mobile else 1280,'height':844 if mobile else 900},service_workers='block')
            if args.snapshot:
                for name in SOURCES:
                    context.route('**/'+name+'*',lambda route,request,name=name:route.fulfill(path=str(source_dir/name),content_type='application/javascript'))
            page=context.new_page();page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
            page.locator('[data-quick-naruto="30007"]').click();page.locator('#scr-menu [data-go="play"]').click();page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"');page.evaluate(HARNESS);page.evaluate(SETUP)
            if mobile:context.new_cdp_session(page).send('Emulation.setCPUThrottlingRate',{'rate':4})
            for stress in ([] if args.phases or args.raf else [False,True]):
                for guard in [False,True]:
                    for skill in ['naruto-gaara','naruto-sand-coffin','naruto-sand-shield','naruto-sand-tsunami','naruto-sand-prison','naruto-sand-armor']:
                        row=page.evaluate(PROBE,{'stress':stress,'guard':guard,'skill':skill,'samples':sample_count,'wall':False});row['mode']='mobileViewportCpu4x' if mobile else 'desktop';report['runs'].append(row)
                        (OUT/(args.phase+'-report.json')).write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(row),flush=True)
            for guard in ([] if args.raf or args.impact_only else [False,True]):
                row=page.evaluate(PROBE,{'stress':True,'guard':guard,'skill':'naruto-sand-coffin','samples':sample_count,'wall':True});row['mode']='mobileViewportCpu4x' if mobile else 'desktop';report['runs'].append(row)
            if args.phases:
                scenarios=[('naruto-sand-tsunami',[1.65,1.8])] if args.impact_only else [('naruto-gaara',[.12,.3]),('naruto-sand-coffin',[.1,.7,1.35]),('naruto-sand-tsunami',[.1,.5,.9,1.3,1.5,1.65,1.8]),('naruto-sand-armor',[.3,3.05]),('naruto-sand-shield',[.1]),('naruto-sand-prison',[6,8.5])]
                for skill,ages in scenarios:
                    for age in ages:
                        row=page.evaluate(PROBE,{'stress':True,'guard':False,'skill':skill,'samples':sample_count,'wall':False,'age':age});row['mode']='mobileViewportCpu4x' if mobile else 'desktop';report['runs'].append(row)
                        (OUT/(args.phase+'-report.json')).write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(row),flush=True)
            if args.raf:
                for guard in [False,True]:
                    page.evaluate(PROBE,{'stress':True,'guard':guard,'skill':'naruto-sand-tsunami','samples':1,'wall':False,'age':.5})
                    row=page.evaluate(r'''async()=>{const A=Acceptance,p=A.p(),times=[],counts=[];let previous=0;
                     const refill=()=>{const list=G.Projectiles.all();for(let i=list.filter(q=>!q.friendly).length;i<160;i++){const angle=i*2.399963229728653,e=G.EnemyMgr.all()[i%G.EnemyMgr.all().length];if(!e)break;const x=e.x,y=e.y;e.x=Math.cos(angle)*290;e.y=Math.sin(angle)*290;e.shoot(-Math.cos(angle),-Math.sin(angle));e.x=x;e.y=y;}};
                     const timer=setInterval(refill,150);A.resume();
                     await new Promise(resolve=>{const sample=t=>{if(previous)times.push(t-previous);previous=t;counts.push({enemy:G.EnemyMgr.all().length,hostile:G.Projectiles.all().filter(q=>!q.friendly).length});if(times.length<90)requestAnimationFrame(sample);else resolve()};requestAnimationFrame(sample)});
                     clearInterval(timer);A.pause();times.sort((a,b)=>a-b);return {rafMs:{median:times[45],p95:times[85],p99:times[89]},frames:times.length,over33ms:times.filter(t=>t>33.4).length,enemies:[Math.min(...counts.map(c=>c.enemy)),Math.max(...counts.map(c=>c.enemy))],hostile:[Math.min(...counts.map(c=>c.hostile)),Math.max(...counts.map(c=>c.hostile))]};}''')
                    row.update({'mode':'mobileViewportCpu4x' if mobile else 'desktop','guard':guard,'nativeGameRaf':True});report['runs'].append(row);print(json.dumps(row),flush=True)
                    (OUT/(args.phase+'-report.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
            context.close()
        browser.close()
    report['endingHashes']={name:hashlib.sha256((source_dir/name).read_bytes()).hexdigest() for name in SOURCES}
    (OUT/(args.phase+'-report.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')

if __name__=='__main__':main()
