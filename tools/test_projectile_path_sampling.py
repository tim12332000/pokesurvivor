"""Compare native cached path sampling with its literal per-sample contract."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_temari import CHROME, URL

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/projectile-path'

CHECK = r"""extended => {
 const W=G.World,assert=(ok,msg)=>{if(!ok)throw Error(msg)},saved={isWall:W.isWall,projectileBlock:W.projectileBlock};
 const brute=(a,b,c,d,target,opts)=>{
   const {radius=1,spacing=4,includeStart=true}=opts||{};
   const n=Math.max(1,Math.ceil(Math.hypot(c-a,d-b)/spacing));
   for(let i=includeStart?0:1;i<=n;i++){
     const x=a+(c-a)*i/n,y=b+(d-b)*i/n;
     if(!opts&&W.isWall(x,y))return false;
     if(W.projectileBlock){const p=W.projectileBlock(x,y,radius);if(p&&p!==target)return false;}
     else if(W.isWall?.(x,y))return false;
   }return true;
 };
 let comparisons=0,blocked=0,open=0;
 const compare=(ray,target,opts)=>{const want=brute(...ray,target,opts),actual=opts?W.projectilePathClear(...ray,target,opts):W.projectilePathClear(...ray,target);
   assert(actual===want,'path mismatch '+JSON.stringify({ray,opts,want,actual}));comparisons++;if(want)open++;else blocked++;};
 // Seeded native terrain, wall boundaries, overlapping props and target props.
 let seed=73021;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
 W.setArena(null);
 for(let i=0;i<1200;i++){
   const x=(random()-.5)*6000,y=(random()-.5)*6000;
   const ray=[x,y,x+(random()-.5)*700,y+(random()-.5)*700];
   compare(ray,null);
   if(extended){
     for(const radius of [0,1,4,12,30])compare(ray,null,{radius,spacing:5,includeStart:false});
     compare(ray,'wall',{radius:1,spacing:5,includeStart:false});compare(ray,null,{});
   }
 }
 const props=W.propsInCircle(0,0,2000).filter(p=>p.solid);
 assert(props.length>0,'native solid prop fixture missing');
 for(const p of props.slice(0,35))for(const dx of [-80,-20,0,20,80]){
   const ray=[p.x+dx,p.y-70,p.x,p.y];compare(ray,p);
   if(extended)compare(ray,p,{radius:8,spacing:5,includeStart:false});
 }
 const p=props.find(p=>p.destructible);assert(p,'native destructible fixture missing');
 const ray=[p.x-70,p.y,p.x+70,p.y];compare(ray,null);W.breakProp(p);compare(ray,null);
 if(extended)compare(ray,null,{radius:4,spacing:5,includeStart:false});
 const nativeComparisons=comparisons,custom=[];
 try{
   const target={solid:true};
   for(const mode of ['wall-and-block','block-only','wall-only','overridden-wall-native-block']){
     W.isWall=mode==='block-only'?undefined:x=>x<1||x>65;
     W.projectileBlock=mode==='wall-only'?undefined:mode==='overridden-wall-native-block'?saved.projectileBlock:(x,y,r)=>x>45&&x<55?(r>2?target:'wall'):null;
     for(const radius of [0,1,5])for(const includeStart of [false,true])for(const targetArg of [null,target,'wall']){
       if(extended)compare([0,0,80,0],targetArg,{radius,spacing:5,includeStart});
     }
     if(mode==='wall-and-block')compare([0,0,80,0],null);
     custom.push(mode);
   }
   // Explicit origin/zero-distance and sample-position checks.
   if(extended){
     let samples=[];W.isWall=()=>{throw Error('projectileBlock must take precedence')};
     W.projectileBlock=(x,y,r)=>{samples.push([x,y,r]);return null};
     assert(W.projectilePathClear(0,0,11,0,null,{radius:7,spacing:5,includeStart:false}),'open custom ray');
     assert(JSON.stringify(samples)===JSON.stringify([[11/3,0,7],[22/3,0,7],[11,0,7]]),'incorrect exact sample positions '+JSON.stringify(samples));
     samples=[];W.projectilePathClear(3,4,3,4,null,{radius:2,spacing:5,includeStart:false});
     assert(JSON.stringify(samples)==='[[3,4,2]]','zero-distance end sample changed');
   }
 }finally{Object.assign(W,saved)}
 assert(blocked>0&&open>0,'native fixture must include open and blocked rays');
 return {comparisons,nativeComparisons,blocked,open,solidProps:props.length,destroyedProp:true,custom,extended};
}"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--legacy-only', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'errors': [], 'checks': {}}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page(viewport={'width': 1100, 'height': 800})
        page.on('pageerror', lambda error: report['errors'].append(str(error)))
        page.goto(URL + ('&' if '?' in URL else '?') + 'layout=wide')
        page.wait_for_function("window.PS_REDRAWN_READY && window.G?.NarutoTemari && document.getElementById('boot').classList.contains('hidden')", polling=20)
        if page.locator('#tap-start').is_visible():
            page.locator('#tap-start').click()
        page.locator('[data-quick-naruto="30011"]').click()
        page.locator('#scr-menu [data-go="play"]').click()
        page.wait_for_function('G.Game.player?.dex===30011 && G.Game.state==="playing"', polling=20)
        page.evaluate('G.Game.togglePause()')
        report['checks'] = page.evaluate(CHECK, not args.legacy_only)
        browser.close()
    report['ok'] = not report['errors']
    path = OUT / ('legacy-baseline.json' if args.legacy_only else 'report.json')
    path.write_text(json.dumps(report, indent=2), 'utf-8')
    print(json.dumps(report))
    if not report['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
