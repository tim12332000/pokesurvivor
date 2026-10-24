"""Lock native Six Paths target selection and sampled terrain visibility."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame

OUT = Path(__file__).resolve().parents[1] / '.omx/state/pain-targeting'
CHECK = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,W=G.World;
 A.reset();const bs=P.actorsFor(p),e=A.spawn(0,0),old=G.Path.dirFor;
 const wall=W.isWall,block=W.projectileBlock;let chosen=null;
 G.Path.dirFor=(enemy,target)=>{chosen=target;return null};
 function reset(){p.x=200;p.y=0;p.dead=false;e.x=e.y=0;e.flying=false;e.sideT=0;e.phase='chase';
   for(let i=0;i<bs.length;i++)Object.assign(bs[i],{x:100+i*10,y:0,dead:false,hp:100,formed:true,protectionRemaining:0});
   W.isWall=()=>false;W.projectileBlock=()=>false;chosen=null;}
 function expect(target,label){e.update(.001,p);A.assert(chosen===target,'wrong target: '+label)}
 try{
   reset();expect(bs[0],'nearest ready body');
   reset();bs[4].x=50;expect(bs[4],'nearest body regardless of family order');
   reset();W.isWall=(x,y)=>x>35&&x<65&&Math.abs(y)<5;bs[1].x=0;bs[1].y=120;expect(bs[1],'blocked nearest skipped');
   reset();p.x=30;expect(p,'closer player');
   for(const patch of [{dead:true},{hp:0},{formed:false},{protectionRemaining:1}]){
     reset();Object.assign(bs[0],patch);expect(bs[1],JSON.stringify(patch));
   }
   reset();bs[1].x=100;expect(bs[0],'equal distance keeps first body');
   reset();p.x=100;expect(p,'equal distance keeps player');
   reset();p.dead=true;expect(bs[0],'dead player rescue keeps body targets');
 }finally{p.dead=false;W.isWall=wall;W.projectileBlock=block;G.Path.dirFor=old;A.reset()}
 return {targetCases:11};
}"""
RAYS = r"""() => {
 const W=G.World,A=Acceptance;Object.assign(W,window.painNativeWorld);
 A.assert(typeof W.projectilePathClear==='function','missing batched visibility');
 function reference(ax,ay,bx,by,target=null){const n=Math.max(1,Math.ceil(Math.hypot(bx-ax,by-ay)/4));
   for(let i=0;i<=n;i++){const x=ax+(bx-ax)*i/n,y=ay+(by-ay)*i/n;if(W.isWall(x,y))return false;
     const b=W.projectileBlock(x,y,1);if(b&&b!==target)return false;}return true;}
 let seed=12345,blocked=0,open=0;
 const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
 for(let i=0;i<600;i++){
   const x=(rand()-.5)*2400,y=(rand()-.5)*2400,dx=(rand()-.5)*700,dy=(rand()-.5)*700;
   const target=i%3===0?W.projectileBlock(x,y,1):null;
   const expected=reference(x,y,x+dx,y+dy,target),actual=W.projectilePathClear(x,y,x+dx,y+dy,target);
   A.assert(expected===actual,'native visibility mismatch '+i);if(actual)open++;else blocked++;
 }
 for(const [x,y]of [[0,0],[-32,-32],[32,32]])A.assert(reference(x,y,x,y)===W.projectilePathClear(x,y,x,y),'zero length mismatch');
 A.assert(open>0&&blocked>0,'missing visibility coverage');
 const props=W.propsInCircle(0,0,1200).filter(p=>p.solid&&!W.isWall(p.x,p.y)).slice(0,20);
 A.assert(props.length>0,'missing native solid prop coverage');
 for(const p of props){
   const first=W.projectileBlock(p.x,p.y,1);
   A.assert(W.projectilePathClear(p.x,p.y,p.x,p.y,first),'first blocker target exception lost');
   for(const target of [null,p])for(const offset of [-32,-12,12,32]){
     const ax=p.x+offset,ay=p.y+offset,bx=p.x-offset,by=p.y-offset;
     A.assert(reference(ax,ay,bx,by,target)===W.projectilePathClear(ax,ay,bx,by,target),'prop intersection mismatch');
   }
 }
 const destroyed=props[0];W.breakProp(destroyed);
 A.assert(reference(destroyed.x-40,destroyed.y,destroyed.x+40,destroyed.y)===W.projectilePathClear(destroyed.x-40,destroyed.y,destroyed.x+40,destroyed.y),'destroyed prop retained');
 // Terrain overrides are used by authored arenas and must remain authoritative.
 const wall=W.isWall,block=W.projectileBlock;
 try{W.isWall=()=>false;W.projectileBlock=()=>false;A.assert(W.projectilePathClear(0,0,500,0),'open override ignored');
   W.projectileBlock=x=>x>=20?'wall':null;A.assert(!W.projectilePathClear(0,0,500,0),'block override ignored');
   W.projectileBlock=()=>false;W.isWall=x=>x>=20;A.assert(!W.projectilePathClear(0,0,500,0),'wall override ignored');
 }finally{W.isWall=wall;W.projectileBlock=block}
 return {rays:603,open,blocked,solidProps:props.length,destruction:true};
}"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    report = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page(viewport={'width': 1200, 'height': 900})
        page.goto(URL)
        frame = game_frame(page)
        frame.evaluate("window.painNativeWorld=Object.fromEntries(['isFree','isWall','projectileBlock','collide','isLiquid'].map(k=>[k,G.World[k]]))")
        enter(frame)
        report['targeting'] = frame.evaluate(CHECK)
        if not args.baseline:
            report['visibility'] = frame.evaluate(RAYS)
        browser.close()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ('baseline.json' if args.baseline else 'report.json')).write_text(json.dumps(report, indent=2), 'utf-8')
    print(json.dumps(report))

if __name__ == '__main__':
    main()
