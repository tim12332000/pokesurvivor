"""Repeatable native Twin Rising Dragons workload; timings are host-specific."""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_tenten import CHROME, HARNESS, SETUP, PROGRESSION

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/tenten-performance'
CHECK = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,out=[];
 const twin=p.moves.find(m=>m.id==='naruto-tenten-twin');
 while(twin.lvl<5)G.Moves.levelUp(twin);
 p.moves.push(G.Moves.instance('naruto-tenten-bounce',5));
 const master=p.moves.find(m=>m.id==='naruto-tenten-mastery');
 while(master.lvl<5)G.Moves.levelUp(master);
 for(const picks of [8,20]){
   A.reset();p.quantityPicks=p.quantityBonus=picks;
   for(let x=120;x<=960;x+=120)for(let y=-360;y<=360;y+=120)A.spawn(x,y);
   p.target=A.spawn(160,0);A.select(twin.id);
   const counts={},timings={},wrapped=[];
   for(const [obj,key] of [[G.World,'projectileBlock'],[G.World,'propsInCircle'],[G.EnemyMgr,'queryCircle']]){
     const original=obj[key];wrapped.push([obj,key,original]);counts[key]=0;timings[key]=0;
     obj[key]=function(...args){counts[key]++;const start=performance.now();try{return original.apply(this,args)}finally{timings[key]+=performance.now()-start}};
   }
   try {
     const cv=document.createElement('canvas');cv.width=1200;cv.height=900;const ctx=cv.getContext('2d');
     const samples=[],drawSamples=[];let peak=0,totalHits=0;
     const start=performance.now();A.castNative(twin.id);const pose=T.activeFor(p),castMs=performance.now()-start;
     for(let i=0;i<120;i++){
       const begin=performance.now();A.resume();try{T.update(1/60)}finally{A.pause()}
       samples.push(performance.now()-begin);peak=Math.max(peak,T.weapons.length);
       const drawStart=performance.now();G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx);drawSamples.push(performance.now()-drawStart);
     }
     totalHits=G.EnemyMgr.all().filter(e=>e.hp<100000).length;
     A.assert(pose.emitted===Math.floor(40*Math.pow(1.25,picks)),'performance workload dropped projectiles');
     const sum=a=>a.reduce((s,n)=>s+n,0),p95=a=>[...a].sort((a,b)=>a-b)[Math.floor(a.length*.95)];
     out.push({picks,emitted:pose.emitted,peak,damagedTargets:totalHits,castMs,simulationMs:sum(samples),simulationP95:p95(samples),drawMs:sum(drawSamples),drawP95:p95(drawSamples),counts,timings});
   } finally {for(const [obj,key,original] of wrapped)obj[key]=original;A.reset();}
 }
 return out;
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page(viewport={'width': 1200, 'height': 900}, service_workers='block')
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto('http://127.0.0.1:8004/.omx/digimon.html?lang=zh-TW')
        page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible():
            page.locator('#tap-start').click()
        page.locator('[data-quick-naruto="30009"]').click()
        page.locator('#scr-menu [data-go="play"]').click()
        page.wait_for_function('G.Game.player?.dex===30009 && G.Game.state==="playing"')
        page.evaluate(HARNESS)
        page.evaluate(SETUP)
        page.evaluate(PROGRESSION)
        report = {'workloads': page.evaluate(CHECK), 'errors': errors}
        assert not errors, errors
        report['ok'] = True
        browser.close()
    label = os.environ.get('TENTEN_PERF_LABEL', 'latest')
    (OUT / f'{label}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
