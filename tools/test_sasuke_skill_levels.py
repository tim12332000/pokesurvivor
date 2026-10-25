"""Sasuke unlocks at character levels 1/2/3/5/6, including upgraded starts."""
import json
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS

CHECK = r"""async () => {
 const A=Acceptance,assert=A.assert;
 G.Naruto.choose(30002);await G.NarutoAssets.ensure(30002);
 const perks=G.Upgrades.perks;
 const starts=[];
 try{
   for(const extra of [false,true]){
     G.Upgrades.perks=function(...args){return {...perks.apply(this,args),startMoves:extra?2:1}};
     G.Flow.goMenu();await G.Flow.play();A.pause();A.arena();
     const p=G.Game.player,signature=G.NarutoSkillCatalog.byDex.get(30002).id;
     assert(p.moves.length===1&&p.moves[0].id===signature,'locked skill granted at start, extra='+extra);
     starts.push({extra,moves:p.moves.map(m=>m.id)});
   }
 }finally{G.Upgrades.perks=perks}
 const p=G.Game.player,thresholds={'naruto-kusanagi':2,'naruto-fireball':3,'naruto-sharingan':5,'naruto-fuma-shuriken':6};
 const levels=[];
 for(let level=1;level<=6;level++){
   p.level=level;
   const pool=G.Moves.poolFor(p.mon),cards=G.LevelUp.offer(p,100);
   for(const [id,required] of Object.entries(thresholds)){
     assert(G.Moves.BY_ID[id].learnLevel===required,'definition '+id);
     assert(pool.includes(id)===(level>=required),'pool '+id+' at '+level);
     assert(cards.some(c=>c.key==='new:'+id)===(level>=required),'card '+id+' at '+level);
   }
   levels.push({level,skills:pool});
 }
 return {starts,levels};
}"""


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(URL + '&layout=wide')
        page.wait_for_function("window.PS_REDRAWN_READY && document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible():
            page.locator('#tap-start').click()
        page.evaluate(HARNESS)
        result = page.evaluate(CHECK)
        assert not errors, errors
        browser.close()
        print(json.dumps({'ok': True, **result}))


if __name__ == '__main__':
    main()
