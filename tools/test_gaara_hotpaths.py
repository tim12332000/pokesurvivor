"""Resource contracts for native Gaara rendering and swept sand bullets."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS, SETUP

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.omx/state/gaara-performance'

CHECKS = r"""() => {
 const A=Acceptance,p=A.p(),N=G.NarutoGaara;
 p.level=25;
 for(const id of ['naruto-sand-coffin','naruto-sand-shield','naruto-sand-tsunami','naruto-sand-prison']){
  if(!p.hasMove(id)){const card=G.LevelUp.offer(p,100).find(c=>c.key==='new:'+id);A.assert(card&&card.apply(p)!==false,'learn fixture '+id)}
 }
 A.gaaraArena();p.target=A.spawn(230,0);A.spawn(180,35);A.spawn(180,-35);
 A.actualCast('naruto-sand-tsunami');A.advance(1);
 A.assert(N.active(p)?.kind==='gaara-tsunami','missing live wave');
 const canvas=document.createElement('canvas');canvas.width=1280;canvas.height=900;const ctx=canvas.getContext('2d');ctx.translate(640,450);
 const query=G.EnemyMgr.queryCircle,wall=G.World.isWall,block=G.World.projectileBlock;
 let queries=0,terrain=0;
 G.EnemyMgr.queryCircle=function(...args){queries++;return query.apply(this,args)};
 G.World.isWall=function(...args){terrain++;return wall.apply(this,args)};
 G.World.projectileBlock=function(...args){terrain++;return block.apply(this,args)};
 try{G.Combat.drawGroundFields(ctx);G.Combat.drawAirFields(ctx)}
 finally{G.EnemyMgr.queryCircle=query;G.World.isWall=wall;G.World.projectileBlock=block}
 A.assert(queries===0&&terrain===0,'drawing repeated combat/terrain queries '+JSON.stringify({queries,terrain}));
 const out={waveDraw:{queries,terrain}};
 const action=N.active(p),victim=action.victims[0];A.assert(victim,'missing wrapped wave victim');
 G.World.isWall=x=>x>80&&x<85;
 try{A.advance(.01);A.assert(!N.active(p).visibleVictims.has(victim),'combat-visible victim remained behind new wall')}
 finally{G.World.isWall=wall}
 A.gaaraArena();p.quantityBonus=20;p.target=A.spawn(230,0);
 A.actualCast('naruto-gaara');A.advance(.45);
 const bullets=N.bullets.length;A.assert(bullets>=3,'missing quantity sand bullets');queries=0;
 G.EnemyMgr.queryCircle=function(...args){queries++;return query.apply(this,args)};
 try{A.advance(.01)}finally{G.EnemyMgr.queryCircle=query}
 A.assert(queries>0&&queries<=bullets,'sand bullet repeated broadphase during one movement '+JSON.stringify({bullets,queries}));
 out.sandBulletStep={bullets,queries};
 return out;
}"""

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'errors':[],'viewports':{}}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=CHROME,headless=True)
            for mobile in [False,True]:
                context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},is_mobile=mobile,has_touch=mobile,service_workers='block')
                page=context.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
                page.goto(URL);page.wait_for_function("window.PS_REDRAWN_READY && G.AnimationLab && document.getElementById('boot').classList.contains('hidden')")
                if page.locator('#tap-start').is_visible():page.locator('#tap-start').click()
                page.locator('[data-quick-naruto="30007"]').click();page.locator('#scr-menu [data-go="play"]').click()
                page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"')
                page.evaluate(HARNESS);page.evaluate(SETUP)
                report['viewports']['mobile' if mobile else 'desktop']=page.evaluate(CHECKS)
                context.close()
            browser.close()
        assert not report['errors'],report['errors'];report['ok']=True
    except Exception as e:
        report.update(ok=False,failure=str(e));raise
    finally:(OUT/'hotpath-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'ok':True,'evidence':str(OUT/'hotpath-report.json')}))

if __name__=='__main__':main()
