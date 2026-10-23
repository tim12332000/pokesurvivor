"""All chest spawns use native locked-chest interaction and loot."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL

CHECK = r"""() => {
 G.Game.togglePause();
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
 window.ChestCheck={chest,level:p.level,time:G.Game.st.time,drops:[],drop:G.Pickups.drop,xp:G.Pickups.dropXp,assert};
 G.Pickups.drop=function(type,...args){ChestCheck.drops.push(type);return ChestCheck.drop.call(this,type,...args)};
 G.Pickups.dropXp=function(...args){ChestCheck.drops.push('xp');return ChestCheck.xp.apply(this,args)};
 p.invuln=999;
 G.Game.togglePause();
 // Stop outside physical contact, then trigger with a single tiny step.
 p.x=chest.x+chest.r+p.r+5;
 G.Interact.update(.001,p);assert(G.Game.state==='playing','chest triggered before contact');
 p.x=chest.x+chest.r+p.r+3;
 G.Interact.update(.001,p);
 assert(G.Game.state==='chest'&&chest.used,'contact did not immediately begin opening');
 assert(!G.Game.openChest(chest),'same chest triggered twice');
 return {smallChests:0,largeChestObservations:chests.length};
}"""

def main():
    report = {}
    out = Path(__file__).resolve().parents[1] / '.omx/state/gaara-chests'
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        for mobile in [False, True]:
            context = browser.new_context(viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(os.environ.get('CHEST_URL',URL)+'&layout=wide')
            page.wait_for_function("window.PS_REDRAWN_READY && document.getElementById('boot').classList.contains('hidden')")
            if page.locator('#tap-start').is_visible():
                page.locator('#tap-start').click()
            page.evaluate('G.Naruto.choose(30007);G.Flow.play()')
            page.wait_for_function("G.Game.player?.dex===30007&&G.Game.state==='playing'")
            label='mobile' if mobile else 'desktop'
            result=report[label] = page.evaluate(CHECK)
            page.screenshot(path=str(out/f'{label}-opening.png'))
            page.wait_for_function('G.Game.chest?.opened===true')
            result['openedAt']=page.evaluate('G.Game.chest.age')
            page.evaluate('''() => {const C=ChestCheck;C.assert(!G.World.specialsNear(C.chest.x,C.chest.y,1).includes(C.chest),'opened chest still exists');
              C.assert(G.Game.player.level===C.level+1,'chest did not directly award one level');
              C.assert(C.drops.includes('coin')&&C.drops.includes('ticket')&&!C.drops.includes('xp'),'loot missing or duplicate XP');
              C.assert(!G.UI.isOpen('scr-levelup'),'cards appeared before post-open delay');}''')
            page.screenshot(path=str(out/f'{label}-opened.png'))
            page.wait_for_function('G.Game.chest?.age>=1.45')
            assert not page.locator('#scr-levelup').is_visible(), 'cards appeared less than 1 s after opening'
            assert page.evaluate('G.Game.st.time===ChestCheck.time'), 'world did not pause during opening'
            page.wait_for_function("G.Game.state==='levelup'")
            assert page.locator('#scr-levelup').is_visible()
            assert page.evaluate('G.Game.chest===null')
            page.screenshot(path=str(out/f'{label}-choices.png'))
            result['coinDrops']=page.evaluate("ChestCheck.drops.filter(t=>t==='coin').length")
            assert result['coinDrops']==9
            page.evaluate('G.RunUI.pick(0)')
            page.wait_for_function("G.Game.state==='playing'")
            # A repeated interaction with the consumed chest cannot award a second level.
            assert page.evaluate('!G.Game.openChest(ChestCheck.chest)')
            page.evaluate('G.Pickups.drop=ChestCheck.drop;G.Pickups.dropXp=ChestCheck.xp')
            # Quitting mid-opening must not leave a delayed reward in the next run.
            page.evaluate('''() => {G.Game.toUI();G.Flow.play();const p=G.Game.player;
              G.Game.openChest({type:'bigchest',x:p.x,y:p.y,r:14,tx:900,ty:900,used:false});
              G.Game.toUI();G.Flow.play();G.Game.togglePause();}''')
            page.wait_for_timeout(1800)
            assert page.evaluate("G.Game.chest===null&&G.Game.player.level===1&&!G.UI.isOpen('scr-levelup')"), 'chest leaked into new run'
            result['delaySeconds']=1
            result['cancelAndRestart']=True
            if not mobile:
                page.evaluate('''() => {G.Game.toUI();G.Game.startRun({seed:73,host:G.Net.uid,
                  members:[{uid:G.Net.uid,name:'Host',dex:30007,shiny:false}]});}''')
                page.wait_for_function("G.Coop.isHost&&G.Game.state==='playing'")
                page.evaluate(CHECK)
                page.wait_for_function("G.Game.state==='levelup'")
                assert page.evaluate('G.Game.player.level===ChestCheck.level+1&&G.Game.chest===null'), 'co-op chest reward/hold stalled'
                page.evaluate('G.RunUI.pick(0)')
                page.wait_for_function("G.Game.state==='playing'")
                page.evaluate('G.Pickups.drop=ChestCheck.drop;G.Pickups.dropXp=ChestCheck.xp;G.Coop.end()')
                result['nativeCoopHost']=True
            assert not errors, errors
            context.close()
        browser.close()
    (out / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, **report}))

if __name__ == '__main__':
    main()
