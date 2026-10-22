"""Native Chidori icon shows tier/quantity limits and frozen live combo progress."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/chidori-hud'
CHECK = r"""() => {
 G.Naruto.choose(30002);G.Flow.play();Acceptance.pause();Acceptance.arena();
 const p=G.Game.player,m=p.moves.find(m=>m.digiMode==='chidori-chain'),N=G.NarutoChidori;
 const render=()=>{
   const ctx=document.createElement('canvas').getContext('2d'),texts=[],fill=ctx.fillText;
   ctx.canvas.width=1280;ctx.canvas.height=900;
   ctx.fillText=function(text,...args){texts.push(String(text));return fill.call(this,text,...args)};
   G.HUD.draw(ctx,1280,900,p,G.Game.st);
   return texts.find(t=>t.startsWith('連招 '));
 };
 const assert=(a,b)=>{if(a!==b)throw Error(a+' != '+b)},tiers=[];
 for(let level=1;level<=5;level++){
   if(level>1)G.Moves.levelUp(m);
   const label=render();assert(label,'連招 '+level*5);tiers.push(label);
 }
 const quantity=G.LevelUp.STATS.find(s=>s.id==='quantity');
 for(let i=0;i<3;i++)quantity.apply(p);
 assert(render(),'連招 48');
 const a=Acceptance.enemy(0,50),b=Acceptance.enemy(.5,90);p.target=a;
 if(!N.cast(p,G.Quantity.snapshot(p,m)))throw Error('native Chidori cast failed');
 for(let i=0;i<200&&N.active?.hitCount<2;i++){Acceptance.resume();try{N.update(.01)}finally{Acceptance.pause()}}
 if(!N.active||N.active.hitCount<2)throw Error('native combo did not hit twice');
 const progress='連招 '+N.active.hitCount+'/48';assert(render(),progress);
 for(let i=0;i<3;i++)quantity.apply(p);
 assert(render(),progress);
 N.clear(p);assert(render(),'連招 95');
 p.addMove('naruto-fuma-shuriken');assert(render(),'連招 95');
 p.setActive(p.slots.findIndex(g=>g.includes(m)));G.EnemyMgr.clear();p.frozen=true;
 return {tiers,quantity3:'連招 48',active:progress,quantity6:'連招 95'};
}"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in [False, True]:
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile)
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.evaluate(HARNESS)
            label = 'mobile' if mobile else 'desktop'
            report[label] = page.evaluate(CHECK)
            page.evaluate('Acceptance.resume()')
            page.wait_for_timeout(100)
            page.screenshot(path=str(OUT / f'{label}.png'))
            assert not errors, errors
            context.close()
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, **report}, ensure_ascii=False))

if __name__ == '__main__':
    main()
