"""Read-only Pain CPU diagnosis; timings exclude counters and GPU presentation."""
import argparse
import hashlib
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/pain-performance'

PROBE = r"""({count,terrain,skills}) => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain;
 p.moves=window.painProfileMoves.slice();
 A.reset();
 G.World.reset(12345);
 if(terrain==='native')Object.assign(G.World,window.painNativeWorld);
 p.hp=p.maxHp=1e8;p.invuln=999;p.quantityBonus=0;
 if(!skills)p.moves=p.moves.filter(m=>m.id==='naruto-pain');
 const center={x:0,y:0};
 if(terrain==='native'){
   let found=false;
   for(let r=0;r<1000&&!found;r+=32)for(let i=0;i<32&&!found;i++){
     const x=Math.cos(i*Math.PI/16)*r,y=Math.sin(i*Math.PI/16)*r;
     if(G.World.isFree(x,y,16,true)){center.x=x;center.y=y;found=true;}
   }
   A.assert(found,'no native terrain fixture');
 }
 p.x=center.x;p.y=center.y;
 for(const b of P.actorsFor(p)){b.x+=center.x;b.y+=center.y;b.hp=b.maxHp=1e8;}
 for(let i=0;i<count;i++){
   const angle=i*2.399963229728653,r=80+(i%15)*36;
   let x=center.x+Math.cos(angle)*r,y=center.y+Math.sin(angle)*r;
   if(terrain==='native'&&!G.World.isFree(x,y,10,true)){
     let found=false;
     for(let offset=0;offset<128&&!found;offset+=8)for(let j=0;j<16&&!found;j++){
       const sx=x+Math.cos(j*Math.PI/8)*offset,sy=y+Math.sin(j*Math.PI/8)*offset;
       if(G.World.isFree(sx,sy,10,true)){x=sx;y=sy;found=true;}
     }
   }
   A.spawn(x,y);
 }
 for(const m of p.moves)m.t=skills?0:999;
 const stats=values=>{values.sort((a,b)=>a-b);return {median:values[Math.floor(values.length*.5)],p95:values[Math.floor(values.length*.95)],max:values.at(-1)}};
 const stages={enemies:[],tick:[],fields:[],resolve:[]},counts={};
 function frame(timed){
   const run=(key,fn)=>{const start=performance.now();fn();if(timed)stages[key].push(performance.now()-start)};
   run('enemies',()=>{G.EnemyMgr.update(1/60,[p]);G.EnemyMgr.rebuildGrid()});
   run('tick',()=>G.Combat.tick(1/60,p,0));
   run('fields',()=>G.Combat.updateFields(1/60));
   run('resolve',()=>{G.Projectiles.update(1/60,p,G.EnemyMgr.all());G.Combat.resolve(1/60,p,0);G.FX.update(1/60)});
 }
 A.resume();
 try{
   for(let i=0;i<20;i++)frame(false);
   for(let i=0;i<120;i++)frame(true);
   const undo=[];
   const terrainKeys=G.World.projectilePathClear?['projectilePathClear','isFree']:['isWall','projectileBlock','isFree'];
   for(const [obj,keys]of [[G.World,terrainKeys],[G.EnemyMgr,['queryCircle','rebuildGrid']]])for(const key of keys){
     const old=obj[key];obj[key]=function(...args){const label=current+'.'+key;counts[label]=(counts[label]||0)+1;return old.apply(this,args)};undo.push(()=>obj[key]=old);
   }
   let current='enemies';
   try{
     G.EnemyMgr.update(1/60,[p]);G.EnemyMgr.rebuildGrid();
     current='tick';G.Combat.tick(1/60,p,0);
     current='fields';G.Combat.updateFields(1/60);
     current='resolve';G.Projectiles.update(1/60,p,G.EnemyMgr.all());G.Combat.resolve(1/60,p,0);
   }finally{for(const restore of undo)restore()}
 }finally{A.pause()}
 // Diagnostic ablation only: protection makes bodies ineligible as enemy targets.
 // This changes behavior and is not a proposed gameplay optimization.
 const protection=P.actorsFor(p).map(b=>b.protectionRemaining),isolated=[];
 A.resume();
 try{
   for(const b of P.actorsFor(p))b.protectionRemaining=999;
   for(let i=0;i<80;i++){const start=performance.now();G.EnemyMgr.update(1/60,[p]);G.EnemyMgr.rebuildGrid();if(i>=20)isolated.push(performance.now()-start)}
 }finally{P.actorsFor(p).forEach((b,i)=>b.protectionRemaining=protection[i]);A.pause()}
 A.assert(G.EnemyMgr.all().length===count&&P.actors().length===5,'benchmark population changed');
 return {count,terrain,skills,actualEnemies:G.EnemyMgr.all().length,bodies:P.actors().length,actions:P.snapshot(p).castCounts,stages:Object.fromEntries(Object.entries(stages).map(([k,v])=>[k,stats(v)])),counts,enemyUpdateWithBodyTargetingDisabledMs:stats(isolated)};
}"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--isolate', action='store_true')
    parser.add_argument('--compare', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    sources = ['.omx/naruto-pain.js', 'js/entities/enemy.js', 'js/world/world.js']
    hashes = lambda: {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources}
    report = {'sourceHashes': hashes(), 'terrainSeed': 12345, 'scope': '120 warmed native CPU updates at dt=1/60; counters in separate untimed frame. Stationary zero-damage enemies, five support bodies, default quantity. Native procedural terrain versus open arena. Excludes rendering, GPU and actual phone performance.', 'runs': [], 'errors': []}
    if args.compare:
        report['baselineSourceHashes'] = {name: hashlib.sha256((OUT / ('before-' + name)).read_bytes()).hexdigest() for name in ['naruto-pain.js', 'world.js']}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        modes = [('before', 1), ('after', 1)] if args.compare else ([('desktop', 1)] if args.isolate else [('desktop', 1), ('cpu4x', 4)])
        for mode, rate in modes:
            context = browser.new_context(viewport={'width': 1200, 'height': 900}, service_workers='block')
            if mode == 'before':
                for name in ['naruto-pain.js', 'world.js']:
                    context.route('**/' + name + '*', lambda route, request, name=name: route.fulfill(path=str(OUT / ('before-' + name)), content_type='application/javascript'))
            outer = context.new_page()
            outer.on('pageerror', lambda error: report['errors'].append(str(error)))
            outer.goto(URL)
            page = game_frame(outer)
            page.evaluate("window.painNativeWorld=Object.fromEntries(['isFree','isWall','projectileBlock','collide','isLiquid'].map(k=>[k,G.World[k]]))")
            enter(page)
            page.evaluate('window.painProfileMoves=G.Game.player.moves.slice()')
            context.new_cdp_session(outer).send('Emulation.setCPUThrottlingRate', {'rate': rate})
            # Restore the original learned moves before resetting each fixture.
            cases = [('native', 90, False), ('native', 240, False), ('native', 240, True)] if args.compare else ([('native', 240, False)] if args.isolate else [('open', 90, False), ('native', 90, False), ('native', 240, False), ('native', 240, True)])
            for terrain, count, skills in cases:
                result = page.evaluate(PROBE, {'count': count, 'terrain': terrain, 'skills': skills})
                result['mode'] = mode
                report['runs'].append(result)
                print(json.dumps(result), flush=True)
            context.close()
        browser.close()
    report['endingHashes'] = hashes()
    assert report['sourceHashes'] == report['endingHashes'], 'runtime source changed during measurement'
    (OUT / ('comparison.json' if args.compare else 'isolation.json' if args.isolate else 'report.json')).write_text(json.dumps(report, indent=2, ensure_ascii=False), 'utf-8')
    assert not report['errors'], report['errors']


if __name__ == '__main__':
    main()
