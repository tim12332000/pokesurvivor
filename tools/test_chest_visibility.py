"""Compare seeded chest density and capture native chest art on biome terrain."""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_animation_complete import CHROME
from test_gaara import URL

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/chest-visibility'

SCENE = r"""() => {
 const canvas=document.createElement('canvas');canvas.width=800;canvas.height=480;
 document.body.replaceChildren(canvas);document.body.style.cssText='margin:0;background:#101820';
 canvas.style.cssText='width:800px;height:480px;image-rendering:pixelated';
 const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;
 for(let i=0;i<4;i++){
   ctx.save();ctx.beginPath();ctx.rect((i%2)*400,Math.floor(i/2)*240,400,240);ctx.clip();
   ctx.translate((i%2)*400,Math.floor(i/2)*240);
   G.World.reset(73);G.World.setBiome(i,true);
   const cam={left:()=>0,top:()=>0,w:400,h:240,sees:()=>true};G.World.drawGround(ctx,cam);
   for(const [type,x] of [['bigchest',120],['bigchest',280]]){
     G.World.drawProp(ctx,{type,x,y:160,r:type==='chest'?12:14,hp:22,maxHp:22,open:0,wiggle:0,flash:0},1);
   }
   ctx.fillStyle='#101820';ctx.fillRect(0,205,400,35);
   ctx.fillStyle='#fff';ctx.font='16px sans-serif';ctx.fillText(G.World.biomeName(),14,229);
   ctx.restore();
 }
 return true;
}"""

DENSITY = r"""oldSource => {
 const current=G.World;eval(oldSource);const previous=G.World;G.World=current;
 const count=world=>{
   const counts={chest:0,bigchest:0,altar:0,spring:0,trap:0};
   for(const seed of [73,191,617,991,1237,1601,2017,2503,3001,4001,5003,6007]){
     world.reset(seed);
     for(let cy=-8;cy<8;cy++)for(let cx=-8;cx<8;cx++){
       const cam={left:()=>cx*world.CW+world.CW/2,top:()=>cy*world.CW+world.CW/2,w:1,h:1,sees:()=>true};
       for(const p of world.visibleProps(cam)){
         if(Math.floor(p.tx/16)!==cx||Math.floor(p.ty/16)!==cy)continue;
         if(p.type in counts)counts[p.type]++;
       }
     }
   }
   return counts;
 };
 const before=count(previous),after=count(current);
 if(after.chest!==0)throw Error('small chests still spawn');
 const ratio=after.bigchest/(before.chest+before.bigchest);
 if(ratio<1.7||ratio>2.3)throw Error('combined chest density ratio '+ratio);
 for(const type of ['altar','spring','trap'])if(before[type]!==after[type])throw Error(type+' density changed');
 return {before,after};
}"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    before = '--before' in sys.argv
    if before:
        (OUT / 'world-before.js').write_bytes((ROOT / 'js/world/world.js').read_bytes())
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page(viewport={'width': 800, 'height': 480}, service_workers='block')
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(URL)
        page.wait_for_function("window.PS_REDRAWN_READY && G.World && document.getElementById('boot').classList.contains('hidden')")
        report = {} if before else page.evaluate(DENSITY, (OUT / 'world-before.js').read_text(encoding='utf-8'))
        page.evaluate(SCENE)
        page.locator('canvas').screenshot(path=str(OUT / ('before.png' if before else 'after.png')))
        assert not errors, errors
        if not before:
            (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps({'ok': True, **report}))
        browser.close()

if __name__ == '__main__':
    main()
