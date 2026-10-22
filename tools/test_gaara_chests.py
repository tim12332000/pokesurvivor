"""All chest spawns use native locked-chest interaction and loot."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL

CHECK = r"""() => {
 G.Naruto.choose(30007);G.Flow.play();G.Game.togglePause();
 const p=G.Game.player,N=G.NarutoGaara,basic=p.moves.find(m=>m.id==='naruto-gaara');
 const assert=(value,message)=>{if(!value)throw Error(message)};
 G.Combat.clearFields();G.EnemyMgr.clear();G.Projectiles.clear();G.World.reset(73);
 const chests=[];
 for(let cy=-8;cy<8;cy++)for(let cx=-8;cx<8;cx++){
   const cam={left:()=>cx*512+256,top:()=>cy*512+256,w:1,h:1,sees:()=>true};
   for(const prop of G.World.visibleProps(cam)){
     assert(prop.type!=='chest','small chest still spawned');
     if(prop.type==='bigchest')chests.push(prop);
   }
 }
 assert(chests.length>0,'no large chests generated');
 const chest=chests[0];p.x=chest.x;p.y=chest.y;p.dead=false;p.target=null;
 assert(chest.hp===Infinity&&!chest.destructible,'replacement is not a locked chest');
 assert(!N.canCast(p,basic),'automatic basic still targets replacement chest');
 const drops=[],drop=G.Pickups.drop,xp=G.Pickups.dropXp;
 G.Pickups.drop=function(type,...args){drops.push(type);return drop.call(this,type,...args)};
 G.Pickups.dropXp=function(...args){drops.push('xp');return xp.apply(this,args)};
 try{
   G.Interact.update(3.4,p);
   assert(G.World.specialsNear(chest.x,chest.y,1).includes(chest),'chest opened early');
   G.Interact.update(.11,p);
 }finally{G.Pickups.drop=drop;G.Pickups.dropXp=xp}
 assert(!G.World.specialsNear(chest.x,chest.y,1).includes(chest),'large chest failed to open');
 assert(drops.includes('coin')&&drops.includes('ticket')&&drops.includes('xp'),'large chest loot missing');
 return {smallChests:0,largeChestObservations:chests.length,opened:true,openSeconds:G.Interact.CHEST_TIME,coinDrops:drops.filter(t=>t==='coin').length};
}"""

def main():
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
            report['mobile' if mobile else 'desktop'] = page.evaluate(CHECK)
            assert not errors, errors
            context.close()
        browser.close()
    out = Path(__file__).resolve().parents[1] / '.omx/state/gaara-chests'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, **report}))

if __name__ == '__main__':
    main()
