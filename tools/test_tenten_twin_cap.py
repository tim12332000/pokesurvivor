"""Native twin quantity boundary, damage conversion and cast snapshot checks."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_tenten import CHROME, HARNESS, SETUP, PROGRESSION, URL
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

CHECK = r"""() => {
 const A=Acceptance,p=A.p(),T=G.NarutoTenten,rows=[];
 const twin=p.moves.find(m=>m.id==='naruto-tenten-twin');
 while(twin.lvl<5)G.Moves.levelUp(twin);
 const savedCount=twin.count,savedDamage=twin.dmg,atk=p.atk;
 try {
   for(const requested of [299,300,301,600,3469]) {
     A.reset();twin.count=requested;p.target=A.spawn(180,0);
     A.castNative(twin.id);const pose=T.activeFor(p),expected=Math.min(300,requested);
     A.assert(pose.count===expected,'cap boundary '+requested);
     A.near(pose.m.dmg,savedDamage*requested/expected,'damage multiplier');
     A.near(pose.m.dmg*pose.count,savedDamage*requested,'total base damage');
     A.assert(twin.count===requested&&twin.dmg===savedDamage&&p.atk===atk,'learned move or player mutated');
     p.quantityPicks=20;A.advance(.13);
     const shots=T.weapons.filter(w=>w.mode==='tenten-twin');
     A.assert(shots.length>0,'missing native shots');
     A.near(shots[0].damage,savedDamage*requested/expected*atk,'actual weapon damage');
     A.near(pose.count,expected,'in-flight quantity changed');
     A.finish(1);A.assert(pose.emitted===expected,'emitted count');
     rows.push({requested,emitted:pose.emitted,multiplier:pose.m.tentenQuantityDamageMultiplier});
   }
   A.reset();twin.count=savedCount;p.quantityPicks=20;p.target=A.spawn(180,0);
   const hits=[],victim=p.target,hurt=victim.hurt;
   victim.hurt=function(...args){if(args[7]===twin.id)hits.push(args[0]);return hurt.apply(this,args)};
   A.castNative(twin.id);const pose=T.activeFor(p);
   A.assert(pose.count===300,'real 20-card cap');
   A.near(pose.m.dmg,12*3469/300,'real 20-card conversion');
   const texts=[],cv=document.createElement('canvas'),ctx=cv.getContext('2d');
   ctx.fillText=(s)=>texts.push(String(s));G.HUD.draw(ctx,1200,900,p,0);
   A.assert(texts.some(s=>s.includes('/300')),'HUD capped cast count');
   A.finish(1);
   A.assert(hits.length>0,'converted weapons failed to hit native enemy');
   A.near(hits[0],pose.m.dmg*atk*G.Types.mult(twin.type,victim.types)*G.Weather.mult(twin.type),'native hit damage');
   A.reset();p.quantityPicks=20;A.select(twin.id);texts.length=0;
   G.HUD.draw(ctx,1200,900,p,0);
   A.assert(texts.includes('忍具 300'),'HUD uncapped before cast');
   const card=G.LevelUp.offer(p,100).find(c=>c.key==='stat:selfClone');card.apply(p);
   const clone=G.SelfClones.actors()[0];clone.x=clone.y=0;clone.target=A.spawn(180,0);
   const cloneMove=clone.moves.find(m=>m.id===twin.id);
   A.assert(T.cast(clone,cloneMove),'clone could not cast');
   const clonePose=T.activeFor(clone);
   A.assert(clonePose.count===300,'clone cap');
   A.near(clonePose.m.dmg*clone.atk,12*3469/300*atk/3,'clone conversion applied once');
   A.reset();p.quantityPicks=20;p.target=A.spawn(180,0);A.castNative('naruto-tenten-fuma');
   A.assert(T.activeFor(p).count===173,'other skill unexpectedly capped or converted');
   return rows;
 } finally {twin.count=savedCount;A.reset();}
}"""

def main():
    out=Path(__file__).resolve().parents[1]/'.omx/state/tenten-twin-cap'
    out.mkdir(parents=True,exist_ok=True)
    report={'viewports':{},'errors':[]}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=CHROME,headless=True)
        for label,width,height in [('desktop',1200,900),('mobile',390,844)]:
            page=browser.new_page(viewport={'width':width,'height':height},service_workers='block')
            page.on('pageerror',lambda e:report['errors'].append(str(e)))
            parts=urlsplit(URL)
            query=dict(parse_qsl(parts.query));query['layout']='wide'
            page.goto(urlunsplit(parts._replace(query=urlencode(query))))
            page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
            page.locator('[data-quick-naruto="30009"]').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30009 && G.Game.state==="playing"')
            for script in [HARNESS,SETUP,PROGRESSION]:page.evaluate(script)
            report['viewports'][label]=page.evaluate(CHECK)
            page.screenshot(path=str(out/f'{label}.png'))
            page.close()
        browser.close()
    assert not report['errors'],report['errors']
    report['ok']=True
    (out/'latest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
