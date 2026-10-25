"""Preta's 300-unit owner leash: actual batch absorption and ready-palm rendering."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_pain_auto import CHROME, URL, enter, game_frame

OUT = Path(__file__).resolve().parents[1] / '.omx/state/pain-absorb-range'
CHECK = r"""() => {
 const A=Acceptance,p=A.p(),P=G.NarutoPain,moves=p.moves,out=[];
 try {
  p.moves=moves.filter(m=>m.id==='naruto-pain-absorb');
  for(const distance of [110,111,299,300,300.01,301]) {
   A.reset();const b=P.actors().find(b=>b.path==='preta');
   P.actorsFor(p).forEach((a,i)=>{a.x=-400-i*30;a.y=-200});b.x=distance;b.y=0;
   const ctx=document.createElement('canvas').getContext('2d'),stroke=ctx.stroke.bind(ctx);let strokes=0;
   ctx.stroke=(...args)=>{strokes++;return stroke(...args)};
   G.PainSkillVFX.absorb.support(ctx,P.stateFor(p));
   A.assert((strokes>0)===(distance<=300),'ready-palm visibility disagrees with owner range '+distance);
   const make=(dx,dy)=>G.Projectiles.spawn({friendly:false,x:b.x+dx,y:dy,px:b.x+dx,py:dy,r:3,dmg:7,painAbsorbable:true});
   const batch=[make(20,0),make(-20,0),make(0,18)],outsidePalm=make(0,50);
   A.resume();G.Combat.resolve(.01,p,0);A.pause();
   const removed=batch.filter(s=>!G.Projectiles.all().includes(s)).length,state=P.snapshot(p);
   A.assert(removed===(distance<=300?3:0),'batch absorption owner boundary '+distance);
   A.assert(G.Projectiles.all().includes(outsidePalm),'owner leash enlarged palm radius');
   A.assert(state.intercepted===removed,'intercept counter mismatch');
   A.assert(state.absorbCooldown===(distance<=300?2.5:0),'owner leash changed cooldown');
   out.push({distance,ready:strokes>0,absorbed:removed,cooldown:state.absorbCooldown});
  }
 } finally {p.moves=moves;A.reset()}
 return out;
}"""


def main():
    report = {'url': URL, 'viewports': {}, 'errors': []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for label, viewport in [('desktop', {'width': 1200, 'height': 900}), ('mobile', {'width': 390, 'height': 844})]:
            page = browser.new_page(viewport=viewport, is_mobile=label == 'mobile', has_touch=label == 'mobile', service_workers='block')
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            page.goto(URL)
            frame = game_frame(page)
            enter(frame)
            report['viewports'][label] = frame.evaluate(CHECK)
            print(label, '300 boundary, batch, ready-palm, cooldown PASS', flush=True)
            page.close()
        browser.close()
    assert not report['errors'], report['errors']
    report['ok'] = True
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), 'utf-8')
    print(json.dumps({'ok': True, 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
