"""Lee's icon shows real binding capacity and the frozen current cast count."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

OUT = Path(__file__).resolve().parents[1] / '.omx/state/lee-bind-hud'
CHECK = r"""() => {
 const A=Acceptance,assert=A.assert;
 G.Naruto.choose(30006);G.Flow.play();A.pause();A.arena();
 const p=G.Game.player,L=G.NarutoLee;p.level=12;p.x=p.y=0;
 assert(p.addMove('naruto-lotus'),'learn Lotus');
 const m=p.moves.find(m=>m.id==='naruto-lotus');p.setActive(p.slots.findIndex(g=>g.includes(m)));
 const render=()=>{
  const canvas=document.createElement('canvas');canvas.width=innerWidth;canvas.height=innerHeight;
  const ctx=canvas.getContext('2d'),fill=ctx.fillText,texts=[];
  ctx.fillText=function(text,...args){texts.push(String(text));return fill.call(this,text,...args)};
  G.HUD.draw(ctx,canvas.width,canvas.height,p,G.Game.st);
  return texts.find(t=>t.startsWith('綁定 ')||t==='近身');
 };
 assert(render()==='綁定 3','base binding capacity missing');
 const quantity=G.LevelUp.STATS.find(s=>s.id==='quantity');quantity.apply(p);quantity.apply(p);
 assert(render()==='綁定 4','quantity binding capacity incorrect');
 for(const [x,y] of [[100,0],[110,20],[120,-20],[130,40]])A.enemy(x,y);
 assert(L.cast(p,m),'native group cast');const f=L.active;
 assert(f.bindLimit===4&&f.boundTargets.length===4,'native cast failed four claims');
 assert(render()==='綁定 4/4','live binding group count missing');
 for(let i=0;i<5;i++)quantity.apply(p);
 assert(render()==='綁定 4/4','live cast changed after quantity cards');
 L.clear(p);assert(render()==='綁定 12','future capacity cap missing');G.EnemyMgr.clear();
 const boss=A.enemy(100,0);boss.boss=true;p.target=boss;
 assert(L.cast(p,m)&&!L.active.pullable,'boss fallback fixture');
 assert(render()==='近身','boss incorrectly labeled as bound');L.clear(p);
 return {base:3,quantity2:4,live:'4/4',futureCap:12,bossApproach:true};
}"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in [False, True]:
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(URL)
            page.wait_for_function("window.PS_REDRAWN_READY && G.NarutoLee && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.evaluate(HARNESS)
            report['mobile' if mobile else 'desktop'] = page.evaluate(CHECK)
            assert not errors, errors
            context.close()
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, **report}))

if __name__ == '__main__':
    main()
