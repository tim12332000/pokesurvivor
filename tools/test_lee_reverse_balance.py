"""Reverse Lotus doubles base cooldown, all level damage, and pull capacity."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from test_lee_reverse_presentation import CHROME, HARNESS, SETUP, URL

OUT = Path(__file__).resolve().parents[1] / '.omx/state/lee-reverse-balance'

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),L=G.NarutoLee,near=(a,b)=>Math.abs(a-b)<1e-7;
 const damage=[420,504,504,504,630],frontDamage=[110,132,132,132,165];
 const levels=damage.map((d,i)=>{
   const m=G.Moves.instance('naruto-reverse-lotus',i+1),front=G.Moves.instance('naruto-lotus',i+1);
   A.assert(near(m.dmg,d)&&m.cd===10,'reverse damage or cooldown mismatch at level '+(i+1));
   A.assert(near(front.dmg,frontDamage[i])&&front.cd===5,'reverse balance leaked into Front Lotus');
   A.assert(m.desc.includes('冷卻 10 秒')&&m.desc.includes('10 名')&&m.desc.includes('24 名'),'reverse description is stale');
   return {level:i+1,damage:m.dmg,cooldown:m.cd};
 });
 const quantities=[];
 for(const [picks,reverse,front]of [[0,10,3],[2,15,4],[20,24,12]]){
   p.quantityPicks=p.quantityBonus=picks;
   const r=L.bindLimitOf(G.Moves.instance('naruto-reverse-lotus'),p),f=L.bindLimitOf(G.Moves.instance('naruto-lotus'),p);
   A.assert(r===reverse&&f===front,'quantity scaling or cap mismatch at picks '+picks);
   quantities.push({picks,reverse:r,front:f});
 }
 p.quantityPicks=p.quantityBonus=0;p.level=12;p.addMove('naruto-reverse-lotus');
 const cooldowns=[];
 for(const cdMul of [1,.5]){
   A.leeArena();p.cdMul=cdMul;const m=A.select('naruto-reverse-lotus');
   Object.assign(m,G.Moves.instance(m.id));const e=A.spawn(35,0),hits=[];p.target=e;
   const hurt=e.hurt;e.hurt=function(...args){hits.push(args[0]);return hurt.apply(this,args)};
   A.actualCast(m.id);const f=L.active,expected=10*cdMul;
   A.assert(near(m.t,expected),'native cooldown does not use new base or cooldown reduction');
   for(let n=0;n<200&&!hits.length;n++)A.advance(.005);
   const first=420*.1*f.attack*G.Types.mult(m.type,e.types)*G.Weather.mult(m.type);
   A.assert(hits.length===1&&near(hits[0],first),'native launch hit did not double');
   cooldowns.push({multiplier:cdMul,cooldown:expected,launchDamage:hits[0]});L.clear(p);
 }
 A.leeArena();p.cdMul=1;
 const move=A.select('naruto-reverse-lotus');Object.assign(move,G.Moves.instance(move.id));
 const main=A.spawn(35,0),nearby=Array.from({length:14},(_,i)=>A.spawn(60+Math.cos(i*Math.PI*2/14)*60,Math.sin(i*Math.PI*2/14)*60));
 p.target=main;A.actualCast(move.id);const actualGroup=L.active.boundTargets.length;
 A.assert(actualGroup===10,'ordinary crowded cast did not pull ten enemies');L.clear(p);
 A.assert([main,...nearby].every(e=>!L.bound(e)&&!L.liftFor(e)),'base group cleanup failed');
 return {levels,quantities,cooldowns,actualGroup};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page(service_workers='block')
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(URL)
        page.wait_for_function("window.G?.NarutoLee && document.querySelector('#boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible():
            page.locator('#tap-start').click()
        page.locator('#scr-menu [data-go="play"]').click()
        page.wait_for_function('G.Game.player?.dex===30006 && G.Game.state==="playing"')
        page.evaluate(HARNESS)
        page.evaluate(SETUP)
        report = page.evaluate(CHECK)
        assert not errors, errors
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, **report}))


if __name__ == '__main__':
    main()
