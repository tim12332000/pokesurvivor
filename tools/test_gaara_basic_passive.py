"""Sand Shower stays automatic, upgradeable and outside selectable skill slots."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_gaara import CHROME, URL, HARNESS, SETUP

OUT = Path(__file__).resolve().parents[1] / '.omx/state/gaara-basic-passive'
CHECK = r"""() => {
 const A=Acceptance,p=A.p(),id='naruto-gaara',basic=p.moves.find(m=>m.id===id);
 const slotless=()=>!p.slots.some(g=>g.includes(basic))&&p.bind[id]===undefined;
 A.assert(basic&&basic.passive&&slotless(),'starter still selectable');
 A.assert(p.slots.length===0,'starter consumed an active slot');
 A.gaaraArena();const target=A.spawn(110,0);p.target=target;
 const step=dt=>{A.resume();try{G.Combat.tick(dt,p,0);G.Combat.updateFields(dt)}finally{A.pause()}};
 const attack=()=>{const hp=target.hp;for(let i=0;i<250&&target.hp===hp;i++)step(.01);A.assert(target.hp<hp,'automatic basic failed');};
 attack();
 const upgrade=G.LevelUp.offer(p,100).find(c=>c.key==='up:'+id);
 A.assert(upgrade&&upgrade.apply(p)!==false&&basic.lvl===2&&slotless(),'basic upgrade failed');
 p.level=12;p.addMove('naruto-sand-coffin');p.addMove('naruto-sand-prison');
 const selected=p.activeGroup()[0];A.assert(selected&&slotless(),'new skill reintroduced basic slot');
 // A legacy saved run retains the learned instance, upgrade, damage and active skill.
 basic.passive=false;basic.dealt=123;p.slots.unshift([basic]);p.active++;p.bind[id]=0;
 G.NarutoSkillCatalog.migrateGaaraPassives(p);
 A.assert(slotless()&&basic.passive&&basic.lvl===2&&basic.dealt===123&&p.activeGroup().includes(selected),'legacy migration damaged state');
 // Runtime must also repair an actively selected legacy basic before combat executes.
 basic.passive=false;p.slots.unshift([basic]);p.active=0;p.bind[id]=0;step(.01);
 A.assert(slotless()&&basic.passive,'runtime kept selectable basic');
 A.assert(p.addMove(id)===false&&p.moves.filter(m=>m.id===id).length===1,'basic duplicated');
 p.setActive(p.slots.findIndex(g=>g.some(m=>m.id==='naruto-sand-prison')));
 attack();A.assert(slotless(),'selected control skill disabled passive');
 const groups=[...p.slots,...p.moves.filter(m=>m.passive).map(m=>[m])];
 A.assert(groups.filter(g=>g.includes(basic)).length===1,'HUD repeats basic');
 return {basicLevel:basic.lvl,selectable:p.slots.map(g=>g.map(m=>m.id)),automaticDamage:100000-target.hp};
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
            page.locator('[data-quick-naruto="30007"]').click()
            page.locator('#scr-menu [data-go="play"]').click()
            page.wait_for_function('G.Game.player?.dex===30007 && G.Game.state==="playing"')
            for setup in [HARNESS, SETUP]:
                page.evaluate(setup)
            label = 'mobile' if mobile else 'desktop'
            report[label] = page.evaluate(CHECK)
            page.evaluate("Acceptance.resume();G.Game.player.frozen=true;G.EnemyMgr.clear()")
            page.wait_for_timeout(100)
            page.screenshot(path=str(OUT / f'{label}.png'))
            assert not errors, errors
            context.close()
        browser.close()
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, **report}))

if __name__ == '__main__':
    main()
